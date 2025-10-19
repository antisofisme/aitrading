# Service Skills Update - Execution Checklist

**Strategic Plan:** `SKILL_UPDATE_STRATEGIC_PLAN.md`
**Date Started:** 2025-10-19
**Status:** Ready to Execute

---

## 🎯 QUICK DECISIONS

### Q1: Which directory is canonical?
**A: BACKEND** (`/mnt/g/khoirul/aitrading/project3/backend/.claude/skills/`)

### Q2: Update or replace?
**A: Template-based UPDATE** (preserve service-specific content, add config sections)

### Q3: Keep both ROOT and BACKEND?
**A: YES**
- ROOT = Template library + Reference
- BACKEND = Production skills for this project

---

## 📋 EXECUTION PHASES

### Phase 1: Data Pipeline (PRIORITY: CRITICAL)
**Services:** 6 services
**Estimated Time:** 3-4 hours

- [x] `service_central_hub.md` - COPY from ROOT (complete)
- [x] `service_polygon_historical_downloader.md` - COPY from ROOT (complete)
- [ ] `service_polygon_live_collector.md` - UPDATE (add config section)
- [ ] `service_dukascopy_historical_downloader.md` - UPDATE (add config section)
- [ ] `service_data_bridge.md` - UPDATE (add config section)
- [ ] `service_tick_aggregator.md` - UPDATE (add config section)

**Validation:**
- [ ] All 6 services have "CENTRALIZED CONFIGURATION" section
- [ ] Safe defaults documented
- [ ] Config examples use ENV vars for secrets
- [ ] Cross-references to central-hub added

---

### Phase 2: ML Pipeline (PRIORITY: HIGH)
**Services:** 4 services
**Estimated Time:** 2-3 hours

- [ ] `service_feature_engineering.md` - UPDATE
- [ ] `service_supervised_training.md` - UPDATE
- [ ] `service_finrl_training.md` - UPDATE
- [ ] `service_inference.md` - UPDATE

**Config Focus:**
- Feature toggles (enable/disable features)
- Batch processing parameters
- Timeout configurations
- Threshold settings

**Validation:**
- [ ] Feature flags documented
- [ ] Training parameter configs added
- [ ] Inference mode configs separated from training

---

### Phase 3: Trading Layer (PRIORITY: MEDIUM)
**Services:** 3 services
**Estimated Time:** 2 hours

- [ ] `service_risk_management.md` - UPDATE
- [ ] `service_execution.md` - UPDATE
- [ ] `service_mt5_connector.md` - UPDATE

**Config Focus:**
- Risk limits (position size, drawdown, daily loss)
- Execution parameters (slippage, timeout)
- MT5 connection settings

**Validation:**
- [ ] Risk limits configurable
- [ ] No trading secrets in examples
- [ ] Graceful degradation for trading critical

---

### Phase 4: Supporting Services (PRIORITY: LOW)
**Services:** 5 services
**Estimated Time:** 2 hours

- [ ] `service_backtesting.md` - UPDATE
- [ ] `service_performance_monitoring.md` - UPDATE
- [ ] `service_notification_hub.md` - UPDATE
- [ ] `service_dashboard.md` - UPDATE
- [ ] `service_external_data_collector.md` - UPDATE

**Config Focus:**
- Monitoring intervals
- Notification thresholds
- Dashboard refresh rates
- External API limits

**Validation:**
- [ ] All 18 services updated
- [ ] Cross-references complete
- [ ] README.md updated

---

## 🔧 UPDATE PROCESS (FOR EACH SERVICE)

### Step 1: Preparation
```bash
# Read template
Read /mnt/g/khoirul/aitrading/.claude/skills/_SERVICE_SKILL_TEMPLATE.md

# Read current service skill
Read /mnt/g/khoirul/aitrading/project3/backend/.claude/skills/service_{name}.md

# Backup (if needed)
cp service_{name}.md service_{name}.md.backup
```

### Step 2: Content Extraction
**Extract from current skill:**
- [ ] Purpose statement
- [ ] Data flow diagram
- [ ] Messaging patterns (NATS/Kafka)
- [ ] Dependencies (upstream/downstream)
- [ ] Critical rules (service-specific)
- [ ] Validation checklist

### Step 3: Config Section Creation
**Identify config categories:**
- [ ] Operational (batch_size, retries, intervals)
- [ ] Features (enable/disable toggles)
- [ ] Business Logic (thresholds, ranges)
- [ ] Service-specific parameters

**Create config.py example:**
```python
# Critical from ENV
self.clickhouse_host = os.getenv('CLICKHOUSE_HOST')
self.clickhouse_password = os.getenv('CLICKHOUSE_PASSWORD')

# Operational from Central Hub
@property
def batch_size(self) -> int:
    return self._operational_config.get('operational', {}).get('batch_size', 100)
```

### Step 4: Merge Content
**Template structure:**
1. ✅ Header (Service Name, Type, Port, Purpose)
2. ✅ Quick Reference
3. ✅ **CENTRALIZED CONFIGURATION** ← INSERT HERE
4. ✅ Critical Rules (merge existing + config rules)
5. ✅ Architecture (keep existing)
6. ✅ Validation Checklist (merge existing + config checks)
7. ✅ Common Issues (add config troubleshooting)
8. ✅ Summary

