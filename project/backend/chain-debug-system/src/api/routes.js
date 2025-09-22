/**
 * API Routes
 * RESTful API endpoints for the Chain Debug System
 */

import express from 'express';
import rateLimit from 'express-rate-limit';
import logger from '../utils/logger.js';

export function setupAPIRoutes(app, components) {
  const router = express.Router();

  // API rate limiting
  const apiLimiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 1000, // limit each IP to 1000 requests per windowMs
    message: 'Too many API requests from this IP'
  });

  router.use(apiLimiter);

  // Request logging middleware
  router.use((req, res, next) => {
    logger.debug(`API ${req.method} ${req.path}`, {
      ip: req.ip,
      userAgent: req.get('User-Agent'),
      timestamp: new Date().toISOString()
    });
    next();
  });

  // Health and Status Endpoints
  router.get('/health', (req, res) => {
    try {
      res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: process.env.npm_package_version || '1.0.0',
        components: {
          healthMonitor: components.healthMonitor?.isHealthy || false,
          impactAnalyzer: components.impactAnalyzer?.isHealthy || false,
          rootCauseAnalyzer: components.rootCauseAnalyzer?.isHealthy || false,
          recoveryOrchestrator: components.recoveryOrchestrator?.isHealthy || false
        }
      });
    } catch (error) {
      logger.error('Health check failed:', error);
      res.status(500).json({ error: 'Health check failed' });
    }
  });

  router.get('/status', async (req, res) => {
    try {
      const systemHealth = await components.healthMonitor.getOverallSystemHealth();

      res.json({
        systemHealth,
        activeChains: systemHealth?.active_chains || 0,
        avgHealthScore: systemHealth?.avg_health_score || 0,
        unhealthyChains: systemHealth?.unhealthy_chains || 0,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      logger.error('Status check failed:', error);
      res.status(500).json({ error: 'Status check failed' });
    }
  });

  // Chain Health Endpoints
  router.get('/chains', async (req, res) => {
    try {
      const timeWindow = parseInt(req.query.timeWindow) || 3600000; // 1 hour default
      const chains = await components.healthMonitor.getActiveChains(timeWindow);

      res.json({
        chains,
        count: chains.length,
        timeWindow,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      logger.error('Failed to get chains:', error);
      res.status(500).json({ error: 'Failed to retrieve chains' });
    }
  });

  router.get('/chains/:chainId/health', async (req, res) => {
    try {
      const { chainId } = req.params;
      const health = await components.healthMonitor.getChainHealth(chainId);

      if (!health) {
        return res.status(404).json({ error: 'Chain health data not found' });
      }

      res.json(health);
    } catch (error) {
      logger.error('Failed to get chain health:', error);
      res.status(500).json({ error: 'Failed to retrieve chain health' });
    }
  });

  router.get('/chains/:chainId/metrics', async (req, res) => {
    try {
      const { chainId } = req.params;
      const timeWindow = parseInt(req.query.timeWindow) || 3600000; // 1 hour

      const health = await components.healthMonitor.getChainHealth(chainId);
      const anomalies = await components.healthMonitor.getChainAnomalies(chainId, timeWindow);

      res.json({
        chainId,
        health,
        anomalies,
        anomalyCount: anomalies.length,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      logger.error('Failed to get chain metrics:', error);
      res.status(500).json({ error: 'Failed to retrieve chain metrics' });
    }
  });

  // Anomaly Detection Endpoints
  router.get('/anomalies', async (req, res) => {
    try {
      const timeWindow = parseInt(req.query.timeWindow) || 3600000; // 1 hour
      const severity = req.query.severity;
      const limit = parseInt(req.query.limit) || 100;

      // This would need to be implemented in the health monitor
      const anomalies = await getRecentAnomalies(components, timeWindow, severity, limit);

      res.json({
        anomalies,
        count: anomalies.length,
        timeWindow,
        filters: { severity },
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      logger.error('Failed to get anomalies:', error);
      res.status(500).json({ error: 'Failed to retrieve anomalies' });
    }
  });

  router.get('/chains/:chainId/anomalies', async (req, res) => {
    try {
      const { chainId } = req.params;
      const timeWindow = parseInt(req.query.timeWindow) || 3600000; // 1 hour

      const anomalies = await components.healthMonitor.getChainAnomalies(chainId, timeWindow);

      res.json({
        chainId,
        anomalies,
        count: anomalies.length,
        timeWindow,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      logger.error('Failed to get chain anomalies:', error);
      res.status(500).json({ error: 'Failed to retrieve chain anomalies' });
    }
  });

  // Impact Analysis Endpoints
  router.post('/chains/:chainId/impact-analysis', async (req, res) => {
    try {
      const { chainId } = req.params;
      const { anomalies } = req.body;

      if (!anomalies || !Array.isArray(anomalies)) {
        return res.status(400).json({ error: 'Anomalies array is required' });
      }

      const impactAssessment = await components.impactAnalyzer.assessImpact(chainId, anomalies);

      if (!impactAssessment) {
        return res.status(404).json({ error: 'Unable to assess impact for chain' });
      }

      res.json(impactAssessment.toJSON());
    } catch (error) {
      logger.error('Failed to assess impact:', error);
      res.status(500).json({ error: 'Failed to assess impact' });
    }
  });

  // Root Cause Analysis Endpoints
  router.post('/chains/:chainId/root-cause-analysis', async (req, res) => {
    try {
      const { chainId } = req.params;
      const { anomalies } = req.body;

      if (!anomalies || !Array.isArray(anomalies)) {
        return res.status(400).json({ error: 'Anomalies array is required' });
      }

      const rootCauseAnalysis = await components.rootCauseAnalyzer.analyzeRootCause(chainId, anomalies);

      if (!rootCauseAnalysis) {
        return res.status(404).json({ error: 'Unable to analyze root cause for chain' });
      }

      res.json(rootCauseAnalysis);
    } catch (error) {
      logger.error('Failed to analyze root cause:', error);
      res.status(500).json({ error: 'Failed to analyze root cause' });
    }
  });

  // Recovery Orchestration Endpoints
  router.post('/chains/:chainId/recovery', async (req, res) => {
    try {
      const { chainId } = req.params;
      const { impactAssessment, rootCauseAnalysis } = req.body;

      if (!impactAssessment) {
        return res.status(400).json({ error: 'Impact assessment is required' });
      }

      const recoveryResult = await components.recoveryOrchestrator.executeRecoveryPlan(
        impactAssessment,
        rootCauseAnalysis
      );

      res.json(recoveryResult);
    } catch (error) {
      logger.error('Failed to execute recovery:', error);
      res.status(500).json({ error: 'Failed to execute recovery plan' });
    }
  });

  router.get('/recovery/active', async (req, res) => {
    try {
      const activeRecoveries = Array.from(components.recoveryOrchestrator.activeRecoveries.keys());

      res.json({
        activeRecoveries,
        count: activeRecoveries.length,
        maxConcurrent: components.recoveryOrchestrator.config.maxConcurrentRecoveries,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      logger.error('Failed to get active recoveries:', error);
      res.status(500).json({ error: 'Failed to retrieve active recoveries' });
    }
  });

  // Debug and Investigation Endpoints
  router.post('/chains/:chainId/investigate', async (req, res) => {
    try {
      const { chainId } = req.params;
      const { anomalies = [] } = req.body;

      // Run complete investigation pipeline
      const [impactAssessment, rootCauseAnalysis] = await Promise.allSettled([
        components.impactAnalyzer.assessImpact(chainId, anomalies),
        components.rootCauseAnalyzer.analyzeRootCause(chainId, anomalies)
      ]);

      const investigation = {
        chainId,
        timestamp: new Date().toISOString(),
        impactAssessment: impactAssessment.status === 'fulfilled' ? impactAssessment.value : null,
        rootCauseAnalysis: rootCauseAnalysis.status === 'fulfilled' ? rootCauseAnalysis.value : null,
        errors: []
      };

      if (impactAssessment.status === 'rejected') {
        investigation.errors.push(`Impact analysis failed: ${impactAssessment.reason.message}`);
      }

      if (rootCauseAnalysis.status === 'rejected') {
        investigation.errors.push(`Root cause analysis failed: ${rootCauseAnalysis.reason.message}`);
      }

      res.json(investigation);
    } catch (error) {
      logger.error('Failed to investigate chain:', error);
      res.status(500).json({ error: 'Failed to investigate chain' });
    }
  });

  // Full Chain Debug Workflow
  router.post('/chains/:chainId/debug', async (req, res) => {
    try {
      const { chainId } = req.params;
      const { autoRecover = false } = req.body;

      // Get recent anomalies
      const anomalies = await components.healthMonitor.getChainAnomalies(chainId, 300000); // 5 minutes

      if (anomalies.length === 0) {
        return res.json({
          chainId,
          status: 'healthy',
          message: 'No recent anomalies detected',
          timestamp: new Date().toISOString()
        });
      }

      // Run full debug workflow
      const debugResult = {
        chainId,
        timestamp: new Date().toISOString(),
        anomalies,
        impactAssessment: null,
        rootCauseAnalysis: null,
        recoveryResult: null,
        errors: []
      };

      try {
        // Impact assessment
        debugResult.impactAssessment = await components.impactAnalyzer.assessImpact(chainId, anomalies);

        // Root cause analysis
        debugResult.rootCauseAnalysis = await components.rootCauseAnalyzer.analyzeRootCause(chainId, anomalies);

        // Auto-recovery if requested and high priority
        if (autoRecover && debugResult.impactAssessment?.isHighPriority()) {
          debugResult.recoveryResult = await components.recoveryOrchestrator.executeRecoveryPlan(
            debugResult.impactAssessment,
            debugResult.rootCauseAnalysis
          );
        }

      } catch (error) {
        debugResult.errors.push(error.message);
      }

      res.json(debugResult);
    } catch (error) {
      logger.error('Failed to debug chain:', error);
      res.status(500).json({ error: 'Failed to debug chain' });
    }
  });

  // Metrics and Analytics Endpoints
  router.get('/metrics/system', async (req, res) => {
    try {
      const timeWindow = parseInt(req.query.timeWindow) || 3600000; // 1 hour

      const metrics = await components.metricsCollector.getSystemMetrics(timeWindow);

      res.json({
        metrics,
        timeWindow,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      logger.error('Failed to get system metrics:', error);
      res.status(500).json({ error: 'Failed to retrieve system metrics' });
    }
  });

  router.get('/metrics/performance', async (req, res) => {
    try {
      const timeWindow = parseInt(req.query.timeWindow) || 3600000; // 1 hour

      const performanceMetrics = await components.metricsCollector.getPerformanceMetrics(timeWindow);

      res.json({
        performanceMetrics,
        timeWindow,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      logger.error('Failed to get performance metrics:', error);
      res.status(500).json({ error: 'Failed to retrieve performance metrics' });
    }
  });

  // Search and Query Endpoints
  router.get('/search/chains', async (req, res) => {
    try {
      const { pattern, status, timeWindow = 3600000 } = req.query;

      const searchResults = await searchChains(components, {
        pattern,
        status,
        timeWindow: parseInt(timeWindow)
      });

      res.json({
        results: searchResults,
        count: searchResults.length,
        query: { pattern, status, timeWindow },
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      logger.error('Failed to search chains:', error);
      res.status(500).json({ error: 'Failed to search chains' });
    }
  });

  // Error handling middleware
  router.use((error, req, res, next) => {
    logger.error('API error:', error);

    res.status(error.status || 500).json({
      error: 'Internal Server Error',
      message: process.env.NODE_ENV === 'development' ? error.message : 'Something went wrong',
      timestamp: new Date().toISOString()
    });
  });

  // Mount router
  app.use('/api/v1', router);

  logger.info('API routes configured');
}

// Helper functions
async function getRecentAnomalies(components, timeWindow, severity, limit) {
  try {
    // This would be implemented as a database query
    const query = `
      SELECT * FROM chain_anomalies
      WHERE timestamp > $1
      ${severity ? 'AND severity = $2' : ''}
      ORDER BY timestamp DESC
      LIMIT $${severity ? 3 : 2}
    `;

    const params = [new Date(Date.now() - timeWindow)];
    if (severity) params.push(severity);
    params.push(limit);

    const result = await components.healthMonitor.database.query(query, params);
    return result.rows;

  } catch (error) {
    logger.error('Failed to get recent anomalies:', error);
    return [];
  }
}

async function searchChains(components, { pattern, status, timeWindow }) {
  try {
    let query = `
      SELECT DISTINCT chain_id, MAX(timestamp) as last_seen
      FROM chain_health_metrics
      WHERE timestamp > $1
    `;

    const params = [new Date(Date.now() - timeWindow)];

    if (pattern) {
      query += ` AND chain_id ILIKE $${params.length + 1}`;
      params.push(`%${pattern}%`);
    }

    if (status) {
      // Map status to health score ranges
      const statusMap = {
        'healthy': 'health_score >= 90',
        'warning': 'health_score BETWEEN 70 AND 89',
        'degraded': 'health_score BETWEEN 50 AND 69',
        'critical': 'health_score < 50'
      };

      if (statusMap[status]) {
        query += ` AND ${statusMap[status]}`;
      }
    }

    query += ' GROUP BY chain_id ORDER BY last_seen DESC LIMIT 100';

    const result = await components.healthMonitor.database.query(query, params);
    return result.rows;

  } catch (error) {
    logger.error('Failed to search chains:', error);
    return [];
  }
}