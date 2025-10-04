# Central Hub SDK

Official client SDKs for integrating services with Suho Central Hub.

## 📁 Directory Structure

```
sdk/
├── python/                  # Python SDK
│   ├── central_hub_sdk/    # Package source
│   │   ├── __init__.py
│   │   └── client.py       # CentralHubClient implementation
│   ├── setup.py            # Package configuration
│   ├── README.md           # Python SDK docs
│   └── MANIFEST.in
│
├── nodejs/                  # Node.js SDK
│   ├── src/
│   │   ├── index.js        # Package entry point
│   │   └── CentralHubClient.js  # Client implementation
│   ├── package.json        # NPM configuration
│   └── README.md           # Node.js SDK docs
│
└── README.md               # This file
```

## 🚀 Quick Start

### Python Services

```bash
# Install from local source (development)
cd /path/to/central-hub/sdk/python
pip install -e .

# Use in your service
from central_hub_sdk import CentralHubClient

client = CentralHubClient(
    service_name="my-service",
    service_type="data-collector",
    version="1.0.0"
)
await client.register()
```

### Node.js Services

```bash
# Install from local source (development)
cd /path/to/central-hub/sdk/nodejs
npm link

# In your service
npm link @suho/central-hub-sdk

// Use in your service
const { CentralHubClient } = require('@suho/central-hub-sdk');

const client = new CentralHubClient({
    serviceName: 'my-service',
    baseURL: 'http://suho-central-hub:7000'
});
await client.register(serviceInfo);
```

## 📦 SDK Features

Both SDKs provide:

- ✅ **Service Registration**: Register your service with Central Hub
- ✅ **Health Reporting**: Automatic heartbeat with metrics
- ✅ **Service Discovery**: Find and communicate with other services
- ✅ **Configuration Management**: Fetch centralized configuration
- ✅ **Retry Logic**: Automatic retry with exponential backoff
- ✅ **Event Handling**: Event-driven architecture (Node.js)
- ✅ **Type Safety**: Full typing support

## 🔧 Docker Integration

### Python Dockerfile

```dockerfile
# Copy and install Central Hub SDK
COPY 01-core-infrastructure/central-hub/sdk/python/ /tmp/central-hub-sdk/
RUN pip install --no-cache-dir /tmp/central-hub-sdk/ && rm -rf /tmp/central-hub-sdk

# Install other requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

### Node.js Dockerfile

```dockerfile
# Copy Central Hub SDK
COPY 01-core-infrastructure/central-hub/sdk/nodejs/ /tmp/central-hub-sdk/

# Install SDK
WORKDIR /tmp/central-hub-sdk
RUN npm install

# Link SDK globally
RUN npm link

# Install your service
WORKDIR /app
COPY package.json .
RUN npm link @suho/central-hub-sdk && npm install
```

### docker-compose.yml

```yaml
services:
  my-service:
    build:
      context: .  # Root directory to access SDK
      dockerfile: path/to/service/Dockerfile
```

## 🏗️ Architecture Pattern

```
┌─────────────────────────────────────────┐
│         Central Hub Service             │
│  ┌──────────────────────────────────┐  │
│  │   Official SDK Packages          │  │
│  │   - Python: central-hub-sdk      │  │
│  │   - Node.js: @suho/central-hub   │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
                   ↑
                   │ HTTP/REST
          ┌────────┴────────┐
          │                 │
┌─────────▼──────┐  ┌──────▼──────────┐
│  Python Service │  │  Node.js Service│
│  (uses SDK)     │  │  (uses SDK)     │
└─────────────────┘  └─────────────────┘
```

## 📋 Best Practices

### 1. Always Install from Central Hub

**❌ Wrong**:
```python
# DON'T: Copy client code to each service
from local_client import CentralHubClient
```

**✅ Correct**:
```python
# DO: Install SDK from Central Hub
from central_hub_sdk import CentralHubClient
```

### 2. Handle Registration Failures

```python
try:
    await client.register()
except Exception as e:
    logger.warning(f"Central Hub unavailable: {e}")
    # Service continues standalone
```

### 3. Always Deregister on Shutdown

```python
try:
    await service.run()
finally:
    await client.deregister()
```

## 🔄 Version Management

### Semantic Versioning

- **Major (1.x.x)**: Breaking API changes
- **Minor (x.1.x)**: New features (backward compatible)
- **Patch (x.x.1)**: Bug fixes

### Upgrading Services

```bash
# Python
pip install --upgrade central-hub-sdk

# Node.js
npm update @suho/central-hub-sdk
```

## 🛠️ Development

### Publishing to Private Registry (Future)

**Python (PyPI)**:
```bash
cd sdk/python
python setup.py sdist bdist_wheel
twine upload --repository-url https://pypi.suho.local dist/*
```

**Node.js (NPM)**:
```bash
cd sdk/nodejs
npm publish --registry https://npm.suho.local
```

## 📝 Migration Guide

### From Old Shared Directory

**Before** (`/00-data-ingestion/shared/central_hub_client.py`):
```python
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
from central_hub_client import CentralHubClient
```

**After** (SDK):
```python
# No path manipulation needed!
from central_hub_sdk import CentralHubClient
```

## 🐛 Troubleshooting

### SDK Not Found

**Problem**: `ModuleNotFoundError: No module named 'central_hub_sdk'`

**Solution**: Verify SDK is installed in Dockerfile:
```dockerfile
COPY 01-core-infrastructure/central-hub/sdk/python/ /tmp/central-hub-sdk/
RUN pip install /tmp/central-hub-sdk/
```

### Import Errors

**Problem**: `AttributeError: module has no attribute 'CentralHubClient'`

**Solution**: Check `__init__.py` exports:
```python
from .client import CentralHubClient
__all__ = ['CentralHubClient']
```

## 📄 License

MIT License - Copyright (c) 2025 Suho Trading System

## 🤝 Contributing

1. Update SDK code in `/sdk/python/` or `/sdk/nodejs/`
2. Update version in `setup.py` or `package.json`
3. Test with example service
4. Update CHANGELOG
5. Rebuild affected services

## 📚 Documentation

- [Python SDK Documentation](python/README.md)
- [Node.js SDK Documentation](nodejs/README.md)
- [Central Hub API Reference](../../docs/API.md)
