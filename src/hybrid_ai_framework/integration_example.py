"""
Hybrid AI Trading Framework - Integration Example
Demonstrates complete integration with existing trading-engine service

This example shows how to:
1. Integrate with existing TradingIndicatorManager (40+ indicators)
2. Combine traditional indicators with AI predictions
3. Use forex/gold specific analysis
4. Implement real-time decision making
5. Manage risk and performance tracking
"""

import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Import existing trading engine components
# from ai_trading.server_microservice.services.trading_engine.src.business.ai_trading_engine import AiTradingEngine
# from ai_trading.server_microservice.services.trading_engine.src.technical_analysis.indicator_manager import TradingIndicatorManager

# Import new hybrid AI framework components
from .core.hybrid_ai_engine import HybridAITradingEngine, HybridAIConfig, TradingAsset
from .core.market_regime_detector import MarketRegimeDetector
from .core.correlation_engine import MultiAssetCorrelationEngine
from .core.sentiment_analyzer import FinBERTSentimentAnalyzer
from .core.session_analyzer import ForexSessionAnalyzer
from .core.automl_optimizer import AutoMLOptimizer


class HybridTradingSystem:
    """
    Complete hybrid trading system integrating existing indicators with AI framework

    This system demonstrates:
    - Integration with existing 40+ indicator system
    - Real-time AI-enhanced decision making
    - Multi-asset correlation analysis
    - Sentiment-driven adjustments
    - Session-based optimization
    - Continuous learning and adaptation
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Initialize hybrid AI engine
        self.ai_config = HybridAIConfig(
            primary_asset=TradingAsset.XAUUSD,  # Gold trading focus
            correlation_assets=[TradingAsset.DXY, TradingAsset.EURUSD, TradingAsset.GBPUSD],
            enable_finbert=True,
            enable_ensemble=True,
            enable_automl=True,
            sentiment_weight=0.2,
            confidence_threshold=0.75
        )

        self.hybrid_ai_engine = HybridAITradingEngine(self.ai_config)

        # Initialize traditional components (would integrate with existing system)
        # self.indicator_manager = TradingIndicatorManager()
        # self.traditional_ai_engine = AiTradingEngine()

        # Performance tracking
        self.trade_history: List[Dict] = []
        self.performance_metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0,
            'hybrid_ai_contribution': 0.0
        }

        self.logger.info("Hybrid Trading System initialized")

    async def initialize(self) -> bool:
        """Initialize all system components"""
        try:
            self.logger.info("Initializing Hybrid Trading System...")

            # Initialize hybrid AI engine
            ai_success = await self.hybrid_ai_engine.initialize()
            if not ai_success:
                self.logger.error("Failed to initialize Hybrid AI Engine")
                return False

            # Initialize traditional components (integration with existing system)
            # indicator_success = await self.indicator_manager.initialize()
            # traditional_ai_success = await self.traditional_ai_engine.initialize()

            self.logger.info("✅ Hybrid Trading System fully initialized")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Hybrid Trading System: {e}")
            return False

    async def generate_trading_decision(self, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate comprehensive trading decision using hybrid approach

        This method demonstrates the complete integration:
        1. Traditional indicator analysis (existing system)
        2. AI-enhanced market analysis (new framework)
        3. Decision fusion and risk management
        4. Performance tracking and learning

        Args:
            market_data: Real-time market data

        Returns:
            Comprehensive trading decision or None if no action recommended
        """
        try:
            self.logger.info(f"Generating trading decision for {market_data.get('symbol', 'Unknown')}")

            # Step 1: Traditional Indicator Analysis (existing system integration)
            traditional_analysis = await self._get_traditional_analysis(market_data)

            # Step 2: Hybrid AI Analysis (new framework)
            ai_analysis = await self._get_ai_analysis(market_data)

            # Step 3: Decision Fusion
            trading_decision = await self._fuse_analyses(traditional_analysis, ai_analysis, market_data)

            # Step 4: Risk Validation
            if trading_decision:
                risk_validated = await self._validate_risk(trading_decision, market_data)
                if not risk_validated:
                    self.logger.warning("Trading decision rejected by risk validation")
                    return None

            # Step 5: Log decision for learning
            if trading_decision:
                await self._log_decision_for_learning(trading_decision, traditional_analysis, ai_analysis)

            return trading_decision

        except Exception as e:
            self.logger.error(f"❌ Trading decision generation failed: {e}")
            return None

    async def _get_traditional_analysis(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get analysis from traditional indicator system (integration point)

        In production, this would call the existing TradingIndicatorManager
        and AiTradingEngine to get traditional analysis
        """
        try:
            # Simulated traditional analysis (in production, this would call existing system)
            # traditional_features = await self.indicator_manager.process_market_data(market_data)
            # ai_prediction = await self.traditional_ai_engine.generate_prediction(traditional_features)

            # Simulated results for demonstration
            traditional_analysis = {
                'technical_score': 0.65,  # From 40+ indicators
                'momentum_signal': 'bullish',
                'volume_confirmation': True,
                'trend_strength': 0.7,
                'volatility_level': 0.4,
                'support_resistance': {
                    'support': market_data.get('close', 1800) * 0.995,
                    'resistance': market_data.get('close', 1800) * 1.005
                },
                'traditional_ai_confidence': 0.68,
                'recommended_action': 'buy',
                'position_size': 0.02,
                'stop_loss': market_data.get('close', 1800) * 0.99,
                'take_profit': market_data.get('close', 1800) * 1.02
            }

            self.logger.debug("Traditional analysis completed")
            return traditional_analysis

        except Exception as e:
            self.logger.error(f"❌ Traditional analysis failed: {e}")
            return {
                'technical_score': 0.5,
                'momentum_signal': 'neutral',
                'volume_confirmation': False,
                'traditional_ai_confidence': 0.3,
                'recommended_action': 'hold'
            }

    async def _get_ai_analysis(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get analysis from hybrid AI framework"""
        try:
            # Get comprehensive AI analysis
            ai_signal = await self.hybrid_ai_engine.generate_trading_signal(market_data)

            if ai_signal:
                ai_analysis = {
                    'ai_signal_type': ai_signal.signal_type,
                    'ai_confidence': ai_signal.confidence,
                    'ai_strength': ai_signal.strength,
                    'sentiment_impact': ai_signal.sentiment_impact,
                    'regime_alignment': ai_signal.regime_alignment,
                    'correlation_risk': ai_signal.correlation_risk,
                    'session_favorability': ai_signal.session_favorability,
                    'market_regime': ai_signal.market_insight.regime_prediction,
                    'price_prediction': ai_signal.market_insight.price_prediction,
                    'risk_factors': ai_signal.market_insight.risk_factors,
                    'opportunities': ai_signal.market_insight.opportunities,
                    'ai_entry_price': ai_signal.entry_price,
                    'ai_stop_loss': ai_signal.stop_loss,
                    'ai_take_profit': ai_signal.take_profit,
                    'ai_position_size': ai_signal.position_size
                }
            else:
                ai_analysis = {
                    'ai_signal_type': 'hold',
                    'ai_confidence': 0.3,
                    'ai_strength': 0.0,
                    'market_regime': 'uncertain'
                }

            self.logger.debug("AI analysis completed")
            return ai_analysis

        except Exception as e:
            self.logger.error(f"❌ AI analysis failed: {e}")
            return {
                'ai_signal_type': 'hold',
                'ai_confidence': 0.3,
                'ai_strength': 0.0,
                'market_regime': 'uncertain'
            }

    async def _fuse_analyses(self, traditional: Dict[str, Any], ai: Dict[str, Any],
                           market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Fuse traditional and AI analyses into unified trading decision

        This is the core of the hybrid approach - combining proven traditional
        indicators with advanced AI insights
        """
        try:
            # Extract key components
            traditional_action = traditional.get('recommended_action', 'hold')
            traditional_confidence = traditional.get('traditional_ai_confidence', 0.5)
            traditional_score = traditional.get('technical_score', 0.5)

            ai_action = ai.get('ai_signal_type', 'hold')
            ai_confidence = ai.get('ai_confidence', 0.5)
            ai_strength = ai.get('ai_strength', 0.5)

            # Decision fusion logic
            fusion_result = await self._calculate_fusion_decision(
                traditional_action, traditional_confidence, traditional_score,
                ai_action, ai_confidence, ai_strength
            )

            if fusion_result['action'] == 'hold':
                return None

            # Calculate position parameters using both analyses
            position_params = await self._calculate_fusion_position_params(
                traditional, ai, market_data, fusion_result
            )

            # Create comprehensive trading decision
            trading_decision = {
                'symbol': market_data.get('symbol', 'XAUUSD'),
                'action': fusion_result['action'],
                'confidence': fusion_result['confidence'],
                'strength': fusion_result['strength'],

                # Position parameters
                'entry_price': position_params['entry_price'],
                'stop_loss': position_params['stop_loss'],
                'take_profit': position_params['take_profit'],
                'position_size': position_params['position_size'],

                # Analysis breakdown
                'traditional_contribution': fusion_result['traditional_weight'],
                'ai_contribution': fusion_result['ai_weight'],
                'traditional_analysis': traditional,
                'ai_analysis': ai,

                # Risk and timing
                'risk_level': position_params['risk_level'],
                'holding_period': position_params['holding_period'],
                'market_timing': ai.get('session_favorability', 0.5),

                # Decision rationale
                'rationale': await self._generate_decision_rationale(
                    traditional, ai, fusion_result
                ),

                'timestamp': datetime.now().isoformat()
            }

            self.logger.info(f"Fusion decision: {fusion_result['action']} with {fusion_result['confidence']:.2f} confidence")
            return trading_decision

        except Exception as e:
            self.logger.error(f"❌ Analysis fusion failed: {e}")
            return None

    async def _calculate_fusion_decision(self, trad_action: str, trad_conf: float, trad_score: float,
                                       ai_action: str, ai_conf: float, ai_strength: float) -> Dict[str, Any]:
        """Calculate fused decision from traditional and AI analyses"""
        try:
            # Weight calculation based on confidence levels
            traditional_weight = trad_conf * 0.6  # 60% weight to traditional (proven system)
            ai_weight = ai_conf * 0.4  # 40% weight to AI (enhancement)

            # Normalize weights
            total_weight = traditional_weight + ai_weight
            if total_weight > 0:
                traditional_weight /= total_weight
                ai_weight /= total_weight

            # Agreement check
            actions_agree = (
                (trad_action in ['buy', 'strong_buy'] and ai_action in ['buy', 'strong_buy']) or
                (trad_action in ['sell', 'strong_sell'] and ai_action in ['sell', 'strong_sell']) or
                (trad_action == 'hold' and ai_action == 'hold')
            )

            # Decision logic
            if actions_agree:
                # Both systems agree - higher confidence
                final_action = trad_action if trad_action != 'hold' else ai_action
                confidence_boost = 1.2  # 20% boost for agreement
                final_confidence = min((trad_conf * traditional_weight + ai_conf * ai_weight) * confidence_boost, 1.0)
            else:
                # Systems disagree - use weighted decision with penalty
                if traditional_weight > ai_weight:
                    final_action = trad_action
                    final_confidence = trad_conf * 0.8  # 20% penalty for disagreement
                else:
                    final_action = ai_action
                    final_confidence = ai_conf * 0.8

                # If confidence too low due to disagreement, default to hold
                if final_confidence < 0.6:
                    final_action = 'hold'
                    final_confidence = 0.5

            # Calculate final strength
            final_strength = (trad_score * traditional_weight + ai_strength * ai_weight)

            return {
                'action': final_action,
                'confidence': final_confidence,
                'strength': final_strength,
                'traditional_weight': traditional_weight,
                'ai_weight': ai_weight,
                'agreement': actions_agree
            }

        except Exception as e:
            self.logger.error(f"❌ Fusion decision calculation failed: {e}")
            return {
                'action': 'hold',
                'confidence': 0.3,
                'strength': 0.0,
                'traditional_weight': 0.6,
                'ai_weight': 0.4,
                'agreement': False
            }

    async def _calculate_fusion_position_params(self, traditional: Dict, ai: Dict,
                                              market_data: Dict, fusion_result: Dict) -> Dict[str, Any]:
        """Calculate position parameters using both analyses"""
        try:
            current_price = market_data.get('close', 1800)

            # Weighted average of position parameters
            trad_weight = fusion_result['traditional_weight']
            ai_weight = fusion_result['ai_weight']

            # Position size (risk-adjusted)
            trad_size = traditional.get('position_size', 0.02)
            ai_size = ai.get('ai_position_size', 0.02)
            base_position_size = trad_size * trad_weight + ai_size * ai_weight

            # Adjust position size based on confidence and agreement
            confidence_multiplier = fusion_result['confidence']
            agreement_multiplier = 1.1 if fusion_result['agreement'] else 0.9

            final_position_size = base_position_size * confidence_multiplier * agreement_multiplier
            final_position_size = min(max(final_position_size, 0.005), 0.05)  # 0.5% to 5% range

            # Stop loss (more conservative approach)
            trad_sl = traditional.get('stop_loss', current_price * 0.99)
            ai_sl = ai.get('ai_stop_loss', current_price * 0.99)

            if fusion_result['action'] in ['buy', 'strong_buy']:
                # For buy orders, use the higher (more conservative) stop loss
                final_stop_loss = max(trad_sl, ai_sl)
            else:
                # For sell orders, use the lower (more conservative) stop loss
                final_stop_loss = min(trad_sl, ai_sl)

            # Take profit (blend both approaches)
            trad_tp = traditional.get('take_profit', current_price * 1.02)
            ai_tp = ai.get('ai_take_profit', current_price * 1.02)
            final_take_profit = trad_tp * trad_weight + ai_tp * ai_weight

            # Entry price (current market price with minor adjustment)
            final_entry_price = current_price

            # Risk level assessment
            correlation_risk = ai.get('correlation_risk', 0.5)
            volatility = traditional.get('volatility_level', 0.5)

            if correlation_risk > 0.7 or volatility > 0.8:
                risk_level = 'high'
                holding_period = 'short'
            elif correlation_risk > 0.4 or volatility > 0.6:
                risk_level = 'medium'
                holding_period = 'medium'
            else:
                risk_level = 'low'
                holding_period = 'long'

            return {
                'entry_price': final_entry_price,
                'stop_loss': final_stop_loss,
                'take_profit': final_take_profit,
                'position_size': final_position_size,
                'risk_level': risk_level,
                'holding_period': holding_period
            }

        except Exception as e:
            self.logger.error(f"❌ Position parameter calculation failed: {e}")
            current_price = market_data.get('close', 1800)
            return {
                'entry_price': current_price,
                'stop_loss': current_price * 0.99,
                'take_profit': current_price * 1.02,
                'position_size': 0.01,
                'risk_level': 'medium',
                'holding_period': 'short'
            }

    async def _validate_risk(self, trading_decision: Dict[str, Any], market_data: Dict[str, Any]) -> bool:
        """Validate trading decision against risk parameters"""
        try:
            # Check confidence threshold
            if trading_decision['confidence'] < self.ai_config.confidence_threshold:
                self.logger.warning(f"Decision confidence {trading_decision['confidence']:.2f} below threshold")
                return False

            # Check position size limits
            position_size = trading_decision['position_size']
            if position_size > 0.05 or position_size < 0.005:
                self.logger.warning(f"Position size {position_size:.3f} outside acceptable range")
                return False

            # Check correlation risk
            if 'ai_analysis' in trading_decision:
                correlation_risk = trading_decision['ai_analysis'].get('correlation_risk', 0.5)
                if correlation_risk > self.ai_config.max_correlation_exposure:
                    self.logger.warning(f"Correlation risk {correlation_risk:.2f} too high")
                    return False

            # Check for recent conflicting trades
            recent_trades = [t for t in self.trade_history[-5:] if
                           (datetime.now() - datetime.fromisoformat(t['timestamp'])).total_seconds() < 3600]

            for trade in recent_trades:
                if (trade['symbol'] == trading_decision['symbol'] and
                    trade['action'] != trading_decision['action']):
                    self.logger.warning("Conflicting signal within last hour")
                    return False

            return True

        except Exception as e:
            self.logger.error(f"❌ Risk validation failed: {e}")
            return False

    async def _generate_decision_rationale(self, traditional: Dict, ai: Dict, fusion_result: Dict) -> str:
        """Generate human-readable rationale for the trading decision"""
        try:
            rationale_parts = []

            # Overall decision
            action = fusion_result['action']
            confidence = fusion_result['confidence']
            rationale_parts.append(f"{action.upper()} signal with {confidence:.1%} confidence")

            # Agreement status
            if fusion_result['agreement']:
                rationale_parts.append("Traditional and AI analyses agree")
            else:
                rationale_parts.append("Mixed signals from traditional and AI analyses")

            # Traditional contribution
            trad_score = traditional.get('technical_score', 0.5)
            rationale_parts.append(f"Traditional indicators: {trad_score:.1%} bullishness")

            # AI contribution
            ai_regime = ai.get('market_regime', 'uncertain')
            ai_confidence = ai.get('ai_confidence', 0.5)
            rationale_parts.append(f"AI analysis: {ai_regime} regime, {ai_confidence:.1%} confidence")

            # Risk factors
            risk_factors = ai.get('risk_factors', [])
            if risk_factors:
                rationale_parts.append(f"Risk factors: {', '.join(risk_factors[:2])}")

            # Session timing
            session_favorability = ai.get('session_favorability', 0.5)
            if session_favorability > 0.7:
                rationale_parts.append("Favorable trading session")
            elif session_favorability < 0.4:
                rationale_parts.append("Suboptimal trading session")

            return "; ".join(rationale_parts)

        except Exception as e:
            self.logger.error(f"❌ Rationale generation failed: {e}")
            return f"Hybrid analysis recommends {fusion_result.get('action', 'hold')}"

    async def _log_decision_for_learning(self, decision: Dict, traditional: Dict, ai: Dict) -> None:
        """Log decision for machine learning and adaptation"""
        try:
            learning_record = {
                'timestamp': datetime.now().isoformat(),
                'decision': decision,
                'traditional_analysis': traditional,
                'ai_analysis': ai,
                'market_conditions': {
                    'regime': ai.get('market_regime', 'unknown'),
                    'volatility': traditional.get('volatility_level', 0.5),
                    'session_favorability': ai.get('session_favorability', 0.5)
                }
            }

            # Store for later analysis and model improvement
            # In production, this would be stored in database
            self.logger.debug("Decision logged for learning")

        except Exception as e:
            self.logger.error(f"❌ Decision logging failed: {e}")

    async def update_performance(self, decision: Dict[str, Any], trade_result: Dict[str, Any]) -> None:
        """Update system performance with trade results"""
        try:
            # Update basic metrics
            self.performance_metrics['total_trades'] += 1
            actual_pnl = trade_result.get('pnl', 0.0)
            self.performance_metrics['total_pnl'] += actual_pnl

            if actual_pnl > 0:
                self.performance_metrics['winning_trades'] += 1

            # Calculate hybrid AI contribution
            ai_weight = decision.get('ai_contribution', 0.4)
            traditional_weight = decision.get('traditional_contribution', 0.6)

            # Estimate how much AI contributed to the result
            ai_contribution_estimate = actual_pnl * ai_weight
            self.performance_metrics['hybrid_ai_contribution'] += ai_contribution_estimate

            # Update AI engine performance
            ai_signal_data = {
                'asset': decision['symbol'],
                'signal_type': decision['action'],
                'predicted_confidence': decision['confidence'],
                'actual_pnl': actual_pnl,
                'success': actual_pnl > 0,
                'timestamp': decision['timestamp']
            }

            await self.hybrid_ai_engine.update_performance(decision, trade_result)

            # Log performance
            win_rate = self.performance_metrics['winning_trades'] / self.performance_metrics['total_trades']
            self.logger.info(f"Performance updated: {win_rate:.1%} win rate, ${self.performance_metrics['total_pnl']:.2f} total PnL")

        except Exception as e:
            self.logger.error(f"❌ Performance update failed: {e}")

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            # Get AI engine status
            ai_status = await self.hybrid_ai_engine.get_system_status()

            # Calculate performance metrics
            total_trades = self.performance_metrics['total_trades']
            win_rate = (self.performance_metrics['winning_trades'] / total_trades) if total_trades > 0 else 0.0
            avg_pnl = (self.performance_metrics['total_pnl'] / total_trades) if total_trades > 0 else 0.0

            # AI contribution analysis
            ai_contribution_pct = 0.0
            if self.performance_metrics['total_pnl'] != 0:
                ai_contribution_pct = (self.performance_metrics['hybrid_ai_contribution'] /
                                     self.performance_metrics['total_pnl']) * 100

            system_status = {
                'system_health': 'healthy',
                'hybrid_integration': 'active',
                'ai_engine_status': ai_status.get('system_health', 'unknown'),

                'performance_metrics': {
                    'total_trades': total_trades,
                    'win_rate': win_rate,
                    'total_pnl': self.performance_metrics['total_pnl'],
                    'average_pnl_per_trade': avg_pnl,
                    'ai_contribution_percentage': ai_contribution_pct
                },

                'ai_framework_status': {
                    'models_active': ai_status.get('models_loaded', 0),
                    'last_analysis': ai_status.get('last_analysis'),
                    'primary_asset': self.ai_config.primary_asset.value,
                    'correlation_assets': [asset.value for asset in self.ai_config.correlation_assets]
                },

                'integration_health': {
                    'traditional_indicators': 'connected',  # Would check actual connection
                    'ai_sentiment_analysis': ai_status.get('configuration', {}).get('enable_finbert', False),
                    'session_analysis': ai_status.get('configuration', {}).get('enable_session_analysis', False),
                    'automl_optimization': ai_status.get('configuration', {}).get('enable_automl', False)
                },

                'recent_decisions': len([t for t in self.trade_history
                                       if (datetime.now() - datetime.fromisoformat(t['timestamp'])).days < 1]),

                'timestamp': datetime.now().isoformat()
            }

            return system_status

        except Exception as e:
            self.logger.error(f"❌ Failed to get system status: {e}")
            return {'system_health': 'error', 'error': str(e)}


# Example usage and testing
async def example_usage():
    """
    Example usage of the hybrid trading system
    """
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Initialize system
    hybrid_system = HybridTradingSystem()
    success = await hybrid_system.initialize()

    if not success:
        logger.error("Failed to initialize hybrid trading system")
        return

    # Simulate market data
    sample_market_data = {
        'symbol': 'XAUUSD',
        'timestamp': datetime.now().isoformat(),
        'open': 1850.25,
        'high': 1852.80,
        'low': 1848.90,
        'close': 1851.45,
        'volume': 125000,
        'close_prices': [1845 + i * 0.1 for i in range(100)],  # 100 periods of price data
        'volumes': [100000 + np.random.randint(-20000, 20000) for _ in range(100)],
        'high_prices': [1845 + i * 0.1 + 0.5 for i in range(100)],
        'low_prices': [1845 + i * 0.1 - 0.5 for i in range(100)],
        'news_data': [
            {
                'title': 'Federal Reserve hints at potential rate changes',
                'content': 'The Federal Reserve indicated possible monetary policy adjustments...',
                'source': 'Reuters',
                'timestamp': datetime.now().isoformat()
            }
        ]
    }

    # Generate trading decision
    logger.info("Generating trading decision...")
    decision = await hybrid_system.generate_trading_decision(sample_market_data)

    if decision:
        logger.info(f"Trading Decision Generated:")
        logger.info(f"  Action: {decision['action']}")
        logger.info(f"  Confidence: {decision['confidence']:.2f}")
        logger.info(f"  Entry Price: ${decision['entry_price']:.2f}")
        logger.info(f"  Stop Loss: ${decision['stop_loss']:.2f}")
        logger.info(f"  Take Profit: ${decision['take_profit']:.2f}")
        logger.info(f"  Position Size: {decision['position_size']:.3f}")
        logger.info(f"  Rationale: {decision['rationale']}")

        # Simulate trade execution and result
        simulated_result = {
            'pnl': np.random.normal(10, 50),  # Random P&L for demonstration
            'execution_price': decision['entry_price'],
            'execution_time': 0.05
        }

        # Update performance
        await hybrid_system.update_performance(decision, simulated_result)

        # Get system status
        status = await hybrid_system.get_system_status()
        logger.info(f"System Status: {status['system_health']}")
        logger.info(f"Win Rate: {status['performance_metrics']['win_rate']:.1%}")
        logger.info(f"AI Contribution: {status['performance_metrics']['ai_contribution_percentage']:.1f}%")

    else:
        logger.info("No trading action recommended")

    logger.info("Example completed successfully")


if __name__ == "__main__":
    asyncio.run(example_usage())


# Export main components
__all__ = [
    'HybridTradingSystem',
    'example_usage'
]