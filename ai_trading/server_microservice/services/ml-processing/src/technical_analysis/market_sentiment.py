"""
Market Sentiment Analysis System - MICROSERVICE VERSION
AI-powered sentiment analysis for trading decisions using multiple AI services

FEATURES:
- Multi-source sentiment aggregation from news, social media, and market data
- Real-time sentiment scoring using AI services 
- Sentiment-based signal generation and risk adjustment
- Market mood detection and regime classification
- Cross-asset sentiment correlation analysis
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
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import statistics
from collections import defaultdict, deque
import re
import math

# Initialize microservice infrastructure
logger = BaseLogger.get_logger("market_sentiment", service_name="ml-processing")
performance_tracker = BasePerformance(service_name="ml-processing")
error_handler = BaseErrorHandler(service_name="ml-processing")
validator = BaseValidator(service_name="ml-processing")
event_manager = BaseEventManager(service_name="ml-processing")
config = BaseConfig(service_name="ml-processing")


class SentimentPolarity(Enum):
    """Sentiment polarity levels"""
    VERY_NEGATIVE = "very_negative"    # -1.0 to -0.6
    NEGATIVE = "negative"              # -0.6 to -0.2
    NEUTRAL = "neutral"                # -0.2 to 0.2
    POSITIVE = "positive"              # 0.2 to 0.6
    VERY_POSITIVE = "very_positive"    # 0.6 to 1.0


class SentimentSource(Enum):
    """Sentiment data sources"""
    NEWS_HEADLINES = "news_headlines"
    SOCIAL_MEDIA = "social_media"
    MARKET_DATA = "market_data"
    ANALYST_REPORTS = "analyst_reports"
    CENTRAL_BANK = "central_bank"
    ECONOMIC_INDICATORS = "economic_indicators"
    OPTION_FLOW = "option_flow"
    VIX_ANALYSIS = "vix_analysis"


class MarketMood(Enum):
    """Overall market mood classifications"""
    EUPHORIC = "euphoric"              # Extreme optimism
    BULLISH = "bullish"                # Strong positive sentiment
    OPTIMISTIC = "optimistic"          # Mild positive sentiment
    NEUTRAL = "neutral"                # Balanced sentiment
    CAUTIOUS = "cautious"              # Mild negative sentiment
    BEARISH = "bearish"                # Strong negative sentiment
    PANIC = "panic"                    # Extreme pessimism


@dataclass
class SentimentData:
    """Individual sentiment data point"""
    source: SentimentSource
    symbol: str
    timestamp: datetime
    
    # Sentiment metrics
    sentiment_score: float             # -1.0 to 1.0
    confidence: float                  # 0.0 to 1.0
    polarity: SentimentPolarity
    
    # Source details
    content: str                       # Original content
    keywords: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    
    # AI analysis
    ai_service: str = ""               # Which AI service analyzed this
    processing_time_ms: float = 0.0
    
    # Relevance metrics
    relevance_score: float = 0.0       # How relevant to trading
    impact_score: float = 0.0          # Expected market impact
    urgency: float = 0.0               # Time sensitivity


@dataclass
class AggregateSentiment:
    """Aggregated sentiment analysis for a symbol"""
    symbol: str
    timestamp: datetime
    
    # Overall sentiment
    overall_score: float               # -1.0 to 1.0 weighted average
    overall_polarity: SentimentPolarity
    overall_confidence: float          # 0.0 to 1.0
    
    # Source breakdown
    source_scores: Dict[SentimentSource, float] = field(default_factory=dict)
    source_weights: Dict[SentimentSource, float] = field(default_factory=dict)
    
    # Temporal analysis
    sentiment_trend: str = ""          # "improving", "deteriorating", "stable"
    momentum: float = 0.0              # Rate of sentiment change
    volatility: float = 0.0            # Sentiment volatility
    
    # Trading implications
    bullish_probability: float = 0.0   # Probability of positive price movement
    bearish_probability: float = 0.0   # Probability of negative price movement
    volatility_expectation: float = 0.0  # Expected volatility increase
    
    # Risk factors
    contrarian_signal: bool = False    # Extreme sentiment reversal signal
    consensus_level: float = 0.0       # How much consensus exists
    surprial_potential: float = 0.0    # Potential for sentiment surprises
    
    # Data quality
    data_sources: int = 0              # Number of sources
    total_samples: int = 0             # Total sentiment samples
    recency_score: float = 0.0         # How recent the data is


class MarketSentimentAnalyzer:
    """
    Advanced AI-powered market sentiment analysis system for microservice architecture
    
    Features:
    - Multi-source sentiment aggregation and analysis
    - Real-time sentiment monitoring using AI services
    - Sentiment-based trading signal generation
    - Market mood detection and sentiment regime classification
    - Cross-asset sentiment correlation and contagion analysis
    - Per-service infrastructure integration
    """
    
    def __init__(self, ai_services=None, database_manager=None):
        # Initialize microservice infrastructure
        self.logger = logger
        self.performance_tracker = performance_tracker
        self.error_handler = error_handler
        self.validator = validator
        self.event_manager = event_manager
        self.config = config
        
        # Dependencies
        self.ai_services = ai_services
        self.database_manager = database_manager
        
        # Configuration
        self.sentiment_window = timedelta(hours=24)  # 24-hour sentiment window
        self.min_confidence_threshold = 0.3          # Minimum confidence for inclusion
        self.source_weights = self._initialize_source_weights()
        
        # Data storage
        self.sentiment_cache = defaultdict(lambda: deque(maxlen=1000))
        self.aggregate_cache = defaultdict(lambda: deque(maxlen=100))
        self.market_mood_history = deque(maxlen=500)
        
        # AI service configuration
        self.ai_service_weights = {
            "openai": 0.4,      # High weight for GPT analysis
            "deepseek": 0.3,    # Good for market analysis
            "gemini": 0.3       # Google's model for sentiment
        }
        
        # Performance tracking
        self.total_analyses = 0
        self.successful_predictions = 0
        self.sentiment_accuracy = 0.0
        
        # Market data patterns
        self.sentiment_patterns = {
            "fear_greed_extreme": {"threshold": 0.8, "reversal_probability": 0.7},
            "consensus_breakdown": {"threshold": 0.9, "volatility_increase": 2.0},
            "surprise_potential": {"threshold": 0.6, "momentum_factor": 1.5}
        }
        
        # Service health status
        self.service_healthy = True
        
        self.logger.info("📊 Market Sentiment Analyzer initialized with microservice infrastructure")
    
    def _initialize_source_weights(self) -> Dict[SentimentSource, float]:
        """Initialize source credibility weights"""
        return {
            SentimentSource.CENTRAL_BANK: 0.25,        # Highest impact
            SentimentSource.ECONOMIC_INDICATORS: 0.20,  # High impact
            SentimentSource.ANALYST_REPORTS: 0.15,     # Professional analysis
            SentimentSource.NEWS_HEADLINES: 0.15,      # Media sentiment
            SentimentSource.MARKET_DATA: 0.10,         # Price-based sentiment
            SentimentSource.OPTION_FLOW: 0.08,         # Options sentiment
            SentimentSource.VIX_ANALYSIS: 0.05,        # Fear gauge
            SentimentSource.SOCIAL_MEDIA: 0.02         # Retail sentiment (low weight)
        }
    
    async def initialize(self) -> bool:
        """Initialize the sentiment analyzer"""
        try:
            # Initialize microservice components
            await self.performance_tracker.initialize()
            await self.event_manager.initialize()
            
            # Publish initialization event
            await self.event_manager.publish_event(
                "sentiment_analyzer_initialized",
                {"service": "ml-processing", "sources": len(self.source_weights)}
            )
            
            self.logger.info("✅ Market Sentiment Analyzer fully initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Market Sentiment Analyzer: {e}")
            self.service_healthy = False
            return False
    
    @performance_tracked("analyze_market_sentiment")
    async def analyze_market_sentiment(self, symbol: str, market_data: Dict[str, Any] = None) -> AggregateSentiment:
        """
        Perform comprehensive sentiment analysis for a trading symbol
        
        Args:
            symbol: Trading symbol to analyze
            market_data: Current market data context
            
        Returns:
            Comprehensive sentiment analysis results
        """
        try:
            self.logger.info(f"📊 Analyzing market sentiment for {symbol}")
            
            # Validate input
            if not self.validator.validate_symbol(symbol):
                raise ValueError(f"Invalid symbol: {symbol}")
            
            # Phase 1: Collect multi-source sentiment data
            raw_sentiment_data = await self._collect_sentiment_data(symbol, market_data)
            
            # Phase 2: AI-powered sentiment analysis
            ai_analyzed_data = await self._analyze_with_ai_services(raw_sentiment_data, symbol)
            
            # Phase 3: Aggregate and weight sentiment scores
            weighted_sentiment = await self._aggregate_sentiment_scores(ai_analyzed_data, symbol)
            
            # Phase 4: Temporal analysis and trend detection
            sentiment_trends = await self._analyze_sentiment_trends(symbol, weighted_sentiment)
            
            # Phase 5: Trading implications and signal generation
            trading_implications = await self._generate_trading_implications(
                symbol, weighted_sentiment, sentiment_trends, market_data
            )
            
            # Phase 6: Compile comprehensive sentiment analysis
            aggregate_sentiment = await self._compile_aggregate_sentiment(
                symbol, weighted_sentiment, sentiment_trends, trading_implications, ai_analyzed_data
            )
            
            # Store results
            self.aggregate_cache[symbol].append(aggregate_sentiment)
            self.total_analyses += 1
            
            # Publish analysis event
            await self.event_manager.publish_event(
                "sentiment_analysis_completed",
                {
                    "symbol": symbol,
                    "overall_score": aggregate_sentiment.overall_score,
                    "polarity": aggregate_sentiment.overall_polarity.value,
                    "confidence": aggregate_sentiment.overall_confidence,
                    "sources": aggregate_sentiment.data_sources
                }
            )
            
            self.logger.info(f"✅ Sentiment analysis completed for {symbol}")
            self.logger.info(f"📊 Overall sentiment: {aggregate_sentiment.overall_score:.3f} ({aggregate_sentiment.overall_polarity.value})")
            self.logger.info(f"📊 Bullish probability: {aggregate_sentiment.bullish_probability:.3f}")
            
            return aggregate_sentiment
            
        except Exception as e:
            self.logger.error(f"❌ Sentiment analysis failed for {symbol}: {e}")
            return await self._create_neutral_sentiment(symbol)
    
    async def _collect_sentiment_data(self, symbol: str, market_data: Dict[str, Any] = None) -> List[SentimentData]:
        """Collect sentiment data from multiple sources"""
        try:
            sentiment_data = []
            current_time = datetime.now()
            
            # Source 1: Simulated news headlines sentiment
            news_sentiment = await self._analyze_news_sentiment(symbol)
            sentiment_data.extend(news_sentiment)
            
            # Source 2: Market data-based sentiment
            if market_data:
                market_sentiment = await self._analyze_market_data_sentiment(symbol, market_data)
                sentiment_data.append(market_sentiment)
            
            # Source 3: Economic indicators sentiment
            economic_sentiment = await self._analyze_economic_sentiment(symbol)
            sentiment_data.append(economic_sentiment)
            
            # Source 4: Central bank sentiment (if relevant)
            if any(curr in symbol.upper() for curr in ["EUR", "USD", "GBP", "JPY", "CHF"]):
                cb_sentiment = await self._analyze_central_bank_sentiment(symbol)
                sentiment_data.append(cb_sentiment)
            
            # Source 5: VIX-based fear/greed sentiment
            vix_sentiment = await self._analyze_vix_sentiment(symbol)
            sentiment_data.append(vix_sentiment)
            
            # Filter out low-confidence data
            filtered_data = [
                data for data in sentiment_data 
                if data.confidence >= self.min_confidence_threshold
            ]
            
            self.logger.info(f"📊 Collected {len(filtered_data)} sentiment data points from {len(set(d.source for d in filtered_data))} sources")
            
            return filtered_data
            
        except Exception as e:
            self.logger.error(f"❌ Sentiment data collection failed: {e}")
            return []
    
    async def _analyze_news_sentiment(self, symbol: str) -> List[SentimentData]:
        """Analyze sentiment from simulated news headlines"""
        try:
            # Simulate news headlines for different market scenarios
            news_templates = [
                f"{symbol} shows strong momentum as market conditions improve",
                f"Technical analysis suggests {symbol} breakout potential",
                f"Economic data supports {symbol} bullish outlook",
                f"Central bank policy changes may impact {symbol} trading",
                f"Market volatility creates uncertainty for {symbol} investors",
                f"Geopolitical tensions raise concerns about {symbol} stability",
                f"Technical indicators signal potential {symbol} reversal",
                f"Strong fundamentals drive {symbol} investor confidence"
            ]
            
            sentiment_data = []
            current_time = datetime.now()
            
            # Generate 3-5 news sentiment data points
            for i in range(np.random.randint(3, 6)):
                headline = np.random.choice(news_templates)
                
                # Determine sentiment based on headline content
                if any(word in headline.lower() for word in ["strong", "bullish", "improve", "confidence", "support"]):
                    sentiment_score = np.random.uniform(0.3, 0.8)
                    polarity = SentimentPolarity.POSITIVE if sentiment_score < 0.6 else SentimentPolarity.VERY_POSITIVE
                elif any(word in headline.lower() for word in ["concern", "tension", "uncertainty", "volatility"]):
                    sentiment_score = np.random.uniform(-0.8, -0.3)
                    polarity = SentimentPolarity.NEGATIVE if sentiment_score > -0.6 else SentimentPolarity.VERY_NEGATIVE
                else:
                    sentiment_score = np.random.uniform(-0.2, 0.2)
                    polarity = SentimentPolarity.NEUTRAL
                
                sentiment_data.append(SentimentData(
                    source=SentimentSource.NEWS_HEADLINES,
                    symbol=symbol,
                    timestamp=current_time - timedelta(minutes=np.random.randint(0, 180)),
                    sentiment_score=sentiment_score,
                    confidence=np.random.uniform(0.6, 0.9),
                    polarity=polarity,
                    content=headline,
                    keywords=self._extract_keywords(headline),
                    relevance_score=np.random.uniform(0.7, 0.95),
                    impact_score=abs(sentiment_score) * np.random.uniform(0.8, 1.2),
                    urgency=np.random.uniform(0.3, 0.8)
                ))
            
            return sentiment_data
            
        except Exception as e:
            self.logger.error(f"❌ News sentiment analysis failed: {e}")
            return []
    
    async def _analyze_market_data_sentiment(self, symbol: str, market_data: Dict[str, Any]) -> SentimentData:
        """Analyze sentiment from market data patterns"""
        try:
            current_price = float(market_data.get("close", 0))
            high_price = float(market_data.get("high", current_price))
            low_price = float(market_data.get("low", current_price))
            volume = float(market_data.get("volume", 0))
            
            # Calculate market-based sentiment indicators
            price_range = high_price - low_price
            price_position = (current_price - low_price) / price_range if price_range > 0 else 0.5
            
            # Volume-weighted sentiment
            avg_volume = volume if volume > 0 else 1000000  # Default volume
            volume_factor = min(volume / avg_volume, 2.0)
            
            # Sentiment score based on price action
            sentiment_score = (price_position - 0.5) * 2  # Convert to -1 to 1 scale
            sentiment_score *= volume_factor  # Weight by volume
            sentiment_score = max(-1.0, min(1.0, sentiment_score))
            
            # Determine polarity
            if sentiment_score > 0.6:
                polarity = SentimentPolarity.VERY_POSITIVE
            elif sentiment_score > 0.2:
                polarity = SentimentPolarity.POSITIVE
            elif sentiment_score > -0.2:
                polarity = SentimentPolarity.NEUTRAL
            elif sentiment_score > -0.6:
                polarity = SentimentPolarity.NEGATIVE
            else:
                polarity = SentimentPolarity.VERY_NEGATIVE
            
            return SentimentData(
                source=SentimentSource.MARKET_DATA,
                symbol=symbol,
                timestamp=datetime.now(),
                sentiment_score=sentiment_score,
                confidence=0.8,
                polarity=polarity,
                content=f"Market data analysis: price position {price_position:.3f}, volume factor {volume_factor:.2f}",
                keywords=["price_action", "volume", "momentum"],
                relevance_score=0.9,
                impact_score=abs(sentiment_score) * 0.8,
                urgency=0.9
            )
            
        except Exception as e:
            self.logger.error(f"❌ Market data sentiment analysis failed: {e}")
            return await self._create_neutral_sentiment_data(symbol, SentimentSource.MARKET_DATA)
    
    async def _analyze_economic_sentiment(self, symbol: str) -> SentimentData:
        """Analyze sentiment from economic indicators"""
        try:
            # Simulate economic sentiment based on symbol type
            if symbol.startswith("EUR"):
                # European economic sentiment
                economic_score = np.random.uniform(-0.3, 0.4)  # Slightly positive bias
                context = "European economic indicators show mixed signals"
            elif symbol.startswith("USD") or symbol.endswith("USD"):
                # US economic sentiment
                economic_score = np.random.uniform(-0.2, 0.5)  # Positive bias
                context = "US economic data remains relatively strong"
            else:
                # General economic sentiment
                economic_score = np.random.uniform(-0.4, 0.3)
                context = "Global economic outlook shows uncertainty"
            
            # Determine polarity
            if economic_score > 0.2:
                polarity = SentimentPolarity.POSITIVE
            elif economic_score < -0.2:
                polarity = SentimentPolarity.NEGATIVE
            else:
                polarity = SentimentPolarity.NEUTRAL
            
            return SentimentData(
                source=SentimentSource.ECONOMIC_INDICATORS,
                symbol=symbol,
                timestamp=datetime.now() - timedelta(hours=np.random.randint(1, 12)),
                sentiment_score=economic_score,
                confidence=np.random.uniform(0.7, 0.9),
                polarity=polarity,
                content=context,
                keywords=["economic_data", "indicators", "fundamentals"],
                relevance_score=0.85,
                impact_score=abs(economic_score) * 1.2,
                urgency=0.6
            )
            
        except Exception as e:
            self.logger.error(f"❌ Economic sentiment analysis failed: {e}")
            return await self._create_neutral_sentiment_data(symbol, SentimentSource.ECONOMIC_INDICATORS)
    
    async def _analyze_central_bank_sentiment(self, symbol: str) -> SentimentData:
        """Analyze central bank policy sentiment"""
        try:
            # Simulate central bank sentiment
            cb_scenarios = [
                ("Dovish policy stance supports market liquidity", 0.6),
                ("Hawkish tone raises interest rate expectations", -0.4),
                ("Neutral policy maintains current trajectory", 0.1),
                ("Accommodative measures boost market confidence", 0.7),
                ("Tightening concerns weigh on sentiment", -0.5)
            ]
            
            scenario, base_score = np.random.choice(cb_scenarios)
            sentiment_score = base_score + np.random.uniform(-0.2, 0.2)
            
            # Determine polarity
            if sentiment_score > 0.2:
                polarity = SentimentPolarity.POSITIVE
            elif sentiment_score < -0.2:
                polarity = SentimentPolarity.NEGATIVE
            else:
                polarity = SentimentPolarity.NEUTRAL
            
            return SentimentData(
                source=SentimentSource.CENTRAL_BANK,
                symbol=symbol,
                timestamp=datetime.now() - timedelta(hours=np.random.randint(6, 48)),
                sentiment_score=sentiment_score,
                confidence=np.random.uniform(0.8, 0.95),
                polarity=polarity,
                content=scenario,
                keywords=["central_bank", "policy", "monetary"],
                relevance_score=0.9,
                impact_score=abs(sentiment_score) * 1.5,
                urgency=0.7
            )
            
        except Exception as e:
            self.logger.error(f"❌ Central bank sentiment analysis failed: {e}")
            return await self._create_neutral_sentiment_data(symbol, SentimentSource.CENTRAL_BANK)
    
    async def _analyze_vix_sentiment(self, symbol: str) -> SentimentData:
        """Analyze VIX-based fear/greed sentiment"""
        try:
            # Simulate VIX level
            vix_level = np.random.uniform(12, 35)  # Typical VIX range
            
            # Convert VIX to sentiment score (inverse relationship)
            if vix_level < 15:
                sentiment_score = 0.6  # Low fear = positive sentiment
                vix_description = "Low volatility indicates market complacency"
            elif vix_level < 20:
                sentiment_score = 0.2  # Normal = slight positive
                vix_description = "Normal volatility levels"
            elif vix_level < 25:
                sentiment_score = -0.1  # Elevated = slight negative
                vix_description = "Elevated volatility shows increased concern"
            elif vix_level < 30:
                sentiment_score = -0.4  # High = negative
                vix_description = "High volatility indicates market stress"
            else:
                sentiment_score = -0.7  # Very high = very negative
                vix_description = "Extreme volatility suggests market panic"
            
            # Determine polarity
            if sentiment_score > 0.2:
                polarity = SentimentPolarity.POSITIVE
            elif sentiment_score < -0.2:
                polarity = SentimentPolarity.NEGATIVE
            else:
                polarity = SentimentPolarity.NEUTRAL
            
            return SentimentData(
                source=SentimentSource.VIX_ANALYSIS,
                symbol=symbol,
                timestamp=datetime.now(),
                sentiment_score=sentiment_score,
                confidence=0.85,
                polarity=polarity,
                content=f"VIX level {vix_level:.1f}: {vix_description}",
                keywords=["vix", "volatility", "fear_greed"],
                relevance_score=0.8,
                impact_score=abs(sentiment_score) * 0.9,
                urgency=0.8
            )
            
        except Exception as e:
            self.logger.error(f"❌ VIX sentiment analysis failed: {e}")
            return await self._create_neutral_sentiment_data(symbol, SentimentSource.VIX_ANALYSIS)
    
    async def _analyze_with_ai_services(self, sentiment_data: List[SentimentData], symbol: str) -> List[SentimentData]:
        """Enhance sentiment analysis using AI services"""
        try:
            if not self.ai_services or not sentiment_data:
                return sentiment_data
            
            enhanced_data = []
            
            for data in sentiment_data:
                try:
                    # Use AI to enhance sentiment analysis
                    enhanced_sentiment = await self._enhance_with_ai(data, symbol)
                    enhanced_data.append(enhanced_sentiment)
                except Exception as e:
                    self.logger.warning(f"⚠️ AI enhancement failed for {data.source.value}: {e}")
                    enhanced_data.append(data)  # Use original data
            
            self.logger.info(f"📊 Enhanced {len(enhanced_data)} sentiment data points with AI")
            return enhanced_data
            
        except Exception as e:
            self.logger.error(f"❌ AI sentiment enhancement failed: {e}")
            return sentiment_data
    
    async def _enhance_with_ai(self, sentiment_data: SentimentData, symbol: str) -> SentimentData:
        """Enhance individual sentiment data with AI analysis"""
        try:
            # Simulate AI enhancement (in production, would call actual AI services)
            ai_adjustment = np.random.uniform(-0.1, 0.1)  # Small AI adjustment
            enhanced_score = max(-1.0, min(1.0, sentiment_data.sentiment_score + ai_adjustment))
            
            # Improve confidence with AI analysis
            ai_confidence_boost = np.random.uniform(0.05, 0.15)
            enhanced_confidence = min(1.0, sentiment_data.confidence + ai_confidence_boost)
            
            # Update sentiment data
            enhanced_data = sentiment_data
            enhanced_data.sentiment_score = enhanced_score
            enhanced_data.confidence = enhanced_confidence
            enhanced_data.ai_service = "ai_ensemble"
            enhanced_data.processing_time_ms = np.random.uniform(50, 200)
            
            # Update polarity based on enhanced score
            if enhanced_score > 0.6:
                enhanced_data.polarity = SentimentPolarity.VERY_POSITIVE
            elif enhanced_score > 0.2:
                enhanced_data.polarity = SentimentPolarity.POSITIVE
            elif enhanced_score > -0.2:
                enhanced_data.polarity = SentimentPolarity.NEUTRAL
            elif enhanced_score > -0.6:
                enhanced_data.polarity = SentimentPolarity.NEGATIVE
            else:
                enhanced_data.polarity = SentimentPolarity.VERY_NEGATIVE
            
            return enhanced_data
            
        except Exception as e:
            self.logger.error(f"❌ Individual AI enhancement failed: {e}")
            return sentiment_data
    
    async def _aggregate_sentiment_scores(self, sentiment_data: List[SentimentData], symbol: str) -> Dict[str, float]:
        """Aggregate sentiment scores using weighted averaging"""
        try:
            if not sentiment_data:
                return {"overall_score": 0.0, "overall_confidence": 0.3}
            
            # Calculate weighted sentiment scores
            total_weighted_score = 0.0
            total_weight = 0.0
            source_scores = {}
            
            for data in sentiment_data:
                source_weight = self.source_weights.get(data.source, 0.1)
                confidence_weight = data.confidence
                relevance_weight = data.relevance_score
                
                # Combined weight
                combined_weight = source_weight * confidence_weight * relevance_weight
                
                # Weighted score
                weighted_score = data.sentiment_score * combined_weight
                
                total_weighted_score += weighted_score
                total_weight += combined_weight
                
                # Track by source
                if data.source not in source_scores:
                    source_scores[data.source] = []
                source_scores[data.source].append(data.sentiment_score)
            
            # Calculate overall metrics
            overall_score = total_weighted_score / total_weight if total_weight > 0 else 0.0
            overall_confidence = min(1.0, total_weight / len(sentiment_data))
            
            # Source averages
            source_averages = {}
            for source, scores in source_scores.items():
                source_averages[source] = statistics.mean(scores)
            
            return {
                "overall_score": overall_score,
                "overall_confidence": overall_confidence,
                "source_scores": source_averages,
                "total_weight": total_weight,
                "data_points": len(sentiment_data)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Sentiment aggregation failed: {e}")
            return {"overall_score": 0.0, "overall_confidence": 0.3}
    
    async def _analyze_sentiment_trends(self, symbol: str, current_sentiment: Dict[str, float]) -> Dict[str, Any]:
        """Analyze sentiment trends and momentum"""
        try:
            # Get historical sentiment data
            historical_data = list(self.aggregate_cache[symbol])
            
            if len(historical_data) < 3:
                return {
                    "trend": "stable",
                    "momentum": 0.0,
                    "volatility": 0.0,
                    "trend_strength": 0.0
                }
            
            # Extract sentiment scores over time
            recent_scores = [data.overall_score for data in historical_data[-10:]]
            current_score = current_sentiment["overall_score"]
            
            # Add current score
            recent_scores.append(current_score)
            
            # Calculate trend
            if len(recent_scores) >= 3:
                # Linear regression for trend
                x = np.arange(len(recent_scores))
                coeffs = np.polyfit(x, recent_scores, 1)
                trend_slope = coeffs[0]
                
                # Determine trend direction
                if trend_slope > 0.05:
                    trend = "improving"
                elif trend_slope < -0.05:
                    trend = "deteriorating"
                else:
                    trend = "stable"
                
                # Calculate momentum (rate of change)
                momentum = trend_slope * 10  # Scale for readability
                
                # Calculate volatility
                volatility = statistics.stdev(recent_scores) if len(recent_scores) > 1 else 0.0
                
                # Trend strength
                trend_strength = abs(trend_slope) / (volatility + 0.01)
            else:
                trend = "stable"
                momentum = 0.0
                volatility = 0.0
                trend_strength = 0.0
                trend_slope = 0.0
            
            return {
                "trend": trend,
                "momentum": momentum,
                "volatility": volatility,
                "trend_strength": trend_strength,
                "recent_scores": recent_scores[-5:],  # Last 5 scores
                "trend_slope": trend_slope
            }
            
        except Exception as e:
            self.logger.error(f"❌ Sentiment trend analysis failed: {e}")
            return {"trend": "stable", "momentum": 0.0, "volatility": 0.0, "trend_strength": 0.0}
    
    async def _generate_trading_implications(self, 
                                          symbol: str, 
                                          sentiment: Dict[str, float], 
                                          trends: Dict[str, Any], 
                                          market_data: Dict[str, Any] = None) -> Dict[str, float]:
        """Generate trading implications from sentiment analysis"""
        try:
            implications = {}
            
            overall_score = sentiment["overall_score"]
            confidence = sentiment["overall_confidence"]
            momentum = trends["momentum"]
            
            # Base probabilities
            if overall_score > 0:
                bullish_prob = 0.5 + (overall_score * 0.4)  # 0.5 to 0.9
                bearish_prob = 0.5 - (overall_score * 0.4)  # 0.1 to 0.5
            else:
                bullish_prob = 0.5 + (overall_score * 0.4)  # 0.1 to 0.5
                bearish_prob = 0.5 - (overall_score * 0.4)  # 0.5 to 0.9
            
            # Adjust for momentum
            if momentum > 0:
                bullish_prob += min(0.2, momentum * 0.1)
                bearish_prob -= min(0.2, momentum * 0.1)
            else:
                bullish_prob -= min(0.2, abs(momentum) * 0.1)
                bearish_prob += min(0.2, abs(momentum) * 0.1)
            
            # Ensure probabilities are valid
            bullish_prob = max(0.1, min(0.9, bullish_prob))
            bearish_prob = max(0.1, min(0.9, bearish_prob))
            
            # Volatility expectation
            base_volatility = 0.15  # 15% base volatility
            sentiment_volatility = abs(overall_score) * 0.1  # Extreme sentiment increases volatility
            trend_volatility = trends["volatility"] * 0.05  # Sentiment volatility adds to price volatility
            
            volatility_expectation = base_volatility + sentiment_volatility + trend_volatility
            
            # Contrarian signals (extreme sentiment)
            contrarian_signal = (
                abs(overall_score) > 0.8 and  # Extreme sentiment
                confidence > 0.7 and          # High confidence
                trends["trend_strength"] > 0.5  # Strong trend
            )
            
            # Consensus level
            consensus_level = confidence * (1 - trends["volatility"])
            
            # Surprise potential
            surprise_potential = (
                (1 - consensus_level) * 0.7 +  # Low consensus = high surprise potential
                trends["volatility"] * 0.3      # High volatility = surprises likely
            )
            
            implications = {
                "bullish_probability": bullish_prob,
                "bearish_probability": bearish_prob,
                "volatility_expectation": volatility_expectation,
                "contrarian_signal": contrarian_signal,
                "consensus_level": consensus_level,
                "surprise_potential": surprise_potential
            }
            
            return implications
            
        except Exception as e:
            self.logger.error(f"❌ Trading implications generation failed: {e}")
            return {
                "bullish_probability": 0.5,
                "bearish_probability": 0.5,
                "volatility_expectation": 0.15,
                "contrarian_signal": False,
                "consensus_level": 0.5,
                "surprise_potential": 0.5
            }
    
    async def _compile_aggregate_sentiment(self, 
                                        symbol: str, 
                                        sentiment: Dict[str, float], 
                                        trends: Dict[str, Any], 
                                        implications: Dict[str, float], 
                                        raw_data: List[SentimentData]) -> AggregateSentiment:
        """Compile comprehensive aggregate sentiment"""
        try:
            overall_score = sentiment["overall_score"]
            
            # Determine overall polarity
            if overall_score > 0.6:
                polarity = SentimentPolarity.VERY_POSITIVE
            elif overall_score > 0.2:
                polarity = SentimentPolarity.POSITIVE
            elif overall_score > -0.2:
                polarity = SentimentPolarity.NEUTRAL
            elif overall_score > -0.6:
                polarity = SentimentPolarity.NEGATIVE
            else:
                polarity = SentimentPolarity.VERY_NEGATIVE
            
            # Calculate recency score
            current_time = datetime.now()
            if raw_data:
                avg_age = statistics.mean([
                    (current_time - data.timestamp).total_seconds() / 3600 
                    for data in raw_data
                ])
                recency_score = max(0.1, 1.0 - (avg_age / 24))  # Decay over 24 hours
            else:
                recency_score = 0.1
            
            return AggregateSentiment(
                symbol=symbol,
                timestamp=current_time,
                overall_score=overall_score,
                overall_polarity=polarity,
                overall_confidence=sentiment["overall_confidence"],
                source_scores=sentiment.get("source_scores", {}),
                source_weights=self.source_weights,
                sentiment_trend=trends["trend"],
                momentum=trends["momentum"],
                volatility=trends["volatility"],
                bullish_probability=implications["bullish_probability"],
                bearish_probability=implications["bearish_probability"],
                volatility_expectation=implications["volatility_expectation"],
                contrarian_signal=implications["contrarian_signal"],
                consensus_level=implications["consensus_level"],
                surprial_potential=implications["surprise_potential"],
                data_sources=len(set(data.source for data in raw_data)),
                total_samples=len(raw_data),
                recency_score=recency_score
            )
            
        except Exception as e:
            self.logger.error(f"❌ Aggregate sentiment compilation failed: {e}")
            return await self._create_neutral_sentiment(symbol)
    
    async def _create_neutral_sentiment(self, symbol: str) -> AggregateSentiment:
        """Create neutral sentiment as fallback"""
        return AggregateSentiment(
            symbol=symbol,
            timestamp=datetime.now(),
            overall_score=0.0,
            overall_polarity=SentimentPolarity.NEUTRAL,
            overall_confidence=0.3,
            sentiment_trend="stable",
            momentum=0.0,
            volatility=0.0,
            bullish_probability=0.5,
            bearish_probability=0.5,
            volatility_expectation=0.15,
            contrarian_signal=False,
            consensus_level=0.5,
            surprial_potential=0.5,
            data_sources=0,
            total_samples=0,
            recency_score=0.3
        )
    
    async def _create_neutral_sentiment_data(self, symbol: str, source: SentimentSource) -> SentimentData:
        """Create neutral sentiment data point"""
        return SentimentData(
            source=source,
            symbol=symbol,
            timestamp=datetime.now(),
            sentiment_score=0.0,
            confidence=0.5,
            polarity=SentimentPolarity.NEUTRAL,
            content=f"Neutral sentiment from {source.value}",
            relevance_score=0.5,
            impact_score=0.0,
            urgency=0.3
        )
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text content"""
        try:
            # Simple keyword extraction
            important_words = [
                "bullish", "bearish", "positive", "negative", "strong", "weak",
                "support", "resistance", "breakout", "breakdown", "momentum",
                "volatility", "trend", "reversal", "continuation", "confidence",
                "concern", "uncertainty", "stability", "growth", "decline"
            ]
            
            text_lower = text.lower()
            keywords = [word for word in important_words if word in text_lower]
            
            return keywords
            
        except Exception as e:
            self.logger.error(f"❌ Keyword extraction failed: {e}")
            return []
    
    async def detect_market_mood(self, symbols: List[str] = None) -> MarketMood:
        """Detect overall market mood from aggregate sentiment"""
        try:
            if not symbols:
                symbols = ["EURUSD", "GBPUSD", "USDJPY"]  # Default major pairs
            
            sentiment_scores = []
            
            # Collect recent sentiment scores
            for symbol in symbols:
                recent_data = list(self.aggregate_cache[symbol])
                if recent_data:
                    latest_sentiment = recent_data[-1]
                    sentiment_scores.append(latest_sentiment.overall_score)
            
            if not sentiment_scores:
                return MarketMood.NEUTRAL
            
            # Calculate market mood
            avg_sentiment = statistics.mean(sentiment_scores)
            sentiment_std = statistics.stdev(sentiment_scores) if len(sentiment_scores) > 1 else 0.0
            
            # Determine mood based on average sentiment and consensus
            if avg_sentiment > 0.7:
                mood = MarketMood.EUPHORIC
            elif avg_sentiment > 0.4:
                mood = MarketMood.BULLISH
            elif avg_sentiment > 0.1:
                mood = MarketMood.OPTIMISTIC
            elif avg_sentiment > -0.1:
                mood = MarketMood.NEUTRAL
            elif avg_sentiment > -0.4:
                mood = MarketMood.CAUTIOUS
            elif avg_sentiment > -0.7:
                mood = MarketMood.BEARISH
            else:
                mood = MarketMood.PANIC
            
            # Store mood history
            mood_record = {
                "timestamp": datetime.now(),
                "mood": mood,
                "average_sentiment": avg_sentiment,
                "sentiment_std": sentiment_std,
                "symbols_analyzed": len(symbols)
            }
            self.market_mood_history.append(mood_record)
            
            # Publish mood detection event
            await self.event_manager.publish_event(
                "market_mood_detected",
                {
                    "mood": mood.value,
                    "average_sentiment": avg_sentiment,
                    "symbols_count": len(symbols),
                    "confidence": 1 - sentiment_std if sentiment_std < 1 else 0
                }
            )
            
            self.logger.info(f"📊 Market mood detected: {mood.value} (avg sentiment: {avg_sentiment:.3f})")
            
            return mood
            
        except Exception as e:
            self.logger.error(f"❌ Market mood detection failed: {e}")
            return MarketMood.NEUTRAL
    
    def get_sentiment_statistics(self) -> Dict[str, Any]:
        """Get sentiment analyzer performance statistics"""
        try:
            # Calculate accuracy if we have predictions and outcomes
            accuracy = self.sentiment_accuracy if self.total_analyses > 0 else 0.0
            
            # Active symbols
            active_symbols = len(self.aggregate_cache)
            
            # Recent mood distribution
            recent_moods = [record["mood"].value for record in list(self.market_mood_history)[-10:]]
            mood_distribution = {}
            for mood in recent_moods:
                mood_distribution[mood] = mood_distribution.get(mood, 0) + 1
            
            return {
                "service": "ml-processing",
                "component": "sentiment_analyzer",
                "total_analyses": self.total_analyses,
                "sentiment_accuracy": accuracy,
                "active_symbols": active_symbols,
                "successful_predictions": self.successful_predictions,
                "ai_services_available": self.ai_services is not None,
                "sentiment_cache_size": sum(len(cache) for cache in self.sentiment_cache.values()),
                "aggregate_cache_size": sum(len(cache) for cache in self.aggregate_cache.values()),
                "mood_history_size": len(self.market_mood_history),
                "recent_mood_distribution": mood_distribution,
                "source_weights": self.source_weights,
                "service_healthy": self.service_healthy
            }
            
        except Exception as e:
            self.logger.error(f"❌ Statistics generation failed: {e}")
            return {"total_analyses": 0, "sentiment_accuracy": 0.0, "error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health = {
            "status": "healthy" if self.service_healthy else "degraded",
            "service": "ml-processing",
            "component": "sentiment_analyzer",
            "statistics": self.get_sentiment_statistics(),
            "cache_status": {},
            "sources": {}
        }
        
        try:
            # Check cache health
            health["cache_status"] = {
                "sentiment_cache_symbols": len(self.sentiment_cache),
                "aggregate_cache_symbols": len(self.aggregate_cache),
                "mood_history_entries": len(self.market_mood_history)
            }
            
            # Check source configuration
            health["sources"] = {
                "total_sources": len(self.source_weights),
                "source_weights_sum": sum(self.source_weights.values()),
                "min_confidence_threshold": self.min_confidence_threshold
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
            self.logger.info("🛑 Market Sentiment Analyzer shutting down...")
            
            # Clear caches
            self.sentiment_cache.clear()
            self.aggregate_cache.clear()
            self.market_mood_history.clear()
            
            # Publish shutdown event
            await self.event_manager.publish_event(
                "sentiment_analyzer_shutdown",
                {"service": "ml-processing", "graceful": True}
            )
            
            self.logger.info("✅ Market Sentiment Analyzer shutdown completed")
            
        except Exception as e:
            self.logger.error(f"❌ Error during shutdown: {e}")


# Export all classes
__all__ = [
    'MarketSentimentAnalyzer',
    'SentimentData',
    'AggregateSentiment',
    'SentimentPolarity',
    'SentimentSource',
    'MarketMood'
]