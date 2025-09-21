/**
 * @fileoverview Shared utilities, types, and middleware for AI Trading Platform
 * @version 1.0.0
 * @author AI Trading Platform Team
 */

// =============================================================================
// TYPE EXPORTS
// =============================================================================

export * from './types';
export * from './types/api';
export * from './types/config';
export * from './types/database';
export * from './types/events';
export * from './types/logging';
export * from './types/monitoring';
export * from './types/trading';

// =============================================================================
// UTILITY EXPORTS
// =============================================================================

export { Logger, createLogger, createServiceLogger, createRequestLogger } from './utils/logger';
export {
  ServiceRegistry,
  ServiceInstance,
  ServiceDiscovery,
  createServiceRegistry,
  createServiceRegistryFromConfig
} from './utils/service-registry';
export {
  HealthChecker,
  createHealthChecker,
  createBasicHealthChecker,
  createHealthMiddleware,
  createReadinessMiddleware
} from './utils/health-checker';

// =============================================================================
// MIDDLEWARE EXPORTS
// =============================================================================

export * from './middleware';

// =============================================================================
// CONFIG EXPORTS
// =============================================================================

export * from './config';

// =============================================================================
// VERSION INFORMATION
// =============================================================================

export const VERSION = '1.0.0';
export const NAME = '@aitrading/shared';

// =============================================================================
// PACKAGE METADATA
// =============================================================================

export const metadata = {
  name: NAME,
  version: VERSION,
  description: 'Shared utilities, types, and middleware for AI Trading Platform',
  buildTime: new Date().toISOString(),
  nodeVersion: process.version,
  platform: process.platform,
  arch: process.arch
};

// =============================================================================
// DEFAULT EXPORT
// =============================================================================

export default {
  VERSION,
  NAME,
  metadata
};