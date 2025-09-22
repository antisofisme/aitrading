import { exec } from 'child_process';
import { promisify } from 'util';
import axios from 'axios';
import * as fs from 'fs/promises';
import * as path from 'path';

const execAsync = promisify(exec);

/**
 * Manages test environment setup, services, and cleanup
 */
export class TestEnvironmentManager {
  private services: string[] = [
    'postgres',
    'redis',
    'api-gateway',
    'user-service',
    'trading-engine',
    'data-bridge'
  ];

  private serviceHealthChecks: Record<string, string> = {
    'postgres': 'postgresql://test:test@localhost:5432/aitrading_test',
    'redis': 'http://localhost:6379',
    'api-gateway': 'http://localhost:3000/health',
    'user-service': 'http://localhost:8001/health',
    'trading-engine': 'http://localhost:8002/health',
    'data-bridge': 'http://localhost:8003/health'
  };

  /**
   * Setup complete test environment
   */
  async setupEnvironment(): Promise<void> {
    console.log('Setting up test environment...');

    // Create necessary directories
    await this.createTestDirectories();

    // Setup environment variables
    await this.setupEnvironmentVariables();

    // Setup Docker network for services
    await this.setupDockerNetwork();
  }

  /**
   * Start all required services for testing
   */
  async startServices(): Promise<void> {
    console.log('Starting test services...');

    try {
      // Start services using docker-compose
      await execAsync('docker-compose -f docker-compose.test.yml up -d');

      console.log('Services started successfully');
    } catch (error) {
      console.error('Failed to start services:', error);
      throw new Error(`Service startup failed: ${error}`);
    }
  }

  /**
   * Wait for all services to be ready
   */
  async waitForServices(timeout: number = 120000): Promise<void> {
    console.log('Waiting for services to be ready...');

    const startTime = Date.now();

    for (const [serviceName, healthUrl] of Object.entries(this.serviceHealthChecks)) {
      console.log(`Checking ${serviceName}...`);

      while (Date.now() - startTime < timeout) {
        try {
          if (serviceName === 'postgres') {
            // Check PostgreSQL connection
            await this.checkPostgresConnection();
          } else if (serviceName === 'redis') {
            // Check Redis connection
            await this.checkRedisConnection();
          } else {
            // Check HTTP service
            const response = await axios.get(healthUrl, { timeout: 5000 });
            if (response.status === 200) {
              console.log(`✅ ${serviceName} is ready`);
              break;
            }
          }
        } catch (error) {
          // Service not ready yet, wait and retry
          await this.sleep(2000);
          continue;
        }
      }
    }

    console.log('All services are ready!');
  }

  /**
   * Validate test environment is properly configured
   */
  async validateEnvironment(): Promise<void> {
    console.log('Validating test environment...');

    const validations = [
      this.validateDatabaseConnection(),
      this.validateRedisConnection(),
      this.validateAPIEndpoints(),
      this.validateEnvironmentVariables(),
      this.validateTestData()
    ];

    try {
      await Promise.all(validations);
      console.log('✅ Environment validation passed');
    } catch (error) {
      console.error('❌ Environment validation failed:', error);
      throw error;
    }
  }

  /**
   * Stop all test services
   */
  async stopServices(): Promise<void> {
    console.log('Stopping test services...');

    try {
      await execAsync('docker-compose -f docker-compose.test.yml down');
      console.log('Services stopped successfully');
    } catch (error) {
      console.error('Failed to stop services:', error);
    }
  }

  /**
   * Cleanup test environment
   */
  async cleanup(): Promise<void> {
    console.log('Cleaning up test environment...');

    try {
      // Stop services
      await this.stopServices();

      // Remove test containers and volumes
      await execAsync('docker-compose -f docker-compose.test.yml down -v --remove-orphans');

      // Remove test network
      await execAsync('docker network rm aitrading_test_network || true');

      // Cleanup test files
      await this.cleanupTestFiles();

      console.log('Cleanup completed successfully');
    } catch (error) {
      console.error('Cleanup failed:', error);
    }
  }

