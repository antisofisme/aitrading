import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { TestDataManager } from './test-data-manager';

/**
 * Helper class for API testing and validation
 */
export class APIHelper {
  private api: AxiosInstance;
  private testDataManager: TestDataManager;
  private baseURL: string;

  constructor() {
    this.baseURL = process.env.API_BASE_URL || 'http://localhost:8000/api/v1';
    this.testDataManager = new TestDataManager();

    this.api = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    });

    // Add request interceptor for logging
    this.api.interceptors.request.use(
      (config) => {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('API Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Add response interceptor for logging
    this.api.interceptors.response.use(
      (response) => {
        console.log(`API Response: ${response.status} ${response.config.url}`);
        return response;
      },
      (error) => {
        console.error('API Response Error:', error.response?.status, error.response?.data);
        return Promise.reject(error);
      }
    );
  }

  /**
   * Set authentication token for requests
   */
  setAuthToken(token: string): void {
    this.api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  /**
   * Clear authentication token
   */
  clearAuthToken(): void {
    delete this.api.defaults.headers.common['Authorization'];
  }

  /**
   * Authenticate user and get token
   */
  async authenticate(role: string = 'trader'): Promise<string> {
    const credentials = this.testDataManager.getTestCredentials(role);

    const response = await this.api.post('/auth/login', {
      email: credentials.email,
      password: credentials.password
    });

    const token = response.data.token;
    this.setAuthToken(token);

    return token;
  }

  /**
   * Test API health
   */
  async checkHealth(): Promise<boolean> {
    try {
      const response = await this.api.get('/health');
      return response.status === 200;
    } catch (error) {
      return false;
    }
  }

  /**
   * User management API tests
   */
  async createUser(userData: any): Promise<AxiosResponse> {
    return await this.api.post('/auth/register', userData);
  }

  async getUserProfile(userId?: string): Promise<AxiosResponse> {
    const endpoint = userId ? `/users/${userId}` : '/users/me';
    return await this.api.get(endpoint);
  }

  async updateUserProfile(updates: any): Promise<AxiosResponse> {
    return await this.api.put('/users/me', updates);
  }

  async deleteUser(userId: string): Promise<AxiosResponse> {
    return await this.api.delete(`/users/${userId}`);
  }

  /**
   * Trading API tests
   */
  async getMarketData(symbol?: string): Promise<AxiosResponse> {
    const endpoint = symbol ? `/market-data/${symbol}` : '/market-data';
    return await this.api.get(endpoint);
  }

  async placeOrder(orderData: {
    symbol: string;
    side: 'buy' | 'sell';
    type: 'market' | 'limit' | 'stop';
    quantity: number;
    price?: number;
    stopLoss?: number;
    takeProfit?: number;
  }): Promise<AxiosResponse> {
    return await this.api.post('/orders', orderData);
  }

  async getOrders(filters?: any): Promise<AxiosResponse> {
    return await this.api.get('/orders', { params: filters });
  }

  async getOrder(orderId: string): Promise<AxiosResponse> {
    return await this.api.get(`/orders/${orderId}`);
  }

  async cancelOrder(orderId: string): Promise<AxiosResponse> {
    return await this.api.delete(`/orders/${orderId}`);
  }

  async getPositions(): Promise<AxiosResponse> {
    return await this.api.get('/positions');
  }

  async closePosition(symbol: string): Promise<AxiosResponse> {
    return await this.api.post(`/positions/${symbol}/close`);
  }

  /**
   * Strategy API tests
   */
  async createStrategy(strategyData: any): Promise<AxiosResponse> {
    return await this.api.post('/strategies', strategyData);
  }

  async getStrategies(): Promise<AxiosResponse> {
    return await this.api.get('/strategies');
  }

  async getStrategy(strategyId: string): Promise<AxiosResponse> {
    return await this.api.get(`/strategies/${strategyId}`);
  }

  async updateStrategy(strategyId: string, updates: any): Promise<AxiosResponse> {
    return await this.api.put(`/strategies/${strategyId}`, updates);
  }

  async deleteStrategy(strategyId: string): Promise<AxiosResponse> {
    return await this.api.delete(`/strategies/${strategyId}`);
  }

  async runBacktest(strategyId: string, params: any): Promise<AxiosResponse> {
    return await this.api.post(`/strategies/${strategyId}/backtest`, params);
  }

  async enableStrategy(strategyId: string): Promise<AxiosResponse> {
    return await this.api.post(`/strategies/${strategyId}/enable`);
  }

  async disableStrategy(strategyId: string): Promise<AxiosResponse> {
    return await this.api.post(`/strategies/${strategyId}/disable`);
  }

  /**
   * Portfolio API tests
   */
  async getPortfolio(): Promise<AxiosResponse> {
    return await this.api.get('/portfolio');
  }

  async getPortfolioHistory(params?: any): Promise<AxiosResponse> {
    return await this.api.get('/portfolio/history', { params });
  }

  async getPortfolioMetrics(): Promise<AxiosResponse> {
    return await this.api.get('/portfolio/metrics');
  }

  /**
   * Analytics API tests
   */
  async getAnalytics(params?: any): Promise<AxiosResponse> {
    return await this.api.get('/analytics', { params });
  }

  async getPerformanceMetrics(params?: any): Promise<AxiosResponse> {
    return await this.api.get('/analytics/performance', { params });
  }

  async getRiskMetrics(): Promise<AxiosResponse> {
    return await this.api.get('/analytics/risk');
  }

  /**
   * Reporting API tests
   */
  async generateReport(reportData: {
    type: string;
    dateFrom: string;
    dateTo: string;
    format?: string;
    filters?: any;
  }): Promise<AxiosResponse> {
    return await this.api.post('/reports', reportData);
  }

  async getReports(): Promise<AxiosResponse> {
    return await this.api.get('/reports');
  }

  async getReport(reportId: string): Promise<AxiosResponse> {
    return await this.api.get(`/reports/${reportId}`);
  }

  async downloadReport(reportId: string): Promise<AxiosResponse> {
    return await this.api.get(`/reports/${reportId}/download`, {
      responseType: 'blob'
    });
  }

  /**
   * Risk management API tests
   */
  async getRiskSettings(): Promise<AxiosResponse> {
    return await this.api.get('/risk/settings');
  }

  async updateRiskSettings(settings: any): Promise<AxiosResponse> {
    return await this.api.put('/risk/settings', settings);
  }

  async getRiskLimits(): Promise<AxiosResponse> {
    return await this.api.get('/risk/limits');
  }

  async checkRiskCompliance(orderData: any): Promise<AxiosResponse> {
    return await this.api.post('/risk/check', orderData);
  }

  /**
   * WebSocket API tests
   */
  async subscribeToMarketData(symbols: string[]): Promise<any> {
    // This would typically use WebSocket connections
    // For testing, we might use a polling approach or mock
    return await this.api.post('/subscriptions/market-data', { symbols });
  }

  async subscribeToOrderUpdates(): Promise<any> {
    return await this.api.post('/subscriptions/orders');
  }

  async subscribeToPositionUpdates(): Promise<any> {
    return await this.api.post('/subscriptions/positions');
  }

  /**
   * Admin API tests
   */
  async getAllUsers(): Promise<AxiosResponse> {
    return await this.api.get('/admin/users');
  }

  async getUserDetails(userId: string): Promise<AxiosResponse> {
    return await this.api.get(`/admin/users/${userId}`);
  }

  async suspendUser(userId: string): Promise<AxiosResponse> {
    return await this.api.post(`/admin/users/${userId}/suspend`);
  }

  async activateUser(userId: string): Promise<AxiosResponse> {
    return await this.api.post(`/admin/users/${userId}/activate`);
  }

  async getSystemMetrics(): Promise<AxiosResponse> {
    return await this.api.get('/admin/metrics');
  }

  async getAuditLogs(params?: any): Promise<AxiosResponse> {
    return await this.api.get('/admin/audit-logs', { params });
  }

  /**
   * Performance testing helpers
   */
  async runLoadTest(endpoint: string, requests: number, concurrency: number): Promise<any> {
    const results = {
      total: requests,
      successful: 0,
      failed: 0,
      avgResponseTime: 0,
      errors: []
    };

    const promises = [];
    const startTime = Date.now();

    for (let i = 0; i < requests; i++) {
      const promise = this.api.get(endpoint)
        .then(() => {
          results.successful++;
        })
        .catch((error) => {
          results.failed++;
          results.errors.push(error.message);
        });

      promises.push(promise);

      // Control concurrency
      if (promises.length >= concurrency) {
        await Promise.all(promises);
        promises.length = 0;
      }
    }

    // Wait for remaining requests
    if (promises.length > 0) {
      await Promise.all(promises);
    }

    const endTime = Date.now();
    results.avgResponseTime = (endTime - startTime) / requests;

    return results;
  }

  /**
   * Data validation helpers
   */
  validateOrderResponse(response: AxiosResponse): boolean {
    const data = response.data;
    return !!(
      data.orderId &&
      data.symbol &&
      data.side &&
      data.quantity &&
      data.status
    );
  }

  validatePositionResponse(response: AxiosResponse): boolean {
    const data = response.data;
    return !!(
      data.symbol &&
      typeof data.quantity === 'number' &&
      typeof data.entryPrice === 'number' &&
      typeof data.currentPrice === 'number'
    );
  }

  validatePortfolioResponse(response: AxiosResponse): boolean {
    const data = response.data;
    return !!(
      typeof data.balance === 'number' &&
      typeof data.equity === 'number' &&
      typeof data.marginUsed === 'number' &&
      typeof data.marginAvailable === 'number'
    );
  }

  /**
   * Error simulation
   */
  simulateNetworkError(): void {
    this.api.interceptors.request.use(
      () => {
        throw new Error('Simulated network error');
      }
    );
  }

  simulateSlowResponse(delay: number): void {
    this.api.interceptors.request.use(
      async (config) => {
        await new Promise(resolve => setTimeout(resolve, delay));
        return config;
      }
    );
  }

  resetInterceptors(): void {
    this.api.interceptors.request.clear();
    this.api.interceptors.response.clear();
  }

  /**
   * Cleanup
   */
  cleanup(): void {
    this.clearAuthToken();
    this.resetInterceptors();
  }
}