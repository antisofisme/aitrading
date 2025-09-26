/**
 * Bidirectional Routing Engine for API Gateway
 *
 * Implements intelligent message routing between Client-MT5 and backend services
 * based on the bidirectional-routing.md contract specification.
 *
 * Features:
 * - Protocol Buffer to Suho Binary Protocol conversion
 * - Multi-transport routing (HTTP, WebSocket, Message Queue)
 * - Central Hub integration for service discovery
 * - Load balancing and failover
 * - Message transformation and validation
 */

const { EventEmitter } = require('events');
const { SuhoBinaryProtocol } = require('../protocols/suho-binary-protocol');

/**
 * Route Configuration - Corrected Flow
 *
 * INPUTS: Data yang MASUK ke API Gateway (dari mana saja)
 * OUTPUTS: Data yang KELUAR dari API Gateway (ke mana saja)
 */
const ROUTE_CONFIG = {
    // INPUT ROUTES: Data masuk ke API Gateway
    inputs: {
        // Input dari Client-MT5 (Binary Protocol via WebSocket)
        'client-mt5': {
            channels: ['trading', 'price-stream'],
            messageTypes: ['price_stream', 'account_profile', 'trading_command', 'execution_confirm', 'heartbeat'],
            protocol: 'suho-binary',
            priority: 'high',
            transform: 'binary-to-protobuf'
        },

        // Input dari Trading Engine (Protocol Buffers via HTTP POST)
        'trading-engine': {
            messageTypes: ['TradingOutput'],
            protocol: 'protobuf',
            priority: 'high',
            transform: 'protobuf-passthrough'
        },

        // Input dari Analytics Service (Protocol Buffers via HTTP POST)
        'analytics-service': {
            messageTypes: ['AnalyticsOutput'],
            protocol: 'protobuf',
            priority: 'medium',
            transform: 'protobuf-passthrough'
        },

        // Input dari ML Processing (Protocol Buffers via HTTP POST)
        'ml-processing': {
            messageTypes: ['MLOutput'],
            protocol: 'protobuf',
            priority: 'high',
            transform: 'protobuf-passthrough'
        },

        // Input dari Notification Hub (Protocol Buffers via HTTP POST)
        'notification-hub': {
            messageTypes: ['NotificationInput'],
            protocol: 'protobuf',
            priority: 'medium',
            transform: 'protobuf-passthrough'
        }
    },

    // OUTPUT ROUTES: Data keluar dari API Gateway
    outputs: {
        // Output ke Client-MT5 (Binary Protocol via WebSocket)
        'to-client-mt5-execution': {
            channel: 'trading',
            messageTypes: ['trading_command', 'execution_response', 'system_status'],
            protocol: 'suho-binary',
            priority: 'high',
            transform: 'protobuf-to-binary'
        },

        // Output ke Frontend Dashboard (JSON via WebSocket)
        'to-frontend-websocket': {
            messageTypes: ['trading_status', 'system_metrics', 'market_data', 'analytics'],
            protocol: 'json-websocket',
            priority: 'medium',
            transform: 'protobuf-to-json'
        },

        // Output ke Telegram Bot (JSON via HTTP Webhook)
        'to-telegram-webhook': {
            messageTypes: ['trading_signal', 'execution_confirm', 'performance_alert', 'system_alert'],
            protocol: 'telegram-api',
            priority: 'medium',
            transform: 'protobuf-to-telegram'
        },

        // Output ke Notification Channels (JSON via HTTP)
        'to-notification-channels': {
            messageTypes: ['email_notification', 'sms_notification', 'push_notification'],
            protocol: 'multi-channel',
            priority: 'low',
            transform: 'protobuf-to-notification'
        },

        // Output ke Backend Services (Protocol Buffers via HTTP/gRPC)
        'to-trading-engine': {
            messageTypes: ['price_stream', 'trading_command', 'account_profile'],
            protocol: 'protobuf-http',
            priority: 'high',
            transform: 'protobuf-to-protobuf'
        },

        'to-ml-processing': {
            messageTypes: ['price_stream', 'market_data'],
            protocol: 'protobuf-http',
            priority: 'high',
            transform: 'protobuf-to-protobuf'
        },

        'to-analytics-service': {
            messageTypes: ['account_profile', 'trading_command', 'execution_confirm', 'price_stream'],
            protocol: 'protobuf-http',
            priority: 'medium',
            transform: 'protobuf-to-protobuf'
        },

        'to-notification-hub': {
            messageTypes: ['trading_alert', 'system_alert', 'performance_alert'],
            protocol: 'protobuf-http',
            priority: 'medium',
            transform: 'protobuf-to-protobuf'
        }
    }
};

