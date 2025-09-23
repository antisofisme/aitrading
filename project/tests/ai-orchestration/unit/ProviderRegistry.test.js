/**
 * Unit tests for ProviderRegistry
 */

const ProviderRegistry = require('../../../backend/ai-orchestration/core/ProviderRegistry');
const BaseProvider = require('../../../backend/ai-orchestration/core/BaseProvider');

// Mock provider for testing
class MockProvider extends BaseProvider {
    constructor(config) {
        super(config);
        this.healthy = true;
    }

    async generateChatCompletion(messages, options = {}) {
        if (!this.healthy) throw new Error('Provider unhealthy');
        return { content: 'Mock response', usage: { total_tokens: 100 }, cost: 0.05 };
    }

    async generateCompletion(prompt, options = {}) {
        if (!this.healthy) throw new Error('Provider unhealthy');
        return { content: 'Mock completion', usage: { total_tokens: 50 }, cost: 0.02 };
    }

    async generateEmbedding(text, options = {}) {
        if (!this.healthy) throw new Error('Provider unhealthy');
        return { embedding: [0.1, 0.2, 0.3], usage: { total_tokens: 25 }, cost: 0.01 };
    }

    async ping() {
        if (!this.healthy) throw new Error('Health check failed');
        return { status: 'healthy' };
    }

    getCapabilities() {
        return {
            provider: this.name,
            supportsChatCompletion: true,
            supportsCompletion: true,
            supportsEmbedding: true,
            supportsStreaming: false,
            supportsFunctionCalling: false,
            maxTokens: 4096,
            models: ['mock-model-1', 'mock-model-2']
        };
    }
}

// Mock unhealthy provider
class UnhealthyProvider extends MockProvider {
    constructor(config) {
        super(config);
        this.healthy = false;
    }
}

