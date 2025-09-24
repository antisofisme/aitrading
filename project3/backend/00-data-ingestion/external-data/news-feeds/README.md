# News Feeds Data Collection

## 🎯 Purpose
**Real-time financial news data collection** dari multiple news providers untuk sentiment analysis, event detection, dan market impact prediction yang mendukung AI trading decisions.

---

## 📰 News Sources Architecture

### **News Provider Structure**:
```
news-feeds/
├── reuters/              # Reuters News API
│   ├── collector.py     # Reuters API integration
│   ├── config.yaml      # Reuters credentials & settings
│   └── parser.py        # Reuters news format parser
├── bloomberg/           # Bloomberg Terminal Data
│   ├── collector.py     # Bloomberg API integration
│   ├── config.yaml      # Bloomberg credentials
│   └── parser.py        # Bloomberg format parser
├── forex-factory/       # Forex Factory News
│   ├── collector.py     # Forex Factory scraper
│   ├── config.yaml      # Scraping settings
│   └── parser.py        # News format parser
└── shared/              # Shared utilities
    ├── news_classifier.py  # News category classification
    ├── sentiment_analyzer.py # News sentiment analysis
    └── impact_scorer.py     # Market impact prediction
```

---

## 🔄 News Collection Process

### **Real-time News Streaming**:
```python
class NewsCollector:
    async def collect_news_feeds(self):
        """Collect real-time news dari multiple sources"""

        # Reuters news stream
        reuters_news = await self.reuters_client.get_live_feed()

        # Bloomberg news stream
        bloomberg_news = await self.bloomberg_client.get_feed()

        # Forex Factory news
        ff_news = await self.forex_factory_client.scrape_latest()

        # Process and merge all news
        for news_item in [reuters_news, bloomberg_news, ff_news]:
            processed_news = await self.process_news_item(news_item)
            await self.stream_to_aggregator(processed_news)
```

### **News Processing Pipeline**:
1. **Data Collection**: Pull dari multiple news APIs
2. **Content Parsing**: Extract title, content, timestamp, source
3. **Classification**: Categorize news (central bank, economic data, geopolitical)
4. **Sentiment Analysis**: Analyze news sentiment (bullish/bearish/neutral)
5. **Impact Scoring**: Predict market impact magnitude
6. **Stream Output**: Send ke Market Aggregator via NATS

---

## 📊 News Data Format

### **Protocol Buffer Schema**:
```protobuf
message NewsItem {
  string news_id = 1;                  // Unique news identifier
  string title = 2;                    // News headline
  string content = 3;                  // News content/summary
  string source = 4;                   // Reuters, Bloomberg, ForexFactory
  int64 timestamp = 5;                 // Publication timestamp
  string category = 6;                 // central_bank, economic, geopolitical
  double sentiment_score = 7;          // -1.0 (bearish) to +1.0 (bullish)
  double impact_score = 8;             // 0.0 (low) to 1.0 (high impact)
  repeated string affected_currencies = 9; // USD, EUR, GBP, etc.
  repeated string keywords = 10;       // Key terms extracted
}
```

### **News Categories**:
- **Central Bank**: Fed, ECB, BoE, BoJ decisions and speeches
- **Economic Data**: GDP, CPI, NFP, unemployment data
- **Geopolitical**: Trade wars, elections, policy changes
- **Market Events**: Earnings, corporate announcements
- **Technical**: Market analysis, technical breakouts

---

## 🎯 News Impact Analysis

### **Sentiment Analysis**:
```python
class NewsSentimentAnalyzer:
    def analyze_sentiment(self, news_content: str) -> float:
        """Analyze news sentiment (-1.0 to +1.0)"""

        # Bullish keywords
        bullish_terms = ['growth', 'positive', 'strong', 'increase', 'boost']

        # Bearish keywords
        bearish_terms = ['decline', 'weak', 'fall', 'concern', 'risk']

        # Calculate sentiment score
        sentiment = self.calculate_weighted_sentiment(news_content,
                                                    bullish_terms, bearish_terms)
        return sentiment
```

### **Market Impact Prediction**:
```python
class NewsImpactScorer:
    def predict_impact(self, news_item: NewsItem) -> float:
        """Predict market impact (0.0 to 1.0)"""

        impact_factors = {
            'central_bank': 0.9,      # High impact
            'economic_data': 0.7,     # Medium-high impact
            'geopolitical': 0.6,      # Medium impact
            'market_events': 0.4      # Lower impact
        }

        base_impact = impact_factors.get(news_item.category, 0.3)

        # Adjust based on sentiment strength
        sentiment_multiplier = abs(news_item.sentiment_score)

        return min(1.0, base_impact * (1 + sentiment_multiplier))
```

---

## ⚡ Performance & Reliability

### **Collection Frequency**:
- **Reuters**: Real-time stream, ~100 news/day
- **Bloomberg**: Real-time stream, ~200 news/day
- **Forex Factory**: Every 5 minutes, ~50 news/day
- **Processing**: <1 second per news item

### **Quality Control**:
```python
class NewsQualityController:
    def validate_news(self, news_item: NewsItem) -> bool:
        """Validate news quality and relevance"""

        # Check required fields
        if not all([news_item.title, news_item.content, news_item.timestamp]):
            return False

        # Check forex relevance
        forex_keywords = ['currency', 'forex', 'central bank', 'interest rate']
        if not any(keyword in news_item.content.lower() for keyword in forex_keywords):
            return False

        # Check freshness (within 24 hours)
        age_hours = (time.time() - news_item.timestamp) / 3600
        if age_hours > 24:
            return False

        return True
```

---

## 🔗 Integration with Trading System

### **Real-time Alerts**:
```python
# High-impact news alert
if news_item.impact_score > 0.8:
    alert = {
        'type': 'high_impact_news',
        'title': news_item.title,
        'sentiment': news_item.sentiment_score,
        'affected_pairs': ['EURUSD', 'GBPUSD'],  # Based on currencies
        'action': 'review_positions'
    }
    await self.send_trader_alert(alert)
```

### **AI Model Features**:
- **Sentiment Scores**: Input features for prediction models
- **Impact Timing**: Event-driven model triggers
- **Category Weighting**: Different impact weights per news type
- **Currency Correlation**: News impact on specific currency pairs

---

## 🎯 Business Value

### **Trading Enhancement**:
- **Event Awareness**: Trade around high-impact news releases
- **Sentiment Integration**: Incorporate market sentiment into decisions
- **Risk Management**: Reduce positions before major announcements
- **Opportunity Detection**: Identify news-driven trading opportunities

### **Competitive Advantage**:
- **Multi-source Intelligence**: Comprehensive news coverage
- **Real-time Processing**: Instant news analysis and alerts
- **AI Integration**: News sentiment as model features
- **Automated Responses**: Event-driven trading strategies

**Key Innovation**: Real-time news collection dan analysis yang mengintegrasikan sentiment analysis dengan market impact prediction untuk intelligent trading decisions.