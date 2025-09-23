/**
 * Integration tests for AIOrchestrator
 */

const { AIOrchestrator } = require('../../../backend/ai-orchestration/index');
const fs = require('fs').promises;
const path = require('path');

// Test configuration directory
const TEST_CONFIG_DIR = path.join(__dirname, 'test-config');

describe('AIOrchestrator Integration Tests', () => {
    let orchestrator;

    beforeAll(async () => {
        // Create test config directory
        await fs.mkdir(TEST_CONFIG_DIR, { recursive: true });
    });

    beforeEach(async () => {
        orchestrator = new AIOrchestrator({
            config: {
                configDir: TEST_CONFIG_DIR
            }
        });
        await orchestrator.initialize();
    });

    afterEach(async () => {
        if (orchestrator) {
            await orchestrator.cleanup();
        }
    });

    afterAll(async () => {
        // Cleanup test config directory
        try {
            await fs.rmdir(TEST_CONFIG_DIR, { recursive: true });
        } catch (error) {
            // Ignore cleanup errors
        }
    });

    describe('Initialization', () => {
        test('should initialize successfully', async () => {
            expect(orchestrator.isInitialized).toBe(true);
            expect(orchestrator.configManager).toBeDefined();
            expect(orchestrator.providerRegistry).toBeDefined();
            expect(orchestrator.healthMonitor).toBeDefined();
            expect(orchestrator.costTracker).toBeDefined();
            expect(orchestrator.rateLimiter).toBeDefined();
        });

        test('should not initialize twice', async () => {
            await orchestrator.initialize(); // Second call should be ignored
            expect(orchestrator.isInitialized).toBe(true);
        });
    });

    describe('Provider Management', () => {
        test('should create mock provider successfully', async () => {
            const config = {
                type: 'custom',
                name: 'test-provider',
                tenant: 'test-tenant',
                baseUrl: 'https://api.test.com',
                apiKey: 'test-key',
                requestFormat: 'openai',
                responseFormat: 'openai'
            };

            const provider = await orchestrator.createProvider(config);

            expect(provider).toBeDefined();
            expect(provider.name).toBe('test-provider');

            // Verify provider is registered
            const retrievedProvider = orchestrator.getProvider('test-provider', 'test-tenant');
            expect(retrievedProvider).toBe(provider);
        });

        test('should list providers for tenant', async () => {
            await orchestrator.createProvider({
                type: 'custom',
                name: 'provider1',
                tenant: 'test-tenant',
                baseUrl: 'https://api.test.com',
                apiKey: 'test-key',
                requestFormat: 'openai',
                responseFormat: 'openai'
            });

            await orchestrator.createProvider({
                type: 'custom',
                name: 'provider2',
                tenant: 'test-tenant',
                baseUrl: 'https://api.test.com',
                apiKey: 'test-key',
                requestFormat: 'openai',
                responseFormat: 'openai'
            });

            const providers = orchestrator.listProviders('test-tenant');
            expect(providers).toHaveLength(2);
            expect(providers.map(p => p.name)).toContain('provider1');
            expect(providers.map(p => p.name)).toContain('provider2');
        });

        test('should remove provider successfully', async () => {
            await orchestrator.createProvider({
                type: 'custom',
                name: 'test-provider',
                tenant: 'test-tenant',
                baseUrl: 'https://api.test.com',
                apiKey: 'test-key',
                requestFormat: 'openai',
                responseFormat: 'openai'
            });

            const result = await orchestrator.removeProvider('test-provider', 'test-tenant');
            expect(result).toBe(true);

            const provider = orchestrator.getProvider('test-provider', 'test-tenant');
            expect(provider).toBeUndefined();
        });

        test('should update provider configuration', async () => {
            await orchestrator.createProvider({
                type: 'custom',
                name: 'test-provider',
                tenant: 'test-tenant',
                baseUrl: 'https://api.test.com',
                apiKey: 'test-key',
                requestFormat: 'openai',
                responseFormat: 'openai'
            });

            const updates = {
                type: 'custom',
                baseUrl: 'https://api.updated.com',
                requestFormat: 'openai',
                responseFormat: 'openai'
            };

            const updatedProvider = await orchestrator.updateProvider('test-provider', 'test-tenant', updates);
            expect(updatedProvider.baseUrl).toBe('https://api.updated.com');
        });
    });

    describe('Health Monitoring', () => {
        beforeEach(async () => {
            await orchestrator.createProvider({
                type: 'custom',
                name: 'test-provider',
                tenant: 'test-tenant',
                baseUrl: 'https://api.test.com',
                apiKey: 'test-key',
                requestFormat: 'openai',
                responseFormat: 'openai'
            });
        });

        test('should get provider health status', () => {
            const health = orchestrator.getProviderHealth('test-provider', 'test-tenant');
            expect(health).toBeDefined();
            expect(health.healthy).toBeDefined();
        });

        test('should get overall health summary', () => {
            const summary = orchestrator.getHealthSummary();
            expect(summary).toBeDefined();
            expect(summary.totalProviders).toBeGreaterThan(0);
            expect(summary.providers).toBeDefined();
        });

        test('should test provider connectivity', async () => {
            const result = await orchestrator.testProvider('test-provider', 'test-tenant');
            expect(result).toBeDefined();
            expect(result.success).toBeDefined();
            expect(result.provider).toBe('test-provider');
            expect(result.tenant).toBe('test-tenant');
        });
    });

    describe('Cost Tracking', () => {
        beforeEach(async () => {
            await orchestrator.createProvider({
                type: 'custom',
                name: 'test-provider',
                tenant: 'test-tenant',
                baseUrl: 'https://api.test.com',
                apiKey: 'test-key',
                requestFormat: 'openai',
                responseFormat: 'openai'
            });
        });

        test('should track costs for tenant', () => {
            // Record some cost data
            orchestrator.costTracker.recordCost(
                'test-provider',
                'test-tenant',
                'test-model',
                0.05,
                100,
                'chat_completion'
            );

            const costs = orchestrator.getCostSummary('test-tenant');
            expect(costs).toBeDefined();
            expect(costs.totalCost).toBe(0.05);
            expect(costs.totalTokens).toBe(100);
        });

        test('should set and get budget', () => {
            const budget = {
                daily: 10.0,
                monthly: 300.0,
                alertEmails: ['test@example.com']
            };

            orchestrator.setBudget('test-tenant', budget);

            const retrievedBudget = orchestrator.costTracker.getBudget('test-tenant');
            expect(retrievedBudget).toBeDefined();
            expect(retrievedBudget.daily).toBe(10.0);
            expect(retrievedBudget.monthly).toBe(300.0);
        });

        test('should get cost analytics', () => {
            // Record some cost data
            orchestrator.costTracker.recordCost(
                'test-provider',
                'test-tenant',
                'test-model',
                0.05,
                100,
                'chat_completion'
            );

            const analytics = orchestrator.getAnalytics('7d', 'test-tenant');
            expect(analytics).toBeDefined();
            expect(analytics.timeRange).toBe('7d');
            expect(analytics.totalCost).toBeGreaterThanOrEqual(0);
        });
    });

    describe('Rate Limiting', () => {
        beforeEach(async () => {
            await orchestrator.createProvider({
                type: 'custom',
                name: 'test-provider',
                tenant: 'test-tenant',
                baseUrl: 'https://api.test.com',
                apiKey: 'test-key',
                requestFormat: 'openai',
                responseFormat: 'openai'
            });
        });

        test('should set and get rate limits', () => {
            const limits = {
                requestsPerSecond: 5,
                requestsPerMinute: 100,
                tokensPerSecond: 1000
            };

            orchestrator.setRateLimit('test-provider', limits, 'provider');

            const status = orchestrator.getRateLimitStatus('test-provider', 'test-tenant');
            expect(status).toBeDefined();
            expect(status.limits).toBeDefined();
            expect(status.usage).toBeDefined();
        });

        test('should get all rate limit statuses', () => {
            const statuses = orchestrator.getRateLimitStatus();
            expect(statuses).toBeDefined();
            expect(typeof statuses).toBe('object');
        });
    });

    describe('Configuration Management', () => {
        test('should create provider from template', async () => {
            const variables = {
                CUSTOM_API_URL: 'https://api.custom.com',
                CUSTOM_API_KEY: 'custom-key'
            };

            const provider = await orchestrator.createProviderFromTemplate(
                'custom',
                'custom-provider',
                'test-tenant',
                variables
            );

            expect(provider).toBeDefined();
            expect(provider.name).toBe('custom-provider');
            expect(provider.baseUrl).toBe('https://api.custom.com');
        });

        test('should export and import configuration', async () => {
            // Create a provider to have some data
            await orchestrator.createProvider({
                type: 'custom',
                name: 'test-provider',
                tenant: 'test-tenant',
                baseUrl: 'https://api.test.com',
                apiKey: 'test-key',
                requestFormat: 'openai',
                responseFormat: 'openai'
            });

            // Export configuration
            const exportData = await orchestrator.exportData();
            expect(exportData).toBeDefined();
            expect(exportData.timestamp).toBeDefined();
            expect(exportData.configuration).toBeDefined();

            // Create new orchestrator and import
            const newOrchestrator = new AIOrchestrator({
                config: {
                    configDir: path.join(TEST_CONFIG_DIR, 'import-test')
                }
            });
            await newOrchestrator.initialize();

            await newOrchestrator.importData(exportData);

            // Verify import
            const importedProvider = newOrchestrator.getProvider('test-provider', 'test-tenant');
            expect(importedProvider).toBeDefined();

            await newOrchestrator.cleanup();
        });
    });

    describe('Statistics', () => {
        beforeEach(async () => {
            await orchestrator.createProvider({
                type: 'custom',
                name: 'test-provider',
                tenant: 'test-tenant',
                baseUrl: 'https://api.test.com',
                apiKey: 'test-key',
                requestFormat: 'openai',
                responseFormat: 'openai'
            });
        });

        test('should get comprehensive statistics', () => {
            const stats = orchestrator.getStatistics();
            expect(stats).toBeDefined();
            expect(stats.providers).toBeDefined();
            expect(stats.health).toBeDefined();
            expect(stats.costs).toBeDefined();
            expect(stats.rateLimits).toBeDefined();
            expect(stats.configuration).toBeDefined();
        });
    });

    describe('Error Handling', () => {
        test('should handle invalid provider configuration', async () => {
            const invalidConfig = {
                type: 'custom',
                name: 'invalid-provider',
                // Missing required fields
            };

            await expect(
                orchestrator.createProvider(invalidConfig)
            ).rejects.toThrow();
        });

        test('should handle non-existent provider operations', async () => {
            expect(() => {
                orchestrator.getProvider('non-existent', 'test-tenant');
            }).not.toThrow();

            const provider = orchestrator.getProvider('non-existent', 'test-tenant');
            expect(provider).toBeUndefined();
        });

        test('should handle removal of non-existent provider', async () => {
            await expect(
                orchestrator.removeProvider('non-existent', 'test-tenant')
            ).rejects.toThrow();
        });
    });

    describe('Multi-tenant Isolation', () => {
        test('should isolate providers between tenants', async () => {
            // Create providers for different tenants
            await orchestrator.createProvider({
                type: 'custom',
                name: 'provider1',
                tenant: 'tenant1',
                baseUrl: 'https://api.test.com',
                apiKey: 'key1',
                requestFormat: 'openai',
                responseFormat: 'openai'
            });

            await orchestrator.createProvider({
                type: 'custom',
                name: 'provider1', // Same name, different tenant
                tenant: 'tenant2',
                baseUrl: 'https://api.test.com',
                apiKey: 'key2',
                requestFormat: 'openai',
                responseFormat: 'openai'
            });

            // Verify isolation
            const provider1 = orchestrator.getProvider('provider1', 'tenant1');
            const provider2 = orchestrator.getProvider('provider1', 'tenant2');

            expect(provider1).toBeDefined();
            expect(provider2).toBeDefined();
            expect(provider1.apiKey).toBe('key1');
            expect(provider2.apiKey).toBe('key2');

            // Verify tenant-specific listing
            const tenant1Providers = orchestrator.listProviders('tenant1');
            const tenant2Providers = orchestrator.listProviders('tenant2');

            expect(tenant1Providers).toHaveLength(1);
            expect(tenant2Providers).toHaveLength(1);
        });
    });

    describe('Configuration Change Handling', () => {
        test('should handle configuration updates', async () => {
            await orchestrator.createProvider({
                type: 'custom',
                name: 'test-provider',
                tenant: 'test-tenant',
                baseUrl: 'https://api.test.com',
                apiKey: 'test-key',
                requestFormat: 'openai',
                responseFormat: 'openai'
            });

            // Simulate configuration change
            await orchestrator.handleConfigUpdate({
                provider: 'custom',
                tenant: 'test-tenant',
                config: {
                    name: 'test-provider',
                    baseUrl: 'https://api.updated.com',
                    apiKey: 'updated-key',
                    requestFormat: 'openai',
                    responseFormat: 'openai'
                }
            });

            const provider = orchestrator.getProvider('test-provider', 'test-tenant');
            expect(provider.baseUrl).toBe('https://api.updated.com');
        });

        test('should handle configuration removal', async () => {
            await orchestrator.createProvider({
                type: 'custom',
                name: 'test-provider',
                tenant: 'test-tenant',
                baseUrl: 'https://api.test.com',
                apiKey: 'test-key',
                requestFormat: 'openai',
                responseFormat: 'openai'
            });

            // Simulate configuration removal
            await orchestrator.handleConfigRemoval({
                provider: 'test-provider',
                tenant: 'test-tenant'
            });

            const provider = orchestrator.getProvider('test-provider', 'test-tenant');
            expect(provider).toBeUndefined();
        });
    });
});

