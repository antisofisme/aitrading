# AI Trading System - Deployment and Infrastructure Requirements

## Executive Summary

This document outlines comprehensive deployment and infrastructure requirements for the AI trading system, covering development, staging, and production environments with focus on reliability, scalability, and security.

## Infrastructure Overview

### Environment Strategy
```
Development → Staging → Production
     ↓           ↓          ↓
  Local Dev   Pre-prod   Live Trading
  Mock Data   Real Data  Real Money
  Single AZ   Multi-AZ   Multi-Region
```

### Infrastructure Tiers
- **Compute Tier**: Kubernetes clusters for application workloads
- **Data Tier**: Databases, message queues, and storage systems
- **Network Tier**: Load balancers, CDN, and security groups
- **Monitoring Tier**: Observability and alerting infrastructure
- **Security Tier**: Identity management, secrets, and compliance

## Cloud Provider Comparison

### Amazon Web Services (AWS) - Recommended
```yaml
# AWS infrastructure overview
Compute:
  - EKS (Kubernetes): Application orchestration
  - EC2: High-performance computing nodes
  - Fargate: Serverless containers
  - Lambda: Event-driven functions

Data:
  - RDS (PostgreSQL): Relational data
  - ElastiCache (Redis): Caching layer
  - InfluxDB (EC2): Time series data
  - S3: Object storage
  - EFS: Shared file systems

Network:
  - ALB/NLB: Load balancing
  - CloudFront: CDN
  - Route 53: DNS
  - VPC: Network isolation

Monitoring:
  - CloudWatch: Metrics and logs
  - X-Ray: Distributed tracing
  - SNS/SQS: Notifications

Security:
  - IAM: Identity and access management
  - Secrets Manager: Secret storage
  - Certificate Manager: SSL/TLS certificates
  - GuardDuty: Threat detection
```

**AWS Cost Estimate**:
- **Development**: $500-1,000/month
- **Staging**: $1,500-3,000/month
- **Production**: $5,000-15,000/month

### Google Cloud Platform (GCP) - Alternative
```yaml
# GCP infrastructure overview
Compute:
  - GKE: Kubernetes clusters
  - Compute Engine: Virtual machines
  - Cloud Run: Serverless containers
  - Cloud Functions: Event functions

Data:
  - Cloud SQL: PostgreSQL managed service
  - Memorystore: Redis managed service
  - BigQuery: Data warehouse
  - Cloud Storage: Object storage

Network:
  - Cloud Load Balancing: Global load balancer
  - Cloud CDN: Content delivery
  - Cloud DNS: Domain name system

Monitoring:
  - Cloud Monitoring: Metrics and alerting
  - Cloud Logging: Log management
  - Cloud Trace: Distributed tracing

Security:
  - Cloud IAM: Identity management
  - Secret Manager: Secret storage
  - Certificate Manager: SSL certificates
```

### Microsoft Azure - Alternative
```yaml
# Azure infrastructure overview
Compute:
  - AKS: Kubernetes service
  - Virtual Machines: Compute instances
  - Container Instances: Serverless containers
  - Functions: Event-driven compute

Data:
  - Azure Database for PostgreSQL: Managed database
  - Azure Cache for Redis: Managed Redis
  - Azure Blob Storage: Object storage

Network:
  - Azure Load Balancer: Load balancing
  - Azure CDN: Content delivery
  - Azure DNS: Domain name system

Monitoring:
  - Azure Monitor: Metrics and logs
  - Application Insights: APM

Security:
  - Azure Active Directory: Identity
  - Key Vault: Secret management
```

## Development Environment Setup

### Local Development Infrastructure
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  # Databases
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: trading_dev
      POSTGRES_USER: trading
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./data/migrations:/docker-entrypoint-initdb.d

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  influxdb:
    image: influxdb:2.7
    ports:
      - "8086:8086"
    environment:
      INFLUXDB_DB: trading_dev
      INFLUXDB_ADMIN_USER: admin
      INFLUXDB_ADMIN_PASSWORD: password
    volumes:
      - influxdb_data:/var/lib/influxdb2

  # Message Queue
  kafka:
    image: confluentinc/cp-kafka:latest
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1

  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    ports:
      - "2181:2181"
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000

  # Monitoring
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards

  # Development tools
  pgadmin:
    image: dpage/pgadmin4:latest
    ports:
      - "8080:80"
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@trading.local
      PGADMIN_DEFAULT_PASSWORD: admin

