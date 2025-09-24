# Central Hub Migration Guide

## 🔄 Update Import Paths untuk Semua Services

Karena Central Hub structure sudah dipecah menjadi `shared/` dan `service/`, semua services lain perlu update import paths.

---

## 📝 REQUIRED CHANGES

### **1. Update Import Paths**

**OLD (Before Migration):**
```python
# Old import path
import sys
sys.path.append('../../../01-core-infrastructure/central-hub/static')

from utils.base_service import BaseService
from logging.error_dna.analyzer import ErrorDNA
from proto.common.base_pb2 import MessageEnvelope
```

**NEW (After Migration):**
```python
# New import path - point to shared subfolder
import sys
sys.path.append('../../../01-core-infrastructure/central-hub/shared')

from utils.base_service import BaseService
from logging.error_dna.analyzer import ErrorDNA
from proto.common.base_pb2 import MessageEnvelope
```

### **2. Docker Volume Mounts**

**OLD Docker Compose:**
```yaml
api-gateway:
  volumes:
    - "./central-hub/static:/shared:ro"
```

**NEW Docker Compose:**
```yaml
api-gateway:
  volumes:
    - "./central-hub/shared:/shared:ro"
```

---

## 🎯 SERVICES YANG PERLU DIUPDATE

### **Services dengan BaseService Integration:**
- ✅ `analytics-service`
- ✅ `notification-hub`
- ✅ `trading-engine`
- ✅ `risk-management`
- ✅ `api-gateway`
- ✅ `data-bridge`
- ✅ `ml-processing`

---

## 🔧 STEP-BY-STEP MIGRATION

### **Step 1: Update Python Import Paths**

Untuk setiap service file yang menggunakan Central Hub imports:

```bash
# Find all files dengan old import path
grep -r "central-hub/static" --include="*.py" .

# Replace dengan new path
sed -i 's|central-hub/static|central-hub/shared|g' **/*.py
```

### **Step 2: Update Docker Configuration**

Update docker-compose files:

```bash
# Find docker-compose files
find . -name "docker-compose*.yml" -exec grep -l "central-hub/static" {} \;

# Replace volume mounts
sed -i 's|central-hub/static|central-hub/shared|g' docker-compose*.yml
```

### **Step 3: Update Service README Files**

Services yang sudah ada standardization section perlu update contoh import:

```bash
# Files yang perlu diupdate:
# - analytics-service/README.md
# - notification-hub/README.md
# - trading-engine/README.md
# - risk-management/README.md
# - api-gateway/README.md
# - data-bridge/README.md
# - ml-processing/README.md
```

---

## 🚀 AUTOMATED MIGRATION SCRIPT

```bash
#!/bin/bash
# migration_script.sh - Update all services

echo "🔄 Starting Central Hub migration..."

# Function to update Python files
update_python_imports() {
    local service_dir="$1"
    if [ -d "$service_dir" ]; then
        echo "Updating Python imports in $service_dir..."
        find "$service_dir" -name "*.py" -exec sed -i 's|central-hub/static|central-hub/shared|g' {} \;
        echo "✅ Updated Python imports in $service_dir"
    fi
}

# Function to update Docker files
update_docker_files() {
    local service_dir="$1"
    if [ -d "$service_dir" ]; then
        echo "Updating Docker files in $service_dir..."
        find "$service_dir" -name "docker-compose*.yml" -exec sed -i 's|central-hub/static|central-hub/shared|g' {} \;
        find "$service_dir" -name "Dockerfile*" -exec sed -i 's|central-hub/static|central-hub/shared|g' {} \;
        echo "✅ Updated Docker files in $service_dir"
    fi
}

# Update all service directories
SERVICES=(
    "02-data-processing/data-bridge"
    "03-trading-core/trading-engine"
    "03-trading-core/risk-management"
    "04-business-platform/analytics-service"
    "04-business-platform/notification-hub"
    "02-data-processing/ml-processing"
    "01-core-infrastructure/api-gateway"
)

for service in "${SERVICES[@]}"; do
    update_python_imports "backend/$service"
    update_docker_files "backend/$service"
done

echo "🎉 Migration completed!"
echo ""
echo "📋 Manual verification needed:"
echo "1. Test import paths in each service"
echo "2. Verify Docker containers start correctly"
echo "3. Run health checks on all services"
```

---

## ✅ VERIFICATION CHECKLIST

### **Per Service Verification:**

**1. Import Path Check:**
```python
# Test in each service
python3 -c "
import sys
sys.path.append('../central-hub/shared')
from utils.base_service import BaseService
print('✅ BaseService import successful')
"
```

**2. Docker Build Check:**
```bash
# Test Docker build untuk each service
docker build -t test-service .
docker run --rm test-service python -c "from utils.base_service import BaseService; print('✅ Docker import successful')"
```

**3. Service Startup Check:**
```bash
# Test service startup
docker-compose up service-name
curl http://localhost:PORT/health
```

---

## 🔧 Central Hub Service Discovery Integration

Services juga perlu integrate dengan Central Hub service discovery:

### **Add to Service Startup:**
```python
# Add to each service startup
import httpx

async def register_with_central_hub():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://central-hub:7000/services/register",
                json={
                    "name": "your-service-name",
                    "host": "your-service-host",
                    "port": 8000,
                    "health_endpoint": "/health"
                }
            )
            print(f"✅ Registered with Central Hub: {response.json()}")
        except Exception as e:
            print(f"❌ Failed to register with Central Hub: {e}")
```

### **Add to Docker Compose:**
```yaml
your-service:
  depends_on:
    - central-hub
  environment:
    - CENTRAL_HUB_URL=http://central-hub:7000
```

---

## 🎯 EXPECTED RESULTS

After migration:

1. ✅ All services use `central-hub/shared` path
2. ✅ BaseService, ErrorDNA, Protocol Buffers work correctly
3. ✅ Central Hub service runs on port 7000
4. ✅ Services register themselves dengan Central Hub
5. ✅ Service discovery API functional
6. ✅ No import errors atau broken dependencies

---

## 🚨 TROUBLESHOOTING

### **Import Errors:**
```bash
# Check Python path
python3 -c "import sys; print(sys.path)"

# Check file exists
ls -la ../central-hub/shared/utils/base_service.py
```

### **Docker Volume Issues:**
```bash
# Check volume mount
docker run -it --rm -v "./central-hub/shared:/shared:ro" python:3.11 ls -la /shared
```

### **Service Discovery Issues:**
```bash
# Check Central Hub is running
curl http://localhost:7000/health/

# Check service registration
curl http://localhost:7000/services/
```

---

**Migration harus dilakukan SEQUENTIALLY untuk avoid breaking changes. Test each service before proceeding to the next.**