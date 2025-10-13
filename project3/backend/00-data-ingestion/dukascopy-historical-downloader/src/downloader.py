"""
Dukascopy Historical Data Downloader
Downloads binary .bi5 tick data files from datafeed.dukascopy.com
"""
import asyncio
import aiohttp
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from pathlib import Path

# SOCKS proxy support
try:
    from aiohttp_socks import ProxyConnector
    SOCKS_AVAILABLE = True
except ImportError:
    SOCKS_AVAILABLE = False
    logging.warning("aiohttp-socks not available, proxy support disabled")

logger = logging.getLogger(__name__)


class DukascopyDownloader:
    """
    Downloads historical tick data from Dukascopy datafeed

    Features:
    - Async HTTP downloads with connection pooling
    - Retry logic with exponential backoff
    - Rate limiting (10 req/sec max)
    - Concurrent downloads (5-10 parallel)
    """

    BASE_URL = "https://datafeed.dukascopy.com/datafeed"

    def __init__(self, max_concurrent: int = 10, rate_limit_per_sec: int = 10):
        """
        Args:
            max_concurrent: Maximum parallel downloads
            rate_limit_per_sec: Maximum requests per second
        """
        self.max_concurrent = max_concurrent
        self.rate_limit_per_sec = rate_limit_per_sec
        self.session: Optional[aiohttp.ClientSession] = None

        # Rate limiting
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._rate_limiter = asyncio.Semaphore(rate_limit_per_sec)

        # Statistics
        self.download_count = 0
        self.retry_count = 0
        self.error_count = 0

    async def connect(self):
        """Initialize HTTP session with connection pooling and optional SOCKS proxy"""
        # Check for HTTP_PROXY or HTTPS_PROXY environment variables
        proxy_url = os.getenv('HTTP_PROXY') or os.getenv('HTTPS_PROXY')

        if proxy_url and SOCKS_AVAILABLE:
            # Use SOCKS proxy connector
            connector = ProxyConnector.from_url(proxy_url)
            logger.info(f"✅ Using SOCKS proxy: {proxy_url}")
        else:
            # Standard TCP connector
            connector = aiohttp.TCPConnector(
                limit=self.max_concurrent,
                limit_per_host=self.max_concurrent,
                ttl_dns_cache=300
            )
            if proxy_url and not SOCKS_AVAILABLE:
                logger.warning("⚠️  Proxy configured but aiohttp-socks not installed")

        timeout = aiohttp.ClientTimeout(
            total=60,  # 60 seconds total timeout
            connect=10,  # 10 seconds to establish connection
            sock_read=30  # 30 seconds to read response
        )

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'Suho-Dukascopy-Downloader/1.0'}
        )

        logger.info(f"✅ HTTP session initialized (max_concurrent={self.max_concurrent})")

    async def download_hour(
        self,
        symbol: str,
        year: int,
        month: int,
        day: int,
        hour: int,
        retry_attempts: int = 3
    ) -> Optional[bytes]:
        """
        Download .bi5 file for a specific hour

        URL format:
        https://datafeed.dukascopy.com/datafeed/{SYMBOL}/{YEAR}/{MONTH:02d}/{DAY:02d}/{HOUR:02d}h_ticks.bi5

        Example:
        https://datafeed.dukascopy.com/datafeed/EURUSD/2024/00/01/00h_ticks.bi5

        Args:
            symbol: Dukascopy symbol (e.g., 'EURUSD')
            year, month, day, hour: Timestamp components
            retry_attempts: Number of retry attempts on failure

        Returns:
            Binary .bi5 file content, or None if download failed
        """
        # Dukascopy uses 0-indexed months (January = 00)
        month_idx = month - 1

        url = f"{self.BASE_URL}/{symbol}/{year}/{month_idx:02d}/{day:02d}/{hour:02d}h_ticks.bi5"

        for attempt in range(retry_attempts):
            try:
                # Rate limiting and concurrency control
                async with self._semaphore, self._rate_limiter:
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            binary_data = await response.read()
                            self.download_count += 1

                            # Log progress
                            if self.download_count % 100 == 0:
                                logger.info(f"📥 Downloaded {self.download_count} hours")

                            return binary_data

                        elif response.status == 404:
                            # No data available for this hour (market closed, weekend, etc.)
                            logger.debug(f"No data: {url} (404)")
                            return None

                        else:
                            logger.warning(f"HTTP {response.status} for {url}")
                            self.error_count += 1

                            # Retry on 5xx errors
                            if response.status >= 500 and attempt < retry_attempts - 1:
                                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                                self.retry_count += 1
                                continue

                            return None

            except asyncio.TimeoutError:
                logger.warning(f"Timeout downloading {url} (attempt {attempt + 1}/{retry_attempts})")
                self.error_count += 1
                if attempt < retry_attempts - 1:
                    await asyncio.sleep(2 ** attempt)
                    self.retry_count += 1
                else:
                    return None

            except Exception as e:
                logger.error(f"Error downloading {url}: {e}")
                self.error_count += 1
                if attempt < retry_attempts - 1:
                    await asyncio.sleep(2 ** attempt)
                    self.retry_count += 1
                else:
                    return None

        return None

    async def download_date_range(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Tuple[datetime, bytes]]:
        """
        Download all hours within a date range

        Args:
            symbol: Dukascopy symbol
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of (timestamp, binary_data) tuples for successfully downloaded hours
        """
        downloads = []
        current = start_date

        # Generate list of all hours to download
        hours_to_download = []
        while current <= end_date:
            hours_to_download.append((
                current.year,
                current.month,
                current.day,
                current.hour,
                current
            ))
            current += timedelta(hours=1)

        logger.info(f"📥 Downloading {len(hours_to_download)} hours for {symbol}")

        # Download in batches
        for year, month, day, hour, timestamp in hours_to_download:
            binary_data = await self.download_hour(symbol, year, month, day, hour)

            if binary_data:
                downloads.append((timestamp, binary_data))

        logger.info(f"✅ Downloaded {len(downloads)}/{len(hours_to_download)} hours for {symbol}")
        return downloads

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            logger.info("✅ HTTP session closed")

    def get_stats(self) -> dict:
        """Get download statistics"""
        return {
            'download_count': self.download_count,
            'retry_count': self.retry_count,
            'error_count': self.error_count,
            'success_rate': (
                self.download_count / (self.download_count + self.error_count)
                if (self.download_count + self.error_count) > 0
                else 0.0
            )
        }
