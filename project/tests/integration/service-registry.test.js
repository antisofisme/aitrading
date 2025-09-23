/**
 * Service Registry Integration Tests
 * Tests Configuration Service as central registry and service discovery
 */

const request = require('supertest');
const { expect } = require('chai');
const axios = require('axios');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs-extra');

describe('Service Registry Integration Tests', () => {
  let configurationService;
  let apiGateway;
  let databaseService;
  const services = new Map();
  const serviceConfig = {
    configurationService: {
      port: 3001,
      host: 'localhost',
      name: 'configuration-service'
    },
    apiGateway: {
      port: 3000,
      host: 'localhost',
      name: 'api-gateway'
    },
    databaseService: {
      port: 3002,
      host: 'localhost',
      name: 'database-service'
    }
  };

  before(async function() {
    this.timeout(30000);
    
    // Start Configuration Service first (acts as service registry)
    console.log('Starting Configuration Service...');
    configurationService = spawn('node', [
      path.join(__dirname, '../../backend/configuration-service/src/index.js')
    ], {
      env: {
        ...process.env,
        PORT: serviceConfig.configurationService.port,
        NODE_ENV: 'test',
        DB_HOST: 'localhost',
        DB_PORT: 5432,
        DB_NAME: 'config_test_db',
        DB_USER: 'test_user',
        DB_PASSWORD: 'test_password'
      }
    });

    // Wait for Configuration Service to be ready
    await waitForService(serviceConfig.configurationService);
    console.log('Configuration Service ready');

    // Start API Gateway
    console.log('Starting API Gateway...');
    apiGateway = spawn('node', [
      path.join(__dirname, '../../backend/api-gateway/src/index.js')
    ], {
      env: {
        ...process.env,
        PORT: serviceConfig.apiGateway.port,
        NODE_ENV: 'test',
        CONFIG_SERVICE_URL: `http://localhost:${serviceConfig.configurationService.port}`
      }
    });

    await waitForService(serviceConfig.apiGateway);
    console.log('API Gateway ready');

    // Start Database Service
    console.log('Starting Database Service...');
    databaseService = spawn('node', [
      path.join(__dirname, '../../backend/database-service/src/index.js')
    ], {
      env: {
        ...process.env,
        PORT: serviceConfig.databaseService.port,
        NODE_ENV: 'test',
        CONFIG_SERVICE_URL: `http://localhost:${serviceConfig.configurationService.port}`
      }
    });

    await waitForService(serviceConfig.databaseService);
    console.log('Database Service ready');

    // Register services in the configuration service registry
    await registerServices();
  });

  after(async function() {
    this.timeout(10000);
    
    // Gracefully shutdown services
    const shutdownPromises = [];
    
    if (configurationService) {
      shutdownPromises.push(shutdownService(configurationService, 'Configuration Service'));
    }
    if (apiGateway) {
      shutdownPromises.push(shutdownService(apiGateway, 'API Gateway'));
    }
    if (databaseService) {
      shutdownPromises.push(shutdownService(databaseService, 'Database Service'));
    }

    await Promise.all(shutdownPromises);
  });

  describe('Service Registration', () => {
    it('should register a new service in the registry', async () => {
      const serviceData = {
        name: 'test-service',
        version: '1.0.0',
        host: 'localhost',
        port: 3003,
        healthCheckUrl: '/health',
        endpoints: [
          { path: '/api/test', method: 'GET' },
          { path: '/api/test', method: 'POST' }
        ],
        tags: ['test', 'microservice'],
        metadata: {
          description: 'Test service for integration testing'
        }
      };

      const response = await axios.post(
        `http://localhost:${serviceConfig.configurationService.port}/api/services/register`,
        serviceData
      );

      expect(response.status).to.equal(201);
      expect(response.data.success).to.be.true;
      expect(response.data.service).to.include({
        name: serviceData.name,
        version: serviceData.version,
        host: serviceData.host,
        port: serviceData.port
      });
    });

    it('should list all registered services', async () => {
      const response = await axios.get(
        `http://localhost:${serviceConfig.configurationService.port}/api/services`
      );

      expect(response.status).to.equal(200);
      expect(response.data.success).to.be.true;
      expect(response.data.services).to.be.an('array');
      expect(response.data.services.length).to.be.at.least(3); // config, api-gateway, database
    });

    it('should discover services by name', async () => {
      const response = await axios.get(
        `http://localhost:${serviceConfig.configurationService.port}/api/services/discover/api-gateway`
      );

      expect(response.status).to.equal(200);
      expect(response.data.success).to.be.true;
      expect(response.data.service).to.include({
        name: 'api-gateway'
      });
    });

    it('should discover services by tags', async () => {
      const response = await axios.get(
        `http://localhost:${serviceConfig.configurationService.port}/api/services/discover?tags=gateway`
      );

      expect(response.status).to.equal(200);
      expect(response.data.success).to.be.true;
      expect(response.data.services).to.be.an('array');
    });
  });

  describe('Service Health Monitoring', () => {
    it('should monitor service health status', async () => {
      const response = await axios.get(
        `http://localhost:${serviceConfig.configurationService.port}/api/services/health`
      );

      expect(response.status).to.equal(200);
      expect(response.data.success).to.be.true;
      expect(response.data.healthStatus).to.be.an('object');
      
      // Check that all services are healthy
      const healthStatuses = Object.values(response.data.healthStatus);
      healthStatuses.forEach(status => {
        expect(status.healthy).to.be.true;
      });
    });

    it('should detect unhealthy service', async function() {
      this.timeout(15000);
      
      // Temporarily stop database service to simulate unhealthy state
      if (databaseService) {
        databaseService.kill('SIGTERM');
        await new Promise(resolve => setTimeout(resolve, 2000));
      }

      const response = await axios.get(
        `http://localhost:${serviceConfig.configurationService.port}/api/services/health`
      );

      expect(response.status).to.equal(200);
      const databaseHealth = response.data.healthStatus['database-service'];
      expect(databaseHealth.healthy).to.be.false;

      // Restart database service
      databaseService = spawn('node', [
        path.join(__dirname, '../../backend/database-service/src/index.js')
      ], {
        env: {
          ...process.env,
          PORT: serviceConfig.databaseService.port,
          NODE_ENV: 'test',
          CONFIG_SERVICE_URL: `http://localhost:${serviceConfig.configurationService.port}`
        }
      });

      await waitForService(serviceConfig.databaseService);
    });
  });

  describe('Configuration Management', () => {
    it('should store and retrieve service configurations', async () => {
      const configData = {
        key: 'api-gateway.rate-limit',
        value: {
          windowMs: 15 * 60 * 1000, // 15 minutes
          max: 100, // limit each IP to 100 requests per windowMs
          message: 'Too many requests, please try again later.'
        },
        type: 'object',
        environment: 'test',
        description: 'Rate limiting configuration for API Gateway'
      };

      // Store configuration
      const setResponse = await axios.post(
        `http://localhost:${serviceConfig.configurationService.port}/api/config`,
        configData
      );

      expect(setResponse.status).to.equal(201);
      expect(setResponse.data.success).to.be.true;

      // Retrieve configuration
      const getResponse = await axios.get(
        `http://localhost:${serviceConfig.configurationService.port}/api/config/api-gateway.rate-limit?environment=test`
      );

      expect(getResponse.status).to.equal(200);
      expect(getResponse.data.success).to.be.true;
      expect(getResponse.data.configuration.value).to.deep.equal(configData.value);
    });

    it('should handle tenant-specific configurations', async () => {
      const tenantConfig = {
        key: 'database.connection-pool',
        value: {
          min: 2,
          max: 20,
          acquireTimeoutMillis: 30000
        },
        type: 'object',
        environment: 'test',
        tenantId: 'tenant-123',
        description: 'Database connection pool for tenant 123'
      };

      const response = await axios.post(
        `http://localhost:${serviceConfig.configurationService.port}/api/config`,
        tenantConfig
      );

      expect(response.status).to.equal(201);
      expect(response.data.configuration.tenantId).to.equal('tenant-123');
    });
  });

  describe('Service Communication', () => {
    it('should facilitate service-to-service communication through registry', async () => {
      // API Gateway discovers Database Service through Configuration Service
      const discoveryResponse = await axios.get(
        `http://localhost:${serviceConfig.apiGateway.port}/api/internal/discover/database-service`
      );

      expect(discoveryResponse.status).to.equal(200);
      expect(discoveryResponse.data.service).to.include({
        name: 'database-service'
      });
    });

    it('should handle service dependency resolution', async () => {
      const dependencyResponse = await axios.get(
        `http://localhost:${serviceConfig.configurationService.port}/api/services/dependencies/api-gateway`
      );

      expect(dependencyResponse.status).to.equal(200);
      expect(dependencyResponse.data.dependencies).to.be.an('array');
      expect(dependencyResponse.data.dependencies).to.include.members([
        'configuration-service',
        'database-service'
      ]);
    });
  });

  // Helper functions
  async function waitForService(serviceConfig, timeout = 15000) {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
      try {
        const response = await axios.get(`http://${serviceConfig.host}:${serviceConfig.port}/health`);
        if (response.status === 200) {
          return true;
        }
      } catch (error) {
        // Service not ready yet, continue waiting
      }
      
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    throw new Error(`Service ${serviceConfig.name} failed to start within ${timeout}ms`);
  }

  async function shutdownService(serviceProcess, serviceName) {
    return new Promise((resolve) => {
      serviceProcess.kill('SIGTERM');
      serviceProcess.on('exit', () => {
        console.log(`${serviceName} shut down`);
        resolve();
      });
      
      // Force kill after 5 seconds
      setTimeout(() => {
        serviceProcess.kill('SIGKILL');
        resolve();
      }, 5000);
    });
  }

  async function registerServices() {
    const servicesToRegister = [
      {
        name: 'api-gateway',
        version: '1.0.0',
        host: 'localhost',
        port: serviceConfig.apiGateway.port,
        healthCheckUrl: '/health',
        endpoints: [
          { path: '/api/*', method: 'ALL' }
        ],
        tags: ['gateway', 'proxy'],
        metadata: {
          description: 'API Gateway for routing requests'
        }
      },
      {
        name: 'database-service',
        version: '1.0.0',
        host: 'localhost',
        port: serviceConfig.databaseService.port,
        healthCheckUrl: '/health',
        endpoints: [
          { path: '/api/database/*', method: 'ALL' }
        ],
        tags: ['database', 'persistence'],
        metadata: {
          description: 'Database service for data operations'
        }
      }
    ];

    for (const service of servicesToRegister) {
      try {
        await axios.post(
          `http://localhost:${serviceConfig.configurationService.port}/api/services/register`,
          service
        );
      } catch (error) {
        console.warn(`Failed to register service ${service.name}:`, error.message);
      }
    }
  }
});
