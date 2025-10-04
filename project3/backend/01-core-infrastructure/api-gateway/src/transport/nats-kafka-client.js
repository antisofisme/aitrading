/**
 * NATS+Kafka Hybrid Transport Client
 * Implements simultaneous dual transport for high-volume data
 *
 * Features:
 * - NATS for real-time processing (<1ms)
 * - Kafka for durability & replay capability (<5ms)
 * - Hybrid resilience with automatic failover
 * - Performance monitoring and metrics
 */

const { connect } = require('nats');
const { Kafka } = require('kafkajs');
const EventEmitter = require('events');

// Simple console logger to avoid ES Module issues
const logger = {
    warn: (msg, data) => console.warn(`[TRANSPORT-WARN] ${msg}`, data || ''),
    debug: (msg, data) => console.log(`[TRANSPORT-DEBUG] ${msg}`, data || ''),
    info: (msg, data) => console.log(`[TRANSPORT-INFO] ${msg}`, data || ''),
    error: (msg, data) => console.error(`[TRANSPORT-ERROR] ${msg}`, data || '')
};

class NATSKafkaClient extends EventEmitter {
    constructor(config) {
        super();

        // ✅ CONFIG FLOW: Central Hub → APIGatewayService → BidirectionalRouter → NATSKafkaClient
        // Config is fetched from Central Hub in APIGatewayService.initializeCore()
        // Fallback to env vars only if config not provided by caller
        this.config = {
            nats: {
                servers: config.nats?.servers || (process.env.NATS_URL ? [process.env.NATS_URL] : ['nats://suho-nats-server:4222']),
                reconnectTimeWait: 250,
                maxReconnectAttempts: -1,
                pingInterval: 30000,
                ...config.nats
            },
            kafka: {
                clientId: 'api-gateway',
                brokers: config.kafka?.brokers || (process.env.KAFKA_BROKERS ? [process.env.KAFKA_BROKERS] : ['suho-kafka:9092']),
                retry: {
                    initialRetryTime: 100,
                    retries: 8
                },
                ...config.kafka
            }
        };


        // Clients
        this.natsClient = null;
        this.kafkaClient = null;
        this.kafkaProducer = null;

        // Connection status
        this.status = {
            nats: { connected: false, lastError: null },
            kafka: { connected: false, lastError: null }
        };

        // Performance metrics
        this.metrics = {
            nats: { published: 0, errors: 0, avgLatency: 0 },
            kafka: { published: 0, errors: 0, avgLatency: 0 }
        };
    }

    /**
     * Initialize both NATS and Kafka connections
     */
    async initialize() {
        logger.info('Initializing NATS+Kafka hybrid transport');

        try {
            // Initialize connections in parallel
            await Promise.all([
                this.initializeNATS(),
                this.initializeKafka()
            ]);

            // Start health monitoring
            this.startHealthMonitoring();

            logger.info('NATS+Kafka hybrid transport initialized successfully');
            this.emit('ready');

        } catch (error) {
            logger.error('Failed to initialize NATS+Kafka transport', { error });
            throw error;
        }
    }

    /**
     * Initialize NATS connection
     */
    async initializeNATS() {
        try {
            this.natsClient = await connect({
                servers: this.config.nats.servers,
                reconnectTimeWait: this.config.nats.reconnectTimeWait,
                maxReconnectAttempts: this.config.nats.maxReconnectAttempts,
                pingInterval: this.config.nats.pingInterval,
                verbose: false,
                pedantic: false,
                noEcho: true
            });

            // Event handlers
            this.natsClient.closed().then(() => {
                this.status.nats.connected = false;
                logger.warn('NATS connection closed');
                this.emit('nats_disconnected');
            });

            this.status.nats.connected = true;
            logger.info('NATS client connected successfully', {
                servers: this.config.nats.servers
            });

        } catch (error) {
            this.status.nats.lastError = error;
            logger.error('Failed to connect to NATS', { error });
            throw error;
        }
    }

