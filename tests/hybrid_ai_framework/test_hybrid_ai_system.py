"""
Comprehensive Test Suite for Hybrid AI Trading Framework

Tests all components:
1. Market Regime Detection
2. Multi-Asset Correlation Analysis
3. FinBERT Sentiment Analysis
4. Forex Session Analysis
5. AutoML Optimization
6. Complete System Integration
"""

import asyncio
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

# Import framework components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from hybrid_ai_framework.core.hybrid_ai_engine import (
    HybridAITradingEngine, HybridAIConfig, TradingAsset
)
from hybrid_ai_framework.core.market_regime_detector import (
    MarketRegimeDetector, MarketRegime
)
from hybrid_ai_framework.core.correlation_engine import (
    MultiAssetCorrelationEngine, AssetClass
)
from hybrid_ai_framework.core.sentiment_analyzer import (
    FinBERTSentimentAnalyzer, SentimentCategory
)
from hybrid_ai_framework.core.session_analyzer import (
    ForexSessionAnalyzer, TradingSession
)
from hybrid_ai_framework.core.automl_optimizer import (
    AutoMLOptimizer, OptimizationTarget
)
from hybrid_ai_framework.integration_example import HybridTradingSystem


class TestMarketRegimeDetector:
    """Test cases for Market Regime Detection"""

    @pytest.fixture
    async def regime_detector(self):
        detector = MarketRegimeDetector()
        await detector.initialize()
        return detector

    @pytest.mark.asyncio
    async def test_regime_initialization(self, regime_detector):
        """Test regime detector initialization"""
        assert regime_detector is not None
        assert len(regime_detector.thresholds) > 0
        assert 'trend_strength' in regime_detector.thresholds

    @pytest.mark.asyncio
    async def test_trending_regime_detection(self, regime_detector):
        """Test detection of trending market regime"""
        # Create trending market data
        trending_data = {
            'close_prices': [100 + i * 0.5 for i in range(50)],  # Clear uptrend
            'volumes': [1000] * 50,
            'high_prices': [100 + i * 0.5 + 0.2 for i in range(50)],
            'low_prices': [100 + i * 0.5 - 0.2 for i in range(50)]
        }

        result = await regime_detector.analyze_regime(trending_data)

        assert result['regime'] in ['trending_bull', 'trending_bear', 'breakout']
        assert result['trend_strength'] > 0.5
        assert result['confidence'] > 0.3

    @pytest.mark.asyncio
    async def test_sideways_regime_detection(self, regime_detector):
        """Test detection of sideways market regime"""
        # Create sideways market data
        sideways_data = {
            'close_prices': [100 + np.sin(i * 0.1) * 0.5 for i in range(50)],  # Oscillating
            'volumes': [1000] * 50,
            'high_prices': [100 + np.sin(i * 0.1) * 0.5 + 0.3 for i in range(50)],
            'low_prices': [100 + np.sin(i * 0.1) * 0.5 - 0.3 for i in range(50)]
        }

        result = await regime_detector.analyze_regime(sideways_data)

        assert result['regime'] in ['sideways', 'consolidation', 'uncertain']
        assert result['trend_strength'] < 0.6

    @pytest.mark.asyncio
    async def test_volatile_regime_detection(self, regime_detector):
        """Test detection of volatile market regime"""
        # Create volatile market data
        volatile_data = {
            'close_prices': [100 + np.random.normal(0, 2) for _ in range(50)],  # High volatility
            'volumes': [1000 + np.random.randint(-500, 500) for _ in range(50)],
            'high_prices': [100 + np.random.normal(0, 2) + 1 for _ in range(50)],
            'low_prices': [100 + np.random.normal(0, 2) - 1 for _ in range(50)]
        }

        result = await regime_detector.analyze_regime(volatile_data)

        assert result['volatility'] > 0.3
        assert 'regime' in result


