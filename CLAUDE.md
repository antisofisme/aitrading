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
- ✅ Do what has been asked; nothing more, nothing less
- ✅ Batch all related operations in single message
- ✅ Keep files modular (< 500 lines)
- ✅ Use environment variables for secrets
- ✅ Test before deploying

**Don'ts:**
- ❌ NEVER create files unless absolutely necessary
- ❌ NEVER save working files, text/mds, tests to the root folder
- ❌ NEVER proactively create documentation files
- ❌ NEVER hardcode API keys, passwords, or secrets
- ❌ NEVER skip testing for critical ML features

**Always prefer:** Editing existing file > Creating new file

## Project Structure

```
project3/
├── backend/
│   ├── 00-data-ingestion/       # Data collection services
│   ├── 01-central-hub/          # Service coordination
│   ├── 02-data-processing/      # Aggregation & indicators
│   └── 03-machine-learning/     # Feature engineering & ML
```

## Current Implementation Status

**Phase 1:** Foundation ✅ COMPLETE (82% ready)
- Historical data: 2.8 years (2023-2025)
- 14 trading pairs
- 7 timeframes (5m, 15m, 30m, 1h, 4h, 1d, 1w)

**Phase 2:** Feature Engineering (IN PROGRESS)
- 72 ML features defined (v2.3 with Fibonacci)
- Feature engineering service updated
- Pending: 14 missing technical indicators

## Key Documents

- `project3/backend/02-data-processing/TRADING_STRATEGY_AND_ML_DESIGN.md` - Main strategy (v2.3)
- `project3/backend/02-data-processing/FOUNDATION_VERIFICATION_REPORT.md` - Phase 1 status
- `project3/backend/02-data-processing/FIBONACCI_ANALYSIS_AND_INTEGRATION.md` - Fibonacci features

## Next Steps

1. Add 14 missing indicators (RSI, Bollinger Bands, Stochastic, SMAs, CCI, MFI)
2. Test feature engineering service
3. Create ML training tables
4. Begin Week 2: Feature Engineering Design

---

**Note:** Keep this file minimal. Detailed instructions in respective service READMEs.
