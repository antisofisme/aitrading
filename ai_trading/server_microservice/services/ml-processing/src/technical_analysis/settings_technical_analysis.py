"""
Configuration settings for Technical Analysis modules - MICROSERVICE VERSION
Centralized configuration for technical indicators, patterns, and market analysis
Optimized for microservice architecture with per-service configuration management
"""

# MICROSERVICE CENTRALIZATION INFRASTRUCTURE
from ....shared.infrastructure.config.base_config import BaseConfig

# Standard library imports
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Initialize microservice configuration
config = BaseConfig(service_name="ml-processing")


class IndicatorType(Enum):
    """Technical indicator types"""
    MOMENTUM = "momentum"
    TREND = "trend"
    VOLATILITY = "volatility"
    VOLUME = "volume"
    OSCILLATOR = "oscillator"
    SUPPORT_RESISTANCE = "support_resistance"
    PATTERN = "pattern"
    SENTIMENT = "sentiment"


class TimeFrame(Enum):
    """Trading timeframes"""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"
    MN1 = "1mn"


class PatternType(Enum):
    """Chart pattern types"""
    REVERSAL = "reversal"
    CONTINUATION = "continuation"
    HARMONIC = "harmonic"
    CANDLESTICK = "candlestick"
    VOLUME = "volume"
    PRICE_ACTION = "price_action"