/**
 * Bidirectional Router Implementation
 */
class BidirectionalRouter extends EventEmitter {
    constructor(options = {}) {
        super();

        this.options = {
            centralHubUrl: 'http://localhost:3000',
            maxRetries: 3,
            retryDelay: 1000,
            healthCheckInterval: 30000,
            loadBalancingStrategy: 'round_robin',
            ...options
        };

        this.binaryProtocol = new SuhoBinaryProtocol();
        this.serviceRegistry = new Map();
        this.routingTable = new Map();
        this.loadBalancers = new Map();
        this.messageQueue = [];
        this.isProcessing = false;

        this.initializeRoutes();
        this.startHealthMonitoring();
    }

    /**
     * Initialize routing table from configuration
     */
    initializeRoutes() {
        // Setup input routes (backend -> Client-MT5)
        for (const [service, config] of Object.entries(ROUTE_CONFIG.inputs)) {
            this.routingTable.set(`input:${service}`, {
                type: 'input',
                service,
                ...config
            });
        }

        // Setup output routes (Client-MT5 -> backend)
        for (const [source, config] of Object.entries(ROUTE_CONFIG.outputs)) {
            this.routingTable.set(`output:${source}`, {
                type: 'output',
                source,
                ...config
            });
        }

        console.log('[ROUTER] Routing table initialized with', this.routingTable.size, 'routes');
    }

    /**
     * Route INPUT message to appropriate outputs
     * @param {string} sourceInput - Source input identifier (from contracts/inputs/)
     * @param {Object} message - Input message
     * @param {Object} metadata - Message metadata
     */
    async routeInput(sourceInput, message, metadata = {}) {
        try {
            const inputRoute = ROUTE_CONFIG.inputs[sourceInput];

            if (!inputRoute) {
                console.warn(`[ROUTER] No input route found for: ${sourceInput}`);
                return;
            }

            console.log(`[ROUTER] Processing input from ${sourceInput}`);

            // Validate message type
            if (!this.validateMessageType(message, inputRoute.messageTypes)) {
                console.warn(`[ROUTER] Invalid message type for ${sourceInput}`);
                return;
            }

            // Transform input message to internal format (usually protobuf)
            const internalMessage = await this.transformMessage(message, inputRoute.transform, 'to_internal');

            // Determine output destinations based on message type and business logic
            const outputDestinations = this.determineOutputDestinations(sourceInput, message.type, metadata);

            // Route to each output destination
            for (const outputDest of outputDestinations) {
                await this.routeToOutput(outputDest, internalMessage, metadata);
            }

            // Log routing success
            this.logRouting(sourceInput, outputDestinations, 'success');

        } catch (error) {
            console.error(`[ROUTER] Error routing input from ${sourceInput}:`, error);
            this.logRouting(sourceInput, [], 'error', error.message);
        }
    }

    /**
     * Route to specific OUTPUT destination
     * @param {string} outputDest - Output destination (from contracts/outputs/)
     * @param {Object} internalMessage - Internal protocol buffer message
     * @param {Object} metadata - Message metadata
     */
    async routeToOutput(outputDest, internalMessage, metadata = {}) {
        try {
            const outputRoute = ROUTE_CONFIG.outputs[outputDest];

            if (!outputRoute) {
                console.warn(`[ROUTER] No output route found for: ${outputDest}`);
                return;
            }

            console.log(`[ROUTER] Routing to output destination: ${outputDest}`);

            // Transform message to output format
            const outputMessage = await this.transformMessage(internalMessage, outputRoute.transform, 'to_output');

            // Send to appropriate destination based on protocol
            switch (outputRoute.protocol) {
                case 'suho-binary':
                    await this.sendToClientMT5(outputMessage, outputRoute.channel, metadata);
                    break;

                case 'json-websocket':
                    await this.sendToFrontendWebSocket(outputMessage, metadata);
                    break;

                case 'telegram-api':
                    await this.sendToTelegramWebhook(outputMessage, metadata);
                    break;

                case 'multi-channel':
                    await this.sendToNotificationChannels(outputMessage, metadata);
                    break;

                case 'protobuf-http':
                    await this.sendToBackendService(outputMessage, outputDest.replace('to-', ''), metadata);
                    break;

                default:
                    console.warn(`[ROUTER] Unknown output protocol: ${outputRoute.protocol}`);
            }

        } catch (error) {
            console.error(`[ROUTER] Error routing to output ${outputDest}:`, error);
        }
    }

