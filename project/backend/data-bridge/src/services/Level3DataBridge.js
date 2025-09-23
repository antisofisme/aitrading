/**
 * Level 3 Data Bridge Integration
 * Connects all Level 3 components for seamless data flow
 * MT5 → Preprocessing → Feature Engineering → AI Orchestration
 */

const EventEmitter = require('events');
const logger = require('../utils/logger');

// Level 3 Components
const DataPreprocessingPipeline = require('./DataPreprocessingPipeline');
const AIDataBridge = require('./AIDataBridge');
const EnhancedFeatureProcessor = require('../../feature-engineering/src/services/EnhancedFeatureProcessor');

class Level3DataBridge extends EventEmitter {
  constructor(config = {}) {
    super();
    this.config = {
      // Performance targets for Level 3
      performanceTargets: {
        endToEndLatency: 50, // ms - Level 3 requirement
        processingLatency: 10, // ms per component
        throughput: 50, // TPS
        accuracy: 99.9, // %
        availability: 99.9 // %
      },
      // Component configurations
      preprocessing: {
        targetLatency: 10,
        enableRealTimeValidation: true,
        enableFeatureExtraction: true,
        multiTenantIsolation: true,
        performanceTracking: true
      },
      featureEngineering: {
        maxProcessingLatency: 10,
        cacheEfficiency: 0.9,
        enableStreamingFeatures: true,
        maxMemoryUsage: 256 * 1024 * 1024
      },
      aiIntegration: {
        aiOrchestrationUrl: process.env.AI_ORCHESTRATION_URL || 'http://localhost:8008',
        streamingEnabled: true,
        maxRetries: 3,
        timeout: 30000
      },
      // Multi-tenant configuration
      multiTenant: {
        enableIsolation: true,
        maxTenantsPerInstance: 1000,
        enablePerTenantMetrics: true
      },
      ...config
    };

    this.isInitialized = false;
    this.isRunning = false;
    this.components = {};
    this.tenantMetrics = new Map();
    this.globalMetrics = {
      totalRequests: 0,
      successfulRequests: 0,
      failedRequests: 0,
      averageEndToEndLatency: 0,
      throughput: 0,
      startTime: Date.now()
    };

    // Performance monitoring
    this.performanceBuffer = [];
    this.alertThresholds = new Map();
    this.healthStatus = 'unknown';
  }

  /**
   * Initialize all Level 3 components
   */
  async initialize() {
    try {
      logger.info('Initializing Level 3 Data Bridge...');

      // Initialize preprocessing pipeline
      this.components.preprocessing = new DataPreprocessingPipeline(this.config.preprocessing);
      await this.components.preprocessing.start();
      logger.info('Data Preprocessing Pipeline initialized');

      // Initialize feature processor
      this.components.featureProcessor = new EnhancedFeatureProcessor(logger);
      await this.components.featureProcessor.initialize();
      logger.info('Enhanced Feature Processor initialized');

      // Initialize AI data bridge
      this.components.aiDataBridge = new AIDataBridge(this.config.aiIntegration);
      await this.components.aiDataBridge.initialize();
      await this.components.aiDataBridge.startStreaming();
      logger.info('AI Data Bridge initialized and streaming started');

      // Setup component event handlers
      this.setupComponentEventHandlers();

      // Start performance monitoring
      this.startPerformanceMonitoring();

      // Start health monitoring
      this.startHealthMonitoring();

      this.isInitialized = true;
      this.healthStatus = 'healthy';

      this.emit('initialized', {
        timestamp: new Date().toISOString(),
        components: Object.keys(this.components),
        performanceTargets: this.config.performanceTargets
      });

      logger.info('Level 3 Data Bridge initialized successfully');
      return { success: true, message: 'Level 3 Data Bridge initialized' };

    } catch (error) {
      this.healthStatus = 'error';
      logger.error('Failed to initialize Level 3 Data Bridge:', error);
      throw error;
    }
  }

