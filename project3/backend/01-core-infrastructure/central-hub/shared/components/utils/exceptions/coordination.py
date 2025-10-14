"""
Service Coordination exceptions
"""

from typing import List, Optional
from .base import CentralHubError, ErrorCode, ErrorSeverity


class CoordinationError(CentralHubError):
    """Base exception for coordination errors"""
    code = ErrorCode.COORDINATION_FAILED
    severity = ErrorSeverity.HIGH
    message = "Service coordination failed"


class WorkflowExecutionError(CoordinationError):
    """Workflow execution failed"""
    code = ErrorCode.WORKFLOW_EXECUTION_FAILED
    severity = ErrorSeverity.HIGH
    message = "Workflow execution failed"

    def __init__(self, workflow_id: str, workflow_name: str, step: Optional[str] = None, **kwargs):
        super().__init__(
            message=f"Workflow '{workflow_name}' (ID: {workflow_id}) failed" + (f" at step '{step}'" if step else ""),
            details={
                "workflow_id": workflow_id,
                "workflow_name": workflow_name,
                "failed_step": step
            },
            **kwargs
        )


class ServiceCommunicationError(CoordinationError):
    """Service-to-service communication failed"""
    code = ErrorCode.SERVICE_COMMUNICATION_ERROR
    severity = ErrorSeverity.HIGH
    message = "Service communication error"

    def __init__(self, source_service: str, target_service: str, operation: str, **kwargs):
        super().__init__(
            message=f"Communication failed: {source_service} → {target_service} ({operation})",
            details={
                "source_service": source_service,
                "target_service": target_service,
                "operation": operation
            },
            **kwargs
        )


class DeadlockDetectedError(CoordinationError):
    """Circular dependency or deadlock detected"""
    code = ErrorCode.DEADLOCK_DETECTED
    severity = ErrorSeverity.CRITICAL
    message = "Deadlock detected"

    def __init__(self, services_involved: List[str], **kwargs):
        super().__init__(
            message=f"Deadlock detected involving services: {', '.join(services_involved)}",
            details={"services_involved": services_involved},
            severity=ErrorSeverity.CRITICAL,
            **kwargs
        )
