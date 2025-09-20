"""
Strategy Templates - Pre-built Trading Strategy Templates
Comprehensive collection of moving average, mean reversion, momentum, and composite strategies
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import numpy as np

from ..models.strategy_models import (
    StrategyTemplate,
    StrategyDefinition,
    StrategyParameters,
    RiskParameters,
    TradingRule,
    StrategyType,
    OptimizationObjective
)

logger = logging.getLogger(__name__)


class TemplateComplexity(Enum):
    """Strategy template complexity levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class StrategyTemplateManager:
    """
    Comprehensive strategy template manager with pre-built strategies
    Includes moving average, mean reversion, momentum, and multi-indicator strategies
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize strategy template manager"""
        self.config = config or {}
        
        # Template storage
        self._templates: Dict[str, StrategyTemplate] = {}
        
        # Load built-in templates
        self._initialize_builtin_templates()
        
        logger.info("StrategyTemplateManager initialized with {} templates".format(len(self._templates)))
    
    def _initialize_builtin_templates(self):
        """Initialize all built-in strategy templates"""
        
        # Moving Average Strategies
        self._create_sma_crossover_template()
        self._create_ema_crossover_template()
        self._create_triple_moving_average_template()
        self._create_adaptive_moving_average_template()
        
        # Mean Reversion Strategies
        self._create_rsi_mean_reversion_template()
        self._create_bollinger_bands_template()
        self._create_mean_reversion_pairs_template()
        self._create_rsi_bollinger_combo_template()
        
        # Momentum Strategies
        self._create_macd_momentum_template()
        self._create_breakout_strategy_template()
        self._create_trend_following_template()
        self._create_momentum_oscillator_template()
        
        # Multi-Indicator Composite Strategies
        self._create_balanced_composite_template()
        self._create_aggressive_growth_template()
        self._create_conservative_income_template()
        self._create_market_neutral_template()
        
        # Advanced Strategies
        self._create_volatility_breakout_template()
        self._create_statistical_arbitrage_template()
        self._create_regime_aware_template()
        
    # ==================== MOVING AVERAGE STRATEGIES ====================
    
    def _create_sma_crossover_template(self):
        """Simple Moving Average Crossover Strategy"""
        
        template = StrategyTemplate(
            template_id="sma_crossover_basic",
            name="Simple Moving Average Crossover",
            strategy_type=StrategyType.MOMENTUM,
            description="Classic trend-following strategy using SMA crossover signals. "
                       "Goes long when fast SMA crosses above slow SMA, short when it crosses below.",
            
            trading_rules=[
                TradingRule(
                    rule_id="sma_long_entry",
                    rule_type="entry",
                    indicator="sma",
                    parameters={"fast_period": 10, "slow_period": 20},
                    logic="crossover_above",
                    weight=1.0,
                    enabled=True
                ),
                TradingRule(
                    rule_id="sma_short_entry", 
                    rule_type="entry",
                    indicator="sma",
                    parameters={"fast_period": 10, "slow_period": 20},
                    logic="crossover_below",
                    weight=1.0,
                    enabled=True
                ),
                TradingRule(
                    rule_id="sma_long_exit",
                    rule_type="exit",
                    indicator="sma", 
                    parameters={"fast_period": 10, "slow_period": 20},
                    logic="crossover_below",
                    weight=1.0,
                    enabled=True
                ),
                TradingRule(
                    rule_id="sma_short_exit",
                    rule_type="exit",
                    indicator="sma",
                    parameters={"fast_period": 10, "slow_period": 20},
                    logic="crossover_above",
                    weight=1.0,
                    enabled=True
                )
            ],
            
            default_parameters=StrategyParameters(
                sma_fast_period=10,
                sma_slow_period=20,
                lookback_period=50,
                rebalancing_frequency="daily"
            ),
            
            risk_parameters=RiskParameters(
                max_position_size=0.1,
                stop_loss_percentage=-0.03,
                take_profit_percentage=0.06,
                max_daily_loss=-0.02,
                max_drawdown=-0.1,
                risk_per_trade=0.02
            ),
            
            parameter_bounds={
                "sma_fast_period": (5, 50),
                "sma_slow_period": (10, 100),
                "lookback_period": (20, 200)
            },
            
            parameter_types={
                "sma_fast_period": "int",
                "sma_slow_period": "int", 
                "lookback_period": "int"
            },
            
            complexity_score=2.0,
            recommended_timeframe="1D",
            minimum_capital=5000.0,
            expected_sharpe=0.8,
            expected_drawdown=-0.08,
            expected_win_rate=0.58,
            required_indicators=["sma"],
            data_requirements=["close_price"],
            version="1.0.0"
        )
        
        self._templates[template.template_id] = template
    
    def _create_ema_crossover_template(self):
        """Exponential Moving Average Crossover Strategy"""
        
        template = StrategyTemplate(
            template_id="ema_crossover_responsive",
            name="Exponential Moving Average Crossover",
            strategy_type=StrategyType.MOMENTUM,
            description="More responsive trend-following strategy using EMA crossover. "
                       "EMAs react faster to price changes than SMAs, providing earlier signals.",
            
            trading_rules=[
                TradingRule(
                    rule_id="ema_long_entry",
                    rule_type="entry",
                    indicator="ema",
                    parameters={"fast_period": 12, "slow_period": 26},
                    logic="crossover_above",
                    weight=1.0,
                    enabled=True
                ),
                TradingRule(
                    rule_id="ema_short_entry",
                    rule_type="entry", 
                    indicator="ema",
                    parameters={"fast_period": 12, "slow_period": 26},
                    logic="crossover_below",
                    weight=1.0,
                    enabled=True
                ),
                TradingRule(
                    rule_id="ema_trend_filter",
                    rule_type="filter",
                    indicator="ema",
                    parameters={"period": 50},
                    logic="price_above",
                    weight=0.3,
                    enabled=True
                )
            ],
            
            default_parameters=StrategyParameters(
                ema_fast_period=12,
                ema_slow_period=26,
                lookback_period=50,
                rebalancing_frequency="daily"
            ),
            
            risk_parameters=RiskParameters(
                max_position_size=0.12,
                stop_loss_percentage=-0.025,
                take_profit_percentage=0.05,
                max_daily_loss=-0.025,
                max_drawdown=-0.12,
                risk_per_trade=0.025
            ),
            
            parameter_bounds={
                "ema_fast_period": (8, 20),
                "ema_slow_period": (20, 50),
                "lookback_period": (30, 100)
            },
            
            parameter_types={
                "ema_fast_period": "int",
                "ema_slow_period": "int",
                "lookback_period": "int"
            },
            
            complexity_score=2.5,
            recommended_timeframe="1D",
            minimum_capital=7500.0,
            expected_sharpe=1.0,
            expected_drawdown=-0.09,
            expected_win_rate=0.62,
            required_indicators=["ema"],
            data_requirements=["close_price"],
            version="1.0.0"
        )
        
        self._templates[template.template_id] = template
    
    def _create_triple_moving_average_template(self):
        """Triple Moving Average Strategy"""
        
        template = StrategyTemplate(
            template_id="triple_ma_system",
            name="Triple Moving Average System",
            strategy_type=StrategyType.MOMENTUM,
            description="Advanced trend-following system using three moving averages for signal confirmation. "
                       "Provides stronger signals by requiring alignment of all three MAs.",
            
            trading_rules=[
                TradingRule(
                    rule_id="triple_ma_bullish_alignment",
                    rule_type="entry",
                    indicator="sma",
                    parameters={"fast": 5, "medium": 15, "slow": 30},
                    logic="bullish_alignment",
                    weight=1.0,
                    enabled=True
                ),
                TradingRule(
                    rule_id="triple_ma_bearish_alignment", 
                    rule_type="entry",
                    indicator="sma",
                    parameters={"fast": 5, "medium": 15, "slow": 30},
                    logic="bearish_alignment",
                    weight=1.0,
                    enabled=True
                ),
                TradingRule(
                    rule_id="ma_divergence_exit",
                    rule_type="exit",
                    indicator="sma",
                    parameters={"fast": 5, "medium": 15},
                    logic="divergence",
                    weight=0.8,
                    enabled=True
                )
            ],
            
            default_parameters=StrategyParameters(
                sma_fast_period=5,
                sma_slow_period=30,
                lookback_period=60,
                custom_parameters={"medium_period": 15}
            ),
            
            risk_parameters=RiskParameters(
                max_position_size=0.08,
                stop_loss_percentage=-0.04,
                take_profit_percentage=0.08,
                max_daily_loss=-0.015,
                max_drawdown=-0.08,
                risk_per_trade=0.015
            ),
            
            parameter_bounds={
                "sma_fast_period": (3, 10),
                "medium_period": (10, 25),
                "sma_slow_period": (25, 60)
            },
            
            parameter_types={
                "sma_fast_period": "int",
                "medium_period": "int",
                "sma_slow_period": "int"
            },
            
            complexity_score=4.0,
            recommended_timeframe="4H",
            minimum_capital=12000.0,
            expected_sharpe=1.2,
            expected_drawdown=-0.06,
            expected_win_rate=0.65,
            required_indicators=["sma"],
            data_requirements=["close_price"],
            version="1.0.0"
        )
        
        self._templates[template.template_id] = template
    
    def _create_adaptive_moving_average_template(self):
        """Adaptive Moving Average Strategy"""
        
        template = StrategyTemplate(
            template_id="adaptive_ma_system",
            name="Adaptive Moving Average System",
            strategy_type=StrategyType.MOMENTUM,
            description="Sophisticated moving average system that adapts periods based on market volatility. "
                       "Uses shorter periods in trending markets and longer periods in ranging markets.",
            
            trading_rules=[
                TradingRule(
                    rule_id="adaptive_ma_entry",
                    rule_type="entry",
                    indicator="ema",
                    parameters={"adaptive": True, "base_period": 20},
                    logic="adaptive_crossover",
                    weight=1.0,
                    enabled=True
                ),
                TradingRule(
                    rule_id="volatility_filter",
                    rule_type="filter",
                    indicator="atr",
                    parameters={"period": 14, "threshold": 0.02},
                    logic="volatility_confirmation",
                    weight=0.4,
                    enabled=True
                )
            ],
            
            default_parameters=StrategyParameters(
                ema_fast_period=10,
                ema_slow_period=20,
                lookback_period=100,
                volatility_threshold=0.02,
                custom_parameters={"adaptation_factor": 0.1}
            ),
            
            risk_parameters=RiskParameters(
                max_position_size=0.15,
                stop_loss_percentage=-0.02,
                take_profit_percentage=0.04,
                max_daily_loss=-0.03,
                max_drawdown=-0.15,
                risk_per_trade=0.03
            ),
            
            parameter_bounds={
                "ema_fast_period": (5, 20),
                "ema_slow_period": (15, 40),
                "volatility_threshold": (0.01, 0.05),
                "adaptation_factor": (0.05, 0.2)
            },
            
            parameter_types={
                "ema_fast_period": "int",
                "ema_slow_period": "int",
                "volatility_threshold": "float",
                "adaptation_factor": "float"
            },
            
            complexity_score=6.0,
            recommended_timeframe="1H",
            minimum_capital=15000.0,
            expected_sharpe=1.4,
            expected_drawdown=-0.12,
            expected_win_rate=0.68,
            required_indicators=["ema", "atr"],
            data_requirements=["ohlc_data"],
            version="1.0.0"
        )
        
        self._templates[template.template_id] = template
    
    # ==================== MEAN REVERSION STRATEGIES ====================
    
    def _create_rsi_mean_reversion_template(self):
        """RSI Mean Reversion Strategy"""
        
        template = StrategyTemplate(
            template_id="rsi_mean_reversion",
            name="RSI Mean Reversion Strategy",
            strategy_type=StrategyType.MEAN_REVERSION,
            description="Classic mean reversion strategy using RSI overbought/oversold levels. "
                       "Buys at oversold levels and sells at overbought levels.",
            
            trading_rules=[
                TradingRule(
                    rule_id="rsi_oversold_entry",
                    rule_type="entry",
                    indicator="rsi",
                    parameters={"period": 14, "oversold_level": 30},
                    logic="oversold",
                    weight=1.0,
                    enabled=True
                ),
                TradingRule(
                    rule_id="rsi_overbought_entry",
                    rule_type="entry", 
                    indicator="rsi",
                    parameters={"period": 14, "overbought_level": 70},
                    logic="overbought",
                    weight=1.0,
                    enabled=True
                ),
                TradingRule(
                    rule_id="rsi_neutral_exit",
                    rule_type="exit",
                    indicator="rsi",
                    parameters={"period": 14, "neutral_level": 50},
                    logic="crosses_neutral",
                    weight=0.8,
                    enabled=True
                )
            ],
            
            default_parameters=StrategyParameters(
                rsi_period=14,
                rsi_oversold=30,
                rsi_overbought=70,
                lookback_period=30
            ),
            
            risk_parameters=RiskParameters(
                max_position_size=0.12,
                stop_loss_percentage=-0.035,
                take_profit_percentage=0.025,
                max_daily_loss=-0.02,
                max_drawdown=-0.1,
                risk_per_trade=0.02
            ),
            
            parameter_bounds={
                "rsi_period": (10, 21),
                "rsi_oversold": (20, 35),
                "rsi_overbought": (65, 80),
                "lookback_period": (20, 50)
            },
            
            parameter_types={
                "rsi_period": "int",
                "rsi_oversold": "float",
                "rsi_overbought": "float",
                "lookback_period": "int"
            },
            
            complexity_score=3.0,
            recommended_timeframe="1D",
            minimum_capital=8000.0,
            expected_sharpe=0.9,
            expected_drawdown=-0.08,
            expected_win_rate=0.64,
            required_indicators=["rsi"],
            data_requirements=["close_price"],
            version="1.0.0"
        )
        
        self._templates[template.template_id] = template
    
    def _create_bollinger_bands_template(self):
        """Bollinger Bands Mean Reversion Strategy"""
        
        template = StrategyTemplate(
            template_id="bollinger_bands_reversion", 
            name="Bollinger Bands Mean Reversion",
            strategy_type=StrategyType.MEAN_REVERSION,
            description="Mean reversion strategy using Bollinger Bands. "
                       "Buys when price touches lower band, sells when price touches upper band.",
            
            trading_rules=[
                TradingRule(
                    rule_id="bb_lower_touch_entry",
                    rule_type="entry",
                    indicator="bb",
                    parameters={"period": 20, "std_dev": 2.0},
                    logic="touch_lower",
                    weight=1.0,
                    enabled=True
                ),
                TradingRule(
                    rule_id="bb_upper_touch_entry",
                    rule_type="entry",
                    indicator="bb", 
                    parameters={"period": 20, "std_dev": 2.0},
                    logic="touch_upper",
                    weight=1.0,
                    enabled=True
                ),
                TradingRule(
                    rule_id="bb_middle_exit",
                    rule_type="exit",
                    indicator="bb",
                    parameters={"period": 20},
                    logic="touch_middle",
                    weight=0.7,
                    enabled=True
                ),
                TradingRule(
                    rule_id="bb_squeeze_filter",
                    rule_type="filter",
                    indicator="bb",
                    parameters={"period": 20, "squeeze_threshold": 0.1},
                    logic="squeeze",
                    weight=0.3,
                    enabled=True
                )
            ],
            
            default_parameters=StrategyParameters(
                bb_period=20,
                bb_std_dev=2.0,
                lookback_period=40,
                custom_parameters={"squeeze_threshold": 0.1}
            ),
            
            risk_parameters=RiskParameters(
                max_position_size=0.1,
                stop_loss_percentage=-0.03,
                take_profit_percentage=0.02,
                max_daily_loss=-0.025,
                max_drawdown=-0.09,
                risk_per_trade=0.025
            ),
            
            parameter_bounds={
                "bb_period": (15, 30),
                "bb_std_dev": (1.5, 2.5),
                "squeeze_threshold": (0.05, 0.2)
            },
            
            parameter_types={
                "bb_period": "int",
                "bb_std_dev": "float",
                "squeeze_threshold": "float"
            },
            
            complexity_score=3.5,
            recommended_timeframe="4H",
            minimum_capital=10000.0,
            expected_sharpe=1.1,
            expected_drawdown=-0.07,
            expected_win_rate=0.66,
            required_indicators=["bb"],
            data_requirements=["close_price"],
            version="1.0.0"
        )
        
        self._templates[template.template_id] = template
    
    def _create_mean_reversion_pairs_template(self):
        """Mean Reversion Pairs Trading Strategy"""
        
        template = StrategyTemplate(
            template_id="mean_reversion_pairs",
            name="Mean Reversion Pairs Trading",
            strategy_type=StrategyType.ARBITRAGE,
            description="Statistical arbitrage strategy trading correlated pairs. "
                       "Goes long underperforming asset and short overperforming asset when spread deviates.",
            
            trading_rules=[
                TradingRule(
                    rule_id="spread_oversold_entry",
                    rule_type="entry",
                    indicator="spread_zscore",
                    parameters={"lookback": 60, "threshold": -2.0},
                    logic="below_threshold",
                    weight=1.0,
                    enabled=True
                ),
                TradingRule(
                    rule_id="spread_overbought_entry",
                    rule_type="entry",
                    indicator="spread_zscore",
                    parameters={"lookback": 60, "threshold": 2.0},
                    logic="above_threshold",
                    weight=1.0,
                    enabled=True
                ),
                TradingRule(
                    rule_id="spread_mean_exit",
                    rule_type="exit",
                    indicator="spread_zscore",
                    parameters={"threshold": 0.0},
                    logic="crosses_zero",
                    weight=1.0,
                    enabled=True
                )
            ],
            
            default_parameters=StrategyParameters(
                lookback_period=60,
                custom_parameters={
                    "correlation_threshold": 0.7,
                    "cointegration_threshold": 0.05,
                    "spread_threshold": 2.0,
                    "half_life_max": 30
                }
            ),
            
            risk_parameters=RiskParameters(
                max_position_size=0.2,  # Higher for pairs trading
                stop_loss_percentage=-0.05,
                take_profit_percentage=0.02,
                max_daily_loss=-0.03,
                max_drawdown=-0.12,
                risk_per_trade=0.03
            ),
            
            parameter_bounds={
                "lookback_period": (40, 120),
                "correlation_threshold": (0.6, 0.9),
                "spread_threshold": (1.5, 3.0)
            },
            
            parameter_types={
                "lookback_period": "int",
                "correlation_threshold": "float",
                "spread_threshold": "float"
            },
            
            complexity_score=7.0,
            recommended_timeframe="1H",
            minimum_capital=25000.0,
            expected_sharpe=1.3,
            expected_drawdown=-0.1,
            expected_win_rate=0.72,
            required_indicators=["correlation", "cointegration", "spread"],
            data_requirements=["close_price_pairs"],
            version="1.0.0"
        )
        
        self._templates[template.template_id] = template
    
    def _create_rsi_bollinger_combo_template(self):
        """RSI + Bollinger Bands Combination Strategy"""
        
        template = StrategyTemplate(
            template_id="rsi_bollinger_combo",
            name="RSI Bollinger Bands Combo",
            strategy_type=StrategyType.MEAN_REVERSION,
            description="Enhanced mean reversion combining RSI and Bollinger Bands for stronger signals. "
                       "Requires both indicators to confirm oversold/overbought conditions.",
            
            trading_rules=[
                TradingRule(
                    rule_id="rsi_bb_oversold_combo",
                    rule_type="entry",
                    indicator="combo",
                    parameters={"rsi_oversold": 30, "bb_lower_touch": True},
                    logic="both_oversold",
                    weight=1.0,
                    enabled=True
                ),
                TradingRule(
                    rule_id="rsi_bb_overbought_combo",
                    rule_type="entry",
                    indicator="combo", 
                    parameters={"rsi_overbought": 70, "bb_upper_touch": True},
                    logic="both_overbought",
                    weight=1.0,
                    enabled=True
                ),
                TradingRule(
                    rule_id="rsi_neutral_or_bb_middle",
                    rule_type="exit",
                    indicator="combo",
                    parameters={"rsi_neutral": 50, "bb_middle": True},
                    logic="either_neutral",
                    weight=0.8,
                    enabled=True
                )
            ],
            
            default_parameters=StrategyParameters(
                rsi_period=14,
                rsi_oversold=30,
                rsi_overbought=70,
                bb_period=20,
                bb_std_dev=2.0,
                lookback_period=40
            ),
            
            risk_parameters=RiskParameters(
                max_position_size=0.08,
                stop_loss_percentage=-0.04,
                take_profit_percentage=0.03,
                max_daily_loss=-0.02,
                max_drawdown=-0.08,
                risk_per_trade=0.02
            ),
            
            parameter_bounds={
                "rsi_period": (10, 21),
                "rsi_oversold": (25, 35),
                "rsi_overbought": (65, 75),
                "bb_period": (15, 25),
                "bb_std_dev": (1.8, 2.2)
            },
            
            parameter_types={
                "rsi_period": "int",
                "rsi_oversold": "float",
                "rsi_overbought": "float",
                "bb_period": "int",
                "bb_std_dev": "float"
            },
            
            complexity_score=4.5,
            recommended_timeframe="1D",
            minimum_capital=12000.0,
            expected_sharpe=1.25,
            expected_drawdown=-0.06,
            expected_win_rate=0.71,
            required_indicators=["rsi", "bb"],
            data_requirements=["close_price"],
            version="1.0.0"
        )
        
        self._templates[template.template_id] = template
    
    # ==================== MOMENTUM STRATEGIES ====================
    
    def _create_macd_momentum_template(self):
        """MACD Momentum Strategy"""
        
        template = StrategyTemplate(
            template_id="macd_momentum_system",
            name="MACD Momentum System",
            strategy_type=StrategyType.MOMENTUM,
            description="Momentum strategy using MACD crossovers and histogram analysis. "
                       "Enters on MACD line crossovers and histogram confirmation.",
            
            trading_rules=[
                TradingRule(
                    rule_id="macd_bullish_crossover",
                    rule_type="entry",
                    indicator="macd",
                    parameters={"fast": 12, "slow": 26, "signal": 9},
                    logic="bullish_crossover",
                    weight=1.0,
                    enabled=True
                ),
                TradingRule(
                    rule_id="macd_bearish_crossover", 
                    rule_type="entry",
                    indicator="macd",
                    parameters={"fast": 12, "slow": 26, "signal": 9},
                    logic="bearish_crossover",
                    weight=1.0,
                    enabled=True
                ),
                TradingRule(
                    rule_id="macd_histogram_divergence",
                    rule_type="exit",
                    indicator="macd",
                    parameters={"divergence_periods": 5},
                    logic="histogram_divergence",
                    weight=0.7,
                    enabled=True
                ),
                TradingRule(
                    rule_id="macd_zero_line_filter",
                    rule_type="filter", 
                    indicator="macd",
                    parameters={},
                    logic="above_zero_line",
                    weight=0.3,
                    enabled=True
                )
            ],
            
            default_parameters=StrategyParameters(
                macd_fast=12,
                macd_slow=26,
                macd_signal=9,
                lookback_period=50,
                custom_parameters={"divergence_periods": 5}
            ),
            
            risk_parameters=RiskParameters(
                max_position_size=0.12,
                stop_loss_percentage=-0.03,
                take_profit_percentage=0.06,
                max_daily_loss=-0.025,
                max_drawdown=-0.1,
                risk_per_trade=0.025
            ),
            
            parameter_bounds={
                "macd_fast": (8, 16),
                "macd_slow": (20, 35),
                "macd_signal": (7, 12),
                "divergence_periods": (3, 8)
            },
            
            parameter_types={
                "macd_fast": "int",
                "macd_slow": "int", 
                "macd_signal": "int",
                "divergence_periods": "int"
            },
            
            complexity_score=4.0,
            recommended_timeframe="4H",
            minimum_capital=10000.0,
            expected_sharpe=1.15,
            expected_drawdown=-0.08,
            expected_win_rate=0.63,
            required_indicators=["macd"],
            data_requirements=["close_price"],
            version="1.0.0"
        )
        
        self._templates[template.template_id] = template
    
    def _create_breakout_strategy_template(self):
        """Breakout Trading Strategy"""
        
        template = StrategyTemplate(
            template_id="volatility_breakout",
            name="Volatility Breakout Strategy", 
            strategy_type=StrategyType.BREAKOUT,
            description="Momentum strategy that trades breakouts from consolidation periods. "
                       "Enters when price breaks above/below volatility-adjusted levels with volume confirmation.",
            
            trading_rules=[
                TradingRule(
                    rule_id="upside_breakout_entry",
                    rule_type="entry",
                    indicator="breakout",
                    parameters={"lookback": 20, "volatility_multiplier": 2.0},
                    logic="upside_breakout",
                    weight=1.0,
                    enabled=True
                ),
                TradingRule(
                    rule_id="downside_breakout_entry",
                    rule_type="entry",
                    indicator="breakout",
                    parameters={"lookback": 20, "volatility_multiplier": 2.0},
                    logic="downside_breakout", 
                    weight=1.0,
                    enabled=True
                ),
                TradingRule(
                    rule_id="volume_confirmation",
                    rule_type="filter",
                    indicator="volume",
                    parameters={"volume_multiplier": 1.5, "lookback": 10},
                    logic="above_average",
                    weight=0.4,
                    enabled=True
                ),
                TradingRule(
                    rule_id="false_breakout_exit",
                    rule_type="exit",
                    indicator="breakout",
                    parameters={"retracement_threshold": 0.5},
                    logic="false_breakout",
                    weight=0.8,
                    enabled=True
                )
            ],
            
            default_parameters=StrategyParameters(
                lookback_period=20,
                volatility_threshold=0.02,
                custom_parameters={
                    "volatility_multiplier": 2.0,
                    "volume_multiplier": 1.5,
                    "min_consolidation_days": 10
                }
            ),
            
            risk_parameters=RiskParameters(
                max_position_size=0.15,
                stop_loss_percentage=-0.02,
                take_profit_percentage=0.08,
                max_daily_loss=-0.03,
                max_drawdown=-0.12,
                risk_per_trade=0.03
            ),
            
            parameter_bounds={
                "lookback_period": (15, 30),
                "volatility_multiplier": (1.5, 3.0),
                "volume_multiplier": (1.2, 2.0),
                "min_consolidation_days": (5, 20)
            },
            
            parameter_types={
                "lookback_period": "int",
                "volatility_multiplier": "float",
                "volume_multiplier": "float", 
                "min_consolidation_days": "int"
            },
            
            complexity_score=5.5,
            recommended_timeframe="1D",
            minimum_capital=15000.0,
            expected_sharpe=1.3,
            expected_drawdown=-0.1,
            expected_win_rate=0.58,
            required_indicators=["atr", "volume", "donchian"],
            data_requirements=["ohlcv_data"],
            version="1.0.0"
        )
        
        self._templates[template.template_id] = template
    
    def _create_trend_following_template(self):
        """Comprehensive Trend Following Strategy"""
        
        template = StrategyTemplate(
            template_id="comprehensive_trend_following",
            name="Comprehensive Trend Following",
            strategy_type=StrategyType.MOMENTUM,
            description="Multi-timeframe trend following system combining multiple trend indicators. "
                       "Uses ADX for trend strength, moving averages for direction, and momentum for timing.",
            
            trading_rules=[
                TradingRule(
                    rule_id="adx_trend_strength",
                    rule_type="filter",
                    indicator="adx",
                    parameters={"period": 14, "strength_threshold": 25},
                    logic="strong_trend",
                    weight=0.4,
                    enabled=True
                ),
                TradingRule(
                    rule_id="ma_trend_direction",
                    rule_type="entry",
                    indicator="ema",
                    parameters={"fast": 21, "slow": 55},
                    logic="trend_alignment",
                    weight=0.8,
                    enabled=True
                ),
                TradingRule(
                    rule_id="momentum_confirmation",
                    rule_type="filter",
                    indicator="roc",
                    parameters={"period": 10, "threshold": 0.02},
                    logic="momentum_confirmation",
                    weight=0.3,
                    enabled=True
                ),
                TradingRule(
                    rule_id="trend_exhaustion_exit",
                    rule_type="exit",
                    indicator="adx",
                    parameters={"exhaustion_threshold": 40},
                    logic="trend_exhaustion",
                    weight=0.6,
                    enabled=True
                )
            ],
            
            default_parameters=StrategyParameters(
                ema_fast_period=21,
                ema_slow_period=55,
                lookback_period=80,
                custom_parameters={
                    "adx_period": 14,
                    "adx_threshold": 25,
                    "roc_period": 10,
                    "momentum_threshold": 0.02
                }
            ),
            
            risk_parameters=RiskParameters(
                max_position_size=0.1,
                stop_loss_percentage=-0.025,
                take_profit_percentage=0.1,
                max_daily_loss=-0.02,
                max_drawdown=-0.08,
                risk_per_trade=0.02
            ),
            
            parameter_bounds={
                "ema_fast_period": (15, 30),
                "ema_slow_period": (45, 70),
                "adx_period": (10, 20),
                "adx_threshold": (20, 35),
                "roc_period": (5, 15)
            },
            
            parameter_types={
                "ema_fast_period": "int",
                "ema_slow_period": "int",
                "adx_period": "int",
                "adx_threshold": "float",
                "roc_period": "int"
            },
            
            complexity_score=6.5,
            recommended_timeframe="4H",
            minimum_capital=18000.0,
            expected_sharpe=1.4,
            expected_drawdown=-0.06,
            expected_win_rate=0.61,
            required_indicators=["ema", "adx", "roc"],
            data_requirements=["ohlc_data"],
            version="1.0.0"
        )
        
        self._templates[template.template_id] = template
    
    def _create_momentum_oscillator_template(self):
        """Momentum Oscillator Strategy"""
        
        template = StrategyTemplate(
            template_id="momentum_oscillator_system",
            name="Momentum Oscillator System",
            strategy_type=StrategyType.MOMENTUM,
            description="Multi-oscillator momentum system combining RSI, Stochastic, and Williams %R. "
                       "Uses oscillator alignment for high-probability momentum entries.",
            
            trading_rules=[
                TradingRule(
                    rule_id="triple_oscillator_bullish",
                    rule_type="entry",
                    indicator="oscillator_combo",
                    parameters={"rsi_threshold": 60, "stoch_threshold": 60, "williams_threshold": -40},
                    logic="bullish_alignment",
                    weight=1.0,
                    enabled=True
                ),
                TradingRule(
                    rule_id="triple_oscillator_bearish",
                    rule_type="entry",
                    indicator="oscillator_combo",
                    parameters={"rsi_threshold": 40, "stoch_threshold": 40, "williams_threshold": -60},
                    logic="bearish_alignment",
                    weight=1.0,
                    enabled=True
                ),
                TradingRule(
                    rule_id="oscillator_divergence",
                    rule_type="exit",
                    indicator="oscillator_combo",
                    parameters={"divergence_periods": 5},
                    logic="momentum_divergence",
                    weight=0.7,
                    enabled=True
                )
            ],
            
            default_parameters=StrategyParameters(
                rsi_period=14,
                lookback_period=50,
                custom_parameters={
                    "stoch_k_period": 14,
                    "stoch_d_period": 3,
                    "williams_period": 14,
                    "bullish_threshold": 60,
                    "bearish_threshold": 40
                }
            ),
            
            risk_parameters=RiskParameters(
                max_position_size=0.12,
                stop_loss_percentage=-0.035,
                take_profit_percentage=0.07,
                max_daily_loss=-0.025,
                max_drawdown=-0.09,
                risk_per_trade=0.025
            ),
            
            parameter_bounds={
                "rsi_period": (10, 21),
                "stoch_k_period": (10, 20),
                "stoch_d_period": (3, 7),
                "williams_period": (10, 20),
                "bullish_threshold": (55, 70),
                "bearish_threshold": (30, 45)
            },
            
            parameter_types={
                "rsi_period": "int",
                "stoch_k_period": "int",
                "stoch_d_period": "int",
                "williams_period": "int",
                "bullish_threshold": "float",
                "bearish_threshold": "float"
            },
            
            complexity_score=5.0,
            recommended_timeframe="1H",
            minimum_capital=14000.0,
            expected_sharpe=1.2,
            expected_drawdown=-0.07,
            expected_win_rate=0.65,
            required_indicators=["rsi", "stochastic", "williams_r"],
            data_requirements=["ohlc_data"],
            version="1.0.0"
        )
        
        self._templates[template.template_id] = template
    
    # ==================== COMPOSITE STRATEGIES ====================
    
    def _create_balanced_composite_template(self):
        """Balanced Multi-Strategy Composite"""
        
        template = StrategyTemplate(
            template_id="balanced_composite_strategy",
            name="Balanced Multi-Strategy System",
            strategy_type=StrategyType.MULTI_INDICATOR,
            description="Balanced approach combining trend following and mean reversion. "
                       "Adapts to market conditions by weighting strategies based on market regime.",
            
            trading_rules=[
                TradingRule(
                    rule_id="trend_component",
                    rule_type="entry",
                    indicator="composite",
                    parameters={"ma_weight": 0.4, "macd_weight": 0.3, "adx_weight": 0.3},
                    logic="trend_consensus",
                    weight=0.6,
                    enabled=True
                ),
                TradingRule(
                    rule_id="mean_reversion_component",
                    rule_type="entry",
                    indicator="composite", 
                    parameters={"rsi_weight": 0.5, "bb_weight": 0.5},
                    logic="mean_reversion_consensus",
                    weight=0.4,
                    enabled=True
                ),
                TradingRule(
                    rule_id="market_regime_filter",
                    rule_type="filter",
                    indicator="volatility",
                    parameters={"volatility_threshold": 0.02, "trend_threshold": 0.15},
                    logic="regime_detection",
                    weight=0.3,
                    enabled=True
                )
            ],
            
            default_parameters=StrategyParameters(
                sma_fast_period=12,
                sma_slow_period=26,
                rsi_period=14,
                bb_period=20,
                bb_std_dev=2.0,
                macd_fast=12,
                macd_slow=26,
                macd_signal=9,
                lookback_period=60,
                custom_parameters={
                    "trend_weight": 0.6,
                    "mean_reversion_weight": 0.4,
                    "regime_adaptation": True
                }
            ),
            
            risk_parameters=RiskParameters(
                max_position_size=0.1,
                stop_loss_percentage=-0.03,
                take_profit_percentage=0.05,
                max_daily_loss=-0.02,
                max_drawdown=-0.08,
                risk_per_trade=0.02
            ),
            
            parameter_bounds={
                "trend_weight": (0.4, 0.8),
                "mean_reversion_weight": (0.2, 0.6),
                "sma_fast_period": (10, 15),
                "sma_slow_period": (20, 35),
                "rsi_period": (12, 18),
                "bb_period": (15, 25)
            },
            
            parameter_types={
                "trend_weight": "float",
                "mean_reversion_weight": "float",
                "sma_fast_period": "int",
                "sma_slow_period": "int",
                "rsi_period": "int",
                "bb_period": "int"
            },
            
            complexity_score=7.5,
            recommended_timeframe="4H",
            minimum_capital=20000.0,
            expected_sharpe=1.5,
            expected_drawdown=-0.06,
            expected_win_rate=0.68,
            required_indicators=["sma", "rsi", "bb", "macd", "adx"],
            data_requirements=["ohlcv_data"],
            version="1.0.0"
        )
        
        self._templates[template.template_id] = template
    
    def _create_aggressive_growth_template(self):
        """Aggressive Growth Strategy"""
        
        template = StrategyTemplate(
            template_id="aggressive_growth_momentum",
            name="Aggressive Growth Momentum",
            strategy_type=StrategyType.MOMENTUM,
            description="High-risk, high-reward momentum strategy for aggressive growth. "
                       "Uses leverage-friendly position sizing and momentum confirmation across multiple timeframes.",
            
            trading_rules=[
                TradingRule(
                    rule_id="strong_momentum_entry",
                    rule_type="entry",
                    indicator="momentum_strength",
                    parameters={"roc_threshold": 0.05, "volume_confirmation": True},
                    logic="strong_momentum",
                    weight=1.0,
                    enabled=True
                ),
                TradingRule(
                    rule_id="breakout_continuation",
                    rule_type="entry",
                    indicator="breakout",
                    parameters={"volatility_expansion": True, "volume_spike": True},
                    logic="continuation_breakout",
                    weight=0.8,
                    enabled=True
                ),
                TradingRule(
                    rule_id="momentum_exhaustion_exit",
                    rule_type="exit",
                    indicator="momentum_strength",
                    parameters={"exhaustion_threshold": 0.8},
                    logic="momentum_exhaustion",
                    weight=0.9,
                    enabled=True
                )
            ],
            
            default_parameters=StrategyParameters(
                lookback_period=30,
                volatility_threshold=0.03,
                momentum_threshold=0.05,
                custom_parameters={
                    "leverage_factor": 1.5,
                    "volatility_expansion_threshold": 1.5,
                    "volume_spike_multiplier": 2.0,
                    "momentum_persistence_days": 3
                }
            ),
            
            risk_parameters=RiskParameters(
                max_position_size=0.2,  # Higher risk tolerance
                stop_loss_percentage=-0.05,
                take_profit_percentage=0.15,
                max_daily_loss=-0.05,
                max_drawdown=-0.2,
                risk_per_trade=0.05
            ),
            
            parameter_bounds={
                "momentum_threshold": (0.03, 0.08),
                "volatility_expansion_threshold": (1.3, 2.0),
                "volume_spike_multiplier": (1.5, 3.0),
                "leverage_factor": (1.0, 2.0),
                "momentum_persistence_days": (2, 7)
            },
            
            parameter_types={
                "momentum_threshold": "float",
                "volatility_expansion_threshold": "float",
                "volume_spike_multiplier": "float",
                "leverage_factor": "float",
                "momentum_persistence_days": "int"
            },
            
            complexity_score=8.0,
            recommended_timeframe="1H",
            minimum_capital=30000.0,
            expected_sharpe=1.8,
            expected_drawdown=-0.15,
            expected_win_rate=0.55,
            required_indicators=["roc", "volume", "atr", "momentum"],
            data_requirements=["ohlcv_data", "intraday_data"],
            version="1.0.0"
        )
        
        self._templates[template.template_id] = template
    
    def _create_conservative_income_template(self):
        """Conservative Income Strategy"""
        
        template = StrategyTemplate(
            template_id="conservative_income_strategy",
            name="Conservative Income Strategy",
            strategy_type=StrategyType.MEAN_REVERSION,
            description="Low-risk income-focused strategy emphasizing capital preservation. "
                       "Uses tight risk controls and high-probability setups with modest profit targets.",
            
            trading_rules=[
                TradingRule(
                    rule_id="high_probability_mean_reversion",
                    rule_type="entry",
                    indicator="probability_combo",
                    parameters={"min_probability": 0.7, "max_risk": 0.01},
                    logic="high_probability_setup",
                    weight=1.0,
                    enabled=True
                ),
                TradingRule(
                    rule_id="dividend_yield_filter",
                    rule_type="filter",
                    indicator="fundamental",
                    parameters={"min_dividend_yield": 0.02, "payout_ratio_max": 0.8},
                    logic="income_quality",
                    weight=0.4,
                    enabled=True
                ),
                TradingRule(
                    rule_id="volatility_filter",
                    rule_type="filter",
                    indicator="volatility",
                    parameters={"max_volatility": 0.15, "stability_score": 0.7},
                    logic="low_volatility",
                    weight=0.3,
                    enabled=True
                )
            ],
            
            default_parameters=StrategyParameters(
                rsi_period=21,
                bb_period=20,
                bb_std_dev=1.5,  # Tighter bands
                lookback_period=100,
                custom_parameters={
                    "min_probability_threshold": 0.7,
                    "stability_requirement": 0.7,
                    "income_focus": True,
                    "capital_preservation": True
                }
            ),
            
            risk_parameters=RiskParameters(
                max_position_size=0.05,  # Very conservative
                stop_loss_percentage=-0.015,  # Tight stops
                take_profit_percentage=0.02,   # Modest targets
                max_daily_loss=-0.01,
                max_drawdown=-0.05,
                risk_per_trade=0.01,
                max_correlation=0.5  # Lower correlation limit
            ),
            
            parameter_bounds={
                "rsi_period": (18, 25),
                "bb_std_dev": (1.2, 1.8),
                "min_probability_threshold": (0.65, 0.8),
                "stability_requirement": (0.6, 0.8)
            },
            
            parameter_types={
                "rsi_period": "int",
                "bb_std_dev": "float",
                "min_probability_threshold": "float",
                "stability_requirement": "float"
            },
            
            complexity_score=4.0,
            recommended_timeframe="1D",
            minimum_capital=50000.0,  # Higher minimum for conservative approach
            expected_sharpe=1.0,
            expected_drawdown=-0.03,
            expected_win_rate=0.75,
            required_indicators=["rsi", "bb", "volatility", "fundamentals"],
            data_requirements=["ohlc_data", "fundamental_data"],
            version="1.0.0"
        )
        
        self._templates[template.template_id] = template
    
    def _create_market_neutral_template(self):
        """Market Neutral Strategy"""
        
        template = StrategyTemplate(
            template_id="market_neutral_pairs",
            name="Market Neutral Pairs Strategy",
            strategy_type=StrategyType.ARBITRAGE,
            description="Market neutral strategy using long/short pairs to minimize market exposure. "
                       "Seeks to profit from relative price movements while hedging market risk.",
            
            trading_rules=[
                TradingRule(
                    rule_id="pairs_identification",
                    rule_type="filter",
                    indicator="statistical_relationship",
                    parameters={"correlation_min": 0.7, "cointegration_pvalue": 0.05},
                    logic="valid_pair",
                    weight=0.5,
                    enabled=True
                ),
                TradingRule(
                    rule_id="spread_entry_long_short",
                    rule_type="entry",
                    indicator="spread_analysis",
                    parameters={"z_score_threshold": 2.0, "half_life_max": 20},
                    logic="spread_divergence",
                    weight=1.0,
                    enabled=True
                ),
                TradingRule(
                    rule_id="beta_neutrality_check",
                    rule_type="filter",
                    indicator="portfolio_beta",
                    parameters={"max_beta_deviation": 0.1},
                    logic="market_neutral",
                    weight=0.4,
                    enabled=True
                )
            ],
            
            default_parameters=StrategyParameters(
                lookback_period=60,
                custom_parameters={
                    "correlation_threshold": 0.7,
                    "cointegration_threshold": 0.05,
                    "z_score_entry": 2.0,
                    "z_score_exit": 0.5,
                    "max_pairs": 10,
                    "beta_target": 0.0,
                    "rebalance_frequency": 5
                }
            ),
            
            risk_parameters=RiskParameters(
                max_position_size=0.15,  # Per side of pair
                stop_loss_percentage=-0.03,
                take_profit_percentage=0.015,
                max_daily_loss=-0.02,
                max_drawdown=-0.08,
                risk_per_trade=0.02,
                max_correlation=0.8  # Allow higher correlation for pairs
            ),
            
            parameter_bounds={
                "correlation_threshold": (0.6, 0.85),
                "z_score_entry": (1.5, 2.5),
                "z_score_exit": (0.2, 0.8),
                "max_pairs": (5, 20),
                "rebalance_frequency": (3, 10)
            },
            
            parameter_types={
                "correlation_threshold": "float",
                "z_score_entry": "float",
                "z_score_exit": "float",
                "max_pairs": "int",
                "rebalance_frequency": "int"
            },
            
            complexity_score=9.0,
            recommended_timeframe="1D",
            minimum_capital=100000.0,  # Requires significant capital for pairs
            expected_sharpe=1.6,
            expected_drawdown=-0.05,
            expected_win_rate=0.68,
            required_indicators=["correlation", "cointegration", "beta", "spread"],
            data_requirements=["multiple_assets", "market_data"],
            version="1.0.0"
        )
        
        self._templates[template.template_id] = template
    
    # ==================== ADVANCED STRATEGIES ====================
    
    def _create_volatility_breakout_template(self):
        """Advanced Volatility Breakout Strategy"""
        
        template = StrategyTemplate(
            template_id="advanced_volatility_breakout",
            name="Advanced Volatility Breakout",
            strategy_type=StrategyType.BREAKOUT,
            description="Sophisticated volatility-based breakout system using volatility regime detection. "
                       "Adapts breakout thresholds based on current volatility environment.",
            
            trading_rules=[
                TradingRule(
                    rule_id="volatility_regime_detection",
                    rule_type="filter",
                    indicator="volatility_regime",
                    parameters={"lookback": 60, "regime_threshold": 0.02},
                    logic="regime_classification",
                    weight=0.4,
                    enabled=True
                ),
                TradingRule(
                    rule_id="adaptive_breakout_entry",
                    rule_type="entry", 
                    indicator="adaptive_breakout",
                    parameters={"base_lookback": 20, "volatility_adjustment": True},
                    logic="volatility_adjusted_breakout",
                    weight=1.0,
                    enabled=True
                ),
                TradingRule(
                    rule_id="volatility_stop_loss",
                    rule_type="exit",
                    indicator="volatility_stop",
                    parameters={"atr_multiplier": 2.5, "dynamic_adjustment": True},
                    logic="volatility_based_stop",
                    weight=0.8,
                    enabled=True
                )
            ],
            
            default_parameters=StrategyParameters(
                lookback_period=20,
                volatility_threshold=0.02,
                custom_parameters={
                    "volatility_lookback": 60,
                    "regime_threshold": 0.02,
                    "low_vol_multiplier": 1.5,
                    "high_vol_multiplier": 2.5,
                    "atr_period": 14,
                    "atr_multiplier": 2.5
                }
            ),
            
            risk_parameters=RiskParameters(
                max_position_size=0.12,
                stop_loss_percentage=-0.04,  # Will be overridden by volatility stops
                take_profit_percentage=0.08,
                max_daily_loss=-0.03,
                max_drawdown=-0.12,
                risk_per_trade=0.03
            ),
            
            parameter_bounds={
                "volatility_lookback": (40, 100),
                "regime_threshold": (0.015, 0.03),
                "low_vol_multiplier": (1.2, 2.0),
                "high_vol_multiplier": (2.0, 3.5),
                "atr_period": (10, 20),
                "atr_multiplier": (2.0, 4.0)
            },
            
            parameter_types={
                "volatility_lookback": "int",
                "regime_threshold": "float",
                "low_vol_multiplier": "float",
                "high_vol_multiplier": "float",
                "atr_period": "int",
                "atr_multiplier": "float"
            },
            
            complexity_score=8.5,
            recommended_timeframe="4H",
            minimum_capital=25000.0,
            expected_sharpe=1.7,
            expected_drawdown=-0.09,
            expected_win_rate=0.58,
            required_indicators=["atr", "volatility", "donchian", "regime"],
            data_requirements=["ohlc_data", "volatility_data"],
            version="1.0.0"
        )
        
        self._templates[template.template_id] = template
    
    def _create_statistical_arbitrage_template(self):
        """Statistical Arbitrage Strategy"""
        
        template = StrategyTemplate(
            template_id="statistical_arbitrage_advanced",
            name="Statistical Arbitrage System", 
            strategy_type=StrategyType.ARBITRAGE,
            description="Advanced statistical arbitrage using machine learning for pattern recognition. "
                       "Identifies temporary price inefficiencies across correlated instruments.",
            
            trading_rules=[
                TradingRule(
                    rule_id="cointegration_identification",
                    rule_type="filter",
                    indicator="cointegration_test",
                    parameters={"johansen_test": True, "adf_test": True, "confidence": 0.95},
                    logic="statistically_significant",
                    weight=0.5,
                    enabled=True
                ),
                TradingRule(
                    rule_id="spread_mean_reversion_entry",
                    rule_type="entry",
                    indicator="spread_model",
                    parameters={"model_type": "kalman_filter", "confidence_threshold": 0.8},
                    logic="mean_reversion_signal",
                    weight=1.0,
                    enabled=True
                ),
                TradingRule(
                    rule_id="statistical_stop_loss",
                    rule_type="exit",
                    indicator="statistical_model",
                    parameters={"model_confidence_threshold": 0.3},
                    logic="model_breakdown",
                    weight=0.9,
                    enabled=True
                )
            ],
            
            default_parameters=StrategyParameters(
                lookback_period=252,  # One year of daily data
                custom_parameters={
                    "cointegration_lookback": 252,
                    "kalman_filter_params": {"state_variance": 0.01, "obs_variance": 0.1},
                    "confidence_threshold": 0.8,
                    "max_spread_age": 30,
                    "min_half_life": 5,
                    "max_half_life": 50
                }
            ),
            
            risk_parameters=RiskParameters(
                max_position_size=0.1,
                stop_loss_percentage=-0.02,
                take_profit_percentage=0.01,
                max_daily_loss=-0.015,
                max_drawdown=-0.06,
                risk_per_trade=0.015
            ),
            
            parameter_bounds={
                "cointegration_lookback": (150, 400),
                "confidence_threshold": (0.7, 0.9),
                "min_half_life": (3, 10),
                "max_half_life": (30, 100),
                "max_spread_age": (20, 60)
            },
            
            parameter_types={
                "cointegration_lookback": "int",
                "confidence_threshold": "float",
                "min_half_life": "int",
                "max_half_life": "int",
                "max_spread_age": "int"
            },
            
            complexity_score=9.5,
            recommended_timeframe="1D",
            minimum_capital=200000.0,  # Requires substantial capital
            expected_sharpe=2.0,
            expected_drawdown=-0.04,
            expected_win_rate=0.72,
            required_indicators=["cointegration", "kalman_filter", "statistical_tests"],
            data_requirements=["multiple_assets", "high_quality_data", "fundamental_data"],
            version="1.0.0"
        )
        
        self._templates[template.template_id] = template
    
    def _create_regime_aware_template(self):
        """Market Regime Aware Strategy"""
        
        template = StrategyTemplate(
            template_id="regime_aware_adaptive",
            name="Market Regime Aware Strategy",
            strategy_type=StrategyType.MULTI_INDICATOR,
            description="Adaptive strategy that switches between different approaches based on market regime. "
                       "Uses machine learning to identify bull, bear, and sideways market conditions.",
            
            trading_rules=[
                TradingRule(
                    rule_id="regime_classification",
                    rule_type="filter",
                    indicator="regime_detector",
                    parameters={"lookback": 60, "confidence_threshold": 0.7},
                    logic="regime_identification",
                    weight=0.6,
                    enabled=True
                ),
                TradingRule(
                    rule_id="bull_market_strategy",
                    rule_type="entry",
                    indicator="trend_following",
                    parameters={"regime": "bull", "aggressiveness": 0.8},
                    logic="bull_market_signals",
                    weight=1.0,
                    enabled=True
                ),
                TradingRule(
                    rule_id="bear_market_strategy",
                    rule_type="entry",
                    indicator="mean_reversion",
                    parameters={"regime": "bear", "defensiveness": 0.8}, 
                    logic="bear_market_signals",
                    weight=1.0,
                    enabled=True
                ),
                TradingRule(
                    rule_id="sideways_market_strategy",
                    rule_type="entry",
                    indicator="range_trading",
                    parameters={"regime": "sideways", "range_detection": True},
                    logic="sideways_market_signals",
                    weight=1.0,
                    enabled=True
                )
            ],
            
            default_parameters=StrategyParameters(
                lookback_period=60,
                custom_parameters={
                    "regime_lookback": 60,
                    "bull_trend_threshold": 0.1,
                    "bear_trend_threshold": -0.1,
                    "sideways_volatility_threshold": 0.15,
                    "regime_confidence_threshold": 0.7,
                    "adaptation_speed": 0.1
                }
            ),
            
            risk_parameters=RiskParameters(
                max_position_size=0.15,  # Adaptive based on regime
                stop_loss_percentage=-0.03,
                take_profit_percentage=0.05,
                max_daily_loss=-0.025,
                max_drawdown=-0.1,
                risk_per_trade=0.025
            ),
            
            parameter_bounds={
                "regime_lookback": (40, 100),
                "bull_trend_threshold": (0.05, 0.2),
                "bear_trend_threshold": (-0.2, -0.05),
                "sideways_volatility_threshold": (0.1, 0.25),
                "regime_confidence_threshold": (0.6, 0.85)
            },
            
            parameter_types={
                "regime_lookback": "int",
                "bull_trend_threshold": "float",
                "bear_trend_threshold": "float", 
                "sideways_volatility_threshold": "float",
                "regime_confidence_threshold": "float"
            },
            
            complexity_score=9.0,
            recommended_timeframe="1D",
            minimum_capital=40000.0,
            expected_sharpe=1.8,
            expected_drawdown=-0.08,
            expected_win_rate=0.66,
            required_indicators=["regime_detector", "trend_indicators", "mean_reversion_indicators"],
            data_requirements=["ohlcv_data", "macro_indicators"],
            version="1.0.0"
        )
        
        self._templates[template.template_id] = template
    
    # ==================== TEMPLATE MANAGEMENT METHODS ====================
    
    def get_template(self, template_id: str) -> Optional[StrategyTemplate]:
        """Get strategy template by ID"""
        return self._templates.get(template_id)
    
    def list_templates(
        self,
        strategy_type: Optional[StrategyType] = None,
        complexity_max: Optional[float] = None,
        min_capital_max: Optional[float] = None
    ) -> List[StrategyTemplate]:
        """List available strategy templates with filtering"""
        
        templates = list(self._templates.values())
        
        # Apply filters
        if strategy_type:
            templates = [t for t in templates if t.strategy_type == strategy_type]
        
        if complexity_max:
            templates = [t for t in templates if t.complexity_score <= complexity_max]
        
        if min_capital_max:
            templates = [t for t in templates if t.minimum_capital <= min_capital_max]
        
        # Sort by complexity (simple to advanced)
        templates.sort(key=lambda x: x.complexity_score)
        
        return templates
    
    def create_strategy_from_template(
        self,
        template_id: str,
        strategy_name: str,
        symbols: List[str],
        customizations: Dict[str, Any] = None,
        created_by: str = "system"
    ) -> Optional[StrategyDefinition]:
        """Create strategy instance from template"""
        
        template = self.get_template(template_id)
        if not template:
            logger.error(f"Template not found: {template_id}")
            return None
        
        try:
            # Generate unique strategy ID
            strategy_id = f"{template_id}_{int(datetime.now().timestamp())}"
            
            # Apply customizations to parameters
            parameters = template.default_parameters.copy()
            if customizations:
                # Update parameters with customizations
                param_dict = parameters.dict()
                param_dict.update(customizations.get('parameters', {}))
                parameters = StrategyParameters(**param_dict)
            
            # Apply customizations to risk parameters
            risk_parameters = template.risk_parameters.copy()
            if customizations and 'risk_parameters' in customizations:
                risk_dict = risk_parameters.dict()
                risk_dict.update(customizations['risk_parameters'])
                risk_parameters = RiskParameters(**risk_dict)
            
            # Create strategy definition
            strategy = StrategyDefinition(
                strategy_id=strategy_id,
                name=strategy_name,
                description=f"Strategy based on {template.name} template",
                strategy_type=template.strategy_type,
                template_id=template_id,
                trading_rules=template.trading_rules.copy(),
                parameters=parameters,
                risk_parameters=risk_parameters,
                symbols=symbols,
                timeframe=template.recommended_timeframe,
                data_requirements=template.data_requirements.copy(),
                created_by=created_by,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                confidence_score=0.6  # Template-based strategies start with moderate confidence
            )
            
            logger.info(f"Strategy created from template: {strategy_id}")
            return strategy
            
        except Exception as e:
            logger.error(f"Failed to create strategy from template {template_id}: {e}")
            return None
    
    def get_template_recommendations(
        self,
        user_profile: Dict[str, Any]
    ) -> List[Tuple[StrategyTemplate, float]]:
        """Get template recommendations based on user profile"""
        
        recommendations = []
        
        # Extract user preferences
        risk_tolerance = user_profile.get('risk_tolerance', 'medium')  # low, medium, high
        experience_level = user_profile.get('experience_level', 'beginner')  # beginner, intermediate, advanced
        capital_available = user_profile.get('capital_available', 10000)
        preferred_timeframe = user_profile.get('timeframe', '1D')
        strategy_preferences = user_profile.get('strategy_types', [])
        
        for template in self._templates.values():
            score = 0.0
            
            # Risk tolerance matching
            if risk_tolerance == 'low' and template.expected_drawdown > -0.08:
                score += 0.3
            elif risk_tolerance == 'medium' and -0.15 <= template.expected_drawdown <= -0.05:
                score += 0.3
            elif risk_tolerance == 'high' and template.expected_drawdown <= -0.1:
                score += 0.3
            
            # Experience level matching  
            if experience_level == 'beginner' and template.complexity_score <= 3.0:
                score += 0.3
            elif experience_level == 'intermediate' and 3.0 <= template.complexity_score <= 6.0:
                score += 0.3
            elif experience_level == 'advanced' and template.complexity_score >= 5.0:
                score += 0.3
            
            # Capital requirements
            if capital_available >= template.minimum_capital:
                score += 0.2
            else:
                score -= 0.3  # Penalize if insufficient capital
            
            # Timeframe preference
            if template.recommended_timeframe == preferred_timeframe:
                score += 0.1
            
            # Strategy type preferences
            if strategy_preferences and template.strategy_type.value in strategy_preferences:
                score += 0.1
            
            # Performance expectations
            if template.expected_sharpe >= 1.0:
                score += 0.1
            
            # Only recommend if score is reasonable
            if score >= 0.3:
                recommendations.append((template, score))
        
        # Sort by score (highest first)
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        return recommendations[:10]  # Top 10 recommendations
    
    def validate_template(self, template: StrategyTemplate) -> List[str]:
        """Validate strategy template for consistency and completeness"""
        
        validation_errors = []
        
        # Check required fields
        if not template.trading_rules:
            validation_errors.append("Template must have at least one trading rule")
        
        if not template.default_parameters:
            validation_errors.append("Template must have default parameters")
        
        if not template.risk_parameters:
            validation_errors.append("Template must have risk parameters")
        
        # Validate trading rules
        has_entry = any(rule.rule_type == "entry" for rule in template.trading_rules)
        if not has_entry:
            validation_errors.append("Template must have at least one entry rule")
        
        # Validate parameter bounds
        for param_name, bounds in template.parameter_bounds.items():
            if len(bounds) != 2 or bounds[0] >= bounds[1]:
                validation_errors.append(f"Invalid parameter bounds for {param_name}: {bounds}")
        
        # Validate risk parameters
        if template.risk_parameters.stop_loss_percentage >= 0:
            validation_errors.append("Stop loss percentage must be negative")
        
        if template.risk_parameters.take_profit_percentage <= 0:
            validation_errors.append("Take profit percentage must be positive")
        
        # Validate expected performance metrics
        if template.expected_win_rate < 0 or template.expected_win_rate > 1:
            validation_errors.append("Expected win rate must be between 0 and 1")
        
        if template.expected_drawdown > 0:
            validation_errors.append("Expected drawdown must be negative")
        
        return validation_errors
    
    def get_template_statistics(self) -> Dict[str, Any]:
        """Get statistics about available templates"""
        
        if not self._templates:
            return {}
        
        templates = list(self._templates.values())
        
        # Strategy type distribution
        type_distribution = {}
        for template in templates:
            strategy_type = template.strategy_type.value
            type_distribution[strategy_type] = type_distribution.get(strategy_type, 0) + 1
        
        # Complexity distribution
        complexity_scores = [t.complexity_score for t in templates]
        
        # Capital requirements
        capital_requirements = [t.minimum_capital for t in templates]
        
        # Performance expectations
        expected_sharpe = [t.expected_sharpe for t in templates]
        expected_drawdown = [t.expected_drawdown for t in templates]
        expected_win_rate = [t.expected_win_rate for t in templates]
        
        stats = {
            "total_templates": len(templates),
            "strategy_types": type_distribution,
            "complexity": {
                "min": min(complexity_scores),
                "max": max(complexity_scores),
                "avg": np.mean(complexity_scores),
                "distribution": {
                    "beginner": len([s for s in complexity_scores if s <= 3.0]),
                    "intermediate": len([s for s in complexity_scores if 3.0 < s <= 6.0]),
                    "advanced": len([s for s in complexity_scores if s > 6.0])
                }
            },
            "capital_requirements": {
                "min": min(capital_requirements),
                "max": max(capital_requirements),
                "avg": np.mean(capital_requirements)
            },
            "performance_expectations": {
                "avg_sharpe": np.mean(expected_sharpe),
                "avg_drawdown": np.mean(expected_drawdown),
                "avg_win_rate": np.mean(expected_win_rate)
            }
        }
        
        return stats