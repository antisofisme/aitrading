# Chain Mapping Integration Guide

## Overview

This guide provides step-by-step instructions for implementing embedded chain mapping capabilities across the AI Trading System's microservices architecture. The implementation enhances existing services without adding new ones, ensuring minimal complexity while maximizing debugging and troubleshooting capabilities.

## Implementation Roadmap

### Phase 1: Foundation Infrastructure (Week 1-2)

#### 1.1 Database Service Enhancements (Port 8008)

**Step 1: Add Chain Tracking Tables**
```sql
-- Execute in PostgreSQL database
-- File: migrations/001_add_chain_tables.sql

-- Chain definitions table
CREATE TABLE chain_definitions (
    id BIGSERIAL PRIMARY KEY,
    chain_id UUID NOT NULL UNIQUE,
    chain_name VARCHAR(255),
    service_topology JSONB NOT NULL,
    expected_services TEXT[] NOT NULL,
    max_duration_ms INTEGER,
    critical_path TEXT[],
    health_check_rules JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Chain history table
CREATE TABLE chain_history (
    id BIGSERIAL PRIMARY KEY,
    chain_id UUID NOT NULL,
    request_id UUID NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    duration_ms INTEGER,
    endpoint VARCHAR(255),
    user_id VARCHAR(100),
    metadata JSONB,
    error_context JSONB,
    dependencies JSONB,
    performance_metrics JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Chain metrics table
CREATE TABLE chain_metrics (
    id BIGSERIAL PRIMARY KEY,
    chain_id UUID NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(18,6) NOT NULL,
    metric_unit VARCHAR(50),
    service_name VARCHAR(100),
    timestamp TIMESTAMP NOT NULL,
    aggregation_period VARCHAR(20),
    tags JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_chain_definitions_chain_id ON chain_definitions(chain_id);
CREATE INDEX idx_chain_definitions_active ON chain_definitions(is_active);
CREATE INDEX idx_chain_history_chain_id ON chain_history(chain_id);
CREATE INDEX idx_chain_history_timestamp ON chain_history(timestamp);
CREATE INDEX idx_chain_history_service_event ON chain_history(service_name, event_type);
CREATE INDEX idx_chain_metrics_chain_id ON chain_metrics(chain_id);
CREATE INDEX idx_chain_metrics_name_timestamp ON chain_metrics(metric_name, timestamp);
```

**Step 2: Add Chain Query Engine**
```python
# File: server_microservice/services/database-service/src/infrastructure/chain/chain_query_engine.py

from typing import List, Dict, Optional
import asyncpg
import json
from datetime import datetime, timedelta

class ChainQueryEngine:
    def __init__(self, db_pool: asyncpg.Pool):
        self.db = db_pool

    async def store_chain_event(self, event: dict) -> bool:
        """Store chain event in database"""
        query = """
        INSERT INTO chain_history (
            chain_id, request_id, service_name, event_type,
            timestamp, duration_ms, endpoint, user_id,
            metadata, error_context, dependencies, performance_metrics
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        """

        try:
            async with self.db.acquire() as conn:
                await conn.execute(
                    query,
                    event['chain_id'],
                    event['request_id'],
                    event['service_name'],
                    event['event_type'],
                    event['timestamp'],
                    event.get('duration_ms'),
                    event.get('endpoint'),
                    event.get('user_id'),
                    json.dumps(event.get('metadata', {})),
                    json.dumps(event.get('error_context')),
                    json.dumps(event.get('dependencies', [])),
                    json.dumps(event.get('performance_metrics', {}))
                )
            return True
        except Exception as e:
            logger.error(f"Failed to store chain event: {e}")
            return False

    async def get_chain_events(self, chain_id: str) -> List[dict]:
        """Get all events for a specific chain"""
        query = """
        SELECT * FROM chain_history
        WHERE chain_id = $1
        ORDER BY timestamp ASC
        """

        async with self.db.acquire() as conn:
            rows = await conn.fetch(query, chain_id)
            return [dict(row) for row in rows]

    async def get_chain_analysis(self, chain_id: str) -> dict:
        """Get comprehensive chain analysis"""
        events = await self.get_chain_events(chain_id)

        if not events:
            return {"error": "Chain not found"}

        analysis = {
            "chain_id": chain_id,
            "total_duration": self._calculate_total_duration(events),
            "service_count": len(set(e['service_name'] for e in events)),
            "success_rate": self._calculate_success_rate(events),
            "bottlenecks": self._identify_bottlenecks(events),
            "dependency_graph": self._build_dependency_graph(events)
        }

        return analysis
```

