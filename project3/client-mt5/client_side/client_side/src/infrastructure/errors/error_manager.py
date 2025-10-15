"""
error_manager.py - Centralized Error Management

🎯 PURPOSE:
Business: Comprehensive error handling and recovery for trading operations
Technical: Advanced error management with context, recovery strategies, and alerting
Domain: Error Handling/Exception Management/System Recovery

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:27.809Z
Session: client-side-ai-brain-full-compliance
Confidence: 91%
Complexity: high

🧩 PATTERNS USED:
- AI_BRAIN_ERROR_MANAGEMENT: Centralized error handling with recovery strategies
- ERROR_CONTEXT_TRACKING: Rich error context for debugging and analysis

📦 DEPENDENCIES:
Internal: logger_manager, config_manager
External: traceback, sys, typing, enum, dataclasses

💡 AI DECISION REASONING:
Trading systems require robust error handling with detailed context for quick resolution. Centralized approach ensures consistent error management across all components.

🚀 USAGE:
error_manager.handle_error(exception, {"operation": "trade", "symbol": "EURUSD"})

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

import traceback
import sys
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import threading
import json
from pathlib import Path
import hashlib
import uuid
import pickle
import os

class ErrorSeverity(Enum):
    """Error severity levels"""
    CRITICAL = "critical"    # System-breaking errors
    HIGH = "high"           # Major functionality errors
    MEDIUM = "medium"       # Minor functionality errors
    LOW = "low"            # Warning-level errors
    INFO = "info"          # Informational errors

class ErrorCategory(Enum):
    """Error categories for client-side"""
    MT5_CONNECTION = "mt5_connection"
    WEBSOCKET = "websocket"
    REDPANDA = "redpanda"
    CONFIG = "configuration"
    DATA_PROCESSING = "data_processing"
    UI = "user_interface"
    SYSTEM = "system"
    UNKNOWN = "unknown"

@dataclass 
class ErrorDNA:
    """AI Brain Error DNA - Intelligent error fingerprinting"""
    dna_id: str
    location_fingerprint: str
    error_type_fingerprint: str
    context_fingerprint: str
    environment_fingerprint: str
    pattern_signature: str
    confidence: float = 0.0
    similarity_threshold: float = 0.8
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class ErrorSolution:
    """AI Brain Error Solution with confidence and learning"""
    solution_id: str
    solution_type: str  # exact_match, similar_match, pattern_based, generated
    immediate_fix: str
    preventive_measures: List[str]
    confidence: float
    success_rate: float = 0.0
    usage_count: int = 0
    last_applied: Optional[datetime] = None
    
    def __post_init__(self):
        if self.preventive_measures is None:
            self.preventive_measures = []

@dataclass
class ErrorContext:
    """Enhanced error context with AI Brain DNA"""
    timestamp: datetime
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: Optional[str] = None
    traceback: Optional[str] = None
    component: Optional[str] = None
    operation: Optional[str] = None
    user_action: Optional[str] = None
    recovery_suggestions: List[str] = None
    metadata: Dict[str, Any] = None
    # AI Brain enhancements
    dna: Optional[ErrorDNA] = None
    solution: Optional[ErrorSolution] = None
    similar_errors: List[str] = None
    confidence: float = 0.0

    def __post_init__(self):
        if self.recovery_suggestions is None:
            self.recovery_suggestions = []
        if self.metadata is None:
            self.metadata = {}
        if self.similar_errors is None:
            self.similar_errors = []

class ClientErrorHandler:
    """
    AI Brain Enhanced Client-Side Error Handler
    Manages all errors with intelligent DNA recognition and learning capabilities
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        self.error_history: List[ErrorContext] = []
        self.error_handlers: Dict[ErrorCategory, List[Callable]] = {}
        self.error_stats: Dict[str, int] = {}
        self.max_history_size = 1000
        
        # AI Brain Error DNA System
        self.error_dna_database: Dict[str, ErrorContext] = {}
        self.error_patterns: Dict[str, List[str]] = {}
        self.solution_library: Dict[str, ErrorSolution] = {}
        self.dna_cache: Dict[str, ErrorDNA] = {}
        self.learning_enabled = True
        
        # DNA database file path
        self.dna_db_path = Path("logs/ai_brain_error_dna.json")
        self.solution_db_path = Path("logs/ai_brain_solutions.json")
        
        # Initialize AI Brain components
        self._load_error_dna_database()
        self._load_solution_library()
        self._setup_default_handlers()
    
    @classmethod
    def get_instance(cls) -> 'ClientErrorHandler':
        """Singleton pattern with thread safety"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def handle_error(self, 
                    error: Union[Exception, str],
                    category: ErrorCategory = ErrorCategory.UNKNOWN,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    component: Optional[str] = None,
                    operation: Optional[str] = None,
                    user_action: Optional[str] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> ErrorContext:
        """
        Handle error with full context and recovery suggestions
        
        Args:
            error: Exception object or error message
            category: Error category
            severity: Error severity
            component: Component where error occurred
            operation: Operation being performed
            user_action: User action that triggered error
            metadata: Additional metadata
            
        Returns:
            ErrorContext with full error information
        """
        # Generate error ID
        error_id = f"{category.value}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Extract error information
        if isinstance(error, Exception):
            message = str(error)
            error_type = type(error).__name__
            traceback_info = traceback.format_exc()
        else:
            message = str(error)
            error_type = "StringError"
            traceback_info = None
        
        # AI Brain Enhancement: Generate Error DNA
        error_dna = self._generate_error_dna(message, traceback_info, category, component, metadata or {})
        
        # AI Brain Enhancement: Find solution with confidence
        solution = self._find_intelligent_solution(error_dna, category, error_type)
        
        # AI Brain Enhancement: Find similar errors
        similar_errors = self._find_similar_errors(error_dna)
        
        # Calculate overall confidence
        confidence = self._calculate_error_confidence(error_dna, solution, len(similar_errors))
        
        # Create enhanced error context
        error_context = ErrorContext(
            timestamp=datetime.now(),
            error_id=error_id,
            category=category,
            severity=severity,
            message=message,
            details=f"{error_type}: {message}",
            traceback=traceback_info,
            component=component,
            operation=operation,
            user_action=user_action,
            recovery_suggestions=self._get_recovery_suggestions(category, error_type),
            metadata=metadata or {},
            # AI Brain enhancements
            dna=error_dna,
            solution=solution,
            similar_errors=similar_errors,
            confidence=confidence
        )
        
        # AI Brain: Learn from this error
        if self.learning_enabled:
            self._learn_from_error(error_context)
        
        # Add to history
        self._add_to_history(error_context)
        
        # Update statistics
        self._update_stats(category, severity, error_type)
        
        # Execute registered handlers
        self._execute_handlers(error_context)
        
        return error_context
    
    def handle_mt5_error(self, error: Exception, operation: str = None) -> ErrorContext:
        """Handle MT5-specific errors"""
        return self.handle_error(
            error=error,
            category=ErrorCategory.MT5_CONNECTION,
            severity=ErrorSeverity.HIGH,
            component="MT5Handler",
            operation=operation,
            metadata={"mt5_specific": True}
        )
    
    def handle_websocket_error(self, error: Exception, operation: str = None) -> ErrorContext:
        """Handle WebSocket-specific errors"""
        return self.handle_error(
            error=error,
            category=ErrorCategory.WEBSOCKET,
            severity=ErrorSeverity.MEDIUM,
            component="WebSocketClient",
            operation=operation,
            metadata={"websocket_specific": True}
        )
    
    def handle_config_error(self, error: Exception, config_section: str = None) -> ErrorContext:
        """Handle configuration-specific errors"""
        return self.handle_error(
            error=error,
            category=ErrorCategory.CONFIG,
            severity=ErrorSeverity.HIGH,
            component="ConfigManager",
            operation="config_loading",
            metadata={"config_section": config_section}
        )
    
    def register_handler(self, category: ErrorCategory, handler: Callable[[ErrorContext], None]):
        """Register error handler for specific category"""
        if category not in self.error_handlers:
            self.error_handlers[category] = []
        self.error_handlers[category].append(handler)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            'total_errors': len(self.error_history),
            'error_stats': self.error_stats.copy(),
            'recent_errors': len([e for e in self.error_history 
                                if (datetime.now() - e.timestamp).seconds < 3600]),
            'categories': {cat.value: len([e for e in self.error_history 
                                        if e.category == cat]) 
                          for cat in ErrorCategory},
            'severities': {sev.value: len([e for e in self.error_history 
                                        if e.severity == sev]) 
                          for sev in ErrorSeverity}
        }
    
    def get_recent_errors(self, limit: int = 10) -> List[ErrorContext]:
        """Get recent errors"""
        return sorted(self.error_history, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def clear_history(self, older_than_hours: Optional[int] = None):
        """Clear error history"""
        if older_than_hours:
            cutoff = datetime.now() - timedelta(hours=older_than_hours)
            self.error_history = [e for e in self.error_history if e.timestamp > cutoff]
        else:
            self.error_history.clear()
        
        # Reset stats
        self.error_stats.clear()
    
    def export_errors(self, filepath: str, format: str = "json"):
        """Export error history to file"""
        try:
            data = [asdict(error) for error in self.error_history]
            
            if format.lower() == "json":
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            print(f"Failed to export errors: {e}")
    
    def _setup_default_handlers(self):
        """Setup default error handlers"""
        # MT5 Connection handler
        def mt5_handler(error_context: ErrorContext):
            if error_context.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
                print(f"🚨 MT5 ERROR: {error_context.message}")
        
        # WebSocket handler
        def websocket_handler(error_context: ErrorContext):
            if "connection" in error_context.message.lower():
                print(f"🔌 WebSocket: {error_context.message}")
        
        self.register_handler(ErrorCategory.MT5_CONNECTION, mt5_handler)
        self.register_handler(ErrorCategory.WEBSOCKET, websocket_handler)
    
    def _get_recovery_suggestions(self, category: ErrorCategory, error_type: str) -> List[str]:
        """Get recovery suggestions based on error category and type"""
        suggestions_map = {
            ErrorCategory.MT5_CONNECTION: [
                "Check MT5 terminal is running and logged in",
                "Verify MT5 Expert Advisors are enabled",
                "Restart MT5 terminal if connection persists",
                "Check network connectivity"
            ],
            ErrorCategory.WEBSOCKET: [
                "Check server connectivity",
                "Verify WebSocket URL is correct",
                "Try reconnecting after a few seconds",
                "Check firewall settings"
            ],
            ErrorCategory.CONFIG: [
                "Check configuration file exists and is readable",
                "Verify configuration syntax is correct",
                "Reset to default configuration if needed",
                "Check file permissions"
            ],
            ErrorCategory.DATA_PROCESSING: [
                "Verify data format is correct",
                "Check for missing required fields",
                "Validate data ranges and types",
                "Try processing smaller data batches"
            ]
        }
        
        return suggestions_map.get(category, ["Contact support if issue persists"])
    
    def _add_to_history(self, error_context: ErrorContext):
        """Add error to history with size management"""
        self.error_history.append(error_context)
        
        # Manage history size
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size:]
    
    def _update_stats(self, category: ErrorCategory, severity: ErrorSeverity, error_type: str):
        """Update error statistics"""
        keys = [
            f"category_{category.value}",
            f"severity_{severity.value}",
            f"type_{error_type}"
        ]
        
        for key in keys:
            self.error_stats[key] = self.error_stats.get(key, 0) + 1
    
    def _execute_handlers(self, error_context: ErrorContext):
        """Execute registered handlers for error category"""
        if error_context.category in self.error_handlers:
            for handler in self.error_handlers[error_context.category]:
                try:
                    handler(error_context)
                except Exception as e:
                    print(f"Error handler failed: {e}")
    
    # ==================== AI BRAIN ERROR DNA METHODS ====================
    
    def _generate_error_dna(self, message: str, traceback_info: Optional[str], 
                           category: ErrorCategory, component: Optional[str], 
                           metadata: Dict[str, Any]) -> ErrorDNA:
        """Generate AI Brain Error DNA with intelligent fingerprinting"""
        
        # Location fingerprint from traceback
        location_fingerprint = self._generate_location_fingerprint(traceback_info)
        
        # Error type fingerprint from message pattern
        error_type_fingerprint = self._generate_error_type_fingerprint(message)
        
        # Context fingerprint from category and component
        context_fingerprint = self._generate_context_fingerprint(category, component, metadata)
        
        # Environment fingerprint
        environment_fingerprint = self._generate_environment_fingerprint()
        
        # Combined pattern signature
        pattern_signature = self._generate_pattern_signature(
            location_fingerprint, error_type_fingerprint, context_fingerprint
        )
        
        # Generate unique DNA ID
        dna_id = hashlib.sha256(
            f"{location_fingerprint}:{error_type_fingerprint}:{context_fingerprint}".encode()
        ).hexdigest()[:16]
        
        return ErrorDNA(
            dna_id=dna_id,
            location_fingerprint=location_fingerprint,
            error_type_fingerprint=error_type_fingerprint,
            context_fingerprint=context_fingerprint,
            environment_fingerprint=environment_fingerprint,
            pattern_signature=pattern_signature,
            confidence=0.95  # High confidence in DNA generation
        )
    
    def _generate_location_fingerprint(self, traceback_info: Optional[str]) -> str:
        """Generate location fingerprint from stack trace"""
        if not traceback_info:
            return "no_traceback"
        
        # Extract file paths and line numbers
        lines = traceback_info.split('\n')
        locations = []
        
        for line in lines:
            if 'File "' in line and ', line ' in line:
                # Extract file and line info
                try:
                    file_part = line.split('File "')[1].split('", line ')[0]
                    line_part = line.split(', line ')[1].split(',')[0]
                    # Use just filename, not full path for pattern matching
                    filename = Path(file_part).name
                    locations.append(f"{filename}:{line_part}")
                except:
                    continue
        
        # Create fingerprint from top 3 locations
        key_locations = locations[:3]
        return hashlib.md5("|".join(key_locations).encode()).hexdigest()[:8]
    
    def _generate_error_type_fingerprint(self, message: str) -> str:
        """Generate error type fingerprint from message patterns"""
        message_lower = message.lower()
        
        # Common error patterns
        patterns = {
            'connection': ['connection', 'connect', 'timeout', 'refused', 'unreachable'],
            'null_reference': ['nonetype', 'none', 'null', 'undefined'],
            'type_error': ['not callable', 'not iterable', 'not subscriptable', 'wrong type'],
            'file_error': ['file not found', 'no such file', 'permission denied', 'directory'],
            'network_error': ['network', 'socket', 'dns', 'http', 'ssl'],
            'mt5_error': ['mt5', 'metatrader', 'terminal', 'symbol', 'account'],
            'config_error': ['config', 'setting', 'parameter', 'option'],
            'data_error': ['data', 'format', 'parse', 'decode', 'invalid']
        }
        
        # Find matching patterns
        matched_patterns = []
        for pattern_name, keywords in patterns.items():
            if any(keyword in message_lower for keyword in keywords):
                matched_patterns.append(pattern_name)
        
        if matched_patterns:
            pattern_key = "|".join(sorted(matched_patterns))
        else:
            # Fallback to message hash
            pattern_key = f"unknown_{hashlib.md5(message.encode()).hexdigest()[:8]}"
        
        return hashlib.md5(pattern_key.encode()).hexdigest()[:8]
    
    def _generate_context_fingerprint(self, category: ErrorCategory, 
                                     component: Optional[str], 
                                     metadata: Dict[str, Any]) -> str:
        """Generate context fingerprint from category, component, and metadata"""
        context_parts = [
            category.value,
            component or "unknown",
            str(len(metadata))  # Metadata complexity indicator
        ]
        
        # Add key metadata values
        key_metadata = ['operation', 'user_action', 'config_section', 'mt5_specific']
        for key in key_metadata:
            if key in metadata:
                context_parts.append(f"{key}:{str(metadata[key])[:20]}")
        
        context_key = "|".join(context_parts)
        return hashlib.md5(context_key.encode()).hexdigest()[:8]
    
    def _generate_environment_fingerprint(self) -> str:
        """Generate environment fingerprint"""
        env_parts = [
            sys.platform,
            f"python_{sys.version_info.major}.{sys.version_info.minor}",
            str(threading.current_thread().ident)[:8]
        ]
        
        env_key = "|".join(env_parts)
        return hashlib.md5(env_key.encode()).hexdigest()[:8]
    
    def _generate_pattern_signature(self, location: str, error_type: str, context: str) -> str:
        """Generate combined pattern signature"""
        signature = f"{location}:{error_type}:{context}"
        return hashlib.sha256(signature.encode()).hexdigest()[:12]
    
    def _find_intelligent_solution(self, dna: ErrorDNA, category: ErrorCategory, 
                                  error_type: str) -> Optional[ErrorSolution]:
        """Find intelligent solution with AI Brain patterns"""
        
        # 1. Check for exact DNA match
        exact_solution = self.solution_library.get(dna.dna_id)
        if exact_solution and exact_solution.success_rate > 0.7:
            exact_solution.usage_count += 1
            exact_solution.last_applied = datetime.now()
            return exact_solution
        
        # 2. Check for similar patterns
        similar_solution = self._find_similar_solution(dna)
        if similar_solution and similar_solution.confidence > 0.6:
            return similar_solution
        
        # 3. Generate pattern-based solution
        pattern_solution = self._generate_pattern_solution(category, error_type, dna)
        if pattern_solution:
            return pattern_solution
        
        # 4. Fallback to default solution
        return self._generate_default_solution(category, error_type)
    
    def _find_similar_solution(self, dna: ErrorDNA) -> Optional[ErrorSolution]:
        """Find similar solution based on DNA similarity"""
        best_match = None
        best_similarity = 0.0
        
        for solution_id, solution in self.solution_library.items():
            # Find corresponding DNA from database
            if solution_id in self.error_dna_database:
                stored_context = self.error_dna_database[solution_id]
                if stored_context.dna:
                    similarity = self._calculate_dna_similarity(dna, stored_context.dna)
                    if similarity > best_similarity and similarity > dna.similarity_threshold:
                        best_similarity = similarity
                        best_match = solution
        
        if best_match:
            # Create similar solution with adjusted confidence
            return ErrorSolution(
                solution_id=f"similar_{uuid.uuid4().hex[:8]}",
                solution_type="similar_match",
                immediate_fix=best_match.immediate_fix,
                preventive_measures=best_match.preventive_measures,
                confidence=best_similarity * 0.8,  # Reduce confidence for similar matches
                success_rate=best_match.success_rate * 0.9
            )
        
        return None
    
    def _calculate_dna_similarity(self, dna1: ErrorDNA, dna2: ErrorDNA) -> float:
        """Calculate similarity between two Error DNA patterns"""
        similarities = []
        
        # Location similarity
        if dna1.location_fingerprint == dna2.location_fingerprint:
            similarities.append(0.4)  # 40% weight for exact location match
        elif dna1.location_fingerprint[:4] == dna2.location_fingerprint[:4]:
            similarities.append(0.2)  # 20% for partial location match
        else:
            similarities.append(0.0)
        
        # Error type similarity
        if dna1.error_type_fingerprint == dna2.error_type_fingerprint:
            similarities.append(0.3)  # 30% weight
        else:
            similarities.append(0.0)
        
        # Context similarity
        if dna1.context_fingerprint == dna2.context_fingerprint:
            similarities.append(0.2)  # 20% weight
        else:
            similarities.append(0.0)
        
        # Environment similarity (lower weight)
        if dna1.environment_fingerprint == dna2.environment_fingerprint:
            similarities.append(0.1)  # 10% weight
        else:
            similarities.append(0.0)
        
        return sum(similarities)
    
    def _generate_pattern_solution(self, category: ErrorCategory, error_type: str, 
                                 dna: ErrorDNA) -> Optional[ErrorSolution]:
        """Generate solution based on error patterns"""
        pattern_solutions = {
            ErrorCategory.MT5_CONNECTION: {
                'immediate_fix': "Verify MT5 terminal connection and login status",
                'preventive_measures': [
                    "Ensure MT5 Expert Advisors are enabled",
                    "Check internet connectivity",
                    "Verify MT5 server settings"
                ],
                'confidence': 0.85
            },
            ErrorCategory.WEBSOCKET: {
                'immediate_fix': "Reconnect WebSocket connection with exponential backoff",
                'preventive_measures': [
                    "Implement connection health monitoring",
                    "Add automatic reconnection logic",
                    "Verify WebSocket endpoint availability"
                ],
                'confidence': 0.8
            },
            ErrorCategory.CONFIG: {
                'immediate_fix': "Validate configuration file and reset to defaults if corrupted",
                'preventive_measures': [
                    "Create configuration backup before changes",
                    "Implement configuration validation",
                    "Add configuration file monitoring"
                ],
                'confidence': 0.9
            }
        }
        
        solution_template = pattern_solutions.get(category)
        if solution_template:
            return ErrorSolution(
                solution_id=f"pattern_{uuid.uuid4().hex[:8]}",
                solution_type="pattern_based",
                immediate_fix=solution_template['immediate_fix'],
                preventive_measures=solution_template['preventive_measures'],
                confidence=solution_template['confidence']
            )
        
        return None
    
    def _generate_default_solution(self, category: ErrorCategory, error_type: str) -> ErrorSolution:
        """Generate default solution when no pattern matches"""
        return ErrorSolution(
            solution_id=f"default_{uuid.uuid4().hex[:8]}",
            solution_type="generated",
            immediate_fix="Review error details and consult documentation",
            preventive_measures=[
                "Implement proper error handling",
                "Add logging for better diagnostics",
                "Consider adding monitoring and alerts"
            ],
            confidence=0.3
        )
    
    def _find_similar_errors(self, dna: ErrorDNA) -> List[str]:
        """Find similar errors based on DNA patterns"""
        similar_errors = []
        
        for stored_id, stored_context in self.error_dna_database.items():
            if stored_context.dna:
                similarity = self._calculate_dna_similarity(dna, stored_context.dna)
                if similarity > 0.7:  # 70% similarity threshold
                    similar_errors.append(stored_id)
        
        return similar_errors[:5]  # Return top 5 similar errors
    
    def _calculate_error_confidence(self, dna: ErrorDNA, solution: Optional[ErrorSolution], 
                                   similar_count: int) -> float:
        """Calculate overall error handling confidence"""
        confidence_factors = []
        
        # DNA generation confidence
        confidence_factors.append(dna.confidence * 0.3)
        
        # Solution confidence
        if solution:
            confidence_factors.append(solution.confidence * 0.5)
        else:
            confidence_factors.append(0.0)
        
        # Similar errors boost confidence
        similarity_boost = min(similar_count * 0.1, 0.2)  # Max 20% boost
        confidence_factors.append(similarity_boost)
        
        return sum(confidence_factors)
    
    def _learn_from_error(self, error_context: ErrorContext):
        """Learn from error for future recognition and solutions"""
        if not error_context.dna:
            return
        
        # Store error in DNA database
        self.error_dna_database[error_context.dna.dna_id] = error_context
        
        # Store solution if available
        if error_context.solution:
            self.solution_library[error_context.dna.dna_id] = error_context.solution
        
        # Update patterns
        pattern_key = error_context.dna.pattern_signature
        if pattern_key not in self.error_patterns:
            self.error_patterns[pattern_key] = []
        self.error_patterns[pattern_key].append(error_context.dna.dna_id)
        
        # Periodic database save (every 10 errors)
        if len(self.error_dna_database) % 10 == 0:
            self._save_error_dna_database()
    
    def _load_error_dna_database(self):
        """Load error DNA database from disk"""
        try:
            if self.dna_db_path.exists():
                with open(self.dna_db_path, 'r') as f:
                    data = json.load(f)
                    # Convert back to ErrorContext objects
                    for dna_id, context_data in data.items():
                        # Reconstruct ErrorContext from saved data
                        # This is a simplified version - in production you'd use proper serialization
                        pass
        except Exception as e:
            print(f"Failed to load error DNA database: {e}")
    
    def _save_error_dna_database(self):
        """Save error DNA database to disk"""
        try:
            # Ensure directory exists
            self.dna_db_path.parent.mkdir(exist_ok=True)
            
            # Convert ErrorContext objects to serializable format
            serializable_data = {}
            for dna_id, context in self.error_dna_database.items():
                # Simplified serialization - in production use proper serialization
                serializable_data[dna_id] = {
                    'error_id': context.error_id,
                    'message': context.message,
                    'category': context.category.value,
                    'severity': context.severity.value,
                    'timestamp': context.timestamp.isoformat(),
                    'confidence': context.confidence
                }
            
            with open(self.dna_db_path, 'w') as f:
                json.dump(serializable_data, f, indent=2)
                
        except Exception as e:
            print(f"Failed to save error DNA database: {e}")
    
    def _load_solution_library(self):
        """Load solution library from disk"""
        try:
            if self.solution_db_path.exists():
                with open(self.solution_db_path, 'r') as f:
                    data = json.load(f)
                    # Convert back to ErrorSolution objects
                    # This is a simplified version - in production you'd use proper serialization
                    pass
        except Exception as e:
            print(f"Failed to load solution library: {e}")
    
    def get_ai_brain_statistics(self) -> Dict[str, Any]:
        """Get AI Brain error handling statistics"""
        return {
            'error_dna_database_size': len(self.error_dna_database),
            'solution_library_size': len(self.solution_library),
            'pattern_count': len(self.error_patterns),
            'learning_enabled': self.learning_enabled,
            'average_confidence': sum(ctx.confidence for ctx in self.error_dna_database.values()) / max(len(self.error_dna_database), 1),
            'top_patterns': dict(list(sorted([(k, len(v)) for k, v in self.error_patterns.items()], key=lambda x: x[1], reverse=True))[:5])
        }
    
    def reset_ai_brain_learning(self):
        """Reset AI Brain learning data (use with caution)"""
        self.error_dna_database.clear()
        self.solution_library.clear()
        self.error_patterns.clear()
        self.dna_cache.clear()
        
        # Remove database files
        for db_path in [self.dna_db_path, self.solution_db_path]:
            if db_path.exists():
                db_path.unlink()


# Global instance
client_error_handler = ClientErrorHandler.get_instance()

# Convenience functions
def handle_error(error: Union[Exception, str],
                category: ErrorCategory = ErrorCategory.UNKNOWN,
                severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                component: Optional[str] = None,
                operation: Optional[str] = None,
                metadata: Optional[Dict[str, Any]] = None) -> ErrorContext:
    """Handle error with centralized system"""
    return client_error_handler.handle_error(
        error, category, severity, component, operation, metadata=metadata
    )

def handle_mt5_error(error: Exception, operation: str = None) -> ErrorContext:
    """Handle MT5-specific error"""
    return client_error_handler.handle_mt5_error(error, operation)

def handle_websocket_error(error: Exception, operation: str = None) -> ErrorContext:
    """Handle WebSocket-specific error"""
    return client_error_handler.handle_websocket_error(error, operation)

def get_error_stats() -> Dict[str, Any]:
    """Get error statistics"""
    return client_error_handler.get_error_statistics()