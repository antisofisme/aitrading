/**
 * Redpanda (Kafka) Manager for Streaming Data
 * Handles real-time data streaming and messaging
 */

const { Kafka } = require('kafkajs');
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
    new winston.transports.File({ filename: 'logs/redpanda.log' })
  ]
});

class RedpandaManager extends IDatabaseManager {
  constructor(config) {
    super();
    this.config = config;
    this.kafka = null;
    this.producer = null;
    this.consumer = null;
    this.admin = null;
    this.isConnected = false;
    this.activeTopics = new Set();
  }

  async initialize() {
    try {
      this.kafka = new Kafka({
        clientId: 'ai-trading-database-service',
        brokers: this.config.brokers || ['localhost:19092'],
        connectionTimeout: 10000,
        requestTimeout: 30000,
        retry: {
          retries: 3,
          initialRetryTime: 300,
          maxRetryTime: 30000
        }
      });

      // Initialize producer
      this.producer = this.kafka.producer({
        maxInFlightRequests: 1,
        idempotent: true,
        transactionTimeout: 30000,
        allowAutoTopicCreation: true
      });

      await this.producer.connect();

      // Initialize admin client
      this.admin = this.kafka.admin();
      await this.admin.connect();

      // Initialize consumer
      this.consumer = this.kafka.consumer({
        groupId: 'ai-trading-database-service',
        sessionTimeout: 30000,
        heartbeatInterval: 3000,
        allowAutoTopicCreation: true
      });

      await this.consumer.connect();

      this.isConnected = true;

      logger.info('Redpanda connection established successfully', {
        brokers: this.config.brokers,
        clientId: 'ai-trading-database-service'
      });

      // Set up error handling
      this.producer.on('producer.connect', () => {
        logger.info('Redpanda producer connected');
      });

      this.producer.on('producer.disconnect', () => {
        logger.warn('Redpanda producer disconnected');
        this.isConnected = false;
      });

      this.consumer.on('consumer.connect', () => {
        logger.info('Redpanda consumer connected');
      });

      this.consumer.on('consumer.disconnect', () => {
        logger.warn('Redpanda consumer disconnected');
      });

      return this.kafka;
    } catch (error) {
      logger.error('Failed to initialize Redpanda connection:', error);
      this.isConnected = false;
      throw error;
    }
  }

  async publishMessage(topic, message, options = {}) {
    if (!this.isConnected) {
      throw new Error('Redpanda not connected');
    }

    try {
      const messagePayload = {
        topic,
        messages: [{
          key: options.key || null,
          value: typeof message === 'string' ? message : JSON.stringify(message),
          partition: options.partition,
          timestamp: options.timestamp || Date.now().toString(),
          headers: options.headers || {}
        }]
      };

      const result = await this.producer.send(messagePayload);

      logger.info('Message published to Redpanda', {
        topic,
        partition: result[0].partition,
        offset: result[0].offset,
        messageSize: messagePayload.messages[0].value.length
      });

      return result;
    } catch (error) {
      logger.error('Failed to publish message to Redpanda:', {
        error: error.message,
        topic,
        messagePreview: message.toString().substring(0, 100)
      });
      throw error;
    }
  }

  async subscribeToTopic(topic, messageHandler, options = {}) {
    if (!this.isConnected) {
      throw new Error('Redpanda not connected');
    }

    try {
      await this.consumer.subscribe({
        topic,
        fromBeginning: options.fromBeginning || false
      });

      this.activeTopics.add(topic);

      await this.consumer.run({
        eachMessage: async ({ topic, partition, message }) => {
          try {
            const messageData = {
              topic,
              partition,
              offset: message.offset,
              key: message.key ? message.key.toString() : null,
              value: message.value.toString(),
              timestamp: message.timestamp,
              headers: message.headers
            };

            await messageHandler(messageData);

            logger.debug('Message processed from Redpanda', {
              topic,
              partition,
              offset: message.offset
            });
          } catch (error) {
            logger.error('Error processing message from Redpanda:', {
              error: error.message,
              topic,
              partition,
              offset: message.offset
            });
          }
        }
      });

      logger.info('Subscribed to Redpanda topic', { topic });
    } catch (error) {
      logger.error('Failed to subscribe to Redpanda topic:', {
        error: error.message,
        topic
      });
      throw error;
    }
  }

  async createTopic(topic, options = {}) {
    if (!this.isConnected) {
      throw new Error('Redpanda not connected');
    }

    try {
      await this.admin.createTopics({
        topics: [{
          topic,
          numPartitions: options.partitions || 3,
          replicationFactor: options.replicationFactor || 1,
          configEntries: options.config || []
        }]
      });

      logger.info('Topic created in Redpanda', {
        topic,
        partitions: options.partitions || 3,
        replicationFactor: options.replicationFactor || 1
      });
    } catch (error) {
      if (error.type === 'TOPIC_ALREADY_EXISTS') {
        logger.info('Topic already exists in Redpanda', { topic });
      } else {
        logger.error('Failed to create topic in Redpanda:', {
          error: error.message,
          topic
        });
        throw error;
      }
    }
  }

