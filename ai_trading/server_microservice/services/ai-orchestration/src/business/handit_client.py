"""
🤖 Handit AI Client - Microservice Implementation
Enterprise-grade domain-specific AI tasks and specialized model coordination with comprehensive infrastructure integration

CENTRALIZED INFRASTRUCTURE:
- Performance tracking untuk AI orchestration operations
- Centralized error handling untuk AI task management  
- Event publishing untuk AI workflow lifecycle monitoring
- Enhanced logging dengan AI-specific configuration
- Comprehensive validation untuk AI task data
- Advanced metrics tracking untuk AI performance optimization
"""

import os
import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import deque, OrderedDict
import weakref

# CENTRALIZED INFRASTRUCTURE - VIA BASE MICROSERVICE
from .base_microservice import AIOrchestrationBaseMicroservice

# Handit AI performance metrics for microservice
ai_orchestration_handit_metrics = {
    "total_tasks_created": 0,
    "successful_tasks": 0,
    "failed_tasks": 0,
    "total_processing_time_ms": 0,
    "avg_task_duration_ms": 0,
    "events_published": 0,
    "validation_errors": 0,
    "concurrent_tasks_peak": 0,
    "microservice_uptime": time.time(),
    "total_api_calls": 0
}

try:
    # Try to import OpenAI as fallback for AI functionality
    import openai
    from openai import AsyncOpenAI
    AI_ORCHESTRATION_HANDIT_AVAILABLE = True
    AI_FALLBACK_TYPE = "openai"
except ImportError:
    try:
        # Try requests for generic HTTP API calls
        import requests
        import aiohttp
        AI_ORCHESTRATION_HANDIT_AVAILABLE = True
        AI_FALLBACK_TYPE = "http"
    except ImportError:
        AI_ORCHESTRATION_HANDIT_AVAILABLE = False
        AI_FALLBACK_TYPE = "mock"


class TaskType(Enum):
    """Types of specialized AI tasks - MICROSERVICE ENHANCED"""
    FINANCIAL_ANALYSIS = "financial_analysis"
    TRADING_SIGNALS = "trading_signals"
    RISK_ASSESSMENT = "risk_assessment"
    PATTERN_RECOGNITION = "pattern_recognition"
    MARKET_PREDICTION = "market_prediction"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    DOCUMENT_ANALYSIS = "document_analysis"
    TIME_SERIES_FORECASTING = "time_series_forecasting"
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"
    MARKET_REGIME_DETECTION = "market_regime_detection"
    ANOMALY_DETECTION = "anomaly_detection"
    CORRELATION_ANALYSIS = "correlation_analysis"


class ModelSpecialty(Enum):
    """Model specializations - MICROSERVICE ENHANCED"""
    FOREX_SPECIALIST = "forex_specialist"
    COMMODITIES_SPECIALIST = "commodities_specialist"
    CRYPTO_SPECIALIST = "crypto_specialist"
    STOCK_ANALYST = "stock_analyst"
    ECONOMIC_ANALYST = "economic_analyst"
    TECHNICAL_ANALYST = "technical_analyst"
    FUNDAMENTAL_ANALYST = "fundamental_analyst"
    RISK_ANALYST = "risk_analyst"
    QUANTITATIVE_ANALYST = "quantitative_analyst"
    BEHAVIORAL_ANALYST = "behavioral_analyst"
    MACRO_ECONOMIST = "macro_economist"
    DERIVATIVES_SPECIALIST = "derivatives_specialist"


class TaskStatus(Enum):
    """Status of AI tasks - MICROSERVICE ENHANCED"""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    RETRYING = "retrying"


