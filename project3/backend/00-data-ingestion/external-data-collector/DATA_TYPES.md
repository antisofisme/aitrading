# External Data Types & Topics

## 📊 Supported Data Types

### 1. **Economic Calendar** ✅ (Implemented)
- **Type**: `economic_calendar`
- **NATS Subject**: `market.external.economic_calendar`
- **Kafka Topic**: `market.external.economic_calendar`
- **Source**: MQL5.com
- **Update Frequency**: Hourly
- **Data Fields**:
  ```json
  {
    "date": "2025-10-06",
    "time": "14:30",
    "currency": "USD",
    "event": "Non-Farm Payrolls",
    "forecast": "200K",
    "previous": "187K",
    "actual": "215K",
    "impact": "high"
  }
  ```

### 2. **FRED Economic Indicators** ✅ (Implemented)
- **Type**: `fred_economic`
- **NATS Subject**: `market.external.fred_economic`
- **Kafka Topic**: `market.external.fred_economic`
- **Source**: FRED (St. Louis Fed)
- **Update Frequency**: 4 hours
- **Data Fields**:
  ```json
  {
    "series_id": "GDP",
    "value": 27724.5,
    "date": "2025-Q1",
    "updated_at": "2025-10-06T14:30:00Z"
  }
  ```
- **Indicators**: GDP, UNRATE, CPIAUCSL, DFF, DGS10, DEXUSEU, DEXJPUS

### 3. **Crypto Sentiment** ✅ (Implemented)
- **Type**: `crypto_sentiment`
- **NATS Subject**: `market.external.crypto_sentiment`
- **Kafka Topic**: `market.external.crypto_sentiment`
- **Source**: CoinGecko
- **Update Frequency**: 30 minutes
- **Data Fields**:
  ```json
  {
    "coin_id": "bitcoin",
    "name": "Bitcoin",
    "symbol": "BTC",
    "price_usd": 42000.50,
    "price_change_24h": 2.5,
    "market_cap_rank": 1,
    "sentiment_votes_up_percentage": 75.3,
    "community_score": 82.5,
    "twitter_followers": 5000000,
    "reddit_subscribers": 4500000,
    "updated_at": "2025-10-06T14:30:00Z"
  }
  ```

### 4. **Fear & Greed Index** ✅ (Implemented)
- **Type**: `fear_greed_index`
- **NATS Subject**: `market.external.fear_greed_index`
- **Kafka Topic**: `market.external.fear_greed_index`
- **Source**: Alternative.me
- **Update Frequency**: Hourly
- **Data Fields**:
  ```json
  {
    "value": 72,
    "classification": "Greed",
    "sentiment_score": 0.44,
    "timestamp": "1696598400",
    "time_until_update": "3600"
  }
  ```

### 5. **Commodity Prices** ✅ (Implemented)
- **Type**: `commodity_prices`
- **NATS Subject**: `market.external.commodity_prices`
- **Kafka Topic**: `market.external.commodity_prices`
- **Source**: Yahoo Finance
- **Update Frequency**: 30 minutes
- **Data Fields**:
  ```json
  {
    "symbol": "GC=F",
    "name": "Gold",
    "currency": "USD",
    "price": 1950.25,
    "previous_close": 1945.00,
    "change": 5.25,
    "change_percent": 0.27,
    "volume": 250000,
    "updated_at": "2025-10-06T14:30:00Z"
  }
  ```
- **Commodities**: Gold (GC=F), Crude Oil (CL=F), Silver (SI=F), Copper (HG=F), Natural Gas (NG=F)

