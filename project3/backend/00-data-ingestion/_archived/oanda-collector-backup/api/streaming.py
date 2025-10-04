"""
Streaming API - Manages real-time data streaming from OANDA
"""
import asyncio
import logging
from typing import List, Optional, Callable, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class StreamingAPI:
    """
    High-level streaming API for OANDA market data
    Manages multiple instrument streams with automatic failover
    """

    def __init__(
        self,
        account_manager,
        stream_manager,
        nats_publisher,
        config: Dict[str, Any]
    ):
        """
        Initialize Streaming API

        Args:
            account_manager: Business layer account manager
            stream_manager: Business layer stream manager
            nats_publisher: NATS publisher for streaming data
            config: Service configuration
        """
        self.account_manager = account_manager
        self.stream_manager = stream_manager
        self.nats_publisher = nats_publisher
        self.config = config
        self._active_streams: Dict[str, asyncio.Task] = {}
        self._running = False

    async def start(self, instruments: List[str]) -> bool:
        """
        Start streaming for specified instruments

        Args:
            instruments: List of instrument symbols (e.g., ['EUR_USD', 'GBP_USD'])

        Returns:
            bool: True if streaming started successfully
        """
        if self._running:
            logger.warning("Streaming already running")
            return False

        logger.info(f"Starting streaming for {len(instruments)} instruments")

        try:
            # Get active account
            account = await self.account_manager.get_active_account()
            if not account:
                logger.error("No active account available")
                return False

            # Initialize streams
            for instrument in instruments:
                stream_task = asyncio.create_task(
                    self._stream_instrument(instrument, account)
                )
                self._active_streams[instrument] = stream_task

            self._running = True
            logger.info(f"Streaming started successfully for {len(instruments)} instruments")
            return True

        except Exception as e:
            logger.error(f"Failed to start streaming: {e}")
            await self.stop()
            return False

    async def stop(self) -> None:
        """Stop all active streams"""
        if not self._running:
            return

        logger.info("Stopping all streams")
        self._running = False

        # Cancel all stream tasks
        for instrument, task in self._active_streams.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.debug(f"Stream cancelled for {instrument}")

        self._active_streams.clear()
        logger.info("All streams stopped")

    async def _stream_instrument(self, instrument: str, account: Dict[str, Any]) -> None:
        """
        Stream data for a single instrument with automatic reconnection

        Args:
            instrument: Instrument symbol
            account: Account configuration
        """
        retry_count = 0
        max_retries = self.config['streaming']['max_reconnect_attempts']

        while self._running and (max_retries < 0 or retry_count < max_retries):
            try:
                logger.info(f"Starting stream for {instrument} (attempt {retry_count + 1})")

                # Create stream through stream manager
                async for tick in self.stream_manager.stream_pricing(
                    account_id=account['id'],
                    instruments=[instrument]
                ):
                    if not self._running:
                        break

                    # Publish to NATS
                    await self._publish_tick(instrument, tick)

                # If we get here, stream ended gracefully
                if self._running:
                    logger.warning(f"Stream ended for {instrument}, reconnecting...")
                    retry_count += 1
                    await asyncio.sleep(self.config['streaming']['reconnect_delay'])
                else:
                    break

            except asyncio.CancelledError:
                logger.info(f"Stream cancelled for {instrument}")
                break

            except Exception as e:
                logger.error(f"Error streaming {instrument}: {e}")
                retry_count += 1

                # Check if we need to failover to another account
                if retry_count >= 3:
                    logger.warning(f"Multiple failures for {instrument}, attempting account failover")
                    new_account = await self.account_manager.failover()
                    if new_account:
                        account = new_account
                        retry_count = 0

                await asyncio.sleep(self.config['streaming']['reconnect_delay'])

    async def _publish_tick(self, instrument: str, tick: Dict[str, Any]) -> None:
        """
        Publish tick data to NATS

        Args:
            instrument: Instrument symbol
            tick: Tick data dictionary
        """
        try:
            # Add metadata
            tick['instrument'] = instrument
            tick['collector_timestamp'] = datetime.utcnow().isoformat()
            tick['collector_instance'] = self.config['service']['instance_id']

            # Publish to NATS subject
            subject = f"{self.config['nats']['subjects']['pricing']}.{instrument}"
            await self.nats_publisher.publish(subject, tick)

        except Exception as e:
            logger.error(f"Failed to publish tick for {instrument}: {e}")

    async def add_instrument(self, instrument: str) -> bool:
        """
        Add a new instrument to active streams

        Args:
            instrument: Instrument symbol

        Returns:
            bool: True if added successfully
        """
        if instrument in self._active_streams:
            logger.warning(f"Instrument {instrument} already streaming")
            return False

        try:
            account = await self.account_manager.get_active_account()
            if not account:
                logger.error("No active account available")
                return False

            stream_task = asyncio.create_task(
                self._stream_instrument(instrument, account)
            )
            self._active_streams[instrument] = stream_task
            logger.info(f"Added stream for {instrument}")
            return True

        except Exception as e:
            logger.error(f"Failed to add instrument {instrument}: {e}")
            return False

    async def remove_instrument(self, instrument: str) -> bool:
        """
        Remove an instrument from active streams

        Args:
            instrument: Instrument symbol

        Returns:
            bool: True if removed successfully
        """
        if instrument not in self._active_streams:
            logger.warning(f"Instrument {instrument} not streaming")
            return False

        try:
            task = self._active_streams[instrument]
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            del self._active_streams[instrument]
            logger.info(f"Removed stream for {instrument}")
            return True

        except Exception as e:
            logger.error(f"Failed to remove instrument {instrument}: {e}")
            return False

    def get_active_instruments(self) -> List[str]:
        """
        Get list of currently streaming instruments

        Returns:
            List[str]: List of instrument symbols
        """
        return list(self._active_streams.keys())

    def is_running(self) -> bool:
        """
        Check if streaming is active

        Returns:
            bool: True if streaming is running
        """
        return self._running
