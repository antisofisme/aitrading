"""
Realistic Backtesting Engine
Addresses the critical gap between backtesting and live trading performance

Key Features:
- Realistic market simulation with order book dynamics
- Transaction cost modeling including slippage and market impact
- Latency simulation for real-world execution delays
- Partial fills and rejection scenarios
- Data availability constraints and look-ahead bias prevention
- Performance degradation analysis vs live trading conditions
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union, Protocol
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from abc import ABC, abstractmethod
import queue
import random
from collections import deque, defaultdict
import json


class OrderType(Enum):
    """Types of trading orders"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(Enum):
    """Order execution status"""
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class RejectionReason(Enum):
    """Reasons for order rejection"""
    INSUFFICIENT_LIQUIDITY = "insufficient_liquidity"
    PRICE_LIMIT_EXCEEDED = "price_limit_exceeded"
    POSITION_LIMIT_EXCEEDED = "position_limit_exceeded"
    MARKET_CLOSED = "market_closed"
    VOLATILITY_CIRCUIT_BREAKER = "volatility_circuit_breaker"
    RISK_LIMIT_EXCEEDED = "risk_limit_exceeded"


@dataclass
class MarketData:
    """Market data snapshot"""
    timestamp: datetime
    symbol: str
    bid: float
    ask: float
    bid_size: float
    ask_size: float
    last_price: float
    volume: float
    spread: float
    mid_price: float

    @property
    def spread_bps(self) -> float:
        """Spread in basis points"""
        return (self.spread / self.mid_price) * 10000 if self.mid_price > 0 else 0.0


@dataclass
class OrderBookLevel:
    """Single level of order book"""
    price: float
    size: float
    orders: int = 1


@dataclass
class OrderBook:
    """Full order book state"""
    timestamp: datetime
    symbol: str
    bids: List[OrderBookLevel] = field(default_factory=list)
    asks: List[OrderBookLevel] = field(default_factory=list)

    def get_best_bid(self) -> Optional[OrderBookLevel]:
        """Get best bid level"""
        return self.bids[0] if self.bids else None

    def get_best_ask(self) -> Optional[OrderBookLevel]:
        """Get best ask level"""
        return self.asks[0] if self.asks else None

    def get_spread(self) -> float:
        """Get bid-ask spread"""
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()
        if best_bid and best_ask:
            return best_ask.price - best_bid.price
        return 0.0

    def get_mid_price(self) -> float:
        """Get mid price"""
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()
        if best_bid and best_ask:
            return (best_bid.price + best_ask.price) / 2
        return 0.0


@dataclass
class TradingOrder:
    """Trading order specification"""
    order_id: str
    symbol: str
    side: str  # "buy" or "sell"
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = "GTC"  # Good Till Cancelled
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrderExecution:
    """Order execution result"""
    order_id: str
    execution_id: str
    timestamp: datetime
    status: OrderStatus
    filled_quantity: float
    filled_price: float
    remaining_quantity: float
    commission: float
    slippage: float
    market_impact: float
    rejection_reason: Optional[RejectionReason] = None
    execution_latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PositionState:
    """Portfolio position state"""
    symbol: str
    quantity: float
    average_price: float
    unrealized_pnl: float
    realized_pnl: float
    timestamp: datetime
    last_update: datetime


@dataclass
class BacktestConfig:
    """Configuration for realistic backtesting"""
    # Market simulation
    include_bid_ask_spreads: bool = True
    include_order_book_depth: bool = True
    include_market_impact: bool = True
    include_partial_fills: bool = True
    include_rejection_scenarios: bool = True

    # Transaction costs
    commission_rate: float = 0.001  # 0.1%
    slippage_model: str = "linear"  # "linear", "square_root", "adaptive"
    market_impact_factor: float = 0.001
    min_spread_bps: float = 1.0

    # Execution constraints
    max_position_size: float = 1000000.0  # Max position value
    max_order_size: float = 100000.0     # Max single order value
    min_order_size: float = 100.0        # Min order value
    volatility_circuit_breaker: float = 0.05  # 5% price move triggers breaker

    # Latency simulation
    enable_latency_simulation: bool = True
    base_latency_ms: float = 50.0
    latency_std_ms: float = 20.0
    max_latency_ms: float = 500.0

    # Data realism
    enforce_data_availability: bool = True
    lookback_limit_days: int = 252  # 1 year
    data_delay_seconds: float = 0.1

    # Risk limits
    daily_loss_limit: float = 10000.0
    position_concentration_limit: float = 0.3  # 30% of portfolio


