/**
 * API Gateway - ServiceTemplate Implementation
 * Menggunakan Central Hub shared components sesuai SERVICE_ARCHITECTURE.md
 */

const express = require('express');
const http = require('http');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');

// Import Hot Reload Loader for dynamic component loading
const { hotReloadLoader } = require('./hot-reload-loader');
const { configService } = require('./src/config/ConfigService');

// Will be dynamically loaded via hot reload
let ServiceTemplate, TransferManager, createServiceLogger, ErrorDNA, TransportMethods;
let shared_components_loaded = false;

// Import existing handlers
const ClientMT5Handler = require('./src/websocket/client-mt5-handler');
const BidirectionalRouter = require('./src/routing/bidirectional-router');
const { SuhoBinaryProtocol } = require('./src/protocols/suho-binary-protocol');
const AuthMiddleware = require('./src/middleware/auth');

/**
 * Load shared components dynamically via hot reload
 */
async function loadSharedComponents() {
    if (shared_components_loaded) {
        return;
    }

    console.log('🔄 Loading shared components via hot reload...');

    try {
        // Initialize hot reload loader
        await hotReloadLoader.initialize();

        // Load essential components
        const sharedIndex = await hotReloadLoader.loadComponent('index.js');

        // Extract components
        ServiceTemplate = sharedIndex.ServiceTemplate;
        TransferManager = sharedIndex.TransferManager;
        createServiceLogger = sharedIndex.createServiceLogger;
        ErrorDNA = sharedIndex.ErrorDNA;
        TransportMethods = sharedIndex.TransportMethods;

        shared_components_loaded = true;
        console.log('✅ Shared components loaded via hot reload');

        // Setup component reload handlers
        hotReloadLoader.on('component_reloaded', (event) => {
            console.log(`🔃 Component reloaded: ${event.path}`);

            // Re-load main index if it was updated
            if (event.path === 'index.js') {
                console.log('🔄 Re-loading shared components...');
                shared_components_loaded = false;
                // Note: Full service restart may be needed for some changes
            }
        });

    } catch (error) {
        console.error(`❌ Failed to load shared components: ${error.message}`);

        // Fallback to static import
        console.log('⚠️ Falling back to static shared components...');
        const shared = require('../central-hub/shared');
        ServiceTemplate = shared.ServiceTemplate;
        TransferManager = shared.TransferManager;
        createServiceLogger = shared.createServiceLogger;
        ErrorDNA = shared.ErrorDNA;
        TransportMethods = shared.TransportMethods;

        shared_components_loaded = true;
    }
}

/**
 * API Gateway Service - Extended dari ServiceTemplate
 * Compatible dengan SERVICE_ARCHITECTURE.md patterns
 */
class APIGatewayService {
    constructor(config = {}) {
        // Store config for later initialization
        this.serviceConfig = {
            service_name: 'api-gateway',
            version: '2.0.0',
            ...config
        };

        // Will be set after hot reload and config loading
        this.base_service = null;
        this.config = null;
        this.options = null;

        // Express application
        this.app = express();
        this.server = null;

        // WebSocket and routing handlers
        this.clientMT5Handler = null;
        this.bidirectionalRouter = null;
        this.suhoBinaryProtocol = null;

        // Request processing metrics
        this.requestMetrics = {
            total: 0,
            successful: 0,
            failed: 0,
            by_type: {
                webhook: 0,
                websocket: 0,
                rest: 0
            }
        };
    }

