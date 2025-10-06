"""
Fear & Greed Index Collector
Fetches crypto fear & greed index from Alternative.me
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


class FearGreedIndexCollector:
    """
    Fear & Greed Index Collector

    Fetches crypto market fear & greed index (0-100)
    - 0-24: Extreme Fear
    - 25-49: Fear
    - 50-74: Greed
    - 75-100: Extreme Greed
    """

    def __init__(self, publisher: Optional[ExternalDataPublisher] = None):
        """
        Initialize Fear & Greed Index collector

        Args:
            publisher: Optional NATS+Kafka publisher
        """
        self.base_url = "https://api.alternative.me/fng/"
        self.session: Optional[aiohttp.ClientSession] = None
        self.publisher = publisher

        logger.info(f"✅ Fear & Greed Index collector initialized")

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
        Collect fear & greed index

        Returns: Dictionary with index data
        """
        if not self.session:
            await self.initialize()

        logger.info(f"📊 Fetching Fear & Greed Index...")

        try:
            params = {'limit': 1}  # Get latest only

            async with self.session.get(self.base_url, params=params) as response:
                if response.status != 200:
                    logger.error(f"HTTP {response.status} from Alternative.me")
                    return None

                result = await response.json()

                if 'data' not in result or not result['data']:
                    logger.error("No data in response")
                    return None

                latest = result['data'][0]

                # Parse index value and classification
                index_value = int(latest['value'])
                classification = latest['value_classification']

                # Calculate sentiment score (-1 to 1)
                sentiment_score = (index_value - 50) / 50  # Normalize to -1 to 1

                data = {
                    'source': 'alternative.me',
                    'collected_at': datetime.utcnow().isoformat(),
                    'index': {
                        'value': index_value,
                        'classification': classification,
                        'sentiment_score': round(sentiment_score, 3),
                        'timestamp': latest['timestamp'],
                        'time_until_update': latest.get('time_until_update')
                    }
                }

                # Publish
                if self.publisher:
                    await self.publisher.publish(
                        data=data['index'],
                        data_type=DataType.FEAR_GREED_INDEX,
                        metadata={
                            'source': 'alternative.me'
                        }
                    )

                logger.info(f"✅ Fear & Greed Index: {index_value} ({classification})")

                return data

        except Exception as e:
            logger.error(f"❌ Fear & Greed Index collection error: {e}")
            raise
