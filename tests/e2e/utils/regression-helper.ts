import { Page } from '@playwright/test';
import * as fs from 'fs/promises';
import * as path from 'path';

/**
 * Helper class for regression testing functionality
 */
export class RegressionHelper {
  private baselineDir = path.join(__dirname, '../data/baselines');
  private screenshotDir = path.join(__dirname, '../data/screenshots');
  private reportDir = path.join(__dirname, '../reports/regression');

  constructor() {
    this.ensureDirectories();
  }

  /**
   * Ensure required directories exist
   */
  private async ensureDirectories(): Promise<void> {
    const directories = [this.baselineDir, this.screenshotDir, this.reportDir];

    for (const dir of directories) {
      try {
        await fs.mkdir(dir, { recursive: true });
      } catch (error) {
        // Directory might already exist
      }
    }
  }

  /**
   * Get baseline data for comparison
   */
  getBaselineData(testName: string): any {
    try {
      const baselinePath = path.join(this.baselineDir, `${testName}.json`);
      const data = require(baselinePath);
      return data;
    } catch (error) {
      console.warn(`No baseline found for ${testName}, creating new baseline`);
      return null;
    }
  }

  /**
   * Update baseline data
   */
  async updateBaseline(testName: string, data: any): Promise<void> {
    const baselinePath = path.join(this.baselineDir, `${testName}.json`);

    const baselineData = {
      ...data,
      lastUpdated: new Date().toISOString(),
      version: await this.getApplicationVersion()
    };

    await fs.writeFile(baselinePath, JSON.stringify(baselineData, null, 2));
  }

  /**
   * Compare with baseline data
   */
  async compareWithBaseline(testName: string, currentData: any): Promise<{
    match: boolean;
    differences: any[];
    baseline: any;
    current: any;
  }> {
    const baseline = this.getBaselineData(testName);

    if (!baseline) {
      await this.updateBaseline(testName, currentData);
      return {
        match: true,
        differences: [],
        baseline: null,
        current: currentData
      };
    }

    const differences = this.findDifferences(baseline, currentData);

    return {
      match: differences.length === 0,
      differences,
      baseline,
      current: currentData
    };
  }

  /**
   * Find differences between two objects
   */
  private findDifferences(baseline: any, current: any, path: string = ''): any[] {
    const differences = [];

    // Handle different types
    if (typeof baseline !== typeof current) {
      differences.push({
        path,
        type: 'type_mismatch',
        baseline: typeof baseline,
        current: typeof current
      });
      return differences;
    }

    // Handle primitive values
    if (typeof baseline !== 'object' || baseline === null) {
      if (baseline !== current) {
        differences.push({
          path,
          type: 'value_change',
          baseline,
          current
        });
      }
      return differences;
    }

    // Handle arrays
    if (Array.isArray(baseline)) {
      if (!Array.isArray(current)) {
        differences.push({
          path,
          type: 'type_mismatch',
          baseline: 'array',
          current: typeof current
        });
        return differences;
      }

      if (baseline.length !== current.length) {
        differences.push({
          path,
          type: 'array_length_change',
          baseline: baseline.length,
          current: current.length
        });
      }

      const minLength = Math.min(baseline.length, current.length);
      for (let i = 0; i < minLength; i++) {
        differences.push(...this.findDifferences(baseline[i], current[i], `${path}[${i}]`));
      }

      return differences;
    }

    // Handle objects
    const baselineKeys = Object.keys(baseline);
    const currentKeys = Object.keys(current);

    // Check for added keys
    const addedKeys = currentKeys.filter(key => !baselineKeys.includes(key));
    addedKeys.forEach(key => {
      differences.push({
        path: `${path}.${key}`,
        type: 'key_added',
        current: current[key]
      });
    });

    // Check for removed keys
    const removedKeys = baselineKeys.filter(key => !currentKeys.includes(key));
    removedKeys.forEach(key => {
      differences.push({
        path: `${path}.${key}`,
        type: 'key_removed',
        baseline: baseline[key]
      });
    });

    // Check for changed values
    const commonKeys = baselineKeys.filter(key => currentKeys.includes(key));
    commonKeys.forEach(key => {
      differences.push(...this.findDifferences(baseline[key], current[key], `${path}.${key}`));
    });

    return differences;
  }

