#!/usr/bin/env node

const { exec } = require('child_process');
const { promisify } = require('util');
const fs = require('fs').promises;
const path = require('path');
const axios = require('axios');

const execAsync = promisify(exec);

/**
 * Test environment setup script
 * Configures and initializes the complete testing environment
 */
class TestEnvironmentSetup {
  constructor() {
    this.config = {
      dockerComposeFile: 'docker-compose.test.yml',
      maxWaitTime: 300000, // 5 minutes
      healthCheckInterval: 5000, // 5 seconds
      services: [
        { name: 'postgres', url: 'postgresql://test:test@localhost:5432/aitrading_test' },
        { name: 'redis', url: 'redis://localhost:6379' },
        { name: 'api-gateway', url: 'http://localhost:3000/health' },
        { name: 'user-service', url: 'http://localhost:8001/health' },
        { name: 'trading-engine', url: 'http://localhost:8002/health' },
        { name: 'data-bridge', url: 'http://localhost:8003/health' }
      ]
    };
  }

  /**
   * Main setup orchestration
   */
  async run() {
    console.log('🚀 Starting test environment setup...');

    try {
      await this.validatePrerequisites();
      await this.setupEnvironmentVariables();
      await this.createDockerNetwork();
      await this.startServices();
      await this.waitForServices();
      await this.initializeDatabase();
      await this.seedTestData();
      await this.validateEnvironment();

      console.log('✅ Test environment setup completed successfully!');

      // Output connection information
      this.displayConnectionInfo();

    } catch (error) {
      console.error('❌ Test environment setup failed:', error.message);
      await this.cleanup();
      process.exit(1);
    }
  }

  /**
   * Validate prerequisites are installed
   */
  async validatePrerequisites() {
    console.log('📋 Validating prerequisites...');

    const requirements = [
      { command: 'docker --version', name: 'Docker' },
      { command: 'docker-compose --version', name: 'Docker Compose' },
      { command: 'node --version', name: 'Node.js' }
    ];

    for (const req of requirements) {
      try {
        await execAsync(req.command);
        console.log(`✅ ${req.name} is available`);
      } catch (error) {
        throw new Error(`${req.name} is not installed or not accessible`);
      }
    }
  }

  /**
   * Setup environment variables
   */
  async setupEnvironmentVariables() {
    console.log('🔧 Setting up environment variables...');

    const envVars = {
      NODE_ENV: 'test',
      DATABASE_URL: 'postgresql://test:test@localhost:5432/aitrading_test',
      REDIS_URL: 'redis://localhost:6379/1',
      API_BASE_URL: 'http://localhost:3000',
      JWT_SECRET: 'test-jwt-secret-key-for-e2e-testing',
      API_KEY: 'test-api-key',
      LOG_LEVEL: 'debug',
      TEST_MODE: 'true',
      PLAYWRIGHT_BROWSERS_PATH: './playwright-browsers',
      PWTEST_SKIP_TEST_OUTPUT: 'true'
    };

    const envContent = Object.entries(envVars)
      .map(([key, value]) => `${key}=${value}`)
      .join('\n');

    await fs.writeFile('.env.test', envContent);
    console.log('✅ Environment variables configured');
  }

  /**
   * Create Docker network for test services
   */
  async createDockerNetwork() {
    console.log('🌐 Creating Docker network...');

    try {
      await execAsync('docker network create aitrading_test_network --driver bridge || true');
      console.log('✅ Docker network created');
    } catch (error) {
      console.log('ℹ️ Docker network already exists or creation failed');
    }
  }

  /**
   * Start all required services
   */
  async startServices() {
    console.log('🏗️ Starting test services...');

    // Pull latest images first
    console.log('📦 Pulling required Docker images...');
    await execAsync(`docker-compose -f ${this.config.dockerComposeFile} pull`);

    // Build custom images
    console.log('🔨 Building custom Docker images...');
    await execAsync(`docker-compose -f ${this.config.dockerComposeFile} build`);

    // Start services
    console.log('🚀 Starting services...');
    await execAsync(`docker-compose -f ${this.config.dockerComposeFile} up -d`);

    console.log('✅ Services started');
  }

  /**
   * Wait for all services to be healthy
   */
  async waitForServices() {
    console.log('⏳ Waiting for services to be ready...');

    const startTime = Date.now();

    while (Date.now() - startTime < this.config.maxWaitTime) {
      let allHealthy = true;

      for (const service of this.config.services) {
        const isHealthy = await this.checkServiceHealth(service);

        if (!isHealthy) {
          allHealthy = false;
          console.log(`⏳ Waiting for ${service.name}...`);
        } else {
          console.log(`✅ ${service.name} is healthy`);
        }
      }

      if (allHealthy) {
        console.log('✅ All services are ready!');
        return;
      }

      await this.sleep(this.config.healthCheckInterval);
    }

    throw new Error('Services did not become healthy within the timeout period');
  }

  /**
   * Check if a service is healthy
   */
  async checkServiceHealth(service) {
    try {
      if (service.name === 'postgres') {
        await execAsync('pg_isready -h localhost -p 5432 -U test -d aitrading_test');
        return true;
      }

      if (service.name === 'redis') {
        await execAsync('redis-cli -h localhost -p 6379 ping');
        return true;
      }

      // HTTP health check
      const response = await axios.get(service.url, { timeout: 5000 });
      return response.status === 200;

    } catch (error) {
      return false;
    }
  }

