# MT5 Bridge Deployment & Monitoring Guide

## 🚀 Deployment Overview

This guide provides comprehensive deployment procedures for the MT5 Bridge Microservice, covering development, staging, and production environments with Docker, Kubernetes, and monitoring setup.

**Deployment Environments:**
- **Development**: Local Docker containers for development and testing
- **Staging**: Docker Compose with production-like configuration
- **Production**: Kubernetes cluster with high availability and scaling

## 📋 Prerequisites

### **System Requirements**

| Environment | CPU | Memory | Storage | Network |
|-------------|-----|--------|---------|---------|
| **Development** | 1 CPU | 512MB | 2GB | 1 Gbps |
| **Staging** | 2 CPU | 1GB | 10GB | 1 Gbps |
| **Production** | 4 CPU | 2GB | 50GB | 10 Gbps |

### **Software Dependencies**

#### **Required Software**
- **Docker**: 20.10+ (with Docker Compose v2)
- **Kubernetes**: 1.24+ (for production)
- **Python**: 3.11+ (for local development)
- **Git**: Latest version
- **curl/wget**: For health checks

#### **Platform-Specific Requirements**

**Windows (Production Trading)**:
```powershell
# MetaTrader 5 Terminal (required for production)
# Download from: https://www.metatrader5.com/
# Minimum version: Build 3550+

# Windows-specific dependencies
pip install MetaTrader5
```

**Linux/WSL (Development)**:
```bash
# Mock MT5 implementation (automatic fallback)
# No additional requirements
```

### **Network Requirements**

```
┌─────────────────────────────────────────────────────────────┐
│                    Network Architecture                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Internet                                                    │
│    │                                                        │
│    ▼                                                        │
│ ┌─────────────┐                                             │
│ │    Nginx    │ ── Port 80/443 (HTTP/HTTPS)               │
│ │Load Balancer│                                             │
│ └─────────────┘                                             │
│    │                                                        │
│    ▼                                                        │
│ ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│ │ MT5-Bridge  │  │ MT5-Bridge  │  │ MT5-Bridge  │          │
│ │Instance #1  │  │Instance #2  │  │Instance #3  │          │
│ │  Port:8001  │  │  Port:8002  │  │  Port:8003  │          │
│ └─────────────┘  └─────────────┘  └─────────────┘          │
│    │                 │                 │                   │
│    └─────────────────┼─────────────────┘                   │
│                      │                                     │
│                      ▼                                     │
│               ┌─────────────┐                              │
│               │  MT5 Server │ ── MetaTrader 5 Terminal    │
│               │ Connection  │                              │
│               └─────────────┘                              │
└─────────────────────────────────────────────────────────────┘
```

**Required Ports**:
- **8001**: HTTP/WebSocket API (configurable)
- **9001**: Metrics endpoint (optional)
- **MT5 Ports**: As configured by MetaTrader 5 terminal

## 🔧 Development Deployment

### **Local Development Setup**

#### **1. Environment Preparation**
```bash
# Clone repository
git clone https://github.com/your-org/mt5-bridge.git
cd mt5-bridge

# Create environment file
cp .env.example .env

# Configure environment variables
cat > .env << EOF
# MT5 Configuration
MT5_SERVER=Demo-Server
MT5_LOGIN=12345
MT5_PASSWORD=demo_password

# Service Configuration
MT5_BRIDGE_PORT=8001
LOG_LEVEL=DEBUG
REDIS_URL=redis://localhost:6379

# Development flags
ENVIRONMENT=development
ENABLE_PROFILING=true
WEBSOCKET_DEBUG=true
EOF
```

#### **2. Docker Development Deployment**
```bash
# Build development image
docker-compose -f docker-compose.dev.yml build

# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# Verify deployment
curl http://localhost:8001/health

# View logs
docker-compose -f docker-compose.dev.yml logs -f mt5-bridge
```

**Development Docker Compose**:
```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  mt5-bridge:
    build:
      context: .
      dockerfile: Dockerfile
      target: development
    ports:
      - "8001:8001"
      - "9001:9001"  # Metrics port
    environment:
      - ENVIRONMENT=development
      - LOG_LEVEL=DEBUG
      - ENABLE_PROFILING=true
      - WEBSOCKET_DEBUG=true
    volumes:
      - .:/app  # Hot reload
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:

networks:
  default:
    name: mt5-bridge-dev
```

