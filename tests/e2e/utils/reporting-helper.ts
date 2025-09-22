import { Page } from '@playwright/test';
import * as fs from 'fs/promises';
import * as path from 'path';

export interface ReportConfig {
  type: string;
  dateFrom: string;
  dateTo: string;
  format?: 'pdf' | 'excel' | 'csv' | 'json';
  filters?: any;
  recipients?: string[];
}

export interface ScheduleConfig {
  name: string;
  reportType: string;
  frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly';
  time: string;
  recipients: string[];
  enabled?: boolean;
}

/**
 * Helper class for reporting and analytics operations in E2E tests
 */
export class ReportingHelper {
  private reportsDir = path.join(__dirname, '../data/reports');

  constructor() {
    this.ensureReportsDirectory();
  }

  /**
   * Ensure reports directory exists
   */
  private async ensureReportsDirectory(): Promise<void> {
    try {
      await fs.mkdir(this.reportsDir, { recursive: true });
    } catch (error) {
      // Directory might already exist
    }
  }

  /**
   * Generate a report through the UI
   */
  async generateReport(page: Page, config: ReportConfig): Promise<string> {
    await page.goto('/reports');

    await page.click('[data-testid="generate-report-button"]');
    await page.selectOption('[data-testid="report-type-select"]', config.type);

    // Set date range
    await page.fill('[data-testid="date-from-input"]', config.dateFrom);
    await page.fill('[data-testid="date-to-input"]', config.dateTo);

    // Set format if specified
    if (config.format) {
      await page.selectOption('[data-testid="report-format-select"]', config.format);
    }

    // Apply filters if specified
    if (config.filters) {
      await this.applyReportFilters(page, config.filters);
    }

    // Generate report
    await page.click('[data-testid="generate-button"]');

    // Wait for generation to complete
    await page.waitForSelector('[data-testid="report-generated-success"]', { timeout: 60000 });

    // Get report ID
    const reportId = await page.locator('[data-testid="report-id"]').textContent();
    return reportId || '';
  }

  /**
   * Apply filters to a report
   */
  private async applyReportFilters(page: Page, filters: any): Promise<void> {
    if (!filters) return;

    // Expand advanced filters if needed
    if (await page.locator('[data-testid="advanced-filters-toggle"]').isVisible()) {
      await page.click('[data-testid="advanced-filters-toggle"]');
    }

    // Symbol filters
    if (filters.symbols) {
      for (const symbol of filters.symbols) {
        await page.check(`[data-testid="symbol-filter-${symbol}"]`);
      }
    }

    // Strategy filters
    if (filters.strategyType) {
      await page.selectOption('[data-testid="strategy-type-filter"]', filters.strategyType);
    }

    // P&L filters
    if (filters.minPnL !== undefined) {
      await page.fill('[data-testid="min-pnl-filter"]', filters.minPnL.toString());
    }

    if (filters.maxPnL !== undefined) {
      await page.fill('[data-testid="max-pnl-filter"]', filters.maxPnL.toString());
    }

    // User filters (for admin reports)
    if (filters.userIds) {
      for (const userId of filters.userIds) {
        await page.check(`[data-testid="user-filter-${userId}"]`);
      }
    }

    // Risk level filters
    if (filters.riskLevels) {
      for (const riskLevel of filters.riskLevels) {
        await page.check(`[data-testid="risk-level-filter-${riskLevel}"]`);
      }
    }
  }

  /**
   * View a generated report
   */
  async viewReport(page: Page, reportId: string): Promise<void> {
    await page.goto('/reports');

    // Find the report in the list
    await page.click(`[data-testid="view-report-${reportId}"]`);

    // Wait for report viewer to load
    await page.waitForSelector('[data-testid="report-viewer"]');
  }

  /**
   * Download a report
   */
  async downloadReport(page: Page, reportId: string, expectedFormat: string = 'pdf'): Promise<string> {
    await page.goto('/reports');

    // Find and click download button
    const downloadPromise = page.waitForEvent('download');
    await page.click(`[data-testid="download-report-${reportId}"]`);

    const download = await downloadPromise;
    const filename = download.suggestedFilename();

    // Save to reports directory
    const filePath = path.join(this.reportsDir, filename);
    await download.saveAs(filePath);

    return filePath;
  }

