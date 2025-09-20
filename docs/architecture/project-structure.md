# AI Trading System - Project Structure Design

## Overview

This document defines the comprehensive project structure for the AI trading system, organized to support microservices architecture, clear separation of concerns, and efficient development workflows.

## Root Project Structure

```
aitrading/
├── README.md
├── CLAUDE.md                          # Claude Code configuration
├── docker-compose.yml                 # Local development setup
├── docker-compose.prod.yml           # Production configuration
├── Makefile                           # Common development tasks
├── .gitignore
├── .env.example
├── .github/                           # GitHub workflows
│   └── workflows/
│       ├── ci.yml
│       ├── cd.yml
│       └── security-scan.yml
│
├── docs/                              # Documentation
│   ├── architecture/                  # Architecture documents
│   ├── api/                          # API documentation
│   ├── deployment/                   # Deployment guides
│   └── user/                         # User manuals
│
├── infrastructure/                    # Infrastructure as Code
│   ├── terraform/                    # Terraform configurations
│   ├── kubernetes/                   # K8s manifests
│   ├── helm/                         # Helm charts
│   └── monitoring/                   # Monitoring configurations
│
├── client/                           # Client-side applications
│   ├── metatrader/                   # MetaTrader integration
│   ├── data-collector/               # Data collection service
│   ├── market-monitor/               # Market monitoring
│   └── data-streamer/                # Data streaming service
│
├── services/                         # Server-side microservices
│   ├── api-gateway/                  # API Gateway
│   ├── data-ingestion/               # Data ingestion service
│   ├── feature-store/                # Feature store service
│   ├── ml-pipeline/                  # ML pipeline service
│   ├── prediction/                   # Prediction service
│   ├── decision/                     # Decision service
│   ├── execution/                    # Execution service
│   ├── risk-manager/                 # Risk management
│   ├── monitoring/                   # System monitoring
│   ├── telegram/                     # Telegram integration
│   └── web-frontend/                 # Web dashboard
│
├── shared/                           # Shared libraries and utilities
│   ├── proto/                        # Protocol Buffer definitions
│   ├── models/                       # Shared data models
│   ├── utils/                        # Common utilities
│   └── config/                       # Configuration management
│
├── ml/                               # Machine Learning components
│   ├── training/                     # Model training pipelines
│   ├── models/                       # Model implementations
│   ├── features/                     # Feature engineering
│   ├── evaluation/                   # Model evaluation
│   └── experiments/                  # ML experiments
│
├── data/                             # Data storage and processing
│   ├── schemas/                      # Data schemas
│   ├── migrations/                   # Database migrations
│   ├── seeds/                        # Test data
│   └── backups/                      # Backup scripts
│
├── tests/                            # Integration and E2E tests
│   ├── integration/                  # Integration tests
│   ├── e2e/                         # End-to-end tests
│   ├── performance/                  # Performance tests
│   └── fixtures/                     # Test data fixtures
│
├── scripts/                          # Utility scripts
│   ├── setup/                        # Environment setup
│   ├── deployment/                   # Deployment scripts
│   ├── maintenance/                  # Maintenance tasks
│   └── data/                         # Data processing scripts
│
└── tools/                            # Development tools
    ├── code-generation/              # Code generators
    ├── testing/                      # Testing utilities
    └── monitoring/                   # Local monitoring tools
```

## Client-Side Project Structure

### MetaTrader Integration
```
client/metatrader/
├── CMakeLists.txt                    # C++ build configuration
├── src/
│   ├── main.cpp                      # Entry point
│   ├── mt_connector.cpp              # MetaTrader connector
│   ├── mt_connector.h
│   ├── data_collector.cpp            # Data collection logic
│   ├── data_collector.h
│   ├── order_executor.cpp            # Order execution
│   ├── order_executor.h
│   └── utils/
│       ├── network.cpp               # Network utilities
│       ├── logging.cpp               # Logging utilities
│       └── config.cpp                # Configuration management
│
├── include/                          # Header files
│   ├── common.h
│   ├── types.h
│   └── constants.h
│
├── mql5/                            # MQL5 Expert Advisors
│   ├── DataExporter.mq5             # Data export EA
│   ├── OrderManager.mq5             # Order management EA
│   └── Include/
│       ├── DataTypes.mqh
│       └── NetworkUtils.mqh
│
├── tests/                           # Unit tests
│   ├── test_connector.cpp
│   ├── test_data_collector.cpp
│   └── test_order_executor.cpp
│
├── config/                          # Configuration files
│   ├── mt5_config.json
│   └── symbols.json
│
├── proto/                           # Protocol buffer definitions
│   ├── market_data.proto
│   └── orders.proto
│
└── docs/                            # Client-specific documentation
    ├── integration-guide.md
    └── configuration.md
```

