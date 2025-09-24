# AI Trading Engine

## 🎯 Purpose
**Machine Learning dan Artificial Intelligence trading decision engine** yang menganalisis real-time market data dari approved brokers, mengintegrasikan external data sources, dan menghasilkan optimized trading execution commands untuk Client-MT5 terminals.

---

## 🤖 AI Trading Engine Architecture

### **AI Engine Structure**:
```
ai-trading-engine/
├── ml-models/              # Machine Learning Models
│   ├── price_prediction/   # Price movement prediction models
│   ├── sentiment_analysis/ # News sentiment analysis models
│   ├── risk_assessment/    # Risk scoring models
│   └── portfolio_opt/      # Portfolio optimization models
├── feature-engineering/    # Data preprocessing & feature extraction
│   ├── technical_features.py  # Technical indicators
│   ├── fundamental_features.py # Economic & news features
│   ├── market_structure.py    # Market microstructure features
│   └── cross_asset.py         # Cross-asset correlation features
├── decision-engine/        # Trading decision logic
│   ├── signal_generator.py    # ML signal generation
│   ├── risk_manager.py       # Risk management engine
│   ├── position_sizer.py     # Position sizing logic
│   └── execution_optimizer.py # Trade execution optimization
├── model-training/         # ML model training pipeline
│   ├── data_pipeline.py      # Training data preparation
│   ├── model_trainer.py      # Model training orchestration
│   ├── backtester.py         # Strategy backtesting
│   └── model_validator.py    # Model performance validation
└── shared/                 # Shared utilities
    ├── ai_config.py         # AI model configurations
    ├── performance_tracker.py # Model performance tracking
    └── feature_store.py      # Feature storage and retrieval
```

---

## 🧠 Machine Learning Models

### **Price Prediction Models**:
```python
class PricePredictionEngine:
    """Advanced price prediction using ensemble ML models"""

    def __init__(self):
        # Ensemble of multiple models
        self.models = {
            'lstm_model': LSTMPricePredictor(),      # Deep learning for sequences
            'xgboost_model': XGBoostPredictor(),     # Gradient boosting
            'transformer': TransformerPredictor(),    # Attention-based model
            'rf_model': RandomForestPredictor()      # Random forest baseline
        }

        self.ensemble_weights = {
            'lstm_model': 0.4,      # Higher weight for deep learning
            'xgboost_model': 0.3,   # Strong gradient boosting
            'transformer': 0.2,     # Attention mechanism
            'rf_model': 0.1         # Baseline model
        }

    async def predict_price_movement(self, market_features: MarketFeatures) -> PredictionResult:
        """Predict price movement using ensemble of ML models"""

        predictions = {}
        confidences = {}

        # Get predictions from all models
        for model_name, model in self.models.items():
            try:
                result = await model.predict(market_features)
                predictions[model_name] = result.prediction
                confidences[model_name] = result.confidence

            except Exception as e:
                logger.warning(f"Model {model_name} prediction failed: {e}")
                predictions[model_name] = 0.0
                confidences[model_name] = 0.0

        # Ensemble prediction (weighted average)
        ensemble_prediction = sum(
            predictions[model] * self.ensemble_weights[model] * confidences[model]
            for model in predictions.keys()
        ) / sum(
            self.ensemble_weights[model] * confidences[model]
            for model in predictions.keys()
        )

        # Ensemble confidence
        ensemble_confidence = sum(
            confidences[model] * self.ensemble_weights[model]
            for model in confidences.keys()
        )

        return PredictionResult(
            prediction=ensemble_prediction,
            confidence=ensemble_confidence,
            model_breakdown=predictions,
            confidence_breakdown=confidences
        )
```

