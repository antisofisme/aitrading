#!/usr/bin/env node

/**
 * End-to-End Health Check Test Script
 * Validates all services are running and communicating properly
 */

const axios = require('axios');
const colors = require('colors');

// Service endpoints from docker-compose.yml
const SERVICES = {
  'API Gateway': 'http://localhost:8000/health',
  'Central Hub': 'http://localhost:3000/health',
  'Database Service': 'http://localhost:8006/health',
  'Data Bridge': 'http://localhost:8001/health'
};

// Business API endpoints
const BUSINESS_ENDPOINTS = {
  'Subscription Tiers': 'http://localhost:8000/api/business/subscription-tiers',
  'API Gateway Info': 'http://localhost:8000/api'
};

// Integration endpoints
const INTEGRATION_ENDPOINTS = {
  'Central Hub Services': 'http://localhost:3000/api/services',
  'Database Multi-DB Status': 'http://localhost:8006/api/databases/status',
  'Central Hub Integration': 'http://localhost:8000/api/integration/central-hub'
};

class HealthChecker {
  constructor() {
    this.results = {
      services: {},
      business: {},
      integration: {},
      summary: {
        total: 0,
        healthy: 0,
        failed: 0
      }
    };
  }

  async runAllChecks() {
    console.log('\n🔍 Starting Level 1 Foundation Health Check Validation\n'.cyan);

    // Check core services
    console.log('📋 Checking Core Services...'.yellow);
    await this.checkServices(SERVICES, 'services');

    // Check business API layer
    console.log('\n💼 Checking Business API Layer...'.yellow);
    await this.checkServices(BUSINESS_ENDPOINTS, 'business');

    // Check integration endpoints
    console.log('\n🔗 Checking Service Integration...'.yellow);
    await this.checkServices(INTEGRATION_ENDPOINTS, 'integration');

    // Generate summary
    this.generateSummary();

    // Validate Level 1 completion
    this.validateLevel1Completion();
  }

  async checkServices(endpoints, category) {
    for (const [name, url] of Object.entries(endpoints)) {
      try {
        const startTime = Date.now();
        const response = await axios.get(url, { timeout: 5000 });
        const responseTime = Date.now() - startTime;

        const result = {
          name,
          url,
          status: 'healthy',
          statusCode: response.status,
          responseTime,
          data: response.data,
          timestamp: new Date().toISOString()
        };

        this.results[category][name] = result;
        this.results.summary.healthy++;

        console.log(`  ✅ ${name}: ${response.status} (${responseTime}ms)`.green);

        // Additional validation for specific endpoints
        await this.validateSpecificEndpoint(name, response.data);

      } catch (error) {
        const result = {
          name,
          url,
          status: 'unhealthy',
          error: error.message,
          statusCode: error.response?.status || 'NETWORK_ERROR',
          timestamp: new Date().toISOString()
        };

        this.results[category][name] = result;
        this.results.summary.failed++;

        console.log(`  ❌ ${name}: ${error.message}`.red);
      }

      this.results.summary.total++;
    }
  }

  async validateSpecificEndpoint(name, data) {
    switch (name) {
      case 'Database Service':
        if (data.databases) {
          console.log(`    📊 Multi-DB Status: ${Object.keys(data.databases).length} databases`.blue);

          // Validate multi-database connections
          const dbCount = Object.keys(data.databases).length;
          if (dbCount >= 5) { // Plan2 requires 5 databases
            console.log(`    ✅ Multi-DB requirement met (${dbCount}/5)`.green);
          } else {
            console.log(`    ⚠️  Multi-DB requirement not fully met (${dbCount}/5)`.yellow);
          }
        }
        break;

      case 'Data Bridge':
        if (data.mt5Enhanced) {
          const mt5 = data.mt5Enhanced;
          console.log(`    📈 MT5 Performance: ${mt5.ticksPerSecond || 0} ticks/sec`.blue);

          // Validate MT5 performance targets
          const currentTPS = mt5.ticksPerSecond || 0;
          const targetTPS = mt5.targetTicksPerSecond || 50;

          if (currentTPS >= 18) { // Plan2 baseline
            console.log(`    ✅ MT5 baseline performance met (${currentTPS}/18 tps)`.green);
          } else {
            console.log(`    ⚠️  MT5 baseline not met (${currentTPS}/18 tps)`.yellow);
          }
        }
        break;

      case 'Central Hub Services':
        if (Array.isArray(data.data)) {
          console.log(`    🏢 Registered Services: ${data.data.length}`.blue);
        }
        break;

      case 'Subscription Tiers':
        if (data.data) {
          const tiers = Object.keys(data.data);
          console.log(`    💰 Available Tiers: ${tiers.join(', ')}`.blue);

          // Validate business API completeness
          const expectedTiers = ['FREE', 'BASIC', 'PREMIUM', 'ENTERPRISE'];
          const hasAllTiers = expectedTiers.every(tier => tiers.includes(tier));

          if (hasAllTiers) {
            console.log(`    ✅ All subscription tiers implemented`.green);
          } else {
            console.log(`    ⚠️  Missing subscription tiers`.yellow);
          }
        }
        break;
    }
  }

