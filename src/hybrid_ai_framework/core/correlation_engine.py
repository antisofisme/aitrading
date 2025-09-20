"""
Multi-Asset Correlation Engine
Advanced correlation analysis for forex/gold trading with DXY integration

Features:
- Real-time correlation calculation between assets
- DXY (Dollar Index) impact analysis for gold and forex
- Cross-asset correlation matrix
- Correlation-based risk assessment
- Dynamic correlation threshold adjustment
- Safe-haven flow analysis for gold
"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict, deque

try:
    from scipy.stats import pearsonr, spearmanr
    from sklearn.preprocessing import StandardScaler
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


class AssetClass(Enum):
    """Asset classification"""
    PRECIOUS_METAL = "precious_metal"
    MAJOR_CURRENCY = "major_currency"
    MINOR_CURRENCY = "minor_currency"
    COMMODITY_CURRENCY = "commodity_currency"
    SAFE_HAVEN = "safe_haven"
    INDEX = "index"


@dataclass
class CorrelationData:
    """Correlation data between two assets"""
    asset1: str
    asset2: str
    correlation: float
    p_value: float
    periods_analyzed: int
    correlation_strength: str  # weak, moderate, strong
    timestamp: datetime
    timeframe: str


@dataclass
class AssetProfile:
    """Profile of trading asset"""
    symbol: str
    asset_class: AssetClass
    base_currency: str
    quote_currency: str
    dxy_sensitivity: float  # How sensitive to DXY changes
    safe_haven_score: float  # Safe haven characteristics
    volatility_profile: str  # low, medium, high
    correlation_history: Dict[str, float] = field(default_factory=dict)


@dataclass
class CorrelationAnalysis:
    """Comprehensive correlation analysis result"""
    primary_asset: str
    correlations: Dict[str, CorrelationData]
    dxy_impact: Dict[str, float]
    risk_assessment: Dict[str, Any]
    safe_haven_flows: Dict[str, float]
    correlation_clusters: List[List[str]]
    diversification_score: float
    timestamp: datetime


class MultiAssetCorrelationEngine:
    """
    Advanced multi-asset correlation analysis engine

    Features:
    - Real-time correlation calculation
    - DXY impact analysis for all assets
    - Gold-specific safe haven analysis
    - Risk diversification scoring
    - Dynamic correlation monitoring
    - Asset clustering by correlation
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Asset profiles
        self.asset_profiles = self._initialize_asset_profiles()

        # Historical data storage
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=500))
        self.return_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=500))

        # Correlation cache
        self.correlation_cache: Dict[str, CorrelationData] = {}
        self.cache_expiry: Dict[str, datetime] = {}

        # Analysis parameters
        self.correlation_periods = {
            'short': 20,
            'medium': 50,
            'long': 100
        }

        # Correlation thresholds
        self.thresholds = {
            'weak': 0.3,
            'moderate': 0.6,
            'strong': 0.8
        }

        # DXY impact factors
        self.dxy_factors = {
            'XAUUSD': -0.8,  # Strong negative correlation
            'EURUSD': -0.7,
            'GBPUSD': -0.6,
            'AUDUSD': -0.5,
            'NZDUSD': -0.5,
            'USDCAD': 0.6,   # Positive correlation
            'USDJPY': 0.7,
            'USDCHF': 0.6
        }

        self.logger.info("Multi-Asset Correlation Engine initialized")

    async def initialize(self, monitored_assets: List) -> bool:
        """Initialize correlation engine with assets to monitor"""
        try:
            self.monitored_assets = [asset.value if hasattr(asset, 'value') else str(asset)
                                   for asset in monitored_assets]

            # Initialize data structures for monitored assets
            for asset in self.monitored_assets:
                if asset not in self.price_history:
                    self.price_history[asset] = deque(maxlen=500)
                    self.return_history[asset] = deque(maxlen=500)

            # Add DXY if not already included
            if 'DXY' not in self.monitored_assets:
                self.monitored_assets.append('DXY')
                self.price_history['DXY'] = deque(maxlen=500)
                self.return_history['DXY'] = deque(maxlen=500)

            self.logger.info(f"✅ Correlation engine initialized for {len(self.monitored_assets)} assets")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize correlation engine: {e}")
            return False

    async def update_price_data(self, asset: str, price: float, timestamp: datetime = None) -> None:
        """Update price data for an asset"""
        try:
            if timestamp is None:
                timestamp = datetime.now()

            # Store price
            self.price_history[asset].append((timestamp, price))

            # Calculate return if we have previous price
            if len(self.price_history[asset]) > 1:
                prev_price = self.price_history[asset][-2][1]
                if prev_price != 0:
                    return_value = (price - prev_price) / prev_price
                    self.return_history[asset].append((timestamp, return_value))

            # Invalidate related correlation cache
            await self._invalidate_correlation_cache(asset)

        except Exception as e:
            self.logger.error(f"❌ Failed to update price data for {asset}: {e}")

    async def analyze_correlations(self, primary_asset: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive correlation analysis

        Args:
            primary_asset: Main asset for analysis
            market_data: Current market data

        Returns:
            Dictionary with correlation analysis results
        """
        try:
            self.logger.debug(f"Analyzing correlations for {primary_asset}")

            # Update current market data
            if 'price' in market_data:
                await self.update_price_data(primary_asset, market_data['price'])

            # Calculate correlations with all monitored assets
            correlations = {}
            for asset in self.monitored_assets:
                if asset != primary_asset:
                    correlation_data = await self._calculate_correlation(primary_asset, asset)
                    if correlation_data:
                        correlations[asset] = correlation_data

            # Analyze DXY impact
            dxy_impact = await self._analyze_dxy_impact(primary_asset)

            # Assess correlation-based risk
            risk_assessment = await self._assess_correlation_risk(primary_asset, correlations)

            # Analyze safe haven flows (especially for gold)
            safe_haven_flows = await self._analyze_safe_haven_flows(primary_asset)

            # Identify correlation clusters
            correlation_clusters = await self._identify_correlation_clusters(primary_asset, correlations)

            # Calculate diversification score
            diversification_score = await self._calculate_diversification_score(correlations)

            # Create analysis result
            analysis = CorrelationAnalysis(
                primary_asset=primary_asset,
                correlations=correlations,
                dxy_impact=dxy_impact,
                risk_assessment=risk_assessment,
                safe_haven_flows=safe_haven_flows,
                correlation_clusters=correlation_clusters,
                diversification_score=diversification_score,
                timestamp=datetime.now()
            )

            return {
                'correlations': {k: {
                    'correlation': v.correlation,
                    'strength': v.correlation_strength,
                    'p_value': v.p_value
                } for k, v in correlations.items()},
                'dxy_impact': dxy_impact,
                'risk_assessment': risk_assessment,
                'safe_haven_flows': safe_haven_flows,
                'diversification_score': diversification_score,
                'correlation_clusters': correlation_clusters
            }

        except Exception as e:
            self.logger.error(f"❌ Correlation analysis failed for {primary_asset}: {e}")
            return await self._fallback_correlation_analysis(primary_asset)

    async def _calculate_correlation(self, asset1: str, asset2: str,
                                   timeframe: str = 'medium') -> Optional[CorrelationData]:
        """Calculate correlation between two assets"""
        try:
            # Check cache first
            cache_key = f"{asset1}_{asset2}_{timeframe}"
            if (cache_key in self.correlation_cache and
                cache_key in self.cache_expiry and
                datetime.now() - self.cache_expiry[cache_key] < timedelta(minutes=5)):
                return self.correlation_cache[cache_key]

            # Get return data for both assets
            periods = self.correlation_periods[timeframe]
            returns1 = await self._get_returns(asset1, periods)
            returns2 = await self._get_returns(asset2, periods)

            if len(returns1) < 10 or len(returns2) < 10:
                return None

            # Align the data by timestamp
            aligned_returns = await self._align_return_data(returns1, returns2)

            if len(aligned_returns) < 10:
                return None

            # Extract aligned return values
            values1 = [r[1] for r in aligned_returns]
            values2 = [r[2] for r in aligned_returns]

            # Calculate Pearson correlation
            if HAS_SCIPY:
                correlation, p_value = pearsonr(values1, values2)
            else:
                correlation = np.corrcoef(values1, values2)[0, 1]
                p_value = 0.05  # Default p-value when scipy not available

            # Determine correlation strength
            abs_corr = abs(correlation)
            if abs_corr >= self.thresholds['strong']:
                strength = 'strong'
            elif abs_corr >= self.thresholds['moderate']:
                strength = 'moderate'
            elif abs_corr >= self.thresholds['weak']:
                strength = 'weak'
            else:
                strength = 'negligible'

            # Create correlation data
            correlation_data = CorrelationData(
                asset1=asset1,
                asset2=asset2,
                correlation=correlation,
                p_value=p_value,
                periods_analyzed=len(aligned_returns),
                correlation_strength=strength,
                timestamp=datetime.now(),
                timeframe=timeframe
            )

            # Cache the result
            self.correlation_cache[cache_key] = correlation_data
            self.cache_expiry[cache_key] = datetime.now()

            return correlation_data

        except Exception as e:
            self.logger.error(f"❌ Correlation calculation failed for {asset1}-{asset2}: {e}")
            return None

    async def _get_returns(self, asset: str, periods: int) -> List[Tuple[datetime, float]]:
        """Get return data for an asset"""
        try:
            if asset not in self.return_history:
                return []

            returns = list(self.return_history[asset])
            return returns[-periods:] if len(returns) >= periods else returns

        except Exception as e:
            self.logger.error(f"❌ Failed to get returns for {asset}: {e}")
            return []

    async def _align_return_data(self, returns1: List[Tuple[datetime, float]],
                                returns2: List[Tuple[datetime, float]]) -> List[Tuple[datetime, float, float]]:
        """Align return data by timestamp"""
        try:
            # Create dictionaries for quick lookup
            returns1_dict = {timestamp: value for timestamp, value in returns1}
            returns2_dict = {timestamp: value for timestamp, value in returns2}

            # Find common timestamps
            common_timestamps = set(returns1_dict.keys()) & set(returns2_dict.keys())

            # Create aligned data
            aligned = [(ts, returns1_dict[ts], returns2_dict[ts])
                      for ts in sorted(common_timestamps)]

            return aligned

        except Exception as e:
            self.logger.error(f"❌ Failed to align return data: {e}")
            return []

    async def _analyze_dxy_impact(self, asset: str) -> Dict[str, float]:
        """Analyze DXY impact on the asset"""
        try:
            dxy_impact = {}

            # Get DXY correlation if available
            if 'DXY' in self.monitored_assets:
                dxy_correlation = await self._calculate_correlation(asset, 'DXY')
                if dxy_correlation:
                    dxy_impact['correlation'] = dxy_correlation.correlation
                    dxy_impact['strength'] = abs(dxy_correlation.correlation)
                else:
                    # Use theoretical DXY factor
                    theoretical_factor = self.dxy_factors.get(asset, 0.0)
                    dxy_impact['correlation'] = theoretical_factor
                    dxy_impact['strength'] = abs(theoretical_factor)

            # Calculate expected impact
            dxy_sensitivity = self.asset_profiles.get(asset, {}).get('dxy_sensitivity', 0.0)
            dxy_impact['sensitivity'] = dxy_sensitivity

            # Risk assessment
            if abs(dxy_impact.get('correlation', 0)) > 0.7:
                dxy_impact['risk_level'] = 'high'
            elif abs(dxy_impact.get('correlation', 0)) > 0.4:
                dxy_impact['risk_level'] = 'medium'
            else:
                dxy_impact['risk_level'] = 'low'

            return dxy_impact

        except Exception as e:
            self.logger.error(f"❌ DXY impact analysis failed for {asset}: {e}")
            return {'correlation': 0.0, 'strength': 0.0, 'sensitivity': 0.0, 'risk_level': 'unknown'}

    async def _assess_correlation_risk(self, primary_asset: str,
                                     correlations: Dict[str, CorrelationData]) -> Dict[str, Any]:
        """Assess correlation-based risk"""
        try:
            risk_assessment = {
                'overall_risk': 'low',
                'high_correlation_count': 0,
                'max_correlation': 0.0,
                'risk_factors': []
            }

            if not correlations:
                return risk_assessment

            # Analyze correlations
            high_corr_count = 0
            max_corr = 0.0

            for asset, corr_data in correlations.items():
                abs_corr = abs(corr_data.correlation)
                max_corr = max(max_corr, abs_corr)

                if abs_corr > 0.8:
                    high_corr_count += 1
                    risk_assessment['risk_factors'].append(f"High correlation with {asset} ({abs_corr:.2f})")

            risk_assessment['high_correlation_count'] = high_corr_count
            risk_assessment['max_correlation'] = max_corr

            # Determine overall risk
            if high_corr_count >= 3 or max_corr > 0.9:
                risk_assessment['overall_risk'] = 'high'
            elif high_corr_count >= 2 or max_corr > 0.7:
                risk_assessment['overall_risk'] = 'medium'
            else:
                risk_assessment['overall_risk'] = 'low'

            return risk_assessment

        except Exception as e:
            self.logger.error(f"❌ Correlation risk assessment failed: {e}")
            return {'overall_risk': 'unknown', 'high_correlation_count': 0, 'max_correlation': 0.0, 'risk_factors': []}

    async def _analyze_safe_haven_flows(self, asset: str) -> Dict[str, float]:
        """Analyze safe haven flows (particularly relevant for gold)"""
        try:
            safe_haven_flows = {}

            # Get asset profile
            asset_profile = self.asset_profiles.get(asset, {})
            safe_haven_score = asset_profile.get('safe_haven_score', 0.0)

            safe_haven_flows['safe_haven_score'] = safe_haven_score

            # Analyze flows based on correlations with risk assets
            risk_assets = ['SPX', 'VIX', 'US10Y']  # Stock index, volatility, bonds
            risk_correlations = []

            for risk_asset in risk_assets:
                if risk_asset in self.monitored_assets:
                    correlation = await self._calculate_correlation(asset, risk_asset)
                    if correlation:
                        risk_correlations.append(correlation.correlation)

            if risk_correlations:
                avg_risk_correlation = np.mean(risk_correlations)
                safe_haven_flows['risk_asset_correlation'] = avg_risk_correlation

                # Safe haven flow strength (negative correlation with risk assets)
                if avg_risk_correlation < -0.5:
                    safe_haven_flows['flow_strength'] = 'strong'
                elif avg_risk_correlation < -0.2:
                    safe_haven_flows['flow_strength'] = 'moderate'
                else:
                    safe_haven_flows['flow_strength'] = 'weak'
            else:
                safe_haven_flows['risk_asset_correlation'] = 0.0
                safe_haven_flows['flow_strength'] = 'unknown'

            return safe_haven_flows

        except Exception as e:
            self.logger.error(f"❌ Safe haven flow analysis failed for {asset}: {e}")
            return {'safe_haven_score': 0.0, 'risk_asset_correlation': 0.0, 'flow_strength': 'unknown'}

    async def _identify_correlation_clusters(self, primary_asset: str,
                                           correlations: Dict[str, CorrelationData]) -> List[List[str]]:
        """Identify assets that are highly correlated (correlation clusters)"""
        try:
            clusters = []

            # Group assets by correlation strength with primary asset
            high_corr_assets = []
            medium_corr_assets = []

            for asset, corr_data in correlations.items():
                abs_corr = abs(corr_data.correlation)
                if abs_corr > 0.7:
                    high_corr_assets.append(asset)
                elif abs_corr > 0.4:
                    medium_corr_assets.append(asset)

            # Create clusters
            if high_corr_assets:
                clusters.append([primary_asset] + high_corr_assets)

            if medium_corr_assets:
                clusters.append(medium_corr_assets)

            return clusters

        except Exception as e:
            self.logger.error(f"❌ Correlation cluster identification failed: {e}")
            return []

    async def _calculate_diversification_score(self, correlations: Dict[str, CorrelationData]) -> float:
        """Calculate portfolio diversification score based on correlations"""
        try:
            if not correlations:
                return 1.0  # Perfect diversification if no correlations

            # Calculate average absolute correlation
            abs_correlations = [abs(corr_data.correlation) for corr_data in correlations.values()]
            avg_abs_correlation = np.mean(abs_correlations)

            # Diversification score (inverse of correlation)
            diversification_score = 1.0 - avg_abs_correlation

            # Ensure score is between 0 and 1
            diversification_score = max(0.0, min(1.0, diversification_score))

            return diversification_score

        except Exception as e:
            self.logger.error(f"❌ Diversification score calculation failed: {e}")
            return 0.5

    async def _invalidate_correlation_cache(self, asset: str) -> None:
        """Invalidate correlation cache entries related to an asset"""
        try:
            keys_to_remove = []
            for key in self.correlation_cache.keys():
                if asset in key:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self.correlation_cache[key]
                if key in self.cache_expiry:
                    del self.cache_expiry[key]

        except Exception as e:
            self.logger.error(f"❌ Failed to invalidate correlation cache: {e}")

    def _initialize_asset_profiles(self) -> Dict[str, AssetProfile]:
        """Initialize asset profiles with characteristics"""
        profiles = {}

        # Gold
        profiles['XAUUSD'] = AssetProfile(
            symbol='XAUUSD',
            asset_class=AssetClass.PRECIOUS_METAL,
            base_currency='XAU',
            quote_currency='USD',
            dxy_sensitivity=-0.8,
            safe_haven_score=0.9,
            volatility_profile='medium'
        )

        # Major forex pairs
        profiles['EURUSD'] = AssetProfile(
            symbol='EURUSD',
            asset_class=AssetClass.MAJOR_CURRENCY,
            base_currency='EUR',
            quote_currency='USD',
            dxy_sensitivity=-0.7,
            safe_haven_score=0.3,
            volatility_profile='medium'
        )

        profiles['GBPUSD'] = AssetProfile(
            symbol='GBPUSD',
            asset_class=AssetClass.MAJOR_CURRENCY,
            base_currency='GBP',
            quote_currency='USD',
            dxy_sensitivity=-0.6,
            safe_haven_score=0.2,
            volatility_profile='high'
        )

        profiles['USDJPY'] = AssetProfile(
            symbol='USDJPY',
            asset_class=AssetClass.MAJOR_CURRENCY,
            base_currency='USD',
            quote_currency='JPY',
            dxy_sensitivity=0.7,
            safe_haven_score=0.4,
            volatility_profile='medium'
        )

        # Commodity currencies
        profiles['AUDUSD'] = AssetProfile(
            symbol='AUDUSD',
            asset_class=AssetClass.COMMODITY_CURRENCY,
            base_currency='AUD',
            quote_currency='USD',
            dxy_sensitivity=-0.5,
            safe_haven_score=0.1,
            volatility_profile='high'
        )

        profiles['USDCAD'] = AssetProfile(
            symbol='USDCAD',
            asset_class=AssetClass.COMMODITY_CURRENCY,
            base_currency='USD',
            quote_currency='CAD',
            dxy_sensitivity=0.6,
            safe_haven_score=0.3,
            volatility_profile='medium'
        )

        profiles['NZDUSD'] = AssetProfile(
            symbol='NZDUSD',
            asset_class=AssetClass.COMMODITY_CURRENCY,
            base_currency='NZD',
            quote_currency='USD',
            dxy_sensitivity=-0.5,
            safe_haven_score=0.1,
            volatility_profile='high'
        )

        # Dollar Index
        profiles['DXY'] = AssetProfile(
            symbol='DXY',
            asset_class=AssetClass.INDEX,
            base_currency='USD',
            quote_currency='BASKET',
            dxy_sensitivity=1.0,
            safe_haven_score=0.6,
            volatility_profile='medium'
        )

        return profiles

    async def _fallback_correlation_analysis(self, primary_asset: str) -> Dict[str, Any]:
        """Fallback correlation analysis when main analysis fails"""
        return {
            'correlations': {},
            'dxy_impact': {'correlation': 0.0, 'strength': 0.0, 'sensitivity': 0.0, 'risk_level': 'unknown'},
            'risk_assessment': {'overall_risk': 'unknown', 'high_correlation_count': 0, 'max_correlation': 0.0, 'risk_factors': []},
            'safe_haven_flows': {'safe_haven_score': 0.0, 'risk_asset_correlation': 0.0, 'flow_strength': 'unknown'},
            'diversification_score': 0.5,
            'correlation_clusters': []
        }

    async def get_status(self) -> Dict[str, Any]:
        """Get correlation engine status"""
        try:
            status = {
                'monitored_assets': len(self.monitored_assets),
                'assets_with_data': len([asset for asset in self.monitored_assets
                                       if len(self.price_history[asset]) > 0]),
                'cache_size': len(self.correlation_cache),
                'total_price_points': sum(len(hist) for hist in self.price_history.values()),
                'total_return_points': sum(len(hist) for hist in self.return_history.values())
            }

            # Asset status
            asset_status = {}
            for asset in self.monitored_assets:
                asset_status[asset] = {
                    'price_points': len(self.price_history[asset]),
                    'return_points': len(self.return_history[asset]),
                    'last_update': self.price_history[asset][-1][0].isoformat() if self.price_history[asset] else None
                }

            status['asset_status'] = asset_status

            return status

        except Exception as e:
            self.logger.error(f"❌ Failed to get correlation engine status: {e}")
            return {'error': str(e)}


# Export main components
__all__ = [
    'MultiAssetCorrelationEngine',
    'CorrelationData',
    'AssetProfile',
    'CorrelationAnalysis',
    'AssetClass'
]