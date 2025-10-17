# Risk Management Service

## 🎯 Purpose
**Advanced risk assessment and portfolio protection engine** yang menganalisis trading signals, menghitung position sizing, melakukan portfolio optimization, dan mengimplementasikan real-time risk limits untuk capital protection dengan <4ms risk calculation.

---

## 📊 ChainFlow Diagram

```
Trading-Engine → Risk-Management → API-Gateway → Client-MT5
      ↓              ↓              ↓              ↓
Trading Signals  Risk Assessment   Approved Signals  Safe Execution
Signal Strength  VaR Calculation   Position Sizing   Risk Controls
Entry Strategy   Portfolio Limits  Stop Loss Adjust  Portfolio Mgmt
User Preferences  Drawdown Control  Risk Metrics     Capital Protection
```

---

## 🏗️ Risk Management Architecture

### **Input Flow**: Trading signals and portfolio data from Trading-Engine
**Data Source**: Trading-Engine → Risk-Management
**Format**: Protocol Buffers (TradingSignalBatch)
**Frequency**: 50+ trading signals/second across 10 trading pairs
**Performance Target**: <4ms risk calculation and approval

### **Output Flow**: Risk-adjusted signals and portfolio recommendations
**Destinations**: API-Gateway (approved signals), Analytics-Service (risk metrics)
**Format**: Protocol Buffers (RiskAssessmentBatch)
**Processing**: VaR calculation + position sizing + portfolio optimization
**Performance Target**: <4ms total risk processing time

---

## 🚀 Transport Architecture & Contract Integration

### **Transport Decision Matrix Applied**:

#### **Kategori A: High Volume + Mission Critical**
- **Primary Transport**: NATS + Protocol Buffers (<1ms latency)
- **Backup Transport**: Kafka + Protocol Buffers (guaranteed delivery)
- **Failover**: Automatic dengan sequence tracking
- **Services**: Trading Signals → Risk Assessment, Risk → Approved Signals
- **Performance**: <4ms risk calculation (critical path)

#### **Kategori B: Medium Volume + Important**
- **Transport**: gRPC (HTTP/2 + Protocol Buffers)
- **Connection**: Pooling + circuit breaker
- **Services**: Portfolio management, risk reporting

#### **Kategori C: Low Volume + Standard**
- **Transport**: HTTP REST + JSON via Kong Gateway
- **Backup**: Redis Queue for reliability
- **Services**: Risk configuration, compliance monitoring

### **Global Decisions Applied**:
✅ **Multi-Transport Architecture**: NATS+Kafka for risk assessment, gRPC for management, HTTP for config
✅ **Protocol Buffers Communication**: 60% smaller risk payloads, 10x faster serialization
✅ **Multi-Tenant Architecture**: Company/user-level risk parameter isolation
✅ **Request Tracing**: Complete correlation ID tracking through risk pipeline
✅ **Central-Hub Coordination**: Risk model registry and compliance monitoring
✅ **JWT + Protocol Buffers Auth**: Optimized authentication for risk endpoints
✅ **Circuit Breaker Pattern**: External market data failover for risk calculations

### **Schema Dependencies**:
```python
# Import from centralized schemas
import sys
sys.path.append('../../../01-core-infrastructure/central-hub/static/generated/python')

from trading.trading_signals_pb2 import TradingSignalBatch, TradingSignal
from risk.risk_assessment_pb2 import RiskAssessmentBatch, RiskAssessment, PortfolioRisk
from risk.position_sizing_pb2 import PositionSizing, KellyCriterion, RiskParity
from risk.var_calculation_pb2 import VaRCalculation, StressTest, CorrelationMatrix
from common.user_context_pb2 import UserContext, SubscriptionTier
from common.request_trace_pb2 import RequestTrace, TraceContext
from portfolio.portfolio_data_pb2 import PortfolioPosition, AccountMetrics
```