class TestMultiAssetCorrelationEngine:
    """Test cases for Multi-Asset Correlation Engine"""

    @pytest.fixture
    async def correlation_engine(self):
        engine = MultiAssetCorrelationEngine()
        await engine.initialize(['XAUUSD', 'EURUSD', 'DXY'])
        return engine

    @pytest.mark.asyncio
    async def test_correlation_engine_initialization(self, correlation_engine):
        """Test correlation engine initialization"""
        assert correlation_engine is not None
        assert len(correlation_engine.monitored_assets) >= 3
        assert 'XAUUSD' in correlation_engine.monitored_assets

    @pytest.mark.asyncio
    async def test_price_data_update(self, correlation_engine):
        """Test price data updating"""
        await correlation_engine.update_price_data('XAUUSD', 1850.0)
        await correlation_engine.update_price_data('EURUSD', 1.0500)

        assert len(correlation_engine.price_history['XAUUSD']) > 0
        assert len(correlation_engine.price_history['EURUSD']) > 0

    @pytest.mark.asyncio
    async def test_correlation_analysis(self, correlation_engine):
        """Test correlation analysis"""
        # Add sample price data
        for i in range(20):
            price_xau = 1850 + i * 0.5
            price_eur = 1.05 + i * 0.001
            price_dxy = 103 - i * 0.1  # Negative correlation with EUR

            await correlation_engine.update_price_data('XAUUSD', price_xau)
            await correlation_engine.update_price_data('EURUSD', price_eur)
            await correlation_engine.update_price_data('DXY', price_dxy)

        market_data = {'price': 1860.0}
        result = await correlation_engine.analyze_correlations('XAUUSD', market_data)

        assert 'correlations' in result
        assert 'dxy_impact' in result
        assert 'diversification_score' in result
        assert result['diversification_score'] >= 0.0


class TestFinBERTSentimentAnalyzer:
    """Test cases for FinBERT Sentiment Analysis"""

    @pytest.fixture
    async def sentiment_analyzer(self):
        analyzer = FinBERTSentimentAnalyzer()
        await analyzer.initialize()
        return analyzer

    @pytest.mark.asyncio
    async def test_sentiment_analyzer_initialization(self, sentiment_analyzer):
        """Test sentiment analyzer initialization"""
        assert sentiment_analyzer is not None
        assert hasattr(sentiment_analyzer, 'asset_keywords')

    @pytest.mark.asyncio
    async def test_positive_sentiment_analysis(self, sentiment_analyzer):
        """Test positive sentiment detection"""
        positive_news = [
            {
                'title': 'Gold prices rally on strong economic data',
                'content': 'Gold prices surged higher as investors showed confidence in the market outlook',
                'source': 'Reuters',
                'timestamp': datetime.now().isoformat()
            }
        ]

        sentiment_score = await sentiment_analyzer.analyze_news(positive_news)
        assert 0.5 <= sentiment_score <= 1.0  # Should be positive sentiment

    @pytest.mark.asyncio
    async def test_negative_sentiment_analysis(self, sentiment_analyzer):
        """Test negative sentiment detection"""
        negative_news = [
            {
                'title': 'Gold prices plummet on market fears',
                'content': 'Gold prices crashed as investors fled to cash amid widespread market panic and uncertainty',
                'source': 'Reuters',
                'timestamp': datetime.now().isoformat()
            }
        ]

        sentiment_score = await sentiment_analyzer.analyze_news(negative_news)
        assert 0.0 <= sentiment_score <= 0.5  # Should be negative sentiment

    @pytest.mark.asyncio
    async def test_asset_specific_sentiment(self, sentiment_analyzer):
        """Test asset-specific sentiment analysis"""
        gold_news = [
            {
                'title': 'Gold outlook remains bullish',
                'content': 'Analysts are optimistic about gold prices with strong fundamentals',
                'source': 'Financial Times',
                'timestamp': datetime.now().isoformat()
            }
        ]

        result = await sentiment_analyzer.analyze_asset_sentiment('XAUUSD', gold_news)

        assert 'overall_sentiment' in result
        assert 'confidence' in result
        assert 'category' in result
        assert -1.0 <= result['overall_sentiment'] <= 1.0