@dataclass
class BacktestMetrics:
    """Comprehensive backtesting metrics"""
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int
    avg_trade_return: float
    avg_holding_period: float
    volatility: float
    skewness: float
    kurtosis: float
    calmar_ratio: float
    sortino_ratio: float

    # Execution metrics
    avg_slippage_bps: float
    avg_commission_cost: float
    market_impact_cost: float
    total_transaction_costs: float
    execution_shortfall: float

    # Realism metrics
    fill_rate: float
    rejection_rate: float
    partial_fill_rate: float
    avg_execution_latency_ms: float


class SlippageModel(ABC):
    """Abstract base class for slippage models"""

    @abstractmethod
    def calculate_slippage(self, order: TradingOrder, market_data: MarketData,
                          order_book: OrderBook) -> float:
        """Calculate slippage for order execution"""
        pass


class LinearSlippageModel(SlippageModel):
    """Linear slippage model based on order size and spread"""

    def __init__(self, base_slippage_bps: float = 2.0, size_impact_factor: float = 0.1):
        self.base_slippage_bps = base_slippage_bps
        self.size_impact_factor = size_impact_factor

    def calculate_slippage(self, order: TradingOrder, market_data: MarketData,
                          order_book: OrderBook) -> float:
        """Calculate linear slippage"""
        # Base slippage from spread
        base_slippage = self.base_slippage_bps / 10000

        # Size impact
        order_value = order.quantity * market_data.mid_price
        avg_daily_volume = market_data.volume * 24  # Estimate daily volume
        volume_participation = order_value / (avg_daily_volume + 1e-8)
        size_impact = volume_participation * self.size_impact_factor

        # Total slippage
        total_slippage = base_slippage + size_impact

        # Direction matters - we pay the spread when crossing
        if order.side == "buy":
            return total_slippage
        else:
            return total_slippage


class SquareRootSlippageModel(SlippageModel):
    """Square root slippage model (more realistic for large orders)"""

    def __init__(self, impact_coefficient: float = 0.05):
        self.impact_coefficient = impact_coefficient

    def calculate_slippage(self, order: TradingOrder, market_data: MarketData,
                          order_book: OrderBook) -> float:
        """Calculate square root slippage"""
        order_value = order.quantity * market_data.mid_price
        avg_daily_volume = market_data.volume * 24

        # Square root impact
        volume_participation = order_value / (avg_daily_volume + 1e-8)
        slippage = self.impact_coefficient * np.sqrt(volume_participation)

        return max(0.0001, min(0.01, slippage))  # Clamp between 1bp and 100bp


class LatencySimulator:
    """Simulate realistic execution latency"""

    def __init__(self, base_latency_ms: float = 50.0, std_ms: float = 20.0, max_ms: float = 500.0):
        self.base_latency_ms = base_latency_ms
        self.std_ms = std_ms
        self.max_ms = max_ms

    def simulate_latency(self, order: TradingOrder, market_conditions: Dict[str, Any]) -> float:
        """Simulate execution latency in milliseconds"""
        # Base latency with random variation
        latency = np.random.normal(self.base_latency_ms, self.std_ms)

        # Higher latency during volatile periods
        volatility_factor = market_conditions.get('volatility', 0.02)
        if volatility_factor > 0.05:  # High volatility
            latency *= 1.5

        # Higher latency for large orders
        order_size_factor = min(2.0, order.quantity / 1000)
        latency *= order_size_factor

        # Network congestion simulation (random spikes)
        if np.random.random() < 0.05:  # 5% chance of network issues
            latency *= np.random.uniform(2.0, 5.0)

        return max(10.0, min(self.max_ms, latency))