### **Enhanced Risk MessageEnvelope**:
```protobuf
message RiskProcessingEnvelope {
  string message_type = 1;           // "risk_assessment"
  string user_id = 2;                // Multi-tenant user identification
  string company_id = 3;             // Multi-tenant company identification
  bytes payload = 4;                 // RiskAssessmentBatch protobuf
  int64 timestamp = 5;               // Risk calculation timestamp
  string service_source = 6;         // "risk-management"
  string correlation_id = 7;         // Request tracing
  TraceContext trace_context = 8;    // Distributed tracing
  RiskProfile risk_profile = 9;      // User risk parameters
  AuthToken auth_token = 10;         // JWT + Protocol Buffers auth
}
```

---

## 📋 Standard Implementation Patterns

### **BaseService Integration:**
```python
# Risk Management menggunakan Central Hub standardization
from central_hub.static.utils import BaseService, ServiceConfig
from central_hub.static.utils.patterns import (
    StandardResponse, StandardDatabaseManager, StandardCacheManager,
    RequestTracer, StandardCircuitBreaker, PerformanceTracker, ErrorDNA
)

class RiskManagementService(BaseService):
    def __init__(self):
        config = ServiceConfig(
            service_name="risk-management",
            version="3.5.0",
            port=8005,
            environment="production"
        )
        super().__init__(config)

        # Service-specific components
        self.var_calculator = None
        self.position_sizer = None

    async def custom_health_checks(self):
        """Risk Management-specific health checks"""
        return {
            "risk_assessments_24h": await self.get_daily_assessment_count(),
            "avg_risk_calc_time_ms": await self.get_avg_risk_time(),
            "risk_approval_rate": await self.get_risk_approval_rate(),
            "portfolio_var_compliance": await self.get_var_compliance_rate()
        }
```

### **Standard Error Handling dengan ErrorDNA:**
```python
async def assess_trading_signals(self, signal_batch: TradingSignalBatch, correlation_id: str):
    """Assess trading signals dengan standardized error handling"""
    try:
        return await self.process_with_tracing(
            "risk_assessment",
            self._assess_risk_batch,
            correlation_id,
            signal_batch
        )
    except Exception as e:
        # ErrorDNA automatic analysis
        error_analysis = self.error_analyzer.analyze_error(
            error_message=str(e),
            stack_trace=traceback.format_exc(),
            correlation_id=correlation_id,
            context={"operation": "risk_assessment", "batch_size": len(signal_batch.signals)}
        )

        self.logger.error(f"Risk assessment failed: {error_analysis.suggested_actions}")
        return StandardResponse.error_response(str(e), correlation_id=correlation_id)
```

### **Standard Cache & Database Patterns:**
```python
# VaR calculation caching
var_calculation = await self.cache.get_or_set(
    f"var:{symbol}:{position_size}:{confidence_level}",
    lambda: self.calculate_var(symbol, position_size, confidence_level),
    ttl=300  # 5 minutes
)

# User risk profile caching
risk_profile = await self.cache.get_or_set(
    f"risk_profile:{user_id}",
    lambda: self.db.fetch_one(
        "SELECT * FROM user_risk_profiles WHERE user_id = $1",
        {"user_id": user_id}
    ),
    ttl=3600  # 1 hour
)
```

### **Circuit Breaker untuk Market Data:**
```python
# Market data service dengan circuit breaker protection
if not await self.check_circuit_breaker("market_data"):
    try:
        volatility = await self.market_data_client.get_volatility(symbol)
        await self.record_external_success("market_data")
        return volatility
    except Exception as e:
        await self.record_external_failure("market_data")
        # Fallback to cached historical volatility
        return await self.get_cached_volatility(symbol)
else:
    return await self.get_cached_volatility(symbol)
```

---

## 🛡️ Advanced Risk Assessment Engine

