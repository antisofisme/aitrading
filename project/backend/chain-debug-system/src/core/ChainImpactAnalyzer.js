/**
 * ChainImpactAnalyzer
 * Predictive impact assessment and cascade risk analysis
 */

import EventEmitter from 'eventemitter3';
import logger from '../utils/logger.js';
import { DependencyGraphAnalyzer } from '../analytics/DependencyGraphAnalyzer.js';
import { ImpactAssessment } from '../models/ImpactAssessment.js';
import { CascadeRisk } from '../models/CascadeRisk.js';
import { UserImpactCalculator } from '../analytics/UserImpactCalculator.js';
import { BusinessImpactCalculator } from '../analytics/BusinessImpactCalculator.js';

export class ChainImpactAnalyzer extends EventEmitter {
  constructor({ database, redis, metricsCollector }) {
    super();

    this.database = database;
    this.redis = redis;
    this.metricsCollector = metricsCollector;

    this.dependencyGraphAnalyzer = null;
    this.userImpactCalculator = null;
    this.businessImpactCalculator = null;

    this.isHealthy = true;

    // Cache for dependency graphs
    this.graphCache = new Map();
    this.cacheExpiry = 300000; // 5 minutes
  }

  async initialize() {
    try {
      logger.info('Initializing ChainImpactAnalyzer...');

      // Initialize analytics components
      this.dependencyGraphAnalyzer = new DependencyGraphAnalyzer({
        database: this.database,
        redis: this.redis
      });

      this.userImpactCalculator = new UserImpactCalculator({
        database: this.database,
        redis: this.redis
      });

      this.businessImpactCalculator = new BusinessImpactCalculator({
        database: this.database,
        redis: this.redis
      });

      await Promise.all([
        this.dependencyGraphAnalyzer.initialize(),
        this.userImpactCalculator.initialize(),
        this.businessImpactCalculator.initialize()
      ]);

      // Load dependency mappings
      await this.loadDependencyMappings();

      logger.info('ChainImpactAnalyzer initialized successfully');

    } catch (error) {
      logger.error('Failed to initialize ChainImpactAnalyzer:', error);
      this.isHealthy = false;
      throw error;
    }
  }

  async assessImpact(chainId, anomalies) {
    try {
      logger.info(`Assessing impact for chain ${chainId} with ${anomalies.length} anomalies`);

      // Get affected services from anomalies and chain analysis
      const affectedServices = await this.getAffectedServices(chainId, anomalies);

      if (affectedServices.length === 0) {
        logger.warn(`No affected services found for chain ${chainId}`);
        return null;
      }

      // Calculate user impact
      const userImpact = await this.userImpactCalculator.calculateImpact(affectedServices);

      // Calculate business impact
      const businessImpact = await this.businessImpactCalculator.calculateImpact(
        affectedServices,
        userImpact
      );

      // Assess cascade risk
      const cascadeRisk = await this.assessCascadeRisk(affectedServices);

      // Determine priority level
      const priorityLevel = this.determinePriorityLevel(userImpact, businessImpact, cascadeRisk);

      // Estimate recovery time
      const estimatedRecoveryTime = await this.estimateRecoveryTime(affectedServices);

      // Create comprehensive impact assessment
      const impactAssessment = new ImpactAssessment({
        chainId,
        affectedServices,
        userImpact,
        businessImpact,
        cascadeRisk,
        priorityLevel,
        estimatedRecoveryTime,
        timestamp: new Date(),
        anomalies
      });

      // Store assessment
      await this.storeImpactAssessment(impactAssessment);

      // Emit impact assessment event
      this.emit('impact:assessed', {
        chainId,
        impactAssessment,
        timestamp: new Date()
      });

      logger.info(`Impact assessment completed for chain ${chainId}: ${priorityLevel} priority`);

      return impactAssessment;

    } catch (error) {
      logger.error(`Failed to assess impact for chain ${chainId}:`, error);
      throw error;
    }
  }

