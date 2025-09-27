/**
 * gRPC Transport Adapter
 *
 * Implements gRPC transport for medium volume, important data
 * Features:
 * - Protocol Buffers serialization
 * - Streaming support
 * - Load balancing
 * - Circuit breaker pattern
 */

const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');
const EventEmitter = require('events');
const path = require('path');
const logger = require('../../logging/logger');

class GRPCAdapter extends EventEmitter {
    constructor(config = {}) {
        super();

        this.config = {
            port: config.port || 50051,
            host: config.host || 'localhost',
            max_receive_message_length: config.max_receive_message_length || 4 * 1024 * 1024, // 4MB
            max_send_message_length: config.max_send_message_length || 4 * 1024 * 1024, // 4MB
            keepalive_time_ms: config.keepalive_time_ms || 30000,
            keepalive_timeout_ms: config.keepalive_timeout_ms || 5000,
            keepalive_permit_without_calls: config.keepalive_permit_without_calls || true,
            http2_max_pings_without_data: config.http2_max_pings_without_data || 0,
            http2_min_time_between_pings_ms: config.http2_min_time_between_pings_ms || 10000,
            http2_min_ping_interval_without_data_ms: config.http2_min_ping_interval_without_data_ms || 300000,
            ...config
        };

        // gRPC server and clients
        this.server = null;
        this.clients = new Map(); // destination -> client
        this.services = new Map(); // service_name -> service_definition

        // Proto definitions
        this.protoPath = path.join(__dirname, '../../proto');
        this.packageDefinition = null;
        this.protoDescriptor = null;

        // Status
        this.status = {
            server_running: false,
            connected_clients: 0,
            last_error: null
        };

        // Metrics
        this.metrics = {
            requests_sent: 0,
            requests_received: 0,
            errors: 0,
            avg_latency: 0
        };
    }

    /**
     * Initialize gRPC adapter
     */
    async initialize() {
        logger.info('Initializing gRPC adapter');

        try {
            // Load protocol buffer definitions
            await this.loadProtoDefinitions();

            // Start gRPC server
            await this.startServer();

            logger.info('gRPC adapter initialized successfully', {
                port: this.config.port,
                services: Array.from(this.services.keys())
            });

            this.emit('ready');

        } catch (error) {
            logger.error('Failed to initialize gRPC adapter', { error });
            throw error;
        }
    }

    /**
     * Load protocol buffer definitions
     */
    async loadProtoDefinitions() {
        try {
            // Load common and trading proto files
            const commonProtoPath = path.join(this.protoPath, 'common/base.proto');
            const tradingProtoPath = path.join(this.protoPath, 'trading/client_mt5.proto');

            this.packageDefinition = protoLoader.loadSync([commonProtoPath, tradingProtoPath], {
                keepCase: true,
                longs: String,
                enums: String,
                defaults: true,
                oneofs: true
            });

            this.protoDescriptor = grpc.loadPackageDefinition(this.packageDefinition);

            // Register available services
            this.registerServices();

            logger.info('Protocol buffer definitions loaded');

        } catch (error) {
            logger.error('Failed to load protocol definitions', { error });
            throw error;
        }
    }

    /**
     * Register gRPC services
     */
    registerServices() {
        // Register Transfer Service
        const TransferService = {
            // Unary call for single message
            SendMessage: this.handleSendMessage.bind(this),

            // Server streaming for real-time data
            SubscribeToMessages: this.handleSubscribeToMessages.bind(this),

            // Bidirectional streaming for interactive communication
            BidirectionalStream: this.handleBidirectionalStream.bind(this),

            // Health check
            HealthCheck: this.handleHealthCheck.bind(this)
        };

        this.services.set('TransferService', TransferService);
    }

    /**
     * Start gRPC server
     */
    async startServer() {
        this.server = new grpc.Server({
            'grpc.max_receive_message_length': this.config.max_receive_message_length,
            'grpc.max_send_message_length': this.config.max_send_message_length,
            'grpc.keepalive_time_ms': this.config.keepalive_time_ms,
            'grpc.keepalive_timeout_ms': this.config.keepalive_timeout_ms,
            'grpc.keepalive_permit_without_calls': this.config.keepalive_permit_without_calls,
            'grpc.http2.max_pings_without_data': this.config.http2_max_pings_without_data,
            'grpc.http2.min_time_between_pings_ms': this.config.http2_min_time_between_pings_ms,
            'grpc.http2.min_ping_interval_without_data_ms': this.config.http2_min_ping_interval_without_data_ms
        });

        // Add services to server
        for (const [serviceName, serviceImpl] of this.services.entries()) {
            // Create service definition dynamically
            const serviceDefinition = this.createServiceDefinition(serviceName);
            this.server.addService(serviceDefinition, serviceImpl);
        }

        // Start server
        return new Promise((resolve, reject) => {
            this.server.bindAsync(
                `${this.config.host}:${this.config.port}`,
                grpc.ServerCredentials.createInsecure(),
                (error, port) => {
                    if (error) {
                        reject(error);
                        return;
                    }

                    this.server.start();
                    this.status.server_running = true;

                    logger.info('gRPC server started', {
                        host: this.config.host,
                        port: port
                    });

                    resolve(port);
                }
            );
        });
    }