### **1. Real-time Risk Calculator**:
```python
class RiskAssessmentEngine:
    def __init__(self, central_hub_client):
        self.central_hub = central_hub_client
        self.circuit_breaker = CircuitBreaker("market-data")
        self.var_calculator = VaRCalculator()
        self.position_sizer = PositionSizer()

    async def assess_trading_signals(self, signal_batch: TradingSignalBatch,
                                   user_context: UserContext,
                                   trace_context: TraceContext) -> RiskAssessmentBatch:
        """Comprehensive risk assessment with multi-tenant isolation"""

        # Request tracing
        with self.tracer.trace("risk_assessment", trace_context.correlation_id):
            start_time = time.time()

            assessment_batch = RiskAssessmentBatch()
            assessment_batch.user_id = signal_batch.user_id
            assessment_batch.company_id = signal_batch.company_id
            assessment_batch.correlation_id = trace_context.correlation_id

            # Load user risk profile
            risk_profile = await self.get_user_risk_profile(user_context)

            # Load current portfolio
            portfolio = await self.get_current_portfolio(user_context)

            # Multi-tenant risk parameter isolation
            company_risk_limits = await self.get_company_risk_limits(user_context.company_id)
            merged_limits = self.merge_risk_limits(risk_profile, company_risk_limits)

            for signal in signal_batch.trading_signals:
                # Individual signal risk assessment
                risk_assessment = await self.assess_individual_signal(
                    signal, portfolio, merged_limits, trace_context
                )

                assessment_batch.assessments.append(risk_assessment)

            # Portfolio-level risk analysis
            portfolio_risk = await self.assess_portfolio_risk(
                assessment_batch.assessments, portfolio, merged_limits
            )
            assessment_batch.portfolio_risk = portfolio_risk

            # Performance metrics
            risk_calc_time = (time.time() - start_time) * 1000
            assessment_batch.performance_metrics.calculation_time_ms = risk_calc_time

            return assessment_batch

    async def assess_individual_signal(self, signal: TradingSignal,
                                     portfolio: Portfolio,
                                     risk_limits: RiskLimits,
                                     trace_context: TraceContext) -> RiskAssessment:
        """Comprehensive individual signal risk assessment"""

        risk_assessment = RiskAssessment()
        risk_assessment.signal_id = signal.signal_id
        risk_assessment.symbol = signal.symbol
        risk_assessment.correlation_id = trace_context.correlation_id

        # Position sizing calculation
        position_sizing = await self.calculate_position_size(
            signal, portfolio, risk_limits
        )
        risk_assessment.position_sizing = position_sizing

        # Value at Risk calculation
        var_analysis = await self.calculate_var(
            signal, portfolio, position_sizing, risk_limits
        )
        risk_assessment.var_analysis = var_analysis

        # Correlation analysis
        correlation_risk = await self.analyze_correlation_risk(
            signal, portfolio, trace_context
        )
        risk_assessment.correlation_risk = correlation_risk

        # Drawdown protection
        drawdown_analysis = await self.analyze_drawdown_risk(
            signal, portfolio, risk_limits
        )
        risk_assessment.drawdown_analysis = drawdown_analysis

        # Overall risk score
        risk_assessment.overall_risk_score = await self.calculate_overall_risk_score(
            var_analysis, correlation_risk, drawdown_analysis
        )

        # Risk approval decision
        risk_assessment.approval_status = await self.make_risk_decision(
            risk_assessment, risk_limits
        )

        return risk_assessment
```

