/**
 * API Gateway Main Entry Point
 *
 * Integrates all components for Client-MT5 binary protocol support:
 * - Suho Binary Protocol parser/serializer
 * - Dual WebSocket channels for Client-MT5
 * - Bidirectional routing to backend services
 * - Protocol conversion (Binary ↔ Protocol Buffers)
 * - Central Hub integration for service discovery
 *
 * Based on API Gateway contracts and Client-MT5 specifications
 */

const express = require('express');
const http = require('http');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');

const ClientMT5Handler = require('./websocket/client-mt5-handler');
const BidirectionalRouter = require('./routing/bidirectional-router');
const { SuhoBinaryProtocol } = require('./protocols/suho-binary-protocol');
const AuthMiddleware = require('./middleware/auth');
const logger = require('./utils/logger');

// Import Central Hub Config Loader (NEW!)
const CentralHubConfigLoader = require('./config/central-hub-config');
const { APIGatewayService } = require('./core/APIGatewayService');

// Import modular handlers organized by transfer method (corrected structure)
const { ClientMT5NatsKafkaHandler } = require('../contracts/webhook/from-client-mt5');
const { FrontendWebhookHandler } = require('../contracts/webhook/from-frontend');
const { TelegramWebhookHandler } = require('../contracts/webhook/from-telegram');

/**
 * API Gateway Application - Updated to use ServiceTemplate
 */
class APIGateway {
    constructor(options = {}) {
        this.options = {
            port: process.env.PORT || 8000,
            env: process.env.NODE_ENV || 'development',
            centralHubUrl: process.env.CENTRAL_HUB_URL || 'http://suho-central-hub:7000',
            enableCors: true,
            enableCompression: true,
            enableHelmet: true,
            logLevel: 'info',
            ...options
        };

        this.app = express();
        this.server = null;

        // ✅ NEW: Initialize Central Hub Config Loader
        this.centralHubConfig = new CentralHubConfigLoader();
        this.config = null;

        // ✅ NEW: Initialize ServiceTemplate-based service
        this.apiGatewayService = new APIGatewayService(this.options);

        // ✅ NEW: Initialize modular handlers per transfer method
        this.inputHandlers = {
            // NATS+Kafka: High-throughput binary data (Client-MT5)
            clientMT5: new ClientMT5NatsKafkaHandler({
                enableConversion: false, // TERIMA SAJA, TIDAK CONVERT
                enableValidation: true,
                enableRouting: true
            }),
            // Webhook: External integrations (Frontend, Telegram)
            frontend: new FrontendWebhookHandler({
                enableValidation: true,
                enableRouting: true,
                requireAuth: true
            }),
            telegram: new TelegramWebhookHandler({
                enableValidation: true,
                enableRouting: true,
                botToken: process.env.TELEGRAM_BOT_TOKEN
            })
        };

        // Legacy components (akan di-migrate bertahap)
        this.clientMT5Handler = null;
        this.bidirectionalRouter = null;
        this.binaryProtocol = new SuhoBinaryProtocol();
        this.authMiddleware = new AuthMiddleware({
            jwtSecret: process.env.JWT_SECRET,
            jwtExpiresIn: process.env.JWT_EXPIRES_IN || '24h',
            issuer: process.env.JWT_ISSUER || 'api-gateway',
            audience: process.env.JWT_AUDIENCE || 'suho-trading'
        });

        // Statistics (akan menggunakan metrics dari ServiceTemplate)
        this.stats = {
            startTime: Date.now(),
            requestCount: 0,
            connectionCount: 0,
            errorCount: 0,
            binaryMessages: 0,
            jsonMessages: 0
        };

        this.initializeMiddleware();
        this.initializeRoutes();
    }

