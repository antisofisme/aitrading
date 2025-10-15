"""
validator.py - Data Validation System

🎯 PURPOSE:
Business: Comprehensive data validation for trading operations and user inputs
Technical: Schema-based validation with custom rules and error reporting
Domain: Data Validation/Input Verification/System Safety

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:27.849Z
Session: client-side-ai-brain-full-compliance
Confidence: 92%
Complexity: medium

🧩 PATTERNS USED:
- AI_BRAIN_VALIDATION_SYSTEM: Comprehensive validation with custom rules
- SCHEMA_BASED_VALIDATION: JSON schema validation for structured data

📦 DEPENDENCIES:
Internal: logger_manager, error_manager
External: jsonschema, typing, dataclasses, decimal

💡 AI DECISION REASONING:
Trading systems require strict data validation to prevent errors and financial losses. Schema-based approach ensures consistency and reliability.

🚀 USAGE:
validator.validate_trade_data({"symbol": "EURUSD", "volume": 1.0})

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

import re
import json
from typing import Dict, Any, Optional, List, Union, Callable, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
import threading
from enum import Enum
from collections import defaultdict

class ValidationLevel(Enum):
    """Validation levels"""
    STRICT = "strict"      # All validations must pass
    NORMAL = "normal"      # Most validations must pass
    LENIENT = "lenient"    # Basic validations only
    BYPASS = "bypass"      # Skip validation (for testing)

class ValidationResult(Enum):
    """Validation result status"""
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"
    SKIPPED = "skipped"

@dataclass
class ValidationError:
    """Validation error details"""
    field: str
    value: Any
    rule: str
    message: str
    severity: str = "error"
    context: Dict[str, Any] = None

    def __post_init__(self):
        if self.context is None:
            self.context = {}

@dataclass
class ValidationReport:
    """Validation report with detailed results"""
    is_valid: bool
    result: ValidationResult
    errors: List[ValidationError]
    warnings: List[ValidationError]
    validated_fields: List[str]
    timestamp: datetime
    validation_time_ms: float
    context: Dict[str, Any] = None

    def __post_init__(self):
        if self.context is None:
            self.context = {}

class ClientValidator:
    """
    Client-Side Centralized Validator
    Manages all validation rules and business logic for MT5 Trading Client
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        self.validation_rules: Dict[str, Dict[str, Any]] = {}
        self.custom_validators: Dict[str, Callable] = {}
        self.cached_patterns: Dict[str, re.Pattern] = {}
        self.validation_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.validation_level = ValidationLevel.NORMAL
        
        # Setup default validation rules
        self._setup_default_rules()
        self._setup_mt5_rules()
        self._setup_trading_rules()
    
    @classmethod
    def get_instance(cls) -> 'ClientValidator':
        """Singleton pattern with thread safety"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def _setup_default_rules(self):
        """Setup default validation rules"""
        self.validation_rules.update({
            # Basic data types
            'string': {
                'type': str,
                'min_length': 0,
                'max_length': 1000,
                'allow_empty': True,
                'strip_whitespace': True
            },
            'integer': {
                'type': int,
                'min_value': None,
                'max_value': None
            },
            'float': {
                'type': float,
                'min_value': None,
                'max_value': None,
                'decimal_places': None
            },
            'boolean': {
                'type': bool
            },
            'datetime': {
                'type': datetime,
                'format': '%Y-%m-%d %H:%M:%S',
                'allow_future': True,
                'allow_past': True
            },
            'email': {
                'type': str,
                'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                'max_length': 254
            },
            'url': {
                'type': str,
                'pattern': r'^https?://[^\s/$.?#].[^\s]*$',
                'max_length': 2000
            }
        })
    
    def _setup_mt5_rules(self):
        """Setup MT5-specific validation rules"""
        self.validation_rules.update({
            # MT5 Account
            'mt5_login': {
                'type': int,
                'min_value': 1,
                'max_value': 999999999,
                'required': True
            },
            'mt5_server': {
                'type': str,
                'pattern': r'^[a-zA-Z0-9.-]+$',
                'min_length': 3,
                'max_length': 100,
                'required': True
            },
            'mt5_password': {
                'type': str,
                'min_length': 4,
                'max_length': 50,
                'required': True,
                'sensitive': True  # Don't log actual value
            },
            
            # MT5 Symbols
            'mt5_symbol': {
                'type': str,
                'pattern': r'^[A-Z]{6}$|^[A-Z]{3}[A-Z]{3}$|^[A-Z]+[0-9]*$',
                'min_length': 3,
                'max_length': 20,
                'examples': ['EURUSD', 'GBPJPY', 'US30', 'XAUUSD']
            },
            
            # MT5 Timeframes
            'mt5_timeframe': {
                'type': str,
                'allowed_values': ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1', 'W1', 'MN1'],
                'case_sensitive': True
            },
            
            # MT5 Trade Types
            'mt5_trade_type': {
                'type': int,
                'allowed_values': [0, 1],  # 0=BUY, 1=SELL
                'description': '0=BUY, 1=SELL'
            },
            
            # MT5 Order Types
            'mt5_order_type': {
                'type': int,
                'allowed_values': [0, 1, 2, 3, 4, 5],  # ORDER_TYPE_*
                'description': 'MT5 order type constants'
            }
        })
    
    def _setup_trading_rules(self):
        """Setup trading-specific validation rules"""
        self.validation_rules.update({
            # Trading Volume (for actual trades)
            'trading_volume': {
                'type': float,
                'min_value': 0.01,
                'max_value': 100.0,
                'decimal_places': 2,
                'step': 0.01
            },
            
            # Tick Data Volume (can be 0 for market data)
            'tick_volume': {
                'type': float,
                'min_value': 0.0,  # Can be 0 for tick data
                'max_value': 10000000.0,
                'decimal_places': 2,
                'allow_zero': True
            },
            
            # Trading Price (for actual trades)
            'trading_price': {
                'type': float,
                'min_value': 0.00001,
                'max_value': 1000000.0,
                'decimal_places': 5
            },
            
            # Tick Price (can be 0 for market data when no price available)
            'tick_price': {
                'type': float,
                'min_value': 0.0,  # Can be 0 for tick data
                'max_value': 1000000.0,
                'decimal_places': 5,
                'allow_zero': True
            },
            
            # Stop Loss / Take Profit
            'sl_tp_price': {
                'type': float,
                'min_value': 0.0,
                'max_value': 1000000.0,
                'decimal_places': 5,
                'allow_zero': True  # 0 means no SL/TP
            },
            
            # Risk Percentage
            'risk_percentage': {
                'type': float,
                'min_value': 0.1,
                'max_value': 10.0,
                'decimal_places': 2,
                'warning_threshold': 5.0  # Warn if > 5%
            },
            
            # Account Balance
            'account_balance': {
                'type': float,
                'min_value': 0.0,
                'max_value': 1000000000.0,
                'decimal_places': 2
            },
            
            # WebSocket URL
            'websocket_url': {
                'type': str,
                'pattern': r'^wss?://[^\s/$.?#].[^\s]*$',
                'max_length': 500,
                'required': True
            },
            
            # Kafka Topic
            'kafka_topic': {
                'type': str,
                'pattern': r'^[a-zA-Z0-9._-]+$',
                'min_length': 1,
                'max_length': 249,
                'required': True
            }
        })
    
    def validate_field(self, field_name: str, value: Any, 
                      rule_name: Optional[str] = None,
                      context: Optional[Dict[str, Any]] = None) -> ValidationReport:
        """
        Validate single field with specified rule
        
        Args:
            field_name: Name of the field being validated
            value: Value to validate
            rule_name: Validation rule to use (defaults to field_name)
            context: Additional context for validation
            
        Returns:
            ValidationReport with validation results
        """
        start_time = datetime.now()
        errors = []
        warnings = []
        
        # Skip validation if level is BYPASS
        if self.validation_level == ValidationLevel.BYPASS:
            return ValidationReport(
                is_valid=True,
                result=ValidationResult.SKIPPED,
                errors=[],
                warnings=[],
                validated_fields=[field_name],
                timestamp=start_time,
                validation_time_ms=0.0,
                context=context or {}
            )
        
        # Determine rule to use
        rule_key = rule_name or field_name
        if rule_key not in self.validation_rules:
            # Try to infer rule from field name patterns
            rule_key = self._infer_rule_from_field_name(field_name)
        
        if rule_key not in self.validation_rules:
            errors.append(ValidationError(
                field=field_name,
                value=value,
                rule='unknown',
                message=f"No validation rule found for field '{field_name}'"
            ))
        else:
            # Apply validation rule
            rule = self.validation_rules[rule_key]
            field_errors, field_warnings = self._apply_rule(field_name, value, rule)
            errors.extend(field_errors)
            warnings.extend(field_warnings)
        
        # Check custom validators
        if field_name in self.custom_validators:
            try:
                custom_result = self.custom_validators[field_name](value, context)
                if not custom_result:
                    errors.append(ValidationError(
                        field=field_name,
                        value=value,
                        rule='custom',
                        message=f"Custom validation failed for field '{field_name}'"
                    ))
            except Exception as e:
                errors.append(ValidationError(
                    field=field_name,
                    value=value,
                    rule='custom',
                    message=f"Custom validator error: {str(e)}"
                ))
        
        # Determine final result
        is_valid = len(errors) == 0
        if is_valid and len(warnings) == 0:
            result = ValidationResult.VALID
        elif is_valid and len(warnings) > 0:
            result = ValidationResult.WARNING
        else:
            result = ValidationResult.INVALID
        
        # Update statistics
        self.validation_stats[rule_key]['total'] += 1
        self.validation_stats[rule_key][result.value] += 1
        
        end_time = datetime.now()
        validation_time = (end_time - start_time).total_seconds() * 1000
        
        return ValidationReport(
            is_valid=is_valid,
            result=result,
            errors=errors,
            warnings=warnings,
            validated_fields=[field_name],
            timestamp=start_time,
            validation_time_ms=validation_time,
            context=context or {}
        )
    
    def validate_dict(self, data: Dict[str, Any], 
                     rule_mapping: Optional[Dict[str, str]] = None,
                     context: Optional[Dict[str, Any]] = None) -> ValidationReport:
        """
        Validate dictionary of fields
        
        Args:
            data: Dictionary to validate
            rule_mapping: Field name to rule name mapping
            context: Additional context for validation
            
        Returns:
            ValidationReport with combined results
        """
        start_time = datetime.now()
        all_errors = []
        all_warnings = []
        validated_fields = []
        
        rule_mapping = rule_mapping or {}
        
        for field_name, value in data.items():
            rule_name = rule_mapping.get(field_name)
            report = self.validate_field(field_name, value, rule_name, context)
            
            all_errors.extend(report.errors)
            all_warnings.extend(report.warnings)
            validated_fields.extend(report.validated_fields)
        
        # Overall validation result
        is_valid = len(all_errors) == 0
        if is_valid and len(all_warnings) == 0:
            result = ValidationResult.VALID
        elif is_valid and len(all_warnings) > 0:
            result = ValidationResult.WARNING
        else:
            result = ValidationResult.INVALID
        
        end_time = datetime.now()
        validation_time = (end_time - start_time).total_seconds() * 1000
        
        return ValidationReport(
            is_valid=is_valid,
            result=result,
            errors=all_errors,
            warnings=all_warnings,
            validated_fields=validated_fields,
            timestamp=start_time,
            validation_time_ms=validation_time,
            context=context or {}
        )
    
    def _apply_rule(self, field_name: str, value: Any, 
                   rule: Dict[str, Any]) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Apply validation rule to value"""
        errors = []
        warnings = []
        
        # Check required
        if rule.get('required', False) and (value is None or value == ''):
            errors.append(ValidationError(
                field=field_name,
                value=value,
                rule='required',
                message=f"Field '{field_name}' is required"
            ))
            return errors, warnings
        
        # Skip further validation if value is None/empty and not required
        if value is None or value == '':
            return errors, warnings
        
        # Type validation
        expected_type = rule.get('type')
        if expected_type and not isinstance(value, expected_type):
            # Try type conversion for basic types
            if expected_type in [int, float, str]:
                try:
                    if expected_type == int:
                        value = int(value)
                    elif expected_type == float:
                        value = float(value)
                    elif expected_type == str:
                        value = str(value)
                except (ValueError, TypeError):
                    errors.append(ValidationError(
                        field=field_name,
                        value=value,
                        rule='type',
                        message=f"Field '{field_name}' must be of type {expected_type.__name__}"
                    ))
                    return errors, warnings
            else:
                errors.append(ValidationError(
                    field=field_name,
                    value=value,
                    rule='type',
                    message=f"Field '{field_name}' must be of type {expected_type.__name__}"
                ))
                return errors, warnings
        
        # String validations
        if isinstance(value, str):
            if rule.get('strip_whitespace', False):
                value = value.strip()
            
            min_length = rule.get('min_length')
            if min_length is not None and len(value) < min_length:
                errors.append(ValidationError(
                    field=field_name,
                    value=value,
                    rule='min_length',
                    message=f"Field '{field_name}' must be at least {min_length} characters"
                ))
            
            max_length = rule.get('max_length')
            if max_length is not None and len(value) > max_length:
                errors.append(ValidationError(
                    field=field_name,
                    value=value,
                    rule='max_length',
                    message=f"Field '{field_name}' must be at most {max_length} characters"
                ))
            
            # Pattern validation
            pattern = rule.get('pattern')
            if pattern:
                if pattern not in self.cached_patterns:
                    self.cached_patterns[pattern] = re.compile(pattern)
                
                regex = self.cached_patterns[pattern]
                if not regex.match(value):
                    examples = rule.get('examples', [])
                    example_text = f" Examples: {', '.join(examples[:3])}" if examples else ""
                    errors.append(ValidationError(
                        field=field_name,
                        value=value,
                        rule='pattern',
                        message=f"Field '{field_name}' format is invalid.{example_text}"
                    ))
        
        # Numeric validations
        if isinstance(value, (int, float)):
            min_value = rule.get('min_value')
            if min_value is not None and value < min_value:
                errors.append(ValidationError(
                    field=field_name,
                    value=value,
                    rule='min_value',
                    message=f"Field '{field_name}' must be at least {min_value}"
                ))
            
            max_value = rule.get('max_value')
            if max_value is not None and value > max_value:
                errors.append(ValidationError(
                    field=field_name,
                    value=value,
                    rule='max_value',
                    message=f"Field '{field_name}' must be at most {max_value}"
                ))
            
            # Warning threshold
            warning_threshold = rule.get('warning_threshold')
            if warning_threshold is not None and value > warning_threshold:
                warnings.append(ValidationError(
                    field=field_name,
                    value=value,
                    rule='warning_threshold',
                    message=f"Field '{field_name}' value {value} exceeds recommended threshold {warning_threshold}",
                    severity='warning'
                ))
        
        # Allowed values validation
        allowed_values = rule.get('allowed_values')
        if allowed_values is not None and value not in allowed_values:
            errors.append(ValidationError(
                field=field_name,
                value=value,
                rule='allowed_values',
                message=f"Field '{field_name}' must be one of: {', '.join(map(str, allowed_values))}"
            ))
        
        return errors, warnings
    
    def _infer_rule_from_field_name(self, field_name: str) -> str:
        """Infer validation rule from field name patterns"""
        field_lower = field_name.lower()
        
        # MT5 patterns
        if 'login' in field_lower or 'account' in field_lower:
            return 'mt5_login'
        elif 'server' in field_lower:
            return 'mt5_server'
        elif 'symbol' in field_lower:
            return 'mt5_symbol'
        elif 'timeframe' in field_lower:
            return 'mt5_timeframe'
        elif 'volume' in field_lower:
            # Context-aware volume validation
            # Check if this is tick data volume or trading volume
            if any(pattern in field_lower for pattern in ['tick', 'market', 'quote', 'feed']):
                return 'tick_volume'
            else:
                return 'trading_volume'
        elif field_lower in ['bid', 'ask', 'last']:
            # Direct tick price fields
            return 'tick_price'
        elif 'price' in field_lower:
            # Context-aware price validation
            # Check if this is tick data price or trading price
            if any(pattern in field_lower for pattern in ['tick', 'market', 'quote', 'feed', 'bid', 'ask', 'last']):
                return 'tick_price'
            else:
                return 'trading_price'
        elif 'balance' in field_lower:
            return 'account_balance'
        elif 'url' in field_lower and 'ws' in field_lower:
            return 'websocket_url'
        elif 'topic' in field_lower:
            return 'kafka_topic'
        elif 'email' in field_lower:
            return 'email'
        elif 'url' in field_lower:
            return 'url'
        
        # Default to string
        return 'string'
    
    def add_custom_validator(self, field_name: str, validator: Callable[[Any, Optional[Dict[str, Any]]], bool]):
        """Add custom validator function"""
        self.custom_validators[field_name] = validator
    
    def add_validation_rule(self, rule_name: str, rule: Dict[str, Any]):
        """Add new validation rule"""
        self.validation_rules[rule_name] = rule
    
    def set_validation_level(self, level: ValidationLevel):
        """Set validation level"""
        self.validation_level = level
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation statistics"""
        return {
            'total_rules': len(self.validation_rules),
            'custom_validators': len(self.custom_validators),
            'cached_patterns': len(self.cached_patterns),
            'validation_level': self.validation_level.value,
            'rule_stats': dict(self.validation_stats)
        }
    
    def clear_statistics(self):
        """Clear validation statistics"""
        self.validation_stats.clear()
    
    # Convenience methods for common validations
    def validate_mt5_connection(self, login: int, server: str, password: str) -> ValidationReport:
        """Validate MT5 connection parameters"""
        return self.validate_dict({
            'login': login,
            'server': server,
            'password': password
        }, {
            'login': 'your_mt5_login',
            'server': 'your_mt5_server',
            'password': 'your_mt5_password_here'
        })
    
    def validate_trading_symbol(self, symbol: str, context: Optional[Dict[str, Any]] = None) -> ValidationReport:
        """Validate trading symbol"""
        return self.validate_field('symbol', symbol, 'mt5_symbol', context)
    
    def validate_trade_params(self, symbol: str, volume: float, price: float, 
                            trade_type: int) -> ValidationReport:
        """Validate trade parameters"""
        return self.validate_dict({
            'symbol': symbol,
            'volume': volume,
            'price': price,
            'trade_type': trade_type
        }, {
            'symbol': 'mt5_symbol',
            'volume': 'trading_volume',
            'price': 'trading_price',
            'trade_type': 'mt5_trade_type'
        })
    
    def validate_websocket_config(self, url: str, timeout: int = None) -> ValidationReport:
        """Validate WebSocket configuration"""
        data = {'url': url}
        rules = {'url': 'websocket_url'}
        
        if timeout is not None:
            data['timeout'] = timeout
            rules['timeout'] = 'integer'
        
        return self.validate_dict(data, rules)
    
    def validate_tick_data(self, symbol: str, bid: float, ask: float, last: float = None, 
                          volume: float = None, context: Optional[Dict[str, Any]] = None) -> ValidationReport:
        """Validate tick data with correct volume and price rules"""
        data = {
            'symbol': symbol,
            'bid': bid,
            'ask': ask
        }
        rules = {
            'symbol': 'mt5_symbol',
            'bid': 'tick_price',  # Use tick_price for market data
            'ask': 'tick_price'   # Use tick_price for market data
        }
        
        if last is not None:
            data['last'] = last
            rules['last'] = 'tick_price'  # Use tick_price to allow last=0
            
        if volume is not None:
            data['volume'] = volume
            rules['volume'] = 'tick_volume'  # Use tick_volume rule for tick data
        
        return self.validate_dict(data, rules, context)


# Global instance
client_validator = ClientValidator.get_instance()

# Convenience functions
def validate_field(field_name: str, value: Any, rule_name: Optional[str] = None,
                  context: Optional[Dict[str, Any]] = None) -> ValidationReport:
    """Validate single field"""
    return client_validator.validate_field(field_name, value, rule_name, context)

def validate_dict(data: Dict[str, Any], rule_mapping: Optional[Dict[str, str]] = None,
                 context: Optional[Dict[str, Any]] = None) -> ValidationReport:
    """Validate dictionary"""
    return client_validator.validate_dict(data, rule_mapping, context)

def validate_mt5_connection(login: int, server: str, password: str) -> ValidationReport:
    """Validate MT5 connection parameters"""
    return client_validator.validate_mt5_connection(login, server, password)

def validate_trading_symbol(symbol: str, context: Optional[Dict[str, Any]] = None) -> ValidationReport:
    """Validate trading symbol"""
    return client_validator.validate_trading_symbol(symbol, context)

def validate_tick_data(symbol: str, bid: float, ask: float, last: float = None, 
                      volume: float = None, context: Optional[Dict[str, Any]] = None) -> ValidationReport:
    """Validate tick data with correct volume and price rules (allows last=0 and volume=0)"""
    return client_validator.validate_tick_data(symbol, bid, ask, last, volume, context)

def get_validation_stats() -> Dict[str, Any]:
    """Get validation statistics"""
    return client_validator.get_validation_statistics()