### Data Collector Service
```
client/data-collector/
├── go.mod
├── go.sum
├── main.go                          # Entry point
├── cmd/
│   └── collector/
│       └── main.go                  # Command-line interface
│
├── internal/
│   ├── collector/
│   │   ├── collector.go             # Main collector logic
│   │   ├── mt_client.go             # MetaTrader client
│   │   ├── validator.go             # Data validation
│   │   ├── enricher.go              # Data enrichment
│   │   └── normalizer.go            # Data normalization
│   │
│   ├── streamer/
│   │   ├── grpc_streamer.go         # gRPC streaming
│   │   ├── kafka_streamer.go        # Kafka streaming
│   │   └── websocket_streamer.go    # WebSocket streaming
│   │
│   ├── storage/
│   │   ├── memory_buffer.go         # In-memory buffering
│   │   ├── file_buffer.go           # File-based buffering
│   │   └── redis_buffer.go          # Redis buffering
│   │
│   └── config/
│       ├── config.go                # Configuration management
│       └── validation.go            # Config validation
│
├── pkg/                             # Public packages
│   ├── models/
│   │   ├── market_data.go           # Market data models
│   │   └── config.go                # Configuration models
│   │
│   └── utils/
│       ├── logger.go                # Logging utilities
│       ├── metrics.go               # Metrics collection
│       └── health.go                # Health checks
│
├── api/                             # API definitions
│   ├── grpc/
│   │   └── market_data.proto
│   │
│   └── rest/
│       └── openapi.yaml
│
├── configs/                         # Configuration files
│   ├── config.yaml
│   ├── config.dev.yaml
│   └── config.prod.yaml
│
├── deployments/                     # Deployment configurations
│   ├── docker/
│   │   └── Dockerfile
│   │
│   └── kubernetes/
│       ├── deployment.yaml
│       ├── service.yaml
│       └── configmap.yaml
│
└── tests/
    ├── unit/
    ├── integration/
    └── testdata/
```

## Server-Side Microservices Structure

### Prediction Service (Python)
```
services/prediction/
├── pyproject.toml                   # Python project configuration
├── requirements.txt                 # Dependencies
├── requirements-dev.txt             # Development dependencies
├── Dockerfile                       # Container configuration
├── docker-compose.yml              # Local testing setup
│
├── app/                             # Application code
│   ├── __init__.py
│   ├── main.py                      # FastAPI application entry point
│   ├── config.py                    # Configuration management
│   │
│   ├── api/                         # API layer
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── endpoints/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── predictions.py   # Prediction endpoints
│   │   │   │   ├── models.py        # Model management endpoints
│   │   │   │   └── health.py        # Health check endpoints
│   │   │   │
│   │   │   └── api.py               # API router
│   │   │
│   │   └── dependencies.py          # FastAPI dependencies
│   │
│   ├── core/                        # Core business logic
│   │   ├── __init__.py
│   │   ├── prediction_engine.py    # Main prediction logic
│   │   ├── model_loader.py          # Model loading and management
│   │   ├── feature_processor.py    # Feature processing
│   │   ├── ensemble_manager.py     # Model ensemble logic
│   │   └── cache_manager.py         # Prediction caching
│   │
│   ├── models/                      # Data models
│   │   ├── __init__.py
│   │   ├── prediction.py           # Prediction models
│   │   ├── features.py             # Feature models
│   │   └── responses.py            # API response models
│   │
│   ├── services/                    # External service clients
│   │   ├── __init__.py
│   │   ├── feature_store.py        # Feature store client
│   │   ├── model_store.py          # Model store client
│   │   └── monitoring.py           # Monitoring service client
│   │
│   └── utils/                       # Utilities
│       ├── __init__.py
│       ├── logging.py              # Logging configuration
│       ├── metrics.py              # Metrics collection
│       ├── exceptions.py           # Custom exceptions
│       └── validators.py           # Data validators
│
├── tests/                           # Test suite
│   ├── __init__.py
│   ├── conftest.py                 # Pytest configuration
│   ├── unit/                       # Unit tests
│   │   ├── test_prediction_engine.py
│   │   ├── test_model_loader.py
│   │   └── test_feature_processor.py
│   │
│   ├── integration/                # Integration tests
│   │   ├── test_api.py
│   │   └── test_services.py
│   │
│   └── fixtures/                   # Test fixtures
│       ├── models/
│       └── data/
│
├── scripts/                        # Utility scripts
│   ├── model_deployment.py         # Model deployment script
│   ├── performance_test.py         # Performance testing
│   └── data_migration.py           # Data migration
│
├── configs/                        # Configuration files
│   ├── config.yaml                 # Default configuration
│   ├── config.dev.yaml            # Development configuration
│   ├── config.test.yaml           # Test configuration
│   └── config.prod.yaml           # Production configuration
│
└── docs/                           # Service documentation
    ├── api.md                      # API documentation
    ├── deployment.md               # Deployment guide
    └── performance.md              # Performance characteristics
```

