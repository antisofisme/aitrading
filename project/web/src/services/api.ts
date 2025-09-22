import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';
import { ApiResponse, PaginatedResponse, User, MarketData, Position, Order, AIPrediction, PerformanceMetrics } from '@/types';

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_TIMEOUT = parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '10000');

class ApiService {
  private api: AxiosInstance;
  private authToken: string | null = null;

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor
    this.api.interceptors.request.use(
      (config) => {
        if (this.authToken) {
          config.headers.Authorization = `Bearer ${this.authToken}`;
        }

        // Add timestamp for cache busting if needed
        if (config.method === 'get') {
          config.params = {
            ...config.params,
            _t: Date.now(),
          };
        }

        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.api.interceptors.response.use(
      (response: AxiosResponse) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          this.clearAuth();
          window.location.href = '/login';
        }

        return Promise.reject(this.formatError(error));
      }
    );
  }

  private formatError(error: AxiosError): Error {
    const message = error.response?.data?.message || error.message || 'An error occurred';
    const formattedError = new Error(message);
    (formattedError as any).status = error.response?.status;
    (formattedError as any).code = error.response?.data?.code;
    return formattedError;
  }

  // Authentication methods
  setAuthToken(token: string) {
    this.authToken = token;
    localStorage.setItem('auth_token', token);
  }

  clearAuth() {
    this.authToken = null;
    localStorage.removeItem('auth_token');
  }

  initAuth() {
    const token = localStorage.getItem('auth_token');
    if (token) {
      this.authToken = token;
    }
  }

  // Authentication API
  async login(email: string, password: string): Promise<{ user: User; token: string }> {
    const response = await this.api.post('/api/v1/auth/login', { email, password });
    return response.data.data;
  }

  async logout(): Promise<void> {
    try {
      await this.api.post('/api/v1/auth/logout');
    } finally {
      this.clearAuth();
    }
  }

  async refreshToken(): Promise<{ token: string }> {
    const response = await this.api.post('/api/v1/auth/refresh');
    return response.data.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.api.get('/api/v1/auth/me');
    return response.data.data;
  }

  // Market Data API
  async getMarketData(symbols?: string[]): Promise<MarketData[]> {
    const params = symbols ? { symbols: symbols.join(',') } : {};
    const response = await this.api.get('/api/v1/market/data', { params });
    return response.data.data;
  }

  async getHistoricalData(\n    symbol: string, \n    timeframe: string, \n    from: Date, \n    to: Date\n  ): Promise<any[]> {\n    const response = await this.api.get(`/api/v1/market/history/${symbol}`, {\n      params: {\n        timeframe,\n        from: from.toISOString(),\n        to: to.toISOString(),\n      },\n    });\n    return response.data.data;\n  }\n\n  // Trading API\n  async getPositions(): Promise<Position[]> {\n    const response = await this.api.get('/api/v1/trading/positions');\n    return response.data.data;\n  }\n\n  async getOrders(status?: string): Promise<Order[]> {\n    const params = status ? { status } : {};\n    const response = await this.api.get('/api/v1/trading/orders', { params });\n    return response.data.data;\n  }\n\n  async placeOrder(order: Partial<Order>): Promise<Order> {\n    const response = await this.api.post('/api/v1/trading/orders', order);\n    return response.data.data;\n  }\n\n  async closePosition(positionId: string): Promise<void> {\n    await this.api.delete(`/api/v1/trading/positions/${positionId}`);\n  }\n\n  async modifyPosition(\n    positionId: string, \n    updates: { sl?: number; tp?: number }\n  ): Promise<Position> {\n    const response = await this.api.patch(`/api/v1/trading/positions/${positionId}`, updates);\n    return response.data.data;\n  }\n\n  // AI Predictions API\n  async getAIPredictions(symbol?: string): Promise<AIPrediction[]> {\n    const params = symbol ? { symbol } : {};\n    const response = await this.api.get('/api/v1/ai/predictions', { params });\n    return response.data.data;\n  }\n\n  async requestAIPrediction(\n    symbol: string, \n    timeframe: string\n  ): Promise<AIPrediction> {\n    const response = await this.api.post('/api/v1/ai/predictions', {\n      symbol,\n      timeframe,\n    });\n    return response.data.data;\n  }\n\n  // Performance Analytics API\n  async getPerformanceMetrics(period?: string): Promise<PerformanceMetrics> {\n    const params = period ? { period } : {};\n    const response = await this.api.get('/api/v1/analytics/performance', { params });\n    return response.data.data;\n  }\n\n  async getTradingMetrics(): Promise<any> {\n    const response = await this.api.get('/api/v1/analytics/trading');\n    return response.data.data;\n  }\n\n  async getRiskMetrics(): Promise<any> {\n    const response = await this.api.get('/api/v1/analytics/risk');\n    return response.data.data;\n  }\n\n  // System Status API\n  async getSystemStatus(): Promise<any[]> {\n    const response = await this.api.get('/api/v1/system/status');\n    return response.data.data;\n  }\n\n  async getServiceHealth(service?: string): Promise<any> {\n    const endpoint = service \n      ? `/api/v1/system/health/${service}`\n      : '/api/v1/system/health';\n    const response = await this.api.get(endpoint);\n    return response.data.data;\n  }\n\n  // Notifications API\n  async getNotifications(unreadOnly = false): Promise<any[]> {\n    const params = unreadOnly ? { unread: 'true' } : {};\n    const response = await this.api.get('/api/v1/notifications', { params });\n    return response.data.data;\n  }\n\n  async markNotificationRead(notificationId: string): Promise<void> {\n    await this.api.patch(`/api/v1/notifications/${notificationId}/read`);\n  }\n\n  async markAllNotificationsRead(): Promise<void> {\n    await this.api.patch('/api/v1/notifications/read-all');\n  }\n\n  // Generic API methods\n  async get<T>(endpoint: string, params?: any): Promise<T> {\n    const response = await this.api.get(endpoint, { params });\n    return response.data.data;\n  }\n\n  async post<T>(endpoint: string, data?: any): Promise<T> {\n    const response = await this.api.post(endpoint, data);\n    return response.data.data;\n  }\n\n  async patch<T>(endpoint: string, data?: any): Promise<T> {\n    const response = await this.api.patch(endpoint, data);\n    return response.data.data;\n  }\n\n  async delete<T>(endpoint: string): Promise<T> {\n    const response = await this.api.delete(endpoint);\n    return response.data.data;\n  }\n}\n\n// Export singleton instance\nexport const apiService = new ApiService();\nexport default apiService;\n\n// Initialize auth on import\nif (typeof window !== 'undefined') {\n  apiService.initAuth();\n}