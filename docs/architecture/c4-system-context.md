# C4 Model: System Context Diagram
## AI Trading Platform - Enterprise Architecture

```mermaid
C4Context
    title System Context Diagram - AI Trading Platform

    Person(trader, "Professional Trader", "Uses platform for automated trading")
    Person(admin, "System Administrator", "Manages platform operations")
    Person(analyst, "Financial Analyst", "Analyzes trading performance")

    System_Boundary(platform, "AI Trading Platform") {
        System(core, "AI Trading Platform", "Enterprise trading system with ML-driven decisions")
    }

    System_Ext(mt5, "MetaTrader 5", "Market data and order execution")
    System_Ext(exchanges, "Financial Exchanges", "Real market data feeds")
    System_Ext(ai_providers, "External AI Services", "OpenAI, DeepSeek, Google AI")
    System_Ext(notification, "Notification Services", "Telegram, Email, SMS")
    System_Ext(compliance, "Regulatory Systems", "Financial compliance reporting")

    Rel(trader, core, "Manages trading strategies", "HTTPS/WebSocket")
    Rel(admin, core, "Monitors system health", "HTTPS API")
    Rel(analyst, core, "Reviews performance data", "HTTPS API")

    Rel(core, mt5, "Receives market data, executes orders", "TCP/API")
    Rel(core, exchanges, "Market data streaming", "WebSocket/FIX")
    Rel(core, ai_providers, "AI model inference", "HTTPS API")
    Rel(core, notification, "Trading alerts", "HTTPS/Bot API")
    Rel(core, compliance, "Regulatory reporting", "HTTPS/SFTP")

    UpdateElementStyle(core, $bgColor="lightblue", $borderColor="blue")
    UpdateElementStyle(mt5, $bgColor="lightgreen", $borderColor="green")
    UpdateElementStyle(ai_providers, $bgColor="lightyellow", $borderColor="orange")
```

### Key External Dependencies

#### Market Data Sources
- **MetaTrader 5**: Primary data source (18+ ticks/second)
- **Financial Exchanges**: Direct market feeds for institutional data
- **Data Vendors**: Bloomberg, Reuters for enhanced market intelligence

#### AI/ML Services
- **OpenAI**: GPT models for market sentiment analysis
- **DeepSeek**: Specialized financial AI models
- **Google AI**: TensorFlow serving for custom models

#### Infrastructure Dependencies
- **Cloud Providers**: AWS/Azure for scalable compute
- **Monitoring**: Prometheus, Grafana for observability
- **Security**: HashiCorp Vault for secrets management

### System Boundaries
- **Internal**: All 11 microservices within platform boundary
- **External**: Market data, AI services, notification systems
- **Compliance**: Regulatory reporting and audit systems

### Performance Context
- **Data Ingestion**: 50+ ticks/second target
- **AI Decisions**: <15ms latency requirement
- **Order Execution**: <1.2ms execution time
- **System Availability**: 99.99% uptime target