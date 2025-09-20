"""
📈 Decision Impact Assessment Framework
Comprehensive framework for assessing the impact of trading decisions with performance correlation analysis

FEATURES:
- Real-time decision impact tracking with market correlation
- Performance attribution analysis linking decisions to outcomes
- Risk-adjusted impact measurement with Sharpe ratio calculations
- Confidence correlation validation with actual performance results
- Multi-timeframe impact assessment (immediate, short-term, long-term)
- Systematic feedback loop for decision quality improvement

IMPACT ASSESSMENT LAYERS:
1. Immediate Impact Assessment - Price movement, slippage, execution quality
2. Short-term Performance - 1-hour to 24-hour outcome tracking
3. Medium-term Analysis - 1-day to 1-week performance correlation
4. Long-term Impact - Multi-week trend and portfolio impact
5. Risk-adjusted Performance - Sharpe, Sortino, and Calmar ratios
6. Confidence Validation - Compare predicted vs actual confidence outcomes
"""

import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import statistics
import math

# Local infrastructure
from .decision_audit_system import decision_audit_system
from ....shared.infrastructure.core.logger_core import CoreLogger
from ....shared.infrastructure.core.cache_core import CoreCache
from ....shared.infrastructure.core.performance_core import CorePerformance

# Initialize components
logger = CoreLogger("trading-engine", "impact-assessor")
cache = CoreCache("decision-impact", max_size=5000, default_ttl=3600)
performance_tracker = CorePerformance("trading-engine")


class ImpactTimeframe(Enum):
    """Timeframes for impact assessment"""
    IMMEDIATE = "immediate"      # 0-5 minutes
    SHORT_TERM = "short_term"    # 5 minutes - 1 hour
    MEDIUM_TERM = "medium_term"  # 1 hour - 1 day
    LONG_TERM = "long_term"      # 1 day - 1 week
    EXTENDED = "extended"        # 1 week+


class ImpactMetricType(Enum):
    """Types of impact metrics"""
    FINANCIAL = "financial"         # PnL, returns, profit factor
    EXECUTION = "execution"         # Slippage, fill rate, timing
    RISK = "risk"                  # Risk-adjusted returns, drawdown
    CONFIDENCE = "confidence"       # Confidence correlation, calibration
    MARKET = "market"              # Market impact, opportunity cost
    BEHAVIORAL = "behavioral"       # Decision pattern, learning effect


class PerformanceAttribution(Enum):
    """Performance attribution categories"""
    PREDICTION_ACCURACY = "prediction_accuracy"
    TIMING_QUALITY = "timing_quality"
    RISK_MANAGEMENT = "risk_management"
    EXECUTION_EFFICIENCY = "execution_efficiency"
    MARKET_CONDITIONS = "market_conditions"
    STRATEGY_SELECTION = "strategy_selection"


@dataclass
class ImpactMetric:
    """Individual impact metric measurement"""
    metric_id: str
    decision_id: str
    timeframe: ImpactTimeframe
    metric_type: ImpactMetricType
    
    # Metric values
    value: float
    normalized_value: float  # 0-1 normalized
    benchmark_value: Optional[float] = None
    
    # Context
    measurement_time: datetime = None
    market_conditions: Dict[str, Any] = None
    
    # Quality indicators
    confidence_interval: Tuple[float, float] = None
    statistical_significance: Optional[float] = None
    
    def __post_init__(self):
        if not self.measurement_time:
            self.measurement_time = datetime.now()


@dataclass
class DecisionImpactAssessment:
    """Comprehensive decision impact assessment"""
    assessment_id: str
    decision_id: str
    
    # Basic decision info
    symbol: str
    action: str
    entry_time: datetime
    entry_price: float
    position_size: float
    initial_confidence: float
    
    # Impact metrics by timeframe
    immediate_impact: Dict[str, Any] = None
    short_term_impact: Dict[str, Any] = None
    medium_term_impact: Dict[str, Any] = None
    long_term_impact: Dict[str, Any] = None
    extended_impact: Dict[str, Any] = None
    
    # Performance attribution
    performance_attribution: Dict[PerformanceAttribution, float] = None
    
    # Risk-adjusted metrics
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    calmar_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    
    # Confidence validation
    confidence_correlation: Optional[float] = None
    confidence_calibration: Optional[float] = None
    prediction_accuracy: Optional[float] = None
    
    # Overall assessment
    overall_impact_score: Optional[float] = None
    decision_quality_score: Optional[float] = None
    
    # Learning insights
    key_insights: List[str] = None
    improvement_areas: List[str] = None
    
    # Metadata
    assessment_timestamp: datetime = None
    last_updated: datetime = None
    
    def __post_init__(self):
        if not self.assessment_timestamp:
            self.assessment_timestamp = datetime.now()
        if not self.last_updated:
            self.last_updated = datetime.now()
        if not self.key_insights:
            self.key_insights = []
        if not self.improvement_areas:
            self.improvement_areas = []
        if not self.performance_attribution:
            self.performance_attribution = {}


@dataclass
class MarketDataPoint:
    """Market data point for impact calculation"""
    timestamp: datetime
    symbol: str
    price: float
    volume: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    spread: Optional[float] = None


