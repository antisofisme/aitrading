"""
Central Hub SDK for Python

Official client library for integrating services with Suho Central Hub.

Usage:
    from central_hub_sdk import CentralHubClient

    client = CentralHubClient(
        service_name="my-service",
        service_type="data-collector",
        version="1.0.0"
    )

    await client.register()
    await client.start_heartbeat_loop()
"""

__version__ = "1.0.0"
__author__ = "Suho Trading System"

from .client import CentralHubClient

__all__ = ['CentralHubClient']
