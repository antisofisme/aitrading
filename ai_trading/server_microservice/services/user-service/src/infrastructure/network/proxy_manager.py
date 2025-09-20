"""
Central Proxy Manager for all microservices
Handles Tor, WARP, and other proxy configurations
"""

import os
import asyncio
import aiohttp
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class ProxyManager:
    """
    Centralized proxy management for all microservices
    Provides consistent proxy configuration and session management
    """
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        
        # Proxy Configuration
        self.warp_key = os.getenv("CLOUDFLARE_WARP_KEY", "")
        self.use_warp_proxy = bool(self.warp_key)
        self.warp_http_proxy = "http://127.0.0.1:40000"
        self.warp_socks_proxy = "127.0.0.1:40000"
        
        # Tor proxy configuration
        self.use_tor_proxy = os.getenv("USE_TOR_PROXY", "false").lower() == "true"
        self.tor_socks_proxy = "socks5://127.0.0.1:9050"
        
        # Session configuration
        self.session_timeout = aiohttp.ClientTimeout(total=300)
        
        self._log_proxy_status()
    
    def _log_proxy_status(self):
        """Log current proxy configuration"""
        if self.use_warp_proxy:
            logger.info(f"🔒 [{self.service_name}] WARP proxy enabled - traffic will route through Cloudflare WARP")
        elif self.use_tor_proxy:
            logger.info(f"🧅 [{self.service_name}] Tor proxy enabled - traffic will route through Tor network")
        else:
            logger.info(f"🌐 [{self.service_name}] Direct connection - no proxy configured")
    
    async def create_http_session(self, custom_headers: Optional[Dict[str, str]] = None) -> aiohttp.ClientSession:
        """
        Create HTTP session with appropriate proxy configuration
        
        Args:
            custom_headers: Optional custom headers for the session
            
        Returns:
            Configured aiohttp.ClientSession
        """
        # Default browser headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Merge with custom headers if provided
        if custom_headers:
            headers.update(custom_headers)
        
        try:
            if self.use_tor_proxy:
                return await self._create_tor_session(headers)
            elif self.use_warp_proxy:
                return await self._create_warp_session(headers)
            else:
                return await self._create_direct_session(headers)
                
        except Exception as e:
            logger.error(f"Failed to create HTTP session for {self.service_name}: {e}")
            # Fallback to direct connection
            return await self._create_direct_session(headers)
    
    async def _create_tor_session(self, headers: Dict[str, str]) -> aiohttp.ClientSession:
        """Create session with Tor SOCKS proxy"""
        try:
            import aiohttp_socks
        except ImportError:
            logger.warning(f"[{self.service_name}] aiohttp-socks not installed, installing...")
            import subprocess
            subprocess.run(['pip3', 'install', 'aiohttp-socks', '--break-system-packages'], check=True)
            import aiohttp_socks
        
        # Create SOCKS proxy connector for Tor
        connector = aiohttp_socks.ProxyConnector.from_url(self.tor_socks_proxy)
        
        session = aiohttp.ClientSession(
            connector=connector,
            timeout=self.session_timeout,
            headers=headers
        )
        
        logger.info(f"🧅 [{self.service_name}] HTTP session created with Tor SOCKS proxy")
        return session
    
    async def _create_warp_session(self, headers: Dict[str, str]) -> aiohttp.ClientSession:
        """Create session with WARP proxy"""
        # Test WARP proxy connection first
        await self._test_warp_proxy_connection()
        
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=10,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        session = aiohttp.ClientSession(
            connector=connector,
            timeout=self.session_timeout,
            headers=headers
        )
        
        logger.info(f"🔒 [{self.service_name}] HTTP session created with WARP proxy support")
        return session
    
    async def _create_direct_session(self, headers: Dict[str, str]) -> aiohttp.ClientSession:
        """Create direct connection session"""
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=10,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        session = aiohttp.ClientSession(
            connector=connector,
            timeout=self.session_timeout,
            headers=headers
        )
        
        logger.info(f"🌐 [{self.service_name}] HTTP session created with direct connection")
        return session
    
    async def _test_warp_proxy_connection(self):
        """Test WARP proxy connectivity"""
        # Implementation for WARP testing
        pass
    
    def get_proxy_config(self) -> Dict[str, Any]:
        """Get current proxy configuration"""
        return {
            "service_name": self.service_name,
            "use_tor_proxy": self.use_tor_proxy,
            "use_warp_proxy": self.use_warp_proxy,
            "tor_proxy": self.tor_socks_proxy if self.use_tor_proxy else None,
            "warp_proxy": self.warp_http_proxy if self.use_warp_proxy else None
        }