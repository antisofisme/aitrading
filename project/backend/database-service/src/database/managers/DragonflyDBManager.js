/**
 * DragonflyDB Cache/Memory Database Manager
 * High-performance Redis-compatible in-memory database
 */

const Redis = require('ioredis');
const IDatabaseManager = require('../interfaces/IDatabaseManager');
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'logs/dragonflydb.log' })
  ]
});

class DragonflyDBManager extends IDatabaseManager {
  constructor(config) {
    super();
    this.config = config;
    this.client = null;
    this.isConnected = false;
    this.connectionAttempts = 0;
    this.maxConnectionAttempts = 5;
  }

  async initialize() {
    try {
      this.client = new Redis({
        host: this.config.host,
        port: this.config.port,
        password: this.config.password,
        maxRetriesPerRequest: this.config.maxRetriesPerRequest || 3,
        retryDelayOnFailover: this.config.retryDelayOnFailover || 100,
        connectTimeout: 10000,
        lazyConnect: true,
        keepAlive: 30000,
        family: 4, // IPv4
      });

      // Test connection
      await this.testConnection();

      this.isConnected = true;
      logger.info('DragonflyDB connection established successfully', {
        host: this.config.host,
        port: this.config.port
      });

      // Set up event handlers
      this.client.on('error', (err) => {
        logger.error('DragonflyDB connection error:', err);
        this.isConnected = false;
      });

      this.client.on('connect', () => {
        logger.debug('DragonflyDB connected');
        this.isConnected = true;
      });

      this.client.on('ready', () => {
        logger.debug('DragonflyDB ready for commands');
        this.isConnected = true;
      });

      this.client.on('close', () => {
        logger.debug('DragonflyDB connection closed');
        this.isConnected = false;
      });

      return this.client;
    } catch (error) {
      logger.error('Failed to initialize DragonflyDB connection:', error);
      this.isConnected = false;
      throw error;
    }
  }

