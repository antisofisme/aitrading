# 📊 Historical Data Scraping Strategy - MQL5 Calendar

## 🎯 Problem Statement

**Goal:** Scrape 1 tahun economic calendar data secara bertahap
- Track data yang sudah/belum di-ambil
- Update actual values yang baru release
- Efficient incremental scraping
- Avoid duplicate data

---

## 🗄️ Database Schema untuk Tracking

### Table 1: `economic_events`
Menyimpan semua event data

```sql
CREATE TABLE economic_events (
    id BIGSERIAL PRIMARY KEY,

    -- Event identifiers
    event_date DATE NOT NULL,
    event_time TIME NOT NULL,
    currency VARCHAR(3) NOT NULL,
    event_name VARCHAR(255) NOT NULL,

    -- Event data
    forecast VARCHAR(50),
    previous VARCHAR(50),
    actual VARCHAR(50),
    impact VARCHAR(10), -- 'high', 'medium', 'low'

    -- Metadata
    source VARCHAR(20) DEFAULT 'mql5',
    scraped_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Unique constraint
    UNIQUE(event_date, event_time, currency, event_name)
);

CREATE INDEX idx_event_date ON economic_events(event_date);
CREATE INDEX idx_currency ON economic_events(currency);
CREATE INDEX idx_event_date_currency ON economic_events(event_date, currency);
```

### Table 2: `scraping_history`
Track scraping progress

```sql
CREATE TABLE scraping_history (
    id BIGSERIAL PRIMARY KEY,

    -- Date range
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,

    -- Results
    events_found INTEGER DEFAULT 0,
    events_new INTEGER DEFAULT 0,
    events_updated INTEGER DEFAULT 0,

    -- Status
    status VARCHAR(20), -- 'success', 'partial', 'failed'
    error_message TEXT,

    -- Timing
    scraped_at TIMESTAMP DEFAULT NOW(),
    duration_seconds INTEGER,

    UNIQUE(start_date, end_date, scraped_at)
);

CREATE INDEX idx_scrape_date ON scraping_history(start_date, end_date);
```

### Table 3: `date_coverage`
Quick lookup untuk tanggal yang sudah di-scrape

```sql
CREATE TABLE date_coverage (
    date DATE PRIMARY KEY,

    -- Coverage info
    events_count INTEGER DEFAULT 0,
    has_actual_values BOOLEAN DEFAULT FALSE,

    -- Metadata
    first_scraped_at TIMESTAMP,
    last_updated_at TIMESTAMP,
    needs_update BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_needs_update ON date_coverage(needs_update);
```

---

## 🔄 Scraping Strategy

### Strategy 1: Initial Historical Backfill (1 Tahun)

**Approach:** Scrape dari hari ini mundur ke belakang

```python
async def backfill_historical_data(months_back: int = 12):
    """
    Scrape historical data dari sekarang mundur N bulan

    Strategy:
    - Start dari today
    - Go back 1 bulan per batch
    - Check database untuk skip dates yang sudah ada
    - Z.ai untuk parsing HTML
    """

    from datetime import datetime, timedelta
    from dateutil.relativedelta import relativedelta

    end_date = datetime.now().date()
    start_date = end_date - relativedelta(months=months_back)

    print(f"📅 Backfilling from {start_date} to {end_date}")
    print(f"   Total: {(end_date - start_date).days} days")
    print()

    # Process per month untuk avoid memory issues
    current_start = start_date

    while current_start < end_date:
        current_end = min(
            current_start + relativedelta(months=1),
            end_date
        )

        print(f"Processing: {current_start} to {current_end}")

        # Check which dates already exist
        existing_dates = await get_existing_dates(current_start, current_end)

        # Get dates to scrape
        dates_to_scrape = []
        current = current_start
        while current <= current_end:
            if current not in existing_dates:
                dates_to_scrape.append(current)
            current += timedelta(days=1)

        print(f"  Need to scrape: {len(dates_to_scrape)} days")
        print(f"  Already have: {len(existing_dates)} days")

        # Scrape missing dates
        for date in dates_to_scrape:
            await scrape_and_save_date(date)
            await asyncio.sleep(2)  # Rate limiting

        current_start = current_end + timedelta(days=1)
```

### Strategy 2: Daily Update (Actual Values)

**Approach:** Update data yang sudah ada dengan actual values baru

