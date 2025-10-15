# Central Hub SDK - Python

Official Python client library for integrating services with Suho Central Hub.

## 🚀 Installation

### From Local Source (Development)

```bash
cd /path/to/central-hub/sdk/python
pip install -e .
```

### From Package (Production)

```bash
pip install central-hub-sdk
```

## 📖 Quick Start

```python
import asyncio
from central_hub_sdk import CentralHubClient

async def main():
    # Initialize client
    client = CentralHubClient(
        service_name="my-service",
        service_type="data-collector",
        version="1.0.0",
        capabilities=[
            "data-collection",
            "real-time-streaming"
        ],
        metadata={
            "source": "polygon.io",
            "mode": "live"
        }
    )

    # Register with Central Hub
    await client.register()

    # Start automatic heartbeat (every 30s)
    asyncio.create_task(client.start_heartbeat_loop())

    # Your service logic here...
    await asyncio.sleep(3600)

    # Deregister on shutdown
    await client.deregister()

if __name__ == "__main__":
    asyncio.run(main())
```

## 🔧 Configuration

### Environment Variables

```bash
CENTRAL_HUB_URL=http://suho-central-hub:7000  # Central Hub base URL
HEARTBEAT_INTERVAL=30                         # Heartbeat interval in seconds
```

### Client Options

```python
client = CentralHubClient(
    service_name="my-service",           # Required: Service identifier
    service_type="data-collector",       # Required: Service type
    version="1.0.0",                     # Required: Service version
    capabilities=[...],                  # Optional: Service capabilities
    metadata={...},                      # Optional: Additional metadata
    central_hub_url="http://...",        # Optional: Override Central Hub URL
    heartbeat_interval=30                # Optional: Heartbeat interval (seconds)
)
```

## 📋 API Reference

### Registration

```python
# Register service with Central Hub
await client.register()

# Deregister service (call on shutdown)
await client.deregister()
```

### Health Reporting

```python
# Send heartbeat with metrics
await client.send_heartbeat(metrics={
    "cpu_usage": 45.2,
    "memory_usage": 1024,
    "requests_processed": 1500
})

# Start automatic heartbeat loop
asyncio.create_task(client.start_heartbeat_loop())
```

### Service Properties

```python
# Check if registered
if client.registered:
    print(f"Service ID: {client.service_id}")
    print(f"Service Name: {client.service_name}")

# Get service information
info = client.get_service_info()
```

## 🏗️ Architecture

```
Your Service
    ↓
CentralHubClient (SDK)
    ↓ HTTP/REST
Central Hub Service
    ↓
Service Registry
```

## 🔍 Error Handling

```python
try:
    await client.register()
except Exception as e:
    logger.error(f"Registration failed: {e}")
    # Service continues without Central Hub (optional)
```

## 📊 Metrics & Monitoring

The SDK automatically reports:

- ✅ Service health status
- ✅ Uptime
- ✅ Custom metrics (via `send_heartbeat`)
- ✅ Connection status

## 🛡️ Best Practices

1. **Always deregister on shutdown**:
   ```python
   try:
       await service.run()
   finally:
       await client.deregister()
   ```

2. **Handle registration failures gracefully**:
   ```python
   try:
       await client.register()
   except Exception:
       logger.warning("Central Hub unavailable, running standalone")
   ```

3. **Use heartbeat for health reporting**:
   ```python
   await client.send_heartbeat(metrics={
       "active_connections": connection_count,
       "queue_size": queue.qsize()
   })
   ```

## 🐛 Debugging

Enable debug logging:

```python
import logging
logging.getLogger('central_hub_sdk').setLevel(logging.DEBUG)
```

## 📝 Changelog

### v1.0.0 (2025-10-04)
- Initial release
- Service registration & discovery
- Automatic heartbeat
- Health reporting
- Metrics collection

## 📄 License

MIT License - Copyright (c) 2025 Suho Trading System

## 🤝 Support

For issues and questions:
- GitHub Issues: https://github.com/suho-trading/central-hub-sdk/issues
- Documentation: https://docs.suho-trading.com/central-hub-sdk
