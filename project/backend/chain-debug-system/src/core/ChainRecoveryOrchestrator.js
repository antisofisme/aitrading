/**
 * ChainRecoveryOrchestrator
 * Automated recovery procedures with circuit breaker patterns
 */

import EventEmitter from 'eventemitter3';
import logger from '../utils/logger.js';
import { ServiceController } from '../recovery/ServiceController.js';
import { TrafficManager } from '../recovery/TrafficManager.js';
import { CircuitBreakerManager } from '../recovery/CircuitBreakerManager.js';
import { RecoveryPlan } from '../models/RecoveryPlan.js';
import { RecoveryResult } from '../models/RecoveryResult.js';
import { RecoveryAction } from '../models/RecoveryAction.js';

export class ChainRecoveryOrchestrator extends EventEmitter {
  constructor({ database, redis, metricsCollector, impactAnalyzer }) {
    super();

    this.database = database;
    this.redis = redis;
    this.metricsCollector = metricsCollector;
    this.impactAnalyzer = impactAnalyzer;

    this.serviceController = null;
    this.trafficManager = null;
    this.circuitBreakerManager = null;

    this.isHealthy = true;

    // Recovery state tracking
    this.activeRecoveries = new Map();
    this.recoveryHistory = [];

    // Configuration
    this.config = {
      maxConcurrentRecoveries: parseInt(process.env.MAX_CONCURRENT_RECOVERIES) || 3,
      recoveryTimeout: parseInt(process.env.RECOVERY_TIMEOUT) || 300000, // 5 minutes
      verificationTimeout: parseInt(process.env.VERIFICATION_TIMEOUT) || 60000, // 1 minute
      enableAutomatedRecovery: process.env.ENABLE_AUTOMATED_RECOVERY !== 'false',
      emergencyMode: false
    };

    // Recovery action priorities
    this.actionPriorities = {
      'circuit_break': 1,
      'traffic_redirect': 2,
      'scale_up': 3,
      'restart': 4,
      'rollback': 5,
      'failover': 6
    };
  }

  async initialize() {
    try {
      logger.info('Initializing ChainRecoveryOrchestrator...');

      // Initialize recovery components
      this.serviceController = new ServiceController({
        database: this.database,
        redis: this.redis
      });

      this.trafficManager = new TrafficManager({
        database: this.database,
        redis: this.redis
      });

      this.circuitBreakerManager = new CircuitBreakerManager({
        database: this.database,
        redis: this.redis
      });

      await Promise.all([
        this.serviceController.initialize(),
        this.trafficManager.initialize(),
        this.circuitBreakerManager.initialize()
      ]);

      // Load recovery configurations
      await this.loadRecoveryConfigurations();

      // Start recovery monitoring
      this.startRecoveryMonitoring();

      logger.info('ChainRecoveryOrchestrator initialized successfully');

    } catch (error) {
      logger.error('Failed to initialize ChainRecoveryOrchestrator:', error);
      this.isHealthy = false;
      throw error;
    }
  }

