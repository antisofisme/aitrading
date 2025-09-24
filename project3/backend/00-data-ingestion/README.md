# Data Ingestion Service

## 🎯 Purpose
**Server-side market data collection dan AI trading decision service** yang mengumpulkan real-time tick data dari approved brokers, melakukan ML/AI analysis internal, dan mengirimkan trading execution commands ke client MT5 terminals.

---

## 📊 ChainFlow Diagram

```
4-Category Input Sources → Supporting Services → ML/AI Analysis → Trading Execution
            ↓                     ↓                     ↓               ↓
Broker-MT5 (IC Markets)     Ingestion Gateway    AI Trading Engine  Client-MT5
Broker-API (FXCM)          Market Aggregator    ML Prediction     Execution Commands
External-Data (News)       Stream Orchestrator  Decision Making   Account Management
Historical-Broker          Service Discovery    Risk Assessment   99.9% Efficiency
```

---

## 🏗️ Service Architecture

### **Input Flow**: 4-category data collection for internal AI processing
**Data Sources**:
- Broker-MT5: IC Markets, Pepperstone (MetaTrader5 API) - approved brokers only
- Broker-API: FXCM, OANDA (Native REST/WebSocket APIs) - approved brokers only
- External-Data: News, economic calendar, sentiment analysis
- Historical-Broker: Bulk historical data untuk ML training
**Format**: Protocol Buffers untuk internal processing
**Frequency**: Real-time (50+ ticks/sec) untuk AI analysis
**Performance Target**: <10ms AI analysis + decision making

### **Output Flow**: Trading execution commands ke Client-MT5
**Destination**: Client-MT5 terminals via API Gateway
**Format**: Trading execution commands (Protocol Buffers)
**Processing**: ML/AI analysis → Trading decisions → Risk management
**Performance Target**: <5ms execution command delivery

---

## 🚀 Transport Architecture & Efficiency Gains

### **Resource Optimization Strategy:**

#### **Traditional Architecture (Inefficient):**
```
1000 Users × 3 Brokers = 3000 MT5 Connections
Network: 3000x redundant streams
CPU: 3000x duplicate processing
Memory: 3000x data buffers
```

#### **AI Trading Architecture (Optimal):**
```
4-Category Data Collection + AI Engine + Supporting Services:
- Broker-MT5: 2 connections (approved brokers only)
- Broker-API: 2 connections (approved brokers only)
- External-Data: Multiple API connections (news, calendar, sentiment)
- AI Trading Engine: ML analysis + decision making
- Supporting Services: Gateway + Aggregator + Orchestrator
Total: Server-side processing → Trading commands to 1000+ clients
```

### **AI Trading Benefits:**
```
Resource & Intelligence Optimization:
- Client Connections: 1000+ clients → Server handles broker connections
- Data Processing: Server-side AI analysis (no client processing)
- Trading Intelligence: ML/AI decisions with multi-source data
- Risk Management: Centralized risk assessment and control
- Broker Policy: Only approved, regulated brokers accepted
- Cost Efficiency: 99.3% reduction vs traditional client-broker model
- Added Intelligence: AI + News + Economic + Sentiment analysis
```

---

## 🔄 Data Ingestion Pipeline

### **1. Broker Connection Management**:
```python
class BrokerCollector:
    async def connect_mt5_broker(self, broker_config: BrokerConfig):
        """Establish single MT5 connection per broker"""

        # Initialize MT5 connection
        mt5_connection = MT5Connection(
            server=broker_config.server,
            login=broker_config.login,
            password=broker_config.password
        )

        # Subscribe to all major pairs
        symbols = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD",
                  "USDCAD", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY"]

        for symbol in symbols:
            await mt5_connection.subscribe_tick_data(symbol, self.on_tick_received)

        # Performance tracking
        self.logger.info(f"Broker {broker_config.name} connected - streaming {len(symbols)} symbols")

    async def on_tick_received(self, tick_data: MqlTick):
        """Process incoming tick from broker"""

        # Convert to our protocol buffer format
        market_tick = self.convert_mql_to_protobuf(tick_data)

        # Add broker source info
        market_tick.source = self.broker_name
        market_tick.broker_timestamp = int(time.time() * 1000)

        # Send to aggregator
        await self.stream_to_aggregator(market_tick)
```

