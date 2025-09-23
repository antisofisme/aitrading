# Services Breakdown (Berdasarkan Plan2)

## 🏗️ Service Architecture Overview

Berdasarkan plan2, sistem memiliki **15 microservices** yang terbagi dalam:

### **Core Services (AI Trading Heritage) - Ports 8000-8009**
Diambil dan enhanced dari ai_trading project yang sudah proven

### **Business Services (New) - Ports 8021-8025**
Services baru untuk revenue generation dan multi-tenant support

---

## 🔧 Core Services (AI Trading Heritage)

### **1. API Gateway (Port 8000)**
**Basis**: ai_trading API Gateway + Business Enhancement
**Purpose**: Entry point dengan multi-tenant routing

#### **AI Trading Heritage**:
- Basic authentication, rate limiting, routing
- Proven service coordination

#### **Business Enhancement**:
- Multi-tenant authentication
- Subscription-based rate limiting
- Intelligent routing dengan user tier management
- Billing integration dan usage analytics

#### **Key Features**:
- JWT token validation dengan multi-tenant support
- Request/response logging per user
- API versioning untuk business tiers
- Error handling dengan business context

---

### **2. Data Bridge (Port 8001)**
**Basis**: ai_trading Data Bridge (18+ ticks/second) + Business Scaling
**Purpose**: MT5 integration dengan per-user data isolation

#### **AI Trading Heritage**:
- Production-validated MT5 connectivity
- Real-time processing (18 ticks/second baseline)
- WebSocket server untuk frontend

#### **Business Enhancement**:
- Per-user data streams dan isolation
- Multi-tenant data processing
- Usage billing tracking
- Performance SLAs (target: 50+ ticks/second)

#### **Key Components**:
- MT5 connection management per user
- Real-time data streaming dengan user context
- WebSocket server untuk multi-user frontend
- Data normalization dengan tenant isolation

---

### **3. Performance Analytics (Port 8002)**
**Basis**: ai_trading Basic Metrics + AI-Specific Enhancement
**Purpose**: AI-specific metrics dan model performance tracking

#### **Current State**: Basic metrics collection
#### **Enhanced Features**:
- AI-specific metrics collection
- Model performance tracking
- Multi-agent coordination metrics
- Business performance analytics

---

### **4. AI Orchestration (Port 8003)**
**Basis**: ai_trading OpenAI/DeepSeek Integration + Multi-Model Enhancement
**Purpose**: Hybrid ML pipeline coordination dengan ensemble methods

#### **AI Trading Heritage**:
- OpenAI, DeepSeek, Google AI integration
- Basic AI workflow coordination

#### **Enhancement**:
- Multi-model orchestrator
- Ensemble methods coordination
- Agent framework integration
- Cross-agent learning coordination

---

### **5. Deep Learning (Port 8004)**
**Basis**: New Service + AI Trading Integration
**Purpose**: Neural networks dan advanced AI processing

#### **Capabilities**:
- Neural network training dan inference
- Pattern recognition untuk trading
- Anomaly detection
- Predictive modeling dengan multi-agent input

---

### **6. AI Provider (Port 8005)**
**Basis**: ai_trading External AI Services + Cost Optimization
**Purpose**: External AI services integration dengan cost management

#### **Supported Providers**:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Google AI (Gemini)
- DeepSeek (custom models)

#### **Business Features**:
- Cost optimization per subscription tier
- Model fallback strategies
- Usage tracking untuk billing

---

### **7. ML Processing (Port 8006) + Database Service**
**Basis**: ai_trading Database Service + Traditional ML Enhancement
**Purpose**: Traditional machine learning + Multi-database coordination

#### **Database Component** (AI Trading Heritage):
- PostgreSQL, ClickHouse, DragonflyDB, Weaviate, ArangoDB
- Multi-DB support proven in production
- Connection pooling dan optimization

#### **ML Component** (New):
- Feature engineering
- Model training/inference
- Data preprocessing
- Hyperparameter optimization

---

### **8. Database Service (Port 8008)**
**Basis**: ai_trading Database Service (Dedicated)
**Purpose**: Dedicated multi-database management

#### **Supported Databases** (AI Trading Heritage):
- **PostgreSQL**: User data, configurations, subscription data
- **ClickHouse**: High-frequency trading data, analytics
- **DragonflyDB**: Caching layer
- **Weaviate**: Vector embeddings untuk AI
- **ArangoDB**: Graph relationships

#### **Business Enhancement**:
- Multi-tenant data isolation
- Subscription billing data management
- Usage tracking integration

---

