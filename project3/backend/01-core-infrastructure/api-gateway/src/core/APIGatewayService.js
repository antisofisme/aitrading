/**
 * API Gateway Service - Implementation menggunakan ServiceTemplate
 *
 * Mengintegrasikan API Gateway dengan SERVICE_ARCHITECTURE.md patterns:
 * - Multi-tenant support dengan tenant_id
 * - Shared TransferManager untuk komunikasi antar service
 * - Binary protocol handling yang kompatibel dengan Client-MT5
 * - Service coordination dan monitoring
 */

const { createCentralHubClient } = require('./CentralHubClient');
const logger = require('../utils/logger');

/**
 * ServiceTemplate implementation (from SERVICE_ARCHITECTURE.md)
 */
class ServiceTemplate {
    constructor(serviceName, serviceConfig) {
        this.serviceName = serviceName;
        this.config = serviceConfig;

        // ✅ CENTRAL HUB CLIENT (replaces shared components)
        this.centralHub = createCentralHubClient({
            serviceName: serviceName,
            centralHubURL: serviceConfig.centralHubURL || process.env.CENTRAL_HUB_URL,
            timeout: serviceConfig.timeout || 5000
        });

        // ✅ SERVICE LOGGER (local implementation)
        this.logger = logger;

        // ✅ SERVICE-SPECIFIC CORE
        this.core = null; // Initialize di child class

        // ✅ SERVICE STATE
        this.isHealthy = true;
        this.startTime = Date.now();
        this.activeConnections = 0;
        this.requestCount = 0;

        // ✅ METRICS TRACKING
        this.initializeMetrics();
    }

    async initialize() {
        this.logger.info(`Initializing ${this.serviceName}`);

        try {
            // 1. Test Central Hub connection
            const isConnected = await this.centralHub.ping();
            if (!isConnected) {
                throw new Error('Cannot connect to Central Hub');
            }

            // 2. Load service-specific config
            await this.loadConfig();

            // 3. Initialize core business logic
            await this.initializeCore();

            // 4. Register contracts dengan Central Hub (optional)
            await this.registerContracts();

            this.logger.info(`${this.serviceName} initialized successfully`);

        } catch (error) {
            this.logger.error(`Failed to initialize ${this.serviceName}`, { error });
            throw error;
        }
    }

    async loadConfig() {
        // Load service-specific configuration
        this.logger.info(`Loading configuration for ${this.serviceName}`);
        return true;
    }

    async registerContracts() {
        // Register service contracts with Central Hub
        this.logger.info(`Registering contracts for ${this.serviceName}`);
        return true;
    }

    async processInput(inputData, sourceService, inputType) {
        const correlationId = inputData.metadata?.correlationId || this.generateCorrelationId();

        try {
            const startTime = Date.now();
            this.requestCount++;
            this.activeConnections++;

            this.logger.info(`Processing input from ${sourceService}`, {
                inputType,
                correlationId,
                dataSize: this.getDataSize(inputData)
            });

            // ✅ STEP 1: Validate input sesuai contracts/inputs/
            await this.validateInput(inputData, sourceService, inputType);

            // ✅ STEP 2: Process via core business logic
            const result = await this.core.process(inputData, {
                sourceService,
                inputType,
                correlationId
            });

            // ✅ STEP 3: Send output sesuai contracts/outputs/
            await this.sendOutputs(result, correlationId);

            this.logger.info(`Successfully processed input`, { correlationId });

            // ✅ TRACK SUCCESS METRICS
            this.trackRequest(startTime, true);

        } catch (error) {
            this.logger.error(`Failed to process input`, {
                error: error.message,
                correlationId,
                sourceService,
                inputType
            });

            // Error handling via shared components
            await this.handleError(error, correlationId);

            // ✅ TRACK ERROR METRICS
            this.trackRequest(startTime, false);
            throw error;

        } finally {
            this.activeConnections--;
        }
    }

    // Implementation of abstract methods
    async initializeCore() {
        // Implement in APIGatewayCore
        return true;
    }

    async validateInput(inputData, sourceService, inputType) {
        // Multi-tenant validation
        if (!inputData.tenant_id && inputType !== 'heartbeat') {
            throw new Error('tenant_id is required for all requests except heartbeat');
        }
        return true;
    }

