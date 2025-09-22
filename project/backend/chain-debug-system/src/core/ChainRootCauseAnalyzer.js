/**
 * ChainRootCauseAnalyzer
 * AI-powered root cause analysis with pattern recognition
 */

import EventEmitter from 'eventemitter3';
import logger from '../utils/logger.js';
import { ChainPatternRecognizer } from '../ml/ChainPatternRecognizer.js';
import { CorrelationAnalyzer } from '../analytics/CorrelationAnalyzer.js';
import { ExternalFactorDetector } from '../analytics/ExternalFactorDetector.js';
import { RootCauseAnalysis } from '../models/RootCauseAnalysis.js';
import { RootCause } from '../models/RootCause.js';

export class ChainRootCauseAnalyzer extends EventEmitter {
  constructor({ database, redis, metricsCollector }) {
    super();

    this.database = database;
    this.redis = redis;
    this.metricsCollector = metricsCollector;

    this.patternRecognizer = null;
    this.correlationAnalyzer = null;
    this.externalFactorDetector = null;

    this.isHealthy = true;

    // Root cause patterns cache
    this.patternCache = new Map();
    this.cacheExpiry = 3600000; // 1 hour

    // Confidence thresholds
    this.confidenceThresholds = {
      high: 0.8,
      medium: 0.6,
      low: 0.4
    };
  }

  async initialize() {
    try {
      logger.info('Initializing ChainRootCauseAnalyzer...');

      // Initialize pattern recognition
      this.patternRecognizer = new ChainPatternRecognizer({
        database: this.database,
        redis: this.redis
      });

      // Initialize correlation analysis
      this.correlationAnalyzer = new CorrelationAnalyzer({
        database: this.database,
        redis: this.redis
      });

      // Initialize external factor detection
      this.externalFactorDetector = new ExternalFactorDetector({
        database: this.database,
        redis: this.redis
      });

      await Promise.all([
        this.patternRecognizer.initialize(),
        this.correlationAnalyzer.initialize(),
        this.externalFactorDetector.initialize()
      ]);

      // Load known patterns
      await this.loadKnownPatterns();

      logger.info('ChainRootCauseAnalyzer initialized successfully');

    } catch (error) {
      logger.error('Failed to initialize ChainRootCauseAnalyzer:', error);
      this.isHealthy = false;
      throw error;
    }
  }

  async analyzeRootCause(chainId, anomalies) {
    try {
      logger.info(`Analyzing root cause for chain ${chainId} with ${anomalies.length} anomalies`);

      // Get comprehensive chain data
      const chainTrace = await this.getChainTrace(chainId);
      const historicalData = await this.getHistoricalChainData(chainId, 7); // 7 days

      if (!chainTrace) {
        logger.warn(`No chain trace found for ${chainId}`);
        return null;
      }

      // Perform multi-dimensional analysis
      const analysisResults = await Promise.allSettled([
        this.patternRecognizer.analyzePatterns(chainTrace, historicalData, anomalies),
        this.correlationAnalyzer.findCorrelations(anomalies, historicalData, chainTrace),
        this.externalFactorDetector.detectFactors(chainTrace.startTime, chainTrace.endTime)
      ]);

      // Extract results
      const patterns = analysisResults[0].status === 'fulfilled' ? analysisResults[0].value : [];
      const correlations = analysisResults[1].status === 'fulfilled' ? analysisResults[1].value : [];
      const externalFactors = analysisResults[2].status === 'fulfilled' ? analysisResults[2].value : [];

      // Log any failures
      analysisResults.forEach((result, index) => {
        if (result.status === 'rejected') {
          const components = ['pattern recognition', 'correlation analysis', 'external factor detection'];
          logger.error(`${components[index]} failed:`, result.reason);
        }
      });

      // Determine primary root cause
      const rootCause = this.determinePrimaryRootCause(patterns, correlations, externalFactors);

      // Generate evidence and recommendations
      const evidence = await this.gatherEvidence(rootCause, chainTrace, anomalies);
      const recommendations = this.generateRecommendedActions(rootCause, evidence);

      // Calculate confidence score
      const confidenceScore = this.calculateConfidenceScore(rootCause, evidence, patterns, correlations);

      // Create comprehensive analysis
      const rootCauseAnalysis = new RootCauseAnalysis({
        chainId,
        primaryRootCause: rootCause,
        contributingFactors: [...patterns, ...correlations, ...externalFactors],
        confidenceScore,
        evidence,
        recommendedActions: recommendations,
        analysisTimestamp: new Date(),
        anomalies,
        chainTrace
      });

      // Store analysis
      await this.storeRootCauseAnalysis(rootCauseAnalysis);

      // Emit analysis completion event
      this.emit('rootcause:analyzed', {
        chainId,
        rootCauseAnalysis,
        timestamp: new Date()
      });

      logger.info(`Root cause analysis completed for chain ${chainId}: ${rootCause.type} (confidence: ${confidenceScore.toFixed(2)})`);

      return rootCauseAnalysis;

    } catch (error) {
      logger.error(`Failed to analyze root cause for chain ${chainId}:`, error);
      throw error;
    }
  }

