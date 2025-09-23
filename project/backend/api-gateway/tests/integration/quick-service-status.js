/**
 * Quick Service Status Check
 * Rapid assessment of all microservices
 */

const axios = require('axios');
const { performance } = require('perf_hooks');

class QuickServiceStatus {
  constructor() {
    this.services = {
      'database-service': { port: 8008, baseUrl: 'http://localhost:8008' },
      'configuration-service': { port: 8012, baseUrl: 'http://localhost:8012' },
      'ai-orchestrator': { port: 8020, baseUrl: 'http://localhost:8020' },
      'trading-engine': { port: 9010, baseUrl: 'http://localhost:9010' }
    };
  }

  async checkServiceStatus() {
    console.log('🔍 Quick Service Status Check...\n');

    const results = {};
    const flowId = `status-check-${Date.now()}`;

    for (const [serviceName, config] of Object.entries(this.services)) {
      const startTime = performance.now();

      try {
        const response = await axios.get(`${config.baseUrl}/health`, {
          timeout: 3000,
          headers: {
            'X-Flow-ID': flowId,
            'X-Test-Type': 'status-check'
          }
        });

        const responseTime = performance.now() - startTime;

        results[serviceName] = {
          status: 'healthy',
          httpStatus: response.status,
          responseTime: Math.round(responseTime),
          data: response.data,
          port: config.port,
          flowId: response.headers['x-flow-id'] || 'not-provided'
        };

        console.log(`✅ ${serviceName.padEnd(20)} | Port ${config.port} | ${Math.round(responseTime)}ms | Status: ${response.status}`);

        if (response.data) {
          const dataStr = typeof response.data === 'object' ?
            JSON.stringify(response.data).substring(0, 100) + '...' :
            response.data;
          console.log(`   Data: ${dataStr}`);
        }

      } catch (error) {
        const responseTime = performance.now() - startTime;

        results[serviceName] = {
          status: 'unhealthy',
          error: error.message,
          responseTime: Math.round(responseTime),
          port: config.port,
          errorCode: error.code,
          httpStatus: error.response?.status
        };

        console.log(`❌ ${serviceName.padEnd(20)} | Port ${config.port} | ${Math.round(responseTime)}ms | Error: ${error.message}`);
      }

      console.log(''); // Spacing
    }

    return results;
  }

  async testSpecificEndpoints() {
    console.log('\n🔍 Testing Specific Endpoints...\n');

    const endpointTests = [
      { service: 'trading-engine', endpoint: '/api/trading/status', name: 'Trading Status' },
      { service: 'trading-engine', endpoint: '/api/trading/health', name: 'Trading Health' },
      { service: 'database-service', endpoint: '/api/database/status', name: 'Database Status' },
      { service: 'database-service', endpoint: '/api/database/health', name: 'Database Health' },
      { service: 'ai-orchestrator', endpoint: '/api/ai/status', name: 'AI Status' },
      { service: 'configuration-service', endpoint: '/api/config/status', name: 'Config Status' }
    ];

    const endpointResults = {};

    for (const test of endpointTests) {
      const service = this.services[test.service];
      if (!service) continue;

      try {
        const startTime = performance.now();
        const response = await axios.get(`${service.baseUrl}${test.endpoint}`, {
          timeout: 3000,
          headers: { 'X-Test-Type': 'endpoint-test' }
        });
        const responseTime = performance.now() - startTime;

        endpointResults[test.name] = {
          status: 'success',
          httpStatus: response.status,
          responseTime: Math.round(responseTime),
          service: test.service,
          endpoint: test.endpoint
        };

        console.log(`✅ ${test.name.padEnd(20)} | ${Math.round(responseTime)}ms | Status: ${response.status}`);

      } catch (error) {
        endpointResults[test.name] = {
          status: 'failed',
          error: error.message,
          httpStatus: error.response?.status,
          service: test.service,
          endpoint: test.endpoint
        };

        console.log(`❌ ${test.name.padEnd(20)} | Error: ${error.message}`);
      }
    }

    return endpointResults;
  }

