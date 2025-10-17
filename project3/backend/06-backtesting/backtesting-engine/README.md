# Backtesting Engine Service

## 🎯 Purpose
**Advanced strategy validation and performance optimization engine** yang melakukan historical simulation, walk-forward analysis, dan strategy optimization untuk memvalidasi trading strategies sebelum live deployment dengan comprehensive performance metrics.

---

## 📊 ChainFlow Diagram

```
Trading-Engine → Backtesting-Engine → Analytics-Service → User Dashboard
      ↓               ↓                    ↓                ↓
Strategy Config   Historical Sim      Performance Data   Strategy Reports
Risk Parameters   Walk-Forward        Optimization       Backtest Results
ML Models         Monte Carlo         Risk Metrics       Strategy Ranking
User Preferences  Stress Testing      Sharpe Ratios      Performance Charts
```

---

## 🏗️ Backtesting Architecture

### **Input Flow**: Trading strategies and optimization requests
**Data Sources**: Trading-Engine (strategies), User requests (backtest parameters)
**Format**: Protocol Buffers (BacktestRequest, StrategyConfig)
**Frequency**: On-demand backtesting requests
**Performance Target**: <2 seconds untuk standard backtest (1 year data)

### **Output Flow**: Comprehensive backtest results and optimization recommendations
**Destinations**: Analytics-Service (performance storage), User Dashboard (reports)
**Format**: Protocol Buffers (BacktestResults, OptimizationReport)
**Processing**: Historical simulation + performance analysis + optimization
**Performance Target**: <2 seconds standard backtest, <30 seconds optimization

---

## 🔧 Protocol Buffers Integration

### **Global Decisions Applied**:
✅ **Protocol Buffers Communication**: 60% smaller backtest payloads, 10x faster serialization
✅ **Multi-Tenant Architecture**: Company/user-level backtest isolation and data access
✅ **Request Tracing**: Complete correlation ID tracking through backtesting pipeline
✅ **Central-Hub Coordination**: Strategy registry and performance benchmarking
✅ **JWT + Protocol Buffers Auth**: Optimized authentication for backtest endpoints
✅ **Circuit Breaker Pattern**: Historical data service failover and caching

### **Schema Dependencies**:
```python
# Import from centralized schemas
import sys
sys.path.append('../../../01-core-infrastructure/central-hub/static/generated/python')

from backtesting.backtest_request_pb2 import BacktestRequest, StrategyDefinition
from backtesting.backtest_results_pb2 import BacktestResults, PerformanceMetrics, TradeAnalysis
from backtesting.optimization_pb2 import OptimizationRequest, OptimizationResults, ParameterSpace
from trading.trading_signals_pb2 import TradingSignal, StrategyConfig
from common.user_context_pb2 import UserContext, SubscriptionTier
from common.request_trace_pb2 import RequestTrace, TraceContext
from risk.risk_assessment_pb2 import RiskMetrics, DrawdownAnalysis
```

### **Enhanced Backtesting MessageEnvelope**:
```protobuf
message BacktestProcessingEnvelope {
  string message_type = 1;           // "backtest_request"
  string user_id = 2;                // Multi-tenant user identification
  string company_id = 3;             // Multi-tenant company identification
  bytes payload = 4;                 // BacktestRequest protobuf
  int64 timestamp = 5;               // Request timestamp
  string service_source = 6;         // "backtesting-engine"
  string correlation_id = 7;         // Request tracing
  TraceContext trace_context = 8;    // Distributed tracing
  StrategyInfo strategy_info = 9;    // Strategy metadata
  AuthToken auth_token = 10;         // JWT + Protocol Buffers auth
}
```

---

## 🔄 Advanced Backtesting Engine

