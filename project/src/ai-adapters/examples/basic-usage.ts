/**
 * Basic usage examples for AI Adapter system
 */

import {
  createSimpleAdapter,
  createMultiProviderAdapter,
  createAdapterFromUrl,
  AIInput
} from '../index.js';

/**
 * Example 1: Simple single-provider setup
 */
async function basicUsageExample() {
  console.log('=== Basic Usage Example ===');

  // Create a simple OpenAI adapter
  const adapter = createSimpleAdapter('openai', process.env.OPENAI_API_KEY || 'your-api-key', {
    model: 'gpt-3.5-turbo',
    timeout: 30000
  });

  // Make a simple request
  const input: AIInput = {
    prompt: 'Explain quantum computing in simple terms',
    parameters: {
      temperature: 0.7,
      maxTokens: 200
    }
  };

  try {
    const result = await adapter.predict(input);
    console.log('Response:', result.content);
    console.log('Usage:', result.usage);
    console.log('Cost estimate: $', adapter.getCostTracking()?.getTotalCosts());
  } catch (error) {
    console.error('Error:', error);
  }

  // Check adapter health
  const health = await adapter.healthCheck();
  console.log('Health:', health.healthy ? 'Good' : 'Poor');
}

/**
 * Example 2: Multi-provider with fallback
 */
async function multiProviderExample() {
  console.log('\n=== Multi-Provider Example ===');

  // Create adapter with multiple providers and fallback
  const adapter = createMultiProviderAdapter([
    {
      provider: 'openai',
      apiKey: process.env.OPENAI_API_KEY || 'openai-key',
      model: 'gpt-3.5-turbo'
    },
    {
      provider: 'anthropic',
      apiKey: process.env.ANTHROPIC_API_KEY || 'anthropic-key',
      model: 'claude-3-sonnet-20240229'
    },
    {
      provider: 'google',
      apiKey: process.env.GOOGLE_API_KEY || 'google-key',
      model: 'gemini-pro'
    }
  ], {
    fallbackEnabled: true,
    loadBalancing: { type: 'round_robin' },
    costTracking: true,
    monitoring: true
  });

  const input: AIInput = {
    prompt: 'Write a short poem about artificial intelligence',
    parameters: {
      temperature: 0.8,
      maxTokens: 150
    }
  };

  try {
    // Make multiple requests to see load balancing
    for (let i = 0; i < 3; i++) {
      const result = await adapter.predict(input);
      console.log(`Request ${i + 1} - Provider: ${result.metadata?.provider}`);
      console.log(`Response: ${result.content.substring(0, 100)}...`);
    }

    // Get performance metrics
    const monitor = adapter.getPerformanceMonitor();
    if (monitor) {
      const metrics = monitor.getMetrics();
      console.log('Performance metrics:', Object.keys(metrics));
    }
  } catch (error) {
    console.error('Error:', error);
  }
}

/**
 * Example 3: Chat conversation
 */
async function chatExample() {
  console.log('\n=== Chat Conversation Example ===');

  const adapter = createSimpleAdapter('openai', process.env.OPENAI_API_KEY || 'your-api-key');

  // Start a conversation
  const conversation: AIInput = {
    systemMessage: 'You are a helpful AI assistant who gives concise answers.',
    messages: [
      { role: 'user', content: 'Hello! What can you help me with?' }
    ],
    parameters: {
      temperature: 0.7,
      maxTokens: 100
    }
  };

  try {
    let result = await adapter.predict(conversation);
    console.log('Assistant:', result.content);

    // Continue conversation
    conversation.messages?.push(
      { role: 'assistant', content: result.content },
      { role: 'user', content: 'Can you explain machine learning briefly?' }
    );

    result = await adapter.predict(conversation);
    console.log('Assistant:', result.content);

    // Show conversation cost
    const costTracker = adapter.getCostTracking();
    if (costTracker) {
      const stats = costTracker.getUsageStats();
      console.log(`Total conversation cost: $${stats.totalCost.toFixed(6)}`);
      console.log(`Average cost per message: $${stats.averageCostPerRequest.toFixed(6)}`);
    }
  } catch (error) {
    console.error('Error:', error);
  }
}

/**
 * Example 4: Custom API integration
 */
async function customAPIExample() {
  console.log('\n=== Custom API Example ===');

  // Example with a hypothetical custom API
  const adapter = createAdapterFromUrl(
    'https://api.example.com/v1/generate',
    'your-api-key',
    {
      timeout: 30000,
      options: {
        requestMapping: {
          promptField: 'input.text',
          modelField: 'model_name',
          maxTokensField: 'generation.max_tokens',
          temperatureField: 'generation.temperature'
        },
        responseMapping: {
          contentField: 'output.text',
          usageTokensField: 'usage.total_tokens',
          finishReasonField: 'status'
        }
      }
    }
  );

  const input: AIInput = {
    prompt: 'Generate a creative story opening',
    parameters: {
      temperature: 0.9,
      maxTokens: 200
    }
  };

  try {
    const result = await adapter.predict(input);
    console.log('Custom API Response:', result.content);
  } catch (error) {
    console.error('Custom API Error:', error);
  }
}

/**
 * Example 5: Local model usage
 */
