/**
 * Webhook Input Handler: Frontend → API Gateway
 *
 * Specialized handler untuk requests dari Frontend web/mobile dashboard
 * - Handle HTTP requests dari React/Vue frontend
 * - Parse JSON data dan user context
 * - Route ke appropriate backend services
 */

class FrontendWebhookHandler {
    constructor(options = {}) {
        this.serviceName = 'frontend-webhook-handler';
        this.options = {
            enableValidation: true,
            enableRouting: true,
            requireAuth: true,
            logLevel: 'info',
            ...options
        };

        this.stats = {
            totalReceived: 0,
            dashboardRequests: 0,
            tradingRequests: 0,
            configRequests: 0,
            errorCount: 0,
            lastReceivedAt: null
        };
    }

    /**
     * Handle incoming Frontend request
     * @param {Object} requestData - JSON data dari frontend
     * @param {Object} metadata - Request metadata (headers, endpoint, etc)
     * @param {Object} context - User context (auth, session, etc)
     * @returns {Object} Processing result
     */
    async handleInput(requestData, metadata = {}, context = {}) {
        const startTime = Date.now();

        try {
            console.log('🖥️ [FRONTEND-WEBHOOK] Request received:', {
                endpoint: metadata.endpoint,
                method: metadata.method,
                userId: context.user_id,
                correlationId: metadata.correlationId
            });

            // Validate frontend request
            const validation = this.validateRequest(requestData, metadata, context);
            if (!validation.isValid) {
                return this.createErrorResponse('VALIDATION_FAILED', validation.errors, metadata);
            }

            // Process frontend request
            const processedData = this.processFrontendRequest(requestData, metadata, context);

            // Determine routing targets
            const routingTargets = this.determineRouting(processedData, context);

            this.updateStats(processedData.request_category);
            this.stats.lastReceivedAt = new Date().toISOString();

            return {
                success: true,
                message: 'Frontend request processed successfully',
                data: {
                    processed_data: processedData,
                    user_id: context.user_id,
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
            console.error('❌ [FRONTEND-WEBHOOK] Processing error:', error);

            return this.createErrorResponse('PROCESSING_ERROR', [error.message], metadata);
        }
    }

    validateRequest(requestData, metadata, context) {
        const errors = [];

        if (!requestData || typeof requestData !== 'object') {
            errors.push('Valid JSON object is required');
        }

        if (this.options.requireAuth && !context.user_id) {
            errors.push('Authentication required for frontend requests');
        }

        if (!metadata.endpoint) {
            errors.push('Endpoint information required');
        }

        return { isValid: errors.length === 0, errors };
    }

    processFrontendRequest(requestData, metadata, context) {
        const requestCategory = this.categorizeRequest(metadata.endpoint);

        return {
            type: 'frontend_webhook',
            request_category: requestCategory,
            endpoint: metadata.endpoint,
            method: metadata.method,
            data: requestData,
            user_context: {
                user_id: context.user_id,
                session_id: context.session_id,
                permissions: context.permissions || []
            },
            timestamp: new Date().toISOString(),
            transport_method: 'webhook'
        };
    }

    categorizeRequest(endpoint) {
        if (endpoint.includes('/trading/')) return 'trading';
        if (endpoint.includes('/dashboard/')) return 'dashboard';
        if (endpoint.includes('/analytics/')) return 'analytics';
        if (endpoint.includes('/config/') || endpoint.includes('/settings/')) return 'config';
        if (endpoint.includes('/user/')) return 'user';
        return 'general';
    }

    determineRouting(processedData, context) {
        const targets = [];

        // Route berdasarkan category dan endpoint
        switch (processedData.request_category) {
            case 'trading':
                targets.push({
                    service: 'trading-engine',
                    priority: 'high',
                    transport_method: 'grpc',
                    reason: 'Trading request dari frontend'
                });
                break;

            case 'dashboard':
            case 'analytics':
                targets.push({
                    service: 'analytics-service',
                    priority: 'medium',
                    transport_method: 'grpc',
                    reason: 'Dashboard/analytics data request'
                });
                break;

            case 'config':
            case 'user':
                targets.push({
                    service: 'user-management',
                    priority: 'medium',
                    transport_method: 'http-rest',
                    reason: 'User/config management'
                });
                break;

            default:
                targets.push({
                    service: 'notification-hub',
                    priority: 'low',
                    transport_method: 'http-rest',
                    reason: 'General frontend request'
                });
        }

        return targets;
    }

    updateStats(category) {
        this.stats.totalReceived++;
        switch (category) {
            case 'trading': this.stats.tradingRequests++; break;
            case 'dashboard': this.stats.dashboardRequests++; break;
            case 'config': this.stats.configRequests++; break;
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
    FrontendWebhookHandler
};