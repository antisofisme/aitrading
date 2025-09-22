import { Page, expect } from '@playwright/test';

export interface OrderRequest {
  symbol: string;
  side: 'buy' | 'sell';
  type?: 'market' | 'limit' | 'stop';
  quantity: number;
  price?: number;
  stopLoss?: number;
  takeProfit?: number;
}

export interface StrategyConfig {
  name: string;
  type: string;
  symbol?: string;
  timeframe?: string;
  riskLevel?: string;
  parameters?: Record<string, any>;
}

/**
 * Helper class for trading-related operations in E2E tests
 */
export class TradingHelper {

  /**
   * Create a new trading strategy
   */
  async createStrategy(page: Page, config: StrategyConfig): Promise<string> {
    await page.goto('/strategies');
    await page.click('[data-testid="create-strategy-button"]');

    // Fill basic strategy information
    await page.fill('[data-testid="strategy-name-input"]', config.name);
    await page.selectOption('[data-testid="strategy-type-select"]', config.type);

    if (config.symbol) {
      await page.selectOption('[data-testid="symbol-select"]', config.symbol);
    }

    if (config.timeframe) {
      await page.selectOption('[data-testid="timeframe-select"]', config.timeframe);
    }

    if (config.riskLevel) {
      await page.selectOption('[data-testid="risk-level-select"]', config.riskLevel);
    }

    // Configure parameters if provided
    if (config.parameters) {
      for (const [key, value] of Object.entries(config.parameters)) {
        await page.fill(`[data-testid="${key}-input"]`, value.toString());
      }
    }

    await page.click('[data-testid="save-strategy-button"]');
    await expect(page.locator('[data-testid="strategy-created-success"]')).toBeVisible();

    const strategyId = await page.locator('[data-testid="strategy-id"]').textContent();
    return strategyId || '';
  }

  /**
   * Enable a trading strategy
   */
  async enableStrategy(page: Page, strategyName: string): Promise<void> {
    await page.goto('/strategies');
    await page.click(`[data-testid="strategy-${strategyName}"] [data-testid="enable-button"]`);
    await page.check('[data-testid="risk-acknowledgment-checkbox"]');
    await page.click('[data-testid="confirm-enable-button"]');
    await expect(page.locator(`[data-testid="strategy-${strategyName}"] [data-testid="status"]`)).toContainText('Active');
  }

  /**
   * Disable a trading strategy
   */
  async disableStrategy(page: Page, strategyName: string): Promise<void> {
    await page.goto('/strategies');
    await page.click(`[data-testid="strategy-${strategyName}"] [data-testid="disable-button"]`);
    await page.click('[data-testid="confirm-disable-button"]');
    await expect(page.locator(`[data-testid="strategy-${strategyName}"] [data-testid="status"]`)).toContainText('Inactive');
  }

  /**
   * Place a market order
   */
  async placeMarketOrder(page: Page, order: OrderRequest): Promise<string> {
    await page.goto('/trading');
    await page.click('[data-testid="new-order-button"]');

    await page.selectOption('[data-testid="order-symbol-select"]', order.symbol);
    await page.selectOption('[data-testid="order-side-select"]', order.side);
    await page.selectOption('[data-testid="order-type-select"]', order.type || 'market');
    await page.fill('[data-testid="order-quantity-input"]', order.quantity.toString());

    if (order.stopLoss) {
      await page.fill('[data-testid="stop-loss-input"]', order.stopLoss.toString());
    }

    if (order.takeProfit) {
      await page.fill('[data-testid="take-profit-input"]', order.takeProfit.toString());
    }

    await page.click('[data-testid="place-order-button"]');
    await expect(page.locator('[data-testid="order-placed-success"]')).toBeVisible();

    const orderId = await page.locator('[data-testid="order-id"]').textContent();
    return orderId || '';
  }

  /**
   * Place a limit order
   */
  async placeLimitOrder(page: Page, order: OrderRequest): Promise<string> {
    if (!order.price) {
      throw new Error('Price is required for limit orders');
    }

    const orderWithType = { ...order, type: 'limit' as const };

    await page.goto('/trading');
    await page.click('[data-testid="new-order-button"]');

    await page.selectOption('[data-testid="order-symbol-select"]', orderWithType.symbol);
    await page.selectOption('[data-testid="order-side-select"]', orderWithType.side);
    await page.selectOption('[data-testid="order-type-select"]', orderWithType.type);
    await page.fill('[data-testid="order-quantity-input"]', orderWithType.quantity.toString());
    await page.fill('[data-testid="order-price-input"]', order.price.toString());

    if (order.stopLoss) {
      await page.fill('[data-testid="stop-loss-input"]', order.stopLoss.toString());
    }

    if (order.takeProfit) {
      await page.fill('[data-testid="take-profit-input"]', order.takeProfit.toString());
    }

    await page.click('[data-testid="place-order-button"]');
    await expect(page.locator('[data-testid="order-placed-success"]')).toBeVisible();

    const orderId = await page.locator('[data-testid="order-id"]').textContent();
    return orderId || '';
  }