async function localModelExample() {
  console.log('\n=== Local Model Example ===');

  // Example with Ollama local model
  const { createLocalAdapter } = await import('../index.js');

  const adapter = createLocalAdapter(
    'http://localhost:11434',
    'llama2',
    'ollama',
    {
      timeout: 60000 // Local models might be slower
    }
  );

  const input: AIInput = {
    prompt: 'Explain the benefits of running AI models locally',
    parameters: {
      temperature: 0.7,
      maxTokens: 300
    }
  };

  try {
    // Check if local model is available
    const health = await adapter.healthCheck();
    if (!health.healthy) {
      console.log('Local model not available. Make sure Ollama is running.');
      return;
    }

    const result = await adapter.predict(input);
    console.log('Local Model Response:', result.content);
    console.log('Response time:', health.responseTime + 'ms');
  } catch (error) {
    console.error('Local Model Error:', error);
  }
}

/**
 * Example 6: Performance monitoring and alerts
 */
async function monitoringExample() {
  console.log('\n=== Performance Monitoring Example ===');

  const adapter = createSimpleAdapter('openai', process.env.OPENAI_API_KEY || 'your-api-key');
  const monitor = adapter.getPerformanceMonitor();

  if (monitor) {
    // Add performance alert rules
    monitor.addAlertRule({
      name: 'High Response Time',
      condition: {
        metric: 'timing.averageResponseTime',
        operator: '>',
        value: 5000, // 5 seconds
        duration: 60 // Over 1 minute
      },
      action: 'log',
      enabled: true
    });

    monitor.addAlertRule({
      name: 'Low Success Rate',
      condition: {
        metric: 'reliability.successRate',
        operator: '<',
        value: 95, // Less than 95%
        duration: 300 // Over 5 minutes
      },
      action: 'log',
      enabled: true
    });

    // Make some test requests
    const inputs = [
      'What is artificial intelligence?',
      'Explain machine learning',
      'What are neural networks?'
    ];

    for (const prompt of inputs) {
      try {
        const result = await adapter.predict({ prompt });
        console.log(`✓ Request completed: ${prompt.substring(0, 30)}...`);
      } catch (error) {
        console.log(`✗ Request failed: ${prompt.substring(0, 30)}...`);
      }
    }

    // Generate performance report
    const report = monitor.generateReport(undefined, undefined, 'text');
    console.log('\nPerformance Report:');
    console.log(report);

    // Check for alerts
    const alerts = monitor.getAlerts(false); // Unacknowledged alerts
    if (alerts.length > 0) {
      console.log('\nActive Alerts:');
      alerts.forEach(alert => {
        console.log(`- ${alert.severity.toUpperCase()}: ${alert.message}`);
      });
    } else {
      console.log('\nNo active alerts.');
    }
  }
}

/**
 * Example 7: Cost tracking and budget management
 */
async function costTrackingExample() {
  console.log('\n=== Cost Tracking Example ===');

  const adapter = createSimpleAdapter('openai', process.env.OPENAI_API_KEY || 'your-api-key');
  const costTracker = adapter.getCostTracking();

  if (costTracker) {
    // Make several requests to accumulate some costs
    const testPrompts = [
      'Write a haiku about programming',
      'Explain the concept of recursion',
      'What are the benefits of cloud computing?',
      'Describe the process of photosynthesis'
    ];

    for (const prompt of testPrompts) {
      try {
        await adapter.predict({
          prompt,
          parameters: { maxTokens: 100 }
        });
      } catch (error) {
        console.log(`Request failed: ${prompt}`);
      }
    }

    // Get cost breakdown
    const totalCosts = costTracker.getTotalCosts();
    const costsByProvider = costTracker.getCostsByProvider();
    const usageStats = costTracker.getUsageStats();

    console.log(`Total costs: $${totalCosts.toFixed(6)}`);
    console.log('Costs by provider:', costsByProvider);
    console.log(`Average cost per request: $${usageStats.averageCostPerRequest.toFixed(6)}`);
    console.log(`Average cost per token: $${usageStats.averageCostPerToken.toFixed(8)}`);

    // Check budget status
    const budgetStatus = costTracker.getBudgetStatus();
    console.log('\nBudget Status:');
    console.log(`Monthly: $${budgetStatus.monthly.spent.toFixed(6)} / $${budgetStatus.monthly.budget} (${budgetStatus.monthly.percentage.toFixed(1)}%)`);
    console.log(`Daily: $${budgetStatus.daily.spent.toFixed(6)} / $${budgetStatus.daily.budget} (${budgetStatus.daily.percentage.toFixed(1)}%)`);

    // Export cost data
    const costReport = costTracker.exportCosts('csv');
    console.log('\nCost report (first 200 chars):');
    console.log(costReport.substring(0, 200) + '...');
  }
}

/**
 * Run all examples
 */
async function runAllExamples() {
  try {
    await basicUsageExample();
    await multiProviderExample();
    await chatExample();
    await customAPIExample();
    await localModelExample();
    await monitoringExample();
    await costTrackingExample();
  } catch (error) {
    console.error('Example execution error:', error);
  }
}

// Export examples for individual usage
export {
  basicUsageExample,
  multiProviderExample,
  chatExample,
  customAPIExample,
  localModelExample,
  monitoringExample,
  costTrackingExample,
  runAllExamples
};

// Run all examples if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runAllExamples();
}