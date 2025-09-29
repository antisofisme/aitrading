"""
Central Hub - Error DNA Implementation
Self-contained implementation that PROVIDES error analysis for other services
"""

import time
import re
from typing import Dict, List, Optional, Any, Tuple
import logging
from enum import Enum
from dataclasses import dataclass


class ErrorType(Enum):
    """Error type classifications"""
    BUSINESS_ERROR = "business_error"
    TECHNICAL_ERROR = "technical_error"
    NETWORK_ERROR = "network_error"
    AUTH_ERROR = "auth_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    CLIENT_ERROR = "client_error"
    UNKNOWN_ERROR = "unknown_error"


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorAnalysis:
    """Error analysis result"""
    error_id: str
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    confidence: float
    suggested_actions: List[str]
    retryable: bool
    user_facing: bool
    metadata: Dict[str, Any]
    timestamp: int


@dataclass
class RecoveryAction:
    """Recovery action recommendation"""
    action_type: str
    description: str
    parameters: Dict[str, Any]
    timeout_seconds: Optional[int]
    max_attempts: Optional[int]


class ErrorDNAImplementation:
    """
    Self-contained Error DNA implementation for Central Hub
    This becomes the 'shared' component that other services import
    """

    def __init__(self, service_name: str = "central-hub"):
        self.service_name = service_name
        self.logger = logging.getLogger(f"{service_name}.error-dna")

        # Error patterns for classification
        self.error_patterns = self._initialize_error_patterns()

        # Recovery strategies
        self.recovery_strategies = self._initialize_recovery_strategies()

        # Error history for learning
        self.error_history: List[ErrorAnalysis] = []

        # Metrics
        self.metrics = {
            "total_errors_analyzed": 0,
            "errors_by_type": {error_type.value: 0 for error_type in ErrorType},
            "errors_by_severity": {severity.value: 0 for severity in ErrorSeverity},
            "recovery_success_rate": 0,
            "avg_analysis_time_ms": 0
        }

    def _initialize_error_patterns(self) -> Dict[ErrorType, Dict[str, Any]]:
        """Initialize error classification patterns"""
        return {
            ErrorType.BUSINESS_ERROR: {
                "keywords": ["validation", "invalid", "missing", "required", "format", "duplicate", "constraint"],
                "status_codes": [400, 409, 422],
                "severity": ErrorSeverity.MEDIUM,
                "user_facing": True,
                "retryable": False
            },
            ErrorType.TECHNICAL_ERROR: {
                "keywords": ["database", "connection", "timeout", "unavailable", "internal", "server"],
                "status_codes": [500, 502, 503, 504],
                "severity": ErrorSeverity.HIGH,
                "user_facing": False,
                "retryable": True
            },
            ErrorType.NETWORK_ERROR: {
                "keywords": ["network", "socket", "refused", "unreachable", "dns", "host"],
                "status_codes": [502, 503, 504],
                "severity": ErrorSeverity.HIGH,
                "user_facing": False,
                "retryable": True
            },
            ErrorType.AUTH_ERROR: {
                "keywords": ["unauthorized", "forbidden", "token", "expired", "permission", "credentials"],
                "status_codes": [401, 403],
                "severity": ErrorSeverity.MEDIUM,
                "user_facing": True,
                "retryable": False
            },
            ErrorType.RATE_LIMIT_ERROR: {
                "keywords": ["rate", "limit", "quota", "throttle", "too many"],
                "status_codes": [429],
                "severity": ErrorSeverity.MEDIUM,
                "user_facing": False,
                "retryable": True
            },
            ErrorType.CLIENT_ERROR: {
                "keywords": ["bad request", "malformed", "syntax", "parse", "format"],
                "status_codes": [400, 415],
                "severity": ErrorSeverity.LOW,
                "user_facing": True,
                "retryable": False
            }
        }

    def _initialize_recovery_strategies(self) -> Dict[ErrorType, List[RecoveryAction]]:
        """Initialize recovery strategies for each error type"""
        return {
            ErrorType.BUSINESS_ERROR: [
                RecoveryAction("notify_user", "Inform user of validation error", {}, None, None),
                RecoveryAction("log_and_return", "Log error and return user-friendly message", {}, None, None)
            ],
            ErrorType.TECHNICAL_ERROR: [
                RecoveryAction("retry_with_backoff", "Retry with exponential backoff", {"base_delay": 1}, 300, 3),
                RecoveryAction("circuit_breaker", "Open circuit breaker", {"timeout": 60}, None, None),
                RecoveryAction("escalate", "Escalate to monitoring system", {}, None, None)
            ],
            ErrorType.NETWORK_ERROR: [
                RecoveryAction("retry_with_backoff", "Retry with exponential backoff", {"base_delay": 2}, 600, 5),
                RecoveryAction("failover_transport", "Switch to backup transport method", {}, None, None),
                RecoveryAction("cache_fallback", "Use cached data if available", {}, None, None)
            ],
            ErrorType.AUTH_ERROR: [
                RecoveryAction("refresh_token", "Attempt token refresh", {}, 30, 1),
                RecoveryAction("redirect_login", "Redirect to login", {}, None, None)
            ],
            ErrorType.RATE_LIMIT_ERROR: [
                RecoveryAction("exponential_backoff", "Wait and retry", {"base_delay": 60}, 3600, 3),
                RecoveryAction("queue_request", "Queue request for later processing", {}, None, None)
            ],
            ErrorType.CLIENT_ERROR: [
                RecoveryAction("validate_and_reject", "Validate input and reject", {}, None, None),
                RecoveryAction("sanitize_input", "Attempt input sanitization", {}, None, None)
            ]
        }

    def analyze_error(self, error: Any, context: Dict[str, Any] = None) -> ErrorAnalysis:
        """Analyze error and classify it"""
        start_time = time.time()
        context = context or {}

        try:
            # Extract error information
            error_info = self._extract_error_info(error)

            # Classify error
            error_type, confidence = self._classify_error(error_info)

            # Determine severity
            severity = self._determine_severity(error_type, error_info, context)

            # Generate error ID
            error_id = self._generate_error_id()

            # Get suggested actions
            suggested_actions = self._get_suggested_actions(error_type)

            # Create analysis result
            analysis = ErrorAnalysis(
                error_id=error_id,
                error_type=error_type,
                severity=severity,
                message=error_info.get("message", str(error)),
                confidence=confidence,
                suggested_actions=suggested_actions,
                retryable=self.error_patterns[error_type]["retryable"],
                user_facing=self.error_patterns[error_type]["user_facing"],
                metadata={
                    "context": context,
                    "error_info": error_info,
                    "service_name": self.service_name
                },
                timestamp=int(time.time() * 1000)
            )

            # Store in history
            self.error_history.append(analysis)
            self._maintain_history_size()

            # Update metrics
            analysis_time_ms = int((time.time() - start_time) * 1000)
            self._update_metrics(analysis, analysis_time_ms)

            self.logger.info(f"Error analyzed: {error_type.value} (confidence: {confidence:.2f})")
            return analysis

        except Exception as e:
            self.logger.error(f"Failed to analyze error: {e}")
            # Return a fallback analysis
            return self._create_fallback_analysis(error, context)

    def _extract_error_info(self, error: Any) -> Dict[str, Any]:
        """Extract structured information from error"""
        if isinstance(error, Exception):
            return {
                "message": str(error),
                "type": type(error).__name__,
                "args": error.args,
                "status_code": getattr(error, "status_code", None)
            }
        elif isinstance(error, dict):
            return error
        elif isinstance(error, str):
            return {"message": error, "type": "StringError"}
        else:
            return {"message": str(error), "type": "UnknownError"}

    def _classify_error(self, error_info: Dict[str, Any]) -> Tuple[ErrorType, float]:
        """Classify error based on patterns"""
        message = error_info.get("message", "").lower()
        status_code = error_info.get("status_code")

        best_match = ErrorType.UNKNOWN_ERROR
        best_confidence = 0.0

        for error_type, pattern in self.error_patterns.items():
            confidence = 0.0
            total_checks = 0

            # Check keywords
            if pattern.get("keywords"):
                total_checks += 1
                keyword_matches = sum(1 for keyword in pattern["keywords"] if keyword in message)
                if keyword_matches > 0:
                    confidence += keyword_matches / len(pattern["keywords"])

            # Check status codes
            if pattern.get("status_codes") and status_code:
                total_checks += 1
                if status_code in pattern["status_codes"]:
                    confidence += 1.0

            # Calculate final confidence
            if total_checks > 0:
                confidence = confidence / total_checks

                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = error_type

        return best_match, best_confidence

    def _determine_severity(self, error_type: ErrorType, error_info: Dict[str, Any],
                          context: Dict[str, Any]) -> ErrorSeverity:
        """Determine error severity"""
        base_severity = self.error_patterns[error_type]["severity"]

        # Escalate severity based on context
        if context.get("critical_path", False):
            if base_severity == ErrorSeverity.LOW:
                return ErrorSeverity.MEDIUM
            elif base_severity == ErrorSeverity.MEDIUM:
                return ErrorSeverity.HIGH

        # Escalate for repeated errors
        recent_similar_errors = self._count_recent_similar_errors(error_type)
        if recent_similar_errors > 5:
            if base_severity == ErrorSeverity.LOW:
                return ErrorSeverity.MEDIUM
            elif base_severity == ErrorSeverity.MEDIUM:
                return ErrorSeverity.HIGH
            elif base_severity == ErrorSeverity.HIGH:
                return ErrorSeverity.CRITICAL

        return base_severity

    def _get_suggested_actions(self, error_type: ErrorType) -> List[str]:
        """Get suggested recovery actions"""
        strategies = self.recovery_strategies.get(error_type, [])
        return [f"{strategy.action_type}: {strategy.description}" for strategy in strategies]

    def _count_recent_similar_errors(self, error_type: ErrorType,
                                   time_window_minutes: int = 60) -> int:
        """Count recent similar errors"""
        cutoff_time = int(time.time() * 1000) - (time_window_minutes * 60 * 1000)
        return sum(1 for error in self.error_history
                  if error.error_type == error_type and error.timestamp > cutoff_time)

    def _generate_error_id(self) -> str:
        """Generate unique error ID"""
        timestamp = int(time.time() * 1000)
        import random
        random_part = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=6))
        return f"err_{self.service_name}_{timestamp}_{random_part}"

    def _create_fallback_analysis(self, error: Any, context: Dict[str, Any]) -> ErrorAnalysis:
        """Create fallback analysis when main analysis fails"""
        return ErrorAnalysis(
            error_id=self._generate_error_id(),
            error_type=ErrorType.UNKNOWN_ERROR,
            severity=ErrorSeverity.MEDIUM,
            message=str(error),
            confidence=0.0,
            suggested_actions=["log_and_escalate: Log error and escalate to support"],
            retryable=False,
            user_facing=False,
            metadata={"context": context, "fallback": True},
            timestamp=int(time.time() * 1000)
        )

    def _maintain_history_size(self, max_size: int = 1000):
        """Maintain error history size"""
        if len(self.error_history) > max_size:
            self.error_history = self.error_history[-max_size:]

    def _update_metrics(self, analysis: ErrorAnalysis, analysis_time_ms: int):
        """Update analysis metrics"""
        self.metrics["total_errors_analyzed"] += 1
        self.metrics["errors_by_type"][analysis.error_type.value] += 1
        self.metrics["errors_by_severity"][analysis.severity.value] += 1

        # Update average analysis time
        total_time = (self.metrics["avg_analysis_time_ms"] *
                     (self.metrics["total_errors_analyzed"] - 1) + analysis_time_ms)
        self.metrics["avg_analysis_time_ms"] = total_time / self.metrics["total_errors_analyzed"]

    def get_recovery_strategies(self, error_type: ErrorType) -> List[RecoveryAction]:
        """Get recovery strategies for error type"""
        return self.recovery_strategies.get(error_type, [])

    def get_statistics(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """Get error analysis statistics"""
        cutoff_time = int(time.time() * 1000) - (time_window_hours * 3600 * 1000)
        recent_errors = [e for e in self.error_history if e.timestamp > cutoff_time]

        return {
            "total_errors_analyzed": self.metrics["total_errors_analyzed"],
            "recent_errors": len(recent_errors),
            "errors_by_type": self.metrics["errors_by_type"],
            "errors_by_severity": self.metrics["errors_by_severity"],
            "avg_analysis_time_ms": self.metrics["avg_analysis_time_ms"],
            "avg_confidence": (
                sum(e.confidence for e in recent_errors) / len(recent_errors)
                if recent_errors else 0
            )
        }

    async def health_check(self) -> Dict[str, Any]:
        """Health check for Error DNA"""
        stats = self.get_statistics()

        # Determine health based on error patterns
        recent_critical_errors = sum(
            1 for e in self.error_history[-100:]
            if e.severity == ErrorSeverity.CRITICAL
        )

        if recent_critical_errors > 10:
            status = "critical"
        elif recent_critical_errors > 5:
            status = "warning"
        else:
            status = "healthy"

        return {
            "status": status,
            "patterns_loaded": len(self.error_patterns),
            "strategies_loaded": len(self.recovery_strategies),
            "recent_errors_analyzed": stats["recent_errors"],
            "critical_errors_recent": recent_critical_errors
        }


# Export class for use by other services
ErrorDNA = ErrorDNAImplementation