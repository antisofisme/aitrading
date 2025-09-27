/**
 * Webhook Input Handler: Telegram Bot → API Gateway
 *
 * Specialized handler untuk webhook dari Telegram Bot API
 * - Handle webhook POST requests dari Telegram Bot
 * - Parse Telegram update objects
 * - Route ke appropriate backend services
 */

class TelegramWebhookHandler {
    constructor(options = {}) {
        this.serviceName = 'telegram-webhook-handler';
        this.options = {
            enableValidation: true,
            enableRouting: true,
            botToken: process.env.TELEGRAM_BOT_TOKEN,
            logLevel: 'info',
            ...options
        };

        this.stats = {
            totalReceived: 0,
            textMessages: 0,
            callbackQueries: 0,
            errorCount: 0,
            lastReceivedAt: null
        };
    }

    /**
     * Handle incoming Telegram webhook
     * @param {Object} telegramUpdate - Telegram update object dari webhook
     * @param {Object} metadata - Request metadata (headers, etc)
     * @param {Object} context - Request context
     * @returns {Object} Processing result
     */
    async handleInput(telegramUpdate, metadata = {}, context = {}) {
        const startTime = Date.now();

        try {
            console.log('💬 [TELEGRAM-WEBHOOK] Update received:', {
                updateId: telegramUpdate.update_id,
                type: this.getUpdateType(telegramUpdate),
                userId: this.getTelegramUserId(telegramUpdate),
                correlationId: metadata.correlationId
            });

            // Validate webhook
            const validation = this.validateWebhook(telegramUpdate, metadata);
            if (!validation.isValid) {
                return this.createErrorResponse('VALIDATION_FAILED', validation.errors, metadata);
            }

            // Process Telegram update
            const processedData = this.processTelegramUpdate(telegramUpdate, metadata, context);

            // Determine routing targets
            const routingTargets = this.determineRouting(processedData, context);

            this.updateStats(processedData.type);
            this.stats.lastReceivedAt = new Date().toISOString();

            return {
                success: true,
                message: 'Telegram webhook processed successfully',
                data: {
                    processed_data: processedData,
                    telegram_user_id: processedData.telegram_user_id,
                    processing_time_ms: Date.now() - startTime
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
            console.error('❌ [TELEGRAM-WEBHOOK] Processing error:', error);

            return this.createErrorResponse('PROCESSING_ERROR', [error.message], metadata);
        }
    }

    validateWebhook(telegramUpdate, metadata) {
        const errors = [];

        if (!telegramUpdate || !telegramUpdate.update_id) {
            errors.push('Valid Telegram update object required');
        }

        // Validate bot token jika ada
        if (this.options.botToken && metadata.botToken !== this.options.botToken) {
            errors.push('Invalid bot token');
        }

        return { isValid: errors.length === 0, errors };
    }

    processTelegramUpdate(telegramUpdate, metadata, context) {
        const updateType = this.getUpdateType(telegramUpdate);
        const telegramUserId = this.getTelegramUserId(telegramUpdate);

        return {
            type: 'telegram_webhook',
            update_type: updateType,
            update_id: telegramUpdate.update_id,
            telegram_user_id: telegramUserId,
            raw_update: telegramUpdate,
            timestamp: new Date().toISOString(),
            transport_method: 'webhook'
        };
    }

    determineRouting(processedData, context) {
        const targets = [];

        // Route berdasarkan update type
        switch (processedData.update_type) {
            case 'message':
                if (processedData.raw_update.message?.text?.startsWith('/trade')) {
                    targets.push({
                        service: 'trading-engine',
                        priority: 'high',
                        transport_method: 'grpc',
                        reason: 'Trading command dari Telegram'
                    });
                } else {
                    targets.push({
                        service: 'notification-hub',
                        priority: 'medium',
                        transport_method: 'http-rest',
                        reason: 'Text message processing'
                    });
                }
                break;

            case 'callback_query':
                targets.push({
                    service: 'notification-hub',
                    priority: 'medium',
                    transport_method: 'http-rest',
                    reason: 'Callback query response'
                });
                break;

            default:
                targets.push({
                    service: 'notification-hub',
                    priority: 'low',
                    transport_method: 'http-rest',
                    reason: 'General Telegram update'
                });
        }

        return targets;
    }

    getUpdateType(telegramUpdate) {
        if (telegramUpdate.message) return 'message';
        if (telegramUpdate.callback_query) return 'callback_query';
        if (telegramUpdate.inline_query) return 'inline_query';
        return 'unknown';
    }

    getTelegramUserId(telegramUpdate) {
        if (telegramUpdate.message) return telegramUpdate.message.from.id;
        if (telegramUpdate.callback_query) return telegramUpdate.callback_query.from.id;
        if (telegramUpdate.inline_query) return telegramUpdate.inline_query.from.id;
        return null;
    }

    updateStats(type) {
        this.stats.totalReceived++;
        switch (type) {
            case 'message': this.stats.textMessages++; break;
            case 'callback_query': this.stats.callbackQueries++; break;
        }
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
        return this.stats;
    }

    async healthCheck() {
        return {
            status: 'healthy',
            service: this.serviceName,
            stats: this.getStats(),
            timestamp: new Date().toISOString()
        };
    }
}

module.exports = {
    TelegramWebhookHandler
};