  async getAffectedServices(chainId, anomalies) {
    try {
      const affectedServices = new Set();

      // Get services from chain events
      const chainServices = await this.getChainServices(chainId);
      chainServices.forEach(service => affectedServices.add(service));

      // Get services from anomalies
      for (const anomaly of anomalies) {
        if (anomaly.affectedServices) {
          anomaly.affectedServices.forEach(service => affectedServices.add(service));
        }

        // Extract services from bottleneck information
        if (anomaly.type === 'dependency_failure' && anomaly.rawData?.bottleneckServices) {
          anomaly.rawData.bottleneckServices.forEach(bottleneck => {
            affectedServices.add(bottleneck.sourceService);
            affectedServices.add(bottleneck.targetService);
          });
        }
      }

      return Array.from(affectedServices);

    } catch (error) {
      logger.error('Failed to get affected services:', error);
      return [];
    }
  }

  async getChainServices(chainId) {
    try {
      const query = `
        SELECT DISTINCT service_name
        FROM chain_events
        WHERE chain_id = $1 AND created_at > $2
        ORDER BY service_name
      `;

      const result = await this.database.query(query, [
        chainId,
        new Date(Date.now() - 3600000) // Last hour
      ]);

      return result.rows.map(row => row.service_name);

    } catch (error) {
      logger.error(`Failed to get services for chain ${chainId}:`, error);
      return [];
    }
  }

  async assessCascadeRisk(affectedServices) {
    try {
      const cascadePaths = [];
      let totalRiskScore = 0;

      for (const service of affectedServices) {
        // Get downstream dependencies
        const downstreamServices = await this.getDownstreamServices(service);

        for (const downstreamService of downstreamServices) {
          // Calculate cascade probability
          const cascadeProbability = await this.calculateCascadeProbability(
            service,
            downstreamService
          );

          if (cascadeProbability > 0.3) { // 30% threshold
            const impactSeverity = await this.estimateCascadeImpact(downstreamService);

            cascadePaths.push({
              sourceService: service,
              targetService: downstreamService,
              probability: cascadeProbability,
              impactSeverity,
              estimatedUsers: await this.estimateAffectedUsers(downstreamService),
              recoveryComplexity: await this.estimateRecoveryComplexity(downstreamService)
            });

            totalRiskScore += cascadeProbability * impactSeverity;
          }
        }
      }

      // Generate mitigation strategies
      const mitigationStrategies = this.generateCascadeMitigationStrategies(cascadePaths);

      return new CascadeRisk({
        riskScore: Math.min(totalRiskScore, 1.0),
        cascadePaths,
        mitigationStrategies,
        affectedServices,
        timestamp: new Date()
      });

    } catch (error) {
      logger.error('Failed to assess cascade risk:', error);
      return new CascadeRisk({
        riskScore: 0,
        cascadePaths: [],
        mitigationStrategies: [],
        affectedServices,
        timestamp: new Date()
      });
    }
  }

  async getDownstreamServices(serviceName) {
    try {
      // Check cache first
      const cacheKey = `downstream:${serviceName}`;
      const cached = this.graphCache.get(cacheKey);

      if (cached && Date.now() - cached.timestamp < this.cacheExpiry) {
        return cached.data;
      }

      // Query dependency graph
      const query = `
        SELECT DISTINCT ce2.service_name as downstream_service
        FROM chain_events ce1
        JOIN chain_events ce2 ON ce1.chain_id = ce2.chain_id
        WHERE ce1.service_name = $1
          AND ce1.event_type = 'dependency_call'
          AND ce2.created_at > ce1.created_at
          AND ce2.created_at < ce1.created_at + INTERVAL '10 seconds'
          AND ce1.created_at > $2
        ORDER BY downstream_service
      `;

      const result = await this.database.query(query, [
        serviceName,
        new Date(Date.now() - 86400000) // Last 24 hours
      ]);

      const downstreamServices = result.rows.map(row => row.downstream_service);

      // Cache result
      this.graphCache.set(cacheKey, {
        data: downstreamServices,
        timestamp: Date.now()
      });

      return downstreamServices;

    } catch (error) {
      logger.error(`Failed to get downstream services for ${serviceName}:`, error);
      return [];
    }
  }