  /**
   * Process data through complete Level 3 pipeline
   */
  async processDataThroughPipeline(tickData, options = {}) {
    if (!this.isInitialized || !this.isRunning) {
      throw new Error('Level 3 Data Bridge is not running');
    }

    const startTime = process.hrtime.bigint();
    const tenantId = options.tenantId || 'default';

    try {
      // Step 1: Data Preprocessing (Target: <10ms)
      const preprocessingStart = process.hrtime.bigint();
      const preprocessedData = await this.components.preprocessing.processTickData(tickData, tenantId);

      if (!preprocessedData) {
        throw new Error('Data preprocessing failed - invalid tick data');
      }

      const preprocessingLatency = Number(process.hrtime.bigint() - preprocessingStart) / 1000000;

      // Step 2: Feature Engineering (Target: <10ms)
      const featureStart = process.hrtime.bigint();
      const enhancedFeatures = await this.components.featureProcessor.processPreprocessedData(
        preprocessedData,
        {
          tenantId,
          streaming: options.streaming || false,
          indicators: options.indicators || ['technical', 'market', 'ai'],
          cacheStrategy: options.cacheStrategy || 'intelligent'
        }
      );

      const featureLatency = Number(process.hrtime.bigint() - featureStart) / 1000000;

      // Step 3: AI Integration (Target: <30ms)
      const aiStart = process.hrtime.bigint();
      const aiResponse = await this.components.aiDataBridge.sendToAI(
        enhancedFeatures,
        options.modelType || 'prediction',
        {
          timeout: options.timeout || 30000,
          priority: options.priority || 'normal'
        }
      );

      const aiLatency = Number(process.hrtime.bigint() - aiStart) / 1000000;

      // Calculate total end-to-end latency
      const endToEndLatency = Number(process.hrtime.bigint() - startTime) / 1000000;

      // Prepare pipeline result
      const pipelineResult = {
        symbol: tickData.symbol,
        tenantId,
        pipeline: {
          preprocessing: {
            data: preprocessedData,
            latency: preprocessingLatency,
            success: true
          },
          featureEngineering: {
            features: enhancedFeatures,
            latency: featureLatency,
            success: true
          },
          aiIntegration: {
            response: aiResponse,
            latency: aiLatency,
            success: true
          }
        },
        performance: {
          endToEndLatency,
          componentLatencies: {
            preprocessing: preprocessingLatency,
            featureEngineering: featureLatency,
            aiIntegration: aiLatency
          },
          targetMet: endToEndLatency <= this.config.performanceTargets.endToEndLatency,
          throughputMet: this.globalMetrics.throughput >= this.config.performanceTargets.throughput
        },
        metadata: {
          timestamp: new Date().toISOString(),
          pipelineVersion: 'level3-v1.0',
          processingNode: process.env.NODE_NAME || 'default'
        }
      };

      // Record metrics
      this.recordPipelineMetrics(pipelineResult, tenantId);

      // Emit pipeline completion event
      this.emit('pipelineCompleted', pipelineResult);

      // Check performance targets and emit alerts if needed
      this.checkPerformanceTargets(pipelineResult);

      return pipelineResult;

    } catch (error) {
      const endToEndLatency = Number(process.hrtime.bigint() - startTime) / 1000000;

      // Record failed request
      this.globalMetrics.failedRequests++;
      this.recordTenantMetric(tenantId, 'failedRequests', 1);

      const errorResult = {
        symbol: tickData.symbol,
        tenantId,
        error: {
          message: error.message,
          type: error.constructor.name,
          timestamp: new Date().toISOString()
        },
        performance: {
          endToEndLatency,
          targetMet: false
        }
      };

      this.emit('pipelineError', errorResult);

      logger.error('Level 3 pipeline processing failed:', error);
      throw error;
    }
  }

  /**
   * Setup event handlers for all components
   */
  setupComponentEventHandlers() {
    // Preprocessing Pipeline Events
    this.components.preprocessing.on('dataProcessed', (event) => {
      this.emit('preprocessingCompleted', event);
    });

    this.components.preprocessing.on('performanceMetrics', (metrics) => {
      this.emit('componentMetrics', { component: 'preprocessing', metrics });
    });

    // Feature Processor Events
    this.components.featureProcessor.on('featuresProcessed', (event) => {
      this.emit('featureProcessingCompleted', event);
    });

    this.components.featureProcessor.on('performanceUpdate', (metrics) => {
      this.emit('componentMetrics', { component: 'featureProcessor', metrics });
    });

    this.components.featureProcessor.on('performanceAlert', (alert) => {
      this.handleComponentAlert('featureProcessor', alert);
    });

    // AI Data Bridge Events
    this.components.aiDataBridge.on('aiPrediction', (prediction) => {
      this.emit('aiPredictionReceived', prediction);
    });

    this.components.aiDataBridge.on('performanceAlert', (alert) => {
      this.handleComponentAlert('aiDataBridge', alert);
    });

    this.components.aiDataBridge.on('aiError', (error) => {
      this.emit('aiIntegrationError', error);
    });

    logger.info('Component event handlers setup complete');
  }

