/**
 * Redis Manager
 * Redis connection and cache management
 */

import Redis from 'ioredis';
import logger from './logger.js';

export class RedisManager {
  constructor(config = {}) {
    this.config = {
      host: config.host || process.env.REDIS_HOST || 'localhost',
      port: config.port || process.env.REDIS_PORT || 6379,
      password: config.password || process.env.REDIS_PASSWORD,
      db: config.db || process.env.REDIS_DB || 0,
      keyPrefix: config.keyPrefix || 'chain-debug:',
      retryDelayOnFailover: 100,
      enableReadyCheck: false,
      maxRetriesPerRequest: null,
      lazyConnect: true
    };

    this.redis = null;
    this.isConnected = false;
  }

  async connect() {
    try {
      logger.info('Connecting to Redis...');

      this.redis = new Redis(this.config);

      // Event handlers
      this.redis.on('connect', () => {
        logger.info('Redis connected');
        this.isConnected = true;
      });

      this.redis.on('ready', () => {
        logger.info('Redis ready');
      });

      this.redis.on('error', (error) => {
        logger.error('Redis error:', error);
        this.isConnected = false;
      });

      this.redis.on('close', () => {
        logger.warn('Redis connection closed');
        this.isConnected = false;
      });

      this.redis.on('reconnecting', () => {
        logger.info('Redis reconnecting...');
      });

      // Test connection
      await this.redis.ping();

      logger.info('Redis connected successfully');

    } catch (error) {
      logger.error('Failed to connect to Redis:', error);
      throw error;
    }
  }

  async disconnect() {
    try {
      if (this.redis) {
        await this.redis.quit();
        this.isConnected = false;
        logger.info('Redis disconnected');
      }
    } catch (error) {
      logger.error('Error disconnecting from Redis:', error);
    }
  }

  // Basic Redis operations
  async get(key) {
    try {
      return await this.redis.get(key);
    } catch (error) {
      logger.error(`Redis GET failed for key ${key}:`, error);
      return null;
    }
  }

  async set(key, value, expiry = null) {
    try {
      if (expiry) {
        return await this.redis.setex(key, expiry, value);
      } else {
        return await this.redis.set(key, value);
      }
    } catch (error) {
      logger.error(`Redis SET failed for key ${key}:`, error);
      return null;
    }
  }

  async setex(key, expiry, value) {
    return this.set(key, value, expiry);
  }

  async del(key) {
    try {
      return await this.redis.del(key);
    } catch (error) {
      logger.error(`Redis DEL failed for key ${key}:`, error);
      return 0;
    }
  }

  async exists(key) {
    try {
      return await this.redis.exists(key);
    } catch (error) {
      logger.error(`Redis EXISTS failed for key ${key}:`, error);
      return 0;
    }
  }

  async expire(key, seconds) {
    try {
      return await this.redis.expire(key, seconds);
    } catch (error) {
      logger.error(`Redis EXPIRE failed for key ${key}:`, error);
      return 0;
    }
  }

  // Hash operations
  async hset(key, field, value) {
    try {
      return await this.redis.hset(key, field, value);
    } catch (error) {
      logger.error(`Redis HSET failed for key ${key}:`, error);
      return 0;
    }
  }

  async hget(key, field) {
    try {
      return await this.redis.hget(key, field);
    } catch (error) {
      logger.error(`Redis HGET failed for key ${key}:`, error);
      return null;
    }
  }

  async hgetall(key) {
    try {
      return await this.redis.hgetall(key);
    } catch (error) {
      logger.error(`Redis HGETALL failed for key ${key}:`, error);
      return {};
    }
  }

  async hdel(key, field) {
    try {
      return await this.redis.hdel(key, field);
    } catch (error) {
      logger.error(`Redis HDEL failed for key ${key}:`, error);
      return 0;
    }
  }

