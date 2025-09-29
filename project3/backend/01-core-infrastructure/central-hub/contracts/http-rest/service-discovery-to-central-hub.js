/**
 * Central Hub Contract: Service Discovery Request (Inbound)
 * Pattern: many-to-one (services → central-hub)
 * Transport: HTTP REST
 *
 * Services request discovery of other services dari Central Hub
 */

const Joi = require('joi');

/**
 * Input validation schema untuk service discovery request
 */
const ServiceDiscoverySchema = Joi.object({
    // Discovery request parameters
    service_name: Joi.string().optional(), // Specific service name or null for all
    service_type: Joi.string().valid('api-gateway', 'trading-engine', 'data-bridge', 'analytics', 'ml-service', 'notification').optional(),
    environment: Joi.string().valid('development', 'staging', 'production').optional(),

    // Filtering criteria
    filters: Joi.object({
        status: Joi.string().valid('active', 'inactive', 'unhealthy').default('active'),
        capabilities: Joi.array().items(Joi.string()).optional(),
        transport_support: Joi.string().valid('http', 'grpc', 'nats-kafka').optional(),
        min_load_capacity: Joi.number().min(0).max(100).optional()
    }).default({}),

    // Request metadata
    requester_service: Joi.string().required(),
    request_purpose: Joi.string().valid('load_balancing', 'direct_communication', 'health_check', 'monitoring').default('direct_communication')
});

/**
 * Process service discovery request
 */
function processServiceDiscovery(inputData, context = {}) {
    // Validate input
    const { error, value } = ServiceDiscoverySchema.validate(inputData);
    if (error) {
        throw new Error(`Service discovery validation failed: ${error.details[0].message}`);
    }

    const discoveryRequest = value;

    // Add system metadata
    discoveryRequest.request_id = `discovery-${Date.now()}`;
    discoveryRequest.requested_at = Date.now();

    return {
        type: 'service_discovery_request',
        data: discoveryRequest,
        routing_targets: ['service-registry'], // Route to service registry for processing
        response_format: 'service_discovery_response',
        metadata: {
            source_contract: 'service-discovery-to-central-hub',
            processing_time: Date.now(),
            correlation_id: context.correlationId || discoveryRequest.request_id,
            cache_duration: 30000 // 30 seconds cache for discovery results
        }
    };
}

const contractInfo = {
    name: 'service-discovery-to-central-hub',
    version: '1.0.0',
    description: 'Handles service discovery requests from all services to Central Hub',
    transport_method: 'http-rest',
    direction: 'inbound',
    pattern: 'many-to-one',
    endpoints: {
        primary: 'GET /discovery/services',
        specific: 'GET /discovery/services/{service_name}',
        filtered: 'POST /discovery/query'
    }
};

module.exports = {
    processServiceDiscovery,
    ServiceDiscoverySchema,
    contractInfo
};