#### **3. Development Testing**
```bash
# Run comprehensive tests
python test_mt5_bridge.py

# Test specific endpoints
curl http://localhost:8001/health
curl http://localhost:8001/status
curl http://localhost:8001/performance/metrics

# Test WebSocket connection
wscat -c ws://localhost:8001/websocket/ws
```

## 🎭 Staging Deployment

### **Staging Environment Setup**

#### **1. Staging Configuration**
```bash
# Create staging environment file
cat > .env.staging << EOF
# MT5 Configuration
MT5_SERVER=Staging-Server
MT5_LOGIN=${STAGING_MT5_LOGIN}
MT5_PASSWORD=${STAGING_MT5_PASSWORD}

# Service Configuration
MT5_BRIDGE_PORT=8001
LOG_LEVEL=INFO
REDIS_URL=redis://redis:6379

# Staging flags
ENVIRONMENT=staging
ENABLE_PROFILING=false
RATE_LIMITING=true
MAX_CONNECTIONS=50
EOF
```

#### **2. Staging Docker Deployment**
```yaml
# docker-compose.staging.yml
version: '3.8'

services:
  mt5-bridge:
    image: mt5-bridge:staging
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    ports:
      - "8001:8001"
    environment:
      - ENVIRONMENT=staging
      - LOG_LEVEL=INFO
      - MAX_CONNECTIONS=50
    env_file:
      - .env.staging
    depends_on:
      - redis
      - monitoring
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    resources:
      limits:
        memory: 1G
        cpus: '2.0'
      reservations:
        memory: 512M
        cpus: '1.0'

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/staging.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - mt5-bridge
    restart: unless-stopped

  monitoring:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    restart: unless-stopped

volumes:
  redis_data:

networks:
  default:
    name: mt5-bridge-staging
```

#### **3. Staging Nginx Configuration**
```nginx
# nginx/staging.conf
events {
    worker_connections 1024;
}

http {
    upstream mt5_bridge {
        server mt5-bridge:8001 max_fails=3 fail_timeout=30s;
    }

    server {
        listen 80;
        server_name staging-mt5-bridge.company.com;

        location / {
            proxy_pass http://mt5_bridge;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket specific settings
            proxy_cache_bypass $http_upgrade;
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        location /health {
            proxy_pass http://mt5_bridge;
            access_log off;
        }
    }
}
```

#### **4. Staging Deployment Script**
```bash
#!/bin/bash
# deploy_staging.sh

set -e

echo "🎭 Staging Deployment Started"
echo "=============================="

# Environment validation
if [ -z "$STAGING_MT5_LOGIN" ]; then
    echo "❌ STAGING_MT5_LOGIN not set"
    exit 1
fi

# Build staging image
echo "📦 Building staging image..."
docker build -t mt5-bridge:staging .

# Deploy staging environment
echo "🚀 Deploying staging environment..."
docker-compose -f docker-compose.staging.yml down
docker-compose -f docker-compose.staging.yml up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 30

# Health check
echo "🏥 Running health checks..."
for i in {1..5}; do
    if curl -f http://localhost:8001/health; then
        echo "✅ Staging deployment successful"
        exit 0
    fi
    echo "⏳ Retrying health check ($i/5)..."
    sleep 10
done

echo "❌ Staging deployment failed"
docker-compose -f docker-compose.staging.yml logs
exit 1
```

## 🏭 Production Deployment

### **Kubernetes Production Deployment**

#### **1. Kubernetes Namespace**
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: mt5-bridge
  labels:
    name: mt5-bridge
    environment: production
```

#### **2. Configuration Management**
```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mt5-bridge-config
  namespace: mt5-bridge
data:
  MT5_SERVER: "FBS-Real"
  LOG_LEVEL: "WARNING"
  ENVIRONMENT: "production"
  MAX_CONNECTIONS: "100"
  REDIS_URL: "redis://redis-service:6379"
  WEBSOCKET_PORT: "8001"
  METRICS_PORT: "9001"
```

```yaml
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: mt5-bridge-secrets
  namespace: mt5-bridge
type: Opaque
data:
  # Base64 encoded values
  MT5_LOGIN: <base64-encoded-login>
  MT5_PASSWORD: <base64-encoded-password>
  API_SECRET_KEY: <base64-encoded-api-key>
