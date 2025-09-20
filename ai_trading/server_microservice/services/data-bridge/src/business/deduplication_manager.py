# Service infrastructure - use absolute imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

try:
    from shared.infrastructure.core.logger_core import get_logger
    from shared.infrastructure.core.error_core import handle_error
    from shared.infrastructure.core.performance_core import performance_tracked
    from shared.infrastructure.core.config_core import CoreConfig
    from shared.infrastructure.core.cache_core import CoreCache
except ImportError as e:
    print(f"⚠️ Infrastructure import issue: {e}")
    # Fallback implementations
    import logging
    
    def get_logger(name, version=None):
        return logging.getLogger(name)
    
    def handle_error(service_name, error, context=None):
        print(f"Error in {service_name}: {error}")
        if context:
            print(f"Context: {context}")
    
    def performance_tracked(service_name, operation_name):
        def decorator(func):
            return func
        return decorator
    
    class CoreConfig:
        def __init__(self, service_name=None):
            pass
        def get(self, key, default=None):
            return default
    
    class CoreCache:
        def __init__(self, name, max_size=1000, default_ttl=300):
            self.name = name
            self.max_size = max_size
            self.default_ttl = default_ttl
            self.cache = {}
        
        async def get(self, key): 
            return None
        
        async def set(self, key, value, ttl=None): 
            pass

"""
Advanced Deduplication Manager for Historical Tick Data Downloads
Comprehensive system to prevent redundant downloads and ensure data completeness

Features:
- Timestamp-based deduplication at file and tick level
- Database query integration to check existing data
- Smart resume functionality for partial downloads
- Data integrity verification with checksums
- Gap detection and filling system
- Progress tracking and detailed logging
"""

import os
import json
import hashlib
import asyncio
import aiofiles
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set, Tuple, Any
from pathlib import Path
from dataclasses import dataclass, asdict
import pandas as pd

# Service-specific infrastructure
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

try:
    from shared.infrastructure.core.logger_core import get_logger
    from shared.infrastructure.core.config_core import CoreConfig
    from shared.infrastructure.core.performance_core import performance_tracked
except ImportError as e:
    print(f"⚠️ Infrastructure import issue: {e}")
    import logging
    get_logger = lambda name, version=None: logging.getLogger(name)
    CoreConfig = type('CoreConfig', (), {})
    performance_tracked = lambda service, operation: lambda func: func

from .database_client import get_database_client

logger = get_logger("data-bridge", "deduplication-manager")

@dataclass
class TimeRange:
    """Represents a time range for data downloads"""
    start: datetime
    end: datetime
    symbol: str
    source: str
    
    def overlaps_with(self, other: 'TimeRange') -> bool:
        """Check if this time range overlaps with another"""
        return (self.start <= other.end and self.end >= other.start and 
                self.symbol == other.symbol and self.source == other.source)
    
    def contains(self, timestamp: datetime) -> bool:
        """Check if a timestamp falls within this range"""
        return self.start <= timestamp <= self.end

@dataclass
class DownloadRecord:
    """Represents a completed download record"""
    symbol: str
    source: str
    time_range: TimeRange
    file_path: str
    file_size: int
    file_hash: str
    tick_count: int
    download_timestamp: datetime
    status: str  # completed, partial, failed
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        # Convert datetime objects to ISO strings
        result['time_range'] = {
            'start': self.time_range.start.isoformat(),
            'end': self.time_range.end.isoformat(),
            'symbol': self.time_range.symbol,
            'source': self.time_range.source
        }
        result['download_timestamp'] = self.download_timestamp.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DownloadRecord':
        """Create from dictionary (for JSON deserialization)"""
        time_range_data = data.pop('time_range')
        time_range = TimeRange(
            start=datetime.fromisoformat(time_range_data['start']),
            end=datetime.fromisoformat(time_range_data['end']),
            symbol=time_range_data['symbol'],
            source=time_range_data['source']
        )
        data['time_range'] = time_range
        data['download_timestamp'] = datetime.fromisoformat(data['download_timestamp'])
        return cls(**data)

@dataclass
class GapInfo:
    """Information about gaps in downloaded data"""
    symbol: str
    source: str
    gap_start: datetime
    gap_end: datetime
    priority: str  # high, medium, low
    reason: str

