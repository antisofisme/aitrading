"""
Input Validation and Sanitization - Enterprise security validation
Comprehensive input validation, sanitization, and XSS protection
"""

import re
import html
import urllib.parse
import json
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pydantic import BaseModel, Field, validator, EmailStr
from fastapi import HTTPException, Request
import bleach
import ipaddress

class SecurityValidationError(Exception):
    """Custom exception for security validation errors"""
    pass

class InputSanitizer:
    """
    Comprehensive input sanitization for XSS and injection prevention
    """
    
    # XSS patterns to detect and remove
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>',
        r'<form[^>]*>.*?</form>',
        r'<meta[^>]*http-equiv[^>]*refresh[^>]*>',
    ]
    
    # SQL injection patterns
    SQL_PATTERNS = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)',
        r'(--|#|/\*|\*/)',
        r'(\bOR\b.*=.*\bOR\b)',
        r'(\bAND\b.*=.*\bAND\b)',
        r'(;.*--)',
        r'(\b(EXEC|EXECUTE)\b\s*\()',
    ]
    
    # Command injection patterns
    COMMAND_PATTERNS = [
        r'[;&|`$(){}\[\]<>]',
        r'(\b(eval|exec|system|shell_exec|passthru|proc_open|popen)\b)',
        r'(\$\w+)',
        r'(`.*`)',
    ]
    
    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r'\.\./',
        r'\.\.\\',
        r'%2e%2e%2f',
        r'%2e%2e%5c',
        r'..%2f',
        r'..%5c',
    ]
    
    def __init__(self):
        # Configure bleach for HTML sanitization
        self.allowed_tags = [
            'p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote'
        ]
        
        self.allowed_attributes = {
            '*': ['class'],
            'a': ['href', 'title'],
            'img': ['src', 'alt', 'width', 'height'],
        }
        
        self.allowed_protocols = ['http', 'https', 'mailto']
    
    def sanitize_html(self, input_text: str, strict: bool = True) -> str:
        """Sanitize HTML content to prevent XSS attacks"""
        if not isinstance(input_text, str):
            return str(input_text)
        
        if strict:
            # Strip all HTML tags
            return bleach.clean(input_text, tags=[], attributes={}, strip=True)
        else:
            # Allow safe HTML tags
            return bleach.clean(
                input_text,
                tags=self.allowed_tags,
                attributes=self.allowed_attributes,
                protocols=self.allowed_protocols,
                strip=True
            )
    
    def detect_xss(self, input_text: str) -> bool:
        """Detect potential XSS attacks"""
        if not isinstance(input_text, str):
            return False
        
        # Convert to lowercase for pattern matching
        text_lower = input_text.lower()
        
        # Check for XSS patterns
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL):
                return True
        
        return False
    
    def detect_sql_injection(self, input_text: str) -> bool:
        """Detect potential SQL injection attacks"""
        if not isinstance(input_text, str):
            return False
        
        # Check for SQL injection patterns
        for pattern in self.SQL_PATTERNS:
            if re.search(pattern, input_text, re.IGNORECASE):
                return True
        
        return False
    
    def detect_command_injection(self, input_text: str) -> bool:
        """Detect potential command injection attacks"""
        if not isinstance(input_text, str):
            return False
        
        # Check for command injection patterns
        for pattern in self.COMMAND_PATTERNS:
            if re.search(pattern, input_text, re.IGNORECASE):
                return True
        
        return False
    
    def detect_path_traversal(self, input_text: str) -> bool:
        """Detect potential path traversal attacks"""
        if not isinstance(input_text, str):
            return False
        
        # Check for path traversal patterns
        for pattern in self.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, input_text, re.IGNORECASE):
                return True
        
        return False
    
    def sanitize_string(
        self, 
        input_text: str, 
        max_length: int = 1000, 
        allow_html: bool = False,
        strict_validation: bool = True
    ) -> str:
        """Comprehensive string sanitization"""
        if not isinstance(input_text, str):
            input_text = str(input_text)
        
        # Length validation
        if len(input_text) > max_length:
            raise SecurityValidationError(f"Input exceeds maximum length of {max_length}")
        
        # Security pattern detection
        if strict_validation:
            if self.detect_xss(input_text):
                raise SecurityValidationError("Potential XSS attack detected")
            
            if self.detect_sql_injection(input_text):
                raise SecurityValidationError("Potential SQL injection detected")
            
            if self.detect_command_injection(input_text):
                raise SecurityValidationError("Potential command injection detected")
            
            if self.detect_path_traversal(input_text):
                raise SecurityValidationError("Potential path traversal detected")
        
        # HTML sanitization
        if allow_html:
            sanitized = self.sanitize_html(input_text, strict=False)
        else:
            sanitized = self.sanitize_html(input_text, strict=True)
        
        # URL decode to catch encoded attacks
        try:
            decoded = urllib.parse.unquote(sanitized)
            if decoded != sanitized:
                # Re-check decoded content
                if strict_validation and (
                    self.detect_xss(decoded) or 
                    self.detect_sql_injection(decoded) or
                    self.detect_command_injection(decoded)
                ):
                    raise SecurityValidationError("Potential attack in URL-encoded content")
        except Exception:
            pass  # If URL decoding fails, continue with original
        
        return sanitized.strip()
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal and other attacks"""
        if not isinstance(filename, str):
            filename = str(filename)
        
        # Remove path components
        filename = filename.split('/')[-1].split('\\')[-1]
        
        # Remove dangerous characters
        filename = re.sub(r'[<>:"|?*\x00-\x1f]', '', filename)
        
        # Remove leading/trailing dots and spaces
        filename = filename.strip('. ')
        
        # Prevent reserved names (Windows)
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL'] + [f'COM{i}' for i in range(1, 10)] + [f'LPT{i}' for i in range(1, 10)]
        if filename.upper() in reserved_names:
            filename = f"_{filename}"
        
        # Ensure minimum length
        if len(filename) == 0:
            filename = "unnamed_file"
        
        return filename[:255]  # Limit to 255 characters

class SecureValidator:
    """
    Secure validation for different data types with security checks
    """
    
    def __init__(self):
        self.sanitizer = InputSanitizer()
    
    def validate_email(self, email: str) -> str:
        """Validate and sanitize email address"""
        if not isinstance(email, str):
            raise SecurityValidationError("Email must be a string")
        
        email = email.strip().lower()
        
        # Length check
        if len(email) > 254:
            raise SecurityValidationError("Email address too long")
        
        # Basic format validation
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise SecurityValidationError("Invalid email format")
        
        # Check for security patterns
        if (self.sanitizer.detect_xss(email) or 
            self.sanitizer.detect_sql_injection(email) or
            self.sanitizer.detect_command_injection(email)):
            raise SecurityValidationError("Email contains suspicious content")
        
        return email
    
    def validate_username(self, username: str) -> str:
        """Validate and sanitize username"""
        if not isinstance(username, str):
            raise SecurityValidationError("Username must be a string")
        
        username = username.strip()
        
        # Length validation
        if len(username) < 3 or len(username) > 50:
            raise SecurityValidationError("Username must be between 3 and 50 characters")
        
        # Format validation (alphanumeric, underscore, dash)
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise SecurityValidationError("Username can only contain letters, numbers, underscore, and dash")
        
        # Security checks
        username = self.sanitizer.sanitize_string(username, max_length=50, strict_validation=True)
        
        return username
    
    def validate_password(self, password: str, min_length: int = 8) -> str:
        """Validate password strength"""
        if not isinstance(password, str):
            raise SecurityValidationError("Password must be a string")
        
        # Length check
        if len(password) < min_length:
            raise SecurityValidationError(f"Password must be at least {min_length} characters")
        
        if len(password) > 128:
            raise SecurityValidationError("Password too long")
        
        # Strength checks
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        
        strength_score = sum([has_upper, has_lower, has_digit, has_special])
        
        if strength_score < 3:
            raise SecurityValidationError(
                "Password must contain at least 3 of: uppercase, lowercase, digit, special character"
            )
        
        # Check for common patterns
        if re.search(r'(.)\1{2,}', password):  # Repeated characters
            raise SecurityValidationError("Password contains too many repeated characters")
        
        if re.search(r'(012|123|234|345|456|567|678|789|890)', password):
            raise SecurityValidationError("Password contains sequential numbers")
        
        if re.search(r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', password.lower()):
            raise SecurityValidationError("Password contains sequential letters")
        
        return password
    
    def validate_phone(self, phone: str) -> str:
        """Validate and sanitize phone number"""
        if not isinstance(phone, str):
            raise SecurityValidationError("Phone must be a string")
        
        # Remove all non-digit characters except +
        phone = re.sub(r'[^\d+]', '', phone)
        
        # Length validation (international format)
        if len(phone) < 7 or len(phone) > 15:
            raise SecurityValidationError("Invalid phone number length")
        
        # Format validation
        if not re.match(r'^\+?[\d]{7,15}$', phone):
            raise SecurityValidationError("Invalid phone number format")
        
        return phone
    
    def validate_url(self, url: str, allowed_schemes: List[str] = None) -> str:
        """Validate and sanitize URL"""
        if not isinstance(url, str):
            raise SecurityValidationError("URL must be a string")
        
        if allowed_schemes is None:
            allowed_schemes = ['http', 'https']
        
        url = url.strip()
        
        # Length check
        if len(url) > 2048:
            raise SecurityValidationError("URL too long")
        
        # Basic format validation
        if not re.match(r'^https?://', url, re.IGNORECASE):
            raise SecurityValidationError("URL must start with http:// or https://")
        
        # Parse URL
        try:
            parsed = urllib.parse.urlparse(url)
        except Exception:
            raise SecurityValidationError("Invalid URL format")
        
        # Validate scheme
        if parsed.scheme.lower() not in allowed_schemes:
            raise SecurityValidationError(f"URL scheme must be one of: {', '.join(allowed_schemes)}")
        
        # Check for suspicious patterns
        if (self.sanitizer.detect_xss(url) or 
            self.sanitizer.detect_command_injection(url)):
            raise SecurityValidationError("URL contains suspicious content")
        
        return url
    
    def validate_ip_address(self, ip: str) -> str:
        """Validate IP address"""
        if not isinstance(ip, str):
            raise SecurityValidationError("IP address must be a string")
        
        ip = ip.strip()
        
        try:
            # This will validate both IPv4 and IPv6
            ipaddress.ip_address(ip)
            return ip
        except ipaddress.AddressValueError:
            raise SecurityValidationError("Invalid IP address format")
    
    def validate_json(self, json_str: str, max_depth: int = 10, max_length: int = 10000) -> dict:
        """Validate and parse JSON with security checks"""
        if not isinstance(json_str, str):
            raise SecurityValidationError("JSON must be a string")
        
        # Length check
        if len(json_str) > max_length:
            raise SecurityValidationError(f"JSON exceeds maximum length of {max_length}")
        
        # Security pattern check
        if (self.sanitizer.detect_xss(json_str) or 
            self.sanitizer.detect_sql_injection(json_str) or
            self.sanitizer.detect_command_injection(json_str)):
            raise SecurityValidationError("JSON contains suspicious content")
        
        try:
            # Parse JSON
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise SecurityValidationError(f"Invalid JSON format: {str(e)}")
        
        # Check depth to prevent deeply nested attacks
        def check_depth(obj, depth=0):
            if depth > max_depth:
                raise SecurityValidationError(f"JSON exceeds maximum depth of {max_depth}")
            
            if isinstance(obj, dict):
                for value in obj.values():
                    check_depth(value, depth + 1)
            elif isinstance(obj, list):
                for item in obj:
                    check_depth(item, depth + 1)
        
        check_depth(data)
        
        return data
    
    def validate_decimal(self, value: Union[str, int, float], max_digits: int = 18, decimal_places: int = 8) -> Decimal:
        """Validate and convert to secure decimal"""
        try:
            if isinstance(value, str):
                # Check for suspicious content in string numbers
                if not re.match(r'^-?\d+(\.\d+)?$', value.strip()):
                    raise SecurityValidationError("Invalid decimal format")
                value = value.strip()
            
            decimal_value = Decimal(str(value))
            
            # Check decimal places
            if decimal_value.as_tuple().exponent < -decimal_places:
                raise SecurityValidationError(f"Too many decimal places (max {decimal_places})")
            
            # Check total digits
            digits = len(decimal_value.as_tuple().digits)
            if digits > max_digits:
                raise SecurityValidationError(f"Too many digits (max {max_digits})")
            
            return decimal_value
            
        except (InvalidOperation, ValueError) as e:
            raise SecurityValidationError(f"Invalid decimal value: {str(e)}")

# Pydantic models with security validation
class SecureBaseModel(BaseModel):
    """Base model with security validation"""
    
    class Config:
        # Prevent extra fields to avoid potential attacks
        extra = "forbid"
        # Validate assignment to prevent bypassing validation
        validate_assignment = True
        # Use enum values for better security
        use_enum_values = True

class SecureUserInput(SecureBaseModel):
    """Secure user input model"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(..., max_length=254)
    full_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    
    @validator('username')
    def validate_username(cls, v):
        validator = SecureValidator()
        return validator.validate_username(v)
    
    @validator('full_name')
    def validate_full_name(cls, v):
        sanitizer = InputSanitizer()
        return sanitizer.sanitize_string(v, max_length=100, allow_html=False)
    
    @validator('phone')
    def validate_phone(cls, v):
        if v is None:
            return v
        validator = SecureValidator()
        return validator.validate_phone(v)

