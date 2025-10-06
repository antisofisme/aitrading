"""
Market Sessions Collector
Monitors forex market session status (Tokyo, London, New York, Sydney)
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from publishers import ExternalDataPublisher, DataType

logger = logging.getLogger(__name__)


class MarketSessionsCollector:
    """
    Market Sessions Collector

    Tracks which forex market sessions are currently active:
    - Tokyo: 00:00-09:00 UTC
    - London: 08:00-16:30 UTC
    - New York: 13:00-22:00 UTC
    - Sydney: 22:00-07:00 UTC (crosses midnight)
    """

    def __init__(
        self,
        sessions: dict = None,
        publisher: Optional[ExternalDataPublisher] = None
    ):
        """
        Initialize Market Sessions collector

        Args:
            sessions: Custom session definitions (UTC times)
            publisher: Optional NATS+Kafka publisher
        """
        self.publisher = publisher

        # Session definitions (UTC times)
        self.sessions = sessions or {
            'tokyo': {'open': '00:00', 'close': '09:00'},
            'london': {'open': '08:00', 'close': '16:30'},
            'newyork': {'open': '13:00', 'close': '22:00'},
            'sydney': {'open': '22:00', 'close': '07:00'}
        }

        logger.info(f"✅ Market Sessions collector initialized")

    async def collect(self) -> Dict[str, Any]:
        """
        Get current market session status

        Returns: Dictionary with session status
        """
        current_time = datetime.utcnow()

        logger.info(f"📊 Calculating market sessions...")

        sessions_status = []
        active_sessions = []

        for session_name, times in self.sessions.items():
            is_active = self._is_session_active(current_time, times)

            session_data = {
                'name': session_name,
                'is_active': is_active,
                'open_time': times['open'],
                'close_time': times['close'],
                'timezone': 'UTC'
            }

            if is_active:
                active_sessions.append(session_name)

                # Calculate time until close
                close_time = self._parse_time(times['close'])
                time_until_close = self._calculate_time_until(current_time, close_time, times)
                session_data['time_until_close_minutes'] = time_until_close
            else:
                # Calculate time until open
                open_time = self._parse_time(times['open'])
                time_until_open = self._calculate_time_until(current_time, open_time, times)
                session_data['time_until_open_minutes'] = time_until_open

            sessions_status.append(session_data)

        # Detect overlapping sessions
        overlapping_sessions = active_sessions if len(active_sessions) > 1 else []

        # Determine market liquidity based on active sessions
        liquidity = self._calculate_liquidity(active_sessions)

        data = {
            'source': 'market_sessions',
            'collected_at': current_time.isoformat(),
            'current_utc_time': current_time.strftime('%H:%M:%S'),
            'active_sessions_count': len(active_sessions),
            'active_sessions': active_sessions,
            'overlapping_sessions': overlapping_sessions,
            'liquidity_level': liquidity,
            'sessions': sessions_status
        }

        # Publish
        if self.publisher:
            await self.publisher.publish(
                data=data,
                data_type=DataType.MARKET_SESSIONS,
                metadata={
                    'source': 'market_sessions'
                }
            )

        logger.info(f"✅ Market Sessions: {len(active_sessions)} active ({', '.join(active_sessions)}) | Liquidity: {liquidity}")

        return data

    def _is_session_active(self, current_time: datetime, session_times: Dict[str, str]) -> bool:
        """Check if session is currently active"""
        open_time = self._parse_time(session_times['open'])
        close_time = self._parse_time(session_times['close'])

        current_minutes = current_time.hour * 60 + current_time.minute
        open_minutes = open_time.hour * 60 + open_time.minute
        close_minutes = close_time.hour * 60 + close_time.minute

        # Handle overnight sessions (e.g., Sydney)
        if close_minutes < open_minutes:
            # Session crosses midnight
            return current_minutes >= open_minutes or current_minutes < close_minutes
        else:
            # Normal session
            return open_minutes <= current_minutes < close_minutes

    def _parse_time(self, time_str: str) -> time:
        """Parse time string (HH:MM) to time object"""
        hour, minute = map(int, time_str.split(':'))
        return time(hour=hour, minute=minute)

    def _calculate_time_until(self, current_time: datetime, target_time: time, session_times: Dict[str, str]) -> int:
        """Calculate minutes until target time"""
        current_minutes = current_time.hour * 60 + current_time.minute
        target_minutes = target_time.hour * 60 + target_time.minute

        # Handle overnight sessions
        open_time = self._parse_time(session_times['open'])
        close_time = self._parse_time(session_times['close'])

        if close_time < open_time and target_time == close_time:
            # Closing time is next day
            if current_minutes >= open_time.hour * 60 + open_time.minute:
                # Currently in session, close is tomorrow
                return (24 * 60) - current_minutes + target_minutes
            else:
                # Currently before session start
                return target_minutes - current_minutes

        if target_minutes < current_minutes:
            # Target is tomorrow
            return (24 * 60) - current_minutes + target_minutes
        else:
            return target_minutes - current_minutes

    def _calculate_liquidity(self, active_sessions: list) -> str:
        """
        Calculate market liquidity level based on active sessions

        Returns: 'low', 'medium', 'high', 'very_high'
        """
        session_count = len(active_sessions)

        # Very high liquidity during major overlaps
        if 'london' in active_sessions and 'newyork' in active_sessions:
            return 'very_high'  # London-NY overlap (highest volume)

        # High liquidity with 2+ active sessions
        if session_count >= 2:
            return 'high'

        # Medium liquidity with major session
        if 'london' in active_sessions or 'newyork' in active_sessions:
            return 'medium'

        # Low liquidity with minor sessions only
        if session_count == 1:
            return 'low'

        # No active sessions
        return 'very_low'