### **2. Advanced Position Sizing Engine**:
```python
class PositionSizingEngine:
    async def calculate_position_size(self, signal: TradingSignal,
                                    portfolio: Portfolio,
                                    risk_limits: RiskLimits) -> PositionSizing:
        """Multi-method position sizing with intelligent selection"""

        position_sizing = PositionSizing()
        position_sizing.symbol = signal.symbol

        # Kelly Criterion calculation
        kelly_size = await self.calculate_kelly_criterion(
            signal, portfolio, risk_limits
        )
        position_sizing.kelly_criterion = kelly_size

        # Fixed fractional method
        fixed_fractional_size = await self.calculate_fixed_fractional(
            signal, portfolio, risk_limits
        )
        position_sizing.fixed_fractional = fixed_fractional_size

        # Volatility-based sizing
        volatility_size = await self.calculate_volatility_based(
            signal, portfolio, risk_limits
        )
        position_sizing.volatility_based = volatility_size

        # Risk parity method
        risk_parity_size = await self.calculate_risk_parity(
            signal, portfolio, risk_limits
        )
        position_sizing.risk_parity = risk_parity_size

        # Optimal size selection
        position_sizing.recommended_size = await self.select_optimal_size(
            kelly_size, fixed_fractional_size, volatility_size, risk_parity_size,
            signal, risk_limits
        )

        # Position size constraints
        position_sizing.final_size = await self.apply_position_constraints(
            position_sizing.recommended_size, signal, portfolio, risk_limits
        )

        return position_sizing

    async def calculate_kelly_criterion(self, signal: TradingSignal,
                                      portfolio: Portfolio,
                                      risk_limits: RiskLimits) -> KellyCriterion:
        """Kelly Criterion for optimal position sizing"""

        kelly = KellyCriterion()

        # Historical win rate for this strategy/symbol
        win_rate = await self.get_historical_win_rate(
            signal.strategy_id, signal.symbol
        )

        # Average win/loss ratio
        avg_win_loss_ratio = await self.get_avg_win_loss_ratio(
            signal.strategy_id, signal.symbol
        )

        # Kelly percentage calculation: f = (bp - q) / b
        # where: b = odds, p = win probability, q = loss probability
        if avg_win_loss_ratio > 0 and win_rate > 0:
            kelly_percentage = (
                (avg_win_loss_ratio * win_rate - (1 - win_rate)) / avg_win_loss_ratio
            )

            # Apply Kelly fraction (usually 25% of full Kelly)
            kelly_fraction = risk_limits.kelly_fraction or 0.25
            adjusted_kelly = kelly_percentage * kelly_fraction

            # Position size based on account equity
            kelly.kelly_percentage = adjusted_kelly
            kelly.position_size = portfolio.equity * adjusted_kelly
            kelly.confidence_level = win_rate
        else:
            # Fallback to minimum position size
            kelly.kelly_percentage = 0.01  # 1%
            kelly.position_size = portfolio.equity * 0.01
            kelly.confidence_level = 0.5

        return kelly

    async def calculate_volatility_based(self, signal: TradingSignal,
                                       portfolio: Portfolio,
                                       risk_limits: RiskLimits) -> VolatilityBasedSizing:
        """Volatility-adjusted position sizing"""

        volatility_sizing = VolatilityBasedSizing()

        # Get symbol volatility
        if self.circuit_breaker.is_open("market-data"):
            # Use cached volatility data
            volatility = await self.get_cached_volatility(signal.symbol)
            volatility_sizing.data_source = "cache"
        else:
            try:
                volatility = await self.get_real_time_volatility(signal.symbol)
                volatility_sizing.data_source = "real_time"
            except Exception as e:
                self.circuit_breaker.trip("market-data")
                volatility = await self.get_cached_volatility(signal.symbol)
                volatility_sizing.data_source = "fallback"

        # Target volatility approach
        target_volatility = risk_limits.target_portfolio_volatility or 0.02  # 2%
        symbol_volatility = volatility.daily_volatility

        # Position size inversely proportional to volatility
        if symbol_volatility > 0:
            volatility_sizing.volatility_ratio = target_volatility / symbol_volatility
            volatility_sizing.position_size = (
                portfolio.equity * volatility_sizing.volatility_ratio
            )
        else:
            volatility_sizing.position_size = portfolio.equity * 0.01

        volatility_sizing.symbol_volatility = symbol_volatility
        volatility_sizing.target_volatility = target_volatility

        return volatility_sizing
```

