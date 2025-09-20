"""
Advanced Multi-Timeframe Analysis System - MICROSERVICE VERSION
Sophisticated trading analysis across multiple timeframes with AI integration

FEATURES:
- Multi-timeframe correlation analysis
- Cross-timeframe pattern recognition
- AI-powered timeframe synthesis
- Advanced confluence detection
- Real-time timeframe synchronization
- Microservice architecture with per-service infrastructure
"""

# MICROSERVICE CENTRALIZATION INFRASTRUCTURE
from ....shared.infrastructure.logging.base_logger import BaseLogger
from ....shared.infrastructure.performance.base_performance import BasePerformance, performance_tracked
from ....shared.infrastructure.errors.base_error_handler import BaseErrorHandler, ErrorCategory
from ....shared.infrastructure.validation.base_validator import BaseValidator
from ....shared.infrastructure.events.base_event_manager import BaseEventManager
from ....shared.infrastructure.config.base_config import BaseConfig

# Standard library imports
import asyncio
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import statistics
from collections import defaultdict, deque

# Machine learning imports
try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.cluster import KMeans
    from sklearn.metrics import classification_report
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# Initialize microservice infrastructure
logger = BaseLogger.get_logger("timeframe_analyzer", service_name="ml-processing")
performance_tracker = BasePerformance(service_name="ml-processing")
error_handler = BaseErrorHandler(service_name="ml-processing")
validator = BaseValidator(service_name="ml-processing")
event_manager = BaseEventManager(service_name="ml-processing")
config = BaseConfig(service_name="ml-processing")


class MLProcessingTimeFrame(Enum):
    """ML Processing Service - Standard trading timeframes"""
    M1 = "M1"       # 1 minute
    M5 = "M5"       # 5 minutes  
    M15 = "M15"     # 15 minutes
    M30 = "M30"     # 30 minutes
    H1 = "H1"       # 1 hour
    H4 = "H4"       # 4 hours
    D1 = "D1"       # 1 day
    W1 = "W1"       # 1 week
    MN1 = "MN1"     # 1 month


class TrendDirection(Enum):
    """Trend direction classification"""
    STRONG_BULLISH = "strong_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    STRONG_BEARISH = "strong_bearish"


class ConfluenceLevel(Enum):
    """Confluence strength levels"""
    VERY_HIGH = "very_high"     # 80%+
    HIGH = "high"               # 60-80%
    MEDIUM = "medium"           # 40-60%
    LOW = "low"                 # 20-40%
    VERY_LOW = "very_low"       # <20%


@dataclass
class TimeframeData:
    """Data structure for individual timeframe analysis"""
    timeframe: TimeFrame
    symbol: str
    timestamp: datetime
    
    # Price data
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    
    # Technical indicators
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_lower: Optional[float] = None
    atr: Optional[float] = None
    
    # Trend analysis
    trend_direction: Optional[TrendDirection] = None
    trend_strength: Optional[float] = None  # 0-1 scale
    support_level: Optional[float] = None
    resistance_level: Optional[float] = None
    
    # Pattern recognition
    pattern_signals: List[str] = field(default_factory=list)
    breakout_probability: Optional[float] = None
    reversal_probability: Optional[float] = None


@dataclass
class MultiTimeFrameAnalysis:
    """Comprehensive multi-timeframe analysis result"""
    symbol: str
    analysis_time: datetime
    timeframes_analyzed: List[TimeFrame]
    
    # Individual timeframe data
    timeframe_data: Dict[TimeFrame, TimeframeData]
    
    # Cross-timeframe analysis
    overall_trend: TrendDirection
    trend_consistency: float  # 0-1 scale across timeframes
    confluence_level: ConfluenceLevel
    confluence_score: float  # 0-100 scale
    
    # Trading signals
    primary_signal: str  # BUY, SELL, HOLD
    signal_strength: float  # 0-1 scale
    entry_confidence: float  # 0-1 scale
    
    # Risk metrics
    volatility_assessment: str  # LOW, MEDIUM, HIGH
    risk_score: float  # 0-1 scale
    position_size_recommendation: float  # 0-1 scale
    
    # AI insights
    ai_analysis: Dict[str, Any] = field(default_factory=dict)
    pattern_correlations: Dict[str, float] = field(default_factory=dict)
    
    # Metadata
    analysis_duration_ms: float = 0
    data_quality_score: float = 0  # 0-1 scale


