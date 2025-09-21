import { api } from './api';

// Memory key patterns for different data types
export const MEMORY_KEYS = {
  // User sessions and preferences
  USER_SESSION: (userId: string) => `session:user:${userId}`,
  USER_PREFERENCES: (userId: string) => `preferences:user:${userId}`,
  USER_DASHBOARD_LAYOUT: (userId: string) => `dashboard:layout:${userId}`,

  // Trading data
  TRADING_POSITIONS: (userId: string) => `trading:positions:${userId}`,
  TRADING_HISTORY: (userId: string) => `trading:history:${userId}`,
  TRADING_WATCHLIST: (userId: string) => `trading:watchlist:${userId}`,

  // AI/ML predictions and insights
  AI_PREDICTIONS: (symbol: string, timeframe: string) => `ai:predictions:${symbol}:${timeframe}`,
  AI_MARKET_REGIME: () => 'ai:market_regime:current',
  AI_SENTIMENT: (symbol: string) => `ai:sentiment:${symbol}`,

  // Real-time market data
  MARKET_PRICES: (symbol: string) => `market:prices:${symbol}`,
  MARKET_NEWS: () => 'market:news:latest',

  // Collaborative coordination
  BACKEND_STATUS: () => 'backend:status',
  BACKEND_COORDINATION: (service: string) => `backend:coordination:${service}`,
  SWARM_STATE: (swarmId: string) => `swarm:state:${swarmId}`,

  // Performance metrics
  PERFORMANCE_METRICS: (userId: string) => `performance:metrics:${userId}`,
  SYSTEM_METRICS: () => 'system:metrics:current',

  // Tenant configuration
  TENANT_CONFIG: (tenantId: string) => `tenant:config:${tenantId}`,
  TENANT_BRANDING: (tenantId: string) => `tenant:branding:${tenantId}`,
} as const;

// Memory service for collaborative backend coordination
class MemoryService {
  private cache = new Map<string, { data: any; timestamp: number; ttl: number }>();
  private readonly defaultTTL = 5 * 60 * 1000; // 5 minutes

  // Store data in memory with TTL
  async store(key: string, data: any, ttl: number = this.defaultTTL): Promise<void> {
    try {
      // Store in local cache
      this.cache.set(key, {
        data,
        timestamp: Date.now(),
        ttl,
      });

      // Store in backend memory for coordination
      await api.post('/api/memory/store', {
        key,
        data,
        ttl,
        clientId: this.getClientId(),
        timestamp: Date.now(),
      });
    } catch (error) {
      console.error('Failed to store in memory:', error);
      // Continue with local cache only if backend fails
    }
  }

  // Retrieve data from memory
  async retrieve(key: string): Promise<any> {
    try {
      // Check local cache first
      const cached = this.cache.get(key);
      if (cached && this.isValid(cached)) {
        return cached.data;
      }

      // Fetch from backend memory
      const response = await api.get(`/api/memory/retrieve/${encodeURIComponent(key)}`);

      if (response.success && response.data) {
        // Update local cache
        this.cache.set(key, {
          data: response.data.value,
          timestamp: Date.now(),
          ttl: response.data.ttl || this.defaultTTL,
        });

        return response.data.value;
      }

      return null;
    } catch (error) {
      console.error('Failed to retrieve from memory:', error);

      // Fall back to local cache
      const cached = this.cache.get(key);
      return cached?.data || null;
    }
  }

  // Update existing data in memory
  async update(key: string, updateFn: (existing: any) => any, ttl?: number): Promise<any> {
    try {
      const existing = await this.retrieve(key);
      const updated = updateFn(existing);

      await this.store(key, updated, ttl);
      return updated;
    } catch (error) {
      console.error('Failed to update memory:', error);
      throw error;
    }
  }

  // Delete data from memory
  async delete(key: string): Promise<void> {
    try {
      // Remove from local cache
      this.cache.delete(key);

      // Delete from backend memory
      await api.delete(`/api/memory/delete/${encodeURIComponent(key)}`);
    } catch (error) {
      console.error('Failed to delete from memory:', error);
    }
  }

  // Search for keys by pattern
  async search(pattern: string): Promise<string[]> {
    try {
      const response = await api.get(`/api/memory/search?pattern=${encodeURIComponent(pattern)}`);

      if (response.success && response.data) {
        return response.data.keys;
      }

      return [];
    } catch (error) {
      console.error('Failed to search memory:', error);
      return [];
    }
  }

