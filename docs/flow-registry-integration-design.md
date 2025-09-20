# Centralized Flow Registry Integration Design

## 🎯 **Problem Addressed**

**Current State (Problematic):**
- LangGraph workflows (ai-orchestration service) - Template-based AI flows
- AI Brain Flow Validator (shared service) - Architecture validation flows
- Chain Mapping Specifications (docs) - 30 distinct chain mappings
- **Each system has independent flow definitions, credentials, and configurations**

**Issues:**
❌ No single source of truth for flow definitions
❌ Scattered credential management across systems
❌ No dependency tracking between flows
❌ Inconsistent flow execution patterns
❌ Difficult to modify flows without breaking integrations

## 🏗️ **Solution: Centralized Flow Registry**

### **Core Architecture**

```
Configuration Service (Port 8012) - ENHANCED
├── Config Management (existing)
├── Credential Management (existing)
└── Flow Registry (NEW)
    ├── Unified Flow Definitions
    ├── Flow Dependency Tracking
    ├── Flow Credential Mapping
    ├── Flow Execution Orchestration
    └── Integration APIs
```

### **Flow Registry Components**

#### **1. Unified Flow Definition Schema**
```typescript
interface FlowDefinition {
  id: string;                    // Unique flow identifier
  name: string;                  // Human-readable name
  type: FlowType;                // "langgraph", "ai_brain", "chain_mapping"
  version: string;               // Semantic versioning
  description: string;           // Flow purpose

  // Flow Structure
  nodes: FlowNode[];             // Execution nodes
  edges: FlowEdge[];             // Node connections
  dependencies: FlowDependency[]; // External dependencies

  // Configuration
  parameters: FlowParameter[];   // Configurable parameters
  credentials: CredentialRef[];  // Required credentials
  environment: EnvConfig;        // Environment settings

  // Execution
  triggers: FlowTrigger[];       // Execution triggers
  schedule: FlowSchedule;        // Scheduled execution
  retryPolicy: RetryPolicy;      // Error handling

  // Metadata
  created_at: timestamp;
  updated_at: timestamp;
  created_by: string;
  status: FlowStatus;
}

enum FlowType {
  LANGGRAPH_WORKFLOW = "langgraph_workflow",
  AI_BRAIN_VALIDATION = "ai_brain_validation",
  CHAIN_MAPPING = "chain_mapping",
  CUSTOM = "custom"
}

enum FlowStatus {
  DRAFT = "draft",
  ACTIVE = "active",
  DEPRECATED = "deprecated",
  ARCHIVED = "archived"
}
```

#### **2. Flow Registry Database Schema**
```sql
-- PostgreSQL tables in Configuration Service database

-- Flow definitions table
CREATE TABLE flow_definitions (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    version VARCHAR(20) NOT NULL,
    description TEXT,
    definition_json JSONB NOT NULL,
    parameters_json JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    UNIQUE(name, version)
);

-- Flow dependencies tracking
CREATE TABLE flow_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flow_id VARCHAR(50) REFERENCES flow_definitions(id) ON DELETE CASCADE,
    depends_on_flow_id VARCHAR(50) REFERENCES flow_definitions(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50) NOT NULL, -- "prerequisite", "parallel", "conditional"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(flow_id, depends_on_flow_id)
);

-- Flow execution history
CREATE TABLE flow_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flow_id VARCHAR(50) REFERENCES flow_definitions(id) ON DELETE CASCADE,
    execution_id VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL, -- "running", "completed", "failed"
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    result_json JSONB,
    error_message TEXT,
    triggered_by VARCHAR(100)
);

-- Flow credential mappings
CREATE TABLE flow_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flow_id VARCHAR(50) REFERENCES flow_definitions(id) ON DELETE CASCADE,
    credential_key VARCHAR(100) NOT NULL,
    credential_type VARCHAR(50) NOT NULL, -- "api_key", "token", "secret"
    is_required BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(flow_id, credential_key)
);

-- Indexes for performance
CREATE INDEX idx_flow_definitions_type ON flow_definitions(type);
CREATE INDEX idx_flow_definitions_status ON flow_definitions(status);
CREATE INDEX idx_flow_executions_flow_id ON flow_executions(flow_id);
CREATE INDEX idx_flow_executions_status ON flow_executions(status);
```