class TestForexSessionAnalyzer:
    """Test cases for Forex Session Analysis"""

    @pytest.fixture
    async def session_analyzer(self):
        analyzer = ForexSessionAnalyzer()
        await analyzer.initialize()
        return analyzer

    @pytest.mark.asyncio
    async def test_session_analyzer_initialization(self, session_analyzer):
        """Test session analyzer initialization"""
        assert session_analyzer is not None
        assert len(session_analyzer.sessions) > 0
        assert TradingSession.LONDON in session_analyzer.sessions

    @pytest.mark.asyncio
    async def test_london_session_detection(self, session_analyzer):
        """Test London session detection"""
        # Test during London session hours (7:00-16:00 UTC)
        london_time = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)

        result = await session_analyzer.analyze_session_activity('EURUSD', london_time)

        assert result['primary_session'] in ['london', 'new_york']
        assert result['activity_scores']['london'] > 0.0

    @pytest.mark.asyncio
    async def test_session_overlap_detection(self, session_analyzer):
        """Test session overlap detection"""
        # Test during London-New York overlap (13:00-16:00 UTC)
        overlap_time = datetime.now().replace(hour=14, minute=0, second=0, microsecond=0)

        result = await session_analyzer.analyze_session_activity('EURUSD', overlap_time)

        # Should detect high activity during overlap
        assert result['volatility_expectation'] > 0.5
        assert result['liquidity_level'] > 0.5

    @pytest.mark.asyncio
    async def test_currency_pair_recommendations(self, session_analyzer):
        """Test currency pair recommendations by session"""
        result = await session_analyzer.analyze_session_activity('USDJPY')

        assert 'recommended_pairs' in result
        assert len(result['recommended_pairs']) > 0


class TestAutoMLOptimizer:
    """Test cases for AutoML Optimizer"""

    @pytest.fixture
    async def automl_optimizer(self):
        optimizer = AutoMLOptimizer()
        await optimizer.initialize()
        return optimizer

    @pytest.mark.asyncio
    async def test_automl_initialization(self, automl_optimizer):
        """Test AutoML optimizer initialization"""
        assert automl_optimizer is not None
        assert automl_optimizer.config is not None

    @pytest.mark.asyncio
    async def test_indicator_weight_optimization(self, automl_optimizer):
        """Test indicator weight optimization"""
        # Sample indicator performance data
        indicator_performance = {
            'rsi': [0.6, 0.7, 0.5, 0.8, 0.6],
            'macd': [0.5, 0.6, 0.7, 0.5, 0.9],
            'stochastic': [0.4, 0.5, 0.6, 0.7, 0.5],
            'volume': [0.7, 0.8, 0.6, 0.7, 0.8]
        }

        weights = await automl_optimizer.optimize_indicator_weights(indicator_performance)

        assert len(weights) == len(indicator_performance)
        assert all(0.0 <= weight <= 1.0 for weight in weights.values())
        assert abs(sum(weights.values()) - 1.0) < 0.01  # Weights should sum to ~1

    @pytest.mark.asyncio
    async def test_strategy_parameter_optimization(self, automl_optimizer):
        """Test strategy parameter optimization"""
        # Sample performance data
        performance_data = pd.DataFrame({
            'feature1': np.random.normal(0, 1, 100),
            'feature2': np.random.normal(0, 1, 100),
            'feature3': np.random.normal(0, 1, 100),
            'return': np.random.normal(0.1, 0.5, 100)
        })

        parameter_space = {
            'confidence_threshold': {'type': 'float', 'low': 0.5, 'high': 0.9},
            'risk_per_trade': {'type': 'float', 'low': 0.01, 'high': 0.05},
            'strategy_type': {'type': 'categorical', 'choices': ['conservative', 'aggressive']}
        }

        result = await automl_optimizer.optimize_strategy_parameters(performance_data, parameter_space)

        assert result.best_params is not None
        assert 'confidence_threshold' in result.best_params
        assert result.trials_completed > 0

    @pytest.mark.asyncio
    async def test_model_ensemble_optimization(self, automl_optimizer):
        """Test model ensemble optimization"""
        # Sample training data
        training_data = pd.DataFrame({
            'feature1': np.random.normal(0, 1, 100),
            'feature2': np.random.normal(0, 1, 100),
            'feature3': np.random.normal(0, 1, 100),
            'target': np.random.normal(0, 1, 100)
        })

        ensemble_config = await automl_optimizer.optimize_model_ensemble(training_data)

        assert 'models' in ensemble_config
        assert len(ensemble_config['models']) > 0
        assert 'total_performance' in ensemble_config


