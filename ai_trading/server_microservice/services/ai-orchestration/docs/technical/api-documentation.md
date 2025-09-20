# AI Orchestration Service - API Documentation

## Overview
Comprehensive REST API for AI workflow orchestration with Handit AI, Letta, LangGraph, and Langfuse integration.

## Base URL
```
http://localhost:8003/api/v1
```

## Authentication
Currently authentication is optional. When enabled, use API key in header:
```
X-API-Key: your_api_key_here
```

## Core Endpoints

### Health & Status

#### GET /health
Health check endpoint with comprehensive service status.

**Response:**
```json
{
  "status": "healthy",
  "service": "ai-orchestration-unified",
  "uptime_seconds": 3600,
  "microservice_version": "2.0.0",
  "active_workflows": 5,
  "active_tasks": 12,
  "component_status": {
    "handit_ai": true,
    "letta_memory": true,
    "langgraph_workflows": true,
    "langfuse_observability": true
  }
}
```

#### GET /status
Detailed service status with component metrics.

**Response:**
```json
{
  "service": "ai-orchestration-unified",
  "status": "running",
  "uptime_seconds": 3600,
  "execution_stats": {
    "total_workflows": 150,
    "successful_workflows": 142,
    "failed_workflows": 8
  },
  "detailed_component_metrics": {
    "handit_ai": {...},
    "letta_memory": {...}
  }
}
```

### AI Orchestration Operations

#### POST /api/v1/orchestration/execute
Execute unified AI orchestration operations.

**Request Body:**
```json
{
  "operation_type": "handit_task|memory_operation|workflow_execution|trace_creation|comprehensive_analysis",
  "parameters": {
    "task_type": "analysis",
    "input_data": {...},
    "model_specialty": "general"
  }
}
```

**Response:**
```json
{
  "success": true,
  "orchestration_id": "orchestration_1641234567890",
  "operation_type": "handit_task",
  "execution_time_ms": 1250.5,
  "result": {
    "handit_result": {...}
  },
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

### Task Management

#### POST /api/v1/ai-orchestration/tasks
Create a new AI task.

**Request Body:**
```json
{
  "task_type": "financial_analysis",
  "specialty": "forex_specialist",
  "input_data": {
    "symbol": "EURUSD",
    "timeframe": "1H",
    "periods": 100
  },
  "priority": 3,
  "timeout": 30,
  "metadata": {}
}
```

**Response:**
```json
{
  "task_id": "handit_ms_financial_analysis_1_1641234567890",
  "status": "pending",
  "task_type": "financial_analysis",
  "specialty": "forex_specialist",
  "priority": 3,
  "created_at": "2024-01-01T12:00:00.000Z"
}
```

#### GET /api/v1/ai-orchestration/tasks/{task_id}
Get task status and results.

**Response:**
```json
{
  "task_id": "handit_ms_financial_analysis_1_1641234567890",
  "status": "completed",
  "task_type": "financial_analysis",
  "specialty": "forex_specialist",
  "priority": 3,
  "created_at": "2024-01-01T12:00:00.000Z",
  "started_at": "2024-01-01T12:00:01.000Z",
  "completed_at": "2024-01-01T12:00:05.500Z",
  "processing_time_ms": 4500.0,
  "result": {
    "analysis": "Handit AI analysis results",
    "confidence": 0.85
  }
}
```

#### GET /api/v1/ai-orchestration/tasks
List tasks with filtering.

**Query Parameters:**
- `status`: Filter by task status
- `task_type`: Filter by task type
- `limit`: Maximum results (1-1000, default: 50)

**Response:**
```json
[
  {
    "task_id": "...",
    "status": "completed",
    "task_type": "financial_analysis",
    "created_at": "..."
  }
]
```

#### DELETE /api/v1/ai-orchestration/tasks/{task_id}
Cancel an active task.

**Response:** 204 No Content

### System Information

#### GET /api/v1/ai-orchestration/metrics
Get comprehensive service metrics.

**Response:**
```json
{
  "api_metrics": {
    "total_requests": 1500,
    "successful_requests": 1450,
    "failed_requests": 50,
    "avg_response_time_ms": 250.5
  },
  "ai_orchestration_handit_metrics": {
    "total_tasks_created": 500,
    "successful_tasks": 475,
    "failed_tasks": 25
  },
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

#### GET /api/v1/ai-orchestration/models
Get available AI models and configurations.

**Response:**
```json
{
  "task_types": [
    "financial_analysis",
    "trading_signals",
    "risk_assessment"
  ],
  "model_specialties": [
    "forex_specialist",
    "crypto_specialist",
    "stock_analyst"
  ],
  "available_models": [
    "handit-forex-microservice-v2",
    "handit-crypto-microservice-v2"
  ]
}
```

## Operation Types

### handit_task
Execute specialized AI tasks using Handit AI models.

**Parameters:**
- `task_type`: Type of analysis (financial_analysis, trading_signals, etc.)
- `input_data`: Market data or analysis input
- `model_specialty`: Specialized model to use

### memory_operation
Manage AI agent memory using Letta integration.

**Parameters:**
- `action`: create_session, add_memory
- `agent_id`: Agent identifier
- `context`: Memory context
- `content`: Memory content (for add_memory)

### workflow_execution
Execute complex multi-step workflows using LangGraph.

**Parameters:**
- `template_name`: Workflow template to execute
- `input_data`: Workflow input data
- `workflow_parameters`: Execution parameters

### trace_creation
Create observability traces using Langfuse.

**Parameters:**
- `trace_name`: Name for the trace
- `input_data`: Trace input data
- `metadata`: Additional trace metadata

### comprehensive_analysis
Execute multi-component analysis using all AI services.

**Parameters:**
- `input_data`: Analysis input data
- `workflow_parameters`: Analysis configuration

## Error Responses

All endpoints return standardized error responses:

```json
{
  "success": false,
  "error": "Error description",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "execution_time_ms": 50.0
}
```

### HTTP Status Codes
- `200`: Success
- `201`: Created
- `204`: No Content
- `400`: Bad Request (validation error)
- `404`: Not Found
- `500`: Internal Server Error

## Rate Limiting
- Default: 1000 requests per minute
- Configurable via `RATE_LIMITING_REQUESTS_PER_MINUTE`
- Returns 429 when limit exceeded

## WebSocket Support
Currently not implemented. Future enhancement for real-time workflow updates.

## SDK Examples

### Python
```python
import httpx

client = httpx.Client(base_url="http://localhost:8003")

# Create task
response = client.post("/api/v1/ai-orchestration/tasks", json={
    "task_type": "financial_analysis",
    "specialty": "forex_specialist",
    "input_data": {"symbol": "EURUSD"},
    "priority": 3
})

task = response.json()
task_id = task["task_id"]

# Get task status
status = client.get(f"/api/v1/ai-orchestration/tasks/{task_id}")
print(status.json())
```

### JavaScript
```javascript
const client = axios.create({
  baseURL: 'http://localhost:8003'
});

// Create comprehensive analysis
const response = await client.post('/api/v1/orchestration/execute', {
  operation_type: 'comprehensive_analysis',
  parameters: {
    input_data: { symbol: 'EURUSD', timeframe: '1H' }
  }
});

console.log(response.data);
```

## Performance Considerations
- Response times typically under 500ms for basic operations
- Complex workflows may take 5-30 seconds
- Caching enabled for duplicate requests (10-minute TTL)
- Memory-optimized with bounded task history (500 entries)

## Monitoring
- Health checks every 30 seconds
- Metrics collection every minute
- Event publishing for all major operations
- Performance tracking with centralized infrastructure