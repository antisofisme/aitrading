import { FullConfig } from '@playwright/test';
import { TestEnvironmentManager } from './utils/test-environment-manager';
import { TestDataManager } from './utils/test-data-manager';
import { DatabaseSeeder } from './utils/database-seeder';
import { ReportGenerator } from './utils/report-generator';

/**
 * Global teardown for E2E tests
 * Runs once after all tests complete
 */
async function globalTeardown(config: FullConfig) {
  console.log('🧹 Starting global E2E test teardown...');

  const testEnvManager = new TestEnvironmentManager();
  const testDataManager = new TestDataManager();
  const dbSeeder = new DatabaseSeeder();
  const reportGenerator = new ReportGenerator();

  try {
    // 1. Generate final test reports
    console.log('📊 Generating test reports...');
    await reportGenerator.generateFinalReport();

    // 2. Cleanup test data
    console.log('🗑️ Cleaning up test data...');
    await testDataManager.cleanupTestData();

    // 3. Reset database
    console.log('🔄 Resetting test database...');
    await dbSeeder.resetDatabase();

    // 4. Archive test results
    console.log('📋 Archiving test results...');
    await reportGenerator.archiveResults();

    // 5. Stop test services
    console.log('🛑 Stopping test services...');
    await testEnvManager.stopServices();

    // 6. Cleanup test environment
    console.log('🧼 Cleaning up test environment...');
    await testEnvManager.cleanup();

    // 7. Export metrics
    console.log('📈 Exporting test metrics...');
    await reportGenerator.exportMetrics();

    console.log('✨ Global teardown completed successfully!');

  } catch (error) {
    console.error('❌ Global teardown failed:', error);

    // Force cleanup on failure
    try {
      await testEnvManager.forceCleanup();
    } catch (forceCleanupError) {
      console.error('Failed to force cleanup:', forceCleanupError);
    }

    // Don't throw to avoid masking original test failures
    console.error('Teardown completed with errors');
  }
}

export default globalTeardown;