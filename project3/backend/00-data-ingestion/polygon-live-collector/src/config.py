"""
Configuration loader for Polygon.io Live Collector
"""
import os
import yaml
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class PairConfig:
    symbol: str
    polygon_symbol: str
    description: str
    priority: int
    use_case: str = None
    volatility: str = None
    poll_interval: int = None

class Config:
    def __init__(self, config_path: str = "/app/config/pairs.yaml"):
        self.config_path = config_path
        self._config = self._load_config()

        # Environment variables
        self.polygon_api_key = os.getenv("POLYGON_API_KEY")
        if not self.polygon_api_key:
            raise ValueError("POLYGON_API_KEY environment variable not set")

        self.instance_id = os.getenv("INSTANCE_ID", "polygon-live-collector-1")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

    def _load_config(self) -> Dict:
        """Load YAML configuration"""
        config_file = Path(self.config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(config_file, 'r') as f:
            return yaml.safe_load(f)

    @property
    def websocket_trading_pairs(self) -> List[PairConfig]:
        """Get WebSocket trading pairs"""
        pairs = []
        for pair in self._config.get('websocket_trading_pairs', []):
            pairs.append(PairConfig(
                symbol=pair['symbol'],
                polygon_symbol=pair['polygon_symbol'],
                description=pair['description'],
                priority=pair['priority'],
                volatility=pair.get('volatility')
            ))
        return pairs

    @property
    def websocket_analysis_pairs(self) -> List[PairConfig]:
        """Get WebSocket analysis pairs"""
        pairs = []
        for pair in self._config.get('websocket_analysis_pairs', []):
            pairs.append(PairConfig(
                symbol=pair['symbol'],
                polygon_symbol=pair['polygon_symbol'],
                description=pair['description'],
                priority=pair['priority'],
                use_case=pair.get('use_case')
            ))
        return pairs

    @property
    def rest_confirmation_pairs(self) -> List[PairConfig]:
        """Get REST confirmation pairs"""
        pairs = []
        for pair in self._config.get('rest_confirmation_pairs', []):
            pairs.append(PairConfig(
                symbol=pair['symbol'],
                polygon_symbol=pair['polygon_symbol'],
                description=pair['description'],
                priority=pair.get('priority', 5),
                use_case=pair.get('use_case'),
                poll_interval=pair.get('poll_interval', 180)
            ))
        return pairs

    @property
    def all_websocket_pairs(self) -> List[PairConfig]:
        """Get all WebSocket pairs (trading + analysis)"""
        return self.websocket_trading_pairs + self.websocket_analysis_pairs

    @property
    def websocket_config(self) -> Dict:
        """Get WebSocket configuration"""
        return self._config.get('websocket_config', {})

    @property
    def rest_config(self) -> Dict:
        """Get REST API configuration"""
        return self._config.get('rest_config', {})

    @property
    def nats_config(self) -> Dict:
        """Get NATS configuration"""
        return self._config.get('nats_config', {})

    @property
    def kafka_config(self) -> Dict:
        """Get Kafka configuration"""
        return self._config.get('kafka_config', {})

    @property
    def monitoring_config(self) -> Dict:
        """Get monitoring configuration"""
        return self._config.get('monitoring', {})

    def get_websocket_subscriptions(self) -> List[str]:
        """
        Generate WebSocket subscription list
        Format: CA.C:EURUSD (Quotes for EUR/USD)
        """
        subscriptions = []
        prefix = self.websocket_config.get('subscription_prefix', 'CA')

        for pair in self.all_websocket_pairs:
            # Polygon uses format: CA.C:EURUSD
            subscription = f"{prefix}.{pair.polygon_symbol}"
            subscriptions.append(subscription)

        return subscriptions

    @property
    def aggregate_config(self) -> Dict:
        """Get aggregate configuration"""
        return self._config.get('aggregate_config', {})

    def get_aggregate_subscriptions(self) -> List[str]:
        """
        Generate aggregate WebSocket subscription list
        Format: CAS.C:EURUSD (Aggregates per second for EUR/USD)
        """
        agg_config = self.aggregate_config

        if not agg_config.get('enabled', False):
            return []

        subscriptions = []
        prefix = agg_config.get('websocket', {}).get('subscription_prefix', 'CAS')
        pairs = agg_config.get('websocket', {}).get('pairs', [])

        for pair_symbol in pairs:
            # Polygon uses format: CAS.C:EURUSD
            subscription = f"{prefix}.{pair_symbol}"
            subscriptions.append(subscription)

        return subscriptions
