# Internal Contract: Data Bridge Validation Rules

## 🎯 Validation Overview
Advanced server-side validation pipeline yang melakukan quality assessment beyond client-side processing dengan subscription-aware validation rules dan performance optimization.

---

## 🔍 Validation Architecture

### **Validation Pipeline Structure**
```
Input: BatchTickData (from Client-MT5)
   ↓
1. Basic Data Integrity Validation
   ↓
2. Market Context Validation
   ↓
3. Cross-Tick Correlation Analysis
   ↓
4. Subscription Tier Validation
   ↓
5. Quality Score Calculation
   ↓
Output: ValidationResults + QualityMetrics
```

### **Performance Target**
- **Per Tick Validation**: <1ms per tick
- **Batch Validation**: <3ms per batch (5 ticks)
- **Quality Assessment**: <0.5ms per batch
- **Memory Usage**: <50MB validation cache

---

## 📋 Validation Rule Categories

### **1. Basic Data Integrity Validation**

#### **Tick Data Structure Validation**
```python
class BasicDataValidator:
    def validate_tick_structure(self, tick: TickData) -> ValidationResult:
        """Validate basic tick data structure and ranges"""

        errors = []

        # Price validation
        if tick.bid <= 0 or tick.ask <= 0:
            errors.append("Invalid price: bid/ask must be positive")

        if tick.ask <= tick.bid:
            errors.append("Invalid spread: ask must be greater than bid")

        # Spread validation (realistic spread ranges)
        spread = tick.ask - tick.bid
        if spread > tick.bid * 0.1:  # 10% spread threshold
            errors.append(f"Unrealistic spread: {spread:.5f}")

        # Timestamp validation
        now = time.time() * 1000
        if tick.timestamp > now + 5000:  # 5 second future tolerance
            errors.append("Invalid timestamp: tick from future")

        if tick.timestamp < now - 300000:  # 5 minute past tolerance
            errors.append("Invalid timestamp: tick too old")

        # Volume validation
        if tick.volume < 0:
            errors.append("Invalid volume: must be non-negative")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            confidence=1.0 - (len(errors) * 0.2)
        )
```

#### **Symbol Validation**
```python
# Valid trading pairs dan their characteristics
VALID_SYMBOLS = {
    'EURUSD': {'min_price': 0.5, 'max_price': 2.0, 'max_spread': 0.0050},
    'GBPUSD': {'min_price': 0.8, 'max_price': 2.5, 'max_spread': 0.0060},
    'USDJPY': {'min_price': 50.0, 'max_price': 200.0, 'max_spread': 0.050},
    'AUDUSD': {'min_price': 0.4, 'max_price': 1.5, 'max_spread': 0.0055},
    'USDCAD': {'min_price': 0.8, 'max_price': 2.0, 'max_spread': 0.0055}
}

def validate_symbol_characteristics(self, tick: TickData) -> ValidationResult:
    """Validate tick against known symbol characteristics"""

    symbol_config = VALID_SYMBOLS.get(tick.symbol)
    if not symbol_config:
        return ValidationResult(False, [f"Unknown symbol: {tick.symbol}"], 0.0)

    errors = []

    # Price range validation
    if not (symbol_config['min_price'] <= tick.bid <= symbol_config['max_price']):
        errors.append(f"Price out of range for {tick.symbol}")

    # Spread validation
    spread = tick.ask - tick.bid
    if spread > symbol_config['max_spread']:
        errors.append(f"Spread too wide for {tick.symbol}: {spread:.5f}")

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        confidence=0.9 if len(errors) == 0 else 0.3
    )
```

---

### **2. Market Context Validation**

#### **Trading Hours Compliance**
```python
class MarketSessionValidator:
    def __init__(self):
        # Market hours (UTC) untuk different regions
        self.market_hours = {
            'EURUSD': {'open': '07:00', 'close': '17:00', 'timezone': 'UTC'},
            'USDJPY': {'open': '21:00', 'close': '07:00', 'timezone': 'UTC'},  # Spans midnight
            'GBPUSD': {'open': '08:00', 'close': '16:00', 'timezone': 'UTC'},
        }

    def validate_trading_hours(self, tick: TickData) -> ValidationResult:
        """Validate tick timestamp against market trading hours"""

        session_config = self.market_hours.get(tick.symbol)
        if not session_config:
            return ValidationResult(True, [], 0.8)  # Unknown symbol, allow with lower confidence

        tick_time = datetime.fromtimestamp(tick.timestamp / 1000, tz=timezone.utc)
        hour = tick_time.strftime('%H:%M')

        # Handle overnight sessions (spans midnight)
        open_time = session_config['open']
        close_time = session_config['close']

        is_valid = self._is_within_trading_hours(hour, open_time, close_time)

        if not is_valid:
            return ValidationResult(
                False,
                [f"Tick outside trading hours for {tick.symbol}: {hour}"],
                0.2
            )

        return ValidationResult(True, [], 0.95)
```