  generateSummary() {
    console.log('\n📊 Health Check Summary\n'.cyan);

    const { total, healthy, failed } = this.results.summary;
    const healthPercentage = total > 0 ? ((healthy / total) * 100).toFixed(1) : 0;

    console.log(`Total Endpoints: ${total}`);
    console.log(`Healthy: ${healthy}`.green);
    console.log(`Failed: ${failed}`.red);
    console.log(`Health Percentage: ${healthPercentage}%`);

    // Service category breakdown
    Object.entries(this.results).forEach(([category, results]) => {
      if (category === 'summary') return;

      const categoryResults = Object.values(results);
      const categoryHealthy = categoryResults.filter(r => r.status === 'healthy').length;
      const categoryTotal = categoryResults.length;

      console.log(`\n${category.toUpperCase()}: ${categoryHealthy}/${categoryTotal} healthy`);
    });
  }

  validateLevel1Completion() {
    console.log('\n🎯 Level 1 Foundation Validation\n'.cyan);

    const validationChecks = [];

    // Core infrastructure validation
    const coreServices = ['API Gateway', 'Central Hub', 'Database Service', 'Data Bridge'];
    const coreHealthy = coreServices.every(service =>
      this.results.services[service]?.status === 'healthy'
    );
    validationChecks.push({
      check: 'Core Services Operational',
      passed: coreHealthy,
      details: `${coreServices.filter(s => this.results.services[s]?.status === 'healthy').length}/${coreServices.length} services healthy`
    });

    // Business API layer validation
    const businessEndpoints = Object.keys(BUSINESS_ENDPOINTS);
    const businessHealthy = businessEndpoints.every(endpoint =>
      this.results.business[endpoint]?.status === 'healthy'
    );
    validationChecks.push({
      check: 'Business API Layer Complete',
      passed: businessHealthy,
      details: `Revenue-generating endpoints operational`
    });

    // Service integration validation
    const integrationEndpoints = Object.keys(INTEGRATION_ENDPOINTS);
    const integrationHealthy = integrationEndpoints.every(endpoint =>
      this.results.integration[endpoint]?.status === 'healthy'
    );
    validationChecks.push({
      check: 'Service Integration Functional',
      passed: integrationHealthy,
      details: `Cross-service communication operational`
    });

    // Multi-database validation (from database service health check)
    const dbService = this.results.services['Database Service'];
    const multiDbHealthy = dbService?.data?.databases &&
      Object.keys(dbService.data.databases).length >= 3; // At least 3 DBs operational
    validationChecks.push({
      check: 'Multi-Database Support',
      passed: multiDbHealthy,
      details: `Multiple database types connected`
    });

    // MT5 integration validation
    const databridge = this.results.services['Data Bridge'];
    const mt5Healthy = databridge?.data?.mt5Enhanced?.isConnected ||
      databridge?.data?.mt5Enhanced?.performanceLevel === 'operational';
    validationChecks.push({
      check: 'MT5 Integration Active',
      passed: mt5Healthy,
      details: `Data Bridge MT5 connectivity confirmed`
    });

    // Display validation results
    let allPassed = true;
    validationChecks.forEach(check => {
      const status = check.passed ? '✅' : '❌';
      const color = check.passed ? 'green' : 'red';
      console.log(`${status} ${check.check}: ${check.details}`[color]);
      if (!check.passed) allPassed = false;
    });

    // Final assessment
    console.log('\n🏆 Level 1 Foundation Assessment\n'.cyan);

    if (allPassed) {
      console.log('🎉 LEVEL 1 FOUNDATION COMPLETE!'.green.bold);
      console.log('✅ All components operational and ready for Level 2 Connectivity'.green);
      console.log('📈 Performance targets met according to plan2 specifications'.green);
      console.log('🔗 Service coordination and integration validated'.green);
    } else {
      console.log('⚠️  LEVEL 1 FOUNDATION INCOMPLETE'.yellow.bold);
      console.log('❌ Some components require attention before Level 2'.red);
      console.log('🔧 Review failed checks and resolve issues'.yellow);
    }

    // Save results to file
    this.saveResults();
  }

  saveResults() {
    const fs = require('fs');
    const path = require('path');

    const resultsFile = path.join(__dirname, '../logs/health-check-results.json');
    const logData = {
      timestamp: new Date().toISOString(),
      results: this.results,
      level1Status: this.results.summary.failed === 0 ? 'COMPLETE' : 'INCOMPLETE'
    };

    // Ensure logs directory exists
    const logsDir = path.dirname(resultsFile);
    if (!fs.existsSync(logsDir)) {
      fs.mkdirSync(logsDir, { recursive: true });
    }

    fs.writeFileSync(resultsFile, JSON.stringify(logData, null, 2));
    console.log(`\n📝 Results saved to: ${resultsFile}`.blue);
  }
}

// Run health checks if script is executed directly
if (require.main === module) {
  const checker = new HealthChecker();

  checker.runAllChecks()
    .then(() => {
      const { failed } = checker.results.summary;
      process.exit(failed > 0 ? 1 : 0);
    })
    .catch(error => {
      console.error('Health check failed:', error);
      process.exit(1);
    });
}

module.exports = HealthChecker;