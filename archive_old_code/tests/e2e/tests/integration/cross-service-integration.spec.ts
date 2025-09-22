import { test, expect } from '@playwright/test';
import { AuthenticationHelper } from '../../utils/authentication-helper';
import { TestDataManager } from '../../utils/test-data-manager';
import { TradingHelper } from '../../utils/trading-helper';
import { APIHelper } from '../../utils/api-helper';

test.describe('Cross-Service Integration Tests', () => {
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

  test.describe('@integration @smoke Service Communication', () => {
    test('should validate API Gateway to User Service integration', async ({ page }) => {
      // Test through UI
      await page.goto('/profile');
      await expect(page.locator('[data-testid="user-profile"]')).toBeVisible();

      // Validate through API
      await apiHelper.authenticate('premium_trader');
      const userProfile = await apiHelper.getUserProfile();

      expect(userProfile.status).toBe(200);
      expect(userProfile.data).toHaveProperty('id');
      expect(userProfile.data).toHaveProperty('email');
      expect(userProfile.data.role).toBe('premium_trader');

      // Cross-validate UI and API data
      const uiEmail = await page.locator('[data-testid="user-email"]').textContent();
      expect(uiEmail).toBe(userProfile.data.email);
    });

    test('should validate Trading Engine to Market Data integration', async ({ page }) => {
      // Place order through UI
      const orderDetails = await tradingHelper.placeMarketOrder(page, {
        symbol: 'EURUSD',
        side: 'buy',
        quantity: 10000
      });

      // Verify order through API
      const apiOrderResponse = await apiHelper.getOrder(orderDetails);
      expect(apiOrderResponse.status).toBe(200);

      // Verify market data is being used
      const marketDataResponse = await apiHelper.getMarketData('EURUSD');
      expect(marketDataResponse.status).toBe(200);
      expect(marketDataResponse.data).toHaveProperty('price');
      expect(marketDataResponse.data).toHaveProperty('timestamp');

      // Check that order price is reasonable relative to market price
      const marketPrice = marketDataResponse.data.price;
      const orderPrice = apiOrderResponse.data.executedPrice || apiOrderResponse.data.price;

      if (orderPrice && marketPrice) {
        const priceDifference = Math.abs(orderPrice - marketPrice);
        expect(priceDifference).toBeLessThan(marketPrice * 0.01); // Within 1%
      }
    });

    test('should validate Portfolio Service integration with Trading Engine', async ({ page }) => {
      // Get initial portfolio state
      const initialPortfolio = await tradingHelper.getPortfolioSummary(page);
      const initialBalance = initialPortfolio.balance;

      // Place and execute trade
      await tradingHelper.placeMarketOrder(page, {
        symbol: 'GBPUSD',
        side: 'buy',
        quantity: 5000
      });

      // Wait for portfolio update
      await page.waitForTimeout(2000);

      // Verify portfolio reflects the trade
      const updatedPortfolio = await tradingHelper.getPortfolioSummary(page);

      // Balance should change due to margin requirements
      expect(updatedPortfolio.marginUsed).toBeGreaterThan(initialPortfolio.marginUsed);
      expect(updatedPortfolio.marginAvailable).toBeLessThan(initialPortfolio.marginAvailable);

      // Verify through API
      const apiPortfolio = await apiHelper.getPortfolio();
      expect(apiPortfolio.status).toBe(200);
      expect(apiPortfolio.data.marginUsed).toBeCloseTo(updatedPortfolio.marginUsed, 2);
    });

    test('should validate Database Service consistency across all services', async ({ page }) => {
      // Create strategy through UI
      const strategyConfig = {
        name: 'Integration Test Strategy',
        type: 'momentum',
        symbol: 'USDJPY',
        timeframe: '1h'
      };

      const strategyId = await tradingHelper.createStrategy(page, strategyConfig);

      // Verify strategy through API
      const apiStrategy = await apiHelper.getStrategy(strategyId);
      expect(apiStrategy.status).toBe(200);
      expect(apiStrategy.data.name).toBe(strategyConfig.name);

      // Enable strategy and place orders
      await tradingHelper.enableStrategy(page, strategyConfig.name);

      // Wait for automated orders (if any)
      await page.waitForTimeout(5000);

      // Check that all services have consistent data
      const orders = await apiHelper.getOrders({ strategyId });
      const positions = await apiHelper.getPositions();
      const portfolio = await apiHelper.getPortfolio();

      // All API calls should succeed
      expect(orders.status).toBe(200);
      expect(positions.status).toBe(200);
      expect(portfolio.status).toBe(200);

      // Data should be consistent
      if (orders.data.length > 0) {
        const orderSymbol = orders.data[0].symbol;
        const hasPosition = positions.data.some((pos: any) => pos.symbol === orderSymbol);

        if (hasPosition) {
          expect(portfolio.data.marginUsed).toBeGreaterThan(0);
        }
      }
    });
  });

  test.describe('@integration Real-time Data Flow', () => {
    test('should validate real-time market data propagation', async ({ page }) => {
      await page.goto('/market-data');

      // Subscribe to market data through API
      await apiHelper.subscribeToMarketData(['EURUSD', 'GBPUSD']);

      // Monitor price updates in UI
      const initialPrice = await page.locator('[data-testid="price-EURUSD"]').textContent();

      // Wait for price update
      await page.waitForFunction(
        (selector, initial) => {
          const element = document.querySelector(selector);
          return element && element.textContent !== initial;
        },
        '[data-testid="price-EURUSD"]',
        initialPrice,
        { timeout: 15000 }
      );

      // Verify timestamp updates
      const timestamp = await page.locator('[data-testid="timestamp-EURUSD"]').textContent();
      const timestampDate = new Date(timestamp!);
      const now = new Date();

      expect(now.getTime() - timestampDate.getTime()).toBeLessThan(60000); // Within 1 minute
    });

    test('should validate order status real-time updates', async ({ page }) => {
      // Place order
      const orderId = await tradingHelper.placeMarketOrder(page, {
        symbol: 'EURUSD',
        side: 'buy',
        quantity: 1000
      });

      // Subscribe to order updates
      await apiHelper.subscribeToOrderUpdates();

      // Navigate to orders page
      await page.goto('/orders');

      // Monitor order status changes
      const initialStatus = await page.locator(`[data-testid="order-status-${orderId}"]`).textContent();

      // Wait for status change (pending -> filled)
      if (initialStatus === 'pending') {
        await page.waitForFunction(
          (id, initial) => {
            const element = document.querySelector(`[data-testid="order-status-${id}"]`);
            return element && element.textContent !== initial;
          },
          orderId,
          initialStatus,
          { timeout: 30000 }
        );

        const finalStatus = await page.locator(`[data-testid="order-status-${orderId}"]`).textContent();
        expect(finalStatus).toMatch(/filled|cancelled|rejected/);
      }
    });

    test('should validate position updates across services', async ({ page }) => {
      // Subscribe to position updates
      await apiHelper.subscribeToPositionUpdates();

      // Place order that creates position
      await tradingHelper.placeMarketOrder(page, {
        symbol: 'GBPUSD',
        side: 'buy',
        quantity: 10000
      });

      // Check positions page
      await page.goto('/positions');

      // Should show new position
      await expect(page.locator('[data-testid="position-GBPUSD"]')).toBeVisible({ timeout: 10000 });

      // Verify position details update in real-time
      const position = await tradingHelper.getPositionDetails(page, 'GBPUSD');
      expect(position).toBeTruthy();
      expect(position.quantity).toBe(10000);

      // Monitor unrealized P&L updates
      const initialPnL = position.unrealizedPnL;

      // Wait for P&L to change (due to price movements)
      await page.waitForFunction(
        (symbol, initial) => {
          const element = document.querySelector(`[data-testid="unrealized-pnl-${symbol}"]`);
          if (!element) return false;
          const current = parseFloat(element.textContent || '0');
          return Math.abs(current - initial) > 0.01; // Changed by at least 1 cent
        },
        'GBPUSD',
        initialPnL,
        { timeout: 30000 }
      );
    });
  });

  test.describe('@integration Error Handling and Recovery', () => {
    test('should handle service failures gracefully', async ({ page }) => {
      // Simulate API failures by intercepting requests
      await page.route('**/api/v1/market-data/**', route => {
        route.fulfill({
          status: 503,
          body: JSON.stringify({ error: 'Service Unavailable' })
        });
      });

      await page.goto('/market-data');

      // Should show error message but not crash
      await expect(page.locator('[data-testid="market-data-error"]')).toBeVisible({ timeout: 10000 });
      await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();

      // Restore service and retry
      await page.unroute('**/api/v1/market-data/**');
      await page.click('[data-testid="retry-button"]');

      // Should recover
      await expect(page.locator('[data-testid="market-data-table"]')).toBeVisible({ timeout: 10000 });
    });

    test('should handle database connection issues', async ({ page }) => {
      // Try to access user data with simulated DB failure
      await page.route('**/api/v1/users/**', route => {
        route.fulfill({
          status: 500,
          body: JSON.stringify({ error: 'Database connection failed' })
        });
      });

      await page.goto('/profile');

      // Should show error state
      await expect(page.locator('[data-testid="profile-error"]')).toBeVisible();
      await expect(page.locator('[data-testid="contact-support"]')).toBeVisible();

      // User should still be able to access other features
      await page.goto('/market-data');
      await expect(page.locator('[data-testid="market-data-table"]')).toBeVisible();
    });

    test('should handle trading engine failures', async ({ page }) => {
      // Simulate trading engine failure
      await page.route('**/api/v1/orders', route => {
        if (route.request().method() === 'POST') {
          route.fulfill({
            status: 503,
            body: JSON.stringify({ error: 'Trading engine unavailable' })
          });
        } else {
          route.continue();
        }
      });

      await page.goto('/trading');
      await page.click('[data-testid="new-order-button"]');

      await page.selectOption('[data-testid="order-symbol-select"]', 'EURUSD');
      await page.selectOption('[data-testid="order-side-select"]', 'buy');
      await page.fill('[data-testid="order-quantity-input"]', '10000');

      await page.click('[data-testid="place-order-button"]');

      // Should show trading engine error
      await expect(page.locator('[data-testid="trading-engine-error"]')).toBeVisible();
      await expect(page.locator('[data-testid="retry-order-button"]')).toBeVisible();

      // Other services should still work
      await page.goto('/portfolio');
      await expect(page.locator('[data-testid="portfolio-summary"]')).toBeVisible();
    });
  });

  test.describe('@integration Data Consistency', () => {
    test('should maintain data consistency across service restarts', async ({ page }) => {
      // Create initial state
      const strategyId = await tradingHelper.createStrategy(page, {
        name: 'Consistency Test Strategy',
        type: 'scalping',
        symbol: 'EURUSD'
      });

      const orderId = await tradingHelper.placeMarketOrder(page, {
        symbol: 'EURUSD',
        side: 'buy',
        quantity: 5000
      });

      // Verify initial state through API
      const initialStrategy = await apiHelper.getStrategy(strategyId);
      const initialOrder = await apiHelper.getOrder(orderId);

      expect(initialStrategy.status).toBe(200);
      expect(initialOrder.status).toBe(200);

      // Simulate service restart by clearing and re-authenticating
      apiHelper.clearAuthToken();
      await apiHelper.authenticate('premium_trader');

      // Verify data persists after restart
      const persistedStrategy = await apiHelper.getStrategy(strategyId);
      const persistedOrder = await apiHelper.getOrder(orderId);

      expect(persistedStrategy.status).toBe(200);
      expect(persistedOrder.status).toBe(200);

      expect(persistedStrategy.data.name).toBe(initialStrategy.data.name);
      expect(persistedOrder.data.symbol).toBe(initialOrder.data.symbol);
    });

    test('should handle concurrent operations correctly', async ({ browser }) => {
      // Create multiple browser contexts for concurrent operations
      const contexts = await Promise.all([
        browser.newContext(),
        browser.newContext(),
        browser.newContext()
      ]);

      const pages = await Promise.all(
        contexts.map(context => context.newPage())
      );

      // Login all users
      await Promise.all([
        authHelper.loginAs(pages[0], 'trader'),
        authHelper.loginAs(pages[1], 'premium_trader'),
        authHelper.loginAs(pages[2], 'trader')
      ]);

      // Perform concurrent operations
      const operations = [
        tradingHelper.placeMarketOrder(pages[0], { symbol: 'EURUSD', side: 'buy', quantity: 1000 }),
        tradingHelper.placeMarketOrder(pages[1], { symbol: 'EURUSD', side: 'sell', quantity: 2000 }),
        tradingHelper.placeMarketOrder(pages[2], { symbol: 'GBPUSD', side: 'buy', quantity: 1500 })
      ];

      const results = await Promise.all(operations);

      // All operations should succeed
      expect(results).toHaveLength(3);
      results.forEach(orderId => {
        expect(orderId).toBeTruthy();
      });

      // Verify system consistency
      for (const page of pages) {
        await page.goto('/orders');
        await expect(page.locator('[data-testid="orders-table"]')).toBeVisible();
      }

      // Cleanup
      await Promise.all(contexts.map(context => context.close()));
    });

    test('should handle transaction rollbacks correctly', async ({ page }) => {
      // Get initial portfolio state
      const initialPortfolio = await apiHelper.getPortfolio();

      // Simulate a failed transaction by intercepting the request
      await page.route('**/api/v1/orders', route => {
        if (route.request().method() === 'POST') {
          // Simulate partial success followed by rollback
          route.fulfill({
            status: 409,
            body: JSON.stringify({
              error: 'Insufficient margin',
              details: 'Transaction rolled back'
            })
          });
        } else {
          route.continue();
        }
      });

      // Try to place order with insufficient margin
      await page.goto('/trading');
      await page.click('[data-testid="new-order-button"]');

      await page.selectOption('[data-testid="order-symbol-select"]', 'EURUSD');
      await page.selectOption('[data-testid="order-side-select"]', 'buy');
      await page.fill('[data-testid="order-quantity-input"]', '1000000'); // Very large order

      await page.click('[data-testid="place-order-button"]');

      // Should show error
      await expect(page.locator('[data-testid="insufficient-margin-error"]')).toBeVisible();

      // Portfolio should remain unchanged
      await page.unroute('**/api/v1/orders');
      const finalPortfolio = await apiHelper.getPortfolio();

      expect(finalPortfolio.data.balance).toBeCloseTo(initialPortfolio.data.balance, 2);
      expect(finalPortfolio.data.marginUsed).toBeCloseTo(initialPortfolio.data.marginUsed, 2);
    });
  });

  test.describe('@integration Performance and Scalability', () => {
    test('should handle high-frequency data updates', async ({ page }) => {
      await page.goto('/market-data');

      // Monitor multiple symbols simultaneously
      const symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD'];

      // Verify all symbols are displaying data
      for (const symbol of symbols) {
        await expect(page.locator(`[data-testid="price-${symbol}"]`)).toBeVisible();
      }

      // Monitor update frequency
      const updateCounts: Record<string, number> = {};
      const monitoringDuration = 30000; // 30 seconds

      const startTime = Date.now();

      while (Date.now() - startTime < monitoringDuration) {
        for (const symbol of symbols) {
          const timestamp = await page.locator(`[data-testid="timestamp-${symbol}"]`).textContent();

          if (timestamp) {
            updateCounts[symbol] = (updateCounts[symbol] || 0) + 1;
          }
        }

        await page.waitForTimeout(1000);
      }

      // Should have received multiple updates for each symbol
      for (const symbol of symbols) {
        expect(updateCounts[symbol]).toBeGreaterThan(10); // At least 10 updates in 30 seconds
      }
    });

    test('should maintain performance under load', async ({ page }) => {
      const startTime = Date.now();

      // Perform multiple operations quickly
      const operations = [
        () => page.goto('/dashboard'),
        () => page.goto('/market-data'),
        () => page.goto('/portfolio'),
        () => page.goto('/orders'),
        () => page.goto('/positions'),
        () => page.goto('/analytics')
      ];

      for (const operation of operations) {
        await operation();
        await page.waitForLoadState('networkidle');
      }

      const totalTime = Date.now() - startTime;

      // Should complete navigation within reasonable time
      expect(totalTime).toBeLessThan(30000); // 30 seconds for all operations

      // All pages should be responsive
      await page.goto('/dashboard');
      await expect(page.locator('[data-testid="dashboard-content"]')).toBeVisible({ timeout: 5000 });
    });
  });
});