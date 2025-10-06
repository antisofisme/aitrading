"""
CoinGecko Sentiment Collector
Fetches cryptocurrency sentiment data from CoinGecko
"""
import logging
import aiohttp
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from publishers import ExternalDataPublisher, DataType

logger = logging.getLogger(__name__)


class CoinGeckoSentimentCollector:
    """
    CoinGecko Sentiment Collector

    Fetches crypto market sentiment and community metrics
    """

    def __init__(
        self,
        coins: list = None,
        publisher: Optional[ExternalDataPublisher] = None
    ):
        """
        Initialize CoinGecko collector

        Args:
            coins: List of CoinGecko coin IDs to track
            publisher: Optional NATS+Kafka publisher
        """
        self.base_url = "https://api.coingecko.com/api/v3"
        self.session: Optional[aiohttp.ClientSession] = None
        self.publisher = publisher

        # Coins to track
        self.coins = coins or ['bitcoin', 'ethereum', 'ripple']

        logger.info(f"✅ CoinGecko collector initialized | Coins: {len(self.coins)}")

    async def initialize(self):
        """Initialize HTTP session"""
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()

    async def collect(self) -> Dict[str, Any]:
        """
        Collect crypto sentiment from CoinGecko

        Returns: Dictionary with sentiment data
        """
        if not self.session:
            await self.initialize()

        logger.info(f"📊 Fetching CoinGecko sentiment...")

        try:
            sentiment_data = []

            for coin_id in self.coins:
                try:
                    data = await self._fetch_coin_sentiment(coin_id)
                    if data:
                        sentiment_data.append(data)

                        # Publish individual coin sentiment
                        if self.publisher:
                            await self.publisher.publish(
                                data=data,
                                data_type=DataType.CRYPTO_SENTIMENT,
                                metadata={
                                    'source': 'coingecko.com',
                                    'coin_id': coin_id
                                }
                            )

                except Exception as e:
                    logger.warning(f"⚠️  Failed to fetch {coin_id}: {e}")
                    continue

            result = {
                'source': 'coingecko.com',
                'collected_at': datetime.utcnow().isoformat(),
                'coins_count': len(sentiment_data),
                'sentiment': sentiment_data
            }

            logger.info(f"✅ CoinGecko: Collected {len(sentiment_data)} coins")

            return result

        except Exception as e:
            logger.error(f"❌ CoinGecko collection error: {e}")
            raise

    async def _fetch_coin_sentiment(self, coin_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch sentiment for single coin

        Args:
            coin_id: CoinGecko coin ID

        Returns: Sentiment data
        """
        try:
            url = f"{self.base_url}/coins/{coin_id}"
            params = {
                'localization': 'false',
                'tickers': 'false',
                'community_data': 'true',
                'developer_data': 'false'
            }

            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    logger.warning(f"HTTP {response.status} for {coin_id}")
                    return None

                data = await response.json()

                # Extract sentiment indicators
                market_data = data.get('market_data', {})
                community_data = data.get('community_data', {})
                sentiment_votes_up = data.get('sentiment_votes_up_percentage', 0)

                return {
                    'coin_id': coin_id,
                    'name': data.get('name'),
                    'symbol': data.get('symbol', '').upper(),
                    'price_usd': market_data.get('current_price', {}).get('usd'),
                    'price_change_24h': market_data.get('price_change_percentage_24h'),
                    'market_cap_rank': data.get('market_cap_rank'),
                    'sentiment_votes_up_percentage': sentiment_votes_up,
                    'community_score': data.get('community_score'),
                    'twitter_followers': community_data.get('twitter_followers'),
                    'reddit_subscribers': community_data.get('reddit_subscribers'),
                    'updated_at': datetime.utcnow().isoformat()
                }

        except Exception as e:
            logger.error(f"Failed to fetch {coin_id}: {e}")
            return None
