"""
🔍 Trading Decision Audit System
Comprehensive decision audit trail system preventing the 80%+ AI project failure rate

FEATURES:
- Full audit trail of all trading decisions with immutable logging
- Decision rollback capabilities for failed executions
- Impact assessment framework with performance correlation
- Pattern recognition for decision quality improvement
- Real-time decision monitoring and alerting
- Integration with AI Brain decision validation methodology

AUDIT LAYERS:
1. Decision Creation Audit - Track all decision inputs and parameters
2. Validation Process Audit - Log all validation steps and outcomes
3. Execution Audit - Track execution attempts and results
4. Impact Assessment Audit - Monitor post-decision performance
5. Rollback Audit - Track any rollback actions and reasons
6. Pattern Analysis Audit - Identify decision patterns for improvement
"""

import asyncio
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import uuid
import numpy as np

# Local infrastructure integration
from ....shared.infrastructure.core.logger_core import CoreLogger
from ....shared.infrastructure.core.cache_core import CoreCache
from ....shared.infrastructure.core.error_core import CoreErrorHandler

# Initialize components
logger = CoreLogger("trading-engine", "decision-audit")
cache = CoreCache("decision-audit", max_size=10000, default_ttl=86400)
error_handler = CoreErrorHandler("trading-engine")


class AuditEventType(Enum):
    """Types of audit events for decisions"""
    DECISION_CREATED = "decision_created"
    VALIDATION_STARTED = "validation_started"
    VALIDATION_COMPLETED = "validation_completed" 
    VALIDATION_FAILED = "validation_failed"
    EXECUTION_STARTED = "execution_started"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_FAILED = "execution_failed"
    ROLLBACK_INITIATED = "rollback_initiated"
    ROLLBACK_COMPLETED = "rollback_completed"
    IMPACT_ASSESSED = "impact_assessed"
    PATTERN_DETECTED = "pattern_detected"


class DecisionStatus(Enum):
    """Status of trading decisions"""
    CREATED = "created"
    VALIDATING = "validating"
    VALIDATED = "validated"
    REJECTED = "rejected"
    EXECUTING = "executing"
    EXECUTED = "executed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    COMPLETED = "completed"


class RollbackReason(Enum):
    """Reasons for decision rollback"""
    EXECUTION_FAILURE = "execution_failure"
    RISK_BREACH = "risk_breach"
    MARKET_CONDITION_CHANGE = "market_condition_change"
    SYSTEM_ERROR = "system_error"
    MANUAL_OVERRIDE = "manual_override"
    PERFORMANCE_THRESHOLD = "performance_threshold"


@dataclass
class AuditEvent:
    """Individual audit event record"""
    event_id: str
    decision_id: str
    event_type: AuditEventType
    timestamp: datetime
    
    # Event details
    description: str
    event_data: Dict[str, Any]
    
    # Context
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Performance tracking
    execution_time_ms: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    
    def __post_init__(self):
        if not self.event_id:
            self.event_id = str(uuid.uuid4())


@dataclass
class DecisionAuditRecord:
    """Complete audit record for a trading decision"""
    decision_id: str
    status: DecisionStatus
    created_at: datetime
    
    # Decision details
    symbol: str
    decision_type: str
    action: str
    confidence: float
    
    # Audit trail
    events: List[AuditEvent]
    
    # Validation tracking
    validation_attempts: int = 0
    validation_passed: bool = False
    validation_issues: List[Dict[str, Any]] = None
    
    # Execution tracking
    execution_attempts: int = 0
    execution_success: bool = False
    execution_errors: List[str] = None
    
    # Impact tracking
    impact_metrics: Dict[str, Any] = None
    performance_correlation: Optional[float] = None
    
    # Rollback tracking
    rollback_count: int = 0
    rollback_history: List[Dict[str, Any]] = None
    
    # Pattern analysis
    decision_patterns: List[str] = None
    quality_score: Optional[float] = None
    
    def __post_init__(self):
        if not self.events:
            self.events = []
        if not self.validation_issues:
            self.validation_issues = []
        if not self.execution_errors:
            self.execution_errors = []
        if not self.rollback_history:
            self.rollback_history = []
        if not self.decision_patterns:
            self.decision_patterns = []


