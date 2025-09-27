# Output Contract: API Gateway → Data Bridge

## Purpose
API Gateway forwards raw Suho Binary Protocol data from Client-MT5 to Data Bridge for binary-to-Protocol Buffers conversion and further processing.

## Protocol
**Format**: Suho Binary Protocol (no conversion at API Gateway)
**Transport**: NATS+Kafka (high volume) / HTTP (low volume)
**Authentication**: Service-to-service authentication

## Data Flow
1. API Gateway receives Suho Binary from Client-MT5
2. API Gateway → Data Bridge (binary passthrough, no conversion)
3. Data Bridge handles conversion and routing to backend services

## Message Types Forwarded
- **PRICE_STREAM** (0x01): Real-time market data
- **ACCOUNT_PROFILE** (0x02): Account information
- **TRADING_COMMAND** (0x03): Trading requests
- **EXECUTION_CONFIRM** (0x04): Trade confirmations
- **HEARTBEAT** (0x06): Connection monitoring

## Data Structure (Raw Binary)
```cpp
struct SuhoBinaryPacket {
    SuhoBinaryHeader header;    // 16 bytes
    SuhoBinaryData   data;      // 128 bytes
    // Total: 144 bytes fixed size
};
```

## Transport Methods

### **High Volume Data (NATS+Kafka HYBRID)**
**Message Types**: `price_stream`, `trading_command`
**Architecture**: Simultaneous dual transport (not fallback)

**NATS Transport**:
- **Subject**: `data-bridge.binary-input`
- **Purpose**: Real-time processing (speed priority)
- **Latency**: <1ms

**Kafka Transport**:
- **Topic**: `data-bridge-binary-input`
- **Purpose**: Durability & replay capability (reliability priority)
- **Partitioning**: User-based consistent hashing

### **Low Volume Data (HTTP)**
**Message Types**: `account_profile`, `execution_confirm`, `heartbeat`
**Endpoint**: `POST /api/data-bridge/binary-input`
**Content-Type**: `application/octet-stream`
**Headers**:
- `X-User-ID`: Client user identifier
- `X-Protocol`: `suho-binary`
- `X-Channel`: `trading` or `price-stream`

## Message Metadata

### **NATS Payload (Real-time)**
```json
{
  "message": "<raw_binary_data>",
  "metadata": {
    "userId": "user123",
    "source": "client-mt5",
    "protocol": "suho-binary",
    "transport": "nats",
    "purpose": "real-time",
    "channel": "trading|price-stream",
    "timestamp": 1640995200000,
    "correlationId": "uuid-v4",
    "noConversion": true
  }
}
```

### **Kafka Payload (Durability)**
```json
{
  "message": "<raw_binary_data>",
  "metadata": {
    "userId": "user123",
    "source": "client-mt5",
    "protocol": "suho-binary",
    "transport": "kafka",
    "purpose": "durability",
    "channel": "trading|price-stream",
    "timestamp": 1640995200000,
    "correlationId": "uuid-v4",
    "noConversion": true
  }
}
```

### **HTTP Headers**
```
Content-Type: application/octet-stream
X-Protocol: suho-binary
X-User-ID: user123
X-Message-Type: price_stream
X-Correlation-ID: uuid-v4
```

## Performance Requirements

### **High Volume (NATS+Kafka HYBRID)**
- **NATS Latency**: <1ms publish time (real-time processing)
- **Kafka Latency**: <5ms publish time (durability storage)
- **Throughput**: 5000+ messages/second aggregate
- **Architecture**: Simultaneous dual transport
- **NATS**: Speed-optimized for immediate processing
- **Kafka**: Durability-optimized for replay & backup

### **Low Volume (HTTP)**
- **Latency**: <5ms request time
- **Throughput**: 100+ messages/second
- **Reliability**: HTTP retry with exponential backoff
- **Size**: Fixed 144-byte packets

## Error Handling

### **NATS Failure Handling**
- **Connection lost**: Reconnect with circuit breaker
- **Subject unavailable**: Retry with exponential backoff
- **Publish failure**: Log error, continue (Kafka still provides durability)

### **Kafka Failure Handling**
- **Producer failure**: Dead letter queue
- **Partition unavailable**: Retry with different partition
- **Broker down**: Log error, continue (NATS still provides real-time)

### **Hybrid Resilience**
- **NATS down**: Real-time processing affected, durability maintained via Kafka
- **Kafka down**: Durability affected, real-time processing maintained via NATS
- **Both down**: Graceful degradation to HTTP transport

### **HTTP Failure Handling**
- **Data Bridge unavailable**: Exponential backoff retry
- **Timeout**: 5-second timeout, then circuit breaker
- **Invalid response**: Log and retry once

## Future Considerations
This contract serves as bridge architecture. When Data Bridge is optimized, API Gateway may resume direct routing to multiple backend services while maintaining binary protocol compatibility.

## Related Contracts
- Input: `contracts/inputs/from-client-mt5.md`
- Internal: `contracts/internal/bidirectional-routing.md`