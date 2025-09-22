/**
 * WebSocket Handler
 * Real-time updates for chain debugging
 */

import logger from '../utils/logger.js';

export function setupWebSocketHandlers(wss, components) {
  const clients = new Set();
  const subscriptions = new Map(); // clientId -> Set of subscriptions

  wss.on('connection', (ws, request) => {
    const clientId = generateClientId();
    clients.add(ws);
    subscriptions.set(clientId, new Set());

    ws.clientId = clientId;

    logger.info(`WebSocket client connected: ${clientId}`, {
      clientsCount: clients.size,
      userAgent: request.headers['user-agent'],
      ip: request.socket.remoteAddress
    });

    // Send welcome message
    ws.send(JSON.stringify({
      type: 'welcome',
      clientId,
      timestamp: new Date().toISOString(),
      availableSubscriptions: [
        'chain-health',
        'anomalies',
        'recovery-events',
        'system-metrics'
      ]
    }));

    // Handle incoming messages
    ws.on('message', async (data) => {
      try {
        const message = JSON.parse(data.toString());
        await handleWebSocketMessage(ws, message, components);
      } catch (error) {
        logger.error('WebSocket message handling failed:', error);
        ws.send(JSON.stringify({
          type: 'error',
          message: 'Invalid message format',
          timestamp: new Date().toISOString()
        }));
      }
    });

    // Handle client disconnect
    ws.on('close', () => {
      clients.delete(ws);
      subscriptions.delete(clientId);
      logger.info(`WebSocket client disconnected: ${clientId}`, {
        clientsCount: clients.size
      });
    });

    // Handle errors
    ws.on('error', (error) => {
      logger.error(`WebSocket error for client ${clientId}:`, error);
      clients.delete(ws);
      subscriptions.delete(clientId);
    });
  });

  // Set up event listeners for real-time updates
  setupComponentEventListeners(components, clients, subscriptions);

  logger.info('WebSocket handlers configured');
}

async function handleWebSocketMessage(ws, message, components) {
  const { type, data } = message;

  switch (type) {
    case 'subscribe':
      await handleSubscribe(ws, data);
      break;

    case 'unsubscribe':
      await handleUnsubscribe(ws, data);
      break;

    case 'get-chain-health':
      await handleGetChainHealth(ws, data, components);
      break;

    case 'get-system-status':
      await handleGetSystemStatus(ws, data, components);
      break;

    case 'trigger-investigation':
      await handleTriggerInvestigation(ws, data, components);
      break;

    default:
      ws.send(JSON.stringify({
        type: 'error',
        message: `Unknown message type: ${type}`,
        timestamp: new Date().toISOString()
      }));
  }
}

async function handleSubscribe(ws, data) {
  const { subscriptionType, filters = {} } = data;
  const clientSubscriptions = subscriptions.get(ws.clientId);

  if (!clientSubscriptions) {
    return;
  }

  const subscriptionKey = `${subscriptionType}:${JSON.stringify(filters)}`;
  clientSubscriptions.add(subscriptionKey);

  ws.send(JSON.stringify({
    type: 'subscription-confirmed',
    subscriptionType,
    filters,
    timestamp: new Date().toISOString()
  }));

  logger.debug(`Client ${ws.clientId} subscribed to ${subscriptionType}`, { filters });
}

async function handleUnsubscribe(ws, data) {
  const { subscriptionType, filters = {} } = data;
  const clientSubscriptions = subscriptions.get(ws.clientId);

  if (!clientSubscriptions) {
    return;
  }

  const subscriptionKey = `${subscriptionType}:${JSON.stringify(filters)}`;
  clientSubscriptions.delete(subscriptionKey);

  ws.send(JSON.stringify({
    type: 'subscription-cancelled',
    subscriptionType,
    filters,
    timestamp: new Date().toISOString()
  }));

  logger.debug(`Client ${ws.clientId} unsubscribed from ${subscriptionType}`, { filters });
}

async function handleGetChainHealth(ws, data, components) {
  try {
    const { chainId } = data;

    if (!chainId) {
      ws.send(JSON.stringify({
        type: 'error',
        message: 'chainId is required',
        timestamp: new Date().toISOString()
      }));
      return;
    }

    const health = await components.healthMonitor.getChainHealth(chainId);
    const anomalies = await components.healthMonitor.getChainAnomalies(chainId, 300000); // 5 minutes

    ws.send(JSON.stringify({
      type: 'chain-health-response',
      chainId,
      health,
      anomalies,
      timestamp: new Date().toISOString()
    }));

  } catch (error) {
    logger.error('Failed to get chain health:', error);
    ws.send(JSON.stringify({
      type: 'error',
      message: 'Failed to retrieve chain health',
      timestamp: new Date().toISOString()
    }));
  }
}

async function handleGetSystemStatus(ws, data, components) {
  try {
    const systemHealth = await components.healthMonitor.getOverallSystemHealth();

    ws.send(JSON.stringify({
      type: 'system-status-response',
      systemHealth,
      timestamp: new Date().toISOString()
    }));

  } catch (error) {
    logger.error('Failed to get system status:', error);
    ws.send(JSON.stringify({
      type: 'error',
      message: 'Failed to retrieve system status',
      timestamp: new Date().toISOString()
    }));
  }
}

