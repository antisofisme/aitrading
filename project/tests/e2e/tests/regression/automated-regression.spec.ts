import { test, expect } from '@playwright/test';
import { AuthenticationHelper } from '../../utils/authentication-helper';
import { TestDataManager } from '../../utils/test-data-manager';
import { TradingHelper } from '../../utils/trading-helper';
import { APIHelper } from '../../utils/api-helper';
import { RegressionHelper } from '../../utils/regression-helper';

test.describe('Automated Regression Tests', () => {
  let authHelper: AuthenticationHelper;
  let testDataManager: TestDataManager;
  let tradingHelper: TradingHelper;
  let apiHelper: APIHelper;
  let regressionHelper: RegressionHelper;

  test.beforeEach(async ({ page }) => {
    authHelper = new AuthenticationHelper();
    testDataManager = new TestDataManager();
    tradingHelper = new TradingHelper();
    apiHelper = new APIHelper();
    regressionHelper = new RegressionHelper();

    await authHelper.loginAs(page, 'premium_trader');
  });

  test.describe('@regression @critical Core Functionality Regression', () => {
    test('should maintain user authentication functionality', async ({ page }) => {
      const testData = regressionHelper.getBaselineData('authentication');

      // Test all authentication scenarios
      const authScenarios = [
        { role: 'trader', expectedFeatures: ['trading', 'portfolio'] },
        { role: 'premium_trader', expectedFeatures: ['trading', 'portfolio', 'analytics', 'advanced_strategies'] },
        { role: 'admin', expectedFeatures: ['trading', 'portfolio', 'analytics', 'user_management', 'system_settings'] }
      ];

      for (const scenario of authScenarios) {
        await authHelper.logout(page);
        await authHelper.loginAs(page, scenario.role);

        // Verify dashboard loads
        await expect(page).toHaveURL(/.*\/dashboard.*/);
        await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();

        // Verify role-specific features
        for (const feature of scenario.expectedFeatures) {
          await expect(page.locator(`[data-testid="${feature}-nav"]`)).toBeVisible();
        }

        // Verify user profile displays correct role
        const userRole = await authHelper.getCurrentUserRole(page);
        expect(userRole).toBe(scenario.role);
      }

      // Compare with baseline
      await regressionHelper.compareWithBaseline('authentication', {
        authScenariosCount: authScenarios.length,
        allScenariosPass: true
      });
    });

    test('should maintain trading engine functionality', async ({ page }) => {
      const baseline = regressionHelper.getBaselineData('trading_engine');

      // Test core trading operations
      const tradingTests = [
        {
          name: 'Market Order Execution',
          action: () => tradingHelper.placeMarketOrder(page, {
            symbol: 'EURUSD',
            side: 'buy',
            quantity: 10000
          })
        },
        {
          name: 'Limit Order Placement',
          action: () => tradingHelper.placeLimitOrder(page, {
            symbol: 'GBPUSD',
            side: 'sell',
            quantity: 5000,
            price: 1.2500
          })
        },
        {
          name: 'Position Management',
          action: async () => {
            const orderId = await tradingHelper.placeMarketOrder(page, {
              symbol: 'USDJPY',
              side: 'buy',
              quantity: 8000
            });
            await tradingHelper.waitForOrderExecution(page, orderId);
            return await tradingHelper.getPositionDetails(page, 'USDJPY');
          }
        }
      ];

      const results = [];

      for (const test of tradingTests) {
        const startTime = Date.now();

        try {
          const result = await test.action();
          const duration = Date.now() - startTime;

          results.push({
            name: test.name,
            success: true,
            duration,
            result
          });

          // Verify performance hasn't degraded
          if (baseline?.performance?.[test.name]) {
            const baselineDuration = baseline.performance[test.name];
            const performanceDegradation = (duration - baselineDuration) / baselineDuration;

            expect(performanceDegradation).toBeLessThan(0.2); // No more than 20% slower
          }

        } catch (error) {
          results.push({
            name: test.name,
            success: false,
            error: error.message
          });
        }
      }

      // All trading operations should succeed
      const failedTests = results.filter(r => !r.success);
      expect(failedTests).toHaveLength(0);

      // Update baseline
      await regressionHelper.updateBaseline('trading_engine', {
        testResults: results,
        timestamp: new Date().toISOString()
      });
    });

    test('should maintain market data functionality', async ({ page }) => {
      const baseline = regressionHelper.getBaselineData('market_data');

      await page.goto('/market-data');

      // Test market data display and updates
      const symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD'];
      const dataPoints = ['price', 'spread', 'volume', 'timestamp'];

      for (const symbol of symbols) {
        // Verify data display
        for (const dataPoint of dataPoints) {
          await expect(page.locator(`[data-testid="${dataPoint}-${symbol}"]`)).toBeVisible();
        }

        // Verify data is current
        const timestamp = await page.locator(`[data-testid="timestamp-${symbol}"]`).textContent();
        const timestampDate = new Date(timestamp!);
        const age = Date.now() - timestampDate.getTime();

        expect(age).toBeLessThan(300000); // Less than 5 minutes old
      }

      // Test real-time updates
      const initialPrice = await page.locator('[data-testid="price-EURUSD"]').textContent();

      await page.waitForFunction(
        (selector, initial) => {
          const element = document.querySelector(selector);
          return element && element.textContent !== initial;
        },
        '[data-testid="price-EURUSD"]',
        initialPrice,
        { timeout: 30000 }
      );

      // Compare update frequency with baseline
      const updateCount = await regressionHelper.measureUpdateFrequency(page, 'EURUSD', 60000);

      if (baseline?.updateFrequency?.EURUSD) {
        const baselineFrequency = baseline.updateFrequency.EURUSD;
        const frequencyRatio = updateCount / baselineFrequency;

        expect(frequencyRatio).toBeGreaterThan(0.8); // At least 80% of baseline frequency
      }

      await regressionHelper.updateBaseline('market_data', {
        updateFrequency: { EURUSD: updateCount },
        timestamp: new Date().toISOString()
      });
    });

    test('should maintain portfolio management functionality', async ({ page }) => {
      const baseline = regressionHelper.getBaselineData('portfolio');

      // Test portfolio operations
      const initialPortfolio = await tradingHelper.getPortfolioSummary(page);

      // Execute trades to test portfolio updates
      await tradingHelper.placeMarketOrder(page, {
        symbol: 'EURUSD',
        side: 'buy',
        quantity: 10000
      });

      await page.waitForTimeout(3000); // Allow for portfolio update

      const updatedPortfolio = await tradingHelper.getPortfolioSummary(page);

      // Verify portfolio calculations
      expect(updatedPortfolio.marginUsed).toBeGreaterThan(initialPortfolio.marginUsed);
      expect(updatedPortfolio.marginAvailable).toBeLessThan(initialPortfolio.marginAvailable);
      expect(updatedPortfolio.equity).toBeCloseTo(initialPortfolio.equity, 0); // Within $1

      // Test portfolio metrics calculations
      await page.goto('/analytics');
      await expect(page.locator('[data-testid="portfolio-metrics"]')).toBeVisible();

      const metrics = {
        totalReturn: await page.locator('[data-testid="total-return"]').textContent(),
        sharpeRatio: await page.locator('[data-testid="sharpe-ratio"]').textContent(),
        maxDrawdown: await page.locator('[data-testid="max-drawdown"]').textContent(),
        winRate: await page.locator('[data-testid="win-rate"]').textContent()
      };

      // Verify metrics are calculated and displayed
      Object.values(metrics).forEach(metric => {
        expect(metric).toMatch(/^-?\d+\.?\d*%?$/); // Should be a number or percentage
      });

      // Compare with baseline metrics
      if (baseline?.metrics) {
        const currentMetrics = {
          totalReturn: parseFloat(metrics.totalReturn!.replace('%', '')),
          sharpeRatio: parseFloat(metrics.sharpeRatio!),
          maxDrawdown: parseFloat(metrics.maxDrawdown!.replace('%', '')),
          winRate: parseFloat(metrics.winRate!.replace('%', ''))
        };

        // Metrics should be within reasonable ranges
        Object.entries(currentMetrics).forEach(([key, value]) => {
          if (baseline.metrics[key] !== undefined) {
            const baselineValue = baseline.metrics[key];
            const difference = Math.abs(value - baselineValue);

            // Allow for normal market variation
            expect(difference).toBeLessThan(Math.abs(baselineValue) * 0.5);
          }
        });
      }
    });
  });

  test.describe('@regression @api API Compatibility Regression', () => {
    test('should maintain API endpoint compatibility', async ({ page }) => {
      await apiHelper.authenticate('premium_trader');

      const endpoints = [
        { method: 'GET', path: '/users/me', description: 'User profile' },
        { method: 'GET', path: '/market-data', description: 'Market data' },
        { method: 'GET', path: '/orders', description: 'Order history' },
        { method: 'GET', path: '/positions', description: 'Current positions' },
        { method: 'GET', path: '/portfolio', description: 'Portfolio summary' },
        { method: 'GET', path: '/strategies', description: 'Trading strategies' },
        { method: 'GET', path: '/analytics', description: 'Analytics data' }
      ];

      const apiResults = [];

      for (const endpoint of endpoints) {
        try {
          const response = await apiHelper.api.request({
            method: endpoint.method,
            url: endpoint.path
          });

          apiResults.push({
            endpoint: `${endpoint.method} ${endpoint.path}`,
            status: response.status,
            description: endpoint.description,
            success: response.status >= 200 && response.status < 300,
            responseTime: response.headers['x-response-time'] || 'N/A'
          });

          // Verify response structure hasn't changed
          if (endpoint.path === '/users/me') {
            expect(response.data).toHaveProperty('id');
            expect(response.data).toHaveProperty('email');
            expect(response.data).toHaveProperty('role');
          }

          if (endpoint.path === '/portfolio') {
            expect(response.data).toHaveProperty('balance');
            expect(response.data).toHaveProperty('equity');
            expect(response.data).toHaveProperty('marginUsed');
          }

        } catch (error) {
          apiResults.push({
            endpoint: `${endpoint.method} ${endpoint.path}`,
            status: error.response?.status || 0,
            description: endpoint.description,
            success: false,
            error: error.message
          });
        }
      }

      // All endpoints should be accessible
      const failedEndpoints = apiResults.filter(r => !r.success);
      expect(failedEndpoints).toHaveLength(0);

      await regressionHelper.updateBaseline('api_compatibility', {
        endpoints: apiResults,
        timestamp: new Date().toISOString()
      });
    });

    test('should maintain API response schemas', async ({ page }) => {
      await apiHelper.authenticate('premium_trader');

      // Test critical API response schemas
      const schemaTests = [
        {
          endpoint: '/market-data/EURUSD',
          expectedSchema: {
            symbol: 'string',
            price: 'number',
            bid: 'number',
            ask: 'number',
            spread: 'number',
            volume: 'number',
            timestamp: 'string'
          }
        },
        {
          endpoint: '/orders',
          expectedSchema: {
            data: 'array',
            total: 'number',
            page: 'number',
            limit: 'number'
          }
        },
        {
          endpoint: '/portfolio',
          expectedSchema: {
            balance: 'number',
            equity: 'number',
            marginUsed: 'number',
            marginAvailable: 'number',
            totalPnL: 'number'
          }
        }
      ];

      for (const schemaTest of schemaTests) {
        const response = await apiHelper.api.get(schemaTest.endpoint);

        expect(response.status).toBe(200);

        // Validate schema
        const data = response.data;

        Object.entries(schemaTest.expectedSchema).forEach(([field, expectedType]) => {
          if (expectedType === 'array') {
            expect(Array.isArray(data[field])).toBe(true);
          } else {
            expect(typeof data[field]).toBe(expectedType);
          }
        });
      }
    });
  });

  test.describe('@regression @performance Performance Regression', () => {
    test('should maintain page load performance', async ({ page }) => {
      const baseline = regressionHelper.getBaselineData('performance');

      const pages = [
        { url: '/dashboard', name: 'Dashboard' },
        { url: '/market-data', name: 'Market Data' },
        { url: '/trading', name: 'Trading' },
        { url: '/portfolio', name: 'Portfolio' },
        { url: '/analytics', name: 'Analytics' }
      ];

      const performanceResults = [];

      for (const pageTest of pages) {
        const startTime = Date.now();

        await page.goto(pageTest.url);
        await page.waitForLoadState('networkidle');

        const loadTime = Date.now() - startTime;

        // Measure key performance metrics
        const metrics = await page.evaluate(() => {
          const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;

          return {
            domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
            loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
            firstPaint: performance.getEntriesByType('paint').find(entry => entry.name === 'first-paint')?.startTime || 0,
            firstContentfulPaint: performance.getEntriesByType('paint').find(entry => entry.name === 'first-contentful-paint')?.startTime || 0
          };
        });

        performanceResults.push({
          page: pageTest.name,
          url: pageTest.url,
          totalLoadTime: loadTime,
          metrics
        });

        // Compare with baseline performance
        if (baseline?.pages?.[pageTest.name]) {
          const baselineLoadTime = baseline.pages[pageTest.name].totalLoadTime;
          const performanceDegradation = (loadTime - baselineLoadTime) / baselineLoadTime;

          expect(performanceDegradation).toBeLessThan(0.3); // No more than 30% slower
        }

        // Verify page loads within acceptable time
        expect(loadTime).toBeLessThan(10000); // Less than 10 seconds
      }

      await regressionHelper.updateBaseline('performance', {
        pages: performanceResults.reduce((acc, result) => {
          acc[result.page] = result;
          return acc;
        }, {} as any),
        timestamp: new Date().toISOString()
      });
    });

    test('should maintain API response times', async ({ page }) => {
      await apiHelper.authenticate('premium_trader');

      const apiEndpoints = [
        '/users/me',
        '/market-data',
        '/orders',
        '/positions',
        '/portfolio'
      ];

      const responseTimeResults = [];

      for (const endpoint of apiEndpoints) {
        const measurements = [];

        // Take multiple measurements for accuracy
        for (let i = 0; i < 5; i++) {
          const startTime = Date.now();

          await apiHelper.api.get(endpoint);

          const responseTime = Date.now() - startTime;
          measurements.push(responseTime);

          await new Promise(resolve => setTimeout(resolve, 100)); // Small delay between requests
        }

        const avgResponseTime = measurements.reduce((sum, time) => sum + time, 0) / measurements.length;

        responseTimeResults.push({
          endpoint,
          avgResponseTime,
          measurements
        });

        // Verify response time is acceptable
        expect(avgResponseTime).toBeLessThan(5000); // Less than 5 seconds
      }

      await regressionHelper.updateBaseline('api_performance', {
        endpoints: responseTimeResults,
        timestamp: new Date().toISOString()
      });
    });
  });

  test.describe('@regression @ui UI/UX Regression', () => {
    test('should maintain visual consistency', async ({ page }) => {
      const pages = [
        '/dashboard',
        '/market-data',
        '/trading',
        '/portfolio'
      ];

      for (const pageUrl of pages) {
        await page.goto(pageUrl);
        await page.waitForLoadState('networkidle');

        // Take screenshot for visual regression
        const screenshot = await page.screenshot({
          fullPage: true,
          animations: 'disabled'
        });

        // Compare with baseline screenshot
        await regressionHelper.compareScreenshot(pageUrl, screenshot);

        // Verify key UI elements are present
        await expect(page.locator('[data-testid="navigation"]')).toBeVisible();
        await expect(page.locator('[data-testid="main-content"]')).toBeVisible();
        await expect(page.locator('[data-testid="footer"]')).toBeVisible();
      }
    });

    test('should maintain accessibility standards', async ({ page }) => {
      const pages = [
        '/dashboard',
        '/market-data',
        '/trading',
        '/portfolio'
      ];

      for (const pageUrl of pages) {
        await page.goto(pageUrl);
        await page.waitForLoadState('networkidle');

        // Run accessibility checks
        const accessibilityResults = await regressionHelper.runAccessibilityCheck(page);

        // Should have no critical accessibility violations
        expect(accessibilityResults.violations.filter(v => v.impact === 'critical')).toHaveLength(0);

        // Should maintain or improve accessibility score
        const baseline = regressionHelper.getBaselineData('accessibility');

        if (baseline?.scores?.[pageUrl]) {
          expect(accessibilityResults.score).toBeGreaterThanOrEqual(baseline.scores[pageUrl]);
        }
      }
    });
  });
});