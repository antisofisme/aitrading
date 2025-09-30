# Project Documentation - Suho AI Trading Platform

## 📚 Documentation Overview

This `docs/` folder contains comprehensive documentation for all components of the Suho AI Trading Platform backend infrastructure.

## 📂 Documentation Structure

```
docs/
├── README.md                   # 📖 This documentation index
└── central-hub/                # 🎯 Central Hub Service Documentation
    ├── README.md               #    Main Central Hub documentation
    ├── SHARED_ARCHITECTURE.md  #    Shared folder architecture guide
    ├── CONTRACTS_GUIDE.md      #    API contracts documentation
    ├── API_DOCUMENTATION.md    #    Complete API reference
    └── SHARED_PROTOCOLS.md     #    Protocol definitions (Binary, Protobuf)
```

## 🎯 Service Documentation

### Central Hub Service
**Location**: `docs/central-hub/`

Central Hub adalah jantung koordinasi dari seluruh platform yang menyediakan:
- Service Discovery & Registration
- Configuration Management (Static & Hot-reload)
- Database Integration Hub
- Health Monitoring
- Contract Validation
- Multi-protocol Communication

**Key Files**:
- **`README.md`** - Complete service overview, quick start, dan integration guide
- **`SHARED_ARCHITECTURE.md`** - Detailed shared folder structure dan configuration patterns
- **`CONTRACTS_GUIDE.md`** - API contracts untuk service communication
- **`API_DOCUMENTATION.md`** - Comprehensive API reference dengan examples

## 🚀 Quick Navigation

### Getting Started
1. **Central Hub Overview** - [`central-hub/README.md`](central-hub/README.md)
2. **API Reference** - [`central-hub/API_DOCUMENTATION.md`](central-hub/API_DOCUMENTATION.md)
3. **Architecture Guide** - [`central-hub/SHARED_ARCHITECTURE.md`](central-hub/SHARED_ARCHITECTURE.md)

### Integration Guides
- **Service Registration** - How to register services with Central Hub
- **Configuration Management** - Using static dan hot-reload configs
- **Health Monitoring** - Implementing health checks
- **Contract Validation** - API contract enforcement

### Development Resources
- **Docker Integration** - Container deployment guides
- **Performance Monitoring** - Metrics dan optimization
- **Troubleshooting** - Common issues dan solutions
- **Best Practices** - Recommended patterns dan practices

## 🔗 External Resources

- **Main Project**: `/mnt/g/khoirul/aitrading/project3/backend/`
- **Central Hub Source**: `01-core-infrastructure/central-hub/`
- **Docker Compose**: `docker-compose.yml`
- **Environment Config**: `.env`

## 📋 Service Status

| Service | Status | Port | Documentation |
|---------|--------|------|---------------|
| Central Hub | ✅ Active | 7000 | [`central-hub/`](central-hub/) |
| API Gateway | 🔄 In Development | 8000 | _Coming Soon_ |
| Trading Engine | 📋 Planned | 8080 | _Coming Soon_ |
| Market Data | 📋 Planned | 8090 | _Coming Soon_ |

## 🛠️ Contributing to Documentation

When adding new services atau components:

1. **Create service folder** dalam `docs/`
2. **Add README.md** dengan service overview
3. **Include API documentation** untuk external interfaces
4. **Document configuration** dan deployment procedures
5. **Update this index** dengan new service links

### Documentation Standards
- **Clear structure** dengan consistent formatting
- **Practical examples** untuk quick implementation
- **Troubleshooting sections** untuk common issues
- **API references** dengan request/response examples
- **Architecture diagrams** where applicable

## 📞 Support

For questions atau issues:
- **Central Hub Health**: http://localhost:7000/health
- **Service Status**: http://localhost:7000/
- **API Docs**: http://localhost:7000/metrics

---

**📚 Comprehensive Documentation untuk Scalable AI Trading Platform**