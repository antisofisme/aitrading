"""
Trading Engine Configuration - Suho AI Trading Platform
=======================================================

Centralized configuration for Trading Engine service.
Placeholder template for when the service is implemented.
"""

CONFIG_TRADING_ENGINE = {
    # Service Metadata
    "service_info": {
        "name": "trading-engine",
        "version": "1.0.0",
        "description": "Core trading execution engine with AI-driven decision making",
        "maintainer": "suho-trading-team@suho.ai",
        "environment": "development"
    },

    # HOT RELOAD: Trading Rules & Logic
    "business_rules": {
        "position_management": {
            "max_position_size_usd": 1000000,
            "max_daily_volume_usd": 10000000,
            "max_positions_per_symbol": 5,
            "position_timeout_minutes": 60
        },
        "risk_management": {
            "max_drawdown_percent": 5.0,
            "stop_loss_percent": 2.0,
            "take_profit_percent": 4.0,
            "daily_loss_limit_usd": 50000
        },
        "execution": {
            "order_timeout_ms": 10000,
            "retry_attempts": 3,
            "slippage_tolerance_pips": 2,
            "minimum_spread_pips": 1
        }
    },

    # HOT RELOAD: AI & ML Parameters
    "ai_parameters": {
        "model_confidence_threshold": 0.75,
        "prediction_horizon_minutes": 30,
        "feature_importance_threshold": 0.1,
        "ensemble_weight": {
            "technical_analysis": 0.4,
            "sentiment_analysis": 0.3,
            "fundamental_analysis": 0.3
        }
    },

    # HOT RELOAD: Market Data
    "market_data": {
        "symbols": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"],
        "timeframes": ["M1", "M5", "M15", "H1", "H4", "D1"],
        "data_providers": ["mt5", "alpha_vantage", "yahoo_finance"],
        "update_frequency_ms": 100
    },

    # STATIC REFERENCES: Infrastructure
    "static_references": {
        "database_url": "ENV:DATABASE_URL",
        "nats_url": "ENV:NATS_URL",
        "mt5_server": "ENV:MT5_SERVER",
        "mt5_login": "ENV:MT5_LOGIN",
        "mt5_password": "ENV:MT5_PASSWORD",
        "api_keys": "ENV:TRADING_API_KEYS"
    },

    # Configuration Metadata
    "config_meta": {
        "version": "1.0.0",
        "last_updated": "2025-09-29T18:45:00Z",
        "updated_by": "trading-team",
        "hot_reload_enabled": True,
        "validation_schema": "trading_engine_config_v1",
        "dependencies": ["api-gateway", "market-data-service"]
    }
}

__all__ = ['CONFIG_TRADING_ENGINE']