class ValidationMiddleware:
    """Middleware for input validation and sanitization"""
    
    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self.sanitizer = InputSanitizer()
        self.validator = SecureValidator()
    
    async def __call__(self, request: Request, call_next: Callable):
        """Validation middleware handler"""
        
        # Skip validation for certain endpoints
        if self._should_skip_validation(request):
            return await call_next(request)
        
        # Validate request
        await self._validate_request(request)
        
        # Process request
        response = await call_next(request)
        
        return response
    
    def _should_skip_validation(self, request: Request) -> bool:
        """Check if validation should be skipped for this request"""
        skip_paths = ["/health", "/docs", "/openapi.json", "/favicon.ico"]
        return any(skip_path in request.url.path for skip_path in skip_paths)
    
    async def _validate_request(self, request: Request):
        """Validate incoming request"""
        
        # Validate headers
        for header_name, header_value in request.headers.items():
            if len(header_value) > 8192:  # Max header length
                raise HTTPException(status_code=400, detail="Header too long")
            
            # Check for suspicious patterns in headers
            if self.strict_mode:
                if (self.sanitizer.detect_xss(header_value) or
                    self.sanitizer.detect_sql_injection(header_value) or
                    self.sanitizer.detect_command_injection(header_value)):
                    raise HTTPException(status_code=400, detail="Suspicious content in headers")
        
        # Validate URL path
        path = request.url.path
        if len(path) > 2048:
            raise HTTPException(status_code=400, detail="URL path too long")
        
        if self.strict_mode:
            if (self.sanitizer.detect_path_traversal(path) or
                self.sanitizer.detect_xss(path) or
                self.sanitizer.detect_command_injection(path)):
                raise HTTPException(status_code=400, detail="Suspicious content in URL path")
        
        # Validate query parameters
        for param_name, param_value in request.query_params.items():
            if len(param_value) > 2048:
                raise HTTPException(status_code=400, detail="Query parameter too long")
            
            if self.strict_mode:
                if (self.sanitizer.detect_xss(param_value) or
                    self.sanitizer.detect_sql_injection(param_value) or
                    self.sanitizer.detect_command_injection(param_value)):
                    raise HTTPException(status_code=400, detail="Suspicious content in query parameters")

def create_validation_middleware(strict_mode: bool = True) -> ValidationMiddleware:
    """Create validation middleware"""
    return ValidationMiddleware(strict_mode=strict_mode)