    generateCorrelationId() {
        return `${this.serviceName}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    getDataSize(data) {
        if (Buffer.isBuffer(data)) return data.length;
        if (typeof data === 'string') return Buffer.byteLength(data, 'utf8');
        if (typeof data === 'object') return Buffer.byteLength(JSON.stringify(data), 'utf8');
        return 0;
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // ✅ METRICS TRACKING INITIALIZATION
    initializeMetrics() {
        this.responseTimes = [];
        this.requestTimestamps = [];
        this.errorCount = 0;
        this.successfulTransfers = 0;
        this.failedTransfers = 0;
        this.eventLoopLag = 0;

        // Clean old metrics every 5 minutes
        setInterval(() => {
            const fiveMinutesAgo = Date.now() - (5 * 60 * 1000);
            this.responseTimes = this.responseTimes.slice(-1000); // Keep last 1000
            this.requestTimestamps = this.requestTimestamps.filter(ts => ts > fiveMinutesAgo);
        }, 5 * 60 * 1000);
    }

    // ✅ TRACK REQUEST METRICS
    trackRequest(startTime, success = true) {
        const duration = Date.now() - startTime;
        this.responseTimes.push(duration);
        this.requestTimestamps.push(Date.now());

        if (success) {
            this.successfulTransfers++;
        } else {
            this.errorCount++;
            this.failedTransfers++;
        }
    }

    async healthCheck() {
        const health = {
            service: this.serviceName,
            status: this.isHealthy ? 'healthy' : 'unhealthy',
            timestamp: new Date().toISOString(),
            uptime_seconds: Math.floor((Date.now() - this.startTime) / 1000),
            active_connections: this.activeConnections,
            total_requests: this.requestCount,
            shared_components: {},
            core: {}
        };

        try {
            // Check Central Hub connection
            health.central_hub = await this.centralHub.getHealth();

            // Check core business logic
            if (this.core && typeof this.core.healthCheck === 'function') {
                health.core = await this.core.healthCheck();
            }

        } catch (error) {
            health.status = 'degraded';
            health.error = error.message;
            this.isHealthy = false;
        }

        return health;
    }
}

/**
 * API Gateway Core - Business logic untuk API Gateway
 */
class APIGatewayCore {
    constructor(apiGateway) {
        this.apiGateway = apiGateway;
        this.binaryOptimizer = new SuhoBinaryOptimizer();
    }

    async process(inputData, context) {
        const { sourceService, inputType, correlationId } = context;

        // Handle different input types
        switch (inputType) {
            case 'client-mt5-binary':
                return this.processClientMT5Binary(inputData, correlationId);

            case 'backend-service-message':
                return this.processBackendMessage(inputData, sourceService, correlationId);

            case 'websocket-message':
                return this.processWebSocketMessage(inputData, correlationId);

            default:
                throw new Error(`Unknown input type: ${inputType}`);
        }
    }

    async processClientMT5Binary(inputData, correlationId) {
        // Add tenant context to binary data
        const withTenant = this.binaryOptimizer.addTenantContext(
            inputData.binary_data,
            inputData.tenant_id
        );

        // Route to appropriate destination based on message type
        return {
            type: 'routing_result',
            data: withTenant,
            routing_targets: this.determineRoutingTargets(withTenant.message_type),
            metadata: {
                correlationId,
                protocol: 'suho-binary',
                optimized: true
            }
        };
    }

    async processBackendMessage(inputData, sourceService, correlationId) {
        // Handle messages from backend services
        return {
            type: 'backend_processed',
            data: inputData,
            routing_targets: this.determineBackendRoutingTargets(sourceService, inputData),
            metadata: {
                correlationId,
                source: sourceService,
                protocol: 'protobuf'
            }
        };
    }

    async processWebSocketMessage(inputData, correlationId) {
        // Handle WebSocket messages
        return {
            type: 'websocket_processed',
            data: inputData,
            routing_targets: ['frontend-websocket'],
            metadata: {
                correlationId,
                protocol: 'json'
            }
        };
    }

    determineRoutingTargets(messageType) {
        const routingMap = {
            'price_stream': ['data-bridge'],
            'account_profile': ['user-service', 'analytics-service'],
            'trade_command': ['trading-engine'],
            'trade_confirmation': ['data-bridge', 'notification-hub'],
            'heartbeat': [] // No routing needed
        };

        return routingMap[messageType] || [];
    }

    determineBackendRoutingTargets(sourceService, message) {
        // Logic untuk menentukan routing berdasarkan backend service output
        if (message.target_clients) {
            return ['client-mt5-execution'];
        }

        if (message.notify_frontend) {
            return ['frontend-websocket'];
        }

        if (message.send_notification) {
            return ['notification-channels'];
        }

        return [];
    }

    async healthCheck() {
        return {
            binary_optimizer: 'operational',
            routing_engine: 'operational',
            message_types_supported: ['price_stream', 'account_profile', 'trade_command', 'trade_confirmation', 'heartbeat']
        };
    }
}

/**
 * Suho Binary Optimizer - from SERVICE_ARCHITECTURE.md
 */
class SuhoBinaryOptimizer {
    addTenantContext(binaryBuffer, tenantId) {
        const parsed = this.parseSuhoBinary(binaryBuffer);
        parsed.tenant_id = tenantId;

        return {
            tenant_id: tenantId,
            message_type: this.getMessageTypeName(parsed.header.message_type),
            timestamp: new Date(Number(parsed.header.timestamp)).toISOString(),
            binary_data: binaryBuffer,
            parsed_data: parsed,
            metadata: {
                correlation_id: this.generateCorrelationId(),
                source_service: 'client-mt5',
                protocol: 'suho-binary',
                version: parsed.header.version
            }
        };
    }

    parseSuhoBinary(buffer) {
        // Validate buffer
        if (!Buffer.isBuffer(buffer) || buffer.length < 16) {
            throw new Error('Invalid Suho binary buffer');
        }

        // Parse header (16 bytes - matches Client-MT5)
        const header = {
            signature: buffer.readUInt32LE(0),      // bytes 0-3: 'SUHO' (little-endian)
            version: buffer.readUInt16LE(4),        // bytes 4-5: Protocol version
            message_type: buffer.readUInt8(6),      // byte 6: Message type (1 byte)
            symbol_count: buffer.readUInt8(7),      // byte 7: Symbol count (1 byte)
            timestamp: buffer.readBigUInt64LE(8),   // bytes 8-15: Timestamp (little-endian)
        };

        const result = {
            header,
            symbols: []
        };

        // Parse price data (16 bytes per symbol - matches Client-MT5)
        let offset = 16;
        for (let i = 0; i < header.symbol_count; i++) {
            if (offset + 16 > buffer.length) {
                throw new Error(`Insufficient data for symbol ${i}`);
            }

            const symbolData = {
                symbol_id: buffer.readUInt32LE(offset),
                bid_price: buffer.readUInt32LE(offset + 4),
                ask_price: buffer.readUInt32LE(offset + 8),
                flags: buffer.readUInt32LE(offset + 12),
            };

            // Extract spread and server_id from flags
            symbolData.spread = symbolData.flags & 0xFFFF;
            symbolData.server_id = (symbolData.flags >> 16) & 0xFFFF;

            // Convert fixed-point to actual prices
            symbolData.bid = symbolData.bid_price / 100000.0;
            symbolData.ask = symbolData.ask_price / 100000.0;

            result.symbols.push(symbolData);
            offset += 16;
        }

        return result;
    }

    getMessageTypeName(type) {
        const types = {
            1: 'price_stream',
            2: 'account_profile',
            3: 'trade_command',
            4: 'trade_confirmation',
            5: 'heartbeat'
        };
        return types[type] || 'unknown';
    }

    generateCorrelationId() {
        return `mt5_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
}

/**
 * API Gateway Service - Extends ServiceTemplate
 */
class APIGatewayService extends ServiceTemplate {
    constructor(options = {}) {
        super('api-gateway', {
            transfer: {
                nats_url: process.env.NATS_URL || 'nats://localhost:4222',
                kafka_brokers: process.env.KAFKA_BROKERS || 'localhost:9092',
                grpc_port: process.env.GRPC_PORT || 50051
            },
            ...options
        });

        // Initialize core business logic
        this.core = new APIGatewayCore(this);

        // Store options for legacy compatibility
        this.options = {
            port: process.env.PORT || 8000,
            env: process.env.NODE_ENV || 'development',
            ...options
        };
    }