  determinePrimaryRootCause(patterns, correlations, externalFactors) {
    try {
      // Combine all potential causes
      const allFactors = [
        ...patterns.map(p => ({ ...p, source: 'pattern' })),
        ...correlations.map(c => ({ ...c, source: 'correlation' })),
        ...externalFactors.map(e => ({ ...e, source: 'external' }))
      ];

      if (allFactors.length === 0) {
        return new RootCause({
          type: 'unknown',
          description: 'Unable to determine root cause from available data',
          confidence: 0.0,
          category: 'unknown',
          source: 'analysis'
        });
      }

      // Sort by confidence score
      allFactors.sort((a, b) => (b.confidence || 0) - (a.confidence || 0));

      const topFactor = allFactors[0];

      // Convert to RootCause format
      return new RootCause({
        type: topFactor.type || 'unknown',
        description: topFactor.description || 'Root cause identified through automated analysis',
        confidence: topFactor.confidence || 0.5,
        category: this.categorizeRootCause(topFactor.type),
        source: topFactor.source,
        rawData: topFactor
      });

    } catch (error) {
      logger.error('Failed to determine primary root cause:', error);
      return new RootCause({
        type: 'analysis_error',
        description: 'Error occurred during root cause analysis',
        confidence: 0.0,
        category: 'system',
        source: 'error'
      });
    }
  }

  categorizeRootCause(type) {
    const categoryMap = {
      // Performance issues
      'performance_degradation': 'performance',
      'memory_leak': 'performance',
      'cpu_spike': 'performance',
      'slow_query': 'performance',
      'bottleneck': 'performance',

      // Infrastructure issues
      'network_latency': 'infrastructure',
      'database_connection': 'infrastructure',
      'disk_space': 'infrastructure',
      'resource_exhaustion': 'infrastructure',

      // Code issues
      'logic_error': 'code',
      'exception': 'code',
      'timeout': 'code',
      'deadlock': 'code',

      // External dependencies
      'external_api_failure': 'external',
      'third_party_timeout': 'external',
      'market_data_lag': 'external',

      // Configuration issues
      'config_error': 'configuration',
      'deployment_issue': 'configuration',
      'environment_mismatch': 'configuration',

      // Security issues
      'rate_limiting': 'security',
      'authentication_failure': 'security',
      'authorization_error': 'security',

      // Default
      'unknown': 'unknown'
    };

    return categoryMap[type] || 'unknown';
  }

  async gatherEvidence(rootCause, chainTrace, anomalies) {
    try {
      const evidence = {
        logs: [],
        metrics: [],
        events: [],
        traces: [],
        systemState: {}
      };

      // Gather relevant logs
      evidence.logs = await this.getRelevantLogs(rootCause, chainTrace);

      // Gather performance metrics
      evidence.metrics = await this.getRelevantMetrics(rootCause, chainTrace);

      // Gather chain events
      evidence.events = await this.getRelevantEvents(rootCause, chainTrace);

      // Gather distributed traces
      evidence.traces = await this.getRelevantTraces(rootCause, chainTrace);

      // Capture system state
      evidence.systemState = await this.captureSystemState(rootCause, chainTrace);

      // Add anomaly context
      evidence.anomalies = anomalies.map(anomaly => ({
        type: anomaly.type,
        severity: anomaly.severity,
        description: anomaly.description,
        metric: anomaly.affectedMetric,
        deviation: anomaly.currentValue / (anomaly.baselineValue || 1)
      }));

      return evidence;

    } catch (error) {
      logger.error('Failed to gather evidence:', error);
      return { logs: [], metrics: [], events: [], traces: [], systemState: {} };
    }
  }

