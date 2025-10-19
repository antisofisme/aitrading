# 🧠 Systematic Debugging Protocol
**MANDATORY FOR ALL BUG FIXES AND FEATURE DEVELOPMENT**

> Based on 2025 research: Multi-Agent Collaboration, Runtime Debugging, and Test-Driven Development

---

## 🚨 **CRITICAL RULE**

**NEVER start coding immediately. ALWAYS follow this 5-phase protocol.**

Research shows: **"Thinking before debugging prevents fixing local issues while missing higher-level architectural problems."**

---

## 📋 **Phase 1: ARCHITECTURE MAPPING (15-30 min minimum)**

### Before touching ANY code, build complete mental model:

```
┌─────────────────────────────────────────────────────────┐
│ MANDATORY CHECKLIST:                                    │
├─────────────────────────────────────────────────────────┤
│ □ Read ALL files involved in the issue                 │
│ □ Draw component interaction diagram                   │
│ □ Document complete data flow (input → output)         │
│ □ Identify ALL interfaces/schemas between components   │
│ □ List assumptions and constraints                     │
│ □ Find potential failure points                        │
└─────────────────────────────────────────────────────────┘
```

### Example Mental Model Template:

```
Component A (file_a.py)
├─ Input: {data structure}
├─ Processing: [step 1, step 2, step 3]
├─ Output: {data structure}
├─ Dependencies: [Component B, Service X]
├─ Interface: Protocol/Schema used
└─ Failure Points: [timeout, schema mismatch, null values]
    ↓
Component B (file_b.py)
├─ Input: {received from A}
├─ Schema Validation: [field1, field2, field3]
├─ Storage: Database table schema
└─ Constraints: [unique keys, foreign keys, data types]
```

**Tools to Use:**
- `Read` all related files first
- `Grep` to find all usages of key functions/variables
- `Glob` to find all test files
- Draw ASCII diagrams in thinking block

---

## 🔬 **Phase 2: HYPOTHESIS GENERATION (Minimum 3 hypotheses)**

### Generate ranked hypotheses BEFORE any debugging:

```python
# Template for each hypothesis:
Hypothesis {N}: {Clear statement of what might be wrong}
├─ Likelihood: High/Medium/Low
├─ Evidence Needed: [What data would prove/disprove this]
├─ Verification Method: [Exact steps to test]
├─ Expected Behavior: [What should happen if correct]
├─ Actual Behavior: [What is happening]
└─ Root Cause If True: [Architectural issue that caused this]
```

### Example (from actual bug):

```
Hypothesis 1: ClickHouse schema mismatch in duplicate check
├─ Likelihood: HIGH
├─ Evidence: Error mentions "Unknown expression identifier 'timestamp_ms'"
├─ Verification: Check live_aggregates table schema vs query
├─ Expected: Query uses field that exists in table
├─ Actual: Query uses timestamp_ms, table has time field
└─ Root Cause: Code written before schema migration, not updated

Hypothesis 2: NATS subject pattern mismatch
├─ Likelihood: MEDIUM
├─ Evidence: Messages published but not received
├─ Verification: Log publisher subject and subscriber pattern
├─ Expected: market.XAUUSD.5m matches market.> subscription
├─ Actual: (needs verification)
└─ Root Cause: Inconsistent naming convention

Hypothesis 3: Message format incompatibility
├─ Likelihood: LOW
├─ Evidence: No parsing errors in logs
├─ Verification: Log message payload structure
├─ Expected: All required fields present
├─ Actual: (needs verification)
└─ Root Cause: Schema evolution without migration
```

**ANTI-PATTERN:**
```
❌ "Let me add debug logging to see what's happening"
❌ "Let me try changing this and see if it works"
❌ "Maybe it's a race condition, let me add sleep()"
```

**CORRECT PATTERN:**
```
✅ Generate 3-5 specific hypotheses ranked by likelihood
✅ Design targeted verification for top hypothesis
✅ Test hypothesis systematically
```

---

## 🧪 **Phase 3: TEST-FIRST VERIFICATION**

### Write verification BEFORE fixing anything:

```python
# 1. Create verification script or test
# This becomes your "Definition of Done"

async def verify_pipeline_fix():
    """
    Verification for: Bars from polygon reaching ClickHouse

    Success Criteria:
    - Polygon publishes bars to NATS
    - Data-bridge receives bars from NATS
    - ClickHouse inserts bars without errors
    - Verification query finds expected bars
    """

    # Test 1: Publisher working
    assert polygon_stats['published_nats'] > 0

    # Test 2: NATS routing working
    assert data_bridge_stats['aggregate_messages'] > 0

    # Test 3: ClickHouse insertion working
    bars_in_db = clickhouse.execute("SELECT count() FROM live_aggregates WHERE ...")
    assert bars_in_db > 0

    # Test 4: Data integrity
    sample_bar = clickhouse.execute("SELECT * FROM live_aggregates LIMIT 1")
    assert sample_bar['symbol'] == expected_symbol
    assert sample_bar['time'] is not None

    return True

# 2. Run verification (SHOULD FAIL initially)
result = verify_pipeline_fix()  # ❌ FAIL - Expected behavior

# 3. Make fix

# 4. Run verification again
result = verify_pipeline_fix()  # ✅ PASS - Fix successful
```

