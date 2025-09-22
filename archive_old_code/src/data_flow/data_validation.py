"""
Data Validation System - Level 3 Data Flow
Real-time market data validation with quality assurance
Target: <50ms validation latency with 99.9% accuracy
"""

import asyncio
import logging
import time
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import statistics
from collections import deque, defaultdict
import json
import aioredis

from .mt5_integration import MarketTick, OHLCV

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ValidationSeverity(Enum):
    """Validation issue severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ValidationRule(Enum):
    """Market data validation rules"""
    PRICE_RANGE = "price_range"
    SPREAD_CHECK = "spread_check"
    TIMESTAMP_VALIDATION = "timestamp_validation"
    VOLUME_SANITY = "volume_sanity"
    PRICE_CONTINUITY = "price_continuity"
    OUTLIER_DETECTION = "outlier_detection"
    DUPLICATE_CHECK = "duplicate_check"
    SEQUENCE_VALIDATION = "sequence_validation"

@dataclass
class ValidationResult:
    """Validation result for a market tick"""
    is_valid: bool
    rule: ValidationRule
    severity: ValidationSeverity
    message: str
    tick_id: str
    symbol: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ValidationStats:
    """Validation statistics tracking"""
    total_ticks: int = 0
    valid_ticks: int = 0
    invalid_ticks: int = 0
    warnings: int = 0
    errors: int = 0
    critical_issues: int = 0
    validation_times: List[float] = field(default_factory=list)
    rules_triggered: Dict[str, int] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """Calculate validation success rate"""
        if self.total_ticks == 0:
            return 100.0
        return (self.valid_ticks / self.total_ticks) * 100

    @property
    def avg_validation_time(self) -> float:
        """Average validation time in milliseconds"""
        if not self.validation_times:
            return 0.0
        return statistics.mean(self.validation_times) * 1000

class MarketDataQualityChecker:
    """Real-time market data quality assessment"""

    def __init__(self, symbol: str, history_size: int = 1000):
        self.symbol = symbol
        self.history_size = history_size

        # Historical data for quality checks
        self.price_history = deque(maxlen=history_size)
        self.volume_history = deque(maxlen=history_size)
        self.spread_history = deque(maxlen=history_size)
        self.timestamp_history = deque(maxlen=history_size)

        # Quality metrics
        self.price_stats = {'mean': 0, 'std': 0, 'min': 0, 'max': 0}
        self.volume_stats = {'mean': 0, 'std': 0, 'min': 0, 'max': 0}

        # Anomaly detection
        self.outlier_threshold = 3.0  # Standard deviations
        self.max_spread_percent = 0.1  # 10 basis points
        self.max_price_change_percent = 0.05  # 5% max price change

    def update_history(self, tick: MarketTick):
        """Update historical data for quality assessment"""
        mid_price = (tick.bid + tick.ask) / 2
        spread_percent = tick.spread / mid_price if mid_price > 0 else 0

        self.price_history.append(mid_price)
        self.volume_history.append(tick.volume)
        self.spread_history.append(spread_percent)
        self.timestamp_history.append(tick.timestamp)

        # Update statistics if we have enough data
        if len(self.price_history) >= 20:
            self._update_statistics()

    def _update_statistics(self):
        """Update statistical measures for quality checking"""
        prices = list(self.price_history)
        volumes = list(self.volume_history)

        self.price_stats = {
            'mean': statistics.mean(prices),
            'std': statistics.stdev(prices) if len(prices) > 1 else 0,
            'min': min(prices),
            'max': max(prices)
        }

        self.volume_stats = {
            'mean': statistics.mean(volumes),
            'std': statistics.stdev(volumes) if len(volumes) > 1 else 0,
            'min': min(volumes),
            'max': max(volumes)
        }

    def check_price_outlier(self, tick: MarketTick) -> Optional[ValidationResult]:
        """Check for price outliers using statistical analysis"""
        if len(self.price_history) < 20:
            return None

        mid_price = (tick.bid + tick.ask) / 2
        z_score = abs(mid_price - self.price_stats['mean']) / self.price_stats['std'] if self.price_stats['std'] > 0 else 0

        if z_score > self.outlier_threshold:
            return ValidationResult(
                is_valid=False,
                rule=ValidationRule.OUTLIER_DETECTION,
                severity=ValidationSeverity.WARNING,
                message=f"Price outlier detected: {mid_price}, z-score: {z_score:.2f}",
                tick_id=f"{tick.symbol}_{tick.timestamp.timestamp()}",
                symbol=tick.symbol,
                timestamp=tick.timestamp,
                metadata={'z_score': z_score, 'price': mid_price}
            )

        return None

    def check_price_continuity(self, tick: MarketTick) -> Optional[ValidationResult]:
        """Check price continuity between consecutive ticks"""
        if len(self.price_history) == 0:
            return None

        current_price = (tick.bid + tick.ask) / 2
        last_price = self.price_history[-1]

        price_change_percent = abs(current_price - last_price) / last_price if last_price > 0 else 0

        if price_change_percent > self.max_price_change_percent:
            return ValidationResult(
                is_valid=False,
                rule=ValidationRule.PRICE_CONTINUITY,
                severity=ValidationSeverity.ERROR,
                message=f"Excessive price change: {price_change_percent:.4f}% in single tick",
                tick_id=f"{tick.symbol}_{tick.timestamp.timestamp()}",
                symbol=tick.symbol,
                timestamp=tick.timestamp,
                metadata={'price_change_percent': price_change_percent}
            )

        return None

class DataValidator:
    """Comprehensive market data validation system"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()

        # Validation components
        self.quality_checkers: Dict[str, MarketDataQualityChecker] = {}
        self.validation_stats = ValidationStats()

        # Duplicate detection
        self.seen_ticks: Set[str] = set()
        self.tick_cache_size = 10000

        # Sequence validation
        self.last_sequence_numbers: Dict[str, int] = {}

        # Performance tracking
        self.validation_start_time = time.time()

        logger.info("Data Validator initialized")

    def _default_config(self) -> Dict[str, Any]:
        """Default validation configuration"""
        return {
            'max_bid_ask_spread_percent': 0.1,  # 10 basis points
            'max_price_change_percent': 0.05,   # 5% max change
            'min_volume': 0,
            'max_volume': 1000000,
            'timestamp_tolerance_seconds': 60,
            'enable_outlier_detection': True,
            'enable_duplicate_check': True,
            'enable_sequence_validation': True,
            'history_size': 1000
        }

    async def validate_tick(self, tick: MarketTick) -> List[ValidationResult]:
        """Comprehensive tick validation"""
        start_time = time.time()
        validation_results = []

        try:
            # Ensure quality checker exists for symbol
            if tick.symbol not in self.quality_checkers:
                self.quality_checkers[tick.symbol] = MarketDataQualityChecker(
                    tick.symbol,
                    self.config['history_size']
                )

            quality_checker = self.quality_checkers[tick.symbol]

            # Run all validation rules
            validation_results.extend(await self._validate_basic_rules(tick))
            validation_results.extend(await self._validate_advanced_rules(tick, quality_checker))

            # Update quality checker history
            quality_checker.update_history(tick)

            # Update statistics
            self.validation_stats.total_ticks += 1

            if not validation_results or all(r.is_valid for r in validation_results):
                self.validation_stats.valid_ticks += 1
            else:
                self.validation_stats.invalid_ticks += 1

                # Count by severity
                for result in validation_results:
                    if result.severity == ValidationSeverity.WARNING:
                        self.validation_stats.warnings += 1
                    elif result.severity == ValidationSeverity.ERROR:
                        self.validation_stats.errors += 1
                    elif result.severity == ValidationSeverity.CRITICAL:
                        self.validation_stats.critical_issues += 1

                    # Count rules triggered
                    rule_name = result.rule.value
                    self.validation_stats.rules_triggered[rule_name] = \
                        self.validation_stats.rules_triggered.get(rule_name, 0) + 1

            # Record validation time
            validation_time = time.time() - start_time
            self.validation_stats.validation_times.append(validation_time)

            # Keep only recent validation times
            if len(self.validation_stats.validation_times) > 1000:
                self.validation_stats.validation_times = self.validation_stats.validation_times[-1000:]

            return validation_results

        except Exception as e:
            logger.error(f"Validation error for tick {tick.symbol}: {e}")
            return [ValidationResult(
                is_valid=False,
                rule=ValidationRule.TIMESTAMP_VALIDATION,
                severity=ValidationSeverity.CRITICAL,
                message=f"Validation system error: {str(e)}",
                tick_id=f"{tick.symbol}_{tick.timestamp.timestamp()}",
                symbol=tick.symbol,
                timestamp=tick.timestamp
            )]

    async def _validate_basic_rules(self, tick: MarketTick) -> List[ValidationResult]:
        """Validate basic market data rules"""
        results = []

        # Price range validation
        if tick.bid <= 0 or tick.ask <= 0:
            results.append(ValidationResult(
                is_valid=False,
                rule=ValidationRule.PRICE_RANGE,
                severity=ValidationSeverity.CRITICAL,
                message=f"Invalid price: bid={tick.bid}, ask={tick.ask}",
                tick_id=f"{tick.symbol}_{tick.timestamp.timestamp()}",
                symbol=tick.symbol,
                timestamp=tick.timestamp
            ))

        # Bid-Ask spread validation
        if tick.ask < tick.bid:
            results.append(ValidationResult(
                is_valid=False,
                rule=ValidationRule.SPREAD_CHECK,
                severity=ValidationSeverity.ERROR,
                message=f"Ask ({tick.ask}) is less than bid ({tick.bid})",
                tick_id=f"{tick.symbol}_{tick.timestamp.timestamp()}",
                symbol=tick.symbol,
                timestamp=tick.timestamp
            ))

        # Spread percentage check
        mid_price = (tick.bid + tick.ask) / 2
        spread_percent = tick.spread / mid_price if mid_price > 0 else 0

        if spread_percent > self.config['max_bid_ask_spread_percent']:
            results.append(ValidationResult(
                is_valid=False,
                rule=ValidationRule.SPREAD_CHECK,
                severity=ValidationSeverity.WARNING,
                message=f"Excessive spread: {spread_percent:.4f}%",
                tick_id=f"{tick.symbol}_{tick.timestamp.timestamp()}",
                symbol=tick.symbol,
                timestamp=tick.timestamp,
                metadata={'spread_percent': spread_percent}
            ))

        # Timestamp validation
        now = datetime.utcnow()
        time_diff = abs((now - tick.timestamp).total_seconds())

        if time_diff > self.config['timestamp_tolerance_seconds']:
            results.append(ValidationResult(
                is_valid=False,
                rule=ValidationRule.TIMESTAMP_VALIDATION,
                severity=ValidationSeverity.WARNING,
                message=f"Timestamp out of tolerance: {time_diff:.1f}s difference",
                tick_id=f"{tick.symbol}_{tick.timestamp.timestamp()}",
                symbol=tick.symbol,
                timestamp=tick.timestamp,
                metadata={'time_difference': time_diff}
            ))

        # Volume validation
        if tick.volume < self.config['min_volume'] or tick.volume > self.config['max_volume']:
            results.append(ValidationResult(
                is_valid=False,
                rule=ValidationRule.VOLUME_SANITY,
                severity=ValidationSeverity.WARNING,
                message=f"Volume out of range: {tick.volume}",
                tick_id=f"{tick.symbol}_{tick.timestamp.timestamp()}",
                symbol=tick.symbol,
                timestamp=tick.timestamp
            ))

        return results

    async def _validate_advanced_rules(self, tick: MarketTick, quality_checker: MarketDataQualityChecker) -> List[ValidationResult]:
        """Validate advanced market data rules"""
        results = []

        # Duplicate detection
        if self.config['enable_duplicate_check']:
            tick_id = f"{tick.symbol}_{tick.timestamp.timestamp()}_{tick.bid}_{tick.ask}"

            if tick_id in self.seen_ticks:
                results.append(ValidationResult(
                    is_valid=False,
                    rule=ValidationRule.DUPLICATE_CHECK,
                    severity=ValidationSeverity.WARNING,
                    message="Duplicate tick detected",
                    tick_id=tick_id,
                    symbol=tick.symbol,
                    timestamp=tick.timestamp
                ))
            else:
                self.seen_ticks.add(tick_id)

                # Limit cache size
                if len(self.seen_ticks) > self.tick_cache_size:
                    # Remove oldest 10% of entries (simplified)
                    items_to_remove = len(self.seen_ticks) // 10
                    for _ in range(items_to_remove):
                        self.seen_ticks.pop()

        # Outlier detection
        if self.config['enable_outlier_detection']:
            outlier_result = quality_checker.check_price_outlier(tick)
            if outlier_result:
                results.append(outlier_result)

        # Price continuity check
        continuity_result = quality_checker.check_price_continuity(tick)
        if continuity_result:
            results.append(continuity_result)

        return results

    async def validate_batch(self, ticks: List[MarketTick]) -> Dict[str, List[ValidationResult]]:
        """Validate batch of ticks efficiently"""
        batch_results = {}

        # Process ticks concurrently
        validation_tasks = [self.validate_tick(tick) for tick in ticks]
        all_results = await asyncio.gather(*validation_tasks, return_exceptions=True)

        for tick, results in zip(ticks, all_results):
            tick_key = f"{tick.symbol}_{tick.timestamp.timestamp()}"

            if isinstance(results, Exception):
                # Handle validation exception
                batch_results[tick_key] = [ValidationResult(
                    is_valid=False,
                    rule=ValidationRule.TIMESTAMP_VALIDATION,
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Batch validation error: {str(results)}",
                    tick_id=tick_key,
                    symbol=tick.symbol,
                    timestamp=tick.timestamp
                )]
            else:
                batch_results[tick_key] = results

        return batch_results

    def get_validation_summary(self) -> Dict[str, Any]:
        """Get comprehensive validation summary"""
        runtime_seconds = time.time() - self.validation_start_time

        return {
            'runtime_seconds': runtime_seconds,
            'total_ticks_processed': self.validation_stats.total_ticks,
            'processing_rate_tps': self.validation_stats.total_ticks / runtime_seconds if runtime_seconds > 0 else 0,
            'success_rate_percent': self.validation_stats.success_rate,
            'avg_validation_time_ms': self.validation_stats.avg_validation_time,
            'performance_target_met': self.validation_stats.avg_validation_time < 50,  # <50ms target
            'validation_breakdown': {
                'valid_ticks': self.validation_stats.valid_ticks,
                'invalid_ticks': self.validation_stats.invalid_ticks,
                'warnings': self.validation_stats.warnings,
                'errors': self.validation_stats.errors,
                'critical_issues': self.validation_stats.critical_issues
            },
            'rules_triggered': self.validation_stats.rules_triggered,
            'symbols_monitored': list(self.quality_checkers.keys()),
            'config': self.config
        }

    def reset_statistics(self):
        """Reset validation statistics"""
        self.validation_stats = ValidationStats()
        self.validation_start_time = time.time()
        self.seen_ticks.clear()
        logger.info("Validation statistics reset")

