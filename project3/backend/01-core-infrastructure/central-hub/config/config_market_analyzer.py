"""
Market Analyzer Configuration - Suho AI Trading Platform
========================================================

Centralized configuration for Market Analyzer service.
Placeholder template for when the service is implemented.
"""

CONFIG_MARKET_ANALYZER = {
    # Service Metadata
    "service_info": {
        "name": "market-analyzer",
        "version": "1.0.0",
        "description": "Real-time market analysis with AI pattern recognition",
        "maintainer": "suho-ai-team@suho.ai",
        "environment": "development"
    },

    # HOT RELOAD: Analysis Parameters
    "business_rules": {
        "technical_analysis": {
            "indicators": ["RSI", "MACD", "Bollinger Bands", "Moving Averages"],
            "timeframes": ["M5", "M15", "H1", "H4"],
            "lookback_periods": 200,
            "signal_threshold": 0.7
        },
        "pattern_recognition": {
            "candlestick_patterns": ["hammer", "doji", "engulfing"],
            "chart_patterns": ["head_shoulders", "triangle", "flag"],
            "confidence_threshold": 0.8
        },
        "sentiment_analysis": {
            "news_sources": ["reuters", "bloomberg", "yahoo_finance"],
            "social_media": ["twitter", "reddit"],
            "sentiment_weight": 0.3
        }
    },

    # HOT RELOAD: AI Model Settings
    "ai_models": {
        "lstm_price_prediction": {
            "enabled": True,
            "sequence_length": 60,
            "prediction_horizon": 30,
            "retrain_frequency_hours": 24
        },
        "transformer_sentiment": {
            "enabled": True,
            "model_name": "bert-base-uncased",
            "max_sequence_length": 512
        }
    },

    # STATIC REFERENCES: Infrastructure
    "static_references": {
        "database_url": "ENV:DATABASE_URL",
        "nats_url": "ENV:NATS_URL",
        "news_api_key": "ENV:NEWS_API_KEY",
        "social_api_keys": "ENV:SOCIAL_API_KEYS"
    },

    # Configuration Metadata
    "config_meta": {
        "version": "1.0.0",
        "last_updated": "2025-09-29T18:45:00Z",
        "updated_by": "ai-team",
        "hot_reload_enabled": True,
        "validation_schema": "market_analyzer_config_v1",
        "dependencies": ["trading-engine", "data-ingestion"]
    }
}

__all__ = ['CONFIG_MARKET_ANALYZER']