### **1. Historical Simulation Engine**:
```python
class HistoricalSimulationEngine:
    def __init__(self, central_hub_client):
        self.central_hub = central_hub_client
        self.circuit_breaker = CircuitBreaker("historical-data")
        self.data_cache = HistoricalDataCache()
        self.performance_calculator = PerformanceCalculator()

    async def run_backtest(self, backtest_request: BacktestRequest,
                         user_context: UserContext,
                         trace_context: TraceContext) -> BacktestResults:
        """Comprehensive historical simulation with multi-tenant isolation"""

        # Request tracing
        with self.tracer.trace("historical_backtest", trace_context.correlation_id):
            start_time = time.time()

            # Multi-tenant data access validation
            await self.validate_data_access(backtest_request, user_context)

            # Load historical data with circuit breaker protection
            historical_data = await self.load_historical_data(
                backtest_request.symbols,
                backtest_request.start_date,
                backtest_request.end_date,
                trace_context
            )

            # Initialize backtest environment
            backtest_env = BacktestEnvironment(
                initial_capital=backtest_request.initial_capital,
                commission=backtest_request.commission_rate,
                slippage=backtest_request.slippage_model
            )

            # Strategy execution simulation
            simulation_results = await self.simulate_strategy_execution(
                backtest_request.strategy_config,
                historical_data,
                backtest_env,
                user_context,
                trace_context
            )

            # Performance analysis
            performance_metrics = await self.calculate_performance_metrics(
                simulation_results, backtest_request
            )

            # Risk analysis
            risk_metrics = await self.calculate_risk_metrics(
                simulation_results, backtest_request
            )

            # Trade analysis
            trade_analysis = await self.analyze_trades(
                simulation_results, backtest_request
            )

            # Compile results
            backtest_results = BacktestResults()
            backtest_results.backtest_id = backtest_request.backtest_id
            backtest_results.user_id = user_context.user_id
            backtest_results.company_id = user_context.company_id
            backtest_results.correlation_id = trace_context.correlation_id
            backtest_results.performance_metrics = performance_metrics
            backtest_results.risk_metrics = risk_metrics
            backtest_results.trade_analysis = trade_analysis
            backtest_results.execution_time_ms = (time.time() - start_time) * 1000

            return backtest_results

    async def simulate_strategy_execution(self, strategy_config: StrategyConfig,
                                        historical_data: HistoricalDataSet,
                                        backtest_env: BacktestEnvironment,
                                        user_context: UserContext,
                                        trace_context: TraceContext) -> SimulationResults:
        """Detailed strategy execution simulation"""

        simulation_results = SimulationResults()
        portfolio = Portfolio(initial_capital=backtest_env.initial_capital)

        # Strategy instance
        strategy = await self.create_strategy_instance(strategy_config, user_context)

        # Time-ordered data processing
        for timestamp, market_data in historical_data.iterate_chronologically():

            # Generate trading signals using strategy
            signals = await strategy.generate_signals(
                market_data, portfolio, timestamp
            )

            # Process each signal
            for signal in signals:
                # Risk management (if enabled in backtest)
                if strategy_config.enable_risk_management:
                    risk_adjusted_signal = await self.apply_backtest_risk_management(
                        signal, portfolio, strategy_config
                    )
                else:
                    risk_adjusted_signal = signal

                # Execute trade simulation
                if risk_adjusted_signal.signal_type != SignalType.HOLD:
                    trade_result = await self.simulate_trade_execution(
                        risk_adjusted_signal, market_data, backtest_env
                    )

                    if trade_result.executed:
                        portfolio.add_trade(trade_result)
                        simulation_results.trades.append(trade_result)

            # Update portfolio value
            portfolio.update_value(market_data, timestamp)
            simulation_results.portfolio_values.append(
                PortfolioSnapshot(timestamp=timestamp, value=portfolio.total_value)
            )

        simulation_results.final_portfolio = portfolio
        return simulation_results
```

