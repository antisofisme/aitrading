# AI Trading Platform - End-to-End Testing Framework

A comprehensive E2E testing framework for the AI Trading Platform, built with Playwright and designed for complete user journey validation, cross-service integration testing, and automated regression testing.

## 🚀 Features

- **Complete User Journey Testing**: Authentication through order execution to reporting
- **Cross-Service Integration**: Validates communication between all microservices
- **Automated Regression Testing**: Prevents feature degradation
- **Performance & Load Testing**: Ensures system scalability
- **Real-time Data Validation**: Tests WebSocket connections and live updates
- **Accessibility Compliance**: WCAG 2.1 validation
- **Multi-Browser Support**: Chrome, Firefox, Safari, and mobile
- **Docker Environment**: Isolated test environment with all services
- **CI/CD Integration**: GitHub Actions workflow included

## 📁 Project Structure

```
tests/e2e/
├── .github/workflows/           # CI/CD workflows
├── config/                      # Configuration files
├── data/                        # Test data and fixtures
│   ├── fixtures/               # Static test data
│   ├── baselines/              # Regression test baselines
│   └── screenshots/            # Visual regression data
├── reports/                     # Test reports and metrics
├── scripts/                     # Setup and utility scripts
├── tests/                       # Test specifications
│   ├── auth/                   # Authentication tests
│   ├── trading/                # Trading workflow tests
│   ├── integration/            # Cross-service tests
│   ├── regression/             # Regression test suites
│   ├── reports/                # Reporting and analytics tests
│   └── performance/            # Performance and load tests
├── utils/                       # Helper utilities
├── docker-compose.test.yml      # Test environment configuration
├── playwright.config.ts         # Playwright configuration
└── package.json                # Dependencies and scripts
```

## 🛠 Prerequisites

- Node.js 18+
- Docker & Docker Compose
- Git
- PostgreSQL client tools (for database operations)

## 🚀 Quick Start

### 1. Installation

```bash
# Install dependencies
npm install
cd tests/e2e && npm install

# Install Playwright browsers
npx playwright install --with-deps
```

### 2. Environment Setup

```bash
# Setup test environment
cd tests/e2e
node scripts/setup-test-environment.js

# Or use Docker for full isolation
npm run test:env:start
```

### 3. Run Tests

```bash
# Run all tests
npm run test:e2e

# Run specific test suites
npm run test:e2e:smoke          # Quick smoke tests
npm run test:e2e:regression     # Full regression suite
npm run test:e2e:integration    # Cross-service tests
npm run test:e2e:performance    # Performance tests

# Run with UI for debugging
npm run test:e2e:ui

# Run in debug mode
npm run test:e2e:debug
```

## 📋 Available Test Suites

### Smoke Tests (`@smoke`)
Quick validation of core functionality:
- User authentication
- Basic trading operations
- System health checks
- **Duration**: ~5-10 minutes

### Regression Tests (`@regression`)
Comprehensive feature validation:
- All user workflows
- API compatibility
- Performance benchmarks
- Visual consistency
- **Duration**: ~30-60 minutes

### Integration Tests (`@integration`)
Cross-service validation:
- Service communication
- Data consistency
- Real-time updates
- Error handling
- **Duration**: ~15-30 minutes

### Performance Tests (`@performance`)
Load and stress testing:
- Page load performance
- API response times
- Concurrent user handling
- Memory usage validation
- **Duration**: ~20-45 minutes

## 🔧 Configuration

### Environment Variables

Create `.env.test` file:

```bash
NODE_ENV=test
DATABASE_URL=postgresql://test:test@localhost:5432/aitrading_test
REDIS_URL=redis://localhost:6379/1
API_BASE_URL=http://localhost:3000
JWT_SECRET=test-jwt-secret-key
API_KEY=test-api-key
LOG_LEVEL=debug
```

### Playwright Configuration

Key settings in `playwright.config.ts`:

```typescript
export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : 4,

  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    video: 'retain-on-failure',
    screenshot: 'only-on-failure'
  },

  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    { name: 'mobile-chrome', use: { ...devices['Pixel 5'] } }
  ]
});
```

## 📊 Test Data Management

### Fixtures and Seed Data

Test data is automatically generated and seeded:

