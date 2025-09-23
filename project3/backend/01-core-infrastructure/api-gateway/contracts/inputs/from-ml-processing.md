# Input Contract: ML Processing → API Gateway

## Purpose
ML Processing service mengirim AI predictions, market analysis, dan confidence scores ke API Gateway untuk distribution ke dashboard dan decision systems.

## Protocol Buffer Schema
**Source**: `central-hub/static/proto/ml/ml-output.proto`
**Message Type**: `MLOutput`
**Transport**: HTTP POST dengan Protocol Buffers binary

## Data Flow
1. ML Processing selesai analysis → Generate predictions dan insights
2. Send results ke API Gateway via HTTP POST
3. API Gateway route ke appropriate destinations (Dashboard, Analytics, Trading Engine)

## Schema Definition
```protobuf
message MLOutput {
  string user_id = 1;
  string company_id = 2;
  repeated MarketPrediction predictions = 3;
  repeated PatternRecognition patterns = 4;
  MarketSentiment sentiment = 5;
  ModelMetrics model_performance = 6;
  int64 timestamp = 7;
  string correlation_id = 8;
}

message MarketPrediction {
  string symbol = 1;              // "EURUSD"
  PredictionType type = 2;        // PRICE/DIRECTION/VOLATILITY
  double confidence = 3;          // 0.85
  double predicted_value = 4;     // Predicted price/direction
  int32 timeframe_minutes = 5;    // Prediction horizon
  repeated double features = 6;   // Input features used
  string model_id = 7;            // Which model generated prediction
  double accuracy_score = 8;      // Historical accuracy of this model
}

message PatternRecognition {
  string symbol = 1;
  PatternType pattern = 2;        // HEAD_SHOULDERS/TRIANGLE/BREAKOUT
  double confidence = 3;
  string description = 4;         // "Bullish head and shoulders forming"
  PatternSignal signal = 5;       // BUY/SELL/NEUTRAL
  double target_price = 6;        // Pattern target
  int64 pattern_start = 7;        // Pattern formation start time
}

message MarketSentiment {
  SentimentType overall = 1;      // BULLISH/BEARISH/NEUTRAL
  double sentiment_score = 2;     // -1.0 to 1.0
  repeated SymbolSentiment symbols = 3;
  NewsImpact news_impact = 4;
  EconomicIndicators economic = 5;
}

message ModelMetrics {
  string model_id = 1;
  double accuracy = 2;            // Current model accuracy
  double precision = 3;           // Precision score
  double recall = 4;              // Recall score
  int32 predictions_today = 5;    // Number of predictions made
  double avg_confidence = 6;      // Average confidence score
  int64 last_training = 7;        // Last model training time
}

enum PredictionType {
  PRICE = 0;
  DIRECTION = 1;
  VOLATILITY = 2;
  SUPPORT_RESISTANCE = 3;
}

enum PatternType {
  HEAD_SHOULDERS = 0;
  TRIANGLE = 1;
  BREAKOUT = 2;
  REVERSAL = 3;
  CONTINUATION = 4;
}

enum PatternSignal {
  PATTERN_BUY = 0;
  PATTERN_SELL = 1;
  PATTERN_NEUTRAL = 2;
}

enum SentimentType {
  BULLISH = 0;
  BEARISH = 1;
  NEUTRAL = 2;
  MIXED = 3;
}
```

## Processing Requirements
- **Model Validation**: Verify ML model identity dan performance metrics
- **Confidence Filtering**: Only forward predictions with confidence > threshold
- **Performance**: <3ms routing time untuk real-time analysis
- **Data Enrichment**: Add user context dan subscription filtering

## Output Destinations
- **Dashboard Updates** → Frontend via WebSocket (real-time charts)
- **Trading Decisions** → Trading Engine for signal generation
- **Analytics Storage** → Analytics Service for performance tracking
- **Model Monitoring** → Central-Hub for ML model health tracking

## Quality Control
- **Prediction Validation**: Check prediction ranges are realistic
- **Model Drift Detection**: Alert if model performance drops
- **Feature Monitoring**: Track input feature quality
- **Accuracy Tracking**: Monitor prediction vs actual performance