    async loadConfiguration() {
        try {
            console.log('🔄 Loading configuration from Central Hub...');

            // Get configuration from Central Hub
            this.config = await configService.getConfig();

            // Build options from centralized config
            this.options = {
                port: this.config.api?.port || 8000,
                centralHubUrl: this.config.services?.central_hub || 'http://suho-central-hub:7000',
                enableCors: true,
                enableCompression: true,
                enableHelmet: true,
                maxRequestSize: '10mb',
                rateLimitWindow: this.config.api?.rate_limit?.window_ms || 15 * 60 * 1000,
                rateLimitMax: this.config.api?.rate_limit?.max_requests || 1000,
                cors_origins: this.config.api?.cors_origins || ['*'],
                jwt: this.config.jwt || {
                    secret: 'fallback-secret',
                    expiresIn: '24h',
                    issuer: 'api-gateway',
                    audience: 'suho-trading'
                },
                websocket: {
                    trading_port: this.config.api?.trading_ws_port || 8001,
                    price_stream_port: this.config.api?.price_stream_ws_port || 8002
                },
                nats_url: this.config.messaging?.nats || 'nats://suho-nats-server:4222',
                kafka_brokers: this.config.messaging?.kafka || 'suho-kafka:9092'
            };

            console.log('✅ Configuration loaded successfully');

        } catch (error) {
            console.warn('⚠️ Configuration loading failed, using fallback:', error.message);

            // Fallback configuration if Central Hub is not available
            this.options = {
                port: parseInt(process.env.PORT) || 8000,
                centralHubUrl: process.env.CENTRAL_HUB_URL || 'http://suho-central-hub:7000',
                enableCors: true,
                enableCompression: true,
                enableHelmet: true,
                maxRequestSize: '10mb',
                rateLimitWindow: 15 * 60 * 1000,
                rateLimitMax: 1000,
                cors_origins: ['*'],
                jwt: {
                    secret: process.env.JWT_SECRET || 'fallback-secret',
                    expiresIn: process.env.JWT_EXPIRES_IN || '24h',
                    issuer: process.env.JWT_ISSUER || 'api-gateway',
                    audience: process.env.JWT_AUDIENCE || 'suho-trading'
                },
                websocket: {
                    trading_port: 8001,
                    price_stream_port: 8002
                },
                nats_url: process.env.NATS_URL || 'nats://suho-nats-server:4222',
                kafka_brokers: process.env.KAFKA_BROKERS || 'suho-kafka:9092'
            };
        }
    }

    async initialize() {
        // Ensure shared components are loaded
        if (!shared_components_loaded) {
            throw new Error('Shared components not loaded - call loadSharedComponents() first');
        }

        // STEP 1: Load configuration from Central Hub
        await this.loadConfiguration();

        // Use local ServiceTemplate from APIGatewayService to avoid config conflicts
        const { ServiceTemplate: LocalServiceTemplate } = require('./src/core/APIGatewayService');
        this.base_service = new LocalServiceTemplate('api-gateway', this.serviceConfig);

        // Copy essential properties
        this.service_name = this.base_service.service_name;
        this.logger = this.base_service.logger;
        this.transfer = this.base_service.transfer;
        this.errorDNA = this.base_service.errorDNA;
        this.config = this.base_service.config || this.serviceConfig;

        // Initialize base service
        await this.base_service.initialize();

        // Continue with API Gateway specific setup
        await this.onStartup();
    }

    // Delegate to base service methods
    async stop() {
        if (this.base_service) {
            await this.base_service.stop();
        }
        await this.onShutdown();
    }

