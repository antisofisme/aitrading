/**
 * NATS+Kafka Input Handler: Client-MT5 → API Gateway
 *
 * Specialized handler untuk high-throughput binary data dari MT5 terminal
 * - Handle Suho Binary Protocol dari MT5
 * - WebSocket dan HTTP transport untuk MT5
 * - Multi-tenant MT5 accounts
 * - Real-time price streams, trading commands
 */

const { SuhoBinaryProtocol, MESSAGE_TYPES } = require('../../src/protocols/suho-binary-protocol');

class ClientMT5NatsKafkaHandler {
    constructor(options = {}) {
        this.serviceName = 'client-mt5-natskafka-handler';
        this.binaryProtocol = new SuhoBinaryProtocol();
        this.options = {
            enableValidation: true,
            enableConversion: false, // TERIMA SAJA, TIDAK CONVERT
            enableRouting: true,
            logLevel: 'info',
            ...options
        };

        this.stats = {
            totalReceived: 0,
            priceStreamCount: 0,
            tradingCommandCount: 0,
            accountProfileCount: 0,
            executionConfirmCount: 0,
            errorCount: 0,
            lastReceivedAt: null
        };
    }

    /**
     * Handle incoming binary data dari Client-MT5
     * @param {Buffer} binaryData - Raw binary data (Suho protocol)
     * @param {Object} metadata - Request metadata
     * @param {Object} context - MT5 context (tenant, user, session)
     * @returns {Object} Processing result
     */
    async handleInput(binaryData, metadata = {}, context = {}) {
        const startTime = Date.now();

        try {
            console.log('📈 [CLIENT-MT5-NATSKAFKA] Binary data received:', {
                dataLength: binaryData?.length,
                tenantId: context.tenant_id,
                transport: metadata.transport,
                correlationId: metadata.correlationId
            });

            // Basic validation
            const validation = this.validateInput(binaryData, metadata, context);
            if (!validation.isValid) {
                return this.createErrorResponse('VALIDATION_FAILED', validation.errors, metadata);
            }

            // Process raw binary data (NO CONVERSION)
            const rawDataInfo = this.processRawData(binaryData, metadata, context);

            // Optional: Parse binary untuk routing decisions
            let parsedData = null;
            let routingHint = 'general';

            if (this.options.enableConversion) {
                try {
                    parsedData = this.binaryProtocol.parsePacket(binaryData);
                    routingHint = parsedData.type;
                    this.updateStats(parsedData.type);
                } catch (parseError) {
                    console.warn('⚠️ [CLIENT-MT5-NATSKAFKA] Parse failed, using raw routing:', parseError.message);
                }
            }

            // Determine routing targets (high-throughput services)
            const routingTargets = this.determineRouting(rawDataInfo, routingHint, context);

            this.updateStats(routingHint);
            this.stats.lastReceivedAt = new Date().toISOString();

            return {
                success: true,
                message: 'Client-MT5 binary data processed successfully',
                data: {
                    raw_data_info: rawDataInfo,
                    parsed_data: parsedData, // null jika conversion disabled
                    tenant_id: context.tenant_id,
                    processing_time_ms: Date.now() - startTime,
                    transport_method: 'nats-kafka'
                },
                routing_targets: routingTargets,
                metadata: {
                    correlationId: metadata.correlationId,
                    timestamp: new Date().toISOString(),
                    handler: this.serviceName
                }
            };

        } catch (error) {
            this.stats.errorCount++;
            console.error('❌ [CLIENT-MT5-NATSKAFKA] Processing error:', error);

            return this.createErrorResponse('PROCESSING_ERROR', [error.message], metadata);
        }
    }

    validateInput(binaryData, metadata, context) {
        const errors = [];

        // Check binary data
        if (!binaryData || !Buffer.isBuffer(binaryData)) {
            errors.push('Binary data is required and must be a Buffer');
        }

        if (binaryData && binaryData.length === 0) {
            errors.push('Binary data cannot be empty');
        }

        // Check size limits
        if (binaryData && binaryData.length > 1024 * 1024) { // 1MB limit
            errors.push('Binary data too large (max 1MB)');
        }

        // Check tenant (multi-tenant requirement)
        if (!context.tenant_id) {
            errors.push('Tenant ID is required for Client-MT5 data');
        }

        return { isValid: errors.length === 0, errors };
    }