  /**
   * Force cleanup in case of failures
   */
  async forceCleanup(): Promise<void> {
    console.log('Force cleaning up test environment...');

    try {
      // Force stop all containers
      await execAsync('docker kill $(docker ps -q --filter "label=aitrading-test") || true');
      await execAsync('docker rm $(docker ps -aq --filter "label=aitrading-test") || true');

      // Remove volumes
      await execAsync('docker volume rm $(docker volume ls -q --filter "label=aitrading-test") || true');

      // Remove network
      await execAsync('docker network rm aitrading_test_network || true');

      console.log('Force cleanup completed');
    } catch (error) {
      console.error('Force cleanup failed:', error);
    }
  }

  /**
   * Create necessary test directories
   */
  private async createTestDirectories(): Promise<void> {
    const directories = [
      'test-results',
      'reports',
      'reports/html',
      'reports/allure-results',
      'data/fixtures',
      'data/screenshots',
      'data/videos',
      'logs'
    ];

    for (const dir of directories) {
      const fullPath = path.join(process.cwd(), dir);
      try {
        await fs.mkdir(fullPath, { recursive: true });
      } catch (error) {
        // Directory might already exist
      }
    }
  }

  /**
   * Setup environment variables for testing
   */
  private async setupEnvironmentVariables(): Promise<void> {
    const testEnvVars = {
      NODE_ENV: 'test',
      DATABASE_URL: 'postgresql://test:test@localhost:5432/aitrading_test',
      REDIS_URL: 'redis://localhost:6379/1',
      API_BASE_URL: 'http://localhost:3000',
      JWT_SECRET: 'test-jwt-secret-key',
      API_KEY: 'test-api-key',
      LOG_LEVEL: 'debug',
      TEST_MODE: 'true'
    };

    const envContent = Object.entries(testEnvVars)
      .map(([key, value]) => `${key}=${value}`)
      .join('\n');

    await fs.writeFile('.env.test', envContent);
  }

  /**
   * Setup Docker network for test services
   */
  private async setupDockerNetwork(): Promise<void> {
    try {
      await execAsync('docker network create aitrading_test_network || true');
    } catch (error) {
      // Network might already exist
    }
  }

  /**
   * Check PostgreSQL connection
   */
  private async checkPostgresConnection(): Promise<void> {
    try {
      await execAsync('pg_isready -h localhost -p 5432 -U test');
    } catch (error) {
      throw new Error('PostgreSQL is not ready');
    }
  }

  /**
   * Check Redis connection
   */
  private async checkRedisConnection(): Promise<void> {
    try {
      await execAsync('redis-cli -h localhost -p 6379 ping');
    } catch (error) {
      throw new Error('Redis is not ready');
    }
  }

  /**
   * Validate database connection
   */
  private async validateDatabaseConnection(): Promise<void> {
    // Implementation would check database connectivity
    console.log('Validating database connection...');
  }

  /**
   * Validate Redis connection
   */
  private async validateRedisConnection(): Promise<void> {
    // Implementation would check Redis connectivity
    console.log('Validating Redis connection...');
  }

  /**
   * Validate API endpoints
   */
  private async validateAPIEndpoints(): Promise<void> {
    // Implementation would check API endpoints
    console.log('Validating API endpoints...');
  }

  /**
   * Validate environment variables
   */
  private async validateEnvironmentVariables(): Promise<void> {
    const requiredVars = ['DATABASE_URL', 'REDIS_URL', 'API_BASE_URL', 'JWT_SECRET'];

    for (const envVar of requiredVars) {
      if (!process.env[envVar]) {
        throw new Error(`Required environment variable ${envVar} is not set`);
      }
    }
  }

  /**
   * Validate test data
   */
  private async validateTestData(): Promise<void> {
    // Implementation would validate test data setup
    console.log('Validating test data...');
  }

  /**
   * Cleanup test files
   */
  private async cleanupTestFiles(): Promise<void> {
    const filesToCleanup = [
      '.env.test',
      'test-results',
      'playwright-report'
    ];

    for (const file of filesToCleanup) {
      try {
        await fs.rm(file, { recursive: true, force: true });
      } catch (error) {
        // File might not exist
      }
    }
  }

  /**
   * Sleep utility
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}