  /**
   * Compare screenshot with baseline
   */
  async compareScreenshot(pageName: string, screenshot: Buffer): Promise<{
    match: boolean;
    difference?: number;
    baselinePath?: string;
    currentPath?: string;
    diffPath?: string;
  }> {
    const baselinePath = path.join(this.screenshotDir, 'baselines', `${pageName}.png`);
    const currentPath = path.join(this.screenshotDir, 'current', `${pageName}.png`);
    const diffPath = path.join(this.screenshotDir, 'diffs', `${pageName}.png`);

    // Ensure directories exist
    await fs.mkdir(path.dirname(baselinePath), { recursive: true });
    await fs.mkdir(path.dirname(currentPath), { recursive: true });
    await fs.mkdir(path.dirname(diffPath), { recursive: true });

    // Save current screenshot
    await fs.writeFile(currentPath, screenshot);

    try {
      // Check if baseline exists
      await fs.access(baselinePath);

      // Compare with baseline (simplified comparison)
      const baselineBuffer = await fs.readFile(baselinePath);
      const match = Buffer.compare(baselineBuffer, screenshot) === 0;

      if (!match) {
        // Generate diff image (this would typically use an image comparison library)
        await this.generateDiffImage(baselinePath, currentPath, diffPath);
      }

      return {
        match,
        difference: match ? 0 : await this.calculateImageDifference(baselinePath, currentPath),
        baselinePath,
        currentPath,
        diffPath: match ? undefined : diffPath
      };

    } catch (error) {
      // No baseline exists, create it
      await fs.writeFile(baselinePath, screenshot);

      return {
        match: true,
        baselinePath,
        currentPath
      };
    }
  }

  /**
   * Generate diff image between two screenshots
   */
  private async generateDiffImage(baseline: string, current: string, diff: string): Promise<void> {
    // This is a placeholder implementation
    // In a real implementation, you would use an image comparison library like pixelmatch

    try {
      const baselineBuffer = await fs.readFile(baseline);
      const currentBuffer = await fs.readFile(current);

      // Simple diff - just copy the current image as diff
      // In reality, you'd generate a proper diff highlighting differences
      await fs.writeFile(diff, currentBuffer);
    } catch (error) {
      console.warn('Failed to generate diff image:', error);
    }
  }

  /**
   * Calculate percentage difference between two images
   */
  private async calculateImageDifference(baseline: string, current: string): Promise<number> {
    // Placeholder implementation
    // In reality, you'd use an image comparison library to calculate actual differences

    try {
      const baselineBuffer = await fs.readFile(baseline);
      const currentBuffer = await fs.readFile(current);

      // Simple comparison based on file size difference
      const sizeDiff = Math.abs(baselineBuffer.length - currentBuffer.length);
      const maxSize = Math.max(baselineBuffer.length, currentBuffer.length);

      return (sizeDiff / maxSize) * 100;
    } catch (error) {
      return 100; // Assume 100% different if comparison fails
    }
  }

  /**
   * Measure update frequency for real-time data
   */
  async measureUpdateFrequency(page: Page, symbol: string, duration: number): Promise<number> {
    let updateCount = 0;
    let lastValue = '';

    const startTime = Date.now();

    while (Date.now() - startTime < duration) {
      try {
        const currentValue = await page.locator(`[data-testid="price-${symbol}"]`).textContent();

        if (currentValue && currentValue !== lastValue) {
          updateCount++;
          lastValue = currentValue;
        }

        await page.waitForTimeout(1000); // Check every second
      } catch (error) {
        // Element might not be visible, continue monitoring
        await page.waitForTimeout(1000);
      }
    }

    return updateCount;
  }

  /**
   * Run accessibility check on page
   */
  async runAccessibilityCheck(page: Page): Promise<{
    score: number;
    violations: any[];
    passes: any[];
  }> {
    // This would typically use axe-core or similar accessibility testing library
    // Placeholder implementation

    try {
      // Inject axe-core if available
      await page.addScriptTag({
        url: 'https://unpkg.com/axe-core@4.4.3/axe.min.js'
      });

      const results = await page.evaluate(() => {
        // @ts-ignore
        if (typeof axe !== 'undefined') {
          // @ts-ignore
          return axe.run();
        }

        // Fallback basic checks
        return {
          violations: [],
          passes: [],
          inapplicable: [],
          incomplete: []
        };
      });

      // Calculate score based on violations
      const totalChecks = results.violations.length + results.passes.length;
      const score = totalChecks > 0 ? (results.passes.length / totalChecks) * 100 : 100;

      return {
        score,
        violations: results.violations,
        passes: results.passes
      };

    } catch (error) {
      console.warn('Accessibility check failed:', error);

      return {
        score: 0,
        violations: [],
        passes: []
      };
    }
  }