volumes:
  postgres_data:
  redis_data:
  influxdb_data:
  prometheus_data:
  grafana_data:
```

### Development Workflow
```bash
#!/bin/bash
# scripts/dev-setup.sh

set -e

echo "Setting up development environment..."

# Create necessary directories
mkdir -p data/{raw,processed,models}
mkdir -p logs
mkdir -p monitoring/{prometheus,grafana}

# Start infrastructure services
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 30

# Initialize databases
echo "Initializing databases..."
python scripts/init-db.py

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements-dev.txt

# Build Go services
echo "Building Go services..."
make build-all

# Run database migrations
echo "Running migrations..."
python scripts/migrate.py

# Load test data
echo "Loading test data..."
python scripts/load-test-data.py

echo "Development environment ready!"
echo "Services available at:"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo "  - InfluxDB: localhost:8086"
echo "  - Kafka: localhost:9092"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3000 (admin/admin)"
echo "  - PgAdmin: http://localhost:8080 (admin@trading.local/admin)"
```

## Staging Environment

### AWS EKS Staging Cluster
```yaml
# terraform/staging/eks.tf
module "eks" {
  source = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = "trading-staging"
  cluster_version = "1.28"

  vpc_id                         = module.vpc.vpc_id
  subnet_ids                     = module.vpc.private_subnets
  cluster_endpoint_public_access = true

  # EKS Managed Node Groups
  eks_managed_node_groups = {
    general = {
      name = "general"

      instance_types = ["m5.large"]

      min_size     = 2
      max_size     = 6
      desired_size = 3

      pre_bootstrap_user_data = <<-EOT
      #!/bin/bash
      /etc/eks/bootstrap.sh trading-staging
      EOT

      vpc_security_group_ids = [aws_security_group.node_group_one.id]
    }

    ml_workloads = {
      name = "ml-workloads"

      instance_types = ["c5.xlarge"]

      min_size     = 1
      max_size     = 4
      desired_size = 2

      labels = {
        WorkloadType = "ml"
      }

      taints = {
        ml = {
          key    = "ml-workload"
          value  = "true"
          effect = "NO_SCHEDULE"
        }
      }
    }
  }

  # aws-auth configmap
  manage_aws_auth_configmap = true

  aws_auth_roles = [
    {
      rolearn  = aws_iam_role.eks_admin.arn
      username = "eks-admin"
      groups   = ["system:masters"]
    },
  ]

  tags = {
    Environment = "staging"
    Terraform   = "true"
  }
}
```

### Staging Database Setup
```yaml
# terraform/staging/databases.tf
# PostgreSQL RDS
resource "aws_db_instance" "postgres_staging" {
  identifier = "trading-postgres-staging"

  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.medium"

  allocated_storage     = 100
  max_allocated_storage = 500
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = "trading_staging"
  username = "trading"
  password = var.postgres_password

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.postgres.name

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "Sun:04:00-Sun:05:00"

  skip_final_snapshot = true
  deletion_protection = false

  performance_insights_enabled = true
  monitoring_interval         = 60
  monitoring_role_arn        = aws_iam_role.rds_monitoring.arn

  tags = {
    Environment = "staging"
  }
}

# Redis ElastiCache
resource "aws_elasticache_replication_group" "redis_staging" {
  replication_group_id       = "trading-redis-staging"
  description                = "Redis cluster for trading staging"

  node_type               = "cache.t3.medium"
  port                    = 6379
  parameter_group_name    = "default.redis7"

  num_cache_clusters      = 2
  automatic_failover_enabled = true
  multi_az_enabled        = true

  subnet_group_name       = aws_elasticache_subnet_group.redis.name
  security_group_ids      = [aws_security_group.redis.id]

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                 = var.redis_auth_token

  tags = {
    Environment = "staging"
  }
}

