"""
Standard Request Tracing untuk semua services
Menyediakan consistent tracing patterns untuk performance monitoring
"""

import time
import uuid
import logging
from typing import Any, Dict, Optional, List, ContextManager
from dataclasses import dataclass, field, asdict
from datetime import datetime
from contextlib import contextmanager
import asyncio
from collections import defaultdict


@dataclass
class TraceSpan:
    """Individual trace span"""
    span_id: str
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    parent_span_id: Optional[str] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    success: bool = True

    def finish(self):
        """Finish the span and calculate duration"""
        if self.end_time is None:
            self.end_time = time.time()
            self.duration_ms = (self.end_time - self.start_time) * 1000

    def add_tag(self, key: str, value: Any):
        """Add tag to span"""
        self.tags[key] = value

    def add_log(self, message: str, level: str = "info", **kwargs):
        """Add log entry to span"""
        log_entry = {
            "timestamp": time.time(),
            "level": level,
            "message": message,
            **kwargs
        }
        self.logs.append(log_entry)

    def add_error(self, error: str):
        """Add error to span"""
        self.errors.append(error)
        self.success = False


@dataclass
class TraceContext:
    """Complete trace context for a request"""
    trace_id: str
    correlation_id: str
    service_name: str
    start_time: float
    spans: Dict[str, TraceSpan] = field(default_factory=dict)
    root_span_id: Optional[str] = None
    current_span_id: Optional[str] = None
    user_id: Optional[str] = None
    company_id: Optional[str] = None
    request_metadata: Dict[str, Any] = field(default_factory=dict)

    def get_duration_ms(self) -> float:
        """Get total trace duration"""
        if self.root_span_id and self.root_span_id in self.spans:
            root_span = self.spans[self.root_span_id]
            if root_span.duration_ms:
                return root_span.duration_ms
        return (time.time() - self.start_time) * 1000

    def get_span_count(self) -> int:
        """Get total number of spans"""
        return len(self.spans)

    def has_errors(self) -> bool:
        """Check if trace has any errors"""
        return any(not span.success for span in self.spans.values())

    def get_all_errors(self) -> List[str]:
        """Get all errors from all spans"""
        errors = []
        for span in self.spans.values():
            errors.extend(span.errors)
        return errors