// Performance tests
describe('AIOrchestrator Performance Tests', () => {
    let orchestrator;

    beforeAll(async () => {
        orchestrator = new AIOrchestrator({
            config: {
                configDir: path.join(__dirname, 'perf-test-config')
            }
        });
        await orchestrator.initialize();
    });

    afterAll(async () => {
        await orchestrator.cleanup();
    });

    test('should handle multiple concurrent provider creations', async () => {
        const providerConfigs = Array.from({ length: 10 }, (_, i) => ({
            type: 'custom',
            name: `provider-${i}`,
            tenant: 'perf-test',
            baseUrl: 'https://api.test.com',
            apiKey: `key-${i}`,
            requestFormat: 'openai',
            responseFormat: 'openai'
        }));

        const startTime = Date.now();

        const providers = await Promise.all(
            providerConfigs.map(config => orchestrator.createProvider(config))
        );

        const endTime = Date.now();
        const duration = endTime - startTime;

        expect(providers).toHaveLength(10);
        expect(duration).toBeLessThan(5000); // Should complete within 5 seconds

        // Verify all providers were created
        const listedProviders = orchestrator.listProviders('perf-test');
        expect(listedProviders).toHaveLength(10);
    });

    test('should maintain performance with many providers', () => {
        const startTime = Date.now();

        const providers = orchestrator.listProviders('perf-test');
        const statistics = orchestrator.getStatistics();
        const healthSummary = orchestrator.getHealthSummary();

        const endTime = Date.now();
        const duration = endTime - startTime;

        expect(providers).toHaveLength(10);
        expect(statistics).toBeDefined();
        expect(healthSummary).toBeDefined();
        expect(duration).toBeLessThan(1000); // Should complete within 1 second
    });
});