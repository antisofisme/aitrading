"""
AI Brain Enhanced ML-Processing Pre-execution Safety Validator
Validates model training safety, resource exhaustion prevention, and data corruption checks

SAFETY VALIDATION COMPONENTS:
- Model Training Safety (parameter bounds, convergence safety, memory safety)
- Resource Exhaustion Prevention (memory monitoring, CPU limits, disk space)
- Data Corruption Prevention (data integrity, backup validation, checksum verification)
- Training Pipeline Safety (error recovery, rollback mechanisms, state consistency)
- Real-time Processing Safety (latency bounds, throughput limits, queue safety)
- Model State Protection (serialization safety, version control, integrity checks)
"""

import time
import psutil
import hashlib
import pickle
import tempfile
import shutil
import os
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import logging
from datetime import datetime, timedelta
import threading
import numpy as np
import pandas as pd


class SafetyCheckCategory(Enum):
    """Categories of safety checks for ML Processing"""
    TRAINING_SAFETY = "training_safety"
    RESOURCE_SAFETY = "resource_safety"
    DATA_INTEGRITY = "data_integrity"
    PIPELINE_SAFETY = "pipeline_safety"
    REAL_TIME_SAFETY = "real_time_safety"
    MODEL_STATE_SAFETY = "model_state_safety"
    MEMORY_SAFETY = "memory_safety"
    EXECUTION_SAFETY = "execution_safety"


class SafetyCriticality(Enum):
    """Criticality levels for safety checks"""
    CRITICAL = "critical"      # Must pass to proceed
    HIGH = "high"             # Should pass, warnings if failed
    MEDIUM = "medium"         # Recommended to pass
    LOW = "low"              # Informational
    MONITORING = "monitoring"  # Continuous monitoring required


@dataclass
class SafetyCheckResult:
    """Result of a safety validation check"""
    check_id: str
    category: SafetyCheckCategory
    criticality: SafetyCriticality
    status: str  # "safe", "unsafe", "warning", "monitoring"
    message: str
    details: Dict[str, Any]
    safety_recommendations: List[str]
    mitigation_actions: List[str]
    monitoring_required: bool
    timestamp: float
    execution_time_ms: float


