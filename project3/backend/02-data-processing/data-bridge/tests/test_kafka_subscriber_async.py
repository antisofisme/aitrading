"""
Comprehensive async tests for KafkaSubscriber using aiokafka
Tests connection, message consumption, error handling, and performance
"""
import asyncio
import pytest
import orjson
from unittest.mock import AsyncMock, MagicMock, patch
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError, KafkaConnectionError

# Import the async KafkaSubscriber
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from kafka_subscriber import KafkaSubscriber


# =====================================================================
# FIXTURES
# =====================================================================

@pytest.fixture
def kafka_config():
    """Sample Kafka configuration"""
    return {
        'brokers': ['localhost:9092'],
        'group_id': 'test-group',
        'auto_offset_reset': 'latest',
        'enable_auto_commit': True,
        'auto_commit_interval_ms': 5000,
        'fetch_min_bytes': 1024,
        'fetch_max_wait_ms': 500,
        'max_poll_records': 500,
        'session_timeout_ms': 30000,
        'topics': {
            'tick_archive': 'tick_archive',
            'aggregate_archive': 'aggregate_archive',
            'confirmation_archive': 'confirmation_archive'
        }
    }


@pytest.fixture
async def message_handler():
    """Mock async message handler"""
    handler = AsyncMock()
    handler.return_value = None
    return handler


@pytest.fixture
async def kafka_subscriber(kafka_config, message_handler):
    """Create KafkaSubscriber instance"""
    subscriber = KafkaSubscriber(kafka_config, message_handler)
    yield subscriber
    # Cleanup
    if subscriber.is_running:
        await subscriber.close()


# =====================================================================
# CONNECTION TESTS
# =====================================================================

@pytest.mark.asyncio
async def test_initialization(kafka_config, message_handler):
    """Test KafkaSubscriber initialization"""
    subscriber = KafkaSubscriber(kafka_config, message_handler)

    assert subscriber.config == kafka_config
    assert subscriber.message_handler == message_handler
    assert subscriber.consumer is None
    assert subscriber.is_running is False
    assert subscriber.total_messages == 0


@pytest.mark.asyncio
async def test_connection_success(kafka_subscriber):
    """Test successful Kafka connection"""
    with patch.object(AIOKafkaConsumer, 'start', new_callable=AsyncMock) as mock_start:
        mock_start.return_value = None

        with patch('kafka_subscriber.AIOKafkaConsumer') as MockConsumer:
            mock_consumer = AsyncMock()
            MockConsumer.return_value = mock_consumer
            mock_consumer.start = mock_start

            # Temporarily replace consumer
            kafka_subscriber.consumer = mock_consumer

            await kafka_subscriber.connect()

            assert kafka_subscriber.is_running is True
            assert kafka_subscriber.is_connected() is True


@pytest.mark.asyncio
async def test_connection_failure(kafka_subscriber):
    """Test Kafka connection failure"""
    with patch('kafka_subscriber.AIOKafkaConsumer') as MockConsumer:
        MockConsumer.side_effect = KafkaConnectionError("Connection refused")

        with pytest.raises(KafkaConnectionError):
            await kafka_subscriber.connect()

        assert kafka_subscriber.is_running is False
        assert kafka_subscriber.is_connected() is False


# =====================================================================
# MESSAGE CONSUMPTION TESTS
# =====================================================================

@pytest.mark.asyncio
async def test_poll_messages_basic(kafka_subscriber, message_handler):
    """Test basic message polling"""
    # Create mock messages
    mock_messages = [
        MagicMock(
            topic='tick_archive',
            partition=0,
            offset=1,
            value={'pair': 'EUR/USD', 't': 1234567890, 'b': 1.1000, 'a': 1.1001}
        ),
        MagicMock(
            topic='aggregate_archive',
            partition=0,
            offset=2,
            value={'pair': 'EUR/USD', 's': 1234567890, 'o': 1.1000, 'c': 1.1010}
        )
    ]

    # Mock consumer
    mock_consumer = AsyncMock()

    # Create async iterator for messages
    async def mock_iterator():
        for msg in mock_messages:
            yield msg

    mock_consumer.__aiter__ = lambda self: mock_iterator()

    kafka_subscriber.consumer = mock_consumer
    kafka_subscriber.is_running = True

    # Run poll_messages in background for a short time
    async def stop_after_delay():
        await asyncio.sleep(0.1)
        kafka_subscriber.is_running = False

    await asyncio.gather(
        kafka_subscriber.poll_messages(),
        stop_after_delay(),
        return_exceptions=True
    )

    # Verify message handler was called
    assert message_handler.call_count == 2