  /**
   * Handle component performance alerts
   */
  handleComponentAlert(componentName, alert) {
    const enhancedAlert = {
      ...alert,
      component: componentName,
      level: 'level3',
      severity: this.calculateAlertSeverity(alert),
      timestamp: new Date().toISOString()
    };

    this.emit('componentAlert', enhancedAlert);

    logger.warn(`Component alert [${componentName}]:`, enhancedAlert);
  }

  /**
   * Calculate alert severity based on performance impact
   */
  calculateAlertSeverity(alert) {
    if (alert.type === 'latency' && alert.current > this.config.performanceTargets.endToEndLatency * 2) {
      return 'critical';
    }
    if (alert.type === 'throughput' && alert.current < this.config.performanceTargets.throughput * 0.5) {
      return 'critical';
    }
    if (alert.type === 'error_rate' && alert.current > 5) {
      return 'high';
    }
    return 'medium';
  }

  /**
   * Start Level 3 data processing
   */
  async start() {
    if (!this.isInitialized) {
      throw new Error('Level 3 Data Bridge must be initialized before starting');
    }

    logger.info('Starting Level 3 Data Bridge processing...');

    this.isRunning = true;
    this.globalMetrics.startTime = Date.now();

    this.emit('started', {
      timestamp: new Date().toISOString(),
      performanceTargets: this.config.performanceTargets
    });

    logger.info('Level 3 Data Bridge processing started successfully');
  }

  /**
   * Stop Level 3 data processing
   */
  async stop() {
    if (!this.isRunning) {
      return;
    }

    logger.info('Stopping Level 3 Data Bridge processing...');

    this.isRunning = false;

    // Stop all components
    if (this.components.preprocessing) {
      await this.components.preprocessing.stop();
    }

    if (this.components.featureProcessor) {
      await this.components.featureProcessor.shutdown();
    }

    if (this.components.aiDataBridge) {
      await this.components.aiDataBridge.shutdown();
    }

    // Stop monitoring
    this.stopPerformanceMonitoring();
    this.stopHealthMonitoring();

    this.emit('stopped', {
      timestamp: new Date().toISOString(),
      finalMetrics: this.getOverallMetrics()
    });

    logger.info('Level 3 Data Bridge processing stopped');
  }

  /**
   * Record pipeline processing metrics
   */
  recordPipelineMetrics(pipelineResult, tenantId) {
    // Global metrics
    this.globalMetrics.totalRequests++;
    this.globalMetrics.successfulRequests++;

    // Update average latency
    const alpha = 0.1;
    this.globalMetrics.averageEndToEndLatency =
      (this.globalMetrics.averageEndToEndLatency * (1 - alpha)) +
      (pipelineResult.performance.endToEndLatency * alpha);

    // Update throughput
    const uptime = (Date.now() - this.globalMetrics.startTime) / 1000;
    this.globalMetrics.throughput = this.globalMetrics.totalRequests / uptime;

    // Tenant-specific metrics
    this.recordTenantMetric(tenantId, 'totalRequests', 1);
    this.recordTenantMetric(tenantId, 'successfulRequests', 1);
    this.recordTenantMetric(tenantId, 'averageLatency', pipelineResult.performance.endToEndLatency);

    // Store in performance buffer for analysis
    this.performanceBuffer.push({
      timestamp: Date.now(),
      tenantId,
      endToEndLatency: pipelineResult.performance.endToEndLatency,
      componentLatencies: pipelineResult.performance.componentLatencies,
      targetMet: pipelineResult.performance.targetMet
    });

    // Keep buffer size manageable
    if (this.performanceBuffer.length > 10000) {
      this.performanceBuffer = this.performanceBuffer.slice(-5000);
    }
  }

  /**
   * Record tenant-specific metric
   */
  recordTenantMetric(tenantId, metric, value) {
    if (!this.tenantMetrics.has(tenantId)) {
      this.tenantMetrics.set(tenantId, {
        totalRequests: 0,
        successfulRequests: 0,
        failedRequests: 0,
        averageLatency: 0,
        firstRequest: Date.now(),
        lastRequest: Date.now()
      });
    }

    const tenantData = this.tenantMetrics.get(tenantId);
    tenantData.lastRequest = Date.now();

    if (metric === 'averageLatency') {
      const alpha = 0.1;
      tenantData.averageLatency = (tenantData.averageLatency * (1 - alpha)) + (value * alpha);
    } else {
      tenantData[metric] = (tenantData[metric] || 0) + value;
    }
  }

