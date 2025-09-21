"""
Data Transformation Middleware
Handles transformation and normalization of data from multiple sources
Supports 14 different data types with high-performance processing
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import numpy as np
from enum import Enum
import re
import json
from concurrent.futures import ThreadPoolExecutor

# Performance monitoring
from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)

# Metrics
TRANSFORM_COUNTER = Counter('data_transformer_operations_total', 'Transformation operations', ['source', 'data_type'])
TRANSFORM_LATENCY = Histogram('data_transformer_latency_seconds', 'Transformation latency', ['operation'])
TRANSFORM_ERROR_COUNTER = Counter('data_transformer_errors_total', 'Transformation errors', ['error_type'])


class TransformationError(Exception):
    """Custom exception for transformation errors"""
    pass


class DataFormat(Enum):
    """Supported data formats"""
    MT5_TICK = "mt5_tick"
    MT5_CANDLE = "mt5_candle"
    TRADINGVIEW_TICK = "tv_tick"
    TRADINGVIEW_CANDLE = "tv_candle"
    BINANCE_TICK = "binance_tick"
    BINANCE_KLINE = "binance_kline"
    ALPHA_VANTAGE = "alpha_vantage"
    YAHOO_FINANCE = "yahoo_finance"
    IEX_CLOUD = "iex_cloud"
    POLYGON_IO = "polygon_io"
    FINNHUB_IO = "finnhub_io"
    QUANDL = "quandl"
    FRED = "fred"
    ECONOMIC_CALENDAR = "economic_calendar"


@dataclass
class TransformationRule:
    """Transformation rule definition"""
    source_field: str
    target_field: str
    transformation: Optional[Callable] = None
    required: bool = True
    default_value: Any = None
    validation: Optional[Callable] = None


@dataclass
class NormalizedTick:
    """Normalized tick data structure"""
    symbol: str
    timestamp: float  # Unix timestamp with nanosecond precision
    bid: Decimal
    ask: Decimal
    last: Decimal
    volume: int
    spread: Decimal
    source: str

    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp,
            'bid': float(self.bid),
            'ask': float(self.ask),
            'last': float(self.last),
            'volume': self.volume,
            'spread': float(self.spread),
            'source': self.source
        }


@dataclass
class NormalizedCandle:
    """Normalized candle data structure"""
    symbol: str
    timestamp: float
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    timeframe: str
    source: str

    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp,
            'open': float(self.open),
            'high': float(self.high),
            'low': float(self.low),
            'close': float(self.close),
            'volume': self.volume,
            'timeframe': self.timeframe,
            'source': self.source
        }


class DataTransformer:
    """High-performance data transformer for multiple sources"""

    def __init__(self):
        self.transformation_rules = self._initialize_transformation_rules()
        self.symbol_mapping = self._initialize_symbol_mapping()
        self.executor = ThreadPoolExecutor(max_workers=4)

    def _initialize_transformation_rules(self) -> Dict[DataFormat, List[TransformationRule]]:
        """Initialize transformation rules for each data format"""
        return {
            DataFormat.MT5_TICK: [
                TransformationRule('symbol', 'symbol', self._normalize_symbol),
                TransformationRule('time', 'timestamp', self._normalize_timestamp_mt5),
                TransformationRule('bid', 'bid', self._normalize_price),
                TransformationRule('ask', 'ask', self._normalize_price),
                TransformationRule('last', 'last', self._normalize_price),
                TransformationRule('volume', 'volume', self._normalize_volume),
            ],

            DataFormat.TRADINGVIEW_TICK: [
                TransformationRule('s', 'symbol', self._normalize_symbol),
                TransformationRule('t', 'timestamp', self._normalize_timestamp_tv),
                TransformationRule('p', 'last', self._normalize_price),
                TransformationRule('s', 'volume', self._normalize_volume, default_value=0),
            ],

            DataFormat.BINANCE_TICK: [
                TransformationRule('s', 'symbol', self._normalize_symbol),
                TransformationRule('E', 'timestamp', self._normalize_timestamp_binance),
                TransformationRule('p', 'last', self._normalize_price),
                TransformationRule('q', 'volume', self._normalize_volume),
                TransformationRule('b', 'bid', self._normalize_price, required=False),
                TransformationRule('a', 'ask', self._normalize_price, required=False),
            ],

            DataFormat.BINANCE_KLINE: [
                TransformationRule('s', 'symbol', self._normalize_symbol),
                TransformationRule('t', 'timestamp', self._normalize_timestamp_binance),
                TransformationRule('o', 'open', self._normalize_price),
                TransformationRule('h', 'high', self._normalize_price),
                TransformationRule('l', 'low', self._normalize_price),
                TransformationRule('c', 'close', self._normalize_price),
                TransformationRule('v', 'volume', self._normalize_volume),
            ],

            DataFormat.ALPHA_VANTAGE: [
                TransformationRule('symbol', 'symbol', self._normalize_symbol),
                TransformationRule('timestamp', 'timestamp', self._normalize_timestamp_iso),
                TransformationRule('open', 'open', self._normalize_price),
                TransformationRule('high', 'high', self._normalize_price),
                TransformationRule('low', 'low', self._normalize_price),
                TransformationRule('close', 'close', self._normalize_price),
                TransformationRule('volume', 'volume', self._normalize_volume),
            ],

            # Add more transformation rules for other formats...
        }

    def _initialize_symbol_mapping(self) -> Dict[str, str]:
        """Initialize symbol mapping between different providers"""
        return {
            # MT5 to standard mapping
            'EURUSD': 'EUR/USD',
            'GBPUSD': 'GBP/USD',
            'USDJPY': 'USD/JPY',
            'USDCHF': 'USD/CHF',
            'AUDUSD': 'AUD/USD',
            'USDCAD': 'USD/CAD',
            'NZDUSD': 'NZD/USD',
            'EURGBP': 'EUR/GBP',
            'EURJPY': 'EUR/JPY',
            'GBPJPY': 'GBP/JPY',
            'XAUUSD': 'XAU/USD',
            'XAGUSD': 'XAG/USD',

            # Binance to standard mapping
            'BTCUSDT': 'BTC/USDT',
            'ETHUSDT': 'ETH/USDT',
            'ADAUSDT': 'ADA/USDT',
            'DOTUSDT': 'DOT/USDT',
            'LINKUSDT': 'LINK/USDT',

            # Add more mappings as needed...
        }

    async def transform_data(
        self,
        data: Dict,
        source_format: DataFormat,
        target_type: str = 'tick'
    ) -> Union[NormalizedTick, NormalizedCandle, Dict]:
        """Transform data from source format to normalized format"""
        start_time = time.time()

        try:
            # Get transformation rules for the source format
            rules = self.transformation_rules.get(source_format)
            if not rules:
                raise TransformationError(f"No transformation rules for format: {source_format}")

            # Apply transformations
            normalized_data = await self._apply_transformations(data, rules)

            # Create appropriate normalized object
            if target_type == 'tick':
                result = await self._create_normalized_tick(normalized_data, source_format.value)
            elif target_type == 'candle':
                result = await self._create_normalized_candle(normalized_data, source_format.value)
            else:
                result = normalized_data

            # Record metrics
            TRANSFORM_COUNTER.labels(
                source=source_format.value,
                data_type=target_type
            ).inc()

            latency = time.time() - start_time
            TRANSFORM_LATENCY.labels(operation='transform').observe(latency)

            return result

        except Exception as e:
            TRANSFORM_ERROR_COUNTER.labels(error_type=type(e).__name__).inc()
            logger.error(f"Transformation error for {source_format}: {e}")
            raise TransformationError(f"Failed to transform data: {str(e)}")

    async def _apply_transformations(
        self,
        data: Dict,
        rules: List[TransformationRule]
    ) -> Dict:
        """Apply transformation rules to data"""
        result = {}

        for rule in rules:
            try:
                # Get source value
                if rule.source_field in data:
                    source_value = data[rule.source_field]
                elif rule.required:
                    raise TransformationError(f"Required field missing: {rule.source_field}")
                else:
                    source_value = rule.default_value

                # Apply transformation
                if rule.transformation and source_value is not None:
                    transformed_value = await self._run_transformation(
                        rule.transformation,
                        source_value
                    )
                else:
                    transformed_value = source_value

                # Apply validation
                if rule.validation and transformed_value is not None:
                    if not await self._run_validation(rule.validation, transformed_value):
                        raise TransformationError(
                            f"Validation failed for field: {rule.target_field}"
                        )

                result[rule.target_field] = transformed_value

            except Exception as e:
                if rule.required:
                    raise TransformationError(
                        f"Failed to transform required field {rule.source_field}: {e}"
                    )
                else:
                    logger.warning(
                        f"Failed to transform optional field {rule.source_field}: {e}"
                    )
                    result[rule.target_field] = rule.default_value

        return result

    async def _run_transformation(self, transformation: Callable, value: Any) -> Any:
        """Run transformation function with proper async handling"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, transformation, value)

    async def _run_validation(self, validation: Callable, value: Any) -> bool:
        """Run validation function with proper async handling"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, validation, value)

    async def _create_normalized_tick(self, data: Dict, source: str) -> NormalizedTick:
        """Create normalized tick object"""
        # Calculate spread if bid and ask are available
        spread = Decimal('0')
        if 'bid' in data and 'ask' in data and data['bid'] and data['ask']:
            spread = Decimal(str(data['ask'])) - Decimal(str(data['bid']))

        # Use last price for missing bid/ask
        if 'last' in data and data['last']:
            if 'bid' not in data or not data['bid']:
                data['bid'] = data['last']
            if 'ask' not in data or not data['ask']:
                data['ask'] = data['last']

        return NormalizedTick(
            symbol=data.get('symbol', ''),
            timestamp=data.get('timestamp', 0.0),
            bid=Decimal(str(data.get('bid', 0))),
            ask=Decimal(str(data.get('ask', 0))),
            last=Decimal(str(data.get('last', 0))),
            volume=int(data.get('volume', 0)),
            spread=spread,
            source=source
        )

    async def _create_normalized_candle(self, data: Dict, source: str) -> NormalizedCandle:
        """Create normalized candle object"""
        return NormalizedCandle(
            symbol=data.get('symbol', ''),
            timestamp=data.get('timestamp', 0.0),
            open=Decimal(str(data.get('open', 0))),
            high=Decimal(str(data.get('high', 0))),
            low=Decimal(str(data.get('low', 0))),
            close=Decimal(str(data.get('close', 0))),
            volume=int(data.get('volume', 0)),
            timeframe=data.get('timeframe', '1m'),
            source=source
        )

    # Transformation functions
    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol format"""
        if not symbol or not isinstance(symbol, str):
            return ''

        # Clean and uppercase
        symbol = symbol.strip().upper()

        # Apply symbol mapping if available
        mapped_symbol = self.symbol_mapping.get(symbol, symbol)

        # Remove common prefixes/suffixes
        mapped_symbol = re.sub(r'^(FX_IDC:|OANDA:)', '', mapped_symbol)
        mapped_symbol = re.sub(r'_(m|h|d)$', '', mapped_symbol)

        return mapped_symbol

    def _normalize_timestamp_mt5(self, timestamp: Any) -> float:
        """Normalize MT5 timestamp to Unix timestamp with nanosecond precision"""
        if isinstance(timestamp, (int, float)):
            # Already Unix timestamp
            return float(timestamp)
        elif isinstance(timestamp, str):
            # Parse ISO format or other string formats
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                return dt.timestamp()
            except:
                # Try parsing as Unix timestamp string
                return float(timestamp)
        else:
            return time.time()

    def _normalize_timestamp_tv(self, timestamp: Any) -> float:
        """Normalize TradingView timestamp"""
        if isinstance(timestamp, (int, float)):
            # TradingView uses milliseconds
            return float(timestamp) / 1000.0
        return self._normalize_timestamp_mt5(timestamp)

    def _normalize_timestamp_binance(self, timestamp: Any) -> float:
        """Normalize Binance timestamp"""
        if isinstance(timestamp, (int, float)):
            # Binance uses milliseconds
            return float(timestamp) / 1000.0
        return self._normalize_timestamp_mt5(timestamp)

    def _normalize_timestamp_iso(self, timestamp: Any) -> float:
        """Normalize ISO timestamp"""
        if isinstance(timestamp, str):
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                return dt.timestamp()
            except:
                pass
        return self._normalize_timestamp_mt5(timestamp)

    def _normalize_price(self, price: Any) -> Decimal:
        """Normalize price to Decimal with proper precision"""
        if price is None:
            return Decimal('0')

        try:
            # Convert to string first to avoid float precision issues
            price_str = str(price)
            decimal_price = Decimal(price_str)

            # Round to 8 decimal places for precision
            return decimal_price.quantize(Decimal('0.00000001'), rounding=ROUND_HALF_UP)

        except (ValueError, TypeError):
            logger.warning(f"Invalid price value: {price}")
            return Decimal('0')

    def _normalize_volume(self, volume: Any) -> int:
        """Normalize volume to integer"""
        if volume is None:
            return 0

        try:
            # Handle scientific notation and float volumes
            if isinstance(volume, str):
                volume = float(volume)
            return int(float(volume))
        except (ValueError, TypeError):
            logger.warning(f"Invalid volume value: {volume}")
            return 0

    # Validation functions
    def _validate_price(self, price: Decimal) -> bool:
        """Validate price value"""
        return price >= 0 and price < Decimal('1000000')  # Reasonable price range

    def _validate_volume(self, volume: int) -> bool:
        """Validate volume value"""
        return volume >= 0 and volume < 10**12  # Reasonable volume range

    def _validate_symbol(self, symbol: str) -> bool:
        """Validate symbol format"""
        return len(symbol) >= 3 and len(symbol) <= 20 and symbol.isalnum()

    async def batch_transform(
        self,
        data_list: List[Dict],
        source_format: DataFormat,
        target_type: str = 'tick'
    ) -> List[Union[NormalizedTick, NormalizedCandle, Dict]]:
        """Transform multiple data items in batch for better performance"""
        start_time = time.time()

        try:
            # Process in parallel for better performance
            tasks = [
                self.transform_data(data, source_format, target_type)
                for data in data_list
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter out exceptions and log errors
            valid_results = []
            error_count = 0

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Batch transform error for item {i}: {result}")
                    error_count += 1
                else:
                    valid_results.append(result)

            # Record batch metrics
            batch_latency = time.time() - start_time
            TRANSFORM_LATENCY.labels(operation='batch_transform').observe(batch_latency)

            if error_count > 0:
                TRANSFORM_ERROR_COUNTER.labels(error_type='batch_error').inc(error_count)

            logger.info(
                f"Batch transform completed: {len(valid_results)}/{len(data_list)} "
                f"successful in {batch_latency:.3f}s"
            )

            return valid_results

        except Exception as e:
            TRANSFORM_ERROR_COUNTER.labels(error_type='batch_exception').inc()
            logger.error(f"Batch transformation failed: {e}")
            raise TransformationError(f"Batch transformation failed: {str(e)}")

    def get_supported_formats(self) -> List[str]:
        """Get list of supported data formats"""
        return [format.value for format in DataFormat]

    def add_transformation_rule(
        self,
        format: DataFormat,
        rule: TransformationRule
    ):
        """Add custom transformation rule"""
        if format not in self.transformation_rules:
            self.transformation_rules[format] = []
        self.transformation_rules[format].append(rule)

    def add_symbol_mapping(self, source_symbol: str, target_symbol: str):
        """Add custom symbol mapping"""
        self.symbol_mapping[source_symbol] = target_symbol


# Performance testing utilities
class TransformationBenchmark:
    """Benchmark transformation performance"""

    @staticmethod
    async def benchmark_single_transform(
        transformer: DataTransformer,
        sample_data: Dict,
        source_format: DataFormat,
        iterations: int = 1000
    ) -> Dict:
        """Benchmark single transformation performance"""
        latencies = []

        for _ in range(iterations):
            start_time = time.time()
            try:
                await transformer.transform_data(sample_data, source_format)
                latency = time.time() - start_time
                latencies.append(latency)
            except Exception as e:
                logger.error(f"Benchmark error: {e}")

        if latencies:
            return {
                'mean_latency': np.mean(latencies),
                'p50_latency': np.percentile(latencies, 50),
                'p95_latency': np.percentile(latencies, 95),
                'p99_latency': np.percentile(latencies, 99),
                'max_latency': np.max(latencies),
                'min_latency': np.min(latencies),
                'successful_transforms': len(latencies),
                'total_iterations': iterations
            }
        else:
            return {'error': 'No successful transformations'}

    @staticmethod
    async def benchmark_batch_transform(
        transformer: DataTransformer,
        sample_data: List[Dict],
        source_format: DataFormat,
        batch_sizes: List[int] = [1, 10, 50, 100, 500]
    ) -> Dict:
        """Benchmark batch transformation performance"""
        results = {}

        for batch_size in batch_sizes:
            if batch_size > len(sample_data):
                continue

            batch_data = sample_data[:batch_size]
            start_time = time.time()

            try:
                transformed = await transformer.batch_transform(
                    batch_data,
                    source_format
                )

                latency = time.time() - start_time
                throughput = len(transformed) / latency if latency > 0 else 0

                results[f'batch_size_{batch_size}'] = {
                    'latency': latency,
                    'throughput_tps': throughput,
                    'successful_transforms': len(transformed),
                    'input_size': len(batch_data)
                }

            except Exception as e:
                results[f'batch_size_{batch_size}'] = {'error': str(e)}

        return results


# Global transformer instance
_transformer_instance = None


def get_transformer() -> DataTransformer:
    """Get global transformer instance"""
    global _transformer_instance
    if _transformer_instance is None:
        _transformer_instance = DataTransformer()
    return _transformer_instance