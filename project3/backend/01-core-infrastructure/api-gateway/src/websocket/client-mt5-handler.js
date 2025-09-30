/**
 * Client-MT5 WebSocket Handler
 *
 * Handles dual WebSocket connections for Client-MT5:
 * 1. Trading Commands Channel - AI signals and execution commands
 * 2. Price Streaming Channel - Real-time market data
 *
 * Features:
 * - Suho Binary Protocol support
 * - Automatic protocol detection (binary vs JSON fallback)
 * - Bidirectional routing to backend services
 * - Connection health monitoring
 * - Per-user session management
 */

const WebSocket = require('ws');
const { SuhoBinaryProtocol } = require('../protocols/suho-binary-protocol');
const { EventEmitter } = require('events');
const AuthMiddleware = require('../middleware/auth');

// Simple console logger to avoid ES Module issues
const logger = {
    warn: (msg, data) => console.warn(`[MT5-WARN] ${msg}`, data || ''),
    debug: (msg, data) => console.log(`[MT5-DEBUG] ${msg}`, data || ''),
    info: (msg, data) => console.log(`[MT5-INFO] ${msg}`, data || ''),
    error: (msg, data) => console.error(`[MT5-ERROR] ${msg}`, data || '')
};

// ✅ NEW: Import Client-MT5 handler from webhook transfer method (corrected structure)
const { ClientMT5NatsKafkaHandler } = require('../../contracts/webhook/from-client-mt5');

/**
 * Client-MT5 WebSocket Connection Handler
 */
class ClientMT5Handler extends EventEmitter {
    constructor(options = {}) {
        super();

        this.options = {
            heartbeatInterval: 30000,
            connectionTimeout: 10000,
            maxReconnectAttempts: 5,
            binaryProtocolEnabled: true,
            port: options.port || 8001,
            type: options.type || 'trading',
            ...options
        };

        // Central Hub integration
        this.centralHub = options.centralHub;
        this.config = options.protocolConfig;

        this.binaryProtocol = new SuhoBinaryProtocol();
        this.connections = new Map(); // userId -> connection data
        this.servers = {
            trading: null,
            priceStream: null
        };

        // ✅ NEW: Use contract input handler untuk Client-MT5 data
        this.clientMT5InputHandler = new ClientMT5NatsKafkaHandler({
            enableConversion: false, // TERIMA SAJA, TIDAK CONVERT
            enableValidation: true,
            enableRouting: true
        });

        // Initialize authentication
        this.authMiddleware = new AuthMiddleware({
            jwtSecret: process.env.JWT_SECRET,
            jwtExpiresIn: process.env.JWT_EXPIRES_IN || '24h',
            issuer: process.env.JWT_ISSUER || 'api-gateway',
            audience: process.env.JWT_AUDIENCE || 'suho-trading'
        });

        this.initializeServers();
    }

    /**
     * Initialize the MT5 handler (called by main app)
     */
    async initialize() {
        console.log('[MT5-HANDLER] Initializing Client-MT5 handler...');

        // Start heartbeat monitoring
        this.startHeartbeatMonitoring();

        console.log('[MT5-HANDLER] Client-MT5 handler initialized successfully');
    }

    /**
     * Initialize WebSocket server based on type (single server per instance)
     */
    initializeServers() {
        const serverType = this.options.type || 'trading';
        const port = this.options.port || (serverType === 'price_stream' ? 8002 : 8001);
        const path = serverType === 'price_stream' ? '/ws/price-stream' : '/ws/trading';

        console.log(`[MT5-HANDLER] Initializing ${serverType} server on port ${port}`);

        // Create single server based on type
        if (serverType === 'price_stream') {
            this.servers.priceStream = new WebSocket.Server({
                port: port,
                path: path
            });
            this.setupPriceStreamServer();
            console.log(`[MT5-HANDLER] Price stream WebSocket server: ws://localhost:${port}${path}`);
        } else {
            this.servers.trading = new WebSocket.Server({
                port: port,
                path: path
            });
            this.setupTradingServer();
            console.log(`[MT5-HANDLER] Trading WebSocket server: ws://localhost:${port}${path}`);
        }
    }