**Step 3: Update Database Service API**
```python
# File: server_microservice/services/database-service/src/api/chain_endpoints.py

from fastapi import APIRouter, HTTPException
from ..infrastructure.chain.chain_query_engine import ChainQueryEngine

router = APIRouter(prefix="/api/v1/chains", tags=["Chain Tracking"])

@router.post("/events")
async def store_chain_event(event: dict):
    """Store chain event"""
    try:
        success = await chain_query_engine.store_chain_event(event)
        if success:
            return {"status": "success"}
        else:
            raise HTTPException(status_code=500, detail="Failed to store event")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events/{chain_id}")
async def get_chain_events(chain_id: str):
    """Get events for a specific chain"""
    try:
        events = await chain_query_engine.get_chain_events(chain_id)
        return {"chain_id": chain_id, "events": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/{chain_id}")
async def get_chain_analysis(chain_id: str):
    """Get chain analysis"""
    try:
        analysis = await chain_query_engine.get_chain_analysis(chain_id)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### 1.2 Internal Event Bus Implementation

**Step 1: Create Event Bus Infrastructure**
```python
# File: server_microservice/services/api-gateway/src/infrastructure/events/chain_event_bus.py

import asyncio
import json
import aioredis
from typing import Dict, Callable, List
from datetime import datetime

class ChainEventBus:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.subscribers: Dict[str, List[Callable]] = {}
        self.redis_client = None

    async def initialize(self):
        """Initialize Redis connection"""
        self.redis_client = await aioredis.from_url(self.redis_url)

    async def publish(self, topic: str, event: dict):
        """Publish event to topic"""
        if not self.redis_client:
            await self.initialize()

        event['published_at'] = datetime.utcnow().isoformat()
        await self.redis_client.publish(topic, json.dumps(event))

        # Also notify local subscribers
        if topic in self.subscribers:
            for callback in self.subscribers[topic]:
                try:
                    await callback(event)
                except Exception as e:
                    logger.error(f"Error in event subscriber: {e}")

    async def subscribe(self, topic: str, callback: Callable):
        """Subscribe to topic with callback"""
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(callback)

        # Also subscribe to Redis
        if not self.redis_client:
            await self.initialize()

        async def redis_subscriber():
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(topic)

            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        event = json.loads(message['data'])
                        await callback(event)
                    except Exception as e:
                        logger.error(f"Error processing Redis event: {e}")

        # Start Redis subscriber in background
        asyncio.create_task(redis_subscriber())

    async def publish_chain_event(self, chain_id: str, service_name: str,
                                event_type: str, metadata: dict = None):
        """Convenience method to publish chain events"""
        event = {
            'chain_id': chain_id,
            'service_name': service_name,
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        }

        await self.publish('chain.events', event)

        # Also publish to service-specific topic
        await self.publish(f'chain.{service_name}', event)
```

### Phase 2: API Gateway Enhancements (Week 2-3)

#### 2.1 Request Tracing Middleware

**Step 1: Implement Chain Context**
```python
# File: server_microservice/services/api-gateway/src/infrastructure/chain/chain_context.py

import uuid
from datetime import datetime
from typing import Dict, List, Optional

