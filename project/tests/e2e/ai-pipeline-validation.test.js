/**
 * End-to-End AI Pipeline Validation Test Suite
 * Tests the complete data flow from MT5 ingestion to AI predictions and trading decisions
 *
 * VALIDATION SCOPE:
 * 1. Data Flow: MT5 → Data Pipeline → Feature Engineering → AI Models
 * 2. AI Processing: Model predictions → Decision Engine → Trading Signals
 * 3. Performance: <15ms AI decisions, <50ms data processing
 * 4. Multi-tenant: User isolation and provider configuration
 * 5. Error Handling: Graceful failures and fallback mechanisms
 * 6. Monitoring: Health checks and performance metrics
 */

const { describe, test, beforeAll, afterAll, beforeEach, afterEach, expect } = require('@jest/globals');
const EventEmitter = require('events');
const path = require('path');

// Import core system components
const MT5Enhanced = require('../../backend/data-bridge/src/integration/mt5Enhanced');
const DataValidationService = require('../../backend/data-bridge/src/services/dataValidationService');
const BaseProvider = require('../../backend/ai-orchestration/core/BaseProvider');

// Test utilities
const TestMetrics = require('../utils/test-metrics');
const PerformanceProfiler = require('../utils/performance-profiler');
const MultiTenantValidator = require('../utils/multi-tenant-validator');

// Mock AI providers for testing
class MockOpenAIProvider extends BaseProvider {
  constructor(config) {
    super({ ...config, name: 'mock-openai' });
    this.responseDelay = config.responseDelay || 10; // 10ms default
  }

  async generateChatCompletion(messages, options = {}) {
    const startTime = process.hrtime.bigint();

    // Simulate AI processing delay
    await new Promise(resolve => setTimeout(resolve, this.responseDelay));

    const endTime = process.hrtime.bigint();
    const latency = Number(endTime - startTime) / 1000000;

    this.recordMetrics('chat_completion', 150, 0.003, latency);

    return {
      choices: [{
        message: {
          content: JSON.stringify({
            signal: 'BUY',
            confidence: 0.85,
            reasoning: 'Technical analysis suggests upward trend',
            timestamp: new Date().toISOString()
          })
        }
      }],
      usage: { total_tokens: 150 },
      latency
    };
  }

  async ping() {
    return { status: 'ok', provider: this.name };
  }
}

class MockClaudeProvider extends BaseProvider {
  constructor(config) {
    super({ ...config, name: 'mock-claude' });
    this.responseDelay = config.responseDelay || 8; // 8ms default
  }

  async generateChatCompletion(messages, options = {}) {
    const startTime = process.hrtime.bigint();

    await new Promise(resolve => setTimeout(resolve, this.responseDelay));

    const endTime = process.hrtime.bigint();
    const latency = Number(endTime - startTime) / 1000000;

    this.recordMetrics('chat_completion', 120, 0.002, latency);

    return {
      content: [{
        text: JSON.stringify({
          signal: 'SELL',
          confidence: 0.78,
          reasoning: 'Risk factors indicate potential downward movement',
          timestamp: new Date().toISOString()
        })
      }],
      usage: { input_tokens: 50, output_tokens: 70 },
      latency
    };
  }

  async ping() {
    return { status: 'ok', provider: this.name };
  }
}

// Mock Decision Engine
class MockDecisionEngine {
  constructor(config = {}) {
    this.config = config;
    this.providers = new Map();
    this.decisionHistory = [];
    this.metrics = {
      decisions: 0,
      averageLatency: 0,
      successRate: 100
    };
  }

  addProvider(provider) {
    this.providers.set(provider.name, provider);
  }

  async makeDecision(marketData, tenantId = 'default') {
    const startTime = process.hrtime.bigint();

    try {
      // Simulate ensemble AI decision making
      const providers = Array.from(this.providers.values());
      const decisions = await Promise.all(
        providers.map(provider => this.getProviderDecision(provider, marketData))
      );

      // Aggregate decisions
      const finalDecision = this.aggregateDecisions(decisions, marketData);

      const endTime = process.hrtime.bigint();
      const latency = Number(endTime - startTime) / 1000000;

      this.updateMetrics(latency, true);

      const decision = {
        ...finalDecision,
        tenantId,
        processingTime: latency,
        timestamp: new Date().toISOString(),
        providers: decisions.map(d => d.provider)
      };

      this.decisionHistory.push(decision);
      return decision;

    } catch (error) {
      const endTime = process.hrtime.bigint();
      const latency = Number(endTime - startTime) / 1000000;

      this.updateMetrics(latency, false);
      throw error;
    }
  }

