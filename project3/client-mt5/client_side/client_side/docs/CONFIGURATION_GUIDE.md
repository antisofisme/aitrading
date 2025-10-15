# MT5 Bridge Configuration Guide

## 🎯 Overview
This guide explains the configuration system for the MT5 Bridge client-side application, including production-optimized defaults and security features.

## 📁 Configuration Files

### `.env` - Active Configuration
- **Location**: `/client_side/.env`
- **Purpose**: Contains actual configuration values used by the application
- **Security**: Can contain encrypted credentials in production

### `.env.example` - Template Configuration
- **Location**: `/client_side/.env.example`
- **Purpose**: Template showing all available configuration options
- **Security**: Contains placeholder values, safe to commit to version control

## 🔧 Configuration Categories

### 1. MT5 Connection Settings
```env
MT5_LOGIN=your_mt5_login
MT5_PASSWORD=your_mt5_password
MT5_SERVER=your_broker_server
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe
MT5_TIMEOUT=60000
```

### 2. Backend Connection Settings
```env
BACKEND_WS_URL=ws://localhost:8000/api/v1/ws/mt5
BACKEND_API_URL=http://localhost:8000/api
BACKEND_AUTH_TOKEN=
BACKEND_RECONNECT_ATTEMPTS=3
BACKEND_HEARTBEAT_INTERVAL=15
BACKEND_CONNECTION_TIMEOUT=10
```

### 3. Trading Settings (Production-Safe Defaults)
```env
TRADING_ENABLED=false          # Must be explicitly enabled
MAX_RISK_PERCENT=1.0           # Conservative 1% risk per trade
MAX_DAILY_TRADES=5             # Maximum 5 trades per day
EMERGENCY_STOP=false
SIMULATION_MODE=true           # Start in simulation mode
PAPER_TRADING=true             # Use paper trading first
```

### 4. Streaming Configuration (Redpanda/Kafka)
```env
STREAMING_BOOTSTRAP_SERVERS=localhost:9092
STREAMING_SECURITY_PROTOCOL=PLAINTEXT
STREAMING_CLIENT_ID=mt5_bridge
STREAMING_AUTO_OFFSET_RESET=latest
TICK_DATA_TOPIC=market_ticks
SIGNAL_TOPIC=trading_signals
EVENTS_TOPIC=trading_events
```

### 5. Logging Configuration (Production-Optimized)
```env
LOG_LEVEL=INFO
LOG_FILE=mt5_bridge.log
LOG_MAX_SIZE=5242880            # 5MB for faster rotation
LOG_RETENTION=3                 # Keep only 3 days of logs
DATABASE_LOGGING_ENABLED=true
LOG_BATCH_SIZE=50              # Smaller batches for real-time logging
LOG_FLUSH_INTERVAL=2.0         # More frequent flushes
```

### 6. Database Logging (ClickHouse)
```env
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
CLICKHOUSE_USER=ai_admin
CLICKHOUSE_PASSWORD=trading_secure_2024
CLICKHOUSE_DATABASE=trading_data
```

## 🛡️ Security Features

### Credential Encryption
The configuration system supports automatic encryption of sensitive credentials for production use.

#### Setup Encryption
```bash
# Generate master key
python manage_credentials.py generate-key

# Encrypt sensitive credentials in .env file
python manage_credentials.py encrypt

# Check encryption status
python manage_credentials.py status
```

#### Encrypted Fields
- `MT5_PASSWORD`
- `MT5_LOGIN`
- `CLICKHOUSE_PASSWORD`
- `BACKEND_AUTH_TOKEN`

#### Environment Variables
```bash
# Set master key for encryption
export ENCRYPTION_MASTER_KEY="your_generated_master_key"
```

## 🚀 Production Optimization

### Safety-First Defaults
- **Trading Disabled**: Requires explicit activation
- **Simulation Mode**: Enabled by default for testing
- **Paper Trading**: Active by default for safe testing
- **Conservative Risk**: 1% maximum risk per trade
- **Limited Trades**: Maximum 5 trades per day

### Connection Optimization
- **Faster Heartbeats**: 15-second intervals for better monitoring
- **Reduced Reconnect Attempts**: 3 attempts for faster failure detection
- **Shorter Timeouts**: 10-second timeout for quick response

### Logging Optimization
- **Smaller Log Files**: 5MB rotation for better performance
- **Shorter Retention**: 3 days to save disk space
- **Real-time Logging**: Smaller batches and frequent flushes

## 📊 Configuration Validation

The system includes comprehensive validation for all configuration values:

### Trading Safety Validation
```python
# Risk percentage validation
if not 0.1 <= risk_percent <= 10.0:
    raise ValueError('Risk percentage must be between 0.1% and 10.0%')

# Daily trades validation
if not 1 <= daily_trades <= 100:
    raise ValueError('Daily trades must be between 1 and 100')
```

### Connection Validation
```python
# URL validation
if not url.startswith(('ws://', 'wss://', 'http://', 'https://')):
    raise ValueError('Invalid URL protocol')

# MT5 login validation
if login <= 0 or login > 999999999:
    raise ValueError('Invalid MT5 login format')
```

## 🔄 Configuration Loading Process

1. **Environment Variables**: Loaded from `.env` file
2. **Credential Decryption**: Automatic decryption of encrypted fields
3. **Validation**: All values validated against safety rules
4. **Default Values**: Production-optimized defaults applied
5. **Type Conversion**: Automatic type conversion and validation

## 🧪 Testing Configuration

### Basic Configuration Test
```bash
python3 -c "
from libs.config.mt5_config import get_mt5_settings
settings = get_mt5_settings()
print('✅ Configuration loaded successfully')
"
```

### Validation Test
```bash
python3 -c "
from libs.config.mt5_config import MT5Settings
# Test with invalid values to verify validation
try:
    settings = MT5Settings(
        mt5_login=123456,
        mt5_password='test',
        mt5_server='test',
        max_risk_percent=15.0  # Too high - should fail
    )
except Exception as e:
    print('✅ Validation working:', e)
"
```

### Security Test
```bash
python manage_credentials.py test
```

## 📝 Best Practices

### Development Environment
1. Use `.env.example` as template
2. Copy to `.env` and configure with your values
3. Keep `SIMULATION_MODE=true` for testing
4. Use `PAPER_TRADING=true` for safe testing

### Production Environment
1. Generate and secure master encryption key
2. Encrypt sensitive credentials
3. Set appropriate risk limits
4. Enable real trading only after thorough testing
5. Monitor logs and connections closely

### Security Recommendations
1. **Never commit** `.env` file to version control
2. **Encrypt credentials** in production environments
3. **Use strong passwords** for MT5 and database access
4. **Regularly rotate** authentication tokens
5. **Monitor access logs** for suspicious activity

## 🔍 Troubleshooting

### Configuration Errors
```bash
# Check configuration status
python manage_credentials.py status

# Validate configuration
python3 -c "from libs.config.mt5_config import get_mt5_settings; get_mt5_settings()"
```

### Connection Issues
- Verify backend URL and port availability
- Check firewall settings for MT5 and backend connections
- Ensure ClickHouse database is running and accessible

### Security Issues
- Verify master key is set correctly
- Check encryption status of sensitive fields
- Ensure proper file permissions on configuration files

## 📞 Support

For configuration issues or questions:
1. Check this guide and inline code documentation
2. Review validation error messages
3. Test configuration with provided utilities
4. Verify all dependencies are installed