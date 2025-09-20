# Service infrastructure - use absolute imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

try:
    from shared.infrastructure.core.logger_core import get_logger
    from shared.infrastructure.core.error_core import handle_error
    from shared.infrastructure.core.performance_core import performance_tracked
    from shared.infrastructure.core.config_core import CoreConfig
    from shared.infrastructure.core.cache_core import CoreCache
except ImportError as e:
    print(f"⚠️ Infrastructure import issue: {e}")
    # Fallback implementations
    import logging
    
    def get_logger(name, version=None):
        return logging.getLogger(name)
    
    def handle_error(service_name, error, context=None):
        print(f"Error in {service_name}: {error}")
        if context:
            print(f"Context: {context}")
    
    def performance_tracked(service_name, operation_name):
        def decorator(func):
            return func
        return decorator
    
    class CoreConfig:
        def __init__(self, service_name=None):
            pass
        def get(self, key, default=None):
            return default
    
    class CoreCache:
        def __init__(self, name, max_size=1000, default_ttl=300):
            self.name = name
            self.max_size = max_size
            self.default_ttl = default_ttl
            self.cache = {}
        
        async def get(self, key): 
            return None
        
        async def set(self, key, value, ttl=None): 
            pass

"""
Trading Calendar - Forex Market Hours & Weekend Management
Smart handling of trading days to ensure data consistency for ML/DL processing
"""

import pytz
from datetime import datetime, timedelta, time
from typing import List, Dict, Optional, Tuple, Set
import holidays
logger = get_logger("data-bridge", "trading-calendar")

