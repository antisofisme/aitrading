# Service Skills Implementation Roadmap

**Purpose:** Track creation of skill files for all 18 microservices with centralized config pattern
**Status:** 3/18 Complete (Template + Central Hub created)
**Date:** 2025-10-19

---

## ✅ COMPLETED (3/18)

### **Infrastructure & Templates**

1. ✅ **centralized_config_management.md**
   - Centralized config architecture
   - ConfigClient design
   - Database schema
   - API endpoints

2. ✅ **service_central_hub.md**
   - Central Hub service skill
   - Config provider pattern
   - API documentation
   - Integration examples

3. ✅ **_SERVICE_SKILL_TEMPLATE.md**
   - Reusable template for all services
   - Centralized config pattern (MANDATORY)
   - Config hierarchy rules
   - Validation checklists

---

## 📋 TODO: SERVICE SKILLS (15/18 Services)

### **Data Ingestion Layer (5 Services)**

#### 1. ⏸️ **service_polygon_live_collector.md**
- Real-time Polygon.io tick collection
- Config: batch_size, symbols, rate_limits
- Dependencies: NATS, Kafka, ClickHouse

#### 2. ⏸️ **service_polygon_historical_downloader.md**
- Historical data download + gap filling
- Config: gap_check_interval, batch_size, download_range
- Dependencies: NATS, Kafka, ClickHouse

#### 3. ⏸️ **service_dukascopy_historical_downloader.md**
- Dukascopy historical data download
- Config: download_range, batch_size, parallel_downloads
- Dependencies: NATS, Kafka, TimescaleDB

#### 4. ⏸️ **service_external_data_collector.md**
- Economic calendar, FRED indicators, commodity prices
- Config: api_keys, fetch_intervals, data_sources
- Dependencies: PostgreSQL, NATS

#### 5. ⏸️ **service_mt5_connector.md**
- MT5 tick data collection
- Config: symbols, poll_interval, batch_size
- Dependencies: NATS, Kafka, TimescaleDB

---

### **Data Processing Layer (3 Services)**

#### 6. ⏸️ **service_data_bridge.md**
- NATS → ClickHouse bridge
- Config: batch_size, buffer_timeout, validation_rules
- Dependencies: NATS, Kafka, ClickHouse

#### 7. ⏸️ **service_tick_aggregator.md**
- Tick → OHLCV aggregation (7 timeframes)
- Config: timeframes, publish_interval, min_ticks
- Dependencies: TimescaleDB, NATS, Kafka, ClickHouse

#### 8. ⏸️ **service_feature_engineering.md**
- ML feature calculation (72 features)
- Config: indicators, lookback_periods, feature_flags
- Dependencies: ClickHouse, NATS, Kafka

---

### **Machine Learning Layer (3 Services)**

#### 9. ⏸️ **service_supervised_training.md**
- Supervised ML model training
- Config: model_params, training_schedule, hyperparameters
- Dependencies: ClickHouse, model storage

#### 10. ⏸️ **service_finrl_training.md**
- FinRL reinforcement learning training
- Config: env_params, agent_config, reward_function
- Dependencies: ClickHouse, model storage

#### 11. ⏸️ **service_inference.md**
- Real-time ML inference
- Config: model_selection, batch_size, confidence_threshold
- Dependencies: ClickHouse, NATS, model storage

---

### **Trading Execution Layer (3 Services)**

#### 12. ⏸️ **service_risk_management.md**
- Risk assessment and position sizing
- Config: risk_limits, max_drawdown, position_size_rules
- Dependencies: PostgreSQL, NATS

#### 13. ⏸️ **service_execution.md**
- Order execution and management
- Config: slippage_tolerance, order_types, execution_strategy
- Dependencies: MT5, PostgreSQL, NATS

#### 14. ⏸️ **service_performance_monitoring.md**
- Trade performance tracking
- Config: metrics, reporting_interval, alert_thresholds
- Dependencies: PostgreSQL, ClickHouse

---

### **Supporting Services Layer (3 Services)**

#### 15. ⏸️ **service_backtesting.md**
- Strategy backtesting engine
- Config: test_period, commission_model, slippage_model
- Dependencies: ClickHouse, PostgreSQL

#### 16. ⏸️ **service_dashboard.md**
- Real-time dashboard and visualization
- Config: refresh_rate, chart_configs, alert_settings
- Dependencies: PostgreSQL, ClickHouse, NATS

#### 17. ⏸️ **service_notification_hub.md**
- Alert and notification management
- Config: channels, templates, priority_rules
- Dependencies: PostgreSQL, external APIs (Telegram, email)

---

## 🎯 IMPLEMENTATION STRATEGY

### **Phase 1: Pilot Services (Priority - Do First)**

Create detailed skills for frequently-modified services:

1. **polygon-historical-downloader** (just fixed)
2. **tick-aggregator** (critical pipeline)
3. **data-bridge** (critical pipeline)

**Estimated Time:** 2-3 hours

---

### **Phase 2: Data Ingestion (High Priority)**

