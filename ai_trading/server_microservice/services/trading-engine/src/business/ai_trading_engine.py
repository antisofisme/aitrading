"""
AI Trading Engine - Business Logic Layer for Trading-Engine Service
Moved from server_side MT5 bridge to proper microservices architecture
"""

import asyncio
import json
import time
import httpx
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import numpy as np

# Local infrastructure integration
from ...shared.infrastructure.core.logger_core import CoreLogger
from ...shared.infrastructure.core.config_core import CoreConfig
from ...shared.infrastructure.core.error_core import CoreErrorHandler
from ...shared.infrastructure.core.performance_core import CorePerformance
from ...shared.infrastructure.core.cache_core import CoreCache

# Initialize local infrastructure components
logger = CoreLogger("trading-engine", "ai_trading")
config = CoreConfig("trading-engine")
error_handler = CoreErrorHandler("trading-engine")
performance_tracker = CorePerformance("trading-engine")
cache = CoreCache("trading-engine")


class TradingSignal(Enum):
    """Trading signal types"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class OrderType(Enum):
    """Order types for MT5 execution"""
    BUY = "buy"
    SELL = "sell"
    BUY_LIMIT = "buy_limit"
    SELL_LIMIT = "sell_limit"
    BUY_STOP = "buy_stop"
    SELL_STOP = "sell_stop"


@dataclass
class AiTradingConfig:
    """Configuration for AI trading engine"""
    enable_ai_validation: bool = True
    require_pattern_confirmation: bool = False
    ai_confidence_threshold: float = 0.75
    min_signal_strength: float = 0.3
    max_risk_per_trade: float = 0.02
    max_daily_risk: float = 0.05
    max_positions: int = 5
    max_drawdown_limit: float = 0.1
    min_lots_per_trade: float = 0.01
    max_lots_per_trade: float = 1.0
    require_ensemble_consensus: bool = True
    enable_pattern_confirmation: bool = True


@dataclass
class TradingOrder:
    """Trading order structure for MT5 execution"""
    symbol: str
    order_type: OrderType
    volume: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    ai_confidence: float = 0.0
    pattern_confidence: float = 0.0
    ensemble_consensus: float = 0.0
    prediction_source: str = ""
    risk_amount: float = 0.0
    comment: str = ""
    magic_number: int = 123456


@dataclass
class TradingResult:
    """Result of trade execution"""
    success: bool
    order_ticket: Optional[int]
    execution_price: Optional[float]
    slippage: float
    execution_time: float
    ai_validation_passed: bool
    risk_validation_passed: bool
    pattern_confirmation: bool
    error_code: Optional[int] = None
    error_description: Optional[str] = None
    timestamp: datetime = None
    execution_id: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class MT5BridgeClient:
    """HTTP client for communicating with MT5-Bridge microservice"""
    
    def __init__(self, mt5_bridge_url: str = "http://localhost:8001"):
        self.base_url = mt5_bridge_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.logger = get_logger("trading-engine", "mt5_client")
    
    async def execute_market_order(
        self,
        symbol: str,
        order_type: OrderType,
        volume: float,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        comment: str = "Trading-Engine Order"
    ) -> Dict[str, Any]:
        """Execute market order via MT5-Bridge service"""
        try:
            payload = {
                "symbol": symbol,
                "order_type": order_type.value,
                "volume": volume,
                "sl": sl,
                "tp": tp,
                "comment": comment
            }
            
            response = await self.client.post(f"{self.base_url}/order", json=payload)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            self.logger.error(f"❌ Failed to execute order via MT5-Bridge: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_current_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current market data via MT5-Bridge service"""
        try:
            response = await self.client.post(f"{self.base_url}/symbol", json={"symbol": symbol})
            response.raise_for_status()
            
            result = response.json()
            if result.get("success"):
                return result.get("symbol")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get market data for {symbol}: {e}")
            return None
    
    async def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get account information via MT5-Bridge service"""
        try:
            response = await self.client.get(f"{self.base_url}/account")
            response.raise_for_status()
            
            result = response.json()
            if result.get("success"):
                return result.get("account")
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get account info: {e}")
            return None
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


class AiTradingEngine:
    """
    AI Trading Engine - Business Logic Layer
    
    Handles:
    - AI prediction processing and signal generation
    - Risk management and trade validation
    - Position sizing and SL/TP calculation
    - Communication with MT5-Bridge for execution
    """
    
    def __init__(self, config: AiTradingConfig = None):
        self.config = config or AiTradingConfig()
        self.logger = get_logger("trading-engine", "ai_trading_engine")
        
        # MT5 Bridge client for infrastructure operations
        self.mt5_client = MT5BridgeClient()
        
        # Risk tracking
        self.risk_metrics = {
            "daily_risk_used": 0.0,
            "max_drawdown": 0.0,
            "position_count": 0,
            "margin_level": 1000.0
        }
        
        # Account info cache
        self.account_info = {"balance": 10000.0, "equity": 10000.0}
        
        self.logger.info("🤖 AI Trading Engine initialized")
    
    async def execute_ai_trade(
        self,
        symbol: str,
        prediction: Dict[str, Any],  # AI prediction data
        pattern_result: Optional[Dict[str, Any]] = None
    ) -> TradingResult:
        """Execute trade based on AI predictions with full validation"""
        try:
            self.logger.info(f"🤖 Executing AI trade for {symbol}")
            
            # Step 1: Generate trading signal from AI predictions
            trading_signal = await self._generate_trading_signal(prediction, pattern_result)
            
            # Step 2: AI validation
            if self.config.enable_ai_validation:
                ai_validation = await self._validate_trade_with_ai(symbol, trading_signal, prediction)
                if not ai_validation['approved']:
                    self.logger.warning(f"⚠️ AI validation rejected trade: {ai_validation['reason']}")
                    return TradingResult(
                        success=False,
                        order_ticket=None,
                        execution_price=None,
                        slippage=0,
                        execution_time=0,
                        ai_validation_passed=False,
                        risk_validation_passed=False,
                        pattern_confirmation=False,
                        error_description=ai_validation['reason'],
                        timestamp=datetime.now()
                    )
            
            # Step 3: Risk validation
            risk_validation = await self._validate_trade_risk(symbol, trading_signal)
            if not risk_validation['approved']:
                self.logger.warning(f"⚠️ Risk validation rejected trade: {risk_validation['reason']}")
                return TradingResult(
                    success=False,
                    order_ticket=None,
                    execution_price=None,
                    slippage=0,
                    execution_time=0,
                    ai_validation_passed=True,
                    risk_validation_passed=False,
                    pattern_confirmation=False,
                    error_description=risk_validation['reason'],
                    timestamp=datetime.now()
                )
            
            # Step 4: Create optimized trading order
            trading_order = await self._create_optimized_order(
                symbol, trading_signal, prediction, pattern_result
            )
            
            # Step 5: Execute the trade via MT5-Bridge
            execution_result = await self._execute_order_via_bridge(trading_order)
            
            # Step 6: Store trade for learning (future implementation)
            if execution_result.success:
                await self._store_trade_for_learning(trading_order, execution_result, prediction)
            
            return execution_result
            
        except Exception as e:
            self.logger.error(f"❌ AI trade execution failed: {e}")
            return TradingResult(
                success=False,
                order_ticket=None,
                execution_price=None,
                slippage=0,
                execution_time=0,
                ai_validation_passed=False,
                risk_validation_passed=False,
                pattern_confirmation=False,
                error_description=str(e),
                timestamp=datetime.now()
            )
    
    async def _generate_trading_signal(
        self,
        prediction: Dict[str, Any],
        pattern_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate trading signal from AI predictions"""
        try:
            # Extract prediction data
            symbol = prediction.get('symbol', 'EURUSD')
            pred_price = prediction.get('ensemble_prediction', 0.0)
            confidence = prediction.get('ensemble_confidence', 0.0)
            ai_score = prediction.get('ai_validation_score', 0.0)
            
            # Get current market data via MT5-Bridge
            current_data = await self.mt5_client.get_current_market_data(symbol)
            if not current_data:
                raise ValueError("Unable to get current market data")
            
            current_price = current_data.get('bid', pred_price)
            
            # Calculate signal strength
            price_change_pct = (pred_price - current_price) / current_price if current_price > 0 else 0
            
            # Determine signal type
            if abs(price_change_pct) < 0.0001:  # Less than 1 pip for major pairs
                signal_type = TradingSignal.HOLD
                signal_strength = 0.0
            elif price_change_pct > 0.002:  # More than 20 pips bullish
                signal_type = TradingSignal.STRONG_BUY
                signal_strength = min(confidence * abs(price_change_pct) * 100, 1.0)
            elif price_change_pct > 0.0005:  # More than 5 pips bullish
                signal_type = TradingSignal.BUY
                signal_strength = min(confidence * abs(price_change_pct) * 50, 1.0)
            elif price_change_pct < -0.002:  # More than 20 pips bearish
                signal_type = TradingSignal.STRONG_SELL
                signal_strength = min(confidence * abs(price_change_pct) * 100, 1.0)
            elif price_change_pct < -0.0005:  # More than 5 pips bearish
                signal_type = TradingSignal.SELL
                signal_strength = min(confidence * abs(price_change_pct) * 50, 1.0)
            else:
                signal_type = TradingSignal.HOLD
                signal_strength = 0.0
            
            # Pattern confirmation
            pattern_confirmation = False
            pattern_strength = 0.0
            if pattern_result:
                pattern_confidence = pattern_result.get('recognition_confidence', 0.0)
                pattern_confirmation = pattern_confidence > 0.6
                pattern_strength = pattern_confidence
            
            # Calculate final signal strength
            final_strength = signal_strength
            if pattern_confirmation:
                final_strength = (signal_strength + pattern_strength) / 2
            
            return {
                'signal_type': signal_type,
                'signal_strength': final_strength,
                'predicted_price': pred_price,
                'current_price': current_price,
                'price_change_pct': price_change_pct,
                'ai_confidence': confidence,
                'ai_score': ai_score,
                'pattern_confirmation': pattern_confirmation,
                'pattern_strength': pattern_strength,
                'market_data': current_data
            }
            
        except Exception as e:
            self.logger.error(f"❌ Signal generation failed: {e}")
            return {
                'signal_type': TradingSignal.HOLD,
                'signal_strength': 0.0,
                'error': str(e)
            }
    
    async def _validate_trade_with_ai(
        self,
        symbol: str,
        trading_signal: Dict[str, Any],
        prediction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate trade using AI services"""
        try:
            # Check AI confidence threshold
            ai_confidence = trading_signal.get('ai_confidence', 0.0)
            if ai_confidence < self.config.ai_confidence_threshold:
                return {
                    'approved': False,
                    'reason': f'AI confidence {ai_confidence:.2f} below threshold {self.config.ai_confidence_threshold}'
                }
            
            # Check ensemble consensus if required
            if self.config.require_ensemble_consensus:
                model_agreement = prediction.get('model_agreement', 0.0)
                if model_agreement < 0.6:  # 60% agreement threshold
                    return {
                        'approved': False,
                        'reason': f'Ensemble model agreement {model_agreement:.2f} too low'
                    }
            
            # Pattern confirmation check
            if self.config.enable_pattern_confirmation:
                pattern_confirmation = trading_signal.get('pattern_confirmation', False)
                if not pattern_confirmation:
                    self.logger.warning("⚠️ Pattern confirmation missing but proceeding")
            
            return {
                'approved': True,
                'reason': 'AI validation passed',
                'confidence': ai_confidence,
                'pattern_confirmed': trading_signal.get('pattern_confirmation', False)
            }
            
        except Exception as e:
            self.logger.error(f"❌ AI validation failed: {e}")
            return {'approved': False, 'reason': f'AI validation error: {e}'}
    
    async def _validate_trade_risk(self, symbol: str, trading_signal: Dict[str, Any]) -> Dict[str, Any]:
        """Validate trade against risk management rules"""
        try:
            # Check signal strength
            signal_strength = trading_signal.get('signal_strength', 0.0)
            if signal_strength < self.config.min_signal_strength:
                return {'approved': False, 'reason': f'Signal strength {signal_strength:.2f} too weak'}
            
            # Update risk metrics
            await self._update_risk_metrics()
            
            # Check daily risk limit
            if self.risk_metrics['daily_risk_used'] >= self.config.max_daily_risk:
                return {'approved': False, 'reason': 'Daily risk limit exceeded'}
            
            # Check max drawdown
            if self.risk_metrics['max_drawdown'] >= self.config.max_drawdown_limit:
                return {'approved': False, 'reason': 'Max drawdown limit reached'}
            
            # Check max positions
            if self.risk_metrics['position_count'] >= self.config.max_positions:
                return {'approved': False, 'reason': 'Max positions limit reached'}
            
            # Check margin requirements
            if self.risk_metrics['margin_level'] < 200:  # 200% minimum margin level
                return {'approved': False, 'reason': 'Insufficient margin'}
            
            return {'approved': True, 'reason': 'Risk validation passed'}
            
        except Exception as e:
            self.logger.error(f"❌ Risk validation failed: {e}")
            return {'approved': False, 'reason': f'Risk validation error: {e}'}
    
    async def _create_optimized_order(
        self,
        symbol: str,
        trading_signal: Dict[str, Any],
        prediction: Dict[str, Any],
        pattern_result: Optional[Dict[str, Any]]
    ) -> TradingOrder:
        """Create optimized trading order with dynamic position sizing"""
        try:
            signal_type = trading_signal['signal_type']
            
            # Determine order type
            if signal_type in [TradingSignal.BUY, TradingSignal.STRONG_BUY]:
                order_type = OrderType.BUY
            elif signal_type in [TradingSignal.SELL, TradingSignal.STRONG_SELL]:
                order_type = OrderType.SELL
            else:
                raise ValueError("Invalid signal type for order creation")
            
            # Calculate optimal position size
            position_size = await self._calculate_position_size(symbol, trading_signal)
            
            # Calculate stop loss and take profit
            stop_loss, take_profit = await self._calculate_sl_tp(symbol, trading_signal, order_type)
            
            # Create order
            order = TradingOrder(
                symbol=symbol,
                order_type=order_type,
                volume=position_size,
                stop_loss=stop_loss,
                take_profit=take_profit,
                ai_confidence=trading_signal.get('ai_confidence', 0.0),
                pattern_confidence=trading_signal.get('pattern_strength', 0.0),
                ensemble_consensus=prediction.get('model_agreement', 0.0),
                prediction_source=prediction.get('source', 'AI Engine'),
                risk_amount=self.config.max_risk_per_trade * self.account_info['balance'],
                comment=f"AI Bot - {signal_type.value} - Conf:{trading_signal.get('ai_confidence', 0):.2f}"
            )
            
            return order
            
        except Exception as e:
            self.logger.error(f"❌ Order creation failed: {e}")
            raise
    
    async def _calculate_position_size(self, symbol: str, trading_signal: Dict[str, Any]) -> float:
        """Calculate optimal position size using dynamic risk management"""
        try:
            # Get account balance
            balance = self.account_info['balance']
            
            # Base risk amount (2% of balance by default)
            risk_amount = balance * self.config.max_risk_per_trade
            
            # Estimate stop loss distance
            signal_strength = trading_signal.get('signal_strength', 0.5)
            current_price = trading_signal.get('current_price', 1.0)
            
            # Dynamic stop loss based on signal strength and volatility
            stop_distance_pips = max(10, int(50 * (1 - signal_strength)))  # 10-50 pips
            
            # Calculate pip value (simplified)
            if symbol.endswith('JPY'):
                pip_size = 0.01
            else:
                pip_size = 0.0001
            
            stop_distance_price = stop_distance_pips * pip_size
            
            # Calculate position size based on risk and stop distance
            if stop_distance_price > 0 and current_price > 0:
                # Simplified position sizing - in production, use proper pip value calculation
                position_size = risk_amount / (stop_distance_price * current_price * 100000)  # Assuming standard lot
            else:
                position_size = self.config.min_lots_per_trade
            
            # Apply constraints
            position_size = max(self.config.min_lots_per_trade, position_size)
            position_size = min(self.config.max_lots_per_trade, position_size)
            
            # Round to valid lot size (0.01 step)
            position_size = round(position_size, 2)
            
            self.logger.info(f"📊 Position size calculated: {position_size} lots for {symbol} "
                           f"(Risk: ${risk_amount:.2f}, Signal: {signal_strength:.2f})")
            
            return position_size
            
        except Exception as e:
            self.logger.error(f"❌ Position size calculation failed: {e}")
            return self.config.min_lots_per_trade
    
    async def _calculate_sl_tp(
        self,
        symbol: str,
        trading_signal: Dict[str, Any],
        order_type: OrderType
    ) -> Tuple[float, float]:
        """Calculate stop loss and take profit levels"""
        try:
            current_price = trading_signal['current_price']
            signal_strength = trading_signal.get('signal_strength', 0.5)
            predicted_price = trading_signal.get('predicted_price', current_price)
            
            # Calculate pip size
            if symbol.endswith('JPY'):
                pip_size = 0.01
            else:
                pip_size = 0.0001
            
            # Dynamic stop loss based on signal strength
            base_stop_pips = 30
            stop_pips = int(base_stop_pips * (1.5 - signal_strength))  # 15-45 pips range
            stop_distance = stop_pips * pip_size
            
            # Take profit based on predicted price movement
            predicted_move = abs(predicted_price - current_price)
            min_tp_distance = 2 * stop_distance  # Minimum 2:1 reward-to-risk
            tp_distance = max(min_tp_distance, predicted_move * 0.8)  # 80% of predicted move
            
            # Calculate levels based on order type
            if order_type == OrderType.BUY:
                stop_loss = current_price - stop_distance
                take_profit = current_price + tp_distance
            else:  # SELL
                stop_loss = current_price + stop_distance
                take_profit = current_price - tp_distance
            
            # Round to 5 decimal places (standard for forex)
            stop_loss = round(stop_loss, 5)
            take_profit = round(take_profit, 5)
            
            self.logger.info(f"📊 SL/TP calculated for {symbol}: SL={stop_loss:.5f}, TP={take_profit:.5f} "
                           f"(Stop: {stop_pips} pips, TP: {int(tp_distance/pip_size)} pips)")
            
            return stop_loss, take_profit
            
        except Exception as e:
            self.logger.error(f"❌ SL/TP calculation failed: {e}")
            # Fallback values
            if order_type == OrderType.BUY:
                return current_price * 0.995, current_price * 1.01  # 0.5% SL, 1% TP
            else:
                return current_price * 1.005, current_price * 0.99   # 0.5% SL, 1% TP
    
    async def _execute_order_via_bridge(self, order: TradingOrder) -> TradingResult:
        """Execute trading order via MT5-Bridge microservice"""
        start_time = time.time()
        
        try:
            # Execute order through MT5-Bridge HTTP API
            result = await self.mt5_client.execute_market_order(
                symbol=order.symbol,
                order_type=order.order_type,
                volume=order.volume,
                sl=order.stop_loss,
                tp=order.take_profit,
                comment=order.comment
            )
            
            execution_time = time.time() - start_time
            
            if result.get("success"):
                self.logger.info(f"✅ Order executed via MT5-Bridge: {order.symbol} {order.order_type.value} "
                               f"{order.volume} lots at {result.get('execution_price', 'N/A')} "
                               f"(Ticket: {result.get('order_ticket', 'N/A')})")
                
                return TradingResult(
                    success=True,
                    order_ticket=result.get('order_ticket'),
                    execution_price=result.get('execution_price'),
                    slippage=0.0,  # Would need to calculate from original vs execution price
                    execution_time=execution_time,
                    ai_validation_passed=True,
                    risk_validation_passed=True,
                    pattern_confirmation=order.pattern_confidence > 0.6,
                    timestamp=datetime.now(),
                    execution_id=f"TE_{int(time.time())}"
                )
            else:
                return TradingResult(
                    success=False,
                    order_ticket=None,
                    execution_price=None,
                    slippage=0,
                    execution_time=execution_time,
                    ai_validation_passed=True,
                    risk_validation_passed=True,
                    pattern_confirmation=order.pattern_confidence > 0.6,
                    error_description=result.get('error', 'Unknown execution error'),
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"❌ Order execution via MT5-Bridge failed: {e}")
            return TradingResult(
                success=False,
                order_ticket=None,
                execution_price=None,
                slippage=0,
                execution_time=execution_time,
                ai_validation_passed=True,
                risk_validation_passed=True,
                pattern_confirmation=False,
                error_description=str(e),
                timestamp=datetime.now()
            )
    
    async def _update_risk_metrics(self):
        """Update risk metrics from account info"""
        try:
            account_info = await self.mt5_client.get_account_info()
            if account_info:
                self.account_info = account_info
                
                # Update risk metrics
                balance = account_info.get('balance', 10000.0)
                equity = account_info.get('equity', 10000.0)
                margin = account_info.get('margin', 0.0)
                free_margin = account_info.get('free_margin', balance)
                
                # Calculate margin level
                if margin > 0:
                    margin_level = (equity / margin) * 100
                else:
                    margin_level = 1000.0  # No positions open
                
                # Calculate drawdown
                max_drawdown = max(0, (balance - equity) / balance) if balance > 0 else 0
                
                self.risk_metrics.update({
                    "margin_level": margin_level,
                    "max_drawdown": max_drawdown,
                    # position_count and daily_risk_used would be tracked separately
                })
                
        except Exception as e:
            self.logger.error(f"❌ Failed to update risk metrics: {e}")
    
    async def _store_trade_for_learning(self, order: TradingOrder, result: TradingResult, prediction: Dict[str, Any]):
        """Store trade data for machine learning (future implementation)"""
        try:
            trade_data = {
                "timestamp": datetime.now().isoformat(),
                "symbol": order.symbol,
                "order_type": order.order_type.value,
                "volume": order.volume,
                "ai_confidence": order.ai_confidence,
                "pattern_confidence": order.pattern_confidence,
                "prediction_source": order.prediction_source,
                "execution_success": result.success,
                "execution_price": result.execution_price,
                "prediction": prediction
            }
            
            # Store in cache for now - in production, would store in database
            await cache.set(f"trade_history_{result.execution_id}", trade_data, ttl=86400)
            
            self.logger.info(f"📊 Trade stored for learning: {result.execution_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to store trade for learning: {e}")
    
    async def get_risk_metrics(self) -> Dict[str, Any]:
        """Get current risk metrics"""
        await self._update_risk_metrics()
        return {
            "risk_metrics": self.risk_metrics,
            "account_info": self.account_info,
            "config": asdict(self.config),
            "timestamp": datetime.now().isoformat()
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.mt5_client.close()


# Export main classes for the Trading-Engine service
__all__ = [
    "AiTradingEngine",
    "AiTradingConfig", 
    "TradingOrder",
    "TradingResult",
    "TradingSignal",
    "OrderType",
    "MT5BridgeClient"
]