  async getRelevantLogs(rootCause, chainTrace) {
    try {
      const timeBuffer = 300000; // 5 minutes before and after
      const startTime = new Date(chainTrace.startTime.getTime() - timeBuffer);
      const endTime = new Date(chainTrace.endTime.getTime() + timeBuffer);

      // Build log search criteria based on root cause type
      const searchCriteria = this.buildLogSearchCriteria(rootCause);

      const query = `
        SELECT * FROM application_logs
        WHERE timestamp BETWEEN $1 AND $2
          AND (
            message ILIKE ANY($3) OR
            level IN ('ERROR', 'WARN') OR
            service_name = ANY($4)
          )
        ORDER BY timestamp DESC
        LIMIT 100
      `;

      const result = await this.database.query(query, [
        startTime,
        endTime,
        searchCriteria.keywords,
        chainTrace.involvedServices || []
      ]);

      return result.rows.map(row => ({
        timestamp: row.timestamp,
        level: row.level,
        service: row.service_name,
        message: row.message,
        stackTrace: row.stack_trace,
        metadata: row.metadata
      }));

    } catch (error) {
      logger.error('Failed to get relevant logs:', error);
      return [];
    }
  }

  buildLogSearchCriteria(rootCause) {
    const criteriaMap = {
      'performance_degradation': {
        keywords: ['%slow%', '%timeout%', '%performance%', '%latency%']
      },
      'memory_leak': {
        keywords: ['%memory%', '%heap%', '%oom%', '%garbage%']
      },
      'database_connection': {
        keywords: ['%connection%', '%database%', '%pool%', '%sql%']
      },
      'network_latency': {
        keywords: ['%network%', '%connection%', '%timeout%', '%unreachable%']
      },
      'external_api_failure': {
        keywords: ['%api%', '%http%', '%request%', '%response%']
      },
      'deadlock': {
        keywords: ['%deadlock%', '%lock%', '%blocked%', '%wait%']
      }
    };

    return criteriaMap[rootCause.type] || { keywords: ['%error%', '%exception%', '%failed%'] };
  }

  async getRelevantMetrics(rootCause, chainTrace) {
    try {
      const timeBuffer = 300000; // 5 minutes buffer
      const startTime = new Date(chainTrace.startTime.getTime() - timeBuffer);
      const endTime = new Date(chainTrace.endTime.getTime() + timeBuffer);

      // Select metrics based on root cause type
      const metricNames = this.getRelevantMetricNames(rootCause);

      const query = `
        SELECT * FROM system_metrics
        WHERE timestamp BETWEEN $1 AND $2
          AND metric_name = ANY($3)
        ORDER BY timestamp DESC
      `;

      const result = await this.database.query(query, [
        startTime,
        endTime,
        metricNames
      ]);

      return result.rows.map(row => ({
        timestamp: row.timestamp,
        name: row.metric_name,
        value: row.value,
        service: row.service_name,
        tags: row.tags
      }));

    } catch (error) {
      logger.error('Failed to get relevant metrics:', error);
      return [];
    }
  }

  getRelevantMetricNames(rootCause) {
    const metricMap = {
      'performance_degradation': ['response_time', 'cpu_usage', 'memory_usage', 'request_rate'],
      'memory_leak': ['memory_usage', 'heap_size', 'gc_time', 'memory_allocation_rate'],
      'database_connection': ['db_connections', 'db_response_time', 'db_error_rate', 'connection_pool_size'],
      'network_latency': ['network_latency', 'tcp_connections', 'packet_loss', 'bandwidth_usage'],
      'cpu_spike': ['cpu_usage', 'cpu_load', 'thread_count', 'process_count'],
      'disk_space': ['disk_usage', 'disk_io', 'file_descriptors', 'inode_usage']
    };

    return metricMap[rootCause.type] || ['response_time', 'error_rate', 'cpu_usage', 'memory_usage'];
  }