    /**
     * Determine output destinations based on input source and message type
     * @param {string} sourceInput - Source input
     * @param {string} messageType - Message type
     * @param {Object} metadata - Message metadata
     * @returns {Array} Array of output destination names
     */
    determineOutputDestinations(sourceInput, messageType, metadata) {
        const destinations = [];

        // Business logic for routing based on source and message type
        switch (sourceInput) {
            case 'client-mt5':
                if (messageType === 'price_stream') {
                    destinations.push('to-ml-processing', 'to-analytics-service');
                } else if (messageType === 'trading_command') {
                    destinations.push('to-trading-engine', 'to-analytics-service');
                } else if (messageType === 'account_profile') {
                    destinations.push('to-analytics-service');
                } else if (messageType === 'execution_confirm') {
                    destinations.push('to-trading-engine', 'to-analytics-service', 'to-frontend-websocket');
                }
                break;

            case 'trading-engine':
                // Trading Engine output goes to Client-MT5 and Frontend
                destinations.push('to-client-mt5-execution', 'to-frontend-websocket');

                // If it's a signal, also send to Telegram
                if (messageType === 'TradingOutput' && metadata.hasSignals) {
                    destinations.push('to-telegram-webhook');
                }
                break;

            case 'analytics-service':
                // Analytics output goes to Frontend Dashboard
                destinations.push('to-frontend-websocket');

                // Performance alerts go to notifications
                if (metadata.alertLevel && metadata.alertLevel !== 'info') {
                    destinations.push('to-notification-channels');
                }
                break;

            case 'ml-processing':
                // ML predictions go to Trading Engine and Frontend
                destinations.push('to-trading-engine', 'to-frontend-websocket');
                break;

            case 'notification-hub':
                // Notifications go to appropriate channels based on type
                if (metadata.channels) {
                    if (metadata.channels.includes('telegram')) {
                        destinations.push('to-telegram-webhook');
                    }
                    if (metadata.channels.includes('email') || metadata.channels.includes('sms')) {
                        destinations.push('to-notification-channels');
                    }
                    if (metadata.channels.includes('dashboard')) {
                        destinations.push('to-frontend-websocket');
                    }
                }
                break;

            default:
                console.warn(`[ROUTER] Unknown input source for routing: ${sourceInput}`);
        }

        return destinations;
    }

    /**
     * Transform message between different protocols
     * @param {Object} message - Source message
     * @param {string} transformType - Transformation type
     * @param {string} direction - 'to_client' or 'to_backend'
     * @returns {Object} Transformed message
     */
    async transformMessage(message, transformType, direction) {
        switch (transformType) {
            case 'protobuf-to-binary':
                if (direction === 'to_client') {
                    return this.binaryProtocol.fromProtocolBuffer(message);
                }
                break;

            case 'binary-to-protobuf':
                if (direction === 'to_backend') {
                    return this.binaryProtocol.toProtocolBuffer(message);
                }
                break;

            case 'protobuf-to-protobuf':
                // Pass through for backend-to-backend communication
                return message;

            case 'protobuf-to-json':
                return this.protobufToJson(message);

            case 'json-to-protobuf':
                return this.jsonToProtobuf(message);

            default:
                console.warn(`[ROUTER] Unknown transform type: ${transformType}`);
                return message;
        }

        return message;
    }

    /**
     * Send message to Client-MT5
     * @param {Buffer|Object} message - Transformed message
     * @param {string} channel - Target channel
     * @param {Object} metadata - Message metadata
     */
    async sendToClientMT5(message, channel, metadata) {
        try {
            // Extract user information from metadata
            const userId = metadata.userId || metadata.user_id || 'unknown';

            // Determine channel type
            const channelType = channel.includes('trading') ? 'trading' : 'price_stream';

            // Emit event for Client-MT5 handler to pick up
            this.emit('client_mt5_message', {
                userId,
                channel: channelType,
                message,
                metadata
            });

            console.log(`[ROUTER] Message sent to Client-MT5 ${channelType} channel for user ${userId}`);

        } catch (error) {
            console.error('[ROUTER] Error sending to Client-MT5:', error);
            throw error;
        }
    }