async function handleTriggerInvestigation(ws, data, components) {
  try {
    const { chainId } = data;

    if (!chainId) {
      ws.send(JSON.stringify({
        type: 'error',
        message: 'chainId is required',
        timestamp: new Date().toISOString()
      }));
      return;
    }

    // Get recent anomalies
    const anomalies = await components.healthMonitor.getChainAnomalies(chainId, 300000); // 5 minutes

    if (anomalies.length === 0) {
      ws.send(JSON.stringify({
        type: 'investigation-response',
        chainId,
        status: 'no-anomalies',
        message: 'No recent anomalies found for investigation',
        timestamp: new Date().toISOString()
      }));
      return;
    }

    // Start investigation
    ws.send(JSON.stringify({
      type: 'investigation-started',
      chainId,
      anomalyCount: anomalies.length,
      timestamp: new Date().toISOString()
    }));

    // Run investigation in background
    Promise.allSettled([
      components.impactAnalyzer.assessImpact(chainId, anomalies),
      components.rootCauseAnalyzer.analyzeRootCause(chainId, anomalies)
    ]).then(([impactResult, rootCauseResult]) => {
      const investigation = {
        chainId,
        impactAssessment: impactResult.status === 'fulfilled' ? impactResult.value : null,
        rootCauseAnalysis: rootCauseResult.status === 'fulfilled' ? rootCauseResult.value : null,
        errors: []
      };

      if (impactResult.status === 'rejected') {
        investigation.errors.push(`Impact analysis failed: ${impactResult.reason.message}`);
      }

      if (rootCauseResult.status === 'rejected') {
        investigation.errors.push(`Root cause analysis failed: ${rootCauseResult.reason.message}`);
      }

      ws.send(JSON.stringify({
        type: 'investigation-completed',
        investigation,
        timestamp: new Date().toISOString()
      }));
    }).catch((error) => {
      logger.error('Investigation failed:', error);
      ws.send(JSON.stringify({
        type: 'investigation-failed',
        chainId,
        error: error.message,
        timestamp: new Date().toISOString()
      }));
    });

  } catch (error) {
    logger.error('Failed to trigger investigation:', error);
    ws.send(JSON.stringify({
      type: 'error',
      message: 'Failed to trigger investigation',
      timestamp: new Date().toISOString()
    }));
  }
}

function setupComponentEventListeners(components, clients, subscriptions) {
  // Chain health updates
  components.healthMonitor.on('chain:health:update', (data) => {
    broadcastToSubscribers(clients, subscriptions, 'chain-health', {
      type: 'chain-health-update',
      ...data
    });
  });

  // Anomaly detection
  components.healthMonitor.on('anomaly:detected', (data) => {
    broadcastToSubscribers(clients, subscriptions, 'anomalies', {
      type: 'anomaly-detected',
      ...data
    });
  });

  // Impact assessments
  components.impactAnalyzer.on('impact:assessed', (data) => {
    broadcastToSubscribers(clients, subscriptions, 'impact-assessments', {
      type: 'impact-assessed',
      ...data
    });
  });

  // Root cause analysis
  components.rootCauseAnalyzer.on('rootcause:analyzed', (data) => {
    broadcastToSubscribers(clients, subscriptions, 'root-cause-analysis', {
      type: 'root-cause-analyzed',
      ...data
    });
  });

  // Recovery events
  components.recoveryOrchestrator.on('recovery:started', (data) => {
    broadcastToSubscribers(clients, subscriptions, 'recovery-events', {
      type: 'recovery-started',
      ...data
    });
  });

  components.recoveryOrchestrator.on('recovery:completed', (data) => {
    broadcastToSubscribers(clients, subscriptions, 'recovery-events', {
      type: 'recovery-completed',
      ...data
    });
  });

  components.recoveryOrchestrator.on('recovery:failed', (data) => {
    broadcastToSubscribers(clients, subscriptions, 'recovery-events', {
      type: 'recovery-failed',
      ...data
    });
  });

  // Recovery action updates
  components.recoveryOrchestrator.on('recovery:action:completed', (data) => {
    broadcastToSubscribers(clients, subscriptions, 'recovery-events', {
      type: 'recovery-action-completed',
      ...data
    });
  });

  logger.info('Component event listeners configured for WebSocket broadcasting');
}

function broadcastToSubscribers(clients, subscriptions, subscriptionType, message) {
  let broadcastCount = 0;

  for (const client of clients) {
    if (client.readyState === client.OPEN) {
      const clientSubscriptions = subscriptions.get(client.clientId);

      if (clientSubscriptions) {
        // Check if client is subscribed to this type
        const isSubscribed = Array.from(clientSubscriptions).some(sub =>
          sub.startsWith(`${subscriptionType}:`)
        );

        if (isSubscribed) {
          try {
            client.send(JSON.stringify(message));
            broadcastCount++;
          } catch (error) {
            logger.error(`Failed to send message to client ${client.clientId}:`, error);
          }
        }
      }
    }
  }

  if (broadcastCount > 0) {
    logger.debug(`Broadcasted ${subscriptionType} event to ${broadcastCount} clients`);
  }
}

function generateClientId() {
  return `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// Utility to broadcast system-wide alerts
export function broadcastAlert(clients, subscriptions, alert) {
  const message = {
    type: 'system-alert',
    alert,
    timestamp: new Date().toISOString()
  };

  for (const client of clients) {
    if (client.readyState === client.OPEN) {
      try {
        client.send(JSON.stringify(message));
      } catch (error) {
        logger.error(`Failed to send alert to client ${client.clientId}:`, error);
      }
    }
  }
}

// Utility to get WebSocket statistics
export function getWebSocketStats(clients, subscriptions) {
  const stats = {
    connectedClients: clients.size,
    totalSubscriptions: 0,
    subscriptionsByType: {}
  };

  for (const clientSubscriptions of subscriptions.values()) {
    stats.totalSubscriptions += clientSubscriptions.size;

    for (const subscription of clientSubscriptions) {
      const [type] = subscription.split(':');
      stats.subscriptionsByType[type] = (stats.subscriptionsByType[type] || 0) + 1;
    }
  }

  return stats;
}