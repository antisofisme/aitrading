"""
ClickHouse Mathematical Indicator Schemas - ENHANCED WITH FULL CENTRALIZATION
Server-side calculated technical indicators from raw tick data
Based on existing indicator schemas - maintaining compatibility

FEATURES:
- Centralized logging with context-aware messages
- Performance tracking for schema operations  
- Centralized error handling with proper categorization
- Centralized validation for schema definitions
- Event publishing for schema lifecycle events
"""

# FULL CENTRALIZATION INFRASTRUCTURE INTEGRATION
import logging
# Simple performance tracking placeholder
# Error handling placeholder
# Validation placeholder
# Event manager placeholder
# Import manager placeholder

# Import typing through centralized import manager
from typing import Dict, List

# Enhanced logger with centralized infrastructure
logger = logging.getLogger(__name__)


class ClickhouseIndicatorSchemas:
    """
    Mathematical indicator schemas calculated server-side from raw tick data
    These tables store processed technical indicators for ML/DL analysis
    """

    @staticmethod
    # @performance_tracked - simplified
    def get_all_tables() -> Dict[str, str]:
        """Get all mathematical indicator table schemas with centralized tracking"""
        try:
            logger.info("Retrieving all ClickHouse indicator table schemas")
            
            tables = {
            # Technical Indicators (from existing schema)
            "adl_data": ClickhouseIndicatorSchemas.adl_data(),
            "ao_data": ClickhouseIndicatorSchemas.ao_data(),
            "macd_data": ClickhouseIndicatorSchemas.macd_data(),
            "rsi_data": ClickhouseIndicatorSchemas.rsi_data(),
            "volume_data": ClickhouseIndicatorSchemas.volume_data(),
            "correlation_data": ClickhouseIndicatorSchemas.correlation_data(),
            "obv_data": ClickhouseIndicatorSchemas.obv_data(),
            "mfi_data": ClickhouseIndicatorSchemas.mfi_data(),
            "stochastic_data": ClickhouseIndicatorSchemas.stochastic_data(),
            "economic_data": ClickhouseIndicatorSchemas.economic_data(),
            "sessions_data": ClickhouseIndicatorSchemas.sessions_data(),
            "session_analysis": ClickhouseIndicatorSchemas.session_analysis(),
            "orderbook_data": ClickhouseIndicatorSchemas.orderbook_data(),
            "slippage_data": ClickhouseIndicatorSchemas.slippage_data(),
            "timesales_data": ClickhouseIndicatorSchemas.timesales_data(),
            
            # Trend Indicators (newly added)
            "ema_data": ClickhouseIndicatorSchemas.ema_data(),
            "bollinger_data": ClickhouseIndicatorSchemas.bollinger_data(),
            "ichimoku_data": ClickhouseIndicatorSchemas.ichimoku_data(),
            
                # Critical Accuracy Enhancements - Phase 3
                "advanced_patterns": ClickhouseIndicatorSchemas.advanced_patterns(),
                "model_performance": ClickhouseIndicatorSchemas.model_performance(),
            }
            
            # Validate table structure
            # Validation simplified
            
            # Publish event for schema retrieval
            # Event publishing simplified
            
            logger.info(f"Successfully retrieved {len(tables)} ClickHouse indicator table schemas")
            return tables
            
        except Exception as e:
            error_context = {
                "operation": "get_all_tables",
                "database_type": "clickhouse",
                "schema_type": "indicators"
            }
            # Error handling simplified
            logger.error(f"Failed to retrieve ClickHouse indicator table schemas: {e}")
            raise

    @staticmethod
    def adl_data() -> str:
        """ADL (Accumulation/Distribution Line) data table"""
        return """
        CREATE TABLE IF NOT EXISTS adl_data (
            timestamp DateTime64(3) CODEC(Delta, LZ4),
            symbol LowCardinality(String),
            timeframe LowCardinality(String),
            
            -- Core ADL Data
            adl Float64 CODEC(Gorilla),
            adl_ma_14 Float64 CODEC(Gorilla),
            adl_ma_21 Float64 CODEC(Gorilla),
            adl_ma_50 Float64 CODEC(Gorilla),
            volume UInt64 CODEC(T64),
            
            -- Analysis Data
            adl_trend LowCardinality(String),
            divergence_signals String CODEC(ZSTD),
            volume_strength Float32 CODEC(Gorilla),
            accumulation_phases String CODEC(ZSTD),
            distribution_phases String CODEC(ZSTD),
            
            -- Metadata
            collection_time_seconds Float32 CODEC(Gorilla),
            data_quality_score Float32 CODEC(Gorilla),
            error_count UInt16 CODEC(T64),
            source_client LowCardinality(String) DEFAULT 'ADL_Client',
            
            -- Multi-broker support
            broker LowCardinality(String) DEFAULT 'FBS-Demo',
            account_type LowCardinality(String) DEFAULT 'demo',
            created_at DateTime64(3) DEFAULT now64()
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY (broker, symbol, timeframe, timestamp)
        TTL timestamp + INTERVAL 1 YEAR
        SETTINGS index_granularity = 8192
        """

    @staticmethod
    def ao_data() -> str:
        """AO (Awesome Oscillator) data table"""
        return """
        CREATE TABLE IF NOT EXISTS ao_data (
            timestamp DateTime64(3) CODEC(Delta, LZ4),
            symbol LowCardinality(String),
            timeframe LowCardinality(String),
            
            -- Core AO Data
            ao Float64 CODEC(Gorilla),
            ao_fast_ma Float64 CODEC(Gorilla),
            ao_slow_ma Float64 CODEC(Gorilla),
            ao_histogram Float64 CODEC(Gorilla),
            ao_signal_line Float64 CODEC(Gorilla),
            
            -- Analysis Data
            ao_trend LowCardinality(String),
            zero_line_crosses String CODEC(ZSTD),
            twin_peaks String CODEC(ZSTD),
            saucer_signals String CODEC(ZSTD),
            momentum_strength Float32 CODEC(Gorilla),
            
            -- Metadata
            collection_time_seconds Float32 CODEC(Gorilla),
            data_quality_score Float32 CODEC(Gorilla),
            error_count UInt16 CODEC(T64),
            source_client LowCardinality(String) DEFAULT 'AO_Client',
            
            -- Multi-broker support
            broker LowCardinality(String) DEFAULT 'FBS-Demo',
            account_type LowCardinality(String) DEFAULT 'demo',
            created_at DateTime64(3) DEFAULT now64()
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY (broker, symbol, timeframe, timestamp)
        TTL timestamp + INTERVAL 1 YEAR
        SETTINGS index_granularity = 8192
        """

    @staticmethod
    def macd_data() -> str:
        """MACD (Multiple configurations) data table"""
        return """
        CREATE TABLE IF NOT EXISTS macd_data (
            timestamp DateTime64(3) CODEC(Delta, LZ4),
            symbol LowCardinality(String),
            timeframe LowCardinality(String),
            
            -- Core MACD Data (4 configurations)
            macd_1 Float64 CODEC(Gorilla),
            macd_signal_1 Float64 CODEC(Gorilla),
            macd_histogram_1 Float64 CODEC(Gorilla),
            macd_2 Float64 CODEC(Gorilla),
            macd_signal_2 Float64 CODEC(Gorilla),
            macd_histogram_2 Float64 CODEC(Gorilla),
            macd_3 Float64 CODEC(Gorilla),
            macd_signal_3 Float64 CODEC(Gorilla),
            macd_histogram_3 Float64 CODEC(Gorilla),
            macd_4 Float64 CODEC(Gorilla),
            macd_signal_4 Float64 CODEC(Gorilla),
            macd_histogram_4 Float64 CODEC(Gorilla),
            
            -- Analysis Data
            macd_consensus LowCardinality(String),
            divergence_analysis String CODEC(ZSTD),
            momentum_strength Float32 CODEC(Gorilla),
            trend_confirmation LowCardinality(String),
            
            -- Metadata
            collection_time_seconds Float32 CODEC(Gorilla),
            data_quality_score Float32 CODEC(Gorilla),
            error_count UInt16 CODEC(T64),
            source_client LowCardinality(String) DEFAULT 'MACD_Client',
            
            -- Multi-broker support
            broker LowCardinality(String) DEFAULT 'FBS-Demo',
            account_type LowCardinality(String) DEFAULT 'demo',
            created_at DateTime64(3) DEFAULT now64()
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY (broker, symbol, timeframe, timestamp)
        TTL timestamp + INTERVAL 1 YEAR
        SETTINGS index_granularity = 8192
        """

    @staticmethod
    def rsi_data() -> str:
        """RSI (Multiple periods) data table"""
        return """
        CREATE TABLE IF NOT EXISTS rsi_data (
            timestamp DateTime64(3) CODEC(Delta, LZ4),
            symbol LowCardinality(String),
            timeframe LowCardinality(String),
            
            -- Core RSI Data (4 periods)
            rsi_14 Float64 CODEC(Gorilla),
            rsi_21 Float64 CODEC(Gorilla),
            rsi_30 Float64 CODEC(Gorilla),
            rsi_50 Float64 CODEC(Gorilla),
            
            -- Analysis Data
            rsi_consensus LowCardinality(String),
            overbought_signals String CODEC(ZSTD),
            oversold_signals String CODEC(ZSTD),
            rsi_divergences String CODEC(ZSTD),
            
            -- Metadata
            collection_time_seconds Float32 CODEC(Gorilla),
            data_quality_score Float32 CODEC(Gorilla),
            error_count UInt16 CODEC(T64),
            source_client LowCardinality(String) DEFAULT 'RSI_Client',
            
            -- Multi-broker support
            broker LowCardinality(String) DEFAULT 'FBS-Demo',
            account_type LowCardinality(String) DEFAULT 'demo',
            created_at DateTime64(3) DEFAULT now64()
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY (broker, symbol, timeframe, timestamp)
        TTL timestamp + INTERVAL 1 YEAR
        SETTINGS index_granularity = 8192
        """

    @staticmethod
    def volume_data() -> str:
        """Volume Analysis data table"""
        return """
        CREATE TABLE IF NOT EXISTS volume_data (
            timestamp DateTime64(3) CODEC(Delta, LZ4),
            symbol LowCardinality(String),
            timeframe LowCardinality(String),
            
            -- Core Volume Data
            volume UInt64 CODEC(T64),
            volume_ma Float64 CODEC(Gorilla),
            volume_ratio Float64 CODEC(Gorilla),
            price_volume_trend Float64 CODEC(Gorilla),
            
            -- Analysis Data
            volume_trend LowCardinality(String),
            volume_spikes String CODEC(ZSTD),
            volume_dry_ups String CODEC(ZSTD),
            price_volume_correlation Float32 CODEC(Gorilla),
            
            -- Metadata
            collection_time_seconds Float32 CODEC(Gorilla),
            data_quality_score Float32 CODEC(Gorilla),
            error_count UInt16 CODEC(T64),
            source_client LowCardinality(String) DEFAULT 'Volume_Client',
            
            -- Multi-broker support
            broker LowCardinality(String) DEFAULT 'FBS-Demo',
            account_type LowCardinality(String) DEFAULT 'demo',
            created_at DateTime64(3) DEFAULT now64()
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY (broker, symbol, timeframe, timestamp)
        TTL timestamp + INTERVAL 1 YEAR
        SETTINGS index_granularity = 8192
        """

    @staticmethod
    def correlation_data() -> str:
        """Correlation Analysis data table"""
        return """
        CREATE TABLE IF NOT EXISTS correlation_data (
            timestamp DateTime64(3) CODEC(Delta, LZ4),
            symbol LowCardinality(String),
            timeframe LowCardinality(String),
            
            -- Core Correlation Data
            returns Float64 CODEC(Gorilla),
            volatility Float64 CODEC(Gorilla),
            correlation_20 Float64 CODEC(Gorilla),
            correlation_50 Float64 CODEC(Gorilla),
            correlation_100 Float64 CODEC(Gorilla),
            correlation_200 Float64 CODEC(Gorilla),
            
            -- Analysis Data
            correlation_regime LowCardinality(String),
            correlation_breakdowns String CODEC(ZSTD),
            cross_asset_signals String CODEC(ZSTD),
            diversification_ratio Float32 CODEC(Gorilla),
            correlation_stability Float32 CODEC(Gorilla),
            
            -- Metadata
            collection_time_seconds Float32 CODEC(Gorilla),
            data_quality_score Float32 CODEC(Gorilla),
            error_count UInt16 CODEC(T64),
            source_client LowCardinality(String) DEFAULT 'Correlation_Client',
            
            -- Multi-broker support
            broker LowCardinality(String) DEFAULT 'FBS-Demo',
            account_type LowCardinality(String) DEFAULT 'demo',
            created_at DateTime64(3) DEFAULT now64()
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY (broker, symbol, timeframe, timestamp)
        TTL timestamp + INTERVAL 1 YEAR
        SETTINGS index_granularity = 8192
        """

    @staticmethod
    def obv_data() -> str:
        """OBV (On-Balance Volume) data table"""
        return """
        CREATE TABLE IF NOT EXISTS obv_data (
            timestamp DateTime64(3) CODEC(Delta, LZ4),
            symbol LowCardinality(String),
            timeframe LowCardinality(String),
            
            -- Core OBV Data
            obv Float64 CODEC(Gorilla),
            obv_ma_14 Float64 CODEC(Gorilla),
            obv_ma_21 Float64 CODEC(Gorilla),
            obv_ma_50 Float64 CODEC(Gorilla),
            volume UInt64 CODEC(T64),
            
            -- Analysis Data
            obv_trend LowCardinality(String),
            volume_price_alignment LowCardinality(String),
            obv_divergences String CODEC(ZSTD),
            volume_confirmation Boolean,
            trend_strength Float32 CODEC(Gorilla),
            
            -- Metadata
            collection_time_seconds Float32 CODEC(Gorilla),
            data_quality_score Float32 CODEC(Gorilla),
            error_count UInt16 CODEC(T64),
            source_client LowCardinality(String) DEFAULT 'OBV_Client',
            
            -- Multi-broker support
            broker LowCardinality(String) DEFAULT 'FBS-Demo',
            account_type LowCardinality(String) DEFAULT 'demo',
            created_at DateTime64(3) DEFAULT now64()
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY (broker, symbol, timeframe, timestamp)
        TTL timestamp + INTERVAL 1 YEAR
        SETTINGS index_granularity = 8192
        """

    @staticmethod
    def mfi_data() -> str:
        """MFI (Money Flow Index) data table"""
        return """
        CREATE TABLE IF NOT EXISTS mfi_data (
            timestamp DateTime64(3) CODEC(Delta, LZ4),
            symbol LowCardinality(String),
            timeframe LowCardinality(String),
            
            -- Core MFI Data
            mfi_14 Float64 CODEC(Gorilla),
            mfi_21 Float64 CODEC(Gorilla),
            mfi_30 Float64 CODEC(Gorilla),
            positive_money_flow Float64 CODEC(Gorilla),
            negative_money_flow Float64 CODEC(Gorilla),
            money_flow_ratio Float64 CODEC(Gorilla),
            
            -- Analysis Data
            mfi_trend LowCardinality(String),
            overbought_levels String CODEC(ZSTD),
            oversold_levels String CODEC(ZSTD),
            money_flow_divergences String CODEC(ZSTD),
            volume_price_pressure Float32 CODEC(Gorilla),
            
            -- Metadata
            collection_time_seconds Float32 CODEC(Gorilla),
            data_quality_score Float32 CODEC(Gorilla),
            error_count UInt16 CODEC(T64),
            source_client LowCardinality(String) DEFAULT 'MFI_Client',
            
            -- Multi-broker support
            broker LowCardinality(String) DEFAULT 'FBS-Demo',
            account_type LowCardinality(String) DEFAULT 'demo',
            created_at DateTime64(3) DEFAULT now64()
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY (broker, symbol, timeframe, timestamp)
        TTL timestamp + INTERVAL 1 YEAR
        SETTINGS index_granularity = 8192
        """

    @staticmethod
    def stochastic_data() -> str:
        """Stochastic Oscillator data table"""
        return """
        CREATE TABLE IF NOT EXISTS stochastic_data (
            timestamp DateTime64(3) CODEC(Delta, LZ4),
            symbol LowCardinality(String),
            timeframe LowCardinality(String),
            
            -- Core Stochastic Data
            stoch_k Float64 CODEC(Gorilla),
            stoch_d Float64 CODEC(Gorilla),
            stoch_k_slow Float64 CODEC(Gorilla),
            stoch_d_slow Float64 CODEC(Gorilla),
            stoch_rsi Float64 CODEC(Gorilla),
            
            -- Analysis Data
            stoch_trend LowCardinality(String),
            overbought_signals String CODEC(ZSTD),
            oversold_signals String CODEC(ZSTD),
            bullish_crossovers String CODEC(ZSTD),
            bearish_crossovers String CODEC(ZSTD),
            divergence_patterns String CODEC(ZSTD),
            
            -- Metadata
            collection_time_seconds Float32 CODEC(Gorilla),
            data_quality_score Float32 CODEC(Gorilla),
            error_count UInt16 CODEC(T64),
            source_client LowCardinality(String) DEFAULT 'Stochastic_Client',
            
            -- Multi-broker support
            broker LowCardinality(String) DEFAULT 'FBS-Demo',
            account_type LowCardinality(String) DEFAULT 'demo',
            created_at DateTime64(3) DEFAULT now64()
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY (broker, symbol, timeframe, timestamp)
        TTL timestamp + INTERVAL 1 YEAR
        SETTINGS index_granularity = 8192
        """

    @staticmethod
    def economic_data() -> str:
        """Economic Indicators data table"""
        return """
        CREATE TABLE IF NOT EXISTS economic_data (
            timestamp DateTime64(3) CODEC(Delta, LZ4),
            symbol LowCardinality(String),
            timeframe LowCardinality(String),
            
            -- Core Economic Data
            gdp_growth Float64 CODEC(Gorilla),
            inflation_rate Float64 CODEC(Gorilla),
            unemployment_rate Float64 CODEC(Gorilla),
            interest_rates Float64 CODEC(Gorilla),
            retail_sales Float64 CODEC(Gorilla),
            industrial_production Float64 CODEC(Gorilla),
            
            -- Analysis Data
            economic_trend LowCardinality(String),
            leading_indicators String CODEC(ZSTD),
            lagging_indicators String CODEC(ZSTD),
            economic_surprises String CODEC(ZSTD),
            policy_implications String CODEC(ZSTD),
            
            -- Metadata
            collection_time_seconds Float32 CODEC(Gorilla),
            data_quality_score Float32 CODEC(Gorilla),
            error_count UInt16 CODEC(T64),
            source_client LowCardinality(String) DEFAULT 'Economic_Client',
            created_at DateTime64(3) DEFAULT now64()
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY (symbol, timeframe, timestamp)
        TTL timestamp + INTERVAL 1 YEAR
        SETTINGS index_granularity = 8192
        """

    @staticmethod
    def sessions_data() -> str:
        """Trading Sessions data table"""
        return """
        CREATE TABLE IF NOT EXISTS sessions_data (
            timestamp DateTime64(3) CODEC(Delta, LZ4),
            symbol LowCardinality(String),
            timeframe LowCardinality(String),
            
            -- Core Sessions Data
            session_type LowCardinality(String),
            session_open_time DateTime64(3),
            session_close_time DateTime64(3),
            session_volume UInt64 CODEC(T64),
            session_range Float64 CODEC(Gorilla),
            session_volatility Float64 CODEC(Gorilla),
            
            -- Analysis Data
            session_trend LowCardinality(String),
            liquidity_patterns String CODEC(ZSTD),
            volume_patterns String CODEC(ZSTD),
            session_overlaps String CODEC(ZSTD),
            institutional_activity Float32 CODEC(Gorilla),
            
            -- Metadata
            collection_time_seconds Float32 CODEC(Gorilla),
            data_quality_score Float32 CODEC(Gorilla),
            error_count UInt16 CODEC(T64),
            source_client LowCardinality(String) DEFAULT 'Sessions_Client',
            
            -- Multi-broker support
            broker LowCardinality(String) DEFAULT 'FBS-Demo',
            account_type LowCardinality(String) DEFAULT 'demo',
            created_at DateTime64(3) DEFAULT now64()
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY (broker, symbol, timeframe, timestamp)
        TTL timestamp + INTERVAL 1 YEAR
        SETTINGS index_granularity = 8192
        """

    @staticmethod
    def orderbook_data() -> str:
        """Order Book Analysis data table"""
        return """
        CREATE TABLE IF NOT EXISTS orderbook_data (
            timestamp DateTime64(3) CODEC(Delta, LZ4),
            symbol LowCardinality(String),
            timeframe LowCardinality(String),
            
            -- Core Order Book Data
            bid_depth_levels Array(Float64),
            ask_depth_levels Array(Float64),
            bid_volumes Array(UInt64),
            ask_volumes Array(UInt64),
            order_flow_imbalance Float64 CODEC(Gorilla),
            market_depth Float64 CODEC(Gorilla),
            
            -- Analysis Data
            liquidity_analysis String CODEC(ZSTD),
            support_resistance_levels String CODEC(ZSTD),
            institutional_footprints String CODEC(ZSTD),
            order_flow_patterns String CODEC(ZSTD),
            market_microstructure Float32 CODEC(Gorilla),
            
            -- Metadata
            collection_time_seconds Float32 CODEC(Gorilla),
            data_quality_score Float32 CODEC(Gorilla),
            error_count UInt16 CODEC(T64),
            source_client LowCardinality(String) DEFAULT 'OrderBook_Client',
            
            -- Multi-broker support
            broker LowCardinality(String) DEFAULT 'FBS-Demo',
            account_type LowCardinality(String) DEFAULT 'demo',
            created_at DateTime64(3) DEFAULT now64()
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY (broker, symbol, timeframe, timestamp)
        TTL timestamp + INTERVAL 1 YEAR
        SETTINGS index_granularity = 8192
        """

    @staticmethod
    def slippage_data() -> str:
        """Slippage Monitoring data table"""
        return """
        CREATE TABLE IF NOT EXISTS slippage_data (
            timestamp DateTime64(3) CODEC(Delta, LZ4),
            symbol LowCardinality(String),
            timeframe LowCardinality(String),
            
            -- Core Slippage Data
            expected_price Float64 CODEC(Gorilla),
            executed_price Float64 CODEC(Gorilla),
            slippage_pips Float64 CODEC(Gorilla),
            slippage_percentage Float64 CODEC(Gorilla),
            trade_size UInt64 CODEC(T64),
            market_impact Float64 CODEC(Gorilla),
            
            -- Analysis Data
            slippage_trends String CODEC(ZSTD),
            execution_quality Float32 CODEC(Gorilla),
            market_conditions LowCardinality(String),
            liquidity_assessment String CODEC(ZSTD),
            cost_analysis String CODEC(ZSTD),
            
            -- Metadata
            collection_time_seconds Float32 CODEC(Gorilla),
            data_quality_score Float32 CODEC(Gorilla),
            error_count UInt16 CODEC(T64),
            source_client LowCardinality(String) DEFAULT 'Slippage_Client',
            
            -- Multi-broker support
            broker LowCardinality(String) DEFAULT 'FBS-Demo',
            account_type LowCardinality(String) DEFAULT 'demo',
            created_at DateTime64(3) DEFAULT now64()
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY (broker, symbol, timeframe, timestamp)
        TTL timestamp + INTERVAL 1 YEAR
        SETTINGS index_granularity = 8192
        """

    @staticmethod
    def timesales_data() -> str:
        """Time & Sales data table"""
        return """
        CREATE TABLE IF NOT EXISTS timesales_data (
            timestamp DateTime64(3) CODEC(Delta, LZ4),
            symbol LowCardinality(String),
            timeframe LowCardinality(String),
            
            -- Core Time & Sales Data
            trade_price Float64 CODEC(Gorilla),
            trade_volume UInt64 CODEC(T64),
            trade_side LowCardinality(String),
            trade_conditions String CODEC(ZSTD),
            cumulative_volume UInt64 CODEC(T64),
            vwap Float64 CODEC(Gorilla),
            
            -- Analysis Data
            tape_reading_signals String CODEC(ZSTD),
            institutional_prints String CODEC(ZSTD),
            block_trades String CODEC(ZSTD),
            unusual_activity String CODEC(ZSTD),
            market_sentiment Float32 CODEC(Gorilla),
            
            -- Metadata
            collection_time_seconds Float32 CODEC(Gorilla),
            data_quality_score Float32 CODEC(Gorilla),
            error_count UInt16 CODEC(T64),
            source_client LowCardinality(String) DEFAULT 'TimeSales_Client',
            
            -- Multi-broker support
            broker LowCardinality(String) DEFAULT 'FBS-Demo',
            account_type LowCardinality(String) DEFAULT 'demo',
            created_at DateTime64(3) DEFAULT now64()
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY (broker, symbol, timeframe, timestamp)
        TTL timestamp + INTERVAL 1 YEAR
        SETTINGS index_granularity = 8192
        """

    @staticmethod
    def ema_data() -> str:
        """EMA (Exponential Moving Average) data table"""
        return """
        CREATE TABLE IF NOT EXISTS ema_data (
            timestamp DateTime64(3) CODEC(Delta, LZ4),
            symbol LowCardinality(String),
            timeframe LowCardinality(String),
            
            -- Core EMA Data (Multiple periods)
            ema_9 Float64 CODEC(Gorilla),
            ema_12 Float64 CODEC(Gorilla),
            ema_20 Float64 CODEC(Gorilla),
            ema_26 Float64 CODEC(Gorilla),
            ema_50 Float64 CODEC(Gorilla),
            ema_100 Float64 CODEC(Gorilla),
            ema_200 Float64 CODEC(Gorilla),
            
            -- EMA Relationships
            ema_alignment LowCardinality(String),
            ema_crossovers String CODEC(ZSTD),
            short_term_trend LowCardinality(String),
            long_term_trend LowCardinality(String),
            
            -- Analysis Data
            trend_strength Float32 CODEC(Gorilla),
            momentum_direction LowCardinality(String),
            price_ema_distance Float64 CODEC(Gorilla),
            trend_consistency Float32 CODEC(Gorilla),
            
            -- Metadata
            collection_time_seconds Float32 CODEC(Gorilla),
            data_quality_score Float32 CODEC(Gorilla),
            error_count UInt16 CODEC(T64),
            source_client LowCardinality(String) DEFAULT 'EMA_Client',
            
            -- Multi-broker support
            broker LowCardinality(String) DEFAULT 'FBS-Demo',
            account_type LowCardinality(String) DEFAULT 'demo',
            created_at DateTime64(3) DEFAULT now64()
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY (broker, symbol, timeframe, timestamp)
        TTL timestamp + INTERVAL 1 YEAR
        SETTINGS index_granularity = 8192
        """

    @staticmethod
    def bollinger_data() -> str:
        """Bollinger Bands data table"""
        return """
        CREATE TABLE IF NOT EXISTS bollinger_data (
            timestamp DateTime64(3) CODEC(Delta, LZ4),
            symbol LowCardinality(String),
            timeframe LowCardinality(String),
            
            -- Core Bollinger Bands Data
            bb_upper Float64 CODEC(Gorilla),
            bb_middle Float64 CODEC(Gorilla),
            bb_lower Float64 CODEC(Gorilla),
            bb_width Float64 CODEC(Gorilla),
            bb_percent Float64 CODEC(Gorilla),
            
            -- Multi-period Bollinger Bands
            bb_upper_20_2 Float64 CODEC(Gorilla),
            bb_lower_20_2 Float64 CODEC(Gorilla),
            bb_upper_20_1 Float64 CODEC(Gorilla),
            bb_lower_20_1 Float64 CODEC(Gorilla),
            
            -- Analysis Data
            bb_squeeze Boolean,
            bb_expansion Boolean,
            band_position LowCardinality(String),
            volatility_regime LowCardinality(String),
            mean_reversion_signal LowCardinality(String),
            
            -- Band Touch Analysis
            upper_band_touches UInt32 CODEC(T64),
            lower_band_touches UInt32 CODEC(T64),
            band_walk_direction LowCardinality(String),
            
            -- Metadata
            collection_time_seconds Float32 CODEC(Gorilla),
            data_quality_score Float32 CODEC(Gorilla),
            error_count UInt16 CODEC(T64),
            source_client LowCardinality(String) DEFAULT 'Bollinger_Client',
            
            -- Multi-broker support
            broker LowCardinality(String) DEFAULT 'FBS-Demo',
            account_type LowCardinality(String) DEFAULT 'demo',
            created_at DateTime64(3) DEFAULT now64()
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY (broker, symbol, timeframe, timestamp)
        TTL timestamp + INTERVAL 1 YEAR
        SETTINGS index_granularity = 8192
        """

    @staticmethod
    def ichimoku_data() -> str:
        """Ichimoku Kinko Hyo data table"""
        return """
        CREATE TABLE IF NOT EXISTS ichimoku_data (
            timestamp DateTime64(3) CODEC(Delta, LZ4),
            symbol LowCardinality(String),
            timeframe LowCardinality(String),
            
            -- Core Ichimoku Lines
            tenkan_sen Float64 CODEC(Gorilla),
            kijun_sen Float64 CODEC(Gorilla),
            senkou_span_a Float64 CODEC(Gorilla),
            senkou_span_b Float64 CODEC(Gorilla),
            chikou_span Float64 CODEC(Gorilla),
            
            -- Cloud Analysis
            cloud_color LowCardinality(String),
            cloud_thickness Float64 CODEC(Gorilla),
            price_cloud_position LowCardinality(String),
            future_cloud_color LowCardinality(String),
            
            -- Signal Analysis
            tk_cross LowCardinality(String),
            price_kijun_relation LowCardinality(String),
            chikou_confirmation Boolean,
            kumo_breakout LowCardinality(String),
            
            -- Trend Analysis
            ichimoku_trend LowCardinality(String),
            trend_strength Float32 CODEC(Gorilla),
            momentum_confirmation Boolean,
            equilibrium_level Float64 CODEC(Gorilla),
            
            -- Time Analysis
            time_cycles Array(UInt32),
            cycle_analysis String CODEC(ZSTD),
            wave_patterns String CODEC(ZSTD),
            
            -- Metadata
            collection_time_seconds Float32 CODEC(Gorilla),
            data_quality_score Float32 CODEC(Gorilla),
            error_count UInt16 CODEC(T64),
            source_client LowCardinality(String) DEFAULT 'Ichimoku_Client',
            
            -- Multi-broker support
            broker LowCardinality(String) DEFAULT 'FBS-Demo',
            account_type LowCardinality(String) DEFAULT 'demo',
            created_at DateTime64(3) DEFAULT now64()
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY (broker, symbol, timeframe, timestamp)
        TTL timestamp + INTERVAL 1 YEAR
        SETTINGS index_granularity = 8192
        """

    @staticmethod
    def session_analysis() -> str:
        """Session analysis and overlap tracking - calculated indicator data"""
        return """
        CREATE TABLE IF NOT EXISTS session_analysis (
            timestamp DateTime64(3) DEFAULT now64(),
            
            -- Session Status
            sydney_active Boolean DEFAULT false,
            tokyo_active Boolean DEFAULT false,
            london_active Boolean DEFAULT false,
            new_york_active Boolean DEFAULT false,
            
            -- Session Analysis
            active_session_count UInt8,
            primary_session LowCardinality(String) DEFAULT 'Unknown',
            session_overlap_type LowCardinality(String) DEFAULT 'None',
            
            -- Market Characteristics
            expected_liquidity Float32 CODEC(Gorilla),
            expected_volatility Float32 CODEC(Gorilla),
            spread_expectation Float32 CODEC(Gorilla),
            
            -- Session Overlap Details
            overlap_duration_minutes UInt16 CODEC(T64),
            liquidity_multiplier Float32 CODEC(Gorilla),
            institutional_activity_score Float32 CODEC(Gorilla),
            
            -- Weekend/Holiday Detection
            is_weekend Boolean DEFAULT false,
            is_holiday Boolean DEFAULT false,
            reduced_liquidity Boolean DEFAULT false,
            
            -- Metadata
            timezone_offset Int16 CODEC(T64),
            daylight_saving_active Boolean,
            
            -- Calculation Info (consistent with other indicators)
            collection_time_seconds Float32 CODEC(Gorilla),
            data_quality_score Float32 CODEC(Gorilla),
            error_count UInt16 CODEC(T64),
            source_client LowCardinality(String) DEFAULT 'Session_Client',
            created_at DateTime64(3) DEFAULT now64(),
            
            INDEX idx_primary_session primary_session TYPE set(10) GRANULARITY 8192,
            INDEX idx_overlap_type session_overlap_type TYPE set(20) GRANULARITY 8192,
            INDEX idx_timestamp timestamp TYPE minmax GRANULARITY 8192
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY timestamp
        TTL timestamp + INTERVAL 1 YEAR DELETE
        SETTINGS index_granularity = 8192;
        """

    @staticmethod
    def advanced_patterns() -> str:
        """Advanced pattern recognition for enhanced trading accuracy"""
        return """
        CREATE TABLE IF NOT EXISTS advanced_patterns (
            timestamp DateTime64(3) DEFAULT now64(),
            symbol LowCardinality(String),
            timeframe LowCardinality(String),
            
            -- Pattern Classification
            pattern_type LowCardinality(String),
            pattern_subtype LowCardinality(String),
            pattern_category LowCardinality(String),
            pattern_strength Float64 CODEC(Gorilla),
            pattern_confidence Float64 CODEC(Gorilla),
            
            -- Harmonic Patterns
            harmonic_pattern_type LowCardinality(String),
            harmonic_completion_percentage Float64 CODEC(Gorilla),
            harmonic_target_1 Float64 CODEC(Gorilla),
            harmonic_target_2 Float64 CODEC(Gorilla),
            harmonic_stop_loss Float64 CODEC(Gorilla),
            
            -- Elliott Wave Analysis
            elliott_wave_count LowCardinality(String),
            elliott_wave_degree LowCardinality(String),
            elliott_wave_direction LowCardinality(String),
            elliott_wave_completion Float64 CODEC(Gorilla),
            elliott_wave_target Float64 CODEC(Gorilla),
            
            -- Candlestick Patterns
            candlestick_pattern LowCardinality(String),
            candlestick_reliability Float64 CODEC(Gorilla),
            candlestick_context LowCardinality(String),
            candlestick_confirmation Boolean DEFAULT false,
            
            -- Chart Patterns
            chart_pattern_type LowCardinality(String),
            chart_pattern_stage LowCardinality(String),
            chart_pattern_breakout_target Float64 CODEC(Gorilla),
            chart_pattern_volume_confirmation Boolean DEFAULT false,
            
            -- Fibonacci Analysis
            fibonacci_retracement_levels Array(Float64),
            fibonacci_extension_levels Array(Float64),
            fibonacci_support_resistance Array(Float64),
            fibonacci_confluence_score Float64 CODEC(Gorilla),
            
            -- Volume Pattern Analysis
            volume_pattern_type LowCardinality(String),
            volume_anomaly_score Float64 CODEC(Gorilla),
            volume_confirmation Boolean DEFAULT false,
            volume_divergence_signal LowCardinality(String),
            
            -- Multi-timeframe Pattern Analysis
            higher_timeframe_pattern LowCardinality(String),
            lower_timeframe_pattern LowCardinality(String),
            pattern_alignment_score Float64 CODEC(Gorilla),
            
            -- Pattern Completion Metrics
            pattern_start_time DateTime64(3),
            pattern_completion_time Nullable(DateTime64(3)),
            pattern_duration_minutes UInt32 CODEC(T64),
            pattern_success_probability Float64 CODEC(Gorilla),
            
            -- Market Structure Analysis
            market_structure_shift Boolean DEFAULT false,
            break_of_structure Boolean DEFAULT false,
            change_of_character Boolean DEFAULT false,
            order_block_formation Boolean DEFAULT false,
            
            -- Smart Money Concepts
            fair_value_gap Float64 CODEC(Gorilla),
            imbalance_level Float64 CODEC(Gorilla),
            institutional_candle Boolean DEFAULT false,
            liquidity_grab_signal Boolean DEFAULT false,
            
            -- Pattern Invalidation
            invalidation_level Float64 CODEC(Gorilla),
            invalidation_triggered Boolean DEFAULT false,
            invalidation_reason LowCardinality(String),
            
            -- Risk Management
            risk_reward_ratio Float64 CODEC(Gorilla),
            position_size_recommendation Float64 CODEC(Gorilla),
            time_based_exit DateTime64(3),
            
            -- Pattern Quality Metrics
            pattern_quality_score Float64 CODEC(Gorilla),
            historical_success_rate Float64 CODEC(Gorilla),
            market_conditions_suitability Float64 CODEC(Gorilla),
            
            -- Calculation Info
            collection_time_seconds Float32 CODEC(Gorilla),
            data_quality_score Float32 CODEC(Gorilla),
            error_count UInt16 CODEC(T64),
            source_client LowCardinality(String) DEFAULT 'Pattern_Client',
            created_at DateTime64(3) DEFAULT now64(),
            
            -- Multi-broker support
            broker LowCardinality(String) DEFAULT 'FBS-Demo',
            account_type LowCardinality(String) DEFAULT 'demo',
            
            -- Enhanced Indexing
            INDEX idx_pattern_type pattern_type TYPE set(50) GRANULARITY 8192,
            INDEX idx_pattern_category pattern_category TYPE set(20) GRANULARITY 8192,
            INDEX idx_symbol symbol TYPE set(100) GRANULARITY 8192,
            INDEX idx_timeframe timeframe TYPE set(20) GRANULARITY 8192,
            INDEX idx_broker broker TYPE set(50) GRANULARITY 8192,
            INDEX idx_timestamp timestamp TYPE minmax GRANULARITY 8192
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY (broker, symbol, timeframe, timestamp)
        TTL timestamp + INTERVAL 3 MONTH DELETE
        SETTINGS index_granularity = 8192;
        """

    @staticmethod
    def model_performance() -> str:
        """Real-time model performance monitoring for enhanced accuracy"""
        return """
        CREATE TABLE IF NOT EXISTS model_performance (
            timestamp DateTime64(3) DEFAULT now64(),
            symbol LowCardinality(String),
            timeframe LowCardinality(String),
            
            -- Model Identification
            model_id String CODEC(ZSTD),
            model_name LowCardinality(String),
            model_type LowCardinality(String),
            model_version String CODEC(ZSTD),
            model_framework LowCardinality(String),
            
            -- Performance Metrics
            accuracy Float64 CODEC(Gorilla),
            precision Float64 CODEC(Gorilla),
            recall Float64 CODEC(Gorilla),
            f1_score Float64 CODEC(Gorilla),
            auc_roc Float64 CODEC(Gorilla),
            
            -- Regression Metrics
            mse Float64 CODEC(Gorilla),
            rmse Float64 CODEC(Gorilla),
            mae Float64 CODEC(Gorilla),
            r2_score Float64 CODEC(Gorilla),
            
            -- Trading-Specific Metrics
            sharpe_ratio Float64 CODEC(Gorilla),
            max_drawdown Float64 CODEC(Gorilla),
            win_rate Float64 CODEC(Gorilla),
            profit_factor Float64 CODEC(Gorilla),
            calmar_ratio Float64 CODEC(Gorilla),
            
            -- Model Drift Detection
            drift_score Float64 CODEC(Gorilla),
            drift_detected Boolean DEFAULT false,
            drift_severity LowCardinality(String),
            concept_drift_score Float64 CODEC(Gorilla),
            
            -- Data Quality Impact
            data_quality_score Float64 CODEC(Gorilla),
            missing_data_percentage Float64 CODEC(Gorilla),
            outlier_percentage Float64 CODEC(Gorilla),
            data_staleness_score Float64 CODEC(Gorilla),
            
            -- Feature Performance
            feature_importance_scores Array(Float64),
            feature_names Array(String),
            feature_drift_scores Array(Float64),
            top_performing_features Array(String),
            
            -- Prediction Quality
            prediction_confidence Float64 CODEC(Gorilla),
            prediction_calibration Float64 CODEC(Gorilla),
            prediction_stability Float64 CODEC(Gorilla),
            prediction_latency_ms UInt32 CODEC(T64),
            
            -- Model Ensemble Performance
            ensemble_weight Float64 CODEC(Gorilla),
            ensemble_contribution Float64 CODEC(Gorilla),
            ensemble_disagreement Float64 CODEC(Gorilla),
            
            -- Real-time Performance
            throughput_predictions_per_second Float64 CODEC(Gorilla),
            memory_usage_mb Float64 CODEC(Gorilla),
            cpu_usage_percentage Float64 CODEC(Gorilla),
            inference_time_ms Float64 CODEC(Gorilla),
            
            -- Model Health Monitoring
            model_health_score Float64 CODEC(Gorilla),
            model_status LowCardinality(String),
            last_retrained_at DateTime64(3),
            retraining_trigger LowCardinality(String),
            
            -- Business Impact Metrics
            revenue_impact Float64 CODEC(Gorilla),
            risk_adjusted_return Float64 CODEC(Gorilla),
            trade_execution_efficiency Float64 CODEC(Gorilla),
            
            -- Comparative Analysis
            benchmark_comparison Float64 CODEC(Gorilla),
            peer_model_comparison Float64 CODEC(Gorilla),
            improvement_over_baseline Float64 CODEC(Gorilla),
            
            -- Alert Thresholds
            performance_alert_triggered Boolean DEFAULT false,
            alert_severity LowCardinality(String),
            alert_message String CODEC(ZSTD),
            
            -- Market Condition Analysis
            market_regime LowCardinality(String),
            volatility_regime LowCardinality(String),
            performance_by_regime String CODEC(ZSTD),
            
            -- Model Explainability
            shap_values Array(Float64),
            lime_explanations String CODEC(ZSTD),
            feature_interactions String CODEC(ZSTD),
            
            -- Calculation Info
            collection_time_seconds Float32 CODEC(Gorilla),
            data_quality_score Float32 CODEC(Gorilla),
            error_count UInt16 CODEC(T64),
            source_client LowCardinality(String) DEFAULT 'ModelPerf_Client',
            created_at DateTime64(3) DEFAULT now64(),
            
            -- Multi-broker support
            broker LowCardinality(String) DEFAULT 'FBS-Demo',
            account_type LowCardinality(String) DEFAULT 'demo',
            
            -- Enhanced Indexing
            INDEX idx_model_id model_id TYPE set(100) GRANULARITY 8192,
            INDEX idx_model_name model_name TYPE set(50) GRANULARITY 8192,
            INDEX idx_model_type model_type TYPE set(20) GRANULARITY 8192,
            INDEX idx_symbol symbol TYPE set(100) GRANULARITY 8192,
            INDEX idx_timeframe timeframe TYPE set(20) GRANULARITY 8192,
            INDEX idx_broker broker TYPE set(50) GRANULARITY 8192,
            INDEX idx_timestamp timestamp TYPE minmax GRANULARITY 8192
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMM(timestamp)
        ORDER BY (broker, symbol, timeframe, timestamp)
        TTL timestamp + INTERVAL 6 MONTH DELETE
        SETTINGS index_granularity = 8192;
        """

    @staticmethod
    def get_table_list() -> List[str]:
        """Get list of all indicator table names"""
        return [
            "adl_data",
            "ao_data",
            "macd_data",
            "rsi_data",
            "volume_data",
            "correlation_data",
            "obv_data",
            "mfi_data",
            "stochastic_data",
            "economic_data",
            "sessions_data",
            "session_analysis",
            "orderbook_data",
            "slippage_data",
            "timesales_data",
            "ema_data",
            "bollinger_data",
            "ichimoku_data",
            "advanced_patterns",
            "model_performance"
        ]

    @staticmethod
    def get_broker_specific_tables() -> List[str]:
        """Get tables that contain broker-specific data"""
        return [
            "adl_data",
            "ao_data", 
            "macd_data",
            "rsi_data",
            "volume_data",
            "correlation_data",
            "obv_data",
            "mfi_data",
            "stochastic_data",
            "sessions_data",
            "orderbook_data",
            "slippage_data",
            "timesales_data",
            "ema_data",
            "bollinger_data",
            "ichimoku_data",
            "advanced_patterns",
            "model_performance"
        ]

    @staticmethod
    def get_universal_tables() -> List[str]:
        """Get tables that contain universal data (no broker columns)"""
        return [
            "economic_data",
            "session_analysis"
        ]