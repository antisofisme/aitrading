#!/usr/bin/env python3
"""
Script untuk update semua service READMEs dengan standardization patterns
"""

import os
import re
from pathlib import Path


SERVICE_CONFIGS = {
    "analytics-service": {
        "port": 8003,
        "version": "4.0.0",
        "health_checks": [
            '"analytics_queries_24h": await self.get_daily_query_count()',
            '"avg_dashboard_response_ms": await self.get_avg_dashboard_time()',
            '"data_processing_success_rate": await self.get_processing_success_rate()'
        ],
        "example_operation": "analytics_query",
        "example_function": "_execute_analytics_query",
        "context_operation": "business_intelligence"
    },
    "notification-hub": {
        "port": 8004,
        "version": "3.0.0",
        "health_checks": [
            '"notifications_sent_24h": await self.get_daily_notification_count()',
            '"avg_delivery_time_ms": await self.get_avg_delivery_time()',
            '"channel_success_rates": await self.get_channel_success_rates()'
        ],
        "example_operation": "notification_delivery",
        "example_function": "_send_notification",
        "context_operation": "notification_processing"
    },
    "trading-engine": {
        "port": 8002,
        "version": "5.0.0",
        "health_checks": [
            '"signals_generated_24h": await self.get_daily_signal_count()',
            '"avg_signal_generation_ms": await self.get_avg_signal_time()',
            '"strategy_success_rates": await self.get_strategy_success_rates()'
        ],
        "example_operation": "signal_generation",
        "example_function": "_generate_trading_signal",
        "context_operation": "trading_signal_generation"
    },
    "risk-management": {
        "port": 8005,
        "version": "3.5.0",
        "health_checks": [
            '"risk_assessments_24h": await self.get_daily_assessment_count()',
            '"avg_risk_calc_time_ms": await self.get_avg_risk_time()',
            '"risk_approval_rate": await self.get_risk_approval_rate()'
        ],
        "example_operation": "risk_assessment",
        "example_function": "_assess_trading_risk",
        "context_operation": "risk_calculation"
    },
    "api-gateway": {
        "port": 8000,
        "version": "2.5.0",
        "health_checks": [
            '"requests_routed_24h": await self.get_daily_request_count()',
            '"avg_routing_time_ms": await self.get_avg_routing_time()',
            '"websocket_connections": await self.get_active_websocket_count()'
        ],
        "example_operation": "request_routing",
        "example_function": "_route_request",
        "context_operation": "api_routing"
    },
    "data-bridge": {
        "port": 8001,
        "version": "2.0.0",
        "health_checks": [
            '"data_batches_processed_24h": await self.get_daily_batch_count()',
            '"avg_processing_time_ms": await self.get_avg_processing_time()',
            '"data_quality_score": await self.get_data_quality_score()'
        ],
        "example_operation": "data_processing",
        "example_function": "_process_data_batch",
        "context_operation": "data_validation"
    },
    "ml-processing": {
        "port": 8007,
        "version": "4.5.0",
        "health_checks": [
            '"predictions_generated_24h": await self.get_daily_prediction_count()',
            '"avg_inference_time_ms": await self.get_avg_inference_time()',
            '"model_accuracy_rates": await self.get_model_accuracy_rates()'
        ],
        "example_operation": "ml_inference",
        "example_function": "_generate_prediction",
        "context_operation": "machine_learning_inference"
    }
}