# InfluxDB on EC2 (managed)
resource "aws_instance" "influxdb_staging" {
  ami           = "ami-0c02fb55956c7d316" # Amazon Linux 2
  instance_type = "m5.large"

  key_name               = aws_key_pair.influxdb.key_name
  vpc_security_group_ids = [aws_security_group.influxdb.id]
  subnet_id              = module.vpc.private_subnets[0]

  root_block_device {
    volume_type = "gp3"
    volume_size = 100
    encrypted   = true
  }

  ebs_block_device {
    device_name = "/dev/sdf"
    volume_type = "gp3"
    volume_size = 500
    encrypted   = true
  }

  user_data = file("${path.module}/influxdb-init.sh")

  tags = {
    Name        = "influxdb-staging"
    Environment = "staging"
  }
}
```

### Kubernetes Application Deployment
```yaml
# k8s/staging/prediction-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prediction-service
  namespace: trading-staging
spec:
  replicas: 2
  selector:
    matchLabels:
      app: prediction-service
  template:
    metadata:
      labels:
        app: prediction-service
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: prediction-service
        image: 123456789012.dkr.ecr.us-west-2.amazonaws.com/trading/prediction-service:staging
        ports:
        - containerPort: 8080
          name: http
        - containerPort: 9090
          name: grpc
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-credentials
              key: url
        - name: MODEL_STORE_PATH
          value: "s3://trading-models-staging/"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: model-cache
          mountPath: /tmp/models
      volumes:
      - name: model-cache
        emptyDir: {}

---
apiVersion: v1
kind: Service
metadata:
  name: prediction-service
  namespace: trading-staging
spec:
  selector:
    app: prediction-service
  ports:
  - name: http
    port: 80
    targetPort: 8080
  - name: grpc
    port: 9090
    targetPort: 9090

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: prediction-service-ingress
  namespace: trading-staging
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internal
    alb.ingress.kubernetes.io/target-type: ip
spec:
  rules:
  - host: prediction-staging.trading.internal
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: prediction-service
            port:
              number: 80
```

## Production Environment

### Multi-Region Production Setup
```yaml
# terraform/production/main.tf
# Primary region: us-west-2
provider "aws" {
  alias  = "primary"
  region = "us-west-2"
}

# Secondary region: us-east-1
provider "aws" {
  alias  = "secondary"
  region = "us-east-1"
}

# Primary EKS cluster
module "eks_primary" {
  source = "../modules/eks"
  providers = {
    aws = aws.primary
  }

  cluster_name = "trading-prod-primary"
  environment  = "production"
  region       = "us-west-2"

  node_groups = {
    general = {
      instance_types = ["m5.xlarge"]
      min_size      = 3
      max_size      = 20
      desired_size  = 6
    }

    ml_workloads = {
      instance_types = ["c5.2xlarge"]
      min_size      = 2
      max_size      = 10
      desired_size  = 4
    }

    high_memory = {
      instance_types = ["r5.xlarge"]
      min_size      = 1
      max_size      = 5
      desired_size  = 2
    }
  }
}

# Secondary EKS cluster (disaster recovery)
module "eks_secondary" {
  source = "../modules/eks"
  providers = {
    aws = aws.secondary
  }

  cluster_name = "trading-prod-secondary"
  environment  = "production"
  region       = "us-east-1"

  node_groups = {
    general = {
      instance_types = ["m5.large"]
      min_size      = 2
      max_size      = 10
      desired_size  = 3
    }
  }
}
```

### Production Database Configuration
```yaml
# terraform/production/databases.tf
# Multi-AZ PostgreSQL with read replicas
resource "aws_db_instance" "postgres_primary" {
  identifier = "trading-postgres-prod"

  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.r5.2xlarge"

  allocated_storage     = 1000
  max_allocated_storage = 5000
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id           = aws_kms_key.rds.arn

  db_name  = "trading_prod"
  username = "trading"
  password = random_password.postgres_password.result

  vpc_security_group_ids = [aws_security_group.rds_primary.id]
  db_subnet_group_name   = aws_db_subnet_group.postgres_primary.name

  # High availability
  multi_az = true

  # Backup configuration
  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "Sun:04:00-Sun:06:00"
  copy_tags_to_snapshot  = true

  # Performance monitoring
  performance_insights_enabled = true
  performance_insights_retention_period = 7
  monitoring_interval = 15
  monitoring_role_arn = aws_iam_role.rds_monitoring.arn

  # Security
  deletion_protection = true
  skip_final_snapshot = false
  final_snapshot_identifier = "trading-postgres-prod-final-snapshot"

  tags = {
    Environment = "production"
    Backup     = "required"
  }
}