### Execution Service (Go)
```
services/execution/
├── go.mod
├── go.sum
├── Makefile                        # Build and deployment tasks
├── Dockerfile                      # Container configuration
├── .dockerignore
│
├── cmd/
│   └── server/
│       └── main.go                 # Application entry point
│
├── internal/                       # Private application code
│   ├── config/
│   │   ├── config.go               # Configuration management
│   │   └── validation.go           # Configuration validation
│   │
│   ├── handler/                    # HTTP/gRPC handlers
│   │   ├── grpc/
│   │   │   ├── execution.go        # gRPC execution handlers
│   │   │   └── health.go           # Health check handlers
│   │   │
│   │   └── http/
│   │       ├── execution.go        # HTTP execution handlers
│   │       ├── metrics.go          # Metrics endpoints
│   │       └── middleware.go       # HTTP middleware
│   │
│   ├── service/                    # Business logic
│   │   ├── execution.go            # Order execution logic
│   │   ├── risk_check.go           # Risk validation
│   │   ├── order_router.go         # Order routing logic
│   │   └── position_tracker.go     # Position tracking
│   │
│   ├── repository/                 # Data access layer
│   │   ├── order.go                # Order repository
│   │   ├── position.go             # Position repository
│   │   └── trade.go                # Trade repository
│   │
│   ├── client/                     # External service clients
│   │   ├── metatrader.go           # MetaTrader client
│   │   ├── risk_manager.go         # Risk manager client
│   │   └── monitoring.go           # Monitoring client
│   │
│   └── model/                      # Data models
│       ├── order.go                # Order models
│       ├── trade.go                # Trade models
│       └── position.go             # Position models
│
├── pkg/                            # Public packages
│   ├── errors/
│   │   └── errors.go               # Custom error types
│   │
│   ├── metrics/
│   │   └── metrics.go              # Metrics definitions
│   │
│   └── utils/
│       ├── logger.go               # Logging utilities
│       ├── validator.go            # Validation utilities
│       └── converter.go            # Data conversion utilities
│
├── api/                            # API definitions
│   ├── proto/
│   │   ├── execution.proto         # gRPC service definition
│   │   └── common.proto            # Common message types
│   │
│   └── openapi/
│       └── execution.yaml          # OpenAPI specification
│
├── deployments/                    # Deployment configurations
│   ├── kubernetes/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── configmap.yaml
│   │   └── secret.yaml
│   │
│   └── docker-compose/
│       └── docker-compose.yml
│
├── scripts/                        # Utility scripts
│   ├── build.sh                    # Build script
│   ├── deploy.sh                   # Deployment script
│   └── test.sh                     # Test runner
│
├── configs/                        # Configuration files
│   ├── config.yaml                 # Default configuration
│   ├── config.dev.yaml            # Development environment
│   └── config.prod.yaml           # Production environment
│
└── test/                           # Test files
    ├── unit/                       # Unit tests
    ├── integration/                # Integration tests
    ├── fixtures/                   # Test fixtures
    └── mocks/                      # Mock implementations
```

## Machine Learning Project Structure

