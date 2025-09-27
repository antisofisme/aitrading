/**
 * NATS+Kafka Hybrid Transport Adapter
 *
 * Implements hybrid transport where:
 * - NATS: Real-time processing (speed priority)
 * - Kafka: Durability & replay capability (reliability priority)
 *
 * Both transports run simultaneously for mission-critical data
 */

const { connect } = require('nats');
const { Kafka } = require('kafkajs');
const EventEmitter = require('events');
const logger = require('../../logging/logger');

class NATSKafkaAdapter extends EventEmitter {
    constructor(config = {}) {
        super();

        this.config = {
            nats: {
                servers: config.nats?.servers || ['nats://localhost:4222'],
                reconnectTimeWait: config.nats?.reconnectTimeWait || 250,
                maxReconnectAttempts: config.nats?.maxReconnectAttempts || -1,
                pingInterval: config.nats?.pingInterval || 30000,
                ...config.nats
            },
            kafka: {
                clientId: config.kafka?.clientId || 'shared-transfer',
                brokers: config.kafka?.brokers || ['localhost:9092'],
                retry: {
                    initialRetryTime: config.kafka?.retry?.initialRetryTime || 100,
                    retries: config.kafka?.retry?.retries || 8
                },
                ...config.kafka
            },
            hybrid_mode: config.hybrid_mode !== false,
            fallback_to_single: config.fallback_to_single !== false
        };

        // Clients
        this.natsClient = null;
        this.kafkaClient = null;
        this.kafkaProducer = null;
        this.kafkaConsumer = null;

        // Status
        this.status = {
            nats: { connected: false, lastError: null },
            kafka: { connected: false, lastError: null }
        };

        // Metrics
        this.metrics = {
            nats: { published: 0, errors: 0, avgLatency: 0 },
            kafka: { published: 0, errors: 0, avgLatency: 0 },
            hybrid: { published: 0, partialSuccess: 0, totalFailures: 0 }
        };
    }

    /**
     * Initialize NATS and Kafka connections
     */
    async initialize() {
        logger.info('Initializing NATS+Kafka hybrid adapter');

        try {
            // Initialize both transports in parallel
            await Promise.allSettled([
                this.initializeNATS(),
                this.initializeKafka()
            ]);

            // Check if at least one transport is available
            if (!this.status.nats.connected && !this.status.kafka.connected) {
                throw new Error('Both NATS and Kafka initialization failed');
            }

            // Start health monitoring
            this.startHealthMonitoring();

            logger.info('NATS+Kafka adapter initialized', {
                nats_connected: this.status.nats.connected,
                kafka_connected: this.status.kafka.connected
            });

            this.emit('ready');

        } catch (error) {
            logger.error('Failed to initialize NATS+Kafka adapter', { error });
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

            // Handle connection events
            this.natsClient.closed().then(() => {
                this.status.nats.connected = false;
                logger.warn('NATS connection closed');
                this.emit('nats_disconnected');
            });

            this.status.nats.connected = true;
            logger.info('NATS client connected', {
                servers: this.config.nats.servers
            });

        } catch (error) {
            this.status.nats.lastError = error;
            this.status.nats.connected = false;
            logger.error('Failed to connect to NATS', { error });

            if (!this.config.fallback_to_single) {
                throw error;
            }
        }
    }

    /**
     * Initialize Kafka connection
     */
    async initializeKafka() {
        try {
            this.kafkaClient = new Kafka(this.config.kafka);

            this.kafkaProducer = this.kafkaClient.producer({
                maxInFlightRequests: 1,
                idempotent: true,
                transactionTimeout: 30000,
                allowAutoTopicCreation: true
            });

            await this.kafkaProducer.connect();

            this.status.kafka.connected = true;
            logger.info('Kafka producer connected', {
                brokers: this.config.kafka.brokers
            });

        } catch (error) {
            this.status.kafka.lastError = error;
            this.status.kafka.connected = false;
            logger.error('Failed to connect to Kafka', { error });

            if (!this.config.fallback_to_single) {
                throw error;
            }
        }
    }

    /**
     * Send message via hybrid transport
     * @param {Object} data - Data to send
     * @param {string} destination - Target service
     * @param {Object} options - Send options
     */
    async send(data, destination, options = {}) {
        const startTime = Date.now();
        const results = { nats: null, kafka: null };

        try {
            // Prepare message envelope
            const messageEnvelope = this.prepareMessage(data, destination, options);

            // Determine subjects/topics
            const natsSubject = this.getNATSSubject(destination, options);
            const kafkaTopic = this.getKafkaTopic(destination, options);

            if (this.config.hybrid_mode && this.status.nats.connected && this.status.kafka.connected) {
                // HYBRID: Execute both transports simultaneously
                await this.sendHybrid(natsSubject, kafkaTopic, messageEnvelope, results);
            } else {
                // FALLBACK: Use single available transport
                await this.sendSingle(natsSubject, kafkaTopic, messageEnvelope, results);
            }

            // Update metrics
            const totalLatency = Date.now() - startTime;
            this.updateMetrics(results, totalLatency);

            // Determine success
            const success = results.nats?.success || results.kafka?.success;

            return {
                success,
                results,
                latency: totalLatency,
                transport: 'nats-kafka'
            };

        } catch (error) {
            logger.error('NATS+Kafka send failed', { error, destination });
            throw error;
        }
    }

