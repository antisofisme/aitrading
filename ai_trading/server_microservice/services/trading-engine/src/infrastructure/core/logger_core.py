"""
AI Brain Enhanced Core Logger Implementation - Production-ready logging with AI Brain integration
Enhanced with confidence tracking, error pattern recognition, and systematic validation
"""
import logging
import json
import sys
import threading
from datetime import datetime
from typing import Dict, Any, Optional
from ..base.base_logger import BaseLogger, LogLevel

# AI Brain Integration
try:
    import sys
    import os
    sys.path.append('/mnt/f/WINDSURF/concept_ai/projects/ai_trading/server_microservice/services')
    from shared.ai_brain_trading_error_dna import AiBrainTradingErrorDNA
    from shared.ai_brain_confidence_framework import AiBrainConfidenceFramework
    AI_BRAIN_AVAILABLE = True
except ImportError:
    AI_BRAIN_AVAILABLE = False

class CoreLogger(BaseLogger):
    """AI Brain Enhanced Core logger implementation with systematic validation and confidence tracking"""
    
    def __init__(self, 
                 service_name: str, 
                 service_id: str = None,
                 log_level: LogLevel = LogLevel.INFO,
                 output_format: str = "json"):
        """
        Initialize AI Brain Enhanced CoreLogger with systematic validation capabilities.
        
        Args:
            service_name: Name of the service using this logger
            service_id: Unique identifier for this service instance (optional)
            log_level: Minimum log level to capture (default: INFO)
            output_format: Log output format - 'json' or 'text' (default: 'json')
        """
        super().__init__(service_name, service_id)
        self.log_level = log_level
        self.output_format = output_format
        
        # AI Brain Integration
        self.ai_brain_error_dna = None
        self.confidence_tracking = {}
        self.error_patterns_logged = []
        
        if AI_BRAIN_AVAILABLE:
            try:
                self.ai_brain_error_dna = AiBrainTradingErrorDNA(f"logger-{service_name}")
                print(f"✅ AI Brain Error DNA initialized for logger: {service_name}")
            except Exception as e:
                print(f"⚠️ AI Brain Error DNA initialization failed: {e}")
        
        self._setup_logger()
        self.setup_service_specific_formatting()
    
    def _setup_logger(self):
        """Setup Python logger with structured formatting"""
        self.logger = logging.getLogger(f"{self.service_name}-{self.service_id}")
        self.logger.setLevel(getattr(logging, self.log_level.value))
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, self.log_level.value))
        
        # Set formatter based on output format
        if self.output_format == "json":
            formatter = self._get_json_formatter()
        else:
            formatter = self._get_text_formatter()
        
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def _get_json_formatter(self):
        """Get JSON formatter for structured logging"""
        class JSONFormatter(logging.Formatter):
            def format(self, record) -> str:
                log_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": record.levelname,
                    "service": record.name.split('-')[0],
                    "service_id": record.name.split('-')[1] if '-' in record.name else "unknown",
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno
                }
                
                # Add exception info if present
                if record.exc_info:
                    log_data["exception"] = self.formatException(record.exc_info)
                
                # Add extra context
                if hasattr(record, 'context'):
                    log_data["context"] = record.context
                
                return json.dumps(log_data, default=str)
        
        return JSONFormatter()
    
    def _get_text_formatter(self):
        """Get text formatter for human-readable logging"""
        return logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def log(self, level: LogLevel, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log message with specified level and optional context.
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: The message to log
            context: Optional dictionary of contextual information to include
        """
        full_context = {**self.context}
        if context:
            full_context.update(context)
        
        # Create log record with context
        log_method = getattr(self.logger, level.value.lower())
        
        # Add context to the record
        extra = {'context': full_context} if full_context else {}
        log_method(message, extra=extra)
    
    def info(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log info message"""
        self.log(LogLevel.INFO, message, context)
    
    def error(self, message: str, error: Exception = None, context: Optional[Dict[str, Any]] = None):
        """AI Brain Enhanced error logging with surgical precision error analysis"""
        full_context = {**self.context}
        if context:
            full_context.update(context)
        
        if error:
            full_context["error_type"] = type(error).__name__
            full_context["error_details"] = str(error)
            
            # AI Brain Error DNA Analysis
            if self.ai_brain_error_dna and AI_BRAIN_AVAILABLE:
                try:
                    ai_brain_analysis = self.ai_brain_error_dna.analyze_error(error, full_context)
                    
                    # Enhance context with AI Brain analysis
                    full_context.update({
                        "ai_brain_pattern": ai_brain_analysis.get("matched_pattern"),
                        "ai_brain_solution_confidence": ai_brain_analysis.get("solution_confidence", 0),
                        "ai_brain_trading_impact": ai_brain_analysis.get("trading_impact"),
                        "ai_brain_urgency": ai_brain_analysis.get("urgency_level"),
                        "ai_brain_recommended_actions": ai_brain_analysis.get("recommended_actions", [])
                    })
                    
                    # Track error pattern
                    self.error_patterns_logged.append({
                        "timestamp": datetime.now().isoformat(),
                        "pattern": ai_brain_analysis.get("matched_pattern"),
                        "confidence": ai_brain_analysis.get("solution_confidence", 0)
                    })
                    
                    # Enhanced error message with AI Brain insights
                    enhanced_message = f"{message} | AI Brain Analysis: Pattern={ai_brain_analysis.get('matched_pattern', 'Unknown')}, Confidence={ai_brain_analysis.get('solution_confidence', 0):.2f}, Impact={ai_brain_analysis.get('trading_impact', 'Unknown')}"
                    
                    # Log AI Brain recommendations if available
                    if ai_brain_analysis.get("recommended_actions"):
                        self.info(f"🧠 AI Brain Recommendations: {ai_brain_analysis['recommended_actions']}")
                        
                except Exception as analysis_error:
                    full_context["ai_brain_analysis_error"] = str(analysis_error)
                    enhanced_message = message
            else:
                enhanced_message = message
        else:
            enhanced_message = message
        
        extra = {'context': full_context} if full_context else {}
        
        if error:
            self.logger.error(enhanced_message, exc_info=error, extra=extra)
        else:
            self.logger.error(enhanced_message, extra=extra)
    
    def warning(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log warning message"""
        self.log(LogLevel.WARNING, message, context)
    
    def debug(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log debug message"""
        self.log(LogLevel.DEBUG, message, context)
    
    def critical(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log critical message"""
        self.log(LogLevel.CRITICAL, message, context)
    
    def setup_service_specific_formatting(self) -> None:
        """Setup service-specific log formatting"""
        # Add service-specific context
        self.add_context("deployment_env", "microservices")
        self.add_context("log_format", self.output_format)
    
    def log_request(self, 
                   method: str, 
                   path: str, 
                   status_code: int,
                   duration_ms: float,
                   user_id: str = None,
                   request_id: str = None):
        """
        Log HTTP request details with performance metrics.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            path: Request path/endpoint
            status_code: HTTP response status code
            duration_ms: Request processing duration in milliseconds
            user_id: Optional user identifier for the request
            request_id: Optional unique request identifier for tracing
        """
        context = {
            "request_method": method,
            "request_path": path,
            "response_status": status_code,
            "duration_ms": duration_ms,
            "request_type": "http"
        }
        
        if user_id:
            context["user_id"] = user_id
        if request_id:
            context["request_id"] = request_id
        
        self.info(f"{method} {path} - {status_code} ({duration_ms}ms)", context)
    
    def log_database_query(self, 
                          query_type: str,
                          table: str,
                          duration_ms: float,
                          rows_affected: int = None):
        """Log database query details"""
        context = {
            "query_type": query_type,
            "table": table,
            "duration_ms": duration_ms,
            "operation_type": "database"
        }
        
        if rows_affected is not None:
            context["rows_affected"] = rows_affected
        
        self.info(f"DB {query_type} on {table} ({duration_ms}ms)", context)
    
    def log_external_service_call(self,
                                 service_name: str,
                                 endpoint: str,
                                 method: str,
                                 status_code: int,
                                 duration_ms: float):
        """Log external service call details"""
        context = {
            "external_service": service_name,
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "operation_type": "external_service"
        }
        
        self.info(f"External call to {service_name} {method} {endpoint} - {status_code} ({duration_ms}ms)", context)
    
    def log_business_event(self,
                          event_name: str,
                          event_data: Dict[str, Any],
                          user_id: str = None):
        """Log business-specific events"""
        context = {
            "event_name": event_name,
            "event_data": event_data,
            "operation_type": "business_event"
        }
        
        if user_id:
            context["user_id"] = user_id
        
        self.info(f"Business event: {event_name}", context)
    
    def set_log_level(self, level: LogLevel) -> None:
        """Change log level dynamically"""
        self.log_level = level
        self.logger.setLevel(getattr(logging, level.value))
        for handler in self.logger.handlers:
            handler.setLevel(getattr(logging, level.value))
    
    # AI Brain Enhanced Logging Methods
    
    def log_confidence_score(self, operation: str, confidence_score: float, context: Optional[Dict[str, Any]] = None):
        """Log confidence score for AI Brain tracking"""
        confidence_context = {
            "operation": operation,
            "confidence_score": confidence_score,
            "confidence_level": "high" if confidence_score >= 0.85 else "medium" if confidence_score >= 0.70 else "low",
            "operation_type": "confidence_tracking"
        }
        
        if context:
            confidence_context.update(context)
        
        # Track confidence for analysis
        if operation not in self.confidence_tracking:
            self.confidence_tracking[operation] = []
        self.confidence_tracking[operation].append({
            "timestamp": datetime.now().isoformat(),
            "confidence": confidence_score
        })
        
        self.info(f"🧠 AI Brain Confidence: {operation} = {confidence_score:.3f}", confidence_context)
    
    def log_trading_decision(self, symbol: str, action: str, confidence: float, reasoning: str, ai_brain_approved: bool = True):
        """Log trading decision with AI Brain validation status"""
        decision_context = {
            "symbol": symbol,
            "action": action,
            "confidence": confidence,
            "ai_brain_approved": ai_brain_approved,
            "operation_type": "trading_decision"
        }
        
        approval_status = "APPROVED" if ai_brain_approved else "BLOCKED"
        confidence_indicator = "🟢" if confidence >= 0.85 else "🟡" if confidence >= 0.70 else "🔴"
        
        message = f"⚡ Trading Decision {approval_status}: {symbol} {action.upper()} {confidence_indicator} ({confidence:.3f}) - {reasoning}"
        
        if ai_brain_approved:
            self.info(message, decision_context)
        else:
            self.warning(message, decision_context)
    
    def log_ai_brain_analysis(self, analysis_type: str, results: Dict[str, Any]):
        """Log AI Brain analysis results"""
        analysis_context = {
            "analysis_type": analysis_type,
            "analysis_results": results,
            "operation_type": "ai_brain_analysis"
        }
        
        pattern = results.get("matched_pattern", "Unknown")
        confidence = results.get("solution_confidence", 0)
        impact = results.get("trading_impact", "Unknown")
        
        self.info(f"🔍 AI Brain {analysis_type}: Pattern={pattern}, Confidence={confidence:.2f}, Impact={impact}", analysis_context)
    
    def log_performance_metric(self, metric_name: str, value: float, target: Optional[float] = None):
        """Log performance metric with AI Brain context"""
        performance_context = {
            "metric_name": metric_name,
            "metric_value": value,
            "target_value": target,
            "performance_status": "above_target" if target and value >= target else "below_target" if target else "measured",
            "operation_type": "performance_metric"
        }
        
        status_indicator = "📈" if not target or value >= target else "📉"
        target_text = f" (target: {target})" if target else ""
        
        self.info(f"{status_indicator} Performance: {metric_name} = {value}{target_text}", performance_context)
    
    def get_ai_brain_statistics(self) -> Dict[str, Any]:
        """Get AI Brain enhanced logging statistics"""
        stats = {
            "error_patterns_count": len(self.error_patterns_logged),
            "confidence_operations": len(self.confidence_tracking),
            "ai_brain_enabled": AI_BRAIN_AVAILABLE and self.ai_brain_error_dna is not None
        }
        
        # Recent confidence trends
        if self.confidence_tracking:
            recent_confidences = []
            for operation, scores in self.confidence_tracking.items():
                recent_scores = [s["confidence"] for s in scores[-10:]]  # Last 10 scores
                if recent_scores:
                    recent_confidences.extend(recent_scores)
            
            if recent_confidences:
                stats["average_confidence"] = sum(recent_confidences) / len(recent_confidences)
                stats["confidence_trend"] = "improving" if len(recent_confidences) > 1 and recent_confidences[-1] > recent_confidences[0] else "stable"
        
        # Error pattern analysis
        if self.error_patterns_logged:
            recent_errors = [e for e in self.error_patterns_logged[-20:]]  # Last 20 errors
            pattern_counts = {}
            for error in recent_errors:
                pattern = error.get("pattern", "Unknown")
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
            
            stats["common_error_patterns"] = pattern_counts
            stats["average_solution_confidence"] = sum([e.get("confidence", 0) for e in recent_errors]) / len(recent_errors) if recent_errors else 0
        
        return stats


# CENTRALIZED LOGGER MANAGER - Simple singleton for all microservices
class SharedInfraLoggerManager:
    """Simple centralized logger management for microservices"""
    
    _loggers = {}
    _lock = threading.RLock()
    
    @classmethod
    def get_logger(cls, service_name: str, service_id: str = None) -> CoreLogger:
        """Get or create logger for service"""
        with cls._lock:
            key = f"{service_name}-{service_id or '001'}"
            if key not in cls._loggers:
                cls._loggers[key] = CoreLogger(service_name, service_id)
            return cls._loggers[key]
    
    @classmethod
    def get_all_loggers(cls):
        """Get all managed loggers"""
        return cls._loggers.copy()


# Simple convenience functions
def get_logger(service_name: str, service_id: str = None) -> CoreLogger:
    """Get logger for service"""
    return SharedInfraLoggerManager.get_logger(service_name, service_id)