### 6. **Market Sessions** ✅ (Implemented)
- **Type**: `market_sessions`
- **NATS Subject**: `market.external.market_sessions`
- **Kafka Topic**: `market.external.market_sessions`
- **Source**: Market Sessions Calculator
- **Update Frequency**: 5 minutes
- **Data Fields**:
  ```json
  {
    "current_utc_time": "14:30:00",
    "active_sessions_count": 2,
    "active_sessions": ["london", "newyork"],
    "overlapping_sessions": ["london", "newyork"],
    "liquidity_level": "very_high",
    "sessions": [
      {
        "name": "london",
        "is_active": true,
        "open_time": "08:00",
        "close_time": "16:30",
        "time_until_close_minutes": 120
      }
    ]
  }
  ```

### 7. **Financial News** (Future)
- **Type**: `news`
- **NATS Subject**: `market.external.news`
- **Kafka Topic**: `market.external.news`
- **Sources**: Reuters, Bloomberg, etc.

### 8. **COT Reports** (Future)
- **Type**: `cot_report`
- **NATS Subject**: `market.external.cot_report`
- **Kafka Topic**: `market.external.cot_report`
- **Source**: CFTC (Commodity Futures Trading Commission)
- **Update Frequency**: Weekly (Friday)

---

## 🔄 Message Format

All messages follow this structure:

```json
{
  "data": {
    // Actual data (varies by type)
  },
  "metadata": {
    "type": "economic_calendar",
    "source": "mql5",
    "timestamp": "2025-10-06T14:30:00Z",
    "version": "1.0.0",
    "scraper_id": "external-data-collector-1"
  }
}
```

---

## 📡 Topic Routing

### NATS Subjects (Real-time)
```
market.external.economic_calendar  → Economic events
market.external.news               → Financial news
market.external.sentiment          → Market sentiment
market.external.cot_report         → COT reports
market.external.market_context     → VIX, correlations
market.external.alternative_data   → Google Trends, etc.
```

### Kafka Topics (Persistence)
```
market.external.economic_calendar  → Long-term storage
market.external.news               → News archive
market.external.sentiment          → Sentiment history
market.external.cot_report         → COT archive
market.external.market_context     → Context data
market.external.alternative_data   → Alternative data
```

---

## 🎯 Consumer Examples

### Subscribe to Economic Calendar (NATS)
```python
from nats.aio.client import Client as NATS

async def handle_economic_event(msg):
    data = json.loads(msg.data.decode())
    print(f"Economic Event: {data['data']['event']}")

nats = NATS()
await nats.connect("nats://suho-nats:4222")
await nats.subscribe("market.external.economic_calendar", cb=handle_economic_event)
```

### Consume from Kafka
```python
from kafka import KafkaConsumer

consumer = KafkaConsumer(
    'market.external.economic_calendar',
    bootstrap_servers=['suho-kafka:9092']
)

for message in consumer:
    data = json.loads(message.value)
    print(f"Economic Event: {data['data']['event']}")
```

---

## 🚀 Adding New Data Types

1. **Add to DataType enum** (`src/publishers/nats_kafka_publisher.py`):
```python
class DataType(Enum):
    YOUR_NEW_TYPE = "your_new_type"
```

2. **Create scraper** (`src/scrapers/your_scraper.py`):
```python
class YourScraper:
    async def scrape(self):
        data = await self._fetch_data()
        await publisher.publish(data, DataType.YOUR_NEW_TYPE)
```

3. **Update config** (`config/scrapers.yaml`):
```yaml
scrapers:
  your_new_scraper:
    enabled: true
    source: yoursite.com
    scrape_interval: 3600
```

4. **Add to main.py**:
```python
if scraper_config['your_new_scraper']['enabled']:
    scraper = YourScraper(...)
    self.scrapers['your_new_scraper'] = scraper
```

---

## 📈 Implementation Status

**✅ Implemented (6 Data Sources)**:
1. Economic Calendar (MQL5)
2. FRED Economic Indicators
3. Crypto Sentiment (CoinGecko)
4. Fear & Greed Index
5. Commodity Prices (Yahoo Finance)
6. Market Sessions

**🚧 Future Expansion**:
- Financial News
- COT Reports
- Custom sentiment indicators
