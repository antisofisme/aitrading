/**
 * Central Hub Contract: Service Registration (Inbound)
 * Pattern: many-to-one (services → central-hub)
 * Transport: HTTP REST
 *
 * Services register themselves dengan Central Hub untuk service discovery
 */

const Joi = require('joi');

/**
 * Input validation schema untuk service registration
 */
const ServiceRegistrationSchema = Joi.object({
    // Service identification
    service_name: Joi.string().required().min(2).max(50),
    host: Joi.string().required(),
    port: Joi.number().integer().min(1).max(65535).required(),
    protocol: Joi.string().valid('http', 'https', 'grpc', 'tcp', 'udp').default('http'),

    // Service metadata
    version: Joi.string().default('1.0.0'),
    environment: Joi.string().valid('development', 'staging', 'production').default('development'),
    health_endpoint: Joi.string().default('/health'),

    // Service capabilities and configuration
    metadata: Joi.object({
        type: Joi.string().valid('api-gateway', 'trading-engine', 'data-bridge', 'analytics', 'ml-service', 'notification').required(),
        capabilities: Joi.array().items(Joi.string()).default([]),
        tenant_support: Joi.boolean().default(false),
        max_connections: Joi.number().integer().min(1).default(1000),
        load_balancing_weight: Joi.number().min(0).max(100).default(10)
    }).required(),

    // Transport preferences
    transport_config: Joi.object({
        preferred_inbound: Joi.array().items(Joi.string().valid('http', 'grpc', 'nats-kafka')).default(['http']),
        preferred_outbound: Joi.array().items(Joi.string().valid('http', 'grpc', 'nats-kafka')).default(['http']),
        supports_streaming: Joi.boolean().default(false),
        max_message_size: Joi.number().integer().min(1024).default(1024 * 1024) // 1MB default
    }).default({})
});

/**
 * Process service registration request
 */
function processServiceRegistration(inputData, context = {}) {
    // Validate input
    const { error, value } = ServiceRegistrationSchema.validate(inputData);
    if (error) {
        throw new Error(`Service registration validation failed: ${error.details[0].message}`);
    }

    const registrationData = value;

    // Add system metadata
    registrationData.registered_at = Date.now();
    registrationData.last_seen = Date.now();
    registrationData.status = 'active';
    registrationData.registration_id = `${registrationData.service_name}-${Date.now()}`;

    // Generate service URL
    const protocol = registrationData.protocol === 'grpc' ? 'grpc' :
                    registrationData.protocol === 'https' ? 'https' : 'http';
    registrationData.url = `${protocol}://${registrationData.host}:${registrationData.port}`;

    return {
        type: 'service_registration',
        data: registrationData,
        routing_targets: ['service-registry'],
        response_format: 'service_registration_response',
        metadata: {
            source_contract: 'service-registration-to-central-hub',
            processing_time: Date.now(),
            correlation_id: context.correlationId || `reg-${Date.now()}`
        }
    };
}

const contractInfo = {
    name: 'service-registration-to-central-hub',
    version: '1.0.0',
    description: 'Handles service registration requests from all services to Central Hub',
    transport_method: 'http-rest',
    direction: 'inbound',
    pattern: 'many-to-one',
    endpoints: { primary: 'POST /discovery/register' }
};

module.exports = {
    processServiceRegistration,
    ServiceRegistrationSchema,
    contractInfo
};