class ChainContext:
    def __init__(self, chain_id: str = None, parent_chain_id: str = None):
        self.chain_id = chain_id or str(uuid.uuid4())
        self.request_id = str(uuid.uuid4())
        self.parent_chain_id = parent_chain_id
        self.start_time = datetime.utcnow()
        self.services: List[Dict] = []
        self.dependencies: List[Dict] = []
        self.metadata: Dict = {}
        self.performance_metrics: Dict = {}
        self.error_context: Optional[Dict] = None

    def add_service(self, service_name: str, endpoint: str = None) -> int:
        """Add service to chain and return index"""
        service_entry = {
            'service_name': service_name,
            'endpoint': endpoint,
            'start_time': datetime.utcnow(),
            'duration_ms': None,
            'status': 'processing'
        }
        self.services.append(service_entry)
        return len(self.services) - 1

    def complete_service(self, service_index: int, status: str = 'success'):
        """Mark service as completed"""
        if service_index < len(self.services):
            service = self.services[service_index]
            service['duration_ms'] = (
                datetime.utcnow() - service['start_time']
            ).total_seconds() * 1000
            service['status'] = status

    def add_dependency(self, target_service: str, call_info: dict):
        """Add dependency call information"""
        dependency = {
            'target_service': target_service,
            'timestamp': datetime.utcnow(),
            **call_info
        }
        self.dependencies.append(dependency)

    def to_chain_event(self, event_type: str, service_name: str) -> dict:
        """Convert to chain event format"""
        return {
            'chain_id': self.chain_id,
            'request_id': self.request_id,
            'service_name': service_name,
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'duration_ms': self.get_total_duration(),
            'metadata': self.metadata,
            'dependencies': self.dependencies,
            'error_context': self.error_context,
            'performance_metrics': self.performance_metrics
        }

    def get_total_duration(self) -> float:
        """Get total chain duration in milliseconds"""
        return (datetime.utcnow() - self.start_time).total_seconds() * 1000
```

**Step 2: Request Tracer Middleware**
```python
# File: server_microservice/services/api-gateway/src/middleware/request_tracer.py

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import asyncio
from ..infrastructure.chain.chain_context import ChainContext
from ..infrastructure.events.chain_event_bus import ChainEventBus

class RequestTracerMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, event_bus: ChainEventBus):
        super().__init__(app)
        self.event_bus = event_bus

    async def dispatch(self, request: Request, call_next):
        # Generate or extract chain ID
        chain_id = request.headers.get('X-Chain-ID')
        parent_chain_id = request.headers.get('X-Parent-Chain-ID')

        # Create chain context
        chain_context = ChainContext(chain_id, parent_chain_id)

        # Add chain context to request state
        request.state.chain_context = chain_context

        # Record chain start
        service_index = chain_context.add_service(
            'api-gateway',
            f"{request.method} {request.url.path}"
        )

        # Add metadata
        chain_context.metadata.update({
            'method': request.method,
            'path': request.url.path,
            'user_agent': request.headers.get('user-agent'),
            'source_ip': request.client.host if request.client else None
        })

        # Publish chain start event
        await self.event_bus.publish_chain_event(
            chain_context.chain_id,
            'api-gateway',
            'start',
            chain_context.metadata
        )

        start_time = time.time()

        try:
            # Add chain headers to outgoing requests
            request.headers.__dict__['_list'].append((
                b'x-chain-id',
                chain_context.chain_id.encode()
            ))
            request.headers.__dict__['_list'].append((
                b'x-request-id',
                chain_context.request_id.encode()
            ))

            # Process request
            response = await call_next(request)

            # Record success
            duration = (time.time() - start_time) * 1000
            chain_context.complete_service(service_index, 'success')

            # Add performance metrics
            chain_context.performance_metrics.update({
                'response_time_ms': duration,
                'status_code': response.status_code,
                'response_size': len(response.body) if hasattr(response, 'body') else 0
            })

            # Publish completion event
            await self.event_bus.publish_chain_event(
                chain_context.chain_id,
                'api-gateway',
                'complete',
                {
                    'duration_ms': duration,
                    'status_code': response.status_code,
                    'success': True
                }
            )

            # Add chain headers to response
            response.headers['X-Chain-ID'] = chain_context.chain_id
            response.headers['X-Request-ID'] = chain_context.request_id

            return response

        except Exception as e:
            # Record error
            duration = (time.time() - start_time) * 1000
            chain_context.complete_service(service_index, 'error')

            chain_context.error_context = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'service': 'api-gateway'
            }

            # Publish error event
            await self.event_bus.publish_chain_event(
                chain_context.chain_id,
                'api-gateway',
                'error',
                {
                    'duration_ms': duration,
                    'error': str(e),
                    'success': False
                }
            )

            raise
