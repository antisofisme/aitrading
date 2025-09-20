"""
Core Response Implementation - Production-ready response standardization
"""
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from ..base.base_response import BaseResponse, ResponseStatus, ResponseType

class CoreResponse(BaseResponse):
    """Core response handler implementation with standardized formatting"""
    
    def __init__(self, service_name: str, service_version: str = "1.0.0"):
        super().__init__(service_name, service_version)
        self.setup_service_specific_responses()
    
    def create_response(self,
                       data: Any = None,
                       status: ResponseStatus = ResponseStatus.SUCCESS,
                       message: str = None,
                       response_type: ResponseType = ResponseType.DATA,
                       metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create standardized response"""
        
        # Generate unique response ID
        response_id = str(uuid.uuid4())
        
        # Build base response structure
        response = {
            "success": status == ResponseStatus.SUCCESS,
            "status": status.value,
            "type": response_type.value,
            "response_id": response_id,
            "service": self.service_name,
            "timestamp": datetime.utcnow().isoformat(),
            "version": self.service_version
        }
        
        # Add data if provided
        if data is not None:
            response["data"] = data
        
        # Add message if provided
        if message:
            response["message"] = message
        
        # Add metadata
        response["metadata"] = self._build_metadata(metadata)
        
        return response
    
    def success_response(self,
                        data: Any = None,
                        message: str = None,
                        metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create success response"""
        return self.create_response(
            data=data,
            status=ResponseStatus.SUCCESS,
            message=message or "Operation completed successfully",
            response_type=ResponseType.DATA,
            metadata=metadata
        )
    
    def error_response(self,
                      error: Union[str, Exception] = None,
                      status_code: int = 500,  
                      details: Optional[Dict[str, Any]] = None,
                      # Additional parameters for compatibility
                      message: str = None,
                      error_code: str = None) -> Dict[str, Any]:
        """Create error response"""
        
        # Handle compatibility parameters
        if message is not None and error is None:
            error = message
        
        # Extract error message
        if isinstance(error, Exception):
            error_message = str(error)
            error_type = type(error).__name__
        elif error is not None:
            error_message = error
            error_type = "GenericError"
        else:
            error_message = message or "Unknown error"
            error_type = "GenericError"
        
        # Build error data
        error_data = {
            "code": status_code,
            "message": error_message,
            "type": error_type
        }
        
        # Add error_code if provided (for compatibility)
        if error_code:
            error_data["error_code"] = error_code
        
        if details:
            error_data["details"] = details
        
        # Add debug information in development
        if self._is_development() and isinstance(error, Exception):
            import traceback
            error_data["traceback"] = traceback.format_exc()
        
        return self.create_response(
            data=error_data,
            status=ResponseStatus.ERROR,
            message=f"Error: {error_message}",
            response_type=ResponseType.ERROR
        )
    
    def warning_response(self,
                        data: Any = None,
                        warning_message: str = None,
                        metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create warning response"""
        return self.create_response(
            data=data,
            status=ResponseStatus.WARNING,
            message=warning_message or "Operation completed with warnings",
            response_type=ResponseType.DATA,
            metadata=metadata
        )
    
    def partial_response(self,
                        data: Any = None,
                        partial_message: str = None,
                        failed_items: Optional[List[Any]] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create partial success response"""
        
        # Add failed items to metadata
        if failed_items:
            if metadata is None:
                metadata = {}
            metadata["failed_items"] = failed_items
            metadata["failed_count"] = len(failed_items)
        
        return self.create_response(
            data=data,
            status=ResponseStatus.PARTIAL,
            message=partial_message or "Operation partially completed",
            response_type=ResponseType.DATA,
            metadata=metadata
        )
    
    def health_response(self,
                       status: str = "healthy",
                       checks: Optional[Dict[str, Any]] = None,
                       metrics: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create health check response"""
        
        health_data = {
            "status": status,
            "service": self.service_name,
            "version": self.service_version,
            "uptime": self._get_uptime(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if checks:
            health_data["checks"] = checks
        
        if metrics:
            health_data["metrics"] = metrics
        
        # Determine response status based on health
        response_status = ResponseStatus.SUCCESS if status == "healthy" else ResponseStatus.WARNING
        
        return self.create_response(
            data=health_data,
            status=response_status,
            message=f"Service is {status}",
            response_type=ResponseType.HEALTH
        )
    
    def metrics_response(self,
                        metrics: Dict[str, Any],
                        metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create metrics response"""
        
        metrics_data = {
            "service": self.service_name,
            "collection_time": datetime.utcnow().isoformat(),
            "metrics": metrics
        }
        
        return self.create_response(
            data=metrics_data,
            status=ResponseStatus.SUCCESS,
            message="Metrics collected successfully",
            response_type=ResponseType.METRICS,
            metadata=metadata
        )
    
    def paginated_response(self,
                          data: List[Any],
                          page: int,
                          page_size: int,
                          total_items: int,
                          metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create paginated response"""
        
        # Calculate pagination metadata
        total_pages = (total_items + page_size - 1) // page_size
        has_next = page < total_pages
        has_previous = page > 1
        
        pagination_info = {
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_previous": has_previous,
            "items_count": len(data)
        }
        
        # Add pagination to metadata
        if metadata is None:
            metadata = {}
        metadata["pagination"] = pagination_info
        
        return self.create_response(
            data=data,
            status=ResponseStatus.SUCCESS,
            message=f"Retrieved {len(data)} items (page {page} of {total_pages})",
            response_type=ResponseType.DATA,
            metadata=metadata
        )
    
    def validate_response_format(self, response: Dict[str, Any]) -> bool:
        """Validate response format against service standards"""
        required_fields = [
            "success", "status", "type", "response_id", 
            "service", "timestamp", "version", "metadata"
        ]
        
        # Check required fields
        for field in required_fields:
            if field not in response:
                return False
        
        # Validate field types
        if not isinstance(response["success"], bool):
            return False
        
        if response["status"] not in [s.value for s in ResponseStatus]:
            return False
        
        if response["type"] not in [t.value for t in ResponseType]:
            return False
        
        if not isinstance(response["metadata"], dict):
            return False
        
        return True
    
    def setup_service_specific_responses(self):
        """Setup service-specific response formats"""
        # Service-specific response customizations
        
        if self.service_name == "api-gateway":
            self._setup_api_gateway_responses()
        elif self.service_name == "trading-engine":
            self._setup_trading_responses()
        elif self.service_name == "database-service":
            self._setup_database_responses()
    
    def _setup_api_gateway_responses(self):
        """Setup API Gateway specific responses"""
        # Add API Gateway specific response fields
        pass
    
    def _setup_trading_responses(self):
        """Setup Trading Engine specific responses"""
        # Add trading specific response fields
        pass
    
    def _setup_database_responses(self):
        """Setup Database Service specific responses"""
        # Add database specific response fields
        pass
    
    def _build_metadata(self, custom_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build response metadata"""
        base_metadata = self.get_base_metadata()
        
        if custom_metadata:
            base_metadata.update(custom_metadata)
        
        return base_metadata
    
    def _get_uptime(self) -> str:
        """Get service uptime (placeholder implementation)"""
        # In a real implementation, this would calculate actual uptime
        return "00:00:00"
    
    def _is_development(self) -> bool:
        """Check if running in development environment"""
        import os
        return os.getenv('ENVIRONMENT', 'development').lower() == 'development'
    
    def create_list_response(self,
                           items: List[Any],
                           total_count: int = None,
                           filters: Optional[Dict[str, Any]] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create response for list operations"""
        
        list_data = {
            "items": items,
            "count": len(items)
        }
        
        if total_count is not None:
            list_data["total_count"] = total_count
        
        if filters:
            list_data["filters"] = filters
        
        # Add list metadata
        if metadata is None:
            metadata = {}
        metadata["list_info"] = {
            "items_returned": len(items),
            "has_filters": bool(filters)
        }
        
        return self.success_response(
            data=list_data,
            message=f"Retrieved {len(items)} items",
            metadata=metadata
        )
    
    def create_operation_response(self,
                                operation: str,
                                result: Any = None,
                                operation_id: str = None,
                                metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create response for specific operations"""
        
        operation_data = {
            "operation": operation,
            "operation_id": operation_id or str(uuid.uuid4()),
            "result": result,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        return self.success_response(
            data=operation_data,
            message=f"Operation '{operation}' completed successfully",
            metadata=metadata
        )
    
    def create_async_response(self,
                            task_id: str,
                            status: str = "accepted",
                            estimated_completion: Optional[str] = None,
                            metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create response for async operations"""
        
        async_data = {
            "task_id": task_id,
            "status": status,
            "submitted_at": datetime.utcnow().isoformat()
        }
        
        if estimated_completion:
            async_data["estimated_completion"] = estimated_completion
        
        return self.create_response(
            data=async_data,
            status=ResponseStatus.SUCCESS,
            message=f"Task {task_id} submitted for processing",
            response_type=ResponseType.MESSAGE,
            metadata=metadata
        )