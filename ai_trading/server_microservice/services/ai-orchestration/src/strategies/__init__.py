"""
AI Strategy Engine - Comprehensive Trading Strategy Framework
AI-powered strategy management with adaptive algorithms and risk control
"""

from .adaptive_strategy_engine import AdaptiveStrategyEngine, StrategyType, StrategyConfig
from .multi_timeframe_coordinator import MultiTimeframeCoordinator, TimeframeConfig, TimeframeType
from .risk_management_ai import RiskManagementAI, RiskLevel, RiskConfig, PositionRisk
from .execution_optimizer import ExecutionOptimizer, ExecutionStrategy, OrderType, ExecutionConfig
from .strategy_performance_tracker import StrategyPerformanceTracker, PerformanceMetrics, TrackingConfig

__all__ = [
    'AdaptiveStrategyEngine',
    'StrategyType',
    'StrategyConfig',
    'MultiTimeframeCoordinator',
    'TimeframeConfig',
    'TimeframeType',
    'RiskManagementAI',
    'RiskLevel',
    'RiskConfig',
    'PositionRisk',
    'ExecutionOptimizer',
    'ExecutionStrategy',
    'OrderType', 
    'ExecutionConfig',
    'StrategyPerformanceTracker',
    'PerformanceMetrics',
    'TrackingConfig'
]

__version__ = "1.0.0"
__service__ = "ai-orchestration"
__component_type__ = "strategies"