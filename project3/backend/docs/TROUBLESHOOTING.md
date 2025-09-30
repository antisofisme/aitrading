# 🔧 Troubleshooting Guide

## Configuration Issues

### Environment Variables Not Loading

**Symptoms:**
- Services fail to start with "Environment variable not found" errors
- Configuration resolution fails in Central Hub
- Database connection errors with default values

**Diagnosis:**
```bash
# Check if .env file exists and has correct permissions
ls -la .env

# Validate .env file syntax
cat .env | grep -E "^[A-Z].*=" | head -10

# Check for missing equals signs
cat .env | grep -E "^[A-Z]" | grep -v "="

# Verify environment variables are loaded in container
docker exec suho-api-gateway env | grep POSTGRES_HOST
```

**Solutions:**
```bash
# Fix .env file syntax
# Remove spaces around equals sign
# WRONG: POSTGRES_HOST = suho-postgresql
# CORRECT: POSTGRES_HOST=suho-postgresql

# Restart services after .env changes
docker-compose restart central-hub api-gateway

# Rebuild if environment variables are built into image
docker-compose build --no-cache api-gateway central-hub
```

### Central Hub Configuration Resolution Errors

**Symptoms:**
- API Gateway fails to get config from Central Hub
- "ENV:VARIABLE_NAME not found" errors in Central Hub logs
- Services using fallback/default values instead of configured values

**Diagnosis:**
```bash
# Check Central Hub health
curl http://localhost:7000/health

# Test configuration API directly
curl -X POST http://localhost:7000/config \
  -H "Content-Type: application/json" \
  -d '{"service_name": "api-gateway"}'

# Check Central Hub logs for resolution errors
docker logs suho-central-hub | grep "ENV:"
```

**Solutions:**
```bash
# Ensure required environment variables are set
docker exec suho-central-hub env | grep POSTGRES_PASSWORD

# Verify static config files use correct ENV: syntax
cat 01-core-infrastructure/central-hub/shared/static/database/postgresql.json

# Restart Central Hub if environment variables were added
docker-compose restart central-hub
```

## Service Connectivity Issues

### Services Can't Connect to Each Other

**Symptoms:**
- "Connection refused" errors
- Services connecting to localhost instead of Docker service names
- Network timeouts between services

**Diagnosis:**
```bash
# Check Docker network
docker network inspect suho-network

# Test inter-service connectivity
docker exec suho-api-gateway ping suho-postgresql
docker exec suho-api-gateway ping suho-central-hub

# Check if services are using correct hostnames
docker logs suho-api-gateway | grep "localhost\|127.0.0.1"
```

**Solutions:**
```bash
# Fix hardcoded localhost references
# Replace 'localhost' with Docker service names in configs

# Verify services are on same network
docker-compose ps

# Restart services with correct network configuration
docker-compose down && docker-compose up -d
```

### Database Connection Issues

**Symptoms:**
- "Connection refused" to database
- Authentication failures
- Timeout errors

**Diagnosis:**
```bash
# Check database container status
docker ps | grep postgres

# Check database logs
docker logs suho-postgresql

# Test database connectivity from API Gateway
docker exec suho-api-gateway nc -zv suho-postgresql 5432

# Verify database credentials
docker exec suho-postgresql psql -U suho_admin -d suho_trading -c "SELECT 1;"
```

**Solutions:**
```bash
# Check database credentials in .env
grep POSTGRES_ .env

# Restart database if configuration changed
docker-compose restart suho-postgresql

# Reset database volume if data is corrupted
docker-compose down -v
docker-compose up -d
```

## Messaging System Issues

### NATS Connection Problems

**Symptoms:**
- "Unable to connect to NATS" errors
- Configuration updates not propagating
- Real-time features not working

**Diagnosis:**
```bash
# Check NATS container status
docker ps | grep nats

# Test NATS connectivity
docker exec suho-api-gateway nc -zv suho-nats-server 4222

# Check NATS logs
docker logs suho-nats-server
```

**Solutions:**
```bash
# Verify NATS configuration
grep NATS_ .env

# Restart NATS service
docker-compose restart suho-nats-server

# Clear NATS data if needed
docker-compose down
docker volume rm suho_nats_data
docker-compose up -d
```

### Kafka Connection Problems

**Symptoms:**
- "KafkaJSConnectionError" messages
- Events not being published/consumed
- Connection to localhost:9092 instead of suho-kafka:9092

**Diagnosis:**
```bash
# Check Kafka container status
docker ps | grep kafka

# Test Kafka connectivity
docker exec suho-api-gateway nc -zv suho-kafka 9092

# Check Kafka logs for connection issues
docker logs suho-kafka | grep ERROR

# Verify Kafka configuration
docker exec suho-kafka kafka-topics.sh --bootstrap-server localhost:9092 --list
```

**Solutions:**
```bash
# Fix localhost references in Kafka configuration
grep -r "localhost:9092" 01-core-infrastructure/

# Update advertised listeners in docker-compose.yml
# Remove localhost from KAFKA_ADVERTISED_LISTENERS

# Restart Kafka with fresh data
docker-compose down
docker volume rm suho_kafka_data
docker-compose up -d suho-zookeeper suho-kafka
```

## Performance Issues

### Slow Configuration Loading

**Symptoms:**
- Services take long time to start
- Configuration API responses are slow
- Timeouts during service initialization