    /**
     * Setup Trading Commands WebSocket Server
     */
    setupTradingServer() {
        this.servers.trading.on('connection', async (ws, req) => {
            try {
                // Authenticate WebSocket connection
                const authResult = await this.authMiddleware.authenticateWebSocket(req);

                if (!authResult.success) {
                    logger.warn('WebSocket authentication failed', {
                        ip: req.socket.remoteAddress,
                        error: authResult.error
                    });

                    ws.close(1008, `Authentication failed: ${authResult.error}`);
                    return;
                }

                const { userContext } = authResult;
                const userId = userContext.userId;

                logger.info('Trading WebSocket authenticated', {
                    userId,
                    subscriptionTier: userContext.subscriptionTier,
                    ip: req.socket.remoteAddress
                });

                // Initialize connection data
                if (!this.connections.has(userId)) {
                    this.connections.set(userId, {
                        userId,
                        userContext,
                        tradingWs: null,
                        priceStreamWs: null,
                        authenticated: true,
                        lastHeartbeat: Date.now(),
                        protocolType: 'auto', // auto-detect
                        subscriptions: new Set()
                    });
                }

                const connection = this.connections.get(userId);
                connection.tradingWs = ws;
                connection.authenticated = true;
                connection.userContext = userContext;

                // Setup message handling
                ws.on('message', (data) => {
                    this.handleTradingMessage(userId, data);
                });

                // Setup connection events
                this.setupConnectionEvents(ws, userId, 'trading');

                // Send welcome message
                this.sendWelcomeMessage(ws, 'trading');

            } catch (error) {
                logger.error('Trading WebSocket connection error', { error });
                ws.close(1011, 'Internal server error');
            }
        });
    }

    /**
     * Setup Price Streaming WebSocket Server
     */
    setupPriceStreamServer() {
        this.servers.priceStream.on('connection', async (ws, req) => {
            try {
                // Authenticate WebSocket connection
                const authResult = await this.authMiddleware.authenticateWebSocket(req);

                if (!authResult.success) {
                    logger.warn('Price stream authentication failed', {
                        ip: req.socket.remoteAddress,
                        error: authResult.error
                    });

                    ws.close(1008, `Authentication failed: ${authResult.error}`);
                    return;
                }

                const { userContext } = authResult;
                const userId = userContext.userId;

                logger.info('Price stream WebSocket authenticated', {
                    userId,
                    subscriptionTier: userContext.subscriptionTier,
                    ip: req.socket.remoteAddress
                });

                // Get or create connection data
                if (!this.connections.has(userId)) {
                    this.connections.set(userId, {
                        userId,
                        userContext,
                        tradingWs: null,
                        priceStreamWs: null,
                        authenticated: true,
                        lastHeartbeat: Date.now(),
                        protocolType: 'auto',
                        subscriptions: new Set()
                    });
                }

                const connection = this.connections.get(userId);
                connection.priceStreamWs = ws;
                connection.authenticated = true;
                connection.userContext = userContext;

                // Setup message handling
                ws.on('message', (data) => {
                    this.handlePriceStreamMessage(userId, data);
                });

                // Setup connection events
                this.setupConnectionEvents(ws, userId, 'price_stream');

                // Send welcome message
                this.sendWelcomeMessage(ws, 'price_stream');

            } catch (error) {
                logger.error('Price stream WebSocket connection error', { error });
                ws.close(1011, 'Internal server error');
            }
        });
    }

    /**
     * Handle trading channel messages
     * @param {string} userId - User identifier
     * @param {Buffer|string} data - Message data
     */
    async handleTradingMessage(userId, data) {
        try {
            const connection = this.connections.get(userId);
            if (!connection) return;

            // Auto-detect protocol type
            if (connection.protocolType === 'auto') {
                connection.protocolType = this.detectProtocolType(data);
                console.log(`[MT5-TRADING] Protocol detected for ${userId}: ${connection.protocolType}`);
            }

            // ✅ NEW: Use contract input handler
            const metadata = {
                contentType: connection.protocolType === 'binary' ? 'application/octet-stream' : 'application/json',
                correlationId: `ws_trading_${userId}_${Date.now()}`,
                userAgent: 'WebSocket-Client-MT5',
                tenantId: connection.tenantId || 'default',
                channel: 'trading',
                transport: 'websocket'
            };

            const context = {
                tenant_id: connection.tenantId || 'default',
                user_id: userId,
                session_id: connection.sessionId || `ws_${userId}`,
                channel: 'trading'
            };

            // Convert data to Buffer if needed
            const binaryData = Buffer.isBuffer(data) ? data : Buffer.from(data);

            // Process through contract input handler
            const result = await this.clientMT5InputHandler.handleInput(binaryData, metadata, context);

            // Update heartbeat
            connection.lastHeartbeat = Date.now();

            // Route message based on centralized handler result
            await this.routeTradingMessage(userId, result.data.parsed_data || { raw: true, type: 'binary_data' });

            console.log(`[MT5-TRADING] ${userId} → processed via contract handler (${connection.protocolType})`);

        } catch (error) {
            console.error(`[MT5-TRADING] Error handling message from ${userId}:`, error);
            this.sendErrorResponse(userId, 'trading', error.message);
        }
    }