```python
async def update_actual_values():
    """
    Update events yang actual value-nya baru keluar

    Strategy:
    - Ambil events dari 7 hari terakhir
    - Re-scrape untuk dapat actual values
    - Update database jika ada perubahan
    """

    from datetime import datetime, timedelta

    # Actual values biasanya keluar dalam 7 hari
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)

    print(f"🔄 Updating actual values: {start_date} to {end_date}")

    for date in date_range(start_date, end_date):
        # Scrape date
        new_events = await scrape_date(date)

        # Get existing events
        existing_events = await db.get_events_by_date(date)

        # Compare and update
        updates = 0
        for new_event in new_events:
            existing = find_matching_event(existing_events, new_event)

            if existing:
                # Check if actual value updated
                if new_event.get('actual') and not existing.get('actual'):
                    await db.update_event_actual(existing['id'], new_event['actual'])
                    updates += 1

        print(f"  {date}: {updates} events updated with actual values")
```

### Strategy 3: Smart Incremental Scraping

**Approach:** Intelligent scheduling berdasarkan event release pattern

```python
async def smart_incremental_scrape():
    """
    Smart scraping strategy:
    - Future dates: Scrape once untuk forecast/previous
    - Recent dates (0-7 days): Daily update untuk actual
    - Old dates (>7 days): No need to update
    """

    today = datetime.now().date()

    # 1. Future events (forecast only)
    future_dates = get_dates_needing_forecast(today, today + timedelta(days=7))
    for date in future_dates:
        if not await has_forecast_data(date):
            await scrape_and_save_date(date)

    # 2. Recent events (actual values)
    recent_dates = get_dates_needing_actual(today - timedelta(days=7), today)
    for date in recent_dates:
        if await needs_actual_update(date):
            await update_date_actuals(date)

    # 3. Historical backfill
    oldest_date = await get_oldest_scraped_date()
    target_date = today - timedelta(days=365)

    if oldest_date > target_date:
        # Fill gaps
        await backfill_date_range(target_date, oldest_date)
```

---

## 🤖 Z.ai Integration untuk Parsing

### Parsing Strategy dengan Z.ai

```python
class ZAIEconomicCalendarParser:
    """
    Z.ai GLM untuk parse HTML dan extract events
    Bisa detect struktur HTML yang berubah
    """

    async def parse_html_to_events(
        self,
        html: str,
        target_date: datetime
    ) -> List[Dict]:
        """
        Parse HTML dengan Z.ai

        Z.ai advantages:
        - Adaptive parsing (HTML structure changes)
        - Extract structured data
        - Handle missing fields
        - Quality validation
        """

        prompt = f"""
        Extract economic calendar events for {target_date.strftime('%Y-%m-%d')}.

        HTML Content:
        {html[:20000]}

        Return JSON array with this structure:
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
        - Only include events for date {target_date.strftime('%Y-%m-%d')}
        - If value is empty/missing, use null
        - Keep original value format (%, K, M, B, etc)
        - Impact: high/medium/low based on market importance
        """

        # Call Z.ai GLM
        response = await self.call_zai_api(prompt)

        # Parse JSON
        events = self.extract_json_from_response(response)

        # Validate and clean
        validated_events = self.validate_events(events, target_date)

        return validated_events
```

---

## 📅 MQL5 URL Structure untuk Historical Data

### URL Patterns

```python
# MQL5 calendar URL structure
BASE_URL = "https://www.mql5.com/en/economic-calendar"

# Method 1: Direct date (may not work for all dates)
url = f"{BASE_URL}?date={date.strftime('%Y.%m.%d')}"

# Method 2: Month view
url = f"{BASE_URL}?month={date.strftime('%Y.%m')}"

# Method 3: Week view
url = f"{BASE_URL}?week={date.isocalendar()[1]}"

# Method 4: Default view (current week)
url = BASE_URL  # Shows current week + upcoming
```

### Testing URL Patterns

