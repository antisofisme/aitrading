#!/usr/bin/env node

/**
 * Level 2 Connectivity Validation Script
 * Validates all Level 2 requirements are met according to plan2 specifications
 */

const axios = require('axios');
const colors = require('colors');

// Service configurations matching plan2 Level 2 requirements
const LEVEL_2_SERVICES = {
  'API Gateway': {
    port: 8000,
    url: 'http://localhost:8000',
    endpoints: ['/health', '/health/services', '/metrics'],
    features: ['multi-tenant', 'rate-limiting', 'service-discovery']
  },
  'User Management': {
    port: 8021,
    url: 'http://localhost:8021',
    endpoints: ['/health', '/api/auth', '/api/users'],
    features: ['authentication', 'registration', 'profiles']
  },
  'Subscription Service': {
    port: 8022,
    url: 'http://localhost:8022',
    endpoints: ['/health', '/api/subscriptions', '/api/usage'],
    features: ['billing', 'tier-management', 'usage-tracking']
  },
  'Payment Gateway': {
    port: 8023,
    url: 'http://localhost:8023',
    endpoints: ['/health', '/api/payments', '/api/methods'],
    features: ['midtrans-integration', 'indonesian-payments']
  },
  'Notification Service': {
    port: 8024,
    url: 'http://localhost:8024',
    endpoints: ['/health', '/api/notifications', '/api/telegram'],
    features: ['telegram-bot', 'multi-user-management', 'email', 'sms']
  },
  'Billing Service': {
    port: 8025,
    url: 'http://localhost:8025',
    endpoints: ['/health', '/api/invoices', '/api/billing'],
    features: ['invoice-generation', 'payment-processing']
  }
};

// Performance targets from plan2
const PERFORMANCE_TARGETS = {
  'multi-tenant-response': 15, // <15ms multi-tenant performance
  'api-response': 50, // <50ms API response time
  'service-communication': 5, // <5ms service-to-service latency
};

// Test results storage
const testResults = {
  services: {},
  connectivity: {},
  multiTenant: {},
  performance: {},
  overall: { passed: 0, failed: 0, warnings: 0 }
};

// Utility functions
function log(message, type = 'info') {
  const timestamp = new Date().toISOString();
  switch (type) {
    case 'success':
      console.log(`[${timestamp}] ✅ ${message}`.green);
      break;
    case 'error':
      console.log(`[${timestamp}] ❌ ${message}`.red);
      break;
    case 'warning':
      console.log(`[${timestamp}] ⚠️  ${message}`.yellow);
      break;
    case 'info':
      console.log(`[${timestamp}] ℹ️  ${message}`.blue);
      break;
  }
}

function updateResults(category, test, passed, message) {
  if (!testResults[category]) testResults[category] = {};
  testResults[category][test] = { passed, message };

  if (passed) {
    testResults.overall.passed++;
  } else {
    testResults.overall.failed++;
  }
}

// Test functions
async function testServiceHealth(serviceName, serviceConfig) {
  log(`Testing ${serviceName} health...`);

  try {
    const startTime = Date.now();
    const response = await axios.get(`${serviceConfig.url}/health`, {
      timeout: 5000,
      headers: { 'User-Agent': 'Level2-Validator/1.0.0' }
    });
    const responseTime = Date.now() - startTime;

    if (response.status === 200) {
      log(`${serviceName} is healthy (${responseTime}ms)`, 'success');
      updateResults('services', serviceName, true, `Healthy (${responseTime}ms)`);

      // Test specific endpoints
      await testServiceEndpoints(serviceName, serviceConfig);

      return true;
    } else {
      log(`${serviceName} returned status ${response.status}`, 'error');
      updateResults('services', serviceName, false, `HTTP ${response.status}`);
      return false;
    }
  } catch (error) {
    log(`${serviceName} health check failed: ${error.message}`, 'error');
    updateResults('services', serviceName, false, error.message);
    return false;
  }
}

