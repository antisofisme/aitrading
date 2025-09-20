"""
AI Brain Enhanced Core Error Handler Implementation - Surgical precision error handling
Enhanced with AI Brain Error DNA for systematic error analysis and prevention
"""
import traceback
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from ..base.base_error_handler import BaseErrorHandler, ErrorSeverity, ErrorCategory

# AI Brain Integration
try:
    import sys
    sys.path.append('/mnt/f/WINDSURF/concept_ai/projects/ai_trading/server_microservice/services')
    from shared.ai_brain_trading_error_dna import AiBrainTradingErrorDNA
    AI_BRAIN_AVAILABLE = True
except ImportError:
    AI_BRAIN_AVAILABLE = False

class CoreErrorHandler(BaseErrorHandler):
    """AI Brain Enhanced Core error handler with surgical precision error analysis"""
    
    def __init__(self, service_name: str, enable_alerting: bool = True):
        """
        Initialize AI Brain Enhanced CoreErrorHandler with systematic error analysis.
        
        Args:
            service_name: Name of the service this error handler belongs to
            enable_alerting: Whether to enable alerting for high severity errors (default: True)
        """
        super().__init__(service_name)
        self.enable_alerting = enable_alerting
        
        # AI Brain Error DNA Integration
        self.ai_brain_error_dna = None
        if AI_BRAIN_AVAILABLE:
            try:
                self.ai_brain_error_dna = AiBrainTradingErrorDNA(f"error-handler-{service_name}")
                print(f"✅ AI Brain Error DNA initialized for error handler: {service_name}")
            except Exception as e:
                print(f"⚠️ AI Brain Error DNA initialization failed: {e}")
        
        self.setup_service_specific_handlers()
    
    def handle_error(self, 
                    error: Exception, 
                    context: Optional[Dict[str, Any]] = None,
                    category: ErrorCategory = ErrorCategory.UNKNOWN,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> Dict[str, Any]:
        """
        AI Brain Enhanced error handling with surgical precision error analysis.
        
        Args:
            error: The exception that occurred
            context: Optional contextual information about when/where the error occurred
            category: Error category (VALIDATION, BUSINESS_LOGIC, SYSTEM, etc.)
            severity: Error severity level (LOW, MEDIUM, HIGH, CRITICAL)
            
        Returns:
            Standardized error response dictionary with AI Brain analysis and solution guidance
        """
        
        # Generate unique error ID
        error_id = str(uuid.uuid4())
        
        # Extract error information
        error_info = self.extract_error_info(error)
        error_info.update({
            "error_id": error_id,
            "category": category.value,
            "severity": severity.value,
            "timestamp": datetime.utcnow().isoformat(),
            "context": context or {}
        })
        
        # AI Brain Error DNA Analysis
        ai_brain_analysis = None
        if self.ai_brain_error_dna and AI_BRAIN_AVAILABLE:
            try:
                print(f"🧠 AI Brain: Performing surgical precision error analysis for error {error_id}")
                ai_brain_analysis = self.ai_brain_error_dna.analyze_error(error, context)
                
                # Enhance error_info with AI Brain insights
                error_info.update({
                    "ai_brain_pattern": ai_brain_analysis.get("matched_pattern"),
                    "ai_brain_solution_confidence": ai_brain_analysis.get("solution_confidence", 0),
                    "ai_brain_trading_impact": ai_brain_analysis.get("trading_impact"),
                    "ai_brain_urgency": ai_brain_analysis.get("urgency_level"),
                    "ai_brain_recommended_actions": ai_brain_analysis.get("recommended_actions", []),
                    "ai_brain_prevention_strategy": ai_brain_analysis.get("prevention_strategy"),
                    "ai_brain_related_patterns": ai_brain_analysis.get("related_patterns", [])
                })
                
                # Adjust severity based on AI Brain analysis
                ai_brain_impact = ai_brain_analysis.get("trading_impact", "unknown")
                ai_brain_urgency = ai_brain_analysis.get("urgency_level", "medium")
                
                if ai_brain_impact == "critical" and ai_brain_urgency == "immediate":
                    severity = ErrorSeverity.CRITICAL
                elif ai_brain_impact == "high" and ai_brain_urgency in ["immediate", "high"]:
                    severity = ErrorSeverity.HIGH
                
                print(f"🧠 AI Brain Error Analysis Complete:")
                print(f"   Pattern: {ai_brain_analysis.get('matched_pattern', 'Unknown')}")
                print(f"   Solution Confidence: {ai_brain_analysis.get('solution_confidence', 0):.2f}")
                print(f"   Trading Impact: {ai_brain_impact}")
                print(f"   Urgency Level: {ai_brain_urgency}")
                
                if ai_brain_analysis.get("recommended_actions"):
                    print(f"   Recommended Actions: {ai_brain_analysis['recommended_actions']}")
                    
            except Exception as analysis_error:
                print(f"⚠️ AI Brain error analysis failed: {analysis_error}")
                error_info["ai_brain_analysis_error"] = str(analysis_error)
        
        # Log the error with AI Brain enhancement
        self.log_error(error_info, severity)
        
        # Send alert if needed (enhanced with AI Brain context)
        if self.enable_alerting and severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self.alert_on_high_severity_error(error_info)
        
        # Create response based on severity
        if severity == ErrorSeverity.CRITICAL:
            status_code = 500
            user_message = "A critical system error occurred. Please try again later."
        elif severity == ErrorSeverity.HIGH:
            status_code = 500
            user_message = "An error occurred while processing your request."
        elif category == ErrorCategory.VALIDATION:
            status_code = 400
            user_message = "Invalid input provided."
        elif category == ErrorCategory.AUTHENTICATION:
            status_code = 401
            user_message = "Authentication required."
        elif category == ErrorCategory.AUTHORIZATION:
            status_code = 403
            user_message = "Access denied."
        else:
            status_code = 500
            user_message = "An unexpected error occurred."
        
        return self.create_error_response(error_info, status_code, user_message)
    
    def handle_validation_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle validation-specific errors"""
        validation_context = {
            "error_type": "validation",
            **(context or {})
        }
        
        return self.handle_error(
            error, 
            validation_context, 
            ErrorCategory.VALIDATION, 
            ErrorSeverity.LOW
        )
    
    def handle_api_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle API-specific errors with appropriate HTTP status codes"""
        api_context = {
            "error_type": "api",
            **(context or {})
        }
        
        # Determine appropriate error category and severity for API errors
        if isinstance(error, ValueError):
            category = ErrorCategory.VALIDATION
            severity = ErrorSeverity.LOW
        elif isinstance(error, (FileNotFoundError, KeyError)):
            category = ErrorCategory.BUSINESS_LOGIC
            severity = ErrorSeverity.MEDIUM
        elif isinstance(error, PermissionError):
            category = ErrorCategory.SECURITY
            severity = ErrorSeverity.HIGH
        else:
            category = ErrorCategory.SYSTEM
            severity = ErrorSeverity.MEDIUM
        
        return self.handle_error(error, api_context, category, severity)
    
    def handle_business_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle business logic errors"""
        business_context = {
            "error_type": "business_logic",
            **(context or {})
        }
        
        return self.handle_error(
            error, 
            business_context, 
            ErrorCategory.BUSINESS_LOGIC, 
            ErrorSeverity.MEDIUM
        )
    
    def handle_external_service_error(self, error: Exception, service_name: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle errors from external service calls"""
        external_context = {
            "error_type": "external_service",
            "external_service": service_name,
            **(context or {})
        }
        
        # Determine severity based on service criticality
        severity = ErrorSeverity.HIGH if self._is_critical_service(service_name) else ErrorSeverity.MEDIUM
        
        return self.handle_error(
            error, 
            external_context, 
            ErrorCategory.EXTERNAL_SERVICE, 
            severity
        )
    
    def handle_database_error(self, error: Exception, operation: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle database-related errors"""
        db_context = {
            "error_type": "database",
            "operation": operation,
            **(context or {})
        }
        
        # Database errors are typically high severity
        severity = ErrorSeverity.HIGH
        
        return self.handle_error(
            error, 
            db_context, 
            ErrorCategory.DATABASE, 
            severity
        )
    
    def create_error_response(self, 
                            error_info: Dict[str, Any], 
                            status_code: int = 500,
                            user_message: str = None) -> Dict[str, Any]:
        """Create standardized error response"""
        
        response = {
            "success": False,
            "error": {
                "id": error_info["error_id"],
                "message": user_message or "An error occurred",
                "code": status_code,
                "category": error_info["category"],
                "severity": error_info["severity"],
                "timestamp": error_info["timestamp"],
                "service": self.service_name
            }
        }
        
        # Include additional details in development/testing
        if self._should_include_debug_info():
            response["error"]["debug"] = {
                "type": error_info["error_type"],
                "details": error_info["error_message"],
                "context": error_info["context"]
            }
            
            # Include traceback only in development
            if self._is_development():
                response["error"]["debug"]["traceback"] = error_info["error_traceback"]
        
        return response
    
    def setup_service_specific_handlers(self) -> None:
        """Setup service-specific error handlers"""
        # Service-specific error handling can be customized here
        
        if self.service_name == "api-gateway":
            # API Gateway specific errors
            self._setup_api_gateway_handlers()
        elif self.service_name == "database-service":
            # Database service specific errors
            self._setup_database_service_handlers()
        elif self.service_name in ["mt5-bridge", "trading-engine"]:
            # Trading related errors
            self._setup_trading_handlers()
    
    def _setup_api_gateway_handlers(self) -> None:
        """Setup API Gateway specific error handlers"""
        # Rate limiting, authentication, routing errors
        pass
    
    def _setup_database_service_handlers(self) -> None:
        """Setup Database Service specific error handlers"""
        # Connection errors, query errors, migration errors
        pass
    
    def _setup_trading_handlers(self) -> None:
        """Setup Trading specific error handlers"""
        # MT5 connection errors, trading execution errors
        pass
    
    def _is_critical_service(self, service_name: str) -> bool:
        """Check if a service is critical"""
        critical_services = [
            "database-service",
            "api-gateway",
            "trading-engine"
        ]
        return service_name in critical_services
    
    def _should_include_debug_info(self) -> bool:
        """Check if debug information should be included"""
        import os
        env = os.getenv('ENVIRONMENT', 'development').lower()
        return env in ['development', 'testing']
    
    def _is_development(self) -> bool:
        """Check if running in development environment"""
        import os
        return os.getenv('ENVIRONMENT', 'development').lower() == 'development'
    
    def alert_on_high_severity_error(self, error_info: Dict[str, Any]) -> None:
        """Send alert for high severity errors"""
        # In a real implementation, this would send alerts via:
        # - Slack/Teams notifications
        # - Email alerts
        # - PagerDuty/similar monitoring
        # - Log aggregation systems (ELK, Datadog, etc.)
        
        alert_data = {
            "service": self.service_name,
            "error_id": error_info["error_id"],
            "severity": error_info["severity"],
            "category": error_info["category"],
            "message": error_info["error_message"],
            "timestamp": error_info["timestamp"]
        }
        
        # For now, just log the alert
        # Use proper logging instead of print for production code
        import logging
        logger = logging.getLogger(f"{self.service_name}-error-alerts")
        logger.critical(f"HIGH SEVERITY ERROR ALERT", extra={"context": alert_data})
    
    def get_error_patterns(self) -> Dict[str, Any]:
        """Get error patterns and trends"""
        patterns = {
            "total_errors": self.error_stats["total_errors"],
            "error_rate_by_category": {},
            "error_rate_by_severity": {},
            "top_error_types": [],
            "service": self.service_name
        }
        
        total = max(self.error_stats["total_errors"], 1)  # Avoid division by zero
        
        # Calculate percentages
        for category, count in self.error_stats["by_category"].items():
            patterns["error_rate_by_category"][category] = {
                "count": count,
                "percentage": round((count / total) * 100, 2)
            }
        
        for severity, count in self.error_stats["by_severity"].items():
            patterns["error_rate_by_severity"][severity] = {
                "count": count,
                "percentage": round((count / total) * 100, 2)
            }
        
        return patterns
    
    def handle_timeout_error(self, operation: str, timeout_seconds: int, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle timeout-specific errors"""
        timeout_error = TimeoutError(f"Operation '{operation}' timed out after {timeout_seconds} seconds")
        
        timeout_context = {
            "error_type": "timeout",
            "operation": operation,
            "timeout_seconds": timeout_seconds,
            **(context or {})
        }
        
        return self.handle_error(
            timeout_error,
            timeout_context,
            ErrorCategory.SYSTEM,
            ErrorSeverity.MEDIUM
        )
    
    def handle_rate_limit_error(self, limit: int, window: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle rate limiting errors"""
        rate_limit_error = Exception(f"Rate limit exceeded: {limit} requests per {window}")
        
        rate_limit_context = {
            "error_type": "rate_limit",
            "limit": limit,
            "window": window,
            **(context or {})
        }
        
        return self.handle_error(
            rate_limit_error,
            rate_limit_context,
            ErrorCategory.SYSTEM,
            ErrorSeverity.LOW
        )
    
    def handle_circuit_breaker_error(self, service_name: str, failure_count: int, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle circuit breaker errors"""
        circuit_error = Exception(f"Circuit breaker open for {service_name} after {failure_count} failures")
        
        circuit_context = {
            "error_type": "circuit_breaker",
            "target_service": service_name,
            "failure_count": failure_count,
            **(context or {})
        }
        
        return self.handle_error(
            circuit_error,
            circuit_context,
            ErrorCategory.EXTERNAL_SERVICE,
            ErrorSeverity.HIGH
        )


# CENTRALIZED ERROR MANAGER - Simple singleton for all microservices
import threading

class SharedInfraErrorManager:
    """Simple centralized error management for microservices"""
    
    _handlers = {}
    _lock = threading.RLock()
    
    @classmethod
    def get_error_handler(cls, service_name: str) -> CoreErrorHandler:
        """Get or create error handler for service"""
        with cls._lock:
            if service_name not in cls._handlers:
                cls._handlers[service_name] = CoreErrorHandler(service_name)
            return cls._handlers[service_name]
    
    @classmethod
    def handle_error(cls, service_name: str, error: Exception, **kwargs):
        """Handle error for service"""
        handler = cls.get_error_handler(service_name)
        return handler.handle_error(error, **kwargs)
    
    @classmethod
    def get_all_handlers(cls):
        """Get all managed error handlers"""
        return cls._handlers.copy()


# Simple convenience functions
def get_error_handler(service_name: str) -> CoreErrorHandler:
    """Get error handler for service"""
    return SharedInfraErrorManager.get_error_handler(service_name)

def handle_error(service_name: str, error: Exception, **kwargs):
    """Handle error for service"""
    return SharedInfraErrorManager.handle_error(service_name, error, **kwargs)

# Decorator for automatic error handling
def handle_errors(service_name: str, operation: str = ""):
    """Decorator for automatic error handling"""
    def decorator(func):
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as operation_error:
                return handle_error(
                    service_name, 
                    operation_error, 
                    context={
                        "operation": operation or func.__name__,
                        "function": func.__name__,
                        "module": func.__module__
                    }
                )
        return wrapper
    return decorator