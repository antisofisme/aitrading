/**
 * StatusMonitoring - Real-time monitoring and status tracking for agent coordination
 * Provides comprehensive monitoring of agents, coordination health, and performance
 */

class StatusMonitoring {
  constructor(memoryCoordination, communicationSystem, lifecycleManager) {
    this.memoryCoordination = memoryCoordination;
    this.communicationSystem = communicationSystem;
    this.lifecycleManager = lifecycleManager;

    this.monitoringActive = false;
    this.monitoringInterval = 15000; // 15 seconds
    this.monitoringTimer = null;

    this.metrics = new Map();
    this.alerts = [];
    this.dashboardData = new Map();
    this.subscribers = new Map();
    this.thresholds = new Map();

    this.setupDefaultThresholds();
  }

  /**
   * Initialize monitoring system
   */
  async initialize() {
    try {
      // Setup monitoring infrastructure
      await this.setupMonitoringInfrastructure();

      // Initialize metrics collection
      this.initializeMetricsCollection();

      // Setup alert system
      this.setupAlertSystem();

      // Start monitoring
      await this.startMonitoring();

      // Store initialization
      await this.memoryCoordination.store(
        'coord/monitoring',
        'initialization',
        {
          initialized: Date.now(),
          interval: this.monitoringInterval,
          thresholds: Object.fromEntries(this.thresholds)
        },
        'system'
      );

      console.log('Status monitoring system initialized');

    } catch (error) {
      console.error('Failed to initialize status monitoring:', error);
      throw error;
    }
  }

  /**
   * Start real-time monitoring
   */
  async startMonitoring() {
    if (this.monitoringActive) return;

    this.monitoringActive = true;

    this.monitoringTimer = setInterval(async () => {
      try {
        await this.performMonitoringCycle();
      } catch (error) {
        console.error('Monitoring cycle failed:', error);
      }
    }, this.monitoringInterval);

    console.log(`Monitoring started with ${this.monitoringInterval}ms interval`);
  }

  /**
   * Stop monitoring
   */
  stopMonitoring() {
    if (!this.monitoringActive) return;

    this.monitoringActive = false;

    if (this.monitoringTimer) {
      clearInterval(this.monitoringTimer);
      this.monitoringTimer = null;
    }

    console.log('Monitoring stopped');
  }

  /**
   * Perform a complete monitoring cycle
   */
  async performMonitoringCycle() {
    const cycleStart = Date.now();
    const cycleId = `cycle_${cycleStart}`;

    try {
      // Collect all metrics in parallel
      const metricsPromises = [
        this.collectSystemMetrics(),
        this.collectAgentMetrics(),
        this.collectCoordinationMetrics(),
        this.collectCommunicationMetrics(),
        this.collectMemoryMetrics()
      ];

      const [
        systemMetrics,
        agentMetrics,
        coordinationMetrics,
        communicationMetrics,
        memoryMetrics
      ] = await Promise.all(metricsPromises);

      // Aggregate metrics
      const aggregatedMetrics = {
        cycleId,
        timestamp: cycleStart,
        duration: Date.now() - cycleStart,
        system: systemMetrics,
        agents: agentMetrics,
        coordination: coordinationMetrics,
        communication: communicationMetrics,
        memory: memoryMetrics
      };

      // Store metrics
      this.metrics.set(cycleId, aggregatedMetrics);

      // Update dashboard data
      await this.updateDashboardData(aggregatedMetrics);

      // Check thresholds and generate alerts
      await this.checkThresholds(aggregatedMetrics);

      // Notify subscribers
      await this.notifySubscribers('metrics_update', aggregatedMetrics);

      // Cleanup old metrics
      this.cleanupOldMetrics();

      return aggregatedMetrics;

    } catch (error) {
      console.error(`Monitoring cycle ${cycleId} failed:`, error);
      throw error;
    }
  }

  /**
   * Collect system-level metrics
   */
  async collectSystemMetrics() {
    const systemStats = this.lifecycleManager.getLifecycleStatistics();
    const coordinationStatus = await this.getCoordinationSystemStatus();

    return {
      timestamp: Date.now(),
      activeAgents: systemStats.activeAgents,
      totalPools: systemStats.totalAgentPools,
      monitoringActive: this.monitoringActive,
      uptime: process.uptime() * 1000,
      memory: {
        used: process.memoryUsage().heapUsed,
        total: process.memoryUsage().heapTotal,
        rss: process.memoryUsage().rss
      },
      coordination: {
        initialized: coordinationStatus.initialized,
        activeBatches: coordinationStatus.activeBatches,
        activeSessions: coordinationStatus.activeSessions
      }
    };
  }