### Step 5: Quality Check
- [ ] Config hierarchy documented (ENV vs Hub)
- [ ] Safe defaults in `_get_safe_defaults()`
- [ ] No hardcoded secrets
- [ ] Cross-reference to central-hub skill
- [ ] File 300-600 lines
- [ ] Service-specific content preserved

### Step 6: Write Updated Skill
```bash
# Write to BACKEND location
Write /mnt/g/khoirul/aitrading/project3/backend/.claude/skills/service_{name}.md
```

---

## ✅ VALIDATION CHECKLIST

### Per-Service Validation

After updating each service:
- [ ] File follows template structure
- [ ] "CENTRALIZED CONFIGURATION" section present
- [ ] Config hierarchy clear (ENV vars vs Central Hub)
- [ ] Safe defaults documented
- [ ] Config properties realistic
- [ ] No secrets in examples (check with: `grep -i "password.*=" service_*.md`)
- [ ] Cross-references accurate
- [ ] Original service-specific content preserved

### Phase Validation

After completing each phase:
- [ ] All phase services updated
- [ ] Consistent format across phase services
- [ ] Config patterns appropriate for service type
- [ ] Cross-references working
- [ ] Git commit with phase summary

### Final Validation

After Phase 4 complete:
- [ ] 18/18 services have config section
- [ ] All skills 300-600 lines
- [ ] Zero hardcoded secrets (`grep -i "api_key.*=\|password.*=" service_*.md`)
- [ ] All reference central-hub (`grep -l "service_central_hub" service_*.md | wc -l` = 17)
- [ ] README.md updated
- [ ] CLAUDE.md references validated

---

## 🎨 CONFIG PATTERNS BY SERVICE TYPE

### Data Ingestion Services
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

### Data Processing Services
```json
{
  "operational": {
    "aggregation_delay_seconds": 5,
    "max_batch_size": 1000,
    "lookback_window_minutes": 60
  },
  "timeframes": {
    "enabled": ["5m", "15m", "30m", "1h", "4h", "1d", "1w"]
  },
  "features": {
    "enable_tick_validation": true
  }
}
```

### ML Services
```json
{
  "operational": {
    "batch_size_samples": 1000,
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

### Trading Services
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

## 🚨 COMMON PITFALLS TO AVOID

### ❌ DON'T:
1. **Replace entire file** - Loses service-specific content
2. **Hardcode secrets** - Check examples for `PASSWORD=`, `API_KEY=`
3. **Skip safe defaults** - Service must work if Hub down
4. **Copy-paste config** - Customize for each service
5. **Ignore validation** - Each service has unique validation needs
6. **Break cross-references** - Links must be accurate

### ✅ DO:
1. **Preserve existing content** - Merge, don't replace
2. **Use ENV vars for secrets** - `os.getenv('PASSWORD')`
3. **Document safe defaults** - `_get_safe_defaults()` method
4. **Customize config** - Service-specific parameters
5. **Validate thoroughly** - Use checklist above
6. **Test references** - Verify all links work

---

## 📊 PROGRESS TRACKING

### Overall Progress
- **Total Services:** 18
- **Completed:** 2 (central-hub, polygon-historical-downloader)
- **Remaining:** 16
- **Progress:** 11%

### Phase Breakdown
| Phase | Services | Status | Progress |
|-------|----------|--------|----------|
| Phase 1 | 6 | 🔄 In Progress | 2/6 (33%) |
| Phase 2 | 4 | ⏳ Pending | 0/4 (0%) |
| Phase 3 | 3 | ⏳ Pending | 0/3 (0%) |
| Phase 4 | 5 | ⏳ Pending | 0/5 (0%) |

---

## 🎯 SUCCESS CRITERIA

**Plan is successful when:**

✅ **Coverage (18/18):**
- All service skills have "CENTRALIZED CONFIGURATION" section
- All services document config hierarchy
- All services have safe defaults

✅ **Quality:**
- Zero hardcoded secrets
- Consistent structure (template-based)
- Service-specific content preserved
- Cross-references accurate

✅ **Operational:**
- Services handle Hub downtime gracefully
- Config changes deployable without code changes
- Hot-reload documented where applicable
- Troubleshooting guides effective

✅ **Documentation:**
- README.md updated
- CLAUDE.md references validated
- Migration guide created
- Template improvements documented

---

## 📝 NOTES & LEARNINGS

### Template Improvements Identified
- [ ] Service-type-specific variants
- [ ] Common issues database
- [ ] Config property generator patterns

### Service-Specific Insights
- [ ] Track unique config patterns
- [ ] Document edge cases
- [ ] Note complex validation requirements

### Process Improvements
- [ ] Batch similar services together
- [ ] Create reusable config snippets
- [ ] Automate validation checks

---

## 🔄 NEXT ACTIONS

### Immediate (Today):
1. [ ] Start Phase 1: `service_polygon_live_collector.md`
2. [ ] Update with config section
3. [ ] Validate against checklist
4. [ ] Continue with remaining Phase 1 services

### Short-term (This Week):
1. [ ] Complete Phase 1 (Data Pipeline)
2. [ ] Complete Phase 2 (ML Pipeline)
3. [ ] Refine template based on learnings

### Long-term (Next Week):
1. [ ] Complete Phase 3 (Trading Layer)
2. [ ] Complete Phase 4 (Supporting Services)
3. [ ] Final validation and documentation
4. [ ] Git commit with comprehensive summary

---

**Ready to execute Phase 1!**
