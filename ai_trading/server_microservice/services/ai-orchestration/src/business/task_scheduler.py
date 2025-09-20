"""
Task Scheduler - Microservice Version with Per-Service Infrastructure
Handles periodic tasks like data gap checking and downloading with microservice infrastructure:
- Per-service error handling untuk task execution failures
- Per-service performance tracking untuk scheduled operations
- Per-service event publishing untuk task lifecycle events
- Per-service validation untuk task configuration
- Per-service logging dengan structured task context
- Per-service dependency injection untuk components
"""

import asyncio
from datetime import datetime, time
from typing import Optional, Dict, Any, List
import time as time_module
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# PER-SERVICE INFRASTRUCTURE INTEGRATION
from ....shared.infrastructure.base_error_handler import BaseErrorHandler, ErrorCategory
from ....shared.infrastructure.base_event_publisher import BaseEventPublisher
from ....shared.infrastructure.base_logger import BaseLogger
from ....shared.infrastructure.base.base_performance import BasePerformance
from ....shared.infrastructure.base_validator import BaseValidator
from ....shared.infrastructure.base_config import BaseConfig

# Initialize per-service infrastructure
error_handler = BaseErrorHandler("ai-orchestration")
event_publisher = BaseEventPublisher("ai-orchestration")
logger = BaseLogger("ai-orchestration", "task_scheduler")
performance_tracker = BasePerformance()
validator = BaseValidator("ai-orchestration")
config = BaseConfig("ai-orchestration")

# Task scheduler performance metrics
task_metrics = {
    "total_scheduled_tasks": 0,
    "successful_executions": 0,
    "failed_executions": 0,
    "data_checks_performed": 0,
    "forced_checks_performed": 0,
    "avg_execution_time_ms": 0,
    "events_published": 0,
    "scheduler_starts": 0,
    "scheduler_stops": 0
}

