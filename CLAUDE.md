# Claude Code Configuration - AI Trading Project

## Project Overview

AI-powered trading system for forex/gold analysis with ML-based predictions.

## Important Instructions

### 🚨 CRITICAL: Concurrent Execution Pattern

**⚡ GOLDEN RULE: "1 MESSAGE = ALL RELATED OPERATIONS"**

Always batch related operations in a SINGLE message for efficiency:

- **TodoWrite**: Batch ALL todos in ONE call (5-10+ todos minimum)
- **File operations**: Batch ALL reads/writes/edits in ONE message
- **Bash commands**: Batch ALL terminal operations in ONE message

**Example - Adding Multiple Indicators:**
```javascript
[Single Message]:
  Edit "technical_indicators.py" (add RSI calculation)
  Edit "technical_indicators.py" (add Bollinger Bands)
  Edit "technical_indicators.py" (add Stochastic)

  TodoWrite { todos: [
    {content: "Add RSI indicator", status: "completed"},
    {content: "Add Bollinger Bands", status: "completed"},
    {content: "Add Stochastic K,D", status: "in_progress"},
    {content: "Test all indicators", status: "pending"},
    {content: "Deploy tick-aggregator", status: "pending"}
  ]}

  Bash "pytest tests/test_indicators.py && docker-compose restart tick-aggregator"
```

**Benefits:**
- ✅ Faster execution (parallel processing)
- ✅ Token efficiency (fewer messages)
- ✅ Better context preservation
- ✅ Atomic operations (all succeed or fail together)

---

### 📁 File Organization Rules

**NEVER save to root folder. Use these directories:**
- `/docs` - Documentation and markdown files
- `/tests` - Test files
- `/config` - Configuration files (YAML, JSON)
- `/scripts` - Utility scripts
- `/src` - Source code files

**Project-specific:**
- `project3/backend/02-data-processing/` - Strategy docs, verification reports
- `project3/backend/03-machine-learning/` - Feature engineering, ML models
- Feature modules: Keep under 500 lines each

---

### 💎 Code Best Practices

- **Modular Design**: Files under 500 lines (split if larger)
- **Environment Safety**: NEVER hardcode secrets (use .env for API keys, passwords)
- **Test-First**: Write tests before implementation when possible
- **Clean Architecture**: Separate concerns (data/processing/ML layers)
- **Documentation**: Keep inline comments + docs/ folder updated

**Security Examples:**
```python
# ❌ WRONG
POLYGON_API_KEY = "abc123xyz"
CLICKHOUSE_PASSWORD = "password123"

# ✅ CORRECT
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD")
```

---

### Development Workflow
- Keep responses concise and to the point
- Only create files when explicitly necessary
- Prefer editing existing files over creating new ones
- Never proactively create documentation unless requested

---

### 🎯 Service Skills - MANDATORY USAGE

**⚡ CRITICAL: Always Use Skills When Working on Services**

Before implementing, reviewing, or fixing ANY service, you MUST:

1. **Read the skill file first**: `.claude/skills/service_{name}.md`
2. **Understand the service**:
   - Purpose (what it does)
   - Data flow (input → process → output)
   - Messaging pattern (NATS/Kafka)
   - Dependencies (upstream/downstream)
3. **Follow Critical Rules** (prevent common mistakes)
4. **Use validation checklist** after making changes

**Available Skills (18 services):**
```
.claude/skills/
├── README.md (index + usage guide)
├── service_polygon_live_collector.md
├── service_polygon_historical_downloader.md
├── service_dukascopy_historical_downloader.md
├── service_external_data_collector.md
├── service_central_hub.md (Core Infrastructure)
├── service_data_bridge.md
├── service_tick_aggregator.md
├── service_feature_engineering.md
├── service_supervised_training.md
├── service_finrl_training.md
├── service_inference.md
├── service_risk_management.md
├── service_execution.md
├── service_performance_monitoring.md
├── service_mt5_connector.md
├── service_backtesting.md
├── service_dashboard.md
└── service_notification_hub.md
```

