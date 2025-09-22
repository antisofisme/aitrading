"""
Forex Session Analysis Engine
Advanced session-based analysis for forex trading optimization

Features:
- Real-time session identification (Asian, European, American)
- Session overlap analysis and impact on volatility
- Currency-specific session preferences
- Liquidity and volatility patterns by session
- Major economic event timing analysis
- Session-based trading strategy recommendations
"""

import asyncio
import pytz
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import numpy as np


class TradingSession(Enum):
    """Major forex trading sessions"""
    SYDNEY = "sydney"
    TOKYO = "tokyo"
    LONDON = "london"
    NEW_YORK = "new_york"
    OVERLAP_ASIAN_EUROPEAN = "asian_european_overlap"
    OVERLAP_EUROPEAN_AMERICAN = "european_american_overlap"


class SessionPhase(Enum):
    """Session phases"""
    PRE_MARKET = "pre_market"
    OPENING = "opening"
    ACTIVE = "active"
    LUNCH = "lunch"
    CLOSING = "closing"
    POST_MARKET = "post_market"


@dataclass
class SessionInfo:
    """Trading session information"""
    session: TradingSession
    timezone: str
    start_hour_utc: int
    end_hour_utc: int
    major_currencies: List[str]
    typical_volatility: str  # low, medium, high
    liquidity_level: str  # low, medium, high
    best_pairs: List[str]


@dataclass
class SessionActivity:
    """Current session activity analysis"""
    active_sessions: List[TradingSession]
    primary_session: TradingSession
    session_phase: SessionPhase
    volatility_expectation: float  # 0-1 scale
    liquidity_level: float  # 0-1 scale
    activity_score: float  # Overall activity score
    recommended_pairs: List[str]
    session_overlap: Optional[TradingSession]
    news_impact_window: bool  # True if in major news time window
    timestamp: datetime


@dataclass
class SessionStatistics:
    """Historical session statistics for a currency pair"""
    pair: str
    session: TradingSession
    avg_volatility: float
    avg_spread: float
    avg_volume: float
    win_rate_long: float
    win_rate_short: float
    best_entry_hours: List[int]
    worst_entry_hours: List[int]
    risk_adjusted_return: float


@dataclass
class SessionAnalysis:
    """Comprehensive session analysis result"""
    current_activity: SessionActivity
    pair_analysis: Dict[str, SessionStatistics]
    session_recommendations: Dict[str, str]
    optimal_trading_windows: Dict[str, List[Tuple[int, int]]]  # Hour ranges
    risk_factors: List[str]
    opportunities: List[str]
    analysis_timestamp: datetime


