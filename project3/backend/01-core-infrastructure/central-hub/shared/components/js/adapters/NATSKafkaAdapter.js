/**
 * NATS+Kafka Hybrid Transport Adapter
 * High-throughput transport untuk real-time trading data
 * Combines NATS speed dengan Kafka durability
 */

const { connect } = require('nats');
const { Kafka } = require('kafkajs');
const EventEmitter = require('events');

class NATSKafkaAdapter extends EventEmitter {
    constructor(config = {}) {
        super();

        this.config = {
            // NATS configuration
            nats_url: config.nats_url || process.env.NATS_URL || 'nats://localhost:4222',
            nats_options: config.nats_options || {},

            // Kafka configuration
            kafka_brokers: config.kafka_brokers || process.env.KAFKA_BROKERS?.split(',') || ['suho-kafka:9092'],
            kafka_client_id: config.kafka_client_id || 'suho-trading-client',
            kafka_options: config.kafka_options || {},

            // Hybrid configuration
            use_hybrid: config.use_hybrid !== false, // Default true
            kafka_topics_prefix: config.kafka_topics_prefix || 'suho-trading',
            nats_subjects_prefix: config.nats_subjects_prefix || 'suho.trading',

            // Performance settings
            max_reconnect_attempts: config.max_reconnect_attempts || 10,
            reconnect_delay: config.reconnect_delay || 2000,
            message_timeout: config.message_timeout || 30000,

            ...config
        };

        // Connection instances
        this.nats_connection = null;
        this.kafka_instance = null;
        this.kafka_producer = null;
        this.kafka_consumer = null;

        // State tracking
        this.is_connected = false;
        this.reconnect_attempts = 0;
        this.message_stats = {
            sent: 0,
            received: 0,
            errors: 0,
            nats_messages: 0,
            kafka_messages: 0
        };

        // Message handlers
        this.subscriptions = new Map();
    }

    async initialize() {
        console.log('Initializing NATS+Kafka adapter...');

        try {
            // Initialize NATS connection
            await this._initializeNATS();

            // Initialize Kafka connection
            await this._initializeKafka();

            this.is_connected = true;
            this.reconnect_attempts = 0;

            console.log('NATS+Kafka adapter initialized successfully');
            this.emit('connected');

        } catch (error) {
            console.error(`Failed to initialize NATS+Kafka adapter: ${error.message}`);
            throw error;
        }
    }

    async _initializeNATS() {
        const nats_options = {
            servers: this.config.nats_url,
            maxReconnectAttempts: this.config.max_reconnect_attempts,
            reconnectTimeWait: this.config.reconnect_delay,
            ...this.config.nats_options
        };

        this.nats_connection = await connect(nats_options);

        // Handle NATS events
        this.nats_connection.addEventListener('disconnect', () => {
            console.warn('NATS disconnected');
            this.emit('nats_disconnected');
        });

        this.nats_connection.addEventListener('reconnect', () => {
            console.log('NATS reconnected');
            this.emit('nats_reconnected');
        });

        console.log('NATS connection established');
    }

    async _initializeKafka() {
        const kafka_config = {
            clientId: this.config.kafka_client_id,
            brokers: this.config.kafka_brokers,
            retry: {
                initialRetryTime: 100,
                retries: this.config.max_reconnect_attempts
            },
            ...this.config.kafka_options
        };

        this.kafka_instance = new Kafka(kafka_config);
        this.kafka_producer = this.kafka_instance.producer();
        this.kafka_consumer = this.kafka_instance.consumer({
            groupId: `${this.config.kafka_client_id}-group`
        });

        await this.kafka_producer.connect();
        await this.kafka_consumer.connect();

        console.log('Kafka connections established');
    }

    async send(data, destination, options = {}) {
        if (!this.is_connected) {
            throw new Error('NATS+Kafka adapter not connected');
        }

        const message_type = options.message_type || this._inferMessageType(data);
        const use_hybrid = options.use_hybrid !== false && this.config.use_hybrid;

        try {
            let results = {};

            if (use_hybrid) {
                // Send via both NATS (speed) and Kafka (durability)
                const [nats_result, kafka_result] = await Promise.allSettled([
                    this._sendViaNATS(data, destination, message_type, options),
                    this._sendViaKafka(data, destination, message_type, options)
                ]);

                results.nats = nats_result.status === 'fulfilled' ? nats_result.value : nats_result.reason;
                results.kafka = kafka_result.status === 'fulfilled' ? kafka_result.value : kafka_result.reason;

                // Consider successful if at least NATS succeeded (for speed)
                if (nats_result.status === 'fulfilled') {
                    this.message_stats.sent++;
                    this.message_stats.nats_messages++;
                    if (kafka_result.status === 'fulfilled') {
                        this.message_stats.kafka_messages++;
                    }
                    return results;
                } else {
                    throw nats_result.reason;
                }

            } else {
                // Use single transport based on message characteristics
                const preferred_transport = this._selectOptimalTransport(message_type, data, options);

                if (preferred_transport === 'nats') {
                    results.nats = await this._sendViaNATS(data, destination, message_type, options);
                    this.message_stats.nats_messages++;
                } else {
                    results.kafka = await this._sendViaKafka(data, destination, message_type, options);
                    this.message_stats.kafka_messages++;
                }

                this.message_stats.sent++;
                return results;
            }

        } catch (error) {
            this.message_stats.errors++;
            console.error(`Failed to send message: ${error.message}`);
            throw error;
        }
    }

