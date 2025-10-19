# Strategic Plan: Service Skills Centralized Configuration Update

**Date:** 2025-10-19
**Author:** Strategic Analysis
**Status:** Ready for Execution
**Scope:** Update 16+ service skills with centralized configuration patterns

---

## 📊 SITUATION ANALYSIS

### Current State

**Two Skill Locations:**

1. **ROOT** (`/mnt/g/khoirul/aitrading/.claude/skills/`)
   - **Files:** 4 files
   - **Status:** Newer, updated with centralized config
   - **Template:** `_SERVICE_SKILL_TEMPLATE.md` (394 lines)
   - **Core docs:**
     - `centralized_config_management.md` (742 lines)
     - `service_central_hub.md` (702 lines) - FULLY UPDATED
     - `service_polygon_historical_downloader.md` (523 lines) - UPDATED

2. **BACKEND** (`/mnt/g/khoirul/aitrading/project3/backend/.claude/skills/`)
   - **Files:** 20 files (18 services + README + systematic_debugging)
   - **Status:** Older, minimal format (60-100 lines each)
   - **Format:** Brief purpose, data flow, critical rules only
   - **Missing:** Centralized configuration section (MANDATORY)

### File Comparison Analysis

| File | ROOT (lines) | BACKEND (lines) | Status | Action Required |
|------|--------------|-----------------|--------|-----------------|
| `service_central_hub.md` | 702 | 247 | ROOT newer | ✅ Copy ROOT → BACKEND |
| `service_polygon_historical_downloader.md` | 523 | 68 | ROOT updated | ✅ Copy ROOT → BACKEND |
| `service_tick_aggregator.md` | - | 66 | BACKEND only | 🔧 Add config section |
| `service_feature_engineering.md` | - | 81 | BACKEND only | 🔧 Add config section |
| Other 14 services | - | 60-100 | BACKEND only | 🔧 Add config section |

---

## 🎯 STRATEGIC DECISIONS

### Decision 1: Canonical Location

**ANSWER: BACKEND is canonical location**

**Rationale:**
1. **Context Awareness:** CLAUDE.md points to BACKEND location: `.claude/skills/service_{name}.md`
2. **Complete Coverage:** BACKEND has all 18 services, ROOT only has 2
3. **Developer Workflow:** Backend developers work in `project3/backend/`
4. **Git Structure:** BACKEND is part of project structure, ROOT is global

**Action:**
- Use BACKEND as primary location
- ROOT serves as reference/template library
- Update BACKEND skills to match ROOT quality

---

### Decision 2: Update Strategy

**ANSWER: Template-based systematic update**

**Pattern:**
```
For each service:
1. Read current BACKEND skill
2. Extract service-specific content (Purpose, Data Flow, Dependencies)
3. Merge with template sections (Centralized Config, Critical Rules)
4. Validate completeness
5. Write updated skill to BACKEND
```

**NOT: Wholesale replacement** (would lose service-specific content)

---

### Decision 3: Consolidation Strategy

**ANSWER: Keep both, different purposes**

**ROOT Purpose:**
- Template library
- Reference documentation
- Latest patterns and best practices
- Shared across multiple projects

**BACKEND Purpose:**
- Production skills for this project
- Service-specific implementations
- Used by Claude during development
- Version-controlled with project

**Sync Pattern:**
- ROOT = Template source → BACKEND = Implementation
- When updating pattern: Update ROOT template → Propagate to BACKEND skills
- When fixing service-specific: Update BACKEND only

---

## 📋 EXECUTION PLAN

### Phase 1: Foundation (PRIORITY: CRITICAL)

**Goal:** Establish baseline with core data pipeline services

**Services (5 services):**
1. ✅ `service_central_hub.md` - Copy from ROOT (already complete)
2. ✅ `service_polygon_historical_downloader.md` - Copy from ROOT (already complete)
3. 🔧 `service_polygon_live_collector.md` - Add config section
4. 🔧 `service_dukascopy_historical_downloader.md` - Add config section
5. 🔧 `service_data_bridge.md` - Add config section
6. 🔧 `service_tick_aggregator.md` - Add config section

