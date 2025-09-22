import { test, expect } from '@playwright/test';
import { AuthenticationHelper } from '../../utils/authentication-helper';
import { TestDataManager } from '../../utils/test-data-manager';
import { TradingHelper } from '../../utils/trading-helper';
import { APIHelper } from '../../utils/api-helper';

test.describe('Performance and Load Testing', () => {
  let authHelper: AuthenticationHelper;
  let testDataManager: TestDataManager;
  let tradingHelper: TradingHelper;
  let apiHelper: APIHelper;

  test.beforeEach(async ({ page }) => {
    authHelper = new AuthenticationHelper();
    testDataManager = new TestDataManager();
    tradingHelper = new TradingHelper();
    apiHelper = new APIHelper();

    await authHelper.loginAs(page, 'premium_trader');
  });

  test.describe('@performance @load Page Load Performance', () => {
    test('should load dashboard within performance budget', async ({ page }) => {
      const performanceBudget = {
        maxLoadTime: 3000,      // 3 seconds
        maxDOMContentLoaded: 2000, // 2 seconds
        maxFirstPaint: 1500,    // 1.5 seconds
        maxFirstContentfulPaint: 2000 // 2 seconds
      };

      // Start performance measurement
      const startTime = Date.now();

      await page.goto('/dashboard');

      // Wait for the page to be fully loaded
      await page.waitForLoadState('networkidle');

      const loadTime = Date.now() - startTime;

      // Check basic load time
      expect(loadTime).toBeLessThan(performanceBudget.maxLoadTime);

      // Get detailed performance metrics
      const metrics = await page.evaluate(() => {
        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        const paintEntries = performance.getEntriesByType('paint');

        return {
          domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
          loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
          firstPaint: paintEntries.find(entry => entry.name === 'first-paint')?.startTime || 0,
          firstContentfulPaint: paintEntries.find(entry => entry.name === 'first-contentful-paint')?.startTime || 0,
          totalSize: navigation.transferSize,
          resourceCount: performance.getEntriesByType('resource').length
        };
      });

      // Validate performance metrics
      expect(metrics.domContentLoaded).toBeLessThan(performanceBudget.maxDOMContentLoaded);
      expect(metrics.firstPaint).toBeLessThan(performanceBudget.maxFirstPaint);
      expect(metrics.firstContentfulPaint).toBeLessThan(performanceBudget.maxFirstContentfulPaint);

      // Resource optimization checks
      expect(metrics.resourceCount).toBeLessThan(50); // Reasonable resource count
      expect(metrics.totalSize).toBeLessThan(2 * 1024 * 1024); // Less than 2MB

      console.log('Performance Metrics:', metrics);
    });

    test('should handle multiple concurrent page loads', async ({ browser }) => {
      const concurrentUsers = 10;
      const contexts = await Promise.all(
        Array(concurrentUsers).fill(null).map(() => browser.newContext())
      );

      const pages = await Promise.all(
        contexts.map(context => context.newPage())
      );

      // Login all users concurrently
      await Promise.all(
        pages.map(page => authHelper.loginAs(page, 'trader'))
      );

      // Measure concurrent page loads
      const startTime = Date.now();

      const loadPromises = pages.map(async (page, index) => {
        const pageStartTime = Date.now();
        await page.goto('/dashboard');
        await page.waitForLoadState('networkidle');
        return Date.now() - pageStartTime;
      });

      const loadTimes = await Promise.all(loadPromises);
      const totalTime = Date.now() - startTime;

      // All pages should load within reasonable time
      loadTimes.forEach((loadTime, index) => {
        expect(loadTime).toBeLessThan(5000); // 5 seconds per page
      });

      // Total time should be reasonable for concurrent loads
      expect(totalTime).toBeLessThan(15000); // 15 seconds total

      const avgLoadTime = loadTimes.reduce((sum, time) => sum + time, 0) / loadTimes.length;
      console.log(`Average load time for ${concurrentUsers} concurrent users: ${avgLoadTime}ms`);

      // Cleanup
      await Promise.all(contexts.map(context => context.close()));
    });

    test('should maintain performance under memory pressure', async ({ page }) => {
      // Navigate through multiple pages to build up memory usage
      const pages = [
        '/dashboard',
        '/market-data',
        '/trading',
        '/portfolio',
        '/analytics',
        '/reports',
        '/strategies'
      ];

      const performanceData = [];

      for (const pageUrl of pages) {
        const startTime = Date.now();

        await page.goto(pageUrl);
        await page.waitForLoadState('networkidle');

        const loadTime = Date.now() - startTime;

        // Get memory usage
        const memoryUsage = await page.evaluate(() => {
          if ('memory' in performance) {
            return {
              usedJSHeapSize: (performance as any).memory.usedJSHeapSize,
              totalJSHeapSize: (performance as any).memory.totalJSHeapSize,
              jsHeapSizeLimit: (performance as any).memory.jsHeapSizeLimit
            };
          }
          return null;
        });

        performanceData.push({
          page: pageUrl,
          loadTime,
          memoryUsage
        });

        // Performance should not degrade significantly
        expect(loadTime).toBeLessThan(4000);
      }

      // Memory usage should not grow excessively
      if (performanceData[0].memoryUsage && performanceData[performanceData.length - 1].memoryUsage) {
        const initialMemory = performanceData[0].memoryUsage.usedJSHeapSize;
        const finalMemory = performanceData[performanceData.length - 1].memoryUsage.usedJSHeapSize;
        const memoryGrowth = finalMemory - initialMemory;

        // Memory growth should be reasonable (less than 50MB)
        expect(memoryGrowth).toBeLessThan(50 * 1024 * 1024);
      }

      console.log('Performance Data:', performanceData);
    });
  });

  test.describe('@performance @api API Performance', () => {
    test('should handle high-frequency API requests', async ({ page }) => {
      await apiHelper.authenticate('premium_trader');

      const requestCount = 100;
      const maxConcurrency = 10;
      const expectedAvgResponseTime = 500; // 500ms

      const results = [];
      const batches = [];

      // Create batches for controlled concurrency
      for (let i = 0; i < requestCount; i += maxConcurrency) {
        const batch = [];
        for (let j = 0; j < maxConcurrency && (i + j) < requestCount; j++) {
          batch.push(async () => {
            const startTime = Date.now();

            try {
              await apiHelper.getMarketData();
              const responseTime = Date.now() - startTime;
              return { success: true, responseTime };
            } catch (error) {
              const responseTime = Date.now() - startTime;
              return { success: false, responseTime, error: error.message };
            }
          });
        }
        batches.push(batch);
      }

      // Execute batches sequentially, requests within batch concurrently
      for (const batch of batches) {
        const batchResults = await Promise.all(batch.map(fn => fn()));
        results.push(...batchResults);
      }

      // Analyze results
      const successfulRequests = results.filter(r => r.success);
      const failedRequests = results.filter(r => !r.success);

      const avgResponseTime = successfulRequests.reduce((sum, r) => sum + r.responseTime, 0) / successfulRequests.length;
      const maxResponseTime = Math.max(...successfulRequests.map(r => r.responseTime));
      const minResponseTime = Math.min(...successfulRequests.map(r => r.responseTime));

      // Performance assertions
      expect(successfulRequests.length).toBeGreaterThan(requestCount * 0.95); // 95% success rate
      expect(avgResponseTime).toBeLessThan(expectedAvgResponseTime);
      expect(maxResponseTime).toBeLessThan(expectedAvgResponseTime * 3); // Max 3x average

      console.log('API Performance Results:', {
        totalRequests: requestCount,
        successful: successfulRequests.length,
        failed: failedRequests.length,
        avgResponseTime,
        minResponseTime,
        maxResponseTime,
        successRate: (successfulRequests.length / requestCount) * 100
      });
    });

    test('should handle bulk trading operations efficiently', async ({ page }) => {
      await apiHelper.authenticate('premium_trader');

      const bulkOperations = [
        // Multiple order placements
        ...Array(20).fill(null).map((_, i) => ({
          type: 'order',
          action: () => apiHelper.placeOrder({
            symbol: ['EURUSD', 'GBPUSD', 'USDJPY'][i % 3],
            side: i % 2 === 0 ? 'buy' : 'sell',
            type: 'market',
            quantity: 1000 + (i * 100)
          })
        })),

        // Portfolio queries
        ...Array(10).fill(null).map(() => ({
          type: 'portfolio',
          action: () => apiHelper.getPortfolio()
        })),

        // Market data requests
        ...Array(15).fill(null).map(() => ({
          type: 'market_data',
          action: () => apiHelper.getMarketData()
        }))
      ];

      const startTime = Date.now();
      const results = [];

      // Execute operations in smaller batches to avoid overwhelming the server
      const batchSize = 5;
      for (let i = 0; i < bulkOperations.length; i += batchSize) {
        const batch = bulkOperations.slice(i, i + batchSize);

        const batchPromises = batch.map(async (op, index) => {
          const opStartTime = Date.now();

          try {
            const result = await op.action();
            return {
              type: op.type,
              index: i + index,
              success: true,
              responseTime: Date.now() - opStartTime,
              status: result.status
            };
          } catch (error) {
            return {
              type: op.type,
              index: i + index,
              success: false,
              responseTime: Date.now() - opStartTime,
              error: error.message
            };
          }
        });

        const batchResults = await Promise.all(batchPromises);
        results.push(...batchResults);

        // Small delay between batches to be courteous to the server
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      const totalTime = Date.now() - startTime;

      // Analyze performance by operation type
      const performanceByType = {};
      results.forEach(result => {
        if (!performanceByType[result.type]) {
          performanceByType[result.type] = {
            successful: 0,
            failed: 0,
            totalResponseTime: 0,
            maxResponseTime: 0,
            minResponseTime: Infinity
          };
        }

        const typeStats = performanceByType[result.type];

        if (result.success) {
          typeStats.successful++;
          typeStats.totalResponseTime += result.responseTime;
          typeStats.maxResponseTime = Math.max(typeStats.maxResponseTime, result.responseTime);
          typeStats.minResponseTime = Math.min(typeStats.minResponseTime, result.responseTime);
        } else {
          typeStats.failed++;
        }
      });

      // Calculate averages
      Object.keys(performanceByType).forEach(type => {
        const stats = performanceByType[type];
        stats.avgResponseTime = stats.totalResponseTime / stats.successful;
        stats.successRate = (stats.successful / (stats.successful + stats.failed)) * 100;
      });

      // Performance assertions
      expect(totalTime).toBeLessThan(30000); // Complete within 30 seconds

      Object.entries(performanceByType).forEach(([type, stats]: [string, any]) => {
        expect(stats.successRate).toBeGreaterThan(90); // 90% success rate per type
        expect(stats.avgResponseTime).toBeLessThan(2000); // Average under 2 seconds
      });

      console.log('Bulk Operations Performance:', {
        totalOperations: bulkOperations.length,
        totalTime,
        performanceByType
      });
    });

    test('should maintain responsiveness under database load', async ({ page }) => {
      await apiHelper.authenticate('premium_trader');

      // Simulate heavy database operations
      const heavyOperations = [
        // Generate large reports
        () => apiHelper.generateReport({
          type: 'comprehensive',
          dateFrom: '2024-01-01',
          dateTo: new Date().toISOString().split('T')[0],
          format: 'excel'
        }),

        // Complex analytics queries
        () => apiHelper.getAnalytics({
          timeframe: '6months',
          includeDetailedBreakdown: true
        }),

        // Historical data retrieval
        () => apiHelper.getPortfolioHistory({
          period: '1year',
          granularity: 'daily'
        })
      ];

      // Concurrent light operations that should remain responsive
      const lightOperations = [
        () => apiHelper.getUserProfile(),
        () => apiHelper.getMarketData('EURUSD'),
        () => apiHelper.getOrders({ limit: 10 })
      ];

      const results = {
        heavy: [],
        light: []
      };

      // Start heavy operations
      const heavyPromises = heavyOperations.map(async (op, index) => {
        const startTime = Date.now();

        try {
          await op();
          return {
            operation: `heavy_${index}`,
            success: true,
            responseTime: Date.now() - startTime
          };
        } catch (error) {
          return {
            operation: `heavy_${index}`,
            success: false,
            responseTime: Date.now() - startTime,
            error: error.message
          };
        }
      });

      // Run light operations every 2 seconds while heavy operations are running
      const lightOperationInterval = setInterval(async () => {
        const lightPromises = lightOperations.map(async (op, index) => {
          const startTime = Date.now();

          try {
            await op();
            return {
              operation: `light_${index}`,
              success: true,
              responseTime: Date.now() - startTime
            };
          } catch (error) {
            return {
              operation: `light_${index}`,
              success: false,
              responseTime: Date.now() - startTime,
              error: error.message
            };
          }
        });

        const lightResults = await Promise.all(lightPromises);
        results.light.push(...lightResults);
      }, 2000);

      // Wait for heavy operations to complete
      results.heavy = await Promise.all(heavyPromises);

      // Stop light operations
      clearInterval(lightOperationInterval);

      // Analyze responsiveness
      const lightResponseTimes = results.light
        .filter(r => r.success)
        .map(r => r.responseTime);

      const avgLightResponseTime = lightResponseTimes.reduce((sum, time) => sum + time, 0) / lightResponseTimes.length;
      const maxLightResponseTime = Math.max(...lightResponseTimes);

      // Light operations should remain responsive even under heavy load
      expect(avgLightResponseTime).toBeLessThan(1000); // Average under 1 second
      expect(maxLightResponseTime).toBeLessThan(3000); // Max under 3 seconds

      console.log('Database Load Test Results:', {
        heavyOperations: results.heavy.length,
        lightOperations: results.light.length,
        avgLightResponseTime,
        maxLightResponseTime,
        heavyOperationsCompleted: results.heavy.filter(r => r.success).length
      });
    });
  });

  test.describe('@performance @stress Stress Testing', () => {
    test('should handle trading system stress', async ({ browser }) => {
      const concurrentTraders = 5;
      const ordersPerTrader = 10;
      const maxExecutionTime = 60000; // 60 seconds

      const contexts = await Promise.all(
        Array(concurrentTraders).fill(null).map(() => browser.newContext())
      );

      const pages = await Promise.all(
        contexts.map(context => context.newPage())
      );

      // Login all traders
      await Promise.all(
        pages.map(page => authHelper.loginAs(page, 'trader'))
      );

      const startTime = Date.now();
      const allResults = [];

      // Each trader places multiple orders concurrently
      const traderPromises = pages.map(async (page, traderIndex) => {
        const traderResults = [];

        for (let orderIndex = 0; orderIndex < ordersPerTrader; orderIndex++) {
          const orderStartTime = Date.now();

          try {
            const orderId = await tradingHelper.placeMarketOrder(page, {
              symbol: ['EURUSD', 'GBPUSD', 'USDJPY'][orderIndex % 3],
              side: orderIndex % 2 === 0 ? 'buy' : 'sell',
              quantity: 1000
            });

            traderResults.push({
              trader: traderIndex,
              order: orderIndex,
              orderId,
              success: true,
              executionTime: Date.now() - orderStartTime
            });

          } catch (error) {
            traderResults.push({
              trader: traderIndex,
              order: orderIndex,
              success: false,
              error: error.message,
              executionTime: Date.now() - orderStartTime
            });
          }

          // Small delay between orders from same trader
          await page.waitForTimeout(500);
        }

        return traderResults;
      });

      const allTraderResults = await Promise.all(traderPromises);
      allResults.push(...allTraderResults.flat());

      const totalTime = Date.now() - startTime;

      // Analyze stress test results
      const successfulOrders = allResults.filter(r => r.success);
      const failedOrders = allResults.filter(r => !r.success);

      const avgExecutionTime = successfulOrders.reduce((sum, r) => sum + r.executionTime, 0) / successfulOrders.length;
      const maxExecutionTime = Math.max(...successfulOrders.map(r => r.executionTime));

      // Stress test assertions
      expect(totalTime).toBeLessThan(maxExecutionTime);
      expect(successfulOrders.length).toBeGreaterThan((concurrentTraders * ordersPerTrader) * 0.8); // 80% success rate
      expect(avgExecutionTime).toBeLessThan(10000); // Average under 10 seconds
      expect(maxExecutionTime).toBeLessThan(30000); // Max under 30 seconds

      console.log('Trading System Stress Test:', {
        concurrentTraders,
        ordersPerTrader,
        totalOrders: concurrentTraders * ordersPerTrader,
        successfulOrders: successfulOrders.length,
        failedOrders: failedOrders.length,
        successRate: (successfulOrders.length / (concurrentTraders * ordersPerTrader)) * 100,
        avgExecutionTime,
        maxExecutionTime,
        totalTime
      });

      // Cleanup
      await Promise.all(contexts.map(context => context.close()));
    });

    test('should recover from memory exhaustion', async ({ page }) => {
      // Create memory pressure by loading large datasets
      const memoryIntensiveOperations = [
        () => page.goto('/analytics?loadAll=true'),
        () => page.goto('/market-data?symbols=all&history=1year'),
        () => page.goto('/reports?type=comprehensive&period=all'),
        () => page.goto('/portfolio?includeHistory=true&period=max')
      ];

      let memoryPressureDetected = false;

      for (const operation of memoryIntensiveOperations) {
        try {
          const startTime = Date.now();

          await operation();
          await page.waitForLoadState('networkidle', { timeout: 30000 });

          const loadTime = Date.now() - startTime;

          // Check for memory pressure indicators
          const performanceData = await page.evaluate(() => {
            if ('memory' in performance) {
              const memory = (performance as any).memory;
              return {
                usedJSHeapSize: memory.usedJSHeapSize,
                totalJSHeapSize: memory.totalJSHeapSize,
                jsHeapSizeLimit: memory.jsHeapSizeLimit,
                memoryPressure: memory.usedJSHeapSize / memory.jsHeapSizeLimit > 0.8
              };
            }
            return null;
          });

          if (performanceData?.memoryPressure) {
            memoryPressureDetected = true;
            console.log('Memory pressure detected:', performanceData);

            // Force garbage collection and verify recovery
            await page.evaluate(() => {
              if ('gc' in window) {
                (window as any).gc();
              }
            });

            // Verify the page is still responsive
            await page.click('[data-testid="user-menu"]');
            await expect(page.locator('[data-testid="user-dropdown"]')).toBeVisible();
          }

          // Performance should degrade gracefully under memory pressure
          if (memoryPressureDetected) {
            expect(loadTime).toBeLessThan(15000); // Allow longer load times under pressure
          } else {
            expect(loadTime).toBeLessThan(8000); // Normal load times
          }

        } catch (error) {
          // Page should not crash completely
          console.warn('Memory intensive operation failed:', error.message);

          // Verify page is still accessible
          await page.goto('/dashboard');
          await expect(page.locator('[data-testid="dashboard-content"]')).toBeVisible();
        }
      }

      // System should recover and be responsive
      await page.goto('/dashboard');
      await expect(page.locator('[data-testid="user-menu"]')).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('@performance @monitoring Real-time Performance Monitoring', () => {
    test('should monitor WebSocket performance', async ({ page }) => {
      await page.goto('/market-data');

      // Monitor WebSocket connections and message frequency
      const wsMetrics = await page.evaluate(() => {
        return new Promise((resolve) => {
          const metrics = {
            connectTime: 0,
            messageCount: 0,
            avgLatency: 0,
            maxLatency: 0,
            errors: 0
          };

          const startTime = Date.now();
          const latencies = [];

          // Mock WebSocket monitoring
          const originalWebSocket = window.WebSocket;
          window.WebSocket = function(url, protocols) {
            const ws = new originalWebSocket(url, protocols);

            ws.addEventListener('open', () => {
              metrics.connectTime = Date.now() - startTime;
            });

            ws.addEventListener('message', (event) => {
              const messageTime = Date.now();
              try {
                const data = JSON.parse(event.data);
                if (data.timestamp) {
                  const latency = messageTime - new Date(data.timestamp).getTime();
                  latencies.push(latency);
                  metrics.messageCount++;
                }
              } catch (e) {
                // Ignore parsing errors
              }
            });

            ws.addEventListener('error', () => {
              metrics.errors++;
            });

            return ws;
          };

          // Monitor for 10 seconds
          setTimeout(() => {
            if (latencies.length > 0) {
              metrics.avgLatency = latencies.reduce((sum, lat) => sum + lat, 0) / latencies.length;
              metrics.maxLatency = Math.max(...latencies);
            }
            resolve(metrics);
          }, 10000);
        });
      });

      // WebSocket performance assertions
      expect(wsMetrics.connectTime).toBeLessThan(5000); // Connect within 5 seconds
      expect(wsMetrics.messageCount).toBeGreaterThan(5); // At least 5 messages in 10 seconds
      expect(wsMetrics.avgLatency).toBeLessThan(500); // Average latency under 500ms
      expect(wsMetrics.maxLatency).toBeLessThan(2000); // Max latency under 2 seconds
      expect(wsMetrics.errors).toBe(0); // No connection errors

      console.log('WebSocket Performance Metrics:', wsMetrics);
    });

    test('should track user interaction responsiveness', async ({ page }) => {
      await page.goto('/trading');

      const interactionMetrics = [];

      // Test various user interactions
      const interactions = [
        {
          name: 'Navigation Click',
          action: () => page.click('[data-testid="portfolio-nav"]')
        },
        {
          name: 'Form Input',
          action: () => page.fill('[data-testid="search-input"]', 'EURUSD')
        },
        {
          name: 'Dropdown Open',
          action: () => page.click('[data-testid="timeframe-select"]')
        },
        {
          name: 'Modal Open',
          action: () => page.click('[data-testid="new-order-button"]')
        },
        {
          name: 'Chart Interaction',
          action: () => page.click('[data-testid="chart-container"]')
        }
      ];

      for (const interaction of interactions) {
        const startTime = Date.now();

        try {
          await interaction.action();

          // Wait for visual response
          await page.waitForTimeout(100);

          const responseTime = Date.now() - startTime;

          interactionMetrics.push({
            name: interaction.name,
            responseTime,
            success: true
          });

          // Interactions should feel responsive
          expect(responseTime).toBeLessThan(200); // Under 200ms for good UX

        } catch (error) {
          interactionMetrics.push({
            name: interaction.name,
            responseTime: Date.now() - startTime,
            success: false,
            error: error.message
          });
        }

        // Small delay between interactions
        await page.waitForTimeout(500);
      }

      const avgResponseTime = interactionMetrics
        .filter(m => m.success)
        .reduce((sum, m) => sum + m.responseTime, 0) / interactionMetrics.filter(m => m.success).length;

      expect(avgResponseTime).toBeLessThan(150); // Average under 150ms

      console.log('User Interaction Metrics:', {
        interactions: interactionMetrics.length,
        successful: interactionMetrics.filter(m => m.success).length,
        avgResponseTime,
        details: interactionMetrics
      });
    });
  });
});