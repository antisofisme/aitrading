import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { ApiResponse, ApiError } from '../types';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';

// Create axios instance with default configuration
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000, // 30 seconds
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    withCredentials: true, // Include cookies for session management
  });

  return client;
};

export const apiClient = createApiClient();

// Token management
let accessToken: string | null = null;
let refreshToken: string | null = null;
let tokenRotationTimer: NodeJS.Timeout | null = null;

export const setTokens = (access: string, refresh?: string) => {
  accessToken = access;
  if (refresh) {
    refreshToken = refresh;
  }

  // Schedule token rotation every 10 minutes
  if (tokenRotationTimer) {
    clearInterval(tokenRotationTimer);
  }

  tokenRotationTimer = setInterval(() => {
    refreshAccessToken();
  }, 10 * 60 * 1000); // 10 minutes
};

export const clearTokens = () => {
  accessToken = null;
  refreshToken = null;

  if (tokenRotationTimer) {
    clearInterval(tokenRotationTimer);
    tokenRotationTimer = null;
  }
};

export const getAccessToken = () => accessToken;

// Token refresh function
const refreshAccessToken = async (): Promise<string | null> => {
  try {
    const response = await axios.post('/api/auth/refresh', {}, {
      withCredentials: true,
      baseURL: API_BASE_URL,
    });

    if (response.data.success && response.data.data.accessToken) {
      accessToken = response.data.data.accessToken;
      return accessToken;
    }

    return null;
  } catch (error) {
    console.error('Token refresh failed:', error);
    clearTokens();
    // Redirect to login if refresh fails
    if (window.location.pathname !== '/auth/login') {
      window.location.href = '/auth/login';
    }
    return null;
  }
};

// Request interceptor for adding auth token
apiClient.interceptors.request.use(
  (config) => {
    // Add security headers
    config.headers['X-Requested-With'] = 'XMLHttpRequest';
    config.headers['X-Client-Timestamp'] = Date.now().toString();
    config.headers['X-Request-ID'] = generateRequestId();

    // Add auth token if available
    if (accessToken) {
      config.headers['Authorization'] = `Bearer ${accessToken}`;
    }

    // Add tenant context if available
    const tenantId = getCurrentTenantId();
    if (tenantId) {
      config.headers['X-Tenant-ID'] = tenantId;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling and token refresh
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error) => {
    const originalRequest = error.config;

    // Handle 401 Unauthorized - attempt token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const newToken = await refreshAccessToken();
      if (newToken) {
        originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
        return apiClient(originalRequest);
      }
    }

    // Handle other errors
    const apiError: ApiError = {
      code: error.response?.data?.code || 'UNKNOWN_ERROR',
      message: error.response?.data?.message || error.message || 'An unexpected error occurred',
      details: error.response?.data?.details,
      timestamp: new Date().toISOString(),
    };

    // Log errors for monitoring
    console.error('API Error:', apiError);

    return Promise.reject(apiError);
  }
);

// Utility functions
const generateRequestId = (): string => {
  return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

const getCurrentTenantId = (): string | null => {
  // Extract tenant ID from subdomain, path, or stored context
  const hostname = window.location.hostname;
  const subdomain = hostname.split('.')[0];

  // If subdomain is not 'www' or 'app', use it as tenant ID
  if (subdomain && !['www', 'app', 'localhost'].includes(subdomain)) {
    return subdomain;
  }

  // Alternative: get from stored context or path
  return localStorage.getItem('tenantId') || null;
};

// API wrapper functions with proper typing
export const api = {
  // Generic request method
  async request<T = any>(config: AxiosRequestConfig): Promise<ApiResponse<T>> {
    try {
      const response = await apiClient(config);
      return response.data;
    } catch (error) {
      throw error;
    }
  },

  // GET request
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>({ ...config, method: 'GET', url });
  },

  // POST request
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>({ ...config, method: 'POST', url, data });
  },

  // PUT request
  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>({ ...config, method: 'PUT', url, data });
  },

  // PATCH request
  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>({ ...config, method: 'PATCH', url, data });
  },

  // DELETE request
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>({ ...config, method: 'DELETE', url });
  },
};

