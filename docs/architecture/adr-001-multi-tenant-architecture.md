# ADR-001: Multi-Tenant Architecture with PostgreSQL RLS

**Status**: Recommended
**Date**: 2025-09-20
**Deciders**: System Architecture Team

## Context

The AI trading platform requires a multi-tenant architecture to serve 1,000+ concurrent users while maintaining strict data isolation between different trading organizations and individual users.

## Decision

We will implement a **shared database, shared schema** multi-tenant architecture using PostgreSQL Row Level Security (RLS) for data isolation.

## Rationale

### Technical Factors
- **Performance**: RLS adds only 5-15% query overhead with proper indexing
- **Security**: Database-level enforcement provides strongest isolation guarantees
- **Scalability**: Single schema simplifies maintenance and scaling operations
- **Cost Efficiency**: Shared resources reduce infrastructure costs significantly

### Implementation Details

```sql
-- Tenant context setting
SET LOCAL app.current_tenant = 'tenant-uuid-here';

-- RLS Policy Example
CREATE POLICY tenant_isolation ON trading_positions
  FOR ALL TO authenticated_users
  USING (tenant_id = current_setting('app.current_tenant')::uuid);

-- Performance optimization
CREATE INDEX idx_positions_tenant_user
  ON trading_positions (tenant_id, user_id, created_at);
```

## Alternatives Considered

1. **Database per Tenant**: Rejected due to complexity at scale (1000+ databases)
2. **Schema per Tenant**: Rejected due to PostgreSQL connection limits
3. **Application-level Filtering**: Rejected due to security risks

## Consequences

### Positive
- ✅ Strong data isolation at database level
- ✅ Simplified operations and maintenance
- ✅ Cost-effective resource utilization
- ✅ Excellent performance with proper indexing

### Negative
- ⚠️ Requires careful RLS policy management
- ⚠️ Database schema changes affect all tenants
- ⚠️ Complex backup/restore procedures

### Neutral
- Connection pooling must be tenant-aware
- Monitoring requires tenant-specific metrics

## Implementation Plan

1. **Week 1**: RLS policy framework
2. **Week 2**: Tenant-aware connection handling
3. **Week 3**: Performance optimization and testing
4. **Week 4**: Security audit and validation