class ForexTradingCalendar:
    """
    Forex Trading Calendar - Manages market hours and trading days
    
    Features:
    - Weekend detection (Saturday-Sunday no data)
    - Market holidays handling
    - Trading session analysis (Sydney, Tokyo, London, New York)
    - Data consistency for ML/DL pipelines
    """
    
    def __init__(self):
        # Major forex market timezones
        self.sydney_tz = pytz.timezone('Australia/Sydney')
        self.tokyo_tz = pytz.timezone('Asia/Tokyo') 
        self.london_tz = pytz.timezone('Europe/London')
        self.newyork_tz = pytz.timezone('America/New_York')
        self.utc_tz = pytz.UTC
        
        # NOTE: Forex market does NOT close for national holidays
        # Only weekends (Saturday-Sunday) affect forex trading
        # National holidays do NOT impact forex market hours
        
        # Trading sessions in UTC (approximate)
        self.trading_sessions = {
            'sydney': {'start': time(21, 0), 'end': time(6, 0)},     # 21:00-06:00 UTC
            'tokyo': {'start': time(23, 0), 'end': time(8, 0)},      # 23:00-08:00 UTC  
            'london': {'start': time(7, 0), 'end': time(16, 0)},     # 07:00-16:00 UTC
            'newyork': {'start': time(12, 0), 'end': time(21, 0)}    # 12:00-21:00 UTC
        }
        
        logger.info("🗓️ Forex Trading Calendar initialized")
        logger.info("📍 Tracking: Sydney, Tokyo, London, New York sessions")
        logger.info("⚠️ Forex only closes weekends (Sat-Sun), NOT national holidays")
    
    def is_trading_day(self, dt: datetime) -> bool:
        """
        Check if a given datetime is a trading day
        
        IMPORTANT: Forex market only closes on weekends (Saturday-Sunday)
        National holidays do NOT affect forex trading (24/5 market)
        
        Args:
            dt: Datetime to check (any timezone, will convert to UTC)
            
        Returns:
            bool: True if trading day, False ONLY for weekends
        """
        # Convert to UTC if needed
        if dt.tzinfo is None:
            dt = self.utc_tz.localize(dt)
        elif dt.tzinfo != self.utc_tz:
            dt = dt.astimezone(self.utc_tz)
        
        # Check if weekend (Saturday = 5, Sunday = 6)
        weekday = dt.weekday()
        if weekday >= 5:  # Saturday or Sunday
            logger.debug(f"📅 {dt.strftime('%Y-%m-%d %H:%M')} is weekend (day {weekday}) - forex closed")
            return False
        
        # Forex trades 24/5 - NO holiday closures (unlike stock markets)
        return True
    
    def is_active_trading_hour(self, dt: datetime) -> Tuple[bool, List[str]]:
        """
        Check if a datetime falls within active trading hours
        
        Args:
            dt: Datetime to check
            
        Returns:
            Tuple[bool, List[str]]: (is_active, list_of_active_sessions)
        """
        if not self.is_trading_day(dt):
            return False, []
        
        # Convert to UTC
        if dt.tzinfo is None:
            dt = self.utc_tz.localize(dt)
        elif dt.tzinfo != self.utc_tz:
            dt = dt.astimezone(self.utc_tz)
        
        current_time = dt.time()
        active_sessions = []
        
        # Check each trading session
        for session, times in self.trading_sessions.items():
            start_time = times['start']
            end_time = times['end']
            
            # Handle sessions that cross midnight (like Sydney)
            if start_time > end_time:
                # Session crosses midnight
                if current_time >= start_time or current_time <= end_time:
                    active_sessions.append(session)
            else:
                # Normal session within same day
                if start_time <= current_time <= end_time:
                    active_sessions.append(session)
        
        return len(active_sessions) > 0, active_sessions
    
    def get_trading_days_range(self, start_date: datetime, end_date: datetime) -> List[datetime]:
        """
        Get list of trading days between start and end date
        
        Args:
            start_date: Start datetime
            end_date: End datetime
            
        Returns:
            List[datetime]: List of trading days only
        """
        trading_days = []
        current = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        while current <= end_date:
            if self.is_trading_day(current):
                trading_days.append(current)
            current += timedelta(days=1)
        
        logger.info(f"📊 Found {len(trading_days)} trading days between {start_date.date()} and {end_date.date()}")
        return trading_days
    
    def get_next_trading_day(self, dt: datetime) -> datetime:
        """
        Get the next trading day after given datetime
        
        Args:
            dt: Reference datetime
            
        Returns:
            datetime: Next trading day
        """
        next_day = dt + timedelta(days=1)
        next_day = next_day.replace(hour=0, minute=0, second=0, microsecond=0)
        
        while not self.is_trading_day(next_day):
            next_day += timedelta(days=1)
        
        return next_day
    
    def get_previous_trading_day(self, dt: datetime) -> datetime:
        """
        Get the previous trading day before given datetime
        
        Args:
            dt: Reference datetime
            
        Returns:
            datetime: Previous trading day
        """
        prev_day = dt - timedelta(days=1)
        prev_day = prev_day.replace(hour=23, minute=59, second=59, microsecond=0)
        
        while not self.is_trading_day(prev_day):
            prev_day -= timedelta(days=1)
        
        return prev_day
    
    def filter_trading_hours_only(self, datetime_list: List[datetime]) -> List[datetime]:
        """
        Filter list to include only trading hours
        
        Args:
            datetime_list: List of datetime objects
            
        Returns:
            List[datetime]: Filtered list with trading hours only
        """
        filtered = []
        skipped_weekend = 0
        skipped_inactive = 0
        
        for dt in datetime_list:
            if not self.is_trading_day(dt):
                # Only weekends get skipped (no holidays in forex)
                skipped_weekend += 1
                continue
            
            is_active, sessions = self.is_active_trading_hour(dt)
            if is_active:
                filtered.append(dt)
            else:
                skipped_inactive += 1
        
        logger.info(f"📊 Trading hours filter results:")
        logger.info(f"  ✅ Kept: {len(filtered)} trading hours")
        logger.info(f"  ❌ Skipped weekends: {skipped_weekend}")
        logger.info(f"  ❌ Skipped inactive hours: {skipped_inactive}")
        
        return filtered
    
    def get_optimal_download_times(self, hours_back: int = 24) -> List[datetime]:
        """
        Get optimal times to download data, skipping weekends/holidays
        
        Args:
            hours_back: How many hours back to generate
            
        Returns:
            List[datetime]: List of optimal download times (trading hours only)
        """
        end_time = datetime.now(self.utc_tz)
        start_time = end_time - timedelta(hours=hours_back)
        
        # Generate hourly intervals
        current = start_time.replace(minute=0, second=0, microsecond=0)
        all_hours = []
        
        while current <= end_time:
            all_hours.append(current)
            current += timedelta(hours=1)
        
        # Filter to trading hours only
        trading_hours = self.filter_trading_hours_only(all_hours)
        
        logger.info(f"🎯 Generated {len(trading_hours)} optimal download times from {len(all_hours)} total hours")
        return trading_hours
    
    def should_download_now(self) -> Tuple[bool, str]:
        """
        Check if current time is suitable for downloading
        
        Note: Downloads can happen ANY TIME (including weekends)
        This only affects the data range being requested, not download timing
        
        Returns:
            Tuple[bool, str]: (should_download, reason)
        """
        now = datetime.now(self.utc_tz)
        
        # ALWAYS allow downloads - even on weekends!
        # The filtering happens on DATA RANGE, not download time
        return True, "Download allowed anytime - data filtering handles weekends"
    
    def get_market_status(self, dt: Optional[datetime] = None) -> Dict:
        """
        Get comprehensive market status for a given datetime
        
        Args:
            dt: Datetime to check (default: now)
            
        Returns:
            Dict: Market status information
        """
        if dt is None:
            dt = datetime.now(self.utc_tz)
        
        # Convert to UTC
        if dt.tzinfo is None:
            dt = self.utc_tz.localize(dt)
        elif dt.tzinfo != self.utc_tz:
            dt = dt.astimezone(self.utc_tz)
        
        is_trading = self.is_trading_day(dt)
        is_active, active_sessions = self.is_active_trading_hour(dt)
        
        status = {
            'datetime': dt.isoformat(),
            'is_trading_day': is_trading,
            'is_active_hour': is_active,
            'active_sessions': active_sessions,
            'weekday': dt.strftime('%A'),
            'weekday_num': dt.weekday(),
            'is_weekend': dt.weekday() >= 5,
            'utc_time': dt.strftime('%H:%M UTC')
        }
        
        # ALWAYS allow downloads - just inform about data quality
        status['recommendation'] = 'DOWNLOAD'
        
        if is_trading and is_active:
            status['reason'] = f"Active trading data - {', '.join(active_sessions)} session(s)"
            status['data_quality'] = 'EXCELLENT'
        elif is_trading and not is_active:
            status['reason'] = "Trading day but inactive hours - limited data"
            status['data_quality'] = 'LIMITED'
        else:
            # Only weekends affect forex (no holidays)
            status['reason'] = f"Weekend ({dt.strftime('%A')}) - forex market closed"
            status['data_quality'] = 'NONE'
        
        return status

# Global trading calendar instance
_trading_calendar = None

def get_trading_calendar() -> ForexTradingCalendar:
    """Get singleton trading calendar instance"""
    global _trading_calendar
    if _trading_calendar is None:
        _trading_calendar = ForexTradingCalendar()
    return _trading_calendar