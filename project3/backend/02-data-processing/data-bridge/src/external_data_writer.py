"""
ClickHouse External Data Writer
Handles writing external market data (economic calendar, sentiment, etc.) to ClickHouse
"""
import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
import clickhouse_connect

logger = logging.getLogger(__name__)


class ExternalDataWriter:
    """
    ClickHouse writer for external market data

    Handles 6 data types:
    1. Economic Calendar (MQL5)
    2. FRED Economic Indicators
    3. Crypto Sentiment (CoinGecko)
    4. Fear & Greed Index
    5. Commodity Prices (Yahoo Finance)
    6. Market Sessions
    """

    def __init__(self, clickhouse_config: Dict[str, Any]):
        """
        Initialize external data writer

        Args:
            clickhouse_config: ClickHouse connection config
        """
        self.config = clickhouse_config
        self.client = None

        # Buffers for batch inserts (by data type)
        self.buffers = {
            'economic_calendar': [],
            'fred_economic': [],
            'crypto_sentiment': [],
            'fear_greed_index': [],
            'commodity_prices': [],
            'market_sessions': []
        }

        # Batch settings
        self.batch_size = 100
        self.batch_timeout = 5  # seconds
        self.last_flush = {key: datetime.utcnow() for key in self.buffers.keys()}

        # Statistics
        self.stats = {key: 0 for key in self.buffers.keys()}
        self.errors = 0

        logger.info("ExternalDataWriter initialized")

    async def connect(self):
        """Connect to ClickHouse"""
        try:
            connection_config = self.config.get('connection', {})

            # Get connection params (same pattern as clickhouse_writer.py)
            host = connection_config.get('host', 'localhost')
            port = connection_config.get('http_port', connection_config.get('port', 8123))
            database = connection_config.get('database', 'suho_analytics')
            username = connection_config.get('username', connection_config.get('user', 'default'))
            password = connection_config.get('password', '')

            self.client = clickhouse_connect.get_client(
                host=host,
                port=int(port),
                username=username,
                password=password,
                database=database
            )

            # Test connection
            self.client.command('SELECT 1')

            logger.info(f"✅ Connected to ClickHouse for External Data: {host}:{port}")

        except Exception as e:
            logger.error(f"❌ ClickHouse connection failed: {e}")
            raise

    async def write_external_data(self, data: Dict[str, Any]):
        """
        Write external data to ClickHouse

        Args:
            data: External data message with metadata
        """
        try:
            # Extract data type
            external_type = data.get('_external_type', 'unknown')

            if external_type not in self.buffers:
                logger.warning(f"⚠️  Unknown external data type: {external_type}")
                return

            # Extract actual data and metadata
            message_data = data.get('data', {})
            metadata = data.get('metadata', {})

            # Parse collected_at timestamp (string → datetime)
            collected_at_str = metadata.get('timestamp', datetime.utcnow().isoformat())
            try:
                # Parse ISO string to datetime
                if isinstance(collected_at_str, str):
                    collected_at = datetime.fromisoformat(collected_at_str.replace('Z', '+00:00'))
                else:
                    collected_at = collected_at_str
            except:
                collected_at = datetime.utcnow()

            # Add to buffer
            self.buffers[external_type].append({
                'data': message_data,
                'metadata': metadata,
                'collected_at': collected_at  # datetime object, not string
            })

            # Check if should flush
            should_flush_size = len(self.buffers[external_type]) >= self.batch_size
            should_flush_time = (datetime.utcnow() - self.last_flush[external_type]).total_seconds() >= self.batch_timeout

            if should_flush_size or should_flush_time:
                await self._flush_buffer(external_type)

        except Exception as e:
            logger.error(f"❌ Error writing external data: {e}")
            self.errors += 1

    async def _flush_buffer(self, data_type: str):
        """Flush buffer for specific data type"""
        if not self.buffers[data_type]:
            return

        buffer = self.buffers[data_type]
        count = len(buffer)

        try:
            # Route to appropriate writer
            if data_type == 'economic_calendar':
                await self._write_economic_calendar(buffer)
            elif data_type == 'fred_economic':
                await self._write_fred_economic(buffer)
            elif data_type == 'crypto_sentiment':
                await self._write_crypto_sentiment(buffer)
            elif data_type == 'fear_greed_index':
                await self._write_fear_greed_index(buffer)
            elif data_type == 'commodity_prices':
                await self._write_commodity_prices(buffer)
            elif data_type == 'market_sessions':
                await self._write_market_sessions(buffer)

            # Clear buffer
            self.buffers[data_type] = []
            self.last_flush[data_type] = datetime.utcnow()
            self.stats[data_type] += count

            logger.info(f"✅ Flushed {count} {data_type} records | Total: {self.stats[data_type]}")

        except Exception as e:
            logger.error(f"❌ Error flushing {data_type}: {e}")
            self.errors += 1

    async def _write_economic_calendar(self, buffer: List[Dict]):
        """Write economic calendar events to ClickHouse"""
        rows = []
        for item in buffer:
            data = item['data']
            metadata = item['metadata']

            rows.append([
                data.get('date'),
                data.get('time'),
                data.get('currency'),
                data.get('event'),
                data.get('forecast'),
                data.get('previous'),
                data.get('actual'),
                data.get('impact'),
                metadata.get('source', 'mql5'),
                item['collected_at']  # datetime object
            ])

        self.client.insert('external_economic_calendar', rows,
                          column_names=['date', 'time', 'currency', 'event', 'forecast',
                                       'previous', 'actual', 'impact', 'source', 'collected_at'])

    async def _write_fred_economic(self, buffer: List[Dict]):
        """Write FRED economic indicators to ClickHouse"""
        rows = []
        for item in buffer:
            data = item['data']
            metadata = item['metadata']

            rows.append([
                data.get('series_id'),
                data.get('value'),
                data.get('date'),
                metadata.get('source', 'fred'),
                item['collected_at']  # datetime object
            ])

        self.client.insert('external_fred_economic', rows,
                          column_names=['series_id', 'value', 'observation_date', 'source', 'collected_at'])

    async def _write_crypto_sentiment(self, buffer: List[Dict]):
        """Write crypto sentiment to ClickHouse"""
        rows = []
        for item in buffer:
            data = item['data']
            metadata = item['metadata']

            rows.append([
                data.get('coin_id'),
                data.get('name'),
                data.get('symbol'),
                data.get('price_usd'),
                data.get('price_change_24h'),
                data.get('market_cap_rank'),
                data.get('sentiment_votes_up_percentage'),
                data.get('community_score'),
                data.get('twitter_followers'),
                data.get('reddit_subscribers'),
                metadata.get('source', 'coingecko'),
                item['collected_at']  # datetime object
            ])

        self.client.insert('external_crypto_sentiment', rows,
                          column_names=['coin_id', 'name', 'symbol', 'price_usd', 'price_change_24h',
                                       'market_cap_rank', 'sentiment_votes_up', 'community_score',
                                       'twitter_followers', 'reddit_subscribers', 'source', 'collected_at'])

    async def _write_fear_greed_index(self, buffer: List[Dict]):
        """Write fear & greed index to ClickHouse"""
        rows = []
        for item in buffer:
            data = item['data']
            metadata = item['metadata']

            rows.append([
                data.get('value'),
                data.get('classification'),
                data.get('sentiment_score'),
                data.get('timestamp'),
                metadata.get('source', 'alternative.me'),
                item['collected_at']  # datetime object
            ])

        self.client.insert('external_fear_greed_index', rows,
                          column_names=['value', 'classification', 'sentiment_score',
                                       'index_timestamp', 'source', 'collected_at'])

    async def _write_commodity_prices(self, buffer: List[Dict]):
        """Write commodity prices to ClickHouse"""
        rows = []
        for item in buffer:
            data = item['data']
            metadata = item['metadata']

            rows.append([
                data.get('symbol'),
                data.get('name'),
                data.get('currency'),
                data.get('price'),
                data.get('previous_close'),
                data.get('change'),
                data.get('change_percent'),
                data.get('volume'),
                metadata.get('source', 'yahoo'),
                item['collected_at']  # datetime object
            ])

        self.client.insert('external_commodity_prices', rows,
                          column_names=['symbol', 'name', 'currency', 'price', 'previous_close',
                                       'change', 'change_percent', 'volume', 'source', 'collected_at'])

    async def _write_market_sessions(self, buffer: List[Dict]):
        """Write market sessions to ClickHouse"""
        rows = []
        for item in buffer:
            data = item['data']
            metadata = item['metadata']

            rows.append([
                data.get('current_utc_time'),
                data.get('active_sessions_count'),
                ','.join(data.get('active_sessions', [])),
                data.get('liquidity_level'),
                item['collected_at']  # datetime object
            ])

        self.client.insert('external_market_sessions', rows,
                          column_names=['current_utc_time', 'active_sessions_count',
                                       'active_sessions', 'liquidity_level', 'collected_at'])

    async def flush_all(self):
        """Flush all buffers"""
        for data_type in self.buffers.keys():
            await self._flush_buffer(data_type)

    def get_stats(self) -> Dict[str, Any]:
        """Get writer statistics"""
        return {
            **self.stats,
            'total': sum(self.stats.values()),
            'errors': self.errors
        }

    async def close(self):
        """Close connection and flush remaining data"""
        logger.info("Closing ExternalDataWriter...")

        # Flush all remaining data
        await self.flush_all()

        if self.client:
            self.client.close()

        logger.info("✅ ExternalDataWriter closed")
