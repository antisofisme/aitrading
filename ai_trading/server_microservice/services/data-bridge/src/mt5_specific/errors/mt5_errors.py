"""
MT5 Bridge Error Handler - Trading platform specific error management
"""
from typing import Dict, Any, Optional
from ...infrastructure.core.error_core import CoreErrorHandler

class MT5BridgeErrorHandler(CoreErrorHandler):
    """MT5 Bridge specific error handler with trading context"""
    
    def __init__(self):
        super().__init__("mt5-bridge")
        self.setup_mt5_error_patterns()
    
    def setup_mt5_error_patterns(self):
        """Setup MT5-specific error patterns and classifications"""
        
        # MT5 Connection Errors
        mt5_connection_errors = {
            "patterns": [
                r".*initialize.*failed.*",
                r".*connection.*timeout.*",
                r".*login.*failed.*",
                r".*server.*unavailable.*",
                r".*invalid.*credentials.*"
            ],
            "classification": "connection_error",
            "severity": "high",
            "retry_strategy": {
                "enabled": True,
                "max_retries": 5,
                "base_delay": 2.0,
                "backoff_factor": 2.0,
                "max_delay": 60.0
            },
            "alerting": {
                "enabled": True,
                "escalation_time": 300  # 5 minutes
            }
        }
        
        # Trading Operation Errors
        trading_errors = {
            "patterns": [
                r".*insufficient.*margin.*",
                r".*invalid.*volume.*",
                r".*market.*closed.*",
                r".*invalid.*price.*",
                r".*order.*rejected.*",
                r".*position.*not.*found.*"
            ],
            "classification": "trading_error",
            "severity": "medium",
            "retry_strategy": {
                "enabled": False  # Don't retry trading operations automatically
            },
            "alerting": {
                "enabled": True,
                "escalation_time": 60  # 1 minute
            }
        }
        
        # Data Processing Errors
        data_errors = {
            "patterns": [
                r".*tick.*processing.*failed.*",
                r".*symbol.*not.*found.*",
                r".*historical.*data.*unavailable.*",
                r".*invalid.*timeframe.*",
                r".*data.*synchronization.*failed.*"
            ],
            "classification": "data_error",
            "severity": "medium",
            "retry_strategy": {
                "enabled": True,
                "max_retries": 3,
                "base_delay": 1.0,
                "backoff_factor": 1.5
            },
            "alerting": {
                "enabled": True,
                "escalation_time": 180  # 3 minutes
            }
        }
        
        # WebSocket Communication Errors
        websocket_errors = {
            "patterns": [
                r".*websocket.*connection.*lost.*",
                r".*client.*disconnected.*",
                r".*message.*send.*failed.*",
                r".*invalid.*websocket.*message.*",
                r".*websocket.*server.*error.*"
            ],
            "classification": "websocket_error",
            "severity": "low",
            "retry_strategy": {
                "enabled": True,
                "max_retries": 2,
                "base_delay": 0.5
            },
            "alerting": {
                "enabled": False  # Don't alert on individual websocket errors
            }
        }
        
        # Risk Management Errors
        risk_errors = {
            "patterns": [
                r".*risk.*limit.*exceeded.*",
                r".*maximum.*drawdown.*reached.*",
                r".*daily.*loss.*limit.*exceeded.*",
                r".*position.*size.*too.*large.*",
                r".*insufficient.*balance.*"
            ],
            "classification": "risk_error",
            "severity": "critical",
            "retry_strategy": {
                "enabled": False  # Never retry risk violations
            },
            "alerting": {
                "enabled": True,
                "escalation_time": 0,  # Immediate escalation
                "notify_channels": ["email", "slack", "sms"]
            }
        }
        
        # Register all error patterns
        self.add_error_pattern("mt5_connection", mt5_connection_errors)
        self.add_error_pattern("trading_operations", trading_errors)
        self.add_error_pattern("data_processing", data_errors)
        self.add_error_pattern("websocket_communication", websocket_errors)
        self.add_error_pattern("risk_management", risk_errors)
    
    def handle_mt5_connection_error(self, 
                                   error: Exception, 
                                   server: str = None,
                                   account: int = None,
                                   attempt: int = 1) -> Dict[str, Any]:
        """Handle MT5 connection specific errors"""
        context = {
            "error_category": "mt5_connection",
            "server": server,
            "account": account,
            "connection_attempt": attempt,
            "component": "mt5_connector"
        }
        
        return self.handle_error(error, context, operation="mt5_connection")
    
    def handle_trading_error(self,
                           error: Exception,
                           symbol: str = None,
                           operation: str = None,
                           volume: float = None,
                           price: float = None) -> Dict[str, Any]:
        """Handle trading operation specific errors"""
        context = {
            "error_category": "trading_error",
            "symbol": symbol,
            "trading_operation": operation,
            "volume": volume,
            "price": price,
            "component": "trading_engine"
        }
        
        return self.handle_error(error, context, operation="trading_operation")
    
    def handle_data_error(self,
                         error: Exception,
                         symbol: str = None,
                         timeframe: str = None,
                         data_type: str = None) -> Dict[str, Any]:
        """Handle data processing specific errors"""
        context = {
            "error_category": "data_error",
            "symbol": symbol,
            "timeframe": timeframe,
            "data_type": data_type,
            "component": "data_processor"
        }
        
        return self.handle_error(error, context, operation="data_processing")
    
    def handle_websocket_error(self,
                              error: Exception,
                              client_id: str = None,
                              message_type: str = None,
                              connection_count: int = None) -> Dict[str, Any]:
        """Handle WebSocket communication specific errors"""
        context = {
            "error_category": "websocket_error",
            "client_id": client_id,
            "message_type": message_type,
            "active_connections": connection_count,
            "component": "websocket_server"
        }
        
        return self.handle_error(error, context, operation="websocket_communication")
    
    def handle_risk_error(self,
                         error: Exception,
                         risk_type: str = None,
                         current_value: float = None,
                         limit_value: float = None,
                         symbol: str = None) -> Dict[str, Any]:
        """Handle risk management specific errors"""
        context = {
            "error_category": "risk_error",
            "risk_type": risk_type,
            "current_value": current_value,
            "limit_value": limit_value,
            "symbol": symbol,
            "component": "risk_manager",
            "immediate_action_required": True
        }
        
        # Log risk errors with high priority
        self.logger.error(f"RISK VIOLATION: {risk_type} - {str(error)}", context)
        
        return self.handle_error(error, context, operation="risk_management")
    
    def get_mt5_error_code_message(self, error_code: int) -> str:
        """Get human-readable message for MT5 error codes"""
        mt5_error_codes = {
            1: "No error",
            2: "Common error",
            3: "Invalid trade parameters",
            4: "Trade server busy",
            5: "Old version of the terminal",
            6: "No connection with trade server",
            7: "Not enough rights",
            8: "Too frequent requests",
            9: "Malfunctional trade operation",
            64: "Account disabled",
            65: "Invalid account",
            128: "Trade timeout",
            129: "Invalid price",
            130: "Invalid stops",
            131: "Invalid trade volume",
            132: "Market is closed",
            133: "Trade is disabled",
            134: "Not enough money",
            135: "Price changed",
            136: "Off quotes",
            137: "Broker is busy",
            138: "Requote",
            139: "Order is locked",
            140: "Only buy orders allowed",
            141: "Too many requests",
            145: "Modification denied because order too close to market",
            146: "Trade context is busy",
            147: "Expirations are denied by broker",
            148: "Amount of open and pending orders has reached the limit"
        }
        
        return mt5_error_codes.get(error_code, f"Unknown MT5 error code: {error_code}")
    
    def create_trading_error_report(self, 
                                   errors_summary: Dict[str, Any],
                                   time_period: int = 3600) -> Dict[str, Any]:
        """Create comprehensive trading error report"""
        report = {
            "report_type": "mt5_trading_errors",
            "time_period_seconds": time_period,
            "summary": errors_summary,
            "recommendations": [],
            "immediate_actions": []
        }
        
        # Analyze error patterns and add recommendations
        if "connection_error" in errors_summary:
            connection_errors = errors_summary["connection_error"]
            if connection_errors.get("count", 0) > 5:
                report["immediate_actions"].append("Check MT5 server connectivity")
                report["recommendations"].append("Consider implementing connection pooling")
        
        if "trading_error" in errors_summary:
            trading_errors = errors_summary["trading_error"]
            if trading_errors.get("count", 0) > 10:
                report["immediate_actions"].append("Review trading parameters")
                report["recommendations"].append("Implement pre-trade validation")
        
        if "risk_error" in errors_summary:
            report["immediate_actions"].append("URGENT: Review risk management settings")
            report["recommendations"].append("Reduce position sizes until risk is controlled")
        
        return report