```

#### **3. Deployment Configuration**
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mt5-bridge-deployment
  namespace: mt5-bridge
  labels:
    app: mt5-bridge
    version: v1.0.0
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
  selector:
    matchLabels:
      app: mt5-bridge
  template:
    metadata:
      labels:
        app: mt5-bridge
        version: v1.0.0
    spec:
      containers:
      - name: mt5-bridge
        image: your-registry/mt5-bridge:1.0.0
        ports:
        - containerPort: 8001
          name: http
        - containerPort: 9001
          name: metrics
        env:
        - name: MT5_LOGIN
          valueFrom:
            secretKeyRef:
              name: mt5-bridge-secrets
              key: MT5_LOGIN
        - name: MT5_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mt5-bridge-secrets
              key: MT5_PASSWORD
        envFrom:
        - configMapRef:
            name: mt5-bridge-config
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 60
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "curl -X POST http://localhost:8001/shutdown"]
      terminationGracePeriodSeconds: 60
      restartPolicy: Always
```

#### **4. Service Configuration**
```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: mt5-bridge-service
  namespace: mt5-bridge
  labels:
    app: mt5-bridge
spec:
  type: ClusterIP
  ports:
  - port: 8001
    targetPort: 8001
    protocol: TCP
    name: http
  - port: 9001
    targetPort: 9001
    protocol: TCP
    name: metrics
  selector:
    app: mt5-bridge
```

#### **5. Ingress Configuration**
```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: mt5-bridge-ingress
  namespace: mt5-bridge
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/websocket-services: "mt5-bridge-service"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - mt5-bridge.company.com
    secretName: mt5-bridge-tls
  rules:
  - host: mt5-bridge.company.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: mt5-bridge-service
            port:
              number: 8001
```

#### **6. Horizontal Pod Autoscaler**
```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mt5-bridge-hpa
  namespace: mt5-bridge
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mt5-bridge-deployment
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

#### **7. Production Deployment Script**
```bash
#!/bin/bash
# deploy_production.sh

set -e

echo "🏭 Production Deployment Started"
echo "================================="

# Prerequisites check
kubectl cluster-info > /dev/null || {
    echo "❌ Kubernetes cluster not accessible"
    exit 1
}

# Create namespace
echo "📁 Creating namespace..."
kubectl apply -f k8s/namespace.yaml

# Deploy secrets (encrypted in CI/CD)
echo "🔐 Deploying secrets..."
kubectl apply -f k8s/secret.yaml

# Deploy configuration
echo "⚙️ Deploying configuration..."
kubectl apply -f k8s/configmap.yaml

# Deploy application
echo "🚀 Deploying application..."
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml

# Wait for rollout
echo "⏳ Waiting for rollout to complete..."
kubectl rollout status deployment/mt5-bridge-deployment -n mt5-bridge --timeout=300s

# Verify deployment
echo "🏥 Running health checks..."
kubectl get pods -n mt5-bridge
kubectl get svc -n mt5-bridge
kubectl get ingress -n mt5-bridge

# Test endpoints
SERVICE_IP=$(kubectl get svc mt5-bridge-service -n mt5-bridge -o jsonpath='{.spec.clusterIP}')
kubectl run test-pod --rm -i --tty --image=curlimages/curl -- curl -f http://$SERVICE_IP:8001/health

echo "✅ Production deployment successful"
```

## 📊 Monitoring & Observability

### **Monitoring Stack Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                   Monitoring Architecture                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │
│ │   Grafana   │    │ Prometheus  │    │  AlertMgr   │       │
│ │ Dashboards  │◀───│   Metrics   │◀───│   Alerts    │       │
│ │             │    │ Collection  │    │             │       │
│ └─────────────┘    └─────────────┘    └─────────────┘       │
│         │                   │                   │           │
│         ▼                   ▼                   ▼           │
│ ┌─────────────┐    ┌─────────────┐    ┌─────────────┐       │
│ │    Logs     │    │   Metrics   │    │ Notifications│       │
│ │ (ELK Stack) │    │ (Time Series│    │(Slack/Email) │       │
│ │             │    │  Database)  │    │             │       │
│ └─────────────┘    └─────────────┘    └─────────────┘       │
│         ▲                   ▲                   ▲           │
│         │                   │                   │           │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │              MT5 Bridge Services                        │ │
│ │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │ │
│ │  │   Service   │  │   Service   │  │   Service   │     │ │
│ │  │ Instance 1  │  │ Instance 2  │  │ Instance 3  │     │ │
│ │  └─────────────┘  └─────────────┘  └─────────────┘     │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### **Prometheus Configuration**
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'mt5-bridge'
    static_configs:
      - targets: ['mt5-bridge-service:9001']
    metrics_path: /metrics
    scrape_interval: 10s
    scrape_timeout: 5s

  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
            - mt5-bridge
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
```