  async getRelevantEvents(rootCause, chainTrace) {
    try {
      const timeBuffer = 300000; // 5 minutes buffer
      const startTime = new Date(chainTrace.startTime.getTime() - timeBuffer);
      const endTime = new Date(chainTrace.endTime.getTime() + timeBuffer);

      const query = `
        SELECT * FROM chain_events
        WHERE chain_id = $1
          OR (created_at BETWEEN $2 AND $3 AND event_type IN ('error', 'timeout', 'exception'))
        ORDER BY created_at DESC
        LIMIT 200
      `;

      const result = await this.database.query(query, [
        chainTrace.chainId,
        startTime,
        endTime
      ]);

      return result.rows.map(row => ({
        timestamp: row.created_at,
        type: row.event_type,
        service: row.service_name,
        status: row.status,
        duration: row.duration_ms,
        error: row.error_message,
        metadata: row.metadata
      }));

    } catch (error) {
      logger.error('Failed to get relevant events:', error);
      return [];
    }
  }

  async getRelevantTraces(rootCause, chainTrace) {
    try {
      // Get distributed tracing data if available
      const query = `
        SELECT * FROM distributed_traces
        WHERE chain_id = $1
          OR (start_time BETWEEN $2 AND $3)
        ORDER BY start_time DESC
        LIMIT 50
      `;

      const result = await this.database.query(query, [
        chainTrace.chainId,
        new Date(chainTrace.startTime.getTime() - 60000),
        new Date(chainTrace.endTime.getTime() + 60000)
      ]);

      return result.rows.map(row => ({
        traceId: row.trace_id,
        spanId: row.span_id,
        service: row.service_name,
        operation: row.operation_name,
        startTime: row.start_time,
        duration: row.duration_ms,
        tags: row.tags,
        annotations: row.annotations
      }));

    } catch (error) {
      logger.error('Failed to get relevant traces:', error);
      return [];
    }
  }

  async captureSystemState(rootCause, chainTrace) {
    try {
      const systemState = {};

      // Get current system metrics
      const currentMetrics = await this.getCurrentSystemMetrics();
      systemState.metrics = currentMetrics;

      // Get service health status
      const serviceHealth = await this.getServiceHealthStatus(chainTrace.involvedServices);
      systemState.serviceHealth = serviceHealth;

      // Get resource utilization
      const resourceUtilization = await this.getResourceUtilization();
      systemState.resources = resourceUtilization;

      // Get active connections and pools
      const connectionState = await this.getConnectionState();
      systemState.connections = connectionState;

      return systemState;

    } catch (error) {
      logger.error('Failed to capture system state:', error);
      return {};
    }
  }

  generateRecommendedActions(rootCause, evidence) {
    const recommendations = [];

    // Generate actions based on root cause type
    switch (rootCause.category) {
      case 'performance':
        recommendations.push(...this.generatePerformanceRecommendations(rootCause, evidence));
        break;
      case 'infrastructure':
        recommendations.push(...this.generateInfrastructureRecommendations(rootCause, evidence));
        break;
      case 'code':
        recommendations.push(...this.generateCodeRecommendations(rootCause, evidence));
        break;
      case 'external':
        recommendations.push(...this.generateExternalRecommendations(rootCause, evidence));
        break;
      case 'configuration':
        recommendations.push(...this.generateConfigurationRecommendations(rootCause, evidence));
        break;
      case 'security':
        recommendations.push(...this.generateSecurityRecommendations(rootCause, evidence));
        break;
      default:
        recommendations.push(...this.generateGenericRecommendations(rootCause, evidence));
    }

    // Sort by priority and feasibility
    return recommendations.sort((a, b) => {
      const priorityOrder = { immediate: 4, high: 3, medium: 2, low: 1 };
      return priorityOrder[b.priority] - priorityOrder[a.priority];
    });
  }

  generatePerformanceRecommendations(rootCause, evidence) {
    const recommendations = [];

    if (rootCause.type === 'performance_degradation') {
      recommendations.push({
        action: 'scale_service',
        description: 'Scale up affected services to handle increased load',
        priority: 'high',
        estimatedImpact: 0.8,
        feasibility: 0.9,
        estimatedTime: 300 // 5 minutes
      });

      recommendations.push({
        action: 'optimize_queries',
        description: 'Analyze and optimize slow database queries',
        priority: 'medium',
        estimatedImpact: 0.7,
        feasibility: 0.6,
        estimatedTime: 1800 // 30 minutes
      });
    }

    if (rootCause.type === 'memory_leak') {
      recommendations.push({
        action: 'restart_service',
        description: 'Restart affected services to clear memory leaks',
        priority: 'immediate',
        estimatedImpact: 0.9,
        feasibility: 0.95,
        estimatedTime: 120 // 2 minutes
      });

      recommendations.push({
        action: 'enable_heap_dump',
        description: 'Enable heap dumps for memory analysis',
        priority: 'medium',
        estimatedImpact: 0.3,
        feasibility: 0.8,
        estimatedTime: 300 // 5 minutes
      });
    }

    return recommendations;
  }