```typescript
// Generate test users
const users = [
  { role: 'admin', email: 'admin@test.com' },
  { role: 'trader', email: 'trader@test.com' },
  { role: 'premium_trader', email: 'premium@test.com' }
];

// Generate trading data
const strategies = generateStrategies(20);
const orders = generateOrders(100);
const positions = generatePositions(50);
```

### Data Reset Between Tests

```bash
# Reset test data
npm run test:data:reset

# Seed fresh data
npm run test:data:seed
```

## 🏗 Docker Test Environment

Full isolated environment with all services:

```yaml
services:
  postgres:         # Test database
  redis:            # Cache and sessions
  api-gateway:      # Main API
  user-service:     # Authentication
  trading-engine:   # Order processing
  data-bridge:      # Market data
  web-ui:           # Frontend application
```

### Docker Commands

```bash
# Start test environment
npm run test:env:start

# Stop environment
npm run test:env:stop

# Reset environment
npm run test:env:reset

# View logs
docker-compose -f docker-compose.test.yml logs -f
```

## 🧪 Writing Tests

### Basic Test Structure

```typescript
import { test, expect } from '@playwright/test';
import { AuthenticationHelper } from '../utils/authentication-helper';
import { TradingHelper } from '../utils/trading-helper';

test.describe('Trading Operations', () => {
  let authHelper: AuthenticationHelper;
  let tradingHelper: TradingHelper;

  test.beforeEach(async ({ page }) => {
    authHelper = new AuthenticationHelper();
    tradingHelper = new TradingHelper();

    await authHelper.loginAs(page, 'premium_trader');
  });

  test('should place market order', async ({ page }) => {
    const orderId = await tradingHelper.placeMarketOrder(page, {
      symbol: 'EURUSD',
      side: 'buy',
      quantity: 10000
    });

    expect(orderId).toBeTruthy();

    // Verify order appears in orders list
    await page.goto('/orders');
    await expect(page.locator(`[data-testid="order-${orderId}"]`)).toBeVisible();
  });
});
```

### Test Categories

Use tags to categorize tests:

- `@smoke` - Quick validation tests
- `@regression` - Full feature validation
- `@integration` - Cross-service tests
- `@performance` - Load and stress tests
- `@accessibility` - WCAG compliance tests
- `@e2e` - Complete user journeys

### Helper Utilities

Framework includes comprehensive helpers:

```typescript
// Authentication
await authHelper.loginAs(page, 'trader');
await authHelper.logout(page);

// Trading operations
const orderId = await tradingHelper.placeMarketOrder(page, orderData);
await tradingHelper.closePosition(page, 'EURUSD');

// API testing
await apiHelper.authenticate('premium_trader');
const response = await apiHelper.getPortfolio();

// Reporting
const reportId = await reportingHelper.generateReport(page, reportConfig);
```

## 📈 Performance Monitoring

### Performance Budgets

Tests enforce performance budgets:

```typescript
const performanceBudget = {
  maxLoadTime: 3000,           // 3 seconds
  maxDOMContentLoaded: 2000,   // 2 seconds
  maxFirstPaint: 1500,         // 1.5 seconds
  maxFirstContentfulPaint: 2000 // 2 seconds
};
```

### Load Testing

Concurrent user simulation:

```typescript
// Test with 10 concurrent users
const concurrentUsers = 10;
const contexts = await Promise.all(
  Array(concurrentUsers).fill(null).map(() => browser.newContext())
);

// Execute operations concurrently
await Promise.all(
  contexts.map(context => performUserJourney(context))
);
```

## 🔄 CI/CD Integration

### GitHub Actions Workflow

Automated testing on:
- Push to main/develop branches
- Pull requests
- Daily scheduled runs
- Manual triggers

```yaml
# .github/workflows/e2e-tests.yml
name: E2E Tests
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC

jobs:
  smoke-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run smoke tests
        run: npm run test:e2e:smoke
```

### Test Artifacts

Automatic collection of:
- Test reports (HTML, JSON, JUnit)
- Screenshots and videos on failure
- Performance metrics
- Accessibility reports
- Coverage data

## 📊 Reporting and Analysis

### Test Reports

Multiple report formats generated:

