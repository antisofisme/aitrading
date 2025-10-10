"""
Central Hub SDK for Python

Official client library for integrating services with Suho Central Hub.

Usage:
    from central_hub_sdk import CentralHubClient, ProgressLogger

    # Service registration
    client = CentralHubClient(
        service_name="my-service",
        service_type="data-collector",
        version="1.0.0"
    )

    await client.register()
    await client.start_heartbeat_loop()

    # Progress tracking
    progress = ProgressLogger(
        task_name="Processing data",
        total_items=100,
        milestones=[25, 50, 75, 100],
        heartbeat_interval=30
    )

    progress.start()
    for i in range(100):
        process_item(i)
        progress.update(current=i+1)
    progress.complete()
"""

__version__ = "1.0.0"
__author__ = "Suho Trading System"

from .client import CentralHubClient
from .progress_logger import ProgressLogger
from .heartbeat_logger import HeartbeatLogger

__all__ = ['CentralHubClient', 'ProgressLogger', 'HeartbeatLogger']