  async executeRecoveryPlan(impactAssessment, rootCauseAnalysis) {
    try {
      const chainId = impactAssessment.chainId;

      logger.info(`Executing recovery plan for chain ${chainId} (priority: ${impactAssessment.priorityLevel})`);

      // Check if recovery is already in progress
      if (this.activeRecoveries.has(chainId)) {
        logger.warn(`Recovery already in progress for chain ${chainId}`);
        return this.activeRecoveries.get(chainId);
      }

      // Check concurrent recovery limits
      if (this.activeRecoveries.size >= this.config.maxConcurrentRecoveries) {
        logger.warn('Maximum concurrent recoveries reached, queuing recovery');
        return await this.queueRecovery(impactAssessment, rootCauseAnalysis);
      }

      // Generate recovery plan
      const recoveryPlan = await this.generateRecoveryPlan(impactAssessment, rootCauseAnalysis);

      // Execute recovery
      const recoveryPromise = this.executeRecovery(recoveryPlan);
      this.activeRecoveries.set(chainId, recoveryPromise);

      // Start recovery timeout
      const timeoutId = setTimeout(() => {
        this.handleRecoveryTimeout(chainId);
      }, this.config.recoveryTimeout);

      try {
        const result = await recoveryPromise;
        clearTimeout(timeoutId);
        this.activeRecoveries.delete(chainId);

        // Store recovery result
        await this.storeRecoveryResult(result);

        // Emit recovery completion
        this.emit('recovery:completed', {
          chainId,
          result,
          timestamp: new Date()
        });

        logger.info(`Recovery completed for chain ${chainId}: ${result.status}`);

        return result;

      } catch (error) {
        clearTimeout(timeoutId);
        this.activeRecoveries.delete(chainId);

        logger.error(`Recovery failed for chain ${chainId}:`, error);

        const failureResult = new RecoveryResult({
          chainId,
          status: 'failed',
          error: error.message,
          startTime: new Date(),
          endTime: new Date(),
          actionsAttempted: [],
          recoveryPlan
        });

        await this.storeRecoveryResult(failureResult);

        this.emit('recovery:failed', {
          chainId,
          error,
          result: failureResult,
          timestamp: new Date()
        });

        throw error;
      }

    } catch (error) {
      logger.error('Failed to execute recovery plan:', error);
      throw error;
    }
  }

  async generateRecoveryPlan(impactAssessment, rootCauseAnalysis) {
    try {
      const recoveryActions = [];

      // Add immediate actions based on severity
      if (impactAssessment.priorityLevel === 'critical') {
        recoveryActions.push(...await this.generateCriticalRecoveryActions(impactAssessment, rootCauseAnalysis));
      }

      // Add root cause specific actions
      if (rootCauseAnalysis && rootCauseAnalysis.recommendedActions) {
        recoveryActions.push(...await this.convertRecommendationsToActions(rootCauseAnalysis.recommendedActions));
      }

      // Add cascade prevention actions
      if (impactAssessment.cascadeRisk.riskScore > 0.7) {
        recoveryActions.push(...await this.generateCascadePreventionActions(impactAssessment.cascadeRisk));
      }

      // Add service-specific recovery actions
      for (const service of impactAssessment.affectedServices) {
        recoveryActions.push(...await this.generateServiceRecoveryActions(service, impactAssessment));
      }

      // Sort actions by priority and dependencies
      const sortedActions = this.sortRecoveryActions(recoveryActions);

      // Create recovery plan
      const recoveryPlan = new RecoveryPlan({
        chainId: impactAssessment.chainId,
        priority: impactAssessment.priorityLevel,
        actions: sortedActions,
        estimatedDuration: this.calculatePlanDuration(sortedActions),
        createdAt: new Date(),
        impactAssessment,
        rootCauseAnalysis
      });

      logger.info(`Generated recovery plan for chain ${impactAssessment.chainId} with ${sortedActions.length} actions`);

      return recoveryPlan;

    } catch (error) {
      logger.error('Failed to generate recovery plan:', error);
      throw error;
    }
  }

  async generateCriticalRecoveryActions(impactAssessment, rootCauseAnalysis) {
    const actions = [];

    // Immediate circuit breaker activation for critical issues
    if (impactAssessment.cascadeRisk.riskScore > 0.8) {
      actions.push(new RecoveryAction({
        type: 'circuit_break',
        description: 'Activate circuit breakers to prevent cascade failure',
        priority: 1,
        estimatedDuration: 30000, // 30 seconds
        targetServices: impactAssessment.affectedServices,
        parameters: {
          duration: 300000, // 5 minutes
          failure_threshold: 5,
          timeout: 30000
        }
      }));
    }

    // Traffic redirection for critical services
    const criticalServices = impactAssessment.affectedServices.filter(service =>
      this.isCriticalService(service)
    );

    if (criticalServices.length > 0) {
      actions.push(new RecoveryAction({
        type: 'traffic_redirect',
        description: `Redirect traffic away from critical services: ${criticalServices.join(', ')}`,
        priority: 2,
        estimatedDuration: 60000, // 1 minute
        targetServices: criticalServices,
        parameters: {
          redirection_percentage: 100,
          backup_services: await this.getBackupServices(criticalServices)
        }
      }));
    }

    return actions;
  }

