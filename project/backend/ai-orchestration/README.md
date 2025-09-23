# AI Orchestration Framework

A flexible, enterprise-grade AI model provider framework that supports multiple AI services through URL + token configuration with comprehensive monitoring, cost tracking, and multi-tenant support.

## Features

### Core Capabilities
- **Multi-Provider Support**: OpenAI, Anthropic, Google AI, Local Models (Ollama, LM Studio), Custom APIs
- **Simple Configuration**: URL + token pattern for easy integration
- **Provider Abstraction**: Standardized interface across all AI providers
- **Automatic Failover**: Intelligent provider selection and failover mechanisms
- **Load Balancing**: Distribute requests across multiple providers

### Enterprise Features
- **Multi-Tenant Architecture**: Isolated provider configurations per tenant
- **Cost Tracking**: Real-time cost monitoring with budget alerts
- **Rate Limiting**: Token bucket rate limiting with per-provider/tenant controls
- **Health Monitoring**: Continuous provider health checks and performance metrics
- **Configuration Management**: Encrypted configuration storage with change detection

### Monitoring & Analytics
- **Performance Metrics**: Latency, error rates, throughput tracking
- **Cost Analytics**: Usage patterns, cost projections, budget management
- **Health Dashboard**: Provider status, uptime monitoring
- **Audit Trail**: Complete request/response logging and analytics

## Quick Start

### Installation

```bash
npm install @your-org/ai-orchestration
```

### Basic Usage

```javascript
const { AIOrchestrator } = require('@your-org/ai-orchestration');

// Initialize orchestrator
const orchestrator = new AIOrchestrator();
await orchestrator.initialize();

// Create OpenAI provider
await orchestrator.createProvider({
    type: 'openai',
    name: 'gpt-provider',
    tenant: 'my-app',
    apiKey: process.env.OPENAI_API_KEY,
    defaultModel: 'gpt-3.5-turbo'
});

// Generate chat completion
const response = await orchestrator.generateChatCompletion([
    { role: 'user', content: 'Hello, world!' }
], {
    tenant: 'my-app',
    maxTokens: 100
});

console.log('Response:', response.content);
console.log('Cost:', response.cost);
console.log('Provider:', response.provider);
```

### API Server

```javascript
const express = require('express');
const { AIOrchestrator, createAPI } = require('@your-org/ai-orchestration');

const app = express();
const orchestrator = new AIOrchestrator();
await orchestrator.initialize();

// Add AI Orchestration API
const api = createAPI(orchestrator);
app.use('/api/ai', api.getRouter());

app.listen(3000, () => {
    console.log('AI Orchestration API running on port 3000');
});
```

## Supported Providers

### OpenAI
```javascript
await orchestrator.createProvider({
    type: 'openai',
    name: 'openai-gpt4',
    apiKey: 'your-openai-key',
    defaultModel: 'gpt-4',
    organization: 'your-org-id' // optional
});
```

### Anthropic Claude
```javascript
await orchestrator.createProvider({
    type: 'anthropic',
    name: 'claude-sonnet',
    apiKey: 'your-anthropic-key',
    defaultModel: 'claude-3-sonnet-20240229',
    anthropicVersion: '2023-06-01'
});
```

### Google AI (Gemini)
```javascript
await orchestrator.createProvider({
    type: 'google',
    name: 'gemini-pro',
    apiKey: 'your-google-key',
    defaultModel: 'gemini-pro'
});
```

### Local Models (Ollama)
```javascript
await orchestrator.createProvider({
    type: 'local',
    name: 'local-llama',
    baseUrl: 'http://localhost:11434',
    serverType: 'ollama',
    defaultModel: 'llama2'
});
```

### Custom APIs
```javascript
await orchestrator.createProvider({
    type: 'custom',
    name: 'my-api',
    baseUrl: 'https://api.mycompany.com/v1',
    apiKey: 'my-key',
    requestFormat: 'openai',
    responseFormat: 'openai',
    endpoints: {
        chatCompletion: '/chat/completions',
        embedding: '/embeddings'
    }
});
```

## Multi-Tenant Support

