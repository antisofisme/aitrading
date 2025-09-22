import { defineConfig, devices } from '@playwright/test';
import * as path from 'path';

/**
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './tests',
  /* Run tests in files in parallel */
  fullyParallel: true,
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,
  /* Opt out of parallel tests on CI. */
  workers: process.env.CI ? 1 : 4,
  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: [
    ['html', { outputFolder: 'reports/html' }],
    ['json', { outputFile: 'reports/test-results.json' }],
    ['junit', { outputFile: 'reports/junit.xml' }],
    ['allure-playwright', { outputFolder: 'reports/allure-results' }],
    ['line'],
    ['github'] // GitHub Actions integration
  ],
  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: process.env.BASE_URL || 'http://localhost:3000',

    /* Collect trace when retrying the failed test. See https://playwright.dev/docs/trace-viewer */
    trace: 'on-first-retry',

    /* Record video on failure */
    video: 'retain-on-failure',

    /* Take screenshot on failure */
    screenshot: 'only-on-failure',

    /* Navigation timeout */
    navigationTimeout: 30000,

    /* Action timeout */
    actionTimeout: 15000,

    /* Expect timeout */
    expect: {
      timeout: 10000
    },

    /* Global test timeout */
    testTimeout: 60000,

    /* Ignore HTTPS errors during testing */
    ignoreHTTPSErrors: true,

    /* Extra HTTP headers */
    extraHTTPHeaders: {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    }
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'setup',
      testMatch: /.*\.setup\.ts/,
      teardown: 'cleanup'
    },
    {
      name: 'cleanup',
      testMatch: /.*\.teardown\.ts/
    },

    /* Desktop Browsers */
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        channel: 'chrome',
        viewport: { width: 1920, height: 1080 }
      },
      dependencies: ['setup']
    },
    {
      name: 'firefox',
      use: {
        ...devices['Desktop Firefox'],
        viewport: { width: 1920, height: 1080 }
      },
      dependencies: ['setup']
    },
    {
      name: 'webkit',
      use: {
        ...devices['Desktop Safari'],
        viewport: { width: 1920, height: 1080 }
      },
      dependencies: ['setup']
    },

    /* Mobile Testing */
    {
      name: 'mobile-chrome',
      use: {
        ...devices['Pixel 5'],
        hasTouch: true
      },
      dependencies: ['setup']
    },
    {
      name: 'mobile-safari',
      use: {
        ...devices['iPhone 12'],
        hasTouch: true
      },
      dependencies: ['setup']
    },

    /* Tablet Testing */
    {
      name: 'tablet',
      use: {
        ...devices['iPad Pro'],
        hasTouch: true
      },
      dependencies: ['setup']
    },

    /* API Testing */
    {
      name: 'api',
      testDir: './tests/api',
      use: {
        baseURL: process.env.API_BASE_URL || 'http://localhost:8000/api/v1'
      },
      dependencies: ['setup']
    },

    /* Performance Testing */
    {
      name: 'performance',
      testDir: './tests/performance',
      use: {
        ...devices['Desktop Chrome'],
        channel: 'chrome'
      },
      dependencies: ['setup']
    }
  ],

  /* Test categorization and filtering */
  grep: [
    /@smoke|@regression|@integration|@e2e/
  ],

  /* Run your local dev server before starting the tests */
  webServer: [
    {
      command: 'npm run start:test',
      port: 3000,
      reuseExistingServer: !process.env.CI,
      env: {
        NODE_ENV: 'test',
        DATABASE_URL: process.env.TEST_DATABASE_URL || 'postgresql://test:test@localhost:5432/aitrading_test',
        REDIS_URL: process.env.TEST_REDIS_URL || 'redis://localhost:6379/1',
        API_KEY: process.env.TEST_API_KEY || 'test-api-key',
        JWT_SECRET: process.env.TEST_JWT_SECRET || 'test-jwt-secret'
      }
    },
    {
      command: 'npm run start:api',
      port: 8000,
      reuseExistingServer: !process.env.CI,
      env: {
        NODE_ENV: 'test',
        PORT: '8000'
      }
    }
  ],

  /* Global setup and teardown */
  globalSetup: path.resolve(__dirname, 'global.setup.ts'),
  globalTeardown: path.resolve(__dirname, 'global.teardown.ts'),

  /* Output directories */
  outputDir: 'test-results/',

  /* Test result directories */
  testDir: './tests',

  /* Metadata */
  metadata: {
    'test-suite': 'AI Trading Platform E2E Tests',
    'version': '1.0.0',
    'environment': process.env.NODE_ENV || 'test',
    'timestamp': new Date().toISOString()
  }
});