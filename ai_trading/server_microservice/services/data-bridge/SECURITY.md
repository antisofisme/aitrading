# Security Guidelines - MT5 Bridge Microservice

## 🔒 Overview

The MT5 Bridge Microservice handles sensitive financial data and trading operations. This document outlines critical security requirements and best practices for secure deployment and operation.

## ⚠️ CRITICAL SECURITY REQUIREMENTS

### 1. Credential Management

#### ❌ NEVER DO:
```bash
# Don't hardcode credentials
MT5_PASSWORD = "hardcoded_password"

# Don't commit to version control
echo "MT5_LOGIN=12345" >> .env
git add .env  # WRONG!

# Don't use weak passwords
MT5_PASSWORD = "123456"
```

#### ✅ ALWAYS DO:
```bash
# Use environment variables
export MT5_LOGIN="$(cat /secure/mt5_login)"
export MT5_PASSWORD="$(cat /secure/mt5_password)"

# Use secure secret management
aws secretsmanager get-secret-value --secret-id mt5-credentials

# Use strong, unique passwords
MT5_PASSWORD="$(openssl rand -base64 32)"
```

### 2. Environment Variable Security

#### Production Environment Variables
```bash
# Required secure configuration
MT5_BRIDGE_SECRET_KEY="$(openssl rand -hex 32)"
MT5_LOGIN="your_secure_login"
MT5_PASSWORD="your_strong_password"
MT5_SERVER="production_server"

# Optional security enhancements
RATE_LIMIT_ENABLED=true
MAX_REQUESTS_PER_MINUTE=1000
WEBSOCKET_AUTH_REQUIRED=true
SSL_CERT_PATH="/certs/mt5-bridge.crt"
SSL_KEY_PATH="/certs/mt5-bridge.key"
```

#### Docker Secrets
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  mt5-bridge:
    image: mt5-bridge:latest
    secrets:
      - mt5_login
      - mt5_password
    environment:
      - MT5_LOGIN_FILE=/run/secrets/mt5_login
      - MT5_PASSWORD_FILE=/run/secrets/mt5_password

secrets:
  mt5_login:
    external: true
  mt5_password:
    external: true
```

### 3. WebSocket Security

#### Authentication
```python
# Client authentication example
import jwt
import websockets

async def connect_with_auth():
    token = jwt.encode(
        {"user_id": "trader_001", "permissions": ["trade", "read"]},
        secret_key,
        algorithm="HS256"
    )
    
    ws = await websockets.connect(
        "wss://mt5-bridge.domain.com/websocket/ws",
        extra_headers={"Authorization": f"Bearer {token}"}
    )
```

#### Rate Limiting
```python
# Automatic rate limiting per client
WEBSOCKET_RATE_LIMITS = {
    "messages_per_second": 100,
    "orders_per_minute": 10,
    "connections_per_ip": 5
}
```

### 4. Input Validation Security

#### Trading Parameter Validation
```python
# All trading inputs are validated
TRADING_VALIDATION_RULES = {
    "symbol": {
        "pattern": r"^[A-Z]{6}$",  # EURUSD format
        "whitelist": ["EURUSD", "GBPUSD", "USDJPY", ...]
    },
    "volume": {
        "min": 0.01,
        "max": 10.0,
        "precision": 2
    },
    "price": {
        "min": 0.0001,
        "max": 10000.0,
        "precision": 5
    }
}
```

#### SQL Injection Prevention
```python
# Using parameterized queries
async def store_trade_data(symbol: str, volume: float):
    query = """
        INSERT INTO trades (symbol, volume, timestamp)
        VALUES ($1, $2, $3)
    """
    await connection.execute(query, symbol, volume, datetime.utcnow())
```

## 🛡️ Security Configuration

### 1. TLS/SSL Configuration

#### Production TLS Setup
```bash
# Generate SSL certificates
openssl req -x509 -newkey rsa:4096 -keyout mt5-bridge.key -out mt5-bridge.crt -days 365

# Configure HTTPS
uvicorn main:app --host 0.0.0.0 --port 8001 --ssl-keyfile=mt5-bridge.key --ssl-certfile=mt5-bridge.crt
```

#### Docker TLS Configuration
```yaml
services:
  mt5-bridge:
    ports:
      - "443:8001"
    volumes:
      - ./certs:/app/certs:ro
    environment:
      - SSL_ENABLED=true
      - SSL_CERT_PATH=/app/certs/mt5-bridge.crt
      - SSL_KEY_PATH=/app/certs/mt5-bridge.key
```

### 2. Network Security

#### Firewall Rules
```bash
# Allow only necessary ports
ufw allow 8001/tcp  # MT5 Bridge API
ufw allow 443/tcp   # HTTPS
ufw deny 22/tcp     # Disable SSH on production

# Restrict WebSocket access
iptables -A INPUT -p tcp --dport 8001 -s trusted_ip_range -j ACCEPT
iptables -A INPUT -p tcp --dport 8001 -j DROP
```

#### VPN/Private Network
```yaml
# Use private networks for production
networks:
  mt5_private:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### 3. Authentication & Authorization

#### JWT Token Configuration
```python
# Secure JWT configuration
JWT_SETTINGS = {
    "algorithm": "RS256",  # Use RSA instead of HS256
    "access_token_expire_minutes": 30,
    "refresh_token_expire_days": 7,
    "issuer": "mt5-bridge-service",
    "audience": ["trading-clients"]
}
```

