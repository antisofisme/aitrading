/**
 * AI Orchestration Framework - Usage Examples
 * Demonstrates how to use the AI provider framework
 */

const { AIOrchestrator } = require('../index');
const { createAPI } = require('../api/routes');
const express = require('express');

async function basicUsageExample() {
    console.log('=== Basic Usage Example ===');

    // Initialize the orchestrator
    const orchestrator = new AIOrchestrator({
        config: {
            configDir: './config'
        }
    });

    await orchestrator.initialize();

    try {
        // Create an OpenAI provider
        const openaiProvider = await orchestrator.createProvider({
            type: 'openai',
            name: 'gpt-provider',
            tenant: 'my-app',
            apiKey: process.env.OPENAI_API_KEY || 'your-openai-key',
            baseUrl: 'https://api.openai.com/v1',
            defaultModel: 'gpt-3.5-turbo'
        });

        console.log('OpenAI provider created:', openaiProvider.name);

        // Create an Anthropic provider
        const anthropicProvider = await orchestrator.createProvider({
            type: 'anthropic',
            name: 'claude-provider',
            tenant: 'my-app',
            apiKey: process.env.ANTHROPIC_API_KEY || 'your-anthropic-key',
            baseUrl: 'https://api.anthropic.com/v1',
            defaultModel: 'claude-3-sonnet-20240229'
        });

        console.log('Anthropic provider created:', anthropicProvider.name);

        // List all providers
        const providers = orchestrator.listProviders('my-app');
        console.log('Available providers:', providers.map(p => p.name));

        // Generate chat completion (will automatically choose best provider)
        const chatResponse = await orchestrator.generateChatCompletion([
            { role: 'user', content: 'Hello! How are you today?' }
        ], {
            tenant: 'my-app',
            maxTokens: 100
        });

        console.log('Chat response:', chatResponse.content);
        console.log('Provider used:', chatResponse.provider);
        console.log('Cost:', chatResponse.cost);

    } catch (error) {
        console.error('Error:', error.message);
    } finally {
        await orchestrator.cleanup();
    }
}

async function localModelExample() {
    console.log('=== Local Model Example ===');

    const orchestrator = new AIOrchestrator();
    await orchestrator.initialize();

    try {
        // Create a local Ollama provider
        const localProvider = await orchestrator.createProvider({
            type: 'local',
            name: 'ollama-llama',
            tenant: 'local-app',
            baseUrl: 'http://localhost:11434',
            serverType: 'ollama',
            defaultModel: 'llama2'
        });

        console.log('Local provider created:', localProvider.name);

        // Test provider connectivity
        const healthCheck = await orchestrator.testProvider('ollama-llama', 'local-app');
        console.log('Health check:', healthCheck);

        if (healthCheck.success) {
            // Generate completion using local model
            const completion = await orchestrator.generateCompletion(
                'Explain the concept of artificial intelligence in simple terms.',
                {
                    tenant: 'local-app',
                    provider: 'ollama-llama',
                    maxTokens: 200
                }
            );

            console.log('Local model response:', completion.content);
            console.log('Cost (should be 0):', completion.cost);
        }

    } catch (error) {
        console.error('Error:', error.message);
    } finally {
        await orchestrator.cleanup();
    }
}

async function customProviderExample() {
    console.log('=== Custom Provider Example ===');

    const orchestrator = new AIOrchestrator();
    await orchestrator.initialize();

    try {
        // Create a custom API provider
        const customProvider = await orchestrator.createProvider({
            type: 'custom',
            name: 'my-custom-api',
            tenant: 'custom-app',
            baseUrl: 'https://api.mycompany.com/v1',
            apiKey: 'my-custom-key',
            requestFormat: 'openai', // Use OpenAI-compatible format
            responseFormat: 'openai',
            authMethod: 'bearer',
            endpoints: {
                chatCompletion: '/chat/completions',
                embedding: '/embeddings'
            },
            customHeaders: {
                'X-Custom-Header': 'my-value'
            }
        });

        console.log('Custom provider created:', customProvider.name);

        // Use custom provider
        const response = await orchestrator.generateChatCompletion([
            { role: 'user', content: 'Test message for custom API' }
        ], {
            tenant: 'custom-app',
            provider: 'my-custom-api'
        });

        console.log('Custom API response:', response);

    } catch (error) {
        console.error('Error:', error.message);
    } finally {
        await orchestrator.cleanup();
    }
}

