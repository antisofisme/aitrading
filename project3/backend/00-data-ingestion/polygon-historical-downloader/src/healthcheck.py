#!/usr/bin/env python3
"""
Health check script for Polygon Historical Downloader
Verifies all dependencies are ready before service starts
"""
import sys
import asyncio


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
        # Verify database exists
        result = client.command('SELECT 1')
        client.close()
        print("ClickHouse: ✅", flush=True)
        return True
    except Exception as e:
        print(f"ClickHouse: ❌ {e}", file=sys.stderr, flush=True)
        return False


async def check_nats():
    """Check NATS connection"""
    try:
        import nats
        import os

        # Use NATS cluster from environment variable (Central Hub v2.0 pattern)
        nats_url = os.getenv('NATS_URL', 'nats://nats-1:4222,nats://nats-2:4222,nats://nats-3:4222')
        servers = [url.strip() for url in nats_url.split(',')]

        nc = await nats.connect(
            servers=servers,
            connect_timeout=3
        )
        await nc.close()
        print("NATS: ✅", flush=True)
        return True
    except Exception as e:
        print(f"NATS: ❌ {e}", file=sys.stderr, flush=True)
        return False


async def check_central_hub():
    """Check Central Hub API health"""
    try:
        # Use aiohttp since it's available in requirements
        import aiohttp
        timeout = aiohttp.ClientTimeout(total=3)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get("http://suho-central-hub:7000/health") as response:
                if response.status == 200:
                    print("Central Hub: ✅", flush=True)
                    return True
                else:
                    print(f"Central Hub: ❌ Status {response.status}", file=sys.stderr, flush=True)
                    return False
    except Exception as e:
        print(f"Central Hub: ❌ {e}", file=sys.stderr, flush=True)
        return False


async def main():
    """Run all health checks"""
    print("🔍 Checking Historical Downloader dependencies...", flush=True)

    # Run synchronous checks first
    clickhouse_ok = check_clickhouse()

    # Run async checks
    results = await asyncio.gather(
        check_nats(),
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
        print("\n✅ All dependencies healthy - Historical Downloader ready to start", flush=True)
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