```
ml/
├── pyproject.toml                  # Python project configuration
├── requirements.txt                # Core dependencies
├── requirements-dev.txt            # Development dependencies
├── dvc.yaml                        # DVC pipeline configuration
├── params.yaml                     # Model parameters
│
├── data/                           # Data management
│   ├── raw/                        # Raw data (not tracked by git)
│   ├── processed/                  # Processed data
│   ├── features/                   # Feature sets
│   └── external/                   # External datasets
│
├── models/                         # Model artifacts
│   ├── trained/                    # Trained models
│   ├── checkpoints/                # Training checkpoints
│   └── experiments/                # Experiment artifacts
│
├── notebooks/                      # Jupyter notebooks
│   ├── exploratory/                # Exploratory data analysis
│   ├── experiments/                # Model experiments
│   └── reports/                    # Analysis reports
│
├── src/                            # Source code
│   ├── __init__.py
│   │
│   ├── data/                       # Data processing
│   │   ├── __init__.py
│   │   ├── loaders.py              # Data loading utilities
│   │   ├── preprocessors.py        # Data preprocessing
│   │   ├── validators.py           # Data validation
│   │   └── splitters.py            # Data splitting logic
│   │
│   ├── features/                   # Feature engineering
│   │   ├── __init__.py
│   │   ├── technical_indicators.py # Technical indicators
│   │   ├── market_features.py      # Market-based features
│   │   ├── time_features.py        # Time-based features
│   │   └── feature_selection.py    # Feature selection
│   │
│   ├── models/                     # Model implementations
│   │   ├── __init__.py
│   │   ├── base.py                 # Base model class
│   │   ├── classical/              # Classical ML models
│   │   │   ├── __init__.py
│   │   │   ├── xgboost_model.py
│   │   │   ├── lightgbm_model.py
│   │   │   └── random_forest.py
│   │   │
│   │   ├── deep_learning/          # Deep learning models
│   │   │   ├── __init__.py
│   │   │   ├── lstm.py
│   │   │   ├── transformer.py
│   │   │   ├── cnn.py
│   │   │   └── autoencoder.py
│   │   │
│   │   └── ensemble/               # Ensemble models
│   │       ├── __init__.py
│   │       ├── voting_ensemble.py
│   │       ├── stacking_ensemble.py
│   │       └── dynamic_ensemble.py
│   │
│   ├── training/                   # Training pipelines
│   │   ├── __init__.py
│   │   ├── trainers.py             # Training orchestration
│   │   ├── hyperparameter_tuning.py # Hyperparameter optimization
│   │   ├── cross_validation.py     # Cross-validation logic
│   │   └── early_stopping.py       # Early stopping callbacks
│   │
│   ├── evaluation/                 # Model evaluation
│   │   ├── __init__.py
│   │   ├── metrics.py              # Evaluation metrics
│   │   ├── backtesting.py          # Backtesting framework
│   │   ├── walk_forward.py         # Walk-forward analysis
│   │   └── stress_testing.py       # Stress testing
│   │
│   ├── inference/                  # Model inference
│   │   ├── __init__.py
│   │   ├── predictor.py            # Prediction logic
│   │   ├── ensemble_predictor.py   # Ensemble predictions
│   │   └── real_time_predictor.py  # Real-time inference
│   │
│   └── utils/                      # Utilities
│       ├── __init__.py
│       ├── config.py               # Configuration management
│       ├── logging.py              # Logging setup
│       ├── metrics.py              # Custom metrics
│       └── visualization.py        # Plotting utilities
│
├── scripts/                        # Training and deployment scripts
│   ├── train_model.py              # Model training script
│   ├── evaluate_model.py           # Model evaluation script
│   ├── hyperparameter_search.py    # Hyperparameter search
│   ├── model_comparison.py         # Model comparison
│   └── deploy_model.py             # Model deployment
│
├── configs/                        # Configuration files
│   ├── model_configs/              # Model-specific configs
│   │   ├── xgboost.yaml
│   │   ├── lstm.yaml
│   │   └── ensemble.yaml
│   │
│   ├── training_configs/           # Training configurations
│   │   ├── quick_train.yaml
│   │   ├── full_train.yaml
│   │   └── hyperparameter_search.yaml
│   │
│   └── feature_configs/            # Feature configurations
│       ├── technical_features.yaml
│       └── market_features.yaml
│
├── tests/                          # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/                       # Unit tests
│   ├── integration/                # Integration tests
│   └── fixtures/                   # Test fixtures
│
└── docs/                           # ML-specific documentation
    ├── model_cards/                # Model documentation
    ├── experiments/                # Experiment reports
    └── performance/                # Performance analysis
```

## Shared Libraries Structure

