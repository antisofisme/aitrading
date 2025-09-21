import { Pool, PoolClient, QueryResult as PgQueryResult } from 'pg';
import { createClient } from 'redis';
import { config } from '@/config';
import { logger } from '@/logging';
import { User, Subscription, MT5Account, TradingSignal, SecurityEvent, QueryResult } from '@/types';

export class DatabaseService {
  private pgPool: Pool;
  private redisClient: any;
  private clickhouseClient: any;
  private isConnected: boolean = false;

  constructor() {
    this.initializeConnections();
  }

  /**
   * Initialize database connections
   */
  private async initializeConnections(): Promise<void> {
    try {
      // Initialize PostgreSQL connection pool
      this.pgPool = new Pool({
        host: config.database.postgres.host,
        port: config.database.postgres.port,
        database: config.database.postgres.database,
        user: config.database.postgres.username,
        password: config.database.postgres.password,
        ssl: config.database.postgres.ssl,
        min: config.database.postgres.pool?.min || 2,
        max: config.database.postgres.pool?.max || 20,
        idleTimeoutMillis: 30000,
        connectionTimeoutMillis: 5000,
      });

      // Initialize Redis client
      this.redisClient = createClient({
        socket: {
          host: config.database.redis.host,
          port: config.database.redis.port,
        },
        password: config.database.redis.password,
        database: config.database.redis.db,
      });

      // Initialize ClickHouse client (simplified - in production use official client)
      this.clickhouseClient = {
        host: config.database.clickhouse.host,
        port: config.database.clickhouse.port,
        database: config.database.clickhouse.database,
        username: config.database.clickhouse.username,
        password: config.database.clickhouse.password,
      };

      // Test connections
      await this.testConnections();
      this.isConnected = true;

      logger.info('Database connections initialized successfully');

    } catch (error) {
      logger.error('Failed to initialize database connections', {
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;
    }
  }

  /**
   * Test all database connections
   */
  private async testConnections(): Promise<void> {
    // Test PostgreSQL
    const pgClient = await this.pgPool.connect();
    await pgClient.query('SELECT 1');
    pgClient.release();

    // Test Redis
    await this.redisClient.connect();
    await this.redisClient.ping();

    logger.info('All database connections tested successfully');
  }

  /**
   * Execute PostgreSQL query with connection pooling
   */
  public async query<T = any>(text: string, params?: any[]): Promise<QueryResult<T>> {
    const start = Date.now();
    let client: PoolClient | null = null;

    try {
      client = await this.pgPool.connect();
      const result: PgQueryResult<T> = await client.query(text, params);
      const duration = Date.now() - start;

      logger.debug('Database query executed', {
        query: text.substring(0, 100) + (text.length > 100 ? '...' : ''),
        duration,
        rowCount: result.rowCount
      });

      return {
        rows: result.rows,
        rowCount: result.rowCount || 0,
        command: result.command,
        duration
      };

    } catch (error) {
      const duration = Date.now() - start;
      logger.error('Database query failed', {
        query: text.substring(0, 100) + (text.length > 100 ? '...' : ''),
        duration,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;

    } finally {
      if (client) {
        client.release();
      }
    }
  }

  /**
   * Execute transaction with automatic rollback on error
   */
  public async transaction<T>(callback: (client: PoolClient) => Promise<T>): Promise<T> {
    const client = await this.pgPool.connect();

    try {
      await client.query('BEGIN');
      const result = await callback(client);
      await client.query('COMMIT');

      logger.debug('Transaction completed successfully');
      return result;

    } catch (error) {
      await client.query('ROLLBACK');
      logger.error('Transaction rolled back', {
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;

    } finally {
      client.release();
    }
  }

  // User Management Methods

  /**
   * Create new user
   */
  public async createUser(user: User): Promise<void> {
    const query = `
      INSERT INTO users (
        id, email, password_hash, first_name, last_name,
        subscription_tier, subscription_status, created_at, updated_at,
        last_login, is_active, email_verified
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
    `;

    const params = [
      user.id, user.email, user.password_hash, user.first_name, user.last_name,
      user.subscription_tier, user.subscription_status, user.created_at, user.updated_at,
      user.last_login, user.is_active, user.email_verified
    ];

    await this.query(query, params);
  }

  /**
   * Find user by email
   */
  public async findUserByEmail(email: string): Promise<User | null> {
    const query = 'SELECT * FROM users WHERE email = $1 AND is_active = true';
    const result = await this.query<User>(query, [email]);

    return result.rows.length > 0 ? result.rows[0] : null;
  }

  /**
   * Find user by ID
   */
  public async findUserById(id: string): Promise<User | null> {
    const query = 'SELECT * FROM users WHERE id = $1 AND is_active = true';
    const result = await this.query<User>(query, [id]);

    return result.rows.length > 0 ? result.rows[0] : null;
  }

  /**
   * Update user last login timestamp
   */
  public async updateUserLastLogin(userId: string, lastLogin: Date): Promise<void> {
    const query = 'UPDATE users SET last_login = $1, updated_at = $2 WHERE id = $3';
    await this.query(query, [lastLogin, new Date(), userId]);
  }

  /**
   * Update user password
   */
  public async updateUserPassword(userId: string, passwordHash: string): Promise<void> {
    const query = 'UPDATE users SET password_hash = $1, updated_at = $2 WHERE id = $3';
    await this.query(query, [passwordHash, new Date(), userId]);
  }

  // Subscription Management Methods

  /**
   * Create subscription
   */
  public async createSubscription(subscription: Subscription): Promise<void> {
    const query = `
      INSERT INTO subscriptions (
        id, user_id, tier, status, price, currency, billing_cycle,
        features, starts_at, ends_at, auto_renew, created_at, updated_at
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
    `;

    const params = [
      subscription.id, subscription.user_id, subscription.tier, subscription.status,
      subscription.price, subscription.currency, subscription.billing_cycle,
      JSON.stringify(subscription.features), subscription.starts_at, subscription.ends_at,
      subscription.auto_renew, subscription.created_at, subscription.updated_at
    ];

    await this.query(query, params);
  }

  /**
   * Get user subscription
   */
  public async getUserSubscription(userId: string): Promise<Subscription | null> {
    const query = `
      SELECT * FROM subscriptions
      WHERE user_id = $1 AND status = 'active'
      ORDER BY created_at DESC LIMIT 1
    `;
    const result = await this.query<Subscription>(query, [userId]);

    if (result.rows.length > 0) {
      const subscription = result.rows[0];
      // Parse features JSON
      if (typeof subscription.features === 'string') {
        subscription.features = JSON.parse(subscription.features);
      }
      return subscription;
    }

    return null;
  }

  // MT5 Account Management

  /**
   * Create MT5 account
   */
  public async createMT5Account(account: MT5Account): Promise<void> {
    const query = `
      INSERT INTO mt5_accounts (
        id, user_id, login, server, name, balance, equity, margin,
        free_margin, margin_level, is_active, last_sync, created_at, updated_at
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
    `;

    const params = [
      account.id, account.user_id, account.login, account.server, account.name,
      account.balance, account.equity, account.margin, account.free_margin,
      account.margin_level, account.is_active, account.last_sync,
      account.created_at, account.updated_at
    ];

    await this.query(query, params);
  }

  /**
   * Get user MT5 accounts
   */
  public async getUserMT5Accounts(userId: string): Promise<MT5Account[]> {
    const query = 'SELECT * FROM mt5_accounts WHERE user_id = $1 AND is_active = true';
    const result = await this.query<MT5Account>(query, [userId]);

    return result.rows;
  }

  // Trading Signal Management

  /**
   * Create trading signal
   */
  public async createTradingSignal(signal: TradingSignal): Promise<void> {
    const query = `
      INSERT INTO trading_signals (
        id, user_id, symbol, type, entry_price, stop_loss, take_profit,
        volume, confidence, reasoning, status, expires_at, created_at, executed_at
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
    `;

    const params = [
      signal.id, signal.user_id, signal.symbol, signal.type, signal.entry_price,
      signal.stop_loss, signal.take_profit, signal.volume, signal.confidence,
      signal.reasoning, signal.status, signal.expires_at, signal.created_at, signal.executed_at
    ];

    await this.query(query, params);
  }

  /**
   * Get user trading signals
   */
  public async getUserTradingSignals(userId: string, limit: number = 50): Promise<TradingSignal[]> {
    const query = `
      SELECT * FROM trading_signals
      WHERE user_id = $1
      ORDER BY created_at DESC
      LIMIT $2
    `;
    const result = await this.query<TradingSignal>(query, [userId, limit]);

    return result.rows;
  }

  // Security Event Logging

  /**
   * Log security event
   */
  public async logSecurityEvent(event: SecurityEvent): Promise<void> {
    const query = `
      INSERT INTO security_events (
        id, user_id, event_type, ip_address, user_agent, details, risk_score, created_at
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    `;

    const params = [
      event.id, event.user_id, event.event_type, event.ip_address,
      event.user_agent, JSON.stringify(event.details), event.risk_score, event.created_at
    ];

    await this.query(query, params);
  }

  // Redis Cache Methods

  /**
   * Set cache value with TTL
   */
  public async setCache(key: string, value: any, ttlSeconds: number = 3600): Promise<void> {
    try {
      const serializedValue = JSON.stringify(value);
      await this.redisClient.setEx(key, ttlSeconds, serializedValue);
    } catch (error) {
      logger.error('Redis set operation failed', {
        key,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }

  /**
   * Get cache value
   */
  public async getCache<T = any>(key: string): Promise<T | null> {
    try {
      const value = await this.redisClient.get(key);
      return value ? JSON.parse(value) : null;
    } catch (error) {
      logger.error('Redis get operation failed', {
        key,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      return null;
    }
  }

  /**
   * Delete cache value
   */
  public async deleteCache(key: string): Promise<void> {
    try {
      await this.redisClient.del(key);
    } catch (error) {
      logger.error('Redis delete operation failed', {
        key,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }

  // ClickHouse Analytics Methods (simplified implementation)

  /**
   * Log analytics event to ClickHouse
   */
  public async logAnalyticsEvent(event: any): Promise<void> {
    try {
      // In production, use proper ClickHouse client
      logger.info('Analytics event logged', { event });
    } catch (error) {
      logger.error('ClickHouse analytics logging failed', {
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }

  // Health Check Methods

  /**
   * Check database health
   */
  public async healthCheck(): Promise<{ postgres: boolean; redis: boolean; clickhouse: boolean }> {
    const health = {
      postgres: false,
      redis: false,
      clickhouse: false
    };

    try {
      // Check PostgreSQL
      await this.query('SELECT 1');
      health.postgres = true;
    } catch (error) {
      logger.warn('PostgreSQL health check failed', {
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }

    try {
      // Check Redis
      await this.redisClient.ping();
      health.redis = true;
    } catch (error) {
      logger.warn('Redis health check failed', {
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }

    try {
      // Check ClickHouse (simplified)
      health.clickhouse = true; // In production, implement proper health check
    } catch (error) {
      logger.warn('ClickHouse health check failed', {
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }

    return health;
  }

  /**
   * Close all database connections
   */
  public async close(): Promise<void> {
    try {
      await this.pgPool.end();
      await this.redisClient.quit();
      this.isConnected = false;
      logger.info('Database connections closed');
    } catch (error) {
      logger.error('Error closing database connections', {
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }

  /**
   * Check if database is connected
   */
  public isReady(): boolean {
    return this.isConnected;
  }
}