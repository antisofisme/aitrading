/**
 * Quick Foundation Validation Script
 * Lightweight validation without full Jest dependency
 */

const config = require('./config/test-config');
const helpers = require('./utils/test-helpers');

class FoundationValidator {
  constructor() {
    this.results = {
      services: {},
      databases: {},
      configuration: {},
      summary: null
    };
  }

  async validateServices() {
    console.log('🔍 Validating Foundation Services...');

    const services = [
      {
        name: 'API Gateway',
        url: config.apiGateway.baseUrl,
        port: config.apiGateway.expectedPort,
        critical: true
      },
      {
        name: 'Database Service',
        url: config.databaseService.baseUrl,
        port: config.databaseService.expectedPort,
        critical: true
      },
      {
        name: 'Data Bridge',
        url: config.dataBridge.baseUrl,
        port: config.dataBridge.expectedPort,
        critical: false
      },
      {
        name: 'Central Hub',
        url: config.centralHub.baseUrl,
        port: config.centralHub.expectedPort,
        critical: true
      }
    ];

    for (const service of services) {
      console.log(`\n🧪 Testing ${service.name}...`);

      try {
        // Check port
        const isPortOpen = await helpers.isPortOpen('localhost', service.port);
        console.log(`   Port ${service.port}: ${isPortOpen ? '✅ Open' : '❌ Closed'}`);

        // Check health
        let health = { isHealthy: false, error: 'Port not open' };
        if (isPortOpen) {
          health = await helpers.checkHealth(service.url);
          console.log(`   Health: ${health.isHealthy ? '✅ Healthy' : '❌ Unhealthy'}`);
        }

        this.results.services[service.name] = {
          port: service.port,
          portOpen: isPortOpen,
          healthy: health.isHealthy,
          critical: service.critical,
          details: health
        };

      } catch (error) {
        console.log(`   Error: ❌ ${error.message}`);
        this.results.services[service.name] = {
          port: service.port,
          portOpen: false,
          healthy: false,
          critical: service.critical,
          error: error.message
        };
      }
    }
  }

  async validateDatabases() {
    console.log('\n🗄️  Validating Multi-Database Setup...');

    const databases = config.databaseService.databases;

    for (const [dbName, dbConfig] of Object.entries(databases)) {
      console.log(`\n🔗 Testing ${dbName} database...`);

      try {
        const dbTest = await helpers.testDatabaseConnection(dbConfig, dbName);
        console.log(`   Connection: ${dbTest.connected ? '✅ Connected' : '❌ Failed'}`);

        if (dbTest.connected) {
          console.log(`   Database: ${dbTest.database}`);
        } else {
          console.log(`   Error: ${dbTest.error}`);
        }

        this.results.databases[dbName] = dbTest;

      } catch (error) {
        console.log(`   Error: ❌ ${error.message}`);
        this.results.databases[dbName] = {
          connected: false,
          database: dbConfig.database,
          error: error.message
        };
      }
    }
  }

  async validateConfiguration() {
    console.log('\n⚙️  Validating Configuration...');

    const fs = require('fs');

    // Check API Gateway config
    const gatewayConfigPath = '/mnt/f/WINDSURF/neliti_code/aitrading/project/backend/api-gateway/config/gateway.config.js';
    let gatewayConfigValid = false;

    try {
      if (fs.existsSync(gatewayConfigPath)) {
        delete require.cache[require.resolve(gatewayConfigPath)];
        const gatewayConfig = require(gatewayConfigPath);
        gatewayConfigValid = gatewayConfig && gatewayConfig.server && gatewayConfig.server.port;
        console.log(`   API Gateway Config: ${gatewayConfigValid ? '✅ Valid' : '❌ Invalid'}`);
      } else {
        console.log(`   API Gateway Config: ❌ File not found`);
      }
    } catch (error) {
      console.log(`   API Gateway Config: ❌ Error loading - ${error.message}`);
    }

    // Check environment variables
    const requiredEnvVars = config.workspace.expectedEnvVars;
    const presentEnvVars = requiredEnvVars.filter(envVar => process.env[envVar]);

    console.log(`   Environment Variables: ${presentEnvVars.length}/${requiredEnvVars.length} present`);
    console.log(`   Present: [${presentEnvVars.join(', ')}]`);

    // Check backend structure
    const backendPath = '/mnt/f/WINDSURF/neliti_code/aitrading/project/backend';
    const expectedServices = ['api-gateway', 'database-service', 'data-bridge', 'central-hub'];
    const existingServices = expectedServices.filter(service => {
      const servicePath = require('path').join(backendPath, service);
      return fs.existsSync(servicePath);
    });

    console.log(`   Backend Structure: ${existingServices.length}/${expectedServices.length} services present`);
    console.log(`   Services: [${existingServices.join(', ')}]`);

    this.results.configuration = {
      gatewayConfig: gatewayConfigValid,
      envVars: {
        total: requiredEnvVars.length,
        present: presentEnvVars.length,
        missing: requiredEnvVars.filter(envVar => !process.env[envVar])
      },
      backendStructure: {
        total: expectedServices.length,
        present: existingServices.length,
        services: existingServices
      }
    };
  }