#### **Market Volatility Context**
```python
def validate_price_volatility(self, tick: TickData, historical_context: dict) -> ValidationResult:
    """Validate tick against recent price movements"""

    # Get recent price history untuk volatility assessment
    recent_prices = historical_context.get('recent_prices', [])
    if len(recent_prices) < 10:
        return ValidationResult(True, [], 0.7)  # Insufficient data

    # Calculate recent volatility
    price_changes = [abs(recent_prices[i] - recent_prices[i-1]) for i in range(1, len(recent_prices))]
    avg_volatility = sum(price_changes) / len(price_changes)

    # Current price change
    last_price = recent_prices[-1]
    current_change = abs(tick.bid - last_price)

    # Volatility threshold (5x average volatility)
    volatility_threshold = avg_volatility * 5

    if current_change > volatility_threshold:
        return ValidationResult(
            False,
            [f"Excessive price movement: {current_change:.5f} > {volatility_threshold:.5f}"],
            0.1
        )

    return ValidationResult(True, [], 0.9)
```

---

### **3. Cross-Tick Correlation Analysis**

#### **Batch Consistency Validation**
```python
class CrossTickValidator:
    def validate_batch_consistency(self, batch_data: BatchTickData) -> ValidationResult:
        """Validate consistency across ticks dalam same batch"""

        errors = []
        ticks = batch_data.ticks

        if len(ticks) < 2:
            return ValidationResult(True, [], 1.0)  # Single tick batch

        # Timestamp ordering validation
        for i in range(1, len(ticks)):
            if ticks[i].timestamp < ticks[i-1].timestamp:
                errors.append(f"Timestamp disorder: tick {i} older than tick {i-1}")

        # Symbol correlation validation (same symbol in batch)
        first_symbol = ticks[0].symbol
        for i, tick in enumerate(ticks[1:], 1):
            if tick.symbol != first_symbol:
                errors.append(f"Symbol mismatch: tick {i} has {tick.symbol}, expected {first_symbol}")

        # Price continuity validation (no extreme jumps)
        for i in range(1, len(ticks)):
            price_change = abs(ticks[i].bid - ticks[i-1].bid) / ticks[i-1].bid
            if price_change > 0.05:  # 5% change threshold
                errors.append(f"Extreme price jump: {price_change:.2%} between ticks {i-1} and {i}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            confidence=1.0 - (len(errors) * 0.15)
        )
```

#### **Cross-Pair Correlation** (Advanced Feature)
```python
def validate_cross_pair_correlation(self, tick: TickData, market_context: dict) -> ValidationResult:
    """Validate tick against correlated currency pairs"""

    # Correlation rules (simplified)
    correlations = {
        'EURUSD': {'GBPUSD': 0.7, 'USDCHF': -0.8},
        'GBPUSD': {'EURUSD': 0.7, 'GBPJPY': 0.6},
        'USDJPY': {'EURJPY': 0.8, 'GBPJPY': 0.6}
    }

    symbol_correlations = correlations.get(tick.symbol, {})
    if not symbol_correlations:
        return ValidationResult(True, [], 0.8)  # No correlation rules

    errors = []
    for correlated_symbol, correlation_coefficient in symbol_correlations.items():
        correlated_price = market_context.get(f"{correlated_symbol}_price")
        if not correlated_price:
            continue

        # Simplified correlation check (actual implementation would be more sophisticated)
        expected_direction = 1 if correlation_coefficient > 0 else -1
        # Implementation would check if price movements are in expected direction

    return ValidationResult(True, [], 0.8)  # Placeholder for complex correlation logic
```

---

### **4. Subscription Tier Validation**

#### **Symbol Access Validation** (From BUSINESS_FEATURES.md)
```python
class SubscriptionValidator:
    def __init__(self):
        # Subscription tier limits (consistent dengan BUSINESS_FEATURES.md)
        self.tier_limits = {
            'free': {
                'symbols': ['EURUSD', 'GBPUSD'],
                'max_ticks_per_second': 10,
                'advanced_validation': False
            },
            'pro': {
                'symbols': ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD'],
                'max_ticks_per_second': 50,
                'advanced_validation': True
            },
            'enterprise': {
                'symbols': 'all',
                'max_ticks_per_second': 'unlimited',
                'advanced_validation': True,
                'real_time_alerts': True
            }
        }

    def validate_subscription_access(self, tick: TickData, user_context: UserContext) -> ValidationResult:
        """Validate tick access against user subscription tier"""

        tier_config = self.tier_limits.get(user_context.tier)
        if not tier_config:
            return ValidationResult(False, ["Invalid subscription tier"], 0.0)

        errors = []

        # Symbol access validation
        allowed_symbols = tier_config['symbols']
        if allowed_symbols != 'all' and tick.symbol not in allowed_symbols:
            errors.append(f"Symbol {tick.symbol} not allowed for {user_context.tier} tier")

        # Rate limiting validation (simplified)
        # Actual implementation would track per-user rates

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            confidence=1.0 if len(errors) == 0 else 0.0
        )
```

