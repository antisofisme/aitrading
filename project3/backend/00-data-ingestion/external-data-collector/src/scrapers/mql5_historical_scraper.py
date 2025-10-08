#!/usr/bin/env python3
"""
MQL5 Historical Economic Calendar Scraper
Uses aiohttp + BeautifulSoup + Z.ai for intelligent scraping
"""
import asyncio
import aiohttp
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Any
from pathlib import Path
import json
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.date_tracker import DateTracker
from publishers import ExternalDataPublisher, DataType


class ZAIParser:
    """Z.ai GLM-4.5-air parser for intelligent HTML parsing"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.z.ai/api/coding/paas/v4/chat/completions"
        self.model = "glm-4.5-air"

    async def parse_calendar_html(
        self,
        html: str,
        target_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Parse HTML with Z.ai GLM

        Args:
            html: HTML content to parse
            target_date: Optional date to filter events

        Returns:
            List of parsed events
        """
        date_filter = target_date.strftime('%Y-%m-%d') if target_date else "any date"

        prompt = f"""Extract economic calendar events from this HTML content.
{f"Filter for date: {date_filter}" if target_date else "Extract all dates"}

HTML Content (truncated to 15000 chars):
{html[:15000]}

Return JSON array with this EXACT structure:
[
  {{
    "date": "YYYY-MM-DD",
    "time": "HH:MM",
    "currency": "USD",
    "event": "Event Name",
    "forecast": "value or null",
    "previous": "value or null",
    "actual": "value or null",
    "impact": "high/medium/low or null"
  }}
]

Rules:
- Only include events for date {date_filter}
- If value is empty/missing, use null
- Keep original value format (%, K, M, B, etc)
- Impact: high/medium/low based on market importance
- Return ONLY valid JSON array, no markdown or explanation
"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,  # Low temperature for consistent parsing
            "max_tokens": 4000
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()

                        # DEBUG: Log full result structure
                        print(f"🔍 Z.ai result keys: {result.keys()}")
                        print(f"🔍 Z.ai choices: {result.get('choices', [])}")

                        content = result['choices'][0]['message']['content']

                        # DEBUG: Log Z.ai response
                        print(f"🔍 Z.ai response length: {len(content)}")
                        print(f"🔍 Z.ai response (first 1000 chars): {content[:1000]}")
                        print(f"🔍 Z.ai response (full): {content}")

                        # Extract JSON from response
                        events = self._extract_json_from_response(content)
                        print(f"🔍 Extracted {len(events)} events from JSON")

                        # Validate and clean
                        validated = self._validate_events(events, target_date)
                        print(f"🔍 Validated {len(validated)} events after filtering")

                        return validated
                    else:
                        error_text = await response.text()
                        print(f"❌ Z.ai API error: {response.status} - {error_text[:200]}")
                        return []

        except Exception as e:
            import traceback
            print(f"❌ Z.ai parsing error: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            return []

    def _extract_json_from_response(self, content: str) -> List[Dict]:
        """Extract JSON array from response (handles markdown code blocks)"""
        # Remove markdown code blocks if present
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```\s*', '', content)

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to find JSON array in text
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return []

    def _validate_events(
        self,
        events: List[Dict],
        target_date: Optional[date]
    ) -> List[Dict]:
        """Validate and clean parsed events"""
        validated = []

        for event in events:
            # Check required fields
            if not all(k in event for k in ['date', 'time', 'currency', 'event']):
                continue

            # Date filter
            if target_date:
                try:
                    event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
                    if event_date != target_date:
                        continue
                except:
                    continue

            # Clean values
            for key in ['forecast', 'previous', 'actual', 'impact']:
                if key not in event or event[key] in ['null', '', 'None']:
                    event[key] = None

            validated.append(event)

        return validated


class MQL5HistoricalScraper:
    """
    MQL5 Economic Calendar Historical Scraper

    Features:
    - aiohttp for HTTP requests (bypasses bot detection)
    - Z.ai for intelligent HTML parsing
    - DateTracker for progress tracking
    - Smart incremental scraping
    """

    def __init__(
        self,
        zai_api_key: str,
        db_connection_string: Optional[str] = None,
        use_zai: bool = True,
        publisher: Optional[ExternalDataPublisher] = None
    ):
        """
        Initialize scraper

        Args:
            zai_api_key: Z.ai API key
            db_connection_string: PostgreSQL connection string
            use_zai: Whether to use Z.ai parser (fallback to regex if False)
            publisher: Optional NATS+Kafka publisher for real-time distribution
        """
        self.base_url = "https://www.mql5.com/en/economic-calendar"
        self.zai_parser = ZAIParser(zai_api_key) if use_zai else None
        self.tracker = DateTracker(db_connection_string)
        self.publisher = publisher

        # HTTP headers (proven to work)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',  # No brotli
            'Connection': 'keep-alive',
        }

    async def fetch_html(self, target_date: Optional[date] = None) -> str:
        """
        Fetch HTML from MQL5

        Args:
            target_date: Optional date for URL filtering

        Returns:
            HTML content
        """
        # Build URL with date parameter
        url = self.base_url
        if target_date:
            url += f"?date={target_date.strftime('%Y.%m.%d')}"

        print(f"   📡 Fetching: {url}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        html = await response.text()
                        print(f"   ✅ Received {len(html)} bytes of HTML")
                        print(f"   🔍 HTML preview (first 200 chars): {html[:200]}")
                        return html
                    else:
                        print(f"❌ HTTP {response.status} for {url}")
                        return ""

        except Exception as e:
            print(f"❌ Fetch error: {e}")
            return ""

    def parse_html_regex(self, html: str) -> List[Dict[str, Any]]:
        """
        Fallback regex parser (if Z.ai not available)

        Args:
            html: HTML content

        Returns:
            List of parsed events
        """
        soup = BeautifulSoup(html, 'lxml')
        text = soup.get_text()

        # Event pattern: date, time, currency, event name
        lines = text.split('\n')
        event_pattern = r'(\d{4}\.\d{2}\.\d{2})\s+(\d{2}:\d{2}),\s+([A-Z]{3}),\s+([^,]+)'

        events = []
        for line in lines:
            match = re.search(event_pattern, line)
            if match:
                date_str, time_str, currency, event_name = match.groups()

                # Extract values
                actual = re.search(r'Actual:\s*([^,]+)', line)
                forecast = re.search(r'Forecast:\s*([^,]+)', line)
                previous = re.search(r'Previous:\s*([^,]+)', line)

                # Convert date format
                try:
                    date_obj = datetime.strptime(date_str, '%Y.%m.%d')
                    date_formatted = date_obj.strftime('%Y-%m-%d')
                except:
                    date_formatted = date_str

                events.append({
                    'date': date_formatted,
                    'time': time_str,
                    'currency': currency,
                    'event': event_name.strip(),
                    'actual': actual.group(1).strip() if actual else None,
                    'forecast': forecast.group(1).strip() if forecast else None,
                    'previous': previous.group(1).strip() if previous else None,
                    'impact': None  # Not available in regex parsing
                })

        return events

    async def scrape_date(self, target_date: date) -> List[Dict[str, Any]]:
        """
        Scrape single date

        Args:
            target_date: Date to scrape

        Returns:
            List of events for that date
        """
        print(f"📅 Scraping: {target_date.strftime('%Y-%m-%d')}")

        # Fetch HTML
        html = await self.fetch_html(target_date)

        if not html:
            print(f"   ❌ No HTML retrieved")
            return []

        # Parse with Z.ai or regex
        if self.zai_parser:
            print(f"   🤖 Parsing with Z.ai...")
            events = await self.zai_parser.parse_calendar_html(html, target_date)
        else:
            print(f"   📝 Parsing with regex...")
            events = self.parse_html_regex(html)
            # Filter for target date
            events = [e for e in events if e['date'] == target_date.strftime('%Y-%m-%d')]

        print(f"   ✅ Found {len(events)} events")

        # Publish to NATS+Kafka if publisher available
        if self.publisher and events:
            print(f"   📤 Publishing {len(events)} events to NATS+Kafka...")
            for event in events:
                await self.publisher.publish(
                    data=event,
                    data_type=DataType.ECONOMIC_CALENDAR,
                    metadata={
                        'source': 'mql5',
                        'scraper_id': 'mql5_historical_scraper',
                        'scrape_date': target_date.isoformat()
                    }
                )

        return events

    async def scrape_date_range(
        self,
        start_date: date,
        end_date: date,
        rate_limit_seconds: int = 2
    ) -> Dict[str, List[Dict]]:
        """
        Scrape date range

        Args:
            start_date: Start date
            end_date: End date
            rate_limit_seconds: Delay between requests

        Returns:
            Dictionary mapping dates to events
        """
        results = {}
        current = start_date

        while current <= end_date:
            # Skip weekends
            if current.weekday() < 5:  # Monday=0, Friday=4
                events = await self.scrape_date(current)
                results[current.strftime('%Y-%m-%d')] = events

                # Update tracker
                has_forecast = any(e.get('forecast') for e in events)
                has_actual = any(e.get('actual') for e in events)
                await self.tracker.mark_date_scraped(
                    current,
                    len(events),
                    has_forecast,
                    has_actual
                )

                # Rate limiting
                await asyncio.sleep(rate_limit_seconds)

            current += timedelta(days=1)

        return results

    async def backfill_historical_data(
        self,
        months_back: int = 12,
        batch_days: int = 30
    ):
        """
        Backfill historical data from today backward

        Args:
            months_back: How many months to go back
            batch_days: Days per batch
        """
        from dateutil.relativedelta import relativedelta

        end_date = datetime.now().date()
        start_date = end_date - relativedelta(months=months_back)

        print("=" * 80)
        print("📊 HISTORICAL BACKFILL")
        print("=" * 80)
        print(f"From: {start_date}")
        print(f"To: {end_date}")
        print(f"Total days: {(end_date - start_date).days}")
        print()

        # Get batches
        batches = await self.tracker.generate_backfill_schedule(
            months_back,
            batch_days
        )

        print(f"Generated {len(batches)} batches")
        print()

        # Process batches
        for i, batch in enumerate(batches, 1):
            print(f"Batch {i}/{len(batches)}: {batch['start_date']} to {batch['end_date']}")
            print(f"  Missing: {batch['missing_count']} days")

            if batch['missing_count'] > 0:
                # Scrape missing dates
                for missing_date in batch['missing_dates']:
                    await self.scrape_date(missing_date)
                    await asyncio.sleep(2)  # Rate limiting

            print()

        # Coverage stats
        stats = await self.tracker.get_coverage_stats()
        print("=" * 80)
        print("✅ BACKFILL COMPLETE")
        print("=" * 80)
        print(f"Total dates scraped: {stats.get('total_dates', 0)}")
        print(f"Total events: {stats.get('total_events', 0)}")
        print(f"Dates with forecast: {stats.get('dates_with_forecast', 0)}")
        print(f"Dates with actual: {stats.get('dates_with_actual', 0)}")

    async def update_recent_actuals(self, days_back: int = 7):
        """
        Update actual values for recent dates

        Args:
            days_back: How many days to check
        """
        print("=" * 80)
        print("🔄 UPDATING RECENT ACTUAL VALUES")
        print("=" * 80)
        print()

        # Get dates needing update from tracker
        dates_needing_update = await self.tracker.get_dates_needing_update(days_back)

        # If no dates in tracker yet (fresh system), scrape today + past 7 days
        if not dates_needing_update:
            print(f"⚠️  No dates in tracker - initializing with today + past {days_back} days")
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)

            dates_needing_update = []
            current = start_date
            while current <= end_date:
                # Skip weekends
                if current.weekday() < 5:  # Monday=0, Friday=4
                    dates_needing_update.append(current)
                current += timedelta(days=1)

        print(f"Found {len(dates_needing_update)} dates needing update")
        print()

        for target_date in dates_needing_update:
            events = await self.scrape_date(target_date)

            # Update tracker
            has_forecast = any(e.get('forecast') for e in events)
            has_actual = any(e.get('actual') for e in events)
            await self.tracker.mark_date_scraped(
                target_date,
                len(events),
                has_forecast,
                has_actual
            )

            await asyncio.sleep(2)  # Rate limiting

        print("✅ Recent actuals updated")

    async def scrape_upcoming(self, days_forward: int = 14):
        """
        Scrape upcoming events (future dates)

        Args:
            days_forward: How many days to scrape forward
        """
        print("=" * 80)
        print("📆 SCRAPING UPCOMING EVENTS")
        print("=" * 80)
        print()

        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=days_forward)

        print(f"Scraping upcoming events from {start_date} to {end_date}")
        print()

        current = start_date
        total_events = 0

        while current <= end_date:
            # Skip weekends
            if current.weekday() < 5:  # Monday=0, Friday=4
                events = await self.scrape_date(current)
                total_events += len(events)

                # Track upcoming events (forecast only, no actual yet)
                has_forecast = any(e.get('forecast') for e in events)
                await self.tracker.mark_date_scraped(
                    current,
                    len(events),
                    has_forecast,
                    False  # has_actual = False for upcoming
                )

                await asyncio.sleep(2)  # Rate limiting

            current += timedelta(days=1)

        print()
        print(f"✅ Scraped {total_events} upcoming events")
        print()