    /**
     * Send message to backend service with load balancing
     * @param {Object} message - Protocol Buffer message
     * @param {string} serviceName - Target service name
     * @param {Object} metadata - Message metadata
     */
    async sendToBackendService(message, serviceName, metadata) {
        try {
            // Get available service instances
            const serviceInstances = await this.getServiceInstances(serviceName);

            if (serviceInstances.length === 0) {
                throw new Error(`No available instances for service: ${serviceName}`);
            }

            // Select instance using load balancing
            const targetInstance = this.selectServiceInstance(serviceName, serviceInstances);

            // Add routing metadata
            const routedMessage = {
                ...message,
                routing_metadata: {
                    source: 'api-gateway',
                    target_service: serviceName,
                    target_instance: targetInstance.id,
                    routing_timestamp: Date.now(),
                    correlation_id: metadata.correlationId || this.generateCorrelationId()
                }
            };

            // Send via appropriate transport
            await this.sendViaTransport(routedMessage, targetInstance, metadata);

            console.log(`[ROUTER] Message sent to ${serviceName} instance ${targetInstance.id}`);

        } catch (error) {
            console.error(`[ROUTER] Error sending to ${serviceName}:`, error);

            // Implement retry logic
            await this.retryMessage(message, serviceName, metadata);
        }
    }

    /**
     * Send to Frontend WebSocket
     * @param {Object} message - Formatted message
     * @param {Object} metadata - Message metadata
     */
    async sendToFrontendWebSocket(message, metadata) {
        this.emit('to-frontend-websocket', { message, metadata });
    }

    /**
     * Send to Telegram Webhook
     * @param {Object} message - Formatted message
     * @param {Object} metadata - Message metadata
     */
    async sendToTelegramWebhook(message, metadata) {
        this.emit('to-telegram-webhook', { message, metadata });
    }

    /**
     * Send to Notification Channels
     * @param {Object} message - Formatted message
     * @param {Object} metadata - Message metadata
     */
    async sendToNotificationChannels(message, metadata) {
        this.emit('to-notification-channels', { message, metadata });
    }

    /**
     * Get available service instances from service registry
     * @param {string} serviceName - Service name
     * @returns {Array} Available service instances
     */
    async getServiceInstances(serviceName) {
        // Check local cache first
        if (this.serviceRegistry.has(serviceName)) {
            const cached = this.serviceRegistry.get(serviceName);
            if (Date.now() - cached.timestamp < 30000) { // 30 second cache
                return cached.instances;
            }
        }

        try {
            // Query Central Hub for service instances
            const instances = await this.queryServiceRegistry(serviceName);

            // Update cache
            this.serviceRegistry.set(serviceName, {
                instances,
                timestamp: Date.now()
            });

            return instances;

        } catch (error) {
            console.error(`[ROUTER] Error getting service instances for ${serviceName}:`, error);

            // Return cached data if available, even if stale
            const cached = this.serviceRegistry.get(serviceName);
            return cached ? cached.instances : [];
        }
    }

    /**
     * Select service instance using load balancing strategy
     * @param {string} serviceName - Service name
     * @param {Array} instances - Available instances
     * @returns {Object} Selected instance
     */
    selectServiceInstance(serviceName, instances) {
        if (!this.loadBalancers.has(serviceName)) {
            this.loadBalancers.set(serviceName, {
                strategy: this.options.loadBalancingStrategy,
                roundRobinIndex: 0,
                requestCounts: new Map()
            });
        }

        const balancer = this.loadBalancers.get(serviceName);

        switch (balancer.strategy) {
            case 'round_robin':
                const instance = instances[balancer.roundRobinIndex % instances.length];
                balancer.roundRobinIndex++;
                return instance;

            case 'least_connections':
                return this.selectLeastConnectedInstance(instances, balancer);

            case 'random':
                return instances[Math.floor(Math.random() * instances.length)];

            default:
                return instances[0]; // Fallback to first instance
        }
    }

    /**
     * Send message via appropriate transport
     * @param {Object} message - Message to send
     * @param {Object} instance - Target service instance
     * @param {Object} metadata - Message metadata
     */
    async sendViaTransport(message, instance, metadata) {
        switch (instance.transport) {
            case 'http':
                await this.sendViaHTTP(message, instance, metadata);
                break;

            case 'websocket':
                await this.sendViaWebSocket(message, instance, metadata);
                break;

            case 'kafka':
                await this.sendViaKafka(message, instance, metadata);
                break;

            case 'nats':
                await this.sendViaNATS(message, instance, metadata);
                break;

            default:
                throw new Error(`Unsupported transport: ${instance.transport}`);
        }
    }

