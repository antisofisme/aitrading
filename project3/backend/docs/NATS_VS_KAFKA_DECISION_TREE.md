# NATS vs Kafka Decision Tree
## Quick Reference Guide for Message System Selection

**Purpose:** Help developers choose the right messaging system for each use case

---

## 🎯 Quick Decision Flowchart

```
START: Need to send message
    ↓
    ├─ Is this MARKET DATA? (shared by all users)
    │   ↓ YES
    │   ├─ Is real-time critical? (<1ms latency)
    │   │   ↓ YES → ✅ USE NATS
    │   │   ↓ NO  → ⚠️ Could use either, prefer NATS (simpler)
    │   │
    │   └─ Examples:
    │       - Live forex quotes ✅ NATS
    │       - OHLCV candles ✅ NATS
    │       - AI signals ✅ NATS
    │       - Technical indicators ✅ NATS
    │
    └─ Is this USER-SPECIFIC DATA?
        ↓ YES
        ├─ Does it need to be PERSISTENT? (audit/compliance)
        │   ↓ YES
        │   ├─ Do you need to REPLAY events? (debugging/backtesting)
        │   │   ↓ YES → ✅ USE KAFKA
        │   │   ↓ NO  → ✅ USE KAFKA (audit still needs persistence)
        │   │
        │   └─ Examples:
        │       - User trades ✅ KAFKA (7 years retention)
        │       - Account settings ✅ KAFKA (event sourcing)
        │       - MT5 status ✅ KAFKA (user state)
        │       - Trading commands ✅ KAFKA (audit trail)
        │
        └─ Is data EPHEMERAL? (no persistence needed)
            ↓ YES → ✅ USE NATS
            │
            └─ Examples:
                - Typing indicators ✅ NATS
                - Presence updates ✅ NATS
                - Temporary notifications ✅ NATS
```

---

## 📊 Comparison Matrix

| Criteria | NATS ✅ | Kafka ✅ |
|----------|---------|----------|
| **Latency** | <1ms | ~10ms |
| **Persistence** | ❌ Ephemeral | ✅ Persistent (disk) |
| **Ordering** | ❌ No guarantee | ✅ Per partition |
| **Multi-tenant** | ⚠️ Manual | ✅ Built-in partitioning |
| **Replay** | ❌ No | ✅ Full replay |
| **Broadcast** | ✅ Efficient (1→N) | ⚠️ Inefficient (N copies) |
| **Complexity** | ✅ Low | ⚠️ Medium |
| **Resource usage** | ✅ Low (memory) | ⚠️ Medium (disk + CPU) |
| **Audit trail** | ❌ No | ✅ Yes |
| **Compliance** | ❌ Not suitable | ✅ Suitable (7yr retention) |

---

## 🏗️ Use Case Breakdown

### ✅ NATS Use Cases

**Domain: Market Data (Shared)**

| Use Case | Subject Pattern | Why NATS? |
|----------|-----------------|-----------|
| Live forex quotes | `market.{symbol}.tick` | ⚡ <1ms latency critical |
| OHLCV candles | `market.{symbol}.{tf}` | ⚡ Real-time charts |
| AI trading signals | `signals.{strategy}.{symbol}` | ⚡ Low latency for entry |
| Technical indicators | `indicators.{type}.{symbol}` | 📊 Calculated on-the-fly |
| Market alerts | `alerts.market.{type}` | 📢 Broadcast to all |
| System health | `system.health.{service}` | 🔍 Monitoring |
| Price alerts | `alerts.price.{symbol}` | 🔔 User-subscribed |

**Characteristics:**
- 📡 Broadcast (1 message → N subscribers)
- ⚡ Ultra-low latency (<1ms)
- 💨 Ephemeral (no disk storage)
- 🔄 Fire-and-forget

**Code Pattern:**
```python
# Publisher
await nats.publish("market.EURUSD.tick", tick_data)

# All subscribers receive same message (efficient broadcast)
await nats.subscribe("market.*.tick")  # All symbols
```

---

### ✅ Kafka Use Cases

**Domain: User Events (Isolated)**

| Use Case | Topic | Partition Key | Retention | Why Kafka? |
|----------|-------|---------------|-----------|------------|
| User login/logout | `user.auth` | `user_id` | 90 days | 📋 Audit trail |
| Account settings | `user.settings` | `user_id` | Infinite | 🔄 Event sourcing |
| Trading commands | `user.commands` | `user_id` | 7 years | ⚖️ Compliance |
| Trade executions | `user.trades` | `user_id` | 7 years | ⚖️ Compliance |
| MT5 account status | `user.mt5_status` | `user_id` | 30 days | 💾 User state |
| Risk alerts | `user.risk_alerts` | `user_id` | 1 year | 🚨 History needed |
| Transactions | `user.transactions` | `user_id` | 10 years | 💰 Financial audit |

