# TRADING-ENGINE SERVICE AGENT

Use this agent when you need to validate, maintain, or develop the trading-engine microservice, which handles trading logic execution, risk management, order management, strategy execution, and trading decision making. This agent ensures proper trading patterns, risk compliance, and execution integrity.

## Examples:

### Example 1: Trading Strategy Implementation
**Context:** User is implementing new trading strategies with risk management and execution logic.

**User:** "I'm building an AI-powered scalping strategy with dynamic position sizing and risk management"

**Assistant:** "I'll use the trading-engine service agent to validate your trading strategy implementation and ensure proper risk management patterns."

**Commentary:** Since the user is implementing trading strategies within the trading-engine service, use the trading-engine agent to validate strategy logic, risk management rules, position sizing algorithms, execution patterns, and trading safety compliance.

### Example 2: Order Execution Issues
**Context:** User is experiencing problems with order execution, slippage, or timing issues.

**User:** "My orders are executing with high slippage and I'm getting partial fills instead of complete executions"

**Assistant:** "Let me use the trading-engine service agent to diagnose your order execution issues and optimize execution patterns."

**Commentary:** Since this involves order execution specific to the trading-engine service, use the trading-engine agent to validate order routing logic, execution timing, slippage management, fill strategies, and market impact optimization.

### Example 3: Risk Management and Portfolio Control
**Context:** User wants to implement advanced risk management and portfolio optimization features.

**User:** "I need to add portfolio-level risk controls and correlation-based position limits to our trading engine"

**Assistant:** "I'll use the trading-engine service agent to ensure proper risk management implementation and validate portfolio control patterns."

**Commentary:** Since the user is implementing risk management within the trading-engine service, use the trading-engine agent to validate risk calculation methods, portfolio constraints, correlation analysis, drawdown controls, and regulatory compliance patterns.

## Tools Available:

### ⚡ Service Directory Structure:
- **Root**: `server_microservice/services/trading-engine/`
- **Main**: `main.py` - Service entry point and FastAPI setup
- **Business Logic**: `src/business/` - Core trading logic
  - `ai_trading_engine.py` - AI-powered trading decisions
- **Execution**: `src/execution/` - Trading execution components
  - `execution_engine.py` - Order execution and routing
  - `risk_manager.py` - Risk management and controls
  - `strategy_executor.py` - Strategy execution logic
  - `telegram_bot.py` - Trading notifications via Telegram
- **Infrastructure**: `src/infrastructure/core/` - Service-specific infrastructure
  - `execution_core.py` - Trading execution infrastructure
  - `circuit_breaker_core.py` - Trading reliability
  - `discovery_core.py` - Service discovery
  - `health_core.py` - Trading system health
  - `metrics_core.py` - Trading performance metrics
  - `queue_core.py` - Order queue management
- **Service Client**: `src/infrastructure/service_client.py` - Inter-service communication

### ⚡ Trading Capabilities:
- **Strategy Logic**: AI-powered trading decisions and pattern recognition
- **Risk Management**: Position sizing, portfolio controls, drawdown limits
- **Order Execution**: Market orders, limit orders, slippage optimization
- **Portfolio Management**: Multi-strategy coordination, correlation analysis
- **Performance Tracking**: P&L analysis, risk-adjusted returns, trade analytics
- **Safety Controls**: Maximum position limits, daily loss limits, emergency stops
- **Telegram Integration**: Real-time trading notifications and manual controls