**Impact:** High - These services run continuously, config changes frequent

**Estimated Time:** 3-4 hours

---

### Phase 2: ML Pipeline (PRIORITY: HIGH)

**Goal:** Enable ML services to use centralized config for feature toggles

**Services (4 services):**
7. 🔧 `service_feature_engineering.md`
8. 🔧 `service_supervised_training.md`
9. 🔧 `service_finrl_training.md`
10. 🔧 `service_inference.md`

**Impact:** High - Feature flags, training parameters change often

**Estimated Time:** 2-3 hours

---

### Phase 3: Trading Layer (PRIORITY: MEDIUM)

**Goal:** Support runtime trading parameter adjustments

**Services (3 services):**
11. 🔧 `service_risk_management.md`
12. 🔧 `service_execution.md`
13. 🔧 `service_mt5_connector.md`

**Impact:** Medium - Less frequent config changes, but critical when needed

**Estimated Time:** 2 hours

---

### Phase 4: Supporting Services (PRIORITY: LOW)

**Goal:** Complete coverage, enable operational flexibility

**Services (4 services):**
14. 🔧 `service_backtesting.md`
15. 🔧 `service_performance_monitoring.md`
16. 🔧 `service_notification_hub.md`
17. 🔧 `service_dashboard.md`
18. 🔧 `service_external_data_collector.md`

**Impact:** Low - Mostly static configurations

**Estimated Time:** 2 hours

---

## 🔧 IMPLEMENTATION PROCESS

### Step-by-Step Update Process

**For each service:**

#### Step 1: Read Current Content
```bash
Read service skill from BACKEND
Extract:
- Purpose
- Data Flow
- Messaging patterns
- Dependencies
- Critical Rules (service-specific)
- Validation checklist
```

#### Step 2: Apply Template Structure
```markdown
Use _SERVICE_SKILL_TEMPLATE.md sections:
1. Header (Service Name, Type, Port, Purpose)
2. Quick Reference
3. ⭐ CENTRALIZED CONFIGURATION (NEW)
   - Configuration Hierarchy
   - Implementation Pattern
   - Service Main - Async Init
4. Critical Rules (merge existing + template)
5. Architecture (existing content)
6. Validation Checklist (merge existing + config checks)
7. Common Issues (add config-related issues)
8. Summary
```

#### Step 3: Service-Specific Config Mapping

**Identify config categories for each service:**

```python
# Data Ingestion Services
polygon_live_collector:
  operational:
    - websocket_reconnect_delay_seconds
    - max_reconnection_attempts
    - buffer_size_ticks
  features:
    - enable_tick_validation
    - enable_duplicate_detection

tick_aggregator:
  operational:
    - aggregation_delay_seconds
    - max_candles_per_batch
    - lookback_window_minutes
  timeframes:
    - enabled_timeframes: ["5m", "15m", "30m", "1h", "4h", "1d", "1w"]

# ML Services
feature_engineering:
  operational:
    - batch_size_candles
    - feature_calculation_timeout_seconds
  features:
    - enable_fibonacci_features
    - enable_technical_indicators
    - enable_external_data_join
  thresholds:
    - null_feature_max_percentage: 0.05

# Trading Services
risk_management:
  operational:
    - position_size_calculation_method
    - max_concurrent_positions
  risk_limits:
    - max_position_size_pct: 0.02
    - max_drawdown_pct: 0.10
    - max_daily_loss_pct: 0.03
```

#### Step 4: Config Code Examples

**Generate service-specific config.py:**

```python
# For each service, create realistic config properties
# Based on service's actual operational parameters
# Example: feature_engineering/config.py

@property
def batch_size_candles(self) -> int:
    """Get batch size for candle processing"""
    return self._operational_config.get('operational', {}).get('batch_size_candles', 1000)

@property
def enable_fibonacci_features(self) -> bool:
    """Check if Fibonacci features enabled"""
    return self._operational_config.get('features', {}).get('enable_fibonacci_features', True)
```

