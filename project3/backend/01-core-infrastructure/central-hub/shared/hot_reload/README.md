# Centralized Configuration Guidelines

## 🎯 Configuration Strategy

### STATIC Configuration (Environment Variables)
Use for infrastructure and security configs that should NOT change during runtime:

- **Database connections**: `DATABASE_URL`, `CLICKHOUSE_URL`, `CACHE_URL`
- **Message queues**: `NATS_URL`, `KAFKA_BROKERS`
- **Security**: `API_KEYS`, `JWT_SECRETS`, `ENCRYPTION_KEYS`
- **Service discovery**: `CONSUL_URL`, `ETCD_ENDPOINTS`

### HOT RELOAD Configuration (Central Hub)
Use for business logic that CAN change during runtime:

- **Business rules**: Rate limits, timeouts, validation rules
- **Feature toggles**: A/B testing flags, debug modes
- **Algorithm parameters**: Trading thresholds, ML model settings
- **Monitoring thresholds**: Alert levels, log verbosity

## 📁 File Naming Convention

```
config_{service_name}.py
```

Examples:
- `config_api_gateway.py`
- `config_trading_engine.py`
- `config_market_analyzer.py`
- `config_risk_manager.py`

## 🏗️ Configuration Structure

Each service config should follow this structure:

```python
{
    "service_info": {...},       # Service metadata
    "business_rules": {...},     # HOT RELOAD: Business logic
    "features": {...},           # HOT RELOAD: Feature flags
    "performance": {...},        # HOT RELOAD: Performance tuning
    "monitoring": {...},         # HOT RELOAD: Monitoring settings
    "static_references": {...},  # STATIC: Environment variable references
    "config_meta": {...}         # Configuration metadata
}
```

## 🔄 Hot Reload Topics

When configs are updated, they're published to NATS:

```
suho.config.update.{service_name}
```

Examples:
- `suho.config.update.api-gateway`
- `suho.config.update.trading-engine`

## ✅ Validation Rules

All configs must pass validation:

1. **Required fields**: Core settings must be present
2. **Numeric ranges**: Values within acceptable limits
3. **Allowed values**: Enums and constrained choices
4. **Type checking**: String/number/boolean validation

## 🚀 Creating a New Service Config

1. Copy `service_config_template.py`
2. Rename to `config_{service_name}.py`
3. Update service-specific values
4. Add to version control
5. Test hot reload functionality

## 🔒 Security Best Practices

1. **Never put secrets in hot reload configs**
2. **Use environment variable references**: `"ENV:SECRET_NAME"`
3. **Validate all inputs** before applying changes
4. **Log all config changes** for audit trail
5. **Test configs in staging** before production

## 📊 Example Service Configs

### API Gateway
```python
"business_rules": {
    "rate_limiting": {
        "requests_per_minute": 1000,
        "burst_limit": 100
    }
}
```

### Trading Engine
```python
"business_rules": {
    "position_limits": {
        "max_position_size_usd": 1000000,
        "max_daily_volume_usd": 10000000
    }
}
```

### Market Analyzer
```python
"business_rules": {
    "analysis_thresholds": {
        "volatility_threshold": 0.05,
        "trend_confidence_min": 0.8
    }
}
```

## 🐛 Troubleshooting

### Config not updating?
1. Check NATS connection
2. Verify topic subscription
3. Check config validation errors
4. Review service logs

### Service crashing after config update?
1. Check validation errors
2. Verify value ranges
3. Test config locally first
4. Use config rollback mechanism