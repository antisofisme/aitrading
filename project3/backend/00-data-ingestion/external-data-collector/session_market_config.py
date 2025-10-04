"""
Market Sessions Configuration - Static Trading Session Data
Provides current trading session, volatility windows, and session overlap detection

FEATURES:
- 4 major trading sessions (Sydney, Tokyo, London, New York)
- Session overlap detection for high volatility periods
- Volatility multipliers based on session activity
- Weekend and holiday detection
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class MarketSessionsConfig:
    """
    Static market sessions configuration with session detection
    and volatility analysis capabilities
    """

    def __init__(self):
        # Trading sessions in UTC hours (24-hour format)
        self.sessions = {
            "Sydney": {
                "open": 21,          # 21:00 UTC
                "close": 6,          # 06:00 UTC (next day)
                "timezone": "Australia/Sydney",
                "active_pairs": ["AUDUSD", "NZDUSD", "AUDJPY", "AUDCAD"]
            },
            "Tokyo": {
                "open": 23,          # 23:00 UTC
                "close": 8,          # 08:00 UTC (next day)
                "timezone": "Asia/Tokyo",
                "active_pairs": ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY"]
            },
            "London": {
                "open": 7,           # 07:00 UTC
                "close": 16,         # 16:00 UTC
                "timezone": "Europe/London",
                "active_pairs": ["EURUSD", "GBPUSD", "EURGBP", "EURJPY"]
            },
            "NewYork": {
                "open": 12,          # 12:00 UTC
                "close": 21,         # 21:00 UTC
                "timezone": "America/New_York",
                "active_pairs": ["EURUSD", "GBPUSD", "USDJPY", "USDCAD"]
            }
        }

        # Session overlaps with higher volatility
        self.overlaps = {
            "Sydney_Tokyo": {
                "start": 23,         # 23:00 UTC
                "end": 6,            # 06:00 UTC (next day)
                "volatility_multiplier": 1.2,
                "active_pairs": ["AUDJPY", "NZDJPY"]
            },
            "London_NewYork": {
                "start": 12,         # 12:00 UTC
                "end": 16,           # 16:00 UTC
                "volatility_multiplier": 1.8,
                "active_pairs": ["EURUSD", "GBPUSD", "USDCAD"]
            }
        }

        # Base volatility multipliers per session
        self.volatility_multipliers = {
            "Sydney": 0.7,       # Lower volatility
            "Tokyo": 0.8,        # Medium-low volatility
            "London": 1.3,       # High volatility
            "NewYork": 1.5,      # Highest volatility
            "Weekend": 0.1       # Very low volatility
        }

    def session_market_get_current_session(self, timestamp: Optional[int] = None) -> Dict:
        """
        Get current active trading session(s)

        Args:
            timestamp: Unix timestamp in milliseconds (optional, uses current time)

        Returns:
            Dict with session info, overlaps, and volatility data
        """
        if timestamp:
            current_time = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
        else:
            current_time = datetime.now(timezone.utc)
            timestamp = int(current_time.timestamp() * 1000)

        current_hour = current_time.hour
        current_weekday = current_time.weekday()  # 0=Monday, 6=Sunday

        # Check if weekend (Saturday=5, Sunday=6)
        if current_weekday >= 5:
            return self.session_market_create_session_info(
                active_sessions=[],
                overlaps=[],
                volatility_multiplier=self.volatility_multipliers["Weekend"],
                timestamp=timestamp,
                is_weekend=True
            )

        active_sessions = []
        active_overlaps = []

        # Check each session
        for session_name, config in self.sessions.items():
            if self.session_market_is_session_active(current_hour, config):
                active_sessions.append(session_name)

        # Check overlaps
        for overlap_name, config in self.overlaps.items():
            if self.session_market_is_overlap_active(current_hour, config):
                active_overlaps.append(overlap_name)

        # Calculate volatility multiplier
        volatility_multiplier = self.session_market_calculate_volatility(
            active_sessions, active_overlaps
        )

        return self.session_market_create_session_info(
            active_sessions=active_sessions,
            overlaps=active_overlaps,
            volatility_multiplier=volatility_multiplier,
            timestamp=timestamp,
            is_weekend=False
        )

    def session_market_is_session_active(self, current_hour: int, session_config: Dict) -> bool:
        """Check if a trading session is currently active"""
        open_hour = session_config["open"]
        close_hour = session_config["close"]

        if open_hour < close_hour:
            # Normal session (e.g., London 7-16)
            return open_hour <= current_hour < close_hour
        else:
            # Overnight session (e.g., Sydney 21-06)
            return current_hour >= open_hour or current_hour < close_hour

    def session_market_is_overlap_active(self, current_hour: int, overlap_config: Dict) -> bool:
        """Check if a session overlap period is active"""
        start_hour = overlap_config["start"]
        end_hour = overlap_config["end"]

        if start_hour < end_hour:
            # Normal overlap (e.g., London_NewYork 12-16)
            return start_hour <= current_hour < end_hour
        else:
            # Overnight overlap (e.g., Sydney_Tokyo 23-06)
            return current_hour >= start_hour or current_hour < end_hour

    def session_market_calculate_volatility(
        self,
        active_sessions: List[str],
        active_overlaps: List[str]
    ) -> float:
        """Calculate volatility multiplier based on active sessions and overlaps"""

        if not active_sessions:
            return 0.3  # Very low activity between sessions

        # Get base volatility from most active session
        base_volatility = max([
            self.volatility_multipliers.get(session, 1.0)
            for session in active_sessions
        ])

        # Apply overlap multipliers
        for overlap in active_overlaps:
            overlap_config = self.overlaps.get(overlap, {})
            overlap_multiplier = overlap_config.get("volatility_multiplier", 1.0)
            base_volatility *= overlap_multiplier

        return min(base_volatility, 2.0)  # Cap at 2.0x

    def session_market_create_session_info(
        self,
        active_sessions: List[str],
        overlaps: List[str],
        volatility_multiplier: float,
        timestamp: int,
        is_weekend: bool
    ) -> Dict:
        """Create standardized session information response"""

        # Get most active pairs for current session(s)
        active_pairs = set()
        for session in active_sessions:
            session_pairs = self.sessions.get(session, {}).get("active_pairs", [])
            active_pairs.update(session_pairs)

        # Add overlap-specific pairs
        for overlap in overlaps:
            overlap_pairs = self.overlaps.get(overlap, {}).get("active_pairs", [])
            active_pairs.update(overlap_pairs)

        return {
            "timestamp": timestamp,
            "current_sessions": active_sessions,
            "session_overlaps": overlaps,
            "volatility_multiplier": round(volatility_multiplier, 2),
            "active_pairs": sorted(list(active_pairs)),
            "is_weekend": is_weekend,
            "is_high_volatility": volatility_multiplier >= 1.5,
            "source": "Static_Config",
            "data_type": "market_session"
        }

    def session_market_get_pair_volatility(self, symbol: str, timestamp: Optional[int] = None) -> Dict:
        """
        Get volatility info specific to a currency pair

        Args:
            symbol: Currency pair (e.g., "EURUSD")
            timestamp: Unix timestamp in milliseconds

        Returns:
            Pair-specific volatility information
        """
        session_info = self.session_market_get_current_session(timestamp)

        # Check if pair is active in current session
        is_pair_active = symbol in session_info["active_pairs"]

        # Adjust volatility for pair activity
        base_volatility = session_info["volatility_multiplier"]
        if is_pair_active:
            pair_volatility = base_volatility
        else:
            pair_volatility = base_volatility * 0.5  # Reduce for inactive pairs

        return {
            "symbol": symbol,
            "timestamp": session_info["timestamp"],
            "volatility_multiplier": round(pair_volatility, 2),
            "is_active_pair": is_pair_active,
            "current_sessions": session_info["current_sessions"],
            "source": "Static_Config"
        }

    def session_market_get_next_session_change(self, timestamp: Optional[int] = None) -> Dict:
        """Get information about the next session opening/closing"""
        if timestamp:
            current_time = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
        else:
            current_time = datetime.now(timezone.utc)

        current_hour = current_time.hour

        # Find next session change (simplified - next hour boundary)
        next_changes = []

        for session_name, config in self.sessions.items():
            open_hour = config["open"]
            close_hour = config["close"]

            # Calculate next open
            if current_hour < open_hour:
                next_changes.append({
                    "session": session_name,
                    "event": "open",
                    "hour": open_hour,
                    "hours_until": open_hour - current_hour
                })
            elif current_hour >= open_hour and open_hour > close_hour:
                # Tomorrow's open for overnight sessions
                hours_until = (24 - current_hour) + open_hour
                next_changes.append({
                    "session": session_name,
                    "event": "open",
                    "hour": open_hour,
                    "hours_until": hours_until
                })

            # Calculate next close
            if current_hour < close_hour:
                next_changes.append({
                    "session": session_name,
                    "event": "close",
                    "hour": close_hour,
                    "hours_until": close_hour - current_hour
                })

        # Sort by hours_until and return next event
        next_changes.sort(key=lambda x: x["hours_until"])

        return {
            "timestamp": int(current_time.timestamp() * 1000),
            "next_event": next_changes[0] if next_changes else None,
            "upcoming_changes": next_changes[:3],  # Next 3 changes
            "source": "Static_Config"
        }

    def session_market_get_all_sessions(self) -> Dict:
        """Get complete session configuration"""
        return {
            "sessions": self.sessions,
            "overlaps": self.overlaps,
            "volatility_multipliers": self.volatility_multipliers,
            "source": "Static_Config"
        }


# Usage Example
def main():
    """Example usage of Market Sessions Config"""
    sessions = MarketSessionsConfig()

    # Get current session info
    current_session = sessions.session_market_get_current_session()
    print("Current Session Info:")
    print(f"Active Sessions: {current_session['current_sessions']}")
    print(f"Volatility Multiplier: {current_session['volatility_multiplier']}")
    print(f"Active Pairs: {current_session['active_pairs']}")
    print(f"Is High Volatility: {current_session['is_high_volatility']}")

    # Get pair-specific info
    eurusd_info = sessions.session_market_get_pair_volatility("EURUSD")
    print(f"\nEURUSD Volatility: {eurusd_info['volatility_multiplier']}")
    print(f"Is Active Pair: {eurusd_info['is_active_pair']}")

    # Get next session change
    next_change = sessions.session_market_get_next_session_change()
    if next_change["next_event"]:
        event = next_change["next_event"]
        print(f"\nNext Event: {event['session']} {event['event']} in {event['hours_until']} hours")


if __name__ == "__main__":
    main()