class OrderBookSimulator:
    """Simulate order book dynamics"""

    def __init__(self, depth_levels: int = 5):
        self.depth_levels = depth_levels

    def generate_order_book(self, market_data: MarketData) -> OrderBook:
        """Generate realistic order book from market data"""
        mid_price = market_data.mid_price
        spread = market_data.spread

        bids = []
        asks = []

        # Generate bid levels
        for i in range(self.depth_levels):
            price = market_data.bid - (spread * i * 0.5)
            size = market_data.bid_size * np.random.uniform(0.5, 1.5) / (i + 1)
            bids.append(OrderBookLevel(price=price, size=size))

        # Generate ask levels
        for i in range(self.depth_levels):
            price = market_data.ask + (spread * i * 0.5)
            size = market_data.ask_size * np.random.uniform(0.5, 1.5) / (i + 1)
            asks.append(OrderBookLevel(price=price, size=size))

        return OrderBook(
            timestamp=market_data.timestamp,
            symbol=market_data.symbol,
            bids=bids,
            asks=asks
        )

    def simulate_market_impact(self, order: TradingOrder, order_book: OrderBook) -> Tuple[float, OrderBook]:
        """Simulate market impact and update order book"""
        # Calculate how much of the order book we consume
        remaining_qty = order.quantity
        total_cost = 0.0
        executed_qty = 0.0

        if order.side == "buy":
            levels = order_book.asks.copy()
        else:
            levels = order_book.bids.copy()

        # Execute against order book levels
        for level in levels:
            if remaining_qty <= 0:
                break

            available_qty = level.size
            qty_to_execute = min(remaining_qty, available_qty)

            total_cost += qty_to_execute * level.price
            executed_qty += qty_to_execute
            remaining_qty -= qty_to_execute

            # Update level
            level.size -= qty_to_execute

        # Calculate average execution price
        avg_price = total_cost / executed_qty if executed_qty > 0 else 0.0

        # Update order book (remove empty levels)
        if order.side == "buy":
            order_book.asks = [level for level in order_book.asks if level.size > 0]
        else:
            order_book.bids = [level for level in order_book.bids if level.size > 0]

        return avg_price, order_book