#### Step 5: Validation

**Quality checks:**
- [ ] Config hierarchy documented (ENV vars vs Central Hub)
- [ ] Safe defaults provided in `_get_safe_defaults()`
- [ ] Service-specific config properties defined
- [ ] Critical rules updated (original + config rules)
- [ ] Validation checklist includes config checks
- [ ] Common issues section has config troubleshooting
- [ ] Cross-references to Central Hub skill
- [ ] No hardcoded secrets in examples

---

## ✅ VALIDATION FRAMEWORK

### Pre-Update Checklist

For each service before updating:
- [ ] Current skill file backed up
- [ ] Service-specific content extracted
- [ ] Config categories identified (operational/features/business_logic)
- [ ] Template sections prepared

### Post-Update Checklist

For each service after updating:
- [ ] File follows template structure
- [ ] Centralized Config section complete
- [ ] Service-specific content preserved
- [ ] Config examples realistic
- [ ] Safe defaults comprehensive
- [ ] Cross-references accurate
- [ ] No secrets in examples
- [ ] Line count: 300-600 lines (detailed, not excessive)

### Batch Validation

After each phase:
- [ ] All phase services updated
- [ ] README.md updated with new structure
- [ ] CLAUDE.md references still accurate
- [ ] Template improvements documented
- [ ] Git commit with clear message

---

## 🎨 TEMPLATE IMPROVEMENTS

### Current Template Strengths

1. ✅ Comprehensive centralized config section (150+ lines)
2. ✅ Clear hierarchy documentation (ENV vs Hub)
3. ✅ Complete code examples (config.py + main.py)
4. ✅ Graceful degradation pattern
5. ✅ Hot-reload support documented

### Proposed Template Enhancements

**Enhancement 1: Service-Type-Specific Templates**

```
Create variants for different service types:
- Data Ingestion (tick collectors, downloaders)
- Data Processing (aggregators, bridges)
- ML (feature engineering, training, inference)
- Trading (risk, execution, connectors)
- Infrastructure (central-hub, monitoring)
```

**Enhancement 2: Config Property Generator**

```python
# Add to template:
# TEMPLATE_CONFIG_PROPERTIES - Common patterns

# For batch processing services:
@property
def batch_size(self) -> int:
    return self._operational_config.get('operational', {}).get('batch_size', 100)

# For feature toggle services:
@property
def enable_{feature_name}(self) -> bool:
    return self._operational_config.get('features', {}).get('enable_{feature_name}', True)

# For threshold services:
@property
def {threshold_name}_threshold(self) -> float:
    return self._operational_config.get('thresholds', {}).get('{threshold_name}', 0.95)
```

**Enhancement 3: Common Issues Database**

```markdown
Create shared issues section:
- Config not loading from Central Hub
- Service crashes on missing ENV var
- Config changes not applied
- Hot-reload not working
- Fallback to defaults when Hub available

Include in template, customize per service
```

---

## 📚 CROSS-REFERENCE STRATEGY

### Skill-to-Skill References

**Pattern:**
Each skill references related skills

**Example:**
```markdown
## Related Skills

**Dependencies:**
- `service_central_hub.md` - Config provider (read this first!)
- `service_tick_aggregator.md` - Upstream data source
- `service_data_bridge.md` - Downstream consumer

**Config Management:**
- `centralized_config_management.md` - System overview
- `_SERVICE_SKILL_TEMPLATE.md` - Template reference
```

### Skill-to-Docs References

**Pattern:**
Link to detailed docs for deep-dives

