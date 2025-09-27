/**
 * Suho Shared Components - Main Entry Point
 *
 * Exports all shared components for use across backend services
 */

// Transfer Layer
const TransferManager = require('./transfer/TransferManager');
const NATSKafkaAdapter = require('./transfer/adapters/NATSKafkaAdapter');
const GRPCAdapter = require('./transfer/adapters/GRPCAdapter');
const HTTPAdapter = require('./transfer/adapters/HTTPAdapter');

// Core Utilities
const ErrorDNA = require('./utils/ErrorDNA');
const { BaseService, ServiceConfig, StandardResponse, CircuitBreaker, RequestTracer } = require('./utils/BaseService');

// Configuration Management
const ConfigManager = require('./config/ConfigManager');

// Monitoring & Metrics
const MetricsCollector = require('./monitoring/MetricsCollector');

// Security
const SecurityValidator = require('./security/SecurityValidator');

// Logging
const logger = require('./logging/logger');
const { createLogger, getLogger, SharedLogger } = require('./logging/logger');

// Re-export for easier imports
module.exports = {
  // Transfer Layer
  TransferManager,
  adapters: {
    NATSKafkaAdapter,
    GRPCAdapter,
    HTTPAdapter
  },

  // Core Utilities
  ErrorDNA,
  BaseService,
  ServiceConfig,
  StandardResponse,
  CircuitBreaker,
  RequestTracer,

  // Configuration Management
  ConfigManager,

  // Monitoring & Metrics
  MetricsCollector,

  // Security
  SecurityValidator,

  // Logging
  logger,
  createLogger,
  getLogger,
  SharedLogger,

  // Utility function to create transfer manager
  createTransfer: (config) => new TransferManager(config),

  // Utility function to get logger for service
  createServiceLogger: (serviceName) => createLogger(serviceName),

  // Utility function to create base service
  createBaseService: (serviceName, config) => new BaseService(serviceName, config),

  // Utility function to create config manager
  createConfigManager: (serviceName, options) => new ConfigManager(serviceName, options),

  // Utility function to create metrics collector
  createMetricsCollector: (serviceName, options) => new MetricsCollector(serviceName, options),

  // Utility function to create security validator
  createSecurityValidator: (options) => new SecurityValidator(options),

  // Utility function to create error DNA
  createErrorDNA: (serviceName) => new ErrorDNA(serviceName),

  // Protocol Buffer paths (for import)
  proto: {
    common: './proto/common/base.proto',
    trading: './proto/trading/client_mt5.proto'
  },

  // Generated protobuf files
  generated: {
    nodejs: './generated/nodejs/',
    typescript: './generated/typescript/'
  }
};

// For CommonJS compatibility
module.exports.default = module.exports;