  /**
   * Check performance targets and emit alerts
   */
  checkPerformanceTargets(pipelineResult) {
    const performance = pipelineResult.performance;
    const targets = this.config.performanceTargets;

    const alerts = [];

    // Check end-to-end latency
    if (performance.endToEndLatency > targets.endToEndLatency) {
      alerts.push({
        type: 'end_to_end_latency',
        message: `End-to-end latency ${performance.endToEndLatency.toFixed(2)}ms exceeds target ${targets.endToEndLatency}ms`,
        current: performance.endToEndLatency,
        target: targets.endToEndLatency,
        severity: 'high'
      });
    }

    // Check component latencies
    Object.entries(performance.componentLatencies).forEach(([component, latency]) => {
      if (latency > targets.processingLatency) {
        alerts.push({
          type: 'component_latency',
          component,
          message: `${component} latency ${latency.toFixed(2)}ms exceeds target ${targets.processingLatency}ms`,
          current: latency,
          target: targets.processingLatency,
          severity: 'medium'
        });
      }
    });

    // Check throughput
    if (this.globalMetrics.throughput < targets.throughput) {
      alerts.push({
        type: 'throughput',
        message: `Throughput ${this.globalMetrics.throughput.toFixed(2)} TPS below target ${targets.throughput} TPS`,
        current: this.globalMetrics.throughput,
        target: targets.throughput,
        severity: 'high'
      });
    }

    // Emit alerts if any
    if (alerts.length > 0) {
      this.emit('performanceAlert', {
        symbol: pipelineResult.symbol,
        tenantId: pipelineResult.tenantId,
        alerts,
        timestamp: new Date().toISOString()
      });
    }
  }

  /**
   * Start performance monitoring
   */
  startPerformanceMonitoring() {
    this.performanceMonitoringInterval = setInterval(() => {
      this.analyzePerformanceTrends();
      this.emitPerformanceUpdate();
    }, 10000); // Every 10 seconds

    logger.info('Performance monitoring started');
  }

  /**
   * Stop performance monitoring
   */
  stopPerformanceMonitoring() {
    if (this.performanceMonitoringInterval) {
      clearInterval(this.performanceMonitoringInterval);
    }
  }

