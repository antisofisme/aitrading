#!/usr/bin/env node

/**
 * @fileoverview Comprehensive health check script for AI Trading Platform
 * @version 1.0.0
 * @author AI Trading Platform Team
 */

const axios = require('axios');
const { performance } = require('perf_hooks');

// =============================================================================
// CONFIGURATION
// =============================================================================

const SERVICES = [
  {
    name: 'API Gateway',
    url: 'http://localhost:8001/health',
    critical: true,
    timeout: 10000
  },
  {
    name: 'Central Hub',
    url: 'http://localhost:8003/health',
    critical: true,
    timeout: 10000
  },
  {
    name: 'Database Service',
    url: 'http://localhost:8005/health',
    critical: true,
    timeout: 10000
  },
  {
    name: 'Data Bridge',
    url: 'http://localhost:8007/health',
    critical: false,
    timeout: 10000
  },
  {
    name: 'Consul',
    url: 'http://localhost:8500/v1/status/leader',
    critical: true,
    timeout: 5000
  },
  {
    name: 'Prometheus',
    url: 'http://localhost:9090/-/healthy',
    critical: false,
    timeout: 5000
  },
  {
    name: 'Grafana',
    url: 'http://localhost:3000/api/health',
    critical: false,
    timeout: 5000
  }
];

const COLORS = {
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  reset: '\x1b[0m',
  bright: '\x1b[1m'
};

// =============================================================================
// HEALTH CHECK FUNCTIONS
// =============================================================================

/**
 * Check health of a single service
 */
async function checkService(service) {
  const startTime = performance.now();

  try {
    const response = await axios.get(service.url, {
      timeout: service.timeout,
      validateStatus: (status) => status < 500
    });

    const endTime = performance.now();
    const responseTime = Math.round(endTime - startTime);

    const isHealthy = response.status >= 200 && response.status < 400;

    return {
      name: service.name,
      status: isHealthy ? 'healthy' : 'unhealthy',
      responseTime,
      statusCode: response.status,
      critical: service.critical,
      details: response.data
    };

  } catch (error) {
    const endTime = performance.now();
    const responseTime = Math.round(endTime - startTime);

    return {
      name: service.name,
      status: 'unhealthy',
      responseTime,
      statusCode: null,
      critical: service.critical,
      error: error.message
    };
  }
}

/**
 * Check all services in parallel
 */
async function checkAllServices() {
  console.log(`${COLORS.bright}${COLORS.blue}🏥 AI Trading Platform - Health Check${COLORS.reset}\n`);
  console.log(`${COLORS.cyan}Checking ${SERVICES.length} services...${COLORS.reset}\n`);

  const promises = SERVICES.map(service => checkService(service));
  const results = await Promise.all(promises);

  return results;
}

/**
 * Display health check results
 */
function displayResults(results) {
  const healthyServices = results.filter(r => r.status === 'healthy');
  const unhealthyServices = results.filter(r => r.status === 'unhealthy');
  const criticalIssues = unhealthyServices.filter(r => r.critical);

  console.log(`${COLORS.bright}📊 Health Check Results${COLORS.reset}\n`);

  // Display individual service results
  results.forEach(result => {
    const statusIcon = result.status === 'healthy' ? '✅' : '❌';
    const statusColor = result.status === 'healthy' ? COLORS.green : COLORS.red;
    const criticalFlag = result.critical ? ' [CRITICAL]' : '';

    console.log(`${statusIcon} ${statusColor}${result.name}${criticalFlag}${COLORS.reset}`);
    console.log(`   Status: ${statusColor}${result.status.toUpperCase()}${COLORS.reset}`);
    console.log(`   Response Time: ${result.responseTime}ms`);

    if (result.statusCode) {
      console.log(`   HTTP Status: ${result.statusCode}`);
    }

    if (result.error) {
      console.log(`   Error: ${COLORS.red}${result.error}${COLORS.reset}`);
    }

    console.log('');
  });

  // Display summary
  console.log(`${COLORS.bright}📈 Summary${COLORS.reset}`);
  console.log(`${COLORS.green}Healthy Services: ${healthyServices.length}${COLORS.reset}`);
  console.log(`${COLORS.red}Unhealthy Services: ${unhealthyServices.length}${COLORS.reset}`);

  if (criticalIssues.length > 0) {
    console.log(`${COLORS.red}${COLORS.bright}Critical Issues: ${criticalIssues.length}${COLORS.reset}`);
  }

  console.log('');

  // Overall status
  if (criticalIssues.length > 0) {
    console.log(`${COLORS.red}${COLORS.bright}🚨 OVERALL STATUS: CRITICAL${COLORS.reset}`);
    console.log(`${COLORS.red}Critical services are down. Immediate attention required.${COLORS.reset}`);
    return 2; // Critical exit code
  } else if (unhealthyServices.length > 0) {
    console.log(`${COLORS.yellow}${COLORS.bright}⚠️  OVERALL STATUS: DEGRADED${COLORS.reset}`);
    console.log(`${COLORS.yellow}Some non-critical services are down.${COLORS.reset}`);
    return 1; // Warning exit code
  } else {
    console.log(`${COLORS.green}${COLORS.bright}✅ OVERALL STATUS: HEALTHY${COLORS.reset}`);
    console.log(`${COLORS.green}All services are operational.${COLORS.reset}`);
    return 0; // Success exit code
  }
}

