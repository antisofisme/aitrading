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
            host='suho-postgresql',
            port=5432,
            database='suho_trading',
            user='suho_admin',
            password='suho_secure_password_2024',
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
        nc = await nats.connect(
            servers=["nats://suho-nats-server:4222"],
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
            host='suho-clickhouse',
            port=8123,
            username='suho_analytics',
            password='clickhouse_secure_2024',
            database='suho_analytics',
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

        producer = AIOKafkaProducer(
            bootstrap_servers='suho-kafka:9092',
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


async def check_central_hub():
    """Check Central Hub API health"""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get("http://suho-central-hub:7000/health")
            if response.status_code == 200:
                print("Central Hub: ✅", flush=True)
                return True
            else:
                print(f"Central Hub: ❌ Status {response.status_code}", file=sys.stderr, flush=True)
                return False
    except Exception as e:
        print(f"Central Hub: ❌ {e}", file=sys.stderr, flush=True)
        return False


async def main():
    """Run all health checks"""
    # Get instance identification
    instance_id = os.getenv('INSTANCE_ID', socket.gethostname())
    instance_number = os.getenv('INSTANCE_NUMBER', '1')

    print(f"🔍 Checking Data Bridge dependencies (Instance: {instance_id} #{instance_number})...", flush=True)

    # Run synchronous checks first
    clickhouse_ok = check_clickhouse()

    # Run async checks (including Kafka)
    results = await asyncio.gather(
        check_postgresql(),
        check_nats(),
        check_kafka(),
        check_central_hub(),
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
