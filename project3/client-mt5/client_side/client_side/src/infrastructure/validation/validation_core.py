"""
validation_core.py - Core Validation Engine

🎯 PURPOSE:
Business: Advanced validation engine with business rule enforcement
Technical: High-performance validation with caching and rule composition
Domain: Validation Engine/Business Rules/Data Integrity

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:27.858Z
Session: client-side-ai-brain-full-compliance
Confidence: 90%
Complexity: high

🧩 PATTERNS USED:
- AI_BRAIN_VALIDATION_ENGINE: Advanced validation with rule composition
- BUSINESS_RULE_ENGINE: Configurable business rule validation

📦 DEPENDENCIES:
Internal: logger_manager, cache_core
External: typing, functools, inspect, ast

💡 AI DECISION REASONING:
Core validation engine provides foundation for all data validation with high performance and extensible rule system.

🚀 USAGE:
validation_core.add_rule("positive_volume", lambda x: x > 0)

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

import re
import json
import threading
import hashlib
import uuid
from typing import Dict, Any, Optional, List, Union, Callable, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
from pathlib import Path
import inspect

class ValidationSeverity(Enum):
    """Validation severity levels"""
    CRITICAL = "critical"  # Must fix before proceeding
    HIGH = "high"         # Should fix soon
    MEDIUM = "medium"     # Should fix when convenient
    LOW = "low"          # Minor issues
    INFO = "info"        # Informational only

class ValidationCategory(Enum):
    """Validation categories for trading client"""
    MT5_CONNECTION = "mt5_connection"
    TRADING_PARAMS = "trading_parameters"
    DATA_INTEGRITY = "data_integrity"
    CONFIGURATION = "configuration"
    SECURITY = "security"
    PERFORMANCE = "performance"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM_STATE = "system_state"
    USER_INPUT = "user_input"
    NETWORK = "network"

class RuleType(Enum):
    """Rule types for different validation approaches"""
    REGEX_PATTERN = "regex_pattern"
    VALUE_RANGE = "value_range"
    TYPE_CHECK = "type_check"
    CUSTOM_FUNCTION = "custom_function"
    BUSINESS_RULE = "business_rule"
    STATE_VALIDATION = "state_validation"
    DEPENDENCY_CHECK = "dependency_check"
    FORMAT_VALIDATION = "format_validation"

@dataclass
class ValidationResult:
    """Validation result with AI Brain intelligence"""
    rule_id: str
    field: str
    value: Any
    is_valid: bool
    severity: ValidationSeverity
    category: ValidationCategory
    message: str
    suggestion: Optional[str] = None
    error_code: Optional[str] = None
    metadata: Dict[str, Any] = None
    confidence: float = 1.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class ValidationRule:
    """AI Brain validation rule with learning capabilities"""
    id: str
    name: str
    category: ValidationCategory
    rule_type: RuleType
    field: str
    description: str
    severity: ValidationSeverity = ValidationSeverity.MEDIUM
    enabled: bool = True
    pattern: Optional[str] = None
    validator_func: Optional[Callable] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    allowed_values: Optional[List[Any]] = None
    required_type: Optional[type] = None
    dependencies: List[str] = None
    metadata: Dict[str, Any] = None
    success_rate: float = 1.0
    usage_count: int = 0
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.metadata is None:
            self.metadata = {}
        if self.last_updated is None:
            self.last_updated = datetime.now()

@dataclass
class ValidationContext:
    """Validation context for complex validations"""
    data: Dict[str, Any]
    source: str
    operation: str
    user_context: Optional[Dict[str, Any]] = None
    system_context: Optional[Dict[str, Any]] = None
    validation_mode: str = "strict"  # strict, permissive, adaptive
    
    def __post_init__(self):
        if self.user_context is None:
            self.user_context = {}
        if self.system_context is None:
            self.system_context = {}

@dataclass
class ValidationStats:
    """Validation system statistics"""
    total_validations: int = 0
    successful_validations: int = 0
    failed_validations: int = 0
    rules_triggered: int = 0
    average_validation_time: float = 0.0
    validations_by_category: Dict[str, int] = None
    validations_by_severity: Dict[str, int] = None
    rule_performance: Dict[str, float] = None
    
    def __post_init__(self):
        if self.validations_by_category is None:
            self.validations_by_category = defaultdict(int)
        if self.validations_by_severity is None:
            self.validations_by_severity = defaultdict(int)
        if self.rule_performance is None:
            self.rule_performance = defaultdict(float)

class ValidationCore:
    """
    AI Brain Validation Core System
    Intelligent business rule validation with adaptive learning
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        # Rule storage and management
        self._rules: Dict[str, ValidationRule] = {}
        self._category_rules: Dict[ValidationCategory, Set[str]] = defaultdict(set)
        self._field_rules: Dict[str, Set[str]] = defaultdict(set)
        
        # AI Brain features
        self._validation_history: deque = deque(maxlen=10000)
        self._rule_learning: Dict[str, List[ValidationResult]] = defaultdict(list)
        self._pattern_cache: Dict[str, re.Pattern] = {}
        self._adaptive_thresholds: Dict[str, Dict[str, float]] = defaultdict(dict)
        
        # Performance tracking
        self._stats = ValidationStats()
        self._validation_times = deque(maxlen=1000)
        
        # Configuration
        self._enable_learning = True
        self._enable_adaptive_thresholds = True
        self._cache_patterns = True
        
        # Persistence
        self._rules_path = Path("logs/validation_rules.json")
        self._stats_path = Path("logs/validation_stats.json")
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Initialize system
        self._initialize_validation_core()
    
    @classmethod
    def get_instance(cls) -> 'ValidationCore':
        """Singleton pattern with thread safety"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def _initialize_validation_core(self):
        """Initialize validation core system"""
        # Load default rules
        self._load_default_rules()
        
        # Load persisted rules and stats
        self._load_persistence()
        
        print("✅ AI Brain Validation Core initialized")
    
    # ==================== RULE MANAGEMENT ====================
    
    def add_rule(self, rule: ValidationRule) -> bool:
        """Add validation rule to the system"""
        try:
            with self._lock:
                # Store rule
                self._rules[rule.id] = rule
                
                # Update category index
                self._category_rules[rule.category].add(rule.id)
                
                # Update field index
                self._field_rules[rule.field].add(rule.id)
                
                # Cache pattern if regex rule
                if rule.rule_type == RuleType.REGEX_PATTERN and rule.pattern:
                    self._pattern_cache[rule.id] = re.compile(rule.pattern)
                
                print(f"➕ Validation rule '{rule.name}' added")
                return True
                
        except Exception as e:
            print(f"❌ Failed to add rule {rule.id}: {e}")
            return False
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove validation rule"""
        try:
            with self._lock:
                if rule_id not in self._rules:
                    return False
                
                rule = self._rules[rule_id]
                
                # Remove from indexes
                self._category_rules[rule.category].discard(rule_id)
                self._field_rules[rule.field].discard(rule_id)
                
                # Remove from pattern cache
                if rule_id in self._pattern_cache:
                    del self._pattern_cache[rule_id]
                
                # Remove rule
                del self._rules[rule_id]
                
                print(f"➖ Validation rule '{rule.name}' removed")
                return True
                
        except Exception as e:
            print(f"❌ Failed to remove rule {rule_id}: {e}")
            return False
    
    def enable_rule(self, rule_id: str) -> bool:
        """Enable validation rule"""
        with self._lock:
            if rule_id in self._rules:
                self._rules[rule_id].enabled = True
                return True
            return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """Disable validation rule"""
        with self._lock:
            if rule_id in self._rules:
                self._rules[rule_id].enabled = False
                return True
            return False
    
    # ==================== VALIDATION METHODS ====================
    
    def validate(self, data: Dict[str, Any], context: ValidationContext) -> List[ValidationResult]:
        """Validate data against all applicable rules"""
        start_time = datetime.now()
        results = []
        
        try:
            with self._lock:
                # Update stats
                self._stats.total_validations += 1
                
                # Get applicable rules based on context
                applicable_rules = self._get_applicable_rules(data, context)
                
                # Execute validation rules
                for rule in applicable_rules:
                    if not rule.enabled:
                        continue
                    
                    # Extract field value
                    field_value = self._extract_field_value(data, rule.field)
                    
                    # Execute rule
                    result = self._execute_rule(rule, field_value, data, context)
                    
                    if result:
                        results.append(result)
                        
                        # Update rule statistics
                        rule.usage_count += 1
                        self._stats.rules_triggered += 1
                        
                        # Learn from result if enabled
                        if self._enable_learning:
                            self._learn_from_result(rule, result)
                
                # Update validation statistics
                has_failures = any(not r.is_valid for r in results)
                if has_failures:
                    self._stats.failed_validations += 1
                else:
                    self._stats.successful_validations += 1
                
                # Update category and severity stats
                for result in results:
                    self._stats.validations_by_category[result.category.value] += 1
                    self._stats.validations_by_severity[result.severity.value] += 1
                
                # Record validation time
                validation_time = (datetime.now() - start_time).total_seconds()
                self._validation_times.append(validation_time)
                self._update_average_validation_time()
                
                # Store in history
                self._validation_history.extend(results)
                
                return results
                
        except Exception as e:
            print(f"❌ Validation error: {e}")
            return [ValidationResult(
                rule_id="system_error",
                field="system",
                value=None,
                is_valid=False,
                severity=ValidationSeverity.CRITICAL,
                category=ValidationCategory.SYSTEM_STATE,
                message=f"Validation system error: {e}",
                confidence=1.0
            )]
    
    def validate_field(self, field: str, value: Any, context: Optional[ValidationContext] = None) -> List[ValidationResult]:
        """Validate single field value"""
        data = {field: value}
        if context is None:
            context = ValidationContext(data=data, source="field_validation", operation="single_field")
        return self.validate(data, context)
    
    def validate_mt5_connection_params(self, params: Dict[str, Any]) -> List[ValidationResult]:
        """Validate MT5 connection parameters"""
        context = ValidationContext(
            data=params,
            source="mt5_handler",
            operation="connection_validation"
        )
        return self.validate(params, context)
    
    def validate_trading_params(self, params: Dict[str, Any]) -> List[ValidationResult]:
        """Validate trading parameters"""
        context = ValidationContext(
            data=params,
            source="trading_engine",
            operation="trade_validation"
        )
        return self.validate(params, context)
    
    def validate_config(self, config: Dict[str, Any], section: str) -> List[ValidationResult]:
        """Validate configuration section"""
        context = ValidationContext(
            data=config,
            source="config_manager",
            operation="config_validation",
            system_context={"section": section}
        )
        return self.validate(config, context)
    
    # ==================== RULE EXECUTION ====================
    
    def _get_applicable_rules(self, data: Dict[str, Any], context: ValidationContext) -> List[ValidationRule]:
        """Get rules applicable to the data and context"""
        applicable_rules = []
        
        # Get rules for each field in data
        for field in data.keys():
            field_rules = self._field_rules.get(field, set())
            for rule_id in field_rules:
                rule = self._rules.get(rule_id)
                if rule and rule.enabled:
                    applicable_rules.append(rule)
        
        # Add context-specific rules based on source/operation
        if context.source == "mt5_handler":
            mt5_rules = self._category_rules.get(ValidationCategory.MT5_CONNECTION, set())
            for rule_id in mt5_rules:
                rule = self._rules.get(rule_id)
                if rule and rule.enabled and rule not in applicable_rules:
                    applicable_rules.append(rule)
        
        return applicable_rules
    
    def _extract_field_value(self, data: Dict[str, Any], field: str) -> Any:
        """Extract field value, supporting nested fields"""
        if '.' in field:
            # Handle nested field access (e.g., "account.login")
            parts = field.split('.')
            value = data
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return None
            return value
        else:
            return data.get(field)
    
    def _execute_rule(self, rule: ValidationRule, field_value: Any, 
                     full_data: Dict[str, Any], context: ValidationContext) -> Optional[ValidationResult]:
        """Execute individual validation rule"""
        try:
            is_valid = True
            message = ""
            suggestion = None
            confidence = 1.0
            
            # Skip validation if field is None and not required
            if field_value is None and not rule.metadata.get("required", True):
                return None
            
            # Execute based on rule type
            if rule.rule_type == RuleType.REGEX_PATTERN:
                is_valid, message, suggestion = self._execute_regex_rule(rule, field_value)
            
            elif rule.rule_type == RuleType.VALUE_RANGE:
                is_valid, message, suggestion = self._execute_range_rule(rule, field_value)
            
            elif rule.rule_type == RuleType.TYPE_CHECK:
                is_valid, message, suggestion = self._execute_type_rule(rule, field_value)
            
            elif rule.rule_type == RuleType.CUSTOM_FUNCTION:
                is_valid, message, suggestion = self._execute_custom_rule(rule, field_value, full_data, context)
            
            elif rule.rule_type == RuleType.BUSINESS_RULE:
                is_valid, message, suggestion, confidence = self._execute_business_rule(rule, field_value, full_data, context)
            
            elif rule.rule_type == RuleType.STATE_VALIDATION:
                is_valid, message, suggestion = self._execute_state_rule(rule, field_value, full_data, context)
            
            elif rule.rule_type == RuleType.DEPENDENCY_CHECK:
                is_valid, message, suggestion = self._execute_dependency_rule(rule, field_value, full_data, context)
            
            else:
                is_valid = True
                message = "Unknown rule type"
            
            # Apply adaptive adjustments if enabled
            if self._enable_adaptive_thresholds:
                confidence = self._apply_adaptive_confidence(rule, confidence)
            
            return ValidationResult(
                rule_id=rule.id,
                field=rule.field,
                value=field_value,
                is_valid=is_valid,
                severity=rule.severity,
                category=rule.category,
                message=message,
                suggestion=suggestion,
                error_code=rule.metadata.get("error_code"),
                metadata=rule.metadata.copy(),
                confidence=confidence
            )
            
        except Exception as e:
            return ValidationResult(
                rule_id=rule.id,
                field=rule.field,
                value=field_value,
                is_valid=False,
                severity=ValidationSeverity.CRITICAL,
                category=rule.category,
                message=f"Rule execution error: {e}",
                confidence=0.5
            )
    
    def _execute_regex_rule(self, rule: ValidationRule, value: Any) -> Tuple[bool, str, Optional[str]]:
        """Execute regex pattern rule"""
        if value is None:
            return False, "Value is None", "Provide a valid value"
        
        str_value = str(value)
        pattern = self._pattern_cache.get(rule.id)
        
        if not pattern:
            return False, "Invalid regex pattern", "Check rule configuration"
        
        if pattern.match(str_value):
            return True, "Pattern matches", None
        else:
            return False, f"Value '{str_value}' does not match pattern '{rule.pattern}'", f"Value should match pattern: {rule.pattern}"
    
    def _execute_range_rule(self, rule: ValidationRule, value: Any) -> Tuple[bool, str, Optional[str]]:
        """Execute value range rule"""
        if value is None:
            return False, "Value is None", "Provide a numeric value"
        
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return False, f"Value '{value}' is not numeric", "Provide a numeric value"
        
        min_val = rule.min_value
        max_val = rule.max_value
        
        if min_val is not None and numeric_value < min_val:
            return False, f"Value {numeric_value} is below minimum {min_val}", f"Value should be >= {min_val}"
        
        if max_val is not None and numeric_value > max_val:
            return False, f"Value {numeric_value} is above maximum {max_val}", f"Value should be <= {max_val}"
        
        return True, "Value is within range", None
    
    def _execute_type_rule(self, rule: ValidationRule, value: Any) -> Tuple[bool, str, Optional[str]]:
        """Execute type check rule"""
        if rule.required_type is None:
            return True, "No type requirement", None
        
        if isinstance(value, rule.required_type):
            return True, f"Value is of type {rule.required_type.__name__}", None
        else:
            return False, f"Expected {rule.required_type.__name__}, got {type(value).__name__}", f"Convert value to {rule.required_type.__name__}"
    
    def _execute_custom_rule(self, rule: ValidationRule, value: Any, 
                           full_data: Dict[str, Any], context: ValidationContext) -> Tuple[bool, str, Optional[str]]:
        """Execute custom function rule"""
        if not rule.validator_func:
            return False, "No validator function defined", "Define validator function"
        
        try:
            # Check function signature
            sig = inspect.signature(rule.validator_func)
            params = list(sig.parameters.keys())
            
            if len(params) == 1:
                result = rule.validator_func(value)
            elif len(params) == 2:
                result = rule.validator_func(value, full_data)
            elif len(params) == 3:
                result = rule.validator_func(value, full_data, context)
            else:
                result = rule.validator_func(value)
            
            # Handle different return types
            if isinstance(result, bool):
                return result, "Custom validation", "Check validation logic"
            elif isinstance(result, tuple) and len(result) >= 2:
                is_valid = result[0]
                message = result[1]
                suggestion = result[2] if len(result) > 2 else None
                return is_valid, message, suggestion
            else:
                return bool(result), "Custom validation", None
                
        except Exception as e:
            return False, f"Custom validator error: {e}", "Check validator function"
    
    def _execute_business_rule(self, rule: ValidationRule, value: Any, 
                             full_data: Dict[str, Any], context: ValidationContext) -> Tuple[bool, str, Optional[str], float]:
        """Execute business rule with confidence scoring"""
        confidence = 1.0
        
        # Business rule examples for MT5 Trading Client
        if rule.id == "mt5_account_balance_check":
            balance = value
            if balance is None or balance < 0:
                return False, "Invalid account balance", "Check account balance", 0.95
            elif balance < 100:  # Warning for low balance
                return False, "Low account balance warning", "Consider adding funds", 0.8
            else:
                return True, "Account balance OK", None, 0.9
        
        elif rule.id == "trading_symbol_validation":
            symbol = value
            valid_symbols = rule.metadata.get("valid_symbols", [])
            if symbol not in valid_symbols:
                return False, f"Invalid trading symbol: {symbol}", "Use valid trading symbol", 0.95
            else:
                return True, "Valid trading symbol", None, 0.9
        
        elif rule.id == "lot_size_validation":
            lot_size = value
            if lot_size <= 0:
                return False, "Lot size must be positive", "Set positive lot size", 1.0
            elif lot_size > 100:  # Large lot size warning
                return False, "Large lot size warning", "Consider smaller lot size for risk management", 0.7
            else:
                return True, "Lot size OK", None, 0.9
        
        # Default business rule behavior
        return True, "Business rule passed", None, confidence
    
    def _execute_state_rule(self, rule: ValidationRule, value: Any, 
                          full_data: Dict[str, Any], context: ValidationContext) -> Tuple[bool, str, Optional[str]]:
        """Execute system state validation rule"""
        # State validation examples
        if rule.id == "mt5_connection_state":
            if context.system_context.get("mt5_connected", False):
                return True, "MT5 is connected", None
            else:
                return False, "MT5 is not connected", "Connect to MT5 terminal"
        
        elif rule.id == "websocket_connection_state":
            if context.system_context.get("websocket_connected", False):
                return True, "WebSocket is connected", None
            else:
                return False, "WebSocket is not connected", "Check WebSocket connection"
        
        return True, "State validation passed", None
    
    def _execute_dependency_rule(self, rule: ValidationRule, value: Any, 
                               full_data: Dict[str, Any], context: ValidationContext) -> Tuple[bool, str, Optional[str]]:
        """Execute dependency check rule"""
        for dependency in rule.dependencies:
            if dependency not in full_data:
                return False, f"Missing dependency: {dependency}", f"Provide {dependency}"
            
            dep_value = full_data[dependency]
            if dep_value is None:
                return False, f"Dependency {dependency} is None", f"Set value for {dependency}"
        
        return True, "All dependencies satisfied", None
    
    # ==================== AI BRAIN LEARNING METHODS ====================
    
    def _learn_from_result(self, rule: ValidationRule, result: ValidationResult):
        """Learn from validation result to improve rules"""
        if not self._enable_learning:
            return
        
        # Store result for learning
        self._rule_learning[rule.id].append(result)
        
        # Keep only recent results (last 1000)
        if len(self._rule_learning[rule.id]) > 1000:
            self._rule_learning[rule.id] = self._rule_learning[rule.id][-1000:]
        
        # Update rule success rate
        rule_results = self._rule_learning[rule.id]
        successful = sum(1 for r in rule_results if r.is_valid)
        rule.success_rate = successful / len(rule_results)
        
        # Adaptive threshold learning
        if self._enable_adaptive_thresholds:
            self._update_adaptive_thresholds(rule, result)
    
    def _update_adaptive_thresholds(self, rule: ValidationRule, result: ValidationResult):
        """Update adaptive thresholds based on validation patterns"""
        rule_id = rule.id
        
        # Track confidence patterns
        if "confidence" not in self._adaptive_thresholds[rule_id]:
            self._adaptive_thresholds[rule_id]["confidence"] = []
        
        self._adaptive_thresholds[rule_id]["confidence"].append(result.confidence)
        
        # Keep only recent data
        if len(self._adaptive_thresholds[rule_id]["confidence"]) > 100:
            self._adaptive_thresholds[rule_id]["confidence"] = self._adaptive_thresholds[rule_id]["confidence"][-100:]
        
        # Calculate adaptive confidence adjustment
        confidence_values = self._adaptive_thresholds[rule_id]["confidence"]
        if len(confidence_values) > 10:
            avg_confidence = sum(confidence_values) / len(confidence_values)
            self._adaptive_thresholds[rule_id]["avg_confidence"] = avg_confidence
    
    def _apply_adaptive_confidence(self, rule: ValidationRule, base_confidence: float) -> float:
        """Apply adaptive confidence adjustments"""
        rule_id = rule.id
        
        if rule_id in self._adaptive_thresholds:
            avg_confidence = self._adaptive_thresholds[rule_id].get("avg_confidence", 1.0)
            
            # Adjust confidence based on historical performance
            adjustment_factor = avg_confidence / 1.0  # Normalize to historical average
            adjusted_confidence = base_confidence * adjustment_factor
            
            # Ensure confidence stays within bounds
            return max(0.1, min(1.0, adjusted_confidence))
        
        return base_confidence
    
    def _update_average_validation_time(self):
        """Update average validation time"""
        if self._validation_times:
            total_time = sum(self._validation_times)
            self._stats.average_validation_time = total_time / len(self._validation_times)
    
    # ==================== DEFAULT RULES ====================
    
    def _load_default_rules(self):
        """Load default validation rules for MT5 Trading Client"""
        default_rules = [
            # MT5 Connection Rules
            ValidationRule(
                id="mt5_server_validation",
                name="MT5 Server Validation",
                category=ValidationCategory.MT5_CONNECTION,
                rule_type=RuleType.REGEX_PATTERN,
                field="server",
                description="Validate MT5 server name format",
                severity=ValidationSeverity.HIGH,
                pattern=r"^[a-zA-Z0-9.-]+:[0-9]+$",
                metadata={"required": True, "error_code": "MT5_INVALID_SERVER"}
            ),
            
            ValidationRule(
                id="mt5_login_validation",
                name="MT5 Login Validation",
                category=ValidationCategory.MT5_CONNECTION,
                rule_type=RuleType.TYPE_CHECK,
                field="login",
                description="Validate MT5 login is numeric",
                severity=ValidationSeverity.HIGH,
                required_type=int,
                metadata={"required": True, "error_code": "MT5_INVALID_LOGIN"}
            ),
            
            # Trading Parameter Rules
            ValidationRule(
                id="lot_size_range",
                name="Lot Size Range",
                category=ValidationCategory.TRADING_PARAMS,
                rule_type=RuleType.VALUE_RANGE,
                field="lot_size",
                description="Validate lot size is within acceptable range",
                severity=ValidationSeverity.MEDIUM,
                min_value=0.01,
                max_value=100.0,
                metadata={"required": True, "error_code": "TRADING_INVALID_LOT_SIZE"}
            ),
            
            ValidationRule(
                id="symbol_format",
                name="Symbol Format",
                category=ValidationCategory.TRADING_PARAMS,
                rule_type=RuleType.REGEX_PATTERN,
                field="symbol",
                description="Validate trading symbol format",
                severity=ValidationSeverity.HIGH,
                pattern=r"^[A-Z]{3,6}$",
                metadata={"required": True, "error_code": "TRADING_INVALID_SYMBOL"}
            ),
            
            # Configuration Rules
            ValidationRule(
                id="config_section_validation",
                name="Config Section Validation",
                category=ValidationCategory.CONFIGURATION,
                rule_type=RuleType.TYPE_CHECK,
                field="config_data",
                description="Validate configuration data is a dictionary",
                severity=ValidationSeverity.HIGH,
                required_type=dict,
                metadata={"required": True, "error_code": "CONFIG_INVALID_TYPE"}
            ),
            
            # Performance Rules
            ValidationRule(
                id="response_time_check",
                name="Response Time Check",
                category=ValidationCategory.PERFORMANCE,
                rule_type=RuleType.VALUE_RANGE,
                field="response_time",
                description="Check response time is within acceptable limits",
                severity=ValidationSeverity.MEDIUM,
                min_value=0.0,
                max_value=5.0,
                metadata={"required": False, "error_code": "PERF_SLOW_RESPONSE"}
            ),
            
            # Security Rules
            ValidationRule(
                id="password_strength",
                name="Password Strength",
                category=ValidationCategory.SECURITY,
                rule_type=RuleType.REGEX_PATTERN,
                field="password",
                description="Validate password meets minimum requirements",
                severity=ValidationSeverity.HIGH,
                pattern=r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$",
                metadata={"required": True, "error_code": "SEC_WEAK_PASSWORD"}
            ),
            
            # Data Integrity Rules
            ValidationRule(
                id="timestamp_validation",
                name="Timestamp Validation",
                category=ValidationCategory.DATA_INTEGRITY,
                rule_type=RuleType.TYPE_CHECK,
                field="timestamp",
                description="Validate timestamp is datetime object",
                severity=ValidationSeverity.MEDIUM,
                required_type=datetime,
                metadata={"required": False, "error_code": "DATA_INVALID_TIMESTAMP"}
            )
        ]
        
        # Add all default rules
        for rule in default_rules:
            self.add_rule(rule)
        
        print(f"📋 Loaded {len(default_rules)} default validation rules")
    
    # ==================== PERSISTENCE ====================
    
    def _save_persistence(self):
        """Save validation rules and statistics to disk"""
        try:
            # Ensure directory exists
            self._rules_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save rules (excluding validator functions)
            rules_data = {}
            for rule_id, rule in self._rules.items():
                rule_data = asdict(rule)
                # Remove non-serializable validator function
                rule_data.pop('validator_func', None)
                rule_data['last_updated'] = rule.last_updated.isoformat()
                rules_data[rule_id] = rule_data
            
            with open(self._rules_path, 'w') as f:
                json.dump(rules_data, f, indent=2)
            
            # Save statistics
            stats_data = asdict(self._stats)
            stats_data['timestamp'] = datetime.now().isoformat()
            
            with open(self._stats_path, 'w') as f:
                json.dump(stats_data, f, indent=2)
                
        except Exception as e:
            print(f"❌ Failed to save validation persistence: {e}")
    
    def _load_persistence(self):
        """Load validation rules and statistics from disk"""
        try:
            # Load rules
            if self._rules_path.exists():
                with open(self._rules_path, 'r') as f:
                    rules_data = json.load(f)
                
                for rule_id, rule_data in rules_data.items():
                    # Skip if rule already exists (default rules take precedence)
                    if rule_id in self._rules:
                        continue
                    
                    # Reconstruct rule (without validator function)
                    rule_data['last_updated'] = datetime.fromisoformat(rule_data['last_updated'])
                    rule = ValidationRule(**rule_data)
                    self.add_rule(rule)
            
            # Load statistics
            if self._stats_path.exists():
                with open(self._stats_path, 'r') as f:
                    stats_data = json.load(f)
                
                # Restore statistics
                for key, value in stats_data.items():
                    if key != 'timestamp' and hasattr(self._stats, key):
                        setattr(self._stats, key, value)
            
            print("📥 Validation persistence loaded")
            
        except Exception as e:
            print(f"❌ Failed to load validation persistence: {e}")
    
    # ==================== STATISTICS AND REPORTING ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive validation statistics"""
        return {
            'total_validations': self._stats.total_validations,
            'successful_validations': self._stats.successful_validations,
            'failed_validations': self._stats.failed_validations,
            'success_rate': self._stats.successful_validations / max(self._stats.total_validations, 1),
            'rules_triggered': self._stats.rules_triggered,
            'average_validation_time_ms': self._stats.average_validation_time * 1000,
            'active_rules': len([r for r in self._rules.values() if r.enabled]),
            'total_rules': len(self._rules),
            'validations_by_category': dict(self._stats.validations_by_category),
            'validations_by_severity': dict(self._stats.validations_by_severity),
            'rule_performance': dict(self._stats.rule_performance),
            'learning_enabled': self._enable_learning,
            'adaptive_thresholds_enabled': self._enable_adaptive_thresholds
        }
    
    def get_rule_performance(self) -> List[Dict[str, Any]]:
        """Get performance data for all rules"""
        performance_data = []
        
        for rule_id, rule in self._rules.items():
            rule_results = self._rule_learning.get(rule_id, [])
            
            performance_data.append({
                'rule_id': rule.id,
                'name': rule.name,
                'category': rule.category.value,
                'enabled': rule.enabled,
                'usage_count': rule.usage_count,
                'success_rate': rule.success_rate,
                'recent_validations': len(rule_results),
                'avg_confidence': sum(r.confidence for r in rule_results) / max(len(rule_results), 1)
            })
        
        return sorted(performance_data, key=lambda x: x['usage_count'], reverse=True)
    
    def get_recent_validations(self, limit: int = 100, category: Optional[ValidationCategory] = None) -> List[Dict[str, Any]]:
        """Get recent validation results"""
        results = list(self._validation_history)
        
        if category:
            results = [r for r in results if r.category == category]
        
        return [asdict(result) for result in results[-limit:]]
    
    def optimize_rules(self):
        """Optimize validation rules based on performance data"""
        with self._lock:
            optimized_count = 0
            
            for rule_id, rule in self._rules.items():
                # Disable rules with very low usage and poor performance
                if rule.usage_count > 100 and rule.success_rate < 0.1:
                    rule.enabled = False
                    optimized_count += 1
                    print(f"⚠️ Disabled poorly performing rule: {rule.name}")
                
                # Adjust severity based on success rate
                elif rule.success_rate < 0.5 and rule.severity == ValidationSeverity.CRITICAL:
                    rule.severity = ValidationSeverity.HIGH
                    optimized_count += 1
                    print(f"📉 Reduced severity for rule: {rule.name}")
            
            if optimized_count > 0:
                print(f"⚡ Optimized {optimized_count} validation rules")
            
            # Save optimizations
            self._save_persistence()


# ==================== CONVENIENCE FUNCTIONS ====================

# Global instance
validation_core = None

def get_validation_core() -> ValidationCore:
    """Get global validation core instance"""
    global validation_core
    if validation_core is None:
        validation_core = ValidationCore.get_instance()
    return validation_core

def validate_data(data: Dict[str, Any], source: str, operation: str) -> List[ValidationResult]:
    """Convenience function to validate data"""
    context = ValidationContext(data=data, source=source, operation=operation)
    return get_validation_core().validate(data, context)

def validate_field_value(field: str, value: Any) -> List[ValidationResult]:
    """Convenience function to validate single field"""
    return get_validation_core().validate_field(field, value)

def add_custom_rule(rule_id: str, name: str, category: ValidationCategory,
                   field: str, validator_func: Callable, 
                   severity: ValidationSeverity = ValidationSeverity.MEDIUM) -> bool:
    """Convenience function to add custom validation rule"""
    rule = ValidationRule(
        id=rule_id,
        name=name,
        category=category,
        rule_type=RuleType.CUSTOM_FUNCTION,
        field=field,
        description=f"Custom validation for {field}",
        severity=severity,
        validator_func=validator_func
    )
    return get_validation_core().add_rule(rule)