# Read replicas for reporting and analytics
resource "aws_db_instance" "postgres_read_replica" {
  count = 2

  identifier = "trading-postgres-read-${count.index + 1}"
  replicate_source_db = aws_db_instance.postgres_primary.identifier

  instance_class = "db.r5.xlarge"
  publicly_accessible = false

  performance_insights_enabled = true
  monitoring_interval = 60

  tags = {
    Environment = "production"
    Purpose    = "read-replica"
  }
}

# Redis cluster for high availability
resource "aws_elasticache_replication_group" "redis_production" {
  replication_group_id = "trading-redis-prod"
  description         = "Redis cluster for trading production"

  node_type          = "cache.r6g.xlarge"
  port              = 6379
  parameter_group_name = aws_elasticache_parameter_group.redis_prod.name

  num_cache_clusters = 3
  automatic_failover_enabled = true
  multi_az_enabled = true

  subnet_group_name  = aws_elasticache_subnet_group.redis_prod.name
  security_group_ids = [aws_security_group.redis_prod.id]

  # Security
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token = random_password.redis_auth_token.result

  # Backup
  snapshot_retention_limit = 7
  snapshot_window         = "03:00-05:00"

  # Maintenance
  maintenance_window = "sun:05:00-sun:07:00"

  tags = {
    Environment = "production"
  }
}
```

### Production Monitoring Stack
```yaml
# k8s/production/monitoring/prometheus.yaml
apiVersion: monitoring.coreos.com/v1
kind: Prometheus
metadata:
  name: prometheus-production
  namespace: monitoring
spec:
  replicas: 2
  retention: 30d
  retentionSize: 100GB

  serviceAccountName: prometheus
  serviceMonitorSelector:
    matchLabels:
      team: trading

  resources:
    requests:
      memory: 4Gi
      cpu: 1000m
    limits:
      memory: 8Gi
      cpu: 2000m

  storage:
    volumeClaimTemplate:
      spec:
        storageClassName: fast-ssd
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 200Gi

  securityContext:
    fsGroup: 2000
    runAsNonRoot: true
    runAsUser: 1000

  additionalScrapeConfigs:
    name: additional-scrape-configs
    key: prometheus-additional.yaml

  ruleSelector:
    matchLabels:
      prometheus: trading-production

  alerting:
    alertmanagers:
    - namespace: monitoring
      name: alertmanager-main
      port: web

---
apiVersion: v1
kind: Secret
metadata:
  name: additional-scrape-configs
  namespace: monitoring
stringData:
  prometheus-additional.yaml: |
    # InfluxDB metrics
    - job_name: 'influxdb'
      static_configs:
      - targets: ['influxdb:8086']

    # External trading APIs
    - job_name: 'external-apis'
      metrics_path: /health
      static_configs:
      - targets: ['mt4-gateway:8080', 'mt5-gateway:8080']

    # Database exporters
    - job_name: 'postgres-exporter'
      static_configs:
      - targets: ['postgres-exporter:9187']

    - job_name: 'redis-exporter'
      static_configs:
      - targets: ['redis-exporter:9121']
```

### Production Security Configuration
```yaml
# k8s/production/security/network-policies.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: trading-services-policy
  namespace: trading-production
spec:
  podSelector:
    matchLabels:
      tier: trading
  policyTypes:
  - Ingress
  - Egress
  ingress:
  # Allow ingress from API gateway
  - from:
    - namespaceSelector:
        matchLabels:
          name: api-gateway
    ports:
    - protocol: TCP
      port: 8080
  # Allow ingress from monitoring
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - protocol: TCP
      port: 9090
  egress:
  # Allow egress to databases
  - to: []
    ports:
    - protocol: TCP
      port: 5432  # PostgreSQL
    - protocol: TCP
      port: 6379  # Redis
    - protocol: TCP
      port: 8086  # InfluxDB
  # Allow egress to other trading services
  - to:
    - podSelector:
        matchLabels:
          tier: trading
  # Allow DNS
  - to: []
    ports:
    - protocol: UDP
      port: 53