### **2. Walk-Forward Analysis Engine**:
```python
class WalkForwardAnalysisEngine:
    async def run_walk_forward_analysis(self, strategy_config: StrategyConfig,
                                      historical_data: HistoricalDataSet,
                                      user_context: UserContext,
                                      trace_context: TraceContext) -> WalkForwardResults:
        """Out-of-sample strategy validation with walk-forward analysis"""

        walk_forward_results = WalkForwardResults()

        # Define analysis periods
        total_period = historical_data.end_date - historical_data.start_date
        in_sample_period = total_period * 0.7  # 70% for optimization
        out_sample_period = total_period * 0.3  # 30% for validation

        # Walk-forward windows
        window_size = timedelta(days=90)  # 3-month windows
        step_size = timedelta(days=30)    # 1-month steps

        current_start = historical_data.start_date
        window_results = []

        while current_start + in_sample_period + out_sample_period <= historical_data.end_date:
            # Define periods
            in_sample_end = current_start + in_sample_period
            out_sample_start = in_sample_end
            out_sample_end = out_sample_start + out_sample_period

            # In-sample optimization
            in_sample_data = historical_data.get_period(current_start, in_sample_end)
            optimized_params = await self.optimize_strategy_parameters(
                strategy_config, in_sample_data, user_context, trace_context
            )

            # Out-of-sample validation
            out_sample_data = historical_data.get_period(out_sample_start, out_sample_end)
            validation_results = await self.validate_optimized_strategy(
                optimized_params, out_sample_data, user_context, trace_context
            )

            # Store window results
            window_result = WalkForwardWindow()
            window_result.in_sample_period = f"{current_start} to {in_sample_end}"
            window_result.out_sample_period = f"{out_sample_start} to {out_sample_end}"
            window_result.optimized_parameters = optimized_params
            window_result.validation_performance = validation_results.performance_metrics
            window_results.append(window_result)

            # Move to next window
            current_start += step_size

        # Aggregate walk-forward results
        walk_forward_results.window_results = window_results
        walk_forward_results.average_out_sample_return = np.mean([
            w.validation_performance.total_return for w in window_results
        ])
        walk_forward_results.average_out_sample_sharpe = np.mean([
            w.validation_performance.sharpe_ratio for w in window_results
        ])
        walk_forward_results.consistency_score = await self.calculate_consistency_score(
            window_results
        )

        return walk_forward_results

    async def optimize_strategy_parameters(self, strategy_config: StrategyConfig,
                                         in_sample_data: HistoricalDataSet,
                                         user_context: UserContext,
                                         trace_context: TraceContext) -> OptimizedParameters:
        """Parameter optimization using genetic algorithm or grid search"""

        # Define parameter space based on subscription tier
        parameter_space = await self.get_parameter_space(strategy_config, user_context)

        if user_context.subscription_tier >= SubscriptionTier.PRO:
            # Genetic algorithm optimization for Pro+ users
            optimizer = GeneticAlgorithmOptimizer()
            optimization_method = "genetic_algorithm"
        else:
            # Grid search for free users
            optimizer = GridSearchOptimizer()
            optimization_method = "grid_search"

        # Run optimization
        best_parameters = await optimizer.optimize(
            strategy_config=strategy_config,
            historical_data=in_sample_data,
            parameter_space=parameter_space,
            objective_function=self.sharpe_ratio_objective,
            max_iterations=100 if user_context.subscription_tier >= SubscriptionTier.PRO else 20
        )

        optimized_params = OptimizedParameters()
        optimized_params.parameters = best_parameters
        optimized_params.optimization_method = optimization_method
        optimized_params.objective_value = await self.evaluate_objective(
            best_parameters, strategy_config, in_sample_data
        )

        return optimized_params
```

