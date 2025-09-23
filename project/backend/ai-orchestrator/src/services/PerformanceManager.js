/**
 * Performance Manager - Monitors and optimizes AI orchestration performance
 * Tracks metrics, identifies bottlenecks, and ensures SLA compliance
 */

class PerformanceManager {
  constructor(logger) {
    this.logger = logger;
    this.performanceMetrics = new Map();
    this.performanceTargets = {
      maxOrchestrationTime: 100, // ms
      serviceAvailability: 0.999, // 99.9%
      aiAccuracy: 0.65, // 65%
      maxInferenceTime: 15, // ms
      multiTenantIsolation: true
    };
    this.alertThresholds = {
      responseTime: 150, // ms
      errorRate: 0.05, // 5%
      accuracy: 0.60 // 60%
    };
    this.isInitialized = false;
  }

  async initialize() {
    try {
      // Initialize performance tracking
      this.initializePerformanceTracking();
      
      // Set up monitoring intervals
      this.setupMonitoring();
      
      this.isInitialized = true;
      this.logger.info('Performance Manager initialized successfully');
      
    } catch (error) {
      this.logger.error('Failed to initialize Performance Manager', {
        error: error.message,
        stack: error.stack
      });
      throw error;
    }
  }

  initializePerformanceTracking() {
    // Initialize global performance metrics
    this.performanceMetrics.set('global', {
      orchestrationRequests: 0,
      successfulRequests: 0,
      failedRequests: 0,
      totalResponseTime: 0,
      averageResponseTime: 0,
      minResponseTime: Infinity,
      maxResponseTime: 0,
      aiAccuracySum: 0,
      aiAccuracyCount: 0,
      averageAiAccuracy: 0,
      lastUpdated: Date.now()
    });

    this.logger.info('Performance tracking initialized');
  }

  setupMonitoring() {
    // Performance analysis every minute
    setInterval(() => {
      this.analyzePerformance();
    }, 60000);

    // Alert checking every 30 seconds
    setInterval(() => {
      this.checkAlerts();
    }, 30000);

    this.logger.info('Performance monitoring started');
  }

  async trackOrchestrationPerformance(orchestrationData) {
    try {
      const {
        tenantId,
        workflowType,
        responseTime,
        success,
        aiAccuracy,
        servicesInvolved
      } = orchestrationData;

      // Update global metrics
      this.updateGlobalMetrics({
        responseTime,
        success,
        aiAccuracy
      });

      // Update tenant-specific metrics
      if (tenantId) {
        this.updateTenantMetrics(tenantId, {
          responseTime,
          success,
          aiAccuracy,
          workflowType
        });
      }

      // Update service-specific metrics
      if (servicesInvolved) {
        this.updateServiceMetrics(servicesInvolved, {
          responseTime,
          success
        });
      }

      this.logger.debug('Orchestration performance tracked', {
        tenantId,
        workflowType,
        responseTime,
        success,
        aiAccuracy
      });

    } catch (error) {
      this.logger.error('Failed to track orchestration performance', {
        error: error.message,
        orchestrationData
      });
    }
  }

  updateGlobalMetrics(data) {
    const global = this.performanceMetrics.get('global');
    
    global.orchestrationRequests++;
    if (data.success) {
      global.successfulRequests++;
    } else {
      global.failedRequests++;
    }

    if (data.responseTime) {
      global.totalResponseTime += data.responseTime;
      global.averageResponseTime = global.totalResponseTime / global.orchestrationRequests;
      global.minResponseTime = Math.min(global.minResponseTime, data.responseTime);
      global.maxResponseTime = Math.max(global.maxResponseTime, data.responseTime);
    }

    if (data.aiAccuracy) {
      global.aiAccuracySum += data.aiAccuracy;
      global.aiAccuracyCount++;
      global.averageAiAccuracy = global.aiAccuracySum / global.aiAccuracyCount;
    }

    global.lastUpdated = Date.now();
  }

  updateTenantMetrics(tenantId, data) {
    const tenantKey = `tenant_${tenantId}`;
    let tenantMetrics = this.performanceMetrics.get(tenantKey);

    if (!tenantMetrics) {
      tenantMetrics = {
        tenantId,
        requests: 0,
        successfulRequests: 0,
        failedRequests: 0,
        totalResponseTime: 0,
        averageResponseTime: 0,
        aiAccuracySum: 0,
        aiAccuracyCount: 0,
        averageAiAccuracy: 0,
        workflowTypes: new Map(),
        lastActivity: Date.now()
      };
      this.performanceMetrics.set(tenantKey, tenantMetrics);
    }

    tenantMetrics.requests++;
    if (data.success) {
      tenantMetrics.successfulRequests++;
    } else {
      tenantMetrics.failedRequests++;
    }

    if (data.responseTime) {
      tenantMetrics.totalResponseTime += data.responseTime;
      tenantMetrics.averageResponseTime = tenantMetrics.totalResponseTime / tenantMetrics.requests;
    }

    if (data.aiAccuracy) {
      tenantMetrics.aiAccuracySum += data.aiAccuracy;
      tenantMetrics.aiAccuracyCount++;
      tenantMetrics.averageAiAccuracy = tenantMetrics.aiAccuracySum / tenantMetrics.aiAccuracyCount;
    }

    if (data.workflowType) {
      const workflowCount = tenantMetrics.workflowTypes.get(data.workflowType) || 0;
      tenantMetrics.workflowTypes.set(data.workflowType, workflowCount + 1);
    }

    tenantMetrics.lastActivity = Date.now();
  }

