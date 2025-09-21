/**
 * Integration Test Helpers
 * Utility functions for LEVEL 1 Foundation service testing
 */

const axios = require('axios');
const WebSocket = require('ws');
const { Pool } = require('pg');
const config = require('../config/test-config');

class TestHelpers {
  constructor() {
    this.dbPools = new Map();
  }

  /**
   * HTTP Request Helper with retry logic
   */
  async makeRequest(method, url, data = null, options = {}) {
    const maxRetries = options.retries || config.environment.retries;
    const timeout = options.timeout || config.environment.timeout;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const requestConfig = {
          method,
          url,
          timeout,
          validateStatus: () => true, // Don't throw on HTTP errors
          ...options.axiosConfig
        };

        if (data) {
          requestConfig.data = data;
        }

        const response = await axios(requestConfig);
        return response;
      } catch (error) {
        if (attempt === maxRetries) {
          throw new Error(`Request failed after ${maxRetries} attempts: ${error.message}`);
        }
        await this.sleep(1000 * attempt); // Exponential backoff
      }
    }
  }

  /**
   * Health Check Helper
   */
  async checkHealth(serviceUrl, endpoint = '/health') {
    try {
      const response = await this.makeRequest('GET', `${serviceUrl}${endpoint}`);

      return {
        isHealthy: response.status === 200,
        status: response.status,
        data: response.data,
        responseTime: response.headers['x-response-time'] || 'unknown'
      };
    } catch (error) {
      return {
        isHealthy: false,
        error: error.message,
        responseTime: 'timeout'
      };
    }
  }

  /**
   * Database Connection Helper
   */
  async testDatabaseConnection(dbConfig, dbName = 'default') {
    try {
      if (!this.dbPools.has(dbName)) {
        const pool = new Pool({
          host: dbConfig.host,
          port: dbConfig.port,
          database: dbConfig.database,
          user: dbConfig.user,
          password: dbConfig.password,
          max: 5,
          connectionTimeoutMillis: 5000,
          idleTimeoutMillis: 30000
        });
        this.dbPools.set(dbName, pool);
      }

      const pool = this.dbPools.get(dbName);
      const client = await pool.connect();

      // Test query
      const result = await client.query('SELECT NOW() as current_time, version() as pg_version');
      client.release();

      return {
        connected: true,
        database: dbConfig.database,
        currentTime: result.rows[0].current_time,
        version: result.rows[0].pg_version
      };
    } catch (error) {
      return {
        connected: false,
        database: dbConfig.database,
        error: error.message
      };
    }
  }

  /**
   * WebSocket Connection Helper
   */
  async testWebSocketConnection(wsUrl, options = {}) {
    return new Promise((resolve) => {
      const timeout = options.timeout || 5000;
      const ws = new WebSocket(wsUrl);
      let isResolved = false;

      const timeoutId = setTimeout(() => {
        if (!isResolved) {
          isResolved = true;
          ws.close();
          resolve({
            connected: false,
            error: 'Connection timeout'
          });
        }
      }, timeout);

      ws.on('open', () => {
        if (!isResolved) {
          isResolved = true;
          clearTimeout(timeoutId);

          // Send ping and wait for response
          ws.send(JSON.stringify({ type: 'ping' }));

          ws.on('message', (data) => {
            try {
              const message = JSON.parse(data.toString());
              ws.close();
              resolve({
                connected: true,
                welcomeMessage: message
              });
            } catch (error) {
              ws.close();
              resolve({
                connected: true,
                error: 'Invalid message format'
              });
            }
          });
        }
      });

      ws.on('error', (error) => {
        if (!isResolved) {
          isResolved = true;
          clearTimeout(timeoutId);
          resolve({
            connected: false,
            error: error.message
          });
        }
      });
    });
  }

  /**
   * Service Discovery Helper
   */
  async discoverServices(centralHubUrl) {
    try {
      const response = await this.makeRequest('GET', `${centralHubUrl}/api/services`);

      if (response.status === 200) {
        return {
          discovered: true,
          services: response.data.services || response.data,
          count: Array.isArray(response.data.services) ? response.data.services.length : 0
        };
      } else {
        return {
          discovered: false,
          error: `HTTP ${response.status}: ${response.statusText}`
        };
      }
    } catch (error) {
      return {
        discovered: false,
        error: error.message
      };
    }
  }

  /**
   * Performance Measurement Helper
   */
  async measurePerformance(testFunction, iterations = 5) {
    const results = [];

    for (let i = 0; i < iterations; i++) {
      const startTime = Date.now();
      try {
        await testFunction();
        const endTime = Date.now();
        results.push({
          iteration: i + 1,
          duration: endTime - startTime,
          success: true
        });
      } catch (error) {
        const endTime = Date.now();
        results.push({
          iteration: i + 1,
          duration: endTime - startTime,
          success: false,
          error: error.message
        });
      }
    }

    const successfulResults = results.filter(r => r.success);
    const avgDuration = successfulResults.length > 0
      ? successfulResults.reduce((sum, r) => sum + r.duration, 0) / successfulResults.length
      : 0;

    return {
      total: results.length,
      successful: successfulResults.length,
      failed: results.length - successfulResults.length,
      averageDuration: avgDuration,
      minDuration: successfulResults.length > 0 ? Math.min(...successfulResults.map(r => r.duration)) : 0,
      maxDuration: successfulResults.length > 0 ? Math.max(...successfulResults.map(r => r.duration)) : 0,
      successRate: (successfulResults.length / results.length) * 100,
      results
    };
  }

  /**
   * Wait/Sleep Helper
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Port Availability Checker
   */
  async isPortOpen(host, port) {
    return new Promise((resolve) => {
      const net = require('net');
      const socket = new net.Socket();

      const timeout = 3000;
      socket.setTimeout(timeout);

      socket.on('connect', () => {
        socket.destroy();
        resolve(true);
      });

      socket.on('timeout', () => {
        socket.destroy();
        resolve(false);
      });

      socket.on('error', () => {
        resolve(false);
      });

      socket.connect(port, host);
    });
  }

  /**
   * Service Startup Detector
   */
  async waitForService(serviceUrl, maxWaitTime = 30000, interval = 1000) {
    const startTime = Date.now();

    while (Date.now() - startTime < maxWaitTime) {
      try {
        const health = await this.checkHealth(serviceUrl);
        if (health.isHealthy) {
          return {
            ready: true,
            waitTime: Date.now() - startTime
          };
        }
      } catch (error) {
        // Continue waiting
      }

      await this.sleep(interval);
    }

    return {
      ready: false,
      waitTime: maxWaitTime,
      error: 'Service did not become ready within timeout'
    };
  }

  /**
   * Cleanup Helper
   */
  async cleanup() {
    // Close all database pools
    for (const [name, pool] of this.dbPools) {
      try {
        await pool.end();
        console.log(`Closed database pool: ${name}`);
      } catch (error) {
        console.error(`Error closing database pool ${name}:`, error.message);
      }
    }
    this.dbPools.clear();
  }

  /**
   * Test Result Formatter
   */
  formatTestResults(results) {
    return {
      timestamp: new Date().toISOString(),
      summary: {
        total: results.length,
        passed: results.filter(r => r.status === 'passed').length,
        failed: results.filter(r => r.status === 'failed').length,
        skipped: results.filter(r => r.status === 'skipped').length
      },
      details: results,
      environment: {
        nodeVersion: process.version,
        platform: process.platform,
        arch: process.arch
      }
    };
  }
}

module.exports = new TestHelpers();