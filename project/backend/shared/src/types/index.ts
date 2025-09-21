/**
 * @fileoverview Shared TypeScript type definitions for AI Trading Platform
 * @version 1.0.0
 * @author AI Trading Platform Team
 */

// =============================================================================
// CORE TYPES
// =============================================================================

export interface BaseEntity {
  readonly id: string;
  readonly createdAt: Date;
  readonly updatedAt: Date;
  readonly version: number;
}

export interface AuditableEntity extends BaseEntity {
  readonly createdBy: string;
  readonly updatedBy: string;
}

// =============================================================================
// SERVICE TYPES
// =============================================================================

export interface ServiceConfig {
  name: string;
  version: string;
  environment: 'development' | 'staging' | 'production';
  port: number;
  adminPort?: number;
  host: string;
  consul: ConsulConfig;
  database?: DatabaseConfig;
  redis?: RedisConfig;
  monitoring?: MonitoringConfig;
}

export interface ConsulConfig {
  host: string;
  port: number;
  token?: string;
  datacenter?: string;
}

export interface DatabaseConfig {
  type: 'postgres' | 'mongodb' | 'redis';
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  ssl?: boolean;
  pool?: {
    min: number;
    max: number;
    acquireTimeoutMillis?: number;
    idleTimeoutMillis?: number;
  };
}

export interface RedisConfig {
  host: string;
  port: number;
  password?: string;
  database?: number;
  cluster?: boolean;
  retryDelayOnFailover?: number;
  maxRetriesPerRequest?: number;
}

// =============================================================================
// HEALTH CHECK TYPES
// =============================================================================

export interface HealthStatus {
  status: 'healthy' | 'unhealthy' | 'degraded';
  timestamp: Date;
  version: string;
  uptime: number;
  environment: string;
  dependencies: HealthDependency[];
  metrics?: HealthMetrics;
}

export interface HealthDependency {
  name: string;
  status: 'healthy' | 'unhealthy' | 'degraded';
  responseTime?: number;
  lastChecked: Date;
  error?: string;
}

export interface HealthMetrics {
  memoryUsage: {
    used: number;
    total: number;
    percentage: number;
  };
  cpuUsage: number;
  diskUsage?: {
    used: number;
    total: number;
    percentage: number;
  };
  requestsPerSecond?: number;
  averageResponseTime?: number;
}

// =============================================================================
// LOGGING TYPES
// =============================================================================

export interface LogLevel {
  level: 'error' | 'warn' | 'info' | 'debug' | 'trace';
}

export interface LogContext {
  service: string;
  version: string;
  environment: string;
  requestId?: string;
  userId?: string;
  traceId?: string;
  spanId?: string;
}

export interface LogEntry extends LogLevel {
  timestamp: Date;
  message: string;
  context: LogContext;
  data?: Record<string, unknown>;
  error?: Error;
}

// =============================================================================
// API TYPES
// =============================================================================

export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: ApiError;
  metadata?: ApiMetadata;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
  stack?: string;
}

export interface ApiMetadata {
  requestId: string;
  timestamp: Date;
  version: string;
  pagination?: PaginationMetadata;
}

export interface PaginationMetadata {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
  hasNext: boolean;
  hasPrevious: boolean;
}

