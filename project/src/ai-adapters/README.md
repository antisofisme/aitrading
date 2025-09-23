# AI Model Adapter System

A standardized interface for seamless AI provider integration with simple URL + token configuration, automatic fallback mechanisms, and comprehensive monitoring.

## Features

- 🔗 **Unified Interface**: Single API for all AI providers (OpenAI, Anthropic, Google AI, Custom APIs, Local models)
- 🔄 **Automatic Fallback**: Smart fallback system with retry logic and circuit breakers
- 📊 **Cost Tracking**: Real-time cost monitoring with budget alerts and detailed breakdowns
- ⚡ **Performance Monitoring**: Response time tracking, success rates, and performance analytics
- 🎚️ **Load Balancing**: Multiple strategies (round-robin, least latency, health-based)
- 🔒 **Rate Limiting**: Built-in rate limiting and quota management
- 🏥 **Health Checks**: Continuous health monitoring with automatic recovery
- 📝 **Configuration Management**: File-based, environment variable, and programmatic configuration
- 🧪 **Comprehensive Testing**: Full test suite with mocks and integration tests

## Quick Start

### Simple Single Provider

```typescript
import { createSimpleAdapter } from './ai-adapters';

// Create OpenAI adapter
const adapter = createSimpleAdapter('openai', 'your-api-key', {
  model: 'gpt-3.5-turbo',
  timeout: 30000
});

// Make a request
const result = await adapter.predict({
  prompt: 'Explain quantum computing',
  parameters: {
    temperature: 0.7,
    maxTokens: 200
  }
});

console.log(result.content);
```

### Multi-Provider with Fallback

```typescript
import { createMultiProviderAdapter } from './ai-adapters';

const adapter = createMultiProviderAdapter([
  {
    provider: 'openai',
    apiKey: 'openai-key',
    model: 'gpt-4'
  },
  {
    provider: 'anthropic',
    apiKey: 'anthropic-key',
    model: 'claude-3-sonnet-20240229'
  }
], {
  fallbackEnabled: true,
  loadBalancing: { type: 'round_robin' },
  costTracking: true,
  monitoring: true
});

const result = await adapter.predict({
  prompt: 'Write a creative story'
});
```

### Custom API Integration

```typescript
import { createAdapterFromUrl } from './ai-adapters';

const adapter = createAdapterFromUrl(
  'https://api.yourprovider.com/v1/generate',
  'your-api-key',
  {
    options: {
      requestMapping: {
        promptField: 'input.text',
        modelField: 'model',
        maxTokensField: 'max_tokens'
      },
      responseMapping: {
        contentField: 'output.text',
        usageTokensField: 'usage.total_tokens'
      }
    }
  }
);
```

## Supported Providers

### OpenAI
- GPT-4, GPT-3.5 Turbo
- Full chat completions support
- Streaming responses
- Function calling

### Anthropic
- Claude 3 (Opus, Sonnet, Haiku)
- Claude 2.1, 2.0, Instant
- System messages
- Multi-turn conversations

### Google AI
- Gemini Pro, Gemini Pro Vision
- PaLM 2 models
- Safety settings
- Content filtering

### Local Models
- Ollama integration
- llama.cpp support
- vLLM compatibility
- Text Generation Inference (TGI)
- Custom local endpoints

### Custom APIs
- Generic REST API adapter
- Configurable request/response mapping
- Custom authentication methods
- Flexible field mapping

## Advanced Features

### Cost Tracking

```typescript
const costTracker = adapter.getCostTracking();

// Set budget limits
costTracker.config.monthlyBudget = 100; // $100/month
costTracker.config.dailyBudget = 10;    // $10/day

// Get cost breakdown
const costs = costTracker.getCostsByProvider();
const stats = costTracker.getUsageStats();

console.log(`Total cost: $${stats.totalCost}`);
console.log(`Average per request: $${stats.averageCostPerRequest}`);
```

### Performance Monitoring

```typescript
const monitor = adapter.getPerformanceMonitor();

// Add alert rules
monitor.addAlertRule({
  name: 'High Response Time',
  condition: {
    metric: 'timing.averageResponseTime',
    operator: '>',
    value: 5000 // 5 seconds
  },
  action: 'log',
  enabled: true
});

// Generate reports
const report = monitor.generateReport();
console.log(report);
```

### Load Balancing Strategies

```typescript
const adapter = new AdapterOrchestrator({
  adapters: providerMap,
  loadBalancing: {
    type: 'least_latency', // or 'round_robin', 'health_based', 'random'
    weights: {
      'openai': 0.6,
      'anthropic': 0.4
    }
  }
});
```

### Rate Limiting

```typescript
const config: ProviderConfig = {
  name: 'openai',
  baseUrl: 'https://api.openai.com/v1',
  apiKey: 'your-key',
  rateLimits: {
    requestsPerMinute: 60,
    tokensPerMinute: 90000
  }
};
```

