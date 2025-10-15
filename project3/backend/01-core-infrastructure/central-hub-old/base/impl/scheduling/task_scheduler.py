#!/usr/bin/env python3
"""
Task Scheduler - Central Hub scheduling engine
Manages scheduled tasks and periodic operations across services
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid

logger = logging.getLogger("central-hub.scheduler")


class TaskStatus(Enum):
    """Scheduled task status"""
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    FAILED = "failed"


class TaskType(Enum):
    """Scheduled task types"""
    INTERVAL = "interval"  # Execute every N seconds
    CRON = "cron"          # Execute based on cron schedule
    ONCE = "once"          # Execute once at specific time


@dataclass
class ScheduledTask:
    """Scheduled task definition"""
    task_id: str
    name: str
    task_type: TaskType
    target_service: str
    operation: str
    schedule_config: Dict[str, Any]  # interval_seconds, cron_expression, execute_at
    input_data: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.ACTIVE
    created_at: float = field(default_factory=time.time)
    last_execution: Optional[float] = None
    next_execution: Optional[float] = None
    execution_count: int = 0
    failure_count: int = 0
    max_failures: int = 5


@dataclass
class TaskExecution:
    """Task execution record"""
    execution_id: str
    task_id: str
    started_at: float
    completed_at: Optional[float] = None
    success: bool = False
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class TaskScheduler:
    """
    Central Hub task scheduling engine
    Manages periodic and scheduled operations across all services
    """

    def __init__(self, service_registry: Dict[str, Dict[str, Any]]):
        self.service_registry = service_registry
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.execution_history: List[TaskExecution] = []
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.scheduler_running = False
        self.logger = logger

        # Initialize default scheduled tasks
        self._initialize_default_tasks()

    def _initialize_default_tasks(self):
        """Initialize default scheduled tasks"""

        # Health check task - every 30 seconds
        self.schedule_task(
            name="system_health_check",
            task_type=TaskType.INTERVAL,
            target_service="central-hub",
            operation="health_check_all_services",
            schedule_config={"interval_seconds": 30}
        )

        # Service registry cleanup - every 5 minutes
        self.schedule_task(
            name="service_registry_cleanup",
            task_type=TaskType.INTERVAL,
            target_service="central-hub",
            operation="cleanup_inactive_services",
            schedule_config={"interval_seconds": 300}
        )

        # Analytics data aggregation - every 10 minutes
        self.schedule_task(
            name="analytics_aggregation",
            task_type=TaskType.INTERVAL,
            target_service="analytics-service",
            operation="aggregate_metrics",
            schedule_config={"interval_seconds": 600}
        )

        # Trading signal generation - every 1 minute
        self.schedule_task(
            name="trading_signal_generation",
            task_type=TaskType.INTERVAL,
            target_service="trading-engine",
            operation="generate_periodic_signals",
            schedule_config={"interval_seconds": 60}
        )

    def schedule_task(
        self,
        name: str,
        task_type: TaskType,
        target_service: str,
        operation: str,
        schedule_config: Dict[str, Any],
        input_data: Dict[str, Any] = None
    ) -> str:
        """Schedule a new task"""

        task_id = str(uuid.uuid4())

        task = ScheduledTask(
            task_id=task_id,
            name=name,
            task_type=task_type,
            target_service=target_service,
            operation=operation,
            schedule_config=schedule_config,
            input_data=input_data or {}
        )

        # Calculate next execution time
        task.next_execution = self._calculate_next_execution(task)

        self.scheduled_tasks[task_id] = task
        self.logger.info(f"Scheduled task: {name} ({task_id}) for {target_service}")

        return task_id

    def _calculate_next_execution(self, task: ScheduledTask) -> float:
        """Calculate next execution time for a task"""
        current_time = time.time()

        if task.task_type == TaskType.INTERVAL:
            interval = task.schedule_config.get("interval_seconds", 60)
            return current_time + interval

        elif task.task_type == TaskType.ONCE:
            execute_at = task.schedule_config.get("execute_at")
            if isinstance(execute_at, (int, float)):
                return execute_at
            else:
                # If not a timestamp, execute immediately
                return current_time

        elif task.task_type == TaskType.CRON:
            # Simple cron implementation - for now just treat as hourly
            return current_time + 3600

        return current_time + 60  # Default to 1 minute

    async def start_scheduler(self):
        """Start the task scheduler"""
        if self.scheduler_running:
            return

        self.scheduler_running = True
        self.logger.info("Task scheduler started")

        while self.scheduler_running:
            try:
                await self._process_scheduled_tasks()
                await asyncio.sleep(1)  # Check every second
            except Exception as e:
                self.logger.error(f"Scheduler error: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying

    async def stop_scheduler(self):
        """Stop the task scheduler"""
        self.scheduler_running = False

        # Cancel all running tasks
        for task_id, running_task in self.running_tasks.items():
            running_task.cancel()

        self.running_tasks.clear()
        self.logger.info("Task scheduler stopped")

    async def _process_scheduled_tasks(self):
        """Process tasks that are ready for execution"""
        current_time = time.time()

        for task_id, task in list(self.scheduled_tasks.items()):
            if (task.status == TaskStatus.ACTIVE and
                task.next_execution and
                current_time >= task.next_execution and
                task_id not in self.running_tasks):

                # Execute task
                running_task = asyncio.create_task(self._execute_task(task))
                self.running_tasks[task_id] = running_task

    async def _execute_task(self, task: ScheduledTask):
        """Execute a scheduled task"""
        execution_id = str(uuid.uuid4())
        execution = TaskExecution(
            execution_id=execution_id,
            task_id=task.task_id,
            started_at=time.time()
        )

        try:
            self.logger.info(f"Executing task: {task.name} ({task.task_id})")

            # Check if target service is available (skip for central-hub internal operations)
            if task.target_service not in ["central-hub", "self"]:
                service_info = self.service_registry.get(task.target_service)
                if not service_info or service_info.get('status') != 'active':
                    raise Exception(f"Target service {task.target_service} not available")

            # Execute real task
            result = await self._execute_real_task(task)

            # Mark execution as successful
            execution.success = True
            execution.result = result
            execution.completed_at = time.time()

            # Update task statistics
            task.execution_count += 1
            task.last_execution = execution.started_at
            task.failure_count = 0  # Reset failure count on success

            self.logger.info(f"Task completed: {task.name} ({task.task_id})")

        except Exception as e:
            execution.success = False
            execution.error_message = str(e)
            execution.completed_at = time.time()

            # Update task failure statistics
            task.failure_count += 1

            if task.failure_count >= task.max_failures:
                task.status = TaskStatus.FAILED
                self.logger.error(f"Task failed permanently: {task.name} ({task.task_id}) - {str(e)}")
            else:
                self.logger.warning(f"Task failed: {task.name} ({task.task_id}) - {str(e)}")

        finally:
            # Schedule next execution
            if task.status == TaskStatus.ACTIVE:
                if task.task_type == TaskType.ONCE:
                    task.status = TaskStatus.STOPPED
                else:
                    task.next_execution = self._calculate_next_execution(task)

            # Record execution
            self.execution_history.append(execution)

            # Clean up running task reference
            self.running_tasks.pop(task.task_id, None)

    async def _execute_real_task(self, task: ScheduledTask) -> Dict[str, Any]:
        """Execute real task operation"""

        if task.operation == "health_check_all_services":
            return await self._execute_health_check_all()

        elif task.operation == "cleanup_inactive_services":
            return await self._execute_cleanup_inactive()

        elif task.operation == "aggregate_metrics":
            return await self._execute_aggregate_metrics(task)

        elif task.operation == "generate_periodic_signals":
            return await self._execute_generate_signals(task)

        else:
            return await self._execute_custom_operation(task)

    async def _execute_health_check_all(self) -> Dict[str, Any]:
        """Real health check execution"""
        import httpx

        healthy_services = 0
        total_services = len(self.service_registry)

        async with httpx.AsyncClient() as client:
            for service_name, service_info in self.service_registry.items():
                try:
                    health_url = f"http://{service_info['host']}:{service_info['port']}{service_info.get('health_endpoint', '/health')}"
                    response = await client.get(health_url, timeout=5.0)
                    if response.status_code == 200:
                        healthy_services += 1
                        # Update service last_seen
                        service_info['last_seen'] = time.time()
                        if self.db_manager:
                            await self.db_manager.execute(
                                "UPDATE service_registry SET last_seen = CURRENT_TIMESTAMP WHERE service_name = $1",
                                {"service_name": service_name}
                            )
                except Exception as e:
                    self.logger.warning(f"Health check failed for {service_name}: {str(e)}")

        return {
            "operation": "health_check",
            "services_checked": total_services,
            "healthy_services": healthy_services,
            "timestamp": time.time()
        }

    async def _execute_cleanup_inactive(self) -> Dict[str, Any]:
        """Real cleanup of inactive services"""
        current_time = time.time()
        inactive_threshold = current_time - 300  # 5 minutes

        inactive_services = []
        for service_name, service_info in list(self.service_registry.items()):
            last_seen = service_info.get('last_seen', 0)
            if last_seen < inactive_threshold:
                inactive_services.append(service_name)
                # Remove from registry
                del self.service_registry[service_name]

                # Remove from database
                if self.db_manager:
                    await self.db_manager.execute(
                        "DELETE FROM service_registry WHERE service_name = $1",
                        {"service_name": service_name}
                    )

        return {
            "operation": "cleanup",
            "inactive_services_removed": len(inactive_services),
            "removed_services": inactive_services,
            "timestamp": time.time()
        }

    async def _execute_aggregate_metrics(self, task: ScheduledTask) -> Dict[str, Any]:
        """Real metrics aggregation"""
        if not self.db_manager:
            raise Exception("Database required for metrics aggregation")

        # Aggregate health metrics
        result = await self.db_manager.fetch_one(
            "SELECT COUNT(*) as total_metrics, AVG(response_time_ms) as avg_response_time FROM health_metrics WHERE timestamp > NOW() - INTERVAL '1 hour'"
        )

        return {
            "operation": "aggregation",
            "metrics_aggregated": result.get('total_metrics', 0),
            "avg_response_time_ms": result.get('avg_response_time', 0),
            "timestamp": time.time()
        }

    async def _execute_generate_signals(self, task: ScheduledTask) -> Dict[str, Any]:
        """Real signal generation coordination"""
        # Coordinate with trading engine
        if self.coordination_router:
            result = await self.coordination_router.route_message(
                message_type="generate_periodic_signals",
                target_service="trading-engine",
                data=task.input_data
            )
            return result
        else:
            # Direct HTTP call to trading engine
            import httpx
            trading_service = self.service_registry.get('trading-engine')
            if trading_service:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"http://{trading_service['host']}:{trading_service['port']}/signals/generate",
                        json=task.input_data,
                        timeout=30.0
                    )
                    return response.json()
            else:
                raise Exception("Trading engine not available")

    async def _execute_custom_operation(self, task: ScheduledTask) -> Dict[str, Any]:
        """Execute custom operation via service call"""
        service_info = self.service_registry.get(task.target_service)
        if not service_info:
            raise Exception(f"Target service {task.target_service} not found")

        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://{service_info['host']}:{service_info['port']}/{task.operation}",
                json=task.input_data,
                timeout=task.timeout_seconds
            )
            return response.json()

    def pause_task(self, task_id: str) -> bool:
        """Pause a scheduled task"""
        task = self.scheduled_tasks.get(task_id)
        if task and task.status == TaskStatus.ACTIVE:
            task.status = TaskStatus.PAUSED
            self.logger.info(f"Task paused: {task.name} ({task_id})")
            return True
        return False

    def resume_task(self, task_id: str) -> bool:
        """Resume a paused task"""
        task = self.scheduled_tasks.get(task_id)
        if task and task.status == TaskStatus.PAUSED:
            task.status = TaskStatus.ACTIVE
            task.next_execution = self._calculate_next_execution(task)
            self.logger.info(f"Task resumed: {task.name} ({task_id})")
            return True
        return False

    def remove_task(self, task_id: str) -> bool:
        """Remove a scheduled task"""
        if task_id in self.scheduled_tasks:
            task = self.scheduled_tasks.pop(task_id)

            # Cancel if currently running
            if task_id in self.running_tasks:
                self.running_tasks[task_id].cancel()
                self.running_tasks.pop(task_id)

            self.logger.info(f"Task removed: {task.name} ({task_id})")
            return True
        return False

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task"""
        task = self.scheduled_tasks.get(task_id)
        if not task:
            return None

        recent_executions = [
            {
                "execution_id": ex.execution_id,
                "started_at": ex.started_at,
                "completed_at": ex.completed_at,
                "success": ex.success,
                "error_message": ex.error_message
            }
            for ex in self.execution_history[-10:]
            if ex.task_id == task_id
        ]

        return {
            "task_id": task.task_id,
            "name": task.name,
            "status": task.status.value,
            "target_service": task.target_service,
            "operation": task.operation,
            "execution_count": task.execution_count,
            "failure_count": task.failure_count,
            "last_execution": task.last_execution,
            "next_execution": task.next_execution,
            "recent_executions": recent_executions
        }

    def get_scheduler_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        active_tasks = sum(1 for t in self.scheduled_tasks.values() if t.status == TaskStatus.ACTIVE)
        total_executions = len(self.execution_history)
        successful_executions = sum(1 for ex in self.execution_history if ex.success)

        return {
            "scheduler_running": self.scheduler_running,
            "total_tasks": len(self.scheduled_tasks),
            "active_tasks": active_tasks,
            "running_tasks": len(self.running_tasks),
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": successful_executions / total_executions if total_executions > 0 else 0,
            "task_types": {
                task_type.value: sum(1 for t in self.scheduled_tasks.values() if t.task_type == task_type)
                for task_type in TaskType
            }
        }