```

#### 2.2 Chain Performance Monitor

**Step 1: Performance Monitoring Component**
```python
# File: server_microservice/services/api-gateway/src/infrastructure/chain/chain_performance_monitor.py

import asyncio
import statistics
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List

class ChainPerformanceMonitor:
    def __init__(self, event_bus: ChainEventBus):
        self.event_bus = event_bus
        self.metrics_buffer = defaultdict(lambda: deque(maxlen=1000))
        self.performance_thresholds = {
            'max_duration_ms': 5000,
            'max_error_rate': 0.05,
            'max_dependency_failures': 0.02
        }

    async def initialize(self):
        """Initialize performance monitoring"""
        # Subscribe to chain events
        await self.event_bus.subscribe('chain.events', self.process_chain_event)

        # Start monitoring tasks
        asyncio.create_task(self.monitor_performance_metrics())
        asyncio.create_task(self.detect_performance_issues())

    async def process_chain_event(self, event: dict):
        """Process incoming chain events for performance tracking"""
        chain_id = event.get('chain_id')
        service_name = event.get('service_name')
        event_type = event.get('event_type')

        if event_type == 'complete':
            # Record performance metrics
            duration = event.get('metadata', {}).get('duration_ms', 0)
            self.metrics_buffer[f"{service_name}_duration"].append(duration)

            # Record overall chain metrics
            self.metrics_buffer[f"chain_{chain_id}_events"].append(event)

        elif event_type == 'error':
            # Record error metrics
            self.metrics_buffer[f"{service_name}_errors"].append(event)

    async def monitor_performance_metrics(self):
        """Continuously monitor performance metrics"""
        while True:
            try:
                current_metrics = self.calculate_current_metrics()

                # Store metrics for analysis
                await self.store_performance_metrics(current_metrics)

                # Check for performance degradation
                degradation_detected = self.check_performance_degradation(current_metrics)
                if degradation_detected:
                    await self.alert_performance_degradation(degradation_detected)

            except Exception as e:
                logger.error(f"Error monitoring performance: {e}")

            await asyncio.sleep(30)  # Monitor every 30 seconds

    def calculate_current_metrics(self) -> Dict:
        """Calculate current performance metrics"""
        metrics = {}

        # Calculate per-service metrics
        for key, values in self.metrics_buffer.items():
            if '_duration' in key:
                service_name = key.replace('_duration', '')
                if values:
                    metrics[f"{service_name}_avg_duration"] = statistics.mean(values)
                    metrics[f"{service_name}_p95_duration"] = self.percentile(values, 0.95)
                    metrics[f"{service_name}_p99_duration"] = self.percentile(values, 0.99)

            elif '_errors' in key:
                service_name = key.replace('_errors', '')
                total_requests = len(self.metrics_buffer.get(f"{service_name}_duration", []))
                error_count = len(values)
                if total_requests > 0:
                    metrics[f"{service_name}_error_rate"] = error_count / total_requests

        return metrics

    async def detect_performance_issues(self):
        """Detect performance issues and anomalies"""
        while True:
            try:
                # Get recent performance data
                recent_metrics = self.get_recent_performance_data()

                # Run anomaly detection
                anomalies = self.detect_anomalies(recent_metrics)

                if anomalies:
                    for anomaly in anomalies:
                        await self.event_bus.publish_chain_event(
                            'system',
                            'performance-monitor',
                            'anomaly_detected',
                            anomaly
                        )

            except Exception as e:
                logger.error(f"Error detecting performance issues: {e}")

            await asyncio.sleep(60)  # Check every minute
```

### Phase 3: Service Integration (Week 3-4)

#### 3.1 Chain-Aware Service Template

**Step 1: Base Chain-Aware Service**
```python
# File: server_microservice/services/shared/chain_aware_service.py