#### Role-Based Access Control
```python
PERMISSIONS = {
    "admin": ["read", "write", "trade", "manage"],
    "trader": ["read", "write", "trade"],
    "viewer": ["read"],
    "api": ["read", "trade"]
}
```

### 4. Audit Logging

#### Security Event Logging
```python
# Log all security-relevant events
SECURITY_EVENTS = [
    "authentication_attempt",
    "authentication_failure", 
    "order_placement",
    "configuration_change",
    "admin_access",
    "unusual_trading_pattern"
]
```

#### Log Format
```json
{
  "timestamp": "2025-01-27T10:00:00Z",
  "event_type": "security",
  "severity": "high",
  "user_id": "trader_001",
  "ip_address": "192.168.1.100",
  "action": "order_placement",
  "details": {
    "symbol": "EURUSD",
    "volume": 10.0,
    "value": 108500
  },
  "result": "success"
}
```

## 🚨 Incident Response

### 1. Security Monitoring

#### Automated Alerts
```python
SECURITY_ALERTS = {
    "failed_login_threshold": 5,
    "unusual_volume_threshold": 100.0,
    "connection_rate_threshold": 50,
    "error_rate_threshold": 10
}
```

#### Monitoring Dashboard
```bash
# Security metrics endpoints
GET /security/metrics        # Security statistics
GET /security/active-sessions # Current sessions
GET /security/audit-log      # Recent security events
```

### 2. Emergency Procedures

#### Emergency Stop
```python
# Immediate trading halt
POST /emergency/stop-all-trading
{
  "reason": "security_incident",
  "stop_new_orders": true,
  "close_existing_positions": false,
  "notify_admins": true
}
```

#### Account Lockout
```python
# Lock compromised accounts
POST /security/lock-account
{
  "account_id": "trader_001",
  "reason": "suspicious_activity",
  "duration_minutes": 60
}
```

### 3. Data Breach Response

#### Data Classification
```
CONFIDENTIAL:
- Trading account credentials
- Personal trading strategies
- Account balance information

RESTRICTED:
- Trading history
- Performance metrics
- System configuration

PUBLIC:
- Market data
- General system status
```

#### Breach Notification
```python
# Automatic breach detection
BREACH_TRIGGERS = [
    "unauthorized_data_access",
    "credential_compromise", 
    "system_intrusion",
    "data_exfiltration"
]
```

## 🔐 Compliance & Regulations

### 1. Financial Regulations

#### Data Retention
```python
DATA_RETENTION_POLICY = {
    "trading_records": "7_years",
    "audit_logs": "5_years", 
    "session_data": "1_year",
    "error_logs": "2_years"
}
```

#### Privacy Compliance
```python
# GDPR/Privacy compliance
PRIVACY_SETTINGS = {
    "data_anonymization": True,
    "right_to_deletion": True,
    "consent_tracking": True,
    "data_export": True
}
```

### 2. Security Standards

#### Compliance Frameworks
- **PCI DSS**: Payment card data security
- **SOX**: Financial reporting controls
- **GDPR**: Personal data protection
- **ISO 27001**: Information security management

#### Security Assessments
```bash
# Regular security assessments
- Penetration testing (quarterly)
- Vulnerability scanning (monthly)
- Code security review (per release)
- Infrastructure audit (semi-annually)
```

## 📋 Security Checklist

### Pre-Deployment Security Audit

#### ✅ Configuration Security
- [ ] No hardcoded credentials
- [ ] Environment variables properly secured
- [ ] SSL/TLS configured correctly
- [ ] Rate limiting enabled
- [ ] Input validation implemented

#### ✅ Access Control
- [ ] Authentication required for all endpoints
- [ ] Role-based permissions configured
- [ ] JWT tokens properly configured
- [ ] Session management implemented

#### ✅ Network Security
- [ ] Firewall rules configured
- [ ] VPN/private network setup
- [ ] DDoS protection enabled
- [ ] Network monitoring active

#### ✅ Monitoring & Logging
- [ ] Security event logging enabled
- [ ] Audit trail implementation
- [ ] Automated alerting configured
- [ ] Log retention policies set

#### ✅ Data Protection
- [ ] Data encryption at rest
- [ ] Data encryption in transit
- [ ] Secure backup procedures
- [ ] Data retention compliance

### Post-Deployment Security Monitoring

#### Daily Checks
```bash
# Monitor for security events
grep "security" /var/log/mt5-bridge/app.log | tail -100

# Check failed authentication attempts
grep "authentication_failure" /var/log/mt5-bridge/security.log

# Monitor unusual trading patterns
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8001/security/unusual-activity
```

#### Weekly Reviews
```bash
# Review security metrics
GET /security/weekly-report

# Check certificate expiration
openssl x509 -in mt5-bridge.crt -noout -dates

# Update security patches
docker pull mt5-bridge:latest-security-patch
```

## 🆘 Emergency Contacts

### Security Incident Response Team
- **Primary**: security@company.com
- **Secondary**: admin@company.com  
- **Emergency**: +1-800-SECURITY

### Compliance Officer
- **Email**: compliance@company.com
- **Phone**: +1-800-COMPLIANCE

---

## ⚠️ REMEMBER: Security is everyone's responsibility

**Report security concerns immediately:**
- Email: security@company.com
- Emergency hotline: +1-800-SECURITY
- Internal security portal: https://security.company.com

**Never ignore potential security issues - when in doubt, report it!**