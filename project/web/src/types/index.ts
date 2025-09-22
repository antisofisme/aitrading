// Core Types for AI Trading Platform

export interface User {
  id: string;
  email: string;
  username: string;
  firstName?: string;
  lastName?: string;
  role: UserRole;
  isActive: boolean;
  createdAt: Date;
  lastLogin?: Date;
}

export enum UserRole {
  ADMIN = 'admin',
  TRADER = 'trader',
  ANALYST = 'analyst',
  VIEWER = 'viewer'
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// Market Data Types
export interface MarketData {
  symbol: string;
  bid: number;
  ask: number;
  spread: number;
  timestamp: Date;
  volume?: number;
  high?: number;
  low?: number;
  open?: number;
  close?: number;
}

export interface Tick {
  symbol: string;
  bid: number;
  ask: number;
  last: number;
  volume: number;
  time: Date;
}

// Trading Types
export interface Position {
  id: string;
  symbol: string;
  type: PositionType;
  volume: number;
  openPrice: number;
  currentPrice: number;
  profit: number;
  swap: number;
  commission: number;
  openTime: Date;
  sl?: number; // Stop Loss
  tp?: number; // Take Profit
}

export enum PositionType {
  BUY = 'buy',
  SELL = 'sell'
}

export interface Order {
  id: string;
  symbol: string;
  type: OrderType;
  volume: number;
  price: number;
  sl?: number;
  tp?: number;
  status: OrderStatus;
  createdAt: Date;
  executedAt?: Date;
}

export enum OrderType {
  MARKET_BUY = 'market_buy',
  MARKET_SELL = 'market_sell',
  LIMIT_BUY = 'limit_buy',
  LIMIT_SELL = 'limit_sell',
  STOP_BUY = 'stop_buy',
  STOP_SELL = 'stop_sell'
}

export enum OrderStatus {
  PENDING = 'pending',
  EXECUTED = 'executed',
  CANCELLED = 'cancelled',
  REJECTED = 'rejected'
}

// AI Prediction Types
export interface AIPrediction {
  id: string;
  symbol: string;
  direction: PredictionDirection;
  confidence: number; // 0-1
  targetPrice: number;
  timeframe: string; // '1m', '5m', '1h', '1d', etc.
  reasoning: string;
  createdAt: Date;
  expiresAt: Date;
  status: PredictionStatus;
}

export enum PredictionDirection {
  BUY = 'buy',
  SELL = 'sell',
  HOLD = 'hold'
}

export enum PredictionStatus {
  ACTIVE = 'active',
  EXECUTED = 'executed',
  EXPIRED = 'expired',
  CANCELLED = 'cancelled'
}

// Performance Analytics Types
export interface PerformanceMetrics {
  totalProfit: number;
  totalTrades: number;
  winRate: number;
  sharpeRatio: number;
  maxDrawdown: number;
  averageWin: number;
  averageLoss: number;
  profitFactor: number;
  period: string;
  updatedAt: Date;
}

export interface TradingMetrics {
  dailyPnL: number;
  weeklyPnL: number;
  monthlyPnL: number;
  totalPnL: number;
  openPositions: number;
  totalVolume: number;
  successRate: number;
  riskScore: number;
}

// WebSocket Types
export interface WSMessage {
  type: WSMessageType;
  data: any;
  timestamp: Date;
}

export enum WSMessageType {
  MARKET_DATA = 'market_data',
  POSITION_UPDATE = 'position_update',
  ORDER_UPDATE = 'order_update',
  AI_PREDICTION = 'ai_prediction',
  NOTIFICATION = 'notification',
  HEARTBEAT = 'heartbeat'
}

// Dashboard Types
export interface DashboardConfig {
  layout: LayoutConfig[];
  theme: 'light' | 'dark';
  autoRefresh: boolean;
  refreshInterval: number;
  notifications: boolean;
}

export interface LayoutConfig {
  id: string;
  component: string;
  x: number;
  y: number;
  w: number;
  h: number;
  minW?: number;
  minH?: number;
}

// API Response Types
export interface ApiResponse<T> {
  data: T;
  message: string;
  success: boolean;
  timestamp: Date;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  hasNext: boolean;
  hasPrev: boolean;
}

// Error Types
export interface ApiError {
  code: string;
  message: string;
  details?: any;
  timestamp: Date;
}

// Chart Types
export interface ChartData {
  timestamp: Date;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface TechnicalIndicator {
  name: string;
  values: number[];
  timestamps: Date[];
  parameters: Record<string, any>;
}

// Notification Types
export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  severity: NotificationSeverity;
  read: boolean;
  createdAt: Date;
  actionUrl?: string;
}

export enum NotificationType {
  TRADE_ALERT = 'trade_alert',
  SYSTEM_ALERT = 'system_alert',
  AI_SIGNAL = 'ai_signal',
  RISK_WARNING = 'risk_warning',
  INFO = 'info'
}

export enum NotificationSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

// System Status Types
export interface SystemStatus {
  service: string;
  status: ServiceStatus;
  lastCheck: Date;
  responseTime: number;
  uptime: number;
  version: string;
}

export enum ServiceStatus {
  HEALTHY = 'healthy',
  WARNING = 'warning',
  ERROR = 'error',
  OFFLINE = 'offline'
}

// Theme Types
export interface ThemeConfig {
  mode: 'light' | 'dark';
  primaryColor: string;
  secondaryColor: string;
  fontFamily: string;
  fontSize: number;
  borderRadius: number;
}