Complete all data ingestion service skills:

4. polygon-live-collector
5. dukascopy-historical-downloader
6. external-data-collector
7. mt5-connector

**Estimated Time:** 3-4 hours

---

### **Phase 3: Processing & ML (Medium Priority)**

8. feature-engineering
9. supervised-training
10. finrl-training
11. inference

**Estimated Time:** 3-4 hours

---

### **Phase 4: Trading & Supporting (Lower Priority)**

12-17. Remaining services

**Estimated Time:** 4-5 hours

---

## 📝 SKILL FILE REQUIREMENTS

### **Mandatory Sections (EVERY Service)**

✅ **Quick Reference**
- When to use this skill
- Key responsibilities
- Data flow diagram

✅ **Centralized Configuration** ⭐
- Config hierarchy (ENV vs Central Hub)
- Implementation pattern (ConfigClient)
- Safe defaults
- Hot-reload support

✅ **Critical Rules**
- Config hierarchy rules
- Graceful degradation
- Service-specific rules

✅ **Architecture**
- Data flow with config integration
- Dependencies
- Message patterns

✅ **Validation Checklist**
- Config validation
- Code validation
- Integration testing

✅ **Common Issues**
- Config loading issues
- Service startup issues
- Runtime issues

✅ **Summary**
- One-line purpose
- Config pattern
- Key success factors

---

## 🔍 QUALITY CHECKLIST

For each skill file created:

- [ ] Uses centralized config pattern (ConfigClient)
- [ ] Follows config hierarchy (critical in ENV, operational in Hub)
- [ ] Includes safe defaults
- [ ] Documents NATS subjects and Kafka topics
- [ ] Lists all dependencies
- [ ] Provides validation checklist
- [ ] Includes common issues and solutions
- [ ] Has working code examples
- [ ] References Central Hub API endpoints
- [ ] Explains graceful degradation

---

## 📊 PROGRESS TRACKING

```
Total Services: 18
Skills Created: 3 (Template + Central Hub + Config Management)
Remaining: 15

Progress: ████░░░░░░░░░░░░ 16.7%

Estimated Time to Complete:
- Pilot (3): 2-3 hours
- Data Ingestion (4): 3-4 hours
- Processing/ML (4): 3-4 hours
- Trading/Supporting (6): 4-5 hours
TOTAL: 12-16 hours
```

---

## 💡 TEMPLATE USAGE

### **Creating New Service Skill**

```bash
# 1. Copy template
cp .claude/skills/_SERVICE_SKILL_TEMPLATE.md \
   .claude/skills/service_polygon_historical_downloader.md

# 2. Replace placeholders
[SERVICE NAME] → Polygon Historical Downloader
[service-name] → polygon-historical-downloader
[SERVICE_TYPE] → Data Ingestion
[PORT] → 8002

# 3. Fill service-specific sections
- Data flow
- Message patterns
- Database schema
- Critical rules

# 4. Test skill file
claude --skill service_polygon_historical_downloader \
       "Show me how to update config"
```

---

## 🎯 NEXT ACTIONS

**Immediate (Tonight/Tomorrow):**
1. Create `service_polygon_historical_downloader.md` (pilot #1)
2. Create `service_tick_aggregator.md` (pilot #2)
3. Create `service_data_bridge.md` (pilot #3)

**Short Term (This Week):**
4-7. Complete Data Ingestion layer skills

**Medium Term (Next Week):**
8-17. Complete remaining services

**Success Criteria:**
- ✅ All 18 services have skill files
- ✅ All follow centralized config pattern
- ✅ All include validation checklists
- ✅ All tested with actual services
- ✅ CLAUDE.md updated with skill file references

---

## 📚 REFERENCE DOCUMENTS

**Architecture:**
- `docs/CENTRAL_HUB_CONFIG_REVIEW.md` - Architecture review
- `docs/CENTRALIZED_CONFIG_PROGRESS.md` - Implementation progress

**Skills:**
- `.claude/skills/centralized_config_management.md` - Config system
- `.claude/skills/service_central_hub.md` - Central Hub service
- `.claude/skills/_SERVICE_SKILL_TEMPLATE.md` - Reusable template

**Database:**
- `central-hub/base/config/database/init-scripts/03-create-service-configs.sql`

**Code:**
- `central-hub/base/api/config.py` - Config API endpoints
- `shared/components/config/client.py` - ConfigClient (to be created)

---

## ✅ COMPLETION CRITERIA

**Project Complete When:**
- [ ] All 18 services have skill files
- [ ] All skills follow centralized config pattern
- [ ] All skills tested with real services
- [ ] ConfigClient library implemented
- [ ] At least 3 services migrated to use ConfigClient
- [ ] Documentation updated in CLAUDE.md
- [ ] Team trained on new pattern

**Current Status:** 16.7% Complete (3/18 skills)
**Target Date:** End of month (10 days remaining)
**Daily Goal:** 1-2 skill files per day

---

This roadmap ensures every service has proper documentation and follows the centralized config architecture!
