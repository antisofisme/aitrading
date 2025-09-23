/**
 * Service Configuration for API Gateway
 * Maps all microservices with their ports and health endpoints
 */

const services = {
  // Core Services
  'configuration-service': {
    name: 'Configuration Service',
    baseUrl: 'http://localhost:8012',
    port: 8012,
    prefix: '/api/config',
    healthEndpoint: '/health',
    timeout: 5000,
    retries: 3,
    critical: true
  },

  'database-service': {
    name: 'Database Service',
    baseUrl: 'http://localhost:8008',
    port: 8008,
    prefix: '/api/database',
    healthEndpoint: '/health',
    timeout: 10000,
    retries: 3,
    critical: true
  },

  // AI Services
  'ai-orchestrator': {
    name: 'AI Orchestrator',
    baseUrl: 'http://localhost:8020',
    port: 8020,
    prefix: '/api/ai',
    healthEndpoint: '/health',
    timeout: 30000,
    retries: 2,
    critical: true
  },

  'ml-predictor': {
    name: 'ML Predictor',
    baseUrl: 'http://localhost:8021',
    port: 8021,
    prefix: '/api/ml',
    healthEndpoint: '/health',
    timeout: 15000,
    retries: 2,
    critical: true
  },

  'risk-analyzer': {
    name: 'Risk Analyzer',
    baseUrl: 'http://localhost:8022',
    port: 8022,
    prefix: '/api/risk',
    healthEndpoint: '/health',
    timeout: 10000,
    retries: 3,
    critical: true
  },

  // Trading Services
  'trading-engine': {
    name: 'Trading Engine',
    baseUrl: 'http://localhost:9000',
    port: 9000,
    prefix: '/api/trading',
    healthEndpoint: '/health',
    timeout: 5000,
    retries: 3,
    critical: true
  },

  'portfolio-manager': {
    name: 'Portfolio Manager',
    baseUrl: 'http://localhost:9001',
    port: 9001,
    prefix: '/api/portfolio',
    healthEndpoint: '/health',
    timeout: 10000,
    retries: 3,
    critical: true
  },

  'order-management': {
    name: 'Order Management',
    baseUrl: 'http://localhost:9002',
    port: 9002,
    prefix: '/api/orders',
    healthEndpoint: '/health',
    timeout: 5000,
    retries: 3,
    critical: true
  },

  // Infrastructure Services
  'data-bridge': {
    name: 'Data Bridge',
    baseUrl: 'http://localhost:5001',
    port: 5001,
    prefix: '/api/data',
    healthEndpoint: '/health',
    timeout: 15000,
    retries: 2,
    critical: true
  },

  'central-hub': {
    name: 'Central Hub',
    baseUrl: 'http://localhost:7000',
    port: 7000,
    prefix: '/api/hub',
    healthEndpoint: '/health',
    timeout: 10000,
    retries: 3,
    critical: true
  },

  // Business Services
  'notification-service': {
    name: 'Notification Service',
    baseUrl: 'http://localhost:9003',
    port: 9003,
    prefix: '/api/notifications',
    healthEndpoint: '/health',
    timeout: 5000,
    retries: 2,
    critical: false
  },

  'user-management': {
    name: 'User Management',
    baseUrl: 'http://localhost:8010',
    port: 8010,
    prefix: '/api/users',
    healthEndpoint: '/health',
    timeout: 10000,
    retries: 3,
    critical: true
  },

  'billing-service': {
    name: 'Billing Service',
    baseUrl: 'http://localhost:8011',
    port: 8011,
    prefix: '/api/billing',
    healthEndpoint: '/health',
    timeout: 10000,
    retries: 2,
    critical: false
  },

  'payment-service': {
    name: 'Payment Service',
    baseUrl: 'http://localhost:8013',
    port: 8013,
    prefix: '/api/payments',
    healthEndpoint: '/health',
    timeout: 15000,
    retries: 3,
    critical: true
  },

  // Compliance & Analytics
  'compliance-monitor': {
    name: 'Compliance Monitor',
    baseUrl: 'http://localhost:8014',
    port: 8014,
    prefix: '/api/compliance',
    healthEndpoint: '/health',
    timeout: 10000,
    retries: 2,
    critical: true
  },

  'backtesting-engine': {
    name: 'Backtesting Engine',
    baseUrl: 'http://localhost:8015',
    port: 8015,
    prefix: '/api/backtesting',
    healthEndpoint: '/health',
    timeout: 30000,
    retries: 1,
    critical: false
  },

  'performance-analytics': {
    name: 'Performance Analytics',
    baseUrl: 'http://localhost:9100',
    port: 9100,
    prefix: '/api/analytics/performance',
    healthEndpoint: '/health',
    timeout: 10000,
    retries: 2,
    critical: false
  },

  'usage-monitoring': {
    name: 'Usage Monitoring',
    baseUrl: 'http://localhost:9101',
    port: 9101,
    prefix: '/api/analytics/usage',
    healthEndpoint: '/health',
    timeout: 10000,
    retries: 2,
    critical: false
  },

  'revenue-analytics': {
    name: 'Revenue Analytics',
    baseUrl: 'http://localhost:9102',
    port: 9102,
    prefix: '/api/analytics/revenue',
    healthEndpoint: '/health',
    timeout: 10000,
    retries: 2,
    critical: false
  },

  // Debug & Chain Services
  'chain-debug-system': {
    name: 'Chain Debug System',
    baseUrl: 'http://localhost:8030',
    port: 8030,
    prefix: '/api/debug',
    healthEndpoint: '/health',
    timeout: 15000,
    retries: 2,
    critical: false
  },

  'ai-chain-analytics': {
    name: 'AI Chain Analytics',
    baseUrl: 'http://localhost:8031',
    port: 8031,
    prefix: '/api/analytics/chains',
    healthEndpoint: '/health',
    timeout: 15000,
    retries: 2,
    critical: false
  }
};

/**
 * Get service configuration by name
 */
const getService = (serviceName) => {
  return services[serviceName] || null;
};

/**
 * Get all services
 */
const getAllServices = () => {
  return services;
};

/**
 * Get critical services (required for platform operation)
 */
const getCriticalServices = () => {
  return Object.fromEntries(
    Object.entries(services).filter(([, service]) => service.critical)
  );
};

/**
 * Get service by prefix
 */
const getServiceByPrefix = (prefix) => {
  return Object.values(services).find(service =>
    service.prefix === prefix || prefix.startsWith(service.prefix)
  );
};

/**
 * Service categories for monitoring and management
 */
const serviceCategories = {
  core: ['configuration-service', 'database-service'],
  ai: ['ai-orchestrator', 'ml-predictor', 'risk-analyzer'],
  trading: ['trading-engine', 'portfolio-manager', 'order-management'],
  infrastructure: ['data-bridge', 'central-hub'],
  business: ['notification-service', 'user-management', 'billing-service', 'payment-service'],
  compliance: ['compliance-monitor', 'backtesting-engine'],
  analytics: ['performance-analytics', 'usage-monitoring', 'revenue-analytics'],
  debug: ['chain-debug-system', 'ai-chain-analytics']
};

/**
 * Get services by category
 */
const getServicesByCategory = (category) => {
  const serviceNames = serviceCategories[category] || [];
  return Object.fromEntries(
    serviceNames.map(name => [name, services[name]])
  );
};

module.exports = {
  services,
  getService,
  getAllServices,
  getCriticalServices,
  getServiceByPrefix,
  serviceCategories,
  getServicesByCategory
};