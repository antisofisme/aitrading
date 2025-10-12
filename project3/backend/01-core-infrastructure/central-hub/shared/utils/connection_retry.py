#!/usr/bin/env python3
"""
Connection Retry Utility
Provides exponential backoff retry logic for service connections
"""
import asyncio
import logging
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)


async def connect_with_retry(
    connect_func: Callable,
    service_name: str,
    max_retries: int = 10,
    initial_backoff: float = 1.0,
    max_backoff: float = 30.0,
    backoff_multiplier: float = 2.0
) -> Any:
    """
    Connect to service with exponential backoff retry logic

    Args:
        connect_func: Async function to call for connection (can be coroutine or regular function)
        service_name: Name for logging purposes
        max_retries: Maximum retry attempts (default: 10)
        initial_backoff: Initial backoff in seconds (default: 1.0)
        max_backoff: Maximum backoff in seconds (default: 30.0)
        backoff_multiplier: Multiplier for exponential backoff (default: 2.0)

    Returns:
        Result from connect_func if successful

    Raises:
        Exception: If all retries exhausted
    """
    backoff = initial_backoff

    for attempt in range(1, max_retries + 1):
        try:
            # Check if function is a coroutine
            if asyncio.iscoroutinefunction(connect_func):
                result = await connect_func()
            else:
                result = connect_func()

            logger.info(f"✅ Connected to {service_name} (attempt {attempt}/{max_retries})")
            return result

        except Exception as e:
            if attempt < max_retries:
                logger.warning(
                    f"⚠️ {service_name} not ready (attempt {attempt}/{max_retries}). "
                    f"Retrying in {backoff:.1f}s... Error: {e}"
                )
                await asyncio.sleep(backoff)
                # Exponential backoff with cap
                backoff = min(backoff * backoff_multiplier, max_backoff)
            else:
                logger.error(
                    f"❌ Failed to connect to {service_name} after {max_retries} attempts. "
                    f"Last error: {e}"
                )
                raise

    # Should never reach here, but just in case
    raise RuntimeError(f"Unexpected error in retry logic for {service_name}")


def sync_connect_with_retry(
    connect_func: Callable,
    service_name: str,
    max_retries: int = 10,
    initial_backoff: float = 1.0,
    max_backoff: float = 30.0,
    backoff_multiplier: float = 2.0
) -> Any:
    """
    Synchronous version of connect_with_retry

    Args:
        connect_func: Synchronous function to call for connection
        service_name: Name for logging purposes
        max_retries: Maximum retry attempts (default: 10)
        initial_backoff: Initial backoff in seconds (default: 1.0)
        max_backoff: Maximum backoff in seconds (default: 30.0)
        backoff_multiplier: Multiplier for exponential backoff (default: 2.0)

    Returns:
        Result from connect_func if successful

    Raises:
        Exception: If all retries exhausted
    """
    import time

    backoff = initial_backoff

    for attempt in range(1, max_retries + 1):
        try:
            result = connect_func()
            logger.info(f"✅ Connected to {service_name} (attempt {attempt}/{max_retries})")
            return result

        except Exception as e:
            if attempt < max_retries:
                logger.warning(
                    f"⚠️ {service_name} not ready (attempt {attempt}/{max_retries}). "
                    f"Retrying in {backoff:.1f}s... Error: {e}"
                )
                time.sleep(backoff)
                # Exponential backoff with cap
                backoff = min(backoff * backoff_multiplier, max_backoff)
            else:
                logger.error(
                    f"❌ Failed to connect to {service_name} after {max_retries} attempts. "
                    f"Last error: {e}"
                )
                raise

    # Should never reach here, but just in case
    raise RuntimeError(f"Unexpected error in retry logic for {service_name}")