  // List operations
  async lpush(key, value) {
    try {
      return await this.redis.lpush(key, value);
    } catch (error) {
      logger.error(`Redis LPUSH failed for key ${key}:`, error);
      return 0;
    }
  }

  async rpush(key, value) {
    try {
      return await this.redis.rpush(key, value);
    } catch (error) {
      logger.error(`Redis RPUSH failed for key ${key}:`, error);
      return 0;
    }
  }

  async lpop(key) {
    try {
      return await this.redis.lpop(key);
    } catch (error) {
      logger.error(`Redis LPOP failed for key ${key}:`, error);
      return null;
    }
  }

  async rpop(key) {
    try {
      return await this.redis.rpop(key);
    } catch (error) {
      logger.error(`Redis RPOP failed for key ${key}:`, error);
      return null;
    }
  }

  async lrange(key, start, stop) {
    try {
      return await this.redis.lrange(key, start, stop);
    } catch (error) {
      logger.error(`Redis LRANGE failed for key ${key}:`, error);
      return [];
    }
  }

  async llen(key) {
    try {
      return await this.redis.llen(key);
    } catch (error) {
      logger.error(`Redis LLEN failed for key ${key}:`, error);
      return 0;
    }
  }

  // Set operations
  async sadd(key, member) {
    try {
      return await this.redis.sadd(key, member);
    } catch (error) {
      logger.error(`Redis SADD failed for key ${key}:`, error);
      return 0;
    }
  }

  async smembers(key) {
    try {
      return await this.redis.smembers(key);
    } catch (error) {
      logger.error(`Redis SMEMBERS failed for key ${key}:`, error);
      return [];
    }
  }

  async sismember(key, member) {
    try {
      return await this.redis.sismember(key, member);
    } catch (error) {
      logger.error(`Redis SISMEMBER failed for key ${key}:`, error);
      return 0;
    }
  }

  async srem(key, member) {
    try {
      return await this.redis.srem(key, member);
    } catch (error) {
      logger.error(`Redis SREM failed for key ${key}:`, error);
      return 0;
    }
  }

  // Sorted set operations
  async zadd(key, score, member) {
    try {
      return await this.redis.zadd(key, score, member);
    } catch (error) {
      logger.error(`Redis ZADD failed for key ${key}:`, error);
      return 0;
    }
  }

  async zrange(key, start, stop, withScores = false) {
    try {
      if (withScores) {
        return await this.redis.zrange(key, start, stop, 'WITHSCORES');
      } else {
        return await this.redis.zrange(key, start, stop);
      }
    } catch (error) {
      logger.error(`Redis ZRANGE failed for key ${key}:`, error);
      return [];
    }
  }

  async zrem(key, member) {
    try {
      return await this.redis.zrem(key, member);
    } catch (error) {
      logger.error(`Redis ZREM failed for key ${key}:`, error);
      return 0;
    }
  }

  // JSON operations (if Redis JSON module is available)
  async jsonSet(key, path, value) {
    try {
      return await this.redis.call('JSON.SET', key, path, JSON.stringify(value));
    } catch (error) {
      // Fallback to regular string set
      if (path === '$') {
        return await this.set(key, JSON.stringify(value));
      }
      logger.error(`Redis JSON.SET failed for key ${key}:`, error);
      return null;
    }
  }

  async jsonGet(key, path = '$') {
    try {
      const result = await this.redis.call('JSON.GET', key, path);
      return result ? JSON.parse(result) : null;
    } catch (error) {
      // Fallback to regular string get
      if (path === '$') {
        const value = await this.get(key);
        return value ? JSON.parse(value) : null;
      }
      logger.error(`Redis JSON.GET failed for key ${key}:`, error);
      return null;
    }
  }

  // Cache management utilities
  async cacheResult(key, data, expiry = 300) {
    const serialized = JSON.stringify(data);
    return await this.setex(key, expiry, serialized);
  }

