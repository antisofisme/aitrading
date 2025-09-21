# Web Dashboard Installation Guide

Complete guide for deploying the responsive web dashboard for analysis, monitoring, and multi-user management.

## Prerequisites

### System Requirements

#### Development Environment
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 5GB free space
- **CPU**: 2 cores minimum, 4 cores recommended
- **Network**: Stable internet connection

#### Production Environment
- **Memory**: 16GB RAM minimum, 32GB recommended
- **Storage**: 50GB SSD storage
- **CPU**: 4 cores minimum, 8 cores recommended
- **Network**: High-bandwidth connection with CDN support

### Software Requirements

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Git**: Latest version
- **SSL Certificate**: For production deployment
- **Domain Name**: For production deployment

## Step 1: Environment Setup

### Install Docker and Dependencies

#### Ubuntu/Debian
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker-compose --version
```

#### CentOS/RHEL
```bash
# Install Docker
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io
sudo systemctl start docker
sudo systemctl enable docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
```

#### Windows
```powershell
# Install Docker Desktop from https://docker.com/get-started
# Or using Chocolatey
choco install docker-desktop -y

# Verify installation
docker --version
docker-compose --version
```

### Clone Repository

```bash
# Navigate to installation directory
cd /opt  # Linux/macOS
# or cd C:\ # Windows

# Clone repository
git clone https://github.com/your-org/ai-trading-platform.git
cd ai-trading-platform

