/**
 * Mock Implementation of ChainHealthMonitor for Testing
 * Provides realistic simulation of service health monitoring and chain analysis
 */

const EventEmitter = require('events');
const { v4: uuidv4 } = require('uuid');

class MockChainHealthMonitor extends EventEmitter {
  constructor(config = {}) {
    super();

    this.config = {
      healthCheckInterval: config.healthCheckInterval || 5000,
      alertThresholds: config.alertThresholds || {
        errorRate: 0.1,
        responseTime: 5000,
        availability: 0.95
      },
      logger: config.logger || this._createMockLogger(),
      metrics: config.metrics || this._createMockMetrics(),
      alertManager: config.alertManager || this._createMockAlertManager(),
      ...config
    };

    // Service registry
    this.services = new Map();
    this.serviceHealthData = new Map();
    this.chains = new Map();

    // Monitoring state
    this.isMonitoring = false;
    this.monitoringInterval = null;

    // Health check simulation
    this.simulatedHealthStates = new Map();
    this.networkLatencies = new Map();
  }

  async initialize() {
    try {
      this.config.logger.info('MockChainHealthMonitor initialized');
      return { success: true };
    } catch (error) {
      this.config.logger.error('Failed to initialize MockChainHealthMonitor', error);
      return { success: false, error: error.message };
    }
  }

  async cleanup() {
    if (this.isMonitoring) {
      await this.stopMonitoring();
    }

    this.services.clear();
    this.serviceHealthData.clear();
    this.chains.clear();
    this.simulatedHealthStates.clear();

    return { success: true };
  }

  async registerService(serviceId, serviceConfig) {
    try {
      if (!serviceId || typeof serviceId !== 'string') {
        return { success: false, error: 'Invalid serviceId' };
      }

      if (!serviceConfig.healthEndpoint) {
        return { success: false, error: 'healthEndpoint required' };
      }

      const service = {
        id: serviceId,
        name: serviceConfig.name || serviceId,
        healthEndpoint: serviceConfig.healthEndpoint,
        dependencies: serviceConfig.dependencies || [],
        criticality: serviceConfig.criticality || 'medium',
        alertThresholds: serviceConfig.alertThresholds || this.config.alertThresholds,
        registeredAt: Date.now(),
        ...serviceConfig
      };

      // Check if updating existing service
      const isUpdate = this.services.has(serviceId);

      this.services.set(serviceId, service);

      // Initialize health data
      if (!this.serviceHealthData.has(serviceId)) {
        this.serviceHealthData.set(serviceId, {
          status: 'unknown',
          availability: 0,
          responseTime: 0,
          errorRate: 0,
          lastCheck: null,
          healthHistory: [],
          circuitBreakerState: 'closed',
          alertsSent: 0,
          recoveryAttempts: 0
        });
      }

      // Set default simulated health state
      if (!this.simulatedHealthStates.has(serviceId)) {
        this.simulatedHealthStates.set(serviceId, {
          status: 'healthy',
          availability: 0.99,
          responseTime: 150,
          errorRate: 0.01
        });
      }

      const logMessage = isUpdate ? 'Service updated' : 'Service registered';
      this.config.logger.info(logMessage, { serviceId, service });
      this.config.metrics.increment('service.registered');

      return { success: true, service };

    } catch (error) {
      this.config.logger.error('Service registration failed', { serviceId, error: error.message });
      return { success: false, error: error.message };
    }
  }

  async registerChain(chainId, chainConfig) {
    try {
      const chain = {
        id: chainId,
        name: chainConfig.name || chainId,
        services: chainConfig.services || [],
        entryPoint: chainConfig.entryPoint,
        criticalPath: chainConfig.criticalPath || [],
        registeredAt: Date.now(),
        ...chainConfig
      };

      this.chains.set(chainId, chain);

      this.config.logger.info('Chain registered', { chainId, chain });
      return { success: true, chain };

    } catch (error) {
      this.config.logger.error('Chain registration failed', { chainId, error: error.message });
      return { success: false, error: error.message };
    }
  }

  async startMonitoring() {
    if (this.isMonitoring) {
      return { success: true, message: 'Already monitoring' };
    }

    try {
      this.isMonitoring = true;

      // Start monitoring interval
      this.monitoringInterval = setInterval(async () => {
        await this._performHealthCheckCycle();
      }, this.config.healthCheckInterval);

      this.config.logger.info('Health monitoring started', {
        interval: this.config.healthCheckInterval,
        serviceCount: this.services.size
      });

      this.emit('monitoringStarted');
      return { success: true };

    } catch (error) {
      this.config.logger.error('Failed to start monitoring', error);
      return { success: false, error: error.message };
    }
  }

  async stopMonitoring() {
    if (!this.isMonitoring) {
      return { success: true, message: 'Not monitoring' };
    }

    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = null;
    }

