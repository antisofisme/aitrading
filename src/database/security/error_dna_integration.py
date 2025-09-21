"""
ErrorDNA Integration for Intelligent Error Tracking
Phase 1 Infrastructure Migration

Integrates with ErrorDNA system for:
- Intelligent error classification and pattern recognition
- Automatic error correlation and root cause analysis
- Proactive error prediction and prevention
- Integration with database security and audit logging
- ML-enhanced error diagnostics
"""

import asyncio
import logging
import json
import hashlib
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, Counter
import threading
import time

from .connection_pooling import DatabaseManager
from .security.database_security import SecurityEventLogger, SecurityEvent

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories for classification."""
    DATABASE = "database"
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    SECURITY = "security"
    UNKNOWN = "unknown"

class ErrorStatus(Enum):
    """Error resolution status."""
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    IGNORED = "ignored"

@dataclass
class ErrorPattern:
    """Error pattern for recognition and classification."""
    pattern_id: str
    name: str
    description: str
    regex_patterns: List[str]
    category: ErrorCategory
    severity: ErrorSeverity
    suggested_actions: List[str]
    related_components: List[str]
    confidence_threshold: float = 0.8

@dataclass
class ErrorEvent:
    """Comprehensive error event data."""
    error_id: str
    timestamp: datetime
    service_name: str
    component: str
    error_message: str
    stack_trace: Optional[str]
    context: Dict[str, Any]

    # Classification
    category: ErrorCategory
    severity: ErrorSeverity
    pattern_id: Optional[str]
    confidence_score: float

    # Metadata
    user_id: Optional[str]
    session_id: Optional[str]
    request_id: Optional[str]
    ip_address: Optional[str]

    # Analysis
    root_cause: Optional[str]
    related_errors: List[str]
    resolution_suggestions: List[str]

    # Status tracking
    status: ErrorStatus
    assigned_to: Optional[str]
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]

@dataclass
class ErrorCluster:
    """Group of related errors for analysis."""
    cluster_id: str
    pattern_id: str
    error_count: int
    first_occurrence: datetime
    last_occurrence: datetime
    affected_users: Set[str]
    affected_components: Set[str]
    trend_analysis: Dict[str, Any]
    severity_distribution: Dict[ErrorSeverity, int]

class ErrorPatternLibrary:
    """Library of error patterns for intelligent classification."""

    def __init__(self):
        self.patterns: Dict[str, ErrorPattern] = {}
        self._load_default_patterns()

    def _load_default_patterns(self):
        """Load default error patterns."""
        patterns = [
            # Database errors
            ErrorPattern(
                pattern_id="db_connection_timeout",
                name="Database Connection Timeout",
                description="Database connection timeout or unavailable",
                regex_patterns=[
                    r"connection.*timeout",
                    r"database.*unavailable",
                    r"connection.*refused",
                    r"timeout.*waiting.*connection"
                ],
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.HIGH,
                suggested_actions=[
                    "Check database server status",
                    "Verify network connectivity",
                    "Review connection pool configuration",
                    "Check for database locks or high load"
                ],
                related_components=["database", "connection_pool", "network"]
            ),

            ErrorPattern(
                pattern_id="db_deadlock",
                name="Database Deadlock",
                description="Database deadlock detected",
                regex_patterns=[
                    r"deadlock.*detected",
                    r"lock.*timeout",
                    r"deadlock.*victim",
                    r"transaction.*rollback.*deadlock"
                ],
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.MEDIUM,
                suggested_actions=[
                    "Review transaction ordering",
                    "Optimize query performance",
                    "Consider transaction isolation levels",
                    "Implement retry logic"
                ],
                related_components=["database", "transactions", "queries"]
            ),

            # Authentication errors
            ErrorPattern(
                pattern_id="auth_invalid_token",
                name="Invalid Authentication Token",
                description="JWT token validation failed",
                regex_patterns=[
                    r"invalid.*token",
                    r"token.*expired",
                    r"token.*malformed",
                    r"signature.*verification.*failed"
                ],
                category=ErrorCategory.AUTHENTICATION,
                severity=ErrorSeverity.MEDIUM,
                suggested_actions=[
                    "Check token expiration",
                    "Verify token signature",
                    "Review token generation logic",
                    "Check client clock synchronization"
                ],
                related_components=["authentication", "jwt", "security"]
            ),

            # Network errors
            ErrorPattern(
                pattern_id="network_timeout",
                name="Network Request Timeout",
                description="Network request timeout or connectivity issue",
                regex_patterns=[
                    r"network.*timeout",
                    r"connection.*reset",
                    r"no.*route.*host",
                    r"network.*unreachable"
                ],
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                suggested_actions=[
                    "Check network connectivity",
                    "Verify firewall rules",
                    "Review timeout configurations",
                    "Check external service status"
                ],
                related_components=["network", "external_services", "firewall"]
            ),

            # Security errors
            ErrorPattern(
                pattern_id="security_unauthorized_access",
                name="Unauthorized Access Attempt",
                description="Attempt to access restricted resource",
                regex_patterns=[
                    r"unauthorized.*access",
                    r"access.*denied",
                    r"permission.*denied",
                    r"forbidden.*resource"
                ],
                category=ErrorCategory.SECURITY,
                severity=ErrorSeverity.HIGH,
                suggested_actions=[
                    "Review access permissions",
                    "Check user roles and privileges",
                    "Audit security policies",
                    "Monitor for potential security threats"
                ],
                related_components=["security", "authorization", "access_control"]
            ),

            # Trading-specific errors
            ErrorPattern(
                pattern_id="trading_account_invalid",
                name="Invalid Trading Account",
                description="Trading account validation failed",
                regex_patterns=[
                    r"invalid.*trading.*account",
                    r"account.*not.*found",
                    r"account.*suspended",
                    r"insufficient.*funds"
                ],
                category=ErrorCategory.BUSINESS_LOGIC,
                severity=ErrorSeverity.HIGH,
                suggested_actions=[
                    "Verify account credentials",
                    "Check account status",
                    "Review account permissions",
                    "Contact account administrator"
                ],
                related_components=["trading", "accounts", "validation"]
            ),

            # ML/AI errors
            ErrorPattern(
                pattern_id="ml_model_error",
                name="ML Model Prediction Error",
                description="Machine learning model prediction failed",
                regex_patterns=[
                    r"model.*prediction.*failed",
                    r"ml.*inference.*error",
                    r"invalid.*model.*input",
                    r"model.*not.*loaded"
                ],
                category=ErrorCategory.BUSINESS_LOGIC,
                severity=ErrorSeverity.MEDIUM,
                suggested_actions=[
                    "Check model availability",
                    "Validate input data format",
                    "Review model health status",
                    "Fallback to default predictions"
                ],
                related_components=["ml_models", "ai_engine", "predictions"]
            )
        ]

        for pattern in patterns:
            self.patterns[pattern.pattern_id] = pattern

    def classify_error(self, error_message: str, stack_trace: str = None,
                      context: Dict[str, Any] = None) -> Tuple[Optional[ErrorPattern], float]:
        """Classify error using pattern matching."""
        text_to_analyze = error_message.lower()
        if stack_trace:
            text_to_analyze += " " + stack_trace.lower()
        if context:
            text_to_analyze += " " + json.dumps(context).lower()

        best_match = None
        best_score = 0.0

        for pattern in self.patterns.values():
            score = self._calculate_pattern_score(text_to_analyze, pattern)
            if score > best_score and score >= pattern.confidence_threshold:
                best_score = score
                best_match = pattern

        return best_match, best_score

    def _calculate_pattern_score(self, text: str, pattern: ErrorPattern) -> float:
        """Calculate pattern matching score."""
        scores = []

        for regex_pattern in pattern.regex_patterns:
            try:
                matches = re.findall(regex_pattern, text, re.IGNORECASE)
                if matches:
                    # Score based on number of matches and pattern complexity
                    score = min(len(matches) * 0.3, 1.0)
                    scores.append(score)
            except re.error:
                continue

        return max(scores) if scores else 0.0

    def add_pattern(self, pattern: ErrorPattern):
        """Add new error pattern to library."""
        self.patterns[pattern.pattern_id] = pattern

    def update_pattern(self, pattern_id: str, updates: Dict[str, Any]):
        """Update existing error pattern."""
        if pattern_id in self.patterns:
            pattern = self.patterns[pattern_id]
            for key, value in updates.items():
                if hasattr(pattern, key):
                    setattr(pattern, key, value)

class ErrorAnalyzer:
    """Advanced error analysis and correlation engine."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.pattern_library = ErrorPatternLibrary()
        self.error_clusters: Dict[str, ErrorCluster] = {}
        self.correlation_cache: Dict[str, List[str]] = {}
        self._lock = threading.Lock()

    async def analyze_error(self, raw_error: Dict[str, Any]) -> ErrorEvent:
        """Analyze and classify error event."""
        try:
            # Generate error ID
            error_id = self._generate_error_id(raw_error)

            # Extract error details
            error_message = raw_error.get('message', '')
            stack_trace = raw_error.get('stack_trace', '')
            context = raw_error.get('context', {})

            # Classify error using pattern library
            pattern, confidence = self.pattern_library.classify_error(
                error_message, stack_trace, context
            )

            # Determine category and severity
            category = pattern.category if pattern else ErrorCategory.UNKNOWN
            severity = pattern.severity if pattern else ErrorSeverity.MEDIUM

            # Create error event
            error_event = ErrorEvent(
                error_id=error_id,
                timestamp=datetime.fromisoformat(raw_error.get('timestamp', datetime.now().isoformat())),
                service_name=raw_error.get('service_name', 'unknown'),
                component=raw_error.get('component', 'unknown'),
                error_message=error_message,
                stack_trace=stack_trace,
                context=context,
                category=category,
                severity=severity,
                pattern_id=pattern.pattern_id if pattern else None,
                confidence_score=confidence,
                user_id=raw_error.get('user_id'),
                session_id=raw_error.get('session_id'),
                request_id=raw_error.get('request_id'),
                ip_address=raw_error.get('ip_address'),
                root_cause=None,
                related_errors=[],
                resolution_suggestions=pattern.suggested_actions if pattern else [],
                status=ErrorStatus.NEW,
                assigned_to=None,
                resolved_at=None,
                resolution_notes=None
            )

            # Perform correlation analysis
            await self._correlate_error(error_event)

            # Update error clusters
            await self._update_clusters(error_event)

            # Store error event
            await self._store_error_event(error_event)

            return error_event

        except Exception as e:
            logger.error(f"Error analysis failed: {e}")
            raise

    def _generate_error_id(self, raw_error: Dict[str, Any]) -> str:
        """Generate unique error ID based on error content."""
        content = f"{raw_error.get('service_name', '')}{raw_error.get('message', '')}{raw_error.get('timestamp', '')}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    async def _correlate_error(self, error_event: ErrorEvent):
        """Find related errors using correlation analysis."""
        try:
            # Look for errors with similar patterns
            similar_errors = await self._find_similar_errors(error_event)
            error_event.related_errors = [e['error_id'] for e in similar_errors[:5]]

            # Analyze root cause based on correlation
            if similar_errors:
                error_event.root_cause = await self._determine_root_cause(error_event, similar_errors)

        except Exception as e:
            logger.error(f"Error correlation failed: {e}")

    async def _find_similar_errors(self, error_event: ErrorEvent) -> List[Dict[str, Any]]:
        """Find errors similar to the current error."""
        try:
            # Query recent errors with same pattern or category
            query = """
            SELECT error_id, error_message, category, severity, timestamp, context
            FROM error_events
            WHERE (pattern_id = $1 OR category = $2)
            AND timestamp > $3
            AND error_id != $4
            ORDER BY timestamp DESC
            LIMIT 20
            """

            recent_time = error_event.timestamp - timedelta(hours=24)

            results = await self.db_manager.postgresql.execute_query(
                query,
                error_event.pattern_id,
                error_event.category.value,
                recent_time,
                error_event.error_id
            )

            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Failed to find similar errors: {e}")
            return []

    async def _determine_root_cause(self, error_event: ErrorEvent,
                                  similar_errors: List[Dict[str, Any]]) -> Optional[str]:
        """Determine potential root cause based on error patterns."""
        try:
            # Analyze error frequency and timing
            error_times = [datetime.fromisoformat(e['timestamp']) for e in similar_errors]
            error_times.append(error_event.timestamp)

            # Check if errors are clustered in time (potential system issue)
            time_diffs = [abs((t1 - t2).total_seconds()) for t1, t2 in zip(error_times[:-1], error_times[1:])]
            avg_time_diff = sum(time_diffs) / len(time_diffs) if time_diffs else 0

            if avg_time_diff < 300:  # Errors within 5 minutes
                return "Potential system-wide issue - errors clustered in time"

            # Check for common context patterns
            context_patterns = defaultdict(int)
            for error in similar_errors:
                context = json.loads(error.get('context', '{}'))
                for key, value in context.items():
                    context_patterns[f"{key}:{value}"] += 1

            if context_patterns:
                most_common = max(context_patterns.items(), key=lambda x: x[1])
                if most_common[1] >= len(similar_errors) * 0.5:
                    return f"Common context pattern: {most_common[0]}"

            # Check component-specific issues
            component_counter = Counter([e.get('component', 'unknown') for e in similar_errors])
            if component_counter:
                most_affected = component_counter.most_common(1)[0]
                if most_affected[1] >= len(similar_errors) * 0.7:
                    return f"Component-specific issue: {most_affected[0]}"

            return None

        except Exception as e:
            logger.error(f"Root cause analysis failed: {e}")
            return None

    async def _update_clusters(self, error_event: ErrorEvent):
        """Update error clusters for trend analysis."""
        try:
            with self._lock:
                cluster_key = f"{error_event.pattern_id or error_event.category.value}_{error_event.component}"

                if cluster_key not in self.error_clusters:
                    self.error_clusters[cluster_key] = ErrorCluster(
                        cluster_id=cluster_key,
                        pattern_id=error_event.pattern_id or error_event.category.value,
                        error_count=0,
                        first_occurrence=error_event.timestamp,
                        last_occurrence=error_event.timestamp,
                        affected_users=set(),
                        affected_components=set(),
                        trend_analysis={},
                        severity_distribution=defaultdict(int)
                    )

                cluster = self.error_clusters[cluster_key]
                cluster.error_count += 1
                cluster.last_occurrence = error_event.timestamp
                cluster.severity_distribution[error_event.severity] += 1

                if error_event.user_id:
                    cluster.affected_users.add(error_event.user_id)
                cluster.affected_components.add(error_event.component)

                # Update trend analysis
                hour_key = error_event.timestamp.strftime('%Y-%m-%d %H:00')
                if 'hourly_counts' not in cluster.trend_analysis:
                    cluster.trend_analysis['hourly_counts'] = defaultdict(int)
                cluster.trend_analysis['hourly_counts'][hour_key] += 1

        except Exception as e:
            logger.error(f"Cluster update failed: {e}")

    async def _store_error_event(self, error_event: ErrorEvent):
        """Store error event in database."""
        try:
            query = """
            INSERT INTO error_events (
                error_id, timestamp, service_name, component, error_message,
                stack_trace, context, category, severity, pattern_id,
                confidence_score, user_id, session_id, request_id, ip_address,
                root_cause, related_errors, resolution_suggestions, status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
            ON CONFLICT (error_id) DO UPDATE SET
                root_cause = EXCLUDED.root_cause,
                related_errors = EXCLUDED.related_errors
            """

            await self.db_manager.postgresql.execute_query(
                query,
                error_event.error_id,
                error_event.timestamp,
                error_event.service_name,
                error_event.component,
                error_event.error_message,
                error_event.stack_trace,
                json.dumps(error_event.context),
                error_event.category.value,
                error_event.severity.value,
                error_event.pattern_id,
                error_event.confidence_score,
                error_event.user_id,
                error_event.session_id,
                error_event.request_id,
                error_event.ip_address,
                error_event.root_cause,
                json.dumps(error_event.related_errors),
                json.dumps(error_event.resolution_suggestions),
                error_event.status.value
            )

        except Exception as e:
            logger.error(f"Failed to store error event: {e}")

    async def get_error_statistics(self, time_range: timedelta = None) -> Dict[str, Any]:
        """Get error statistics and trends."""
        try:
            if not time_range:
                time_range = timedelta(days=7)

            start_time = datetime.now() - time_range

            # Get error counts by category and severity
            stats_query = """
            SELECT
                category,
                severity,
                COUNT(*) as error_count,
                COUNT(DISTINCT user_id) as affected_users,
                COUNT(DISTINCT component) as affected_components
            FROM error_events
            WHERE timestamp >= $1
            GROUP BY category, severity
            ORDER BY error_count DESC
            """

            stats_results = await self.db_manager.postgresql.execute_query(stats_query, start_time)

            # Get trending errors
            trending_query = """
            SELECT
                pattern_id,
                category,
                COUNT(*) as occurrence_count,
                AVG(confidence_score) as avg_confidence,
                MAX(timestamp) as last_occurrence
            FROM error_events
            WHERE timestamp >= $1 AND pattern_id IS NOT NULL
            GROUP BY pattern_id, category
            HAVING COUNT(*) >= 5
            ORDER BY occurrence_count DESC
            LIMIT 10
            """

            trending_results = await self.db_manager.postgresql.execute_query(trending_query, start_time)

            # Get resolution statistics
            resolution_query = """
            SELECT
                status,
                COUNT(*) as count,
                AVG(EXTRACT(EPOCH FROM (resolved_at - timestamp))/3600) as avg_resolution_hours
            FROM error_events
            WHERE timestamp >= $1
            GROUP BY status
            """

            resolution_results = await self.db_manager.postgresql.execute_query(resolution_query, start_time)

            return {
                'time_range': str(time_range),
                'error_statistics': [dict(row) for row in stats_results],
                'trending_errors': [dict(row) for row in trending_results],
                'resolution_statistics': [dict(row) for row in resolution_results],
                'cluster_analysis': self._get_cluster_summary()
            }

        except Exception as e:
            logger.error(f"Failed to get error statistics: {e}")
            return {}

    def _get_cluster_summary(self) -> Dict[str, Any]:
        """Get summary of error clusters."""
        with self._lock:
            if not self.error_clusters:
                return {}

            summary = {
                'total_clusters': len(self.error_clusters),
                'active_clusters': 0,
                'critical_clusters': 0,
                'top_clusters': []
            }

            recent_time = datetime.now() - timedelta(hours=6)

            for cluster in self.error_clusters.values():
                if cluster.last_occurrence > recent_time:
                    summary['active_clusters'] += 1

                if cluster.error_count >= 10 or ErrorSeverity.CRITICAL in cluster.severity_distribution:
                    summary['critical_clusters'] += 1

            # Get top clusters by error count
            top_clusters = sorted(
                self.error_clusters.values(),
                key=lambda x: x.error_count,
                reverse=True
            )[:5]

            summary['top_clusters'] = [
                {
                    'cluster_id': cluster.cluster_id,
                    'error_count': cluster.error_count,
                    'affected_users': len(cluster.affected_users),
                    'affected_components': list(cluster.affected_components),
                    'last_occurrence': cluster.last_occurrence.isoformat()
                }
                for cluster in top_clusters
            ]

            return summary