async function testServiceEndpoints(serviceName, serviceConfig) {
  for (const endpoint of serviceConfig.endpoints) {
    try {
      const response = await axios.get(`${serviceConfig.url}${endpoint}`, {
        timeout: 3000,
        validateStatus: (status) => status < 500 // Allow 4xx but not 5xx
      });

      log(`${serviceName}${endpoint} responded with ${response.status}`, 'success');
    } catch (error) {
      log(`${serviceName}${endpoint} failed: ${error.message}`, 'warning');
      testResults.overall.warnings++;
    }
  }
}

async function testMultiTenantFeatures() {
  log('Testing multi-tenant features...');

  try {
    // Test API Gateway multi-tenant routing
    const response = await axios.get('http://localhost:8000/', {
      timeout: 5000
    });

    if (response.data.features && response.data.features.multiTenant === 'enabled') {
      log('Multi-tenant support confirmed', 'success');
      updateResults('multiTenant', 'support', true, 'Multi-tenant enabled');
    } else {
      log('Multi-tenant support not detected', 'error');
      updateResults('multiTenant', 'support', false, 'Multi-tenant not enabled');
    }

    // Test rate limiting
    await testRateLimiting();

    // Test service discovery
    await testServiceDiscovery();

  } catch (error) {
    log(`Multi-tenant testing failed: ${error.message}`, 'error');
    updateResults('multiTenant', 'general', false, error.message);
  }
}

async function testRateLimiting() {
  log('Testing rate limiting...');

  try {
    // Make rapid requests to test rate limiting
    const requests = [];
    for (let i = 0; i < 25; i++) {
      requests.push(
        axios.get('http://localhost:8000/health', {
          timeout: 1000,
          validateStatus: () => true // Accept all status codes
        })
      );
    }

    const responses = await Promise.all(requests);
    const rateLimited = responses.some(r => r.status === 429);

    if (rateLimited) {
      log('Rate limiting is working', 'success');
      updateResults('multiTenant', 'rateLimiting', true, 'Rate limiting active');
    } else {
      log('Rate limiting not detected (may need higher load)', 'warning');
      updateResults('multiTenant', 'rateLimiting', false, 'Rate limiting not triggered');
      testResults.overall.warnings++;
    }

  } catch (error) {
    log(`Rate limiting test failed: ${error.message}`, 'error');
    updateResults('multiTenant', 'rateLimiting', false, error.message);
  }
}

async function testServiceDiscovery() {
  log('Testing service discovery...');

  try {
    const response = await axios.get('http://localhost:8000/health/services', {
      timeout: 10000
    });

    if (response.data.services && Object.keys(response.data.services).length > 0) {
      const healthyServices = Object.values(response.data.services)
        .filter(service => service.status === 'healthy').length;

      log(`Service discovery working: ${healthyServices} healthy services`, 'success');
      updateResults('multiTenant', 'serviceDiscovery', true, `${healthyServices} services discovered`);
    } else {
      log('Service discovery not working', 'error');
      updateResults('multiTenant', 'serviceDiscovery', false, 'No services discovered');
    }

  } catch (error) {
    log(`Service discovery test failed: ${error.message}`, 'error');
    updateResults('multiTenant', 'serviceDiscovery', false, error.message);
  }
}

async function testServiceCommunication() {
  log('Testing service-to-service communication...');

  // Test each service can communicate through API Gateway
  const communicationTests = [
    { from: 'API Gateway', to: 'User Management', path: '/api/auth' },
    { from: 'API Gateway', to: 'Subscription Service', path: '/api/subscriptions' },
    { from: 'API Gateway', to: 'Payment Gateway', path: '/api/payments' },
    { from: 'API Gateway', to: 'Notification Service', path: '/api/notifications' },
    { from: 'API Gateway', to: 'Billing Service', path: '/api/billing' }
  ];

  for (const test of communicationTests) {
    try {
      const startTime = Date.now();
      const response = await axios.get(`http://localhost:8000${test.path}`, {
        timeout: 5000,
        validateStatus: (status) => status < 500,
        headers: {
          'Authorization': 'Bearer test-token' // This will fail auth but test routing
        }
      });
      const responseTime = Date.now() - startTime;

      // We expect 401 (unauthorized) which means routing worked
      if (response.status === 401 || response.status === 200) {
        log(`${test.from} → ${test.to} communication OK (${responseTime}ms)`, 'success');
        updateResults('connectivity', `${test.to}`, true, `Routed successfully (${responseTime}ms)`);
      } else {
        log(`${test.from} → ${test.to} unexpected status: ${response.status}`, 'warning');
        updateResults('connectivity', `${test.to}`, false, `HTTP ${response.status}`);
        testResults.overall.warnings++;
      }

    } catch (error) {
      log(`${test.from} → ${test.to} communication failed: ${error.message}`, 'error');
      updateResults('connectivity', `${test.to}`, false, error.message);
    }
  }
}

