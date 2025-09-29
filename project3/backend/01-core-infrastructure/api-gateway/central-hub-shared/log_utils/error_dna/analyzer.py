"""
ErrorDNA Analyzer - Intelligent error pattern analysis dan classification
Menganalisis error patterns untuk predictive issue detection
"""

import re
import hashlib
import logging as python_logging
from typing import Any, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import json


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error category classification"""
    DATABASE = "database"
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    EXTERNAL_SERVICE = "external_service"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM_RESOURCE = "system_resource"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


@dataclass
class ErrorPattern:
    """Error pattern definition"""
    pattern_id: str
    error_signature: str
    category: ErrorCategory
    severity: ErrorSeverity
    regex_patterns: List[str] = field(default_factory=list)
    keywords: Set[str] = field(default_factory=set)
    stack_trace_patterns: List[str] = field(default_factory=list)
    frequency: int = 0
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    affected_services: Set[str] = field(default_factory=set)
    correlation_patterns: List[str] = field(default_factory=list)


@dataclass
class ErrorOccurrence:
    """Individual error occurrence"""
    error_id: str
    service_name: str
    timestamp: datetime
    error_message: str
    stack_trace: Optional[str] = None
    error_type: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None
    pattern_id: Optional[str] = None
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    category: ErrorCategory = ErrorCategory.UNKNOWN


@dataclass
class ErrorAnalysis:
    """Error analysis result"""
    error_occurrence: ErrorOccurrence
    matched_patterns: List[ErrorPattern]
    confidence_score: float
    suggested_actions: List[str] = field(default_factory=list)
    related_errors: List[str] = field(default_factory=list)
    trend_analysis: Dict[str, Any] = field(default_factory=dict)


class ErrorDNAAnalyzer:
    """
    Advanced error pattern analyzer yang dapat:
    - Mengidentifikasi error patterns secara otomatis
    - Mengklasifikasikan error berdasarkan severity dan category
    - Melakukan trend analysis untuk predictive maintenance
    - Memberikan suggested actions untuk error resolution
    """

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = python_logging.getLogger(f"{service_name}.error_dna")

        # Error storage
        self.error_occurrences: deque = deque(maxlen=10000)
        self.error_patterns: Dict[str, ErrorPattern] = {}

        # Analysis caches
        self.pattern_cache: Dict[str, str] = {}  # error_signature -> pattern_id
        self.trend_cache: Dict[str, Dict] = {}

        # Load built-in patterns
        self._load_builtin_patterns()

    def _load_builtin_patterns(self):
        """Load built-in error patterns"""
        builtin_patterns = [
            # Database errors
            {
                "pattern_id": "db_connection_timeout",
                "error_signature": "database_connection_timeout",
                "category": ErrorCategory.DATABASE,
                "severity": ErrorSeverity.HIGH,
                "regex_patterns": [
                    r"connection.*timeout",
                    r"database.*timeout",
                    r"pool.*timeout"
                ],
                "keywords": {"connection", "timeout", "database", "pool"},
                "stack_trace_patterns": ["asyncpg", "psycopg", "sqlalchemy"]
            },
            {
                "pattern_id": "db_connection_refused",
                "error_signature": "database_connection_refused",
                "category": ErrorCategory.DATABASE,
                "severity": ErrorSeverity.CRITICAL,
                "regex_patterns": [
                    r"connection.*refused",
                    r"could not connect",
                    r"database.*unavailable"
                ],
                "keywords": {"connection", "refused", "database", "unavailable"}
            },

            # Network errors
            {
                "pattern_id": "network_timeout",
                "error_signature": "network_request_timeout",
                "category": ErrorCategory.NETWORK,
                "severity": ErrorSeverity.MEDIUM,
                "regex_patterns": [
                    r"request.*timeout",
                    r"http.*timeout",
                    r"connection.*timeout"
                ],
                "keywords": {"request", "timeout", "http", "network"}
            },
            {
                "pattern_id": "network_connection_error",
                "error_signature": "network_connection_error",
                "category": ErrorCategory.NETWORK,
                "severity": ErrorSeverity.HIGH,
                "regex_patterns": [
                    r"connection.*error",
                    r"network.*unreachable",
                    r"host.*unreachable"
                ],
                "keywords": {"connection", "error", "network", "unreachable", "host"}
            },

            # Authentication errors
            {
                "pattern_id": "auth_token_invalid",
                "error_signature": "authentication_token_invalid",
                "category": ErrorCategory.AUTHENTICATION,
                "severity": ErrorSeverity.MEDIUM,
                "regex_patterns": [
                    r"token.*invalid",
                    r"token.*expired",
                    r"authentication.*failed"
                ],
                "keywords": {"token", "invalid", "expired", "authentication", "failed"}
            },
            {
                "pattern_id": "auth_unauthorized",
                "error_signature": "authorization_failed",
                "category": ErrorCategory.AUTHENTICATION,
                "severity": ErrorSeverity.MEDIUM,
                "regex_patterns": [
                    r"unauthorized",
                    r"access.*denied",
                    r"permission.*denied"
                ],
                "keywords": {"unauthorized", "access", "denied", "permission"}
            },

            # Validation errors
            {
                "pattern_id": "validation_schema",
                "error_signature": "schema_validation_error",
                "category": ErrorCategory.VALIDATION,
                "severity": ErrorSeverity.LOW,
                "regex_patterns": [
                    r"validation.*error",
                    r"schema.*error",
                    r"invalid.*format"
                ],
                "keywords": {"validation", "schema", "invalid", "format"}
            },

            # External service errors
            {
                "pattern_id": "external_api_error",
                "error_signature": "external_service_error",
                "category": ErrorCategory.EXTERNAL_SERVICE,
                "severity": ErrorSeverity.MEDIUM,
                "regex_patterns": [
                    r"external.*api.*error",
                    r"service.*unavailable",
                    r"api.*error"
                ],
                "keywords": {"external", "api", "service", "unavailable"}
            },

            # System resource errors
            {
                "pattern_id": "memory_error",
                "error_signature": "memory_exhaustion",
                "category": ErrorCategory.SYSTEM_RESOURCE,
                "severity": ErrorSeverity.CRITICAL,
                "regex_patterns": [
                    r"out of memory",
                    r"memory.*error",
                    r"allocation.*failed"
                ],
                "keywords": {"memory", "allocation", "failed", "exhaustion"}
            },
            {
                "pattern_id": "disk_space_error",
                "error_signature": "disk_space_exhaustion",
                "category": ErrorCategory.SYSTEM_RESOURCE,
                "severity": ErrorSeverity.HIGH,
                "regex_patterns": [
                    r"no space left",
                    r"disk.*full",
                    r"storage.*full"
                ],
                "keywords": {"space", "disk", "full", "storage"}
            }
        ]

        for pattern_data in builtin_patterns:
            pattern = ErrorPattern(**pattern_data)
            self.error_patterns[pattern.pattern_id] = pattern

    def analyze_error(self,
                     error_message: str,
                     stack_trace: Optional[str] = None,
                     error_type: Optional[str] = None,
                     context: Optional[Dict[str, Any]] = None,
                     user_id: Optional[str] = None,
                     correlation_id: Optional[str] = None) -> ErrorAnalysis:
        """Analyze error dan return comprehensive analysis"""

        # Create error occurrence
        error_occurrence = ErrorOccurrence(
            error_id=self._generate_error_id(error_message, stack_trace),
            service_name=self.service_name,
            timestamp=datetime.utcnow(),
            error_message=error_message,
            stack_trace=stack_trace,
            error_type=error_type,
            context=context or {},
            user_id=user_id,
            correlation_id=correlation_id
        )

        # Find matching patterns
        matched_patterns = self._find_matching_patterns(error_occurrence)

        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(error_occurrence, matched_patterns)

        # Update pattern frequencies
        self._update_pattern_frequencies(matched_patterns)

        # Set category and severity based on best match
        if matched_patterns:
            best_match = matched_patterns[0]
            error_occurrence.pattern_id = best_match.pattern_id
            error_occurrence.category = best_match.category
            error_occurrence.severity = best_match.severity

        # Store error occurrence
        self.error_occurrences.append(error_occurrence)

        # Generate suggested actions
        suggested_actions = self._generate_suggested_actions(error_occurrence, matched_patterns)

        # Find related errors
        related_errors = self._find_related_errors(error_occurrence)

        # Perform trend analysis
        trend_analysis = self._perform_trend_analysis(error_occurrence)

        # Create analysis result
        analysis = ErrorAnalysis(
            error_occurrence=error_occurrence,
            matched_patterns=matched_patterns,
            confidence_score=confidence_score,
            suggested_actions=suggested_actions,
            related_errors=related_errors,
            trend_analysis=trend_analysis
        )

        self.logger.info(f"Analyzed error {error_occurrence.error_id} with confidence {confidence_score:.2f}")
        return analysis

    def _generate_error_id(self, error_message: str, stack_trace: Optional[str] = None) -> str:
        """Generate unique error ID"""
        content = error_message + (stack_trace or "")
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _find_matching_patterns(self, error_occurrence: ErrorOccurrence) -> List[ErrorPattern]:
        """Find patterns that match the error"""
        matched_patterns = []

        error_text = error_occurrence.error_message.lower()
        stack_text = (error_occurrence.stack_trace or "").lower()
        full_text = error_text + " " + stack_text

        for pattern in self.error_patterns.values():
            match_score = 0

            # Check regex patterns
            for regex_pattern in pattern.regex_patterns:
                if re.search(regex_pattern, full_text, re.IGNORECASE):
                    match_score += 2

            # Check keywords
            words = set(full_text.split())
            keyword_matches = len(words.intersection(pattern.keywords))
            match_score += keyword_matches

            # Check stack trace patterns
            for stack_pattern in pattern.stack_trace_patterns:
                if stack_pattern.lower() in stack_text:
                    match_score += 1

            # If we have a match, add to results
            if match_score > 0:
                # Store match score in pattern for sorting
                pattern.match_score = match_score
                matched_patterns.append(pattern)

        # Sort by match score (highest first)
        matched_patterns.sort(key=lambda p: getattr(p, 'match_score', 0), reverse=True)

        return matched_patterns

    def _calculate_confidence_score(self, error_occurrence: ErrorOccurrence,
                                  matched_patterns: List[ErrorPattern]) -> float:
        """Calculate confidence score for error classification"""
        if not matched_patterns:
            return 0.0

        best_pattern = matched_patterns[0]
        match_score = getattr(best_pattern, 'match_score', 0)

        # Base confidence from match score
        base_confidence = min(match_score / 5.0, 1.0)  # Normalize to 0-1

        # Boost confidence if multiple patterns match
        pattern_boost = min(len(matched_patterns) * 0.1, 0.3)

        # Boost confidence if we've seen this pattern before
        frequency_boost = min(best_pattern.frequency * 0.01, 0.2)

        # Final confidence score
        confidence = min(base_confidence + pattern_boost + frequency_boost, 1.0)

        return confidence

    def _update_pattern_frequencies(self, matched_patterns: List[ErrorPattern]):
        """Update pattern frequencies"""
        current_time = datetime.utcnow()

        for pattern in matched_patterns:
            pattern.frequency += 1
            pattern.last_seen = current_time
            pattern.affected_services.add(self.service_name)

            if pattern.first_seen is None:
                pattern.first_seen = current_time

    def _generate_suggested_actions(self, error_occurrence: ErrorOccurrence,
                                  matched_patterns: List[ErrorPattern]) -> List[str]:
        """Generate suggested actions for error resolution"""
        suggestions = []

        if not matched_patterns:
            suggestions.append("Investigate error message and stack trace for clues")
            suggestions.append("Check service logs for related errors")
            return suggestions

        best_pattern = matched_patterns[0]

        # Category-specific suggestions
        if best_pattern.category == ErrorCategory.DATABASE:
            suggestions.extend([
                "Check database connection pool status",
                "Verify database server availability",
                "Review database query performance",
                "Check for database locks or deadlocks"
            ])

        elif best_pattern.category == ErrorCategory.NETWORK:
            suggestions.extend([
                "Verify network connectivity to external services",
                "Check DNS resolution",
                "Review network timeouts configuration",
                "Test external service availability"
            ])

        elif best_pattern.category == ErrorCategory.AUTHENTICATION:
            suggestions.extend([
                "Verify authentication token validity",
                "Check user permissions",
                "Review authentication configuration",
                "Validate token expiration settings"
            ])

        elif best_pattern.category == ErrorCategory.EXTERNAL_SERVICE:
            suggestions.extend([
                "Check external service status",
                "Review API rate limits",
                "Verify service credentials",
                "Implement circuit breaker if not present"
            ])

        elif best_pattern.category == ErrorCategory.SYSTEM_RESOURCE:
            suggestions.extend([
                "Monitor system resource usage",
                "Check memory/disk space availability",
                "Review resource allocation",
                "Consider scaling resources"
            ])

        # Severity-specific suggestions
        if best_pattern.severity == ErrorSeverity.CRITICAL:
            suggestions.insert(0, "⚠️ CRITICAL: Immediate attention required")
            suggestions.append("Consider alerting on-call team")

        elif best_pattern.severity == ErrorSeverity.HIGH:
            suggestions.insert(0, "🔥 HIGH PRIORITY: Address as soon as possible")

        return suggestions

    def _find_related_errors(self, error_occurrence: ErrorOccurrence) -> List[str]:
        """Find related errors based on correlation ID, user ID, or time proximity"""
        related_errors = []

        # Look for errors with same correlation ID
        if error_occurrence.correlation_id:
            for other_error in self.error_occurrences:
                if (other_error.correlation_id == error_occurrence.correlation_id and
                    other_error.error_id != error_occurrence.error_id):
                    related_errors.append(other_error.error_id)

        # Look for errors from same user
        if error_occurrence.user_id and len(related_errors) < 5:
            for other_error in self.error_occurrences:
                if (other_error.user_id == error_occurrence.user_id and
                    other_error.error_id != error_occurrence.error_id and
                    other_error.error_id not in related_errors):
                    time_diff = abs((other_error.timestamp - error_occurrence.timestamp).total_seconds())
                    if time_diff < 300:  # Within 5 minutes
                        related_errors.append(other_error.error_id)

        return related_errors[:5]  # Limit to 5 related errors

    def _perform_trend_analysis(self, error_occurrence: ErrorOccurrence) -> Dict[str, Any]:
        """Perform trend analysis for the error pattern"""
        if not error_occurrence.pattern_id:
            return {}

        pattern_id = error_occurrence.pattern_id
        current_time = datetime.utcnow()

        # Get errors for this pattern in last 24 hours
        day_ago = current_time - timedelta(days=1)
        recent_errors = [
            err for err in self.error_occurrences
            if err.pattern_id == pattern_id and err.timestamp >= day_ago
        ]

        if len(recent_errors) < 2:
            return {"trend": "insufficient_data"}

        # Calculate hourly error counts
        hourly_counts = defaultdict(int)
        for error in recent_errors:
            hour = error.timestamp.replace(minute=0, second=0, microsecond=0)
            hourly_counts[hour] += 1

        # Analyze trend
        counts = list(hourly_counts.values())
        if len(counts) >= 3:
            recent_avg = sum(counts[-3:]) / 3
            earlier_avg = sum(counts[:-3]) / max(len(counts) - 3, 1)

            if recent_avg > earlier_avg * 1.5:
                trend = "increasing"
                severity = "high" if recent_avg > earlier_avg * 2 else "medium"
            elif recent_avg < earlier_avg * 0.5:
                trend = "decreasing"
                severity = "low"
            else:
                trend = "stable"
                severity = "low"
        else:
            trend = "stable"
            severity = "low"

        return {
            "trend": trend,
            "severity": severity,
            "count_24h": len(recent_errors),
            "avg_per_hour": len(recent_errors) / 24,
            "peak_hour_count": max(counts) if counts else 0
        }

    def get_error_statistics(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive error statistics"""
        current_time = datetime.utcnow()
        cutoff_time = current_time - timedelta(hours=time_window_hours)

        recent_errors = [
            err for err in self.error_occurrences
            if err.timestamp >= cutoff_time
        ]

        # Category statistics
        category_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        pattern_counts = defaultdict(int)

        for error in recent_errors:
            category_counts[error.category.value] += 1
            severity_counts[error.severity.value] += 1
            if error.pattern_id:
                pattern_counts[error.pattern_id] += 1

        # Top error patterns
        top_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "time_window_hours": time_window_hours,
            "total_errors": len(recent_errors),
            "unique_patterns": len(pattern_counts),
            "category_breakdown": dict(category_counts),
            "severity_breakdown": dict(severity_counts),
            "top_error_patterns": [
                {"pattern_id": pid, "count": count} for pid, count in top_patterns
            ],
            "error_rate_per_hour": len(recent_errors) / time_window_hours
        }

    def get_pattern_details(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific pattern"""
        if pattern_id not in self.error_patterns:
            return None

        pattern = self.error_patterns[pattern_id]

        # Get recent occurrences
        recent_occurrences = [
            err for err in self.error_occurrences
            if err.pattern_id == pattern_id
        ][-10:]  # Last 10 occurrences

        return {
            "pattern_id": pattern.pattern_id,
            "category": pattern.category.value,
            "severity": pattern.severity.value,
            "frequency": pattern.frequency,
            "first_seen": pattern.first_seen.isoformat() if pattern.first_seen else None,
            "last_seen": pattern.last_seen.isoformat() if pattern.last_seen else None,
            "affected_services": list(pattern.affected_services),
            "recent_occurrences": [
                {
                    "error_id": err.error_id,
                    "timestamp": err.timestamp.isoformat(),
                    "service": err.service_name,
                    "message": err.error_message[:100] + "..." if len(err.error_message) > 100 else err.error_message
                }
                for err in recent_occurrences
            ]
        }

    def clear_old_errors(self, older_than_days: int = 7):
        """Clear old error occurrences"""
        cutoff_time = datetime.utcnow() - timedelta(days=older_than_days)

        # Filter out old errors
        self.error_occurrences = deque([
            err for err in self.error_occurrences
            if err.timestamp >= cutoff_time
        ], maxlen=self.error_occurrences.maxlen)

        self.logger.info(f"Cleared errors older than {older_than_days} days")

    def export_error_data(self, format: str = "json") -> Any:
        """Export error data for external analysis"""
        if format.lower() == "json":
            return {
                "service_name": self.service_name,
                "export_timestamp": datetime.utcnow().isoformat(),
                "total_patterns": len(self.error_patterns),
                "total_errors": len(self.error_occurrences),
                "patterns": {
                    pid: {
                        "category": pattern.category.value,
                        "severity": pattern.severity.value,
                        "frequency": pattern.frequency,
                        "first_seen": pattern.first_seen.isoformat() if pattern.first_seen else None,
                        "last_seen": pattern.last_seen.isoformat() if pattern.last_seen else None
                    }
                    for pid, pattern in self.error_patterns.items()
                },
                "statistics": self.get_error_statistics()
            }
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Convenience class for easy import
class ErrorDNA(ErrorDNAAnalyzer):
    """Alias for ErrorDNAAnalyzer for backward compatibility"""
    pass