from abc import ABC, abstractmethod
import httpx
import time
from typing import Optional, Dict, Any

class ChainAwareService(ABC):
    def __init__(self, service_name: str, event_bus: ChainEventBus):
        self.service_name = service_name
        self.event_bus = event_bus
        self.chain_context: Optional[ChainContext] = None

    async def initialize_chain_awareness(self):
        """Initialize chain awareness for the service"""
        await self.event_bus.initialize()
        await self.event_bus.subscribe(
            f'chain.{self.service_name}',
            self.handle_chain_event
        )

    def extract_chain_context(self, headers: Dict[str, str]) -> Optional[ChainContext]:
        """Extract chain context from request headers"""
        chain_id = headers.get('x-chain-id')
        request_id = headers.get('x-request-id')

        if chain_id:
            context = ChainContext(chain_id)
            context.request_id = request_id or context.request_id
            return context
        return None

    async def start_chain_operation(self, operation_name: str,
                                  chain_context: ChainContext) -> int:
        """Start a chain operation"""
        service_index = chain_context.add_service(self.service_name, operation_name)

        # Publish start event
        await self.event_bus.publish_chain_event(
            chain_context.chain_id,
            self.service_name,
            'start',
            {'operation': operation_name}
        )

        return service_index

    async def complete_chain_operation(self, service_index: int,
                                     chain_context: ChainContext,
                                     status: str = 'success',
                                     metadata: Dict = None):
        """Complete a chain operation"""
        chain_context.complete_service(service_index, status)

        # Publish completion event
        await self.event_bus.publish_chain_event(
            chain_context.chain_id,
            self.service_name,
            'complete' if status == 'success' else 'error',
            metadata or {}
        )

    async def call_downstream_service(self, service_url: str,
                                    chain_context: ChainContext,
                                    method: str = 'GET',
                                    **kwargs) -> httpx.Response:
        """Make chain-aware call to downstream service"""
        start_time = time.time()

        # Add chain headers
        headers = kwargs.get('headers', {})
        headers.update({
            'X-Chain-ID': chain_context.chain_id,
            'X-Request-ID': chain_context.request_id,
            'X-Source-Service': self.service_name
        })
        kwargs['headers'] = headers

        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(method, service_url, **kwargs)

                # Record successful dependency call
                duration = (time.time() - start_time) * 1000
                chain_context.add_dependency(
                    self.extract_service_name_from_url(service_url),
                    {
                        'endpoint': service_url,
                        'method': method,
                        'duration_ms': duration,
                        'status': 'success',
                        'status_code': response.status_code
                    }
                )

                return response

        except Exception as e:
            # Record failed dependency call
            duration = (time.time() - start_time) * 1000
            chain_context.add_dependency(
                self.extract_service_name_from_url(service_url),
                {
                    'endpoint': service_url,
                    'method': method,
                    'duration_ms': duration,
                    'status': 'error',
                    'error': str(e)
                }
            )
            raise

    @abstractmethod
    async def handle_chain_event(self, event: Dict[str, Any]):
        """Handle chain events specific to this service"""
        pass

    def extract_service_name_from_url(self, url: str) -> str:
        """Extract service name from URL"""
        # Simple implementation - extract from port or hostname
        if ':800' in url:
            port = url.split(':800')[1].split('/')[0]
            port_to_service = {
                '0': 'api-gateway',
                '1': 'data-bridge',
                '2': 'performance-analytics',
                '3': 'ai-orchestration',
                '4': 'deep-learning',
                '5': 'ai-provider',
                '6': 'ml-processing',
                '7': 'trading-engine',
                '8': 'database-service',
                '9': 'user-service'
            }
            return port_to_service.get(port, 'unknown')
        return 'unknown'
```

#### 3.2 Update Existing Services

**Example: Data Bridge Service Enhancement**
```python
# File: server_microservice/services/data-bridge/src/api/websocket_handler.py

from ..shared.chain_aware_service import ChainAwareService