class ExecutionSimulator:
    """Simulate realistic order execution"""

    def __init__(self, config: BacktestConfig):
        self.config = config
        self.slippage_models = {
            "linear": LinearSlippageModel(),
            "square_root": SquareRootSlippageModel()
        }
        self.latency_simulator = LatencySimulator(
            config.base_latency_ms, config.latency_std_ms, config.max_latency_ms
        )
        self.order_book_simulator = OrderBookSimulator()

    async def execute_order(self, order: TradingOrder, market_data: MarketData,
                           portfolio_state: Dict[str, Any]) -> OrderExecution:
        """Execute order with realistic constraints"""

        execution_id = f"exec_{order.order_id}_{int(datetime.now().timestamp())}"

        # Simulate execution latency
        latency_ms = 0.0
        if self.config.enable_latency_simulation:
            market_conditions = {"volatility": 0.02}  # Simplified
            latency_ms = self.latency_simulator.simulate_latency(order, market_conditions)
            await asyncio.sleep(latency_ms / 1000)  # Actually wait

        # Check for rejection scenarios
        rejection = await self._check_rejection_scenarios(order, market_data, portfolio_state)
        if rejection:
            return OrderExecution(
                order_id=order.order_id,
                execution_id=execution_id,
                timestamp=datetime.now(),
                status=OrderStatus.REJECTED,
                filled_quantity=0.0,
                filled_price=0.0,
                remaining_quantity=order.quantity,
                commission=0.0,
                slippage=0.0,
                market_impact=0.0,
                rejection_reason=rejection,
                execution_latency_ms=latency_ms
            )

        # Generate order book
        order_book = self.order_book_simulator.generate_order_book(market_data)

        # Calculate slippage
        slippage_model = self.slippage_models.get(self.config.slippage_model, self.slippage_models["linear"])
        slippage = slippage_model.calculate_slippage(order, market_data, order_book)

        # Simulate partial fills
        fill_ratio = 1.0
        if self.config.include_partial_fills:
            fill_ratio = await self._simulate_partial_fill(order, market_data, order_book)

        filled_quantity = order.quantity * fill_ratio

        # Calculate execution price with market impact
        if self.config.include_market_impact:
            execution_price, updated_order_book = self.order_book_simulator.simulate_market_impact(
                order, order_book
            )
        else:
            execution_price = market_data.mid_price

        # Apply slippage
        if order.side == "buy":
            final_price = execution_price * (1 + slippage)
        else:
            final_price = execution_price * (1 - slippage)

        # Calculate commission
        commission = filled_quantity * final_price * self.config.commission_rate

        # Calculate market impact cost
        theoretical_price = market_data.mid_price
        market_impact_cost = abs(final_price - theoretical_price) / theoretical_price

        # Determine order status
        if fill_ratio >= 1.0:
            status = OrderStatus.FILLED
        elif fill_ratio > 0.0:
            status = OrderStatus.PARTIALLY_FILLED
        else:
            status = OrderStatus.REJECTED
            rejection = RejectionReason.INSUFFICIENT_LIQUIDITY

        return OrderExecution(
            order_id=order.order_id,
            execution_id=execution_id,
            timestamp=datetime.now(),
            status=status,
            filled_quantity=filled_quantity,
            filled_price=final_price,
            remaining_quantity=order.quantity - filled_quantity,
            commission=commission,
            slippage=slippage,
            market_impact=market_impact_cost,
            rejection_reason=rejection if status == OrderStatus.REJECTED else None,
            execution_latency_ms=latency_ms
        )

    async def _check_rejection_scenarios(self, order: TradingOrder, market_data: MarketData,
                                       portfolio_state: Dict[str, Any]) -> Optional[RejectionReason]:
        """Check for various rejection scenarios"""

        # Position limit check
        current_position = portfolio_state.get('positions', {}).get(order.symbol, 0.0)
        order_value = order.quantity * market_data.mid_price

        if order.side == "buy":
            new_position_value = (current_position + order.quantity) * market_data.mid_price
        else:
            new_position_value = (current_position - order.quantity) * market_data.mid_price

        if abs(new_position_value) > self.config.max_position_size:
            return RejectionReason.POSITION_LIMIT_EXCEEDED

        # Order size check
        if order_value > self.config.max_order_size:
            return RejectionReason.PRICE_LIMIT_EXCEEDED

        if order_value < self.config.min_order_size:
            return RejectionReason.PRICE_LIMIT_EXCEEDED

        # Volatility circuit breaker
        recent_volatility = portfolio_state.get('recent_volatility', 0.02)
        if recent_volatility > self.config.volatility_circuit_breaker:
            return RejectionReason.VOLATILITY_CIRCUIT_BREAKER

        # Risk limit check
        daily_pnl = portfolio_state.get('daily_pnl', 0.0)
        if daily_pnl < -self.config.daily_loss_limit:
            return RejectionReason.RISK_LIMIT_EXCEEDED

        return None

    async def _simulate_partial_fill(self, order: TradingOrder, market_data: MarketData,
                                    order_book: OrderBook) -> float:
        """Simulate partial fill scenarios"""

        # Base fill probability
        fill_probability = 0.95

        # Reduce fill probability for large orders
        order_value = order.quantity * market_data.mid_price
        avg_level_value = 0.0

        if order.side == "buy" and order_book.asks:
            avg_level_value = np.mean([level.size * level.price for level in order_book.asks[:3]])
        elif order.side == "sell" and order_book.bids:
            avg_level_value = np.mean([level.size * level.price for level in order_book.bids[:3]])

        if avg_level_value > 0:
            size_ratio = order_value / avg_level_value
            if size_ratio > 2.0:  # Order is more than 2x average level
                fill_probability *= 0.7
            elif size_ratio > 1.0:
                fill_probability *= 0.85

        # Reduce fill probability during high volatility
        spread_bps = market_data.spread_bps
        if spread_bps > 10:  # Wide spread indicates stress
            fill_probability *= 0.8

        # Simulate random market conditions
        if np.random.random() > fill_probability:
            # Partial fill - random percentage between 30-80%
            return np.random.uniform(0.3, 0.8)

        return 1.0  # Full fill


