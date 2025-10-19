# Skills Comprehensive Review & Update Plan

**Date:** 2025-10-19
**Purpose:** Review all 18 service skills, add centralized config, ensure synergy and cross-references
**Status:** 🔄 In Progress

---

## 📊 CURRENT STATE ANALYSIS

### **Skill Locations**

We have TWO skill directories:

**1. Root Level** (`/mnt/g/khoirul/aitrading/.claude/skills/`):
- `_SERVICE_SKILL_TEMPLATE.md` - Template for all skills ✅
- `centralized_config_management.md` - Config guide ✅
- `service_central_hub.md` - Central Hub skill ✅ (Updated)
- `service_polygon_historical_downloader.md` - Polygon historical skill ✅ (Updated)

**2. Backend Level** (`/mnt/g/khoirul/aitrading/project3/backend/.claude/skills/`):
- `README.md` - Skills index
- `systematic_debugging.md` - Debugging protocol ✅
- **18 service skills** (service_*.md)
- 3 helper skills (central-hub-debugger, central-hub-fixer, central-hub-service-creator)

---

### **Service Skills Status** (18 Total)

| # | Service | Config Section | Size | Priority | Dependencies |
|---|---------|----------------|------|----------|--------------|
| 1 | ✅ central-hub | ✅ Updated | 7.2K | DONE | None (core infrastructure) |
| 2 | ✅ polygon-historical-downloader | ✅ Updated | 2.9K | DONE | Central Hub, ClickHouse, NATS, Kafka |
| 3 | ❌ polygon-live-collector | ❌ Missing | 2.5K | HIGH | Central Hub, ClickHouse, NATS, Kafka |
| 4 | ❌ dukascopy-historical-downloader | ❌ Missing | 2.8K | HIGH | Central Hub, ClickHouse, NATS, Kafka |
| 5 | ❌ external-data-collector | ❌ Missing | 3.0K | HIGH | Central Hub, PostgreSQL, NATS |
| 6 | ❌ tick-aggregator | ❌ Missing | 2.9K | HIGH | Central Hub, ClickHouse, NATS, Kafka |
| 7 | ❌ data-bridge | ❌ Missing | 3.0K | HIGH | Central Hub, ClickHouse, NATS, Kafka |
| 8 | ❌ feature-engineering | ❌ Missing | 3.7K | MEDIUM | Central Hub, ClickHouse, NATS |
| 9 | ❌ supervised-training | ❌ Missing | 2.9K | MEDIUM | Central Hub, PostgreSQL, ClickHouse |
| 10 | ❌ finrl-training | ❌ Missing | 3.0K | MEDIUM | Central Hub, PostgreSQL, ClickHouse |
| 11 | ❌ inference | ❌ Missing | 3.1K | MEDIUM | Central Hub, NATS, model storage |
| 12 | ❌ risk-management | ❌ Missing | 3.1K | MEDIUM | Central Hub, NATS, PostgreSQL |
| 13 | ❌ execution | ❌ Missing | 3.2K | MEDIUM | Central Hub, NATS, MT5 |
| 14 | ❌ performance-monitoring | ❌ Missing | 3.4K | MEDIUM | Central Hub, PostgreSQL, NATS |
| 15 | ❌ mt5-connector | ❌ Missing | 3.1K | MEDIUM | Central Hub, NATS |
| 16 | ❌ backtesting | ❌ Missing | 2.9K | LOW | Central Hub, ClickHouse |
| 17 | ❌ dashboard | ❌ Missing | 2.7K | LOW | Central Hub, all services |
| 18 | ❌ notification-hub | ❌ Missing | 3.2K | LOW | Central Hub, NATS |

**Summary:**
- ✅ **2 skills updated** (11%)
- ❌ **16 skills need update** (89%)

---

## 🗺️ SERVICE DEPENDENCY MAP

### **Data Flow Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                     CENTRAL HUB (Core)                          │
│  - Service discovery                                            │
│  - Configuration management (ConfigClient API)                  │
│  - Health monitoring                                            │
│  - NATS/Kafka coordination                                      │
└──────────────┬──────────────────────────────────────────────────┘
               │ Config + Discovery
        ┌──────┴──────┬──────┬──────┬──────┐
        ↓             ↓      ↓      ↓      ↓