**Benefits:**
- Clear success criteria before starting
- Prevents "looks like it works" false positives
- Creates regression test for future
- Forces understanding of expected behavior

---

## 🔧 **Phase 4: INCREMENTAL FIXES (ONE AT A TIME)**

### CRITICAL: Fix one thing, verify immediately

```
┌─────────────────────────────────────────────────────────┐
│ WORKFLOW:                                               │
├─────────────────────────────────────────────────────────┤
│ 1. Test Hypothesis #1 (highest likelihood)             │
│    ├─ Make MINIMAL change (1 file, 1 function)         │
│    ├─ Document what changed and why                    │
│    ├─ Rebuild/restart affected service ONLY            │
│    └─ Run verification immediately                     │
│                                                          │
│ 2. If PASS → Done. If FAIL → Revert and test next      │
│                                                          │
│ 3. Test Hypothesis #2                                  │
│    └─ Repeat process                                   │
└─────────────────────────────────────────────────────────┘
```

### Example (Correct Approach):

```bash
# Fix 1: Schema mismatch in duplicate check
Edit clickhouse_writer.py (change timestamp_ms → time)
Rebuild data-bridge ONLY
Test: Check logs for schema errors
Result: ✅ PASS - No more schema errors

# Fix 2: (Not needed - Fix 1 solved it)
```

### ANTI-PATTERNS (NEVER DO):

```
❌ Fix multiple files simultaneously
❌ Make "while I'm here" improvements
❌ Batch multiple changes before testing
❌ Assume fix worked without verification
❌ Add logging as "temporary" without removal plan
```

### CORRECT PATTERNS:

```
✅ Fix ONE file at a time
✅ Test immediately after each change
✅ Revert if fix doesn't work
✅ Document each change in git commit
✅ Remove debug code after issue resolved
```

---

## 📊 **Phase 5: ROOT CAUSE ANALYSIS**

### After successful fix, ask "Why did this happen?"

```
Fix Applied: Changed duplicate check to use 'time' field
    ↓
Symptom: Query failed with "Unknown expression identifier"
    ↓
Immediate Cause: Code used timestamp_ms, schema had time
    ↓
Root Cause: Schema migration happened, code not updated
    ↓
Prevention:
├─ Add integration test for schema compatibility
├─ Add schema version checking in startup
├─ Document schema changes in CHANGELOG
└─ Add pre-commit hook to check for hardcoded field names
```

**Template:**

```
ROOT CAUSE ANALYSIS:
├─ What broke? [Specific symptom]
├─ Why did it break? [Immediate cause]
├─ Why did that happen? [Ask "why" 3-5 times]
├─ What prevented catching this earlier?
└─ Prevention measures:
    ├─ Code change needed
    ├─ Test to add
    ├─ Documentation to update
    └─ Process improvement
```

---

## 🤖 **When to Use Specialized Agents**

For complex issues, delegate to specialized agents AFTER completing Phase 1-2:

```javascript
// ❌ WRONG: Delegate without mental model
Task("debugger", "Fix the pipeline", "debugger")

// ✅ CORRECT: Delegate with complete context
Task("error-detective", `
ARCHITECTURE:
${mental_model_diagram}

HYPOTHESES GENERATED:
1. Schema mismatch (HIGH likelihood)
   Evidence: ${evidence}
2. NATS routing issue (MEDIUM)
   Evidence: ${evidence}

TASK: Test hypothesis #1 systematically with verification
`, "error-detective")
```

**Agent Types:**
- `error-detective` - Log analysis, error correlation
- `tdd-orchestrator` - Test-first development
- `debugger` - General debugging (use with detailed context)
- `code-reviewer` - Pre-merge review
- `architect-review` - Architectural validation

---

## 📈 **Metrics for Success**

Track these to measure improvement:

```
Before Protocol:
├─ Time to fix: 3-4 hours (trial and error)
├─ False fixes: 3-5 attempts
├─ Regressions: 20% of fixes break something else
└─ Root cause found: 30%

After Protocol:
├─ Time to fix: 30-60 min (systematic)
├─ False fixes: 0-1 attempts
├─ Regressions: <5%
└─ Root cause found: 90%
```

---

## 🎯 **Quick Reference Checklist**

Before ANY coding session:

```
□ Phase 1: Built complete mental model (15-30 min)
□ Phase 2: Generated 3+ ranked hypotheses
□ Phase 3: Written verification test (fails initially)
□ Phase 4: Fixed ONE thing, verified immediately
□ Phase 5: Documented root cause and prevention
```

**Estimated Time Investment:**
- Protocol overhead: +30 minutes upfront
- Time saved: -2 to 3 hours of trial-and-error
- **Net savings: 1.5 to 2.5 hours per bug**

---

## 📚 **References**

Research papers (2025):
- "Multi-Agent Collaboration and Runtime Debugging for LLM Code Generation"
- "Test-Driven Development: Mental Models for Code Understanding"
- "The Debugging Mindset: Think Before Fixing"

Best practices:
- Incremental development with immediate verification
- Hypothesis-driven debugging
- Root cause analysis over symptom fixing

---

**Last Updated:** 2025-10-19
**Version:** 1.0
**Status:** MANDATORY for all debugging tasks