    this.isMonitoring = false;

    this.config.logger.info('Health monitoring stopped');
    this.emit('monitoringStopped');

    return { success: true };
  }

  async getServiceHealth(serviceId) {
    if (!this.services.has(serviceId)) {
      return { success: false, error: 'Service not found' };
    }

    const healthData = this.serviceHealthData.get(serviceId);
    const simulatedState = this.simulatedHealthStates.get(serviceId);

    return {
      success: true,
      ...healthData,
      ...simulatedState
    };
  }

  async analyzeChainHealth(chainId) {
    try {
      const chain = this.chains.get(chainId);
      if (!chain) {
        return { success: false, error: 'Chain not found' };
      }

      const chainHealth = {
        chainId,
        overallStatus: 'healthy',
        healthyServices: 0,
        degradedServices: 0,
        unhealthyServices: 0,
        availabilityScore: 1.0,
        criticalPathFailure: false,
        affectedServices: [],
        timestamp: Date.now()
      };

      let minAvailability = 1.0;
      const serviceStatuses = [];

      // Analyze each service in the chain
      for (const serviceId of chain.services) {
        const healthData = this.serviceHealthData.get(serviceId);
        const simulatedState = this.simulatedHealthStates.get(serviceId);

        if (healthData && simulatedState) {
          const status = simulatedState.status;
          const availability = simulatedState.availability;

          serviceStatuses.push({ serviceId, status, availability });

          // Count service states
          switch (status) {
            case 'healthy':
              chainHealth.healthyServices++;
              break;
            case 'degraded':
              chainHealth.degradedServices++;
              break;
            case 'unhealthy':
              chainHealth.unhealthyServices++;
              chainHealth.affectedServices.push(serviceId);
              break;
          }

          // Track minimum availability
          if (availability < minAvailability) {
            minAvailability = availability;
          }

          // Check for critical path failures
          if (status === 'unhealthy' && chain.criticalPath.includes(serviceId)) {
            chainHealth.criticalPathFailure = true;
          }
        }
      }

      // Determine overall status
      if (chainHealth.unhealthyServices > 0 || chainHealth.criticalPathFailure) {
        chainHealth.overallStatus = 'unhealthy';
      } else if (chainHealth.degradedServices > 0) {
        chainHealth.overallStatus = 'degraded';
      }

      chainHealth.availabilityScore = minAvailability;

      return { success: true, ...chainHealth };

    } catch (error) {
      this.config.logger.error('Chain health analysis failed', { chainId, error: error.message });
      return { success: false, error: error.message };
    }
  }

  async getServiceDependencies(serviceId) {
    const service = this.services.get(serviceId);
    if (!service) {
      return { success: false, error: 'Service not found' };
    }

    // Find dependents (services that depend on this service)
    const dependents = [];
    for (const [id, svc] of this.services) {
      if (svc.dependencies.includes(serviceId)) {
        dependents.push(id);
      }
    }

    return {
      success: true,
      serviceId,
      dependencies: service.dependencies,
      dependents
    };
  }

  // Mock-specific methods for testing
  _setServiceHealth(serviceId, status, availability = null) {
    if (!this.simulatedHealthStates.has(serviceId)) {
      this.simulatedHealthStates.set(serviceId, {});
    }

    const state = this.simulatedHealthStates.get(serviceId);
    state.status = status;

    if (availability !== null) {
      state.availability = availability;
    }

    // Update response time based on status
    switch (status) {
      case 'healthy':
        state.responseTime = 100 + Math.random() * 100; // 100-200ms
        state.errorRate = Math.random() * 0.01; // 0-1%
        break;
      case 'degraded':
        state.responseTime = 500 + Math.random() * 1000; // 500-1500ms
        state.errorRate = 0.05 + Math.random() * 0.05; // 5-10%
        break;
      case 'unhealthy':
        state.responseTime = 5000 + Math.random() * 5000; // 5-10s
        state.errorRate = 0.5 + Math.random() * 0.5; // 50-100%
        break;
    }

    this.simulatedHealthStates.set(serviceId, state);
  }

  async _performHealthCheck(serviceId) {
    const simulatedState = this.simulatedHealthStates.get(serviceId);
    if (!simulatedState) {
      return {
        status: 'unknown',
        responseTime: 0,
        timestamp: Date.now()
      };
    }

    // Simulate network latency
    const latency = this.networkLatencies.get(serviceId) || 0;
    await new Promise(resolve => setTimeout(resolve, latency));

    return {
      status: simulatedState.status,
      responseTime: simulatedState.responseTime,
      errorRate: simulatedState.errorRate,
      availability: simulatedState.availability,
      timestamp: Date.now()
    };
  }

  async _processHealthCheck(serviceId, healthResult) {
    const healthData = this.serviceHealthData.get(serviceId);
    if (!healthData) return;

    // Update health data
    healthData.status = healthResult.status;
    healthData.lastCheck = healthResult.timestamp;
    healthData.responseTime = healthResult.responseTime;
    healthData.errorRate = healthResult.errorRate;

    // Add to history
    healthData.healthHistory.push({
      timestamp: healthResult.timestamp,
      status: healthResult.status,
      responseTime: healthResult.responseTime,
      errorRate: healthResult.errorRate
    });

    // Keep only last 100 entries
    if (healthData.healthHistory.length > 100) {
      healthData.healthHistory = healthData.healthHistory.slice(-100);
    }

    // Calculate availability
    const recentChecks = healthData.healthHistory.slice(-20); // Last 20 checks
    const healthyChecks = recentChecks.filter(check => check.status === 'healthy').length;
    healthData.availability = recentChecks.length > 0 ? healthyChecks / recentChecks.length : 0;

    // Check for alerts
    await this._checkAlerts(serviceId, healthData);

    // Update metrics
    this.config.metrics.gauge('service.health.response_time', healthResult.responseTime, { serviceId });
    this.config.metrics.gauge('service.health.availability', healthData.availability, { serviceId });

    if (healthResult.status === 'unhealthy') {
      this.config.metrics.increment('service.health.failure', { serviceId });
    }

    // Emit event
    this.emit('healthCheckCompleted', { serviceId, healthResult, healthData });
  }

  async _performHealthCheckCycle() {
    const services = Array.from(this.services.keys());

    for (const serviceId of services) {
      try {
        const healthResult = await this._performHealthCheck(serviceId);
        await this._processHealthCheck(serviceId, healthResult);
      } catch (error) {
        this.config.logger.error('Health check failed', { serviceId, error: error.message });
      }
    }
  }

  async _checkAlerts(serviceId, healthData) {
    const service = this.services.get(serviceId);
    const thresholds = service.alertThresholds || this.config.alertThresholds;

    const alerts = [];

    // Check response time threshold
    if (healthData.responseTime > thresholds.responseTime) {
      alerts.push({
        type: 'performance_degradation',
        serviceId,
        severity: 'medium',
        message: `Response time exceeded threshold: ${healthData.responseTime}ms > ${thresholds.responseTime}ms`,
        metrics: { averageResponseTime: healthData.responseTime },
        timestamp: Date.now()
      });
    }

    // Check availability threshold
    if (healthData.availability < thresholds.availability) {
      alerts.push({
        type: 'availability_degradation',
        serviceId,
        severity: 'high',
        message: `Availability below threshold: ${healthData.availability} < ${thresholds.availability}`,
        timestamp: Date.now()
      });
    }

    // Check for service failure
    if (healthData.status === 'unhealthy') {
      alerts.push({
        type: 'service_failure',
        serviceId,
        severity: service.criticality === 'high' ? 'high' : 'medium',
        message: 'Service is unhealthy',
        timestamp: Date.now()
      });
    }

    // Send alerts
    for (const alert of alerts) {
      await this.config.alertManager.sendAlert(alert);
      healthData.alertsSent++;

      // Check for escalation
      if (healthData.alertsSent > 2) {
        await this.config.alertManager.escalateAlert(alert);
      }
    }
  }

  async _attemptRecovery(serviceId, strategy) {
    const healthData = this.serviceHealthData.get(serviceId);
    if (!healthData) return { success: false };

    healthData.recoveryAttempts++;

    // Simulate recovery attempt
    const success = Math.random() > 0.3; // 70% success rate

    if (success) {
      // Improve service health
      const currentState = this.simulatedHealthStates.get(serviceId);
      if (currentState && currentState.status === 'unhealthy') {
        currentState.status = 'degraded';
        currentState.availability = Math.min(0.9, currentState.availability + 0.2);
      }
    }

    return { success, strategy, attempts: healthData.recoveryAttempts };
  }

  _getServiceHealth(serviceId) {
    return {
      addHealthCheck: (result) => {
        const healthData = this.serviceHealthData.get(serviceId) || { healthHistory: [] };
        healthData.healthHistory.push(result);
        this.serviceHealthData.set(serviceId, healthData);
      },
      calculateAvailability: () => {
        const healthData = this.serviceHealthData.get(serviceId);
        if (!healthData || !healthData.healthHistory) return 0;

        const recentChecks = healthData.healthHistory.slice(-10);
        const healthyChecks = recentChecks.filter(check => check.status === 'healthy').length;
        return recentChecks.length > 0 ? healthyChecks / recentChecks.length : 0;
      }
    };
  }

  _getServiceMetrics(serviceId) {
    const healthData = this.serviceHealthData.get(serviceId);
    if (!healthData || !healthData.healthHistory) {
      return { averageResponseTime: 0, p95ResponseTime: 0 };
    }

    const responseTimes = healthData.healthHistory.map(h => h.responseTime).sort((a, b) => a - b);
    const averageResponseTime = responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length;
    const p95ResponseTime = responseTimes[Math.floor(responseTimes.length * 0.95)] || 0;

    return { averageResponseTime, p95ResponseTime };
  }

  _detectAnomalies(serviceId) {
    const healthData = this.serviceHealthData.get(serviceId);
    if (!healthData || !healthData.healthHistory || healthData.healthHistory.length < 10) {
      return [];
    }

    const anomalies = [];
    const recentChecks = healthData.healthHistory.slice(-20);
    const responseTimes = recentChecks.map(h => h.responseTime);

    // Calculate baseline (excluding last 3 entries)
    const baseline = responseTimes.slice(0, -3);
    const avgBaseline = baseline.reduce((a, b) => a + b, 0) / baseline.length;

    // Check for spikes
    const recent = responseTimes.slice(-3);
    const maxRecent = Math.max(...recent);

    if (maxRecent > avgBaseline * 3) { // 3x baseline
      anomalies.push({
        type: 'response_time_spike',
        timestamp: Date.now(),
        value: maxRecent,
        baseline: avgBaseline
      });
    }

    return anomalies;
  }

  _getRecoveryStats(serviceId) {
    const healthData = this.serviceHealthData.get(serviceId);
    if (!healthData) {
      return { totalAttempts: 0, successfulRecoveries: 0, successRate: 0 };
    }

    // Simulate recovery stats
    const totalAttempts = healthData.recoveryAttempts || 0;
    const successfulRecoveries = Math.floor(totalAttempts * 0.7); // 70% success rate

    return {
      totalAttempts,
      successfulRecoveries,
      successRate: totalAttempts > 0 ? successfulRecoveries / totalAttempts : 0
    };
  }

  async generateHealthReport() {
    const services = Array.from(this.services.keys());
    let healthyServices = 0;
    let degradedServices = 0;
    let unhealthyServices = 0;
    let totalAvailability = 0;

    for (const serviceId of services) {
      const healthData = this.serviceHealthData.get(serviceId);
      const simulatedState = this.simulatedHealthStates.get(serviceId);

      if (healthData && simulatedState) {
        switch (simulatedState.status) {
          case 'healthy':
            healthyServices++;
            break;
          case 'degraded':
            degradedServices++;
            break;
          case 'unhealthy':
            unhealthyServices++;
            break;
        }

        totalAvailability += simulatedState.availability;
      }
    }

    return {
      totalServices: services.length,
      healthyServices,
      degradedServices,
      unhealthyServices,
      overallAvailability: services.length > 0 ? totalAvailability / services.length : 0,
      timestamp: Date.now()
    };
  }

  async exportPrometheusMetrics() {
    let metrics = '# HELP service_health_status Current health status of services\n';
    metrics += '# TYPE service_health_status gauge\n';

    for (const [serviceId, state] of this.simulatedHealthStates) {
      const statusValue = state.status === 'healthy' ? 1 : (state.status === 'degraded' ? 0.5 : 0);
      metrics += `service_health_status{service="${serviceId}"} ${statusValue}\n`;
      metrics += `service_response_time{service="${serviceId}"} ${state.responseTime}\n`;
      metrics += `service_availability{service="${serviceId}"} ${state.availability}\n`;
    }

    return metrics;
  }

  async processNetworkEvents(events) {
    // Simulate processing network events
    await new Promise(resolve => setTimeout(resolve, events.length / 100));

    for (const event of events) {
      if (event.serviceId && this.serviceHealthData.has(event.serviceId)) {
        const healthData = this.serviceHealthData.get(event.serviceId);

        // Update metrics based on event
        if (event.metrics) {
          healthData.responseTime = event.metrics.responseTime || healthData.responseTime;
          healthData.errorRate = event.metrics.errorRate || healthData.errorRate;
        }
      }
    }

    return { success: true, processedEvents: events.length };
  }

  // Helper methods for creating mocks
  _createMockLogger() {
    return {
      info: jest.fn(),
      warn: jest.fn(),
      error: jest.fn(),
      debug: jest.fn()
    };
  }

  _createMockMetrics() {
    return {
      increment: jest.fn(),
      gauge: jest.fn(),
      histogram: jest.fn(),
      timer: jest.fn()
    };
  }

  _createMockAlertManager() {
    return {
      sendAlert: jest.fn().mockResolvedValue({ success: true }),
      escalateAlert: jest.fn().mockResolvedValue({ success: true })
    };
  }
}

module.exports = MockChainHealthMonitor;