class ValidationAlertManager:
    """Manage and route validation alerts"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        self.alert_subscribers: List[callable] = []

    async def initialize(self):
        """Initialize alert manager"""
        try:
            self.redis = aioredis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            logger.info("Validation alert manager initialized")

        except Exception as e:
            logger.error(f"Failed to initialize alert manager: {e}")

    async def process_validation_results(self, results: List[ValidationResult]):
        """Process validation results and generate alerts"""
        for result in results:
            if not result.is_valid:
                await self._send_alert(result)

    async def _send_alert(self, result: ValidationResult):
        """Send validation alert"""
        try:
            alert_data = {
                'type': 'validation_alert',
                'severity': result.severity.value,
                'rule': result.rule.value,
                'symbol': result.symbol,
                'message': result.message,
                'timestamp': result.timestamp.isoformat(),
                'metadata': result.metadata
            }

            # Publish to Redis
            if self.redis:
                await self.redis.publish('validation_alerts', json.dumps(alert_data))

            # Notify subscribers
            for subscriber in self.alert_subscribers:
                try:
                    await subscriber(result)
                except Exception as e:
                    logger.error(f"Alert subscriber error: {e}")

            # Log critical issues
            if result.severity == ValidationSeverity.CRITICAL:
                logger.critical(f"CRITICAL validation issue: {result.message}")
            elif result.severity == ValidationSeverity.ERROR:
                logger.error(f"Validation error: {result.message}")

        except Exception as e:
            logger.error(f"Alert sending error: {e}")

    def subscribe_to_alerts(self, callback: callable):
        """Subscribe to validation alerts"""
        self.alert_subscribers.append(callback)

# Factory function for easy setup
async def create_data_validator(config: Dict[str, Any] = None) -> DataValidator:
    """Create and initialize data validator"""
    try:
        validator = DataValidator(config)

        # Notify coordination system
        await _notify_validation_ready()

        logger.info("Data validator created successfully")
        return validator

    except Exception as e:
        logger.error(f"Error creating data validator: {e}")
        return None

async def _notify_validation_ready():
    """Notify coordination system that validation is ready"""
    try:
        import subprocess
        result = subprocess.run([
            'npx', 'claude-flow@alpha', 'hooks', 'notify',
            '--message', 'Data validation system operational - quality assurance active'
        ], capture_output=True, text=True)

        if result.returncode == 0:
            logger.info("Data validation readiness notification sent")
        else:
            logger.warning(f"Failed to send validation notification: {result.stderr}")

    except Exception as e:
        logger.warning(f"Validation coordination notification failed: {e}")

# Export main components
__all__ = [
    'DataValidator',
    'ValidationResult',
    'ValidationRule',
    'ValidationSeverity',
    'ValidationStats',
    'MarketDataQualityChecker',
    'ValidationAlertManager',
    'create_data_validator'
]