"""
ConfigClient Usage Examples

This file demonstrates how to use ConfigClient in your service.
"""

import asyncio
import logging
from client import ConfigClient

# Setup logging
logging.basicConfig(level=logging.INFO)


# ============================================================
# EXAMPLE 1: Basic Usage (Recommended Pattern)
# ============================================================

async def example_basic_usage():
    """Basic usage: Fetch config with caching and fallback"""

    # Safe defaults (fallback jika Central Hub down)
    safe_defaults = {
        "operational": {
            "batch_size": 100,
            "max_retries": 3,
            "gap_check_interval_hours": 1
        },
        "features": {
            "enable_verification": True
        }
    }

    # Create client
    config_client = ConfigClient(
        service_name="polygon-historical-downloader",
        central_hub_url="http://localhost:7000",  # atau http://suho-central-hub:7000
        safe_defaults=safe_defaults,
        cache_ttl_seconds=300  # 5 minutes
    )

    # Initialize (fetch initial config)
    await config_client.init_async()

    # Get config (dari cache atau Central Hub)
    config = await config_client.get_config()

    print(f"✅ Config loaded: {config}")

    # Akses config values
    batch_size = config['operational']['batch_size']
    gap_interval = config['operational']['gap_check_interval_hours']

    print(f"📊 Batch size: {batch_size}")
    print(f"⏰ Gap check interval: {gap_interval} hours")

    # Cleanup
    await config_client.shutdown()


# ============================================================
# EXAMPLE 2: With Hot-Reload (NATS Subscription)
# ============================================================

async def example_with_hot_reload():
    """Advanced: Config hot-reload tanpa restart service"""

    safe_defaults = {
        "operational": {
            "batch_size": 100
        }
    }

    # Create client dengan NATS hot-reload enabled
    config_client = ConfigClient(
        service_name="polygon-historical-downloader",
        central_hub_url="http://localhost:7000",
        safe_defaults=safe_defaults,
        enable_nats_updates=True,  # Enable hot-reload
        nats_url="nats://localhost:4222"
    )

    # Callback function ketika config diupdate
    def on_config_changed(new_config):
        print(f"🔄 Config updated! New batch_size: {new_config['operational']['batch_size']}")

    # Register callback
    config_client.on_config_update(on_config_changed)

    # Initialize
    await config_client.init_async()

    # Get initial config
    config = await config_client.get_config()
    print(f"Initial config: {config}")

    # Service runs...
    # Jika admin update config di Central Hub:
    # → POST http://central-hub:7000/api/v1/config/polygon-historical-downloader
    # → NATS broadcast
    # → on_config_changed() dipanggil otomatis
    # → Config di-reload tanpa restart!

    # Keep running untuk listen NATS updates
    print("Listening for config updates... (Press Ctrl+C to exit)")
    try:
        await asyncio.sleep(3600)  # Run for 1 hour
    except KeyboardInterrupt:
        print("Shutting down...")

    await config_client.shutdown()


# ============================================================
# EXAMPLE 3: Integration in Service Config Class
# ============================================================

class ServiceConfig:
    """
    Example: How to integrate ConfigClient in your service config class
    """

    def __init__(self):
        # === CRITICAL CONFIGS dari ENV VARS ===
        import os
        self.polygon_api_key = os.getenv("POLYGON_API_KEY")
        self.clickhouse_host = os.getenv("CLICKHOUSE_HOST")
        self.clickhouse_password = os.getenv("CLICKHOUSE_PASSWORD")

        if not self.polygon_api_key:
            raise ValueError("POLYGON_API_KEY environment variable not set")

        # === OPERATIONAL CONFIGS dari Central Hub ===
        self._config_client = ConfigClient(
            service_name="polygon-historical-downloader",
            central_hub_url=os.getenv("CENTRAL_HUB_URL", "http://suho-central-hub:7000"),
            safe_defaults=self._get_safe_defaults(),
            cache_ttl_seconds=300,
            enable_nats_updates=True  # Optional: hot-reload
        )

        self._operational_config = None

    def _get_safe_defaults(self) -> dict:
        """Safe fallback configuration"""
        return {
            "operational": {
                "gap_check_interval_hours": 1,
                "batch_size": 100,
                "max_retries": 3,
                "retry_delay_seconds": 10,
                "verification_enabled": True
            },
            "download": {
                "start_date": "today-7days",
                "end_date": "today"
            },
            "features": {
                "enable_gap_verification": True,
                "enable_period_tracker": True,
                "enable_auto_backfill": True
            }
        }

    async def init_async(self):
        """Async initialization - fetch operational configs"""
        await self._config_client.init_async()
        self._operational_config = await self._config_client.get_config()

        # Optional: Register callback untuk hot-reload
        def on_update(new_config):
            self._operational_config = new_config
            print(f"✅ Config reloaded at runtime!")

        self._config_client.on_config_update(on_update)

    async def shutdown(self):
        """Cleanup"""
        await self._config_client.shutdown()

    # === CONFIG PROPERTIES ===

    @property
    def gap_check_interval_hours(self) -> int:
        return self._operational_config.get('operational', {}).get('gap_check_interval_hours', 1)

    @property
    def batch_size(self) -> int:
        return self._operational_config.get('operational', {}).get('batch_size', 100)

    @property
    def max_retries(self) -> int:
        return self._operational_config.get('operational', {}).get('max_retries', 3)

    @property
    def download_range(self) -> dict:
        return self._operational_config.get('download', {
            'start_date': 'today-7days',
            'end_date': 'today'
        })

    @property
    def enable_gap_verification(self) -> bool:
        return self._operational_config.get('features', {}).get('enable_gap_verification', True)


async def example_service_integration():
    """Example: Using ConfigClient in your service"""

    # Create service config
    config = ServiceConfig()

    # Async init (fetch from Central Hub)
    await config.init_async()

    # Use config
    print(f"Polygon API Key: {config.polygon_api_key[:10]}...")
    print(f"Batch size: {config.batch_size}")
    print(f"Gap check interval: {config.gap_check_interval_hours} hours")
    print(f"Download range: {config.download_range}")

    # Service logic runs...
    # Config auto-reloads jika admin update di Central Hub

    # Cleanup
    await config.shutdown()


# ============================================================
# EXAMPLE 4: Utility Helper - Get Value by Path
# ============================================================

async def example_get_value():
    """Example: Get nested config value by dot-notation path"""

    config_client = ConfigClient(
        service_name="polygon-historical-downloader",
        central_hub_url="http://localhost:7000",
        safe_defaults={
            "operational": {
                "batch_size": 100
            }
        }
    )

    await config_client.init_async()

    # Get value by path (dot notation)
    batch_size = config_client.get_value("operational.batch_size", default=100)
    gap_interval = config_client.get_value("operational.gap_check_interval_hours", default=1)

    print(f"Batch size: {batch_size}")
    print(f"Gap interval: {gap_interval}")

    await config_client.shutdown()


# ============================================================
# Run Examples
# ============================================================

async def main():
    print("=" * 60)
    print("ConfigClient Usage Examples")
    print("=" * 60)

    print("\n[Example 1] Basic Usage")
    print("-" * 60)
    await example_basic_usage()

    print("\n[Example 2] Service Integration")
    print("-" * 60)
    await example_service_integration()

    print("\n[Example 3] Get Value by Path")
    print("-" * 60)
    await example_get_value()

    # Uncomment to test hot-reload (requires NATS running)
    # print("\n[Example 4] Hot-Reload Demo")
    # print("-" * 60)
    # await example_with_hot_reload()


if __name__ == "__main__":
    asyncio.run(main())