### **3. Value at Risk (VaR) Calculator**:
```python
class VaRCalculator:
    async def calculate_var(self, signal: TradingSignal,
                          portfolio: Portfolio,
                          position_sizing: PositionSizing,
                          risk_limits: RiskLimits) -> VaRCalculation:
        """Comprehensive Value at Risk calculation"""

        var_calculation = VaRCalculation()
        var_calculation.symbol = signal.symbol
        var_calculation.position_size = position_sizing.final_size

        # Historical VaR (95% confidence)
        historical_var = await self.calculate_historical_var(
            signal.symbol, position_sizing.final_size, confidence_level=0.95
        )
        var_calculation.historical_var_95 = historical_var

        # Parametric VaR
        parametric_var = await self.calculate_parametric_var(
            signal.symbol, position_sizing.final_size, confidence_level=0.95
        )
        var_calculation.parametric_var_95 = parametric_var

        # Monte Carlo VaR
        monte_carlo_var = await self.calculate_monte_carlo_var(
            signal.symbol, position_sizing.final_size, confidence_level=0.95
        )
        var_calculation.monte_carlo_var_95 = monte_carlo_var

        # Expected Shortfall (Conditional VaR)
        expected_shortfall = await self.calculate_expected_shortfall(
            signal.symbol, position_sizing.final_size, confidence_level=0.95
        )
        var_calculation.expected_shortfall_95 = expected_shortfall

        # Portfolio VaR impact
        portfolio_var_impact = await self.calculate_portfolio_var_impact(
            signal, portfolio, position_sizing.final_size
        )
        var_calculation.portfolio_var_impact = portfolio_var_impact

        # Risk limit validation
        var_calculation.exceeds_var_limit = (
            max(historical_var, parametric_var, monte_carlo_var) >
            risk_limits.max_var_per_trade
        )

        return var_calculation

    async def calculate_historical_var(self, symbol: str,
                                     position_size: float,
                                     confidence_level: float) -> float:
        """Historical simulation VaR calculation"""

        # Get historical price returns
        historical_returns = await self.get_historical_returns(symbol, days=252)

        if not historical_returns:
            return position_size * 0.02  # 2% fallback

        # Sort returns and find percentile
        sorted_returns = sorted(historical_returns)
        percentile_index = int((1 - confidence_level) * len(sorted_returns))
        var_return = sorted_returns[percentile_index]

        # VaR in monetary terms
        historical_var = abs(var_return * position_size)

        return historical_var

    async def calculate_monte_carlo_var(self, symbol: str,
                                      position_size: float,
                                      confidence_level: float,
                                      simulations: int = 10000) -> float:
        """Monte Carlo simulation VaR calculation"""

        # Get volatility and drift parameters
        volatility = await self.get_symbol_volatility(symbol)
        drift = await self.get_symbol_drift(symbol)

        # Monte Carlo simulation
        simulated_returns = []
        for _ in range(simulations):
            # Generate random return using normal distribution
            random_return = np.random.normal(drift, volatility)
            simulated_returns.append(random_return)

        # Calculate VaR from simulated returns
        sorted_returns = sorted(simulated_returns)
        percentile_index = int((1 - confidence_level) * len(sorted_returns))
        var_return = sorted_returns[percentile_index]

        monte_carlo_var = abs(var_return * position_size)

        return monte_carlo_var
```

### **4. Portfolio Risk Analyzer**:
```python
class PortfolioRiskAnalyzer:
    async def assess_portfolio_risk(self, new_assessments: List[RiskAssessment],
                                  current_portfolio: Portfolio,
                                  risk_limits: RiskLimits) -> PortfolioRisk:
        """Comprehensive portfolio-level risk analysis"""

        portfolio_risk = PortfolioRisk()

        # Current portfolio metrics
        portfolio_risk.current_exposure = await self.calculate_total_exposure(
            current_portfolio
        )
        portfolio_risk.current_var = await self.calculate_portfolio_var(
            current_portfolio
        )

        # Projected portfolio after new positions
        projected_portfolio = await self.project_portfolio_with_new_positions(
            current_portfolio, new_assessments
        )

        portfolio_risk.projected_exposure = await self.calculate_total_exposure(
            projected_portfolio
        )
        portfolio_risk.projected_var = await self.calculate_portfolio_var(
            projected_portfolio
        )

        # Correlation analysis
        correlation_matrix = await self.calculate_correlation_matrix(
            projected_portfolio
        )
        portfolio_risk.correlation_analysis = correlation_matrix

        # Concentration risk
        concentration_risk = await self.analyze_concentration_risk(
            projected_portfolio, risk_limits
        )
        portfolio_risk.concentration_risk = concentration_risk

        # Sector/currency exposure
        exposure_analysis = await self.analyze_exposure_by_category(
            projected_portfolio
        )
        portfolio_risk.exposure_analysis = exposure_analysis

        # Risk limit compliance
        portfolio_risk.risk_limit_compliance = await self.check_risk_limit_compliance(
            portfolio_risk, risk_limits
        )

        # Overall portfolio risk score
        portfolio_risk.overall_risk_score = await self.calculate_portfolio_risk_score(
            portfolio_risk
        )

        return portfolio_risk

    async def analyze_concentration_risk(self, portfolio: Portfolio,
                                       risk_limits: RiskLimits) -> ConcentrationRisk:
        """Analyze portfolio concentration risk"""

        concentration = ConcentrationRisk()

        # Position concentration
        position_weights = []
        for position in portfolio.positions:
            weight = position.notional_value / portfolio.total_value
            position_weights.append(weight)

        # Herfindahl-Hirschman Index (HHI)
        hhi = sum(weight ** 2 for weight in position_weights)
        concentration.hhi_index = hhi

        # Maximum single position weight
        concentration.max_position_weight = max(position_weights) if position_weights else 0

        # Currency concentration
        currency_exposure = {}
        for position in portfolio.positions:
            base_currency = position.symbol[:3]
            quote_currency = position.symbol[3:]

            currency_exposure[base_currency] = currency_exposure.get(base_currency, 0) + position.notional_value
            currency_exposure[quote_currency] = currency_exposure.get(quote_currency, 0) - position.notional_value

        # Maximum currency exposure
        max_currency_exposure = max(abs(exp) for exp in currency_exposure.values()) if currency_exposure else 0
        concentration.max_currency_exposure_pct = max_currency_exposure / portfolio.total_value

        # Concentration limit violations
        concentration.exceeds_position_limit = (
            concentration.max_position_weight > risk_limits.max_position_concentration
        )
        concentration.exceeds_currency_limit = (
            concentration.max_currency_exposure_pct > risk_limits.max_currency_exposure
        )

        return concentration
```