**Diagnosis:**
```bash
# Check Central Hub response time
time curl http://localhost:7000/health

# Monitor Central Hub CPU/memory usage
docker stats suho-central-hub

# Check for config file parsing errors
docker logs suho-central-hub | grep "parsing\|loading"
```

**Solutions:**
```bash
# Optimize static config files (remove unnecessary data)
# Cache frequently accessed configurations
# Reduce config file sizes

# Restart Central Hub
docker-compose restart central-hub
```

### High Memory Usage

**Symptoms:**
- Services consuming excessive memory
- Out of memory errors
- System becoming unresponsive

**Diagnosis:**
```bash
# Check container memory usage
docker stats

# Check system memory
free -h

# Identify memory leaks in logs
docker logs suho-api-gateway | grep "memory\|heap"
```

**Solutions:**
```bash
# Restart memory-intensive services
docker-compose restart api-gateway central-hub

# Optimize configuration caching
# Review and optimize service resource limits

# Clean up unused Docker resources
docker system prune -f
```

## Docker and Container Issues

### Container Restart Loops

**Symptoms:**
- Services constantly restarting
- "Container exited with code X" messages
- Services never reach healthy state

**Diagnosis:**
```bash
# Check container status
docker-compose ps

# Check exit codes and restart counts
docker ps -a

# Examine container logs for exit reasons
docker logs suho-api-gateway --tail 50
```

**Solutions:**
```bash
# Fix configuration issues causing exits
# Check dependencies are available before service starts
# Add health checks with appropriate timeouts

# Restart with fresh containers
docker-compose down
docker-compose up --force-recreate -d
```

### Build Issues

**Symptoms:**
- Docker build failures
- "npm install" errors during build
- Missing dependencies in containers

**Diagnosis:**
```bash
# Check build logs
docker-compose build api-gateway 2>&1 | tee build.log

# Verify Dockerfile syntax
docker build -t test-api-gateway 01-core-infrastructure/api-gateway/

# Check for network issues during build
docker build --no-cache 01-core-infrastructure/api-gateway/
```

**Solutions:**
```bash
# Clear Docker build cache
docker builder prune -f

# Update package.json if dependencies changed
# Fix Dockerfile syntax errors

# Rebuild from scratch
docker-compose build --no-cache --pull
```

## Development Environment Issues

### Hot Reload Not Working

**Symptoms:**
- Code changes not reflected immediately
- Need manual restarts for changes
- File watching not working

**Diagnosis:**
```bash
# Check hot reload settings
grep HOT_RELOAD .env

# Verify file mounting in docker-compose.yml
docker-compose config | grep volumes

# Check file permissions
ls -la 01-core-infrastructure/api-gateway/
```

**Solutions:**
```bash
# Enable hot reload in .env
HOT_RELOAD_ENABLED=true

# Ensure proper volume mounting
# Fix file permissions if needed

# Restart services with new configuration
docker-compose restart api-gateway
```

### Permission Issues

**Symptoms:**
- "Permission denied" errors
- Unable to write to mounted volumes
- File creation failures

**Diagnosis:**
```bash
# Check file permissions
ls -la .env
ls -la 01-core-infrastructure/

# Check user in container
docker exec suho-api-gateway whoami
docker exec suho-api-gateway id
```

**Solutions:**
```bash
# Fix file permissions
chmod 644 .env
chown -R 1000:1000 01-core-infrastructure/

# Update Dockerfile USER directive if needed
# Ensure consistent user/group IDs
```

## Emergency Procedures

### Complete System Reset

When multiple issues occur simultaneously:

```bash
# 1. Stop all services
docker-compose down

# 2. Remove all volumes (CAUTION: This deletes all data)
docker volume prune -f

# 3. Remove all containers
docker container prune -f

# 4. Remove all networks
docker network prune -f

# 5. Rebuild everything from scratch
docker-compose build --no-cache --pull

# 6. Start services
docker-compose up -d

# 7. Verify health
curl http://localhost:7000/health
curl http://localhost:8000/health
```

### Configuration Rollback

If new configuration causes issues:

```bash
# 1. Restore previous .env file
cp .env.backup .env

# 2. Restart affected services
docker-compose restart central-hub api-gateway

# 3. Verify system is working
curl http://localhost:7000/health
```

### Log Collection for Support

Collect comprehensive logs for debugging:

```bash
# Create log collection directory
mkdir -p debug-logs/$(date +%Y%m%d_%H%M%S)
cd debug-logs/$(date +%Y%m%d_%H%M%S)

# Collect service logs
docker logs suho-central-hub > central-hub.log 2>&1
docker logs suho-api-gateway > api-gateway.log 2>&1
docker logs suho-postgresql > postgresql.log 2>&1
docker logs suho-kafka > kafka.log 2>&1
docker logs suho-nats-server > nats.log 2>&1

# Collect system information
docker-compose config > docker-compose-resolved.yml
docker ps -a > containers.txt
docker network ls > networks.txt
docker volume ls > volumes.txt
cp ../../.env env-file.txt

# Create summary
echo "System Debug Information - $(date)" > README.txt
echo "Issue Description: [DESCRIBE ISSUE HERE]" >> README.txt
```

---

**Emergency Contact**: Check project documentation for support channels
**Last Updated**: 2024
**Version**: 1.0.0