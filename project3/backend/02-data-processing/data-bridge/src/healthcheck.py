#!/usr/bin/env python3
"""
Health check script for Data Bridge
Verifies all dependencies are ready before service starts
"""
import sys
import os
import socket
import asyncio


async def check_postgresql():
    """Check PostgreSQL/TimescaleDB connection"""
    try:
        import asyncpg
        conn = await asyncpg.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=int(os.getenv('POSTGRES_PORT', 5432)),
            database=os.getenv('POSTGRES_DB', 'suho_trading'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', ''),
            timeout=3
        )
        await conn.execute('SELECT 1')
        await conn.close()
        print("PostgreSQL: ✅", flush=True)
        return True
    except Exception as e:
        print(f"PostgreSQL: ❌ {e}", file=sys.stderr, flush=True)
        return False


async def check_nats():
    """Check NATS connection"""
    try:
        import nats
        nats_url = os.getenv('NATS_URL', 'nats://localhost:4222')
        # Take first URL if cluster (comma-separated)
        first_url = nats_url.split(',')[0].strip()
        nc = await nats.connect(
            servers=[first_url],
            connect_timeout=3
        )
        await nc.close()
        print("NATS: ✅", flush=True)
        return True
    except Exception as e:
        print(f"NATS: ❌ {e}", file=sys.stderr, flush=True)
        return False


def check_clickhouse():
    """Check ClickHouse connection"""
    try:
        import clickhouse_connect
        client = clickhouse_connect.get_client(
            host=os.getenv('CLICKHOUSE_HOST', 'localhost'),
            port=int(os.getenv('CLICKHOUSE_HTTP_PORT', 8123)),
            username=os.getenv('CLICKHOUSE_USER', 'default'),
            password=os.getenv('CLICKHOUSE_PASSWORD', ''),
            database=os.getenv('CLICKHOUSE_DATABASE', 'suho_analytics'),
            connect_timeout=3
        )
        client.ping()
        client.close()
        print("ClickHouse: ✅", flush=True)
        return True
    except Exception as e:
        print(f"ClickHouse: ❌ {e}", file=sys.stderr, flush=True)
        return False


async def check_kafka():
    """Check Kafka connection (non-critical - service has circuit breaker)"""
    try:
        from aiokafka import AIOKafkaProducer
        from aiokafka.errors import KafkaConnectionError

        kafka_brokers = os.getenv('KAFKA_BROKERS', 'localhost:9092')
        producer = AIOKafkaProducer(
            bootstrap_servers=kafka_brokers,
            request_timeout_ms=3000
        )
        await producer.start()
        await producer.stop()
        print("Kafka: ✅", flush=True)
        return True
    except KafkaConnectionError:
        print("Kafka: ⚠️  Not available (service will use circuit breaker)", flush=True)
        return True  # Non-critical: circuit breaker handles Kafka issues
    except Exception as e:
        print(f"Kafka: ⚠️  {e} (service will use circuit breaker)", flush=True)
        return True  # Non-critical: circuit breaker handles Kafka issues


async def check_dragonflydb():
    """Check DragonflyDB connection"""
    try:
        import redis.asyncio as redis
        client = redis.Redis(
            host=os.getenv('DRAGONFLY_HOST', 'localhost'),
            port=int(os.getenv('DRAGONFLY_PORT', 6379)),
            password=os.getenv('DRAGONFLY_PASSWORD', None),
            db=int(os.getenv('DRAGONFLY_DB', 0)),
            socket_connect_timeout=3
        )
        await client.ping()
        await client.aclose()
        print("DragonflyDB: ✅", flush=True)
        return True
    except Exception as e:
        print(f"DragonflyDB: ❌ {e}", file=sys.stderr, flush=True)
        return False


async def main():
    """Run all health checks"""
    # Get instance identification
    instance_id = os.getenv('INSTANCE_ID', socket.gethostname())
    instance_number = os.getenv('INSTANCE_NUMBER', '1')

    print(f"🔍 Checking Data Bridge dependencies (Instance: {instance_id} #{instance_number})...", flush=True)

    # Run synchronous checks first
    clickhouse_ok = check_clickhouse()

    # Run async checks
    results = await asyncio.gather(
        check_postgresql(),
        check_dragonflydb(),
        check_nats(),
        check_kafka(),
        return_exceptions=True
    )

    # Process results
    checks = [clickhouse_ok]
    for result in results:
        if isinstance(result, Exception):
            print(f"Check failed with exception: {result}", file=sys.stderr, flush=True)
            checks.append(False)
        else:
            checks.append(result)

    # Final verdict
    failed_count = checks.count(False)
    if all(checks):
        print("\n✅ All dependencies healthy - Data Bridge ready to start", flush=True)
        sys.exit(0)
    else:
        print(f"\n❌ {failed_count} dependencies not ready - cannot start service", file=sys.stderr, flush=True)
        sys.exit(1)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Health check interrupted", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Health check failed: {e}", file=sys.stderr)
        sys.exit(1)
