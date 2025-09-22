import { test, expect } from '@playwright/test';
import { AuthenticationHelper } from '../../utils/authentication-helper';
import { TestDataManager } from '../../utils/test-data-manager';
import { TradingHelper } from '../../utils/trading-helper';
import { APIHelper } from '../../utils/api-helper';

test.describe('Complete Trading Workflow', () => {
  let authHelper: AuthenticationHelper;
  let testDataManager: TestDataManager;
  let tradingHelper: TradingHelper;
  let apiHelper: APIHelper;

  test.beforeEach(async ({ page }) => {
    authHelper = new AuthenticationHelper();
    testDataManager = new TestDataManager();
    tradingHelper = new TradingHelper();
    apiHelper = new APIHelper();

    // Login as premium trader for full access
    await authHelper.loginAs(page, 'premium_trader');
  });

  test.describe('@e2e @smoke Complete Trading Journey', () => {
    test('should complete full trading workflow from strategy creation to order execution', async ({ page }) => {
      const testStrategy = {
        name: 'E2E Test Strategy',
        type: 'momentum',
        symbol: 'EURUSD',
        timeframe: '15m',
        riskLevel: 'medium'
      };

      // Step 1: Create Trading Strategy
      console.log('Step 1: Creating trading strategy...');
      await page.goto('/strategies');
      await page.click('[data-testid="create-strategy-button"]');

      await page.fill('[data-testid="strategy-name-input"]', testStrategy.name);
      await page.selectOption('[data-testid="strategy-type-select"]', testStrategy.type);
      await page.selectOption('[data-testid="symbol-select"]', testStrategy.symbol);
      await page.selectOption('[data-testid="timeframe-select"]', testStrategy.timeframe);
      await page.selectOption('[data-testid="risk-level-select"]', testStrategy.riskLevel);

      // Configure strategy parameters
      await page.fill('[data-testid="stop-loss-input"]', '2.0');
      await page.fill('[data-testid="take-profit-input"]', '4.0');
      await page.fill('[data-testid="max-positions-input"]', '3');

      await page.click('[data-testid="save-strategy-button"]');
      await expect(page.locator('[data-testid="strategy-created-success"]')).toBeVisible();

      const strategyId = await page.locator('[data-testid="strategy-id"]').textContent();

      // Step 2: Backtest Strategy
      console.log('Step 2: Running strategy backtest...');
      await page.click('[data-testid="backtest-button"]');
      await page.selectOption('[data-testid="backtest-period-select"]', '1month');
      await page.click('[data-testid="run-backtest-button"]');

      // Wait for backtest completion
      await expect(page.locator('[data-testid="backtest-results"]')).toBeVisible({ timeout: 30000 });

      // Verify backtest results
      const winRate = await page.locator('[data-testid="win-rate"]').textContent();
      const totalTrades = await page.locator('[data-testid="total-trades"]').textContent();
      const profitFactor = await page.locator('[data-testid="profit-factor"]').textContent();

      expect(parseFloat(winRate!)).toBeGreaterThan(0);
      expect(parseInt(totalTrades!)).toBeGreaterThan(0);
      expect(parseFloat(profitFactor!)).toBeGreaterThan(0);

      // Step 3: Enable Live Trading
      console.log('Step 3: Enabling live trading...');
      await page.click('[data-testid="enable-live-trading-button"]');
      await page.check('[data-testid="risk-acknowledgment-checkbox"]');
      await page.click('[data-testid="confirm-live-trading-button"]');

      await expect(page.locator('[data-testid="strategy-status"]')).toContainText('Active');

      // Step 4: Monitor Real-time Market Data
      console.log('Step 4: Monitoring market data...');
      await page.goto('/market-data');

      // Verify real-time price updates
      await expect(page.locator(`[data-testid="price-${testStrategy.symbol}"]`)).toBeVisible();

      const initialPrice = await page.locator(`[data-testid="price-${testStrategy.symbol}"]`).textContent();

      // Wait for price update
      await page.waitForFunction(
        (selector, initial) => {
          const element = document.querySelector(selector);
          return element && element.textContent !== initial;
        },
        `[data-testid="price-${testStrategy.symbol}"]`,
        initialPrice,
        { timeout: 10000 }
      );

      // Step 5: Place Manual Order
      console.log('Step 5: Placing manual order...');
      await page.goto('/trading');
      await page.click('[data-testid="new-order-button"]');

      await page.selectOption('[data-testid="order-symbol-select"]', testStrategy.symbol);
      await page.selectOption('[data-testid="order-side-select"]', 'buy');
      await page.selectOption('[data-testid="order-type-select"]', 'market');
      await page.fill('[data-testid="order-quantity-input"]', '10000');

      // Set stop loss and take profit
      await page.fill('[data-testid="stop-loss-input"]', '1.0850');
      await page.fill('[data-testid="take-profit-input"]', '1.0950');

      await page.click('[data-testid="place-order-button"]');
      await expect(page.locator('[data-testid="order-placed-success"]')).toBeVisible();

      const orderId = await page.locator('[data-testid="order-id"]').textContent();

      // Step 6: Verify Order Execution
      console.log('Step 6: Verifying order execution...');
      await page.goto('/orders');

      // Check order status
      await expect(page.locator(`[data-testid="order-${orderId}"]`)).toBeVisible();
      await expect(page.locator(`[data-testid="order-status-${orderId}"]`)).toContainText(/filled|pending/);

      // Step 7: Monitor Position
      console.log('Step 7: Monitoring position...');
      await page.goto('/positions');

      if (await page.locator(`[data-testid="position-${testStrategy.symbol}"]`).isVisible()) {
        // Verify position details
        await expect(page.locator(`[data-testid="position-symbol-${testStrategy.symbol}"]`)).toContainText(testStrategy.symbol);
        await expect(page.locator(`[data-testid="position-quantity-${testStrategy.symbol}"]`)).toContainText('10,000');

        // Check unrealized P&L
        const unrealizedPnL = await page.locator(`[data-testid="unrealized-pnl-${testStrategy.symbol}"]`).textContent();
        expect(unrealizedPnL).toMatch(/[+-]?\d+\.?\d*/);
      }

      // Step 8: Close Position
      console.log('Step 8: Closing position...');
      if (await page.locator(`[data-testid="close-position-${testStrategy.symbol}"]`).isVisible()) {
        await page.click(`[data-testid="close-position-${testStrategy.symbol}"]`);
        await page.click('[data-testid="confirm-close-position"]');

        await expect(page.locator('[data-testid="position-closed-success"]')).toBeVisible();
      }

      // Step 9: Review Trading History
      console.log('Step 9: Reviewing trading history...');
      await page.goto('/history');

      // Verify trade appears in history
      await expect(page.locator(`[data-testid="trade-${orderId}"]`)).toBeVisible();

      // Check trade details
      await page.click(`[data-testid="trade-details-${orderId}"]`);
      await expect(page.locator('[data-testid="trade-details-modal"]')).toBeVisible();

      await expect(page.locator('[data-testid="trade-symbol"]')).toContainText(testStrategy.symbol);
      await expect(page.locator('[data-testid="trade-quantity"]')).toContainText('10,000');

      // Step 10: Generate Performance Report
      console.log('Step 10: Generating performance report...');
      await page.goto('/reports');
      await page.click('[data-testid="generate-report-button"]');

      await page.selectOption('[data-testid="report-type-select"]', 'daily_pnl');
      await page.fill('[data-testid="date-from-input"]', '2024-01-01');
      await page.fill('[data-testid="date-to-input"]', new Date().toISOString().split('T')[0]);

      await page.click('[data-testid="generate-button"]');
      await expect(page.locator('[data-testid="report-generated-success"]')).toBeVisible();

      // Verify report content
      await expect(page.locator('[data-testid="report-total-trades"]')).toBeVisible();
      await expect(page.locator('[data-testid="report-total-pnl"]')).toBeVisible();
      await expect(page.locator('[data-testid="report-win-rate"]')).toBeVisible();

      console.log('✅ Complete trading workflow executed successfully');
    });

    test('should handle trading workflow with multiple strategies', async ({ page }) => {
      const strategies = [
        { name: 'Momentum Strategy', type: 'momentum', symbol: 'EURUSD' },
        { name: 'Mean Reversion Strategy', type: 'mean_reversion', symbol: 'GBPUSD' },
        { name: 'Scalping Strategy', type: 'scalping', symbol: 'USDJPY' }
      ];

      // Create multiple strategies
      for (const strategy of strategies) {
        await tradingHelper.createStrategy(page, strategy);
        await tradingHelper.enableStrategy(page, strategy.name);
      }

      // Monitor all strategies
      await page.goto('/dashboard');

      // Verify all strategies are active
      for (const strategy of strategies) {
        await expect(page.locator(`[data-testid="strategy-${strategy.name}"]`)).toBeVisible();
        await expect(page.locator(`[data-testid="strategy-status-${strategy.name}"]`)).toContainText('Active');
      }

      // Check portfolio diversification
      await page.goto('/portfolio');

      // Should show positions across multiple symbols
      for (const strategy of strategies) {
        if (await page.locator(`[data-testid="exposure-${strategy.symbol}"]`).isVisible()) {
          await expect(page.locator(`[data-testid="exposure-${strategy.symbol}"]`)).toBeVisible();
        }
      }
    });
  });

  test.describe('@e2e @regression Risk Management Workflow', () => {
    test('should enforce risk limits and circuit breakers', async ({ page }) => {
      // Set up risk limits
      await page.goto('/settings/risk');

      await page.fill('[data-testid="max-daily-loss-input"]', '1000');
      await page.fill('[data-testid="max-position-size-input"]', '50000');
      await page.fill('[data-testid="max-open-positions-input"]', '5');
      await page.click('[data-testid="save-risk-settings-button"]');

      // Try to place order exceeding limits
      await page.goto('/trading');
      await page.click('[data-testid="new-order-button"]');

      await page.selectOption('[data-testid="order-symbol-select"]', 'EURUSD');
      await page.selectOption('[data-testid="order-side-select"]', 'buy');
      await page.fill('[data-testid="order-quantity-input"]', '100000'); // Exceeds limit

      await page.click('[data-testid="place-order-button"]');

      // Should show risk limit error
      await expect(page.locator('[data-testid="risk-limit-error"]')).toContainText('exceeds maximum position size');
    });

    test('should handle margin requirements and leverage', async ({ page }) => {
      // Check margin requirements
      await page.goto('/trading');
      await page.click('[data-testid="new-order-button"]');

      await page.selectOption('[data-testid="order-symbol-select"]', 'EURUSD');
      await page.fill('[data-testid="order-quantity-input"]', '100000');

      // Check calculated margin
      const requiredMargin = await page.locator('[data-testid="required-margin"]').textContent();
      expect(parseFloat(requiredMargin!)).toBeGreaterThan(0);

      // Check available margin
      const availableMargin = await page.locator('[data-testid="available-margin"]').textContent();
      expect(parseFloat(availableMargin!)).toBeGreaterThan(0);
    });
  });

  test.describe('@e2e @integration Cross-Service Integration', () => {
    test('should integrate trading with portfolio management', async ({ page }) => {
      // Place a trade
      const orderDetails = await tradingHelper.placeMarketOrder(page, {
        symbol: 'EURUSD',
        side: 'buy',
        quantity: 10000
      });

      // Check portfolio update
      await page.goto('/portfolio');
      await page.waitForLoadState('networkidle');

      // Portfolio should reflect the new position
      if (await page.locator('[data-testid="portfolio-positions"]').isVisible()) {
        await expect(page.locator(`[data-testid="position-EURUSD"]`)).toBeVisible();
      }

      // Check balance updates
      const portfolioBalance = await page.locator('[data-testid="portfolio-balance"]').textContent();
      expect(parseFloat(portfolioBalance!)).toBeGreaterThan(0);
    });

    test('should integrate with analytics and reporting', async ({ page }) => {
      // Execute some trades
      await tradingHelper.executeMultipleTrades(page, [
        { symbol: 'EURUSD', side: 'buy', quantity: 10000 },
        { symbol: 'GBPUSD', side: 'sell', quantity: 15000 },
        { symbol: 'USDJPY', side: 'buy', quantity: 20000 }
      ]);

      // Check analytics dashboard
      await page.goto('/analytics');

      // Should show updated metrics
      await expect(page.locator('[data-testid="trades-today"]')).toContainText(/[1-9]\d*/);
      await expect(page.locator('[data-testid="active-positions"]')).toContainText(/[0-9]+/);
      await expect(page.locator('[data-testid="total-pnl"]')).toBeVisible();

      // Check detailed analytics
      await page.click('[data-testid="detailed-analytics-tab"]');
      await expect(page.locator('[data-testid="performance-chart"]')).toBeVisible();
      await expect(page.locator('[data-testid="risk-metrics"]')).toBeVisible();
    });

    test('should integrate with market data feeds', async ({ page }) => {
      await page.goto('/market-data');

      // Verify real-time data feeds
      const symbols = ['EURUSD', 'GBPUSD', 'USDJPY'];

      for (const symbol of symbols) {
        await expect(page.locator(`[data-testid="price-${symbol}"]`)).toBeVisible();
        await expect(page.locator(`[data-testid="spread-${symbol}"]`)).toBeVisible();
        await expect(page.locator(`[data-testid="volume-${symbol}"]`)).toBeVisible();
      }

      // Check price updates
      const initialPrice = await page.locator('[data-testid="price-EURUSD"]').textContent();

      // Wait for price to update
      await page.waitForFunction(
        (selector, initial) => {
          const element = document.querySelector(selector);
          return element && element.textContent !== initial;
        },
        '[data-testid="price-EURUSD"]',
        initialPrice,
        { timeout: 15000 }
      );
    });
  });

  test.describe('@e2e @performance Performance and Load Testing', () => {
    test('should handle high-frequency trading operations', async ({ page }) => {
      const startTime = Date.now();

      // Place multiple orders rapidly
      for (let i = 0; i < 10; i++) {
        await tradingHelper.placeMarketOrder(page, {
          symbol: 'EURUSD',
          side: i % 2 === 0 ? 'buy' : 'sell',
          quantity: 1000
        });
      }

      const endTime = Date.now();
      const totalTime = endTime - startTime;

      // Should complete within reasonable time
      expect(totalTime).toBeLessThan(30000); // 30 seconds

      // Verify all orders were processed
      await page.goto('/orders');
      const orderRows = await page.locator('[data-testid^="order-"]').count();
      expect(orderRows).toBeGreaterThanOrEqual(10);
    });

    test('should handle concurrent user sessions', async ({ browser }) => {
      // Create multiple browser contexts for concurrent users
      const contexts = await Promise.all([
        browser.newContext(),
        browser.newContext(),
        browser.newContext()
      ]);

      const pages = await Promise.all(
        contexts.map(context => context.newPage())
      );

      // Login different users concurrently
      await Promise.all([
        authHelper.loginAs(pages[0], 'trader'),
        authHelper.loginAs(pages[1], 'premium_trader'),
        authHelper.loginAs(pages[2], 'trader')
      ]);

      // Execute trading operations concurrently
      await Promise.all([
        tradingHelper.placeMarketOrder(pages[0], { symbol: 'EURUSD', side: 'buy', quantity: 5000 }),
        tradingHelper.placeMarketOrder(pages[1], { symbol: 'GBPUSD', side: 'sell', quantity: 7500 }),
        tradingHelper.placeMarketOrder(pages[2], { symbol: 'USDJPY', side: 'buy', quantity: 10000 })
      ]);

      // All operations should succeed
      for (const page of pages) {
        await expect(page.locator('[data-testid="order-placed-success"]')).toBeVisible();
      }

      // Cleanup
      await Promise.all(contexts.map(context => context.close()));
    });
  });
});