class TaskPriority(Enum):
    """Task priority levels - MICROSERVICE ENHANCED"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


@dataclass
class AIOrchestrationHanditTask:
    """
    Handit AI task definition - MICROSERVICE ENHANCED WITH FULL CENTRALIZATION
    Enterprise-grade AI task with comprehensive tracking and monitoring for microservice architecture
    """
    id: str
    task_type: TaskType
    specialty: ModelSpecialty
    input_data: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    timeout: int = 30
    retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Enhanced tracking fields for microservice
    status: TaskStatus = TaskStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    processing_time_ms: float = 0.0
    retry_count: int = 0
    last_error: Optional[str] = None
    microservice_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post initialization setup with microservice centralization"""
        self.microservice_metadata.update({
            "creation_method": "handit_task_microservice",
            "microservice": "ai-orchestration", 
            "centralized_infrastructure": True,
            "creation_timestamp": time.time(),
            "environment": os.getenv("MICROSERVICE_ENVIRONMENT", "development")
        })
    
    # Note: Performance tracking moved to service level
    def start_processing(self):
        """Mark task as started with microservice centralized tracking"""
        try:
            self.status = TaskStatus.PROCESSING
            self.started_at = datetime.now().isoformat()
            
            # Publish task start event for microservice
            from .base_microservice import EventManager
            EventManager.publish_event(
                event_type="handit_microservice_task_started",
                component="ai_orchestration_microservice",
                message=f"Handit AI microservice task started: {self.task_type.value}",
                data={
                    "task_id": self.id,
                    "task_type": self.task_type.value,
                    "specialty": self.specialty.value,
                    "priority": self.priority.value,
                    "microservice": "ai-orchestration"
                }
            )
            ai_orchestration_handit_metrics["events_published"] += 1
            
        except Exception as e:
            from .base_microservice import ErrorHandler
            error_response = ErrorHandler.handle_error(
                error=e,
                component="handit_ai_microservice",
                operation="start_processing",
                context={"task_id": self.id}
            )
            # Note: handit_logger not defined in scope, using regular logger
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to start microservice task processing: {error_response}")
    
    # Note: Performance tracking moved to service level
    def complete_processing(self, processing_time_ms: float):
        """Mark task as completed with microservice centralized tracking"""
        try:
            self.status = TaskStatus.COMPLETED
            self.completed_at = datetime.now().isoformat()
            self.processing_time_ms = processing_time_ms
            
            # Update metrics
            ai_orchestration_handit_metrics["successful_tasks"] += 1
            ai_orchestration_handit_metrics["total_processing_time_ms"] += processing_time_ms
            
            # Calculate average for microservice
            if ai_orchestration_handit_metrics["successful_tasks"] > 0:
                ai_orchestration_handit_metrics["avg_task_duration_ms"] = (
                    ai_orchestration_handit_metrics["total_processing_time_ms"] / ai_orchestration_handit_metrics["successful_tasks"]
                )
            
            # Publish task completion event for microservice
            from .base_microservice import EventManager
            EventManager.publish_event(
                event_type="handit_microservice_task_completed",
                component="ai_orchestration_microservice",
                message=f"Handit AI microservice task completed: {self.task_type.value}",
                data={
                    "task_id": self.id,
                    "processing_time_ms": processing_time_ms,
                    "specialty": self.specialty.value,
                    "retry_count": self.retry_count,
                    "microservice": "ai-orchestration"
                }
            )
            ai_orchestration_handit_metrics["events_published"] += 1
            
        except Exception as e:
            from .base_microservice import ErrorHandler
            error_response = ErrorHandler.handle_error(
                error=e,
                component="handit_ai_microservice",
                operation="complete_processing",
                context={"task_id": self.id}
            )
            # Note: handit_logger not defined in scope, using regular logger
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to complete microservice task processing: {error_response}")


