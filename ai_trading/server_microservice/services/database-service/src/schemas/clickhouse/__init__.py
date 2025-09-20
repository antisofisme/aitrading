"""
ClickHouse Database Schemas
Complete schema collection organized by data type and processing stage
"""

from .raw_data_schemas import ClickhouseRawDataSchemas
from .indicator_schemas import ClickhouseIndicatorSchemas
from .external_data_schemas import ClickhouseExternalDataSchemas
from .ml_processing_schemas import ClickhouseMlProcessingSchemas
from .dl_processing_schemas import ClickhouseDlProcessingSchemas

# Create unified clickhouse schemas class
class ClickHouseSchemas:
    """Unified clickhouse schemas access"""
    ClickhouseRawData = ClickhouseRawDataSchemas
    ClickhouseIndicator = ClickhouseIndicatorSchemas
    ClickhouseExternalData = ClickhouseExternalDataSchemas
    ClickhouseMlProcessing = ClickhouseMlProcessingSchemas
    ClickhouseDlProcessing = ClickhouseDlProcessingSchemas

__all__ = [
    "ClickHouseSchemas",
   
    "ClickhouseRawDataSchemas",
    "ClickhouseIndicatorSchemas", 
    "ClickhouseExternalDataSchemas",
    "ClickhouseMlProcessingSchemas",
    "ClickhouseDlProcessingSchemas"
]