# Skill: inference-service Service

## Purpose
Real-time prediction service. Loads trained models/agents and generates trading signals from live ml_features.

## Key Facts
- **Phase**: Live Trading (Phase 3)
- **Status**: ⚠️ To Implement
- **Priority**: P2 (High - core trading capability)
- **Latency**: < 100ms per prediction (real-time requirement)
- **Models**: Loads from model_checkpoints or agent_checkpoints

## Data Flow
```
NATS: features.> (subscribe real-time)
ClickHouse.ml_features (latest candle fallback)
ClickHouse.model_checkpoints (load trained models)
  → inference-service (generate predictions/actions)
  → ClickHouse.trading_signals
  → ClickHouse.model_predictions (debug)
  → NATS: signals.{symbol} (real-time signals)
  → Kafka: trading_signals_archive (audit trail)
```

## Messaging
- **NATS Subscribe**: `features.>` (all feature streams from feature-engineering)
- **NATS Publish**: `signals.EURUSD`, `signals.XAUUSD`, etc. (trading signals)
- **Kafka Publish**: `trading_signals_archive` (compliance, audit)
- **Pattern**: Both NATS + Kafka (critical trading data needs real-time + audit)

## Dependencies
- **Upstream**:
  - feature-engineering-service (real-time features via NATS)
  - supervised-training-service OR finrl-training-service (trained models/agents)
- **Downstream**: risk-management (consumes signals via NATS)
- **Infrastructure**: ClickHouse, NATS cluster, Kafka

## Critical Rules
1. **NEVER** use historical features (live inference needs live data only!)
2. **ALWAYS** publish to both NATS + Kafka (audit trail mandatory)
3. **VERIFY** model loaded correctly (check checkpoint metadata)
4. **ENSURE** latency < 100ms (trading window is critical)
5. **VALIDATE** signal format before publishing (symbol, type, confidence, price levels)

## Signal Types
- **buy**: Open long position
- **sell**: Open short position
- **hold**: Do nothing
- **close_long**: Close existing long
- **close_short**: Close existing short

## Signal Fields
- signal_id (UUID)
- symbol, timeframe, timestamp
- signal_type (buy/sell/hold/close)
- confidence_score (0-1)
- entry_price, stop_loss, take_profit
- position_size_recommended

## Validation
When working on this service, ALWAYS verify:
- [ ] NATS subscribes to `features.>` (real-time features)
- [ ] Model/agent loaded successfully (check logs)
- [ ] Signals published to NATS `signals.*` (risk-management receives)
- [ ] Kafka archives to `trading_signals_archive`
- [ ] Latency < 100ms (measure time from feature → signal)

## Reference Docs

**Service Documentation:**
- Planning guide: `PLANNING_SKILL_GUIDE.md` (Service 10, lines 1452-1650)
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 544-576)
- Flow + messaging: `SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 472-525)
- Database schema: `table_database_trading.md` (trading_signals table)

**Operational Skills (Central-Hub Agent Tools):**
- 🔍 Debug issues: `.claude/skills/central-hub-debugger/`
- 🔧 Fix problems: `.claude/skills/central-hub-fixer/`
- ➕ Create new service: `.claude/skills/central-hub-service-creator/`
