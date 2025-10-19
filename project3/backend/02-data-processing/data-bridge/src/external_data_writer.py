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

            logger.debug(f"📥 Received external data | Type: {external_type} | Source: {data.get('_source')} | Topic: {data.get('_topic')}")

            if external_type not in self.buffers:
                logger.warning(f"⚠️  Unknown external data type: {external_type} | Available types: {list(self.buffers.keys())}")
                return

            # Extract actual data and metadata
            message_data = data.get('data', {})
            metadata = data.get('metadata', {})

            if not message_data:
                logger.warning(f"⚠️  Empty data for type {external_type} | Full message: {data}")
                return

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

            buffer_size = len(self.buffers[external_type])
            logger.debug(f"✅ Added to buffer | Type: {external_type} | Buffer size: {buffer_size}/{self.batch_size}")

            # Check if should flush
            should_flush_size = buffer_size >= self.batch_size
            time_since_flush = (datetime.utcnow() - self.last_flush[external_type]).total_seconds()
            should_flush_time = time_since_flush >= self.batch_timeout

            if should_flush_size or should_flush_time:
                flush_reason = "size" if should_flush_size else f"timeout ({time_since_flush:.1f}s)"
                logger.info(f"💾 Flushing buffer | Type: {external_type} | Reason: {flush_reason} | Size: {buffer_size}")
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

            # Parse date + time to event_time (DateTime64)
            event_date_str = data.get('date', '')
            event_time_str = data.get('time', '00:00')

            try:
                # Combine date + time → datetime
                from datetime import datetime as dt
                event_datetime_str = f"{event_date_str} {event_time_str}"
                event_time = dt.strptime(event_datetime_str, '%Y-%m-%d %H:%M')
                # Make timezone-aware (UTC)
                import pytz
                event_time = pytz.UTC.localize(event_time)
            except:
                event_time = datetime.utcnow()

            # Map impact: 'high'/'medium'/'low' or None → lowercase string
            impact = (data.get('impact') or 'low').lower()

            # Schema: event_time, currency, event_name, impact, forecast, previous, actual, scraped_at
            rows.append([
                event_time,  # DateTime64(3, 'UTC')
                data.get('currency') or '',  # String
                data.get('event') or '',  # event_name - String
                impact,  # Enum8('low', 'medium', 'high')
                data.get('forecast'),  # Nullable(String)
                data.get('previous'),  # Nullable(String)
                data.get('actual'),  # Nullable(String)
                item['collected_at']  # scraped_at - DateTime64(3, 'UTC')
            ])

        self.client.insert('external_economic_calendar', rows,
                          column_names=['event_time', 'currency', 'event_name', 'impact',
                                       'forecast', 'previous', 'actual', 'scraped_at'])

    async def _write_fred_economic(self, buffer: List[Dict]):
        """Write FRED economic indicators to ClickHouse"""
        rows = []
        for item in buffer:
            data = item['data']
            metadata = item['metadata']

            # Parse observation date (YYYY-MM-DD string → DateTime64 with 00:00:00 time)
            observation_date_str = data.get('date', '')
            if observation_date_str:
                try:
                    from datetime import datetime as dt
                    import pytz
                    # Parse date and set time to midnight UTC
                    release_time = dt.strptime(observation_date_str, '%Y-%m-%d')
                    release_time = pytz.UTC.localize(release_time)
                except:
                    release_time = datetime.utcnow()
            else:
                release_time = datetime.utcnow()

            # Schema: release_time, series_id, series_name, value, unit, scraped_at
            series_id = data.get('series_id', '')

            # Map series_id to series_name and unit
            series_mapping = {
                'GDP': ('Gross Domestic Product', 'Billions'),
                'UNRATE': ('Unemployment Rate', 'Percent'),
                'CPIAUCSL': ('Consumer Price Index', 'Index'),
                'DFF': ('Federal Funds Rate', 'Percent'),
                'DGS10': ('10-Year Treasury Rate', 'Percent'),
                'DEXUSEU': ('USD/EUR Exchange Rate', 'Rate'),
                'DEXJPUS': ('JPY/USD Exchange Rate', 'Rate')
            }

            series_name, unit = series_mapping.get(series_id, (series_id, 'Unknown'))

            rows.append([
                release_time,  # DateTime64(3, 'UTC')
                series_id,  # String
                series_name,  # String
                float(data.get('value') or 0),  # Float64
                unit,  # String
                item['collected_at']  # scraped_at - DateTime64(3, 'UTC')
            ])

        self.client.insert('external_fred_indicators', rows,
                          column_names=['release_time', 'series_id', 'series_name', 'value', 'unit', 'scraped_at'])

    async def _write_crypto_sentiment(self, buffer: List[Dict]):
        """Write crypto sentiment to ClickHouse"""
        rows = []
        for item in buffer:
            data = item['data']
            metadata = item['metadata']

            # Handle NULL values with defaults
            rows.append([
                data.get('coin_id', ''),
                data.get('name', ''),
                data.get('symbol', ''),
                float(data.get('price_usd') or 0),
                float(data.get('price_change_24h') or 0),
                int(data.get('market_cap_rank') or 0),
                float(data.get('sentiment_votes_up_percentage') or 0),
                float(data.get('community_score') or 0),
                int(data.get('twitter_followers') or 0),
                int(data.get('reddit_subscribers') or 0),
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

            # Parse timestamp (Unix timestamp string from API)
            timestamp_value = data.get('timestamp', '')
            if timestamp_value:
                try:
                    # Convert Unix timestamp (seconds) to datetime
                    from datetime import datetime
                    index_timestamp = datetime.utcfromtimestamp(int(timestamp_value))
                except:
                    index_timestamp = datetime.utcnow()
            else:
                from datetime import datetime
                index_timestamp = datetime.utcnow()

            # Handle NULL values with defaults
            rows.append([
                int(data.get('value') or 0),
                data.get('classification', ''),
                float(data.get('sentiment_score') or 0),
                index_timestamp,  # datetime object, not string
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

            # Schema: price_time, symbol, commodity_name, price, currency, change_pct, volume, scraped_at

            # Map symbol to commodity_name
            commodity_mapping = {
                'GC=F': 'Gold',
                'CL=F': 'Crude Oil',
                'SI=F': 'Silver',
                'HG=F': 'Copper',
                'NG=F': 'Natural Gas'
            }

            symbol = data.get('symbol', '')
            commodity_name = commodity_mapping.get(symbol, data.get('name', symbol))

            rows.append([
                item['collected_at'],  # price_time - DateTime64(3, 'UTC')
                symbol,  # String
                commodity_name,  # String
                float(data.get('price') or 0),  # Decimal(18,5)
                data.get('currency', 'USD'),  # String
                float(data.get('change_percent') or 0),  # change_pct - Float64
                int(data.get('volume') or 0),  # UInt64
                item['collected_at']  # scraped_at - DateTime64(3, 'UTC')
            ])

        self.client.insert('external_commodity_prices', rows,
                          column_names=['price_time', 'symbol', 'commodity_name', 'price',
                                       'currency', 'change_pct', 'volume', 'scraped_at'])

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
