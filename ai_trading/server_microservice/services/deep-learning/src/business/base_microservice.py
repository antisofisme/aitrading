"""
🧠 Deep Learning Base Microservice - CENTRALIZED INFRASTRUCTURE FOUNDATION
Enterprise-grade base class for all Deep Learning microservice components

CENTRALIZED INFRASTRUCTURE:
- Standardized configuration management for DL workflows
- Centralized logging with DL-specific context
- Performance tracking with DL metrics collection
- Error handling with DL classification and recovery
- Event publishing with DL-specific patterns
- Health monitoring with DL model and GPU status checks
"""

import os
import sys
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

# SHARED INFRASTRUCTURE INTEGRATION
from ....shared.infrastructure.core.logger_core import CoreLogger
from ....shared.infrastructure.core.error_core import CoreErrorHandler
from ....shared.infrastructure.core.performance_core import CorePerformance
from ....shared.infrastructure.core.config_core import CoreConfig
from ....shared.infrastructure.optional.event_core import CoreEventManager
from ....shared.infrastructure.optional.validation_core import CoreValidator


class DeepLearningBaseMicroservice(ABC):
    """
    🧠 Base Microservice Class for Deep Learning Components
    
    Enterprise-grade foundation providing:
    - Centralized configuration management for DL workflows
    - Standardized logging with DL-specific context
    - Performance tracking and DL metrics collection
    - Error handling with DL-specific classification
    - Event publishing with DL workflow patterns
    - Health monitoring and DL model status checks
    - GPU resource management and monitoring
    """
    
    def __init__(self, service_name: str, component_name: str):
        """Initialize base microservice with centralized DL infrastructure"""
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
            
            # DL-specific initialization
            self._setup_dl_specific_components()
            
            # Publish initialization event
            self._publish_initialization_event()
            
            self.logger.info(f"✅ {self.microservice_id} DL base microservice initialized with centralized infrastructure")
            
        except Exception as e:
            error_response = CoreErrorHandler.handle_error(
                error=e,
                component=f"{service_name}_{component_name}_base",
                operation="initialize_dl_base_microservice",
                context={"service_name": service_name, "component_name": component_name}
            )
            raise RuntimeError(f"Failed to initialize DL base microservice: {error_response}")
    
    def _setup_centralized_logging(self):
        """Setup centralized logging with DL-specific context"""
        self.logger = CoreLogger.get_logger(f"{self.microservice_id}_microservice", {
            "component": "deep_learning_microservice",
            "service": self.service_name,
            "feature": self.component_name,
            "microservice_id": self.microservice_id,
            "ml_type": "deep_learning"
        })
    
    def _setup_centralized_configuration(self):
        """Setup centralized configuration management for DL"""
        try:
            # Load service-specific DL configuration through ConfigManager
            self.config = CoreConfig.get_config(f"{self.microservice_id}_config", self._get_default_config())
            
            # Load DL-specific environment settings
            self.environment = self.config.get("environment", "development")
            self.debug_mode = self.config.get("debug", False)
            self.enabled = self.config.get("enabled", True)
            
            # DL-specific configuration
            self.dl_config = self.config.get("dl_config", {})
            self.model_storage_path = self.config.get("model_storage_path", "/tmp/dl_models")
            self.checkpoint_path = self.config.get("checkpoint_path", "/tmp/dl_checkpoints")
            self.tensorboard_log_path = self.config.get("tensorboard_log_path", "/tmp/tensorboard_logs")
            self.max_model_memory_mb = self.config.get("max_model_memory_mb", 8192)
            self.enable_gpu = self.config.get("enable_gpu", True)
            self.mixed_precision = self.config.get("mixed_precision", False)
            self.distributed_training = self.config.get("distributed_training", False)
            self.max_batch_size = self.config.get("max_batch_size", 32)
            
        except Exception as e:
            self.logger.error(f"Failed to setup centralized DL configuration: {str(e)}")
            # Fallback to default DL configuration
            self.config = self._get_default_config()
            self.environment = "development"
            self.debug_mode = False
            self.enabled = True
            self.dl_config = {}
            self.model_storage_path = "/tmp/dl_models"
            self.checkpoint_path = "/tmp/dl_checkpoints"
            self.tensorboard_log_path = "/tmp/tensorboard_logs"
            self.max_model_memory_mb = 8192
            self.enable_gpu = True
            self.mixed_precision = False
            self.distributed_training = False
            self.max_batch_size = 32
    
    def _setup_centralized_metrics(self):
        """Setup centralized metrics collection for DL operations"""
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
            
            # DL-specific metrics
            "models_trained": 0,
            "models_loaded": 0,
            "inference_requests": 0,
            "training_epochs_completed": 0,
            "training_time_total_ms": 0,
            "inference_time_total_ms": 0,
            "data_loading_time_ms": 0,
            "model_evaluations": 0,
            "fine_tuning_sessions": 0,
            "checkpoints_saved": 0,
            "model_deployments": 0,
            "active_models": 0,
            "memory_usage_mb": 0,
            "cpu_utilization": 0.0,
            "gpu_utilization": 0.0,
            "gpu_memory_used_mb": 0.0,
            "gpu_memory_total_mb": 0.0,
            "batch_processing_count": 0,
            "gradients_computed": 0,
            "loss_calculations": 0,
            "optimizer_steps": 0,
            "learning_rate_updates": 0,
            "attention_computations": 0,
            "transformer_forward_passes": 0
        }
        
        # Register metrics with PerformanceManager
        CorePerformance.register_service_metrics(
            service_name=self.microservice_id,
            metrics_dict=self.metrics
        )
    
    def _setup_centralized_health_monitoring(self):
        """Setup centralized health monitoring for DL services"""
        self.health_status = {
            "status": "healthy",
            "service": self.microservice_id,
            "component": self.component_name,
            "initialized": True,
            "last_check": datetime.now().isoformat(),
            
            # DL-specific health status
            "models_status": "ready",
            "data_pipeline_status": "ready",
            "storage_available": True,
            "memory_available": True,
            "gpu_available": self.enable_gpu,
            "gpu_count": 0,
            "gpu_memory_available": True,
            "dl_frameworks_loaded": False,
            "cuda_available": False,
            "mixed_precision_enabled": self.mixed_precision,
            "distributed_training_ready": self.distributed_training
        }
    
    def _setup_dl_specific_components(self):
        """Setup DL-specific components and resources"""
        try:
            # Initialize DL model registry
            self.model_registry = {}
            self.active_models = {}
            self.training_jobs = {}
            self.inference_sessions = {}
            self.checkpoints = {}
            
            # DL framework status
            self.dl_frameworks = {
                "pytorch": False,
                "tensorflow": False,
                "transformers": False,
                "keras": False,
                "lightning": False,
                "numpy": False,
                "pandas": False
            }
            
            # GPU status
            self.gpu_status = {
                "cuda_available": False,
                "gpu_count": 0,
                "gpu_devices": [],
                "total_memory_mb": 0,
                "available_memory_mb": 0
            }
            
            # Initialize DL frameworks availability check
            self._check_dl_frameworks()
            self._check_gpu_availability()
            
            # Setup storage directories
            os.makedirs(self.model_storage_path, exist_ok=True)
            os.makedirs(self.checkpoint_path, exist_ok=True)
            os.makedirs(self.tensorboard_log_path, exist_ok=True)
            
            self.logger.info("✅ DL-specific components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to setup DL-specific components: {str(e)}")
    
    def _check_dl_frameworks(self):
        """Check availability of DL frameworks"""
        try:
            # Check PyTorch
            try:
                import torch
                self.dl_frameworks["pytorch"] = True
                self.logger.info(f"PyTorch {torch.__version__} available")
            except ImportError:
                pass
            
            # Check TensorFlow
            try:
                import tensorflow as tf
                self.dl_frameworks["tensorflow"] = True
                self.logger.info(f"TensorFlow {tf.__version__} available")
            except ImportError:
                pass
            
            # Check Transformers
            try:
                import transformers
                self.dl_frameworks["transformers"] = True
                self.logger.info(f"Transformers {transformers.__version__} available")
            except ImportError:
                pass
            
            # Check Keras
            try:
                import keras
                self.dl_frameworks["keras"] = True
            except ImportError:
                pass
            
            # Check Lightning
            try:
                import lightning
                self.dl_frameworks["lightning"] = True
            except ImportError:
                pass
            
            # Check NumPy
            try:
                import numpy
                self.dl_frameworks["numpy"] = True
            except ImportError:
                pass
            
            # Check Pandas
            try:
                import pandas
                self.dl_frameworks["pandas"] = True
            except ImportError:
                pass
            
            self.health_status["dl_frameworks_loaded"] = any(self.dl_frameworks.values())
            
        except Exception as e:
            self.logger.error(f"Failed to check DL frameworks: {str(e)}")
    
    def _check_gpu_availability(self):
        """Check GPU availability and status"""
        try:
            # Check CUDA with PyTorch
            if self.dl_frameworks["pytorch"]:
                import torch
                if torch.cuda.is_available():
                    self.gpu_status["cuda_available"] = True
                    self.gpu_status["gpu_count"] = torch.cuda.device_count()
                    
                    for i in range(self.gpu_status["gpu_count"]):
                        device_props = torch.cuda.get_device_properties(i)
                        self.gpu_status["gpu_devices"].append({
                            "device_id": i,
                            "name": device_props.name,
                            "total_memory_mb": device_props.total_memory // (1024 * 1024),
                            "major": device_props.major,
                            "minor": device_props.minor
                        })
                        self.gpu_status["total_memory_mb"] += device_props.total_memory // (1024 * 1024)
                    
                    self.health_status["cuda_available"] = True
                    self.health_status["gpu_count"] = self.gpu_status["gpu_count"]
                    self.logger.info(f"CUDA available with {self.gpu_status['gpu_count']} GPU(s)")
            
            # Check GPU with TensorFlow
            elif self.dl_frameworks["tensorflow"]:
                import tensorflow as tf
                gpu_devices = tf.config.list_physical_devices('GPU')
                if gpu_devices:
                    self.gpu_status["cuda_available"] = True
                    self.gpu_status["gpu_count"] = len(gpu_devices)
                    self.health_status["cuda_available"] = True
                    self.health_status["gpu_count"] = len(gpu_devices)
                    self.logger.info(f"TensorFlow GPU available with {len(gpu_devices)} GPU(s)")
            
            # Update metrics
            self.metrics["gpu_memory_total_mb"] = self.gpu_status["total_memory_mb"]
            
        except Exception as e:
            self.logger.error(f"Failed to check GPU availability: {str(e)}")
    
    def _publish_initialization_event(self):
        """Publish standardized DL initialization event"""
        try:
            CoreEventManager.publish_event(
                event_type=f"{self.microservice_id}_dl_initialized",
                component=f"{self.microservice_id}_microservice",
                message=f"{self.microservice_id} DL microservice initialized with centralized infrastructure",
                data={
                    "service_name": self.service_name,
                    "component_name": self.component_name,
                    "microservice_id": self.microservice_id,
                    "environment": self.environment,
                    "enabled": self.enabled,
                    "ml_type": "deep_learning",
                    "dl_frameworks": self.dl_frameworks,
                    "gpu_status": self.gpu_status,
                    "model_storage_path": self.model_storage_path,
                    "enable_gpu": self.enable_gpu,
                    "mixed_precision": self.mixed_precision,
                    "distributed_training": self.distributed_training,
                    "initialization_timestamp": time.time(),
                    "centralized_infrastructure": True
                }
            )
            self.metrics["events_published"] += 1
            
        except Exception as e:
            self.logger.error(f"Failed to publish DL initialization event: {str(e)}")
    
    @abstractmethod
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for the specific DL microservice component"""
        pass
    
    @abstractmethod
    def _perform_health_checks(self) -> Dict[str, Any]:
        """Perform DL component-specific health checks"""
        pass
    
    @performance_tracked(operation_name="centralized_dl_health_check")
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status with DL-specific patterns"""
        try:
            # Update uptime
            uptime = time.time() - self.metrics["startup_time"]
            self.metrics["uptime_seconds"] = uptime
            self.metrics["health_checks"] += 1
            
            # Perform DL component-specific health checks
            component_health = self._perform_health_checks()
            
            # Check DL framework status
            self._check_dl_frameworks()
            self._check_gpu_availability()
            
            # Update GPU utilization if available
            if self.gpu_status["cuda_available"] and self.dl_frameworks["pytorch"]:
                try:
                    import torch
                    if torch.cuda.is_available():
                        for i in range(torch.cuda.device_count()):
                            memory_allocated = torch.cuda.memory_allocated(i) // (1024 * 1024)
                            memory_cached = torch.cuda.memory_reserved(i) // (1024 * 1024)
                            self.metrics["gpu_memory_used_mb"] = memory_allocated
                            self.gpu_status["available_memory_mb"] = (
                                self.gpu_status["total_memory_mb"] - memory_cached
                            )
                except Exception:
                    pass
            
            # Create standardized DL health response
            health_data = {
                "status": "healthy" if component_health.get("healthy", True) else "unhealthy",
                "service": self.microservice_id,
                "component": self.component_name,
                "uptime_seconds": uptime,
                "environment": self.environment,
                "enabled": self.enabled,
                "metrics": self.metrics.copy(),
                "component_health": component_health,
                "dl_specific_status": {
                    "dl_frameworks": self.dl_frameworks,
                    "gpu_status": self.gpu_status,
                    "active_models": len(self.active_models),
                    "training_jobs": len(self.training_jobs),
                    "inference_sessions": len(self.inference_sessions),
                    "checkpoints": len(self.checkpoints),
                    "model_storage_available": os.path.exists(self.model_storage_path),
                    "checkpoint_storage_available": os.path.exists(self.checkpoint_path),
                    "tensorboard_available": os.path.exists(self.tensorboard_log_path),
                    "cuda_available": self.gpu_status["cuda_available"],
                    "mixed_precision_enabled": self.mixed_precision,
                    "distributed_training_ready": self.distributed_training
                },
                "configuration": {
                    "debug_mode": self.debug_mode,
                    "environment": self.environment,
                    "enabled": self.enabled,
                    "model_storage_path": self.model_storage_path,
                    "max_model_memory_mb": self.max_model_memory_mb,
                    "enable_gpu": self.enable_gpu,
                    "mixed_precision": self.mixed_precision,
                    "distributed_training": self.distributed_training,
                    "max_batch_size": self.max_batch_size
                },
                "timestamp": datetime.now().isoformat(),
                "centralized_infrastructure": True
            }
            
            # Update last check time
            self.health_status["last_check"] = datetime.now().isoformat()
            
            return health_data
            
        except Exception as e:
            error_response = CoreErrorHandler.handle_error(
                error=e,
                component=f"{self.microservice_id}_microservice",
                operation="dl_health_check",
                context={"service_name": self.service_name}
            )
            self.logger.error(f"DL health check failed: {error_response}")
            
            return {
                "status": "error",
                "service": self.microservice_id,
                "component": self.component_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    @performance_tracked(operation_name="centralized_dl_operation_tracking")
    def track_dl_operation(self, operation_name: str, operation_type: str = "general", success: bool = True, 
                          duration_ms: float = 0, metadata: Optional[Dict[str, Any]] = None):
        """Track DL operations with centralized performance management"""
        try:
            # Update general metrics
            self.metrics["total_operations"] += 1
            if success:
                self.metrics["successful_operations"] += 1
            else:
                self.metrics["failed_operations"] += 1
            
            self.metrics["last_activity"] = time.time()
            
            # Update DL-specific metrics based on operation type
            if operation_type == "training":
                self.metrics["models_trained"] += 1
                if duration_ms > 0:
                    self.metrics["training_time_total_ms"] += duration_ms
            elif operation_type == "inference":
                self.metrics["inference_requests"] += 1
                if duration_ms > 0:
                    self.metrics["inference_time_total_ms"] += duration_ms
            elif operation_type == "epoch_completion":
                self.metrics["training_epochs_completed"] += 1
            elif operation_type == "data_loading":
                if duration_ms > 0:
                    self.metrics["data_loading_time_ms"] += duration_ms
            elif operation_type == "evaluation":
                self.metrics["model_evaluations"] += 1
            elif operation_type == "fine_tuning":
                self.metrics["fine_tuning_sessions"] += 1
            elif operation_type == "checkpoint_save":
                self.metrics["checkpoints_saved"] += 1
            elif operation_type == "deployment":
                self.metrics["model_deployments"] += 1
            elif operation_type == "batch_processing":
                self.metrics["batch_processing_count"] += 1
            elif operation_type == "gradient_computation":
                self.metrics["gradients_computed"] += 1
            elif operation_type == "loss_calculation":
                self.metrics["loss_calculations"] += 1
            elif operation_type == "optimizer_step":
                self.metrics["optimizer_steps"] += 1
            elif operation_type == "learning_rate_update":
                self.metrics["learning_rate_updates"] += 1
            elif operation_type == "attention_computation":
                self.metrics["attention_computations"] += 1
            elif operation_type == "transformer_forward":
                self.metrics["transformer_forward_passes"] += 1
            
            # Record with PerformanceManager
            CorePerformance.record_metric(
                operation=f"{self.microservice_id}_dl_{operation_name}",
                duration_ms=duration_ms,
                success=success,
                metadata={
                    "service_name": self.service_name,
                    "component_name": self.component_name,
                    "microservice_id": self.microservice_id,
                    "operation_type": operation_type,
                    "ml_type": "deep_learning",
                    "gpu_used": self.enable_gpu,
                    "mixed_precision": self.mixed_precision,
                    **(metadata or {})
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to track DL operation {operation_name}: {str(e)}")
    
    @performance_tracked(operation_name="centralized_dl_error_handling")
    def handle_dl_error(self, error: Exception, operation: str, operation_type: str = "general", 
                       context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle DL errors with centralized error management"""
        try:
            self.metrics["errors_handled"] += 1
            self.metrics["failed_operations"] += 1
            
            error_response = CoreErrorHandler.handle_error(
                error=error,
                component=f"{self.microservice_id}_microservice",
                operation=operation,
                context={
                    "service_name": self.service_name,
                    "component_name": self.component_name,
                    "microservice_id": self.microservice_id,
                    "operation_type": operation_type,
                    "ml_type": "deep_learning",
                    "gpu_enabled": self.enable_gpu,
                    "cuda_available": self.gpu_status["cuda_available"],
                    **(context or {})
                }
            )
            
            self.logger.error(f"DL error in {operation}: {error_response}")
            return error_response
            
        except Exception as e:
            self.logger.critical(f"Critical error in DL error handling: {str(e)}")
            return {"error": "Critical DL error handling failure", "details": str(e)}
    
    @performance_tracked(operation_name="centralized_dl_event_publishing")
    def publish_dl_event(self, event_type: str, message: str, operation_type: str = "general", 
                        data: Optional[Dict[str, Any]] = None):
        """Publish DL events with centralized patterns"""
        try:
            CoreEventManager.publish_event(
                event_type=f"{self.microservice_id}_dl_{event_type}",
                component=f"{self.microservice_id}_microservice",
                message=f"[{self.microservice_id}] {message}",
                data={
                    "service_name": self.service_name,
                    "component_name": self.component_name,
                    "microservice_id": self.microservice_id,
                    "environment": self.environment,
                    "operation_type": operation_type,
                    "ml_type": "deep_learning",
                    "gpu_status": self.gpu_status,
                    "timestamp": time.time(),
                    **(data or {})
                }
            )
            self.metrics["events_published"] += 1
            
        except Exception as e:
            self.logger.error(f"Failed to publish DL event {event_type}: {str(e)}")
    
    # ===== SERVICE COMMUNICATION METHODS =====
    
    @performance_tracked(operation_name="communicate_with_service")
    async def communicate_with_service(self, 
                                     service_name: str, 
                                     endpoint: str, 
                                     data: Dict[str, Any], 
                                     method: str = "POST") -> Dict[str, Any]:
        """
        Communicate with other microservices in the AI trading platform
        Handles service discovery and communication patterns
        """
        try:
            import aiohttp
            import asyncio
            
            # Service discovery - map service names to endpoints
            service_endpoints = {
                "ai-orchestration": "http://ai-orchestration:8004",
                "ai-provider": "http://ai-provider:8005", 
                "ml-processing": "http://ml-processing:8008",
                "trading-engine": "http://trading-engine:8001",
                "data-bridge": "http://data-bridge:8002",
                "database-service": "http://database-service:8006",
                "user-service": "http://user-service:8009",
                "api-gateway": "http://api-gateway:8000"
            }
            
            if service_name not in service_endpoints:
                raise ValueError(f"Unknown service: {service_name}")
            
            base_url = service_endpoints[service_name]
            full_url = f"{base_url}{endpoint}"
            
            # Add authentication and correlation headers
            headers = {
                "Content-Type": "application/json",
                "X-Service-Name": self.service_name,
                "X-Service-Component": self.component_name,
                "X-Request-ID": f"{self.microservice_id}_{int(time.time())}"
            }
            
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                if method.upper() == "POST":
                    async with session.post(full_url, json=data, headers=headers) as response:
                        result = await response.json()
                elif method.upper() == "GET":
                    async with session.get(full_url, params=data, headers=headers) as response:
                        result = await response.json()
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                # Log successful communication
                self.logger.info(f"✅ Communication with {service_name} successful: {endpoint}")
                
                # Track communication metrics
                self.track_dl_operation(
                    operation_name=f"communicate_{service_name}",
                    operation_type="service_communication", 
                    success=True,
                    metadata={
                        "target_service": service_name,
                        "endpoint": endpoint,
                        "method": method,
                        "response_status": response.status
                    }
                )
                
                return {
                    "success": True,
                    "data": result,
                    "service": service_name,
                    "endpoint": endpoint,
                    "status_code": response.status
                }
                
        except Exception as e:
            # Track failed communication
            self.track_dl_operation(
                operation_name=f"communicate_{service_name}",
                operation_type="service_communication",
                success=False,
                metadata={
                    "target_service": service_name,
                    "endpoint": endpoint,
                    "error": str(e)
                }
            )
            
            error_response = self.handle_dl_error(e, f"communicate_with_{service_name}", "service_communication")
            self.logger.error(f"❌ Communication with {service_name} failed: {error_response}")
            
            return {
                "success": False,
                "error": str(e),
                "service": service_name,
                "endpoint": endpoint
            }
    
    async def register_with_api_gateway(self) -> bool:
        """Register this service with the API gateway for service discovery"""
        try:
            registration_data = {
                "service_name": self.service_name,
                "service_id": self.microservice_id,
                "host": f"{self.service_name}",
                "port": self._get_service_port(),
                "health_endpoint": "/health",
                "tags": ["deep-learning", "ai", "microservice"],
                "metadata": {
                    "component": self.component_name,
                    "ml_type": "deep_learning",
                    "gpu_enabled": self.enable_gpu,
                    "frameworks": list(k for k, v in self.dl_frameworks.items() if v),
                    "version": "2.0.0"
                }
            }
            
            result = await self.communicate_with_service(
                service_name="api-gateway",
                endpoint="/api/v1/services/register",
                data=registration_data,
                method="POST"
            )
            
            if result.get("success"):
                self.logger.info(f"✅ Successfully registered with API Gateway")
                return True
            else:
                self.logger.error(f"❌ Failed to register with API Gateway: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Service registration failed: {e}")
            return False
    
    async def get_ml_processing_insights(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """Get unsupervised learning insights from ML-processing service"""
        try:
            request_data = {
                "symbol": symbol,
                "timeframe": timeframe,
                "analysis_type": "unsupervised_learning",
                "include_clustering": True,
                "include_anomaly_detection": True
            }
            
            result = await self.communicate_with_service(
                service_name="ml-processing",
                endpoint="/api/v1/ml/analyze",
                data=request_data,
                method="POST"
            )
            
            if result.get("success"):
                return result.get("data", {})
            else:
                self.logger.warning(f"⚠️ Failed to get ML insights: {result}")
                return {}
                
        except Exception as e:
            self.logger.error(f"❌ ML processing communication failed: {e}")
            return {}
    
    async def send_prediction_to_trading_engine(self, prediction_data: Dict[str, Any]) -> bool:
        """Send deep learning predictions to trading engine"""
        try:
            result = await self.communicate_with_service(
                service_name="trading-engine",
                endpoint="/api/v1/predictions/deep-learning",
                data=prediction_data,
                method="POST"
            )
            
            if result.get("success"):
                self.logger.info(f"✅ Prediction sent to trading engine")
                return True
            else:
                self.logger.error(f"❌ Failed to send prediction: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Trading engine communication failed: {e}")
            return False
    
    async def get_real_time_market_data(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """Get real-time market data from data-bridge service"""
        try:
            request_data = {
                "symbol": symbol,
                "timeframe": timeframe,
                "include_indicators": True,
                "include_volume": True,
                "limit": 100
            }
            
            result = await self.communicate_with_service(
                service_name="data-bridge",
                endpoint="/api/v1/market-data/real-time",
                data=request_data,
                method="GET"
            )
            
            if result.get("success"):
                return result.get("data", {})
            else:
                self.logger.warning(f"⚠️ Failed to get market data: {result}")
                return {}
                
        except Exception as e:
            self.logger.error(f"❌ Data bridge communication failed: {e}")
            return {}
    
    async def save_model_to_database(self, model_data: Dict[str, Any]) -> bool:
        """Save trained model to database service"""
        try:
            result = await self.communicate_with_service(
                service_name="database-service",
                endpoint="/api/v1/models/save",
                data=model_data,
                method="POST"
            )
            
            if result.get("success"):
                self.logger.info(f"✅ Model saved to database")
                return True
            else:
                self.logger.error(f"❌ Failed to save model: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Database service communication failed: {e}")
            return False
    
    async def notify_telegram_bot(self, message: str, data: Dict[str, Any] = None) -> bool:
        """Send notifications through Telegram bot in trading engine"""
        try:
            notification_data = {
                "message": message,
                "source": self.microservice_id,
                "type": "deep_learning_prediction",
                "data": data or {},
                "timestamp": datetime.now().isoformat()
            }
            
            result = await self.communicate_with_service(
                service_name="trading-engine",
                endpoint="/api/v1/notifications/telegram",
                data=notification_data,
                method="POST"
            )
            
            if result.get("success"):
                self.logger.info(f"✅ Telegram notification sent")
                return True
            else:
                self.logger.warning(f"⚠️ Telegram notification failed: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Telegram notification failed: {e}")
            return False
    
    def _get_service_port(self) -> int:
        """Get the port number for this service"""
        # Deep learning service typically runs on port 8007
        return 8007
    
    def validate_dl_data(self, data: Dict[str, Any], required_fields: List[str], 
                        data_type: str = "general") -> bool:
        """Validate DL data with centralized validation"""
        try:
            validation_result = CoreValidator.validate_required_fields(data, required_fields)
            
            if hasattr(validation_result, 'is_valid'):
                return validation_result.is_valid
            else:
                # Fallback validation
                return all(field in data and data[field] is not None for field in required_fields)
                
        except Exception as e:
            self.logger.error(f"DL data validation failed for {data_type}: {str(e)}")
            return False


class DeepLearningMicroserviceFactory:
    """Factory for creating Deep Learning microservice instances with centralized infrastructure"""
    
    @staticmethod
    def create_microservice(component_type: str, service_name: str = "deep-learning") -> DeepLearningBaseMicroservice:
        """Create DL microservice instance with proper centralization"""
        
        # Import specific DL microservice implementations
        if component_type == "neural_network_trainer":
            from .neural_network_trainer import DeepLearningNeuralNetworkTrainer
            return DeepLearningNeuralNetworkTrainer()
        elif component_type == "transformer_fine_tuner":
            from .transformer_fine_tuner import DeepLearningTransformerFineTuner
            return DeepLearningTransformerFineTuner()
        elif component_type == "inference_engine":
            from .inference_engine import DeepLearningInferenceEngine
            return DeepLearningInferenceEngine()
        elif component_type == "model_optimizer":
            from .model_optimizer import DeepLearningModelOptimizer
            return DeepLearningModelOptimizer()
        elif component_type == "data_pipeline":
            from .data_pipeline import DeepLearningDataPipeline
            return DeepLearningDataPipeline()
        else:
            raise ValueError(f"Unknown DL microservice component type: {component_type}")


# Helper function to get DL microservice instance
def get_deep_learning_microservice(component_type: str = "neural_network_trainer") -> DeepLearningBaseMicroservice:
    """Get Deep Learning microservice instance with centralized infrastructure"""
    return DeepLearningMicroserviceFactory.create_microservice(component_type)