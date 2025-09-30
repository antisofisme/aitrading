# Central Hub Architecture Refactor Plan

**Date**: September 30, 2025
**Status**: Planning Phase
**Objective**: Reorganize Central Hub for cleaner, more logical architecture

## 🎯 **CURRENT PROBLEMS**

### **1️⃣ Confusing Structure**
```
central-hub/
├── service/          # ❌ Unclear naming (what kind of service?)
├── config/           # ❌ Separate from service code
├── shared/           # ❌ Mixed components and configs
└── contracts/        # ✅ OK
```

### **2️⃣ Mixed Responsibilities**
- `shared/` contains both **code components** AND **configuration logic**
- `config/` separated from `service/` even though they're part of same application
- No clear separation between **static** vs **hot-reload** configurations

## 🏗️ **NEW ARCHITECTURE DESIGN**

### **📁 Target Structure**
```
central-hub/
├── core/                    # ✨ Central Hub application
│   ├── api/                # REST API endpoints
│   ├── business/           # Business logic
│   ├── config/             # ✨ Central Hub's own configuration
│   ├── middleware/         # FastAPI middlewares
│   └── app.py              # Main application entry
│
├── shared/                  # ✨ Everything shared with other services
│   ├── components/         # Code components (hot-reload distributed)
│   │   ├── js/            # JavaScript utilities & classes
│   │   │   ├── utils/     # BaseService, ComponentSubscriber
│   │   │   ├── adapters/  # NATSKafkaAdapter, etc.
│   │   │   └── transport/ # TransferManager
│   │   ├── proto/         # Protocol Buffer definitions
│   │   ├── suho-binary/   # Binary protocol implementations
│   │   └── utils/         # Cross-language utilities
│   │
│   ├── static/             # ✨ Static configurations (startup)
│   │   ├── database/      # DB connection templates
│   │   ├── security/      # JWT secrets, API keys templates
│   │   └── services/      # Service-specific static configs
│   │       ├── api-gateway.json
│   │       ├── trading-engine.json
│   │       └── analytics.json
│   │
│   └── hot-reload/         # ✨ Dynamic configurations (runtime)
│       ├── business/      # Business rules (rate limits, CORS)
│       ├── features/      # Feature flags
│       └── routing/       # Dynamic routing rules
│
└── contracts/              # API contracts & validation schemas
    ├── central-hub/       # Central Hub API contracts
    ├── api-gateway/       # API Gateway contracts
    └── shared/            # Shared contract definitions
```

## 🔄 **DISTRIBUTION FLOWS**

### **1️⃣ Code Components Flow**
```
shared/components/
    ↓ (hot-reload via ComponentSubscriber)
Other Services
    ↓ (import and use)
Shared Functionality
```

### **2️⃣ Static Configuration Flow**
```
shared/static/
    ↓ (HTTP API at startup)
Services ConfigService.getConfig()
    ↓ (cache locally)
Service Operations
```

### **3️⃣ Hot-Reload Configuration Flow**
```
shared/hot-reload/
    ↓ (NATS broadcast)
Services Runtime Update
    ↓ (live apply)
Dynamic Configuration Changes
```

## 📝 **KEY PRINCIPLES**

### **🎯 Clear Separation of Concerns**
- **`core/`**: What Central Hub **IS** (its own application code)
- **`shared/`**: What Central Hub **MANAGES** (resources for other services)
- **`contracts/`**: What Central Hub **DEFINES** (API interfaces)

### **🏗️ Unified Shared Resources**
- All shared resources in one place (`shared/`)
- Clear categorization: `components/`, `static/`, `hot-reload/`
- Consistent distribution mechanisms

### **📊 Logical Grouping**
- Configuration by **type** (static vs hot-reload)
- Components by **language/purpose** (js, proto, utils)
- Services by **name** (api-gateway, trading-engine)

## 🚀 **BENEFITS OF NEW ARCHITECTURE**

### **✅ Developer Experience**
- **Clear mental model**: Easy to understand what goes where
- **Predictable structure**: Consistent patterns across all services
- **Self-documenting**: Folder names explain their purpose

### **✅ Operational Benefits**
- **Easier debugging**: Clear separation of configuration types
- **Better scalability**: Add new services without restructuring
- **Maintainable**: Less confusion about file locations

### **✅ Technical Benefits**
- **Clean distribution**: Each type has its own flow
- **Version control**: Clear change tracking per configuration type
- **Testing**: Easier to test static vs dynamic configs separately

## 📋 **MIGRATION PLAN**

### **Phase 1: Documentation** ✅
- [x] Create this architecture plan
- [ ] Update system documentation
- [ ] Review with team

### **Phase 2: Structure Refactor**
- [ ] Rename `service/` → `core/`
- [ ] Move `config/` → `core/config/`
- [ ] Reorganize `shared/` with subfolders
- [ ] Update Docker configurations

### **Phase 3: Code Updates**
- [ ] Update import paths
- [ ] Update API endpoints
- [ ] Update distribution logic
- [ ] Update tests

### **Phase 4: Validation**
- [ ] Test all services still work
- [ ] Verify hot-reload functionality
- [ ] Validate configuration distribution
- [ ] Update documentation

## ⚠️ **RISKS & MITIGATION**

### **Risk 1: Breaking Changes**
- **Mitigation**: Incremental migration with backward compatibility
- **Strategy**: Keep old paths working during transition

### **Risk 2: Complex Migration**
- **Mitigation**: Clear step-by-step plan with rollback points
- **Strategy**: Test each phase thoroughly before proceeding

### **Risk 3: Team Confusion**
- **Mitigation**: Clear documentation and communication
- **Strategy**: Training session after migration complete

## 🎯 **SUCCESS CRITERIA**

1. **All services work** with new structure
2. **Hot-reload functionality** preserved
3. **Configuration distribution** working correctly
4. **Developer onboarding** faster due to clearer structure
5. **Zero downtime** during migration

---

**Next Steps**: Get team approval → Start Phase 2 (Structure Refactor)