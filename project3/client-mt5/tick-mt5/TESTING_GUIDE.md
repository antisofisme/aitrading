# Testing Guide - Suho WebSocket Tick Streamer

## Status: ✅ READY TO TEST

Semua komponen sudah dibuat dan siap untuk testing:
- ✅ SuhoWebSocketStreamer.mq5 (MT5 tick collector)
- ✅ OptimizedWebSocket.mqh (WebSocket client library)
- ✅ BinaryProtocol.mqh (Suho Binary Protocol encoder)
- ✅ websocket-server.js (Test server dengan mock NATS)

---

## Testing Flow

```
┌─────────────────┐
│  MT5 Terminal   │
│  (14 pairs)     │
└────────┬────────┘
         │ WebSocket Binary Frames
         │ ws://localhost:8001/ws/ticks
         ↓
┌──────────────────────┐
│ websocket-server.js  │ ← Test server (standalone)
│  + Mock NATS Client  │
└──────────────────────┘
         │
         ↓ Console log
   📊 Binary frames received
   📤 Mock NATS publish
```

---

## Step 1: Compile MT5 Files

### 1.1 Copy Files ke MT5 Terminal

```bash
# Copy entire tick-mt5 folder ke MT5 Experts directory
# Contoh path Windows:
C:\Users\YourName\AppData\Roaming\MetaQuotes\Terminal\{TERMINAL_ID}\MQL5\Experts\tick-mt5\
```

Copy 3 files ini:
- `SuhoWebSocketStreamer.mq5`
- `OptimizedWebSocket.mqh`
- `BinaryProtocol.mqh`

### 1.2 Compile di MT5 MetaEditor

1. Buka **MetaEditor** (F4 di MT5)
2. Open file: `Experts\tick-mt5\SuhoWebSocketStreamer.mq5`
3. Klik **Compile** (F7) atau menu `File > Compile`
4. Pastikan **0 errors**, warning OK (biasanya ada warning soal includes)

Output: `SuhoWebSocketStreamer.ex5` akan dibuat

---

## Step 2: Start Test Server

### 2.1 Install Dependencies (first time only)

```bash
cd /mnt/g/khoirul/aitrading/project3/backend/01-core-infrastructure/api-gateway
npm install
```

### 2.2 Start WebSocket Test Server

```bash
cd /mnt/g/khoirul/aitrading/project3/backend/01-core-infrastructure/api-gateway
node websocket-server.js
```

**Expected Output:**
```
═══════════════════════════════════════════════════════════════════
🚀 WebSocket Tick Passthrough Server - STARTED
═══════════════════════════════════════════════════════════════════
📡 Listening on: 0.0.0.0:8003 (all interfaces)

🔌 Access from:
   WSL/Linux:  ws://localhost:8003/ws/ticks
   Windows MT5: ws://172.24.56.226:8003/ws/ticks  ← USE THIS!

📊 Stats: http://172.24.56.226:8003/stats
💚 Health: http://172.24.56.226:8003/health
═══════════════════════════════════════════════════════════════════
✅ Ready to receive binary frames from MT5!
```

**⚠️ IMPORTANT:** Server runs in WSL, MT5 runs in Windows!
- Use **WSL IP** (`172.24.56.226`) not `localhost`
- WSL IP shown in server startup message

---

## Step 3: Run MT5 Tick Collector

### 3.1 Attach EA to Chart

