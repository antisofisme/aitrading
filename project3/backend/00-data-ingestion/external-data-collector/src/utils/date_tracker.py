"""
Date Tracking Utility
Untuk track data yang sudah/belum di-scrape
"""
from datetime import datetime, timedelta, date
from typing import List, Dict, Set, Optional
from pathlib import Path
import json
import asyncpg


class DateTracker:
    """
    Track scraping progress dan identify missing dates

    Features:
    - Track completed dates
    - Identify gaps in coverage
    - Determine which dates need updates
    - Generate scraping schedule
    """

    def __init__(self, db_connection_string: Optional[str] = None):
        """
        Initialize tracker

        Args:
            db_connection_string: PostgreSQL connection string
                                 If None, use JSON file for tracking
        """
        self.db_conn_str = db_connection_string
        self.use_db = db_connection_string is not None

        # JSON file fallback
        self.tracking_file = Path(__file__).parent.parent.parent / 'data' / 'date_tracking.json'
        self.tracking_file.parent.mkdir(exist_ok=True)

    # ========================================================================
    # Database Methods
    # ========================================================================

    async def get_db_connection(self):
        """Get database connection"""
        if not self.use_db:
            raise ValueError("Database not configured")
        return await asyncpg.connect(self.db_conn_str)

    async def init_database(self):
        """Initialize database tables"""
        conn = await self.get_db_connection()

        try:
            # Create date_coverage table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS date_coverage (
                    date DATE PRIMARY KEY,
                    events_count INTEGER DEFAULT 0,
                    has_forecast BOOLEAN DEFAULT FALSE,
                    has_actual BOOLEAN DEFAULT FALSE,
                    first_scraped_at TIMESTAMP,
                    last_updated_at TIMESTAMP,
                    needs_update BOOLEAN DEFAULT FALSE
                )
            """)

            # Create scraping_history table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS scraping_history (
                    id SERIAL PRIMARY KEY,
                    scrape_date DATE NOT NULL,
                    events_found INTEGER DEFAULT 0,
                    events_new INTEGER DEFAULT 0,
                    events_updated INTEGER DEFAULT 0,
                    status VARCHAR(20),
                    error_message TEXT,
                    scraped_at TIMESTAMP DEFAULT NOW(),
                    duration_seconds INTEGER
                )
            """)

            # Create indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_needs_update
                ON date_coverage(needs_update)
            """)

            print("✅ Database tables initialized")

        finally:
            await conn.close()

    async def mark_date_scraped(
        self,
        scrape_date: date,
        events_count: int,
        has_forecast: bool = False,
        has_actual: bool = False
    ):
        """Mark a date as scraped"""

        if self.use_db:
            conn = await self.get_db_connection()
            try:
                await conn.execute("""
                    INSERT INTO date_coverage
                        (date, events_count, has_forecast, has_actual,
                         first_scraped_at, last_updated_at)
                    VALUES ($1, $2, $3, $4, NOW(), NOW())
                    ON CONFLICT (date) DO UPDATE SET
                        events_count = $2,
                        has_forecast = $3,
                        has_actual = $4,
                        last_updated_at = NOW()
                """, scrape_date, events_count, has_forecast, has_actual)
            finally:
                await conn.close()
        else:
            # JSON file fallback
            tracking = self.load_tracking_file()
            date_str = scrape_date.strftime('%Y-%m-%d')

            tracking[date_str] = {
                'events_count': events_count,
                'has_forecast': has_forecast,
                'has_actual': has_actual,
                'last_updated': datetime.now().isoformat()
            }

            self.save_tracking_file(tracking)

    async def get_scraped_dates(
        self,
        start_date: date,
        end_date: date
    ) -> Set[date]:
        """Get all dates that have been scraped in range"""

        if self.use_db:
            conn = await self.get_db_connection()
            try:
                rows = await conn.fetch("""
                    SELECT date FROM date_coverage
                    WHERE date >= $1 AND date <= $2
                """, start_date, end_date)

                return {row['date'] for row in rows}
            finally:
                await conn.close()
        else:
            # JSON file fallback
            tracking = self.load_tracking_file()
            scraped = set()

            current = start_date
            while current <= end_date:
                date_str = current.strftime('%Y-%m-%d')
                if date_str in tracking:
                    scraped.add(current)
                current += timedelta(days=1)

            return scraped

    async def get_missing_dates(
        self,
        start_date: date,
        end_date: date,
        include_weekends: bool = False
    ) -> List[date]:
        """
        Get dates that haven't been scraped yet

        Args:
            start_date: Start of range
            end_date: End of range
            include_weekends: Include Saturday/Sunday

        Returns:
            List of missing dates
        """
        scraped_dates = await self.get_scraped_dates(start_date, end_date)

        missing = []
        current = start_date

        while current <= end_date:
            # Skip weekends if not included
            if not include_weekends and current.weekday() >= 5:
                current += timedelta(days=1)
                continue

            if current not in scraped_dates:
                missing.append(current)

            current += timedelta(days=1)

        return missing

    async def get_dates_needing_update(
        self,
        days_back: int = 7
    ) -> List[date]:
        """
        Get recent dates that might have new actual values

        Args:
            days_back: How many days to check

        Returns:
            List of dates needing update
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)

        if self.use_db:
            conn = await self.get_db_connection()
            try:
                rows = await conn.fetch("""
                    SELECT date FROM date_coverage
                    WHERE date >= $1 AND date <= $2
                      AND has_forecast = TRUE
                      AND (has_actual = FALSE OR needs_update = TRUE)
                    ORDER BY date
                """, start_date, end_date)

                return [row['date'] for row in rows]
            finally:
                await conn.close()
        else:
            # JSON file fallback
            tracking = self.load_tracking_file()
            needs_update = []

            current = start_date
            while current <= end_date:
                date_str = current.strftime('%Y-%m-%d')

                if date_str in tracking:
                    data = tracking[date_str]
                    if data.get('has_forecast') and not data.get('has_actual'):
                        needs_update.append(current)

                current += timedelta(days=1)

            return needs_update

    # ========================================================================
    # JSON File Methods (Fallback)
    # ========================================================================

    def load_tracking_file(self) -> Dict:
        """Load tracking data from JSON file"""
        if self.tracking_file.exists():
            with open(self.tracking_file, 'r') as f:
                return json.load(f)
        return {}

    def save_tracking_file(self, data: Dict):
        """Save tracking data to JSON file"""
        with open(self.tracking_file, 'w') as f:
            json.dump(data, f, indent=2)

    # ========================================================================
    # Scraping Schedule Generation
    # ========================================================================

    async def generate_backfill_schedule(
        self,
        months_back: int = 12,
        batch_days: int = 30
    ) -> List[Dict]:
        """
        Generate batched schedule for historical backfill

        Args:
            months_back: How many months to go back
            batch_days: Days per batch

        Returns:
            List of batches with {start_date, end_date, missing_count}
        """
        from dateutil.relativedelta import relativedelta

        end_date = datetime.now().date()
        start_date = end_date - relativedelta(months=months_back)

        batches = []
        current_start = start_date

        while current_start < end_date:
            current_end = min(
                current_start + timedelta(days=batch_days - 1),
                end_date
            )

            # Get missing dates in this batch
            missing = await self.get_missing_dates(current_start, current_end)

            batches.append({
                'start_date': current_start,
                'end_date': current_end,
                'missing_count': len(missing),
                'missing_dates': missing
            })

            current_start = current_end + timedelta(days=1)

        return batches

    async def get_coverage_stats(self) -> Dict:
        """Get overall coverage statistics"""

        if self.use_db:
            conn = await self.get_db_connection()
            try:
                stats = await conn.fetchrow("""
                    SELECT
                        COUNT(*) as total_dates,
                        SUM(events_count) as total_events,
                        COUNT(*) FILTER (WHERE has_forecast) as dates_with_forecast,
                        COUNT(*) FILTER (WHERE has_actual) as dates_with_actual,
                        MIN(date) as earliest_date,
                        MAX(date) as latest_date
                    FROM date_coverage
                """)

                return dict(stats)
            finally:
                await conn.close()
        else:
            # JSON file fallback
            tracking = self.load_tracking_file()

            if not tracking:
                return {
                    'total_dates': 0,
                    'total_events': 0,
                    'dates_with_forecast': 0,
                    'dates_with_actual': 0
                }

            total_events = sum(d.get('events_count', 0) for d in tracking.values())
            with_forecast = sum(1 for d in tracking.values() if d.get('has_forecast'))
            with_actual = sum(1 for d in tracking.values() if d.get('has_actual'))

            dates = sorted(tracking.keys())

            return {
                'total_dates': len(tracking),
                'total_events': total_events,
                'dates_with_forecast': with_forecast,
                'dates_with_actual': with_actual,
                'earliest_date': dates[0] if dates else None,
                'latest_date': dates[-1] if dates else None
            }


# Convenience functions
async def get_dates_to_scrape(months_back: int = 12) -> List[date]:
    """Get list of dates that need to be scraped"""
    tracker = DateTracker()

    from dateutil.relativedelta import relativedelta
    end_date = datetime.now().date()
    start_date = end_date - relativedelta(months=months_back)

    missing = await tracker.get_missing_dates(start_date, end_date)

    return missing


async def print_coverage_report():
    """Print coverage statistics"""
    tracker = DateTracker()
    stats = await tracker.get_coverage_stats()

    print("=" * 80)
    print("📊 SCRAPING COVERAGE REPORT")
    print("=" * 80)
    print()
    print(f"Total Dates Scraped:     {stats.get('total_dates', 0)}")
    print(f"Total Events:            {stats.get('total_events', 0)}")
    print(f"Dates with Forecast:     {stats.get('dates_with_forecast', 0)}")
    print(f"Dates with Actual:       {stats.get('dates_with_actual', 0)}")

    if stats.get('earliest_date'):
        print(f"Earliest Date:           {stats['earliest_date']}")
        print(f"Latest Date:             {stats['latest_date']}")

    print()