    async initializeCore() {
        // Initialize API Gateway specific components
        this.logger.info('Initializing API Gateway core components');
        return true;
    }

    async sendOutputs(processedData, correlationId) {
        // Send outputs based on routing targets
        for (const target of processedData.routing_targets) {
            try {
                await this.centralHub.sendMessage(
                    target,
                    processedData.data,
                    {
                        correlationId,
                        transportMethod: 'auto',
                        metadata: {
                            source_service: this.serviceName,
                            target_service: target,
                            message_type: processedData.type
                        }
                    }
                );

                this.logger.debug(`Sent output to ${target}`, { correlationId });
            } catch (error) {
                this.logger.error(`Failed to send output to ${target}`, {
                    error: error.message,
                    correlationId
                });
                throw error;
            }
        }
    }

    // Legacy compatibility methods
    async start() {
        await this.initialize();
        this.logger.info(`API Gateway Service started on port ${this.options.port}`);
    }

    async stop() {
        await this.shutdown();
    }

    async shutdown() {
        this.logger.info(`Shutting down ${this.serviceName}`);

        try {
            // 1. Stop accepting new requests
            this.isHealthy = false;

            // 2. Wait for active connections to finish
            while (this.activeConnections > 0) {
                this.logger.info(`Waiting for ${this.activeConnections} active connections`);
                await this.sleep(1000);
            }

            // 3. Shutdown core business logic
            if (this.core && typeof this.core.shutdown === 'function') {
                await this.core.shutdown();
            }

            // 4. Central Hub cleanup (no explicit shutdown needed for HTTP client)
            this.logger.info('Central Hub client will be cleaned up automatically');

            this.logger.info(`${this.serviceName} shutdown complete`);

        } catch (error) {
            this.logger.error(`Error during shutdown`, { error });
        }
    }
}

module.exports = {
    APIGatewayService,
    ServiceTemplate,
    APIGatewayCore,
    SuhoBinaryOptimizer
};