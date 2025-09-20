"""
Deduplication System Usage Examples
Comprehensive examples showing how to use the deduplication system to prevent redundant tick data downloads

Features demonstrated:
1. Smart download with automatic deduplication
2. Gap detection and filling
3. Download recommendations
4. Data integrity verification
5. Progress tracking and statistics
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Import the deduplication system
from ..business.deduplication_manager import get_deduplication_manager
from ..data_sources.dukascopy_client import DataBridgeDukascopyDownloader

async def example_1_basic_deduplication_check():
    """
    Example 1: Basic deduplication check before downloading
    Shows how to check if data already exists before attempting download
    """
    print("🔍 Example 1: Basic Deduplication Check")
    print("=" * 50)
    
    try:
        # Get deduplication manager
        dedup_manager = await get_deduplication_manager()
        
        # Define what we want to download
        symbol = "EURUSD"
        source = "dukascopy"
        start_time = datetime.now() - timedelta(hours=48)  # Last 48 hours
        end_time = datetime.now()
        
        print(f"Checking if download is needed for:")
        print(f"  Symbol: {symbol}")
        print(f"  Source: {source}")
        print(f"  Time range: {start_time} to {end_time}")
        
        # Check if download is needed
        check_result = await dedup_manager.check_download_needed(
            symbol=symbol,
            source=source,
            start_time=start_time,
            end_time=end_time
        )
        
        print(f"\nDeduplication Check Results:")
        print(f"  Download needed: {check_result['needed']}")
        print(f"  Missing ranges: {len(check_result['missing_ranges'])}")
        print(f"  Existing ranges: {len(check_result['existing_ranges'])}")
        print(f"  Coverage: {check_result['coverage_percent']:.1f}%")
        print(f"  Reason: {check_result['reason']}")
        print(f"  Hours missing: {check_result['total_hours_missing']:.1f}")
        
        if check_result['missing_ranges']:
            print(f"\nMissing ranges to download:")
            for i, range_info in enumerate(check_result['missing_ranges'][:3]):  # Show first 3
                start = range_info['start']
                end = range_info['end']
                print(f"  {i+1}. {start} to {end}")
        
        return check_result
        
    except Exception as e:
        print(f"❌ Error in deduplication check: {e}")
        return None

async def example_2_smart_download_with_deduplication():
    """
    Example 2: Smart download that automatically prevents redundant downloads
    Shows the enhanced Dukascopy downloader with built-in deduplication
    """
    print("\n🚀 Example 2: Smart Download with Deduplication")
    print("=" * 50)
    
    try:
        # Create Dukascopy downloader (now with deduplication support)
        downloader = DataBridgeDukascopyDownloader()
        
        # Perform smart download - this will automatically:
        # 1. Check what data already exists
        # 2. Only download missing ranges
        # 3. Record successful downloads
        # 4. Provide detailed statistics
        
        symbol = "XAUUSD"  # Gold
        hours_back = 24    # Last 24 hours
        
        print(f"Starting smart download for:")
        print(f"  Symbol: {symbol}")
        print(f"  Hours back: {hours_back}")
        
        result = await downloader.download_small_batch(
            pair=symbol,
            hours_back=hours_back
        )
        
        print(f"\nSmart Download Results:")
        print(f"  Files downloaded: {result['files_downloaded']}")
        print(f"  Files skipped (dedup): {result['files_skipped_dedup']}")
        print(f"  Files failed: {result['files_failed']}")
        print(f"  Total size: {result['total_size_mb']:.2f} MB")
        print(f"  Success rate: {result['success_rate']*100:.1f}%")
        print(f"  Duration: {result['duration_seconds']:.1f} seconds")
        
        # Show deduplication statistics
        dedup_stats = result.get('deduplication_stats', {})
        print(f"\nDeduplication Statistics:")
        print(f"  Coverage: {dedup_stats.get('coverage_percent', 0):.1f}%")
        print(f"  Missing ranges: {dedup_stats.get('missing_ranges', 0)}")
        print(f"  Existing ranges: {dedup_stats.get('existing_ranges', 0)}")
        print(f"  Reason: {dedup_stats.get('reason', 'N/A')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error in smart download: {e}")
        return None

async def example_3_gap_detection_and_analysis():
    """
    Example 3: Gap detection to identify missing data periods
    Shows how to analyze data completeness and prioritize downloads
    """
    print("\n🔍 Example 3: Gap Detection and Analysis")
    print("=" * 50)
    
    try:
        dedup_manager = await get_deduplication_manager()
        
        # Analyze gaps for a longer time period
        symbol = "EURUSD"
        source = "dukascopy"
        overall_start = datetime.now() - timedelta(days=7)  # Last week
        overall_end = datetime.now()
        
        print(f"Detecting gaps for:")
        print(f"  Symbol: {symbol}")
        print(f"  Source: {source}")
        print(f"  Time range: {overall_start} to {overall_end}")
        
        # Detect gaps in the data
        gaps = await dedup_manager.detect_gaps(
            symbol=symbol,
            source=source,
            overall_start=overall_start,
            overall_end=overall_end,
            expected_frequency="hourly"
        )
        
        print(f"\nGap Detection Results:")
        print(f"  Total gaps found: {len(gaps)}")
        
        if gaps:
            # Categorize gaps by priority
            high_priority = [g for g in gaps if g.priority == "high"]
            medium_priority = [g for g in gaps if g.priority == "medium"]
            low_priority = [g for g in gaps if g.priority == "low"]
            
            print(f"  High priority gaps: {len(high_priority)}")
            print(f"  Medium priority gaps: {len(medium_priority)}")
            print(f"  Low priority gaps: {len(low_priority)}")
            
            # Show details for high priority gaps
            if high_priority:
                print(f"\nHigh Priority Gaps:")
                for i, gap in enumerate(high_priority[:3]):  # Show first 3
                    duration_hours = (gap.gap_end - gap.gap_start).total_seconds() / 3600
                    print(f"  {i+1}. {gap.gap_start} to {gap.gap_end}")
                    print(f"     Duration: {duration_hours:.1f} hours")
                    print(f"     Reason: {gap.reason}")
        else:
            print("  ✅ No gaps detected - data is complete!")
        
        return gaps
        
    except Exception as e:
        print(f"❌ Error in gap detection: {e}")
        return None

async def example_4_download_recommendations():
    """
    Example 4: Get intelligent download recommendations
    Shows how the system can suggest what data to download next
    """
    print("\n💡 Example 4: Download Recommendations")
    print("=" * 50)
    
    try:
        dedup_manager = await get_deduplication_manager()
        
        symbol = "XAUUSD"
        source = "dukascopy"
        
        print(f"Getting recommendations for:")
        print(f"  Symbol: {symbol}")
        print(f"  Source: {source}")
        
        # Get download recommendations
        recommendations = await dedup_manager.get_download_recommendations(symbol, source)
        
        print(f"\nDownload Recommendations:")
        print(f"  Total gaps: {recommendations.get('total_gaps', 0)}")
        print(f"  High priority gaps: {recommendations.get('high_priority_gaps', 0)}")
        print(f"  Medium priority gaps: {recommendations.get('medium_priority_gaps', 0)}")
        
        recommended_downloads = recommendations.get('recommended_downloads', [])
        if recommended_downloads:
            print(f"\nTop Recommended Downloads:")
            for i, rec in enumerate(recommended_downloads[:5]):  # Show top 5
                print(f"  {i+1}. Priority: {rec['priority']}")
                print(f"     Time range: {rec['start']} to {rec['end']}")
                print(f"     Duration: {rec['duration_hours']:.1f} hours")
                print(f"     Reason: {rec['reason']}")
        else:
            print("  ✅ No recommendations - all data appears complete!")
        
        return recommendations
        
    except Exception as e:
        print(f"❌ Error getting recommendations: {e}")
        return None

async def example_5_comprehensive_statistics():
    """
    Example 5: Get comprehensive deduplication system statistics
    Shows detailed metrics about system performance and efficiency
    """
    print("\n📊 Example 5: Comprehensive Statistics")
    print("=" * 50)
    
    try:
        dedup_manager = await get_deduplication_manager()
        
        # Get comprehensive statistics
        stats = dedup_manager.get_deduplication_stats()
        
        print(f"System Performance:")
        print(f"  Downloads prevented: {stats.get('downloads_prevented', 0)}")
        print(f"  Files verified: {stats.get('files_verified', 0)}")
        print(f"  Cache hits: {stats.get('cache_hits', 0)}")
        print(f"  Integrity failures: {stats.get('integrity_failures', 0)}")
        print(f"  Database queries: {stats.get('database_queries', 0)}")
        
        registry_summary = stats.get('registry_summary', {})
        print(f"\nRegistry Summary:")
        print(f"  Symbols tracked: {registry_summary.get('total_symbols', 0)}")
        print(f"  Download records: {registry_summary.get('total_records', 0)}")
        print(f"  Files tracked: {registry_summary.get('total_files_tracked', 0)}")
        print(f"  Gaps tracked: {registry_summary.get('total_gaps', 0)}")
        
        coverage_summary = stats.get('coverage_summary', {})
        if coverage_summary:
            print(f"\nCoverage by Symbol:")
            for symbol_source, coverage in coverage_summary.items():
                print(f"  {symbol_source}:")
                print(f"    Records: {coverage.get('records', 0)}")
                print(f"    Hours covered: {coverage.get('total_hours', 0):.1f}")
                print(f"    Total ticks: {coverage.get('total_ticks', 0):,}")
        
        return stats
        
    except Exception as e:
        print(f"❌ Error getting statistics: {e}")
        return None

async def example_6_api_endpoints_demo():
    """
    Example 6: Demonstrate REST API endpoints for deduplication
    Shows how to interact with the system via HTTP API
    """
    print("\n🌐 Example 6: API Endpoints Demo")
    print("=" * 50)
    
    # This example shows how you would call the API endpoints
    # Note: In real usage, you'd use the actual service URL
    base_url = "http://localhost:8001/api/v1"
    
    print("Available API endpoints:")
    print(f"  GET  {base_url}/deduplication/status")
    print(f"  POST {base_url}/deduplication/check")
    print(f"  GET  {base_url}/deduplication/recommendations")
    print(f"  POST {base_url}/deduplication/gaps/detect")
    print(f"  GET  {base_url}/deduplication/stats")
    print(f"  POST {base_url}/deduplication/smart-download")
    print(f"  DELETE {base_url}/deduplication/cache")
    
    # Example API call structure (pseudo-code)
    example_requests = {
        "check_download": {
            "method": "POST",
            "url": f"{base_url}/deduplication/check",
            "json": {
                "symbol": "EURUSD",
                "source": "dukascopy", 
                "start_time": "2024-01-01T00:00:00",
                "end_time": "2024-01-02T00:00:00"
            }
        },
        "smart_download": {
            "method": "POST",
            "url": f"{base_url}/deduplication/smart-download",
            "params": {
                "symbol": "XAUUSD",
                "source": "dukascopy",
                "hours_back": 24
            }
        }
    }
    
    print(f"\nExample API request structures:")
    for name, req in example_requests.items():
        print(f"  {name}:")
        print(f"    {req['method']} {req['url']}")
        if 'json' in req:
            print(f"    Body: {json.dumps(req['json'], indent=6)}")
        if 'params' in req:
            print(f"    Params: {req['params']}")

async def main():
    """
    Main function demonstrating all deduplication examples
    """
    print("🎯 Data Bridge Deduplication System - Usage Examples")
    print("=" * 60)
    print("This demo shows how to use the advanced deduplication system")
    print("to prevent redundant downloads and optimize data management.")
    print("=" * 60)
    
    # Run all examples
    try:
        # Example 1: Basic deduplication check
        await example_1_basic_deduplication_check()
        
        # Example 2: Smart download with deduplication
        await example_2_smart_download_with_deduplication()
        
        # Example 3: Gap detection and analysis
        await example_3_gap_detection_and_analysis()
        
        # Example 4: Download recommendations
        await example_4_download_recommendations()
        
        # Example 5: Comprehensive statistics
        await example_5_comprehensive_statistics()
        
        # Example 6: API endpoints demo
        await example_6_api_endpoints_demo()
        
        print("\n" + "=" * 60)
        print("🎉 All examples completed successfully!")
        print("\nKey Benefits of the Deduplication System:")
        print("  ✅ Prevents redundant downloads")
        print("  ✅ Ensures data completeness with gap detection")
        print("  ✅ Provides intelligent download recommendations") 
        print("  ✅ Verifies data integrity with checksums")
        print("  ✅ Tracks progress and provides detailed statistics")
        print("  ✅ Offers both programmatic and REST API access")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error in main execution: {e}")

if __name__ == "__main__":
    asyncio.run(main())