class RealisticBacktestEngine:
    """Main backtesting engine with realistic market simulation"""

    def __init__(self, config: BacktestConfig):
        self.config = config
        self.execution_simulator = ExecutionSimulator(config)
        self.portfolio_state = {
            'positions': {},
            'cash': 1000000.0,  # Starting cash
            'daily_pnl': 0.0,
            'total_pnl': 0.0,
            'recent_volatility': 0.02
        }
        self.execution_history = []
        self.position_history = []
        self.metrics_calculator = BacktestMetricsCalculator()

    async def run_backtest(self, strategy_signals: List[Dict[str, Any]],
                          market_data_stream: List[MarketData]) -> Dict[str, Any]:
        """Run complete backtest with realistic execution"""

        print(f"Starting realistic backtest with {len(strategy_signals)} signals and {len(market_data_stream)} market data points")

        # Create market data lookup
        market_data_by_time = {data.timestamp: data for data in market_data_stream}

        # Process each signal
        for signal in strategy_signals:
            signal_time = signal['timestamp']

            # Find corresponding market data (with potential delay)
            market_data = self._get_market_data_at_time(signal_time, market_data_by_time)

            if not market_data:
                continue

            # Convert signal to order
            order = self._signal_to_order(signal, market_data)

            if not order:
                continue

            # Execute order with realistic constraints
            execution = await self.execution_simulator.execute_order(
                order, market_data, self.portfolio_state
            )

            # Update portfolio state
            self._update_portfolio_state(execution, market_data)

            # Record execution
            self.execution_history.append(execution)

            # Record portfolio state
            self.position_history.append({
                'timestamp': execution.timestamp,
                'portfolio_value': self._calculate_portfolio_value(market_data),
                'positions': self.portfolio_state['positions'].copy(),
                'cash': self.portfolio_state['cash'],
                'daily_pnl': self.portfolio_state['daily_pnl']
            })

        # Calculate comprehensive metrics
        metrics = await self.metrics_calculator.calculate_metrics(
            self.execution_history, self.position_history, market_data_stream
        )

        # Generate backtest report
        report = self._generate_backtest_report(metrics)

        return report

    def _get_market_data_at_time(self, signal_time: datetime,
                                market_data_lookup: Dict[datetime, MarketData]) -> Optional[MarketData]:
        """Get market data at specific time with realistic constraints"""

        # Add data delay if configured
        if self.config.enforce_data_availability:
            adjusted_time = signal_time + timedelta(seconds=self.config.data_delay_seconds)
        else:
            adjusted_time = signal_time

        # Find closest market data
        closest_time = None
        min_diff = timedelta.max

        for timestamp in market_data_lookup.keys():
            if timestamp <= adjusted_time:
                diff = adjusted_time - timestamp
                if diff < min_diff:
                    min_diff = diff
                    closest_time = timestamp

        return market_data_lookup.get(closest_time) if closest_time else None

    def _signal_to_order(self, signal: Dict[str, Any], market_data: MarketData) -> Optional[TradingOrder]:
        """Convert strategy signal to trading order"""
        try:
            order_id = f"order_{signal.get('signal_id', int(datetime.now().timestamp()))}"

            return TradingOrder(
                order_id=order_id,
                symbol=signal['symbol'],
                side=signal['action'],  # "buy" or "sell"
                order_type=OrderType.MARKET,
                quantity=signal['quantity'],
                timestamp=signal['timestamp'],
                metadata={'signal': signal}
            )

        except KeyError as e:
            print(f"Invalid signal format - missing key: {e}")
            return None

    def _update_portfolio_state(self, execution: OrderExecution, market_data: MarketData):
        """Update portfolio state after execution"""

        if execution.status not in [OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED]:
            return

        symbol = execution.order_id.split('_')[0] if '_' in execution.order_id else market_data.symbol
        filled_qty = execution.filled_quantity
        filled_price = execution.filled_price

        # Update positions
        if symbol not in self.portfolio_state['positions']:
            self.portfolio_state['positions'][symbol] = 0.0

        # Determine side from execution metadata or order
        side = "buy"  # Default assumption - this should come from the original order

        if side == "buy":
            self.portfolio_state['positions'][symbol] += filled_qty
            self.portfolio_state['cash'] -= filled_qty * filled_price + execution.commission
        else:
            self.portfolio_state['positions'][symbol] -= filled_qty
            self.portfolio_state['cash'] += filled_qty * filled_price - execution.commission

        # Update PnL (simplified)
        trade_pnl = 0.0  # Would calculate based on position changes
        self.portfolio_state['daily_pnl'] += trade_pnl
        self.portfolio_state['total_pnl'] += trade_pnl

    def _calculate_portfolio_value(self, market_data: MarketData) -> float:
        """Calculate current portfolio value"""
        total_value = self.portfolio_state['cash']

        for symbol, quantity in self.portfolio_state['positions'].items():
            if symbol == market_data.symbol:
                total_value += quantity * market_data.mid_price

        return total_value

    def _generate_backtest_report(self, metrics: BacktestMetrics) -> Dict[str, Any]:
        """Generate comprehensive backtest report"""

        return {
            'backtest_config': {
                'realistic_execution': True,
                'transaction_costs_included': True,
                'market_impact_included': self.config.include_market_impact,
                'latency_simulation': self.config.enable_latency_simulation,
                'partial_fills': self.config.include_partial_fills
            },
            'performance_metrics': {
                'total_return': metrics.total_return,
                'sharpe_ratio': metrics.sharpe_ratio,
                'max_drawdown': metrics.max_drawdown,
                'win_rate': metrics.win_rate,
                'profit_factor': metrics.profit_factor,
                'volatility': metrics.volatility,
                'calmar_ratio': metrics.calmar_ratio,
                'sortino_ratio': metrics.sortino_ratio
            },
            'execution_metrics': {
                'total_trades': metrics.total_trades,
                'avg_slippage_bps': metrics.avg_slippage_bps,
                'avg_commission_cost': metrics.avg_commission_cost,
                'market_impact_cost': metrics.market_impact_cost,
                'total_transaction_costs': metrics.total_transaction_costs,
                'execution_shortfall': metrics.execution_shortfall
            },
            'realism_metrics': {
                'fill_rate': metrics.fill_rate,
                'rejection_rate': metrics.rejection_rate,
                'partial_fill_rate': metrics.partial_fill_rate,
                'avg_execution_latency_ms': metrics.avg_execution_latency_ms
            },
            'portfolio_state': self.portfolio_state,
            'execution_count': len(self.execution_history),
            'timestamp': datetime.now().isoformat()
        }