    /**
     * Send message via HTTP POST
     * @param {Object} message - Message to send
     * @param {Object} instance - Target instance
     * @param {Object} metadata - Message metadata
     */
    async sendViaHTTP(message, instance, metadata) {
        // Implementation would use HTTP client (axios, fetch, etc.)
        // For now, emit event for HTTP handler
        this.emit('http_message', {
            url: instance.url,
            message,
            headers: {
                'Content-Type': 'application/x-protobuf',
                'X-Correlation-ID': metadata.correlationId || this.generateCorrelationId()
            }
        });
    }

    /**
     * Validate message type against allowed types
     * @param {Object} message - Message to validate
     * @param {Array} allowedTypes - Allowed message types
     * @returns {boolean} True if valid
     */
    validateMessageType(message, allowedTypes) {
        const messageType = message.type || message.constructor.name;
        return allowedTypes.includes(messageType);
    }

    /**
     * Convert Protocol Buffer to JSON
     * @param {Object} protoMessage - Protocol Buffer message
     * @returns {Object} JSON object
     */
    protobufToJson(protoMessage) {
        // Convert Protocol Buffer to plain JSON
        // This would typically use protobuf.js or similar library
        return JSON.parse(JSON.stringify(protoMessage));
    }

    /**
     * Query service registry from Central Hub
     * @param {string} serviceName - Service name
     * @returns {Array} Service instances
     */
    async queryServiceRegistry(serviceName) {
        // Implementation would query Central Hub API
        // For now, return mock data
        return [
            {
                id: `${serviceName}-1`,
                url: `http://localhost:3001/${serviceName}`,
                transport: 'http',
                health: 'healthy',
                load: 0.3
            }
        ];
    }

    /**
     * Start health monitoring for service instances
     */
    startHealthMonitoring() {
        setInterval(async () => {
            for (const [serviceName, cached] of this.serviceRegistry.entries()) {
                for (const instance of cached.instances) {
                    try {
                        await this.checkInstanceHealth(instance);
                    } catch (error) {
                        console.warn(`[ROUTER] Health check failed for ${instance.id}:`, error);
                        // Mark instance as unhealthy
                        instance.health = 'unhealthy';
                    }
                }
            }
        }, this.options.healthCheckInterval);
    }

    /**
     * Check health of service instance
     * @param {Object} instance - Service instance
     */
    async checkInstanceHealth(instance) {
        // Implementation would perform actual health check
        // For now, assume all instances are healthy
        instance.health = 'healthy';
        instance.lastHealthCheck = Date.now();
    }

    /**
     * Retry failed message delivery
     * @param {Object} message - Original message
     * @param {string} serviceName - Target service
     * @param {Object} metadata - Message metadata
     */
    async retryMessage(message, serviceName, metadata) {
        const retries = metadata.retries || 0;

        if (retries >= this.options.maxRetries) {
            console.error(`[ROUTER] Max retries exceeded for ${serviceName}`);
            this.emit('message_failed', { message, serviceName, metadata });
            return;
        }

        // Exponential backoff
        const delay = this.options.retryDelay * Math.pow(2, retries);

        setTimeout(() => {
            this.sendToBackendService(message, serviceName, {
                ...metadata,
                retries: retries + 1
            });
        }, delay);
    }

    /**
     * Log routing operation
     * @param {string} source - Source of message
     * @param {Array} targets - Target destinations
     * @param {string} status - Operation status
     * @param {string} error - Error message (if any)
     */
    logRouting(source, targets, status, error = null) {
        const logEntry = {
            timestamp: new Date().toISOString(),
            source,
            targets,
            status,
            error
        };

        console.log(`[ROUTER-LOG] ${JSON.stringify(logEntry)}`);

        // Emit for monitoring systems
        this.emit('routing_log', logEntry);
    }

    /**
     * Generate unique correlation ID
     * @returns {string} Correlation ID
     */
    generateCorrelationId() {
        return 'route_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    /**
     * Get routing statistics
     * @returns {Object} Routing statistics
     */
    getRoutingStats() {
        return {
            active_routes: this.routingTable.size,
            cached_services: this.serviceRegistry.size,
            load_balancers: this.loadBalancers.size,
            message_queue_size: this.messageQueue.length
        };
    }

    /**
     * Shutdown the router
     */
    shutdown() {
        console.log('[ROUTER] Shutting down bidirectional router...');

        // Clear caches and timers
        this.serviceRegistry.clear();
        this.routingTable.clear();
        this.loadBalancers.clear();
        this.messageQueue = [];

        console.log('[ROUTER] Shutdown complete');
    }
}

module.exports = BidirectionalRouter;