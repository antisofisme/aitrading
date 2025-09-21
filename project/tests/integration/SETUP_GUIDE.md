# LEVEL 1 Foundation Setup Guide

This guide helps you set up and validate the LEVEL 1 Foundation services for the AI Trading Platform.

## Current Status

✅ **Test Suite Created** - Comprehensive integration tests ready
✅ **Configuration Validated** - All config files and structure correct
✅ **Backend Structure** - All 4 foundation services present
❌ **Services Running** - Services need to be started
❌ **Database Setup** - PostgreSQL databases need configuration

## Foundation Score: 7%

The foundation structure is correct but services need to be started and configured.

## Quick Setup

### 1. Start PostgreSQL

```bash
# Install PostgreSQL (if not installed)
sudo apt-get install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create databases
sudo -u postgres psql -c "CREATE DATABASE aitrading_main;"
sudo -u postgres psql -c "CREATE DATABASE aitrading_auth;"
sudo -u postgres psql -c "CREATE DATABASE aitrading_trading;"
sudo -u postgres psql -c "CREATE DATABASE aitrading_market;"
sudo -u postgres psql -c "CREATE DATABASE aitrading_analytics;"

# Create user (optional)
sudo -u postgres psql -c "CREATE USER aitrading WITH PASSWORD 'aitrading123';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON ALL DATABASES TO aitrading;"
```

### 2. Set Environment Variables

```bash
# Add to ~/.bashrc or create .env file
export NODE_ENV=development
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=postgres
export DB_PASSWORD=postgres
export GATEWAY_PORT=3001
export CENTRAL_HUB_URL=http://localhost:7000
```

### 3. Start Foundation Services

```bash
# Terminal 1 - API Gateway (Port 3001)
cd /mnt/f/WINDSURF/neliti_code/aitrading/project/backend/api-gateway
npm install
npm start

# Terminal 2 - Database Service (Port 8008)
cd /mnt/f/WINDSURF/neliti_code/aitrading/project/backend/database-service
npm install
npm start

# Terminal 3 - Data Bridge (Port 5001)
cd /mnt/f/WINDSURF/neliti_code/aitrading/project/backend/data-bridge
npm install
npm start

# Terminal 4 - Central Hub (Port 7000)
cd /mnt/f/WINDSURF/neliti_code/aitrading/project/backend/central-hub
npm install
npm start
```

### 4. Validate Foundation

```bash
# Quick validation
cd /mnt/f/WINDSURF/neliti_code/aitrading/project/tests/integration
node validate-foundation.js

# Full integration tests
npm test

# Individual service tests
npm run test:api-gateway
npm run test:database
npm run test:central-hub
```

## Expected Ports

- **API Gateway**: 3001
- **Database Service**: 8008
- **Data Bridge**: 5001
- **Central Hub**: 7000
- **PostgreSQL**: 5432

## Validation Targets

- **Foundation Score**: 90%+ (Ready for LEVEL 2)
- **Critical Services**: All healthy
- **Database Connections**: All 5 connected
- **Configuration**: Valid and complete

## Troubleshooting

### Port Conflicts
```bash
# Check what's using a port
sudo lsof -i :3001
sudo lsof -i :8008
sudo lsof -i :5001
sudo lsof -i :7000

# Kill process using port
sudo kill -9 <PID>
```

### Database Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Connect to PostgreSQL
sudo -u postgres psql

# List databases
\l

# Check connections
SELECT * FROM pg_stat_activity;
```

### Service Issues
```bash
# Check service logs
cd backend/[service-name]
npm run dev  # Development mode with logs

# Check if service files exist
ls -la src/server.js
ls -la package.json
```

## Testing Strategy

1. **Start with Configuration** - Validate all config files exist
2. **Setup Databases** - Create and test all 5 PostgreSQL databases
3. **Start Services One by One** - Begin with API Gateway, then Database Service
4. **Test Each Service** - Validate individually before full integration
5. **Run Full Test Suite** - Complete validation with orchestrator

## Success Criteria

✅ **API Gateway** - Healthy on port 3001, auth system ready
✅ **Database Service** - Healthy on port 8008, all 5 DBs connected
✅ **Data Bridge** - Healthy on port 5001, WebSocket functional
✅ **Central Hub** - Healthy on port 7000, service discovery working
✅ **Configuration** - All environment variables and configs valid

## Next Steps

Once LEVEL 1 Foundation achieves 90%+ score:

1. **LEVEL 2 Connectivity** - Service integration and data flow
2. **LEVEL 3 Intelligence** - AI model integration
3. **LEVEL 4 Trading** - Trading engine implementation
4. **LEVEL 5 Production** - Deployment and monitoring

---

**Current Status**: Foundation structure ready, services need startup and configuration.
**Estimated Setup Time**: 30-45 minutes
**Validation Tool**: `node validate-foundation.js`