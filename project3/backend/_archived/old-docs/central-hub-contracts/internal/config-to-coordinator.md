# Internal Contract: Configuration Manager to Coordination Router

## Overview
Internal coordination antara Configuration Manager dan Coordination Router untuk dynamic routing updates.

## Data Flow
```
Config Change → Config Manager → Coordination Router → Transport Method Updates
```

## Interface Specification

### Input: Configuration Change
```javascript
{
    config_change_type: "transport_routing" | "service_priorities" | "load_balancing" | "circuit_breaker",
    affected_services: string[],
    changes: {
        routing_rules: {
            service_patterns: string[],
            transport_preferences: {
                primary: "http" | "grpc" | "nats-kafka",
                fallback: "http" | "grpc" | "nats-kafka",
                conditions: object
            }
        },
        priority_adjustments: {
            service_name: string,
            old_priority: number,
            new_priority: number
        }[],
        load_balancing_changes: {
            service_name: string,
            weight_changes: object
        }[],
        circuit_breaker_config: {
            service_name: string,
            failure_threshold: number,
            timeout_ms: number,
            recovery_timeout_ms: number
        }[]
    },
    effective_immediately: boolean,
    rollback_config: object
}
```

### Output: Routing Update
```javascript
{
    routing_update_id: string,
    coordinator_actions: [
        {
            action_type: "update_transport_matrix" | "adjust_priorities" | "reconfigure_circuit_breaker",
            target_services: string[],
            new_configuration: object,
            validation_required: boolean
        }
    ],
    routing_table_changes: {
        added_routes: object[],
        modified_routes: object[],
        removed_routes: string[]
    },
    performance_impact: {
        estimated_latency_change_ms: number,
        affected_message_types: string[]
    }
}
```

## Processing Rules

### Transport Routing Changes
1. Validate new routing rules
2. Create transition plan
3. Update routing matrix gradually
4. Monitor performance impact

### Priority Adjustments
1. Recalculate service weights
2. Update load balancing algorithms
3. Redistribute traffic gradually

### Circuit Breaker Updates
1. Update failure thresholds
2. Adjust timeout configurations
3. Reset circuit breaker states if needed

## Coordination Requirements
- Zero-downtime configuration updates
- Gradual rollout of routing changes
- Automatic rollback on failure detection
- Performance monitoring during transitions

## Validation Rules
- Routing rules must have valid fallbacks
- Priority values must sum to reasonable totals
- Circuit breaker thresholds must be realistic
- No circular routing dependencies