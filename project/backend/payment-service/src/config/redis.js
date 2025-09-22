const Redis = require('ioredis');
const logger = require('./logger');

class RedisConnection {
  constructor() {
    this.redis = null;
    this.subscriber = null;
    this.isConnected = false;
  }

  connect() {
    try {
      const redisConfig = {
        host: process.env.REDIS_HOST || 'localhost',
        port: process.env.REDIS_PORT || 6379,
        password: process.env.REDIS_PASSWORD || null,
        db: process.env.REDIS_DB || 0,
        retryDelayOnFailover: 100,
        maxRetriesPerRequest: 3,
        lazyConnect: true
      };

      this.redis = new Redis(redisConfig);
      this.subscriber = new Redis(redisConfig);

      this.redis.on('connect', () => {
        logger.info('✅ Redis connected successfully', {
          service: 'payment-service',
          host: redisConfig.host,
          port: redisConfig.port
        });
        this.isConnected = true;
      });

      this.redis.on('error', (err) => {
        logger.error('❌ Redis connection error', { error: err.message });
        this.isConnected = false;
      });

      this.redis.on('close', () => {
        logger.warn('⚠️ Redis connection closed');
        this.isConnected = false;
      });

      return this.redis.connect();
    } catch (error) {
      logger.error('❌ Redis initialization failed', { error: error.message });
      throw error;
    }
  }

  getClient() {
    if (!this.redis) {
      throw new Error('Redis not initialized. Call connect() first.');
    }
    return this.redis;
  }

  getSubscriber() {
    if (!this.subscriber) {
      throw new Error('Redis subscriber not initialized. Call connect() first.');
    }
    return this.subscriber;
  }

  async disconnect() {
    try {
      if (this.redis) {
        await this.redis.quit();
      }
      if (this.subscriber) {
        await this.subscriber.quit();
      }
      this.isConnected = false;
      logger.info('📤 Redis disconnected gracefully');
    } catch (error) {
      logger.error('❌ Error disconnecting from Redis', { error: error.message });
      throw error;
    }
  }

  async setCache(key, value, ttl = 3600) {
    try {
      const client = this.getClient();
      if (ttl) {
        await client.setex(key, ttl, JSON.stringify(value));
      } else {
        await client.set(key, JSON.stringify(value));
      }
    } catch (error) {
      logger.error('❌ Redis SET error', { key, error: error.message });
      throw error;
    }
  }

  async getCache(key) {
    try {
      const client = this.getClient();
      const value = await client.get(key);
      return value ? JSON.parse(value) : null;
    } catch (error) {
      logger.error('❌ Redis GET error', { key, error: error.message });
      return null;
    }
  }

  async deleteCache(key) {
    try {
      const client = this.getClient();
      await client.del(key);
    } catch (error) {
      logger.error('❌ Redis DELETE error', { key, error: error.message });
      throw error;
    }
  }

  getConnectionStatus() {
    return {
      isConnected: this.isConnected,
      status: this.redis ? this.redis.status : 'not_initialized'
    };
  }
}

module.exports = new RedisConnection();