  /**
   * Create a scheduled report
   */
  async createScheduledReport(page: Page, config: ScheduleConfig): Promise<string> {
    await page.goto('/reports/scheduled');

    await page.click('[data-testid="create-scheduled-report-button"]');

    // Fill schedule configuration
    await page.fill('[data-testid="schedule-name-input"]', config.name);
    await page.selectOption('[data-testid="report-type-select"]', config.reportType);
    await page.selectOption('[data-testid="schedule-frequency-select"]', config.frequency);
    await page.fill('[data-testid="schedule-time-input"]', config.time);

    // Set recipients
    await page.fill('[data-testid="email-recipients-input"]', config.recipients.join(', '));

    // Set enabled status
    if (config.enabled === false) {
      await page.uncheck('[data-testid="schedule-enabled-checkbox"]');
    }

    await page.click('[data-testid="save-schedule-button"]');

    // Wait for confirmation
    await page.waitForSelector('[data-testid="schedule-created-success"]');

    // Get schedule ID
    const scheduleId = await page.locator('[data-testid="schedule-id"]').textContent();
    return scheduleId || '';
  }

  /**
   * Get analytics data from dashboard
   */
  async getAnalyticsData(page: Page): Promise<any> {
    await page.goto('/analytics');

    // Wait for analytics to load
    await page.waitForSelector('[data-testid="analytics-dashboard"]');

    // Extract key metrics
    const data = {
      totalReturn: await page.locator('[data-testid="total-return"]').textContent(),
      dailyPnL: await page.locator('[data-testid="daily-pnl"]').textContent(),
      openPositions: await page.locator('[data-testid="open-positions"]').textContent(),
      activeStrategies: await page.locator('[data-testid="active-strategies"]').textContent(),
      winRate: await page.locator('[data-testid="win-rate"]').textContent(),
      sharpeRatio: await page.locator('[data-testid="sharpe-ratio"]').textContent(),
      maxDrawdown: await page.locator('[data-testid="max-drawdown"]').textContent(),
      volatility: await page.locator('[data-testid="volatility"]').textContent()
    };

    return data;
  }

  /**
   * Get strategy comparison data
   */
  async getStrategyComparison(page: Page, strategyIds: string[]): Promise<any> {
    await page.goto('/analytics/strategies');

    // Select strategies for comparison
    for (const strategyId of strategyIds) {
      await page.check(`[data-testid="compare-strategy-${strategyId}"]`);
    }

    await page.click('[data-testid="compare-strategies-button"]');

    // Wait for comparison to load
    await page.waitForSelector('[data-testid="strategy-comparison-chart"]');

    // Extract comparison data
    const comparisonData = [];

    for (const strategyId of strategyIds) {
      const strategyData = {
        id: strategyId,
        winRate: await page.locator(`[data-testid="win-rate-${strategyId}"]`).textContent(),
        profitFactor: await page.locator(`[data-testid="profit-factor-${strategyId}"]`).textContent(),
        maxDrawdown: await page.locator(`[data-testid="max-drawdown-${strategyId}"]`).textContent(),
        totalTrades: await page.locator(`[data-testid="total-trades-${strategyId}"]`).textContent(),
        avgProfit: await page.locator(`[data-testid="avg-profit-${strategyId}"]`).textContent()
      };

      comparisonData.push(strategyData);
    }

    return comparisonData;
  }

  /**
   * Get portfolio allocation data
   */
  async getPortfolioAllocation(page: Page): Promise<any> {
    await page.goto('/analytics/portfolio');

    await page.waitForSelector('[data-testid="portfolio-allocation"]');

    // Extract allocation data
    const allocation = {
      assetDistribution: {},
      sectorExposure: {},
      riskMetrics: {
        beta: await page.locator('[data-testid="portfolio-beta"]').textContent(),
        var: await page.locator('[data-testid="portfolio-var"]').textContent(),
        volatility: await page.locator('[data-testid="portfolio-volatility"]').textContent()
      }
    };

    // Get asset distribution
    const assetElements = await page.locator('[data-testid^="asset-percentage-"]').all();
    for (const element of assetElements) {
      const testId = await element.getAttribute('data-testid');
      const asset = testId?.replace('asset-percentage-', '') || '';
      const percentage = await element.textContent();
      allocation.assetDistribution[asset] = percentage;
    }

    // Get sector exposure
    const sectorElements = await page.locator('[data-testid^="sector-exposure-"]').all();
    for (const element of sectorElements) {
      const testId = await element.getAttribute('data-testid');
      const sector = testId?.replace('sector-exposure-', '') || '';
      const exposure = await element.textContent();
      allocation.sectorExposure[sector] = exposure;
    }

    return allocation;
  }

  /**
   * Validate report content structure
   */
  async validateReportContent(page: Page, reportType: string): Promise<boolean> {
    const requiredSections = this.getRequiredSections(reportType);

    for (const section of requiredSections) {
      const sectionElement = page.locator(`[data-testid="${section}"]`);
      if (!(await sectionElement.isVisible())) {
        console.error(`Required section ${section} not found in ${reportType} report`);
        return false;
      }
    }

    return true;
  }

