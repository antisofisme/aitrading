#!/usr/bin/env python3
"""
Polygon.io Historical Downloader
Downloads historical forex data and publishes to NATS/Kafka
Refactored to use environment variables (Central Hub v2.0 pattern)
"""
import asyncio
import logging
import sys
import os
from pathlib import Path
from datetime import datetime, date, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from downloader import PolygonHistoricalDownloader
from publisher import MessagePublisher
from period_tracker import PeriodTracker

# Add shared components to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from shared.components.utils.gap_fill_verifier import GapFillVerifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class PolygonHistoricalService:
    def __init__(self):
        self.config = Config()
        self.downloader = PolygonHistoricalDownloader(
            api_key=self.config.polygon_api_key,
            config=self.config.download_config
        )

        # Publisher will be initialized from environment variables
        self.publisher = None

        # Gap fill verifier will be initialized from environment variables
        self.verifier = None

        # Period tracker to prevent duplicate downloads
        self.period_tracker = PeriodTracker(
            tracker_file="/data/downloaded_periods.json"
        )

        # Statistics
        self.stats = {
            "total_downloaded": 0,
            "total_published": 0,
            "gaps_filled": 0,
            "errors": 0
        }

        logger.info("=" * 80)
        logger.info("POLYGON.IO HISTORICAL DOWNLOADER + GAP VERIFICATION")
        logger.info("=" * 80)
        logger.info(f"Instance ID: {self.config.instance_id}")
        logger.info(f"Log Level: {self.config.log_level}")

    async def run_initial_download(self):
        """Download historical data for all pairs and publish to NATS/Kafka"""
        logger.info("📥 Starting initial historical download...")

        # Get messaging configs from environment variables
        nats_config = self.config.nats_config
        kafka_config = self.config.kafka_config

        nats_url = nats_config['url']
        kafka_brokers = ','.join(kafka_config['brokers'])

        logger.info(f"✅ Configuration loaded from environment variables")
        logger.info(f"✅ NATS: {nats_url}")
        logger.info(f"✅ Kafka: {kafka_brokers}")

        # Initialize publisher with config
        self.publisher = MessagePublisher(
            nats_url=nats_url,
            kafka_brokers=kafka_brokers
        )

        download_cfg = self.config.download_config
        pairs = self.config.pairs

        # Connect publisher ONCE at start
        await self.publisher.connect()

        try:
            # Download and publish EACH PAIR immediately (don't wait for all!)
            total_published = 0

            for pair in pairs:
                try:
                    # Determine timeframe from config
                    timeframe, multiplier = self.config.get_timeframe_for_pair(pair)
                    timeframe_str = f"{multiplier}{timeframe[0]}"  # "1m", "5m", etc

                    # ✅ LAYER 1: CHECK PERIOD TRACKER (Primary defense against re-downloads)
                    is_downloaded, tracker_reason = self.period_tracker.is_period_downloaded(
                        symbol=pair.symbol,
                        timeframe=timeframe_str,
                        start_date=download_cfg['start_date'],
                        end_date=download_cfg['end_date']
                    )

                    if is_downloaded:
                        logger.info(f"⏭️  {pair.symbol} already downloaded - SKIPPING (Reason: {tracker_reason})")
                        continue

                    # ✅ LAYER 2: CHECK IF DATA ALREADY EXISTS IN CLICKHOUSE (Backup check)
                    should_download = True
                    try:
                        ch_config = self.config.clickhouse_config

                        from clickhouse_driver import Client
                        ch_client = Client(
                            host=ch_config['host'],
                            port=ch_config['port'],
                            user=ch_config['user'],
                            password=ch_config['password'],
                            database=ch_config['database']
                        )

                        # Check existing data range for this pair
                        query = f"""
                            SELECT
                                COUNT(*) as count,
                                MIN(time) as min_date,
                                MAX(time) as max_date
                            FROM {ch_config['table']}
                            WHERE symbol = %(symbol)s
                              AND timeframe = %(timeframe)s
                        """
                        result = ch_client.execute(query, {
                            'symbol': pair.symbol,
                            'timeframe': timeframe_str
                        })

                        if result and result[0][0] > 0:
                            existing_count = result[0][0]
                            existing_min = result[0][1]
                            existing_max = result[0][2]

                            # Parse requested date range and ensure timezone consistency
                            from datetime import datetime, timezone, timedelta
                            requested_start = datetime.strptime(download_cfg['start_date'], '%Y-%m-%d').replace(tzinfo=timezone.utc)
                            requested_end = datetime.strptime(download_cfg['end_date'], '%Y-%m-%d').replace(tzinfo=timezone.utc) if download_cfg['end_date'] not in ['now', 'today'] else datetime.now(timezone.utc)

                            # Ensure existing timestamps are timezone-aware
                            if existing_min.tzinfo is None:
                                existing_min = existing_min.replace(tzinfo=timezone.utc)
                            if existing_max.tzinfo is None:
                                existing_max = existing_max.replace(tzinfo=timezone.utc)

                            # Check if existing data covers requested range
                            covers_start = existing_min <= requested_start
                            covers_end = existing_max >= requested_end

                            # CRITICAL: Even if START/END covered, check for MIDDLE gaps!
                            # Use get_date_range_gaps() to detect ALL missing dates
                            logger.info(f"🔍 {pair.symbol}: Checking for gaps (including middle gaps)...")

                            from gap_detector import GapDetector
                            gap_detector = GapDetector(ch_config)

                            # Get ALL missing dates in full requested range
                            missing_dates = gap_detector.get_date_range_gaps(
                                symbol=pair.symbol,
                                start_date=download_cfg['start_date'],
                                end_date=download_cfg['end_date'] if download_cfg['end_date'] not in ['now', 'today'] else datetime.now().strftime('%Y-%m-%d'),
                                timeframe=timeframe_str
                            )

                            if not missing_dates:
                                # NO GAPS - data complete!
                                logger.info(f"✅ {pair.symbol} has {existing_count:,} bars with NO GAPS - SKIPPING")
                                should_download = False
                            else:
                                # GAPS DETECTED (Start/Middle/End) - Download ONLY missing dates
                                logger.warning(f"⚠️  {pair.symbol} has {existing_count:,} bars BUT {len(missing_dates)} dates MISSING!")
                                logger.warning(f"   Existing range: {existing_min} to {existing_max}")
                                logger.warning(f"   Missing dates: {len(missing_dates)} total")

                                # Group consecutive missing dates into gap ranges
                                gap_ranges = []
                                if missing_dates:
                                    # Convert string dates to datetime
                                    missing_datetime = [datetime.strptime(d, '%Y-%m-%d').replace(tzinfo=timezone.utc) for d in missing_dates]
                                    missing_datetime.sort()

                                    # Group consecutive dates
                                    current_start = missing_datetime[0]
                                    current_end = missing_datetime[0]

                                    for i in range(1, len(missing_datetime)):
                                        # Check if this date is consecutive (within 4 days to account for weekends)
                                        if (missing_datetime[i] - current_end).days <= 4:
                                            current_end = missing_datetime[i]
                                        else:
                                            # Gap ended, save range
                                            gap_type = "MIDDLE"
                                            if current_start <= requested_start + timedelta(days=7):
                                                gap_type = "START"
                                            elif current_end >= requested_end - timedelta(days=7):
                                                gap_type = "END"

                                            gap_ranges.append((current_start, current_end, gap_type))
                                            logger.warning(f"   📥 {gap_type} Gap: {current_start.date()} to {current_end.date()}")

                                            # Start new range
                                            current_start = missing_datetime[i]
                                            current_end = missing_datetime[i]

                                    # Don't forget last range
                                    gap_type = "MIDDLE"
                                    if current_start <= requested_start + timedelta(days=7):
                                        gap_type = "START"
                                    elif current_end >= requested_end - timedelta(days=7):
                                        gap_type = "END"
                                    gap_ranges.append((current_start, current_end, gap_type))
                                    logger.warning(f"   📥 {gap_type} Gap: {current_start.date()} to {current_end.date()}")

                                # Store gap ranges for chunked download
                                pair.gap_ranges = gap_ranges
                                should_download = True
                        else:
                            logger.info(f"📥 {pair.symbol} is EMPTY - starting download (Priority {pair.priority})")
                            should_download = True

                    except Exception as check_error:
                        logger.warning(f"⚠️  Could not check existing data for {pair.symbol}: {check_error}")
                        logger.warning(f"⚠️  SKIPPING {pair.symbol} - will retry on next gap check cycle")
                        logger.warning(f"⚠️  This prevents accidental re-download of ALL historical data")
                        should_download = False

                    # Skip download if data already covers requested range
                    if not should_download:
                        continue

                    # Check if this is gap filling or fresh download
                    if hasattr(pair, 'gap_ranges') and pair.gap_ranges:
                        # GAP FILLING MODE: Download ONLY missing ranges in chunks
                        logger.info(f"📥 GAP FILLING: {len(pair.gap_ranges)} gaps detected for {pair.symbol}")

                        # Calculate total chunks for progress tracking
                        def calculate_total_chunks(gap_ranges, chunk_months=3):
                            total = 0
                            for gap_start, gap_end, _ in gap_ranges:
                                current = gap_start
                                while current < gap_end:
                                    total += 1
                                    # Move 3 months forward
                                    new_month = current.month + chunk_months
                                    new_year = current.year + (new_month - 1) // 12
                                    new_month = ((new_month - 1) % 12) + 1
                                    try:
                                        current = current.replace(year=new_year, month=new_month)
                                    except ValueError:
                                        current = current.replace(year=new_year, month=new_month, day=1)
                                    if current >= gap_end:
                                        break
                            return total

                        total_chunks = calculate_total_chunks(pair.gap_ranges)

                        logger.info(f"📥 Downloading {pair.symbol} gaps: {total_chunks} chunks")

                        all_bars = []
                        chunk_idx = 0

                        for gap_start, gap_end, gap_type in pair.gap_ranges:
                            # Split gap into 3-month chunks to prevent OOM
                            chunk_months = 3
                            current = gap_start

                            while current < gap_end:
                                chunk_idx += 1

                                # Calculate chunk end (3 months or gap_end, whichever is earlier)
                                new_month = current.month + chunk_months
                                new_year = current.year + (new_month - 1) // 12
                                new_month = ((new_month - 1) % 12) + 1

                                try:
                                    chunk_end_date = current.replace(year=new_year, month=new_month)
                                except ValueError:
                                    # Handle day overflow (e.g., Jan 31 + 3 months = Apr 31 invalid)
                                    chunk_end_date = current.replace(year=new_year, month=new_month, day=1)

                                chunk_end = min(chunk_end_date, gap_end)

                                # Download this chunk
                                chunk_results = await self.downloader.download_all_pairs(
                                    pairs=[pair],
                                    start_date=current.strftime('%Y-%m-%d'),
                                    end_date=chunk_end.strftime('%Y-%m-%d'),
                                    get_timeframe_func=self.config.get_timeframe_for_pair
                                )

                                chunk_bars = chunk_results.get(pair.symbol, [])
                                all_bars.extend(chunk_bars)

                                # Log progress
                                progress_pct = (chunk_idx / total_chunks) * 100 if total_chunks > 0 else 0
                                if chunk_idx % 5 == 0 or chunk_idx == total_chunks:
                                    logger.info(
                                        f"📊 {pair.symbol} gap fill progress: {chunk_idx}/{total_chunks} chunks "
                                        f"({progress_pct:.1f}%) - {len(all_bars):,} bars - {gap_type} gap"
                                    )

                                # Move to next chunk
                                current = chunk_end + timedelta(days=1)

                        bars = all_bars
                        logger.info(f"✅ Completed {pair.symbol} gap fill: {len(bars):,} bars, {len(pair.gap_ranges)} gaps")

                        # ✅ MARK EACH GAP RANGE AS DOWNLOADED
                        for gap_start, gap_end, gap_type in pair.gap_ranges:
                            self.period_tracker.mark_downloaded(
                                symbol=pair.symbol,
                                timeframe=timeframe_str,
                                start_date=gap_start.strftime('%Y-%m-%d'),
                                end_date=gap_end.strftime('%Y-%m-%d'),
                                bars_count=len(bars) // len(pair.gap_ranges),  # Approximate bars per gap
                                source='polygon_gap_fill',
                                verified=False  # Will be verified later
                            )

                    else:
                        # FRESH DOWNLOAD MODE: Download full range in chunks (ONLY for EMPTY database)
                        logger.info(f"📥 Fresh download: {download_cfg['start_date']} to {download_cfg['end_date']}")

                        # Split into 3-month chunks
                        from datetime import datetime, timedelta
                        start = datetime.strptime(download_cfg['start_date'], '%Y-%m-%d')
                        end = datetime.strptime(download_cfg['end_date'], '%Y-%m-%d')

                        # Calculate total chunks for progress tracking
                        def calculate_fresh_chunks(start, end, chunk_months=3):
                            total = 0
                            current = start
                            while current < end:
                                total += 1
                                new_month = current.month + chunk_months
                                new_year = current.year + (new_month - 1) // 12
                                new_month = ((new_month - 1) % 12) + 1
                                try:
                                    current = current.replace(year=new_year, month=new_month)
                                except ValueError:
                                    current = current.replace(year=new_year, month=new_month, day=1)
                                if current >= end:
                                    break
                            return total

                        total_chunks = calculate_fresh_chunks(start, end)

                        logger.info(f"📥 Initial download {pair.symbol}: {total_chunks} chunks")

                        all_bars = []
                        current = start
                        chunk_months = 3
                        chunk_idx = 0

                        while current < end:
                            chunk_idx += 1

                            # Calculate chunk end (3 months forward)
                            new_month = current.month + chunk_months
                            new_year = current.year + (new_month - 1) // 12
                            new_month = ((new_month - 1) % 12) + 1

                            try:
                                chunk_end_date = current.replace(year=new_year, month=new_month)
                            except ValueError:
                                chunk_end_date = current.replace(year=new_year, month=new_month, day=1)

                            chunk_end = min(chunk_end_date, end)

                            chunk_results = await self.downloader.download_all_pairs(
                                pairs=[pair],
                                start_date=current.strftime('%Y-%m-%d'),
                                end_date=chunk_end.strftime('%Y-%m-%d'),
                                get_timeframe_func=self.config.get_timeframe_for_pair
                            )

                            chunk_bars = chunk_results.get(pair.symbol, [])
                            all_bars.extend(chunk_bars)

                            # Log progress
                            progress_pct = (chunk_idx / total_chunks) * 100 if total_chunks > 0 else 0
                            if chunk_idx % 5 == 0 or chunk_idx == total_chunks:
                                logger.info(
                                    f"📊 {pair.symbol} download progress: {chunk_idx}/{total_chunks} chunks "
                                    f"({progress_pct:.1f}%) - {len(all_bars):,} bars"
                                )

                            current = chunk_end + timedelta(days=1)

                        bars = all_bars
                        logger.info(f"✅ Completed {pair.symbol} download: {len(bars):,} bars")

                    if bars:
                        logger.info(f"📤 Publishing {len(bars)} bars for {pair.symbol} to NATS/Kafka...")

                        # Convert to aggregate format
                        aggregates = []
                        for bar in bars:
                            aggregate = {
                                'symbol': bar['symbol'],
                                'timeframe': timeframe_str,
                                'timestamp_ms': bar['timestamp_ms'],
                                'open': bar['open'],
                                'high': bar['high'],
                                'low': bar['low'],
                                'close': bar['close'],
                                'volume': bar['volume'],
                                'vwap': bar.get('vwap', 0),
                                'range_pips': (bar['high'] - bar['low']) * 10000,  # Pips
                                'start_time': bar['timestamp'],
                                'end_time': bar['timestamp'],  # Historical data is already aggregated
                                'source': 'polygon_historical',
                                'event_type': 'ohlcv'
                            }
                            aggregates.append(aggregate)

                        # Publish in batches
                        batch_size = 100

                        for i in range(0, len(aggregates), batch_size):
                            batch = aggregates[i:i+batch_size]
                            await self.publisher.publish_batch(batch)
                            total_published += len(batch)

                            # Log progress every 10K bars
                            if i > 0 and i % 10000 == 0:
                                progress_pct = (i / len(aggregates)) * 100
                                logger.info(
                                    f"📤 Publishing {pair.symbol}: {i:,}/{len(aggregates):,} bars ({progress_pct:.1f}%)"
                                )

                        logger.info(f"✅ Published {len(aggregates)} bars for {pair.symbol}")
                        self.stats["total_published"] += len(aggregates)

                        # ✅ MARK PERIOD AS DOWNLOADED (before verification)
                        self.period_tracker.mark_downloaded(
                            symbol=pair.symbol,
                            timeframe=timeframe_str,
                            start_date=download_cfg['start_date'],
                            end_date=download_cfg['end_date'],
                            bars_count=len(bars),
                            source='polygon_historical',
                            verified=False  # Will be updated after verification
                        )

                        # ✅ CRITICAL: VERIFY data reached ClickHouse before continuing!
                        logger.info(f"🔍 Verifying {pair.symbol} data in ClickHouse...")
                        await asyncio.sleep(5)  # Wait for data-bridge to process

                        try:
                            # Get ClickHouse config from environment variables
                            ch_config = self.config.clickhouse_config

                            from clickhouse_driver import Client
                            ch_client = Client(
                                host=ch_config['host'],
                                port=ch_config['port'],
                                user=ch_config['user'],
                                password=ch_config['password'],
                                database=ch_config['database']
                            )

                            # Count bars in ClickHouse for this pair
                            query = f"""
                                SELECT COUNT(*) as count
                                FROM {ch_config['table']}
                                WHERE symbol = %(symbol)s
                                  AND timeframe = %(timeframe)s
                                  AND time >= %(start_date)s
                            """
                            result = ch_client.execute(query, {
                                'symbol': pair.symbol,
                                'timeframe': timeframe_str,
                                'start_date': download_cfg['start_date']
                            })

                            bars_in_clickhouse = result[0][0] if result else 0
                            verification_ratio = bars_in_clickhouse / len(bars) if len(bars) > 0 else 0

                            # Use timeframe-aware threshold for verification
                            from gap_detector import INTRADAY_TIMEFRAMES, INTRADAY_THRESHOLD, DAILY_THRESHOLD
                            if timeframe_str in INTRADAY_TIMEFRAMES:
                                verification_threshold = INTRADAY_THRESHOLD  # 100% for intraday
                            else:
                                verification_threshold = DAILY_THRESHOLD  # 80% for daily+

                            logger.info(
                                f"📊 Verification: {bars_in_clickhouse}/{len(bars)} bars in ClickHouse "
                                f"({verification_ratio*100:.1f}%) - Threshold: {verification_threshold*100}% for {timeframe_str}"
                            )

                            if verification_ratio < verification_threshold:
                                logger.error(f"⚠️  VERIFICATION FAILED: Only {verification_ratio*100:.1f}% of data reached ClickHouse!")
                                logger.error(f"⚠️  Expected: {len(bars)}, Got: {bars_in_clickhouse}")
                                logger.error(f"⚠️  Data-bridge might have crashed during publish. Re-publishing...")

                                # Re-publish missing data
                                await asyncio.sleep(10)  # Wait longer
                                for i in range(0, len(aggregates), batch_size):
                                    batch = aggregates[i:i+batch_size]
                                    await self.publisher.publish_batch(batch)

                                logger.info(f"♻️  Re-published {len(aggregates)} bars for {pair.symbol}")
                            else:
                                logger.info(f"✅ Verification PASSED: {pair.symbol} data complete in ClickHouse")

                                # ✅ UPDATE PERIOD TRACKER: Mark as verified
                                self.period_tracker.mark_downloaded(
                                    symbol=pair.symbol,
                                    timeframe=timeframe_str,
                                    start_date=download_cfg['start_date'],
                                    end_date=download_cfg['end_date'],
                                    bars_count=bars_in_clickhouse,
                                    source='polygon_historical',
                                    verified=True  # Verification passed!
                                )

                        except Exception as verify_error:
                            logger.warning(f"⚠️  Could not verify ClickHouse data: {verify_error}")
                            logger.warning(f"⚠️  Continuing anyway, gap detection will handle missing data")

                        # Update stats
                        self.stats["total_downloaded"] += len(bars)

                except Exception as pair_error:
                    logger.error(f"❌ Error downloading/publishing {pair.symbol}: {pair_error}", exc_info=True)
                    # Continue with next pair even if one fails
                    continue

            # Show final stats
            stats = self.publisher.get_stats()
            logger.info("=" * 80)
            logger.info("📊 DOWNLOAD COMPLETE - Final Stats:")
            logger.info(f"   Downloaded: {self.stats['total_downloaded']:,} bars")
            logger.info(f"   Published: {total_published:,} messages")
            logger.info(f"   NATS: {stats['published_nats']:,} messages")
            logger.info(f"   Buffered: {stats['buffered_to_disk']:,} messages")
            logger.info(f"   Errors: {stats['errors']}")
            logger.info("=" * 80)

        finally:
            await self.publisher.disconnect()

        logger.info("✅ Initial download complete")

    async def download_and_verify_gap(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        timeframe: str = '1m',
        max_retry_attempts: int = 3
    ) -> bool:
        """
        Download gap and verify it reached ClickHouse with retry logic

        Pipeline: Polygon -> NATS -> Tick Aggregator -> Data Bridge -> ClickHouse
        Expected propagation time: 30-60 seconds

        Args:
            symbol: Trading pair (e.g., 'XAU/USD')
            start_date: Gap start date
            end_date: Gap end date
            timeframe: Timeframe (default: '1m')
            max_retry_attempts: Maximum retry attempts (default: 3)

        Returns:
            True if download and verification succeeded
        """
        try:
            # 1. Download data from Polygon
            logger.info(f"📥 Downloading gap: {symbol} {start_date} to {end_date}")

            # Use existing downloader with date range
            timeframe_parts = timeframe.replace('m', ' minute').replace('h', ' hour').replace('d', ' day')
            results = await self.downloader.download_all_pairs(
                pairs=[p for p in self.config.pairs if p.symbol == symbol],
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                get_timeframe_func=self.config.get_timeframe_for_pair
            )

            bars = results.get(symbol, [])

            if not bars:
                logger.warning(f"No data downloaded for {symbol} {start_date}")
                return False

            logger.info(f"Downloaded {len(bars)} bars")

            # 2. Publish to NATS
            logger.info(f"📤 Publishing {len(bars)} bars to NATS")

            # Convert to aggregate format
            aggregates = []
            for bar in bars:
                aggregate = {
                    'symbol': bar['symbol'],
                    'timeframe': timeframe,
                    'timestamp_ms': bar['timestamp_ms'],
                    'open': bar['open'],
                    'high': bar['high'],
                    'low': bar['low'],
                    'close': bar['close'],
                    'volume': bar['volume'],
                    'vwap': bar.get('vwap', 0),
                    'range_pips': (bar['high'] - bar['low']) * 10000,
                    'start_time': bar['timestamp'],
                    'end_time': bar['timestamp'],
                    'source': 'polygon_gap_fill',
                    'event_type': 'ohlcv'
                }
                aggregates.append(aggregate)

            # Publish in batches
            batch_size = 100
            for i in range(0, len(aggregates), batch_size):
                batch = aggregates[i:i+batch_size]
                await self.publisher.publish_batch(batch)

            # 3. Wait for data to propagate through pipeline
            logger.info("⏳ Waiting 30s for data to propagate through pipeline...")
            await asyncio.sleep(30)

            # 4. Verify each date in range with retry
            if not self.verifier:
                logger.error("Verifier not initialized!")
                return False

            current_date = start_date
            all_verified = True

            while current_date <= end_date:
                # Skip weekends (Forex closed)
                if current_date.weekday() < 5:
                    verified = await self.verifier.verify_with_retry(
                        symbol=symbol,
                        timeframe=timeframe,
                        target_date=current_date,
                        min_bars=1,
                        max_retries=3,
                        retry_delay=10
                    )

                    if not verified:
                        logger.error(f"❌ Verification failed: {symbol} {current_date}")
                        all_verified = False

                current_date += timedelta(days=1)

            if all_verified:
                logger.info(f"✅ Gap filled and verified: {symbol} {start_date} to {end_date}")
            else:
                logger.error(f"❌ Gap verification incomplete: {symbol} {start_date} to {end_date}")

            return all_verified

        except Exception as e:
            logger.error(f"Download and verify failed: {e}", exc_info=True)
            return False

    async def retry_failed_verifications(self, failed_gaps: list, max_retry_attempts: int = 2):
        """
        Retry gaps that failed verification

        Args:
            failed_gaps: List of gap dictionaries with symbol, timeframe, start_date, end_date
            max_retry_attempts: Maximum retry attempts (default: 2)
        """
        logger.info(f"🔄 Retrying {len(failed_gaps)} failed gap verifications...")

        permanently_failed = []

        for gap in failed_gaps:
            retry_count = gap.get('retry_count', 0)

            if retry_count >= max_retry_attempts:
                logger.error(
                    f"⛔ Max retries ({max_retry_attempts}) reached for "
                    f"{gap['symbol']} {gap['start_date']} to {gap['end_date']}, "
                    f"marking for manual review"
                )
                permanently_failed.append(gap)
                continue

            logger.info(
                f"🔄 Retry attempt {retry_count + 1}/{max_retry_attempts}: "
                f"{gap['symbol']} {gap['start_date']} to {gap['end_date']}"
            )

            # Wait before retry (exponential backoff)
            wait_time = 30 * (2 ** retry_count)  # 30s, 60s, 120s...
            logger.info(f"⏳ Waiting {wait_time}s before retry...")
            await asyncio.sleep(wait_time)

            # Retry download and verification
            success = await self.download_and_verify_gap(
                symbol=gap['symbol'],
                start_date=gap['start_date'],
                end_date=gap['end_date'],
                timeframe=gap['timeframe'],
                max_retry_attempts=3
            )

            if success:
                logger.info(f"✅ Retry successful: {gap['symbol']} {gap['start_date']}")

                # Mark as complete in tracker
                self.period_tracker.mark_downloaded(
                    symbol=gap['symbol'],
                    timeframe=gap['timeframe'],
                    start_date=gap['start_date'].strftime('%Y-%m-%d'),
                    end_date=gap['end_date'].strftime('%Y-%m-%d'),
                    bars_count=0,
                    source='polygon_gap_fill_retry',
                    verified=True
                )
            else:
                logger.warning(f"⚠️  Retry failed: {gap['symbol']} {gap['start_date']}")
                gap['retry_count'] = retry_count + 1
                permanently_failed.append(gap)

        # Log permanently failed gaps for manual review
        if permanently_failed:
            logger.error("=" * 80)
            logger.error("⛔ GAPS REQUIRING MANUAL REVIEW")
            logger.error("=" * 80)
            for gap in permanently_failed:
                logger.error(
                    f"   {gap['symbol']} {gap['timeframe']}: "
                    f"{gap['start_date']} to {gap['end_date']} "
                    f"(retries: {gap.get('retry_count', 0)})"
                )
                if 'error' in gap:
                    logger.error(f"      Error: {gap['error']}")
            logger.error("=" * 80)

        return len(permanently_failed) == 0

    async def check_and_fill_gaps(self):
        """Check for gaps and download missing data with verification"""
        try:
            logger.info("🔍 Checking for data gaps...")

            # Get ClickHouse config from environment variables
            gap_config = self.config.clickhouse_config

            # Initialize verifier if not already done
            if not self.verifier:
                self.verifier = GapFillVerifier(gap_config)
                logger.info("✅ Gap fill verifier initialized")

            # Initialize gap detector
            from gap_detector import GapDetector
            gap_detector = GapDetector(gap_config)

            # Get messaging configs from environment variables
            nats_config = self.config.nats_config
            kafka_config = self.config.kafka_config

            nats_url = nats_config['url']
            kafka_brokers = ','.join(kafka_config['brokers'])

            # Reinitialize publisher
            self.publisher = MessagePublisher(
                nats_url=nats_url,
                kafka_brokers=kafka_brokers
            )
            await self.publisher.connect()

            # Check gaps for all pairs with verification
            pairs = self.config.pairs
            total_gaps_filled = 0
            failed_gaps = []

            for pair in pairs:
                symbol = pair.symbol
                logger.info(f"🔍 Checking gaps for {symbol}...")

                # Determine timeframe
                timeframe, multiplier = self.config.get_timeframe_for_pair(pair)
                timeframe_str = f"{multiplier}{timeframe[0]}"

                # ✅ USE DATE RANGE GAP DETECTION (not detect_gaps which only finds gaps BETWEEN data)
                # Get missing dates in configured range (default: today-7days to today)
                download_cfg = self.config.download_config
                from datetime import datetime, timedelta

                # Parse date range from config
                if download_cfg['start_date'].startswith('today'):
                    # Parse "today-7days" format
                    days_back = int(download_cfg['start_date'].replace('today-', '').replace('days', ''))
                    start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
                else:
                    start_date = download_cfg['start_date']

                if download_cfg['end_date'] == 'today':
                    end_date = datetime.now().strftime('%Y-%m-%d')
                else:
                    end_date = download_cfg['end_date']

                logger.info(f"📅 Checking date range: {start_date} to {end_date}")

                # Get ALL missing dates in this range (handles empty database + partial data)
                missing_dates = gap_detector.get_date_range_gaps(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    timeframe=timeframe_str
                )

                if missing_dates:
                    logger.info(f"📥 Found {len(missing_dates)} missing dates for {symbol}, downloading with verification...")

                    # Convert missing dates to gap ranges (consecutive dates grouped)
                    gaps = []
                    if missing_dates:
                        # Sort dates
                        sorted_dates = sorted([datetime.strptime(d, '%Y-%m-%d').date() for d in missing_dates])

                        # Group consecutive dates WITH MAX 7 DAYS PER GAP (prevent huge ranges)
                        MAX_GAP_DAYS = 7
                        gap_start = sorted_dates[0]
                        gap_end = sorted_dates[0]

                        for i in range(1, len(sorted_dates)):
                            # Check if consecutive (within 4 days for weekends) AND gap not too large
                            days_between = (sorted_dates[i] - gap_end).days
                            gap_size = (gap_end - gap_start).days

                            if days_between <= 4 and gap_size < MAX_GAP_DAYS:
                                # Continue current gap
                                gap_end = sorted_dates[i]
                            else:
                                # Save previous gap (max 7 days)
                                gaps.append((gap_start, gap_end))
                                # Start new gap
                                gap_start = sorted_dates[i]
                                gap_end = sorted_dates[i]

                        # Don't forget last gap
                        gaps.append((gap_start, gap_end))

                    logger.info(f"📥 Grouped into {len(gaps)} gap ranges")

                    for gap_start, gap_end in gaps:
                        try:
                            # gap_start and gap_end are already date objects from above
                            gap_start_date = gap_start
                            gap_end_date = gap_end

                            # Download and verify with retry
                            success = await self.download_and_verify_gap(
                                symbol=symbol,
                                start_date=gap_start_date,
                                end_date=gap_end_date,
                                timeframe=timeframe_str,
                                max_retry_attempts=3
                            )

                            if success:
                                logger.info(f"✅ Gap filled and verified: {symbol} {gap_start_date} -> {gap_end_date}")

                                # Mark as complete in tracker
                                self.period_tracker.mark_downloaded(
                                    symbol=symbol,
                                    timeframe=timeframe_str,
                                    start_date=gap_start_date.strftime('%Y-%m-%d'),
                                    end_date=gap_end_date.strftime('%Y-%m-%d'),
                                    bars_count=0,  # Will be counted in verification
                                    source='polygon_gap_fill',
                                    verified=True  # Verified after download
                                )
                                total_gaps_filled += 1
                            else:
                                logger.error(f"❌ Gap fill failed or unverified: {symbol} {gap_start_date} -> {gap_end_date}")
                                failed_gaps.append({
                                    'symbol': symbol,
                                    'timeframe': timeframe_str,
                                    'start_date': gap_start_date,
                                    'end_date': gap_end_date,
                                    'retry_count': 0
                                })

                        except Exception as e:
                            logger.error(f"❌ Error filling gap for {symbol}: {e}", exc_info=True)
                            failed_gaps.append({
                                'symbol': symbol,
                                'timeframe': timeframe_str,
                                'start_date': gap_start_date if 'gap_start_date' in locals() else gap_start,
                                'end_date': gap_end_date if 'gap_end_date' in locals() else gap_end,
                                'retry_count': 0,
                                'error': str(e)
                            })

                else:
                    logger.info(f"✅ No gaps found for {symbol}")

            # Retry failed verifications
            if failed_gaps:
                logger.warning(f"⚠️  {len(failed_gaps)} gaps failed verification, retrying...")
                await self.retry_failed_verifications(failed_gaps, max_retry_attempts=2)

            await self.publisher.disconnect()

            if total_gaps_filled > 0:
                logger.info(f"✅ Gap filling complete: {total_gaps_filled} gaps filled")
                self.stats["gaps_filled"] += total_gaps_filled
            else:
                logger.info("✅ No gaps to fill")

        except Exception as e:
            logger.error(f"❌ Error in gap checking: {e}", exc_info=True)
            self.stats["errors"] += 1

    async def start(self):
        """Start the historical downloader in continuous mode"""
        try:
            schedules = self.config.schedules
            gap_check_interval = schedules.get('gap_check', {}).get('interval_hours', 1)

            logger.info("🚀 Starting CONTINUOUS historical downloader...")
            logger.info(f"⏰ Gap check interval: {gap_check_interval} hour(s)")

            # Initial download on startup (DISABLED by default - polygon-historical is for gap filling only!)
            # Dukascopy handles initial historical download (2+ years)
            if schedules.get('initial_download', {}).get('on_startup', False):
                logger.warning("⚠️  Initial download is ENABLED - this should only run ONCE for setup!")
                await self.run_initial_download()
            else:
                logger.info("✅ Initial download DISABLED (gap filling mode only)")

            # Continuous gap checking + buffer flushing loop
            buffer_flush_interval = 300  # Flush buffer every 5 minutes
            last_buffer_flush = asyncio.get_event_loop().time()
            first_run = True  # Flag for immediate first gap check

            while True:
                try:
                    current_time = asyncio.get_event_loop().time()

                    # Check if time to flush buffer (every 5 minutes)
                    if current_time - last_buffer_flush >= buffer_flush_interval:
                        logger.info("♻️ Flushing disk buffer...")

                        # Initialize publisher if needed
                        if not self.publisher:
                            nats_config = self.config.nats_config
                            kafka_config = self.config.kafka_config

                            nats_url = nats_config['url']
                            kafka_brokers = ','.join(kafka_config['brokers'])

                            self.publisher = MessagePublisher(nats_url, kafka_brokers)
                            await self.publisher.connect()

                        flushed = await self.publisher.flush_buffer()

                        if flushed > 0:
                            logger.info(f"♻️ Flushed {flushed} buffered messages")

                        await self.publisher.disconnect()
                        self.publisher = None

                        last_buffer_flush = current_time

                    # ✅ FIX: Run gap check IMMEDIATELY on first run, then wait for next cycle
                    if first_run:
                        logger.info("🚀 Running first gap check immediately on startup...")
                        first_run = False
                    else:
                        # Wait for next check (after first run)
                        logger.info(f"⏰ Waiting {gap_check_interval} hour(s) until next gap check...")
                        await asyncio.sleep(min(gap_check_interval * 3600, buffer_flush_interval))

                    # Check and fill gaps
                    await self.check_and_fill_gaps()

                except Exception as e:
                    logger.error(f"❌ Error in gap check cycle: {e}", exc_info=True)
                    # Continue running even if one cycle fails
                    await asyncio.sleep(60)  # Wait 1 minute before retrying

        except KeyboardInterrupt:
            logger.info("🛑 Received shutdown signal")
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}", exc_info=True)
        finally:
            # Show final statistics
            logger.info("=" * 80)
            logger.info("📊 FINAL STATISTICS:")
            logger.info(f"   Downloaded: {self.stats['total_downloaded']:,} bars")
            logger.info(f"   Published: {self.stats['total_published']:,} messages")
            logger.info(f"   Gaps filled: {self.stats['gaps_filled']}")
            logger.info(f"   Errors: {self.stats['errors']}")
            logger.info("=" * 80)
            logger.info("✅ Historical downloader stopped")

async def main():
    service = PolygonHistoricalService()
    await service.start()

if __name__ == '__main__':
    asyncio.run(main())
