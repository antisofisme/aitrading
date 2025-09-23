/**
 * Unit tests for BaseProvider
 */

const BaseProvider = require('../../../backend/ai-orchestration/core/BaseProvider');

// Mock provider for testing
class MockProvider extends BaseProvider {
    constructor(config) {
        super(config);
        this.mockResponses = {
            ping: { status: 'healthy' },
            chat: { content: 'Mock response', usage: { total_tokens: 100 } },
            completion: { content: 'Mock completion', usage: { total_tokens: 50 } },
            embedding: { embedding: [0.1, 0.2, 0.3], usage: { total_tokens: 25 } }
        };
    }

    async generateChatCompletion(messages, options = {}) {
        return this.mockResponses.chat;
    }

    async generateCompletion(prompt, options = {}) {
        return this.mockResponses.completion;
    }

    async generateEmbedding(text, options = {}) {
        return this.mockResponses.embedding;
    }

    async ping() {
        return this.mockResponses.ping;
    }
}

describe('BaseProvider', () => {
    let provider;

    beforeEach(() => {
        provider = new MockProvider({
            name: 'test-provider',
            baseUrl: 'https://api.test.com',
            apiKey: 'test-key'
        });
    });

    describe('Constructor', () => {
        test('should initialize with correct configuration', () => {
            expect(provider.name).toBe('test-provider');
            expect(provider.baseUrl).toBe('https://api.test.com');
            expect(provider.apiKey).toBe('test-key');
            expect(provider.metrics).toBeDefined();
            expect(provider.metrics.requests).toBe(0);
        });

        test('should initialize metrics object', () => {
            expect(provider.metrics).toEqual({
                requests: 0,
                tokens: 0,
                errors: 0,
                latency: [],
                cost: 0
            });
        });
    });

    describe('Health Check', () => {
        test('should return healthy status on successful ping', async () => {
            const health = await provider.healthCheck();

            expect(health.healthy).toBe(true);
            expect(health.provider).toBe('test-provider');
            expect(health.timestamp).toBeDefined();
            expect(health.latency).toBeGreaterThanOrEqual(0);
        });

        test('should return unhealthy status on ping failure', async () => {
            provider.ping = jest.fn().mockRejectedValue(new Error('Connection failed'));

            const health = await provider.healthCheck();

            expect(health.healthy).toBe(false);
            expect(health.error).toBe('Connection failed');
            expect(health.provider).toBe('test-provider');
        });
    });

    describe('Headers', () => {
        test('should return correct default headers', () => {
            const headers = provider.getHeaders();

            expect(headers).toEqual({
                'Content-Type': 'application/json',
                'Authorization': 'Bearer test-key',
                'User-Agent': 'AI-Orchestration-Framework/1.0.0'
            });
        });
    });

    describe('Metrics Recording', () => {
        test('should record metrics correctly', () => {
            provider.recordMetrics('chat', 100, 0.05, 500);

            expect(provider.metrics.requests).toBe(1);
            expect(provider.metrics.tokens).toBe(100);
            expect(provider.metrics.cost).toBe(0.05);
            expect(provider.metrics.latency).toContain(500);
            expect(provider.metrics.errors).toBe(0);
        });

        test('should record error metrics', () => {
            const error = new Error('Test error');
            provider.recordMetrics('chat', 0, 0, 500, error);

            expect(provider.metrics.requests).toBe(1);
            expect(provider.metrics.errors).toBe(1);
            expect(provider.metrics.latency).toContain(500);
        });

        test('should limit latency array size', () => {
            // Record more than 100 latency measurements
            for (let i = 0; i < 150; i++) {
                provider.recordMetrics('test', 1, 0, i);
            }

            expect(provider.metrics.latency.length).toBe(100);
            expect(provider.metrics.latency[0]).toBe(50); // First 50 should be removed
        });
    });

    describe('Get Metrics', () => {
        test('should return metrics with average latency', () => {
            provider.recordMetrics('test', 10, 0.01, 100);
            provider.recordMetrics('test', 20, 0.02, 200);

            const metrics = provider.getMetrics();

            expect(metrics.requests).toBe(2);
            expect(metrics.tokens).toBe(30);
            expect(metrics.cost).toBe(0.03);
            expect(metrics.avgLatency).toBe(150);
            expect(metrics.provider).toBe('test-provider');
            expect(metrics.uptime).toBeGreaterThan(0);
        });

        test('should return zero average latency when no measurements', () => {
            const metrics = provider.getMetrics();
            expect(metrics.avgLatency).toBe(0);
        });
    });

    describe('Request Validation', () => {
        test('should validate valid request', () => {
            const request = { messages: [{ role: 'user', content: 'test' }] };
            expect(() => provider.validateRequest(request)).not.toThrow();
        });

        test('should throw error for null request', () => {
            expect(() => provider.validateRequest(null)).toThrow('Request is required');
        });

        test('should throw error for non-object request', () => {
            expect(() => provider.validateRequest('invalid')).toThrow('Request must be an object');
        });
    });

    describe('Error Handling', () => {
        test('should enhance error with provider information', () => {
            const originalError = new Error('Original error');
            const context = { method: 'test' };

            const enhancedError = provider.handleError(originalError, context);

            expect(enhancedError.message).toBe('[test-provider] Original error');
            expect(enhancedError.provider).toBe('test-provider');
            expect(enhancedError.context).toEqual(context);
            expect(enhancedError.originalError).toBe(originalError);
        });
    });

    describe('Retry Logic', () => {
        test('should retry failed operations', async () => {
            let attemptCount = 0;
            const mockFunction = jest.fn(() => {
                attemptCount++;
                if (attemptCount < 3) {
                    throw new Error('Temporary failure');
                }
                return 'success';
            });

            const result = await provider.executeWithRetry(mockFunction, 3, 10);

            expect(result).toBe('success');
            expect(mockFunction).toHaveBeenCalledTimes(3);
        });

        test('should throw error after max retries', async () => {
            const mockFunction = jest.fn(() => {
                throw new Error('Persistent failure');
            });

            await expect(
                provider.executeWithRetry(mockFunction, 2, 10)
            ).rejects.toThrow('[test-provider] Persistent failure');

            expect(mockFunction).toHaveBeenCalledTimes(2);
        });

        test('should succeed on first attempt', async () => {
            const mockFunction = jest.fn(() => 'immediate success');

            const result = await provider.executeWithRetry(mockFunction, 3, 10);

            expect(result).toBe('immediate success');
            expect(mockFunction).toHaveBeenCalledTimes(1);
        });
    });

    describe('Capabilities', () => {
        test('should return default capabilities', () => {
            const capabilities = provider.getCapabilities();

            expect(capabilities).toEqual({
                provider: 'test-provider',
                supportsChatCompletion: true,
                supportsCompletion: true,
                supportsEmbedding: false,
                supportsStreaming: false,
                supportsFunctionCalling: false,
                maxTokens: 4096,
                models: []
            });
        });
    });

    describe('Component Setters', () => {
        test('should set rate limiter', () => {
            const mockRateLimiter = { limit: 100 };
            provider.setRateLimiter(mockRateLimiter);
            expect(provider.rateLimiter).toBe(mockRateLimiter);
        });

        test('should set health checker', () => {
            const mockHealthChecker = { check: true };
            provider.setHealthChecker(mockHealthChecker);
            expect(provider.healthChecker).toBe(mockHealthChecker);
        });

        test('should set cost tracker', () => {
            const mockCostTracker = { track: true };
            provider.setCostTracker(mockCostTracker);
            expect(provider.costTracker).toBe(mockCostTracker);
        });
    });

    describe('Uptime Calculation', () => {
        test('should calculate uptime', () => {
            const uptime1 = provider.getUptime();
            expect(uptime1).toBeGreaterThan(0);

            // Wait a bit and check again
            setTimeout(() => {
                const uptime2 = provider.getUptime();
                expect(uptime2).toBeGreaterThan(uptime1);
            }, 10);
        });
    });

    describe('Abstract Methods', () => {
        test('should throw error for unimplemented methods in base class', async () => {
            const baseProvider = new BaseProvider({
                name: 'base',
                baseUrl: 'test',
                apiKey: 'test'
            });

            await expect(
                baseProvider.generateChatCompletion([])
            ).rejects.toThrow('generateChatCompletion must be implemented by provider subclass');

            await expect(
                baseProvider.generateCompletion('test')
            ).rejects.toThrow('generateCompletion must be implemented by provider subclass');

            await expect(
                baseProvider.generateEmbedding('test')
            ).rejects.toThrow('generateEmbedding must be implemented by provider subclass');
        });
    });
});

// Test suite for provider subclass requirements
describe('Provider Subclass Requirements', () => {
    test('should enforce required method implementations', () => {
        // Test that a subclass must implement abstract methods
        class IncompleteProvider extends BaseProvider {
            // Missing required methods
        }

        const incompleteProvider = new IncompleteProvider({
            name: 'incomplete',
            baseUrl: 'test',
            apiKey: 'test'
        });

        // Should throw errors for unimplemented methods
        expect(async () => {
            await incompleteProvider.generateChatCompletion([]);
        }).rejects;
    });

    test('should work correctly with complete implementation', async () => {
        // MockProvider has all required methods implemented
        const messages = [{ role: 'user', content: 'test' }];
        const result = await provider.generateChatCompletion(messages);

        expect(result).toEqual(provider.mockResponses.chat);
    });
});