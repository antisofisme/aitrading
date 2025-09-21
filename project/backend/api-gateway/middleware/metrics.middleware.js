const promClient = require('prom-client');
const logger = require('../utils/logger');

// Create a Registry to register metrics
const register = new promClient.Registry();

// Add default metrics
promClient.collectDefaultMetrics({
  register,
  prefix: 'gateway_'
});

// Custom metrics
const httpRequestDuration = new promClient.Histogram({
  name: 'gateway_http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'status_code', 'service'],
  buckets: [0.1, 0.5, 1, 2, 5, 10]
});

const httpRequestTotal = new promClient.Counter({
  name: 'gateway_http_requests_total',
  help: 'Total number of HTTP requests',
  labelNames: ['method', 'route', 'status_code', 'service']
});

const httpRequestSize = new promClient.Histogram({
  name: 'gateway_http_request_size_bytes',
  help: 'Size of HTTP requests in bytes',
  labelNames: ['method', 'route'],
  buckets: [100, 1000, 10000, 100000, 1000000]
});

const httpResponseSize = new promClient.Histogram({
  name: 'gateway_http_response_size_bytes',
  help: 'Size of HTTP responses in bytes',
  labelNames: ['method', 'route', 'status_code'],
  buckets: [100, 1000, 10000, 100000, 1000000]
});

const activeConnections = new promClient.Gauge({
  name: 'gateway_active_connections',
  help: 'Number of active connections'
});

const proxyRequestDuration = new promClient.Histogram({
  name: 'gateway_proxy_request_duration_seconds',
  help: 'Duration of proxy requests to backend services',
  labelNames: ['service', 'status_code'],
  buckets: [0.1, 0.5, 1, 2, 5, 10, 30]
});

const proxyRequestTotal = new promClient.Counter({
  name: 'gateway_proxy_requests_total',
  help: 'Total number of proxy requests to backend services',
  labelNames: ['service', 'status_code']
});

const authAttempts = new promClient.Counter({
  name: 'gateway_auth_attempts_total',
  help: 'Total number of authentication attempts',
  labelNames: ['result', 'method'] // result: success|failure, method: jwt|api_key
});

const rateLimitHits = new promClient.Counter({
  name: 'gateway_rate_limit_hits_total',
  help: 'Total number of rate limit hits',
  labelNames: ['endpoint']
});

const errorTotal = new promClient.Counter({
  name: 'gateway_errors_total',
  help: 'Total number of errors',
  labelNames: ['type', 'code']
});

// Register metrics
register.registerMetric(httpRequestDuration);
register.registerMetric(httpRequestTotal);
register.registerMetric(httpRequestSize);
register.registerMetric(httpResponseSize);
register.registerMetric(activeConnections);
register.registerMetric(proxyRequestDuration);
register.registerMetric(proxyRequestTotal);
register.registerMetric(authAttempts);
register.registerMetric(rateLimitHits);
register.registerMetric(errorTotal);

// Track active connections
let currentConnections = 0;

// Metrics middleware
const metricsMiddleware = (req, res, next) => {
  const startTime = Date.now();

  // Increment active connections
  currentConnections++;
  activeConnections.set(currentConnections);

  // Track request size
  const requestSize = JSON.stringify(req.body).length || 0;
  httpRequestSize.observe(
    { method: req.method, route: getRoute(req.route) },
    requestSize
  );

  // Override res.end to capture metrics on response
  const originalEnd = res.end;
  res.end = function(chunk, encoding) {
    // Calculate response time
    const responseTime = (Date.now() - startTime) / 1000;

    // Get service name from URL
    const service = getServiceFromUrl(req.originalUrl);
    const route = getRoute(req.route) || req.originalUrl;
    const statusCode = res.statusCode.toString();

    // Record metrics
    httpRequestDuration.observe(
      { method: req.method, route, status_code: statusCode, service },
      responseTime
    );

    httpRequestTotal.inc({
      method: req.method,
      route,
      status_code: statusCode,
      service
    });

    // Track response size
    const responseSize = chunk ? chunk.length : 0;
    httpResponseSize.observe(
      { method: req.method, route, status_code: statusCode },
      responseSize
    );

    // Track errors
    if (res.statusCode >= 400) {
      const errorType = res.statusCode >= 500 ? 'server_error' : 'client_error';
      errorTotal.inc({ type: errorType, code: statusCode });
    }

    // Decrement active connections
    currentConnections--;
    activeConnections.set(currentConnections);

    // Log request
    logger.info(`${req.method} ${req.originalUrl} ${res.statusCode} - ${responseTime * 1000}ms`, {
      method: req.method,
      url: req.originalUrl,
      statusCode: res.statusCode,
      responseTime: responseTime * 1000,
      service,
      userAgent: req.get('User-Agent'),
      ip: req.ip,
      userId: req.auth?.user?.id
    });

    originalEnd.call(this, chunk, encoding);
  };

  next();
};

// Helper function to extract service name from URL
function getServiceFromUrl(url) {
  const matches = url.match(/^\/api\/v\d+\/([^\/]+)/);
  return matches ? matches[1] : 'unknown';
}

// Helper function to get route pattern
function getRoute(route) {
  return route ? route.path : null;
}

// Metrics endpoint handler
const metricsHandler = async (req, res) => {
  try {
    res.set('Content-Type', register.contentType);
    const metrics = await register.metrics();
    res.end(metrics);
  } catch (error) {
    logger.error('Error generating metrics:', error);
    res.status(500).end('Error generating metrics');
  }
};

// Custom metric functions for use in other modules
const metrics = {
  // Record authentication attempts
  recordAuthAttempt: (result, method = 'jwt') => {
    authAttempts.inc({ result, method });
  },

  // Record rate limit hits
  recordRateLimitHit: (endpoint) => {
    rateLimitHits.inc({ endpoint });
  },

  // Record proxy request metrics
  recordProxyRequest: (service, statusCode, duration) => {
    proxyRequestTotal.inc({ service, status_code: statusCode.toString() });
    proxyRequestDuration.observe(
      { service, status_code: statusCode.toString() },
      duration / 1000
    );
  },

  // Get current metrics
  getMetrics: () => register.metrics(),

  // Get registry for external use
  getRegister: () => register
};

module.exports = {
  metricsMiddleware,
  metricsHandler,
  metrics
};