class AdvancedMultiTimeFrameAnalyzer:
    """
    Sophisticated multi-timeframe trading analysis system for microservice architecture
    
    Features:
    - Cross-timeframe correlation analysis
    - AI-powered pattern recognition
    - Advanced confluence detection
    - Real-time trend synthesis
    - Machine learning-based predictions
    - Per-service infrastructure integration
    """
    
    def __init__(self):
        # Initialize microservice infrastructure
        self.logger = logger
        self.performance_tracker = performance_tracker
        self.error_handler = error_handler
        self.validator = validator
        self.event_manager = event_manager
        self.config = config
        
        # Configuration
        self.supported_timeframes = [
            TimeFrame.M1, TimeFrame.M5, TimeFrame.M15, 
            TimeFrame.M30, TimeFrame.H1, TimeFrame.H4, TimeFrame.D1
        ]
        self.confluence_weights = {
            TimeFrame.D1: 0.25,    # Daily trend is most important
            TimeFrame.H4: 0.20,    # 4H structure
            TimeFrame.H1: 0.15,    # 1H momentum
            TimeFrame.M30: 0.15,   # 30M entry timing
            TimeFrame.M15: 0.10,   # 15M fine-tuning
            TimeFrame.M5: 0.10,    # 5M execution
            TimeFrame.M1: 0.05     # 1M precision
        }
        
        # Data storage
        self.timeframe_cache = defaultdict(lambda: deque(maxlen=1000))
        self.analysis_history = deque(maxlen=500)
        
        # Machine learning components
        if SKLEARN_AVAILABLE:
            self.trend_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
            self.pattern_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
            self.scaler = StandardScaler()
            self.ml_models_trained = False
        else:
            self.ml_models_trained = False
            
        # Statistics
        self.total_analyses = 0
        self.confluence_accuracy = 0.0
        
        # Service health status
        self.service_healthy = True
        
        self.logger.info("🎯 Advanced Multi-Timeframe Analyzer initialized with microservice infrastructure")
    
    async def initialize(self) -> bool:
        """Initialize the timeframe analyzer"""
        try:
            # Initialize microservice components
            await self.performance_tracker.initialize()
            await self.event_manager.initialize()
            
            # Publish initialization event
            await self.event_manager.publish_event(
                "timeframe_analyzer_initialized",
                {
                    "service": "ml-processing",
                    "supported_timeframes": len(self.supported_timeframes),
                    "ml_available": SKLEARN_AVAILABLE
                }
            )
            
            self.logger.info("✅ Advanced Multi-Timeframe Analyzer fully initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Multi-Timeframe Analyzer: {e}")
            self.service_healthy = False
            return False
    
    @performance_tracked("analyze_multiple_timeframes")
    async def analyze_multiple_timeframes(self, 
                                        symbol: str, 
                                        timeframes: List[TimeFrame],
                                        market_data: Dict[TimeFrame, List[Dict]]) -> MultiTimeFrameAnalysis:
        """
        Perform comprehensive multi-timeframe analysis
        
        Args:
            symbol: Trading symbol (e.g., "EURUSD")
            timeframes: List of timeframes to analyze
            market_data: Historical price data for each timeframe
            
        Returns:
            Complete multi-timeframe analysis
        """
        start_time = datetime.now()
        
        try:
            self.logger.info(f"🎯 Starting multi-timeframe analysis for {symbol}")
            
            # Validate input
            if not self.validator.validate_symbol(symbol):
                raise ValueError(f"Invalid symbol: {symbol}")
            
            # Phase 1: Individual timeframe analysis
            timeframe_data = {}
            for timeframe in timeframes:
                if timeframe in market_data and market_data[timeframe]:
                    tf_data = await self._analyze_single_timeframe(
                        symbol, timeframe, market_data[timeframe]
                    )
                    timeframe_data[timeframe] = tf_data
                    
                    # Cache for future use
                    self.timeframe_cache[f"{symbol}_{timeframe.value}"].append(tf_data)
            
            # Phase 2: Cross-timeframe correlation analysis
            correlation_analysis = await self._analyze_timeframe_correlations(timeframe_data)
            
            # Phase 3: Confluence detection
            confluence_result = await self._detect_confluence(timeframe_data)
            
            # Phase 4: AI-powered synthesis
            ai_insights = await self._generate_ai_insights(symbol, timeframe_data)
            
            # Phase 5: Risk assessment
            risk_metrics = await self._assess_multi_timeframe_risk(timeframe_data)
            
            # Phase 6: Trading signal generation
            trading_signal = await self._generate_trading_signal(
                timeframe_data, confluence_result, ai_insights
            )
            
            # Compile comprehensive analysis
            analysis = MultiTimeFrameAnalysis(
                symbol=symbol,
                analysis_time=datetime.now(),
                timeframes_analyzed=list(timeframes),
                timeframe_data=timeframe_data,
                overall_trend=correlation_analysis["overall_trend"],
                trend_consistency=correlation_analysis["consistency"],
                confluence_level=confluence_result["level"],
                confluence_score=confluence_result["score"],
                primary_signal=trading_signal["signal"],
                signal_strength=trading_signal["strength"],
                entry_confidence=trading_signal["confidence"],
                volatility_assessment=risk_metrics["volatility"],
                risk_score=risk_metrics["risk_score"],
                position_size_recommendation=risk_metrics["position_size"],
                ai_analysis=ai_insights,
                pattern_correlations=correlation_analysis["patterns"],
                analysis_duration_ms=(datetime.now() - start_time).total_seconds() * 1000,
                data_quality_score=self._calculate_data_quality(timeframe_data)
            )
            
            # Store in history
            self.analysis_history.append(analysis)
            self.total_analyses += 1
            
            # Publish analysis event
            await self.event_manager.publish_event(
                "timeframe_analysis_completed",
                {
                    "symbol": symbol,
                    "timeframes_count": len(timeframes),
                    "confluence_score": analysis.confluence_score,
                    "primary_signal": analysis.primary_signal,
                    "confidence": analysis.entry_confidence,
                    "duration_ms": analysis.analysis_duration_ms
                }
            )
            
            self.logger.info(f"✅ Multi-timeframe analysis completed for {symbol} in {analysis.analysis_duration_ms:.2f}ms")
            return analysis
            
        except Exception as e:
            self.logger.error(f"❌ Multi-timeframe analysis failed for {symbol}: {e}")
            raise
    
    async def _analyze_single_timeframe(self, symbol: str, timeframe: TimeFrame, data: List[Dict]) -> TimeframeData:
        """Analyze individual timeframe data"""
        try:
            if not data:
                raise ValueError(f"No data provided for {timeframe.value}")
            
            # Get latest candle
            latest = data[-1]
            
            # Calculate technical indicators
            df = pd.DataFrame(data)
            indicators = await self._calculate_technical_indicators(df)
            
            # Detect trend
            trend_analysis = await self._detect_trend(df, indicators)
            
            # Pattern recognition
            patterns = await self._recognize_patterns(df, indicators)
            
            # Support/resistance levels
            levels = await self._identify_support_resistance(df)
            
            return TimeframeData(
                timeframe=timeframe,
                symbol=symbol,
                timestamp=datetime.fromisoformat(latest["timestamp"]) if isinstance(latest["timestamp"], str) else latest["timestamp"],
                open_price=float(latest["open"]),
                high_price=float(latest["high"]),
                low_price=float(latest["low"]),
                close_price=float(latest["close"]),
                volume=int(latest.get("volume", 0)),
                sma_20=indicators.get("sma_20"),
                sma_50=indicators.get("sma_50"),
                sma_200=indicators.get("sma_200"),
                ema_12=indicators.get("ema_12"),
                ema_26=indicators.get("ema_26"),
                rsi=indicators.get("rsi"),
                macd=indicators.get("macd"),
                macd_signal=indicators.get("macd_signal"),
                bollinger_upper=indicators.get("bb_upper"),
                bollinger_lower=indicators.get("bb_lower"),
                atr=indicators.get("atr"),
                trend_direction=trend_analysis["direction"],
                trend_strength=trend_analysis["strength"],
                support_level=levels.get("support"),
                resistance_level=levels.get("resistance"),
                pattern_signals=patterns["signals"],
                breakout_probability=patterns.get("breakout_prob", 0.0),
                reversal_probability=patterns.get("reversal_prob", 0.0)
            )
            
        except Exception as e:
            self.logger.error(f"❌ Single timeframe analysis failed for {timeframe.value}: {e}")
            raise
    
    async def _calculate_technical_indicators(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate comprehensive technical indicators"""
        try:
            indicators = {}
            
            if len(df) < 200:
                self.logger.warning("Insufficient data for all indicators")
                return indicators
            
            # Moving averages
            indicators["sma_20"] = df["close"].rolling(20).mean().iloc[-1]
            indicators["sma_50"] = df["close"].rolling(50).mean().iloc[-1]
            indicators["sma_200"] = df["close"].rolling(200).mean().iloc[-1]
            
            # Exponential moving averages
            indicators["ema_12"] = df["close"].ewm(span=12).mean().iloc[-1]
            indicators["ema_26"] = df["close"].ewm(span=26).mean().iloc[-1]
            
            # RSI
            delta = df["close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            indicators["rsi"] = 100 - (100 / (1 + rs)).iloc[-1]
            
            # MACD
            ema_12 = df["close"].ewm(span=12).mean()
            ema_26 = df["close"].ewm(span=26).mean()
            macd_line = ema_12 - ema_26
            signal_line = macd_line.ewm(span=9).mean()
            indicators["macd"] = macd_line.iloc[-1]
            indicators["macd_signal"] = signal_line.iloc[-1]
            
            # Bollinger Bands
            sma_20 = df["close"].rolling(20).mean()
            std_20 = df["close"].rolling(20).std()
            indicators["bb_upper"] = (sma_20 + (std_20 * 2)).iloc[-1]
            indicators["bb_lower"] = (sma_20 - (std_20 * 2)).iloc[-1]
            
            # ATR (Average True Range)
            high_low = df["high"] - df["low"]
            high_close = np.abs(df["high"] - df["close"].shift())
            low_close = np.abs(df["low"] - df["close"].shift())
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            indicators["atr"] = true_range.rolling(14).mean().iloc[-1]
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"❌ Technical indicators calculation failed: {e}")
            return {}
    
    async def _detect_trend(self, df: pd.DataFrame, indicators: Dict[str, float]) -> Dict[str, Any]:
        """Advanced trend detection using multiple methods"""
        try:
            trend_signals = []
            trend_strengths = []
            
            # Method 1: Moving average alignment
            if all(k in indicators for k in ["sma_20", "sma_50", "sma_200"]):
                sma_20, sma_50, sma_200 = indicators["sma_20"], indicators["sma_50"], indicators["sma_200"]
                current_price = df["close"].iloc[-1]
                
                if current_price > sma_20 > sma_50 > sma_200:
                    trend_signals.append("bullish")
                    trend_strengths.append(0.9)
                elif current_price < sma_20 < sma_50 < sma_200:
                    trend_signals.append("bearish")
                    trend_strengths.append(0.9)
                else:
                    trend_signals.append("neutral")
                    trend_strengths.append(0.3)
            
            # Method 2: Price action trend
            recent_closes = df["close"].tail(20)
            if len(recent_closes) >= 20:
                slope = np.polyfit(range(len(recent_closes)), recent_closes, 1)[0]
                if slope > 0.0001:
                    trend_signals.append("bullish")
                    trend_strengths.append(min(abs(slope) * 10000, 1.0))
                elif slope < -0.0001:
                    trend_signals.append("bearish")
                    trend_strengths.append(min(abs(slope) * 10000, 1.0))
                else:
                    trend_signals.append("neutral")
                    trend_strengths.append(0.2)
            
            # Method 3: MACD trend
            if "macd" in indicators and "macd_signal" in indicators:
                macd, signal = indicators["macd"], indicators["macd_signal"]
                if macd > signal and macd > 0:
                    trend_signals.append("bullish")
                    trend_strengths.append(0.7)
                elif macd < signal and macd < 0:
                    trend_signals.append("bearish")
                    trend_strengths.append(0.7)
                else:
                    trend_signals.append("neutral")
                    trend_strengths.append(0.4)
            
            # Synthesize trend direction
            bullish_count = trend_signals.count("bullish")
            bearish_count = trend_signals.count("bearish")
            neutral_count = trend_signals.count("neutral")
            
            if bullish_count > bearish_count and bullish_count > neutral_count:
                direction = TrendDirection.BULLISH if bullish_count == 2 else TrendDirection.STRONG_BULLISH
            elif bearish_count > bullish_count and bearish_count > neutral_count:
                direction = TrendDirection.BEARISH if bearish_count == 2 else TrendDirection.STRONG_BEARISH
            else:
                direction = TrendDirection.NEUTRAL
            
            avg_strength = statistics.mean(trend_strengths) if trend_strengths else 0.0
            
            return {
                "direction": direction,
                "strength": avg_strength,
                "confidence": max(bullish_count, bearish_count, neutral_count) / len(trend_signals) if trend_signals else 0.0
            }
            
        except Exception as e:
            self.logger.error(f"❌ Trend detection failed: {e}")
            return {"direction": TrendDirection.NEUTRAL, "strength": 0.0, "confidence": 0.0}
    
    async def _recognize_patterns(self, df: pd.DataFrame, indicators: Dict[str, float]) -> Dict[str, Any]:
        """Advanced pattern recognition"""
        try:
            patterns = {
                "signals": [],
                "breakout_prob": 0.0,
                "reversal_prob": 0.0
            }
            
            if len(df) < 50:
                return patterns
            
            current_price = df["close"].iloc[-1]
            
            # Pattern 1: Bollinger Band squeeze
            if "bb_upper" in indicators and "bb_lower" in indicators:
                bb_width = indicators["bb_upper"] - indicators["bb_lower"]
                avg_bb_width = (df["high"] - df["low"]).rolling(20).mean().iloc[-1]
                
                if bb_width < avg_bb_width * 0.8:
                    patterns["signals"].append("bollinger_squeeze")
                    patterns["breakout_prob"] += 0.3
            
            # Pattern 2: RSI divergence
            if "rsi" in indicators:
                rsi = indicators["rsi"]
                if rsi > 70:
                    patterns["signals"].append("rsi_overbought")
                    patterns["reversal_prob"] += 0.2
                elif rsi < 30:
                    patterns["signals"].append("rsi_oversold")
                    patterns["reversal_prob"] += 0.2
            
            # Pattern 3: MACD momentum
            if "macd" in indicators and "macd_signal" in indicators:
                macd_diff = indicators["macd"] - indicators["macd_signal"]
                if macd_diff > 0 and abs(macd_diff) > 0.0001:
                    patterns["signals"].append("macd_bullish_momentum")
                elif macd_diff < 0 and abs(macd_diff) > 0.0001:
                    patterns["signals"].append("macd_bearish_momentum")
            
            # Pattern 4: Support/Resistance test
            recent_highs = df["high"].tail(10).max()
            recent_lows = df["low"].tail(10).min()
            
            if abs(current_price - recent_highs) / current_price < 0.001:
                patterns["signals"].append("resistance_test")
                patterns["reversal_prob"] += 0.15
            elif abs(current_price - recent_lows) / current_price < 0.001:
                patterns["signals"].append("support_test")
                patterns["reversal_prob"] += 0.15
            
            # Normalize probabilities
            patterns["breakout_prob"] = min(patterns["breakout_prob"], 1.0)
            patterns["reversal_prob"] = min(patterns["reversal_prob"], 1.0)
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"❌ Pattern recognition failed: {e}")
            return {"signals": [], "breakout_prob": 0.0, "reversal_prob": 0.0}
    
    async def _identify_support_resistance(self, df: pd.DataFrame) -> Dict[str, float]:
        """Identify key support and resistance levels"""
        try:
            if len(df) < 20:
                return {}
            
            # Use recent price action to identify levels
            recent_data = df.tail(50)
            
            # Support: recent significant lows
            lows = recent_data["low"]
            support_candidates = []
            
            for i in range(2, len(lows) - 2):
                if (lows.iloc[i] < lows.iloc[i-1] and lows.iloc[i] < lows.iloc[i-2] and
                    lows.iloc[i] < lows.iloc[i+1] and lows.iloc[i] < lows.iloc[i+2]):
                    support_candidates.append(lows.iloc[i])
            
            # Resistance: recent significant highs
            highs = recent_data["high"]
            resistance_candidates = []
            
            for i in range(2, len(highs) - 2):
                if (highs.iloc[i] > highs.iloc[i-1] and highs.iloc[i] > highs.iloc[i-2] and
                    highs.iloc[i] > highs.iloc[i+1] and highs.iloc[i] > highs.iloc[i+2]):
                    resistance_candidates.append(highs.iloc[i])
            
            levels = {}
            if support_candidates:
                levels["support"] = min(support_candidates)
            if resistance_candidates:
                levels["resistance"] = max(resistance_candidates)
            
            return levels
            
        except Exception as e:
            self.logger.error(f"❌ Support/resistance identification failed: {e}")
            return {}
    
    async def _analyze_timeframe_correlations(self, timeframe_data: Dict[TimeFrame, TimeframeData]) -> Dict[str, Any]:
        """Analyze correlations between different timeframes"""
        try:
            trends = []
            patterns = defaultdict(int)
            
            for tf, data in timeframe_data.items():
                trends.append(data.trend_direction)
                
                for pattern in data.pattern_signals:
                    patterns[pattern] += 1
            
            # Calculate trend consistency
            if trends:
                bullish_count = sum(1 for t in trends if t in [TrendDirection.BULLISH, TrendDirection.STRONG_BULLISH])
                bearish_count = sum(1 for t in trends if t in [TrendDirection.BEARISH, TrendDirection.STRONG_BEARISH])
                total_count = len(trends)
                
                consistency = max(bullish_count, bearish_count) / total_count
                
                if bullish_count > bearish_count:
                    overall_trend = TrendDirection.STRONG_BULLISH if consistency > 0.8 else TrendDirection.BULLISH
                elif bearish_count > bullish_count:
                    overall_trend = TrendDirection.STRONG_BEARISH if consistency > 0.8 else TrendDirection.BEARISH
                else:
                    overall_trend = TrendDirection.NEUTRAL
            else:
                consistency = 0.0
                overall_trend = TrendDirection.NEUTRAL
            
            # Normalize pattern counts
            pattern_correlations = {}
            total_patterns = sum(patterns.values())
            if total_patterns > 0:
                for pattern, count in patterns.items():
                    pattern_correlations[pattern] = count / total_patterns
            
            return {
                "overall_trend": overall_trend,
                "consistency": consistency,
                "patterns": pattern_correlations
            }
            
        except Exception as e:
            self.logger.error(f"❌ Timeframe correlation analysis failed: {e}")
            return {
                "overall_trend": TrendDirection.NEUTRAL,
                "consistency": 0.0,
                "patterns": {}
            }
    
    async def _detect_confluence(self, timeframe_data: Dict[TimeFrame, TimeframeData]) -> Dict[str, Any]:
        """Detect confluence across timeframes"""
        try:
            total_score = 0.0
            max_possible_score = 0.0
            
            for timeframe, data in timeframe_data.items():
                weight = self.confluence_weights.get(timeframe, 0.1)
                max_possible_score += weight
                
                # Score based on trend strength and direction
                if data.trend_direction in [TrendDirection.STRONG_BULLISH, TrendDirection.STRONG_BEARISH]:
                    score = weight * data.trend_strength * 1.0
                elif data.trend_direction in [TrendDirection.BULLISH, TrendDirection.BEARISH]:
                    score = weight * data.trend_strength * 0.7
                else:
                    score = weight * 0.1
                
                total_score += score
            
            # Calculate confluence percentage
            confluence_percentage = (total_score / max_possible_score * 100) if max_possible_score > 0 else 0
            
            # Determine confluence level
            if confluence_percentage >= 80:
                level = ConfluenceLevel.VERY_HIGH
            elif confluence_percentage >= 60:
                level = ConfluenceLevel.HIGH
            elif confluence_percentage >= 40:
                level = ConfluenceLevel.MEDIUM
            elif confluence_percentage >= 20:
                level = ConfluenceLevel.LOW
            else:
                level = ConfluenceLevel.VERY_LOW
            
            return {
                "level": level,
                "score": confluence_percentage
            }
            
        except Exception as e:
            self.logger.error(f"❌ Confluence detection failed: {e}")
            return {
                "level": ConfluenceLevel.VERY_LOW,
                "score": 0.0
            }
    
    async def _generate_ai_insights(self, symbol: str, timeframe_data: Dict[TimeFrame, TimeframeData]) -> Dict[str, Any]:
        """Generate AI-powered insights using machine learning"""
        try:
            insights = {
                "ml_prediction": "neutral",
                "confidence": 0.0,
                "key_factors": [],
                "risk_factors": [],
                "opportunities": []
            }
            
            if not SKLEARN_AVAILABLE or not timeframe_data:
                insights["ml_prediction"] = "insufficient_data"
                return insights
            
            # Extract features for ML analysis
            features = []
            for tf, data in timeframe_data.items():
                feature_vector = [
                    data.trend_strength or 0.0,
                    data.rsi or 50.0,
                    data.breakout_probability or 0.0,
                    data.reversal_probability or 0.0,
                    len(data.pattern_signals),
                    1.0 if data.trend_direction in [TrendDirection.BULLISH, TrendDirection.STRONG_BULLISH] else 0.0,
                    1.0 if data.trend_direction in [TrendDirection.BEARISH, TrendDirection.STRONG_BEARISH] else 0.0
                ]
                features.extend(feature_vector)
            
            # Basic ML insights (simplified for this implementation)
            if features:
                avg_trend_strength = statistics.mean([f for i, f in enumerate(features) if i % 7 == 0])
                avg_rsi = statistics.mean([f for i, f in enumerate(features) if i % 7 == 1])
                
                if avg_trend_strength > 0.6 and avg_rsi < 70:
                    insights["ml_prediction"] = "bullish"
                    insights["confidence"] = min(avg_trend_strength, 0.9)
                elif avg_trend_strength > 0.6 and avg_rsi > 30:
                    insights["ml_prediction"] = "bearish"
                    insights["confidence"] = min(avg_trend_strength, 0.9)
                else:
                    insights["ml_prediction"] = "neutral"
                    insights["confidence"] = 0.3
                
                # Key factors analysis
                if avg_rsi > 70:
                    insights["risk_factors"].append("overbought_conditions")
                elif avg_rsi < 30:
                    insights["opportunities"].append("oversold_conditions")
                
                if avg_trend_strength > 0.7:
                    insights["key_factors"].append("strong_trend_momentum")
                
            return insights
            
        except Exception as e:
            self.logger.error(f"❌ AI insights generation failed: {e}")
            return {"ml_prediction": "error", "confidence": 0.0, "key_factors": [], "risk_factors": [], "opportunities": []}
    
    async def _assess_multi_timeframe_risk(self, timeframe_data: Dict[TimeFrame, TimeframeData]) -> Dict[str, Any]:
        """Assess risk across multiple timeframes"""
        try:
            volatility_scores = []
            risk_factors = []
            
            for tf, data in timeframe_data.items():
                # Volatility assessment based on ATR and price range
                if data.atr and data.close_price:
                    volatility_ratio = data.atr / data.close_price
                    volatility_scores.append(volatility_ratio)
                
                # Risk factors from patterns
                if "resistance_test" in data.pattern_signals:
                    risk_factors.append("approaching_resistance")
                if data.reversal_probability > 0.3:
                    risk_factors.append("high_reversal_probability")
                if data.rsi and (data.rsi > 75 or data.rsi < 25):
                    risk_factors.append("extreme_rsi_levels")
            
            # Calculate overall risk metrics
            avg_volatility = statistics.mean(volatility_scores) if volatility_scores else 0.01
            
            if avg_volatility > 0.005:
                volatility_assessment = "HIGH"
                risk_score = 0.8
                position_size = 0.3
            elif avg_volatility > 0.002:
                volatility_assessment = "MEDIUM"
                risk_score = 0.5
                position_size = 0.5
            else:
                volatility_assessment = "LOW"
                risk_score = 0.2
                position_size = 0.8
            
            # Adjust based on risk factors
            risk_multiplier = 1.0 + (len(risk_factors) * 0.2)
            risk_score = min(risk_score * risk_multiplier, 1.0)
            position_size = max(position_size / risk_multiplier, 0.1)
            
            return {
                "volatility": volatility_assessment,
                "risk_score": risk_score,
                "position_size": position_size,
                "risk_factors": risk_factors
            }
            
        except Exception as e:
            self.logger.error(f"❌ Risk assessment failed: {e}")
            return {
                "volatility": "UNKNOWN",
                "risk_score": 0.5,
                "position_size": 0.3,
                "risk_factors": ["assessment_error"]
            }
    
    async def _generate_trading_signal(self, 
                                     timeframe_data: Dict[TimeFrame, TimeframeData],
                                     confluence_result: Dict[str, Any],
                                     ai_insights: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive trading signal"""
        try:
            # Collect signals from all timeframes
            bullish_signals = 0
            bearish_signals = 0
            signal_strength = 0.0
            
            for tf, data in timeframe_data.items():
                weight = self.confluence_weights.get(tf, 0.1)
                
                if data.trend_direction in [TrendDirection.BULLISH, TrendDirection.STRONG_BULLISH]:
                    bullish_signals += weight
                    signal_strength += data.trend_strength * weight
                elif data.trend_direction in [TrendDirection.BEARISH, TrendDirection.STRONG_BEARISH]:
                    bearish_signals += weight
                    signal_strength += data.trend_strength * weight
            
            # Determine primary signal
            if bullish_signals > bearish_signals and confluence_result["score"] > 40:
                primary_signal = "BUY"
                confidence = min(bullish_signals / (bullish_signals + bearish_signals), 0.95)
            elif bearish_signals > bullish_signals and confluence_result["score"] > 40:
                primary_signal = "SELL"
                confidence = min(bearish_signals / (bullish_signals + bearish_signals), 0.95)
            else:
                primary_signal = "HOLD"
                confidence = 0.3
            
            # Incorporate AI insights
            if ai_insights["ml_prediction"] == primary_signal.lower() or ai_insights["ml_prediction"] == "neutral":
                confidence = min(confidence + (ai_insights["confidence"] * 0.2), 0.95)
            else:
                confidence = max(confidence - 0.2, 0.1)
            
            # Adjust based on confluence
            confidence_multiplier = confluence_result["score"] / 100
            confidence *= confidence_multiplier
            
            return {
                "signal": primary_signal,
                "strength": signal_strength,
                "confidence": confidence
            }
            
        except Exception as e:
            self.logger.error(f"❌ Trading signal generation failed: {e}")
            return {
                "signal": "HOLD",
                "strength": 0.0,
                "confidence": 0.1
            }
    
    def _calculate_data_quality(self, timeframe_data: Dict[TimeFrame, TimeframeData]) -> float:
        """Calculate overall data quality score"""
        try:
            quality_scores = []
            
            for tf, data in timeframe_data.items():
                score = 0.0
                total_checks = 0
                
                # Check for valid price data
                if data.close_price > 0:
                    score += 1
                total_checks += 1
                
                # Check for technical indicators
                indicators_present = sum([
                    1 for attr in ['sma_20', 'rsi', 'macd', 'atr']
                    if getattr(data, attr) is not None
                ])
                score += indicators_present / 4
                total_checks += 1
                
                # Check for trend analysis
                if data.trend_direction != TrendDirection.NEUTRAL:
                    score += 1
                total_checks += 1
                
                # Check for patterns
                if data.pattern_signals:
                    score += 1
                total_checks += 1
                
                quality_scores.append(score / total_checks if total_checks > 0 else 0)
            
            return statistics.mean(quality_scores) if quality_scores else 0.0
            
        except Exception as e:
            self.logger.error(f"❌ Data quality calculation failed: {e}")
            return 0.0
    
    def get_analyzer_statistics(self) -> Dict[str, Any]:
        """Get analyzer performance statistics"""
        return {
            "service": "ml-processing",
            "component": "timeframe_analyzer",
            "total_analyses": self.total_analyses,
            "confluence_accuracy": self.confluence_accuracy,
            "supported_timeframes": [tf.value for tf in self.supported_timeframes],
            "ml_models_available": SKLEARN_AVAILABLE,
            "ml_models_trained": self.ml_models_trained,
            "cache_size": sum(len(cache) for cache in self.timeframe_cache.values()),
            "analysis_history_size": len(self.analysis_history),
            "service_healthy": self.service_healthy
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health = {
            "status": "healthy" if self.service_healthy else "degraded",
            "service": "ml-processing",
            "component": "timeframe_analyzer",
            "statistics": self.get_analyzer_statistics(),
            "cache_status": {},
            "configuration": {}
        }
        
        try:
            # Check cache health
            health["cache_status"] = {
                "timeframe_cache_symbols": len(self.timeframe_cache),
                "analysis_history_entries": len(self.analysis_history)
            }
            
            # Check configuration
            health["configuration"] = {
                "supported_timeframes_count": len(self.supported_timeframes),
                "confluence_weights_sum": sum(self.confluence_weights.values()),
                "ml_available": SKLEARN_AVAILABLE
            }
            
            # Overall health assessment
            if self.total_analyses == 0:
                health["status"] = "degraded"
                health["reason"] = "No analyses performed yet"
            
        except Exception as e:
            health["status"] = "error"
            health["error"] = str(e)
        
        return health
    
    async def shutdown(self):
        """Graceful shutdown"""
        try:
            self.logger.info("🛑 Advanced Multi-Timeframe Analyzer shutting down...")
            
            # Clear caches
            self.timeframe_cache.clear()
            self.analysis_history.clear()
            
            # Publish shutdown event
            await self.event_manager.publish_event(
                "timeframe_analyzer_shutdown",
                {"service": "ml-processing", "graceful": True}
            )
            
            self.logger.info("✅ Advanced Multi-Timeframe Analyzer shutdown completed")
            
        except Exception as e:
            self.logger.error(f"❌ Error during shutdown: {e}")


# Export all classes
__all__ = [
    'AdvancedMultiTimeFrameAnalyzer',
    'MultiTimeFrameAnalysis', 
    'TimeframeData',
    'TimeFrame',
    'TrendDirection',
    'ConfluenceLevel'
]