"""
🤖 ML Processing Base Microservice - CENTRALIZED INFRASTRUCTURE FOUNDATION
Enterprise-grade base class for all ML Processing microservice components

CENTRALIZED INFRASTRUCTURE:
- Standardized configuration management for ML workflows
- Centralized logging with ML-specific context
- Performance tracking with ML metrics collection
- Error handling with ML classification and recovery
- Event publishing with ML-specific patterns
- Health monitoring with ML model status checks
"""

import os
import sys
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

# CENTRALIZED INFRASTRUCTURE - PROPER SETUP
def setup_centralized_infrastructure():
    """Setup centralized infrastructure paths for ML Processing microservice"""
    server_side_src = Path(__file__).parent.parent.parent.parent.parent.parent / "server_side" / "src"
    if str(server_side_src) not in sys.path:
        sys.path.insert(0, str(server_side_src))

# Initialize centralized infrastructure once
setup_centralized_infrastructure()

# Service-specific infrastructure imports (microservice pattern)
from ...shared.infrastructure.core.logger_core import CoreLogger
from ...shared.infrastructure.core.error_core import CoreErrorHandler
from ...shared.infrastructure.core.performance_core import CorePerformance, performance_tracked
from ...shared.infrastructure.core.config_core import CoreConfig
from ...shared.infrastructure.optional.event_core import CoreEventManager
from ...shared.infrastructure.optional.validation_core import CoreValidator


