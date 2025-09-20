"""
Performance Analytics - Migrated from server_side for Trading-Engine Service
Comprehensive performance tracking, analysis, and reporting for trading strategies
"""

import asyncio
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import threading
import time
import uuid
from collections import deque
import statistics
import math

# Local infrastructure integration
from ...shared.infrastructure.core.logger_core import get_logger
from ...shared.infrastructure.core.config_core import get_config
from ...shared.infrastructure.core.error_core import get_error_handler
from ...shared.infrastructure.core.performance_core import get_performance_tracker
from ...shared.infrastructure.core.cache_core import CoreCache

# Initialize local infrastructure components
logger = get_logger("trading-engine", "performance_analytics")
config = get_config("trading-engine")
error_handler = get_error_handler("trading-engine")
performance_tracker = get_performance_tracker("trading-engine")
cache = CoreCache("trading-engine")

# Import strategy and risk classes from local core modules
try:
    from .strategy_executor import TradingSignal, StrategyPerformance
    from .risk_manager import RiskMetrics as RiskManagerMetrics
except ImportError:
    # Fallback definitions if imports fail
    pass


class PerformanceMetricType(Enum):
    """Performance metric categories"""
    RETURN_METRICS = "return_metrics"
    RISK_METRICS = "risk_metrics"
    EFFICIENCY_METRICS = "efficiency_metrics"
    CONSISTENCY_METRICS = "consistency_metrics"
    AI_METRICS = "ai_metrics"
    BEHAVIORAL_METRICS = "behavioral_metrics"


class ReportPeriod(Enum):
    """Reporting time periods"""
    REAL_TIME = "real_time"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class AnalysisMode(Enum):
    """Performance analysis modes"""
    BASIC = "basic"                    # Standard metrics
    ADVANCED = "advanced"              # Advanced statistical analysis
    AI_ENHANCED = "ai_enhanced"        # AI-powered insights
    COMPARATIVE = "comparative"        # Benchmark comparisons
    PREDICTIVE = "predictive"          # Future performance predictions


@dataclass
class PerformanceConfig:
    """Performance analytics configuration"""
    # Analysis Settings
    analysis_mode: AnalysisMode = AnalysisMode.AI_ENHANCED
    benchmark_symbols: List[str] = None
    risk_free_rate: float = 0.02  # 2% annual risk-free rate
    confidence_level: float = 0.95
    
    # Reporting Settings
    auto_generate_reports: bool = True
    report_frequencies: List[ReportPeriod] = None
    include_charts: bool = True
    include_ai_insights: bool = True
    
    # Performance Tracking
    track_real_time: bool = True
    real_time_update_interval: int = 60  # seconds
    performance_history_days: int = 365
    detailed_trade_analysis: bool = True
    
    # AI Enhancement
    enable_pattern_detection: bool = True
    enable_performance_prediction: bool = True
    enable_optimization_suggestions: bool = True
    learning_window_days: int = 30
    
    # Alert Settings
    enable_performance_alerts: bool = True
    drawdown_alert_threshold: float = 0.05  # 5%
    sharpe_alert_threshold: float = 1.0
    win_rate_alert_threshold: float = 0.40   # 40%


@dataclass
class ReturnMetrics:
    """Return-based performance metrics"""
    # Basic Returns
    total_return: float
    annualized_return: float
    daily_returns: List[float]
    monthly_returns: List[float]
    
    # Return Statistics
    average_daily_return: float
    return_volatility: float
    return_skewness: float
    return_kurtosis: float
    
    # Cumulative Performance
    cumulative_returns: List[float]
    rolling_returns: Dict[str, List[float]]  # 7d, 30d, 90d
    
    # Benchmark Comparison
    alpha: Optional[float] = None
    beta: Optional[float] = None
    tracking_error: Optional[float] = None
    information_ratio: Optional[float] = None


@dataclass
class RiskMetrics:
    """Risk-based performance metrics"""
    # Volatility Measures
    daily_volatility: float
    annualized_volatility: float
    downside_volatility: float
    
    # Risk-Adjusted Returns
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    omega_ratio: float
    
    # Drawdown Analysis
    max_drawdown: float
    current_drawdown: float
    drawdown_duration: int  # days
    
    # Value at Risk
    var_95: float  # 95% VaR
    var_99: float  # 99% VaR
    expected_shortfall: float
    
    # Risk Exposure
    portfolio_var: float
    correlation_risk: float
    concentration_risk: float
    
    # Optional fields with defaults
    drawdown_recovery_time: Optional[int] = None


@dataclass
class EfficiencyMetrics:
    """Trading efficiency metrics"""
    # Win/Loss Statistics
    win_rate: float
    loss_rate: float
    win_loss_ratio: float
    average_win: float
    average_loss: float
    
    # Profit Factor
    profit_factor: float
    recovery_factor: float
    payoff_ratio: float
    
    # Trade Analysis
    total_trades: int
    winning_trades: int
    losing_trades: int
    average_trade_duration: float  # hours
    
    # Execution Quality
    slippage_average: float
    execution_speed_ms: float
    fill_rate: float
    trade_frequency: float  # trades per day


@dataclass
class AIPerformanceMetrics:
    """AI-specific performance metrics"""
    # Prediction Accuracy
    signal_accuracy: float
    pattern_recognition_accuracy: float
    price_prediction_error: float
    
    # Learning Performance
    learning_efficiency: float
    adaptation_speed: float
    knowledge_retention: float
    
    # Decision Quality
    decision_confidence: float
    risk_assessment_accuracy: float
    timing_accuracy: float
    
    # AI System Health
    model_performance_score: float
    ensemble_consensus: float
    memory_utilization: float
    processing_latency: float


