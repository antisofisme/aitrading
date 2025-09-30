/**
 * Central Hub Contract: Scaling Command (Outbound)
 * Pattern: one-to-many (central-hub → services)
 * Transport: NATS+Kafka
 *
 * Central Hub broadcasts scaling decisions ke services
 */

const Joi = require('joi');

/**
 * Output schema untuk scaling command
 */
const ScalingCommandSchema = Joi.object({
    // Command metadata
    command_id: Joi.string().required(),
    timestamp: Joi.number().required(),
    command_type: Joi.string().valid('scale_up', 'scale_down', 'scale_out', 'scale_in', 'emergency_scale').required(),

    // Target specification
    target_service: Joi.string().required(),
    target_instances: Joi.array().items(Joi.string()).optional(), // Specific instances or null for all

    // Scaling parameters
    scaling_action: Joi.object({
        // Vertical scaling (scale up/down)
        cpu_adjustment: Joi.object({
            current_limit: Joi.string().optional(), // e.g., "1000m"
            new_limit: Joi.string().optional(),
            percentage_change: Joi.number().optional()
        }).optional(),

        memory_adjustment: Joi.object({
            current_limit: Joi.string().optional(), // e.g., "512Mi"
            new_limit: Joi.string().optional(),
            percentage_change: Joi.number().optional()
        }).optional(),

        // Horizontal scaling (scale out/in)
        replica_adjustment: Joi.object({
            current_replicas: Joi.number().integer().min(0).optional(),
            target_replicas: Joi.number().integer().min(0).optional(),
            min_replicas: Joi.number().integer().min(1).default(1),
            max_replicas: Joi.number().integer().max(50).default(10)
        }).optional(),

        // Load balancing adjustments
        load_balancing: Joi.object({
            weight_adjustment: Joi.number().min(0).max(100).optional(),
            traffic_percentage: Joi.number().min(0).max(100).optional()
        }).optional()
    }).required(),

    // Execution parameters
    execution: Joi.object({
        priority: Joi.string().valid('low', 'normal', 'high', 'emergency').default('normal'),
        timeout_ms: Joi.number().min(1000).default(300000), // 5 minutes default
        rollback_on_failure: Joi.boolean().default(true),
        gradual_rollout: Joi.boolean().default(true),
        health_check_delay_ms: Joi.number().min(0).default(30000) // 30 seconds
    }).default({}),

    // Context and reasoning
    trigger: Joi.object({
        reason: Joi.string().valid(
            'cpu_pressure', 'memory_pressure', 'high_load', 'low_utilization',
            'response_time_degradation', 'error_rate_spike', 'manual_request',
            'scheduled_scaling', 'predictive_scaling'
        ).required(),
        metrics: Joi.object().optional(), // Triggering metrics
        confidence: Joi.number().min(0).max(1).default(0.8),
        source: Joi.string().required() // What triggered this decision
    }).required(),

    // Notification settings
    notifications: Joi.object({
        notify_on_start: Joi.boolean().default(true),
        notify_on_completion: Joi.boolean().default(true),
        notify_on_failure: Joi.boolean().default(true),
        notification_channels: Joi.array().items(Joi.string()).default(['monitoring'])
    }).default({})
});

/**
 * Format scaling command
 */
function formatScalingCommand(targetService, scalingAction, trigger, executionOptions = {}) {
    const command = {
        command_id: `scale-${targetService}-${Date.now()}`,
        timestamp: Date.now(),
        command_type: determineCommandType(scalingAction),
        target_service: targetService,
        target_instances: executionOptions.target_instances || null,
        scaling_action: scalingAction,
        execution: {
            priority: executionOptions.priority || 'normal',
            timeout_ms: executionOptions.timeout_ms || 300000,
            rollback_on_failure: executionOptions.rollback_on_failure !== false,
            gradual_rollout: executionOptions.gradual_rollout !== false,
            health_check_delay_ms: executionOptions.health_check_delay_ms || 30000
        },
        trigger: trigger,
        notifications: executionOptions.notifications || {
            notify_on_start: true,
            notify_on_completion: true,
            notify_on_failure: true,
            notification_channels: ['monitoring']
        }
    };

    // Validate command format
    const { error } = ScalingCommandSchema.validate(command);
    if (error) {
        throw new Error(`Scaling command validation failed: ${error.details[0].message}`);
    }

    return command;
}

/**
 * Determine command type based on scaling action
 */