  async listTopics() {
    if (!this.isConnected) {
      throw new Error('Redpanda not connected');
    }

    try {
      const metadata = await this.admin.fetchTopicMetadata();
      return metadata.topics.map(topic => ({
        name: topic.name,
        partitions: topic.partitions.length,
        partitionDetails: topic.partitions
      }));
    } catch (error) {
      logger.error('Failed to list topics in Redpanda:', error);
      throw error;
    }
  }

  async getTopicOffsets(topic) {
    if (!this.isConnected) {
      throw new Error('Redpanda not connected');
    }

    try {
      const metadata = await this.admin.fetchTopicOffsets(topic);
      return metadata;
    } catch (error) {
      logger.error('Failed to get topic offsets:', { error: error.message, topic });
      throw error;
    }
  }

  async close() {
    try {
      if (this.consumer) {
        await this.consumer.disconnect();
      }
      if (this.producer) {
        await this.producer.disconnect();
      }
      if (this.admin) {
        await this.admin.disconnect();
      }

      this.isConnected = false;
      this.activeTopics.clear();

      logger.info('Redpanda connections closed');
    } catch (error) {
      logger.error('Error closing Redpanda connections:', error);
    }
  }

  getStatus() {
    return {
      type: 'redpanda',
      connected: this.isConnected,
      activeTopics: Array.from(this.activeTopics),
      topicCount: this.activeTopics.size,
      config: {
        brokers: this.config.brokers,
        clientId: 'ai-trading-database-service'
      }
    };
  }

  async healthCheck() {
    try {
      if (!this.isConnected) {
        return {
          status: 'unhealthy',
          error: 'Not connected',
          timestamp: new Date().toISOString()
        };
      }

      const startTime = Date.now();

      // Test with admin metadata fetch
      const metadata = await this.admin.fetchTopicMetadata();

      const responseTime = Date.now() - startTime;

      return {
        status: 'healthy',
        responseTime,
        timestamp: new Date().toISOString(),
        details: {
          brokerCount: metadata.brokers.length,
          topicCount: metadata.topics.length,
          activeTopics: Array.from(this.activeTopics),
          lastCheck: new Date().toISOString()
        }
      };
    } catch (error) {
      logger.error('Redpanda health check failed:', error);
      return {
        status: 'unhealthy',
        error: error.message,
        timestamp: new Date().toISOString()
      };
    }
  }

  getType() {
    return 'redpanda';
  }

  getConfig() {
    return {
      ...this.config,
      // Don't expose sensitive information
      sasl: this.config.sasl ? { mechanism: this.config.sasl.mechanism } : undefined
    };
  }

  // Redpanda-specific convenience methods
  async publishTradeEvent(tradeData) {
    return await this.publishMessage('trading-events', tradeData, {
      key: tradeData.symbol || tradeData.id,
      headers: {
        'event-type': 'trade',
        'timestamp': Date.now().toString()
      }
    });
  }

  async publishMarketData(marketData) {
    return await this.publishMessage('market-data', marketData, {
      key: marketData.symbol,
      headers: {
        'event-type': 'market-data',
        'timestamp': Date.now().toString()
      }
    });
  }

  async publishAnalyticsEvent(analyticsData) {
    return await this.publishMessage('analytics-events', analyticsData, {
      key: analyticsData.type || 'general',
      headers: {
        'event-type': 'analytics',
        'timestamp': Date.now().toString()
      }
    });
  }

  async subscribeToTradeEvents(handler) {
    return await this.subscribeToTopic('trading-events', handler);
  }

  async subscribeToMarketData(handler) {
    return await this.subscribeToTopic('market-data', handler);
  }

  async subscribeToAnalyticsEvents(handler) {
    return await this.subscribeToTopic('analytics-events', handler);
  }

  // Create essential topics for AI Trading Platform
  async initializeStandardTopics() {
    const topics = [
      { name: 'trading-events', partitions: 6, description: 'Trade execution events' },
      { name: 'market-data', partitions: 12, description: 'Real-time market data' },
      { name: 'analytics-events', partitions: 3, description: 'Analytics and AI events' },
      { name: 'risk-alerts', partitions: 2, description: 'Risk management alerts' },
      { name: 'system-events', partitions: 2, description: 'System monitoring events' }
    ];

    for (const topicConfig of topics) {
      try {
        await this.createTopic(topicConfig.name, {
          partitions: topicConfig.partitions,
          replicationFactor: 1
        });
        logger.info(`Standard topic initialized: ${topicConfig.name} - ${topicConfig.description}`);
      } catch (error) {
        logger.warn(`Failed to create topic ${topicConfig.name}:`, error.message);
      }
    }
  }
}

module.exports = RedpandaManager;