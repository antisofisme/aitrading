"""
ConfigClient - Client library for fetching operational configs from Central Hub

Usage:
    from shared.components.config.client import ConfigClient

    # Initialize
    config_client = ConfigClient(
        service_name="polygon-historical-downloader",
        central_hub_url="http://suho-central-hub:7000"
    )

    # Fetch config (with caching and fallback)
    config = await config_client.get_config()

    # Access config values
    batch_size = config['operational']['batch_size']

    # Optional: Subscribe to hot-reload
    await config_client.subscribe_to_updates()
"""

import asyncio
import logging
import time
import json
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta

try:
    import aiohttp
except ImportError:
    aiohttp = None

try:
    import nats
except ImportError:
    nats = None


class ConfigClient:
    """
    Client for fetching operational configs from Central Hub

    Features:
    - Fetch config from Central Hub API
    - Local caching with TTL (default: 5 minutes)
    - Automatic fallback to safe defaults if Hub unavailable
    - Optional NATS subscription for hot-reload (zero-downtime config updates)
    - Retry logic with exponential backoff

    Example:
        >>> config_client = ConfigClient("my-service")
        >>> await config_client.init_async()
        >>> config = await config_client.get_config()
        >>> print(config['operational']['batch_size'])
        100
    """

    def __init__(
        self,
        service_name: str,
        central_hub_url: str = "http://suho-central-hub:7000",
        cache_ttl_seconds: int = 300,  # 5 minutes
        enable_nats_updates: bool = False,
        nats_url: Optional[str] = None,
        safe_defaults: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        retry_delay_seconds: float = 1.0
    ):
        """
        Initialize ConfigClient

        Args:
            service_name: Name of the service (e.g., "polygon-historical-downloader")
            central_hub_url: Central Hub base URL (default: http://suho-central-hub:7000)
            cache_ttl_seconds: Cache time-to-live in seconds (default: 300 = 5 minutes)
            enable_nats_updates: Enable NATS subscription for hot-reload (default: False)
            nats_url: NATS server URL (default: from env or nats://nats-1:4222)
            safe_defaults: Safe fallback config if Hub unavailable (default: None)
            max_retries: Maximum retry attempts for API calls (default: 3)
            retry_delay_seconds: Initial retry delay in seconds (default: 1.0)
        """
        self.service_name = service_name
        self.central_hub_url = central_hub_url.rstrip('/')
        self.cache_ttl_seconds = cache_ttl_seconds
        self.enable_nats_updates = enable_nats_updates
        self.nats_url = nats_url or "nats://nats-1:4222,nats://nats-2:4222,nats://nats-3:4222"
        self.safe_defaults = safe_defaults or {}
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds

        # Cache
        self._cache: Optional[Dict[str, Any]] = None
        self._cache_timestamp: Optional[datetime] = None

        # NATS client
        self._nats_client: Optional[Any] = None
        self._nats_subscription = None

        # Callbacks for config updates
        self._update_callbacks: list[Callable] = []

        # Logger
        self.logger = logging.getLogger(f"{service_name}.config-client")

        # HTTP session
        self._http_session: Optional[aiohttp.ClientSession] = None

    async def init_async(self):
        """
        Async initialization

        Call this after creating ConfigClient instance to:
        1. Fetch initial config from Central Hub
        2. Subscribe to NATS updates (if enabled)
        """
        # Create HTTP session
        if aiohttp:
            self._http_session = aiohttp.ClientSession()

        # Fetch initial config
        try:
            await self.get_config()
            self.logger.info(f"✅ ConfigClient initialized for {self.service_name}")
        except Exception as e:
            self.logger.warning(f"⚠️ Initial config fetch failed, using defaults: {e}")

        # Subscribe to NATS updates
        if self.enable_nats_updates:
            try:
                await self.subscribe_to_updates()
            except Exception as e:
                self.logger.warning(f"⚠️ NATS subscription failed (non-critical): {e}")

    async def shutdown(self):
        """Cleanup resources"""
        # Close NATS connection
        if self._nats_client and self._nats_client.is_connected:
            await self._nats_client.close()
            self.logger.info("NATS connection closed")

        # Close HTTP session
        if self._http_session:
            await self._http_session.close()
            self.logger.info("HTTP session closed")

    def _is_cache_valid(self) -> bool:
        """Check if cached config is still valid"""
        if self._cache is None or self._cache_timestamp is None:
            return False

        elapsed = datetime.now() - self._cache_timestamp
        return elapsed.total_seconds() < self.cache_ttl_seconds

    async def get_config(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get operational config (with caching and fallback)

        Priority:
        1. Valid cache (if not expired and not force_refresh)
        2. Fetch from Central Hub API
        3. Fallback to safe defaults

        Args:
            force_refresh: Force fetch from Central Hub, ignore cache

        Returns:
            Config dictionary

        Example:
            >>> config = await client.get_config()
            >>> batch_size = config['operational']['batch_size']
        """
        # Return cached config if valid
        if not force_refresh and self._is_cache_valid():
            self.logger.debug(f"Config cache hit for {self.service_name}")
            return self._cache

        # Fetch from Central Hub
        try:
            config = await self._fetch_from_hub()

            # Update cache
            self._cache = config
            self._cache_timestamp = datetime.now()

            self.logger.info(f"✅ Config fetched from Central Hub for {self.service_name}")
            return config

        except Exception as e:
            self.logger.warning(
                f"⚠️ Failed to fetch config from Central Hub: {e}. "
                f"Using {'cached' if self._cache else 'default'} config"
            )

            # Fallback to cache (even if expired) or defaults
            if self._cache is not None:
                return self._cache
            else:
                return self.safe_defaults

    async def _fetch_from_hub(self) -> Dict[str, Any]:
        """
        Fetch config from Central Hub API with retry logic

        Endpoint: GET /api/v1/config/{service_name}

        Returns:
            Config dictionary from Central Hub

        Raises:
            Exception if all retries fail
        """
        url = f"{self.central_hub_url}/api/v1/config/{self.service_name}"

        last_exception = None

        for attempt in range(self.max_retries):
            try:
                if self._http_session:
                    # Use aiohttp (async)
                    async with self._http_session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status == 404:
                            raise ValueError(f"Config not found for service: {self.service_name}")
                        elif response.status != 200:
                            raise ValueError(f"Central Hub returned status {response.status}")

                        data = await response.json()

                        # Parse config_json if it's a string (JSONB stored as string)
                        config = data.get('config', {})
                        if isinstance(config, str):
                            config = json.loads(config)

                        return config
                else:
                    # Fallback to sync requests if aiohttp not available
                    import requests
                    response = requests.get(url, timeout=10)

                    if response.status_code == 404:
                        raise ValueError(f"Config not found for service: {self.service_name}")
                    elif response.status_code != 200:
                        raise ValueError(f"Central Hub returned status {response.status_code}")

                    data = response.json()

                    config = data.get('config', {})
                    if isinstance(config, str):
                        config = json.loads(config)

                    return config

            except Exception as e:
                last_exception = e

                if attempt < self.max_retries - 1:
                    delay = self.retry_delay_seconds * (2 ** attempt)  # Exponential backoff
                    self.logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries} failed: {e}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(f"All {self.max_retries} attempts failed")

        # All retries exhausted
        raise last_exception

    async def subscribe_to_updates(self):
        """
        Subscribe to NATS for hot-reload updates

        Subject: config.update.{service_name}

        When Central Hub broadcasts config update:
        1. Receive NATS message
        2. Parse new config
        3. Update cache
        4. Trigger callbacks

        Example:
            >>> await client.subscribe_to_updates()
            >>> # Config will auto-reload when updated in Central Hub
        """
        if not nats:
            self.logger.warning("NATS library not available, hot-reload disabled")
            return

        try:
            # Connect to NATS
            self._nats_client = await nats.connect(self.nats_url.split(',')[0])

            # Subscribe to config updates
            subject = f"config.update.{self.service_name}"

            async def message_handler(msg):
                try:
                    # Parse update message
                    data = json.loads(msg.data.decode())
                    new_config = data.get('config', {})

                    # Parse if string
                    if isinstance(new_config, str):
                        new_config = json.loads(new_config)

                    # Update cache
                    self._cache = new_config
                    self._cache_timestamp = datetime.now()

                    self.logger.info(
                        f"🔄 Config hot-reloaded for {self.service_name} "
                        f"(version: {data.get('version', 'unknown')})"
                    )

                    # Trigger callbacks
                    for callback in self._update_callbacks:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(new_config)
                            else:
                                callback(new_config)
                        except Exception as e:
                            self.logger.error(f"Callback error: {e}")

                except Exception as e:
                    self.logger.error(f"Failed to handle config update: {e}")

            self._nats_subscription = await self._nats_client.subscribe(
                subject,
                cb=message_handler
            )

            self.logger.info(f"✅ Subscribed to NATS: {subject}")

        except Exception as e:
            self.logger.error(f"❌ Failed to subscribe to NATS: {e}")
            raise

    def on_config_update(self, callback: Callable):
        """
        Register callback for config updates

        Callback will be called when config is updated via NATS hot-reload.

        Args:
            callback: Function or coroutine to call on update
                     Signature: callback(new_config: Dict[str, Any])

        Example:
            >>> def my_callback(new_config):
            >>>     print(f"Config updated: {new_config}")
            >>>
            >>> client.on_config_update(my_callback)
        """
        self._update_callbacks.append(callback)

    def get_value(self, path: str, default: Any = None) -> Any:
        """
        Get config value by dot-notation path

        Args:
            path: Dot-notation path (e.g., "operational.batch_size")
            default: Default value if path not found

        Returns:
            Config value or default

        Example:
            >>> batch_size = client.get_value("operational.batch_size", 100)
        """
        if self._cache is None:
            return default

        keys = path.split('.')
        value = self._cache

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value
