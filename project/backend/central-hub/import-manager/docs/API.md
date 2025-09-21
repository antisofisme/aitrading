# Import Manager API Documentation

## Overview

The Import Manager provides a unified interface for importing data from various sources into the AI Trading Platform Central Hub. It supports file-based imports, streaming data, database queries, and API integrations with comprehensive error handling and validation.

## Quick Start

```python
from import_manager import ImportManager, ImportConfig, ImportType

# Create Import Manager
manager = ImportManager()

# Simple file import
config = ImportConfig(
    import_id="my_import",
    import_type=ImportType.FILE,
    source_path="/path/to/data.json",
    format_type="json"
)

result = await manager.import_data(config)
print(f"Imported {result.records_processed} records")
```

## Core Classes

### ImportManager

Main class for managing all import operations.

#### Constructor

```python
ImportManager(config_path: Optional[str] = None)
```

**Parameters:**
- `config_path`: Path to configuration directory (optional)

#### Methods

##### import_data()

```python
async def import_data(self, import_config: ImportConfig) -> ImportResult
```

Main method for importing data.

**Parameters:**
- `import_config`: ImportConfig object with import settings

**Returns:**
- `ImportResult`: Result object with import statistics and status

**Example:**
```python
config = ImportConfig(
    import_id="market_data_import",
    import_type=ImportType.FILE,
    source_path="market_data.json",
    format_type="json",
    validation_enabled=True
)

result = await manager.import_data(config)
```

##### get_import_status()

```python
def get_import_status(self, import_id: str) -> Optional[ImportResult]
```

Get the status of a specific import.

**Parameters:**
- `import_id`: Unique identifier for the import

**Returns:**
- `ImportResult` object or `None` if not found

##### list_active_imports()

```python
def list_active_imports(self) -> List[ImportResult]
```

Get list of all active imports.

**Returns:**
- List of `ImportResult` objects

##### cancel_import()

```python
def cancel_import(self, import_id: str) -> bool
```

Cancel an active import.

**Parameters:**
- `import_id`: Unique identifier for the import

**Returns:**
- `True` if cancelled successfully, `False` otherwise

##### get_statistics()

```python
def get_statistics(self) -> Dict[str, Any]
```

Get import manager statistics.

**Returns:**
- Dictionary with statistics including success rates and counts

##### health_check()

```python
async def health_check(self) -> Dict[str, Any]
```

Perform health check of the import system.

**Returns:**
- Dictionary with health status information

### ImportConfig

Configuration class for import operations.

```python
@dataclass
class ImportConfig:
    import_id: str
    import_type: ImportType
    source_path: str
    target_path: Optional[str] = None
    format_type: str = "json"
    batch_size: int = 1000
    max_retries: int = 3
    timeout_seconds: int = 300
    validation_enabled: bool = True
    error_on_validation_failure: bool = False
    metadata: Dict[str, Any] = None
```

**Fields:**
- `import_id`: Unique identifier for this import operation
- `import_type`: Type of import (FILE, STREAM, DATABASE, API, BATCH)
- `source_path`: Path or URL to the data source
- `target_path`: Optional target path for processed data
- `format_type`: Data format (json, csv, xml, txt)
- `batch_size`: Number of records to process per batch
- `max_retries`: Maximum number of retry attempts
- `timeout_seconds`: Import timeout in seconds
- `validation_enabled`: Whether to validate imported data
- `error_on_validation_failure`: Whether to fail on validation errors
- `metadata`: Additional metadata for the import

### ImportResult

Result class containing import operation details.

```python
@dataclass
class ImportResult:
    import_id: str
    status: ImportStatus
    records_processed: int = 0
    records_failed: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
```

**Properties:**
- `duration_seconds`: Calculated duration of the import
- `success_rate`: Calculated success rate as percentage

### ImportType

Enumeration of supported import types.

```python
class ImportType(Enum):
    FILE = "file"
    STREAM = "stream"
    DATABASE = "database"
    API = "api"
    BATCH = "batch"
```

### ImportStatus

Enumeration of import operation statuses.

```python
class ImportStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

## Central Hub Integration

### CentralHubImportIntegration

Specialized integration class for Central Hub operations.

```python
integration = CentralHubImportIntegration(import_manager)
```

#### Methods

##### import_market_data()

```python
async def import_market_data(self, source_path: str, format_type: str = 'json') -> ImportResult
```

Import market data with Central Hub-specific configuration.

##### import_trading_signals()

```python
async def import_trading_signals(self, stream_source: str) -> ImportResult
```

Import trading signals via streaming.

##### import_configuration()

```python
async def import_configuration(self, config_path: str) -> ImportResult
```

Import configuration data with strict validation.

## Convenience Functions

### create_import_manager()

```python
def create_import_manager(config_path: Optional[str] = None) -> ImportManager
```

Create and configure Import Manager instance.

### create_central_hub_integration()

```python
def create_central_hub_integration(config_path: Optional[str] = None) -> CentralHubImportIntegration
```

Create Central Hub integration with Import Manager.

### quick_import()

```python
async def quick_import(source_path: str, import_type: ImportType = ImportType.FILE, 
                      format_type: str = 'json') -> ImportResult