1. Buka **MT5 Terminal**
2. Open any chart (symbol doesn't matter - collector streams all 14 pairs)
3. Drag `SuhoWebSocketStreamer` dari **Navigator > Experts** ke chart
4. Dialog akan muncul dengan parameters

### 3.2 Configure Parameters

**⚠️ PENTING:** Gunakan WSL IP, bukan localhost!

```
WebSocket URL: ws://172.24.56.226:8003/ws/ticks  ← GUNAKAN INI!
Broker Name: FBS                                  (ganti sesuai broker Anda)
Account ID: 101632934                             (ganti dengan account Anda)
Use Async: false                                  (false = real-time)
Ping Interval: 30                                 (seconds)
Enable Logs: true                                 (untuk debugging)
```

**Why WSL IP?**
- Server runs in **WSL (Linux)**: `172.24.56.226:8003`
- MT5 runs in **Windows**: Can't use `localhost`
- Must use WSL IP to connect across environments

Klik **OK** untuk start.

### 3.3 Expected Output di MT5 Terminal

```
═══════════════════════════════════════════════════════════
🚀 Suho Tick Data Collector - Starting...
⚠️  NOTE: This is NOT a trading EA!
📤 ONE-WAY: Upload tick data only (no commands received)
═══════════════════════════════════════════════════════════
✅ Symbol available: EURUSD
✅ Symbol available: GBPUSD
✅ Symbol available: USDJPY
... (all 14 pairs)
───────────────────────────────────────────────────────────
📊 Configuration:
   WebSocket URL: ws://localhost:8001/ws/ticks
   Broker: FBS
   Account: 101632934
   Protocol: Suho Binary (32 bytes per tick)
   Async Mode: Disabled (real-time)
   Ping Interval: 30s
   Available Pairs: 14/14
═══════════════════════════════════════════════════════════
✅ Tick Data Collector initialized successfully!
📤 ONE-WAY Upload: Streaming 14 pairs
⚡ Suho Binary Protocol - 32 bytes per tick
🚫 Does NOT execute trades or receive commands
═══════════════════════════════════════════════════════════

📊 Stats: Sent=140 Errors=0 Queue=0 | Ticks/sec: 14
📊 Stats: Sent=280 Errors=0 Queue=0 | Ticks/sec: 14
```

---

## Step 4: Monitor Test Server

### 4.1 Console Output (websocket-server.js)

Anda akan melihat log seperti ini:

```
🔌 [WS-TICK] Client connected: client-xyz
📥 [WS-TICK] Binary frame received: 32 bytes
🔍 [WS-TICK] Magic: 0x53554854 ✅ (SUHO)
📤 [MOCK-NATS] Published to: market.ticks.raw.binary
   Data size: 32 bytes
   Metadata: {
     source: 'mt5_websocket',
     clientId: 'client-xyz',
     timestamp: 1734567890123,
     size: 32
   }
```

### 4.2 Check Stats Endpoint

```bash
curl http://localhost:8001/stats
```

Expected response:
```json
{
  "totalClients": 1,
  "totalFramesReceived": 140,
  "totalBytesSent": 4480,
  "totalBytesReceived": 4480,
  "totalErrors": 0,
  "uptime": "00:01:23",
  "clients": [
    {
      "id": "client-xyz",
      "connectedAt": "2024-10-13T14:30:00.000Z",
      "framesReceived": 140,
      "lastFrameAt": "2024-10-13T14:30:10.000Z"
    }
  ]
}
```

---

## Step 5: Validation Checklist

### ✅ MT5 Side
- [ ] EA compiled successfully (0 errors)
- [ ] All 14 symbols available and selected
- [ ] WebSocket connected successfully
- [ ] Ticks are being sent (check MT5 terminal log)
- [ ] No errors in Expert tab

### ✅ Server Side
- [ ] Test server started on port 8001
- [ ] WebSocket connection established
- [ ] Binary frames received (32 bytes each)
- [ ] Magic number validated (0x53554854)
- [ ] Mock NATS publishes working
- [ ] Stats endpoint shows activity

### ✅ Protocol Validation
- [ ] Frame size = 32 bytes (header 16 + data 16)
- [ ] Magic = 0x53554854 ("SUHO")
- [ ] Version = 0x0001
- [ ] Message type = 0x03 (PRICE_STREAM)
- [ ] Data count = 1 (single tick per frame)
- [ ] Timestamp in milliseconds

---

## Common Issues

### Issue 1: MT5 Can't Connect to WebSocket
**Symptoms**: "Failed to connect to WebSocket server"

**Solutions**:
1. Check if test server is running (`node websocket-server.js`)
2. Verify port 8001 is not blocked by firewall
3. Use `ws://localhost:8001/ws/ticks` (not `wss://` for local test)

### Issue 2: Symbols Not Available
**Symptoms**: "Symbol NOT available: EURUSD"

**Solutions**:
1. Open Market Watch (Ctrl+M)
2. Right-click > "Show All"
3. Or manually add missing symbols

### Issue 3: Send Errors
**Symptoms**: "Send errors: 100 (disconnected or network issue)"

**Solutions**:
1. Check WebSocket connection status
2. Restart test server
3. Remove and re-attach EA to chart

---

## Performance Benchmarks

**Expected Performance:**

| Metric | Target | Description |
|--------|--------|-------------|
| Latency | <10ms | MT5 → Server |
| Throughput | 140 ticks/sec | 14 pairs × ~10 ticks/sec |
| Frame size | 32 bytes | Fixed (Suho Binary) |
| Bandwidth | ~17 KB/sec | 140 × 32 bytes |
| CPU (MT5) | <5% | Low overhead |
| Memory | <10 MB | Small footprint |

---

## Next Steps After Successful Test

1. **Integration dengan API Gateway penuh** (bukan mock server)
2. **Update Data Bridge** untuk handle 14 symbol IDs
3. **Deploy ke production** dengan NATS cluster
4. **Load testing** dengan market hours (high volume)
5. **Monitoring** dengan Grafana dashboard

---

## Quick Commands Cheat Sheet

```bash
# Start test server
cd /mnt/g/khoirul/aitrading/project3/backend/01-core-infrastructure/api-gateway
node websocket-server.js

# Check stats
curl http://localhost:8001/stats

# Check health
curl http://localhost:8001/health

# View server logs
# (just watch the console where websocket-server.js is running)
```

---

## Testing Complete ✅

Kalau semua checklist di atas passed, artinya:
- ✅ MT5 WebSocket tick streaming **WORKING**
- ✅ Suho Binary Protocol encoding **CORRECT**
- ✅ Server passthrough **FUNCTIONAL**
- ✅ Ready untuk integration dengan NATS cluster

**Timestamp**: 2024-10-13
**Version**: tick-mt5 v1.0.0
**Protocol**: Suho Binary Protocol v1
