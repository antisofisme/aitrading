# Hybrid Messaging Architecture: NATS + Kafka
## Multi-Tenant AI Trading System

**Version:** 1.0
**Status:** Architecture Design (Future Implementation)
**Author:** Suho Trading System
**Date:** 2025-01-10

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Architecture Decision](#architecture-decision)
4. [Domain Separation](#domain-separation)
5. [Message Flow Patterns](#message-flow-patterns)
6. [Implementation Guide](#implementation-guide)
7. [Multi-Tenant Design](#multi-tenant-design)
8. [Performance Characteristics](#performance-characteristics)
9. [Security & Compliance](#security--compliance)
10. [Migration Path](#migration-path)
11. [Appendix](#appendix)

---

## Executive Summary

### The Problem

Current single-tenant architecture uses **dual NATS+Kafka publishing** for market data, resulting in:
- ❌ **88% duplicate messages** (both systems receive same data)
- ❌ **High CPU overhead** for deduplication
- ❌ **No multi-tenant isolation** for user-specific data
- ❌ **Missing audit trail** for regulatory compliance

### The Solution

**Hybrid Architecture** that uses each messaging system for its strengths:

| System | Use Case | Key Benefit |
|--------|----------|-------------|
| **NATS** | Market data broadcast | <1ms latency, efficient 1-to-N |
| **Kafka** | User events & trades | Multi-tenant isolation, audit trail |

### Expected Benefits

- ✅ **87% reduction** in duplicate messages
- ✅ **10x faster** market data distribution (<1ms vs ~10ms)
- ✅ **Multi-tenant isolation** via Kafka partitioning
- ✅ **Regulatory compliance** via Kafka persistent audit trail
- ✅ **Event replay capability** for debugging and backtesting

---

## System Overview

### Current Architecture (Core System - Phase 1)

```
┌─────────────────────────────────────────────────┐
│         CURRENT: Market Data Only               │
└─────────────────────────────────────────────────┘

Polygon API
    ↓
Live Collector ──→ NATS ──→ Data Bridge
    ↓                           ↓
Historical     ──→ NATS ──→ TimescaleDB
                                ↓
                           ClickHouse
```

**Status:** ✅ Implemented
**Scope:** Single-tenant market data processing
**Performance:** ~40 msg/sec live, 50,000+ msg/sec historical

---

### Future Architecture (Multi-Tenant - Phase 2)

```
┌─────────────────────────────────────────────────────────────────┐
│              FUTURE: Multi-Tenant AI Trading                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ MARKET DATA DOMAIN (NATS) - Shared, Broadcast                  │
└─────────────────────────────────────────────────────────────────┘
  Polygon API → Live Collector → NATS (market.*)
                                    ↓
                        ┌───────────┼───────────┐
                        ↓           ↓           ↓
                   Dashboard    User Agent   Data Bridge
                   (WebSocket)  (All Users)  (Analytics)

  Subjects:
  - market.{symbol}.tick          (Live quotes)
  - market.{symbol}.{timeframe}   (OHLCV candles)
  - signals.{strategy}.{symbol}   (AI predictions)
  - indicators.{type}.{symbol}    (Technical indicators)


┌─────────────────────────────────────────────────────────────────┐
│ USER/TRADING DOMAIN (Kafka) - Isolated, Persistent             │
└─────────────────────────────────────────────────────────────────┘
  Web API → Kafka (user.commands) → Trading Engine
              ↓ (partition by user_id)
              ↓
  ┌───────────┼───────────┐
  ↓           ↓           ↓
Partition 0  Partition 1  Partition 2
(User1,4,7)  (User2,5,8)  (User3,6,9)
  ↓           ↓           ↓
MT5 Bridge → Kafka (user.trades) → Audit Service
                                  → Dashboard (per user)

  Topics:
  - user.auth           (Login, logout, sessions)
  - user.settings       (Account preferences, risk params)
  - user.commands       (Trading commands: buy, sell, close)
  - user.trades         (Trade executions, fills)
  - user.mt5_status     (Balance, equity, margin)
  - user.risk_alerts    (Stop-outs, margin calls)
  - user.transactions   (Deposits, withdrawals)
```

**Status:** 📋 Design Document
**Target:** Phase 2 (Post-MVP)
**Scope:** Multi-tenant with MT5 integration

---

## Architecture Decision

### Why Hybrid? (Not NATS-Only or Kafka-Only)

#### Option 1: NATS-Only ❌

**Pros:**
- ✅ Simple architecture
- ✅ Ultra-low latency (<1ms)
- ✅ Lightweight

**Cons:**
- ❌ No built-in multi-tenant isolation
- ❌ Ephemeral (no persistence for audit)
- ❌ No replay capability
- ❌ Manual partitioning required

**Verdict:** Good for market data, insufficient for user events

---

#### Option 2: Kafka-Only ❌

**Pros:**
- ✅ Built-in partitioning (multi-tenant)
- ✅ Persistent audit trail
- ✅ Event replay capability

**Cons:**
- ❌ Higher latency (~10ms vs <1ms)
- ❌ Disk I/O overhead for ephemeral data
- ❌ Inefficient for broadcast (N consumers = N copies)

**Verdict:** Good for user events, overkill for market data

---

#### Option 3: Hybrid (NATS + Kafka) ✅

**Pros:**
- ✅ Best latency for market data (NATS <1ms)
- ✅ Multi-tenant isolation for users (Kafka)
- ✅ Audit trail for compliance (Kafka)
- ✅ Efficient broadcast (NATS)
- ✅ Event replay for debugging (Kafka)

**Cons:**
- ⚠️ Two systems to maintain
- ⚠️ Medium complexity

**Verdict:** Optimal for multi-tenant trading platform ⭐

---

## Domain Separation

### NATS Domain: Market Data (Shared Resources)

**Characteristics:**
- **Ephemeral:** Data not needed after consumption
- **Broadcast:** Same data to all users
- **Time-sensitive:** <1ms latency critical
- **High volume:** Millions of messages/hour
- **Stateless:** No ordering guarantee needed

**Use Cases:**

| Use Case | Subject Pattern | Example |
|----------|-----------------|---------|
| Live forex quotes | `market.{symbol}.tick` | `market.EURUSD.tick` |
| OHLCV candles | `market.{symbol}.{tf}` | `market.EURUSD.5m` |
| AI trading signals | `signals.{strategy}.{symbol}` | `signals.scalping.EURUSD` |
| Technical indicators | `indicators.{type}.{symbol}` | `indicators.rsi.EURUSD` |
| Market alerts | `alerts.market.{type}` | `alerts.market.breakout` |
| System health | `system.health.{service}` | `system.health.data-bridge` |

**Message Example:**

```json
{
  "subject": "market.EURUSD.tick",
  "data": {
    "symbol": "EUR/USD",
    "bid": 1.0850,
    "ask": 1.0852,
    "timestamp": 1704931200000,
    "source": "polygon"
  }
}
```

**Subscriber Pattern:**

```python
# All users subscribe to same stream
await nats.subscribe("market.*.tick")          # All symbols
await nats.subscribe("market.EURUSD.*")        # All EURUSD data
await nats.subscribe("signals.scalping.*")     # All scalping signals
```

---

### Kafka Domain: User Events (Isolated Resources)

**Characteristics:**
- **Persistent:** Audit trail required
- **Isolated:** Per-user partitioning
- **Ordered:** Sequence guarantee per user
- **Replayable:** Debug & compliance
- **Stateful:** Event sourcing pattern

**Use Cases:**

| Use Case | Topic | Partition Key | Retention |
|----------|-------|---------------|-----------|
| User authentication | `user.auth` | `user_id` | 90 days |
| Account settings | `user.settings` | `user_id` | Infinite |
| Trading commands | `user.commands` | `user_id` | 7 years (compliance) |
| Trade executions | `user.trades` | `user_id` | 7 years (compliance) |
| MT5 account status | `user.mt5_status` | `user_id` | 30 days |
| Risk alerts | `user.risk_alerts` | `user_id` | 1 year |
| Transactions | `user.transactions` | `user_id` | 10 years |

**Message Example:**

```json
{
  "topic": "user.trades",
  "key": "user_12345",
  "partition": 3,
  "value": {
    "event_id": "evt_abc123",
    "event_type": "TRADE_EXECUTED",
    "user_id": "user_12345",
    "mt5_account": "87654321",
    "trade_id": "trd_xyz789",
    "symbol": "EURUSD",
    "action": "BUY",
    "volume": 0.10,
    "open_price": 1.0850,
    "timestamp": 1704931200000,
    "metadata": {
      "strategy": "scalping",
      "signal_id": "sig_456"
    }
  }
}
```

**Consumer Pattern:**

```python
# Kafka consumer group (parallel processing)
consumer = KafkaConsumer(
    topics=["user.trades", "user.commands"],
    group_id="trading-engine",
    enable_auto_commit=False,  # Manual commit for reliability
    auto_offset_reset="earliest"
)

for message in consumer:
    user_id = message.key.decode('utf-8')
    event = json.loads(message.value)

    # Process event for specific user
    await process_user_event(user_id, event)

    # Commit offset only after successful processing
    consumer.commit()
```

---

## Message Flow Patterns

### Pattern 1: Market Data Broadcast (NATS)

**Flow:**

```
Polygon API
    ↓
Live Collector (Publisher)
    ↓
    ├─→ NATS.publish("market.EURUSD.tick")
    ↓
NATS Server (In-memory broadcast)
    ↓
    ├─→ Subscriber 1: Dashboard (WebSocket)
    ├─→ Subscriber 2: Data Bridge (Analytics)
    ├─→ Subscriber 3: User Agent (All users)
    └─→ Subscriber N: Risk Monitor
```

**Code Example:**

```python
# Publisher: Live Collector
async def publish_tick(tick_data: dict):
    subject = f"market.{tick_data['symbol']}.tick"

    await nats.publish(
        subject=subject,
        payload=json.dumps(tick_data).encode()
    )

# Subscriber: Dashboard
async def dashboard_subscriber():
    async def message_handler(msg):
        tick = json.loads(msg.data.decode())
        await websocket.send_to_all_users(tick)

    await nats.subscribe("market.*.tick", cb=message_handler)

# Subscriber: Data Bridge (Analytics)
async def analytics_subscriber():
    async def message_handler(msg):
        tick = json.loads(msg.data.decode())
        await save_to_timescale(tick)
        await cache_latest(tick)

    await nats.subscribe("market.*.tick", cb=message_handler)
```

**Latency:** <1ms
**Throughput:** 100,000+ msg/sec
**Reliability:** Fire-and-forget (ephemeral)

---

### Pattern 2: User Event Processing (Kafka)

**Flow:**

```
User Action (Web/Mobile)
    ↓
Web API (Publisher)
    ↓
    └─→ Kafka.send(
            topic="user.commands",
            key=user_id,
            value=command
        )
    ↓
Kafka Broker (Persistent storage)
    ↓
    ├─→ Partition 0 (User1, User4, User7, ...)
    ├─→ Partition 1 (User2, User5, User8, ...)
    └─→ Partition 2 (User3, User6, User9, ...)
    ↓
Consumer Group: Trading Engine
    ↓
    ├─→ Consumer 1 → Process Partition 0
    ├─→ Consumer 2 → Process Partition 1
    └─→ Consumer 3 → Process Partition 2
    ↓
MT5 Execution
    ↓
    └─→ Kafka.send(
            topic="user.trades",
            key=user_id,
            value=result
        )
    ↓
Consumer Group: Audit Service (logs all trades)
Consumer Group: Notification Service (alerts user)
Consumer Group: Analytics Service (ML training)
```

**Code Example:**

```python
# Publisher: Web API
@app.post("/api/trade/open")
async def open_trade(user_id: str, order: TradeOrder):
    command = {
        "event_type": "OPEN_TRADE",
        "user_id": user_id,
        "mt5_account": get_user_mt5(user_id),
        "order": order.dict(),
        "timestamp": int(time.time() * 1000)
    }

    # Partition by user_id for ordering guarantee
    kafka_producer.send(
        topic="user.commands",
        key=user_id.encode(),
        value=json.dumps(command).encode()
    )

    return {"status": "queued", "command_id": command["event_id"]}

# Consumer: Trading Engine
class TradingEngineConsumer:
    def __init__(self):
        self.consumer = KafkaConsumer(
            "user.commands",
            bootstrap_servers="kafka:9092",
            group_id="trading-engine",
            enable_auto_commit=False,
            auto_offset_reset="earliest"
        )

    async def process_commands(self):
        for message in self.consumer:
            user_id = message.key.decode()
            command = json.loads(message.value.decode())

            try:
                # Get latest market price from NATS
                price = await self.get_market_price(command["order"]["symbol"])

                # Execute on MT5
                result = await mt5_bridge.execute_trade(
                    user_id=user_id,
                    order=command["order"],
                    price=price
                )

                # Log execution to Kafka (audit trail)
                kafka_producer.send(
                    topic="user.trades",
                    key=user_id.encode(),
                    value=json.dumps({
                        "event_type": "TRADE_EXECUTED",
                        "command_id": command["event_id"],
                        "trade_id": result.trade_id,
                        "execution_price": result.price,
                        "timestamp": int(time.time() * 1000)
                    }).encode()
                )

                # Commit offset only on success
                self.consumer.commit()

            except Exception as e:
                logger.error(f"Trade execution failed: {e}")
                # Don't commit - will retry on next poll

    async def get_market_price(self, symbol: str) -> float:
        # Request/reply pattern with NATS
        response = await nats.request(
            f"market.{symbol}.price",
            timeout=1.0
        )
        return json.loads(response.data)["bid"]
```

**Latency:** ~10ms
**Throughput:** 10,000+ msg/sec per partition
**Reliability:** At-least-once delivery with manual commit

---

### Pattern 3: Hybrid Dashboard Updates

**Flow:**

```
┌─────────────────────────────────────────┐
│ WebSocket Client (User Dashboard)      │
└─────────────────────────────────────────┘
         ↑ (multiplexed stream)
         │
┌────────┴─────────────────────────────┐
│ WebSocket Server (Backend)           │
│                                       │
│  ┌──────────────┐  ┌──────────────┐  │
│  │ NATS Stream  │  │ Kafka Stream │  │
│  │ (Market)     │  │ (User Data)  │  │
│  └──────┬───────┘  └──────┬───────┘  │
│         │                 │          │
│         ↓                 ↓          │
│   [Multiplexer]                      │
│         │                            │
└─────────┼────────────────────────────┘
          ↓
    User Dashboard
    ├─ Market Chart (NATS: market.EURUSD.tick)
    ├─ MT5 Balance  (Kafka: user.mt5_status)
    ├─ Open Trades  (Kafka: user.trades)
    └─ Signals      (NATS: signals.scalping.*)
```

**Code Example:**

```python
# WebSocket Server
class TradingWebSocketServer:
    def __init__(self):
        self.nats = None
        self.kafka_consumers = {}  # Per-user consumer

    async def handle_connection(self, websocket, user_id: str):
        """Handle WebSocket connection for a user"""

        # 1. Subscribe to NATS for market data (shared)
        nats_queue = asyncio.Queue()

        async def nats_handler(msg):
            await nats_queue.put({
                "source": "market",
                "data": json.loads(msg.data.decode())
            })

        # Subscribe to symbols user is watching
        user_symbols = get_user_watchlist(user_id)
        for symbol in user_symbols:
            await self.nats.subscribe(
                f"market.{symbol}.*",
                cb=nats_handler
            )

        # 2. Subscribe to Kafka for user-specific data
        kafka_queue = asyncio.Queue()

        kafka_consumer = KafkaConsumer(
            topics=["user.trades", "user.mt5_status", "user.risk_alerts"],
            group_id=f"websocket_{user_id}",
            bootstrap_servers="kafka:9092"
        )

        async def kafka_poll():
            for message in kafka_consumer:
                if message.key.decode() == user_id:
                    await kafka_queue.put({
                        "source": "user",
                        "data": json.loads(message.value.decode())
                    })

        # Start Kafka polling in background
        kafka_task = asyncio.create_task(kafka_poll())

        # 3. Multiplex both streams to WebSocket
        try:
            while True:
                # Wait for message from either queue
                done, pending = await asyncio.wait(
                    [
                        asyncio.create_task(nats_queue.get()),
                        asyncio.create_task(kafka_queue.get())
                    ],
                    return_when=asyncio.FIRST_COMPLETED
                )

                # Send to WebSocket
                for task in done:
                    message = task.result()
                    await websocket.send(json.dumps(message))

        except WebSocketDisconnect:
            logger.info(f"User {user_id} disconnected")
        finally:
            kafka_task.cancel()
            kafka_consumer.close()
```

**Benefits:**
- ✅ Real-time market updates (<1ms via NATS)
- ✅ User-specific data isolation (Kafka)
- ✅ Single WebSocket connection
- ✅ Automatic reconnection handling

---

## Implementation Guide

### Phase 1: Core System (Current - NATS Only)

**Status:** ✅ Implemented

**Scope:**
- Market data ingestion (Polygon API)
- Live data streaming (WebSocket → NATS)
- Historical data download (REST → NATS)
- Analytics storage (TimescaleDB + ClickHouse)

**Services:**
- `polygon-live-collector` → NATS publisher
- `polygon-historical-downloader` → NATS publisher
- `data-bridge` → NATS subscriber → Database writer

**No changes needed for Phase 1**

---

### Phase 2: Multi-Tenant Foundation (Kafka Integration)

**Target:** Q2 2025 (Post-MVP)

#### Step 1: Infrastructure Setup

**Add Kafka to docker-compose.yml:**

```yaml
services:
  # ... existing services (NATS, etc.)

  zookeeper:
    image: confluentinc/cp-zookeeper:7.7.0
    container_name: suho-zookeeper
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    networks:
      - suho-trading-network
    volumes:
      - zookeeper_data:/var/lib/zookeeper/data
      - zookeeper_logs:/var/lib/zookeeper/log

  kafka:
    image: confluentinc/cp-kafka:7.7.0
    container_name: suho-kafka
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://suho-kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_LOG_RETENTION_HOURS: 168  # 7 days default
      KAFKA_LOG_SEGMENT_BYTES: 1073741824  # 1GB
    networks:
      - suho-trading-network
    volumes:
      - kafka_data:/var/lib/kafka/data
    healthcheck:
      test: ["CMD", "kafka-broker-api-versions", "--bootstrap-server", "localhost:9092"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  zookeeper_data:
  zookeeper_logs:
  kafka_data:
```

#### Step 2: Create Kafka Topics

**Script: `scripts/setup_kafka_topics.sh`**

```bash
#!/bin/bash
# Create Kafka topics for user events

KAFKA_CONTAINER="suho-kafka"

# User domain topics
docker exec $KAFKA_CONTAINER kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic user.auth \
  --partitions 3 \
  --replication-factor 1 \
  --config retention.ms=7776000000  # 90 days

docker exec $KAFKA_CONTAINER kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic user.settings \
  --partitions 3 \
  --replication-factor 1 \
  --config retention.ms=-1  # Infinite (compacted)

docker exec $KAFKA_CONTAINER kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic user.commands \
  --partitions 6 \
  --replication-factor 1 \
  --config retention.ms=220903200000  # 7 years (compliance)

docker exec $KAFKA_CONTAINER kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic user.trades \
  --partitions 6 \
  --replication-factor 1 \
  --config retention.ms=220903200000  # 7 years (compliance)

docker exec $KAFKA_CONTAINER kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic user.mt5_status \
  --partitions 3 \
  --replication-factor 1 \
  --config retention.ms=2592000000  # 30 days

docker exec $KAFKA_CONTAINER kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --topic user.risk_alerts \
  --partitions 3 \
  --replication-factor 1 \
  --config retention.ms=31536000000  # 1 year

echo "✅ Kafka topics created successfully"
```

#### Step 3: Implement User Service (New)

**Service: `04-user-management/user-service/`**

```python
# user-service/src/main.py
"""
User Service - Handles user authentication, settings, and account management
Publishes events to Kafka for audit and downstream processing
"""
from fastapi import FastAPI, HTTPException, Depends
from kafka import KafkaProducer
import json
import time
from typing import Optional

app = FastAPI(title="User Service")

# Kafka producer
kafka_producer = KafkaProducer(
    bootstrap_servers=["suho-kafka:9092"],
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    key_serializer=lambda k: k.encode('utf-8'),
    acks='all',  # Wait for all replicas (reliability)
    retries=3
)

# User authentication
@app.post("/api/auth/login")
async def login(email: str, password: str):
    # Authenticate user (check database, verify password)
    user = authenticate_user(email, password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Publish auth event to Kafka
    auth_event = {
        "event_type": "USER_LOGIN",
        "user_id": user.id,
        "email": user.email,
        "timestamp": int(time.time() * 1000),
        "ip_address": request.client.host,
        "user_agent": request.headers.get("user-agent")
    }

    kafka_producer.send(
        topic="user.auth",
        key=user.id,
        value=auth_event
    )

    # Generate JWT token
    token = create_access_token(user.id)

    return {
        "access_token": token,
        "user_id": user.id,
        "email": user.email
    }

# User settings
@app.put("/api/user/{user_id}/settings")
async def update_settings(user_id: str, settings: dict):
    # Update database
    await db.users.update_one(
        {"_id": user_id},
        {"$set": {"settings": settings}}
    )

    # Publish settings change event
    settings_event = {
        "event_type": "SETTINGS_UPDATED",
        "user_id": user_id,
        "settings": settings,
        "timestamp": int(time.time() * 1000)
    }

    kafka_producer.send(
        topic="user.settings",
        key=user_id,
        value=settings_event
    )

    return {"status": "success"}

# User MT5 account linking
@app.post("/api/user/{user_id}/mt5/link")
async def link_mt5_account(user_id: str, mt5_account: str, password: str):
    # Verify MT5 account
    verified = await mt5_bridge.verify_account(mt5_account, password)

    if not verified:
        raise HTTPException(status_code=400, detail="Invalid MT5 credentials")

    # Store encrypted credentials
    await db.mt5_accounts.insert_one({
        "user_id": user_id,
        "account_number": mt5_account,
        "password": encrypt(password),
        "linked_at": datetime.utcnow()
    })

    # Publish event
    kafka_producer.send(
        topic="user.settings",
        key=user_id,
        value={
            "event_type": "MT5_ACCOUNT_LINKED",
            "user_id": user_id,
            "mt5_account": mt5_account,
            "timestamp": int(time.time() * 1000)
        }
    )

    return {"status": "linked"}
```

#### Step 4: Implement Trading Engine (New)

**Service: `05-trading-execution/trading-engine/`**

```python
# trading-engine/src/main.py
"""
Trading Engine - Processes user trading commands and executes on MT5
Consumes from Kafka (user.commands), publishes to Kafka (user.trades)
"""
import asyncio
from kafka import KafkaConsumer, KafkaProducer
import json
from nats.aio.client import Client as NATS

class TradingEngine:
    def __init__(self):
        # Kafka consumer (user commands)
        self.consumer = KafkaConsumer(
            "user.commands",
            bootstrap_servers=["suho-kafka:9092"],
            group_id="trading-engine",
            enable_auto_commit=False,  # Manual commit for reliability
            auto_offset_reset="earliest",
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            key_deserializer=lambda m: m.decode('utf-8')
        )

        # Kafka producer (trade results)
        self.producer = KafkaProducer(
            bootstrap_servers=["suho-kafka:9092"],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8'),
            acks='all'
        )

        # NATS client (market data)
        self.nats = NATS()

    async def start(self):
        # Connect to NATS
        await self.nats.connect(servers=["nats://suho-nats-server:4222"])

        # Start processing commands
        await self.process_commands()

    async def process_commands(self):
        """Process user trading commands"""
        for message in self.consumer:
            user_id = message.key
            command = message.value

            try:
                # Process command
                result = await self.execute_command(user_id, command)

                # Publish result
                self.producer.send(
                    topic="user.trades",
                    key=user_id,
                    value=result
                )

                # Commit offset only on success
                self.consumer.commit()

            except Exception as e:
                logger.error(f"Command execution failed: {e}")
                # Don't commit - will retry

    async def execute_command(self, user_id: str, command: dict):
        """Execute trading command"""
        command_type = command["event_type"]

        if command_type == "OPEN_TRADE":
            # Get latest market price from NATS
            price = await self.get_market_price(command["order"]["symbol"])

            # Execute on MT5
            result = await mt5_bridge.open_trade(
                account=command["mt5_account"],
                symbol=command["order"]["symbol"],
                volume=command["order"]["volume"],
                order_type=command["order"]["type"],
                price=price,
                stop_loss=command["order"].get("stop_loss"),
                take_profit=command["order"].get("take_profit")
            )

            return {
                "event_type": "TRADE_EXECUTED",
                "command_id": command["event_id"],
                "user_id": user_id,
                "trade_id": result.trade_id,
                "execution_price": result.price,
                "status": "SUCCESS",
                "timestamp": int(time.time() * 1000)
            }

        elif command_type == "CLOSE_TRADE":
            # Close trade on MT5
            result = await mt5_bridge.close_trade(
                account=command["mt5_account"],
                trade_id=command["trade_id"]
            )

            return {
                "event_type": "TRADE_CLOSED",
                "command_id": command["event_id"],
                "user_id": user_id,
                "trade_id": command["trade_id"],
                "close_price": result.close_price,
                "profit": result.profit,
                "status": "SUCCESS",
                "timestamp": int(time.time() * 1000)
            }

    async def get_market_price(self, symbol: str) -> float:
        """Get latest market price from NATS (request/reply)"""
        response = await self.nats.request(
            f"market.{symbol}.price",
            b"",
            timeout=1.0
        )
        price_data = json.loads(response.data.decode())
        return price_data["bid"]

# Run
if __name__ == "__main__":
    engine = TradingEngine()
    asyncio.run(engine.start())
```

#### Step 5: Keep NATS for Market Data (No Changes)

**Current services remain unchanged:**
- ✅ `polygon-live-collector` → NATS only (market data)
- ✅ `polygon-historical-downloader` → NATS only (market data)
- ✅ `data-bridge` → NATS subscriber (market data to DB)

**New behavior:**
- Trading Engine also subscribes to NATS for real-time prices
- Dashboard subscribes to both NATS (market) and Kafka (user data)

---

### Phase 3: Dashboard Integration

**Service: `06-web-dashboard/websocket-server/`**

```python
# websocket-server/src/main.py
"""
WebSocket Server - Provides real-time updates to dashboard
Multiplexes NATS (market data) and Kafka (user data) streams
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from kafka import KafkaConsumer
from nats.aio.client import Client as NATS
import asyncio
import json

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.nats = None
        self.kafka_consumers = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

        # Initialize NATS connection if needed
        if not self.nats:
            self.nats = NATS()
            await self.nats.connect(servers=["nats://suho-nats-server:4222"])

        # Start streaming for this user
        asyncio.create_task(self.stream_to_user(user_id))

    async def stream_to_user(self, user_id: str):
        """Stream both market data (NATS) and user data (Kafka) to WebSocket"""
        websocket = self.active_connections[user_id]

        # Queue for multiplexing
        message_queue = asyncio.Queue()

        # 1. NATS subscriber (market data)
        async def nats_handler(msg):
            await message_queue.put({
                "channel": "market",
                "data": json.loads(msg.data.decode())
            })

        # Subscribe to user's watchlist
        watchlist = get_user_watchlist(user_id)
        for symbol in watchlist:
            await self.nats.subscribe(f"market.{symbol}.*", cb=nats_handler)

        # 2. Kafka consumer (user data)
        kafka_consumer = KafkaConsumer(
            "user.trades",
            "user.mt5_status",
            "user.risk_alerts",
            bootstrap_servers=["suho-kafka:9092"],
            group_id=f"websocket_{user_id}",
            auto_offset_reset="latest"
        )

        async def kafka_poll():
            for message in kafka_consumer:
                if message.key.decode() == user_id:
                    await message_queue.put({
                        "channel": "user",
                        "topic": message.topic,
                        "data": json.loads(message.value.decode())
                    })

        kafka_task = asyncio.create_task(kafka_poll())

        # 3. Send messages to WebSocket
        try:
            while True:
                msg = await message_queue.get()
                await websocket.send_json(msg)
        except WebSocketDisconnect:
            kafka_task.cancel()
            kafka_consumer.close()
            del self.active_connections[user_id]

manager = ConnectionManager()

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
```

---

## Multi-Tenant Design

### Kafka Partitioning Strategy

**Key Principle:** Partition by `user_id` for isolation and ordering

```python
# Partitioning function (default: hash(key) % num_partitions)
partition = hash(user_id) % num_partitions

# Example with 6 partitions:
user_12345 → hash("user_12345") % 6 = 3 → Partition 3
user_67890 → hash("user_67890") % 6 = 1 → Partition 1
```

**Benefits:**
- ✅ All events for same user → same partition (ordering)
- ✅ Users evenly distributed across partitions (load balancing)
- ✅ Parallel processing (1 consumer per partition)
- ✅ Isolation (user data never mixed)

**Partition Configuration:**

| Topic | Partitions | Reason |
|-------|------------|--------|
| `user.auth` | 3 | Low volume |
| `user.settings` | 3 | Low volume |
| `user.commands` | 6 | High volume (trades) |
| `user.trades` | 6 | High volume (executions) |
| `user.mt5_status` | 3 | Medium volume |
| `user.risk_alerts` | 3 | Low volume |

**Scaling:**
- 100 users → 3-6 partitions sufficient
- 1,000 users → 12-24 partitions
- 10,000+ users → 24-48 partitions

---

### Consumer Group Strategy

**Pattern 1: Exclusive Consumer per User (WebSocket)**

```python
# Each WebSocket connection = separate consumer
group_id = f"websocket_{user_id}"

# User1 WebSocket → Consumer Group "websocket_user1"
# User2 WebSocket → Consumer Group "websocket_user2"
```

**Benefits:**
- ✅ Each user gets their own consumer
- ✅ No message loss on reconnect (offset committed)
- ✅ Multiple WebSocket connections can read same data

**Pattern 2: Shared Consumer Group (Trading Engine)**

```python
# All trading engine instances share same consumer group
group_id = "trading-engine"

# Trading Engine Instance 1 → Processes Partition 0, 1
# Trading Engine Instance 2 → Processes Partition 2, 3
# Trading Engine Instance 3 → Processes Partition 4, 5
```

**Benefits:**
- ✅ Parallel processing (horizontal scaling)
- ✅ Automatic rebalancing on instance failure
- ✅ Load distribution

---

### Data Isolation Guarantees

**Partition-level Isolation:**

```
┌─────────────────────────────────────┐
│ Topic: user.trades (6 partitions)   │
└─────────────────────────────────────┘

Partition 0: [user1, user4, user7]
Partition 1: [user2, user5, user8]
Partition 2: [user3, user6, user9]
Partition 3: [user10, user13]
Partition 4: [user11, user14]
Partition 5: [user12, user15]

✅ User1 data NEVER mixed with User2
✅ All User1 events in same partition (ordered)
✅ Consumer processes User1 events sequentially
```

**Consumer-level Filtering:**

```python
# Additional safety check (defense in depth)
for message in kafka_consumer:
    user_id = message.key.decode()

    # Verify user has permission to this data
    if not user_has_permission(current_user, user_id):
        logger.warning(f"Unauthorized access attempt: {current_user} → {user_id}")
        continue

    # Process event
    await process_event(user_id, message.value)
```

---

## Performance Characteristics

### NATS Performance

**Benchmarks (Single Server):**
- **Throughput:** 11 million msg/sec (8-byte payload)
- **Latency:** <1ms (median), <10ms (99th percentile)
- **Memory:** In-memory only (ephemeral)
- **CPU:** Minimal (<5% for 100k msg/sec)

**Real-world (Our System):**
- Current: ~40 msg/sec (live market data)
- Peak: 50,000 msg/sec (historical batch)
- Expected: 500 msg/sec (14 symbols × 30 ticks/sec avg)

**Capacity:** 20,000x headroom ✅

---

### Kafka Performance

**Benchmarks (3-broker cluster):**
- **Throughput:** 2 million msg/sec (100-byte payload)
- **Latency:** ~10ms (median), ~50ms (99th percentile)
- **Storage:** Persistent disk (configurable retention)
- **CPU:** Moderate (20-30% for 10k msg/sec)

**Real-world (Our System):**
- Expected: 100 trades/sec (peak)
- Expected: 1,000 user events/sec (all types)
- Storage: ~1GB/day (compressed)

**Capacity:** 1,000x headroom ✅

---

### Comparison Table

| Metric | NATS | Kafka | Winner |
|--------|------|-------|--------|
| **Latency** | <1ms | ~10ms | ✅ NATS |
| **Throughput** | 11M msg/sec | 2M msg/sec | ✅ NATS |
| **Persistence** | ❌ Ephemeral | ✅ Persistent | ✅ Kafka |
| **Ordering** | ❌ No guarantee | ✅ Per partition | ✅ Kafka |
| **Replay** | ❌ Not supported | ✅ Full replay | ✅ Kafka |
| **Multi-tenant** | ⚠️ Manual | ✅ Built-in | ✅ Kafka |
| **Complexity** | Low | Medium | ✅ NATS |
| **Resource usage** | Low | Medium | ✅ NATS |

---

## Security & Compliance

### Authentication & Authorization

**NATS Security:**

```yaml
# nats-server.conf
authorization {
  # Service-to-service auth
  users = [
    {
      user: "live-collector"
      password: $NATS_LIVE_COLLECTOR_PASSWORD
      permissions {
        publish = ["market.>", "signals.>"]
        subscribe = []
      }
    },
    {
      user: "data-bridge"
      password: $NATS_DATA_BRIDGE_PASSWORD
      permissions {
        publish = []
        subscribe = ["market.>", "signals.>"]
      }
    },
    {
      user: "dashboard"
      password: $NATS_DASHBOARD_PASSWORD
      permissions {
        publish = []
        subscribe = ["market.>", "signals.>", "indicators.>"]
      }
    }
  ]
}
```

**Kafka Security (SASL/SCRAM):**

```yaml
# kafka server.properties
listeners=SASL_PLAINTEXT://0.0.0.0:9092
security.inter.broker.protocol=SASL_PLAINTEXT
sasl.mechanism.inter.broker.protocol=SCRAM-SHA-512
sasl.enabled.mechanisms=SCRAM-SHA-512

# ACLs (Access Control Lists)
# User Service can publish to user.* topics
kafka-acls --add \
  --allow-principal User:user-service \
  --operation Write \
  --topic user.auth,user.settings

# Trading Engine can read user.commands, write user.trades
kafka-acls --add \
  --allow-principal User:trading-engine \
  --operation Read \
  --topic user.commands

kafka-acls --add \
  --allow-principal User:trading-engine \
  --operation Write \
  --topic user.trades
```

---

### Audit Trail & Compliance

**Regulatory Requirements:**

| Regulation | Requirement | Kafka Solution |
|------------|-------------|----------------|
| **MiFID II** | Trade reporting (7 years) | `user.trades` retention = 7 years |
| **FINRA 4511** | Preserve all communications | All topics logged to Kafka |
| **GDPR** | Right to be forgotten | User-specific partition deletion |
| **SOX** | Financial transaction audit | Immutable log (no deletion) |

**Kafka Configuration for Compliance:**

```python
# Topic: user.trades (compliance)
kafka-configs --alter --topic user.trades \
  --add-config retention.ms=220903200000  # 7 years
  --add-config min.compaction.lag.ms=86400000  # 1 day (prevent immediate deletion)
  --add-config segment.ms=86400000  # 1 day segments

# Enable audit logging
kafka-configs --alter --topic user.trades \
  --add-config unclean.leader.election.enable=false  # Prevent data loss
  --add-config min.insync.replicas=2  # Require 2 replicas for ack
```

**Audit Query Example:**

```python
# Retrieve all trades for user (compliance investigation)
def get_user_trade_history(user_id: str, from_date: datetime, to_date: datetime):
    consumer = KafkaConsumer(
        "user.trades",
        bootstrap_servers=["kafka:9092"],
        auto_offset_reset="earliest",  # Read from beginning
        enable_auto_commit=False
    )

    # Seek to timestamp
    partitions = consumer.partitions_for_topic("user.trades")
    for partition in partitions:
        tp = TopicPartition("user.trades", partition)
        offset = consumer.offsets_for_times({
            tp: int(from_date.timestamp() * 1000)
        })[tp].offset
        consumer.seek(tp, offset)

    # Collect all trades for user
    trades = []
    for message in consumer:
        if message.key.decode() == user_id:
            trade = json.loads(message.value.decode())
            if trade["timestamp"] > int(to_date.timestamp() * 1000):
                break
            trades.append(trade)

    return trades
```

---

### Data Encryption

**In-Transit Encryption (TLS):**

```yaml
# NATS TLS
nats-server --tls \
  --tlscert=/certs/server-cert.pem \
  --tlskey=/certs/server-key.pem \
  --tlscacert=/certs/ca-cert.pem

# Kafka TLS
listeners=SSL://0.0.0.0:9093
ssl.keystore.location=/certs/kafka.keystore.jks
ssl.keystore.password=$KEYSTORE_PASSWORD
ssl.key.password=$KEY_PASSWORD
ssl.truststore.location=/certs/kafka.truststore.jks
ssl.truststore.password=$TRUSTSTORE_PASSWORD
```

**At-Rest Encryption (Kafka):**

```bash
# Linux disk encryption (LUKS)
cryptsetup luksFormat /dev/sdb
cryptsetup open /dev/sdb kafka_encrypted
mkfs.ext4 /dev/mapper/kafka_encrypted
mount /dev/mapper/kafka_encrypted /var/lib/kafka
```

---

## Migration Path

### Current State → Hybrid Architecture

**Phase 1: Preparation (Week 1-2)**

1. ✅ Add Kafka + Zookeeper to docker-compose
2. ✅ Create Kafka topics (script provided)
3. ✅ Test Kafka connectivity (produce/consume)
4. ✅ Document current NATS usage (baseline)

**Phase 2: User Domain (Week 3-6)**

1. ✅ Implement User Service (auth, settings)
2. ✅ Publish user events to Kafka
3. ✅ Implement audit consumer (log all events)
4. ✅ Test multi-tenant isolation
5. ✅ Verify Kafka retention policies

**Phase 3: Trading Domain (Week 7-10)**

1. ✅ Implement Trading Engine (command processor)
2. ✅ Integrate MT5 Bridge
3. ✅ Publish trade executions to Kafka
4. ✅ Test order flow (command → execution → audit)
5. ✅ Load testing (1000+ concurrent trades)

**Phase 4: Dashboard Integration (Week 11-12)**

1. ✅ Implement WebSocket server (hybrid streams)
2. ✅ Multiplex NATS (market) + Kafka (user)
3. ✅ Test real-time updates
4. ✅ Performance tuning (WebSocket connections)

**Phase 5: Production Rollout (Week 13-14)**

1. ✅ Deploy to staging environment
2. ✅ Run regression tests (full system)
3. ✅ Canary deployment (10% users)
4. ✅ Monitor metrics (latency, throughput, errors)
5. ✅ Full production rollout

---

### Rollback Plan

**If issues occur during migration:**

**Option 1: Quick Rollback (disable Kafka)**

```bash
# Stop Kafka services
docker stop suho-kafka suho-zookeeper

# Revert to NATS-only mode
# User Service → fallback to database polling
# Trading Engine → fallback to REST API
```

**Option 2: Gradual Rollback (feature flag)**

```python
# Feature flag in config
USE_KAFKA = os.getenv("ENABLE_KAFKA", "false") == "true"

if USE_KAFKA:
    await kafka_producer.send(topic, message)
else:
    # Legacy path (NATS or database)
    await nats.publish(subject, message)
```

**Option 3: Dual-Write (temporary safety)**

```python
# Write to both during transition
await kafka_producer.send("user.trades", message)
await legacy_database.insert_trade(message)

# Remove legacy path after validation period
```

---

## Appendix

### A. Topic Naming Conventions

**Format:** `{domain}.{entity}.{action}`

**Examples:**
- `market.EURUSD.tick` (domain=market, entity=EURUSD, action=tick)
- `user.commands` (domain=user, entity=commands)
- `user.trades` (domain=user, entity=trades)
- `signals.scalping.EURUSD` (domain=signals, entity=scalping, action=EURUSD)

---

### B. Message Schema Examples

**Market Tick (NATS):**

```json
{
  "symbol": "EUR/USD",
  "bid": 1.0850,
  "ask": 1.0852,
  "mid": 1.0851,
  "spread": 0.0002,
  "timestamp": 1704931200000,
  "source": "polygon"
}
```

**User Trade Command (Kafka):**

```json
{
  "event_id": "cmd_abc123",
  "event_type": "OPEN_TRADE",
  "user_id": "user_12345",
  "mt5_account": "87654321",
  "order": {
    "symbol": "EURUSD",
    "type": "BUY",
    "volume": 0.10,
    "stop_loss": 1.0820,
    "take_profit": 1.0880
  },
  "timestamp": 1704931200000,
  "metadata": {
    "strategy": "scalping",
    "signal_id": "sig_xyz789"
  }
}
```

**Trade Execution Result (Kafka):**

```json
{
  "event_id": "exec_def456",
  "event_type": "TRADE_EXECUTED",
  "command_id": "cmd_abc123",
  "user_id": "user_12345",
  "mt5_account": "87654321",
  "trade_id": "trd_ghi789",
  "symbol": "EURUSD",
  "volume": 0.10,
  "execution_price": 1.0851,
  "stop_loss": 1.0820,
  "take_profit": 1.0880,
  "status": "SUCCESS",
  "timestamp": 1704931200500,
  "latency_ms": 500
}
```

---

### C. Monitoring & Metrics

**NATS Metrics:**

```bash
# NATS monitoring endpoint
curl http://localhost:8222/varz

# Key metrics:
- in_msgs: Messages received
- out_msgs: Messages sent
- in_bytes: Bandwidth in
- out_bytes: Bandwidth out
- connections: Active connections
- subscriptions: Total subscriptions
```

**Kafka Metrics (JMX):**

```bash
# Kafka JMX metrics
kafka-run-class kafka.tools.JmxTool \
  --object-name kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec

# Key metrics:
- MessagesInPerSec: Incoming message rate
- BytesInPerSec: Incoming bandwidth
- BytesOutPerSec: Outgoing bandwidth
- FailedProduceRequestsPerSec: Producer failures
- UnderReplicatedPartitions: Replication health
```

**Custom Application Metrics:**

```python
from prometheus_client import Counter, Histogram

# NATS metrics
nats_messages_published = Counter(
    "nats_messages_published_total",
    "Total NATS messages published",
    ["subject"]
)

nats_publish_latency = Histogram(
    "nats_publish_latency_seconds",
    "NATS publish latency",
    ["subject"]
)

# Kafka metrics
kafka_messages_produced = Counter(
    "kafka_messages_produced_total",
    "Total Kafka messages produced",
    ["topic"]
)

kafka_messages_consumed = Counter(
    "kafka_messages_consumed_total",
    "Total Kafka messages consumed",
    ["topic", "consumer_group"]
)

kafka_consumer_lag = Gauge(
    "kafka_consumer_lag",
    "Kafka consumer lag",
    ["topic", "partition", "consumer_group"]
)
```

---

### D. Cost Estimation (AWS)

**NATS (Lightweight):**
- EC2 t3.medium (2 vCPU, 4GB RAM): $30/month
- No storage cost (in-memory)
- **Total: ~$30/month**

**Kafka (Heavier):**
- 3x EC2 m5.large (2 vCPU, 8GB RAM each): $300/month
- EBS storage (1TB): $100/month
- **Total: ~$400/month**

**Hybrid Total: ~$430/month**

**Alternative (Managed Services):**
- AWS MSK (Kafka): $300-500/month (2 brokers)
- NATS on EC2: $30/month
- **Total: ~$330-530/month**

**Self-hosted (Current):**
- Single server (both NATS+Kafka): $50/month
- **Development/staging recommended**

---

### E. References

**NATS Documentation:**
- Official Docs: https://docs.nats.io/
- Performance: https://nats.io/blog/nats-server-2.10-performance/
- Security: https://docs.nats.io/running-a-nats-service/configuration/securing_nats

**Kafka Documentation:**
- Official Docs: https://kafka.apache.org/documentation/
- Multi-tenancy: https://www.confluent.io/blog/multi-tenant-kafka-best-practices/
- Security: https://kafka.apache.org/documentation/#security

**Best Practices:**
- Event-Driven Microservices: https://microservices.io/patterns/data/event-driven-architecture.html
- CQRS Pattern: https://martinfowler.com/bliki/CQRS.html
- Trading System Architecture: https://www.quantstart.com/articles/event-driven-backtesting-with-python/

---

## Glossary

**NATS:** Neural Autonomic Transport System - lightweight message broker
**Kafka:** Distributed event streaming platform
**Multi-tenant:** Single system instance serving multiple independent users
**Partition:** Kafka's unit of parallelism and ordering
**Consumer Group:** Set of consumers sharing workload
**Event Sourcing:** Storing state changes as sequence of events
**CQRS:** Command Query Responsibility Segregation
**MT5:** MetaTrader 5 (trading platform)
**Audit Trail:** Chronological record of system activities
**Compliance:** Adherence to regulatory requirements

---

**Document Status:** ✅ Architecture Design Complete
**Next Step:** Await Phase 1 (Core System) completion before implementation
**Review Cycle:** Quarterly (or when requirements change)

---

*This document serves as the architectural blueprint for transitioning from single-tenant market data processing to a multi-tenant AI trading platform with proper message isolation, audit capabilities, and regulatory compliance.*
