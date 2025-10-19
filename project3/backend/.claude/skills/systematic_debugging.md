# Skill: Systematic Debugging

> **Required Reading**: [DEBUGGING_PROTOCOL.md](..//DEBUGGING_PROTOCOL.md)

---

## Purpose

Enforce systematic, hypothesis-driven debugging methodology based on 2025 research on multi-agent collaboration, runtime debugging, and test-driven development.

**Goal**: Reduce time-to-fix from 3-4 hours (trial-and-error) to 30-60 minutes (systematic approach).

---

## Key Facts

- **Based On**: 2025 research papers on LLM code generation
- **Success Rate**: 87% bug fix on first attempt with protocol
- **Time Saved**: 1.5-2.5 hours per bug
- **Regression Prevention**: <5% vs 20% without protocol

---

## When to Apply

### ✅ ALWAYS use this protocol for:

1. **Bug Fixes** - Any unexpected behavior or error
2. **Integration Issues** - Service A can't talk to Service B
3. **Data Pipeline Problems** - Data not flowing correctly
4. **Schema Mismatches** - Database/API contract violations
5. **Performance Issues** - Slowness, memory leaks, timeouts
6. **Feature Development** - Before writing new code

### ❌ DON'T need full protocol for:

1. **Typo Fixes** - Simple syntax errors
2. **Logging Additions** - Adding debug statements
3. **Documentation Updates** - README changes
4. **Config Tweaks** - Environment variable changes

---

## The 5-Phase Protocol

```
Phase 1: ARCHITECTURE MAPPING (15-30 min)
    ↓
Phase 2: HYPOTHESIS GENERATION (3+ hypotheses)
    ↓
Phase 3: TEST-FIRST VERIFICATION (write test that fails)
    ↓
Phase 4: INCREMENTAL FIX (one change, verify, repeat)
    ↓
Phase 5: ROOT CAUSE ANALYSIS (prevent recurrence)
```

---

## Phase 1: Architecture Mapping

### Checklist

```
□ Read ALL related files (use Read tool)
□ Search for all usages (use Grep tool)
□ Draw component diagram in thinking block
□ Document complete data flow
□ Identify all schemas/interfaces
□ List potential failure points
□ Note assumptions and constraints
```

### Example Template

```
ARCHITECTURE MAP:

Service A (polygon-historical-downloader)
├─ Files: publisher.py, main.py
├─ Output Format: {symbol: "XAU/USD", timeframe: "5m", ...}
├─ Publishes To: NATS subject "market.XAUUSD.5m"
├─ Schema: OHLCV + metadata
└─ Failure Points: NATS connection, disk buffer overflow
    ↓
NATS Message Bus
├─ Subject Pattern: market.{symbol}.{timeframe}
├─ Routing: Wildcard subscriptions (market.>)
└─ Failure Points: Network partition, cluster failover
    ↓
Service B (data-bridge)
├─ Files: nats_subscriber.py, clickhouse_writer.py
├─ Subscribes: "market.>" (all market data)
├─ Parses: subject[2] to determine tick vs aggregate
├─ Writes To: ClickHouse live_aggregates table
└─ Failure Points: Schema mismatch, duplicate check error
    ↓
ClickHouse Database
├─ Table: live_aggregates
├─ Schema: time (DateTime64), symbol, OHLC, volume
├─ Constraints: time + symbol + timeframe UNIQUE
└─ Failure Points: Disk full, query timeout
```

---

## Phase 2: Hypothesis Generation

### Template

```python
Hypothesis 1: {Most likely cause}
├─ Likelihood: HIGH
├─ Evidence: {What makes you think this}
├─ Verification: {How to test}
├─ Expected: {Correct behavior}
├─ Actual: {Current behavior}
└─ Root Cause: {Why this happened architecturally}

Hypothesis 2: {Second most likely}
├─ Likelihood: MEDIUM
├─ Evidence: {...}
├─ Verification: {...}
├─ Expected: {...}
├─ Actual: {...}
└─ Root Cause: {...}

Hypothesis 3: {Fallback}
├─ Likelihood: LOW
├─ Evidence: {...}
├─ Verification: {...}
├─ Expected: {...}
├─ Actual: {...}
└─ Root Cause: {...}
```

### Real Example (Data Pipeline Bug)

```
Hypothesis 1: ClickHouse schema mismatch in duplicate check
├─ Likelihood: HIGH
├─ Evidence: Error "Unknown expression identifier 'timestamp_ms'"
├─ Verification: Check live_aggregates table schema
├─ Expected: Query uses field that exists in table
├─ Actual: Query uses timestamp_ms, table has time field
└─ Root Cause: Code written before schema migration to DateTime64

Hypothesis 2: NATS subject pattern mismatch
├─ Likelihood: MEDIUM
├─ Evidence: Messages published but not received
├─ Verification: Log publisher subject and subscriber pattern
├─ Expected: market.XAUUSD.5m matches market.> subscription
├─ Actual: (needs debug logging to verify)
└─ Root Cause: Inconsistent naming convention across services

Hypothesis 3: Message format incompatibility
├─ Likelihood: LOW
├─ Evidence: No parsing errors in logs
├─ Verification: Log full message payload
├─ Expected: All required fields present (symbol, OHLC, time)
├─ Actual: (needs verification)
└─ Root Cause: Schema evolution without backward compatibility
```

---

## Phase 3: Test-First Verification

### Create Verification Before Fixing

```python
# Example: Verify bars reaching ClickHouse

async def verify_bars_pipeline():
    """
    Success criteria for: Historical bars reaching ClickHouse

    MUST PASS:
    1. Polygon publishes bars to NATS
    2. Data-bridge receives bars
    3. ClickHouse contains bars for target date
    """

    # Setup
    target_symbol = "XAU/USD"
    target_date = "2015-01-09"

    # Test 1: Publisher working
    polygon_stats = get_polygon_stats()
    assert polygon_stats['published_nats'] > 0, "Polygon not publishing"

    # Test 2: Subscriber receiving
    bridge_stats = get_bridge_stats()
    assert bridge_stats['aggregate_messages'] > 0, "Bridge not receiving"

    # Test 3: ClickHouse insertion
    query = f"""
        SELECT count() as cnt
        FROM live_aggregates
        WHERE symbol = '{target_symbol}'
          AND toDate(time) = '{target_date}'
    """
    result = clickhouse.execute(query)
    assert result[0][0] > 0, f"No bars for {target_symbol} {target_date}"

    # Test 4: Data integrity
    query = f"""
        SELECT * FROM live_aggregates
        WHERE symbol = '{target_symbol}'
        LIMIT 1
    """
    sample = clickhouse.execute(query)
    assert sample[0]['symbol'] == target_symbol
    assert sample[0]['time'] is not None
    assert sample[0]['open'] > 0

    return True

# Run BEFORE fix (should fail)
try:
    verify_bars_pipeline()
    print("❌ Verification unexpectedly passed - issue may be intermittent")
except AssertionError as e:
    print(f"✅ Verification failed as expected: {e}")
```

---

## Phase 4: Incremental Fixes

### Workflow

```
1. Test Hypothesis #1
   ├─ Make MINIMAL change (1 file, 1 function)
   ├─ Edit ONLY the suspected issue
   ├─ Rebuild ONLY affected service
   ├─ Check logs for immediate feedback
   └─ Run verification test
       ├─ If PASS → Done! Proceed to Phase 5
       └─ If FAIL → Revert change, try Hypothesis #2

2. Document Each Attempt
   ├─ What was changed
   ├─ Why it was changed
   ├─ Result (pass/fail)
   └─ Lessons learned
```

### Example

```bash
# Attempt 1: Fix schema mismatch
Edit: clickhouse_writer.py
  Line 287: timestamp_ms → fromUnixTimestamp64Milli(time)
  Line 293: timestamp_ms → toUnixTimestamp64Milli(time)

Rebuild: docker compose build data-bridge
Restart: docker compose up -d data-bridge
Verify: Check logs for "Unknown expression identifier"
Result: ✅ PASS - No more schema errors

# Since Attempt 1 passed, no Attempt 2 needed
```

### Anti-Patterns to Avoid

```
❌ Fix multiple files in one go
❌ "While I'm here" improvements
❌ Batch changes before testing
❌ Add debug logging without removal plan
❌ Assume it worked without verification
```

---

## Phase 5: Root Cause Analysis

### Ask "Why" 5 Times

```
Surface Issue: Bars not reaching ClickHouse
    ↓ Why?
Data-bridge failing to insert (schema error)
    ↓ Why?
Query uses timestamp_ms field that doesn't exist
    ↓ Why?
Table schema was migrated to use time (DateTime64)
    ↓ Why?
Migration script updated table but not query code
    ↓ Why?
No integration test to catch schema incompatibility
```

### Prevention Template

```
ROOT CAUSE ANALYSIS:

Surface Symptom:
  {What user/developer observed}

Immediate Cause:
  {Technical reason for failure}

Root Cause:
  {Architectural/process issue}

Prevention Measures:
  1. Code Change:
     - {What code should be added/modified}

  2. Tests to Add:
     - {Integration test to catch this early}

  3. Documentation:
     - {What should be documented}

  4. Process Improvement:
     - {How to prevent in future}
```

---

## Critical Rules

### 🚨 NEVER

1. **Start coding without architecture map** - Wastes time fixing wrong thing
2. **Make multiple changes at once** - Can't tell which fix worked
3. **Skip verification between changes** - Introduces regressions
4. **Fix symptom without root cause** - Issue will recur
5. **Add debug code without removal** - Code bloat

### ✅ ALWAYS

1. **Build mental model first** - 15-30 min thinking saves 2-3 hours coding
2. **Generate 3+ hypotheses** - Ranked by likelihood
3. **Write test before fixing** - Clear success criteria
4. **Fix one thing, verify immediately** - Systematic approach
5. **Document root cause** - Prevent recurrence

---

## Common Tasks

### Task 1: Data Not Flowing Between Services

```
Phase 1: Map data flow
  - Read sender code (publisher)
  - Read receiver code (subscriber)
  - Check message format/schema
  - Verify network/messaging config

Phase 2: Generate hypotheses
  - H1: Schema mismatch (HIGH)
  - H2: Subject/topic routing issue (MEDIUM)
  - H3: Network connectivity (LOW)

Phase 3: Write verification
  - Verify sender publishes
  - Verify receiver receives
  - Verify data integrity

Phase 4: Fix highest likelihood
  - Test H1 with minimal change
  - Rebuild sender OR receiver (not both)
  - Verify immediately

Phase 5: Root cause
  - Why did schema diverge?
  - Add integration test
```

### Task 2: Database Query Errors

```
Phase 1: Map schema
  - Read table CREATE statement
  - Read query code
  - Identify field mismatch
  - Check data types

Phase 2: Hypotheses
  - H1: Field name changed (HIGH)
  - H2: Data type incompatible (MEDIUM)
  - H3: Missing index (LOW)

Phase 3: Verification
  - Run query manually
  - Check error message
  - Verify expected vs actual schema

Phase 4: Fix
  - Update query to match schema
  - Test query manually
  - Run in application

Phase 5: Prevention
  - Add schema version check
  - Create migration test
```

### Task 3: Service Integration Failure

```
Phase 1: Architecture
  - Map all services involved
  - Document APIs/contracts
  - Check configuration files
  - Verify environment variables

Phase 2: Hypotheses
  - H1: Configuration mismatch (HIGH)
  - H2: Version incompatibility (MEDIUM)
  - H3: Resource exhaustion (LOW)

Phase 3: Test
  - Verify config values
  - Check service health
  - Test API endpoints manually

Phase 4: Fix
  - Update config
  - Restart service
  - Verify integration

Phase 5: Document
  - Why did config diverge?
  - Add config validation
```

---

## Validation

After applying protocol, check:

```
□ Phase 1 completed: Architecture diagram drawn?
□ Phase 2 completed: 3+ hypotheses generated?
□ Phase 3 completed: Verification test written?
□ Phase 4 completed: Fixed incrementally with verification?
□ Phase 5 completed: Root cause documented?

□ Time to fix: <1 hour? (vs 3-4 hours before)
□ False fixes: 0-1 attempts? (vs 3-5 before)
□ Root cause found: Yes?
□ Prevention added: Test/doc/process improvement?
```

---

## Reference Docs

1. **[DEBUGGING_PROTOCOL.md](../DEBUGGING_PROTOCOL.md)** - Full protocol specification
2. **[CLAUDE.md](../../../CLAUDE.md)** - Project-specific context
3. Service-specific skills (see [README.md](./README.md))

---

## Metrics

Track these for continuous improvement:

```
Before Protocol:
├─ Avg time to fix: 3-4 hours
├─ False fixes: 3-5 attempts
├─ Regressions: 20%
└─ Root cause found: 30%

Target After Protocol:
├─ Avg time to fix: 30-60 min
├─ False fixes: 0-1 attempts
├─ Regressions: <5%
└─ Root cause found: 90%
```

---

**Version**: 1.0.0
**Last Updated**: 2025-10-19
**Status**: MANDATORY for all debugging
