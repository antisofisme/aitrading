// Authentication Types
export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  tenant: Tenant;
  subscription: Subscription;
  preferences: UserPreferences;
  createdAt: string;
  lastLoginAt: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  token: string | null;
}

export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface RegisterData {
  email: string;
  password: string;
  name: string;
  companyName?: string;
  acceptTerms: boolean;
}

// Multi-tenant Types
export interface Tenant {
  id: string;
  name: string;
  slug: string;
  tier: SubscriptionTier;
  settings: TenantSettings;
  branding: TenantBranding;
  features: string[];
  limits: TenantLimits;
  createdAt: string;
}

export interface TenantSettings {
  timezone: string;
  currency: string;
  language: string;
  notifications: NotificationSettings;
}

export interface TenantBranding {
  primaryColor: string;
  secondaryColor: string;
  logo?: string;
  favicon?: string;
  theme: 'light' | 'dark' | 'auto';
}

export interface TenantLimits {
  maxUsers: number;
  maxPositions: number;
  maxAlerts: number;
  apiCallsPerMonth: number;
  dataRetentionDays: number;
}

// Subscription Types
export type SubscriptionTier = 'free' | 'basic' | 'pro' | 'enterprise';

export interface Subscription {
  id: string;
  tier: SubscriptionTier;
  status: 'active' | 'expired' | 'cancelled' | 'suspended';
  features: string[];
  limits: SubscriptionLimits;
  billingCycle: 'monthly' | 'yearly';
  currentPeriodStart: string;
  currentPeriodEnd: string;
  nextBillingDate?: string;
  cancelAtPeriodEnd: boolean;
}

export interface SubscriptionLimits {
  maxPositions: number;
  maxAlerts: number;
  aiPredictionsPerDay: number;
  realTimeData: boolean;
  advancedCharts: boolean;
  customStrategies: boolean;
  apiAccess: boolean;
  priority_support: boolean;
}

// Trading Types
export interface TradingPosition {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  size: number;
  entryPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPercent: number;
  openTime: string;
  status: 'open' | 'closed' | 'pending';
  stopLoss?: number;
  takeProfit?: number;
  aiConfidence?: number;
  marketRegime?: string;
}

export interface MarketData {
  symbol: string;
  bid: number;
  ask: number;
  last: number;
  volume: number;
  change: number;
  changePercent: number;
  high24h: number;
  low24h: number;
  timestamp: string;
}

export interface OrderRequest {
  symbol: string;
  side: 'buy' | 'sell';
  type: 'market' | 'limit' | 'stop';
  size: number;
  price?: number;
  stopLoss?: number;
  takeProfit?: number;
  timeInForce?: 'GTC' | 'IOC' | 'FOK';
}

// AI/ML Types
export interface AIPrediction {
  id: string;
  symbol: string;
  prediction: 'bullish' | 'bearish' | 'neutral';
  confidence: number;
  timeframe: string;
  targetPrice?: number;
  stopLoss?: number;
  reasoning: string[];
  modelUsed: string[];
  marketRegime: string;
  riskLevel: 'low' | 'medium' | 'high';
  generatedAt: string;
  expiresAt: string;
}

export interface MarketRegime {
  type: string;
  confidence: number;
  characteristics: string[];
  recommendation: string;
  volatility: 'low' | 'medium' | 'high';
  trend: 'uptrend' | 'downtrend' | 'sideways';
  updatedAt: string;
}

export interface PerformanceMetrics {
  totalReturn: number;
  totalReturnPercent: number;
  sharpeRatio: number;
  maxDrawdown: number;
  winRate: number;
  profitFactor: number;
  totalTrades: number;
  avgTradeSize: number;
  bestTrade: number;
  worstTrade: number;
  avgHoldingPeriod: number;
  updatedAt: string;
}

// Chart Types
export interface ChartData {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface ChartIndicator {
  name: string;
  values: number[];
  color: string;
  visible: boolean;
}

export interface ChartConfig {
  timeframe: '1m' | '5m' | '15m' | '1h' | '4h' | '1d' | '1w';
  indicators: ChartIndicator[];
  chartType: 'candlestick' | 'line' | 'area';
  overlays: string[];
  theme: 'light' | 'dark';
}

// WebSocket Types
export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
  channel?: string;
}

