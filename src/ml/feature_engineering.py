"""
AI Trading System - Feature Engineering Module
==============================================

This module implements comprehensive feature engineering strategies for
the AI trading system, including technical indicators, market microstructure
features, cross-asset features, and alternative data processing.
"""

import numpy as np
import pandas as pd
import talib
from typing import Dict, List, Optional, Tuple, Any
from scipy import stats
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler
from sklearn.feature_selection import SelectKBest, f_regression, mutual_info_regression
import warnings
warnings.filterwarnings('ignore')

class TechnicalIndicators:
    """Technical indicator calculations using TA-Lib and custom implementations"""

    @staticmethod
    def price_features(df: pd.DataFrame, price_col: str = 'close') -> pd.DataFrame:
        """Calculate price-based technical indicators"""
        features = pd.DataFrame(index=df.index)
        prices = df[price_col].values

        # Moving averages
        for period in [5, 10, 20, 50, 200]:
            features[f'sma_{period}'] = talib.SMA(prices, timeperiod=period)
            features[f'ema_{period}'] = talib.EMA(prices, timeperiod=period)
            features[f'price_sma_{period}_ratio'] = prices / features[f'sma_{period}']

        # RSI
        for period in [14, 21]:
            features[f'rsi_{period}'] = talib.RSI(prices, timeperiod=period)

        # MACD
        macd, macd_signal, macd_hist = talib.MACD(prices)
        features['macd'] = macd
        features['macd_signal'] = macd_signal
        features['macd_histogram'] = macd_hist

        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = talib.BBANDS(prices)
        features['bb_upper'] = bb_upper
        features['bb_middle'] = bb_middle
        features['bb_lower'] = bb_lower
        features['bb_width'] = (bb_upper - bb_lower) / bb_middle
        features['bb_position'] = (prices - bb_lower) / (bb_upper - bb_lower)

        # ATR
        high = df['high'].values
        low = df['low'].values
        for period in [14, 21]:
            features[f'atr_{period}'] = talib.ATR(high, low, prices, timeperiod=period)

        # Stochastic Oscillator
        slowk, slowd = talib.STOCH(high, low, prices)
        features['stoch_k'] = slowk
        features['stoch_d'] = slowd

        # Williams %R
        features['williams_r'] = talib.WILLR(high, low, prices)

        # CCI
        features['cci'] = talib.CCI(high, low, prices)

        # Price momentum
        for period in [1, 5, 10, 20]:
            features[f'momentum_{period}'] = prices / np.roll(prices, period) - 1

        return features

    @staticmethod
    def volume_features(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate volume-based indicators"""
        features = pd.DataFrame(index=df.index)

        volume = df['volume'].values
        prices = df['close'].values
        high = df['high'].values
        low = df['low'].values

        # Volume moving averages
        for period in [10, 20, 50]:
            features[f'volume_sma_{period}'] = talib.SMA(volume, timeperiod=period)
            features[f'volume_ratio_{period}'] = volume / features[f'volume_sma_{period}']

        # VWAP
        typical_price = (high + low + prices) / 3
        features['vwap'] = np.cumsum(typical_price * volume) / np.cumsum(volume)
        features['vwap_deviation'] = (prices - features['vwap']) / features['vwap']

        # Volume indicators
        features['ad_line'] = talib.AD(high, low, prices, volume)
        features['obv'] = talib.OBV(prices, volume)
        features['chaikin_mf'] = talib.ADOSC(high, low, prices, volume)

        # Volume price trend
        features['vpt'] = TechnicalIndicators._volume_price_trend(prices, volume)

        # Price volume relationships
        features['price_volume_corr'] = TechnicalIndicators._rolling_correlation(
            prices, volume, window=20
        )

        return features

    @staticmethod
    def volatility_features(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate volatility-based features"""
        features = pd.DataFrame(index=df.index)

        prices = df['close'].values
        high = df['high'].values
        low = df['low'].values
        returns = np.log(prices / np.roll(prices, 1))

        # Realized volatility
        for window in [5, 10, 20, 50]:
            features[f'realized_vol_{window}'] = pd.Series(returns).rolling(window).std() * np.sqrt(252)

        # GARCH volatility (simplified)
        features['garch_vol'] = TechnicalIndicators._garch_volatility(returns)

        # High-low ratios
        features['hl_ratio'] = (high - low) / prices
        features['hl_ratio_ma'] = pd.Series(features['hl_ratio']).rolling(20).mean()

        # Parkinson volatility
        features['parkinson_vol'] = TechnicalIndicators._parkinson_volatility(high, low)

        # Volatility cones
        features['vol_cone_percentile'] = TechnicalIndicators._volatility_cone(returns)

        return features

    @staticmethod
    def _volume_price_trend(prices: np.ndarray, volume: np.ndarray) -> np.ndarray:
        """Calculate Volume Price Trend indicator"""
        price_changes = np.diff(prices, prepend=prices[0])
        vpt = np.zeros_like(prices)
        for i in range(1, len(prices)):
            vpt[i] = vpt[i-1] + volume[i] * (price_changes[i] / prices[i-1])
        return vpt

    @staticmethod
    def _rolling_correlation(x: np.ndarray, y: np.ndarray, window: int) -> np.ndarray:
        """Calculate rolling correlation between two series"""
        corr = np.full_like(x, np.nan)
        for i in range(window, len(x)):
            corr[i] = np.corrcoef(x[i-window:i], y[i-window:i])[0, 1]
        return corr

    @staticmethod
    def _garch_volatility(returns: np.ndarray, alpha: float = 0.1, beta: float = 0.85) -> np.ndarray:
        """Simplified GARCH(1,1) volatility estimation"""
        vol = np.zeros_like(returns)
        vol[0] = np.std(returns[:30])  # Initialize with first 30 observations

        for i in range(1, len(returns)):
            vol[i] = np.sqrt(alpha * returns[i-1]**2 + beta * vol[i-1]**2)

        return vol

    @staticmethod
    def _parkinson_volatility(high: np.ndarray, low: np.ndarray, window: int = 20) -> np.ndarray:
        """Calculate Parkinson volatility estimator"""
        hl_ratio = np.log(high / low) ** 2
        return pd.Series(hl_ratio).rolling(window).mean().values * np.sqrt(252 / (4 * np.log(2)))

    @staticmethod
    def _volatility_cone(returns: np.ndarray, windows: List[int] = [10, 20, 50, 100]) -> np.ndarray:
        """Calculate volatility cone percentiles"""
        percentiles = np.full_like(returns, np.nan)

        for i in range(max(windows), len(returns)):
            current_vols = []
            for window in windows:
                vol = np.std(returns[i-window:i]) * np.sqrt(252)
                current_vols.append(vol)

            # Calculate percentile rank of current volatility
            historical_vols = []
            for j in range(max(windows), i):
                for window in windows:
                    vol = np.std(returns[j-window:j]) * np.sqrt(252)
                    historical_vols.append(vol)

            if historical_vols:
                percentiles[i] = stats.percentileofscore(historical_vols, np.mean(current_vols))

        return percentiles

class MarketMicrostructure:
    """Market microstructure feature calculations"""

    @staticmethod
    def bid_ask_features(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate bid-ask spread features"""
        features = pd.DataFrame(index=df.index)

        if 'bid' in df.columns and 'ask' in df.columns:
            bid = df['bid'].values
            ask = df['ask'].values
            mid = (bid + ask) / 2

            # Spread measures
            features['bid_ask_spread'] = ask - bid
            features['relative_spread'] = (ask - bid) / mid
            features['spread_ma'] = pd.Series(features['bid_ask_spread']).rolling(20).mean()

            # Order imbalance (simplified)
            features['order_imbalance'] = (bid - ask) / (bid + ask)

        return features

    @staticmethod
    def trade_features(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate trade-based features"""
        features = pd.DataFrame(index=df.index)

        if 'trade_size' in df.columns:
            trade_size = df['trade_size'].values

            # Trade size statistics
            for window in [10, 20, 50]:
                features[f'trade_size_avg_{window}'] = pd.Series(trade_size).rolling(window).mean()
                features[f'trade_size_std_{window}'] = pd.Series(trade_size).rolling(window).std()

        # Trade frequency (simplified as inverse of time between trades)
        if 'timestamp' in df.columns:
            time_diff = df['timestamp'].diff().dt.total_seconds()
            features['trade_frequency'] = 1 / time_diff.rolling(20).mean()

        return features

class CrossAssetFeatures:
    """Cross-asset and market regime features"""

    @staticmethod
    def correlation_features(df: pd.DataFrame, benchmark_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Calculate correlations with other assets"""
        features = pd.DataFrame(index=df.index)
        returns = df['close'].pct_change()

        for asset_name, asset_data in benchmark_data.items():
            if 'close' in asset_data.columns:
                asset_returns = asset_data['close'].pct_change()

                # Rolling correlations
                for window in [20, 50, 100]:
                    features[f'{asset_name}_corr_{window}'] = returns.rolling(window).corr(asset_returns)

                # Beta calculation
                features[f'{asset_name}_beta'] = CrossAssetFeatures._rolling_beta(
                    returns, asset_returns, window=50
                )

        return features

    @staticmethod
    def regime_features(df: pd.DataFrame, vix_data: pd.DataFrame = None) -> pd.DataFrame:
        """Calculate market regime indicators"""
        features = pd.DataFrame(index=df.index)

        if vix_data is not None and 'close' in vix_data.columns:
            vix = vix_data['close'].reindex(df.index, method='ffill')

            # VIX features
            features['vix_level'] = vix
            features['vix_percentile'] = vix.rolling(252).rank(pct=True)
            features['vix_spike'] = (vix > vix.rolling(20).mean() + 2 * vix.rolling(20).std()).astype(int)

        # Market stress indicators
        returns = df['close'].pct_change()
        features['drawdown'] = CrossAssetFeatures._calculate_drawdown(df['close'])
        features['volatility_regime'] = CrossAssetFeatures._volatility_regime(returns)

        return features

    @staticmethod
    def _rolling_beta(asset_returns: pd.Series, market_returns: pd.Series, window: int) -> pd.Series:
        """Calculate rolling beta"""
        def beta_calc(x, y):
            if len(x) < 10 or len(y) < 10:
                return np.nan
            covariance = np.cov(x, y)[0, 1]
            market_variance = np.var(y)
            return covariance / market_variance if market_variance != 0 else np.nan

        return asset_returns.rolling(window).apply(
            lambda x: beta_calc(x.values, market_returns.loc[x.index].values)
        )

    @staticmethod
    def _calculate_drawdown(prices: pd.Series) -> pd.Series:
        """Calculate rolling maximum drawdown"""
        cumulative = (1 + prices.pct_change()).cumprod()
        running_max = cumulative.expanding().max()
        return (cumulative - running_max) / running_max

    @staticmethod
    def _volatility_regime(returns: pd.Series, threshold: float = 0.02) -> pd.Series:
        """Classify volatility regime (low/medium/high)"""
        rolling_vol = returns.rolling(20).std() * np.sqrt(252)
        vol_percentiles = rolling_vol.rolling(252).rank(pct=True)

        regime = pd.Series(index=returns.index, dtype=int)
        regime[vol_percentiles <= 0.33] = 0  # Low volatility
        regime[(vol_percentiles > 0.33) & (vol_percentiles <= 0.67)] = 1  # Medium volatility
        regime[vol_percentiles > 0.67] = 2  # High volatility

        return regime

class AlternativeDataFeatures:
    """Alternative data feature processing"""

    @staticmethod
    def news_sentiment_features(sentiment_data: pd.DataFrame) -> pd.DataFrame:
        """Process news sentiment data"""
        features = pd.DataFrame(index=sentiment_data.index)

        if 'sentiment_score' in sentiment_data.columns:
            sentiment = sentiment_data['sentiment_score']

            # Sentiment features
            features['sentiment_score'] = sentiment
            features['sentiment_ma'] = sentiment.rolling(5).mean()
            features['sentiment_std'] = sentiment.rolling(10).std()
            features['sentiment_momentum'] = sentiment - sentiment.shift(1)

            # Sentiment extremes
            features['sentiment_extreme_positive'] = (sentiment > sentiment.quantile(0.9)).astype(int)
            features['sentiment_extreme_negative'] = (sentiment < sentiment.quantile(0.1)).astype(int)

        return features

    @staticmethod
    def social_sentiment_features(social_data: pd.DataFrame) -> pd.DataFrame:
        """Process social media sentiment data"""
        features = pd.DataFrame(index=social_data.index)

        if 'mentions' in social_data.columns and 'sentiment' in social_data.columns:
            mentions = social_data['mentions']
            sentiment = social_data['sentiment']

            # Volume-weighted sentiment
            features['weighted_sentiment'] = sentiment * mentions
            features['mention_volume'] = mentions
            features['sentiment_dispersion'] = social_data.groupby(social_data.index.date)['sentiment'].std()

        return features

class TemporalFeatures:
    """Time-based feature engineering"""

    @staticmethod
    def calendar_features(df: pd.DataFrame) -> pd.DataFrame:
        """Generate calendar-based features"""
        features = pd.DataFrame(index=df.index)

        # Time features
        features['hour'] = df.index.hour
        features['day_of_week'] = df.index.dayofweek
        features['month'] = df.index.month
        features['quarter'] = df.index.quarter

        # Cyclical encoding
        features['hour_sin'] = np.sin(2 * np.pi * features['hour'] / 24)
        features['hour_cos'] = np.cos(2 * np.pi * features['hour'] / 24)
        features['day_sin'] = np.sin(2 * np.pi * features['day_of_week'] / 7)
        features['day_cos'] = np.cos(2 * np.pi * features['day_of_week'] / 7)
        features['month_sin'] = np.sin(2 * np.pi * features['month'] / 12)
        features['month_cos'] = np.cos(2 * np.pi * features['month'] / 12)

        # Market session indicators
        features['pre_market'] = ((features['hour'] >= 4) & (features['hour'] < 9.5)).astype(int)
        features['market_open'] = ((features['hour'] >= 9.5) & (features['hour'] < 16)).astype(int)
        features['after_hours'] = ((features['hour'] >= 16) & (features['hour'] < 20)).astype(int)

        # Special periods
        features['month_end'] = (df.index.day > 25).astype(int)
        features['month_beginning'] = (df.index.day <= 5).astype(int)
        features['friday_close'] = ((features['day_of_week'] == 4) & (features['hour'] >= 15)).astype(int)

        return features

class FeatureEngineer:
    """Main feature engineering class that orchestrates all feature calculations"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.scalers = {}
        self.feature_selectors = {}

    def create_features(
        self,
        df: pd.DataFrame,
        benchmark_data: Optional[Dict[str, pd.DataFrame]] = None,
        sentiment_data: Optional[pd.DataFrame] = None,
        social_data: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """Create comprehensive feature set"""

        all_features = []

        # Technical indicators
        tech_features = TechnicalIndicators.price_features(df)
        tech_features = pd.concat([tech_features, TechnicalIndicators.volume_features(df)], axis=1)
        tech_features = pd.concat([tech_features, TechnicalIndicators.volatility_features(df)], axis=1)
        all_features.append(tech_features)

        # Market microstructure
        if any(col in df.columns for col in ['bid', 'ask', 'trade_size']):
            micro_features = MarketMicrostructure.bid_ask_features(df)
            micro_features = pd.concat([micro_features, MarketMicrostructure.trade_features(df)], axis=1)
            all_features.append(micro_features)

        # Cross-asset features
        if benchmark_data:
            cross_features = CrossAssetFeatures.correlation_features(df, benchmark_data)
            cross_features = pd.concat([cross_features, CrossAssetFeatures.regime_features(df)], axis=1)
            all_features.append(cross_features)

        # Alternative data
        if sentiment_data is not None:
            sentiment_features = AlternativeDataFeatures.news_sentiment_features(sentiment_data)
            all_features.append(sentiment_features)

        if social_data is not None:
            social_features = AlternativeDataFeatures.social_sentiment_features(social_data)
            all_features.append(social_features)

        # Temporal features
        temporal_features = TemporalFeatures.calendar_features(df)
        all_features.append(temporal_features)

        # Combine all features
        combined_features = pd.concat(all_features, axis=1)

        # Add statistical features
        combined_features = self._add_statistical_features(combined_features, df)

        # Add lag features
        combined_features = self._add_lag_features(combined_features)

        return combined_features

    def _add_statistical_features(self, features: pd.DataFrame, price_data: pd.DataFrame) -> pd.DataFrame:
        """Add statistical transformations of features"""
        returns = price_data['close'].pct_change()

        # Rolling statistics for key features
        for col in features.select_dtypes(include=[np.number]).columns[:20]:  # Limit to avoid explosion
            for window in [5, 10, 20]:
                features[f'{col}_ma_{window}'] = features[col].rolling(window).mean()
                features[f'{col}_std_{window}'] = features[col].rolling(window).std()
                features[f'{col}_zscore_{window}'] = (
                    features[col] - features[col].rolling(window).mean()
                ) / features[col].rolling(window).std()

        # Cross-feature interactions (limited set)
        key_features = ['rsi_14', 'macd', 'bb_position', 'volume_ratio_20']
        for i, feat1 in enumerate(key_features):
            for feat2 in key_features[i+1:]:
                if feat1 in features.columns and feat2 in features.columns:
                    features[f'{feat1}_{feat2}_ratio'] = features[feat1] / (features[feat2] + 1e-8)

        return features

    def _add_lag_features(self, features: pd.DataFrame, lags: List[int] = [1, 2, 3, 5]) -> pd.DataFrame:
        """Add lagged versions of key features"""
        key_features = ['rsi_14', 'macd', 'bb_position', 'realized_vol_20']

        for feature in key_features:
            if feature in features.columns:
                for lag in lags:
                    features[f'{feature}_lag_{lag}'] = features[feature].shift(lag)

        return features

    def scale_features(
        self,
        features: pd.DataFrame,
        method: str = 'robust',
        fit: bool = True
    ) -> pd.DataFrame:
        """Scale features using specified method"""

        if method not in self.scalers:
            if method == 'standard':
                self.scalers[method] = StandardScaler()
            elif method == 'robust':
                self.scalers[method] = RobustScaler()
            elif method == 'minmax':
                self.scalers[method] = MinMaxScaler()
            else:
                raise ValueError(f"Unknown scaling method: {method}")

        numeric_cols = features.select_dtypes(include=[np.number]).columns
        scaled_features = features.copy()

        if fit:
            scaled_values = self.scalers[method].fit_transform(features[numeric_cols])
        else:
            scaled_values = self.scalers[method].transform(features[numeric_cols])

        scaled_features[numeric_cols] = scaled_values
        return scaled_features

    def select_features(
        self,
        features: pd.DataFrame,
        target: pd.Series,
        method: str = 'mutual_info',
        k: int = 100,
        fit: bool = True
    ) -> pd.DataFrame:
        """Select top k features using specified method"""

        if method not in self.feature_selectors:
            if method == 'f_regression':
                self.feature_selectors[method] = SelectKBest(f_regression, k=k)
            elif method == 'mutual_info':
                self.feature_selectors[method] = SelectKBest(mutual_info_regression, k=k)
            else:
                raise ValueError(f"Unknown feature selection method: {method}")

        if fit:
            selected_features = self.feature_selectors[method].fit_transform(features, target)
            selected_feature_names = features.columns[self.feature_selectors[method].get_support()]
        else:
            selected_features = self.feature_selectors[method].transform(features)
            selected_feature_names = features.columns[self.feature_selectors[method].get_support()]

        return pd.DataFrame(selected_features, columns=selected_feature_names, index=features.index)

    def get_feature_importance(self, method: str = 'mutual_info') -> Dict[str, float]:
        """Get feature importance scores from the last feature selection"""
        if method in self.feature_selectors:
            selector = self.feature_selectors[method]
            if hasattr(selector, 'scores_'):
                feature_names = self.last_feature_names if hasattr(self, 'last_feature_names') else []
                return dict(zip(feature_names, selector.scores_))
        return {}

    def remove_correlated_features(
        self,
        features: pd.DataFrame,
        threshold: float = 0.95
    ) -> pd.DataFrame:
        """Remove highly correlated features"""
        corr_matrix = features.corr().abs()
        upper_triangle = corr_matrix.where(
            np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
        )

        to_drop = [column for column in upper_triangle.columns if any(upper_triangle[column] > threshold)]
        return features.drop(columns=to_drop)

    def create_target(
        self,
        df: pd.DataFrame,
        target_type: str = 'returns',
        horizon: int = 1,
        **kwargs
    ) -> pd.Series:
        """Create target variable for prediction"""

        if target_type == 'returns':
            # Future returns
            returns = df['close'].pct_change(horizon).shift(-horizon)
            return returns

        elif target_type == 'direction':
            # Direction of price movement
            returns = df['close'].pct_change(horizon).shift(-horizon)
            return (returns > 0).astype(int)

        elif target_type == 'volatility':
            # Future realized volatility
            returns = df['close'].pct_change()
            vol = returns.rolling(horizon).std().shift(-horizon)
            return vol

        elif target_type == 'sharpe':
            # Future Sharpe ratio
            returns = df['close'].pct_change()
            rolling_returns = returns.rolling(horizon).mean()
            rolling_vol = returns.rolling(horizon).std()
            sharpe = (rolling_returns / rolling_vol).shift(-horizon)
            return sharpe

        else:
            raise ValueError(f"Unknown target type: {target_type}")