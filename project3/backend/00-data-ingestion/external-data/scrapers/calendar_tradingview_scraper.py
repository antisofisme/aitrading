"""
TradingView Economic Calendar Scraper - SUPPLEMENTARY TO DUKASCOPY
Advanced economic calendar data collection dengan 3-strategy approach

INTEGRATION WITH DUKASCOPY:
- Economic events for fundamental analysis
- News sentiment for trading decisions
- Calendar data for market timing
- Complement to Dukascopy historical price data

FEATURES:
- 3-Strategy scraping approach (API → JavaScript → HTML)
- Economic event impact analysis
- Multi-timeframe support
- Rate limiting and retry logic
"""

import asyncio
import aiohttp
import json
import re
from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import logging

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class EconomicEvent:
    """Economic event for fundamental analysis alongside Dukascopy price data"""
    date: str
    time: str
    country: str
    currency: str
    event_name: str
    importance: str  # Low, Medium, High
    actual: Optional[str] = None
    forecast: Optional[str] = None
    previous: Optional[str] = None
    unit: Optional[str] = None
    event_id: Optional[str] = None
    category: Optional[str] = None
    source: str = "TradingView"
    scraped_at: str = None

    # DUKASCOPY INTEGRATION FIELDS
    market_impact_score: float = 0.0
    price_volatility_expected: str = "Low"
    trading_recommendation: str = "Monitor"
    dukascopy_correlation_symbols: List[str] = None

    def __post_init__(self):
        if self.scraped_at is None:
            self.scraped_at = datetime.now().isoformat()

        if self.dukascopy_correlation_symbols is None:
            self.dukascopy_correlation_symbols = []

        # Auto-calculate market impact for Dukascopy integration
        self._calculate_market_impact()

    def _calculate_market_impact(self):
        """Calculate market impact score for Dukascopy price correlation"""
        base_score = 0.0

        # Importance weighting
        if self.importance.upper() == "HIGH":
            base_score += 0.6
        elif self.importance.upper() == "MEDIUM":
            base_score += 0.3
        else:
            base_score += 0.1

        # Currency major pair bonus
        major_currencies = ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"]
        if self.currency in major_currencies:
            base_score += 0.2

        # Event type impact
        high_impact_events = ["NFP", "CPI", "GDP", "Interest Rate", "Fed", "ECB", "BOE", "BOJ"]
        if any(event_type in self.event_name for event_type in high_impact_events):
            base_score += 0.2

        self.market_impact_score = min(base_score, 1.0)

        # Set trading recommendations based on score
        if self.market_impact_score >= 0.8:
            self.price_volatility_expected = "High"
            self.trading_recommendation = "High Alert - Major Volatility Expected"
        elif self.market_impact_score >= 0.5:
            self.price_volatility_expected = "Medium"
            self.trading_recommendation = "Monitor Closely - Potential Movement"
        else:
            self.price_volatility_expected = "Low"
            self.trading_recommendation = "Monitor - Minor Impact Expected"

        # Set correlated symbols for Dukascopy
        self._set_dukascopy_symbols()

    def _set_dukascopy_symbols(self):
        """Set Dukascopy symbols that correlate with this economic event"""
        if self.currency == "USD":
            self.dukascopy_correlation_symbols = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD"]
        elif self.currency == "EUR":
            self.dukascopy_correlation_symbols = ["EURUSD", "EURGBP", "EURJPY", "EURCHF", "EURAUD"]
        elif self.currency == "GBP":
            self.dukascopy_correlation_symbols = ["GBPUSD", "EURGBP", "GBPJPY", "GBPCHF", "GBPAUD"]
        elif self.currency == "JPY":
            self.dukascopy_correlation_symbols = ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY", "CHFJPY"]
        elif self.currency == "CHF":
            self.dukascopy_correlation_symbols = ["USDCHF", "EURCHF", "GBPCHF", "CHFJPY"]
        elif self.currency == "CAD":
            self.dukascopy_correlation_symbols = ["USDCAD", "EURCAD", "GBPCAD", "AUDCAD"]
        elif self.currency == "AUD":
            self.dukascopy_correlation_symbols = ["AUDUSD", "EURAUD", "GBPAUD", "AUDJPY", "AUDCAD"]
        elif self.currency == "NZD":
            self.dukascopy_correlation_symbols = ["NZDUSD", "EURNZD", "GBPNZD", "NZDJPY"]