### Tenant Isolation
```javascript
// Create providers for different tenants
await orchestrator.createProvider({
    type: 'openai',
    name: 'gpt-provider',
    tenant: 'tenant-a',
    apiKey: 'tenant-a-key'
});

await orchestrator.createProvider({
    type: 'anthropic',
    name: 'claude-provider',
    tenant: 'tenant-b',
    apiKey: 'tenant-b-key'
});

// Use tenant-specific providers
const responseA = await orchestrator.generateChatCompletion(messages, {
    tenant: 'tenant-a'
});

const responseB = await orchestrator.generateChatCompletion(messages, {
    tenant: 'tenant-b'
});
```

### Budget Management
```javascript
// Set budget limits per tenant
orchestrator.setBudget('tenant-a', {
    daily: 50.0,
    monthly: 1000.0,
    alertEmails: ['admin@tenant-a.com'],
    enforceHardLimit: true
});

// Get cost summary
const costs = orchestrator.getCostSummary('tenant-a');
console.log('Total cost:', costs.totalCost);
console.log('Monthly projection:', costs.monthlyProjection);
```

## Rate Limiting

### Provider-Level Limits
```javascript
orchestrator.setRateLimit('openai-provider', {
    requestsPerSecond: 10,
    requestsPerMinute: 300,
    requestsPerHour: 1000,
    tokensPerSecond: 1000,
    concurrentRequests: 5
}, 'provider');
```

### Tenant-Level Limits
```javascript
orchestrator.setRateLimit('tenant-a', {
    requestsPerSecond: 20,
    requestsPerMinute: 600,
    tokensPerSecond: 2000
}, 'tenant');
```

## Health Monitoring

### Check Provider Health
```javascript
// Individual provider health
const health = orchestrator.getProviderHealth('gpt-provider', 'my-app');
console.log('Healthy:', health.healthy);
console.log('Latency:', health.avgLatency);
console.log('Error rate:', health.errorRate);

// Overall health summary
const summary = orchestrator.getHealthSummary();
console.log('Total providers:', summary.totalProviders);
console.log('Healthy providers:', summary.healthy);
```

### Test Connectivity
```javascript
const result = await orchestrator.testProvider('gpt-provider', 'my-app');
console.log('Connection test:', result.success);
```

## Configuration Templates

### Use Built-in Templates
```javascript
// Create from OpenAI template
await orchestrator.createProviderFromTemplate('openai', 'my-openai', 'my-app', {
    OPENAI_API_KEY: 'your-key',
    OPENAI_ORG_ID: 'your-org'
});

// Create from custom template
await orchestrator.createProviderFromTemplate('custom', 'my-custom', 'my-app', {
    CUSTOM_API_URL: 'https://api.example.com',
    CUSTOM_API_KEY: 'your-key'
});
```

### Register Custom Templates
```javascript
orchestrator.configManager.registerTemplate('my-template', {
    baseUrl: '{{API_URL}}',
    apiKey: '{{API_KEY}}',
    requestFormat: 'openai',
    responseFormat: 'openai',
    customHeaders: {
        'X-Custom-Header': '{{CUSTOM_VALUE}}'
    }
});
```

## API Endpoints

The framework provides a comprehensive REST API:

### Provider Management
- `POST /api/ai/providers` - Create provider
- `GET /api/ai/providers` - List providers
- `GET /api/ai/providers/:name` - Get provider details
- `PUT /api/ai/providers/:name` - Update provider
- `DELETE /api/ai/providers/:name` - Remove provider
- `POST /api/ai/providers/:name/test` - Test provider

### AI Generation
- `POST /api/ai/chat/completions` - Generate chat completion
- `POST /api/ai/completions` - Generate text completion
- `POST /api/ai/embeddings` - Generate embeddings

### Monitoring
- `GET /api/ai/health` - Overall health status
- `GET /api/ai/health/:name` - Provider health
- `GET /api/ai/metrics` - Performance metrics
- `GET /api/ai/statistics` - System statistics

### Cost Management
- `GET /api/ai/costs` - Cost summary
- `GET /api/ai/costs/analytics` - Cost analytics
- `POST /api/ai/budgets` - Set budget
- `GET /api/ai/budgets/:tenant` - Get budget

### Rate Limiting
- `GET /api/ai/rate-limits` - Rate limit status
- `POST /api/ai/rate-limits` - Set rate limits
- `DELETE /api/ai/rate-limits/:provider/:tenant` - Reset limits

## Configuration

