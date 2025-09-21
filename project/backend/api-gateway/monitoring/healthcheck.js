#!/usr/bin/env node

/**
 * Standalone health check script for Docker and Kubernetes
 * Usage: node healthcheck.js [--detailed] [--timeout=5000]
 */

const http = require('http');
const https = require('https');
const url = require('url');

class HealthChecker {
  constructor(options = {}) {
    this.timeout = options.timeout || 5000;
    this.detailed = options.detailed || false;
    this.host = options.host || 'localhost';
    this.port = options.port || process.env.GATEWAY_PORT || 8000;
    this.protocol = options.protocol || 'http';
  }

  async check() {
    try {
      const endpoint = this.detailed ? '/health/detailed' : '/health';
      const checkUrl = `${this.protocol}://${this.host}:${this.port}${endpoint}`;

      console.log(`Checking health at ${checkUrl}`);

      const result = await this.makeRequest(checkUrl);

      if (result.statusCode === 200) {
        console.log('✅ Health check passed');
        if (this.detailed && result.data) {
          console.log('📊 Health details:');
          console.log(JSON.stringify(result.data, null, 2));
        }
        process.exit(0);
      } else {
        console.error(`❌ Health check failed with status ${result.statusCode}`);
        if (result.data) {
          console.error('Response:', JSON.stringify(result.data, null, 2));
        }
        process.exit(1);
      }
    } catch (error) {
      console.error('❌ Health check error:', error.message);
      process.exit(1);
    }
  }

  makeRequest(checkUrl) {
    return new Promise((resolve, reject) => {
      const parsedUrl = url.parse(checkUrl);
      const client = parsedUrl.protocol === 'https:' ? https : http;

      const options = {
        hostname: parsedUrl.hostname,
        port: parsedUrl.port,
        path: parsedUrl.path,
        method: 'GET',
        timeout: this.timeout,
        headers: {
          'User-Agent': 'HealthChecker/1.0.0',
          'Accept': 'application/json'
        }
      };

      const req = client.request(options, (res) => {
        let data = '';

        res.on('data', (chunk) => {
          data += chunk;
        });

        res.on('end', () => {
          try {
            const parsedData = data ? JSON.parse(data) : null;
            resolve({
              statusCode: res.statusCode,
              data: parsedData,
              headers: res.headers
            });
          } catch (error) {
            resolve({
              statusCode: res.statusCode,
              data: data,
              headers: res.headers
            });
          }
        });
      });

      req.on('timeout', () => {
        req.destroy();
        reject(new Error(`Health check timeout after ${this.timeout}ms`));
      });

      req.on('error', (error) => {
        reject(error);
      });

      req.end();
    });
  }

  static parseArgs(args) {
    const options = {};

    for (const arg of args) {
      if (arg === '--detailed') {
        options.detailed = true;
      } else if (arg.startsWith('--timeout=')) {
        options.timeout = parseInt(arg.split('=')[1], 10);
      } else if (arg.startsWith('--host=')) {
        options.host = arg.split('=')[1];
      } else if (arg.startsWith('--port=')) {
        options.port = parseInt(arg.split('=')[1], 10);
      } else if (arg.startsWith('--protocol=')) {
        options.protocol = arg.split('=')[1];
      }
    }

    return options;
  }
}

// Comprehensive health check for monitoring systems
class ComprehensiveHealthChecker extends HealthChecker {
  async checkAll() {
    const results = {
      gateway: null,
      services: {},
      overall: 'unknown',
      timestamp: new Date().toISOString()
    };

    try {
      // Check gateway health
      results.gateway = await this.checkGateway();

      // Check individual services if gateway is healthy
      if (results.gateway.healthy) {
        results.services = await this.checkServices();
      }

      // Determine overall health
      results.overall = this.determineOverallHealth(results);

      console.log('🔍 Comprehensive Health Check Results:');
      console.log(JSON.stringify(results, null, 2));

      if (results.overall === 'healthy') {
        process.exit(0);
      } else {
        process.exit(1);
      }

    } catch (error) {
      console.error('❌ Comprehensive health check failed:', error.message);
      process.exit(1);
    }
  }

  async checkGateway() {
    try {
      const result = await this.makeRequest(`${this.protocol}://${this.host}:${this.port}/health`);
      return {
        healthy: result.statusCode === 200,
        statusCode: result.statusCode,
        data: result.data
      };
    } catch (error) {
      return {
        healthy: false,
        error: error.message
      };
    }
  }

  async checkServices() {
    const services = {};
    const serviceNames = ['auth', 'users', 'trading', 'market', 'ai', 'notifications'];

    const checks = serviceNames.map(async (serviceName) => {
      try {
        const result = await this.makeRequest(
          `${this.protocol}://${this.host}:${this.port}/health/services/${serviceName}`
        );
        services[serviceName] = {
          healthy: result.statusCode === 200,
          statusCode: result.statusCode,
          data: result.data
        };
      } catch (error) {
        services[serviceName] = {
          healthy: false,
          error: error.message
        };
      }
    });

    await Promise.all(checks);
    return services;
  }

  determineOverallHealth(results) {
    if (!results.gateway?.healthy) {
      return 'unhealthy';
    }

    const serviceHealths = Object.values(results.services);
    if (serviceHealths.length === 0) {
      return results.gateway.healthy ? 'healthy' : 'unhealthy';
    }

    const healthyServices = serviceHealths.filter(s => s.healthy).length;
    const totalServices = serviceHealths.length;

    if (healthyServices === totalServices) {
      return 'healthy';
    } else if (healthyServices >= totalServices * 0.7) {
      return 'degraded';
    } else {
      return 'unhealthy';
    }
  }
}

// Main execution
if (require.main === module) {
  const args = process.argv.slice(2);
  const options = HealthChecker.parseArgs(args);

  if (args.includes('--comprehensive')) {
    const checker = new ComprehensiveHealthChecker(options);
    checker.checkAll();
  } else {
    const checker = new HealthChecker(options);
    checker.check();
  }
}

module.exports = { HealthChecker, ComprehensiveHealthChecker };