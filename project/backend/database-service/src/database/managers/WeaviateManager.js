/**
 * Weaviate Vector Database Manager
 * AI/ML vector database for similarity search and recommendations
 */

const weaviate = require('weaviate-ts-client');
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
    new winston.transports.File({ filename: 'logs/weaviate.log' })
  ]
});

class WeaviateManager extends IDatabaseManager {
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
      // Create Weaviate client
      let clientBuilder = weaviate.client({
        scheme: this.config.scheme,
        host: `${this.config.host}:${this.config.port}`,
      });

      if (this.config.apiKey) {
        clientBuilder = clientBuilder.withApiKey(this.config.apiKey);
      }

      this.client = clientBuilder.build();

      // Test connection
      await this.testConnection();

      this.isConnected = true;
      logger.info('Weaviate connection established successfully', {
        host: this.config.host,
        port: this.config.port,
        scheme: this.config.scheme
      });

      return this.client;
    } catch (error) {
      logger.error('Failed to initialize Weaviate connection:', error);
      this.isConnected = false;
      throw error;
    }
  }

  async testConnection() {
    let lastError;
    for (let attempt = 1; attempt <= this.maxConnectionAttempts; attempt++) {
      try {
        const meta = await this.client.misc.metaGetter().do();

        logger.info('Weaviate connection test successful', {
          attempt,
          version: meta.version,
          hostname: meta.hostname
        });
        return;
      } catch (error) {
        lastError = error;
        logger.warn(`Weaviate connection attempt ${attempt} failed:`, error.message);

        if (attempt < this.maxConnectionAttempts) {
          const delay = Math.pow(2, attempt) * 1000; // Exponential backoff
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }
    throw lastError;
  }

  async query(queryObj, params = []) {
    if (!this.isConnected) {
      throw new Error('Weaviate not connected');
    }

    try {
      const start = Date.now();
      let result;

      // Handle different query types
      if (typeof queryObj === 'string') {
        // GraphQL query
        result = await this.client.graphql.raw().withQuery(queryObj).do();
      } else if (queryObj.type === 'search') {
        // Vector search
        result = await this.vectorSearch(queryObj);
      } else if (queryObj.type === 'get') {
        // Get objects
        result = await this.getObjects(queryObj);
      } else {
        throw new Error('Unsupported query type for Weaviate');
      }

      const duration = Date.now() - start;

      logger.info('Weaviate query executed', {
        duration,
        type: queryObj.type || 'graphql',
        resultCount: result.data ? Object.keys(result.data).length : 0
      });

      return {
        data: result.data || result,
        errors: result.errors || [],
        duration,
        type: queryObj.type || 'graphql'
      };
    } catch (error) {
      logger.error('Weaviate query error:', {
        error: error.message,
        queryType: queryObj.type || 'unknown'
      });
      throw error;
    }
  }

  async getClient() {
    if (!this.isConnected) {
      throw new Error('Weaviate not connected');
    }
    return this.client;
  }

  async close() {
    if (this.client) {
      // Weaviate client doesn't require explicit closing
      this.isConnected = false;
      logger.info('Weaviate connection closed');
    }
  }

  getStatus() {
    return {
      type: 'weaviate',
      connected: this.isConnected,
      config: {
        host: this.config.host,
        port: this.config.port,
        scheme: this.config.scheme,
        hasApiKey: !!this.config.apiKey
      }
    };
  }

  async healthCheck() {
    try {
      const startTime = Date.now();
      const meta = await this.client.misc.metaGetter().do();
      const responseTime = Date.now() - startTime;

      return {
        status: 'healthy',
        responseTime,
        timestamp: new Date().toISOString(),
        details: {
          version: meta.version,
          hostname: meta.hostname,
          modules: meta.modules,
          status: this.getStatus(),
          lastCheck: new Date().toISOString()
        }
      };
    } catch (error) {
      logger.error('Weaviate health check failed:', error);
      return {
        status: 'unhealthy',
        error: error.message,
        timestamp: new Date().toISOString()
      };
    }
  }

  getType() {
    return 'weaviate';
  }

  getConfig() {
    return { ...this.config, apiKey: this.config.apiKey ? '***' : undefined };
  }

  // Weaviate doesn't support traditional transactions
  async beginTransaction() {
    throw new Error('Weaviate does not support traditional transactions');
  }

  async commitTransaction(transaction) {
    throw new Error('Weaviate does not support traditional transactions');
  }

  async rollbackTransaction(transaction) {
    throw new Error('Weaviate does not support traditional transactions');
  }

  // Weaviate-specific methods
  async createClass(className, properties, vectorizer = 'text2vec-openai') {
    try {
      const classDefinition = {
        class: className,
        properties: properties,
        vectorizer: vectorizer,
        moduleConfig: {
          'text2vec-openai': {
            model: 'ada',
            modelVersion: '002',
            type: 'text'
          }
        }
      };

      const result = await this.client.schema.classCreator().withClass(classDefinition).do();
      logger.info(`Created Weaviate class: ${className}`);
      return result;
    } catch (error) {
      logger.error(`Failed to create Weaviate class ${className}:`, error);
      throw error;
    }
  }

  async addObject(className, properties, vector = null) {
    try {
      let creator = this.client.data.creator()
        .withClassName(className)
        .withProperties(properties);

      if (vector) {
        creator = creator.withVector(vector);
      }

      const result = await creator.do();
      return result;
    } catch (error) {
      logger.error(`Failed to add object to ${className}:`, error);
      throw error;
    }
  }

  async addObjects(className, objects) {
    try {
      const batcher = this.client.batch.objectsBatcher();

      objects.forEach(obj => {
        let objectCreator = batcher.withObject({
          class: className,
          properties: obj.properties
        });

        if (obj.vector) {
          objectCreator.withVector(obj.vector);
        }
      });

      const result = await batcher.do();
      return result;
    } catch (error) {
      logger.error(`Failed to batch add objects to ${className}:`, error);
      throw error;
    }
  }

  async vectorSearch(searchObj) {
    const {
      className,
      vector,
      concepts = [],
      limit = 10,
      certainty = 0.7,
      properties = []
    } = searchObj;

    try {
      let searcher = this.client.graphql.get()
        .withClassName(className)
        .withLimit(limit);

      if (properties.length > 0) {
        searcher = searcher.withFields(properties.join(' '));
      }

      if (vector) {
        searcher = searcher.withNearVector({
          vector: vector,
          certainty: certainty
        });
      } else if (concepts.length > 0) {
        searcher = searcher.withNearText({
          concepts: concepts,
          certainty: certainty
        });
      }

      const result = await searcher.do();
      return result;
    } catch (error) {
      logger.error('Vector search failed:', error);
      throw error;
    }
  }

  async getObjects(getObj) {
    const {
      className,
      properties = [],
      where = null,
      limit = 100
    } = getObj;

    try {
      let getter = this.client.graphql.get()
        .withClassName(className)
        .withLimit(limit);

      if (properties.length > 0) {
        getter = getter.withFields(properties.join(' '));
      }

      if (where) {
        getter = getter.withWhere(where);
      }

      const result = await getter.do();
      return result;
    } catch (error) {
      logger.error('Get objects failed:', error);
      throw error;
    }
  }

  async deleteClass(className) {
    try {
      const result = await this.client.schema.classDeleter().withClassName(className).do();
      logger.info(`Deleted Weaviate class: ${className}`);
      return result;
    } catch (error) {
      logger.error(`Failed to delete Weaviate class ${className}:`, error);
      throw error;
    }
  }

  async getSchema() {
    try {
      const schema = await this.client.schema.getter().do();
      return schema;
    } catch (error) {
      logger.error('Failed to get Weaviate schema:', error);
      throw error;
    }
  }

  async getClassInfo(className) {
    try {
      const classInfo = await this.client.schema.classGetter().withClassName(className).do();
      return classInfo;
    } catch (error) {
      logger.error(`Failed to get class info for ${className}:`, error);
      throw error;
    }
  }

  // AI/ML specific operations
  async similaritySearch(className, queryText, limit = 10) {
    return await this.vectorSearch({
      className,
      concepts: [queryText],
      limit,
      certainty: 0.7
    });
  }

  async recommendSimilar(className, objectId, limit = 10) {
    try {
      const result = await this.client.graphql.get()
        .withClassName(className)
        .withNearObject({
          id: objectId
        })
        .withLimit(limit)
        .do();

      return result;
    } catch (error) {
      logger.error('Recommendation search failed:', error);
      throw error;
    }
  }

  async classify(className, properties, targetProperty) {
    try {
      const result = await this.client.classifications.scheduler()
        .withType('knn')
        .withClassName(className)
        .withClassifyProperties([targetProperty])
        .withBasedOnProperties(properties)
        .do();

      return result;
    } catch (error) {
      logger.error('Classification failed:', error);
      throw error;
    }
  }
}

module.exports = WeaviateManager;