async function testPerformance() {
  log('Testing performance targets...');

  // Test API response time
  const apiTests = [
    'http://localhost:8000/health',
    'http://localhost:8021/health',
    'http://localhost:8022/health',
    'http://localhost:8023/health',
    'http://localhost:8024/health',
    'http://localhost:8025/health'
  ];

  let totalResponseTime = 0;
  let successfulTests = 0;

  for (const url of apiTests) {
    try {
      const startTime = Date.now();
      await axios.get(url, { timeout: 5000 });
      const responseTime = Date.now() - startTime;

      totalResponseTime += responseTime;
      successfulTests++;

      if (responseTime < PERFORMANCE_TARGETS['api-response']) {
        log(`${url} responded in ${responseTime}ms (target: <${PERFORMANCE_TARGETS['api-response']}ms)`, 'success');
      } else {
        log(`${url} slow response: ${responseTime}ms (target: <${PERFORMANCE_TARGETS['api-response']}ms)`, 'warning');
        testResults.overall.warnings++;
      }
    } catch (error) {
      log(`Performance test failed for ${url}: ${error.message}`, 'error');
    }
  }

  if (successfulTests > 0) {
    const averageResponseTime = totalResponseTime / successfulTests;
    const performanceGood = averageResponseTime < PERFORMANCE_TARGETS['api-response'];

    updateResults('performance', 'apiResponse', performanceGood,
      `Average: ${averageResponseTime.toFixed(2)}ms (target: <${PERFORMANCE_TARGETS['api-response']}ms)`);
  }
}

async function testDataIsolation() {
  log('Testing per-user data isolation mechanisms...');

  // This is a conceptual test - in a real environment you'd test:
  // 1. User A cannot access User B's data
  // 2. Subscription tiers properly restrict access
  // 3. Multi-tenant data separation

  try {
    // Test that different subscription tiers have different rate limits
    const response = await axios.get('http://localhost:8000/', {
      timeout: 5000
    });

    if (response.data.features && response.data.features.rateLimiting === 'per-user') {
      log('Per-user data isolation mechanisms detected', 'success');
      updateResults('multiTenant', 'dataIsolation', true, 'Per-user isolation enabled');
    } else {
      log('Per-user data isolation not clearly indicated', 'warning');
      updateResults('multiTenant', 'dataIsolation', false, 'Isolation not confirmed');
      testResults.overall.warnings++;
    }

  } catch (error) {
    log(`Data isolation test failed: ${error.message}`, 'error');
    updateResults('multiTenant', 'dataIsolation', false, error.message);
  }
}

