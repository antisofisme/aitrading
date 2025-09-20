# Port Allocation Reference - Hybrid AI Trading System

## 🏗️ **Complete Port Allocation Matrix**

### **Client Side Services (Local PC)**
| Service | Port | Status | Purpose |
|---------|------|--------|---------|
| metatrader-connector | 9001 | Active | MT5 data bridge |
| data-collector | 9002 | Active | Multi-source data aggregation |
| market-monitor | 9003 | Active | Real-time market analysis |
| config-manager | 9004 | Active | Local configuration management |

### **Server Side Services (Cloud/Remote)**

#### **Core Infrastructure Services (8000-8009)**
| Service | Port | Status | Purpose | Phase |
|---------|------|--------|---------|-------|
| api-gateway | 8000 | Active | AI-aware routing, authentication | Phase 1 |
| data-bridge | 8001 | Active | Enhanced MT5 integration, multi-source | Phase 1 |
| performance-analytics | 8002 | Active | AI-specific metrics, performance tracking | Phase 1 |
| ai-orchestration | 8003 | Active | Multi-model coordination | Phase 1 |
| **RESERVED** | 8004 | Reserved | Future expansion | - |
| **RESERVED** | 8005 | Reserved | Future expansion | - |
| **RESERVED** | 8006 | Reserved | Future expansion | - |
| trading-engine | 8007 | Active | AI-driven trading decisions | Phase 1 |
| database-service | 8008 | Active | Multi-DB support (PostgreSQL, ClickHouse, etc.) | Phase 1 |
| user-service | 8009 | Active | Multi-tenant support | Phase 1 |

#### **AI/ML Pipeline Services (8011-8016)**
| Service | Port | Status | Purpose | Phase |
|---------|------|--------|---------|-------|
| **RESERVED** | 8010 | Reserved | Future AI expansion | - |
| feature-engineering | 8011 | Active | Advanced technical indicators | Phase 2 |
| ml-supervised | 8012 | Active | XGBoost, LightGBM models | Phase 2 |
| ml-deep-learning | 8013 | Active | LSTM, Transformer networks | Phase 2 |
| pattern-validator | 8014 | Active | AI pattern verification | Phase 2 |
| telegram-service | 8015 | Active | Real-time notifications | Phase 3 |
| backtesting-engine | 8016 | Active | Strategy validation | Post-Launch |

#### **Compliance & Regulatory Services (8017-8019)**
| Service | Port | Status | Purpose | Phase |
|---------|------|--------|---------|-------|
| compliance-monitor | 8017 | Active | Real-time regulatory monitoring | Phase 2 |
| audit-trail | 8018 | Active | Immutable audit logging | Phase 2 |
| regulatory-reporting | 8019 | Active | Automated compliance reporting | Phase 3 |

### **Infrastructure Services (Non-HTTP)**
| Service | Port | Status | Purpose |
|---------|------|--------|---------|
| kafka | 9092 | Active | Event streaming |
| zookeeper | 2181 | Active | Kafka coordination |
| elasticsearch | 9200, 9300 | Active | Audit log storage |
| jaeger | 16686, 14268 | Active | Distributed tracing |
| airflow | 8080 | Active | Workflow orchestration |

## 🔍 **Port Conflict Resolution**

### **Previous Conflicts Resolved**
- ✅ **No Port 8010 Conflict**: Port 8010 is reserved for future expansion
- ✅ **Performance Analytics Correct**: Already properly allocated to port 8002
- ✅ **Compliance Services Added**: All compliance services (8017-8019) properly documented

### **Port Allocation Strategy**
- **8000-8009**: Core infrastructure and proven services
- **8010**: Reserved for future AI expansion
- **8011-8016**: AI/ML pipeline services
- **8017-8019**: Compliance and regulatory services
- **8020+**: Available for future services

## 📊 **Service Dependencies Matrix**

### **Phase 1 Dependencies**
```
api-gateway (8000) ← Client requests
├── database-service (8008)
├── data-bridge (8001)
├── trading-engine (8007)
├── ai-orchestration (8003)
└── performance-analytics (8002)
```

### **Phase 2 Dependencies**
```
ai-orchestration (8003) ← AI pipeline
├── feature-engineering (8011)
├── ml-supervised (8012)
├── ml-deep-learning (8013)
├── pattern-validator (8014)
├── compliance-monitor (8017) ← NEW
└── audit-trail (8018) ← NEW
```

### **Phase 3 Dependencies**
```
telegram-service (8015) ← User notifications
├── trading-engine (8007)
├── performance-analytics (8002)
├── compliance-monitor (8017)
└── regulatory-reporting (8019) ← NEW
```

## 🛡️ **Security Considerations**

### **Public Access**
- **Port 8000**: API Gateway (public, secured with OAuth2/JWT)

### **Internal Network Only**
- **Ports 8001-8019**: All internal services
- **VPN Required**: For external access to internal services

### **Compliance Network**
- **Ports 8017-8019**: Isolated compliance network segment
- **Enhanced Security**: Additional encryption and access controls

## 📈 **Performance Specifications**

### **Latency Requirements**
| Service | Target Latency | Max Latency |
|---------|---------------|-------------|
| api-gateway (8000) | <10ms | <50ms |
| trading-engine (8007) | <50ms | <200ms |
| feature-engineering (8011) | <50ms | <100ms |
| ml-supervised (8012) | <100ms | <200ms |
| compliance-monitor (8017) | <500ms | <1000ms |

### **Throughput Requirements**
| Service | Target RPS | Max RPS |
|---------|-----------|---------|
| api-gateway (8000) | 1000 | 5000 |
| data-bridge (8001) | 100 | 500 |
| feature-engineering (8011) | 200 | 1000 |

## ✅ **Validation Checklist**

### **Port Allocation Validation**
- [x] No port conflicts across all services
- [x] All services have unique port assignments
- [x] Port ranges logically organized by function
- [x] Compliance services properly isolated
- [x] Future expansion ports reserved

### **Service Integration Validation**
- [x] All dependencies documented
- [x] Service communication patterns defined
- [x] Security boundaries established
- [x] Performance requirements specified

### **Documentation Validation**
- [x] Master plan updated with compliance services
- [x] Technical architecture reflects all ports
- [x] Phase plans include compliance development
- [x] Cost calculations include compliance infrastructure

## 🎯 **Implementation Status**

### **Phase 1 (Complete)**
- ✅ Core services (8000-8009) operational
- ✅ Basic infrastructure validated
- ✅ Performance benchmarks met

### **Phase 2 (In Progress)**
- ✅ AI services (8011-8014) planned
- ✅ Compliance services (8017-8018) structured
- 🔄 Implementation in progress

### **Phase 3 (Planned)**
- 📋 Telegram service (8015) planned
- 📋 Regulatory reporting (8019) planned
- 📋 User features integration

### **Post-Launch (Future)**
- 📋 Backtesting engine (8016) enhancement
- 📋 Additional AI services (8020+)
- 📋 Advanced compliance features

---

**Status**: ✅ **PORT ALLOCATION CONFLICTS RESOLVED**
**Last Updated**: December 2024
**Next Review**: Phase 2 completion