  /**
   * Generate regression test report
   */
  async generateRegressionReport(testResults: any[]): Promise<string> {
    const reportPath = path.join(this.reportDir, `regression-report-${Date.now()}.html`);

    const html = `
<!DOCTYPE html>
<html>
<head>
    <title>Regression Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background: #f5f5f5; padding: 20px; border-radius: 5px; }
        .summary { margin: 20px 0; }
        .test-result { margin: 10px 0; padding: 15px; border-radius: 5px; }
        .pass { background: #d4edda; border: 1px solid #c3e6cb; }
        .fail { background: #f8d7da; border: 1px solid #f5c6cb; }
        .differences { margin: 10px 0; font-family: monospace; }
        .screenshot { margin: 10px; }
        .screenshot img { max-width: 300px; border: 1px solid #ddd; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Regression Test Report</h1>
        <p>Generated: ${new Date().toISOString()}</p>
        <p>Application Version: ${await this.getApplicationVersion()}</p>
    </div>

    <div class="summary">
        <h2>Summary</h2>
        <p>Total Tests: ${testResults.length}</p>
        <p>Passed: ${testResults.filter(r => r.success).length}</p>
        <p>Failed: ${testResults.filter(r => !r.success).length}</p>
    </div>

    <div class="results">
        <h2>Test Results</h2>
        ${testResults.map(result => `
            <div class="test-result ${result.success ? 'pass' : 'fail'}">
                <h3>${result.name}</h3>
                <p>Status: ${result.success ? 'PASS' : 'FAIL'}</p>
                ${result.error ? `<p>Error: ${result.error}</p>` : ''}
                ${result.differences ? `
                    <div class="differences">
                        <h4>Differences:</h4>
                        <pre>${JSON.stringify(result.differences, null, 2)}</pre>
                    </div>
                ` : ''}
                ${result.screenshots ? `
                    <div class="screenshot">
                        <h4>Screenshots:</h4>
                        ${result.screenshots.map((img: any) => `
                            <div>
                                <p>${img.name}</p>
                                <img src="${img.path}" alt="${img.name}" />
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `).join('')}
    </div>
</body>
</html>
    `;

    await fs.writeFile(reportPath, html);
    return reportPath;
  }

  /**
   * Get application version
   */
  private async getApplicationVersion(): Promise<string> {
    try {
      const packagePath = path.join(__dirname, '../../../package.json');
      const packageJson = JSON.parse(await fs.readFile(packagePath, 'utf8'));
      return packageJson.version || '1.0.0';
    } catch (error) {
      return '1.0.0';
    }
  }

  /**
   * Archive old regression data
   */
  async archiveOldData(retentionDays: number = 30): Promise<void> {
    const archiveDir = path.join(this.reportDir, 'archive');
    await fs.mkdir(archiveDir, { recursive: true });

    const cutoffDate = new Date(Date.now() - (retentionDays * 24 * 60 * 60 * 1000));

    try {
      const files = await fs.readdir(this.reportDir);

      for (const file of files) {
        if (file === 'archive') continue;

        const filePath = path.join(this.reportDir, file);
        const stats = await fs.stat(filePath);

        if (stats.mtime < cutoffDate) {
          const archivePath = path.join(archiveDir, file);
          await fs.rename(filePath, archivePath);
        }
      }
    } catch (error) {
      console.warn('Failed to archive old data:', error);
    }
  }

  /**
   * Clean up temporary files
   */
  async cleanup(): Promise<void> {
    try {
      // Clean up old screenshots
      const currentDir = path.join(this.screenshotDir, 'current');
      const diffDir = path.join(this.screenshotDir, 'diffs');

      for (const dir of [currentDir, diffDir]) {
        try {
          const files = await fs.readdir(dir);
          for (const file of files) {
            await fs.unlink(path.join(dir, file));
          }
        } catch (error) {
          // Directory might not exist
        }
      }
    } catch (error) {
      console.warn('Cleanup failed:', error);
    }
  }
}