#!/usr/bin/env python3
"""
MQL5 Historical Economic Calendar Scraper
Uses Playwright + BeautifulSoup for JavaScript rendering and HTML parsing

Features:
- Playwright for JavaScript rendering (handles dynamic content)
- BeautifulSoup HTML parser (fast, reliable, no API cost)
- Historical backfill (10 years back)
- Rate limiting to avoid blocking
- NATS+Kafka real-time publishing
- Date tracking for incremental updates
"""
import asyncio
import aiohttp
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Any
from pathlib import Path
import json
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.date_tracker import DateTracker
from publishers import ExternalDataPublisher, DataType


class MQL5HistoricalScraper:
    """
    MQL5 Economic Calendar Historical Scraper

    Features:
    - Playwright for JavaScript rendering (handles dynamic content loading)
    - BeautifulSoup for robust HTML parsing (NO AI needed!)
    - DateTracker for progress tracking
    - Historical backfill (10 years back)
    - Smart incremental scraping with rate limiting
    """

    def __init__(
        self,
        db_connection_string: Optional[str] = None,
        publisher: Optional[ExternalDataPublisher] = None
    ):
        """
        Initialize scraper

        Args:
            db_connection_string: PostgreSQL connection string
            publisher: Optional NATS+Kafka publisher for real-time distribution
        """
        self.base_url = "https://www.mql5.com/en/economic-calendar"
        self.tracker = DateTracker(db_connection_string)
        self.publisher = publisher
        self.playwright = None
        self.browser = None

    async def init_browser(self):
        """Initialize Playwright browser for JavaScript rendering with anti-detection"""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            # Launch with anti-detection args
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            )
            print("✅ Playwright browser initialized (stealth mode)")

    async def close_browser(self):
        """Close Playwright browser"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
            print("✅ Playwright browser closed")

    async def fetch_html(self, target_date: Optional[date] = None) -> str:
        """
        Fetch HTML from MQL5 using Playwright (JavaScript rendering)

        Args:
            target_date: Optional date for URL filtering

        Returns:
            HTML content after JavaScript execution
        """
        # Build URL with date parameter
        url = self.base_url
        if target_date:
            url += f"?date={target_date.strftime('%Y.%m.%d')}"

        print(f"   📡 Fetching: {url}")

        try:
            # Initialize browser if not already done
            if not self.browser:
                await self.init_browser()

            # Create new page with anti-detection
            page = await self.browser.new_page(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='en-US'
            )

            # Remove webdriver flag
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            # Navigate and wait for content to load
            await page.goto(url, wait_until='networkidle', timeout=30000)

            # Wait for calendar container to appear (dynamic content)
            try:
                await page.wait_for_selector('.economic-calendar__content', timeout=10000)
                print("   ✅ Calendar content loaded")
            except:
                print("   ⚠️  Calendar content selector not found")
                # Try alternative selector
                try:
                    await page.wait_for_selector('table', timeout=5000)
                    print("   ✅ Found table element")
                except:
                    print("   ⚠️  No table element found")

            # Get rendered HTML
            html = await page.content()
            await page.close()

            print(f"   ✅ Received {len(html)} bytes of rendered HTML")

            # Debug: print first 500 chars if HTML is suspiciously small
            if len(html) < 1000:
                print(f"   🔍 HTML content: {html[:500]}")

            return html

        except Exception as e:
            print(f"❌ Fetch error: {e}")
            return ""

    def parse_html_beautifulsoup(self, html: str, target_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """
        BeautifulSoup HTML parser for MQL5 calendar structure

        MQL5 uses: <div class="ec-table__item"> for each event

        Args:
            html: HTML content
            target_date: Optional date filter

        Returns:
            List of parsed events
        """
        soup = BeautifulSoup(html, 'lxml')
        events = []

        # Find all calendar event items (MQL5 structure)
        rows = soup.find_all('div', class_='ec-table__item')

        print(f"🔍 Found {len(rows)} economic events in HTML")

        # Track current date from date titles
        current_date = target_date.isoformat() if target_date else None

        for row in rows:
            try:
                event = {}

                # Check if previous sibling is a date title
                prev_sibling = row.find_previous_sibling('div', class_='ec-table__title')
                if prev_sibling:
                    date_text = prev_sibling.get_text(strip=True)
                    # Parse "13 October, Monday" → 2025-10-13
                    try:
                        parts = date_text.split(',')[0].strip()  # "13 October"
                        year = datetime.now().year
                        parsed_date = datetime.strptime(f"{parts} {year}", "%d %B %Y").date()
                        current_date = parsed_date.isoformat()
                    except:
                        pass

                if not current_date:
                    continue

                event['date'] = current_date

                # Extract time
                time_elem = row.find('div', class_='ec-table__col_time')
                if time_elem:
                    time_div = time_elem.find('div')
                    event['time'] = time_div.get_text(strip=True) if time_div else 'All day'
                else:
                    event['time'] = 'All day'

                # Extract currency
                currency_elem = row.find('div', class_='ec-table__curency-name')
                if currency_elem:
                    event['currency'] = currency_elem.get_text(strip=True)
                else:
                    event['currency'] = 'ALL'

                # Extract event name
                event_elem = row.find('div', class_='ec-table__col_event')
                if event_elem:
                    link = event_elem.find('a')
                    event['event'] = link.get_text(strip=True) if link else event_elem.get_text(strip=True)
                else:
                    continue  # Skip if no event name

                # Extract forecast
                forecast_elem = row.find('div', class_='ec-table__col_forecast')
                if forecast_elem:
                    forecast = forecast_elem.get_text(strip=True)
                    event['forecast'] = forecast if forecast and forecast != '-' else None
                else:
                    event['forecast'] = None

                # Extract previous
                previous_elem = row.find('div', class_='ec-table__col_previous')
                if previous_elem:
                    prev_div = previous_elem.find('div')
                    previous = prev_div.get_text(strip=True) if prev_div else previous_elem.get_text(strip=True)
                    event['previous'] = previous if previous and previous != '-' else None
                else:
                    event['previous'] = None

                # Extract actual
                actual_elem = row.find('div', class_='ec-table__col_actual')
                if actual_elem:
                    actual_span = actual_elem.find('span')
                    actual = actual_span.get_text(strip=True) if actual_span else actual_elem.get_text(strip=True)
                    event['actual'] = actual if actual and actual != '-' else None
                else:
                    event['actual'] = None

                # Extract impact level
                impact_elem = row.find('span', class_=lambda x: x and 'ec-table__importance' in x)
                if impact_elem:
                    classes = impact_elem.get('class', [])
                    for cls in classes:
                        if '_low' in cls:
                            event['impact'] = 'low'
                            break
                        elif '_medium' in cls:
                            event['impact'] = 'medium'
                            break
                        elif '_high' in cls:
                            event['impact'] = 'high'
                            break
                    else:
                        title = impact_elem.get('title', '').lower()
                        if 'high' in title:
                            event['impact'] = 'high'
                        elif 'medium' in title:
                            event['impact'] = 'medium'
                        else:
                            event['impact'] = 'low'
                else:
                    event['impact'] = 'low'

                # Date filter
                if target_date:
                    try:
                        event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
                        if event_date != target_date:
                            continue
                    except:
                        continue

                # Clean empty values
                for key in ['forecast', 'previous', 'actual']:
                    if event.get(key) in ['', '-', '—', 'N/A', None]:
                        event[key] = None

                events.append(event)

            except Exception as e:
                print(f"⚠️ Skipping row due to parse error: {e}")
                continue

        print(f"✅ Successfully parsed {len(events)} events")
        return events

    def parse_html_regex(self, html: str) -> List[Dict[str, Any]]:
        """
        DEPRECATED: Legacy regex parser (kept for fallback)
        USE parse_html_beautifulsoup() instead!
        """
        print("⚠️ Using deprecated regex parser - consider using BeautifulSoup parser")

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
        Scrape single date using BeautifulSoup parser (NO AI!)

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

        # Parse with BeautifulSoup (robust HTML parser - NO AI!)
        print(f"   📝 Parsing with BeautifulSoup...")
        events = self.parse_html_beautifulsoup(html, target_date)

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
