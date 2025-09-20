"""
Base Response Interface - Abstract class for service-specific response standardization
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from datetime import datetime

class ResponseStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    PARTIAL = "partial"

class ResponseType(Enum):
    DATA = "data"
    MESSAGE = "message"
    HEALTH = "health"
    METRICS = "metrics"
    ERROR = "error"

class BaseResponse(ABC):
    """Abstract base class for all service response handlers"""
    
    def __init__(self, service_name: str, service_version: str = "1.0.0"):
        self.service_name = service_name
        self.service_version = service_version
    
    @abstractmethod
    def create_response(self,
                       data: Any = None,
                       status: ResponseStatus = ResponseStatus.SUCCESS,
                       message: str = None,
                       response_type: ResponseType = ResponseType.DATA,
                       metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create standardized response"""
        pass
    
    @abstractmethod
    def success_response(self,
                        data: Any = None,
                        message: str = None,
                        metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create success response"""
        pass
    
    @abstractmethod
    def error_response(self,
                      error: Union[str, Exception],
                      status_code: int = 500,
                      details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create error response"""
        pass
    
    @abstractmethod
    def warning_response(self,
                        data: Any = None,
                        warning_message: str = None,
                        metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create warning response"""
        pass
    
    @abstractmethod
    def partial_response(self,
                        data: Any = None,
                        partial_message: str = None,
                        failed_items: Optional[List[Any]] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create partial success response"""
        pass
    
    @abstractmethod
    def health_response(self,
                       status: str = "healthy",
                       checks: Optional[Dict[str, Any]] = None,
                       metrics: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create health check response"""
        pass
    
    @abstractmethod
    def metrics_response(self,
                        metrics: Dict[str, Any],
                        metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create metrics response"""
        pass
    
    @abstractmethod
    def paginated_response(self,
                          data: List[Any],
                          page: int,
                          page_size: int,
                          total_items: int,
                          metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create paginated response"""
        pass
    
    def get_base_metadata(self) -> Dict[str, Any]:
        """Get base metadata for all responses"""
        return {
            "service": self.service_name,
            "version": self.service_version,
            "timestamp": datetime.utcnow().isoformat(),
            "timezone": "UTC"
        }
    
    def add_request_metadata(self, 
                           request_id: str = None,
                           user_id: str = None,
                           correlation_id: str = None) -> Dict[str, Any]:
        """Add request-specific metadata"""
        metadata = self.get_base_metadata()
        
        if request_id:
            metadata["request_id"] = request_id
        if user_id:
            metadata["user_id"] = user_id
        if correlation_id:
            metadata["correlation_id"] = correlation_id
            
        return metadata
    
    @abstractmethod
    def validate_response_format(self, response: Dict[str, Any]) -> bool:
        """Validate response format against service standards"""
        pass
    
    @abstractmethod
    def setup_service_specific_responses(self):
        """Setup service-specific response formats"""
        pass