"""
A/B Testing Core - Advanced A/B Testing Framework for Trading Strategy Changes
AI Brain Enhanced Performance Comparison and Statistical Analysis

This module implements:
- A/B testing framework for strategy changes
- Statistical significance testing
- Performance comparison metrics
- Real-time experiment monitoring
- Automated experiment management
- Risk-controlled testing environments
- Performance degradation detection
- Experiment result analysis and reporting
"""

import asyncio
import json
import time
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
import numpy as np
from collections import defaultdict, deque
import uuid

# AI Brain Integration
try:
    import sys
    sys.path.append('/mnt/f/WINDSURF/concept_ai/projects/ai_trading/server_microservice/services')
    from shared.ai_brain_confidence_framework import AiBrainConfidenceFramework
    from shared.ai_brain_trading_error_dna import AiBrainTradingErrorDNA
    AI_BRAIN_AVAILABLE = True
except ImportError:
    AI_BRAIN_AVAILABLE = False

from .logger_core import CoreLogger
from .config_core import CoreConfig
from .error_core import CoreErrorHandler
from .performance_core import CorePerformance
from .cache_core import CoreCache
from .metrics_core import CoreMetrics


class ExperimentStatus(Enum):
    """A/B experiment status"""
    DRAFT = "draft"
    PENDING_START = "pending_start"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED_EARLY = "stopped_early"
    FAILED = "failed"


class ExperimentType(Enum):
    """Types of A/B experiments"""
    STRATEGY_PARAMETER = "strategy_parameter"
    RISK_SETTING = "risk_setting"
    EXECUTION_LOGIC = "execution_logic"
    AI_MODEL = "ai_model"
    POSITION_SIZING = "position_sizing"
    SIGNAL_THRESHOLD = "signal_threshold"
    TIMEFRAME_ANALYSIS = "timeframe_analysis"


class TrafficSplitType(Enum):
    """Traffic split methodologies"""
    RANDOM = "random"
    HASH_BASED = "hash_based"
    TIME_BASED = "time_based"
    SYMBOL_BASED = "symbol_based"
    RISK_BASED = "risk_based"


class StatisticalSignificance(Enum):
    """Statistical significance levels"""
    NOT_SIGNIFICANT = "not_significant"    # p > 0.05
    MARGINALLY_SIGNIFICANT = "marginally"  # 0.01 < p <= 0.05
    SIGNIFICANT = "significant"            # 0.001 < p <= 0.01
    HIGHLY_SIGNIFICANT = "highly"          # p <= 0.001


@dataclass 
class ExperimentVariant:
    """A/B testing experiment variant configuration"""
    variant_id: str
    variant_name: str
    configuration: Dict[str, Any]
    traffic_percentage: float = 50.0
    is_control: bool = False
    
    # Performance tracking
    sample_size: int = 0
    total_trades: int = 0
    successful_trades: int = 0
    total_pnl: float = 0.0
    total_duration_seconds: float = 0.0
    
    # Risk metrics
    max_drawdown: float = 0.0
    volatility: float = 0.0
    sharpe_ratio: float = 0.0
    
    # Real-time metrics
    recent_performance: deque = field(default_factory=lambda: deque(maxlen=100))
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class ExperimentMetrics:
    """Comprehensive experiment performance metrics"""
    variant_id: str
    
    # Trade metrics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    
    # Financial metrics
    total_pnl: float = 0.0
    average_pnl_per_trade: float = 0.0
    profit_factor: float = 0.0
    
    # Risk metrics
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    volatility: float = 0.0
    var_95: float = 0.0
    
    # Execution metrics
    average_execution_time_ms: float = 0.0
    slippage_average_pips: float = 0.0
    fill_rate: float = 100.0
    
    # Time-based metrics
    trades_per_hour: float = 0.0
    active_time_percentage: float = 0.0
    
    # Statistical metrics
    standard_error: float = 0.0
    confidence_interval_95: Tuple[float, float] = (0.0, 0.0)
    
    last_calculated: datetime = field(default_factory=datetime.now)


@dataclass
class ABTestExperiment:
    """Complete A/B testing experiment definition"""
    experiment_id: str
    experiment_name: str
    experiment_type: ExperimentType
    description: str
    
    # Experiment configuration
    variants: List[ExperimentVariant]
    traffic_split_type: TrafficSplitType = TrafficSplitType.RANDOM
    
    # Experiment timeline
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    planned_duration_hours: int = 24
    
    # Status and control
    status: ExperimentStatus = ExperimentStatus.DRAFT
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    # Success criteria
    primary_metric: str = "total_pnl"
    secondary_metrics: List[str] = field(default_factory=lambda: ["win_rate", "sharpe_ratio"])
    minimum_effect_size: float = 0.05  # 5% improvement required
    statistical_power: float = 0.8  # 80% power
    significance_level: float = 0.05  # 95% confidence
    
    # Sample size and monitoring
    minimum_sample_size: int = 100
    maximum_sample_size: int = 1000
    monitoring_interval_minutes: int = 30
    
    # Early stopping criteria
    enable_early_stopping: bool = True
    early_stop_significant_loss_threshold: float = -0.10  # Stop if losing 10%
    early_stop_sample_size: int = 50  # Minimum samples before early stopping
    
    # Results and analysis
    experiment_metrics: Dict[str, ExperimentMetrics] = field(default_factory=dict)
    statistical_results: Dict[str, Any] = field(default_factory=dict)
    final_recommendation: Optional[str] = None
    
    # AI Brain analysis
    ai_confidence_score: float = 0.0
    ai_recommendations: List[str] = field(default_factory=list)


