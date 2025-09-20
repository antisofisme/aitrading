"""
Enhanced Error Classification Core - Advanced error categorization for microservices
"""
import traceback
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
from .service_identity_core import get_service_identity, get_service_context

class ErrorSeverity(Enum):
    """Standardized error severity levels"""
    CRITICAL = "critical"      # Service completely unavailable
    HIGH = "high"             # Major functionality impacted
    MEDIUM = "medium"         # Some functionality impacted
    LOW = "low"              # Minor issues, service mostly functional
    INFO = "info"            # Informational, no functional impact

class ErrorCategory(Enum):
    """Standardized error categories across microservices"""
    # Infrastructure errors
    INFRASTRUCTURE = "infrastructure"
    DATABASE = "database"
    NETWORK = "network"
    MEMORY = "memory"
    DISK = "disk"
    SECURITY = "security"
    
    # Business logic errors
    BUSINESS_LOGIC = "business_logic"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    
    # Service-specific errors
    AI_MODEL = "ai_model"
    ML_PROCESSING = "ml_processing"
    DATA_PROCESSING = "data_processing"
    TRADING_ENGINE = "trading_engine"
    API_GATEWAY = "api_gateway"
    
    # External service errors
    EXTERNAL_API = "external_api"
    THIRD_PARTY = "third_party"
    
    # System errors
    CONFIGURATION = "configuration"
    DEPENDENCY = "dependency"
    UNKNOWN = "unknown"

@dataclass
class ClassifiedError:
    """Standardized classified error structure"""
    error_id: str
    error_type: str
    error_message: str
    category: ErrorCategory
    severity: ErrorSeverity
    service_name: str
    service_context: Dict[str, Any]
    timestamp: datetime
    stack_trace: str
    additional_context: Dict[str, Any]
    recovery_suggestions: List[str]
    related_metrics: Dict[str, float]
    impact_assessment: str

