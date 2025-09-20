"""
🧠 Deep Learning API Endpoints - Microservice Implementation
Enterprise-grade API endpoints for neural networks with PyTorch, TensorFlow, and Transformers

CENTRALIZED INFRASTRUCTURE:
- Performance tracking for DL operations
- Centralized error handling for DL API responses
- Event publishing for DL lifecycle monitoring
- Enhanced logging with DL-specific configuration
- Comprehensive validation for DL requests
- Advanced metrics tracking for DL performance optimization
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query, Path, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

# CENTRALIZED INFRASTRUCTURE - PROPER PATHS
import sys
from pathlib import Path

# Import shared infrastructure
from ....shared.infrastructure.core.logger_core import CoreLogger
from ....shared.infrastructure.core.error_core import CoreErrorHandler
from ....shared.infrastructure.core.performance_core import CorePerformance
from ....shared.infrastructure.core.config_core import CoreConfig
from ....shared.infrastructure.optional.event_core import CoreEventManager
from ....shared.infrastructure.optional.validation_core import CoreValidator

# Enhanced logger for API endpoints  
logger_core = CoreLogger("deep-learning", "api")
api_logger = logger_core

# API performance metrics
api_metrics = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "avg_response_time_ms": 0,
    "total_response_time_ms": 0,
    "events_published": 0,
    "validation_errors": 0,
    "concurrent_requests_peak": 0,
    "health_checks": 0,
    "model_training_requests": 0,
    "inference_requests": 0,
    "fine_tuning_requests": 0,
    "gpu_utilization_avg": 0.0
}

# FastAPI router for deep learning
router = APIRouter(prefix="/api/v1/deep-learning", tags=["Deep Learning"])


# ENUMS FOR DEEP LEARNING

class DLTaskType(Enum):
    """Types of deep learning tasks supported"""
    IMAGE_CLASSIFICATION = "image_classification"
    TIME_SERIES_FORECASTING = "time_series_forecasting"
    SEQUENCE_MODELING = "sequence_modeling"
    NATURAL_LANGUAGE_PROCESSING = "nlp"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    ANOMALY_DETECTION = "anomaly_detection"
    GENERATIVE_MODELING = "generative_modeling"
    REINFORCEMENT_LEARNING = "reinforcement_learning"
    TRANSFORMER_FINE_TUNING = "transformer_fine_tuning"


class DLFramework(Enum):
    """Deep learning frameworks supported"""
    PYTORCH = "pytorch"
    TENSORFLOW = "tensorflow"
    TRANSFORMERS = "transformers"
    KERAS = "keras"
    LIGHTNING = "lightning"


class NetworkArchitecture(Enum):
    """Neural network architectures supported"""
    CNN = "cnn"
    RNN = "rnn"
    LSTM = "lstm"
    GRU = "gru"
    TRANSFORMER = "transformer"
    BERT = "bert"
    GPT = "gpt"
    RESNET = "resnet"
    ATTENTION = "attention"
    AUTOENCODER = "autoencoder"
    GAN = "gan"
    VAE = "vae"


class TrainingStatus(Enum):
    """Deep learning model training status"""
    PENDING = "pending"
    TRAINING = "training"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    DEPLOYED = "deployed"
    FINE_TUNING = "fine_tuning"


# PYDANTIC MODELS FOR DL API

class DLTrainingRequest(BaseModel):
    """Request model for deep learning model training"""
    task_type: str = Field(..., description="Type of DL task to perform")
    framework: str = Field(..., description="DL framework to use")
    architecture: str = Field(..., description="Neural network architecture")
    training_data: Dict[str, Any] = Field(..., description="Training dataset configuration")
    model_config: Dict[str, Any] = Field(..., description="Model architecture configuration")
    training_config: Dict[str, Any] = Field(..., description="Training hyperparameters")
    validation_config: Optional[Dict[str, Any]] = Field(default=None, description="Validation configuration")
    model_name: str = Field(..., description="Unique model name/identifier")
    use_gpu: bool = Field(default=True, description="Use GPU for training")
    distributed_training: bool = Field(default=False, description="Enable distributed training")
    checkpointing: bool = Field(default=True, description="Enable model checkpointing")
    early_stopping: bool = Field(default=True, description="Enable early stopping")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    
    @validator('task_type')
    def validate_task_type(cls, v):
        try:
            DLTaskType(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid task_type. Must be one of: {[t.value for t in DLTaskType]}")
    
    @validator('framework')
    def validate_framework(cls, v):
        try:
            DLFramework(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid framework. Must be one of: {[f.value for f in DLFramework]}")
    
    @validator('architecture')
    def validate_architecture(cls, v):
        try:
            NetworkArchitecture(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid architecture. Must be one of: {[a.value for a in NetworkArchitecture]}")


class DLInferenceRequest(BaseModel):
    """Request model for deep learning inference"""
    model_name: str = Field(..., description="Name of trained model to use")
    input_data: Dict[str, Any] = Field(..., description="Input data for inference")
    preprocessing_config: Optional[Dict[str, Any]] = Field(default=None, description="Preprocessing configuration")
    postprocessing_config: Optional[Dict[str, Any]] = Field(default=None, description="Postprocessing configuration")
    batch_size: int = Field(default=1, ge=1, le=1000, description="Batch size for inference")
    use_gpu: bool = Field(default=True, description="Use GPU for inference")
    return_attention_weights: bool = Field(default=False, description="Return attention weights for transformers")
    return_embeddings: bool = Field(default=False, description="Return intermediate embeddings")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class FineTuningRequest(BaseModel):
    """Request model for model fine-tuning"""
    base_model_name: str = Field(..., description="Base model to fine-tune")
    task_type: str = Field(..., description="Target task type for fine-tuning")
    fine_tuning_data: Dict[str, Any] = Field(..., description="Fine-tuning dataset configuration")
    fine_tuning_config: Dict[str, Any] = Field(..., description="Fine-tuning hyperparameters")
    target_model_name: str = Field(..., description="Name for fine-tuned model")
    freeze_layers: Optional[List[str]] = Field(default=None, description="Layers to freeze during fine-tuning")
    learning_rate_schedule: Optional[Dict[str, Any]] = Field(default=None, description="Learning rate scheduling")
    use_lora: bool = Field(default=False, description="Use LoRA (Low-Rank Adaptation)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class DLModelResponse(BaseModel):
    """Response model for deep learning model operations"""
    model_id: str
    model_name: str
    status: str
    task_type: str
    framework: str
    architecture: str
    created_at: str
    training_started_at: Optional[str] = None
    training_completed_at: Optional[str] = None
    training_time_ms: float = 0.0
    training_metrics: Optional[Dict[str, Any]] = None
    validation_metrics: Optional[Dict[str, Any]] = None
    model_config: Dict[str, Any] = {}
    training_config: Dict[str, Any] = {}
    model_size_mb: float = 0.0
    parameters_count: int = 0
    gpu_memory_used_mb: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}


class DLInferenceResponse(BaseModel):
    """Response model for deep learning inference"""
    inference_id: str
    model_name: str
    predictions: List[Any]
    confidence_scores: Optional[List[float]] = None
    attention_weights: Optional[Dict[str, Any]] = None
    embeddings: Optional[Dict[str, Any]] = None
    inference_time_ms: float = 0.0
    preprocessing_time_ms: float = 0.0
    postprocessing_time_ms: float = 0.0
    batch_size: int
    gpu_memory_used_mb: float = 0.0
    metadata: Dict[str, Any] = {}
    timestamp: str


class DLHealthResponse(BaseModel):
    """Response model for deep learning service health check"""
    service: str
    status: str
    uptime_seconds: float
    microservice_version: str
    available_frameworks: List[str]
    available_architectures: List[str]
    gpu_available: bool
    gpu_count: int
    gpu_memory_total_mb: float
    gpu_memory_used_mb: float
    trained_models_count: int
    active_training_jobs: int
    metrics: Dict[str, Any]
    system_resources: Dict[str, Any]
    timestamp: str


# API ENDPOINTS

@router.post("/train", response_model=DLModelResponse, status_code=201)
@performance_tracked(operation_name="train_dl_model_endpoint")
async def train_deep_learning_model(
    training_request: DLTrainingRequest,
    background_tasks: BackgroundTasks
) -> DLModelResponse:
    """
    Train deep learning model with FULL CENTRALIZATION
    Enterprise-grade neural network training with comprehensive validation and monitoring
    """
    start_time = time.perf_counter()
    
    try:
        # Update API metrics
        api_metrics["total_requests"] += 1
        api_metrics["model_training_requests"] += 1
        
        # Enhanced validation
        validation_result = Validator.validate_required_fields(
            training_request.dict(), 
            ["task_type", "framework", "architecture", "training_data", "model_config", "training_config", "model_name"]
        )
        
        if not validation_result.is_valid:
            api_metrics["validation_errors"] += 1
            api_metrics["failed_requests"] += 1
            
            error_response = ErrorHandler.handle_error(
                error=ValueError(f"Invalid training request: {validation_result.get_error_messages()}"),
                component="deep_learning_api",
                operation="train_model",
                context={"request_data": training_request.dict()}
            )
            
            raise HTTPException(
                status_code=400,
                detail=f"Validation failed: {validation_result.get_error_messages()}"
            )
        
        # Generate model ID
        model_id = f"dl_model_{int(time.time() * 1000)}"
        
        # Create training task (this would typically queue the training job)
        training_task = {
            "model_id": model_id,
            "model_name": training_request.model_name,
            "task_type": training_request.task_type,
            "framework": training_request.framework,
            "architecture": training_request.architecture,
            "status": TrainingStatus.PENDING.value,
            "created_at": datetime.now().isoformat(),
            "model_config": training_request.model_config,
            "training_config": training_request.training_config,
            "use_gpu": training_request.use_gpu,
            "distributed_training": training_request.distributed_training,
            "metadata": training_request.metadata or {}
        }
        
        # Calculate response time
        response_time = (time.perf_counter() - start_time) * 1000
        
        # Update API metrics
        api_metrics["successful_requests"] += 1
        api_metrics["total_response_time_ms"] += response_time
        if api_metrics["successful_requests"] > 0:
            api_metrics["avg_response_time_ms"] = (
                api_metrics["total_response_time_ms"] / api_metrics["successful_requests"]
            )
        
        # Record performance metrics
        PerformanceManager.record_metric(
            operation="train_dl_model_endpoint",
            duration_ms=response_time,
            success=True,
            metadata={
                "task_type": training_request.task_type,
                "framework": training_request.framework,
                "architecture": training_request.architecture,
                "model_name": training_request.model_name,
                "use_gpu": training_request.use_gpu,
                "microservice": "deep-learning"
            }
        )
        
        # Publish training event
        EventManager.publish_event(
            event_type="dl_model_training_started",
            component="deep_learning_api",
            message=f"Deep learning model training started: {training_request.model_name}",
            data={
                "model_id": model_id,
                "task_type": training_request.task_type,
                "framework": training_request.framework,
                "architecture": training_request.architecture,
                "response_time_ms": response_time,
                "api_endpoint": "/train"
            }
        )
        api_metrics["events_published"] += 1
        
        # Create response
        response = DLModelResponse(
            model_id=model_id,
            model_name=training_request.model_name,
            status=TrainingStatus.PENDING.value,
            task_type=training_request.task_type,
            framework=training_request.framework,
            architecture=training_request.architecture,
            created_at=training_task["created_at"],
            model_config=training_task["model_config"],
            training_config=training_task["training_config"],
            metadata=training_task["metadata"]
        )
        
        api_logger.info(f"✅ Deep learning model training queued: {model_id} ({response_time:.2f}ms)")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        response_time = (time.perf_counter() - start_time) * 1000
        api_metrics["failed_requests"] += 1
        
        error_response = ErrorHandler.handle_error(
            error=e,
            component="deep_learning_api",
            operation="train_model",
            context={"request_data": training_request.dict()}
        )
        
        api_logger.error(f"❌ Failed to start deep learning model training: {error_response}")
        raise HTTPException(status_code=500, detail=f"Failed to start training: {str(e)}")


@router.post("/inference", response_model=DLInferenceResponse)
@performance_tracked(operation_name="dl_inference_endpoint")
async def run_deep_learning_inference(
    inference_request: DLInferenceRequest
) -> DLInferenceResponse:
    """
    Run deep learning inference with FULL CENTRALIZATION
    Enterprise-grade neural network inference with comprehensive monitoring
    """
    start_time = time.perf_counter()
    
    try:
        # Update API metrics
        api_metrics["total_requests"] += 1
        api_metrics["inference_requests"] += 1
        
        # Enhanced validation
        validation_result = Validator.validate_required_fields(
            inference_request.dict(), 
            ["model_name", "input_data"]
        )
        
        if not validation_result.is_valid:
            api_metrics["validation_errors"] += 1
            api_metrics["failed_requests"] += 1
            
            raise HTTPException(
                status_code=400,
                detail=f"Validation failed: {validation_result.get_error_messages()}"
            )
        
        # Generate inference ID
        inference_id = f"dl_inf_{int(time.time() * 1000)}"
        
        # Mock inference results (in real implementation, this would load and use the trained model)
        mock_predictions = [
            {"class": "bullish", "probability": 0.87},
            {"class": "bearish", "probability": 0.13}
        ] if inference_request.input_data else []
        
        mock_confidence_scores = [0.94, 0.89, 0.92] if mock_predictions else []
        mock_attention_weights = {"layer_1": [0.3, 0.7], "layer_2": [0.6, 0.4]} if inference_request.return_attention_weights else None
        mock_embeddings = {"hidden_state": [0.1, 0.2, 0.3]} if inference_request.return_embeddings else None
        
        # Calculate response time
        response_time = (time.perf_counter() - start_time) * 1000
        
        # Update API metrics
        api_metrics["successful_requests"] += 1
        api_metrics["total_response_time_ms"] += response_time
        if api_metrics["successful_requests"] > 0:
            api_metrics["avg_response_time_ms"] = (
                api_metrics["total_response_time_ms"] / api_metrics["successful_requests"]
            )
        
        # Create response
        response = DLInferenceResponse(
            inference_id=inference_id,
            model_name=inference_request.model_name,
            predictions=mock_predictions,
            confidence_scores=mock_confidence_scores,
            attention_weights=mock_attention_weights,
            embeddings=mock_embeddings,
            inference_time_ms=response_time * 0.8,  # Mock inference time
            preprocessing_time_ms=response_time * 0.1,  # Mock preprocessing time
            postprocessing_time_ms=response_time * 0.1,  # Mock postprocessing time
            batch_size=inference_request.batch_size,
            gpu_memory_used_mb=2048.5,  # Mock GPU memory usage
            metadata=inference_request.metadata or {},
            timestamp=datetime.now().isoformat()
        )
        
        api_logger.info(f"🧠 Deep learning inference completed: {inference_id} ({response_time:.2f}ms)")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        response_time = (time.perf_counter() - start_time) * 1000
        api_metrics["failed_requests"] += 1
        
        error_response = ErrorHandler.handle_error(
            error=e,
            component="deep_learning_api",
            operation="inference",
            context={"request_data": inference_request.dict()}
        )
        
        api_logger.error(f"❌ Failed to run deep learning inference: {error_response}")
        raise HTTPException(status_code=500, detail=f"Failed to run inference: {str(e)}")


@router.post("/fine-tune", response_model=DLModelResponse, status_code=201)
@performance_tracked(operation_name="fine_tune_dl_model_endpoint")
async def fine_tune_model(
    fine_tuning_request: FineTuningRequest,
    background_tasks: BackgroundTasks
) -> DLModelResponse:
    """
    Fine-tune deep learning model with FULL CENTRALIZATION
    Enterprise-grade model fine-tuning with comprehensive validation and monitoring
    """
    start_time = time.perf_counter()
    
    try:
        # Update API metrics
        api_metrics["total_requests"] += 1
        api_metrics["fine_tuning_requests"] += 1
        
        # Enhanced validation
        validation_result = Validator.validate_required_fields(
            fine_tuning_request.dict(), 
            ["base_model_name", "task_type", "fine_tuning_data", "fine_tuning_config", "target_model_name"]
        )
        
        if not validation_result.is_valid:
            api_metrics["validation_errors"] += 1
            api_metrics["failed_requests"] += 1
            
            raise HTTPException(
                status_code=400,
                detail=f"Validation failed: {validation_result.get_error_messages()}"
            )
        
        # Generate model ID
        model_id = f"dl_ft_model_{int(time.time() * 1000)}"
        
        # Create fine-tuning task
        fine_tuning_task = {
            "model_id": model_id,
            "model_name": fine_tuning_request.target_model_name,
            "base_model_name": fine_tuning_request.base_model_name,
            "task_type": fine_tuning_request.task_type,
            "status": TrainingStatus.FINE_TUNING.value,
            "created_at": datetime.now().isoformat(),
            "fine_tuning_config": fine_tuning_request.fine_tuning_config,
            "freeze_layers": fine_tuning_request.freeze_layers or [],
            "use_lora": fine_tuning_request.use_lora,
            "metadata": fine_tuning_request.metadata or {}
        }
        
        # Calculate response time
        response_time = (time.perf_counter() - start_time) * 1000
        
        # Update API metrics
        api_metrics["successful_requests"] += 1
        api_metrics["total_response_time_ms"] += response_time
        if api_metrics["successful_requests"] > 0:
            api_metrics["avg_response_time_ms"] = (
                api_metrics["total_response_time_ms"] / api_metrics["successful_requests"]
            )
        
        # Create response
        response = DLModelResponse(
            model_id=model_id,
            model_name=fine_tuning_request.target_model_name,
            status=TrainingStatus.FINE_TUNING.value,
            task_type=fine_tuning_request.task_type,
            framework="transformers",  # Default for fine-tuning
            architecture="transformer",  # Default for fine-tuning
            created_at=fine_tuning_task["created_at"],
            model_config={"base_model": fine_tuning_request.base_model_name},
            training_config=fine_tuning_task["fine_tuning_config"],
            metadata=fine_tuning_task["metadata"]
        )
        
        api_logger.info(f"🔧 Model fine-tuning queued: {model_id} ({response_time:.2f}ms)")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        response_time = (time.perf_counter() - start_time) * 1000
        api_metrics["failed_requests"] += 1
        
        error_response = ErrorHandler.handle_error(
            error=e,
            component="deep_learning_api",
            operation="fine_tune",
            context={"request_data": fine_tuning_request.dict()}
        )
        
        api_logger.error(f"❌ Failed to start model fine-tuning: {error_response}")
        raise HTTPException(status_code=500, detail=f"Failed to start fine-tuning: {str(e)}")


@router.get("/models", response_model=List[DLModelResponse])
@performance_tracked(operation_name="list_dl_models_endpoint")
async def list_deep_learning_models(
    status: Optional[str] = Query(None, description="Filter by model status"),
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    framework: Optional[str] = Query(None, description="Filter by framework"),
    limit: int = Query(default=50, ge=1, le=1000, description="Maximum number of models to return")
) -> List[DLModelResponse]:
    """
    List deep learning models with filtering with FULL CENTRALIZATION
    Enterprise-grade model listing with comprehensive filtering and monitoring
    """
    start_time = time.perf_counter()
    
    try:
        # Update API metrics
        api_metrics["total_requests"] += 1
        
        # Mock models list (in real implementation, this would query the model registry)
        mock_models = [
            DLModelResponse(
                model_id="dl_model_1",
                model_name="trading_lstm_forecaster",
                status=TrainingStatus.COMPLETED.value,
                task_type=DLTaskType.TIME_SERIES_FORECASTING.value,
                framework=DLFramework.PYTORCH.value,
                architecture=NetworkArchitecture.LSTM.value,
                created_at=datetime.now().isoformat(),
                training_completed_at=datetime.now().isoformat(),
                training_time_ms=120000.0,
                training_metrics={"loss": 0.025, "val_loss": 0.031},
                validation_metrics={"mae": 0.15, "rmse": 0.22},
                model_config={"hidden_size": 128, "num_layers": 3},
                training_config={"learning_rate": 0.001, "batch_size": 32, "epochs": 100},
                model_size_mb=45.2,
                parameters_count=2500000,
                gpu_memory_used_mb=4096.0,
                metadata={"version": "1.0", "author": "dl_team"}
            )
        ]
        
        # Apply filters
        filtered_models = []
        for model in mock_models:
            if status and model.status != status:
                continue
            if task_type and model.task_type != task_type:
                continue
            if framework and model.framework != framework:
                continue
            filtered_models.append(model)
        
        # Limit results
        filtered_models = filtered_models[:limit]
        
        # Calculate response time
        response_time = (time.perf_counter() - start_time) * 1000
        api_metrics["successful_requests"] += 1
        
        api_logger.info(f"📋 Listed {len(filtered_models)} deep learning models ({response_time:.2f}ms)")
        return filtered_models
        
    except Exception as e:
        response_time = (time.perf_counter() - start_time) * 1000
        api_metrics["failed_requests"] += 1
        
        error_response = ErrorHandler.handle_error(
            error=e,
            component="deep_learning_api",
            operation="list_models",
            context={"status": status, "task_type": task_type, "framework": framework, "limit": limit}
        )
        
        api_logger.error(f"❌ Failed to list deep learning models: {error_response}")
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")


@router.get("/health", response_model=DLHealthResponse)
@performance_tracked(operation_name="dl_health_check_endpoint")
async def health_check() -> DLHealthResponse:
    """
    Health check for deep learning microservice with FULL CENTRALIZATION
    Enterprise-grade health monitoring with comprehensive metrics
    """
    start_time = time.perf_counter()
    
    try:
        # Update API metrics
        api_metrics["total_requests"] += 1
        api_metrics["health_checks"] += 1
        
        # Calculate response time
        response_time = (time.perf_counter() - start_time) * 1000
        api_metrics["successful_requests"] += 1
        
        # Create health response
        response = DLHealthResponse(
            service="deep-learning",
            status="healthy",
            uptime_seconds=time.time() - api_metrics.get("startup_time", time.time()),
            microservice_version="2.0.0",
            available_frameworks=[framework.value for framework in DLFramework],
            available_architectures=[arch.value for arch in NetworkArchitecture],
            gpu_available=True,  # Mock GPU availability
            gpu_count=2,  # Mock GPU count
            gpu_memory_total_mb=16384.0,  # Mock total GPU memory
            gpu_memory_used_mb=4096.0,  # Mock used GPU memory
            trained_models_count=1,  # Mock count
            active_training_jobs=0,  # Mock count
            metrics=api_metrics.copy(),
            system_resources={
                "cpu_usage": 35.8,
                "memory_usage": 65.4,
                "disk_usage": 18.7,
                "gpu_temperature": 72.5,
                "gpu_utilization": 45.2
            },
            timestamp=datetime.now().isoformat()
        )
        
        api_logger.debug(f"✅ Deep learning health check completed ({response_time:.2f}ms)")
        return response
        
    except Exception as e:
        response_time = (time.perf_counter() - start_time) * 1000
        api_metrics["failed_requests"] += 1
        
        error_response = ErrorHandler.handle_error(
            error=e,
            component="deep_learning_api",
            operation="health_check",
            context={}
        )
        
        api_logger.error(f"❌ Deep learning health check failed: {error_response}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/frameworks", response_model=Dict[str, List[str]])
@performance_tracked(operation_name="get_dl_frameworks_endpoint")
async def get_available_frameworks() -> Dict[str, List[str]]:
    """
    Get available deep learning frameworks and architectures with FULL CENTRALIZATION
    Enterprise-grade framework discovery with comprehensive information
    """
    start_time = time.perf_counter()
    
    try:
        # Update API metrics
        api_metrics["total_requests"] += 1
        
        # Calculate response time
        response_time = (time.perf_counter() - start_time) * 1000
        api_metrics["successful_requests"] += 1
        
        # Create frameworks response
        response = {
            "task_types": [task_type.value for task_type in DLTaskType],
            "frameworks": [framework.value for framework in DLFramework],
            "architectures": [arch.value for arch in NetworkArchitecture],
            "training_statuses": [status.value for status in TrainingStatus],
            "supported_tasks": {
                "computer_vision": ["image_classification", "object_detection", "segmentation"],
                "nlp": ["sentiment_analysis", "text_classification", "language_modeling"],
                "time_series": ["forecasting", "anomaly_detection", "trend_analysis"],
                "generative": ["text_generation", "image_generation", "data_synthesis"]
            },
            "optimization_techniques": [
                "adam", "sgd", "adagrad", "rmsprop", "learning_rate_scheduling",
                "gradient_clipping", "weight_decay", "dropout", "batch_normalization"
            ]
        }
        
        api_logger.debug(f"🧠 Deep learning frameworks list retrieved ({response_time:.2f}ms)")
        return response
        
    except Exception as e:
        response_time = (time.perf_counter() - start_time) * 1000
        api_metrics["failed_requests"] += 1
        
        error_response = ErrorHandler.handle_error(
            error=e,
            component="deep_learning_api",
            operation="get_frameworks",
            context={}
        )
        
        api_logger.error(f"❌ Failed to get deep learning frameworks: {error_response}")
        raise HTTPException(status_code=500, detail=f"Failed to get frameworks: {str(e)}")


# STARTUP EVENT

@router.on_event("startup")
async def startup_event():
    """Startup event for deep learning API"""
    try:
        # Initialize startup time
        api_metrics["startup_time"] = time.time()
        
        # Publish API startup event
        EventManager.publish_event(
            event_type="deep_learning_api_startup",
            component="deep_learning_api",
            message="Deep learning API microservice started",
            data={
                "api_version": "2.0.0",
                "microservice": "deep-learning",
                "startup_timestamp": time.time(),
                "supported_frameworks": [framework.value for framework in DLFramework],
                "supported_architectures": [arch.value for arch in NetworkArchitecture]
            }
        )
        api_metrics["events_published"] += 1
        
        api_logger.info("🚀 Deep Learning API microservice started successfully")
        
    except Exception as e:
        error_response = ErrorHandler.handle_error(
            error=e,
            component="deep_learning_api",
            operation="startup",
            context={}
        )
        api_logger.error(f"❌ Failed to start deep learning API: {error_response}")


# SHUTDOWN EVENT

@router.on_event("shutdown")
async def shutdown_event():
    """Shutdown event for deep learning API"""
    try:
        # Publish API shutdown event
        EventManager.publish_event(
            event_type="deep_learning_api_shutdown",
            component="deep_learning_api",
            message="Deep learning API microservice shutting down",
            data={
                "final_metrics": api_metrics.copy(),
                "shutdown_timestamp": time.time()
            }
        )
        
        api_logger.info("🛑 Deep Learning API microservice shutdown complete")
        
    except Exception as e:
        api_logger.error(f"❌ Error during deep learning API shutdown: {str(e)}")