"""
Standard Response Format untuk semua services
Menyediakan konsistensi dalam response structure
"""

from dataclasses import dataclass
from typing import Any, Optional, Dict, List
from datetime import datetime
from enum import Enum


class ResponseStatus(Enum):
    """Standard response status codes"""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL_SUCCESS = "partial_success"
    TIMEOUT = "timeout"
    CIRCUIT_BREAKER_OPEN = "circuit_breaker_open"


@dataclass
class StandardResponse:
    """
    Standard response format untuk semua internal service operations
    """
    success: bool
    data: Optional[Any] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    processing_time_ms: Optional[float] = None
    correlation_id: Optional[str] = None
    timestamp: Optional[str] = None
    service_name: Optional[str] = None
    status: ResponseStatus = ResponseStatus.SUCCESS

    def __post_init__(self):
        """Set default values after initialization"""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()

        if not self.success and self.status == ResponseStatus.SUCCESS:
            self.status = ResponseStatus.ERROR

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "success": self.success,
            "status": self.status.value,
            "data": self.data,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "processing_time_ms": self.processing_time_ms,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
            "service_name": self.service_name
        }

    @classmethod
    def success_response(cls,
                        data: Any = None,
                        processing_time_ms: Optional[float] = None,
                        correlation_id: Optional[str] = None,
                        service_name: Optional[str] = None) -> 'StandardResponse':
        """Create a success response"""
        return cls(
            success=True,
            data=data,
            processing_time_ms=processing_time_ms,
            correlation_id=correlation_id,
            service_name=service_name,
            status=ResponseStatus.SUCCESS
        )

    @classmethod
    def error_response(cls,
                      error_message: str,
                      error_code: Optional[str] = None,
                      processing_time_ms: Optional[float] = None,
                      correlation_id: Optional[str] = None,
                      service_name: Optional[str] = None) -> 'StandardResponse':
        """Create an error response"""
        return cls(
            success=False,
            error_message=error_message,
            error_code=error_code,
            processing_time_ms=processing_time_ms,
            correlation_id=correlation_id,
            service_name=service_name,
            status=ResponseStatus.ERROR
        )

    @classmethod
    def timeout_response(cls,
                        error_message: str = "Operation timed out",
                        processing_time_ms: Optional[float] = None,
                        correlation_id: Optional[str] = None,
                        service_name: Optional[str] = None) -> 'StandardResponse':
        """Create a timeout response"""
        return cls(
            success=False,
            error_message=error_message,
            error_code="TIMEOUT",
            processing_time_ms=processing_time_ms,
            correlation_id=correlation_id,
            service_name=service_name,
            status=ResponseStatus.TIMEOUT
        )

    @classmethod
    def circuit_breaker_response(cls,
                                service: str,
                                correlation_id: Optional[str] = None,
                                service_name: Optional[str] = None) -> 'StandardResponse':
        """Create a circuit breaker open response"""
        return cls(
            success=False,
            error_message=f"Circuit breaker open for {service}",
            error_code="CIRCUIT_BREAKER_OPEN",
            correlation_id=correlation_id,
            service_name=service_name,
            status=ResponseStatus.CIRCUIT_BREAKER_OPEN
        )


@dataclass
class BatchResponse:
    """
    Standard response format untuk batch operations
    """
    total_items: int
    successful_items: int
    failed_items: int
    success_rate: float
    responses: List[StandardResponse]
    overall_success: bool
    processing_time_ms: Optional[float] = None
    correlation_id: Optional[str] = None
    timestamp: Optional[str] = None

    def __post_init__(self):
        """Calculate derived values"""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()

        # Calculate success rate
        if self.total_items > 0:
            self.success_rate = self.successful_items / self.total_items
        else:
            self.success_rate = 0.0

        # Overall success if all items succeeded
        self.overall_success = self.successful_items == self.total_items

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "total_items": self.total_items,
            "successful_items": self.successful_items,
            "failed_items": self.failed_items,
            "success_rate": self.success_rate,
            "overall_success": self.overall_success,
            "processing_time_ms": self.processing_time_ms,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
            "responses": [r.to_dict() for r in self.responses]
        }

    @classmethod
    def from_responses(cls,
                      responses: List[StandardResponse],
                      processing_time_ms: Optional[float] = None,
                      correlation_id: Optional[str] = None) -> 'BatchResponse':
        """Create batch response from individual responses"""
        total_items = len(responses)
        successful_items = sum(1 for r in responses if r.success)
        failed_items = total_items - successful_items

        return cls(
            total_items=total_items,
            successful_items=successful_items,
            failed_items=failed_items,
            responses=responses,
            processing_time_ms=processing_time_ms,
            correlation_id=correlation_id
        )


@dataclass
class HealthCheckResponse:
    """Standard health check response format"""
    service_name: str
    status: str  # "healthy", "degraded", "unhealthy"
    version: str
    timestamp: str
    uptime_seconds: int
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "service": self.service_name,
            "status": self.status,
            "version": self.version,
            "timestamp": self.timestamp,
            "uptime_seconds": self.uptime_seconds,
            **self.details
        }

    @classmethod
    def healthy(cls,
               service_name: str,
               version: str,
               uptime_seconds: int,
               details: Optional[Dict[str, Any]] = None) -> 'HealthCheckResponse':
        """Create healthy status response"""
        return cls(
            service_name=service_name,
            status="healthy",
            version=version,
            timestamp=datetime.utcnow().isoformat(),
            uptime_seconds=uptime_seconds,
            details=details or {}
        )

    @classmethod
    def degraded(cls,
                service_name: str,
                version: str,
                uptime_seconds: int,
                reason: str,
                details: Optional[Dict[str, Any]] = None) -> 'HealthCheckResponse':
        """Create degraded status response"""
        response_details = details or {}
        response_details["degradation_reason"] = reason

        return cls(
            service_name=service_name,
            status="degraded",
            version=version,
            timestamp=datetime.utcnow().isoformat(),
            uptime_seconds=uptime_seconds,
            details=response_details
        )

    @classmethod
    def unhealthy(cls,
                 service_name: str,
                 version: str,
                 uptime_seconds: int,
                 error: str,
                 details: Optional[Dict[str, Any]] = None) -> 'HealthCheckResponse':
        """Create unhealthy status response"""
        response_details = details or {}
        response_details["error"] = error

        return cls(
            service_name=service_name,
            status="unhealthy",
            version=version,
            timestamp=datetime.utcnow().isoformat(),
            uptime_seconds=uptime_seconds,
            details=response_details
        )