  async testConnection() {
    let lastError;
    for (let attempt = 1; attempt <= this.maxConnectionAttempts; attempt++) {
      try {
        await this.client.connect();
        const pong = await this.client.ping();
        const info = await this.client.info('server');

        logger.info('DragonflyDB connection test successful', {
          attempt,
          response: pong,
          serverInfo: info.split('\r\n')[1] // Get version line
        });
        return;
      } catch (error) {
        lastError = error;
        logger.warn(`DragonflyDB connection attempt ${attempt} failed:`, error.message);

        if (attempt < this.maxConnectionAttempts) {
          const delay = Math.pow(2, attempt) * 1000; // Exponential backoff
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }
    throw lastError;
  }

  async query(command, ...args) {
    if (!this.isConnected) {
      throw new Error('DragonflyDB not connected');
    }

    try {
      const start = Date.now();
      const result = await this.client[command.toLowerCase()](...args);
      const duration = Date.now() - start;

      logger.debug('DragonflyDB command executed', {
        command,
        args: args.length,
        duration,
        resultType: typeof result
      });

      return {
        result: result,
        command: command,
        duration
      };
    } catch (error) {
      logger.error('DragonflyDB command error:', {
        error: error.message,
        command,
        args: args.slice(0, 2) // Log first 2 args only for brevity
      });
      throw error;
    }
  }

  async getClient() {
    if (!this.isConnected) {
      throw new Error('DragonflyDB not connected');
    }
    return this.client;
  }

  async close() {
    if (this.client) {
      await this.client.quit();
      this.isConnected = false;
      logger.info('DragonflyDB connection closed');
    }
  }

  getStatus() {
    return {
      type: 'dragonflydb',
      connected: this.isConnected,
      config: {
        host: this.config.host,
        port: this.config.port,
        maxRetries: this.config.maxRetriesPerRequest,
        retryDelay: this.config.retryDelayOnFailover
      }
    };
  }

  async healthCheck() {
    try {
      const startTime = Date.now();
      const pong = await this.client.ping();
      const responseTime = Date.now() - startTime;

      const info = await this.client.info();
      const memoryInfo = await this.client.info('memory');

      return {
        status: 'healthy',
        responseTime,
        timestamp: new Date().toISOString(),
        details: {
          ping: pong,
          serverInfo: info.split('\r\n').slice(0, 5).join('\n'),
          memoryInfo: memoryInfo.split('\r\n').slice(0, 5).join('\n'),
          status: this.getStatus(),
          lastCheck: new Date().toISOString()
        }
      };
    } catch (error) {
      logger.error('DragonflyDB health check failed:', error);
      return {
        status: 'unhealthy',
        error: error.message,
        timestamp: new Date().toISOString()
      };
    }
  }

  getType() {
    return 'dragonflydb';
  }

  getConfig() {
    return { ...this.config, password: this.config.password ? '***' : undefined };
  }

  // DragonflyDB doesn't support traditional transactions, but supports MULTI/EXEC
  async beginTransaction() {
    const multi = this.client.multi();
    return multi;
  }

  async commitTransaction(multi) {
    try {
      const results = await multi.exec();
      logger.debug('DragonflyDB transaction committed');
      return results;
    } catch (error) {
      logger.error('Failed to commit DragonflyDB transaction:', error);
      throw error;
    }
  }

  async rollbackTransaction(multi) {
    try {
      await multi.discard();
      logger.debug('DragonflyDB transaction discarded');
    } catch (error) {
      logger.error('Failed to discard DragonflyDB transaction:', error);
      throw error;
    }
  }

  // DragonflyDB/Redis-specific methods

  // String operations
  async set(key, value, options = {}) {
    const args = [key, value];
    if (options.ex) args.push('EX', options.ex);
    if (options.px) args.push('PX', options.px);
    if (options.nx) args.push('NX');
    if (options.xx) args.push('XX');

    return await this.client.set(...args);
  }

  async get(key) {
    return await this.client.get(key);
  }

  async mget(...keys) {
    return await this.client.mget(...keys);
  }

  async mset(data) {
    const args = [];
    Object.entries(data).forEach(([key, value]) => {
      args.push(key, value);
    });
    return await this.client.mset(...args);
  }

  async del(...keys) {
    return await this.client.del(...keys);
  }

  async exists(...keys) {
    return await this.client.exists(...keys);
  }

  async expire(key, seconds) {
    return await this.client.expire(key, seconds);
  }

  async ttl(key) {
    return await this.client.ttl(key);
  }

  // Hash operations
  async hset(key, field, value) {
    return await this.client.hset(key, field, value);
  }

  async hget(key, field) {
    return await this.client.hget(key, field);
  }

  async hgetall(key) {
    return await this.client.hgetall(key);
  }

  async hmset(key, data) {
    return await this.client.hmset(key, data);
  }

  async hdel(key, ...fields) {
    return await this.client.hdel(key, ...fields);
  }

  async hkeys(key) {
    return await this.client.hkeys(key);
  }

  async hvals(key) {
    return await this.client.hvals(key);
  }

  // List operations
  async lpush(key, ...values) {
    return await this.client.lpush(key, ...values);
  }

  async rpush(key, ...values) {
    return await this.client.rpush(key, ...values);
  }

  async lpop(key, count = 1) {
    return await this.client.lpop(key, count);
  }

  async rpop(key, count = 1) {
    return await this.client.rpop(key, count);
  }

  async lrange(key, start, stop) {
    return await this.client.lrange(key, start, stop);
  }

  async llen(key) {
    return await this.client.llen(key);
  }

  // Set operations
  async sadd(key, ...members) {
    return await this.client.sadd(key, ...members);
  }

  async srem(key, ...members) {
    return await this.client.srem(key, ...members);
  }

  async smembers(key) {
    return await this.client.smembers(key);
  }

  async sismember(key, member) {
    return await this.client.sismember(key, member);
  }

  async scard(key) {
    return await this.client.scard(key);
  }

  // Sorted set operations
  async zadd(key, score, member, ...args) {
    return await this.client.zadd(key, score, member, ...args);
  }

  async zrem(key, ...members) {
    return await this.client.zrem(key, ...members);
  }

  async zrange(key, start, stop, withScores = false) {
    const args = [key, start, stop];
    if (withScores) args.push('WITHSCORES');
    return await this.client.zrange(...args);
  }

  async zrangebyscore(key, min, max, options = {}) {
    const args = [key, min, max];
    if (options.withScores) args.push('WITHSCORES');
    if (options.limit) args.push('LIMIT', options.limit.offset, options.limit.count);
    return await this.client.zrangebyscore(...args);
  }

  async zcard(key) {
    return await this.client.zcard(key);
  }

  async zscore(key, member) {
    return await this.client.zscore(key, member);
  }

  // Pub/Sub operations
  async publish(channel, message) {
    return await this.client.publish(channel, message);
  }

  async subscribe(...channels) {
    return await this.client.subscribe(...channels);
  }

  async unsubscribe(...channels) {
    return await this.client.unsubscribe(...channels);
  }

  // Cache-specific operations
  async setCache(key, value, ttl = 3600) {
    return await this.set(key, JSON.stringify(value), { ex: ttl });
  }

  async getCache(key) {
    const value = await this.get(key);
    try {
      return value ? JSON.parse(value) : null;
    } catch (error) {
      logger.warn('Failed to parse cached value:', error);
      return value;
    }
  }

  async invalidatePattern(pattern) {
    const keys = await this.client.keys(pattern);
    if (keys.length > 0) {
      return await this.del(...keys);
    }
    return 0;
  }

  async getMemoryUsage() {
    const info = await this.client.info('memory');
    const lines = info.split('\r\n');
    const memory = {};

    lines.forEach(line => {
      if (line.includes(':')) {
        const [key, value] = line.split(':');
        if (key.startsWith('used_memory')) {
          memory[key] = value;
        }
      }
    });

    return memory;
  }

  async flushdb() {
    return await this.client.flushdb();
  }

  async dbsize() {
    return await this.client.dbsize();
  }

  // Performance monitoring
  async slowlog(count = 10) {
    return await this.client.slowlog('get', count);
  }

  async clientList() {
    return await this.client.client('list');
  }

  async configGet(parameter) {
    return await this.client.config('get', parameter);
  }
}

module.exports = DragonflyDBManager;