class ScheduledTasksManager:
    """
    Enhanced Scheduled Tasks Manager with Per-Service Infrastructure
    
    Manages scheduled tasks for the trading system dengan microservice infrastructure:
    - Performance tracking untuk all task operations
    - Per-service error handling with recovery mechanisms
    - Event publishing untuk task lifecycle management
    - Configuration validation dan management
    - Per-service logging dengan structured context
    """
    
    def __init__(self, scheduler_config: dict, data_bridge_client=None):
        self.start_time = time_module.perf_counter()
        
        try:
            # Validate initialization parameters
            validation_result = validator.validate_dict(
                data={"config": scheduler_config, "data_bridge_available": data_bridge_client is not None},
                schema={
                    "config": {"type": "dict", "required": True},
                    "data_bridge_available": {"type": "bool", "required": True}
                },
                context="task_scheduler_initialization"
            )
            
            if not validation_result['valid']:
                error_response = error_handler.handle_error(
                    error=ValueError(f"Task scheduler initialization validation failed: {validation_result['errors']}"),
                    error_category=ErrorCategory.VALIDATION_ERROR,
                    context={
                        "component": "task_scheduler",
                        "operation": "initialization",
                        "config_available": scheduler_config is not None
                    }
                )
                logger.error(f"Task scheduler initialization validation failed: {error_response}")
                raise ValueError(f"Validation failed: {validation_result['errors']}")
            
            # Store configuration through per-service config
            self.config = scheduler_config
            self.data_bridge_client = data_bridge_client
            
            # Initialize scheduler with enhanced error handling
            try:
                self.scheduler = AsyncIOScheduler()
                logger.debug("AsyncIOScheduler initialized successfully")
            except Exception as e:
                error_response = error_handler.handle_error(
                    error=e,
                    error_category=ErrorCategory.SYSTEM_ERROR,
                    context={
                        "component": "apscheduler",
                        "operation": "initialize_scheduler"
                    }
                )
                logger.error(f"Failed to initialize scheduler: {error_response}")
                raise
            
            # Initialize data bridge client availability check
            if data_bridge_client:
                logger.debug("Data bridge client available for task scheduling")
            else:
                logger.warning("Data bridge client not available - some tasks may be limited")
            
            # State management
            self.is_running = False
            self.scheduled_jobs = {}
            
            # Record initialization performance
            initialization_time = (time_module.perf_counter() - self.start_time) * 1000
            performance_tracker.record_operation(
                operation_name="task_scheduler_initialization",
                duration_ms=initialization_time,
                success=True,
                metadata={
                    "data_bridge_available": self.data_bridge_client is not None,
                    "config_provided": scheduler_config is not None
                }
            )
            
            # Publish initialization event
            event_publisher.publish_event(
                event_type="task_scheduler_initialized",
                data={
                    "initialization_time_ms": initialization_time,
                    "data_bridge_available": self.data_bridge_client is not None,
                    "timestamp": datetime.now().isoformat()
                },
                context="task_scheduler"
            )
            task_metrics["events_published"] += 1
            
            logger.info(
                f"Task scheduler initialized successfully in {initialization_time:.2f}ms - Data bridge: {'Available' if self.data_bridge_client else 'Not Available'}"
            )
            
        except Exception as e:
            # Handle initialization failure
            initialization_time = (time_module.perf_counter() - self.start_time) * 1000
            
            error_response = error_handler.handle_error(
                error=e,
                error_category=ErrorCategory.SYSTEM_ERROR,
                context={
                    "component": "task_scheduler",
                    "operation": "initialization"
                }
            )
            logger.error(f"Task scheduler initialization failed: {error_response}")
            
            # Record failed initialization
            performance_tracker.record_operation(
                operation_name="task_scheduler_initialization",
                duration_ms=initialization_time,
                success=False,
                metadata={"error": str(e)}
            )
            
            # Publish initialization failure event
            event_publisher.publish_event(
                event_type="task_scheduler_initialization_failed",
                data={
                    "error": str(e),
                    "initialization_time_ms": initialization_time
                },
                context="task_scheduler"
            )
            
            raise
        
    async def start(self):
        """Start the scheduled tasks dengan PER-SERVICE INFRASTRUCTURE"""
        start_time = time_module.perf_counter()
        
        try:
            # Validate scheduler start request
            validation_result = validator.validate_dict(
                data={
                    "is_currently_running": self.is_running,
                    "scheduler_available": self.scheduler is not None
                },
                schema={
                    "is_currently_running": {"type": "bool", "required": True},
                    "scheduler_available": {"type": "bool", "required": True}
                },
                context="task_scheduler_start"
            )
            
            if not validation_result['valid']:
                error_response = error_handler.handle_error(
                    error=ValueError(f"Task scheduler start validation failed: {validation_result['errors']}"),
                    error_category=ErrorCategory.VALIDATION_ERROR,
                    context={
                        "component": "task_scheduler",
                        "operation": "start_scheduler",
                        "is_running": self.is_running
                    }
                )
                logger.warning(f"Start validation failed: {error_response}")
                return
            
            if self.is_running:
                logger.warning("Scheduled tasks already running - skipping start")
                return
            
            # Publish scheduler start event
            event_publisher.publish_event(
                event_type="task_scheduler_start_requested",
                data={"timestamp": datetime.now().isoformat()},
                context="task_scheduler"
            )
            task_metrics["events_published"] += 1
            
            # Configure scheduled tasks based on config
            try:
                await self._configure_tasks()
                logger.debug("Task configuration completed successfully")
            except Exception as e:
                error_response = error_handler.handle_error(
                    error=e,
                    error_category=ErrorCategory.CONFIGURATION_ERROR,
                    context={
                        "component": "task_configuration",
                        "operation": "configure_scheduled_tasks"
                    }
                )
                logger.error(f"Task configuration failed: {error_response}")
                raise
            
            # Start scheduler with error handling
            try:
                self.scheduler.start()
                self.is_running = True
                logger.debug("APScheduler started successfully")
            except Exception as e:
                error_response = error_handler.handle_error(
                    error=e,
                    error_category=ErrorCategory.SYSTEM_ERROR,
                    context={
                        "component": "apscheduler",
                        "operation": "start_scheduler"
                    }
                )
                logger.error(f"Failed to start scheduler: {error_response}")
                raise
            
            # Run initial data check if enabled and data bridge available
            data_config = self.config.get('data_collection', {})
            auto_download = data_config.get('auto_download', {})
            
            if auto_download.get('enabled', False) and self.data_bridge_client:
                try:
                    logger.info("Running initial data check")
                    await self.check_and_download_missing_data()
                    logger.debug("Initial data check completed successfully")
                except Exception as e:
                    error_response = error_handler.handle_error(
                        error=e,
                        error_category=ErrorCategory.SYSTEM_ERROR,
                        context={
                            "component": "initial_data_check",
                            "operation": "run_initial_check"
                        }
                    )
                    logger.warning(f"Initial data check failed: {error_response}")
                    # Don't raise - scheduler should still start even if initial check fails
            
            # Record performance metrics
            processing_time = (time_module.perf_counter() - start_time) * 1000
            performance_tracker.record_operation(
                operation_name="task_scheduler_start",
                duration_ms=processing_time,
                success=True,
                metadata={
                    "tasks_configured": len(self.scheduled_jobs),
                    "initial_check_enabled": auto_download.get('enabled', False)
                }
            )
            
            # Update success metrics
            task_metrics["scheduler_starts"] += 1
            
            # Publish successful start event
            event_publisher.publish_event(
                event_type="task_scheduler_started",
                data={
                    "processing_time_ms": processing_time,
                    "tasks_configured": len(self.scheduled_jobs),
                    "initial_check_enabled": auto_download.get('enabled', False),
                    "timestamp": datetime.now().isoformat()
                },
                context="task_scheduler"
            )
            
            logger.info(
                f"Task scheduler started successfully in {processing_time:.2f}ms - {len(self.scheduled_jobs)} tasks configured"
            )
            
        except Exception as e:
            # Handle scheduler start failure
            processing_time = (time_module.perf_counter() - start_time) * 1000
            
            error_response = error_handler.handle_error(
                error=e,
                error_category=ErrorCategory.SYSTEM_ERROR,
                context={
                    "component": "task_scheduler",
                    "operation": "start_scheduler"
                }
            )
            logger.error(f"Failed to start scheduled tasks: {error_response}")
            
            # Publish start failure event
            event_publisher.publish_event(
                event_type="task_scheduler_start_failed",
                data={
                    "error": str(e),
                    "processing_time_ms": processing_time
                },
                context="task_scheduler"
            )
            
            # Record failed performance metric
            performance_tracker.record_operation(
                operation_name="task_scheduler_start",
                duration_ms=processing_time,
                success=False,
                metadata={"error": str(e)}
            )
            
            # Reset state on failure
            self.is_running = False
            
            raise
    
    async def stop(self):
        """Stop the scheduled tasks dengan PER-SERVICE INFRASTRUCTURE"""
        start_time = time_module.perf_counter()
        
        try:
            # Validate scheduler stop request
            validation_result = validator.validate_dict(
                data={
                    "is_currently_running": self.is_running,
                    "scheduler_available": self.scheduler is not None
                },
                schema={
                    "is_currently_running": {"type": "bool", "required": True},
                    "scheduler_available": {"type": "bool", "required": True}
                },
                context="task_scheduler_stop"
            )
            
            if not validation_result['valid']:
                error_response = error_handler.handle_error(
                    error=ValueError(f"Task scheduler stop validation failed: {validation_result['errors']}"),
                    error_category=ErrorCategory.VALIDATION_ERROR,
                    context={
                        "component": "task_scheduler",
                        "operation": "stop_scheduler",
                        "is_running": self.is_running
                    }
                )
                logger.warning(f"Stop validation failed: {error_response}")
                return
            
            if not self.is_running:
                logger.info("Scheduled tasks already stopped - skipping stop")
                return
            
            # Publish scheduler stop event
            event_publisher.publish_event(
                event_type="task_scheduler_stop_requested",
                data={
                    "active_jobs": len(self.scheduled_jobs),
                    "timestamp": datetime.now().isoformat()
                },
                context="task_scheduler"
            )
            task_metrics["events_published"] += 1
            
            # Shutdown scheduler with error handling
            try:
                self.scheduler.shutdown(wait=True)
                self.is_running = False
                logger.debug("APScheduler shutdown completed")
            except Exception as e:
                error_response = error_handler.handle_error(
                    error=e,
                    error_category=ErrorCategory.SYSTEM_ERROR,
                    context={
                        "component": "apscheduler",
                        "operation": "shutdown_scheduler"
                    }
                )
                logger.error(f"Failed to shutdown scheduler cleanly: {error_response}")
                # Force state reset even if shutdown fails
                self.is_running = False
            
            # Clear scheduled jobs tracking
            jobs_count = len(self.scheduled_jobs)
            self.scheduled_jobs.clear()
            
            # Record performance metrics
            processing_time = (time_module.perf_counter() - start_time) * 1000
            performance_tracker.record_operation(
                operation_name="task_scheduler_stop",
                duration_ms=processing_time,
                success=True,
                metadata={"jobs_stopped": jobs_count}
            )
            
            # Update success metrics
            task_metrics["scheduler_stops"] += 1
            
            # Publish successful stop event
            event_publisher.publish_event(
                event_type="task_scheduler_stopped",
                data={
                    "processing_time_ms": processing_time,
                    "jobs_stopped": jobs_count,
                    "timestamp": datetime.now().isoformat()
                },
                context="task_scheduler"
            )
            
            logger.info(
                f"Task scheduler stopped successfully in {processing_time:.2f}ms - {jobs_count} jobs stopped"
            )
            
        except Exception as e:
            # Handle scheduler stop failure
            processing_time = (time_module.perf_counter() - start_time) * 1000
            
            error_response = error_handler.handle_error(
                error=e,
                error_category=ErrorCategory.SYSTEM_ERROR,
                context={
                    "component": "task_scheduler",
                    "operation": "stop_scheduler"
                }
            )
            logger.error(f"Failed to stop scheduled tasks: {error_response}")
            
            # Publish stop failure event
            event_publisher.publish_event(
                event_type="task_scheduler_stop_failed",
                data={
                    "error": str(e),
                    "processing_time_ms": processing_time
                },
                context="task_scheduler"
            )
            
            # Record failed performance metric
            performance_tracker.record_operation(
                operation_name="task_scheduler_stop",
                duration_ms=processing_time,
                success=False,
                metadata={"error": str(e)}
            )
            
            # Force state reset on failure
            self.is_running = False
            
            raise
    
    async def _configure_tasks(self):
        """Configure scheduled tasks based on configuration dengan PER-SERVICE INFRASTRUCTURE"""
        config_start_time = time_module.perf_counter()
        
        try:
            # Validate task configuration
            validation_result = validator.validate_dict(
                data={
                    "config": self.config,
                    "data_bridge_available": self.data_bridge_client is not None
                },
                schema={
                    "config": {"type": "dict", "required": True},
                    "data_bridge_available": {"type": "bool", "required": True}
                },
                context="task_configuration"
            )
            
            if not validation_result['valid']:
                error_response = error_handler.handle_error(
                    error=ValueError(f"Task configuration validation failed: {validation_result['errors']}"),
                    error_category=ErrorCategory.VALIDATION_ERROR,
                    context={
                        "component": "task_configuration",
                        "operation": "configure_tasks",
                        "config_available": self.config is not None
                    }
                )
                logger.warning(f"Task configuration validation failed: {error_response}")
                return
            
            # Get configuration with error handling
            try:
                data_config = self.config.get('data_collection', {})
                auto_download = data_config.get('auto_download', {})
            except Exception as e:
                error_response = error_handler.handle_error(
                    error=e,
                    error_category=ErrorCategory.CONFIGURATION_ERROR,
                    context={
                        "component": "task_configuration",
                        "operation": "get_data_collection_config"
                    }
                )
                logger.error(f"Failed to get data collection config: {error_response}")
                raise
            
            if auto_download.get('enabled', False):
                interval = auto_download.get('check_interval', 'daily')
                check_time = auto_download.get('check_time', '03:00')
                
                logger.debug(f"Configuring {interval} data check at {check_time}")
                
                # Configure based on interval type
                try:
                    if interval == 'daily':
                        await self._configure_daily_task(check_time)
                    elif interval == 'hourly':
                        await self._configure_hourly_task()
                    elif interval == 'weekly':
                        await self._configure_weekly_task(check_time)
                    else:
                        error_response = error_handler.handle_error(
                            error=ValueError(f"Invalid interval type: {interval}"),
                            error_category=ErrorCategory.VALIDATION_ERROR,
                            context={
                                "component": "task_configuration",
                                "operation": "configure_task_interval",
                                "interval": interval
                            }
                        )
                        logger.warning(f"Invalid interval configuration: {error_response}")
                except Exception as e:
                    error_response = error_handler.handle_error(
                        error=e,
                        error_category=ErrorCategory.CONFIGURATION_ERROR,
                        context={
                            "component": "task_configuration",
                            "operation": f"configure_{interval}_task"
                        }
                    )
                    logger.error(f"Failed to configure {interval} task: {error_response}")
                    raise
            else:
                logger.info("Auto download disabled - no tasks scheduled")
            
            # Record configuration performance
            config_time = (time_module.perf_counter() - config_start_time) * 1000
            performance_tracker.record_operation(
                operation_name="task_configuration",
                duration_ms=config_time,
                success=True,
                metadata={
                    "tasks_configured": len(self.scheduled_jobs),
                    "auto_download_enabled": auto_download.get('enabled', False)
                }
            )
            
            # Publish configuration completion event
            event_publisher.publish_event(
                event_type="task_configuration_completed",
                data={
                    "tasks_configured": len(self.scheduled_jobs),
                    "configuration_time_ms": config_time,
                    "auto_download_enabled": auto_download.get('enabled', False),
                    "timestamp": datetime.now().isoformat()
                },
                context="task_scheduler"
            )
            task_metrics["events_published"] += 1
            
            logger.info(
                f"Task configuration completed in {config_time:.2f}ms - {len(self.scheduled_jobs)} tasks configured"
            )
            
        except Exception as e:
            # Handle configuration failure
            config_time = (time_module.perf_counter() - config_start_time) * 1000
            
            error_response = error_handler.handle_error(
                error=e,
                error_category=ErrorCategory.CONFIGURATION_ERROR,
                context={
                    "component": "task_scheduler",
                    "operation": "configure_tasks"
                }
            )
            logger.error(f"Task configuration failed: {error_response}")
            
            # Publish configuration failure event
            event_publisher.publish_event(
                event_type="task_configuration_failed",
                data={
                    "error": str(e),
                    "configuration_time_ms": config_time
                },
                context="task_scheduler"
            )
            
            # Record failed performance metric
            performance_tracker.record_operation(
                operation_name="task_configuration",
                duration_ms=config_time,
                success=False,
                metadata={"error": str(e)}
            )
            
            raise
    
    async def _configure_daily_task(self, check_time: str):
        """Configure daily data check task"""
        try:
            # Parse time with validation
            hour, minute = map(int, check_time.split(':'))
            
            if not (0 <= hour <= 23) or not (0 <= minute <= 59):
                raise ValueError(f"Invalid time format: {check_time}")
            
            # Schedule daily data check
            job = self.scheduler.add_job(
                self.check_and_download_missing_data,
                CronTrigger(hour=hour, minute=minute),
                id='daily_data_check',
                name='Daily Data Gap Check',
                misfire_grace_time=3600  # 1 hour grace time
            )
            
            self.scheduled_jobs['daily_data_check'] = {
                'id': 'daily_data_check',
                'name': 'Daily Data Gap Check',
                'trigger': f"Daily at {check_time}",
                'job': job
            }
            
            logger.info(f"Scheduled daily data check at {check_time}")
            
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                error_category=ErrorCategory.CONFIGURATION_ERROR,
                context={
                    "component": "daily_task_configuration",
                    "operation": "configure_daily_data_check"
                }
            )
            logger.error(f"Failed to configure daily task: {error_response}")
            raise
    
    async def _configure_hourly_task(self):
        """Configure hourly data check task"""
        try:
            # Schedule hourly data check
            job = self.scheduler.add_job(
                self.check_and_download_missing_data,
                'interval',
                hours=1,
                id='hourly_data_check',
                name='Hourly Data Gap Check'
            )
            
            self.scheduled_jobs['hourly_data_check'] = {
                'id': 'hourly_data_check',
                'name': 'Hourly Data Gap Check',
                'trigger': 'Every hour',
                'job': job
            }
            
            logger.info("Scheduled hourly data check")
            
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                error_category=ErrorCategory.CONFIGURATION_ERROR,
                context={
                    "component": "hourly_task_configuration",
                    "operation": "configure_hourly_data_check"
                }
            )
            logger.error(f"Failed to configure hourly task: {error_response}")
            raise
    
    async def _configure_weekly_task(self, check_time: str):
        """Configure weekly data check task"""
        try:
            # Parse time with validation
            hour, minute = map(int, check_time.split(':'))
            
            if not (0 <= hour <= 23) or not (0 <= minute <= 59):
                raise ValueError(f"Invalid time format: {check_time}")
            
            # Schedule weekly data check (Monday at specified time)
            job = self.scheduler.add_job(
                self.check_and_download_missing_data,
                CronTrigger(day_of_week='mon', hour=hour, minute=minute),
                id='weekly_data_check',
                name='Weekly Data Gap Check'
            )
            
            self.scheduled_jobs['weekly_data_check'] = {
                'id': 'weekly_data_check',
                'name': 'Weekly Data Gap Check',
                'trigger': f"Weekly on Monday at {check_time}",
                'job': job
            }
            
            logger.info(f"Scheduled weekly data check on Monday at {check_time}")
            
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                error_category=ErrorCategory.CONFIGURATION_ERROR,
                context={
                    "component": "weekly_task_configuration",
                    "operation": "configure_weekly_data_check"
                }
            )
            logger.error(f"Failed to configure weekly task: {error_response}")
            raise
    
    async def check_and_download_missing_data(self):
        """Check for missing data and download if needed - delegates to data-bridge service"""
        operation_start = time_module.perf_counter()
        
        try:
            if not self.data_bridge_client:
                logger.warning("Data bridge client not available - skipping data check")
                return
            
            logger.info("Starting scheduled data gap check")
            
            # Publish data check start event
            event_publisher.publish_event(
                event_type="data_check_started",
                data={"timestamp": datetime.now().isoformat()},
                context="task_scheduler"
            )
            
            # Call data-bridge service for data checking and downloading
            try:
                result = await self.data_bridge_client.check_and_download_missing_data()
                
                # Record successful operation
                operation_time = (time_module.perf_counter() - operation_start) * 1000
                performance_tracker.record_operation(
                    operation_name="scheduled_data_check",
                    duration_ms=operation_time,
                    success=True,
                    metadata=result
                )
                
                # Update metrics
                task_metrics["data_checks_performed"] += 1
                task_metrics["successful_executions"] += 1
                
                # Publish successful data check event
                event_publisher.publish_event(
                    event_type="data_check_completed",
                    data={
                        "result": result,
                        "operation_time_ms": operation_time,
                        "timestamp": datetime.now().isoformat()
                    },
                    context="task_scheduler"
                )
                
                logger.info(f"Scheduled data check completed successfully in {operation_time:.2f}ms")
                
            except Exception as e:
                # Handle data check failure
                operation_time = (time_module.perf_counter() - operation_start) * 1000
                
                error_response = error_handler.handle_error(
                    error=e,
                    error_category=ErrorCategory.EXTERNAL_SERVICE_ERROR,
                    context={
                        "component": "data_bridge_client",
                        "operation": "check_and_download_missing_data"
                    }
                )
                logger.error(f"Scheduled data check failed: {error_response}")
                
                # Record failed operation
                performance_tracker.record_operation(
                    operation_name="scheduled_data_check",
                    duration_ms=operation_time,
                    success=False,
                    metadata={"error": str(e)}
                )
                
                # Update failure metrics
                task_metrics["failed_executions"] += 1
                
                # Publish failed data check event
                event_publisher.publish_event(
                    event_type="data_check_failed",
                    data={
                        "error": str(e),
                        "operation_time_ms": operation_time,
                        "timestamp": datetime.now().isoformat()
                    },
                    context="task_scheduler"
                )
                
                # Don't raise - allow scheduler to continue with next execution
                
        except Exception as e:
            # Handle unexpected errors
            operation_time = (time_module.perf_counter() - operation_start) * 1000
            
            error_response = error_handler.handle_error(
                error=e,
                error_category=ErrorCategory.SYSTEM_ERROR,
                context={
                    "component": "task_scheduler",
                    "operation": "check_and_download_missing_data"
                }
            )
            logger.error(f"Unexpected error during data check: {error_response}")
            
            # Record failed operation
            performance_tracker.record_operation(
                operation_name="scheduled_data_check",
                duration_ms=operation_time,
                success=False,
                metadata={"error": str(e)}
            )
            
            # Update failure metrics
            task_metrics["failed_executions"] += 1
    
    async def force_data_check(self):
        """Force immediate data check - manually triggered"""
        try:
            logger.info("Force data check requested")
            
            # Publish force check event
            event_publisher.publish_event(
                event_type="force_data_check_requested",
                data={"timestamp": datetime.now().isoformat()},
                context="task_scheduler"
            )
            
            # Execute data check
            await self.check_and_download_missing_data()
            
            # Update metrics
            task_metrics["forced_checks_performed"] += 1
            
            logger.info("Force data check completed")
            
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                error_category=ErrorCategory.SYSTEM_ERROR,
                context={
                    "component": "task_scheduler",
                    "operation": "force_data_check"
                }
            )
            logger.error(f"Force data check failed: {error_response}")
            raise
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        try:
            return {
                "is_running": self.is_running,
                "scheduled_jobs": len(self.scheduled_jobs),
                "jobs_detail": list(self.scheduled_jobs.keys()),
                "metrics": task_metrics.copy(),
                "data_bridge_available": self.data_bridge_client is not None,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            error_response = error_handler.handle_error(
                error=e,
                error_category=ErrorCategory.SYSTEM_ERROR,
                context={
                    "component": "task_scheduler",
                    "operation": "get_scheduler_status"
                }
            )
            logger.error(f"Failed to get scheduler status: {error_response}")
            return {"error": str(e)}