  generateSummary() {
    console.log('\n📊 Foundation Validation Summary');
    console.log('================================');

    // Service Summary
    const totalServices = Object.keys(this.results.services).length;
    const healthyServices = Object.values(this.results.services).filter(s => s.healthy).length;
    const criticalServices = Object.values(this.results.services).filter(s => s.critical).length;
    const healthyCriticalServices = Object.values(this.results.services).filter(s => s.critical && s.healthy).length;

    console.log(`\n🏥 Services: ${healthyServices}/${totalServices} healthy`);
    console.log(`   Critical: ${healthyCriticalServices}/${criticalServices} healthy`);

    Object.entries(this.results.services).forEach(([name, service]) => {
      const icon = service.healthy ? '🟢' : (service.critical ? '🔴' : '🟡');
      console.log(`   ${icon} ${name}: ${service.healthy ? 'Healthy' : 'Unhealthy'}${service.critical ? ' (critical)' : ''}`);
    });

    // Database Summary
    const totalDbs = Object.keys(this.results.databases).length;
    const connectedDbs = Object.values(this.results.databases).filter(db => db.connected).length;

    console.log(`\n🗄️  Databases: ${connectedDbs}/${totalDbs} connected`);
    Object.entries(this.results.databases).forEach(([name, db]) => {
      const icon = db.connected ? '🟢' : '🔴';
      console.log(`   ${icon} ${name}: ${db.connected ? 'Connected' : 'Failed'}`);
    });

    // Configuration Summary
    const config = this.results.configuration;
    console.log(`\n⚙️  Configuration:`);
    console.log(`   Gateway Config: ${config.gatewayConfig ? '✅' : '❌'}`);
    console.log(`   Environment Variables: ${config.envVars.present}/${config.envVars.total}`);
    console.log(`   Backend Structure: ${config.backendStructure.present}/${config.backendStructure.total}`);

    // Overall Assessment
    const foundationScore = this.calculateFoundationScore();
    console.log(`\n🎯 Foundation Score: ${foundationScore}%`);

    let status, recommendation;
    if (foundationScore >= 90) {
      status = '🎉 Excellent - Ready for LEVEL 2';
      recommendation = 'Foundation is solid. Proceed with LEVEL 2 Connectivity.';
    } else if (foundationScore >= 75) {
      status = '✅ Good - Minor issues';
      recommendation = 'Foundation is mostly ready. Address minor issues before LEVEL 2.';
    } else if (foundationScore >= 50) {
      status = '⚠️  Fair - Needs attention';
      recommendation = 'Foundation needs work. Fix critical issues before proceeding.';
    } else {
      status = '❌ Poor - Major issues';
      recommendation = 'Foundation requires significant work before LEVEL 2.';
    }

    console.log(`\n${status}`);
    console.log(`💡 ${recommendation}`);

    this.results.summary = {
      foundationScore,
      status,
      recommendation,
      services: { total: totalServices, healthy: healthyServices, critical: criticalServices, healthyCritical: healthyCriticalServices },
      databases: { total: totalDbs, connected: connectedDbs },
      configuration: config
    };

    return this.results.summary;
  }

  calculateFoundationScore() {
    let score = 0;
    let maxScore = 0;

    // Services (40% weight)
    const serviceWeight = 40;
    const totalServices = Object.keys(this.results.services).length;
    const healthyServices = Object.values(this.results.services).filter(s => s.healthy).length;
    score += (healthyServices / totalServices) * serviceWeight;
    maxScore += serviceWeight;

    // Critical Services (30% weight)
    const criticalWeight = 30;
    const criticalServices = Object.values(this.results.services).filter(s => s.critical);
    const healthyCriticalServices = criticalServices.filter(s => s.healthy);
    if (criticalServices.length > 0) {
      score += (healthyCriticalServices.length / criticalServices.length) * criticalWeight;
    }
    maxScore += criticalWeight;

    // Databases (20% weight)
    const dbWeight = 20;
    const totalDbs = Object.keys(this.results.databases).length;
    const connectedDbs = Object.values(this.results.databases).filter(db => db.connected).length;
    if (totalDbs > 0) {
      score += (connectedDbs / totalDbs) * dbWeight;
    }
    maxScore += dbWeight;

    // Configuration (10% weight)
    const configWeight = 10;
    const config = this.results.configuration;
    let configScore = 0;
    if (config.gatewayConfig) configScore += 0.4;
    if (config.envVars.present > 0) configScore += 0.3;
    if (config.backendStructure.present >= 3) configScore += 0.3;
    score += configScore * configWeight;
    maxScore += configWeight;

    return Math.round((score / maxScore) * 100);
  }

  async validate() {
    console.log('🚀 LEVEL 1 Foundation Validator');
    console.log('===============================');

    try {
      await this.validateServices();
      await this.validateDatabases();
      await this.validateConfiguration();

      const summary = this.generateSummary();

      // Save results
      const fs = require('fs');
      const path = require('path');
      const resultsDir = path.join(__dirname, 'results');

      if (!fs.existsSync(resultsDir)) {
        fs.mkdirSync(resultsDir, { recursive: true });
      }

      const resultsFile = path.join(resultsDir, `foundation-validation-${Date.now()}.json`);
      fs.writeFileSync(resultsFile, JSON.stringify(this.results, null, 2));

      console.log(`\n📄 Results saved to: ${resultsFile}`);

      return summary;

    } catch (error) {
      console.error('\n❌ Validation failed:', error);
      throw error;
    } finally {
      await helpers.cleanup();
    }
  }
}

// Run if called directly
if (require.main === module) {
  const validator = new FoundationValidator();
  validator.validate()
    .then(summary => {
      const exitCode = summary.foundationScore >= 75 ? 0 : 1;
      process.exit(exitCode);
    })
    .catch(error => {
      console.error('❌ Validation error:', error);
      process.exit(1);
    });
}

module.exports = FoundationValidator;