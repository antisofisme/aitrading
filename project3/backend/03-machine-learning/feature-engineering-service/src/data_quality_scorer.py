"""
Data Quality Scorer - Calculates completeness score for ML features

Addresses Issue: External Data Timing Mismatch
Solution: Track feature completeness with data_quality_score (0-1)

Usage:
    scorer = DataQualityScorer()
    score, report = scorer.calculate_quality(features_dict, external_data)
"""

import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)


class DataQualityScorer:
    """
    Calculates data quality score (0-1) for ML features

    Quality Factors:
    - External data availability (news, economic indicators, sentiment)
    - Multi-timeframe data completeness
    - Technical indicator availability
    """

    # Feature group weights (based on expected importance)
    WEIGHTS = {
        'news_calendar': 0.20,  # 20% - High importance
        'external_indicators': 0.15,  # 15% - Medium importance
        'multi_timeframe': 0.15,  # 15% - Medium importance
        'technical_indicators': 0.10,  # 10% - Low importance
        'price_data': 0.40  # 40% - Critical (always should be 100%)
    }

    # Required fields per group
    REQUIRED_FIELDS = {
        'news_calendar': [
            'upcoming_high_impact_events_4h',
            'time_to_next_event_minutes',
            'event_impact_score',
            'event_type_category'
        ],
        'external_indicators': [
            'fred_gdp',
            'fred_unemployment',
            'fear_greed_index',
            'gold_price'
        ],
        'multi_timeframe': [
            'm5_momentum',
            'm15_consolidation',
            'h1_trend',
            'h4_structure',
            'd1_bias'
        ],
        'technical_indicators': [
            'rsi_value',
            'macd_histogram',
            'stochastic_k',
            'atr_current'
        ],
        'price_data': [
            'open', 'high', 'low', 'close', 'volume'
        ]
    }

    def calculate_quality(
        self,
        features: Dict[str, Any],
        external_data: Dict[str, Any]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate data quality score (0-1)

        Args:
            features: Calculated features dictionary
            external_data: External data dictionary

        Returns:
            (score, report) tuple
                - score: 0.0 (no data) to 1.0 (complete data)
                - report: Detailed breakdown per group
        """
        group_scores = {}
        report = {}

        # 1. Price Data Quality (should always be 1.0)
        price_score = self._check_price_data(features)
        group_scores['price_data'] = price_score
        report['price_data'] = {
            'score': price_score,
            'status': 'complete' if price_score == 1.0 else 'missing_fields'
        }

        # 2. News/Calendar Quality
        news_score = self._check_news_calendar(features, external_data)
        group_scores['news_calendar'] = news_score
        report['news_calendar'] = {
            'score': news_score,
            'status': self._get_status(news_score)
        }

        # 3. External Indicators Quality
        external_score = self._check_external_indicators(external_data)
        group_scores['external_indicators'] = external_score
        report['external_indicators'] = {
            'score': external_score,
            'status': self._get_status(external_score)
        }

        # 4. Multi-Timeframe Quality
        mtf_score = self._check_multi_timeframe(features)
        group_scores['multi_timeframe'] = mtf_score
        report['multi_timeframe'] = {
            'score': mtf_score,
            'status': self._get_status(mtf_score)
        }

        # 5. Technical Indicators Quality
        tech_score = self._check_technical_indicators(features)
        group_scores['technical_indicators'] = tech_score
        report['technical_indicators'] = {
            'score': tech_score,
            'status': self._get_status(tech_score)
        }

        # Calculate weighted total score
        total_score = sum(
            group_scores[group] * self.WEIGHTS[group]
            for group in group_scores
        )

        report['total_score'] = total_score
        report['quality_level'] = self._get_quality_level(total_score)

        return total_score, report

    def _check_price_data(self, features: Dict[str, Any]) -> float:
        """Check if basic price data is complete"""
        required = self.REQUIRED_FIELDS['price_data']
        present = sum(1 for field in required if field in features and features[field] is not None)
        return present / len(required)

    def _check_news_calendar(self, features: Dict[str, Any], external_data: Dict[str, Any]) -> float:
        """Check if news/calendar data is available"""
        required = self.REQUIRED_FIELDS['news_calendar']
        present = sum(
            1 for field in required
            if field in features and features[field] is not None and features[field] != 0
        )
        return present / len(required)

    def _check_external_indicators(self, external_data: Dict[str, Any]) -> float:
        """Check if external indicators are available"""
        if not external_data or external_data.get('economic_indicators', {}).get('empty', True):
            return 0.0

        indicators = external_data.get('economic_indicators', {})
        available_count = sum(
            1 for key, value in indicators.items()
            if key != 'empty' and value is not None
        )

        # At least 4 indicators expected (GDP, unemployment, CPI, interest rates)
        expected_count = 4
        return min(available_count / expected_count, 1.0)

    def _check_multi_timeframe(self, features: Dict[str, Any]) -> float:
        """Check if multi-timeframe features are calculated"""
        required = self.REQUIRED_FIELDS['multi_timeframe']
        present = sum(1 for field in required if field in features and features[field] is not None)
        return present / len(required)

    def _check_technical_indicators(self, features: Dict[str, Any]) -> float:
        """Check if technical indicators are available"""
        required = self.REQUIRED_FIELDS['technical_indicators']
        present = sum(1 for field in required if field in features and features[field] is not None)
        return present / len(required)

    def _get_status(self, score: float) -> str:
        """Get status label for a score"""
        if score >= 0.9:
            return 'complete'
        elif score >= 0.7:
            return 'good'
        elif score >= 0.5:
            return 'partial'
        elif score > 0:
            return 'poor'
        else:
            return 'missing'

    def _get_quality_level(self, score: float) -> str:
        """Get overall quality level"""
        if score >= 0.95:
            return 'EXCELLENT'
        elif score >= 0.85:
            return 'GOOD'
        elif score >= 0.70:
            return 'ACCEPTABLE'
        elif score >= 0.50:
            return 'POOR'
        else:
            return 'CRITICAL'


# Example usage
if __name__ == '__main__':
    # Test with sample data
    scorer = DataQualityScorer()

    # Complete data scenario
    complete_features = {
        'open': 2645.12, 'high': 2647.85, 'low': 2644.20, 'close': 2646.50, 'volume': 1234,
        'upcoming_high_impact_events_4h': 2,
        'time_to_next_event_minutes': 120,
        'event_impact_score': 3,
        'event_type_category': 'NFP',
        'm5_momentum': 0.02,
        'm15_consolidation': 1,
        'h1_trend': 1,
        'h4_structure': 'bullish',
        'd1_bias': 1,
        'rsi_value': 58.2,
        'macd_histogram': 1.35,
        'stochastic_k': 72.34,
        'atr_current': 18.45
    }

    complete_external = {
        'economic_calendar': [
            {'event': 'NFP', 'impact': 'high', 'time_to_event': 120}
        ],
        'economic_indicators': {
            'GDP': 3.2,
            'UNRATE': 3.8,
            'CPIAUCSL': 304.7,
            'DFF': 5.25
        }
    }

    score, report = scorer.calculate_quality(complete_features, complete_external)
    print(f"Complete Data Quality: {score:.3f} ({report['quality_level']})")
    print(f"Report: {report}")

    # Missing external data scenario
    incomplete_external = {'economic_indicators': {'empty': True}}

    score2, report2 = scorer.calculate_quality(complete_features, incomplete_external)
    print(f"\nMissing External Data Quality: {score2:.3f} ({report2['quality_level']})")
    print(f"Report: {report2}")
