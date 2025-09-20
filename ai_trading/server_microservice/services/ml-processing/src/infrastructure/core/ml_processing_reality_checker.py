"""
AI Brain Enhanced ML-Processing Reality Checker
Comprehensive validation of data quality, algorithm availability, and computational resource checks

REALITY VALIDATION COMPONENTS:
- Data Quality Reality Checks (completeness, integrity, statistical validity)
- Algorithm Availability Checks (library versions, model compatibility)
- Computational Resource Validation (memory, CPU, GPU availability)
- Training Environment Reality (feature consistency, target availability)
- Model Deployment Readiness (inference capability, latency requirements)
- Real-time Processing Reality (streaming data, latency constraints)
"""

import time
import psutil
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import logging
from datetime import datetime, timedelta
import sys
import importlib
import gc
import threading


class RealityCheckCategory(Enum):
    """Categories of reality checks for ML Processing"""
    DATA_QUALITY = "data_quality"
    ALGORITHM_AVAILABILITY = "algorithm_availability"
    RESOURCE_AVAILABILITY = "resource_availability"
    TRAINING_ENVIRONMENT = "training_environment"
    DEPLOYMENT_READINESS = "deployment_readiness"
    REAL_TIME_CAPABILITY = "real_time_capability"
    FEATURE_INTEGRITY = "feature_integrity"
    MODEL_COMPATIBILITY = "model_compatibility"


class RealityCheckSeverity(Enum):
    """Severity levels for reality check failures"""
    CRITICAL = "critical"      # Blocks operation completely
    HIGH = "high"             # Significantly impacts performance
    MEDIUM = "medium"         # Moderate impact, workaround possible
    LOW = "low"              # Minor issue, doesn't affect core functionality
    INFO = "info"            # Informational, no action required


@dataclass
class RealityCheckResult:
    """Result of a reality check validation"""
    check_id: str
    category: RealityCheckCategory
    severity: RealityCheckSeverity
    status: str  # "pass", "fail", "warning"
    message: str
    details: Dict[str, Any]
    recommendations: List[str]
    timestamp: float
    execution_time_ms: float


