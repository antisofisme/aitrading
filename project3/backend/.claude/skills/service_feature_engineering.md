# Skill: feature-engineering-service Service

## Purpose
Calculate 110 ML features from candles + external data. Powers both training (historical) and inference (live).

## Key Facts
- **Phase**: Data Foundation (Phase 1)
- **Status**: ✅ Active, Production
- **Priority**: P0 (Critical - training and inference depend on this)
- **Features**: 110 derived features (NO raw OHLC stored)
- **Mode**: Both historical (with targets) + live (no targets)

## Data Flow
```
NATS: bars.> (subscribe real-time) + ClickHouse.aggregates (read)
  + ClickHouse.external_* (economic calendar, FRED, commodities)
  → feature-engineering-service (calculate 110 features)
  → ClickHouse.ml_features (110 derived features ONLY)
  → NATS: features.{symbol}.{timeframe} (real-time)
  → Kafka: ml_features_archive (optional)
```

## Messaging
- **NATS Subscribe**: `bars.>` (all candles from tick-aggregator)
- **NATS Publish**: `features.EURUSD.5m`, `features.XAUUSD.1h`, etc.
- **Kafka Publish**: `ml_features_archive` (optional, for training replay)
- **Pattern**: NATS primary, Kafka optional (features derived from archived candles)

## Dependencies
- **Upstream**:
  - tick-aggregator (candles via NATS `bars.*`)
  - external-data-collector (economic data, FRED, commodities)
- **Downstream**:
  - supervised-training-service (reads historical ml_features)
  - finrl-training-service (reads historical ml_features)
  - inference-service (subscribes to `features.*` via NATS)
- **Infrastructure**: ClickHouse, NATS cluster, Kafka (optional)

## Critical Rules
1. **NEVER** store raw OHLC in ml_features (only derived features!)
2. **ALWAYS** calculate targets for historical mode (training needs targets)
3. **NEVER** calculate targets for live mode (inference has no future data)
4. **VERIFY** all 110 features calculated (no missing features)
5. **VALIDATE** no NULL values in critical features (RSI, MACD, etc.)

## Common Tasks
- **Add indicator**: Update `src/features/technical_indicators.py` → Add to feature list
- **Add external feature**: Join with external_* tables → Merge into ml_features
- **Debug missing features**: Check candles exist, verify external data available

## Feature Breakdown
- **Technical indicators**: RSI, MACD, Bollinger, Stochastic, ATR, ADX, CCI, MFI (35 features)
- **Fibonacci levels**: Support/resistance (8 features)
- **Market sessions**: London/NY/Tokyo overlaps (6 features)
- **Calendar features**: Day of week, month boundaries (5 features)
- **Lagged features**: Previous N candles (20 features)
- **Rolling stats**: Support/resistance zones (15 features)
- **Multi-timeframe**: Higher TF context (15 features)
- **External data**: Economic events, FRED, commodities (6 features)
- **Targets**: Future returns (5 targets - historical only)

## Validation
When working on this service, ALWAYS verify:
- [ ] ml_features table has 110 columns (NOT 115 with OHLC!)
- [ ] Features calculated for all symbols + timeframes
- [ ] Historical mode: targets exist (future_return_5m, etc.)
- [ ] Live mode: NO targets (only 110 features, no future data)
- [ ] NATS publishes `features.*.*` (inference-service subscribes)

## Reference Docs
- Planning guide: `PLANNING_SKILL_GUIDE.md` (Service 7, lines 810-1050)
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 420-454)
- Flow + messaging: `SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 310-372)
- Database schema: `table_database_process.md` (ml_features table - v2.0.0)