#### **Feature Access Validation**
```python
def validate_feature_access(self, validation_type: str, user_context: UserContext) -> bool:
    """Validate if user has access to specific validation features"""

    tier_config = self.tier_limits.get(user_context.tier, {})

    feature_access = {
        'advanced_validation': tier_config.get('advanced_validation', False),
        'real_time_alerts': tier_config.get('real_time_alerts', False),
        'cross_pair_correlation': user_context.tier == 'enterprise',
        'historical_analysis': user_context.tier in ['pro', 'enterprise']
    }

    return feature_access.get(validation_type, False)
```

---

### **5. Quality Score Calculation**

#### **Comprehensive Quality Assessment**
```python
class QualityScoreCalculator:
    def calculate_quality_score(self, enriched_data: EnrichedBatchData) -> QualityScore:
        """Calculate comprehensive quality score untuk batch"""

        # Individual validation scores
        basic_validation_score = self.calculate_basic_validation_score(enriched_data)
        market_context_score = self.calculate_market_context_score(enriched_data)
        consistency_score = self.calculate_consistency_score(enriched_data)

        # Weighted quality score
        weights = {
            'basic_validation': 0.4,    # 40% weight
            'market_context': 0.3,      # 30% weight
            'consistency': 0.2,         # 20% weight
            'user_relevance': 0.1       # 10% weight
        }

        overall_score = (
            basic_validation_score * weights['basic_validation'] +
            market_context_score * weights['market_context'] +
            consistency_score * weights['consistency'] +
            self.calculate_user_relevance_score(enriched_data) * weights['user_relevance']
        )

        return QualityScore(
            overall_score=overall_score,
            basic_validation=basic_validation_score,
            market_context=market_context_score,
            consistency=consistency_score,
            confidence_level=self.calculate_confidence_level(enriched_data),
            processing_timestamp=int(time.time() * 1000)
        )
```

#### **Quality Score Thresholds**
```python
QUALITY_THRESHOLDS = {
    'excellent': 0.95,      # Premium quality data
    'good': 0.85,          # Standard quality
    'acceptable': 0.70,     # Minimum acceptable quality
    'poor': 0.50,          # Quality issues detected
    'rejected': 0.30       # Below minimum standards
}

def get_quality_classification(self, score: float) -> str:
    """Classify quality based on score"""
    for classification, threshold in QUALITY_THRESHOLDS.items():
        if score >= threshold:
            return classification
    return 'rejected'
```

---

## 🔧 Validation Configuration

### **Performance Optimization**
```python
class ValidationConfig:
    def __init__(self):
        # Performance settings
        self.max_validation_time_ms = 3000  # 3ms per batch
        self.cache_validation_results = True
        self.cache_ttl_seconds = 60

        # Quality thresholds
        self.min_acceptable_quality = 0.7
        self.auto_reject_threshold = 0.3

        # Feature flags per subscription tier
        self.feature_flags = {
            'free': ['basic_validation'],
            'pro': ['basic_validation', 'market_context', 'consistency_check'],
            'enterprise': ['all_validations', 'advanced_analytics', 'real_time_alerts']
        }
```

### **Error Handling Strategy**
```python
class ValidationErrorHandler:
    def handle_validation_failure(self, tick: TickData, validation_result: ValidationResult) -> ProcessingDecision:
        """Handle different types of validation failures"""

        if validation_result.confidence < 0.3:
            return ProcessingDecision.REJECT  # Hard rejection

        elif validation_result.confidence < 0.7:
            return ProcessingDecision.FLAG_AND_STORE  # Store dengan warning flag

        else:
            return ProcessingDecision.ACCEPT_WITH_WARNING  # Accept dengan quality note
```

---

## 📊 Validation Metrics & Monitoring

### **Performance Metrics**
```python
# Validation performance tracking
validation_metrics = {
    'avg_validation_time_ms': 2.1,
    'validation_success_rate': 0.97,
    'quality_score_distribution': {
        'excellent': 0.45,
        'good': 0.35,
        'acceptable': 0.15,
        'poor': 0.04,
        'rejected': 0.01
    },
    'error_categories': {
        'timestamp_errors': 0.02,
        'price_range_errors': 0.01,
        'spread_errors': 0.005,
        'correlation_errors': 0.003
    }
}
```

### **Alerting Thresholds**
- **Validation Time**: >5ms average (performance degradation)
- **Quality Score**: <0.8 average (quality issues)
- **Error Rate**: >5% validation failures (data quality problems)
- **Rejection Rate**: >2% hard rejections (severe quality issues)

---

**Key Innovation**: Comprehensive multi-layered validation dengan subscription-aware processing, real-time quality assessment, dan performance optimization untuk enterprise-grade trading data validation.