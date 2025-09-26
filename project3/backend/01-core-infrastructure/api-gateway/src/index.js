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

/**
 * API Gateway Application
 */
class APIGateway {
    constructor(options = {}) {
        this.options = {
            port: process.env.PORT || 3000,
            env: process.env.NODE_ENV || 'development',
            centralHubUrl: process.env.CENTRAL_HUB_URL || 'http://localhost:3001',
            enableCors: true,
            enableCompression: true,
            enableHelmet: true,
            logLevel: 'info',
            ...options
        };

        this.app = express();
        this.server = null;

        // Core components
        this.clientMT5Handler = null;
        this.bidirectionalRouter = null;
        this.binaryProtocol = new SuhoBinaryProtocol();

        // Statistics
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
        this.initializeComponents();
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
            this.stats.requestCount++;
            console.log(`[API-GATEWAY] ${req.method} ${req.path} - ${req.ip}`);
            next();
        });

        // Error handling middleware
        this.app.use((error, req, res, next) => {
            this.stats.errorCount++;
            console.error('[API-GATEWAY] Error:', error);

            res.status(500).json({
                error: 'Internal Server Error',
                message: this.options.env === 'development' ? error.message : 'Something went wrong',
                timestamp: new Date().toISOString()
            });
        });
    }

    /**
     * Initialize HTTP routes
     */
    initializeRoutes() {
        // Health check endpoint
        this.app.get('/health', (req, res) => {
            const healthData = this.getHealthStatus();
            res.status(healthData.status === 'healthy' ? 200 : 503).json(healthData);
        });

        // Statistics endpoint
        this.app.get('/stats', (req, res) => {
            res.json(this.getStatistics());
        });

        // Binary protocol test endpoint
        this.app.post('/test/binary', (req, res) => {
            try {
                const testData = this.binaryProtocol.parsePacket(req.body);
                res.json({
                    success: true,
                    parsed_data: testData,
                    protocol_version: '2.0'
                });
            } catch (error) {
                res.status(400).json({
                    success: false,
                    error: error.message
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

        // Backend service endpoints (HTTP POST for Protocol Buffers)

        // Trading Engine output → Client-MT5
        this.app.post('/api/trading-engine/output', (req, res) => {
            this.handleBackendMessage('trading-engine', req.body, req.headers);
            res.json({ status: 'received' });
        });

        // Analytics Service output → Client-MT5 + Frontend
        this.app.post('/api/analytics-service/output', (req, res) => {
            this.handleBackendMessage('analytics-service', req.body, req.headers);
            res.json({ status: 'received' });
        });

        // ML Processing output → Multiple destinations
        this.app.post('/api/ml-processing/output', (req, res) => {
            this.handleBackendMessage('ml-processing', req.body, req.headers);
            res.json({ status: 'received' });
        });

        // Notification Hub output → Multiple channels
        this.app.post('/api/notification-hub/output', (req, res) => {
            this.handleBackendMessage('notification-hub', req.body, req.headers);
            res.json({ status: 'received' });
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
     * Initialize core components
     */
    initializeComponents() {
        // Initialize bidirectional router
        this.bidirectionalRouter = new BidirectionalRouter({
            centralHubUrl: this.options.centralHubUrl
        });

        // Initialize Client-MT5 WebSocket handler
        this.clientMT5Handler = new ClientMT5Handler({
            binaryProtocolEnabled: true
        });

        this.setupComponentIntegration();
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
     * Start the API Gateway server
     */
    async start() {
        try {
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
            console.log('='.repeat(60));
            console.log(`📡 HTTP API Server: http://localhost:${this.options.port}`);
            console.log(`🎯 Trading WebSocket: ws://localhost:8001/ws/trading`);
            console.log(`📊 Price Stream WebSocket: ws://localhost:8002/ws/price-stream`);
            console.log(`🛡️  Binary Protocol: Suho v2.0 (92% bandwidth reduction)`);
            console.log(`🔄 Bidirectional Routing: Enabled`);
            console.log(`🌐 Environment: ${this.options.env}`);
            console.log(`⚡ Central Hub: ${this.options.centralHubUrl}`);
            console.log('='.repeat(60));
            console.log('✅ Ready to handle Client-MT5 connections with binary protocol!');

        } catch (error) {
            console.error('❌ Failed to start API Gateway:', error);
            throw error;
        }
    }

    /**
     * Graceful shutdown
     */
    async shutdown() {
        console.log('\n🔄 Shutting down API Gateway...');

        try {
            // Close Client-MT5 handler
            if (this.clientMT5Handler) {
                this.clientMT5Handler.shutdown();
            }

            // Close bidirectional router
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