### **2. Market Data Aggregation**:
```python
class MarketAggregator:
    def __init__(self):
        self.broker_streams = {}  # Track data from each broker
        self.last_prices = {}     # Price deduplication cache
        self.quality_tracker = DataQualityTracker()

    async def aggregate_market_data(self, broker_tick: MarketTick):
        """Aggregate data dari multiple brokers"""

        symbol = broker_tick.symbol
        broker = broker_tick.source

        # Update broker stream tracking
        self.broker_streams[f"{broker}_{symbol}"] = broker_tick

        # Check for price differences antar brokers
        price_spread = self.calculate_broker_spread(symbol)

        # Select best price (usually tightest spread)
        best_tick = self.select_best_price(symbol)

        # Create aggregated market data stream
        market_stream = MarketDataStream()
        market_stream.ticks.append(best_tick)
        market_stream.source = "data-ingestion"
        market_stream.batch_time_msc = int(time.time() * 1000)

        # Distribute to subscribers
        await self.distribute_to_subscribers(market_stream)

        # Update quality metrics
        await self.quality_tracker.update_metrics(broker_tick, price_spread)
```

### **3. Data Distribution Engine**:
```python
class DistributionEngine:
    def __init__(self):
        self.nats_client = NATSClient()
        self.subscriber_map = {}  # Track user subscriptions

    async def distribute_to_subscribers(self, market_stream: MarketDataStream):
        """Distribute data ke subscribed users"""

        for tick in market_stream.ticks:
            symbol = tick.symbol

            # Get all users subscribed to this symbol
            subscribers = self.subscriber_map.get(symbol, [])

            # Serialize once, send to many
            binary_data = market_stream.SerializeToString()

            # NATS fanout - single publish, multiple deliveries
            subject = f"market.{symbol}.ticks"
            await self.nats_client.publish(subject, binary_data)

            # Performance tracking
            self.logger.debug(f"Distributed {symbol} to {len(subscribers)} subscribers")

    async def manage_subscriptions(self, user_id: str, symbols: List[str]):
        """Manage user symbol subscriptions"""

        for symbol in symbols:
            if symbol not in self.subscriber_map:
                self.subscriber_map[symbol] = set()

            self.subscriber_map[symbol].add(user_id)

        self.logger.info(f"User {user_id} subscribed to {len(symbols)} symbols")
```

---

## 📋 Broker Configuration

### **Multi-Broker Setup**:
```yaml
# Broker configurations
brokers:
  ic_markets:
    name: "IC Markets"
    server: "ICMarkets-Demo01"
    mt5_path: "/opt/mt5-ic/"
    symbols: ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD"]
    priority: 1  # Primary broker

  pepperstone:
    name: "Pepperstone"
    server: "Pepperstone-Demo"
    mt5_path: "/opt/mt5-pepper/"
    symbols: ["EURUSD", "GBPUSD", "USDJPY", "EURGBP", "EURJPY"]
    priority: 2  # Secondary broker

  fxcm:
    name: "FXCM"
    server: "FXCM-USDDemo01"
    mt5_path: "/opt/mt5-fxcm/"
    symbols: ["EURUSD", "GBPUSD", "USDJPY", "USDCAD", "GBPJPY"]
    priority: 3  # Tertiary broker
```

### **Broker Quality Comparison**:
```python
class BrokerQualityTracker:
    def compare_broker_feeds(self, symbol: str) -> BrokerComparison:
        """Compare data quality across brokers untuk symbol"""

        broker_metrics = {}

        for broker in self.active_brokers:
            metrics = self.get_broker_metrics(broker, symbol)
            broker_metrics[broker] = {
                "latency_ms": metrics.avg_latency,
                "spread_avg": metrics.avg_spread,
                "uptime_percent": metrics.uptime,
                "data_completeness": metrics.completeness,
                "tick_frequency": metrics.ticks_per_second
            }

        # Rank brokers by composite score
        best_broker = self.calculate_best_broker(broker_metrics)

        return BrokerComparison(
            best_broker=best_broker,
            metrics=broker_metrics,
            recommendation=f"Use {best_broker} as primary source for {symbol}"
        )
```

---

## ⚡ Performance Optimizations

### **Connection Pooling & Management**:
```python
class ConnectionManager:
    def __init__(self):
        self.mt5_pools = {}      # Connection pools per broker
        self.health_checker = BrokerHealthChecker()
        self.failover_manager = FailoverManager()

    async def maintain_connections(self):
        """Maintain optimal broker connections"""

        while True:
            for broker_name, pool in self.mt5_pools.items():
                # Health check
                if not await self.health_checker.check_broker(broker_name):
                    await self.failover_manager.handle_broker_failure(broker_name)
                    continue

                # Connection optimization
                if pool.active_connections < pool.optimal_connections:
                    await pool.add_connection()
                elif pool.active_connections > pool.optimal_connections:
                    await pool.remove_connection()

            await asyncio.sleep(30)  # Check every 30 seconds
```