@dataclass
class TradingIndicatorConfig:
    """Trading indicator configuration for microservice"""
    # Core indicators enabled
    indicators_enabled: bool = config.get_bool("trading_indicators_enabled", True)
    
    # RSI configuration
    rsi_enabled: bool = config.get_bool("indicator_rsi_enabled", True)
    rsi_period: int = config.get_int("indicator_rsi_period", 14)
    rsi_overbought: float = config.get_float("indicator_rsi_overbought", 70.0)
    rsi_oversold: float = config.get_float("indicator_rsi_oversold", 30.0)
    
    # MACD configuration
    macd_enabled: bool = config.get_bool("indicator_macd_enabled", True)
    macd_fast_period: int = config.get_int("indicator_macd_fast_period", 12)
    macd_slow_period: int = config.get_int("indicator_macd_slow_period", 26)
    macd_signal_period: int = config.get_int("indicator_macd_signal_period", 9)
    
    # Stochastic configuration
    stochastic_enabled: bool = config.get_bool("indicator_stochastic_enabled", True)
    stochastic_k_period: int = config.get_int("indicator_stochastic_k_period", 14)
    stochastic_d_period: int = config.get_int("indicator_stochastic_d_period", 3)
    stochastic_smooth: int = config.get_int("indicator_stochastic_smooth", 3)
    
    # Money Flow Index configuration
    mfi_enabled: bool = config.get_bool("indicator_mfi_enabled", True)
    mfi_period: int = config.get_int("indicator_mfi_period", 14)
    mfi_overbought: float = config.get_float("indicator_mfi_overbought", 80.0)
    mfi_oversold: float = config.get_float("indicator_mfi_oversold", 20.0)
    
    # Accumulation/Distribution Line
    adl_enabled: bool = config.get_bool("indicator_adl_enabled", True)
    
    # Awesome Oscillator
    ao_enabled: bool = config.get_bool("indicator_ao_enabled", True)
    ao_fast_period: int = config.get_int("indicator_ao_fast_period", 5)
    ao_slow_period: int = config.get_int("indicator_ao_slow_period", 34)
    
    # On-Balance Volume
    obv_enabled: bool = config.get_bool("indicator_obv_enabled", True)
    
    # Volume indicators
    volume_enabled: bool = config.get_bool("indicator_volume_enabled", True)
    volume_sma_period: int = config.get_int("indicator_volume_sma_period", 20)
    
    # Correlation analysis
    correlation_enabled: bool = config.get_bool("indicator_correlation_enabled", True)
    correlation_period: int = config.get_int("indicator_correlation_period", 50)
    correlation_pairs: List[str] = field(default_factory=lambda: 
        config.get_list("indicator_correlation_pairs", ["XAUUSD", "EURUSD", "XAGUSD", "AUDUSD"])
    )
    
    # Order book analysis
    orderbook_enabled: bool = config.get_bool("indicator_orderbook_enabled", True)
    orderbook_levels: int = config.get_int("indicator_orderbook_levels", 10)
    
    # Session analysis
    session_analysis_enabled: bool = config.get_bool("indicator_session_analysis_enabled", True)
    session_overlap_analysis: bool = config.get_bool("indicator_session_overlap_analysis", True)
    
    # Slippage analysis
    slippage_enabled: bool = config.get_bool("indicator_slippage_enabled", True)
    slippage_threshold: float = config.get_float("indicator_slippage_threshold", 0.0001)
    
    # Time and sales analysis
    timesales_enabled: bool = config.get_bool("indicator_timesales_enabled", True)
    timesales_window: int = config.get_int("indicator_timesales_window", 100)
    
    # Economic indicator integration
    economic_enabled: bool = config.get_bool("indicator_economic_enabled", True)
    economic_impact_threshold: str = config.get_string("indicator_economic_impact_threshold", "medium")
    
    # Bollinger Bands configuration
    bollinger_enabled: bool = config.get_bool("indicator_bollinger_enabled", True)
    bollinger_period: int = config.get_int("indicator_bollinger_period", 20)
    bollinger_std_dev: float = config.get_float("indicator_bollinger_std_dev", 2.0)
    bollinger_squeeze_enabled: bool = config.get_bool("indicator_bollinger_squeeze", True)
    
    # Ichimoku configuration
    ichimoku_enabled: bool = config.get_bool("indicator_ichimoku_enabled", True)
    ichimoku_tenkan_period: int = config.get_int("indicator_ichimoku_tenkan_period", 9)
    ichimoku_kijun_period: int = config.get_int("indicator_ichimoku_kijun_period", 26)
    ichimoku_senkou_b_period: int = config.get_int("indicator_ichimoku_senkou_b_period", 52)
    ichimoku_chikou_displacement: int = config.get_int("indicator_ichimoku_chikou_displacement", 26)
    
    # EMA (Exponential Moving Average) configuration
    ema_enabled: bool = config.get_bool("indicator_ema_enabled", True)
    ema_periods: List[int] = field(default_factory=lambda: 
        config.get_list("indicator_ema_periods", [9, 21, 50, 200])
    )
    ema_cross_signals: bool = config.get_bool("indicator_ema_cross_signals", True)
    
    # SMA (Simple Moving Average) configuration
    sma_enabled: bool = config.get_bool("indicator_sma_enabled", True)
    sma_periods: List[int] = field(default_factory=lambda: 
        config.get_list("indicator_sma_periods", [10, 20, 50, 100, 200])
    )
    sma_cross_signals: bool = config.get_bool("indicator_sma_cross_signals", True)
    
    # ATR (Average True Range) configuration
    atr_enabled: bool = config.get_bool("indicator_atr_enabled", True)
    atr_period: int = config.get_int("indicator_atr_period", 14)
    atr_volatility_bands: bool = config.get_bool("indicator_atr_volatility_bands", True)
    
    # Williams %R configuration
    williams_r_enabled: bool = config.get_bool("indicator_williams_r_enabled", True)
    williams_r_period: int = config.get_int("indicator_williams_r_period", 14)
    williams_r_overbought: float = config.get_float("indicator_williams_r_overbought", -20.0)
    williams_r_oversold: float = config.get_float("indicator_williams_r_oversold", -80.0)
    
    # CCI (Commodity Channel Index) configuration
    cci_enabled: bool = config.get_bool("indicator_cci_enabled", True)
    cci_period: int = config.get_int("indicator_cci_period", 20)
    cci_overbought: float = config.get_float("indicator_cci_overbought", 100.0)
    cci_oversold: float = config.get_float("indicator_cci_oversold", -100.0)
    
    # Parabolic SAR configuration
    parabolic_sar_enabled: bool = config.get_bool("indicator_parabolic_sar_enabled", True)
    parabolic_sar_step: float = config.get_float("indicator_parabolic_sar_step", 0.02)
    parabolic_sar_maximum: float = config.get_float("indicator_parabolic_sar_maximum", 0.2)
    
    # Aroon configuration
    aroon_enabled: bool = config.get_bool("indicator_aroon_enabled", True)
    aroon_period: int = config.get_int("indicator_aroon_period", 14)
    
    # Chande Momentum Oscillator
    cmo_enabled: bool = config.get_bool("indicator_cmo_enabled", True)
    cmo_period: int = config.get_int("indicator_cmo_period", 14)
    
    # Donchian Channel
    donchian_enabled: bool = config.get_bool("indicator_donchian_enabled", True)
    donchian_period: int = config.get_int("indicator_donchian_period", 20)
    
    # Keltner Channel
    keltner_enabled: bool = config.get_bool("indicator_keltner_enabled", True)
    keltner_period: int = config.get_int("indicator_keltner_period", 20)
    keltner_multiplier: float = config.get_float("indicator_keltner_multiplier", 2.0)