### **9. Trading Engine (Port 8007)**
**Basis**: ai_trading Trading Logic + Multi-User Enhancement
**Purpose**: Core trading logic dengan multi-user isolation

#### **AI Trading Heritage**:
- Proven trading logic
- Order placement dan execution
- Risk management

#### **Business Enhancement**:
- Multi-user trading isolation
- Subscription-based features
- Performance SLAs
- Per-user trading limits

---

### **10. User Service (Port 8009)**
**Basis**: New Service + AI Trading User Context
**Purpose**: User management dan authentication

#### **Core Features**:
- User registration/login
- Profile management
- Session management dengan JWT
- Permission handling
- Account settings dengan subscription context

---

## 💼 Business Services (New - Revenue Generation)

### **11. User Management (Port 8021)**
**Purpose**: Comprehensive user lifecycle management

#### **Features**:
- User registration dengan email verification
- Profile management dengan trading preferences
- Account settings dan customization
- User analytics untuk business intelligence

---

### **12. Subscription Service (Port 8022)**
**Purpose**: Billing, usage tracking, tier management

#### **Subscription Tiers** (dari Plan2):
- **Free Tier**: Basic predictions, limited API calls
- **Pro Tier**: Advanced features, higher quotas
- **Enterprise Tier**: Full access, unlimited usage

#### **Features**:
- Subscription tier management
- Usage quota enforcement
- Billing preparation infrastructure
- Rate limiting rules per tier

---

### **13. Payment Gateway (Port 8023)**
**Purpose**: Midtrans integration + Indonesian payments

#### **Features**:
- Midtrans payment processing
- Indonesian payment methods
- Invoice generation
- Payment status tracking
- Subscription billing automation

---

### **14. Notification Service (Port 8024)**
**Purpose**: Multi-user Telegram bot management

#### **AI Trading Heritage Enhancement**:
- Enhanced dari ai_trading Telegram bot (18+ commands)
- Multi-user support dengan user context
- Agent coordination notifications

#### **Features**:
- Multi-tenant Telegram bot management
- Real-time trading alerts per user
- Agent-driven notifications
- Subscription-based notification features

---

### **15. Billing Service (Port 8025)**
**Purpose**: Invoice generation + payment processing

#### **Features**:
- Automated invoice generation
- Usage-based billing calculation
- Payment processing coordination
- Revenue tracking dan analytics

---

## 🔄 Service Communication Patterns

### **Core Service Dependencies**:
```
API Gateway (8000) → All Services (routing)
Data Bridge (8001) → Database Service (8008) (store market data)
Performance Analytics (8002) → All Services (collect metrics)
AI Services (8003-8005) → Database Service (8008) + AI Provider
Trading Engine (8007) → Database Service (8008) + Data Bridge (8001)
User Service (8009) → Database Service (8008)
```

### **Business Service Dependencies**:
```
User Management (8021) → Database Service (8008)
Subscription Service (8022) → User Management (8021) + Database Service
Payment Gateway (8023) → Subscription Service (8022) + External APIs
Notification Service (8024) → User Management (8021) + Telegram API
Billing Service (8025) → Subscription Service (8022) + Payment Gateway
```

### **Cross-Service Integration**:
```
API Gateway (8000) → Business Services (rate limiting, authentication)
All Services → Performance Analytics (8002) (metrics collection)
All Services → Notification Service (8024) (alerts dan updates)
```

## 📊 Performance Requirements (dari Plan2)

### **AI Services Performance**:
- **AI Decision Making**: <15ms
- **Order Execution**: <1.2ms
- **Data Processing**: 50+ ticks/second
- **System Availability**: 99.99%

### **Business Services Performance**:
- **API Response**: <50ms untuk business endpoints
- **Rate Limiting**: Per subscription tier enforcement
- **Usage Tracking**: Real-time untuk billing accuracy
- **Subscription Enforcement**: Perfect tier compliance

### **Database Performance**:
- **PostgreSQL**: <10ms query response
- **ClickHouse**: <100ms analytics query
- **DragonflyDB**: <1ms cache access
- **Multi-DB Coordination**: <200ms cross-database operations

## 🔒 Security Implementation

### **Service-to-Service Security**:
- JWT tokens untuk internal communication
- API keys untuk service authentication
- Rate limiting per service dan user
- Request validation dan sanitization

### **Business Security**:
- Multi-tenant data isolation
- Subscription tier access control
- Payment data encryption
- Audit logging untuk compliance

### **Database Security**:
- Connection encryption
- Access control per service
- Query sanitization
- Backup encryption