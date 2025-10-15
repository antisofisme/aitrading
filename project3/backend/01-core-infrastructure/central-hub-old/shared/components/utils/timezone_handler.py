"""
Timezone Handler - Universal Timestamp Standardization for Multi-Tenant Trading System

🌍 PROBLEM SOLVED:
1. API timestamps (Polygon.io): UTC
2. System internal: UTC
3. Multi-tenant clients: Different timezones (WIB, WITA, WIT, EST, etc.)
4. MT4/MT5 brokers: GMT+2, GMT+3, etc.

🎯 SOLUTION: 3-Layer Strategy
- Layer 1: Storage (ALWAYS UTC)
- Layer 2: API (UTC + Unix epoch)
- Layer 3: Client Display (Localized on request)

📋 STANDARDS:
- ISO 8601: "2025-10-11T04:58:00.000Z"
- Unix epoch (ms): 1760156280000
- Timezone-aware: datetime.now(timezone.utc)
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Union
import pytz
from zoneinfo import ZoneInfo


class TimezoneHandler:
    """
    Universal timezone handler for multi-tenant trading system

    Key Principles:
    1. ALWAYS store in UTC
    2. ALWAYS return both UTC + localized timestamps
    3. Client chooses display timezone
    4. Use Unix epoch (ms) for comparisons
    """

    # Common trading timezones
    TRADING_TIMEZONES = {
        # Asia
        "WIB": "Asia/Jakarta",       # UTC+7 (Indonesia Western)
        "WITA": "Asia/Makassar",     # UTC+8 (Indonesia Central)
        "WIT": "Asia/Jayapura",      # UTC+9 (Indonesia Eastern)
        "SGT": "Asia/Singapore",     # UTC+8
        "HKT": "Asia/Hong_Kong",     # UTC+8
        "JST": "Asia/Tokyo",         # UTC+9

        # Europe
        "GMT": "Europe/London",      # UTC+0
        "CET": "Europe/Paris",       # UTC+1
        "EET": "Europe/Athens",      # UTC+2

        # Americas
        "EST": "America/New_York",   # UTC-5
        "CST": "America/Chicago",    # UTC-6
        "PST": "America/Los_Angeles",# UTC-8

        # MT4/MT5 Broker Times
        "GMT+2": "Etc/GMT-2",        # Most MT4 brokers
        "GMT+3": "Etc/GMT-3",        # Some MT5 brokers
    }

    @staticmethod
    def now_utc() -> datetime:
        """
        Get current time in UTC (timezone-aware)

        Returns:
            datetime with UTC timezone

        Example:
            >>> now = TimezoneHandler.now_utc()
            >>> print(now)
            2025-10-11 04:58:00+00:00
        """
        return datetime.now(timezone.utc)

    @staticmethod
    def to_utc(dt: Union[datetime, str, int, float], from_tz: str = "UTC") -> datetime:
        """
        Convert any datetime to UTC timezone-aware datetime

        Args:
            dt: datetime object, ISO string, or Unix timestamp (ms)
            from_tz: Source timezone (if dt is naive)

        Returns:
            datetime with UTC timezone

        Examples:
            >>> # From naive datetime
            >>> dt = datetime(2025, 10, 11, 11, 58, 0)  # WIB time
            >>> utc = TimezoneHandler.to_utc(dt, from_tz="WIB")
            >>> print(utc)
            2025-10-11 04:58:00+00:00

            >>> # From ISO string
            >>> utc = TimezoneHandler.to_utc("2025-10-11T11:58:00+07:00")
            >>> print(utc)
            2025-10-11 04:58:00+00:00

            >>> # From Unix epoch (ms)
            >>> utc = TimezoneHandler.to_utc(1760156280000)
            >>> print(utc)
            2025-10-11 04:58:00+00:00
        """
        # Handle Unix timestamp (ms)
        if isinstance(dt, (int, float)):
            return datetime.fromtimestamp(dt / 1000.0, tz=timezone.utc)

        # Handle ISO string
        if isinstance(dt, str):
            # Parse ISO 8601
            if '+' in dt or 'Z' in dt:
                # Already has timezone info
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            else:
                # Naive string, assume from_tz
                dt = datetime.fromisoformat(dt)
                tz = TimezoneHandler._get_timezone(from_tz)
                dt = dt.replace(tzinfo=tz)

            return dt.astimezone(timezone.utc)

        # Handle datetime object
        if dt.tzinfo is None:
            # Naive datetime, add timezone
            tz = TimezoneHandler._get_timezone(from_tz)
            dt = dt.replace(tzinfo=tz)

        return dt.astimezone(timezone.utc)

    @staticmethod
    def to_timezone(dt: Union[datetime, str, int, float], to_tz: str) -> datetime:
        """
        Convert datetime to specific timezone

        Args:
            dt: datetime object, ISO string, or Unix timestamp (ms)
            to_tz: Target timezone

        Returns:
            datetime in target timezone

        Example:
            >>> utc_time = TimezoneHandler.now_utc()
            >>> wib_time = TimezoneHandler.to_timezone(utc_time, "WIB")
            >>> print(f"UTC: {utc_time}")
            UTC: 2025-10-11 04:58:00+00:00
            >>> print(f"WIB: {wib_time}")
            WIB: 2025-10-11 11:58:00+07:00
        """
        # First convert to UTC
        utc_dt = TimezoneHandler.to_utc(dt)

        # Then convert to target timezone
        target_tz = TimezoneHandler._get_timezone(to_tz)
        return utc_dt.astimezone(target_tz)

    @staticmethod
    def to_unix_ms(dt: Union[datetime, str]) -> int:
        """
        Convert datetime to Unix timestamp in milliseconds

        Args:
            dt: datetime object or ISO string

        Returns:
            Unix timestamp in milliseconds

        Example:
            >>> dt = TimezoneHandler.now_utc()
            >>> ms = TimezoneHandler.to_unix_ms(dt)
            >>> print(ms)
            1760156280000
        """
        if isinstance(dt, str):
            dt = TimezoneHandler.to_utc(dt)

        return int(dt.timestamp() * 1000)

    @staticmethod
    def format_iso(dt: datetime) -> str:
        """
        Format datetime to ISO 8601 string with timezone

        Args:
            dt: datetime object

        Returns:
            ISO 8601 string

        Example:
            >>> dt = TimezoneHandler.now_utc()
            >>> iso = TimezoneHandler.format_iso(dt)
            >>> print(iso)
            2025-10-11T04:58:00.000Z
        """
        if dt.tzinfo is None:
            # Assume UTC if naive
            dt = dt.replace(tzinfo=timezone.utc)

        # Format with timezone
        return dt.isoformat(timespec='milliseconds')

    @staticmethod
    def create_multi_tz_response(
        dt: Union[datetime, str, int, float],
        timezones: list[str] = ["UTC", "WIB"]
    ) -> Dict[str, str]:
        """
        Create multi-timezone response for API

        Args:
            dt: datetime object, ISO string, or Unix timestamp
            timezones: List of timezone codes to include

        Returns:
            Dictionary with timestamps in multiple timezones

        Example:
            >>> dt = TimezoneHandler.now_utc()
            >>> response = TimezoneHandler.create_multi_tz_response(dt, ["UTC", "WIB", "EST"])
            >>> print(response)
            {
                "timestamp_ms": 1760156280000,
                "timestamp_utc": "2025-10-11T04:58:00.000Z",
                "timestamp_wib": "2025-10-11T11:58:00.000+07:00",
                "timestamp_est": "2025-10-10T23:58:00.000-05:00"
            }
        """
        # Convert to UTC
        utc_dt = TimezoneHandler.to_utc(dt)

        result = {
            "timestamp_ms": TimezoneHandler.to_unix_ms(utc_dt)
        }

        for tz_code in timezones:
            localized_dt = TimezoneHandler.to_timezone(utc_dt, tz_code)
            key = f"timestamp_{tz_code.lower().replace('+', 'p').replace('-', 'm')}"
            result[key] = TimezoneHandler.format_iso(localized_dt)

        return result

    @staticmethod
    def _get_timezone(tz_code: str) -> Union[timezone, ZoneInfo]:
        """
        Get timezone object from code

        Args:
            tz_code: Timezone code (e.g., "UTC", "WIB", "EST")

        Returns:
            Timezone object
        """
        if tz_code == "UTC":
            return timezone.utc

        # Check if it's a known trading timezone
        if tz_code in TimezoneHandler.TRADING_TIMEZONES:
            tz_name = TimezoneHandler.TRADING_TIMEZONES[tz_code]
        else:
            tz_name = tz_code

        try:
            return ZoneInfo(tz_name)
        except Exception:
            # Fallback to pytz
            return pytz.timezone(tz_name)

    @staticmethod
    def get_trading_hours_utc(
        open_time: str,
        close_time: str,
        local_tz: str = "WIB"
    ) -> tuple[datetime, datetime]:
        """
        Convert local trading hours to UTC

        Args:
            open_time: Local opening time (HH:MM)
            close_time: Local closing time (HH:MM)
            local_tz: Local timezone code

        Returns:
            Tuple of (open_utc, close_utc)

        Example:
            >>> # Indonesian market: 09:00-16:00 WIB
            >>> open_utc, close_utc = TimezoneHandler.get_trading_hours_utc("09:00", "16:00", "WIB")
            >>> print(f"Open UTC: {open_utc.time()}")
            Open UTC: 02:00:00
            >>> print(f"Close UTC: {close_utc.time()}")
            Close UTC: 09:00:00
        """
        # Get today's date in local timezone
        local_tz_obj = TimezoneHandler._get_timezone(local_tz)
        today_local = datetime.now(local_tz_obj).date()

        # Parse times
        open_hour, open_minute = map(int, open_time.split(':'))
        close_hour, close_minute = map(int, close_time.split(':'))

        # Create datetime objects in local timezone
        open_local = datetime(
            today_local.year, today_local.month, today_local.day,
            open_hour, open_minute,
            tzinfo=local_tz_obj
        )
        close_local = datetime(
            today_local.year, today_local.month, today_local.day,
            close_hour, close_minute,
            tzinfo=local_tz_obj
        )

        # Convert to UTC
        return open_local.astimezone(timezone.utc), close_local.astimezone(timezone.utc)


# Example usage and tests
if __name__ == "__main__":
    print("=" * 80)
    print("TIMEZONE HANDLER - MULTI-TENANT STANDARDIZATION")
    print("=" * 80)

    # Get current time in UTC
    now = TimezoneHandler.now_utc()
    print(f"\n1. Current UTC time:")
    print(f"   {now}")
    print(f"   {TimezoneHandler.format_iso(now)}")
    print(f"   {TimezoneHandler.to_unix_ms(now)} (Unix ms)")

    # Multi-timezone response (for API)
    print(f"\n2. Multi-timezone API response:")
    response = TimezoneHandler.create_multi_tz_response(now, ["UTC", "WIB", "WITA", "EST"])
    for key, value in response.items():
        print(f"   {key}: {value}")

    # Trading hours conversion
    print(f"\n3. Trading hours (Indonesia IDX):")
    print(f"   Local time (WIB): 09:00 - 16:00")
    open_utc, close_utc = TimezoneHandler.get_trading_hours_utc("09:00", "16:00", "WIB")
    print(f"   UTC time: {open_utc.time()} - {close_utc.time()}")

    # Convert between timezones
    print(f"\n4. Timezone conversions:")
    print(f"   UTC: {now}")
    print(f"   WIB (Indonesia): {TimezoneHandler.to_timezone(now, 'WIB')}")
    print(f"   EST (New York): {TimezoneHandler.to_timezone(now, 'EST')}")
    print(f"   GMT+2 (MT4): {TimezoneHandler.to_timezone(now, 'GMT+2')}")

    print("\n" + "=" * 80)
