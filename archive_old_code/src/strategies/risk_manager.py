"""
Risk Management System with Kelly Criterion and ML Position Sizing
Advanced risk management with dynamic position sizing and portfolio protection.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import warnings
warnings.filterwarnings('ignore')

from .strategy_engine import TradingSignal, MarketData

logger = logging.getLogger(__name__)

@dataclass
class PositionSize:
    """Position sizing information"""
    size: float
    risk_amount: float
    kelly_fraction: float
    ml_adjustment: float
    confidence_multiplier: float
    max_position_limit: float

@dataclass
class RiskMetrics:
    """Risk assessment metrics"""
    portfolio_value: float
    used_margin: float
    available_margin: float
    portfolio_var: float  # Value at Risk
    portfolio_volatility: float
    sharpe_ratio: float
    max_drawdown: float
    current_drawdown: float

class KellyCriterionCalculator:
    """Kelly Criterion calculator for optimal position sizing"""

    def __init__(self, lookback_period: int = 100):
        self.lookback_period = lookback_period
        self.historical_returns = []
        self.win_rate = 0.0
        self.avg_win = 0.0
        self.avg_loss = 0.0

    def update_history(self, trade_return: float):
        """Update historical returns for Kelly calculation"""
        self.historical_returns.append(trade_return)
        if len(self.historical_returns) > self.lookback_period:
            self.historical_returns.pop(0)

        if len(self.historical_returns) >= 10:  # Minimum sample size
            self._calculate_kelly_parameters()

    def _calculate_kelly_parameters(self):
        """Calculate win rate and average win/loss"""
        returns = np.array(self.historical_returns)
        wins = returns[returns > 0]
        losses = returns[returns < 0]

        self.win_rate = len(wins) / len(returns) if len(returns) > 0 else 0.0
        self.avg_win = np.mean(wins) if len(wins) > 0 else 0.0
        self.avg_loss = abs(np.mean(losses)) if len(losses) > 0 else 0.01  # Avoid division by zero

    def calculate_kelly_fraction(self, expected_return: float = None) -> float:
        """
        Calculate Kelly fraction: f = (bp - q) / b
        where:
        - b = average win / average loss ratio
        - p = probability of winning
        - q = probability of losing (1 - p)
        """
        if len(self.historical_returns) < 10:
            return 0.01  # Conservative default

        if expected_return is not None:
            # Use provided expected return
            win_loss_ratio = abs(expected_return) / self.avg_loss if self.avg_loss > 0 else 1.0
        else:
            # Use historical win/loss ratio
            win_loss_ratio = self.avg_win / self.avg_loss if self.avg_loss > 0 else 1.0

        kelly_fraction = (win_loss_ratio * self.win_rate - (1 - self.win_rate)) / win_loss_ratio

        # Apply safety constraints
        kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25%

        return kelly_fraction

class MLPositionSizer:
    """Machine Learning-based position sizing"""

    def __init__(self):
        self.feature_history = []
        self.return_history = []
        self.model = None
        self.is_trained = False
        self.min_samples = 50

    def add_training_data(self, features: Dict[str, float], actual_return: float):
        """Add training data for ML model"""
        feature_vector = [
            features.get('confidence', 0.0),
            features.get('volatility', 0.0),
            features.get('volume_ratio', 1.0),
            features.get('rsi', 50.0),
            features.get('atr_normalized', 0.0),
            features.get('market_regime_score', 0.0),
            features.get('correlation_score', 0.0)
        ]

        self.feature_history.append(feature_vector)
        self.return_history.append(actual_return)

        # Keep only recent samples
        if len(self.feature_history) > 200:
            self.feature_history.pop(0)
            self.return_history.pop(0)

        # Retrain model periodically
        if len(self.feature_history) >= self.min_samples and len(self.feature_history) % 20 == 0:
            self._train_model()

    def _train_model(self):
        """Train ML model for position sizing"""
        try:
            X = np.array(self.feature_history)
            y = np.array(self.return_history)

            # Use Random Forest for robustness
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            self.model.fit(X, y)
            self.is_trained = True

            logger.info(f"ML position sizing model retrained with {len(X)} samples")

        except Exception as e:
            logger.error(f"Error training ML position sizing model: {e}")
            self.is_trained = False

    def predict_adjustment(self, features: Dict[str, float]) -> float:
        """Predict position size adjustment factor"""
        if not self.is_trained or self.model is None:
            return 1.0  # No adjustment

        try:
            feature_vector = np.array([[
                features.get('confidence', 0.0),
                features.get('volatility', 0.0),
                features.get('volume_ratio', 1.0),
                features.get('rsi', 50.0),
                features.get('atr_normalized', 0.0),
                features.get('market_regime_score', 0.0),
                features.get('correlation_score', 0.0)
            ]])

            predicted_return = self.model.predict(feature_vector)[0]

            # Convert predicted return to position adjustment
            # Higher predicted returns -> larger position (up to 2x)
            # Lower predicted returns -> smaller position (down to 0.5x)
            adjustment = 1.0 + np.tanh(predicted_return * 5) * 0.5
            adjustment = max(0.5, min(adjustment, 2.0))

            return adjustment

        except Exception as e:
            logger.error(f"Error predicting position adjustment: {e}")
            return 1.0

class RiskManager:
    """Comprehensive risk management system"""

    def __init__(self, config: Dict[str, Any]):
        self.config = {
            'max_portfolio_risk': 0.02,  # 2% max portfolio risk per trade
            'max_position_size': 0.10,   # 10% max position size
            'max_drawdown_limit': 0.20,  # 20% max drawdown
            'var_confidence': 0.05,      # 95% VaR confidence
            'volatility_lookback': 30,   # Days for volatility calculation
            'correlation_threshold': 0.7, # Position correlation limit
            **config
        }

        self.kelly_calculator = KellyCriterionCalculator()
        self.ml_sizer = MLPositionSizer()
        self.portfolio_history = []
        self.position_history = []
        self.current_positions = {}

    def calculate_position_size(self, signal: TradingSignal, market_data: MarketData,
                              portfolio_value: float, risk_metrics: RiskMetrics) -> PositionSize:
        """Calculate optimal position size using multiple methods"""

        # 1. Kelly Criterion sizing
        kelly_fraction = self.kelly_calculator.calculate_kelly_fraction()

        # 2. Volatility-adjusted sizing
        volatility = self._calculate_volatility(market_data)
        vol_adjustment = 1.0 / (1.0 + volatility * 10)  # Reduce size in high volatility

        # 3. Confidence-based sizing
        confidence_multiplier = signal.confidence

        # 4. ML-based adjustment
        ml_features = self._extract_ml_features(signal, market_data, risk_metrics)
        ml_adjustment = self.ml_sizer.predict_adjustment(ml_features)

        # 5. Risk-based sizing (maximum risk per trade)
        if signal.stop_loss is not None:
            risk_per_share = abs(signal.price - signal.stop_loss)
            max_shares_by_risk = (portfolio_value * self.config['max_portfolio_risk']) / risk_per_share
            risk_based_size = max_shares_by_risk / portfolio_value  # As fraction of portfolio
        else:
            # Use ATR-based risk estimate
            atr = np.std(market_data.close[-14:])  # 14-period volatility
            estimated_risk = 2 * atr  # 2 ATR stop loss
            max_shares_by_risk = (portfolio_value * self.config['max_portfolio_risk']) / estimated_risk
            risk_based_size = max_shares_by_risk / portfolio_value

        # Combine all sizing methods
        base_size = min(
            kelly_fraction * 0.5,  # Conservative Kelly
            risk_based_size,
            self.config['max_position_size']
        )

        # Apply adjustments
        final_size = base_size * vol_adjustment * confidence_multiplier * ml_adjustment

        # Final safety checks
        final_size = max(0.001, min(final_size, self.config['max_position_size']))

        # Check portfolio constraints
        if not self._check_portfolio_constraints(final_size, risk_metrics):
            final_size *= 0.5  # Reduce position size

        risk_amount = final_size * portfolio_value * (risk_per_share / signal.price if signal.stop_loss else 0.02)

        return PositionSize(
            size=final_size,
            risk_amount=risk_amount,
            kelly_fraction=kelly_fraction,
            ml_adjustment=ml_adjustment,
            confidence_multiplier=confidence_multiplier,
            max_position_limit=self.config['max_position_size']
        )

    def _calculate_volatility(self, market_data: MarketData) -> float:
        """Calculate historical volatility"""
        if len(market_data.close) < self.config['volatility_lookback']:
            return 0.02  # Default volatility

        returns = np.diff(np.log(market_data.close[-self.config['volatility_lookback']:]))
        volatility = np.std(returns) * np.sqrt(252)  # Annualized volatility
        return volatility

    def _extract_ml_features(self, signal: TradingSignal, market_data: MarketData,
                           risk_metrics: RiskMetrics) -> Dict[str, float]:
        """Extract features for ML position sizing"""
        volatility = self._calculate_volatility(market_data)

        # Normalize ATR
        atr = np.std(market_data.close[-14:])
        atr_normalized = atr / signal.price

        # Volume analysis
        volume_ma = np.mean(market_data.volume[-20:])
        volume_ratio = market_data.volume[-1] / volume_ma

        # Market regime score (simplified)
        returns = np.diff(np.log(market_data.close[-30:]))
        trend_strength = abs(np.mean(returns)) / np.std(returns) if np.std(returns) > 0 else 0
        market_regime_score = min(trend_strength, 2.0) / 2.0

        return {
            'confidence': signal.confidence,
            'volatility': volatility,
            'volume_ratio': volume_ratio,
            'rsi': signal.metadata.get('rsi', 50.0),
            'atr_normalized': atr_normalized,
            'market_regime_score': market_regime_score,
            'correlation_score': 0.0  # Placeholder for portfolio correlation
        }

    def _check_portfolio_constraints(self, position_size: float, risk_metrics: RiskMetrics) -> bool:
        """Check if position meets portfolio constraints"""

        # Check maximum drawdown
        if risk_metrics.current_drawdown > self.config['max_drawdown_limit']:
            return False

        # Check available margin
        if risk_metrics.used_margin / risk_metrics.portfolio_value > 0.8:  # 80% margin utilization
            return False

        # Check VaR limits
        if risk_metrics.portfolio_var > risk_metrics.portfolio_value * 0.05:  # 5% daily VaR limit
            return False

        return True

    def calculate_portfolio_metrics(self, positions: Dict[str, Dict], market_data_dict: Dict[str, MarketData]) -> RiskMetrics:
        """Calculate current portfolio risk metrics"""

        portfolio_value = sum(pos['value'] for pos in positions.values())
        used_margin = sum(pos.get('margin', 0) for pos in positions.values())

        # Calculate portfolio volatility
        portfolio_returns = []
        if len(self.portfolio_history) > 1:
            portfolio_returns = [
                (self.portfolio_history[i] - self.portfolio_history[i-1]) / self.portfolio_history[i-1]
                for i in range(1, len(self.portfolio_history))
            ]

        portfolio_volatility = np.std(portfolio_returns) if len(portfolio_returns) > 10 else 0.02

        # Calculate VaR (95% confidence)
        if len(portfolio_returns) > 30:
            portfolio_var = abs(np.percentile(portfolio_returns, 5) * portfolio_value)
        else:
            portfolio_var = portfolio_value * 0.02  # Default 2% VaR

        # Calculate Sharpe ratio
        if len(portfolio_returns) > 30:
            avg_return = np.mean(portfolio_returns)
            sharpe_ratio = avg_return / portfolio_volatility if portfolio_volatility > 0 else 0
        else:
            sharpe_ratio = 0.0

        # Calculate drawdown
        if len(self.portfolio_history) > 0:
            peak = max(self.portfolio_history)
            current_drawdown = (peak - portfolio_value) / peak if peak > 0 else 0
            max_drawdown = max([
                (peak - val) / peak for peak, val in
                zip(np.maximum.accumulate(self.portfolio_history), self.portfolio_history)
            ]) if len(self.portfolio_history) > 1 else 0
        else:
            current_drawdown = max_drawdown = 0.0

        return RiskMetrics(
            portfolio_value=portfolio_value,
            used_margin=used_margin,
            available_margin=portfolio_value - used_margin,
            portfolio_var=portfolio_var,
            portfolio_volatility=portfolio_volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            current_drawdown=current_drawdown
        )

    def update_position_performance(self, signal: TradingSignal, actual_return: float):
        """Update performance tracking for position sizing optimization"""
        # Update Kelly calculator
        self.kelly_calculator.update_history(actual_return)

        # Update ML model with features and performance
        market_features = {
            'confidence': signal.confidence,
            'volatility': 0.02,  # Would be calculated from market data
            'volume_ratio': 1.0,
            'rsi': signal.metadata.get('rsi', 50.0),
            'atr_normalized': 0.01,
            'market_regime_score': 0.5,
            'correlation_score': 0.0
        }
        self.ml_sizer.add_training_data(market_features, actual_return)

    def should_exit_position(self, position: Dict, current_price: float, risk_metrics: RiskMetrics) -> bool:
        """Determine if a position should be exited based on risk management rules"""

        # Check stop loss
        if 'stop_loss' in position and position['stop_loss'] is not None:
            if position['side'] == 'long' and current_price <= position['stop_loss']:
                return True
            elif position['side'] == 'short' and current_price >= position['stop_loss']:
                return True

        # Check take profit
        if 'take_profit' in position and position['take_profit'] is not None:
            if position['side'] == 'long' and current_price >= position['take_profit']:
                return True
            elif position['side'] == 'short' and current_price <= position['take_profit']:
                return True

        # Check maximum drawdown
        if risk_metrics.current_drawdown > self.config['max_drawdown_limit']:
            return True

        # Check position age (time-based exit)
        position_age = time.time() - position.get('entry_time', time.time())
        if position_age > 86400 * 7:  # 7 days maximum hold
            return True

        return False

    def get_risk_summary(self) -> Dict[str, Any]:
        """Get comprehensive risk summary"""
        return {
            'kelly_win_rate': self.kelly_calculator.win_rate,
            'kelly_avg_win': self.kelly_calculator.avg_win,
            'kelly_avg_loss': self.kelly_calculator.avg_loss,
            'ml_model_trained': self.ml_sizer.is_trained,
            'ml_samples': len(self.ml_sizer.feature_history),
            'config': self.config
        }