class ErrorClassificationCore:
    """
    Enhanced error classification system for microservices.
    Provides intelligent error categorization, severity assessment, and recovery suggestions.
    """
    
    def __init__(self, service_name: str = None):
        """Initialize error classification system"""
        self.service_identity = get_service_identity(service_name)
        self.service_name = self.service_identity.service_name
        
        # Error patterns and classification rules
        self.classification_rules = self._setup_classification_rules()
        self.recovery_patterns = self._setup_recovery_patterns()
        
        # Error tracking
        self.error_history: List[ClassifiedError] = []
        self.error_patterns: Dict[str, int] = {}
        
    def _setup_classification_rules(self) -> Dict[str, Dict[str, Any]]:
        """Setup error classification rules based on patterns"""
        return {
            # Database errors
            "connection": {
                "category": ErrorCategory.DATABASE,
                "severity": ErrorSeverity.HIGH,
                "keywords": ["connection", "timeout", "database", "sql", "postgres", "clickhouse"],
                "impact": "Database operations unavailable"
            },
            "query": {
                "category": ErrorCategory.DATABASE,
                "severity": ErrorSeverity.MEDIUM,
                "keywords": ["query", "syntax", "table", "column", "constraint"],
                "impact": "Specific database operations failing"
            },
            
            # Network errors
            "network_timeout": {
                "category": ErrorCategory.NETWORK,
                "severity": ErrorSeverity.HIGH,
                "keywords": ["timeout", "network", "connection refused", "unreachable"],
                "impact": "External communication disrupted"
            },
            "api_error": {
                "category": ErrorCategory.EXTERNAL_API,
                "severity": ErrorSeverity.MEDIUM,
                "keywords": ["api", "http", "response", "status code"],
                "impact": "External API integration issues"
            },
            
            # Memory and resource errors
            "memory": {
                "category": ErrorCategory.MEMORY,
                "severity": ErrorSeverity.CRITICAL,
                "keywords": ["memory", "out of memory", "allocation", "heap"],
                "impact": "Service memory exhausted"
            },
            "disk_space": {
                "category": ErrorCategory.DISK,
                "severity": ErrorSeverity.HIGH,
                "keywords": ["disk", "space", "storage", "no space left"],
                "impact": "Storage capacity exceeded"
            },
            
            # Security errors
            "authentication": {
                "category": ErrorCategory.AUTHENTICATION,
                "severity": ErrorSeverity.HIGH,
                "keywords": ["authentication", "login", "credentials", "token", "unauthorized"],
                "impact": "User authentication failures"
            },
            "authorization": {
                "category": ErrorCategory.AUTHORIZATION,
                "severity": ErrorSeverity.MEDIUM,
                "keywords": ["authorization", "permission", "access denied", "forbidden"],
                "impact": "Access control violations"
            },
            
            # Service-specific patterns
            "ml_model": {
                "category": ErrorCategory.AI_MODEL,
                "severity": ErrorSeverity.HIGH,
                "keywords": ["model", "inference", "training", "prediction", "ml", "ai"],
                "impact": "AI/ML functionality compromised"
            },
            "trading": {
                "category": ErrorCategory.TRADING_ENGINE,
                "severity": ErrorSeverity.CRITICAL,
                "keywords": ["trading", "order", "position", "market", "execution"],
                "impact": "Trading operations affected"
            },
            "data_processing": {
                "category": ErrorCategory.DATA_PROCESSING,
                "severity": ErrorSeverity.MEDIUM,
                "keywords": ["data", "processing", "transform", "parse", "format"],
                "impact": "Data processing pipeline issues"
            },
            
            # Configuration errors
            "configuration": {
                "category": ErrorCategory.CONFIGURATION,
                "severity": ErrorSeverity.HIGH,
                "keywords": ["config", "configuration", "settings", "environment", "missing"],
                "impact": "Service configuration problems"
            },
            
            # Validation errors
            "validation": {
                "category": ErrorCategory.VALIDATION,
                "severity": ErrorSeverity.LOW,
                "keywords": ["validation", "invalid", "format", "required", "missing field"],
                "impact": "Input validation failures"
            }
        }
    
    def _setup_recovery_patterns(self) -> Dict[ErrorCategory, List[str]]:
        """Setup recovery suggestions based on error categories"""
        return {
            ErrorCategory.DATABASE: [
                "Check database connection settings",
                "Verify database service is running",
                "Review connection pool configuration",
                "Check database credentials",
                "Monitor database performance metrics"
            ],
            ErrorCategory.NETWORK: [
                "Verify network connectivity",
                "Check firewall settings",
                "Review DNS configuration",
                "Implement retry mechanism",
                "Check external service status"
            ],
            ErrorCategory.MEMORY: [
                "Monitor memory usage patterns",
                "Optimize memory allocation",
                "Increase service memory limits",
                "Review for memory leaks",
                "Implement memory cleanup procedures"
            ],
            ErrorCategory.SECURITY: [
                "Review authentication configuration",
                "Check credential validity",
                "Verify security policies",
                "Review access control settings",
                "Monitor security logs"
            ],
            ErrorCategory.AI_MODEL: [
                "Verify model file availability",
                "Check model version compatibility",
                "Review model input format",
                "Monitor GPU/CPU resources",
                "Validate model configuration"
            ],
            ErrorCategory.TRADING_ENGINE: [
                "Check market data feed",
                "Verify trading permissions",
                "Review risk management rules",
                "Check order execution status",
                "Monitor market conditions"
            ],
            ErrorCategory.CONFIGURATION: [
                "Review configuration files",
                "Check environment variables",
                "Verify service dependencies",
                "Validate configuration syntax",
                "Review default settings"
            ]
        }
    
    def classify_error(self, 
                      error: Union[Exception, str],
                      additional_context: Dict[str, Any] = None,
                      custom_category: ErrorCategory = None,
                      custom_severity: ErrorSeverity = None) -> ClassifiedError:
        """
        Classify an error with intelligent categorization and severity assessment.
        
        Args:
            error: Exception object or error message string
            additional_context: Additional context information
            custom_category: Override automatic category detection
            custom_severity: Override automatic severity assessment
            
        Returns:
            ClassifiedError: Fully classified error with metadata
        """
        # Extract error information
        if isinstance(error, Exception):
            error_type = type(error).__name__
            error_message = str(error)
            stack_trace = traceback.format_exc()
        else:
            error_type = "GenericError"
            error_message = str(error)
            stack_trace = ""
        
        # Generate unique error ID
        error_id = self._generate_error_id(error_type, error_message)
        
        # Classify error if not provided
        if custom_category is None:
            category = self._classify_error_category(error_message, error_type)
        else:
            category = custom_category
            
        if custom_severity is None:
            severity = self._assess_error_severity(error_message, error_type, category)
        else:
            severity = custom_severity
        
        # Get recovery suggestions
        recovery_suggestions = self._get_recovery_suggestions(category, error_message)
        
        # Assess impact
        impact_assessment = self._assess_impact(category, severity)
        
        # Collect related metrics
        related_metrics = self._collect_related_metrics(category)
        
        # Create classified error
        classified_error = ClassifiedError(
            error_id=error_id,
            error_type=error_type,
            error_message=error_message,
            category=category,
            severity=severity,
            service_name=self.service_name,
            service_context=get_service_context(),
            timestamp=datetime.utcnow(),
            stack_trace=stack_trace,
            additional_context=additional_context or {},
            recovery_suggestions=recovery_suggestions,
            related_metrics=related_metrics,
            impact_assessment=impact_assessment
        )
        
        # Store error for pattern analysis
        self._store_error_for_analysis(classified_error)
        
        return classified_error
    
    def _classify_error_category(self, error_message: str, error_type: str) -> ErrorCategory:
        """Classify error category based on message and type patterns"""
        error_text = f"{error_message} {error_type}".lower()
        
        # Score each classification rule
        scores = {}
        for rule_name, rule in self.classification_rules.items():
            score = 0
            for keyword in rule["keywords"]:
                if keyword.lower() in error_text:
                    score += 1
            if score > 0:
                scores[rule["category"]] = scores.get(rule["category"], 0) + score
        
        # Return category with highest score
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        return ErrorCategory.UNKNOWN
    
    def _assess_error_severity(self, error_message: str, error_type: str, category: ErrorCategory) -> ErrorSeverity:
        """Assess error severity based on patterns and category"""
        error_text = f"{error_message} {error_type}".lower()
        
        # Critical patterns
        critical_patterns = [
            "out of memory", "memory error", "segmentation fault",
            "service unavailable", "critical", "fatal",
            "cannot start", "crashed", "terminated"
        ]
        
        # High severity patterns
        high_patterns = [
            "connection refused", "timeout", "authentication failed",
            "database error", "network error", "permission denied"
        ]
        
        # Check for critical patterns
        if any(pattern in error_text for pattern in critical_patterns):
            return ErrorSeverity.CRITICAL
        
        # Check for high severity patterns
        if any(pattern in error_text for pattern in high_patterns):
            return ErrorSeverity.HIGH
        
        # Category-based severity
        if category in [ErrorCategory.INFRASTRUCTURE, ErrorCategory.SECURITY]:
            return ErrorSeverity.HIGH
        elif category in [ErrorCategory.BUSINESS_LOGIC, ErrorCategory.DATABASE]:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    def _get_recovery_suggestions(self, category: ErrorCategory, error_message: str) -> List[str]:
        """Get recovery suggestions based on error category and specific patterns"""
        suggestions = self.recovery_patterns.get(category, ["Review error logs", "Contact system administrator"])
        
        # Add specific suggestions based on error message
        error_text = error_message.lower()
        if "timeout" in error_text:
            suggestions.append("Increase timeout values")
        if "permission" in error_text:
            suggestions.append("Check file/directory permissions")
        if "missing" in error_text:
            suggestions.append("Verify required resources are available")
        
        return suggestions
    
    def _assess_impact(self, category: ErrorCategory, severity: ErrorSeverity) -> str:
        """Assess the impact of the error on service functionality"""
        impact_matrix = {
            (ErrorCategory.INFRASTRUCTURE, ErrorSeverity.CRITICAL): "Complete service outage",
            (ErrorCategory.DATABASE, ErrorSeverity.HIGH): "Data operations severely impacted",
            (ErrorCategory.NETWORK, ErrorSeverity.HIGH): "External connectivity compromised",
            (ErrorCategory.SECURITY, ErrorSeverity.HIGH): "Security breach risk",
            (ErrorCategory.AI_MODEL, ErrorSeverity.HIGH): "AI functionality unavailable",
            (ErrorCategory.TRADING_ENGINE, ErrorSeverity.CRITICAL): "Trading operations halted"
        }
        
        return impact_matrix.get((category, severity), f"{severity.value.title()} impact on {category.value}")
    
    def _collect_related_metrics(self, category: ErrorCategory) -> Dict[str, float]:
        """Collect metrics related to the error category"""
        # This would integrate with the monitoring system
        # For now, return placeholder metrics
        return {
            "error_frequency": 1.0,
            "service_uptime": 0.0,
            "resource_usage": 0.0
        }
    
    def _generate_error_id(self, error_type: str, error_message: str) -> str:
        """Generate unique error ID for tracking"""
        import hashlib
        error_content = f"{self.service_name}:{error_type}:{error_message[:100]}"
        return hashlib.md5(error_content.encode()).hexdigest()[:12]
    
    def _store_error_for_analysis(self, classified_error: ClassifiedError) -> None:
        """Store error for pattern analysis and trending"""
        self.error_history.append(classified_error)
        
        # Track error patterns
        pattern_key = f"{classified_error.category.value}:{classified_error.error_type}"
        self.error_patterns[pattern_key] = self.error_patterns.get(pattern_key, 0) + 1
        
        # Keep only last 1000 errors to avoid memory bloat
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]
    
    def get_error_patterns(self, hours: int = 24) -> Dict[str, Any]:
        """Get error patterns and trends for specified duration"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_errors = [e for e in self.error_history if e.timestamp >= cutoff_time]
        
        # Group by category and severity
        by_category = {}
        by_severity = {}
        
        for error in recent_errors:
            category = error.category.value
            severity = error.severity.value
            
            by_category[category] = by_category.get(category, 0) + 1
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        return {
            "total_errors": len(recent_errors),
            "by_category": by_category,
            "by_severity": by_severity,
            "top_patterns": dict(sorted(self.error_patterns.items(), key=lambda x: x[1], reverse=True)[:10]),
            "analysis_period_hours": hours,
            "service_name": self.service_name
        }
    
    def get_critical_errors(self, hours: int = 1) -> List[ClassifiedError]:
        """Get critical errors from recent period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [
            error for error in self.error_history 
            if error.timestamp >= cutoff_time and error.severity == ErrorSeverity.CRITICAL
        ]


# Service Error Classification Singleton
_error_classifier = None

def get_error_classifier(service_name: str = None) -> ErrorClassificationCore:
    """Get or create error classifier singleton"""
    global _error_classifier
    
    if _error_classifier is None:
        _error_classifier = ErrorClassificationCore(service_name)
    
    return _error_classifier

def classify_error(error: Union[Exception, str], 
                  context: Dict[str, Any] = None,
                  category: ErrorCategory = None,
                  severity: ErrorSeverity = None) -> ClassifiedError:
    """Convenience function to classify errors"""
    classifier = get_error_classifier()
    return classifier.classify_error(error, context, category, severity)

def get_error_patterns(hours: int = 24) -> Dict[str, Any]:
    """Convenience function to get error patterns"""
    classifier = get_error_classifier()
    return classifier.get_error_patterns(hours)