**Example:**
```markdown
## Documentation

**Service Specific:**
- Implementation: `02-data-processing/tick-aggregator/README.md`
- Config examples: `02-data-processing/tick-aggregator/config/`

**Architecture:**
- Planning: `docs/PLANNING_SKILL_GUIDE.md` (Service 6)
- Flow: `docs/SERVICE_FLOW_TREE_WITH_MESSAGING.md`
- Schema: `docs/table_database_input.md`

**Central Hub:**
- Config API: `docs/central-hub/API_DOCUMENTATION.md`
- Config patterns: `docs/CONFIG_ARCHITECTURE.md`
```

---

## 🔄 MAINTENANCE STRATEGY

### When to Update Skills

**Trigger Events:**

1. **Service Implementation Changes**
   - New config parameters added
   - Dependencies changed
   - Data flow modified
   → Update service-specific skill only

2. **Pattern Changes**
   - New config hierarchy rule
   - Updated ConfigClient interface
   - New validation pattern
   → Update template → Propagate to all skills

3. **Infrastructure Changes**
   - Central Hub API changes
   - Database schema updates
   - Messaging patterns changed
   → Update central-hub skill → Update affected service skills

### Sync Process

**ROOT → BACKEND:**
```bash
# When template updated in ROOT
1. Update _SERVICE_SKILL_TEMPLATE.md in ROOT
2. Document changes in CHANGELOG
3. Review all BACKEND skills
4. Apply template changes where applicable
5. Test with 2-3 sample services
6. Batch update remaining services
```

**BACKEND → ROOT:**
```bash
# When service-specific improvement discovered
1. Implement in BACKEND skill
2. Evaluate if pattern is reusable
3. If yes: Abstract to template in ROOT
4. Apply to other similar services in BACKEND
```

---

## 📊 SUCCESS METRICS

### Quantitative Metrics

**Coverage:**
- [ ] 18/18 services have centralized config section
- [ ] 100% skills follow template structure
- [ ] All skills 300-600 lines (comprehensive)

**Quality:**
- [ ] Zero hardcoded secrets in examples
- [ ] All services have safe defaults
- [ ] All config hierarchies documented
- [ ] Cross-references complete (100%)

**Operational:**
- [ ] Config changes deployable without code changes
- [ ] All services handle Hub downtime gracefully
- [ ] Hot-reload working where applicable
- [ ] Config audit trail functional

### Qualitative Metrics

**Developer Experience:**
- ✅ Developers find config patterns immediately
- ✅ Consistent config approach across all services
- ✅ Clear separation: ENV vars vs Central Hub
- ✅ Troubleshooting guides effective

**System Reliability:**
- ✅ Services survive Central Hub downtime
- ✅ Config changes applied without restart
- ✅ Rollback process documented and tested
- ✅ Audit trail supports debugging

---

## 🚀 EXECUTION TIMELINE

### Week 1: Foundation + ML Pipeline

**Day 1-2: Phase 1 (Data Pipeline)**
- Update 6 data ingestion/processing services
- Test config integration
- Validate safe defaults

**Day 3-4: Phase 2 (ML Pipeline)**
- Update 4 ML services
- Test feature toggles
- Validate training parameter changes

**Day 5: Review + Adjust**
- Review first 10 services
- Refine template based on learnings
- Update documentation

### Week 2: Trading + Supporting Services

**Day 6-7: Phase 3 (Trading Layer)**
- Update 3 trading services
- Test risk parameter changes
- Validate execution configs

**Day 8-9: Phase 4 (Supporting Services)**
- Update 5 supporting services
- Complete coverage

**Day 10: Final Validation**
- Complete cross-reference audit
- Update README.md
- Create migration guide
- Git commit with comprehensive message

---

## 🎯 DELIVERABLES

### Primary Deliverables

1. **Updated Skills (18 files)**
   - All services with centralized config section
   - Consistent structure and format
   - Service-specific content preserved

2. **Enhanced Template**
   - Service-type-specific variants
   - Common issues database
   - Config property patterns

3. **Documentation**
   - This strategic plan
   - Migration guide for future services
   - README.md updated
   - CLAUDE.md cross-references validated