┌─────────────────────────────────────────────────────────────────┐
│               DATA INGESTION LAYER (5 services)                 │
├─────────────────────────────────────────────────────────────────┤
│ 1. polygon-live-collector          → ClickHouse (live_ticks)   │
│ 2. polygon-historical-downloader   → ClickHouse (live_aggregates)│
│ 3. dukascopy-historical-downloader → ClickHouse (historical_*)  │
│ 4. external-data-collector         → PostgreSQL (economic data) │
│ 5. mt5-connector                   → NATS (MT5 data stream)     │
└──────────────┬──────────────────────────────────────────────────┘
               │ NATS: market.*, mt5.*
               │ Kafka: tick_archive, aggregate_archive
               ↓
┌─────────────────────────────────────────────────────────────────┐
│             DATA PROCESSING LAYER (3 services)                  │
├─────────────────────────────────────────────────────────────────┤
│ 6. tick-aggregator      → Aggregate ticks to OHLCV (7 timeframes)│
│ 7. data-bridge          → Route data between systems            │
│ 8. feature-engineering  → Calculate 72 ML features              │
└──────────────┬──────────────────────────────────────────────────┘
               │ NATS: bars.*, features.*
               │ Kafka: feature_archive
               ↓
┌─────────────────────────────────────────────────────────────────┐
│           MACHINE LEARNING LAYER (3 services)                   │
├─────────────────────────────────────────────────────────────────┤
│ 9. supervised-training  → Train supervised models (XGBoost, etc)│
│10. finrl-training       → Train RL agents (PPO, DQN, A2C)      │
│11. inference            → Real-time predictions                 │
└──────────────┬──────────────────────────────────────────────────┘
               │ NATS: predictions.*
               ↓
┌─────────────────────────────────────────────────────────────────┐
│            TRADING EXECUTION LAYER (3 services)                 │
├─────────────────────────────────────────────────────────────────┤
│12. risk-management      → Position sizing, stop-loss            │
│13. execution            → Order execution logic                 │
│14. mt5-connector        → MT5 trade execution                   │
└──────────────┬──────────────────────────────────────────────────┘
               │ NATS: trades.*, orders.*
               ↓
┌─────────────────────────────────────────────────────────────────┐
│           SUPPORTING SERVICES LAYER (4 services)                │
├─────────────────────────────────────────────────────────────────┤
│15. performance-monitoring → Track trading performance           │
│16. backtesting           → Historical strategy testing          │
│17. dashboard             → Web UI for monitoring                │
│18. notification-hub      → Alerts & notifications               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔗 CROSS-REFERENCE MATRIX

### **Which Skills Reference Which**

| Service | Depends On | Referenced By |
|---------|-----------|---------------|
| **central-hub** | None (core) | ALL 17 services |
| **polygon-historical** | central-hub, tick-aggregator | data-bridge, feature-engineering |
| **polygon-live** | central-hub, tick-aggregator | data-bridge, feature-engineering |
| **dukascopy-historical** | central-hub, tick-aggregator | data-bridge |
| **external-data-collector** | central-hub | feature-engineering |
| **mt5-connector** | central-hub | execution, data-bridge |
| **tick-aggregator** | central-hub, data-ingestion (all) | feature-engineering, data-bridge |
| **data-bridge** | central-hub, tick-aggregator | feature-engineering |
| **feature-engineering** | central-hub, data-bridge | supervised-training, finrl-training |
| **supervised-training** | central-hub, feature-engineering | inference |
| **finrl-training** | central-hub, feature-engineering | inference |
| **inference** | central-hub, ML-training (both) | risk-management, execution |
| **risk-management** | central-hub, inference | execution |
| **execution** | central-hub, risk-management | mt5-connector, performance-monitoring |
| **performance-monitoring** | central-hub, execution | dashboard |
| **backtesting** | central-hub, all data services | dashboard |
| **dashboard** | central-hub, ALL services | notification-hub |
| **notification-hub** | central-hub, performance-monitoring | Users |

---

## 🚨 ISSUES FOUND

### **1. Missing Centralized Config Sections** ⚠️ CRITICAL

**16 services** lack centralized configuration documentation:
- No ConfigClient usage examples
- No config hierarchy explanation
- No distinction between ENV vars vs Central Hub configs
- No safe defaults documentation

**Impact:**
- Developers won't know how to integrate with ConfigClient
- Risk of putting secrets in Central Hub
- Inconsistent config patterns across services

---

### **2. Missing Cross-References** ⚠️ MEDIUM

**Current state:**
- Skills exist in isolation
- No "See also" sections
- No data flow references
- No upstream/downstream service mentions

**Impact:**
- Developers don't understand service relationships
- Hard to trace data flows
- Missing context when debugging

---

### **3. Potential Duplications** ⚠️ LOW

**Areas to check:**
- NATS subject patterns (might be documented in multiple skills)
- ClickHouse schema descriptions
- Common operational patterns

**Status:** Need detailed review

---