  // Bulk operations for efficiency
  async bulkStore(items: { key: string; data: any; ttl?: number }[]): Promise<void> {
    try {
      // Update local cache
      items.forEach(item => {
        this.cache.set(item.key, {
          data: item.data,
          timestamp: Date.now(),
          ttl: item.ttl || this.defaultTTL,
        });
      });

      // Bulk store in backend
      await api.post('/api/memory/bulk-store', {
        items: items.map(item => ({
          ...item,
          ttl: item.ttl || this.defaultTTL,
        })),
        clientId: this.getClientId(),
        timestamp: Date.now(),
      });
    } catch (error) {
      console.error('Failed to bulk store in memory:', error);
    }
  }

  async bulkRetrieve(keys: string[]): Promise<{ [key: string]: any }> {
    try {
      const response = await api.post('/api/memory/bulk-retrieve', {
        keys,
        clientId: this.getClientId(),
      });

      if (response.success && response.data) {
        // Update local cache with retrieved data
        Object.entries(response.data).forEach(([key, value]: [string, any]) => {
          if (value !== null) {
            this.cache.set(key, {
              data: value,
              timestamp: Date.now(),
              ttl: this.defaultTTL,
            });
          }
        });

        return response.data;
      }

      return {};
    } catch (error) {
      console.error('Failed to bulk retrieve from memory:', error);

      // Fall back to local cache
      const result: { [key: string]: any } = {};
      keys.forEach(key => {
        const cached = this.cache.get(key);
        if (cached && this.isValid(cached)) {
          result[key] = cached.data;
        }
      });

      return result;
    }
  }

  // Coordination methods for backend services
  async coordinateWithBackend(service: string, data: any): Promise<void> {
    const key = MEMORY_KEYS.BACKEND_COORDINATION(service);

    await this.store(key, {
      service,
      data,
      clientId: this.getClientId(),
      timestamp: Date.now(),
      coordination: true,
    }, 2 * 60 * 1000); // 2 minutes TTL for coordination
  }

  async getBackendCoordination(service: string): Promise<any> {
    const key = MEMORY_KEYS.BACKEND_COORDINATION(service);
    return await this.retrieve(key);
  }

  // Swarm state coordination
  async updateSwarmState(swarmId: string, state: any): Promise<void> {
    const key = MEMORY_KEYS.SWARM_STATE(swarmId);

    await this.store(key, {
      swarmId,
      state,
      clientId: this.getClientId(),
      timestamp: Date.now(),
    }, 10 * 60 * 1000); // 10 minutes TTL
  }

  async getSwarmState(swarmId: string): Promise<any> {
    const key = MEMORY_KEYS.SWARM_STATE(swarmId);
    return await this.retrieve(key);
  }

  // Real-time data synchronization
  async syncRealTimeData(dataType: string, symbol: string, data: any): Promise<void> {
    const key = `realtime:${dataType}:${symbol}`;

    await this.store(key, {
      symbol,
      data,
      timestamp: Date.now(),
      realtime: true,
    }, 30 * 1000); // 30 seconds TTL for real-time data
  }

  async getRealTimeData(dataType: string, symbol: string): Promise<any> {
    const key = `realtime:${dataType}:${symbol}`;
    return await this.retrieve(key);
  }

  // Session management
  async storeUserSession(userId: string, sessionData: any): Promise<void> {
    const key = MEMORY_KEYS.USER_SESSION(userId);

    await this.store(key, {
      userId,
      sessionData,
      timestamp: Date.now(),
    }, 24 * 60 * 60 * 1000); // 24 hours TTL
  }

  async getUserSession(userId: string): Promise<any> {
    const key = MEMORY_KEYS.USER_SESSION(userId);
    return await this.retrieve(key);
  }

  // Performance tracking
  async trackPerformance(metric: string, value: number, tags?: any): Promise<void> {
    const key = `performance:${metric}:${Date.now()}`;

    await this.store(key, {
      metric,
      value,
      tags,
      timestamp: Date.now(),
      clientId: this.getClientId(),
    }, 60 * 60 * 1000); // 1 hour TTL
  }

  // Utility methods
  private isValid(cached: { timestamp: number; ttl: number }): boolean {
    return Date.now() - cached.timestamp < cached.ttl;
  }

