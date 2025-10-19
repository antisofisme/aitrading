# AI Trading System - Service Skills

> **Purpose**: Per-service knowledge base untuk memastikan Claude konsisten saat bekerja pada setiap service.
> **Format**: Anthropic Skills-compatible markdown files
> **Coverage**: 18 services (Phase 1-4) + Universal debugging protocol
> **Usage**: Reference these skills when working on specific services

---

## 🧠 **Core Skills (Universal)**

| # | Skill | File | Status | Priority |
|---|-------|------|--------|----------|
| 0 | **Systematic Debugging** | [**systematic_debugging.md**](./systematic_debugging.md) | ✅ **MANDATORY** | **🚨 CRITICAL** |

**Usage:** Apply this skill for ALL bug fixes and complex feature development before writing any code.

---

## 📋 Skill Files Index

### **Phase 1: Data Foundation (Active)**

| # | Service | Skill File | Status |
|---|---------|------------|--------|
| 1 | polygon-live-collector | [service_polygon_live_collector.md](./service_polygon_live_collector.md) | ✅ Active |
| 2 | polygon-historical-downloader | [service_polygon_historical_downloader.md](./service_polygon_historical_downloader.md) | ✅ Active |
| 3 | dukascopy-historical-downloader | [service_dukascopy_historical_downloader.md](./service_dukascopy_historical_downloader.md) | ✅ Active |
| 4 | external-data-collector | [service_external_data_collector.md](./service_external_data_collector.md) | ✅ Active |
| 5 | **central-hub** | [**service_central_hub.md**](./service_central_hub.md) | ✅ **Active** (Core Infrastructure) |
| 6 | data-bridge | [service_data_bridge.md](./service_data_bridge.md) | ✅ Active |
| 7 | tick-aggregator | [service_tick_aggregator.md](./service_tick_aggregator.md) | ✅ Active |
| 8 | feature-engineering-service | [service_feature_engineering.md](./service_feature_engineering.md) | ✅ Active |

---

### **Phase 2: ML Training (To Implement)**

| # | Service | Skill File | Status |
|---|---------|------------|--------|
| 8 | supervised-training-service | [service_supervised_training.md](./service_supervised_training.md) | ⚠️ To Implement |
| 9 | finrl-training-service | [service_finrl_training.md](./service_finrl_training.md) | ⚠️ To Build |

---

### **Phase 3: Live Trading (To Implement)**

| # | Service | Skill File | Status |
|---|---------|------------|--------|
| 10 | inference-service | [service_inference.md](./service_inference.md) | ⚠️ To Implement |
| 11 | execution-service | [service_execution.md](./service_execution.md) | ⚠️ To Implement |
| 12 | risk-management | [service_risk_management.md](./service_risk_management.md) | ⚠️ To Implement |
| 13 | performance-monitoring | [service_performance_monitoring.md](./service_performance_monitoring.md) | ⚠️ To Build |

---

### **Phase 4: Supporting Services (To Implement)**

| # | Service | Skill File | Status |
|---|---------|------------|--------|
| 14 | mt5-connector | [service_mt5_connector.md](./service_mt5_connector.md) | ⚠️ To Implement |
| 15 | backtesting-engine | [service_backtesting.md](./service_backtesting.md) | ⚠️ To Implement |
| 16 | dashboard-service | [service_dashboard.md](./service_dashboard.md) | ⚠️ To Implement |
| 17 | notification-hub | [service_notification_hub.md](./service_notification_hub.md) | ⚠️ To Implement |

---

## 🎯 How to Use Skills

### **For Claude (AI Assistant)**

When user asks you to work on a specific service:

1. **Read the skill file first** (e.g., `service_tick_aggregator.md`)
2. **Understand the service purpose** and data flow
3. **Check critical rules** (what to NEVER do, what to ALWAYS do)
4. **Follow validation checklist** after making changes
5. **Reference the detailed docs** linked at bottom of skill file

### **For Developers**

When implementing or debugging a service:

1. Open the corresponding skill file
2. Review "Common Tasks" section for your specific task
3. Check "Critical Rules" to avoid common mistakes
4. Use "Validation" checklist to verify your changes
5. Consult "Reference Docs" for detailed technical specs

---

## 📚 Knowledge Base Structure

Each skill file contains:

```markdown
# Skill: {service-name} Service

## Purpose
Brief description of what this service does

## Key Facts
- Phase, Status, Priority
- Key metrics, constraints

## Data Flow
Visual diagram: Input → Process → Output

## Messaging
NATS/Kafka configuration (subscribe/publish)

## Dependencies
Upstream/downstream services

## Critical Rules
5 most important rules to follow (prevent mistakes)

## Common Tasks
3-4 real-world tasks with steps

## Validation
Checklist to verify changes work correctly

## Reference Docs
Links to detailed documentation (7 files)
```

---

## 🔗 Related Documentation

These skill files reference 7 core documentation files:

1. **PLANNING_SKILL_GUIDE.md** - Comprehensive planning templates per service
2. **SERVICE_ARCHITECTURE_AND_FLOW.md** - Complete service architecture reference
3. **SERVICE_FLOW_TREE_WITH_MESSAGING.md** - Data flow + messaging patterns
4. **table_database_input.md** - Data ingestion tables (Phase 1)
5. **table_database_process.md** - ML features tables (Phase 1)
6. **table_database_training.md** - Training tables (Phase 2, to be designed)
7. **table_database_trading.md** - Trading tables (Phase 3, to be designed)

**Location**: `/mnt/g/khoirul/aitrading/project3/backend/docs/`

---

## 🎯 Skill File Benefits

### **Consistency**
- Claude has same understanding every time
- No confusion about service boundaries
- Clear upstream/downstream dependencies

### **Safety**
- Critical rules prevent common mistakes
- Validation checklists catch errors early
- Messaging patterns prevent data loss

### **Speed**
- Quick reference for common tasks
- No need to read 2000+ line docs
- Direct links to detailed sections

### **Quality**
- Enforces best practices
- Validates changes before deployment
- Ensures completeness (no missing steps)

---

## ✅ Maintenance

When updating services:

1. **Update skill file** if service purpose/flow changes
2. **Update validation checklist** if new checks needed
3. **Add common tasks** as new patterns emerge
4. **Keep critical rules current** (add new gotchas)

**Version**: 1.0.0
**Last Updated**: 2025-10-18
**Maintainer**: Development Team