def generate_standardization_section(service_name: str, config: dict) -> str:
    """Generate standardization section for service README"""

    health_checks = ',\n            '.join(config["health_checks"])

    return f"""---

## 📋 Standard Implementation Pattern

### **BaseService Integration:**
```python
# {service_name.title().replace('-', ' ')} implementation menggunakan Central Hub standards
from central_hub.static.utils import BaseService, ServiceConfig
from central_hub.static.utils.patterns import (
    StandardResponse, StandardDatabaseManager, StandardCacheManager,
    RequestTracer, StandardCircuitBreaker, PerformanceTracker, ErrorDNA
)

class {service_name.replace('-', '').title()}Service(BaseService):
    def __init__(self):
        config = ServiceConfig(
            service_name="{service_name}",
            version="{config['version']}",
            port={config['port']},
            environment="production"
        )
        super().__init__(config)

        # Service-specific initialization
        self.performance_tracker = PerformanceTracker("{service_name}")
        self.error_analyzer = ErrorDNA("{service_name}")

    async def custom_health_checks(self):
        """{service_name.title().replace('-', ' ')}-specific health checks"""
        return {{
            {health_checks}
        }}

    async def process_service_request(self, request_data, correlation_id):
        """Standard {service_name.replace('-', ' ')} processing with patterns"""
        return await self.process_with_tracing(
            "{config['example_operation']}",
            self.{config['example_function']},
            correlation_id,
            request_data
        )
```

### **Standard Error Handling:**
```python
# ErrorDNA integration untuk intelligent error analysis
try:
    service_result = await self.process_{config['context_operation']}(data)
except Exception as e:
    # Automatic error analysis dengan suggestions
    error_analysis = self.error_analyzer.analyze_error(
        error_message=str(e),
        stack_trace=traceback.format_exc(),
        correlation_id=correlation_id,
        context={{"operation": "{config['context_operation']}", "user_id": user_id}}
    )

    # Log dengan ErrorDNA insights
    self.logger.error(f"{service_name.title().replace('-', ' ')} processing failed: {{error_analysis.suggested_actions}}")

    return StandardResponse.error_response(
        error_message=str(e),
        correlation_id=correlation_id,
        service_name=self.service_name
    )
```

### **Standard Performance Monitoring:**
```python
# Automatic performance tracking untuk all {service_name.replace('-', ' ')} operations
with self.performance_tracker.measure("{config['example_operation']}", user_id=user_id):
    result_data = await self.execute_{config['context_operation']}(request)

# Get performance insights
performance_summary = self.performance_tracker.get_performance_summary()
```

### **Standard Database & Cache Access:**
```python
# Consistent database patterns
service_data = await self.db.fetch_many(
    "SELECT * FROM {service_name.replace('-', '_')}_data WHERE user_id = $1 AND date >= $2",
    {{"user_id": user_id, "date": start_date}}
)

# Standard caching patterns
cached_result = await self.cache.get_or_set(
    f"{service_name.replace('-', '_')}:data:{{user_id}}",
    lambda: self.generate_{config['context_operation']}_data(user_id),
    ttl=300  # 5 minutes
)
```

### **Standard Circuit Breaker Protection:**
```python
# External service calls dengan circuit breaker protection
if not await self.check_circuit_breaker("external_service"):
    try:
        result = await self.call_external_service(data)
        await self.record_external_success("external_service")
        return result
    except Exception as e:
        await self.record_external_failure("external_service")
        raise
else:
    # Circuit breaker is open, use fallback
    return await self.get_fallback_result(data)
```

---"""


def update_service_readme(service_path: Path, service_name: str):
    """Update individual service README with standardization"""
    readme_path = service_path / "README.md"

    if not readme_path.exists():
        print(f"❌ README.md not found for {service_name}")
        return

    config = SERVICE_CONFIGS.get(service_name)
    if not config:
        print(f"⚠️  No config found for {service_name}, skipping...")
        return

    # Read current README content
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if standardization section already exists
    if "## 📋 Standard Implementation Pattern" in content:
        print(f"✅ {service_name} already has standardization section")
        return

    # Find insertion point (after transport architecture section)
    insertion_patterns = [
        r"(```\n\n---\n\n## 📈 Advanced)",
        r"(```\n\n---\n\n## 🔄 Advanced)",
        r"(```\n\n---\n\n## 🤖 Multi-Model)",
        r"(```\n\n---\n\n## 🛡️ Advanced)",
        r"(```\n\n---\n\n## ⚡ Performance)",
        r"(```\n\n---\n\n## 🔧 WebSocket)",
        r"(```\n\n---\n\n## 🔄 Data Processing)"
    ]

    standardization_section = generate_standardization_section(service_name, config)
    insertion_point = None

    for pattern in insertion_patterns:
        match = re.search(pattern, content)
        if match:
            insertion_point = match.start(1)
            break

    if insertion_point is None:
        # If no insertion point found, add before the last section
        lines = content.split('\n')
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].startswith('## '):
                insertion_point = content.find(lines[i])
                break

    if insertion_point is not None:
        # Insert standardization section
        new_content = (
            content[:insertion_point] +
            standardization_section +
            "\n\n" +
            content[insertion_point:]
        )

        # Write updated content
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"✅ Updated {service_name} README with standardization patterns")
    else:
        print(f"❌ Could not find insertion point for {service_name}")


def main():
    """Main function to update all service READMEs"""
    print("🚀 Updating all service READMEs with standardization patterns...")

    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent.parent
    backend_dir = project_root / "backend"

    # Find all service directories
    service_dirs = []

    # Search in different backend subdirectories
    search_dirs = [
        "01-core-infrastructure",
        "02-data-processing",
        "03-trading-core",
        "04-business-platform",
        "05-communication"
    ]

    for search_dir in search_dirs:
        search_path = backend_dir / search_dir
        if search_path.exists():
            for item in search_path.iterdir():
                if item.is_dir() and (item / "README.md").exists():
                    service_name = item.name
                    if service_name in SERVICE_CONFIGS:
                        service_dirs.append((item, service_name))

    print(f"Found {len(service_dirs)} services to update:")
    for service_path, service_name in service_dirs:
        print(f"  - {service_name}")

    print()

    # Update each service
    for service_path, service_name in service_dirs:
        update_service_readme(service_path, service_name)

    print(f"\n🎉 Completed updating {len(service_dirs)} service READMEs!")
    print("\n📋 All services now have standardized:")
    print("  ✅ BaseService integration")
    print("  ✅ ErrorDNA intelligent error handling")
    print("  ✅ Performance tracking")
    print("  ✅ Standard database/cache patterns")
    print("  ✅ Circuit breaker protection")
    print("  ✅ Request tracing")


if __name__ == "__main__":
    main()