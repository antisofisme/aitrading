/**
 * AI Performance Benchmarks Test Suite
 * Comprehensive performance testing for AI decision-making components
 */

const { describe, test, beforeAll, afterAll, expect } = require('@jest/globals');
const { MockOpenAIProvider, MockClaudeProvider, MockDecisionEngine } = require('../e2e/ai-pipeline-validation.test');
const TestMetrics = require('../utils/test-metrics');
const PerformanceProfiler = require('../utils/performance-profiler');

describe('AI Performance Benchmarks', () => {
  let providers;
  let decisionEngine;
  let testMetrics;
  let profiler;

  const performanceTargets = {
    maxLatencyMs: 15,
    minThroughput: 100, // decisions per second
    maxMemoryUsageMB: 500,
    minSuccessRate: 99.0
  };

  beforeAll(async () => {
    testMetrics = new TestMetrics();
    profiler = new PerformanceProfiler();

    // Initialize AI providers with different configurations
    providers = {
      fastProvider: new MockOpenAIProvider({
        apiKey: 'test-key',
        responseDelay: 5 // Very fast
      }),
      standardProvider: new MockClaudeProvider({
        apiKey: 'test-key',
        responseDelay: 10 // Standard speed
      }),
      slowProvider: new MockOpenAIProvider({
        apiKey: 'test-key',
        responseDelay: 20 // Slower
      })
    };

    decisionEngine = new MockDecisionEngine();

    console.log('🚀 AI Performance benchmark environment initialized');
  });

  afterAll(() => {
    console.log('✅ AI Performance benchmarks completed');
  });

  describe('1. Individual Provider Performance', () => {
    test('OpenAI provider latency benchmark', async () => {
      const provider = providers.fastProvider;
      const iterations = 100;
      const latencies = [];

      profiler.start();

      for (let i = 0; i < iterations; i++) {
        const start = process.hrtime.bigint();

        await provider.generateChatCompletion([{
          role: 'user',
          content: 'Analyze market data and provide trading signal'
        }]);

        const end = process.hrtime.bigint();
        const latency = Number(end - start) / 1000000;
        latencies.push(latency);
      }

      const report = profiler.stop();

      // Performance analysis
      const avgLatency = latencies.reduce((a, b) => a + b, 0) / latencies.length;
      const p95Latency = latencies.sort((a, b) => a - b)[Math.floor(iterations * 0.95)];
      const maxLatency = Math.max(...latencies);
      const minLatency = Math.min(...latencies);

      // Assertions
      expect(avgLatency).toBeLessThan(performanceTargets.maxLatencyMs);
      expect(p95Latency).toBeLessThan(performanceTargets.maxLatencyMs * 1.5);

      console.log(`📊 OpenAI Provider Performance:`);
      console.log(`   Average latency: ${avgLatency.toFixed(2)}ms`);
      console.log(`   P95 latency: ${p95Latency.toFixed(2)}ms`);
      console.log(`   Min/Max: ${minLatency.toFixed(2)}ms / ${maxLatency.toFixed(2)}ms`);
      console.log(`   Target: <${performanceTargets.maxLatencyMs}ms`);
    });

    test('Claude provider latency benchmark', async () => {
      const provider = providers.standardProvider;
      const iterations = 100;
      const latencies = [];

      for (let i = 0; i < iterations; i++) {
        const start = process.hrtime.bigint();

        await provider.generateChatCompletion([{
          role: 'user',
          content: 'Analyze market trends and provide recommendations'
        }]);

        const end = process.hrtime.bigint();
        const latency = Number(end - start) / 1000000;
        latencies.push(latency);
      }

      const avgLatency = latencies.reduce((a, b) => a + b, 0) / latencies.length;
      const p95Latency = latencies.sort((a, b) => a - b)[Math.floor(iterations * 0.95)];

      expect(avgLatency).toBeLessThan(performanceTargets.maxLatencyMs);

      console.log(`📊 Claude Provider Performance:`);
      console.log(`   Average latency: ${avgLatency.toFixed(2)}ms`);
      console.log(`   P95 latency: ${p95Latency.toFixed(2)}ms`);
    });

    test('Provider health check performance', async () => {
      const healthCheckLatencies = [];

      for (const [name, provider] of Object.entries(providers)) {
        const iterations = 50;
        const latencies = [];

        for (let i = 0; i < iterations; i++) {
          const start = process.hrtime.bigint();
          await provider.healthCheck();
          const end = process.hrtime.bigint();

          const latency = Number(end - start) / 1000000;
          latencies.push(latency);
        }

        const avgLatency = latencies.reduce((a, b) => a + b, 0) / latencies.length;
        healthCheckLatencies.push({ provider: name, avgLatency });

        // Health checks should be very fast (<5ms)
        expect(avgLatency).toBeLessThan(5);
      }

      console.log(`🏥 Health Check Performance:`);
      healthCheckLatencies.forEach(({ provider, avgLatency }) => {
        console.log(`   ${provider}: ${avgLatency.toFixed(2)}ms`);
      });
    });
  });

  describe('2. Decision Engine Performance', () => {
    test('Single decision latency benchmark', async () => {
      // Add all providers to decision engine
      Object.values(providers).forEach(provider => {
        decisionEngine.addProvider(provider);
      });

      const iterations = 50;
      const latencies = [];

      for (let i = 0; i < iterations; i++) {
        const marketData = {
          symbol: 'EURUSD',
          bid: 1.0850 + (Math.random() - 0.5) * 0.001,
          ask: 1.0852 + (Math.random() - 0.5) * 0.001,
          timestamp: new Date().toISOString()
        };

        const start = process.hrtime.bigint();
        const decision = await decisionEngine.makeDecision(marketData, 'benchmark-tenant');
        const end = process.hrtime.bigint();

        const latency = Number(end - start) / 1000000;
        latencies.push(latency);

        // Validate decision structure
        expect(decision.signal).toBeDefined();
        expect(decision.confidence).toBeDefined();
        expect(decision.processingTime).toBeDefined();
      }

      const avgLatency = latencies.reduce((a, b) => a + b, 0) / latencies.length;
      const p95Latency = latencies.sort((a, b) => a - b)[Math.floor(iterations * 0.95)];

      expect(avgLatency).toBeLessThan(performanceTargets.maxLatencyMs);

      console.log(`🤖 Decision Engine Performance:`);
      console.log(`   Average decision latency: ${avgLatency.toFixed(2)}ms`);
      console.log(`   P95 latency: ${p95Latency.toFixed(2)}ms`);
      console.log(`   Providers used: ${decisionEngine.providers.size}`);
    });

    test('Throughput benchmark - decisions per second', async () => {
      const testDuration = 10000; // 10 seconds
      const startTime = Date.now();
      let decisionsCompleted = 0;
      const errors = [];

      // Generate decisions as fast as possible for test duration
      const decisionPromises = [];

      while (Date.now() - startTime < testDuration) {
        const marketData = {
          symbol: 'EURUSD',
          bid: 1.0850 + (Math.random() - 0.5) * 0.001,
          ask: 1.0852 + (Math.random() - 0.5) * 0.001,
          timestamp: new Date().toISOString()
        };

        const decisionPromise = decisionEngine.makeDecision(marketData, 'throughput-test')
          .then(() => {
            decisionsCompleted++;
          })
          .catch(error => {
            errors.push(error);
          });

        decisionPromises.push(decisionPromise);

        // Small delay to prevent overwhelming the system
        await new Promise(resolve => setTimeout(resolve, 10));
      }

      // Wait for all decisions to complete
      await Promise.all(decisionPromises);

      const actualDuration = Date.now() - startTime;
      const throughput = (decisionsCompleted / actualDuration) * 1000; // decisions per second
      const errorRate = (errors.length / (decisionsCompleted + errors.length)) * 100;

      // Performance assertions
      expect(throughput).toBeGreaterThan(performanceTargets.minThroughput);
      expect(errorRate).toBeLessThan(1); // <1% error rate

      console.log(`⚡ Throughput Benchmark:`);
      console.log(`   Decisions completed: ${decisionsCompleted}`);
      console.log(`   Test duration: ${actualDuration}ms`);
      console.log(`   Throughput: ${throughput.toFixed(1)} decisions/second`);
      console.log(`   Target: >${performanceTargets.minThroughput} decisions/second`);
      console.log(`   Error rate: ${errorRate.toFixed(2)}%`);
    });

    test('Concurrent decision handling', async () => {
      const concurrencyLevels = [10, 25, 50, 100];
      const results = [];

      for (const concurrency of concurrencyLevels) {
        const decisions = [];
        const startTime = Date.now();

        // Create concurrent decisions
        const decisionPromises = Array.from({ length: concurrency }, async (_, i) => {
          const marketData = {
            symbol: `TEST${i % 5}`, // Rotate through 5 symbols
            bid: 1.0850 + (Math.random() - 0.5) * 0.001,
            ask: 1.0852 + (Math.random() - 0.5) * 0.001,
            timestamp: new Date().toISOString()
          };

          const decision = await decisionEngine.makeDecision(marketData, `concurrent-${i}`);
          return decision;
        });

        const completedDecisions = await Promise.all(decisionPromises);
        const endTime = Date.now();

        const totalLatency = endTime - startTime;
        const avgLatency = totalLatency / concurrency;

        results.push({
          concurrency,
          totalLatency,
          avgLatency,
          successfulDecisions: completedDecisions.length
        });

        // All decisions should complete successfully
        expect(completedDecisions).toHaveLength(concurrency);
        expect(completedDecisions.every(d => d.signal)).toBe(true);
      }

      console.log(`🔄 Concurrent Decision Handling:`);
      results.forEach(result => {
        console.log(`   Concurrency ${result.concurrency}: ${result.avgLatency.toFixed(2)}ms avg latency`);
      });

      // Performance should degrade gracefully with increased concurrency
      const latencyIncrease = results[results.length - 1].avgLatency / results[0].avgLatency;
      expect(latencyIncrease).toBeLessThan(5); // Should not increase more than 5x
    });
  });

  describe('3. Memory and Resource Usage', () => {
    test('Memory usage during sustained operation', async () => {
      const initialMemory = process.memoryUsage();
      const iterations = 200;
      const memorySnapshots = [];

      // Capture memory usage during operation
      for (let i = 0; i < iterations; i++) {
        const marketData = {
          symbol: 'EURUSD',
          bid: 1.0850 + (Math.random() - 0.5) * 0.001,
          ask: 1.0852 + (Math.random() - 0.5) * 0.001,
          timestamp: new Date().toISOString()
        };

        await decisionEngine.makeDecision(marketData, 'memory-test');

        // Capture memory every 20 iterations
        if (i % 20 === 0) {
          memorySnapshots.push({
            iteration: i,
            memory: process.memoryUsage()
          });
        }
      }

      const finalMemory = process.memoryUsage();
      const memoryIncrease = finalMemory.heapUsed - initialMemory.heapUsed;
      const memoryIncreasePercentage = (memoryIncrease / initialMemory.heapUsed) * 100;

      // Memory should not increase significantly (< 50% growth)
      expect(memoryIncreasePercentage).toBeLessThan(50);

      console.log(`💾 Memory Usage Analysis:`);
      console.log(`   Initial heap: ${(initialMemory.heapUsed / 1024 / 1024).toFixed(2)}MB`);
      console.log(`   Final heap: ${(finalMemory.heapUsed / 1024 / 1024).toFixed(2)}MB`);
      console.log(`   Memory increase: ${(memoryIncrease / 1024 / 1024).toFixed(2)}MB (${memoryIncreasePercentage.toFixed(1)}%)`);
      console.log(`   Target: <${performanceTargets.maxMemoryUsageMB}MB total`);
    });

    test('Garbage collection impact', async () => {
      // Force garbage collection before test
      if (global.gc) {
        global.gc();
      }

      const preGCMemory = process.memoryUsage();

      // Perform operations that create objects
      for (let i = 0; i < 100; i++) {
        const marketData = {
          symbol: 'EURUSD',
          bid: 1.0850 + (Math.random() - 0.5) * 0.001,
          ask: 1.0852 + (Math.random() - 0.5) * 0.001,
          timestamp: new Date().toISOString(),
          // Add some extra data to increase memory usage
          metadata: {
            iteration: i,
            randomData: Array.from({ length: 100 }, () => Math.random())
          }
        };

        await decisionEngine.makeDecision(marketData, 'gc-test');
      }

      const preGCMemoryAfter = process.memoryUsage();

      // Force garbage collection
      if (global.gc) {
        global.gc();
      }

      const postGCMemory = process.memoryUsage();

      const gcReclaimed = preGCMemoryAfter.heapUsed - postGCMemory.heapUsed;
      const gcEfficiency = (gcReclaimed / preGCMemoryAfter.heapUsed) * 100;

      console.log(`🗑️  Garbage Collection Analysis:`);
      console.log(`   Pre-operations: ${(preGCMemory.heapUsed / 1024 / 1024).toFixed(2)}MB`);
      console.log(`   Pre-GC: ${(preGCMemoryAfter.heapUsed / 1024 / 1024).toFixed(2)}MB`);
      console.log(`   Post-GC: ${(postGCMemory.heapUsed / 1024 / 1024).toFixed(2)}MB`);
      console.log(`   Reclaimed: ${(gcReclaimed / 1024 / 1024).toFixed(2)}MB (${gcEfficiency.toFixed(1)}%)`);

      // GC should reclaim at least some memory
      expect(gcReclaimed).toBeGreaterThan(0);
    });
  });

  describe('4. Error Handling and Recovery', () => {
    test('Provider failure handling performance', async () => {
      // Create a failing provider
      const failingProvider = {
        name: 'failing-provider',
        generateChatCompletion: jest.fn().mockRejectedValue(new Error('Provider failed')),
        getMetrics: () => ({ requests: 0, errors: 1, tokens: 0, cost: 0 })
      };

      decisionEngine.addProvider(failingProvider);

      const iterations = 20;
      const latencies = [];
      const successCount = { success: 0, failure: 0 };

      for (let i = 0; i < iterations; i++) {
        const marketData = {
          symbol: 'EURUSD',
          bid: 1.0850,
          ask: 1.0852,
          timestamp: new Date().toISOString()
        };

        const start = process.hrtime.bigint();

        try {
          const decision = await decisionEngine.makeDecision(marketData, 'failure-test');
          const end = process.hrtime.bigint();
          const latency = Number(end - start) / 1000000;

          latencies.push(latency);
          successCount.success++;

          // Should still get valid decisions from working providers
          expect(decision.signal).toBeDefined();
        } catch (error) {
          successCount.failure++;
        }
      }

      // Remove failing provider
      decisionEngine.providers.delete('failing-provider');

      const avgLatency = latencies.length > 0 ? latencies.reduce((a, b) => a + b, 0) / latencies.length : 0;
      const successRate = (successCount.success / iterations) * 100;

      // Should maintain reasonable performance despite failures
      expect(successRate).toBeGreaterThan(50); // At least 50% success
      if (latencies.length > 0) {
        expect(avgLatency).toBeLessThan(performanceTargets.maxLatencyMs * 2); // Allow 2x latency during failures
      }

      console.log(`🚨 Failure Handling Performance:`);
      console.log(`   Success rate: ${successRate.toFixed(1)}%`);
      console.log(`   Average latency (successful): ${avgLatency.toFixed(2)}ms`);
      console.log(`   Successful decisions: ${successCount.success}/${iterations}`);
    });

    test('Recovery time after provider restoration', async () => {
      const workingProvider = providers.fastProvider;

      // Simulate provider going down and coming back up
      const originalMethod = workingProvider.generateChatCompletion;

      // Make provider fail
      workingProvider.generateChatCompletion = jest.fn().mockRejectedValue(new Error('Temporary failure'));

      // Try some decisions while provider is down
      let failureCount = 0;
      for (let i = 0; i < 5; i++) {
        try {
          await decisionEngine.makeDecision({
            symbol: 'EURUSD',
            bid: 1.0850,
            ask: 1.0852,
            timestamp: new Date().toISOString()
          }, 'recovery-test');
        } catch (error) {
          failureCount++;
        }
      }

      // Restore provider
      workingProvider.generateChatCompletion = originalMethod;

      // Measure recovery time
      const recoveryStart = Date.now();
      let recoverySuccessful = false;

      for (let i = 0; i < 10 && !recoverySuccessful; i++) {
        try {
          const decision = await decisionEngine.makeDecision({
            symbol: 'EURUSD',
            bid: 1.0850,
            ask: 1.0852,
            timestamp: new Date().toISOString()
          }, 'recovery-test');

          if (decision.signal) {
            recoverySuccessful = true;
          }
        } catch (error) {
          // Continue trying
        }

        await new Promise(resolve => setTimeout(resolve, 100)); // Wait 100ms between attempts
      }

      const recoveryTime = Date.now() - recoveryStart;

      expect(recoverySuccessful).toBe(true);
      expect(recoveryTime).toBeLessThan(2000); // Should recover within 2 seconds

      console.log(`🔄 Recovery Performance:`);
      console.log(`   Failures during downtime: ${failureCount}`);
      console.log(`   Recovery time: ${recoveryTime}ms`);
      console.log(`   Recovery successful: ${recoverySuccessful ? '✅' : '❌'}`);
    });
  });

  describe('5. Performance Regression Detection', () => {
    test('Baseline performance establishment', async () => {
      const baselineIterations = 100;
      const baselineLatencies = [];

      // Establish performance baseline
      for (let i = 0; i < baselineIterations; i++) {
        const marketData = {
          symbol: 'EURUSD',
          bid: 1.0850,
          ask: 1.0852,
          timestamp: new Date().toISOString()
        };

        const start = process.hrtime.bigint();
        await decisionEngine.makeDecision(marketData, 'baseline-test');
        const end = process.hrtime.bigint();

        const latency = Number(end - start) / 1000000;
        baselineLatencies.push(latency);
      }

      const baselineAvg = baselineLatencies.reduce((a, b) => a + b, 0) / baselineLatencies.length;
      const baselineP95 = baselineLatencies.sort((a, b) => a - b)[Math.floor(baselineIterations * 0.95)];

      // Store baseline for comparison in CI/CD
      const baseline = {
        averageLatency: baselineAvg,
        p95Latency: baselineP95,
        timestamp: new Date().toISOString(),
        iterations: baselineIterations
      };

      // Validate against targets
      expect(baseline.averageLatency).toBeLessThan(performanceTargets.maxLatencyMs);
      expect(baseline.p95Latency).toBeLessThan(performanceTargets.maxLatencyMs * 1.5);

      console.log(`📏 Performance Baseline Established:`);
      console.log(`   Average latency: ${baseline.averageLatency.toFixed(2)}ms`);
      console.log(`   P95 latency: ${baseline.p95Latency.toFixed(2)}ms`);
      console.log(`   Iterations: ${baseline.iterations}`);

      // In a real environment, you would save this baseline to a file or database
      // for comparison in future test runs
    });
  });
});