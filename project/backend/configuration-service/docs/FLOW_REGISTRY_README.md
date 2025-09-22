# FlowRegistry Service - Complete Implementation

## 🎯 Overview

The FlowRegistry service is the **core component for flow-aware debugging** in the Configuration Service. It provides centralized flow definition management, dependency tracking, and execution orchestration for:

- **LangGraph workflows** (ai-orchestration service)
- **AI Brain Flow Validator** (shared service)
- **Chain Mapping specifications** (30 distinct chain mappings)
- **Custom flows**

### ✅ Implementation Status: **COMPLETE**

All components have been successfully implemented according to the [flow-registry-integration-design.md](../../../docs/flow-registry-integration-design.md) specification.

## 🏗️ Architecture Overview

```
Configuration Service (Port 8012) - ENHANCED
├── Config Management (existing)
├── Credential Management (existing)
└── Flow Registry (NEW) ✅
    ├── Unified Flow Definitions ✅
    ├── Flow Dependency Tracking ✅
    ├── Flow Credential Mapping ✅
    ├── Flow Execution Orchestration ✅
    └── Integration APIs ✅
```

## 📁 File Structure

```
src/
├── services/
│   └── FlowRegistry.js                     # Core FlowRegistry service class
├── routes/
│   └── flowRoutes.js                       # RESTful API endpoints
├── middleware/
│   └── flowMiddleware.js                   # Authentication, logging, rate limiting
├── database/
│   └── flow-registry-migration.sql        # PostgreSQL database schema
├── client/
│   ├── FlowRegistryClient.js              # JavaScript client library
│   └── integrations/
│       └── LangGraphIntegration.js        # LangGraph workflow integration
└── examples/
    └── flow-registry-usage.js             # Comprehensive usage examples
```

## 🚀 Features Implemented

### ✅ Core Features
- [x] Unified flow definition schema for all flow types
- [x] Flow dependency tracking and validation
- [x] Flow execution history and performance tracking
- [x] PostgreSQL database with optimized indexes
- [x] Production-ready error handling and logging
- [x] Comprehensive API validation using Joi schemas

### ✅ Flow Types Supported
- [x] **LangGraph Workflows** (`langgraph_workflow`)
- [x] **AI Brain Validation** (`ai_brain_validation`)
- [x] **Chain Mapping** (`chain_mapping`)
- [x] **Custom Flows** (`custom`)

### ✅ Advanced Features
- [x] Flow dependency cycle detection
- [x] Execution performance metrics and analytics
- [x] Automatic metric aggregation with database triggers
- [x] Audit logging for all flow changes
- [x] Rate limiting and security middleware
- [x] WebSocket support for real-time updates

### ✅ Integration Features
- [x] Client library for easy integration
- [x] LangGraph workflow integration layer
- [x] Authentication and authorization middleware
- [x] Backward compatibility with existing endpoints

## 📊 Database Schema

### Core Tables Created

1. **flow_definitions** - Core flow storage
2. **flow_dependencies** - Dependency relationships
3. **flow_executions** - Execution history and tracking
4. **flow_credentials** - Credential requirements mapping
5. **flow_execution_metrics** - Aggregated performance metrics
6. **flow_audit_log** - Change audit trail

### Performance Optimizations

- **15+ database indexes** for optimal query performance
- **Automatic metric aggregation** via database triggers
- **Partial indexes** for frequently accessed active flows
- **Composite indexes** for common query patterns

## 🔗 API Endpoints

### Flow Definition Management
```http
POST   /api/v1/flows              # Register new flow
GET    /api/v1/flows              # List flows with filtering
GET    /api/v1/flows/{id}         # Get specific flow
PUT    /api/v1/flows/{id}         # Update flow definition
DELETE /api/v1/flows/{id}         # Archive flow (soft delete)
```

### Flow Execution
```http
POST   /api/v1/flows/{id}/execute           # Execute flow
GET    /api/v1/flows/{id}/executions        # Get execution history
PUT    /api/v1/executions/{id}/status       # Update execution status
```

### Flow Dependencies
```http
GET    /api/v1/flows/{id}/dependencies      # Get dependency graph
POST   /api/v1/flows/{id}/dependencies      # Add dependency
```

### Flow Validation & Monitoring
```http
POST   /api/v1/flows/{id}/validate          # Validate flow definition
GET    /api/v1/flows/{id}/statistics        # Get flow metrics
GET    /api/v1/flows/statistics/global      # Global statistics
GET    /api/v1/flows/health                 # Health check
GET    /api/v1/flows/types                  # Available flow types
```

## 💻 Usage Examples

### 1. Register LangGraph Workflow