function determineCommandType(scalingAction) {
    // Horizontal scaling
    if (scalingAction.replica_adjustment) {
        const current = scalingAction.replica_adjustment.current_replicas;
        const target = scalingAction.replica_adjustment.target_replicas;
        if (target > current) return 'scale_out';
        if (target < current) return 'scale_in';
    }

    // Vertical scaling
    if (scalingAction.cpu_adjustment || scalingAction.memory_adjustment) {
        const cpuIncrease = scalingAction.cpu_adjustment?.percentage_change > 0;
        const memoryIncrease = scalingAction.memory_adjustment?.percentage_change > 0;
        if (cpuIncrease || memoryIncrease) return 'scale_up';
        else return 'scale_down';
    }

    return 'scale_up'; // Default
}

/**
 * Create emergency scaling command
 */
function createEmergencyScalingCommand(targetService, emergencyMetrics) {
    const scalingAction = {
        replica_adjustment: {
            current_replicas: emergencyMetrics.current_replicas || 1,
            target_replicas: Math.min((emergencyMetrics.current_replicas || 1) * 2, 10),
            min_replicas: 1,
            max_replicas: 10
        }
    };

    const trigger = {
        reason: emergencyMetrics.cpu_usage > 95 ? 'cpu_pressure' :
               emergencyMetrics.memory_usage > 95 ? 'memory_pressure' :
               emergencyMetrics.error_rate > 50 ? 'error_rate_spike' : 'high_load',
        metrics: emergencyMetrics,
        confidence: 0.95,
        source: 'emergency-auto-scaling'
    };

    const executionOptions = {
        priority: 'emergency',
        timeout_ms: 60000, // 1 minute for emergency
        gradual_rollout: false, // Immediate for emergency
        health_check_delay_ms: 10000 // Faster health check
    };

    return formatScalingCommand(targetService, scalingAction, trigger, executionOptions);
}

/**
 * Create predictive scaling command
 */
function createPredictiveScalingCommand(targetService, prediction) {
    const scalingAction = {
        replica_adjustment: {
            current_replicas: prediction.current_replicas,
            target_replicas: prediction.predicted_optimal_replicas,
            min_replicas: 1,
            max_replicas: prediction.max_allowed_replicas || 10
        }
    };

    const trigger = {
        reason: 'predictive_scaling',
        metrics: prediction.forecasted_metrics,
        confidence: prediction.confidence,
        source: 'ml-predictive-scaler'
    };

    const executionOptions = {
        priority: 'normal',
        gradual_rollout: true,
        health_check_delay_ms: 60000 // Longer for predictive
    };

    return formatScalingCommand(targetService, scalingAction, trigger, executionOptions);
}

/**
 * Calculate rollback command
 */
function createRollbackCommand(originalCommand) {
    const rollbackAction = { ...originalCommand.scaling_action };

    // Reverse the scaling action
    if (rollbackAction.replica_adjustment) {
        const current = rollbackAction.replica_adjustment.target_replicas;
        const original = rollbackAction.replica_adjustment.current_replicas;
        rollbackAction.replica_adjustment.current_replicas = current;
        rollbackAction.replica_adjustment.target_replicas = original;
    }

    if (rollbackAction.cpu_adjustment) {
        rollbackAction.cpu_adjustment.percentage_change = -rollbackAction.cpu_adjustment.percentage_change;
    }

    if (rollbackAction.memory_adjustment) {
        rollbackAction.memory_adjustment.percentage_change = -rollbackAction.memory_adjustment.percentage_change;
    }

    const trigger = {
        reason: 'manual_request',
        source: 'rollback-automation',
        confidence: 1.0
    };

    return formatScalingCommand(originalCommand.target_service, rollbackAction, trigger, {
        priority: 'high',
        rollback_on_failure: false // Don't rollback a rollback
    });
}

const contractInfo = {
    name: 'scaling-command-from-central-hub',
    version: '1.0.0',
    description: 'Scaling commands broadcast from Central Hub to services via NATS+Kafka',
    transport_method: 'nats-kafka',
    direction: 'outbound',
    pattern: 'one-to-many',
    nats_subject: 'scaling.commands.{target_service}',
    kafka_topic: 'scaling-commands',
    delivery_guarantee: 'at-least-once',
    response_required: true
};

module.exports = {
    formatScalingCommand,
    createEmergencyScalingCommand,
    createPredictiveScalingCommand,
    createRollbackCommand,
    ScalingCommandSchema,
    contractInfo
};