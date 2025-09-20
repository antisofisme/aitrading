"""
Base Error Handler Interface - Abstract class for service-specific error handling
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from enum import Enum
import traceback

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_SERVICE = "external_service"
    DATABASE = "database"
    NETWORK = "network"
    SYSTEM = "system"
    UNKNOWN = "unknown"

class BaseErrorHandler(ABC):
    """Abstract base class for all service error handlers"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.error_stats = {
            "total_errors": 0,
            "by_category": {},
            "by_severity": {}
        }
    
    @abstractmethod
    def handle_error(self, 
                    error: Exception, 
                    context: Optional[Dict[str, Any]] = None,
                    category: ErrorCategory = ErrorCategory.UNKNOWN,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> Dict[str, Any]:
        """Handle error and return standardized error response"""
        pass
    
    @abstractmethod
    def handle_validation_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle validation-specific errors"""
        pass
    
    @abstractmethod
    def handle_business_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle business logic errors"""
        pass
    
    @abstractmethod
    def handle_external_service_error(self, error: Exception, service_name: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle errors from external service calls"""
        pass
    
    @abstractmethod
    def handle_database_error(self, error: Exception, operation: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle database-related errors"""
        pass
    
    def extract_error_info(self, error: Exception) -> Dict[str, Any]:
        """Extract standardized error information"""
        return {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "error_traceback": traceback.format_exc(),
            "service": self.service_name
        }
    
    def log_error(self, error_info: Dict[str, Any], severity: ErrorSeverity):
        """Log error information (to be implemented by concrete classes)"""
        # Update stats
        self.error_stats["total_errors"] += 1
        
        category = error_info.get("category", "unknown")
        self.error_stats["by_category"][category] = self.error_stats["by_category"].get(category, 0) + 1
        
        severity_str = severity.value
        self.error_stats["by_severity"][severity_str] = self.error_stats["by_severity"].get(severity_str, 0) + 1
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        return self.error_stats.copy()
    
    def reset_error_stats(self):
        """Reset error statistics"""
        self.error_stats = {
            "total_errors": 0,
            "by_category": {},
            "by_severity": {}
        }
    
    @abstractmethod
    def create_error_response(self, 
                            error_info: Dict[str, Any], 
                            status_code: int = 500,
                            user_message: str = None) -> Dict[str, Any]:
        """Create standardized error response"""
        pass
    
    @abstractmethod
    def setup_service_specific_handlers(self):
        """Setup service-specific error handlers"""
        pass