### Environment Variables
```bash
# Default API keys (can be overridden per provider)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key

# Configuration
AI_CONFIG_DIR=./config
AI_ENCRYPTION_KEY=your-encryption-key

# Monitoring
AI_HEALTH_CHECK_INTERVAL=60000
AI_COST_ALERT_WEBHOOK=https://your-webhook.com
```

### Configuration Files
The framework stores configurations in encrypted JSON files:

```
config/
├── defaults.json          # Default provider settings
├── tenant-default.json    # Default tenant configuration
├── tenant-myapp.json      # Tenant-specific configuration
└── templates.json         # Custom templates
```

## Monitoring & Analytics

### Performance Metrics
```javascript
const metrics = orchestrator.getStatistics();
console.log('Request count:', metrics.providers.totalRequests);
console.log('Average latency:', metrics.providers.avgLatency);
console.log('Error rate:', metrics.providers.errorRate);
```

### Cost Analytics
```javascript
const analytics = orchestrator.getAnalytics('7d', 'my-app');
console.log('7-day cost:', analytics.totalCost);
console.log('Token usage:', analytics.totalTokens);
console.log('Top models:', analytics.topModels);
```

### Export/Import
```javascript
// Export configuration and data
const exportData = await orchestrator.exportData({
    includeSecrets: false,
    includeHistory: true
});

// Import to another instance
await newOrchestrator.importData(exportData);
```

## Error Handling

The framework provides comprehensive error handling:

```javascript
try {
    const response = await orchestrator.generateChatCompletion(messages, options);
} catch (error) {
    if (error.message.includes('Rate limit exceeded')) {
        // Handle rate limiting
        console.log('Rate limited, retry after:', error.retryAfter);
    } else if (error.message.includes('No healthy providers')) {
        // Handle provider outage
        console.log('All providers unavailable');
    } else {
        // Handle other errors
        console.error('Generation failed:', error.message);
    }
}
```

## Advanced Features

### Custom Adapters
```javascript
// Create custom request/response adapter
const customAdapter = orchestrator.adapter.createCustomAdapter('my-format', {
    requestTransform: (request) => {
        // Transform request to provider format
        return transformedRequest;
    },
    responseTransform: (response) => {
        // Transform response to standard format
        return transformedResponse;
    }
});
```

### Hooks and Events
```javascript
// Register configuration change hooks
orchestrator.configManager.registerHook('config.updated', async (data) => {
    console.log('Provider updated:', data.provider);
});

orchestrator.configManager.registerHook('config.removed', async (data) => {
    console.log('Provider removed:', data.provider);
});
```

### Custom Validators
```javascript
// Register custom configuration validator
orchestrator.configManager.registerValidator('my-provider', async (config) => {
    const errors = [];

    if (!config.customField) {
        errors.push('customField is required');
    }

    return {
        valid: errors.length === 0,
        errors
    };
});
```

## Testing

### Unit Tests
```bash
npm test
```

### Integration Tests
```bash
npm run test:integration
```

### Load Testing
```bash
npm run test:load
```

## Performance

The framework is designed for high performance:

- **Concurrent Processing**: Multiple requests handled simultaneously
- **Connection Pooling**: Efficient HTTP connection management
- **Caching**: Response caching for improved latency
- **Load Balancing**: Distribute load across providers
- **Circuit Breakers**: Automatic failover for unhealthy providers

### Benchmarks
- **Throughput**: 1000+ requests/second per provider
- **Latency**: <10ms framework overhead
- **Memory**: <100MB for 100 providers
- **Startup**: <2s initialization time

## Security

### Encryption
- API keys encrypted at rest using AES-256
- Configuration files encrypted
- Secure key management

### Authentication
- JWT token support for API endpoints
- Role-based access control (RBAC)
- Tenant isolation

### Audit Logging
- Complete request/response logging
- Configuration change tracking
- Cost and usage auditing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Development Setup
```bash
git clone https://github.com/your-org/ai-orchestration
cd ai-orchestration
npm install
npm run dev
```

## License

MIT License - see LICENSE file for details.

## Support

- Documentation: [https://docs.ai-orchestration.com](https://docs.ai-orchestration.com)
- Issues: [GitHub Issues](https://github.com/your-org/ai-orchestration/issues)
- Discussions: [GitHub Discussions](https://github.com/your-org/ai-orchestration/discussions)
- Email: support@ai-orchestration.com

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.