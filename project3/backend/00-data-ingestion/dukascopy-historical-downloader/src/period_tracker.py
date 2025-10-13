"""
Period Tracker for Dukascopy Historical Downloader
Prevents re-downloading already processed periods
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Set

logger = logging.getLogger(__name__)


class PeriodTracker:
    """
    Tracks downloaded periods to prevent duplicate downloads

    Storage:
    - JSON file with set of downloaded period keys
    - Key format: "{symbol}_{date}" (e.g., "EURUSD_2024-01-01")
    """

    def __init__(self, storage_path: str = "/data/period_tracker.json"):
        """
        Args:
            storage_path: Path to JSON storage file
        """
        self.storage_path = Path(storage_path)
        self.downloaded_periods: Set[str] = self._load()

    def _load(self) -> Set[str]:
        """Load downloaded periods from JSON file"""
        if not self.storage_path.exists():
            logger.info("Period tracker: No existing data, starting fresh")
            return set()

        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                periods = set(data.get('downloaded_periods', []))
                logger.info(f"Period tracker: Loaded {len(periods)} downloaded periods")
                return periods
        except Exception as e:
            logger.warning(f"Failed to load period tracker: {e}, starting fresh")
            return set()

    def _save(self):
        """Save downloaded periods to JSON file"""
        try:
            # Ensure directory exists
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                'downloaded_periods': sorted(list(self.downloaded_periods)),
                'last_updated': datetime.utcnow().isoformat()
            }

            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Period tracker saved: {len(self.downloaded_periods)} periods")
        except Exception as e:
            logger.error(f"Failed to save period tracker: {e}")

    def is_downloaded(self, symbol: str, date: datetime) -> bool:
        """
        Check if a period has been downloaded

        Args:
            symbol: Trading pair (e.g., 'EURUSD')
            date: Date to check

        Returns:
            True if already downloaded
        """
        key = self._make_key(symbol, date)
        return key in self.downloaded_periods

    def mark_downloaded(self, symbol: str, date: datetime):
        """
        Mark a period as downloaded

        Args:
            symbol: Trading pair
            date: Date downloaded
        """
        key = self._make_key(symbol, date)
        self.downloaded_periods.add(key)
        self._save()

    def _make_key(self, symbol: str, date: datetime) -> str:
        """
        Generate period key

        Args:
            symbol: Trading pair
            date: Date

        Returns:
            Key string: "{symbol}_{YYYY-MM-DD}"
        """
        return f"{symbol}_{date.strftime('%Y-%m-%d')}"

    def get_stats(self) -> dict:
        """Get tracker statistics"""
        return {
            'total_downloaded_periods': len(self.downloaded_periods)
        }
