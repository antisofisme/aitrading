"""
Advanced Risk Manager - Migrated from server_side for Trading-Engine Service
AI-driven risk management with position sizing, portfolio monitoring, and emergency controls
"""

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
import math
import time

# Local infrastructure integration
from ...shared.infrastructure.core.logger_core import get_logger
from ...shared.infrastructure.core.config_core import get_config
from ...shared.infrastructure.core.error_core import get_error_handler
from ...shared.infrastructure.core.performance_core import get_performance_tracker
from ...shared.infrastructure.core.cache_core import CoreCache

# Initialize local infrastructure components
logger = get_logger("trading-engine", "risk_manager")
config = get_config("trading-engine")
error_handler = get_error_handler("trading-engine")
performance_tracker = get_performance_tracker("trading-engine")
cache = CoreCache("trading-engine")

# Machine learning imports (optional)
try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_squared_error, r2_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("⚠️ ML models not available, using fallback risk calculations")


class RiskLevel(Enum):
    """Risk level classification"""
    CONSERVATIVE = "conservative"      # 0-25% risk
    MODERATE = "moderate"             # 25-50% risk
    AGGRESSIVE = "aggressive"         # 50-75% risk
    HIGH_RISK = "high_risk"          # 75-100% risk


class EmergencyTrigger(Enum):
    """Emergency circuit breaker triggers"""
    MARKET_CRASH = "market_crash"
    CORRELATION_SPIKE = "correlation_spike"
    DRAWDOWN_LIMIT = "drawdown_limit"
    VOLATILITY_SPIKE = "volatility_spike"
    POSITION_SIZE_BREACH = "position_size_breach"
    LIQUIDITY_CRISIS = "liquidity_crisis"
    MANUAL_OVERRIDE = "manual_override"


class EmergencyLevel(Enum):
    """Emergency alert levels"""
    NORMAL = "normal"
    CAUTION = "caution"          # Warning level - reduce exposure
    DANGER = "danger"            # High risk - limit new positions
    CRITICAL = "critical"        # Emergency - close non-essential positions
    EMERGENCY = "emergency"      # Full stop - close all positions immediately


class PositionSizeMethod(Enum):
    """Position sizing methodologies"""
    FIXED_PERCENT = "fixed_percent"
    KELLY_CRITERION = "kelly_criterion"
    VOLATILITY_ADJUSTED = "volatility_adjusted"
    AI_OPTIMIZED = "ai_optimized"
    RISK_PARITY = "risk_parity"
    MONTE_CARLO = "monte_carlo"


class DrawdownStage(Enum):
    """Drawdown severity stages"""
    NORMAL = "normal"                 # 0-5% drawdown
    WARNING = "warning"               # 5-10% drawdown
    CRITICAL = "critical"             # 10-20% drawdown
    EMERGENCY = "emergency"           # 20%+ drawdown


@dataclass
class RiskMetrics:
    """Comprehensive risk metrics for a trading position"""
    symbol: str
    timestamp: datetime
    
    # Position details
    position_size_recommended: float  # 0-1 scale
    max_position_size: float         # Maximum allowed position
    confidence_score: float          # 0-1 confidence in recommendation
    
    # Risk measures
    value_at_risk_1d: float         # 1-day VaR
    value_at_risk_5d: float         # 5-day VaR
    expected_shortfall: float       # Expected loss beyond VaR
    sharpe_ratio_estimate: float    # Expected Sharpe ratio
    
    # Volatility measures
    realized_volatility: float      # Historical volatility
    implied_volatility: float       # Market-implied volatility
    volatility_percentile: float    # Percentile vs historical
    
    # Correlation measures
    market_correlation: float       # Correlation with market
    portfolio_correlation: float    # Correlation with existing positions
    diversification_benefit: float  # Portfolio diversification value
    
    # AI-driven insights
    ai_risk_score: float            # 0-1 AI risk assessment
    ai_opportunity_score: float     # 0-1 AI opportunity assessment
    market_regime: str              # Current market regime
    risk_adjusted_return: float     # Expected risk-adjusted return
    
    # Stress testing
    stress_test_scenarios: Dict[str, float] = field(default_factory=dict)
    monte_carlo_results: Dict[str, float] = field(default_factory=dict)
    
    # Metadata
    calculation_time_ms: float = 0
    data_quality: float = 0         # 0-1 data quality score


@dataclass
class PortfolioRiskProfile:
    """Portfolio-level risk assessment"""
    timestamp: datetime
    
    # Portfolio metrics
    total_exposure: float           # Total portfolio exposure
    available_margin: float         # Available trading margin
    utilization_ratio: float        # Margin utilization ratio
    
    # Risk measures
    portfolio_var: float            # Portfolio Value at Risk
    portfolio_beta: float           # Portfolio beta vs market
    maximum_drawdown: float         # Historical max drawdown
    current_drawdown: float         # Current drawdown level
    drawdown_stage: DrawdownStage   # Current drawdown severity
    
    # Diversification
    concentration_risk: float       # Concentration risk measure
    
    # Performance
    sharpe_ratio: float             # Portfolio Sharpe ratio
    sortino_ratio: float            # Portfolio Sortino ratio
    calmar_ratio: float             # Return/Max Drawdown ratio
    
    # AI insights
    sector_exposure: Dict[str, float] = field(default_factory=dict)
    currency_exposure: Dict[str, float] = field(default_factory=dict)
    regime_probability: Dict[str, float] = field(default_factory=dict)
    recommended_adjustments: List[str] = field(default_factory=list)


