"""
FRED Economic Data Collector - US Economic Indicators
Federal Reserve Economic Data API integration

FEATURES:
- GDP, CPI, Employment data collection
- Currency-relevant economic indicators
- Historical economic data for backtesting
- Real-time economic releases
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging

from ..schemas.market_data_pb2 import EconomicIndicator

logger = logging.getLogger(__name__)


class FREDCollector:
    """
    FRED (Federal Reserve Economic Data) collector
    Provides US economic indicators for fundamental analysis
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.stlouisfed.org/fred"
        self.session = None

        # Key economic indicators that impact forex markets
        self.forex_relevant_indicators = {
            # GDP & Growth
            "GDP": "Gross Domestic Product",
            "GDPC1": "Real GDP",
            "GDPPOT": "Real Potential GDP",

            # Inflation
            "CPIAUCSL": "Consumer Price Index",
            "CPILFESL": "Core CPI (Less Food & Energy)",
            "PCEPI": "PCE Price Index",
            "PCEPILFE": "Core PCE Price Index",

            # Employment
            "UNRATE": "Unemployment Rate",
            "PAYEMS": "Nonfarm Payrolls",
            "CIVPART": "Labor Force Participation Rate",
            "AWHAETP": "Average Hourly Earnings",

            # Interest Rates
            "FEDFUNDS": "Federal Funds Rate",
            "DGS10": "10-Year Treasury Rate",
            "DGS2": "2-Year Treasury Rate",
            "TB3MS": "3-Month Treasury Bill",

            # Money Supply
            "M1SL": "M1 Money Supply",
            "M2SL": "M2 Money Supply",
            "BOGMBASE": "Monetary Base",

            # Trade & Balance
            "BOPGSTB": "Trade Balance",
            "IMPGS": "Imports of Goods and Services",
            "EXPGS": "Exports of Goods and Services",

            # Manufacturing & Industry
            "INDPRO": "Industrial Production Index",
            "NAPM": "ISM Manufacturing PMI",
            "HOUST": "Housing Starts",
            "PERMIT": "Building Permits",

            # Consumer & Retail
            "RSAFS": "Retail Sales",
            "PCE": "Personal Consumption Expenditures",
            "PSAVERT": "Personal Saving Rate",
            "UMCSENT": "University of Michigan Consumer Sentiment"
        }

        # Currency impact mapping
        self.currency_impact = {
            "GDP": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF"],
            "CPIAUCSL": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD"],
            "UNRATE": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF"],
            "FEDFUNDS": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD", "USDCAD"],
            "PAYEMS": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF"],
            "BOPGSTB": ["EURUSD", "USDJPY", "USDCHF", "USDCAD"]
        }

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def get_economic_data(
        self,
        series_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[EconomicIndicator]:
        """
        Get economic data series from FRED

        Args:
            series_id: FRED series ID (e.g., 'GDP', 'CPIAUCSL')
            start_date: Start date for data
            end_date: End date for data
            limit: Maximum number of observations

        Returns:
            List of EconomicIndicator objects
        """
        try:
            # Build request parameters
            params = {
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json",
                "limit": limit
            }

            if start_date:
                params["observation_start"] = start_date.strftime("%Y-%m-%d")
            if end_date:
                params["observation_end"] = end_date.strftime("%Y-%m-%d")

            url = f"{self.base_url}/series/observations"

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return await self._parse_fred_data(series_id, data)
                else:
                    logger.error(f"FRED API error: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"FRED data fetch error for {series_id}: {e}")
            return []

    async def _parse_fred_data(
        self,
        series_id: str,
        data: Dict[str, Any]
    ) -> List[EconomicIndicator]:
        """Parse FRED API response to EconomicIndicator objects"""
        indicators = []

        try:
            # Get series info
            series_info = await self._get_series_info(series_id)

            observations = data.get("observations", [])

            for obs in observations:
                # Skip missing values
                if obs.get("value") == "." or obs.get("value") is None:
                    continue

                indicator = EconomicIndicator()
                indicator.series_id = series_id
                indicator.name = series_info.get("title", series_id)
                indicator.category = "US_Economic_Indicators"
                indicator.subcategory = self._get_subcategory(series_id)

                # Parse date
                date_str = obs.get("date")
                if date_str:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    indicator.timestamp = int(date_obj.timestamp() * 1000)

                # Parse value
                try:
                    indicator.value = float(obs.get("value"))
                except (ValueError, TypeError):
                    continue

                indicator.units = series_info.get("units", "")
                indicator.frequency = series_info.get("frequency", "")
                indicator.last_updated = int(datetime.now().timestamp() * 1000)
                indicator.source = "FRED"

                # Add currency impact
                indicator.currency_impact = self.currency_impact.get(series_id, [])

                # Market impact scoring
                indicator.market_impact_score = self._calculate_market_impact(series_id)

                indicators.append(indicator)

            return indicators

        except Exception as e:
            logger.error(f"FRED data parsing error: {e}")
            return []

    async def _get_series_info(self, series_id: str) -> Dict[str, Any]:
        """Get series metadata from FRED"""
        try:
            params = {
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json"
            }

            url = f"{self.base_url}/series"

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    series_list = data.get("seriess", [])
                    if series_list:
                        return series_list[0]

                return {}

        except Exception as e:
            logger.warning(f"Failed to get series info for {series_id}: {e}")
            return {}

    def _get_subcategory(self, series_id: str) -> str:
        """Categorize economic indicators by type"""
        gdp_indicators = ["GDP", "GDPC1", "GDPPOT"]
        inflation_indicators = ["CPIAUCSL", "CPILFESL", "PCEPI", "PCEPILFE"]
        employment_indicators = ["UNRATE", "PAYEMS", "CIVPART", "AWHAETP"]
        interest_rate_indicators = ["FEDFUNDS", "DGS10", "DGS2", "TB3MS"]
        money_supply_indicators = ["M1SL", "M2SL", "BOGMBASE"]
        trade_indicators = ["BOPGSTB", "IMPGS", "EXPGS"]
        manufacturing_indicators = ["INDPRO", "NAPM", "HOUST", "PERMIT"]
        consumer_indicators = ["RSAFS", "PCE", "PSAVERT", "UMCSENT"]

        if series_id in gdp_indicators:
            return "GDP_Growth"
        elif series_id in inflation_indicators:
            return "Inflation"
        elif series_id in employment_indicators:
            return "Employment"
        elif series_id in interest_rate_indicators:
            return "Interest_Rates"
        elif series_id in money_supply_indicators:
            return "Money_Supply"
        elif series_id in trade_indicators:
            return "Trade_Balance"
        elif series_id in manufacturing_indicators:
            return "Manufacturing"
        elif series_id in consumer_indicators:
            return "Consumer"
        else:
            return "Other"

    def _calculate_market_impact(self, series_id: str) -> float:
        """Calculate market impact score (0-1) based on forex relevance"""
        high_impact = ["CPIAUCSL", "PAYEMS", "FEDFUNDS", "GDP", "UNRATE"]
        medium_impact = ["CPILFESL", "DGS10", "BOPGSTB", "NAPM", "RSAFS"]

        if series_id in high_impact:
            return 0.9
        elif series_id in medium_impact:
            return 0.7
        else:
            return 0.5

    async def get_latest_releases(self) -> List[EconomicIndicator]:
        """Get latest economic data releases"""
        try:
            params = {
                "api_key": self.api_key,
                "file_type": "json",
                "limit": 50
            }

            url = f"{self.base_url}/releases/dates"

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    # Process recent releases
                    return await self._process_recent_releases(data)

                return []

        except Exception as e:
            logger.error(f"FRED latest releases error: {e}")
            return []

    async def _process_recent_releases(self, data: Dict[str, Any]) -> List[EconomicIndicator]:
        """Process recent releases and get their data"""
        indicators = []

        try:
            releases = data.get("release_dates", [])

            # Get recent releases (last 7 days)
            cutoff_date = datetime.now() - timedelta(days=7)

            for release in releases:
                release_date = datetime.strptime(release.get("date"), "%Y-%m-%d")

                if release_date >= cutoff_date:
                    release_id = release.get("release_id")

                    # Get series for this release
                    series_data = await self._get_release_series(release_id)

                    for series_id in series_data:
                        if series_id in self.forex_relevant_indicators:
                            # Get latest data for this series
                            latest_data = await self.get_economic_data(
                                series_id,
                                start_date=cutoff_date,
                                limit=1
                            )
                            indicators.extend(latest_data)

            return indicators

        except Exception as e:
            logger.error(f"Process recent releases error: {e}")
            return []

    async def _get_release_series(self, release_id: str) -> List[str]:
        """Get series IDs for a specific release"""
        try:
            params = {
                "release_id": release_id,
                "api_key": self.api_key,
                "file_type": "json",
                "limit": 100
            }

            url = f"{self.base_url}/release/series"

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    series_list = data.get("seriess", [])
                    return [series.get("id") for series in series_list]

                return []

        except Exception as e:
            logger.warning(f"Get release series error: {e}")
            return []

    async def get_all_forex_indicators(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[EconomicIndicator]:
        """Get all forex-relevant economic indicators"""
        all_indicators = []

        for series_id in self.forex_relevant_indicators.keys():
            indicators = await self.get_economic_data(
                series_id,
                start_date=start_date,
                end_date=end_date
            )
            all_indicators.extend(indicators)

            # Rate limiting
            await asyncio.sleep(0.1)

        return all_indicators

    def get_supported_indicators(self) -> Dict[str, str]:
        """Get list of supported forex-relevant indicators"""
        return self.forex_relevant_indicators.copy()


# Usage Example
async def main():
    """Example usage of FRED Collector"""
    api_key = "6d60cc45ff2ae7245feffad1513d7bef"

    async with FREDCollector(api_key) as fred:

        # Get specific indicator (CPI)
        print("Getting CPI data...")
        cpi_data = await fred.get_economic_data(
            "CPIAUCSL",
            start_date=datetime.now() - timedelta(days=365)
        )
        print(f"Retrieved {len(cpi_data)} CPI observations")

        if cpi_data:
            latest_cpi = cpi_data[-1]
            print(f"Latest CPI: {latest_cpi.value} ({latest_cpi.timestamp})")
            print(f"Currency Impact: {latest_cpi.currency_impact}")

        # Get all forex indicators
        print("\nGetting all forex-relevant indicators...")
        all_data = await fred.get_all_forex_indicators(
            start_date=datetime.now() - timedelta(days=90)
        )
        print(f"Total indicators retrieved: {len(all_data)}")

        # Group by category
        by_category = {}
        for indicator in all_data:
            cat = indicator.subcategory
            if cat not in by_category:
                by_category[cat] = 0
            by_category[cat] += 1

        print("Indicators by category:")
        for cat, count in by_category.items():
            print(f"  {cat}: {count}")


if __name__ == "__main__":
    asyncio.run(main())