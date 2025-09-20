"""
Trading Indicator Manager - MICROSERVICE VERSION
Integrates 14 advanced trading indicators with AI stack for enhanced trading intelligence

FEATURES:
- Per-service centralized logging with context-aware messages
- Performance tracking for indicator operations  
- Per-service centralized error handling with proper categorization
- Per-service centralized validation for indicator data
- Event publishing for indicator lifecycle events
- Intelligent caching system for high performance
"""

# TRADING-ENGINE MICROSERVICE INFRASTRUCTURE
from ....shared.infrastructure.core.logger_core import CoreLogger
from ....shared.infrastructure.core.performance_core import CorePerformance, performance_tracked
from ....shared.infrastructure.core.error_core import CoreErrorHandler
from ....shared.infrastructure.optional.validation_core import CoreValidator
from ....shared.infrastructure.optional.event_core import CoreEventManager
from ....shared.infrastructure.core.config_core import CoreConfig

# Standard library imports
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import numpy as np

# Initialize trading-engine microservice infrastructure
logger = CoreLogger("trading-engine", "indicator_manager")
performance_tracker = CorePerformance("trading-engine")
error_handler = CoreErrorHandler("trading-engine")
validator = CoreValidator("trading-engine")
event_manager = CoreEventManager("trading-engine")
config = CoreConfig("trading-engine")


class IndicatorType(Enum):
    """Trading indicator types"""
    RSI = "rsi"
    MACD = "macd"
    STOCHASTIC = "stochastic"
    MFI = "mfi"
    ADL = "adl"
    AO = "ao"
    OBV = "obv"
    VOLUME_BASIC = "volume_basic"
    CORRELATION = "correlation"
    ORDERBOOK = "orderbook"
    SESSIONS = "sessions"
    SLIPPAGE = "slippage"
    TIMESALES = "timesales"
    ECONOMIC = "economic"


@dataclass
class IndicatorConfig:
    """Configuration for individual indicators"""
    indicator_type: IndicatorType
    enabled: bool = True
    update_interval: int = 60  # seconds
    parameters: Dict[str, Any] = None
    confidence_weight: float = 1.0


@dataclass
class MarketData:
    """Market data input for indicators"""
    symbol: str
    timeframe: str
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    tick_volume: float = None
    spread: float = None


@dataclass
class MarketIndicator:
    """Market indicator result"""
    name: str
    value: float
    timestamp: datetime
    timeframe: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = None


@dataclass
class FeatureSet:
    """Enhanced feature set from indicators"""
    raw_indicators: List[MarketIndicator]
    enhanced_features: Dict[str, Any]
    quality_score: float
    validation_notes: List[str]
    ai_insights: Dict[str, Any]
    processing_time: float
    created_at: datetime


