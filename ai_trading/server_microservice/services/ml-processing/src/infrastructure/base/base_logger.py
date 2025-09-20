"""
Base Logger Interface - Abstract class for service-specific loggers
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum

class LogLevel(Enum):
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    PERFORMANCE = "PERFORMANCE"
    INFO = "INFO"
    TRADING = "TRADING"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class BaseLogger(ABC):
    """Abstract base class for all service loggers"""
    
    def __init__(self, service_name: str, service_id: str = None):
        self.service_name = service_name
        self.service_id = service_id or f"{service_name}-001"
        self.context = {
            "service": service_name,
            "service_id": self.service_id
        }
    
    @abstractmethod
    def log(self, level: LogLevel, message: str, context: Optional[Dict[str, Any]] = None):
        """Log message with level and context"""
        pass
    
    @abstractmethod
    def info(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log info message"""
        pass
    
    @abstractmethod
    def error(self, message: str, error: Exception = None, context: Optional[Dict[str, Any]] = None):
        """Log error message with optional exception"""
        pass
    
    @abstractmethod
    def warning(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log warning message"""
        pass
    
    @abstractmethod
    def debug(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log debug message"""
        pass
    
    @abstractmethod
    def critical(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log critical message"""
        pass
    
    def add_context(self, key: str, value: Any):
        """Add persistent context to logger"""
        self.context[key] = value
    
    def remove_context(self, key: str):
        """Remove context from logger"""
        self.context.pop(key, None)
    
    def get_context(self) -> Dict[str, Any]:
        """Get current logger context"""
        return self.context.copy()
    
    @abstractmethod
    def setup_service_specific_formatting(self):
        """Setup service-specific log formatting"""
        pass