    /**
     * Send via hybrid mode (both NATS and Kafka)
     */
    async sendHybrid(natsSubject, kafkaTopic, messageEnvelope, results) {
        const promises = [];

        // NATS: Real-time processing
        promises.push(
            this.publishViaNATS(natsSubject, {
                ...messageEnvelope,
                transport: 'nats',
                purpose: 'real-time'
            }).then(result => {
                results.nats = result;
            }).catch(error => {
                results.nats = { error, success: false };
            })
        );

        // Kafka: Durability & replay
        promises.push(
            this.publishViaKafka(kafkaTopic, {
                ...messageEnvelope,
                transport: 'kafka',
                purpose: 'durability'
            }).then(result => {
                results.kafka = result;
            }).catch(error => {
                results.kafka = { error, success: false };
            })
        );

        // Wait for both to complete
        await Promise.allSettled(promises);

        // Log results
        const natsSuccess = results.nats?.success;
        const kafkaSuccess = results.kafka?.success;

        if (natsSuccess && kafkaSuccess) {
            logger.debug('Hybrid transport: both succeeded');
            this.metrics.hybrid.published++;
        } else if (natsSuccess || kafkaSuccess) {
            logger.warn('Hybrid transport: partial success', {
                nats_success: natsSuccess,
                kafka_success: kafkaSuccess
            });
            this.metrics.hybrid.partialSuccess++;
        } else {
            logger.error('Hybrid transport: both failed');
            this.metrics.hybrid.totalFailures++;
        }
    }

    /**
     * Send via single transport (fallback mode)
     */
    async sendSingle(natsSubject, kafkaTopic, messageEnvelope, results) {
        if (this.status.nats.connected) {
            // Use NATS
            results.nats = await this.publishViaNATS(natsSubject, messageEnvelope);
        } else if (this.status.kafka.connected) {
            // Use Kafka
            results.kafka = await this.publishViaKafka(kafkaTopic, messageEnvelope);
        } else {
            throw new Error('No transport available');
        }
    }

    /**
     * Publish via NATS
     */
    async publishViaNATS(subject, messageEnvelope) {
        const startTime = Date.now();

        try {
            if (!this.status.nats.connected) {
                throw new Error('NATS not connected');
            }

            // Serialize data
            const serializedData = this.serializeForNATS(messageEnvelope);

            // Publish
            this.natsClient.publish(subject, serializedData);

            const latency = Date.now() - startTime;
            this.metrics.nats.published++;
            this.metrics.nats.avgLatency = (this.metrics.nats.avgLatency * 0.9) + (latency * 0.1);

            return { success: true, latency, transport: 'nats' };

        } catch (error) {
            this.metrics.nats.errors++;
            this.status.nats.lastError = error;
            throw error;
        }
    }

    /**
     * Publish via Kafka
     */
    async publishViaKafka(topic, messageEnvelope) {
        const startTime = Date.now();

        try {
            if (!this.status.kafka.connected) {
                throw new Error('Kafka not connected');
            }

            // Prepare Kafka message
            const kafkaMessage = {
                topic: topic,
                messages: [{
                    key: messageEnvelope.metadata?.userId || 'default',
                    value: this.serializeForKafka(messageEnvelope),
                    partition: this.getKafkaPartition(messageEnvelope.metadata?.userId),
                    headers: {
                        correlationId: messageEnvelope.metadata?.correlationId,
                        source: messageEnvelope.metadata?.source_service || 'unknown',
                        timestamp: Date.now().toString()
                    }
                }]
            };

            // Send to Kafka
            const result = await this.kafkaProducer.send(kafkaMessage);

            const latency = Date.now() - startTime;
            this.metrics.kafka.published++;
            this.metrics.kafka.avgLatency = (this.metrics.kafka.avgLatency * 0.9) + (latency * 0.1);

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
            throw error;
        }
    }

    /**
     * Prepare message envelope
     */
    prepareMessage(data, destination, options) {
        return {
            data: data,
            metadata: {
                timestamp: Date.now(),
                correlationId: options.correlationId || this.generateCorrelationId(),
                source_service: options.metadata?.source_service,
                destination_service: destination,
                userId: options.metadata?.userId,
                ...options.metadata
            }
        };
    }

    /**
     * Get NATS subject
     */
    getNATSSubject(destination, options) {
        const baseSubject = options.natsSubject || `${destination}.input`;
        return baseSubject;
    }