**Characteristics:**
- 🔒 Isolation (partition per user)
- 💾 Persistent (disk storage)
- 📜 Ordered (sequence per partition)
- 🔁 Replayable (debugging/backtest)
- ⚖️ Compliant (regulatory)

**Code Pattern:**
```python
# Publisher
kafka.send(
    topic="user.trades",
    key=user_id,        # Partition by user
    value=trade_data
)

# Consumer (parallel processing per partition)
consumer = KafkaConsumer(
    "user.trades",
    group_id="audit-service",
    enable_auto_commit=False  # Manual commit for reliability
)
```

---

## 🎓 Real-World Scenarios

### Scenario 1: User Opens Trade

**Question:** Where does each step go?

```
User clicks BUY button on dashboard
    ↓
1. Dashboard → Web API
   Data: { user_id, symbol, volume, type }
   Decision: ✅ KAFKA (user.commands)
   Why: User command needs audit trail (compliance)
   ↓
2. Trading Engine reads command
   Source: ✅ KAFKA (user.commands)
   Why: Persistent, ordered per user
   ↓
3. Trading Engine gets current price
   Source: ✅ NATS (market.EURUSD.price)
   Why: Real-time, low latency critical
   ↓
4. Trading Engine executes on MT5
   Log: ✅ KAFKA (user.trades)
   Why: Trade execution needs 7-year retention
   ↓
5. Dashboard receives update
   Source: ✅ KAFKA (user.trades)
   Why: User-specific data, needs to survive refresh
```

---

### Scenario 2: Display Market Chart

**Question:** How to stream live prices to chart?

```
User opens EUR/USD chart
    ↓
1. Dashboard subscribes to live ticks
   Source: ✅ NATS (market.EURUSD.tick)
   Why: Real-time updates (<1ms), broadcast to all users
   ↓
2. Dashboard subscribes to 1-minute candles
   Source: ✅ NATS (market.EURUSD.1m)
   Why: Real-time candle updates, shared data
   ↓
3. Dashboard loads historical candles (initial)
   Source: 🗄️ Database (ClickHouse)
   Why: Historical data, query API not streaming
   ↓
4. Chart updates in real-time
   Stream: ✅ NATS (WebSocket ← NATS)
   Why: Low latency, ephemeral updates
```

---

### Scenario 3: AI Signal Distribution

**Question:** How to send AI prediction to all users?

```
AI Engine generates trading signal
    ↓
1. AI Engine publishes signal
   Target: ✅ NATS (signals.scalping.EURUSD)
   Why: Broadcast to all users, low latency
   ↓
2. All users' trading agents receive signal
   Source: ✅ NATS (signals.scalping.*)
   Why: Same signal → all users (efficient broadcast)
   ↓
3. Each user's agent decides to trade
   Decision logic: Local (per-user settings)
   ↓
4. User agent sends trade command
   Target: ✅ KAFKA (user.commands)
   Why: User-specific action, needs audit
   ↓
5. Trading Engine processes each user's command
   Source: ✅ KAFKA (user.commands, partitioned)
   Why: Parallel processing, ordered per user
```

**Key Insight:**
- Signal distribution (1→N): NATS ✅
- Individual user actions (N separate): Kafka ✅

---

### Scenario 4: User Subscription Management

**Question:** User changes strategy settings?

```
User updates trading strategy settings
    ↓
1. Dashboard → Web API
   Data: { user_id, strategy: "scalping", risk: "low" }
   Decision: ✅ KAFKA (user.settings)
   Why: Event sourcing (rebuild user state from events)
   ↓
2. Settings Service updates database
   Source: ✅ KAFKA (user.settings consumer)
   Why: Persistent, ordered state changes
   ↓
3. Notify trading agent of settings change
   How: Query latest settings from database
   (Not via NATS - settings are not ephemeral!)
   ↓
4. Trading Agent applies new settings
   Source: Database (latest user settings)
   Why: Settings need to survive restarts
```

**Anti-pattern ❌:**
```python
# DON'T use NATS for settings
await nats.publish("user.settings.update", settings)
# Problem: Lost on restart! No persistence!
```

