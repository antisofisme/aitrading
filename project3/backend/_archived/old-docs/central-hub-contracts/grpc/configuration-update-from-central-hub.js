/**
 * Central Hub Contract: Configuration Update (Outbound)
 * Pattern: one-to-many (central-hub → services)
 * Transport: gRPC Streaming
 *
 * Central Hub broadcasts configuration updates ke services
 */

const Joi = require('joi');

/**
 * Output schema untuk configuration update
 */
const ConfigurationUpdateSchema = Joi.object({
    // Update metadata
    update_id: Joi.string().required(),
    timestamp: Joi.number().required(),
    update_type: Joi.string().valid('service-specific', 'environment', 'shared', 'emergency').required(),

    // Target specification
    target_services: Joi.array().items(Joi.string()).optional(), // null = broadcast to all
    environment: Joi.string().valid('development', 'staging', 'production').required(),

    // Configuration changes
    changes: Joi.array().items(
        Joi.object({
            key: Joi.string().required(),
            old_value: Joi.any().optional(),
            new_value: Joi.any().required(),
            action: Joi.string().valid('add', 'update', 'delete').required(),
            requires_restart: Joi.boolean().default(false)
        })
    ).required(),

    // Update context
    source: Joi.string().required(), // Who triggered the update
    reason: Joi.string().optional(),
    priority: Joi.string().valid('low', 'normal', 'high', 'critical').default('normal'),

    // Rollback information
    rollback_config: Joi.object().optional(),
    rollback_timeout_ms: Joi.number().default(300000) // 5 minutes default
});

/**
 * Format configuration update broadcast
 */
function formatConfigurationUpdate(configChanges, targetServices, updateContext = {}) {
    const update = {
        update_id: `config-update-${Date.now()}`,
        timestamp: Date.now(),
        update_type: updateContext.type || 'shared',
        target_services: targetServices,
        environment: updateContext.environment || 'production',
        changes: configChanges,
        source: updateContext.source || 'central-hub',
        reason: updateContext.reason,
        priority: updateContext.priority || 'normal',
        rollback_config: updateContext.rollback_config,
        rollback_timeout_ms: updateContext.rollback_timeout_ms || 300000
    };

    // Validate update format
    const { error } = ConfigurationUpdateSchema.validate(update);
    if (error) {
        throw new Error(`Configuration update validation failed: ${error.details[0].message}`);
    }

    return update;
}

/**
 * Determine which services need specific config changes
 */
function determineTargetServices(changes, allServices) {
    const targets = new Set();

    changes.forEach(change => {
        // Service-specific configurations
        if (change.key.startsWith('services.')) {
            const serviceName = change.key.split('.')[1];
            if (allServices.includes(serviceName)) {
                targets.add(serviceName);
            }
        }
        // Shared configurations - broadcast to all
        else if (change.key.startsWith('shared.') || change.key.startsWith('database.')) {
            allServices.forEach(service => targets.add(service));
        }
        // Environment configurations
        else if (change.key.startsWith('env.')) {
            // Send to all services in the environment
            allServices.forEach(service => targets.add(service));
        }
    });

    return Array.from(targets);
}

/**
 * Create rollback configuration
 */
function createRollbackConfig(changes) {
    return {
        rollback_id: `rollback-${Date.now()}`,
        original_changes: changes.map(change => ({
            key: change.key,
            value: change.old_value,
            action: change.action === 'add' ? 'delete' :
                   change.action === 'delete' ? 'add' : 'update'
        }))
    };
}

/**
 * Priority-based delivery configuration
 */
function getDeliveryConfig(priority) {
    const configs = {
        low: { timeout_ms: 30000, retry_count: 1 },
        normal: { timeout_ms: 15000, retry_count: 2 },
        high: { timeout_ms: 10000, retry_count: 3 },
        critical: { timeout_ms: 5000, retry_count: 5 }
    };

    return configs[priority] || configs.normal;
}

const contractInfo = {
    name: 'configuration-update-from-central-hub',
    version: '1.0.0',
    description: 'Configuration updates broadcast from Central Hub to services via gRPC streaming',
    transport_method: 'grpc',
    direction: 'outbound',
    pattern: 'one-to-many',
    grpc_service: 'ConfigurationManagement',
    grpc_method: 'StreamConfigUpdates',
    streaming: true,
    delivery_guarantee: 'at-least-once'
};

module.exports = {
    formatConfigurationUpdate,
    determineTargetServices,
    createRollbackConfig,
    getDeliveryConfig,
    ConfigurationUpdateSchema,
    contractInfo
};