  async convertRecommendationsToActions(recommendations) {
    const actions = [];

    for (const recommendation of recommendations) {
      const action = await this.convertRecommendationToAction(recommendation);
      if (action) {
        actions.push(action);
      }
    }

    return actions;
  }

  async convertRecommendationToAction(recommendation) {
    try {
      const actionMap = {
        'scale_service': 'scale_up',
        'restart_service': 'restart',
        'restart_affected_services': 'restart',
        'enable_circuit_breaker': 'circuit_break',
        'increase_timeout_values': 'config_update',
        'switch_data_provider': 'failover',
        'rollback_configuration': 'rollback'
      };

      const actionType = actionMap[recommendation.action] || recommendation.action;

      return new RecoveryAction({
        type: actionType,
        description: recommendation.description,
        priority: this.convertPriorityToNumber(recommendation.priority),
        estimatedDuration: (recommendation.estimatedTime || 300) * 1000, // Convert to milliseconds
        targetServices: recommendation.targetServices || [],
        parameters: recommendation.parameters || {},
        estimatedImpact: recommendation.estimatedImpact || 0.5,
        feasibility: recommendation.feasibility || 0.7
      });

    } catch (error) {
      logger.error('Failed to convert recommendation to action:', error);
      return null;
    }
  }

  async generateCascadePreventionActions(cascadeRisk) {
    const actions = [];

    for (const cascadePath of cascadeRisk.cascadePaths) {
      if (cascadePath.probability > 0.7) {
        // High probability cascade - immediate circuit breaker
        actions.push(new RecoveryAction({
          type: 'circuit_break',
          description: `Prevent cascade from ${cascadePath.sourceService} to ${cascadePath.targetService}`,
          priority: 1,
          estimatedDuration: 30000,
          targetServices: [cascadePath.sourceService],
          parameters: {
            target_service: cascadePath.targetService,
            duration: 600000 // 10 minutes
          }
        }));
      } else if (cascadePath.impactSeverity > 0.8) {
        // High impact target - preemptive scaling
        actions.push(new RecoveryAction({
          type: 'scale_up',
          description: `Preemptively scale ${cascadePath.targetService} to handle potential cascade`,
          priority: 3,
          estimatedDuration: 120000,
          targetServices: [cascadePath.targetService],
          parameters: {
            scale_factor: 1.5,
            duration: 1800000 // 30 minutes
          }
        }));
      }
    }

    return actions;
  }

  async generateServiceRecoveryActions(serviceName, impactAssessment) {
    const actions = [];

    // Get service-specific recovery strategies
    const serviceConfig = await this.getServiceRecoveryConfig(serviceName);

    if (serviceConfig) {
      // Health check action
      actions.push(new RecoveryAction({
        type: 'health_check',
        description: `Perform health check on ${serviceName}`,
        priority: 5,
        estimatedDuration: 15000,
        targetServices: [serviceName],
        parameters: {
          timeout: 10000,
          retry_count: 3
        }
      }));

      // Service-specific recovery based on configuration
      if (serviceConfig.preferredRecoveryMethod === 'restart') {
        actions.push(new RecoveryAction({
          type: 'restart',
          description: `Restart ${serviceName}`,
          priority: 4,
          estimatedDuration: serviceConfig.restartDuration || 60000,
          targetServices: [serviceName],
          parameters: {
            graceful: true,
            timeout: serviceConfig.shutdownTimeout || 30000
          }
        }));
      } else if (serviceConfig.preferredRecoveryMethod === 'scale') {
        actions.push(new RecoveryAction({
          type: 'scale_up',
          description: `Scale up ${serviceName}`,
          priority: 3,
          estimatedDuration: serviceConfig.scaleDuration || 120000,
          targetServices: [serviceName],
          parameters: {
            scale_factor: serviceConfig.scaleMultiplier || 2,
            max_instances: serviceConfig.maxInstances || 10
          }
        }));
      }
    }

    return actions;
  }