  generateInfrastructureRecommendations(rootCause, evidence) {
    const recommendations = [];

    if (rootCause.type === 'network_latency') {
      recommendations.push({
        action: 'check_network_connectivity',
        description: 'Verify network connectivity and routing',
        priority: 'immediate',
        estimatedImpact: 0.8,
        feasibility: 0.9,
        estimatedTime: 180 // 3 minutes
      });

      recommendations.push({
        action: 'optimize_network_routing',
        description: 'Optimize network routing and load balancing',
        priority: 'high',
        estimatedImpact: 0.7,
        feasibility: 0.7,
        estimatedTime: 900 // 15 minutes
      });
    }

    if (rootCause.type === 'database_connection') {
      recommendations.push({
        action: 'increase_connection_pool',
        description: 'Increase database connection pool size',
        priority: 'high',
        estimatedImpact: 0.8,
        feasibility: 0.8,
        estimatedTime: 300 // 5 minutes
      });

      recommendations.push({
        action: 'restart_database_proxy',
        description: 'Restart database proxy/connection manager',
        priority: 'medium',
        estimatedImpact: 0.6,
        feasibility: 0.7,
        estimatedTime: 600 // 10 minutes
      });
    }

    return recommendations;
  }

  generateCodeRecommendations(rootCause, evidence) {
    const recommendations = [];

    if (rootCause.type === 'deadlock') {
      recommendations.push({
        action: 'restart_affected_services',
        description: 'Restart services to clear deadlock conditions',
        priority: 'immediate',
        estimatedImpact: 0.9,
        feasibility: 0.95,
        estimatedTime: 180 // 3 minutes
      });

      recommendations.push({
        action: 'analyze_deadlock_pattern',
        description: 'Analyze deadlock patterns for code improvements',
        priority: 'medium',
        estimatedImpact: 0.5,
        feasibility: 0.6,
        estimatedTime: 3600 // 1 hour
      });
    }

    if (rootCause.type === 'timeout') {
      recommendations.push({
        action: 'increase_timeout_values',
        description: 'Temporarily increase timeout configurations',
        priority: 'high',
        estimatedImpact: 0.7,
        feasibility: 0.8,
        estimatedTime: 300 // 5 minutes
      });

      recommendations.push({
        action: 'implement_circuit_breaker',
        description: 'Implement circuit breaker pattern for failing calls',
        priority: 'medium',
        estimatedImpact: 0.8,
        feasibility: 0.5,
        estimatedTime: 1800 // 30 minutes
      });
    }

    return recommendations;
  }

  generateExternalRecommendations(rootCause, evidence) {
    const recommendations = [];

    if (rootCause.type === 'external_api_failure') {
      recommendations.push({
        action: 'enable_fallback_mechanism',
        description: 'Enable fallback mechanisms for external API calls',
        priority: 'immediate',
        estimatedImpact: 0.8,
        feasibility: 0.7,
        estimatedTime: 600 // 10 minutes
      });

      recommendations.push({
        action: 'contact_external_provider',
        description: 'Contact external service provider for status update',
        priority: 'high',
        estimatedImpact: 0.3,
        feasibility: 0.9,
        estimatedTime: 300 // 5 minutes
      });
    }

    if (rootCause.type === 'market_data_lag') {
      recommendations.push({
        action: 'switch_data_provider',
        description: 'Switch to backup market data provider',
        priority: 'immediate',
        estimatedImpact: 0.9,
        feasibility: 0.8,
        estimatedTime: 300 // 5 minutes
      });
    }

    return recommendations;
  }