  /**
   * Cancel an order
   */
  async cancelOrder(page: Page, orderId: string): Promise<void> {
    await page.goto('/orders');
    await page.click(`[data-testid="cancel-order-${orderId}"]`);
    await page.click('[data-testid="confirm-cancel-button"]');
    await expect(page.locator(`[data-testid="order-status-${orderId}"]`)).toContainText('Cancelled');
  }

  /**
   * Close a position
   */
  async closePosition(page: Page, symbol: string): Promise<void> {
    await page.goto('/positions');
    await page.click(`[data-testid="close-position-${symbol}"]`);
    await page.click('[data-testid="confirm-close-position"]');
    await expect(page.locator('[data-testid="position-closed-success"]')).toBeVisible();
  }

  /**
   * Execute multiple trades
   */
  async executeMultipleTrades(page: Page, orders: OrderRequest[]): Promise<string[]> {
    const orderIds: string[] = [];

    for (const order of orders) {
      const orderId = await this.placeMarketOrder(page, order);
      orderIds.push(orderId);

      // Small delay between orders
      await page.waitForTimeout(1000);
    }

    return orderIds;
  }

  /**
   * Get current market price for a symbol
   */
  async getMarketPrice(page: Page, symbol: string): Promise<number> {
    await page.goto('/market-data');
    const priceText = await page.locator(`[data-testid="price-${symbol}"]`).textContent();
    return parseFloat(priceText || '0');
  }

  /**
   * Get current spread for a symbol
   */
  async getSpread(page: Page, symbol: string): Promise<number> {
    await page.goto('/market-data');
    const spreadText = await page.locator(`[data-testid="spread-${symbol}"]`).textContent();
    return parseFloat(spreadText || '0');
  }

  /**
   * Wait for order execution
   */
  async waitForOrderExecution(page: Page, orderId: string, timeout: number = 30000): Promise<void> {
    await page.goto('/orders');

    await page.waitForFunction(
      (id) => {
        const statusElement = document.querySelector(`[data-testid="order-status-${id}"]`);
        return statusElement && statusElement.textContent === 'Filled';
      },
      orderId,
      { timeout }
    );
  }

  /**
   * Get position details
   */
  async getPositionDetails(page: Page, symbol: string): Promise<any> {
    await page.goto('/positions');

    if (!(await page.locator(`[data-testid="position-${symbol}"]`).isVisible())) {
      return null;
    }

    const quantity = await page.locator(`[data-testid="position-quantity-${symbol}"]`).textContent();
    const entryPrice = await page.locator(`[data-testid="position-entry-price-${symbol}"]`).textContent();
    const currentPrice = await page.locator(`[data-testid="position-current-price-${symbol}"]`).textContent();
    const unrealizedPnL = await page.locator(`[data-testid="unrealized-pnl-${symbol}"]`).textContent();

    return {
      symbol,
      quantity: parseFloat(quantity || '0'),
      entryPrice: parseFloat(entryPrice || '0'),
      currentPrice: parseFloat(currentPrice || '0'),
      unrealizedPnL: parseFloat(unrealizedPnL || '0')
    };
  }

  /**
   * Get order details
   */
  async getOrderDetails(page: Page, orderId: string): Promise<any> {
    await page.goto('/orders');
    await page.click(`[data-testid="order-details-${orderId}"]`);

    await expect(page.locator('[data-testid="order-details-modal"]')).toBeVisible();

    const symbol = await page.locator('[data-testid="order-detail-symbol"]').textContent();
    const side = await page.locator('[data-testid="order-detail-side"]').textContent();
    const quantity = await page.locator('[data-testid="order-detail-quantity"]').textContent();
    const price = await page.locator('[data-testid="order-detail-price"]').textContent();
    const status = await page.locator('[data-testid="order-detail-status"]').textContent();

    await page.click('[data-testid="close-modal-button"]');

    return {
      orderId,
      symbol,
      side,
      quantity: parseFloat(quantity || '0'),
      price: parseFloat(price || '0'),
      status
    };
  }