# Set proper permissions (Linux/macOS)
sudo chown -R $USER:$USER .
chmod +x scripts/*.sh
```

## Step 2: Configuration

### Environment Configuration

```bash
# Copy environment template
cp .env.example .env.web

# Generate secure secrets
openssl rand -hex 32  # For JWT_SECRET
openssl rand -hex 32  # For ENCRYPTION_KEY
openssl rand -base64 32  # For REDIS_PASSWORD
```

### Edit Environment Variables

```bash
# Edit configuration
nano .env.web  # or vim .env.web
```

#### Basic Configuration
```bash
# Application Configuration
NODE_ENV=production
APP_VERSION=1.0.0
DOMAIN=yourdomain.com
API_BASE_URL=https://api.yourdomain.com

# Database Configuration
POSTGRES_DB=aitrading_web
POSTGRES_USER=aitrading
POSTGRES_PASSWORD=your_secure_database_password
DATABASE_URL=postgresql://aitrading:your_secure_database_password@postgres-main:5432/aitrading_web

# ClickHouse Configuration
CLICKHOUSE_DB=aitrading_analytics
CLICKHOUSE_USER=aitrading
CLICKHOUSE_PASSWORD=your_clickhouse_password

# Redis Configuration
REDIS_PASSWORD=your_redis_password
REDIS_URL=redis://:your_redis_password@redis-cache:6379

# Security Configuration
JWT_SECRET=your_32_character_jwt_secret_key
ENCRYPTION_KEY=your_32_character_encryption_key
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Payment Configuration (Midtrans for Indonesia)
MIDTRANS_SERVER_KEY=your_midtrans_server_key
MIDTRANS_CLIENT_KEY=your_midtrans_client_key
MIDTRANS_ENVIRONMENT=production  # or sandbox

# International Payments (Stripe)
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM=noreply@yourdomain.com

# SSL Configuration
SSL_CERT_PATH=/etc/ssl/certs/yourdomain.com.crt
SSL_KEY_PATH=/etc/ssl/private/yourdomain.com.key
```

#### Advanced Configuration
```bash
# Performance Configuration
DB_POOL_SIZE=20
DB_CONNECTION_TIMEOUT=5000
REDIS_MAX_MEMORY=2gb
CLICKHOUSE_MAX_MEMORY=4gb

# Analytics Configuration
ANALYTICS_RETENTION_DAYS=730
REAL_TIME_ANALYTICS=true
DATA_EXPORT_ENABLED=true

# Security Configuration
SESSION_TIMEOUT=15m
REFRESH_TOKEN_EXPIRY=7d
MFA_ENABLED=true
PASSWORD_MIN_LENGTH=12

# Rate Limiting
RATE_LIMIT_WEB_USER=1000
RATE_LIMIT_WEB_ANONYMOUS=100
RATE_LIMIT_API_USER=500

# Monitoring Configuration
PROMETHEUS_ENABLED=true
GRAFANA_ADMIN_PASSWORD=your_grafana_password
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=90
```

## Step 3: SSL Certificate Setup

### Option 1: Let's Encrypt (Free)

```bash
# Install Certbot
sudo apt install certbot

# Generate certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./docker/web/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./docker/web/ssl/key.pem

# Set proper permissions
sudo chown $USER:$USER ./docker/web/ssl/*
chmod 600 ./docker/web/ssl/*
```

### Option 2: Commercial Certificate

```bash
# Create SSL directory
mkdir -p ./docker/web/ssl

# Copy your certificate files
cp your_certificate.crt ./docker/web/ssl/cert.pem
cp your_private_key.key ./docker/web/ssl/key.pem

# Set proper permissions
chmod 600 ./docker/web/ssl/*
```

### Option 3: Self-Signed (Development Only)

```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout ./docker/web/ssl/key.pem -out ./docker/web/ssl/cert.pem -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Set permissions
chmod 600 ./docker/web/ssl/*
```

## Step 4: Deployment Options

### Option 1: Web-Only Deployment (Recommended for Analysis)

```bash
# Deploy web dashboard only
docker-compose -f docker-compose.web-only.yml up -d

# Wait for all services to start
sleep 60

# Check service status
docker-compose -f docker-compose.web-only.yml ps

# View logs
docker-compose -f docker-compose.web-only.yml logs -f web-dashboard
```

### Option 2: Full Production Deployment

```bash
# Deploy all services including backend
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Option 3: Development Deployment

```bash
# Deploy in development mode
docker-compose -f docker-compose.dev.yml up -d

# Access development environment
echo "Web Dashboard: http://localhost:3000"
echo "API Gateway: http://localhost:8000"
echo "Database Admin: http://localhost:8080"
```

## Step 5: Initial Setup

### Database Initialization

```bash
# Wait for database to be ready
docker-compose exec postgres-main pg_isready -U aitrading

# Run database migrations
docker-compose exec web-dashboard npm run db:migrate

# Seed initial data
docker-compose exec web-dashboard npm run db:seed

# Create admin user
docker-compose exec web-dashboard npm run user:create-admin
```

### Verify Installation

```bash
# Check all services are running
docker-compose ps

# Test web dashboard
curl -k https://localhost/health

# Test API gateway
curl -k https://localhost/api/health

# Test database connection
docker-compose exec postgres-main psql -U aitrading -d aitrading_web -c "SELECT version();"
```

## Step 6: Configure Load Balancer (Production)

### Nginx Configuration

Create `/etc/nginx/sites-available/aitrading`:

```nginx
upstream web_dashboard {
    server localhost:3000;
}

upstream api_gateway {
    server localhost:8000;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS configuration
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/yourdomain.com.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.com.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header Referrer-Policy "strict-origin-when-cross-origin";

    # Web Dashboard
    location / {
        proxy_pass http://web_dashboard;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # API Gateway
    location /api/ {
        proxy_pass http://api_gateway/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket Support
    location /ws/ {
        proxy_pass http://localhost:8001/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/aitrading /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Step 7: Monitoring Setup

### Prometheus Configuration

```bash
# Access Prometheus
echo "Prometheus: http://localhost:9090"

# Access Grafana
echo "Grafana: http://localhost:3001"
echo "Username: admin"
echo "Password: ${GRAFANA_ADMIN_PASSWORD}"
```

### Import Grafana Dashboards

```bash
# Import pre-configured dashboards
docker-compose exec grafana grafana-cli plugins install grafana-worldmap-panel
docker-compose exec grafana grafana-cli plugins install grafana-piechart-panel

# Restart Grafana to load plugins
docker-compose restart grafana
```

## Step 8: Backup and Recovery

### Setup Automated Backups

```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/aitrading"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
docker-compose exec -T postgres-main pg_dump -U aitrading aitrading_web > $BACKUP_DIR/database_$DATE.sql

# Backup volumes
docker run --rm -v aitrading_postgres-data:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/postgres_data_$DATE.tar.gz -C /data .
docker run --rm -v aitrading_redis-data:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/redis_data_$DATE.tar.gz -C /data .

# Backup configuration
cp -r .env.web docker-compose*.yml $BACKUP_DIR/config_$DATE/

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
EOF

chmod +x backup.sh

# Setup daily backup cron job
echo "0 2 * * * /opt/ai-trading-platform/backup.sh" | sudo crontab -
```

### Recovery Procedure

```bash
# Stop services
docker-compose down

# Restore database
docker-compose up -d postgres-main
sleep 30
cat backup/database_YYYYMMDD_HHMMSS.sql | docker-compose exec -T postgres-main psql -U aitrading -d aitrading_web

# Restore volumes
docker run --rm -v aitrading_postgres-data:/data -v ./backup:/backup alpine tar xzf /backup/postgres_data_YYYYMMDD_HHMMSS.tar.gz -C /data
docker run --rm -v aitrading_redis-data:/data -v ./backup:/backup alpine tar xzf /backup/redis_data_YYYYMMDD_HHMMSS.tar.gz -C /data

# Start all services
docker-compose up -d
```

## Step 9: Performance Optimization

### Database Optimization

```bash
# Optimize PostgreSQL
docker-compose exec postgres-main psql -U aitrading -d aitrading_web -c "
  ALTER SYSTEM SET shared_buffers = '256MB';
  ALTER SYSTEM SET effective_cache_size = '1GB';
  ALTER SYSTEM SET maintenance_work_mem = '64MB';
  ALTER SYSTEM SET checkpoint_completion_target = 0.9;
  ALTER SYSTEM SET wal_buffers = '16MB';
  ALTER SYSTEM SET default_statistics_target = 100;
  SELECT pg_reload_conf();
"

# Optimize ClickHouse
docker-compose exec clickhouse-analytics clickhouse-client --query "
  SET max_memory_usage = 4000000000;
  SET max_threads = 4;
  SET max_execution_time = 300;
"
```

### Web Server Optimization

```bash
# Enable Redis persistence
docker-compose exec redis-cache redis-cli CONFIG SET save "900 1 300 10 60 10000"

# Optimize Nginx (if using external Nginx)
sudo nano /etc/nginx/nginx.conf
```

Add to nginx.conf:
```nginx
worker_processes auto;
worker_connections 1024;

http {
    # Enable gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss application/atom+xml image/svg+xml;

    # Enable caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## Step 10: Security Hardening

### Firewall Configuration

```bash
# Ubuntu/Debian
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22      # SSH
sudo ufw allow 80      # HTTP
sudo ufw allow 443     # HTTPS
sudo ufw enable

# CentOS/RHEL
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### Security Updates

```bash
# Setup automatic security updates
cat > update-system.sh << 'EOF'
#!/bin/bash
# Update system packages
apt update && apt upgrade -y

# Update Docker images
docker-compose pull
docker-compose up -d

# Clean up old images
docker image prune -f

echo "System updated: $(date)"
EOF

chmod +x update-system.sh

# Schedule weekly updates
echo "0 3 * * 0 /opt/ai-trading-platform/update-system.sh" | sudo crontab -
```

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check Docker daemon
sudo systemctl status docker

# Check resource usage
docker system df
docker system prune -f

# Check logs
docker-compose logs service-name
```

#### Database Connection Issues
```bash
# Check database status
docker-compose exec postgres-main pg_isready -U aitrading

# Reset database connection
docker-compose restart postgres-main
sleep 30
docker-compose restart web-dashboard
```

#### SSL Certificate Issues
```bash
# Check certificate validity
openssl x509 -in ./docker/web/ssl/cert.pem -text -noout

# Renew Let's Encrypt certificate
sudo certbot renew
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./docker/web/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./docker/web/ssl/key.pem
docker-compose restart nginx
```

### Performance Issues
```bash
# Check resource usage
docker stats

# Monitor database performance
docker-compose exec postgres-main psql -U aitrading -d aitrading_web -c "SELECT * FROM pg_stat_activity;"

# Check Redis performance
docker-compose exec redis-cache redis-cli info stats
```

## Support and Resources

### Access URLs

After successful installation:
- **Web Dashboard**: https://yourdomain.com
- **API Documentation**: https://yourdomain.com/api/docs
- **Admin Panel**: https://yourdomain.com/admin
- **Monitoring**: https://yourdomain.com/grafana

### Support Channels

- **Documentation**: [docs.aitrading.com](https://docs.aitrading.com)
- **Discord Community**: [discord.gg/aitrading](https://discord.gg/aitrading)
- **Email Support**: support@aitrading.com
- **Enterprise Support**: enterprise@aitrading.com

---

**🚀 Your web dashboard is now ready for multi-user trading analytics and monitoring!**