  generateConfigurationRecommendations(rootCause, evidence) {
    const recommendations = [];

    if (rootCause.type === 'config_error') {
      recommendations.push({
        action: 'rollback_configuration',
        description: 'Rollback to previous known good configuration',
        priority: 'immediate',
        estimatedImpact: 0.9,
        feasibility: 0.8,
        estimatedTime: 420 // 7 minutes
      });

      recommendations.push({
        action: 'validate_configuration',
        description: 'Validate current configuration against schema',
        priority: 'high',
        estimatedImpact: 0.5,
        feasibility: 0.9,
        estimatedTime: 180 // 3 minutes
      });
    }

    return recommendations;
  }

  generateSecurityRecommendations(rootCause, evidence) {
    const recommendations = [];

    if (rootCause.type === 'rate_limiting') {
      recommendations.push({
        action: 'adjust_rate_limits',
        description: 'Temporarily adjust rate limiting thresholds',
        priority: 'high',
        estimatedImpact: 0.8,
        feasibility: 0.9,
        estimatedTime: 180 // 3 minutes
      });

      recommendations.push({
        action: 'analyze_traffic_patterns',
        description: 'Analyze traffic patterns for legitimate vs malicious requests',
        priority: 'medium',
        estimatedImpact: 0.6,
        feasibility: 0.7,
        estimatedTime: 900 // 15 minutes
      });
    }

    return recommendations;
  }

  generateGenericRecommendations(rootCause, evidence) {
    return [
      {
        action: 'investigate_logs',
        description: 'Manually investigate system logs for additional clues',
        priority: 'medium',
        estimatedImpact: 0.5,
        feasibility: 0.9,
        estimatedTime: 1200 // 20 minutes
      },
      {
        action: 'monitor_system_metrics',
        description: 'Continue monitoring system metrics for trends',
        priority: 'low',
        estimatedImpact: 0.3,
        feasibility: 0.95,
        estimatedTime: 60 // 1 minute
      }
    ];
  }

  calculateConfidenceScore(rootCause, evidence, patterns, correlations) {
    let confidence = rootCause.confidence || 0.5;

    // Adjust based on evidence quantity and quality
    const evidenceScore = this.calculateEvidenceScore(evidence);
    confidence = confidence * 0.7 + evidenceScore * 0.3;

    // Adjust based on pattern recognition strength
    if (patterns.length > 0) {
      const patternConfidence = patterns.reduce((sum, p) => sum + (p.confidence || 0.5), 0) / patterns.length;
      confidence = confidence * 0.8 + patternConfidence * 0.2;
    }

    // Adjust based on correlation strength
    if (correlations.length > 0) {
      const correlationConfidence = correlations.reduce((sum, c) => sum + (c.confidence || 0.5), 0) / correlations.length;
      confidence = confidence * 0.9 + correlationConfidence * 0.1;
    }

    return Math.min(Math.max(confidence, 0), 1);
  }

  calculateEvidenceScore(evidence) {
    let score = 0;

    // Weight different types of evidence
    if (evidence.logs && evidence.logs.length > 0) score += 0.3;
    if (evidence.metrics && evidence.metrics.length > 0) score += 0.3;
    if (evidence.events && evidence.events.length > 0) score += 0.2;
    if (evidence.traces && evidence.traces.length > 0) score += 0.2;

    return Math.min(score, 1);
  }

  async getChainTrace(chainId) {
    try {
      const query = `
        SELECT
          chain_id,
          MIN(created_at) as start_time,
          MAX(created_at) as end_time,
          ARRAY_AGG(DISTINCT service_name) as involved_services,
          COUNT(*) as total_events
        FROM chain_events
        WHERE chain_id = $1
        GROUP BY chain_id
      `;

      const result = await this.database.query(query, [chainId]);

      if (result.rows.length === 0) {
        return null;
      }

      const row = result.rows[0];

      return {
        chainId: row.chain_id,
        startTime: row.start_time,
        endTime: row.end_time,
        involvedServices: row.involved_services,
        totalEvents: row.total_events,
        duration: row.end_time - row.start_time
      };

    } catch (error) {
      logger.error(`Failed to get chain trace for ${chainId}:`, error);
      return null;
    }
  }

  async getHistoricalChainData(chainId, days) {
    try {
      const query = `
        SELECT * FROM chain_events
        WHERE chain_id = $1 AND created_at > $2
        ORDER BY created_at DESC
        LIMIT 10000
      `;

      const result = await this.database.query(query, [
        chainId,
        new Date(Date.now() - days * 24 * 60 * 60 * 1000)
      ]);

      return result.rows;

    } catch (error) {
      logger.error(`Failed to get historical data for chain ${chainId}:`, error);
      return [];
    }
  }

