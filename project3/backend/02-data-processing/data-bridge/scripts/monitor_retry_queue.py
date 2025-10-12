#!/usr/bin/env python3
"""
Retry Queue Monitoring Script

Monitor the health and performance of the Data Bridge retry queue system.

Usage:
    python monitor_retry_queue.py                 # Single check
    python monitor_retry_queue.py --watch         # Continuous monitoring
    python monitor_retry_queue.py --dlq           # Show DLQ messages
    python monitor_retry_queue.py --replay ID     # Replay specific DLQ message

Requirements:
    - PostgreSQL connection to suho_analytics database
    - Environment variables: POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD
"""
import asyncio
import asyncpg
import os
import sys
import json
from datetime import datetime, timezone
from typing import Optional


class RetryQueueMonitor:
    """Monitor for Data Bridge retry queue and DLQ"""

    def __init__(self, pg_pool):
        self.pg_pool = pg_pool

    async def get_dlq_stats(self) -> dict:
        """Get Dead Letter Queue statistics"""
        async with self.pg_pool.acquire() as conn:
            # Total messages in DLQ
            total = await conn.fetchval("SELECT COUNT(*) FROM data_bridge_dlq")

            # Unreplayed messages
            unreplayed = await conn.fetchval(
                "SELECT COUNT(*) FROM data_bridge_dlq WHERE replayed = FALSE"
            )

            # Messages by type
            by_type = await conn.fetch(
                """
                SELECT message_type, COUNT(*) as count
                FROM data_bridge_dlq
                WHERE replayed = FALSE
                GROUP BY message_type
                ORDER BY count DESC
                """
            )

            # Recent failures (last hour)
            recent = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM data_bridge_dlq
                WHERE created_at > NOW() - INTERVAL '1 hour'
                """
            )

            # Most common errors
            errors = await conn.fetch(
                """
                SELECT
                    SUBSTRING(last_error, 1, 100) as error_snippet,
                    COUNT(*) as count
                FROM data_bridge_dlq
                WHERE replayed = FALSE
                GROUP BY error_snippet
                ORDER BY count DESC
                LIMIT 5
                """
            )

            return {
                'total': total,
                'unreplayed': unreplayed,
                'replayed': total - unreplayed,
                'by_type': {row['message_type']: row['count'] for row in by_type},
                'recent_1h': recent,
                'top_errors': [
                    {'error': row['error_snippet'], 'count': row['count']}
                    for row in errors
                ]
            }

    async def get_dlq_messages(
        self,
        limit: int = 50,
        message_type: Optional[str] = None,
        replayed: bool = False
    ) -> list:
        """Get messages from DLQ"""
        query = """
            SELECT
                id,
                correlation_id,
                message_type,
                message_data,
                retry_count,
                first_attempt_time,
                last_error,
                priority,
                replayed,
                created_at
            FROM data_bridge_dlq
            WHERE replayed = $1
        """

        params = [replayed]

        if message_type:
            query += " AND message_type = $2"
            params.append(message_type)

        query += " ORDER BY priority ASC, created_at DESC LIMIT $" + str(len(params) + 1)
        params.append(limit)

        async with self.pg_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]

    async def replay_message(self, message_id: int, notes: str = "Manual replay") -> bool:
        """
        Mark a DLQ message as ready for replay

        NOTE: This only marks the message - actual replay requires
        re-sending to ClickHouse Writer manually or via replay script
        """
        async with self.pg_pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE data_bridge_dlq
                SET replayed = TRUE, replayed_at = NOW(), replay_notes = $2
                WHERE id = $1
                """,
                message_id, notes
            )
            return result == "UPDATE 1"

    async def print_stats(self):
        """Print DLQ statistics to console"""
        stats = await self.get_dlq_stats()

        print("\n" + "=" * 80)
        print("RETRY QUEUE & DEAD LETTER QUEUE STATISTICS")
        print("=" * 80)
        print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
        print()

        print(f"📊 Total DLQ Messages:      {stats['total']}")
        print(f"   ├─ Unreplayed:           {stats['unreplayed']}")
        print(f"   └─ Replayed:             {stats['replayed']}")
        print()

        print(f"🕐 Recent Failures (1h):    {stats['recent_1h']}")
        print()

        if stats['by_type']:
            print("📦 Messages by Type:")
            for msg_type, count in stats['by_type'].items():
                print(f"   ├─ {msg_type:15s} {count:>6d}")
            print()

        if stats['top_errors']:
            print("❌ Top Error Messages:")
            for i, error in enumerate(stats['top_errors'], 1):
                print(f"   {i}. [{error['count']:>3d}x] {error['error']}")
            print()

        # Health assessment
        if stats['unreplayed'] == 0:
            print("✅ HEALTH: Excellent - No messages in DLQ")
        elif stats['unreplayed'] < 100:
            print(f"⚠️  HEALTH: Warning - {stats['unreplayed']} messages in DLQ")
        else:
            print(f"🔴 HEALTH: Critical - {stats['unreplayed']} messages in DLQ!")

        print("=" * 80 + "\n")

    async def print_dlq_messages(self, limit: int = 20):
        """Print recent DLQ messages"""
        messages = await self.get_dlq_messages(limit=limit)

        print("\n" + "=" * 80)
        print(f"RECENT DLQ MESSAGES (showing {len(messages)} of {limit})")
        print("=" * 80)

        for msg in messages:
            print(f"\n📋 ID: {msg['id']} | Correlation: {msg['correlation_id']}")
            print(f"   Type:     {msg['message_type']}")
            print(f"   Priority: {msg['priority']} (1=HIGH, 2=MEDIUM, 3=LOW)")
            print(f"   Retries:  {msg['retry_count']}")
            print(f"   Created:  {msg['created_at']}")
            print(f"   Error:    {msg['last_error'][:100]}...")

            # Show message data preview
            data = msg['message_data']
            if isinstance(data, str):
                data = json.loads(data)
            print(f"   Symbol:   {data.get('symbol', 'N/A')}")
            print(f"   Time:     {data.get('timeframe', 'N/A')}")
            print(f"   Source:   {data.get('source', 'N/A')}")

        print("=" * 80 + "\n")

    async def watch(self, interval: int = 30):
        """Continuously monitor DLQ (refresh every N seconds)"""
        print("🔄 Starting continuous monitoring (Ctrl+C to stop)...")
        print(f"Refresh interval: {interval} seconds\n")

        try:
            while True:
                await self.print_stats()
                await asyncio.sleep(interval)
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped")


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Monitor Data Bridge Retry Queue")
    parser.add_argument('--watch', action='store_true', help='Continuous monitoring')
    parser.add_argument('--interval', type=int, default=30, help='Watch interval (seconds)')
    parser.add_argument('--dlq', action='store_true', help='Show DLQ messages')
    parser.add_argument('--limit', type=int, default=20, help='Number of DLQ messages to show')
    parser.add_argument('--replay', type=int, help='Replay specific DLQ message by ID')
    parser.add_argument('--notes', type=str, default='Manual replay', help='Replay notes')

    args = parser.parse_args()

    # Get PostgreSQL connection details from environment
    pg_host = os.getenv('POSTGRES_HOST', 'localhost')
    pg_port = int(os.getenv('POSTGRES_PORT', 5432))
    pg_database = os.getenv('POSTGRES_DATABASE', 'suho_analytics')
    pg_user = os.getenv('POSTGRES_USER', 'postgres')
    pg_password = os.getenv('POSTGRES_PASSWORD', '')

    # Create connection pool
    try:
        pg_pool = await asyncpg.create_pool(
            host=pg_host,
            port=pg_port,
            database=pg_database,
            user=pg_user,
            password=pg_password,
            min_size=1,
            max_size=3,
            command_timeout=30
        )
        print(f"✅ Connected to PostgreSQL: {pg_host}:{pg_port}/{pg_database}\n")
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        sys.exit(1)

    monitor = RetryQueueMonitor(pg_pool)

    try:
        if args.replay:
            # Replay specific message
            success = await monitor.replay_message(args.replay, args.notes)
            if success:
                print(f"✅ Message {args.replay} marked for replay")
            else:
                print(f"❌ Failed to mark message {args.replay} for replay")

        elif args.dlq:
            # Show DLQ messages
            await monitor.print_dlq_messages(limit=args.limit)

        elif args.watch:
            # Continuous monitoring
            await monitor.watch(interval=args.interval)

        else:
            # Single stats check
            await monitor.print_stats()

    finally:
        await pg_pool.close()


if __name__ == '__main__':
    asyncio.run(main())