    processRawData(binaryData, metadata, context) {
        const rawInfo = {
            data_length: binaryData.length,
            is_buffer: Buffer.isBuffer(binaryData),
            tenant_id: context.tenant_id,
            transport: metadata.transport || 'unknown',
            received_at: new Date().toISOString(),
            data_hash: this.calculateDataHash(binaryData)
        };

        // Try to identify Suho protocol tanpa full parsing
        if (binaryData.length >= 16) {
            try {
                const magic = binaryData.readUInt32LE(0);
                const version = binaryData.readUInt16LE(4);
                const msgType = binaryData.readUInt8(6);

                rawInfo.suspected_protocol = {
                    is_suho_format: magic === 0x53554854,
                    magic_hex: magic.toString(16),
                    version,
                    message_type: msgType,
                    likely_suho: magic === 0x53554854 && version === 1
                };
            } catch (error) {
                rawInfo.suspected_protocol = {
                    is_suho_format: false,
                    parse_error: 'Could not read header'
                };
            }
        }

        return rawInfo;
    }

    determineRouting(rawInfo, routingHint, context) {
        const targets = [];

        // NATS+Kafka: High-throughput routing

        // Primary: Data Bridge (raw storage)
        targets.push({
            service: 'data-bridge',
            priority: 'critical',
            transport_method: 'nats-kafka',
            reason: 'High-throughput raw data storage and processing'
        });

        // Secondary: Route berdasarkan suspected message type
        if (rawInfo.suspected_protocol?.is_suho_format) {
            switch (routingHint) {
                case 'price_stream':
                    targets.push({
                        service: 'ml-processing',
                        priority: 'high',
                        transport_method: 'nats-kafka',
                        reason: 'Real-time price analysis via NATS+Kafka'
                    });
                    break;

                case 'trading_command':
                    targets.push({
                        service: 'trading-engine',
                        priority: 'critical',
                        transport_method: 'grpc',
                        reason: 'Trading execution via gRPC'
                    });
                    break;

                case 'execution_confirm':
                    targets.push({
                        service: 'analytics-service',
                        priority: 'high',
                        transport_method: 'grpc',
                        reason: 'Execution tracking via gRPC'
                    });
                    break;

                default:
                    // General MT5 data
                    targets.push({
                        service: 'analytics-service',
                        priority: 'medium',
                        transport_method: 'nats-kafka',
                        reason: 'General MT5 data processing'
                    });
            }
        }

        return targets;
    }

    updateStats(messageType) {
        this.stats.totalReceived++;

        switch (messageType) {
            case 'price_stream':
                this.stats.priceStreamCount++;
                break;
            case 'trading_command':
                this.stats.tradingCommandCount++;
                break;
            case 'account_profile':
                this.stats.accountProfileCount++;
                break;
            case 'execution_confirm':
                this.stats.executionConfirmCount++;
                break;
        }
    }

    calculateDataHash(data) {
        const crypto = require('crypto');
        return crypto.createHash('sha256').update(data).digest('hex').substring(0, 16);
    }

    createErrorResponse(errorType, errors, metadata) {
        this.stats.errorCount++;

        return {
            success: false,
            error: {
                type: errorType,
                message: errors.join('; '),
                details: errors,
                timestamp: new Date().toISOString(),
                correlationId: metadata.correlationId
            },
            data: null,
            routing_targets: [],
            metadata: {
                correlationId: metadata.correlationId,
                timestamp: new Date().toISOString(),
                handler: this.serviceName
            }
        };
    }

    getStats() {
        return {
            ...this.stats,
            error_rate: this.stats.totalReceived > 0 ? this.stats.errorCount / this.stats.totalReceived : 0
        };
    }

    async healthCheck() {
        const stats = this.getStats();

        return {
            status: stats.error_rate < 0.1 ? 'healthy' : 'degraded',
            service: this.serviceName,
            stats,
            transport_method: 'nats-kafka',
            timestamp: new Date().toISOString()
        };
    }
}

module.exports = {
    ClientMT5NatsKafkaHandler,
    MESSAGE_TYPES
};