class RequestTracer:
    """
    Standard request tracer untuk semua services
    Menyediakan distributed tracing dengan sampling dan performance monitoring
    """

    def __init__(self, service_name: str, sampling_rate: float = 0.1):
        self.service_name = service_name
        self.sampling_rate = sampling_rate
        self.active_traces: Dict[str, TraceContext] = {}
        self.completed_traces: List[TraceContext] = []
        self.max_completed_traces = 1000
        self.logger = logging.getLogger(f"{service_name}.tracer")

        # Performance metrics
        self.operation_metrics = defaultdict(list)
        self.error_counts = defaultdict(int)

    def should_trace(self, correlation_id: Optional[str] = None, force: bool = False) -> bool:
        """Determine if request should be traced"""
        if force:
            return True

        if correlation_id and correlation_id in self.active_traces:
            return True

        # Sample based on sampling rate
        return hash(correlation_id or uuid.uuid4().hex) % 1000 < (self.sampling_rate * 1000)

    def start_trace(self,
                   operation_name: str,
                   correlation_id: Optional[str] = None,
                   user_id: Optional[str] = None,
                   company_id: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> TraceContext:
        """Start a new trace"""
        trace_id = str(uuid.uuid4())
        correlation_id = correlation_id or str(uuid.uuid4())

        trace_context = TraceContext(
            trace_id=trace_id,
            correlation_id=correlation_id,
            service_name=self.service_name,
            start_time=time.time(),
            user_id=user_id,
            company_id=company_id,
            request_metadata=metadata or {}
        )

        # Create root span
        root_span = self.start_span(operation_name, trace_context)
        trace_context.root_span_id = root_span.span_id

        self.active_traces[correlation_id] = trace_context

        self.logger.debug(f"Started trace {trace_id} for operation {operation_name}")
        return trace_context

    def start_span(self,
                  operation_name: str,
                  trace_context: TraceContext,
                  parent_span_id: Optional[str] = None,
                  tags: Optional[Dict[str, Any]] = None) -> TraceSpan:
        """Start a new span within a trace"""
        span_id = str(uuid.uuid4())

        span = TraceSpan(
            span_id=span_id,
            operation_name=operation_name,
            start_time=time.time(),
            parent_span_id=parent_span_id or trace_context.current_span_id,
            tags=tags or {}
        )

        # Add service tag
        span.add_tag("service.name", self.service_name)

        # Add user context tags if available
        if trace_context.user_id:
            span.add_tag("user.id", trace_context.user_id)
        if trace_context.company_id:
            span.add_tag("company.id", trace_context.company_id)

        trace_context.spans[span_id] = span
        trace_context.current_span_id = span_id

        return span

    def finish_span(self, span_id: str, trace_context: TraceContext):
        """Finish a span"""
        if span_id in trace_context.spans:
            span = trace_context.spans[span_id]
            span.finish()

            # Update operation metrics
            self.operation_metrics[span.operation_name].append(span.duration_ms)

            # Update error counts
            if not span.success:
                self.error_counts[span.operation_name] += 1

            self.logger.debug(f"Finished span {span_id} ({span.operation_name}) in {span.duration_ms:.2f}ms")

    def finish_trace(self, correlation_id: str):
        """Finish a trace"""
        if correlation_id in self.active_traces:
            trace_context = self.active_traces[correlation_id]

            # Finish all unfinished spans
            for span in trace_context.spans.values():
                if span.end_time is None:
                    span.finish()

            # Move to completed traces
            self.completed_traces.append(trace_context)

            # Limit completed traces to prevent memory issues
            if len(self.completed_traces) > self.max_completed_traces:
                self.completed_traces.pop(0)

            # Remove from active traces
            del self.active_traces[correlation_id]

            total_duration = trace_context.get_duration_ms()
            span_count = trace_context.get_span_count()
            has_errors = trace_context.has_errors()

            self.logger.info(f"Finished trace {trace_context.trace_id} in {total_duration:.2f}ms with {span_count} spans (errors: {has_errors})")

    @contextmanager
    def trace(self, operation_name: str, correlation_id: Optional[str] = None, **kwargs):
        """Context manager for tracing operations"""
        if not self.should_trace(correlation_id):
            yield None
            return

        trace_context = None
        span = None

        try:
            # Get or create trace context
            if correlation_id and correlation_id in self.active_traces:
                trace_context = self.active_traces[correlation_id]
                span = self.start_span(operation_name, trace_context)
            else:
                trace_context = self.start_trace(operation_name, correlation_id, **kwargs)
                span = trace_context.spans[trace_context.root_span_id]

            yield span

        except Exception as e:
            if span:
                span.add_error(str(e))
            raise

        finally:
            if span and trace_context:
                self.finish_span(span.span_id, trace_context)

                # If this is the root span, finish the trace
                if span.span_id == trace_context.root_span_id:
                    self.finish_trace(trace_context.correlation_id)

    def add_error(self, correlation_id: str, error: str):
        """Add error to current trace"""
        if correlation_id in self.active_traces:
            trace_context = self.active_traces[correlation_id]
            if trace_context.current_span_id:
                current_span = trace_context.spans[trace_context.current_span_id]
                current_span.add_error(error)

    def add_tag(self, correlation_id: str, key: str, value: Any):
        """Add tag to current span"""
        if correlation_id in self.active_traces:
            trace_context = self.active_traces[correlation_id]
            if trace_context.current_span_id:
                current_span = trace_context.spans[trace_context.current_span_id]
                current_span.add_tag(key, value)

    def add_log(self, correlation_id: str, message: str, level: str = "info", **kwargs):
        """Add log to current span"""
        if correlation_id in self.active_traces:
            trace_context = self.active_traces[correlation_id]
            if trace_context.current_span_id:
                current_span = trace_context.spans[trace_context.current_span_id]
                current_span.add_log(message, level, **kwargs)

    def get_trace(self, correlation_id: str) -> Optional[TraceContext]:
        """Get active trace by correlation ID"""
        return self.active_traces.get(correlation_id)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for all operations"""
        metrics = {}

        for operation, durations in self.operation_metrics.items():
            if durations:
                metrics[operation] = {
                    "count": len(durations),
                    "avg_duration_ms": sum(durations) / len(durations),
                    "min_duration_ms": min(durations),
                    "max_duration_ms": max(durations),
                    "p95_duration_ms": self._percentile(durations, 95),
                    "p99_duration_ms": self._percentile(durations, 99),
                    "error_count": self.error_counts.get(operation, 0),
                    "error_rate": self.error_counts.get(operation, 0) / len(durations)
                }

        return {
            "operations": metrics,
            "active_traces": len(self.active_traces),
            "completed_traces": len(self.completed_traces),
            "sampling_rate": self.sampling_rate
        }

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0.0

        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        if index >= len(sorted_data):
            index = len(sorted_data) - 1

        return sorted_data[index]

    def clear_metrics(self):
        """Clear performance metrics"""
        self.operation_metrics.clear()
        self.error_counts.clear()
        self.completed_traces.clear()

    def export_traces(self, correlation_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Export traces for external systems (Jaeger, Zipkin, etc.)"""
        traces_to_export = []

        # Export active traces
        for correlation_id, trace_context in self.active_traces.items():
            if correlation_ids is None or correlation_id in correlation_ids:
                traces_to_export.append(self._trace_to_dict(trace_context))

        # Export completed traces
        for trace_context in self.completed_traces:
            if correlation_ids is None or trace_context.correlation_id in correlation_ids:
                traces_to_export.append(self._trace_to_dict(trace_context))

        return traces_to_export

    def _trace_to_dict(self, trace_context: TraceContext) -> Dict[str, Any]:
        """Convert trace context to dictionary for export"""
        return {
            "trace_id": trace_context.trace_id,
            "correlation_id": trace_context.correlation_id,
            "service_name": trace_context.service_name,
            "start_time": trace_context.start_time,
            "duration_ms": trace_context.get_duration_ms(),
            "span_count": trace_context.get_span_count(),
            "has_errors": trace_context.has_errors(),
            "user_id": trace_context.user_id,
            "company_id": trace_context.company_id,
            "metadata": trace_context.request_metadata,
            "spans": [asdict(span) for span in trace_context.spans.values()]
        }