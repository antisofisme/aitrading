"""
Core Validator - Comprehensive input validation with business rules
"""
import re
import json
from datetime import datetime, date
from typing import Dict, Any, Optional, List, Union, Callable, Type
from enum import Enum
from dataclasses import dataclass

class ValidationSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ValidationResult:
    """Result of validation operation"""
    is_valid: bool
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    field_results: Dict[str, bool]
    metadata: Optional[Dict[str, Any]] = None

class ValidationRule:
    """Base validation rule"""
    
    def __init__(self, field_name: str, error_message: str = None, severity: ValidationSeverity = ValidationSeverity.ERROR):
        self.field_name = field_name
        self.error_message = error_message or f"Invalid value for {field_name}"
        self.severity = severity
    
    def validate(self, value: Any, context: Dict[str, Any] = None) -> bool:
        """Override this method in subclasses"""
        return True
    
    def get_error(self, value: Any) -> Dict[str, Any]:
        """Get error details"""
        return {
            "field": self.field_name,
            "message": self.error_message,
            "severity": self.severity.value,
            "value": value,
            "rule": self.__class__.__name__
        }

class RequiredRule(ValidationRule):
    """Required field validation"""
    
    def validate(self, value: Any, context: Dict[str, Any] = None) -> bool:
        return value is not None and value != "" and value != []

class TypeRule(ValidationRule):
    """Type validation"""
    
    def __init__(self, field_name: str, expected_type: Type, **kwargs):
        super().__init__(field_name, **kwargs)
        self.expected_type = expected_type
        self.error_message = self.error_message or f"{field_name} must be of type {expected_type.__name__}"
    
    def validate(self, value: Any, context: Dict[str, Any] = None) -> bool:
        return isinstance(value, self.expected_type)

class RangeRule(ValidationRule):
    """Range validation for numeric values"""
    
    def __init__(self, field_name: str, min_value: Union[int, float] = None, max_value: Union[int, float] = None, **kwargs):
        super().__init__(field_name, **kwargs)
        self.min_value = min_value
        self.max_value = max_value
        self.error_message = self.error_message or f"{field_name} must be between {min_value} and {max_value}"
    
    def validate(self, value: Any, context: Dict[str, Any] = None) -> bool:
        if not isinstance(value, (int, float)):
            return False
        
        if self.min_value is not None and value < self.min_value:
            return False
        
        if self.max_value is not None and value > self.max_value:
            return False
        
        return True

class LengthRule(ValidationRule):
    """Length validation for strings and collections"""
    
    def __init__(self, field_name: str, min_length: int = None, max_length: int = None, **kwargs):
        super().__init__(field_name, **kwargs)
        self.min_length = min_length
        self.max_length = max_length
        self.error_message = self.error_message or f"{field_name} length must be between {min_length} and {max_length}"
    
    def validate(self, value: Any, context: Dict[str, Any] = None) -> bool:
        if not hasattr(value, '__len__'):
            return False
        
        length = len(value)
        
        if self.min_length is not None and length < self.min_length:
            return False
        
        if self.max_length is not None and length > self.max_length:
            return False
        
        return True

class RegexRule(ValidationRule):
    """Regular expression validation"""
    
    def __init__(self, field_name: str, pattern: str, **kwargs):
        super().__init__(field_name, **kwargs)
        self.pattern = re.compile(pattern)
        self.error_message = self.error_message or f"{field_name} format is invalid"
    
    def validate(self, value: Any, context: Dict[str, Any] = None) -> bool:
        if not isinstance(value, str):
            return False
        
        return bool(self.pattern.match(value))

class EmailRule(RegexRule):
    """Email validation"""
    
    def __init__(self, field_name: str, **kwargs):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        super().__init__(field_name, email_pattern, **kwargs)
        self.error_message = self.error_message or f"{field_name} must be a valid email address"

class CustomRule(ValidationRule):
    """Custom validation with function"""
    
    def __init__(self, field_name: str, validation_func: Callable[[Any, Dict[str, Any]], bool], **kwargs):
        super().__init__(field_name, **kwargs)
        self.validation_func = validation_func
    
    def validate(self, value: Any, context: Dict[str, Any] = None) -> bool:
        return self.validation_func(value, context or {})

