const axios = require('axios');

/**
 * Service for integrating with Central Hub
 * Handles user authentication events and coordination
 */
class CentralHubService {
  constructor() {
    this.baseURL = process.env.CENTRAL_HUB_URL || 'http://localhost:3000';
    this.apiKey = process.env.CENTRAL_HUB_API_KEY || 'hub-api-key';
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 5000,
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json'
      }
    });
  }

  /**
   * Notify Central Hub of user login
   */
  async notifyUserLogin(user, sessionInfo) {
    try {
      const response = await this.client.post('/api/hub/events/user-login', {
        userId: user.id,
        email: user.email,
        role: user.role,
        loginTime: new Date().toISOString(),
        sessionInfo
      });

      return response.data;
    } catch (error) {
      console.error('Failed to notify Central Hub of user login:', error.message);
      // Don't throw error - this is a non-critical operation
      return null;
    }
  }

  /**
   * Notify Central Hub of user logout
   */
  async notifyUserLogout(userId, sessionInfo) {
    try {
      const response = await this.client.post('/api/hub/events/user-logout', {
        userId,
        logoutTime: new Date().toISOString(),
        sessionInfo
      });

      return response.data;
    } catch (error) {
      console.error('Failed to notify Central Hub of user logout:', error.message);
      return null;
    }
  }

  /**
   * Sync user data with Central Hub
   */
  async syncUserData(user) {
    try {
      const response = await this.client.post('/api/hub/users/sync', {
        userId: user.id,
        email: user.email,
        role: user.role,
        isActive: user.isActive,
        lastSync: new Date().toISOString()
      });

      return response.data;
    } catch (error) {
      console.error('Failed to sync user data with Central Hub:', error.message);
      return null;
    }
  }

  /**
   * Validate user permissions with Central Hub
   */
  async validateUserPermissions(userId, resource, action) {
    try {
      const response = await this.client.post('/api/hub/permissions/validate', {
        userId,
        resource,
        action,
        timestamp: new Date().toISOString()
      });

      return response.data;
    } catch (error) {
      console.error('Failed to validate permissions with Central Hub:', error.message);
      // Default to deny if Central Hub is unavailable
      return { allowed: false, reason: 'Hub unavailable' };
    }
  }

  /**
   * Get system status from Central Hub
   */
  async getSystemStatus() {
    try {
      const response = await this.client.get('/api/hub/status');
      return response.data;
    } catch (error) {
      console.error('Failed to get system status from Central Hub:', error.message);
      return { status: 'unavailable', error: error.message };
    }
  }

  /**
   * Register authentication service with Central Hub
   */
  async registerService() {
    try {
      const response = await this.client.post('/api/hub/services/register', {
        serviceName: 'api-gateway',
        serviceType: 'authentication',
        version: '1.0.0',
        endpoints: [
          '/api/auth/login',
          '/api/auth/register',
          '/api/auth/logout',
          '/api/auth/refresh',
          '/api/auth/verify'
        ],
        capabilities: [
          'jwt-authentication',
          'role-based-access',
          'token-refresh',
          'user-management'
        ],
        registeredAt: new Date().toISOString()
      });

      console.log('API Gateway registered with Central Hub:', response.data);
      return response.data;
    } catch (error) {
      console.error('Failed to register with Central Hub:', error.message);
      return null;
    }
  }

  /**
   * Health check for Central Hub connectivity
   */
  async healthCheck() {
    try {
      const response = await this.client.get('/api/hub/health');
      return {
        connected: true,
        status: response.data,
        responseTime: response.headers['x-response-time'] || 'unknown'
      };
    } catch (error) {
      return {
        connected: false,
        error: error.message,
        timestamp: new Date().toISOString()
      };
    }
  }
}

// Export singleton instance
module.exports = new CentralHubService();