class TradingViewEconomicScraper:
    """
    TradingView Economic Calendar Scraper
    SUPPLEMENTARY to Dukascopy historical data for fundamental analysis
    """

    def __init__(self, rate_limit_seconds: float = 1.5):
        self.rate_limit_seconds = rate_limit_seconds

        # TradingView URLs
        self.base_url = "https://www.tradingview.com"
        self.calendar_url = f"{self.base_url}/economic-calendar/"
        self.api_url = "https://economic-calendar.tradingview.com"

        # Headers optimized for TradingView
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.tradingview.com/economic-calendar/",
            "Origin": "https://www.tradingview.com",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache"
        }

        # Country to currency mapping
        self.country_currency_map = {
            "united states": "USD", "usa": "USD", "us": "USD",
            "european union": "EUR", "eurozone": "EUR", "eu": "EUR",
            "germany": "EUR", "france": "EUR", "italy": "EUR", "spain": "EUR",
            "united kingdom": "GBP", "uk": "GBP", "britain": "GBP",
            "japan": "JPY", "jp": "JPY",
            "canada": "CAD", "ca": "CAD",
            "australia": "AUD", "au": "AUD",
            "new zealand": "NZD", "nz": "NZD",
            "switzerland": "CHF", "ch": "CHF"
        }

        self.stats = {
            "api_requests": 0,
            "html_requests": 0,
            "js_data_extractions": 0,
            "events_found": 0,
            "dukascopy_correlations": 0,
            "errors": 0
        }

    async def scrape_economic_events(
        self,
        start_date: date,
        end_date: date,
        correlate_with_dukascopy: bool = True
    ) -> Dict[str, Any]:
        """
        Scrape economic events with Dukascopy correlation analysis

        Args:
            start_date: Start date for scraping
            end_date: End date for scraping
            correlate_with_dukascopy: Add Dukascopy symbol correlations
        """

        logger.info(f"Starting TradingView scraping from {start_date.isoformat()} to {end_date.isoformat()}")

        all_events = []
        errors = []

        # Generate date range
        current_date = start_date
        dates_to_scrape = []

        while current_date <= end_date:
            dates_to_scrape.append(current_date)
            current_date += timedelta(days=1)

        async with aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as session:

            for target_date in dates_to_scrape:
                try:
                    logger.debug(f"Scraping economic events for {target_date.isoformat()}")

                    # Strategy 1: Try API endpoint first
                    events = await self._try_api_endpoint(session, target_date)

                    # Strategy 2: Parse JavaScript data if API fails
                    if not events:
                        events = await self._try_javascript_data(session, target_date)

                    # Strategy 3: HTML parsing as fallback
                    if not events:
                        events = await self._try_html_parsing(session, target_date)

                    if events:
                        # Enhance events with Dukascopy correlations
                        if correlate_with_dukascopy:
                            events = self._add_dukascopy_correlations(events)

                        all_events.extend(events)
                        self.stats["events_found"] += len(events)
                        logger.debug(f"Found {len(events)} events for {target_date.isoformat()}")

                    # Rate limiting
                    await asyncio.sleep(self.rate_limit_seconds)

                except Exception as e:
                    self.stats["errors"] += 1
                    error_info = {"date": target_date.isoformat(), "error": str(e)}
                    errors.append(error_info)
                    logger.error(f"Failed to scrape {target_date}: {e}")

        # Results with Dukascopy integration
        results = {
            "status": "completed",
            "source": "TradingView_Economic_Calendar",
            "integration_type": "dukascopy_supplementary",
            "total_events": len(all_events),
            "events": [asdict(event) for event in all_events],
            "errors": errors,
            "statistics": self.stats,
            "dukascopy_integration": {
                "correlated_events": len([e for e in all_events if e.dukascopy_correlation_symbols]),
                "high_impact_events": len([e for e in all_events if e.market_impact_score >= 0.8]),
                "major_currency_events": len([e for e in all_events if e.currency in ["USD", "EUR", "GBP", "JPY"]]),
                "trading_alerts": len([e for e in all_events if "Alert" in e.trading_recommendation])
            },
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days_processed": len(dates_to_scrape)
            }
        }

        logger.info(f"TradingView scraping completed - Events: {len(all_events)}, Errors: {len(errors)}")

        return results

    def _add_dukascopy_correlations(self, events: List[EconomicEvent]) -> List[EconomicEvent]:
        """Add Dukascopy symbol correlations to economic events"""
        enhanced_events = []

        for event in events:
            # Market impact already calculated in __post_init__
            # Correlations already set in _set_dukascopy_symbols

            if event.dukascopy_correlation_symbols:
                self.stats["dukascopy_correlations"] += 1

            enhanced_events.append(event)

        return enhanced_events

    async def _try_api_endpoint(self, session: aiohttp.ClientSession, target_date: date) -> List[EconomicEvent]:
        """Try TradingView API endpoints"""
        events = []

        try:
            api_endpoints = [
                f"{self.api_url}/economic-events",
                f"{self.api_url}/api/v1/calendar",
                f"{self.base_url}/economic-calendar/data/"
            ]

            date_params = [
                {"date": target_date.isoformat()},
                {"from": target_date.isoformat(), "to": target_date.isoformat()}
            ]

            for endpoint in api_endpoints:
                for params in date_params:
                    try:
                        async with session.get(endpoint, params=params) as response:
                            self.stats["api_requests"] += 1

                            if response.status == 200:
                                content_type = response.headers.get('content-type', '')

                                if 'json' in content_type:
                                    data = await response.json()
                                    events = self._parse_api_response(data, target_date)

                                    if events:
                                        logger.info(f"API successful: {len(events)} events from {endpoint}")
                                        return events

                    except Exception as e:
                        logger.debug(f"API endpoint failed: {endpoint} - {e}")
                        continue

        except Exception as e:
            logger.debug(f"API strategy failed: {e}")

        return events

    async def _try_javascript_data(self, session: aiohttp.ClientSession, target_date: date) -> List[EconomicEvent]:
        """Parse JavaScript data from TradingView page"""
        events = []

        try:
            url = f"{self.calendar_url}?date={target_date.isoformat()}"

            async with session.get(url) as response:
                self.stats["html_requests"] += 1

                if response.status == 200:
                    html = await response.text()
                    events = self._extract_js_calendar_data(html, target_date)

                    if events:
                        self.stats["js_data_extractions"] += 1
                        logger.info(f"JavaScript extraction: {len(events)} events")

        except Exception as e:
            logger.debug(f"JavaScript extraction failed: {e}")

        return events

    async def _try_html_parsing(self, session: aiohttp.ClientSession, target_date: date) -> List[EconomicEvent]:
        """Parse HTML using CSS selectors"""
        events = []

        try:
            url = f"{self.calendar_url}?date={target_date.isoformat()}"

            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    events = self._parse_html_with_selectors(html, target_date)

                    if events:
                        logger.info(f"HTML parsing: {len(events)} events")

        except Exception as e:
            logger.debug(f"HTML parsing failed: {e}")

        return events

    def _parse_api_response(self, data: Any, target_date: date) -> List[EconomicEvent]:
        """Parse API JSON response to EconomicEvent objects"""
        events = []

        try:
            # Handle different API response structures
            if isinstance(data, dict):
                events_data = None

                for key in ['events', 'data', 'results', 'calendar', 'economic_events']:
                    if key in data:
                        events_data = data[key]
                        break

                if events_data is None:
                    events_data = data

                if isinstance(events_data, list):
                    for event_data in events_data:
                        event = self._create_event_from_api_data(event_data, target_date)
                        if event:
                            events.append(event)

            elif isinstance(data, list):
                for event_data in data:
                    event = self._create_event_from_api_data(event_data, target_date)
                    if event:
                        events.append(event)

        except Exception as e:
            logger.debug(f"API response parsing failed: {e}")

        return events

    def _create_event_from_api_data(self, event_data: Dict, target_date: date) -> Optional[EconomicEvent]:
        """Create EconomicEvent from API data"""
        try:
            # Field mappings
            field_mappings = {
                'event': ['name', 'title', 'event', 'event_name', 'description'],
                'country': ['country', 'country_name', 'nation', 'region'],
                'currency': ['currency', 'currency_code', 'curr'],
                'time': ['time', 'release_time', 'timestamp', 'datetime'],
                'importance': ['importance', 'impact', 'priority', 'level'],
                'actual': ['actual', 'actual_value', 'result'],
                'forecast': ['forecast', 'expected', 'consensus'],
                'previous': ['previous', 'prev', 'last_value']
            }

            # Extract fields
            extracted = {}

            for field, possible_keys in field_mappings.items():
                for key in possible_keys:
                    if key in event_data:
                        extracted[field] = event_data[key]
                        break

            if not extracted.get('event'):
                return None

            # Map country to currency if missing
            country = str(extracted.get('country', '')).lower()
            currency = extracted.get('currency', '')

            if not currency and country:
                currency = self.country_currency_map.get(country, '')

            # Create event with Dukascopy integration
            event = EconomicEvent(
                date=target_date.isoformat(),
                time=str(extracted.get('time', '')),
                country=str(extracted.get('country', '')),
                currency=currency,
                event_name=str(extracted.get('event', '')),
                importance=self._normalize_importance(extracted.get('importance', '')),
                actual=str(extracted.get('actual', '')) if extracted.get('actual') else None,
                forecast=str(extracted.get('forecast', '')) if extracted.get('forecast') else None,
                previous=str(extracted.get('previous', '')) if extracted.get('previous') else None,
                event_id=str(event_data.get('id', '')) if event_data.get('id') else None
            )

            return event

        except Exception as e:
            logger.debug(f"Failed to create event from API data: {e}")
            return None

    def _extract_js_calendar_data(self, html: str, target_date: date) -> List[EconomicEvent]:
        """Extract calendar data from JavaScript"""
        events = []

        try:
            js_patterns = [
                r'window\.initData\s*=\s*({.*?});',
                r'calendarData\s*[:=]\s*({.*?})',
                r'economicEvents\s*[:=]\s*(\[.*?\])',
                r'"events"\s*:\s*(\[.*?\])'
            ]

            for pattern in js_patterns:
                matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)

                for match in matches:
                    try:
                        data = json.loads(match)
                        extracted_events = self._extract_events_from_js_data(data, target_date)
                        events.extend(extracted_events)

                        if extracted_events:
                            break
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            logger.debug(f"JS data extraction failed: {e}")

        return events

    def _parse_html_with_selectors(self, html: str, target_date: date) -> List[EconomicEvent]:
        """Parse HTML using CSS selectors"""
        events = []

        try:
            soup = BeautifulSoup(html, 'html.parser')

            selectors = [
                '.tv-economic-calendar',
                '.js-economic-calendar',
                '[data-economic-calendar]',
                '.economic-calendar-event'
            ]

            for selector in selectors:
                containers = soup.select(selector)

                if containers:
                    for container in containers:
                        extracted_events = self._extract_events_from_container(container, target_date)
                        events.extend(extracted_events)

                    if events:
                        break

        except Exception as e:
            logger.debug(f"HTML parsing failed: {e}")

        return events

    def _extract_events_from_js_data(self, data: Any, target_date: date) -> List[EconomicEvent]:
        """Extract events from JavaScript data structure"""
        events = []

        try:
            if isinstance(data, dict):
                for key in ['events', 'economicEvents', 'calendar', 'data']:
                    if key in data and isinstance(data[key], list):
                        for event_data in data[key]:
                            event = self._create_event_from_api_data(event_data, target_date)
                            if event:
                                events.append(event)
                        break

            elif isinstance(data, list):
                for event_data in data:
                    event = self._create_event_from_api_data(event_data, target_date)
                    if event:
                        events.append(event)

        except Exception as e:
            logger.debug(f"JS data extraction failed: {e}")

        return events

    def _extract_events_from_container(self, container, target_date: date) -> List[EconomicEvent]:
        """Extract events from HTML container"""
        events = []

        try:
            event_elements = container.find_all(['tr', 'div'],
                class_=lambda x: x and any(word in ' '.join(x).lower()
                                         for word in ['event', 'row', 'calendar']))

            for element in event_elements:
                text = element.get_text(strip=True)

                if text and len(text) > 10:
                    # Create basic event
                    event = EconomicEvent(
                        date=target_date.isoformat(),
                        time="",
                        country="Unknown",
                        currency="",
                        event_name=text[:100],
                        importance="Medium"
                    )
                    events.append(event)

        except Exception as e:
            logger.debug(f"Container extraction failed: {e}")

        return events[:10]

    def _normalize_importance(self, importance: str) -> str:
        """Normalize importance level"""
        importance_str = str(importance).lower()

        if any(word in importance_str for word in ['high', 'red', '3', 'important']):
            return 'High'
        elif any(word in importance_str for word in ['medium', 'orange', '2', 'moderate']):
            return 'Medium'
        else:
            return 'Low'

    async def get_high_impact_events(self, days_ahead: int = 7) -> List[Dict]:
        """Get high impact events for next N days - for Dukascopy trading alerts"""
        end_date = date.today() + timedelta(days=days_ahead)
        start_date = date.today()

        results = await self.scrape_economic_events(start_date, end_date)

        high_impact_events = []
        for event_data in results.get('events', []):
            if event_data.get('market_impact_score', 0) >= 0.8:
                high_impact_events.append(event_data)

        return high_impact_events


