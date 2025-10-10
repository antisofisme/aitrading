"""
Configuration loader for Polygon.io Historical Downloader
"""
import os
import yaml
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class PairConfig:
    symbol: str
    polygon_symbol: str
    priority: int

class Config:
    def __init__(self, config_path: str = "/app/config/schedule.yaml"):
        self.config_path = config_path
        self._config = self._load_config()

        # Environment variables
        self.polygon_api_key = os.getenv("POLYGON_API_KEY")
        if not self.polygon_api_key:
            raise ValueError("POLYGON_API_KEY environment variable not set")

        self.instance_id = os.getenv("INSTANCE_ID", "polygon-historical-downloader-1")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

    def _load_config(self) -> Dict:
        """Load YAML configuration"""
        config_file = Path(self.config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(config_file, 'r') as f:
            return yaml.safe_load(f)

    @property
    def pairs(self) -> List[PairConfig]:
        """Get all pairs to download"""
        pairs = []
        for pair in self._config.get('pairs', []):
            pairs.append(PairConfig(
                symbol=pair['symbol'],
                polygon_symbol=pair['polygon_symbol'],
                priority=pair['priority']
            ))
        return pairs

    @property
    def download_config(self) -> Dict:
        """Get download configuration"""
        config = self._config.get('download', {})

        # Parse dates - ENV takes priority over YAML config
        start_date = os.getenv('HISTORICAL_START_DATE',
                               config.get('start_date', '2023-01-01'))
        end_date = os.getenv('HISTORICAL_END_DATE',
                             config.get('end_date', 'today'))

        if end_date == 'today' or end_date == 'now':
            end_date = datetime.now().strftime('%Y-%m-%d')

        config['start_date'] = start_date
        config['end_date'] = end_date

        return config

    @property
    def gap_detection_config(self) -> Dict:
        """Get gap detection configuration"""
        return self._config.get('gap_detection', {})

    @property
    def schedules(self) -> Dict:
        """Get schedule configuration"""
        return self._config.get('schedules', {})

    @property
    def monitoring_config(self) -> Dict:
        """Get monitoring configuration"""
        return self._config.get('monitoring', {})

    def get_timeframe_for_pair(self, pair: PairConfig) -> tuple:
        """
        Get timeframe and multiplier for a pair based on priority

        Returns: (timeframe, multiplier)
        """
        download_cfg = self.download_config
        granularity = download_cfg.get('granularity', {})

        if pair.priority <= 2:
            # Trading pairs: 1-minute bars
            cfg = granularity.get('trading_pairs', {})
        elif pair.priority == 3:
            # Analysis pairs: 1-minute bars
            cfg = granularity.get('analysis_pairs', {})
        else:
            # Confirmation pairs: 5-minute bars
            cfg = granularity.get('confirmation_pairs', {})

        timeframe = cfg.get('timeframe', 'minute')
        multiplier = cfg.get('multiplier', 1)

        return timeframe, multiplier