class DecisionImpactAssessor:
    """
    Comprehensive decision impact assessment system
    Tracks and analyzes the real-world impact of trading decisions
    """
    
    def __init__(self):
        """Initialize decision impact assessor"""
        
        # Impact storage
        self.impact_assessments: Dict[str, DecisionImpactAssessment] = {}
        self.impact_metrics: Dict[str, List[ImpactMetric]] = defaultdict(list)
        
        # Market data tracking
        self.market_data_buffer: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Correlation tracking
        self.confidence_performance_data = deque(maxlen=500)
        
        # Benchmark data
        self.benchmark_metrics = {
            "average_slippage": 0.0002,  # 2 pips
            "average_fill_rate": 0.98,
            "market_correlation": 0.65,
            "execution_time_ms": 150
        }
        
        # Assessment statistics
        self.assessment_statistics = {
            "total_assessments": 0,
            "positive_impact_count": 0,
            "negative_impact_count": 0,
            "average_impact_score": 0.0,
            "average_confidence_correlation": 0.0,
            "total_pnl_tracked": 0.0,
            "assessment_accuracy": 0.0
        }
        
        # Performance attribution tracking
        self.attribution_analysis = {attr.value: deque(maxlen=200) for attr in PerformanceAttribution}
        
        logger.info("Decision Impact Assessor initialized")
    
    async def create_impact_assessment(
        self,
        decision_id: str,
        decision_data: Dict[str, Any]
    ) -> DecisionImpactAssessment:
        """Create new impact assessment for a decision"""
        
        try:
            assessment_id = f"impact_{int(datetime.now().timestamp() * 1000)}"
            
            # Extract decision details
            symbol = decision_data.get("symbol", "UNKNOWN")
            action = decision_data.get("action", "hold")
            entry_price = decision_data.get("entry_price", 0.0)
            position_size = decision_data.get("position_size", 0.0)
            initial_confidence = decision_data.get("confidence", 0.5)
            
            # Create assessment record
            assessment = DecisionImpactAssessment(
                assessment_id=assessment_id,
                decision_id=decision_id,
                symbol=symbol,
                action=action,
                entry_time=datetime.now(),
                entry_price=entry_price,
                position_size=position_size,
                initial_confidence=initial_confidence
            )
            
            # Store assessment
            self.impact_assessments[decision_id] = assessment
            
            # Update statistics
            self.assessment_statistics["total_assessments"] += 1
            
            # Cache for quick access
            await cache.set(f"assessment:{decision_id}", asdict(assessment), ttl=7200)
            
            logger.info(f"Impact assessment created: {assessment_id} for decision {decision_id}")
            
            return assessment
            
        except Exception as e:
            logger.error(f"Failed to create impact assessment: {e}")
            raise
    
    async def update_market_data(self, symbol: str, market_data: MarketDataPoint):
        """Update market data for impact calculation"""
        
        try:
            # Store market data
            self.market_data_buffer[symbol].append(market_data)
            
            # Trigger impact updates for active assessments
            active_assessments = [
                assessment for assessment in self.impact_assessments.values()
                if assessment.symbol == symbol and assessment.extended_impact is None
            ]
            
            for assessment in active_assessments:
                await self._update_assessment_with_market_data(assessment, market_data)
            
        except Exception as e:
            logger.error(f"Failed to update market data: {e}")
    
    async def _update_assessment_with_market_data(
        self,
        assessment: DecisionImpactAssessment,
        market_data: MarketDataPoint
    ):
        """Update assessment with new market data"""
        
        try:
            time_elapsed = market_data.timestamp - assessment.entry_time
            
            # Determine which timeframe to update
            if time_elapsed <= timedelta(minutes=5):
                await self._update_immediate_impact(assessment, market_data)
            elif time_elapsed <= timedelta(hours=1):
                await self._update_short_term_impact(assessment, market_data)
            elif time_elapsed <= timedelta(days=1):
                await self._update_medium_term_impact(assessment, market_data)
            elif time_elapsed <= timedelta(weeks=1):
                await self._update_long_term_impact(assessment, market_data)
            else:
                await self._update_extended_impact(assessment, market_data)
            
            # Update last updated timestamp
            assessment.last_updated = datetime.now()
            
            # Update cache
            await cache.set(f"assessment:{assessment.decision_id}", asdict(assessment), ttl=7200)
            
        except Exception as e:
            logger.error(f"Failed to update assessment with market data: {e}")
    
    async def _update_immediate_impact(
        self,
        assessment: DecisionImpactAssessment,
        market_data: MarketDataPoint
    ):
        """Update immediate impact (0-5 minutes)"""
        
        try:
            current_price = market_data.price
            entry_price = assessment.entry_price
            position_size = assessment.position_size
            
            # Calculate immediate PnL
            if assessment.action == "buy":
                pnl = (current_price - entry_price) * position_size
                unrealized_return = (current_price - entry_price) / entry_price
            elif assessment.action == "sell":
                pnl = (entry_price - current_price) * position_size
                unrealized_return = (entry_price - current_price) / entry_price
            else:
                pnl = 0.0
                unrealized_return = 0.0
            
            # Calculate slippage (if execution price differs from expected)
            expected_price = entry_price  # Would be from original quote
            slippage = abs(current_price - expected_price) / expected_price
            
            # Market impact assessment
            market_impact = await self._calculate_market_impact(
                assessment.symbol,
                position_size,
                market_data.timestamp
            )
            
            # Execution quality metrics
            execution_quality = await self._assess_execution_quality(assessment, market_data)
            
            assessment.immediate_impact = {
                "pnl": pnl,
                "unrealized_return": unrealized_return,
                "slippage": slippage,
                "market_impact": market_impact,
                "execution_quality": execution_quality,
                "price_move_pips": abs(current_price - entry_price) * 10000,  # For forex
                "timestamp": market_data.timestamp.isoformat()
            }
            
            logger.debug(f"Immediate impact updated: {assessment.decision_id} - PnL: {pnl:.2f}")
            
        except Exception as e:
            logger.error(f"Failed to update immediate impact: {e}")
    
    async def _update_short_term_impact(
        self,
        assessment: DecisionImpactAssessment,
        market_data: MarketDataPoint
    ):
        """Update short-term impact (5 minutes - 1 hour)"""
        
        try:
            # Calculate short-term performance metrics
            performance_metrics = await self._calculate_performance_metrics(
                assessment,
                market_data,
                ImpactTimeframe.SHORT_TERM
            )
            
            # Confidence correlation analysis
            confidence_correlation = await self._calculate_confidence_correlation(
                assessment,
                performance_metrics["return"]
            )
            
            # Risk metrics
            risk_metrics = await self._calculate_short_term_risk_metrics(assessment, market_data)
            
            assessment.short_term_impact = {
                **performance_metrics,
                "confidence_correlation": confidence_correlation,
                **risk_metrics,
                "timestamp": market_data.timestamp.isoformat()
            }
            
            logger.debug(f"Short-term impact updated: {assessment.decision_id}")
            
        except Exception as e:
            logger.error(f"Failed to update short-term impact: {e}")
    
    async def _update_medium_term_impact(
        self,
        assessment: DecisionImpactAssessment,
        market_data: MarketDataPoint
    ):
        """Update medium-term impact (1 hour - 1 day)"""
        
        try:
            # Performance metrics
            performance_metrics = await self._calculate_performance_metrics(
                assessment,
                market_data,
                ImpactTimeframe.MEDIUM_TERM
            )
            
            # Risk-adjusted metrics
            risk_adjusted_metrics = await self._calculate_risk_adjusted_metrics(
                assessment,
                market_data
            )
            
            # Update Sharpe ratio
            assessment.sharpe_ratio = risk_adjusted_metrics.get("sharpe_ratio")
            
            # Performance attribution analysis
            attribution = await self._analyze_performance_attribution(assessment, market_data)
            assessment.performance_attribution = attribution
            
            assessment.medium_term_impact = {
                **performance_metrics,
                **risk_adjusted_metrics,
                "performance_attribution": attribution,
                "timestamp": market_data.timestamp.isoformat()
            }
            
            logger.debug(f"Medium-term impact updated: {assessment.decision_id}")
            
        except Exception as e:
            logger.error(f"Failed to update medium-term impact: {e}")
    
    async def _update_long_term_impact(
        self,
        assessment: DecisionImpactAssessment,
        market_data: MarketDataPoint
    ):
        """Update long-term impact (1 day - 1 week)"""
        
        try:
            # Long-term performance analysis
            performance_metrics = await self._calculate_performance_metrics(
                assessment,
                market_data,
                ImpactTimeframe.LONG_TERM
            )
            
            # Complete risk-adjusted metrics
            assessment.sortino_ratio = await self._calculate_sortino_ratio(assessment, market_data)
            assessment.calmar_ratio = await self._calculate_calmar_ratio(assessment, market_data)
            assessment.max_drawdown = await self._calculate_max_drawdown(assessment)
            
            # Final confidence validation
            assessment.confidence_correlation = await self._calculate_final_confidence_correlation(assessment)
            assessment.confidence_calibration = await self._calculate_confidence_calibration(assessment)
            assessment.prediction_accuracy = await self._calculate_prediction_accuracy(assessment)
            
            assessment.long_term_impact = {
                **performance_metrics,
                "sortino_ratio": assessment.sortino_ratio,
                "calmar_ratio": assessment.calmar_ratio,
                "max_drawdown": assessment.max_drawdown,
                "confidence_metrics": {
                    "correlation": assessment.confidence_correlation,
                    "calibration": assessment.confidence_calibration,
                    "accuracy": assessment.prediction_accuracy
                },
                "timestamp": market_data.timestamp.isoformat()
            }
            
            logger.debug(f"Long-term impact updated: {assessment.decision_id}")
            
        except Exception as e:
            logger.error(f"Failed to update long-term impact: {e}")
    
    async def _update_extended_impact(
        self,
        assessment: DecisionImpactAssessment,
        market_data: MarketDataPoint
    ):
        """Update extended impact (1 week+) and finalize assessment"""
        
        try:
            # Final performance calculation
            final_metrics = await self._calculate_performance_metrics(
                assessment,
                market_data,
                ImpactTimeframe.EXTENDED
            )
            
            # Calculate overall impact scores
            assessment.overall_impact_score = await self._calculate_overall_impact_score(assessment)
            assessment.decision_quality_score = await self._calculate_decision_quality_score(assessment)
            
            # Generate insights and improvement areas
            insights = await self._generate_impact_insights(assessment)
            assessment.key_insights = insights["insights"]
            assessment.improvement_areas = insights["improvement_areas"]
            
            assessment.extended_impact = {
                **final_metrics,
                "overall_impact_score": assessment.overall_impact_score,
                "decision_quality_score": assessment.decision_quality_score,
                "finalized": True,
                "timestamp": market_data.timestamp.isoformat()
            }
            
            # Update global statistics
            await self._update_global_statistics(assessment)
            
            # Log final assessment to audit system
            await decision_audit_system.assess_decision_impact(
                assessment.decision_id,
                {
                    "pnl": final_metrics.get("total_pnl", 0.0),
                    "duration_minutes": (market_data.timestamp - assessment.entry_time).total_seconds() / 60,
                    "execution_quality": assessment.immediate_impact.get("execution_quality", 0.5) if assessment.immediate_impact else 0.5,
                    "overall_impact_score": assessment.overall_impact_score
                }
            )
            
            logger.info(f"Extended impact finalized: {assessment.decision_id} - Score: {assessment.overall_impact_score:.3f}")
            
        except Exception as e:
            logger.error(f"Failed to update extended impact: {e}")
    
    async def _calculate_performance_metrics(
        self,
        assessment: DecisionImpactAssessment,
        market_data: MarketDataPoint,
        timeframe: ImpactTimeframe
    ) -> Dict[str, Any]:
        """Calculate performance metrics for given timeframe"""
        
        try:
            current_price = market_data.price
            entry_price = assessment.entry_price
            position_size = assessment.position_size
            
            # Basic PnL calculation
            if assessment.action == "buy":
                pnl = (current_price - entry_price) * position_size
                return_pct = (current_price - entry_price) / entry_price
            elif assessment.action == "sell":
                pnl = (entry_price - current_price) * position_size
                return_pct = (entry_price - current_price) / entry_price
            else:
                pnl = 0.0
                return_pct = 0.0
            
            # Time-based metrics
            time_elapsed = market_data.timestamp - assessment.entry_time
            holding_period_hours = time_elapsed.total_seconds() / 3600
            
            # Annualized return (approximate)
            if holding_period_hours > 0:
                annualized_return = return_pct * (8760 / holding_period_hours)  # 365 * 24 hours
            else:
                annualized_return = 0.0
            
            # Risk-free rate adjustment (simplified)
            risk_free_rate = 0.02  # 2% annual risk-free rate
            excess_return = annualized_return - risk_free_rate
            
            return {
                "total_pnl": pnl,
                "return": return_pct,
                "annualized_return": annualized_return,
                "excess_return": excess_return,
                "holding_period_hours": holding_period_hours,
                "price_change_pct": (current_price - entry_price) / entry_price,
                "current_price": current_price
            }
            
        except Exception as e:
            logger.error(f"Performance metrics calculation failed: {e}")
            return {"total_pnl": 0.0, "return": 0.0, "error": str(e)}
    
    async def _calculate_confidence_correlation(self, assessment: DecisionImpactAssessment, actual_return: float) -> float:
        """Calculate correlation between predicted confidence and actual performance"""
        
        try:
            initial_confidence = assessment.initial_confidence
            
            # Normalize actual return to 0-1 scale for comparison
            # Assume returns typically range from -10% to +10%
            normalized_return = max(0, min(1, (actual_return + 0.1) / 0.2))
            
            # Calculate simple correlation measure
            correlation = 1 - abs(initial_confidence - normalized_return)
            
            # Store for global analysis
            self.confidence_performance_data.append({
                "confidence": initial_confidence,
                "normalized_return": normalized_return,
                "correlation": correlation,
                "timestamp": datetime.now().isoformat()
            })
            
            return correlation
            
        except Exception as e:
            logger.error(f"Confidence correlation calculation failed: {e}")
            return 0.5
    
    async def _calculate_market_impact(
        self,
        symbol: str,
        position_size: float,
        timestamp: datetime
    ) -> float:
        """Calculate market impact of the trade"""
        
        try:
            # Get recent market data for the symbol
            market_buffer = self.market_data_buffer[symbol]
            
            if len(market_buffer) < 2:
                return 0.0  # Not enough data
            
            # Simple market impact estimation based on position size
            # In production, this would use more sophisticated models
            base_impact = 0.0001  # 1 pip base impact
            size_multiplier = min(5.0, position_size)  # Cap at 5x multiplier
            
            market_impact = base_impact * size_multiplier
            
            return market_impact
            
        except Exception as e:
            logger.error(f"Market impact calculation failed: {e}")
            return 0.0
    
    async def _assess_execution_quality(
        self,
        assessment: DecisionImpactAssessment,
        market_data: MarketDataPoint
    ) -> float:
        """Assess execution quality based on various factors"""
        
        try:
            quality_factors = []
            
            # Slippage factor
            if market_data.bid and market_data.ask:
                spread = market_data.ask - market_data.bid
                expected_slippage = spread / 2
                actual_slippage = abs(market_data.price - assessment.entry_price)
                
                if expected_slippage > 0:
                    slippage_ratio = actual_slippage / expected_slippage
                    slippage_quality = max(0, 1 - (slippage_ratio - 1))  # 1.0 = perfect, <1.0 = worse than expected
                    quality_factors.append(slippage_quality)
            
            # Timing factor (simplified)
            time_since_entry = market_data.timestamp - assessment.entry_time
            timing_quality = max(0.5, 1 - (time_since_entry.total_seconds() / 300))  # Prefer quick execution
            quality_factors.append(timing_quality)
            
            # Market conditions factor
            if market_data.volume:
                # Higher volume generally means better execution
                volume_quality = min(1.0, market_data.volume / 1000)  # Normalize volume
                quality_factors.append(volume_quality)
            
            # Calculate overall execution quality
            if quality_factors:
                execution_quality = statistics.mean(quality_factors)
            else:
                execution_quality = 0.7  # Default moderate quality
            
            return execution_quality
            
        except Exception as e:
            logger.error(f"Execution quality assessment failed: {e}")
            return 0.5
    
    async def _calculate_short_term_risk_metrics(
        self,
        assessment: DecisionImpactAssessment,
        market_data: MarketDataPoint
    ) -> Dict[str, float]:
        """Calculate short-term risk metrics"""
        
        try:
            # Get price history for volatility calculation
            symbol_data = list(self.market_data_buffer[assessment.symbol])
            
            if len(symbol_data) < 10:
                return {"volatility": 0.01, "var_95": 0.02}  # Default values
            
            # Calculate recent price volatility
            recent_prices = [point.price for point in symbol_data[-20:]]  # Last 20 data points
            if len(recent_prices) >= 2:
                returns = [
                    (recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1] 
                    for i in range(1, len(recent_prices))
                ]
                volatility = np.std(returns) if returns else 0.01
            else:
                volatility = 0.01
            
            # Calculate Value at Risk (simplified)
            current_return = 0.0
            if assessment.entry_price > 0:
                if assessment.action == "buy":
                    current_return = (market_data.price - assessment.entry_price) / assessment.entry_price
                elif assessment.action == "sell":
                    current_return = (assessment.entry_price - market_data.price) / assessment.entry_price
            
            # 95% VaR approximation
            var_95 = abs(current_return - (1.645 * volatility))  # 1.645 is 95% confidence z-score
            
            return {
                "volatility": volatility,
                "var_95": var_95,
                "current_return": current_return
            }
            
        except Exception as e:
            logger.error(f"Short-term risk metrics calculation failed: {e}")
            return {"volatility": 0.01, "var_95": 0.02, "error": str(e)}
    
    async def _calculate_risk_adjusted_metrics(
        self,
        assessment: DecisionImpactAssessment,
        market_data: MarketDataPoint
    ) -> Dict[str, float]:
        """Calculate risk-adjusted performance metrics"""
        
        try:
            # Get return and volatility
            if assessment.short_term_impact:
                return_pct = assessment.short_term_impact.get("return", 0.0)
                volatility = assessment.short_term_impact.get("volatility", 0.01)
            else:
                # Calculate from current data
                if assessment.entry_price > 0:
                    if assessment.action == "buy":
                        return_pct = (market_data.price - assessment.entry_price) / assessment.entry_price
                    else:
                        return_pct = (assessment.entry_price - market_data.price) / assessment.entry_price
                else:
                    return_pct = 0.0
                volatility = 0.01  # Default
            
            # Sharpe ratio calculation
            risk_free_rate = 0.02 / 252  # Daily risk-free rate (approximate)
            if volatility > 0:
                sharpe_ratio = (return_pct - risk_free_rate) / volatility
            else:
                sharpe_ratio = 0.0
            
            # Information ratio (against benchmark)
            benchmark_return = 0.0  # Assume benchmark is 0
            tracking_error = volatility  # Simplified
            if tracking_error > 0:
                information_ratio = (return_pct - benchmark_return) / tracking_error
            else:
                information_ratio = 0.0
            
            return {
                "sharpe_ratio": sharpe_ratio,
                "information_ratio": information_ratio,
                "return_volatility_ratio": return_pct / volatility if volatility > 0 else 0.0
            }
            
        except Exception as e:
            logger.error(f"Risk-adjusted metrics calculation failed: {e}")
            return {"sharpe_ratio": 0.0, "information_ratio": 0.0}
    
    async def _analyze_performance_attribution(
        self,
        assessment: DecisionImpactAssessment,
        market_data: MarketDataPoint
    ) -> Dict[PerformanceAttribution, float]:
        """Analyze performance attribution across different factors"""
        
        try:
            attribution = {}
            
            # Prediction accuracy attribution (based on confidence correlation)
            if hasattr(assessment, 'short_term_impact') and assessment.short_term_impact:
                confidence_corr = assessment.short_term_impact.get("confidence_correlation", 0.5)
                attribution[PerformanceAttribution.PREDICTION_ACCURACY] = confidence_corr * 0.3
            else:
                attribution[PerformanceAttribution.PREDICTION_ACCURACY] = 0.15
            
            # Timing quality attribution
            time_elapsed = market_data.timestamp - assessment.entry_time
            timing_score = max(0, 1 - (time_elapsed.total_seconds() / 3600))  # 1 hour optimal
            attribution[PerformanceAttribution.TIMING_QUALITY] = timing_score * 0.2
            
            # Risk management attribution
            if assessment.immediate_impact:
                execution_quality = assessment.immediate_impact.get("execution_quality", 0.5)
                attribution[PerformanceAttribution.RISK_MANAGEMENT] = execution_quality * 0.2
            else:
                attribution[PerformanceAttribution.RISK_MANAGEMENT] = 0.1
            
            # Execution efficiency attribution
            if assessment.immediate_impact:
                slippage = assessment.immediate_impact.get("slippage", 0.001)
                efficiency_score = max(0, 1 - (slippage * 1000))  # Convert to efficiency score
                attribution[PerformanceAttribution.EXECUTION_EFFICIENCY] = efficiency_score * 0.15
            else:
                attribution[PerformanceAttribution.EXECUTION_EFFICIENCY] = 0.1
            
            # Market conditions attribution (residual)
            market_attribution = 1.0 - sum(attribution.values())
            attribution[PerformanceAttribution.MARKET_CONDITIONS] = max(0, market_attribution * 0.1)
            
            # Strategy selection attribution
            attribution[PerformanceAttribution.STRATEGY_SELECTION] = 0.05  # Base attribution
            
            # Normalize to sum to 1.0
            total_attribution = sum(attribution.values())
            if total_attribution > 0:
                attribution = {k: v / total_attribution for k, v in attribution.items()}
            
            return attribution
            
        except Exception as e:
            logger.error(f"Performance attribution analysis failed: {e}")
            return {attr: 1.0 / len(PerformanceAttribution) for attr in PerformanceAttribution}
    
    async def _calculate_sortino_ratio(
        self,
        assessment: DecisionImpactAssessment,
        market_data: MarketDataPoint
    ) -> float:
        """Calculate Sortino ratio (downside deviation)"""
        
        try:
            # Get price history for downside calculation
            symbol_data = list(self.market_data_buffer[assessment.symbol])
            
            if len(symbol_data) < 10:
                return 0.0
            
            # Calculate returns since entry
            entry_price = assessment.entry_price
            returns = []
            
            for data_point in symbol_data[-20:]:  # Last 20 points
                if assessment.action == "buy":
                    ret = (data_point.price - entry_price) / entry_price
                else:
                    ret = (entry_price - data_point.price) / entry_price
                returns.append(ret)
            
            if not returns:
                return 0.0
            
            # Calculate downside deviation
            target_return = 0.0  # Minimum acceptable return
            negative_returns = [ret for ret in returns if ret < target_return]
            
            if len(negative_returns) > 1:
                downside_deviation = np.std(negative_returns)
            else:
                downside_deviation = 0.01  # Small positive value to avoid division by zero
            
            # Current return
            current_return = returns[-1] if returns else 0.0
            risk_free_rate = 0.02 / 252  # Daily rate
            
            # Sortino ratio
            if downside_deviation > 0:
                sortino_ratio = (current_return - risk_free_rate) / downside_deviation
            else:
                sortino_ratio = 0.0
            
            return sortino_ratio
            
        except Exception as e:
            logger.error(f"Sortino ratio calculation failed: {e}")
            return 0.0
    
    async def _calculate_calmar_ratio(
        self,
        assessment: DecisionImpactAssessment,
        market_data: MarketDataPoint
    ) -> float:
        """Calculate Calmar ratio (return/max drawdown)"""
        
        try:
            # Calculate current return
            if assessment.medium_term_impact:
                current_return = assessment.medium_term_impact.get("annualized_return", 0.0)
            else:
                current_return = 0.0
            
            # Calculate max drawdown
            max_drawdown = await self._calculate_max_drawdown(assessment)
            
            # Calmar ratio
            if abs(max_drawdown) > 0.001:  # Avoid division by very small numbers
                calmar_ratio = current_return / abs(max_drawdown)
            else:
                calmar_ratio = 0.0
            
            return calmar_ratio
            
        except Exception as e:
            logger.error(f"Calmar ratio calculation failed: {e}")
            return 0.0
    
    async def _calculate_max_drawdown(self, assessment: DecisionImpactAssessment) -> float:
        """Calculate maximum drawdown since position entry"""
        
        try:
            # Get price history since entry
            symbol_data = list(self.market_data_buffer[assessment.symbol])
            entry_time = assessment.entry_time
            entry_price = assessment.entry_price
            
            # Filter data since entry
            relevant_data = [
                point for point in symbol_data 
                if point.timestamp >= entry_time
            ]
            
            if len(relevant_data) < 2:
                return 0.0
            
            # Calculate cumulative returns
            peak_value = 0.0
            max_drawdown = 0.0
            
            for data_point in relevant_data:
                # Calculate current return
                if assessment.action == "buy":
                    current_return = (data_point.price - entry_price) / entry_price
                else:
                    current_return = (entry_price - data_point.price) / entry_price
                
                # Update peak
                peak_value = max(peak_value, current_return)
                
                # Calculate drawdown
                drawdown = peak_value - current_return
                max_drawdown = max(max_drawdown, drawdown)
            
            return max_drawdown
            
        except Exception as e:
            logger.error(f"Max drawdown calculation failed: {e}")
            return 0.0
    
    async def _calculate_final_confidence_correlation(self, assessment: DecisionImpactAssessment) -> float:
        """Calculate final confidence correlation with actual performance"""
        
        try:
            # Get final performance data
            if assessment.long_term_impact:
                final_return = assessment.long_term_impact.get("return", 0.0)
            elif assessment.medium_term_impact:
                final_return = assessment.medium_term_impact.get("return", 0.0)
            else:
                return 0.5  # Default correlation
            
            # Compare with initial confidence
            initial_confidence = assessment.initial_confidence
            
            # Normalize return for comparison (-10% to +10% -> 0 to 1)
            normalized_return = max(0, min(1, (final_return + 0.1) / 0.2))
            
            # Calculate correlation
            correlation = 1 - abs(initial_confidence - normalized_return)
            
            return correlation
            
        except Exception as e:
            logger.error(f"Final confidence correlation calculation failed: {e}")
            return 0.5
    
    async def _calculate_confidence_calibration(self, assessment: DecisionImpactAssessment) -> float:
        """Calculate confidence calibration score"""
        
        try:
            # Confidence calibration measures how well confidence predicts success
            initial_confidence = assessment.initial_confidence
            
            # Determine if decision was "successful" based on final outcome
            if assessment.long_term_impact:
                final_return = assessment.long_term_impact.get("return", 0.0)
            elif assessment.medium_term_impact:
                final_return = assessment.medium_term_impact.get("return", 0.0)
            else:
                final_return = 0.0
            
            # Binary success indicator
            success = 1.0 if final_return > 0 else 0.0
            
            # Calibration error (how far off confidence was from actual success)
            calibration_error = abs(initial_confidence - success)
            calibration_score = 1.0 - calibration_error
            
            return max(0.0, calibration_score)
            
        except Exception as e:
            logger.error(f"Confidence calibration calculation failed: {e}")
            return 0.5
    
    async def _calculate_prediction_accuracy(self, assessment: DecisionImpactAssessment) -> float:
        """Calculate prediction accuracy score"""
        
        try:
            # Compare predicted direction with actual outcome
            predicted_action = assessment.action
            
            if assessment.long_term_impact:
                actual_return = assessment.long_term_impact.get("return", 0.0)
            else:
                actual_return = 0.0
            
            # Determine actual direction
            actual_direction = "buy" if actual_return > 0 else "sell" if actual_return < 0 else "hold"
            
            # Calculate accuracy
            if predicted_action == actual_direction:
                accuracy = 1.0
            elif predicted_action == "hold":
                accuracy = 0.5  # Neutral prediction gets partial credit
            else:
                accuracy = 0.0  # Wrong direction
            
            # Adjust by magnitude of return
            return_magnitude = min(1.0, abs(actual_return) * 10)  # Scale return magnitude
            adjusted_accuracy = accuracy * (0.5 + 0.5 * return_magnitude)
            
            return adjusted_accuracy
            
        except Exception as e:
            logger.error(f"Prediction accuracy calculation failed: {e}")
            return 0.5
    
    async def _calculate_overall_impact_score(self, assessment: DecisionImpactAssessment) -> float:
        """Calculate overall impact score combining all metrics"""
        
        try:
            impact_components = []
            
            # Financial performance (40% weight)
            if assessment.extended_impact:
                financial_return = assessment.extended_impact.get("return", 0.0)
                # Normalize to 0-1 scale (-10% to +10% return)
                normalized_financial = max(0, min(1, (financial_return + 0.1) / 0.2))
                impact_components.append(("financial", normalized_financial, 0.40))
            
            # Risk-adjusted performance (25% weight)
            if assessment.sharpe_ratio is not None:
                # Normalize Sharpe ratio (-2 to +2 -> 0 to 1)
                normalized_sharpe = max(0, min(1, (assessment.sharpe_ratio + 2) / 4))
                impact_components.append(("risk_adjusted", normalized_sharpe, 0.25))
            
            # Execution quality (15% weight)
            if assessment.immediate_impact:
                execution_quality = assessment.immediate_impact.get("execution_quality", 0.5)
                impact_components.append(("execution", execution_quality, 0.15))
            
            # Confidence correlation (10% weight)
            if assessment.confidence_correlation is not None:
                impact_components.append(("confidence", assessment.confidence_correlation, 0.10))
            
            # Prediction accuracy (10% weight)
            if assessment.prediction_accuracy is not None:
                impact_components.append(("prediction", assessment.prediction_accuracy, 0.10))
            
            # Calculate weighted impact score
            if impact_components:
                total_weight = sum(weight for _, _, weight in impact_components)
                weighted_score = sum(
                    score * weight for _, score, weight in impact_components
                ) / total_weight
            else:
                weighted_score = 0.5  # Default neutral score
            
            return max(0.0, min(1.0, weighted_score))
            
        except Exception as e:
            logger.error(f"Overall impact score calculation failed: {e}")
            return 0.5
    
    async def _calculate_decision_quality_score(self, assessment: DecisionImpactAssessment) -> float:
        """Calculate decision quality score based on process quality"""
        
        try:
            quality_factors = []
            
            # Confidence appropriateness
            if assessment.confidence_calibration is not None:
                quality_factors.append(assessment.confidence_calibration)
            
            # Risk management quality
            if assessment.immediate_impact:
                execution_quality = assessment.immediate_impact.get("execution_quality", 0.5)
                quality_factors.append(execution_quality)
            
            # Timing quality
            if assessment.performance_attribution:
                timing_attr = assessment.performance_attribution.get(PerformanceAttribution.TIMING_QUALITY, 0.5)
                quality_factors.append(timing_attr)
            
            # Strategy selection quality
            if assessment.performance_attribution:
                strategy_attr = assessment.performance_attribution.get(PerformanceAttribution.STRATEGY_SELECTION, 0.5)
                quality_factors.append(strategy_attr)
            
            # Overall process quality
            if quality_factors:
                decision_quality = statistics.mean(quality_factors)
            else:
                decision_quality = 0.5
            
            return max(0.0, min(1.0, decision_quality))
            
        except Exception as e:
            logger.error(f"Decision quality score calculation failed: {e}")
            return 0.5
    
    async def _generate_impact_insights(self, assessment: DecisionImpactAssessment) -> Dict[str, List[str]]:
        """Generate insights and improvement areas from impact assessment"""
        
        insights = []
        improvement_areas = []
        
        try:
            # Financial performance insights
            if assessment.extended_impact:
                final_return = assessment.extended_impact.get("return", 0.0)
                if final_return > 0.02:  # > 2% return
                    insights.append(f"✅ Strong financial performance: {final_return:.2%} return")
                elif final_return < -0.02:  # < -2% return
                    insights.append(f"❌ Poor financial performance: {final_return:.2%} loss")
                    improvement_areas.append("Review prediction accuracy and risk management")
            
            # Risk-adjusted performance insights
            if assessment.sharpe_ratio is not None:
                if assessment.sharpe_ratio > 1.0:
                    insights.append(f"✅ Excellent risk-adjusted returns (Sharpe: {assessment.sharpe_ratio:.2f})")
                elif assessment.sharpe_ratio < 0:
                    insights.append(f"❌ Poor risk-adjusted returns (Sharpe: {assessment.sharpe_ratio:.2f})")
                    improvement_areas.append("Improve risk management or reduce position sizing")
            
            # Confidence correlation insights
            if assessment.confidence_correlation is not None:
                if assessment.confidence_correlation > 0.8:
                    insights.append("✅ Excellent confidence calibration - predictions well-calibrated")
                elif assessment.confidence_correlation < 0.5:
                    insights.append("❌ Poor confidence calibration - overconfident or underconfident")
                    improvement_areas.append("Improve confidence estimation methodology")
            
            # Execution quality insights
            if assessment.immediate_impact:
                execution_quality = assessment.immediate_impact.get("execution_quality", 0.5)
                if execution_quality > 0.8:
                    insights.append("✅ High-quality execution with minimal slippage")
                elif execution_quality < 0.5:
                    insights.append("❌ Poor execution quality with significant slippage")
                    improvement_areas.append("Optimize execution timing and order management")
            
            # Drawdown insights
            if assessment.max_drawdown is not None:
                if assessment.max_drawdown > 0.05:  # > 5% drawdown
                    insights.append(f"⚠️ Significant drawdown experienced: {assessment.max_drawdown:.2%}")
                    improvement_areas.append("Implement better stop-loss or position management")
            
            # Performance attribution insights
            if assessment.performance_attribution:
                best_factor = max(assessment.performance_attribution.items(), key=lambda x: x[1])
                worst_factor = min(assessment.performance_attribution.items(), key=lambda x: x[1])
                
                insights.append(f"🎯 Strongest factor: {best_factor[0].value} ({best_factor[1]:.2%})")
                if worst_factor[1] < 0.3:
                    improvement_areas.append(f"Focus on improving {worst_factor[0].value}")
            
            # Overall quality insights
            if assessment.decision_quality_score is not None:
                if assessment.decision_quality_score > 0.8:
                    insights.append("✅ High-quality decision process")
                elif assessment.decision_quality_score < 0.5:
                    insights.append("❌ Decision process needs improvement")
                    improvement_areas.append("Review decision-making methodology and criteria")
            
        except Exception as e:
            logger.error(f"Impact insights generation failed: {e}")
            insights.append(f"⚠️ Insights generation error: {str(e)}")
        
        return {
            "insights": insights,
            "improvement_areas": improvement_areas
        }
    
    async def _update_global_statistics(self, assessment: DecisionImpactAssessment):
        """Update global assessment statistics"""
        
        try:
            # Count positive/negative impacts
            if assessment.overall_impact_score is not None:
                if assessment.overall_impact_score > 0.5:
                    self.assessment_statistics["positive_impact_count"] += 1
                else:
                    self.assessment_statistics["negative_impact_count"] += 1
                
                # Update average impact score
                total_assessments = self.assessment_statistics["total_assessments"]
                current_avg = self.assessment_statistics["average_impact_score"]
                new_score = assessment.overall_impact_score
                
                self.assessment_statistics["average_impact_score"] = (
                    (current_avg * (total_assessments - 1)) + new_score
                ) / total_assessments
            
            # Update average confidence correlation
            if assessment.confidence_correlation is not None:
                total_assessments = self.assessment_statistics["total_assessments"]
                current_avg = self.assessment_statistics["average_confidence_correlation"]
                new_correlation = assessment.confidence_correlation
                
                self.assessment_statistics["average_confidence_correlation"] = (
                    (current_avg * (total_assessments - 1)) + new_correlation
                ) / total_assessments
            
            # Update total PnL tracked
            if assessment.extended_impact:
                pnl = assessment.extended_impact.get("total_pnl", 0.0)
                self.assessment_statistics["total_pnl_tracked"] += pnl
            
        except Exception as e:
            logger.error(f"Global statistics update failed: {e}")
    
    async def get_assessment(self, decision_id: str) -> Optional[DecisionImpactAssessment]:
        """Get impact assessment for a decision"""
        
        try:
            # Try cache first
            cached_assessment = await cache.get(f"assessment:{decision_id}")
            if cached_assessment:
                return DecisionImpactAssessment(**cached_assessment)
            
            # Return from memory
            return self.impact_assessments.get(decision_id)
            
        except Exception as e:
            logger.error(f"Failed to get assessment: {e}")
            return None
    
    def get_assessment_statistics(self) -> Dict[str, Any]:
        """Get comprehensive assessment statistics"""
        
        return {
            "assessment_statistics": self.assessment_statistics.copy(),
            "total_assessments_tracked": len(self.impact_assessments),
            "confidence_performance_samples": len(self.confidence_performance_data),
            "market_data_symbols": list(self.market_data_buffer.keys()),
            "benchmark_metrics": self.benchmark_metrics.copy(),
            "attribution_analysis": {
                attr: len(samples) for attr, samples in self.attribution_analysis.items()
            },
            "last_updated": datetime.now().isoformat()
        }


# Global instance
decision_impact_assessor = DecisionImpactAssessor()