### **Sentiment Analysis Models**:
```python
class NewsSentimentAnalyzer:
    """Advanced news sentiment analysis for trading decisions"""

    def __init__(self):
        # Multiple sentiment models
        self.models = {
            'finbert': FinBERTSentimentModel(),      # Financial BERT
            'vader': VaderSentimentAnalyzer(),       # Rule-based sentiment
            'custom_lstm': CustomLSTMSentiment()     # Custom trained model
        }

    async def analyze_market_sentiment(self, news_data: List[NewsItem]) -> MarketSentiment:
        """Analyze overall market sentiment from news data"""

        sentiment_scores = []
        impact_weighted_scores = []

        for news_item in news_data:
            # Analyze sentiment with multiple models
            sentiments = {}
            for model_name, model in self.models.items():
                sentiment = await model.analyze(news_item.content)
                sentiments[model_name] = sentiment

            # Ensemble sentiment score
            ensemble_sentiment = np.mean([s.score for s in sentiments.values()])

            # Weight by news impact score
            impact_weight = news_item.impact_score
            impact_weighted_scores.append(ensemble_sentiment * impact_weight)
            sentiment_scores.append(ensemble_sentiment)

        # Overall market sentiment
        overall_sentiment = np.mean(impact_weighted_scores) if impact_weighted_scores else 0.0
        sentiment_volatility = np.std(sentiment_scores) if sentiment_scores else 0.0

        return MarketSentiment(
            overall_score=overall_sentiment,
            volatility=sentiment_volatility,
            bullish_ratio=len([s for s in sentiment_scores if s > 0.1]) / len(sentiment_scores),
            bearish_ratio=len([s for s in sentiment_scores if s < -0.1]) / len(sentiment_scores),
            news_count=len(news_data)
        )
```

---

## ⚡ Feature Engineering Pipeline

### **Technical Feature Extraction**:
```python
class TechnicalFeatureExtractor:
    """Extract technical analysis features for ML models"""

    def extract_features(self, price_data: List[TickData]) -> TechnicalFeatures:
        """Extract comprehensive technical features"""

        features = TechnicalFeatures()

        # Convert to pandas for technical analysis
        df = self.convert_to_dataframe(price_data)

        # Moving averages
        features.sma_20 = ta.SMA(df['close'], timeperiod=20).iloc[-1]
        features.sma_50 = ta.SMA(df['close'], timeperiod=50).iloc[-1]
        features.ema_12 = ta.EMA(df['close'], timeperiod=12).iloc[-1]
        features.ema_26 = ta.EMA(df['close'], timeperiod=26).iloc[-1]

        # Momentum indicators
        features.rsi = ta.RSI(df['close'], timeperiod=14).iloc[-1]
        features.macd, features.macd_signal, features.macd_histogram = ta.MACD(df['close'])
        features.stochastic_k, features.stochastic_d = ta.STOCH(df['high'], df['low'], df['close'])

        # Volatility indicators
        features.bollinger_upper, features.bollinger_middle, features.bollinger_lower = ta.BBANDS(df['close'])
        features.atr = ta.ATR(df['high'], df['low'], df['close'], timeperiod=14).iloc[-1]

        # Volume indicators
        features.volume_sma = ta.SMA(df['volume'], timeperiod=20).iloc[-1]
        features.volume_ratio = df['volume'].iloc[-1] / features.volume_sma

        # Price action features
        features.price_change_1h = (df['close'].iloc[-1] - df['close'].iloc[-60]) / df['close'].iloc[-60]
        features.price_change_4h = (df['close'].iloc[-1] - df['close'].iloc[-240]) / df['close'].iloc[-240]
        features.price_change_24h = (df['close'].iloc[-1] - df['close'].iloc[-1440]) / df['close'].iloc[-1440]

        return features
```

### **Fundamental Feature Integration**:
```python
class FundamentalFeatureExtractor:
    """Extract fundamental analysis features"""

    async def extract_features(self, symbol: str, news_data: List[NewsItem],
                             economic_data: List[EconomicEvent]) -> FundamentalFeatures:
        """Extract fundamental features for trading decisions"""

        features = FundamentalFeatures()

        # Currency strength analysis
        base_currency = symbol[:3]
        quote_currency = symbol[3:]

        features.base_currency_strength = await self.analyze_currency_strength(base_currency, economic_data)
        features.quote_currency_strength = await self.analyze_currency_strength(quote_currency, economic_data)

        # Economic event impact
        features.upcoming_events_impact = self.calculate_upcoming_events_impact(economic_data)
        features.recent_events_impact = self.calculate_recent_events_impact(economic_data)

        # News sentiment features
        symbol_news = [n for n in news_data if symbol in n.affected_currencies]
        if symbol_news:
            sentiment_analyzer = NewsSentimentAnalyzer()
            market_sentiment = await sentiment_analyzer.analyze_market_sentiment(symbol_news)

            features.news_sentiment = market_sentiment.overall_score
            features.news_impact = np.mean([n.impact_score for n in symbol_news])
            features.news_volume = len(symbol_news)

        return features
```