### **Grafana Dashboard Configuration**
```json
{
  "dashboard": {
    "title": "MT5 Bridge Monitoring",
    "panels": [
      {
        "title": "Service Health",
        "type": "stat",
        "targets": [
          {
            "query": "up{job=\"mt5-bridge\"}",
            "legendFormat": "Instance {{instance}}"
          }
        ]
      },
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "query": "rate(http_requests_total[5m])",
            "legendFormat": "Requests/sec"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "query": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "WebSocket Connections",
        "type": "graph",
        "targets": [
          {
            "query": "websocket_active_connections",
            "legendFormat": "Active Connections"
          }
        ]
      },
      {
        "title": "Cache Performance",
        "type": "graph",
        "targets": [
          {
            "query": "cache_hit_rate_percent",
            "legendFormat": "Hit Rate %"
          }
        ]
      },
      {
        "title": "MT5 Connection Status",
        "type": "stat",
        "targets": [
          {
            "query": "mt5_connection_status",
            "legendFormat": "MT5 Connected"
          }
        ]
      }
    ]
  }
}
```

### **Alert Rules Configuration**
```yaml
# monitoring/alert_rules.yml
groups:
  - name: mt5-bridge-alerts
    rules:
      - alert: ServiceDown
        expr: up{job="mt5-bridge"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "MT5 Bridge service is down"
          description: "Service {{ $labels.instance }} has been down for more than 1 minute"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"

      - alert: MT5Disconnected
        expr: mt5_connection_status == 0
        for: 30s
        labels:
          severity: high
        annotations:
          summary: "MT5 connection lost"
          description: "MT5 terminal connection has been lost on {{ $labels.instance }}"

      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is above 90% on {{ $labels.instance }}"

      - alert: LowCacheHitRate
        expr: cache_hit_rate_percent < 70
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Low cache hit rate"
          description: "Cache hit rate is {{ $value }}% on {{ $labels.instance }}"
```

### **ELK Stack for Logging**
```yaml
# monitoring/elk-stack.yml
version: '3.8'

services:
  elasticsearch:
    image: elasticsearch:8.5.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - es_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"

  logstash:
    image: logstash:8.5.0
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline
    ports:
      - "5044:5044"
    depends_on:
      - elasticsearch

  kibana:
    image: kibana:8.5.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch

volumes:
  es_data:
```

### **Health Check Automation**
```bash
#!/bin/bash
# health_monitor.sh

ENDPOINTS=(
    "http://mt5-bridge.company.com/health"
    "http://mt5-bridge.company.com/websocket/ws/health"
    "http://mt5-bridge.company.com/performance/metrics"
)

SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"

check_endpoint() {
    local url=$1
    local name=$(echo $url | cut -d'/' -f3)
    
    if curl -f -s --max-time 10 "$url" > /dev/null; then
        echo "✅ $name: Healthy"
        return 0
    else
        echo "❌ $name: Unhealthy"
        
        # Send Slack notification
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"🚨 MT5 Bridge Health Alert: $name is unhealthy\"}" \
            "$SLACK_WEBHOOK"
        
        return 1
    fi
}

# Check all endpoints
failed_checks=0
for endpoint in "${ENDPOINTS[@]}"; do
    if ! check_endpoint "$endpoint"; then
        ((failed_checks++))
    fi
done

# Exit with error if any checks failed
if [ $failed_checks -gt 0 ]; then
    echo "❌ $failed_checks health check(s) failed"
    exit 1
else
    echo "✅ All health checks passed"
    exit 0
fi
```

## 🔄 CI/CD Pipeline

