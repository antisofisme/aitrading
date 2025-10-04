/**
 * API Gateway - Suho AI Trading Platform
 *
 * Main entry point with Central Hub integration following ChainFlow pattern:
 * 1. Register with Central Hub for service discovery
 * 2. Get configuration from Central Hub hot-reload
 * 3. Use shared components from Central Hub
 * 4. Report health status to Central Hub
 *
 * Responsibilities:
 * - HTTP/WebSocket protocol handling
 * - Suho Binary Protocol ↔ JSON conversion
 * - Client-MT5 integration
 * - Request routing and load balancing
 * - Authentication & authorization
 */

const express = require('express');
const http = require('http');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const axios = require('axios');

// Core API Gateway modules
const ClientMT5Handler = require('./src/websocket/client-mt5-handler');
const BidirectionalRouter = require('./src/routing/bidirectional-router');
const { SuhoBinaryProtocol } = require('./src/protocols/suho-binary-protocol');
const AuthMiddleware = require('./src/middleware/auth');

// Central Hub integration - Using SDK
const CentralHubClient = require('@suho/central-hub-sdk');
const ServiceConfig = require('./src/config/service-config');

class APIGateway {
    constructor() {
        this.app = express();
        this.server = null;
        this.centralHub = null;
        this.config = null;
        this.isRegistered = false;

        // Service metadata for Central Hub registration
        this.serviceInfo = {
            name: 'api-gateway',
            host: process.env.API_GATEWAY_HOST || 'suho-api-gateway',
            port: parseInt(process.env.PORT || '8000'),
            protocol: 'http',
            version: '2.0.0',
            environment: process.env.NODE_ENV || 'development',
            health_endpoint: '/health',
            metadata: {
                type: 'api-gateway',
                capabilities: ['http', 'websocket', 'trading', 'suho-binary-protocol'],
                max_connections: 1000,
                load_balancing_weight: 10
            },
            transport_config: {
                preferred_inbound: ['http', 'websocket'],
                preferred_outbound: ['http', 'nats-kafka'],
                supports_streaming: true,
                max_message_size: 1048576
            }
        };
    }

    async initialize() {
        try {
            console.log('🚀 Initializing API Gateway...');

            // Step 1: Initialize Central Hub client
            this.centralHub = new CentralHubClient({
                baseURL: process.env.CENTRAL_HUB_URL || 'http://suho-central-hub:7000',
                serviceName: 'api-gateway',
                retryAttempts: 5,
                retryDelay: 2000
            });

            // Step 2: Register with Central Hub
            await this.registerWithCentralHub();

            // Step 3: Load configuration from Central Hub
            await this.loadConfiguration();

            // Step 4: Setup Express middleware
            this.setupMiddleware();

            // Step 5: Setup routes and WebSocket handlers
            this.setupRoutes();
            this.setupWebSocket();

            // Step 6: Start health monitoring
            this.startHealthMonitoring();

            console.log('✅ API Gateway initialized successfully');
        } catch (error) {
            console.error('❌ Failed to initialize API Gateway:', error);
            throw error;
        }
    }

    async registerWithCentralHub() {
        try {
            console.log('📡 Registering with Central Hub...');

            const registrationResult = await this.centralHub.register(this.serviceInfo);
            this.isRegistered = true;

            console.log('✅ Registered with Central Hub:', registrationResult.service_id);
        } catch (error) {
            console.error('❌ Failed to register with Central Hub:', error);
            // Continue with fallback mode
            console.log('⚠️  Running in standalone mode without Central Hub');
        }
    }

    async loadConfiguration() {
        try {
            console.log('⚙️  Loading configuration from Central Hub...');

            if (this.isRegistered) {
                this.config = await this.centralHub.getConfiguration('api-gateway');
                console.log('✅ Configuration loaded from Central Hub');
            } else {
                // Fallback to local configuration
                this.config = ServiceConfig.getDefaultConfig();
                console.log('⚠️  Using default configuration (fallback mode)');
            }
        } catch (error) {
            console.error('❌ Failed to load configuration:', error);
            this.config = ServiceConfig.getDefaultConfig();
            console.log('⚠️  Using default configuration (fallback)');
        }
    }

    setupMiddleware() {
        // Security middleware
        this.app.use(helmet({
            contentSecurityPolicy: false,
            crossOriginEmbedderPolicy: false
        }));

        // CORS configuration from Central Hub config
        const corsOptions = this.config?.api_gateway?.cors || {
            origin: ['*'],
            methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
            allowedHeaders: ['*'],
            credentials: true
        };
        this.app.use(cors(corsOptions));

        // Compression
        this.app.use(compression());

        // JSON parsing with size limits from config
        const maxRequestSize = this.config?.business_rules?.validation_rules?.max_request_size_mb || 10;
        this.app.use(express.json({ limit: `${maxRequestSize}mb` }));
        this.app.use(express.urlencoded({ extended: true, limit: `${maxRequestSize}mb` }));

        // Authentication middleware (conditional based on config)
        if (this.config?.business_rules?.validation_rules?.require_authentication) {
            this.app.use('/api', AuthMiddleware.authenticate);
        }

        // Rate limiting from Central Hub config
        if (this.config?.business_rules?.rate_limiting?.enabled) {
            this.setupRateLimiting();
        }

        console.log('✅ Middleware configured');
    }