---
# Pod Security Policy
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: trading-restricted
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
```

## CI/CD Pipeline

### GitHub Actions Workflow
```yaml
# .github/workflows/deploy.yml
name: Deploy Trading System

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  AWS_REGION: us-west-2
  ECR_REGISTRY: 123456789012.dkr.ecr.us-west-2.amazonaws.com

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Set up Go
      uses: actions/setup-go@v4
      with:
        go-version: '1.21'

    - name: Install dependencies
      run: |
        pip install -r requirements-dev.txt
        go mod download

    - name: Run Python tests
      run: |
        python -m pytest tests/python/ -v --cov=src/

    - name: Run Go tests
      run: |
        go test ./services/execution/... -v -race -coverprofile=coverage.out

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service:
          - prediction
          - execution
          - decision
          - risk-manager

    steps:
    - uses: actions/checkout@v4

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ env.AWS_REGION }}

    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v1

    - name: Build and push Docker image
      run: |
        # Build image
        docker build -t $ECR_REGISTRY/trading/${{ matrix.service }}:$GITHUB_SHA \
          -f services/${{ matrix.service }}/Dockerfile .

        # Push to ECR
        docker push $ECR_REGISTRY/trading/${{ matrix.service }}:$GITHUB_SHA

        # Tag as latest for main branch
        if [ "$GITHUB_REF" = "refs/heads/main" ]; then
          docker tag $ECR_REGISTRY/trading/${{ matrix.service }}:$GITHUB_SHA \
            $ECR_REGISTRY/trading/${{ matrix.service }}:latest
          docker push $ECR_REGISTRY/trading/${{ matrix.service }}:latest
        fi

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop'

    steps:
    - uses: actions/checkout@v4

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ env.AWS_REGION }}

    - name: Install kubectl
      uses: azure/setup-kubectl@v3

    - name: Update kubeconfig
      run: |
        if [ "$GITHUB_REF" = "refs/heads/main" ]; then
          aws eks update-kubeconfig --name trading-prod-primary
        else
          aws eks update-kubeconfig --name trading-staging
        fi

    - name: Deploy to Kubernetes
      run: |
        # Set environment
        if [ "$GITHUB_REF" = "refs/heads/main" ]; then
          ENV="production"
        else
          ENV="staging"
        fi

        # Update image tags in manifests
        for service in prediction execution decision risk-manager; do
          yq e '.spec.template.spec.containers[0].image =
            "'$ECR_REGISTRY'/trading/'$service':'$GITHUB_SHA'"' \
            -i k8s/$ENV/$service.yaml
        done

        # Apply manifests
        kubectl apply -f k8s/$ENV/

        # Wait for rollout
        for service in prediction execution decision risk-manager; do
          kubectl rollout status deployment/$service-service -n trading-$ENV
        done

  security-scan:
    runs-on: ubuntu-latest
    needs: build

    steps:
    - uses: actions/checkout@v4

    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: '${{ env.ECR_REGISTRY }}/trading/prediction:${{ github.sha }}'
        format: 'sarif'
        output: 'trivy-results.sarif'

    - name: Upload Trivy scan results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'
```

## Disaster Recovery and Backup

### Backup Strategy
```bash
#!/bin/bash
# scripts/backup-production.sh

set -e

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
S3_BACKUP_BUCKET="trading-backups-production"

echo "Starting production backup: $BACKUP_DATE"

# Database backup
echo "Backing up PostgreSQL..."
pg_dump $DATABASE_URL | gzip > /tmp/postgres_backup_$BACKUP_DATE.sql.gz
aws s3 cp /tmp/postgres_backup_$BACKUP_DATE.sql.gz \
  s3://$S3_BACKUP_BUCKET/postgres/postgres_backup_$BACKUP_DATE.sql.gz