### **4. Inconsistent Structure** ⚠️ LOW

**Some skills have:**
- Different section orders
- Different terminology
- Different levels of detail

**Impact:** Harder to navigate skills

---

## 📋 UPDATE PLAN

### **Phase 1: Priority Updates** (HIGH - Data Pipeline)

Update skills for core data flow services:

1. ✅ **central-hub** (DONE)
2. ✅ **polygon-historical-downloader** (DONE)
3. ❌ **polygon-live-collector**
4. ❌ **dukascopy-historical-downloader**
5. ❌ **tick-aggregator**
6. ❌ **data-bridge**
7. ❌ **external-data-collector**

**Estimated Time:** 3-4 hours (30min per skill)

---

### **Phase 2: ML Pipeline** (MEDIUM)

8. ❌ **feature-engineering**
9. ❌ **supervised-training**
10. ❌ **finrl-training**
11. ❌ **inference**

**Estimated Time:** 2 hours

---

### **Phase 3: Trading Execution** (MEDIUM)

12. ❌ **risk-management**
13. ❌ **execution**
14. ❌ **mt5-connector**

**Estimated Time:** 1.5 hours

---

### **Phase 4: Supporting Services** (LOW)

15. ❌ **performance-monitoring**
16. ❌ **backtesting**
17. ❌ **dashboard**
18. ❌ **notification-hub**

**Estimated Time:** 2 hours

---

## 📝 STANDARDIZED SKILL STRUCTURE

### **Required Sections (All Skills)**

```markdown
# {Service Name} Service Skill

**Service Name:** {service-name}
**Type:** {Data Ingestion|Data Processing|ML|Trading|Supporting}
**Port:** {port}
**Purpose:** {one-line description}

---

## 📋 QUICK REFERENCE

**When to use this skill:**
- {bullet points}

**Key Responsibilities:**
- {bullet points}

**Data Flow:**
```
{ASCII diagram}
```

---

## ⚠️ CENTRALIZED CONFIGURATION (MANDATORY)

### **Configuration Hierarchy**

```python
# ===== CRITICAL CONFIGS → Environment Variables (.env) =====
# NEVER put these in Central Hub!

{service-specific ENV vars}

# ===== OPERATIONAL CONFIGS → Central Hub =====
# Safe to change at runtime via ConfigClient

{
  "operational": {...},
  "features": {...},
  "business_logic": {...}
}
```

### **ConfigClient Integration**

```python
from shared.components.config import ConfigClient

# Initialize
config_client = ConfigClient(
    service_name="{service-name}",
    safe_defaults={...}
)
await config_client.init_async()

# Get config
config = await config_client.get_config()
batch_size = config['operational']['batch_size']
```

### **Safe Defaults (CRITICAL)**

```python
# Service MUST work with these defaults even if Central Hub is down!
safe_defaults = {
    "operational": {...},
    "features": {...}
}
```

**📖 See also:**
- `.claude/skills/service_central_hub.md` - Central Hub config API
- `docs/CONFIG_ARCHITECTURE.md` - Complete config guide

---

## 🏗️ ARCHITECTURE

{Service-specific architecture}

---

## 🔧 CRITICAL RULES

{Service-specific rules}

---

## 🔗 RELATED SERVICES

**Upstream (Data Sources):**
- 📥 `service_xxx` - {what data}

**Downstream (Data Consumers):**
- 📤 `service_yyy` - {what data}

**📖 See also:**
- `.claude/skills/service_xxx.md` - {description}

---

## 📊 DATA FLOW

{Detailed data flow}

---

## ✅ VALIDATION CHECKLIST

{Service-specific validations}

---

## 🚨 COMMON ISSUES

{Service-specific issues}

---

## 📖 REFERENCE

{Service-specific reference}
```

---

## 🎯 EXECUTION STRATEGY

### **Approach: Systematic Batch Updates**

**Option A: Sequential** (Safer, slower)
- Update 1 skill at a time
- Test cross-references
- Verify consistency
- ⏱️ Time: ~8-10 hours total

**Option B: Batched** (Faster, need validation)
- Update Phase 1 (7 skills) in parallel
- Review cross-references together
- Update Phase 2-4
- ⏱️ Time: ~4-5 hours total

**Recommendation:** **Option B with validation**

---

### **Step-by-Step Process**

**For Each Skill:**

1. **Read existing skill** (understand current state)
2. **Add centralized config section** (using template)
3. **Identify dependencies** (upstream/downstream)
4. **Add cross-references** (related skills)
5. **Check for duplications** (with other skills)
6. **Validate consistency** (terminology, structure)

**After All Updates:**

