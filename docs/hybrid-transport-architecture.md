# Hybrid Transport Architecture Specification

## Overview
Dual-channel communication system for high-volume, mission-critical trading data with automatic failover capabilities.

## Architecture Components

### 1. Primary Channel: WebSocket (Speed Priority)
- **Purpose**: Ultra-low latency data delivery
- **Capacity**: 50,000+ messages/second per connection
- **Use Cases**: Live tick data, real-time trading signals, instant order confirmations

### 2. Backup Channel: Kafka (Reliability Priority)
- **Purpose**: Guaranteed delivery and data persistence
- **Capacity**: 100,000+ messages/second with partitioning
- **Use Cases**: All critical data backup, gap recovery, audit trail

### 3. Automatic Failover System
- **Sequence Tracking**: Every message has unique sequence number
- **Gap Detection**: Monitors for missing sequences in WebSocket stream
- **Circuit Breaker**: Automatic switch to Kafka when WebSocket fails
- **Recovery**: Automatic WebSocket reconnection with gap filling

## Data Flow Design

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Data Source   │───▶│ Dual Channel │───▶│   Consumer      │
│  (MT5/Service)  │    │  Publisher   │    │   (Frontend/    │
└─────────────────┘    └──────────────┘    │    Service)     │
                              │             └─────────────────┘
                              ▼
                    ┌─────────────────┐
                    │ Sequence Tracker│
                    │ & Gap Detector  │
                    └─────────────────┘
```

## Implementation Strategy

### Phase 1: Core Services (High Volume)
1. **Tick Data Pipeline**: MT5 ↔ Signal Generator ↔ Risk Management
2. **Trading Decision Flow**: Signal Generator ↔ Portfolio Manager ↔ Order Execution
3. **Real-time Updates**: Any Service ↔ Frontend (WebSocket primary)

### Phase 2: Business Services (Medium Volume)
1. **User Management**: Standard HTTP with connection pooling
2. **Analytics**: Kafka for batch processing, WebSocket for real-time charts
3. **Notifications**: WebSocket for instant alerts, HTTP for confirmations

### Phase 3: Support Services (Low Volume)
1. **Configuration**: Simple HTTP POST
2. **Logging**: Kafka async
3. **Monitoring**: HTTP with caching

## Performance Characteristics

### Expected Throughput
- **WebSocket Primary**: 2-5ms latency, 50K msg/s per connection
- **Kafka Backup**: 10-50ms latency, 100K+ msg/s total
- **Failover Time**: < 100ms automatic detection and switch
- **Recovery Time**: < 1 second with gap filling

### Resource Requirements
- **Memory**: 2GB per service for message buffering
- **CPU**: 20% overhead for dual-channel management
- **Network**: 2x bandwidth usage during normal operation
- **Storage**: Kafka retention for 7 days minimum

## Error Handling & Recovery

### Automatic Failover Triggers
1. WebSocket connection lost (> 3 consecutive failures)
2. Message sequence gap detected (> 10 missing sequences)
3. Latency threshold exceeded (> 500ms for 3 consecutive messages)
4. Circuit breaker activation (error rate > 5% in 30 seconds)

### Recovery Procedures
1. **Gap Recovery**: Request missing sequences from Kafka
2. **Connection Recovery**: Exponential backoff reconnection (100ms → 10s)
3. **State Synchronization**: Verify last received sequence before resuming
4. **Health Check**: Continuous monitoring of both channels

## Security & Monitoring

### Security Features
- TLS 1.3 for all WebSocket connections
- SASL/SCRAM authentication for Kafka
- Message encryption for sensitive data
- Connection rate limiting

### Monitoring Points
- Message sequence integrity
- Channel health status
- Failover frequency and duration
- Performance metrics (latency, throughput)
- Error rates and types