  sortRecoveryActions(actions) {
    return actions.sort((a, b) => {
      // Sort by priority first
      if (a.priority !== b.priority) {
        return a.priority - b.priority;
      }

      // Then by estimated impact (higher impact first)
      if (a.estimatedImpact !== b.estimatedImpact) {
        return (b.estimatedImpact || 0) - (a.estimatedImpact || 0);
      }

      // Then by feasibility (higher feasibility first)
      return (b.feasibility || 0) - (a.feasibility || 0);
    });
  }

  calculatePlanDuration(actions) {
    // Calculate total duration considering parallel execution possibilities
    let totalDuration = 0;
    let currentParallelBatch = [];

    for (const action of actions) {
      // Check if action can run in parallel with current batch
      if (this.canRunInParallel(action, currentParallelBatch)) {
        currentParallelBatch.push(action);
      } else {
        // Finish current batch and start new one
        if (currentParallelBatch.length > 0) {
          totalDuration += Math.max(...currentParallelBatch.map(a => a.estimatedDuration));
        }
        currentParallelBatch = [action];
      }
    }

    // Add duration of final batch
    if (currentParallelBatch.length > 0) {
      totalDuration += Math.max(...currentParallelBatch.map(a => a.estimatedDuration));
    }

    return totalDuration;
  }

  canRunInParallel(action, currentBatch) {
    if (currentBatch.length === 0) return true;

    // Actions affecting the same service cannot run in parallel
    for (const batchAction of currentBatch) {
      const commonServices = action.targetServices.filter(service =>
        batchAction.targetServices.includes(service)
      );
      if (commonServices.length > 0) return false;

      // Certain action types cannot run in parallel
      const conflictingTypes = ['restart', 'rollback', 'failover'];
      if (conflictingTypes.includes(action.type) || conflictingTypes.includes(batchAction.type)) {
        return false;
      }
    }

    return true;
  }

  async executeRecovery(recoveryPlan) {
    try {
      const startTime = new Date();
      const executedActions = [];
      let recoveryStatus = 'in_progress';

      logger.info(`Starting recovery execution for chain ${recoveryPlan.chainId}`);

      // Emit recovery started event
      this.emit('recovery:started', {
        chainId: recoveryPlan.chainId,
        plan: recoveryPlan,
        timestamp: startTime
      });

      // Execute actions in priority order
      for (const action of recoveryPlan.actions) {
        try {
          logger.info(`Executing recovery action: ${action.type} - ${action.description}`);

          const actionStartTime = new Date();
          const actionResult = await this.executeRecoveryAction(action);

          actionResult.startTime = actionStartTime;
          actionResult.endTime = new Date();
          actionResult.duration = actionResult.endTime - actionStartTime;

          executedActions.push(actionResult);

          // Emit action completed event
          this.emit('recovery:action:completed', {
            chainId: recoveryPlan.chainId,
            action,
            result: actionResult,
            timestamp: new Date()
          });

          // Check if action failed and determine if we should continue
          if (!actionResult.success) {
            if (action.priority <= 2) { // Critical actions
              logger.error(`Critical recovery action failed: ${action.type}`);
              recoveryStatus = 'failed';
              break;
            } else {
              logger.warn(`Non-critical recovery action failed: ${action.type}, continuing...`);
            }
          }

          // Brief pause between actions
          await this.delay(2000);

        } catch (error) {
          logger.error(`Recovery action failed: ${action.type}`, error);

          executedActions.push({
            action,
            success: false,
            error: error.message,
            startTime: new Date(),
            endTime: new Date()
          });

          if (action.priority <= 2) {
            recoveryStatus = 'failed';
            break;
          }
        }
      }

      // Wait for stabilization
      logger.info('Waiting for system stabilization...');
      await this.delay(30000); // 30 seconds

      // Verify recovery success
      const verificationResult = await this.verifyRecovery(recoveryPlan.chainId);

      if (verificationResult.successful) {
        recoveryStatus = 'succeeded';
      } else if (recoveryStatus !== 'failed') {
        recoveryStatus = 'partial';
      }

      const endTime = new Date();
      const totalDuration = endTime - startTime;

      const recoveryResult = new RecoveryResult({
        chainId: recoveryPlan.chainId,
        status: recoveryStatus,
        startTime,
        endTime,
        totalDuration,
        actionsExecuted: executedActions,
        verificationResult,
        recoveryPlan
      });

      logger.info(`Recovery execution completed for chain ${recoveryPlan.chainId}: ${recoveryStatus}`);

      return recoveryResult;

    } catch (error) {
      logger.error('Recovery execution failed:', error);
      throw error;
    }
  }

