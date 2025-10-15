#!/usr/bin/env python3
"""
Progress Logger - Shared logging component for SUHO Trading Platform

Hybrid approach: Milestone-based + Time-based heartbeat logging
Reduces log spam while ensuring process liveness visibility

Features:
- Log at percentage milestones (25%, 50%, 75%, 100%)
- Force log every N seconds (heartbeat) if no milestone
- Anti-spam protection (minimum interval between logs)
- Auto-detect stuck/hang processes
- ETA calculation
- Consistent format across all services

Usage:
    from central_hub_sdk import ProgressLogger

    progress = ProgressLogger(
        task_name="Downloading XAU/USD gaps",
        total_items=40,
        service_name="historical-downloader",
        milestones=[25, 50, 75, 100],
        heartbeat_interval=30
    )

    progress.start()

    for i, chunk in enumerate(chunks):
        process_chunk(chunk)
        progress.update(current=i+1, additional_info={"bars": bar_count})

    progress.complete(summary={"total_bars": 3_500_000})
"""

import logging
import time
from datetime import datetime
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)


class ProgressLogger:
    """
    Hybrid Progress Logger: Milestone + Time-Based Heartbeat

    Prevents log spam while proving process is alive:
    - Logs at milestones (25%, 50%, 75%, 100%) with 📊 emoji
    - Force logs every N seconds (heartbeat) with 💓 emoji
    - Detects stuck processes (same progress for too long)
    - Calculates ETA based on current progress

    Example Output:
        📥 Starting: Downloading XAU/USD gaps (40 items)
        📊 25% complete (10/40 items) - ⏱️ 45s - ETA: 2m 15s - bars: 860,246
        💓 Still running: 32% (13/40 items) - ⏱️ 1m 30s - bars: 1,118,198
        📊 50% complete (20/40 items) - ⏱️ 2m 5s - ETA: 2m 5s - bars: 1,720,492
        📊 75% complete (30/40 items) - ⏱️ 3m 10s - ETA: 1m 3s - bars: 2,580,738
        ✅ 100% complete (40/40 items) - ⏱️ 4m 15s - bars: 3,440,984
    """

    def __init__(
        self,
        task_name: str,
        total_items: int,
        service_name: str = "unknown",
        milestones: Optional[List[int]] = None,
        heartbeat_interval: int = 30,
        min_log_interval: int = 10,
        log_level: str = "INFO"
    ):
        """
        Initialize Hybrid Progress Logger

        Args:
            task_name: Human-readable task description (e.g., "Downloading XAU/USD gaps")
            total_items: Total number of items to process (e.g., 40 chunks)
            service_name: Service identifier for context
            milestones: Percentage points to log at (default: [25, 50, 75, 100])
            heartbeat_interval: Force log every N seconds if no milestone (default: 30)
            min_log_interval: Minimum seconds between logs to prevent spam (default: 10)
            log_level: Logging level (default: INFO)
        """
        self.task_name = task_name
        self.total_items = total_items
        self.service_name = service_name
        self.milestones = milestones or [25, 50, 75, 100]
        self.heartbeat_interval = heartbeat_interval
        self.min_log_interval = min_log_interval
        self.log_level = getattr(logging, log_level.upper())

        # State tracking
        self.current_item = 0
        self.start_time = None
        self.last_log_time = 0
        self.last_logged_percentage = 0
        self.last_logged_item = 0
        self.completed = False

        # Stuck detection
        self.stuck_threshold = heartbeat_interval * 3  # 3x heartbeat = likely stuck
        self.stuck_warning_shown = False

    def start(self):
        """Start progress tracking and log initial message"""
        self.start_time = time.time()
        self.last_log_time = self.start_time

        logger.log(
            self.log_level,
            f"📥 Starting: {self.task_name} ({self.total_items} items)"
        )

    def update(self, current: int, additional_info: Optional[Dict[str, Any]] = None):
        """
        Update progress and log if needed (milestone or heartbeat)

        This method intelligently decides when to log:
        1. At milestones (25%, 50%, 75%, 100%)
        2. Every heartbeat_interval seconds if no milestone
        3. Respects min_log_interval to prevent spam
        4. Detects stuck processes

        Args:
            current: Current item count (1-indexed, e.g., 10 out of 40)
            additional_info: Extra info to log (e.g., {"bars": 860246, "errors": 0})
        """
        self.current_item = current
        current_time = time.time()
        current_percentage = int((current / self.total_items) * 100)

        # Determine if should log
        should_log = False
        log_type = None

        # Check 1: Milestone reached?
        if self._check_milestone(current_percentage):
            should_log = True
            log_type = "milestone"

        # Check 2: Heartbeat timeout? (force log if too long since last log)
        elif (current_time - self.last_log_time) >= self.heartbeat_interval:
            should_log = True
            log_type = "heartbeat"

        # Check 3: Anti-spam protection
        if should_log and (current_time - self.last_log_time) < self.min_log_interval:
            # Too soon since last log, skip
            should_log = False

        # Log if needed
        if should_log:
            self._log_progress(current_percentage, log_type, additional_info)
            self.last_log_time = current_time
            self.last_logged_percentage = current_percentage
            self.last_logged_item = current

        # Check 4: Stuck detection (no progress for too long)
        self._check_stuck(current_time)

    def _check_milestone(self, current_pct: int) -> bool:
        """Check if current percentage crosses a milestone"""
        for milestone in self.milestones:
            if self.last_logged_percentage < milestone <= current_pct:
                return True
        return False

    def _check_stuck(self, current_time: float):
        """
        Detect if process is stuck (same item for too long)

        Warns if no progress for 3x heartbeat interval
        """
        if self.stuck_warning_shown:
            return

        time_on_same_item = current_time - self.last_log_time
        no_progress = self.current_item == self.last_logged_item

        if no_progress and time_on_same_item >= self.stuck_threshold:
            logger.warning(
                f"⚠️ WARNING: No progress for {int(time_on_same_item)}s "
                f"- possible hang at item {self.current_item}/{self.total_items}"
            )
            self.stuck_warning_shown = True

    def _log_progress(
        self,
        percentage: int,
        log_type: str,
        additional_info: Optional[Dict] = None
    ):
        """
        Log progress with appropriate emoji based on type

        Args:
            percentage: Current percentage (0-100)
            log_type: "milestone" or "heartbeat"
            additional_info: Extra info to append to log
        """
        elapsed = time.time() - self.start_time
        elapsed_str = self._format_duration(elapsed)

        # Calculate ETA (simple linear extrapolation)
        if percentage > 0 and percentage < 100:
            total_estimated = (elapsed / percentage) * 100
            remaining = total_estimated - elapsed
            eta_str = self._format_duration(remaining)
        else:
            eta_str = None

        # Choose emoji and status based on log type
        if percentage == 100:
            emoji = "✅"
            status = "complete"
        elif log_type == "milestone":
            emoji = "📊"
            status = f"{percentage}% complete"
        else:  # heartbeat
            emoji = "💓"
            status = f"Still running: {percentage}%"

        # Build log message
        info_parts = [
            status,
            f"({self.current_item}/{self.total_items} items)",
            f"⏱️ {elapsed_str}"
        ]

        # Add ETA only if not 100%
        if eta_str:
            info_parts.append(f"ETA: {eta_str}")

        # Add additional info
        if additional_info:
            for key, value in additional_info.items():
                # Format large numbers with commas
                if isinstance(value, int) and value > 1000:
                    formatted = f"{value:,}"
                else:
                    formatted = str(value)
                info_parts.append(f"{key}: {formatted}")

        log_msg = " - ".join(info_parts)
        logger.log(self.log_level, f"{emoji} {log_msg}")

        # Reset stuck warning if progress made
        if self.current_item > self.last_logged_item:
            self.stuck_warning_shown = False

    def complete(self, summary: Optional[Dict[str, Any]] = None):
        """
        Mark task as complete and log final summary

        Args:
            summary: Final summary info (e.g., {"total_bars": 3500000, "errors": 0})
        """
        if self.completed:
            return

        self.completed = True

        # Force log 100% if not already logged
        if self.last_logged_percentage < 100:
            self._log_progress(100, "milestone", summary)
        else:
            # Just log final summary
            elapsed = time.time() - self.start_time
            elapsed_str = self._format_duration(elapsed)

            summary_parts = [f"⏱️ Total time: {elapsed_str}"]
            if summary:
                for key, value in summary.items():
                    if isinstance(value, int) and value > 1000:
                        formatted = f"{value:,}"
                    else:
                        formatted = str(value)
                    summary_parts.append(f"{key}: {formatted}")

            logger.log(
                self.log_level,
                f"✅ {self.task_name} complete - {' - '.join(summary_parts)}"
            )

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
        Get current progress statistics

        Returns:
            Dict with current progress info
        """
        return {
            'task_name': self.task_name,
            'current_item': self.current_item,
            'total_items': self.total_items,
            'percentage': int((self.current_item / self.total_items) * 100) if self.total_items > 0 else 0,
            'elapsed_seconds': time.time() - self.start_time if self.start_time else 0,
            'completed': self.completed
        }
