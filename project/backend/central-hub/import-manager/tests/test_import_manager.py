"""
Test Suite for Import Manager - Phase 1

Comprehensive tests for Import Manager functionality including:
- File processing
- Stream processing
- Error handling
- Validation
- Central Hub integration
- Memory coordination
"""

import asyncio
import json
import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from import_manager import (
    ImportManager,
    ImportConfig,
    ImportResult,
    ImportType,
    ImportStatus,
    CentralHubImportIntegration,
    create_import_manager,
    quick_import
)


class TestImportManager:
    """Test cases for ImportManager class"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def import_manager(self, temp_config_dir):
        """Create ImportManager instance with temporary config"""
        return ImportManager(config_path=temp_config_dir)
    
    @pytest.fixture
    def sample_json_file(self, temp_config_dir):
        """Create sample JSON file for testing"""
        data = {
            "records": [
                {"id": 1, "symbol": "EURUSD", "price": 1.1234},
                {"id": 2, "symbol": "GBPUSD", "price": 1.3456},
                {"id": 3, "symbol": "USDJPY", "price": 110.25}
            ],
            "timestamp": "2025-01-09T10:00:00Z"
        }
        
        file_path = Path(temp_config_dir) / "sample_data.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        return str(file_path)
    
    @pytest.fixture
    def sample_csv_file(self, temp_config_dir):
        """Create sample CSV file for testing"""
        csv_content = "symbol,price,timestamp\nEURUSD,1.1234,2025-01-09T10:00:00Z\nGBPUSD,1.3456,2025-01-09T10:01:00Z\nUSDJPY,110.25,2025-01-09T10:02:00Z\n"
        
        file_path = Path(temp_config_dir) / "sample_data.csv"
        with open(file_path, 'w') as f:
            f.write(csv_content)
        
        return str(file_path)
    
    def test_import_manager_initialization(self, temp_config_dir):
        """Test ImportManager initialization"""
        manager = ImportManager(config_path=temp_config_dir)
        
        assert manager.config_path == temp_config_dir
        assert manager.logger is not None
        assert isinstance(manager.active_imports, dict)
        assert len(manager.processors) == 5
        assert len(manager.validators) == 3
        assert manager.config is not None
    
    def test_configuration_loading(self, import_manager):
        """Test configuration loading and default creation"""
        assert import_manager.config is not None
        assert 'default_batch_size' in import_manager.config
        assert 'supported_formats' in import_manager.config
        assert 'memory_coordination' in import_manager.config
        
        # Check config file was created
        config_file = Path(import_manager.config_path) / "import_config.json"
        assert config_file.exists()
    
    @pytest.mark.asyncio
    async def test_json_file_import(self, import_manager, sample_json_file):
        """Test JSON file import"""
        config = ImportConfig(
            import_id="test_json_import",
            import_type=ImportType.FILE,
            source_path=sample_json_file,
            format_type="json"
        )
        
        result = await import_manager.import_data(config)
        
        assert result.status == ImportStatus.COMPLETED
        assert result.records_processed > 0
        assert result.records_failed == 0
        assert result.error_message is None
        assert 'file_format' in result.metadata
        assert result.metadata['file_format'] == 'json'
    
    @pytest.mark.asyncio
    async def test_csv_file_import(self, import_manager, sample_csv_file):
        """Test CSV file import"""
        config = ImportConfig(
            import_id="test_csv_import",
            import_type=ImportType.FILE,
            source_path=sample_csv_file,
            format_type="csv"
        )
        
        result = await import_manager.import_data(config)
        
        assert result.status == ImportStatus.COMPLETED
        assert result.records_processed == 3  # 4 lines - 1 header
        assert result.records_failed == 0
        assert 'columns' in result.metadata
        assert result.metadata['columns'] == 3
    
    @pytest.mark.asyncio
    async def test_stream_import(self, import_manager):
        """Test stream import processing"""
        config = ImportConfig(
            import_id="test_stream_import",
            import_type=ImportType.STREAM,
            source_path="mock://stream/endpoint",
            format_type="json",
            batch_size=500
        )
        
        result = await import_manager.import_data(config)
        
        assert result.status == ImportStatus.COMPLETED
        assert result.records_processed > 0
        assert result.records_failed == 0
    
    @pytest.mark.asyncio
    async def test_database_import(self, import_manager):
        """Test database import processing"""
        config = ImportConfig(
            import_id="test_database_import",
            import_type=ImportType.DATABASE,
            source_path="SELECT * FROM market_data LIMIT 1000",
            format_type="json"
        )
        
        result = await import_manager.import_data(config)
        
        assert result.status == ImportStatus.COMPLETED
        assert result.records_processed == 1500  # Mock value
        assert 'database_type' in result.metadata
    
    @pytest.mark.asyncio
    async def test_api_import(self, import_manager):
        """Test API import processing"""
        config = ImportConfig(
            import_id="test_api_import",
            import_type=ImportType.API,
            source_path="https://api.example.com/market-data",
            format_type="json"
        )
        
        result = await import_manager.import_data(config)
        
        assert result.status == ImportStatus.COMPLETED
        assert result.records_processed == 750  # Mock value
        assert 'api_endpoint' in result.metadata
    
    @pytest.mark.asyncio
    async def test_batch_import(self, import_manager):
        """Test batch import processing"""
        config = ImportConfig(
            import_id="test_batch_import",
            import_type=ImportType.BATCH,
            source_path="batch://data/source",
            format_type="json",
            batch_size=1000
        )
        
        result = await import_manager.import_data(config)
        
        assert result.status == ImportStatus.COMPLETED
        assert result.records_processed == 10000  # 10 batches * 1000
        assert result.records_failed == 0
    
    @pytest.mark.asyncio
    async def test_file_not_found_error(self, import_manager):
        """Test handling of file not found error"""
        config = ImportConfig(
            import_id="test_file_not_found",
            import_type=ImportType.FILE,
            source_path="/nonexistent/file.json",
            format_type="json"
        )
        
        result = await import_manager.import_data(config)
        
        assert result.status == ImportStatus.FAILED
        assert "not found" in result.error_message
    
    @pytest.mark.asyncio
    async def test_invalid_json_error(self, import_manager, temp_config_dir):
        """Test handling of invalid JSON file"""
        # Create invalid JSON file
        invalid_file = Path(temp_config_dir) / "invalid.json"
        with open(invalid_file, 'w') as f:
            f.write('{"invalid": json}')
        
        config = ImportConfig(
            import_id="test_invalid_json",
            import_type=ImportType.FILE,
            source_path=str(invalid_file),
            format_type="json"
        )
        
        result = await import_manager.import_data(config)
        
        assert result.status == ImportStatus.FAILED
        assert "Invalid JSON format" in result.error_message
    
    @pytest.mark.asyncio
    async def test_validation_enabled(self, import_manager, sample_json_file):
        """Test import with validation enabled"""
        config = ImportConfig(
            import_id="test_validation",
            import_type=ImportType.FILE,
            source_path=sample_json_file,
            format_type="json",
            validation_enabled=True
        )
        
        result = await import_manager.import_data(config)
        
        assert result.status == ImportStatus.COMPLETED
        assert result.metadata.get('validation_passed') is True
    
    @pytest.mark.asyncio
    async def test_validation_failure_non_critical(self, import_manager):
        """Test validation failure with error_on_validation_failure=False"""
        config = ImportConfig(
            import_id="test_validation_failure",
            import_type=ImportType.FILE,
            source_path="/nonexistent/file.json",
            format_type="json",
            validation_enabled=True,
            error_on_validation_failure=False
        )
        
        result = await import_manager.import_data(config)
        
        # Should fail due to file not found, not validation
        assert result.status == ImportStatus.FAILED
    
    def test_get_import_status(self, import_manager):
        """Test getting import status"""
        # No active imports initially
        status = import_manager.get_import_status("nonexistent")
        assert status is None
        
        # Add a mock import
        result = ImportResult(
            import_id="test_import",
            status=ImportStatus.PROCESSING
        )
        import_manager.active_imports["test_import"] = result
        
        status = import_manager.get_import_status("test_import")
        assert status is not None
        assert status.import_id == "test_import"
        assert status.status == ImportStatus.PROCESSING
    
    def test_list_active_imports(self, import_manager):
        """Test listing active imports"""
        # Initially empty
        imports = import_manager.list_active_imports()
        assert len(imports) == 0
        
        # Add mock imports
        for i in range(3):
            result = ImportResult(
                import_id=f"test_import_{i}",
                status=ImportStatus.PROCESSING
            )
            import_manager.active_imports[f"test_import_{i}"] = result
        
        imports = import_manager.list_active_imports()
        assert len(imports) == 3
    
    def test_cancel_import(self, import_manager):
        """Test cancelling an import"""
        # Add a processing import
        result = ImportResult(
            import_id="test_cancel",
            status=ImportStatus.PROCESSING
        )
        import_manager.active_imports["test_cancel"] = result
        
        # Cancel it
        cancelled = import_manager.cancel_import("test_cancel")
        assert cancelled is True
        
        # Check status
        status = import_manager.get_import_status("test_cancel")
        assert status.status == ImportStatus.CANCELLED
        
        # Try to cancel non-existent
        cancelled = import_manager.cancel_import("nonexistent")
        assert cancelled is False
    
    def test_get_statistics(self, import_manager):
        """Test getting import statistics"""
        # Add various import results
        statuses = [ImportStatus.COMPLETED, ImportStatus.FAILED, ImportStatus.PROCESSING, ImportStatus.COMPLETED]
        
        for i, status in enumerate(statuses):
            result = ImportResult(
                import_id=f"test_stats_{i}",
                status=status
            )
            import_manager.active_imports[f"test_stats_{i}"] = result
        
        stats = import_manager.get_statistics()
        
        assert stats['total_imports'] == 4
        assert stats['completed'] == 2
        assert stats['failed'] == 1
        assert stats['processing'] == 1
        assert stats['success_rate'] == 50.0
        assert 'configuration' in stats
    
    @pytest.mark.asyncio
    async def test_health_check(self, import_manager):
        """Test health check functionality"""
        health = await import_manager.health_check()
        
        assert health['status'] == 'healthy'
        assert 'timestamp' in health
        assert health['active_imports'] == 0
        assert health['configuration_loaded'] is True
        assert health['logging_active'] is True
        assert health['config_directory_accessible'] is True
    
    def test_context_manager(self, temp_config_dir):
        """Test ImportManager as context manager"""
        with ImportManager(config_path=temp_config_dir) as manager:
            assert manager is not None
            
            # Add a processing import
            result = ImportResult(
                import_id="context_test",
                status=ImportStatus.PROCESSING
            )
            manager.active_imports["context_test"] = result
        
        # Should be cancelled after exit
        # Note: In the actual implementation, we'd check the status was set to CANCELLED


class TestCentralHubIntegration:
    """Test cases for Central Hub integration"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def integration(self, temp_config_dir):
        """Create Central Hub integration instance"""
        import_manager = ImportManager(config_path=temp_config_dir)
        return CentralHubImportIntegration(import_manager)
    
    @pytest.fixture
    def sample_market_data_file(self, temp_config_dir):
        """Create sample market data file"""
        data = {
            "market_data": [
                {"symbol": "EURUSD", "bid": 1.1234, "ask": 1.1236, "timestamp": "2025-01-09T10:00:00Z"},
                {"symbol": "GBPUSD", "bid": 1.3454, "ask": 1.3458, "timestamp": "2025-01-09T10:01:00Z"}
            ]
        }
        
        file_path = Path(temp_config_dir) / "market_data.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        return str(file_path)
    
    @pytest.mark.asyncio
    async def test_import_market_data(self, integration, sample_market_data_file):
        """Test importing market data through Central Hub integration"""
        result = await integration.import_market_data(sample_market_data_file, "json")
        
        assert result.status == ImportStatus.COMPLETED
        assert result.records_processed > 0
        assert result.metadata['data_type'] == 'market_data'
        assert result.metadata['source'] == 'central_hub'
        assert result.import_id.startswith('market_data_')
    
    @pytest.mark.asyncio
    async def test_import_trading_signals(self, integration):
        """Test importing trading signals via streaming"""
        result = await integration.import_trading_signals("stream://trading/signals")
        
        assert result.status == ImportStatus.COMPLETED
        assert result.records_processed > 0
        assert result.metadata['data_type'] == 'trading_signals'
        assert result.metadata['source'] == 'central_hub'
        assert result.import_id.startswith('trading_signals_')
    
    @pytest.mark.asyncio
    async def test_import_configuration(self, integration, temp_config_dir):
        """Test importing configuration data"""
        # Create sample config file
        config_data = {
            "trading_parameters": {
                "max_position_size": 10000,
                "risk_level": 0.02
            },
            "api_settings": {
                "timeout": 30,
                "retries": 3
            }
        }
        
        config_file = Path(temp_config_dir) / "trading_config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        result = await integration.import_configuration(str(config_file))
        
        assert result.status == ImportStatus.COMPLETED
        assert result.records_processed > 0
        assert result.metadata['data_type'] == 'configuration'
        assert result.metadata['source'] == 'central_hub'
        assert result.import_id.startswith('configuration_')


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    def test_create_import_manager(self, temp_config_dir):
        """Test create_import_manager function"""
        manager = create_import_manager(temp_config_dir)
        
        assert isinstance(manager, ImportManager)
        assert manager.config_path == temp_config_dir
    
    def test_create_central_hub_integration(self, temp_config_dir):
        """Test create_central_hub_integration function"""
        integration = create_central_hub_integration(temp_config_dir)
        
        assert isinstance(integration, CentralHubImportIntegration)
        assert isinstance(integration.import_manager, ImportManager)
    
    @pytest.mark.asyncio
    async def test_quick_import(self, temp_config_dir):
        """Test quick_import function"""
        # Create sample file
        data = {"test": "data"}
        file_path = Path(temp_config_dir) / "quick_test.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        result = await quick_import(str(file_path), ImportType.FILE, "json")
        
        assert result.status == ImportStatus.COMPLETED
        assert result.records_processed > 0
        assert result.import_id.startswith('quick_import_')