  async calculateCascadeProbability(sourceService, targetService) {
    try {
      // Get historical cascade data
      const historicalCascades = await this.getHistoricalCascades(sourceService, targetService);

      // Get dependency strength
      const dependencyStrength = await this.getDependencyStrength(sourceService, targetService);

      // Get service resilience metrics
      const targetResilience = await this.getServiceResilience(targetService);

      // Calculate probability using weighted factors
      const historicalFactor = historicalCascades.length > 0 ?
        Math.min(historicalCascades.length / 10, 0.8) : 0.1;

      const dependencyFactor = dependencyStrength;
      const resilienceFactor = 1 - targetResilience;

      // Weighted combination
      const probability = (
        historicalFactor * 0.4 +
        dependencyFactor * 0.4 +
        resilienceFactor * 0.2
      );

      return Math.min(Math.max(probability, 0), 1);

    } catch (error) {
      logger.error('Failed to calculate cascade probability:', error);
      return 0.5; // Default moderate probability
    }
  }

  async getHistoricalCascades(sourceService, targetService) {
    try {
      const query = `
        SELECT * FROM cascade_history
        WHERE source_service = $1 AND target_service = $2
          AND created_at > $3
        ORDER BY created_at DESC
      `;

      const result = await this.database.query(query, [
        sourceService,
        targetService,
        new Date(Date.now() - 2592000000) // Last 30 days
      ]);

      return result.rows;

    } catch (error) {
      logger.error('Failed to get historical cascades:', error);
      return [];
    }
  }

  async getDependencyStrength(sourceService, targetService) {
    try {
      const query = `
        SELECT
          COUNT(*) as call_count,
          AVG(CASE WHEN ce.status = 'success' THEN 1 ELSE 0 END) as success_rate,
          AVG(duration_ms) as avg_duration
        FROM chain_events ce
        WHERE ce.service_name = $1
          AND ce.dependencies @> $2
          AND ce.created_at > $3
      `;

      const result = await this.database.query(query, [
        sourceService,
        JSON.stringify([{ target_service: targetService }]),
        new Date(Date.now() - 86400000) // Last 24 hours
      ]);

      const stats = result.rows[0];

      if (!stats || stats.call_count === 0) {
        return 0.1; // Low dependency strength
      }

      // Calculate strength based on call frequency and reliability
      const frequencyScore = Math.min(stats.call_count / 100, 1); // Normalize
      const reliabilityScore = stats.success_rate || 0;

      return (frequencyScore * 0.6 + reliabilityScore * 0.4);

    } catch (error) {
      logger.error('Failed to get dependency strength:', error);
      return 0.5; // Default moderate strength
    }
  }

  async getServiceResilience(serviceName) {
    try {
      const query = `
        SELECT
          AVG(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_rate,
          AVG(duration_ms) as avg_duration,
          COUNT(*) as total_calls
        FROM chain_events
        WHERE service_name = $1 AND created_at > $2
      `;

      const result = await this.database.query(query, [
        serviceName,
        new Date(Date.now() - 86400000) // Last 24 hours
      ]);

      const stats = result.rows[0];

      if (!stats || stats.total_calls === 0) {
        return 0.5; // Default moderate resilience
      }

      // Calculate resilience based on success rate and performance stability
      const successRate = stats.success_rate || 0;
      const performanceStability = Math.max(0, 1 - (stats.avg_duration / 5000)); // 5s baseline

      return (successRate * 0.7 + performanceStability * 0.3);

    } catch (error) {
      logger.error('Failed to get service resilience:', error);
      return 0.5; // Default moderate resilience
    }
  }

  async estimateCascadeImpact(serviceName) {
    try {
      // Get service criticality score
      const criticalityScore = await this.getServiceCriticality(serviceName);

      // Get user base size
      const userBaseSize = await this.getServiceUserBase(serviceName);

      // Get business value
      const businessValue = await this.getServiceBusinessValue(serviceName);

      // Calculate overall impact severity (0-1)
      const impactSeverity = (
        criticalityScore * 0.4 +
        Math.min(userBaseSize / 10000, 1) * 0.3 +
        businessValue * 0.3
      );

      return Math.min(Math.max(impactSeverity, 0), 1);

    } catch (error) {
      logger.error('Failed to estimate cascade impact:', error);
      return 0.5; // Default moderate impact
    }
  }

