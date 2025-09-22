// Core Types for AI Trading Backend API
import { Request } from 'express';

// User Types
export interface User {
  id: string;
  email: string;
  password_hash: string;
  first_name: string;
  last_name: string;
  subscription_tier: SubscriptionTier;
  subscription_status: SubscriptionStatus;
  created_at: Date;
  updated_at: Date;
  last_login: Date | null;
  is_active: boolean;
  email_verified: boolean;
  mt5_accounts?: MT5Account[];
}

export interface UserProfile {
  id: string;
  user_id: string;
  risk_tolerance: 'low' | 'medium' | 'high';
  max_daily_loss: number;
  max_position_size: number;
  preferred_symbols: string[];
  timezone: string;
  notifications_enabled: boolean;
  created_at: Date;
  updated_at: Date;
}

// Subscription Types
export enum SubscriptionTier {
  FREE = 'free',
  BASIC = 'basic',
  PRO = 'pro',
  ENTERPRISE = 'enterprise'
}

export enum SubscriptionStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  SUSPENDED = 'suspended',
  CANCELLED = 'cancelled'
}

export interface Subscription {
  id: string;
  user_id: string;
  tier: SubscriptionTier;
  status: SubscriptionStatus;
  price: number;
  currency: string;
  billing_cycle: 'monthly' | 'yearly';
  features: string[];
  starts_at: Date;
  ends_at: Date;
  auto_renew: boolean;
  created_at: Date;
  updated_at: Date;
}

// MT5 Integration Types
export interface MT5Account {
  id: string;
  user_id: string;
  login: string;
  server: string;
  name: string;
  balance: number;
  equity: number;
  margin: number;
  free_margin: number;
  margin_level: number;
  is_active: boolean;
  last_sync: Date;
  created_at: Date;
  updated_at: Date;
}

export interface MT5Connection {
  id: string;
  account_id: string;
  status: 'connected' | 'disconnected' | 'error';
  latency_ms: number;
  last_heartbeat: Date;
  error_count: number;
  created_at: Date;
}

export interface MT5Trade {
  id: string;
  account_id: string;
  ticket: number;
  symbol: string;
  type: 'buy' | 'sell';
  volume: number;
  open_price: number;
  close_price?: number;
  stop_loss?: number;
  take_profit?: number;
  commission: number;
  swap: number;
  profit: number;
  opened_at: Date;
  closed_at?: Date;
  created_at: Date;
}

// Trading Signal Types
export interface TradingSignal {
  id: string;
  user_id: string;
  symbol: string;
  type: 'buy' | 'sell';
  entry_price: number;
  stop_loss?: number;
  take_profit?: number;
  volume: number;
  confidence: number;
  reasoning: string;
  status: 'pending' | 'executed' | 'cancelled' | 'expired';
  expires_at: Date;
  created_at: Date;
  executed_at?: Date;
}

// API Types
export interface AuthenticatedRequest extends Request {
  user?: User;
  subscription?: Subscription;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  timestamp: Date;
  request_id: string;
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

// Database Types
export interface DatabaseConfig {
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  ssl?: boolean;
  pool?: {
    min: number;
    max: number;
  };
}

export interface QueryResult<T = any> {
  rows: T[];
  rowCount: number;
  command: string;
  duration: number;
}

// Security Types
export interface JWTPayload {
  user_id: string;
  email: string;
  subscription_tier: SubscriptionTier;
  iat: number;
  exp: number;
  jti: string;
}

export interface RefreshTokenPayload {
  user_id: string;
  token_id: string;
  iat: number;
  exp: number;
}

export interface SecurityEvent {
  id: string;
  user_id?: string;
  event_type: 'login' | 'logout' | 'failed_login' | 'token_refresh' | 'password_change' | 'suspicious_activity';
  ip_address: string;
  user_agent: string;
  details: Record<string, any>;
  risk_score: number;
  created_at: Date;
}

// Error Types
export interface ErrorDNAError {
  id: string;
  error_code: string;
  message: string;
  stack?: string;
  context: Record<string, any>;
  user_id?: string;
  request_id: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  created_at: Date;
}

// Logging Types
export enum LogLevel {
  DEBUG = 'debug',
  INFO = 'info',
  WARN = 'warn',
  ERROR = 'error',
  CRITICAL = 'critical'
}

export interface LogEntry {
  level: LogLevel;
  message: string;
  timestamp: Date;
  request_id?: string;
  user_id?: string;
  service: string;
  component: string;
  metadata?: Record<string, any>;
}

// Rate Limiting Types
export interface RateLimitConfig {
  windowMs: number;
  max: number;
  message: string;
  skipSuccessfulRequests?: boolean;
  skipFailedRequests?: boolean;
  keyGenerator?: (req: Request) => string;
}

// Health Check Types
export interface HealthStatus {
  service: string;
  status: 'healthy' | 'unhealthy' | 'degraded';
  checks: HealthCheck[];
  timestamp: Date;
}

export interface HealthCheck {
  name: string;
  status: 'pass' | 'fail' | 'warn';
  duration_ms: number;
  message?: string;
  details?: Record<string, any>;
}

// Performance Types
export interface PerformanceMetrics {
  request_count: number;
  average_response_time: number;
  error_rate: number;
  throughput: number;
  memory_usage: number;
  cpu_usage: number;
  active_connections: number;
  timestamp: Date;
}

// Validation Types
export interface ValidationError {
  field: string;
  message: string;
  value?: any;
}

export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
}

// WebSocket Types
export interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp: Date;
  user_id?: string;
}

export interface WebSocketConnection {
  id: string;
  user_id: string;
  socket: any;
  last_ping: Date;
  created_at: Date;
}

// Configuration Types
export interface AppConfig {
  port: number;
  nodeEnv: string;
  apiVersion: string;
  cors: {
    origin: string | string[];
    credentials: boolean;
  };
  jwt: {
    secret: string;
    refreshSecret: string;
    expiresIn: string;
    refreshExpiresIn: string;
  };
  database: {
    postgres: DatabaseConfig;
    clickhouse: DatabaseConfig;
    redis: {
      host: string;
      port: number;
      password?: string;
      db: number;
    };
  };
  mt5: {
    websocketHost: string;
    websocketPort: number;
    connectionTimeout: number;
    retryAttempts: number;
    poolSize: number;
  };
  security: {
    bcryptRounds: number;
    rateLimiting: RateLimitConfig;
  };
  logging: {
    level: LogLevel;
    maxFiles: string;
    maxSize: string;
    compress: boolean;
  };
}