  /**
   * Analyze performance trends
   */
  analyzePerformanceTrends() {
    if (this.performanceBuffer.length < 10) return;

    const recent = this.performanceBuffer.slice(-100); // Last 100 requests
    const recentLatencies = recent.map(r => r.endToEndLatency);
    const recentTargetsMet = recent.filter(r => r.targetMet).length;

    const trends = {
      averageLatency: recentLatencies.reduce((a, b) => a + b, 0) / recentLatencies.length,
      p95Latency: this.calculatePercentile(recentLatencies, 95),
      p99Latency: this.calculatePercentile(recentLatencies, 99),
      targetMetPercentage: (recentTargetsMet / recent.length) * 100,
      throughput: this.globalMetrics.throughput
    };

    this.emit('performanceTrends', {
      trends,
      sampleSize: recent.length,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Calculate percentile from array of values
   */
  calculatePercentile(values, percentile) {
    const sorted = values.slice().sort((a, b) => a - b);
    const index = Math.ceil((percentile / 100) * sorted.length) - 1;
    return sorted[index] || 0;
  }

  /**
   * Emit performance update
   */
  emitPerformanceUpdate() {
    const metrics = this.getOverallMetrics();

    this.emit('performanceUpdate', {
      metrics,
      health: this.healthStatus,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Start health monitoring
   */
  startHealthMonitoring() {
    this.healthMonitoringInterval = setInterval(async () => {
      await this.checkSystemHealth();
    }, 30000); // Every 30 seconds

    logger.info('Health monitoring started');
  }

  /**
   * Stop health monitoring
   */
  stopHealthMonitoring() {
    if (this.healthMonitoringInterval) {
      clearInterval(this.healthMonitoringInterval);
    }
  }

  /**
   * Check overall system health
   */
  async checkSystemHealth() {
    try {
      const healthChecks = {
        preprocessing: this.components.preprocessing?.getStatus?.() || { isRunning: false },
        featureProcessor: this.components.featureProcessor?.getStatus?.() || { isInitialized: false },
        aiDataBridge: this.components.aiDataBridge?.getStatus?.() || { isConnected: false }
      };

      const allHealthy = Object.values(healthChecks).every(status => {
        return status.isRunning !== false && status.isInitialized !== false && status.isConnected !== false;
      });

      this.healthStatus = allHealthy ? 'healthy' : 'degraded';

      // Check performance health
      const performanceHealthy =
        this.globalMetrics.averageEndToEndLatency <= this.config.performanceTargets.endToEndLatency &&
        this.globalMetrics.throughput >= this.config.performanceTargets.throughput * 0.8; // 80% threshold

      if (!performanceHealthy) {
        this.healthStatus = 'performance_degraded';
      }

      this.emit('healthUpdate', {
        status: this.healthStatus,
        components: healthChecks,
        performance: {
          latency: this.globalMetrics.averageEndToEndLatency,
          throughput: this.globalMetrics.throughput,
          healthy: performanceHealthy
        },
        timestamp: new Date().toISOString()
      });

    } catch (error) {
      this.healthStatus = 'error';
      logger.error('Health monitoring error:', error);
    }
  }

  /**
   * Get overall metrics
   */
  getOverallMetrics() {
    const uptime = (Date.now() - this.globalMetrics.startTime) / 1000;
    const errorRate = this.globalMetrics.totalRequests > 0 ?
      (this.globalMetrics.failedRequests / this.globalMetrics.totalRequests) * 100 : 0;

    return {
      global: {
        ...this.globalMetrics,
        uptime,
        errorRate,
        successRate: 100 - errorRate
      },
      tenants: {
        count: this.tenantMetrics.size,
        metrics: Object.fromEntries(this.tenantMetrics)
      },
      performance: {
        targets: this.config.performanceTargets,
        current: {
          endToEndLatency: this.globalMetrics.averageEndToEndLatency,
          throughput: this.globalMetrics.throughput,
          errorRate
        },
        health: this.healthStatus
      },
      components: {
        preprocessing: this.components.preprocessing?.getMetrics?.() || {},
        featureProcessor: this.components.featureProcessor?.getStatus?.() || {},
        aiDataBridge: this.components.aiDataBridge?.getMetrics?.() || {}
      }
    };
  }

  /**
   * Get Level 3 status summary
   */
  getLevel3Status() {
    const metrics = this.getOverallMetrics();

    return {
      level: 3,
      status: this.healthStatus,
      isInitialized: this.isInitialized,
      isRunning: this.isRunning,
      performance: {
        endToEndLatency: {
          current: metrics.global.averageEndToEndLatency,
          target: this.config.performanceTargets.endToEndLatency,
          met: metrics.global.averageEndToEndLatency <= this.config.performanceTargets.endToEndLatency
        },
        throughput: {
          current: metrics.global.throughput,
          target: this.config.performanceTargets.throughput,
          met: metrics.global.throughput >= this.config.performanceTargets.throughput
        },
        accuracy: {
          current: metrics.global.successRate,
          target: this.config.performanceTargets.accuracy,
          met: metrics.global.successRate >= this.config.performanceTargets.accuracy
        }
      },
      components: {
        preprocessing: this.components.preprocessing ? 'active' : 'inactive',
        featureEngineering: this.components.featureProcessor ? 'active' : 'inactive',
        aiIntegration: this.components.aiDataBridge ? 'active' : 'inactive'
      },
      metrics: metrics.global,
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Process batch of tick data through pipeline
   */
  async processBatch(tickDataArray, options = {}) {
    const batchStartTime = process.hrtime.bigint();
    const results = [];
    const errors = [];

    try {
      const promises = tickDataArray.map(async (tickData, index) => {
        try {
          const result = await this.processDataThroughPipeline(tickData, {
            ...options,
            batchIndex: index,
            batchSize: tickDataArray.length
          });
          return { index, result, success: true };
        } catch (error) {
          return { index, error, success: false };
        }
      });

      const batchResults = await Promise.allSettled(promises);

      batchResults.forEach(({ value }) => {
        if (value.success) {
          results.push(value.result);
        } else {
          errors.push(value.error);
        }
      });

      const batchLatency = Number(process.hrtime.bigint() - batchStartTime) / 1000000;

      this.emit('batchProcessed', {
        batchSize: tickDataArray.length,
        successCount: results.length,
        errorCount: errors.length,
        batchLatency,
        averageLatency: batchLatency / tickDataArray.length,
        timestamp: new Date().toISOString()
      });

      return {
        success: true,
        results,
        errors,
        metrics: {
          batchSize: tickDataArray.length,
          successCount: results.length,
          errorCount: errors.length,
          batchLatency,
          averageLatency: batchLatency / tickDataArray.length
        }
      };

    } catch (error) {
      logger.error('Batch processing failed:', error);
      throw error;
    }
  }
}

module.exports = Level3DataBridge;