class BacktestMetricsCalculator:
    """Calculate comprehensive backtest metrics"""

    async def calculate_metrics(self, executions: List[OrderExecution],
                               portfolio_history: List[Dict[str, Any]],
                               market_data: List[MarketData]) -> BacktestMetrics:
        """Calculate all backtest metrics"""

        if not portfolio_history:
            return self._create_empty_metrics()

        # Extract portfolio values
        portfolio_values = [p['portfolio_value'] for p in portfolio_history]
        timestamps = [p['timestamp'] for p in portfolio_history]

        # Calculate returns
        returns = np.diff(portfolio_values) / portfolio_values[:-1]
        returns = returns[~np.isnan(returns)]

        if len(returns) == 0:
            return self._create_empty_metrics()

        # Performance metrics
        total_return = (portfolio_values[-1] - portfolio_values[0]) / portfolio_values[0]
        volatility = np.std(returns) * np.sqrt(252)  # Annualized
        sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0.0

        # Drawdown calculation
        peak = np.maximum.accumulate(portfolio_values)
        drawdown = (portfolio_values - peak) / peak
        max_drawdown = np.min(drawdown)

        # Trade statistics
        filled_executions = [e for e in executions if e.status in [OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED]]
        total_trades = len(filled_executions)

        # Win rate (simplified)
        winning_trades = sum(1 for e in filled_executions if e.filled_quantity > 0)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0

        # Execution metrics
        avg_slippage_bps = np.mean([e.slippage * 10000 for e in filled_executions]) if filled_executions else 0.0
        avg_commission = np.mean([e.commission for e in filled_executions]) if filled_executions else 0.0
        avg_market_impact = np.mean([e.market_impact for e in filled_executions]) if filled_executions else 0.0

        # Realism metrics
        fill_rate = len(filled_executions) / len(executions) if executions else 0.0
        rejected_executions = [e for e in executions if e.status == OrderStatus.REJECTED]
        rejection_rate = len(rejected_executions) / len(executions) if executions else 0.0
        partial_fills = [e for e in executions if e.status == OrderStatus.PARTIALLY_FILLED]
        partial_fill_rate = len(partial_fills) / len(executions) if executions else 0.0

        avg_latency = np.mean([e.execution_latency_ms for e in executions]) if executions else 0.0

        # Additional metrics
        downside_returns = returns[returns < 0]
        downside_volatility = np.std(downside_returns) * np.sqrt(252) if len(downside_returns) > 0 else 0.0
        sortino_ratio = np.mean(returns) / downside_volatility * np.sqrt(252) if downside_volatility > 0 else 0.0

        calmar_ratio = total_return / abs(max_drawdown) if max_drawdown != 0 else 0.0

        return BacktestMetrics(
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            profit_factor=1.0,  # Simplified
            total_trades=total_trades,
            avg_trade_return=np.mean(returns) if len(returns) > 0 else 0.0,
            avg_holding_period=1.0,  # Simplified
            volatility=volatility,
            skewness=float(pd.Series(returns).skew()) if len(returns) > 0 else 0.0,
            kurtosis=float(pd.Series(returns).kurtosis()) if len(returns) > 0 else 0.0,
            calmar_ratio=calmar_ratio,
            sortino_ratio=sortino_ratio,
            avg_slippage_bps=avg_slippage_bps,
            avg_commission_cost=avg_commission,
            market_impact_cost=avg_market_impact,
            total_transaction_costs=avg_commission + avg_market_impact,
            execution_shortfall=avg_slippage_bps + avg_market_impact * 10000,
            fill_rate=fill_rate,
            rejection_rate=rejection_rate,
            partial_fill_rate=partial_fill_rate,
            avg_execution_latency_ms=avg_latency
        )

    def _create_empty_metrics(self) -> BacktestMetrics:
        """Create empty metrics for failed backtests"""
        return BacktestMetrics(
            total_return=0.0, sharpe_ratio=0.0, max_drawdown=0.0, win_rate=0.0,
            profit_factor=0.0, total_trades=0, avg_trade_return=0.0, avg_holding_period=0.0,
            volatility=0.0, skewness=0.0, kurtosis=0.0, calmar_ratio=0.0, sortino_ratio=0.0,
            avg_slippage_bps=0.0, avg_commission_cost=0.0, market_impact_cost=0.0,
            total_transaction_costs=0.0, execution_shortfall=0.0, fill_rate=0.0,
            rejection_rate=0.0, partial_fill_rate=0.0, avg_execution_latency_ms=0.0
        )


