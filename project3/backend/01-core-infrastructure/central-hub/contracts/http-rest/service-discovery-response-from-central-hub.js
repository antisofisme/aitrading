/**
 * Central Hub Contract: Service Discovery Response (Outbound)
 * Pattern: one-to-many (central-hub → services)
 * Transport: HTTP REST
 *
 * Central Hub responds dengan discovered services
 */

const Joi = require('joi');

/**
 * Output schema untuk service discovery response
 */
const ServiceDiscoveryResponseSchema = Joi.object({
    // Response metadata
    request_id: Joi.string().required(),
    success: Joi.boolean().required(),
    timestamp: Joi.number().required(),

    // Discovery results
    services: Joi.object().pattern(
        Joi.string(), // service_name
        Joi.object({
            name: Joi.string().required(),
            host: Joi.string().required(),
            port: Joi.number().required(),
            protocol: Joi.string().required(),
            url: Joi.string().required(),
            version: Joi.string().required(),
            status: Joi.string().valid('active', 'inactive', 'unhealthy').required(),
            health_endpoint: Joi.string().required(),
            metadata: Joi.object().required(),
            registered_at: Joi.number().required(),
            last_seen: Joi.number().required()
        })
    ).optional(),

    // Response statistics
    count: Joi.number().integer().min(0).required(),
    filters_applied: Joi.object().optional(),
    cache_info: Joi.object({
        cached: Joi.boolean().required(),
        cache_age_ms: Joi.number().optional(),
        expires_at: Joi.number().optional()
    }).optional()
});

/**
 * Format service discovery response
 */
function formatServiceDiscoveryResponse(discoveryResults, originalRequest, context = {}) {
    // Extract services from discovery results
    const services = discoveryResults.services || {};

    // Apply filters if specified in original request
    let filteredServices = services;
    if (originalRequest.filters) {
        filteredServices = applyFilters(services, originalRequest.filters);
    }

    const response = {
        request_id: originalRequest.request_id,
        success: true,
        timestamp: Date.now(),
        services: filteredServices,
        count: Object.keys(filteredServices).length,
        filters_applied: originalRequest.filters || {},
        cache_info: {
            cached: discoveryResults.from_cache || false,
            cache_age_ms: discoveryResults.cache_age_ms || 0,
            expires_at: Date.now() + (context.cache_duration || 30000)
        }
    };

    // Validate response format
    const { error } = ServiceDiscoveryResponseSchema.validate(response);
    if (error) {
        throw new Error(`Service discovery response validation failed: ${error.details[0].message}`);
    }

    return response;
}

/**
 * Apply filters to services list
 */
function applyFilters(services, filters) {
    let filtered = { ...services };

    // Filter by status
    if (filters.status) {
        filtered = Object.fromEntries(
            Object.entries(filtered).filter(([_, service]) => service.status === filters.status)
        );
    }

    // Filter by capabilities
    if (filters.capabilities && filters.capabilities.length > 0) {
        filtered = Object.fromEntries(
            Object.entries(filtered).filter(([_, service]) => {
                const serviceCapabilities = service.metadata.capabilities || [];
                return filters.capabilities.some(cap => serviceCapabilities.includes(cap));
            })
        );
    }

    // Filter by transport support
    if (filters.transport_support) {
        filtered = Object.fromEntries(
            Object.entries(filtered).filter(([_, service]) => {
                const transportConfig = service.transport_config || {};
                const supportedMethods = [
                    ...(transportConfig.preferred_inbound || []),
                    ...(transportConfig.preferred_outbound || [])
                ];
                return supportedMethods.includes(filters.transport_support);
            })
        );
    }

    return filtered;
}

/**
 * Format error response
 */
function formatErrorResponse(error, originalRequest) {
    return {
        request_id: originalRequest.request_id || `error-${Date.now()}`,
        success: false,
        timestamp: Date.now(),
        error: {
            message: error.message,
            code: error.code || 'DISCOVERY_ERROR',
            details: error.details || {}
        },
        services: {},
        count: 0
    };
}

const contractInfo = {
    name: 'service-discovery-response-from-central-hub',
    version: '1.0.0',
    description: 'Service discovery response sent from Central Hub to requesting services',
    transport_method: 'http-rest',
    direction: 'outbound',
    pattern: 'one-to-many',
    response_to: 'service-discovery-to-central-hub'
};

module.exports = {
    formatServiceDiscoveryResponse,
    formatErrorResponse,
    ServiceDiscoveryResponseSchema,
    contractInfo
};