#### **3. Flow Registry API Endpoints**
```yaml
# REST API integrated into Configuration Service (Port 8012)

POST /api/v1/flows:
  summary: Register new flow definition
  requestBody:
    content:
      application/json:
        schema:
          $ref: '#/components/schemas/FlowDefinition'
  responses:
    201:
      description: Flow registered successfully

GET /api/v1/flows:
  summary: List all flows with filtering
  parameters:
    - name: type
      in: query
      schema:
        $ref: '#/components/schemas/FlowType'
    - name: status
      in: query
      schema:
        $ref: '#/components/schemas/FlowStatus'
  responses:
    200:
      description: List of flows

GET /api/v1/flows/{flow_id}:
  summary: Get specific flow definition
  responses:
    200:
      description: Flow definition

PUT /api/v1/flows/{flow_id}:
  summary: Update flow definition
  responses:
    200:
      description: Flow updated

DELETE /api/v1/flows/{flow_id}:
  summary: Archive flow definition
  responses:
    204:
      description: Flow archived

# Flow execution endpoints
POST /api/v1/flows/{flow_id}/execute:
  summary: Execute flow with parameters
  requestBody:
    content:
      application/json:
        schema:
          type: object
          properties:
            parameters:
              type: object
            environment:
              type: string
  responses:
    202:
      description: Flow execution started

GET /api/v1/flows/{flow_id}/executions:
  summary: Get flow execution history
  responses:
    200:
      description: Execution history

# Flow dependency endpoints
GET /api/v1/flows/{flow_id}/dependencies:
  summary: Get flow dependency graph
  responses:
    200:
      description: Dependency graph

POST /api/v1/flows/{flow_id}/dependencies:
  summary: Add flow dependency
  responses:
    201:
      description: Dependency added
```

## 🔗 **Integration Strategy**

### **Phase 1: LangGraph Workflows Integration**
```python
# ai-orchestration service integration
from config_client import ConfigurationClient, FlowRegistryClient

class LangGraphWorkflowManager:
    def __init__(self):
        self.config_client = ConfigurationClient("http://configuration-service:8012")
        self.flow_registry = FlowRegistryClient("http://configuration-service:8012")

    async def register_workflow(self, workflow_definition):
        """Register LangGraph workflow in central registry"""
        flow_def = {
            "id": f"langgraph_{workflow_definition['name']}",
            "name": workflow_definition['name'],
            "type": "langgraph_workflow",
            "version": "1.0.0",
            "description": workflow_definition.get('description', ''),
            "definition_json": workflow_definition,
            "parameters": workflow_definition.get('parameters', {}),
            "credentials": workflow_definition.get('required_credentials', [])
        }
        return await self.flow_registry.register_flow(flow_def)

    async def execute_workflow(self, workflow_id, parameters=None):
        """Execute workflow using centralized credentials and config"""
        # Get flow definition from registry
        flow = await self.flow_registry.get_flow(workflow_id)

        # Get credentials from config service
        credentials = {}
        for cred_ref in flow['credentials']:
            credentials[cred_ref['key']] = await self.config_client.get_credential(
                cred_ref['key'], cred_ref['type']
            )

        # Execute workflow with centralized config
        execution_id = await self._execute_langgraph_workflow(
            flow['definition_json'],
            parameters or {},
            credentials
        )

        # Track execution in registry
        await self.flow_registry.track_execution(workflow_id, execution_id)
        return execution_id
```

### **Phase 2: AI Brain Flow Validator Integration**
```python
# shared/ai_brain_flow_validator.py integration
from config_client import FlowRegistryClient

class AIBrainFlowValidator:
    def __init__(self):
        self.flow_registry = FlowRegistryClient("http://configuration-service:8012")

    async def register_validation_flow(self, validation_name, validation_rules):
        """Register validation flow in central registry"""
        flow_def = {
            "id": f"ai_brain_validation_{validation_name}",
            "name": f"AI Brain Validation: {validation_name}",
            "type": "ai_brain_validation",
            "version": "1.0.0",
            "description": f"Validation flow for {validation_name}",
            "definition_json": {
                "validation_rules": validation_rules,
                "validator_type": "ai_brain"
            },
            "parameters": [],
            "credentials": []
        }
        return await self.flow_registry.register_flow(flow_def)

    async def validate_architecture(self, architecture_definition):
        """Validate architecture using registered flows"""
        # Get validation flows from registry
        validation_flows = await self.flow_registry.list_flows(
            type="ai_brain_validation",
            status="active"
        )

        # Execute validations
        results = {}
        for flow in validation_flows:
            result = await self._execute_validation(
                flow['definition_json']['validation_rules'],
                architecture_definition
            )
            results[flow['name']] = result

        return results
```

