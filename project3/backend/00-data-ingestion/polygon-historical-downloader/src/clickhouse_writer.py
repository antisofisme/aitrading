"""
ClickHouse Writer for Historical Data
"""
import logging
from typing import List, Dict
from clickhouse_driver import Client

logger = logging.getLogger(__name__)

class ClickHouseWriter:
    def __init__(self, config: dict):
        self.config = config
        self.client = Client(
            host=config.get('host', 'suho-clickhouse'),
            port=config.get('port', 9000),
            user=config.get('user', 'suho_analytics'),
            password=config['password'],
            database=config.get('database', 'suho_analytics')
        )

        self.table = config.get('table', 'ticks')
        self.insert_count = 0

        # Create table if needed
        if config.get('auto_create_table', True):
            self._create_table()

    def _create_table(self):
        """Create ticks table if not exists"""
        try:
            create_table_sql = f"""
                CREATE TABLE IF NOT EXISTS {self.table} (
                    symbol String,
                    timestamp DateTime64(3),
                    timestamp_ms Int64,
                    open Float64,
                    high Float64,
                    low Float64,
                    close Float64,
                    bid Float64,
                    ask Float64,
                    mid Float64,
                    volume UInt64,
                    vwap Float64,
                    num_trades UInt32,
                    source String
                ) ENGINE = MergeTree()
                PARTITION BY toYYYYMM(timestamp)
                ORDER BY (symbol, timestamp)
                SETTINGS index_granularity = 8192
            """

            self.client.execute(create_table_sql)
            logger.info(f"✅ Table {self.table} ready")

        except Exception as e:
            logger.error(f"Error creating table: {e}")

    def bulk_insert(self, data: List[Dict]):
        """Bulk insert tick data"""
        if not data:
            return

        try:
            # Prepare rows
            rows = []
            for tick in data:
                rows.append((
                    tick.get('symbol'),
                    tick.get('timestamp'),
                    tick.get('timestamp_ms'),
                    tick.get('open', 0),
                    tick.get('high', 0),
                    tick.get('low', 0),
                    tick.get('close', 0),
                    tick.get('bid', 0),
                    tick.get('ask', 0),
                    tick.get('mid', 0),
                    tick.get('volume', 0),
                    tick.get('vwap', 0),
                    tick.get('num_trades', 0),
                    tick.get('source', 'polygon_historical')
                ))

            # Insert
            insert_sql = f"""
                INSERT INTO {self.table}
                (symbol, timestamp, timestamp_ms, open, high, low, close, bid, ask, mid, volume, vwap, num_trades, source)
                VALUES
            """

            self.client.execute(insert_sql, rows)
            self.insert_count += len(rows)

            logger.info(f"✅ Inserted {len(rows)} records (Total: {self.insert_count})")

        except Exception as e:
            logger.error(f"Error inserting data: {e}")

    def get_stats(self) -> dict:
        """Get writer statistics"""
        return {
            'insert_count': self.insert_count
        }
