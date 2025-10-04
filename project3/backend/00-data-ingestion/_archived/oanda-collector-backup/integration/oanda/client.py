"""
OANDA v20 API Client
"""
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
import asyncio
import json
import v20

logger = logging.getLogger(__name__)


class OandaClient:
    """
    Wrapper for OANDA v20 API
    Provides async interface for pricing streams and REST endpoints
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize OANDA client

        Args:
            config: OANDA configuration from config.yaml
        """
        self.config = config
        self.environment = config['oanda']['environment']

        # Determine API hostname
        if self.environment == 'practice':
            self.api_url = 'https://api-fxpractice.oanda.com'
            self.stream_url = 'https://stream-fxpractice.oanda.com'
        else:  # live
            self.api_url = 'https://api-fxtrade.oanda.com'
            self.stream_url = 'https://stream-fxtrade.oanda.com'

        # API settings
        self.timeout = config['oanda'].get('timeout', 30)
        self.max_retries = config['oanda'].get('max_retries', 3)

        # Rate limiting tracking
        self.request_count = 0
        self.stream_count = 0

        logger.info(f"OANDA client initialized for {self.environment} environment")

    def _create_context(self, account_id: str, api_token: str) -> v20.Context:
        """
        Create v20 API context for an account

        Args:
            account_id: OANDA account ID
            api_token: API token for the account

        Returns:
            v20.Context object
        """
        return v20.Context(
            hostname=self.api_url.replace('https://', ''),
            token=api_token,
            timeout=self.timeout
        )

    async def stream_pricing(
        self,
        account_id: str,
        instruments: List[str],
        api_token: str,
        snapshot: bool = True
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream real-time pricing data

        Args:
            account_id: OANDA account ID
            instruments: List of instruments to stream
            api_token: API token for authentication
            snapshot: Include initial price snapshot

        Yields:
            Dict containing pricing tick or heartbeat
        """
        # Check stream limit
        if self.stream_count >= self.config['oanda']['rate_limits']['max_streams_per_ip']:
            raise Exception(
                f"Maximum streams per IP ({self.stream_count}) reached"
            )

        ctx = self._create_context(account_id, api_token)

        logger.info(
            f"Opening pricing stream for account {account_id}: "
            f"{len(instruments)} instruments"
        )

        self.stream_count += 1

        try:
            # Create streaming request
            response = ctx.pricing.stream(
                account_id,
                instruments=','.join(instruments),
                snapshot=snapshot
            )

            # Process stream
            for msg_type, msg in response.parts():
                if msg_type == "pricing.ClientPrice":
                    # Price update
                    yield {
                        'type': 'PRICE',
                        'instrument': msg.instrument,
                        'time': msg.time,
                        'bids': [
                            {'price': str(bid.price), 'liquidity': bid.liquidity}
                            for bid in msg.bids
                        ],
                        'asks': [
                            {'price': str(ask.price), 'liquidity': ask.liquidity}
                            for ask in msg.asks
                        ],
                        'closeoutBid': str(msg.closeoutBid) if msg.closeoutBid else None,
                        'closeoutAsk': str(msg.closeoutAsk) if msg.closeoutAsk else None,
                        'status': msg.status,
                        'tradeable': msg.tradeable
                    }

                elif msg_type == "pricing.PricingHeartbeat":
                    # Heartbeat
                    yield {
                        'type': 'HEARTBEAT',
                        'time': msg.time
                    }

        except Exception as e:
            if 'V20' in str(type(e).__name__):
                logger.error(f"OANDA API error in pricing stream: {e}")
                raise
            logger.error(f"Error in pricing stream: {e}")
            raise

        finally:
            self.stream_count -= 1
            logger.info(f"Pricing stream closed for account {account_id}")

    async def get_pricing(
        self,
        account_id: str,
        api_token: str,
        instruments: List[str],
        include_home_conversions: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Get current pricing (REST endpoint)

        Args:
            account_id: OANDA account ID
            api_token: API token
            instruments: List of instruments
            include_home_conversions: Include home currency conversions

        Returns:
            Dict containing current prices
        """
        ctx = self._create_context(account_id, api_token)

        try:
            self.request_count += 1

            response = ctx.pricing.get(
                account_id,
                instruments=','.join(instruments),
                includeHomeConversions=include_home_conversions
            )

            if response.status != 200:
                logger.error(f"OANDA API error: {response.status}")
                return None

            return {
                'prices': [
                    {
                        'instrument': price.instrument,
                        'time': price.time,
                        'bids': [
                            {'price': str(bid.price), 'liquidity': bid.liquidity}
                            for bid in price.bids
                        ],
                        'asks': [
                            {'price': str(ask.price), 'liquidity': ask.liquidity}
                            for ask in price.asks
                        ],
                        'closeoutBid': str(price.closeoutBid) if price.closeoutBid else None,
                        'closeoutAsk': str(price.closeoutAsk) if price.closeoutAsk else None,
                        'status': price.status,
                        'tradeable': price.tradeable
                    }
                    for price in response.body.get('prices', [])
                ],
                'time': response.body.get('time')
            }

        except Exception as e:
            if 'V20' in str(type(e).__name__):
                logger.error(f"OANDA API error in get_pricing: {e}")
                return None
            logger.error(f"Error in get_pricing: {e}")
            return None

    async def get_candles(
        self,
        api_token: str,
        instrument: str,
        granularity: str = "M1",
        count: int = 500,
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None,
        price: str = "MBA"
    ) -> Optional[Dict[str, Any]]:
        """
        Get historical candle data

        Args:
            api_token: API token
            instrument: Instrument symbol
            granularity: Candle granularity
            count: Number of candles
            from_time: Start time
            to_time: End time
            price: Price type (M=mid, B=bid, A=ask)

        Returns:
            Dict containing candle data
        """
        # Note: Candles endpoint doesn't need account_id
        ctx = v20.Context(
            hostname=self.api_url.replace('https://', ''),
            token=api_token,
            timeout=self.timeout
        )

        try:
            self.request_count += 1

            # Build parameters
            params = {
                'granularity': granularity,
                'price': price
            }

            if count:
                params['count'] = count
            if from_time:
                params['from'] = from_time.isoformat() + 'Z'
            if to_time:
                params['to'] = to_time.isoformat() + 'Z'

            response = ctx.instrument.candles(instrument, **params)

            if response.status != 200:
                logger.error(f"OANDA API error: {response.status}")
                return None

            return {
                'instrument': response.body.get('instrument'),
                'granularity': response.body.get('granularity'),
                'candles': [
                    {
                        'time': candle.time,
                        'volume': candle.volume,
                        'complete': candle.complete,
                        'mid': {
                            'o': str(candle.mid.o),
                            'h': str(candle.mid.h),
                            'l': str(candle.mid.l),
                            'c': str(candle.mid.c)
                        } if hasattr(candle, 'mid') and candle.mid else None,
                        'bid': {
                            'o': str(candle.bid.o),
                            'h': str(candle.bid.h),
                            'l': str(candle.bid.l),
                            'c': str(candle.bid.c)
                        } if hasattr(candle, 'bid') and candle.bid else None,
                        'ask': {
                            'o': str(candle.ask.o),
                            'h': str(candle.ask.h),
                            'l': str(candle.ask.l),
                            'c': str(candle.ask.c)
                        } if hasattr(candle, 'ask') and candle.ask else None
                    }
                    for candle in response.body.get('candles', [])
                ]
            }

        except Exception as e:
            if 'V20' in str(type(e).__name__):
                logger.error(f"OANDA API error in get_candles: {e}")
                return None
            logger.error(f"Error in get_candles: {e}")
            return None

    async def get_instrument(
        self,
        api_token: str,
        account_id: str,
        instrument: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get instrument information

        Args:
            api_token: API token
            account_id: OANDA account ID
            instrument: Instrument symbol

        Returns:
            Dict containing instrument details
        """
        ctx = self._create_context(account_id, api_token)

        try:
            self.request_count += 1

            response = ctx.account.instruments(account_id, instruments=instrument)

            if response.status != 200:
                logger.error(f"OANDA API error: {response.status}")
                return None

            instruments = response.body.get('instruments', [])
            if not instruments:
                return None

            inst = instruments[0]
            return {
                'name': inst.name,
                'type': inst.type,
                'displayName': inst.displayName,
                'pipLocation': inst.pipLocation,
                'displayPrecision': inst.displayPrecision,
                'tradeUnitsPrecision': inst.tradeUnitsPrecision,
                'minimumTradeSize': str(inst.minimumTradeSize),
                'maximumTrailingStopDistance': str(inst.maximumTrailingStopDistance),
                'minimumTrailingStopDistance': str(inst.minimumTrailingStopDistance),
                'maximumPositionSize': str(inst.maximumPositionSize),
                'maximumOrderUnits': str(inst.maximumOrderUnits),
                'marginRate': str(inst.marginRate)
            }

        except Exception as e:
            if 'V20' in str(type(e).__name__):
                logger.error(f"OANDA API error in get_instrument: {e}")
                return None
            logger.error(f"Error in get_instrument: {e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """
        Get client statistics

        Returns:
            Dict containing usage statistics
        """
        return {
            'environment': self.environment,
            'api_url': self.api_url,
            'stream_url': self.stream_url,
            'total_requests': self.request_count,
            'active_streams': self.stream_count,
            'max_streams': self.config['oanda']['rate_limits']['max_streams_per_ip']
        }