class MlProcessingBaseMicroservice(ABC):
    """
    🤖 Base Microservice Class for ML Processing Components
    
    Enterprise-grade foundation providing:
    - Centralized configuration management for ML workflows
    - Standardized logging with ML-specific context
    - Performance tracking and ML metrics collection
    - Error handling with ML-specific classification
    - Event publishing with ML workflow patterns
    - Health monitoring and ML model status checks
    """
    
    @performance_tracked(service_name="ml-processing", operation_name="initialize_ml_base_microservice")
    def __init__(self, service_name: str, component_name: str):
        """Initialize base microservice with centralized ML infrastructure"""
        try:
            # Core service identification
            self.service_name = service_name
            self.component_name = component_name
            self.microservice_id = f"{service_name}_{component_name}"
            
            # Initialize centralized infrastructure
            self._setup_centralized_logging()
            self._setup_centralized_configuration()
            self._setup_centralized_metrics()
            self._setup_centralized_health_monitoring()
            
            # ML-specific initialization
            self._setup_ml_specific_components()
            
            # Publish initialization event
            self._publish_initialization_event()
            
            self.logger.info(f"✅ {self.microservice_id} ML base microservice initialized with centralized infrastructure")
            
        except Exception as e:
            error_handler = CoreErrorHandler(service_name)
            error_response = error_handler.handle_error(
                error=e,
                context={"service_name": service_name, "component_name": component_name}
            )
            raise RuntimeError(f"Failed to initialize ML base microservice: {error_response}")
    
    def _setup_centralized_logging(self):
        """Setup centralized logging with ML-specific context"""
        self.logger = CoreLogger(f"{self.microservice_id}_microservice", self.microservice_id)
    
    def _setup_centralized_configuration(self):
        """Setup centralized configuration management for ML"""
        try:
            # Load service-specific ML configuration through ConfigManager
            self.config_manager = CoreConfig(self.service_name)
            
            # Load ML-specific environment settings
            self.environment = self.config_manager.get("environment", "development")
            self.debug_mode = self.config_manager.get("debug", False)
            self.enabled = self.config_manager.get("enabled", True)
            
            # ML-specific configuration
            self.ml_config = self.config_manager.get("ml_config", {})
            self.model_storage_path = self.config_manager.get("model_storage_path", "/tmp/ml_models")
            self.data_cache_path = self.config_manager.get("data_cache_path", "/tmp/ml_data_cache")
            self.max_model_memory_mb = self.config_manager.get("max_model_memory_mb", 2048)
            self.enable_gpu = self.config_manager.get("enable_gpu", False)
            
        except Exception as e:
            self.logger.error(f"Failed to setup centralized ML configuration: {str(e)}")
            # Fallback to default ML configuration
            self.environment = "development"
            self.debug_mode = False
            self.enabled = True
            self.ml_config = {}
            self.model_storage_path = "/tmp/ml_models"
            self.data_cache_path = "/tmp/ml_data_cache"
            self.max_model_memory_mb = 2048
            self.enable_gpu = False
    
    def _setup_centralized_metrics(self):
        """Setup centralized metrics collection for ML operations"""
        self.metrics = {
            "startup_time": time.time(),
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "health_checks": 0,
            "events_published": 0,
            "errors_handled": 0,
            "uptime_seconds": 0,
            "last_activity": time.time(),
            
            # ML-specific metrics
            "models_trained": 0,
            "models_loaded": 0,
            "predictions_made": 0,
            "training_time_total_ms": 0,
            "inference_time_total_ms": 0,
            "feature_engineering_operations": 0,
            "data_preprocessing_operations": 0,
            "model_evaluations": 0,
            "hyperparameter_tuning_sessions": 0,
            "cross_validation_runs": 0,
            "model_deployments": 0,
            "active_models": 0,
            "memory_usage_mb": 0,
            "cpu_utilization": 0.0,
            "gpu_utilization": 0.0
        }
        
        # Metrics are stored locally and can be accessed via get_health_status
    
    def _setup_centralized_health_monitoring(self):
        """Setup centralized health monitoring for ML services"""
        self.health_status = {
            "status": "healthy",
            "service": self.microservice_id,
            "component": self.component_name,
            "initialized": True,
            "last_check": datetime.now().isoformat(),
            
            # ML-specific health status
            "models_status": "ready",
            "data_pipeline_status": "ready",
            "storage_available": True,
            "memory_available": True,
            "gpu_available": self.enable_gpu,
            "ml_frameworks_loaded": False
        }
    
    def _setup_ml_specific_components(self):
        """Setup ML-specific components and resources"""
        try:
            # Initialize ML model registry
            self.model_registry = {}
            self.active_models = {}
            self.training_jobs = {}
            self.feature_pipelines = {}
            
            # ML framework status
            self.ml_frameworks = {
                "scikit_learn": False,
                "xgboost": False,
                "catboost": False,
                "lightgbm": False,
                "pandas": False,
                "numpy": False
            }
            
            # Initialize ML frameworks availability check
            self._check_ml_frameworks()
            
            # Setup model storage directories
            os.makedirs(self.model_storage_path, exist_ok=True)
            os.makedirs(self.data_cache_path, exist_ok=True)
            
            self.logger.info("✅ ML-specific components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to setup ML-specific components: {str(e)}")
    
    def _check_ml_frameworks(self):
        """Check availability of ML frameworks"""
        try:
            # Check scikit-learn
            try:
                import sklearn
                self.ml_frameworks["scikit_learn"] = True
            except ImportError:
                pass
            
            # Check XGBoost
            try:
                import xgboost
                self.ml_frameworks["xgboost"] = True
            except ImportError:
                pass
            
            # Check CatBoost
            try:
                import catboost
                self.ml_frameworks["catboost"] = True
            except ImportError:
                pass
            
            # Check LightGBM
            try:
                import lightgbm
                self.ml_frameworks["lightgbm"] = True
            except ImportError:
                pass
            
            # Check Pandas
            try:
                import pandas
                self.ml_frameworks["pandas"] = True
            except ImportError:
                pass
            
            # Check NumPy
            try:
                import numpy
                self.ml_frameworks["numpy"] = True
            except ImportError:
                pass
            
            self.health_status["ml_frameworks_loaded"] = any(self.ml_frameworks.values())
            
        except Exception as e:
            self.logger.error(f"Failed to check ML frameworks: {str(e)}")
    
    def _publish_initialization_event(self):
        """Publish standardized ML initialization event"""
        try:
            event_manager = CoreEventManager(self.service_name)
            # Create event data with message and metadata
            event_data = {
                "message": f"{self.microservice_id} ML microservice initialized with centralized infrastructure",
                "service_name": self.service_name,
                "component_name": self.component_name,
                "microservice_id": self.microservice_id,
                "environment": self.environment,
                "enabled": self.enabled,
                "ml_type": "traditional_ml",
                "ml_frameworks": self.ml_frameworks,
                "model_storage_path": self.model_storage_path,
                "enable_gpu": self.enable_gpu,
                "initialization_timestamp": time.time(),
                "centralized_infrastructure": True
            }
            # Note: Using try-except as event publishing is not critical for initialization
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    event_manager.publish_event(
                        event_name=f"{self.microservice_id}_ml_initialized",
                        data=event_data
                    )
                )
                loop.close()
            except Exception as event_error:
                self.logger.warning(f"Failed to publish initialization event: {event_error}")
            self.metrics["events_published"] += 1
            
        except Exception as e:
            self.logger.error(f"Failed to publish ML initialization event: {str(e)}")
    
    @abstractmethod
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for the specific ML microservice component"""
        pass
    
    @abstractmethod
    def _perform_health_checks(self) -> Dict[str, Any]:
        """Perform ML component-specific health checks"""
        pass
    
    @performance_tracked(service_name="ml-processing", operation_name="centralized_ml_health_check")
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status with ML-specific patterns"""
        try:
            # Update uptime
            uptime = time.time() - self.metrics["startup_time"]
            self.metrics["uptime_seconds"] = uptime
            self.metrics["health_checks"] += 1
            
            # Perform ML component-specific health checks
            component_health = self._perform_health_checks()
            
            # Check ML framework status
            self._check_ml_frameworks()
            
            # Create standardized ML health response
            health_data = {
                "status": "healthy" if component_health.get("healthy", True) else "unhealthy",
                "service": self.microservice_id,
                "component": self.component_name,
                "uptime_seconds": uptime,
                "environment": self.environment,
                "enabled": self.enabled,
                "metrics": self.metrics.copy(),
                "component_health": component_health,
                "ml_specific_status": {
                    "ml_frameworks": self.ml_frameworks,
                    "active_models": len(self.active_models),
                    "training_jobs": len(self.training_jobs),
                    "feature_pipelines": len(self.feature_pipelines),
                    "model_storage_available": os.path.exists(self.model_storage_path),
                    "data_cache_available": os.path.exists(self.data_cache_path),
                    "gpu_enabled": self.enable_gpu
                },
                "configuration": {
                    "debug_mode": self.debug_mode,
                    "environment": self.environment,
                    "enabled": self.enabled,
                    "model_storage_path": self.model_storage_path,
                    "max_model_memory_mb": self.max_model_memory_mb,
                    "enable_gpu": self.enable_gpu
                },
                "timestamp": datetime.now().isoformat(),
                "centralized_infrastructure": True
            }
            
            # Update last check time
            self.health_status["last_check"] = datetime.now().isoformat()
            
            return health_data
            
        except Exception as e:
            error_handler = CoreErrorHandler(self.service_name)
            error_response = error_handler.handle_error(
                error=e,
                context={"service_name": self.service_name}
            )
            self.logger.error(f"ML health check failed: {error_response}")
            
            return {
                "status": "error",
                "service": self.microservice_id,
                "component": self.component_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    @performance_tracked(service_name="ml-processing", operation_name="centralized_ml_operation_tracking")
    def track_ml_operation(self, operation_name: str, operation_type: str = "general", success: bool = True, 
                          duration_ms: float = 0, metadata: Optional[Dict[str, Any]] = None):
        """Track ML operations with centralized performance management"""
        try:
            # Update general metrics
            self.metrics["total_operations"] += 1
            if success:
                self.metrics["successful_operations"] += 1
            else:
                self.metrics["failed_operations"] += 1
            
            self.metrics["last_activity"] = time.time()
            
            # Update ML-specific metrics based on operation type
            if operation_type == "training":
                self.metrics["models_trained"] += 1
                if duration_ms > 0:
                    self.metrics["training_time_total_ms"] += duration_ms
            elif operation_type == "inference":
                self.metrics["predictions_made"] += 1
                if duration_ms > 0:
                    self.metrics["inference_time_total_ms"] += duration_ms
            elif operation_type == "feature_engineering":
                self.metrics["feature_engineering_operations"] += 1
            elif operation_type == "preprocessing":
                self.metrics["data_preprocessing_operations"] += 1
            elif operation_type == "evaluation":
                self.metrics["model_evaluations"] += 1
            elif operation_type == "hyperparameter_tuning":
                self.metrics["hyperparameter_tuning_sessions"] += 1
            elif operation_type == "cross_validation":
                self.metrics["cross_validation_runs"] += 1
            elif operation_type == "deployment":
                self.metrics["model_deployments"] += 1
            
            # Performance metrics are tracked locally in self.metrics
            
        except Exception as e:
            self.logger.error(f"Failed to track ML operation {operation_name}: {str(e)}")
    
    @performance_tracked(service_name="ml-processing", operation_name="centralized_ml_error_handling")
    def handle_ml_error(self, error: Exception, operation: str, operation_type: str = "general", 
                       context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle ML errors with centralized error management"""
        try:
            self.metrics["errors_handled"] += 1
            self.metrics["failed_operations"] += 1
            
            error_handler = CoreErrorHandler(self.service_name)
            error_response = error_handler.handle_error(
                error=error,
                context={
                    "service_name": self.service_name,
                    "component_name": self.component_name,
                    "microservice_id": self.microservice_id,
                    "operation_type": operation_type,
                    "ml_type": "traditional_ml",
                    **(context or {})
                }
            )
            
            self.logger.error(f"ML error in {operation}: {error_response}")
            return error_response
            
        except Exception as e:
            self.logger.critical(f"Critical error in ML error handling: {str(e)}")
            return {"error": "Critical ML error handling failure", "details": str(e)}
    
    @performance_tracked(service_name="ml-processing", operation_name="centralized_ml_event_publishing")
    def publish_ml_event(self, event_type: str, message: str, operation_type: str = "general", 
                        data: Optional[Dict[str, Any]] = None):
        """Publish ML events with centralized patterns"""
        try:
            event_manager = CoreEventManager(self.service_name)
            event_data = {
                "message": f"[{self.microservice_id}] {message}",
                "service_name": self.service_name,
                "component_name": self.component_name,
                "microservice_id": self.microservice_id,
                "environment": self.environment,
                "operation_type": operation_type,
                "ml_type": "traditional_ml",
                "timestamp": time.time(),
                **(data or {})
            }
            # Note: Using try-except as event publishing is not critical
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    event_manager.publish_event(
                        event_name=f"{self.microservice_id}_ml_{event_type}",
                        data=event_data
                    )
                )
                loop.close()
            except Exception as event_error:
                self.logger.warning(f"Failed to publish ML event {event_type}: {event_error}")
            self.metrics["events_published"] += 1
            
        except Exception as e:
            self.logger.error(f"Failed to publish ML event {event_type}: {str(e)}")
    
    def validate_ml_data(self, data: Dict[str, Any], required_fields: List[str], 
                        data_type: str = "general") -> bool:
        """Validate ML data with centralized validation"""
        try:
            validation_result = CoreValidator.validate_required_fields(data, required_fields)
            
            if hasattr(validation_result, 'is_valid'):
                return validation_result.is_valid
            else:
                # Fallback validation
                return all(field in data and data[field] is not None for field in required_fields)
                
        except Exception as e:
            self.logger.error(f"ML data validation failed for {data_type}: {str(e)}")
            return False


class MlProcessingMicroserviceFactory:
    """Factory for creating ML Processing microservice instances with centralized infrastructure"""
    
    @staticmethod
    def create_microservice(component_type: str, service_name: str = "ml-processing") -> MlProcessingBaseMicroservice:
        """Create ML microservice instance with proper centralization"""
        
        # Import specific ML microservice implementations
        if component_type == "traditional_ml_trainer":
            from .traditional_ml_trainer import MLProcessingTraditionalMLTrainer
            return MLProcessingTraditionalMLTrainer()
        elif component_type == "feature_engineer":
            from .feature_engineer import MLProcessingFeatureEngineer
            return MLProcessingFeatureEngineer()
        elif component_type == "model_evaluator":
            from .model_evaluator import MLProcessingModelEvaluator
            return MLProcessingModelEvaluator()
        elif component_type == "hyperparameter_tuner":
            from .hyperparameter_tuner import MLProcessingHyperparameterTuner
            return MLProcessingHyperparameterTuner()
        elif component_type == "data_preprocessor":
            from .data_preprocessor import MLProcessingDataPreprocessor
            return MLProcessingDataPreprocessor()
        else:
            raise ValueError(f"Unknown ML microservice component type: {component_type}")


# Helper function to get ML microservice instance
def get_ml_processing_microservice(component_type: str = "traditional_ml_trainer") -> MlProcessingBaseMicroservice:
    """Get ML Processing microservice instance with centralized infrastructure"""
    return MlProcessingMicroserviceFactory.create_microservice(component_type)