class TestMemoryCoordination:
    """Test memory coordination functionality"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def import_manager(self, temp_config_dir):
        """Create ImportManager instance with memory coordination enabled"""
        return ImportManager(config_path=temp_config_dir)
    
    @pytest.mark.asyncio
    async def test_memory_coordination_update(self, import_manager, temp_config_dir):
        """Test memory coordination updates during import"""
        # Create sample file
        data = {"coordination": "test"}
        file_path = Path(temp_config_dir) / "coordination_test.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        config = ImportConfig(
            import_id="coordination_test",
            import_type=ImportType.FILE,
            source_path=str(file_path),
            format_type="json"
        )
        
        result = await import_manager.import_data(config)
        
        # Check that coordination file was created
        coordination_file = Path(import_manager.config_path) / "coordination" / "coordination_test_status.json"
        assert coordination_file.exists()
        
        # Check coordination data
        with open(coordination_file, 'r') as f:
            coordination_data = json.load(f)
        
        assert coordination_data['import_id'] == 'coordination_test'
        assert coordination_data['agent'] == 'import_manager'
        assert coordination_data['phase'] == 'infrastructure_migration'
        assert coordination_data['status'] == 'completed'


if __name__ == "__main__":
    # Run specific tests for development
    pytest.main(["-v", __file__])