class CoreValidator:
    """Core validator with comprehensive validation capabilities"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.field_rules: Dict[str, List[ValidationRule]] = {}
        self.business_rules: List[Callable] = []
        self.validation_cache = {}
        self.setup_service_specific_rules()
    
    def add_field_rule(self, rule: ValidationRule):
        """Add validation rule for a field"""
        if rule.field_name not in self.field_rules:
            self.field_rules[rule.field_name] = []
        
        self.field_rules[rule.field_name].append(rule)
    
    def add_business_rule(self, rule_func: Callable[[Dict[str, Any]], ValidationResult]):
        """Add business logic validation rule"""
        self.business_rules.append(rule_func)
    
    def validate_data(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> ValidationResult:
        """Validate data against all rules"""
        errors = []
        warnings = []
        field_results = {}
        
        # Validate individual fields
        for field_name, rules in self.field_rules.items():
            field_value = data.get(field_name)
            field_valid = True
            
            for rule in rules:
                if not rule.validate(field_value, context):
                    field_valid = False
                    error_details = rule.get_error(field_value)
                    
                    if rule.severity == ValidationSeverity.ERROR or rule.severity == ValidationSeverity.CRITICAL:
                        errors.append(error_details)
                    else:
                        warnings.append(error_details)
            
            field_results[field_name] = field_valid
        
        # Validate business rules
        for business_rule in self.business_rules:
            try:
                business_result = business_rule(data, context or {})
                if not business_result.is_valid:
                    errors.extend(business_result.errors)
                    warnings.extend(business_result.warnings)
            except Exception as e:
                errors.append({
                    "field": "business_rule",
                    "message": f"Business rule validation failed: {str(e)}",
                    "severity": "error",
                    "rule": "BusinessRule"
                })
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            field_results=field_results,
            metadata={
                "service": self.service_name,
                "validation_time": datetime.utcnow().isoformat(),
                "total_fields": len(field_results),
                "rules_checked": sum(len(rules) for rules in self.field_rules.values()) + len(self.business_rules)
            }
        )
    
    def validate_field(self, field_name: str, value: Any, context: Dict[str, Any] = None) -> ValidationResult:
        """Validate a single field"""
        if field_name not in self.field_rules:
            return ValidationResult(
                is_valid=True,
                errors=[],
                warnings=[],
                field_results={field_name: True}
            )
        
        errors = []
        warnings = []
        field_valid = True
        
        for rule in self.field_rules[field_name]:
            if not rule.validate(value, context):
                field_valid = False
                error_details = rule.get_error(value)
                
                if rule.severity == ValidationSeverity.ERROR or rule.severity == ValidationSeverity.CRITICAL:
                    errors.append(error_details)
                else:
                    warnings.append(error_details)
        
        return ValidationResult(
            is_valid=field_valid,
            errors=errors,
            warnings=warnings,
            field_results={field_name: field_valid}
        )
    
    def setup_service_specific_rules(self):
        """Setup service-specific validation rules"""
        if self.service_name == "api-gateway":
            self._setup_api_gateway_rules()
        elif self.service_name == "trading-engine":
            self._setup_trading_engine_rules()
        elif self.service_name == "user-service":
            self._setup_user_service_rules()
    
    def _setup_api_gateway_rules(self):
        """Setup API Gateway validation rules"""
        # Request validation rules
        self.add_field_rule(RequiredRule("endpoint"))
        self.add_field_rule(RegexRule("endpoint", r'^/[a-zA-Z0-9/_-]*$'))
        self.add_field_rule(TypeRule("method", str))
        
        # Rate limiting validation
        self.add_field_rule(RangeRule("requests_per_minute", min_value=1, max_value=10000))
    
    def _setup_trading_engine_rules(self):
        """Setup Trading Engine validation rules"""
        # Trading symbol validation
        self.add_field_rule(RequiredRule("symbol"))
        self.add_field_rule(RegexRule("symbol", r'^[A-Z]{3,6}$'))
        
        # Volume validation
        self.add_field_rule(RequiredRule("volume"))
        self.add_field_rule(TypeRule("volume", (int, float)))
        self.add_field_rule(RangeRule("volume", min_value=0.01, max_value=1000000))
        
        # Price validation
        self.add_field_rule(TypeRule("price", (int, float)))
        self.add_field_rule(RangeRule("price", min_value=0.01))
        
        # Add trading-specific business rules
        self.add_business_rule(self._validate_trading_hours)
        self.add_business_rule(self._validate_risk_limits)
    
    def _setup_user_service_rules(self):
        """Setup User Service validation rules"""
        # User registration validation
        self.add_field_rule(RequiredRule("email"))
        self.add_field_rule(EmailRule("email"))
        
        self.add_field_rule(RequiredRule("password"))
        self.add_field_rule(LengthRule("password", min_length=8, max_length=128))
        
        self.add_field_rule(RequiredRule("username"))
        self.add_field_rule(LengthRule("username", min_length=3, max_length=50))
        self.add_field_rule(RegexRule("username", r'^[a-zA-Z0-9_]+$'))
    
    def _validate_trading_hours(self, data: Dict[str, Any], context: Dict[str, Any]) -> ValidationResult:
        """Business rule: Validate trading hours"""
        errors = []
        warnings = []
        
        # Check if market is open (simplified example)
        current_hour = datetime.utcnow().hour
        
        if current_hour < 9 or current_hour > 17:  # Simplified market hours
            warnings.append({
                "field": "trading_time",
                "message": "Trading outside normal market hours",
                "severity": "warning",
                "rule": "TradingHours"
            })
        
        return ValidationResult(
            is_valid=True,  # Just a warning
            errors=errors,
            warnings=warnings,
            field_results={}
        )
    
    def _validate_risk_limits(self, data: Dict[str, Any], context: Dict[str, Any]) -> ValidationResult:
        """Business rule: Validate risk limits"""
        errors = []
        warnings = []
        
        volume = data.get('volume', 0)
        price = data.get('price', 0)
        
        # Calculate position value
        position_value = volume * price
        
        # Check position size limits
        max_position_value = context.get('max_position_value', 100000)
        
        if position_value > max_position_value:
            errors.append({
                "field": "position_value",
                "message": f"Position value {position_value} exceeds limit {max_position_value}",
                "severity": "error",
                "rule": "RiskLimit"
            })
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            field_results={}
        )
    
    # Common validation patterns
    def validate_api_request(self, request_data: Dict[str, Any], endpoint: str) -> ValidationResult:
        """Validate API request data"""
        context = {"endpoint": endpoint, "service": self.service_name}
        return self.validate_data(request_data, context)
    
    def validate_trading_order(self, order_data: Dict[str, Any], user_context: Dict[str, Any]) -> ValidationResult:
        """Validate trading order"""
        context = {"order_type": "trading", **user_context}
        return self.validate_data(order_data, context)
    
    def validate_user_input(self, user_data: Dict[str, Any], operation: str) -> ValidationResult:
        """Validate user input"""
        context = {"operation": operation, "service": self.service_name}
        return self.validate_data(user_data, context)
    
    # Validation utilities
    def create_validation_schema(self, schema_name: str) -> Dict[str, Any]:
        """Create validation schema for documentation"""
        schema = {
            "schema_name": schema_name,
            "service": self.service_name,
            "fields": {},
            "business_rules": len(self.business_rules)
        }
        
        for field_name, rules in self.field_rules.items():
            field_info = {
                "required": any(isinstance(rule, RequiredRule) for rule in rules),
                "type": None,
                "rules": []
            }
            
            for rule in rules:
                rule_info = {
                    "type": rule.__class__.__name__,
                    "message": rule.error_message,
                    "severity": rule.severity.value
                }
                
                # Add rule-specific details
                if isinstance(rule, TypeRule):
                    field_info["type"] = rule.expected_type.__name__
                elif isinstance(rule, RangeRule):
                    rule_info["min"] = rule.min_value
                    rule_info["max"] = rule.max_value
                elif isinstance(rule, LengthRule):
                    rule_info["min_length"] = rule.min_length
                    rule_info["max_length"] = rule.max_length
                elif isinstance(rule, RegexRule):
                    rule_info["pattern"] = rule.pattern.pattern
                
                field_info["rules"].append(rule_info)
            
            schema["fields"][field_name] = field_info
        
        return schema
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        total_rules = sum(len(rules) for rules in self.field_rules.values())
        
        return {
            "service": self.service_name,
            "total_field_rules": total_rules,
            "total_business_rules": len(self.business_rules),
            "fields_with_validation": len(self.field_rules),
            "validation_cache_size": len(self.validation_cache)
        }
    
    def clear_validation_cache(self):
        """Clear validation cache"""
        self.validation_cache.clear()
    
    # Preset validation patterns
    @staticmethod
    def create_trading_validator(service_name: str) -> 'CoreValidator':
        """Create validator with trading-specific rules"""
        validator = CoreValidator(service_name)
        
        # Trading symbol rules
        validator.add_field_rule(RequiredRule("symbol"))
        validator.add_field_rule(RegexRule("symbol", r'^[A-Z]{3,6}$'))
        
        # Volume rules
        validator.add_field_rule(RequiredRule("volume"))
        validator.add_field_rule(TypeRule("volume", (int, float)))
        validator.add_field_rule(RangeRule("volume", min_value=0.01, max_value=1000000))
        
        # Price rules
        validator.add_field_rule(TypeRule("price", (int, float)))
        validator.add_field_rule(RangeRule("price", min_value=0.01))
        
        return validator
    
    @staticmethod
    def create_api_validator(service_name: str) -> 'CoreValidator':
        """Create validator with API-specific rules"""
        validator = CoreValidator(service_name)
        
        # Request validation
        validator.add_field_rule(RequiredRule("method"))
        validator.add_field_rule(TypeRule("method", str))
        
        validator.add_field_rule(RequiredRule("endpoint"))
        validator.add_field_rule(RegexRule("endpoint", r'^/[a-zA-Z0-9/_-]*$'))
        
        # Content validation
        validator.add_field_rule(TypeRule("content_type", str))
        
        return validator


# CENTRALIZED VALIDATION MANAGER - Simple singleton for all microservices
import threading

class SharedInfraValidationManager:
    """Simple centralized validation management for microservices"""
    
    _validators = {}
    _lock = threading.RLock()
    
    @classmethod
    def get_validator(cls, service_name: str, validator_type: str = "default") -> CoreValidator:
        """Get or create validator for service"""
        with cls._lock:
            key = f"{service_name}-{validator_type}"
            if key not in cls._validators:
                if validator_type == "trading":
                    cls._validators[key] = CoreValidator.create_trading_validator(service_name)
                elif validator_type == "api":
                    cls._validators[key] = CoreValidator.create_api_validator(service_name)
                else:
                    cls._validators[key] = CoreValidator(service_name)
            return cls._validators[key]
    
    @classmethod
    def validate_data(cls, service_name: str, data: Dict[str, Any], validator_type: str = "default", **kwargs):
        """Validate data for service"""
        validator = cls.get_validator(service_name, validator_type)
        return validator.validate_data(data, **kwargs)
    
    @classmethod
    def validate_trading_data(cls, service_name: str, data: Dict[str, Any], **kwargs):
        """Validate trading data for service"""
        validator = cls.get_validator(service_name, "trading")
        return validator.validate_data(data, **kwargs)
    
    @classmethod
    def get_all_validators(cls):
        """Get all managed validators"""
        return cls._validators.copy()


# Simple convenience functions
def get_validator(service_name: str, validator_type: str = "default") -> CoreValidator:
    """Get validator for service"""
    return SharedInfraValidationManager.get_validator(service_name, validator_type)

def validate_data(service_name: str, data: Dict[str, Any], validator_type: str = "default", **kwargs):
    """Validate data for service"""
    return SharedInfraValidationManager.validate_data(service_name, data, validator_type, **kwargs)

def validate_trading_data(service_name: str, data: Dict[str, Any], **kwargs):
    """Validate trading data for service"""
    return SharedInfraValidationManager.validate_trading_data(service_name, data, **kwargs)

# Quick validation functions  
def validate_trading_symbol(service_name: str, symbol: str) -> ValidationResult:
    """Quick trading symbol validation"""
    validator = get_validator(service_name, "trading")
    return validator.validate_field("symbol", symbol)

def validate_trading_price(service_name: str, price: Union[str, float, int]) -> ValidationResult:
    """Quick trading price validation"""
    validator = get_validator(service_name, "trading")
    return validator.validate_field("price", price)

def validate_trading_volume(service_name: str, volume: Union[str, float, int]) -> ValidationResult:
    """Quick trading volume validation"""
    validator = get_validator(service_name, "trading")
    return validator.validate_field("volume", volume)