---

## 🔍 Multi-Tenant Risk Management

### **Company-Level Risk Controls**:
```python
class CompanyRiskManager:
    async def get_company_risk_limits(self, company_id: str) -> CompanyRiskLimits:
        """Get company-specific risk parameters and limits"""

        company_limits = await self.database.get_company_risk_limits(company_id)

        if not company_limits:
            # Default company limits
            company_limits = CompanyRiskLimits(
                max_daily_var=10000.0,              # $10,000 daily VaR
                max_position_concentration=0.1,     # 10% max single position
                max_currency_exposure=0.2,          # 20% max currency exposure
                max_drawdown_threshold=0.15,        # 15% max drawdown
                allowed_instruments=self.get_default_instruments(),
                trading_hours_restriction=True
            )

        return company_limits

    async def enforce_company_limits(self, risk_assessment: RiskAssessment,
                                   company_limits: CompanyRiskLimits,
                                   user_context: UserContext) -> RiskAssessment:
        """Enforce company-level risk limits"""

        # Check if instrument is allowed
        if risk_assessment.symbol not in company_limits.allowed_instruments:
            risk_assessment.approval_status = ApprovalStatus.REJECTED
            risk_assessment.rejection_reason = f"Instrument {risk_assessment.symbol} not allowed by company policy"
            return risk_assessment

        # Check trading hours
        if company_limits.trading_hours_restriction:
            if not await self.is_within_trading_hours(risk_assessment.symbol):
                risk_assessment.approval_status = ApprovalStatus.REJECTED
                risk_assessment.rejection_reason = "Outside company-approved trading hours"
                return risk_assessment

        # Apply company position sizing limits
        if risk_assessment.position_sizing.final_size > company_limits.max_position_size:
            # Reduce position size to company limit
            original_size = risk_assessment.position_sizing.final_size
            risk_assessment.position_sizing.final_size = company_limits.max_position_size
            risk_assessment.risk_adjustments.append(
                f"Position reduced from {original_size} to {company_limits.max_position_size} (company limit)"
            )

        return risk_assessment
```