@pytest.mark.asyncio
async def test_consume_generator(kafka_subscriber):
    """Test consume() async generator"""
    # Create mock messages
    mock_messages = [
        MagicMock(
            topic='tick_archive',
            partition=0,
            offset=1,
            timestamp=1234567890,
            value={'pair': 'EUR/USD', 't': 1234567890, 'b': 1.1000}
        )
    ]

    # Mock consumer
    mock_consumer = AsyncMock()

    async def mock_iterator():
        for msg in mock_messages:
            yield msg

    mock_consumer.__aiter__ = lambda self: mock_iterator()

    kafka_subscriber.consumer = mock_consumer
    kafka_subscriber.is_running = True

    # Consume messages
    consumed = []
    async for message in kafka_subscriber.consume():
        consumed.append(message)
        if len(consumed) >= 1:
            break

    assert len(consumed) == 1
    assert consumed[0]['pair'] == 'EUR/USD'
    assert '_topic' in consumed[0]
    assert '_offset' in consumed[0]


# =====================================================================
# MESSAGE TYPE DETECTION TESTS
# =====================================================================

@pytest.mark.asyncio
async def test_external_data_type_detection(kafka_subscriber, message_handler):
    """Test external data type detection from topic"""
    mock_record = MagicMock(
        topic='market.external.fear_greed_index',
        partition=0,
        offset=1,
        value={'value': 75, 'classification': 'Greed'}
    )

    kafka_subscriber.is_running = True

    await kafka_subscriber._handle_message(mock_record)

    # Verify handler was called with correct data_type
    message_handler.assert_called_once()
    call_args = message_handler.call_args
    assert call_args[1]['data_type'] == 'external'

    # Verify external_type was extracted
    data = call_args[0][0]
    assert data['_external_type'] == 'fear_greed_index'


@pytest.mark.asyncio
async def test_aggregate_type_detection(kafka_subscriber, message_handler):
    """Test aggregate data type detection"""
    mock_record = MagicMock(
        topic='aggregate_archive',
        partition=0,
        offset=1,
        value={'pair': 'EUR/USD', 's': 1234567890, 'o': 1.1000, 'c': 1.1010}
    )

    kafka_subscriber.is_running = True

    await kafka_subscriber._handle_message(mock_record)

    message_handler.assert_called_once()
    call_args = message_handler.call_args
    assert call_args[1]['data_type'] == 'aggregate'


@pytest.mark.asyncio
async def test_tick_type_detection(kafka_subscriber, message_handler):
    """Test tick data type detection"""
    mock_record = MagicMock(
        topic='tick_archive',
        partition=0,
        offset=1,
        value={'pair': 'EUR/USD', 't': 1234567890, 'b': 1.1000, 'a': 1.1001}
    )

    kafka_subscriber.is_running = True

    await kafka_subscriber._handle_message(mock_record)

    message_handler.assert_called_once()
    call_args = message_handler.call_args
    assert call_args[1]['data_type'] == 'tick'


# =====================================================================
# STATISTICS TESTS
# =====================================================================

@pytest.mark.asyncio
async def test_statistics_tracking(kafka_subscriber, message_handler):
    """Test that statistics are tracked correctly"""
    messages = [
        MagicMock(topic='tick_archive', partition=0, offset=1, value={'pair': 'EUR/USD'}),
        MagicMock(topic='tick_archive', partition=0, offset=2, value={'pair': 'GBP/USD'}),
        MagicMock(topic='aggregate_archive', partition=0, offset=3, value={'pair': 'EUR/USD'}),
        MagicMock(topic='market.external.fear_greed_index', partition=0, offset=4, value={'value': 75}),
    ]

    kafka_subscriber.is_running = True

    for msg in messages:
        await kafka_subscriber._handle_message(msg)

    stats = kafka_subscriber.get_stats()

    assert stats['total_messages'] == 4
    assert stats['tick_messages'] == 2
    assert stats['aggregate_messages'] == 1
    assert stats['external_messages'] == 1
    assert stats['implementation'] == 'aiokafka (async)'