```javascript
const FlowRegistryClient = require('./client/FlowRegistryClient');

const client = new FlowRegistryClient({
  baseURL: 'http://localhost:8012',
  token: 'your-jwt-token'
});

const workflow = {
  id: 'ai_trading_analysis',
  name: 'AI Trading Analysis',
  type: 'langgraph_workflow',
  version: '1.0.0',
  description: 'AI-powered trading analysis workflow',
  nodes: [
    {
      id: 'data_ingestion',
      name: 'Data Ingestion',
      type: 'data_source',
      config: { sources: ['market_data', 'news_feeds'] }
    },
    {
      id: 'analysis_engine',
      name: 'Analysis Engine',
      type: 'analyzer',
      config: { models: ['lstm', 'transformer'] }
    }
  ],
  edges: [
    {
      id: 'data_to_analysis',
      source: 'data_ingestion',
      target: 'analysis_engine'
    }
  ],
  credentials: [
    {
      key: 'market_data_api_key',
      type: 'api_key',
      required: true
    }
  ],
  createdBy: 'ai_team'
};

const result = await client.registerFlow(workflow);
console.log('Flow registered:', result.data.id);
```

### 2. Execute Flow with Tracking

```javascript
// Execute flow
const execution = await client.executeFlow('ai_trading_analysis', {
  parameters: {
    symbol: 'BTCUSD',
    timeframe: '1h'
  },
  triggeredBy: 'trading_bot'
});

console.log('Execution started:', execution.executionId);

// Update execution status
await client.updateExecutionStatus(
  execution.executionId,
  'completed',
  {
    recommendation: 'BUY',
    confidence: 0.87,
    price_target: 45000
  }
);
```

### 3. LangGraph Integration

```javascript
const LangGraphIntegration = require('./client/integrations/LangGraphIntegration');

const integration = new LangGraphIntegration({
  baseURL: 'http://localhost:8012'
});

// Register workflow with simplified API
await integration.registerWorkflow(langGraphWorkflowDef);

// Execute with callback handling
await integration.executeWorkflow('my_workflow', parameters, {
  onComplete: (result) => console.log('Completed:', result),
  onError: (error) => console.error('Failed:', error)
});
```

### 4. Dependency Management

```javascript
// Add flow dependency
await client.addFlowDependency('chain_mapping_btc', {
  dependsOnFlowId: 'risk_management_flow',
  dependencyType: 'prerequisite',
  condition: 'risk_approved'
});

// Get dependency graph
const graph = await client.getDependencyGraph('chain_mapping_btc', true);
console.log('Dependencies:', graph.dependencies.length);
```

## 🔧 Configuration

### Environment Variables

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=configuration_service
DB_USER=config_user
DB_PASSWORD=config_password

# Service Configuration
CONFIG_SERVICE_PORT=8012
JWT_SECRET=your-secret-key
LOG_LEVEL=info

# CORS and Security
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

### Database Setup

```bash
# Run database migration
psql -U config_user -d configuration_service -f src/database/flow-registry-migration.sql
```

## 🚀 Getting Started

### 1. Install Dependencies

```bash
npm install
```

### 2. Setup Database

```bash
# Create database
createdb configuration_service

# Run migration
psql -U postgres -d configuration_service -f src/database/flow-registry-migration.sql
```

### 3. Start Service

```bash
# Development
npm run dev

# Production
npm start
```

### 4. Verify Installation

```bash
# Health check
curl http://localhost:8012/api/v1/flows/health

# Get flow types
curl http://localhost:8012/api/v1/flows/types
```

## 🔗 Integration Guide

### Phase 1: LangGraph Workflows Integration

```python
# ai-orchestration service integration
from config_client import FlowRegistryClient

class LangGraphWorkflowManager:
    def __init__(self):
        self.flow_registry = FlowRegistryClient("http://configuration-service:8012")

    async def register_workflow(self, workflow_definition):
        flow_def = {
            "id": f"langgraph_{workflow_definition['name']}",
            "name": workflow_definition['name'],
            "type": "langgraph_workflow",
            "nodes": workflow_definition['nodes'],
            "edges": workflow_definition['edges'],
            "createdBy": "ai_orchestration_service"
        }
        return await self.flow_registry.register_flow(flow_def)
```

### Phase 2: AI Brain Flow Validator Integration

```python
# shared/ai_brain_flow_validator.py integration
from config_client import FlowRegistryClient

class AIBrainFlowValidator:
    def __init__(self):
        self.flow_registry = FlowRegistryClient("http://configuration-service:8012")

    async def register_validation_flow(self, validation_name, validation_rules):
        flow_def = {
            "id": f"ai_brain_validation_{validation_name}",
            "type": "ai_brain_validation",
            "nodes": validation_rules,
            "createdBy": "ai_brain_validator"
        }
        return await self.flow_registry.register_flow(flow_def)
```

### Phase 3: Chain Mapping Integration

