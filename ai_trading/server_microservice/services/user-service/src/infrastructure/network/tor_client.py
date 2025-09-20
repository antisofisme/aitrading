"""
Tor SOCKS Proxy Client
Specialized client for Tor network connections
"""

import asyncio
import aiohttp
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class TorProxyClient:
    """
    Specialized Tor SOCKS proxy client
    Handles Tor-specific configuration and error handling
    """
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.tor_socks_proxy = "socks5://127.0.0.1:9050"
        self.timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes for Tor
    
    async def create_session(self, headers: Optional[dict] = None) -> aiohttp.ClientSession:
        """Create Tor SOCKS proxy session"""
        try:
            import aiohttp_socks
        except ImportError:
            logger.error(f"[{self.service_name}] aiohttp-socks required for Tor proxy")
            raise ImportError("aiohttp-socks package required for Tor functionality")
        
        # Create SOCKS proxy connector
        connector = aiohttp_socks.ProxyConnector.from_url(self.tor_socks_proxy)
        
        session = aiohttp.ClientSession(
            connector=connector,
            timeout=self.timeout,
            headers=headers or {}
        )
        
        logger.info(f"🧅 [{self.service_name}] Tor SOCKS session created")
        return session
    
    async def test_connectivity(self) -> bool:
        """Test Tor proxy connectivity"""
        try:
            session = await self.create_session()
            
            # Test with httpbin to check connectivity
            async with session.get('https://httpbin.org/ip') as response:
                if response.status == 200:
                    data = await response.json()
                    tor_ip = data.get('origin', 'unknown')
                    logger.info(f"🧅 [{self.service_name}] Tor connectivity confirmed, exit IP: {tor_ip}")
                    await session.close()
                    return True
                    
            await session.close()
            return False
            
        except Exception as e:
            logger.error(f"🧅 [{self.service_name}] Tor connectivity test failed: {e}")
            return False