    setupRateLimiting() {
        // Implement rate limiting based on Central Hub configuration
        const rateLimitConfig = this.config.business_rules.rate_limiting;

        // Simple in-memory rate limiting (production should use Redis)
        const requestCounts = new Map();

        this.app.use((req, res, next) => {
            const clientIP = req.ip || req.connection.remoteAddress;
            const now = Date.now();
            const windowStart = now - (60 * 1000); // 1 minute window

            if (!requestCounts.has(clientIP)) {
                requestCounts.set(clientIP, []);
            }

            const requests = requestCounts.get(clientIP);
            const recentRequests = requests.filter(time => time > windowStart);

            if (recentRequests.length >= rateLimitConfig.requests_per_minute) {
                return res.status(429).json({
                    error: 'Rate limit exceeded',
                    limit: rateLimitConfig.requests_per_minute,
                    window: '1 minute'
                });
            }

            recentRequests.push(now);
            requestCounts.set(clientIP, recentRequests);

            next();
        });

        console.log(`✅ Rate limiting configured: ${rateLimitConfig.requests_per_minute}/minute`);
    }

    setupRoutes() {
        // Health check endpoint
        this.app.get('/health', (req, res) => {
            res.json({
                status: 'healthy',
                service: 'api-gateway',
                version: this.serviceInfo.version,
                timestamp: Date.now(),
                central_hub_connected: this.isRegistered,
                uptime: process.uptime()
            });
        });

        // Service info endpoint
        this.app.get('/', (req, res) => {
            res.json({
                service: 'api-gateway',
                version: this.serviceInfo.version,
                description: 'Suho AI Trading Platform API Gateway',
                endpoints: {
                    health: '/health',
                    api: '/api/*',
                    websocket: 'ws://localhost:8001',
                    trading_ws: 'ws://localhost:8002'
                },
                central_hub_integration: this.isRegistered,
                capabilities: this.serviceInfo.metadata.capabilities
            });
        });

        // Initialize bidirectional router with Central Hub service discovery
        const router = new BidirectionalRouter({
            centralHub: this.centralHub,
            config: this.config
        });

        // API routes with intelligent routing
        this.app.use('/api', router.getExpressRouter());

        console.log('✅ Routes configured');
    }

    setupWebSocket() {
        // WebSocket server for Client-MT5 integration
        const wsServer = http.createServer();

        // Trading WebSocket (port 8001)
        const tradingHandler = new ClientMT5Handler({
            port: 8001,
            protocolConfig: this.config?.api_gateway?.suho_binary_protocol,
            centralHub: this.centralHub
        });

        // Price Stream WebSocket (port 8002)
        const priceHandler = new ClientMT5Handler({
            port: 8002,
            type: 'price_stream',
            protocolConfig: this.config?.api_gateway?.suho_binary_protocol,
            centralHub: this.centralHub
        });

        tradingHandler.initialize();
        priceHandler.initialize();

        console.log('✅ WebSocket handlers configured');
        console.log('   - Trading WebSocket: ws://localhost:8001');
        console.log('   - Price Stream WebSocket: ws://localhost:8002');
    }

    startHealthMonitoring() {
        // Report health to Central Hub every 30 seconds
        setInterval(async () => {
            if (this.isRegistered) {
                try {
                    await this.centralHub.reportHealth({
                        status: 'healthy',
                        timestamp: Date.now(),
                        metrics: {
                            uptime: process.uptime(),
                            memory_usage: process.memoryUsage(),
                            active_connections: this.getActiveConnections()
                        }
                    });
                } catch (error) {
                    console.error('Failed to report health to Central Hub:', error);
                }
            }
        }, 30000);

        console.log('✅ Health monitoring started');
    }

    getActiveConnections() {
        // Get active connection count from WebSocket handlers
        return 0; // Placeholder - implement actual connection counting
    }

    async start() {
        try {
            await this.initialize();

            const port = this.serviceInfo.port;
            this.server = this.app.listen(port, '0.0.0.0', () => {
                console.log(`🚀 API Gateway running on port ${port}`);
                console.log(`📊 Health check: http://localhost:${port}/health`);
                console.log(`🔗 Central Hub integration: ${this.isRegistered ? 'ACTIVE' : 'DISABLED'}`);
            });

            // Graceful shutdown
            process.on('SIGTERM', () => this.shutdown());
            process.on('SIGINT', () => this.shutdown());

        } catch (error) {
            console.error('❌ Failed to start API Gateway:', error);
            process.exit(1);
        }
    }

    async shutdown() {
        console.log('🛑 Shutting down API Gateway...');

        if (this.isRegistered) {
            try {
                await this.centralHub.unregister();
                console.log('✅ Unregistered from Central Hub');
            } catch (error) {
                console.error('Failed to unregister from Central Hub:', error);
            }
        }

        if (this.server) {
            this.server.close(() => {
                console.log('✅ API Gateway shut down gracefully');
                process.exit(0);
            });
        }
    }
}

// Start API Gateway
if (require.main === module) {
    const gateway = new APIGateway();
    gateway.start().catch(error => {
        console.error('Failed to start API Gateway:', error);
        process.exit(1);
    });
}

module.exports = APIGateway;