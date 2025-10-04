"""
OANDA Collector - Main Application
Multi-account OANDA data collector with failover support
"""
import asyncio
import signal
import sys
from pathlib import Path
from typing import Optional
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from infrastructure.logging.logger import setup_logging
from infrastructure.config.config_manager import ConfigManager
from infrastructure.discovery.service_registry import ServiceRegistry
from infrastructure.memory.memory_store import MemoryStore

from integration.oanda.client import OandaClient
from integration.central_hub.client import CentralHubClient
from integration.streaming.nats_publisher import NatsPublisher

from business.account_manager import AccountManager
from business.stream_manager import StreamManager

from api.streaming import StreamingAPI
from api.pricing import PricingAPI

logger = logging.getLogger(__name__)


class OandaCollectorService:
    """
    Main OANDA Collector Service
    Orchestrates all components and manages service lifecycle
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize OANDA Collector Service

        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config: Optional[ConfigManager] = None
        self.running = False

        # Components
        self.central_hub_client: Optional[CentralHubClient] = None
        self.oanda_client: Optional[OandaClient] = None
        self.nats_publisher: Optional[NatsPublisher] = None
        self.service_registry: Optional[ServiceRegistry] = None
        self.memory_store: Optional[MemoryStore] = None

        # Business layer
        self.account_manager: Optional[AccountManager] = None
        self.stream_manager: Optional[StreamManager] = None

        # API layer
        self.streaming_api: Optional[StreamingAPI] = None
        self.pricing_api: Optional[PricingAPI] = None

        # Background tasks
        self.tasks = []

    async def initialize(self) -> bool:
        """
        Initialize all service components

        Returns:
            bool: True if initialization successful
        """
        try:
            logger.info("=" * 60)
            logger.info("OANDA Collector Service - Initializing")
            logger.info("=" * 60)

            # 1. Load configuration
            self.config = ConfigManager(self.config_path)
            config_data = self.config.load_config()

            # Setup logging
            setup_logging(config_data['logging'])

            # Validate configuration
            if not self.config.validate_config():
                logger.error("Configuration validation failed")
                return False

            # 2. Initialize Central Hub client
            logger.info("Connecting to Central Hub...")
            self.central_hub_client = CentralHubClient(config_data)

            # Sync configuration with Central Hub
            service_name = config_data['service']['name']
            await self.config.sync_with_central_hub(service_name)

            # 3. Initialize Memory Store
            self.memory_store = MemoryStore(
                self.central_hub_client,
                namespace=f"oanda-collector:{config_data['service']['instance_id']}"
            )

            # 4. Initialize OANDA client
            logger.info("Initializing OANDA client...")
            self.oanda_client = OandaClient(config_data)

            # 5. Initialize NATS publisher
            logger.info("Connecting to NATS...")
            self.nats_publisher = NatsPublisher(config_data)
            if not await self.nats_publisher.connect():
                logger.error("Failed to connect to NATS")
                return False

            # 6. Initialize Business Layer
            logger.info("Initializing business layer...")

            # Account Manager
            self.account_manager = AccountManager(
                accounts_config=config_data['oanda']['accounts'],
                failover_config=config_data['oanda']['failover'],
                memory_store=self.memory_store
            )

            if not await self.account_manager.initialize():
                logger.error("Failed to initialize account manager")
                return False

            # Stream Manager
            self.stream_manager = StreamManager(
                oanda_client=self.oanda_client,
                config=config_data,
                memory_store=self.memory_store
            )

            # 7. Initialize API Layer
            logger.info("Initializing API layer...")

            self.streaming_api = StreamingAPI(
                account_manager=self.account_manager,
                stream_manager=self.stream_manager,
                nats_publisher=self.nats_publisher,
                config=config_data
            )

            self.pricing_api = PricingAPI(
                account_manager=self.account_manager,
                oanda_client=self.oanda_client,
                config=config_data
            )

            # 8. Register with Central Hub
            logger.info("Registering with Central Hub...")
            self.service_registry = ServiceRegistry(
                central_hub_client=self.central_hub_client,
                config=config_data
            )

            metadata = {
                'type': 'oanda-collector',
                'capabilities': ['pricing-stream', 'candles-historical', 'multi-account', 'auto-failover'],
                'oanda_config': {
                    'environment': config_data['oanda']['environment'],
                    'active_accounts': len([
                        acc for acc in config_data['oanda']['accounts']
                        if acc.get('enabled')
                    ]),
                    'max_streams': config_data['oanda']['rate_limits']['max_streams_per_ip'],
                    'instruments': list(config_data['streaming']['instruments'].get('forex', []))
                }
            }

            # TODO: Get actual service host/port from environment or config
            if not await self.service_registry.register(
                host=config_data['service']['instance_id'],
                port=8080,
                metadata=metadata
            ):
                logger.warning("Service registration failed, continuing anyway...")

            logger.info("=" * 60)
            logger.info("OANDA Collector Service - Initialization Complete")
            logger.info("=" * 60)

            return True

        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            return False

    async def start(self) -> None:
        """Start the service"""
        try:
            # Get instruments from config
            instruments = []
            for category, inst_list in self.config.get_section('streaming')['instruments'].items():
                instruments.extend(inst_list)

            logger.info(f"Starting data collection for {len(instruments)} instruments")

            # Start streaming
            if not await self.streaming_api.start(instruments):
                logger.error("Failed to start streaming")
                return

            # Start background tasks
            self.tasks.append(
                asyncio.create_task(self.account_manager.run_health_checks())
            )

            self.tasks.append(
                asyncio.create_task(self.stream_manager.manage_buffer())
            )

            # Start config watch
            if self.config.get('central_hub.config_sync.enabled', True):
                self.tasks.append(
                    asyncio.create_task(self.config.watch_for_updates())
                )

            self.running = True
            logger.info("OANDA Collector Service is running")

            # Keep service running
            while self.running:
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Error in service execution: {e}", exc_info=True)
            await self.shutdown()

    async def shutdown(self) -> None:
        """Graceful shutdown"""
        if not self.running:
            return

        logger.info("=" * 60)
        logger.info("OANDA Collector Service - Shutting Down")
        logger.info("=" * 60)

        self.running = False

        # Stop streaming
        if self.streaming_api:
            await self.streaming_api.stop()

        # Cancel background tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Cleanup components
        if self.stream_manager:
            await self.stream_manager.cleanup()

        if self.service_registry:
            await self.service_registry.deregister()

        if self.nats_publisher:
            await self.nats_publisher.disconnect()

        if self.central_hub_client:
            await self.central_hub_client.close()

        logger.info("Shutdown complete")


async def main():
    """Main entry point"""
    # Create service
    service = OandaCollectorService()

    # Setup signal handlers
    loop = asyncio.get_event_loop()

    def signal_handler(sig):
        logger.info(f"Received signal {sig}, initiating shutdown...")
        asyncio.create_task(service.shutdown())

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))

    # Initialize and start
    if await service.initialize():
        await service.start()
    else:
        logger.error("Service initialization failed")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