  updateServiceMetrics(servicesInvolved, data) {
    for (const serviceName of servicesInvolved) {
      const serviceKey = `service_${serviceName}`;
      let serviceMetrics = this.performanceMetrics.get(serviceKey);

      if (!serviceMetrics) {
        serviceMetrics = {
          serviceName,
          invocations: 0,
          successfulInvocations: 0,
          failedInvocations: 0,
          totalResponseTime: 0,
          averageResponseTime: 0,
          lastInvocation: Date.now()
        };
        this.performanceMetrics.set(serviceKey, serviceMetrics);
      }

      serviceMetrics.invocations++;
      if (data.success) {
        serviceMetrics.successfulInvocations++;
      } else {
        serviceMetrics.failedInvocations++;
      }

      if (data.responseTime) {
        serviceMetrics.totalResponseTime += data.responseTime;
        serviceMetrics.averageResponseTime = serviceMetrics.totalResponseTime / serviceMetrics.invocations;
      }

      serviceMetrics.lastInvocation = Date.now();
    }
  }

  async validateAIAccuracy(tenantId) {
    try {
      let accuracyData;

      if (tenantId) {
        const tenantMetrics = this.performanceMetrics.get(`tenant_${tenantId}`);
        accuracyData = {
          averageAccuracy: tenantMetrics?.averageAiAccuracy || 0,
          totalPredictions: tenantMetrics?.aiAccuracyCount || 0,
          tenantId
        };
      } else {
        const globalMetrics = this.performanceMetrics.get('global');
        accuracyData = {
          averageAccuracy: globalMetrics.averageAiAccuracy,
          totalPredictions: globalMetrics.aiAccuracyCount
        };
      }

      const isCompliant = accuracyData.averageAccuracy >= this.performanceTargets.aiAccuracy;
      
      const validation = {
        ...accuracyData,
        target: this.performanceTargets.aiAccuracy,
        isCompliant,
        compliancePercentage: (accuracyData.averageAccuracy / this.performanceTargets.aiAccuracy) * 100,
        recommendations: this.generateAccuracyRecommendations(accuracyData.averageAccuracy)
      };

      this.logger.info('AI accuracy validation completed', {
        tenantId,
        averageAccuracy: accuracyData.averageAccuracy,
        isCompliant,
        target: this.performanceTargets.aiAccuracy
      });

      return validation;

    } catch (error) {
      this.logger.error('AI accuracy validation failed', {
        tenantId,
        error: error.message
      });
      throw error;
    }
  }

  generateAccuracyRecommendations(currentAccuracy) {
    const recommendations = [];

    if (currentAccuracy < this.performanceTargets.aiAccuracy) {
      recommendations.push('Consider retraining models with more recent data');
      recommendations.push('Evaluate feature engineering improvements');
      recommendations.push('Implement ensemble methods for better accuracy');
    }

    if (currentAccuracy < 0.60) {
      recommendations.push('CRITICAL: Immediate model review required');
      recommendations.push('Consider switching to alternative models');
    }

    if (currentAccuracy > 0.80) {
      recommendations.push('Excellent accuracy - consider documenting best practices');
      recommendations.push('Monitor for potential overfitting');
    }

    return recommendations;
  }

  analyzePerformance() {
    try {
      const global = this.performanceMetrics.get('global');
      
      const analysis = {
        timestamp: Date.now(),
        orchestrationCompliance: {
          target: this.performanceTargets.maxOrchestrationTime,
          actual: global.averageResponseTime,
          compliant: global.averageResponseTime <= this.performanceTargets.maxOrchestrationTime
        },
        accuracyCompliance: {
          target: this.performanceTargets.aiAccuracy,
          actual: global.averageAiAccuracy,
          compliant: global.averageAiAccuracy >= this.performanceTargets.aiAccuracy
        },
        successRate: global.orchestrationRequests > 0 
          ? global.successfulRequests / global.orchestrationRequests 
          : 0,
        totalRequests: global.orchestrationRequests,
        performanceGrade: this.calculatePerformanceGrade(global)
      };

      this.logger.info('Performance analysis completed', analysis);

      return analysis;

    } catch (error) {
      this.logger.error('Performance analysis failed', { error: error.message });
    }
  }