### **User Risk Profile Management**:
```python
class UserRiskProfileManager:
    async def get_user_risk_profile(self, user_context: UserContext) -> UserRiskProfile:
        """Get user-specific risk profile with subscription-based features"""

        base_profile = await self.get_base_risk_profile(user_context.subscription_tier)
        user_customizations = await self.get_user_customizations(user_context.user_id)

        # Merge base profile with user customizations
        risk_profile = self.merge_risk_profiles(base_profile, user_customizations)

        # Dynamic risk adjustment based on performance
        performance_adjustment = await self.calculate_performance_adjustment(
            user_context.user_id
        )
        risk_profile = self.apply_performance_adjustment(risk_profile, performance_adjustment)

        return risk_profile

    def get_base_risk_profile(self, tier: SubscriptionTier) -> UserRiskProfile:
        """Get default risk profile based on subscription tier"""

        tier_profiles = {
            SubscriptionTier.FREE: UserRiskProfile(
                max_position_size=1000.0,           # $1,000 max position
                max_daily_var=100.0,                # $100 daily VaR
                max_positions=3,                    # 3 concurrent positions
                risk_tolerance=RiskTolerance.CONSERVATIVE,
                advanced_sizing_methods=False
            ),
            SubscriptionTier.PRO: UserRiskProfile(
                max_position_size=10000.0,          # $10,000 max position
                max_daily_var=1000.0,               # $1,000 daily VaR
                max_positions=10,                   # 10 concurrent positions
                risk_tolerance=RiskTolerance.MODERATE,
                advanced_sizing_methods=True,
                kelly_criterion_enabled=True
            ),
            SubscriptionTier.ENTERPRISE: UserRiskProfile(
                max_position_size=100000.0,         # $100,000 max position
                max_daily_var=10000.0,              # $10,000 daily VaR
                max_positions=50,                   # 50 concurrent positions
                risk_tolerance=RiskTolerance.AGGRESSIVE,
                advanced_sizing_methods=True,
                kelly_criterion_enabled=True,
                custom_risk_models_enabled=True,
                portfolio_optimization_enabled=True
            )
        }

        return tier_profiles.get(tier, tier_profiles[SubscriptionTier.FREE])
```

---

## ⚡ Performance Optimizations

### **Risk Calculation Caching**:
```python
class RiskCalculationCache:
    def __init__(self):
        self.var_cache = TTLCache(maxsize=500, ttl=300)      # 5 minute TTL
        self.correlation_cache = TTLCache(maxsize=100, ttl=600)  # 10 minute TTL
        self.volatility_cache = TTLCache(maxsize=200, ttl=300)   # 5 minute TTL

    async def get_cached_var(self, symbol: str, position_size: float,
                           confidence_level: float) -> Optional[float]:
        """Get cached VaR calculation"""

        cache_key = f"{symbol}:{position_size}:{confidence_level}"
        return self.var_cache.get(cache_key)

    async def cache_var_calculation(self, symbol: str, position_size: float,
                                  confidence_level: float, var_value: float):
        """Cache VaR calculation with intelligent TTL"""

        cache_key = f"{symbol}:{position_size}:{confidence_level}"
        self.var_cache[cache_key] = var_value

    async def get_cached_correlation_matrix(self, symbols: List[str]) -> Optional[CorrelationMatrix]:
        """Get cached correlation matrix for symbol set"""

        symbols_key = ":".join(sorted(symbols))
        return self.correlation_cache.get(symbols_key)
```

### **Parallel Risk Assessment**:
```python
async def assess_multiple_signals(self, signal_batches: List[TradingSignalBatch],
                                trace_context: TraceContext) -> List[RiskAssessmentBatch]:
    """Parallel risk assessment for multiple signal batches"""

    # Create assessment tasks
    tasks = []
    for batch in signal_batches:
        task = asyncio.create_task(
            self.assess_trading_signals(batch, trace_context)
        )
        tasks.append(task)

    # Execute in parallel
    assessment_batches = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle exceptions
    successful_assessments = []
    for i, result in enumerate(assessment_batches):
        if isinstance(result, Exception):
            self.logger.error(f"Risk assessment failed for batch {i}: {result}")
            # Add error to trace
            self.tracer.add_error(trace_context.correlation_id, str(result))
        else:
            successful_assessments.append(result)

    return successful_assessments
```

---

## 🔍 Health Monitoring & Compliance

