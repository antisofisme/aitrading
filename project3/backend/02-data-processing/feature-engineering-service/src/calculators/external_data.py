"""
External Data Features Calculator - 12 features
Economic calendar (3) + FRED indicators (4) + Commodity prices (5)
"""
import pandas as pd
from typing import Dict, Optional

class ExternalDataCalculator:
    """Calculate external data features"""

    def __init__(self, clickhouse_client=None):
        """
        Args:
            clickhouse_client: ClickHouse client for querying external tables
        """
        self.client = clickhouse_client

    def calculate(self,
                  current_time: pd.Timestamp,
                  symbol: str) -> Dict[str, Optional[float]]:
        """
        Calculate external data features

        Args:
            current_time: Current timestamp
            symbol: Trading symbol (e.g., 'C:EURUSD')

        Returns:
            Dictionary with 12 external data features
        """
        features = {
            # Economic Calendar (3 features)
            'upcoming_event_minutes': None,
            'upcoming_event_impact': None,
            'recent_event_minutes': None,

            # FRED Indicators (4 features)
            'gdp_latest': None,
            'unemployment_latest': None,
            'cpi_latest': None,
            'interest_rate_latest': None,

            # Commodity Prices (4 features - oil_change_pct missing in schema counts)
            'gold_price': None,
            'oil_price': None,
            'gold_change_pct': None,
            'oil_change_pct': None
        }

        if self.client is None:
            return features

        try:
            # Extract currency from symbol (e.g., 'C:EURUSD' → 'EUR', 'USD')
            if symbol.startswith('C:'):
                pair = symbol[2:]  # Remove 'C:' prefix
                currency = pair[:3] if len(pair) >= 6 else None
            else:
                currency = None

            # === ECONOMIC CALENDAR ===
            # Simplified: Return None for Phase 1 (tables may not exist yet)
            # TODO: Implement in Phase 2 when external tables are populated

            # === FRED INDICATORS ===
            # Simplified: Return None for Phase 1
            # TODO: Implement when FRED data available

            # === COMMODITY PRICES ===
            # Simplified: Return None for Phase 1
            # TODO: Implement when commodity data available

        except Exception as e:
            print(f"Error fetching external data: {e}")

        return features