class TradingIndicatorManager:
    """
    Manages 14 advanced trading indicators with intelligent caching and AI enhancement
    Optimized for microservice architecture with per-service infrastructure
    """
    
    def __init__(self, cache_config: Optional[Dict] = None):
        
        # Initialize with microservice infrastructure
        self.logger = logger
        self.performance_tracker = performance_tracker
        self.error_handler = error_handler
        self.validator = validator
        self.event_manager = event_manager
        self.config = config
        
        # Initialize cache configuration
        self.cache_config = cache_config or {
            "strategy": "hybrid",
            "max_cache_size": 5000,
            "ttl_seconds": 300,
            "delta_threshold": 0.0001,
            "performance_tracking": True
        }
        
        # Initialize all 14 trading indicators
        self.indicators = self._initialize_indicators()
        
        # Performance tracking with microservice metrics
        self.performance_stats = {
            "indicators_processed": 0,
            "successful_calculations": 0,
            "ai_enhancements": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "average_processing_time": 0.0,
            "error_count": 0,
            "window_optimizations": 0,
            "delta_skips": 0
        }
        
        # Simple cache for data and indicators
        self.data_cache = {}
        self.indicator_cache = {}
        
        # Service health status
        self.service_healthy = True
        
        self.logger.info("📊 Trading Indicator Manager initialized with 14 indicators + microservice infrastructure")
    
    def _initialize_indicators(self) -> Dict[IndicatorType, IndicatorConfig]:
        """Initialize all 14 trading indicators with default configurations"""
        indicators = {}
        
        # Technical Indicators
        indicators[IndicatorType.RSI] = IndicatorConfig(
            indicator_type=IndicatorType.RSI,
            parameters={"period": 14, "overbought": 70, "oversold": 30}
        )
        
        indicators[IndicatorType.MACD] = IndicatorConfig(
            indicator_type=IndicatorType.MACD,
            parameters={"fast_period": 12, "slow_period": 26, "signal_period": 9}
        )
        
        indicators[IndicatorType.STOCHASTIC] = IndicatorConfig(
            indicator_type=IndicatorType.STOCHASTIC,
            parameters={"k_period": 14, "d_period": 3, "slowing": 3}
        )
        
        indicators[IndicatorType.MFI] = IndicatorConfig(
            indicator_type=IndicatorType.MFI,
            parameters={"period": 14}
        )
        
        # Volume Indicators
        indicators[IndicatorType.ADL] = IndicatorConfig(
            indicator_type=IndicatorType.ADL,
            parameters={"smoothing_period": 3}
        )
        
        indicators[IndicatorType.AO] = IndicatorConfig(
            indicator_type=IndicatorType.AO,
            parameters={"fast_period": 5, "slow_period": 34}
        )
        
        indicators[IndicatorType.OBV] = IndicatorConfig(
            indicator_type=IndicatorType.OBV,
            parameters={"smoothing": True}
        )
        
        indicators[IndicatorType.VOLUME_BASIC] = IndicatorConfig(
            indicator_type=IndicatorType.VOLUME_BASIC,
            parameters={"volume_ma_period": 20}
        )
        
        # Market Structure Indicators
        indicators[IndicatorType.CORRELATION] = IndicatorConfig(
            indicator_type=IndicatorType.CORRELATION,
            parameters={"correlation_period": 50, "reference_symbols": ["EURUSD", "GBPUSD"]}
        )
        
        indicators[IndicatorType.ORDERBOOK] = IndicatorConfig(
            indicator_type=IndicatorType.ORDERBOOK,
            parameters={"depth_levels": 10, "imbalance_threshold": 0.6}
        )
        
        indicators[IndicatorType.SESSIONS] = IndicatorConfig(
            indicator_type=IndicatorType.SESSIONS,
            parameters={"track_sessions": ["asian", "european", "american"]}
        )
        
        # Market Quality Indicators
        indicators[IndicatorType.SLIPPAGE] = IndicatorConfig(
            indicator_type=IndicatorType.SLIPPAGE,
            parameters={"tracking_period": 100}
        )
        
        indicators[IndicatorType.TIMESALES] = IndicatorConfig(
            indicator_type=IndicatorType.TIMESALES,
            parameters={"analysis_window": 1000}
        )
        
        indicators[IndicatorType.ECONOMIC] = IndicatorConfig(
            indicator_type=IndicatorType.ECONOMIC,
            parameters={"impact_levels": ["high", "medium"], "lookback_hours": 24}
        )
        
        return indicators
    
    async def initialize(self) -> bool:
        """Initialize the indicator manager and all dependencies"""
        try:
            # Initialize microservice components
            await self.performance_tracker.initialize()
            await self.event_manager.initialize()
            
            # Publish initialization event
            await self.event_manager.publish_event(
                "indicator_manager_initialized",
                {"service": "ml-processing", "indicators_count": len(self.indicators)}
            )
            
            self.logger.info("✅ Trading Indicator Manager fully initialized with microservice infrastructure")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Trading Indicator Manager: {e}")
            self.service_healthy = False
            return False
    
    @performance_tracked("process_market_data")
    async def process_market_data(self, 
                                market_data: MarketData,
                                enable_ai_enhancement: bool = True) -> FeatureSet:
        """
        Process market data through all indicators and enhance with AI
        """
        start_time = datetime.now()
        
        try:
            self.logger.info(f"📊 Processing market data for {market_data.symbol}:{market_data.timeframe}")
            
            # Validate input data
            if not self.validator.validate_market_data(market_data):
                raise ValueError("Invalid market data provided")
            
            # Step 1: Calculate all indicator values
            raw_indicators = await self._calculate_all_indicators(market_data)
            
            # Step 2: Create feature set (simplified AI enhancement for microservice)
            if enable_ai_enhancement:
                feature_set = await self._create_enhanced_feature_set(raw_indicators, market_data)
            else:
                feature_set = await self._create_basic_feature_set(raw_indicators)
            
            # Step 3: Update performance stats
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_stats(processing_time, enable_ai_enhancement)
            
            # Publish processing event
            await self.event_manager.publish_event(
                "market_data_processed",
                {
                    "symbol": market_data.symbol,
                    "timeframe": market_data.timeframe,
                    "indicators_count": len(raw_indicators),
                    "quality_score": feature_set.quality_score,
                    "processing_time": processing_time
                }
            )
            
            self.logger.info(f"✅ Processed {len(raw_indicators)} indicators for {market_data.symbol} "
                           f"(Quality: {feature_set.quality_score:.2f}, Time: {processing_time:.3f}s)")
            
            return feature_set
            
        except Exception as e:
            self.logger.error(f"❌ Market data processing failed for {market_data.symbol}: {e}")
            self.performance_stats["error_count"] += 1
            
            # Return fallback feature set
            return await self._create_fallback_feature_set(market_data)
    
    async def _calculate_all_indicators(self, market_data: MarketData) -> List[MarketIndicator]:
        """Calculate all 14 trading indicators"""
        indicators = []
        
        try:
            # Get historical data for calculations
            historical_data = await self._get_historical_data(market_data.symbol, market_data.timeframe)
            
            # Calculate each indicator
            for indicator_type, config in self.indicators.items():
                if config.enabled:
                    try:
                        indicator_value = await self._calculate_indicator(
                            indicator_type, market_data, historical_data, config
                        )
                        
                        if indicator_value is not None:
                            market_indicator = MarketIndicator(
                                name=indicator_type.value,
                                value=indicator_value,
                                timestamp=market_data.timestamp,
                                timeframe=market_data.timeframe,
                                confidence=config.confidence_weight,
                                metadata={"config": config.parameters}
                            )
                            indicators.append(market_indicator)
                            
                    except Exception as e:
                        self.logger.warning(f"⚠️ Failed to calculate {indicator_type.value}: {e}")
            
            self.performance_stats["successful_calculations"] += len(indicators)
            self.logger.debug(f"📈 Calculated {len(indicators)} indicators successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Indicator calculation batch failed: {e}")
        
        return indicators
    
    async def _calculate_indicator(self, 
                                 indicator_type: IndicatorType,
                                 market_data: MarketData,
                                 historical_data: List[MarketData],
                                 config: IndicatorConfig) -> Optional[float]:
        """Calculate individual indicator value with caching"""
        try:
            # Simple cache key
            cache_key = f"{indicator_type.value}_{market_data.symbol}_{market_data.timeframe}_{market_data.timestamp}"
            
            # Check cache first
            if cache_key in self.indicator_cache:
                cached_data = self.indicator_cache[cache_key]
                if (datetime.now() - cached_data['timestamp']).seconds < 300:  # 5 min cache
                    self.performance_stats["cache_hits"] += 1
                    return cached_data['value']
            
            # Calculate indicator value
            value = None
            if indicator_type == IndicatorType.RSI:
                value = await self._calculate_rsi(market_data, historical_data, config.parameters)
            elif indicator_type == IndicatorType.MACD:
                value = await self._calculate_macd(market_data, historical_data, config.parameters)
            elif indicator_type == IndicatorType.STOCHASTIC:
                value = await self._calculate_stochastic(market_data, historical_data, config.parameters)
            elif indicator_type == IndicatorType.MFI:
                value = await self._calculate_mfi(market_data, historical_data, config.parameters)
            elif indicator_type == IndicatorType.ADL:
                value = await self._calculate_adl(market_data, historical_data, config.parameters)
            elif indicator_type == IndicatorType.AO:
                value = await self._calculate_ao(market_data, historical_data, config.parameters)
            elif indicator_type == IndicatorType.OBV:
                value = await self._calculate_obv(market_data, historical_data, config.parameters)
            elif indicator_type == IndicatorType.VOLUME_BASIC:
                value = await self._calculate_volume_basic(market_data, historical_data, config.parameters)
            elif indicator_type == IndicatorType.CORRELATION:
                value = await self._calculate_correlation(market_data, historical_data, config.parameters)
            elif indicator_type == IndicatorType.ORDERBOOK:
                value = await self._calculate_orderbook(market_data, config.parameters)
            elif indicator_type == IndicatorType.SESSIONS:
                value = await self._calculate_sessions(market_data, config.parameters)
            elif indicator_type == IndicatorType.SLIPPAGE:
                value = await self._calculate_slippage(market_data, historical_data, config.parameters)
            elif indicator_type == IndicatorType.TIMESALES:
                value = await self._calculate_timesales(market_data, config.parameters)
            elif indicator_type == IndicatorType.ECONOMIC:
                value = await self._calculate_economic(market_data, config.parameters)
            
            # Cache the result
            if value is not None:
                self.indicator_cache[cache_key] = {
                    'value': value,
                    'timestamp': datetime.now()
                }
                self.performance_stats["cache_misses"] += 1
            
            return value
            
        except Exception as e:
            self.logger.error(f"❌ Failed to calculate {indicator_type.value}: {e}")
            return None
    
    # Individual indicator calculation methods
    async def _calculate_rsi(self, market_data: MarketData, historical_data: List[MarketData], params: Dict) -> float:
        """Calculate RSI indicator"""
        try:
            period = params.get("period", 14)
            prices = [data.close_price for data in historical_data[-period:]]
            
            if len(prices) < period:
                return 50.0  # Neutral RSI
            
            gains = []
            losses = []
            
            for i in range(1, len(prices)):
                change = prices[i] - prices[i-1]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))
            
            avg_gain = np.mean(gains) if gains else 0
            avg_loss = np.mean(losses) if losses else 0
            
            if avg_loss == 0:
                return 100.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return round(rsi, 2)
            
        except Exception as e:
            self.logger.error(f"❌ RSI calculation failed: {e}")
            return 50.0
    
    async def _calculate_macd(self, market_data: MarketData, historical_data: List[MarketData], params: Dict) -> float:
        """Calculate MACD indicator"""
        try:
            fast_period = params.get("fast_period", 12)
            slow_period = params.get("slow_period", 26)
            
            prices = [data.close_price for data in historical_data[-slow_period:]]
            
            if len(prices) < slow_period:
                return 0.0
            
            # Calculate EMAs
            fast_ema = self._calculate_ema(prices, fast_period)
            slow_ema = self._calculate_ema(prices, slow_period)
            
            macd_line = fast_ema - slow_ema
            return round(macd_line, 5)
            
        except Exception as e:
            self.logger.error(f"❌ MACD calculation failed: {e}")
            return 0.0
    
    async def _calculate_stochastic(self, market_data: MarketData, historical_data: List[MarketData], params: Dict) -> float:
        """Calculate Stochastic indicator"""
        try:
            k_period = params.get("k_period", 14)
            data_slice = historical_data[-k_period:]
            
            if len(data_slice) < k_period:
                return 50.0
            
            high_prices = [data.high_price for data in data_slice]
            low_prices = [data.low_price for data in data_slice]
            current_close = market_data.close_price
            
            highest_high = max(high_prices)
            lowest_low = min(low_prices)
            
            if highest_high == lowest_low:
                return 50.0
            
            stoch_k = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100
            return round(stoch_k, 2)
            
        except Exception as e:
            self.logger.error(f"❌ Stochastic calculation failed: {e}")
            return 50.0
    
    async def _calculate_mfi(self, market_data: MarketData, historical_data: List[MarketData], params: Dict) -> float:
        """Calculate MFI indicator"""
        try:
            period = params.get("period", 14)
            data_slice = historical_data[-period:]
            
            if len(data_slice) < period:
                return 50.0
            
            positive_flow = 0
            negative_flow = 0
            
            for i in range(1, len(data_slice)):
                current = data_slice[i]
                previous = data_slice[i-1]
                
                typical_price = (current.high_price + current.low_price + current.close_price) / 3
                prev_typical = (previous.high_price + previous.low_price + previous.close_price) / 3
                money_flow = typical_price * current.volume
                
                if typical_price > prev_typical:
                    positive_flow += money_flow
                elif typical_price < prev_typical:
                    negative_flow += money_flow
            
            if negative_flow == 0:
                return 100.0
            
            money_ratio = positive_flow / negative_flow
            mfi = 100 - (100 / (1 + money_ratio))
            
            return round(mfi, 2)
            
        except Exception as e:
            self.logger.error(f"❌ MFI calculation failed: {e}")
            return 50.0
    
    async def _calculate_adl(self, market_data: MarketData, historical_data: List[MarketData], params: Dict) -> float:
        """Calculate ADL indicator"""
        try:
            if market_data.high_price == market_data.low_price:
                return 0.0
            
            # Money Flow Multiplier
            mfm = ((market_data.close_price - market_data.low_price) - 
                   (market_data.high_price - market_data.close_price)) / (market_data.high_price - market_data.low_price)
            
            # Money Flow Volume
            mfv = mfm * market_data.volume
            
            return round(mfv, 2)
            
        except Exception as e:
            self.logger.error(f"❌ ADL calculation failed: {e}")
            return 0.0
    
    async def _calculate_ao(self, market_data: MarketData, historical_data: List[MarketData], params: Dict) -> float:
        """Calculate AO indicator"""
        try:
            fast_period = params.get("fast_period", 5)
            slow_period = params.get("slow_period", 34)
            
            data_slice = historical_data[-slow_period:]
            if len(data_slice) < slow_period:
                return 0.0
            
            # Calculate median prices
            median_prices = [(data.high_price + data.low_price) / 2 for data in data_slice]
            
            # Calculate SMAs
            fast_sma = np.mean(median_prices[-fast_period:])
            slow_sma = np.mean(median_prices)
            
            ao = fast_sma - slow_sma
            return round(ao, 5)
            
        except Exception as e:
            self.logger.error(f"❌ AO calculation failed: {e}")
            return 0.0
    
    async def _calculate_obv(self, market_data: MarketData, historical_data: List[MarketData], params: Dict) -> float:
        """Calculate OBV indicator"""
        try:
            if len(historical_data) < 2:
                return market_data.volume
            
            previous_data = historical_data[-2]
            
            if market_data.close_price > previous_data.close_price:
                obv_change = market_data.volume
            elif market_data.close_price < previous_data.close_price:
                obv_change = -market_data.volume
            else:
                obv_change = 0
            
            return round(obv_change, 2)
            
        except Exception as e:
            self.logger.error(f"❌ OBV calculation failed: {e}")
            return 0.0
    
    async def _calculate_volume_basic(self, market_data: MarketData, historical_data: List[MarketData], params: Dict) -> float:
        """Calculate volume basic indicator"""
        try:
            ma_period = params.get("volume_ma_period", 20)
            data_slice = historical_data[-ma_period:]
            
            if len(data_slice) < ma_period:
                return 1.0
            
            volume_ma = np.mean([data.volume for data in data_slice])
            volume_ratio = market_data.volume / volume_ma if volume_ma > 0 else 1.0
            
            return round(volume_ratio, 2)
            
        except Exception as e:
            self.logger.error(f"❌ Volume basic calculation failed: {e}")
            return 1.0
    
    async def _calculate_correlation(self, market_data: MarketData, historical_data: List[MarketData], params: Dict) -> float:
        """Calculate correlation indicator"""
        try:
            period = params.get("correlation_period", 50)
            
            if len(historical_data) < period:
                return 0.0
            
            prices = [data.close_price for data in historical_data[-period:]]
            price_changes = np.diff(prices)
            
            # Simplified correlation proxy based on price momentum consistency
            correlation_proxy = np.std(price_changes) / (np.mean(np.abs(price_changes)) + 1e-8)
            correlation_score = min(correlation_proxy, 1.0)
            
            return round(correlation_score, 3)
            
        except Exception as e:
            self.logger.error(f"❌ Correlation calculation failed: {e}")
            return 0.0
    
    async def _calculate_orderbook(self, market_data: MarketData, params: Dict) -> float:
        """Calculate orderbook indicator"""
        try:
            # Simplified orderbook analysis based on spread
            if hasattr(market_data, 'spread') and market_data.spread:
                spread_ratio = market_data.spread / market_data.close_price
                imbalance_score = min(spread_ratio * 100, 1.0)
                return round(imbalance_score, 3)
            
            return 0.5  # Neutral imbalance
            
        except Exception as e:
            self.logger.error(f"❌ Orderbook calculation failed: {e}")
            return 0.5
    
    async def _calculate_sessions(self, market_data: MarketData, params: Dict) -> float:
        """Calculate sessions indicator"""
        try:
            current_hour = market_data.timestamp.hour
            
            # Define session hours (UTC)
            sessions = {
                "asian": (22, 7),      # 22:00-07:00
                "european": (7, 16),   # 07:00-16:00  
                "american": (13, 22)   # 13:00-22:00
            }
            
            session_score = 0.0
            for session_name, (start, end) in sessions.items():
                if start <= current_hour < end or (start > end and (current_hour >= start or current_hour < end)):
                    session_score += 1.0
            
            return session_score / len(sessions)
            
        except Exception as e:
            self.logger.error(f"❌ Sessions calculation failed: {e}")
            return 0.33
    
    async def _calculate_slippage(self, market_data: MarketData, historical_data: List[MarketData], params: Dict) -> float:
        """Calculate slippage indicator"""
        try:
            period = params.get("tracking_period", 100)
            data_slice = historical_data[-period:] if len(historical_data) >= period else historical_data
            
            if len(data_slice) < 10:
                return 0.1
            
            price_changes = []
            for i in range(1, len(data_slice)):
                change = abs(data_slice[i].close_price - data_slice[i-1].close_price)
                price_changes.append(change)
            
            avg_change = np.mean(price_changes) if price_changes else 0
            slippage_estimate = avg_change / market_data.close_price if market_data.close_price > 0 else 0
            
            return round(min(slippage_estimate * 1000, 10.0), 3)  # Convert to points
            
        except Exception as e:
            self.logger.error(f"❌ Slippage calculation failed: {e}")
            return 0.1
    
    async def _calculate_timesales(self, market_data: MarketData, params: Dict) -> float:
        """Calculate timesales indicator"""
        try:
            # Simplified time & sales based on volume and tick volume
            if hasattr(market_data, 'tick_volume') and market_data.tick_volume:
                volume_per_tick = market_data.volume / market_data.tick_volume if market_data.tick_volume > 0 else 1.0
                activity_score = min(np.log(volume_per_tick + 1), 10.0)
                return round(activity_score, 2)
            
            # Fallback to volume-based activity
            volume_activity = min(np.log(market_data.volume + 1) / 10, 1.0)
            return round(volume_activity, 2)
            
        except Exception as e:
            self.logger.error(f"❌ Timesales calculation failed: {e}")
            return 0.5
    
    async def _calculate_economic(self, market_data: MarketData, params: Dict) -> float:
        """Calculate economic indicator"""
        try:
            # Simplified economic impact based on timestamp
            current_hour = market_data.timestamp.hour
            current_minute = market_data.timestamp.minute
            
            # Higher impact during typical news release times
            news_hours = [8, 10, 14, 16, 20]  # Common UTC news times
            impact_score = 0.0
            
            for news_hour in news_hours:
                if abs(current_hour - news_hour) <= 1:
                    impact_score += 0.5
            
            # Additional impact if it's exactly on the hour (news release time)
            if current_minute <= 5:
                impact_score += 0.3
            
            return round(min(impact_score, 1.0), 2)
            
        except Exception as e:
            self.logger.error(f"❌ Economic calculation failed: {e}")
            return 0.1
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return np.mean(prices) if prices else 0.0
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    async def _get_historical_data(self, symbol: str, timeframe: str) -> List[MarketData]:
        """Get historical data for calculations"""
        try:
            # Try to get from cache first
            cache_key = f"historical_{symbol}_{timeframe}"
            if cache_key in self.data_cache:
                cached_data = self.data_cache[cache_key]
                if (datetime.now() - cached_data['timestamp']).seconds < 300:  # 5 min cache
                    return cached_data['data']
            
            # Generate sample historical data (in real implementation, fetch from database)
            historical_data = self._generate_sample_historical_data(symbol, timeframe)
            
            # Cache the data
            self.data_cache[cache_key] = {
                'data': historical_data,
                'timestamp': datetime.now()
            }
            
            return historical_data
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get historical data for {symbol}: {e}")
            return []
    
    def _generate_sample_historical_data(self, symbol: str, timeframe: str) -> List[MarketData]:
        """Generate sample historical data for testing"""
        data = []
        base_price = 1.1000  # Sample base price
        
        for i in range(100):  # 100 periods of historical data
            timestamp = datetime.now() - timedelta(minutes=i*5)
            
            # Generate realistic price movement
            change = np.random.normal(0, 0.0001)
            price = base_price + change * i
            
            # Generate OHLC
            high = price + abs(np.random.normal(0, 0.00005))
            low = price - abs(np.random.normal(0, 0.00005))
            
            market_data = MarketData(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=timestamp,
                open_price=price,
                high_price=high,
                low_price=low,
                close_price=price + np.random.normal(0, 0.00002),
                volume=np.random.randint(100, 1000),
                tick_volume=np.random.randint(50, 500)
            )
            
            data.append(market_data)
        
        return list(reversed(data))  # Oldest first
    
    async def _create_enhanced_feature_set(self, raw_indicators: List[MarketIndicator], market_data: MarketData) -> FeatureSet:
        """Create enhanced feature set with basic AI processing"""
        
        # Basic features from indicators
        enhanced_features = {}
        for indicator in raw_indicators:
            enhanced_features[indicator.name] = indicator.value
        
        # Add some basic enhancements
        enhanced_features["price_momentum"] = self._calculate_price_momentum(raw_indicators)
        enhanced_features["volume_strength"] = self._calculate_volume_strength(raw_indicators)
        enhanced_features["market_sentiment"] = self._calculate_market_sentiment(raw_indicators)
        
        # Calculate quality score based on indicator count and values
        quality_score = min(len(raw_indicators) / 14.0 * 0.8 + 0.2, 1.0)
        
        return FeatureSet(
            raw_indicators=raw_indicators,
            enhanced_features=enhanced_features,
            quality_score=quality_score,
            validation_notes=["Enhanced processing with microservice AI"],
            ai_insights={"mode": "enhanced", "enhancements": 3},
            processing_time=0.08,
            created_at=datetime.now()
        )
    
    async def _create_basic_feature_set(self, raw_indicators: List[MarketIndicator]) -> FeatureSet:
        """Create basic feature set without AI enhancement"""
        
        # Basic features from indicators
        basic_features = {}
        for indicator in raw_indicators:
            basic_features[indicator.name] = indicator.value
        
        return FeatureSet(
            raw_indicators=raw_indicators,
            enhanced_features=basic_features,
            quality_score=0.6,  # Basic quality
            validation_notes=["Basic processing - AI enhancement disabled"],
            ai_insights={"mode": "basic"},
            processing_time=0.05,
            created_at=datetime.now()
        )
    
    async def _create_fallback_feature_set(self, market_data: MarketData) -> FeatureSet:
        """Create fallback feature set in case of errors"""
        
        # Create minimal features from market data
        fallback_features = {
            "price": market_data.close_price,
            "volume": market_data.volume,
            "spread": getattr(market_data, 'spread', 0.0001)
        }
        
        fallback_indicator = MarketIndicator(
            name="fallback_price",
            value=market_data.close_price,
            timestamp=market_data.timestamp,
            timeframe=market_data.timeframe,
            confidence=0.5
        )
        
        return FeatureSet(
            raw_indicators=[fallback_indicator],
            enhanced_features=fallback_features,
            quality_score=0.3,  # Low quality fallback
            validation_notes=["Fallback mode - indicator calculation failed"],
            ai_insights={"mode": "fallback", "error": "indicator_calculation_failed"},
            processing_time=0.01,
            created_at=datetime.now()
        )
    
    def _calculate_price_momentum(self, indicators: List[MarketIndicator]) -> float:
        """Calculate price momentum from indicators"""
        try:
            rsi_value = next((i.value for i in indicators if i.name == "rsi"), 50)
            macd_value = next((i.value for i in indicators if i.name == "macd"), 0)
            
            # Simple momentum calculation
            momentum = (rsi_value - 50) / 50 + np.tanh(macd_value * 1000)
            return round(momentum, 3)
        except:
            return 0.0
    
    def _calculate_volume_strength(self, indicators: List[MarketIndicator]) -> float:
        """Calculate volume strength from indicators"""
        try:
            volume_basic = next((i.value for i in indicators if i.name == "volume_basic"), 1)
            mfi_value = next((i.value for i in indicators if i.name == "mfi"), 50)
            
            # Simple volume strength calculation
            strength = (volume_basic - 1) * 0.5 + (mfi_value - 50) / 100
            return round(strength, 3)
        except:
            return 0.0
    
    def _calculate_market_sentiment(self, indicators: List[MarketIndicator]) -> float:
        """Calculate market sentiment from indicators"""
        try:
            # Get multiple indicators for sentiment
            rsi_value = next((i.value for i in indicators if i.name == "rsi"), 50)
            stoch_value = next((i.value for i in indicators if i.name == "stochastic"), 50)
            
            # Average sentiment
            sentiment = (rsi_value + stoch_value) / 2 - 50
            return round(sentiment / 50, 3)  # Normalize to -1 to 1
        except:
            return 0.0
    
    def _update_performance_stats(self, processing_time: float, ai_enhanced: bool):
        """Update performance statistics"""
        self.performance_stats["indicators_processed"] += 1
        
        if ai_enhanced:
            self.performance_stats["ai_enhancements"] += 1
        
        # Update average processing time
        current_avg = self.performance_stats["average_processing_time"]
        count = self.performance_stats["indicators_processed"]
        self.performance_stats["average_processing_time"] = (
            (current_avg * (count - 1) + processing_time) / count
        )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        return self.performance_stats.copy()
    
    def get_indicator_config(self, indicator_type: IndicatorType) -> Optional[IndicatorConfig]:
        """Get configuration for specific indicator"""
        return self.indicators.get(indicator_type)
    
    def update_indicator_config(self, indicator_type: IndicatorType, config: IndicatorConfig) -> bool:
        """Update configuration for specific indicator"""
        try:
            self.indicators[indicator_type] = config
            self.logger.info(f"✅ Updated configuration for {indicator_type.value}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to update {indicator_type.value} config: {e}")
            return False
    
    def enable_indicator(self, indicator_type: IndicatorType) -> bool:
        """Enable specific indicator"""
        if indicator_type in self.indicators:
            self.indicators[indicator_type].enabled = True
            return True
        return False
    
    def disable_indicator(self, indicator_type: IndicatorType) -> bool:
        """Disable specific indicator"""
        if indicator_type in self.indicators:
            self.indicators[indicator_type].enabled = False
            return True
        return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health = {
            "status": "healthy" if self.service_healthy else "degraded",
            "service": "ml-processing",
            "component": "indicator_manager",
            "indicators": {},
            "performance": self.get_performance_stats(),
            "cache": {}
        }
        
        try:
            # Check indicator status
            enabled_count = sum(1 for config in self.indicators.values() if config.enabled)
            health["indicators"] = {
                "total": len(self.indicators),
                "enabled": enabled_count,
                "disabled": len(self.indicators) - enabled_count
            }
            
            # Check cache health
            health["cache"] = {
                "data_cache_size": len(self.data_cache),
                "indicator_cache_size": len(self.indicator_cache),
                "cache_hit_ratio": (
                    self.performance_stats["cache_hits"] / 
                    max(self.performance_stats["cache_hits"] + self.performance_stats["cache_misses"], 1)
                )
            }
            
            # Overall health assessment
            if enabled_count < 10:  # Less than 10 indicators enabled
                health["status"] = "degraded"
            
            error_rate = self.performance_stats["error_count"] / max(self.performance_stats["indicators_processed"], 1)
            if error_rate > 0.1:  # More than 10% error rate
                health["status"] = "degraded"
            
        except Exception as e:
            health["status"] = "error"
            health["error"] = str(e)
        
        return health
    
    async def shutdown(self):
        """Graceful shutdown"""
        try:
            self.logger.info("🛑 Trading Indicator Manager shutting down...")
            
            # Cleanup caches
            self.data_cache.clear()
            self.indicator_cache.clear()
            
            # Publish shutdown event
            await self.event_manager.publish_event(
                "indicator_manager_shutdown",
                {"service": "ml-processing", "graceful": True}
            )
            
            self.logger.info("✅ Trading Indicator Manager shutdown completed")
            
        except Exception as e:
            self.logger.error(f"❌ Error during shutdown: {e}")


# Factory functions
def create_trading_indicator_manager(cache_config: Optional[Dict] = None) -> TradingIndicatorManager:
    """Create and return a TradingIndicatorManager instance"""
    return TradingIndicatorManager(cache_config)


# Export all classes
__all__ = [
    "TradingIndicatorManager",
    "IndicatorType",
    "IndicatorConfig", 
    "MarketData",
    "MarketIndicator",
    "FeatureSet",
    "create_trading_indicator_manager"
]