### **3. Monte Carlo Simulation Engine**:
```python
class MonteCarloSimulationEngine:
    async def run_monte_carlo_analysis(self, backtest_results: BacktestResults,
                                     user_context: UserContext,
                                     simulations: int = 1000) -> MonteCarloResults:
        """Monte Carlo simulation for strategy robustness analysis"""

        # Subscription-based simulation limits
        max_simulations = self.get_max_simulations(user_context.subscription_tier)
        simulations = min(simulations, max_simulations)

        monte_carlo_results = MonteCarloResults()
        simulation_outcomes = []

        # Extract trade statistics from backtest
        trade_returns = [trade.return_pct for trade in backtest_results.trade_analysis.trades]
        win_rate = backtest_results.trade_analysis.win_rate
        avg_win = backtest_results.trade_analysis.average_win
        avg_loss = backtest_results.trade_analysis.average_loss

        # Run Monte Carlo simulations
        for sim_id in range(simulations):
            simulated_returns = await self.simulate_trading_sequence(
                trade_returns, win_rate, avg_win, avg_loss,
                num_trades=len(trade_returns)
            )

            # Calculate simulation metrics
            sim_outcome = SimulationOutcome()
            sim_outcome.total_return = sum(simulated_returns)
            sim_outcome.max_drawdown = self.calculate_max_drawdown(simulated_returns)
            sim_outcome.sharpe_ratio = self.calculate_sharpe_ratio(simulated_returns)
            sim_outcome.final_equity = (1 + sim_outcome.total_return) * backtest_results.initial_capital

            simulation_outcomes.append(sim_outcome)

        # Statistical analysis of outcomes
        monte_carlo_results.simulation_count = simulations
        monte_carlo_results.outcomes = simulation_outcomes

        # Confidence intervals
        returns = [outcome.total_return for outcome in simulation_outcomes]
        monte_carlo_results.return_percentiles = {
            "5th": np.percentile(returns, 5),
            "25th": np.percentile(returns, 25),
            "50th": np.percentile(returns, 50),
            "75th": np.percentile(returns, 75),
            "95th": np.percentile(returns, 95)
        }

        # Risk metrics
        drawdowns = [outcome.max_drawdown for outcome in simulation_outcomes]
        monte_carlo_results.max_drawdown_95th_percentile = np.percentile(drawdowns, 95)

        # Probability of positive returns
        positive_returns = sum(1 for r in returns if r > 0)
        monte_carlo_results.probability_of_profit = positive_returns / simulations

        return monte_carlo_results

    def get_max_simulations(self, tier: SubscriptionTier) -> int:
        """Get maximum Monte Carlo simulations based on subscription"""

        simulation_limits = {
            SubscriptionTier.FREE: 100,
            SubscriptionTier.PRO: 1000,
            SubscriptionTier.ENTERPRISE: 10000
        }

        return simulation_limits.get(tier, 100)
```