@dataclass
class CacheConfig:
    """Intelligent indicator cache configuration for microservice"""
    # Cache settings
    cache_enabled: bool = config.get_bool("indicator_cache_enabled", True)
    cache_ttl: int = config.get_int("indicator_cache_ttl", 300)  # 5 minutes
    cache_size_limit: int = config.get_int("indicator_cache_size_limit", 10000)
    
    # Delta-based optimization
    delta_optimization_enabled: bool = config.get_bool("indicator_cache_delta_optimization", True)
    delta_threshold: float = config.get_float("indicator_cache_delta_threshold", 0.0001)
    
    # Window optimization
    window_optimization_enabled: bool = config.get_bool("indicator_cache_window_optimization", True)
    optimization_window: int = config.get_int("indicator_cache_optimization_window", 1000)
    
    # Performance monitoring
    performance_monitoring_enabled: bool = config.get_bool("indicator_cache_performance_monitoring", True)
    cache_hit_rate_threshold: float = config.get_float("indicator_cache_hit_rate_threshold", 0.8)
    
    # Memory management
    memory_management_enabled: bool = config.get_bool("indicator_cache_memory_management", True)
    max_memory_usage_mb: int = config.get_int("indicator_cache_max_memory_mb", 512)
    
    # Precomputation
    precomputation_enabled: bool = config.get_bool("indicator_cache_precomputation", True)
    precomputation_symbols: List[str] = field(default_factory=lambda: 
        config.get_list("indicator_cache_precomputation_symbols", ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"])
    )


@dataclass
class MultiTimeframeConfig:
    """Multi-timeframe analysis configuration for microservice"""
    # Multi-timeframe analysis
    multi_timeframe_enabled: bool = config.get_bool("multi_timeframe_enabled", True)
    primary_timeframe: TimeFrame = TimeFrame(config.get_string("multi_timeframe_primary", "1h"))
    secondary_timeframes: List[TimeFrame] = field(default_factory=lambda: 
        [TimeFrame(tf) for tf in config.get_list("multi_timeframe_secondary", ["15m", "4h", "1d"])]
    )
    
    # Trend alignment
    trend_alignment_enabled: bool = config.get_bool("multi_timeframe_trend_alignment", True)
    trend_alignment_threshold: float = config.get_float("multi_timeframe_trend_alignment_threshold", 0.7)
    
    # Higher timeframe confirmation
    htf_confirmation_enabled: bool = config.get_bool("multi_timeframe_htf_confirmation", True)
    htf_confirmation_timeframes: List[TimeFrame] = field(default_factory=lambda: 
        [TimeFrame(tf) for tf in config.get_list("multi_timeframe_htf_confirmation_timeframes", ["4h", "1d"])]
    )
    
    # Lower timeframe precision
    ltf_precision_enabled: bool = config.get_bool("multi_timeframe_ltf_precision", True)
    ltf_precision_timeframes: List[TimeFrame] = field(default_factory=lambda: 
        [TimeFrame(tf) for tf in config.get_list("multi_timeframe_ltf_precision_timeframes", ["1m", "5m", "15m"])]
    )
    
    # Divergence detection
    divergence_detection_enabled: bool = config.get_bool("multi_timeframe_divergence_detection", True)
    divergence_confirmation_periods: int = config.get_int("multi_timeframe_divergence_confirmation_periods", 3)
    
    # Market structure analysis
    market_structure_enabled: bool = config.get_bool("multi_timeframe_market_structure", True)
    structure_confirmation_timeframes: List[TimeFrame] = field(default_factory=lambda: 
        [TimeFrame(tf) for tf in config.get_list("multi_timeframe_structure_confirmation", ["1h", "4h", "1d"])]
    )


@dataclass
class PatternRecognitionConfig:
    """Pattern recognition configuration for microservice"""
    # Pattern recognition
    pattern_recognition_enabled: bool = config.get_bool("pattern_recognition_enabled", True)
    pattern_confidence_threshold: float = config.get_float("pattern_recognition_confidence_threshold", 0.7)
    
    # Neural pattern recognition
    neural_patterns_enabled: bool = config.get_bool("pattern_recognition_neural_enabled", True)
    neural_model_path: str = config.get_string("pattern_recognition_neural_model_path", "models/neural_patterns.pkl")
    
    # Classical patterns
    classical_patterns_enabled: bool = config.get_bool("pattern_recognition_classical_enabled", True)
    classical_patterns: List[str] = field(default_factory=lambda: 
        config.get_list("pattern_recognition_classical_patterns", 
                       ["head_shoulders", "double_top", "double_bottom", "triangle", "flag", "pennant", "wedge"])
    )
    
    # Candlestick patterns
    candlestick_patterns_enabled: bool = config.get_bool("pattern_recognition_candlestick_enabled", True)
    candlestick_patterns: List[str] = field(default_factory=lambda: 
        config.get_list("pattern_recognition_candlestick_patterns", 
                       ["doji", "hammer", "shooting_star", "engulfing", "harami", "morning_star", "evening_star"])
    )
    
    # Harmonic patterns
    harmonic_patterns_enabled: bool = config.get_bool("pattern_recognition_harmonic_enabled", True)
    harmonic_patterns: List[str] = field(default_factory=lambda: 
        config.get_list("pattern_recognition_harmonic_patterns", 
                       ["gartley", "butterfly", "bat", "crab", "deep_crab", "shark", "cypher"])
    )
    
    # Volume patterns
    volume_patterns_enabled: bool = config.get_bool("pattern_recognition_volume_enabled", True)
    volume_confirmation_required: bool = config.get_bool("pattern_recognition_volume_confirmation", True)
    
    # Pattern validation
    pattern_validation_enabled: bool = config.get_bool("pattern_recognition_validation_enabled", True)
    validation_periods: int = config.get_int("pattern_recognition_validation_periods", 10)
    
    # Enhanced pattern discovery
    enhanced_discovery_enabled: bool = config.get_bool("pattern_recognition_enhanced_discovery", True)
    discovery_algorithms: List[str] = field(default_factory=lambda: 
        config.get_list("pattern_recognition_discovery_algorithms", 
                       ["dtw", "matrix_profile", "symbolic_representation", "motif_discovery"])
    )


@dataclass
class MarketSentimentConfig:
    """Market sentiment analysis configuration for microservice"""
    # Sentiment analysis
    sentiment_analysis_enabled: bool = config.get_bool("sentiment_analysis_enabled", True)
    sentiment_sources: List[str] = field(default_factory=lambda: 
        config.get_list("sentiment_analysis_sources", ["news", "social_media", "economic_calendar", "cot_reports"])
    )
    
    # News sentiment
    news_sentiment_enabled: bool = config.get_bool("sentiment_news_enabled", True)
    news_sources: List[str] = field(default_factory=lambda: 
        config.get_list("sentiment_news_sources", ["reuters", "bloomberg", "forex_factory", "investing_com"])
    )
    news_sentiment_model: str = config.get_string("sentiment_news_model", "finbert")
    
    # Social media sentiment
    social_media_enabled: bool = config.get_bool("sentiment_social_media_enabled", False)
    social_media_sources: List[str] = field(default_factory=lambda: 
        config.get_list("sentiment_social_media_sources", ["twitter", "reddit", "telegram"])
    )
    
    # Economic calendar sentiment
    economic_calendar_enabled: bool = config.get_bool("sentiment_economic_calendar_enabled", True)
    economic_impact_weights: Dict[str, float] = field(default_factory=lambda: {
        "high": config.get_float("sentiment_economic_high_weight", 1.0),
        "medium": config.get_float("sentiment_economic_medium_weight", 0.6),
        "low": config.get_float("sentiment_economic_low_weight", 0.3)
    })
    
    # COT reports sentiment
    cot_reports_enabled: bool = config.get_bool("sentiment_cot_reports_enabled", True)
    cot_instruments: List[str] = field(default_factory=lambda: 
        config.get_list("sentiment_cot_instruments", ["GOLD", "SILVER", "CRUDE_OIL", "EURUSD", "GBPUSD", "USDJPY"])
    )
    
    # Sentiment aggregation
    sentiment_aggregation_method: str = config.get_string("sentiment_aggregation_method", "weighted_average")
    sentiment_threshold_bullish: float = config.get_float("sentiment_threshold_bullish", 0.6)
    sentiment_threshold_bearish: float = config.get_float("sentiment_threshold_bearish", -0.6)
    
    # Real-time sentiment updates
    realtime_sentiment_enabled: bool = config.get_bool("sentiment_realtime_enabled", True)
    sentiment_update_interval: int = config.get_int("sentiment_update_interval", 300)  # 5 minutes


@dataclass
class AdvancedPatternConfig:
    """Advanced pattern recognition configuration for microservice"""
    # General pattern recognition
    pattern_recognition_enabled: bool = config.get_bool("pattern_recognition_enabled", True)
    pattern_confidence_threshold: float = config.get_float("pattern_confidence_threshold", 0.7)
    
    # Harmonic Patterns
    harmonic_patterns_enabled: bool = config.get_bool("harmonic_patterns_enabled", True)
    harmonic_patterns: List[str] = field(default_factory=lambda: 
        config.get_list("harmonic_pattern_types", ["gartley", "butterfly", "bat", "crab", "deep_crab", "shark", "cypher"])
    )
    harmonic_completion_threshold: float = config.get_float("harmonic_completion_threshold", 0.8)
    
    # Elliott Wave Analysis
    elliott_wave_enabled: bool = config.get_bool("elliott_wave_enabled", True)
    elliott_wave_degrees: List[str] = field(default_factory=lambda: 
        config.get_list("elliott_wave_degrees", ["minuette", "minute", "minor", "intermediate", "primary"])
    )
    elliott_wave_completion_threshold: float = config.get_float("elliott_wave_completion", 0.6)
    
    # Candlestick Patterns
    candlestick_patterns_enabled: bool = config.get_bool("candlestick_patterns_enabled", True)
    candlestick_patterns: List[str] = field(default_factory=lambda: 
        config.get_list("candlestick_pattern_types", 
                       ["doji", "hammer", "shooting_star", "engulfing", "harami", "morning_star", "evening_star", "piercing_line", "dark_cloud_cover"])
    )
    candlestick_reliability_threshold: float = config.get_float("candlestick_reliability", 0.7)
    
    # Chart Patterns
    chart_patterns_enabled: bool = config.get_bool("chart_patterns_enabled", True)
    chart_patterns: List[str] = field(default_factory=lambda: 
        config.get_list("chart_pattern_types", 
                       ["head_shoulders", "double_top", "double_bottom", "triangle", "flag", "pennant", "wedge", "cup_handle"])
    )
    chart_pattern_volume_confirmation: bool = config.get_bool("chart_pattern_volume_confirmation", True)
    
    # Fibonacci Analysis
    fibonacci_enabled: bool = config.get_bool("fibonacci_enabled", True)
    fibonacci_retracement_levels: List[float] = field(default_factory=lambda: 
        config.get_list("fibonacci_retracement", [0.236, 0.382, 0.5, 0.618, 0.786])
    )
    fibonacci_extension_levels: List[float] = field(default_factory=lambda: 
        config.get_list("fibonacci_extension", [1.272, 1.414, 1.618, 2.618])
    )
    fibonacci_confluence_threshold: float = config.get_float("fibonacci_confluence", 0.8)
    
    # Volume Pattern Analysis
    volume_patterns_enabled: bool = config.get_bool("volume_patterns_enabled", True)
    volume_anomaly_threshold: float = config.get_float("volume_anomaly_threshold", 2.0)  # 2x normal
    volume_confirmation_required: bool = config.get_bool("volume_confirmation", True)
    
    # Market Structure Analysis
    market_structure_enabled: bool = config.get_bool("market_structure_enabled", True)
    market_structure_shift_enabled: bool = config.get_bool("market_structure_shift_enabled", True)
    break_of_structure_enabled: bool = config.get_bool("break_of_structure_enabled", True)
    change_of_character_enabled: bool = config.get_bool("change_of_character_enabled", True)
    order_block_formation_enabled: bool = config.get_bool("order_block_formation_enabled", True)
    
    # Smart Money Concepts
    smart_money_concepts_enabled: bool = config.get_bool("smart_money_concepts_enabled", True)
    fair_value_gaps_enabled: bool = config.get_bool("fair_value_gaps_enabled", True)
    imbalance_detection_enabled: bool = config.get_bool("imbalance_detection_enabled", True)
    institutional_candles_enabled: bool = config.get_bool("institutional_candles_enabled", True)
    liquidity_grabs_enabled: bool = config.get_bool("liquidity_grabs_enabled", True)
    
    # Multi-timeframe Pattern Analysis
    multi_timeframe_patterns_enabled: bool = config.get_bool("multi_timeframe_patterns_enabled", True)
    pattern_alignment_threshold: float = config.get_float("pattern_alignment_threshold", 0.7)
    
    # Pattern Quality and Risk Management
    pattern_quality_enabled: bool = config.get_bool("pattern_quality_enabled", True)
    historical_success_rate_threshold: float = config.get_float("historical_success_rate", 0.6)
    risk_reward_ratio_minimum: float = config.get_float("risk_reward_ratio_min", 1.5)
    
    # Pattern Invalidation
    invalidation_monitoring_enabled: bool = config.get_bool("invalidation_monitoring_enabled", True)
    invalidation_auto_trigger: bool = config.get_bool("invalidation_auto_trigger", True)


@dataclass
class TechnicalAnalysisSettings:
    """Main technical analysis settings for microservice"""
    # Module settings
    enabled: bool = config.get_bool("technical_analysis_enabled", True)
    debug_mode: bool = config.get_bool("technical_analysis_debug", False)
    
    # Configuration components
    indicators: TradingIndicatorConfig = field(default_factory=TradingIndicatorConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    multi_timeframe: MultiTimeframeConfig = field(default_factory=MultiTimeframeConfig)
    pattern_recognition: PatternRecognitionConfig = field(default_factory=PatternRecognitionConfig)
    market_sentiment: MarketSentimentConfig = field(default_factory=MarketSentimentConfig)
    advanced_patterns: AdvancedPatternConfig = field(default_factory=AdvancedPatternConfig)
    
    # Processing settings
    batch_size: int = config.get_int("technical_analysis_batch_size", 1000)
    max_workers: int = config.get_int("technical_analysis_max_workers", 4)
    processing_timeout: int = config.get_int("technical_analysis_processing_timeout", 30)
    
    # Data requirements
    min_data_points: int = config.get_int("technical_analysis_min_data_points", 100)
    max_data_points: int = config.get_int("technical_analysis_max_data_points", 10000)
    data_quality_threshold: float = config.get_float("technical_analysis_data_quality_threshold", 0.95)
    
    # Output settings
    output_format: str = config.get_string("technical_analysis_output_format", "json")
    include_metadata: bool = config.get_bool("technical_analysis_include_metadata", True)
    include_confidence_scores: bool = config.get_bool("technical_analysis_include_confidence_scores", True)
    
    # Database integration
    database_enabled: bool = config.get_bool("technical_analysis_database_enabled", True)
    store_results: bool = config.get_bool("technical_analysis_store_results", True)
    result_retention_days: int = config.get_int("technical_analysis_result_retention_days", 30)
    
    # Logging and monitoring
    logging_enabled: bool = config.get_bool("technical_analysis_logging_enabled", True)
    logging_level: str = config.get_string("technical_analysis_logging_level", "INFO")
    metrics_enabled: bool = config.get_bool("technical_analysis_metrics_enabled", True)
    
    # Error handling
    error_handling_enabled: bool = config.get_bool("technical_analysis_error_handling", True)
    max_retries: int = config.get_int("technical_analysis_max_retries", 3)
    retry_delay: int = config.get_int("technical_analysis_retry_delay", 1)
    
    # Health checks
    health_check_enabled: bool = config.get_bool("technical_analysis_health_check", True)
    health_check_interval: int = config.get_int("technical_analysis_health_check_interval", 300)  # 5 minutes
    
    # Microservice specific settings
    service_name: str = "ml-processing"
    service_version: str = config.get_string("service_version", "1.0.0")


# Global settings instance for microservice
technical_analysis_settings = TechnicalAnalysisSettings()


def get_technical_analysis_settings() -> TechnicalAnalysisSettings:
    """Get technical analysis settings for microservice"""
    return technical_analysis_settings


def get_enabled_indicators() -> List[str]:
    """Get list of enabled indicators"""
    enabled_indicators = []
    settings = technical_analysis_settings.indicators
    
    if settings.rsi_enabled:
        enabled_indicators.append("RSI")
    if settings.macd_enabled:
        enabled_indicators.append("MACD")
    if settings.stochastic_enabled:
        enabled_indicators.append("Stochastic")
    if settings.mfi_enabled:
        enabled_indicators.append("MFI")
    if settings.adl_enabled:
        enabled_indicators.append("ADL")
    if settings.ao_enabled:
        enabled_indicators.append("AO")
    if settings.obv_enabled:
        enabled_indicators.append("OBV")
    if settings.volume_enabled:
        enabled_indicators.append("Volume")
    if settings.correlation_enabled:
        enabled_indicators.append("Correlation")
    if settings.orderbook_enabled:
        enabled_indicators.append("Orderbook")
    if settings.session_analysis_enabled:
        enabled_indicators.append("Session")
    if settings.slippage_enabled:
        enabled_indicators.append("Slippage")
    if settings.timesales_enabled:
        enabled_indicators.append("Timesales")
    if settings.economic_enabled:
        enabled_indicators.append("Economic")
    if settings.bollinger_enabled:
        enabled_indicators.append("Bollinger")
    if settings.ichimoku_enabled:
        enabled_indicators.append("Ichimoku")
    if settings.ema_enabled:
        enabled_indicators.append("EMA")
    if settings.sma_enabled:
        enabled_indicators.append("SMA")
    if settings.atr_enabled:
        enabled_indicators.append("ATR")
    if settings.williams_r_enabled:
        enabled_indicators.append("Williams_R")
    if settings.cci_enabled:
        enabled_indicators.append("CCI")
    if settings.parabolic_sar_enabled:
        enabled_indicators.append("Parabolic_SAR")
    if settings.aroon_enabled:
        enabled_indicators.append("Aroon")
    if settings.cmo_enabled:
        enabled_indicators.append("CMO")
    if settings.donchian_enabled:
        enabled_indicators.append("Donchian")
    if settings.keltner_enabled:
        enabled_indicators.append("Keltner")
    
    return enabled_indicators


def get_enabled_patterns() -> List[str]:
    """Get list of enabled pattern types"""
    enabled_patterns = []
    settings = technical_analysis_settings.pattern_recognition
    
    if settings.classical_patterns_enabled:
        enabled_patterns.extend(settings.classical_patterns)
    if settings.candlestick_patterns_enabled:
        enabled_patterns.extend(settings.candlestick_patterns)
    if settings.harmonic_patterns_enabled:
        enabled_patterns.extend(settings.harmonic_patterns)
    
    return enabled_patterns


def get_multi_timeframe_config() -> Dict[str, Any]:
    """Get multi-timeframe analysis configuration"""
    settings = technical_analysis_settings.multi_timeframe
    return {
        "enabled": settings.multi_timeframe_enabled,
        "primary_timeframe": settings.primary_timeframe.value,
        "secondary_timeframes": [tf.value for tf in settings.secondary_timeframes],
        "trend_alignment": settings.trend_alignment_enabled,
        "htf_confirmation": settings.htf_confirmation_enabled,
        "ltf_precision": settings.ltf_precision_enabled,
        "divergence_detection": settings.divergence_detection_enabled,
        "market_structure": settings.market_structure_enabled
    }


def get_sentiment_analysis_config() -> Dict[str, Any]:
    """Get sentiment analysis configuration"""
    settings = technical_analysis_settings.market_sentiment
    return {
        "enabled": settings.sentiment_analysis_enabled,
        "sources": settings.sentiment_sources,
        "news_enabled": settings.news_sentiment_enabled,
        "social_media_enabled": settings.social_media_enabled,
        "economic_calendar_enabled": settings.economic_calendar_enabled,
        "cot_reports_enabled": settings.cot_reports_enabled,
        "realtime_enabled": settings.realtime_sentiment_enabled,
        "update_interval": settings.sentiment_update_interval
    }


def get_enabled_advanced_patterns() -> List[str]:
    """Get list of enabled advanced pattern types"""
    enabled_patterns = []
    settings = technical_analysis_settings.advanced_patterns
    
    if settings.harmonic_patterns_enabled:
        enabled_patterns.extend(settings.harmonic_patterns)
    if settings.elliott_wave_enabled:
        enabled_patterns.append("elliott_wave")
    if settings.candlestick_patterns_enabled:
        enabled_patterns.extend(settings.candlestick_patterns)
    if settings.chart_patterns_enabled:
        enabled_patterns.extend(settings.chart_patterns)
    if settings.fibonacci_enabled:
        enabled_patterns.append("fibonacci")
    if settings.volume_patterns_enabled:
        enabled_patterns.append("volume_patterns")
    if settings.market_structure_enabled:
        enabled_patterns.append("market_structure")
    if settings.smart_money_concepts_enabled:
        enabled_patterns.append("smart_money_concepts")
    if settings.fair_value_gaps_enabled:
        enabled_patterns.append("fair_value_gaps")
    if settings.institutional_candles_enabled:
        enabled_patterns.append("institutional_candles")
    if settings.liquidity_grabs_enabled:
        enabled_patterns.append("liquidity_grabs")
    if settings.break_of_structure_enabled:
        enabled_patterns.append("break_of_structure")
    if settings.change_of_character_enabled:
        enabled_patterns.append("change_of_character")
    if settings.order_block_formation_enabled:
        enabled_patterns.append("order_block_formation")
    
    return enabled_patterns


def get_cache_config() -> Dict[str, Any]:
    """Get cache configuration"""
    settings = technical_analysis_settings.cache
    return {
        "cache_enabled": settings.cache_enabled,
        "cache_ttl": settings.cache_ttl,
        "cache_size_limit": settings.cache_size_limit,
        "delta_optimization_enabled": settings.delta_optimization_enabled,
        "delta_threshold": settings.delta_threshold,
        "window_optimization_enabled": settings.window_optimization_enabled,
        "optimization_window": settings.optimization_window,
        "performance_monitoring_enabled": settings.performance_monitoring_enabled,
        "cache_hit_rate_threshold": settings.cache_hit_rate_threshold,
        "memory_management_enabled": settings.memory_management_enabled,
        "max_memory_usage_mb": settings.max_memory_usage_mb,
        "precomputation_enabled": settings.precomputation_enabled,
        "precomputation_symbols": settings.precomputation_symbols
    }


def get_microservice_config() -> Dict[str, Any]:
    """Get microservice-specific configuration"""
    settings = technical_analysis_settings
    return {
        "service_name": settings.service_name,
        "service_version": settings.service_version,
        "enabled": settings.enabled,
        "debug_mode": settings.debug_mode,
        "batch_size": settings.batch_size,
        "max_workers": settings.max_workers,
        "processing_timeout": settings.processing_timeout,
        "min_data_points": settings.min_data_points,
        "max_data_points": settings.max_data_points,
        "data_quality_threshold": settings.data_quality_threshold,
        "database_enabled": settings.database_enabled,
        "store_results": settings.store_results,
        "result_retention_days": settings.result_retention_days,
        "logging_enabled": settings.logging_enabled,
        "logging_level": settings.logging_level,
        "metrics_enabled": settings.metrics_enabled,
        "error_handling_enabled": settings.error_handling_enabled,
        "max_retries": settings.max_retries,
        "retry_delay": settings.retry_delay,
        "health_check_enabled": settings.health_check_enabled,
        "health_check_interval": settings.health_check_interval
    }


# Export main configuration classes and functions
__all__ = [
    'TechnicalAnalysisSettings',
    'TradingIndicatorConfig',
    'CacheConfig',
    'MultiTimeframeConfig',
    'PatternRecognitionConfig',
    'MarketSentimentConfig',
    'AdvancedPatternConfig',
    'IndicatorType',
    'TimeFrame',
    'PatternType',
    'technical_analysis_settings',
    'get_technical_analysis_settings',
    'get_enabled_indicators',
    'get_enabled_patterns',
    'get_multi_timeframe_config',
    'get_sentiment_analysis_config',
    'get_enabled_advanced_patterns',
    'get_cache_config',
    'get_microservice_config'
]