### Supporting Deliverables

4. **Quality Assurance**
   - Validation checklist results
   - Coverage report (18/18 complete)
   - Cross-reference matrix

5. **Operational Guides**
   - How to add new service skill
   - How to update existing skill
   - How to sync ROOT ↔ BACKEND

---

## 🛡️ RISK MITIGATION

### Risk 1: Breaking Existing Skills

**Mitigation:**
- Backup all files before updating
- Preserve service-specific content
- Test with Claude before committing
- Git version control (easy rollback)

### Risk 2: Inconsistent Updates

**Mitigation:**
- Use template strictly
- Batch update similar services together
- Cross-validate after each phase
- Peer review (if available)

### Risk 3: Template Becomes Outdated

**Mitigation:**
- Document template update process
- Schedule quarterly reviews
- Track pattern evolution
- Maintain CHANGELOG

### Risk 4: Over-Engineering

**Mitigation:**
- Keep skills practical (300-600 lines)
- Focus on developer needs
- Avoid unnecessary abstraction
- Validate with real use cases

---

## 📖 APPENDICES

### Appendix A: Service Categorization

**Data Ingestion (5):**
1. polygon-live-collector
2. polygon-historical-downloader
3. dukascopy-historical-downloader
4. external-data-collector
5. data-bridge

**Data Processing (1):**
6. tick-aggregator

**ML Pipeline (4):**
7. feature-engineering
8. supervised-training
9. finrl-training
10. inference

**Trading Execution (3):**
11. risk-management
12. execution
13. mt5-connector

**Infrastructure (2):**
14. central-hub
15. performance-monitoring

**Supporting (3):**
16. backtesting
17. dashboard
18. notification-hub

### Appendix B: Config Category Templates

**Data Ingestion Services:**
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

**ML Services:**
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

**Trading Services:**
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

### Appendix C: Quick Reference Commands

**Update single service:**
```bash
# Read template
Read _SERVICE_SKILL_TEMPLATE.md

# Read current skill
Read service_{name}.md

# Merge content
# Write updated skill
Write service_{name}.md
```

**Batch validation:**
```bash
# Check all skills have config section
grep -l "CENTRALIZED CONFIGURATION" *.md | wc -l
# Expected: 18

# Check line counts
wc -l service_*.md
# Expected: 300-600 lines each

# Check for secrets
grep -i "password\|api_key.*=" service_*.md
# Expected: No hardcoded secrets
```

**Cross-reference audit:**
```bash
# Check all skills reference central-hub
grep -l "service_central_hub.md" service_*.md | wc -l
# Expected: 17 (all except central-hub itself)

# Check config management references
grep -l "centralized_config_management.md" service_*.md | wc -l
# Expected: 18
```

---

## ✅ CONCLUSION

### Summary

This strategic plan provides:
1. ✅ Clear canonical location decision (BACKEND)
2. ✅ Systematic update strategy (template-based)
3. ✅ Prioritized execution phases (4 phases)
4. ✅ Quality validation framework
5. ✅ Maintenance and sync strategy
6. ✅ Risk mitigation measures

### Next Steps

**Immediate (Today):**
1. Review and approve this plan
2. Backup current BACKEND skills
3. Begin Phase 1 execution

**Short-term (Week 1):**
1. Complete Phase 1 & 2 (Data + ML pipeline)
2. Validate with real Claude usage
3. Refine template based on learnings

**Long-term (Week 2+):**
1. Complete Phase 3 & 4 (Trading + Supporting)
2. Final validation and documentation
3. Establish maintenance routine

### Success Criteria

**Plan is successful when:**
- ✅ All 18 services have comprehensive, consistent skills
- ✅ Centralized config pattern adopted uniformly
- ✅ Developers can find config info in <2 minutes
- ✅ Services handle Central Hub downtime gracefully
- ✅ Config changes deployable without code changes
- ✅ Template supports future service additions

**Ready to execute!**