**Example Workflow:**

User: "Fix bug in tick-aggregator"

**Step 1 - Read Skill:**
```bash
Read ".claude/skills/service_tick_aggregator.md"
```

**Step 2 - Understand:**
- Purpose: Aggregate ticks → OHLCV candles (7 timeframes)
- Flow: TimescaleDB.ticks → Aggregator → ClickHouse.aggregates → NATS + Kafka
- Critical Rule: NEVER skip NATS publishing (feature-engineering needs it!)

**Step 3 - Implement Fix:**
- Follow critical rules from skill file
- Maintain data flow consistency
- Keep messaging pattern intact

**Step 4 - Validate:**
```bash
# From skill file validation checklist:
- [ ] Candles in ClickHouse
- [ ] NATS publishes bars.*.*
- [ ] Kafka archives aggregate_archive
- [ ] All 7 timeframes active
- [ ] No NULL values in OHLC
```

**Why Skills Are Mandatory:**
- ✅ **Consistency**: Same understanding every time
- ✅ **No mistakes**: Critical rules prevent common errors
- ✅ **Correct flow**: Maintain data pipeline integrity
- ✅ **Proper messaging**: Don't break NATS/Kafka patterns

**RULE: NEVER work on a service without reading its skill file first!**

---

### 🤖 Useful Agent Types

When spawning agents for complex tasks, use these specialized types:

**Core Development:**
- `ml-developer` - ML feature engineering specialist (Fibonacci, indicators, feature calculators)
- `backend-dev` - Backend service development (data-bridge, tick-aggregator, feature-service)
- `code-analyzer` - Code quality review (analyze fibonacci.py, check complexity)
- `tester` - Testing & validation (test 72 features, validate ML pipeline)
- `reviewer` - Code review (review before merge, check best practices)

**Usage Example:**
```javascript
Task("ML Developer", "Implement RSI and Bollinger Bands indicators with TA-Lib", "ml-developer")
Task("Tester", "Create comprehensive tests for 72 ML features", "tester")
Task("Code Analyzer", "Review fibonacci.py code quality and performance", "code-analyzer")
```

---

### 📝 Critical Reminders

**Do's:**
- ✅ **READ SKILL FILE FIRST** before working on any service
- ✅ Do what has been asked; nothing more, nothing less
- ✅ Batch all related operations in single message
- ✅ Keep files modular (< 500 lines)
- ✅ Use environment variables for secrets
- ✅ Test before deploying
- ✅ Follow validation checklist from skill files

**Don'ts:**
- ❌ **NEVER work on service without reading skill file**
- ❌ NEVER create files unless absolutely necessary
- ❌ NEVER save working files, text/mds, tests to the root folder
- ❌ NEVER proactively create documentation files
- ❌ NEVER hardcode API keys, passwords, or secrets
- ❌ NEVER skip testing for critical ML features
- ❌ NEVER break messaging patterns (NATS/Kafka)
- ❌ NEVER skip validation checklist

**Always prefer:**
- Reading skill file > Guessing service behavior
- Editing existing file > Creating new file

## 📚 Documentation Structure

This project uses a **layered documentation approach**:

### **Layer 1: Quick Reference (Skills)**
- **Location**: `.claude/skills/service_{name}.md`
- **Purpose**: Fast, per-service knowledge base
- **Usage**: Read FIRST before working on any service

### **Layer 2: Complete Architecture**
- **Location**: `project3/backend/docs/*.md`
- **Purpose**: Detailed architecture, planning templates, database schemas
- **Usage**: Reference for deep implementation details

### **Layer 3: Service-Specific**
- **Location**: Each service folder (e.g., `00-data-ingestion/tick-aggregator/`)
- **Purpose**: Implementation details, config examples, README
- **Usage**: Service-specific technical details

**Rule**: Always start with Layer 1 (Skills) → Layer 2 (Docs) → Layer 3 (Service folder)

---

**Note:** This file contains **working guidelines only**. For project status, implementation details, and roadmap, check the documentation layers above.