### **4. Performance Metrics Calculator**:
```python
class PerformanceCalculator:
    async def calculate_comprehensive_metrics(self, simulation_results: SimulationResults,
                                            backtest_request: BacktestRequest) -> PerformanceMetrics:
        """Calculate comprehensive performance and risk metrics"""

        metrics = PerformanceMetrics()
        portfolio_values = [snapshot.value for snapshot in simulation_results.portfolio_values]
        returns = self.calculate_returns(portfolio_values)

        # Return metrics
        metrics.total_return = (portfolio_values[-1] - portfolio_values[0]) / portfolio_values[0]
        metrics.annualized_return = self.annualize_return(metrics.total_return, len(returns))
        metrics.compound_annual_growth_rate = ((portfolio_values[-1] / portfolio_values[0]) **
                                             (252 / len(returns))) - 1

        # Risk metrics
        metrics.volatility = np.std(returns) * np.sqrt(252)  # Annualized
        metrics.sharpe_ratio = (metrics.annualized_return - 0.02) / metrics.volatility  # Assuming 2% risk-free rate
        metrics.sortino_ratio = self.calculate_sortino_ratio(returns)
        metrics.calmar_ratio = metrics.annualized_return / abs(self.calculate_max_drawdown(portfolio_values))

        # Drawdown analysis
        metrics.max_drawdown = self.calculate_max_drawdown(portfolio_values)
        metrics.max_drawdown_duration = self.calculate_max_drawdown_duration(portfolio_values)
        metrics.avg_drawdown = self.calculate_average_drawdown(portfolio_values)

        # Trade-based metrics
        if simulation_results.trades:
            metrics.total_trades = len(simulation_results.trades)
            winning_trades = [t for t in simulation_results.trades if t.pnl > 0]
            losing_trades = [t for t in simulation_results.trades if t.pnl < 0]

            metrics.win_rate = len(winning_trades) / len(simulation_results.trades)
            metrics.profit_factor = (sum(t.pnl for t in winning_trades) /
                                   abs(sum(t.pnl for t in losing_trades))) if losing_trades else float('inf')

            metrics.average_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
            metrics.average_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
            metrics.largest_win = max([t.pnl for t in winning_trades]) if winning_trades else 0
            metrics.largest_loss = min([t.pnl for t in losing_trades]) if losing_trades else 0

            # Consecutive metrics
            metrics.max_consecutive_wins = self.calculate_max_consecutive_wins(simulation_results.trades)
            metrics.max_consecutive_losses = self.calculate_max_consecutive_losses(simulation_results.trades)

        # Risk-adjusted metrics
        metrics.value_at_risk_95 = np.percentile(returns, 5)
        metrics.expected_shortfall_95 = np.mean([r for r in returns if r <= metrics.value_at_risk_95])
        metrics.tail_ratio = abs(np.percentile(returns, 95)) / abs(np.percentile(returns, 5))

        # Benchmark comparison (if provided)
        if backtest_request.benchmark_symbol:
            benchmark_performance = await self.calculate_benchmark_performance(
                backtest_request.benchmark_symbol,
                backtest_request.start_date,
                backtest_request.end_date
            )
            metrics.alpha = metrics.annualized_return - benchmark_performance.return
            metrics.beta = self.calculate_beta(returns, benchmark_performance.returns)
            metrics.information_ratio = metrics.alpha / np.std(returns - benchmark_performance.returns)

        return metrics

    def calculate_max_drawdown(self, portfolio_values: List[float]) -> float:
        """Calculate maximum drawdown"""

        peak = portfolio_values[0]
        max_dd = 0

        for value in portfolio_values:
            if value > peak:
                peak = value

            drawdown = (peak - value) / peak
            if drawdown > max_dd:
                max_dd = drawdown

        return max_dd

    def calculate_sortino_ratio(self, returns: List[float],
                              target_return: float = 0.0) -> float:
        """Calculate Sortino ratio (downside deviation)"""

        excess_returns = [r - target_return for r in returns]
        downside_returns = [r for r in excess_returns if r < 0]

        if not downside_returns:
            return float('inf')

        downside_deviation = np.sqrt(np.mean([r**2 for r in downside_returns])) * np.sqrt(252)
        excess_return = np.mean(excess_returns) * 252

        return excess_return / downside_deviation if downside_deviation > 0 else float('inf')
```

---

## 📊 Multi-Tenant Backtesting

### **Subscription-Based Features**:
```python
class BacktestFeatureManager:
    def __init__(self):
        self.tier_features = {
            SubscriptionTier.FREE: {
                "max_backtest_period_days": 365,      # 1 year max
                "max_symbols": 3,                     # 3 symbols max
                "optimization_enabled": False,
                "monte_carlo_simulations": 100,
                "walk_forward_analysis": False,
                "custom_benchmarks": False,
                "advanced_metrics": False
            },
            SubscriptionTier.PRO: {
                "max_backtest_period_days": 1825,     # 5 years max
                "max_symbols": 10,                    # 10 symbols max
                "optimization_enabled": True,
                "monte_carlo_simulations": 1000,
                "walk_forward_analysis": True,
                "custom_benchmarks": True,
                "advanced_metrics": True,
                "genetic_algorithm_optimization": True
            },
            SubscriptionTier.ENTERPRISE: {
                "max_backtest_period_days": 3650,     # 10 years max
                "max_symbols": 50,                    # 50 symbols max
                "optimization_enabled": True,
                "monte_carlo_simulations": 10000,
                "walk_forward_analysis": True,
                "custom_benchmarks": True,
                "advanced_metrics": True,
                "genetic_algorithm_optimization": True,
                "stress_testing": True,
                "custom_performance_metrics": True,
                "portfolio_backtesting": True
            }
        }

    async def validate_backtest_request(self, request: BacktestRequest,
                                      user_context: UserContext) -> ValidationResult:
        """Validate backtest request against subscription limits"""

        features = self.tier_features[user_context.subscription_tier]
        validation_result = ValidationResult()

        # Check period limit
        period_days = (request.end_date - request.start_date).days
        if period_days > features["max_backtest_period_days"]:
            validation_result.errors.append(
                f"Backtest period {period_days} days exceeds limit of {features['max_backtest_period_days']} days"
            )

        # Check symbol limit
        if len(request.symbols) > features["max_symbols"]:
            validation_result.errors.append(
                f"Symbol count {len(request.symbols)} exceeds limit of {features['max_symbols']}"
            )

        # Check feature availability
        if request.enable_optimization and not features["optimization_enabled"]:
            validation_result.errors.append("Strategy optimization not available in current subscription")

        if request.enable_walk_forward and not features["walk_forward_analysis"]:
            validation_result.errors.append("Walk-forward analysis not available in current subscription")

        validation_result.is_valid = len(validation_result.errors) == 0
        return validation_result
```

