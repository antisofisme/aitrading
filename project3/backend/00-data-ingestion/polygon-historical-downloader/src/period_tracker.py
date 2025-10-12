"""
Period Tracker for Historical Downloader
Tracks downloaded periods to prevent re-downloads and duplication

This solves the 178x duplication issue by maintaining a persistent record
of what data has been downloaded, independent of ClickHouse data checks.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import asyncio
from threading import Lock

logger = logging.getLogger(__name__)


class PeriodTracker:
    """
    Tracks downloaded periods to prevent duplicate downloads

    Storage format:
    {
        "EUR/USD_1m": [
            {
                "start": "2015-01-01T00:00:00+00:00",
                "end": "2015-04-01T23:59:59+00:00",
                "downloaded_at": "2025-10-10T10:30:00+00:00",
                "source": "polygon_historical",
                "bars_count": 125000,
                "verified": true
            }
        ]
    }
    """

    def __init__(self, tracker_file: str = "/data/downloaded_periods.json"):
        self.tracker_file = Path(tracker_file)
        self.periods: Dict[str, List[dict]] = {}
        self.lock = Lock()

        # Ensure data directory exists
        self.tracker_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing periods
        self._load()

        logger.info(f"📋 Period tracker initialized: {self.tracker_file}")
        logger.info(f"📊 Tracking {len(self.periods)} symbol/timeframe combinations")

    def _load(self):
        """Load periods from JSON file"""
        with self.lock:
            try:
                if self.tracker_file.exists():
                    with open(self.tracker_file, 'r') as f:
                        self.periods = json.load(f)
                    logger.info(f"✅ Loaded {len(self.periods)} tracked periods from {self.tracker_file}")
                else:
                    logger.info(f"📝 No existing tracker file, starting fresh")
                    self.periods = {}
            except Exception as e:
                logger.error(f"❌ Error loading tracker file: {e}")
                logger.warning(f"⚠️  Starting with empty tracker")
                self.periods = {}

    def _save(self):
        """Save periods to JSON file"""
        try:
            with self.lock:
                with open(self.tracker_file, 'w') as f:
                    json.dump(self.periods, f, indent=2)
                logger.debug(f"💾 Saved periods to {self.tracker_file}")
        except Exception as e:
            logger.error(f"❌ Error saving tracker file: {e}")

    def _get_key(self, symbol: str, timeframe: str) -> str:
        """Generate key for symbol/timeframe combination"""
        return f"{symbol}_{timeframe}"

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to timezone-aware datetime"""
        try:
            dt = datetime.fromisoformat(date_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception as e:
            logger.error(f"Error parsing date {date_str}: {e}")
            raise

    def is_period_downloaded(
        self,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a period has already been downloaded

        Args:
            symbol: Trading pair (e.g., "EUR/USD")
            timeframe: Timeframe (e.g., "1m", "5m")
            start_date: Start date (ISO format or YYYY-MM-DD)
            end_date: End date (ISO format or YYYY-MM-DD)

        Returns:
            (is_downloaded, reason)
            - True if period is covered by existing downloads
            - False if period needs to be downloaded
        """
        key = self._get_key(symbol, timeframe)

        with self.lock:
            # No records for this symbol/timeframe
            if key not in self.periods:
                return False, "No previous downloads recorded"

            try:
                # Parse requested dates
                if len(start_date) == 10:  # YYYY-MM-DD
                    requested_start = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                else:
                    requested_start = self._parse_date(start_date)

                if end_date in ['now', 'today']:
                    requested_end = datetime.now(timezone.utc)
                elif len(end_date) == 10:
                    requested_end = datetime.strptime(end_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                else:
                    requested_end = self._parse_date(end_date)

                # Check if any existing period covers this range
                for period in self.periods[key]:
                    existing_start = self._parse_date(period['start'])
                    existing_end = self._parse_date(period['end'])

                    # Check if requested range is fully covered
                    if existing_start <= requested_start and existing_end >= requested_end:
                        downloaded_at = period.get('downloaded_at', 'unknown')
                        bars_count = period.get('bars_count', 'unknown')

                        reason = (
                            f"Already downloaded on {downloaded_at} "
                            f"({bars_count} bars, verified={period.get('verified', False)})"
                        )

                        logger.info(f"✅ {key} period {start_date} to {end_date} already covered")
                        logger.info(f"   Existing: {existing_start.date()} to {existing_end.date()}")

                        return True, reason

                # Not fully covered
                return False, "Period not fully covered by existing downloads"

            except Exception as e:
                logger.error(f"Error checking period: {e}")
                # On error, return False to be safe (allow download)
                return False, f"Error checking period: {e}"

    def mark_downloaded(
        self,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
        bars_count: int = 0,
        source: str = "polygon_historical",
        verified: bool = False
    ):
        """
        Mark a period as downloaded

        Args:
            symbol: Trading pair
            timeframe: Timeframe
            start_date: Start date (ISO format or YYYY-MM-DD)
            end_date: End date (ISO format or YYYY-MM-DD)
            bars_count: Number of bars downloaded
            source: Data source (polygon_historical or polygon_gap_fill)
            verified: Whether data was verified in ClickHouse
        """
        key = self._get_key(symbol, timeframe)

        try:
            # Parse dates
            if len(start_date) == 10:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            else:
                start_dt = self._parse_date(start_date)

            if end_date in ['now', 'today']:
                end_dt = datetime.now(timezone.utc)
            elif len(end_date) == 10:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            else:
                end_dt = self._parse_date(end_date)

            # Create period record
            period_record = {
                'start': start_dt.isoformat(),
                'end': end_dt.isoformat(),
                'downloaded_at': datetime.now(timezone.utc).isoformat(),
                'source': source,
                'bars_count': bars_count,
                'verified': verified
            }

            with self.lock:
                # Initialize list if needed
                if key not in self.periods:
                    self.periods[key] = []

                # Add period record
                self.periods[key].append(period_record)

            # Save to disk (already has its own lock)
            self._save()

            logger.info(f"✅ Marked {key} as downloaded: {start_date} to {end_date} ({bars_count} bars)")

        except Exception as e:
            logger.error(f"❌ Error marking period as downloaded: {e}")

    def get_downloaded_periods(self, symbol: str, timeframe: str) -> List[dict]:
        """
        Get all downloaded periods for a symbol/timeframe

        Returns: List of period records
        """
        key = self._get_key(symbol, timeframe)
        with self.lock:
            return self.periods.get(key, []).copy()

    def get_missing_ranges(
        self,
        symbol: str,
        timeframe: str,
        requested_start: str,
        requested_end: str
    ) -> List[Tuple[str, str]]:
        """
        Calculate missing date ranges that need to be downloaded

        Returns: List of (start_date, end_date) tuples for missing ranges
        """
        # Check if period is already downloaded
        is_downloaded, reason = self.is_period_downloaded(
            symbol, timeframe, requested_start, requested_end
        )

        if is_downloaded:
            return []  # Nothing missing

        # For simplicity, return the full requested range if not covered
        # A more sophisticated implementation could calculate precise gaps
        return [(requested_start, requested_end)]

    def clear_symbol(self, symbol: str, timeframe: Optional[str] = None):
        """
        Clear tracking for a symbol (useful for testing or re-downloads)

        Args:
            symbol: Trading pair
            timeframe: Optional specific timeframe (if None, clears all timeframes)
        """
        with self.lock:
            if timeframe:
                key = self._get_key(symbol, timeframe)
                if key in self.periods:
                    del self.periods[key]
                    self._save()
                    logger.info(f"🗑️  Cleared tracking for {key}")
            else:
                # Clear all timeframes for this symbol
                keys_to_delete = [k for k in self.periods.keys() if k.startswith(f"{symbol}_")]
                for key in keys_to_delete:
                    del self.periods[key]

                self._save()
                logger.info(f"🗑️  Cleared all tracking for {symbol} ({len(keys_to_delete)} timeframes)")

    def get_stats(self) -> dict:
        """Get tracker statistics"""
        with self.lock:
            total_periods = sum(len(periods) for periods in self.periods.values())
            total_bars = sum(
                sum(p.get('bars_count', 0) for p in periods)
                for periods in self.periods.values()
            )

            return {
                'tracked_combinations': len(self.periods),
                'total_periods': total_periods,
                'total_bars_tracked': total_bars,
                'tracker_file': str(self.tracker_file)
            }
