"""
📝 Comprehensive Decision Logging System
Structured audit capabilities with AI Brain methodology integration

FEATURES:
- Multi-level structured logging with full audit trails
- Integration with AI Brain decision validation methodology
- Real-time decision monitoring and alerting capabilities
- Comprehensive metrics tracking with performance correlation
- Pattern-based logging for continuous improvement insights
- Export capabilities for compliance and analysis requirements

LOGGING LEVELS:
1. TRACE - Detailed execution flow and internal state changes
2. DEBUG - Decision validation steps and intermediate calculations  
3. INFO - Key decision events and milestone achievements
4. WARN - Validation warnings and potential issues
5. ERROR - Decision failures and system errors
6. CRITICAL - System failures requiring immediate attention

STRUCTURED LOGGING COMPONENTS:
- Decision Context Logging - Full decision environment capture
- Validation Process Logging - Step-by-step validation tracking
- Execution Logging - Trade execution and outcome tracking
- Performance Logging - Impact assessment and correlation analysis
- Error Logging - Comprehensive error analysis and resolution tracking
- Audit Logging - Compliance and regulatory audit requirements
"""

import asyncio
import json
import logging
import structlog
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from collections import defaultdict, deque
import gzip
import os

# Local infrastructure
from ....shared.infrastructure.core.logger_core import CoreLogger
from ....shared.infrastructure.core.cache_core import CoreCache

# Initialize base components
base_logger = CoreLogger("trading-engine", "decision-logger")
cache = CoreCache("decision-logs", max_size=10000, default_ttl=86400)


class DecisionLogLevel(Enum):
    """Decision-specific log levels"""
    TRACE = "TRACE"
    DEBUG = "DEBUG" 
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DecisionLogCategory(Enum):
    """Categories of decision logs"""
    DECISION_CONTEXT = "decision_context"
    VALIDATION_PROCESS = "validation_process"
    AI_BRAIN_INTEGRATION = "ai_brain_integration"
    CONFIDENCE_ANALYSIS = "confidence_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    EXECUTION_TRACKING = "execution_tracking"
    PERFORMANCE_CORRELATION = "performance_correlation"
    PATTERN_RECOGNITION = "pattern_recognition"
    ERROR_ANALYSIS = "error_analysis"
    AUDIT_COMPLIANCE = "audit_compliance"