    async _sendViaNATS(data, destination, message_type, options) {
        const subject = this._buildNATSSubject(destination, message_type);
        const message = this._formatMessage(data, options);

        if (options.request_reply) {
            // Request-reply pattern
            const timeout = options.timeout || this.config.message_timeout;
            const response = await this.nats_connection.request(subject, message, { timeout });
            return this._parseMessage(response.data);
        } else {
            // Publish pattern
            this.nats_connection.publish(subject, message);
            return { transport: 'nats', subject, timestamp: new Date().toISOString() };
        }
    }

    async _sendViaKafka(data, destination, message_type, options) {
        const topic = this._buildKafkaTopic(destination, message_type);
        const message = {
            key: options.partition_key || destination,
            value: this._formatMessage(data, options),
            timestamp: Date.now(),
            headers: {
                'message-type': message_type,
                'destination': destination,
                'correlation-id': options.correlation_id || ''
            }
        };

        const result = await this.kafka_producer.send({
            topic,
            messages: [message]
        });

        return {
            transport: 'kafka',
            topic,
            partition: result[0].partition,
            offset: result[0].baseOffset,
            timestamp: new Date().toISOString()
        };
    }

    async subscribe(destination, message_type, handler, options = {}) {
        const subscription_id = `${destination}:${message_type}`;

        if (this.subscriptions.has(subscription_id)) {
            throw new Error(`Already subscribed to ${subscription_id}`);
        }

        const subscription_info = {
            destination,
            message_type,
            handler,
            options,
            nats_subscription: null,
            kafka_subscription: null
        };

        try {
            // Subscribe via NATS for real-time
            if (options.enable_nats !== false) {
                const subject = this._buildNATSSubject(destination, message_type);
                const nats_sub = this.nats_connection.subscribe(subject);

                (async () => {
                    for await (const msg of nats_sub) {
                        try {
                            const parsed_data = this._parseMessage(msg.data);
                            await handler(parsed_data, {
                                transport: 'nats',
                                subject: msg.subject,
                                reply: msg.reply
                            });
                            this.message_stats.received++;
                        } catch (error) {
                            console.error(`NATS message handler error: ${error.message}`);
                            this.message_stats.errors++;
                        }
                    }
                })();

                subscription_info.nats_subscription = nats_sub;
            }

            // Subscribe via Kafka for reliability
            if (options.enable_kafka !== false) {
                const topic = this._buildKafkaTopic(destination, message_type);

                await this.kafka_consumer.subscribe({ topic });

                const kafka_handler = async ({ topic, partition, message }) => {
                    try {
                        const parsed_data = this._parseMessage(message.value);
                        await handler(parsed_data, {
                            transport: 'kafka',
                            topic,
                            partition,
                            offset: message.offset,
                            timestamp: message.timestamp
                        });
                        this.message_stats.received++;
                    } catch (error) {
                        console.error(`Kafka message handler error: ${error.message}`);
                        this.message_stats.errors++;
                    }
                };

                this.kafka_consumer.run({
                    eachMessage: kafka_handler
                });

                subscription_info.kafka_subscription = { topic, handler: kafka_handler };
            }

            this.subscriptions.set(subscription_id, subscription_info);

            console.log(`Subscribed to ${subscription_id}`);
            return subscription_id;

        } catch (error) {
            console.error(`Failed to subscribe to ${subscription_id}: ${error.message}`);
            throw error;
        }
    }

    async unsubscribe(subscription_id) {
        const subscription = this.subscriptions.get(subscription_id);
        if (!subscription) {
            throw new Error(`Subscription not found: ${subscription_id}`);
        }

        try {
            // Unsubscribe from NATS
            if (subscription.nats_subscription) {
                subscription.nats_subscription.unsubscribe();
            }

            // Unsubscribe from Kafka (more complex - would need to stop consumer)
            if (subscription.kafka_subscription) {
                // Note: Kafka consumer unsubscription is more complex
                // In production, you might want to manage this differently
                console.warn('Kafka unsubscription not fully implemented');
            }

            this.subscriptions.delete(subscription_id);
            console.log(`Unsubscribed from ${subscription_id}`);

        } catch (error) {
            console.error(`Failed to unsubscribe from ${subscription_id}: ${error.message}`);
            throw error;
        }
    }