---

## 🚫 Common Anti-Patterns

### ❌ Anti-Pattern 1: User Data on NATS

**Wrong:**
```python
# User trade result on NATS
await nats.publish("user.trades.user123", trade_result)
```

**Problems:**
- ❌ Lost if consumer offline
- ❌ No audit trail
- ❌ Can't replay for debugging
- ❌ No compliance

**Correct:**
```python
# User trade result on Kafka
kafka.send(
    topic="user.trades",
    key="user123",
    value=trade_result
)
```

---

### ❌ Anti-Pattern 2: Market Data on Kafka

**Wrong:**
```python
# Live market tick on Kafka
kafka.send(
    topic="market.ticks",
    value=tick_data
)
```

**Problems:**
- ❌ 10x higher latency (~10ms vs <1ms)
- ❌ Disk I/O overhead (ephemeral data!)
- ❌ Inefficient broadcast (N consumers = N copies)

**Correct:**
```python
# Live market tick on NATS
await nats.publish("market.EURUSD.tick", tick_data)
```

---

### ❌ Anti-Pattern 3: Dual-Publish Same Data

**Wrong:**
```python
# Publish to BOTH (current problem!)
await nats.publish("market.tick", tick_data)
kafka.send("market_archive", tick_data)  # 88% duplicate!
```

**Problems:**
- ❌ 88% duplicate processing
- ❌ 2x bandwidth
- ❌ 2x CPU for deduplication

**Correct:**
```python
# Market data → NATS only
await nats.publish("market.EURUSD.tick", tick_data)

# Database handles persistence (not Kafka)
data_bridge_subscriber.save_to_database(tick_data)
```

---

## 📋 Checklist: Which System?

**Use NATS if ALL are true:**
- [ ] Data is **shared** by multiple consumers (broadcast)
- [ ] **Real-time** latency is critical (<1ms)
- [ ] Data is **ephemeral** (not needed after consumption)
- [ ] **No audit trail** required
- [ ] **No replay** needed

**Use Kafka if ANY are true:**
- [ ] Data is **user-specific** (needs isolation)
- [ ] **Persistence** required (audit/compliance)
- [ ] **Ordering** guarantee needed per user
- [ ] **Replay capability** needed (debugging/backtesting)
- [ ] **Regulatory compliance** (financial data)
- [ ] **Event sourcing** pattern (rebuild state from events)

**Use BOTH (Hybrid) if:**
- [ ] System has **market data** (NATS) AND **user events** (Kafka)
- [ ] Need **best of both** (low latency + compliance)
- [ ] Multi-tenant platform (different data types)

---

## 🎯 Summary Decision Table

| Data Type | System | Reason |
|-----------|--------|--------|
| **Market Data** |
| Live forex quotes | NATS | Broadcast, <1ms latency |
| OHLCV candles | NATS | Real-time, ephemeral |
| AI signals | NATS | Low latency, broadcast |
| Technical indicators | NATS | Calculated on-the-fly |
| **User Events** |
| Login/logout | Kafka | Audit trail |
| Account settings | Kafka | Event sourcing |
| Trading commands | Kafka | Compliance (7yr) |
| Trade executions | Kafka | Compliance (7yr) |
| MT5 status | Kafka | User state |
| Risk alerts | Kafka | History needed |
| Transactions | Kafka | Financial audit |
| **System Events** |
| Health checks | NATS | Ephemeral, monitoring |
| Service discovery | NATS | Real-time, lightweight |
| Logs (structured) | Kafka | Audit, analysis |

---

## 🔑 Key Takeaways

1. **NATS = Speed + Broadcast**
   - Use for market data (shared, real-time)
   - No persistence needed

2. **Kafka = Isolation + Compliance**
   - Use for user events (isolated, persistent)
   - Regulatory requirements

3. **Hybrid = Best of Both**
   - Market data → NATS (fast)
   - User data → Kafka (compliant)
   - Don't duplicate between systems!

4. **When in Doubt:**
   - Ask: "Does this need to survive a restart?" → Kafka
   - Ask: "Is <1ms latency critical?" → NATS
   - Ask: "Is this user-specific?" → Kafka
   - Ask: "Is this broadcast to all?" → NATS

---

**Document Version:** 1.0
**Last Updated:** 2025-01-10
**Next Review:** After Phase 1 completion

---

*This decision tree serves as a quick reference for developers building the multi-tenant AI trading platform. When implementing new features, consult this guide to choose the appropriate messaging system.*