### **Company-Level Backtesting**:
```python
class CompanyBacktestManager:
    async def get_company_backtest_config(self, company_id: str) -> CompanyBacktestConfig:
        """Get company-specific backtesting configuration"""

        config = await self.database.get_company_backtest_config(company_id)

        if not config:
            # Default company config
            config = CompanyBacktestConfig(
                allowed_symbols=self.get_default_symbols(),
                max_concurrent_backtests=5,
                data_retention_days=90,
                shared_benchmark_library=True,
                risk_model_validation_required=False
            )

        return config

    async def manage_backtest_queue(self, company_id: str) -> BacktestQueue:
        """Manage company backtest execution queue"""

        company_config = await self.get_company_backtest_config(company_id)
        current_queue = await self.get_current_backtest_queue(company_id)

        # Prioritize backtests based on user tier and request time
        prioritized_queue = await self.prioritize_backtest_queue(current_queue)

        # Enforce concurrent limits
        if len(prioritized_queue.running_backtests) >= company_config.max_concurrent_backtests:
            # Queue additional requests
            return prioritized_queue

        # Start next backtests in queue
        available_slots = (company_config.max_concurrent_backtests -
                          len(prioritized_queue.running_backtests))

        for i in range(min(available_slots, len(prioritized_queue.pending_backtests))):
            backtest_request = prioritized_queue.pending_backtests.pop(0)
            await self.start_backtest_execution(backtest_request)
            prioritized_queue.running_backtests.append(backtest_request)

        return prioritized_queue
```

---

## ⚡ Performance Optimizations

### **Historical Data Caching**:
```python
class HistoricalDataCache:
    def __init__(self):
        self.data_cache = TTLCache(maxsize=100, ttl=3600)  # 1 hour TTL
        self.compression_enabled = True

    async def get_cached_data(self, symbols: List[str],
                            start_date: datetime,
                            end_date: datetime) -> Optional[HistoricalDataSet]:
        """Get cached historical data with intelligent compression"""

        cache_key = self.generate_cache_key(symbols, start_date, end_date)

        if cache_key in self.data_cache:
            compressed_data = self.data_cache[cache_key]
            if self.compression_enabled:
                return self.decompress_data(compressed_data)
            else:
                return compressed_data

        return None

    async def cache_historical_data(self, symbols: List[str],
                                  start_date: datetime,
                                  end_date: datetime,
                                  data: HistoricalDataSet):
        """Cache historical data with compression"""

        cache_key = self.generate_cache_key(symbols, start_date, end_date)

        if self.compression_enabled:
            compressed_data = self.compress_data(data)
            self.data_cache[cache_key] = compressed_data
        else:
            self.data_cache[cache_key] = data

    def compress_data(self, data: HistoricalDataSet) -> bytes:
        """Compress historical data using Protocol Buffers + gzip"""

        # Serialize to Protocol Buffers
        pb_data = data.SerializeToString()

        # Compress with gzip
        compressed = gzip.compress(pb_data)

        return compressed

    def decompress_data(self, compressed_data: bytes) -> HistoricalDataSet:
        """Decompress historical data"""

        # Decompress gzip
        pb_data = gzip.decompress(compressed_data)

        # Parse Protocol Buffers
        data = HistoricalDataSet()
        data.ParseFromString(pb_data)

        return data
```

