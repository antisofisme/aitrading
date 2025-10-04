"""
Stream Manager - Manages OANDA pricing streams with buffering and error handling
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class StreamManager:
    """
    Manages real-time pricing streams from OANDA
    Handles stream lifecycle, buffering, and error recovery
    """

    def __init__(
        self,
        oanda_client,
        config: Dict[str, Any],
        memory_store=None
    ):
        """
        Initialize Stream Manager

        Args:
            oanda_client: OANDA API client
            config: Streaming configuration
            memory_store: Central Hub memory store for coordination
        """
        self.oanda_client = oanda_client
        self.config = config
        self.memory_store = memory_store

        # Stream tracking
        self.active_streams: Dict[str, asyncio.Task] = {}
        self.stream_stats: Dict[str, Dict[str, Any]] = {}
        self.buffer: Dict[str, List[Dict[str, Any]]] = {}

        # Configuration
        self.buffer_size = config['streaming'].get('buffer_size', 1000)
        self.flush_interval = config['streaming'].get('flush_interval', 1)
        self.heartbeat_interval = config['streaming'].get('heartbeat_interval', 5)

    async def stream_pricing(
        self,
        account_id: str,
        instruments: List[str]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream pricing data from OANDA

        Args:
            account_id: OANDA account ID
            instruments: List of instruments to stream

        Yields:
            Dict containing pricing tick data
        """
        stream_id = f"{account_id}:{','.join(instruments)}"

        # Initialize stream stats
        self.stream_stats[stream_id] = {
            'started_at': datetime.utcnow().isoformat(),
            'ticks_received': 0,
            'errors': 0,
            'last_tick': None,
            'instruments': instruments
        }

        logger.info(f"Starting pricing stream for {len(instruments)} instruments on account {account_id}")

        try:
            # Create OANDA streaming request
            async for response in self.oanda_client.stream_pricing(
                account_id=account_id,
                instruments=instruments
            ):
                if response.get('type') == 'PRICE':
                    # Update stats
                    self.stream_stats[stream_id]['ticks_received'] += 1
                    self.stream_stats[stream_id]['last_tick'] = datetime.utcnow().isoformat()

                    # Parse and enrich tick data
                    tick = self._parse_pricing_tick(response)

                    # Add to buffer
                    instrument = tick['instrument']
                    if instrument not in self.buffer:
                        self.buffer[instrument] = []
                    self.buffer[instrument].append(tick)

                    # Yield to consumer
                    yield tick

                elif response.get('type') == 'HEARTBEAT':
                    logger.debug(f"Heartbeat received for stream {stream_id}")
                    self.stream_stats[stream_id]['last_heartbeat'] = datetime.utcnow().isoformat()

        except asyncio.CancelledError:
            logger.info(f"Stream {stream_id} cancelled")
            raise

        except Exception as e:
            self.stream_stats[stream_id]['errors'] += 1
            logger.error(f"Error in pricing stream {stream_id}: {e}")
            raise

        finally:
            logger.info(
                f"Stream {stream_id} ended. "
                f"Ticks received: {self.stream_stats[stream_id]['ticks_received']}, "
                f"Errors: {self.stream_stats[stream_id]['errors']}"
            )

    def _parse_pricing_tick(self, raw_tick: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and enrich raw OANDA pricing tick

        Args:
            raw_tick: Raw tick data from OANDA

        Returns:
            Enriched tick dictionary
        """
        # Extract bid/ask prices
        bids = raw_tick.get('bids', [])
        asks = raw_tick.get('asks', [])

        if not bids or not asks:
            logger.warning(f"Incomplete tick data: {raw_tick}")
            return raw_tick

        # Best bid/ask
        best_bid = float(bids[0]['price'])
        best_ask = float(asks[0]['price'])

        # Calculate derived values
        mid_price = (best_bid + best_ask) / 2
        spread = best_ask - best_bid
        spread_pips = spread * 10000  # For forex pairs

        # Enrich tick
        enriched_tick = {
            'type': raw_tick.get('type'),
            'instrument': raw_tick.get('instrument'),
            'time': raw_tick.get('time'),
            'bids': bids,
            'asks': asks,
            'closeoutBid': raw_tick.get('closeoutBid'),
            'closeoutAsk': raw_tick.get('closeoutAsk'),
            'status': raw_tick.get('status'),
            'tradeable': raw_tick.get('tradeable'),

            # Computed fields
            'computed': {
                'best_bid': best_bid,
                'best_ask': best_ask,
                'mid_price': round(mid_price, 5),
                'spread': round(spread, 5),
                'spread_pips': round(spread_pips, 1),
                'bid_liquidity': bids[0].get('liquidity', 0),
                'ask_liquidity': asks[0].get('liquidity', 0)
            },

            # Collector metadata
            'collector_timestamp': datetime.utcnow().isoformat(),
            'collector_instance': self.config['service']['instance_id']
        }

        return enriched_tick

    async def get_buffered_ticks(self, instrument: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get buffered ticks for an instrument

        Args:
            instrument: Instrument symbol
            limit: Maximum number of ticks to return

        Returns:
            List of tick dictionaries
        """
        if instrument not in self.buffer:
            return []

        # Return last N ticks
        ticks = self.buffer[instrument][-limit:]
        return ticks

    async def flush_buffer(self, instrument: Optional[str] = None) -> int:
        """
        Flush buffered data

        Args:
            instrument: Specific instrument to flush, or None for all

        Returns:
            Number of ticks flushed
        """
        if instrument:
            if instrument in self.buffer:
                count = len(self.buffer[instrument])
                self.buffer[instrument] = []
                logger.debug(f"Flushed {count} ticks for {instrument}")
                return count
            return 0
        else:
            total = sum(len(ticks) for ticks in self.buffer.values())
            self.buffer = {}
            logger.debug(f"Flushed {total} total ticks")
            return total

    async def manage_buffer(self) -> None:
        """
        Background task to manage buffer size and flush interval
        """
        while True:
            try:
                await asyncio.sleep(self.flush_interval)

                # Check buffer sizes
                for instrument, ticks in list(self.buffer.items()):
                    if len(ticks) > self.buffer_size:
                        # Keep only last buffer_size ticks
                        self.buffer[instrument] = ticks[-self.buffer_size:]
                        logger.debug(
                            f"Trimmed buffer for {instrument} to {self.buffer_size} ticks"
                        )

                # Store buffer stats in Central Hub
                if self.memory_store:
                    await self._update_buffer_stats()

            except Exception as e:
                logger.error(f"Error in buffer management: {e}")

    async def _update_buffer_stats(self) -> None:
        """Update buffer statistics in Central Hub memory"""
        try:
            stats = {
                'timestamp': datetime.utcnow().isoformat(),
                'total_instruments': len(self.buffer),
                'total_buffered': sum(len(ticks) for ticks in self.buffer.values()),
                'instruments': {
                    instrument: len(ticks)
                    for instrument, ticks in self.buffer.items()
                }
            }

            await self.memory_store.set(
                f'buffer_stats:{self.config["service"]["instance_id"]}',
                stats
            )

        except Exception as e:
            logger.error(f"Failed to update buffer stats: {e}")

    def get_stream_stats(self, stream_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get streaming statistics

        Args:
            stream_id: Specific stream ID, or None for all

        Returns:
            Dict containing stream statistics
        """
        if stream_id:
            return self.stream_stats.get(stream_id, {})

        return {
            'active_streams': len(self.active_streams),
            'total_ticks': sum(
                stats['ticks_received']
                for stats in self.stream_stats.values()
            ),
            'total_errors': sum(
                stats['errors']
                for stats in self.stream_stats.values()
            ),
            'streams': self.stream_stats
        }

    def get_buffer_stats(self) -> Dict[str, Any]:
        """
        Get buffer statistics

        Returns:
            Dict containing buffer statistics
        """
        return {
            'total_instruments': len(self.buffer),
            'total_buffered': sum(len(ticks) for ticks in self.buffer.values()),
            'buffer_size_limit': self.buffer_size,
            'instruments': {
                instrument: {
                    'buffered_count': len(ticks),
                    'latest_tick': ticks[-1] if ticks else None
                }
                for instrument, ticks in self.buffer.items()
            }
        }

    async def cleanup(self) -> None:
        """
        Cleanup resources on shutdown
        """
        logger.info("Cleaning up stream manager")

        # Cancel active streams
        for stream_id, task in self.active_streams.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Clear buffers
        await self.flush_buffer()

        # Clear stats
        self.stream_stats.clear()
        self.active_streams.clear()

        logger.info("Stream manager cleanup complete")