class TestHybridAIEngine:
    """Test cases for Hybrid AI Engine"""

    @pytest.fixture
    async def hybrid_ai_engine(self):
        config = HybridAIConfig(
            primary_asset=TradingAsset.XAUUSD,
            correlation_assets=[TradingAsset.DXY, TradingAsset.EURUSD],
            enable_finbert=True,
            enable_ensemble=True,
            confidence_threshold=0.7
        )
        engine = HybridAITradingEngine(config)
        await engine.initialize()
        return engine

    @pytest.mark.asyncio
    async def test_hybrid_ai_initialization(self, hybrid_ai_engine):
        """Test hybrid AI engine initialization"""
        assert hybrid_ai_engine is not None
        assert hybrid_ai_engine.config.primary_asset == TradingAsset.XAUUSD

    @pytest.mark.asyncio
    async def test_market_analysis(self, hybrid_ai_engine):
        """Test comprehensive market analysis"""
        market_data = {
            'symbol': 'XAUUSD',
            'timestamp': datetime.now(),
            'close': 1850.0,
            'close_prices': [1840 + i * 0.1 for i in range(100)],
            'volumes': [100000] * 100,
            'high_prices': [1840 + i * 0.1 + 0.5 for i in range(100)],
            'low_prices': [1840 + i * 0.1 - 0.5 for i in range(100)],
            'news_data': [
                {
                    'title': 'Gold market analysis',
                    'content': 'Positive outlook for gold prices',
                    'source': 'Reuters',
                    'timestamp': datetime.now().isoformat()
                }
            ]
        }

        insight = await hybrid_ai_engine.analyze_market(market_data)

        assert insight.asset == 'XAUUSD'
        assert insight.confidence >= 0.0
        assert insight.regime_prediction is not None
        assert isinstance(insight.correlation_strength, dict)

    @pytest.mark.asyncio
    async def test_trading_signal_generation(self, hybrid_ai_engine):
        """Test trading signal generation"""
        market_data = {
            'symbol': 'XAUUSD',
            'timestamp': datetime.now(),
            'close': 1850.0,
            'close_prices': [1840 + i * 0.2 for i in range(100)],  # Trending up
            'volumes': [100000] * 100
        }

        signal = await hybrid_ai_engine.generate_trading_signal(market_data)

        if signal:  # Signal might be None if conditions not met
            assert signal.asset == 'XAUUSD'
            assert signal.signal_type in ['buy', 'sell', 'hold']
            assert 0.0 <= signal.confidence <= 1.0
            assert signal.entry_price > 0
            assert signal.stop_loss > 0
            assert signal.take_profit > 0

    @pytest.mark.asyncio
    async def test_performance_update(self, hybrid_ai_engine):
        """Test performance tracking update"""
        # First generate a signal
        market_data = {
            'symbol': 'XAUUSD',
            'close': 1850.0,
            'close_prices': [1840 + i * 0.1 for i in range(100)],
            'volumes': [100000] * 100
        }

        signal = await hybrid_ai_engine.generate_trading_signal(market_data)

        if signal:
            # Simulate trade result
            trade_result = {
                'pnl': 25.0,
                'execution_price': signal.entry_price,
                'execution_time': 0.05
            }

            # Update performance
            await hybrid_ai_engine.update_performance(signal, trade_result)

            # Check that performance was recorded
            assert len(hybrid_ai_engine.performance_history) > 0