### **Parallel Backtest Execution**:
```python
async def run_multiple_backtests(self, backtest_requests: List[BacktestRequest],
                               trace_context: TraceContext) -> List[BacktestResults]:
    """Parallel execution of multiple backtests"""

    # Create backtest tasks
    tasks = []
    for request in backtest_requests:
        task = asyncio.create_task(
            self.run_backtest(request, trace_context)
        )
        tasks.append(task)

    # Execute with controlled concurrency
    semaphore = asyncio.Semaphore(5)  # Max 5 concurrent backtests

    async def controlled_backtest(request):
        async with semaphore:
            return await self.run_backtest(request, trace_context)

    # Execute all backtests
    results = await asyncio.gather(*[
        controlled_backtest(request) for request in backtest_requests
    ], return_exceptions=True)

    # Handle exceptions
    successful_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            self.logger.error(f"Backtest {i} failed: {result}")
            # Add error to trace
            self.tracer.add_error(trace_context.correlation_id, str(result))
        else:
            successful_results.append(result)

    return successful_results
```

---

## 🔍 Health Monitoring & Performance

### **Service Health Check**:
```python
@app.get("/health")
async def health_check():
    """Comprehensive backtesting engine health check"""

    health_status = {
        "service": "backtesting-engine",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.5.0"
    }

    try:
        # Backtest performance metrics
        health_status["avg_backtest_time_seconds"] = await self.get_avg_backtest_time()
        health_status["backtest_success_rate"] = await self.get_backtest_success_rate()

        # Optimization performance
        health_status["optimization_completion_rate"] = await self.get_optimization_completion_rate()
        health_status["avg_optimization_time_seconds"] = await self.get_avg_optimization_time()

        # Data availability
        health_status["historical_data_coverage"] = await self.check_data_coverage()
        health_status["data_quality_score"] = await self.get_data_quality_score()

        # Resource utilization
        health_status["cpu_usage_percent"] = await self.get_cpu_usage()
        health_status["memory_usage_percent"] = await self.get_memory_usage()
        health_status["active_backtests"] = await self.get_active_backtest_count()

        # Cache performance
        health_status["cache_hit_rate"] = await self.get_cache_hit_rate()
        health_status["data_compression_ratio"] = await self.get_compression_ratio()

        # Circuit breaker status
        health_status["circuit_breakers"] = await self.get_circuit_breaker_summary()

    except Exception as e:
        health_status["status"] = "degraded"
        health_status["error"] = str(e)

    return health_status
```

---

## 🎯 Business Value

### **Strategy Validation Excellence**:
- **Sub-2 Second Backtests**: Fast strategy validation for rapid iteration
- **Walk-Forward Analysis**: Out-of-sample validation for robust strategies
- **Monte Carlo Simulation**: Strategy robustness and risk assessment
- **Comprehensive Metrics**: 20+ performance and risk metrics

### **Multi-Tenant Strategy Development**:
- **Subscription-Based Features**: Tiered backtesting capabilities
- **Company-Level Controls**: Shared benchmark libraries and risk models
- **Queue Management**: Fair resource allocation across users
- **Data Isolation**: Secure multi-tenant historical data access

### **Technical Excellence**:
- **Protocol Buffers**: 60% smaller backtest payloads, 10x faster processing
- **Intelligent Caching**: Historical data compression and smart TTL
- **Circuit Breaker Protected**: Data service failover for continuous operation
- **Parallel Execution**: Concurrent backtest processing for scalability

---

**Input Flow**: Trading-Engine (strategies) → Backtesting-Engine (validation)
**Output Flow**: Backtesting-Engine → Analytics-Service → User Dashboard
**Key Innovation**: Sub-2 second comprehensive strategy validation dengan walk-forward analysis dan Monte Carlo simulation untuk robust strategy development.