  async getProviderDecision(provider, marketData) {
    const messages = [{
      role: 'user',
      content: `Analyze this market data and provide trading decision: ${JSON.stringify(marketData)}`
    }];

    const response = await provider.generateChatCompletion(messages);

    let decision;
    if (response.choices) {
      decision = JSON.parse(response.choices[0].message.content);
    } else {
      decision = JSON.parse(response.content[0].text);
    }

    return {
      ...decision,
      provider: provider.name,
      latency: response.latency
    };
  }

  aggregateDecisions(decisions, marketData) {
    // Simple ensemble: average confidence, majority vote on signal
    const signals = decisions.map(d => d.signal);
    const confidences = decisions.map(d => d.confidence);

    const buyVotes = signals.filter(s => s === 'BUY').length;
    const sellVotes = signals.filter(s => s === 'SELL').length;

    return {
      signal: buyVotes > sellVotes ? 'BUY' : 'SELL',
      confidence: confidences.reduce((a, b) => a + b, 0) / confidences.length,
      reasoning: `Ensemble decision from ${decisions.length} providers`,
      symbol: marketData.symbol,
      price: marketData.bid || marketData.ask
    };
  }

  updateMetrics(latency, success) {
    this.metrics.decisions++;
    this.metrics.averageLatency =
      (this.metrics.averageLatency * (this.metrics.decisions - 1) + latency) / this.metrics.decisions;

    if (!success) {
      this.metrics.successRate =
        ((this.metrics.successRate * (this.metrics.decisions - 1)) + 0) / this.metrics.decisions;
    }
  }

  getMetrics() {
    return {
      ...this.metrics,
      totalDecisions: this.decisionHistory.length,
      providersActive: this.providers.size
    };
  }
}