    /**
     * Handle price stream messages
     * @param {string} userId - User identifier
     * @param {Buffer|string} data - Message data
     */
    async handlePriceStreamMessage(userId, data) {
        try {
            const connection = this.connections.get(userId);
            if (!connection) return;

            // Auto-detect protocol type
            if (connection.protocolType === 'auto') {
                connection.protocolType = this.detectProtocolType(data);
                console.log(`[MT5-PRICE] Protocol detected for ${userId}: ${connection.protocolType}`);
            }

            // ✅ NEW: Use contract input handler
            const metadata = {
                contentType: connection.protocolType === 'binary' ? 'application/octet-stream' : 'application/json',
                correlationId: `ws_price_${userId}_${Date.now()}`,
                userAgent: 'WebSocket-Client-MT5',
                tenantId: connection.tenantId || 'default',
                channel: 'price_stream',
                transport: 'websocket'
            };

            const context = {
                tenant_id: connection.tenantId || 'default',
                user_id: userId,
                session_id: connection.sessionId || `ws_${userId}`,
                channel: 'price_stream'
            };

            // Convert data to Buffer if needed
            const binaryData = Buffer.isBuffer(data) ? data : Buffer.from(data);

            // Process through contract input handler
            const result = await this.clientMT5InputHandler.handleInput(binaryData, metadata, context);

            // Update heartbeat
            connection.lastHeartbeat = Date.now();

            // Route message based on centralized handler result
            await this.routePriceStreamMessage(userId, result.data.parsed_data || { raw: true, type: 'binary_data' });

            console.log(`[MT5-PRICE] ${userId} → processed via contract handler (${connection.protocolType})`);

        } catch (error) {
            console.error(`[MT5-PRICE] Error handling message from ${userId}:`, error);
            this.sendErrorResponse(userId, 'price_stream', error.message);
        }
    }

    /**
     * Route trading messages using the corrected input/output flow
     * @param {string} userId - User identifier
     * @param {Object} message - Parsed message
     */
    async routeTradingMessage(userId, message) {
        try {
            // Add user context to metadata
            const metadata = {
                userId,
                source: 'client-mt5',
                channel: 'trading',
                timestamp: Date.now()
            };

            // Route as INPUT from client-mt5
            this.emit('input_message', {
                sourceInput: 'client-mt5',
                message: message,
                metadata: metadata
            });

            // Handle special cases locally
            if (message.type === 'heartbeat') {
                this.sendHeartbeatResponse(userId);
            }

        } catch (error) {
            console.error(`[MT5-TRADING] Error routing message:`, error);
            this.sendErrorResponse(userId, 'trading', error.message);
        }
    }

    /**
     * Route price stream messages using the corrected input/output flow
     * @param {string} userId - User identifier
     * @param {Object} message - Parsed message
     */
    async routePriceStreamMessage(userId, message) {
        try {
            // Add user context to metadata
            const metadata = {
                userId,
                source: 'client-mt5',
                channel: 'price-stream',
                timestamp: Date.now()
            };

            // Route as INPUT from client-mt5
            this.emit('input_message', {
                sourceInput: 'client-mt5',
                message: message,
                metadata: metadata
            });

            // Handle special cases locally
            if (message.type === 'subscription') {
                this.handleSubscription(userId, message);
            }

        } catch (error) {
            console.error(`[MT5-PRICE] Error routing message:`, error);
            this.sendErrorResponse(userId, 'price_stream', error.message);
        }
    }

    /**
     * Detect protocol type from message data
     * @param {Buffer|string} data - Message data
     * @returns {string} Protocol type ('binary' or 'json')
     */
    detectProtocolType(data) {
        if (Buffer.isBuffer(data) && data.length >= 4) {
            // Check for Suho binary magic number
            const magic = data.readUInt32LE(0);
            if (magic === 0x53554854) { // "SUHO"
                return 'binary';
            }
        }

        // Try to parse as JSON
        try {
            JSON.parse(data.toString());
            return 'json';
        } catch {
            // If not JSON and not binary, default to binary
            return 'binary';
        }
    }

