#!/usr/bin/env python3
"""
Health check endpoint for Dukascopy Historical Downloader
Exit code 0 = healthy, 1 = unhealthy
"""
import sys
import os
import logging

# Setup logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_clickhouse_connection() -> bool:
    """Verify ClickHouse connectivity"""
    try:
        import clickhouse_connect

        host = os.getenv('CLICKHOUSE_HOST', 'suho-clickhouse')
        port = int(os.getenv('CLICKHOUSE_PORT', '9000'))
        user = os.getenv('CLICKHOUSE_USER', 'suho_analytics')
        password = os.getenv('CLICKHOUSE_PASSWORD', '')

        client = clickhouse_connect.get_client(
            host=host,
            port=port,
            username=user,
            password=password
        )

        # Simple query test
        result = client.query('SELECT 1')
        client.close()

        return result.result_rows[0][0] == 1
    except Exception as e:
        logger.error(f"ClickHouse check failed: {e}")
        return False


def check_nats_reachable() -> bool:
    """Verify NATS cluster is reachable (network check only)"""
    try:
        import socket

        nats_url = os.getenv('NATS_URL', 'nats://nats-1:4222,nats://nats-2:4222,nats://nats-3:4222')

        # Parse first NATS server
        if ',' in nats_url:
            first_url = nats_url.split(',')[0].strip()
        else:
            first_url = nats_url

        # Extract host and port from nats://host:port
        url_parts = first_url.replace('nats://', '').split(':')
        host = url_parts[0]
        port = int(url_parts[1]) if len(url_parts) > 1 else 4222

        # Simple socket connection test
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()

        return result == 0
    except Exception as e:
        logger.error(f"NATS reachability check failed: {e}")
        return False


def check_config_file() -> bool:
    """Verify configuration file exists"""
    try:
        from pathlib import Path

        config_file = Path('/app/config/pairs.yaml')
        return config_file.exists()
    except Exception as e:
        logger.error(f"Config file check failed: {e}")
        return False


def check_health() -> bool:
    """Run all health checks"""
    checks = [
        ("Configuration File", check_config_file()),
        ("ClickHouse Connection", check_clickhouse_connection()),
        ("NATS Reachability", check_nats_reachable()),
    ]

    all_healthy = all(status for _, status in checks)

    # Log results
    for name, status in checks:
        logger.info(f"{name}: {'✓' if status else '✗'}")

    return all_healthy


if __name__ == "__main__":
    try:
        is_healthy = check_health()
        sys.exit(0 if is_healthy else 1)
    except Exception as e:
        logger.error(f"Health check crashed: {e}", exc_info=True)
        sys.exit(1)