class ErrorDNAIntegration:
    """Main ErrorDNA integration manager."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.error_analyzer = ErrorAnalyzer(db_manager)
        self.security_logger = SecurityEventLogger(db_manager)

    async def initialize(self):
        """Initialize ErrorDNA integration."""
        try:
            # Create error events table
            await self._create_error_tables()

            # Initialize error analyzer
            await self._load_custom_patterns()

            logger.info("ErrorDNA integration initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize ErrorDNA integration: {e}")
            raise

    async def _create_error_tables(self):
        """Create error tracking tables."""
        try:
            # Error events table
            await self.db_manager.postgresql.execute_query("""
            CREATE TABLE IF NOT EXISTS error_events (
                error_id VARCHAR(32) PRIMARY KEY,
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                service_name VARCHAR(100) NOT NULL,
                component VARCHAR(100) NOT NULL,
                error_message TEXT NOT NULL,
                stack_trace TEXT,
                context JSONB DEFAULT '{}',
                category VARCHAR(50) NOT NULL,
                severity VARCHAR(20) NOT NULL,
                pattern_id VARCHAR(100),
                confidence_score FLOAT DEFAULT 0.0,
                user_id UUID,
                session_id UUID,
                request_id VARCHAR(100),
                ip_address INET,
                root_cause TEXT,
                related_errors JSONB DEFAULT '[]',
                resolution_suggestions JSONB DEFAULT '[]',
                status VARCHAR(20) DEFAULT 'new',
                assigned_to VARCHAR(100),
                resolved_at TIMESTAMP WITH TIME ZONE,
                resolution_notes TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
            """)

            # Error patterns table
            await self.db_manager.postgresql.execute_query("""
            CREATE TABLE IF NOT EXISTS error_patterns (
                pattern_id VARCHAR(100) PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                regex_patterns JSONB NOT NULL,
                category VARCHAR(50) NOT NULL,
                severity VARCHAR(20) NOT NULL,
                suggested_actions JSONB DEFAULT '[]',
                related_components JSONB DEFAULT '[]',
                confidence_threshold FLOAT DEFAULT 0.8,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
            """)

            # Create indexes for performance
            await self.db_manager.postgresql.execute_query("""
            CREATE INDEX IF NOT EXISTS idx_error_events_timestamp ON error_events(timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_error_events_category ON error_events(category);
            CREATE INDEX IF NOT EXISTS idx_error_events_severity ON error_events(severity);
            CREATE INDEX IF NOT EXISTS idx_error_events_pattern ON error_events(pattern_id);
            CREATE INDEX IF NOT EXISTS idx_error_events_user ON error_events(user_id);
            CREATE INDEX IF NOT EXISTS idx_error_events_service ON error_events(service_name);
            """)

        except Exception as e:
            logger.error(f"Failed to create error tables: {e}")
            raise

    async def _load_custom_patterns(self):
        """Load custom error patterns from database."""
        try:
            results = await self.db_manager.postgresql.execute_query("""
            SELECT * FROM error_patterns WHERE is_active = TRUE
            """)

            for row in results:
                pattern = ErrorPattern(
                    pattern_id=row['pattern_id'],
                    name=row['name'],
                    description=row['description'],
                    regex_patterns=row['regex_patterns'],
                    category=ErrorCategory(row['category']),
                    severity=ErrorSeverity(row['severity']),
                    suggested_actions=row['suggested_actions'],
                    related_components=row['related_components'],
                    confidence_threshold=row['confidence_threshold']
                )
                self.error_analyzer.pattern_library.add_pattern(pattern)

        except Exception as e:
            logger.error(f"Failed to load custom patterns: {e}")

    async def report_error(self, error_data: Dict[str, Any]) -> ErrorEvent:
        """Report and analyze error event."""
        try:
            # Analyze error
            error_event = await self.error_analyzer.analyze_error(error_data)

            # Log security event if error is security-related
            if error_event.category == ErrorCategory.SECURITY:
                await self.security_logger.log_security_event(SecurityEvent(
                    event_type="security_error",
                    user_id=error_event.user_id,
                    event_category="error_tracking",
                    severity=error_event.severity.value,
                    description=f"Security error detected: {error_event.error_message}",
                    details={
                        "error_id": error_event.error_id,
                        "component": error_event.component,
                        "pattern_id": error_event.pattern_id,
                        "confidence": error_event.confidence_score
                    },
                    ip_address=error_event.ip_address,
                    is_suspicious=error_event.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]
                ))

            # Store in ClickHouse for analytics
            await self._store_error_analytics(error_event)

            return error_event

        except Exception as e:
            logger.error(f"Error reporting failed: {e}")
            raise

    async def _store_error_analytics(self, error_event: ErrorEvent):
        """Store error event in ClickHouse for analytics."""
        try:
            clickhouse_data = {
                'timestamp': error_event.timestamp,
                'service_name': error_event.service_name,
                'log_level': 'ERROR',
                'user_id': error_event.user_id or '',
                'session_id': error_event.session_id or '',
                'message': f"ErrorDNA: {error_event.error_message}",
                'details': json.dumps({
                    'error_id': error_event.error_id,
                    'category': error_event.category.value,
                    'severity': error_event.severity.value,
                    'pattern_id': error_event.pattern_id,
                    'confidence_score': error_event.confidence_score,
                    'root_cause': error_event.root_cause
                }),
                'context': json.dumps(error_event.context),
                'error_category': error_event.category.value,
                'hostname': error_event.context.get('hostname', ''),
                'process_id': error_event.context.get('process_id', 0),
                'thread_id': error_event.context.get('thread_id', 0)
            }

            await self.db_manager.clickhouse.insert_data('logs_hot', [clickhouse_data])

        except Exception as e:
            logger.error(f"Failed to store error analytics: {e}")

    async def get_error_insights(self, time_range: timedelta = None) -> Dict[str, Any]:
        """Get error insights and recommendations."""
        try:
            insights = await self.error_analyzer.get_error_statistics(time_range)

            # Add proactive recommendations
            insights['recommendations'] = await self._generate_recommendations(insights)

            # Add predictive analysis
            insights['predictions'] = await self._generate_predictions(insights)

            return insights

        except Exception as e:
            logger.error(f"Failed to get error insights: {e}")
            return {}

    async def _generate_recommendations(self, insights: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate proactive recommendations based on error patterns."""
        recommendations = []

        # Analyze trending errors
        for error in insights.get('trending_errors', []):
            if error['occurrence_count'] >= 10:
                recommendations.append({
                    'type': 'pattern_trend',
                    'priority': 'high',
                    'description': f"High frequency error pattern detected: {error['pattern_id']}",
                    'action': 'Investigate root cause and implement preventive measures',
                    'affected_category': error['category']
                })

        # Analyze critical clusters
        cluster_summary = insights.get('cluster_analysis', {})
        if cluster_summary.get('critical_clusters', 0) > 0:
            recommendations.append({
                'type': 'critical_clusters',
                'priority': 'critical',
                'description': f"{cluster_summary['critical_clusters']} critical error clusters detected",
                'action': 'Immediate investigation required for critical error clusters',
                'details': cluster_summary.get('top_clusters', [])
            })

        return recommendations

    async def _generate_predictions(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        """Generate predictive analysis for error trends."""
        predictions = {
            'risk_level': 'low',
            'trend_analysis': {},
            'potential_issues': []
        }

        try:
            # Analyze error trend patterns
            error_stats = insights.get('error_statistics', [])
            total_errors = sum(stat['error_count'] for stat in error_stats)

            if total_errors > 100:
                predictions['risk_level'] = 'medium'
                predictions['potential_issues'].append('High error volume detected')

            critical_errors = sum(
                stat['error_count'] for stat in error_stats
                if stat['severity'] == 'critical'
            )

            if critical_errors > 5:
                predictions['risk_level'] = 'high'
                predictions['potential_issues'].append('Multiple critical errors indicate system instability')

            # Analyze cluster trends
            cluster_summary = insights.get('cluster_analysis', {})
            if cluster_summary.get('active_clusters', 0) > 10:
                predictions['risk_level'] = 'high'
                predictions['potential_issues'].append('High number of active error clusters')

        except Exception as e:
            logger.error(f"Prediction generation failed: {e}")

        return predictions

    async def health_check(self) -> Dict[str, Any]:
        """Perform ErrorDNA integration health check."""
        health = {
            'status': 'healthy',
            'pattern_library': {},
            'error_analysis': {},
            'storage': {}
        }

        try:
            # Check pattern library
            patterns_count = len(self.error_analyzer.pattern_library.patterns)
            health['pattern_library'] = {
                'total_patterns': patterns_count,
                'status': 'healthy' if patterns_count > 0 else 'warning'
            }

            # Check error analysis capability
            test_error = {
                'message': 'test connection timeout error',
                'timestamp': datetime.now().isoformat(),
                'service_name': 'test_service',
                'component': 'test_component',
                'context': {}
            }

            test_result = await self.error_analyzer.analyze_error(test_error)
            health['error_analysis'] = {
                'classification_working': test_result.category != ErrorCategory.UNKNOWN,
                'confidence_score': test_result.confidence_score,
                'status': 'healthy' if test_result.confidence_score > 0.5 else 'warning'
            }

            # Check storage
            recent_errors = await self.db_manager.postgresql.execute_query("""
            SELECT COUNT(*) as count FROM error_events WHERE timestamp > NOW() - INTERVAL '1 hour'
            """)

            health['storage'] = {
                'recent_errors': recent_errors[0]['count'] if recent_errors else 0,
                'status': 'healthy'
            }

        except Exception as e:
            health['status'] = 'unhealthy'
            health['error'] = str(e)

        return health

# Global ErrorDNA integration instance
error_dna_integration: Optional[ErrorDNAIntegration] = None

async def get_error_dna_integration(db_manager: DatabaseManager) -> ErrorDNAIntegration:
    """Get the global ErrorDNA integration instance."""
    global error_dna_integration
    if not error_dna_integration:
        error_dna_integration = ErrorDNAIntegration(db_manager)
        await error_dna_integration.initialize()
    return error_dna_integration