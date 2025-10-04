"""
Pricing API - Handles pricing data requests and historical data
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PricingAPI:
    """
    API for fetching pricing and candle data from OANDA
    Handles both current pricing and historical candle requests
    """

    def __init__(
        self,
        account_manager,
        oanda_client,
        config: Dict[str, Any]
    ):
        """
        Initialize Pricing API

        Args:
            account_manager: Business layer account manager
            oanda_client: OANDA API client
            config: Service configuration
        """
        self.account_manager = account_manager
        self.oanda_client = oanda_client
        self.config = config

    async def get_pricing(
        self,
        instruments: List[str],
        include_home_conversions: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Get current pricing for instruments

        Args:
            instruments: List of instrument symbols
            include_home_conversions: Include home currency conversion rates

        Returns:
            Dict containing pricing data or None on error
        """
        try:
            account = await self.account_manager.get_active_account()
            if not account:
                logger.error("No active account available")
                return None

            response = await self.oanda_client.get_pricing(
                account_id=account['id'],
                instruments=instruments,
                include_home_conversions=include_home_conversions
            )

            return response

        except Exception as e:
            logger.error(f"Failed to get pricing: {e}")
            # Try failover
            account = await self.account_manager.failover()
            if account:
                try:
                    response = await self.oanda_client.get_pricing(
                        account_id=account['id'],
                        instruments=instruments,
                        include_home_conversions=include_home_conversions
                    )
                    return response
                except Exception as retry_error:
                    logger.error(f"Failover pricing request also failed: {retry_error}")

            return None

    async def get_candles(
        self,
        instrument: str,
        granularity: str = "M1",
        count: int = 500,
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None,
        price: str = "MBA"  # M=mid, B=bid, A=ask
    ) -> Optional[Dict[str, Any]]:
        """
        Get historical candle data

        Args:
            instrument: Instrument symbol
            granularity: Candle granularity (S5, M1, M5, H1, D, etc.)
            count: Number of candles to fetch (max 5000)
            from_time: Start time for candles
            to_time: End time for candles
            price: Price type (M, B, A, or combination)

        Returns:
            Dict containing candle data or None on error
        """
        try:
            account = await self.account_manager.get_active_account()
            if not account:
                logger.error("No active account available")
                return None

            response = await self.oanda_client.get_candles(
                instrument=instrument,
                granularity=granularity,
                count=count,
                from_time=from_time,
                to_time=to_time,
                price=price
            )

            return response

        except Exception as e:
            logger.error(f"Failed to get candles: {e}")
            # Try failover
            account = await self.account_manager.failover()
            if account:
                try:
                    response = await self.oanda_client.get_candles(
                        instrument=instrument,
                        granularity=granularity,
                        count=count,
                        from_time=from_time,
                        to_time=to_time,
                        price=price
                    )
                    return response
                except Exception as retry_error:
                    logger.error(f"Failover candles request also failed: {retry_error}")

            return None

    async def get_latest_candles(
        self,
        instruments: List[str],
        granularity: str = "M1",
        count: int = 1
    ) -> Dict[str, Any]:
        """
        Get latest candles for multiple instruments

        Args:
            instruments: List of instrument symbols
            granularity: Candle granularity
            count: Number of latest candles per instrument

        Returns:
            Dict mapping instrument to candle data
        """
        results = {}

        for instrument in instruments:
            candles = await self.get_candles(
                instrument=instrument,
                granularity=granularity,
                count=count
            )
            if candles:
                results[instrument] = candles

        return results

    async def get_instrument_info(self, instrument: str) -> Optional[Dict[str, Any]]:
        """
        Get instrument information (pip location, display precision, etc.)

        Args:
            instrument: Instrument symbol

        Returns:
            Dict containing instrument details or None on error
        """
        try:
            account = await self.account_manager.get_active_account()
            if not account:
                logger.error("No active account available")
                return None

            response = await self.oanda_client.get_instrument(
                account_id=account['id'],
                instrument=instrument
            )

            return response

        except Exception as e:
            logger.error(f"Failed to get instrument info: {e}")
            return None
