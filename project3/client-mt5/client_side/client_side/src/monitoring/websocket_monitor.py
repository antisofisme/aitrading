"""
websocket_monitor.py - WebSocket Endpoint Monitoring

🎯 PURPOSE:
Business: Monitor WebSocket connections across all 11 microservices for complete system health
Technical: Real-time monitoring for 45+ WebSocket endpoints with priority tracking and intelligent routing
Domain: WebSocket/Monitoring/Service Health/System Integration

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:27.770Z
Session: client-side-ai-brain-full-compliance
Confidence: 91%
Complexity: high

🧩 PATTERNS USED:
- AI_BRAIN_WEBSOCKET_MONITORING: Complete microservice monitoring with AI patterns
- PRIORITY_BASED_MONITORING: Intelligent priority-based endpoint monitoring

📦 DEPENDENCIES:
Internal: centralized_logger, error_handler, data_source_monitor
External: asyncio, websockets, dataclasses, enum, json

💡 AI DECISION REASONING:
Comprehensive WebSocket monitoring critical for distributed trading system reliability. Priority-based approach ensures critical services monitored first.

🚀 USAGE:
monitor = WebSocketMonitor(); await monitor.start_monitoring(ServicePriority.CRITICAL)

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

import asyncio
import websockets
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import logging

# Import centralized infrastructure
from ..infrastructure import get_logger, get_client_settings, handle_error


class ConnectionStatus(str, Enum):
    """WebSocket connection status"""
    CONNECTED = "connected"
    CONNECTING = "connecting" 
    DISCONNECTED = "disconnected"
    FAILED = "failed"
    TIMEOUT = "timeout"
    ERROR = "error"


class ServicePriority(str, Enum):
    """Service monitoring priority"""
    CRITICAL = "critical"      # Trading, Data-Bridge, API Gateway
    HIGH = "high"             # AI services, User Service  
    MEDIUM = "medium"         # ML Processing, Database
    LOW = "low"               # System monitoring, Health checks


@dataclass
class WebSocketEndpoint:
    """WebSocket endpoint configuration"""
    url: str
    name: str
    service: str
    port: int
    priority: ServicePriority
    description: str
    retry_attempts: int = 3
    timeout: int = 10
    ping_interval: int = 30
    expected_message_types: List[str] = field(default_factory=list)
    
    # Status tracking
    status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    last_connected: Optional[datetime] = None
    last_message: Optional[datetime] = None
    connection_attempts: int = 0
    total_messages: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    response_time: Optional[float] = None


class WebSocketMonitor:
    """
    Comprehensive WebSocket Monitor for All Services
    Monitors 45+ endpoints across 11 microservices with prioritized monitoring
    """
    
    def __init__(self):
        self.logger = get_logger('websocket_monitor', context={
            'component': 'websocket_monitor',
            'version': '2.0.0-comprehensive'
        })
        
        # Load client settings
        self.settings = get_client_settings()
        
        # WebSocket endpoint registry
        self.endpoints: Dict[str, WebSocketEndpoint] = {}
        self.connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        
        # Monitoring state
        self.is_monitoring = False
        self.start_time = datetime.now(timezone.utc)
        self.status_callbacks: List[Callable] = []
        
        # Performance metrics
        self.metrics = {
            "total_endpoints": 0,
            "connected_endpoints": 0,
            "failed_endpoints": 0,
            "critical_services_up": 0,
            "total_messages": 0,
            "average_response_time": 0.0,
            "uptime_seconds": 0.0
        }
        
        # Initialize all service endpoints
        self._initialize_endpoints()
        
        self.logger.info(f"🚀 WebSocket Monitor initialized with {len(self.endpoints)} endpoints")
    
    def _initialize_endpoints(self):
        """Initialize all WebSocket endpoints for all services"""
        
        # 1. API GATEWAY (8000) - Entry Point & Routing
        self._add_api_gateway_endpoints()
        
        # 2. DATA-BRIDGE (8001) - Market Data & MT5
        self._add_data_bridge_endpoints()
        
        # 3. AI ORCHESTRATION (8003) - AI Workflow Coordination  
        self._add_ai_orchestration_endpoints()
        
        # 4. DEEP LEARNING (8004) - Neural Network Processing
        self._add_deep_learning_endpoints()
        
        # 5. AI PROVIDER (8005) - LLM Integration
        self._add_ai_provider_endpoints()
        
        # 6. ML PROCESSING (8006) - Traditional ML
        self._add_ml_processing_endpoints()
        
        # 7. TRADING ENGINE (8007) - Trading Logic & Execution
        self._add_trading_engine_endpoints()
        
        # 8. DATABASE SERVICE (8008) - Data Persistence & Streaming
        self._add_database_service_endpoints()
        
        # 9. USER SERVICE (8009) - User Management & Notifications
        self._add_user_service_endpoints()
        
        # 10. PERFORMANCE ANALYTICS (8002) - Performance Metrics & Analytics
        self._add_performance_analytics_endpoints()
        
        # 11. STRATEGY OPTIMIZATION (8010) - Trading Strategy Optimization
        self._add_strategy_optimization_endpoints()
        
        self.metrics["total_endpoints"] = len(self.endpoints)
    
    def _add_api_gateway_endpoints(self):
        """API Gateway WebSocket endpoints"""
        base_url = "ws://localhost:8000"
        
        endpoints = [
            # Client-facing resource-based endpoints
            ("market-data", "/api/stream/market-data", "Real-time market data streaming", ServicePriority.CRITICAL, 
             ["tick_data", "price_updates", "volume_data"]),
            ("trading", "/api/stream/trading", "Trading signals and execution updates", ServicePriority.CRITICAL,
             ["trading_signal", "execution_update", "risk_alert"]),
            ("account", "/api/stream/account", "Account balance and position updates", ServicePriority.CRITICAL,
             ["account_info", "balance_update", "position_change"]),
            ("news", "/api/stream/news", "Economic news and market events", ServicePriority.HIGH,
             ["economic_calendar", "market_news", "volatility_alert"]),
            ("system", "/api/stream/system", "System health and service alerts", ServicePriority.HIGH,
             ["health_check", "service_alert", "performance_metric"]),
            
            # Test endpoints
            ("test-simple", "/ws/test", "Simple WebSocket testing", ServicePriority.LOW, ["hello"]),
            ("test-advanced", "/api/v1/ws/test", "Advanced WebSocket testing", ServicePriority.LOW, ["connection_established"])
        ]
        
        for name, path, desc, priority, msg_types in endpoints:
            self.endpoints[f"gateway-{name}"] = WebSocketEndpoint(
                url=f"{base_url}{path}",
                name=f"Gateway {name.title()}",
                service="api-gateway",
                port=8000,
                priority=priority,
                description=desc,
                expected_message_types=msg_types
            )
    
    def _add_data_bridge_endpoints(self):
        """Data-Bridge WebSocket endpoints"""
        base_url = "ws://localhost:8001"
        
        endpoints = [
            # Main MT5 endpoints
            ("mt5-main", "/api/v1/ws", "Main MT5 WebSocket endpoint", ServicePriority.CRITICAL,
             ["connection_established", "tick_data", "account_info", "trading_signal"]),
            ("mt5-status", "/api/v1/ws/status", "MT5 connection status monitoring", ServicePriority.HIGH,
             ["websocket_status", "mt5_bridge_status"]),
            ("mt5-health", "/api/v1/ws/health", "MT5 WebSocket health checks", ServicePriority.HIGH,
             ["health_check", "connection_metrics"]),
            
            # Internal proxy endpoints (for API Gateway)
            ("internal-market", "/api/v1/api/internal/market-data", "Internal market data for API Gateway", ServicePriority.MEDIUM,
             ["internal_connection_established", "tick_data"]),
            ("internal-trading", "/api/v1/api/internal/trading", "Internal trading for API Gateway", ServicePriority.MEDIUM,
             ["internal_connection_established", "trading_signal"]),
            ("internal-account", "/api/v1/api/internal/account", "Internal account for API Gateway", ServicePriority.MEDIUM,
             ["internal_connection_established", "account_info"])
        ]
        
        for name, path, desc, priority, msg_types in endpoints:
            self.endpoints[f"bridge-{name}"] = WebSocketEndpoint(
                url=f"{base_url}{path}",
                name=f"Bridge {name.title()}",
                service="data-bridge", 
                port=8001,
                priority=priority,
                description=desc,
                expected_message_types=msg_types
            )
    
    def _add_ai_orchestration_endpoints(self):
        """AI Orchestration WebSocket endpoints"""
        base_url = "ws://localhost:8003"
        
        endpoints = [
            ("workflows", "/api/v1/ws/workflows", "Real-time AI workflow status updates", ServicePriority.HIGH,
             ["workflow_started", "workflow_completed", "workflow_error", "step_update"]),
            ("agents", "/api/v1/ws/agents", "AI agent coordination and status", ServicePriority.HIGH,
             ["agent_status", "agent_coordination", "task_assignment"]),
            ("tasks", "/api/v1/ws/tasks", "Task scheduling and completion notifications", ServicePriority.HIGH,
             ["task_queued", "task_started", "task_completed", "task_failed"]),
            ("monitoring", "/api/v1/ws/monitoring", "AI performance metrics streaming", ServicePriority.MEDIUM,
             ["performance_metric", "resource_usage", "ai_health_check"])
        ]
        
        for name, path, desc, priority, msg_types in endpoints:
            self.endpoints[f"ai-orch-{name}"] = WebSocketEndpoint(
                url=f"{base_url}{path}",
                name=f"AI Orchestration {name.title()}",
                service="ai-orchestration",
                port=8003,
                priority=priority,
                description=desc,
                expected_message_types=msg_types
            )
    
    def _add_deep_learning_endpoints(self):
        """Deep Learning WebSocket endpoints"""
        base_url = "ws://localhost:8004"
        
        endpoints = [
            ("training", "/api/v1/ws/training", "Neural network training progress", ServicePriority.HIGH,
             ["training_started", "epoch_completed", "training_completed", "training_metrics"]),
            ("inference", "/api/v1/ws/inference", "Real-time inference results", ServicePriority.HIGH,
             ["inference_request", "inference_result", "batch_prediction"]),
            ("gpu-metrics", "/api/v1/ws/gpu-metrics", "GPU utilization monitoring", ServicePriority.MEDIUM,
             ["gpu_usage", "memory_usage", "temperature", "power_consumption"]),
            ("model-updates", "/api/v1/ws/model-updates", "Model checkpoint notifications", ServicePriority.MEDIUM,
             ["checkpoint_saved", "model_exported", "weights_updated"])
        ]
        
        for name, path, desc, priority, msg_types in endpoints:
            self.endpoints[f"dl-{name}"] = WebSocketEndpoint(
                url=f"{base_url}{path}",
                name=f"Deep Learning {name.title()}",
                service="deep-learning",
                port=8004,
                priority=priority,
                description=desc,
                expected_message_types=msg_types
            )
    
    def _add_ai_provider_endpoints(self):
        """AI Provider WebSocket endpoints"""
        base_url = "ws://localhost:8005"
        
        endpoints = [
            ("completions", "/api/v1/ws/completions", "Streaming AI completions", ServicePriority.HIGH,
             ["completion_chunk", "completion_completed", "completion_error"]),
            ("provider-health", "/api/v1/ws/provider-health", "AI provider status monitoring", ServicePriority.HIGH,
             ["provider_status", "api_health", "rate_limit_status"]),
            ("cost-tracking", "/api/v1/ws/cost-tracking", "Real-time cost updates", ServicePriority.MEDIUM,
             ["cost_update", "usage_metrics", "billing_alert"]),
            ("failover", "/api/v1/ws/failover", "Provider failover notifications", ServicePriority.HIGH,
             ["failover_triggered", "provider_switched", "recovery_completed"])
        ]
        
        for name, path, desc, priority, msg_types in endpoints:
            self.endpoints[f"ai-provider-{name}"] = WebSocketEndpoint(
                url=f"{base_url}{path}",
                name=f"AI Provider {name.title()}",
                service="ai-provider",
                port=8005,
                priority=priority,
                description=desc,
                expected_message_types=msg_types
            )
    
    def _add_ml_processing_endpoints(self):
        """ML Processing WebSocket endpoints"""
        base_url = "ws://localhost:8006"
        
        endpoints = [
            ("training-jobs", "/api/v1/ws/training-jobs", "Model training progress updates", ServicePriority.MEDIUM,
             ["job_started", "progress_update", "job_completed", "job_failed"]),
            ("predictions", "/api/v1/ws/predictions", "Batch prediction results streaming", ServicePriority.MEDIUM,
             ["prediction_batch", "prediction_result", "batch_completed"]),
            ("feature-engineering", "/api/v1/ws/feature-engineering", "Feature processing status", ServicePriority.MEDIUM,
             ["feature_extraction", "feature_selection", "processing_completed"]),
            ("model-evaluation", "/api/v1/ws/model-evaluation", "Real-time evaluation metrics", ServicePriority.MEDIUM,
             ["evaluation_metrics", "performance_score", "validation_result"])
        ]
        
        for name, path, desc, priority, msg_types in endpoints:
            self.endpoints[f"ml-{name}"] = WebSocketEndpoint(
                url=f"{base_url}{path}",
                name=f"ML Processing {name.title()}",
                service="ml-processing",
                port=8006,
                priority=priority,
                description=desc,
                expected_message_types=msg_types
            )
    
    def _add_trading_engine_endpoints(self):
        """Trading Engine WebSocket endpoints"""
        base_url = "ws://localhost:8007"
        
        endpoints = [
            ("executions", "/api/v1/ws/executions", "Real-time trade execution updates", ServicePriority.CRITICAL,
             ["order_placed", "order_filled", "execution_report", "trade_completed"]),
            ("signals", "/api/v1/ws/signals", "Trading signal generation and validation", ServicePriority.CRITICAL,
             ["signal_generated", "signal_validated", "signal_executed", "signal_rejected"]),
            ("risk-alerts", "/api/v1/ws/risk-alerts", "Risk management notifications", ServicePriority.CRITICAL,
             ["risk_limit_exceeded", "margin_call", "position_risk", "portfolio_risk"]),
            ("portfolio", "/api/v1/ws/portfolio", "Portfolio performance updates", ServicePriority.HIGH,
             ["position_update", "pnl_update", "portfolio_metrics", "performance_summary"])
        ]
        
        for name, path, desc, priority, msg_types in endpoints:
            self.endpoints[f"trading-{name}"] = WebSocketEndpoint(
                url=f"{base_url}{path}",
                name=f"Trading Engine {name.title()}",
                service="trading-engine",
                port=8007,
                priority=priority,
                description=desc,
                expected_message_types=msg_types
            )
    
    def _add_database_service_endpoints(self):
        """Database Service WebSocket endpoints"""
        base_url = "ws://localhost:8008"
        
        endpoints = [
            ("query-streams", "/api/v1/ws/query-streams", "Real-time query result streaming", ServicePriority.MEDIUM,
             ["query_started", "query_result", "query_completed", "streaming_data"]),
            ("data-changes", "/api/v1/ws/data-changes", "Database change notifications", ServicePriority.HIGH,
             ["data_inserted", "data_updated", "data_deleted", "schema_changed"]),
            ("schema-updates", "/api/v1/ws/schema-updates", "Schema modification alerts", ServicePriority.MEDIUM,
             ["schema_migration", "table_created", "index_updated"]),
            ("health-monitoring", "/api/v1/ws/health-monitoring", "Multi-database health status", ServicePriority.HIGH,
             ["db_health_check", "connection_status", "performance_metrics"])
        ]
        
        for name, path, desc, priority, msg_types in endpoints:
            self.endpoints[f"db-{name}"] = WebSocketEndpoint(
                url=f"{base_url}{path}",
                name=f"Database {name.title()}",
                service="database-service",
                port=8008,
                priority=priority,
                description=desc,
                expected_message_types=msg_types
            )
    
    def _add_user_service_endpoints(self):
        """User Service WebSocket endpoints"""
        base_url = "ws://localhost:8009"
        
        endpoints = [
            ("notifications", "/api/v1/ws/notifications", "User notification delivery", ServicePriority.HIGH,
             ["notification_sent", "notification_read", "alert_triggered"]),
            ("sessions", "/api/v1/ws/sessions", "Session activity monitoring", ServicePriority.MEDIUM,
             ["session_started", "session_activity", "session_expired"]),
            ("project-updates", "/api/v1/ws/project-updates", "Project collaboration updates", ServicePriority.MEDIUM,
             ["project_updated", "task_assigned", "collaboration_event"]),
            ("workflow-status", "/api/v1/ws/workflow-status", "User workflow execution status", ServicePriority.MEDIUM,
             ["workflow_triggered", "step_completed", "workflow_finished"])
        ]
        
        for name, path, desc, priority, msg_types in endpoints:
            self.endpoints[f"user-{name}"] = WebSocketEndpoint(
                url=f"{base_url}{path}",
                name=f"User Service {name.title()}",
                service="user-service",
                port=8009,
                priority=priority,
                description=desc,
                expected_message_types=msg_types
            )
    
    def _add_performance_analytics_endpoints(self):
        """Performance Analytics WebSocket endpoints"""
        base_url = "ws://localhost:8002"
        
        endpoints = [
            ("metrics", "/api/v1/ws/metrics", "Real-time performance metrics streaming", ServicePriority.HIGH,
             ["performance_metric", "latency_update", "throughput_metric"]),
            ("analytics", "/api/v1/ws/analytics", "Advanced analytics and insights", ServicePriority.MEDIUM,
             ["analytics_result", "trend_analysis", "performance_insights"]),
            ("alerts", "/api/v1/ws/alerts", "Performance alert notifications", ServicePriority.HIGH,
             ["performance_alert", "threshold_exceeded", "system_warning"]),
            ("reports", "/api/v1/ws/reports", "Report generation status updates", ServicePriority.MEDIUM,
             ["report_started", "report_progress", "report_completed"])
        ]
        
        for name, path, desc, priority, msg_types in endpoints:
            self.endpoints[f"perf-{name}"] = WebSocketEndpoint(
                url=f"{base_url}{path}",
                name=f"Performance Analytics {name.title()}",
                service="performance-analytics",
                port=8002,
                priority=priority,
                description=desc,
                expected_message_types=msg_types
            )
    
    def _add_strategy_optimization_endpoints(self):
        """Strategy Optimization WebSocket endpoints"""
        base_url = "ws://localhost:8010"
        
        endpoints = [
            ("optimization", "/api/v1/ws/optimization", "Strategy optimization progress", ServicePriority.HIGH,
             ["optimization_started", "optimization_progress", "optimization_completed"]),
            ("backtesting", "/api/v1/ws/backtesting", "Backtesting results streaming", ServicePriority.HIGH,
             ["backtest_started", "backtest_progress", "backtest_results"]),
            ("strategy-updates", "/api/v1/ws/strategy-updates", "Strategy parameter updates", ServicePriority.MEDIUM,
             ["parameters_updated", "strategy_deployed", "performance_metrics"]),
            ("genetic-algorithm", "/api/v1/ws/genetic-algorithm", "Genetic algorithm evolution progress", ServicePriority.MEDIUM,
             ["generation_completed", "fitness_improved", "convergence_reached"])
        ]
        
        for name, path, desc, priority, msg_types in endpoints:
            self.endpoints[f"strategy-{name}"] = WebSocketEndpoint(
                url=f"{base_url}{path}",
                name=f"Strategy Optimization {name.title()}",
                service="strategy-optimization",
                port=8010,
                priority=priority,
                description=desc,
                expected_message_types=msg_types
            )
    
    def add_status_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add callback for status updates"""
        self.status_callbacks.append(callback)
    
    async def start_monitoring(self, priority_filter: Optional[ServicePriority] = None):
        """Start monitoring all or filtered endpoints"""
        self.is_monitoring = True
        self.start_time = datetime.now(timezone.utc)
        
        endpoints_to_monitor = self.endpoints.copy()
        
        # Filter by priority if specified
        if priority_filter:
            endpoints_to_monitor = {
                k: v for k, v in self.endpoints.items() 
                if v.priority == priority_filter
            }
        
        self.logger.info(f"🚀 Starting WebSocket monitoring for {len(endpoints_to_monitor)} endpoints")
        
        # Start monitoring tasks for each endpoint
        for endpoint_id, endpoint in endpoints_to_monitor.items():
            task = asyncio.create_task(self._monitor_endpoint(endpoint_id, endpoint))
            self.monitoring_tasks[endpoint_id] = task
        
        # Start metrics collection task
        metrics_task = asyncio.create_task(self._collect_metrics())
        self.monitoring_tasks["metrics"] = metrics_task
    
    async def stop_monitoring(self):
        """Stop all monitoring tasks"""
        self.is_monitoring = False
        
        self.logger.info("🛑 Stopping WebSocket monitoring")
        
        # Cancel all monitoring tasks
        for task in self.monitoring_tasks.values():
            if not task.done():
                task.cancel()
        
        # Close all connections
        for connection in self.connections.values():
            if not connection.closed:
                await connection.close()
        
        self.monitoring_tasks.clear()
        self.connections.clear()
    
    async def _monitor_endpoint(self, endpoint_id: str, endpoint: WebSocketEndpoint):
        """Monitor a single WebSocket endpoint"""
        while self.is_monitoring:
            try:
                endpoint.status = ConnectionStatus.CONNECTING
                endpoint.connection_attempts += 1
                
                start_time = time.time()
                
                # Attempt WebSocket connection
                async with websockets.connect(
                    endpoint.url,
                    timeout=endpoint.timeout,
                    ping_interval=endpoint.ping_interval
                ) as websocket:
                    
                    endpoint.status = ConnectionStatus.CONNECTED
                    endpoint.last_connected = datetime.now(timezone.utc)
                    endpoint.response_time = time.time() - start_time
                    self.connections[endpoint_id] = websocket
                    
                    self.logger.info(f"✅ Connected to {endpoint.name}: {endpoint.url}")
                    
                    # Listen for messages
                    async for message in websocket:
                        endpoint.last_message = datetime.now(timezone.utc)
                        endpoint.total_messages += 1
                        
                        try:
                            # Try to parse as JSON
                            data = json.loads(message)
                            await self._process_message(endpoint_id, endpoint, data)
                        except json.JSONDecodeError:
                            # Handle plain text messages
                            await self._process_message(endpoint_id, endpoint, {"text": message})
            
            except asyncio.TimeoutError:
                endpoint.status = ConnectionStatus.TIMEOUT
                endpoint.error_count += 1
                endpoint.last_error = "Connection timeout"
                
            except ConnectionRefusedError:
                endpoint.status = ConnectionStatus.FAILED
                endpoint.error_count += 1
                endpoint.last_error = "Connection refused"
                
            except Exception as e:
                endpoint.status = ConnectionStatus.ERROR
                endpoint.error_count += 1
                endpoint.last_error = str(e)
                handle_error(e, context={"endpoint": endpoint.name, "url": endpoint.url})
            
            finally:
                if endpoint_id in self.connections:
                    del self.connections[endpoint_id]
            
            # Wait before retry (exponential backoff)
            if self.is_monitoring and endpoint.connection_attempts < endpoint.retry_attempts:
                wait_time = min(2 ** endpoint.connection_attempts, 60)  # Max 60 seconds
                await asyncio.sleep(wait_time)
            else:
                endpoint.status = ConnectionStatus.FAILED
                break
    
    async def _process_message(self, endpoint_id: str, endpoint: WebSocketEndpoint, data: Dict[str, Any]):
        """Process received WebSocket message"""
        # Log message type if available
        message_type = data.get('type', 'unknown')
        if message_type in endpoint.expected_message_types:
            self.logger.debug(f"📨 {endpoint.name} received expected message: {message_type}")
        else:
            self.logger.debug(f"📨 {endpoint.name} received message: {message_type}")
        
        # Trigger callbacks
        for callback in self.status_callbacks:
            try:
                await callback({
                    "endpoint_id": endpoint_id,
                    "endpoint": endpoint,
                    "message": data,
                    "message_type": message_type
                })
            except Exception as e:
                self.logger.error(f"Status callback error: {e}")
    
    async def _collect_metrics(self):
        """Collect and update monitoring metrics"""
        while self.is_monitoring:
            # Count connections by status
            connected = sum(1 for ep in self.endpoints.values() if ep.status == ConnectionStatus.CONNECTED)
            failed = sum(1 for ep in self.endpoints.values() if ep.status == ConnectionStatus.FAILED)
            
            # Count critical services
            critical_up = sum(1 for ep in self.endpoints.values() 
                            if ep.priority == ServicePriority.CRITICAL and ep.status == ConnectionStatus.CONNECTED)
            
            # Calculate average response time
            response_times = [ep.response_time for ep in self.endpoints.values() if ep.response_time]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
            
            # Calculate total messages
            total_messages = sum(ep.total_messages for ep in self.endpoints.values())
            
            # Update metrics
            self.metrics.update({
                "connected_endpoints": connected,
                "failed_endpoints": failed,
                "critical_services_up": critical_up,
                "total_messages": total_messages,
                "average_response_time": avg_response_time,
                "uptime_seconds": (datetime.now(timezone.utc) - self.start_time).total_seconds()
            })
            
            await asyncio.sleep(5)  # Update every 5 seconds
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get comprehensive monitoring status"""
        # Group endpoints by service
        services = {}
        for endpoint_id, endpoint in self.endpoints.items():
            if endpoint.service not in services:
                services[endpoint.service] = {
                    "endpoints": [],
                    "connected": 0,
                    "total": 0,
                    "health_score": 0.0
                }
            
            services[endpoint.service]["endpoints"].append({
                "id": endpoint_id,
                "name": endpoint.name,
                "url": endpoint.url,
                "status": endpoint.status.value,
                "priority": endpoint.priority.value,
                "last_connected": endpoint.last_connected.isoformat() if endpoint.last_connected else None,
                "total_messages": endpoint.total_messages,
                "error_count": endpoint.error_count,
                "response_time": endpoint.response_time
            })
            
            services[endpoint.service]["total"] += 1
            if endpoint.status == ConnectionStatus.CONNECTED:
                services[endpoint.service]["connected"] += 1
            
            # Calculate health score (connected endpoints / total endpoints)
            services[endpoint.service]["health_score"] = (
                services[endpoint.service]["connected"] / services[endpoint.service]["total"] * 100
            )
        
        return {
            "monitoring_active": self.is_monitoring,
            "start_time": self.start_time.isoformat(),
            "metrics": self.metrics,
            "services": services,
            "summary": {
                "total_services": len(services),
                "healthy_services": sum(1 for s in services.values() if s["health_score"] > 80),
                "critical_services_status": {
                    service: data["health_score"] 
                    for service, data in services.items() 
                    if any(ep["priority"] == "critical" for ep in data["endpoints"])
                }
            }
        }
    
    def get_endpoint_details(self, endpoint_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for specific endpoint"""
        if endpoint_id not in self.endpoints:
            return None
        
        endpoint = self.endpoints[endpoint_id]
        return {
            "id": endpoint_id,
            "name": endpoint.name,
            "service": endpoint.service,
            "url": endpoint.url,
            "port": endpoint.port,
            "priority": endpoint.priority.value,
            "description": endpoint.description,
            "status": endpoint.status.value,
            "last_connected": endpoint.last_connected.isoformat() if endpoint.last_connected else None,
            "last_message": endpoint.last_message.isoformat() if endpoint.last_message else None,
            "connection_attempts": endpoint.connection_attempts,
            "total_messages": endpoint.total_messages,
            "error_count": endpoint.error_count,
            "last_error": endpoint.last_error,
            "response_time": endpoint.response_time,
            "expected_message_types": endpoint.expected_message_types,
            "is_connected": endpoint_id in self.connections
        }


# Export main class
__all__ = [
    "WebSocketMonitor", 
    "WebSocketEndpoint", 
    "ConnectionStatus", 
    "ServicePriority"
]