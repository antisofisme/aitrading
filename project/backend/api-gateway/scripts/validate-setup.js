#!/usr/bin/env node

/**
 * API Gateway Setup Validation Script
 *
 * Validates that the enhanced API Gateway can be deployed and communicate
 * with all required services and databases.
 */

const axios = require('axios');
const fs = require('fs');
const path = require('path');

class SetupValidator {
  constructor() {
    this.results = [];
    this.configServiceURL = 'http://localhost:8012';
    this.databaseConnections = {
      postgres: { host: 'localhost', port: 5432 },
      dragonflydb: { host: 'localhost', port: 6379 },
      clickhouse: { host: 'localhost', port: 8123 },
      weaviate: { host: 'localhost', port: 8080 },
      arangodb: { host: 'localhost', port: 8529 },
      redis: { host: 'localhost', port: 6380 }
    };
  }

  async validate() {
    console.log('🔍 Validating Enhanced API Gateway Setup...\n');

    const validations = [
      { name: 'Check Enhanced Server File', test: () => this.checkEnhancedServerFile() },
      { name: 'Check Required Dependencies', test: () => this.checkDependencies() },
      { name: 'Validate Configuration Service', test: () => this.validateConfigurationService() },
      { name: 'Check Database Connectivity', test: () => this.checkDatabaseConnectivity() },
      { name: 'Validate File Structure', test: () => this.validateFileStructure() },
      { name: 'Check Environment Variables', test: () => this.checkEnvironmentVariables() }
    ];

    for (const validation of validations) {
      await this.runValidation(validation.name, validation.test);
    }

    this.printSummary();
  }

  async runValidation(name, testFn) {
    process.stdout.write(`Testing ${name}...`);

    try {
      await testFn();
      this.results.push({ name, status: 'PASS' });
      console.log(`\r✅ ${name} - PASSED`);
    } catch (error) {
      this.results.push({ name, status: 'FAIL', error: error.message });
      console.log(`\r❌ ${name} - FAILED`);
      console.log(`   Error: ${error.message}`);
    }
  }

  checkEnhancedServerFile() {
    const serverPath = path.join(__dirname, '..', 'src', 'new-enhanced-server.js');
    if (!fs.existsSync(serverPath)) {
      throw new Error('Enhanced server file not found');
    }

    const content = fs.readFileSync(serverPath, 'utf8');
    const requiredComponents = [
      'DatabaseManager',
      'FlowAwareErrorHandler',
      'ConfigurationServiceClient',
      'EnhancedAPIGateway'
    ];

    for (const component of requiredComponents) {
      if (!content.includes(component)) {
        throw new Error(`Missing required component: ${component}`);
      }
    }
  }

  checkDependencies() {
    const packagePath = path.join(__dirname, '..', 'package.json');
    if (!fs.existsSync(packagePath)) {
      throw new Error('package.json not found');
    }

    const packageJson = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
    const requiredDeps = [
      'pg',
      '@clickhouse/client',
      'weaviate-ts-client',
      'arangojs',
      'joi',
      'winston',
      'axios'
    ];

    for (const dep of requiredDeps) {
      if (!packageJson.dependencies[dep]) {
        throw new Error(`Missing required dependency: ${dep}`);
      }
    }
  }

  async validateConfigurationService() {
    try {
      const response = await axios.get(`${this.configServiceURL}/health`, { timeout: 5000 });

      if (response.status !== 200) {
        throw new Error(`Configuration Service returned status ${response.status}`);
      }

      const health = response.data;
      if (!health.status || health.status !== 'healthy') {
        throw new Error(`Configuration Service not healthy: ${health.status}`);
      }

      // Test Flow Registry endpoint
      try {
        await axios.get(`${this.configServiceURL}/api/v1/flows`, { timeout: 5000 });
      } catch (error) {
        if (error.response && [401, 403, 404].includes(error.response.status)) {
          // These are acceptable - service is running
        } else {
          throw new Error(`Flow Registry endpoint not accessible: ${error.message}`);
        }
      }

    } catch (error) {
      throw new Error(`Configuration Service validation failed: ${error.message}`);
    }
  }

  async checkDatabaseConnectivity() {
    const net = require('net');

    const checkPort = (host, port) => {
      return new Promise((resolve) => {
        const socket = new net.Socket();
        socket.setTimeout(2000);

        socket.on('connect', () => {
          socket.destroy();
          resolve(true);
        });

        socket.on('error', () => {
          resolve(false);
        });

        socket.on('timeout', () => {
          socket.destroy();
          resolve(false);
        });

        socket.connect(port, host);
      });
    };

    const connectionResults = {};

    for (const [dbName, config] of Object.entries(this.databaseConnections)) {
      const isConnectable = await checkPort(config.host, config.port);
      connectionResults[dbName] = isConnectable;
    }

    const connectedDbs = Object.entries(connectionResults)
      .filter(([db, connected]) => connected)
      .map(([db]) => db);

    if (connectedDbs.length === 0) {
      throw new Error('No databases are reachable');
    }

    console.log(`\n   Connected databases: ${connectedDbs.join(', ')}`);

    const disconnectedDbs = Object.entries(connectionResults)
      .filter(([db, connected]) => !connected)
      .map(([db]) => db);

    if (disconnectedDbs.length > 0) {
      console.log(`   Disconnected databases: ${disconnectedDbs.join(', ')}`);
    }
  }

  validateFileStructure() {
    const requiredFiles = [
      'src/config/DatabaseManager.js',
      'src/middleware/FlowAwareErrorHandler.js',
      'src/services/ConfigurationServiceClient.js',
      'tests/integration/enhanced-gateway.test.js',
      'scripts/test-deployment.js'
    ];

    for (const file of requiredFiles) {
      const filePath = path.join(__dirname, '..', file);
      if (!fs.existsSync(filePath)) {
        throw new Error(`Required file missing: ${file}`);
      }
    }
  }

  checkEnvironmentVariables() {
    const requiredEnvVars = [
      'POSTGRES_URL',
      'DRAGONFLY_HOST',
      'CLICKHOUSE_HOST',
      'WEAVIATE_HOST',
      'ARANGO_URL',
      'FLOW_REGISTRY_URL'
    ];

    const missingVars = [];

    for (const envVar of requiredEnvVars) {
      if (!process.env[envVar]) {
        missingVars.push(envVar);
      }
    }

    if (missingVars.length > 0) {
      console.log(`\n   Missing environment variables: ${missingVars.join(', ')}`);
      console.log('   Note: These will use default values if not set');
    }
  }

  printSummary() {
    const passed = this.results.filter(r => r.status === 'PASS').length;
    const failed = this.results.filter(r => r.status === 'FAIL').length;

    console.log('\n' + '='.repeat(60));
    console.log('📊 VALIDATION SUMMARY');
    console.log('='.repeat(60));

    console.log(`✅ Passed: ${passed}`);
    console.log(`❌ Failed: ${failed}`);

    if (failed === 0) {
      console.log('\n🎉 Enhanced API Gateway setup is valid and ready for deployment!');
      console.log('\nNext steps:');
      console.log('1. Run: npm run start:enhanced');
      console.log('2. Test: npm run test:integration');
      console.log('3. Validate: node scripts/test-deployment.js');
    } else {
      console.log('\n⚠️  Some validations failed. Please fix the issues before deployment.');
      process.exit(1);
    }
  }
}

// Run validation if called directly
if (require.main === module) {
  const validator = new SetupValidator();
  validator.validate().catch(error => {
    console.error('💥 Validation failed:', error.message);
    process.exit(1);
  });
}

module.exports = SetupValidator;