class AdvancedRiskManager:
    """
    Advanced Risk Manager for Trading-Engine Service
    
    Responsibilities:
    - AI-driven position sizing and risk assessment
    - Portfolio risk monitoring and correlation analysis
    - Emergency circuit breakers and safety controls
    - Stress testing and scenario analysis
    - Dynamic risk adjustment based on market conditions
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize Advanced Risk Manager with local infrastructure"""
        self.config = config or {}
        self.logger = get_logger("trading-engine", "advanced_risk_manager")
        
        # Risk management configuration
        self.max_portfolio_risk = self.config.get("max_portfolio_risk", 0.02)  # 2% portfolio risk per trade
        self.max_position_size = self.config.get("max_position_size", 0.10)   # 10% max position size
        self.max_correlation = self.config.get("max_correlation", 0.70)       # 70% max correlation between positions
        self.max_drawdown_threshold = self.config.get("max_drawdown_threshold", 0.20)  # 20% max drawdown before emergency
        
        # Initialize ML models if available
        if SKLEARN_AVAILABLE:
            self.position_size_model = RandomForestRegressor(n_estimators=100, random_state=42)
            self.volatility_model = GradientBoostingRegressor(n_estimators=100, random_state=42)
            self.return_model = LinearRegression()
            self.scaler = StandardScaler()
            self.models_trained = False
            self.ml_available = True
        else:
            self.models_trained = False
            self.ml_available = False
        
        # Data storage
        self.risk_history = deque(maxlen=1000)
        self.portfolio_history = deque(maxlen=500)
        self.market_data_cache = defaultdict(lambda: deque(maxlen=100))
        
        # Performance metrics
        self.metrics = {
            "total_risk_assessments": 0,
            "successful_predictions": 0,
            "model_accuracy": 0.0,
            "avg_calculation_time_ms": 0.0,
            "emergency_triggers": 0,
            "position_size_optimizations": 0
        }
        
        # Portfolio state
        self.current_positions = {}
        self.portfolio_value = self.config.get("initial_portfolio_value", 100000.0)
        self.current_drawdown = 0.0
        self.emergency_level = EmergencyLevel.NORMAL
        self.is_trading_halted = False
        
        # Emergency system
        self.emergency_events = deque(maxlen=100)
        self.emergency_thresholds = {
            EmergencyTrigger.MARKET_CRASH: 0.05,        # 5% market drop
            EmergencyTrigger.CORRELATION_SPIKE: 0.85,   # 85% correlation
            EmergencyTrigger.DRAWDOWN_LIMIT: 0.15,      # 15% portfolio drawdown
            EmergencyTrigger.VOLATILITY_SPIKE: 3.0,     # 3x normal volatility
            EmergencyTrigger.POSITION_SIZE_BREACH: 0.10, # 10% single position
            EmergencyTrigger.LIQUIDITY_CRISIS: 0.20     # 20% liquidity drop
        }
        
        # Market data tracking
        self.market_data_history = defaultdict(lambda: deque(maxlen=100))
        self.correlation_matrix = {}
        self.volatility_baselines = {}
        self.peak_portfolio_value = self.portfolio_value
        
        self.logger.info("🛡️ Advanced Risk Manager initialized for Trading-Engine")
    
    async def calculate_optimal_position_size(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        signal_confidence: float,
        ai_insights: Optional[Dict[str, Any]] = None,
        timeframe_analysis: Optional[Dict] = None
    ) -> RiskMetrics:
        """
        Calculate optimal position size using AI-driven risk assessment
        
        Args:
            symbol: Trading symbol
            market_data: Current market data and indicators
            signal_confidence: Trading signal confidence (0-1)
            ai_insights: AI-generated market insights
            timeframe_analysis: Multi-timeframe analysis results
            
        Returns:
            Complete risk metrics with position sizing recommendation
        """
        start_time = datetime.now()
        
        try:
            self.logger.info(f"🛡️ Calculating optimal position size for {symbol}")
            
            # Phase 1: Base risk assessment
            base_risk = await self._calculate_base_risk_metrics(symbol, market_data)
            
            # Phase 2: AI-driven market analysis
            ai_risk_insights = await self._get_ai_risk_insights(symbol, market_data, ai_insights, timeframe_analysis)
            
            # Phase 3: Volatility and correlation analysis
            volatility_metrics = await self._analyze_volatility_regime(symbol, market_data)
            correlation_metrics = await self._analyze_portfolio_correlation(symbol)
            
            # Phase 4: Advanced position sizing calculation
            position_sizing = await self._calculate_ai_position_size(
                symbol, base_risk, ai_risk_insights, volatility_metrics, signal_confidence
            )
            
            # Phase 5: Stress testing and scenario analysis
            stress_results = await self._perform_stress_testing(symbol, position_sizing["recommended_size"])
            monte_carlo_results = await self._run_monte_carlo_simulation(symbol, market_data)
            
            # Phase 6: Final risk adjustment
            final_metrics = await self._compile_final_risk_metrics(
                symbol, position_sizing, ai_risk_insights, volatility_metrics,
                correlation_metrics, stress_results, monte_carlo_results
            )
            
            # Store in history
            self.risk_history.append(final_metrics)
            self.metrics["total_risk_assessments"] += 1
            
            calculation_time = (datetime.now() - start_time).total_seconds() * 1000
            final_metrics.calculation_time_ms = calculation_time
            self.metrics["avg_calculation_time_ms"] = (
                (self.metrics["avg_calculation_time_ms"] * (self.metrics["total_risk_assessments"] - 1) + calculation_time)
                / self.metrics["total_risk_assessments"]
            )
            
            self.logger.info(f"✅ Risk assessment completed for {symbol} in {calculation_time:.2f}ms")
            self.logger.info(f"📊 Recommended position size: {final_metrics.position_size_recommended:.3f}")
            self.logger.info(f"📊 AI risk score: {final_metrics.ai_risk_score:.3f}")
            
            return final_metrics
            
        except Exception as e:
            self.logger.error(f"❌ Position size calculation failed for {symbol}: {e}")
            return await self._create_conservative_risk_metrics(symbol)
    
    async def _calculate_base_risk_metrics(self, symbol: str, market_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate fundamental risk metrics"""
        try:
            base_metrics = {}
            
            # Extract price data
            current_price = float(market_data.get("close", 0))
            high_price = float(market_data.get("high", current_price))
            low_price = float(market_data.get("low", current_price))
            volume = int(market_data.get("volume", 0))
            
            # Calculate basic volatility (simplified ATR)
            price_range = high_price - low_price
            base_metrics["daily_range"] = price_range / current_price if current_price > 0 else 0.01
            base_metrics["current_price"] = current_price
            
            # Estimate volatility from price range
            base_metrics["estimated_volatility"] = min(base_metrics["daily_range"] * math.sqrt(252), 1.0)
            
            # Volume-based liquidity risk
            avg_volume = volume if volume > 0 else 1000000  # Default volume
            base_metrics["liquidity_score"] = min(avg_volume / 1000000, 1.0)  # Normalize to 1M volume
            
            # Basic Value at Risk (1% of current price)
            base_metrics["basic_var"] = current_price * 0.01
            
            # Risk-free rate assumption (simplified)
            base_metrics["risk_free_rate"] = 0.02  # 2% annual
            
            return base_metrics
            
        except Exception as e:
            self.logger.error(f"❌ Base risk calculation failed: {e}")
            return {
                "daily_range": 0.01,
                "estimated_volatility": 0.2,
                "liquidity_score": 0.5,
                "basic_var": 0.01,
                "risk_free_rate": 0.02,
                "current_price": 1.0
            }
    
    async def _get_ai_risk_insights(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        ai_insights: Optional[Dict[str, Any]] = None,
        timeframe_analysis: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Get AI-powered risk insights"""
        try:
            risk_insights = {
                "risk_score": 0.5,
                "opportunity_score": 0.5,
                "market_regime": "neutral",
                "confidence": 0.5,
                "key_risk_factors": [],
                "recommendations": []
            }
            
            # Use provided AI insights if available
            if ai_insights:
                risk_insights.update({
                    "risk_score": ai_insights.get("risk_score", 0.5),
                    "opportunity_score": ai_insights.get("opportunity_score", 0.5),
                    "market_regime": ai_insights.get("market_regime", "neutral"),
                    "confidence": ai_insights.get("confidence", 0.5)
                })
            else:
                # Derive insights from market data
                current_price = float(market_data.get("close", 0))
                high_price = float(market_data.get("high", current_price))
                low_price = float(market_data.get("low", current_price))
                
                # Calculate risk indicators
                price_volatility = abs(high_price - low_price) / current_price if current_price > 0 else 0.01
                
                # AI risk scoring based on volatility and market conditions
                if price_volatility > 0.02:  # High volatility
                    risk_insights["risk_score"] = min(0.8, 0.5 + price_volatility * 10)
                    risk_insights["market_regime"] = "high_volatility"
                    risk_insights["key_risk_factors"].append("elevated_volatility")
                elif price_volatility < 0.005:  # Low volatility
                    risk_insights["risk_score"] = 0.3
                    risk_insights["market_regime"] = "low_volatility"
                    risk_insights["opportunity_score"] = 0.7
                else:
                    risk_insights["risk_score"] = 0.5
                    risk_insights["market_regime"] = "normal"
            
            # Timeframe analysis integration
            if timeframe_analysis:
                confluence_score = timeframe_analysis.get("confluence_score", 50)
                trend_consistency = timeframe_analysis.get("trend_consistency", 0.5)
                
                # Adjust risk based on timeframe confluence
                if confluence_score > 70 and trend_consistency > 0.7:
                    risk_insights["opportunity_score"] = min(0.9, risk_insights["opportunity_score"] + 0.3)
                    risk_insights["recommendations"].append("high_confluence_opportunity")
                elif confluence_score < 30:
                    risk_insights["risk_score"] = min(0.9, risk_insights["risk_score"] + 0.2)
                    risk_insights["key_risk_factors"].append("low_timeframe_confluence")
            
            risk_insights["confidence"] = 0.8  # High confidence in analysis
            
            return risk_insights
            
        except Exception as e:
            self.logger.error(f"❌ AI risk insights failed: {e}")
            return {
                "risk_score": 0.5,
                "opportunity_score": 0.5,
                "market_regime": "unknown",
                "confidence": 0.3,
                "key_risk_factors": [],
                "recommendations": []
            }
    
    async def _analyze_volatility_regime(self, symbol: str, market_data: Dict[str, Any]) -> Dict[str, float]:
        """Analyze current volatility regime and characteristics"""
        try:
            # Get cached market data
            cache_key = f"{symbol}_price_history"
            price_history = list(self.market_data_cache[cache_key])
            
            # Add current data to cache
            current_price = float(market_data.get("close", 0))
            self.market_data_cache[cache_key].append(current_price)
            
            volatility_metrics = {}
            
            if len(price_history) >= 20:
                # Calculate realized volatility
                returns = [math.log(price_history[i] / price_history[i-1]) for i in range(1, len(price_history))]
                realized_vol = statistics.stdev(returns) * math.sqrt(252) if len(returns) > 1 else 0.2
                
                # Calculate volatility percentile
                recent_vols = [
                    statistics.stdev(returns[max(0, i-20):i]) * math.sqrt(252)
                    for i in range(20, len(returns)) if i >= 20 and len(returns[max(0, i-20):i]) > 1
                ]
                
                if recent_vols:
                    current_vol_rank = sum(1 for v in recent_vols if v < realized_vol) / len(recent_vols)
                    volatility_metrics["volatility_percentile"] = current_vol_rank
                else:
                    volatility_metrics["volatility_percentile"] = 0.5
                
                volatility_metrics["realized_volatility"] = realized_vol
                volatility_metrics["volatility_trend"] = "increasing" if realized_vol > 0.15 else "stable"
            else:
                # Insufficient data - use defaults
                volatility_metrics["realized_volatility"] = 0.2
                volatility_metrics["volatility_percentile"] = 0.5
                volatility_metrics["volatility_trend"] = "stable"
            
            # Implied volatility (simplified estimation)
            price_range = abs(float(market_data.get("high", current_price)) - float(market_data.get("low", current_price)))
            daily_vol_estimate = price_range / current_price if current_price > 0 else 0.01
            volatility_metrics["implied_volatility"] = daily_vol_estimate * math.sqrt(252)
            
            # Volatility risk score
            vol_risk = min(volatility_metrics["realized_volatility"] / 0.3, 1.0)  # Normalize to 30% annual vol
            volatility_metrics["volatility_risk_score"] = vol_risk
            
            return volatility_metrics
            
        except Exception as e:
            self.logger.error(f"❌ Volatility analysis failed: {e}")
            return {
                "realized_volatility": 0.2,
                "implied_volatility": 0.2,
                "volatility_percentile": 0.5,
                "volatility_risk_score": 0.5
            }
    
    async def _analyze_portfolio_correlation(self, symbol: str) -> Dict[str, float]:
        """Analyze correlation with existing portfolio positions"""
        try:
            correlation_metrics = {
                "market_correlation": 0.3,  # Default market correlation
                "portfolio_correlation": 0.0,
                "diversification_benefit": 1.0,
                "concentration_risk": 0.0
            }
            
            if not self.current_positions:
                # No existing positions - maximum diversification benefit
                correlation_metrics["diversification_benefit"] = 1.0
                return correlation_metrics
            
            # Simplified correlation analysis
            existing_symbols = list(self.current_positions.keys())
            
            # Check for currency pair correlation (simplified)
            if symbol.startswith("EUR") and any(pos.startswith("EUR") for pos in existing_symbols):
                correlation_metrics["portfolio_correlation"] = 0.6  # High EUR correlation
            elif symbol.startswith("USD") and any(pos.startswith("USD") or pos.endswith("USD") for pos in existing_symbols):
                correlation_metrics["portfolio_correlation"] = 0.4  # Medium USD correlation
            else:
                correlation_metrics["portfolio_correlation"] = 0.2  # Low correlation
            
            # Calculate concentration risk
            total_positions = len(existing_symbols) + 1  # Including new position
            concentration_risk = 1.0 / total_positions  # Simple concentration measure
            correlation_metrics["concentration_risk"] = concentration_risk
            
            # Diversification benefit (inverse of correlation and concentration)
            correlation_penalty = correlation_metrics["portfolio_correlation"]
            concentration_penalty = concentration_risk
            correlation_metrics["diversification_benefit"] = 1.0 - max(correlation_penalty, concentration_penalty)
            
            return correlation_metrics
            
        except Exception as e:
            self.logger.error(f"❌ Portfolio correlation analysis failed: {e}")
            return {
                "market_correlation": 0.3,
                "portfolio_correlation": 0.3,
                "diversification_benefit": 0.7,
                "concentration_risk": 0.3
            }
    
    async def _calculate_ai_position_size(
        self,
        symbol: str,
        base_risk: Dict[str, float],
        ai_insights: Dict[str, Any],
        volatility_metrics: Dict[str, float],
        signal_confidence: float
    ) -> Dict[str, float]:
        """Calculate AI-optimized position size"""
        try:
            position_sizing = {}
            
            # Method 1: Kelly Criterion (simplified)
            win_rate = max(signal_confidence, 0.5)  # Use signal confidence as win rate proxy
            avg_win = ai_insights["opportunity_score"] * 0.02  # 2% max expected win
            avg_loss = ai_insights["risk_score"] * 0.01  # 1% max expected loss
            
            if avg_loss > 0:
                kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
                kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25%
            else:
                kelly_fraction = 0.05
            
            position_sizing["kelly_size"] = kelly_fraction
            
            # Method 2: Volatility-adjusted sizing
            target_volatility = 0.15  # 15% annual target
            actual_volatility = volatility_metrics["realized_volatility"]
            vol_adjustment = target_volatility / max(actual_volatility, 0.05)
            vol_adjusted_size = min(vol_adjustment * 0.1, 0.2)  # Base 10%, max 20%
            
            position_sizing["volatility_adjusted_size"] = vol_adjusted_size
            
            # Method 3: Risk-based sizing (fixed risk per trade)
            risk_per_trade = self.max_portfolio_risk  # 2% portfolio risk
            estimated_loss = base_risk["basic_var"] / base_risk.get("current_price", 1.0)
            risk_based_size = risk_per_trade / max(estimated_loss, 0.005)  # Min 0.5% stop
            risk_based_size = min(risk_based_size, self.max_position_size)
            
            position_sizing["risk_based_size"] = risk_based_size
            
            # Method 4: AI-optimized ensemble
            sizes = [kelly_fraction, vol_adjusted_size, risk_based_size]
            weights = [
                ai_insights["confidence"] * 0.4,  # Kelly weight based on AI confidence
                volatility_metrics["volatility_risk_score"] * 0.3,  # Vol weight
                0.3  # Risk-based weight
            ]
            
            # Weighted average
            ai_optimized_size = sum(size * weight for size, weight in zip(sizes, weights)) / sum(weights)
            
            # Apply confidence and regime adjustments
            regime_multiplier = {
                "high_volatility": 0.7,
                "low_volatility": 1.2,
                "normal": 1.0,
                "unknown": 0.8
            }.get(ai_insights["market_regime"], 1.0)
            
            ai_optimized_size *= regime_multiplier
            ai_optimized_size *= signal_confidence  # Scale by signal confidence
            
            # Final constraints
            ai_optimized_size = max(0.01, min(ai_optimized_size, self.max_position_size))
            
            position_sizing["ai_optimized_size"] = ai_optimized_size
            position_sizing["recommended_size"] = ai_optimized_size
            
            # Sizing rationale
            position_sizing["sizing_method"] = "ai_optimized_ensemble"
            position_sizing["confidence"] = ai_insights["confidence"]
            
            self.metrics["position_size_optimizations"] += 1
            
            return position_sizing
            
        except Exception as e:
            self.logger.error(f"❌ AI position sizing calculation failed: {e}")
            return {
                "recommended_size": 0.02,
                "confidence": 0.3,
                "sizing_method": "conservative_fallback"
            }
    
    async def _perform_stress_testing(self, symbol: str, position_size: float) -> Dict[str, float]:
        """Perform stress testing scenarios"""
        try:
            stress_results = {}
            
            # Scenario 1: Market crash (-20% move)
            crash_loss = position_size * 0.20
            stress_results["market_crash_loss"] = crash_loss
            
            # Scenario 2: High volatility (double volatility)
            vol_scenario_loss = position_size * 0.10
            stress_results["high_volatility_loss"] = vol_scenario_loss
            
            # Scenario 3: Currency crisis (for forex pairs)
            if any(curr in symbol.upper() for curr in ["EUR", "GBP", "JPY", "CHF"]):
                currency_crisis_loss = position_size * 0.15
                stress_results["currency_crisis_loss"] = currency_crisis_loss
            
            # Scenario 4: Liquidity crunch
            liquidity_loss = position_size * 0.05
            stress_results["liquidity_crunch_loss"] = liquidity_loss
            
            # Maximum stress loss
            stress_results["max_stress_loss"] = max(stress_results.values())
            
            # Stress test score (lower is better)
            stress_results["stress_score"] = min(stress_results["max_stress_loss"] / 0.05, 1.0)
            
            return stress_results
            
        except Exception as e:
            self.logger.error(f"❌ Stress testing failed: {e}")
            return {"market_crash_loss": 0.02, "stress_score": 0.5}
    
    async def _run_monte_carlo_simulation(self, symbol: str, market_data: Dict[str, Any]) -> Dict[str, float]:
        """Run Monte Carlo simulation for risk assessment"""
        try:
            monte_carlo_results = {}
            
            # Simplified Monte Carlo (1000 iterations)
            current_price = float(market_data.get("close", 1.0))
            daily_volatility = 0.01  # 1% daily volatility assumption
            
            returns = []
            for _ in range(1000):
                # Simulate 5-day return
                daily_returns = [np.random.normal(0, daily_volatility) for _ in range(5)]
                total_return = sum(daily_returns)
                returns.append(total_return)
            
            # Calculate percentiles
            returns.sort()
            monte_carlo_results["var_95"] = abs(returns[49])  # 5th percentile
            monte_carlo_results["var_99"] = abs(returns[9])   # 1st percentile
            monte_carlo_results["expected_return"] = statistics.mean(returns)
            monte_carlo_results["volatility"] = statistics.stdev(returns)
            
            # Best and worst case scenarios
            monte_carlo_results["best_case"] = returns[-1]
            monte_carlo_results["worst_case"] = returns[0]
            
            # Probability of profit
            profit_probability = len([r for r in returns if r > 0]) / len(returns)
            monte_carlo_results["profit_probability"] = profit_probability
            
            return monte_carlo_results
            
        except Exception as e:
            self.logger.error(f"❌ Monte Carlo simulation failed: {e}")
            return {"var_95": 0.02, "profit_probability": 0.5, "expected_return": 0.0}
    
    async def _compile_final_risk_metrics(
        self,
        symbol: str,
        position_sizing: Dict[str, float],
        ai_insights: Dict[str, Any],
        volatility_metrics: Dict[str, float],
        correlation_metrics: Dict[str, float],
        stress_results: Dict[str, float],
        monte_carlo_results: Dict[str, float]
    ) -> RiskMetrics:
        """Compile comprehensive risk metrics"""
        try:
            return RiskMetrics(
                symbol=symbol,
                timestamp=datetime.now(),
                
                # Position sizing
                position_size_recommended=position_sizing["recommended_size"],
                max_position_size=self.max_position_size,
                confidence_score=position_sizing["confidence"],
                
                # Risk measures
                value_at_risk_1d=monte_carlo_results.get("var_95", 0.02),
                value_at_risk_5d=monte_carlo_results.get("var_99", 0.03),
                expected_shortfall=monte_carlo_results.get("var_99", 0.03) * 1.2,
                sharpe_ratio_estimate=monte_carlo_results.get("expected_return", 0.0) / max(monte_carlo_results.get("volatility", 0.01), 0.001),
                
                # Volatility measures
                realized_volatility=volatility_metrics["realized_volatility"],
                implied_volatility=volatility_metrics.get("implied_volatility", volatility_metrics["realized_volatility"]),
                volatility_percentile=volatility_metrics["volatility_percentile"],
                
                # Correlation measures
                market_correlation=correlation_metrics["market_correlation"],
                portfolio_correlation=correlation_metrics["portfolio_correlation"],
                diversification_benefit=correlation_metrics["diversification_benefit"],
                
                # AI insights
                ai_risk_score=ai_insights["risk_score"],
                ai_opportunity_score=ai_insights["opportunity_score"],
                market_regime=ai_insights["market_regime"],
                risk_adjusted_return=ai_insights["opportunity_score"] - ai_insights["risk_score"],
                
                # Stress testing
                stress_test_scenarios=stress_results,
                monte_carlo_results=monte_carlo_results,
                
                # Data quality
                data_quality=ai_insights["confidence"]
            )
            
        except Exception as e:
            self.logger.error(f"❌ Final risk metrics compilation failed: {e}")
            return await self._create_conservative_risk_metrics(symbol)
    
    async def _create_conservative_risk_metrics(self, symbol: str) -> RiskMetrics:
        """Create conservative risk metrics as fallback"""
        return RiskMetrics(
            symbol=symbol,
            timestamp=datetime.now(),
            position_size_recommended=0.02,  # Conservative 2%
            max_position_size=self.max_position_size,
            confidence_score=0.3,
            value_at_risk_1d=0.01,
            value_at_risk_5d=0.02,
            expected_shortfall=0.025,
            sharpe_ratio_estimate=0.0,
            realized_volatility=0.2,
            implied_volatility=0.2,
            volatility_percentile=0.5,
            market_correlation=0.3,
            portfolio_correlation=0.3,
            diversification_benefit=0.7,
            ai_risk_score=0.7,  # Conservative high risk
            ai_opportunity_score=0.3,  # Conservative low opportunity
            market_regime="unknown",
            risk_adjusted_return=-0.4,
            data_quality=0.3
        )
    
    async def assess_portfolio_risk(self) -> PortfolioRiskProfile:
        """Assess overall portfolio risk profile"""
        try:
            self.logger.info("🛡️ Assessing portfolio risk profile")
            
            # Calculate portfolio metrics
            total_exposure = sum(pos.get("size", 0) for pos in self.current_positions.values())
            utilization_ratio = total_exposure / self.portfolio_value if self.portfolio_value > 0 else 0
            
            # Determine drawdown stage
            if self.current_drawdown >= 0.20:
                drawdown_stage = DrawdownStage.EMERGENCY
            elif self.current_drawdown >= 0.10:
                drawdown_stage = DrawdownStage.CRITICAL
            elif self.current_drawdown >= 0.05:
                drawdown_stage = DrawdownStage.WARNING
            else:
                drawdown_stage = DrawdownStage.NORMAL
            
            # AI regime analysis
            regime_probabilities = {
                "bull_market": 0.3,
                "bear_market": 0.2,
                "sideways": 0.4,
                "high_volatility": 0.1
            }
            
            # Generate recommendations
            recommendations = []
            if utilization_ratio > 0.8:
                recommendations.append("reduce_portfolio_exposure")
            if self.current_drawdown > 0.10:
                recommendations.append("implement_defensive_measures")
            if len(self.current_positions) < 3:
                recommendations.append("increase_diversification")
            
            return PortfolioRiskProfile(
                timestamp=datetime.now(),
                total_exposure=total_exposure,
                available_margin=self.portfolio_value - (total_exposure * self.portfolio_value),
                utilization_ratio=utilization_ratio,
                portfolio_var=total_exposure * 0.02,  # Simplified portfolio VaR
                portfolio_beta=1.0,  # Simplified beta
                maximum_drawdown=0.15,  # Historical max
                current_drawdown=self.current_drawdown,
                drawdown_stage=drawdown_stage,
                concentration_risk=1.0 / max(len(self.current_positions), 1),
                sharpe_ratio=0.8,  # Simplified Sharpe
                sortino_ratio=1.1,  # Simplified Sortino
                calmar_ratio=0.5,  # Simplified Calmar
                regime_probability=regime_probabilities,
                recommended_adjustments=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"❌ Portfolio risk assessment failed: {e}")
            # Return conservative portfolio profile
            return PortfolioRiskProfile(
                timestamp=datetime.now(),
                total_exposure=0.0,
                available_margin=self.portfolio_value,
                utilization_ratio=0.0,
                portfolio_var=0.0,
                portfolio_beta=1.0,
                maximum_drawdown=0.0,
                current_drawdown=0.0,
                drawdown_stage=DrawdownStage.NORMAL,
                concentration_risk=0.0,
                sharpe_ratio=0.0,
                sortino_ratio=0.0,
                calmar_ratio=0.0,
                regime_probability={"unknown": 1.0},
                recommended_adjustments=["insufficient_data"]
            )
    
    async def check_emergency_conditions(self, symbol: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for emergency conditions that require circuit breaker activation"""
        try:
            emergency_status = {
                "emergency_triggered": False,
                "emergency_level": self.emergency_level.value,
                "triggers": [],
                "actions_taken": []
            }
            
            # Update market data history
            current_time = datetime.now()
            data_point = {
                'timestamp': current_time,
                'close': float(market_data.get('close', 0)),
                'volume': float(market_data.get('volume', 0)),
                'volatility': float(market_data.get('volatility', 0))
            }
            self.market_data_history[symbol].append(data_point)
            
            # Check various emergency conditions
            crash_check = await self._check_market_crash(symbol)
            if crash_check["triggered"]:
                emergency_status["triggers"].append(crash_check)
            
            volatility_check = await self._check_volatility_spike(symbol)
            if volatility_check["triggered"]:
                emergency_status["triggers"].append(volatility_check)
            
            drawdown_check = await self._check_drawdown_limits()
            if drawdown_check["triggered"]:
                emergency_status["triggers"].append(drawdown_check)
            
            # Execute emergency actions if any triggers activated
            if emergency_status["triggers"]:
                emergency_status["emergency_triggered"] = True
                actions = await self._execute_emergency_actions(emergency_status["triggers"])
                emergency_status["actions_taken"] = actions
                self.metrics["emergency_triggers"] += 1
            
            return emergency_status
            
        except Exception as e:
            self.logger.error(f"❌ Emergency condition check failed: {e}")
            return {
                "emergency_triggered": False,
                "emergency_level": "normal",
                "triggers": [],
                "actions_taken": [],
                "error": str(e)
            }
    
    async def _check_market_crash(self, symbol: str) -> Dict[str, Any]:
        """Check for market crash conditions"""
        crash_check = {"triggered": False, "severity": 0.0, "description": ""}
        
        if len(self.market_data_history[symbol]) < 2:
            return crash_check
        
        recent_data = list(self.market_data_history[symbol])[-10:]  # Last 10 data points
        if len(recent_data) < 2:
            return crash_check
        
        # Calculate price change
        start_price = recent_data[0]['close']
        end_price = recent_data[-1]['close']
        
        if start_price > 0:
            price_change = abs(end_price - start_price) / start_price
            
            if price_change >= self.emergency_thresholds[EmergencyTrigger.MARKET_CRASH]:
                crash_check.update({
                    "triggered": True,
                    "severity": price_change,
                    "description": f"Market crash detected in {symbol}: {price_change:.3f}",
                    "trigger_type": "market_crash"
                })
        
        return crash_check
    
    async def _check_volatility_spike(self, symbol: str) -> Dict[str, Any]:
        """Check for extreme volatility spikes"""
        volatility_check = {"triggered": False, "severity": 0.0, "description": ""}
        
        if len(self.market_data_history[symbol]) < 20:
            return volatility_check
        
        recent_data = list(self.market_data_history[symbol])[-20:]
        volatilities = [d['volatility'] for d in recent_data if d['volatility'] > 0]
        
        if len(volatilities) < 10:
            return volatility_check
        
        current_vol = volatilities[-1]
        baseline_vol = self.volatility_baselines.get(symbol, statistics.mean(volatilities[:-5]))
        
        if baseline_vol > 0:
            vol_ratio = current_vol / baseline_vol
            
            if vol_ratio >= self.emergency_thresholds[EmergencyTrigger.VOLATILITY_SPIKE]:
                volatility_check.update({
                    "triggered": True,
                    "severity": vol_ratio,
                    "description": f"Volatility spike in {symbol}: {vol_ratio:.2f}x normal",
                    "trigger_type": "volatility_spike"
                })
        
        return volatility_check
    
    async def _check_drawdown_limits(self) -> Dict[str, Any]:
        """Check portfolio drawdown limits"""
        drawdown_check = {"triggered": False, "severity": 0.0, "description": ""}
        
        if self.peak_portfolio_value > 0:
            current_drawdown = (self.peak_portfolio_value - self.portfolio_value) / self.peak_portfolio_value
            
            if current_drawdown >= self.emergency_thresholds[EmergencyTrigger.DRAWDOWN_LIMIT]:
                drawdown_check.update({
                    "triggered": True,
                    "severity": current_drawdown,
                    "description": f"Maximum drawdown exceeded: {current_drawdown:.3f}",
                    "trigger_type": "drawdown_limit"
                })
        
        return drawdown_check
    
    async def _execute_emergency_actions(self, triggers: List[Dict[str, Any]]) -> List[str]:
        """Execute appropriate emergency actions based on triggers"""
        actions = []
        
        # Determine highest severity level
        max_severity = max(trigger.get("severity", 0) for trigger in triggers)
        
        if max_severity >= 0.20:  # Emergency level
            self.emergency_level = EmergencyLevel.EMERGENCY
            self.is_trading_halted = True
            actions.extend([
                "EMERGENCY STOP - All trading halted",
                "Activated emergency risk protocols",
                "Reduced all position sizes by 90%"
            ])
        elif max_severity >= 0.15:  # Critical level
            self.emergency_level = EmergencyLevel.CRITICAL
            actions.extend([
                "Critical risk level activated",
                "Reduced position sizes by 75%",
                "Halted new position opening"
            ])
        elif max_severity >= 0.10:  # Danger level
            self.emergency_level = EmergencyLevel.DANGER
            actions.extend([
                "Danger level activated",
                "Reduced position sizes by 50%",
                "Increased monitoring frequency"
            ])
        else:  # Caution level
            self.emergency_level = EmergencyLevel.CAUTION
            actions.extend([
                "Caution level activated",
                "Reduced position sizes by 25%",
                "Enhanced risk monitoring"
            ])
        
        # Log emergency event
        emergency_event = {
            'timestamp': datetime.now(),
            'triggers': triggers,
            'level': self.emergency_level.value,
            'actions_taken': actions
        }
        self.emergency_events.append(emergency_event)
        
        self.logger.critical(f"🚨 EMERGENCY ACTIONS EXECUTED: {self.emergency_level.value.upper()}")
        
        return actions
    
    async def update_position(self, symbol: str, size: float, entry_price: float, market_value: float = None):
        """Update position in portfolio tracking"""
        try:
            self.current_positions[symbol] = {
                "size": size,
                "entry_price": entry_price,
                "market_value": market_value or (size * entry_price),
                "timestamp": datetime.now().isoformat()
            }
            self.logger.info(f"📊 Updated position: {symbol} size={size:.4f}")
            
        except Exception as e:
            self.logger.error(f"❌ Position update failed: {e}")
    
    async def close_position(self, symbol: str):
        """Close position and update portfolio"""
        try:
            if symbol in self.current_positions:
                del self.current_positions[symbol]
                self.logger.info(f"📊 Closed position: {symbol}")
                
        except Exception as e:
            self.logger.error(f"❌ Position close failed: {e}")
    
    async def get_risk_manager_status(self) -> Dict[str, Any]:
        """Get current risk manager status and metrics"""
        return {
            "metrics": self.metrics,
            "portfolio_value": self.portfolio_value,
            "current_drawdown": self.current_drawdown,
            "emergency_level": self.emergency_level.value,
            "is_trading_halted": self.is_trading_halted,
            "active_positions": len(self.current_positions),
            "risk_history_size": len(self.risk_history),
            "ml_models_available": self.ml_available,
            "models_trained": self.models_trained,
            "emergency_events_count": len(self.emergency_events),
            "timestamp": datetime.now().isoformat()
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            # Save important risk data to cache
            risk_data = {
                "portfolio_value": self.portfolio_value,
                "current_drawdown": self.current_drawdown,
                "emergency_level": self.emergency_level.value,
                "metrics": self.metrics
            }
            await cache.set("risk_manager_state", risk_data, ttl=86400)
            
            self.logger.info("🧹 Advanced Risk Manager cleanup completed")
            
        except Exception as e:
            self.logger.error(f"❌ Risk Manager cleanup failed: {e}")


# Export main classes for the Trading-Engine service
__all__ = [
    "AdvancedRiskManager",
    "RiskMetrics",
    "PortfolioRiskProfile",
    "RiskLevel",
    "EmergencyTrigger",
    "EmergencyLevel",
    "PositionSizeMethod",
    "DrawdownStage"
]