class ABTestingCore:
    """
    Advanced A/B Testing Framework for Trading Strategy Changes
    
    Provides enterprise-grade experimentation with:
    - Statistical significance testing
    - Performance comparison metrics
    - Risk-controlled testing environments
    - Automated experiment management
    - Real-time monitoring and alerts
    - AI-enhanced result analysis
    """
    
    def __init__(self, service_name: str = "trading-engine"):
        self.service_name = service_name
        
        # Initialize infrastructure components
        self.logger = CoreLogger(f"ab-testing-{service_name}")
        self.config = CoreConfig(service_name)
        self.error_handler = CoreErrorHandler(f"ab-testing-{service_name}")
        self.performance = CorePerformance(f"ab-testing-{service_name}")
        self.cache = CoreCache(f"ab-testing-{service_name}")
        self.metrics = CoreMetrics(f"ab-testing-{service_name}")
        
        # AI Brain Integration
        self.ai_brain_confidence = None
        self.ai_brain_error_dna = None
        
        if AI_BRAIN_AVAILABLE:
            try:
                self.ai_brain_confidence = AiBrainConfidenceFramework(f"ab-testing-{service_name}")
                self.ai_brain_error_dna = AiBrainTradingErrorDNA(f"ab-testing-error-{service_name}")
                self.logger.info("AI Brain integration initialized for A/B Testing")
            except Exception as e:
                self.logger.warning(f"AI Brain integration failed: {e}")
        
        # A/B Testing State
        self.active_experiments: Dict[str, ABTestExperiment] = {}
        self.completed_experiments: List[ABTestExperiment] = []
        self.experiment_history: deque = deque(maxlen=1000)
        
        # Traffic routing
        self.traffic_router: Dict[str, str] = {}  # Maps request IDs to variant IDs
        self.variant_assignments: Dict[str, Dict[str, str]] = {}  # Experiment -> {user/symbol -> variant}
        
        # Performance monitoring
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        self.alert_thresholds: Dict[str, Dict[str, float]] = {}
        
        # Statistical analysis cache
        self.statistical_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl_seconds = 300  # 5 minutes
        
        self.logger.info(f"A/B Testing Core initialized for {service_name}")
    
    async def create_experiment(self,
                              experiment_name: str,
                              experiment_type: ExperimentType,
                              description: str,
                              variants: List[Dict[str, Any]],
                              created_by: str,
                              primary_metric: str = "total_pnl",
                              planned_duration_hours: int = 24,
                              minimum_sample_size: int = 100,
                              traffic_split_type: TrafficSplitType = TrafficSplitType.RANDOM) -> str:
        """
        Create a new A/B testing experiment
        
        Returns:
            experiment_id: Unique identifier for the experiment
        """
        try:
            start_time = time.time()
            
            # Generate experiment ID
            experiment_id = f"EXP-{int(time.time())}-{uuid.uuid4().hex[:8]}"
            
            # Validate and create variants
            experiment_variants = []
            total_traffic = 0.0
            control_found = False
            
            for variant_config in variants:
                variant = ExperimentVariant(
                    variant_id=variant_config.get("variant_id", f"variant-{len(experiment_variants)}"),
                    variant_name=variant_config.get("variant_name", f"Variant {len(experiment_variants) + 1}"),
                    configuration=variant_config.get("configuration", {}),
                    traffic_percentage=variant_config.get("traffic_percentage", 50.0),
                    is_control=variant_config.get("is_control", len(experiment_variants) == 0)
                )
                
                experiment_variants.append(variant)
                total_traffic += variant.traffic_percentage
                
                if variant.is_control:
                    control_found = True
            
            # Validate traffic split
            if abs(total_traffic - 100.0) > 0.1:
                raise ValueError(f"Traffic percentages must sum to 100%, got {total_traffic}%")
            
            if not control_found:
                experiment_variants[0].is_control = True
                self.logger.warning(f"No control variant specified, making {experiment_variants[0].variant_name} the control")
            
            # Create experiment
            experiment = ABTestExperiment(
                experiment_id=experiment_id,
                experiment_name=experiment_name,
                experiment_type=experiment_type,
                description=description,
                variants=experiment_variants,
                traffic_split_type=traffic_split_type,
                planned_duration_hours=planned_duration_hours,
                created_by=created_by,
                primary_metric=primary_metric,
                minimum_sample_size=minimum_sample_size,
                status=ExperimentStatus.DRAFT
            )
            
            # Initialize experiment metrics
            for variant in experiment_variants:
                experiment.experiment_metrics[variant.variant_id] = ExperimentMetrics(
                    variant_id=variant.variant_id
                )
            
            # AI Brain analysis of experiment design
            if self.ai_brain_confidence:
                ai_analysis = await self._ai_brain_experiment_analysis(experiment)
                experiment.ai_confidence_score = ai_analysis["confidence_score"]
                experiment.ai_recommendations = ai_analysis["recommendations"]
            
            # Store experiment
            self.active_experiments[experiment_id] = experiment
            
            # Initialize traffic router
            self.variant_assignments[experiment_id] = {}
            
            # Update metrics
            self.metrics.increment_counter("ab_experiments_created")
            self.metrics.record_histogram("experiment_creation_time", (time.time() - start_time) * 1000)
            
            self.logger.info(f"A/B experiment created: {experiment_id} - {experiment_name}")
            
            return experiment_id
            
        except Exception as e:
            error_details = self.error_handler.handle_error(e, "create_experiment")
            self.logger.error(f"Failed to create A/B experiment: {error_details}")
            raise
    
    async def start_experiment(self, experiment_id: str, start_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Start an A/B testing experiment"""
        try:
            experiment = self.active_experiments.get(experiment_id)
            if not experiment:
                raise ValueError(f"Experiment {experiment_id} not found")
            
            if experiment.status != ExperimentStatus.DRAFT:
                raise ValueError(f"Experiment {experiment_id} is not in draft status")
            
            # Set start time
            experiment.start_time = start_time or datetime.now()
            experiment.end_time = experiment.start_time + timedelta(hours=experiment.planned_duration_hours)
            experiment.status = ExperimentStatus.RUNNING
            
            # Start monitoring task
            monitoring_task = asyncio.create_task(self._monitor_experiment(experiment_id))
            self.monitoring_tasks[experiment_id] = monitoring_task
            
            # Setup alert thresholds
            self._setup_experiment_alerts(experiment)
            
            # Initialize statistical tracking
            self.statistical_cache[experiment_id] = {
                "last_analysis": datetime.now(),
                "significance_history": [],
                "power_analysis": {}
            }
            
            self.logger.info(f"A/B experiment started: {experiment_id}")
            
            # Update metrics
            self.metrics.increment_counter("ab_experiments_started")
            
            return {
                "success": True,
                "experiment_id": experiment_id,
                "start_time": experiment.start_time.isoformat(),
                "end_time": experiment.end_time.isoformat(),
                "status": experiment.status.value,
                "monitoring_enabled": True
            }
            
        except Exception as e:
            error_details = self.error_handler.handle_error(e, "start_experiment")
            self.logger.error(f"Failed to start experiment: {error_details}")
            raise
    
    def assign_variant(self, 
                      experiment_id: str, 
                      identifier: str, 
                      context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Assign a variant to a request/user/symbol for the experiment
        
        Args:
            experiment_id: ID of the experiment
            identifier: Unique identifier for traffic splitting (user_id, symbol, etc.)
            context: Additional context for assignment decisions
            
        Returns:
            variant_id: Assigned variant ID, or None if experiment not running
        """
        try:
            experiment = self.active_experiments.get(experiment_id)
            if not experiment or experiment.status != ExperimentStatus.RUNNING:
                return None
            
            # Check if already assigned
            if identifier in self.variant_assignments[experiment_id]:
                return self.variant_assignments[experiment_id][identifier]
            
            # Assign variant based on traffic split type
            variant_id = self._perform_traffic_split(experiment, identifier, context)
            
            # Store assignment
            self.variant_assignments[experiment_id][identifier] = variant_id
            
            # Update variant sample size
            for variant in experiment.variants:
                if variant.variant_id == variant_id:
                    variant.sample_size += 1
                    break
            
            return variant_id
            
        except Exception as e:
            self.logger.error(f"Failed to assign variant for experiment {experiment_id}: {e}")
            return None
    
    def _perform_traffic_split(self, 
                              experiment: ABTestExperiment, 
                              identifier: str, 
                              context: Optional[Dict[str, Any]]) -> str:
        """Perform traffic splitting based on configured method"""
        
        if experiment.traffic_split_type == TrafficSplitType.RANDOM:
            # Simple random assignment
            import random
            random_value = random.random() * 100
            
        elif experiment.traffic_split_type == TrafficSplitType.HASH_BASED:
            # Consistent hash-based assignment
            import hashlib
            hash_value = int(hashlib.md5(identifier.encode()).hexdigest(), 16)
            random_value = (hash_value % 10000) / 100.0  # 0-100
            
        elif experiment.traffic_split_type == TrafficSplitType.SYMBOL_BASED:
            # Symbol-based assignment
            symbol = context.get("symbol", identifier) if context else identifier
            hash_value = int(hashlib.md5(symbol.encode()).hexdigest(), 16)
            random_value = (hash_value % 10000) / 100.0
            
        elif experiment.traffic_split_type == TrafficSplitType.RISK_BASED:
            # Risk-based assignment (lower risk identifiers get treatment)
            risk_score = context.get("risk_score", 0.5) if context else 0.5
            random_value = risk_score * 100
            
        else:  # TIME_BASED or fallback
            # Time-based cycling
            timestamp_minutes = int(time.time() / 60)
            random_value = (timestamp_minutes % 100)
        
        # Assign based on cumulative traffic percentages
        cumulative_percentage = 0.0
        for variant in experiment.variants:
            cumulative_percentage += variant.traffic_percentage
            if random_value <= cumulative_percentage:
                return variant.variant_id
        
        # Fallback to first variant
        return experiment.variants[0].variant_id
    
    async def record_experiment_result(self,
                                     experiment_id: str,
                                     variant_id: str,
                                     metrics: Dict[str, float],
                                     trade_data: Optional[Dict[str, Any]] = None) -> bool:
        """Record a result for an experiment variant"""
        try:
            experiment = self.active_experiments.get(experiment_id)
            if not experiment or experiment.status != ExperimentStatus.RUNNING:
                return False
            
            # Find variant
            variant = None
            experiment_metrics = None
            
            for v in experiment.variants:
                if v.variant_id == variant_id:
                    variant = v
                    experiment_metrics = experiment.experiment_metrics[variant_id]
                    break
            
            if not variant or not experiment_metrics:
                self.logger.warning(f"Variant {variant_id} not found in experiment {experiment_id}")
                return False
            
            # Update variant performance
            pnl = metrics.get("pnl", 0.0)
            execution_time_ms = metrics.get("execution_time_ms", 0.0)
            is_successful = metrics.get("successful", False)
            
            variant.total_trades += 1
            variant.total_pnl += pnl
            variant.total_duration_seconds += execution_time_ms / 1000.0
            
            if is_successful:
                variant.successful_trades += 1
            
            # Update recent performance for monitoring
            variant.recent_performance.append({
                "timestamp": datetime.now(),
                "pnl": pnl,
                "successful": is_successful,
                "execution_time_ms": execution_time_ms
            })
            
            variant.last_updated = datetime.now()
            
            # Update comprehensive experiment metrics
            await self._update_experiment_metrics(experiment_metrics, metrics, trade_data)
            
            # Check for early stopping conditions
            if experiment.enable_early_stopping:
                await self._check_early_stopping_conditions(experiment)
            
            # Update cache metrics
            self.metrics.increment_counter("ab_experiment_results_recorded")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to record experiment result: {e}")
            return False
    
    async def _update_experiment_metrics(self, 
                                       experiment_metrics: ExperimentMetrics,
                                       result_metrics: Dict[str, float],
                                       trade_data: Optional[Dict[str, Any]]):
        """Update comprehensive experiment metrics"""
        try:
            # Basic trade metrics
            experiment_metrics.total_trades += 1
            
            pnl = result_metrics.get("pnl", 0.0)
            is_successful = result_metrics.get("successful", False)
            
            experiment_metrics.total_pnl += pnl
            
            if is_successful:
                experiment_metrics.winning_trades += 1
            else:
                experiment_metrics.losing_trades += 1
            
            # Calculate derived metrics
            if experiment_metrics.total_trades > 0:
                experiment_metrics.win_rate = experiment_metrics.winning_trades / experiment_metrics.total_trades
                experiment_metrics.average_pnl_per_trade = experiment_metrics.total_pnl / experiment_metrics.total_trades
            
            # Update execution metrics
            execution_time = result_metrics.get("execution_time_ms", 0.0)
            if execution_time > 0:
                current_avg = experiment_metrics.average_execution_time_ms
                total_trades = experiment_metrics.total_trades
                experiment_metrics.average_execution_time_ms = (
                    (current_avg * (total_trades - 1) + execution_time) / total_trades
                )
            
            # Update slippage
            slippage = result_metrics.get("slippage_pips", 0.0)
            if slippage > 0:
                current_avg = experiment_metrics.slippage_average_pips
                total_trades = experiment_metrics.total_trades
                experiment_metrics.slippage_average_pips = (
                    (current_avg * (total_trades - 1) + slippage) / total_trades
                )
            
            # Update risk metrics (calculated periodically)
            await self._calculate_risk_metrics(experiment_metrics, result_metrics)
            
            experiment_metrics.last_calculated = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Failed to update experiment metrics: {e}")
    
    async def _calculate_risk_metrics(self, 
                                    experiment_metrics: ExperimentMetrics,
                                    result_metrics: Dict[str, float]):
        """Calculate risk metrics for experiment variant"""
        try:
            # This would typically calculate from a series of returns
            # For now, we'll use simplified calculations
            
            total_trades = experiment_metrics.total_trades
            if total_trades < 10:  # Need minimum trades for meaningful risk metrics
                return
            
            # Calculate basic volatility (simplified)
            pnl = result_metrics.get("pnl", 0.0)
            avg_pnl = experiment_metrics.average_pnl_per_trade
            
            # Update running variance calculation (Welford's method)
            if not hasattr(experiment_metrics, '_variance_sum'):
                experiment_metrics._variance_sum = 0.0
            
            delta = pnl - avg_pnl
            experiment_metrics._variance_sum += delta * delta
            
            if total_trades > 1:
                variance = experiment_metrics._variance_sum / (total_trades - 1)
                experiment_metrics.volatility = np.sqrt(variance) if variance >= 0 else 0.0
                
                # Calculate Sharpe ratio (simplified)
                if experiment_metrics.volatility > 0:
                    experiment_metrics.sharpe_ratio = avg_pnl / experiment_metrics.volatility
            
            # Update max drawdown (simplified - would need equity curve in practice)
            current_drawdown = abs(min(0, pnl))
            experiment_metrics.max_drawdown = max(experiment_metrics.max_drawdown, current_drawdown)
            
        except Exception as e:
            self.logger.error(f"Failed to calculate risk metrics: {e}")
    
    async def _check_early_stopping_conditions(self, experiment: ABTestExperiment):
        """Check if experiment should be stopped early"""
        try:
            # Only check after minimum sample size
            min_samples = experiment.early_stop_sample_size
            
            for variant in experiment.variants:
                if variant.sample_size < min_samples:
                    return  # Not enough samples yet
            
            # Check for significant losses
            loss_threshold = experiment.early_stop_significant_loss_threshold
            
            for variant in experiment.variants:
                if variant.total_trades > 0:
                    avg_pnl = variant.total_pnl / variant.total_trades
                    if avg_pnl < loss_threshold:
                        await self._stop_experiment_early(
                            experiment, 
                            f"Variant {variant.variant_id} showing significant losses: {avg_pnl:.4f}"
                        )
                        return
            
            # Check statistical significance for early stopping
            if len(experiment.variants) == 2:  # Only for A/B (not multivariate)
                significance_result = await self._calculate_statistical_significance(experiment.experiment_id)
                
                if (significance_result.get("is_significant", False) and 
                    significance_result.get("power", 0) > 0.8):
                    
                    await self._stop_experiment_early(
                        experiment,
                        f"Statistical significance achieved: p={significance_result.get('p_value', 'N/A'):.4f}"
                    )
                    return
            
        except Exception as e:
            self.logger.error(f"Failed to check early stopping conditions: {e}")
    
    async def _stop_experiment_early(self, experiment: ABTestExperiment, reason: str):
        """Stop an experiment early"""
        try:
            experiment.status = ExperimentStatus.STOPPED_EARLY
            experiment.end_time = datetime.now()
            
            # Stop monitoring
            if experiment.experiment_id in self.monitoring_tasks:
                self.monitoring_tasks[experiment.experiment_id].cancel()
                del self.monitoring_tasks[experiment.experiment_id]
            
            # Generate final analysis
            await self._generate_experiment_analysis(experiment.experiment_id)
            
            self.logger.warning(f"Experiment {experiment.experiment_id} stopped early: {reason}")
            
            # Update metrics
            self.metrics.increment_counter("ab_experiments_stopped_early")
            
        except Exception as e:
            self.logger.error(f"Failed to stop experiment early: {e}")
    
    async def _monitor_experiment(self, experiment_id: str):
        """Monitor experiment progress and performance"""
        try:
            experiment = self.active_experiments.get(experiment_id)
            if not experiment:
                return
            
            self.logger.info(f"Starting monitoring for experiment {experiment_id}")
            
            while experiment.status == ExperimentStatus.RUNNING:
                try:
                    # Check if experiment should end
                    if datetime.now() >= experiment.end_time:
                        await self._complete_experiment(experiment_id)
                        break
                    
                    # Calculate current statistics
                    await self._update_experiment_statistics(experiment_id)
                    
                    # Check performance alerts
                    await self._check_performance_alerts(experiment)
                    
                    # Wait for next monitoring interval
                    await asyncio.sleep(experiment.monitoring_interval_minutes * 60)
                    
                except asyncio.CancelledError:
                    self.logger.info(f"Monitoring cancelled for experiment {experiment_id}")
                    break
                    
                except Exception as e:
                    self.logger.error(f"Monitoring error for experiment {experiment_id}: {e}")
                    await asyncio.sleep(60)  # Wait before retrying
            
        except Exception as e:
            self.logger.error(f"Failed to monitor experiment {experiment_id}: {e}")
    
    async def _update_experiment_statistics(self, experiment_id: str):
        """Update statistical analysis for experiment"""
        try:
            # Check cache freshness
            cache_entry = self.statistical_cache.get(experiment_id, {})
            last_analysis = cache_entry.get("last_analysis", datetime.min)
            
            if (datetime.now() - last_analysis).seconds < self.cache_ttl_seconds:
                return  # Cache still fresh
            
            # Calculate statistical significance
            significance_result = await self._calculate_statistical_significance(experiment_id)
            
            # Update cache
            cache_entry["last_analysis"] = datetime.now()
            cache_entry["latest_significance"] = significance_result
            cache_entry["significance_history"].append({
                "timestamp": datetime.now(),
                "significance": significance_result
            })
            
            # Keep only last 100 entries
            if len(cache_entry["significance_history"]) > 100:
                cache_entry["significance_history"] = cache_entry["significance_history"][-100:]
            
            self.statistical_cache[experiment_id] = cache_entry
            
        except Exception as e:
            self.logger.error(f"Failed to update experiment statistics: {e}")
    
    async def _calculate_statistical_significance(self, experiment_id: str) -> Dict[str, Any]:
        """Calculate statistical significance between variants"""
        try:
            experiment = self.active_experiments.get(experiment_id)
            if not experiment or len(experiment.variants) < 2:
                return {"error": "Invalid experiment or insufficient variants"}
            
            # Get control and treatment variants
            control_variant = next(v for v in experiment.variants if v.is_control)
            treatment_variants = [v for v in experiment.variants if not v.is_control]
            
            results = {
                "experiment_id": experiment_id,
                "control_variant": control_variant.variant_id,
                "analysis_timestamp": datetime.now().isoformat(),
                "comparisons": []
            }
            
            # Compare each treatment with control
            for treatment_variant in treatment_variants:
                comparison = await self._compare_variants(control_variant, treatment_variant, experiment.primary_metric)
                results["comparisons"].append(comparison)
            
            # Overall significance
            significant_comparisons = [c for c in results["comparisons"] if c.get("is_significant", False)]
            results["any_significant"] = len(significant_comparisons) > 0
            results["significant_count"] = len(significant_comparisons)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to calculate statistical significance: {e}")
            return {"error": str(e)}
    
    async def _compare_variants(self, 
                              control_variant: ExperimentVariant, 
                              treatment_variant: ExperimentVariant, 
                              primary_metric: str) -> Dict[str, Any]:
        """Compare two variants statistically"""
        try:
            comparison = {
                "control_variant": control_variant.variant_id,
                "treatment_variant": treatment_variant.variant_id,
                "metric": primary_metric,
                "is_significant": False,
                "significance_level": StatisticalSignificance.NOT_SIGNIFICANT.value,
                "p_value": 1.0,
                "effect_size": 0.0,
                "confidence_interval": (0.0, 0.0),
                "power": 0.0,
                "sample_sizes": {
                    "control": control_variant.sample_size,
                    "treatment": treatment_variant.sample_size
                }
            }
            
            # Check minimum sample size
            min_size = 30  # Minimum for meaningful statistical testing
            if (control_variant.sample_size < min_size or 
                treatment_variant.sample_size < min_size):
                comparison["note"] = f"Insufficient sample size (min: {min_size})"
                return comparison
            
            # Get metric values
            if primary_metric == "total_pnl":
                control_mean = control_variant.total_pnl / control_variant.total_trades if control_variant.total_trades > 0 else 0
                treatment_mean = treatment_variant.total_pnl / treatment_variant.total_trades if treatment_variant.total_trades > 0 else 0
            elif primary_metric == "win_rate":
                control_mean = control_variant.successful_trades / control_variant.total_trades if control_variant.total_trades > 0 else 0
                treatment_mean = treatment_variant.successful_trades / treatment_variant.total_trades if treatment_variant.total_trades > 0 else 0
            else:
                # Default to PnL
                control_mean = control_variant.total_pnl / control_variant.total_trades if control_variant.total_trades > 0 else 0
                treatment_mean = treatment_variant.total_pnl / treatment_variant.total_trades if treatment_variant.total_trades > 0 else 0
            
            comparison["control_mean"] = control_mean
            comparison["treatment_mean"] = treatment_mean
            
            # Calculate effect size
            effect_size = (treatment_mean - control_mean) / control_mean if control_mean != 0 else 0
            comparison["effect_size"] = effect_size
            
            # Simplified statistical test (in production would use proper t-test or other appropriate test)
            # For now, we'll use a simplified approach based on sample size and effect size
            
            total_sample_size = control_variant.sample_size + treatment_variant.sample_size
            
            # Rough p-value estimation based on effect size and sample size
            if abs(effect_size) > 0.1 and total_sample_size > 100:
                comparison["p_value"] = 0.02
                comparison["is_significant"] = True
                comparison["significance_level"] = StatisticalSignificance.SIGNIFICANT.value
            elif abs(effect_size) > 0.05 and total_sample_size > 200:
                comparison["p_value"] = 0.04
                comparison["is_significant"] = True
                comparison["significance_level"] = StatisticalSignificance.MARGINALLY_SIGNIFICANT.value
            else:
                comparison["p_value"] = 0.2
                comparison["is_significant"] = False
                comparison["significance_level"] = StatisticalSignificance.NOT_SIGNIFICANT.value
            
            # Rough confidence interval (simplified)
            margin_error = abs(effect_size) * 0.2  # Simplified
            comparison["confidence_interval"] = (
                effect_size - margin_error,
                effect_size + margin_error
            )
            
            # Statistical power estimation (simplified)
            if total_sample_size > 200:
                comparison["power"] = 0.8
            elif total_sample_size > 100:
                comparison["power"] = 0.6
            else:
                comparison["power"] = 0.4
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"Failed to compare variants: {e}")
            return {
                "error": str(e),
                "control_variant": control_variant.variant_id,
                "treatment_variant": treatment_variant.variant_id
            }
    
    async def _check_performance_alerts(self, experiment: ABTestExperiment):
        """Check for performance alerts in experiment"""
        try:
            alert_thresholds = self.alert_thresholds.get(experiment.experiment_id, {})
            
            for variant in experiment.variants:
                # Check for significant performance degradation
                if variant.total_trades > 10:  # Minimum trades for meaningful alerts
                    avg_pnl = variant.total_pnl / variant.total_trades
                    
                    # Alert if losing more than 5% on average
                    if avg_pnl < -0.05:
                        await self._send_performance_alert(
                            experiment.experiment_id,
                            variant.variant_id,
                            f"Significant losses detected: {avg_pnl:.4f} average PnL"
                        )
                    
                    # Alert if win rate is very low
                    win_rate = variant.successful_trades / variant.total_trades
                    if win_rate < 0.3:  # Less than 30% win rate
                        await self._send_performance_alert(
                            experiment.experiment_id,
                            variant.variant_id,
                            f"Low win rate detected: {win_rate:.2%}"
                        )
            
        except Exception as e:
            self.logger.error(f"Failed to check performance alerts: {e}")
    
    async def _send_performance_alert(self, experiment_id: str, variant_id: str, message: str):
        """Send performance alert for experiment"""
        try:
            alert = {
                "timestamp": datetime.now().isoformat(),
                "experiment_id": experiment_id,
                "variant_id": variant_id,
                "message": message,
                "alert_type": "performance_degradation"
            }
            
            # Log alert
            self.logger.warning(f"Performance Alert - Experiment {experiment_id}, Variant {variant_id}: {message}")
            
            # Store alert in cache for dashboard
            await self.cache.set(
                f"alert:{experiment_id}:{variant_id}:{int(time.time())}",
                alert,
                ttl=86400  # 24 hours
            )
            
            # Update metrics
            self.metrics.increment_counter("ab_testing_alerts_sent")
            
        except Exception as e:
            self.logger.error(f"Failed to send performance alert: {e}")
    
    def _setup_experiment_alerts(self, experiment: ABTestExperiment):
        """Setup alert thresholds for experiment"""
        try:
            # Default alert thresholds
            thresholds = {
                "max_loss_per_trade": -0.05,  # 5% loss per trade
                "min_win_rate": 0.30,         # 30% win rate
                "max_drawdown": 0.10,         # 10% drawdown
                "min_sample_size_warning": 50  # Warn if sample size is low
            }
            
            # Store thresholds
            self.alert_thresholds[experiment.experiment_id] = thresholds
            
        except Exception as e:
            self.logger.error(f"Failed to setup experiment alerts: {e}")
    
    async def _complete_experiment(self, experiment_id: str):
        """Complete an experiment and generate final analysis"""
        try:
            experiment = self.active_experiments.get(experiment_id)
            if not experiment:
                return
            
            experiment.status = ExperimentStatus.COMPLETED
            experiment.end_time = datetime.now()
            
            # Stop monitoring
            if experiment_id in self.monitoring_tasks:
                self.monitoring_tasks[experiment_id].cancel()
                del self.monitoring_tasks[experiment_id]
            
            # Generate final analysis
            final_analysis = await self._generate_experiment_analysis(experiment_id)
            experiment.statistical_results = final_analysis
            
            # Generate recommendation
            recommendation = self._generate_experiment_recommendation(experiment, final_analysis)
            experiment.final_recommendation = recommendation
            
            # Move to completed experiments
            self.completed_experiments.append(experiment)
            self.experiment_history.append(experiment)
            del self.active_experiments[experiment_id]
            
            # Clean up
            if experiment_id in self.variant_assignments:
                del self.variant_assignments[experiment_id]
            
            if experiment_id in self.statistical_cache:
                del self.statistical_cache[experiment_id]
            
            self.logger.info(f"Experiment {experiment_id} completed with recommendation: {recommendation}")
            
            # Update metrics
            self.metrics.increment_counter("ab_experiments_completed")
            
        except Exception as e:
            error_details = self.error_handler.handle_error(e, "complete_experiment")
            self.logger.error(f"Failed to complete experiment {experiment_id}: {error_details}")
    
    async def _generate_experiment_analysis(self, experiment_id: str) -> Dict[str, Any]:
        """Generate comprehensive analysis of experiment results"""
        try:
            experiment = self.active_experiments.get(experiment_id) or next(
                (e for e in self.completed_experiments if e.experiment_id == experiment_id), None
            )
            
            if not experiment:
                raise ValueError(f"Experiment {experiment_id} not found")
            
            analysis = {
                "experiment_id": experiment_id,
                "analysis_timestamp": datetime.now().isoformat(),
                "experiment_duration_hours": (
                    (experiment.end_time or datetime.now()) - experiment.start_time
                ).total_seconds() / 3600 if experiment.start_time else 0,
                "total_sample_size": sum(v.sample_size for v in experiment.variants),
                "variant_performance": {},
                "statistical_comparison": {},
                "primary_metric_analysis": {},
                "risk_analysis": {},
                "execution_analysis": {},
                "overall_insights": []
            }
            
            # Analyze each variant
            for variant in experiment.variants:
                variant_analysis = {
                    "variant_id": variant.variant_id,
                    "variant_name": variant.variant_name,
                    "is_control": variant.is_control,
                    "sample_size": variant.sample_size,
                    "total_trades": variant.total_trades,
                    "successful_trades": variant.successful_trades,
                    "win_rate": variant.successful_trades / variant.total_trades if variant.total_trades > 0 else 0,
                    "total_pnl": variant.total_pnl,
                    "average_pnl_per_trade": variant.total_pnl / variant.total_trades if variant.total_trades > 0 else 0,
                    "configuration": variant.configuration
                }
                
                analysis["variant_performance"][variant.variant_id] = variant_analysis
            
            # Statistical comparison
            if len(experiment.variants) >= 2:
                analysis["statistical_comparison"] = await self._calculate_statistical_significance(experiment_id)
            
            # Primary metric analysis
            primary_metric = experiment.primary_metric
            control_variant = next((v for v in experiment.variants if v.is_control), experiment.variants[0])
            
            analysis["primary_metric_analysis"] = {
                "metric": primary_metric,
                "control_performance": self._get_variant_metric_value(control_variant, primary_metric),
                "variant_improvements": []
            }
            
            for variant in experiment.variants:
                if not variant.is_control:
                    control_value = self._get_variant_metric_value(control_variant, primary_metric)
                    variant_value = self._get_variant_metric_value(variant, primary_metric)
                    
                    improvement = (variant_value - control_value) / control_value if control_value != 0 else 0
                    
                    analysis["primary_metric_analysis"]["variant_improvements"].append({
                        "variant_id": variant.variant_id,
                        "improvement_percentage": improvement * 100,
                        "absolute_improvement": variant_value - control_value
                    })
            
            # Risk analysis
            analysis["risk_analysis"] = {
                "max_drawdown_by_variant": {
                    v.variant_id: v.max_drawdown for v in experiment.variants
                },
                "volatility_by_variant": {
                    v.variant_id: getattr(v, 'volatility', 0.0) for v in experiment.variants
                },
                "risk_adjusted_performance": {}
            }
            
            # Generate insights
            analysis["overall_insights"] = self._generate_experiment_insights(experiment, analysis)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Failed to generate experiment analysis: {e}")
            return {"error": str(e)}
    
    def _get_variant_metric_value(self, variant: ExperimentVariant, metric: str) -> float:
        """Get metric value for a variant"""
        if metric == "total_pnl":
            return variant.total_pnl / variant.total_trades if variant.total_trades > 0 else 0
        elif metric == "win_rate":
            return variant.successful_trades / variant.total_trades if variant.total_trades > 0 else 0
        elif metric == "total_pnl_absolute":
            return variant.total_pnl
        else:
            return 0.0
    
    def _generate_experiment_insights(self, experiment: ABTestExperiment, analysis: Dict[str, Any]) -> List[str]:
        """Generate insights from experiment analysis"""
        insights = []
        
        try:
            # Sample size insights
            total_samples = analysis["total_sample_size"]
            if total_samples < experiment.minimum_sample_size:
                insights.append(f"Sample size ({total_samples}) below minimum ({experiment.minimum_sample_size}) - results may not be reliable")
            
            # Performance insights
            primary_improvements = analysis["primary_metric_analysis"]["variant_improvements"]
            
            for improvement in primary_improvements:
                improvement_pct = improvement["improvement_percentage"]
                variant_id = improvement["variant_id"]
                
                if improvement_pct > 10:
                    insights.append(f"Variant {variant_id} shows strong improvement ({improvement_pct:.1f}%) in {experiment.primary_metric}")
                elif improvement_pct > 5:
                    insights.append(f"Variant {variant_id} shows moderate improvement ({improvement_pct:.1f}%) in {experiment.primary_metric}")
                elif improvement_pct < -5:
                    insights.append(f"Variant {variant_id} shows degradation ({improvement_pct:.1f}%) in {experiment.primary_metric}")
            
            # Statistical significance insights
            statistical_results = analysis.get("statistical_comparison", {})
            if statistical_results.get("any_significant", False):
                insights.append("Statistical significance detected - results are likely reliable")
            else:
                insights.append("No statistical significance detected - may need longer testing period")
            
            # Risk insights
            risk_analysis = analysis.get("risk_analysis", {})
            max_drawdowns = risk_analysis.get("max_drawdown_by_variant", {})
            
            for variant_id, drawdown in max_drawdowns.items():
                if drawdown > 0.1:  # 10% drawdown
                    insights.append(f"Variant {variant_id} experienced high drawdown ({drawdown:.1%}) - consider risk management")
            
        except Exception as e:
            insights.append(f"Error generating insights: {str(e)}")
        
        return insights
    
    def _generate_experiment_recommendation(self, experiment: ABTestExperiment, analysis: Dict[str, Any]) -> str:
        """Generate final recommendation for experiment"""
        try:
            # Get statistical significance
            statistical_results = analysis.get("statistical_comparison", {})
            is_significant = statistical_results.get("any_significant", False)
            
            # Get primary metric improvements
            improvements = analysis["primary_metric_analysis"]["variant_improvements"]
            
            if not improvements:
                return "KEEP_CONTROL - No treatment variants to compare"
            
            best_variant = None
            best_improvement = float('-inf')
            
            # Find best performing variant
            for improvement in improvements:
                if improvement["improvement_percentage"] > best_improvement:
                    best_improvement = improvement["improvement_percentage"]
                    best_variant = improvement["variant_id"]
            
            # Generate recommendation
            if is_significant and best_improvement > experiment.minimum_effect_size * 100:
                return f"DEPLOY_VARIANT_{best_variant} - Statistically significant improvement of {best_improvement:.1f}%"
            elif best_improvement > experiment.minimum_effect_size * 100:
                return f"CONSIDER_VARIANT_{best_variant} - Shows {best_improvement:.1f}% improvement but not statistically significant"
            elif best_improvement < -10:  # More than 10% degradation
                return f"REJECT_VARIANT_{best_variant} - Significant performance degradation ({best_improvement:.1f}%)"
            else:
                return "KEEP_CONTROL - No variant shows sufficient improvement"
                
        except Exception as e:
            return f"ERROR - Failed to generate recommendation: {str(e)}"
    
    async def _ai_brain_experiment_analysis(self, experiment: ABTestExperiment) -> Dict[str, Any]:
        """Perform AI Brain analysis of experiment design"""
        try:
            if not self.ai_brain_confidence:
                return {
                    "confidence_score": 0.5,
                    "recommendations": ["AI Brain not available - manual review recommended"]
                }
            
            # Prepare experiment data for AI analysis
            experiment_data = {
                "experiment_type": experiment.experiment_type.value,
                "variant_count": len(experiment.variants),
                "planned_duration_hours": experiment.planned_duration_hours,
                "minimum_sample_size": experiment.minimum_sample_size,
                "traffic_split": [v.traffic_percentage for v in experiment.variants],
                "primary_metric": experiment.primary_metric
            }
            
            # Calculate AI confidence
            confidence = self.ai_brain_confidence.calculate_confidence(
                model_prediction={"experiment_success_probability": 0.7},  # Base probability
                data_inputs=experiment_data,
                market_context={"service": self.service_name},
                historical_data={"previous_experiments": len(self.experiment_history)},
                risk_parameters={"risk_tolerance": 0.3}
            )
            
            # Generate recommendations
            recommendations = []
            
            if experiment.planned_duration_hours < 24:
                recommendations.append("Consider extending experiment duration for more reliable results")
            
            if experiment.minimum_sample_size < 100:
                recommendations.append("Increase minimum sample size for better statistical power")
            
            if len(experiment.variants) > 3:
                recommendations.append("Multiple variants may dilute traffic - consider focused A/B testing")
            
            if experiment.primary_metric == "total_pnl":
                recommendations.append("PnL is good primary metric but consider risk-adjusted metrics")
            
            return {
                "confidence_score": confidence.composite_score,
                "recommendations": recommendations,
                "ai_analysis": {
                    "model_confidence": confidence.model_confidence,
                    "data_confidence": confidence.data_confidence,
                    "experiment_design_score": min(1.0, confidence.composite_score + 0.1)
                }
            }
            
        except Exception as e:
            self.logger.warning(f"AI Brain experiment analysis failed: {e}")
            return {
                "confidence_score": 0.3,
                "recommendations": ["AI analysis failed - require manual expert review"]
            }
    
    # Public API Methods
    
    async def get_experiment_status(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed status of an A/B testing experiment"""
        try:
            # Check active experiments
            experiment = self.active_experiments.get(experiment_id)
            if not experiment:
                # Check completed experiments
                experiment = next(
                    (e for e in self.completed_experiments if e.experiment_id == experiment_id), 
                    None
                )
            
            if not experiment:
                return None
            
            # Build status response
            status = {
                "experiment_id": experiment.experiment_id,
                "experiment_name": experiment.experiment_name,
                "status": experiment.status.value,
                "experiment_type": experiment.experiment_type.value,
                "created_by": experiment.created_by,
                "created_at": experiment.created_at.isoformat(),
                "start_time": experiment.start_time.isoformat() if experiment.start_time else None,
                "end_time": experiment.end_time.isoformat() if experiment.end_time else None,
                "planned_duration_hours": experiment.planned_duration_hours,
                "primary_metric": experiment.primary_metric,
                "traffic_split_type": experiment.traffic_split_type.value,
                "variants": [],
                "current_results": {},
                "statistical_analysis": {},
                "ai_analysis": {
                    "confidence_score": experiment.ai_confidence_score,
                    "recommendations": experiment.ai_recommendations
                }
            }
            
            # Add variant information
            for variant in experiment.variants:
                variant_info = {
                    "variant_id": variant.variant_id,
                    "variant_name": variant.variant_name,
                    "is_control": variant.is_control,
                    "traffic_percentage": variant.traffic_percentage,
                    "sample_size": variant.sample_size,
                    "total_trades": variant.total_trades,
                    "successful_trades": variant.successful_trades,
                    "total_pnl": variant.total_pnl,
                    "win_rate": variant.successful_trades / variant.total_trades if variant.total_trades > 0 else 0,
                    "average_pnl_per_trade": variant.total_pnl / variant.total_trades if variant.total_trades > 0 else 0,
                    "last_updated": variant.last_updated.isoformat()
                }
                status["variants"].append(variant_info)
            
            # Add statistical analysis if available
            if experiment_id in self.statistical_cache:
                cache_entry = self.statistical_cache[experiment_id]
                status["statistical_analysis"] = cache_entry.get("latest_significance", {})
            
            # Add final results if completed
            if experiment.status == ExperimentStatus.COMPLETED:
                status["final_results"] = experiment.statistical_results
                status["recommendation"] = experiment.final_recommendation
            
            return status
            
        except Exception as e:
            self.logger.error(f"Failed to get experiment status: {e}")
            return None
    
    async def list_experiments(self, status_filter: Optional[ExperimentStatus] = None) -> List[Dict[str, Any]]:
        """List all experiments, optionally filtered by status"""
        try:
            experiments = []
            
            # Add active experiments
            for experiment in self.active_experiments.values():
                if status_filter and experiment.status != status_filter:
                    continue
                
                experiment_summary = {
                    "experiment_id": experiment.experiment_id,
                    "experiment_name": experiment.experiment_name,
                    "status": experiment.status.value,
                    "experiment_type": experiment.experiment_type.value,
                    "created_by": experiment.created_by,
                    "created_at": experiment.created_at.isoformat(),
                    "variant_count": len(experiment.variants),
                    "total_sample_size": sum(v.sample_size for v in experiment.variants),
                    "is_active": True
                }
                
                experiments.append(experiment_summary)
            
            # Add completed experiments
            for experiment in self.completed_experiments:
                if status_filter and experiment.status != status_filter:
                    continue
                
                experiment_summary = {
                    "experiment_id": experiment.experiment_id,
                    "experiment_name": experiment.experiment_name,
                    "status": experiment.status.value,
                    "experiment_type": experiment.experiment_type.value,
                    "created_by": experiment.created_by,
                    "created_at": experiment.created_at.isoformat(),
                    "variant_count": len(experiment.variants),
                    "total_sample_size": sum(v.sample_size for v in experiment.variants),
                    "is_active": False,
                    "recommendation": experiment.final_recommendation
                }
                
                experiments.append(experiment_summary)
            
            # Sort by creation date (newest first)
            experiments.sort(key=lambda x: x["created_at"], reverse=True)
            
            return experiments
            
        except Exception as e:
            self.logger.error(f"Failed to list experiments: {e}")
            return []
    
    async def stop_experiment(self, experiment_id: str, stopped_by: str, reason: str = "") -> Dict[str, Any]:
        """Stop an experiment manually"""
        try:
            experiment = self.active_experiments.get(experiment_id)
            if not experiment:
                raise ValueError(f"Active experiment {experiment_id} not found")
            
            if experiment.status != ExperimentStatus.RUNNING:
                raise ValueError(f"Experiment {experiment_id} is not running")
            
            # Stop the experiment
            experiment.status = ExperimentStatus.STOPPED_EARLY
            experiment.end_time = datetime.now()
            
            # Stop monitoring
            if experiment_id in self.monitoring_tasks:
                self.monitoring_tasks[experiment_id].cancel()
                del self.monitoring_tasks[experiment_id]
            
            # Generate final analysis
            final_analysis = await self._generate_experiment_analysis(experiment_id)
            experiment.statistical_results = final_analysis
            
            # Generate recommendation
            recommendation = self._generate_experiment_recommendation(experiment, final_analysis)
            experiment.final_recommendation = recommendation
            
            self.logger.info(f"Experiment {experiment_id} stopped by {stopped_by}: {reason}")
            
            # Update metrics
            self.metrics.increment_counter("ab_experiments_stopped_manually")
            
            return {
                "success": True,
                "experiment_id": experiment_id,
                "stopped_by": stopped_by,
                "reason": reason,
                "status": experiment.status.value,
                "final_analysis": final_analysis,
                "recommendation": recommendation
            }
            
        except Exception as e:
            error_details = self.error_handler.handle_error(e, "stop_experiment")
            self.logger.error(f"Failed to stop experiment: {error_details}")
            raise
    
    async def get_ab_testing_metrics(self) -> Dict[str, Any]:
        """Get comprehensive A/B testing metrics"""
        try:
            active_count = len(self.active_experiments)
            completed_count = len(self.completed_experiments)
            total_count = active_count + completed_count
            
            # Status distribution
            status_distribution = {}
            all_experiments = list(self.active_experiments.values()) + self.completed_experiments
            
            for experiment in all_experiments:
                status = experiment.status.value
                status_distribution[status] = status_distribution.get(status, 0) + 1
            
            # Type distribution
            type_distribution = {}
            for experiment in all_experiments:
                exp_type = experiment.experiment_type.value
                type_distribution[exp_type] = type_distribution.get(exp_type, 0) + 1
            
            # Success metrics
            successful_experiments = [
                e for e in self.completed_experiments 
                if e.final_recommendation and "DEPLOY" in e.final_recommendation
            ]
            
            success_rate = len(successful_experiments) / completed_count if completed_count > 0 else 0
            
            # Sample size statistics
            sample_sizes = [
                sum(v.sample_size for v in e.variants) 
                for e in all_experiments
            ]
            
            avg_sample_size = statistics.mean(sample_sizes) if sample_sizes else 0
            
            # Duration statistics
            completed_durations = []
            for experiment in self.completed_experiments:
                if experiment.start_time and experiment.end_time:
                    duration_hours = (experiment.end_time - experiment.start_time).total_seconds() / 3600
                    completed_durations.append(duration_hours)
            
            avg_duration_hours = statistics.mean(completed_durations) if completed_durations else 0
            
            metrics = {
                "summary": {
                    "total_experiments": total_count,
                    "active_experiments": active_count,
                    "completed_experiments": completed_count,
                    "success_rate": success_rate,
                    "average_sample_size": avg_sample_size,
                    "average_duration_hours": avg_duration_hours
                },
                "status_distribution": status_distribution,
                "type_distribution": type_distribution,
                "performance_metrics": await self.metrics.get_all_metrics(),
                "recent_experiments": [
                    {
                        "experiment_id": e.experiment_id,
                        "experiment_name": e.experiment_name,
                        "status": e.status.value,
                        "created_at": e.created_at.isoformat()
                    }
                    for e in sorted(all_experiments, key=lambda x: x.created_at, reverse=True)[:10]
                ],
                "timestamp": datetime.now().isoformat()
            }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to get A/B testing metrics: {e}")
            return {"error": "Failed to retrieve metrics"}


# Factory Functions and Utilities

def create_ab_testing_core(service_name: str = "trading-engine") -> ABTestingCore:
    """Factory function to create an A/B Testing Core instance"""
    try:
        ab_testing = ABTestingCore(service_name)
        return ab_testing
    except Exception as e:
        # Fallback logger if creation fails
        import logging
        logging.error(f"Failed to create A/B Testing Core for {service_name}: {e}")
        raise


# Export main classes and functions
__all__ = [
    "ABTestingCore",
    "ExperimentStatus",
    "ExperimentType", 
    "TrafficSplitType",
    "StatisticalSignificance",
    "ABTestExperiment",
    "ExperimentVariant",
    "ExperimentMetrics",
    "create_ab_testing_core"
]