#!/usr/bin/env python3
"""
Heartbeat Logger - Live service logging component for SUHO Trading Platform

For continuous/infinite services that never "complete"
Provides periodic heartbeat logs to prove service is alive and track metrics

Features:
- Periodic heartbeat logging (every N seconds)
- Metrics tracking (total processed, throughput, errors)
- Uptime calculation
- Rate limiting (no spam)
- Auto-calculate items/sec throughput
- Simple API for live services

Usage:
    from central_hub_sdk import HeartbeatLogger

    # Initialize for live service
    heartbeat = HeartbeatLogger(
        service_name="live-collector",
        task_name="WebSocket streaming",
        heartbeat_interval=30  # Log every 30 seconds
    )

    heartbeat.start()

    # In your processing loop
    while True:
        process_tick(tick_data)

        # Update metrics (will auto-log when interval reached)
        heartbeat.update(
            processed_count=1,
            additional_metrics={"symbol": "XAU/USD", "latency_ms": 15}
        )

    # Optional: force log current state
    heartbeat.log_status()
"""

import logging
import time
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class HeartbeatLogger:
    """
    Heartbeat Logger for Live/Infinite Services

    Designed for continuous services that never complete:
    - WebSocket collectors (streaming ticks)
    - Message queue consumers (NATS/Kafka)
    - Continuous aggregators
    - Real-time processors

    Prevents log spam while proving service is alive and healthy.

    Example Output:
        🚀 Starting: WebSocket streaming (live-collector)
        💓 Heartbeat - ⏱️ 30s - ticks: 1,542 (51.4/s) - errors: 0 - symbol: XAU/USD
        💓 Heartbeat - ⏱️ 1m 0s - ticks: 3,124 (52.1/s) - errors: 0 - symbol: EUR/USD
        💓 Heartbeat - ⏱️ 1m 30s - ticks: 4,689 (52.1/s) - errors: 2 - latency: 12ms
    """

    def __init__(
        self,
        service_name: str,
        task_name: str = "Processing",
        heartbeat_interval: int = 30,
        log_level: str = "INFO"
    ):
        """
        Initialize Heartbeat Logger for live service

        Args:
            service_name: Service identifier (e.g., "live-collector", "data-bridge")
            task_name: Human-readable task description (e.g., "WebSocket streaming")
            heartbeat_interval: Seconds between heartbeat logs (default: 30)
            log_level: Logging level (default: INFO)
        """
        self.service_name = service_name
        self.task_name = task_name
        self.heartbeat_interval = heartbeat_interval
        self.log_level = getattr(logging, log_level.upper())

        # State tracking
        self.start_time = None
        self.last_log_time = 0
        self.total_processed = 0
        self.total_errors = 0

        # Rate calculation
        self.last_count = 0
        self.last_rate_time = 0

        # Latest metrics for display
        self.latest_metrics: Dict[str, Any] = {}

    def start(self):
        """Start heartbeat tracking and log initial message"""
        self.start_time = time.time()
        self.last_log_time = self.start_time
        self.last_rate_time = self.start_time

        logger.log(
            self.log_level,
            f"🚀 Starting: {self.task_name} ({self.service_name})"
        )

    def update(
        self,
        processed_count: int = 1,
        error_count: int = 0,
        additional_metrics: Optional[Dict[str, Any]] = None
    ):
        """
        Update metrics and auto-log if heartbeat interval reached

        Call this in your processing loop. Logger will automatically
        decide when to log based on heartbeat_interval.

        Args:
            processed_count: Number of items processed (default: 1)
            error_count: Number of errors (default: 0)
            additional_metrics: Extra metrics to display (e.g., {"symbol": "XAU/USD", "latency_ms": 15})
        """
        # Update counters
        self.total_processed += processed_count
        self.total_errors += error_count

        # Store latest metrics for next log
        if additional_metrics:
            self.latest_metrics = additional_metrics

        current_time = time.time()

        # Check if heartbeat interval reached
        if (current_time - self.last_log_time) >= self.heartbeat_interval:
            self.log_status()
            self.last_log_time = current_time

    def log_status(self):
        """
        Force log current status (useful for manual logging)

        Can be called manually for important events or status checks
        """
        if not self.start_time:
            logger.warning("⚠️ HeartbeatLogger not started - call start() first")
            return

        current_time = time.time()
        elapsed = current_time - self.start_time
        elapsed_str = self._format_duration(elapsed)

        # Calculate throughput (items/second)
        time_delta = current_time - self.last_rate_time
        if time_delta > 0:
            count_delta = self.total_processed - self.last_count
            rate = count_delta / time_delta
        else:
            rate = 0

        # Update for next rate calculation
        self.last_rate_time = current_time
        self.last_count = self.total_processed

        # Build log message
        info_parts = [
            f"⏱️ {elapsed_str}",
            f"processed: {self.total_processed:,} ({rate:.1f}/s)"
        ]

        # Add errors if any
        if self.total_errors > 0:
            info_parts.append(f"errors: {self.total_errors}")

        # Add additional metrics
        if self.latest_metrics:
            for key, value in self.latest_metrics.items():
                # Format large numbers with commas
                if isinstance(value, int) and value > 1000:
                    formatted = f"{value:,}"
                else:
                    formatted = str(value)
                info_parts.append(f"{key}: {formatted}")

        log_msg = " - ".join(info_parts)
        logger.log(self.log_level, f"💓 Heartbeat - {log_msg}")

        # Clear latest metrics after logging
        self.latest_metrics = {}

    def increment(self, count: int = 1):
        """
        Quick increment helper (just count, no auto-log)

        Use this in tight loops where you don't want to check heartbeat
        every iteration. Then call log_status() manually when needed.

        Args:
            count: Number to increment (default: 1)
        """
        self.total_processed += count

    def increment_errors(self, count: int = 1):
        """
        Increment error counter

        Args:
            count: Number of errors to add (default: 1)
        """
        self.total_errors += count

    def _format_duration(self, seconds: float) -> str:
        """
        Format duration in human-readable format

        Examples:
            45 seconds -> "45s"
            125 seconds -> "2m 5s"
            7325 seconds -> "2h 2m"
        """
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"

    def get_stats(self) -> Dict[str, Any]:
        """
        Get current statistics

        Returns:
            Dict with current stats (processed, errors, uptime, rate)
        """
        current_time = time.time()
        elapsed = current_time - self.start_time if self.start_time else 0
        rate = self.total_processed / elapsed if elapsed > 0 else 0

        return {
            'service_name': self.service_name,
            'task_name': self.task_name,
            'total_processed': self.total_processed,
            'total_errors': self.total_errors,
            'uptime_seconds': elapsed,
            'rate_per_second': rate,
            'latest_metrics': self.latest_metrics.copy()
        }

    def reset_counters(self):
        """
        Reset processed/error counters (keep uptime)

        Useful for periodic resets (e.g., daily counter reset)
        """
        logger.info(f"🔄 Resetting counters - Total: {self.total_processed:,}, Errors: {self.total_errors}")
        self.total_processed = 0
        self.total_errors = 0
        self.last_count = 0
