"""
Unit tests for Gap Fill Verification

Tests the GapFillVerifier utility and integration with Historical Downloader
"""
import pytest
import asyncio
from datetime import date, datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
import os

# Add project paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../project3/backend')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../project3/backend/00-data-ingestion/polygon-historical-downloader/src')))

from shared.components.utils.gap_fill_verifier import GapFillVerifier


class TestGapFillVerifier:
    """Test suite for GapFillVerifier utility"""

    @pytest.fixture
    def mock_clickhouse_config(self):
        """Mock ClickHouse configuration"""
        return {
            'host': 'localhost',
            'port': 9000,
            'database': 'test_db',
            'user': 'test_user',
            'password': 'test_password'
        }

    @pytest.fixture
    def verifier(self, mock_clickhouse_config):
        """Create verifier instance with mocked ClickHouse client"""
        with patch('shared.components.utils.gap_fill_verifier.Client') as mock_client:
            verifier = GapFillVerifier(mock_clickhouse_config)
            verifier.clickhouse = mock_client.return_value
            return verifier

    def test_verifier_initialization(self, mock_clickhouse_config):
        """Test verifier initializes correctly"""
        with patch('shared.components.utils.gap_fill_verifier.Client') as mock_client:
            verifier = GapFillVerifier(mock_clickhouse_config)

            mock_client.assert_called_once_with(
                host='localhost',
                port=9000,
                database='test_db',
                user='test_user',
                password='test_password'
            )

    def test_verify_date_has_data_success(self, verifier):
        """Test verification succeeds when data exists"""
        # Mock ClickHouse query result: 288 bars found
        verifier.clickhouse.execute = Mock(return_value=[(288,)])

        result = verifier.verify_date_has_data(
            symbol='XAU/USD',
            timeframe='5m',
            target_date=date(2025, 10, 10),
            min_bars=1
        )

        assert result is True
        verifier.clickhouse.execute.assert_called_once()

    def test_verify_date_has_data_failure(self, verifier):
        """Test verification fails when no data exists"""
        # Mock ClickHouse query result: 0 bars found
        verifier.clickhouse.execute = Mock(return_value=[(0,)])

        result = verifier.verify_date_has_data(
            symbol='XAU/USD',
            timeframe='5m',
            target_date=date(2025, 10, 10),
            min_bars=1
        )

        assert result is False

    def test_verify_date_has_data_insufficient_bars(self, verifier):
        """Test verification fails when bar count below minimum"""
        # Mock ClickHouse query result: 50 bars found, need 100
        verifier.clickhouse.execute = Mock(return_value=[(50,)])

        result = verifier.verify_date_has_data(
            symbol='XAU/USD',
            timeframe='5m',
            target_date=date(2025, 10, 10),
            min_bars=100
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_verify_with_retry_first_attempt_success(self, verifier):
        """Test retry succeeds on first attempt"""
        verifier.verify_date_has_data = Mock(return_value=True)

        result = await verifier.verify_with_retry(
            symbol='XAU/USD',
            timeframe='5m',
            target_date=date(2025, 10, 10),
            min_bars=1,
            max_retries=3,
            retry_delay=1
        )

        assert result is True
        assert verifier.verify_date_has_data.call_count == 1

    @pytest.mark.asyncio
    async def test_verify_with_retry_second_attempt_success(self, verifier):
        """Test retry succeeds on second attempt"""
        # First call fails, second succeeds
        verifier.verify_date_has_data = Mock(side_effect=[False, True])

        result = await verifier.verify_with_retry(
            symbol='XAU/USD',
            timeframe='5m',
            target_date=date(2025, 10, 10),
            min_bars=1,
            max_retries=3,
            retry_delay=1
        )

        assert result is True
        assert verifier.verify_date_has_data.call_count == 2

    @pytest.mark.asyncio
    async def test_verify_with_retry_all_attempts_fail(self, verifier):
        """Test retry fails after max attempts"""
        verifier.verify_date_has_data = Mock(return_value=False)

        result = await verifier.verify_with_retry(
            symbol='XAU/USD',
            timeframe='5m',
            target_date=date(2025, 10, 10),
            min_bars=1,
            max_retries=3,
            retry_delay=1
        )

        assert result is False
        assert verifier.verify_date_has_data.call_count == 3

    def test_verify_date_range(self, verifier):
        """Test date range verification"""
        # Mock: Monday and Tuesday have data, Wednesday missing
        def mock_verify(symbol, timeframe, target_date, min_bars):
            if target_date.weekday() == 2:  # Wednesday
                return False
            return True

        verifier.verify_date_has_data = Mock(side_effect=mock_verify)

        start = date(2025, 10, 6)  # Monday
        end = date(2025, 10, 8)    # Wednesday

        all_verified, verified_dates, failed_dates = verifier.verify_date_range(
            symbol='XAU/USD',
            timeframe='5m',
            start_date=start,
            end_date=end,
            min_bars=1
        )

        assert all_verified is False
        assert len(verified_dates) == 2  # Mon, Tue
        assert len(failed_dates) == 1    # Wed
        assert failed_dates[0].weekday() == 2  # Wednesday

    def test_get_date_bar_count(self, verifier):
        """Test getting bar count for a date"""
        verifier.clickhouse.execute = Mock(return_value=[(288,)])

        count = verifier.get_date_bar_count(
            symbol='XAU/USD',
            timeframe='5m',
            target_date=date(2025, 10, 10)
        )

        assert count == 288

    def test_get_date_range_stats(self, verifier):
        """Test getting date range statistics"""
        # Mock query result: total_bars, dates_with_data, min_date, max_date
        verifier.clickhouse.execute = Mock(return_value=[(
            1440,  # total bars
            5,     # dates with data
            datetime(2025, 10, 6),  # min date
            datetime(2025, 10, 10)  # max date
        )])

        stats = verifier.get_date_range_stats(
            symbol='XAU/USD',
            timeframe='5m',
            start_date=date(2025, 10, 6),
            end_date=date(2025, 10, 10)
        )

        assert stats['total_bars'] == 1440
        assert stats['dates_with_data'] == 5
        assert stats['dates_expected'] == 5  # Mon-Fri
        assert stats['avg_bars_per_day'] == 288
        assert stats['completeness'] == 1.0  # 100%


class TestGapFillIntegration:
    """Integration tests for gap filling with verification"""

    @pytest.mark.asyncio
    async def test_download_and_verify_gap_success(self):
        """Test successful gap download and verification"""
        with patch('main.PolygonHistoricalService') as mock_service:
            service = mock_service.return_value

            # Mock downloader
            service.downloader.download_all_pairs = AsyncMock(return_value={
                'XAU/USD': [
                    {
                        'symbol': 'XAU/USD',
                        'timestamp_ms': 1728561600000,
                        'timestamp': '2025-10-10T10:00:00Z',
                        'open': 2650.50,
                        'high': 2651.00,
                        'low': 2650.00,
                        'close': 2650.75,
                        'volume': 100
                    }
                ]
            })

            # Mock publisher
            service.publisher.publish_batch = AsyncMock()

            # Mock verifier
            mock_verifier = Mock()
            mock_verifier.verify_with_retry = AsyncMock(return_value=True)
            service.verifier = mock_verifier

            # Test download_and_verify_gap
            from main import PolygonHistoricalService
            service_instance = PolygonHistoricalService()

            # Replace with mocks
            service_instance.downloader = service.downloader
            service_instance.publisher = service.publisher
            service_instance.verifier = mock_verifier
            service_instance.config = Mock()
            service_instance.config.pairs = []

            result = await service_instance.download_and_verify_gap(
                symbol='XAU/USD',
                start_date=date(2025, 10, 10),
                end_date=date(2025, 10, 10),
                timeframe='5m'
            )

            assert result is True
            service.downloader.download_all_pairs.assert_called_once()
            service.publisher.publish_batch.assert_called()
            mock_verifier.verify_with_retry.assert_called_once()

    @pytest.mark.asyncio
    async def test_retry_failed_verifications(self):
        """Test retry logic for failed verifications"""
        with patch('main.PolygonHistoricalService') as mock_service:
            service = mock_service.return_value

            # Mock failed gaps
            failed_gaps = [
                {
                    'symbol': 'XAU/USD',
                    'timeframe': '5m',
                    'start_date': date(2025, 10, 10),
                    'end_date': date(2025, 10, 10),
                    'retry_count': 0
                }
            ]

            # Mock download_and_verify_gap to succeed on retry
            service.download_and_verify_gap = AsyncMock(return_value=True)
            service.period_tracker = Mock()
            service.period_tracker.mark_downloaded = Mock()

            from main import PolygonHistoricalService
            service_instance = PolygonHistoricalService()
            service_instance.download_and_verify_gap = service.download_and_verify_gap
            service_instance.period_tracker = service.period_tracker
            service_instance.central_hub = Mock()
            service_instance.central_hub.registered = False

            result = await service_instance.retry_failed_verifications(
                failed_gaps,
                max_retry_attempts=2
            )

            assert result is True
            service.download_and_verify_gap.assert_called_once()
            service.period_tracker.mark_downloaded.assert_called_once()


class TestVerificationWorkflow:
    """End-to-end workflow tests"""

    @pytest.mark.asyncio
    async def test_full_verification_workflow(self):
        """Test complete gap fill workflow with verification"""
        # This would be an integration test with real services
        # Placeholder for demonstration
        pass

    def test_verification_logging(self, caplog):
        """Test that verification produces correct logs"""
        mock_config = {
            'host': 'localhost',
            'port': 9000,
            'database': 'test_db',
            'user': 'test_user',
            'password': 'test_password'
        }

        with patch('shared.components.utils.gap_fill_verifier.Client'):
            verifier = GapFillVerifier(mock_config)

            # Check initialization log
            assert 'GapFillVerifier initialized' in caplog.text


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