  async getServiceCriticality(serviceName) {
    try {
      // Define criticality mapping
      const criticalityMap = {
        'api-gateway': 0.9,
        'trading-engine': 0.95,
        'user-management': 0.8,
        'payment-service': 0.85,
        'notification-service': 0.6,
        'monitoring': 0.4,
        'billing-service': 0.7,
        'compliance-monitor': 0.8,
        'data-bridge': 0.75,
        'database-service': 0.9,
        'ai-orchestration': 0.8,
        'ml-ensemble': 0.7,
        'realtime-inference-engine': 0.85
      };

      return criticalityMap[serviceName] || 0.5; // Default moderate criticality

    } catch (error) {
      logger.error('Failed to get service criticality:', error);
      return 0.5;
    }
  }

  async getServiceUserBase(serviceName) {
    try {
      const query = `
        SELECT COUNT(DISTINCT user_id) as unique_users
        FROM chain_events
        WHERE service_name = $1
          AND user_id IS NOT NULL
          AND created_at > $2
      `;

      const result = await this.database.query(query, [
        serviceName,
        new Date(Date.now() - 86400000) // Last 24 hours
      ]);

      return result.rows[0]?.unique_users || 0;

    } catch (error) {
      logger.error('Failed to get service user base:', error);
      return 0;
    }
  }

  async getServiceBusinessValue(serviceName) {
    try {
      // Define business value mapping (0-1)
      const businessValueMap = {
        'trading-engine': 1.0,
        'payment-service': 0.95,
        'api-gateway': 0.85,
        'user-management': 0.8,
        'billing-service': 0.9,
        'compliance-monitor': 0.7,
        'realtime-inference-engine': 0.85,
        'ai-orchestration': 0.75,
        'data-bridge': 0.65,
        'notification-service': 0.4,
        'monitoring': 0.3
      };

      return businessValueMap[serviceName] || 0.5;

    } catch (error) {
      logger.error('Failed to get service business value:', error);
      return 0.5;
    }
  }

  generateCascadeMitigationStrategies(cascadePaths) {
    const strategies = [];

    if (cascadePaths.length === 0) {
      return strategies;
    }

    // Group by source service
    const serviceGroups = cascadePaths.reduce((acc, path) => {
      if (!acc[path.sourceService]) {
        acc[path.sourceService] = [];
      }
      acc[path.sourceService].push(path);
      return acc;
    }, {});

    for (const [sourceService, paths] of Object.entries(serviceGroups)) {
      const highRiskPaths = paths.filter(p => p.probability > 0.7);

      if (highRiskPaths.length > 0) {
        strategies.push({
          type: 'circuit_breaker',
          description: `Activate circuit breaker for ${sourceService}`,
          targetService: sourceService,
          priority: 'high',
          estimatedEffectiveness: 0.8
        });
      }

      const criticalTargets = paths.filter(p => p.impactSeverity > 0.8);

      if (criticalTargets.length > 0) {
        strategies.push({
          type: 'traffic_isolation',
          description: `Isolate traffic to critical services: ${criticalTargets.map(p => p.targetService).join(', ')}`,
          targetServices: criticalTargets.map(p => p.targetService),
          priority: 'critical',
          estimatedEffectiveness: 0.9
        });
      }
    }

    // Add preemptive scaling strategy
    const allTargets = [...new Set(cascadePaths.map(p => p.targetService))];
    if (allTargets.length > 0) {
      strategies.push({
        type: 'preemptive_scaling',
        description: `Scale up potential cascade targets: ${allTargets.join(', ')}`,
        targetServices: allTargets,
        priority: 'medium',
        estimatedEffectiveness: 0.6
      });
    }

    return strategies.sort((a, b) => {
      const priorityOrder = { critical: 3, high: 2, medium: 1, low: 0 };
      return priorityOrder[b.priority] - priorityOrder[a.priority];
    });
  }

  determinePriorityLevel(userImpact, businessImpact, cascadeRisk) {
    const userScore = userImpact.totalAffectedUsers / 1000; // Normalize per 1k users
    const businessScore = businessImpact.estimatedLoss / 10000; // Normalize per $10k
    const cascadeScore = cascadeRisk.riskScore;

    const overallScore = (userScore * 0.3 + businessScore * 0.4 + cascadeScore * 0.3);

    if (overallScore > 0.8) return 'critical';
    if (overallScore > 0.6) return 'high';
    if (overallScore > 0.3) return 'medium';
    return 'low';
  }