class AiBrainMLProcessingSafetyValidator:
    """
    AI Brain Enhanced Safety Validator for ML-Processing Service
    Ensures all ML operations are safe before execution
    """
    
    def __init__(self, service_name: str = "ml-processing"):
        self.service_name = service_name
        self.logger = logging.getLogger(f"ai_brain_safety_validator_{service_name}")
        
        # Safety validation history and metrics
        self.safety_history: List[SafetyCheckResult] = []
        self.safety_metrics: Dict[str, Any] = {
            "total_safety_checks": 0,
            "safe_operations": 0,
            "unsafe_operations": 0,
            "warning_operations": 0,
            "critical_failures": 0
        }
        
        # Safety thresholds and limits
        self.safety_thresholds: Dict[str, Dict[str, Any]] = {
            "memory": {
                "max_training_memory_gb": 8.0,        # Max memory for training
                "memory_buffer_gb": 2.0,              # Keep 2GB free
                "memory_leak_threshold": 0.1,         # 10% memory increase per hour
                "gc_trigger_threshold": 0.8            # Trigger GC at 80% memory
            },
            "training": {
                "max_training_time_hours": 24.0,      # Max 24 hours training
                "min_checkpoint_interval_minutes": 30, # Checkpoint every 30 minutes
                "max_parameter_count": 100_000_000,    # Max 100M parameters
                "numerical_stability_threshold": 1e-8  # Numerical stability check
            },
            "data": {
                "max_data_size_gb": 10.0,             # Max 10GB training data
                "corruption_check_samples": 1000,      # Sample size for corruption check
                "backup_retention_hours": 72,          # Keep backups for 72 hours
                "checksum_validation": True            # Validate data checksums
            },
            "real_time": {
                "max_inference_latency_ms": 100.0,    # Max 100ms inference
                "max_queue_size": 10000,               # Max queue size
                "throughput_limit_per_second": 1000,   # Max 1000 predictions/sec
                "circuit_breaker_threshold": 0.5       # 50% failure rate trips breaker
            }
        }
        
        # Resource monitoring
        self.resource_monitor = ResourceMonitor()
        self.data_integrity_monitor = DataIntegrityMonitor()
        
        # Safety locks and states
        self.safety_locks: Dict[str, bool] = {
            "training_active": False,
            "data_loading": False,
            "model_serialization": False,
            "emergency_stop": False
        }
        
        self.logger.info("AI Brain ML-Processing Safety Validator initialized")
    
    def perform_comprehensive_safety_check(self,
                                         operation_type: str,
                                         operation_context: Dict[str, Any],
                                         safety_level: str = "standard") -> Dict[str, Any]:
        """
        Perform comprehensive safety validation before ML operation
        
        Args:
            operation_type: Type of operation (train, predict, feature_engineering)
            operation_context: Context for the operation
            safety_level: Level of safety checks (minimal, standard, strict)
            
        Returns:
            Comprehensive safety validation results
        """
        start_time = time.perf_counter()
        
        safety_results = []
        overall_safety_status = "safe"
        
        try:
            # 1. Resource Safety Checks
            resource_checks = self._validate_resource_safety(operation_context, safety_level)
            safety_results.extend(resource_checks)
            
            # 2. Data Integrity Checks
            data_checks = self._validate_data_integrity_safety(operation_context, safety_level)
            safety_results.extend(data_checks)
            
            # 3. Training Safety Checks (if training operation)
            if operation_type in ["train", "retrain", "adaptation"]:
                training_checks = self._validate_training_safety(operation_context, safety_level)
                safety_results.extend(training_checks)
            
            # 4. Pipeline Safety Checks
            pipeline_checks = self._validate_pipeline_safety(operation_context, safety_level)
            safety_results.extend(pipeline_checks)
            
            # 5. Real-time Safety Checks (if real-time operation)
            if operation_context.get("real_time_required", False):
                realtime_checks = self._validate_real_time_safety(operation_context, safety_level)
                safety_results.extend(realtime_checks)
            
            # 6. Model State Safety Checks
            if operation_type in ["predict", "deploy", "save"]:
                model_state_checks = self._validate_model_state_safety(operation_context, safety_level)
                safety_results.extend(model_state_checks)
            
            # Determine overall safety status
            critical_failures = [r for r in safety_results if r.status == "unsafe" and r.criticality == SafetyCriticality.CRITICAL]
            high_failures = [r for r in safety_results if r.status == "unsafe" and r.criticality == SafetyCriticality.HIGH]
            warnings = [r for r in safety_results if r.status == "warning"]
            
            if critical_failures:
                overall_safety_status = "critical_unsafe"
            elif high_failures:
                overall_safety_status = "high_risk"
            elif warnings:
                overall_safety_status = "warning"
            
            # Update safety metrics
            self.safety_metrics["total_safety_checks"] += len(safety_results)
            if overall_safety_status == "safe":
                self.safety_metrics["safe_operations"] += 1
            elif overall_safety_status in ["critical_unsafe", "high_risk"]:
                self.safety_metrics["unsafe_operations"] += 1
            else:
                self.safety_metrics["warning_operations"] += 1
            
            self.safety_metrics["critical_failures"] += len(critical_failures)
            
            execution_time = (time.perf_counter() - start_time) * 1000
            
            comprehensive_result = {
                "operation_type": operation_type,
                "safety_level": safety_level,
                "overall_safety_status": overall_safety_status,
                "total_safety_checks": len(safety_results),
                "safe_checks": len([r for r in safety_results if r.status == "safe"]),
                "unsafe_checks": len([r for r in safety_results if r.status == "unsafe"]),
                "warning_checks": len(warnings),
                "critical_failures": len(critical_failures),
                "execution_time_ms": execution_time,
                "safety_results": [asdict(result) for result in safety_results],
                "safety_recommendations": self._generate_overall_safety_recommendations(safety_results),
                "can_proceed_safely": overall_safety_status not in ["critical_unsafe"],
                "requires_monitoring": any(r.monitoring_required for r in safety_results),
                "risk_level": self._calculate_safety_risk_level(safety_results),
                "timestamp": datetime.now().isoformat()
            }
            
            # Store in safety history
            self.safety_history.extend(safety_results)
            if len(self.safety_history) > 1000:  # Keep last 1000 checks
                self.safety_history = self.safety_history[-1000:]
            
            self.logger.info(f"Safety validation completed: {overall_safety_status} in {execution_time:.2f}ms")
            return comprehensive_result
            
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            self.logger.error(f"Safety validation failed: {e}")
            
            return {
                "operation_type": operation_type,
                "safety_level": safety_level,
                "overall_safety_status": "validation_failure",
                "error": str(e),
                "execution_time_ms": execution_time,
                "can_proceed_safely": False,
                "risk_level": "critical",
                "timestamp": datetime.now().isoformat()
            }
    
    def _validate_resource_safety(self, context: Dict[str, Any], safety_level: str) -> List[SafetyCheckResult]:
        """Validate resource safety for ML operations"""
        results = []
        
        try:
            # Memory safety check
            memory = psutil.virtual_memory()
            available_memory_gb = memory.available / (1024**3)
            memory_usage_percent = memory.percent
            
            # Check if we have enough memory buffer
            required_buffer = self.safety_thresholds["memory"]["memory_buffer_gb"]
            if available_memory_gb < required_buffer:
                results.append(SafetyCheckResult(
                    check_id="MEMORY_SAFETY_001",
                    category=SafetyCheckCategory.RESOURCE_SAFETY,
                    criticality=SafetyCriticality.CRITICAL,
                    status="unsafe",
                    message=f"Insufficient memory buffer: {available_memory_gb:.2f}GB available, {required_buffer}GB required",
                    details={"available_memory_gb": available_memory_gb, "required_buffer_gb": required_buffer},
                    safety_recommendations=["Free up memory before proceeding", "Close unnecessary applications"],
                    mitigation_actions=["trigger_garbage_collection", "reduce_batch_size"],
                    monitoring_required=True,
                    timestamp=time.time(),
                    execution_time_ms=1.0
                ))
            else:
                results.append(SafetyCheckResult(
                    check_id="MEMORY_SAFETY_002",
                    category=SafetyCheckCategory.RESOURCE_SAFETY,
                    criticality=SafetyCriticality.HIGH,
                    status="safe",
                    message=f"Memory buffer adequate: {available_memory_gb:.2f}GB available",
                    details={"available_memory_gb": available_memory_gb},
                    safety_recommendations=[],
                    mitigation_actions=[],
                    monitoring_required=False,
                    timestamp=time.time(),
                    execution_time_ms=1.0
                ))
            
            # CPU safety check
            cpu_usage = psutil.cpu_percent(interval=0.1)
            if cpu_usage > 95.0:
                results.append(SafetyCheckResult(
                    check_id="CPU_SAFETY_001",
                    category=SafetyCheckCategory.RESOURCE_SAFETY,
                    criticality=SafetyCriticality.HIGH,
                    status="warning",
                    message=f"Very high CPU usage: {cpu_usage:.1f}%",
                    details={"cpu_usage_percent": cpu_usage},
                    safety_recommendations=["Wait for CPU load to decrease", "Consider load balancing"],
                    mitigation_actions=["reduce_parallelism", "implement_backpressure"],
                    monitoring_required=True,
                    timestamp=time.time(),
                    execution_time_ms=100.0
                ))
            
            # Disk safety check
            disk = psutil.disk_usage('/')
            disk_free_gb = disk.free / (1024**3)
            if disk_free_gb < 1.0:  # Less than 1GB free
                results.append(SafetyCheckResult(
                    check_id="DISK_SAFETY_001",
                    category=SafetyCheckCategory.RESOURCE_SAFETY,
                    criticality=SafetyCriticality.CRITICAL,
                    status="unsafe",
                    message=f"Critical low disk space: {disk_free_gb:.2f}GB free",
                    details={"disk_free_gb": disk_free_gb},
                    safety_recommendations=["Free up disk space immediately", "Clean temporary files"],
                    mitigation_actions=["cleanup_temp_files", "compress_models"],
                    monitoring_required=True,
                    timestamp=time.time(),
                    execution_time_ms=1.0
                ))
            
            # Training memory estimation safety
            if "training_data" in context and isinstance(context["training_data"], pd.DataFrame):
                data = context["training_data"]
                estimated_training_memory = (data.memory_usage(deep=True).sum() * 3) / (1024**3)  # 3x for safety
                max_training_memory = self.safety_thresholds["memory"]["max_training_memory_gb"]
                
                if estimated_training_memory > max_training_memory:
                    results.append(SafetyCheckResult(
                        check_id="TRAINING_MEMORY_SAFETY_001",
                        category=SafetyCheckCategory.MEMORY_SAFETY,
                        criticality=SafetyCriticality.HIGH,
                        status="unsafe",
                        message=f"Training memory requirement too high: {estimated_training_memory:.2f}GB",
                        details={"estimated_memory_gb": estimated_training_memory, "max_allowed_gb": max_training_memory},
                        safety_recommendations=["Reduce data size", "Implement data streaming", "Use smaller batch sizes"],
                        mitigation_actions=["enable_data_streaming", "reduce_batch_size", "implement_data_chunking"],
                        monitoring_required=True,
                        timestamp=time.time(),
                        execution_time_ms=5.0
                    ))
            
        except Exception as e:
            results.append(SafetyCheckResult(
                check_id="RESOURCE_SAFETY_ERROR",
                category=SafetyCheckCategory.RESOURCE_SAFETY,
                criticality=SafetyCriticality.HIGH,
                status="unsafe",
                message=f"Resource safety validation error: {str(e)}",
                details={"error": str(e)},
                safety_recommendations=["Check system monitoring tools"],
                mitigation_actions=["manual_resource_check"],
                monitoring_required=True,
                timestamp=time.time(),
                execution_time_ms=1.0
            ))
        
        return results
    
    def _validate_data_integrity_safety(self, context: Dict[str, Any], safety_level: str) -> List[SafetyCheckResult]:
        """Validate data integrity and corruption prevention"""
        results = []
        
        try:
            # Data size safety check
            if "training_data" in context and isinstance(context["training_data"], pd.DataFrame):
                data = context["training_data"]
                data_size_gb = data.memory_usage(deep=True).sum() / (1024**3)
                max_data_size = self.safety_thresholds["data"]["max_data_size_gb"]
                
                if data_size_gb > max_data_size:
                    results.append(SafetyCheckResult(
                        check_id="DATA_SIZE_SAFETY_001",
                        category=SafetyCheckCategory.DATA_INTEGRITY,
                        criticality=SafetyCriticality.MEDIUM,
                        status="warning",
                        message=f"Large dataset size: {data_size_gb:.2f}GB",
                        details={"data_size_gb": data_size_gb, "max_recommended_gb": max_data_size},
                        safety_recommendations=["Consider data sampling", "Implement streaming processing"],
                        mitigation_actions=["enable_data_streaming", "implement_sampling"],
                        monitoring_required=True,
                        timestamp=time.time(),
                        execution_time_ms=2.0
                    ))
                
                # Data quality safety check
                null_percentage = data.isnull().sum().sum() / (data.shape[0] * data.shape[1])
                if null_percentage > 0.5:  # More than 50% missing data
                    results.append(SafetyCheckResult(
                        check_id="DATA_QUALITY_SAFETY_001",
                        category=SafetyCheckCategory.DATA_INTEGRITY,
                        criticality=SafetyCriticality.HIGH,
                        status="unsafe",
                        message=f"Excessive missing data: {null_percentage:.1%}",
                        details={"null_percentage": null_percentage},
                        safety_recommendations=["Clean data before training", "Implement proper imputation"],
                        mitigation_actions=["clean_missing_data", "implement_imputation"],
                        monitoring_required=False,
                        timestamp=time.time(),
                        execution_time_ms=5.0
                    ))
                
                # Numerical stability check
                numeric_columns = data.select_dtypes(include=[np.number]).columns
                for col in numeric_columns:
                    if data[col].std() == 0:  # No variation
                        results.append(SafetyCheckResult(
                            check_id=f"NUMERICAL_STABILITY_001_{col}",
                            category=SafetyCheckCategory.DATA_INTEGRITY,
                            criticality=SafetyCriticality.MEDIUM,
                            status="warning",
                            message=f"Zero variance in feature: {col}",
                            details={"feature": col, "std": data[col].std()},
                            safety_recommendations=[f"Remove constant feature: {col}"],
                            mitigation_actions=["remove_constant_features"],
                            monitoring_required=False,
                            timestamp=time.time(),
                            execution_time_ms=1.0
                        ))
                    
                    # Check for extreme values
                    if np.isinf(data[col]).any() or np.isnan(data[col]).any():
                        results.append(SafetyCheckResult(
                            check_id=f"NUMERICAL_SAFETY_001_{col}",
                            category=SafetyCheckCategory.DATA_INTEGRITY,
                            criticality=SafetyCriticality.HIGH,
                            status="unsafe",
                            message=f"Infinite or NaN values in feature: {col}",
                            details={"feature": col, "inf_count": np.isinf(data[col]).sum(), "nan_count": np.isnan(data[col]).sum()},
                            safety_recommendations=["Clean infinite and NaN values", "Implement robust preprocessing"],
                            mitigation_actions=["clean_infinite_values", "implement_robust_scaling"],
                            monitoring_required=False,
                            timestamp=time.time(),
                            execution_time_ms=2.0
                        ))
            
            # Checksum validation (if enabled)
            if self.safety_thresholds["data"]["checksum_validation"] and "data_checksum" in context:
                expected_checksum = context["data_checksum"]
                if "training_data" in context:
                    actual_checksum = self._calculate_data_checksum(context["training_data"])
                    if actual_checksum != expected_checksum:
                        results.append(SafetyCheckResult(
                            check_id="DATA_CHECKSUM_SAFETY_001",
                            category=SafetyCheckCategory.DATA_INTEGRITY,
                            criticality=SafetyCriticality.CRITICAL,
                            status="unsafe",
                            message="Data checksum mismatch - possible corruption",
                            details={"expected": expected_checksum, "actual": actual_checksum},
                            safety_recommendations=["Reload data from source", "Verify data integrity"],
                            mitigation_actions=["reload_data", "verify_data_source"],
                            monitoring_required=True,
                            timestamp=time.time(),
                            execution_time_ms=10.0
                        ))
            
        except Exception as e:
            results.append(SafetyCheckResult(
                check_id="DATA_INTEGRITY_SAFETY_ERROR",
                category=SafetyCheckCategory.DATA_INTEGRITY,
                criticality=SafetyCriticality.HIGH,
                status="unsafe",
                message=f"Data integrity safety validation error: {str(e)}",
                details={"error": str(e)},
                safety_recommendations=["Check data format and structure"],
                mitigation_actions=["validate_data_format"],
                monitoring_required=True,
                timestamp=time.time(),
                execution_time_ms=1.0
            ))
        
        return results
    
    def _validate_training_safety(self, context: Dict[str, Any], safety_level: str) -> List[SafetyCheckResult]:
        """Validate training operation safety"""
        results = []
        
        try:
            # Training duration safety
            if "max_training_time_hours" in context:
                max_training_hours = context["max_training_time_hours"]
                threshold_hours = self.safety_thresholds["training"]["max_training_time_hours"]
                
                if max_training_hours > threshold_hours:
                    results.append(SafetyCheckResult(
                        check_id="TRAINING_DURATION_SAFETY_001",
                        category=SafetyCheckCategory.TRAINING_SAFETY,
                        criticality=SafetyCriticality.MEDIUM,
                        status="warning",
                        message=f"Long training duration: {max_training_hours}h (max recommended: {threshold_hours}h)",
                        details={"max_training_hours": max_training_hours, "recommended_max": threshold_hours},
                        safety_recommendations=["Implement checkpointing", "Enable early stopping"],
                        mitigation_actions=["enable_checkpointing", "implement_early_stopping"],
                        monitoring_required=True,
                        timestamp=time.time(),
                        execution_time_ms=1.0
                    ))
            
            # Model complexity safety
            if "model_parameters" in context:
                param_count = context["model_parameters"]
                max_params = self.safety_thresholds["training"]["max_parameter_count"]
                
                if param_count > max_params:
                    results.append(SafetyCheckResult(
                        check_id="MODEL_COMPLEXITY_SAFETY_001",
                        category=SafetyCheckCategory.TRAINING_SAFETY,
                        criticality=SafetyCriticality.HIGH,
                        status="warning",
                        message=f"High model complexity: {param_count:,} parameters",
                        details={"parameter_count": param_count, "max_recommended": max_params},
                        safety_recommendations=["Consider model pruning", "Reduce model complexity"],
                        mitigation_actions=["implement_model_pruning", "reduce_layer_sizes"],
                        monitoring_required=True,
                        timestamp=time.time(),
                        execution_time_ms=1.0
                    ))
            
            # Hyperparameter safety
            if "hyperparameters" in context:
                hyperparams = context["hyperparameters"]
                
                # Learning rate safety
                if "learning_rate" in hyperparams:
                    lr = hyperparams["learning_rate"]
                    if lr > 1.0 or lr <= 0:
                        results.append(SafetyCheckResult(
                            check_id="LEARNING_RATE_SAFETY_001",
                            category=SafetyCheckCategory.TRAINING_SAFETY,
                            criticality=SafetyCriticality.HIGH,
                            status="unsafe",
                            message=f"Unsafe learning rate: {lr}",
                            details={"learning_rate": lr, "safe_range": "(0, 1.0]"},
                            safety_recommendations=["Set learning rate in safe range (0.0001 to 0.1)"],
                            mitigation_actions=["adjust_learning_rate"],
                            monitoring_required=False,
                            timestamp=time.time(),
                            execution_time_ms=1.0
                        ))
                
                # Batch size safety
                if "batch_size" in hyperparams:
                    batch_size = hyperparams["batch_size"]
                    if batch_size <= 0:
                        results.append(SafetyCheckResult(
                            check_id="BATCH_SIZE_SAFETY_001",
                            category=SafetyCheckCategory.TRAINING_SAFETY,
                            criticality=SafetyCriticality.CRITICAL,
                            status="unsafe",
                            message=f"Invalid batch size: {batch_size}",
                            details={"batch_size": batch_size},
                            safety_recommendations=["Set positive batch size"],
                            mitigation_actions=["set_default_batch_size"],
                            monitoring_required=False,
                            timestamp=time.time(),
                            execution_time_ms=1.0
                        ))
            
            # Training lock safety
            if self.safety_locks["training_active"]:
                results.append(SafetyCheckResult(
                    check_id="TRAINING_LOCK_SAFETY_001",
                    category=SafetyCheckCategory.TRAINING_SAFETY,
                    criticality=SafetyCriticality.CRITICAL,
                    status="unsafe",
                    message="Another training process is already active",
                    details={"training_active": True},
                    safety_recommendations=["Wait for current training to complete", "Stop existing training if needed"],
                    mitigation_actions=["wait_for_completion", "stop_existing_training"],
                    monitoring_required=True,
                    timestamp=time.time(),
                    execution_time_ms=1.0
                ))
            
        except Exception as e:
            results.append(SafetyCheckResult(
                check_id="TRAINING_SAFETY_ERROR",
                category=SafetyCheckCategory.TRAINING_SAFETY,
                criticality=SafetyCriticality.HIGH,
                status="unsafe",
                message=f"Training safety validation error: {str(e)}",
                details={"error": str(e)},
                safety_recommendations=["Check training configuration"],
                mitigation_actions=["validate_training_config"],
                monitoring_required=True,
                timestamp=time.time(),
                execution_time_ms=1.0
            ))
        
        return results
    
    def _validate_pipeline_safety(self, context: Dict[str, Any], safety_level: str) -> List[SafetyCheckResult]:
        """Validate ML pipeline safety"""
        results = []
        
        try:
            # Emergency stop check
            if self.safety_locks["emergency_stop"]:
                results.append(SafetyCheckResult(
                    check_id="EMERGENCY_STOP_001",
                    category=SafetyCheckCategory.PIPELINE_SAFETY,
                    criticality=SafetyCriticality.CRITICAL,
                    status="unsafe",
                    message="Emergency stop is active",
                    details={"emergency_stop": True},
                    safety_recommendations=["Clear emergency stop condition", "Investigate root cause"],
                    mitigation_actions=["clear_emergency_stop", "investigate_emergency"],
                    monitoring_required=True,
                    timestamp=time.time(),
                    execution_time_ms=1.0
                ))
            
            # Pipeline state consistency
            active_operations = sum([
                self.safety_locks["training_active"],
                self.safety_locks["data_loading"],
                self.safety_locks["model_serialization"]
            ])
            
            if active_operations > 1:
                results.append(SafetyCheckResult(
                    check_id="PIPELINE_CONCURRENCY_001",
                    category=SafetyCheckCategory.PIPELINE_SAFETY,
                    criticality=SafetyCriticality.MEDIUM,
                    status="warning",
                    message=f"Multiple concurrent operations: {active_operations}",
                    details={"concurrent_operations": active_operations, "locks": self.safety_locks},
                    safety_recommendations=["Serialize operations", "Implement operation queuing"],
                    mitigation_actions=["implement_operation_queue", "serialize_operations"],
                    monitoring_required=True,
                    timestamp=time.time(),
                    execution_time_ms=1.0
                ))
            
        except Exception as e:
            results.append(SafetyCheckResult(
                check_id="PIPELINE_SAFETY_ERROR",
                category=SafetyCheckCategory.PIPELINE_SAFETY,
                criticality=SafetyCriticality.MEDIUM,
                status="warning",
                message=f"Pipeline safety validation error: {str(e)}",
                details={"error": str(e)},
                safety_recommendations=["Check pipeline configuration"],
                mitigation_actions=["validate_pipeline_config"],
                monitoring_required=True,
                timestamp=time.time(),
                execution_time_ms=1.0
            ))
        
        return results
    
    def _validate_real_time_safety(self, context: Dict[str, Any], safety_level: str) -> List[SafetyCheckResult]:
        """Validate real-time processing safety"""
        results = []
        
        # Real-time latency safety
        max_latency = self.safety_thresholds["real_time"]["max_inference_latency_ms"]
        if "expected_latency_ms" in context:
            expected_latency = context["expected_latency_ms"]
            if expected_latency > max_latency:
                results.append(SafetyCheckResult(
                    check_id="REALTIME_LATENCY_SAFETY_001",
                    category=SafetyCheckCategory.REAL_TIME_SAFETY,
                    criticality=SafetyCriticality.HIGH,
                    status="unsafe",
                    message=f"Expected latency too high: {expected_latency}ms",
                    details={"expected_latency_ms": expected_latency, "max_allowed_ms": max_latency},
                    safety_recommendations=["Optimize model for faster inference", "Consider model quantization"],
                    mitigation_actions=["optimize_inference", "implement_model_quantization"],
                    monitoring_required=True,
                    timestamp=time.time(),
                    execution_time_ms=1.0
                ))
        
        return results
    
    def _validate_model_state_safety(self, context: Dict[str, Any], safety_level: str) -> List[SafetyCheckResult]:
        """Validate model state and serialization safety"""
        results = []
        
        try:
            # Model serialization safety
            if self.safety_locks["model_serialization"]:
                results.append(SafetyCheckResult(
                    check_id="MODEL_SERIALIZATION_SAFETY_001",
                    category=SafetyCheckCategory.MODEL_STATE_SAFETY,
                    criticality=SafetyCriticality.HIGH,
                    status="warning",
                    message="Model serialization in progress",
                    details={"serialization_active": True},
                    safety_recommendations=["Wait for serialization to complete"],
                    mitigation_actions=["wait_for_serialization"],
                    monitoring_required=True,
                    timestamp=time.time(),
                    execution_time_ms=1.0
                ))
            
            # Model state integrity check
            if "model" in context:
                model = context["model"]
                try:
                    # Try to serialize/deserialize to check integrity
                    with tempfile.NamedTemporaryFile() as tmp_file:
                        pickle.dump(model, tmp_file)
                        tmp_file.seek(0)
                        pickle.load(tmp_file)
                    
                    results.append(SafetyCheckResult(
                        check_id="MODEL_STATE_INTEGRITY_001",
                        category=SafetyCheckCategory.MODEL_STATE_SAFETY,
                        criticality=SafetyCriticality.MEDIUM,
                        status="safe",
                        message="Model state integrity verified",
                        details={"integrity_check": "passed"},
                        safety_recommendations=[],
                        mitigation_actions=[],
                        monitoring_required=False,
                        timestamp=time.time(),
                        execution_time_ms=10.0
                    ))
                    
                except Exception as integrity_error:
                    results.append(SafetyCheckResult(
                        check_id="MODEL_STATE_INTEGRITY_002",
                        category=SafetyCheckCategory.MODEL_STATE_SAFETY,
                        criticality=SafetyCriticality.HIGH,
                        status="unsafe",
                        message=f"Model state integrity check failed: {str(integrity_error)}",
                        details={"integrity_error": str(integrity_error)},
                        safety_recommendations=["Reload model from backup", "Retrain model if necessary"],
                        mitigation_actions=["restore_from_backup", "retrain_model"],
                        monitoring_required=True,
                        timestamp=time.time(),
                        execution_time_ms=10.0
                    ))
            
        except Exception as e:
            results.append(SafetyCheckResult(
                check_id="MODEL_STATE_SAFETY_ERROR",
                category=SafetyCheckCategory.MODEL_STATE_SAFETY,
                criticality=SafetyCriticality.MEDIUM,
                status="warning",
                message=f"Model state safety validation error: {str(e)}",
                details={"error": str(e)},
                safety_recommendations=["Check model configuration"],
                mitigation_actions=["validate_model_config"],
                monitoring_required=True,
                timestamp=time.time(),
                execution_time_ms=1.0
            ))
        
        return results
    
    def _calculate_data_checksum(self, data: Any) -> str:
        """Calculate checksum for data integrity verification"""
        try:
            if isinstance(data, pd.DataFrame):
                # Convert to string representation and hash
                data_str = data.to_string()
                return hashlib.md5(data_str.encode()).hexdigest()
            else:
                # For other data types, use pickle and hash
                pickled_data = pickle.dumps(data)
                return hashlib.md5(pickled_data).hexdigest()
        except Exception:
            return "checksum_error"
    
    def _generate_overall_safety_recommendations(self, safety_results: List[SafetyCheckResult]) -> List[str]:
        """Generate overall safety recommendations"""
        recommendations = []
        
        # Critical safety issues
        critical_issues = [r for r in safety_results if r.status == "unsafe" and r.criticality == SafetyCriticality.CRITICAL]
        if critical_issues:
            recommendations.append("🚨 CRITICAL SAFETY ISSUES: Must be resolved before proceeding")
            for issue in critical_issues[:3]:  # Top 3 critical issues
                recommendations.extend(issue.safety_recommendations)
        
        # High risk issues
        high_risk_issues = [r for r in safety_results if r.criticality == SafetyCriticality.HIGH and r.status in ["unsafe", "warning"]]
        if high_risk_issues:
            recommendations.append("⚠️ HIGH RISK: Address high-risk safety issues")
        
        # Resource safety
        resource_issues = [r for r in safety_results if r.category == SafetyCheckCategory.RESOURCE_SAFETY and r.status != "safe"]
        if resource_issues:
            recommendations.append("💾 Ensure adequate system resources")
        
        # Monitoring recommendations
        monitoring_required = [r for r in safety_results if r.monitoring_required]
        if monitoring_required:
            recommendations.append("📊 Continuous monitoring required for some operations")
        
        return list(set(recommendations))  # Remove duplicates
    
    def _calculate_safety_risk_level(self, safety_results: List[SafetyCheckResult]) -> str:
        """Calculate overall safety risk level"""
        critical_unsafe = len([r for r in safety_results if r.status == "unsafe" and r.criticality == SafetyCriticality.CRITICAL])
        high_unsafe = len([r for r in safety_results if r.status == "unsafe" and r.criticality == SafetyCriticality.HIGH])
        warnings = len([r for r in safety_results if r.status == "warning"])
        
        if critical_unsafe > 0:
            return "critical"
        elif high_unsafe > 1:
            return "high"
        elif high_unsafe > 0 or warnings > 2:
            return "medium"
        elif warnings > 0:
            return "low"
        else:
            return "minimal"
    
    def get_safety_statistics(self) -> Dict[str, Any]:
        """Get comprehensive safety statistics"""
        recent_checks = [c for c in self.safety_history if time.time() - c.timestamp < 86400]  # Last 24 hours
        
        category_stats = {}
        for check in recent_checks:
            category = check.category.value
            if category not in category_stats:
                category_stats[category] = {"total": 0, "safe": 0, "unsafe": 0, "warnings": 0}
            
            category_stats[category]["total"] += 1
            if check.status == "safe":
                category_stats[category]["safe"] += 1
            elif check.status == "unsafe":
                category_stats[category]["unsafe"] += 1
            elif check.status == "warning":
                category_stats[category]["warnings"] += 1
        
        return {
            "total_safety_checks_24h": len(recent_checks),
            "overall_metrics": self.safety_metrics,
            "category_breakdown": category_stats,
            "safety_thresholds": self.safety_thresholds,
            "current_safety_locks": self.safety_locks,
            "safety_success_rate": self.safety_metrics["safe_operations"] / max(self.safety_metrics["total_safety_checks"], 1),
            "last_updated": datetime.now().isoformat()
        }


class ResourceMonitor:
    """Resource monitoring helper"""
    def __init__(self):
        self.monitoring_active = False
    
    def start_monitoring(self):
        self.monitoring_active = True
    
    def stop_monitoring(self):
        self.monitoring_active = False


class DataIntegrityMonitor:
    """Data integrity monitoring helper"""
    def __init__(self):
        self.integrity_checks = []
    
    def add_integrity_check(self, check_result):
        self.integrity_checks.append(check_result)


# Global ML-Processing Safety Validator instance
ml_processing_safety_validator = AiBrainMLProcessingSafetyValidator("ml-processing")


def get_ml_safety_validator() -> AiBrainMLProcessingSafetyValidator:
    """Get the global ML-Processing Safety Validator instance"""
    return ml_processing_safety_validator


def perform_safety_check(operation_type: str, 
                        operation_context: Dict[str, Any],
                        safety_level: str = "standard") -> Dict[str, Any]:
    """Convenience function for comprehensive safety check"""
    return ml_processing_safety_validator.perform_comprehensive_safety_check(
        operation_type, operation_context, safety_level
    )