### **Service Health Check**:
```python
@app.get("/health")
async def health_check():
    """Comprehensive risk management service health check"""

    health_status = {
        "service": "risk-management",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0"
    }

    try:
        # Risk calculation performance
        health_status["avg_risk_calc_time_ms"] = await self.get_avg_risk_calc_time()
        health_status["var_calculation_accuracy"] = await self.get_var_accuracy()

        # Position sizing performance
        health_status["position_sizing_success_rate"] = await self.get_sizing_success_rate()
        health_status["kelly_criterion_performance"] = await self.get_kelly_performance()

        # Portfolio risk metrics
        health_status["portfolio_risk_compliance"] = await self.get_compliance_rate()
        health_status["drawdown_protection_active"] = await self.check_drawdown_protection()

        # Circuit breaker status
        health_status["market_data_circuit_breaker"] = await self.get_circuit_breaker_status()

        # Multi-tenant metrics
        health_status["active_risk_profiles"] = await self.get_active_profile_count()
        health_status["company_risk_policies"] = await self.get_company_policy_count()

        # Cache performance
        health_status["cache_hit_rate"] = await self.get_cache_hit_rate()

    except Exception as e:
        health_status["status"] = "degraded"
        health_status["error"] = str(e)

    return health_status
```

### **Risk Compliance Monitoring**:
```python
class RiskComplianceMonitor:
    async def monitor_risk_compliance(self, user_id: str,
                                    risk_assessment: RiskAssessment,
                                    trace_context: TraceContext):
        """Real-time risk compliance monitoring"""

        # Check for risk limit violations
        violations = []

        if risk_assessment.var_analysis.exceeds_var_limit:
            violations.append(ViolationType.VAR_LIMIT_EXCEEDED)

        if risk_assessment.portfolio_risk.exceeds_concentration_limit:
            violations.append(ViolationType.CONCENTRATION_LIMIT_EXCEEDED)

        if risk_assessment.drawdown_analysis.exceeds_drawdown_limit:
            violations.append(ViolationType.DRAWDOWN_LIMIT_EXCEEDED)

        # Report violations
        if violations:
            compliance_alert = ComplianceAlert()
            compliance_alert.user_id = user_id
            compliance_alert.violations = violations
            compliance_alert.correlation_id = trace_context.correlation_id
            compliance_alert.timestamp = int(time.time() * 1000)

            await self.send_compliance_alert(compliance_alert)

        # Update compliance metrics
        await self.update_compliance_metrics(user_id, violations)
```

---

## 🎯 Business Value

### **Capital Protection Excellence**:
- **Sub-4ms Risk Calculation**: Real-time risk assessment without latency impact
- **Multi-Method Position Sizing**: Kelly Criterion + Volatility-based + Risk Parity
- **Advanced VaR Calculation**: Historical + Parametric + Monte Carlo methods
- **Portfolio Risk Management**: Correlation analysis + concentration limits

### **Multi-Tenant Risk Controls**:
- **Company-Level Policies**: Centralized risk governance for organizations
- **Subscription-Based Limits**: Tiered risk management features
- **Dynamic Risk Adjustment**: Performance-based risk parameter optimization
- **Compliance Monitoring**: Real-time violation detection and alerting

### **Technical Excellence**:
- **Circuit Breaker Protected**: Market data failover for continuous operation
- **Protocol Buffers**: 60% smaller risk payloads, 10x faster processing
- **Intelligent Caching**: VaR + correlation + volatility caching optimization
- **Request Tracing**: Complete correlation ID tracking through risk pipeline

---

## 🔗 Service Contract Specifications

### **Risk Management Proto Contracts**:
- **Input Contract**: Trading Signals via NATS/Kafka from `/trading/trading_signals.proto`
- **Output Contract**: Risk Assessments via NATS/Kafka to `/risk/risk_assessment.proto`
- **Portfolio Management**: gRPC service for portfolio analysis dan compliance monitoring

### **Critical Path Integration**:
- **Trading-Engine → Risk-Management**: NATS primary, Kafka backup
- **Risk-Management → API-Gateway**: NATS primary, Kafka backup
- **Risk-Management → Analytics**: gRPC for risk metrics

---

**Input Flow**: Trading-Engine (trading signals) → Risk-Management (risk assessment)
**Output Flow**: Risk-Management → API-Gateway → Client-MT5 (approved signals)
**Key Innovation**: Sub-4ms comprehensive risk assessment dengan multi-transport architecture, multi-tenant controls dan advanced portfolio protection untuk optimal capital preservation.