class ChainAwareDataBridge(ChainAwareService):
    def __init__(self, event_bus: ChainEventBus):
        super().__init__('data-bridge', event_bus)

    async def handle_market_data(self, data: dict, headers: Dict[str, str]):
        """Process market data with chain tracking"""

        # Extract or create chain context
        chain_context = self.extract_chain_context(headers)
        if not chain_context:
            chain_context = ChainContext()

        # Start chain operation
        service_index = await self.start_chain_operation(
            'process_market_data', chain_context
        )

        try:
            # Process data
            processed_data = await self.process_data(data)

            # Store data with chain context
            await self.store_data_with_chain(processed_data, chain_context)

            # Forward to downstream services
            await self.forward_to_feature_store(processed_data, chain_context)

            # Complete operation
            await self.complete_chain_operation(
                service_index, chain_context, 'success',
                {'data_points': len(processed_data), 'symbol': data.get('symbol')}
            )

        except Exception as e:
            await self.complete_chain_operation(
                service_index, chain_context, 'error',
                {'error': str(e)}
            )
            raise

    async def forward_to_feature_store(self, data: dict, chain_context: ChainContext):
        """Forward data to feature store with chain context"""

        feature_store_url = "http://localhost:8008/api/v1/features/store"

        await self.call_downstream_service(
            feature_store_url,
            chain_context,
            method='POST',
            json=data
        )

    async def handle_chain_event(self, event: Dict[str, Any]):
        """Handle chain events for data bridge"""
        event_type = event.get('event_type')

        if event_type == 'error':
            # Handle error propagation
            logger.warning(f"Chain error detected: {event}")

        elif event_type == 'performance_degradation':
            # Adjust processing based on performance issues
            await self.adjust_processing_rate(event.get('metadata', {}))
```

### Phase 4: Monitoring and Analytics (Week 4-5)

#### 4.1 Enhanced Performance Analytics

**Update Performance Analytics Service**
```python
# File: server_microservice/services/performance-analytics/src/api/chain_analytics.py

from fastapi import APIRouter, Depends, HTTPException
from ..infrastructure.chain.chain_analyzer import ChainAnalyzer
from ..infrastructure.chain.anomaly_detector import ChainAnomalyDetector

router = APIRouter(prefix="/api/v1/analytics/chains")

@router.get("/health/overview")
async def get_chain_health_overview():
    """Get overall chain health overview"""
    try:
        analyzer = ChainAnalyzer()
        health_overview = await analyzer.get_chain_health_overview()
        return health_overview
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance/real-time")
async def get_real_time_performance():
    """Get real-time chain performance metrics"""
    try:
        analyzer = ChainAnalyzer()
        metrics = await analyzer.get_real_time_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/anomalies/detect")
