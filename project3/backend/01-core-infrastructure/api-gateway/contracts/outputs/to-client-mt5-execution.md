# Output Contract: API Gateway → Client-MT5 Execution

## Purpose
API Gateway mengirim auto execution commands ke Client-MT5 untuk immediate trade execution berdasarkan AI trading decisions.

## Protocol Buffer Schema
**Source**: `central-hub/static/proto/trading/execution-command.proto`
**Message Type**: `ExecutionCommand`
**Transport**: WebSocket Binary (real-time)

## Data Flow
1. Trading Engine → API Gateway → Trading decisions
2. API Gateway filter untuk auto execution only
3. Send execution commands ke Client-MT5 via WebSocket
4. Client-MT5 execute trades di MT5 terminal

## Schema Definition
```protobuf
message ExecutionCommand {
  string command_id = 1;       // Unique execution ID
  string user_id = 2;
  string mt5_account = 3;      // Target MT5 account
  ExecutionAction action = 4;
  ExecutionParams params = 5;
  int64 timestamp = 6;
  string correlation_id = 7;   // Link to original signal
}

message ExecutionAction {
  ActionType type = 1;         // OPEN_POSITION/CLOSE_POSITION/MODIFY
  string symbol = 2;           // "EURUSD"
  TradeDirection direction = 3; // BUY/SELL
  double volume = 4;           // 0.1 lot
  double price = 5;            // Entry price (optional for market orders)
  double stop_loss = 6;        // SL level
  double take_profit = 7;      // TP level
}

message ExecutionParams {
  OrderType order_type = 1;    // MARKET/PENDING/STOP
  int32 slippage = 2;          // Max slippage in points
  string comment = 3;          // "AI Signal BUY EURUSD"
  int32 magic_number = 4;      // Expert Advisor ID
  int64 expiration = 5;        // Order expiration (for pending)
}

enum ActionType {
  OPEN_POSITION = 0;
  CLOSE_POSITION = 1;
  MODIFY_POSITION = 2;
  CANCEL_ORDER = 3;
}

enum TradeDirection {
  BUY = 0;
  SELL = 1;
}

enum OrderType {
  MARKET = 0;
  PENDING = 1;
  STOP = 2;
  LIMIT = 3;
}
```

## Security Requirements
- **User Authorization**: Verify user has auto-trading enabled
- **Account Validation**: Confirm MT5 account belongs to user
- **Risk Limits**: Check position sizing within user limits
- **Real-time Delivery**: <100ms execution command delivery

## Error Handling
- **Connection Lost**: Buffer commands untuk reconnection
- **Invalid Account**: Log error, notify user via alternative channel
- **Risk Violation**: Block execution, alert user
- **MT5 Execution Failure**: Retry mechanism dengan exponential backoff

## Response Expected
Client-MT5 harus send execution result kembali ke API Gateway:
```protobuf
message ExecutionResult {
  string command_id = 1;       // Link to original command
  ExecutionStatus status = 2;  // SUCCESS/FAILED/PARTIAL
  string order_ticket = 3;     // MT5 order ticket number
  double executed_price = 4;   // Actual execution price
  string error_message = 5;    // If failed
  int64 execution_time = 6;    // MT5 execution timestamp
}
```