  async storeRootCauseAnalysis(analysis) {
    try {
      const query = `
        INSERT INTO root_cause_analyses
        (chain_id, root_cause_type, root_cause_description, confidence_score,
         contributing_factors, evidence, recommended_actions, analysis_timestamp, raw_data)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
      `;

      await this.database.query(query, [
        analysis.chainId,
        analysis.primaryRootCause.type,
        analysis.primaryRootCause.description,
        analysis.confidenceScore,
        JSON.stringify(analysis.contributingFactors),
        JSON.stringify(analysis.evidence),
        JSON.stringify(analysis.recommendedActions),
        analysis.analysisTimestamp,
        JSON.stringify(analysis)
      ]);

    } catch (error) {
      logger.error('Failed to store root cause analysis:', error);
    }
  }

  async loadKnownPatterns() {
    try {
      logger.info('Loading known root cause patterns...');

      // Load patterns from database or initialize with defaults
      await this.patternRecognizer.loadPatterns();

      logger.info('Known patterns loaded successfully');

    } catch (error) {
      logger.error('Failed to load known patterns:', error);
    }
  }

  async getCurrentSystemMetrics() {
    try {
      const query = `
        SELECT metric_name, value, service_name, timestamp
        FROM system_metrics
        WHERE timestamp > $1
        ORDER BY timestamp DESC
        LIMIT 100
      `;

      const result = await this.database.query(query, [
        new Date(Date.now() - 300000) // Last 5 minutes
      ]);

      return result.rows;

    } catch (error) {
      logger.error('Failed to get current system metrics:', error);
      return [];
    }
  }

  async getServiceHealthStatus(services) {
    try {
      if (!services || services.length === 0) {
        return {};
      }

      const healthStatus = {};

      for (const service of services) {
        try {
          // Get recent health check results
          const query = `
            SELECT status, last_check, response_time
            FROM service_health_checks
            WHERE service_name = $1
            ORDER BY last_check DESC
            LIMIT 1
          `;

          const result = await this.database.query(query, [service]);

          healthStatus[service] = result.rows[0] || {
            status: 'unknown',
            last_check: null,
            response_time: null
          };

        } catch (error) {
          logger.error(`Failed to get health status for ${service}:`, error);
          healthStatus[service] = { status: 'error', error: error.message };
        }
      }

      return healthStatus;

    } catch (error) {
      logger.error('Failed to get service health status:', error);
      return {};
    }
  }

  async getResourceUtilization() {
    try {
      const query = `
        SELECT
          metric_name,
          AVG(value) as avg_value,
          MAX(value) as max_value,
          service_name
        FROM system_metrics
        WHERE timestamp > $1
          AND metric_name IN ('cpu_usage', 'memory_usage', 'disk_usage', 'network_usage')
        GROUP BY metric_name, service_name
      `;

      const result = await this.database.query(query, [
        new Date(Date.now() - 600000) // Last 10 minutes
      ]);

      return result.rows.reduce((acc, row) => {
        if (!acc[row.service_name]) {
          acc[row.service_name] = {};
        }
        acc[row.service_name][row.metric_name] = {
          average: row.avg_value,
          maximum: row.max_value
        };
        return acc;
      }, {});

    } catch (error) {
      logger.error('Failed to get resource utilization:', error);
      return {};
    }
  }

  async getConnectionState() {
    try {
      const query = `
        SELECT
          service_name,
          connection_type,
          active_connections,
          max_connections,
          timestamp
        FROM connection_metrics
        WHERE timestamp > $1
        ORDER BY timestamp DESC
      `;

      const result = await this.database.query(query, [
        new Date(Date.now() - 300000) // Last 5 minutes
      ]);

      return result.rows.reduce((acc, row) => {
        if (!acc[row.service_name]) {
          acc[row.service_name] = {};
        }
        acc[row.service_name][row.connection_type] = {
          active: row.active_connections,
          max: row.max_connections,
          utilization: row.active_connections / row.max_connections
        };
        return acc;
      }, {});

    } catch (error) {
      logger.error('Failed to get connection state:', error);
      return {};
    }
  }
}