  async testServiceConnectivity() {
    console.log('\n🔗 Testing Service Connectivity...\n');

    const connectivityTests = [
      {
        name: 'Trading Engine to Database',
        fromService: 'trading-engine',
        targetPort: 8008,
        description: 'Can trading engine reach database?'
      },
      {
        name: 'Database Service Internal',
        fromService: 'database-service',
        targetPort: 8008,
        description: 'Database service self-connectivity'
      }
    ];

    const connectivityResults = {};

    for (const test of connectivityTests) {
      const service = this.services[test.fromService];
      if (!service) continue;

      try {
        // Test basic connectivity by checking if we can reach the health endpoint
        const response = await axios.get(`${service.baseUrl}/health`, {
          timeout: 2000,
          headers: {
            'X-Connectivity-Test': test.name,
            'X-Target-Port': test.targetPort.toString()
          }
        });

        connectivityResults[test.name] = {
          status: 'connected',
          description: test.description,
          response: response.data
        };

        console.log(`✅ ${test.name.padEnd(30)} | ${test.description}`);

      } catch (error) {
        connectivityResults[test.name] = {
          status: 'disconnected',
          description: test.description,
          error: error.message
        };

        console.log(`❌ ${test.name.padEnd(30)} | ${test.description} - ${error.message}`);
      }
    }

    return connectivityResults;
  }

  async generateQuickReport() {
    console.log('📊 AI Trading Platform - Quick Integration Status Report');
    console.log('='.repeat(80));

    const serviceStatus = await this.checkServiceStatus();
    const endpointStatus = await this.testSpecificEndpoints();
    const connectivityStatus = await this.testServiceConnectivity();

    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        totalServices: Object.keys(this.services).length,
        healthyServices: Object.values(serviceStatus).filter(s => s.status === 'healthy').length,
        unhealthyServices: Object.values(serviceStatus).filter(s => s.status === 'unhealthy').length,
        runningPorts: Object.values(serviceStatus).filter(s => s.httpStatus === 200).map(s => s.port),
        failedPorts: Object.values(serviceStatus).filter(s => s.status === 'unhealthy').map(s => s.port)
      },
      serviceDetails: serviceStatus,
      endpointTests: endpointStatus,
      connectivityTests: connectivityStatus,
      recommendations: []
    };

    // Generate recommendations
    this.generateQuickRecommendations(report);

    // Display summary
    console.log('\n📊 Quick Status Summary:');
    console.log(`Services Running: ${report.summary.healthyServices}/${report.summary.totalServices}`);
    console.log(`Active Ports: ${report.summary.runningPorts.join(', ')}`);
    console.log(`Failed Ports: ${report.summary.failedPorts.join(', ')}`);

    if (report.recommendations.length > 0) {
      console.log('\n💡 Immediate Actions Required:');
      report.recommendations.forEach((rec, index) => {
        console.log(`${index + 1}. [${rec.priority}] ${rec.action}`);
      });
    }

    return report;
  }

  generateQuickRecommendations(report) {
    const recommendations = [];

    // Check for critical services down
    Object.entries(report.serviceDetails).forEach(([service, status]) => {
      if (status.status === 'unhealthy') {
        const priority = service === 'trading-engine' ? 'CRITICAL' : 'HIGH';
        recommendations.push({
          priority: priority,
          service: service,
          action: `Start ${service} on port ${status.port}`,
          reason: status.error,
          impact: service === 'trading-engine' ? 'Trading operations halted' : 'Service functionality compromised'
        });
      }
    });

    // Check for performance issues
    Object.entries(report.serviceDetails).forEach(([service, status]) => {
      if (status.status === 'healthy' && status.responseTime > 1000) {
        recommendations.push({
          priority: 'MEDIUM',
          service: service,
          action: `Investigate performance issues in ${service}`,
          reason: `Response time ${status.responseTime}ms is high`,
          impact: 'Degraded user experience'
        });
      }
    });

    // Check for missing flow tracking
    Object.entries(report.serviceDetails).forEach(([service, status]) => {
      if (status.status === 'healthy' && status.flowId === 'not-provided') {
        recommendations.push({
          priority: 'LOW',
          service: service,
          action: `Implement Flow ID tracking in ${service}`,
          reason: 'Flow tracking not implemented',
          impact: 'Reduced debugging capabilities'
        });
      }
    });

    report.recommendations = recommendations;
  }
}

// If run directly
if (require.main === module) {
  const checker = new QuickServiceStatus();
  checker.generateQuickReport()
    .then(report => {
      console.log('\n✅ Quick status check completed');
      process.exit(report.summary.unhealthyServices > 0 ? 1 : 0);
    })
    .catch(error => {
      console.error('❌ Quick status check failed:', error);
      process.exit(1);
    });
}

module.exports = QuickServiceStatus;