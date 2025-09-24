# Supporting Services Infrastructure

## 🎯 Purpose
**Core infrastructure services** yang mendukung data ingestion operation dengan service discovery, data aggregation, stream management, dan performance optimization untuk scalable multi-tenant data processing.

---

## 🏗️ Supporting Services Architecture

### **Infrastructure Services**:
```
supporting-services/
├── ingestion-gateway/      # Service discovery & coordination
│   ├── gateway.py         # Main API gateway for ingestion
│   ├── service_registry.py # Service discovery and health
│   ├── load_balancer.py   # Load balancing across collectors
│   └── auth_manager.py    # Internal service authentication
├── market-aggregator/      # Central data processing hub
│   ├── aggregator.py      # Core aggregation engine
│   ├── price_merger.py    # Multi-broker price merging
│   ├── quality_scorer.py  # Data quality assessment
│   ├── context_enricher.py # External data integration
│   └── deduplication.py   # Duplicate tick removal
└── stream-orchestrator/    # Stream flow management
    ├── orchestrator.py    # Stream coordination
    ├── topic_manager.py   # NATS topic organization
    ├── subscription_mgr.py # Client subscription handling
    ├── performance_opt.py # Stream performance tuning
    └── failover_manager.py # Stream failover handling
```

---

## 🔄 Service Interaction Flow

### **1. Ingestion Gateway**:
```python
class IngestionGateway:
    """Central coordination service for all data collectors"""

    async def register_collector(self, collector_info: CollectorInfo):
        """Register MT5/API/External data collectors"""

    async def health_monitor(self):
        """Monitor health of all registered collectors"""

    async def load_balance(self, data_stream):
        """Balance load across active collectors"""

    async def route_to_aggregator(self, processed_data):
        """Route validated data to market aggregator"""
```

**Responsibilities**:
- **Service Discovery**: Register and discover MT5-brokers, API-brokers, external-data collectors
- **Health Monitoring**: Real-time health checks for all collectors
- **Load Balancing**: Distribute processing load efficiently
- **Authentication**: Internal service-to-service security

### **2. Market Aggregator**:
```python
class MarketAggregator:
    """Central data processing and merging engine"""

    async def aggregate_broker_prices(self, mt5_data, api_data):
        """Merge prices from MT5 and API brokers"""

    async def enrich_with_external_data(self, price_data, news_data, sentiment_data):
        """Add external context to price data"""

    async def select_best_price(self, aggregated_data):
        """Select optimal price from multiple sources"""

    async def stream_to_bridge(self, enriched_data):
        """Stream processed data to Data Bridge"""
```

**Responsibilities**:
- **Price Aggregation**: Merge MT5-brokers + API-brokers data
- **External Integration**: Incorporate news, calendar, sentiment data
- **Quality Control**: Data validation and best price selection
- **Context Enrichment**: Add fundamental analysis context

### **3. Stream Orchestrator**:
```python
class StreamOrchestrator:
    """Stream management and optimization service"""

    async def manage_nats_topics(self):
        """Organize NATS topics for efficient routing"""

    async def optimize_throughput(self):
        """Optimize stream performance for 1000+ subscribers"""

    async def handle_subscriptions(self, client_subscriptions):
        """Coordinate client subscription requests"""

    async def manage_failover(self):
        """Handle stream failover and recovery"""
```

**Responsibilities**:
- **NATS Management**: Topic organization and message routing
- **Performance Optimization**: Stream tuning for high throughput
- **Subscription Coordination**: Client subscription management
- **Failover Handling**: Stream redundancy and recovery

---

## 📊 Complete Data Flow dengan Supporting Services

### **End-to-End Processing Pipeline**:
```
Data Collectors → Ingestion Gateway → Market Aggregator → Stream Orchestrator → Data Bridge
       ↓               ↓                   ↓                  ↓                 ↓
MT5-Brokers       Service Discovery   Price Merging      Topic Routing      Client Dist.
API-Brokers       Health Monitor      Quality Control    Performance Opt    Subscription
External-Data     Load Balancing      Context Enrich     Failover Mgmt      Real-time
```

### **Service Communication Pattern**:
- **Collectors → Gateway**: Health reports, data streams
- **Gateway → Aggregator**: Validated, balanced data streams
- **Aggregator → Orchestrator**: Processed, enriched market data
- **Orchestrator → Data Bridge**: Optimized, routed data streams

---

## ⚡ Performance & Scalability

### **Horizontal Scaling**:
- **Gateway**: Multiple instances for high availability
- **Aggregator**: Parallel processing for multiple symbols
- **Orchestrator**: Distributed stream management

### **Performance Targets**:
- **Gateway Latency**: <1ms service discovery and routing
- **Aggregation Latency**: <2ms price merging and quality control
- **Stream Latency**: <1ms NATS topic routing and optimization
- **Total Processing**: <5ms dari collector input ke Data Bridge output

### **Reliability Features**:
- **Health Monitoring**: Real-time collector health tracking
- **Auto-Recovery**: Automatic service restart and failover
- **Load Distribution**: Intelligent load balancing across services
- **Data Integrity**: End-to-end data validation and quality assurance

---

## 🎯 Business Benefits

### **Operational Excellence**:
- **Centralized Monitoring**: Single dashboard for all ingestion services
- **Automated Failover**: Zero-downtime service recovery
- **Performance Optimization**: Continuous throughput improvement
- **Scalable Architecture**: Handle 10,000+ concurrent users

### **Cost Efficiency**:
- **Resource Optimization**: Efficient use of server resources
- **Automated Operations**: Reduced manual intervention
- **Preventive Monitoring**: Early problem detection and resolution
- **Consolidated Infrastructure**: Shared services reduce overhead

---

**Key Innovation**: Comprehensive supporting services infrastructure yang mengoptimalkan data ingestion operation dengan automated service discovery, intelligent aggregation, dan high-performance stream management untuk enterprise-scale trading platform.