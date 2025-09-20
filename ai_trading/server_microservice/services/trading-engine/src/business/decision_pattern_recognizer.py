"""
🔍 Decision Pattern Recognition System
Continuous improvement through systematic pattern analysis and learning from decision outcomes

FEATURES:
- Advanced pattern recognition using statistical and machine learning methods
- Multi-dimensional pattern analysis across decision attributes
- Automated pattern discovery and classification
- Continuous learning from decision outcomes
- Pattern-based recommendation system
- Integration with AI Brain methodology for systematic improvement

PATTERN CATEGORIES:
1. Success Patterns - Identify characteristics of successful decisions
2. Failure Patterns - Recognize patterns leading to poor outcomes  
3. Market Condition Patterns - Market-specific decision patterns
4. Strategy Performance Patterns - Strategy effectiveness patterns
5. Confidence Calibration Patterns - Confidence vs outcome patterns
6. Risk Management Patterns - Risk-return optimization patterns
7. Temporal Patterns - Time-based decision performance patterns
8. Correlation Patterns - Inter-market relationship patterns

PATTERN RECOGNITION METHODS:
- Statistical Pattern Analysis - Correlation and regression analysis
- Clustering Analysis - Unsupervised pattern discovery
- Classification Models - Supervised pattern learning
- Time Series Analysis - Temporal pattern recognition
- Association Rule Mining - Decision rule discovery
- Anomaly Detection - Outlier pattern identification
"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque, Counter
import statistics
import json
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')

# Local components
from ....shared.infrastructure.core.logger_core import CoreLogger
from ....shared.infrastructure.core.cache_core import CoreCache

# Initialize components
logger = CoreLogger("trading-engine", "pattern-recognizer")
cache = CoreCache("decision-patterns", max_size=3000, default_ttl=7200)


class PatternType(Enum):
    """Types of decision patterns"""
    SUCCESS_PATTERN = "success_pattern"
    FAILURE_PATTERN = "failure_pattern"
    MARKET_CONDITION_PATTERN = "market_condition_pattern"
    STRATEGY_PERFORMANCE_PATTERN = "strategy_performance_pattern"
    CONFIDENCE_CALIBRATION_PATTERN = "confidence_calibration_pattern"
    RISK_MANAGEMENT_PATTERN = "risk_management_pattern"
    TEMPORAL_PATTERN = "temporal_pattern"
    CORRELATION_PATTERN = "correlation_pattern"
    ANOMALY_PATTERN = "anomaly_pattern"


class PatternConfidence(Enum):
    """Confidence levels for pattern recognition"""
    LOW = "low"          # 50-65% confidence
    MEDIUM = "medium"    # 65-80% confidence
    HIGH = "high"        # 80-95% confidence
    VERY_HIGH = "very_high"  # 95%+ confidence


class PatternImpact(Enum):
    """Impact levels of recognized patterns"""
    MINOR = "minor"      # < 2% impact on outcomes
    MODERATE = "moderate"  # 2-5% impact
    SIGNIFICANT = "significant"  # 5-10% impact
    MAJOR = "major"      # 10%+ impact


@dataclass
class DecisionDataPoint:
    """Individual decision data point for pattern analysis"""
    decision_id: str
    timestamp: datetime
    
    # Decision attributes
    symbol: str
    action: str
    confidence: float
    position_size: float
    risk_per_trade: float
    
    # Context attributes
    market_volatility: float
    market_trend: str
    liquidity: float
    strategy_id: Optional[str]
    
    # Outcome attributes
    success: Optional[bool] = None
    pnl: Optional[float] = None
    execution_quality: Optional[float] = None
    holding_period_minutes: Optional[float] = None
    
    # Derived attributes
    hour_of_day: int = 0
    day_of_week: int = 0
    volatility_regime: str = "normal"
    
    def __post_init__(self):
        self.hour_of_day = self.timestamp.hour
        self.day_of_week = self.timestamp.weekday()
        
        if self.market_volatility > 0.8:
            self.volatility_regime = "high"
        elif self.market_volatility < 0.3:
            self.volatility_regime = "low"
        else:
            self.volatility_regime = "normal"


@dataclass
class RecognizedPattern:
    """A recognized decision pattern"""
    pattern_id: str
    pattern_type: PatternType
    pattern_name: str
    description: str
    
    # Pattern characteristics
    pattern_attributes: Dict[str, Any]
    pattern_rules: List[str]
    
    # Pattern metrics
    confidence: PatternConfidence
    impact: PatternImpact
    support_count: int  # Number of decisions supporting this pattern
    success_rate: float
    avg_improvement: float
    
    # Temporal information
    discovered_at: datetime
    last_updated: datetime
    
    # Pattern validation
    validation_score: float
    statistical_significance: float
    
    # Recommendations
    pattern_recommendations: List[str]
    optimization_suggestions: List[str]
    
    # Metadata
    pattern_details: Dict[str, Any] = None
    
    def __post_init__(self):
        if not self.pattern_details:
            self.pattern_details = {}


@dataclass
class PatternAnalysisResult:
    """Result of pattern analysis"""
    analysis_id: str
    analysis_timestamp: datetime
    
    # Discovered patterns
    new_patterns: List[RecognizedPattern]
    updated_patterns: List[RecognizedPattern]
    deprecated_patterns: List[str]  # Pattern IDs that are no longer valid
    
    # Analysis metrics
    total_patterns_analyzed: int
    pattern_discovery_rate: float
    pattern_validation_accuracy: float
    
    # Data quality
    data_points_analyzed: int
    data_quality_score: float
    temporal_coverage_days: int
    
    # Insights and recommendations
    key_insights: List[str]
    improvement_recommendations: List[str]
    pattern_based_optimizations: List[str]
    
    # Statistical summary
    analysis_statistics: Dict[str, Any]


class DecisionPatternRecognizer:
    """
    Advanced decision pattern recognition system
    Implements continuous learning from decision outcomes
    """
    
    def __init__(self):
        """Initialize decision pattern recognizer"""
        
        # Pattern storage
        self.recognized_patterns: Dict[str, RecognizedPattern] = {}
        self.decision_data: deque = deque(maxlen=5000)  # Recent decisions
        
        # Pattern analysis configuration
        self.analysis_config = {
            "min_pattern_support": 10,      # Minimum decisions to form a pattern
            "min_confidence_threshold": 0.65,  # Minimum pattern confidence
            "min_improvement_threshold": 0.02,  # Minimum 2% improvement
            "pattern_update_frequency_hours": 6,  # Update patterns every 6 hours
            "clustering_eps": 0.3,          # DBSCAN clustering parameter
            "clustering_min_samples": 5      # Minimum samples per cluster
        }\n        \n        # Feature extraction configuration\n        self.feature_extractors = {\n            \"decision_features\": [\"confidence\", \"position_size\", \"risk_per_trade\"],\n            \"market_features\": [\"market_volatility\", \"liquidity\"],\n            \"temporal_features\": [\"hour_of_day\", \"day_of_week\"],\n            \"outcome_features\": [\"pnl\", \"execution_quality\", \"holding_period_minutes\"]\n        }\n        \n        # Pattern discovery algorithms\n        self.clustering_models = {\n            \"kmeans\": None,\n            \"dbscan\": None,\n            \"scaler\": StandardScaler()\n        }\n        \n        # Pattern performance tracking\n        self.pattern_performance = defaultdict(lambda: {\n            \"predictions_made\": 0,\n            \"correct_predictions\": 0,\n            \"accuracy\": 0.0,\n            \"last_updated\": datetime.now()\n        })\n        \n        # Analysis statistics\n        self.analysis_statistics = {\n            \"total_analyses_performed\": 0,\n            \"patterns_discovered\": 0,\n            \"patterns_validated\": 0,\n            \"patterns_deprecated\": 0,\n            \"average_pattern_accuracy\": 0.0,\n            \"last_analysis_time\": None,\n            \"data_quality_trend\": \"stable\"\n        }\n        \n        logger.info(\"Decision Pattern Recognizer initialized with advanced ML capabilities\")\n    \n    async def add_decision_data(\n        self,\n        decision_id: str,\n        decision_attributes: Dict[str, Any],\n        market_context: Dict[str, Any],\n        outcome_data: Optional[Dict[str, Any]] = None\n    ):\n        \"\"\"\n        Add decision data for pattern analysis\n        \n        Args:\n            decision_id: Unique decision identifier\n            decision_attributes: Decision characteristics\n            market_context: Market conditions at decision time\n            outcome_data: Decision outcomes (if available)\n        \"\"\"\n        \n        try:\n            # Create data point\n            data_point = DecisionDataPoint(\n                decision_id=decision_id,\n                timestamp=datetime.now(),\n                symbol=decision_attributes.get(\"symbol\", \"UNKNOWN\"),\n                action=decision_attributes.get(\"action\", \"hold\"),\n                confidence=decision_attributes.get(\"confidence\", 0.5),\n                position_size=decision_attributes.get(\"position_size\", 0.0),\n                risk_per_trade=decision_attributes.get(\"risk_per_trade\", 0.02),\n                market_volatility=market_context.get(\"volatility\", 0.5),\n                market_trend=market_context.get(\"trend\", \"neutral\"),\n                liquidity=market_context.get(\"liquidity\", 0.7),\n                strategy_id=decision_attributes.get(\"strategy_id\")\n            )\n            \n            # Add outcome data if available\n            if outcome_data:\n                data_point.success = outcome_data.get(\"success\", None)\n                data_point.pnl = outcome_data.get(\"pnl\", None)\n                data_point.execution_quality = outcome_data.get(\"execution_quality\", None)\n                data_point.holding_period_minutes = outcome_data.get(\"holding_period_minutes\", None)\n            \n            # Store data point\n            self.decision_data.append(data_point)\n            \n            # Cache for quick access\n            await cache.set(f\"decision_data:{decision_id}\", asdict(data_point), ttl=86400)\n            \n            logger.debug(f\"Decision data added: {decision_id}\")\n            \n            # Trigger pattern analysis if enough new data\n            if len(self.decision_data) % 50 == 0:  # Analyze every 50 decisions\n                await self._trigger_pattern_analysis()\n            \n        except Exception as e:\n            logger.error(f\"Failed to add decision data: {e}\")\n    \n    async def update_decision_outcome(\n        self,\n        decision_id: str,\n        outcome_data: Dict[str, Any]\n    ):\n        \"\"\"\n        Update decision outcome for pattern learning\n        \n        Args:\n            decision_id: Decision identifier\n            outcome_data: Actual outcome data\n        \"\"\"\n        \n        try:\n            # Find decision data point\n            data_point = None\n            for dp in self.decision_data:\n                if dp.decision_id == decision_id:\n                    data_point = dp\n                    break\n            \n            if data_point:\n                # Update outcome data\n                data_point.success = outcome_data.get(\"success\")\n                data_point.pnl = outcome_data.get(\"pnl\")\n                data_point.execution_quality = outcome_data.get(\"execution_quality\")\n                data_point.holding_period_minutes = outcome_data.get(\"holding_period_minutes\")\n                \n                # Update cache\n                await cache.set(f\"decision_data:{decision_id}\", asdict(data_point), ttl=86400)\n                \n                logger.debug(f\"Decision outcome updated: {decision_id}\")\n                \n                # Validate existing patterns with new outcome\n                await self._validate_patterns_with_outcome(data_point)\n            else:\n                logger.warning(f\"Decision data not found for outcome update: {decision_id}\")\n            \n        except Exception as e:\n            logger.error(f\"Failed to update decision outcome: {e}\")\n    \n    async def analyze_patterns(\n        self,\n        force_analysis: bool = False\n    ) -> PatternAnalysisResult:\n        \"\"\"\n        Perform comprehensive pattern analysis\n        \n        Args:\n            force_analysis: Force analysis even if not enough time has passed\n            \n        Returns:\n            Pattern analysis results\n        \"\"\"\n        \n        try:\n            analysis_id = f\"analysis_{int(datetime.now().timestamp() * 1000)}\"\n            \n            logger.info(f\"\ud83d\udd0d Starting pattern analysis: {analysis_id}\")\n            \n            # Check if analysis is needed\n            if not force_analysis:\n                last_analysis = self.analysis_statistics.get(\"last_analysis_time\")\n                if last_analysis:\n                    time_since_analysis = datetime.now() - last_analysis\n                    if time_since_analysis < timedelta(hours=self.analysis_config[\"pattern_update_frequency_hours\"]):\n                        logger.info(\"Pattern analysis skipped - too recent\")\n                        return self._create_empty_analysis_result(analysis_id)\n            \n            # Prepare data for analysis\n            analysis_data = await self._prepare_analysis_data()\n            \n            if len(analysis_data) < self.analysis_config[\"min_pattern_support\"]:\n                logger.warning(f\"Insufficient data for pattern analysis: {len(analysis_data)} decisions\")\n                return self._create_empty_analysis_result(analysis_id)\n            \n            # Perform pattern discovery\n            new_patterns = await self._discover_patterns(analysis_data)\n            \n            # Update existing patterns\n            updated_patterns = await self._update_existing_patterns(analysis_data)\n            \n            # Validate pattern significance\n            validated_patterns = await self._validate_pattern_significance(new_patterns + updated_patterns)\n            \n            # Identify deprecated patterns\n            deprecated_patterns = await self._identify_deprecated_patterns(analysis_data)\n            \n            # Generate insights and recommendations\n            insights = await self._generate_pattern_insights(validated_patterns, analysis_data)\n            \n            # Create analysis result\n            analysis_result = PatternAnalysisResult(\n                analysis_id=analysis_id,\n                analysis_timestamp=datetime.now(),\n                new_patterns=[p for p in validated_patterns if p.pattern_id not in self.recognized_patterns],\n                updated_patterns=[p for p in validated_patterns if p.pattern_id in self.recognized_patterns],\n                deprecated_patterns=deprecated_patterns,\n                total_patterns_analyzed=len(validated_patterns),\n                pattern_discovery_rate=len(new_patterns) / max(1, len(analysis_data)),\n                pattern_validation_accuracy=await self._calculate_validation_accuracy(),\n                data_points_analyzed=len(analysis_data),\n                data_quality_score=self._calculate_data_quality_score(analysis_data),\n                temporal_coverage_days=self._calculate_temporal_coverage(analysis_data),\n                key_insights=insights[\"insights\"],\n                improvement_recommendations=insights[\"recommendations\"],\n                pattern_based_optimizations=insights[\"optimizations\"],\n                analysis_statistics=self._generate_analysis_statistics(analysis_data, validated_patterns)\n            )\n            \n            # Update pattern storage\n            await self._update_pattern_storage(validated_patterns, deprecated_patterns)\n            \n            # Update analysis statistics\n            self._update_analysis_statistics(analysis_result)\n            \n            logger.info(f\"\u2705 Pattern analysis completed: {analysis_id} - {len(validated_patterns)} patterns\")\n            \n            return analysis_result\n            \n        except Exception as e:\n            logger.error(f\"\u274c Pattern analysis failed: {e}\")\n            return self._create_error_analysis_result(analysis_id, str(e))\n    \n    async def _prepare_analysis_data(self) -> List[DecisionDataPoint]:\n        \"\"\"Prepare data for pattern analysis\"\"\"\n        \n        try:\n            # Filter data points with complete information\n            complete_data = [\n                dp for dp in self.decision_data\n                if dp.success is not None and dp.pnl is not None\n            ]\n            \n            # Sort by timestamp\n            complete_data.sort(key=lambda x: x.timestamp)\n            \n            return complete_data\n            \n        except Exception as e:\n            logger.error(f\"Data preparation failed: {e}\")\n            return []\n    \n    async def _discover_patterns(self, data: List[DecisionDataPoint]) -> List[RecognizedPattern]:\n        \"\"\"Discover new patterns using machine learning\"\"\"\n        \n        patterns = []\n        \n        try:\n            if len(data) < self.analysis_config[\"min_pattern_support\"]:\n                return patterns\n            \n            # Extract features for clustering\n            features = self._extract_features(data)\n            \n            if len(features) == 0:\n                return patterns\n            \n            # Standardize features\n            scaled_features = self.clustering_models[\"scaler\"].fit_transform(features)\n            \n            # Perform clustering analysis\n            clusters = await self._perform_clustering(scaled_features)\n            \n            # Analyze each cluster for patterns\n            for cluster_id, cluster_indices in clusters.items():\n                if len(cluster_indices) >= self.analysis_config[\"min_pattern_support\"]:\n                    cluster_data = [data[i] for i in cluster_indices]\n                    pattern = await self._analyze_cluster_pattern(cluster_id, cluster_data)\n                    \n                    if pattern:\n                        patterns.append(pattern)\n            \n            # Discover temporal patterns\n            temporal_patterns = await self._discover_temporal_patterns(data)\n            patterns.extend(temporal_patterns)\n            \n            # Discover market condition patterns\n            market_patterns = await self._discover_market_condition_patterns(data)\n            patterns.extend(market_patterns)\n            \n            return patterns\n            \n        except Exception as e:\n            logger.error(f\"Pattern discovery failed: {e}\")\n            return []\n    \n    def _extract_features(self, data: List[DecisionDataPoint]) -> np.ndarray:\n        \"\"\"Extract features for pattern analysis\"\"\"\n        \n        try:\n            features = []\n            \n            for dp in data:\n                feature_vector = [\n                    dp.confidence,\n                    dp.position_size,\n                    dp.risk_per_trade,\n                    dp.market_volatility,\n                    dp.liquidity,\n                    dp.hour_of_day / 24.0,  # Normalize hour\n                    dp.day_of_week / 6.0,   # Normalize day\n                    1.0 if dp.action == \"buy\" else 0.0 if dp.action == \"sell\" else 0.5,\n                    1.0 if dp.market_trend == \"uptrend\" else 0.0 if dp.market_trend == \"downtrend\" else 0.5,\n                    1.0 if dp.volatility_regime == \"high\" else 0.0 if dp.volatility_regime == \"low\" else 0.5\n                ]\n                \n                # Add outcome features if available\n                if dp.success is not None:\n                    feature_vector.append(1.0 if dp.success else 0.0)\n                if dp.pnl is not None:\n                    feature_vector.append(min(1.0, max(-1.0, dp.pnl / 0.1)))  # Normalize PnL\n                if dp.execution_quality is not None:\n                    feature_vector.append(dp.execution_quality)\n                \n                features.append(feature_vector)\n            \n            return np.array(features)\n            \n        except Exception as e:\n            logger.error(f\"Feature extraction failed: {e}\")\n            return np.array([])\n    \n    async def _perform_clustering(self, features: np.ndarray) -> Dict[int, List[int]]:\n        \"\"\"Perform clustering to discover pattern groups\"\"\"\n        \n        clusters = {}\n        \n        try:\n            # DBSCAN clustering for anomaly detection\n            dbscan = DBSCAN(\n                eps=self.analysis_config[\"clustering_eps\"],\n                min_samples=self.analysis_config[\"clustering_min_samples\"]\n            )\n            dbscan_labels = dbscan.fit_predict(features)\n            \n            # Group indices by cluster\n            for idx, label in enumerate(dbscan_labels):\n                if label != -1:  # Ignore noise points\n                    if label not in clusters:\n                        clusters[label] = []\n                    clusters[label].append(idx)\n            \n            # K-means clustering for additional pattern discovery\n            if len(features) >= 20:  # Need sufficient data for K-means\n                n_clusters = min(8, max(2, len(features) // 10))  # Adaptive cluster count\n                \n                kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)\n                kmeans_labels = kmeans.fit_predict(features)\n                \n                # Add K-means clusters (with offset to avoid collision with DBSCAN)\n                max_dbscan_label = max(clusters.keys()) if clusters else -1\n                \n                for idx, label in enumerate(kmeans_labels):\n                    cluster_id = max_dbscan_label + 1 + label\n                    if cluster_id not in clusters:\n                        clusters[cluster_id] = []\n                    clusters[cluster_id].append(idx)\n            \n            return clusters\n            \n        except Exception as e:\n            logger.error(f\"Clustering failed: {e}\")\n            return {}\n    \n    async def _analyze_cluster_pattern(\n        self,\n        cluster_id: int,\n        cluster_data: List[DecisionDataPoint]\n    ) -> Optional[RecognizedPattern]:\n        \"\"\"Analyze a cluster to identify patterns\"\"\"\n        \n        try:\n            if len(cluster_data) < self.analysis_config[\"min_pattern_support\"]:\n                return None\n            \n            # Calculate cluster statistics\n            success_rate = statistics.mean([1 if dp.success else 0 for dp in cluster_data if dp.success is not None])\n            avg_confidence = statistics.mean([dp.confidence for dp in cluster_data])\n            avg_pnl = statistics.mean([dp.pnl for dp in cluster_data if dp.pnl is not None])\n            \n            # Only create pattern if it shows improvement\n            if success_rate < 0.5 and avg_pnl <= 0:\n                # This might be a failure pattern\n                pattern_type = PatternType.FAILURE_PATTERN\n                improvement = -(success_rate - 0.5)  # Negative improvement for failure patterns\n            elif success_rate > 0.6 or avg_pnl > 0.02:\n                # This is a success pattern\n                pattern_type = PatternType.SUCCESS_PATTERN\n                improvement = max(success_rate - 0.5, avg_pnl * 10)  # Convert to percentage\n            else:\n                return None  # Not significant enough\n            \n            # Check minimum improvement threshold\n            if abs(improvement) < self.analysis_config[\"min_improvement_threshold\"]:\n                return None\n            \n            # Identify pattern attributes\n            pattern_attributes = self._identify_cluster_attributes(cluster_data)\n            \n            # Generate pattern rules\n            pattern_rules = self._generate_pattern_rules(cluster_data, pattern_attributes)\n            \n            # Determine confidence level\n            confidence_level = self._determine_confidence_level(success_rate, len(cluster_data))\n            \n            # Determine impact level\n            impact_level = self._determine_impact_level(improvement)\n            \n            # Create pattern\n            pattern = RecognizedPattern(\n                pattern_id=f\"cluster_{cluster_id}_{int(datetime.now().timestamp())}\",\n                pattern_type=pattern_type,\n                pattern_name=f\"Cluster {cluster_id} {pattern_type.value.replace('_', ' ').title()}\",\n                description=self._generate_pattern_description(pattern_attributes, success_rate, improvement),\n                pattern_attributes=pattern_attributes,\n                pattern_rules=pattern_rules,\n                confidence=confidence_level,\n                impact=impact_level,\n                support_count=len(cluster_data),\n                success_rate=success_rate,\n                avg_improvement=improvement,\n                discovered_at=datetime.now(),\n                last_updated=datetime.now(),\n                validation_score=self._calculate_pattern_validation_score(cluster_data),\n                statistical_significance=self._calculate_statistical_significance(cluster_data),\n                pattern_recommendations=self._generate_pattern_recommendations(pattern_type, pattern_attributes),\n                optimization_suggestions=self._generate_optimization_suggestions(pattern_attributes, improvement)\n            )\n            \n            return pattern\n            \n        except Exception as e:\n            logger.error(f\"Cluster pattern analysis failed: {e}\")\n            return None\n    \n    def _identify_cluster_attributes(self, cluster_data: List[DecisionDataPoint]) -> Dict[str, Any]:\n        \"\"\"Identify key attributes of a cluster\"\"\"\n        \n        attributes = {}\n        \n        try:\n            # Confidence range\n            confidences = [dp.confidence for dp in cluster_data]\n            attributes[\"confidence_range\"] = {\n                \"min\": min(confidences),\n                \"max\": max(confidences),\n                \"mean\": statistics.mean(confidences),\n                \"std\": statistics.stdev(confidences) if len(confidences) > 1 else 0\n            }\n            \n            # Common actions\n            actions = [dp.action for dp in cluster_data]\n            action_counts = Counter(actions)\n            attributes[\"primary_action\"] = action_counts.most_common(1)[0][0]\n            attributes[\"action_distribution\"] = dict(action_counts)\n            \n            # Market conditions\n            volatilities = [dp.market_volatility for dp in cluster_data]\n            attributes[\"volatility_range\"] = {\n                \"min\": min(volatilities),\n                \"max\": max(volatilities),\n                \"mean\": statistics.mean(volatilities)\n            }\n            \n            # Temporal patterns\n            hours = [dp.hour_of_day for dp in cluster_data]\n            hour_counts = Counter(hours)\n            attributes[\"common_hours\"] = [hour for hour, count in hour_counts.most_common(3)]\n            \n            # Strategy patterns\n            strategies = [dp.strategy_id for dp in cluster_data if dp.strategy_id]\n            if strategies:\n                strategy_counts = Counter(strategies)\n                attributes[\"primary_strategies\"] = dict(strategy_counts.most_common(3))\n            \n            # Risk patterns\n            risks = [dp.risk_per_trade for dp in cluster_data]\n            attributes[\"risk_range\"] = {\n                \"min\": min(risks),\n                \"max\": max(risks),\n                \"mean\": statistics.mean(risks)\n            }\n            \n            return attributes\n            \n        except Exception as e:\n            logger.error(f\"Cluster attribute identification failed: {e}\")\n            return {}\n    \n    def _generate_pattern_rules(self, cluster_data: List[DecisionDataPoint], attributes: Dict[str, Any]) -> List[str]:\n        \"\"\"Generate human-readable pattern rules\"\"\"\n        \n        rules = []\n        \n        try:\n            # Confidence rules\n            conf_range = attributes.get(\"confidence_range\", {})\n            if conf_range:\n                rules.append(f\"Confidence between {conf_range['min']:.2f} and {conf_range['max']:.2f}\")\n            \n            # Action rules\n            primary_action = attributes.get(\"primary_action\")\n            if primary_action:\n                rules.append(f\"Primary action: {primary_action}\")\n            \n            # Market condition rules\n            vol_range = attributes.get(\"volatility_range\", {})\n            if vol_range:\n                if vol_range[\"mean\"] > 0.7:\n                    rules.append(\"High volatility market conditions\")\n                elif vol_range[\"mean\"] < 0.3:\n                    rules.append(\"Low volatility market conditions\")\n                else:\n                    rules.append(\"Normal volatility market conditions\")\n            \n            # Temporal rules\n            common_hours = attributes.get(\"common_hours\", [])\n            if common_hours:\n                rules.append(f\"Most common trading hours: {', '.join(map(str, common_hours))}\")\n            \n            # Strategy rules\n            strategies = attributes.get(\"primary_strategies\", {})\n            if strategies:\n                top_strategy = max(strategies.items(), key=lambda x: x[1])[0]\n                rules.append(f\"Most effective strategy: {top_strategy}\")\n            \n            # Risk rules\n            risk_range = attributes.get(\"risk_range\", {})\n            if risk_range:\n                rules.append(f\"Risk per trade: {risk_range['min']:.3f} to {risk_range['max']:.3f}\")\n            \n            return rules\n            \n        except Exception as e:\n            logger.error(f\"Pattern rule generation failed: {e}\")\n            return []\n    \n    def _determine_confidence_level(self, success_rate: float, sample_size: int) -> PatternConfidence:\n        \"\"\"Determine confidence level for pattern\"\"\"\n        \n        # Base confidence on success rate and sample size\n        base_confidence = success_rate\n        \n        # Adjust for sample size (more samples = higher confidence)\n        size_adjustment = min(0.2, sample_size / 100)  # Up to 20% boost for large samples\n        adjusted_confidence = base_confidence + size_adjustment\n        \n        # Classify confidence level\n        if adjusted_confidence >= 0.95:\n            return PatternConfidence.VERY_HIGH\n        elif adjusted_confidence >= 0.80:\n            return PatternConfidence.HIGH\n        elif adjusted_confidence >= 0.65:\n            return PatternConfidence.MEDIUM\n        else:\n            return PatternConfidence.LOW\n    \n    def _determine_impact_level(self, improvement: float) -> PatternImpact:\n        \"\"\"Determine impact level of pattern\"\"\"\n        \n        abs_improvement = abs(improvement)\n        \n        if abs_improvement >= 0.10:  # 10%+ improvement\n            return PatternImpact.MAJOR\n        elif abs_improvement >= 0.05:  # 5-10% improvement\n            return PatternImpact.SIGNIFICANT\n        elif abs_improvement >= 0.02:  # 2-5% improvement\n            return PatternImpact.MODERATE\n        else:\n            return PatternImpact.MINOR\n    \n    async def _trigger_pattern_analysis(self):\n        \"\"\"Trigger pattern analysis asynchronously\"\"\"\n        \n        try:\n            asyncio.create_task(self.analyze_patterns())\n        except Exception as e:\n            logger.error(f\"Failed to trigger pattern analysis: {e}\")\n    \n    def get_pattern_recommendations(\n        self,\n        decision_attributes: Dict[str, Any],\n        market_context: Dict[str, Any]\n    ) -> List[Dict[str, Any]]:\n        \"\"\"Get pattern-based recommendations for a decision\"\"\"\n        \n        recommendations = []\n        \n        try:\n            # Match current decision attributes against known patterns\n            for pattern in self.recognized_patterns.values():\n                match_score = self._calculate_pattern_match_score(\n                    decision_attributes,\n                    market_context,\n                    pattern\n                )\n                \n                if match_score > 0.7:  # High match threshold\n                    recommendation = {\n                        \"pattern_id\": pattern.pattern_id,\n                        \"pattern_name\": pattern.pattern_name,\n                        \"pattern_type\": pattern.pattern_type.value,\n                        \"match_score\": match_score,\n                        \"success_rate\": pattern.success_rate,\n                        \"expected_improvement\": pattern.avg_improvement,\n                        \"recommendations\": pattern.pattern_recommendations,\n                        \"confidence\": pattern.confidence.value\n                    }\n                    \n                    recommendations.append(recommendation)\n            \n            # Sort by match score and expected improvement\n            recommendations.sort(\n                key=lambda x: x[\"match_score\"] * (1 + x[\"expected_improvement\"]),\n                reverse=True\n            )\n            \n            return recommendations[:5]  # Top 5 recommendations\n            \n        except Exception as e:\n            logger.error(f\"Pattern recommendation generation failed: {e}\")\n            return []\n    \n    def _calculate_pattern_match_score(\n        self,\n        decision_attributes: Dict[str, Any],\n        market_context: Dict[str, Any],\n        pattern: RecognizedPattern\n    ) -> float:\n        \"\"\"Calculate how well current decision matches a pattern\"\"\"\n        \n        try:\n            match_factors = []\n            \n            # Confidence match\n            decision_confidence = decision_attributes.get(\"confidence\", 0.5)\n            pattern_conf_range = pattern.pattern_attributes.get(\"confidence_range\", {})\n            \n            if pattern_conf_range:\n                conf_min, conf_max = pattern_conf_range[\"min\"], pattern_conf_range[\"max\"]\n                if conf_min <= decision_confidence <= conf_max:\n                    match_factors.append(1.0)\n                else:\n                    # Calculate distance from range\n                    distance = min(\n                        abs(decision_confidence - conf_min),\n                        abs(decision_confidence - conf_max)\n                    )\n                    match_factors.append(max(0, 1 - distance * 2))  # Penalty for being outside range\n            \n            # Action match\n            decision_action = decision_attributes.get(\"action\", \"hold\")\n            pattern_action = pattern.pattern_attributes.get(\"primary_action\")\n            \n            if pattern_action and decision_action == pattern_action:\n                match_factors.append(1.0)\n            elif pattern_action:\n                match_factors.append(0.3)  # Partial match for different action\n            \n            # Market volatility match\n            market_volatility = market_context.get(\"volatility\", 0.5)\n            pattern_vol_range = pattern.pattern_attributes.get(\"volatility_range\", {})\n            \n            if pattern_vol_range:\n                vol_min, vol_max = pattern_vol_range[\"min\"], pattern_vol_range[\"max\"]\n                if vol_min <= market_volatility <= vol_max:\n                    match_factors.append(1.0)\n                else:\n                    distance = min(\n                        abs(market_volatility - vol_min),\n                        abs(market_volatility - vol_max)\n                    )\n                    match_factors.append(max(0, 1 - distance))  # Volatility match\n            \n            # Calculate weighted average\n            if match_factors:\n                return statistics.mean(match_factors)\n            else:\n                return 0.0\n            \n        except Exception as e:\n            logger.error(f\"Pattern match score calculation failed: {e}\")\n            return 0.0\n    \n    def get_pattern_statistics(self) -> Dict[str, Any]:\n        \"\"\"Get comprehensive pattern recognition statistics\"\"\"\n        \n        return {\n            \"pattern_statistics\": {\n                \"total_patterns\": len(self.recognized_patterns),\n                \"patterns_by_type\": self._count_patterns_by_type(),\n                \"patterns_by_confidence\": self._count_patterns_by_confidence(),\n                \"patterns_by_impact\": self._count_patterns_by_impact()\n            },\n            \"analysis_statistics\": self.analysis_statistics.copy(),\n            \"data_statistics\": {\n                \"total_decisions_tracked\": len(self.decision_data),\n                \"decisions_with_outcomes\": sum(\n                    1 for dp in self.decision_data \n                    if dp.success is not None\n                ),\n                \"data_quality_score\": self._calculate_data_quality_score(list(self.decision_data))\n            },\n            \"pattern_performance\": dict(self.pattern_performance),\n            \"system_health\": {\n                \"pattern_recognition_active\": len(self.recognized_patterns) > 0,\n                \"clustering_models_ready\": self.clustering_models[\"scaler\"] is not None,\n                \"sufficient_data_available\": len(self.decision_data) >= self.analysis_config[\"min_pattern_support\"]\n            },\n            \"timestamp\": datetime.now().isoformat()\n        }\n    \n    # Helper methods for statistics and utilities...\n    def _count_patterns_by_type(self) -> Dict[str, int]:\n        pattern_counts = defaultdict(int)\n        for pattern in self.recognized_patterns.values():\n            pattern_counts[pattern.pattern_type.value] += 1\n        return dict(pattern_counts)\n    \n    def _count_patterns_by_confidence(self) -> Dict[str, int]:\n        confidence_counts = defaultdict(int)\n        for pattern in self.recognized_patterns.values():\n            confidence_counts[pattern.confidence.value] += 1\n        return dict(confidence_counts)\n    \n    def _count_patterns_by_impact(self) -> Dict[str, int]:\n        impact_counts = defaultdict(int)\n        for pattern in self.recognized_patterns.values():\n            impact_counts[pattern.impact.value] += 1\n        return dict(impact_counts)\n\n\n# Global instance\ndecision_pattern_recognizer = DecisionPatternRecognizer()