    /**
     * Get Kafka topic
     */
    getKafkaTopic(destination, options) {
        const baseTopic = options.kafkaTopic || `${destination}-input`;
        return baseTopic;
    }

    /**
     * Serialize data for NATS
     */
    serializeForNATS(messageEnvelope) {
        if (Buffer.isBuffer(messageEnvelope.data)) {
            return messageEnvelope.data;
        }
        return Buffer.from(JSON.stringify(messageEnvelope), 'utf8');
    }

    /**
     * Serialize data for Kafka
     */
    serializeForKafka(messageEnvelope) {
        if (Buffer.isBuffer(messageEnvelope.data)) {
            return messageEnvelope.data;
        }
        return Buffer.from(JSON.stringify(messageEnvelope), 'utf8');
    }

    /**
     * Get Kafka partition for consistent user routing
     */
    getKafkaPartition(userId) {
        if (!userId) return 0;

        let hash = 0;
        for (let i = 0; i < userId.length; i++) {
            hash = ((hash << 5) - hash + userId.charCodeAt(i)) & 0xffffffff;
        }

        // Assume 3 partitions by default
        return Math.abs(hash) % 3;
    }

    /**
     * Receive messages (consumer)
     */
    async receive(source, handler) {
        const consumers = [];

        // NATS subscription
        if (this.status.nats.connected) {
            const natsSubject = `${source}.output`;
            const subscription = this.natsClient.subscribe(natsSubject);

            (async () => {
                for await (const msg of subscription) {
                    try {
                        const data = JSON.parse(msg.data.toString());
                        await handler(data, 'nats');
                    } catch (error) {
                        logger.error('NATS message processing error', { error });
                    }
                }
            })();

            consumers.push({ type: 'nats', subscription });
        }

        // Kafka subscription
        if (this.status.kafka.connected) {
            const kafkaConsumer = this.kafkaClient.consumer({
                groupId: `${this.config.kafka.clientId}-consumer`
            });

            await kafkaConsumer.connect();
            await kafkaConsumer.subscribe({
                topic: `${source}-output`,
                fromBeginning: false
            });

            await kafkaConsumer.run({
                eachMessage: async ({ topic, partition, message }) => {
                    try {
                        const data = JSON.parse(message.value.toString());
                        await handler(data, 'kafka');
                    } catch (error) {
                        logger.error('Kafka message processing error', { error });
                    }
                }
            });

            consumers.push({ type: 'kafka', consumer: kafkaConsumer });
        }

        return consumers;
    }

    /**
     * Update metrics
     */
    updateMetrics(results, totalLatency) {
        // Individual transport metrics are updated in publish methods
        // This updates overall metrics
    }

    /**
     * Start health monitoring
     */
    startHealthMonitoring() {
        setInterval(async () => {
            await this.checkHealth();
        }, 30000); // Every 30 seconds
    }

    /**
     * Check health and attempt reconnection
     */
    async checkHealth() {
        // Check NATS
        if (!this.status.nats.connected && this.natsClient) {
            try {
                logger.info('Attempting NATS reconnection');
                await this.initializeNATS();
            } catch (error) {
                logger.error('NATS reconnection failed', { error });
            }
        }

        // Check Kafka
        if (!this.status.kafka.connected && this.kafkaProducer) {
            try {
                logger.info('Attempting Kafka reconnection');
                await this.initializeKafka();
            } catch (error) {
                logger.error('Kafka reconnection failed', { error });
            }
        }

        this.emit('health_check', {
            nats: this.status.nats,
            kafka: this.status.kafka,
            metrics: this.metrics
        });
    }

    /**
     * Health check
     */
    async healthCheck() {
        return {
            status: (this.status.nats.connected || this.status.kafka.connected) ? 'healthy' : 'unhealthy',
            nats: {
                connected: this.status.nats.connected,
                error: this.status.nats.lastError?.message
            },
            kafka: {
                connected: this.status.kafka.connected,
                error: this.status.kafka.lastError?.message
            },
            metrics: this.metrics
        };
    }

    /**
     * Generate correlation ID
     */
    generateCorrelationId() {
        return `nats_kafka_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Graceful shutdown
     */
    async shutdown() {
        logger.info('Shutting down NATS+Kafka adapter');

        try {
            const shutdownPromises = [];

            if (this.natsClient) {
                shutdownPromises.push(this.natsClient.close());
            }

            if (this.kafkaProducer) {
                shutdownPromises.push(this.kafkaProducer.disconnect());
            }

            if (this.kafkaConsumer) {
                shutdownPromises.push(this.kafkaConsumer.disconnect());
            }

            await Promise.all(shutdownPromises);
            logger.info('NATS+Kafka adapter shutdown complete');

        } catch (error) {
            logger.error('Error during NATS+Kafka adapter shutdown', { error });
        }
    }
}

module.exports = NATSKafkaAdapter;