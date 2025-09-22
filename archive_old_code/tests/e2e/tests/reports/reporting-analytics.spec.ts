import { test, expect } from '@playwright/test';
import { AuthenticationHelper } from '../../utils/authentication-helper';
import { TestDataManager } from '../../utils/test-data-manager';
import { TradingHelper } from '../../utils/trading-helper';
import { APIHelper } from '../../utils/api-helper';
import { ReportingHelper } from '../../utils/reporting-helper';

test.describe('Reporting and Analytics E2E Tests', () => {
  let authHelper: AuthenticationHelper;
  let testDataManager: TestDataManager;
  let tradingHelper: TradingHelper;
  let apiHelper: APIHelper;
  let reportingHelper: ReportingHelper;

  test.beforeEach(async ({ page }) => {
    authHelper = new AuthenticationHelper();
    testDataManager = new TestDataManager();
    tradingHelper = new TradingHelper();
    apiHelper = new APIHelper();
    reportingHelper = new ReportingHelper();

    await authHelper.loginAs(page, 'premium_trader');
  });

  test.describe('@e2e @smoke Report Generation', () => {
    test('should generate daily P&L report', async ({ page }) => {
      // Execute some trades to have data for reporting
      await tradingHelper.executeMultipleTrades(page, [
        { symbol: 'EURUSD', side: 'buy', quantity: 10000 },
        { symbol: 'GBPUSD', side: 'sell', quantity: 15000 },
        { symbol: 'USDJPY', side: 'buy', quantity: 8000 }
      ]);

      // Navigate to reports section
      await page.goto('/reports');
      await expect(page.locator('[data-testid="reports-dashboard"]')).toBeVisible();

      // Generate daily P&L report
      await page.click('[data-testid="generate-report-button"]');
      await page.selectOption('[data-testid="report-type-select"]', 'daily_pnl');

      // Set date range
      const today = new Date().toISOString().split('T')[0];
      await page.fill('[data-testid="date-from-input"]', today);
      await page.fill('[data-testid="date-to-input"]', today);

      // Select format
      await page.selectOption('[data-testid="report-format-select"]', 'pdf');

      // Generate report
      await page.click('[data-testid="generate-button"]');

      // Wait for report generation
      await expect(page.locator('[data-testid="report-generating"]')).toBeVisible();
      await expect(page.locator('[data-testid="report-generated-success"]')).toBeVisible({ timeout: 30000 });

      // Verify report details
      const reportId = await page.locator('[data-testid="report-id"]').textContent();
      expect(reportId).toBeTruthy();

      // Check report contains expected data
      await page.click('[data-testid="view-report-button"]');
      await expect(page.locator('[data-testid="report-viewer"]')).toBeVisible();

      // Verify report sections
      await expect(page.locator('[data-testid="report-title"]')).toContainText('Daily P&L Report');
      await expect(page.locator('[data-testid="report-date-range"]')).toContainText(today);
      await expect(page.locator('[data-testid="report-summary"]')).toBeVisible();
      await expect(page.locator('[data-testid="report-trades-table"]')).toBeVisible();

      // Verify key metrics are present
      await expect(page.locator('[data-testid="total-trades"]')).toBeVisible();
      await expect(page.locator('[data-testid="total-pnl"]')).toBeVisible();
      await expect(page.locator('[data-testid="win-rate"]')).toBeVisible();
      await expect(page.locator('[data-testid="largest-win"]')).toBeVisible();
      await expect(page.locator('[data-testid="largest-loss"]')).toBeVisible();

      // Download report
      const downloadPromise = page.waitForEvent('download');
      await page.click('[data-testid="download-report-button"]');
      const download = await downloadPromise;

      expect(download.suggestedFilename()).toMatch(/daily_pnl_report.*\.pdf$/);
    });

    test('should generate monthly performance summary', async ({ page }) => {
      await page.goto('/reports');

      await page.click('[data-testid="generate-report-button"]');
      await page.selectOption('[data-testid="report-type-select"]', 'monthly_summary');

      // Set monthly date range
      const startOfMonth = new Date(new Date().getFullYear(), new Date().getMonth(), 1);
      const endOfMonth = new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0);

      await page.fill('[data-testid="date-from-input"]', startOfMonth.toISOString().split('T')[0]);
      await page.fill('[data-testid="date-to-input"]', endOfMonth.toISOString().split('T')[0]);

      await page.selectOption('[data-testid="report-format-select"]', 'excel');
      await page.click('[data-testid="generate-button"]');

      await expect(page.locator('[data-testid="report-generated-success"]')).toBeVisible({ timeout: 45000 });

      // View the generated report
      await page.click('[data-testid="view-report-button"]');

      // Verify monthly summary components
      await expect(page.locator('[data-testid="monthly-overview"]')).toBeVisible();
      await expect(page.locator('[data-testid="performance-chart"]')).toBeVisible();
      await expect(page.locator('[data-testid="top-strategies"]')).toBeVisible();
      await expect(page.locator('[data-testid="risk-metrics"]')).toBeVisible();

      // Check specific metrics
      await expect(page.locator('[data-testid="monthly-return"]')).toBeVisible();
      await expect(page.locator('[data-testid="sharpe-ratio"]')).toBeVisible();
      await expect(page.locator('[data-testid="max-drawdown"]')).toBeVisible();
      await expect(page.locator('[data-testid="volatility"]')).toBeVisible();
    });

    test('should generate risk analysis report', async ({ page }) => {
      await page.goto('/reports');

      await page.click('[data-testid="generate-report-button"]');
      await page.selectOption('[data-testid="report-type-select"]', 'risk_analysis');

      // Set analysis period
      const oneWeekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
      const today = new Date();

      await page.fill('[data-testid="date-from-input"]', oneWeekAgo.toISOString().split('T')[0]);
      await page.fill('[data-testid="date-to-input"]', today.toISOString().split('T')[0]);

      await page.click('[data-testid="generate-button"]');
      await expect(page.locator('[data-testid="report-generated-success"]')).toBeVisible({ timeout: 30000 });

      await page.click('[data-testid="view-report-button"]');

      // Verify risk analysis components
      await expect(page.locator('[data-testid="risk-summary"]')).toBeVisible();
      await expect(page.locator('[data-testid="var-calculation"]')).toBeVisible();
      await expect(page.locator('[data-testid="position-sizes"]')).toBeVisible();
      await expect(page.locator('[data-testid="correlation-matrix"]')).toBeVisible();
      await expect(page.locator('[data-testid="stress-test-results"]')).toBeVisible();

      // Check risk metrics values
      const varValue = await page.locator('[data-testid="var-value"]').textContent();
      const maxDrawdown = await page.locator('[data-testid="max-drawdown-value"]').textContent();

      expect(varValue).toMatch(/\d+\.?\d*%?/);
      expect(maxDrawdown).toMatch(/\d+\.?\d*%?/);
    });

    test('should generate custom report with filters', async ({ page }) => {
      await page.goto('/reports');

      await page.click('[data-testid="generate-report-button"]');
      await page.selectOption('[data-testid="report-type-select"]', 'custom');

      // Configure custom report filters
      await page.click('[data-testid="advanced-filters-toggle"]');

      // Symbol filters
      await page.check('[data-testid="symbol-filter-EURUSD"]');
      await page.check('[data-testid="symbol-filter-GBPUSD"]');

      // Strategy filters
      await page.selectOption('[data-testid="strategy-type-filter"]', 'momentum');

      // Performance filters
      await page.fill('[data-testid="min-pnl-filter"]', '100');
      await page.fill('[data-testid="max-pnl-filter"]', '10000');

      // Date range
      const oneMonthAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
      await page.fill('[data-testid="date-from-input"]', oneMonthAgo.toISOString().split('T')[0]);
      await page.fill('[data-testid="date-to-input"]', new Date().toISOString().split('T')[0]);

      await page.click('[data-testid="generate-button"]');
      await expect(page.locator('[data-testid="report-generated-success"]')).toBeVisible({ timeout: 30000 });

      await page.click('[data-testid="view-report-button"]');

      // Verify filtered data
      const tradesTable = page.locator('[data-testid="filtered-trades-table"]');
      await expect(tradesTable).toBeVisible();

      // Check that only filtered symbols appear
      const symbolCells = await tradesTable.locator('td[data-column="symbol"]').allTextContents();
      const allowedSymbols = ['EURUSD', 'GBPUSD'];

      symbolCells.forEach(symbol => {
        expect(allowedSymbols).toContain(symbol);
      });
    });
  });

  test.describe('@e2e @integration Analytics Dashboard', () => {
    test('should display real-time analytics dashboard', async ({ page }) => {
      await page.goto('/analytics');

      // Verify main dashboard components
      await expect(page.locator('[data-testid="analytics-dashboard"]')).toBeVisible();
      await expect(page.locator('[data-testid="performance-overview"]')).toBeVisible();
      await expect(page.locator('[data-testid="real-time-metrics"]')).toBeVisible();

      // Check key performance indicators
      await expect(page.locator('[data-testid="total-return"]')).toBeVisible();
      await expect(page.locator('[data-testid="daily-pnl"]')).toBeVisible();
      await expect(page.locator('[data-testid="open-positions"]')).toBeVisible();
      await expect(page.locator('[data-testid="active-strategies"]')).toBeVisible();

      // Verify charts are loaded
      await expect(page.locator('[data-testid="pnl-chart"]')).toBeVisible();
      await expect(page.locator('[data-testid="performance-chart"]')).toBeVisible();
      await expect(page.locator('[data-testid="drawdown-chart"]')).toBeVisible();

      // Test interactive chart features
      await page.click('[data-testid="chart-timeframe-1d"]');
      await page.waitForTimeout(2000); // Allow chart to update

      await page.click('[data-testid="chart-timeframe-1w"]');
      await page.waitForTimeout(2000);

      await page.click('[data-testid="chart-timeframe-1m"]');
      await page.waitForTimeout(2000);

      // Verify metrics update with timeframe changes
      const metricValue = await page.locator('[data-testid="period-return"]').textContent();
      expect(metricValue).toMatch(/[+-]?\d+\.?\d*%?/);
    });

    test('should display strategy performance comparison', async ({ page }) => {
      await page.goto('/analytics/strategies');

      await expect(page.locator('[data-testid="strategy-comparison"]')).toBeVisible();

      // Check strategy list
      const strategyList = page.locator('[data-testid="strategy-list"]');
      await expect(strategyList).toBeVisible();

      // Select strategies for comparison
      await page.check('[data-testid="compare-strategy-1"]');
      await page.check('[data-testid="compare-strategy-2"]');

      await page.click('[data-testid="compare-strategies-button"]');

      // Verify comparison charts
      await expect(page.locator('[data-testid="strategy-comparison-chart"]')).toBeVisible();
      await expect(page.locator('[data-testid="performance-table"]')).toBeVisible();

      // Check comparison metrics
      await expect(page.locator('[data-testid="win-rate-comparison"]')).toBeVisible();
      await expect(page.locator('[data-testid="profit-factor-comparison"]')).toBeVisible();
      await expect(page.locator('[data-testid="drawdown-comparison"]')).toBeVisible();
    });

    test('should display portfolio allocation analytics', async ({ page }) => {
      await page.goto('/analytics/portfolio');

      // Verify portfolio analytics components
      await expect(page.locator('[data-testid="portfolio-allocation"]')).toBeVisible();
      await expect(page.locator('[data-testid="asset-distribution"]')).toBeVisible();
      await expect(page.locator('[data-testid="sector-exposure"]')).toBeVisible();

      // Check allocation charts
      await expect(page.locator('[data-testid="allocation-pie-chart"]')).toBeVisible();
      await expect(page.locator('[data-testid="exposure-bar-chart"]')).toBeVisible();

      // Test drill-down functionality
      await page.click('[data-testid="allocation-segment-forex"]');
      await expect(page.locator('[data-testid="forex-details"]')).toBeVisible();

      // Verify risk metrics
      await expect(page.locator('[data-testid="portfolio-beta"]')).toBeVisible();
      await expect(page.locator('[data-testid="portfolio-var"]')).toBeVisible();
      await expect(page.locator('[data-testid="correlation-matrix"]')).toBeVisible();
    });
  });

  test.describe('@e2e @performance Report Performance', () => {
    test('should handle large dataset reports efficiently', async ({ page }) => {
      // Generate a report with large dataset
      await page.goto('/reports');

      await page.click('[data-testid="generate-report-button"]');
      await page.selectOption('[data-testid="report-type-select"]', 'comprehensive');

      // Set large date range (6 months)
      const sixMonthsAgo = new Date(Date.now() - 180 * 24 * 60 * 60 * 1000);
      await page.fill('[data-testid="date-from-input"]', sixMonthsAgo.toISOString().split('T')[0]);
      await page.fill('[data-testid="date-to-input"]', new Date().toISOString().split('T')[0]);

      const startTime = Date.now();

      await page.click('[data-testid="generate-button"]');

      // Should show loading indicator
      await expect(page.locator('[data-testid="report-generating"]')).toBeVisible();

      // Wait for completion with reasonable timeout
      await expect(page.locator('[data-testid="report-generated-success"]')).toBeVisible({ timeout: 120000 });

      const generationTime = Date.now() - startTime;

      // Report generation should complete within reasonable time
      expect(generationTime).toBeLessThan(120000); // 2 minutes

      // Verify report can be opened quickly
      const viewStartTime = Date.now();
      await page.click('[data-testid="view-report-button"]');
      await expect(page.locator('[data-testid="report-viewer"]')).toBeVisible();

      const viewTime = Date.now() - viewStartTime;
      expect(viewTime).toBeLessThan(10000); // 10 seconds
    });

    test('should handle concurrent report generation', async ({ browser }) => {
      // Create multiple browser contexts for concurrent users
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

      // Generate reports concurrently
      const reportRequests = pages.map(async (page, index) => {
        await page.goto('/reports');
        await page.click('[data-testid="generate-report-button"]');
        await page.selectOption('[data-testid="report-type-select"]', 'daily_pnl');

        const today = new Date().toISOString().split('T')[0];
        await page.fill('[data-testid="date-from-input"]', today);
        await page.fill('[data-testid="date-to-input"]', today);

        await page.click('[data-testid="generate-button"]');

        return await page.waitForSelector('[data-testid="report-generated-success"]', { timeout: 60000 });
      });

      // All reports should generate successfully
      const results = await Promise.all(reportRequests);
      expect(results).toHaveLength(3);

      // Cleanup
      await Promise.all(contexts.map(context => context.close()));
    });
  });

  test.describe('@e2e @regression Report Export Functionality', () => {
    test('should export reports in multiple formats', async ({ page }) => {
      await page.goto('/reports');

      // Generate a base report
      await page.click('[data-testid="generate-report-button"]');
      await page.selectOption('[data-testid="report-type-select"]', 'performance_review');

      const oneWeekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
      await page.fill('[data-testid="date-from-input"]', oneWeekAgo.toISOString().split('T')[0]);
      await page.fill('[data-testid="date-to-input"]', new Date().toISOString().split('T')[0]);

      await page.click('[data-testid="generate-button"]');
      await expect(page.locator('[data-testid="report-generated-success"]')).toBeVisible({ timeout: 30000 });

      const reportId = await page.locator('[data-testid="report-id"]').textContent();

      // Test PDF export
      await page.selectOption('[data-testid="export-format-select"]', 'pdf');
      const pdfDownload = page.waitForEvent('download');
      await page.click('[data-testid="export-report-button"]');
      const pdfFile = await pdfDownload;
      expect(pdfFile.suggestedFilename()).toMatch(/.*\.pdf$/);

      // Test Excel export
      await page.selectOption('[data-testid="export-format-select"]', 'excel');
      const excelDownload = page.waitForEvent('download');
      await page.click('[data-testid="export-report-button"]');
      const excelFile = await excelDownload;
      expect(excelFile.suggestedFilename()).toMatch(/.*\.xlsx$/);

      // Test CSV export
      await page.selectOption('[data-testid="export-format-select"]', 'csv');
      const csvDownload = page.waitForEvent('download');
      await page.click('[data-testid="export-report-button"]');
      const csvFile = await csvDownload;
      expect(csvFile.suggestedFilename()).toMatch(/.*\.csv$/);
    });

    test('should handle scheduled report generation', async ({ page }) => {
      await page.goto('/reports/scheduled');

      // Create a scheduled report
      await page.click('[data-testid="create-scheduled-report-button"]');

      await page.fill('[data-testid="schedule-name-input"]', 'Daily Performance Report');
      await page.selectOption('[data-testid="report-type-select"]', 'daily_pnl');
      await page.selectOption('[data-testid="schedule-frequency-select"]', 'daily');
      await page.fill('[data-testid="schedule-time-input"]', '09:00');

      // Set recipients
      await page.fill('[data-testid="email-recipients-input"]', 'trader@test.com, manager@test.com');

      await page.click('[data-testid="save-schedule-button"]');
      await expect(page.locator('[data-testid="schedule-created-success"]')).toBeVisible();

      // Verify scheduled report appears in list
      await expect(page.locator('[data-testid="scheduled-reports-list"]')).toBeVisible();
      await expect(page.locator('[data-testid="schedule-Daily Performance Report"]')).toBeVisible();

      // Test schedule modification
      await page.click('[data-testid="edit-schedule-Daily Performance Report"]');
      await page.selectOption('[data-testid="schedule-frequency-select"]', 'weekly');
      await page.click('[data-testid="save-schedule-button"]');

      await expect(page.locator('[data-testid="schedule-updated-success"]')).toBeVisible();
    });
  });

  test.describe('@e2e @compliance Compliance and Audit Reports', () => {
    test('should generate compliance audit report', async ({ page }) => {
      // Switch to admin user for compliance features
      await authHelper.logout(page);
      await authHelper.loginAs(page, 'admin');

      await page.goto('/reports/compliance');

      await page.click('[data-testid="generate-compliance-report-button"]');
      await page.selectOption('[data-testid="compliance-type-select"]', 'audit_trail');

      // Set audit period
      const oneMonthAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
      await page.fill('[data-testid="audit-date-from-input"]', oneMonthAgo.toISOString().split('T')[0]);
      await page.fill('[data-testid="audit-date-to-input"]', new Date().toISOString().split('T')[0]);

      // Select audit categories
      await page.check('[data-testid="audit-category-user-actions"]');
      await page.check('[data-testid="audit-category-trading-activities"]');
      await page.check('[data-testid="audit-category-system-changes"]');

      await page.click('[data-testid="generate-audit-report-button"]');
      await expect(page.locator('[data-testid="audit-report-generated"]')).toBeVisible({ timeout: 45000 });

      // Verify audit report content
      await page.click('[data-testid="view-audit-report-button"]');

      await expect(page.locator('[data-testid="audit-summary"]')).toBeVisible();
      await expect(page.locator('[data-testid="audit-events-table"]')).toBeVisible();
      await expect(page.locator('[data-testid="user-activity-chart"]')).toBeVisible();
      await expect(page.locator('[data-testid="risk-violations"]')).toBeVisible();

      // Check audit trail details
      const auditEvents = await page.locator('[data-testid="audit-event"]').count();
      expect(auditEvents).toBeGreaterThan(0);
    });

    test('should generate regulatory compliance report', async ({ page }) => {
      await authHelper.loginAs(page, 'admin');
      await page.goto('/reports/compliance');

      await page.click('[data-testid="generate-compliance-report-button"]');
      await page.selectOption('[data-testid="compliance-type-select"]', 'regulatory');

      // Select regulatory framework
      await page.selectOption('[data-testid="regulatory-framework-select"]', 'MiFID_II');

      // Set reporting period
      const quarterStart = new Date(new Date().getFullYear(), Math.floor(new Date().getMonth() / 3) * 3, 1);
      const quarterEnd = new Date(quarterStart.getFullYear(), quarterStart.getMonth() + 3, 0);

      await page.fill('[data-testid="reporting-date-from-input"]', quarterStart.toISOString().split('T')[0]);
      await page.fill('[data-testid="reporting-date-to-input"]', quarterEnd.toISOString().split('T')[0]);

      await page.click('[data-testid="generate-regulatory-report-button"]');
      await expect(page.locator('[data-testid="regulatory-report-generated"]')).toBeVisible({ timeout: 60000 });

      // Verify regulatory report sections
      await page.click('[data-testid="view-regulatory-report-button"]');

      await expect(page.locator('[data-testid="regulatory-summary"]')).toBeVisible();
      await expect(page.locator('[data-testid="transaction-reporting"]')).toBeVisible();
      await expect(page.locator('[data-testid="best-execution-analysis"]')).toBeVisible();
      await expect(page.locator('[data-testid="client-reporting"]')).toBeVisible();
      await expect(page.locator('[data-testid="compliance-metrics"]')).toBeVisible();
    });
  });

  test.describe('@e2e @api Report API Integration', () => {
    test('should generate reports via API', async ({ page }) => {
      await apiHelper.authenticate('premium_trader');

      // Generate report via API
      const reportRequest = {
        type: 'daily_pnl',
        dateFrom: new Date().toISOString().split('T')[0],
        dateTo: new Date().toISOString().split('T')[0],
        format: 'pdf',
        filters: {
          symbols: ['EURUSD', 'GBPUSD'],
          minPnL: 0
        }
      };

      const reportResponse = await apiHelper.generateReport(reportRequest);
      expect(reportResponse.status).toBe(201);

      const reportId = reportResponse.data.reportId;
      expect(reportId).toBeTruthy();

      // Poll for report completion
      let reportStatus = 'generating';
      let attempts = 0;
      const maxAttempts = 30;

      while (reportStatus === 'generating' && attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 2000));

        const statusResponse = await apiHelper.getReport(reportId);
        reportStatus = statusResponse.data.status;
        attempts++;
      }

      expect(reportStatus).toBe('completed');

      // Download report
      const downloadResponse = await apiHelper.downloadReport(reportId);
      expect(downloadResponse.status).toBe(200);
      expect(downloadResponse.headers['content-type']).toContain('application/pdf');
    });

    test('should validate report API error handling', async ({ page }) => {
      await apiHelper.authenticate('trader');

      // Test with invalid date range
      const invalidRequest = {
        type: 'daily_pnl',
        dateFrom: '2024-12-31',
        dateTo: '2024-01-01', // End date before start date
        format: 'pdf'
      };

      try {
        await apiHelper.generateReport(invalidRequest);
        expect(false).toBe(true); // Should not reach here
      } catch (error) {
        expect(error.response.status).toBe(400);
        expect(error.response.data.error).toContain('Invalid date range');
      }

      // Test with unauthorized report type
      const unauthorizedRequest = {
        type: 'compliance_audit', // Requires admin role
        dateFrom: new Date().toISOString().split('T')[0],
        dateTo: new Date().toISOString().split('T')[0],
        format: 'pdf'
      };

      try {
        await apiHelper.generateReport(unauthorizedRequest);
        expect(false).toBe(true); // Should not reach here
      } catch (error) {
        expect(error.response.status).toBe(403);
        expect(error.response.data.error).toContain('Insufficient permissions');
      }
    });
  });
});