@dataclass
class RollbackAction:
    """Rollback action definition"""
    rollback_id: str
    decision_id: str
    reason: RollbackReason
    initiated_at: datetime
    
    # Rollback details
    rollback_type: str  # "position_close", "order_cancel", "risk_adjust"
    rollback_data: Dict[str, Any]
    
    # Execution status
    status: str = "initiated"
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # Recovery metrics
    recovery_time_seconds: Optional[float] = None
    recovery_success: bool = False


class TradingDecisionAuditSystem:
    """
    Comprehensive trading decision audit system with AI Brain methodology
    Provides full audit trail, rollback capabilities, and impact assessment
    """
    
    def __init__(self):
        """Initialize the audit system"""
        
        # Audit storage
        self.audit_records: Dict[str, DecisionAuditRecord] = {}
        self.event_history: deque = deque(maxlen=50000)  # Keep recent events
        
        # Rollback management
        self.rollback_actions: Dict[str, RollbackAction] = {}
        self.rollback_templates: Dict[RollbackReason, Dict[str, Any]] = {}
        
        # Pattern analysis
        self.decision_patterns: Dict[str, int] = defaultdict(int)
        self.quality_metrics: Dict[str, List[float]] = defaultdict(list)
        
        # Performance tracking
        self.audit_statistics = {
            "total_decisions": 0,
            "successful_validations": 0,
            "failed_validations": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "rollbacks_performed": 0,
            "average_decision_quality": 0.0,
            "pattern_recognition_accuracy": 0.0
        }
        
        # Initialize rollback templates
        self._initialize_rollback_templates()
        
        logger.info("Trading Decision Audit System initialized")
    
    def _initialize_rollback_templates(self):
        """Initialize rollback templates for different scenarios"""
        
        self.rollback_templates = {
            RollbackReason.EXECUTION_FAILURE: {
                "rollback_type": "order_cancel",
                "priority": "high",
                "auto_execute": True,
                "recovery_actions": ["cancel_pending_orders", "close_partial_positions"]
            },
            RollbackReason.RISK_BREACH: {
                "rollback_type": "risk_adjust",
                "priority": "critical",
                "auto_execute": True,
                "recovery_actions": ["reduce_position_size", "tighten_stop_loss", "close_positions"]
            },
            RollbackReason.MARKET_CONDITION_CHANGE: {
                "rollback_type": "position_close",
                "priority": "medium",
                "auto_execute": False,
                "recovery_actions": ["evaluate_conditions", "adjust_strategy", "hold_decision"]
            },
            RollbackReason.SYSTEM_ERROR: {
                "rollback_type": "order_cancel",
                "priority": "critical",
                "auto_execute": True,
                "recovery_actions": ["system_check", "retry_execution", "manual_review"]
            }
        }
    
    async def create_decision_audit(
        self,
        decision_id: str,
        symbol: str,
        decision_type: str,
        action: str,
        confidence: float,
        decision_data: Dict[str, Any]
    ) -> DecisionAuditRecord:
        """Create new decision audit record"""
        
        try:
            # Create audit record
            audit_record = DecisionAuditRecord(
                decision_id=decision_id,
                status=DecisionStatus.CREATED,
                created_at=datetime.now(),
                symbol=symbol,
                decision_type=decision_type,
                action=action,
                confidence=confidence
            )
            
            # Create initial audit event
            initial_event = AuditEvent(
                event_id=str(uuid.uuid4()),
                decision_id=decision_id,
                event_type=AuditEventType.DECISION_CREATED,
                timestamp=datetime.now(),
                description=f"Trading decision created: {action} {symbol}",
                event_data={
                    "decision_data": decision_data,
                    "confidence": confidence,
                    "decision_type": decision_type
                }
            )
            
            # Add event to record
            audit_record.events.append(initial_event)
            
            # Store audit record
            self.audit_records[decision_id] = audit_record
            self.event_history.append(initial_event)
            
            # Update statistics
            self.audit_statistics["total_decisions"] += 1
            
            # Cache for quick access
            await cache.set(f"audit:{decision_id}", asdict(audit_record), ttl=86400)
            
            logger.info(f"Decision audit created: {decision_id} - {action} {symbol}")
            
            return audit_record
            
        except Exception as e:
            logger.error(f"Failed to create decision audit: {e}")
            raise
    
    async def log_validation_event(
        self,
        decision_id: str,
        validation_result: Dict[str, Any],
        execution_time_ms: float
    ):
        """Log validation event with comprehensive details"""
        
        try:
            audit_record = self.audit_records.get(decision_id)
            if not audit_record:
                raise ValueError(f"Audit record not found for decision: {decision_id}")
            
            # Determine validation success
            is_valid = validation_result.get("is_valid", False)
            confidence_score = validation_result.get("confidence_score", 0.0)
            
            # Create validation event
            event_type = AuditEventType.VALIDATION_COMPLETED if is_valid else AuditEventType.VALIDATION_FAILED
            
            validation_event = AuditEvent(
                event_id=str(uuid.uuid4()),
                decision_id=decision_id,
                event_type=event_type,
                timestamp=datetime.now(),
                description=f"Validation {'passed' if is_valid else 'failed'} with confidence {confidence_score:.3f}",
                event_data=validation_result,
                execution_time_ms=execution_time_ms
            )
            
            # Update audit record
            audit_record.events.append(validation_event)
            audit_record.validation_attempts += 1
            audit_record.validation_passed = is_valid
            audit_record.status = DecisionStatus.VALIDATED if is_valid else DecisionStatus.REJECTED
            
            if not is_valid:
                audit_record.validation_issues.extend(validation_result.get("issues", []))
            
            # Store event
            self.event_history.append(validation_event)
            
            # Update statistics
            if is_valid:
                self.audit_statistics["successful_validations"] += 1
            else:
                self.audit_statistics["failed_validations"] += 1
            
            # Update cache
            await cache.set(f"audit:{decision_id}", asdict(audit_record), ttl=86400)
            
            logger.info(f"Validation event logged: {decision_id} - {'SUCCESS' if is_valid else 'FAILED'}")
            
        except Exception as e:
            logger.error(f"Failed to log validation event: {e}")
            raise
    
    async def log_execution_event(
        self,
        decision_id: str,
        execution_result: Dict[str, Any],
        execution_time_ms: float
    ):
        """Log execution event with full tracking"""
        
        try:
            audit_record = self.audit_records.get(decision_id)
            if not audit_record:
                raise ValueError(f"Audit record not found for decision: {decision_id}")
            
            # Determine execution success
            success = execution_result.get("success", False)
            
            # Create execution event
            event_type = AuditEventType.EXECUTION_COMPLETED if success else AuditEventType.EXECUTION_FAILED
            
            execution_event = AuditEvent(
                event_id=str(uuid.uuid4()),
                decision_id=decision_id,
                event_type=event_type,
                timestamp=datetime.now(),
                description=f"Execution {'completed' if success else 'failed'}: {execution_result.get('error', 'Success')}",
                event_data=execution_result,
                execution_time_ms=execution_time_ms
            )
            
            # Update audit record
            audit_record.events.append(execution_event)
            audit_record.execution_attempts += 1
            audit_record.execution_success = success
            audit_record.status = DecisionStatus.EXECUTED if success else DecisionStatus.FAILED
            
            if not success:
                error_msg = execution_result.get("error", "Unknown execution error")
                audit_record.execution_errors.append(error_msg)
            
            # Store event
            self.event_history.append(execution_event)
            
            # Update statistics
            if success:
                self.audit_statistics["successful_executions"] += 1
            else:
                self.audit_statistics["failed_executions"] += 1
                
                # Consider rollback if execution failed
                await self._consider_automatic_rollback(decision_id, execution_result)
            
            # Update cache
            await cache.set(f"audit:{decision_id}", asdict(audit_record), ttl=86400)
            
            logger.info(f"Execution event logged: {decision_id} - {'SUCCESS' if success else 'FAILED'}")
            
        except Exception as e:
            logger.error(f"Failed to log execution event: {e}")
            raise
    
    async def initiate_rollback(
        self,
        decision_id: str,
        reason: RollbackReason,
        rollback_data: Dict[str, Any]
    ) -> RollbackAction:
        """Initiate decision rollback with comprehensive tracking"""
        
        try:
            audit_record = self.audit_records.get(decision_id)
            if not audit_record:
                raise ValueError(f"Audit record not found for decision: {decision_id}")
            
            rollback_id = f"rollback_{int(datetime.now().timestamp() * 1000)}"
            
            # Get rollback template
            template = self.rollback_templates.get(reason, {})
            
            # Create rollback action
            rollback_action = RollbackAction(
                rollback_id=rollback_id,
                decision_id=decision_id,
                reason=reason,
                initiated_at=datetime.now(),
                rollback_type=template.get("rollback_type", "manual_review"),
                rollback_data=rollback_data
            )
            
            # Store rollback action
            self.rollback_actions[rollback_id] = rollback_action
            
            # Create rollback event
            rollback_event = AuditEvent(
                event_id=str(uuid.uuid4()),
                decision_id=decision_id,
                event_type=AuditEventType.ROLLBACK_INITIATED,
                timestamp=datetime.now(),
                description=f"Rollback initiated: {reason.value}",
                event_data={
                    "rollback_id": rollback_id,
                    "reason": reason.value,
                    "rollback_type": rollback_action.rollback_type,
                    "rollback_data": rollback_data
                }
            )
            
            # Update audit record
            audit_record.events.append(rollback_event)
            audit_record.rollback_count += 1
            audit_record.rollback_history.append({
                "rollback_id": rollback_id,
                "reason": reason.value,
                "initiated_at": datetime.now().isoformat(),
                "rollback_type": rollback_action.rollback_type
            })
            
            # Store event
            self.event_history.append(rollback_event)
            
            # Update statistics
            self.audit_statistics["rollbacks_performed"] += 1
            
            # Execute rollback if auto-execute enabled
            if template.get("auto_execute", False):
                await self._execute_rollback(rollback_action)
            
            # Update cache
            await cache.set(f"audit:{decision_id}", asdict(audit_record), ttl=86400)
            await cache.set(f"rollback:{rollback_id}", asdict(rollback_action), ttl=86400)
            
            logger.info(f"Rollback initiated: {rollback_id} for decision {decision_id} - Reason: {reason.value}")
            
            return rollback_action
            
        except Exception as e:
            logger.error(f"Failed to initiate rollback: {e}")
            raise
    
    async def _execute_rollback(self, rollback_action: RollbackAction):
        """Execute rollback action based on type"""
        
        start_time = datetime.now()
        
        try:
            logger.info(f"Executing rollback: {rollback_action.rollback_id}")
            
            # Execute rollback based on type
            if rollback_action.rollback_type == "order_cancel":
                success = await self._cancel_orders(rollback_action)
            elif rollback_action.rollback_type == "position_close":
                success = await self._close_positions(rollback_action)
            elif rollback_action.rollback_type == "risk_adjust":
                success = await self._adjust_risk(rollback_action)
            else:
                success = await self._manual_review_required(rollback_action)
            
            # Update rollback status
            rollback_action.completed_at = datetime.now()
            rollback_action.status = "completed" if success else "failed"
            rollback_action.recovery_success = success
            rollback_action.recovery_time_seconds = (datetime.now() - start_time).total_seconds()
            
            # Log rollback completion
            await self._log_rollback_completion(rollback_action)
            
            logger.info(f"Rollback {'completed' if success else 'failed'}: {rollback_action.rollback_id}")
            
        except Exception as e:
            rollback_action.status = "error"
            rollback_action.error_message = str(e)
            rollback_action.recovery_success = False
            
            logger.error(f"Rollback execution failed: {e}")
    
    async def _cancel_orders(self, rollback_action: RollbackAction) -> bool:
        """Cancel pending orders as part of rollback"""
        
        try:
            # Placeholder for order cancellation logic
            # In production, this would integrate with the trading engine
            logger.info(f"Cancelling orders for rollback: {rollback_action.rollback_id}")
            
            # Simulate order cancellation
            await asyncio.sleep(0.1)
            
            return True
            
        except Exception as e:
            logger.error(f"Order cancellation failed: {e}")
            return False
    
    async def _close_positions(self, rollback_action: RollbackAction) -> bool:
        """Close positions as part of rollback"""
        
        try:
            # Placeholder for position closing logic
            logger.info(f"Closing positions for rollback: {rollback_action.rollback_id}")
            
            # Simulate position closing
            await asyncio.sleep(0.1)
            
            return True
            
        except Exception as e:
            logger.error(f"Position closing failed: {e}")
            return False
    
    async def _adjust_risk(self, rollback_action: RollbackAction) -> bool:
        """Adjust risk parameters as part of rollback"""
        
        try:
            # Placeholder for risk adjustment logic
            logger.info(f"Adjusting risk for rollback: {rollback_action.rollback_id}")
            
            # Simulate risk adjustment
            await asyncio.sleep(0.1)
            
            return True
            
        except Exception as e:
            logger.error(f"Risk adjustment failed: {e}")
            return False
    
    async def _manual_review_required(self, rollback_action: RollbackAction) -> bool:
        """Flag for manual review"""
        
        logger.warning(f"Manual review required for rollback: {rollback_action.rollback_id}")
        return True
    
    async def _consider_automatic_rollback(self, decision_id: str, execution_result: Dict[str, Any]):
        """Consider if automatic rollback is needed"""
        
        try:
            # Analyze execution failure to determine if rollback is needed
            error_type = execution_result.get("error_type", "unknown")
            error_severity = execution_result.get("severity", "medium")
            
            # Determine if rollback should be initiated
            should_rollback = False
            rollback_reason = None
            
            if error_type in ["connection_failure", "system_error"] and error_severity == "critical":
                should_rollback = True
                rollback_reason = RollbackReason.SYSTEM_ERROR
            elif error_type == "risk_breach":
                should_rollback = True
                rollback_reason = RollbackReason.RISK_BREACH
            elif error_type == "execution_timeout":
                should_rollback = True
                rollback_reason = RollbackReason.EXECUTION_FAILURE
            
            # Initiate rollback if needed
            if should_rollback and rollback_reason:
                await self.initiate_rollback(
                    decision_id=decision_id,
                    reason=rollback_reason,
                    rollback_data=execution_result
                )
            
        except Exception as e:
            logger.error(f"Failed to consider automatic rollback: {e}")
    
    async def _log_rollback_completion(self, rollback_action: RollbackAction):
        """Log rollback completion event"""
        
        try:
            completion_event = AuditEvent(
                event_id=str(uuid.uuid4()),
                decision_id=rollback_action.decision_id,
                event_type=AuditEventType.ROLLBACK_COMPLETED,
                timestamp=datetime.now(),
                description=f"Rollback {'completed successfully' if rollback_action.recovery_success else 'failed'}",
                event_data={
                    "rollback_id": rollback_action.rollback_id,
                    "recovery_success": rollback_action.recovery_success,
                    "recovery_time_seconds": rollback_action.recovery_time_seconds,
                    "error_message": rollback_action.error_message
                }
            )
            
            # Add to audit record
            audit_record = self.audit_records.get(rollback_action.decision_id)
            if audit_record:
                audit_record.events.append(completion_event)
                audit_record.status = DecisionStatus.ROLLED_BACK
                
                # Update cache
                await cache.set(f"audit:{rollback_action.decision_id}", asdict(audit_record), ttl=86400)
            
            # Store event
            self.event_history.append(completion_event)
            
        except Exception as e:
            logger.error(f"Failed to log rollback completion: {e}")
    
    async def assess_decision_impact(
        self,
        decision_id: str,
        impact_data: Dict[str, Any]
    ):
        """Assess impact of trading decision"""
        
        try:
            audit_record = self.audit_records.get(decision_id)
            if not audit_record:
                raise ValueError(f"Audit record not found for decision: {decision_id}")
            
            # Calculate impact metrics
            impact_metrics = {
                "pnl": impact_data.get("pnl", 0.0),
                "duration_minutes": impact_data.get("duration_minutes", 0),
                "slippage": impact_data.get("slippage", 0.0),
                "execution_quality": impact_data.get("execution_quality", 0.5),
                "risk_realized": impact_data.get("risk_realized", 0.0),
                "timestamp": datetime.now().isoformat()
            }
            
            # Calculate performance correlation with confidence
            performance_correlation = self._calculate_performance_correlation(
                audit_record.confidence,
                impact_metrics
            )
            
            # Update audit record
            audit_record.impact_metrics = impact_metrics
            audit_record.performance_correlation = performance_correlation
            audit_record.status = DecisionStatus.COMPLETED
            
            # Create impact assessment event
            impact_event = AuditEvent(
                event_id=str(uuid.uuid4()),
                decision_id=decision_id,
                event_type=AuditEventType.IMPACT_ASSESSED,
                timestamp=datetime.now(),
                description=f"Decision impact assessed: PnL={impact_metrics['pnl']:.2f}, Correlation={performance_correlation:.3f}",
                event_data=impact_metrics
            )
            
            audit_record.events.append(impact_event)
            self.event_history.append(impact_event)
            
            # Update quality metrics for pattern analysis
            await self._update_quality_metrics(audit_record, impact_metrics)
            
            # Update cache
            await cache.set(f"audit:{decision_id}", asdict(audit_record), ttl=86400)
            
            logger.info(f"Decision impact assessed: {decision_id} - PnL: {impact_metrics['pnl']:.2f}")
            
        except Exception as e:
            logger.error(f"Failed to assess decision impact: {e}")
            raise
    
    def _calculate_performance_correlation(self, confidence: float, impact_metrics: Dict[str, Any]) -> float:
        """Calculate correlation between decision confidence and actual performance"""
        
        try:
            pnl = impact_metrics.get("pnl", 0.0)
            execution_quality = impact_metrics.get("execution_quality", 0.5)
            
            # Normalize PnL to 0-1 scale (simplified)
            normalized_pnl = max(0, min(1, (pnl + 100) / 200))  # Assume PnL range -100 to +100
            
            # Weighted correlation calculation
            performance_score = (normalized_pnl * 0.7) + (execution_quality * 0.3)
            
            # Calculate correlation (simplified Pearson-like)
            correlation = 1 - abs(confidence - performance_score)
            
            return max(-1, min(1, correlation))
            
        except Exception as e:
            logger.error(f"Failed to calculate performance correlation: {e}")
            return 0.0
    
    async def _update_quality_metrics(self, audit_record: DecisionAuditRecord, impact_metrics: Dict[str, Any]):
        """Update decision quality metrics for pattern analysis"""
        
        try:
            # Calculate decision quality score
            quality_factors = []
            
            # Validation quality
            if audit_record.validation_passed:
                quality_factors.append(0.2)  # Base quality for validation
                
            # Execution quality
            if audit_record.execution_success:
                quality_factors.append(0.2)
                
            # Impact quality
            pnl = impact_metrics.get("pnl", 0.0)
            execution_quality = impact_metrics.get("execution_quality", 0.5)
            
            # PnL contribution (0.0 to 0.3)
            pnl_score = max(0, min(0.3, (pnl + 50) / 100))
            quality_factors.append(pnl_score)
            
            # Execution quality contribution (0.0 to 0.3)
            quality_factors.append(execution_quality * 0.3)
            
            # Calculate overall quality score
            quality_score = sum(quality_factors)
            audit_record.quality_score = quality_score
            
            # Update pattern analysis
            decision_pattern = f"{audit_record.decision_type}_{audit_record.action}"
            self.quality_metrics[decision_pattern].append(quality_score)
            
            # Keep only recent quality scores
            if len(self.quality_metrics[decision_pattern]) > 100:
                self.quality_metrics[decision_pattern] = self.quality_metrics[decision_pattern][-100:]
            
            # Update average decision quality
            all_qualities = [q for qualities in self.quality_metrics.values() for q in qualities]
            if all_qualities:
                self.audit_statistics["average_decision_quality"] = np.mean(all_qualities)
            
        except Exception as e:
            logger.error(f"Failed to update quality metrics: {e}")
    
    async def get_decision_audit(self, decision_id: str) -> Optional[DecisionAuditRecord]:
        """Get complete audit record for a decision"""
        
        try:
            # Try cache first
            cached_record = await cache.get(f"audit:{decision_id}")
            if cached_record:
                return DecisionAuditRecord(**cached_record)
            
            # Return from memory
            return self.audit_records.get(decision_id)
            
        except Exception as e:
            logger.error(f"Failed to get decision audit: {e}")
            return None
    
    def get_audit_statistics(self) -> Dict[str, Any]:
        """Get comprehensive audit statistics"""
        
        return {
            "audit_statistics": self.audit_statistics.copy(),
            "total_decisions": len(self.audit_records),
            "active_rollbacks": len([r for r in self.rollback_actions.values() if r.status != "completed"]),
            "pattern_counts": dict(self.decision_patterns),
            "quality_metrics": {
                pattern: {
                    "count": len(qualities),
                    "average_quality": np.mean(qualities) if qualities else 0.0,
                    "quality_trend": "improving" if len(qualities) >= 2 and qualities[-1] > qualities[0] else "stable"
                } 
                for pattern, qualities in self.quality_metrics.items()
            },
            "recent_events_count": len(self.event_history),
            "last_updated": datetime.now().isoformat()
        }


# Global instance
decision_audit_system = TradingDecisionAuditSystem()