class DataBridgeDeduplicationManager:
    """
    Comprehensive deduplication manager for historical tick data downloads
    
    Prevents redundant downloads by:
    1. Maintaining a local registry of downloaded time periods
    2. Querying database for existing tick timestamps
    3. Calculating file checksums for integrity verification
    4. Smart gap detection and filling
    5. Resume functionality for partial downloads
    """
    
    def __init__(self, base_data_dir: str = "historical_data"):
        self.config = CoreConfig("data-bridge")
        self.cache = CoreCache("data-bridge-dedup", max_size=10000, default_ttl=3600)  # 1 hour cache
        
        self.base_data_dir = Path(base_data_dir)
        self.base_data_dir.mkdir(exist_ok=True)
        
        # Registry files for tracking downloads
        self.registry_dir = self.base_data_dir / "registry"
        self.registry_dir.mkdir(exist_ok=True)
        
        # Registry files
        self.download_registry_file = self.registry_dir / "download_registry.json"
        self.timestamp_index_file = self.registry_dir / "timestamp_index.json"
        self.checksum_registry_file = self.registry_dir / "checksum_registry.json"
        self.gaps_registry_file = self.registry_dir / "gaps_registry.json"
        
        # In-memory registries
        self.download_registry: Dict[str, List[DownloadRecord]] = {}
        self.timestamp_index: Dict[str, Dict[str, Set[str]]] = {}  # symbol -> source -> set of hour timestamps
        self.checksum_registry: Dict[str, str] = {}  # file_path -> hash
        self.gaps_registry: Dict[str, List[GapInfo]] = {}
        
        # Configuration
        self.batch_size = self.config.get('deduplication.batch_size', 100)
        self.integrity_check_enabled = self.config.get('deduplication.integrity_check', True)
        self.database_query_enabled = self.config.get('deduplication.database_query', True)
        self.auto_fill_gaps = self.config.get('deduplication.auto_fill_gaps', False)
        
        # Statistics
        self.stats = {
            "downloads_prevented": 0,
            "files_verified": 0,
            "gaps_detected": 0,
            "database_queries": 0,
            "cache_hits": 0,
            "integrity_failures": 0,
            "last_update": datetime.now(timezone.utc)
        }
        
        logger.info("Deduplication manager initialized", {
            "base_dir": str(self.base_data_dir),
            "registry_dir": str(self.registry_dir),
            "batch_size": self.batch_size,
            "integrity_check": self.integrity_check_enabled,
            "database_query": self.database_query_enabled
        })
    
    async def initialize(self):
        """Initialize deduplication manager and load existing registries"""
        try:
            await self._load_registries()
            await self._rebuild_timestamp_index()
            logger.info("Deduplication manager initialized successfully", {
                "total_records": sum(len(records) for records in self.download_registry.values()),
                "indexed_timestamps": sum(
                    sum(len(timestamps) for timestamps in sources.values()) 
                    for sources in self.timestamp_index.values()
                ),
                "checksums": len(self.checksum_registry),
                "gaps": sum(len(gaps) for gaps in self.gaps_registry.values())
            })
        except Exception as e:
            logger.error(f"Failed to initialize deduplication manager: {e}")
            raise
    
    @performance_tracked("unknown-service", "check_download_needed")
    async def check_download_needed(self, symbol: str, source: str, 
                                  start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """
        Check if a download is needed for the specified time range
        
        Returns:
            Dict with keys: needed (bool), missing_ranges (list), existing_ranges (list), reason (str)
        """
        try:
            cache_key = f"download_check:{symbol}:{source}:{start_time.isoformat()}:{end_time.isoformat()}"
            cached_result = await self.cache.get(cache_key)
            if cached_result:
                self.stats["cache_hits"] += 1
                return cached_result
            
            requested_range = TimeRange(start_time, end_time, symbol, source)
            
            # Step 1: Check local registry
            existing_ranges = await self._get_existing_ranges(symbol, source, start_time, end_time)
            
            # Step 2: Check database if enabled
            if self.database_query_enabled:
                database_ranges = await self._query_database_ranges(symbol, source, start_time, end_time)
                existing_ranges.extend(database_ranges)
            
            # Step 3: Calculate missing ranges
            missing_ranges = self._calculate_missing_ranges(requested_range, existing_ranges)
            
            # Step 4: Verify file integrity for existing ranges
            if self.integrity_check_enabled:
                verified_ranges = []
                for range_info in existing_ranges:
                    if await self._verify_range_integrity(range_info):
                        verified_ranges.append(range_info)
                    else:
                        # Add to missing ranges if integrity check fails
                        missing_ranges.append(range_info['time_range'])
                        self.stats["integrity_failures"] += 1
                existing_ranges = verified_ranges
            
            # Determine if download is needed
            download_needed = len(missing_ranges) > 0
            
            if download_needed:
                reason = f"Missing {len(missing_ranges)} time ranges"
                if not existing_ranges:
                    reason = "No existing data found"
                elif self.integrity_check_enabled and self.stats["integrity_failures"] > 0:
                    reason += f", {self.stats['integrity_failures']} integrity failures"
            else:
                reason = "All data already exists and verified"
                self.stats["downloads_prevented"] += 1
            
            result = {
                "needed": download_needed,
                "missing_ranges": [self._timerange_to_dict(r) for r in missing_ranges],
                "existing_ranges": existing_ranges,
                "reason": reason,
                "total_hours_missing": sum(
                    (r.end - r.start).total_seconds() / 3600 for r in missing_ranges
                ),
                "coverage_percent": (
                    (1 - len(missing_ranges) / max(1, len(existing_ranges) + len(missing_ranges))) * 100
                )
            }
            
            # Cache result for 1 hour
            await self.cache.set(cache_key, result, ttl=3600)
            
            logger.info(f"Download check completed for {symbol} {source}", {
                "needed": download_needed,
                "missing_ranges": len(missing_ranges),
                "existing_ranges": len(existing_ranges),
                "reason": reason
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking download needed: {e}")
            # Return conservative result - assume download is needed
            return {
                "needed": True,
                "missing_ranges": [self._timerange_to_dict(TimeRange(start_time, end_time, symbol, source))],
                "existing_ranges": [],
                "reason": f"Error during check: {e}",
                "total_hours_missing": (end_time - start_time).total_seconds() / 3600,
                "coverage_percent": 0
            }
    
    @performance_tracked("unknown-service", "record_download")
    async def record_download(self, symbol: str, source: str, 
                            start_time: datetime, end_time: datetime,
                            file_path: str, tick_count: int, 
                            status: str = "completed", 
                            metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Record a completed download in the registry
        
        Returns:
            Success status
        """
        try:
            if not Path(file_path).exists():
                logger.warning(f"File does not exist for recording: {file_path}")
                return False
            
            # Calculate file info
            file_stat = Path(file_path).stat()
            file_size = file_stat.st_size
            file_hash = await self._calculate_file_hash(file_path)
            
            # Create download record
            download_record = DownloadRecord(
                symbol=symbol,
                source=source,
                time_range=TimeRange(start_time, end_time, symbol, source),
                file_path=str(file_path),
                file_size=file_size,
                file_hash=file_hash,
                tick_count=tick_count,
                download_timestamp=datetime.now(timezone.utc),
                status=status,
                metadata=metadata or {}
            )
            
            # Add to registries
            key = f"{symbol}:{source}"
            if key not in self.download_registry:
                self.download_registry[key] = []
            
            self.download_registry[key].append(download_record)
            
            # Update timestamp index
            await self._update_timestamp_index(symbol, source, start_time, end_time)
            
            # Update checksum registry
            self.checksum_registry[str(file_path)] = file_hash
            
            # Save registries
            await self._save_registries()
            
            logger.info(f"Download recorded successfully", {
                "symbol": symbol,
                "source": source,
                "time_range": f"{start_time} to {end_time}",
                "file_size": file_size,
                "tick_count": tick_count,
                "status": status
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error recording download: {e}")
            return False
    
    @performance_tracked("unknown-service", "detect_gaps")
    async def detect_gaps(self, symbol: str, source: str, 
                         overall_start: datetime, overall_end: datetime,
                         expected_frequency: str = "hourly") -> List[GapInfo]:
        """
        Detect gaps in downloaded data for a symbol and source
        
        Args:
            expected_frequency: "hourly", "daily", or "continuous"
        """
        try:
            gaps = []
            
            # Get existing ranges
            existing_ranges = await self._get_existing_ranges(symbol, source, overall_start, overall_end)
            
            if not existing_ranges:
                # No data exists - entire range is a gap
                gaps.append(GapInfo(
                    symbol=symbol,
                    source=source,
                    gap_start=overall_start,
                    gap_end=overall_end,
                    priority="high",
                    reason="No data exists for time range"
                ))
            else:
                # Sort existing ranges by start time
                existing_ranges.sort(key=lambda x: x['time_range']['start'])
                
                # Check for gap before first range
                first_start = datetime.fromisoformat(existing_ranges[0]['time_range']['start'])
                if overall_start < first_start:
                    gaps.append(GapInfo(
                        symbol=symbol,
                        source=source,
                        gap_start=overall_start,
                        gap_end=first_start,
                        priority="medium",
                        reason="Gap before first data range"
                    ))
                
                # Check for gaps between ranges
                for i in range(len(existing_ranges) - 1):
                    current_end = datetime.fromisoformat(existing_ranges[i]['time_range']['end'])
                    next_start = datetime.fromisoformat(existing_ranges[i + 1]['time_range']['start'])
                    
                    if expected_frequency == "hourly":
                        # Allow up to 1 hour gap for hourly data
                        if (next_start - current_end).total_seconds() > 3600:
                            gaps.append(GapInfo(
                                symbol=symbol,
                                source=source,
                                gap_start=current_end,
                                gap_end=next_start,
                                priority="medium",
                                reason="Gap between data ranges"
                            ))
                    elif expected_frequency == "continuous":
                        # Any gap is significant for continuous data
                        if (next_start - current_end).total_seconds() > 60:  # More than 1 minute
                            gaps.append(GapInfo(
                                symbol=symbol,
                                source=source,
                                gap_start=current_end,
                                gap_end=next_start,
                                priority="high",
                                reason="Continuous data gap"
                            ))
                
                # Check for gap after last range
                last_end = datetime.fromisoformat(existing_ranges[-1]['time_range']['end'])
                if overall_end > last_end:
                    gaps.append(GapInfo(
                        symbol=symbol,
                        source=source,
                        gap_start=last_end,
                        gap_end=overall_end,
                        priority="medium",
                        reason="Gap after last data range"
                    ))
            
            # Update gaps registry
            key = f"{symbol}:{source}"
            self.gaps_registry[key] = gaps
            self.stats["gaps_detected"] = len(gaps)
            
            # Save gaps registry
            await self._save_gaps_registry()
            
            logger.info(f"Gap detection completed for {symbol} {source}", {
                "gaps_found": len(gaps),
                "overall_range": f"{overall_start} to {overall_end}",
                "existing_ranges": len(existing_ranges)
            })
            
            return gaps
            
        except Exception as e:
            logger.error(f"Error detecting gaps: {e}")
            return []
    
    async def get_download_recommendations(self, symbol: str, source: str) -> Dict[str, Any]:
        """
        Get recommendations for what data should be downloaded next
        """
        try:
            key = f"{symbol}:{source}"
            gaps = self.gaps_registry.get(key, [])
            
            # Sort gaps by priority and size
            high_priority_gaps = [g for g in gaps if g.priority == "high"]
            medium_priority_gaps = [g for g in gaps if g.priority == "medium"]
            
            recommendations = {
                "symbol": symbol,
                "source": source,
                "high_priority_gaps": len(high_priority_gaps),
                "medium_priority_gaps": len(medium_priority_gaps),
                "total_gaps": len(gaps),
                "recommended_downloads": []
            }
            
            # Add specific recommendations
            for gap in high_priority_gaps[:5]:  # Top 5 high priority
                recommendations["recommended_downloads"].append({
                    "priority": gap.priority,
                    "start": gap.gap_start.isoformat(),
                    "end": gap.gap_end.isoformat(),
                    "reason": gap.reason,
                    "duration_hours": (gap.gap_end - gap.gap_start).total_seconds() / 3600
                })
            
            for gap in medium_priority_gaps[:3]:  # Top 3 medium priority
                recommendations["recommended_downloads"].append({
                    "priority": gap.priority,
                    "start": gap.gap_start.isoformat(),
                    "end": gap.gap_end.isoformat(),
                    "reason": gap.reason,
                    "duration_hours": (gap.gap_end - gap.gap_start).total_seconds() / 3600
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return {"error": str(e)}
    
    def get_deduplication_stats(self) -> Dict[str, Any]:
        """Get comprehensive deduplication statistics"""
        return {
            **self.stats,
            "registry_summary": {
                "total_symbols": len(self.download_registry),
                "total_records": sum(len(records) for records in self.download_registry.values()),
                "total_files_tracked": len(self.checksum_registry),
                "total_gaps": sum(len(gaps) for gaps in self.gaps_registry.values())
            },
            "coverage_summary": {
                symbol_source: {
                    "records": len(records),
                    "total_hours": sum(
                        (r.time_range.end - r.time_range.start).total_seconds() / 3600 
                        for r in records
                    ),
                    "total_ticks": sum(r.tick_count for r in records)
                }
                for symbol_source, records in self.download_registry.items()
            }
        }
    
    # Private helper methods
    
    async def _load_registries(self):
        """Load all registries from files"""
        try:
            # Load download registry
            if self.download_registry_file.exists():
                async with aiofiles.open(self.download_registry_file, 'r') as f:
                    data = json.loads(await f.read())
                    self.download_registry = {
                        key: [DownloadRecord.from_dict(record) for record in records]
                        for key, records in data.items()
                    }
            
            # Load timestamp index
            if self.timestamp_index_file.exists():
                async with aiofiles.open(self.timestamp_index_file, 'r') as f:
                    data = json.loads(await f.read())
                    self.timestamp_index = {
                        symbol: {
                            source: set(timestamps) 
                            for source, timestamps in sources.items()
                        }
                        for symbol, sources in data.items()
                    }
            
            # Load checksum registry
            if self.checksum_registry_file.exists():
                async with aiofiles.open(self.checksum_registry_file, 'r') as f:
                    self.checksum_registry = json.loads(await f.read())
            
            # Load gaps registry
            if self.gaps_registry_file.exists():
                await self._load_gaps_registry()
            
        except Exception as e:
            logger.warning(f"Error loading registries: {e}")
            # Initialize empty registries if loading fails
            self.download_registry = {}
            self.timestamp_index = {}
            self.checksum_registry = {}
            self.gaps_registry = {}
    
    async def _save_registries(self):
        """Save all registries to files"""
        try:
            # Save download registry
            registry_data = {
                key: [record.to_dict() for record in records]
                for key, records in self.download_registry.items()
            }
            async with aiofiles.open(self.download_registry_file, 'w') as f:
                await f.write(json.dumps(registry_data, indent=2, default=str))
            
            # Save timestamp index
            timestamp_data = {
                symbol: {
                    source: list(timestamps)
                    for source, timestamps in sources.items()
                }
                for symbol, sources in self.timestamp_index.items()
            }
            async with aiofiles.open(self.timestamp_index_file, 'w') as f:
                await f.write(json.dumps(timestamp_data, indent=2))
            
            # Save checksum registry
            async with aiofiles.open(self.checksum_registry_file, 'w') as f:
                await f.write(json.dumps(self.checksum_registry, indent=2))
            
            self.stats["last_update"] = datetime.now(timezone.utc)
            
        except Exception as e:
            logger.error(f"Error saving registries: {e}")
    
    async def _load_gaps_registry(self):
        """Load gaps registry from file"""
        try:
            async with aiofiles.open(self.gaps_registry_file, 'r') as f:
                data = json.loads(await f.read())
                self.gaps_registry = {
                    key: [
                        GapInfo(
                            symbol=gap['symbol'],
                            source=gap['source'],
                            gap_start=datetime.fromisoformat(gap['gap_start']),
                            gap_end=datetime.fromisoformat(gap['gap_end']),
                            priority=gap['priority'],
                            reason=gap['reason']
                        )
                        for gap in gaps
                    ]
                    for key, gaps in data.items()
                }
        except Exception as e:
            logger.warning(f"Error loading gaps registry: {e}")
            self.gaps_registry = {}
    
    async def _save_gaps_registry(self):
        """Save gaps registry to file"""
        try:
            gaps_data = {
                key: [
                    {
                        "symbol": gap.symbol,
                        "source": gap.source,
                        "gap_start": gap.gap_start.isoformat(),
                        "gap_end": gap.gap_end.isoformat(),
                        "priority": gap.priority,
                        "reason": gap.reason
                    }
                    for gap in gaps
                ]
                for key, gaps in self.gaps_registry.items()
            }
            async with aiofiles.open(self.gaps_registry_file, 'w') as f:
                await f.write(json.dumps(gaps_data, indent=2))
        except Exception as e:
            logger.error(f"Error saving gaps registry: {e}")
    
    async def _rebuild_timestamp_index(self):
        """Rebuild timestamp index from download registry"""
        self.timestamp_index = {}
        
        for key, records in self.download_registry.items():
            symbol, source = key.split(':', 1)
            
            if symbol not in self.timestamp_index:
                self.timestamp_index[symbol] = {}
            if source not in self.timestamp_index[symbol]:
                self.timestamp_index[symbol][source] = set()
            
            for record in records:
                # Add hourly timestamps for the record's time range
                current_time = record.time_range.start.replace(minute=0, second=0, microsecond=0)
                end_time = record.time_range.end
                
                while current_time <= end_time:
                    self.timestamp_index[symbol][source].add(current_time.isoformat())
                    current_time += timedelta(hours=1)
    
    async def _get_existing_ranges(self, symbol: str, source: str, 
                                 start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Get existing download ranges for a symbol/source/time period"""
        key = f"{symbol}:{source}"
        records = self.download_registry.get(key, [])
        
        existing_ranges = []
        for record in records:
            # Check if record overlaps with requested time range
            if (record.time_range.start <= end_time and record.time_range.end >= start_time):
                existing_ranges.append({
                    "time_range": {
                        "start": record.time_range.start.isoformat(),
                        "end": record.time_range.end.isoformat()
                    },
                    "file_path": record.file_path,
                    "tick_count": record.tick_count,
                    "status": record.status,
                    "download_timestamp": record.download_timestamp.isoformat()
                })
        
        return existing_ranges
    
    async def _query_database_ranges(self, symbol: str, source: str,
                                   start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Query database for existing tick data ranges"""
        if not self.database_query_enabled:
            return []
        
        try:
            self.stats["database_queries"] += 1
            
            # Get database client
            db_client = await get_database_client()
            
            # Query for existing timestamps in the database
            # This is a simplified query - in a real implementation, you'd query for timestamp ranges
            query_result = await self._query_database_timestamps(db_client, symbol, start_time, end_time)
            
            # Convert database results to range format
            database_ranges = []
            if query_result:
                # Group consecutive timestamps into ranges
                timestamps = sorted(query_result)
                if timestamps:
                    range_start = timestamps[0]
                    range_end = timestamps[0]
                    
                    for ts in timestamps[1:]:
                        if (ts - range_end).total_seconds() <= 3600:  # Within 1 hour
                            range_end = ts
                        else:
                            # Gap found, close current range and start new one
                            database_ranges.append({
                                "time_range": {
                                    "start": range_start.isoformat(),
                                    "end": range_end.isoformat()
                                },
                                "file_path": "database",
                                "tick_count": -1,  # Unknown from database
                                "status": "database",
                                "download_timestamp": datetime.now(timezone.utc).isoformat()
                            })
                            range_start = ts
                            range_end = ts
                    
                    # Add final range
                    database_ranges.append({
                        "time_range": {
                            "start": range_start.isoformat(),
                            "end": range_end.isoformat()
                        },
                        "file_path": "database",
                        "tick_count": -1,
                        "status": "database", 
                        "download_timestamp": datetime.now(timezone.utc).isoformat()
                    })
            
            return database_ranges
            
        except Exception as e:
            logger.warning(f"Database query failed: {e}")
            return []
    
    async def _query_database_timestamps(self, db_client, symbol: str, 
                                       start_time: datetime, end_time: datetime) -> List[datetime]:
        """Query database for specific timestamps (placeholder - implement based on your DB schema)"""
        try:
            # This is a placeholder implementation
            # In a real implementation, you would query your ClickHouse database for timestamps
            
            # Example query structure (adapt to your actual database schema):
            # SELECT DISTINCT toStartOfHour(timestamp) as hour_timestamp 
            # FROM ticks 
            # WHERE symbol = '{symbol}' 
            #   AND timestamp >= '{start_time}' 
            #   AND timestamp <= '{end_time}'
            # ORDER BY hour_timestamp
            
            # For now, return empty list since we don't have direct database query capability
            return []
            
        except Exception as e:
            logger.error(f"Database timestamp query failed: {e}")
            return []
    
    def _calculate_missing_ranges(self, requested_range: TimeRange, 
                                existing_ranges: List[Dict[str, Any]]) -> List[TimeRange]:
        """Calculate missing time ranges that need to be downloaded"""
        if not existing_ranges:
            return [requested_range]
        
        # Convert existing ranges to TimeRange objects
        existing_time_ranges = []
        for range_data in existing_ranges:
            tr_data = range_data["time_range"]
            existing_time_ranges.append(TimeRange(
                start=datetime.fromisoformat(tr_data["start"]),
                end=datetime.fromisoformat(tr_data["end"]),
                symbol=requested_range.symbol,
                source=requested_range.source
            ))
        
        # Sort existing ranges by start time
        existing_time_ranges.sort(key=lambda x: x.start)
        
        # Find missing ranges
        missing_ranges = []
        current_time = requested_range.start
        
        for existing_range in existing_time_ranges:
            # If there's a gap before this existing range
            if current_time < existing_range.start:
                missing_ranges.append(TimeRange(
                    start=current_time,
                    end=existing_range.start,
                    symbol=requested_range.symbol,
                    source=requested_range.source
                ))
            
            # Move current time to the end of this existing range
            current_time = max(current_time, existing_range.end)
        
        # If there's a gap after all existing ranges
        if current_time < requested_range.end:
            missing_ranges.append(TimeRange(
                start=current_time,
                end=requested_range.end,
                symbol=requested_range.symbol,
                source=requested_range.source
            ))
        
        return missing_ranges
    
    async def _verify_range_integrity(self, range_info: Dict[str, Any]) -> bool:
        """Verify integrity of an existing data range"""
        if not self.integrity_check_enabled:
            return True
        
        try:
            file_path = range_info.get("file_path")
            if not file_path or file_path == "database":
                return True  # Can't verify database entries
            
            if not Path(file_path).exists():
                logger.warning(f"File missing for integrity check: {file_path}")
                return False
            
            # Check if we have a stored checksum
            stored_hash = self.checksum_registry.get(file_path)
            if stored_hash:
                current_hash = await self._calculate_file_hash(file_path)
                integrity_valid = stored_hash == current_hash
                if integrity_valid:
                    self.stats["files_verified"] += 1
                else:
                    logger.warning(f"Integrity check failed for {file_path}")
                return integrity_valid
            
            # No stored checksum, assume valid but calculate and store it
            current_hash = await self._calculate_file_hash(file_path)
            self.checksum_registry[file_path] = current_hash
            self.stats["files_verified"] += 1
            return True
            
        except Exception as e:
            logger.error(f"Error verifying integrity: {e}")
            return False
    
    async def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of a file"""
        try:
            hash_sha256 = hashlib.sha256()
            async with aiofiles.open(file_path, 'rb') as f:
                while chunk := await f.read(8192):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating file hash: {e}")
            return ""
    
    async def _update_timestamp_index(self, symbol: str, source: str, 
                                    start_time: datetime, end_time: datetime):
        """Update timestamp index with new time range"""
        if symbol not in self.timestamp_index:
            self.timestamp_index[symbol] = {}
        if source not in self.timestamp_index[symbol]:
            self.timestamp_index[symbol][source] = set()
        
        # Add hourly timestamps for the time range
        current_time = start_time.replace(minute=0, second=0, microsecond=0)
        while current_time <= end_time:
            self.timestamp_index[symbol][source].add(current_time.isoformat())
            current_time += timedelta(hours=1)
    
    def _timerange_to_dict(self, time_range: TimeRange) -> Dict[str, Any]:
        """Convert TimeRange to dictionary"""
        return {
            "start": time_range.start.isoformat(),
            "end": time_range.end.isoformat(),
            "symbol": time_range.symbol,
            "source": time_range.source
        }

# Global deduplication manager instance
_deduplication_manager: Optional[DataBridgeDeduplicationManager] = None

async def get_deduplication_manager() -> DataBridgeDeduplicationManager:
    """Get global deduplication manager instance"""
    global _deduplication_manager
    if _deduplication_manager is None:
        _deduplication_manager = DataBridgeDeduplicationManager()
        await _deduplication_manager.initialize()
    return _deduplication_manager

async def cleanup_deduplication_manager():
    """Cleanup global deduplication manager"""
    global _deduplication_manager
    if _deduplication_manager:
        await _deduplication_manager._save_registries()
        _deduplication_manager = None