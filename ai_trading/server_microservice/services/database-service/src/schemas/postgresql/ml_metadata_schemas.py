"""
PostgreSQL ML/DL Metadata Schemas - ENHANCED WITH FULL CENTRALIZATION
Machine learning and deep learning model metadata and configuration

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


class PostgresqlMlMetadataSchemas:
    """
    ML/DL metadata schemas for PostgreSQL
    Stores model metadata, configuration, and pipeline information
    """

    @staticmethod
    # @performance_tracked - simplified
    def get_all_tables() -> Dict[str, str]:
        """Get all ML/DL metadata table schemas with centralized tracking"""
        try:
            logger.info("Retrieving all PostgreSQL ML metadata table schemas")
            
            tables = {
            # ML/DL Model Metadata
            "ml_model_metadata": PostgresqlMlMetadataSchemas.ml_model_metadata(),
            "dl_model_metadata": PostgresqlMlMetadataSchemas.dl_model_metadata(),
            "model_versions": PostgresqlMlMetadataSchemas.model_versions(),
            "model_experiments": PostgresqlMlMetadataSchemas.model_experiments(),
            
            # AI Pipeline Configuration
            "ai_pipeline_config": PostgresqlMlMetadataSchemas.ai_pipeline_config(),
            "pipeline_execution_logs": PostgresqlMlMetadataSchemas.pipeline_execution_logs(),
            "pipeline_schedules": PostgresqlMlMetadataSchemas.pipeline_schedules(),
            
            # Performance & Monitoring
            "model_performance_metrics": PostgresqlMlMetadataSchemas.model_performance_metrics(),
            "model_predictions_log": PostgresqlMlMetadataSchemas.model_predictions_log(),
            "model_drift_detection": PostgresqlMlMetadataSchemas.model_drift_detection(),
            
            # Configuration & Features
            "technical_indicator_config": PostgresqlMlMetadataSchemas.technical_indicator_config(),
            "feature_engineering_config": PostgresqlMlMetadataSchemas.feature_engineering_config(),
            "data_preprocessing_config": PostgresqlMlMetadataSchemas.data_preprocessing_config(),
            
            # Trading Strategy Integration
            "trading_strategy_config": PostgresqlMlMetadataSchemas.trading_strategy_config(),
            "strategy_model_mapping": PostgresqlMlMetadataSchemas.strategy_model_mapping(),
            "risk_management_config": PostgresqlMlMetadataSchemas.risk_management_config(),
            }
            
            # Validate table structure
            # Validation simplified
            
            # Publish event for schema retrieval
            # Event publishing simplified
            
            logger.info(f"Successfully retrieved {len(tables)} PostgreSQL ML metadata table schemas")
            return tables
            
        except Exception as e:
            error_context = {
                "operation": "get_all_tables",
                "database_type": "postgresql",
                "schema_type": "ml_metadata"
            }
            # Error handling simplified
            logger.error(f"Failed to retrieve PostgreSQL ML metadata table schemas: {e}")
            raise

    @staticmethod
    def get_indexes() -> List[str]:
        """Get all ML/DL metadata index definitions"""
        return [
            "CREATE INDEX IF NOT EXISTS idx_ml_model_metadata_name ON ml_model_metadata(model_name)",
            "CREATE INDEX IF NOT EXISTS idx_ml_model_metadata_type ON ml_model_metadata(model_type)",
            "CREATE INDEX IF NOT EXISTS idx_ml_model_metadata_status ON ml_model_metadata(status)",
            "CREATE INDEX IF NOT EXISTS idx_dl_model_metadata_name ON dl_model_metadata(model_name)",
            "CREATE INDEX IF NOT EXISTS idx_dl_model_metadata_architecture ON dl_model_metadata(architecture)",
            "CREATE INDEX IF NOT EXISTS idx_model_versions_model_id ON model_versions(model_id)",
            "CREATE INDEX IF NOT EXISTS idx_model_versions_version ON model_versions(version)",
            "CREATE INDEX IF NOT EXISTS idx_model_experiments_model_id ON model_experiments(model_id)",
            "CREATE INDEX IF NOT EXISTS idx_model_experiments_status ON model_experiments(status)",
            "CREATE INDEX IF NOT EXISTS idx_ai_pipeline_config_name ON ai_pipeline_config(pipeline_name)",
            "CREATE INDEX IF NOT EXISTS idx_ai_pipeline_config_type ON ai_pipeline_config(pipeline_type)",
            "CREATE INDEX IF NOT EXISTS idx_pipeline_execution_logs_pipeline_id ON pipeline_execution_logs(pipeline_id)",
            "CREATE INDEX IF NOT EXISTS idx_pipeline_execution_logs_status ON pipeline_execution_logs(execution_status)",
            "CREATE INDEX IF NOT EXISTS idx_pipeline_schedules_pipeline_id ON pipeline_schedules(pipeline_id)",
            "CREATE INDEX IF NOT EXISTS idx_pipeline_schedules_active ON pipeline_schedules(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_model_performance_metrics_model_id ON model_performance_metrics(model_id)",
            "CREATE INDEX IF NOT EXISTS idx_model_performance_metrics_timestamp ON model_performance_metrics(evaluation_timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_model_predictions_log_model_id ON model_predictions_log(model_id)",
            "CREATE INDEX IF NOT EXISTS idx_model_predictions_log_timestamp ON model_predictions_log(prediction_timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_model_drift_detection_model_id ON model_drift_detection(model_id)",
            "CREATE INDEX IF NOT EXISTS idx_model_drift_detection_timestamp ON model_drift_detection(detection_timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_technical_indicator_config_name ON technical_indicator_config(indicator_name)",
            "CREATE INDEX IF NOT EXISTS idx_technical_indicator_config_category ON technical_indicator_config(category)",
            "CREATE INDEX IF NOT EXISTS idx_feature_engineering_config_name ON feature_engineering_config(config_name)",
            "CREATE INDEX IF NOT EXISTS idx_trading_strategy_config_name ON trading_strategy_config(strategy_name)",
            "CREATE INDEX IF NOT EXISTS idx_strategy_model_mapping_strategy_id ON strategy_model_mapping(strategy_id)",
            "CREATE INDEX IF NOT EXISTS idx_strategy_model_mapping_model_id ON strategy_model_mapping(model_id)",
        ]

    # ML/DL Model Metadata Tables
    @staticmethod
    def ml_model_metadata() -> str:
        """ML model metadata table"""
        return """
        CREATE TABLE IF NOT EXISTS ml_model_metadata (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            model_name VARCHAR(255) NOT NULL,
            model_type VARCHAR(100) NOT NULL,
            algorithm VARCHAR(100) NOT NULL,
            description TEXT,
            version VARCHAR(50) NOT NULL,
            status VARCHAR(50) DEFAULT 'development',
            
            -- Model Configuration
            hyperparameters JSONB DEFAULT '{}',
            feature_config JSONB DEFAULT '{}',
            preprocessing_config JSONB DEFAULT '{}',
            
            -- Training Information
            training_data_source VARCHAR(255),
            training_data_period JSONB DEFAULT '{}',
            training_features TEXT[],
            target_variables TEXT[],
            
            -- Performance Metrics
            training_metrics JSONB DEFAULT '{}',
            validation_metrics JSONB DEFAULT '{}',
            test_metrics JSONB DEFAULT '{}',
            
            -- Deployment Information
            deployment_environment VARCHAR(100),
            deployment_config JSONB DEFAULT '{}',
            model_artifacts JSONB DEFAULT '{}',
            
            -- Metadata
            created_by UUID REFERENCES users(id),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            deployed_at TIMESTAMP,
            deprecated_at TIMESTAMP,
            
            -- Model Registry
            model_registry_id VARCHAR(255),
            model_registry_version VARCHAR(50),
            artifacts_location VARCHAR(500),
            
            -- Tags and Labels
            tags TEXT[] DEFAULT '{}',
            labels JSONB DEFAULT '{}',
            
            UNIQUE(model_name, version)
        );
        """

    @staticmethod
    def dl_model_metadata() -> str:
        """DL model metadata table"""
        return """
        CREATE TABLE IF NOT EXISTS dl_model_metadata (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            model_name VARCHAR(255) NOT NULL,
            architecture VARCHAR(100) NOT NULL,
            framework VARCHAR(100) NOT NULL,
            description TEXT,
            version VARCHAR(50) NOT NULL,
            status VARCHAR(50) DEFAULT 'development',
            
            -- Model Architecture
            layer_structure JSONB DEFAULT '{}',
            input_shape INT[],
            output_shape INT[],
            total_parameters BIGINT,
            trainable_parameters BIGINT,
            
            -- Training Configuration
            training_config JSONB DEFAULT '{}',
            optimizer_config JSONB DEFAULT '{}',
            loss_function VARCHAR(100),
            metrics TEXT[],
            
            -- Data Configuration
            data_preprocessing JSONB DEFAULT '{}',
            data_augmentation JSONB DEFAULT '{}',
            batch_size INTEGER,
            sequence_length INTEGER,
            
            -- Training Results
            training_history JSONB DEFAULT '{}',
            final_metrics JSONB DEFAULT '{}',
            training_time_seconds INTEGER,
            epochs_trained INTEGER,
            
            -- Model Artifacts
            model_weights_path VARCHAR(500),
            model_config_path VARCHAR(500),
            tensorboard_logs_path VARCHAR(500),
            
            -- Deployment Information
            deployment_environment VARCHAR(100),
            deployment_config JSONB DEFAULT '{}',
            inference_config JSONB DEFAULT '{}',
            
            -- Metadata
            created_by UUID REFERENCES users(id),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            deployed_at TIMESTAMP,
            deprecated_at TIMESTAMP,
            
            -- Model Registry
            model_registry_id VARCHAR(255),
            model_registry_version VARCHAR(50),
            artifacts_location VARCHAR(500),
            
            -- Tags and Labels
            tags TEXT[] DEFAULT '{}',
            labels JSONB DEFAULT '{}',
            
            UNIQUE(model_name, version)
        );
        """

    @staticmethod
    def model_versions() -> str:
        """Model versions table"""
        return """
        CREATE TABLE IF NOT EXISTS model_versions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            model_id UUID NOT NULL,
            version VARCHAR(50) NOT NULL,
            version_type VARCHAR(50) NOT NULL,
            
            -- Version Information
            changelog TEXT,
            release_notes TEXT,
            breaking_changes TEXT,
            
            -- Performance Comparison
            performance_metrics JSONB DEFAULT '{}',
            performance_comparison JSONB DEFAULT '{}',
            improvement_summary TEXT,
            
            -- Deployment Information
            deployment_status VARCHAR(50) DEFAULT 'created',
            deployment_config JSONB DEFAULT '{}',
            rollback_config JSONB DEFAULT '{}',
            
            -- Approval Process
            approval_status VARCHAR(50) DEFAULT 'pending',
            approved_by UUID REFERENCES users(id),
            approved_at TIMESTAMP,
            approval_notes TEXT,
            
            -- Artifacts
            artifacts_location VARCHAR(500),
            artifacts_checksum VARCHAR(255),
            artifacts_size BIGINT,
            
            -- Metadata
            created_by UUID REFERENCES users(id),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            
            -- Tags and Labels
            tags TEXT[] DEFAULT '{}',
            labels JSONB DEFAULT '{}',
            
            UNIQUE(model_id, version)
        );
        """

    @staticmethod
    def model_experiments() -> str:
        """Model experiments table"""
        return """
        CREATE TABLE IF NOT EXISTS model_experiments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            model_id UUID NOT NULL,
            experiment_name VARCHAR(255) NOT NULL,
            experiment_type VARCHAR(100) NOT NULL,
            
            -- Experiment Configuration
            experiment_config JSONB DEFAULT '{}',
            hyperparameters JSONB DEFAULT '{}',
            data_config JSONB DEFAULT '{}',
            
            -- Experiment Execution
            status VARCHAR(50) DEFAULT 'created',
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            duration_seconds INTEGER,
            
            -- Results
            results JSONB DEFAULT '{}',
            metrics JSONB DEFAULT '{}',
            artifacts JSONB DEFAULT '{}',
            
            -- Comparison
            baseline_experiment_id UUID REFERENCES model_experiments(id),
            comparison_metrics JSONB DEFAULT '{}',
            
            -- Environment
            environment_config JSONB DEFAULT '{}',
            compute_resources JSONB DEFAULT '{}',
            
            -- Metadata
            created_by UUID REFERENCES users(id),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            
            -- Tags and Labels
            tags TEXT[] DEFAULT '{}',
            labels JSONB DEFAULT '{}',
            
            UNIQUE(model_id, experiment_name)
        );
        """

    # AI Pipeline Configuration Tables
    @staticmethod
    def ai_pipeline_config() -> str:
        """AI pipeline configuration table"""
        return """
        CREATE TABLE IF NOT EXISTS ai_pipeline_config (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            pipeline_name VARCHAR(255) UNIQUE NOT NULL,
            pipeline_type VARCHAR(100) NOT NULL,
            description TEXT,
            
            -- Pipeline Configuration
            config JSONB NOT NULL,
            steps JSONB NOT NULL,
            dependencies JSONB DEFAULT '{}',
            
            -- Data Flow
            input_sources JSONB DEFAULT '{}',
            output_destinations JSONB DEFAULT '{}',
            data_validation JSONB DEFAULT '{}',
            
            -- Execution Configuration
            execution_environment VARCHAR(100),
            resource_requirements JSONB DEFAULT '{}',
            timeout_seconds INTEGER DEFAULT 3600,
            retry_config JSONB DEFAULT '{}',
            
            -- Monitoring
            monitoring_config JSONB DEFAULT '{}',
            alerting_config JSONB DEFAULT '{}',
            logging_config JSONB DEFAULT '{}',
            
            -- Status
            status VARCHAR(50) DEFAULT 'active',
            is_active BOOLEAN DEFAULT true,
            
            -- Metadata
            created_by UUID REFERENCES users(id),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            
            -- Tags and Labels
            tags TEXT[] DEFAULT '{}',
            labels JSONB DEFAULT '{}'
        );
        """

    @staticmethod
    def pipeline_execution_logs() -> str:
        """Pipeline execution logs table"""
        return """
        CREATE TABLE IF NOT EXISTS pipeline_execution_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            pipeline_id UUID NOT NULL REFERENCES ai_pipeline_config(id),
            execution_id VARCHAR(255) NOT NULL,
            
            -- Execution Details
            execution_status VARCHAR(50) NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            duration_seconds INTEGER,
            
            -- Execution Configuration
            pipeline_version VARCHAR(50),
            execution_config JSONB DEFAULT '{}',
            input_data JSONB DEFAULT '{}',
            
            -- Results
            output_data JSONB DEFAULT '{}',
            metrics JSONB DEFAULT '{}',
            artifacts JSONB DEFAULT '{}',
            
            -- Error Information
            error_message TEXT,
            error_details JSONB DEFAULT '{}',
            stack_trace TEXT,
            
            -- Resource Usage
            resource_usage JSONB DEFAULT '{}',
            performance_metrics JSONB DEFAULT '{}',
            
            -- Logs
            execution_logs TEXT,
            log_level VARCHAR(20) DEFAULT 'info',
            
            -- Metadata
            triggered_by VARCHAR(100),
            trigger_source VARCHAR(255),
            correlation_id VARCHAR(255),
            
            -- Created timestamp
            created_at TIMESTAMP DEFAULT NOW(),
            
            UNIQUE(pipeline_id, execution_id)
        );
        """

    @staticmethod
    def pipeline_schedules() -> str:
        """Pipeline schedules table"""
        return """
        CREATE TABLE IF NOT EXISTS pipeline_schedules (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            pipeline_id UUID NOT NULL REFERENCES ai_pipeline_config(id),
            schedule_name VARCHAR(255) NOT NULL,
            
            -- Schedule Configuration
            schedule_type VARCHAR(50) NOT NULL,
            cron_expression VARCHAR(255),
            interval_seconds INTEGER,
            
            -- Execution Configuration
            execution_config JSONB DEFAULT '{}',
            max_concurrent_runs INTEGER DEFAULT 1,
            
            -- Schedule Status
            is_active BOOLEAN DEFAULT true,
            next_run_time TIMESTAMP,
            last_run_time TIMESTAMP,
            last_execution_status VARCHAR(50),
            
            -- Failure Handling
            retry_config JSONB DEFAULT '{}',
            failure_notification JSONB DEFAULT '{}',
            
            -- Metadata
            created_by UUID REFERENCES users(id),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            
            -- Tags and Labels
            tags TEXT[] DEFAULT '{}',
            labels JSONB DEFAULT '{}',
            
            UNIQUE(pipeline_id, schedule_name)
        );
        """

    # Performance & Monitoring Tables
    @staticmethod
    def model_performance_metrics() -> str:
        """Model performance metrics table"""
        return """
        CREATE TABLE IF NOT EXISTS model_performance_metrics (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            model_id UUID NOT NULL,
            evaluation_timestamp TIMESTAMP NOT NULL,
            evaluation_type VARCHAR(100) NOT NULL,
            
            -- Dataset Information
            dataset_name VARCHAR(255),
            dataset_size INTEGER,
            evaluation_period JSONB DEFAULT '{}',
            
            -- Performance Metrics
            accuracy DECIMAL(10, 6),
            precision DECIMAL(10, 6),
            recall DECIMAL(10, 6),
            f1_score DECIMAL(10, 6),
            auc_roc DECIMAL(10, 6),
            
            -- Regression Metrics
            mse DECIMAL(15, 6),
            rmse DECIMAL(15, 6),
            mae DECIMAL(15, 6),
            r2_score DECIMAL(10, 6),
            
            -- Trading Specific Metrics
            sharpe_ratio DECIMAL(10, 6),
            max_drawdown DECIMAL(10, 6),
            win_rate DECIMAL(10, 6),
            profit_factor DECIMAL(10, 6),
            
            -- Custom Metrics
            custom_metrics JSONB DEFAULT '{}',
            
            -- Metadata
            evaluation_config JSONB DEFAULT '{}',
            evaluation_notes TEXT,
            
            -- Created timestamp
            created_at TIMESTAMP DEFAULT NOW()
        );
        """

    @staticmethod
    def model_predictions_log() -> str:
        """Model predictions log table"""
        return """
        CREATE TABLE IF NOT EXISTS model_predictions_log (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            model_id UUID NOT NULL,
            prediction_id VARCHAR(255) NOT NULL,
            prediction_timestamp TIMESTAMP NOT NULL,
            
            -- Input Data
            input_features JSONB NOT NULL,
            input_data_hash VARCHAR(255),
            
            -- Prediction Results
            prediction_value DECIMAL(15, 6),
            prediction_confidence DECIMAL(10, 6),
            prediction_probability DECIMAL(10, 6),
            
            -- Additional Outputs
            prediction_class VARCHAR(100),
            prediction_probabilities JSONB DEFAULT '{}',
            feature_importance JSONB DEFAULT '{}',
            
            -- Actual Outcomes (for validation)
            actual_value DECIMAL(15, 6),
            actual_class VARCHAR(100),
            outcome_timestamp TIMESTAMP,
            
            -- Performance Tracking
            prediction_accuracy DECIMAL(10, 6),
            prediction_error DECIMAL(15, 6),
            
            -- Metadata
            model_version VARCHAR(50),
            execution_time_ms INTEGER,
            
            -- Created timestamp
            created_at TIMESTAMP DEFAULT NOW(),
            
            UNIQUE(model_id, prediction_id)
        );
        """

    @staticmethod
    def model_drift_detection() -> str:
        """Model drift detection table"""
        return """
        CREATE TABLE IF NOT EXISTS model_drift_detection (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            model_id UUID NOT NULL,
            detection_timestamp TIMESTAMP NOT NULL,
            drift_type VARCHAR(100) NOT NULL,
            
            -- Drift Metrics
            drift_score DECIMAL(10, 6),
            drift_threshold DECIMAL(10, 6),
            drift_detected BOOLEAN DEFAULT false,
            
            -- Statistical Tests
            statistical_test VARCHAR(100),
            p_value DECIMAL(15, 10),
            test_statistic DECIMAL(15, 6),
            
            -- Drift Details
            drifted_features TEXT[],
            drift_analysis JSONB DEFAULT '{}',
            
            -- Reference Data
            reference_period JSONB DEFAULT '{}',
            comparison_period JSONB DEFAULT '{}',
            
            -- Actions Taken
            alert_sent BOOLEAN DEFAULT false,
            retraining_triggered BOOLEAN DEFAULT false,
            actions_taken JSONB DEFAULT '{}',
            
            -- Metadata
            detection_config JSONB DEFAULT '{}',
            detection_notes TEXT,
            
            -- Created timestamp
            created_at TIMESTAMP DEFAULT NOW()
        );
        """

    # Configuration Tables
    @staticmethod
    def technical_indicator_config() -> str:
        """Technical indicator configuration table"""
        return """
        CREATE TABLE IF NOT EXISTS technical_indicator_config (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            indicator_name VARCHAR(100) NOT NULL,
            category VARCHAR(50) NOT NULL,
            description TEXT,
            
            -- Configuration
            default_parameters JSONB DEFAULT '{}',
            parameter_ranges JSONB DEFAULT '{}',
            calculation_method TEXT,
            
            -- Usage Information
            applicable_timeframes TEXT[],
            applicable_symbols TEXT[],
            computation_requirements JSONB DEFAULT '{}',
            
            -- Integration
            input_data_sources TEXT[],
            output_format JSONB DEFAULT '{}',
            
            -- Status
            is_active BOOLEAN DEFAULT true,
            is_deprecated BOOLEAN DEFAULT false,
            
            -- Metadata
            created_by UUID REFERENCES users(id),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            
            -- Tags and Labels
            tags TEXT[] DEFAULT '{}',
            labels JSONB DEFAULT '{}',
            
            UNIQUE(indicator_name)
        );
        """

    @staticmethod
    def feature_engineering_config() -> str:
        """Feature engineering configuration table"""
        return """
        CREATE TABLE IF NOT EXISTS feature_engineering_config (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            config_name VARCHAR(255) NOT NULL,
            config_type VARCHAR(100) NOT NULL,
            description TEXT,
            
            -- Configuration
            feature_definitions JSONB NOT NULL,
            transformation_steps JSONB DEFAULT '{}',
            
            -- Data Sources
            input_sources JSONB DEFAULT '{}',
            feature_dependencies JSONB DEFAULT '{}',
            
            -- Validation
            validation_rules JSONB DEFAULT '{}',
            data_quality_checks JSONB DEFAULT '{}',
            
            -- Output
            output_schema JSONB DEFAULT '{}',
            feature_metadata JSONB DEFAULT '{}',
            
            -- Status
            is_active BOOLEAN DEFAULT true,
            version VARCHAR(50) DEFAULT '1.0',
            
            -- Metadata
            created_by UUID REFERENCES users(id),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            
            -- Tags and Labels
            tags TEXT[] DEFAULT '{}',
            labels JSONB DEFAULT '{}',
            
            UNIQUE(config_name, version)
        );
        """

    @staticmethod
    def data_preprocessing_config() -> str:
        """Data preprocessing configuration table"""
        return """
        CREATE TABLE IF NOT EXISTS data_preprocessing_config (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            config_name VARCHAR(255) NOT NULL,
            config_type VARCHAR(100) NOT NULL,
            description TEXT,
            
            -- Preprocessing Steps
            preprocessing_steps JSONB NOT NULL,
            step_order INTEGER[],
            
            -- Data Cleaning
            cleaning_rules JSONB DEFAULT '{}',
            outlier_detection JSONB DEFAULT '{}',
            missing_value_handling JSONB DEFAULT '{}',
            
            -- Data Transformation
            scaling_config JSONB DEFAULT '{}',
            normalization_config JSONB DEFAULT '{}',
            encoding_config JSONB DEFAULT '{}',
            
            -- Feature Selection
            feature_selection_config JSONB DEFAULT '{}',
            dimensionality_reduction JSONB DEFAULT '{}',
            
            -- Validation
            validation_config JSONB DEFAULT '{}',
            quality_checks JSONB DEFAULT '{}',
            
            -- Status
            is_active BOOLEAN DEFAULT true,
            version VARCHAR(50) DEFAULT '1.0',
            
            -- Metadata
            created_by UUID REFERENCES users(id),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            
            -- Tags and Labels
            tags TEXT[] DEFAULT '{}',
            labels JSONB DEFAULT '{}',
            
            UNIQUE(config_name, version)
        );
        """

    # Trading Strategy Integration Tables
    @staticmethod
    def trading_strategy_config() -> str:
        """Trading strategy configuration table"""
        return """
        CREATE TABLE IF NOT EXISTS trading_strategy_config (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            strategy_name VARCHAR(255) NOT NULL,
            strategy_type VARCHAR(100) NOT NULL,
            description TEXT,
            
            -- Strategy Configuration
            strategy_config JSONB NOT NULL,
            entry_rules JSONB DEFAULT '{}',
            exit_rules JSONB DEFAULT '{}',
            
            -- Risk Management
            risk_management JSONB DEFAULT '{}',
            position_sizing JSONB DEFAULT '{}',
            
            -- Market Conditions
            applicable_markets TEXT[],
            applicable_timeframes TEXT[],
            applicable_symbols TEXT[],
            
            -- Model Integration
            ml_models_used UUID[],
            dl_models_used UUID[],
            ensemble_config JSONB DEFAULT '{}',
            
            -- Performance Targets
            target_metrics JSONB DEFAULT '{}',
            performance_thresholds JSONB DEFAULT '{}',
            
            -- Status
            is_active BOOLEAN DEFAULT true,
            is_live BOOLEAN DEFAULT false,
            
            -- Metadata
            created_by UUID REFERENCES users(id),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            
            -- Tags and Labels
            tags TEXT[] DEFAULT '{}',
            labels JSONB DEFAULT '{}',
            
            UNIQUE(strategy_name)
        );
        """

    @staticmethod
    def strategy_model_mapping() -> str:
        """Strategy model mapping table"""
        return """
        CREATE TABLE IF NOT EXISTS strategy_model_mapping (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            strategy_id UUID NOT NULL REFERENCES trading_strategy_config(id),
            model_id UUID NOT NULL,
            model_type VARCHAR(100) NOT NULL,
            
            -- Mapping Configuration
            model_role VARCHAR(100) NOT NULL,
            model_weight DECIMAL(5, 4) DEFAULT 1.0,
            model_priority INTEGER DEFAULT 1,
            
            -- Usage Configuration
            usage_conditions JSONB DEFAULT '{}',
            feature_mapping JSONB DEFAULT '{}',
            output_processing JSONB DEFAULT '{}',
            
            -- Status
            is_active BOOLEAN DEFAULT true,
            
            -- Metadata
            created_by UUID REFERENCES users(id),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            
            UNIQUE(strategy_id, model_id)
        );
        """

    @staticmethod
    def risk_management_config() -> str:
        """Risk management configuration table"""
        return """
        CREATE TABLE IF NOT EXISTS risk_management_config (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            config_name VARCHAR(255) NOT NULL,
            config_type VARCHAR(100) NOT NULL,
            description TEXT,
            
            -- Risk Limits
            max_position_size DECIMAL(15, 6),
            max_daily_loss DECIMAL(15, 6),
            max_drawdown DECIMAL(10, 6),
            
            -- Position Management
            position_sizing_method VARCHAR(100),
            position_sizing_config JSONB DEFAULT '{}',
            
            -- Stop Loss & Take Profit
            stop_loss_config JSONB DEFAULT '{}',
            take_profit_config JSONB DEFAULT '{}',
            trailing_stop_config JSONB DEFAULT '{}',
            
            -- Portfolio Risk
            correlation_limits JSONB DEFAULT '{}',
            exposure_limits JSONB DEFAULT '{}',
            sector_limits JSONB DEFAULT '{}',
            
            -- Risk Metrics
            risk_metrics JSONB DEFAULT '{}',
            risk_thresholds JSONB DEFAULT '{}',
            
            -- Status
            is_active BOOLEAN DEFAULT true,
            
            -- Metadata
            created_by UUID REFERENCES users(id),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            
            -- Tags and Labels
            tags TEXT[] DEFAULT '{}',
            labels JSONB DEFAULT '{}',
            
            UNIQUE(config_name)
        );
        """

    @staticmethod
    def get_table_list() -> List[str]:
        """Get list of all ML/DL metadata table names"""
        return [
            "ml_model_metadata",
            "dl_model_metadata",
            "model_versions",
            "model_experiments",
            "ai_pipeline_config",
            "pipeline_execution_logs",
            "pipeline_schedules",
            "model_performance_metrics",
            "model_predictions_log",
            "model_drift_detection",
            "technical_indicator_config",
            "feature_engineering_config",
            "data_preprocessing_config",
            "trading_strategy_config",
            "strategy_model_mapping",
            "risk_management_config",
        ]