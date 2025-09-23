# Input Contract: Analytics-Service → API Gateway

## Purpose
Analytics Service mengirim computed insights, performance metrics, dan analytics reports ke API Gateway untuk distribution ke Dashboard dan external reporting systems.

## Protocol Buffer Schema
**Source**: `central-hub/static/proto/analytics/analytics-output.proto`
**Message Type**: `AnalyticsOutput`
**Transport**: HTTP POST dengan Protocol Buffers binary

## Data Flow
1. Analytics Service process historical data → Generate insights dan metrics
2. Compute performance analytics dan trend analysis
3. Send results ke API Gateway via HTTP POST
4. API Gateway route ke Dashboard dan reporting channels

## Schema Definition
```protobuf
message AnalyticsOutput {
  string user_id = 1;
  string company_id = 2;
  repeated PerformanceMetrics performance = 3;
  repeated TradingInsights insights = 4;
  MarketAnalytics market_analytics = 5;
  SystemMetrics system_metrics = 6;
  int64 timestamp = 7;
  string correlation_id = 8;
  AnalyticsTimeframe timeframe = 9;
}

message PerformanceMetrics {
  string period = 1;                  // "daily", "weekly", "monthly"
  TradingPerformance trading = 2;
  AccountMetrics account = 3;
  RiskMetrics risk = 4;
  ModelPerformance model = 5;
  ComparisonData comparison = 6;
}

message TradingPerformance {
  int32 total_trades = 1;             // 156
  int32 winning_trades = 2;           // 112
  int32 losing_trades = 3;            // 44
  double win_rate = 4;                // 0.718 (71.8%)
  double profit_factor = 5;           // 1.45
  double sharpe_ratio = 6;            // 1.23
  double max_drawdown = 7;            // 0.08 (8%)
  double total_return = 8;            // 0.125 (12.5%)
  double average_win = 9;             // 35.50
  double average_loss = 10;           // -18.25
  double largest_win = 11;            // 85.00
  double largest_loss = 12;           // -45.00
}

message AccountMetrics {
  double starting_balance = 1;        // 10000.00
  double current_balance = 2;         // 11250.00
  double peak_balance = 3;            // 11400.00
  double total_deposits = 4;          // 10000.00
  double total_withdrawals = 5;       // 0.00
  double net_profit = 6;              // 1250.00
  double unrealized_pnl = 7;          // 15.50
  double margin_usage = 8;            // 0.35 (35%)
}

message RiskMetrics {
  double var_95 = 1;                  // Value at Risk 95%
  double expected_shortfall = 2;      // Conditional VaR
  double beta = 3;                    // Market beta
  double correlation_spy = 4;         // Correlation with S&P 500
  double max_position_size = 5;       // Largest position % of account
  double average_holding_time = 6;    // Hours
  double risk_reward_ratio = 7;       // Average RR ratio
}

message ModelPerformance {
  string model_id = 1;                // "lstm_v2.1"
  double accuracy = 2;                // 0.745 (74.5%)
  double precision = 3;               // 0.72
  double recall = 4;                  // 0.68
  double f1_score = 5;                // 0.70
  int32 predictions_made = 6;         // 450
  int32 successful_predictions = 7;   // 335
  double confidence_average = 8;      // 0.83
  ModelDrift drift_analysis = 9;
}

message TradingInsights {
  InsightType type = 1;               // PATTERN/TIMING/SYMBOL/STRATEGY
  string title = 2;                   // "Best Trading Hours Identified"
  string description = 3;             // Detailed insight description
  double confidence = 4;              // 0.85
  repeated string recommendations = 5; // Action recommendations
  InsightImpact impact = 6;           // Expected impact assessment
  repeated string supporting_data = 7; // Charts, tables references
}

message MarketAnalytics {
  repeated SymbolAnalytics symbols = 1;
  MarketSentiment sentiment = 2;
  VolatilityAnalysis volatility = 3;
  CorrelationMatrix correlations = 4;
  SeasonalPatterns seasonal = 5;
}

message SystemMetrics {
  double avg_latency_ms = 1;          // 15.5
  double uptime_percentage = 2;       // 99.9
  int64 total_api_calls = 3;          // 15645
  int64 successful_calls = 4;         // 15598
  double error_rate = 5;              // 0.003 (0.3%)
  repeated ServiceMetric services = 6;
}

message ComparisonData {
  BenchmarkComparison benchmark = 1;
  PeerComparison peers = 2;
  HistoricalComparison historical = 3;
}

message ModelDrift {
  double drift_score = 1;             // 0.05 (5% drift)
  string drift_status = 2;            // "stable", "moderate", "high"
  repeated string affected_features = 3;
  string last_retrain_date = 4;
  bool retrain_recommended = 5;
}

message InsightImpact {
  ImpactLevel level = 1;              // LOW/MEDIUM/HIGH
  double expected_improvement = 2;    // 0.15 (15% improvement)
  string timeframe = 3;               // "1-2 weeks"
  string metric_affected = 4;         // "win_rate", "profit_factor"
}

message SymbolAnalytics {
  string symbol = 1;                  // "EURUSD"
  double performance = 2;             // Symbol-specific performance
  double volatility = 3;              // Current volatility
  double volume_trend = 4;            // Volume trend analysis
  TrendDirection trend = 5;           // BULLISH/BEARISH/SIDEWAYS
}

message BenchmarkComparison {
  string benchmark_name = 1;          // "S&P 500"
  double our_return = 2;              // 0.125
  double benchmark_return = 3;        // 0.08
  double outperformance = 4;          // 0.045 (4.5%)
  double tracking_error = 5;          // 0.12
}

enum InsightType {
  PATTERN_INSIGHT = 0;
  TIMING_INSIGHT = 1;
  SYMBOL_INSIGHT = 2;
  STRATEGY_INSIGHT = 3;
  RISK_INSIGHT = 4;
}

enum ImpactLevel {
  LOW_IMPACT = 0;
  MEDIUM_IMPACT = 1;
  HIGH_IMPACT = 2;
}

enum TrendDirection {
  BULLISH = 0;
  BEARISH = 1;
  SIDEWAYS = 2;
}

enum AnalyticsTimeframe {
  REALTIME = 0;
  HOURLY = 1;
  DAILY = 2;
  WEEKLY = 3;
  MONTHLY = 4;
}
```

## Processing Requirements
- **Data Validation**: Verify analytics data integrity dan accuracy
- **Performance**: <5ms processing time untuk real-time updates
- **Aggregation**: Combine multiple analytics sources untuk comprehensive view
- **Caching**: Cache computed analytics untuk 15 minutes

## Output Destinations
- **Performance Dashboard** → Frontend via WebSocket (real-time charts)
- **Reports Generation** → PDF/Excel export service
- **External APIs** → Third-party analytics platforms
- **Data Warehouse** → Historical analytics storage

## Analytics Categories
- **Trading Performance** → Win rate, profit factor, Sharpe ratio
- **Risk Analysis** → VaR, drawdown, correlation analysis
- **Model Performance** → Accuracy, precision, drift detection
- **Market Insights** → Trend analysis, volatility patterns
- **System Health** → Latency, uptime, error rates

## Quality Assurance
- **Outlier Detection**: Flag unusual metric values
- **Data Freshness**: Ensure analytics are based on recent data
- **Accuracy Validation**: Cross-validate with multiple data sources
- **Historical Consistency**: Maintain consistent calculation methods