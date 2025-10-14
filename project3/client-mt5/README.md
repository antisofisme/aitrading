# Suho MT5 Client Components

## Folder Structure

```
client-mt5/
├── tick-mt5/          # Tick Data Collector (NOT a trading EA!)
│   ├── SuhoWebSocketStreamer.mq5
│   ├── OptimizedWebSocket.mqh
│   └── BinaryProtocol.mqh
│
└── ea-mt5/            # Trading EA (for user trading)
    ├── SuhoAITrading.mq5
    └── BinaryProtocol.mqh
```

---

## 1. Tick Data Collector (tick-mt5/)

### Purpose
**Pure data collection** - streams real-time tick data to backend for analytics.

### ⚠️ IMPORTANT: NOT A TRADING EA!
- **ONE-WAY communication**: Upload only (MT5 → Server)
- **Does NOT receive commands** from server
- **Does NOT execute trades**
- **Does NOT manage positions**

### Communication Flow
```
MT5 Terminal
    ↓ OnTick() - collect tick data
    ↓ Encode to Suho Binary Protocol (32 bytes)
    ↓ WebSocket ws://localhost:8001/ws/ticks
    ↓ ONE-WAY UPLOAD ONLY
    ↓
API Gateway (Passthrough)
    ↓
NATS → Data Bridge → ClickHouse
```

### Features
- Real-time streaming of 14 forex pairs + gold
- Suho Binary Protocol (68% smaller than JSON)
- Ultra-low latency (<10ms)
- Automatic reconnection
- Performance monitoring

### Installation
1. Copy entire `tick-mt5/` folder to MT5 Experts directory
2. Compile `SuhoWebSocketStreamer.mq5`
3. Attach to any chart (symbol doesn't matter)
4. Configure WebSocket URL: `ws://localhost:8001/ws/ticks`

### Configuration
```mql5
input string InpWebSocketUrl = "ws://localhost:8001/ws/ticks";
input string InpBrokerName = "FBS";
input string InpAccountId = "101632934";
input int    InpPingInterval = 30;  // Keep-alive ping
```

---

## 2. Trading EA (ea-mt5/)

### Purpose
**User trading execution** - receives trading signals and executes trades.

### ⚠️ DIFFERENT FROM TICK COLLECTOR!
- **TWO-WAY communication**: Send & receive (MT5 ↔ Server)
- **Receives trading commands** from server
- **Executes trades** (open, close, modify)
- **Sends account info** (balance, positions, etc)

### Communication Flow
```
Trading EA ↔ API Gateway
    ↑ Receive: Trading commands (open/close/modify)
    ↓ Send: Account info, positions, executions

WebSocket: ws://localhost:8002/ws/trading (different port!)
Protocol: Suho Binary Protocol (bidirectional)
```

### Features
- Bidirectional WebSocket connection
- Receives trading signals from AI/ML backend
- Executes trades with risk management
- Sends execution confirmations
- Account monitoring

### Installation
1. Copy `ea-mt5/SuhoAITrading.mq5` to MT5 Experts directory
2. Compile
3. Attach to trading chart
4. Configure trading parameters

---

## Key Differences

| Feature | Tick Collector | Trading EA |
|---------|---------------|------------|
| Purpose | Data collection | Trade execution |
| Communication | ONE-WAY (upload) | TWO-WAY (bidirectional) |
| WebSocket | ws://.../ticks | ws://.../trading |
| Port | 8001 | 8002 |
| Receives commands | ❌ NO | ✅ YES |
| Executes trades | ❌ NO | ✅ YES |
| Data sent | Tick data only | Account info + confirmations |

---

## Protocol: Suho Binary Protocol

Both components use **Suho Binary Protocol** for efficiency:

### Packet Structure (32 bytes)
```
Header (16 bytes):
  [0-3]   Magic: 0x53554854 ("SUHO")
  [4-5]   Version: 0x0001
  [6]     Message Type
  [7]     Data Count
  [8-15]  Timestamp (ms)

Data (16 bytes per tick/command):
  [0-3]   Symbol ID (1-14)
  [4-7]   Bid/Price
  [8-11]  Ask/Value
  [12-15] Flags
```

### Symbol IDs (14 pairs)
```
1=EURUSD, 2=GBPUSD, 3=USDJPY, 4=USDCHF,
5=AUDUSD, 6=USDCAD, 7=NZDUSD, 8=EURGBP,
9=EURJPY, 10=GBPJPY, 11=AUDJPY, 12=NZDJPY,
13=CHFJPY, 14=XAUUSD
```

---

## FAQ

**Q: Can I use both together?**
A: Yes! Run tick collector on one chart, trading EA on another.

**Q: Does tick collector affect trading EA?**
A: No, completely independent.

**Q: Why separate collectors?**
A: Separation of concerns - data collection vs trading logic.

**Q: Which one should I use?**
- For data analytics → Tick Collector
- For automated trading → Trading EA
- For both → Run both (different charts)