    /**
     * Forward message to Trading Engine
     * @param {Object} protoMessage - Protocol Buffer message
     */
    async forwardToTradingEngine(protoMessage) {
        try {
            // Add API Gateway metadata
            protoMessage.source = 'client-mt5';
            protoMessage.gateway_timestamp = Date.now();

            // Forward via HTTP POST (as specified in contracts)
            await this.sendToBackendService('trading-engine', protoMessage);

            console.log('[MT5-ROUTER] Message forwarded to Trading Engine');
        } catch (error) {
            console.error('[MT5-ROUTER] Error forwarding to Trading Engine:', error);
        }
    }

    /**
     * Forward message to ML Processing Service
     * @param {Object} protoMessage - Protocol Buffer message
     */
    async forwardToMLProcessing(protoMessage) {
        try {
            // Add real-time processing flag
            protoMessage.processing_priority = 'real_time';
            protoMessage.source = 'client-mt5';

            // Forward to ML Processing
            await this.sendToBackendService('ml-processing', protoMessage);

            console.log('[MT5-ROUTER] Price data forwarded to ML Processing');
        } catch (error) {
            console.error('[MT5-ROUTER] Error forwarding to ML Processing:', error);
        }
    }

    /**
     * Forward message to Analytics Service
     * @param {Object} protoMessage - Protocol Buffer message
     */
    async forwardToAnalyticsService(protoMessage) {
        try {
            // Add analytics metadata
            protoMessage.analytics_enabled = true;
            protoMessage.source = 'client-mt5';

            // Forward to Analytics Service
            await this.sendToBackendService('analytics-service', protoMessage);

            console.log('[MT5-ROUTER] Data forwarded to Analytics Service');
        } catch (error) {
            console.error('[MT5-ROUTER] Error forwarding to Analytics Service:', error);
        }
    }

    /**
     * Send message to backend service
     * @param {string} serviceName - Target service name
     * @param {Object} message - Message to send
     */
    async sendToBackendService(serviceName, message) {
        // This would be implemented with actual HTTP client or message queue
        // For now, emit event for routing layer to handle
        this.emit('backend_message', {
            service: serviceName,
            message: message,
            timestamp: Date.now()
        });
    }

    /**
     * Send message to Client-MT5
     * @param {string} userId - Target user
     * @param {string} channel - Channel type ('trading' or 'price_stream')
     * @param {Object} message - Message to send
     */
    sendToClient(userId, channel, message) {
        const connection = this.connections.get(userId);
        if (!connection) {
            console.warn(`[MT5-SENDER] No connection found for user: ${userId}`);
            return;
        }

        const ws = channel === 'trading' ? connection.tradingWs : connection.priceStreamWs;
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            console.warn(`[MT5-SENDER] ${channel} WebSocket not ready for user: ${userId}`);
            return;
        }