  /**
   * Collect agent-specific metrics
   */
  async collectAgentMetrics() {
    const agents = Array.from(this.lifecycleManager.activeAgents.values());
    const agentMetrics = {};

    // Collect metrics for each agent in parallel
    const metricsPromises = agents.map(async agent => {
      try {
        const metrics = {
          id: agent.id,
          type: agent.type,
          status: agent.status,
          health: agent.health,
          uptime: Date.now() - agent.lifecycle.spawned,
          restarts: agent.lifecycle.restarts,
          lastHeartbeat: agent.lifecycle.heartbeat,
          resources: {
            cpu: await this.getAgentCPUUsage(agent.id),
            memory: await this.getAgentMemoryUsage(agent.id),
            tasks: await this.getAgentTaskCount(agent.id)
          },
          performance: {
            responseTime: await this.getAgentResponseTime(agent.id),
            throughput: await this.getAgentThroughput(agent.id),
            errorRate: await this.getAgentErrorRate(agent.id)
          }
        };

        return { [agent.id]: metrics };
      } catch (error) {
        return { [agent.id]: { error: error.message, timestamp: Date.now() } };
      }
    });

    const metricsResults = await Promise.all(metricsPromises);
    metricsResults.forEach(result => Object.assign(agentMetrics, result));

    return {
      totalAgents: agents.length,
      agents: agentMetrics,
      aggregated: this.calculateAggregatedAgentMetrics(agentMetrics)
    };
  }

  /**
   * Collect coordination system metrics
   */
  async collectCoordinationMetrics() {
    const memoryStats = this.memoryCoordination.getMemoryStatistics();
    const communicationStats = this.communicationSystem.getCommunicationStats();

    return {
      memory: {
        totalOperations: memoryStats.global.totalOperations,
        activeAgents: Object.keys(memoryStats.agents).length,
        sharedNamespaces: Object.keys(memoryStats.shared).length,
        recentActivity: memoryStats.operations.recentActivity
      },
      batches: await this.getBatchMetrics(),
      workflows: await this.getWorkflowMetrics(),
      conflicts: await this.getConflictMetrics()
    };
  }

  /**
   * Collect communication system metrics
   */
  async collectCommunicationMetrics() {
    const stats = this.communicationSystem.getCommunicationStats();

    return {
      totalMessages: stats.totalMessages,
      totalAgents: stats.totalAgents,
      averageLatency: stats.averageLatency,
      messagesByType: stats.messagesByType,
      messagesByAgent: stats.messagesByAgent,
      conflictsDetected: stats.conflictsDetected,
      channels: await this.getCommunicationChannelMetrics()
    };
  }

  /**
   * Collect memory system metrics
   */
  async collectMemoryMetrics() {
    const memoryStats = this.memoryCoordination.getMemoryStatistics();

    return {
      global: memoryStats.global,
      agents: memoryStats.agents,
      shared: memoryStats.shared,
      operations: memoryStats.operations,
      performance: {
        averageReadTime: await this.getAverageMemoryReadTime(),
        averageWriteTime: await this.getAverageMemoryWriteTime(),
        cacheHitRate: await this.getMemoryCacheHitRate()
      }
    };
  }

  /**
   * Update dashboard data for real-time display
   */
  async updateDashboardData(metrics) {
    const dashboard = {
      timestamp: metrics.timestamp,
      overview: {
        systemHealth: this.calculateSystemHealth(metrics),
        activeAgents: metrics.system.activeAgents,
        totalMessages: metrics.communication.totalMessages,
        averageLatency: metrics.communication.averageLatency,
        memoryUsage: metrics.system.memory.used
      },
      agents: {
        total: metrics.agents.totalAgents,
        healthy: Object.values(metrics.agents.agents).filter(a => a.health === 'healthy').length,
        degraded: Object.values(metrics.agents.agents).filter(a => a.health === 'degraded').length,
        unhealthy: Object.values(metrics.agents.agents).filter(a => a.health === 'unhealthy').length
      },
      coordination: {
        activeBatches: metrics.system.coordination.activeBatches,
        memoryOperations: metrics.memory.global.totalOperations,
        communicationHealth: this.calculateCommunicationHealth(metrics.communication)
      },
      alerts: this.getRecentAlerts(10),
      trends: await this.calculateTrends()
    };

    this.dashboardData.set('current', dashboard);

    // Store in memory for cross-agent access
    await this.memoryCoordination.store(
      'coord/monitoring',
      'dashboard',
      dashboard,
      'system'
    );
  }