## Configuration Management

### File-based Configuration

```typescript
import { createAdapterFromConfig } from './ai-adapters';

const adapter = await createAdapterFromConfig('./config/ai-adapters.json');
```

Example configuration file:

```json
{
  "defaultProvider": "openai",
  "providers": {
    "openai": {
      "name": "openai",
      "baseUrl": "https://api.openai.com/v1",
      "apiKey": "${OPENAI_API_KEY}",
      "defaultModel": "gpt-3.5-turbo",
      "rateLimits": {
        "requestsPerMinute": 60,
        "tokensPerMinute": 90000
      }
    },
    "anthropic": {
      "name": "anthropic",
      "baseUrl": "https://api.anthropic.com/v1",
      "apiKey": "${ANTHROPIC_API_KEY}",
      "defaultModel": "claude-3-sonnet-20240229"
    }
  },
  "fallback": {
    "enabled": true,
    "providers": ["openai", "anthropic"],
    "triggers": ["error", "timeout", "rate_limit"]
  },
  "costTracking": {
    "enabled": true,
    "monthlyBudget": 100,
    "alertThresholds": [50, 75, 90]
  }
}
```

### Environment Variables

```bash
# Global settings
AI_ADAPTER_DEFAULT_PROVIDER=openai
AI_ADAPTER_TIMEOUT=30000
AI_ADAPTER_DEBUG=false

# Provider configurations
AI_ADAPTER_OPENAI_API_KEY=your-openai-key
AI_ADAPTER_OPENAI_BASE_URL=https://api.openai.com/v1
AI_ADAPTER_OPENAI_DEFAULT_MODEL=gpt-3.5-turbo

AI_ADAPTER_ANTHROPIC_API_KEY=your-anthropic-key
AI_ADAPTER_ANTHROPIC_BASE_URL=https://api.anthropic.com/v1
```

## Error Handling

The adapter system provides comprehensive error handling with categorized error types:

```typescript
try {
  const result = await adapter.predict(input);
} catch (error) {
  if (error.type === 'rate_limit') {
    console.log('Rate limit exceeded, retrying...');
  } else if (error.type === 'auth') {
    console.log('Authentication failed');
  } else if (error.type === 'network') {
    console.log('Network error, checking fallback...');
  }
}
```

Error types:
- `auth`: Authentication/authorization errors
- `rate_limit`: Rate limiting errors (retryable)
- `timeout`: Request timeout errors (retryable)
- `network`: Network/connectivity errors (retryable)
- `validation`: Input validation errors
- `unknown`: Unclassified errors

## Testing

```bash
# Run all tests
npm test

# Run specific test suites
npm run test:unit
npm run test:integration

# Run with coverage
npm run test:coverage
```

## Examples

See the `/examples` directory for comprehensive usage examples:

- Basic usage with single provider
- Multi-provider setup with fallback
- Chat conversations
- Custom API integration
- Local model usage
- Performance monitoring
- Cost tracking

## API Reference

### Core Interfaces

#### AIInput
```typescript
interface AIInput {
  prompt?: string;
  systemMessage?: string;
  messages?: ChatMessage[];
  parameters?: {
    temperature?: number;
    maxTokens?: number;
    topP?: number;
    topK?: number;
    // ... other parameters
  };
  stream?: boolean;
  customHeaders?: Record<string, string>;
}
```

#### AIOutput
```typescript
interface AIOutput {
  content: string;
  choices?: string[];
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
  raw?: any;
  metadata?: {
    model: string;
    provider: string;
    requestId?: string;
    finishReason?: string;
  };
}
```

#### AIProvider
```typescript
interface AIProvider {
  readonly name: string;
  readonly config: ProviderConfig;

  predict(input: AIInput): Promise<AIOutput>;
  healthCheck(): Promise<HealthStatus>;
  getUsage(): UsageMetrics;
  getRateLimit(): RateLimitInfo;
  resetUsage(): void;
  validateConfig(): Promise<boolean>;
}
```

### Factory Functions

- `createSimpleAdapter(provider, apiKey, options?)`: Create single provider adapter
- `createMultiProviderAdapter(configs, options?)`: Create multi-provider adapter
- `createAdapterFromUrl(url, token, options?)`: Create adapter from URL
- `createAdapterFromConfig(configPath, options?)`: Create from configuration file

### Utility Classes

- `AdapterOrchestrator`: Manages multiple adapters with load balancing and fallback
- `CostTracker`: Tracks costs and manages budgets
- `PerformanceMonitor`: Monitors performance metrics and alerts
- `RateLimiter`: Manages rate limiting and quotas
- `ConfigManager`: Handles configuration loading and validation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

- Documentation: [GitHub Wiki](link-to-wiki)
- Issues: [GitHub Issues](link-to-issues)
- Examples: See `/examples` directory
- Tests: See `/tests` directory

---

Built with ❤️ for seamless AI integration