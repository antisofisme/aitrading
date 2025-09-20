"""
Configuration settings for Output Execution modules
Centralized configuration for strategies, risk management, and execution
"""

import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Import centralized configuration manager
from ....shared.infrastructure.config_manager import get_config_manager


class ExecutionMode(Enum):
    """Execution modes"""
    PAPER = "paper"
    LIVE = "live"
    SIMULATION = "simulation"
    BACKTEST = "backtest"
    FORWARD_TEST = "forward_test"


class RiskLevel(Enum):
    """Risk levels"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    CUSTOM = "custom"


class OrderType(Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"
    ICEBERG = "iceberg"
    TWAP = "twap"
    VWAP = "vwap"


@dataclass
class TradingStrategiesConfig:
    """Trading strategies configuration"""
    # Strategy execution
    strategies_enabled: bool = field(default_factory=lambda: get_config_manager().get('trading_strategies.enabled', True))
    execution_mode: ExecutionMode = field(default_factory=lambda: ExecutionMode(get_config_manager().get('trading_strategies.execution_mode', 'paper')))
    
    # Multi-strategy execution
    multi_strategy_enabled: bool = field(default_factory=lambda: get_config_manager().get('trading_strategies.multi_strategy_enabled', True))
    max_concurrent_strategies: int = field(default_factory=lambda: get_config_manager().get('trading_strategies.max_concurrent_strategies', 5))
    strategy_allocation: Dict[str, float] = field(default_factory=lambda: {
        "trend_following": get_config_manager().get('trading_strategies.allocation.trend_following', 0.3),
        "mean_reversion": get_config_manager().get('trading_strategies.allocation.mean_reversion', 0.2),
        "breakout": get_config_manager().get('trading_strategies.allocation.breakout', 0.2),
        "arbitrage": get_config_manager().get('trading_strategies.allocation.arbitrage', 0.1),
        "ai_driven": get_config_manager().get('trading_strategies.allocation.ai_driven', 0.2)
    })
    
    # Strategy parameters
    trend_following_enabled: bool = field(default_factory=lambda: get_config_manager().get('trading_strategies.trend_following.enabled', True))
    trend_following_periods: List[int] = field(default_factory=lambda: 
        [int(x) for x in get_config_manager().get('trading_strategies.trend_following.periods', '20,50,200').split(',')]
    )
    
    mean_reversion_enabled: bool = field(default_factory=lambda: get_config_manager().get('trading_strategies.mean_reversion.enabled', True))
    mean_reversion_lookback: int = field(default_factory=lambda: get_config_manager().get('trading_strategies.mean_reversion.lookback', 14))
    mean_reversion_threshold: float = field(default_factory=lambda: get_config_manager().get('trading_strategies.mean_reversion.threshold', 2.0))
    
    breakout_enabled: bool = field(default_factory=lambda: get_config_manager().get('trading_strategies.breakout.enabled', True))
    breakout_confirmation_bars: int = field(default_factory=lambda: get_config_manager().get('trading_strategies.breakout.confirmation_bars', 3))
    breakout_volume_confirmation: bool = field(default_factory=lambda: get_config_manager().get('trading_strategies.breakout.volume_confirmation', True))
    
    # AI-driven strategies
    ai_driven_enabled: bool = field(default_factory=lambda: get_config_manager().get('trading_strategies.ai_driven.enabled', True))
    ai_confidence_threshold: float = field(default_factory=lambda: get_config_manager().get('trading_strategies.ai_driven.confidence_threshold', 0.7))
    ai_consensus_required: bool = field(default_factory=lambda: get_config_manager().get('trading_strategies.ai_driven.consensus_required', True))
    
    # Portfolio management
    portfolio_rebalancing_enabled: bool = field(default_factory=lambda: get_config_manager().get('trading_strategies.portfolio.rebalancing_enabled', True))
    rebalancing_frequency: str = field(default_factory=lambda: get_config_manager().get('trading_strategies.portfolio.rebalancing_frequency', 'daily'))  # hourly, daily, weekly
    correlation_based_allocation: bool = field(default_factory=lambda: get_config_manager().get('trading_strategies.portfolio.correlation_based_allocation', True))


@dataclass
class RiskManagementConfig:
    """Risk management configuration"""
    # Risk management
    risk_management_enabled: bool = field(default_factory=lambda: get_config_manager().get('advanced_risk_management.enabled', True))
    risk_level: RiskLevel = field(default_factory=lambda: RiskLevel(get_config_manager().get('advanced_risk_management.risk_level', 'moderate')))
    
    # Position sizing
    position_sizing_enabled: bool = field(default_factory=lambda: get_config_manager().get('advanced_risk_management.position_sizing.enabled', True))
    position_sizing_method: str = field(default_factory=lambda: get_config_manager().get('advanced_risk_management.position_sizing.method', 'kelly'))  # fixed, percentage, kelly, volatility
    max_position_size: float = field(default_factory=lambda: get_config_manager().get('advanced_risk_management.position_sizing.max_position_size', 0.02))  # 2% of account
    
    # Stop loss and take profit
    stop_loss_enabled: bool = field(default_factory=lambda: get_config_manager().get('advanced_risk_management.stop_loss.enabled', True))
    stop_loss_method: str = field(default_factory=lambda: get_config_manager().get('advanced_risk_management.stop_loss.method', 'atr'))  # fixed, percentage, atr, volatility
    stop_loss_atr_multiplier: float = field(default_factory=lambda: get_config_manager().get('advanced_risk_management.stop_loss.atr_multiplier', 2.0))
    
    take_profit_enabled: bool = field(default_factory=lambda: get_config_manager().get('advanced_risk_management.take_profit.enabled', True))
    take_profit_method: str = field(default_factory=lambda: get_config_manager().get('advanced_risk_management.take_profit.method', 'risk_reward'))  # fixed, percentage, risk_reward
    risk_reward_ratio: float = field(default_factory=lambda: get_config_manager().get('advanced_risk_management.take_profit.risk_reward_ratio', 2.0))
    
    # Trailing stops
    trailing_stop_enabled: bool = field(default_factory=lambda: get_config_manager().get('advanced_risk_management.trailing_stop.enabled', True))
    trailing_stop_distance: float = field(default_factory=lambda: get_config_manager().get('advanced_risk_management.trailing_stop.distance', 0.001))  # 10 pips
    trailing_stop_activation: float = field(default_factory=lambda: get_config_manager().get('advanced_risk_management.trailing_stop.activation', 0.5))  # 50% of TP
    
    # Drawdown protection
    drawdown_protection_enabled: bool = field(default_factory=lambda: get_config_manager().get('advanced_risk_management.drawdown_protection.enabled', True))
    max_daily_drawdown: float = field(default_factory=lambda: get_config_manager().get('advanced_risk_management.drawdown_protection.max_daily_drawdown', 0.05))  # 5%
    max_total_drawdown: float = field(default_factory=lambda: get_config_manager().get('advanced_risk_management.drawdown_protection.max_total_drawdown', 0.20))  # 20%
    
    # Exposure limits
    exposure_limits_enabled: bool = field(default_factory=lambda: get_config_manager().get('advanced_risk_management.exposure_limits.enabled', True))
    max_currency_exposure: float = field(default_factory=lambda: get_config_manager().get('advanced_risk_management.exposure_limits.max_currency_exposure', 0.10))  # 10%
    max_correlation_exposure: float = field(default_factory=lambda: get_config_manager().get('advanced_risk_management.exposure_limits.max_correlation_exposure', 0.15))  # 15%
    
    # Real-time monitoring
    realtime_monitoring_enabled: bool = field(default_factory=lambda: get_config_manager().get('advanced_risk_management.realtime_monitoring.enabled', True))
    monitoring_frequency: int = field(default_factory=lambda: get_config_manager().get('advanced_risk_management.realtime_monitoring.frequency_seconds', 10))  # seconds
    emergency_stop_enabled: bool = field(default_factory=lambda: get_config_manager().get('advanced_risk_management.realtime_monitoring.emergency_stop_enabled', True))


@dataclass
class ExecutionEngineConfig:
    """Execution engine configuration"""
    # Execution engine
    execution_enabled: bool = field(default_factory=lambda: get_config_manager().get('execution_engine.enabled', True))
    execution_delay: int = field(default_factory=lambda: get_config_manager().get('execution_engine.execution_delay_ms', 100))  # milliseconds
    
    # Order management
    order_management_enabled: bool = field(default_factory=lambda: get_config_manager().get('execution_engine.order_management.enabled', True))
    default_order_type: OrderType = field(default_factory=lambda: OrderType(get_config_manager().get('execution_engine.order_management.default_order_type', 'market')))
    order_timeout: int = field(default_factory=lambda: get_config_manager().get('execution_engine.order_management.order_timeout_seconds', 30))  # seconds
    
    # Slippage control
    slippage_control_enabled: bool = field(default_factory=lambda: get_config_manager().get('execution_engine.slippage_control.enabled', True))
    max_slippage: float = field(default_factory=lambda: get_config_manager().get('execution_engine.slippage_control.max_slippage', 0.0001))  # 1 pip
    slippage_tolerance: float = field(default_factory=lambda: get_config_manager().get('execution_engine.slippage_control.tolerance', 0.5))  # 50%
    
    # Execution algorithms
    execution_algorithms_enabled: bool = field(default_factory=lambda: get_config_manager().get('execution_engine.algorithms.enabled', True))
    twap_enabled: bool = field(default_factory=lambda: get_config_manager().get('execution_engine.algorithms.twap_enabled', True))
    vwap_enabled: bool = field(default_factory=lambda: get_config_manager().get('execution_engine.algorithms.vwap_enabled', True))
    iceberg_enabled: bool = field(default_factory=lambda: get_config_manager().get('execution_engine.algorithms.iceberg_enabled', True))
    
    # Market impact minimization
    market_impact_minimization: bool = field(default_factory=lambda: get_config_manager().get('execution_engine.market_impact.minimization_enabled', True))
    max_market_impact: float = field(default_factory=lambda: get_config_manager().get('execution_engine.market_impact.max_impact', 0.0005))  # 5 pips
    
    # Partial fills
    partial_fills_enabled: bool = field(default_factory=lambda: get_config_manager().get('execution_engine.partial_fills.enabled', True))
    min_fill_size: float = field(default_factory=lambda: get_config_manager().get('execution_engine.partial_fills.min_fill_size', 0.01))  # 0.01 lots
    
    # Latency optimization
    latency_optimization_enabled: bool = field(default_factory=lambda: get_config_manager().get('execution_engine.latency_optimization.enabled', True))
    max_latency: int = field(default_factory=lambda: get_config_manager().get('execution_engine.latency_optimization.max_latency_ms', 100))  # milliseconds
    
    # Broker integration
    broker_integration_enabled: bool = field(default_factory=lambda: get_config_manager().get('execution_engine.broker_integration.enabled', True))
    primary_broker: str = field(default_factory=lambda: get_config_manager().get('execution_engine.broker_integration.primary_broker', 'FBS-Demo'))
    backup_brokers: List[str] = field(default_factory=lambda: 
        get_config_manager().get('execution_engine.broker_integration.backup_brokers', 'IC-Markets,Dukascopy').split(',')
    )


@dataclass
class DashboardConfig:
    """Live trading dashboard configuration"""
    # Dashboard
    dashboard_enabled: bool = field(default_factory=lambda: get_config_manager().get('dashboard.enabled', True))
    dashboard_update_frequency: int = field(default_factory=lambda: get_config_manager().get('dashboard.update_frequency_ms', 1000))  # milliseconds
    
    # Real-time data
    realtime_data_enabled: bool = field(default_factory=lambda: get_config_manager().get('dashboard.realtime_data.enabled', True))
    data_refresh_rate: int = field(default_factory=lambda: get_config_manager().get('dashboard.realtime_data.refresh_rate_ms', 500))  # milliseconds
    
    # Performance metrics
    performance_metrics_enabled: bool = field(default_factory=lambda: get_config_manager().get('dashboard.performance_metrics.enabled', True))
    metrics_display: List[str] = field(default_factory=lambda: 
        get_config_manager().get('dashboard.performance_metrics.display_metrics', 'pnl,drawdown,sharpe,win_rate,trades_today').split(',')
    )
    
    # Risk monitoring
    risk_monitoring_display: bool = field(default_factory=lambda: get_config_manager().get('dashboard.risk_monitoring.display_enabled', True))
    risk_alerts_enabled: bool = field(default_factory=lambda: get_config_manager().get('dashboard.risk_monitoring.alerts_enabled', True))
    
    # Portfolio overview
    portfolio_overview_enabled: bool = field(default_factory=lambda: get_config_manager().get('dashboard.portfolio_overview.enabled', True))
    portfolio_allocation_display: bool = field(default_factory=lambda: get_config_manager().get('dashboard.portfolio_overview.allocation_display', True))
    
    # Charts and visualization
    charts_enabled: bool = field(default_factory=lambda: get_config_manager().get('dashboard.charts.enabled', True))
    chart_types: List[str] = field(default_factory=lambda: 
        get_config_manager().get('dashboard.charts.chart_types', 'candlestick,line,volume,indicators').split(',')
    )
    
    # Notifications
    notifications_enabled: bool = field(default_factory=lambda: get_config_manager().get('dashboard.notifications.enabled', True))
    notification_methods: List[str] = field(default_factory=lambda: 
        get_config_manager().get('dashboard.notifications.methods', 'email,telegram,desktop').split(',')
    )
    
    # Export and reporting
    export_enabled: bool = field(default_factory=lambda: get_config_manager().get('dashboard.export.enabled', True))
    export_formats: List[str] = field(default_factory=lambda: 
        get_config_manager().get('dashboard.export.formats', 'csv,excel,pdf,json').split(',')
    )
    
    # Multi-broker support
    multi_broker_display: bool = field(default_factory=lambda: get_config_manager().get('dashboard.multi_broker.display_enabled', True))
    broker_comparison_enabled: bool = field(default_factory=lambda: get_config_manager().get('dashboard.multi_broker.comparison_enabled', True))


@dataclass
class PerformanceAnalyticsConfig:
    """Performance analytics configuration"""
    # Performance analytics
    analytics_enabled: bool = field(default_factory=lambda: get_config_manager().get('performance_analytics.enabled', True))
    analytics_update_frequency: str = field(default_factory=lambda: get_config_manager().get('performance_analytics.update_frequency', 'hourly'))  # realtime, hourly, daily
    
    # Statistical analysis
    statistical_analysis_enabled: bool = field(default_factory=lambda: get_config_manager().get('performance_analytics.statistical_analysis.enabled', True))
    statistics_metrics: List[str] = field(default_factory=lambda: 
        get_config_manager().get('performance_analytics.statistical_analysis.statistics', 'sharpe,sortino,calmar,max_drawdown,var,cvar').split(',')
    )
    
    # Backtesting
    backtesting_enabled: bool = field(default_factory=lambda: get_config_manager().get('performance_analytics.backtesting.enabled', True))
    backtesting_period: int = field(default_factory=lambda: get_config_manager().get('performance_analytics.backtesting.period_days', 252))  # days
    walk_forward_analysis: bool = field(default_factory=lambda: get_config_manager().get('performance_analytics.backtesting.walk_forward_analysis', True))
    
    # Benchmark comparison
    benchmark_comparison_enabled: bool = field(default_factory=lambda: get_config_manager().get('performance_analytics.benchmark_comparison.enabled', True))
    benchmark_instruments: List[str] = field(default_factory=lambda: 
        get_config_manager().get('performance_analytics.benchmark_comparison.instruments', 'SPX500,EURUSD,XAUUSD').split(',')
    )
    
    # Attribution analysis
    attribution_analysis_enabled: bool = field(default_factory=lambda: get_config_manager().get('performance_analytics.attribution_analysis.enabled', True))
    attribution_levels: List[str] = field(default_factory=lambda: 
        get_config_manager().get('performance_analytics.attribution_analysis.levels', 'strategy,instrument,sector,timeframe').split(',')
    )
    
    # Risk-adjusted returns
    risk_adjusted_returns_enabled: bool = field(default_factory=lambda: get_config_manager().get('performance_analytics.risk_adjusted_returns.enabled', True))
    risk_free_rate: float = field(default_factory=lambda: get_config_manager().get('performance_analytics.risk_adjusted_returns.risk_free_rate', 0.05))  # 5%
    
    # Monte Carlo analysis
    monte_carlo_enabled: bool = field(default_factory=lambda: get_config_manager().get('performance_analytics.monte_carlo.enabled', True))
    monte_carlo_simulations: int = field(default_factory=lambda: get_config_manager().get('performance_analytics.monte_carlo.simulations', 1000))
    
    # Stress testing
    stress_testing_enabled: bool = field(default_factory=lambda: get_config_manager().get('performance_analytics.stress_testing.enabled', True))
    stress_scenarios: List[str] = field(default_factory=lambda: 
        get_config_manager().get('performance_analytics.stress_testing.scenarios', '2008_crisis,covid_2020,flash_crash').split(',')
    )


@dataclass
class TelegramBotConfig:
    """Telegram bot configuration"""
    # Telegram bot
    telegram_enabled: bool = field(default_factory=lambda: get_config_manager().get('advanced_telegram.enabled', False))
    bot_token: str = field(default_factory=lambda: get_config_manager().get('advanced_telegram.bot_token', ''))
    chat_id: str = field(default_factory=lambda: get_config_manager().get('advanced_telegram.chat_id', ''))
    
    # Notifications
    trade_notifications: bool = field(default_factory=lambda: get_config_manager().get('advanced_telegram.notifications.trade_notifications', True))
    risk_alerts: bool = field(default_factory=lambda: get_config_manager().get('advanced_telegram.notifications.risk_alerts', True))
    performance_updates: bool = field(default_factory=lambda: get_config_manager().get('advanced_telegram.notifications.performance_updates', True))
    
    # Update frequency
    update_frequency: str = field(default_factory=lambda: get_config_manager().get('advanced_telegram.updates.frequency', 'hourly'))  # realtime, hourly, daily
    daily_summary: bool = field(default_factory=lambda: get_config_manager().get('advanced_telegram.updates.daily_summary', True))
    
    # Interactive features
    interactive_commands: bool = field(default_factory=lambda: get_config_manager().get('advanced_telegram.interactive.commands_enabled', True))
    command_whitelist: List[str] = field(default_factory=lambda: 
        get_config_manager().get('advanced_telegram.interactive.command_whitelist', 'status,performance,positions,stop_trading').split(',')
    )
    
    # Security
    user_authentication: bool = field(default_factory=lambda: get_config_manager().get('advanced_telegram.security.user_authentication', True))
    authorized_users: List[str] = field(default_factory=lambda: 
        get_config_manager().get('advanced_telegram.security.authorized_users', '').split(',') if get_config_manager().get('advanced_telegram.security.authorized_users', '') else []
    )


@dataclass
class OutputExecutionSettings:
    """Main output execution settings"""
    # Module settings
    enabled: bool = field(default_factory=lambda: get_config_manager().get('output_execution.enabled', True))
    debug_mode: bool = field(default_factory=lambda: get_config_manager().get('output_execution.debug_mode', False))
    
    # Configuration components
    strategies: TradingStrategiesConfig = field(default_factory=TradingStrategiesConfig)
    risk_management: RiskManagementConfig = field(default_factory=RiskManagementConfig)
    execution_engine: ExecutionEngineConfig = field(default_factory=ExecutionEngineConfig)
    dashboard: DashboardConfig = field(default_factory=DashboardConfig)
    performance_analytics: PerformanceAnalyticsConfig = field(default_factory=PerformanceAnalyticsConfig)
    telegram_bot: TelegramBotConfig = field(default_factory=TelegramBotConfig)
    
    # Execution settings
    execution_mode: ExecutionMode = field(default_factory=lambda: ExecutionMode(get_config_manager().get('output_execution.processing.execution_mode', 'paper')))
    max_simultaneous_orders: int = field(default_factory=lambda: get_config_manager().get('output_execution.processing.max_simultaneous_orders', 10))
    order_queue_size: int = field(default_factory=lambda: get_config_manager().get('output_execution.processing.order_queue_size', 1000))
    
    # Performance settings
    performance_monitoring_enabled: bool = field(default_factory=lambda: get_config_manager().get('output_execution.performance_monitoring.enabled', True))
    performance_metrics: List[str] = field(default_factory=lambda: 
        get_config_manager().get('output_execution.performance_monitoring.metrics', 'latency,throughput,success_rate,slippage').split(',')
    )
    
    # Database integration
    database_enabled: bool = field(default_factory=lambda: get_config_manager().get('output_execution.database_integration.enabled', True))
    store_orders: bool = field(default_factory=lambda: get_config_manager().get('output_execution.database_integration.store_orders', True))
    store_trades: bool = field(default_factory=lambda: get_config_manager().get('output_execution.database_integration.store_trades', True))
    store_performance: bool = field(default_factory=lambda: get_config_manager().get('output_execution.database_integration.store_performance', True))
    
    # Logging and monitoring
    logging_enabled: bool = field(default_factory=lambda: get_config_manager().get('output_execution.logging.enabled', True))
    logging_level: str = field(default_factory=lambda: get_config_manager().get('output_execution.logging.level', 'INFO'))
    metrics_enabled: bool = field(default_factory=lambda: get_config_manager().get('output_execution.logging.metrics_enabled', True))
    
    # Error handling
    error_handling_enabled: bool = field(default_factory=lambda: get_config_manager().get('output_execution.error_handling.enabled', True))
    max_retries: int = field(default_factory=lambda: get_config_manager().get('output_execution.error_handling.max_retries', 3))
    retry_delay: int = field(default_factory=lambda: get_config_manager().get('output_execution.error_handling.retry_delay_seconds', 1))
    
    # Health checks
    health_check_enabled: bool = field(default_factory=lambda: get_config_manager().get('output_execution.health_checks.enabled', True))
    health_check_interval: int = field(default_factory=lambda: get_config_manager().get('output_execution.health_checks.interval_seconds', 60))  # 1 minute


# Global settings instance
output_execution_settings = OutputExecutionSettings()


def get_output_execution_settings() -> OutputExecutionSettings:
    """Get output execution settings"""
    return output_execution_settings


def get_enabled_strategies() -> List[str]:
    """Get list of enabled trading strategies"""
    enabled_strategies = []
    settings = output_execution_settings.strategies
    
    if settings.trend_following_enabled:
        enabled_strategies.append("trend_following")
    if settings.mean_reversion_enabled:
        enabled_strategies.append("mean_reversion")
    if settings.breakout_enabled:
        enabled_strategies.append("breakout")
    if settings.ai_driven_enabled:
        enabled_strategies.append("ai_driven")
    
    return enabled_strategies


def get_risk_management_config() -> Dict[str, Any]:
    """Get risk management configuration"""
    settings = output_execution_settings.risk_management
    return {
        "enabled": settings.risk_management_enabled,
        "risk_level": settings.risk_level.value,
        "position_sizing": settings.position_sizing_enabled,
        "max_position_size": settings.max_position_size,
        "stop_loss_enabled": settings.stop_loss_enabled,
        "take_profit_enabled": settings.take_profit_enabled,
        "trailing_stop_enabled": settings.trailing_stop_enabled,
        "drawdown_protection": settings.drawdown_protection_enabled,
        "max_daily_drawdown": settings.max_daily_drawdown,
        "max_total_drawdown": settings.max_total_drawdown,
        "realtime_monitoring": settings.realtime_monitoring_enabled
    }


def get_execution_config() -> Dict[str, Any]:
    """Get execution configuration"""
    settings = output_execution_settings.execution_engine
    return {
        "enabled": settings.execution_enabled,
        "execution_delay": settings.execution_delay,
        "default_order_type": settings.default_order_type.value,
        "slippage_control": settings.slippage_control_enabled,
        "max_slippage": settings.max_slippage,
        "execution_algorithms": settings.execution_algorithms_enabled,
        "market_impact_minimization": settings.market_impact_minimization,
        "latency_optimization": settings.latency_optimization_enabled,
        "primary_broker": settings.primary_broker,
        "backup_brokers": settings.backup_brokers
    }


def get_dashboard_config() -> Dict[str, Any]:
    """Get dashboard configuration"""
    settings = output_execution_settings.dashboard
    return {
        "enabled": settings.dashboard_enabled,
        "update_frequency": settings.dashboard_update_frequency,
        "realtime_data": settings.realtime_data_enabled,
        "performance_metrics": settings.performance_metrics_enabled,
        "risk_monitoring": settings.risk_monitoring_display,
        "portfolio_overview": settings.portfolio_overview_enabled,
        "charts_enabled": settings.charts_enabled,
        "notifications_enabled": settings.notifications_enabled,
        "export_enabled": settings.export_enabled,
        "multi_broker_display": settings.multi_broker_display
    }


def get_performance_analytics_config() -> Dict[str, Any]:
    """Get performance analytics configuration"""
    settings = output_execution_settings.performance_analytics
    return {
        "enabled": settings.analytics_enabled,
        "update_frequency": settings.analytics_update_frequency,
        "statistical_analysis": settings.statistical_analysis_enabled,
        "backtesting": settings.backtesting_enabled,
        "benchmark_comparison": settings.benchmark_comparison_enabled,
        "attribution_analysis": settings.attribution_analysis_enabled,
        "risk_adjusted_returns": settings.risk_adjusted_returns_enabled,
        "monte_carlo": settings.monte_carlo_enabled,
        "stress_testing": settings.stress_testing_enabled
    }


def get_telegram_config() -> Dict[str, Any]:
    """Get Telegram bot configuration"""
    settings = output_execution_settings.telegram_bot
    return {
        "enabled": settings.telegram_enabled,
        "bot_token": settings.bot_token,
        "chat_id": settings.chat_id,
        "trade_notifications": settings.trade_notifications,
        "risk_alerts": settings.risk_alerts,
        "performance_updates": settings.performance_updates,
        "update_frequency": settings.update_frequency,
        "interactive_commands": settings.interactive_commands,
        "user_authentication": settings.user_authentication
    }


def get_strategy_allocation() -> Dict[str, float]:
    """Get strategy allocation weights"""
    settings = output_execution_settings.strategies
    return settings.strategy_allocation


def is_live_trading_enabled() -> bool:
    """Check if live trading is enabled"""
    return output_execution_settings.execution_mode == ExecutionMode.LIVE


def get_max_risk_per_trade() -> float:
    """Get maximum risk per trade"""
    settings = output_execution_settings.risk_management
    return settings.max_position_size


def get_enabled_notification_methods() -> List[str]:
    """Get list of enabled notification methods"""
    settings = output_execution_settings.dashboard
    return settings.notification_methods if settings.notifications_enabled else []