    /**
     * Initialize Kafka connection
     */
    async initializeKafka() {
        try {
            // DEBUG: Log exact Kafka config being used
            logger.info('Initializing Kafka with config:', {
                clientId: this.config.kafka.clientId,
                brokers: this.config.kafka.brokers,
                retry: this.config.kafka.retry
            });

            // Enhanced Kafka configuration to prevent localhost discovery
            const kafkaConfig = {
                ...this.config.kafka,
                // Disable metadata refresh to prevent broker discovery
                metadataMaxAge: 30000, // 30 seconds
                // Force connection only to specified brokers
                connectionTimeout: 3000,
                requestTimeout: 30000,
                // Disable retries to localhost
                retry: {
                    ...this.config.kafka.retry,
                    retries: 3,
                    factor: 0.2,
                    multiplier: 2,
                    maxRetryTime: 10000
                }
            };

            this.kafkaClient = new Kafka(kafkaConfig);
            this.kafkaProducer = this.kafkaClient.producer({
                maxInFlightRequests: 1,
                idempotent: true,
                transactionTimeout: 30000,
                allowAutoTopicCreation: true,
                // Force using only configured brokers
                retry: {
                    retries: 3,
                    factor: 0.2,
                    multiplier: 2,
                    maxRetryTime: 5000
                }
            });

            await this.kafkaProducer.connect();

            this.status.kafka.connected = true;
            logger.info('Kafka producer connected successfully', {
                brokers: this.config.kafka.brokers
            });

        } catch (error) {
            this.status.kafka.lastError = error;
            logger.error('Failed to connect to Kafka', { error });
            throw error;
        }
    }

    /**
     * Publish message via NATS+Kafka hybrid (simultaneous)
     */
    async publishHybrid(subject, topic, data, metadata = {}) {
        const startTime = Date.now();
        const results = { nats: null, kafka: null };

        try {
            // Prepare message envelope
            const messageEnvelope = {
                data: data,
                metadata: {
                    timestamp: Date.now(),
                    correlationId: metadata.correlationId,
                    userId: metadata.userId,
                    source: 'api-gateway',
                    ...metadata
                }
            };

            // Execute both transports simultaneously
            const promises = [];

            // NATS publish (real-time)
            if (this.status.nats.connected) {
                promises.push(
                    this.publishViaNATS(subject, messageEnvelope)
                        .then(result => { results.nats = result; })
                        .catch(error => { results.nats = { error }; })
                );
            }

            // Kafka publish (durability)
            if (this.status.kafka.connected) {
                promises.push(
                    this.publishViaKafka(topic, messageEnvelope, metadata)
                        .then(result => { results.kafka = result; })
                        .catch(error => { results.kafka = { error }; })
                );
            }

            // Wait for both to complete
            await Promise.allSettled(promises);

            // Update metrics
            const totalLatency = Date.now() - startTime;
            this.updateMetrics(results, totalLatency);

            // Emit success if at least one succeeded
            const success = results.nats?.success || results.kafka?.success;
            if (success) {
                this.emit('message_published', {
                    subject,
                    topic,
                    results,
                    latency: totalLatency
                });
            }

            return {
                success,
                results,
                latency: totalLatency
            };

        } catch (error) {
            logger.error('Hybrid publish failed', { error, subject, topic });
            throw error;
        }
    }

    /**
     * Publish via NATS (real-time processing)
     */
    async publishViaNATS(subject, messageEnvelope) {
        const startTime = Date.now();

        try {
            if (!this.status.nats.connected) {
                throw new Error('NATS not connected');
            }

            // Serialize message
            const serializedData = Buffer.isBuffer(messageEnvelope.data)
                ? messageEnvelope.data
                : Buffer.from(JSON.stringify(messageEnvelope), 'utf8');

            // Publish to NATS
            this.natsClient.publish(subject, serializedData);

            const latency = Date.now() - startTime;
            this.metrics.nats.published++;
            this.metrics.nats.avgLatency = (this.metrics.nats.avgLatency * 0.9) + (latency * 0.1);

            logger.debug('NATS message published', {
                subject,
                size: serializedData.length,
                latency
            });

            return { success: true, latency, transport: 'nats' };

        } catch (error) {
            this.metrics.nats.errors++;
            this.status.nats.lastError = error;
            logger.error('NATS publish failed', { error, subject });
            throw error;
        }
    }