/**
 * Generate JSON report
 */
function generateJsonReport(results) {
  const timestamp = new Date().toISOString();
  const report = {
    timestamp,
    summary: {
      total: results.length,
      healthy: results.filter(r => r.status === 'healthy').length,
      unhealthy: results.filter(r => r.status === 'unhealthy').length,
      critical_issues: results.filter(r => r.status === 'unhealthy' && r.critical).length
    },
    services: results.map(result => ({
      name: result.name,
      status: result.status,
      response_time_ms: result.responseTime,
      http_status: result.statusCode,
      critical: result.critical,
      error: result.error || null,
      checked_at: timestamp
    }))
  };

  return JSON.stringify(report, null, 2);
}

// =============================================================================
// MAIN EXECUTION
// =============================================================================

async function main() {
  const args = process.argv.slice(2);
  const jsonOutput = args.includes('--json');
  const continuous = args.includes('--continuous');
  const interval = parseInt(args.find(arg => arg.startsWith('--interval='))?.split('=')[1]) || 30;

  if (continuous) {
    console.log(`${COLORS.cyan}Running continuous health checks every ${interval} seconds...${COLORS.reset}\n`);
    console.log(`${COLORS.cyan}Press Ctrl+C to stop${COLORS.reset}\n`);

    while (true) {
      const results = await checkAllServices();

      if (jsonOutput) {
        console.log(generateJsonReport(results));
      } else {
        const exitCode = displayResults(results);
        if (exitCode === 2) {
          console.log(`${COLORS.red}Critical issues detected! Consider alerting operations team.${COLORS.reset}\n`);
        }
      }

      console.log(`${COLORS.cyan}Next check in ${interval} seconds...${COLORS.reset}\n`);
      await new Promise(resolve => setTimeout(resolve, interval * 1000));
    }
  } else {
    // Single run
    const results = await checkAllServices();

    if (jsonOutput) {
      console.log(generateJsonReport(results));
    } else {
      const exitCode = displayResults(results);
      process.exit(exitCode);
    }
  }
}

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log(`\n${COLORS.yellow}Health check terminated by user${COLORS.reset}`);
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log(`\n${COLORS.yellow}Health check terminated${COLORS.reset}`);
  process.exit(0);
});

// Error handling
process.on('unhandledRejection', (reason, promise) => {
  console.error(`${COLORS.red}Unhandled Rejection at:${COLORS.reset}`, promise, `${COLORS.red}reason:${COLORS.reset}`, reason);
  process.exit(1);
});

// Show usage if help requested
if (process.argv.includes('--help') || process.argv.includes('-h')) {
  console.log(`
${COLORS.bright}AI Trading Platform - Health Check Tool${COLORS.reset}

Usage: node health-check.js [options]

Options:
  --json                 Output results in JSON format
  --continuous          Run continuous health checks
  --interval=<seconds>  Set interval for continuous checks (default: 30)
  --help, -h           Show this help message

Examples:
  node health-check.js                    # Single health check
  node health-check.js --json             # JSON output
  node health-check.js --continuous       # Continuous monitoring
  node health-check.js --continuous --interval=60  # Check every 60 seconds

Exit Codes:
  0  All services healthy
  1  Some non-critical services unhealthy
  2  Critical services unhealthy
`);
  process.exit(0);
}

// Run the health check
main().catch(error => {
  console.error(`${COLORS.red}Health check failed:${COLORS.reset}`, error);
  process.exit(1);
});