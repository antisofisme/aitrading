# Service Skills Update - File Locations Reference

**Quick reference for all files involved in this update project**

---

## 📍 PLANNING DOCUMENTS (BACKEND)

Location: `/mnt/g/khoirul/aitrading/project3/backend/docs/`

| Document | Size | Purpose | Read Time |
|----------|------|---------|-----------|
| `SKILL_UPDATE_INDEX.md` | 8.9K | Navigation guide | 5 min |
| `SKILL_UPDATE_QUICK_REFERENCE.md` | 11K | Quick start guide | 5 min |
| `SKILL_UPDATE_EXECUTION_CHECKLIST.md` | 11K | Step-by-step checklist | 10 min |
| `SKILL_UPDATE_SUMMARY.md` | 8.4K | Executive summary | 10 min |
| `SKILL_UPDATE_STRATEGIC_PLAN.md` | 20K | Complete analysis | 30-60 min |

---

## 🎨 TEMPLATE FILES (ROOT)

Location: `/mnt/g/khoirul/aitrading/.claude/skills/`

| File | Lines | Purpose |
|------|-------|---------|
| `_SERVICE_SKILL_TEMPLATE.md` | 394 | Service skill template |
| `centralized_config_management.md` | 742 | Config system overview |
| `service_central_hub.md` | 702 | Complete example (UPDATED) |
| `service_polygon_historical_downloader.md` | 523 | Complete example (UPDATED) |

---

## 📂 PRODUCTION SKILLS (BACKEND)

Location: `/mnt/g/khoirul/aitrading/project3/backend/.claude/skills/`

### ✅ COMPLETE (2 services)

| Service | Lines | Status |
|---------|-------|--------|
| `service_central_hub.md` | 247 → 702 | ✅ Updated (copied from ROOT) |
| `service_polygon_historical_downloader.md` | 68 → 523 | ✅ Updated (copied from ROOT) |

### 🔄 PHASE 1: Data Pipeline (4 remaining)

| Service | Current Lines | Status | Priority |
|---------|---------------|--------|----------|
| `service_polygon_live_collector.md` | 61 | ⏳ Needs update | 🔴 CRITICAL |
| `service_dukascopy_historical_downloader.md` | 67 | ⏳ Needs update | 🔴 CRITICAL |
| `service_data_bridge.md` | 70 | ⏳ Needs update | 🔴 CRITICAL |
| `service_tick_aggregator.md` | 66 | ⏳ Needs update | 🔴 CRITICAL |

### 🔄 PHASE 2: ML Pipeline (4 services)

| Service | Current Lines | Status | Priority |
|---------|---------------|--------|----------|
| `service_feature_engineering.md` | 81 | ⏳ Needs update | 🟠 HIGH |
| `service_supervised_training.md` | 70 | ⏳ Needs update | 🟠 HIGH |
| `service_finrl_training.md` | 80 | ⏳ Needs update | 🟠 HIGH |
| `service_inference.md` | 79 | ⏳ Needs update | 🟠 HIGH |

### 🔄 PHASE 3: Trading Layer (3 services)

| Service | Current Lines | Status | Priority |
|---------|---------------|--------|----------|
| `service_risk_management.md` | 78 | ⏳ Needs update | 🟡 MEDIUM |
| `service_execution.md` | 78 | ⏳ Needs update | 🟡 MEDIUM |
| `service_mt5_connector.md` | 86 | ⏳ Needs update | 🟡 MEDIUM |

### 🔄 PHASE 4: Supporting Services (5 services)

| Service | Current Lines | Status | Priority |
|---------|---------------|--------|----------|
| `service_backtesting.md` | 83 | ⏳ Needs update | 🟢 LOW |
| `service_performance_monitoring.md` | 87 | ⏳ Needs update | 🟢 LOW |
| `service_notification_hub.md` | 102 | ⏳ Needs update | 🟢 LOW |
| `service_dashboard.md` | 87 | ⏳ Needs update | 🟢 LOW |
| `service_external_data_collector.md` | 77 | ⏳ Needs update | 🟢 LOW |

---

## 📊 STATISTICS

### Overall Progress
- **Total Services:** 18
- **Completed:** 2 (11%)
- **Remaining:** 16 (89%)

### Expected File Sizes (after update)
- **Before:** 60-100 lines (minimal)
- **After:** 300-600 lines (comprehensive with config section)

### Total Work
- **Services to update:** 16
- **Estimated time per service:** 40 minutes
- **Total estimated time:** ~10 hours
- **Timeline:** 2 weeks (with validation and documentation)