### **GitHub Actions Workflow**
```yaml
# .github/workflows/deploy.yml
name: Deploy MT5 Bridge

on:
  push:
    branches: [main]
    tags: ['v*']
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: mt5-bridge

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
          
      - name: Run tests
        run: |
          pytest tests/ --cov=src
          
  build:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v3
      
      - name: Log in to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
          
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            
      - name: Build and push Docker image
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: staging
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to staging
        run: |
          ./scripts/deploy_staging.sh
        env:
          STAGING_MT5_LOGIN: ${{ secrets.STAGING_MT5_LOGIN }}
          STAGING_MT5_PASSWORD: ${{ secrets.STAGING_MT5_PASSWORD }}

  deploy-production:
    needs: [build, deploy-staging]
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/v')
    environment: production
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure kubectl
        run: |
          echo "${{ secrets.KUBE_CONFIG }}" | base64 -d > kubeconfig
          export KUBECONFIG=kubeconfig
          
      - name: Deploy to production
        run: |
          ./scripts/deploy_production.sh
        env:
          PROD_MT5_LOGIN: ${{ secrets.PROD_MT5_LOGIN }}
          PROD_MT5_PASSWORD: ${{ secrets.PROD_MT5_PASSWORD }}
```

## 🔐 Security Configuration

### **Production Security Checklist**

#### **✅ Pre-Deployment Security**
- [ ] **Secrets Management**: All credentials stored in secure vault
- [ ] **Network Security**: Firewall rules configured
- [ ] **Container Security**: Base images scanned for vulnerabilities
- [ ] **TLS/SSL**: HTTPS and WSS enabled with valid certificates
- [ ] **Authentication**: API keys and JWT tokens configured
- [ ] **Rate Limiting**: Enabled and configured appropriately

#### **SSL/TLS Certificate Management**
```bash
# Using cert-manager for automatic SSL certificates
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.11.0/cert-manager.yaml

# ClusterIssuer configuration
cat > cluster-issuer.yaml << EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@company.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF

kubectl apply -f cluster-issuer.yaml
```

### **Backup & Disaster Recovery**

#### **Backup Strategy**
```bash
#!/bin/bash
# backup_service.sh

BACKUP_DIR="/backup/mt5-bridge/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup Kubernetes configurations
kubectl get all -n mt5-bridge -o yaml > "$BACKUP_DIR/k8s-resources.yaml"
kubectl get secrets -n mt5-bridge -o yaml > "$BACKUP_DIR/secrets.yaml"
kubectl get configmaps -n mt5-bridge -o yaml > "$BACKUP_DIR/configmaps.yaml"

# Backup application logs
kubectl logs -n mt5-bridge -l app=mt5-bridge --all-containers=true > "$BACKUP_DIR/application.log"

# Backup monitoring data
curl -s http://prometheus:9090/api/v1/query?query=up > "$BACKUP_DIR/metrics.json"

echo "Backup completed: $BACKUP_DIR"
```

#### **Disaster Recovery Plan**
1. **Service Failure**: Automatic pod restart and scaling
2. **Node Failure**: Kubernetes reschedules pods to healthy nodes
3. **Cluster Failure**: Multi-region deployment with DNS failover
4. **Data Loss**: Restore from automated backups
5. **Complete Disaster**: Activate disaster recovery site

## 📋 Post-Deployment Verification

### **Deployment Verification Checklist**

```bash
#!/bin/bash
# verify_deployment.sh

echo "🔍 Post-Deployment Verification"
echo "==============================="

# Service Health
echo "1. Service Health Check:"
curl -f http://mt5-bridge.company.com/health || echo "❌ Health check failed"

# WebSocket Connectivity
echo "2. WebSocket Test:"
timeout 10 wscat -c wss://mt5-bridge.company.com/websocket/ws -x '{"type":"heartbeat","timestamp":"'$(date -Iseconds)'","data":{"client":"test"}}' || echo "❌ WebSocket test failed"

# Performance Metrics
echo "3. Performance Check:"
RESPONSE_TIME=$(curl -w "@curl-format.txt" -o /dev/null -s http://mt5-bridge.company.com/health)
echo "Response time: $RESPONSE_TIME"

# Load Test
echo "4. Load Test:"
ab -n 100 -c 10 http://mt5-bridge.company.com/health

# Security Test
echo "5. Security Check:"
nmap -p 8001 mt5-bridge.company.com

echo "✅ Deployment verification completed"
```

---

**This comprehensive deployment guide ensures reliable, scalable, and secure MT5 Bridge operations across all environments with enterprise-grade monitoring and observability.**