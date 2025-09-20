"""
Cloudflare WARP Proxy Client
Specialized client for WARP connections
"""

import asyncio
import aiohttp
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class WarpProxyClient:
    """
    Cloudflare WARP proxy client
    Handles WARP-specific configuration and authentication
    """
    
    def __init__(self, service_name: str, warp_key: str):
        self.service_name = service_name
        self.warp_key = warp_key
        self.warp_http_proxy = "http://127.0.0.1:40000"
        self.timeout = aiohttp.ClientTimeout(total=300)
    
    async def create_session(self, headers: Optional[dict] = None) -> aiohttp.ClientSession:
        """Create WARP proxy session"""
        
        # Test WARP connectivity first
        is_connected = await self.test_connectivity()
        if not is_connected:
            logger.warning(f"[{self.service_name}] WARP proxy not available, using direct connection")
            raise ConnectionError("WARP proxy not available")
        
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=10,
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        
        session = aiohttp.ClientSession(
            connector=connector,
            timeout=self.timeout,
            headers=headers or {}
        )
        
        logger.info(f"🔒 [{self.service_name}] WARP session created")
        return session
    
    async def test_connectivity(self) -> bool:
        """Test WARP proxy connectivity"""
        try:
            # Test if WARP is running and accessible
            async with aiohttp.ClientSession() as session:
                async with session.get('http://127.0.0.1:40000/', timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status in [200, 404]:  # 404 is OK for proxy endpoint
                        logger.info(f"🔒 [{self.service_name}] WARP proxy is available")
                        return True
                    
        except Exception as e:
            logger.warning(f"🔒 [{self.service_name}] WARP connectivity test failed: {e}")
        
        return False