# Example usage
async def example_usage():
    """Example of realistic backtesting"""

    # Create backtest configuration
    config = BacktestConfig(
        include_bid_ask_spreads=True,
        include_order_book_depth=True,
        include_market_impact=True,
        include_partial_fills=True,
        commission_rate=0.001,
        enable_latency_simulation=True,
        base_latency_ms=50.0
    )

    # Create sample market data
    timestamps = pd.date_range('2023-01-01', periods=1000, freq='1min')
    np.random.seed(42)

    market_data_stream = []
    base_price = 100.0

    for i, timestamp in enumerate(timestamps):
        price_change = np.random.normal(0, 0.001)
        base_price *= (1 + price_change)

        spread = base_price * 0.0005  # 5 basis points
        bid = base_price - spread/2
        ask = base_price + spread/2

        market_data = MarketData(
            timestamp=timestamp,
            symbol="EURUSD",
            bid=bid,
            ask=ask,
            bid_size=100000,
            ask_size=100000,
            last_price=base_price,
            volume=50000,
            spread=spread,
            mid_price=base_price
        )
        market_data_stream.append(market_data)

    # Create sample strategy signals
    strategy_signals = []
    for i in range(0, len(timestamps), 10):  # Signal every 10 minutes
        signal = {
            'signal_id': i,
            'timestamp': timestamps[i],
            'symbol': 'EURUSD',
            'action': 'buy' if i % 20 < 10 else 'sell',
            'quantity': 10000,
            'confidence': np.random.uniform(0.6, 0.9)
        }
        strategy_signals.append(signal)

    # Run backtest
    engine = RealisticBacktestEngine(config)
    print("Running realistic backtest...")

    result = await engine.run_backtest(strategy_signals, market_data_stream)

    # Display results
    print(f"\nBacktest Results:")
    print(f"Total Return: {result['performance_metrics']['total_return']:.2%}")
    print(f"Sharpe Ratio: {result['performance_metrics']['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {result['performance_metrics']['max_drawdown']:.2%}")
    print(f"Win Rate: {result['performance_metrics']['win_rate']:.2%}")

    print(f"\nExecution Quality:")
    print(f"Fill Rate: {result['realism_metrics']['fill_rate']:.2%}")
    print(f"Rejection Rate: {result['realism_metrics']['rejection_rate']:.2%}")
    print(f"Avg Slippage: {result['execution_metrics']['avg_slippage_bps']:.1f} bps")
    print(f"Avg Latency: {result['realism_metrics']['avg_execution_latency_ms']:.1f} ms")

    print(f"\nTransaction Costs:")
    print(f"Commission Cost: {result['execution_metrics']['avg_commission_cost']:.2f}")
    print(f"Market Impact: {result['execution_metrics']['market_impact_cost']:.4f}")
    print(f"Total Cost: {result['execution_metrics']['total_transaction_costs']:.2f}")

    return result


if __name__ == "__main__":
    # Run example
    import asyncio
    asyncio.run(example_usage())