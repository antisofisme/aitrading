/**
 * ArangoDB Graph Database Manager
 * Multi-model database for graph, document, and key-value data
 */

const { Database } = require('arangojs');
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
    new winston.transports.File({ filename: 'logs/arangodb.log' })
  ]
});

class ArangoDBManager extends IDatabaseManager {
  constructor(config) {
    super();
    this.config = config;
    this.db = null;
    this.isConnected = false;
    this.connectionAttempts = 0;
    this.maxConnectionAttempts = 5;
  }

  async initialize() {
    try {
      this.db = new Database({
        url: this.config.url,
        databaseName: this.config.database,
        auth: {
          username: this.config.username,
          password: this.config.password
        },
        agentOptions: {
          maxSockets: this.config.maxSockets || 20
        }
      });

      // Test connection
      await this.testConnection();

      this.isConnected = true;
      logger.info('ArangoDB connection established successfully', {
        url: this.config.url,
        database: this.config.database
      });

      return this.db;
    } catch (error) {
      logger.error('Failed to initialize ArangoDB connection:', error);
      this.isConnected = false;
      throw error;
    }
  }

  async testConnection() {
    let lastError;
    for (let attempt = 1; attempt <= this.maxConnectionAttempts; attempt++) {
      try {
        const version = await this.db.version();

        logger.info('ArangoDB connection test successful', {
          attempt,
          version: version.version,
          server: version.server
        });
        return;
      } catch (error) {
        lastError = error;
        logger.warn(`ArangoDB connection attempt ${attempt} failed:`, error.message);

        if (attempt < this.maxConnectionAttempts) {
          const delay = Math.pow(2, attempt) * 1000; // Exponential backoff
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }
    throw lastError;
  }

  async query(aqlQuery, bindVars = {}) {
    if (!this.isConnected) {
      throw new Error('ArangoDB not connected');
    }

    try {
      const start = Date.now();
      const cursor = await this.db.query(aqlQuery, bindVars);
      const result = await cursor.all();
      const duration = Date.now() - start;

      logger.info('ArangoDB query executed', {
        duration,
        resultCount: result.length,
        query: aqlQuery.substring(0, 100) + (aqlQuery.length > 100 ? '...' : '')
      });

      return {
        result: result,
        count: result.length,
        duration,
        extra: cursor.extra || {}
      };
    } catch (error) {
      logger.error('ArangoDB query error:', {
        error: error.message,
        query: aqlQuery.substring(0, 100),
        code: error.code
      });
      throw error;
    }
  }

  async getClient() {
    if (!this.isConnected) {
      throw new Error('ArangoDB not connected');
    }
    return this.db;
  }

  async close() {
    if (this.db) {
      await this.db.close();
      this.isConnected = false;
      logger.info('ArangoDB connection closed');
    }
  }

  getStatus() {
    return {
      type: 'arangodb',
      connected: this.isConnected,
      config: {
        url: this.config.url,
        database: this.config.database,
        username: this.config.username,
        maxSockets: this.config.maxSockets
      }
    };
  }

  async healthCheck() {
    try {
      const startTime = Date.now();
      const version = await this.db.version();
      const responseTime = Date.now() - startTime;

      return {
        status: 'healthy',
        responseTime,
        timestamp: new Date().toISOString(),
        details: {
          version: version.version,
          server: version.server,
          status: this.getStatus(),
          lastCheck: new Date().toISOString()
        }
      };
    } catch (error) {
      logger.error('ArangoDB health check failed:', error);
      return {
        status: 'unhealthy',
        error: error.message,
        timestamp: new Date().toISOString()
      };
    }
  }

  getType() {
    return 'arangodb';
  }

  getConfig() {
    return { ...this.config, password: '***' };
  }

  async beginTransaction() {
    try {
      const trx = await this.db.beginTransaction({
        collections: { read: [], write: [] }
      });
      return trx;
    } catch (error) {
      logger.error('Failed to begin ArangoDB transaction:', error);
      throw error;
    }
  }

  async commitTransaction(transaction) {
    try {
      await transaction.commit();
      logger.debug('ArangoDB transaction committed');
    } catch (error) {
      logger.error('Failed to commit ArangoDB transaction:', error);
      throw error;
    }
  }

  async rollbackTransaction(transaction) {
    try {
      await transaction.abort();
      logger.debug('ArangoDB transaction rolled back');
    } catch (error) {
      logger.error('Failed to rollback ArangoDB transaction:', error);
      throw error;
    }
  }

  // ArangoDB-specific methods

  // Collection operations
  async createCollection(name, type = 'document') {
    try {
      const collection = await this.db.createCollection(name, { type });
      logger.info(`Created ArangoDB collection: ${name}`);
      return collection;
    } catch (error) {
      logger.error(`Failed to create collection ${name}:`, error);
      throw error;
    }
  }

  async getCollection(name) {
    return this.db.collection(name);
  }

  async dropCollection(name) {
    try {
      const collection = this.db.collection(name);
      await collection.drop();
      logger.info(`Dropped ArangoDB collection: ${name}`);
    } catch (error) {
      logger.error(`Failed to drop collection ${name}:`, error);
      throw error;
    }
  }

  // Document operations
  async insertDocument(collectionName, document) {
    try {
      const collection = this.db.collection(collectionName);
      const result = await collection.save(document);
      return result;
    } catch (error) {
      logger.error(`Failed to insert document into ${collectionName}:`, error);
      throw error;
    }
  }

  async getDocument(collectionName, key) {
    try {
      const collection = this.db.collection(collectionName);
      const document = await collection.document(key);
      return document;
    } catch (error) {
      logger.error(`Failed to get document ${key} from ${collectionName}:`, error);
      throw error;
    }
  }

  async updateDocument(collectionName, key, data) {
    try {
      const collection = this.db.collection(collectionName);
      const result = await collection.update(key, data);
      return result;
    } catch (error) {
      logger.error(`Failed to update document ${key} in ${collectionName}:`, error);
      throw error;
    }
  }

  async deleteDocument(collectionName, key) {
    try {
      const collection = this.db.collection(collectionName);
      const result = await collection.remove(key);
      return result;
    } catch (error) {
      logger.error(`Failed to delete document ${key} from ${collectionName}:`, error);
      throw error;
    }
  }

  // Graph operations
  async createGraph(name, edgeDefinitions = []) {
    try {
      const graph = await this.db.createGraph(name, edgeDefinitions);
      logger.info(`Created ArangoDB graph: ${name}`);
      return graph;
    } catch (error) {
      logger.error(`Failed to create graph ${name}:`, error);
      throw error;
    }
  }

  async getGraph(name) {
    return this.db.graph(name);
  }

  async dropGraph(name, dropCollections = false) {
    try {
      const graph = this.db.graph(name);
      await graph.drop(dropCollections);
      logger.info(`Dropped ArangoDB graph: ${name}`);
    } catch (error) {
      logger.error(`Failed to drop graph ${name}:`, error);
      throw error;
    }
  }

  async addVertex(graphName, collectionName, data) {
    try {
      const graph = this.db.graph(graphName);
      const collection = graph.vertexCollection(collectionName);
      const result = await collection.save(data);
      return result;
    } catch (error) {
      logger.error(`Failed to add vertex to ${graphName}:`, error);
      throw error;
    }
  }

  async addEdge(graphName, collectionName, from, to, data = {}) {
    try {
      const graph = this.db.graph(graphName);
      const collection = graph.edgeCollection(collectionName);
      const result = await collection.save({ ...data, _from: from, _to: to });
      return result;
    } catch (error) {
      logger.error(`Failed to add edge to ${graphName}:`, error);
      throw error;
    }
  }

  // Graph traversal
  async traverseGraph(startVertex, options = {}) {
    const {
      direction = 'outbound',
      minDepth = 1,
      maxDepth = 5,
      edgeCollection = null,
      filter = null
    } = options;

    try {
      let aql = `
        FOR v, e, p IN ${minDepth}..${maxDepth} ${direction} '${startVertex}'
      `;

      if (edgeCollection) {
        aql += ` ${edgeCollection}`;
      }

      if (filter) {
        aql += ` FILTER ${filter}`;
      }

      aql += ' RETURN { vertex: v, edge: e, path: p }';

      const result = await this.query(aql);
      return result.result;
    } catch (error) {
      logger.error('Graph traversal failed:', error);
      throw error;
    }
  }

  // Shortest path
  async shortestPath(from, to, options = {}) {
    const {
      edgeCollection = null,
      direction = 'outbound',
      weightAttribute = null
    } = options;

    try {
      let aql = `
        FOR v, e IN ${direction} SHORTEST_PATH '${from}' TO '${to}'
      `;

      if (edgeCollection) {
        aql += ` ${edgeCollection}`;
      }

      if (weightAttribute) {
        aql += ` OPTIONS { weightAttribute: '${weightAttribute}' }`;
      }

      aql += ' RETURN { vertex: v, edge: e }';

      const result = await this.query(aql);
      return result.result;
    } catch (error) {
      logger.error('Shortest path query failed:', error);
      throw error;
    }
  }

  // Analytics and aggregation
  async getCollectionStats(collectionName) {
    try {
      const aql = `
        RETURN {
          count: LENGTH(@@collection),
          figures: COLLECTION_FIGURES(@@collection)
        }
      `;

      const result = await this.query(aql, { '@collection': collectionName });
      return result.result[0];
    } catch (error) {
      logger.error(`Failed to get stats for collection ${collectionName}:`, error);
      throw error;
    }
  }

  async createIndex(collectionName, fields, type = 'hash', options = {}) {
    try {
      const collection = this.db.collection(collectionName);
      const result = await collection.createIndex({ type, fields, ...options });
      logger.info(`Created index on ${collectionName}:`, { fields, type });
      return result;
    } catch (error) {
      logger.error(`Failed to create index on ${collectionName}:`, error);
      throw error;
    }
  }

  async getIndexes(collectionName) {
    try {
      const collection = this.db.collection(collectionName);
      const indexes = await collection.indexes();
      return indexes;
    } catch (error) {
      logger.error(`Failed to get indexes for ${collectionName}:`, error);
      throw error;
    }
  }
}

module.exports = ArangoDBManager;