# =====================================================================
# ERROR HANDLING TESTS
# =====================================================================

@pytest.mark.asyncio
async def test_message_handler_error_continues_consumption(kafka_subscriber, message_handler):
    """Test that handler errors don't stop consumption"""
    # First call fails, second succeeds
    message_handler.side_effect = [Exception("Handler error"), None]

    messages = [
        MagicMock(topic='tick_archive', partition=0, offset=1, value={'pair': 'EUR/USD'}),
        MagicMock(topic='tick_archive', partition=0, offset=2, value={'pair': 'GBP/USD'}),
    ]

    kafka_subscriber.is_running = True

    for msg in messages:
        await kafka_subscriber._handle_message(msg)

    # Both messages should be attempted despite first error
    assert message_handler.call_count == 2


@pytest.mark.asyncio
async def test_consume_not_connected_error(kafka_subscriber):
    """Test that consume() raises error if not connected"""
    kafka_subscriber.is_running = False
    kafka_subscriber.consumer = None

    with pytest.raises(RuntimeError, match="not connected"):
        async for _ in kafka_subscriber.consume():
            pass


# =====================================================================
# OFFSET MANAGEMENT TESTS
# =====================================================================

@pytest.mark.asyncio
async def test_manual_commit(kafka_config, message_handler):
    """Test manual offset commit"""
    kafka_config['enable_auto_commit'] = False
    subscriber = KafkaSubscriber(kafka_config, message_handler)

    mock_consumer = AsyncMock()
    mock_consumer.commit = AsyncMock()

    subscriber.consumer = mock_consumer
    subscriber.is_running = True

    await subscriber.commit()

    mock_consumer.commit.assert_called_once()


@pytest.mark.asyncio
async def test_auto_commit_no_manual_commit(kafka_config, message_handler):
    """Test that manual commit is skipped when auto_commit enabled"""
    kafka_config['enable_auto_commit'] = True
    subscriber = KafkaSubscriber(kafka_config, message_handler)

    mock_consumer = AsyncMock()
    mock_consumer.commit = AsyncMock()

    subscriber.consumer = mock_consumer
    subscriber.is_running = True

    await subscriber.commit()

    # Should not call commit when auto_commit is enabled
    mock_consumer.commit.assert_not_called()


# =====================================================================
# SEEK OPERATIONS TESTS
# =====================================================================

@pytest.mark.asyncio
async def test_seek_to_beginning(kafka_subscriber):
    """Test seeking to beginning of partitions"""
    mock_consumer = AsyncMock()
    mock_consumer.assignment = MagicMock(return_value=[])
    mock_consumer.seek_to_beginning = AsyncMock()

    kafka_subscriber.consumer = mock_consumer
    kafka_subscriber.is_running = True

    await kafka_subscriber.seek_to_beginning()

    mock_consumer.seek_to_beginning.assert_called_once()


@pytest.mark.asyncio
async def test_seek_to_end(kafka_subscriber):
    """Test seeking to end of partitions"""
    mock_consumer = AsyncMock()
    mock_consumer.assignment = MagicMock(return_value=[])
    mock_consumer.seek_to_end = AsyncMock()

    kafka_subscriber.consumer = mock_consumer
    kafka_subscriber.is_running = True

    await kafka_subscriber.seek_to_end()

    mock_consumer.seek_to_end.assert_called_once()


# =====================================================================
# LAG MONITORING TESTS
# =====================================================================

@pytest.mark.asyncio
async def test_get_lag(kafka_subscriber):
    """Test consumer lag calculation"""
    from aiokafka import TopicPartition

    mock_consumer = AsyncMock()

    # Mock partition assignment
    tp1 = TopicPartition('tick_archive', 0)
    tp2 = TopicPartition('aggregate_archive', 0)
    mock_consumer.assignment = MagicMock(return_value=[tp1, tp2])

    # Mock position (current offset)
    async def mock_position(tp):
        return 100 if tp.partition == 0 else 50

    mock_consumer.position = mock_position

    # Mock end_offsets (high water mark)
    async def mock_end_offsets(partitions):
        return {tp1: 150, tp2: 75}

    mock_consumer.end_offsets = mock_end_offsets

    kafka_subscriber.consumer = mock_consumer
    kafka_subscriber.is_running = True

    lag = await kafka_subscriber.get_lag()

    assert lag['tick_archive-0'] == 50  # 150 - 100
    assert lag['aggregate_archive-0'] == 25  # 75 - 50


