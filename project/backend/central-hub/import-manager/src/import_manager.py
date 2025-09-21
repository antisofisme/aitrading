"""
Import Manager - Phase 1 Infrastructure Migration

Purpose: Basic data import functionality for AI Trading Platform Central Hub
Phase: 1 - Infrastructure Migration 
Target: Simple and reliable import management for data sources

Features:
- File and stream processing
- Error handling and validation
- Central Hub integration
- Memory coordination for agent communication
- Simple configuration management
"""

import asyncio
import json
import logging
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import traceback


class ImportType(Enum):
    """Types of imports supported"""
    FILE = "file"
    STREAM = "stream"
    DATABASE = "database"
    API = "api"
    BATCH = "batch"


class ImportStatus(Enum):
    """Import operation status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ImportConfig:
    """Import configuration"""
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

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ImportResult:
    """Import operation result"""
    import_id: str
    status: ImportStatus
    records_processed: int = 0
    records_failed: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        total = self.records_processed + self.records_failed
        if total == 0:
            return 0.0
        return (self.records_processed / total) * 100


class ImportManager:
    """
    Import Manager for Phase 1 Infrastructure Migration
    
    Provides basic data import functionality with error handling,
    validation, and Central Hub integration.
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize Import Manager"""
        self.config_path = config_path or "/mnt/f/WINDSURF/neliti_code/aitrading/project/backend/central-hub/import-manager/config"
        self.logger = self._setup_logging()
        self.active_imports: Dict[str, ImportResult] = {}
        self.processors: Dict[ImportType, Callable] = {
            ImportType.FILE: self._process_file_import,
            ImportType.STREAM: self._process_stream_import,
            ImportType.DATABASE: self._process_database_import,
            ImportType.API: self._process_api_import,
            ImportType.BATCH: self._process_batch_import
        }
        self.validators: Dict[str, Callable] = {
            'json': self._validate_json,
            'csv': self._validate_csv,
            'xml': self._validate_xml
        }
        self._lock = threading.Lock()
        self._load_configuration()
        self.logger.info("Import Manager initialized successfully")

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for Import Manager"""
        logger = logging.getLogger('import_manager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # File handler
            log_dir = Path(self.config_path) / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_dir / "import_manager.log")
            file_handler.setLevel(logging.DEBUG)
            
            # Formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            file_handler.setFormatter(formatter)
            
            logger.addHandler(console_handler)
            logger.addHandler(file_handler)
            
        return logger

    def _load_configuration(self):
        """Load import manager configuration"""
        config_file = Path(self.config_path) / "import_config.json"
        
        # Create default config if it doesn't exist
        if not config_file.exists():
            default_config = {
                "default_batch_size": 1000,
                "default_timeout": 300,
                "max_concurrent_imports": 5,
                "validation_enabled": True,
                "error_on_validation_failure": False,
                "supported_formats": ["json", "csv", "xml", "txt"],
                "memory_coordination": {
                    "enabled": True,
                    "update_interval": 30
                }
            }
            
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            self.logger.info(f"Created default configuration at {config_file}")
        
        # Load configuration
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.logger.info(f"Configuration loaded from {config_file}")

    async def import_data(self, import_config: ImportConfig) -> ImportResult:
        """
        Main import method - handles all import types
        
        Args:
            import_config: Import configuration
            
        Returns:
            ImportResult with operation details
        """
        result = ImportResult(
            import_id=import_config.import_id,
            status=ImportStatus.PENDING,
            start_time=datetime.now()
        )
        
        # Store active import
        with self._lock:
            self.active_imports[import_config.import_id] = result
        
        try:
            self.logger.info(f"Starting import {import_config.import_id} - Type: {import_config.import_type.value}")
            
            # Update status to processing
            result.status = ImportStatus.PROCESSING
            
            # Coordinate via memory
            await self._update_memory_coordination(import_config, result)
            
            # Get appropriate processor
            processor = self.processors.get(import_config.import_type)
            if not processor:
                raise ValueError(f"Unsupported import type: {import_config.import_type}")
            
            # Process import
            await processor(import_config, result)
            
            # Validate if enabled
            if import_config.validation_enabled:
                await self._validate_import(import_config, result)
            
            # Mark as completed
            result.status = ImportStatus.COMPLETED
            result.end_time = datetime.now()
            
            self.logger.info(
                f"Import {import_config.import_id} completed successfully. "
                f"Processed: {result.records_processed}, Failed: {result.records_failed}"
            )
            
        except Exception as e:
            result.status = ImportStatus.FAILED
            result.end_time = datetime.now()
            result.error_message = str(e)
            
            self.logger.error(
                f"Import {import_config.import_id} failed: {e}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            
        finally:
            # Final memory coordination update
            await self._update_memory_coordination(import_config, result)
            
        return result

    async def _process_file_import(self, config: ImportConfig, result: ImportResult):
        """Process file-based imports"""
        source_path = Path(config.source_path)
        
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {config.source_path}")
        
        self.logger.info(f"Processing file import from {source_path}")
        
        # Read and process file based on format
        if config.format_type == 'json':
            await self._process_json_file(source_path, config, result)
        elif config.format_type == 'csv':
            await self._process_csv_file(source_path, config, result)
        elif config.format_type == 'xml':
            await self._process_xml_file(source_path, config, result)
        elif config.format_type == 'txt':
            await self._process_text_file(source_path, config, result)
        else:
            raise ValueError(f"Unsupported file format: {config.format_type}")

    async def _process_stream_import(self, config: ImportConfig, result: ImportResult):
        """Process streaming imports"""
        self.logger.info(f"Processing stream import from {config.source_path}")
        
        # Mock stream processing for Phase 1
        # In production, this would connect to actual streaming sources
        processed = 0
        batch_size = config.batch_size
        
        # Simulate processing batches
        for batch_num in range(5):  # Process 5 batches as example
            await asyncio.sleep(0.1)  # Simulate processing time
            processed += batch_size
            result.records_processed = processed
            
            self.logger.debug(f"Processed batch {batch_num + 1}, total records: {processed}")
            
            # Update coordination every batch
            await self._update_memory_coordination(config, result)

    async def _process_database_import(self, config: ImportConfig, result: ImportResult):
        """Process database imports"""
        self.logger.info(f"Processing database import from {config.source_path}")
        
        # Mock database processing for Phase 1
        # In production, this would connect to actual databases
        result.records_processed = 1500  # Mock processed count
        result.metadata['database_type'] = 'postgresql'
        result.metadata['query_executed'] = config.source_path

    async def _process_api_import(self, config: ImportConfig, result: ImportResult):
        """Process API imports"""
        self.logger.info(f"Processing API import from {config.source_path}")
        
        # Mock API processing for Phase 1
        # In production, this would make actual API calls
        result.records_processed = 750  # Mock processed count
        result.metadata['api_endpoint'] = config.source_path
        result.metadata['response_format'] = config.format_type

    async def _process_batch_import(self, config: ImportConfig, result: ImportResult):
        """Process batch imports"""
        self.logger.info(f"Processing batch import from {config.source_path}")
        
        # Mock batch processing for Phase 1
        batch_size = config.batch_size
        total_batches = 10
        
        for batch in range(total_batches):
            await asyncio.sleep(0.05)  # Simulate processing
            result.records_processed += batch_size
            
            if batch % 3 == 0:  # Update coordination every 3 batches
                await self._update_memory_coordination(config, result)

    async def _process_json_file(self, file_path: Path, config: ImportConfig, result: ImportResult):
        """Process JSON file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                result.records_processed = len(data)
            elif isinstance(data, dict):
                result.records_processed = 1
            else:
                result.records_processed = 1
                
            result.metadata['file_size'] = file_path.stat().st_size
            result.metadata['file_format'] = 'json'
            
        except json.JSONDecodeError as e:
            result.records_failed = 1
            raise ValueError(f"Invalid JSON format: {e}")

    async def _process_csv_file(self, file_path: Path, config: ImportConfig, result: ImportResult):
        """Process CSV file"""
        import csv
        
        try:
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                rows = list(reader)
                result.records_processed = len(rows) - 1  # Exclude header
                
            result.metadata['file_size'] = file_path.stat().st_size
            result.metadata['file_format'] = 'csv'
            result.metadata['columns'] = len(rows[0]) if rows else 0
            
        except Exception as e:
            result.records_failed = 1
            raise ValueError(f"CSV processing error: {e}")

    async def _process_xml_file(self, file_path: Path, config: ImportConfig, result: ImportResult):
        """Process XML file"""
        import xml.etree.ElementTree as ET
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Count child elements as records
            result.records_processed = len(list(root))
            result.metadata['file_size'] = file_path.stat().st_size
            result.metadata['file_format'] = 'xml'
            result.metadata['root_tag'] = root.tag
            
        except ET.ParseError as e:
            result.records_failed = 1
            raise ValueError(f"XML parsing error: {e}")

    async def _process_text_file(self, file_path: Path, config: ImportConfig, result: ImportResult):
        """Process text file"""
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            result.records_processed = len(lines)
            result.metadata['file_size'] = file_path.stat().st_size
            result.metadata['file_format'] = 'txt'
            result.metadata['encoding'] = 'utf-8'
            
        except Exception as e:
            result.records_failed = 1
            raise ValueError(f"Text file processing error: {e}")

    async def _validate_import(self, config: ImportConfig, result: ImportResult):
        """Validate import results"""
        validator = self.validators.get(config.format_type)
        if not validator:
            self.logger.warning(f"No validator available for format: {config.format_type}")
            return
        
        try:
            await validator(config, result)
            result.metadata['validation_passed'] = True
            self.logger.info(f"Validation passed for import {config.import_id}")
            
        except Exception as e:
            result.metadata['validation_passed'] = False
            result.metadata['validation_error'] = str(e)
            
            if config.error_on_validation_failure:
                raise ValueError(f"Validation failed: {e}")
            else:
                self.logger.warning(f"Validation failed for import {config.import_id}: {e}")

    async def _validate_json(self, config: ImportConfig, result: ImportResult):
        """Validate JSON import"""
        if result.records_processed == 0:
            raise ValueError("No records processed")
        
        # Basic validation - can be extended
        if result.records_failed > result.records_processed * 0.1:  # 10% failure threshold
            raise ValueError("Too many failed records")

    async def _validate_csv(self, config: ImportConfig, result: ImportResult):
        """Validate CSV import"""
        if result.records_processed == 0:
            raise ValueError("No records processed")
        
        # Check for minimum column count if specified
        min_columns = config.metadata.get('min_columns', 1)
        actual_columns = result.metadata.get('columns', 0)
        
        if actual_columns < min_columns:
            raise ValueError(f"Expected at least {min_columns} columns, got {actual_columns}")

    async def _validate_xml(self, config: ImportConfig, result: ImportResult):
        """Validate XML import"""
        if result.records_processed == 0:
            raise ValueError("No records processed")
        
        # Basic structure validation
        root_tag = result.metadata.get('root_tag')
        if not root_tag:
            raise ValueError("No root tag found in XML")

    async def _update_memory_coordination(self, config: ImportConfig, result: ImportResult):
        """Update memory for agent coordination"""
        if not self.config.get('memory_coordination', {}).get('enabled', True):
            return
        
        try:
            coordination_data = {
                'import_id': config.import_id,
                'import_type': config.import_type.value,
                'status': result.status.value,
                'records_processed': result.records_processed,
                'records_failed': result.records_failed,
                'timestamp': datetime.now().isoformat(),
                'agent': 'import_manager',
                'phase': 'infrastructure_migration'
            }
            
            # In a real implementation, this would use the actual memory coordination system
            # For Phase 1, we'll use a simple file-based approach
            memory_file = Path(self.config_path) / "coordination" / f"{config.import_id}_status.json"
            memory_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(memory_file, 'w') as f:
                json.dump(coordination_data, f, indent=2)
            
            self.logger.debug(f"Updated memory coordination for {config.import_id}")
            
        except Exception as e:
            self.logger.warning(f"Failed to update memory coordination: {e}")

    def get_import_status(self, import_id: str) -> Optional[ImportResult]:
        """Get status of specific import"""
        with self._lock:
            return self.active_imports.get(import_id)

    def list_active_imports(self) -> List[ImportResult]:
        """List all active imports"""
        with self._lock:
            return list(self.active_imports.values())

    def cancel_import(self, import_id: str) -> bool:
        """Cancel an active import"""
        with self._lock:
            if import_id in self.active_imports:
                result = self.active_imports[import_id]
                if result.status in [ImportStatus.PENDING, ImportStatus.PROCESSING]:
                    result.status = ImportStatus.CANCELLED
                    result.end_time = datetime.now()
                    self.logger.info(f"Import {import_id} cancelled")
                    return True
        return False

    def get_statistics(self) -> Dict[str, Any]:
        """Get import manager statistics"""
        with self._lock:
            total_imports = len(self.active_imports)
            completed = sum(1 for r in self.active_imports.values() if r.status == ImportStatus.COMPLETED)
            failed = sum(1 for r in self.active_imports.values() if r.status == ImportStatus.FAILED)
            processing = sum(1 for r in self.active_imports.values() if r.status == ImportStatus.PROCESSING)
            
            return {
                'total_imports': total_imports,
                'completed': completed,
                'failed': failed,
                'processing': processing,
                'success_rate': (completed / total_imports * 100) if total_imports > 0 else 0,
                'configuration': self.config
            }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'active_imports': len(self.active_imports),
            'configuration_loaded': bool(self.config),
            'logging_active': self.logger.isEnabledFor(logging.INFO)
        }
        
        # Check if config directory is accessible
        try:
            config_path = Path(self.config_path)
            health_status['config_directory_accessible'] = config_path.exists() and config_path.is_dir()
        except Exception:
            health_status['config_directory_accessible'] = False
            health_status['status'] = 'degraded'
        
        return health_status

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources"""
        self.logger.info("Import Manager shutting down")
        
        # Cancel any processing imports
        with self._lock:
            for import_id, result in self.active_imports.items():
                if result.status == ImportStatus.PROCESSING:
                    result.status = ImportStatus.CANCELLED
                    result.end_time = datetime.now()
                    self.logger.info(f"Cancelled import {import_id} during shutdown")


# Central Hub Integration
class CentralHubImportIntegration:
    """
    Integration layer between Import Manager and Central Hub
    Provides unified interface for Central Hub to use Import Manager
    """
    
    def __init__(self, import_manager: ImportManager):
        self.import_manager = import_manager
        self.logger = logging.getLogger('central_hub_import_integration')
    
    async def import_market_data(self, source_path: str, format_type: str = 'json') -> ImportResult:
        """Import market data for Central Hub"""
        config = ImportConfig(
            import_id=f"market_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            import_type=ImportType.FILE,
            source_path=source_path,
            format_type=format_type,
            batch_size=5000,
            validation_enabled=True,
            metadata={'data_type': 'market_data', 'source': 'central_hub'}
        )
        
        return await self.import_manager.import_data(config)
    
    async def import_trading_signals(self, stream_source: str) -> ImportResult:
        """Import trading signals via streaming"""
        config = ImportConfig(
            import_id=f"trading_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            import_type=ImportType.STREAM,
            source_path=stream_source,
            format_type='json',
            batch_size=1000,
            validation_enabled=True,
            metadata={'data_type': 'trading_signals', 'source': 'central_hub'}
        )
        
        return await self.import_manager.import_data(config)
    
    async def import_configuration(self, config_path: str) -> ImportResult:
        """Import configuration data"""
        config = ImportConfig(
            import_id=f"configuration_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            import_type=ImportType.FILE,
            source_path=config_path,
            format_type='json',
            validation_enabled=True,
            error_on_validation_failure=True,
            metadata={'data_type': 'configuration', 'source': 'central_hub'}
        )
        
        return await self.import_manager.import_data(config)


# Convenience functions for easy usage
def create_import_manager(config_path: Optional[str] = None) -> ImportManager:
    """Create and configure Import Manager instance"""
    return ImportManager(config_path)


def create_central_hub_integration(config_path: Optional[str] = None) -> CentralHubImportIntegration:
    """Create Central Hub integration with Import Manager"""
    import_manager = create_import_manager(config_path)
    return CentralHubImportIntegration(import_manager)


async def quick_import(source_path: str, import_type: ImportType = ImportType.FILE, 
                      format_type: str = 'json') -> ImportResult:
    """Quick import function for simple use cases"""
    with create_import_manager() as manager:
        config = ImportConfig(
            import_id=f"quick_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            import_type=import_type,
            source_path=source_path,
            format_type=format_type
        )
        return await manager.import_data(config)