describe('ProviderRegistry', () => {
    let registry;

    beforeEach(() => {
        registry = new ProviderRegistry();

        // Register mock providers
        registry.registerProviderClass('mock', MockProvider);
        registry.registerProviderClass('unhealthy', UnhealthyProvider);
    });

    afterEach(async () => {
        await registry.cleanup();
    });

    describe('Provider Class Registration', () => {
        test('should register provider class successfully', () => {
            registry.registerProviderClass('test', MockProvider);
            expect(registry.providerClasses.has('test')).toBe(true);
        });

        test('should throw error for non-BaseProvider class', () => {
            class InvalidProvider {}

            expect(() => {
                registry.registerProviderClass('invalid', InvalidProvider);
            }).toThrow('Provider class must extend BaseProvider');
        });
    });

    describe('Provider Creation', () => {
        test('should create provider successfully', async () => {
            const config = {
                type: 'mock',
                name: 'test-provider',
                tenant: 'test-tenant',
                baseUrl: 'https://api.test.com',
                apiKey: 'test-key'
            };

            const provider = await registry.createProvider(config);

            expect(provider).toBeInstanceOf(MockProvider);
            expect(provider.name).toBe('test-provider');
            expect(registry.providers.has('test-tenant:test-provider')).toBe(true);
        });

        test('should throw error for unknown provider type', async () => {
            const config = {
                type: 'unknown',
                name: 'test-provider',
                baseUrl: 'https://api.test.com',
                apiKey: 'test-key'
            };

            await expect(registry.createProvider(config)).rejects.toThrow('Unknown provider type: unknown');
        });

        test('should throw error for duplicate provider', async () => {
            const config = {
                type: 'mock',
                name: 'test-provider',
                tenant: 'test-tenant',
                baseUrl: 'https://api.test.com',
                apiKey: 'test-key'
            };

            await registry.createProvider(config);

            await expect(registry.createProvider(config)).rejects.toThrow('Provider test-tenant:test-provider already exists');
        });
    });

    describe('Provider Retrieval', () => {
        beforeEach(async () => {
            await registry.createProvider({
                type: 'mock',
                name: 'provider1',
                tenant: 'tenant1',
                baseUrl: 'https://api.test.com',
                apiKey: 'test-key'
            });

            await registry.createProvider({
                type: 'mock',
                name: 'provider2',
                tenant: 'tenant1',
                baseUrl: 'https://api.test.com',
                apiKey: 'test-key'
            });
        });

        test('should get provider by name and tenant', () => {
            const provider = registry.getProvider('provider1', 'tenant1');
            expect(provider).toBeInstanceOf(MockProvider);
            expect(provider.name).toBe('provider1');
        });

        test('should return undefined for non-existent provider', () => {
            const provider = registry.getProvider('non-existent', 'tenant1');
            expect(provider).toBeUndefined();
        });

        test('should list providers for tenant', () => {
            const providers = registry.listProviders('tenant1');
            expect(providers).toHaveLength(2);
            expect(providers.map(p => p.name)).toContain('provider1');
            expect(providers.map(p => p.name)).toContain('provider2');
        });

        test('should return empty list for non-existent tenant', () => {
            const providers = registry.listProviders('non-existent');
            expect(providers).toHaveLength(0);
        });
    });

    describe('Provider Removal', () => {
        beforeEach(async () => {
            await registry.createProvider({
                type: 'mock',
                name: 'test-provider',
                tenant: 'test-tenant',
                baseUrl: 'https://api.test.com',
                apiKey: 'test-key'
            });
        });

        test('should remove provider successfully', async () => {
            const result = await registry.removeProvider('test-provider', 'test-tenant');
            expect(result).toBe(true);
            expect(registry.providers.has('test-tenant:test-provider')).toBe(false);
        });

        test('should throw error for non-existent provider', async () => {
            await expect(
                registry.removeProvider('non-existent', 'test-tenant')
            ).rejects.toThrow('Provider test-tenant:non-existent not found');
        });
    });

    describe('Provider Updates', () => {
        beforeEach(async () => {
            await registry.createProvider({
                type: 'mock',
                name: 'test-provider',
                tenant: 'test-tenant',
                baseUrl: 'https://api.test.com',
                apiKey: 'test-key'
            });
        });

        test('should update provider configuration', async () => {
            const updates = {
                type: 'mock',
                baseUrl: 'https://api.updated.com'
            };

            const provider = await registry.updateProvider('test-provider', 'test-tenant', updates);

            expect(provider).toBeInstanceOf(MockProvider);
            expect(provider.baseUrl).toBe('https://api.updated.com');
        });
    });

    describe('Best Provider Selection', () => {
        beforeEach(async () => {
            // Create healthy provider
            await registry.createProvider({
                type: 'mock',
                name: 'healthy-provider',
                tenant: 'test-tenant',
                baseUrl: 'https://api.test.com',
                apiKey: 'test-key'
            });

            // Create unhealthy provider
            await registry.createProvider({
                type: 'unhealthy',
                name: 'unhealthy-provider',
                tenant: 'test-tenant',
                baseUrl: 'https://api.test.com',
                apiKey: 'test-key'
            });
        });

        test('should return best available provider', () => {
            const provider = registry.getBestProvider({}, 'test-tenant');
            expect(provider.name).toBe('healthy-provider');
        });

        test('should filter by capabilities', () => {
            const provider = registry.getBestProvider({
                supportsFunctionCalling: true
            }, 'test-tenant');

            // Should not find any provider since mock doesn't support function calling
            expect(() => {
                registry.getBestProvider({ supportsFunctionCalling: true }, 'test-tenant');
            }).toThrow('No providers meet the specified criteria');
        });

        test('should throw error when no providers available', () => {
            expect(() => {
                registry.getBestProvider({}, 'non-existent-tenant');
            }).toThrow('No providers available for tenant: non-existent-tenant');
        });
    });

    describe('Load Balanced Provider', () => {
        beforeEach(async () => {
            await registry.createProvider({
                type: 'mock',
                name: 'provider1',
                tenant: 'test-tenant',
                baseUrl: 'https://api.test.com',
                apiKey: 'test-key'
            });

            await registry.createProvider({
                type: 'mock',
                name: 'provider2',
                tenant: 'test-tenant',
                baseUrl: 'https://api.test.com',
                apiKey: 'test-key'
            });
        });

        test('should return load balanced provider', () => {
            const provider = registry.getLoadBalancedProvider('test-tenant');
            expect(['provider1', 'provider2']).toContain(provider.name);
        });

        test('should throw error when no healthy providers', () => {
            expect(() => {
                registry.getLoadBalancedProvider('non-existent-tenant');
            }).toThrow('No healthy providers available');
        });
    });

    describe('Failover Execution', () => {
        beforeEach(async () => {
            await registry.createProvider({
                type: 'mock',
                name: 'healthy-provider',
                tenant: 'test-tenant',
                baseUrl: 'https://api.test.com',
                apiKey: 'test-key'
            });

            await registry.createProvider({
                type: 'unhealthy',
                name: 'unhealthy-provider',
                tenant: 'test-tenant',
                baseUrl: 'https://api.test.com',
                apiKey: 'test-key'
            });
        });

        test('should execute with successful provider', async () => {
            const requestFn = jest.fn(async (provider) => {
                return await provider.generateChatCompletion([{ role: 'user', content: 'test' }]);
            });

            const result = await registry.executeWithFailover(requestFn, {}, 'test-tenant');

            expect(result.content).toBe('Mock response');
            expect(requestFn).toHaveBeenCalled();
        });

        test('should failover to next provider on error', async () => {
            const requestFn = jest.fn()
                .mockRejectedValueOnce(new Error('First provider failed'))
                .mockResolvedValueOnce({ content: 'Success from second provider' });

            const result = await registry.executeWithFailover(requestFn, {}, 'test-tenant', 2);

            expect(result.content).toBe('Success from second provider');
            expect(requestFn).toHaveBeenCalledTimes(2);
        });

        test('should throw error when all providers fail', async () => {
            const requestFn = jest.fn().mockRejectedValue(new Error('All providers failed'));

            await expect(
                registry.executeWithFailover(requestFn, {}, 'test-tenant', 3)
            ).rejects.toThrow('All providers failed');
        });

        test('should throw error when no healthy providers available', async () => {
            const requestFn = jest.fn();

            await expect(
                registry.executeWithFailover(requestFn, {}, 'non-existent-tenant')
            ).rejects.toThrow('No healthy providers available');
        });
    });

    describe('Statistics', () => {
        beforeEach(async () => {
            await registry.createProvider({
                type: 'mock',
                name: 'provider1',
                tenant: 'tenant1',
                baseUrl: 'https://api.test.com',
                apiKey: 'test-key'
            });

            await registry.createProvider({
                type: 'mock',
                name: 'provider2',
                tenant: 'tenant2',
                baseUrl: 'https://api.test.com',
                apiKey: 'test-key'
            });
        });

        test('should return registry statistics', () => {
            const stats = registry.getStatistics();

            expect(stats.totalProviders).toBe(2);
            expect(stats.tenants).toContain('tenant1');
            expect(stats.tenants).toContain('tenant2');
            expect(stats.providerTypes['MockProvider']).toBe(2);
            expect(stats.healthyProviders).toBe(2);
        });
    });

    describe('Provider Key Generation', () => {
        test('should generate correct provider key', () => {
            const key = registry.getProviderKey('test-provider', 'test-tenant');
            expect(key).toBe('test-tenant:test-provider');
        });

        test('should use default tenant when not specified', () => {
            const key = registry.getProviderKey('test-provider');
            expect(key).toBe('default:test-provider');
        });
    });

    describe('Cleanup', () => {
        test('should cleanup resources', async () => {
            await registry.createProvider({
                type: 'mock',
                name: 'test-provider',
                tenant: 'test-tenant',
                baseUrl: 'https://api.test.com',
                apiKey: 'test-key'
            });

            await registry.cleanup();

            expect(registry.providers.size).toBe(0);
            expect(registry.configurations.size).toBe(0);
        });
    });
});

