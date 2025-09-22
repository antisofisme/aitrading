import { chromium, FullConfig } from '@playwright/test';
import { TestEnvironmentManager } from './utils/test-environment-manager';
import { TestDataManager } from './utils/test-data-manager';
import { DatabaseSeeder } from './utils/database-seeder';
import { AuthenticationHelper } from './utils/authentication-helper';

/**
 * Global setup for E2E tests
 * Runs once before all tests
 */
async function globalSetup(config: FullConfig) {
  console.log('🚀 Starting global E2E test setup...');

  const testEnvManager = new TestEnvironmentManager();
  const testDataManager = new TestDataManager();
  const dbSeeder = new DatabaseSeeder();
  const authHelper = new AuthenticationHelper();

  try {
    // 1. Setup test environment
    console.log('📦 Setting up test environment...');
    await testEnvManager.setupEnvironment();

    // 2. Start required services
    console.log('🔧 Starting test services...');
    await testEnvManager.startServices();

    // 3. Wait for services to be ready
    console.log('⏳ Waiting for services to be ready...');
    await testEnvManager.waitForServices();

    // 4. Setup test database
    console.log('🗄️ Setting up test database...');
    await dbSeeder.setupDatabase();

    // 5. Seed test data
    console.log('🌱 Seeding test data...');
    await testDataManager.seedTestData();

    // 6. Create test users and authentication
    console.log('👤 Creating test users...');
    await authHelper.createTestUsers();

    // 7. Generate authentication tokens
    console.log('🔐 Generating authentication tokens...');
    await authHelper.generateTestTokens();

    // 8. Setup browser context with authentication
    console.log('🌐 Setting up authenticated browser context...');
    const browser = await chromium.launch();
    const context = await browser.newContext();

    // Login and save authentication state
    const page = await context.newPage();
    await authHelper.loginAndSaveState(page, context);

    await browser.close();

    // 9. Validate test environment
    console.log('✅ Validating test environment...');
    await testEnvManager.validateEnvironment();

    console.log('✨ Global setup completed successfully!');

  } catch (error) {
    console.error('❌ Global setup failed:', error);

    // Cleanup on failure
    try {
      await testEnvManager.cleanup();
    } catch (cleanupError) {
      console.error('Failed to cleanup after setup failure:', cleanupError);
    }

    throw error;
  }
}

export default globalSetup;