---

## 🎯 CONFIG PATTERNS BY SERVICE

### Data Ingestion Services (Phase 1)
**Services:** polygon-live-collector, dukascopy-historical-downloader, data-bridge

**Config Categories:**
- `operational`: batch_size, max_retries, retry_delay_seconds, buffer_size
- `features`: enable_validation, enable_duplicate_check
- `download`: start_date, end_date

### Data Processing Services (Phase 1)
**Services:** tick-aggregator

**Config Categories:**
- `operational`: aggregation_delay_seconds, max_batch_size, lookback_window_minutes
- `timeframes`: enabled (array)
- `features`: enable_tick_validation

### ML Services (Phase 2)
**Services:** feature-engineering, supervised-training, finrl-training, inference

**Config Categories:**
- `operational`: batch_size_samples, timeout_seconds
- `features`: enable_technical_indicators, enable_fibonacci_features, enable_external_data
- `thresholds`: null_max_percentage, feature_correlation_min

### Trading Services (Phase 3)
**Services:** risk-management, execution, mt5-connector

**Config Categories:**
- `operational`: max_concurrent_positions, position_check_interval_seconds
- `risk_limits`: max_position_size_pct, max_drawdown_pct, max_daily_loss_pct
- `features`: enable_trailing_stop, enable_partial_close

### Supporting Services (Phase 4)
**Services:** backtesting, performance-monitoring, notification-hub, dashboard, external-data-collector

**Config Categories:**
- `operational`: monitoring_interval_seconds, refresh_rate_seconds
- `thresholds`: alert_thresholds, performance_metrics
- `features`: enable_specific_features

---

## 🔍 QUICK FIND COMMANDS

### Check if service updated
```bash
grep -l "CENTRALIZED CONFIGURATION" /mnt/g/khoirul/aitrading/project3/backend/.claude/skills/service_*.md
```

### Count updated services
```bash
grep -l "CENTRALIZED CONFIGURATION" /mnt/g/khoirul/aitrading/project3/backend/.claude/skills/service_*.md | wc -l
```

### Check for hardcoded secrets
```bash
grep -i "password.*=\|api_key.*=" /mnt/g/khoirul/aitrading/project3/backend/.claude/skills/service_*.md
```

### Check line counts
```bash
wc -l /mnt/g/khoirul/aitrading/project3/backend/.claude/skills/service_*.md
```

### Find services without config section
```bash
for f in /mnt/g/khoirul/aitrading/project3/backend/.claude/skills/service_*.md; do
  if ! grep -q "CENTRALIZED CONFIGURATION" "$f"; then
    echo "Missing config: $(basename $f)"
  fi
done
```

---

## 📚 RELATED DOCUMENTATION

### Project Documentation
- `/mnt/g/khoirul/aitrading/CLAUDE.md` - Project instructions
- `/mnt/g/khoirul/aitrading/project3/backend/docs/` - Architecture docs

### Central Hub Documentation
- `docs/central-hub/README.md` - Complete guide
- `docs/central-hub/API_DOCUMENTATION.md` - API reference
- `docs/CONFIG_ARCHITECTURE.md` - Config system architecture

### Service Documentation
- `PLANNING_SKILL_GUIDE.md` - Service planning guide
- `SERVICE_ARCHITECTURE_AND_FLOW.md` - Architecture overview
- `SERVICE_FLOW_TREE_WITH_MESSAGING.md` - Flow diagrams

---

## ✅ VALIDATION CHECKLIST

### Per-Service Files Check
- [ ] File location: `/mnt/g/khoirul/aitrading/project3/backend/.claude/skills/service_{name}.md`
- [ ] File size: 300-600 lines
- [ ] Has "CENTRALIZED CONFIGURATION" section
- [ ] No hardcoded secrets
- [ ] Cross-references to central-hub
- [ ] Service-specific content preserved

### Batch Validation
- [ ] All 18 services in BACKEND location
- [ ] 2 services already updated (central-hub, polygon-historical)
- [ ] 16 services need update
- [ ] Template files available in ROOT
- [ ] Planning documents complete

---

## 🚀 NEXT STEPS

1. **Read planning documents** (start with QUICK_REFERENCE.md)
2. **Choose Phase 1 service** (data pipeline, critical priority)
3. **Follow 5-step process** (read, extract, create, merge, validate)
4. **Update service file** in BACKEND location
5. **Track progress** in execution checklist

---

**All files ready. All paths documented. Ready to execute!**