```
shared/
├── proto/                          # Protocol Buffer definitions
│   ├── market_data.proto           # Market data messages
│   ├── orders.proto                # Order messages
│   ├── predictions.proto           # Prediction messages
│   ├── common.proto                # Common types
│   └── Makefile                    # Proto compilation
│
├── models/                         # Shared data models
│   ├── python/                     # Python models
│   │   ├── __init__.py
│   │   ├── market_data.py
│   │   ├── orders.py
│   │   └── predictions.py
│   │
│   ├── go/                         # Go models
│   │   ├── market_data.go
│   │   ├── orders.go
│   │   └── predictions.go
│   │
│   └── cpp/                        # C++ models
│       ├── market_data.h
│       ├── orders.h
│       └── predictions.h
│
├── utils/                          # Common utilities
│   ├── python/                     # Python utilities
│   │   ├── __init__.py
│   │   ├── logging.py
│   │   ├── metrics.py
│   │   ├── config.py
│   │   └── validation.py
│   │
│   ├── go/                         # Go utilities
│   │   ├── logging/
│   │   ├── metrics/
│   │   ├── config/
│   │   └── validation/
│   │
│   └── cpp/                        # C++ utilities
│       ├── logging.h
│       ├── metrics.h
│       └── config.h
│
└── config/                         # Configuration schemas
    ├── schemas/                    # JSON schemas
    │   ├── service_config.json
    │   ├── model_config.json
    │   └── deployment_config.json
    │
    └── templates/                  # Configuration templates
        ├── service.yaml.template
        └── deployment.yaml.template
```

## Infrastructure Structure

```
infrastructure/
├── terraform/                     # Terraform configurations
│   ├── environments/              # Environment-specific configs
│   │   ├── dev/
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   └── terraform.tfvars
│   │   │
│   │   ├── staging/
│   │   └── prod/
│   │
│   ├── modules/                   # Reusable Terraform modules
│   │   ├── eks/                   # EKS cluster module
│   │   ├── rds/                   # RDS database module
│   │   ├── redis/                 # Redis cluster module
│   │   └── monitoring/            # Monitoring stack module
│   │
│   └── global/                    # Global resources
│       ├── iam/                   # IAM roles and policies
│       ├── vpc/                   # VPC configuration
│       └── dns/                   # DNS configuration
│
├── kubernetes/                    # Kubernetes manifests
│   ├── namespaces/                # Namespace definitions
│   ├── rbac/                      # RBAC configurations
│   ├── storage/                   # Storage classes and PVCs
│   ├── networking/                # Network policies
│   └── monitoring/                # Monitoring stack
│
├── helm/                          # Helm charts
│   ├── charts/                    # Custom Helm charts
│   │   ├── trading-api/
│   │   ├── ml-pipeline/
│   │   └── monitoring-stack/
│   │
│   └── values/                    # Environment-specific values
│       ├── dev/
│       ├── staging/
│       └── prod/
│
└── monitoring/                    # Monitoring configurations
    ├── prometheus/                # Prometheus configurations
    ├── grafana/                   # Grafana dashboards
    ├── alertmanager/              # Alert rules
    └── jaeger/                    # Tracing configuration
```

## Development Workflow Support

### Root Makefile
```makefile
# Makefile for development tasks
.PHONY: help setup build test deploy clean

help:
	@echo "Available commands:"
	@echo "  setup     - Set up development environment"
	@echo "  build     - Build all services"
	@echo "  test      - Run all tests"
	@echo "  deploy    - Deploy to development environment"
	@echo "  clean     - Clean build artifacts"

setup:
	@echo "Setting up development environment..."
	./scripts/setup/init-dev-env.sh

build:
	@echo "Building all services..."
	docker-compose -f docker-compose.yml build

test:
	@echo "Running tests..."
	./scripts/testing/run-all-tests.sh

deploy:
	@echo "Deploying to development..."
	./scripts/deployment/deploy-dev.sh

clean:
	@echo "Cleaning up..."
	docker-compose down --volumes --remove-orphans
	docker system prune -f
```

### VS Code Configuration
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "go.useLanguageServer": true,
    "go.toolsManagement.autoUpdate": true,
    "files.exclude": {
        "**/__pycache__": true,
        "**/node_modules": true,
        "**/target": true,
        "**/.git": true
    },
    "search.exclude": {
        "**/node_modules": true,
        "**/bower_components": true,
        "**/*.code-search": true,
        "**/venv": true,
        "**/__pycache__": true
    }
}
```

### Git Configuration
```gitignore
# .gitignore
# Binaries and executables
*.exe
*.dll
*.so
*.dylib
target/
dist/
build/

# Language-specific
__pycache__/
*.py[cod]
*.pyo
*.pyd
.Python
node_modules/
*.log

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Environment
.env
*.env
.env.local
.env.production

# Data and models
data/raw/
data/processed/
models/trained/
*.pkl
*.joblib
*.h5
*.onnx

# Terraform
*.tfstate
*.tfstate.*
.terraform/
.terraform.lock.hcl

# Kubernetes
.kubeconfig
```

This project structure provides a solid foundation for developing, testing, and deploying the AI trading system while maintaining clear separation of concerns and supporting efficient development workflows.