  async estimateRecoveryTime(affectedServices) {
    try {
      let totalRecoveryTime = 0;

      for (const service of affectedServices) {
        const serviceRecoveryTime = await this.getServiceRecoveryTime(service);
        totalRecoveryTime = Math.max(totalRecoveryTime, serviceRecoveryTime);
      }

      // Add coordination overhead for multiple services
      if (affectedServices.length > 1) {
        totalRecoveryTime *= (1 + (affectedServices.length - 1) * 0.2);
      }

      return Math.round(totalRecoveryTime);

    } catch (error) {
      logger.error('Failed to estimate recovery time:', error);
      return 300; // Default 5 minutes
    }
  }

  async getServiceRecoveryTime(serviceName) {
    try {
      // Get historical recovery times
      const query = `
        SELECT AVG(recovery_time_seconds) as avg_recovery_time
        FROM recovery_history
        WHERE service_name = $1 AND created_at > $2
      `;

      const result = await this.database.query(query, [
        serviceName,
        new Date(Date.now() - 2592000000) // Last 30 days
      ]);

      const avgRecoveryTime = result.rows[0]?.avg_recovery_time;

      if (avgRecoveryTime) {
        return avgRecoveryTime;
      }

      // Default recovery times by service type
      const defaultRecoveryTimes = {
        'api-gateway': 120,
        'trading-engine': 300,
        'user-management': 180,
        'payment-service': 240,
        'database-service': 600,
        'notification-service': 90,
        'monitoring': 60
      };

      return defaultRecoveryTimes[serviceName] || 180; // Default 3 minutes

    } catch (error) {
      logger.error('Failed to get service recovery time:', error);
      return 180;
    }
  }

  async loadDependencyMappings() {
    try {
      logger.info('Loading service dependency mappings...');

      // Load and cache service dependencies
      await this.dependencyGraphAnalyzer.buildSystemDependencyGraph();

      logger.info('Dependency mappings loaded successfully');

    } catch (error) {
      logger.error('Failed to load dependency mappings:', error);
    }
  }

  async storeImpactAssessment(impactAssessment) {
    try {
      const query = `
        INSERT INTO impact_assessments
        (chain_id, affected_services, user_impact, business_impact, cascade_risk,
         priority_level, estimated_recovery_time, timestamp, raw_data)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
      `;

      await this.database.query(query, [
        impactAssessment.chainId,
        JSON.stringify(impactAssessment.affectedServices),
        JSON.stringify(impactAssessment.userImpact),
        JSON.stringify(impactAssessment.businessImpact),
        JSON.stringify(impactAssessment.cascadeRisk),
        impactAssessment.priorityLevel,
        impactAssessment.estimatedRecoveryTime,
        impactAssessment.timestamp,
        JSON.stringify(impactAssessment)
      ]);

    } catch (error) {
      logger.error('Failed to store impact assessment:', error);
    }
  }

  async estimateAffectedUsers(serviceName) {
    try {
      const userBase = await this.getServiceUserBase(serviceName);

      // Estimate percentage of users affected based on service type
      const affectedPercentageMap = {
        'api-gateway': 1.0, // All users
        'trading-engine': 0.8, // Active traders
        'user-management': 1.0, // All users
        'payment-service': 0.6, // Users making transactions
        'notification-service': 0.9, // Most users
        'monitoring': 0.0 // Internal only
      };

      const affectedPercentage = affectedPercentageMap[serviceName] || 0.5;

      return Math.round(userBase * affectedPercentage);

    } catch (error) {
      logger.error('Failed to estimate affected users:', error);
      return 0;
    }
  }

  async estimateRecoveryComplexity(serviceName) {
    try {
      // Define complexity scores (0-1)
      const complexityMap = {
        'database-service': 0.9,
        'trading-engine': 0.8,
        'payment-service': 0.7,
        'api-gateway': 0.6,
        'user-management': 0.6,
        'notification-service': 0.3,
        'monitoring': 0.2
      };

      return complexityMap[serviceName] || 0.5;

    } catch (error) {
      logger.error('Failed to estimate recovery complexity:', error);
      return 0.5;
    }
  }
}