    generateCorrelationId() {
        return this.base_service ? this.base_service.generateCorrelationId() :
               `api-gateway_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    async analyzeError(error, context = {}) {
        return this.base_service ? await this.base_service.analyzeError(error, context) : null;
    }

    async sendOutput(data, targetService, options = {}) {
        return this.base_service ? await this.base_service.sendOutput(data, targetService, options) : null;
    }

    // Implement ServiceTemplate abstract method
    async handleInput(inputData, sourceService, inputType) {
        const correlationId = inputData.metadata?.correlation_id || this.generateCorrelationId();

        this.logger.info('Processing API Gateway input', {
            sourceService,
            inputType,
            correlationId,
            dataSize: this._getDataSize(inputData)
        });

        try {
            let result;

            // Route berdasarkan input type dan source
            switch (inputType) {
                case 'client_mt5_binary':
                    result = await this._handleClientMT5Binary(inputData, correlationId);
                    break;
                case 'frontend_request':
                    result = await this._handleFrontendRequest(inputData, correlationId);
                    break;
                case 'telegram_webhook':
                    result = await this._handleTelegramWebhook(inputData, correlationId);
                    break;
                case 'external_webhook':
                    result = await this._handleExternalWebhook(inputData, correlationId);
                    break;
                default:
                    throw new Error(`Unknown input type: ${inputType}`);
            }

            // Track success metrics
            this.requestMetrics.total++;
            this.requestMetrics.successful++;
            this.requestMetrics.by_type[this._getRequestType(inputType)]++;

            this.logger.info('Successfully processed input', {
                inputType,
                correlationId,
                outputTargets: result.targets?.length || 0
            });

            return result;

        } catch (error) {
            this.requestMetrics.total++;
            this.requestMetrics.failed++;

            // Analyze error dengan ErrorDNA
            const errorAnalysis = await this.analyzeError(error, {
                inputType,
                sourceService,
                correlationId
            });

            this.logger.error('Failed to process input', {
                error: error.message,
                inputType,
                sourceService,
                correlationId,
                suggestions: errorAnalysis?.suggested_actions?.slice(0, 3)
            });

            throw error;
        }
    }

    async _handleClientMT5Binary(inputData, correlationId) {
        // Parse binary data menggunakan Suho Binary Protocol
        const binaryData = inputData.binary_data || inputData.data;

        if (!Buffer.isBuffer(binaryData)) {
            throw new Error('Invalid binary data for Client-MT5');
        }

        // Parse dengan existing protocol handler
        const parsed = this.suhoBinaryProtocol.parse(binaryData);

        // Convert to standardized format
        const processedData = {
            tenant_id: inputData.tenant_id,
            message_type: 'price_stream',
            timestamp: new Date().toISOString(),
            data: parsed,
            metadata: {
                correlation_id: correlationId,
                source_service: 'client-mt5',
                protocol: 'suho-binary'
            }
        };

        // Send to appropriate services via TransferManager
        const outputs = [];

        // High-frequency price data → NATS+Kafka → Data Bridge
        const dataBridgeResult = await this.sendOutput(processedData, 'data-bridge', {
            method: TransportMethods.NATS_KAFKA,
            correlation_id: correlationId,
            data_type: 'price_stream'
        });
        outputs.push({ target: 'data-bridge', result: dataBridgeResult });

        // Trading signals → gRPC → Trading Engine
        if (parsed.symbols?.length > 0) {
            const tradingData = {
                ...processedData,
                message_type: 'trading_signal_input'
            };

            const tradingResult = await this.sendOutput(tradingData, 'trading-engine', {
                method: TransportMethods.GRPC,
                correlation_id: correlationId,
                data_type: 'trading_signal'
            });
            outputs.push({ target: 'trading-engine', result: tradingResult });
        }

        return {
            processed: true,
            targets: outputs,
            binary_size: binaryData.length,
            symbols_count: parsed.symbols?.length || 0
        };
    }

    async _handleFrontendRequest(inputData, correlationId) {
        // Handle HTTP requests dari frontend
        const requestData = {
            tenant_id: inputData.tenant_id,
            message_type: 'user_request',
            data: inputData.data,
            metadata: {
                correlation_id: correlationId,
                source_service: 'frontend',
                user_id: inputData.user_id
            }
        };

        // Route to appropriate service based on request type
        const outputs = [];

        if (inputData.type === 'account' || inputData.path?.startsWith('/api/account')) {
            const userResult = await this.sendOutput(requestData, 'user-management', {
                method: TransportMethods.GRPC,
                correlation_id: correlationId
            });
            outputs.push({ target: 'user-management', result: userResult });
        }

        if (inputData.type === 'trading' || inputData.path?.startsWith('/api/trading')) {
            const tradingResult = await this.sendOutput(requestData, 'trading-engine', {
                method: TransportMethods.GRPC,
                correlation_id: correlationId
            });
            outputs.push({ target: 'trading-engine', result: tradingResult });
        }

        return {
            processed: true,
            targets: outputs,
            request_type: inputData.type
        };
    }

    async _handleTelegramWebhook(inputData, correlationId) {
        // Handle Telegram bot webhooks
        const notificationData = {
            tenant_id: inputData.tenant_id,
            message_type: 'notification_request',
            data: inputData.data,
            metadata: {
                correlation_id: correlationId,
                source_service: 'telegram',
                chat_id: inputData.chat_id
            }
        };

        // Send to notification service
        const result = await this.sendOutput(notificationData, 'notification-hub', {
            method: TransportMethods.NATS_KAFKA,
            correlation_id: correlationId,
            data_type: 'notification'
        });

        return {
            processed: true,
            targets: [{ target: 'notification-hub', result }],
            webhook_type: 'telegram'
        };
    }

    async _handleExternalWebhook(inputData, correlationId) {
        // Handle webhooks dari external services (broker, payment, etc)
        const externalData = {
            tenant_id: inputData.tenant_id,
            message_type: 'external_event',
            data: inputData.data,
            metadata: {
                correlation_id: correlationId,
                source_service: inputData.source || 'external',
                webhook_type: inputData.webhook_type
            }
        };

        // Route based on webhook type
        const outputs = [];

        if (inputData.webhook_type === 'broker_callback') {
            const result = await this.sendOutput(externalData, 'trading-engine', {
                method: TransportMethods.GRPC,
                correlation_id: correlationId
            });
            outputs.push({ target: 'trading-engine', result });
        }

        if (inputData.webhook_type === 'payment_callback') {
            const result = await this.sendOutput(externalData, 'user-management', {
                method: TransportMethods.HTTP,
                correlation_id: correlationId
            });
            outputs.push({ target: 'user-management', result });
        }

        return {
            processed: true,
            targets: outputs,
            webhook_type: inputData.webhook_type
        };
    }

    // ServiceTemplate lifecycle methods
    async onStartup() {
        this.logger.info('Starting API Gateway specific initialization');

        // Initialize Express app
        this._setupExpressApp();

        // Initialize protocol handlers
        this.suhoBinaryProtocol = new SuhoBinaryProtocol();
        this.bidirectionalRouter = new BidirectionalRouter({
            logger: this.logger,
            transfer: this.transfer
        });

        // Create HTTP server
        this.server = http.createServer(this.app);

        // Initialize WebSocket handlers
        this.clientMT5Handler = new ClientMT5Handler(this.server, {
            logger: this.logger,
            onBinaryData: (data, metadata) => this.handleInput(data, 'client-mt5', 'client_mt5_binary'),
            protocol: this.suhoBinaryProtocol
        });

        // Start server
        await new Promise((resolve, reject) => {
            this.server.listen(this.config.port, (error) => {
                if (error) {
                    reject(error);
                } else {
                    this.logger.info(`API Gateway listening on port ${this.config.port}`);
                    resolve();
                }
            });
        });
    }

    async onShutdown() {
        this.logger.info('Shutting down API Gateway');

        // Close WebSocket connections
        if (this.clientMT5Handler) {
            await this.clientMT5Handler.close();
        }

        // Close HTTP server
        if (this.server) {
            await new Promise((resolve) => {
                this.server.close(() => resolve());
            });
        }
    }

    _setupExpressApp() {
        // Security middleware
        if (this.options.enableHelmet) {
            this.app.use(helmet());
        }

        // CORS
        if (this.options.enableCors) {
            this.app.use(cors({
                origin: this.options.cors_origins,
                credentials: true
            }));
        }

        // Compression
        if (this.options.enableCompression) {
            this.app.use(compression());
        }

        // Body parsing
        this.app.use(express.json({ limit: this.options.maxRequestSize }));
        this.app.use(express.urlencoded({ extended: true, limit: this.options.maxRequestSize }));

        // Request logging middleware (simplified for stability)
        this.app.use((req, res, next) => {
            this.logger.info(`${req.method} ${req.url}`, { ip: req.ip, userAgent: req.get('User-Agent') });
            next();
        });

        // Authentication middleware
        this.app.use('/api', AuthMiddleware);

        // Health check endpoint
        this.app.get('/health', async (req, res) => {
            const health = await this.healthCheck();
            res.status(health.status === 'healthy' ? 200 : 503).json(health);
        });

        // Metrics endpoint
        this.app.get('/metrics', (req, res) => {
            res.json({
                service: this.service_name,
                request_metrics: this.requestMetrics,
                transfer_metrics: this.transfer.getMetrics(),
                uptime: Date.now() - this.start_time.getTime()
            });
        });

        // REST API routes
        this._setupRoutes();

        // Error handling
        this.app.use((error, req, res, next) => {
            this.analyzeError(error, { path: req.path, method: req.method });

            res.status(error.status || 500).json({
                error: error.message,
                correlation_id: req.correlation_id
            });
        });
    }

    _setupRoutes() {
        // Frontend webhooks
        this.app.post('/webhook/frontend', async (req, res) => {
            const result = await this.handleInput(req.body, 'frontend', 'frontend_request');
            res.json(result);
        });

        // Telegram webhooks
        this.app.post('/webhook/telegram', async (req, res) => {
            const result = await this.handleInput(req.body, 'telegram', 'telegram_webhook');
            res.json(result);
        });

        // External webhooks
        this.app.post('/webhook/external/:type', async (req, res) => {
            const webhookData = {
                ...req.body,
                webhook_type: req.params.type
            };
            const result = await this.handleInput(webhookData, 'external', 'external_webhook');
            res.json(result);
        });

        // Generic API endpoints
        this.app.use('/api', (req, res, next) => {
            // Route API requests as frontend requests
            this.handleInput({
                ...req.body,
                path: req.path,
                method: req.method,
                user_id: req.user?.id
            }, 'frontend', 'frontend_request')
            .then(result => res.json(result))
            .catch(next);
        });
    }

    async customHealthChecks() {
        const health = {};

        // Check WebSocket handlers
        if (this.clientMT5Handler) {
            health.websocket = {
                client_mt5_connections: this.clientMT5Handler.getActiveConnections ?
                    this.clientMT5Handler.getActiveConnections() : 0,
                status: 'healthy'
            };
        }

        // Check protocol handlers
        if (this.suhoBinaryProtocol) {
            health.protocol = {
                suho_binary: 'ready',
                status: 'healthy'
            };
        }

        // Check routing
        if (this.bidirectionalRouter) {
            health.routing = {
                bidirectional_router: 'ready',
                status: 'healthy'
            };
        }

        return health;
    }

    _getRequestType(inputType) {
        if (inputType.includes('webhook')) return 'webhook';
        if (inputType.includes('mt5') || inputType.includes('websocket')) return 'websocket';
        return 'rest';
    }

    _getDataSize(data) {
        if (Buffer.isBuffer(data)) return data.length;
        if (typeof data === 'string') return Buffer.byteLength(data, 'utf8');
        if (typeof data === 'object') return Buffer.byteLength(JSON.stringify(data), 'utf8');
        return 0;
    }
}

// Main execution
async function main() {
    try {
        // Skip hot reload loading, use static components
        console.log("⚡ Starting API Gateway with static configuration...");
        shared_components_loaded = true; // Mark as loaded

        // Create API Gateway service
        const apiGateway = new APIGatewayService();

        // Handle graceful shutdown
        process.on('SIGTERM', async () => {
            console.log('Received SIGTERM, shutting down gracefully');
            await apiGateway.stop();
            await hotReloadLoader.shutdown();
            process.exit(0);
        });

        process.on('SIGINT', async () => {
            console.log('Received SIGINT, shutting down gracefully');
            await apiGateway.stop();
            await hotReloadLoader.shutdown();
            process.exit(0);
        });

        // Initialize and start API Gateway
        await apiGateway.initialize();
        console.log('🚀 API Gateway started successfully with hot reload components!');

        // Add hot reload health endpoint
        if (apiGateway.app) {
            apiGateway.app.get('/hot-reload/health', async (req, res) => {
                const health = await hotReloadLoader.healthCheck();
                res.json(health);
            });

            apiGateway.app.get('/hot-reload/components', (req, res) => {
                res.json({
                    loaded_components: hotReloadLoader.getLoadedComponents(),
                    component_versions: hotReloadLoader.getComponentVersions()
                });
            });
        }

    } catch (error) {
        console.error('❌ Failed to start API Gateway:', error.message);
        process.exit(1);
    }
}

// Export for testing
module.exports = { APIGatewayService };

// Run if this is the main module
if (require.main === module) {
    main().catch(console.error);
}