---

## 🎯 Trading Decision Engine

### **Signal Generation Pipeline**:
```python
class TradingSignalGenerator:
    """Generate trading signals from ML model predictions"""

    def __init__(self):
        self.price_predictor = PricePredictionEngine()
        self.sentiment_analyzer = NewsSentimentAnalyzer()
        self.risk_manager = RiskManager()

    async def generate_trading_signal(self, market_data: MarketData) -> TradingSignal:
        """Generate comprehensive trading signal"""

        # Extract features
        technical_features = self.technical_extractor.extract_features(market_data.price_data)
        fundamental_features = await self.fundamental_extractor.extract_features(
            market_data.symbol, market_data.news_data, market_data.economic_data
        )

        # ML model predictions
        price_prediction = await self.price_predictor.predict_price_movement(
            MarketFeatures(technical_features, fundamental_features)
        )

        # Risk assessment
        risk_assessment = await self.risk_manager.assess_risk(market_data, price_prediction)

        # Generate signal
        signal_strength = self.calculate_signal_strength(price_prediction, risk_assessment)
        signal_direction = self.determine_direction(price_prediction)

        # Position sizing
        position_size = self.position_sizer.calculate_position_size(
            signal_strength, risk_assessment, market_data.account_info
        )

        return TradingSignal(
            symbol=market_data.symbol,
            direction=signal_direction,  # BUY/SELL/HOLD
            strength=signal_strength,    # 0.0 - 1.0
            confidence=price_prediction.confidence,
            position_size=position_size,
            stop_loss=self.calculate_stop_loss(price_prediction, risk_assessment),
            take_profit=self.calculate_take_profit(price_prediction, risk_assessment),
            risk_reward_ratio=risk_assessment.risk_reward_ratio,
            model_breakdown=price_prediction.model_breakdown
        )
```

### **Risk Management Engine**:
```python
class RiskManager:
    """Advanced risk management for AI trading decisions"""

    async def assess_risk(self, market_data: MarketData,
                         prediction: PredictionResult) -> RiskAssessment:
        """Comprehensive risk assessment"""

        risk_factors = {}

        # Market volatility risk
        risk_factors['volatility_risk'] = self.assess_volatility_risk(market_data.price_data)

        # News event risk
        risk_factors['news_risk'] = self.assess_news_event_risk(market_data.news_data)

        # Economic calendar risk
        risk_factors['economic_risk'] = self.assess_economic_event_risk(market_data.economic_data)

        # Model confidence risk
        risk_factors['model_risk'] = 1.0 - prediction.confidence

        # Correlation risk
        risk_factors['correlation_risk'] = await self.assess_correlation_risk(market_data.symbol)

        # Overall risk score
        overall_risk = np.mean(list(risk_factors.values()))

        return RiskAssessment(
            overall_risk_score=overall_risk,
            risk_factors=risk_factors,
            max_position_size=self.calculate_max_position_size(overall_risk),
            recommended_stop_loss=self.calculate_dynamic_stop_loss(overall_risk),
            risk_reward_ratio=self.calculate_optimal_risk_reward(overall_risk),
            approved=overall_risk < 0.7  # Only approve low-medium risk trades
        )
```

---

## 🎯 Business Value

### **AI Trading Advantages**:
- **Multi-Model Intelligence**: Ensemble of ML models for robust predictions
- **Real-time Analysis**: <10ms decision making dengan advanced features
- **Risk-Aware Trading**: Comprehensive risk assessment untuk every trade
- **News Integration**: Sentiment analysis dari multiple news sources
- **Continuous Learning**: Models continuously updated dengan new data

### **Client Protection**:
- **Centralized Risk Management**: Server-side risk control
- **Approved Brokers Only**: Regulated broker policy enforcement
- **Position Sizing**: Intelligent position sizing based on risk assessment
- **Stop Loss Automation**: Dynamic stop loss calculations
- **Performance Monitoring**: Real-time model performance tracking

**Key Innovation**: Advanced AI trading engine yang mengombinasikan multiple ML models, news sentiment analysis, dan comprehensive risk management untuk intelligent, automated trading decisions yang melindungi client capital.