```

Quick import function for simple use cases.

## Supported File Formats

### JSON

```python
config = ImportConfig(
    import_id="json_import",
    import_type=ImportType.FILE,
    source_path="data.json",
    format_type="json"
)
```

### CSV

```python
config = ImportConfig(
    import_id="csv_import",
    import_type=ImportType.FILE,
    source_path="data.csv",
    format_type="csv",
    metadata={"min_columns": 3}
)
```

### XML

```python
config = ImportConfig(
    import_id="xml_import",
    import_type=ImportType.FILE,
    source_path="data.xml",
    format_type="xml"
)
```

### Text

```python
config = ImportConfig(
    import_id="text_import",
    import_type=ImportType.FILE,
    source_path="data.txt",
    format_type="txt"
)
```

## Error Handling

The Import Manager provides comprehensive error handling:

```python
try:
    result = await manager.import_data(config)
    if result.status == ImportStatus.FAILED:
        print(f"Import failed: {result.error_message}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Configuration

The Import Manager uses a JSON configuration file:

```json
{
  "default_batch_size": 1000,
  "default_timeout": 300,
  "max_concurrent_imports": 5,
  "validation_enabled": true,
  "supported_formats": ["json", "csv", "xml", "txt"],
  "memory_coordination": {
    "enabled": true,
    "update_interval": 30
  }
}
```

## Memory Coordination

The Import Manager coordinates with other agents through memory updates:

```python
# Memory coordination is automatic during imports
# Status updates are written to coordination files
# Other agents can read these files for coordination
```

## Usage Examples

### Basic File Import

```python
from import_manager import create_import_manager, ImportConfig, ImportType

# Create manager
manager = create_import_manager()

# Configure import
config = ImportConfig(
    import_id="example_import",
    import_type=ImportType.FILE,
    source_path="example_data.json",
    format_type="json",
    validation_enabled=True
)

# Execute import
result = await manager.import_data(config)
print(f"Status: {result.status}")
print(f"Records processed: {result.records_processed}")
print(f"Success rate: {result.success_rate}%")
```

### Streaming Import

```python
config = ImportConfig(
    import_id="stream_import",
    import_type=ImportType.STREAM,
    source_path="stream://data/source",
    format_type="json",
    batch_size=500
)

result = await manager.import_data(config)
```

### Central Hub Integration

```python
from import_manager import create_central_hub_integration

# Create integration
integration = create_central_hub_integration()

# Import market data
result = await integration.import_market_data(
    source_path="market_data.json",
    format_type="json"
)

# Import trading signals
result = await integration.import_trading_signals(
    stream_source="stream://trading/signals"
)
```

### Monitoring Imports

```python
# Check import status
status = manager.get_import_status("my_import_id")
if status:
    print(f"Status: {status.status}")
    print(f"Progress: {status.records_processed} records")

# List all active imports
active_imports = manager.list_active_imports()
for import_result in active_imports:
    print(f"Import {import_result.import_id}: {import_result.status}")

# Get statistics
stats = manager.get_statistics()
print(f"Success rate: {stats['success_rate']}%")
print(f"Total imports: {stats['total_imports']}")
```

### Error Handling and Validation

```python
config = ImportConfig(
    import_id="validated_import",
    import_type=ImportType.FILE,
    source_path="data.csv",
    format_type="csv",
    validation_enabled=True,
    error_on_validation_failure=True,  # Fail on validation errors
    metadata={"min_columns": 5}  # Require at least 5 columns
)

try:
    result = await manager.import_data(config)
    if result.metadata.get('validation_passed'):
        print("Validation passed")
except ValueError as e:
    print(f"Validation failed: {e}")
```

## Integration with Central Hub

The Import Manager is designed to integrate seamlessly with the Central Hub:

1. **Memory Coordination**: Updates shared memory for agent communication
2. **Status Reporting**: Provides real-time status updates
3. **Error Reporting**: Comprehensive error reporting for debugging
4. **Performance Metrics**: Tracks performance for optimization

## Best Practices

1. **Use descriptive import IDs**: Include timestamp and data type
2. **Enable validation**: Always validate imported data in production
3. **Monitor imports**: Check status and statistics regularly
4. **Handle errors gracefully**: Implement proper error handling
5. **Use appropriate batch sizes**: Balance memory usage and performance
6. **Configure timeouts**: Set reasonable timeouts for your use case

## Troubleshooting

### Common Issues

1. **File not found**: Check source path exists and is accessible
2. **Invalid format**: Ensure file format matches format_type
3. **Memory issues**: Reduce batch_size for large files
4. **Timeout errors**: Increase timeout_seconds for slow operations
5. **Validation failures**: Check validation rules and data quality

### Debugging

```python
# Enable debug logging
import logging
logging.getLogger('import_manager').setLevel(logging.DEBUG)

# Check health status
health = await manager.health_check()
print(f"Health status: {health}")

# Get detailed statistics
stats = manager.get_statistics()
print(f"Detailed stats: {stats}")
```