  /**
   * Initialize database schemas and structures
   */
  async initializeDatabase() {
    console.log('🗄️ Initializing database...');

    try {
      // Run database migrations/initialization
      const initScript = path.join(__dirname, 'init-database.sql');

      try {
        await fs.access(initScript);
        await execAsync(`psql postgresql://test:test@localhost:5432/aitrading_test -f ${initScript}`);
        console.log('✅ Database initialized from script');
      } catch (error) {
        console.log('ℹ️ No database initialization script found, skipping');
      }

      // Verify database connection
      await execAsync('psql postgresql://test:test@localhost:5432/aitrading_test -c "SELECT 1;"');
      console.log('✅ Database connection verified');

    } catch (error) {
      console.warn('⚠️ Database initialization warning:', error.message);
    }
  }

  /**
   * Seed test data
   */
  async seedTestData() {
    console.log('🌱 Seeding test data...');

    try {
      // Use the TestDataManager to seed data
      const { TestDataManager } = require('../utils/test-data-manager');
      const testDataManager = new TestDataManager();

      await testDataManager.seedTestData();
      console.log('✅ Test data seeded');

    } catch (error) {
      console.warn('⚠️ Test data seeding warning:', error.message);
    }
  }

  /**
   * Validate the complete environment
   */
  async validateEnvironment() {
    console.log('🔍 Validating test environment...');

    const validations = [
      this.validateDatabaseConnection(),
      this.validateRedisConnection(),
      this.validateAPIEndpoints(),
      this.validateWebInterface()
    ];

    try {
      await Promise.all(validations);
      console.log('✅ Environment validation passed');
    } catch (error) {
      throw new Error(`Environment validation failed: ${error.message}`);
    }
  }

  /**
   * Validate database connection and basic operations
   */
  async validateDatabaseConnection() {
    try {
      await execAsync('psql postgresql://test:test@localhost:5432/aitrading_test -c "SELECT COUNT(*) FROM pg_tables;"');
    } catch (error) {
      throw new Error('Database connection validation failed');
    }
  }

  /**
   * Validate Redis connection
   */
  async validateRedisConnection() {
    try {
      await execAsync('redis-cli -h localhost -p 6379 set test_key test_value');
      await execAsync('redis-cli -h localhost -p 6379 get test_key');
      await execAsync('redis-cli -h localhost -p 6379 del test_key');
    } catch (error) {
      throw new Error('Redis connection validation failed');
    }
  }

  /**
   * Validate API endpoints
   */
  async validateAPIEndpoints() {
    const endpoints = [
      'http://localhost:3000/health',
      'http://localhost:8001/health',
      'http://localhost:8002/health',
      'http://localhost:8003/health'
    ];

    for (const endpoint of endpoints) {
      try {
        const response = await axios.get(endpoint, { timeout: 5000 });
        if (response.status !== 200) {
          throw new Error(`Endpoint ${endpoint} returned status ${response.status}`);
        }
      } catch (error) {
        throw new Error(`API endpoint validation failed for ${endpoint}: ${error.message}`);
      }
    }
  }

  /**
   * Validate web interface
   */
  async validateWebInterface() {
    try {
      const response = await axios.get('http://localhost:3001', { timeout: 10000 });
      if (response.status !== 200) {
        throw new Error(`Web interface returned status ${response.status}`);
      }
    } catch (error) {
      console.warn('⚠️ Web interface validation warning:', error.message);
    }
  }

  /**
   * Display connection information
   */
  displayConnectionInfo() {
    console.log('\n📊 Test Environment Ready!');
    console.log('==========================================');
    console.log('🌐 Web Interface:     http://localhost:3001');
    console.log('🔌 API Gateway:       http://localhost:3000');
    console.log('👤 User Service:      http://localhost:8001');
    console.log('💹 Trading Engine:    http://localhost:8002');
    console.log('📈 Data Bridge:       http://localhost:8003');
    console.log('🗄️ Database:          postgresql://test:test@localhost:5432/aitrading_test');
    console.log('🔴 Redis:             redis://localhost:6379');
    console.log('📊 Grafana:           http://localhost:3001 (admin/test)');
    console.log('🎯 Prometheus:        http://localhost:9090');
    console.log('🐰 RabbitMQ:          http://localhost:15672 (test/test)');
    console.log('==========================================\n');

    console.log('🧪 Ready for E2E testing!');
    console.log('📝 Run tests with: npm run test:e2e');
    console.log('🎭 Run with UI: npm run test:e2e:ui');
    console.log('🔧 Debug mode: npm run test:e2e:debug\n');
  }

  /**
   * Cleanup on failure
   */
  async cleanup() {
    console.log('🧹 Cleaning up on failure...');

    try {
      await execAsync(`docker-compose -f ${this.config.dockerComposeFile} down -v --remove-orphans`);
      await execAsync('docker network rm aitrading_test_network || true');
    } catch (error) {
      console.warn('⚠️ Cleanup warning:', error.message);
    }
  }

  /**
   * Sleep utility
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Main execution
if (require.main === module) {
  const setup = new TestEnvironmentSetup();
  setup.run().catch(error => {
    console.error('Setup failed:', error);
    process.exit(1);
  });
}

module.exports = TestEnvironmentSetup;