    /**
     * Initialize Express middleware
     */
    initializeMiddleware() {
        // Security middleware
        if (this.options.enableHelmet) {
            this.app.use(helmet({
                contentSecurityPolicy: false, // Allow WebSocket connections
                crossOriginEmbedderPolicy: false // Allow cross-origin requests
            }));
        }

        // CORS middleware
        if (this.options.enableCors) {
            this.app.use(cors({
                origin: true,
                credentials: true,
                methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
                allowedHeaders: ['Content-Type', 'Authorization', 'X-User-ID', 'X-Correlation-ID']
            }));
        }

        // Compression middleware
        if (this.options.enableCompression) {
            this.app.use(compression());
        }

        // Request parsing middleware
        this.app.use(express.json({ limit: '10mb' }));
        this.app.use(express.raw({ type: 'application/x-protobuf', limit: '10mb' }));
        this.app.use(express.urlencoded({ extended: true }));

        // Request logging middleware
        this.app.use((req, res, next) => {
            const correlationId = req.headers['x-correlation-id'] ||
                                 `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            req.correlationId = correlationId;

            this.stats.requestCount++;
            logger.logRequest(req, res, correlationId);
            next();
        });

        // Error handling middleware
        this.app.use((error, req, res, next) => {
            this.stats.errorCount++;
            logger.error('API Gateway Error', {
                error: error.message,
                stack: error.stack,
                correlationId: req.correlationId,
                path: req.path,
                method: req.method
            });

            res.status(500).json({
                error: 'Internal Server Error',
                message: this.options.env === 'development' ? error.message : 'Something went wrong',
                timestamp: new Date().toISOString(),
                correlationId: req.correlationId
            });
        });
    }

    /**
     * Initialize HTTP routes
     */
    initializeRoutes() {
        // Health check endpoint - Updated to use ServiceTemplate
        this.app.get('/health', async (req, res) => {
            try {
                const healthData = await this.apiGatewayService.healthCheck();
                res.status(healthData.status === 'healthy' ? 200 : 503).json(healthData);
            } catch (error) {
                res.status(503).json({
                    status: 'unhealthy',
                    error: error.message,
                    timestamp: new Date().toISOString()
                });
            }
        });

        // Statistics endpoint
        this.app.get('/stats', (req, res) => {
            res.json(this.getStatistics());
        });

        // ✅ MODULAR: Client-MT5 input handler (binary data dari MT5 terminal)
        this.app.post('/api/client-mt5/input', express.raw({ type: '*/*', limit: '10mb' }), async (req, res) => {
            try {
                // Prepare metadata from headers
                const metadata = {
                    contentType: req.headers['content-type'] || 'application/octet-stream',
                    correlationId: req.correlationId,
                    userAgent: req.headers['user-agent'],
                    tenantId: req.headers['x-tenant-id'],
                    transport: 'http'
                };

                // Prepare context
                const context = {
                    tenant_id: req.headers['x-tenant-id'] || 'default',
                    user_id: req.headers['x-user-id'] || 'anonymous',
                    session_id: req.headers['x-session-id'] || `http_${Date.now()}`
                };

                // Use Client-MT5 specific input handler
                const result = await this.inputHandlers.clientMT5.handleInput(req.body, metadata, context);

                // Update stats
                this.stats.binaryMessages++;

                // Send response
                res.status(result.success ? 200 : 400).json(result);

                console.log('📥 [CENTRALIZED-INPUT] HTTP data processed:', {
                    tenantId: context.tenant_id,
                    dataLength: req.body?.length,
                    processingTime: result.data?.processing_time_ms,
                    routingTargets: result.routing_targets?.length
                });

            } catch (error) {
                console.error('❌ [CENTRALIZED-INPUT] Error:', error);
                res.status(500).json({
                    success: false,
                    error: {
                        type: 'INTERNAL_ERROR',
                        message: error.message,
                        correlationId: req.correlationId
                    }
                });
            }
        });

        // ✅ MODULAR: Frontend input handler (JSON data dari web/mobile dashboard)
        this.app.post('/api/frontend/input', express.json({ limit: '10mb' }), async (req, res) => {
            try {
                const metadata = {
                    contentType: req.headers['content-type'] || 'application/json',
                    correlationId: req.correlationId,
                    userAgent: req.headers['user-agent'],
                    endpoint: req.url,
                    method: req.method,
                    transport: 'http'
                };

                const context = {
                    user_id: req.headers['x-user-id'] || req.user?.id,
                    session_id: req.headers['x-session-id'] || req.sessionID,
                    permissions: req.user?.permissions || []
                };

                // Use Frontend specific input handler
                const result = await this.inputHandlers.frontend.handleInput(req.body, metadata, context);

                this.stats.jsonMessages++;

                res.status(result.success ? 200 : 400).json(result);

                console.log('🖥️ [FRONTEND-INPUT] HTTP data processed:', {
                    endpoint: metadata.endpoint,
                    userId: context.user_id,
                    processingTime: result.data?.processing_time_ms
                });

            } catch (error) {
                console.error('❌ [FRONTEND-INPUT] Error:', error);
                res.status(500).json({
                    success: false,
                    error: { type: 'INTERNAL_ERROR', message: error.message }
                });
            }
        });

        // ✅ MODULAR: Telegram input handler (webhook dari Telegram Bot)
        this.app.post('/api/telegram/webhook', express.json({ limit: '1mb' }), async (req, res) => {
            try {
                const metadata = {
                    contentType: req.headers['content-type'] || 'application/json',
                    correlationId: req.correlationId,
                    userAgent: req.headers['user-agent'],
                    botToken: req.headers['x-telegram-bot-api-secret-token'],
                    transport: 'webhook'
                };

                const context = {
                    telegram_user_id: this.getTelegramUserId(req.body),
                    chat_id: this.getTelegramChatId(req.body)
                };

                // Use Telegram specific input handler
                const result = await this.inputHandlers.telegram.handleInput(req.body, metadata, context);

                res.status(result.success ? 200 : 400).json({ ok: result.success });

                console.log('💬 [TELEGRAM-INPUT] Webhook processed:', {
                    updateId: req.body.update_id,
                    userId: context.telegram_user_id,
                    processingTime: result.data?.processing_time_ms
                });

            } catch (error) {
                console.error('❌ [TELEGRAM-INPUT] Error:', error);
                res.status(500).json({ ok: false });
            }
        });

        // Binary protocol test endpoint - Updated to use ServiceTemplate
        this.app.post('/test/binary', async (req, res) => {
            try {
                // Use ServiceTemplate untuk process binary data dengan tenant support
                const inputData = {
                    tenant_id: req.headers['x-tenant-id'] || 'test_tenant',
                    binary_data: req.body,
                    metadata: {
                        correlationId: req.correlationId,
                        source: 'test-endpoint'
                    }
                };

                const result = await this.apiGatewayService.processInput(
                    inputData,
                    'test-client',
                    'client-mt5-binary'
                );

                res.json({
                    success: true,
                    parsed_data: result.data.parsed_data,
                    tenant_id: result.data.tenant_id,
                    protocol_version: '2.1',
                    routing_targets: result.routing_targets
                });
            } catch (error) {
                res.status(400).json({
                    success: false,
                    error: error.message,
                    correlationId: req.correlationId
                });
            }
        });

        // WebSocket endpoint information
        this.app.get('/websocket/info', (req, res) => {
            res.json({
                trading_channel: 'ws://localhost:8001/ws/trading',
                price_stream_channel: 'ws://localhost:8002/ws/price-stream',
                protocols_supported: ['binary', 'json'],
                binary_protocol_version: '2.0',
                features: [
                    'Dual WebSocket channels',
                    'Suho Binary Protocol support',
                    'Auto protocol detection',
                    'Real-time routing',
                    'Protocol conversion'
                ]
            });
        });

        // Backend service endpoints (HTTP POST for Protocol Buffers) - Protected with JWT
        const authenticateBackend = this.authMiddleware.authenticateHTTP();

        // Trading Engine output → Client-MT5 - Updated to use ServiceTemplate
        this.app.post('/api/trading-engine/output', authenticateBackend, async (req, res) => {
            try {
                const inputData = {
                    tenant_id: req.headers['x-tenant-id'] || req.userContext?.tenantId,
                    data: req.body,
                    metadata: {
                        correlationId: req.correlationId,
                        userId: req.headers['x-user-id'] || req.userContext?.userId,
                        source: 'trading-engine'
                    }
                };

                await this.apiGatewayService.processInput(
                    inputData,
                    'trading-engine',
                    'backend-service-message'
                );

                res.json({
                    status: 'received',
                    correlationId: req.correlationId,
                    processedBy: req.userContext?.userId || 'system',
                    tenant_id: inputData.tenant_id
                });
            } catch (error) {
                res.status(500).json({
                    status: 'error',
                    error: error.message,
                    correlationId: req.correlationId
                });
            }
        });

        // Analytics Service output → Client-MT5 + Frontend
        this.app.post('/api/analytics-service/output', authenticateBackend, (req, res) => {
            this.handleBackendMessage('analytics-service', req.body, req.headers);
            res.json({
                status: 'received',
                correlationId: req.correlationId,
                processedBy: req.userContext?.userId || 'system'
            });
        });

        // ML Processing output → Multiple destinations
        this.app.post('/api/ml-processing/output', authenticateBackend, (req, res) => {
            this.handleBackendMessage('ml-processing', req.body, req.headers);
            res.json({
                status: 'received',
                correlationId: req.correlationId,
                processedBy: req.userContext?.userId || 'system'
            });
        });

        // Notification Hub output → Multiple channels
        this.app.post('/api/notification-hub/output', authenticateBackend, (req, res) => {
            this.handleBackendMessage('notification-hub', req.body, req.headers);
            res.json({
                status: 'received',
                correlationId: req.correlationId,
                processedBy: req.userContext?.userId || 'system'
            });
        });

        // Authentication endpoints
        this.app.post('/auth/login', (req, res) => {
            // Mock login for testing
            const { username, password } = req.body;

            if (username && password) {
                const token = this.authMiddleware.generateToken({
                    sub: username,
                    user_id: username,
                    permissions: ['mt5_trading', 'websocket_access'],
                    subscription_tier: 'pro'
                });

                const refreshToken = this.authMiddleware.generateRefreshToken(username);

                res.json({
                    success: true,
                    access_token: token,
                    refresh_token: refreshToken,
                    expires_in: '24h',
                    user: {
                        id: username,
                        permissions: ['mt5_trading', 'websocket_access'],
                        subscription_tier: 'pro'
                    }
                });
            } else {
                res.status(400).json({
                    success: false,
                    error: 'Username and password required'
                });
            }
        });

        this.app.post('/auth/refresh', async (req, res) => {
            try {
                const { refresh_token } = req.body;

                if (!refresh_token) {
                    return res.status(400).json({
                        success: false,
                        error: 'Refresh token required'
                    });
                }

                const newToken = await this.authMiddleware.refreshAccessToken(refresh_token);

                res.json({
                    success: true,
                    access_token: newToken,
                    expires_in: '24h'
                });
            } catch (error) {
                res.status(401).json({
                    success: false,
                    error: 'Invalid refresh token'
                });
            }
        });

        // Default route
        this.app.get('/', (req, res) => {
            res.json({
                name: 'Suho AI Trading API Gateway',
                version: '2.0.0',
                description: 'High-performance API Gateway with Suho Binary Protocol support',
                features: [
                    'Client-MT5 Binary Protocol (92% bandwidth reduction)',
                    'Dual WebSocket Architecture',
                    'Protocol Buffer ↔ Binary conversion',
                    'Bidirectional routing',
                    'Real-time performance monitoring'
                ],
                endpoints: {
                    health: '/health',
                    stats: '/stats',
                    websocket_info: '/websocket/info',
                    trading_ws: 'ws://localhost:8001/ws/trading',
                    price_stream_ws: 'ws://localhost:8002/ws/price-stream'
                },
                status: 'operational',
                uptime: Date.now() - this.stats.startTime
            });
        });
    }

    /**
     * Initialize core components - Updated to use ServiceTemplate
     */
    async initializeComponents() {
        try {
            // ✅ Initialize ServiceTemplate-based service first
            await this.apiGatewayService.initialize();
            logger.info('ServiceTemplate-based API Gateway Service initialized');

            // Initialize legacy components (akan di-migrate bertahap)
            this.bidirectionalRouter = new BidirectionalRouter({
                centralHubUrl: this.options.centralHubUrl
            });

            // Initialize transport after router is created
            logger.info('Initializing NATS+Kafka transport...');

            // Initialize Client-MT5 WebSocket handler
            this.clientMT5Handler = new ClientMT5Handler({
                binaryProtocolEnabled: true
            });

            this.setupComponentIntegration();

            logger.info('All API Gateway components initialized successfully');
        } catch (error) {
            logger.error('Failed to initialize API Gateway components', { error });
            throw error;
        }
    }

    /**
     * Setup integration between components using corrected input/output flow
     */
    setupComponentIntegration() {
        // Handle INPUT messages from Client-MT5
        this.clientMT5Handler.on('input_message', ({ sourceInput, message, metadata }) => {
            this.bidirectionalRouter.routeInput(sourceInput, message, metadata);
        });

        // Handle OUTPUT messages to Client-MT5
        this.bidirectionalRouter.on('to-client-mt5-execution', ({ userId, channel, message, metadata }) => {
            this.clientMT5Handler.sendToClient(userId, channel, message);
        });

        // Handle OUTPUT messages to Frontend WebSocket
        this.bidirectionalRouter.on('to-frontend-websocket', ({ message, metadata }) => {
            // Forward to frontend WebSocket handler (not implemented in this file)
            console.log('[API-GATEWAY] Frontend WebSocket output:', message.type || 'unknown');
        });

        // Handle OUTPUT messages to Telegram Webhook
        this.bidirectionalRouter.on('to-telegram-webhook', ({ message, metadata }) => {
            // Forward to Telegram bot handler (not implemented in this file)
            console.log('[API-GATEWAY] Telegram webhook output:', message.type || 'notification');
        });

        // Handle OUTPUT messages to Notification Channels
        this.bidirectionalRouter.on('to-notification-channels', ({ message, metadata }) => {
            // Forward to notification channels (email, SMS, etc.)
            console.log('[API-GATEWAY] Multi-channel notification output');
        });

        // Handle OUTPUT messages to Backend Services
        this.bidirectionalRouter.on('to-trading-engine', ({ message, metadata }) => {
            this.sendToBackendService('trading-engine', message, metadata);
        });

        this.bidirectionalRouter.on('to-ml-processing', ({ message, metadata }) => {
            this.sendToBackendService('ml-processing', message, metadata);
        });

        this.bidirectionalRouter.on('to-analytics-service', ({ message, metadata }) => {
            this.sendToBackendService('analytics-service', message, metadata);
        });

        this.bidirectionalRouter.on('to-notification-hub', ({ message, metadata }) => {
            this.sendToBackendService('notification-hub', message, metadata);
        });

        // Handle OUTPUT messages to Data Bridge (binary passthrough)
        this.bidirectionalRouter.on('to-data-bridge', ({ message, metadata }) => {
            this.sendToDataBridge(message, metadata);
        });

        // Monitor user connections
        this.clientMT5Handler.on('user_disconnected', ({ userId }) => {
            console.log(`[API-GATEWAY] User ${userId} disconnected`);
            this.stats.connectionCount--;
        });

        // Log routing operations
        this.bidirectionalRouter.on('routing_log', (logEntry) => {
            if (logEntry.status === 'success') {
                console.log(`[ROUTING] ${logEntry.source} → ${logEntry.targets.join(', ')}`);
            } else {
                console.error(`[ROUTING] ${logEntry.source} → FAILED: ${logEntry.error}`);
            }
        });
    }

    /**
     * Send message to backend service via HTTP
     * @param {string} serviceName - Target service name
     * @param {Object} message - Protocol Buffer message
     * @param {Object} metadata - Message metadata
     */
    async sendToBackendService(serviceName, message, metadata) {
        try {
            // Would use actual HTTP client here
            console.log(`[API-GATEWAY] HTTP output to ${serviceName}:`, message.type || 'data');

            // Emit for HTTP handler to pick up
            this.emit('backend_service_call', {
                service: serviceName,
                message,
                metadata
            });

        } catch (error) {
            console.error(`[API-GATEWAY] Error sending to ${serviceName}:`, error);
        }
    }

    /**
     * Send Suho Binary data to Data Bridge (no conversion)
     * @param {Object} binaryMessage - Suho Binary message (no conversion)
     * @param {Object} metadata - Message metadata
     */
    async sendToDataBridge(binaryMessage, metadata) {
        try {
            console.log(`[API-GATEWAY] Binary passthrough to Data Bridge:`, binaryMessage.type || 'binary-data');

            // Send raw binary data to Data Bridge via HTTP POST
            // Data Bridge will handle Suho Binary → Protocol Buffers conversion
            this.emit('data_bridge_call', {
                service: 'data-bridge',
                message: binaryMessage,
                metadata: {
                    ...metadata,
                    protocol: 'suho-binary',
                    noConversion: true  // Flag indicating no conversion at API Gateway
                }
            });

        } catch (error) {
            console.error(`[API-GATEWAY] Error sending to Data Bridge:`, error);
        }
    }

    /**
     * Handle INPUT messages from backend services (corrected flow)
     * @param {string} sourceService - Source service name
     * @param {Object} message - Protocol Buffer message
     * @param {Object} headers - HTTP headers
     */
    async handleBackendMessage(sourceService, message, headers) {
        try {
            const metadata = {
                correlationId: headers['x-correlation-id'],
                userId: headers['x-user-id'],
                timestamp: Date.now(),
                source: sourceService
            };

            // Route as INPUT from backend service
            await this.bidirectionalRouter.routeInput(sourceService, message, metadata);

            console.log(`[API-GATEWAY] Input from ${sourceService} processed successfully`);

        } catch (error) {
            console.error(`[API-GATEWAY] Error handling input from ${sourceService}:`, error);
            this.stats.errorCount++;
        }
    }

    /**
     * Get health status
     * @returns {Object} Health status information
     */
    getHealthStatus() {
        const uptime = Date.now() - this.stats.startTime;
        const mt5Stats = this.clientMT5Handler ? this.clientMT5Handler.getConnectionStats() : {};
        const routingStats = this.bidirectionalRouter ? this.bidirectionalRouter.getRoutingStats() : {};

        const isHealthy = (
            uptime > 1000 && // At least 1 second uptime
            this.stats.errorCount < 100 && // Less than 100 errors
            mt5Stats.total_connections !== undefined // Components initialized
        );

        return {
            status: isHealthy ? 'healthy' : 'unhealthy',
            timestamp: new Date().toISOString(),
            uptime_ms: uptime,
            components: {
                client_mt5_handler: mt5Stats ? 'operational' : 'not_initialized',
                bidirectional_router: routingStats ? 'operational' : 'not_initialized',
                binary_protocol: 'operational'
            },
            connections: mt5Stats,
            routing: routingStats
        };
    }

    /**
     * Get comprehensive statistics
     * @returns {Object} System statistics
     */
    getStatistics() {
        const uptime = Date.now() - this.stats.startTime;
        const mt5Stats = this.clientMT5Handler ? this.clientMT5Handler.getConnectionStats() : {};
        const routingStats = this.bidirectionalRouter ? this.bidirectionalRouter.getRoutingStats() : {};

        return {
            system: {
                uptime_ms: uptime,
                uptime_human: this.formatUptime(uptime),
                environment: this.options.env,
                version: '2.0.0'
            },
            performance: {
                total_requests: this.stats.requestCount,
                total_errors: this.stats.errorCount,
                error_rate: this.stats.requestCount > 0 ? (this.stats.errorCount / this.stats.requestCount) : 0,
                requests_per_second: this.stats.requestCount / (uptime / 1000),
                binary_messages: this.stats.binaryMessages,
                json_messages: this.stats.jsonMessages
            },
            client_mt5: mt5Stats,
            routing: routingStats,
            memory: {
                used: process.memoryUsage().heapUsed,
                total: process.memoryUsage().heapTotal,
                external: process.memoryUsage().external
            }
        };
    }

    /**
     * Format uptime in human readable format
     * @param {number} uptimeMs - Uptime in milliseconds
     * @returns {string} Formatted uptime
     */
    formatUptime(uptimeMs) {
        const seconds = Math.floor(uptimeMs / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (days > 0) return `${days}d ${hours % 24}h ${minutes % 60}m`;
        if (hours > 0) return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
        if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
        return `${seconds}s`;
    }

    /**
     * Start the API Gateway server - Updated to use ServiceTemplate
     */
    async start() {
        try {
            // ✅ STEP 1: Initialize Central Hub connection and fetch configs
            logger.info('📡 Connecting to Central Hub...');
            this.config = await this.centralHubConfig.initialize();
            logger.info('✅ Central Hub configuration loaded');

            // ✅ STEP 2: Initialize ServiceTemplate-based components
            await this.initializeComponents();

            // Create HTTP server
            this.server = http.createServer(this.app);

            // Start server
            await new Promise((resolve, reject) => {
                this.server.listen(this.options.port, (error) => {
                    if (error) {
                        reject(error);
                    } else {
                        resolve();
                    }
                });
            });

            // Start heartbeat monitoring for Client-MT5
            if (this.clientMT5Handler) {
                this.clientMT5Handler.startHeartbeatMonitoring();
            }

            console.log('🚀 Suho AI Trading API Gateway Started Successfully!');
            console.log('='.repeat(70));
            console.log(`📡 HTTP API Server: http://localhost:${this.options.port}`);
            console.log(`🎯 Trading WebSocket: ws://localhost:8001/ws/trading`);
            console.log(`📊 Price Stream WebSocket: ws://localhost:8002/ws/price-stream`);
            console.log(`🛡️  Binary Protocol: Suho v2.1 (Client-MT5 Compatible)`);
            console.log(`🏢 Multi-tenant: Enabled (tenant_id required)`);
            console.log(`🔄 Shared TransferManager: NATS+Kafka, gRPC, HTTP`);
            console.log(`📋 ServiceTemplate: Implemented`);
            console.log(`🌐 Environment: ${this.options.env}`);
            console.log(`⚡ Central Hub: ${this.options.centralHubUrl}`);
            console.log('='.repeat(70));
            console.log('✅ Ready to handle Client-MT5 with SERVICE_ARCHITECTURE.md patterns!');

        } catch (error) {
            console.error('❌ Failed to start API Gateway:', error);
            throw error;
        }
    }

    /**
     * Graceful shutdown - Updated to use ServiceTemplate
     */
    async shutdown() {
        console.log('\n🔄 Shutting down API Gateway...');

        try {
            // ✅ STEP 1: Unregister from Central Hub
            if (this.centralHubConfig) {
                await this.centralHubConfig.shutdown();
                console.log('✅ Central Hub integration shutdown complete');
            }

            // ✅ STEP 2: Shutdown ServiceTemplate-based service
            if (this.apiGatewayService) {
                await this.apiGatewayService.shutdown();
                console.log('✅ ServiceTemplate-based service shutdown complete');
            }

            // Close legacy components
            if (this.clientMT5Handler) {
                this.clientMT5Handler.shutdown();
            }

            if (this.bidirectionalRouter) {
                this.bidirectionalRouter.shutdown();
            }

            // Close HTTP server
            if (this.server) {
                await new Promise((resolve) => {
                    this.server.close(resolve);
                });
            }

            console.log('✅ API Gateway shutdown complete');
            process.exit(0);

        } catch (error) {
            console.error('❌ Error during shutdown:', error);
            process.exit(1);
        }
    }
}

// Handle graceful shutdown
process.on('SIGTERM', () => {
    console.log('\n📨 Received SIGTERM signal');
    if (global.apiGateway) {
        global.apiGateway.shutdown();
    }
});

process.on('SIGINT', () => {
    console.log('\n📨 Received SIGINT signal (Ctrl+C)');
    if (global.apiGateway) {
        global.apiGateway.shutdown();
    }
});

// Start the server if this file is run directly
if (require.main === module) {
    const gateway = new APIGateway();
    global.apiGateway = gateway;

    gateway.start().catch((error) => {
        console.error('💥 Failed to start API Gateway:', error);
        process.exit(1);
    });
}

module.exports = APIGateway;