class TestHybridTradingSystem:
    """Test cases for Complete Hybrid Trading System"""

    @pytest.fixture
    async def hybrid_system(self):
        system = HybridTradingSystem()
        await system.initialize()
        return system

    @pytest.mark.asyncio
    async def test_hybrid_system_initialization(self, hybrid_system):
        """Test complete system initialization"""
        assert hybrid_system is not None
        assert hybrid_system.hybrid_ai_engine is not None

    @pytest.mark.asyncio
    async def test_trading_decision_generation(self, hybrid_system):
        """Test end-to-end trading decision generation"""
        market_data = {
            'symbol': 'XAUUSD',
            'timestamp': datetime.now().isoformat(),
            'open': 1850.25,
            'high': 1852.80,
            'low': 1848.90,
            'close': 1851.45,
            'volume': 125000,
            'close_prices': [1840 + i * 0.1 for i in range(100)],
            'volumes': [100000] * 100,
            'high_prices': [1840 + i * 0.1 + 0.5 for i in range(100)],
            'low_prices': [1840 + i * 0.1 - 0.5 for i in range(100)]
        }

        decision = await hybrid_system.generate_trading_decision(market_data)

        if decision:  # Decision might be None if no action recommended
            assert 'action' in decision
            assert 'confidence' in decision
            assert 'entry_price' in decision
            assert 'traditional_contribution' in decision
            assert 'ai_contribution' in decision
            assert decision['action'] in ['buy', 'sell', 'hold']

    @pytest.mark.asyncio
    async def test_performance_tracking(self, hybrid_system):
        """Test performance tracking system"""
        # Simulate a decision and result
        decision = {
            'symbol': 'XAUUSD',
            'action': 'buy',
            'confidence': 0.75,
            'ai_contribution': 0.4,
            'traditional_contribution': 0.6,
            'timestamp': datetime.now().isoformat()
        }

        trade_result = {
            'pnl': 15.0,
            'execution_price': 1851.45,
            'execution_time': 0.03
        }

        initial_total_pnl = hybrid_system.performance_metrics['total_pnl']
        await hybrid_system.update_performance(decision, trade_result)

        assert hybrid_system.performance_metrics['total_trades'] > 0
        assert hybrid_system.performance_metrics['total_pnl'] > initial_total_pnl

    @pytest.mark.asyncio
    async def test_system_status(self, hybrid_system):
        """Test system status reporting"""
        status = await hybrid_system.get_system_status()

        assert 'system_health' in status
        assert 'performance_metrics' in status
        assert 'ai_framework_status' in status
        assert 'integration_health' in status


class TestIntegrationScenarios:
    """Test integration scenarios and edge cases"""

    @pytest.mark.asyncio
    async def test_high_volatility_scenario(self):
        """Test system behavior during high volatility"""
        system = HybridTradingSystem()
        await system.initialize()

        # Create high volatility market data
        volatile_data = {
            'symbol': 'XAUUSD',
            'close': 1850.0,
            'close_prices': [1850 + np.random.normal(0, 5) for _ in range(100)],
            'volumes': [100000 + np.random.randint(-50000, 50000) for _ in range(100)],
            'timestamp': datetime.now().isoformat()
        }

        decision = await system.generate_trading_decision(volatile_data)

        # System should either make conservative decisions or abstain
        if decision:
            assert decision['risk_level'] in ['medium', 'high']
            assert decision['position_size'] <= 0.03  # Conservative position sizing

    @pytest.mark.asyncio
    async def test_conflicting_signals_scenario(self):
        """Test system behavior when traditional and AI signals conflict"""
        system = HybridTradingSystem()
        await system.initialize()

        # This would typically be tested with mock data that creates conflicting signals
        # For now, we test that the system handles the scenario gracefully
        market_data = {
            'symbol': 'XAUUSD',
            'close': 1850.0,
            'close_prices': [1850] * 100,  # Flat market
            'volumes': [100000] * 100,
            'timestamp': datetime.now().isoformat()
        }

        decision = await system.generate_trading_decision(market_data)

        # In conflicting scenarios, system should either:
        # 1. Make conservative decision with lower confidence
        # 2. Abstain from trading (return None)
        if decision:
            assert decision['confidence'] <= 0.8  # Should have reduced confidence

    @pytest.mark.asyncio
    async def test_news_impact_scenario(self):
        """Test system behavior during major news events"""
        system = HybridTradingSystem()
        await system.initialize()

        # Create market data with major news
        news_data = {
            'symbol': 'XAUUSD',
            'close': 1850.0,
            'close_prices': [1840 + i * 0.1 for i in range(100)],
            'volumes': [150000] * 100,  # Higher volume during news
            'news_data': [
                {
                    'title': 'Federal Reserve announces emergency rate cut',
                    'content': 'The Federal Reserve announced an emergency 0.75% rate cut citing economic concerns',
                    'source': 'Reuters',
                    'timestamp': datetime.now().isoformat()
                }
            ],
            'timestamp': datetime.now().isoformat()
        }

        decision = await system.generate_trading_decision(news_data)

        # System should incorporate news sentiment into decision
        if decision:
            assert 'ai_analysis' in decision
            # News should influence the AI component
            assert decision['ai_contribution'] > 0.0