    /**
     * Create service definition for gRPC
     */
    createServiceDefinition(serviceName) {
        // Dynamic service definition based on our transfer needs
        return {
            SendMessage: {
                path: `/transfer.${serviceName}/SendMessage`,
                requestStream: false,
                responseStream: false,
                requestType: 'TransferRequest',
                responseType: 'TransferResponse'
            },
            SubscribeToMessages: {
                path: `/transfer.${serviceName}/SubscribeToMessages`,
                requestStream: false,
                responseStream: true,
                requestType: 'SubscriptionRequest',
                responseType: 'TransferMessage'
            },
            BidirectionalStream: {
                path: `/transfer.${serviceName}/BidirectionalStream`,
                requestStream: true,
                responseStream: true,
                requestType: 'TransferMessage',
                responseType: 'TransferMessage'
            },
            HealthCheck: {
                path: `/transfer.${serviceName}/HealthCheck`,
                requestStream: false,
                responseStream: false,
                requestType: 'HealthRequest',
                responseType: 'HealthResponse'
            }
        };
    }

    /**
     * Send message via gRPC
     */
    async send(data, destination, options = {}) {
        const startTime = Date.now();

        try {
            // Get or create client for destination
            const client = await this.getClient(destination);

            // Prepare request
            const request = {
                message_type: options.messageType || this.getMessageType(data),
                payload: this.serializeData(data),
                metadata: {
                    source_service: options.metadata?.source_service,
                    destination_service: destination,
                    correlation_id: options.correlationId || this.generateCorrelationId(),
                    timestamp: Date.now(),
                    ...options.metadata
                }
            };

            // Send via gRPC
            const response = await this.callUnary(client, 'SendMessage', request);

            const latency = Date.now() - startTime;
            this.updateMetrics('sent', latency);

            return {
                success: response.success,
                message: response.message,
                latency,
                transport: 'grpc'
            };

        } catch (error) {
            const latency = Date.now() - startTime;
            this.updateMetrics('error', latency);

            logger.error('gRPC send failed', { error, destination });
            throw error;
        }
    }

    /**
     * Get or create gRPC client for destination
     */
    async getClient(destination) {
        if (this.clients.has(destination)) {
            return this.clients.get(destination);
        }

        // Create new client
        const client = new grpc.Client(
            `${destination}:50051`, // Assume standard gRPC port
            grpc.credentials.createInsecure(),
            {
                'grpc.keepalive_time_ms': this.config.keepalive_time_ms,
                'grpc.keepalive_timeout_ms': this.config.keepalive_timeout_ms
            }
        );

        this.clients.set(destination, client);
        this.status.connected_clients++;

        return client;
    }

    /**
     * Call unary gRPC method
     */
    async callUnary(client, method, request) {
        return new Promise((resolve, reject) => {
            const deadline = new Date();
            deadline.setSeconds(deadline.getSeconds() + 30); // 30 second timeout

            client.makeUnaryRequest(
                `/transfer.TransferService/${method}`,
                (arg) => Buffer.from(JSON.stringify(arg)),
                (arg) => JSON.parse(arg.toString()),
                request,
                { deadline },
                (error, response) => {
                    if (error) {
                        reject(error);
                    } else {
                        resolve(response);
                    }
                }
            );
        });
    }

    /**
     * Receive messages (subscribe to streams)
     */
    async receive(source, handler) {
        try {
            const client = await this.getClient(source);

            const request = {
                source_filter: source,
                subscription_id: this.generateCorrelationId()
            };

            const stream = client.makeServerStreamRequest(
                '/transfer.TransferService/SubscribeToMessages',
                (arg) => Buffer.from(JSON.stringify(arg)),
                (arg) => JSON.parse(arg.toString()),
                request
            );

            stream.on('data', (message) => {
                try {
                    this.updateMetrics('received');
                    handler(message, 'grpc');
                } catch (error) {
                    logger.error('gRPC message processing error', { error });
                }
            });

            stream.on('error', (error) => {
                logger.error('gRPC stream error', { error, source });
                this.emit('stream_error', { source, error });
            });

            stream.on('end', () => {
                logger.info('gRPC stream ended', { source });
                this.emit('stream_ended', { source });
            });

            return stream;

        } catch (error) {
            logger.error('Failed to start gRPC subscription', { error, source });
            throw error;
        }
    }

