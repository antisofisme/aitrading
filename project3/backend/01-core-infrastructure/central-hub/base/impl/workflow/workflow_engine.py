#!/usr/bin/env python3
"""
Workflow Engine - Central Hub workflow management
Manages cross-service workflows and orchestration
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("central-hub.workflow")


class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(Enum):
    """Workflow step status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """Individual workflow step definition"""
    step_id: str
    service: str
    operation: str
    input_data: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    timeout_seconds: int = 30
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class WorkflowExecution:
    """Workflow execution tracking"""
    workflow_id: str
    name: str
    status: WorkflowStatus
    steps: List[WorkflowStep]
    step_statuses: Dict[str, StepStatus] = field(default_factory=dict)
    step_results: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error_message: Optional[str] = None


class WorkflowEngine:
    """
    Central Hub workflow orchestration engine
    Manages complex multi-service workflows
    """

    def __init__(self, service_registry: Dict[str, Dict[str, Any]]):
        self.service_registry = service_registry
        self.active_workflows: Dict[str, WorkflowExecution] = {}
        self.workflow_history: List[WorkflowExecution] = []
        self.workflow_templates: Dict[str, List[WorkflowStep]] = {}
        self.logger = logger

        # Initialize default workflow templates
        self._initialize_default_templates()

    def _initialize_default_templates(self):
        """Initialize default workflow templates"""

        # Trading signal processing workflow
        self.workflow_templates["trading_signal_processing"] = [
            WorkflowStep(
                step_id="data_validation",
                service="data-bridge",
                operation="validate_market_data",
                dependencies=[]
            ),
            WorkflowStep(
                step_id="signal_generation",
                service="trading-engine",
                operation="generate_signals",
                dependencies=["data_validation"]
            ),
            WorkflowStep(
                step_id="risk_assessment",
                service="risk-management",
                operation="assess_signal_risk",
                dependencies=["signal_generation"]
            ),
            WorkflowStep(
                step_id="notification",
                service="notification-hub",
                operation="send_signal_notification",
                dependencies=["risk_assessment"]
            )
        ]

        # System health check workflow
        self.workflow_templates["system_health_check"] = [
            WorkflowStep(
                step_id="gateway_health",
                service="api-gateway",
                operation="health_check",
                dependencies=[]
            ),
            WorkflowStep(
                step_id="data_health",
                service="data-bridge",
                operation="health_check",
                dependencies=[]
            ),
            WorkflowStep(
                step_id="trading_health",
                service="trading-engine",
                operation="health_check",
                dependencies=[]
            ),
            WorkflowStep(
                step_id="analytics_health",
                service="analytics-service",
                operation="health_check",
                dependencies=[]
            ),
            WorkflowStep(
                step_id="health_summary",
                service="central-hub",
                operation="compile_health_summary",
                dependencies=["gateway_health", "data_health", "trading_health", "analytics_health"]
            )
        ]

    async def start_workflow(self, template_name: str, input_data: Dict[str, Any] = None) -> str:
        """Start a new workflow execution"""

        if template_name not in self.workflow_templates:
            raise ValueError(f"Unknown workflow template: {template_name}")

        workflow_id = str(uuid.uuid4())
        steps = self._prepare_workflow_steps(template_name, input_data or {})

        workflow = WorkflowExecution(
            workflow_id=workflow_id,
            name=template_name,
            status=WorkflowStatus.PENDING,
            steps=steps
        )

        # Initialize step statuses
        for step in steps:
            workflow.step_statuses[step.step_id] = StepStatus.PENDING

        self.active_workflows[workflow_id] = workflow
        self.logger.info(f"Started workflow: {template_name} ({workflow_id})")

        # Start execution in background
        asyncio.create_task(self._execute_workflow(workflow_id))

        return workflow_id

    def _prepare_workflow_steps(self, template_name: str, input_data: Dict[str, Any]) -> List[WorkflowStep]:
        """Prepare workflow steps with input data"""
        steps = []

        for template_step in self.workflow_templates[template_name]:
            step = WorkflowStep(
                step_id=template_step.step_id,
                service=template_step.service,
                operation=template_step.operation,
                input_data={**template_step.input_data, **input_data},
                dependencies=template_step.dependencies.copy(),
                timeout_seconds=template_step.timeout_seconds,
                max_retries=template_step.max_retries
            )
            steps.append(step)

        return steps

    async def _execute_workflow(self, workflow_id: str):
        """Execute workflow steps in dependency order"""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return

        try:
            workflow.status = WorkflowStatus.RUNNING
            workflow.started_at = time.time()

            # Execute steps based on dependencies
            while True:
                ready_steps = self._get_ready_steps(workflow)

                if not ready_steps:
                    # Check if all steps are completed
                    if all(status in [StepStatus.COMPLETED, StepStatus.SKIPPED, StepStatus.FAILED]
                           for status in workflow.step_statuses.values()):
                        break
                    else:
                        # Wait for running steps
                        await asyncio.sleep(0.1)
                        continue

                # Execute ready steps in parallel
                tasks = []
                for step in ready_steps:
                    workflow.step_statuses[step.step_id] = StepStatus.RUNNING
                    task = asyncio.create_task(self._execute_step(workflow_id, step))
                    tasks.append(task)

                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)

            # Determine final workflow status
            if any(status == StepStatus.FAILED for status in workflow.step_statuses.values()):
                workflow.status = WorkflowStatus.FAILED
            else:
                workflow.status = WorkflowStatus.COMPLETED

            workflow.completed_at = time.time()
            self.logger.info(f"Workflow completed: {workflow.name} ({workflow_id}) - {workflow.status.value}")

        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.error_message = str(e)
            workflow.completed_at = time.time()
            self.logger.error(f"Workflow failed: {workflow.name} ({workflow_id}) - {str(e)}")

        finally:
            # Move to history
            self.workflow_history.append(workflow)
            self.active_workflows.pop(workflow_id, None)

    def _get_ready_steps(self, workflow: WorkflowExecution) -> List[WorkflowStep]:
        """Get steps that are ready to execute (dependencies satisfied)"""
        ready_steps = []

        for step in workflow.steps:
            if workflow.step_statuses[step.step_id] != StepStatus.PENDING:
                continue

            # Check if all dependencies are completed
            dependencies_satisfied = all(
                workflow.step_statuses.get(dep_id) == StepStatus.COMPLETED
                for dep_id in step.dependencies
            )

            if dependencies_satisfied:
                ready_steps.append(step)

        return ready_steps

    async def _execute_step(self, workflow_id: str, step: WorkflowStep):
        """Execute a single workflow step"""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return

        try:
            # Simulate step execution
            self.logger.info(f"Executing step: {step.step_id} on {step.service}")

            # Check if service is available
            service_info = self.service_registry.get(step.service)
            if not service_info or service_info.get('status') != 'active':
                raise Exception(f"Service {step.service} not available")

            # Real operation execution via coordination router
            if hasattr(self, 'coordination_router') and self.coordination_router:
                result = await self.coordination_router.route_message(
                    message_type=step.operation,
                    target_service=step.service,
                    data=step.input_data
                )
            else:
                # Direct service call
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"http://{service_info['host']}:{service_info['port']}/{step.operation}",
                        json=step.input_data,
                        timeout=step.timeout_seconds
                    )
                    result = response.json()

            # Store real step result
            workflow.step_results[step.step_id] = {
                "service": step.service,
                "operation": step.operation,
                "status": "completed",
                "timestamp": time.time(),
                "data": result
            }

            workflow.step_statuses[step.step_id] = StepStatus.COMPLETED
            self.logger.info(f"Step completed: {step.step_id}")

        except Exception as e:
            workflow.step_statuses[step.step_id] = StepStatus.FAILED
            workflow.step_results[step.step_id] = {
                "error": str(e),
                "timestamp": time.time()
            }
            self.logger.error(f"Step failed: {step.step_id} - {str(e)}")

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow execution status"""
        workflow = self.active_workflows.get(workflow_id)

        if not workflow:
            # Check history
            for historical_workflow in self.workflow_history:
                if historical_workflow.workflow_id == workflow_id:
                    workflow = historical_workflow
                    break

        if not workflow:
            return None

        return {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "status": workflow.status.value,
            "steps": {
                step.step_id: {
                    "service": step.service,
                    "operation": step.operation,
                    "status": workflow.step_statuses.get(step.step_id, StepStatus.PENDING).value,
                    "result": workflow.step_results.get(step.step_id)
                }
                for step in workflow.steps
            },
            "created_at": workflow.created_at,
            "started_at": workflow.started_at,
            "completed_at": workflow.completed_at,
            "execution_time_seconds": (
                (workflow.completed_at or time.time()) - (workflow.started_at or workflow.created_at)
            ) if workflow.started_at else None
        }

    def get_workflow_stats(self) -> Dict[str, Any]:
        """Get workflow engine statistics"""
        total_workflows = len(self.workflow_history) + len(self.active_workflows)
        completed_workflows = sum(1 for w in self.workflow_history if w.status == WorkflowStatus.COMPLETED)

        return {
            "active_workflows": len(self.active_workflows),
            "total_workflows": total_workflows,
            "completed_workflows": completed_workflows,
            "success_rate": completed_workflows / len(self.workflow_history) if self.workflow_history else 0,
            "available_templates": list(self.workflow_templates.keys())
        }