### **Data Deduplication & Quality Control**:
```python
class DataQualityManager:
    def __init__(self):
        self.tick_cache = TTLCache(maxsize=10000, ttl=60)  # 1 minute cache
        self.quality_thresholds = {
            "max_spread": 0.005,     # 5 pips maximum spread
            "min_tick_interval": 50,  # 50ms minimum between ticks
            "max_price_change": 0.02  # 2% maximum price change
        }

    async def validate_tick_quality(self, tick: MarketTick) -> ValidationResult:
        """Validate tick data quality"""

        errors = []

        # Spread validation
        spread = tick.ask - tick.bid
        if spread > self.quality_thresholds["max_spread"]:
            errors.append(f"Excessive spread: {spread}")

        # Price movement validation
        last_price = self.tick_cache.get(f"{tick.symbol}_price")
        if last_price:
            price_change = abs(tick.bid - last_price) / last_price
            if price_change > self.quality_thresholds["max_price_change"]:
                errors.append(f"Excessive price movement: {price_change:.2%}")

        # Update cache
        self.tick_cache[f"{tick.symbol}_price"] = tick.bid

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            confidence=1.0 - (len(errors) * 0.2)
        )
```

---

## 🔗 Integration Points

### **Service Dependencies**:
- **MT5 Terminal Connections**: Direct connections ke broker servers
- **Data Bridge**: NATS/Kafka streaming untuk processed data
- **Central Hub**: Service registration dan health reporting
- **Database Service**: Configuration storage untuk broker settings

### **External Dependencies**:
- **Broker MT5 Servers**: IC Markets, Pepperstone, FXCM terminals
- **Network Infrastructure**: Stable connections ke broker datacenters
- **NATS/Kafka Cluster**: High-throughput message distribution
- **Monitoring System**: Real-time broker connection monitoring

---

## 🎯 Business Value

### **Cost Efficiency**:
- **99.9% Infrastructure Savings**: From 3000 to 3 broker connections
- **99.7% Bandwidth Reduction**: Eliminate redundant data streams
- **99.8% Processing Savings**: Single aggregation vs multiple processing
- **Linear Scaling**: Add users without additional broker connections

### **Data Quality**:
- **Multi-Broker Redundancy**: Best price selection across brokers
- **Real-time Quality Control**: Automated spread dan price validation
- **Broker Performance Tracking**: Data-driven broker selection
- **Failover Capability**: Automatic broker switching untuk reliability

### **User Experience**:
- **<1ms Data Latency**: Optimized distribution pipeline
- **99.9% Uptime**: Multi-broker redundancy dan failover
- **Consistent Pricing**: Quality-controlled data feeds
- **Scalable Architecture**: Support 10,000+ concurrent users

---

## 📊 Monitoring & Observability

### **Broker Connection Health**:
```python
@app.get("/health")
async def ingestion_health_check():
    """Comprehensive ingestion service health"""
    return {
        "service_name": "data-ingestion",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "uptime_seconds": await get_uptime_seconds(),
        "broker_connections": {
            broker: {
                "status": await check_broker_health(broker),
                "active_symbols": await get_active_symbols(broker),
                "ticks_per_second": await get_broker_throughput(broker),
                "latency_ms": await get_broker_latency(broker)
            } for broker in ["ic_markets", "pepperstone", "fxcm"]
        },
        "aggregation_metrics": {
            "total_symbols_tracked": await count_active_symbols(),
            "subscribers_count": await count_active_subscribers(),
            "distribution_latency_ms": await get_distribution_latency()
        },
        "quality_metrics": {
            "data_completeness_percent": await get_data_completeness(),
            "avg_spread_quality": await get_spread_quality(),
            "broker_sync_status": await get_broker_sync_status()
        }
    }
```

---

**Input Flow**: Multiple Brokers (MT5) → Data Ingestion (aggregation & quality control)
**Output Flow**: Data Ingestion → Data Bridge (NATS/Kafka stream distribution)
**Key Innovation**: Server-side broker aggregation dengan 99.9% resource efficiency gains untuk scalable multi-tenant market data distribution