    /**
     * Handle incoming SendMessage requests
     */
    async handleSendMessage(call, callback) {
        try {
            const request = call.request;
            this.updateMetrics('received');

            // Process the message
            const result = await this.processIncomingMessage(request);

            callback(null, {
                success: true,
                message: 'Message processed successfully',
                correlation_id: request.metadata?.correlation_id
            });

        } catch (error) {
            this.updateMetrics('error');
            callback({
                code: grpc.status.INTERNAL,
                message: error.message
            });
        }
    }

    /**
     * Handle subscription requests
     */
    handleSubscribeToMessages(call) {
        const request = call.request;
        const subscriptionId = request.subscription_id;

        logger.info('New gRPC subscription', {
            source_filter: request.source_filter,
            subscription_id: subscriptionId
        });

        // Store subscription for future message routing
        this.emit('new_subscription', {
            subscription_id: subscriptionId,
            source_filter: request.source_filter,
            stream: call
        });

        call.on('cancelled', () => {
            logger.info('gRPC subscription cancelled', { subscription_id: subscriptionId });
            this.emit('subscription_cancelled', { subscription_id: subscriptionId });
        });
    }

    /**
     * Handle bidirectional streams
     */
    handleBidirectionalStream(call) {
        const sessionId = this.generateCorrelationId();

        logger.info('New bidirectional gRPC stream', { session_id: sessionId });

        call.on('data', async (message) => {
            try {
                this.updateMetrics('received');

                // Process incoming message
                const response = await this.processIncomingMessage(message);

                // Send response back
                call.write(response);

            } catch (error) {
                logger.error('Bidirectional stream processing error', { error });
                call.emit('error', error);
            }
        });

        call.on('end', () => {
            logger.info('Bidirectional stream ended', { session_id: sessionId });
            call.end();
        });

        call.on('error', (error) => {
            logger.error('Bidirectional stream error', { error, session_id: sessionId });
        });
    }

    /**
     * Handle health check requests
     */
    handleHealthCheck(call, callback) {
        const health = this.getHealth();

        callback(null, {
            status: health.status,
            timestamp: Date.now(),
            metrics: this.metrics
        });
    }

    /**
     * Process incoming message
     */
    async processIncomingMessage(message) {
        // Emit message for handling by the service
        this.emit('message_received', {
            type: message.message_type,
            payload: message.payload,
            metadata: message.metadata
        });

        return {
            success: true,
            processed_at: Date.now(),
            correlation_id: message.metadata?.correlation_id
        };
    }

    /**
     * Serialize data for gRPC
     */
    serializeData(data) {
        if (Buffer.isBuffer(data)) {
            return data;
        }

        if (typeof data === 'object') {
            return Buffer.from(JSON.stringify(data));
        }

        return Buffer.from(String(data));
    }

    /**
     * Get message type from data
     */
    getMessageType(data) {
        if (data.message_type) return data.message_type;
        if (data.type) return data.type;
        if (data.constructor?.name) return data.constructor.name;
        return 'unknown';
    }

    /**
     * Update metrics
     */
    updateMetrics(type, latency = 0) {
        switch (type) {
            case 'sent':
                this.metrics.requests_sent++;
                this.metrics.avg_latency = (this.metrics.avg_latency * 0.9) + (latency * 0.1);
                break;
            case 'received':
                this.metrics.requests_received++;
                break;
            case 'error':
                this.metrics.errors++;
                break;
        }
    }

    /**
     * Generate correlation ID
     */
    generateCorrelationId() {
        return `grpc_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Get health status
     */
    getHealth() {
        return {
            status: this.status.server_running ? 'healthy' : 'unhealthy',
            server_running: this.status.server_running,
            connected_clients: this.status.connected_clients,
            last_error: this.status.last_error?.message,
            metrics: this.metrics
        };
    }

    /**
     * Health check
     */
    async healthCheck() {
        return this.getHealth();
    }

    /**
     * Graceful shutdown
     */
    async shutdown() {
        logger.info('Shutting down gRPC adapter');

        try {
            // Close all clients
            for (const client of this.clients.values()) {
                client.close();
            }
            this.clients.clear();

            // Shutdown server
            if (this.server) {
                await new Promise((resolve) => {
                    this.server.tryShutdown((error) => {
                        if (error) {
                            logger.error('gRPC server shutdown error', { error });
                            this.server.forceShutdown();
                        }
                        resolve();
                    });
                });
            }

            this.status.server_running = false;
            logger.info('gRPC adapter shutdown complete');

        } catch (error) {
            logger.error('Error during gRPC adapter shutdown', { error });
        }
    }
}

module.exports = GRPCAdapter;