  /**
   * Check thresholds and generate alerts
   */
  async checkThresholds(metrics) {
    const alerts = [];

    // Check system thresholds
    await this.checkSystemThresholds(metrics.system, alerts);

    // Check agent thresholds
    await this.checkAgentThresholds(metrics.agents, alerts);

    // Check coordination thresholds
    await this.checkCoordinationThresholds(metrics.coordination, alerts);

    // Process new alerts
    for (const alert of alerts) {
      await this.processAlert(alert);
    }

    return alerts;
  }

  /**
   * Check system-level thresholds
   */
  async checkSystemThresholds(systemMetrics, alerts) {
    const thresholds = this.thresholds.get('system') || {};

    // Memory usage threshold
    if (systemMetrics.memory.used > (thresholds.maxMemoryUsage || 1000000000)) { // 1GB default
      alerts.push({
        type: 'system',
        severity: 'high',
        metric: 'memory_usage',
        value: systemMetrics.memory.used,
        threshold: thresholds.maxMemoryUsage,
        message: `System memory usage exceeded threshold: ${systemMetrics.memory.used} bytes`
      });
    }

    // Agent count threshold
    if (systemMetrics.activeAgents > (thresholds.maxActiveAgents || 50)) {
      alerts.push({
        type: 'system',
        severity: 'medium',
        metric: 'agent_count',
        value: systemMetrics.activeAgents,
        threshold: thresholds.maxActiveAgents,
        message: `Active agent count exceeded threshold: ${systemMetrics.activeAgents}`
      });
    }
  }

  /**
   * Check agent-level thresholds
   */
  async checkAgentThresholds(agentMetrics, alerts) {
    const thresholds = this.thresholds.get('agents') || {};

    Object.values(agentMetrics.agents).forEach(agent => {
      if (agent.error) return; // Skip errored agents

      // Response time threshold
      if (agent.performance.responseTime > (thresholds.maxResponseTime || 5000)) {
        alerts.push({
          type: 'agent',
          agentId: agent.id,
          severity: 'medium',
          metric: 'response_time',
          value: agent.performance.responseTime,
          threshold: thresholds.maxResponseTime,
          message: `Agent ${agent.id} response time exceeded threshold`
        });
      }

      // Error rate threshold
      if (agent.performance.errorRate > (thresholds.maxErrorRate || 0.1)) {
        alerts.push({
          type: 'agent',
          agentId: agent.id,
          severity: 'high',
          metric: 'error_rate',
          value: agent.performance.errorRate,
          threshold: thresholds.maxErrorRate,
          message: `Agent ${agent.id} error rate exceeded threshold`
        });
      }

      // Health check
      if (agent.health === 'unhealthy') {
        alerts.push({
          type: 'agent',
          agentId: agent.id,
          severity: 'critical',
          metric: 'health',
          value: agent.health,
          message: `Agent ${agent.id} is unhealthy`
        });
      }
    });
  }

  /**
   * Check coordination-level thresholds
   */
  async checkCoordinationThresholds(coordinationMetrics, alerts) {
    const thresholds = this.thresholds.get('coordination') || {};

    // Memory operations threshold
    if (coordinationMetrics.memory.totalOperations > (thresholds.maxMemoryOperations || 10000)) {
      alerts.push({
        type: 'coordination',
        severity: 'medium',
        metric: 'memory_operations',
        value: coordinationMetrics.memory.totalOperations,
        threshold: thresholds.maxMemoryOperations,
        message: 'Memory operations exceeded threshold'
      });
    }
  }