// Integration test with real components
describe('ProviderRegistry Integration', () => {
    let registry;

    beforeEach(() => {
        registry = new ProviderRegistry();
        registry.registerProviderClass('mock', MockProvider);
    });

    afterEach(async () => {
        await registry.cleanup();
    });

    test('should integrate with health monitor', async () => {
        const provider = await registry.createProvider({
            type: 'mock',
            name: 'test-provider',
            tenant: 'test-tenant',
            baseUrl: 'https://api.test.com',
            apiKey: 'test-key'
        });

        // Health monitor should be attached
        expect(provider.healthChecker).toBe(registry.healthMonitor);
    });

    test('should integrate with cost tracker', async () => {
        const provider = await registry.createProvider({
            type: 'mock',
            name: 'test-provider',
            tenant: 'test-tenant',
            baseUrl: 'https://api.test.com',
            apiKey: 'test-key'
        });

        // Cost tracker should be attached
        expect(provider.costTracker).toBe(registry.costTracker);
    });

    test('should integrate with rate limiter', async () => {
        const provider = await registry.createProvider({
            type: 'mock',
            name: 'test-provider',
            tenant: 'test-tenant',
            baseUrl: 'https://api.test.com',
            apiKey: 'test-key'
        });

        // Rate limiter should be attached
        expect(provider.rateLimiter).toBe(registry.rateLimiter);
    });
});