```python
async def test_mql5_url_patterns():
    """Test which URL pattern works best for historical data"""

    test_dates = [
        datetime(2024, 10, 5),  # Specific date
        datetime(2024, 9, 1),   # Beginning of month
        datetime(2024, 1, 15),  # Old date
    ]

    for date in test_dates:
        print(f"\nTesting date: {date.strftime('%Y-%m-%d')}")

        # Test different URL patterns
        patterns = {
            'date': f"?date={date.strftime('%Y.%m.%d')}",
            'month': f"?month={date.strftime('%Y.%m')}",
            'default': ""
        }

        for pattern_name, pattern in patterns.items():
            url = BASE_URL + pattern
            events = await scrape_url(url)

            # Filter for target date
            date_events = [e for e in events if e['date'] == date.strftime('%Y-%m-%d')]

            print(f"  {pattern_name}: {len(date_events)} events")
```

---

## 🔧 Implementation Plan

### Phase 1: Setup Database & Tracking (Week 1)

```python
# 1. Create database tables
await create_database_schema()

# 2. Implement helper functions
async def get_existing_dates(start_date, end_date):
    """Query date_coverage table"""
    pass

async def has_forecast_data(date):
    """Check if date has forecast data"""
    pass

async def needs_actual_update(date):
    """Check if date needs actual value update"""
    pass
```

### Phase 2: Implement Scraper (Week 1-2)

```python
class MQL5HistoricalScraper:
    def __init__(self):
        self.parser = ZAIEconomicCalendarParser()
        self.db = DatabaseManager()

    async def scrape_date(self, date: datetime) -> List[Dict]:
        """Scrape single date"""
        # Fetch HTML
        html = await self.fetch_mql5_html(date)

        # Parse with Z.ai
        events = await self.parser.parse_html_to_events(html, date)

        return events

    async def save_events(self, events: List[Dict]):
        """Save events to database with upsert"""
        for event in events:
            await self.db.upsert_event(event)

    async def update_coverage(self, date: datetime, event_count: int):
        """Update date_coverage table"""
        await self.db.upsert_coverage(date, event_count)
```

### Phase 3: Backfill Historical (Week 2)

```python
async def run_historical_backfill():
    """Main backfill process"""

    scraper = MQL5HistoricalScraper()

    # Backfill 1 year
    await scraper.backfill_historical_data(months_back=12)

    print("✅ Historical backfill complete!")
```

### Phase 4: Daily Updates (Week 3)

```python
# Schedule daily updates
async def daily_update_job():
    """Run daily at 00:00 UTC"""

    scraper = MQL5HistoricalScraper()

    # Update recent actuals
    await scraper.update_actual_values()

    # Scrape upcoming events
    await scraper.scrape_upcoming_events(days_ahead=7)
```

---

## 📊 Monitoring & Quality Checks

### Data Quality Checks

```python
async def validate_data_quality():
    """Run quality checks on scraped data"""

    checks = {
        'missing_dates': await check_missing_dates(),
        'duplicate_events': await check_duplicates(),
        'forecast_coverage': await check_forecast_coverage(),
        'actual_coverage': await check_actual_coverage(),
    }

    return checks

async def check_missing_dates():
    """Find dates with no data"""
    # Should have data for every trading day
    pass

async def check_forecast_coverage():
    """Check % of events with forecast"""
    # Should be >80%
    pass
```

---

## 🎯 Example Implementation

```python
# Complete example
async def main():
    # Initialize
    scraper = MQL5HistoricalScraper(
        zai_api_key="your-key",
        db_connection="postgresql://..."
    )

    # 1. Initial backfill (one time)
    print("Starting historical backfill...")
    await scraper.backfill_historical_data(months_back=12)

    # 2. Daily update schedule
    scheduler = AsyncIOScheduler()

    # Update actuals daily at 02:00 UTC
    scheduler.add_job(
        scraper.update_actual_values,
        'cron',
        hour=2,
        minute=0
    )

    # Scrape upcoming events daily at 01:00 UTC
    scheduler.add_job(
        scraper.scrape_upcoming_events,
        'cron',
        hour=1,
        minute=0,
        kwargs={'days_ahead': 7}
    )

    # Quality check weekly
    scheduler.add_job(
        validate_data_quality,
        'cron',
        day_of_week='mon',
        hour=3,
        minute=0
    )

    scheduler.start()
```

---

## 🚀 Next Steps

1. ✅ Setup PostgreSQL/ClickHouse tables
2. ✅ Implement base scraper dengan aiohttp
3. ✅ Integrate Z.ai parser
4. ✅ Test URL patterns untuk historical data
5. ✅ Implement backfill logic
6. ✅ Setup daily update scheduler
7. ✅ Add monitoring & alerts

Mau lanjut implement? 🚀