  /**
   * Process and store alert
   */
  async processAlert(alert) {
    alert.id = `alert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    alert.timestamp = Date.now();
    alert.acknowledged = false;

    // Add to alerts array
    this.alerts.push(alert);

    // Store in memory
    await this.memoryCoordination.store(
      'coord/alerts',
      alert.id,
      alert,
      'system'
    );

    // Notify subscribers
    await this.notifySubscribers('alert', alert);

    // Log alert
    console.warn(`ALERT [${alert.severity}] ${alert.type}: ${alert.message}`);

    // Limit alerts array size
    if (this.alerts.length > 1000) {
      this.alerts = this.alerts.slice(-500);
    }
  }

  /**
   * Subscribe to monitoring updates
   */
  subscribe(subscriberId, eventTypes, callback) {
    if (!this.subscribers.has(subscriberId)) {
      this.subscribers.set(subscriberId, new Map());
    }

    const subscriberEvents = this.subscribers.get(subscriberId);

    eventTypes.forEach(eventType => {
      subscriberEvents.set(eventType, callback);
    });

    return true;
  }

  /**
   * Unsubscribe from monitoring updates
   */
  unsubscribe(subscriberId, eventTypes = null) {
    const subscriberEvents = this.subscribers.get(subscriberId);
    if (!subscriberEvents) return false;

    if (eventTypes) {
      eventTypes.forEach(eventType => {
        subscriberEvents.delete(eventType);
      });

      if (subscriberEvents.size === 0) {
        this.subscribers.delete(subscriberId);
      }
    } else {
      this.subscribers.delete(subscriberId);
    }

    return true;
  }

  /**
   * Notify subscribers of events
   */
  async notifySubscribers(eventType, data) {
    const notifications = [];

    this.subscribers.forEach((events, subscriberId) => {
      const callback = events.get(eventType) || events.get('*'); // wildcard support
      if (callback) {
        notifications.push(
          Promise.resolve(callback({
            eventType,
            data,
            timestamp: Date.now(),
            subscriberId
          })).catch(error => {
            console.error(`Notification failed for subscriber ${subscriberId}:`, error);
          })
        );
      }
    });

    await Promise.all(notifications);
  }

  /**
   * Get current monitoring status
   */
  getMonitoringStatus() {
    return {
      active: this.monitoringActive,
      interval: this.monitoringInterval,
      totalMetrics: this.metrics.size,
      totalAlerts: this.alerts.length,
      subscribers: this.subscribers.size,
      lastCycle: this.getLastCycleTime(),
      dashboard: this.dashboardData.get('current'),
      thresholds: Object.fromEntries(this.thresholds)
    };
  }

  /**
   * Get monitoring dashboard data
   */
  getDashboardData() {
    return this.dashboardData.get('current') || null;
  }

  /**
   * Get recent alerts
   */
  getRecentAlerts(count = 50) {
    return this.alerts
      .slice(-count)
      .sort((a, b) => b.timestamp - a.timestamp);
  }

  /**
   * Acknowledge alert
   */
  async acknowledgeAlert(alertId, acknowledgedBy = 'system') {
    const alert = this.alerts.find(a => a.id === alertId);
    if (alert) {
      alert.acknowledged = true;
      alert.acknowledgedBy = acknowledgedBy;
      alert.acknowledgedAt = Date.now();

      // Update in memory
      await this.memoryCoordination.store(
        'coord/alerts',
        alertId,
        alert,
        'system'
      );

      return true;
    }
    return false;
  }

  /**
   * Setup default monitoring thresholds
   */
  setupDefaultThresholds() {
    this.thresholds.set('system', {
      maxMemoryUsage: 2000000000, // 2GB
      maxActiveAgents: 100,
      maxCPUUsage: 90 // percentage
    });

    this.thresholds.set('agents', {
      maxResponseTime: 10000, // 10 seconds
      maxErrorRate: 0.15, // 15%
      maxMemoryUsage: 100000000 // 100MB per agent
    });

    this.thresholds.set('coordination', {
      maxMemoryOperations: 50000,
      maxCommunicationLatency: 2000, // 2 seconds
      maxConflicts: 10
    });
  }

  /**
   * Setup monitoring infrastructure
   */
  async setupMonitoringInfrastructure() {
    // Initialize monitoring data structures
    await this.memoryCoordination.store(
      'coord/monitoring',
      'structure',
      {
        metricsNamespaces: [
          'coord/metrics/system',
          'coord/metrics/agents',
          'coord/metrics/coordination',
          'coord/metrics/communication'
        ],
        alertNamespaces: [
          'coord/alerts',
          'coord/thresholds'
        ],
        dashboardNamespaces: [
          'coord/dashboard'
        ]
      },
      'system'
    );
  }

  /**
   * Initialize metrics collection
   */
  initializeMetricsCollection() {
    // Setup metrics collection intervals and data structures
    this.metricsCollectionStart = Date.now();
  }

  /**
   * Setup alert system
   */
  setupAlertSystem() {
    // Configure alert processing and notification system
    this.alertSystemInitialized = Date.now();
  }

  /**
   * Helper methods for metrics calculation
   */

  async getCoordinationSystemStatus() {
    // Mock implementation - would get actual coordination status
    return {
      initialized: true,
      activeBatches: 0,
      activeSessions: 0
    };
  }

  async getAgentCPUUsage(agentId) {
    // Mock implementation - would get actual CPU usage
    return Math.random() * 100;
  }

  async getAgentMemoryUsage(agentId) {
    // Mock implementation - would get actual memory usage
    return Math.random() * 100000000;
  }

  async getAgentTaskCount(agentId) {
    // Mock implementation - would get actual task count
    return Math.floor(Math.random() * 10);
  }

  async getAgentResponseTime(agentId) {
    // Mock implementation - would calculate actual response time
    return Math.random() * 5000;
  }

  async getAgentThroughput(agentId) {
    // Mock implementation - would calculate actual throughput
    return Math.random() * 100;
  }

  async getAgentErrorRate(agentId) {
    // Mock implementation - would calculate actual error rate
    return Math.random() * 0.1;
  }

  calculateAggregatedAgentMetrics(agentMetrics) {
    const agents = Object.values(agentMetrics).filter(a => !a.error);
    if (agents.length === 0) return {};

    return {
      averageResponseTime: agents.reduce((sum, a) => sum + a.performance.responseTime, 0) / agents.length,
      averageErrorRate: agents.reduce((sum, a) => sum + a.performance.errorRate, 0) / agents.length,
      totalUptime: agents.reduce((sum, a) => sum + a.uptime, 0),
      totalRestarts: agents.reduce((sum, a) => sum + a.restarts, 0)
    };
  }

  async getBatchMetrics() {
    // Mock implementation - would get actual batch metrics
    return { activeBatches: 0, completedBatches: 0 };
  }

  async getWorkflowMetrics() {
    // Mock implementation - would get actual workflow metrics
    return { activeWorkflows: 0, completedWorkflows: 0 };
  }

  async getConflictMetrics() {
    // Mock implementation - would get actual conflict metrics
    return { activeConflicts: 0, resolvedConflicts: 0 };
  }

  async getCommunicationChannelMetrics() {
    // Mock implementation - would get actual channel metrics
    return { totalChannels: 0, activeChannels: 0 };
  }

  async getAverageMemoryReadTime() {
    return Math.random() * 10;
  }

  async getAverageMemoryWriteTime() {
    return Math.random() * 15;
  }

  async getMemoryCacheHitRate() {
    return Math.random();
  }

  calculateSystemHealth(metrics) {
    // Simple health calculation based on various factors
    let health = 100;

    // Factor in agent health
    const agentMetrics = Object.values(metrics.agents.agents).filter(a => !a.error);
    const healthyAgents = agentMetrics.filter(a => a.health === 'healthy').length;
    const healthyRatio = agentMetrics.length > 0 ? healthyAgents / agentMetrics.length : 1;
    health *= healthyRatio;

    // Factor in communication latency
    if (metrics.communication.averageLatency > 2000) {
      health *= 0.8;
    }

    // Factor in memory usage
    const memoryUsageRatio = metrics.system.memory.used / metrics.system.memory.total;
    if (memoryUsageRatio > 0.8) {
      health *= 0.9;
    }

    return Math.round(health);
  }

  calculateCommunicationHealth(communicationMetrics) {
    let health = 100;

    // Factor in latency
    if (communicationMetrics.averageLatency > 1000) {
      health -= 20;
    }

    // Factor in conflicts
    if (communicationMetrics.conflictsDetected > 5) {
      health -= 30;
    }

    return Math.max(0, health);
  }

  async calculateTrends() {
    // Calculate trends from historical metrics
    const recentMetrics = Array.from(this.metrics.values()).slice(-10);
    if (recentMetrics.length < 2) return {};

    return {
      agentCountTrend: this.calculateTrend(recentMetrics.map(m => m.system.activeAgents)),
      latencyTrend: this.calculateTrend(recentMetrics.map(m => m.communication.averageLatency)),
      memoryTrend: this.calculateTrend(recentMetrics.map(m => m.system.memory.used))
    };
  }

  calculateTrend(values) {
    if (values.length < 2) return 'stable';

    const recent = values.slice(-3).reduce((sum, val) => sum + val, 0) / 3;
    const older = values.slice(0, -3).reduce((sum, val) => sum + val, 0) / (values.length - 3);

    const change = (recent - older) / older;

    if (change > 0.1) return 'increasing';
    if (change < -0.1) return 'decreasing';
    return 'stable';
  }

  getLastCycleTime() {
    const metrics = Array.from(this.metrics.values());
    return metrics.length > 0 ? metrics[metrics.length - 1].timestamp : null;
  }

  cleanupOldMetrics() {
    // Keep only last 100 metric cycles
    if (this.metrics.size > 100) {
      const entries = Array.from(this.metrics.entries()).slice(-50);
      this.metrics.clear();
      entries.forEach(([key, value]) => this.metrics.set(key, value));
    }
  }

  /**
   * Cleanup monitoring system
   */
  cleanup() {
    this.stopMonitoring();
    this.metrics.clear();
    this.alerts = [];
    this.dashboardData.clear();
    this.subscribers.clear();
    this.thresholds.clear();
  }
}

module.exports = StatusMonitoring;