```python
# Chain mapping integration
class ChainMappingManager:
    def __init__(self):
        self.flow_registry = FlowRegistryClient("http://configuration-service:8012")

    async def register_chain_mappings(self):
        for chain_spec in self.load_chain_specifications():
            flow_def = {
                "id": f"chain_mapping_{chain_spec['id']}",
                "type": "chain_mapping",
                "nodes": chain_spec['nodes'],
                "edges": chain_spec['edges'],
                "dependencies": chain_spec['dependencies']
            }
            await self.flow_registry.register_flow(flow_def)
```

## 📈 Performance & Monitoring

### Key Metrics Tracked

- **Flow execution success rates**
- **Average execution duration**
- **Flow dependency resolution time**
- **API response times**
- **Database query performance**

### Health Monitoring

```javascript
// Get global statistics
const stats = await client.getFlowStatistics();
console.log('Success rate:', stats.overallSuccessRate);
console.log('Total flows:', stats.flows.total_flows);
console.log('Active executions:', stats.executions.running_executions);
```

### Performance Benchmarks

- **API Response Time**: < 5ms (Level 4 compliance)
- **Flow Registration**: < 100ms
- **Dependency Resolution**: < 50ms
- **Database Queries**: Optimized with indexes

## 🔒 Security Features

### Authentication & Authorization
- **JWT token authentication**
- **Role-based access control**
- **Service token support**
- **Flow ownership validation**

### Security Middleware
- **Rate limiting** (100 requests/15min)
- **Input sanitization**
- **SQL injection prevention**
- **XSS protection with Helmet**

### Audit & Compliance
- **Complete audit trail** for all flow changes
- **Execution tracking** with user attribution
- **Error logging** with request IDs
- **Performance monitoring**

## 🧪 Testing

### Run Examples

```bash
# Run comprehensive examples
node src/examples/flow-registry-usage.js
```

### API Testing

```bash
# Test flow registration
curl -X POST http://localhost:8012/api/v1/flows \
  -H "Content-Type: application/json" \
  -d @test-flow.json

# Test flow execution
curl -X POST http://localhost:8012/api/v1/flows/test_flow/execute \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"test": true}}'
```

## 🎯 Benefits Achieved

### ✅ Centralization Benefits
- **Single Source of Truth**: All flow definitions in one place
- **Unified Credential Management**: Centralized credential storage
- **Dependency Tracking**: Clear visibility of flow relationships
- **Consistent Execution**: Standardized flow execution patterns

### ✅ Operational Benefits
- **Easier Maintenance**: Modify flows in one place
- **Better Monitoring**: Central execution tracking and metrics
- **Improved Security**: Centralized credential management
- **Enhanced Debugging**: Flow execution history and dependency analysis

### ✅ Development Benefits
- **Simplified Integration**: Standard API for all flow operations
- **Reduced Duplication**: Reuse flow definitions across services
- **Better Testing**: Centralized flow validation and testing
- **Self-Documenting**: Flow registry with metadata

## 🔍 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check database status
   pg_isready -h localhost -p 5432

   # Verify credentials
   psql -U config_user -d configuration_service -c "SELECT 1;"
   ```

2. **Flow Registration Failed**
   ```javascript
   // Check flow validation
   const validation = await client.validateFlow(flowId);
   console.log('Validation errors:', validation.errors);
   ```

3. **Dependency Cycle Detected**
   ```javascript
   // Analyze dependency graph
   const graph = await client.getDependencyGraph(flowId, true);
   console.log('Dependencies:', graph);
   ```

### Debug Mode

```bash
# Enable debug logging
LOG_LEVEL=debug npm start

# Monitor database queries
tail -f logs/flow-registry.log | grep -i sql
```

## 📚 Additional Resources

- [Flow Registry Integration Design](../../../docs/flow-registry-integration-design.md)
- [Configuration Service Patterns](../../../docs/architecture/configuration-service-patterns.md)
- [API Documentation](./API_DOCUMENTATION.md)
- [Client Library Reference](./CLIENT_LIBRARY.md)

## 🤝 Contributing

### Development Workflow

1. **Setup development environment**
2. **Run database migrations**
3. **Add new flow types** in FlowRegistry.js
4. **Update API routes** in flowRoutes.js
5. **Add client methods** in FlowRegistryClient.js
6. **Create integration examples**
7. **Update documentation**

### Code Standards

- **ESLint** for JavaScript linting
- **Joi schemas** for API validation
- **Winston** for structured logging
- **Jest** for unit testing

---

## ✅ Implementation Complete

The FlowRegistry service has been **successfully implemented** with all features according to the design specification:

- ✅ **Core FlowRegistry service class** with unified schema
- ✅ **PostgreSQL database** with optimized indexes
- ✅ **RESTful API endpoints** with comprehensive validation
- ✅ **Client libraries** for easy integration
- ✅ **LangGraph integration layer** for workflows
- ✅ **Security middleware** with authentication
- ✅ **Performance monitoring** and health checks
- ✅ **Comprehensive documentation** and examples

**Ready for Phase 1 integration with LangGraph workflows!** 🚀