  async executeRecoveryAction(action) {
    try {
      const result = { action, success: false, details: '', error: null };

      switch (action.type) {
        case 'circuit_break':
          result.success = await this.circuitBreakerManager.activateCircuitBreaker(
            action.targetServices,
            action.parameters
          );
          result.details = `Circuit breaker activated for services: ${action.targetServices.join(', ')}`;
          break;

        case 'traffic_redirect':
          result.success = await this.trafficManager.redirectTraffic(
            action.targetServices,
            action.parameters
          );
          result.details = `Traffic redirected for services: ${action.targetServices.join(', ')}`;
          break;

        case 'scale_up':
          result.success = await this.serviceController.scaleServices(
            action.targetServices,
            action.parameters
          );
          result.details = `Services scaled up: ${action.targetServices.join(', ')}`;
          break;

        case 'restart':
          result.success = await this.serviceController.restartServices(
            action.targetServices,
            action.parameters
          );
          result.details = `Services restarted: ${action.targetServices.join(', ')}`;
          break;

        case 'rollback':
          result.success = await this.serviceController.rollbackServices(
            action.targetServices,
            action.parameters
          );
          result.details = `Services rolled back: ${action.targetServices.join(', ')}`;
          break;

        case 'failover':
          result.success = await this.serviceController.failoverServices(
            action.targetServices,
            action.parameters
          );
          result.details = `Failover executed for services: ${action.targetServices.join(', ')}`;
          break;

        case 'health_check':
          result.success = await this.serviceController.performHealthCheck(
            action.targetServices,
            action.parameters
          );
          result.details = `Health check performed for services: ${action.targetServices.join(', ')}`;
          break;

        case 'config_update':
          result.success = await this.serviceController.updateConfiguration(
            action.targetServices,
            action.parameters
          );
          result.details = `Configuration updated for services: ${action.targetServices.join(', ')}`;
          break;

        default:
          result.error = `Unknown recovery action type: ${action.type}`;
          logger.error(result.error);
      }

      return result;

    } catch (error) {
      return {
        action,
        success: false,
        error: error.message,
        details: ''
      };
    }
  }