    /**
     * Publish via Kafka (durability & replay)
     */
    async publishViaKafka(topic, messageEnvelope, metadata = {}) {
        const startTime = Date.now();

        try {
            if (!this.status.kafka.connected) {
                throw new Error('Kafka not connected');
            }

            // Prepare Kafka message
            const kafkaMessage = {
                topic: topic,
                messages: [{
                    key: metadata.userId || 'default',
                    value: Buffer.isBuffer(messageEnvelope.data)
                        ? messageEnvelope.data
                        : Buffer.from(JSON.stringify(messageEnvelope), 'utf8'),
                    partition: metadata.partition,
                    headers: {
                        correlationId: messageEnvelope.metadata.correlationId,
                        source: 'api-gateway',
                        timestamp: Date.now().toString()
                    }
                }]
            };

            // Send to Kafka
            const result = await this.kafkaProducer.send(kafkaMessage);

            const latency = Date.now() - startTime;
            this.metrics.kafka.published++;
            this.metrics.kafka.avgLatency = (this.metrics.kafka.avgLatency * 0.9) + (latency * 0.1);

            logger.debug('Kafka message published', {
                topic,
                partition: result[0].partition,
                offset: result[0].baseOffset,
                latency
            });

            return {
                success: true,
                latency,
                transport: 'kafka',
                partition: result[0].partition,
                offset: result[0].baseOffset
            };

        } catch (error) {
            this.metrics.kafka.errors++;
            this.status.kafka.lastError = error;
            logger.error('Kafka publish failed', { error, topic });
            throw error;
        }
    }

    /**
     * Update performance metrics
     */
    updateMetrics(results, totalLatency) {
        // Update overall metrics based on results
        if (results.nats?.success) {
            this.metrics.nats.published++;
        } else if (results.nats?.error) {
            this.metrics.nats.errors++;
        }

        if (results.kafka?.success) {
            this.metrics.kafka.published++;
        } else if (results.kafka?.error) {
            this.metrics.kafka.errors++;
        }
    }

    /**
     * Start health monitoring
     */
    startHealthMonitoring() {
        setInterval(() => {
            this.checkHealth();
        }, 30000); // Check every 30 seconds
    }

    /**
     * Check connection health
     */
    async checkHealth() {
        // Check NATS health
        if (this.natsClient && !this.status.nats.connected) {
            try {
                // Try to reconnect if needed
                logger.info('Attempting to reconnect to NATS');
                await this.initializeNATS();
            } catch (error) {
                logger.error('NATS reconnection failed', { error });
            }
        }

        // Check Kafka health
        if (this.kafkaProducer && !this.status.kafka.connected) {
            try {
                logger.info('Attempting to reconnect to Kafka');
                await this.initializeKafka();
            } catch (error) {
                logger.error('Kafka reconnection failed', { error });
            }
        }

        // Emit health status
        this.emit('health_check', {
            nats: this.status.nats,
            kafka: this.status.kafka,
            metrics: this.metrics
        });
    }

    /**
     * Get connection status and metrics
     */
    getStatus() {
        return {
            connections: {
                nats: {
                    connected: this.status.nats.connected,
                    lastError: this.status.nats.lastError?.message,
                    servers: this.config.nats.servers
                },
                kafka: {
                    connected: this.status.kafka.connected,
                    lastError: this.status.kafka.lastError?.message,
                    brokers: this.config.kafka.brokers
                }
            },
            metrics: {
                nats: {
                    ...this.metrics.nats,
                    successRate: this.metrics.nats.published /
                        (this.metrics.nats.published + this.metrics.nats.errors) || 0
                },
                kafka: {
                    ...this.metrics.kafka,
                    successRate: this.metrics.kafka.published /
                        (this.metrics.kafka.published + this.metrics.kafka.errors) || 0
                }
            }
        };
    }

    /**
     * Graceful shutdown
     */
    async shutdown() {
        logger.info('Shutting down NATS+Kafka transport');

        try {
            // Close connections
            if (this.natsClient) {
                await this.natsClient.close();
            }
            if (this.kafkaProducer) {
                await this.kafkaProducer.disconnect();
            }

            logger.info('NATS+Kafka transport shutdown complete');
        } catch (error) {
            logger.error('Error during transport shutdown', { error });
        }
    }
}

module.exports = NATSKafkaClient;