async function multiTenantExample() {
    console.log('=== Multi-Tenant Example ===');

    const orchestrator = new AIOrchestrator();
    await orchestrator.initialize();

    try {
        // Create providers for different tenants
        await orchestrator.createProvider({
            type: 'openai',
            name: 'gpt-provider',
            tenant: 'tenant-a',
            apiKey: 'tenant-a-openai-key',
            defaultModel: 'gpt-3.5-turbo'
        });

        await orchestrator.createProvider({
            type: 'anthropic',
            name: 'claude-provider',
            tenant: 'tenant-b',
            apiKey: 'tenant-b-anthropic-key',
            defaultModel: 'claude-3-sonnet-20240229'
        });

        // Set different budgets for each tenant
        orchestrator.setBudget('tenant-a', {
            daily: 50.0,
            monthly: 1000.0,
            alertEmails: ['admin-a@company.com']
        });

        orchestrator.setBudget('tenant-b', {
            daily: 100.0,
            monthly: 2000.0,
            alertEmails: ['admin-b@company.com']
        });

        // Set different rate limits
        orchestrator.setRateLimit('tenant-a', {
            requestsPerSecond: 5,
            requestsPerMinute: 100
        }, 'tenant');

        orchestrator.setRateLimit('tenant-b', {
            requestsPerSecond: 10,
            requestsPerMinute: 300
        }, 'tenant');

        // Generate responses for each tenant
        const responseA = await orchestrator.generateChatCompletion([
            { role: 'user', content: 'Hello from tenant A' }
        ], { tenant: 'tenant-a' });

        const responseB = await orchestrator.generateChatCompletion([
            { role: 'user', content: 'Hello from tenant B' }
        ], { tenant: 'tenant-b' });

        console.log('Tenant A response:', responseA.content, 'Provider:', responseA.provider);
        console.log('Tenant B response:', responseB.content, 'Provider:', responseB.provider);

        // Check costs per tenant
        const costsA = orchestrator.getCostSummary('tenant-a');
        const costsB = orchestrator.getCostSummary('tenant-b');

        console.log('Tenant A costs:', costsA);
        console.log('Tenant B costs:', costsB);

    } catch (error) {
        console.error('Error:', error.message);
    } finally {
        await orchestrator.cleanup();
    }
}

async function failoverExample() {
    console.log('=== Failover Example ===');

    const orchestrator = new AIOrchestrator();
    await orchestrator.initialize();

    try {
        // Create primary provider
        await orchestrator.createProvider({
            type: 'openai',
            name: 'primary-gpt',
            tenant: 'failover-app',
            apiKey: 'primary-key',
            defaultModel: 'gpt-4'
        });

        // Create fallback provider
        await orchestrator.createProvider({
            type: 'anthropic',
            name: 'fallback-claude',
            tenant: 'failover-app',
            apiKey: 'fallback-key',
            defaultModel: 'claude-3-sonnet-20240229'
        });

        // Create local fallback
        await orchestrator.createProvider({
            type: 'local',
            name: 'local-fallback',
            tenant: 'failover-app',
            baseUrl: 'http://localhost:11434',
            serverType: 'ollama',
            defaultModel: 'llama2'
        });

        console.log('Providers created for failover testing');

        // Test automatic failover (framework will try providers in order of health/performance)
        const response = await orchestrator.generateChatCompletion([
            { role: 'user', content: 'This should work with any available provider' }
        ], {
            tenant: 'failover-app',
            maxTokens: 100
        });

        console.log('Failover response:', response.content);
        console.log('Provider used:', response.provider);

        // Check health of all providers
        const healthSummary = orchestrator.getHealthSummary();
        console.log('Health summary:', healthSummary);

    } catch (error) {
        console.error('Error:', error.message);
    } finally {
        await orchestrator.cleanup();
    }
}

async function monitoringExample() {
    console.log('=== Monitoring Example ===');

    const orchestrator = new AIOrchestrator();
    await orchestrator.initialize();

    try {
        // Create provider
        await orchestrator.createProvider({
            type: 'openai',
            name: 'monitored-provider',
            tenant: 'monitoring-app',
            apiKey: 'test-key',
            defaultModel: 'gpt-3.5-turbo'
        });

        // Simulate some usage
        for (let i = 0; i < 5; i++) {
            try {
                await orchestrator.generateChatCompletion([
                    { role: 'user', content: `Test message ${i + 1}` }
                ], {
                    tenant: 'monitoring-app',
                    provider: 'monitored-provider'
                });
            } catch (error) {
                // Expected to fail with test key
                console.log(`Request ${i + 1} failed (expected with test key)`);
            }
        }

        // Get provider health
        const health = orchestrator.getProviderHealth('monitored-provider', 'monitoring-app');
        console.log('Provider health:', health);

        // Get rate limit status
        const rateLimits = orchestrator.getRateLimitStatus('monitored-provider', 'monitoring-app');
        console.log('Rate limit status:', rateLimits);

        // Get cost analytics
        const analytics = orchestrator.getAnalytics('1d', 'monitoring-app');
        console.log('Cost analytics:', analytics);

        // Get comprehensive statistics
        const statistics = orchestrator.getStatistics();
        console.log('System statistics:', statistics);

    } catch (error) {
        console.error('Error:', error.message);
    } finally {
        await orchestrator.cleanup();
    }
}

