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
Dukascopy & TrueFX Historical Tick Data Downloader
Automated download system for high-quality historical tick data
No account registration required - direct HTTP downloads

Sources:
- Dukascopy: Swiss bank, highest accuracy (98-99%)
- TrueFX: Institutional feeds, validation data (95-98%)
"""

import os
import asyncio
import aiohttp
import aiofiles
import struct
import gzip
import zipfile
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import pandas as pd
from pathlib import Path
import time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import json
import socket

# Additional infrastructure imports for fallback compatibility
try:
    from shared.infrastructure.core.config_core import CoreConfig
    from shared.infrastructure.core.performance_core import performance_tracked
except ImportError:
    pass
from ..business.deduplication_manager import get_deduplication_manager

# Import central proxy manager and trading calendar
try:
    from shared.infrastructure.network import ProxyManager
except ImportError:
    class ProxyManager:
        def __init__(self, *args, **kwargs): pass
        def get_proxies(self): return []
from ..business.trading_calendar import get_trading_calendar

logger = get_logger("data-bridge", "dukascopy-client")

class DataBridgeDukascopyDownloader:
    """
    Data Bridge Service - Dukascopy and TrueFX Historical Downloader
    
    Features:
    - No account registration required
    - Highest accuracy data sources  
    - Parallel downloads with retry logic
    - Data validation and quality checks
    - Automatic format conversion
    """
    
    def __init__(self, base_data_dir: str = "historical_data"):
        self.config = CoreConfig("data-bridge")
        nce
        self.performance = CorePerformance("data-bridge")
        
        self.base_data_dir = Path(base_data_dir)
        self.base_data_dir.mkdir(exist_ok=True)
        
        # Initialize deduplication manager and trading calendar
        self.deduplication_manager = None
        self.trading_calendar = get_trading_calendar()
        
        # Create subdirectories
        self.dukascopy_dir = self.base_data_dir / "dukascopy"
        self.truefx_dir = self.base_data_dir / "truefx"
        self.processed_dir = self.base_data_dir / "processed"
        self.reports_dir = self.base_data_dir / "reports"
        
        for dir_path in [self.dukascopy_dir, self.truefx_dir, self.processed_dir, self.reports_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Core focus pairs: Gold and high correlation with EURUSD
        self.core_pairs = [
            "XAUUSD",  # Gold - Primary focus
            "EURUSD",  # EUR/USD - Primary focus
        ]
        
        # High correlation pairs with Gold (negative correlation with USD strength)
        self.gold_correlation_pairs = [
            "XAGUSD",  # Silver - High correlation with Gold (~0.85)
            "AUDUSD",  # Australian Dollar - Gold mining country (~0.75)
            "NZDUSD",  # New Zealand Dollar - Commodity currency (~0.65)
            "USDCHF",  # Swiss Franc - Safe haven, inverse correlation (~-0.60)
        ]
        
        # High correlation pairs with EURUSD (EUR strength vs USD)
        self.eurusd_correlation_pairs = [
            "GBPUSD",  # British Pound - High correlation with EUR (~0.85)
            "AUDUSD",  # Australian Dollar - Risk-on currency (~0.75)
            "NZDUSD",  # New Zealand Dollar - Risk-on currency (~0.70)
            "EURJPY",  # EUR/JPY - EUR strength indicator (~0.80)
            "EURGBP",  # EUR/GBP - Direct EUR strength (~0.60)
        ]
        
        # Major USD pairs for cross-validation
        self.usd_strength_pairs = [
            "USDJPY",  # USD/JPY - USD strength indicator
            "USDCAD",  # USD/CAD - Commodity vs USD
            "USDCHF",  # USD/CHF - Safe haven analysis
        ]
        
        # Combined optimized pairs for Gold-EURUSD correlation analysis
        self.optimized_pairs = list(set(
            self.core_pairs + 
            self.gold_correlation_pairs + 
            self.eurusd_correlation_pairs + 
            self.usd_strength_pairs
        ))
        
        # Legacy major pairs (for backward compatibility)
        self.major_pairs = [
            "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD",
            "USDCAD", "NZDUSD", "EURJPY", "GBPJPY", "AUDJPY"
        ]
        
        self.metal_pairs = [
            "XAUUSD",  # Gold
            "XAGUSD",  # Silver
        ]
        
        # All available pairs
        self.all_pairs = self.optimized_pairs + self.major_pairs + self.metal_pairs
        
        # Download statistics
        self.download_stats = {
            "dukascopy": {"files": 0, "size_mb": 0, "errors": 0, "pairs": {}},
            "truefx": {"files": 0, "size_mb": 0, "errors": 0, "pairs": {}},
            "processed": {"files": 0, "size_mb": 0, "errors": 0, "total_rows": 0}
        }
        
        # HTTP session settings - SAME AS WORKING SERVER_SIDE VERSION
        self.session_timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes (same as server_side)
        self.max_concurrent_downloads = 3  # Same as server_side working config
        self.retry_attempts = 3  # Same as server_side
        self.delay_between_requests = 0.1  # Small delay to be respectful (same as server_side)
        
        # Initialize central proxy manager
        self.proxy_manager = ProxyManager("data-bridge")
        
    async def initialize_deduplication(self):
        """Initialize deduplication manager"""
        if self.deduplication_manager is None:
            self.deduplication_manager = await get_deduplication_manager()
            logger.info("Deduplication manager initialized for Dukascopy downloader")
    
    async def _create_http_session(self) -> aiohttp.ClientSession:
        """Create HTTP session using central proxy manager"""
        try:
            # Use central proxy manager for session creation
            session = await self.proxy_manager.create_http_session()
            logger.info("✅ HTTP session created using central proxy manager")
            return session
        except Exception as e:
            logger.error(f"Failed to create HTTP session via proxy manager: {e}")
            # Fallback to basic connection
            logger.info("📡 Falling back to basic connection")
            return aiohttp.ClientSession(timeout=self.session_timeout)
    
        
    @performance_tracked("unknown-service", "download_small_batch")
    async def download_small_batch(self, 
                                 pair: str = "EURUSD",
                                 hours_back: int = None) -> Dict[str, any]:
        """
        Download small batch for connection-limited environments with deduplication
        
        Args:
            pair: Single currency pair to download
            hours_back: Number of hours back from now (default from env: DUKASCOPY_HOURS_BACK)
            
        Returns:
            Dictionary with download results
        """
        from datetime import datetime, timedelta
        import time
        
        # Get hours_back from environment if not provided
        if hours_back is None:
            hours_back = int(os.getenv("DUKASCOPY_HOURS_BACK", "720"))  # Default 1 month
        
        logger.info(f"🚀 Starting SMART DOWNLOAD with deduplication: {pair} for last {hours_back} hours")
        
        # Initialize deduplication manager
        await self.initialize_deduplication()
        
        start_time = time.time()
        results = {
            "pair": pair,
            "hours_back": hours_back,
            "files_downloaded": 0,
            "files_failed": 0,
            "files_skipped_dedup": 0,
            "total_size_mb": 0.0,
            "duration_seconds": 0.0,
            "success_rate": 0.0,
            "files": [],
            "deduplication_stats": {}
        }
        
        # Calculate time range using trading calendar
        end_time = datetime.now()
        start_download_time = end_time - timedelta(hours=hours_back)
        
        logger.info(f"📅 Time range: {start_download_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}")
        
        # Show current market status (informational only - doesn't block downloads)
        market_status = self.trading_calendar.get_market_status()
        logger.info(f"📊 Download timing: {market_status['recommendation']} - {market_status['reason']}")
        logger.info(f"📊 Data quality expected: {market_status['data_quality']}")
        
        if market_status['data_quality'] == 'NONE':
            logger.info("💡 Note: Downloading on weekend - will filter out weekend data automatically (forex closes Sat-Sun only)")
        elif market_status['data_quality'] == 'LIMITED':
            logger.info("⏰ Outside active hours - some time ranges may have limited data")
        
        # Check what downloads are needed using deduplication manager
        dedup_check = await self.deduplication_manager.check_download_needed(
            symbol=pair,
            source="dukascopy",
            start_time=start_download_time,
            end_time=end_time
        )
        
        results["deduplication_stats"] = {
            "download_needed": dedup_check["needed"],
            "missing_ranges": len(dedup_check["missing_ranges"]),
            "existing_ranges": len(dedup_check["existing_ranges"]),
            "coverage_percent": dedup_check["coverage_percent"],
            "reason": dedup_check["reason"]
        }
        
        if not dedup_check["needed"]:
            logger.info(f"✅ DEDUPLICATION: All data already exists for {pair} ({dedup_check['reason']})")
            results["duration_seconds"] = time.time() - start_time
            results["success_rate"] = 1.0
            results["files_skipped_dedup"] = len(dedup_check["existing_ranges"])
            return results
        
        logger.info(f"📊 DEDUPLICATION: {len(dedup_check['missing_ranges'])} ranges need download, "
                   f"{len(dedup_check['existing_ranges'])} already exist ({dedup_check['coverage_percent']:.1f}% coverage)")
        
        # Create pair directory
        pair_dir = self.dukascopy_dir / pair
        pair_dir.mkdir(exist_ok=True)
        
        # Generate download tasks only for missing ranges (smart deduplication)
        download_tasks = []
        
        for missing_range_dict in dedup_check["missing_ranges"]:
            range_start = datetime.fromisoformat(missing_range_dict["start"])
            range_end = datetime.fromisoformat(missing_range_dict["end"])
            
            current_time = range_start.replace(minute=0, second=0, microsecond=0)
            
            while current_time <= range_end:
                # CRITICAL: Skip weekend DATA (not download time) for ML/DL consistency
                # Forex only closes weekends (Sat-Sun), NOT national holidays
                if not self.trading_calendar.is_trading_day(current_time):
                    logger.debug(f"⏭️  Skipping weekend DATA: {current_time.strftime('%Y-%m-%d %H:00')} ({current_time.strftime('%A')}) - forex market closed")
                    current_time += timedelta(hours=1)
                    continue
                
                year = current_time.year
                month = current_time.month
                day = current_time.day
                hour = current_time.hour
                
                url = self._build_dukascopy_url(pair, year, month, day, hour)
                filename = f"{pair}_{year}_{month:02d}_{day:02d}_{hour:02d}.bi5"
                filepath = pair_dir / filename
                
                # Additional check: Skip if file exists and is not empty (double-check)
                if not filepath.exists() or filepath.stat().st_size == 0:
                    download_tasks.append({
                        "url": url,
                        "filepath": filepath,
                        "time_str": current_time.strftime('%Y-%m-%d %H:00'),
                        "timestamp": current_time,
                        "is_trading_day": True  # Mark as verified trading day
                    })
                
                current_time += timedelta(hours=1)
        
        logger.info(f"📊 Found {len(download_tasks)} files to download")
        
        if not download_tasks:
            logger.info("ℹ️  All files already exist")
            results["success_rate"] = 1.0
            results["duration_seconds"] = time.time() - start_time
            return results
        
        # Download files one by one (ultra conservative) with WARP proxy support
        session = await self._create_http_session()
        try:
            for i, task in enumerate(download_tasks):
                try:
                    logger.info(f"📥 Downloading {i+1}/{len(download_tasks)}: {task['time_str']}")
                    
                    result = await self._download_dukascopy_file(session, task["url"], task["filepath"])
                    
                    if result and result.get("success"):
                        results["files_downloaded"] += 1
                        results["total_size_mb"] += result.get("size_mb", 0)
                        results["files"].append({
                            "time": task["time_str"],
                            "size_mb": result.get("size_mb", 0),
                            "status": "success"
                        })
                        
                        # Record successful download in deduplication manager
                        try:
                            await self.deduplication_manager.record_download(
                                symbol=pair,
                                source="dukascopy",
                                start_time=task["timestamp"],
                                end_time=task["timestamp"] + timedelta(hours=1),
                                file_path=str(task["filepath"]),
                                tick_count=0,  # Will be updated during processing
                                status="completed",
                                metadata={
                                    "file_size_mb": result.get("size_mb", 0),
                                    "download_method": "small_batch"
                                }
                            )
                        except Exception as e:
                            logger.warning(f"Failed to record download in deduplication manager: {e}")
                        
                        logger.info(f"  ✅ Success: {result.get('size_mb', 0):.2f} MB (recorded in registry)")
                    else:
                        results["files_failed"] += 1
                        results["files"].append({
                            "time": task["time_str"],
                            "size_mb": 0,
                            "status": "failed"
                        })
                        logger.info(f"  ❌ Failed or no data")
                    
                    # Respectful delay between downloads
                    await asyncio.sleep(self.delay_between_requests)
                    
                except Exception as e:
                    results["files_failed"] += 1
                    results["files"].append({
                        "time": task["time_str"],
                        "size_mb": 0,
                        "status": "error",
                        "error": str(e)[:100]
                    })
                    logger.error(f"  ❌ Error: {str(e)[:50]}")
        finally:
            await session.close()
        
        # Calculate final statistics
        results["duration_seconds"] = time.time() - start_time
        total_files = results["files_downloaded"] + results["files_failed"]
        results["success_rate"] = (results["files_downloaded"] / total_files) if total_files > 0 else 0.0
        
        # Get final deduplication stats
        final_dedup_stats = self.deduplication_manager.get_deduplication_stats() if self.deduplication_manager else {}
        results["final_deduplication_stats"] = final_dedup_stats.get("stats", {})
        
        logger.info(f"🎉 Smart download completed in {results['duration_seconds']:.1f} seconds")
        logger.info(f"📊 Downloaded: {results['files_downloaded']}/{total_files} files ({results['success_rate']*100:.1f}%)")
        logger.info(f"📊 Skipped (dedup): {results['files_skipped_dedup']} files")
        logger.info(f"📊 Total size: {results['total_size_mb']:.2f} MB")
        logger.info(f"📊 Coverage: {results['deduplication_stats'].get('coverage_percent', 0):.1f}%")
        
        return results

    @performance_tracked("unknown-service", "download_historical_data")
    async def download_historical_data(self, 
                                     pairs: Optional[List[str]] = None,
                                     start_year: int = 2019,
                                     end_year: int = 2024,
                                     focus_mode: str = "gold_eurusd_correlation") -> Dict[str, any]:
        """
        Download historical tick data for specified pairs and years
        
        Args:
            pairs: List of currency pairs (default: optimized pairs for Gold-EURUSD correlation)
            start_year: Starting year for download
            end_year: Ending year for download
            focus_mode: Download focus mode:
                - "gold_eurusd_correlation": Optimized pairs for Gold-EURUSD correlation analysis
                - "gold_only": Only Gold and Silver
                - "eurusd_only": Only EUR/USD and related pairs
                - "all_major": All major currency pairs
                - "custom": Use provided pairs list
            
        Returns:
            Dictionary with download results and statistics
        """
        # Determine which pairs to download based on focus mode
        if pairs is None:
            if focus_mode == "gold_eurusd_correlation":
                pairs = self.optimized_pairs.copy()
            elif focus_mode == "gold_only":
                pairs = ["XAUUSD", "XAGUSD", "USDCHF"]  # Gold, Silver, and safe haven
            elif focus_mode == "eurusd_only":
                pairs = ["EURUSD", "GBPUSD", "EURJPY", "EURGBP", "USDCHF"]
            elif focus_mode == "all_major":
                pairs = self.major_pairs.copy()
            else:
                pairs = self.optimized_pairs.copy()  # Default to optimized pairs
        
        logger.info(f"🚀 Starting historical data download for {len(pairs)} pairs ({start_year}-{end_year})")
        logger.info(f"📊 Pairs to download: {', '.join(pairs)}")
        
        start_time = time.time()
        results = {
            "pairs": pairs,
            "years": list(range(start_year, end_year + 1)),
            "dukascopy_results": {},
            "truefx_results": {},
            "processing_results": {},
            "summary": {},
            "data_quality": {}
        }
        
        # Download from each source
        for i, pair in enumerate(pairs):
            logger.info(f"📊 Processing pair {i+1}/{len(pairs)}: {pair}")
            
            # Download Dukascopy data (primary source - highest accuracy)
            try:
                dukascopy_result = await self._download_dukascopy_pair(pair, start_year, end_year)
                results["dukascopy_results"][pair] = dukascopy_result
                logger.info(f"✅ Dukascopy {pair}: {dukascopy_result.get('files_downloaded', 0)} files")
            except Exception as e:
                logger.error(f"❌ Dukascopy {pair} failed: {e}")
                results["dukascopy_results"][pair] = {"error": str(e)}
            
            # Download TrueFX data (validation source)
            try:
                truefx_result = await self._download_truefx_pair(pair, start_year, end_year)
                results["truefx_results"][pair] = truefx_result
                logger.info(f"✅ TrueFX {pair}: {truefx_result.get('files_downloaded', 0)} files")
            except Exception as e:
                logger.error(f"❌ TrueFX {pair} failed: {e}")
                results["truefx_results"][pair] = {"error": str(e)}
            
            # Process and validate data
            try:
                processing_result = await self._process_pair_data(pair, start_year, end_year)
                results["processing_results"][pair] = processing_result
                logger.info(f"✅ Processed {pair}: {processing_result.get('total_rows', 0)} rows")
            except Exception as e:
                logger.error(f"❌ Processing {pair} failed: {e}")
                results["processing_results"][pair] = {"error": str(e)}
            
            # Small delay between pairs
            await asyncio.sleep(1)
        
        # Generate comprehensive summary
        total_time = time.time() - start_time
        results["summary"] = await self._generate_summary_report(results, total_time)
        results["data_quality"] = await self._analyze_data_quality(pairs)
        
        logger.info(f"🎉 Historical data download completed in {total_time:.2f} seconds")
        logger.info(f"📊 Total files: {results['summary'].get('total_files', 0)}")
        logger.info(f"📊 Total size: {results['summary'].get('total_size_mb', 0):.2f} MB")
        
        return results
    
    async def _download_dukascopy_pair(self, pair: str, start_year: int, end_year: int) -> Dict[str, any]:
        """Download Dukascopy tick data for a specific pair"""
        logger.info(f"📥 Downloading Dukascopy data for {pair}")
        
        pair_dir = self.dukascopy_dir / pair
        pair_dir.mkdir(exist_ok=True)
        
        download_results = {
            "files_downloaded": 0, 
            "files_failed": 0, 
            "files_skipped": 0,
            "total_size_mb": 0,
            "years_completed": []
        }
        
        # Generate download tasks
        download_tasks = []
        
        for year in range(start_year, end_year + 1):
            year_tasks = []
            
            for month in range(1, 13):
                # Get days in month
                if month == 2:
                    days = 29 if year % 4 == 0 else 28
                elif month in [4, 6, 9, 11]:
                    days = 30
                else:
                    days = 31
                
                for day in range(1, days + 1):
                    for hour in range(24):
                        url = self._build_dukascopy_url(pair, year, month, day, hour)
                        filename = f"{pair}_{year}_{month:02d}_{day:02d}_{hour:02d}.bi5"
                        filepath = pair_dir / filename
                        
                        # Skip if file already exists and is not empty
                        if filepath.exists() and filepath.stat().st_size > 0:
                            download_results["files_skipped"] += 1
                            continue
                            
                        year_tasks.append((url, filepath))
            
            if year_tasks:
                download_tasks.extend(year_tasks)
        
        if not download_tasks:
            logger.info(f"ℹ️  All Dukascopy files for {pair} already exist")
            return download_results
        
        logger.info(f"📊 Dukascopy {pair}: {len(download_tasks)} files to download")
        
        # Download files in batches with WARP proxy support
        session = await self._create_http_session()
        try:
            for i in range(0, len(download_tasks), self.max_concurrent_downloads):
                batch = download_tasks[i:i + self.max_concurrent_downloads]
                
                batch_results = await asyncio.gather(*[
                    self._download_dukascopy_file(session, url, filepath)
                    for url, filepath in batch
                ], return_exceptions=True)
                
                # Process batch results
                for result in batch_results:
                    if isinstance(result, Exception):
                        download_results["files_failed"] += 1
                        logger.debug(f"Download failed: {result}")
                    elif result:
                        download_results["files_downloaded"] += 1
                        download_results["total_size_mb"] += result.get("size_mb", 0)
                
                # Progress update every 100 files
                if i % 100 == 0:
                    progress = (i + len(batch)) / len(download_tasks) * 100
                    logger.info(f"  📊 {pair} progress: {progress:.1f}% ({i + len(batch)}/{len(download_tasks)})")
                
                # Small delay between batches
                await asyncio.sleep(self.delay_between_requests)
        finally:
            await session.close()
        
        # Update statistics
        self.download_stats["dukascopy"]["files"] += download_results["files_downloaded"]
        self.download_stats["dukascopy"]["size_mb"] += download_results["total_size_mb"]
        self.download_stats["dukascopy"]["errors"] += download_results["files_failed"]
        self.download_stats["dukascopy"]["pairs"][pair] = download_results
        
        logger.info(f"✅ Dukascopy {pair}: {download_results['files_downloaded']} files, "
                   f"{download_results['total_size_mb']:.2f} MB")
        
        return download_results
    
    async def _download_truefx_pair(self, pair: str, start_year: int, end_year: int) -> Dict[str, any]:
        """Download TrueFX tick data for a specific pair"""
        logger.info(f"📥 Downloading TrueFX data for {pair}")
        
        pair_dir = self.truefx_dir / pair
        pair_dir.mkdir(exist_ok=True)
        
        download_results = {
            "files_downloaded": 0, 
            "files_failed": 0, 
            "files_skipped": 0,
            "total_size_mb": 0,
            "years_completed": []
        }
        
        # TrueFX provides monthly files
        download_tasks = []
        
        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                url = self._build_truefx_url(pair, year, month)
                filename = f"{pair}_{year}_{month:02d}.csv.zip"
                filepath = pair_dir / filename
                
                # Skip if file already exists and is not empty
                if filepath.exists() and filepath.stat().st_size > 0:
                    download_results["files_skipped"] += 1
                    continue
                    
                download_tasks.append((url, filepath))
        
        if not download_tasks:
            logger.info(f"ℹ️  All TrueFX files for {pair} already exist")
            return download_results
        
        logger.info(f"📊 TrueFX {pair}: {len(download_tasks)} files to download")
        
        # Download files sequentially (TrueFX is more sensitive to concurrent requests) with WARP proxy support
        session = await self._create_http_session()
        try:
            for i, (url, filepath) in enumerate(download_tasks):
                try:
                    result = await self._download_truefx_file(session, url, filepath)
                    if result:
                        download_results["files_downloaded"] += 1
                        download_results["total_size_mb"] += result.get("size_mb", 0)
                    else:
                        download_results["files_failed"] += 1
                        
                    # Progress update
                    if i % 5 == 0:
                        progress = (i + 1) / len(download_tasks) * 100
                        logger.info(f"  📊 {pair} progress: {progress:.1f}% ({i + 1}/{len(download_tasks)})")
                    
                    # Delay between downloads
                    await asyncio.sleep(self.delay_between_requests * 2)  # More delay for TrueFX
                    
                except Exception as e:
                    logger.warning(f"Failed to download {url}: {e}")
                    download_results["files_failed"] += 1
        finally:
            await session.close()
        
        # Update statistics
        self.download_stats["truefx"]["files"] += download_results["files_downloaded"]
        self.download_stats["truefx"]["size_mb"] += download_results["total_size_mb"]
        self.download_stats["truefx"]["errors"] += download_results["files_failed"]
        self.download_stats["truefx"]["pairs"][pair] = download_results
        
        logger.info(f"✅ TrueFX {pair}: {download_results['files_downloaded']} files, "
                   f"{download_results['total_size_mb']:.2f} MB")
        
        return download_results
    
    async def _download_dukascopy_file(self, session: aiohttp.ClientSession, 
                                     url: str, filepath: Path) -> Optional[Dict[str, any]]:
        """Download a single Dukascopy .bi5 file"""
        for attempt in range(self.retry_attempts):
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        # Check if content is meaningful
                        if len(content) < 10:
                            return None
                        
                        # Decompress if gzipped
                        if content.startswith(b'\x1f\x8b'):
                            try:
                                content = gzip.decompress(content)
                            except gzip.BadGzipFile:
                                logger.warning(f"Invalid gzip file: {url}")
                                return None
                        
                        # Save file
                        async with aiofiles.open(filepath, 'wb') as f:
                            await f.write(content)
                        
                        size_mb = len(content) / (1024 * 1024)
                        return {"size_mb": size_mb, "success": True}
                        
                    elif response.status == 404:
                        # File doesn't exist (weekend/holiday/no trading)
                        return None
                    else:
                        logger.debug(f"HTTP {response.status} for {url}")
                        
            except asyncio.TimeoutError:
                logger.debug(f"Timeout downloading {url}, attempt {attempt + 1}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(1)
            except Exception as e:
                logger.debug(f"Error downloading {url}: {e}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(1)
        
        return None
    
    async def _download_truefx_file(self, session: aiohttp.ClientSession, 
                                  url: str, filepath: Path) -> Optional[Dict[str, any]]:
        """Download a single TrueFX CSV file"""
        for attempt in range(self.retry_attempts):
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        # Check if content is meaningful
                        if len(content) < 10:
                            return None
                        
                        # Save file
                        async with aiofiles.open(filepath, 'wb') as f:
                            await f.write(content)
                        
                        size_mb = len(content) / (1024 * 1024)
                        return {"size_mb": size_mb, "success": True}
                        
                    elif response.status == 404:
                        # File doesn't exist
                        return None
                    else:
                        logger.debug(f"HTTP {response.status} for {url}")
                        
            except asyncio.TimeoutError:
                logger.debug(f"Timeout downloading {url}, attempt {attempt + 1}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(1)
            except Exception as e:
                logger.debug(f"Error downloading {url}: {e}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(1)
        
        return None
    
    def _build_dukascopy_url(self, pair: str, year: int, month: int, day: int, hour: int) -> str:
        """Build Dukascopy download URL"""
        # Dukascopy uses 0-based months
        return f"https://datafeed.dukascopy.com/datafeed/{pair}/{year}/{month-1:02d}/{day:02d}/{hour:02d}h_ticks.bi5"
    
    def _build_truefx_url(self, pair: str, year: int, month: int) -> str:
        """Build TrueFX download URL"""
        month_names = [
            "JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE",
            "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"
        ]
        
        # TrueFX only supports major pairs
        if pair not in ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD"]:
            return None
        
        month_name = month_names[month - 1]
        return f"https://truefx.com/dev/data/{year}/{month_name}-{year}/{pair}-{year}-{month:02d}.csv.zip"
    
    def _convert_dukascopy_bi5_to_csv(self, bi5_filepath) -> Optional[pd.DataFrame]:
        """Convert Dukascopy .bi5 binary file to CSV format"""
        try:
            with open(bi5_filepath, 'rb') as f:
                data = f.read()
            
            if len(data) < 20:
                return None
            
            # Decompress if needed - check for different compression formats
            if data.startswith(b'\x1f\x8b'):  # gzip
                try:
                    data = gzip.decompress(data)
                except gzip.BadGzipFile:
                    return None
            elif data.startswith(b'\xfd7zXZ') or data.startswith(b']\x00\x00'):  # LZMA
                try:
                    import lzma
                    data = lzma.decompress(data)
                except Exception:
                    return None
            
            # Parse binary data
            # Each tick is 20 bytes: time(4) + ask(4) + bid(4) + ask_volume(4) + bid_volume(4)
            tick_size = 20
            if len(data) % tick_size != 0:
                logger.warning(f"Invalid file size for {bi5_filepath}: {len(data)} bytes")
                return None
            
            num_ticks = len(data) // tick_size
            if num_ticks == 0:
                return None
            
            ticks = []
            
            # Extract hour from filename for timestamp calculation
            if isinstance(bi5_filepath, str):
                from pathlib import Path
                bi5_filepath = Path(bi5_filepath)
            filename_parts = bi5_filepath.stem.split('_')
            if len(filename_parts) >= 5:
                year = int(filename_parts[1])
                month = int(filename_parts[2])
                day = int(filename_parts[3])
                hour = int(filename_parts[4])
                
                # Base timestamp for the hour
                base_timestamp = datetime(year, month, day, hour)
                
                for i in range(num_ticks):
                    try:
                        offset = i * tick_size
                        tick_data = struct.unpack('>IIIII', data[offset:offset + tick_size])
                        
                        # Convert to readable format
                        timestamp_ms = tick_data[0]
                        ask = tick_data[1] / 100000.0  # Convert to price
                        bid = tick_data[2] / 100000.0  # Convert to price
                        ask_volume = tick_data[3] / 1000000.0  # Convert to volume
                        bid_volume = tick_data[4] / 1000000.0  # Convert to volume
                        
                        # Calculate actual timestamp
                        actual_timestamp = base_timestamp + timedelta(milliseconds=timestamp_ms)
                        
                        ticks.append({
                            'timestamp': actual_timestamp,
                            'bid': bid,
                            'ask': ask,
                            'bid_volume': bid_volume,
                            'ask_volume': ask_volume,
                            'volume': (bid_volume + ask_volume) / 2,
                            'spread': ask - bid,
                            'mid_price': (bid + ask) / 2
                        })
                        
                    except struct.error:
                        continue
            
            if ticks:
                return pd.DataFrame(ticks)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to convert {bi5_filepath}: {e}")
            return None
    
    def _process_truefx_csv(self, csv_filepath: Path) -> Optional[pd.DataFrame]:
        """Process TrueFX CSV file"""
        try:
            # Extract if zipped
            if csv_filepath.suffix == '.zip':
                with zipfile.ZipFile(csv_filepath, 'r') as zip_ref:
                    # Find CSV file in zip
                    csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
                    if not csv_files:
                        return None
                    
                    # Read CSV from zip
                    with zip_ref.open(csv_files[0]) as csv_file:
                        df = pd.read_csv(csv_file, header=None)
            else:
                df = pd.read_csv(csv_filepath, header=None)
            
            if df.empty:
                return None
            
            # TrueFX format: Symbol,Date,Bid,Ask
            df.columns = ['symbol', 'timestamp', 'bid', 'ask']
            
            # Convert timestamp
            df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y%m%d %H:%M:%S.%f')
            
            # Calculate additional fields
            df['spread'] = df['ask'] - df['bid']
            df['mid_price'] = (df['bid'] + df['ask']) / 2
            df['volume'] = 1.0  # TrueFX doesn't provide volume
            df['bid_volume'] = 0.5
            df['ask_volume'] = 0.5
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to process {csv_filepath}: {e}")
            return None
    
    async def _process_pair_data(self, pair: str, start_year: int, end_year: int) -> Dict[str, any]:
        """Process and convert raw data files to unified CSV format"""
        logger.info(f"🔄 Processing data for {pair}")
        
        processed_pair_dir = self.processed_dir / pair
        processed_pair_dir.mkdir(exist_ok=True)
        
        results = {
            "dukascopy_processed": 0, 
            "truefx_processed": 0, 
            "total_rows": 0,
            "years_processed": []
        }
        
        # Process Dukascopy files
        dukascopy_pair_dir = self.dukascopy_dir / pair
        if dukascopy_pair_dir.exists():
            bi5_files = list(dukascopy_pair_dir.glob("*.bi5"))
            logger.info(f"🔄 Processing {len(bi5_files)} Dukascopy files for {pair}")
            
            # Process files in parallel
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = []
                
                for bi5_file in bi5_files:
                    if bi5_file.stat().st_size > 0:  # Only process non-empty files
                        future = executor.submit(self._convert_dukascopy_bi5_to_csv, bi5_file)
                        futures.append((bi5_file, future))
                
                # Collect results
                for bi5_file, future in futures:
                    try:
                        df = future.result(timeout=30)
                        if df is not None and len(df) > 0:
                            # Save processed CSV
                            csv_filename = bi5_file.stem + ".csv"
                            csv_filepath = processed_pair_dir / f"dukascopy_{csv_filename}"
                            
                            # Add metadata
                            df['source'] = 'dukascopy'
                            df['pair'] = pair
                            df['broker'] = 'dukascopy'
                            df['account_type'] = 'interbank'
                            
                            df.to_csv(csv_filepath, index=False)
                            
                            results["dukascopy_processed"] += 1
                            results["total_rows"] += len(df)
                            
                    except Exception as e:
                        logger.warning(f"Failed to process {bi5_file}: {e}")
        
        # Process TrueFX files
        truefx_pair_dir = self.truefx_dir / pair
        if truefx_pair_dir.exists():
            truefx_files = list(truefx_pair_dir.glob("*.csv*"))
            logger.info(f"🔄 Processing {len(truefx_files)} TrueFX files for {pair}")
            
            for truefx_file in truefx_files:
                if truefx_file.stat().st_size > 0:  # Only process non-empty files
                    try:
                        df = self._process_truefx_csv(truefx_file)
                        if df is not None and len(df) > 0:
                            # Save processed CSV
                            csv_filename = truefx_file.stem.replace('.csv', '') + ".csv"
                            csv_filepath = processed_pair_dir / f"truefx_{csv_filename}"
                            
                            # Add metadata
                            df['source'] = 'truefx'
                            df['pair'] = pair
                            df['broker'] = 'truefx'
                            df['account_type'] = 'institutional'
                            
                            df.to_csv(csv_filepath, index=False)
                            
                            results["truefx_processed"] += 1
                            results["total_rows"] += len(df)
                            
                    except Exception as e:
                        logger.warning(f"Failed to process {truefx_file}: {e}")
        
        logger.info(f"✅ Processed {pair}: {results['dukascopy_processed']} Dukascopy, "
                   f"{results['truefx_processed']} TrueFX, {results['total_rows']} total rows")
        
        return results
    
    async def _generate_summary_report(self, results: Dict, total_time: float) -> Dict[str, any]:
        """Generate comprehensive summary report"""
        summary = {
            "download_time_seconds": total_time,
            "download_time_formatted": f"{total_time/3600:.1f} hours" if total_time > 3600 else f"{total_time/60:.1f} minutes",
            "total_files": self.download_stats["dukascopy"]["files"] + self.download_stats["truefx"]["files"],
            "total_size_mb": self.download_stats["dukascopy"]["size_mb"] + self.download_stats["truefx"]["size_mb"],
            "total_errors": self.download_stats["dukascopy"]["errors"] + self.download_stats["truefx"]["errors"],
            "total_rows": self.download_stats["processed"]["total_rows"],
            "sources": {
                "dukascopy": {
                    "files": self.download_stats["dukascopy"]["files"],
                    "size_mb": self.download_stats["dukascopy"]["size_mb"],
                    "errors": self.download_stats["dukascopy"]["errors"]
                },
                "truefx": {
                    "files": self.download_stats["truefx"]["files"],
                    "size_mb": self.download_stats["truefx"]["size_mb"],
                    "errors": self.download_stats["truefx"]["errors"]
                }
            },
            "pairs_completed": len(results["pairs"]),
            "estimated_storage_compressed": f"{(self.download_stats['dukascopy']['size_mb'] + self.download_stats['truefx']['size_mb']) * 0.2:.1f} MB"
        }
        
        # Save detailed report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filepath = self.reports_dir / f"download_summary_{timestamp}.json"
        
        detailed_report = {
            "summary": summary,
            "detailed_results": results,
            "download_statistics": self.download_stats,
            "timestamp": datetime.now().isoformat(),
            "configuration": {
                "max_concurrent_downloads": self.max_concurrent_downloads,
                "retry_attempts": self.retry_attempts,
                "delay_between_requests": self.delay_between_requests
            }
        }
        
        async with aiofiles.open(report_filepath, 'w') as f:
            await f.write(json.dumps(detailed_report, indent=2, default=str))
        
        logger.info(f"📊 Detailed report saved: {report_filepath}")
        
        return summary
    
    async def _analyze_data_quality(self, pairs: List[str]) -> Dict[str, any]:
        """Analyze data quality and provide recommendations"""
        quality_report = {
            "overall_quality": "good",
            "recommendations": [],
            "pair_analysis": {}
        }
        
        for pair in pairs:
            dukascopy_files = len(list((self.dukascopy_dir / pair).glob("*.bi5"))) if (self.dukascopy_dir / pair).exists() else 0
            truefx_files = len(list((self.truefx_dir / pair).glob("*.csv*"))) if (self.truefx_dir / pair).exists() else 0
            processed_files = len(list((self.processed_dir / pair).glob("*.csv"))) if (self.processed_dir / pair).exists() else 0
            
            quality_report["pair_analysis"][pair] = {
                "dukascopy_files": dukascopy_files,
                "truefx_files": truefx_files,
                "processed_files": processed_files,
                "data_sources": 2 if dukascopy_files > 0 and truefx_files > 0 else 1,
                "quality_rating": "excellent" if dukascopy_files > 1000 else "good" if dukascopy_files > 100 else "limited"
            }
        
        return quality_report
    
    def get_download_progress(self) -> Dict[str, any]:
        """Get current download progress"""
        return {
            "statistics": self.download_stats,
            "data_directories": {
                "dukascopy": str(self.dukascopy_dir),
                "truefx": str(self.truefx_dir),
                "processed": str(self.processed_dir),
                "reports": str(self.reports_dir)
            },
            "available_pairs": {
                "major": self.major_pairs,
                "metals": self.metal_pairs,
                "optimized": self.optimized_pairs
            }
        }


# Example usage
async def main():
    """Example usage of the Dukascopy/TrueFX downloader for Gold-EURUSD correlation analysis"""
    downloader = DataBridgeDukascopyDownloader()
    
    # Download optimized pairs for Gold-EURUSD correlation analysis
    results = await downloader.download_historical_data(
        pairs=None,  # Use optimized pairs for Gold-EURUSD correlation
        start_year=2022,
        end_year=2024,
        focus_mode="gold_eurusd_correlation"
    )
    
    print("🎉 Gold-EURUSD correlation data download completed!")
    print(f"📊 Pairs downloaded: {', '.join(results['pairs'])}")
    print(f"📊 Summary: {results['summary']}")
    print(f"📊 Data quality: {results['data_quality']}")
    
    # Print optimized pairs info
    print("\n🔍 Optimized pairs for analysis:")
    print(f"  Core pairs: {downloader.core_pairs}")
    print(f"  Gold correlation: {downloader.gold_correlation_pairs}")
    print(f"  EURUSD correlation: {downloader.eurusd_correlation_pairs}")
    print(f"  USD strength: {downloader.usd_strength_pairs}")

if __name__ == "__main__":
    asyncio.run(main())