@dataclass
class AIOrchestrationHanditResponse:
    """
    Response from Handit AI - MICROSERVICE ENHANCED WITH FULL CENTRALIZATION
    Enterprise-grade AI response with comprehensive tracking and validation for microservice architecture
    """
    task_id: str
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None
    confidence: float = 0.0
    model_used: Optional[str] = None
    processing_time_ms: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Enhanced tracking fields for microservice
    response_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    validation_score: float = 0.0
    quality_metrics: Dict[str, float] = field(default_factory=dict)
    microservice_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post initialization setup with microservice centralization"""
        self.microservice_metadata.update({
            "response_method": "handit_response_microservice",
            "microservice": "ai-orchestration",
            "centralized_infrastructure": True,
            "response_timestamp": time.time(),
            "environment": os.getenv("MICROSERVICE_ENVIRONMENT", "development")
        })
        
        # Calculate validation score based on response quality
        self._calculate_validation_score()
    
    def _calculate_validation_score(self):
        """Calculate validation score based on response quality for microservice"""
        try:
            score = 0.0
            
            # Base score from confidence
            if self.confidence > 0:
                score += min(self.confidence * 0.4, 0.4)
            
            # Score from result completeness
            if self.result:
                score += 0.3
                if len(self.result) > 3:  # Rich result
                    score += 0.1
            
            # Score from processing time (optimized for microservice)
            if 0 < self.processing_time_ms < 500:  # Under 500ms for microservice
                score += 0.2
            elif 500 <= self.processing_time_ms < 2000:  # 500ms-2s
                score += 0.1
            
            # Penalty for errors
            if self.error:
                score -= 0.2
            
            self.validation_score = max(0.0, min(1.0, score))
            
        except Exception as e:
            # Note: handit_logger not defined in scope, using regular logger
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to calculate validation score for microservice: {str(e)}")
            self.validation_score = 0.0


class AIOrchestrationHanditClient(AIOrchestrationBaseMicroservice):
    """
    Handit AI Client for Microservice - ENHANCED WITH FULL CENTRALIZATION
    Enterprise-grade domain-specific AI operations for microservice architecture
    
    CENTRALIZED INFRASTRUCTURE:
    - Performance tracking untuk AI orchestration operations  
    - Centralized error handling untuk AI task management
    - Event publishing untuk AI workflow lifecycle monitoring
    - Enhanced logging dengan AI-specific configuration
    - Comprehensive validation untuk AI task data
    - Advanced metrics tracking untuk AI performance optimization
    """
    
    # Performance tracking is handled by base microservice
    def __init__(self):
        """Initialize Handit AI Microservice dengan FULL CENTRALIZATION"""
        try:
            # Initialize base microservice infrastructure
            super().__init__(service_name="ai-orchestration", component_name="handit_client")
            
            # Component-specific initialization
            self.client = None
            self.ai_mode = "mock"  # Default to mock mode
            self.models: Dict[ModelSpecialty, str] = {}
            self.task_queue: List[AIOrchestrationHanditTask] = []
            self.active_tasks: Dict[str, AIOrchestrationHanditTask] = {}
            
            # Memory-optimized completed tasks with LRU cache (max 1000 entries)
            self.completed_tasks: OrderedDict[str, AIOrchestrationHanditResponse] = OrderedDict()
            self._max_completed_tasks = 1000
            
            # Component-specific monitoring with memory bounds
            self.task_history: deque = deque(maxlen=500)  # Bounded history
            self.performance_analytics: Dict[str, Any] = {}
            self.model_usage_stats: Dict[str, int] = {}
            
            # Task execution cache for duplicate requests
            self._task_cache: OrderedDict[str, AIOrchestrationHanditResponse] = OrderedDict()
            self._max_cache_size = 100
            
            # Setup models and client
            self._setup_models()
            self._setup_microservice_client()
            
            # Publish component initialization event
            self.publish_event(
                event_type="handit_initialized",
                message="Handit AI component initialized with full centralization",
                data={
                    "handit_available": AI_ORCHESTRATION_HANDIT_AVAILABLE,
                    "models_count": len(self.models),
                    "microservice_version": "2.0.0"
                }
            )
            ai_orchestration_handit_metrics["events_published"] += 1
            
            if not AI_ORCHESTRATION_HANDIT_AVAILABLE:
                self.logger.warning("Handit AI SDK not available. Using mock implementation for microservice.")
            
            self.logger.info(f"✅ Handit AI component initialized with centralization infrastructure")
            
        except Exception as e:
            error_response = self.handle_error(e, "initialize", {"component": "handit_client"})
            self.logger.error(f"Failed to initialize Handit AI microservice: {error_response}")
            raise
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for Handit AI component"""
        # Use service-specific centralized configuration
        handit_config = self.config_manager.get('handit', {})
        
        return {
            "api_key": handit_config.get("api_key", ""),
            "base_url": handit_config.get("base_url", "https://api.handit.ai"),
            "enabled": handit_config.get("enabled", True),
            "timeout": handit_config.get("timeout_seconds", 30),
            "max_concurrent": handit_config.get("max_concurrent_requests", 10),
            "health_check_interval": self.config_manager.get('monitoring.health_check_interval_seconds', 30)
        }
    
    def _perform_health_checks(self) -> Dict[str, Any]:
        """Perform Handit AI specific health checks"""
        try:
            # Use inherited validation from base microservice
            base_url = self.config.get("base_url", "")
            if base_url:
                # Basic URL validation - can be enhanced later
                if not base_url.startswith(('http://', 'https://')):
                    ai_orchestration_handit_metrics["validation_errors"] += 1
                    self.logger.warning(f"Invalid base URL in config: {base_url}")
                    return {"healthy": False, "error": "Invalid base URL configuration"}
            
            return {
                "healthy": True,
                "handit_available": AI_ORCHESTRATION_HANDIT_AVAILABLE,
                "client_initialized": self.client is not None,
                "models_count": len(self.models),
                "active_tasks": len(self.active_tasks),
                "queued_tasks": len(self.task_queue),
                "completed_tasks": len(self.completed_tasks)
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    # Performance tracking is handled by base microservice
    def _setup_models(self):
        """Setup available Handit AI models untuk microservice dengan FULL CENTRALIZATION"""
        try:
            # Enhanced model mapping for microservice
            self.models = {
                ModelSpecialty.FOREX_SPECIALIST: "handit-forex-microservice-v2",
                ModelSpecialty.COMMODITIES_SPECIALIST: "handit-commodities-microservice-v2", 
                ModelSpecialty.CRYPTO_SPECIALIST: "handit-crypto-microservice-v2",
                ModelSpecialty.STOCK_ANALYST: "handit-stocks-microservice-v2",
                ModelSpecialty.ECONOMIC_ANALYST: "handit-economics-microservice-v2",
                ModelSpecialty.TECHNICAL_ANALYST: "handit-technical-microservice-v2",
                ModelSpecialty.FUNDAMENTAL_ANALYST: "handit-fundamental-microservice-v2",
                ModelSpecialty.RISK_ANALYST: "handit-risk-microservice-v2",
                ModelSpecialty.QUANTITATIVE_ANALYST: "handit-quant-microservice-v2",
                ModelSpecialty.BEHAVIORAL_ANALYST: "handit-behavioral-microservice-v2",
                ModelSpecialty.MACRO_ECONOMIST: "handit-macro-microservice-v2",
                ModelSpecialty.DERIVATIVES_SPECIALIST: "handit-derivatives-microservice-v2"
            }
            
            # Initialize model usage statistics for microservice
            for specialty in self.models.keys():
                self.model_usage_stats[specialty.value] = 0
            
            # Publish models setup event for microservice
            self.publish_event(
                event_type="models_setup",
                message=f"Setup {len(self.models)} Handit AI model specialties",
                data={
                    "models_count": len(self.models),
                    "specialties": [s.value for s in self.models.keys()]
                }
            )
            ai_orchestration_handit_metrics["events_published"] += 1
            
            self.logger.info(f"✅ Setup {len(self.models)} Handit AI microservice model specialties")
            
        except Exception as e:
            error_response = self.handle_error(e, "setup_models", {})
            self.logger.error(f"Failed to setup microservice models: {error_response}")
            # Initialize empty models dict as fallback
            self.models = {}
            self.model_usage_stats = {}
    
    # Performance tracking is handled by base microservice
    def _setup_microservice_client(self):
        """Setup AI client with multiple fallback options"""
        try:
            if not AI_ORCHESTRATION_HANDIT_AVAILABLE:
                self.logger.warning("⚠️ AI services not available, using mock implementation")
                return
            
            if not self.enabled:
                self.logger.info("🔅 AI services disabled via configuration")
                return
            
            # Initialize based on available AI service
            if AI_FALLBACK_TYPE == "openai":
                self._setup_openai_client()
            elif AI_FALLBACK_TYPE == "http":
                self._setup_http_client()
            else:
                self.logger.warning("🔄 Using mock implementation")
            
            self.logger.info(f"✅ AI client setup complete (mode: {AI_FALLBACK_TYPE})")
            
        except Exception as e:
            error_response = self.handle_error(e, "setup_client", {})
            self.logger.error(f"❌ Failed to setup AI client: {error_response}")
    
    def _setup_openai_client(self):
        """Setup OpenAI client as AI fallback"""
        try:
            api_key = self.config.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
            if api_key:
                self.client = AsyncOpenAI(api_key=api_key)
                self.ai_mode = "openai"
                self.logger.info("🤖 OpenAI client initialized successfully")
            else:
                self.logger.warning("⚠️ OpenAI API key not found, using mock mode")
                self.ai_mode = "mock"
        except Exception as e:
            self.logger.error(f"Failed to setup OpenAI client: {e}")
            self.ai_mode = "mock"
    
    def _setup_http_client(self):
        """Setup HTTP client for generic API calls"""
        try:
            import aiohttp
            self.client = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.get("timeout_seconds", 30))
            )
            self.ai_mode = "http"
            self.logger.info("🌐 HTTP client initialized for generic AI API calls")
        except Exception as e:
            self.logger.error(f"Failed to setup HTTP client: {e}")
            self.ai_mode = "mock"
    
    async def _execute_ai_task(
        self,
        task_id: str,
        task_type: str,
        specialty: str,
        input_data: Dict[str, Any],
        start_time: float
    ) -> Dict[str, Any]:
        """Execute AI task with appropriate backend"""
        try:
            if self.ai_mode == "openai" and self.client:
                return await self._execute_openai_task(task_id, task_type, specialty, input_data, start_time)
            elif self.ai_mode == "http" and self.client:
                return await self._execute_http_task(task_id, task_type, specialty, input_data, start_time)
            else:
                return await self._execute_mock_task(task_id, task_type, specialty, input_data, start_time)
        except Exception as e:
            self.logger.error(f"AI task execution failed: {e}")
            return await self._execute_mock_task(task_id, task_type, specialty, input_data, start_time)
    
    async def _execute_openai_task(
        self,
        task_id: str,
        task_type: str,
        specialty: str,
        input_data: Dict[str, Any],
        start_time: float
    ) -> Dict[str, Any]:
        """Execute task using OpenAI API"""
        try:
            # Prepare prompt based on task type and specialty
            prompt = self._build_ai_prompt(task_type, specialty, input_data)
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"You are a specialized AI assistant for {specialty} tasks."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            execution_time = (time.perf_counter() - start_time) * 1000
            
            return {
                "task_id": task_id,
                "status": "completed",
                "result": {
                    "analysis": response.choices[0].message.content,
                    "confidence": 0.85,
                    "model_used": "gpt-3.5-turbo",
                    "processing_time_ms": execution_time,
                    "tokens_used": response.usage.total_tokens if response.usage else 0
                },
                "execution_time_ms": execution_time,
                "success": True
            }
        except Exception as e:
            self.logger.error(f"OpenAI task execution failed: {e}")
            return await self._execute_mock_task(task_id, task_type, specialty, input_data, start_time)
    
    async def _execute_http_task(
        self,
        task_id: str,
        task_type: str,
        specialty: str,
        input_data: Dict[str, Any],
        start_time: float
    ) -> Dict[str, Any]:
        """Execute task using HTTP API call"""
        try:
            # Prepare API payload
            payload = {
                "task_type": task_type,
                "specialty": specialty,
                "input_data": input_data,
                "task_id": task_id
            }
            
            # Make HTTP request to AI service
            base_url = self.config.get("base_url", "https://api.handit.ai")
            api_key = self.config.get("api_key", "")
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}" if api_key else ""
            }
            
            async with self.client.post(
                f"{base_url}/v1/tasks",
                json=payload,
                headers=headers
            ) as response:
                if response.status == 200:
                    result_data = await response.json()
                    execution_time = (time.perf_counter() - start_time) * 1000
                    
                    return {
                        "task_id": task_id,
                        "status": "completed",
                        "result": result_data.get("result", {}),
                        "execution_time_ms": execution_time,
                        "success": True
                    }
                else:
                    self.logger.warning(f"HTTP API call failed: {response.status}")
                    return await self._execute_mock_task(task_id, task_type, specialty, input_data, start_time)
        except Exception as e:
            self.logger.error(f"HTTP task execution failed: {e}")
            return await self._execute_mock_task(task_id, task_type, specialty, input_data, start_time)
    
    async def _execute_mock_task(
        self,
        task_id: str,
        task_type: str,
        specialty: str,
        input_data: Dict[str, Any],
        start_time: float
    ) -> Dict[str, Any]:
        """Execute mock task for testing/fallback"""
        execution_time = (time.perf_counter() - start_time) * 1000
        
        # Simulate processing time
        await asyncio.sleep(0.1)
        
        return {
            "task_id": task_id,
            "status": "completed",
            "result": {
                "analysis": f"Mock AI analysis for {task_type} using {specialty} specialty",
                "confidence": 0.85,
                "model_used": f"mock-{specialty}-v2",
                "processing_time_ms": execution_time,
                "mock": True
            },
            "execution_time_ms": execution_time,
            "success": True
        }
    
    def _build_ai_prompt(self, task_type: str, specialty: str, input_data: Dict[str, Any]) -> str:
        """Build appropriate prompt for AI task"""
        prompt_templates = {
            "analysis": f"Perform a detailed {specialty} analysis of the following data: {json.dumps(input_data)}",
            "comprehensive_analysis": f"Conduct a comprehensive {specialty} analysis including multiple perspectives and detailed insights for: {json.dumps(input_data)}",
            "trading_signal_generation": f"Generate trading signals based on {specialty} analysis of: {json.dumps(input_data)}",
            "risk_assessment": f"Assess risks from a {specialty} perspective for: {json.dumps(input_data)}",
            "market_sentiment": f"Analyze market sentiment using {specialty} techniques for: {json.dumps(input_data)}"
        }
        
        return prompt_templates.get(task_type, f"Analyze the following {specialty} data: {json.dumps(input_data)}")
    
    def _generate_cache_key(self, task_type: TaskType, specialty: ModelSpecialty, input_data: Dict[str, Any]) -> str:
        """Generate cache key for task deduplication"""
        import hashlib
        # Create deterministic hash from task parameters
        key_data = f"{task_type.value}:{specialty.value}:{json.dumps(input_data, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _cleanup_completed_tasks(self):
        """Remove old completed tasks to prevent memory bloat"""
        while len(self.completed_tasks) > self._max_completed_tasks:
            self.completed_tasks.popitem(last=False)  # Remove oldest
    
    def _cleanup_task_cache(self):
        """Remove old cached tasks"""
        while len(self._task_cache) > self._max_cache_size:
            self._task_cache.popitem(last=False)  # Remove oldest
    
    # Performance tracking is handled by base microservice
    async def create_task(
        self,
        task_type: TaskType,
        specialty: ModelSpecialty,
        input_data: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: int = 30,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new Handit AI task in microservice dengan FULL CENTRALIZATION"""
        start_time = time.perf_counter()
        
        try:
            # Check task cache for duplicate requests (performance optimization)
            cache_key = self._generate_cache_key(task_type, specialty, input_data)
            if cache_key in self._task_cache:
                cached_response = self._task_cache[cache_key]
                self.logger.info(f"🚀 Returning cached task result for: {task_type.value}")
                return cached_response.task_id
            
            # Generate task ID for microservice
            task_id = f"handit_ms_{task_type.value}_{len(self.active_tasks)}_{int(time.time() * 1000)}"
            
            # Enhanced validation for microservice
            if not self.validate_data(
                {"task_type": task_type.value, "specialty": specialty.value}, 
                ["task_type", "specialty"]
            ):
                ai_orchestration_handit_metrics["validation_errors"] += 1
                raise ValueError(f"Invalid task parameters for microservice")
            
            # Create enhanced task for microservice
            task = AIOrchestrationHanditTask(
                id=task_id,
                task_type=task_type,
                specialty=specialty,
                input_data=input_data,
                priority=priority,
                timeout=timeout,
                metadata=metadata or {}
            )
            
            # Add to microservice queue
            self.task_queue.append(task)
            self.active_tasks[task_id] = task
            
            # Add to task history with memory bounds
            self.task_history.append({
                "task_id": task_id,
                "task_type": task_type.value,
                "specialty": specialty.value,
                "created_at": datetime.now().isoformat(),
                "priority": priority.value
            })
            
            # Update microservice metrics
            ai_orchestration_handit_metrics["total_tasks_created"] += 1
            self.track_operation("create_task", True, {"task_type": task_type.value, "specialty": specialty.value})
            
            # Cleanup memory periodically
            if len(self.completed_tasks) > self._max_completed_tasks * 0.9:
                self._cleanup_completed_tasks()
            if len(self._task_cache) > self._max_cache_size * 0.9:
                self._cleanup_task_cache()
            
            # Calculate creation time
            creation_time = (time.perf_counter() - start_time) * 1000
            
            self.logger.info(f"🤖 Created Handit AI microservice task: {task_id} - {task_type.value}")
            return task_id
            
        except Exception as e:
            creation_time = (time.perf_counter() - start_time) * 1000
            ai_orchestration_handit_metrics["failed_tasks"] += 1
            
            error_response = self.handle_error(
                e, "create_task", 
                {"task_type": task_type.value if task_type else "unknown"}
            )
            
            self.logger.error(f"❌ Failed to create microservice task: {error_response}")
            raise
    
    # Performance tracking is handled by base microservice
    async def execute_task(
        self,
        task_type: str,
        input_data: Dict[str, Any],
        model_specialty: str = "general"
    ) -> Dict[str, Any]:
        """Execute Handit AI task with service-specific implementation"""
        start_time = time.perf_counter()
        
        try:
            # Convert string types to enums
            task_type_enum = TaskType(task_type) if isinstance(task_type, str) else task_type
            specialty_enum = ModelSpecialty(model_specialty) if isinstance(model_specialty, str) else model_specialty
            
            # Create task
            task_id = await self.create_task(
                task_type=task_type_enum,
                specialty=specialty_enum,
                input_data=input_data
            )
            
            # Execute task with appropriate AI service
            result = await self._execute_ai_task(
                task_id=task_id,
                task_type=task_type,
                specialty=model_specialty,
                input_data=input_data,
                start_time=start_time
            )
            
            # Update metrics
            ai_orchestration_handit_metrics["successful_tasks"] += 1
            self.track_operation("execute_task", True, {"task_type": task_type, "specialty": model_specialty})
            
            self.logger.info(f"✅ Task executed successfully: {task_id} - {task_type}")
            return result
            
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            ai_orchestration_handit_metrics["failed_tasks"] += 1
            
            error_response = self.handle_error(
                e, "execute_task",
                {"task_type": task_type, "model_specialty": model_specialty}
            )
            
            self.logger.error(f"❌ Task execution failed: {error_response}")
            raise
    
    def get_enhanced_health_status(self) -> Dict[str, Any]:
        """Get enhanced health status with Handit AI specific metrics"""
        # Get base health status from parent
        base_health = super().get_health_status()
        
        # Add Handit AI specific metrics
        current_load = len(self.active_tasks)
        base_health.update({
            "status": "healthy" if current_load < self.config.get("max_concurrent", 10) else "busy",
            "handit_metrics": {
                "total_tasks": ai_orchestration_handit_metrics["total_tasks_created"],
                "successful_tasks": ai_orchestration_handit_metrics["successful_tasks"],
                "failed_tasks": ai_orchestration_handit_metrics["failed_tasks"],
                "active_tasks": len(self.active_tasks),
                "queued_tasks": len(self.task_queue),
                "completed_tasks": len(self.completed_tasks),
                "avg_processing_time_ms": ai_orchestration_handit_metrics["avg_task_duration_ms"]
            },
            "models": {
                "available_models": len(self.models),
                "model_usage_stats": self.model_usage_stats
            },
            "microservice_version": "2.0.0"
        })
        
        return base_health


# Global microservice instance
ai_orchestration_handit_client = AIOrchestrationHanditClient()


def get_handit_microservice() -> AIOrchestrationHanditClient:
    """Get the global Handit AI microservice instance"""
    return ai_orchestration_handit_client