        try {
            let data;

            // Send in the same protocol as received
            if (connection.protocolType === 'binary') {
                data = this.binaryProtocol.fromProtocolBuffer(message);
            } else {
                data = JSON.stringify(message);
            }

            ws.send(data);
            console.log(`[MT5-SENDER] Message sent to ${userId} via ${channel} channel`);

        } catch (error) {
            console.error(`[MT5-SENDER] Error sending to ${userId}:`, error);
        }
    }

    /**
     * Setup connection event handlers
     * @param {WebSocket} ws - WebSocket connection
     * @param {string} userId - User identifier
     * @param {string} channel - Channel type
     */
    setupConnectionEvents(ws, userId, channel) {
        ws.on('close', () => {
            console.log(`[MT5-${channel.toUpperCase()}] Connection closed: ${userId}`);
            this.handleDisconnection(userId, channel);
        });

        ws.on('error', (error) => {
            console.error(`[MT5-${channel.toUpperCase()}] Connection error for ${userId}:`, error);
            this.handleConnectionError(userId, channel, error);
        });

        ws.on('pong', () => {
            const connection = this.connections.get(userId);
            if (connection) {
                connection.lastHeartbeat = Date.now();
            }
        });
    }

    /**
     * Handle connection disconnection
     * @param {string} userId - User identifier
     * @param {string} channel - Channel that disconnected
     */
    handleDisconnection(userId, channel) {
        const connection = this.connections.get(userId);
        if (!connection) return;

        if (channel === 'trading') {
            connection.tradingWs = null;
        } else if (channel === 'price_stream') {
            connection.priceStreamWs = null;
        }

        // If both channels are disconnected, remove connection
        if (!connection.tradingWs && !connection.priceStreamWs) {
            this.connections.delete(userId);
            console.log(`[MT5-HANDLER] User ${userId} fully disconnected`);

            // Notify backend services
            this.emit('user_disconnected', { userId, timestamp: Date.now() });
        }
    }

    /**
     * Extract user ID from request
     * @param {Object} req - HTTP request object
     * @returns {string} User identifier
     */
    extractUserId(req) {
        // Extract from URL parameters, headers, or JWT token
        const url = new URL(req.url, `http://${req.headers.host}`);
        const userId = url.searchParams.get('userId') ||
                      req.headers['x-user-id'] ||
                      'anonymous_' + Date.now();

        return userId;
    }

    /**
     * Send welcome message to client
     * @param {WebSocket} ws - WebSocket connection
     * @param {string} channel - Channel type
     */
    sendWelcomeMessage(ws, channel) {
        const welcomeMessage = {
            type: 'welcome',
            channel: channel,
            server_time: Date.now(),
            protocol_version: '2.0',
            binary_protocol_supported: true
        };

        ws.send(JSON.stringify(welcomeMessage));
    }

    /**
     * Send error response to client
     * @param {string} userId - User identifier
     * @param {string} channel - Channel type
     * @param {string} error - Error message
     */
    sendErrorResponse(userId, channel, error) {
        const errorMessage = {
            type: 'error',
            error: error,
            timestamp: Date.now()
        };

        this.sendToClient(userId, channel, errorMessage);
    }

    /**
     * Send heartbeat response
     * @param {string} userId - User identifier
     */
    sendHeartbeatResponse(userId) {
        const heartbeatResponse = {
            type: 'heartbeat_ack',
            timestamp: Date.now()
        };

        this.sendToClient(userId, 'trading', heartbeatResponse);
    }

    /**
     * Handle symbol subscription
     * @param {string} userId - User identifier
     * @param {Object} message - Subscription message
     */
    handleSubscription(userId, message) {
        const connection = this.connections.get(userId);
        if (!connection) return;

        if (message.action === 'subscribe') {
            message.symbols.forEach(symbol => {
                connection.subscriptions.add(symbol);
            });
        } else if (message.action === 'unsubscribe') {
            message.symbols.forEach(symbol => {
                connection.subscriptions.delete(symbol);
            });
        }

        console.log(`[MT5-SUBSCRIPTION] User ${userId} ${message.action}: ${message.symbols.join(', ')}`);
    }

    /**
     * Start heartbeat monitoring
     */
    startHeartbeatMonitoring() {
        setInterval(() => {
            const now = Date.now();

            for (const [userId, connection] of this.connections.entries()) {
                if (now - connection.lastHeartbeat > this.options.heartbeatInterval * 2) {
                    console.warn(`[MT5-HEARTBEAT] User ${userId} heartbeat timeout`);

                    // Send ping to both channels
                    if (connection.tradingWs?.readyState === WebSocket.OPEN) {
                        connection.tradingWs.ping();
                    }
                    if (connection.priceStreamWs?.readyState === WebSocket.OPEN) {
                        connection.priceStreamWs.ping();
                    }
                }
            }
        }, this.options.heartbeatInterval);
    }

    /**
     * Get connection statistics
     * @returns {Object} Connection stats
     */
    getConnectionStats() {
        const stats = {
            total_connections: this.connections.size,
            trading_connections: 0,
            price_stream_connections: 0,
            binary_protocol_users: 0,
            json_protocol_users: 0
        };

        for (const connection of this.connections.values()) {
            if (connection.tradingWs?.readyState === WebSocket.OPEN) {
                stats.trading_connections++;
            }
            if (connection.priceStreamWs?.readyState === WebSocket.OPEN) {
                stats.price_stream_connections++;
            }
            if (connection.protocolType === 'binary') {
                stats.binary_protocol_users++;
            } else if (connection.protocolType === 'json') {
                stats.json_protocol_users++;
            }
        }

        return stats;
    }

    /**
     * Shutdown the handler
     */
    shutdown() {
        console.log('[MT5-HANDLER] Shutting down...');

        // Close all connections
        for (const [userId, connection] of this.connections.entries()) {
            if (connection.tradingWs) connection.tradingWs.close();
            if (connection.priceStreamWs) connection.priceStreamWs.close();
        }

        // Close servers
        if (this.servers.trading) this.servers.trading.close();
        if (this.servers.priceStream) this.servers.priceStream.close();

        this.connections.clear();
        console.log('[MT5-HANDLER] Shutdown complete');
    }
}

module.exports = ClientMT5Handler;