# Input Contract: Trading Engine → API Gateway

## Purpose
Trading Engine mengirim hasil AI analysis ke API Gateway untuk distribution ke multiple destinations (Client-MT5, Frontend, Telegram).

## Protocol Buffer Schema
**Source**: `central-hub/static/proto/trading/trading-output.proto`
**Message Type**: `TradingOutput`
**Transport**: HTTP POST dengan Protocol Buffers binary

## Data Flow
1. Trading Engine selesai analysis → Generate trading decisions
2. Send hasil ke API Gateway via HTTP POST
3. API Gateway route ke appropriate destinations based on decision type

## Schema Definition
```protobuf
message TradingOutput {
  string user_id = 1;
  string company_id = 2;
  repeated TradingSignal signals = 3;
  repeated AutoExecution executions = 4;
  DashboardUpdate dashboard_data = 5;
  int64 timestamp = 6;
  string correlation_id = 7;
}

message TradingSignal {
  string symbol = 1;           // "EURUSD"
  SignalType signal = 2;       // BUY/SELL/HOLD
  double confidence = 3;       // 0.85
  double entry_price = 4;      // 1.0845
  double stop_loss = 5;        // 1.0820
  double take_profit = 6;      // 1.0880
  string reasoning = 7;        // "Strong bullish pattern"
}

message AutoExecution {
  string mt5_account = 1;      // MT5 login
  TradingSignal signal = 2;
  double position_size = 3;    // 0.1 lot
  ExecutionMode mode = 4;      // IMMEDIATE/PENDING
}

enum SignalType {
  SIGNAL_BUY = 0;
  SIGNAL_SELL = 1;
  SIGNAL_HOLD = 2;
  SIGNAL_CLOSE = 3;
}
```

## Processing Requirements
- **Validation**: Verify trading signals are within user subscription limits
- **Routing**: Distribute based on user preferences (manual vs auto)
- **Performance**: <2ms routing time untuk real-time trading
- **Security**: Validate Trading Engine identity and user permissions

## Output Destinations
- **Auto Execution** → Client-MT5 via WebSocket
- **Trading Signals** → Telegram Bot via webhook
- **Dashboard Data** → Frontend via WebSocket
- **Analytics** → Database untuk historical tracking