class AiBrainMLProcessingRealityChecker:
    """
    AI Brain Enhanced Reality Checker for ML-Processing Service
    Validates all aspects of ML operations before execution
    """
    
    def __init__(self, service_name: str = "ml-processing"):
        self.service_name = service_name
        self.logger = logging.getLogger(f"ai_brain_reality_checker_{service_name}")
        
        # Reality check history and metrics
        self.check_history: List[RealityCheckResult] = []
        self.check_metrics: Dict[str, Any] = {
            "total_checks": 0,
            "passed_checks": 0,
            "failed_checks": 0,
            "warning_checks": 0
        }
        
        # System resource baselines
        self.system_baseline: Dict[str, float] = {}
        self.resource_thresholds: Dict[str, float] = {
            "memory_usage_threshold": 0.85,      # 85% memory usage
            "cpu_usage_threshold": 0.90,         # 90% CPU usage
            "disk_usage_threshold": 0.95,        # 95% disk usage
            "min_available_memory_gb": 2.0,      # Minimum 2GB available
            "max_training_memory_gb": 16.0,      # Maximum training memory
            "min_inference_latency_ms": 100.0    # Maximum acceptable inference latency
        }
        
        # Algorithm availability cache
        self.algorithm_availability: Dict[str, bool] = {}
        self.library_versions: Dict[str, str] = {}
        
        # Initialize baseline measurements
        self._initialize_system_baseline()
        self._check_algorithm_availability()
        
    def _initialize_system_baseline(self):
        """Initialize system resource baselines"""
        try:
            # CPU baseline
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_baseline["cpu_usage"] = cpu_percent
            
            # Memory baseline
            memory = psutil.virtual_memory()
            self.system_baseline["memory_usage"] = memory.percent
            self.system_baseline["available_memory_gb"] = memory.available / (1024**3)
            
            # Disk baseline
            disk = psutil.disk_usage('/')
            self.system_baseline["disk_usage"] = disk.percent
            
            self.logger.info(f"System baseline initialized: {self.system_baseline}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize system baseline: {e}")
            self.system_baseline = {"error": str(e)}
    
    def _check_algorithm_availability(self):
        """Check availability of ML algorithms and libraries"""
        libraries_to_check = [
            "sklearn", "xgboost", "lightgbm", "catboost", 
            "numpy", "pandas", "scipy", "joblib"
        ]
        
        for lib_name in libraries_to_check:
            try:
                lib = importlib.import_module(lib_name)
                self.algorithm_availability[lib_name] = True
                self.library_versions[lib_name] = getattr(lib, '__version__', 'unknown')
            except ImportError:
                self.algorithm_availability[lib_name] = False
                self.library_versions[lib_name] = 'not_available'
        
        self.logger.info(f"Algorithm availability: {self.algorithm_availability}")
    
    def perform_comprehensive_reality_check(self, 
                                          operation_type: str,
                                          operation_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive reality check before ML operation
        
        Args:
            operation_type: Type of operation (train, predict, feature_engineering)
            operation_context: Context for the operation
            
        Returns:
            Comprehensive reality check results
        """
        start_time = time.perf_counter()
        
        check_results = []
        overall_status = "pass"
        
        try:
            # 1. Data Quality Reality Checks
            data_checks = self._validate_data_reality(operation_context)
            check_results.extend(data_checks)
            
            # 2. Algorithm Availability Checks
            algorithm_checks = self._validate_algorithm_reality(operation_context)
            check_results.extend(algorithm_checks)
            
            # 3. Resource Availability Checks
            resource_checks = self._validate_resource_reality(operation_context)
            check_results.extend(resource_checks)
            
            # 4. Training Environment Checks (if applicable)
            if operation_type in ["train", "retrain", "adaptation"]:
                training_checks = self._validate_training_environment_reality(operation_context)
                check_results.extend(training_checks)
            
            # 5. Deployment Readiness Checks (if applicable)
            if operation_type in ["predict", "deploy"]:
                deployment_checks = self._validate_deployment_readiness_reality(operation_context)
                check_results.extend(deployment_checks)
            
            # 6. Real-time Capability Checks
            if operation_context.get("real_time_required", False):
                realtime_checks = self._validate_real_time_capability_reality(operation_context)
                check_results.extend(realtime_checks)
            
            # Determine overall status
            critical_failures = [r for r in check_results if r.status == "fail" and r.severity == RealityCheckSeverity.CRITICAL]
            high_failures = [r for r in check_results if r.status == "fail" and r.severity == RealityCheckSeverity.HIGH]
            warnings = [r for r in check_results if r.status == "warning"]
            
            if critical_failures:
                overall_status = "critical_failure"
            elif high_failures:
                overall_status = "high_risk"
            elif warnings:
                overall_status = "warning"
            
            # Update metrics
            self.check_metrics["total_checks"] += len(check_results)
            self.check_metrics["passed_checks"] += len([r for r in check_results if r.status == "pass"])
            self.check_metrics["failed_checks"] += len([r for r in check_results if r.status == "fail"])
            self.check_metrics["warning_checks"] += len(warnings)
            
            execution_time = (time.perf_counter() - start_time) * 1000
            
            comprehensive_result = {
                "operation_type": operation_type,
                "overall_status": overall_status,
                "total_checks": len(check_results),
                "passed_checks": len([r for r in check_results if r.status == "pass"]),
                "failed_checks": len([r for r in check_results if r.status == "fail"]),
                "warning_checks": len(warnings),
                "critical_failures": len(critical_failures),
                "execution_time_ms": execution_time,
                "check_results": [asdict(result) for result in check_results],
                "recommendations": self._generate_overall_recommendations(check_results),
                "can_proceed": overall_status not in ["critical_failure"],
                "risk_level": self._calculate_risk_level(check_results),
                "timestamp": datetime.now().isoformat()
            }
            
            # Store in history
            self.check_history.extend(check_results)
            if len(self.check_history) > 1000:  # Keep last 1000 checks
                self.check_history = self.check_history[-1000:]
            
            self.logger.info(f"Reality check completed: {overall_status} in {execution_time:.2f}ms")
            return comprehensive_result
            
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            self.logger.error(f"Reality check failed: {e}")
            
            return {
                "operation_type": operation_type,
                "overall_status": "check_failure",
                "error": str(e),
                "execution_time_ms": execution_time,
                "can_proceed": False,
                "risk_level": "unknown",
                "timestamp": datetime.now().isoformat()
            }
    
    def _validate_data_reality(self, context: Dict[str, Any]) -> List[RealityCheckResult]:
        """Validate data quality and integrity reality"""
        results = []
        
        try:
            # Check if training data is provided and valid
            if "training_data" in context:
                data = context["training_data"]
                
                # Data completeness check
                if isinstance(data, pd.DataFrame):
                    missing_percentage = data.isnull().sum().sum() / (data.shape[0] * data.shape[1])
                    
                    if missing_percentage > 0.3:
                        results.append(RealityCheckResult(
                            check_id="DATA_COMPLETENESS_001",
                            category=RealityCheckCategory.DATA_QUALITY,
                            severity=RealityCheckSeverity.CRITICAL,
                            status="fail",
                            message=f"High missing data percentage: {missing_percentage:.2%}",
                            details={"missing_percentage": missing_percentage, "shape": data.shape},
                            recommendations=["Implement data imputation", "Check data source quality"],
                            timestamp=time.time(),
                            execution_time_ms=1.0
                        ))
                    elif missing_percentage > 0.1:
                        results.append(RealityCheckResult(
                            check_id="DATA_COMPLETENESS_002",
                            category=RealityCheckCategory.DATA_QUALITY,
                            severity=RealityCheckSeverity.MEDIUM,
                            status="warning",
                            message=f"Moderate missing data: {missing_percentage:.2%}",
                            details={"missing_percentage": missing_percentage},
                            recommendations=["Consider data imputation strategies"],
                            timestamp=time.time(),
                            execution_time_ms=1.0
                        ))
                    else:
                        results.append(RealityCheckResult(
                            check_id="DATA_COMPLETENESS_003",
                            category=RealityCheckCategory.DATA_QUALITY,
                            severity=RealityCheckSeverity.INFO,
                            status="pass",
                            message="Data completeness acceptable",
                            details={"missing_percentage": missing_percentage},
                            recommendations=[],
                            timestamp=time.time(),
                            execution_time_ms=1.0
                        ))
                    
                    # Data size validation
                    if data.shape[0] < 100:
                        results.append(RealityCheckResult(
                            check_id="DATA_SIZE_001",
                            category=RealityCheckCategory.DATA_QUALITY,
                            severity=RealityCheckSeverity.HIGH,
                            status="fail",
                            message=f"Insufficient training data: {data.shape[0]} samples",
                            details={"sample_count": data.shape[0], "minimum_recommended": 1000},
                            recommendations=["Collect more training data", "Consider data augmentation"],
                            timestamp=time.time(),
                            execution_time_ms=1.0
                        ))
                    elif data.shape[0] < 1000:
                        results.append(RealityCheckResult(
                            check_id="DATA_SIZE_002",
                            category=RealityCheckCategory.DATA_QUALITY,
                            severity=RealityCheckSeverity.MEDIUM,
                            status="warning",
                            message=f"Limited training data: {data.shape[0]} samples",
                            details={"sample_count": data.shape[0]},
                            recommendations=["Consider collecting more data for better model performance"],
                            timestamp=time.time(),
                            execution_time_ms=1.0
                        ))
                    
                    # Feature consistency check
                    if "features" in context:
                        expected_features = context["features"]
                        available_features = list(data.columns)
                        missing_features = set(expected_features) - set(available_features)
                        
                        if missing_features:
                            results.append(RealityCheckResult(
                                check_id="FEATURE_CONSISTENCY_001",
                                category=RealityCheckCategory.FEATURE_INTEGRITY,
                                severity=RealityCheckSeverity.CRITICAL,
                                status="fail",
                                message=f"Missing required features: {missing_features}",
                                details={"missing_features": list(missing_features)},
                                recommendations=["Ensure all required features are available", "Check feature pipeline"],
                                timestamp=time.time(),
                                execution_time_ms=1.0
                            ))
                        else:
                            results.append(RealityCheckResult(
                                check_id="FEATURE_CONSISTENCY_002",
                                category=RealityCheckCategory.FEATURE_INTEGRITY,
                                severity=RealityCheckSeverity.INFO,
                                status="pass",
                                message="All required features available",
                                details={"feature_count": len(expected_features)},
                                recommendations=[],
                                timestamp=time.time(),
                                execution_time_ms=1.0
                            ))
                    
                    # Data distribution check
                    numeric_columns = data.select_dtypes(include=[np.number]).columns
                    if len(numeric_columns) > 0:
                        # Check for extreme outliers
                        outlier_features = []
                        for col in numeric_columns:
                            Q1 = data[col].quantile(0.25)
                            Q3 = data[col].quantile(0.75)
                            IQR = Q3 - Q1
                            lower_bound = Q1 - 3 * IQR
                            upper_bound = Q3 + 3 * IQR
                            
                            outliers = ((data[col] < lower_bound) | (data[col] > upper_bound)).sum()
                            outlier_percentage = outliers / len(data)
                            
                            if outlier_percentage > 0.05:  # More than 5% outliers
                                outlier_features.append(col)
                        
                        if outlier_features:
                            results.append(RealityCheckResult(
                                check_id="DATA_DISTRIBUTION_001",
                                category=RealityCheckCategory.DATA_QUALITY,
                                severity=RealityCheckSeverity.MEDIUM,
                                status="warning",
                                message=f"High outlier percentage in features: {outlier_features}",
                                details={"outlier_features": outlier_features},
                                recommendations=["Consider outlier treatment", "Validate data collection process"],
                                timestamp=time.time(),
                                execution_time_ms=5.0
                            ))
                
                # Target variable validation (for supervised learning)
                if "target" in context and isinstance(data, pd.DataFrame):
                    target_col = context["target"]
                    if target_col in data.columns:
                        target_missing = data[target_col].isnull().sum() / len(data)
                        if target_missing > 0.05:
                            results.append(RealityCheckResult(
                                check_id="TARGET_QUALITY_001",
                                category=RealityCheckCategory.DATA_QUALITY,
                                severity=RealityCheckSeverity.HIGH,
                                status="fail",
                                message=f"High missing target values: {target_missing:.2%}",
                                details={"target_missing_percentage": target_missing},
                                recommendations=["Clean target data", "Implement target imputation"],
                                timestamp=time.time(),
                                execution_time_ms=1.0
                            ))
                    else:
                        results.append(RealityCheckResult(
                            check_id="TARGET_AVAILABILITY_001",
                            category=RealityCheckCategory.DATA_QUALITY,
                            severity=RealityCheckSeverity.CRITICAL,
                            status="fail",
                            message=f"Target column '{target_col}' not found in data",
                            details={"target_column": target_col, "available_columns": list(data.columns)},
                            recommendations=["Verify target column name", "Check data preprocessing pipeline"],
                            timestamp=time.time(),
                            execution_time_ms=1.0
                        ))
            
        except Exception as e:
            results.append(RealityCheckResult(
                check_id="DATA_VALIDATION_ERROR",
                category=RealityCheckCategory.DATA_QUALITY,
                severity=RealityCheckSeverity.HIGH,
                status="fail",
                message=f"Data validation error: {str(e)}",
                details={"error": str(e)},
                recommendations=["Check data format and structure"],
                timestamp=time.time(),
                execution_time_ms=1.0
            ))
        
        return results
    
    def _validate_algorithm_reality(self, context: Dict[str, Any]) -> List[RealityCheckResult]:
        """Validate algorithm availability and compatibility"""
        results = []
        
        try:
            # Check required algorithm availability
            if "algorithm" in context:
                algorithm = context["algorithm"]
                
                # Map algorithms to required libraries
                algorithm_library_map = {
                    "random_forest": ["sklearn"],
                    "gradient_boosting": ["sklearn"],
                    "xgboost": ["xgboost"],
                    "catboost": ["catboost"],
                    "lightgbm": ["lightgbm"],
                    "svm": ["sklearn"],
                    "linear_regression": ["sklearn"],
                    "logistic_regression": ["sklearn"]
                }
                
                required_libs = algorithm_library_map.get(algorithm, [])
                
                for lib in required_libs:
                    if not self.algorithm_availability.get(lib, False):
                        results.append(RealityCheckResult(
                            check_id=f"ALGORITHM_AVAILABILITY_{lib.upper()}",
                            category=RealityCheckCategory.ALGORITHM_AVAILABILITY,
                            severity=RealityCheckSeverity.CRITICAL,
                            status="fail",
                            message=f"Required library '{lib}' not available for algorithm '{algorithm}'",
                            details={"algorithm": algorithm, "missing_library": lib},
                            recommendations=[f"Install {lib} library", "Check environment setup"],
                            timestamp=time.time(),
                            execution_time_ms=1.0
                        ))
                    else:
                        results.append(RealityCheckResult(
                            check_id=f"ALGORITHM_AVAILABILITY_{lib.upper()}_OK",
                            category=RealityCheckCategory.ALGORITHM_AVAILABILITY,
                            severity=RealityCheckSeverity.INFO,
                            status="pass",
                            message=f"Library '{lib}' available (version: {self.library_versions.get(lib, 'unknown')})",
                            details={"library": lib, "version": self.library_versions.get(lib)},
                            recommendations=[],
                            timestamp=time.time(),
                            execution_time_ms=1.0
                        ))
            
            # Check core ML libraries
            core_libraries = ["numpy", "pandas", "scipy"]
            for lib in core_libraries:
                if not self.algorithm_availability.get(lib, False):
                    results.append(RealityCheckResult(
                        check_id=f"CORE_LIBRARY_{lib.upper()}",
                        category=RealityCheckCategory.ALGORITHM_AVAILABILITY,
                        severity=RealityCheckSeverity.CRITICAL,
                        status="fail",
                        message=f"Core library '{lib}' not available",
                        details={"library": lib},
                        recommendations=[f"Install {lib} library"],
                        timestamp=time.time(),
                        execution_time_ms=1.0
                    ))
            
        except Exception as e:
            results.append(RealityCheckResult(
                check_id="ALGORITHM_CHECK_ERROR",
                category=RealityCheckCategory.ALGORITHM_AVAILABILITY,
                severity=RealityCheckSeverity.HIGH,
                status="fail",
                message=f"Algorithm validation error: {str(e)}",
                details={"error": str(e)},
                recommendations=["Check algorithm configuration"],
                timestamp=time.time(),
                execution_time_ms=1.0
            ))
        
        return results
    
    def _validate_resource_reality(self, context: Dict[str, Any]) -> List[RealityCheckResult]:
        """Validate computational resource availability"""
        results = []
        
        try:
            # Memory availability check
            memory = psutil.virtual_memory()
            available_memory_gb = memory.available / (1024**3)
            memory_usage_percent = memory.percent
            
            if available_memory_gb < self.resource_thresholds["min_available_memory_gb"]:
                results.append(RealityCheckResult(
                    check_id="MEMORY_AVAILABILITY_001",
                    category=RealityCheckCategory.RESOURCE_AVAILABILITY,
                    severity=RealityCheckSeverity.CRITICAL,
                    status="fail",
                    message=f"Insufficient available memory: {available_memory_gb:.2f}GB",
                    details={"available_memory_gb": available_memory_gb, "minimum_required": self.resource_thresholds["min_available_memory_gb"]},
                    recommendations=["Free up memory", "Close unnecessary applications", "Consider upgrading RAM"],
                    timestamp=time.time(),
                    execution_time_ms=1.0
                ))
            elif memory_usage_percent > self.resource_thresholds["memory_usage_threshold"] * 100:
                results.append(RealityCheckResult(
                    check_id="MEMORY_USAGE_001",
                    category=RealityCheckCategory.RESOURCE_AVAILABILITY,
                    severity=RealityCheckSeverity.HIGH,
                    status="warning",
                    message=f"High memory usage: {memory_usage_percent:.1f}%",
                    details={"memory_usage_percent": memory_usage_percent},
                    recommendations=["Monitor memory usage during operation", "Consider garbage collection"],
                    timestamp=time.time(),
                    execution_time_ms=1.0
                ))
            else:
                results.append(RealityCheckResult(
                    check_id="MEMORY_AVAILABILITY_OK",
                    category=RealityCheckCategory.RESOURCE_AVAILABILITY,
                    severity=RealityCheckSeverity.INFO,
                    status="pass",
                    message=f"Memory availability acceptable: {available_memory_gb:.2f}GB available",
                    details={"available_memory_gb": available_memory_gb, "usage_percent": memory_usage_percent},
                    recommendations=[],
                    timestamp=time.time(),
                    execution_time_ms=1.0
                ))
            
            # CPU availability check
            cpu_usage = psutil.cpu_percent(interval=0.1)
            if cpu_usage > self.resource_thresholds["cpu_usage_threshold"] * 100:
                results.append(RealityCheckResult(
                    check_id="CPU_USAGE_001",
                    category=RealityCheckCategory.RESOURCE_AVAILABILITY,
                    severity=RealityCheckSeverity.MEDIUM,
                    status="warning",
                    message=f"High CPU usage: {cpu_usage:.1f}%",
                    details={"cpu_usage_percent": cpu_usage},
                    recommendations=["Monitor CPU usage during operation", "Consider load balancing"],
                    timestamp=time.time(),
                    execution_time_ms=100.0
                ))
            
            # Disk space check
            disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent
            if disk_usage_percent > self.resource_thresholds["disk_usage_threshold"] * 100:
                results.append(RealityCheckResult(
                    check_id="DISK_SPACE_001",
                    category=RealityCheckCategory.RESOURCE_AVAILABILITY,
                    severity=RealityCheckSeverity.HIGH,
                    status="fail",
                    message=f"Low disk space: {disk_usage_percent:.1f}% used",
                    details={"disk_usage_percent": disk_usage_percent},
                    recommendations=["Free up disk space", "Clean temporary files"],
                    timestamp=time.time(),
                    execution_time_ms=1.0
                ))
            
        except Exception as e:
            results.append(RealityCheckResult(
                check_id="RESOURCE_CHECK_ERROR",
                category=RealityCheckCategory.RESOURCE_AVAILABILITY,
                severity=RealityCheckSeverity.HIGH,
                status="fail",
                message=f"Resource validation error: {str(e)}",
                details={"error": str(e)},
                recommendations=["Check system monitoring tools"],
                timestamp=time.time(),
                execution_time_ms=1.0
            ))
        
        return results
    
    def _validate_training_environment_reality(self, context: Dict[str, Any]) -> List[RealityCheckResult]:
        """Validate training environment readiness"""
        results = []
        
        try:
            # Training configuration validation
            if "hyperparameters" in context:
                hyperparams = context["hyperparameters"]
                
                # Learning rate validation
                if "learning_rate" in hyperparams:
                    lr = hyperparams["learning_rate"]
                    if lr <= 0 or lr > 1:
                        results.append(RealityCheckResult(
                            check_id="HYPERPARAMETER_LR_001",
                            category=RealityCheckCategory.TRAINING_ENVIRONMENT,
                            severity=RealityCheckSeverity.HIGH,
                            status="fail",
                            message=f"Invalid learning rate: {lr}",
                            details={"learning_rate": lr, "valid_range": "(0, 1]"},
                            recommendations=["Set learning rate between 0.0001 and 0.1"],
                            timestamp=time.time(),
                            execution_time_ms=1.0
                        ))
                    elif lr > 0.5:
                        results.append(RealityCheckResult(
                            check_id="HYPERPARAMETER_LR_002",
                            category=RealityCheckCategory.TRAINING_ENVIRONMENT,
                            severity=RealityCheckSeverity.MEDIUM,
                            status="warning",
                            message=f"Very high learning rate: {lr}",
                            details={"learning_rate": lr},
                            recommendations=["Consider reducing learning rate for stability"],
                            timestamp=time.time(),
                            execution_time_ms=1.0
                        ))
                
                # Batch size validation
                if "batch_size" in hyperparams:
                    batch_size = hyperparams["batch_size"]
                    if batch_size <= 0:
                        results.append(RealityCheckResult(
                            check_id="HYPERPARAMETER_BATCH_001",
                            category=RealityCheckCategory.TRAINING_ENVIRONMENT,
                            severity=RealityCheckSeverity.HIGH,
                            status="fail",
                            message=f"Invalid batch size: {batch_size}",
                            details={"batch_size": batch_size},
                            recommendations=["Set positive batch size"],
                            timestamp=time.time(),
                            execution_time_ms=1.0
                        ))
                    elif batch_size > 1024:
                        results.append(RealityCheckResult(
                            check_id="HYPERPARAMETER_BATCH_002",
                            category=RealityCheckCategory.TRAINING_ENVIRONMENT,
                            severity=RealityCheckSeverity.MEDIUM,
                            status="warning",
                            message=f"Very large batch size: {batch_size}",
                            details={"batch_size": batch_size},
                            recommendations=["Large batch sizes may require more memory and affect convergence"],
                            timestamp=time.time(),
                            execution_time_ms=1.0
                        ))
            
            # Training data size vs memory check
            if "training_data" in context and isinstance(context["training_data"], pd.DataFrame):
                data = context["training_data"]
                estimated_memory_gb = (data.memory_usage(deep=True).sum()) / (1024**3)
                available_memory_gb = psutil.virtual_memory().available / (1024**3)
                
                if estimated_memory_gb > available_memory_gb * 0.5:  # Uses more than 50% of available memory
                    results.append(RealityCheckResult(
                        check_id="TRAINING_MEMORY_001",
                        category=RealityCheckCategory.TRAINING_ENVIRONMENT,
                        severity=RealityCheckSeverity.HIGH,
                        status="warning",
                        message=f"Training data may consume significant memory: {estimated_memory_gb:.2f}GB",
                        details={"estimated_memory_gb": estimated_memory_gb, "available_memory_gb": available_memory_gb},
                        recommendations=["Consider data batching", "Monitor memory usage", "Implement data streaming"],
                        timestamp=time.time(),
                        execution_time_ms=5.0
                    ))
            
        except Exception as e:
            results.append(RealityCheckResult(
                check_id="TRAINING_ENV_CHECK_ERROR",
                category=RealityCheckCategory.TRAINING_ENVIRONMENT,
                severity=RealityCheckSeverity.HIGH,
                status="fail",
                message=f"Training environment validation error: {str(e)}",
                details={"error": str(e)},
                recommendations=["Check training configuration"],
                timestamp=time.time(),
                execution_time_ms=1.0
            ))
        
        return results
    
    def _validate_deployment_readiness_reality(self, context: Dict[str, Any]) -> List[RealityCheckResult]:
        """Validate deployment readiness for model inference"""
        results = []
        
        try:
            # Model availability check
            if "model_name" in context:
                model_name = context["model_name"]
                # This would check if model exists in model registry/storage
                # For now, we'll simulate the check
                results.append(RealityCheckResult(
                    check_id="MODEL_AVAILABILITY_001",
                    category=RealityCheckCategory.DEPLOYMENT_READINESS,
                    severity=RealityCheckSeverity.INFO,
                    status="pass",
                    message=f"Model deployment readiness check passed for {model_name}",
                    details={"model_name": model_name},
                    recommendations=[],
                    timestamp=time.time(),
                    execution_time_ms=1.0
                ))
            
            # Inference latency check
            if context.get("real_time_required", False):
                # Simulate latency check
                estimated_latency_ms = 50.0  # This would be calculated based on model complexity
                max_acceptable_latency = context.get("max_latency_ms", self.resource_thresholds["min_inference_latency_ms"])
                
                if estimated_latency_ms > max_acceptable_latency:
                    results.append(RealityCheckResult(
                        check_id="INFERENCE_LATENCY_001",
                        category=RealityCheckCategory.DEPLOYMENT_READINESS,
                        severity=RealityCheckSeverity.HIGH,
                        status="fail",
                        message=f"Estimated inference latency too high: {estimated_latency_ms}ms",
                        details={"estimated_latency_ms": estimated_latency_ms, "max_acceptable_ms": max_acceptable_latency},
                        recommendations=["Optimize model for inference", "Consider model quantization", "Use faster algorithms"],
                        timestamp=time.time(),
                        execution_time_ms=1.0
                    ))
                else:
                    results.append(RealityCheckResult(
                        check_id="INFERENCE_LATENCY_002",
                        category=RealityCheckCategory.DEPLOYMENT_READINESS,
                        severity=RealityCheckSeverity.INFO,
                        status="pass",
                        message=f"Inference latency acceptable: {estimated_latency_ms}ms",
                        details={"estimated_latency_ms": estimated_latency_ms},
                        recommendations=[],
                        timestamp=time.time(),
                        execution_time_ms=1.0
                    ))
            
        except Exception as e:
            results.append(RealityCheckResult(
                check_id="DEPLOYMENT_CHECK_ERROR",
                category=RealityCheckCategory.DEPLOYMENT_READINESS,
                severity=RealityCheckSeverity.HIGH,
                status="fail",
                message=f"Deployment readiness validation error: {str(e)}",
                details={"error": str(e)},
                recommendations=["Check deployment configuration"],
                timestamp=time.time(),
                execution_time_ms=1.0
            ))
        
        return results
    
    def _validate_real_time_capability_reality(self, context: Dict[str, Any]) -> List[RealityCheckResult]:
        """Validate real-time processing capabilities"""
        results = []
        
        try:
            # System load check for real-time operations
            load_avg = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
            cpu_count = psutil.cpu_count()
            
            if load_avg > cpu_count * 0.8:  # High system load
                results.append(RealityCheckResult(
                    check_id="REALTIME_LOAD_001",
                    category=RealityCheckCategory.REAL_TIME_CAPABILITY,
                    severity=RealityCheckSeverity.HIGH,
                    status="warning",
                    message=f"High system load may affect real-time performance: {load_avg}",
                    details={"load_average": load_avg, "cpu_count": cpu_count},
                    recommendations=["Monitor system performance", "Consider load balancing"],
                    timestamp=time.time(),
                    execution_time_ms=1.0
                ))
            
            # Network connectivity check (for real-time data)
            if context.get("requires_network", False):
                results.append(RealityCheckResult(
                    check_id="REALTIME_NETWORK_001",
                    category=RealityCheckCategory.REAL_TIME_CAPABILITY,
                    severity=RealityCheckSeverity.INFO,
                    status="pass",
                    message="Network connectivity assumed available",
                    details={},
                    recommendations=["Monitor network latency for real-time data feeds"],
                    timestamp=time.time(),
                    execution_time_ms=1.0
                ))
            
        except Exception as e:
            results.append(RealityCheckResult(
                check_id="REALTIME_CHECK_ERROR",
                category=RealityCheckCategory.REAL_TIME_CAPABILITY,
                severity=RealityCheckSeverity.MEDIUM,
                status="warning",
                message=f"Real-time capability validation error: {str(e)}",
                details={"error": str(e)},
                recommendations=["Check system monitoring capabilities"],
                timestamp=time.time(),
                execution_time_ms=1.0
            ))
        
        return results
    
    def _generate_overall_recommendations(self, check_results: List[RealityCheckResult]) -> List[str]:
        """Generate overall recommendations based on all check results"""
        recommendations = []
        
        # Critical failures
        critical_failures = [r for r in check_results if r.status == "fail" and r.severity == RealityCheckSeverity.CRITICAL]
        if critical_failures:
            recommendations.append("🚨 CRITICAL: Address critical failures before proceeding")
            for failure in critical_failures[:3]:  # Top 3 critical issues
                recommendations.extend(failure.recommendations)
        
        # High severity issues
        high_issues = [r for r in check_results if r.severity == RealityCheckSeverity.HIGH and r.status in ["fail", "warning"]]
        if high_issues:
            recommendations.append("⚠️ HIGH PRIORITY: Address high-severity issues")
            for issue in high_issues[:2]:  # Top 2 high priority issues
                recommendations.extend(issue.recommendations)
        
        # Resource optimization
        resource_issues = [r for r in check_results if r.category == RealityCheckCategory.RESOURCE_AVAILABILITY]
        if any(r.status in ["fail", "warning"] for r in resource_issues):
            recommendations.append("💾 Optimize system resources before heavy ML operations")
        
        # Data quality
        data_issues = [r for r in check_results if r.category == RealityCheckCategory.DATA_QUALITY]
        if any(r.status in ["fail", "warning"] for r in data_issues):
            recommendations.append("📊 Improve data quality for better ML performance")
        
        return list(set(recommendations))  # Remove duplicates
    
    def _calculate_risk_level(self, check_results: List[RealityCheckResult]) -> str:
        """Calculate overall risk level based on check results"""
        critical_count = len([r for r in check_results if r.severity == RealityCheckSeverity.CRITICAL and r.status == "fail"])
        high_count = len([r for r in check_results if r.severity == RealityCheckSeverity.HIGH and r.status == "fail"])
        warning_count = len([r for r in check_results if r.status == "warning"])
        
        if critical_count > 0:
            return "critical"
        elif high_count > 2:
            return "high"
        elif high_count > 0 or warning_count > 3:
            return "medium"
        elif warning_count > 0:
            return "low"
        else:
            return "minimal"
    
    def get_reality_check_statistics(self) -> Dict[str, Any]:
        """Get comprehensive reality check statistics"""
        recent_checks = [c for c in self.check_history if time.time() - c.timestamp < 86400]  # Last 24 hours
        
        category_stats = {}
        for check in recent_checks:
            category = check.category.value
            if category not in category_stats:
                category_stats[category] = {"total": 0, "passed": 0, "failed": 0, "warnings": 0}
            
            category_stats[category]["total"] += 1
            if check.status == "pass":
                category_stats[category]["passed"] += 1
            elif check.status == "fail":
                category_stats[category]["failed"] += 1
            elif check.status == "warning":
                category_stats[category]["warnings"] += 1
        
        return {
            "total_checks_24h": len(recent_checks),
            "overall_metrics": self.check_metrics,
            "category_breakdown": category_stats,
            "system_baseline": self.system_baseline,
            "algorithm_availability": self.algorithm_availability,
            "library_versions": self.library_versions,
            "resource_thresholds": self.resource_thresholds,
            "check_success_rate": self.check_metrics["passed_checks"] / max(self.check_metrics["total_checks"], 1),
            "last_updated": datetime.now().isoformat()
        }


# Global ML-Processing Reality Checker instance
ml_processing_reality_checker = AiBrainMLProcessingRealityChecker("ml-processing")


def get_ml_reality_checker() -> AiBrainMLProcessingRealityChecker:
    """Get the global ML-Processing Reality Checker instance"""
    return ml_processing_reality_checker


def perform_reality_check(operation_type: str, operation_context: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function for comprehensive reality check"""
    return ml_processing_reality_checker.perform_comprehensive_reality_check(operation_type, operation_context)