# Internal Contract: Service Registry to Discovery Coordination

## Overview
Internal coordination antara Service Registry dan Discovery modules dalam Central Hub.

## Data Flow
```
Service Registration → Service Registry → Discovery Coordinator → Service Discovery Response
```

## Interface Specification

### Input: Registry Update
```javascript
{
    event_type: "service_registered" | "service_updated" | "service_deregistered",
    service_data: {
        service_name: string,
        host: string,
        port: number,
        protocol: string,
        metadata: object,
        status: "active" | "inactive" | "unhealthy",
        registered_at: number,
        last_seen: number
    },
    change_details: {
        changed_fields: string[],
        old_values: object,
        new_values: object
    },
    correlation_id: string
}
```

### Output: Discovery Update
```javascript
{
    discovery_action: "add_service" | "update_service" | "remove_service",
    service_index_update: {
        service_name: string,
        searchable_fields: {
            type: string,
            capabilities: string[],
            environment: string,
            transport_methods: string[]
        },
        routing_info: {
            url: string,
            preferred_transport: string,
            load_balancing_weight: number
        }
    },
    cache_invalidation: {
        affected_queries: string[],
        cache_keys_to_clear: string[]
    }
}
```

## Processing Rules

### Service Registration
1. Add service to searchable index
2. Update routing tables
3. Invalidate relevant discovery caches
4. Trigger health monitoring setup

### Service Update
1. Compare changed fields
2. Update search index if metadata changed
3. Update routing info if connection details changed
4. Selective cache invalidation

### Service Deregistration
1. Remove from all indexes
2. Clean up routing tables
3. Stop health monitoring
4. Full cache invalidation for service

## Performance Requirements
- Processing latency: < 50ms
- Index update propagation: < 100ms
- Cache invalidation: < 200ms

## Error Handling
- Failed index updates: Retry with exponential backoff
- Partial updates: Rollback to consistent state
- Cache invalidation failures: Log and continue (non-critical)