    _inferMessageType(data) {
        if (data.message_type) return data.message_type;
        if (data.type) return data.type;
        if (data.symbols && Array.isArray(data.symbols)) return 'price_stream';
        if (data.command || data.action) return 'trading_command';
        return 'generic';
    }

    _selectOptimalTransport(message_type, data, options) {
        // High-frequency or real-time -> NATS
        const high_frequency_types = ['price_stream', 'tick_data', 'heartbeat'];
        if (high_frequency_types.includes(message_type) || options.real_time) {
            return 'nats';
        }

        // Important data that needs durability -> Kafka
        const durable_types = ['trading_command', 'execution_confirm', 'account_update'];
        if (durable_types.includes(message_type) || options.durable) {
            return 'kafka';
        }

        // Default to NATS for speed
        return 'nats';
    }

    _buildNATSSubject(destination, message_type) {
        return `${this.config.nats_subjects_prefix}.${destination}.${message_type}`;
    }

    _buildKafkaTopic(destination, message_type) {
        return `${this.config.kafka_topics_prefix}-${destination}-${message_type}`;
    }

    _formatMessage(data, options) {
        if (Buffer.isBuffer(data)) {
            return data;
        }

        const message = {
            data,
            metadata: {
                timestamp: new Date().toISOString(),
                correlation_id: options.correlation_id,
                source: options.source || 'unknown'
            }
        };

        return JSON.stringify(message);
    }

    _parseMessage(raw_data) {
        if (Buffer.isBuffer(raw_data)) {
            // Try to parse as JSON, fallback to raw buffer
            try {
                return JSON.parse(raw_data.toString());
            } catch {
                return raw_data;
            }
        }

        if (typeof raw_data === 'string') {
            try {
                return JSON.parse(raw_data);
            } catch {
                return raw_data;
            }
        }

        return raw_data;
    }

    async healthCheck() {
        const health = {
            adapter: 'NATSKafkaAdapter',
            status: 'healthy',
            timestamp: new Date().toISOString(),
            connections: {},
            stats: this.message_stats
        };

        try {
            // Check NATS connection
            if (this.nats_connection) {
                health.connections.nats = {
                    status: this.nats_connection.isClosed() ? 'disconnected' : 'connected',
                    servers: this.nats_connection.getServerInfo()
                };
            } else {
                health.connections.nats = { status: 'not_initialized' };
            }

            // Check Kafka connections
            if (this.kafka_producer && this.kafka_consumer) {
                // Kafka doesn't have simple health check, so we'll assume healthy if connections exist
                health.connections.kafka = {
                    status: 'connected',
                    producer: 'healthy',
                    consumer: 'healthy'
                };
            } else {
                health.connections.kafka = { status: 'not_initialized' };
            }

            // Overall status
            const nats_healthy = health.connections.nats.status === 'connected';
            const kafka_healthy = health.connections.kafka.status === 'connected';

            if (!nats_healthy && !kafka_healthy) {
                health.status = 'unhealthy';
            } else if (!nats_healthy || !kafka_healthy) {
                health.status = 'degraded';
            }

        } catch (error) {
            health.status = 'error';
            health.error = error.message;
        }

        return health;
    }

    async shutdown() {
        console.log('Shutting down NATS+Kafka adapter...');

        try {
            // Unsubscribe from all subscriptions
            for (const subscription_id of this.subscriptions.keys()) {
                await this.unsubscribe(subscription_id);
            }

            // Close NATS connection
            if (this.nats_connection) {
                await this.nats_connection.close();
                this.nats_connection = null;
            }

            // Close Kafka connections
            if (this.kafka_producer) {
                await this.kafka_producer.disconnect();
                this.kafka_producer = null;
            }

            if (this.kafka_consumer) {
                await this.kafka_consumer.disconnect();
                this.kafka_consumer = null;
            }

            this.is_connected = false;

            console.log('NATS+Kafka adapter shutdown complete');
            this.emit('disconnected');

        } catch (error) {
            console.error(`Error during shutdown: ${error.message}`);
            throw error;
        }
    }

    getStats() {
        return {
            ...this.message_stats,
            subscriptions: this.subscriptions.size,
            is_connected: this.is_connected,
            reconnect_attempts: this.reconnect_attempts
        };
    }
}

module.exports = NATSKafkaAdapter;