class ForexSessionAnalyzer:
    """
    Advanced forex session analysis engine

    Features:
    - Real-time session tracking across global markets
    - Currency pair optimization by session
    - Volatility and liquidity pattern analysis
    - Economic event timing correlation
    - Session overlap impact analysis
    - Dynamic trading window recommendations
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Initialize session information
        self.sessions = self._initialize_sessions()

        # Session statistics storage
        self.session_stats: Dict[str, Dict[TradingSession, SessionStatistics]] = {}

        # Economic event schedule
        self.economic_events = self._initialize_economic_events()

        # Currency pair preferences by session
        self.session_preferences = self._initialize_session_preferences()

        # Volatility patterns by hour
        self.hourly_volatility_patterns: Dict[str, Dict[int, float]] = {}

        # Analysis cache
        self.analysis_cache = {}
        self.cache_expiry = {}

        self.logger.info("Forex Session Analyzer initialized")

    async def initialize(self) -> bool:
        """Initialize the session analyzer"""
        try:
            # Load historical session statistics
            await self._load_session_statistics()

            # Initialize volatility patterns
            await self._initialize_volatility_patterns()

            self.logger.info("✅ Forex Session Analyzer fully initialized")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Forex Session Analyzer: {e}")
            return False

    async def analyze_session_activity(self, asset: str, timestamp: datetime = None) -> Dict[str, Any]:
        """
        Analyze current session activity for an asset

        Args:
            asset: Currency pair or asset symbol
            timestamp: Analysis timestamp (default: now)

        Returns:
            Dictionary with session activity analysis
        """
        try:
            if timestamp is None:
                timestamp = datetime.now(pytz.UTC)

            self.logger.debug(f"Analyzing session activity for {asset} at {timestamp}")

            # Get current session activity
            current_activity = await self._analyze_current_activity(timestamp)

            # Get pair-specific session statistics
            pair_analysis = await self._analyze_pair_sessions(asset)

            # Generate session recommendations
            session_recommendations = await self._generate_session_recommendations(asset, current_activity)

            # Calculate optimal trading windows
            optimal_windows = await self._calculate_optimal_windows(asset)

            # Identify risk factors and opportunities
            risk_factors = await self._identify_session_risks(asset, current_activity)
            opportunities = await self._identify_session_opportunities(asset, current_activity)

            analysis = SessionAnalysis(
                current_activity=current_activity,
                pair_analysis=pair_analysis,
                session_recommendations=session_recommendations,
                optimal_trading_windows=optimal_windows,
                risk_factors=risk_factors,
                opportunities=opportunities,
                analysis_timestamp=timestamp
            )

            # Convert to dictionary for return
            return {
                'activity_scores': {
                    session.value: self._get_session_activity_score(session, timestamp)
                    for session in TradingSession if not session.value.endswith('_overlap')
                },
                'primary_session': current_activity.primary_session.value,
                'session_phase': current_activity.session_phase.value,
                'volatility_expectation': current_activity.volatility_expectation,
                'liquidity_level': current_activity.liquidity_level,
                'recommended_pairs': current_activity.recommended_pairs,
                'session_overlap': current_activity.session_overlap.value if current_activity.session_overlap else None,
                'news_impact_window': current_activity.news_impact_window,
                'optimal_windows': optimal_windows,
                'session_recommendations': session_recommendations,
                'risk_factors': risk_factors,
                'opportunities': opportunities
            }

        except Exception as e:
            self.logger.error(f"❌ Session activity analysis failed for {asset}: {e}")
            return await self._fallback_session_analysis(asset)

    async def _analyze_current_activity(self, timestamp: datetime) -> SessionActivity:
        """Analyze current session activity"""
        try:
            utc_hour = timestamp.hour

            # Determine active sessions
            active_sessions = []
            session_overlap = None

            for session_name, session_info in self.sessions.items():
                if self._is_session_active(session_info, utc_hour):
                    active_sessions.append(session_name)

            # Check for overlaps
            if TradingSession.LONDON in active_sessions and TradingSession.NEW_YORK in active_sessions:
                session_overlap = TradingSession.OVERLAP_EUROPEAN_AMERICAN
            elif TradingSession.TOKYO in active_sessions and TradingSession.LONDON in active_sessions:
                session_overlap = TradingSession.OVERLAP_ASIAN_EUROPEAN

            # Determine primary session
            primary_session = await self._determine_primary_session(active_sessions, utc_hour)

            # Determine session phase
            session_phase = await self._determine_session_phase(primary_session, utc_hour)

            # Calculate activity metrics
            volatility_expectation = await self._calculate_volatility_expectation(active_sessions, session_overlap)
            liquidity_level = await self._calculate_liquidity_level(active_sessions, session_overlap)
            activity_score = await self._calculate_activity_score(active_sessions, session_overlap, utc_hour)

            # Get recommended pairs for current sessions
            recommended_pairs = await self._get_recommended_pairs(active_sessions)

            # Check if in news impact window
            news_impact_window = await self._is_news_impact_window(utc_hour)

            return SessionActivity(
                active_sessions=active_sessions,
                primary_session=primary_session,
                session_phase=session_phase,
                volatility_expectation=volatility_expectation,
                liquidity_level=liquidity_level,
                activity_score=activity_score,
                recommended_pairs=recommended_pairs,
                session_overlap=session_overlap,
                news_impact_window=news_impact_window,
                timestamp=timestamp
            )

        except Exception as e:
            self.logger.error(f"❌ Current activity analysis failed: {e}")
            return await self._fallback_current_activity(timestamp)

    async def _analyze_pair_sessions(self, pair: str) -> Dict[str, SessionStatistics]:
        """Analyze session statistics for a specific pair"""
        try:
            pair_analysis = {}

            for session in TradingSession:
                if session.value.endswith('_overlap'):
                    continue

                # Get or calculate session statistics
                if pair in self.session_stats and session in self.session_stats[pair]:
                    stats = self.session_stats[pair][session]
                else:
                    stats = await self._calculate_session_statistics(pair, session)

                pair_analysis[session.value] = stats

            return pair_analysis

        except Exception as e:
            self.logger.error(f"❌ Pair session analysis failed for {pair}: {e}")
            return {}

    async def _calculate_session_statistics(self, pair: str, session: TradingSession) -> SessionStatistics:
        """Calculate session statistics for a pair"""
        try:
            # Default statistics (in production, these would be calculated from historical data)
            session_info = self.sessions[session]

            # Estimate statistics based on session characteristics
            if pair in session_info.best_pairs:
                avg_volatility = 0.8 if session_info.typical_volatility == 'high' else 0.6
                avg_volume = 0.9 if session_info.liquidity_level == 'high' else 0.7
                win_rate_long = 0.55
                win_rate_short = 0.55
            else:
                avg_volatility = 0.4 if session_info.typical_volatility == 'high' else 0.3
                avg_volume = 0.5 if session_info.liquidity_level == 'high' else 0.4
                win_rate_long = 0.48
                win_rate_short = 0.48

            # Estimate spread based on liquidity
            avg_spread = 0.8 if session_info.liquidity_level == 'high' else 1.2

            # Best/worst entry hours (simplified)
            session_start = session_info.start_hour_utc
            best_entry_hours = [session_start, (session_start + 1) % 24]
            worst_entry_hours = [(session_start + 6) % 24, (session_start + 7) % 24]

            # Risk-adjusted return
            risk_adjusted_return = avg_volatility * (win_rate_long + win_rate_short) / 2

            return SessionStatistics(
                pair=pair,
                session=session,
                avg_volatility=avg_volatility,
                avg_spread=avg_spread,
                avg_volume=avg_volume,
                win_rate_long=win_rate_long,
                win_rate_short=win_rate_short,
                best_entry_hours=best_entry_hours,
                worst_entry_hours=worst_entry_hours,
                risk_adjusted_return=risk_adjusted_return
            )

        except Exception as e:
            self.logger.error(f"❌ Session statistics calculation failed: {e}")
            return SessionStatistics(
                pair=pair,
                session=session,
                avg_volatility=0.5,
                avg_spread=1.0,
                avg_volume=0.5,
                win_rate_long=0.5,
                win_rate_short=0.5,
                best_entry_hours=[9, 10],
                worst_entry_hours=[21, 22],
                risk_adjusted_return=0.25
            )

    def _is_session_active(self, session_info: SessionInfo, utc_hour: int) -> bool:
        """Check if a session is currently active"""
        start_hour = session_info.start_hour_utc
        end_hour = session_info.end_hour_utc

        if start_hour <= end_hour:
            # Normal session (doesn't cross midnight)
            return start_hour <= utc_hour < end_hour
        else:
            # Session crosses midnight
            return utc_hour >= start_hour or utc_hour < end_hour

    async def _determine_primary_session(self, active_sessions: List[TradingSession], utc_hour: int) -> TradingSession:
        """Determine the primary active session"""
        if not active_sessions:
            # Default to the session that should be most active at this hour
            if 6 <= utc_hour < 15:
                return TradingSession.LONDON
            elif 13 <= utc_hour < 22:
                return TradingSession.NEW_YORK
            elif 22 <= utc_hour or utc_hour < 6:
                return TradingSession.TOKYO
            else:
                return TradingSession.SYDNEY

        # Priority order: overlaps > major sessions > minor sessions
        if TradingSession.LONDON in active_sessions and TradingSession.NEW_YORK in active_sessions:
            return TradingSession.LONDON  # European-American overlap
        elif TradingSession.TOKYO in active_sessions and TradingSession.LONDON in active_sessions:
            return TradingSession.LONDON  # Asian-European overlap
        elif TradingSession.LONDON in active_sessions:
            return TradingSession.LONDON
        elif TradingSession.NEW_YORK in active_sessions:
            return TradingSession.NEW_YORK
        elif TradingSession.TOKYO in active_sessions:
            return TradingSession.TOKYO
        else:
            return active_sessions[0]

    async def _determine_session_phase(self, primary_session: TradingSession, utc_hour: int) -> SessionPhase:
        """Determine the current phase of the primary session"""
        try:
            session_info = self.sessions[primary_session]
            start_hour = session_info.start_hour_utc
            end_hour = session_info.end_hour_utc

            # Calculate hours into session
            if start_hour <= end_hour:
                if utc_hour < start_hour or utc_hour >= end_hour:
                    return SessionPhase.POST_MARKET
                hours_into_session = utc_hour - start_hour
            else:
                if start_hour <= utc_hour:
                    hours_into_session = utc_hour - start_hour
                else:
                    hours_into_session = (24 - start_hour) + utc_hour

            session_length = (end_hour - start_hour) % 24

            # Determine phase based on position in session
            if hours_into_session < 1:
                return SessionPhase.OPENING
            elif hours_into_session < session_length * 0.6:
                return SessionPhase.ACTIVE
            elif hours_into_session < session_length * 0.8:
                return SessionPhase.LUNCH
            else:
                return SessionPhase.CLOSING

        except Exception as e:
            self.logger.error(f"❌ Session phase determination failed: {e}")
            return SessionPhase.ACTIVE

    async def _calculate_volatility_expectation(self, active_sessions: List[TradingSession],
                                              session_overlap: Optional[TradingSession]) -> float:
        """Calculate expected volatility based on active sessions"""
        try:
            base_volatility = 0.3  # Base volatility level

            # Add volatility for each active session
            for session in active_sessions:
                if session in self.sessions:
                    session_info = self.sessions[session]
                    if session_info.typical_volatility == 'high':
                        base_volatility += 0.3
                    elif session_info.typical_volatility == 'medium':
                        base_volatility += 0.2
                    else:
                        base_volatility += 0.1

            # Boost for session overlaps
            if session_overlap:
                base_volatility += 0.4

            return min(base_volatility, 1.0)

        except Exception as e:
            self.logger.error(f"❌ Volatility expectation calculation failed: {e}")
            return 0.5

    async def _calculate_liquidity_level(self, active_sessions: List[TradingSession],
                                       session_overlap: Optional[TradingSession]) -> float:
        """Calculate liquidity level based on active sessions"""
        try:
            base_liquidity = 0.2

            # Add liquidity for each active session
            for session in active_sessions:
                if session in self.sessions:
                    session_info = self.sessions[session]
                    if session_info.liquidity_level == 'high':
                        base_liquidity += 0.4
                    elif session_info.liquidity_level == 'medium':
                        base_liquidity += 0.3
                    else:
                        base_liquidity += 0.2

            # Major boost for overlaps
            if session_overlap:
                base_liquidity += 0.5

            return min(base_liquidity, 1.0)

        except Exception as e:
            self.logger.error(f"❌ Liquidity level calculation failed: {e}")
            return 0.5

    async def _calculate_activity_score(self, active_sessions: List[TradingSession],
                                      session_overlap: Optional[TradingSession], utc_hour: int) -> float:
        """Calculate overall activity score"""
        try:
            # Base score from number of active sessions
            base_score = len(active_sessions) * 0.2

            # Bonus for high-activity sessions
            major_sessions = [TradingSession.LONDON, TradingSession.NEW_YORK]
            major_active = len([s for s in active_sessions if s in major_sessions])
            base_score += major_active * 0.3

            # Overlap bonus
            if session_overlap:
                base_score += 0.4

            # News time bonus
            if await self._is_news_impact_window(utc_hour):
                base_score += 0.2

            return min(base_score, 1.0)

        except Exception as e:
            self.logger.error(f"❌ Activity score calculation failed: {e}")
            return 0.5

    async def _get_recommended_pairs(self, active_sessions: List[TradingSession]) -> List[str]:
        """Get recommended currency pairs for active sessions"""
        try:
            recommended_pairs = set()

            for session in active_sessions:
                if session in self.sessions:
                    session_info = self.sessions[session]
                    recommended_pairs.update(session_info.best_pairs)

            return list(recommended_pairs)[:5]  # Top 5 recommendations

        except Exception as e:
            self.logger.error(f"❌ Recommended pairs calculation failed: {e}")
            return ['EURUSD', 'GBPUSD', 'USDJPY']

    async def _is_news_impact_window(self, utc_hour: int) -> bool:
        """Check if current time is in a major news impact window"""
        # Major news times (UTC)
        news_hours = [8, 9, 10, 12, 13, 14, 15, 16]  # European and US news times
        return utc_hour in news_hours

    def _get_session_activity_score(self, session: TradingSession, timestamp: datetime) -> float:
        """Get activity score for a specific session"""
        try:
            utc_hour = timestamp.hour

            if session not in self.sessions:
                return 0.0

            session_info = self.sessions[session]

            if not self._is_session_active(session_info, utc_hour):
                return 0.0

            # Base activity score
            if session_info.liquidity_level == 'high':
                base_score = 0.8
            elif session_info.liquidity_level == 'medium':
                base_score = 0.6
            else:
                base_score = 0.4

            # Adjust based on session phase
            start_hour = session_info.start_hour_utc
            hours_into_session = (utc_hour - start_hour) % 24

            # Peak activity in first few hours
            if hours_into_session <= 2:
                base_score *= 1.2
            elif hours_into_session >= 6:
                base_score *= 0.8

            return min(base_score, 1.0)

        except Exception as e:
            self.logger.error(f"❌ Session activity score calculation failed: {e}")
            return 0.5

    def _initialize_sessions(self) -> Dict[TradingSession, SessionInfo]:
        """Initialize trading session information"""
        return {
            TradingSession.SYDNEY: SessionInfo(
                session=TradingSession.SYDNEY,
                timezone='Australia/Sydney',
                start_hour_utc=21,
                end_hour_utc=6,
                major_currencies=['AUD', 'NZD', 'JPY'],
                typical_volatility='low',
                liquidity_level='low',
                best_pairs=['AUDUSD', 'NZDUSD', 'AUDJPY']
            ),
            TradingSession.TOKYO: SessionInfo(
                session=TradingSession.TOKYO,
                timezone='Asia/Tokyo',
                start_hour_utc=0,
                end_hour_utc=9,
                major_currencies=['JPY', 'AUD', 'NZD'],
                typical_volatility='medium',
                liquidity_level='medium',
                best_pairs=['USDJPY', 'EURJPY', 'GBPJPY', 'AUDJPY']
            ),
            TradingSession.LONDON: SessionInfo(
                session=TradingSession.LONDON,
                timezone='Europe/London',
                start_hour_utc=7,
                end_hour_utc=16,
                major_currencies=['EUR', 'GBP', 'CHF'],
                typical_volatility='high',
                liquidity_level='high',
                best_pairs=['EURUSD', 'GBPUSD', 'EURGBP', 'USDCHF']
            ),
            TradingSession.NEW_YORK: SessionInfo(
                session=TradingSession.NEW_YORK,
                timezone='America/New_York',
                start_hour_utc=13,
                end_hour_utc=22,
                major_currencies=['USD', 'CAD'],
                typical_volatility='high',
                liquidity_level='high',
                best_pairs=['EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD']
            )
        }

    def _initialize_economic_events(self) -> Dict[int, List[str]]:
        """Initialize major economic event schedule by hour (UTC)"""
        return {
            8: ['German IFO', 'UK Inflation'],
            9: ['UK GDP', 'EU PMI'],
            10: ['ECB Interest Rate Decision'],
            12: ['US ISM Manufacturing'],
            13: ['US GDP', 'US Inflation'],
            14: ['US Retail Sales', 'US Industrial Production'],
            15: ['US Employment Data', 'FOMC Minutes'],
            16: ['US Consumer Confidence'],
            18: ['FOMC Interest Rate Decision']
        }

    def _initialize_session_preferences(self) -> Dict[str, Dict[TradingSession, float]]:
        """Initialize currency pair preferences by session"""
        return {
            'EURUSD': {
                TradingSession.LONDON: 0.9,
                TradingSession.NEW_YORK: 0.8,
                TradingSession.TOKYO: 0.4,
                TradingSession.SYDNEY: 0.3
            },
            'GBPUSD': {
                TradingSession.LONDON: 1.0,
                TradingSession.NEW_YORK: 0.7,
                TradingSession.TOKYO: 0.3,
                TradingSession.SYDNEY: 0.2
            },
            'USDJPY': {
                TradingSession.TOKYO: 0.9,
                TradingSession.NEW_YORK: 0.8,
                TradingSession.LONDON: 0.6,
                TradingSession.SYDNEY: 0.5
            },
            'XAUUSD': {
                TradingSession.LONDON: 0.8,
                TradingSession.NEW_YORK: 0.9,
                TradingSession.TOKYO: 0.6,
                TradingSession.SYDNEY: 0.4
            }
        }

    async def _load_session_statistics(self) -> None:
        """Load historical session statistics"""
        # Placeholder for loading historical data
        # In production, this would load from database
        self.logger.info("Session statistics loading not implemented yet")

    async def _initialize_volatility_patterns(self) -> None:
        """Initialize hourly volatility patterns"""
        # Placeholder for volatility pattern initialization
        # In production, this would be calculated from historical data
        self.logger.info("Volatility patterns initialization not implemented yet")

    async def _generate_session_recommendations(self, asset: str, current_activity: SessionActivity) -> Dict[str, str]:
        """Generate session-based trading recommendations"""
        try:
            recommendations = {}

            # Current session recommendation
            if current_activity.session_overlap:
                recommendations['current_session'] = f"Overlap period - high activity expected ({current_activity.session_overlap.value})"
            else:
                recommendations['current_session'] = f"Active in {current_activity.primary_session.value} session"

            # Asset-specific recommendation
            if asset in self.session_preferences:
                best_sessions = sorted(
                    self.session_preferences[asset].items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                best_session = best_sessions[0][0]
                recommendations['best_session'] = f"Optimal session for {asset}: {best_session.value}"

            # Activity level recommendation
            if current_activity.activity_score > 0.7:
                recommendations['activity_level'] = "High activity - good for trading"
            elif current_activity.activity_score > 0.4:
                recommendations['activity_level'] = "Moderate activity - selective trading"
            else:
                recommendations['activity_level'] = "Low activity - consider waiting"

            return recommendations

        except Exception as e:
            self.logger.error(f"❌ Session recommendations generation failed: {e}")
            return {'current_session': 'Active trading session', 'activity_level': 'Moderate activity'}

    async def _calculate_optimal_windows(self, asset: str) -> Dict[str, List[Tuple[int, int]]]:
        """Calculate optimal trading windows for the asset"""
        try:
            optimal_windows = {}

            for session in TradingSession:
                if session.value.endswith('_overlap'):
                    continue

                session_info = self.sessions[session]
                start_hour = session_info.start_hour_utc

                # Optimal window is typically first 3-4 hours of session
                window_start = start_hour
                window_end = (start_hour + 4) % 24

                optimal_windows[session.value] = [(window_start, window_end)]

            return optimal_windows

        except Exception as e:
            self.logger.error(f"❌ Optimal windows calculation failed: {e}")
            return {}

    async def _identify_session_risks(self, asset: str, current_activity: SessionActivity) -> List[str]:
        """Identify session-based risk factors"""
        risks = []

        try:
            # Low liquidity risk
            if current_activity.liquidity_level < 0.4:
                risks.append("Low liquidity - increased spread risk")

            # News impact risk
            if current_activity.news_impact_window:
                risks.append("Major news window - increased volatility risk")

            # Session transition risk
            utc_hour = current_activity.timestamp.hour
            transition_hours = [6, 7, 15, 16, 21, 22]  # Major session transitions
            if utc_hour in transition_hours:
                risks.append("Session transition - potential gap risk")

            # Weekend approach risk
            weekday = current_activity.timestamp.weekday()
            if weekday == 4 and utc_hour >= 20:  # Friday evening
                risks.append("Weekend approach - reduced liquidity")

        except Exception as e:
            self.logger.error(f"❌ Session risk identification failed: {e}")

        return risks

    async def _identify_session_opportunities(self, asset: str, current_activity: SessionActivity) -> List[str]:
        """Identify session-based opportunities"""
        opportunities = []

        try:
            # High activity opportunity
            if current_activity.activity_score > 0.7:
                opportunities.append("High session activity - good trading conditions")

            # Overlap opportunity
            if current_activity.session_overlap:
                opportunities.append(f"Session overlap active - {current_activity.session_overlap.value}")

            # Volatility opportunity
            if current_activity.volatility_expectation > 0.6:
                opportunities.append("High volatility expected - momentum opportunities")

            # Liquidity opportunity
            if current_activity.liquidity_level > 0.7:
                opportunities.append("High liquidity - tight spreads expected")

        except Exception as e:
            self.logger.error(f"❌ Session opportunity identification failed: {e}")

        return opportunities

    async def _fallback_session_analysis(self, asset: str) -> Dict[str, Any]:
        """Fallback session analysis when main analysis fails"""
        current_time = datetime.now(pytz.UTC)
        utc_hour = current_time.hour

        # Determine basic session
        if 7 <= utc_hour < 16:
            primary_session = 'london'
            activity_score = 0.8
        elif 13 <= utc_hour < 22:
            primary_session = 'new_york'
            activity_score = 0.7
        elif 0 <= utc_hour < 9:
            primary_session = 'tokyo'
            activity_score = 0.6
        else:
            primary_session = 'sydney'
            activity_score = 0.4

        return {
            'activity_scores': {
                'london': 0.8 if primary_session == 'london' else 0.0,
                'new_york': 0.7 if primary_session == 'new_york' else 0.0,
                'tokyo': 0.6 if primary_session == 'tokyo' else 0.0,
                'sydney': 0.4 if primary_session == 'sydney' else 0.0
            },
            'primary_session': primary_session,
            'session_phase': 'active',
            'volatility_expectation': 0.5,
            'liquidity_level': 0.5,
            'recommended_pairs': ['EURUSD', 'GBPUSD', 'USDJPY'],
            'session_overlap': None,
            'news_impact_window': False,
            'optimal_windows': {},
            'session_recommendations': {'current_session': f'Active in {primary_session} session'},
            'risk_factors': [],
            'opportunities': []
        }

    async def _fallback_current_activity(self, timestamp: datetime) -> SessionActivity:
        """Fallback current activity analysis"""
        return SessionActivity(
            active_sessions=[TradingSession.LONDON],
            primary_session=TradingSession.LONDON,
            session_phase=SessionPhase.ACTIVE,
            volatility_expectation=0.5,
            liquidity_level=0.5,
            activity_score=0.5,
            recommended_pairs=['EURUSD', 'GBPUSD'],
            session_overlap=None,
            news_impact_window=False,
            timestamp=timestamp
        )


# Export main components
__all__ = [
    'ForexSessionAnalyzer',
    'TradingSession',
    'SessionPhase',
    'SessionInfo',
    'SessionActivity',
    'SessionStatistics',
    'SessionAnalysis'
]