7. **Update CLAUDE.md** (add skill references)
8. **Update skills README.md** (index of all skills)
9. **Create skill cross-reference map** (visual diagram)
10. **Run validation agent** (check consistency)

---

## 📖 TEMPLATES TO USE

### **1. Centralized Config Section Template**

Located at: `.claude/skills/_SERVICE_SKILL_TEMPLATE.md`

**Key Components:**
- Configuration hierarchy (ENV vs Central Hub)
- ConfigClient integration code
- Safe defaults example
- Cross-reference to Central Hub skill

### **2. Cross-Reference Template**

```markdown
## 🔗 RELATED SERVICES

**Upstream (Data Sources):**
- 📥 `service_xxx` - Provides {what}
  → **See:** `.claude/skills/service_xxx.md`

**Downstream (Data Consumers):**
- 📤 `service_yyy` - Consumes {what}
  → **See:** `.claude/skills/service_yyy.md`

**Infrastructure:**
- 🏛️ `central-hub` - Configuration management
  → **See:** `.claude/skills/service_central_hub.md`

**📖 Configuration:**
- `docs/CONFIG_ARCHITECTURE.md` - Complete config guide
```

---

## ✅ VALIDATION CHECKLIST

**Before Starting:**
- [x] Current state analyzed
- [x] Service dependencies mapped
- [x] Update plan created
- [x] Templates prepared

**During Updates:**
- [ ] Each skill has centralized config section
- [ ] Each skill has cross-references
- [ ] Config hierarchy is consistent
- [ ] No secrets in example configs
- [ ] Safe defaults are comprehensive

**After Updates:**
- [ ] All 18 skills updated
- [ ] CLAUDE.md updated
- [ ] README.md updated
- [ ] No duplications found
- [ ] No contradictions found
- [ ] Validation agent review passed

---

## 🚀 NEXT ACTIONS

**Immediate (Ready to Start):**

1. **Start Phase 1** (HIGH priority skills)
   - polygon-live-collector
   - dukascopy-historical-downloader
   - tick-aggregator
   - data-bridge
   - external-data-collector

2. **Use template** from `_SERVICE_SKILL_TEMPLATE.md`

3. **Add cross-references** as we go

**After Each Phase:**
- Review for consistency
- Check cross-references
- Validate against template

---

## 📊 PROGRESS TRACKING

### **Phase 1: Data Pipeline** (0/5)
- [ ] polygon-live-collector
- [ ] dukascopy-historical-downloader
- [ ] tick-aggregator
- [ ] data-bridge
- [ ] external-data-collector

### **Phase 2: ML Pipeline** (0/4)
- [ ] feature-engineering
- [ ] supervised-training
- [ ] finrl-training
- [ ] inference

### **Phase 3: Trading Execution** (0/3)
- [ ] risk-management
- [ ] execution
- [ ] mt5-connector

### **Phase 4: Supporting** (0/4)
- [ ] performance-monitoring
- [ ] backtesting
- [ ] dashboard
- [ ] notification-hub

**Total Progress: 2/18 (11%)**

---

## 💡 KEY INSIGHTS

### **What Makes Skills Synergistic:**

1. **Clear Service Boundaries**
   - Each skill documents ONE service
   - No overlap in responsibilities
   - Clear upstream/downstream relationships

2. **Consistent Patterns**
   - Same config hierarchy across all services
   - Same cross-reference format
   - Same validation checklist structure

3. **Comprehensive Cross-References**
   - Links to upstream services (data sources)
   - Links to downstream services (data consumers)
   - Links to Central Hub (config provider)
   - Links to docs (CONFIG_ARCHITECTURE.md)

4. **No Duplications**
   - Common patterns documented once (in Central Hub skill)
   - Service-specific details in each skill
   - Templates for reusable components

---

## 📅 TIMELINE ESTIMATE

**Optimistic:** 4-5 hours (batched approach)
**Realistic:** 6-8 hours (with validation)
**Pessimistic:** 10-12 hours (if many issues found)

**Recommended Schedule:**
- **Session 1 (2 hours):** Phase 1 - Data pipeline (5 skills)
- **Session 2 (1.5 hours):** Phase 2 - ML pipeline (4 skills)
- **Session 3 (1.5 hours):** Phase 3 - Trading execution (3 skills)
- **Session 4 (1.5 hours):** Phase 4 - Supporting services (4 skills)
- **Session 5 (1 hour):** CLAUDE.md update + final validation

**Total: 7.5 hours across 5 sessions**

---

**Status:** ✅ Analysis Complete - Ready to Execute
**Next Step:** Start Phase 1 updates
**Date:** 2025-10-19
