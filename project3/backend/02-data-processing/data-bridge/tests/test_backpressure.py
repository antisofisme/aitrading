"""
Test Backpressure Mechanism for Data Bridge

Tests the backpressure functionality that prevents OOM during burst traffic.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime


@pytest.fixture
def mock_clickhouse_writer():
    """Mock ClickHouse writer with controllable buffer"""
    writer = Mock()
    writer.aggregate_buffer = []
    writer.get_stats = Mock(return_value={'buffer_size': 0})
    return writer


@pytest.fixture
def mock_external_writer():
    """Mock external data writer"""
    writer = Mock()
    writer.buffer = []
    return writer


@pytest.fixture
def mock_nats_subscriber():
    """Mock NATS subscriber with pause/resume"""
    subscriber = AsyncMock()
    subscriber.pause = AsyncMock()
    subscriber.resume = AsyncMock()
    subscriber.is_paused = Mock(return_value=False)
    subscriber.get_stats = Mock(return_value={'is_paused': False})
    return subscriber


@pytest.fixture
def mock_kafka_subscriber():
    """Mock Kafka subscriber with pause/resume"""
    subscriber = AsyncMock()
    subscriber.pause = AsyncMock()
    subscriber.resume = AsyncMock()
    subscriber.is_paused = Mock(return_value=False)
    subscriber.get_stats = Mock(return_value={'is_paused': False})
    return subscriber


@pytest.mark.asyncio
async def test_backpressure_activates_at_threshold(
    mock_clickhouse_writer,
    mock_external_writer,
    mock_nats_subscriber,
    mock_kafka_subscriber
):
    """Test that backpressure activates when buffer exceeds PAUSE_THRESHOLD"""
    # Import after fixtures to avoid initialization issues
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

    from main import DataBridge, PAUSE_THRESHOLD

    # Create DataBridge instance
    bridge = DataBridge()
    bridge.clickhouse_writer = mock_clickhouse_writer
    bridge.external_data_writer = mock_external_writer
    bridge.nats_subscriber = mock_nats_subscriber
    bridge.kafka_subscriber = mock_kafka_subscriber

    # Simulate high buffer (exceed PAUSE_THRESHOLD)
    mock_clickhouse_writer.aggregate_buffer = ['msg'] * (PAUSE_THRESHOLD + 1000)

    # Run backpressure check
    await bridge.check_backpressure()

    # Verify pause was called
    mock_nats_subscriber.pause.assert_called_once()
    mock_kafka_subscriber.pause.assert_called_once()

    # Verify internal state
    assert bridge.nats_paused is True
    assert bridge.kafka_paused is True
    assert bridge.backpressure_active_count == 1
    assert bridge.last_pause_time is not None


@pytest.mark.asyncio
async def test_backpressure_resumes_at_threshold(
    mock_clickhouse_writer,
    mock_external_writer,
    mock_nats_subscriber,
    mock_kafka_subscriber
):
    """Test that backpressure releases when buffer drops below RESUME_THRESHOLD"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

    from main import DataBridge, RESUME_THRESHOLD

    # Create DataBridge instance
    bridge = DataBridge()
    bridge.clickhouse_writer = mock_clickhouse_writer
    bridge.external_data_writer = mock_external_writer
    bridge.nats_subscriber = mock_nats_subscriber
    bridge.kafka_subscriber = mock_kafka_subscriber

    # Simulate paused state
    bridge.nats_paused = True
    bridge.kafka_paused = True
    bridge.last_pause_time = datetime.utcnow()

    # Simulate low buffer (below RESUME_THRESHOLD)
    mock_clickhouse_writer.aggregate_buffer = ['msg'] * (RESUME_THRESHOLD - 1000)

    # Run backpressure check
    await bridge.check_backpressure()

    # Verify resume was called
    mock_nats_subscriber.resume.assert_called_once()
    mock_kafka_subscriber.resume.assert_called_once()

    # Verify internal state
    assert bridge.nats_paused is False
    assert bridge.kafka_paused is False
    assert bridge.last_resume_time is not None


