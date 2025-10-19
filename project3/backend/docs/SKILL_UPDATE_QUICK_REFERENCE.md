# Service Skills Update - Quick Reference Guide

**For:** Developers executing the skill update plan
**Read Time:** 5 minutes
**Full Details:** See `SKILL_UPDATE_STRATEGIC_PLAN.md`

---

## ⚡ QUICK ANSWERS

### Q: Which directory should I use?
**A: BACKEND** (`/mnt/g/khoirul/aitrading/project3/backend/.claude/skills/`)

### Q: Do I replace or update files?
**A: UPDATE** (merge template + existing content)

### Q: What about ROOT directory?
**A: Keep it** (template library, don't modify)

### Q: How many services need updating?
**A: 16 services** (2 already done: central-hub, polygon-historical-downloader)

---

## 🎯 DECISION FLOWCHART

```
Start: Need to update service skill
    |
    ├─> Q: Is it central-hub or polygon-historical-downloader?
    |   └─> YES: Already complete ✅
    |   └─> NO: Continue ↓
    |
    ├─> Q: Which phase does this service belong to?
    |   ├─> Data Pipeline (Phase 1) → Priority: CRITICAL
    |   ├─> ML Pipeline (Phase 2) → Priority: HIGH
    |   ├─> Trading Layer (Phase 3) → Priority: MEDIUM
    |   └─> Supporting (Phase 4) → Priority: LOW
    |
    ├─> Follow 5-step process:
    |   1. Read template + current skill
    |   2. Extract service-specific content
    |   3. Create config section
    |   4. Merge content
    |   5. Validate
    |
    └─> Done: Move to next service
```

---

## 📋 5-STEP UPDATE PROCESS

### Step 1: READ (2 minutes)
```bash
# Read the template
Read /mnt/g/khoirul/aitrading/.claude/skills/_SERVICE_SKILL_TEMPLATE.md

# Read current service skill
Read /mnt/g/khoirul/aitrading/project3/backend/.claude/skills/service_{name}.md
```

**What to look for:**
- Template structure (what sections to add)
- Current skill content (what to preserve)

---

### Step 2: EXTRACT (5 minutes)
**From current skill, extract:**
- [ ] Purpose statement (1-2 sentences)
- [ ] Data flow diagram
- [ ] Messaging patterns (NATS subjects, Kafka topics)
- [ ] Dependencies (upstream/downstream services)
- [ ] Service-specific critical rules
- [ ] Existing validation checklist

**Note these down** - You'll merge them later

---

### Step 3: CREATE CONFIG SECTION (10 minutes)

**A. Identify Config Categories**

Ask yourself:
1. What operational settings change at runtime?
   → `operational` section
2. What features can be toggled on/off?
   → `features` section
3. What business logic has thresholds?
   → `business_logic` or `risk_limits` section

**B. Map to Config Hierarchy**

```
ENV VARS (Critical):
- Database credentials (CLICKHOUSE_PASSWORD)
- API keys (POLYGON_API_KEY)
- Infrastructure hosts (NATS_URL, KAFKA_BROKERS)

CENTRAL HUB (Operational):
- Batch sizes (batch_size: 100)
- Retry logic (max_retries: 3)
- Intervals (gap_check_interval_hours: 1)
- Feature toggles (enable_validation: true)
- Thresholds (max_drawdown_pct: 0.10)
```

**C. Write Config Examples**

Use service-type pattern from checklist:
- Data Ingestion → See "Data Ingestion Services" pattern
- ML Services → See "ML Services" pattern
- Trading Services → See "Trading Services" pattern

---

### Step 4: MERGE CONTENT (15 minutes)

**Template Structure (use this order):**

```markdown
# [Service Name] Service Skill

**Service Name:** [service-name]
**Type:** [Data Ingestion | Data Processing | ML | Trading | Infrastructure]
**Port:** [8001-8018]
**Purpose:** [One-line from Step 2]

---

## 📋 QUICK REFERENCE
[Use template boilerplate + customize]

## ⭐ CENTRALIZED CONFIGURATION (MANDATORY)
[Created in Step 3 - full config section from template]

## 🔧 CRITICAL RULES
[Merge: Template config rules + Existing service rules]

## 🏗️ ARCHITECTURE
[Keep existing data flow + dependencies]

## ✅ VALIDATION CHECKLIST
[Merge: Template config checks + Existing validations]

## 🚨 COMMON ISSUES
[Add config troubleshooting from template]

## 📖 SUMMARY
[Use template summary pattern]
```

**Key Points:**
- ✅ Preserve all service-specific content
- ✅ Add complete config section from template
- ✅ Merge critical rules (don't replace)
- ✅ Update validation checklist

---

### Step 5: VALIDATE (5 minutes)

**Checklist:**
- [ ] File has "⭐ CENTRALIZED CONFIGURATION" section
- [ ] Config hierarchy clear (ENV vars vs Central Hub)
- [ ] Safe defaults documented in `_get_safe_defaults()`
- [ ] No hardcoded secrets
  ```bash
  grep -i "password.*=\|api_key.*=" service_{name}.md
  # Should only show ENV var examples
  ```
- [ ] Cross-reference to `service_central_hub.md` added
- [ ] Service-specific content preserved
- [ ] File length: 300-600 lines

**If all ✅ → Save file → Move to next service**

---

## 🎨 CONFIG PATTERNS (COPY-PASTE READY)

### Data Ingestion Pattern
```json
{
  "operational": {
    "batch_size": 100,
    "max_retries": 3,
    "retry_delay_seconds": 10,
    "buffer_size": 1000
  },
  "features": {
    "enable_validation": true,
    "enable_duplicate_check": true
  },
  "download": {
    "start_date": "today-7days",
    "end_date": "today"
  }
}
```

### ML Services Pattern
```json
{
  "operational": {
    "batch_size_samples": 1000,
    "max_features": 110,
    "timeout_seconds": 300
  },
  "features": {
    "enable_technical_indicators": true,
    "enable_fibonacci_features": true,
    "enable_external_data": true
  },
  "thresholds": {
    "null_max_percentage": 0.05,
    "feature_correlation_min": 0.01
  }
}
```

### Trading Services Pattern
```json
{
  "operational": {
    "max_concurrent_positions": 5,
    "position_check_interval_seconds": 1
  },
  "risk_limits": {
    "max_position_size_pct": 0.02,
    "max_drawdown_pct": 0.10,
    "max_daily_loss_pct": 0.03
  },
  "features": {
    "enable_trailing_stop": true,
    "enable_partial_close": true
  }
}
```

---

## 🚨 COMMON MISTAKES

### ❌ MISTAKE 1: Replace Entire File
**Wrong:**
```bash
# Copy template and replace
cp _SERVICE_SKILL_TEMPLATE.md service_tick_aggregator.md
# Then fill in details
```

**Right:**
```bash
# Read both, extract from current, merge with template
# Preserve: data flow, dependencies, service-specific rules
```

---

### ❌ MISTAKE 2: Hardcode Secrets
**Wrong:**
```python
CLICKHOUSE_PASSWORD = "clickhouse_secure_2024"
POLYGON_API_KEY = "abc123xyz"
```

**Right:**
```python
CLICKHOUSE_PASSWORD = os.getenv('CLICKHOUSE_PASSWORD')
POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')
```

---

### ❌ MISTAKE 3: Skip Safe Defaults
**Wrong:**
```python
async def init_async(self):
    self._operational_config = await self.config_client.get_config()
    # ❌ What if Central Hub is down?
```

**Right:**
```python
async def init_async(self):
    try:
        self._operational_config = await self.config_client.get_config()
    except Exception as e:
        logger.warning(f"Central Hub unavailable: {e}")
        self._operational_config = self._get_safe_defaults()
```

---

### ❌ MISTAKE 4: Generic Config
**Wrong:**
```json
{
  "operational": {
    "batch_size": 100,
    "max_retries": 3
  }
}
```

**Right (service-specific):**
```json
{
  "operational": {
    "aggregation_delay_seconds": 5,
    "max_candles_per_batch": 1000,
    "lookback_window_minutes": 60
  },
  "timeframes": {
    "enabled": ["5m", "15m", "30m", "1h", "4h", "1d", "1w"]
  }
}
```

---

## 📊 PROGRESS TRACKER

### Overall
- **Total:** 18 services
- **Complete:** 2 (11%)
- **Remaining:** 16

### By Phase
| Phase | Services | Priority | Complete | Remaining |
|-------|----------|----------|----------|-----------|
| Phase 1 | 6 | 🔴 CRITICAL | 2 | 4 |
| Phase 2 | 4 | 🟠 HIGH | 0 | 4 |
| Phase 3 | 3 | 🟡 MEDIUM | 0 | 3 |
| Phase 4 | 5 | 🟢 LOW | 0 | 5 |

---

## 🎯 PRIORITIZATION GUIDE

### When to Update Which Service?

**1. Start with Phase 1 (Data Pipeline)**
- **Why:** Continuous operation, config changes most frequent
- **Services:** polygon-live-collector, dukascopy-historical, data-bridge, tick-aggregator

**2. Then Phase 2 (ML Pipeline)**
- **Why:** Feature toggles change often during development
- **Services:** feature-engineering, supervised-training, finrl-training, inference

**3. Then Phase 3 (Trading Layer)**
- **Why:** Critical when changes needed, but less frequent
- **Services:** risk-management, execution, mt5-connector

**4. Finally Phase 4 (Supporting)**
- **Why:** Mostly static configurations
- **Services:** backtesting, performance-monitoring, notification-hub, dashboard, external-data-collector

---

## ⏱️ TIME ESTIMATES

### Per Service
- **Read:** 2 minutes
- **Extract:** 5 minutes
- **Config Section:** 10 minutes
- **Merge:** 15 minutes
- **Validate:** 5 minutes
- **Total:** ~40 minutes per service

### Per Phase
- **Phase 1:** 4 services × 40min = 2.5 hours (+ 2 done = 6 total)
- **Phase 2:** 4 services × 40min = 2.5 hours
- **Phase 3:** 3 services × 40min = 2 hours
- **Phase 4:** 5 services × 40min = 3 hours
- **Grand Total:** ~10 hours

---

## ✅ DONE CRITERIA

### Service is Complete When:
- [ ] File saved to BACKEND location
- [ ] All 5 steps completed
- [ ] Validation checklist passes
- [ ] No hardcoded secrets
- [ ] Cross-references accurate

### Phase is Complete When:
- [ ] All phase services updated
- [ ] Batch validation passes
- [ ] Git commit created
- [ ] Progress tracker updated

### Project is Complete When:
- [ ] 18/18 services updated
- [ ] Final validation passes
- [ ] README.md updated
- [ ] CLAUDE.md validated

---

## 📚 DOCUMENT REFERENCES

### Quick Start
- **This Document** - Quick reference (you are here)
- **Execution Checklist** - `SKILL_UPDATE_EXECUTION_CHECKLIST.md` (phase-by-phase)

### Deep Dive
- **Strategic Plan** - `SKILL_UPDATE_STRATEGIC_PLAN.md` (complete analysis)
- **Summary** - `SKILL_UPDATE_SUMMARY.md` (executive overview)

### Templates
- **Service Template** - `/mnt/g/khoirul/aitrading/.claude/skills/_SERVICE_SKILL_TEMPLATE.md`
- **Config Guide** - `/mnt/g/khoirul/aitrading/.claude/skills/centralized_config_management.md`

---

## 🚀 START NOW

### Your First Service

**Choose one from Phase 1:**
1. `service_polygon_live_collector.md`
2. `service_dukascopy_historical_downloader.md`
3. `service_data_bridge.md`
4. `service_tick_aggregator.md`

**Follow the 5 steps above**
**Total time:** ~40 minutes
**Result:** One more service ✅

---

**Good luck! 🎯**