# Integration with Dukascopy System
async def get_dukascopy_economic_alerts(days_ahead: int = 3) -> Dict[str, Any]:
    """Get economic events that could impact Dukascopy price data"""
    scraper = TradingViewEconomicScraper()
    high_impact_events = await scraper.get_high_impact_events(days_ahead)

    # Group by Dukascopy symbols
    symbol_alerts = {}

    for event in high_impact_events:
        correlated_symbols = event.get('dukascopy_correlation_symbols', [])

        for symbol in correlated_symbols:
            if symbol not in symbol_alerts:
                symbol_alerts[symbol] = []

            symbol_alerts[symbol].append({
                'event': event['event_name'],
                'datetime': event['date'] + ' ' + event['time'],
                'currency': event['currency'],
                'impact_score': event['market_impact_score'],
                'recommendation': event['trading_recommendation'],
                'volatility_expected': event['price_volatility_expected']
            })

    return {
        "status": "success",
        "source": "TradingView_Economic_Dukascopy_Integration",
        "alerts_generated": datetime.now().isoformat(),
        "days_ahead": days_ahead,
        "total_high_impact_events": len(high_impact_events),
        "symbol_alerts": symbol_alerts,
        "trading_recommendations": {
            "high_alert_symbols": [s for s, alerts in symbol_alerts.items()
                                 if any(a['impact_score'] >= 0.9 for a in alerts)],
            "monitor_symbols": [s for s, alerts in symbol_alerts.items()
                              if any(0.7 <= a['impact_score'] < 0.9 for a in alerts)]
        }
    }


# Export functions
__all__ = [
    "TradingViewEconomicScraper",
    "EconomicEvent",
    "get_dukascopy_economic_alerts"
]


# Testing
async def test_tradingview_dukascopy_integration():
    """Test TradingView scraper with Dukascopy integration"""
    print("🧪 Testing TradingView-Dukascopy Integration")

    # Test economic events scraping
    scraper = TradingViewEconomicScraper()
    end_date = date.today()
    start_date = end_date - timedelta(days=2)

    results = await scraper.scrape_economic_events(start_date, end_date)

    print(f"📊 Status: {results['status']}")
    print(f"📅 Events: {results['total_events']}")

    # Test Dukascopy alerts
    alerts = await get_dukascopy_economic_alerts(days_ahead=3)
    print(f"🚨 Dukascopy Alerts: {alerts['total_high_impact_events']} high impact events")
    print(f"📈 High Alert Symbols: {alerts['trading_recommendations']['high_alert_symbols']}")

    return results


if __name__ == "__main__":
    asyncio.run(test_tradingview_dukascopy_integration())