  /**
   * Set risk parameters
   */
  async setRiskParameters(page: Page, params: {
    maxDailyLoss?: number;
    maxPositionSize?: number;
    maxOpenPositions?: number;
    leverage?: number;
  }): Promise<void> {
    await page.goto('/settings/risk');

    if (params.maxDailyLoss) {
      await page.fill('[data-testid="max-daily-loss-input"]', params.maxDailyLoss.toString());
    }

    if (params.maxPositionSize) {
      await page.fill('[data-testid="max-position-size-input"]', params.maxPositionSize.toString());
    }

    if (params.maxOpenPositions) {
      await page.fill('[data-testid="max-open-positions-input"]', params.maxOpenPositions.toString());
    }

    if (params.leverage) {
      await page.selectOption('[data-testid="leverage-select"]', params.leverage.toString());
    }

    await page.click('[data-testid="save-risk-settings-button"]');
    await expect(page.locator('[data-testid="risk-settings-saved"]')).toBeVisible();
  }

  /**
   * Run strategy backtest
   */
  async runBacktest(page: Page, strategyName: string, period: string = '1month'): Promise<any> {
    await page.goto('/strategies');
    await page.click(`[data-testid="strategy-${strategyName}"] [data-testid="backtest-button"]`);

    await page.selectOption('[data-testid="backtest-period-select"]', period);
    await page.click('[data-testid="run-backtest-button"]');

    // Wait for backtest completion
    await expect(page.locator('[data-testid="backtest-results"]')).toBeVisible({ timeout: 60000 });

    const winRate = await page.locator('[data-testid="win-rate"]').textContent();
    const totalTrades = await page.locator('[data-testid="total-trades"]').textContent();
    const profitFactor = await page.locator('[data-testid="profit-factor"]').textContent();
    const maxDrawdown = await page.locator('[data-testid="max-drawdown"]').textContent();
    const sharpeRatio = await page.locator('[data-testid="sharpe-ratio"]').textContent();

    return {
      winRate: parseFloat(winRate || '0'),
      totalTrades: parseInt(totalTrades || '0'),
      profitFactor: parseFloat(profitFactor || '0'),
      maxDrawdown: parseFloat(maxDrawdown || '0'),
      sharpeRatio: parseFloat(sharpeRatio || '0')
    };
  }

  /**
   * Get portfolio summary
   */
  async getPortfolioSummary(page: Page): Promise<any> {
    await page.goto('/portfolio');

    const balance = await page.locator('[data-testid="portfolio-balance"]').textContent();
    const equity = await page.locator('[data-testid="portfolio-equity"]').textContent();
    const marginUsed = await page.locator('[data-testid="margin-used"]').textContent();
    const marginAvailable = await page.locator('[data-testid="margin-available"]').textContent();
    const totalPnL = await page.locator('[data-testid="total-pnl"]').textContent();
    const dayPnL = await page.locator('[data-testid="day-pnl"]').textContent();

    return {
      balance: parseFloat(balance || '0'),
      equity: parseFloat(equity || '0'),
      marginUsed: parseFloat(marginUsed || '0'),
      marginAvailable: parseFloat(marginAvailable || '0'),
      totalPnL: parseFloat(totalPnL || '0'),
      dayPnL: parseFloat(dayPnL || '0')
    };
  }

  /**
   * Monitor real-time price updates
   */
  async monitorPriceUpdates(page: Page, symbol: string, duration: number = 10000): Promise<number[]> {
    await page.goto('/market-data');

    const prices: number[] = [];
    const startTime = Date.now();

    while (Date.now() - startTime < duration) {
      const priceText = await page.locator(`[data-testid="price-${symbol}"]`).textContent();
      const price = parseFloat(priceText || '0');

      if (price > 0) {
        prices.push(price);
      }

      await page.waitForTimeout(1000);
    }

    return prices;
  }

  /**
   * Export trading data
   */
  async exportTradingData(page: Page, format: 'csv' | 'excel' | 'pdf' = 'csv'): Promise<void> {
    await page.goto('/history');
    await page.click('[data-testid="export-data-button"]');
    await page.selectOption('[data-testid="export-format-select"]', format);
    await page.click('[data-testid="confirm-export-button"]');

    // Wait for download
    const downloadPromise = page.waitForEvent('download');
    await downloadPromise;
  }
}