async function templateExample() {
    console.log('=== Template Example ===');

    const orchestrator = new AIOrchestrator();
    await orchestrator.initialize();

    try {
        // Create provider from OpenAI template
        const openaiProvider = await orchestrator.createProviderFromTemplate(
            'openai',
            'template-openai',
            'template-app',
            {
                OPENAI_API_KEY: 'your-openai-key',
                OPENAI_ORG_ID: 'your-org-id'
            }
        );

        console.log('OpenAI provider from template:', openaiProvider.name);

        // Create provider from custom template
        const customProvider = await orchestrator.createProviderFromTemplate(
            'custom',
            'template-custom',
            'template-app',
            {
                CUSTOM_API_URL: 'https://api.custom.com',
                CUSTOM_API_KEY: 'custom-key'
            }
        );

        console.log('Custom provider from template:', customProvider.name);

        // List all providers
        const providers = orchestrator.listProviders('template-app');
        console.log('Providers created from templates:', providers.map(p => p.name));

    } catch (error) {
        console.error('Error:', error.message);
    } finally {
        await orchestrator.cleanup();
    }
}

async function apiServerExample() {
    console.log('=== API Server Example ===');

    const orchestrator = new AIOrchestrator();
    await orchestrator.initialize();

    // Create Express app
    const app = express();
    app.use(express.json());

    // Add AI Orchestration API routes
    const api = createAPI(orchestrator);
    app.use('/api/ai', api.getRouter());

    // Add error handling
    app.use(api.errorHandler);

    // Start server
    const PORT = process.env.PORT || 3000;
    const server = app.listen(PORT, () => {
        console.log(`AI Orchestration API server running on port ${PORT}`);
        console.log('Available endpoints:');
        console.log('  POST /api/ai/providers - Create provider');
        console.log('  GET /api/ai/providers - List providers');
        console.log('  POST /api/ai/chat/completions - Generate chat completion');
        console.log('  GET /api/ai/health - Check health');
        console.log('  GET /api/ai/statistics - Get statistics');
    });

    // Cleanup function
    const cleanup = async () => {
        console.log('Shutting down API server...');
        server.close();
        await orchestrator.cleanup();
    };

    process.on('SIGINT', cleanup);
    process.on('SIGTERM', cleanup);

    return { app, server, cleanup };
}

async function exportImportExample() {
    console.log('=== Export/Import Example ===');

    const orchestrator1 = new AIOrchestrator({
        config: { configDir: './config-export' }
    });
    await orchestrator1.initialize();

    try {
        // Create some providers
        await orchestrator1.createProvider({
            type: 'openai',
            name: 'export-provider',
            tenant: 'export-app',
            apiKey: 'test-key',
            defaultModel: 'gpt-3.5-turbo'
        });

        // Set budget and rate limits
        orchestrator1.setBudget('export-app', {
            daily: 25.0,
            monthly: 500.0
        });

        orchestrator1.setRateLimit('export-app', {
            requestsPerSecond: 10
        }, 'tenant');

        // Export configuration
        const exportData = await orchestrator1.exportData({
            includeSecrets: false,
            includeHistory: true
        });

        console.log('Configuration exported');

        // Create new orchestrator and import
        const orchestrator2 = new AIOrchestrator({
            config: { configDir: './config-import' }
        });
        await orchestrator2.initialize();

        await orchestrator2.importData(exportData);

        console.log('Configuration imported');

        // Verify import
        const importedProviders = orchestrator2.listProviders('export-app');
        console.log('Imported providers:', importedProviders.map(p => p.name));

        await orchestrator2.cleanup();

    } catch (error) {
        console.error('Error:', error.message);
    } finally {
        await orchestrator1.cleanup();
    }
}

// Run examples
async function runExamples() {
    const examples = [
        basicUsageExample,
        localModelExample,
        customProviderExample,
        multiTenantExample,
        failoverExample,
        monitoringExample,
        templateExample,
        exportImportExample
    ];

    for (const example of examples) {
        try {
            await example();
            console.log('\n' + '='.repeat(50) + '\n');
        } catch (error) {
            console.error(`Example failed: ${example.name}`, error.message);
            console.log('\n' + '='.repeat(50) + '\n');
        }
    }
}

// Export examples for use in other files
module.exports = {
    basicUsageExample,
    localModelExample,
    customProviderExample,
    multiTenantExample,
    failoverExample,
    monitoringExample,
    templateExample,
    apiServerExample,
    exportImportExample,
    runExamples
};

// Run examples if this file is executed directly
if (require.main === module) {
    runExamples().catch(console.error);
}