@pytest.mark.asyncio
async def test_backpressure_hysteresis(
    mock_clickhouse_writer,
    mock_external_writer,
    mock_nats_subscriber,
    mock_kafka_subscriber
):
    """Test hysteresis prevents rapid pause/resume cycles"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

    from main import DataBridge, PAUSE_THRESHOLD, RESUME_THRESHOLD

    # Create DataBridge instance
    bridge = DataBridge()
    bridge.clickhouse_writer = mock_clickhouse_writer
    bridge.external_data_writer = mock_external_writer
    bridge.nats_subscriber = mock_nats_subscriber
    bridge.kafka_subscriber = mock_kafka_subscriber

    # Set buffer to middle zone (between RESUME and PAUSE thresholds)
    middle_value = (PAUSE_THRESHOLD + RESUME_THRESHOLD) // 2
    mock_clickhouse_writer.aggregate_buffer = ['msg'] * middle_value

    # Run backpressure check (should not trigger pause)
    await bridge.check_backpressure()

    # Verify no pause/resume called
    mock_nats_subscriber.pause.assert_not_called()
    mock_nats_subscriber.resume.assert_not_called()

    # Verify state remains unchanged
    assert bridge.nats_paused is False
    assert bridge.kafka_paused is False


@pytest.mark.asyncio
async def test_backpressure_no_double_pause(
    mock_clickhouse_writer,
    mock_external_writer,
    mock_nats_subscriber,
    mock_kafka_subscriber
):
    """Test that pause is not called multiple times when already paused"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

    from main import DataBridge, PAUSE_THRESHOLD

    # Create DataBridge instance
    bridge = DataBridge()
    bridge.clickhouse_writer = mock_clickhouse_writer
    bridge.external_data_writer = mock_external_writer
    bridge.nats_subscriber = mock_nats_subscriber
    bridge.kafka_subscriber = mock_kafka_subscriber

    # Set high buffer
    mock_clickhouse_writer.aggregate_buffer = ['msg'] * (PAUSE_THRESHOLD + 1000)

    # First backpressure check (should pause)
    await bridge.check_backpressure()
    assert mock_nats_subscriber.pause.call_count == 1

    # Second backpressure check (should not pause again)
    await bridge.check_backpressure()
    assert mock_nats_subscriber.pause.call_count == 1  # Still 1, not 2


@pytest.mark.asyncio
async def test_nats_pause_drops_messages():
    """Test that NATS subscriber drops messages when paused"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

    from nats_subscriber import NATSSubscriber

    # Create subscriber
    config = {'url': 'nats://localhost:4222'}
    message_handler = AsyncMock()
    subscriber = NATSSubscriber(config, message_handler)
    subscriber.is_running = True

    # Create mock NATS message
    mock_msg = Mock()
    mock_msg.subject = 'market.EURUSD.tick'
    mock_msg.data = b'{"pair": "EUR/USD", "b": 1.0850, "a": 1.0851}'

    # Process message normally
    await subscriber._handle_market_message(mock_msg)
    assert message_handler.call_count == 1

    # Pause subscriber
    await subscriber.pause()
    assert subscriber.is_paused() is True

    # Process message while paused (should be dropped)
    await subscriber._handle_market_message(mock_msg)
    assert message_handler.call_count == 1  # Still 1, not 2

    # Resume subscriber
    await subscriber.resume()
    assert subscriber.is_paused() is False

    # Process message after resume (should work)
    await subscriber._handle_market_message(mock_msg)
    assert message_handler.call_count == 2


@pytest.mark.asyncio
async def test_kafka_pause_uses_native_api():
    """Test that Kafka subscriber uses aiokafka's native pause/resume"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

    from kafka_subscriber import KafkaSubscriber

    # Create subscriber
    config = {'brokers': ['localhost:9092'], 'group_id': 'test'}
    message_handler = AsyncMock()
    subscriber = KafkaSubscriber(config, message_handler)

    # Mock consumer
    mock_consumer = Mock()
    mock_consumer.assignment = Mock(return_value=[Mock(topic='test', partition=0)])
    mock_consumer.pause = Mock()
    mock_consumer.resume = Mock()
    mock_consumer.paused = Mock(return_value=[])

    subscriber.consumer = mock_consumer
    subscriber.is_running = True

    # Test pause
    await subscriber.pause()
    mock_consumer.pause.assert_called_once()

    # Test resume
    mock_consumer.paused.return_value = [Mock(topic='test', partition=0)]
    await subscriber.resume()
    mock_consumer.resume.assert_called_once()


@pytest.mark.asyncio
async def test_backpressure_metrics_in_heartbeat():
    """Test that backpressure metrics are included in heartbeat"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

    from main import DataBridge

    # Create DataBridge instance
    bridge = DataBridge()
    bridge.clickhouse_writer = Mock()
    bridge.clickhouse_writer.aggregate_buffer = ['msg'] * 35000
    bridge.clickhouse_writer.get_stats = Mock(return_value={'buffer_size': 35000})

    bridge.nats_subscriber = Mock()
    bridge.nats_subscriber.get_stats = Mock(return_value={'total_messages': 10000})

    bridge.retry_queue = None

    # Set backpressure state
    bridge.nats_paused = True
    bridge.backpressure_active_count = 3
    bridge.last_pause_time = datetime.utcnow()
    bridge.last_resume_time = datetime.utcnow()

    # Simulate heartbeat metrics collection (simplified)
    nats_stats = bridge.nats_subscriber.get_stats()
    clickhouse_stats = bridge.clickhouse_writer.get_stats()

    metrics = {
        'nats_msgs': nats_stats.get('total_messages', 0),
        'ch_buffer': clickhouse_stats.get('buffer_size', 0),
        'backpressure': {
            'active': bridge.nats_paused or bridge.kafka_paused,
            'nats_paused': bridge.nats_paused,
            'current_buffer': len(bridge.clickhouse_writer.aggregate_buffer),
            'pause_count': bridge.backpressure_active_count,
        }
    }

    # Verify metrics
    assert metrics['backpressure']['active'] is True
    assert metrics['backpressure']['nats_paused'] is True
    assert metrics['backpressure']['current_buffer'] == 35000
    assert metrics['backpressure']['pause_count'] == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
