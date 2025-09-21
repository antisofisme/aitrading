# PC Client Installation Guide

Complete guide for setting up the Windows PC client for live trading with MetaTrader 5 integration.

## Prerequisites

### System Requirements

- **Operating System**: Windows 10/11 (64-bit)
- **Memory**: 8GB RAM minimum, 16GB recommended
- **Storage**: 10GB free space, SSD recommended
- **CPU**: Intel i5 or AMD Ryzen 5 equivalent or better
- **Network**: Stable internet connection with low latency to broker

### Software Requirements

- **MetaTrader 5**: Latest version from your broker
- **Node.js**: Version 18 or higher
- **Python**: Version 3.9 or higher
- **Git**: Latest version
- **Docker Desktop**: Latest version (optional, for containerized deployment)

## Step 1: Environment Setup

### Install Required Software

```powershell
# Install using Chocolatey (recommended)
# First install Chocolatey if not already installed
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install required software
choco install nodejs python git docker-desktop -y

# Verify installations
node --version
python --version
git --version
docker --version
```

### Alternative Manual Installation

1. **Node.js**: Download from [nodejs.org](https://nodejs.org/)
2. **Python**: Download from [python.org](https://python.org/)
3. **Git**: Download from [git-scm.com](https://git-scm.com/)
4. **Docker Desktop**: Download from [docker.com](https://docker.com/)

## Step 2: Download and Setup

### Clone Repository

```powershell
# Navigate to desired installation directory
cd C:\
mkdir AITrading
cd AITrading

# Clone the repository
git clone https://github.com/your-org/ai-trading-platform.git
cd ai-trading-platform

# Install dependencies
npm install
```

### Python Environment Setup

```powershell
# Create Python virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install additional AI/ML packages
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## Step 3: MetaTrader 5 Configuration

### Install MetaTrader 5

1. Download MT5 from your broker's website
2. Install MT5 with default settings
3. Create or login to your trading account
4. Enable automated trading:
   - Tools → Options → Expert Advisors
   - Check "Allow automated trading"
   - Check "Allow DLL imports"
   - Check "Allow WebRequest for listed URL"

### Configure MT5 for API Access

```mql5
// Add to MT5 Tools → Options → Expert Advisors → Allowed URLs:
https://api.aitrading.com
http://localhost:8000
http://localhost:9001
```

### Test MT5 Connection

```powershell
# Test MT5 installation
python scripts/test_mt5_connection.py

# Expected output:
# MetaTrader 5 version: X.X.X
# Connection status: Connected
# Account info: [Your account details]
```

## Step 4: Configuration

### Create Environment File

```powershell
# Copy example environment file
copy .env.example .env.pc-client

# Edit configuration file
notepad .env.pc-client
```

### Environment Configuration

```bash
# MetaTrader 5 Configuration
MT5_LOGIN=your_mt5_login
MT5_PASSWORD=your_mt5_password
MT5_SERVER=your_broker_server
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe

# Trading Configuration
TRADING_MODE=paper  # Start with paper trading
MAX_RISK_PER_TRADE=0.02
CONFIDENCE_THRESHOLD=0.75
ALLOWED_SYMBOLS=EURUSD,GBPUSD,USDJPY,XAUUSD

# AI Configuration
AI_MODEL_PATH=./models
INFERENCE_TIMEOUT=100
MODEL_UPDATE_INTERVAL=3600000

# Backend Configuration
BACKEND_URL=http://localhost:8000
API_KEY=your_api_key
WEBSOCKET_URL=ws://localhost:8001

# Security Configuration
ENCRYPTION_KEY=your_32_character_encryption_key
JWT_SECRET=your_jwt_secret

# Logging Configuration
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=30
```

### Validate Configuration

```powershell
# Validate configuration
npm run validate:config

# Test all connections
npm run test:connections

# Expected output:
# ✓ MT5 connection successful
# ✓ Backend API accessible
# ✓ WebSocket connection established
# ✓ AI models loaded successfully
```

## Step 5: Installation Methods

### Method 1: Native Installation (Recommended)

```powershell
# Setup PC client
npm run setup:pc-client

# Install Windows service (optional)
npm run install:service

# Start services
npm run start:pc-client

# Check status
npm run status:pc-client
```

### Method 2: Docker Installation

```powershell
# Build Docker images
docker-compose -f docker-compose.pc-client.yml build

# Start all services
docker-compose -f docker-compose.pc-client.yml up -d

# Check service status
docker-compose -f docker-compose.pc-client.yml ps

# View logs
docker-compose -f docker-compose.pc-client.yml logs -f
```

## Step 6: Testing and Validation

### Paper Trading Test

```powershell
# Start in paper trading mode
npm run start:trading --mode=paper

# Run automated tests
npm run test:paper-trading

# Monitor performance
npm run monitor:trading
```

### System Health Check

```powershell
# Complete system health check
npm run health:check

# Performance benchmark
npm run benchmark:performance

# Security audit
npm run audit:security
```

### AI Model Validation

```powershell
# Test AI model inference
npm run test:ai-models

# Validate prediction accuracy
npm run validate:predictions

# Check model performance
npm run monitor:ai-performance
```

## Step 7: Go Live

### Pre-Live Checklist

- [ ] Paper trading successful for at least 1 week
- [ ] All tests passing
- [ ] Risk management validated
- [ ] Account funding confirmed
- [ ] Backup and recovery tested

### Switch to Live Trading

```powershell
# Stop paper trading
npm run stop:trading

# Update configuration
# Edit .env.pc-client: TRADING_MODE=live

# Start live trading
npm run start:trading --mode=live --confirm

# Monitor closely for first few hours
npm run monitor:live-trading
```

## Monitoring and Maintenance

### Real-time Monitoring

```powershell
# View real-time dashboard
npm run dashboard:pc-client

# Monitor trading performance
npm run monitor:performance

# Check system resources
npm run monitor:system
```

### Daily Maintenance

```powershell
# Daily health check
npm run daily:health-check

# Update AI models
npm run update:models

# Backup configuration
npm run backup:config

# Generate daily report
npm run generate:daily-report
```

### Log Management

```powershell
# View recent logs
npm run logs:recent

# Archive old logs
npm run logs:archive

# Clean up disk space
npm run cleanup:logs
```

## Troubleshooting

### Common Issues

#### MT5 Connection Problems

```powershell
# Check MT5 terminal status
tasklist | findstr terminal64.exe

# Restart MT5 terminal
npm run restart:mt5

# Test connection manually
python scripts/diagnose_mt5.py
```

#### AI Model Issues

```powershell
# Clear model cache
npm run clear:model-cache

# Reload models
npm run reload:models

# Test inference pipeline
npm run test:inference
```

#### Performance Issues

```powershell
# Check system resources
Get-Counter "\Processor(_Total)\% Processor Time"
Get-Counter "\Memory\Available MBytes"

# Optimize performance
npm run optimize:performance

# Check for bottlenecks
npm run diagnose:bottlenecks
```

### Recovery Procedures

#### Complete System Recovery

```powershell
# Stop all services
npm run stop:all

# Reset to clean state
npm run reset:clean

# Restore from backup
npm run restore:backup --date=YYYY-MM-DD

# Restart services
npm run start:all
```

#### Emergency Stop

```powershell
# Emergency stop all trading
npm run emergency:stop

# Close all positions
npm run close:all-positions

# Disconnect from broker
npm run disconnect:broker
```

## Security Considerations

### Data Protection

- All sensitive data is encrypted at rest
- API communications use TLS 1.3
- Local database is encrypted with AES-256
- Configuration files use secure credential storage

### Network Security

- Firewall rules for outbound broker connections only
- VPN recommended for broker connections
- No inbound network access required
- Local services bound to localhost only

### Access Control

- Windows service runs with limited privileges
- Log files have restricted access permissions
- Configuration requires administrator access
- API keys stored in secure credential store

## Performance Optimization

### Hardware Optimization

- Use SSD for database and logs
- Ensure adequate RAM for AI models
- Low-latency network connection
- Dedicated CPU cores for trading threads

### Software Optimization

```powershell
# Optimize database performance
npm run optimize:database

# Tune AI model performance
npm run tune:ai-models

# Configure OS for trading
npm run optimize:windows
```

## Support and Resources

### Documentation

- [API Reference](API_REFERENCE.md)
- [Trading Strategies](TRADING_STRATEGIES.md)
- [Risk Management](RISK_MANAGEMENT.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)

### Community Support

- **Discord**: [discord.gg/aitrading](https://discord.gg/aitrading)
- **Email**: support@aitrading.com
- **GitHub Issues**: [Repository Issues](https://github.com/your-org/ai-trading-platform/issues)

### Professional Support

- **Enterprise Support**: enterprise@aitrading.com
- **Custom Development**: development@aitrading.com
- **Training Services**: training@aitrading.com

---

**⚠️ Risk Warning**: Trading involves substantial risk of loss. Always use proper risk management and start with paper trading. This software is provided as-is without warranty.