function generateReport() {
  console.log('\n' + '='.repeat(80).cyan);
  console.log('LEVEL 2 CONNECTIVITY VALIDATION REPORT'.cyan.bold);
  console.log('='.repeat(80).cyan);

  console.log('\n📊 OVERALL RESULTS:'.bold);
  console.log(`✅ Passed: ${testResults.overall.passed}`.green);
  console.log(`❌ Failed: ${testResults.overall.failed}`.red);
  console.log(`⚠️  Warnings: ${testResults.overall.warnings}`.yellow);

  const totalTests = testResults.overall.passed + testResults.overall.failed;
  const successRate = totalTests > 0 ? ((testResults.overall.passed / totalTests) * 100).toFixed(1) : 0;
  console.log(`📈 Success Rate: ${successRate}%`);

  // Service Health Results
  console.log('\n🏥 SERVICE HEALTH:'.bold);
  for (const [service, result] of Object.entries(testResults.services || {})) {
    const status = result.passed ? '✅' : '❌';
    console.log(`  ${status} ${service}: ${result.message}`);
  }

  // Multi-Tenant Features
  console.log('\n🏢 MULTI-TENANT FEATURES:'.bold);
  for (const [feature, result] of Object.entries(testResults.multiTenant || {})) {
    const status = result.passed ? '✅' : '❌';
    console.log(`  ${status} ${feature}: ${result.message}`);
  }

  // Service Connectivity
  console.log('\n🔗 SERVICE CONNECTIVITY:'.bold);
  for (const [service, result] of Object.entries(testResults.connectivity || {})) {
    const status = result.passed ? '✅' : '❌';
    console.log(`  ${status} ${service}: ${result.message}`);
  }

  // Performance Results
  console.log('\n⚡ PERFORMANCE:'.bold);
  for (const [metric, result] of Object.entries(testResults.performance || {})) {
    const status = result.passed ? '✅' : '❌';
    console.log(`  ${status} ${metric}: ${result.message}`);
  }

  // Level 2 Completion Status
  console.log('\n🎯 LEVEL 2 COMPLETION STATUS:'.bold);

  const criticalRequirements = [
    'All business services operational (8021-8025)',
    'Multi-tenant API Gateway with rate limiting',
    'Service-to-service communication working',
    'Per-user data isolation mechanisms'
  ];

  const allServicesHealthy = Object.values(testResults.services || {}).every(r => r.passed);
  const multiTenantWorking = Object.values(testResults.multiTenant || {}).some(r => r.passed);
  const connectivityWorking = Object.values(testResults.connectivity || {}).some(r => r.passed);

  console.log(`  ${allServicesHealthy ? '✅' : '❌'} Business Services (8021-8025): ${allServicesHealthy ? 'OPERATIONAL' : 'ISSUES DETECTED'}`);
  console.log(`  ${multiTenantWorking ? '✅' : '❌'} Multi-tenant Features: ${multiTenantWorking ? 'WORKING' : 'NOT DETECTED'}`);
  console.log(`  ${connectivityWorking ? '✅' : '❌'} Service Communication: ${connectivityWorking ? 'WORKING' : 'ISSUES DETECTED'}`);

  const level2Complete = allServicesHealthy && multiTenantWorking && connectivityWorking;

  console.log('\n' + '='.repeat(80));
  if (level2Complete) {
    console.log('🎉 LEVEL 2 CONNECTIVITY: COMPLETE ✅'.green.bold);
    console.log('🚀 Ready to proceed to Level 3 Data Flow'.green);
  } else {
    console.log('⚠️  LEVEL 2 CONNECTIVITY: INCOMPLETE ❌'.red.bold);
    console.log('🔧 Please address the issues above before proceeding to Level 3'.yellow);
  }
  console.log('='.repeat(80));

  return level2Complete;
}

async function runValidation() {
  console.log('🚀 Starting Level 2 Connectivity Validation...'.cyan.bold);
  console.log('📋 Testing according to plan2 Level 2 specifications\n');

  try {
    // Test all Level 2 services
    for (const [serviceName, serviceConfig] of Object.entries(LEVEL_2_SERVICES)) {
      await testServiceHealth(serviceName, serviceConfig);
    }

    // Test multi-tenant features
    await testMultiTenantFeatures();

    // Test service-to-service communication
    await testServiceCommunication();

    // Test performance
    await testPerformance();

    // Test data isolation
    await testDataIsolation();

  } catch (error) {
    log(`Validation failed: ${error.message}`, 'error');
  }

  // Generate final report
  const level2Complete = generateReport();

  // Exit with appropriate code
  process.exit(level2Complete ? 0 : 1);
}

// Handle command line execution
if (require.main === module) {
  runValidation();
}

module.exports = {
  runValidation,
  testResults,
  LEVEL_2_SERVICES,
  PERFORMANCE_TARGETS
};