export interface PaginationParams {
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

// =============================================================================
// TRADING TYPES
// =============================================================================

export interface TradingSymbol {
  symbol: string;
  name: string;
  type: 'forex' | 'crypto' | 'stock' | 'commodity';
  exchange?: string;
  precision: number;
  minLot: number;
  maxLot: number;
  lotStep: number;
  contractSize: number;
  currency: string;
  isActive: boolean;
}

export interface TradingOrder extends BaseEntity {
  symbol: string;
  type: 'market' | 'limit' | 'stop' | 'stop_limit';
  side: 'buy' | 'sell';
  amount: number;
  price?: number;
  stopPrice?: number;
  timeInForce: 'GTC' | 'IOC' | 'FOK' | 'GTD';
  status: 'pending' | 'filled' | 'partially_filled' | 'cancelled' | 'rejected';
  filledAmount: number;
  averagePrice?: number;
  commission?: number;
  userId: string;
  accountId: string;
}

export interface TradingPosition extends BaseEntity {
  symbol: string;
  side: 'long' | 'short';
  amount: number;
  entryPrice: number;
  currentPrice: number;
  unrealizedPnL: number;
  realizedPnL: number;
  commission: number;
  userId: string;
  accountId: string;
}

export interface TradingAccount extends AuditableEntity {
  userId: string;
  type: 'demo' | 'live';
  broker: string;
  balance: number;
  equity: number;
  margin: number;
  freeMargin: number;
  marginLevel: number;
  currency: string;
  leverage: number;
  isActive: boolean;
  mt5Login?: string;
  mt5Server?: string;
}

// =============================================================================
// MT5 INTEGRATION TYPES
// =============================================================================

export interface MT5Config {
  host: string;
  port: number;
  login: string;
  password: string;
  server: string;
  timeout: number;
}

export interface MT5TickData {
  symbol: string;
  timestamp: Date;
  bid: number;
  ask: number;
  volume: number;
  spread: number;
}

export interface MT5BarData {
  symbol: string;
  timeframe: MT5Timeframe;
  timestamp: Date;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export type MT5Timeframe =
  | 'M1' | 'M5' | 'M15' | 'M30'
  | 'H1' | 'H4' | 'H12'
  | 'D1' | 'W1' | 'MN1';

export interface MT5OrderRequest {
  action: 'buy' | 'sell';
  symbol: string;
  volume: number;
  price?: number;
  sl?: number;
  tp?: number;
  deviation?: number;
  type?: 'market' | 'pending';
  comment?: string;
  magic?: number;
}

// =============================================================================
// MONITORING TYPES
// =============================================================================

export interface MonitoringConfig {
  prometheus?: {
    enabled: boolean;
    port: number;
    path: string;
  };
  apm?: {
    enabled: boolean;
    serverUrl: string;
    secretToken?: string;
  };
  tracing?: {
    enabled: boolean;
    jaegerEndpoint?: string;
  };
}

export interface Metric {
  name: string;
  type: 'counter' | 'gauge' | 'histogram' | 'summary';
  value: number;
  labels?: Record<string, string>;
  timestamp?: Date;
}

// =============================================================================
// EVENT TYPES
// =============================================================================

export interface DomainEvent extends BaseEntity {
  type: string;
  aggregateId: string;
  aggregateType: string;
  data: Record<string, unknown>;
  metadata: EventMetadata;
}

export interface EventMetadata {
  correlationId: string;
  causationId?: string;
  userId?: string;
  source: string;
  version: number;
}

// =============================================================================
// UTILITY TYPES
// =============================================================================

export type RequireAtLeastOne<T, Keys extends keyof T = keyof T> =
  Pick<T, Exclude<keyof T, Keys>>
  & {
    [K in Keys]-?: Required<Pick<T, K>> & Partial<Pick<T, Exclude<Keys, K>>>;
  }[Keys];

export type Optional<T, K extends keyof T> = Pick<Partial<T>, K> & Omit<T, K>;

export type DeepPartial<T> = T extends object ? {
  [P in keyof T]?: DeepPartial<T[P]>;
} : T;

export type Constructor<T = {}> = new (...args: any[]) => T;

// =============================================================================
// VALIDATION TYPES
// =============================================================================

export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
}

export interface ValidationError {
  field: string;
  message: string;
  value?: unknown;
}

// =============================================================================
// CACHE TYPES
// =============================================================================

export interface CacheOptions {
  ttl?: number;
  tags?: string[];
  compress?: boolean;
}

export interface CacheEntry<T = unknown> {
  value: T;
  ttl: number;
  createdAt: Date;
  tags?: string[];
}

// =============================================================================
// SECURITY TYPES
// =============================================================================

export interface JWTPayload {
  sub: string;
  iat: number;
  exp: number;
  aud: string;
  iss: string;
  roles: string[];
  permissions: string[];
}

export interface AuthContext {
  userId: string;
  roles: string[];
  permissions: string[];
  sessionId: string;
  ipAddress: string;
  userAgent: string;
}

// =============================================================================
// EXPORTS
// =============================================================================

export * from './api';
export * from './config';
export * from './database';
export * from './events';
export * from './logging';
export * from './monitoring';
export * from './trading';