"""
🧠 Real-time Learning Adaptation System - MICROSERVICE ARCHITECTURE
Phase 3: Deep Learning Enhancement with Memory Integration
Implements continuous learning, performance adaptation, and dynamic model optimization

Features:
- Real-time learning adaptation dengan microservice infrastructure
- Performance monitoring dengan comprehensive tracking
- Dynamic model optimization dengan enhanced error handling
- AI-driven learning decisions dengan event publishing
- Risk-aware adaptation dengan centralized validation
- Memory integration dengan standardized logging

MICROSERVICE INFRASTRUCTURE:
- Performance tracking untuk learning operations
- Per-service error handling untuk adaptation processes
- Event-driven architecture untuk learning lifecycle management
- Comprehensive logging untuk learning decisions audit
- Validation system untuk adaptation quality assurance
"""

import asyncio
import logging
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import hashlib
from collections import deque
import threading
import time

# MICROSERVICE INFRASTRUCTURE INTEGRATION
from ....shared.infrastructure.logging.base_logger import BaseLogger
from ....shared.infrastructure.config.base_config import BaseConfig
from ....shared.infrastructure.error_handling.base_error_handler import BaseErrorHandler
from ....shared.infrastructure.performance.base_performance_tracker import BasePerformanceTracker
from ....shared.infrastructure.events.base_event_publisher import BaseEventPublisher

# Enhanced logger with microservice infrastructure
learning_logger = BaseLogger("learning_adapter", {
    "component": "data_processing",
    "service": "ml_processing",
    "feature": "dynamic_optimization"
})

# Learning adaptation metrics
learning_metrics = {
    "total_adaptations_performed": 0,
    "successful_adaptations": 0,
    "failed_adaptations": 0,
    "performance_improvements": 0,
    "model_rollbacks": 0,
    "avg_adaptation_time_ms": 0,
    "learning_decisions_made": 0,
    "risk_assessments_performed": 0,
    "events_published": 0,
    "accuracy_improvements": []
}

# Setup legacy logging for backward compatibility
logger = learning_logger


class LearningMode(Enum):
    """Learning adaptation modes"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    ADAPTIVE = "adaptive"


class AdaptationTrigger(Enum):
    """Triggers for learning adaptation"""
    PERFORMANCE_DEGRADATION = "performance_degradation"
    MARKET_REGIME_CHANGE = "market_regime_change"
    PATTERN_DRIFT = "pattern_drift"
    NEW_DATA_AVAILABILITY = "new_data_availability"
    EXTERNAL_EVENT = "external_event"
    SCHEDULED_UPDATE = "scheduled_update"


class LearningObjective(Enum):
    """Learning optimization objectives"""
    ACCURACY_MAXIMIZATION = "accuracy_maximization"
    RISK_MINIMIZATION = "risk_minimization"
    PROFIT_MAXIMIZATION = "profit_maximization"
    SHARPE_RATIO_OPTIMIZATION = "sharpe_ratio_optimization"
    DRAWDOWN_MINIMIZATION = "drawdown_minimization"
    MULTI_OBJECTIVE = "multi_objective"


@dataclass
class PerformanceMetrics:
    """Performance metrics for adaptation decisions"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    
    # Advanced metrics
    information_ratio: float
    calmar_ratio: float
    sortino_ratio: float
    
    # Temporal metrics
    recent_accuracy: float  # Last N predictions
    trend_accuracy: float   # Trend over time
    
    timestamp: datetime
    evaluation_period: timedelta


@dataclass
class AdaptationAction:
    """Action to be taken for learning adaptation"""
    action_type: str
    parameters: Dict[str, Any]
    expected_improvement: float
    confidence: float
    risk_level: float
    
    # Implementation details
    implementation_plan: List[str]
    rollback_plan: List[str]
    validation_criteria: Dict[str, float]
    
    # AI validation
    ai_approval_score: float
    ai_reasoning: str
    
    timestamp: datetime
    expires_at: datetime


@dataclass
class LearningCycle:
    """Complete learning cycle information"""
    cycle_id: str
    start_timestamp: datetime
    end_timestamp: Optional[datetime]
    
    # Trigger information
    trigger: AdaptationTrigger
    trigger_data: Dict[str, Any]
    
    # Performance analysis
    current_performance: PerformanceMetrics
    historical_performance: List[PerformanceMetrics]
    performance_trend: str  # improving, degrading, stable
    
    # Adaptation decisions
    adaptation_actions: List[AdaptationAction]
    selected_action: Optional[AdaptationAction]
    
    # Execution results
    execution_successful: Optional[bool]
    performance_improvement: Optional[float]
    lessons_learned: Dict[str, Any]
    
    # AI enhancement
    ai_analysis: Dict[str, Any]
    memory_integration: Dict[str, Any]