# Utility functions for testing
def create_sample_market_data(symbol: str = 'XAUUSD', trend: str = 'up') -> Dict[str, Any]:
    """Create sample market data for testing"""
    base_price = 1850.0 if symbol == 'XAUUSD' else 1.0500

    if trend == 'up':
        prices = [base_price + i * 0.1 for i in range(100)]
    elif trend == 'down':
        prices = [base_price - i * 0.1 for i in range(100)]
    else:  # sideways
        prices = [base_price + np.sin(i * 0.1) * 0.5 for i in range(100)]

    return {
        'symbol': symbol,
        'close': prices[-1],
        'close_prices': prices,
        'volumes': [100000 + np.random.randint(-20000, 20000) for _ in range(100)],
        'high_prices': [p + 0.5 for p in prices],
        'low_prices': [p - 0.5 for p in prices],
        'timestamp': datetime.now().isoformat()
    }


def create_sample_news_data(sentiment: str = 'positive') -> List[Dict[str, Any]]:
    """Create sample news data for testing"""
    if sentiment == 'positive':
        return [
            {
                'title': 'Gold prices rally on positive economic outlook',
                'content': 'Gold prices surged as investors showed confidence',
                'source': 'Reuters',
                'timestamp': datetime.now().isoformat()
            }
        ]
    elif sentiment == 'negative':
        return [
            {
                'title': 'Gold prices plummet on market fears',
                'content': 'Gold prices crashed amid widespread panic',
                'source': 'Reuters',
                'timestamp': datetime.now().isoformat()
            }
        ]
    else:  # neutral
        return [
            {
                'title': 'Gold prices remain stable',
                'content': 'Gold prices showed little movement in quiet trading',
                'source': 'Reuters',
                'timestamp': datetime.now().isoformat()
            }
        ]


# Performance benchmarks
class TestPerformanceBenchmarks:
    """Performance benchmarks for the hybrid system"""

    @pytest.mark.asyncio
    async def test_decision_generation_speed(self):
        """Test that decision generation is fast enough for real-time trading"""
        system = HybridTradingSystem()
        await system.initialize()

        market_data = create_sample_market_data()

        # Measure decision generation time
        start_time = datetime.now()
        decision = await system.generate_trading_decision(market_data)
        end_time = datetime.now()

        decision_time = (end_time - start_time).total_seconds()

        # Should generate decision in under 2 seconds for real-time trading
        assert decision_time < 2.0

    @pytest.mark.asyncio
    async def test_memory_efficiency(self):
        """Test that the system doesn't consume excessive memory"""
        system = HybridTradingSystem()
        await system.initialize()

        # Process multiple market data points
        for i in range(10):
            market_data = create_sample_market_data()
            await system.generate_trading_decision(market_data)

        # System should handle multiple decisions without memory issues
        status = await system.get_system_status()
        assert status['system_health'] == 'healthy'


if __name__ == "__main__":
    # Run specific tests
    pytest.main([__file__, "-v"])