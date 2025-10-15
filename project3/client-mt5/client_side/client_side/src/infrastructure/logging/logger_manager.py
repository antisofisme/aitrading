"""
logger_manager.py - Centralized Logging Manager

🎯 PURPOSE:
Business: Unified logging system for all client-side trading operations
Technical: Advanced logging with context, performance tracking, and structured output
Domain: Logging/Infrastructure/System Monitoring

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:27.790Z
Session: client-side-ai-brain-full-compliance
Confidence: 94%
Complexity: medium

🧩 PATTERNS USED:
- AI_BRAIN_CENTRALIZED_LOGGING: Centralized logging with context and performance tracking
- STRUCTURED_LOGGING: JSON-structured logging for analysis and monitoring

📦 DEPENDENCIES:
Internal: config_manager, performance_manager
External: logging, json, datetime, threading, inspect

💡 AI DECISION REASONING:
Centralized logging essential for trading system debugging and monitoring. Structured JSON format enables automated log analysis and alerting.

🚀 USAGE:
logger = LoggerManager.get_instance(); logger.info("Trade executed", {"symbol": "EURUSD"})

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

import logging
import sys
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from datetime import datetime
import json
import threading
from dataclasses import dataclass
from loguru import logger as loguru_logger
import os

# Import colorama for Windows color support
try:
    import colorama
    colorama.init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False

@dataclass
class LoggerConfig:
    """Logger configuration"""
    name: str
    level: str = "INFO"
    format_template: str = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} | {message}"
    file_path: Optional[str] = None
    rotation: str = "10 MB"
    retention: str = "7 days"
    compression: str = "zip"
    serialize: bool = False
    colorize: bool = True
    context_fields: List[str] = None

    def __post_init__(self):
        if self.context_fields is None:
            self.context_fields = []

class ClientLoggerManager:
    """
    Client-Side Centralized Logger Manager
    Manages all logging for MT5 Trading Client with context and performance
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        self.loggers: Dict[str, Any] = {}
        self.logger_configs: Dict[str, LoggerConfig] = {}
        self.log_stats: Dict[str, Dict[str, int]] = {}
        self.context_data: Dict[str, Dict[str, Any]] = {}
        self.log_handlers: List[int] = []
        self._setup_base_configuration()
    
    @classmethod
    def get_instance(cls) -> 'ClientLoggerManager':
        """Singleton pattern with thread safety"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def _setup_base_configuration(self):
        """Setup base logging configuration"""
        # Create logs directory
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Remove ALL existing loguru handlers to prevent duplicates
        loguru_logger.remove()
        
        # Also remove any standard logging handlers
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        
        # Setup default configurations
        self._setup_default_configs()
    
    def _setup_default_configs(self):
        """Setup default logger configurations"""
        base_format = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} | {message}"
        
        self.logger_configs.update({
            # Main application logger
            'main': LoggerConfig(
                name='MT5Client',
                level='INFO',
                format_template=base_format,
                file_path="logs/mt5_client.log",
                context_fields=['component', 'operation']
            ),
            
            # MT5 Handler logger
            'mt5_handler': LoggerConfig(
                name='MT5Handler',
                level='INFO',
                format_template="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | MT5 | {message}",
                file_path="logs/mt5_handler.log",
                context_fields=['symbol', 'timeframe', 'account']
            ),
            
            # WebSocket logger
            'websocket': LoggerConfig(
                name='WebSocket',
                level='INFO',
                format_template="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | WS | {message}",
                file_path="logs/websocket.log",
                context_fields=['connection_id', 'message_type']
            ),
            
            # Redpanda logger
            'redpanda': LoggerConfig(
                name='Redpanda',
                level='INFO',
                format_template="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | Kafka | {message}",
                file_path="logs/redpanda.log",
                context_fields=['topic', 'partition']
            ),
            
            # Hybrid Bridge logger
            'bridge': LoggerConfig(
                name='HybridBridge',
                level='INFO',
                format_template="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | Bridge | {message}",
                file_path="logs/hybrid_bridge.log",
                context_fields=['bridge_mode', 'tick_count']
            ),
            
            # Performance logger
            'performance': LoggerConfig(
                name='Performance',
                level='DEBUG',
                format_template="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | PERF | {message}",
                file_path="logs/performance.log",
                context_fields=['operation', 'duration_ms', 'memory_mb']
            ),
            
            # Error logger
            'error': LoggerConfig(
                name='Errors',
                level='ERROR',
                format_template="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | ERROR | {message}",
                file_path="logs/errors.log",
                context_fields=['error_type', 'component', 'severity']
            )
        })
    
    def get_logger(self, name: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Get SINGLE centralized logger - same instance for ALL requests
        
        Args:
            name: Logger name (ignored - using single logger)
            context: Optional context data (ignored for simplicity)
            
        Returns:
            Single centralized logger instance
        """
        # Return single centralized logger for ALL requests
        if not hasattr(self, '_single_logger'):
            self._single_logger = self._create_single_logger()
        
        return self._single_logger
    
    def _create_single_logger(self) -> Any:
        """Create single centralized logger with colored format"""
        # Setup single console handler with colored format based on content
        def format_message(record):
            """Format message with color based on content"""
            try:
                message = str(record["message"])
                
                # Color rules based on message content
                if any(keyword in message.lower() for keyword in ["error", "failed", "disconnected", "timeout", "❌", "🔴", "terhenti"]):
                    # RED for errors/failures
                    return f"<red>{message}</red>"
                elif any(keyword in message.lower() for keyword in ["success", "connected", "active", "✅", "running", "🔵", "started", "initialized"]):
                    # BLUE for success/running
                    return f"<blue>{message}</blue>"
                else:
                    # YELLOW for general information
                    return f"<yellow>{message}</yellow>"
            except Exception:
                # Fallback for any formatting issues
                return f"<white>{record['message']}</white>"
        
        # Use simpler approach - let loguru handle format and add color codes
        sink_config = {
            'sink': sys.stdout,
            'format': "{message}",  
            'level': 'INFO',
            'colorize': not COLORAMA_AVAILABLE,  # Use loguru colors only if colorama not available
            'filter': self._color_filter,
            'diagnose': False  # Disable backtrace for cleaner output
        }
        
        # Add single console handler
        console_handler_id = loguru_logger.add(**sink_config)
        self.log_handlers.append(console_handler_id)
        
        # Return simple logger
        return loguru_logger
    
    def _apply_color(self, text: str, color: str) -> str:
        """Apply color to text using colorama if available"""
        if not COLORAMA_AVAILABLE:
            return text
            
        color_map = {
            'blue': colorama.Fore.CYAN,        # Light blue (cyan)
            'red': colorama.Fore.RED + colorama.Style.DIM,  # Maroon (dimmed red)
            'yellow': colorama.Fore.YELLOW,
            'green': colorama.Fore.GREEN,
            'white': colorama.Fore.WHITE
        }
        
        color_code = color_map.get(color, colorama.Fore.WHITE)
        return f"{color_code}{text}{colorama.Style.RESET_ALL}"
    
    def _color_filter(self, record):
        """Add color to messages based on content - only color status/detail parts"""
        try:
            message = str(record["message"])
            message_lower = message.lower()
            
            # Try to parse message structure: "Description: Status/Detail"
            if ":" in message:
                parts = message.split(":", 1)
                if len(parts) == 2:
                    description = parts[0].strip()
                    status_detail = parts[1].strip()
                    status_lower = status_detail.lower()
                    
                    # Determine color for status/detail part based on content
                    color = None
                    
                    # PRIORITY 1: BLUE for positive status words
                    if any(keyword in status_lower for keyword in ["ready", "active", "loaded", "initialized", "success", "connected", "✅", "running", "🔵", "started", "healthy", "normal", "optimal"]):
                        color = "blue"
                    # PRIORITY 2: RED for problems/failures
                    elif any(keyword in status_lower for keyword in ["failed", "disconnected", "timeout", "❌", "🔴", "terhenti", "exception", "crash", "denied", "error", "unavailable", "missing"]):
                        color = "red"
                    # PRIORITY 3: YELLOW for general information
                    else:
                        color = "yellow"
                    
                    # Apply color using colorama or loguru tags
                    if COLORAMA_AVAILABLE:
                        colored_status = self._apply_color(status_detail, color)
                    else:
                        # Use loguru color tags with light colors
                        loguru_color_map = {
                            'blue': 'cyan',        # Light blue
                            'red': 'red',          # Maroon (loguru doesn't have maroon, use red)
                            'yellow': 'yellow',
                            'green': 'green',
                            'white': 'white'
                        }
                        loguru_color = loguru_color_map.get(color, 'white')
                        colored_status = f"<{loguru_color}>{status_detail}</{loguru_color}>"
                    
                    # Reconstruct message with only status part colored
                    record["message"] = f"{description}: {colored_status}"
                    return True
            
            # If no colon found, check for status words and color accordingly
            color = None
            
            # PRIORITY 1: BLUE for positive status words
            if any(keyword in message_lower for keyword in ["ready", "active", "loaded", "initialized", "success", "connected", "✅", "running", "🔵", "started", "healthy"]):
                color = "blue"
            # PRIORITY 2: RED for problems/failures  
            elif any(keyword in message_lower for keyword in ["failed", "disconnected", "timeout", "❌", "🔴", "terhenti", "exception", "crash", "denied", "error:"]):
                color = "red"
            # PRIORITY 3: YELLOW for general information (default)
            else:
                color = "yellow"
            
            # Apply color using colorama or loguru tags
            if COLORAMA_AVAILABLE:
                record["message"] = self._apply_color(message, color)
            else:
                # Use loguru color tags with light colors
                loguru_color_map = {
                    'blue': 'cyan',        # Light blue
                    'red': 'red',          # Maroon (loguru doesn't have maroon, use red)
                    'yellow': 'yellow',
                    'green': 'green',
                    'white': 'white'
                }
                loguru_color = loguru_color_map.get(color, 'white')
                record["message"] = f"<{loguru_color}>{message}</{loguru_color}>"
                
        except Exception:
            # Leave message as-is if error
            pass
        
        return True
    
    def _create_logger(self, name: str) -> Any:
        """Create new logger with configuration"""
        # Get configuration
        config = self.logger_configs.get(name, self._get_default_config(name))
        
        # Only add handlers if this is the first logger to prevent duplicates
        if len(self.log_handlers) == 0:
            # Setup sink configuration - simple format for console
            sink_config = {
                'sink': sys.stdout,
                'format': "{message}",  # Only show message, no timestamp or logger name
                'level': config.level,
                'colorize': config.colorize
            }
            
            # Add console handler (only once)
            console_handler_id = loguru_logger.add(**sink_config)
            self.log_handlers.append(console_handler_id)
        
        # Add file sink if specified (each logger gets its own file)
        if config.file_path:
            file_sink_config = {
                'sink': config.file_path,
                'format': config.format_template,
                'level': config.level,
                'rotation': config.rotation,
                'retention': config.retention,
                'compression': config.compression,
                'serialize': config.serialize,
                'colorize': False
            }
            
            # Add file handler
            file_handler_id = loguru_logger.add(**file_sink_config)
            self.log_handlers.append(file_handler_id)
        
        # Create logger with context binding
        contextual_logger = loguru_logger.bind(name=config.name)
        
        # Initialize stats
        self.log_stats[name] = {
            'debug': 0, 'info': 0, 'warning': 0, 'error': 0, 'critical': 0
        }
        
        return contextual_logger
    
    def _get_default_config(self, name: str) -> LoggerConfig:
        """Get default configuration for unknown logger"""
        return LoggerConfig(
            name=name.title(),
            level='INFO',
            file_path=f"logs/{name.lower()}.log",
            context_fields=['component']
        )
    
    def set_context(self, logger_name: str, context: Dict[str, Any]):
        """Set context data for logger"""
        if logger_name not in self.context_data:
            self.context_data[logger_name] = {}
        
        self.context_data[logger_name].update(context)
    
    def get_context(self, logger_name: str) -> Dict[str, Any]:
        """Get context data for logger"""
        return self.context_data.get(logger_name, {})
    
    def log_with_context(self, logger_name: str, level: str, message: str, 
                        context: Optional[Dict[str, Any]] = None):
        """Log message with context"""
        logger_instance = self.get_logger(logger_name)
        
        # Combine stored and provided context
        full_context = self.get_context(logger_name).copy()
        if context:
            full_context.update(context)
        
        # Create contextual logger
        contextual_logger = logger_instance.bind(**full_context)
        
        # Log with appropriate level
        getattr(contextual_logger, level.lower())(message)
        
        # Update stats
        if logger_name in self.log_stats:
            self.log_stats[logger_name][level.lower()] += 1
    
    def setup_mt5_logger(self, account: str = None, server: str = None) -> Any:
        """Setup MT5-specific logger with trading context"""
        context = {}
        if account:
            context['account'] = account
        if server:
            context['server'] = server
        
        return self.get_logger('mt5_handler', context)
    
    def setup_websocket_logger(self, connection_id: str = None) -> Any:
        """Setup WebSocket-specific logger"""
        context = {}
        if connection_id:
            context['connection_id'] = connection_id
        
        return self.get_logger('websocket', context)
    
    def setup_performance_logger(self) -> Any:
        """Setup performance-specific logger"""
        return self.get_logger('performance')
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """Get logging statistics"""
        return {
            'total_loggers': len(self.loggers),
            'log_stats': self.log_stats.copy(),
            'context_data_size': {name: len(ctx) for name, ctx in self.context_data.items()},
            'active_handlers': len(self.log_handlers)
        }
    
    def set_log_level(self, logger_name: str, level: str):
        """Change log level for specific logger"""
        if logger_name in self.logger_configs:
            self.logger_configs[logger_name].level = level
            # Recreate logger with new level
            if logger_name in self.loggers:
                del self.loggers[logger_name]
                self.get_logger(logger_name)
    
    def export_logs(self, logger_name: str, filepath: str, 
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None):
        """Export logs to file"""
        # This would require implementing log reading from files
        # For now, just copy the current log file
        config = self.logger_configs.get(logger_name)
        if config and config.file_path:
            try:
                import shutil
                shutil.copy2(config.file_path, filepath)
            except Exception as e:
                print(f"Failed to export logs: {e}")
    
    def cleanup_old_logs(self, days: int = 7):
        """Clean up old log files"""
        logs_dir = Path("logs")
        if logs_dir.exists():
            cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)
            for log_file in logs_dir.glob("*.log*"):
                if log_file.stat().st_mtime < cutoff_time:
                    try:
                        log_file.unlink()
                    except Exception as e:
                        print(f"Failed to delete {log_file}: {e}")


# Global instance
client_logger_manager = ClientLoggerManager.get_instance()

# Convenience functions
def get_logger(name: str, context: Optional[Dict[str, Any]] = None) -> Any:
    """Get logger with centralized configuration"""
    return client_logger_manager.get_logger(name, context)

def setup_mt5_logger(account: str = None, server: str = None) -> Any:
    """Setup MT5-specific logger"""
    return client_logger_manager.setup_mt5_logger(account, server)

def setup_websocket_logger(connection_id: str = None) -> Any:
    """Setup WebSocket-specific logger"""
    return client_logger_manager.setup_websocket_logger(connection_id)

def get_log_stats() -> Dict[str, Any]:
    """Get logging statistics"""
    return client_logger_manager.get_log_statistics()

def log_with_context(logger_name: str, level: str, message: str, 
                    context: Optional[Dict[str, Any]] = None):
    """Log message with context"""
    return client_logger_manager.log_with_context(logger_name, level, message, context)