// Rate limiting helper
class RateLimiter {
  private requests: number[] = [];
  private maxRequests: number;
  private timeWindow: number;

  constructor(maxRequests: number = 100, timeWindowMs: number = 60000) {
    this.maxRequests = maxRequests;
    this.timeWindow = timeWindowMs;
  }

  canMakeRequest(): boolean {
    const now = Date.now();
    const cutoff = now - this.timeWindow;

    // Remove old requests
    this.requests = this.requests.filter(time => time > cutoff);

    // Check if we can make a new request
    if (this.requests.length < this.maxRequests) {
      this.requests.push(now);
      return true;
    }

    return false;
  }

  getRemainingRequests(): number {
    const now = Date.now();
    const cutoff = now - this.timeWindow;
    this.requests = this.requests.filter(time => time > cutoff);
    return Math.max(0, this.maxRequests - this.requests.length);
  }
}

export const rateLimiter = new RateLimiter();

// Security validation helpers
export const validateApiResponse = <T>(response: any): response is ApiResponse<T> => {
  return (
    typeof response === 'object' &&
    response !== null &&
    typeof response.success === 'boolean'
  );
};

export const sanitizeApiData = (data: any): any => {
  if (typeof data === 'string') {
    return data.replace(/[<>'"&]/g, '');
  }

  if (Array.isArray(data)) {
    return data.map(sanitizeApiData);
  }

  if (typeof data === 'object' && data !== null) {
    const sanitized: any = {};
    for (const [key, value] of Object.entries(data)) {
      sanitized[key] = sanitizeApiData(value);
    }
    return sanitized;
  }

  return data;
};

// API endpoint constants
export const API_ENDPOINTS = {
  // Authentication
  AUTH: {
    LOGIN: '/api/auth/login',
    LOGOUT: '/api/auth/logout',
    REGISTER: '/api/auth/register',
    REFRESH: '/api/auth/refresh',
    VERIFY_EMAIL: '/api/auth/verify-email',
    RESET_PASSWORD: '/api/auth/reset-password',
    UPDATE_PASSWORD: '/api/auth/update-password',
    PROFILE: '/api/auth/profile',
  },

  // Trading
  TRADING: {
    POSITIONS: '/api/trading/positions',
    ORDERS: '/api/trading/orders',
    HISTORY: '/api/trading/history',
    BALANCE: '/api/trading/balance',
    PORTFOLIO: '/api/trading/portfolio',
  },

  // Market Data
  MARKET: {
    PRICES: '/api/market/prices',
    SYMBOLS: '/api/market/symbols',
    HISTORY: '/api/market/history',
    NEWS: '/api/market/news',
  },

  // AI/ML
  AI: {
    PREDICTIONS: '/api/ai/predictions',
    INSIGHTS: '/api/ai/insights',
    REGIME: '/api/ai/market-regime',
    CONFIDENCE: '/api/ai/confidence',
  },

  // User Management
  USER: {
    PROFILE: '/api/user/profile',
    PREFERENCES: '/api/user/preferences',
    NOTIFICATIONS: '/api/user/notifications',
    SETTINGS: '/api/user/settings',
  },

  // Subscription
  SUBSCRIPTION: {
    STATUS: '/api/subscription/status',
    PLANS: '/api/subscription/plans',
    BILLING: '/api/subscription/billing',
    USAGE: '/api/subscription/usage',
  },

  // System
  SYSTEM: {
    STATUS: '/api/system/status',
    HEALTH: '/api/system/health',
    METRICS: '/api/system/metrics',
  },
} as const;

// WebSocket URL
export const WS_URL = WS_BASE_URL;

// Export default
export default api;