  async getCachedResult(key) {
    const cached = await this.get(key);
    return cached ? JSON.parse(cached) : null;
  }

  async invalidatePattern(pattern) {
    try {
      const keys = await this.redis.keys(pattern);
      if (keys.length > 0) {
        return await this.redis.del(...keys);
      }
      return 0;
    } catch (error) {
      logger.error(`Failed to invalidate pattern ${pattern}:`, error);
      return 0;
    }
  }

  // Lock utilities
  async acquireLock(lockKey, expiry = 30, timeout = 10000) {
    const lockValue = `${Date.now()}-${Math.random()}`;
    const start = Date.now();

    while (Date.now() - start < timeout) {
      const result = await this.redis.set(lockKey, lockValue, 'EX', expiry, 'NX');
      if (result === 'OK') {
        return { acquired: true, lockValue };
      }

      // Wait a bit before retrying
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    return { acquired: false, lockValue: null };
  }

  async releaseLock(lockKey, lockValue) {
    const script = `
      if redis.call("GET", KEYS[1]) == ARGV[1] then
        return redis.call("DEL", KEYS[1])
      else
        return 0
      end
    `;

    try {
      return await this.redis.eval(script, 1, lockKey, lockValue);
    } catch (error) {
      logger.error(`Failed to release lock ${lockKey}:`, error);
      return 0;
    }
  }

  // Health check
  async healthCheck() {
    try {
      const start = Date.now();
      await this.redis.ping();
      const latency = Date.now() - start;

      const info = await this.redis.info('memory');
      const memoryUsage = this.parseRedisInfo(info);

      return {
        connected: true,
        latency,
        memoryUsage: memoryUsage.used_memory_human,
        keyspaceHits: memoryUsage.keyspace_hits,
        keyspaceMisses: memoryUsage.keyspace_misses
      };
    } catch (error) {
      return {
        connected: false,
        error: error.message
      };
    }
  }

  parseRedisInfo(info) {
    const lines = info.split('\r\n');
    const parsed = {};

    for (const line of lines) {
      if (line && !line.startsWith('#')) {
        const [key, value] = line.split(':');
        if (key && value !== undefined) {
          // Try to parse as number
          const numValue = Number(value);
          parsed[key] = isNaN(numValue) ? value : numValue;
        }
      }
    }

    return parsed;
  }

  // Pub/Sub utilities
  async publish(channel, message) {
    try {
      const serialized = typeof message === 'string' ? message : JSON.stringify(message);
      return await this.redis.publish(channel, serialized);
    } catch (error) {
      logger.error(`Failed to publish to channel ${channel}:`, error);
      return 0;
    }
  }

  async subscribe(channel, callback) {
    try {
      const subscriber = this.redis.duplicate();

      subscriber.on('message', (receivedChannel, message) => {
        if (receivedChannel === channel) {
          try {
            const parsed = JSON.parse(message);
            callback(parsed);
          } catch (error) {
            callback(message);
          }
        }
      });

      await subscriber.subscribe(channel);
      return subscriber;
    } catch (error) {
      logger.error(`Failed to subscribe to channel ${channel}:`, error);
      return null;
    }
  }

  // Pipeline operations for bulk operations
  pipeline() {
    return this.redis.pipeline();
  }

  async executePipeline(pipeline) {
    try {
      return await pipeline.exec();
    } catch (error) {
      logger.error('Pipeline execution failed:', error);
      return [];
    }
  }

  // Utility methods
  buildKey(...parts) {
    return parts.filter(part => part != null).join(':');
  }

  async flushAll() {
    try {
      return await this.redis.flushall();
    } catch (error) {
      logger.error('Failed to flush all keys:', error);
      return 'ERROR';
    }
  }

  async keys(pattern) {
    try {
      return await this.redis.keys(pattern);
    } catch (error) {
      logger.error(`Failed to get keys for pattern ${pattern}:`, error);
      return [];
    }
  }
}