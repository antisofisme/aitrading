"""
Feature Calculator - Orchestrator for 72 ML Features (v2.3)

Based on TRADING_STRATEGY_AND_ML_DESIGN.md v2.3

Feature Groups (72 total):
1. News/Calendar (8) - 18%
2. Price Action/Structure (10) - 17%
3. Multi-Timeframe (9) - 14%
4. Candlestick Patterns (9) - 14%
5. Volume Analysis (8) - 14%
6. Volatility/Regime (6) - 11%
7. Divergence (4) - 9%
8. Market Context (6) - 7%
9. Momentum Indicators (3) - 5%
10. Moving Averages (2) - 2%
11. Fibonacci (9) - 8% ⭐ NEW v2.3
12. Structure SL/TP (5) - 5%
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from datetime import datetime

# Feature calculation modules (to be created)
from .features import (
    NewsCalendarFeatures,
    PriceActionFeatures,
    MultiTimeframeFeatures,
    CandlestickPatternFeatures,
    VolumeFeatures,
    VolatilityRegimeFeatures,
    DivergenceFeatures,
    MarketContextFeatures,
    MomentumFeatures,
    MovingAverageFeatures,
    FibonacciFeatures,  # NEW v2.3
    StructureSLTPFeatures
)

logger = logging.getLogger(__name__)


class FeatureCalculator:
    """
    Main feature calculator orchestrator

    Calculates 72 features from (v2.3):
    - Aggregates data (OHLCV + 26 indicators)
    - External data (6 sources)
    - Multi-timeframe context
    - Fibonacci levels (NEW v2.3)
    """

    def __init__(self, config: Dict[str, Any], clickhouse_client):
        self.config = config
        self.clickhouse = clickhouse_client

        # Initialize feature calculators
        self.news_calculator = NewsCalendarFeatures(config)
        self.price_action_calculator = PriceActionFeatures(config)
        self.multi_tf_calculator = MultiTimeframeFeatures(config)
        self.candlestick_calculator = CandlestickPatternFeatures(config)
        self.volume_calculator = VolumeFeatures(config)
        self.volatility_calculator = VolatilityRegimeFeatures(config)
        self.divergence_calculator = DivergenceFeatures(config)
        self.market_context_calculator = MarketContextFeatures(config)
        self.momentum_calculator = MomentumFeatures(config)
        self.ma_calculator = MovingAverageFeatures(config)
        self.fibonacci_calculator = FibonacciFeatures(config)  # NEW v2.3
        self.sl_tp_calculator = StructureSLTPFeatures(config)

        logger.info("🧮 Feature Calculator initialized with 12 feature groups (v2.3)")

    async def calculate_features(
        self,
        aggregates_batch: pd.DataFrame,
        timeframe: str = '1h'
    ) -> pd.DataFrame:
        """
        Calculate all 72 features for a batch of candles (v2.3)

        Args:
            aggregates_batch: DataFrame with OHLCV + indicators
            timeframe: Primary timeframe (default: '1h')

        Returns:
            DataFrame with 72 features + metadata (v2.3)
        """
        if aggregates_batch.empty:
            logger.warning("⚠️ Empty aggregates batch")
            return pd.DataFrame()

        logger.info(f"🧮 Calculating 72 features for {len(aggregates_batch)} candles... (v2.3)")

        results = []

        for idx, candle in aggregates_batch.iterrows():
            try:
                timestamp = pd.Timestamp(candle['timestamp'])
                symbol = candle['symbol']

                # 1. Get multi-timeframe data
                multi_tf_data = await self.clickhouse.get_multi_timeframe_aggregates(
                    symbol=symbol,
                    timestamp=timestamp,
                    lookback_candles=200
                )

                # 2. Get external data
                external_data = await self.clickhouse.get_external_data(
                    timestamp=timestamp,
                    lookback_hours=24
                )

                # 3. Calculate all feature groups
                features = {}

                # Group 1: News/Calendar (8 features) - 20%
                if self.config['feature_groups']['news_calendar']['enabled']:
                    news_features = self.news_calculator.calculate(
                        timestamp=timestamp,
                        external_data=external_data
                    )
                    features.update(news_features)

                # Group 2: Price Action/Structure (10 features) - 18%
                if self.config['feature_groups']['price_action']['enabled']:
                    price_features = self.price_action_calculator.calculate(
                        candle=candle,
                        multi_tf_data=multi_tf_data
                    )
                    features.update(price_features)

                # Group 3: Multi-Timeframe (9 features) - 15%
                if self.config['feature_groups']['multi_timeframe']['enabled']:
                    mtf_features = self.multi_tf_calculator.calculate(
                        multi_tf_data=multi_tf_data,
                        current_timestamp=timestamp
                    )
                    features.update(mtf_features)

                # Group 4: Candlestick Patterns (9 features) - 15%
                if self.config['feature_groups']['candlestick_patterns']['enabled']:
                    candle_features = self.candlestick_calculator.calculate(
                        candle=candle,
                        h1_data=multi_tf_data.get('1h', pd.DataFrame())
                    )
                    features.update(candle_features)

                # Group 5: Volume Analysis (8 features) - 15%
                if self.config['feature_groups']['volume_analysis']['enabled']:
                    volume_features = self.volume_calculator.calculate(
                        candle=candle,
                        h1_data=multi_tf_data.get('1h', pd.DataFrame())
                    )
                    features.update(volume_features)

                # Group 6: Volatility/Regime (6 features) - 12%
                if self.config['feature_groups']['volatility_regime']['enabled']:
                    volatility_features = self.volatility_calculator.calculate(
                        candle=candle,
                        h1_data=multi_tf_data.get('1h', pd.DataFrame())
                    )
                    features.update(volatility_features)

                # Group 7: Divergence (4 features) - 10%
                if self.config['feature_groups']['divergence']['enabled']:
                    divergence_features = self.divergence_calculator.calculate(
                        h1_data=multi_tf_data.get('1h', pd.DataFrame())
                    )
                    features.update(divergence_features)

                # Group 8: Market Context (6 features) - 8%
                if self.config['feature_groups']['market_context']['enabled']:
                    context_features = self.market_context_calculator.calculate(
                        timestamp=timestamp,
                        external_data=external_data
                    )
                    features.update(context_features)

                # Group 9: Momentum Indicators (3 features) - 5%
                if self.config['feature_groups']['momentum_indicators']['enabled']:
                    momentum_features = self.momentum_calculator.calculate(
                        candle=candle
                    )
                    features.update(momentum_features)

                # Group 10: Moving Averages (2 features) - 2%
                if self.config['feature_groups']['moving_averages']['enabled']:
                    ma_features = self.ma_calculator.calculate(
                        candle=candle
                    )
                    features.update(ma_features)

                # Group 11: Fibonacci (9 features) - 8% ⭐ NEW v2.3
                if self.config['feature_groups'].get('fibonacci', {}).get('enabled', True):
                    fibonacci_features = self.fibonacci_calculator.calculate(
                        candle=candle,
                        multi_tf_data=multi_tf_data
                    )
                    features.update(fibonacci_features)

                # Group 12: Structure SL/TP (5 features) - 5%
                if self.config['feature_groups']['structure_sl_tp']['enabled']:
                    sl_tp_features = self.sl_tp_calculator.calculate(
                        candle=candle,
                        h1_data=multi_tf_data.get('1h', pd.DataFrame())
                    )
                    features.update(sl_tp_features)

                # Add metadata
                features['symbol'] = symbol
                features['timeframe'] = timeframe
                features['timestamp'] = timestamp
                features['timestamp_ms'] = candle['timestamp_ms']

                # Calculate target variable (binary: next candle UP/DOWN)
                features['target'] = self._calculate_target(candle, aggregates_batch, idx)

                results.append(features)

                logger.debug(f"✅ Features calculated for {timestamp}: {len(features)} fields")

            except Exception as e:
                logger.error(f"❌ Feature calculation failed for candle {idx}: {e}")
                continue

        # Convert to DataFrame
        features_df = pd.DataFrame(results)

        logger.info(f"✅ Feature calculation complete: {len(features_df)} rows with {len(features_df.columns)} columns")

        return features_df

    def _calculate_target(
        self,
        current_candle: pd.Series,
        aggregates_batch: pd.DataFrame,
        current_idx: int
    ) -> int:
        """
        Calculate target variable: 1 if next candle closes higher, 0 otherwise

        Args:
            current_candle: Current candle data
            aggregates_batch: Full batch of candles
            current_idx: Index of current candle

        Returns:
            1 (UP) or 0 (DOWN)
        """
        try:
            # Check if next candle exists
            if current_idx + 1 < len(aggregates_batch):
                next_candle = aggregates_batch.iloc[current_idx + 1]

                current_close = float(current_candle['close'])
                next_close = float(next_candle['close'])

                # Binary target: 1 if next close > current close
                return 1 if next_close > current_close else 0
            else:
                # No next candle available
                return -1  # Mark as unknown

        except Exception as e:
            logger.error(f"❌ Target calculation failed: {e}")
            return -1