  private getClientId(): string {
    let clientId = localStorage.getItem('clientId');
    if (!clientId) {
      clientId = `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('clientId', clientId);
    }
    return clientId;
  }

  // Cleanup expired cache entries
  private cleanupCache(): void {
    const now = Date.now();

    for (const [key, cached] of this.cache.entries()) {
      if (!this.isValid(cached)) {
        this.cache.delete(key);
      }
    }
  }

  // Start automatic cache cleanup
  startCleanup(): void {
    setInterval(() => {
      this.cleanupCache();
    }, 5 * 60 * 1000); // Cleanup every 5 minutes
  }

  // Get cache statistics
  getCacheStats(): { size: number; keys: string[] } {
    return {
      size: this.cache.size,
      keys: Array.from(this.cache.keys()),
    };
  }
}

// Create singleton instance
export const memoryService = new MemoryService();

// Start automatic cleanup
memoryService.startCleanup();

// React hook for using memory service
export const useMemory = () => {
  return {
    store: memoryService.store.bind(memoryService),
    retrieve: memoryService.retrieve.bind(memoryService),
    update: memoryService.update.bind(memoryService),
    delete: memoryService.delete.bind(memoryService),
    search: memoryService.search.bind(memoryService),
    bulkStore: memoryService.bulkStore.bind(memoryService),
    bulkRetrieve: memoryService.bulkRetrieve.bind(memoryService),
    coordinateWithBackend: memoryService.coordinateWithBackend.bind(memoryService),
    getBackendCoordination: memoryService.getBackendCoordination.bind(memoryService),
    updateSwarmState: memoryService.updateSwarmState.bind(memoryService),
    getSwarmState: memoryService.getSwarmState.bind(memoryService),
    syncRealTimeData: memoryService.syncRealTimeData.bind(memoryService),
    getRealTimeData: memoryService.getRealTimeData.bind(memoryService),
    storeUserSession: memoryService.storeUserSession.bind(memoryService),
    getUserSession: memoryService.getUserSession.bind(memoryService),
    trackPerformance: memoryService.trackPerformance.bind(memoryService),
    getCacheStats: memoryService.getCacheStats.bind(memoryService),
  };
};

// Specialized hooks for specific use cases
export const useUserMemory = (userId: string) => {
  const memory = useMemory();

  return {
    storePreferences: (prefs: any) => memory.store(MEMORY_KEYS.USER_PREFERENCES(userId), prefs),
    getPreferences: () => memory.retrieve(MEMORY_KEYS.USER_PREFERENCES(userId)),
    storeDashboardLayout: (layout: any) => memory.store(MEMORY_KEYS.USER_DASHBOARD_LAYOUT(userId), layout),
    getDashboardLayout: () => memory.retrieve(MEMORY_KEYS.USER_DASHBOARD_LAYOUT(userId)),
    storeSession: (sessionData: any) => memory.storeUserSession(userId, sessionData),
    getSession: () => memory.getUserSession(userId),
  };
};

export const useTradingMemory = (userId: string) => {
  const memory = useMemory();

  return {
    storePositions: (positions: any) => memory.store(MEMORY_KEYS.TRADING_POSITIONS(userId), positions),
    getPositions: () => memory.retrieve(MEMORY_KEYS.TRADING_POSITIONS(userId)),
    storeHistory: (history: any) => memory.store(MEMORY_KEYS.TRADING_HISTORY(userId), history),
    getHistory: () => memory.retrieve(MEMORY_KEYS.TRADING_HISTORY(userId)),
    storeWatchlist: (watchlist: any) => memory.store(MEMORY_KEYS.TRADING_WATCHLIST(userId), watchlist),
    getWatchlist: () => memory.retrieve(MEMORY_KEYS.TRADING_WATCHLIST(userId)),
  };
};

export const useAIMemory = () => {
  const memory = useMemory();

  return {
    storePrediction: (symbol: string, timeframe: string, prediction: any) =>
      memory.store(MEMORY_KEYS.AI_PREDICTIONS(symbol, timeframe), prediction, 4 * 60 * 60 * 1000), // 4 hours
    getPrediction: (symbol: string, timeframe: string) =>
      memory.retrieve(MEMORY_KEYS.AI_PREDICTIONS(symbol, timeframe)),
    storeMarketRegime: (regime: any) =>
      memory.store(MEMORY_KEYS.AI_MARKET_REGIME(), regime, 30 * 60 * 1000), // 30 minutes
    getMarketRegime: () =>
      memory.retrieve(MEMORY_KEYS.AI_MARKET_REGIME()),
    storeSentiment: (symbol: string, sentiment: any) =>
      memory.store(MEMORY_KEYS.AI_SENTIMENT(symbol), sentiment, 15 * 60 * 1000), // 15 minutes
    getSentiment: (symbol: string) =>
      memory.retrieve(MEMORY_KEYS.AI_SENTIMENT(symbol)),
  };
};

export const useBackendCoordination = () => {
  const memory = useMemory();

  return {
    coordinate: memory.coordinateWithBackend,
    getCoordination: memory.getBackendCoordination,
    updateSwarmState: memory.updateSwarmState,
    getSwarmState: memory.getSwarmState,
    trackPerformance: memory.trackPerformance,
  };
};

// Export everything
export { memoryService as default };
export default memoryService;