  async verifyRecovery(chainId) {
    try {
      logger.info(`Verifying recovery for chain ${chainId}`);

      // Wait a bit more for metrics to stabilize
      await this.delay(10000);

      // Check if new anomalies have been detected
      const recentAnomalies = await this.getRecentAnomalies(chainId, 300000); // Last 5 minutes

      // Check chain health metrics
      const healthMetrics = await this.getChainHealthMetrics(chainId);

      // Check service availability
      const serviceAvailability = await this.checkServiceAvailability(chainId);

      // Determine if recovery was successful
      const successful = (
        recentAnomalies.length === 0 &&
        healthMetrics.healthScore > 70 &&
        serviceAvailability.allHealthy
      );

      const verificationResult = {
        successful,
        healthScore: healthMetrics.healthScore,
        recentAnomalies: recentAnomalies.length,
        serviceAvailability,
        verifiedAt: new Date(),
        remainingIssues: []
      };

      if (!successful) {
        verificationResult.remainingIssues = [
          ...recentAnomalies.map(a => `Anomaly: ${a.type} - ${a.description}`),
          ...(healthMetrics.healthScore <= 70 ? ['Low health score'] : []),
          ...(serviceAvailability.unhealthyServices.map(s => `Unhealthy service: ${s}`))
        ];
      }

      logger.info(`Recovery verification completed for chain ${chainId}: ${successful ? 'SUCCESS' : 'ISSUES REMAIN'}`);

      return verificationResult;

    } catch (error) {
      logger.error('Recovery verification failed:', error);
      return {
        successful: false,
        error: error.message,
        verifiedAt: new Date(),
        remainingIssues: ['Verification failed']
      };
    }
  }

  async getRecentAnomalies(chainId, timeWindow) {
    try {
      const query = `
        SELECT * FROM chain_anomalies
        WHERE chain_id = $1 AND timestamp > $2
        ORDER BY timestamp DESC
      `;

      const result = await this.database.query(query, [
        chainId,
        new Date(Date.now() - timeWindow)
      ]);

      return result.rows;

    } catch (error) {
      logger.error('Failed to get recent anomalies:', error);
      return [];
    }
  }

  async getChainHealthMetrics(chainId) {
    try {
      const query = `
        SELECT * FROM chain_health_metrics
        WHERE chain_id = $1
        ORDER BY timestamp DESC
        LIMIT 1
      `;

      const result = await this.database.query(query, [chainId]);

      return result.rows[0] || { healthScore: 0 };

    } catch (error) {
      logger.error('Failed to get chain health metrics:', error);
      return { healthScore: 0 };
    }
  }

  async checkServiceAvailability(chainId) {
    try {
      // Get services involved in the chain
      const services = await this.getChainServices(chainId);

      const healthChecks = await Promise.allSettled(
        services.map(service => this.serviceController.checkServiceHealth(service))
      );

      const healthyServices = [];
      const unhealthyServices = [];

      healthChecks.forEach((result, index) => {
        const service = services[index];
        if (result.status === 'fulfilled' && result.value) {
          healthyServices.push(service);
        } else {
          unhealthyServices.push(service);
        }
      });

      return {
        allHealthy: unhealthyServices.length === 0,
        healthyServices,
        unhealthyServices,
        totalServices: services.length,
        healthPercentage: (healthyServices.length / services.length) * 100
      };

    } catch (error) {
      logger.error('Failed to check service availability:', error);
      return {
        allHealthy: false,
        healthyServices: [],
        unhealthyServices: [],
        totalServices: 0,
        healthPercentage: 0
      };
    }
  }

  async getChainServices(chainId) {
    try {
      const query = `
        SELECT DISTINCT service_name
        FROM chain_events
        WHERE chain_id = $1 AND created_at > $2
      `;

      const result = await this.database.query(query, [
        chainId,
        new Date(Date.now() - 3600000) // Last hour
      ]);

      return result.rows.map(row => row.service_name);

    } catch (error) {
      logger.error('Failed to get chain services:', error);
      return [];
    }
  }

  convertPriorityToNumber(priority) {
    const priorityMap = {
      'immediate': 1,
      'critical': 1,
      'high': 2,
      'medium': 3,
      'low': 4
    };

    return priorityMap[priority] || 3;
  }

  isCriticalService(serviceName) {
    const criticalServices = [
      'api-gateway',
      'trading-engine',
      'user-management',
      'payment-service',
      'database-service'
    ];

    return criticalServices.includes(serviceName);
  }