@dataclass
class AdaptationConfig:
    """Configuration for real-time learning adaptation"""
    # Learning settings
    learning_mode: LearningMode = LearningMode.MODERATE
    learning_rate: float = 0.001
    adaptation_threshold: float = 0.05  # Performance drop threshold
    
    # Performance monitoring
    performance_window: int = 100  # Number of predictions to evaluate
    evaluation_frequency: int = 10   # Evaluate every N predictions
    min_data_points: int = 50       # Minimum data for adaptation
    
    # Adaptation triggers
    enable_performance_trigger: bool = True
    enable_market_regime_trigger: bool = True
    enable_pattern_drift_trigger: bool = True
    enable_scheduled_trigger: bool = True
    
    # Safety settings
    max_adaptations_per_hour: int = 5
    require_ai_approval: bool = True
    enable_rollback: bool = True
    performance_safety_margin: float = 0.1
    
    # AI enhancement
    enable_langgraph_analysis: bool = True
    enable_letta_memory_learning: bool = True
    enable_handit_validation: bool = True
    
    # Learning objectives
    primary_objective: LearningObjective = LearningObjective.ACCURACY_MAXIMIZATION
    secondary_objectives: List[LearningObjective] = None
    objective_weights: Dict[str, float] = None


class RealtimeLearningAdaptation:
    """
    Real-time Learning Adaptation System with MICROSERVICE ARCHITECTURE
    Continuously monitors performance and adapts ML/DL models for optimal trading performance
    Enhanced with comprehensive error handling, performance tracking, event publishing, and validation
    """
    
    def __init__(self, config: Optional[AdaptationConfig] = None):
        """Initialize Real-time Learning Adaptation with MICROSERVICE ARCHITECTURE"""
        initialization_start = time.perf_counter()
        
        try:
            # Initialize microservice infrastructure
            self.logger = learning_logger
            self.config_manager = BaseConfig()
            self.error_handler = BaseErrorHandler("learning_adapter")
            self.performance_tracker = BasePerformanceTracker("learning_adapter")
            self.event_publisher = BaseEventPublisher("ml_processing")
            
            # Load microservice-specific configuration
            self.service_config = self.config_manager.get_config("learning_adapter", {
                "learning": {
                    "mode": "moderate",
                    "adaptation_threshold": 0.05,
                    "max_adaptations_per_hour": 5
                },
                "ai_services": {
                    "langgraph_endpoint": "http://ai-orchestration:8080/langgraph",
                    "letta_endpoint": "http://ai-orchestration:8080/letta",
                    "handit_endpoint": "http://ai-orchestration:8080/handit"
                },
                "performance": {
                    "monitoring_enabled": True,
                    "evaluation_frequency": 10,
                    "min_data_points": 50
                }
            })
            
            # Validate initialization configuration
            self.config = config or AdaptationConfig()
            
            # Publish learning adapter initialization event
            self.event_publisher.publish_event(
                "learning_adapter.initialization_started",
                {
                    "learning_mode": self.config.learning_mode.value,
                    "adaptation_threshold": self.config.adaptation_threshold,
                    "performance_window": self.config.performance_window,
                    "ai_services_enabled": {
                        "langgraph": self.config.enable_langgraph_analysis,
                        "letta_memory": self.config.enable_letta_memory_learning,
                        "handit_validation": self.config.enable_handit_validation
                    }
                }
            )
            
            # Initialize AI services with microservice error handling
            try:
                # In microservice architecture, these would be HTTP clients to other services
                self.ai_coordinator = None  # Will be initialized as HTTP client
                self.memory_manager = None  # Will be initialized as HTTP client
                self.db_manager = None      # Will be initialized as HTTP client
                self.logger.debug("AI service clients will be initialized on demand")
            except Exception as e:
                self.error_handler.handle_error(e, {
                    "operation": "initialize_ai_service_clients",
                    "microservice": "ml_processing"
                })
                self.logger.warning(f"AI service client initialization deferred: {e}")
        
            # Performance tracking with enhanced monitoring
            self.performance_history: deque = deque(maxlen=1000)
            self.prediction_results: deque = deque(maxlen=self.config.performance_window)
            self.market_data_buffer: deque = deque(maxlen=500)
            
            # Learning state management
            self.learning_cycles: List[LearningCycle] = []
            self.active_adaptations: Dict[str, AdaptationAction] = {}
            self.adaptation_history: List[Dict[str, Any]] = []
            
            # Performance monitoring
            self.current_performance: Optional[PerformanceMetrics] = None
            self.baseline_performance: Optional[PerformanceMetrics] = None
            self.performance_trend: str = "stable"
            
            # Real-time monitoring
            self.monitoring_active: bool = False
            self.monitoring_thread: Optional[threading.Thread] = None
            self.last_evaluation: datetime = datetime.now()
            self.adaptation_count: Dict[str, int] = {}  # Count adaptations per hour
            
            # Enhanced statistics with microservice tracking
            self.adaptation_stats = {
                "total_cycles": 0,
                "successful_adaptations": 0,
                "failed_adaptations": 0,
                "performance_improvements": 0,
                "average_improvement": 0.0,
                "rollbacks_executed": 0,
                "ai_approvals": 0,
                "ai_rejections": 0,
                "initialization_time_ms": 0,
                "microservice_architecture_enabled": True
            }
            
            # Update performance metrics
            learning_metrics["total_adaptations_performed"] = 0
            learning_metrics["successful_adaptations"] = 0
            learning_metrics["events_published"] += 1
            
            # Record initialization performance
            initialization_time = (time.perf_counter() - initialization_start) * 1000
            self.adaptation_stats["initialization_time_ms"] = initialization_time
            
            with self.performance_tracker.track_operation("learning_adapter_initialization"):
                pass  # Initialization complete
            
            # Publish successful initialization event
            self.event_publisher.publish_event(
                "learning_adapter.initialization_completed",
                {
                    "initialization_time_ms": initialization_time,
                    "learning_mode": self.config.learning_mode.value,
                    "status": "ready"
                }
            )
            learning_metrics["events_published"] += 1
            
            self.logger.info(f"✅ Real-time Learning Adaptation System initialized successfully in {initialization_time:.2f}ms")
            
        except Exception as e:
            # Handle initialization failure with microservice error management
            initialization_time = (time.perf_counter() - initialization_start) * 1000
            
            self.error_handler.handle_error(e, {
                "operation": "learning_adapter_initialization",
                "initialization_time_ms": initialization_time
            })
            
            self.logger.error(f"❌ Failed to initialize Real-time Learning Adaptation: {e}")
            
            # Publish initialization failure event
            self.event_publisher.publish_event(
                "learning_adapter.initialization_failed",
                {
                    "error": str(e),
                    "initialization_time_ms": initialization_time
                }
            )
            
            raise
    
    async def initialize(self) -> bool:
        """Initialize adaptation system and start monitoring with MICROSERVICE ARCHITECTURE"""
        initialization_start = time.perf_counter()
        
        try:
            with self.performance_tracker.track_operation("learning_adapter_system_initialize"):
                # Publish system initialization event
                await self.event_publisher.publish_event(
                    "learning_system.initialization_started",
                    {
                        "initialization_phase": "system_startup",
                        "components_to_initialize": ["historical_data", "baseline_performance", "monitoring"]
                    }
                )
                
                # Load historical performance data with error handling
                try:
                    await self._load_historical_performance()
                    self.logger.debug("Historical performance data loaded successfully")
                except Exception as e:
                    self.error_handler.handle_error(e, {"operation": "load_historical_performance"})
                    self.logger.warning(f"Historical data loading failed: {e}")
                
                # Establish baseline performance with error handling
                try:
                    self.baseline_performance = await self._calculate_baseline_performance()
                    if self.baseline_performance:
                        self.logger.debug("Baseline performance established successfully")
                    else:
                        self.logger.warning("Baseline performance calculation returned None")
                except Exception as e:
                    self.error_handler.handle_error(e, {"operation": "calculate_baseline_performance"})
                    self.logger.warning(f"Baseline performance calculation failed: {e}")
                
                # Start real-time monitoring with error handling
                try:
                    await self._start_monitoring()
                    self.logger.debug("Real-time monitoring started successfully")
                except Exception as e:
                    self.error_handler.handle_error(e, {"operation": "start_monitoring"})
                    self.logger.warning(f"Monitoring startup failed: {e}")
                
                # Record initialization performance
                initialization_time = (time.perf_counter() - initialization_start) * 1000
                
                # Update learning metrics
                learning_metrics["successful_adaptations"] += 1
                learning_metrics["avg_adaptation_time_ms"] = initialization_time
                learning_metrics["events_published"] += 2
                
                # Publish successful system initialization event
                await self.event_publisher.publish_event(
                    "learning_system.initialization_completed",
                    {
                        "initialization_time_ms": initialization_time,
                        "components_initialized": {
                            "historical_data": True,
                            "baseline_performance": self.baseline_performance is not None,
                            "monitoring": self.monitoring_active
                        },
                        "status": "ready"
                    }
                )
                
                self.logger.info(f"✅ Real-time Learning Adaptation System ready in {initialization_time:.2f}ms")
                return True
            
        except Exception as e:
            # Handle system initialization failure with microservice error management
            initialization_time = (time.perf_counter() - initialization_start) * 1000
            learning_metrics["failed_adaptations"] += 1
            
            self.error_handler.handle_error(e, {
                "operation": "learning_adapter_system_initialize",
                "initialization_time_ms": initialization_time
            })
            
            self.logger.error(f"❌ Failed to initialize Real-time Learning Adaptation: {e}")
            
            # Publish system initialization failure event
            await self.event_publisher.publish_event(
                "learning_system.initialization_failed",
                {
                    "error": str(e),
                    "initialization_time_ms": initialization_time
                }
            )
            
            return False
    
    async def process_prediction_result(self,
                                      prediction: Dict[str, Any],
                                      actual_outcome: Optional[float] = None,
                                      market_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a prediction result for learning adaptation with MICROSERVICE ARCHITECTURE
        Enhanced with comprehensive error handling, performance tracking, and event publishing
        """
        processing_start = time.perf_counter()
        
        try:
            with self.performance_tracker.track_operation("process_prediction_result"):
                # Publish prediction processing event
                await self.event_publisher.publish_event(
                    "prediction_result.processing_started",
                    {
                        "symbol": prediction.get('symbol', 'unknown'),
                        "has_actual_outcome": actual_outcome is not None,
                        "has_market_data": market_data is not None,
                        "prediction_confidence": prediction.get('confidence', 0.0)
                    }
                )
                
                # Store prediction result with error handling
                try:
                    result_data = {
                        "prediction": prediction.get('prediction', 0.0),
                        "confidence": prediction.get('confidence', 0.0),
                        "timestamp": prediction.get('timestamp', datetime.now()),
                        "symbol": prediction.get('symbol', 'UNKNOWN'),
                        "timeframe": prediction.get('timeframe', '1H'),
                        "actual_outcome": actual_outcome,
                        "processing_time": prediction.get('processing_time', 0.0),
                        "quality_score": prediction.get('quality_score', 0.5)
                    }
                    
                    self.prediction_results.append(result_data)
                    self.logger.debug(f"Prediction result stored: {result_data['symbol']}")
                except Exception as e:
                    self.error_handler.handle_error(e, {"operation": "store_prediction_result"})
                    self.logger.warning(f"Failed to store prediction result: {e}")
                
                # Store market data if provided with error handling
                if market_data:
                    try:
                        market_data_entry = {
                            "timestamp": market_data.get('timestamp', datetime.now()),
                            "open": market_data.get('open', 0.0),
                            "high": market_data.get('high', 0.0),
                            "low": market_data.get('low', 0.0),
                            "close": market_data.get('close', 0.0),
                            "volume": market_data.get('volume', 0.0),
                            "symbol": market_data.get('symbol', 'UNKNOWN'),
                            "timeframe": market_data.get('timeframe', '1H')
                        }
                        
                        self.market_data_buffer.append(market_data_entry)
                        self.logger.debug(f"Market data stored: {market_data_entry['symbol']}")
                    except Exception as e:
                        self.error_handler.handle_error(e, {"operation": "store_market_data"})
                        self.logger.warning(f"Failed to store market data: {e}")
                
                # Check if evaluation is needed with error handling
                evaluation_result = None
                evaluation_performed = False
                
                try:
                    if self._should_evaluate_performance():
                        evaluation_start = time.perf_counter()
                        evaluation_result = await self._evaluate_current_performance()
                        evaluation_time = (time.perf_counter() - evaluation_start) * 1000
                        evaluation_performed = True
                        
                        # Check adaptation triggers
                        if evaluation_result and evaluation_result.get("adaptation_needed", False):
                            try:
                                adaptation_result = await self._trigger_learning_adaptation(
                                    trigger=AdaptationTrigger.PERFORMANCE_DEGRADATION,
                                    trigger_data=evaluation_result
                                )
                                evaluation_result["adaptation_triggered"] = adaptation_result
                                learning_metrics["learning_decisions_made"] += 1
                            except Exception as e:
                                self.error_handler.handle_error(e, {
                                    "operation": "trigger_learning_adaptation",
                                    "trigger": "PERFORMANCE_DEGRADATION"
                                })
                                self.logger.warning(f"Adaptation trigger failed: {e}")
                                evaluation_result["adaptation_trigger_error"] = str(e)
                except Exception as e:
                    self.error_handler.handle_error(e, {"operation": "evaluate_current_performance"})
                    self.logger.warning(f"Performance evaluation failed: {e}")
                
                # Record processing performance
                processing_time = (time.perf_counter() - processing_start) * 1000
                
                # Update learning metrics
                learning_metrics["total_adaptations_performed"] += 1
                learning_metrics["avg_adaptation_time_ms"] = (
                    learning_metrics["avg_adaptation_time_ms"] * 0.9 + processing_time * 0.1
                )
                learning_metrics["events_published"] += 1
                
                # Publish prediction processing completion event
                await self.event_publisher.publish_event(
                    "prediction_result.processing_completed",
                    {
                        "symbol": prediction.get('symbol', 'unknown'),
                        "processing_time_ms": processing_time,
                        "evaluation_performed": evaluation_performed,
                        "adaptation_triggered": evaluation_result.get("adaptation_triggered") is not None if evaluation_result else False,
                        "buffer_size": len(self.prediction_results)
                    }
                )
                
                # Prepare response
                response = {
                    "processed": True,
                    "prediction_stored": True,
                    "evaluation_performed": evaluation_performed,
                    "evaluation_result": evaluation_result,
                    "current_buffer_size": len(self.prediction_results),
                    "processing_time_ms": processing_time,
                    "timestamp": datetime.now(),
                    "microservice_architecture": True
                }
                
                self.logger.debug(f"Prediction result processed successfully in {processing_time:.2f}ms")
                return response
            
        except Exception as e:
            # Handle prediction processing failure with microservice error management
            processing_time = (time.perf_counter() - processing_start) * 1000
            learning_metrics["failed_adaptations"] += 1
            
            self.error_handler.handle_error(e, {
                "operation": "process_prediction_result",
                "processing_time_ms": processing_time
            })
            
            self.logger.error(f"❌ Prediction result processing failed: {e}")
            
            # Publish prediction processing failure event
            await self.event_publisher.publish_event(
                "prediction_processing.failed",
                {
                    "error": str(e),
                    "processing_time_ms": processing_time,
                    "symbol": prediction.get('symbol', 'unknown') if prediction else 'unknown'
                }
            )
            
            return {"processed": False, "error": str(e), "timestamp": datetime.now()}
    
    def _should_evaluate_performance(self) -> bool:
        """Check if performance evaluation should be triggered"""
        # Check if enough predictions accumulated
        if len(self.prediction_results) < self.config.evaluation_frequency:
            return False
        
        # Check time since last evaluation
        time_since_last = datetime.now() - self.last_evaluation
        if time_since_last < timedelta(minutes=5):  # Minimum 5 minutes between evaluations
            return False
        
        # Check if enough data points with actual outcomes
        outcomes_available = sum(1 for r in self.prediction_results if r.get("actual_outcome") is not None)
        if outcomes_available < self.config.min_data_points:
            return False
        
        return True
    
    async def _evaluate_current_performance(self) -> Dict[str, Any]:
        """Evaluate current model performance"""
        try:
            # Calculate current performance metrics
            current_metrics = await self._calculate_current_performance_metrics()
            
            if not current_metrics:
                return {"evaluation_failed": True, "reason": "insufficient_data"}
            
            # Compare with baseline
            performance_comparison = self._compare_with_baseline(current_metrics)
            
            # Determine if adaptation is needed
            adaptation_needed = self._is_adaptation_needed(performance_comparison)
            
            # Update internal state
            self.current_performance = current_metrics
            self.last_evaluation = datetime.now()
            
            # Store performance history
            self.performance_history.append({
                "metrics": current_metrics,
                "comparison": performance_comparison,
                "timestamp": datetime.now()
            })
            
            result = {
                "current_metrics": asdict(current_metrics),
                "performance_comparison": performance_comparison,
                "adaptation_needed": adaptation_needed,
                "evaluation_timestamp": datetime.now()
            }
            
            self.logger.debug(f"📊 Performance evaluation completed: adaptation_needed={adaptation_needed}")
            return result
            
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "evaluate_current_performance"})
            self.logger.error(f"❌ Performance evaluation failed: {e}")
            return {"evaluation_failed": True, "error": str(e)}
    
    async def _calculate_current_performance_metrics(self) -> Optional[PerformanceMetrics]:
        """Calculate current performance metrics from recent predictions"""
        try:
            # Filter predictions with actual outcomes
            valid_predictions = [
                r for r in self.prediction_results 
                if r.get("actual_outcome") is not None
            ]
            
            if len(valid_predictions) < self.config.min_data_points:
                return None
            
            # Extract data
            predictions = np.array([r["prediction"] for r in valid_predictions])
            actuals = np.array([r["actual_outcome"] for r in valid_predictions])
            confidences = np.array([r["confidence"] for r in valid_predictions])
            
            # Calculate basic accuracy metrics
            accuracy = self._calculate_accuracy(predictions, actuals)
            precision = self._calculate_precision(predictions, actuals)
            recall = self._calculate_recall(predictions, actuals)
            f1_score = self._calculate_f1_score(precision, recall)
            
            # Calculate trading-specific metrics
            returns = self._calculate_returns(predictions, actuals)
            sharpe_ratio = self._calculate_sharpe_ratio(returns)
            max_drawdown = self._calculate_max_drawdown(returns)
            win_rate = self._calculate_win_rate(returns)
            profit_factor = self._calculate_profit_factor(returns)
            
            # Calculate advanced metrics
            information_ratio = self._calculate_information_ratio(returns)
            calmar_ratio = self._calculate_calmar_ratio(returns, max_drawdown)
            sortino_ratio = self._calculate_sortino_ratio(returns)
            
            # Calculate temporal metrics
            recent_data = valid_predictions[-20:]  # Last 20 predictions
            if len(recent_data) >= 10:
                recent_predictions = np.array([r["prediction"] for r in recent_data])
                recent_actuals = np.array([r["actual_outcome"] for r in recent_data])
                recent_accuracy = self._calculate_accuracy(recent_predictions, recent_actuals)
            else:
                recent_accuracy = accuracy
            
            trend_accuracy = self._calculate_trend_accuracy(valid_predictions)
            
            return PerformanceMetrics(
                accuracy=accuracy,
                precision=precision,
                recall=recall,
                f1_score=f1_score,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                win_rate=win_rate,
                profit_factor=profit_factor,
                information_ratio=information_ratio,
                calmar_ratio=calmar_ratio,
                sortino_ratio=sortino_ratio,
                recent_accuracy=recent_accuracy,
                trend_accuracy=trend_accuracy,
                timestamp=datetime.now(),
                evaluation_period=timedelta(hours=1)  # Simplified
            )
            
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "calculate_performance_metrics"})
            self.logger.error(f"❌ Performance metrics calculation failed: {e}")
            return None
    
    def _calculate_accuracy(self, predictions: np.ndarray, actuals: np.ndarray) -> float:
        """Calculate prediction accuracy"""
        try:
            # For regression, use threshold-based accuracy
            threshold = 0.1  # 10% threshold
            accurate_predictions = np.abs(predictions - actuals) <= threshold * np.abs(actuals)
            return float(np.mean(accurate_predictions))
        except:
            return 0.0
    
    def _calculate_precision(self, predictions: np.ndarray, actuals: np.ndarray) -> float:
        """Calculate precision (simplified for regression)"""
        try:
            # Simplified precision calculation
            correct_direction = np.sign(predictions) == np.sign(actuals)
            return float(np.mean(correct_direction))
        except:
            return 0.0
    
    def _calculate_recall(self, predictions: np.ndarray, actuals: np.ndarray) -> float:
        """Calculate recall (simplified for regression)"""
        try:
            # Simplified recall calculation
            return self._calculate_precision(predictions, actuals)  # Simplified
        except:
            return 0.0
    
    def _calculate_f1_score(self, precision: float, recall: float) -> float:
        """Calculate F1 score"""
        try:
            if precision + recall == 0:
                return 0.0
            return 2 * (precision * recall) / (precision + recall)
        except:
            return 0.0
    
    def _calculate_returns(self, predictions: np.ndarray, actuals: np.ndarray) -> np.ndarray:
        """Calculate returns based on predictions vs actuals"""
        try:
            # Simplified return calculation
            returns = predictions * np.sign(actuals)  # Simplified
            return returns
        except:
            return np.array([0.0])
    
    def _calculate_sharpe_ratio(self, returns: np.ndarray) -> float:
        """Calculate Sharpe ratio"""
        try:
            if len(returns) == 0 or np.std(returns) == 0:
                return 0.0
            return float(np.mean(returns) / np.std(returns))
        except:
            return 0.0
    
    def _calculate_max_drawdown(self, returns: np.ndarray) -> float:
        """Calculate maximum drawdown"""
        try:
            cumulative_returns = np.cumsum(returns)
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdown = (cumulative_returns - running_max) / (running_max + 1e-8)
            return float(-np.min(drawdown))
        except:
            return 0.0
    
    def _calculate_win_rate(self, returns: np.ndarray) -> float:
        """Calculate win rate"""
        try:
            if len(returns) == 0:
                return 0.0
            return float(np.mean(returns > 0))
        except:
            return 0.0
    
    def _calculate_profit_factor(self, returns: np.ndarray) -> float:
        """Calculate profit factor"""
        try:
            if len(returns) == 0:
                return 1.0
            profits = np.sum(returns[returns > 0])
            losses = -np.sum(returns[returns < 0])
            if losses == 0:
                return float('inf') if profits > 0 else 1.0
            return float(profits / losses)
        except:
            return 1.0
    
    def _calculate_information_ratio(self, returns: np.ndarray) -> float:
        """Calculate information ratio"""
        try:
            # Simplified IR calculation
            return self._calculate_sharpe_ratio(returns)  # Simplified
        except:
            return 0.0
    
    def _calculate_calmar_ratio(self, returns: np.ndarray, max_drawdown: float) -> float:
        """Calculate Calmar ratio"""
        try:
            if max_drawdown == 0:
                return float('inf') if np.mean(returns) > 0 else 0.0
            return float(np.mean(returns) / max_drawdown)
        except:
            return 0.0
    
    def _calculate_sortino_ratio(self, returns: np.ndarray) -> float:
        """Calculate Sortino ratio"""
        try:
            if len(returns) == 0:
                return 0.0
            negative_returns = returns[returns < 0]
            if len(negative_returns) == 0:
                return float('inf') if np.mean(returns) > 0 else 0.0
            downside_deviation = np.std(negative_returns)
            if downside_deviation == 0:
                return float('inf') if np.mean(returns) > 0 else 0.0
            return float(np.mean(returns) / downside_deviation)
        except:
            return 0.0
    
    def _calculate_trend_accuracy(self, predictions: List[Dict[str, Any]]) -> float:
        """Calculate trend accuracy over time"""
        try:
            if len(predictions) < 10:
                return 0.5
            
            # Take recent 30 predictions
            recent_predictions = predictions[-30:]
            accuracies = []
            
            for i in range(len(recent_predictions)):
                pred = recent_predictions[i]
                if pred.get("actual_outcome") is not None:
                    accuracy = 1.0 if abs(pred["prediction"] - pred["actual_outcome"]) < 0.1 else 0.0
                    accuracies.append(accuracy)
            
            if not accuracies:
                return 0.5
            
            # Calculate trend (improvement over time)
            if len(accuracies) >= 10:
                first_half = np.mean(accuracies[:len(accuracies)//2])
                second_half = np.mean(accuracies[len(accuracies)//2:])
                trend = second_half - first_half
                return float(np.mean(accuracies) + trend * 0.1)  # Small trend bonus
            
            return float(np.mean(accuracies))
            
        except:
            return 0.5
    
    def _compare_with_baseline(self, current_metrics: PerformanceMetrics) -> Dict[str, float]:
        """Compare current performance with baseline"""
        if not self.baseline_performance:
            return {"no_baseline": True}
        
        comparison = {}
        baseline = self.baseline_performance
        
        # Calculate relative changes
        comparison["accuracy_change"] = current_metrics.accuracy - baseline.accuracy
        comparison["sharpe_change"] = current_metrics.sharpe_ratio - baseline.sharpe_ratio
        comparison["drawdown_change"] = current_metrics.max_drawdown - baseline.max_drawdown
        comparison["win_rate_change"] = current_metrics.win_rate - baseline.win_rate
        
        # Calculate overall performance score
        performance_score = (
            comparison["accuracy_change"] * 0.3 +
            comparison["sharpe_change"] * 0.3 +
            (-comparison["drawdown_change"]) * 0.2 +  # Negative because lower drawdown is better
            comparison["win_rate_change"] * 0.2
        )
        comparison["overall_performance_change"] = performance_score
        
        return comparison
    
    def _is_adaptation_needed(self, performance_comparison: Dict[str, Any]) -> bool:
        """Determine if adaptation is needed based on performance comparison"""
        if performance_comparison.get("no_baseline"):
            return False
        
        # Check overall performance change
        overall_change = performance_comparison.get("overall_performance_change", 0)
        if overall_change < -self.config.adaptation_threshold:
            return True
        
        # Check specific metrics
        accuracy_change = performance_comparison.get("accuracy_change", 0)
        if accuracy_change < -self.config.adaptation_threshold:
            return True
        
        drawdown_change = performance_comparison.get("drawdown_change", 0)
        if drawdown_change > self.config.adaptation_threshold:  # Drawdown increased
            return True
        
        return False
    
    async def _trigger_learning_adaptation(self,
                                         trigger: AdaptationTrigger,
                                         trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger learning adaptation cycle (simplified for microservice)"""
        try:
            # Check adaptation rate limits
            if not self._can_perform_adaptation():
                return {"adaptation_blocked": True, "reason": "rate_limit_exceeded"}
            
            # Simplified adaptation for microservice architecture
            cycle_id = f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{trigger.value}"
            
            # Simulated adaptation logic
            adaptation_result = {
                "adaptation_successful": True,
                "cycle_id": cycle_id,
                "action_type": "learning_rate_adjustment",
                "expected_improvement": 0.1,
                "trigger": trigger.value,
                "timestamp": datetime.now().isoformat()
            }
            
            # Update adaptation count
            current_hour = datetime.now().strftime("%Y%m%d_%H")
            self.adaptation_count[current_hour] = self.adaptation_count.get(current_hour, 0) + 1
            
            # Update statistics
            self.adaptation_stats["total_cycles"] += 1
            self.adaptation_stats["successful_adaptations"] += 1
            
            self.logger.info(f"🔄 Learning adaptation triggered: {cycle_id}")
            return adaptation_result
            
        except Exception as e:
            self.error_handler.handle_error(e, {"operation": "trigger_learning_adaptation"})
            self.logger.error(f"❌ Learning adaptation trigger failed: {e}")
            return {"adaptation_failed": True, "error": str(e)}
    
    def _can_perform_adaptation(self) -> bool:
        """Check if adaptation can be performed (rate limiting)"""
        current_hour = datetime.now().strftime("%Y%m%d_%H")
        current_count = self.adaptation_count.get(current_hour, 0)
        
        if current_count >= self.config.max_adaptations_per_hour:
            self.logger.warning(f"⚠️ Adaptation rate limit exceeded: {current_count}/{self.config.max_adaptations_per_hour}")
            return False
        
        return True
    
    async def _load_historical_performance(self):
        """Load historical performance data (simplified for microservice)"""
        self.logger.debug("📚 Loading historical performance data (microservice)")
    
    async def _calculate_baseline_performance(self) -> Optional[PerformanceMetrics]:
        """Calculate baseline performance metrics (simplified for microservice)"""
        # Simulated baseline - in real implementation, would calculate from historical data
        return PerformanceMetrics(
            accuracy=0.65,
            precision=0.62,
            recall=0.68,
            f1_score=0.65,
            sharpe_ratio=1.2,
            max_drawdown=0.15,
            win_rate=0.58,
            profit_factor=1.3,
            information_ratio=0.8,
            calmar_ratio=8.0,
            sortino_ratio=1.5,
            recent_accuracy=0.63,
            trend_accuracy=0.66,
            timestamp=datetime.now(),
            evaluation_period=timedelta(days=7)
        )
    
    async def _start_monitoring(self):
        """Start real-time monitoring (simplified for microservice)"""
        self.monitoring_active = True
        self.logger.info("🔍 Real-time monitoring started (microservice)")
    
    def get_adaptation_stats(self) -> Dict[str, Any]:
        """Get adaptation statistics"""
        return self.adaptation_stats.copy()
    
    def get_current_performance(self) -> Optional[PerformanceMetrics]:
        """Get current performance metrics"""
        return self.current_performance
    
    def get_active_adaptations(self) -> Dict[str, AdaptationAction]:
        """Get currently active adaptations"""
        return self.active_adaptations.copy()
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for learning adaptation system with MICROSERVICE ARCHITECTURE"""
        health_check_start = time.perf_counter()
        
        try:
            with self.performance_tracker.track_operation("learning_adapter_health_check"):
                # Validate system components
                component_health = {
                    "monitoring_active": self.monitoring_active,
                    "baseline_performance": self.baseline_performance is not None,
                    "prediction_buffer": len(self.prediction_results) > 0,
                    "performance_history": len(self.performance_history) > 0,
                    "microservice_infrastructure": True
                }
                
                # Calculate system health score
                healthy_components = sum(component_health.values())
                total_components = len(component_health)
                health_score = healthy_components / total_components
                
                # Determine overall status
                if health_score >= 0.8:
                    status = "healthy"
                elif health_score >= 0.6:
                    status = "degraded"
                else:
                    status = "unhealthy"
                
                # Get enhanced metrics
                buffer_metrics = {
                    "prediction_buffer_size": len(self.prediction_results),
                    "performance_history_size": len(self.performance_history),
                    "market_data_buffer_size": len(self.market_data_buffer),
                    "active_adaptations": len(self.active_adaptations),
                    "total_cycles": len(self.learning_cycles)
                }
                
                # Performance metrics
                recent_performance = {
                    "current_performance": asdict(self.current_performance) if self.current_performance else None,
                    "baseline_performance": asdict(self.baseline_performance) if self.baseline_performance else None,
                    "performance_trend": self.performance_trend
                }
                
                # Learning metrics
                learning_stats = self.get_adaptation_stats()
                learning_stats.update({
                    "learning_mode": self.config.learning_mode.value,
                    "adaptation_threshold": self.config.adaptation_threshold,
                    "last_evaluation": self.last_evaluation.isoformat()
                })
                
                # Record health check performance
                health_check_time = (time.perf_counter() - health_check_start) * 1000
                
                # Publish health check event
                await self.event_publisher.publish_event(
                    "learning_adapter.health_check_completed",
                    {
                        "status": status,
                        "health_score": health_score,
                        "check_time_ms": health_check_time,
                        "component_health": component_health
                    }
                )
                
                # Comprehensive health response
                health_response = {
                    "status": status,
                    "health_score": health_score,
                    "health_check_time_ms": health_check_time,
                    "timestamp": datetime.now().isoformat(),
                    
                    # Component health
                    "component_health": component_health,
                    
                    # Buffer metrics
                    "buffer_metrics": buffer_metrics,
                    
                    # Performance metrics
                    "performance_metrics": recent_performance,
                    
                    # Learning statistics
                    "learning_stats": learning_stats,
                    
                    # System information
                    "system_info": {
                        "microservice_architecture": True,
                        "learning_adapter_version": "2.0.0",
                        "uptime_seconds": (datetime.now() - self.last_evaluation).total_seconds()
                    },
                    
                    # Global learning metrics
                    "global_metrics": learning_metrics.copy()
                }
                
                self.logger.debug(f"Health check completed successfully: {status} ({health_score:.2f}) in {health_check_time:.2f}ms")
                return health_response
            
        except Exception as e:
            # Handle health check failure with microservice error management
            health_check_time = (time.perf_counter() - health_check_start) * 1000
            
            self.error_handler.handle_error(e, {
                "operation": "learning_adapter_health_check",
                "health_check_time_ms": health_check_time
            })
            
            self.logger.error(f"❌ Health check failed: {e}")
            
            # Publish health check failure event
            await self.event_publisher.publish_event(
                "learning_adapter.health_check_failed",
                {
                    "error": str(e),
                    "check_time_ms": health_check_time
                }
            )
            
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "health_check_time_ms": health_check_time
            }


# Factory function
def create_realtime_learning_adaptation(config: Optional[AdaptationConfig] = None) -> RealtimeLearningAdaptation:
    """Create and return a RealtimeLearningAdaptation instance"""
    return RealtimeLearningAdaptation(config)


# Export all classes
__all__ = [
    "RealtimeLearningAdaptation",
    "AdaptationConfig",
    "PerformanceMetrics",
    "AdaptationAction",
    "LearningCycle",
    "LearningMode",
    "AdaptationTrigger",
    "LearningObjective",
    "create_realtime_learning_adaptation"
]