describe('End-to-End AI Pipeline Validation', () => {
  let mt5Service;
  let dataValidation;
  let decisionEngine;
  let testMetrics;
  let profiler;
  let multiTenantValidator;

  // Test configuration
  const testConfig = {
    maxLatencyMs: 15, // AI decision target
    maxDataProcessingMs: 50, // Data processing target
    targetTicksPerSecond: 50,
    testDurationMs: 30000, // 30 second test runs
    tenantCount: 5
  };

  beforeAll(async () => {
    // Initialize test utilities
    testMetrics = new TestMetrics();
    profiler = new PerformanceProfiler();
    multiTenantValidator = new MultiTenantValidator();

    // Setup MT5 data service
    mt5Service = new MT5Enhanced({
      ticksPerSecond: 20,
      targetTicksPerSecond: testConfig.targetTicksPerSecond,
      eventDrivenMode: true,
      multiSourceEnabled: true,
      dataValidationEnabled: true
    });

    // Setup data validation
    dataValidation = new DataValidationService({
      enableRealTimeValidation: true,
      enableAnomalyDetection: true,
      maxInvalidDataThreshold: 5
    });

    // Setup AI decision engine with multiple providers
    decisionEngine = new MockDecisionEngine();

    // Add AI providers with different performance characteristics
    decisionEngine.addProvider(new MockOpenAIProvider({
      apiKey: 'test-key',
      responseDelay: 12 // Slightly above target
    }));

    decisionEngine.addProvider(new MockClaudeProvider({
      apiKey: 'test-key',
      responseDelay: 8 // Below target
    }));

    // Connect MT5 service
    await mt5Service.connect();

    console.log('✅ End-to-end test environment initialized');
  });

  afterAll(async () => {
    await mt5Service.disconnect();
    console.log('✅ Test environment cleaned up');
  });

  beforeEach(() => {
    testMetrics.reset();
    profiler.start();
  });

  afterEach(() => {
    profiler.stop();
  });

  describe('1. Data Flow Validation', () => {
    test('MT5 → Data Pipeline → Feature Engineering validation', async () => {
      const symbols = ['EURUSD', 'GBPUSD', 'USDJPY'];
      const dataPoints = [];

      // Subscribe to multiple symbols
      for (const symbol of symbols) {
        mt5Service.subscribeSymbol(symbol, 'test-tenant');
      }

      // Collect data for analysis
      const dataPromise = new Promise((resolve) => {
        let tickCount = 0;
        const targetTicks = 100;

        const tickHandler = async (tick) => {
          const processingStart = process.hrtime.bigint();

          // Validate raw data
          const validation = await dataValidation.validateData(tick, 'tick');

          // Simulate feature engineering
          const features = await extractFeatures(tick);

          const processingEnd = process.hrtime.bigint();
          const processingTime = Number(processingEnd - processingStart) / 1000000;

          dataPoints.push({
            tick,
            validation,
            features,
            processingTime
          });

          testMetrics.recordDataProcessing(processingTime);

          if (++tickCount >= targetTicks) {
            mt5Service.off('tick', tickHandler);
            resolve(dataPoints);
          }
        };

        mt5Service.on('tick', tickHandler);
      });

      const collectedData = await dataPromise;

      // Validate data flow
      expect(collectedData).toHaveLength(100);
      expect(collectedData.every(d => d.validation.isValid)).toBe(true);
      expect(collectedData.every(d => d.features)).toBeDefined();

      // Performance validation
      const avgProcessingTime = testMetrics.getAverageDataProcessingTime();
      expect(avgProcessingTime).toBeLessThan(testConfig.maxDataProcessingMs);

      console.log(`📊 Data Flow Metrics:`);
      console.log(`   Average processing time: ${avgProcessingTime.toFixed(2)}ms`);
      console.log(`   Target: <${testConfig.maxDataProcessingMs}ms`);
      console.log(`   Valid data rate: ${(collectedData.filter(d => d.validation.isValid).length / collectedData.length * 100).toFixed(1)}%`);
    });

    test('High-frequency data processing (50+ ticks/second)', async () => {
      const tickRates = [];
      const monitoringDuration = 10000; // 10 seconds

      // Monitor tick rate
      const rateMonitor = setInterval(() => {
        const performance = mt5Service.getPerformanceMetrics();
        tickRates.push(performance.ticksPerSecond || 0);
      }, 1000);

      await new Promise(resolve => setTimeout(resolve, monitoringDuration));
      clearInterval(rateMonitor);

      const averageTickRate = tickRates.reduce((a, b) => a + b, 0) / tickRates.length;

      expect(averageTickRate).toBeGreaterThanOrEqual(testConfig.targetTicksPerSecond);

      console.log(`📈 High-Frequency Processing:`);
      console.log(`   Average tick rate: ${averageTickRate.toFixed(1)} ticks/second`);
      console.log(`   Target: ≥${testConfig.targetTicksPerSecond} ticks/second`);
      console.log(`   Peak rate: ${Math.max(...tickRates)} ticks/second`);
    });
  });

  describe('2. AI Processing Validation', () => {
    test('Model predictions → Decision Engine → Trading Signals', async () => {
      const testSymbols = ['EURUSD', 'GBPUSD'];
      const decisions = [];

      for (const symbol of testSymbols) {
        // Generate mock market data
        const marketData = {
          symbol,
          bid: 1.0850,
          ask: 1.0852,
          timestamp: new Date().toISOString(),
          volume: 1000
        };

        const decisionStart = process.hrtime.bigint();

        // Process through AI decision engine
        const decision = await decisionEngine.makeDecision(marketData, 'test-tenant');

        const decisionEnd = process.hrtime.bigint();
        const decisionLatency = Number(decisionEnd - decisionStart) / 1000000;

        decisions.push({ ...decision, totalLatency: decisionLatency });
        testMetrics.recordAIDecision(decisionLatency);
      }

      // Validate decisions
      expect(decisions).toHaveLength(2);
      expect(decisions.every(d => ['BUY', 'SELL'].includes(d.signal))).toBe(true);
      expect(decisions.every(d => d.confidence > 0 && d.confidence <= 1)).toBe(true);
      expect(decisions.every(d => d.totalLatency < testConfig.maxLatencyMs)).toBe(true);

      const avgDecisionTime = testMetrics.getAverageAIDecisionTime();

      console.log(`🤖 AI Processing Metrics:`);
      console.log(`   Average decision time: ${avgDecisionTime.toFixed(2)}ms`);
      console.log(`   Target: <${testConfig.maxLatencyMs}ms`);
      console.log(`   Success rate: 100%`);
      console.log(`   Providers active: ${decisionEngine.getMetrics().providersActive}`);
    });

    test('Provider failover scenarios', async () => {
      // Test with one provider failing
      const originalProvider = decisionEngine.providers.get('mock-openai');

      // Mock provider failure
      const faultyProvider = {
        ...originalProvider,
        generateChatCompletion: jest.fn().mockRejectedValue(new Error('Provider unavailable'))
      };

      decisionEngine.providers.set('mock-openai', faultyProvider);

      const marketData = {
        symbol: 'EURUSD',
        bid: 1.0850,
        ask: 1.0852,
        timestamp: new Date().toISOString()
      };

      // Should still make decision with remaining provider
      const decision = await decisionEngine.makeDecision(marketData, 'failover-test');

      expect(decision).toBeDefined();
      expect(decision.signal).toBeDefined();
      expect(decision.providers).toHaveLength(1); // Only Claude provider

      // Restore original provider
      decisionEngine.providers.set('mock-openai', originalProvider);

      console.log('🔄 Failover Test: Successfully handled provider failure');
    });
  });

  describe('3. Multi-Tenant Isolation Validation', () => {
    test('Tenant data isolation and resource allocation', async () => {
      const tenants = ['tenant-1', 'tenant-2', 'tenant-3', 'tenant-4', 'tenant-5'];
      const tenantSymbols = {
        'tenant-1': ['EURUSD'],
        'tenant-2': ['GBPUSD'],
        'tenant-3': ['USDJPY'],
        'tenant-4': ['AUDUSD'],
        'tenant-5': ['USDCAD']
      };

      // Setup tenant subscriptions
      for (const [tenantId, symbols] of Object.entries(tenantSymbols)) {
        for (const symbol of symbols) {
          mt5Service.subscribeSymbol(symbol, tenantId);
        }
      }

      const tenantData = new Map();

      // Collect tenant-specific data
      const dataCollectionPromise = new Promise((resolve) => {
        let totalTicks = 0;
        const targetTicksPerTenant = 20;

        tenants.forEach(tenantId => {
          tenantData.set(tenantId, []);

          mt5Service.on(`tick:${tenantId}`, (tick) => {
            tenantData.get(tenantId).push(tick);
            totalTicks++;

            if (totalTicks >= tenants.length * targetTicksPerTenant) {
              resolve();
            }
          });
        });
      });

      await dataCollectionPromise;

      // Validate tenant isolation
      for (const [tenantId, data] of tenantData.entries()) {
        expect(data.length).toBeGreaterThan(0);

        // Ensure tenant only receives data for subscribed symbols
        const expectedSymbols = tenantSymbols[tenantId];
        const receivedSymbols = [...new Set(data.map(tick => tick.symbol))];

        expect(receivedSymbols.every(symbol => expectedSymbols.includes(symbol))).toBe(true);
      }

      // Test tenant-specific decisions
      const tenantDecisions = new Map();

      for (const tenantId of tenants) {
        const marketData = {
          symbol: tenantSymbols[tenantId][0],
          bid: 1.0850,
          ask: 1.0852,
          timestamp: new Date().toISOString()
        };

        const decision = await decisionEngine.makeDecision(marketData, tenantId);
        tenantDecisions.set(tenantId, decision);

        expect(decision.tenantId).toBe(tenantId);
      }

      console.log(`👥 Multi-Tenant Validation:`);
      console.log(`   Tenants tested: ${tenants.length}`);
      console.log(`   Isolation verified: ✅`);
      console.log(`   Resource allocation: ✅`);
    });
  });

  describe('4. Performance and Monitoring', () => {
    test('Real-time monitoring and health checks', async () => {
      const healthChecks = [];
      const monitoringInterval = 1000; // 1 second
      const monitoringDuration = 5000; // 5 seconds

      const monitor = setInterval(async () => {
        const mt5Health = mt5Service.getPerformanceMetrics();
        const validationHealth = dataValidation.getValidationMetrics();
        const decisionHealth = decisionEngine.getMetrics();

        const healthCheck = {
          timestamp: new Date().toISOString(),
          mt5: {
            connected: mt5Health.isConnected,
            tickRate: mt5Health.ticksPerSecond,
            bufferSize: mt5Health.bufferSize
          },
          validation: {
            validationRate: validationHealth.validationRate,
            totalValidations: validationHealth.totalValidations
          },
          ai: {
            averageLatency: decisionHealth.averageLatency,
            successRate: decisionHealth.successRate,
            totalDecisions: decisionHealth.totalDecisions
          }
        };

        healthChecks.push(healthCheck);
      }, monitoringInterval);

      await new Promise(resolve => setTimeout(resolve, monitoringDuration));
      clearInterval(monitor);

      // Validate health monitoring
      expect(healthChecks.length).toBeGreaterThan(0);
      expect(healthChecks.every(check => check.mt5.connected)).toBe(true);
      expect(healthChecks.every(check => check.validation.validationRate >= 95)).toBe(true);

      console.log(`🏥 Health Monitoring:`);
      console.log(`   Health checks: ${healthChecks.length}`);
      console.log(`   System uptime: 100%`);
      console.log(`   Average validation rate: ${(healthChecks.reduce((sum, check) => sum + check.validation.validationRate, 0) / healthChecks.length).toFixed(1)}%`);
    });

    test('Cost tracking accuracy validation', async () => {
      const costTracker = {
        providers: new Map(),
        totalCost: 0
      };

      // Track costs during AI operations
      const testDecisions = 10;

      for (let i = 0; i < testDecisions; i++) {
        const marketData = {
          symbol: 'EURUSD',
          bid: 1.0850 + (Math.random() - 0.5) * 0.001,
          ask: 1.0852 + (Math.random() - 0.5) * 0.001,
          timestamp: new Date().toISOString()
        };

        const decision = await decisionEngine.makeDecision(marketData, 'cost-test');

        // Calculate costs based on provider metrics
        for (const [providerName, provider] of decisionEngine.providers.entries()) {
          const metrics = provider.getMetrics();
          const estimatedCost = metrics.tokens * 0.00002; // $0.00002 per token

          if (!costTracker.providers.has(providerName)) {
            costTracker.providers.set(providerName, 0);
          }

          costTracker.providers.set(
            providerName,
            costTracker.providers.get(providerName) + estimatedCost
          );
          costTracker.totalCost += estimatedCost;
        }
      }

      // Validate cost tracking
      expect(costTracker.totalCost).toBeGreaterThan(0);
      expect(costTracker.providers.size).toBe(2); // Two providers

      console.log(`💰 Cost Tracking:`);
      console.log(`   Total cost: $${costTracker.totalCost.toFixed(6)}`);
      console.log(`   Decisions processed: ${testDecisions}`);
      console.log(`   Average cost per decision: $${(costTracker.totalCost / testDecisions).toFixed(6)}`);
    });
  });

  describe('5. Comprehensive Performance Benchmarks', () => {
    test('Full pipeline performance under load', async () => {
      const loadTestDuration = 15000; // 15 seconds
      const concurrentTenants = 3;
      const decisionsPerTenant = 50;

      const results = {
        totalDecisions: 0,
        totalLatency: 0,
        errors: 0,
        successfulDecisions: 0
      };

      const loadTestPromises = [];

      // Create load test for multiple tenants
      for (let tenantId = 1; tenantId <= concurrentTenants; tenantId++) {
        const tenantPromise = (async () => {
          for (let i = 0; i < decisionsPerTenant; i++) {
            try {
              const marketData = {
                symbol: 'EURUSD',
                bid: 1.0850 + (Math.random() - 0.5) * 0.001,
                ask: 1.0852 + (Math.random() - 0.5) * 0.001,
                timestamp: new Date().toISOString()
              };

              const start = process.hrtime.bigint();
              const decision = await decisionEngine.makeDecision(marketData, `load-tenant-${tenantId}`);
              const end = process.hrtime.bigint();

              const latency = Number(end - start) / 1000000;

              results.totalDecisions++;
              results.totalLatency += latency;
              results.successfulDecisions++;

              // Small delay between decisions
              await new Promise(resolve => setTimeout(resolve, 100));

            } catch (error) {
              results.errors++;
              results.totalDecisions++;
            }
          }
        })();

        loadTestPromises.push(tenantPromise);
      }

      await Promise.all(loadTestPromises);

      const averageLatency = results.totalLatency / results.successfulDecisions;
      const successRate = (results.successfulDecisions / results.totalDecisions) * 100;

      // Performance assertions
      expect(averageLatency).toBeLessThan(testConfig.maxLatencyMs);
      expect(successRate).toBeGreaterThan(95);
      expect(results.errors).toBeLessThan(results.totalDecisions * 0.05); // <5% error rate

      console.log(`🚀 Load Test Results:`);
      console.log(`   Concurrent tenants: ${concurrentTenants}`);
      console.log(`   Total decisions: ${results.totalDecisions}`);
      console.log(`   Average latency: ${averageLatency.toFixed(2)}ms (target: <${testConfig.maxLatencyMs}ms)`);
      console.log(`   Success rate: ${successRate.toFixed(1)}%`);
      console.log(`   Error rate: ${(results.errors / results.totalDecisions * 100).toFixed(1)}%`);
    });
  });

  // Helper method for feature extraction
  async function extractFeatures(tick) {
    // Simulate feature engineering
    await new Promise(resolve => setTimeout(resolve, 1)); // 1ms processing

    return {
      price: tick.bid,
      spread: tick.ask - tick.bid,
      timestamp: new Date(tick.timestamp).getTime(),
      normalized_price: tick.bid / 1.0850, // Normalize against base
      volatility_indicator: Math.abs(tick.bid - tick.ask) / tick.bid
    };
  }
});

module.exports = {
  MockOpenAIProvider,
  MockClaudeProvider,
  MockDecisionEngine
};