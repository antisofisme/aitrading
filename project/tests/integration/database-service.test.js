/**
 * Database Service Integration Tests
 * Tests multi-database operations and routing through Database Service
 */

const { expect } = require('chai');
const axios = require('axios');
const { Pool } = require('pg');
const mongoose = require('mongoose');
const Redis = require('ioredis');
const { MongoMemoryServer } = require('mongodb-memory-server');

describe('Database Service Integration Tests', () => {
  let databaseServiceUrl;
  let pgPool;
  let mongoServer;
  let redisClient;
  const testDatabases = {
    postgres: null,
    mongodb: null,
    redis: null
  };

  before(async function() {
    this.timeout(30000);
    
    databaseServiceUrl = process.env.DATABASE_SERVICE_URL || 'http://localhost:3002';
    
    // Setup test databases
    await setupTestDatabases();
    
    console.log('Database Service and test databases ready');
  });

  after(async function() {
    this.timeout(10000);
    
    // Cleanup test databases
    await cleanupTestDatabases();
  });

  describe('PostgreSQL Operations', () => {
    it('should create a new table', async () => {
      const createTableRequest = {
        database: 'postgres',
        operation: 'createTable',
        tableName: 'test_users',
        schema: {
          id: { type: 'SERIAL', primaryKey: true },
          username: { type: 'VARCHAR(50)', unique: true, notNull: true },
          email: { type: 'VARCHAR(100)', unique: true, notNull: true },
          created_at: { type: 'TIMESTAMP', default: 'CURRENT_TIMESTAMP' },
          metadata: { type: 'JSONB' }
        }
      };

      const response = await axios.post(
        `${databaseServiceUrl}/api/database/execute`,
        createTableRequest
      );

      expect(response.status).to.equal(200);
      expect(response.data.success).to.be.true;
      expect(response.data.result).to.include('CREATE TABLE');
    });

    it('should insert data into PostgreSQL table', async () => {
      const insertRequest = {
        database: 'postgres',
        operation: 'insert',
        tableName: 'test_users',
        data: {
          username: 'john_doe',
          email: 'john@example.com',
          metadata: { 
            role: 'trader',
            preferences: { theme: 'dark', notifications: true }
          }
        }
      };

      const response = await axios.post(
        `${databaseServiceUrl}/api/database/execute`,
        insertRequest
      );

      expect(response.status).to.equal(200);
      expect(response.data.success).to.be.true;
      expect(response.data.result.insertedId).to.exist;
    });

    it('should query data from PostgreSQL table', async () => {
      const queryRequest = {
        database: 'postgres',
        operation: 'select',
        tableName: 'test_users',
        conditions: { username: 'john_doe' },
        fields: ['id', 'username', 'email', 'metadata']
      };

      const response = await axios.post(
        `${databaseServiceUrl}/api/database/query`,
        queryRequest
      );

      expect(response.status).to.equal(200);
      expect(response.data.success).to.be.true;
      expect(response.data.result).to.be.an('array');
      expect(response.data.result[0]).to.include({
        username: 'john_doe',
        email: 'john@example.com'
      });
      expect(response.data.result[0].metadata.role).to.equal('trader');
    });

    it('should perform complex join queries', async () => {
      // First create orders table
      await axios.post(`${databaseServiceUrl}/api/database/execute`, {
        database: 'postgres',
        operation: 'createTable',
        tableName: 'test_orders',
        schema: {
          id: { type: 'SERIAL', primaryKey: true },
          user_id: { type: 'INTEGER', references: 'test_users(id)' },
          symbol: { type: 'VARCHAR(10)', notNull: true },
          quantity: { type: 'INTEGER', notNull: true },
          price: { type: 'DECIMAL(10,2)' },
          order_type: { type: 'VARCHAR(20)', notNull: true },
          status: { type: 'VARCHAR(20)', default: 'pending' },
          created_at: { type: 'TIMESTAMP', default: 'CURRENT_TIMESTAMP' }
        }
      });

      // Insert test order
      await axios.post(`${databaseServiceUrl}/api/database/execute`, {
        database: 'postgres',
        operation: 'insert',
        tableName: 'test_orders',
        data: {
          user_id: 1,
          symbol: 'AAPL',
          quantity: 100,
          price: 150.00,
          order_type: 'market',
          status: 'filled'
        }
      });

      // Perform join query
      const joinRequest = {
        database: 'postgres',
        operation: 'join',
        query: `
          SELECT u.username, u.email, o.symbol, o.quantity, o.price, o.status
          FROM test_users u
          INNER JOIN test_orders o ON u.id = o.user_id
          WHERE u.username = $1
        `,
        parameters: ['john_doe']
      };

      const response = await axios.post(
        `${databaseServiceUrl}/api/database/query`,
        joinRequest
      );

      expect(response.status).to.equal(200);
      expect(response.data.success).to.be.true;
      expect(response.data.result[0]).to.include({
        username: 'john_doe',
        symbol: 'AAPL',
        quantity: 100,
        status: 'filled'
      });
    });

    it('should handle transactions', async () => {
      const transactionRequest = {
        database: 'postgres',
        operation: 'transaction',
        queries: [
          {
            operation: 'insert',
            tableName: 'test_users',
            data: {
              username: 'jane_doe',
              email: 'jane@example.com'
            }
          },
          {
            operation: 'insert',
            tableName: 'test_orders',
            data: {
              user_id: 2, // Will be resolved from previous insert
              symbol: 'GOOGL',
              quantity: 50,
              price: 2500.00,
              order_type: 'limit'
            }
          }
        ]
      };

      const response = await axios.post(
        `${databaseServiceUrl}/api/database/transaction`,
        transactionRequest
      );

      expect(response.status).to.equal(200);
      expect(response.data.success).to.be.true;
      expect(response.data.result.transactionId).to.exist;
    });
  });

  describe('MongoDB Operations', () => {
    it('should create and insert document into MongoDB collection', async () => {
      const insertRequest = {
        database: 'mongodb',
        operation: 'insertOne',
        collection: 'portfolios',
        document: {
          userId: 'user123',
          totalValue: 50000,
          positions: [
            { symbol: 'AAPL', quantity: 100, avgPrice: 150.00 },
            { symbol: 'GOOGL', quantity: 25, avgPrice: 2500.00 }
          ],
          riskMetrics: {
            beta: 1.2,
            sharpeRatio: 1.8,
            volatility: 0.15
          },
          lastUpdated: new Date()
        }
      };

      const response = await axios.post(
        `${databaseServiceUrl}/api/database/execute`,
        insertRequest
      );

      expect(response.status).to.equal(200);
      expect(response.data.success).to.be.true;
      expect(response.data.result.insertedId).to.exist;
    });

    it('should query documents from MongoDB collection', async () => {
      const queryRequest = {
        database: 'mongodb',
        operation: 'find',
        collection: 'portfolios',
        filter: { userId: 'user123' },
        projection: { userId: 1, totalValue: 1, 'riskMetrics.beta': 1 }
      };

      const response = await axios.post(
        `${databaseServiceUrl}/api/database/query`,
        queryRequest
      );

      expect(response.status).to.equal(200);
      expect(response.data.success).to.be.true;
      expect(response.data.result).to.be.an('array');
      expect(response.data.result[0]).to.include({
        userId: 'user123',
        totalValue: 50000
      });
      expect(response.data.result[0].riskMetrics.beta).to.equal(1.2);
    });

    it('should perform aggregation queries', async () => {
      // Insert more portfolio data
      await axios.post(`${databaseServiceUrl}/api/database/execute`, {
        database: 'mongodb',
        operation: 'insertMany',
        collection: 'portfolios',
        documents: [
          {
            userId: 'user456',
            totalValue: 75000,
            positions: [{ symbol: 'TSLA', quantity: 200, avgPrice: 250.00 }],
            riskMetrics: { beta: 1.5, sharpeRatio: 2.1, volatility: 0.25 }
          },
          {
            userId: 'user789',
            totalValue: 30000,
            positions: [{ symbol: 'MSFT', quantity: 150, avgPrice: 200.00 }],
            riskMetrics: { beta: 0.8, sharpeRatio: 1.5, volatility: 0.12 }
          }
        ]
      });

      const aggregationRequest = {
        database: 'mongodb',
        operation: 'aggregate',
        collection: 'portfolios',
        pipeline: [
          {
            $group: {
              _id: null,
              totalPortfolioValue: { $sum: '$totalValue' },
              avgBeta: { $avg: '$riskMetrics.beta' },
              avgSharpeRatio: { $avg: '$riskMetrics.sharpeRatio' },
              portfolioCount: { $sum: 1 }
            }
          }
        ]
      };

      const response = await axios.post(
        `${databaseServiceUrl}/api/database/query`,
        aggregationRequest
      );

      expect(response.status).to.equal(200);
      expect(response.data.success).to.be.true;
      expect(response.data.result[0]).to.include({
        totalPortfolioValue: 155000,
        portfolioCount: 3
      });
      expect(response.data.result[0].avgBeta).to.be.approximately(1.17, 0.1);
    });

    it('should update documents with complex operations', async () => {
      const updateRequest = {
        database: 'mongodb',
        operation: 'updateOne',
        collection: 'portfolios',
        filter: { userId: 'user123' },
        update: {
          $inc: { totalValue: 5000 },
          $set: { 'riskMetrics.lastCalculated': new Date() },
          $push: {
            positions: {
              symbol: 'NVDA',
              quantity: 30,
              avgPrice: 450.00
            }
          }
        }
      };

      const response = await axios.post(
        `${databaseServiceUrl}/api/database/execute`,
        updateRequest
      );

      expect(response.status).to.equal(200);
      expect(response.data.success).to.be.true;
      expect(response.data.result.modifiedCount).to.equal(1);
    });
  });

  describe('Redis Operations', () => {
    it('should set and get key-value pairs', async () => {
      const setRequest = {
        database: 'redis',
        operation: 'set',
        key: 'user:123:session',
        value: JSON.stringify({
          sessionId: 'sess_123456',
          userId: 'user123',
          loginTime: new Date().toISOString(),
          permissions: ['trade', 'view_portfolio']
        }),
        ttl: 3600 // 1 hour
      };

      const setResponse = await axios.post(
        `${databaseServiceUrl}/api/database/execute`,
        setRequest
      );

      expect(setResponse.status).to.equal(200);
      expect(setResponse.data.success).to.be.true;

      const getRequest = {
        database: 'redis',
        operation: 'get',
        key: 'user:123:session'
      };

      const getResponse = await axios.post(
        `${databaseServiceUrl}/api/database/query`,
        getRequest
      );

      expect(getResponse.status).to.equal(200);
      expect(getResponse.data.success).to.be.true;
      
      const sessionData = JSON.parse(getResponse.data.result);
      expect(sessionData.userId).to.equal('user123');
      expect(sessionData.permissions).to.include('trade');
    });

    it('should handle hash operations', async () => {
      const hashRequest = {
        database: 'redis',
        operation: 'hset',
        key: 'market:prices',
        fields: {
          'AAPL': '155.50',
          'GOOGL': '2580.75',
          'TSLA': '245.20',
          'MSFT': '205.30'
        }
      };

      const setResponse = await axios.post(
        `${databaseServiceUrl}/api/database/execute`,
        hashRequest
      );

      expect(setResponse.status).to.equal(200);
      expect(setResponse.data.success).to.be.true;

      const getHashRequest = {
        database: 'redis',
        operation: 'hgetall',
        key: 'market:prices'
      };

      const getResponse = await axios.post(
        `${databaseServiceUrl}/api/database/query`,
        getHashRequest
      );

      expect(getResponse.status).to.equal(200);
      expect(getResponse.data.result).to.include({
        'AAPL': '155.50',
        'GOOGL': '2580.75'
      });
    });

    it('should handle list operations for real-time data', async () => {
      const pushRequest = {
        database: 'redis',
        operation: 'lpush',
        key: 'alerts:user123',
        values: [
          JSON.stringify({
            type: 'price_alert',
            symbol: 'AAPL',
            message: 'AAPL reached target price of $155',
            timestamp: new Date().toISOString()
          }),
          JSON.stringify({
            type: 'trade_execution',
            symbol: 'GOOGL',
            message: 'Your GOOGL order has been executed',
            timestamp: new Date().toISOString()
          })
        ]
      };

      const pushResponse = await axios.post(
        `${databaseServiceUrl}/api/database/execute`,
        pushRequest
      );

      expect(pushResponse.status).to.equal(200);
      expect(pushResponse.data.success).to.be.true;

      const rangeRequest = {
        database: 'redis',
        operation: 'lrange',
        key: 'alerts:user123',
        start: 0,
        stop: -1
      };

      const rangeResponse = await axios.post(
        `${databaseServiceUrl}/api/database/query`,
        rangeRequest
      );

      expect(rangeResponse.status).to.equal(200);
      expect(rangeResponse.data.result).to.be.an('array');
      expect(rangeResponse.data.result.length).to.equal(2);
    });
  });

  describe('Cross-Database Operations', () => {
    it('should execute operations across multiple databases', async () => {
      const multiDbRequest = {
        operation: 'multi-database',
        transactions: [
          {
            database: 'postgres',
            operation: 'insert',
            tableName: 'test_users',
            data: {
              username: 'cross_db_user',
              email: 'crossdb@example.com'
            }
          },
          {
            database: 'mongodb',
            operation: 'insertOne',
            collection: 'user_preferences',
            document: {
              userId: 'cross_db_user',
              preferences: {
                theme: 'dark',
                notifications: true,
                defaultView: 'portfolio'
              }
            }
          },
          {
            database: 'redis',
            operation: 'set',
            key: 'user:cross_db_user:cache',
            value: JSON.stringify({ cached: true, timestamp: new Date() }),
            ttl: 300
          }
        ]
      };

      const response = await axios.post(
        `${databaseServiceUrl}/api/database/multi-execute`,
        multiDbRequest
      );

      expect(response.status).to.equal(200);
      expect(response.data.success).to.be.true;
      expect(response.data.results).to.be.an('array');
      expect(response.data.results.length).to.equal(3);
      
      // Verify all operations succeeded
      response.data.results.forEach(result => {
        expect(result.success).to.be.true;
      });
    });

    it('should handle data synchronization between databases', async () => {
      const syncRequest = {
        operation: 'sync',
        sourceDatabase: 'postgres',
        targetDatabase: 'mongodb',
        mapping: {
          sourceTable: 'test_users',
          targetCollection: 'users_sync',
          fieldMapping: {
            id: '_id',
            username: 'username',
            email: 'email',
            created_at: 'createdAt',
            metadata: 'metadata'
          }
        },
        syncType: 'full' // or 'incremental'
      };

      const response = await axios.post(
        `${databaseServiceUrl}/api/database/sync`,
        syncRequest
      );

      expect(response.status).to.equal(200);
      expect(response.data.success).to.be.true;
      expect(response.data.syncedRecords).to.be.a('number');
      expect(response.data.syncedRecords).to.be.greaterThan(0);
    });

    it('should perform database health checks', async () => {
      const healthResponse = await axios.get(
        `${databaseServiceUrl}/api/database/health`
      );

      expect(healthResponse.status).to.equal(200);
      expect(healthResponse.data.success).to.be.true;
      expect(healthResponse.data.databases).to.be.an('object');
      
      expect(healthResponse.data.databases.postgres).to.include({
        connected: true,
        status: 'healthy'
      });
      expect(healthResponse.data.databases.mongodb).to.include({
        connected: true,
        status: 'healthy'
      });
      expect(healthResponse.data.databases.redis).to.include({
        connected: true,
        status: 'healthy'
      });
    });
  });

  describe('Performance and Load Testing', () => {
    it('should handle concurrent database operations', async function() {
      this.timeout(30000);
      
      const concurrentOperations = [];
      const numberOfOperations = 50;

      for (let i = 0; i < numberOfOperations; i++) {
        const operation = axios.post(
          `${databaseServiceUrl}/api/database/execute`,
          {
            database: 'postgres',
            operation: 'insert',
            tableName: 'test_users',
            data: {
              username: `concurrent_user_${i}`,
              email: `user${i}@concurrent.com`
            }
          }
        );
        concurrentOperations.push(operation);
      }

      const results = await Promise.allSettled(concurrentOperations);
      const successfulOps = results.filter(result => 
        result.status === 'fulfilled' && 
        result.value.data.success === true
      );

      expect(successfulOps.length).to.be.at.least(numberOfOperations * 0.95); // 95% success rate
    });

    it('should handle large data operations efficiently', async function() {
      this.timeout(60000);
      
      const largeDataset = [];
      for (let i = 0; i < 1000; i++) {
        largeDataset.push({
          userId: `bulk_user_${i}`,
          totalValue: Math.random() * 100000,
          positions: [
            { symbol: 'AAPL', quantity: Math.floor(Math.random() * 1000) },
            { symbol: 'GOOGL', quantity: Math.floor(Math.random() * 100) }
          ],
          riskMetrics: {
            beta: Math.random() * 2,
            sharpeRatio: Math.random() * 3,
            volatility: Math.random() * 0.5
          }
        });
      }

      const startTime = Date.now();
      
      const response = await axios.post(
        `${databaseServiceUrl}/api/database/execute`,
        {
          database: 'mongodb',
          operation: 'insertMany',
          collection: 'bulk_portfolios',
          documents: largeDataset
        }
      );

      const endTime = Date.now();
      const duration = endTime - startTime;

      expect(response.status).to.equal(200);
      expect(response.data.success).to.be.true;
      expect(response.data.result.insertedCount).to.equal(1000);
      expect(duration).to.be.lessThan(10000); // Should complete within 10 seconds
    });
  });

  describe('Error Handling and Recovery', () => {
    it('should handle database connection failures gracefully', async () => {
      const invalidDbRequest = {
        database: 'invalid_database',
        operation: 'select',
        tableName: 'test_table'
      };

      const response = await axios.post(
        `${databaseServiceUrl}/api/database/execute`,
        invalidDbRequest
      );

      expect(response.status).to.equal(400);
      expect(response.data.success).to.be.false;
      expect(response.data.error).to.include('Unsupported database type');
    });

    it('should validate request parameters', async () => {
      const invalidRequest = {
        database: 'postgres',
        operation: 'insert',
        // Missing tableName and data
      };

      try {
        await axios.post(
          `${databaseServiceUrl}/api/database/execute`,
          invalidRequest
        );
      } catch (error) {
        expect(error.response.status).to.equal(400);
        expect(error.response.data.success).to.be.false;
        expect(error.response.data.error).to.contain('validation');
      }
    });

    it('should handle transaction rollbacks on failure', async () => {
      const failingTransactionRequest = {
        database: 'postgres',
        operation: 'transaction',
        queries: [
          {
            operation: 'insert',
            tableName: 'test_users',
            data: {
              username: 'rollback_user',
              email: 'rollback@example.com'
            }
          },
          {
            operation: 'insert',
            tableName: 'nonexistent_table', // This will fail
            data: { invalid: 'data' }
          }
        ]
      };

      try {
        await axios.post(
          `${databaseServiceUrl}/api/database/transaction`,
          failingTransactionRequest
        );
      } catch (error) {
        expect(error.response.status).to.equal(500);
        expect(error.response.data.success).to.be.false;
        expect(error.response.data.error).to.contain('transaction');
      }

      // Verify rollback - user should not exist
      const verifyRequest = {
        database: 'postgres',
        operation: 'select',
        tableName: 'test_users',
        conditions: { username: 'rollback_user' }
      };

      const verifyResponse = await axios.post(
        `${databaseServiceUrl}/api/database/query`,
        verifyRequest
      );

      expect(verifyResponse.data.result).to.be.an('array').that.is.empty;
    });
  });

  // Helper functions
  async function setupTestDatabases() {
    // Setup PostgreSQL test database
    pgPool = new Pool({
      host: process.env.TEST_PG_HOST || 'localhost',
      port: process.env.TEST_PG_PORT || 5432,
      database: process.env.TEST_PG_DATABASE || 'test_trading_db',
      user: process.env.TEST_PG_USER || 'test_user',
      password: process.env.TEST_PG_PASSWORD || 'test_password'
    });
    testDatabases.postgres = pgPool;

    // Setup MongoDB test database
    mongoServer = await MongoMemoryServer.create();
    const mongoUri = mongoServer.getUri();
    await mongoose.connect(mongoUri, {
      useNewUrlParser: true,
      useUnifiedTopology: true
    });
    testDatabases.mongodb = mongoose.connection;

    // Setup Redis test database
    redisClient = new Redis({
      host: process.env.TEST_REDIS_HOST || 'localhost',
      port: process.env.TEST_REDIS_PORT || 6379,
      db: process.env.TEST_REDIS_DB || 1 // Use test database
    });
    testDatabases.redis = redisClient;

    // Wait for all connections to be ready
    await Promise.all([
      pgPool.query('SELECT 1'),
      mongoose.connection.db.admin().ping(),
      redisClient.ping()
    ]);

    console.log('All test databases connected successfully');
  }

  async function cleanupTestDatabases() {
    // Cleanup PostgreSQL
    if (pgPool) {
      await pgPool.query('DROP TABLE IF EXISTS test_orders CASCADE');
      await pgPool.query('DROP TABLE IF EXISTS test_users CASCADE');
      await pgPool.end();
    }

    // Cleanup MongoDB
    if (mongoose.connection.readyState === 1) {
      await mongoose.connection.db.dropDatabase();
      await mongoose.disconnect();
    }
    if (mongoServer) {
      await mongoServer.stop();
    }

    // Cleanup Redis
    if (redisClient) {
      await redisClient.flushdb();
      await redisClient.disconnect();
    }

    console.log('Test databases cleaned up');
  }
});