  /**
   * Get required sections for different report types
   */
  private getRequiredSections(reportType: string): string[] {
    const sectionMap: Record<string, string[]> = {
      'daily_pnl': [
        'report-title',
        'report-date-range',
        'report-summary',
        'total-trades',
        'total-pnl',
        'win-rate',
        'largest-win',
        'largest-loss'
      ],
      'monthly_summary': [
        'monthly-overview',
        'performance-chart',
        'top-strategies',
        'risk-metrics',
        'monthly-return',
        'sharpe-ratio',
        'max-drawdown',
        'volatility'
      ],
      'risk_analysis': [
        'risk-summary',
        'var-calculation',
        'position-sizes',
        'correlation-matrix',
        'stress-test-results'
      ],
      'performance_review': [
        'performance-summary',
        'strategy-breakdown',
        'profit-analysis',
        'risk-assessment',
        'recommendations'
      ]
    };

    return sectionMap[reportType] || [];
  }

  /**
   * Export analytics data to file
   */
  async exportAnalyticsData(page: Page, format: 'csv' | 'excel' | 'json' = 'csv'): Promise<string> {
    await page.goto('/analytics');

    await page.click('[data-testid="export-analytics-button"]');
    await page.selectOption('[data-testid="export-format-select"]', format);

    const downloadPromise = page.waitForEvent('download');
    await page.click('[data-testid="confirm-export-button"]');

    const download = await downloadPromise;
    const filename = download.suggestedFilename();
    const filePath = path.join(this.reportsDir, filename);

    await download.saveAs(filePath);
    return filePath;
  }

  /**
   * Schedule bulk report generation
   */
  async scheduleBulkReports(page: Page, configs: ScheduleConfig[]): Promise<string[]> {
    const scheduleIds = [];

    for (const config of configs) {
      const scheduleId = await this.createScheduledReport(page, config);
      scheduleIds.push(scheduleId);

      // Small delay between creations
      await page.waitForTimeout(1000);
    }

    return scheduleIds;
  }

  /**
   * Get report generation history
   */
  async getReportHistory(page: Page): Promise<any[]> {
    await page.goto('/reports/history');

    await page.waitForSelector('[data-testid="report-history-table"]');

    const reports = [];
    const reportRows = await page.locator('[data-testid^="report-row-"]').all();

    for (const row of reportRows) {
      const reportData = {
        id: await row.locator('[data-column="id"]').textContent(),
        type: await row.locator('[data-column="type"]').textContent(),
        status: await row.locator('[data-column="status"]').textContent(),
        createdAt: await row.locator('[data-column="created-at"]').textContent(),
        generatedAt: await row.locator('[data-column="generated-at"]').textContent(),
        size: await row.locator('[data-column="size"]').textContent()
      };

      reports.push(reportData);
    }

    return reports;
  }

  /**
   * Monitor real-time analytics updates
   */
  async monitorAnalyticsUpdates(page: Page, duration: number = 30000): Promise<any[]> {
    await page.goto('/analytics');

    const updates = [];
    const startTime = Date.now();

    while (Date.now() - startTime < duration) {
      try {
        const currentData = await this.getAnalyticsData(page);
        updates.push({
          timestamp: new Date().toISOString(),
          data: currentData
        });

        await page.waitForTimeout(5000); // Check every 5 seconds
      } catch (error) {
        console.warn('Error monitoring analytics updates:', error);
        break;
      }
    }

    return updates;
  }

  /**
   * Validate chart data accuracy
   */
  async validateChartData(page: Page, chartSelector: string): Promise<boolean> {
    const chart = page.locator(chartSelector);

    if (!(await chart.isVisible())) {
      return false;
    }

    // Check if chart has data points
    const dataPoints = await chart.locator('.chart-data-point').count();
    if (dataPoints === 0) {
      return false;
    }

    // Verify chart axes are labeled
    const xAxis = await chart.locator('.x-axis').isVisible();
    const yAxis = await chart.locator('.y-axis').isVisible();

    return xAxis && yAxis;
  }

  /**
   * Clean up test reports
   */
  async cleanup(): Promise<void> {
    try {
      const files = await fs.readdir(this.reportsDir);

      for (const file of files) {
        const filePath = path.join(this.reportsDir, file);
        await fs.unlink(filePath);
      }
    } catch (error) {
      console.warn('Failed to cleanup test reports:', error);
    }
  }
}