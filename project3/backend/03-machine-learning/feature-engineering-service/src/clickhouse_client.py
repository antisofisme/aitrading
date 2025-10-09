"""
ClickHouse Client for Feature Engineering Service

Responsibilities:
1. Read from aggregates table (OHLCV + 26 indicators)
2. Read from 6 external data tables
3. Write to ml_training_data table
"""

import logging
import pandas as pd
import clickhouse_connect
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)


class ClickHouseClient:
    """ClickHouse client for ML feature engineering"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = None

        logger.info("📊 ClickHouse Client initialized")

    async def connect(self):
        """Connect to ClickHouse"""
        try:
            connection_config = self.config.get('connection', {})

            host = connection_config.get('host', 'localhost')
            port = connection_config.get('http_port', connection_config.get('port', 8123))
            database = connection_config.get('database', 'suho_analytics')
            username = connection_config.get('username', connection_config.get('user', 'default'))
            password = connection_config.get('password', '')

            self.client = clickhouse_connect.get_client(
                host=host,
                port=int(port),
                database=database,
                username=username,
                password=password,
                connect_timeout=30,
                send_receive_timeout=300
            )

            # Test connection
            self.client.command('SELECT 1')

            logger.info(f"✅ Connected to ClickHouse: {host}:{port} (database: {database})")

        except Exception as e:
            logger.error(f"❌ ClickHouse connection failed: {e}")
            raise

    async def query(self, sql: str) -> pd.DataFrame:
        """
        Execute SELECT query and return DataFrame

        Args:
            sql: SQL query string

        Returns:
            pd.DataFrame with query results
        """
        try:
            result = self.client.query(sql)

            # Convert to DataFrame
            if result.result_rows:
                df = pd.DataFrame(result.result_rows, columns=result.column_names)
                logger.debug(f"✅ Query returned {len(df)} rows")
                return df
            else:
                logger.warning("⚠️ Query returned 0 rows")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"❌ Query failed: {e}")
            logger.error(f"SQL: {sql[:200]}...")  # Log first 200 chars
            raise

    async def get_aggregates(
        self,
        symbol: str,
        timeframe: str,
        start_time: str,
        end_time: str
    ) -> pd.DataFrame:
        """
        Get aggregates data for feature calculation

        Args:
            symbol: Trading pair (e.g., 'XAU/USD')
            timeframe: Timeframe (e.g., '1h')
            start_time: Start timestamp (ISO format)
            end_time: End timestamp (ISO format)

        Returns:
            DataFrame with OHLCV + indicators
        """
        query = f"""
        SELECT
            symbol, timeframe, timestamp, timestamp_ms,
            open, high, low, close, volume,
            vwap, range_pips, body_pips,
            start_time, end_time, source,
            indicators
        FROM aggregates
        WHERE symbol = '{symbol}'
          AND timeframe = '{timeframe}'
          AND timestamp >= toDateTime('{start_time}')
          AND timestamp <= toDateTime('{end_time}')
        ORDER BY timestamp ASC
        """

        df = await self.query(query)

        # Parse indicators JSON
        if not df.empty and 'indicators' in df.columns:
            df['indicators_parsed'] = df['indicators'].apply(
                lambda x: json.loads(x) if x else {}
            )

        return df

    async def get_multi_timeframe_aggregates(
        self,
        symbol: str,
        timestamp: pd.Timestamp,
        lookback_candles: int = 200
    ) -> Dict[str, pd.DataFrame]:
        """
        Get multi-timeframe aggregates for a specific timestamp

        Args:
            symbol: Trading pair
            timestamp: Reference timestamp (H1)
            lookback_candles: Number of candles to look back

        Returns:
            Dict of {timeframe: DataFrame}
        """
        timeframes = ['5m', '15m', '1h', '4h', '1d', '1w']
        results = {}

        for tf in timeframes:
            # Calculate lookback time based on timeframe
            if tf == '5m':
                lookback_hours = lookback_candles * 5 / 60
            elif tf == '15m':
                lookback_hours = lookback_candles * 15 / 60
            elif tf == '1h':
                lookback_hours = lookback_candles
            elif tf == '4h':
                lookback_hours = lookback_candles * 4
            elif tf == '1d':
                lookback_hours = lookback_candles * 24
            else:  # 1w
                lookback_hours = lookback_candles * 24 * 7

            start_time = timestamp - pd.Timedelta(hours=lookback_hours)

            df = await self.get_aggregates(
                symbol=symbol,
                timeframe=tf,
                start_time=start_time.isoformat(),
                end_time=timestamp.isoformat()
            )

            results[tf] = df

        logger.debug(f"✅ Fetched multi-TF data: {[f'{k}={len(v)}' for k, v in results.items()]}")

        return results

    async def get_external_data(
        self,
        timestamp: pd.Timestamp,
        lookback_hours: int = 24
    ) -> Dict[str, pd.DataFrame]:
        """
        Get external data for feature calculation

        Args:
            timestamp: Reference timestamp
            lookback_hours: Hours to look back

        Returns:
            Dict of {table_name: DataFrame}
        """
        start_time = timestamp - pd.Timedelta(hours=lookback_hours)
        results = {}

        # 1. Economic Calendar
        query = f"""
        SELECT *
        FROM external_economic_calendar
        WHERE collected_at >= toDateTime('{start_time.isoformat()}')
          AND collected_at <= toDateTime('{timestamp.isoformat()}')
        ORDER BY collected_at DESC
        """
        results['economic_calendar'] = await self.query(query)

        # 2. Market Sessions
        query = f"""
        SELECT *
        FROM external_market_sessions
        WHERE collected_at >= toDateTime('{start_time.isoformat()}')
          AND collected_at <= toDateTime('{timestamp.isoformat()}')
        ORDER BY collected_at DESC
        LIMIT 1
        """
        results['market_sessions'] = await self.query(query)

        # 3. Fear & Greed Index
        query = f"""
        SELECT *
        FROM external_fear_greed_index
        WHERE collected_at >= toDateTime('{start_time.isoformat()}')
          AND collected_at <= toDateTime('{timestamp.isoformat()}')
        ORDER BY collected_at DESC
        LIMIT 1
        """
        results['fear_greed'] = await self.query(query)

        # 4. Commodity Prices
        query = f"""
        SELECT *
        FROM external_commodity_prices
        WHERE collected_at >= toDateTime('{start_time.isoformat()}')
          AND collected_at <= toDateTime('{timestamp.isoformat()}')
        ORDER BY collected_at DESC
        """
        results['commodity_prices'] = await self.query(query)

        # 5. Crypto Sentiment
        query = f"""
        SELECT *
        FROM external_crypto_sentiment
        WHERE collected_at >= toDateTime('{start_time.isoformat()}')
          AND collected_at <= toDateTime('{timestamp.isoformat()}')
        ORDER BY collected_at DESC
        """
        results['crypto_sentiment'] = await self.query(query)

        # 6. FRED Economic
        query = f"""
        SELECT *
        FROM external_fred_economic
        WHERE collected_at >= toDateTime('{start_time.isoformat()}')
          AND collected_at <= toDateTime('{timestamp.isoformat()}')
        ORDER BY collected_at DESC
        """
        results['fred_economic'] = await self.query(query)

        logger.debug(f"✅ Fetched external data: {[f'{k}={len(v)}' for k, v in results.items()]}")

        return results

    async def insert_training_data(self, df: pd.DataFrame):
        """
        Insert feature data to ml_training_data table

        Args:
            df: DataFrame with 63 features + metadata
        """
        if df.empty:
            logger.warning("⚠️ No data to insert")
            return

        try:
            # Prepare data for insertion
            data = df.to_dict('records')

            # Convert to list of lists
            rows = [list(row.values()) for row in data]
            column_names = list(df.columns)

            # Insert to ClickHouse
            self.client.insert(
                'ml_training_data',
                rows,
                column_names=column_names
            )

            logger.info(f"✅ Inserted {len(df)} rows to ml_training_data table")

        except Exception as e:
            logger.error(f"❌ Insert failed: {e}")
            raise

    async def close(self):
        """Close connection"""
        if self.client:
            self.client.close()
            logger.info("✅ ClickHouse connection closed")