```bash
# HTML report with videos and screenshots
npm run report:html

# Allure report with detailed analytics
npm run report:allure

# JSON data for custom analysis
npm run report:json
```

### Regression Analysis

Automated comparison with baselines:

```typescript
// Compare current performance with baseline
const comparison = await regressionHelper.compareWithBaseline(
  'page_load_performance',
  currentMetrics
);

if (!comparison.match) {
  console.log('Performance regression detected:', comparison.differences);
}
```

### Visual Regression

Screenshot comparison for UI consistency:

```typescript
// Take and compare screenshots
await regressionHelper.compareScreenshot('dashboard', screenshot);
```

## 🛡 Best Practices

### 1. Test Organization

- Keep tests focused and atomic
- Use descriptive test names
- Group related tests in describe blocks
- Tag tests appropriately

### 2. Data Management

- Use test-specific data
- Clean up after tests
- Avoid test interdependencies
- Use fixtures for consistent data

### 3. Error Handling

- Expect and handle failures gracefully
- Provide meaningful error messages
- Include debugging information
- Use proper timeouts

### 4. Performance

- Run tests in parallel when possible
- Use appropriate wait strategies
- Monitor test execution times
- Optimize for CI/CD environments

## 🔧 Troubleshooting

### Common Issues

1. **Services not starting**
   ```bash
   # Check service health
   docker-compose -f docker-compose.test.yml ps

   # View service logs
   docker-compose -f docker-compose.test.yml logs [service-name]
   ```

2. **Database connection issues**
   ```bash
   # Test database connectivity
   psql postgresql://test:test@localhost:5432/aitrading_test -c "SELECT 1;"
   ```

3. **Port conflicts**
   ```bash
   # Check port usage
   netstat -tulpn | grep :3000

   # Kill processes using required ports
   pkill -f "node.*3000"
   ```

4. **Browser issues**
   ```bash
   # Reinstall browsers
   npx playwright install --force

   # Install system dependencies
   npx playwright install-deps
   ```

### Debug Mode

Run tests in debug mode for troubleshooting:

```bash
# Debug specific test
npx playwright test tests/auth/login.spec.ts --debug

# Debug with UI mode
npx playwright test --ui

# Generate trace for failed tests
npx playwright test --trace on
```

## 📚 Advanced Usage

### Custom Test Data

Create custom test scenarios:

```typescript
// Custom user with specific configuration
const customUser = await testDataManager.createCustomUser({
  role: 'trader',
  balance: 50000,
  riskLevel: 'high',
  strategies: ['momentum', 'scalping']
});
```

### API Load Testing

Stress test specific endpoints:

```typescript
const loadTestResults = await apiHelper.runLoadTest(
  '/api/v1/market-data',
  requests: 1000,
  concurrency: 50
);
```

### Custom Reporters

Implement custom test reporters:

```typescript
class CustomReporter {
  onTestResult(test, result) {
    // Send results to external monitoring system
    sendToMonitoring(test, result);
  }
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add comprehensive tests
4. Ensure all tests pass
5. Submit a pull request

### Code Quality Standards

- TypeScript for type safety
- ESLint for code quality
- Prettier for formatting
- 90%+ test coverage for new features

## 📞 Support

- **Documentation**: Check README files in subdirectories
- **Issues**: Use GitHub Issues for bug reports
- **Discussions**: GitHub Discussions for questions
- **Wiki**: Detailed guides and examples

## 📄 License

MIT License - see LICENSE file for details.

---

## 🎯 Quick Reference

### Essential Commands

```bash
# Setup
npm run test:setup

# Run all tests
npm run test:e2e

# Smoke tests only
npm run test:e2e:smoke

# Debug mode
npm run test:e2e:debug

# Performance tests
npm run test:e2e:performance

# Generate reports
npm run report:generate

# Clean up
npm run test:cleanup
```

### Test Tags

- `@smoke` - Essential functionality
- `@regression` - Full test suite
- `@integration` - Service integration
- `@performance` - Load testing
- `@accessibility` - WCAG compliance
- `@critical` - Must-pass tests

This E2E testing framework provides comprehensive coverage of the AI Trading Platform, ensuring reliability, performance, and user experience quality across all components and user journeys.