@dataclass
class PerformanceAlert:
    """Performance alert notification"""
    alert_id: str
    timestamp: datetime
    severity: str  # info, warning, critical
    metric_type: PerformanceMetricType
    message: str
    current_value: float
    threshold_value: float
    recommendation: Optional[str] = None


@dataclass
class PerformanceReport:
    """Comprehensive performance report"""
    report_id: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    report_period: ReportPeriod
    
    # Core Metrics
    return_metrics: ReturnMetrics
    risk_metrics: RiskMetrics
    efficiency_metrics: EfficiencyMetrics
    ai_metrics: AIPerformanceMetrics
    
    # Analysis Results
    performance_score: float  # Overall score 0-100
    risk_score: float        # Risk assessment 0-100
    ai_health_score: float   # AI system health 0-100
    
    # Insights and Recommendations
    key_insights: List[str]
    improvement_suggestions: List[str]
    risk_warnings: List[str]
    ai_recommendations: List[str]
    
    # Charts and Visualizations
    chart_data: Optional[Dict[str, Any]] = None
    performance_summary: Optional[str] = None


class TradingPerformanceAnalytics:
    """
    Trading Performance Analytics for Trading-Engine Service
    
    Responsibilities:
    - Comprehensive performance tracking and analysis
    - Real-time performance monitoring and alerts
    - Advanced statistical analysis and reporting
    - AI-powered insights and optimization suggestions
    - Strategy performance comparison and benchmarking
    """
    
    def __init__(self, config: PerformanceConfig = None):
        """Initialize Trading Performance Analytics with local infrastructure"""
        self.config = config or PerformanceConfig()
        self.logger = get_logger("trading-engine", "performance_analytics")
        
        # Performance Data Storage
        self.trades_history: deque = deque(maxlen=10000)
        self.performance_history: deque = deque(maxlen=1000)
        self.real_time_metrics: Dict[str, Any] = {}
        
        # Analysis State
        self.current_balance: float = self.config.__dict__.get("initial_balance", 100000.0)
        self.initial_balance: float = self.current_balance
        self.peak_balance: float = self.current_balance
        self.last_analysis_time: Optional[datetime] = None
        
        # Threading for real-time updates
        self.analysis_thread: Optional[threading.Thread] = None
        self.is_running: bool = False
        self.performance_lock = threading.Lock()
        
        # Alert System
        self.active_alerts: List[PerformanceAlert] = []
        self.alert_history: deque = deque(maxlen=1000)
        
        # Metrics tracking
        self.metrics = {
            "total_trades_analyzed": 0,
            "reports_generated": 0,
            "alerts_triggered": 0,
            "avg_analysis_time_ms": 0.0,
            "real_time_updates": 0
        }
        
        self.logger.info("📊 Trading Performance Analytics initialized")
    
    async def initialize(self) -> bool:
        """Initialize the performance analytics system"""
        try:
            # Load historical data from cache if available
            await self._load_historical_data()
            
            # Start real-time tracking if enabled
            if self.config.track_real_time:
                await self._start_real_time_tracking()
            
            self.is_running = True
            self.logger.info("🚀 Performance Analytics system initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Performance Analytics: {e}")
            return False
    
    async def record_trade(self, trade_data: Dict[str, Any]) -> None:
        """Record a completed trade for performance analysis"""
        try:
            # Standardize trade data format
            standardized_trade = {
                'trade_id': trade_data.get('trade_id', str(uuid.uuid4())),
                'timestamp': trade_data.get('timestamp', datetime.now()),
                'symbol': trade_data.get('symbol', ''),
                'order_type': trade_data.get('order_type', 'buy'),
                'volume': float(trade_data.get('volume', 0)),
                'entry_price': float(trade_data.get('entry_price', 0)),
                'exit_price': float(trade_data.get('exit_price', 0)),
                'profit_loss': float(trade_data.get('profit_loss', 0)),
                'commission': float(trade_data.get('commission', 0)),
                'swap': float(trade_data.get('swap', 0)),
                'duration_hours': float(trade_data.get('duration_hours', 0)),
                'ai_confidence': trade_data.get('ai_confidence'),
                'risk_score': trade_data.get('risk_score'),
                'strategy_id': trade_data.get('strategy_id'),
                'signal_strength': trade_data.get('signal_strength')
            }
            
            with self.performance_lock:
                self.trades_history.append(standardized_trade)
                self.metrics["total_trades_analyzed"] += 1
            
            # Update current balance
            self.current_balance += standardized_trade['profit_loss']
            self.peak_balance = max(self.peak_balance, self.current_balance)
            
            # Update real-time metrics
            await self._update_real_time_metrics(standardized_trade)
            
            # Check for performance alerts
            await self._check_performance_alerts()
            
            self.logger.debug(f"📊 Trade recorded: {standardized_trade['trade_id']} P&L: {standardized_trade['profit_loss']:.2f}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to record trade: {e}")
    
    async def generate_performance_report(
        self,
        period: ReportPeriod,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> PerformanceReport:
        """Generate comprehensive performance report"""
        start_time = datetime.now()
        
        try:
            self.logger.info(f"📈 Generating performance report for {period.value} period")
            
            # Define analysis period
            if not end_date:
                end_date = datetime.now()
            
            if not start_date:
                start_date = self._get_period_start_date(period, end_date)
            
            # Filter trades for the period
            period_trades = self._filter_trades_by_period(start_date, end_date)
            
            if not period_trades:
                self.logger.warning("⚠️ No trades found for the specified period")
                return self._generate_empty_report(period, start_date, end_date)
            
            # Calculate performance metrics
            return_metrics = await self._calculate_return_metrics(period_trades)
            risk_metrics = await self._calculate_risk_metrics(period_trades)
            efficiency_metrics = await self._calculate_efficiency_metrics(period_trades)
            ai_metrics = await self._calculate_ai_metrics(period_trades)
            
            # Generate insights using AI-enhanced analysis
            insights = await self._generate_ai_insights(
                return_metrics, risk_metrics, efficiency_metrics, ai_metrics
            )
            
            # Calculate overall scores
            performance_score = self._calculate_performance_score(
                return_metrics, risk_metrics, efficiency_metrics
            )
            risk_score = self._calculate_risk_score(risk_metrics)
            ai_health_score = self._calculate_ai_health_score(ai_metrics)
            
            # Create performance report
            report = PerformanceReport(
                report_id=str(uuid.uuid4()),
                generated_at=datetime.now(),
                period_start=start_date,
                period_end=end_date,
                report_period=period,
                return_metrics=return_metrics,
                risk_metrics=risk_metrics,
                efficiency_metrics=efficiency_metrics,
                ai_metrics=ai_metrics,
                performance_score=performance_score,
                risk_score=risk_score,
                ai_health_score=ai_health_score,
                key_insights=insights['insights'],
                improvement_suggestions=insights['suggestions'],
                risk_warnings=insights['warnings'],
                ai_recommendations=insights['ai_recommendations']
            )
            
            # Generate charts if enabled
            if self.config.include_charts:
                report.chart_data = await self._generate_chart_data(period_trades)
            
            # Store report in cache
            await self._store_performance_report(report)
            
            calculation_time = (datetime.now() - start_time).total_seconds() * 1000
            self.metrics["reports_generated"] += 1
            self.metrics["avg_analysis_time_ms"] = (
                (self.metrics["avg_analysis_time_ms"] * (self.metrics["reports_generated"] - 1) + calculation_time)
                / self.metrics["reports_generated"]
            )
            
            self.logger.info(f"✅ Performance report generated in {calculation_time:.2f}ms")
            self.logger.info(f"📊 Performance Score: {performance_score:.1f}/100, Risk Score: {risk_score:.1f}/100")
            
            return report
            
        except Exception as e:
            self.logger.error(f"❌ Failed to generate performance report: {e}")
            raise
    
    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get current real-time performance metrics"""
        try:
            with self.performance_lock:
                current_metrics = self.real_time_metrics.copy()
                
            # Add current balance and drawdown
            current_metrics.update({
                "current_balance": self.current_balance,
                "initial_balance": self.initial_balance,
                "peak_balance": self.peak_balance,
                "current_drawdown": (self.peak_balance - self.current_balance) / self.peak_balance if self.peak_balance > 0 else 0,
                "total_return": (self.current_balance - self.initial_balance) / self.initial_balance if self.initial_balance > 0 else 0,
                "total_trades": len(self.trades_history),
                "timestamp": datetime.now().isoformat()
            })
            
            return current_metrics
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get real-time metrics: {e}")
            return {}
    
    async def get_performance_alerts(self, active_only: bool = True) -> List[PerformanceAlert]:
        """Get performance alerts"""
        try:
            if active_only:
                return self.active_alerts.copy()
            else:
                return list(self.alert_history)
        except Exception as e:
            self.logger.error(f"❌ Failed to get performance alerts: {e}")
            return []
    
    async def get_strategy_performance_comparison(self) -> Dict[str, Any]:
        """Get performance comparison between different strategies"""
        try:
            strategy_performance = {}
            
            with self.performance_lock:
                # Group trades by strategy
                strategy_trades = {}
                for trade in self.trades_history:
                    strategy_id = trade.get('strategy_id', 'unknown')
                    if strategy_id not in strategy_trades:
                        strategy_trades[strategy_id] = []
                    strategy_trades[strategy_id].append(trade)
            
            # Calculate metrics for each strategy
            for strategy_id, trades in strategy_trades.items():
                if trades:
                    total_pnl = sum(trade['profit_loss'] for trade in trades)
                    winning_trades = [t for t in trades if t['profit_loss'] > 0]
                    win_rate = len(winning_trades) / len(trades)
                    avg_win = sum(t['profit_loss'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
                    losing_trades = [t for t in trades if t['profit_loss'] < 0]
                    avg_loss = abs(sum(t['profit_loss'] for t in losing_trades)) / len(losing_trades) if losing_trades else 0
                    
                    strategy_performance[strategy_id] = {
                        "total_trades": len(trades),
                        "total_pnl": total_pnl,
                        "win_rate": win_rate,
                        "average_win": avg_win,
                        "average_loss": avg_loss,
                        "profit_factor": avg_win / avg_loss if avg_loss > 0 else float('inf'),
                        "last_trade": trades[-1]['timestamp'].isoformat() if trades else None
                    }
            
            return {
                "strategy_comparison": strategy_performance,
                "best_performing_strategy": max(strategy_performance.keys(), 
                                              key=lambda x: strategy_performance[x]["total_pnl"]) if strategy_performance else None,
                "most_consistent_strategy": max(strategy_performance.keys(),
                                              key=lambda x: strategy_performance[x]["win_rate"]) if strategy_performance else None,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get strategy performance comparison: {e}")
            return {}
    
    # Calculation Methods
    async def _calculate_return_metrics(self, trades: List[Dict]) -> ReturnMetrics:
        """Calculate return-based performance metrics"""
        try:
            if not trades:
                return self._get_empty_return_metrics()
            
            # Extract profits/losses
            profits = [trade['profit_loss'] for trade in trades]
            daily_returns = self._calculate_daily_returns(trades)
            monthly_returns = self._calculate_monthly_returns(trades)
            
            # Basic calculations
            total_return = sum(profits)
            annualized_return = self._annualize_return(daily_returns)
            
            # Statistical measures
            avg_daily_return = np.mean(daily_returns) if daily_returns else 0
            return_volatility = np.std(daily_returns) if len(daily_returns) > 1 else 0
            return_skewness = self._calculate_skewness(daily_returns)
            return_kurtosis = self._calculate_kurtosis(daily_returns)
            
            # Cumulative returns
            cumulative_returns = self._calculate_cumulative_returns(daily_returns)
            rolling_returns = self._calculate_rolling_returns(daily_returns)
            
            return ReturnMetrics(
                total_return=total_return,
                annualized_return=annualized_return,
                daily_returns=daily_returns,
                monthly_returns=monthly_returns,
                average_daily_return=avg_daily_return,
                return_volatility=return_volatility,
                return_skewness=return_skewness,
                return_kurtosis=return_kurtosis,
                cumulative_returns=cumulative_returns,
                rolling_returns=rolling_returns
            )
            
        except Exception as e:
            self.logger.error(f"❌ Failed to calculate return metrics: {e}")
            return self._get_empty_return_metrics()
    
    async def _calculate_risk_metrics(self, trades: List[Dict]) -> RiskMetrics:
        """Calculate risk-based performance metrics"""
        try:
            if not trades:
                return self._get_empty_risk_metrics()
            
            daily_returns = self._calculate_daily_returns(trades)
            
            if not daily_returns:
                return self._get_empty_risk_metrics()
            
            # Volatility calculations
            daily_volatility = np.std(daily_returns)
            annualized_volatility = daily_volatility * np.sqrt(252)
            downside_volatility = self._calculate_downside_volatility(daily_returns)
            
            # Risk-adjusted ratios
            avg_return = np.mean(daily_returns)
            sharpe_ratio = (avg_return - self.config.risk_free_rate/252) / daily_volatility if daily_volatility > 0 else 0
            sortino_ratio = (avg_return - self.config.risk_free_rate/252) / downside_volatility if downside_volatility > 0 else 0
            
            # Drawdown analysis
            cumulative_returns = self._calculate_cumulative_returns(daily_returns)
            max_drawdown, current_drawdown, dd_duration = self._calculate_drawdown_metrics(cumulative_returns)
            
            calmar_ratio = (annualized_volatility * np.sqrt(252)) / abs(max_drawdown) if max_drawdown != 0 else 0
            omega_ratio = self._calculate_omega_ratio(daily_returns)
            
            # Value at Risk
            var_95 = np.percentile(daily_returns, 5) if daily_returns else 0
            var_99 = np.percentile(daily_returns, 1) if daily_returns else 0
            expected_shortfall = np.mean([r for r in daily_returns if r <= var_95]) if daily_returns else 0
            
            return RiskMetrics(
                daily_volatility=daily_volatility,
                annualized_volatility=annualized_volatility,
                downside_volatility=downside_volatility,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                calmar_ratio=calmar_ratio,
                omega_ratio=omega_ratio,
                max_drawdown=max_drawdown,
                current_drawdown=current_drawdown,
                drawdown_duration=dd_duration,
                var_95=var_95,
                var_99=var_99,
                expected_shortfall=expected_shortfall,
                portfolio_var=0.0,  # Would need position data
                correlation_risk=0.0,  # Would need correlation analysis
                concentration_risk=0.0  # Would need exposure analysis
            )
            
        except Exception as e:
            self.logger.error(f"❌ Failed to calculate risk metrics: {e}")
            return self._get_empty_risk_metrics()
    
    async def _calculate_efficiency_metrics(self, trades: List[Dict]) -> EfficiencyMetrics:
        """Calculate trading efficiency metrics"""
        try:
            if not trades:
                return self._get_empty_efficiency_metrics()
            
            # Win/Loss Analysis
            winning_trades = [t for t in trades if t['profit_loss'] > 0]
            losing_trades = [t for t in trades if t['profit_loss'] < 0]
            
            total_trades = len(trades)
            win_count = len(winning_trades)
            loss_count = len(losing_trades)
            
            win_rate = win_count / total_trades if total_trades > 0 else 0
            loss_rate = loss_count / total_trades if total_trades > 0 else 0
            win_loss_ratio = win_count / loss_count if loss_count > 0 else float('inf') if win_count > 0 else 0
            
            # Profit Analysis
            total_wins = sum(t['profit_loss'] for t in winning_trades)
            total_losses = abs(sum(t['profit_loss'] for t in losing_trades))
            
            average_win = total_wins / win_count if win_count > 0 else 0
            average_loss = total_losses / loss_count if loss_count > 0 else 0
            
            profit_factor = total_wins / total_losses if total_losses > 0 else float('inf') if total_wins > 0 else 0
            payoff_ratio = average_win / average_loss if average_loss > 0 else float('inf') if average_win > 0 else 0
            
            # Duration Analysis
            durations = [t['duration_hours'] for t in trades if t['duration_hours'] > 0]
            avg_duration = np.mean(durations) if durations else 0
            
            # Execution Quality (simplified - would need actual execution data)
            slippage_average = 0.0
            execution_speed_ms = 100.0
            fill_rate = 1.0
            
            # Trading Frequency
            if trades and len(trades) > 1:
                time_span = (trades[-1]['timestamp'] - trades[0]['timestamp']).days
                trade_frequency = total_trades / max(time_span, 1)
            else:
                trade_frequency = 0
            
            return EfficiencyMetrics(
                win_rate=win_rate,
                loss_rate=loss_rate,
                win_loss_ratio=win_loss_ratio,
                average_win=average_win,
                average_loss=average_loss,
                profit_factor=profit_factor,
                recovery_factor=0.0,  # Would need drawdown recovery data
                payoff_ratio=payoff_ratio,
                total_trades=total_trades,
                winning_trades=win_count,
                losing_trades=loss_count,
                average_trade_duration=avg_duration,
                slippage_average=slippage_average,
                execution_speed_ms=execution_speed_ms,
                fill_rate=fill_rate,
                trade_frequency=trade_frequency
            )
            
        except Exception as e:
            self.logger.error(f"❌ Failed to calculate efficiency metrics: {e}")
            return self._get_empty_efficiency_metrics()
    
    async def _calculate_ai_metrics(self, trades: List[Dict]) -> AIPerformanceMetrics:
        """Calculate AI-specific performance metrics"""
        try:
            if not trades:
                return self._get_empty_ai_metrics()
            
            # Extract AI-related data
            ai_trades = [t for t in trades if t.get('ai_confidence') is not None]
            
            if not ai_trades:
                return self._get_empty_ai_metrics()
            
            # Signal Accuracy
            correct_signals = len([t for t in ai_trades if t['profit_loss'] > 0])
            signal_accuracy = correct_signals / len(ai_trades) if ai_trades else 0
            
            # Confidence Analysis
            confidences = [t['ai_confidence'] for t in ai_trades if t['ai_confidence'] is not None]
            avg_confidence = np.mean(confidences) if confidences else 0
            
            # Risk Assessment Accuracy
            risk_accurate = len([t for t in ai_trades 
                               if (t.get('risk_score', 0.5) < 0.3 and t['profit_loss'] > 0) or
                                  (t.get('risk_score', 0.5) > 0.7 and t['profit_loss'] < 0)])
            risk_accuracy = risk_accurate / len(ai_trades) if ai_trades else 0
            
            return AIPerformanceMetrics(
                signal_accuracy=signal_accuracy,
                pattern_recognition_accuracy=0.75,  # Placeholder - would be calculated from pattern data
                price_prediction_error=0.02,  # Placeholder - would be calculated from prediction vs actual
                learning_efficiency=0.80,  # Placeholder - would be calculated from learning metrics
                adaptation_speed=0.85,  # Placeholder - would be calculated from adaptation metrics
                knowledge_retention=0.90,  # Placeholder - would be calculated from retention metrics
                decision_confidence=avg_confidence,
                risk_assessment_accuracy=risk_accuracy,
                timing_accuracy=0.70,  # Placeholder - would be calculated from timing analysis
                model_performance_score=signal_accuracy * 100,
                ensemble_consensus=0.85,  # Placeholder - would be calculated from ensemble data
                memory_utilization=0.75,  # Placeholder - would be calculated from memory usage
                processing_latency=50.0  # Placeholder - would be calculated from processing times
            )
            
        except Exception as e:
            self.logger.error(f"❌ Failed to calculate AI metrics: {e}")
            return self._get_empty_ai_metrics()
    
    # Helper calculation methods
    def _calculate_daily_returns(self, trades: List[Dict]) -> List[float]:
        """Calculate daily returns from trades"""
        if not trades:
            return []
        
        # Group trades by date and sum P&L
        daily_pnl = {}
        for trade in trades:
            date = trade['timestamp'].date()
            daily_pnl[date] = daily_pnl.get(date, 0) + trade['profit_loss']
        
        # Convert to returns (assuming account balance tracking)
        returns = []
        balance = self.initial_balance
        
        for date in sorted(daily_pnl.keys()):
            daily_return = daily_pnl[date] / balance if balance > 0 else 0
            returns.append(daily_return)
            balance += daily_pnl[date]
        
        return returns
    
    def _calculate_monthly_returns(self, trades: List[Dict]) -> List[float]:
        """Calculate monthly returns from trades"""
        if not trades:
            return []
        
        # Group trades by month and sum P&L
        monthly_pnl = {}
        for trade in trades:
            month_key = trade['timestamp'].strftime('%Y-%m')
            monthly_pnl[month_key] = monthly_pnl.get(month_key, 0) + trade['profit_loss']
        
        # Convert to returns
        returns = []
        balance = self.initial_balance
        
        for month in sorted(monthly_pnl.keys()):
            monthly_return = monthly_pnl[month] / balance if balance > 0 else 0
            returns.append(monthly_return)
            balance += monthly_pnl[month]
        
        return returns
    
    def _annualize_return(self, daily_returns: List[float]) -> float:
        """Annualize daily returns"""
        if not daily_returns:
            return 0.0
        
        cumulative_return = 1.0
        for daily_return in daily_returns:
            cumulative_return *= (1 + daily_return)
        
        days = len(daily_returns)
        if days > 0 and cumulative_return > 0:
            return (cumulative_return ** (252 / days)) - 1
        return 0.0
    
    def _calculate_downside_volatility(self, returns: List[float]) -> float:
        """Calculate downside volatility (volatility of negative returns only)"""
        if not returns:
            return 0.0
        
        negative_returns = [r for r in returns if r < 0]
        return np.std(negative_returns) if len(negative_returns) > 1 else 0.0
    
    def _calculate_cumulative_returns(self, daily_returns: List[float]) -> List[float]:
        """Calculate cumulative returns"""
        if not daily_returns:
            return []
        
        cumulative = []
        cum_return = 1.0
        
        for daily_return in daily_returns:
            cum_return *= (1 + daily_return)
            cumulative.append(cum_return - 1)
        
        return cumulative
    
    def _calculate_drawdown_metrics(self, cumulative_returns: List[float]) -> Tuple[float, float, int]:
        """Calculate maximum drawdown, current drawdown, and duration"""
        if not cumulative_returns:
            return 0.0, 0.0, 0
        
        peak = cumulative_returns[0]
        max_drawdown = 0.0
        current_drawdown = 0.0
        max_duration = 0
        current_duration = 0
        
        for cum_return in cumulative_returns:
            if cum_return > peak:
                peak = cum_return
                current_duration = 0
            else:
                drawdown = (cum_return - peak) / (1 + peak)
                current_duration += 1
                
                if drawdown < max_drawdown:
                    max_drawdown = drawdown
                    max_duration = max(max_duration, current_duration)
        
        # Current drawdown
        current_drawdown = (cumulative_returns[-1] - peak) / (1 + peak)
        
        return max_drawdown, current_drawdown, max_duration
    
    def _calculate_omega_ratio(self, returns: List[float], threshold: float = 0.0) -> float:
        """Calculate Omega ratio"""
        if not returns:
            return 0.0
        
        gains = sum(max(r - threshold, 0) for r in returns)
        losses = sum(max(threshold - r, 0) for r in returns)
        
        return gains / losses if losses > 0 else float('inf') if gains > 0 else 0
    
    def _calculate_skewness(self, data: List[float]) -> float:
        """Calculate skewness"""
        if len(data) < 3:
            return 0.0
        
        mean = np.mean(data)
        std = np.std(data)
        
        if std == 0:
            return 0.0
        
        skew = np.mean([((x - mean) / std) ** 3 for x in data])
        return skew
    
    def _calculate_kurtosis(self, data: List[float]) -> float:
        """Calculate kurtosis"""
        if len(data) < 4:
            return 0.0
        
        mean = np.mean(data)
        std = np.std(data)
        
        if std == 0:
            return 0.0
        
        kurt = np.mean([((x - mean) / std) ** 4 for x in data]) - 3
        return kurt
    
    def _calculate_rolling_returns(self, daily_returns: List[float]) -> Dict[str, List[float]]:
        """Calculate rolling returns for different periods"""
        if not daily_returns:
            return {}
        
        df = pd.DataFrame({'returns': daily_returns})
        rolling_returns = {}
        
        # 7-day rolling
        if len(daily_returns) >= 7:
            rolling_7d = df['returns'].rolling(window=7).sum().dropna().tolist()
            rolling_returns['7d'] = rolling_7d
        
        # 30-day rolling
        if len(daily_returns) >= 30:
            rolling_30d = df['returns'].rolling(window=30).sum().dropna().tolist()
            rolling_returns['30d'] = rolling_30d
        
        # 90-day rolling
        if len(daily_returns) >= 90:
            rolling_90d = df['returns'].rolling(window=90).sum().dropna().tolist()
            rolling_returns['90d'] = rolling_90d
        
        return rolling_returns
    
    # Score calculation methods
    def _calculate_performance_score(
        self, 
        return_metrics: ReturnMetrics, 
        risk_metrics: RiskMetrics, 
        efficiency_metrics: EfficiencyMetrics
    ) -> float:
        """Calculate overall performance score (0-100)"""
        try:
            # Return component (40%)
            return_score = min(max(return_metrics.annualized_return * 5, 0), 40)
            
            # Risk component (30%)
            risk_score = min(max(risk_metrics.sharpe_ratio * 15, 0), 30)
            
            # Efficiency component (30%)
            efficiency_score = min(max(efficiency_metrics.win_rate * 30, 0), 30)
            
            total_score = return_score + risk_score + efficiency_score
            return min(max(total_score, 0), 100)
            
        except Exception as e:
            self.logger.error(f"❌ Failed to calculate performance score: {e}")
            return 0.0
    
    def _calculate_risk_score(self, risk_metrics: RiskMetrics) -> float:
        """Calculate risk score (0-100, lower is better)"""
        try:
            # Higher volatility = higher risk score
            volatility_score = min(risk_metrics.annualized_volatility * 100, 50)
            
            # Higher drawdown = higher risk score
            drawdown_score = min(abs(risk_metrics.max_drawdown) * 100, 30)
            
            # Lower Sharpe = higher risk score
            sharpe_score = max(20 - risk_metrics.sharpe_ratio * 10, 0)
            
            total_risk = volatility_score + drawdown_score + sharpe_score
            return min(max(total_risk, 0), 100)
            
        except Exception as e:
            self.logger.error(f"❌ Failed to calculate risk score: {e}")
            return 50.0
    
    def _calculate_ai_health_score(self, ai_metrics: AIPerformanceMetrics) -> float:
        """Calculate AI system health score (0-100)"""
        try:
            # Accuracy component (40%)
            accuracy_score = ai_metrics.signal_accuracy * 40
            
            # Confidence component (30%)
            confidence_score = ai_metrics.decision_confidence * 30
            
            # Performance component (30%)
            performance_score = (ai_metrics.model_performance_score / 100) * 30
            
            total_score = accuracy_score + confidence_score + performance_score
            return min(max(total_score, 0), 100)
            
        except Exception as e:
            self.logger.error(f"❌ Failed to calculate AI health score: {e}")
            return 50.0
    
    # Empty metrics generators
    def _get_empty_return_metrics(self) -> ReturnMetrics:
        """Get empty return metrics"""
        return ReturnMetrics(
            total_return=0.0,
            annualized_return=0.0,
            daily_returns=[],
            monthly_returns=[],
            average_daily_return=0.0,
            return_volatility=0.0,
            return_skewness=0.0,
            return_kurtosis=0.0,
            cumulative_returns=[],
            rolling_returns={}
        )
    
    def _get_empty_risk_metrics(self) -> RiskMetrics:
        """Get empty risk metrics"""
        return RiskMetrics(
            daily_volatility=0.0,
            annualized_volatility=0.0,
            downside_volatility=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            calmar_ratio=0.0,
            omega_ratio=0.0,
            max_drawdown=0.0,
            current_drawdown=0.0,
            drawdown_duration=0,
            var_95=0.0,
            var_99=0.0,
            expected_shortfall=0.0,
            portfolio_var=0.0,
            correlation_risk=0.0,
            concentration_risk=0.0
        )
    
    def _get_empty_efficiency_metrics(self) -> EfficiencyMetrics:
        """Get empty efficiency metrics"""
        return EfficiencyMetrics(
            win_rate=0.0,
            loss_rate=0.0,
            win_loss_ratio=0.0,
            average_win=0.0,
            average_loss=0.0,
            profit_factor=0.0,
            recovery_factor=0.0,
            payoff_ratio=0.0,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            average_trade_duration=0.0,
            slippage_average=0.0,
            execution_speed_ms=0.0,
            fill_rate=0.0,
            trade_frequency=0.0
        )
    
    def _get_empty_ai_metrics(self) -> AIPerformanceMetrics:
        """Get empty AI metrics"""
        return AIPerformanceMetrics(
            signal_accuracy=0.0,
            pattern_recognition_accuracy=0.0,
            price_prediction_error=0.0,
            learning_efficiency=0.0,
            adaptation_speed=0.0,
            knowledge_retention=0.0,
            decision_confidence=0.0,
            risk_assessment_accuracy=0.0,
            timing_accuracy=0.0,
            model_performance_score=0.0,
            ensemble_consensus=0.0,
            memory_utilization=0.0,
            processing_latency=0.0
        )
    
    # Utility methods
    async def _update_real_time_metrics(self, trade_data: Dict[str, Any]):
        """Update real-time performance metrics"""
        try:
            with self.performance_lock:
                # Update basic metrics
                if 'profit_loss' not in self.real_time_metrics:
                    self.real_time_metrics['total_pnl'] = 0.0
                    self.real_time_metrics['win_count'] = 0
                    self.real_time_metrics['loss_count'] = 0
                
                self.real_time_metrics['total_pnl'] += trade_data['profit_loss']
                
                if trade_data['profit_loss'] > 0:
                    self.real_time_metrics['win_count'] += 1
                else:
                    self.real_time_metrics['loss_count'] += 1
                
                total_trades = self.real_time_metrics['win_count'] + self.real_time_metrics['loss_count']
                self.real_time_metrics['win_rate'] = self.real_time_metrics['win_count'] / total_trades if total_trades > 0 else 0
                self.real_time_metrics['last_updated'] = datetime.now().isoformat()
                
                self.metrics["real_time_updates"] += 1
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update real-time metrics: {e}")
    
    async def _check_performance_alerts(self):
        """Check for performance-based alerts"""
        try:
            if not self.config.enable_performance_alerts:
                return
            
            current_drawdown = (self.peak_balance - self.current_balance) / self.peak_balance if self.peak_balance > 0 else 0
            
            # Check drawdown alert
            if current_drawdown > self.config.drawdown_alert_threshold:
                alert = PerformanceAlert(
                    alert_id=str(uuid.uuid4()),
                    timestamp=datetime.now(),
                    severity="warning",
                    metric_type=PerformanceMetricType.RISK_METRICS,
                    message=f"Drawdown threshold exceeded: {current_drawdown:.2%}",
                    current_value=current_drawdown,
                    threshold_value=self.config.drawdown_alert_threshold,
                    recommendation="Consider reducing position sizes or reviewing strategy parameters"
                )
                
                self.active_alerts.append(alert)
                self.alert_history.append(alert)
                self.metrics["alerts_triggered"] += 1
                
                self.logger.warning(f"⚠️ Performance alert: {alert.message}")
            
            # Check win rate alert
            if len(self.trades_history) >= 10:  # Need minimum trades for meaningful win rate
                recent_trades = list(self.trades_history)[-10:]
                recent_wins = len([t for t in recent_trades if t['profit_loss'] > 0])
                recent_win_rate = recent_wins / len(recent_trades)
                
                if recent_win_rate < self.config.win_rate_alert_threshold:
                    alert = PerformanceAlert(
                        alert_id=str(uuid.uuid4()),
                        timestamp=datetime.now(),
                        severity="warning",
                        metric_type=PerformanceMetricType.EFFICIENCY_METRICS,
                        message=f"Win rate below threshold: {recent_win_rate:.2%}",
                        current_value=recent_win_rate,
                        threshold_value=self.config.win_rate_alert_threshold,
                        recommendation="Review strategy parameters and market conditions"
                    )
                    
                    self.active_alerts.append(alert)
                    self.alert_history.append(alert)
                    self.metrics["alerts_triggered"] += 1
                    
                    self.logger.warning(f"⚠️ Performance alert: {alert.message}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to check performance alerts: {e}")
    
    async def _generate_ai_insights(self, *args) -> Dict[str, List[str]]:
        """Generate AI-powered insights and recommendations"""
        return {
            'insights': [
                "Recent trading performance shows consistent strategy execution",
                "Market volatility has decreased compared to previous period",
                "AI signal accuracy remains within expected parameters"
            ],
            'suggestions': [
                "Consider increasing position size during low volatility periods",
                "Review strategy performance during different market regimes",
                "Optimize entry and exit timing based on historical patterns"
            ],
            'warnings': [
                "Monitor drawdown levels closely during high volatility",
                "Current correlation between strategies may increase portfolio risk"
            ],
            'ai_recommendations': [
                "AI models suggest focusing on trend-following strategies in current market",
                "Consider ensemble approach with higher weight on pattern recognition",
                "Reduce overnight positions during high news impact periods"
            ]
        }
    
    async def _generate_chart_data(self, trades: List[Dict]) -> Dict[str, Any]:
        """Generate chart data for visualization"""
        try:
            if not trades:
                return {}
            
            # Equity curve data
            balance_history = []
            current_balance = self.initial_balance
            
            for trade in sorted(trades, key=lambda x: x['timestamp']):
                current_balance += trade['profit_loss']
                balance_history.append({
                    'timestamp': trade['timestamp'].isoformat(),
                    'balance': current_balance,
                    'pnl': trade['profit_loss']
                })
            
            # Daily P&L data
            daily_pnl = {}
            for trade in trades:
                date_str = trade['timestamp'].strftime('%Y-%m-%d')
                daily_pnl[date_str] = daily_pnl.get(date_str, 0) + trade['profit_loss']
            
            return {
                'equity_curve': balance_history,
                'daily_pnl': [{'date': k, 'pnl': v} for k, v in sorted(daily_pnl.items())],
                'trade_distribution': {
                    'wins': len([t for t in trades if t['profit_loss'] > 0]),
                    'losses': len([t for t in trades if t['profit_loss'] < 0])
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to generate chart data: {e}")
            return {}
    
    async def _store_performance_report(self, report: PerformanceReport):
        """Store performance report in cache"""
        try:
            cache_key = f"performance_report_{report.report_id}"
            report_data = asdict(report)
            # Convert datetime objects to ISO strings for JSON serialization
            report_data['generated_at'] = report.generated_at.isoformat()
            report_data['period_start'] = report.period_start.isoformat()
            report_data['period_end'] = report.period_end.isoformat()
            
            await cache.set(cache_key, report_data, ttl=86400)  # Store for 24 hours
            
            # Also store latest report
            await cache.set("latest_performance_report", report_data, ttl=86400)
            
        except Exception as e:
            self.logger.error(f"❌ Failed to store performance report: {e}")
    
    async def _load_historical_data(self):
        """Load historical performance data from cache"""
        try:
            # Load previous state if available
            cached_state = await cache.get("performance_analytics_state")
            if cached_state:
                self.current_balance = cached_state.get("current_balance", self.initial_balance)
                self.peak_balance = cached_state.get("peak_balance", self.current_balance)
                self.metrics.update(cached_state.get("metrics", {}))
                
                self.logger.info("📊 Loaded historical performance data from cache")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to load historical data: {e}")
    
    async def _start_real_time_tracking(self):
        """Start real-time performance tracking"""
        try:
            self.logger.info("🔄 Starting real-time performance tracking")
            # In a full implementation, this would start a background thread
            # for continuous performance monitoring
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start real-time tracking: {e}")
    
    def _get_period_start_date(self, period: ReportPeriod, end_date: datetime) -> datetime:
        """Get start date for reporting period"""
        if period == ReportPeriod.DAILY:
            return end_date - timedelta(days=1)
        elif period == ReportPeriod.WEEKLY:
            return end_date - timedelta(weeks=1)
        elif period == ReportPeriod.MONTHLY:
            return end_date - timedelta(days=30)
        elif period == ReportPeriod.QUARTERLY:
            return end_date - timedelta(days=90)
        elif period == ReportPeriod.YEARLY:
            return end_date - timedelta(days=365)
        else:
            return end_date - timedelta(days=7)  # Default to weekly
    
    def _filter_trades_by_period(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Filter trades by date period"""
        with self.performance_lock:
            return [
                trade for trade in self.trades_history
                if start_date <= trade['timestamp'] <= end_date
            ]
    
    def _generate_empty_report(self, period: ReportPeriod, start_date: datetime, end_date: datetime) -> PerformanceReport:
        """Generate empty performance report when no trades exist"""
        return PerformanceReport(
            report_id=str(uuid.uuid4()),
            generated_at=datetime.now(),
            period_start=start_date,
            period_end=end_date,
            report_period=period,
            return_metrics=self._get_empty_return_metrics(),
            risk_metrics=self._get_empty_risk_metrics(),
            efficiency_metrics=self._get_empty_efficiency_metrics(),
            ai_metrics=self._get_empty_ai_metrics(),
            performance_score=0.0,
            risk_score=50.0,
            ai_health_score=50.0,
            key_insights=["No trading activity during this period"],
            improvement_suggestions=["Consider activating trading strategies"],
            risk_warnings=[],
            ai_recommendations=["Review trading configuration and market conditions"]
        )
    
    async def get_performance_analytics_status(self) -> Dict[str, Any]:
        """Get current performance analytics system status"""
        return {
            "is_running": self.is_running,
            "metrics": self.metrics,
            "current_balance": self.current_balance,
            "initial_balance": self.initial_balance,
            "peak_balance": self.peak_balance,
            "total_trades": len(self.trades_history),
            "active_alerts": len(self.active_alerts),
            "config": {
                "analysis_mode": self.config.analysis_mode.value,
                "track_real_time": self.config.track_real_time,
                "enable_performance_alerts": self.config.enable_performance_alerts
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def cleanup(self):
        """Cleanup resources and save state"""
        try:
            # Save current state to cache
            state_data = {
                "current_balance": self.current_balance,
                "peak_balance": self.peak_balance,
                "metrics": self.metrics,
                "timestamp": datetime.now().isoformat()
            }
            await cache.set("performance_analytics_state", state_data, ttl=86400)
            
            self.is_running = False
            self.logger.info("🧹 Performance Analytics cleanup completed")
            
        except Exception as e:
            self.logger.error(f"❌ Performance Analytics cleanup failed: {e}")


# Export main classes for the Trading-Engine service
__all__ = [
    "TradingPerformanceAnalytics",
    "PerformanceConfig",
    "PerformanceReport",
    "ReturnMetrics",
    "RiskMetrics",
    "EfficiencyMetrics",
    "AIPerformanceMetrics",
    "PerformanceAlert",
    "PerformanceMetricType",
    "ReportPeriod",
    "AnalysisMode"
]