  async getBackupServices(services) {
    const backupMap = {
      'api-gateway': ['api-gateway-backup'],
      'trading-engine': ['trading-engine-backup'],
      'payment-service': ['payment-service-backup']
    };

    const backups = [];
    for (const service of services) {
      if (backupMap[service]) {
        backups.push(...backupMap[service]);
      }
    }

    return backups;
  }

  async getServiceRecoveryConfig(serviceName) {
    try {
      const query = `
        SELECT * FROM service_recovery_configs
        WHERE service_name = $1
      `;

      const result = await this.database.query(query, [serviceName]);

      return result.rows[0] || {
        preferredRecoveryMethod: 'restart',
        restartDuration: 60000,
        scaleDuration: 120000,
        shutdownTimeout: 30000,
        scaleMultiplier: 2,
        maxInstances: 10
      };

    } catch (error) {
      logger.error('Failed to get service recovery config:', error);
      return null;
    }
  }

  async loadRecoveryConfigurations() {
    try {
      logger.info('Loading recovery configurations...');

      // Load service recovery configurations
      await this.serviceController.loadServiceConfigurations();

      // Load traffic management rules
      await this.trafficManager.loadTrafficRules();

      // Load circuit breaker configurations
      await this.circuitBreakerManager.loadCircuitBreakerConfigs();

      logger.info('Recovery configurations loaded successfully');

    } catch (error) {
      logger.error('Failed to load recovery configurations:', error);
    }
  }

  startRecoveryMonitoring() {
    // Monitor recovery progress
    setInterval(() => {
      this.monitorActiveRecoveries();
    }, 30000); // Every 30 seconds

    logger.info('Recovery monitoring started');
  }

  async monitorActiveRecoveries() {
    try {
      for (const [chainId, recoveryPromise] of this.activeRecoveries) {
        // Check if recovery is taking too long
        const recoveryStartTime = recoveryPromise.startTime || new Date();
        const elapsedTime = Date.now() - recoveryStartTime.getTime();

        if (elapsedTime > this.config.recoveryTimeout) {
          logger.warn(`Recovery timeout for chain ${chainId}`);
          this.handleRecoveryTimeout(chainId);
        }
      }

    } catch (error) {
      logger.error('Failed to monitor active recoveries:', error);
    }
  }

  async handleRecoveryTimeout(chainId) {
    try {
      logger.warn(`Handling recovery timeout for chain ${chainId}`);

      // Cancel the recovery
      this.activeRecoveries.delete(chainId);

      // Emit timeout event
      this.emit('recovery:timeout', {
        chainId,
        timestamp: new Date()
      });

      // Store timeout result
      const timeoutResult = new RecoveryResult({
        chainId,
        status: 'timeout',
        startTime: new Date(),
        endTime: new Date(),
        totalDuration: this.config.recoveryTimeout,
        error: 'Recovery timed out'
      });

      await this.storeRecoveryResult(timeoutResult);

    } catch (error) {
      logger.error('Failed to handle recovery timeout:', error);
    }
  }

  async queueRecovery(impactAssessment, rootCauseAnalysis) {
    // For now, reject additional recoveries
    // In production, implement a proper queuing system
    throw new Error('Maximum concurrent recoveries reached. Please try again later.');
  }

  async storeRecoveryResult(result) {
    try {
      const query = `
        INSERT INTO recovery_results
        (chain_id, status, start_time, end_time, total_duration,
         actions_executed, verification_result, raw_data)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
      `;

      await this.database.query(query, [
        result.chainId,
        result.status,
        result.startTime,
        result.endTime,
        result.totalDuration,
        JSON.stringify(result.actionsExecuted || []),
        JSON.stringify(result.verificationResult || {}),
        JSON.stringify(result)
      ]);

    } catch (error) {
      logger.error('Failed to store recovery result:', error);
    }
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}