  calculatePerformanceGrade(metrics) {
    let score = 0;
    let maxScore = 0;

    // Response time score (30 points)
    maxScore += 30;
    if (metrics.averageResponseTime <= this.performanceTargets.maxOrchestrationTime) {
      score += 30;
    } else if (metrics.averageResponseTime <= this.performanceTargets.maxOrchestrationTime * 1.5) {
      score += 20;
    } else if (metrics.averageResponseTime <= this.performanceTargets.maxOrchestrationTime * 2) {
      score += 10;
    }

    // Accuracy score (40 points)
    maxScore += 40;
    if (metrics.averageAiAccuracy >= this.performanceTargets.aiAccuracy) {
      score += 40;
    } else if (metrics.averageAiAccuracy >= this.performanceTargets.aiAccuracy * 0.9) {
      score += 30;
    } else if (metrics.averageAiAccuracy >= this.performanceTargets.aiAccuracy * 0.8) {
      score += 20;
    } else if (metrics.averageAiAccuracy >= this.performanceTargets.aiAccuracy * 0.7) {
      score += 10;
    }

    // Success rate score (30 points)
    maxScore += 30;
    const successRate = metrics.orchestrationRequests > 0 
      ? metrics.successfulRequests / metrics.orchestrationRequests 
      : 0;
    
    if (successRate >= 0.99) {
      score += 30;
    } else if (successRate >= 0.95) {
      score += 25;
    } else if (successRate >= 0.90) {
      score += 20;
    } else if (successRate >= 0.80) {
      score += 10;
    }

    const percentage = (score / maxScore) * 100;
    
    if (percentage >= 90) return 'A';
    if (percentage >= 80) return 'B';
    if (percentage >= 70) return 'C';
    if (percentage >= 60) return 'D';
    return 'F';
  }

  checkAlerts() {
    try {
      const global = this.performanceMetrics.get('global');
      const alerts = [];

      // Response time alert
      if (global.averageResponseTime > this.alertThresholds.responseTime) {
        alerts.push({
          type: 'response_time',
          severity: 'warning',
          message: `Average response time (${global.averageResponseTime}ms) exceeds threshold (${this.alertThresholds.responseTime}ms)`,
          timestamp: Date.now()
        });
      }

      // Error rate alert
      const errorRate = global.orchestrationRequests > 0 
        ? global.failedRequests / global.orchestrationRequests 
        : 0;
      
      if (errorRate > this.alertThresholds.errorRate) {
        alerts.push({
          type: 'error_rate',
          severity: 'critical',
          message: `Error rate (${(errorRate * 100).toFixed(2)}%) exceeds threshold (${(this.alertThresholds.errorRate * 100).toFixed(2)}%)`,
          timestamp: Date.now()
        });
      }

      // Accuracy alert
      if (global.averageAiAccuracy < this.alertThresholds.accuracy) {
        alerts.push({
          type: 'ai_accuracy',
          severity: 'warning',
          message: `AI accuracy (${(global.averageAiAccuracy * 100).toFixed(2)}%) below threshold (${(this.alertThresholds.accuracy * 100).toFixed(2)}%)`,
          timestamp: Date.now()
        });
      }

      if (alerts.length > 0) {
        this.logger.warn('Performance alerts detected', { alerts });
      }

      return alerts;

    } catch (error) {
      this.logger.error('Alert checking failed', { error: error.message });
    }
  }

  getPerformanceReport(timeRange = '1h') {
    const global = this.performanceMetrics.get('global');
    
    return {
      summary: {
        totalRequests: global.orchestrationRequests,
        successRate: global.orchestrationRequests > 0 
          ? (global.successfulRequests / global.orchestrationRequests) * 100 
          : 0,
        averageResponseTime: global.averageResponseTime,
        averageAiAccuracy: global.averageAiAccuracy * 100,
        performanceGrade: this.calculatePerformanceGrade(global)
      },
      compliance: {
        orchestrationTime: {
          target: this.performanceTargets.maxOrchestrationTime,
          actual: global.averageResponseTime,
          compliant: global.averageResponseTime <= this.performanceTargets.maxOrchestrationTime
        },
        aiAccuracy: {
          target: this.performanceTargets.aiAccuracy * 100,
          actual: global.averageAiAccuracy * 100,
          compliant: global.averageAiAccuracy >= this.performanceTargets.aiAccuracy
        }
      },
      metrics: {
        minResponseTime: global.minResponseTime,
        maxResponseTime: global.maxResponseTime,
        totalAiPredictions: global.aiAccuracyCount
      },
      generated: Date.now()
    };
  }

  isHealthy() {
    return this.isInitialized;
  }

  getMetrics() {
    const global = this.performanceMetrics.get('global');
    
    return {
      totalRequests: global.orchestrationRequests,
      successfulRequests: global.successfulRequests,
      failedRequests: global.failedRequests,
      averageResponseTime: global.averageResponseTime,
      averageAiAccuracy: global.averageAiAccuracy,
      performanceGrade: this.calculatePerformanceGrade(global),
      lastUpdated: global.lastUpdated
    };
  }
}

module.exports = PerformanceManager;