class AlertSeverity(Enum):
    """Alert severity levels for monitoring"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DecisionLogEntry:
    """Structured decision log entry"""
    
    # Basic identification
    log_id: str
    decision_id: str
    timestamp: datetime
    
    # Log classification
    level: DecisionLogLevel
    category: DecisionLogCategory
    
    # Content
    message: str
    structured_data: Dict[str, Any]
    
    # Context
    symbol: Optional[str] = None
    action: Optional[str] = None
    confidence: Optional[float] = None
    
    # Performance tracking
    execution_time_ms: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    
    # Error tracking
    error_code: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    stack_trace: Optional[str] = None
    
    # Correlation tracking
    correlation_id: Optional[str] = None
    parent_log_id: Optional[str] = None
    
    # Alert information
    alert_required: bool = False
    alert_severity: Optional[AlertSeverity] = None
    
    def __post_init__(self):
        if not self.log_id:
            self.log_id = str(uuid.uuid4())


@dataclass
class LoggingMetrics:
    """Logging system metrics"""
    
    # Volume metrics
    total_logs: int = 0
    logs_by_level: Dict[str, int] = None
    logs_by_category: Dict[str, int] = None
    
    # Performance metrics
    average_log_processing_ms: float = 0.0
    peak_memory_usage_mb: float = 0.0
    
    # Error tracking
    error_count: int = 0
    critical_count: int = 0
    
    # Alert metrics
    alerts_generated: int = 0
    alerts_by_severity: Dict[str, int] = None
    
    # System health
    logging_system_healthy: bool = True
    last_health_check: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.logs_by_level:
            self.logs_by_level = {level.value: 0 for level in DecisionLogLevel}
        if not self.logs_by_category:
            self.logs_by_category = {cat.value: 0 for cat in DecisionLogCategory}
        if not self.alerts_by_severity:
            self.alerts_by_severity = {sev.value: 0 for sev in AlertSeverity}


class DecisionLogger:
    """
    Comprehensive decision logging system with structured audit capabilities
    Integrates with AI Brain methodology for systematic decision tracking
    """
    
    def __init__(self, log_directory: str = "./logs/decisions"):
        """Initialize decision logger"""
        
        self.log_directory = log_directory
        self.ensure_log_directory()
        
        # Configure structured logging
        self.structured_logger = self._configure_structured_logger()
        
        # In-memory log storage for recent logs
        self.recent_logs: deque = deque(maxlen=5000)
        self.decision_logs: Dict[str, List[DecisionLogEntry]] = defaultdict(list)
        
        # Alerting system
        self.alert_rules: List[Dict[str, Any]] = []
        self.active_alerts: List[Dict[str, Any]] = []
        
        # Performance tracking
        self.logging_metrics = LoggingMetrics()\n        \n        # Pattern recognition\n        self.log_patterns: Dict[str, int] = defaultdict(int)\n        self.error_patterns: Dict[str, int] = defaultdict(int)\n        \n        # Export settings\n        self.auto_export_enabled = True\n        self.export_interval_hours = 24\n        self.last_export_time = datetime.now()\n        \n        # Initialize default alert rules\n        self._initialize_default_alert_rules()\n        \n        base_logger.info(\"Decision Logger initialized with structured audit capabilities\")\n    \n    def ensure_log_directory(self):\n        \"\"\"Ensure log directory exists\"\"\"\n        \n        try:\n            os.makedirs(self.log_directory, exist_ok=True)\n            os.makedirs(f\"{self.log_directory}/exports\", exist_ok=True)\n            os.makedirs(f\"{self.log_directory}/alerts\", exist_ok=True)\n        except Exception as e:\n            base_logger.error(f\"Failed to create log directories: {e}\")\n    \n    def _configure_structured_logger(self) -> structlog.BoundLogger:\n        \"\"\"Configure structured logging with custom processors\"\"\"\n        \n        try:\n            # Configure structlog\n            structlog.configure(\n                processors=[\n                    structlog.contextvars.merge_contextvars,\n                    structlog.processors.add_log_level,\n                    structlog.processors.StackInfoRenderer(),\n                    structlog.dev.set_exc_info,\n                    structlog.processors.TimeStamper(fmt=\"ISO\"),\n                    structlog.dev.ConsoleRenderer(colors=True)\n                ],\n                wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),\n                logger_factory=structlog.PrintLoggerFactory(),\n                cache_logger_on_first_use=True\n            )\n            \n            return structlog.get_logger(\"decision_logger\")\n            \n        except Exception as e:\n            base_logger.error(f\"Failed to configure structured logger: {e}\")\n            # Fallback to basic logger\n            return base_logger\n    \n    def _initialize_default_alert_rules(self):\n        \"\"\"Initialize default alerting rules\"\"\"\n        \n        self.alert_rules = [\n            {\n                \"rule_id\": \"critical_errors\",\n                \"condition\": lambda entry: entry.level == DecisionLogLevel.CRITICAL,\n                \"severity\": AlertSeverity.CRITICAL,\n                \"message\": \"Critical decision system error detected\",\n                \"cooldown_minutes\": 5\n            },\n            {\n                \"rule_id\": \"validation_failures\",\n                \"condition\": lambda entry: (\n                    entry.category == DecisionLogCategory.VALIDATION_PROCESS and \n                    entry.level == DecisionLogLevel.ERROR\n                ),\n                \"severity\": AlertSeverity.HIGH,\n                \"message\": \"Decision validation failure detected\",\n                \"cooldown_minutes\": 10\n            },\n            {\n                \"rule_id\": \"ai_brain_issues\",\n                \"condition\": lambda entry: (\n                    entry.category == DecisionLogCategory.AI_BRAIN_INTEGRATION and\n                    entry.level in [DecisionLogLevel.ERROR, DecisionLogLevel.CRITICAL]\n                ),\n                \"severity\": AlertSeverity.HIGH,\n                \"message\": \"AI Brain integration issue detected\",\n                \"cooldown_minutes\": 15\n            },\n            {\n                \"rule_id\": \"low_confidence_pattern\",\n                \"condition\": lambda entry: (\n                    entry.confidence is not None and\n                    entry.confidence < 0.5 and\n                    entry.category == DecisionLogCategory.CONFIDENCE_ANALYSIS\n                ),\n                \"severity\": AlertSeverity.MEDIUM,\n                \"message\": \"Pattern of low confidence decisions detected\",\n                \"cooldown_minutes\": 30\n            }\n        ]\n    \n    async def log_decision_event(\n        self,\n        decision_id: str,\n        level: DecisionLogLevel,\n        category: DecisionLogCategory,\n        message: str,\n        structured_data: Optional[Dict[str, Any]] = None,\n        symbol: Optional[str] = None,\n        action: Optional[str] = None,\n        confidence: Optional[float] = None,\n        execution_time_ms: Optional[float] = None,\n        correlation_id: Optional[str] = None,\n        error_details: Optional[Dict[str, Any]] = None\n    ) -> DecisionLogEntry:\n        \"\"\"\n        Log a decision event with full structured data\n        \n        Args:\n            decision_id: Unique decision identifier\n            level: Log level (TRACE, DEBUG, INFO, WARN, ERROR, CRITICAL)\n            category: Log category for classification\n            message: Human-readable log message\n            structured_data: Additional structured data\n            symbol: Trading symbol if applicable\n            action: Decision action if applicable\n            confidence: Decision confidence if applicable\n            execution_time_ms: Execution time if applicable\n            correlation_id: Correlation ID for tracking related events\n            error_details: Error details if applicable\n            \n        Returns:\n            The created log entry\n        \"\"\"\n        \n        try:\n            # Create log entry\n            log_entry = DecisionLogEntry(\n                log_id=str(uuid.uuid4()),\n                decision_id=decision_id,\n                timestamp=datetime.now(),\n                level=level,\n                category=category,\n                message=message,\n                structured_data=structured_data or {},\n                symbol=symbol,\n                action=action,\n                confidence=confidence,\n                execution_time_ms=execution_time_ms,\n                correlation_id=correlation_id,\n                error_details=error_details\n            )\n            \n            # Store in memory\n            self.recent_logs.append(log_entry)\n            self.decision_logs[decision_id].append(log_entry)\n            \n            # Update metrics\n            self._update_logging_metrics(log_entry)\n            \n            # Log to structured logger\n            await self._write_structured_log(log_entry)\n            \n            # Check alert rules\n            await self._check_alert_rules(log_entry)\n            \n            # Cache for quick access\n            await cache.set(f\"log:{log_entry.log_id}\", asdict(log_entry), ttl=3600)\n            \n            # Pattern recognition\n            self._analyze_log_patterns(log_entry)\n            \n            return log_entry\n            \n        except Exception as e:\n            base_logger.error(f\"Failed to log decision event: {e}\")\n            raise\n    \n    async def log_validation_step(\n        self,\n        decision_id: str,\n        step_name: str,\n        step_result: Dict[str, Any],\n        execution_time_ms: float,\n        correlation_id: Optional[str] = None\n    ):\n        \"\"\"Log a validation step with detailed results\"\"\"\n        \n        level = DecisionLogLevel.DEBUG if step_result.get(\"success\", True) else DecisionLogLevel.WARN\n        \n        await self.log_decision_event(\n            decision_id=decision_id,\n            level=level,\n            category=DecisionLogCategory.VALIDATION_PROCESS,\n            message=f\"Validation step '{step_name}' {'completed' if step_result.get('success', True) else 'failed'}\",\n            structured_data={\n                \"step_name\": step_name,\n                \"step_result\": step_result,\n                \"validation_context\": \"systematic_validation\"\n            },\n            execution_time_ms=execution_time_ms,\n            correlation_id=correlation_id\n        )\n    \n    async def log_ai_brain_interaction(\n        self,\n        decision_id: str,\n        interaction_type: str,\n        ai_brain_data: Dict[str, Any],\n        success: bool,\n        execution_time_ms: float\n    ):\n        \"\"\"Log AI Brain system interaction\"\"\"\n        \n        level = DecisionLogLevel.INFO if success else DecisionLogLevel.ERROR\n        \n        await self.log_decision_event(\n            decision_id=decision_id,\n            level=level,\n            category=DecisionLogCategory.AI_BRAIN_INTEGRATION,\n            message=f\"AI Brain {interaction_type} {'successful' if success else 'failed'}\",\n            structured_data={\n                \"interaction_type\": interaction_type,\n                \"ai_brain_data\": ai_brain_data,\n                \"integration_success\": success,\n                \"ai_brain_available\": True\n            },\n            execution_time_ms=execution_time_ms\n        )\n    \n    async def log_confidence_analysis(\n        self,\n        decision_id: str,\n        confidence_data: Dict[str, Any],\n        correlation_analysis: Dict[str, Any]\n    ):\n        \"\"\"Log confidence analysis results\"\"\"\n        \n        base_confidence = confidence_data.get(\"base_confidence\", 0.5)\n        adjusted_confidence = confidence_data.get(\"adjusted_confidence\", 0.5)\n        \n        level = DecisionLogLevel.INFO\n        if adjusted_confidence < 0.5:\n            level = DecisionLogLevel.WARN\n        elif adjusted_confidence < 0.3:\n            level = DecisionLogLevel.ERROR\n        \n        await self.log_decision_event(\n            decision_id=decision_id,\n            level=level,\n            category=DecisionLogCategory.CONFIDENCE_ANALYSIS,\n            message=f\"Confidence analysis: {base_confidence:.3f} -> {adjusted_confidence:.3f}\",\n            structured_data={\n                \"confidence_data\": confidence_data,\n                \"correlation_analysis\": correlation_analysis,\n                \"confidence_improvement\": adjusted_confidence - base_confidence,\n                \"analysis_quality\": \"high\" if len(correlation_analysis) > 3 else \"medium\"\n            },\n            confidence=adjusted_confidence\n        )\n    \n    async def log_execution_event(\n        self,\n        decision_id: str,\n        execution_data: Dict[str, Any],\n        success: bool,\n        execution_time_ms: float\n    ):\n        \"\"\"Log trade execution event\"\"\"\n        \n        level = DecisionLogLevel.INFO if success else DecisionLogLevel.ERROR\n        \n        await self.log_decision_event(\n            decision_id=decision_id,\n            level=level,\n            category=DecisionLogCategory.EXECUTION_TRACKING,\n            message=f\"Trade execution {'successful' if success else 'failed'}\",\n            structured_data={\n                \"execution_data\": execution_data,\n                \"execution_success\": success,\n                \"slippage\": execution_data.get(\"slippage\", 0.0),\n                \"fill_quality\": execution_data.get(\"fill_quality\", \"unknown\")\n            },\n            symbol=execution_data.get(\"symbol\"),\n            action=execution_data.get(\"action\"),\n            execution_time_ms=execution_time_ms,\n            error_details=execution_data.get(\"error_details\") if not success else None\n        )\n    \n    async def log_performance_correlation(\n        self,\n        decision_id: str,\n        performance_data: Dict[str, Any],\n        correlation_metrics: Dict[str, float]\n    ):\n        \"\"\"Log performance correlation analysis\"\"\"\n        \n        correlation_quality = correlation_metrics.get(\"overall_correlation\", 0.5)\n        level = DecisionLogLevel.INFO\n        \n        if correlation_quality < 0.3:\n            level = DecisionLogLevel.WARN\n        elif correlation_quality > 0.8:\n            level = DecisionLogLevel.INFO  # Good correlation\n        \n        await self.log_decision_event(\n            decision_id=decision_id,\n            level=level,\n            category=DecisionLogCategory.PERFORMANCE_CORRELATION,\n            message=f\"Performance correlation analysis: {correlation_quality:.3f}\",\n            structured_data={\n                \"performance_data\": performance_data,\n                \"correlation_metrics\": correlation_metrics,\n                \"correlation_quality\": correlation_quality,\n                \"analysis_completeness\": len(performance_data) / 10  # Expect ~10 metrics\n            }\n        )\n    \n    async def log_error_with_analysis(\n        self,\n        decision_id: str,\n        error: Exception,\n        error_context: Dict[str, Any],\n        stack_trace: Optional[str] = None\n    ):\n        \"\"\"Log error with comprehensive analysis\"\"\"\n        \n        error_type = type(error).__name__\n        error_message = str(error)\n        \n        await self.log_decision_event(\n            decision_id=decision_id,\n            level=DecisionLogLevel.ERROR,\n            category=DecisionLogCategory.ERROR_ANALYSIS,\n            message=f\"Decision error: {error_type} - {error_message}\",\n            structured_data={\n                \"error_type\": error_type,\n                \"error_message\": error_message,\n                \"error_context\": error_context,\n                \"error_severity\": self._classify_error_severity(error),\n                \"recovery_suggestions\": self._generate_error_recovery_suggestions(error, error_context)\n            },\n            error_details={\n                \"error_type\": error_type,\n                \"error_message\": error_message,\n                \"context\": error_context\n            },\n            stack_trace=stack_trace\n        )\n    \n    async def log_audit_event(\n        self,\n        decision_id: str,\n        audit_data: Dict[str, Any],\n        compliance_check: bool = True\n    ):\n        \"\"\"Log audit event for compliance tracking\"\"\"\n        \n        await self.log_decision_event(\n            decision_id=decision_id,\n            level=DecisionLogLevel.INFO,\n            category=DecisionLogCategory.AUDIT_COMPLIANCE,\n            message=f\"Audit event: {audit_data.get('event_type', 'unknown')}\",\n            structured_data={\n                \"audit_data\": audit_data,\n                \"compliance_check\": compliance_check,\n                \"audit_timestamp\": datetime.now().isoformat(),\n                \"regulatory_requirements\": audit_data.get(\"regulatory_requirements\", []),\n                \"audit_trail_complete\": self._verify_audit_trail_completeness(decision_id)\n            }\n        )\n    \n    async def _write_structured_log(self, log_entry: DecisionLogEntry):\n        \"\"\"Write log entry to structured logger\"\"\"\n        \n        try:\n            # Prepare log data for structured logger\n            log_data = {\n                \"decision_id\": log_entry.decision_id,\n                \"log_id\": log_entry.log_id,\n                \"category\": log_entry.category.value,\n                \"structured_data\": log_entry.structured_data,\n                \"symbol\": log_entry.symbol,\n                \"action\": log_entry.action,\n                \"confidence\": log_entry.confidence,\n                \"execution_time_ms\": log_entry.execution_time_ms,\n                \"correlation_id\": log_entry.correlation_id\n            }\n            \n            # Add error details if present\n            if log_entry.error_details:\n                log_data[\"error_details\"] = log_entry.error_details\n            \n            # Log based on level\n            if log_entry.level == DecisionLogLevel.TRACE:\n                self.structured_logger.debug(log_entry.message, **log_data)\n            elif log_entry.level == DecisionLogLevel.DEBUG:\n                self.structured_logger.debug(log_entry.message, **log_data)\n            elif log_entry.level == DecisionLogLevel.INFO:\n                self.structured_logger.info(log_entry.message, **log_data)\n            elif log_entry.level == DecisionLogLevel.WARN:\n                self.structured_logger.warning(log_entry.message, **log_data)\n            elif log_entry.level == DecisionLogLevel.ERROR:\n                self.structured_logger.error(log_entry.message, **log_data)\n            elif log_entry.level == DecisionLogLevel.CRITICAL:\n                self.structured_logger.critical(log_entry.message, **log_data)\n            \n        except Exception as e:\n            base_logger.error(f\"Failed to write structured log: {e}\")\n    \n    def _update_logging_metrics(self, log_entry: DecisionLogEntry):\n        \"\"\"Update logging metrics\"\"\"\n        \n        try:\n            # Update volume metrics\n            self.logging_metrics.total_logs += 1\n            self.logging_metrics.logs_by_level[log_entry.level.value] += 1\n            self.logging_metrics.logs_by_category[log_entry.category.value] += 1\n            \n            # Update error metrics\n            if log_entry.level == DecisionLogLevel.ERROR:\n                self.logging_metrics.error_count += 1\n            elif log_entry.level == DecisionLogLevel.CRITICAL:\n                self.logging_metrics.critical_count += 1\n            \n            # Update performance metrics\n            if log_entry.execution_time_ms:\n                current_avg = self.logging_metrics.average_log_processing_ms\n                total_logs = self.logging_metrics.total_logs\n                \n                # Calculate new average\n                self.logging_metrics.average_log_processing_ms = (\n                    (current_avg * (total_logs - 1)) + log_entry.execution_time_ms\n                ) / total_logs\n            \n        except Exception as e:\n            base_logger.error(f\"Failed to update logging metrics: {e}\")\n    \n    async def _check_alert_rules(self, log_entry: DecisionLogEntry):\n        \"\"\"Check alert rules and generate alerts if needed\"\"\"\n        \n        try:\n            for rule in self.alert_rules:\n                if rule[\"condition\"](log_entry):\n                    # Check cooldown\n                    rule_id = rule[\"rule_id\"]\n                    cooldown_minutes = rule.get(\"cooldown_minutes\", 10)\n                    \n                    # Check if alert was recently generated for this rule\n                    recent_alerts = [\n                        alert for alert in self.active_alerts\n                        if (\n                            alert[\"rule_id\"] == rule_id and\n                            datetime.now() - datetime.fromisoformat(alert[\"timestamp\"]) < timedelta(minutes=cooldown_minutes)\n                        )\n                    ]\n                    \n                    if not recent_alerts:\n                        await self._generate_alert(log_entry, rule)\n            \n        except Exception as e:\n            base_logger.error(f\"Failed to check alert rules: {e}\")\n    \n    async def _generate_alert(\n        self,\n        log_entry: DecisionLogEntry,\n        rule: Dict[str, Any]\n    ):\n        \"\"\"Generate alert for log entry\"\"\"\n        \n        try:\n            alert = {\n                \"alert_id\": str(uuid.uuid4()),\n                \"rule_id\": rule[\"rule_id\"],\n                \"decision_id\": log_entry.decision_id,\n                \"severity\": rule[\"severity\"].value,\n                \"message\": rule[\"message\"],\n                \"log_entry_id\": log_entry.log_id,\n                \"timestamp\": datetime.now().isoformat(),\n                \"details\": {\n                    \"log_level\": log_entry.level.value,\n                    \"log_category\": log_entry.category.value,\n                    \"log_message\": log_entry.message,\n                    \"structured_data\": log_entry.structured_data\n                },\n                \"acknowledged\": False,\n                \"resolved\": False\n            }\n            \n            # Store alert\n            self.active_alerts.append(alert)\n            \n            # Update metrics\n            self.logging_metrics.alerts_generated += 1\n            self.logging_metrics.alerts_by_severity[rule[\"severity\"].value] += 1\n            \n            # Cache alert\n            await cache.set(f\"alert:{alert['alert_id']}\", alert, ttl=86400)\n            \n            # Log alert generation\n            base_logger.warning(f\"Alert generated: {alert['alert_id']} - {rule['message']}\")\n            \n            # Mark log entry as requiring alert\n            log_entry.alert_required = True\n            log_entry.alert_severity = rule[\"severity\"]\n            \n        except Exception as e:\n            base_logger.error(f\"Failed to generate alert: {e}\")\n    \n    def _analyze_log_patterns(self, log_entry: DecisionLogEntry):\n        \"\"\"Analyze log patterns for insights\"\"\"\n        \n        try:\n            # Pattern key creation\n            pattern_key = f\"{log_entry.category.value}_{log_entry.level.value}\"\n            self.log_patterns[pattern_key] += 1\n            \n            # Error pattern analysis\n            if log_entry.level in [DecisionLogLevel.ERROR, DecisionLogLevel.CRITICAL]:\n                error_pattern = f\"{log_entry.category.value}_error\"\n                self.error_patterns[error_pattern] += 1\n            \n            # Symbol-specific patterns\n            if log_entry.symbol:\n                symbol_pattern = f\"{log_entry.symbol}_{log_entry.category.value}\"\n                self.log_patterns[symbol_pattern] += 1\n            \n        except Exception as e:\n            base_logger.error(f\"Failed to analyze log patterns: {e}\")\n    \n    def _classify_error_severity(self, error: Exception) -> str:\n        \"\"\"Classify error severity for analysis\"\"\"\n        \n        error_type = type(error).__name__\n        \n        # Critical errors\n        if error_type in [\"SystemExit\", \"MemoryError\", \"KeyboardInterrupt\"]:\n            return \"critical\"\n        \n        # High severity errors\n        elif error_type in [\"ConnectionError\", \"TimeoutError\", \"ValidationError\"]:\n            return \"high\"\n        \n        # Medium severity errors\n        elif error_type in [\"ValueError\", \"TypeError\", \"KeyError\"]:\n            return \"medium\"\n        \n        # Low severity errors\n        else:\n            return \"low\"\n    \n    def _generate_error_recovery_suggestions(self, error: Exception, context: Dict[str, Any]) -> List[str]:\n        \"\"\"Generate error recovery suggestions\"\"\"\n        \n        suggestions = []\n        error_type = type(error).__name__\n        \n        if error_type == \"ConnectionError\":\n            suggestions.extend([\n                \"Check network connectivity\",\n                \"Verify service endpoints are accessible\",\n                \"Review connection timeout settings\",\n                \"Consider implementing connection retry logic\"\n            ])\n        \n        elif error_type == \"ValidationError\":\n            suggestions.extend([\n                \"Review input data quality and format\",\n                \"Check validation rules for accuracy\",\n                \"Implement input sanitization\",\n                \"Add pre-validation checks\"\n            ])\n        \n        elif error_type == \"TimeoutError\":\n            suggestions.extend([\n                \"Increase timeout values\",\n                \"Optimize processing performance\",\n                \"Implement asynchronous processing\",\n                \"Add progress monitoring\"\n            ])\n        \n        else:\n            suggestions.extend([\n                \"Review error context and logs\",\n                \"Check system resources and performance\",\n                \"Verify input parameters and data quality\",\n                \"Consider implementing error handling\"\n            ])\n        \n        return suggestions\n    \n    def _verify_audit_trail_completeness(self, decision_id: str) -> bool:\n        \"\"\"Verify audit trail completeness for a decision\"\"\"\n        \n        try:\n            decision_logs = self.decision_logs.get(decision_id, [])\n            \n            if not decision_logs:\n                return False\n            \n            # Check for required audit events\n            required_categories = [\n                DecisionLogCategory.DECISION_CONTEXT,\n                DecisionLogCategory.VALIDATION_PROCESS,\n                DecisionLogCategory.EXECUTION_TRACKING\n            ]\n            \n            present_categories = set(log.category for log in decision_logs)\n            \n            return all(cat in present_categories for cat in required_categories)\n            \n        except Exception as e:\n            base_logger.error(f\"Failed to verify audit trail completeness: {e}\")\n            return False\n    \n    async def get_decision_logs(\n        self,\n        decision_id: str,\n        level_filter: Optional[DecisionLogLevel] = None,\n        category_filter: Optional[DecisionLogCategory] = None,\n        limit: int = 100\n    ) -> List[DecisionLogEntry]:\n        \"\"\"Get logs for a specific decision with optional filtering\"\"\"\n        \n        try:\n            decision_logs = self.decision_logs.get(decision_id, [])\n            \n            # Apply filters\n            filtered_logs = decision_logs\n            \n            if level_filter:\n                filtered_logs = [log for log in filtered_logs if log.level == level_filter]\n            \n            if category_filter:\n                filtered_logs = [log for log in filtered_logs if log.category == category_filter]\n            \n            # Sort by timestamp (newest first) and limit\n            filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)\n            \n            return filtered_logs[:limit]\n            \n        except Exception as e:\n            base_logger.error(f\"Failed to get decision logs: {e}\")\n            return []\n    \n    async def export_logs(\n        self,\n        start_date: datetime,\n        end_date: datetime,\n        export_format: str = \"json\",\n        include_structured_data: bool = True\n    ) -> str:\n        \"\"\"Export logs for specified date range\"\"\"\n        \n        try:\n            # Filter logs by date range\n            export_logs = [\n                log for log in self.recent_logs\n                if start_date <= log.timestamp <= end_date\n            ]\n            \n            # Prepare export data\n            export_data = {\n                \"export_info\": {\n                    \"start_date\": start_date.isoformat(),\n                    \"end_date\": end_date.isoformat(),\n                    \"total_logs\": len(export_logs),\n                    \"export_timestamp\": datetime.now().isoformat()\n                },\n                \"logs\": []\n            }\n            \n            for log in export_logs:\n                log_data = {\n                    \"log_id\": log.log_id,\n                    \"decision_id\": log.decision_id,\n                    \"timestamp\": log.timestamp.isoformat(),\n                    \"level\": log.level.value,\n                    \"category\": log.category.value,\n                    \"message\": log.message,\n                    \"symbol\": log.symbol,\n                    \"action\": log.action,\n                    \"confidence\": log.confidence,\n                    \"execution_time_ms\": log.execution_time_ms,\n                    \"correlation_id\": log.correlation_id\n                }\n                \n                if include_structured_data:\n                    log_data[\"structured_data\"] = log.structured_data\n                    log_data[\"error_details\"] = log.error_details\n                \n                export_data[\"logs\"].append(log_data)\n            \n            # Generate export file\n            filename = f\"decision_logs_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.{export_format}\"\n            filepath = os.path.join(self.log_directory, \"exports\", filename)\n            \n            if export_format == \"json\":\n                with open(filepath, 'w') as f:\n                    json.dump(export_data, f, indent=2, default=str)\n            elif export_format == \"json.gz\":\n                with gzip.open(filepath, 'wt') as f:\n                    json.dump(export_data, f, indent=2, default=str)\n            \n            base_logger.info(f\"Logs exported to: {filepath}\")\n            \n            return filepath\n            \n        except Exception as e:\n            base_logger.error(f\"Failed to export logs: {e}\")\n            raise\n    \n    def get_logging_statistics(self) -> Dict[str, Any]:\n        \"\"\"Get comprehensive logging statistics\"\"\"\n        \n        return {\n            \"logging_metrics\": asdict(self.logging_metrics),\n            \"pattern_analysis\": {\n                \"log_patterns\": dict(self.log_patterns),\n                \"error_patterns\": dict(self.error_patterns),\n                \"top_log_patterns\": sorted(self.log_patterns.items(), key=lambda x: x[1], reverse=True)[:10],\n                \"top_error_patterns\": sorted(self.error_patterns.items(), key=lambda x: x[1], reverse=True)[:5]\n            },\n            \"alert_summary\": {\n                \"active_alerts\": len(self.active_alerts),\n                \"total_alerts_generated\": self.logging_metrics.alerts_generated,\n                \"alerts_by_severity\": self.logging_metrics.alerts_by_severity,\n                \"recent_alerts\": self.active_alerts[-5:] if self.active_alerts else []\n            },\n            \"system_health\": {\n                \"logging_system_healthy\": self.logging_metrics.logging_system_healthy,\n                \"recent_logs_count\": len(self.recent_logs),\n                \"tracked_decisions\": len(self.decision_logs),\n                \"last_export_time\": self.last_export_time.isoformat()\n            },\n            \"timestamp\": datetime.now().isoformat()\n        }\n\n\n# Global instance\ndecision_logger = DecisionLogger()