### **Phase 3: Chain Mapping Integration**
```python
# Integration with docs/chain-mapping-specifications.md
from config_client import FlowRegistryClient

class ChainMappingManager:
    def __init__(self):
        self.flow_registry = FlowRegistryClient("http://configuration-service:8012")

    async def register_chain_mappings(self):
        """Register all 30 chain mappings as flows"""
        chain_specs = await self._load_chain_specifications()

        for chain_spec in chain_specs:
            flow_def = {
                "id": f"chain_mapping_{chain_spec['id']}",
                "name": f"Chain Mapping: {chain_spec['name']}",
                "type": "chain_mapping",
                "version": "1.0.0",
                "description": chain_spec['description'],
                "definition_json": {
                    "nodes": chain_spec['nodes'],
                    "edges": chain_spec['edges'],
                    "dependencies": chain_spec['dependencies']
                },
                "parameters": chain_spec.get('parameters', []),
                "credentials": chain_spec.get('credentials', [])
            }
            await self.flow_registry.register_flow(flow_def)

    async def execute_chain(self, chain_id, input_data):
        """Execute chain mapping with centralized tracking"""
        flow = await self.flow_registry.get_flow(f"chain_mapping_{chain_id}")

        # Execute chain with dependency tracking
        execution_id = await self._execute_chain_flow(
            flow['definition_json'],
            input_data
        )

        # Track in registry
        await self.flow_registry.track_execution(flow['id'], execution_id)
        return execution_id
```

## 📋 **Implementation Timeline**

### **Phase 0 (Week 0): Configuration Service Enhancement**
- **Day 4**: Implement Flow Registry core functionality
  - Database schema creation
  - Basic API endpoints
  - Flow definition CRUD operations
  - Integration with existing Configuration Service

### **Phase 1 (Week 1-3): Service Integration**
- **Week 1**: LangGraph Workflows integration
  - Modify ai-orchestration service to use Flow Registry
  - Migrate existing workflows to central registry
  - Test workflow execution with centralized credentials

### **Phase 2 (Week 4-7): AI Pipeline Integration**
- **Week 4**: AI Brain Flow Validator integration
  - Integrate validation flows with registry
  - Centralize validation flow definitions
  - **Week 5-7**: Chain Mapping integration during ML development
  - Register all 30 chain mappings as flows
  - Implement dependency tracking

### **Phase 3 (Week 8-9): User Features**
- Flow monitoring in dashboard
- Flow execution tracking in Telegram bot

### **Phase 4 (Week 10-12): Production**
- Production flow monitoring
- Flow performance optimization
- Flow dependency analysis

## 🎯 **Benefits Achieved**

### **Centralization Benefits**
✅ **Single Source of Truth**: All flow definitions in one place
✅ **Unified Credential Management**: All flow credentials managed centrally
✅ **Dependency Tracking**: Clear visibility of flow dependencies
✅ **Consistent Execution**: Standardized flow execution patterns
✅ **Version Control**: Flow versioning and change tracking

### **Operational Benefits**
✅ **Easier Maintenance**: Modify flows in one place, affect all consumers
✅ **Better Monitoring**: Central flow execution tracking and metrics
✅ **Improved Security**: Centralized credential management and audit trails
✅ **Enhanced Debugging**: Flow execution history and dependency analysis
✅ **Scalable Integration**: Easy addition of new flow types and systems

### **Development Benefits**
✅ **Simplified Integration**: Standard API for all flow operations
✅ **Reduced Duplication**: Reuse flow definitions across services
✅ **Better Testing**: Centralized flow validation and testing
✅ **Documentation**: Self-documenting flow registry with metadata

## 📊 **Cost Impact**

- **Additional Development**: +1 day (Day 4 of Phase 0)
- **Total Phase 0**: 5 days instead of 4 days
- **Additional Cost**: +$1K (total Phase 0: $6K instead of $5K)
- **Total Project Cost**: $90K remains unchanged (absorbed in Phase 0)
- **Long-term Savings**: Reduced maintenance and integration complexity

## ✅ **Success Criteria**

### **Technical Success**
- All existing flow systems integrated with central registry
- Flow execution performance maintained or improved
- Zero downtime migration of existing flows
- Comprehensive dependency tracking operational

### **Operational Success**
- Single configuration point for all flows
- Centralized credential management working
- Flow monitoring and alerting functional
- Development team trained on new system

**Status**: ✅ **READY FOR IMPLEMENTATION IN PHASE 0**