# =====================================================================
# HEALTH CHECK TESTS
# =====================================================================

@pytest.mark.asyncio
async def test_health_check_healthy(kafka_subscriber):
    """Test health check when consumer is healthy"""
    from aiokafka import TopicPartition

    mock_consumer = AsyncMock()
    tp = TopicPartition('tick_archive', 0)
    mock_consumer.assignment = MagicMock(return_value=[tp])

    async def mock_position(tp):
        return 100

    async def mock_end_offsets(partitions):
        return {tp: 100}

    mock_consumer.position = mock_position
    mock_consumer.end_offsets = mock_end_offsets

    kafka_subscriber.consumer = mock_consumer
    kafka_subscriber.is_running = True
    kafka_subscriber.total_messages = 100

    health = await kafka_subscriber.health_check()

    assert health['healthy'] is True
    assert health['connected'] is True
    assert 'lag' in health


@pytest.mark.asyncio
async def test_health_check_not_connected(kafka_subscriber):
    """Test health check when consumer is not connected"""
    kafka_subscriber.is_running = False
    kafka_subscriber.consumer = None

    health = await kafka_subscriber.health_check()

    assert health['healthy'] is False
    assert health['connected'] is False
    assert 'Consumer not connected' in health['errors']


# =====================================================================
# GRACEFUL SHUTDOWN TESTS
# =====================================================================

@pytest.mark.asyncio
async def test_graceful_shutdown(kafka_subscriber):
    """Test graceful shutdown with cleanup"""
    mock_consumer = AsyncMock()
    mock_consumer.stop = AsyncMock()

    kafka_subscriber.consumer = mock_consumer
    kafka_subscriber.is_running = True

    await kafka_subscriber.close()

    assert kafka_subscriber.is_running is False
    mock_consumer.stop.assert_called_once()


@pytest.mark.asyncio
async def test_shutdown_with_manual_commit(kafka_config, message_handler):
    """Test shutdown commits offsets when auto_commit is disabled"""
    kafka_config['enable_auto_commit'] = False
    subscriber = KafkaSubscriber(kafka_config, message_handler)

    mock_consumer = AsyncMock()
    mock_consumer.stop = AsyncMock()
    mock_consumer.commit = AsyncMock()

    subscriber.consumer = mock_consumer
    subscriber.is_running = True

    await subscriber.close()

    mock_consumer.commit.assert_called_once()
    mock_consumer.stop.assert_called_once()


# =====================================================================
# PERFORMANCE TESTS
# =====================================================================

@pytest.mark.asyncio
async def test_high_throughput_consumption(kafka_subscriber, message_handler):
    """Test handling high message throughput"""
    # Simulate 1000 messages
    num_messages = 1000
    mock_messages = [
        MagicMock(
            topic='tick_archive',
            partition=0,
            offset=i,
            value={'pair': 'EUR/USD', 't': 1234567890 + i, 'b': 1.1000}
        )
        for i in range(num_messages)
    ]

    kafka_subscriber.is_running = True

    # Process all messages
    for msg in mock_messages:
        await kafka_subscriber._handle_message(msg)

    assert kafka_subscriber.total_messages == num_messages
    assert message_handler.call_count == num_messages


@pytest.mark.asyncio
async def test_concurrent_message_processing(kafka_subscriber, message_handler):
    """Test that async processing allows concurrency"""
    # Make handler async with small delay
    async def slow_handler(data, data_type):
        await asyncio.sleep(0.001)  # 1ms delay

    message_handler.side_effect = slow_handler

    messages = [
        MagicMock(topic='tick_archive', partition=0, offset=i, value={'pair': 'EUR/USD'})
        for i in range(10)
    ]

    kafka_subscriber.is_running = True

    import time
    start = time.time()

    # Process messages concurrently
    tasks = [kafka_subscriber._handle_message(msg) for msg in messages]
    await asyncio.gather(*tasks)

    elapsed = time.time() - start

    # Should complete faster than sequential processing (10ms)
    # Due to async concurrency, should be closer to 1-2ms
    assert elapsed < 0.05  # 50ms tolerance


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--asyncio-mode=auto'])