export interface WebSocketConnection {
  url: string;
  isConnected: boolean;
  lastMessage?: WebSocketMessage;
  connectionId?: string;
  subscriptions: string[];
}

// Notification Types
export interface Notification {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  read: boolean;
  category: 'trading' | 'account' | 'system' | 'ai';
  priority: 'low' | 'medium' | 'high' | 'critical';
  actionUrl?: string;
  actionText?: string;
  createdAt: string;
  expiresAt?: string;
}

export interface NotificationSettings {
  email: boolean;
  push: boolean;
  sms: boolean;
  trading: boolean;
  ai: boolean;
  account: boolean;
  system: boolean;
  marketing: boolean;
}

// User Preferences
export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  timezone: string;
  currency: string;
  notifications: NotificationSettings;
  dashboard: DashboardPreferences;
  trading: TradingPreferences;
}

export interface DashboardPreferences {
  layout: 'compact' | 'comfortable' | 'spacious';
  widgets: string[];
  chartDefaults: ChartConfig;
  autoRefresh: boolean;
  refreshInterval: number;
}

export interface TradingPreferences {
  defaultSize: number;
  riskPercent: number;
  confirmOrders: boolean;
  oneClickTrading: boolean;
  soundAlerts: boolean;
  showPnL: 'absolute' | 'percentage' | 'both';
}

// API Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  errors?: string[];
  pagination?: PaginationInfo;
}

export interface PaginationInfo {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
  hasMore: boolean;
}

export interface ApiError {
  code: string;
  message: string;
  details?: any;
  timestamp: string;
}

// Portfolio Types
export interface Portfolio {
  id: string;
  totalValue: number;
  cash: number;
  positions: TradingPosition[];
  dayChange: number;
  dayChangePercent: number;
  totalPnL: number;
  totalPnLPercent: number;
  metrics: PerformanceMetrics;
  riskMetrics: RiskMetrics;
  updatedAt: string;
}

export interface RiskMetrics {
  totalRisk: number;
  varDaily: number;
  beta: number;
  correlation: number;
  leverage: number;
  marginUsed: number;
  marginAvailable: number;
  riskScore: number;
}

// Dashboard Types
export interface DashboardWidget {
  id: string;
  type: string;
  title: string;
  size: 'small' | 'medium' | 'large';
  position: { x: number; y: number };
  visible: boolean;
  settings: Record<string, any>;
}

export interface DashboardLayout {
  id: string;
  name: string;
  widgets: DashboardWidget[];
  isDefault: boolean;
  createdAt: string;
  updatedAt: string;
}

// Real-time Data Types
export interface RealTimeUpdate {
  type: 'price' | 'position' | 'order' | 'ai_prediction' | 'alert';
  symbol?: string;
  data: any;
  timestamp: string;
}

export interface SystemStatus {
  status: 'healthy' | 'degraded' | 'down';
  services: ServiceStatus[];
  lastChecked: string;
  uptime: number;
}

export interface ServiceStatus {
  name: string;
  status: 'healthy' | 'degraded' | 'down';
  latency: number;
  lastChecked: string;
  message?: string;
}

// Form Types
export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'email' | 'password' | 'number' | 'select' | 'checkbox' | 'radio';
  required?: boolean;
  placeholder?: string;
  options?: { value: string; label: string }[];
  validation?: ValidationRule[];
}

export interface ValidationRule {
  type: 'required' | 'email' | 'min' | 'max' | 'pattern';
  value?: any;
  message: string;
}

// Theme Types
export interface ThemeConfig {
  mode: 'light' | 'dark';
  primaryColor: string;
  secondaryColor: string;
  typography: TypographyConfig;
  spacing: number;
  borderRadius: number;
}

export interface TypographyConfig {
  fontFamily: string;
  fontSize: number;
  fontWeight: {
    light: number;
    regular: number;
    medium: number;
    bold: number;
  };
}