# Redis backup
echo "Backing up Redis..."
redis-cli --rdb /tmp/redis_backup_$BACKUP_DATE.rdb
gzip /tmp/redis_backup_$BACKUP_DATE.rdb
aws s3 cp /tmp/redis_backup_$BACKUP_DATE.rdb.gz \
  s3://$S3_BACKUP_BUCKET/redis/redis_backup_$BACKUP_DATE.rdb.gz

# InfluxDB backup
echo "Backing up InfluxDB..."
influx backup -t $INFLUX_TOKEN /tmp/influxdb_backup_$BACKUP_DATE
tar -czf /tmp/influxdb_backup_$BACKUP_DATE.tar.gz -C /tmp influxdb_backup_$BACKUP_DATE
aws s3 cp /tmp/influxdb_backup_$BACKUP_DATE.tar.gz \
  s3://$S3_BACKUP_BUCKET/influxdb/influxdb_backup_$BACKUP_DATE.tar.gz

# Model artifacts backup
echo "Backing up ML models..."
aws s3 sync s3://trading-models-production/ \
  s3://$S3_BACKUP_BUCKET/models/models_backup_$BACKUP_DATE/ --delete

# Configuration backup
echo "Backing up Kubernetes configurations..."
kubectl get all,configmaps,secrets -o yaml > /tmp/k8s_config_$BACKUP_DATE.yaml
aws s3 cp /tmp/k8s_config_$BACKUP_DATE.yaml \
  s3://$S3_BACKUP_BUCKET/k8s/k8s_config_$BACKUP_DATE.yaml

# Cleanup local files
rm -f /tmp/*_backup_$BACKUP_DATE*

echo "Backup completed: $BACKUP_DATE"

# Retention: Keep last 30 daily backups
aws s3api list-objects-v2 --bucket $S3_BACKUP_BUCKET --prefix postgres/ \
  --query 'Contents[?LastModified<=`'$(date -d "30 days ago" --iso-8601)'`].Key' \
  --output text | xargs -r aws s3 rm --recursive s3://$S3_BACKUP_BUCKET/
```

### Disaster Recovery Plan
```yaml
# disaster-recovery-playbook.yml
---
disaster_recovery_playbook:
  scenarios:
    - name: "Primary Region Failure"
      severity: "Critical"
      rto: "15 minutes"  # Recovery Time Objective
      rpo: "5 minutes"   # Recovery Point Objective

      steps:
        1. "Verify primary region status"
        2. "Activate secondary region EKS cluster"
        3. "Restore database from latest backup"
        4. "Update DNS to point to secondary region"
        5. "Verify all services are operational"
        6. "Monitor trading activity"

    - name: "Database Corruption"
      severity: "High"
      rto: "30 minutes"
      rpo: "1 hour"

      steps:
        1. "Stop all trading activities"
        2. "Identify corruption scope"
        3. "Restore from latest clean backup"
        4. "Replay transaction logs if available"
        5. "Validate data integrity"
        6. "Resume trading activities"

    - name: "Kubernetes Cluster Failure"
      severity: "High"
      rto: "20 minutes"
      rpo: "10 minutes"

      steps:
        1. "Assess cluster health"
        2. "Deploy services to backup cluster"
        3. "Restore persistent volumes"
        4. "Update load balancer targets"
        5. "Verify service connectivity"

  automation:
    health_checks:
      - endpoint: "https://api.trading.com/health"
        interval: "30s"
        timeout: "5s"
        retries: 3

    failover_triggers:
      - metric: "service_availability"
        threshold: "< 95%"
        duration: "5m"
        action: "initiate_failover"

    notifications:
      - type: "slack"
        webhook: "$SLACK_WEBHOOK_URL"
        escalation: "@oncall-team"

      - type: "pagerduty"
        service_key: "$PAGERDUTY_SERVICE_KEY"
        escalation_policy: "trading-critical"

  testing:
    schedule: "monthly"
    scenarios:
      - "Simulated region failure"
      - "Database failover test"
      - "Network partition test"

    validation:
      - "All services respond within SLA"
      - "Data consistency verified"
      - "No data loss detected"
      - "Trading operations resumed"
```

This comprehensive deployment and infrastructure guide provides a robust foundation for deploying the AI trading system across multiple environments with proper security, monitoring, and disaster recovery capabilities.