async def detect_chain_anomalies():
    """Detect anomalies in chain performance"""
    try:
        detector = ChainAnomalyDetector()
        anomalies = await detector.detect_current_anomalies()
        return {"anomalies": anomalies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/optimization/recommendations")
async def get_optimization_recommendations():
    """Get AI-driven optimization recommendations"""
    try:
        analyzer = ChainAnalyzer()
        recommendations = await analyzer.get_optimization_recommendations()
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### 4.2 Debugging and Troubleshooting Tools

**Chain Debugging CLI Tool**
```bash
#!/bin/bash
# File: scripts/chain-debug.sh

# Chain debugging utilities

function get_chain_trace() {
    local chain_id=$1
    echo "Getting trace for chain: $chain_id"
    curl -s "http://localhost:8002/api/v1/analytics/chains/trace/$chain_id" | jq .
}

function get_chain_health() {
    echo "Getting overall chain health..."
    curl -s "http://localhost:8002/api/v1/analytics/chains/health/overview" | jq .
}

function monitor_real_time() {
    echo "Monitoring real-time chain performance..."
    while true; do
        clear
        curl -s "http://localhost:8002/api/v1/analytics/chains/performance/real-time" | jq .
        sleep 5
    done
}

function detect_anomalies() {
    echo "Detecting chain anomalies..."
    curl -s "http://localhost:8002/api/v1/analytics/chains/anomalies/detect" | jq .
}

function get_service_impact() {
    local service_name=$1
    echo "Getting impact analysis for service: $service_name"
    curl -s "http://localhost:8002/api/v1/analytics/chains/services/$service_name/impact" | jq .
}

# Main menu
case "$1" in
    "trace")
        get_chain_trace $2
        ;;
    "health")
        get_chain_health
        ;;
    "monitor")
        monitor_real_time
        ;;
    "anomalies")
        detect_anomalies
        ;;
    "impact")
        get_service_impact $2
        ;;
    *)
        echo "Usage: $0 {trace|health|monitor|anomalies|impact} [chain_id|service_name]"
        echo ""
        echo "Commands:"
        echo "  trace <chain_id>     - Get detailed trace for specific chain"
        echo "  health              - Get overall chain health overview"
        echo "  monitor             - Monitor real-time performance"
        echo "  anomalies           - Detect performance anomalies"
        echo "  impact <service>    - Get service impact analysis"
        ;;
esac
```

### Phase 5: Testing and Validation (Week 5-6)

#### 5.1 Chain Mapping Tests

**Integration Test Suite**
```python
# File: tests/integration/test_chain_mapping.py

import pytest
import asyncio
import uuid
from datetime import datetime
import httpx

class TestChainMapping:

    @pytest.mark.asyncio
    async def test_end_to_end_chain_tracking(self):
        """Test complete chain tracking through all services"""

        # Generate test chain ID
        chain_id = str(uuid.uuid4())

        # Make request with chain ID
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/v1/data/ingest",
                headers={'X-Chain-ID': chain_id},
                json={'symbol': 'EURUSD', 'price': 1.1234}
            )

        assert response.status_code == 200

        # Wait for chain to complete
        await asyncio.sleep(2)

        # Verify chain was tracked
        async with httpx.AsyncClient() as client:
            trace_response = await client.get(
                f"http://localhost:8008/api/v1/chains/events/{chain_id}"
            )

        assert trace_response.status_code == 200

        trace_data = trace_response.json()
        events = trace_data['events']

        # Verify we have events from multiple services
        services = set(event['service_name'] for event in events)
        assert 'api-gateway' in services
        assert 'data-bridge' in services
        assert len(services) >= 2

        # Verify chain completion
        completion_events = [e for e in events if e['event_type'] == 'complete']
        assert len(completion_events) > 0

    @pytest.mark.asyncio
    async def test_chain_error_tracking(self):
        """Test error tracking in chain"""

        chain_id = str(uuid.uuid4())

        # Make request that will cause error
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/v1/data/ingest",
                headers={'X-Chain-ID': chain_id},
                json={'invalid': 'data'}  # This should cause validation error
            )

        # Wait for chain processing
        await asyncio.sleep(2)

        # Get chain events
        async with httpx.AsyncClient() as client:
            trace_response = await client.get(
                f"http://localhost:8008/api/v1/chains/events/{chain_id}"
            )

        trace_data = trace_response.json()
        events = trace_data['events']

        # Verify error was tracked
        error_events = [e for e in events if e['event_type'] == 'error']
        assert len(error_events) > 0

        # Verify error context is present
        error_event = error_events[0]
        assert 'error_context' in error_event
        assert error_event['error_context'] is not None

    @pytest.mark.asyncio
    async def test_chain_performance_monitoring(self):
        """Test chain performance monitoring"""

        # Generate multiple requests to build performance data
        chain_ids = []
        for i in range(10):
            chain_id = str(uuid.uuid4())
            chain_ids.append(chain_id)

            async with httpx.AsyncClient() as client:
                await client.post(
                    "http://localhost:8000/api/v1/data/ingest",
                    headers={'X-Chain-ID': chain_id},
                    json={'symbol': 'EURUSD', 'price': 1.1234 + i * 0.0001}
                )

        # Wait for processing
        await asyncio.sleep(5)

        # Get performance metrics
        async with httpx.AsyncClient() as client:
            metrics_response = await client.get(
                "http://localhost:8002/api/v1/analytics/chains/performance/real-time"
            )

        assert metrics_response.status_code == 200

        metrics = metrics_response.json()
        assert 'active_chains' in metrics
        assert 'average_duration' in metrics
        assert metrics['active_chains'] >= 0

    @pytest.mark.asyncio
    async def test_chain_anomaly_detection(self):
        """Test chain anomaly detection"""

        # Get current anomalies
        async with httpx.AsyncClient() as client:
            anomalies_response = await client.get(
                "http://localhost:8002/api/v1/analytics/chains/anomalies/detect"
            )

        assert anomalies_response.status_code == 200

        anomalies_data = anomalies_response.json()
        assert 'anomalies' in anomalies_data
        assert isinstance(anomalies_data['anomalies'], list)
```

#### 5.2 Performance Validation

**Load Testing with Chain Tracking**
```python
# File: tests/performance/test_chain_performance.py

import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
import httpx

async def load_test_with_chain_tracking():
    """Load test with chain tracking enabled"""

    concurrent_requests = 100
    total_requests = 1000

    async def make_request():
        chain_id = str(uuid.uuid4())
        start_time = time.time()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/v1/data/ingest",
                headers={'X-Chain-ID': chain_id},
                json={'symbol': 'EURUSD', 'price': 1.1234}
            )

        duration = time.time() - start_time
        return {
            'chain_id': chain_id,
            'duration': duration,
            'status_code': response.status_code,
            'success': response.status_code == 200
        }

    # Run load test
    semaphore = asyncio.Semaphore(concurrent_requests)

    async def bounded_request():
        async with semaphore:
            return await make_request()

    print(f"Starting load test: {total_requests} requests with {concurrent_requests} concurrent")

    start_time = time.time()
    tasks = [bounded_request() for _ in range(total_requests)]
    results = await asyncio.gather(*tasks)
    total_time = time.time() - start_time

    # Analyze results
    durations = [r['duration'] for r in results]
    success_count = sum(1 for r in results if r['success'])

    print(f"\nLoad Test Results:")
    print(f"Total requests: {total_requests}")
    print(f"Successful requests: {success_count}")
    print(f"Success rate: {success_count/total_requests:.2%}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Requests per second: {total_requests/total_time:.2f}")
    print(f"Average response time: {statistics.mean(durations):.3f}s")
    print(f"P95 response time: {statistics.quantiles(durations, n=20)[18]:.3f}s")
    print(f"P99 response time: {statistics.quantiles(durations, n=100)[98]:.3f}s")

if __name__ == "__main__":
    asyncio.run(load_test_with_chain_tracking())
```

## Deployment Instructions

### 1. Database Migration
```bash
# Run database migrations
cd server_microservice/services/database-service
python -m alembic upgrade head

# Verify tables were created
psql -d trading_db -c "\dt chain_*"
```

### 2. Service Updates
```bash
# Update each service with chain awareness
for service in api-gateway data-bridge performance-analytics; do
    cd server_microservice/services/$service
    docker-compose build
    docker-compose up -d
    cd -
done
```

### 3. Configuration Updates
```yaml
# Update docker-compose.yml
version: '3.8'
services:
  api-gateway:
    environment:
      - CHAIN_TRACKING_ENABLED=true
      - EVENT_BUS_URL=redis://redis:6379

  performance-analytics:
    environment:
      - CHAIN_ANALYTICS_ENABLED=true
      - AI_MODELS_PATH=/models/chain
```

### 4. Monitoring Setup
```bash
# Start monitoring
./scripts/chain-debug.sh health

# Monitor real-time performance
./scripts/chain-debug.sh monitor

# Check for anomalies
./scripts/chain-debug.sh anomalies
```

## Success Metrics

- **Chain Tracking Coverage**: 100% of requests tracked through all services
- **Performance Impact**: < 5% overhead on request processing
- **Debug Time Reduction**: 70% faster issue resolution
- **Anomaly Detection**: 95% accuracy in detecting performance issues
- **System Reliability**: 99.9% uptime with proactive issue detection

This comprehensive implementation provides embedded chain mapping capabilities that enhance the AI Trading System's observability, debugging, and troubleshooting capabilities without adding architectural complexity or requiring new services.