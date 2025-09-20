"""
AI Brain Trading Error DNA System - Surgical Precision Error Analysis
Trading-specific error patterns with learning and prevention capabilities
"""

import time
import traceback
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import hashlib

class TradingErrorCategory(Enum):
    """Trading-specific error categories"""
    DATA_QUALITY = "data_quality"
    MODEL_PREDICTION = "model_prediction"
    RISK_MANAGEMENT = "risk_management"
    MARKET_CONDITIONS = "market_conditions"
    EXECUTION_FAILURE = "execution_failure"
    CONFIGURATION = "configuration"
    SYSTEM_INTEGRATION = "system_integration"
    PERFORMANCE_DEGRADATION = "performance_degradation"

@dataclass
class TradingErrorPattern:
    """Trading error pattern with solution guidance"""
    error_id: str
    category: TradingErrorCategory
    pattern: str
    description: str
    solution_confidence: float  # 0.0 to 1.0
    solution_steps: List[str]
    prevention_strategy: str
    related_patterns: List[str]
    trading_context: Dict[str, Any]
    
class AiBrainTradingErrorDNA:
    """
    AI Brain Error DNA System for Trading Operations
    Provides surgical precision error analysis with learning capabilities
    """
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.error_patterns: Dict[str, TradingErrorPattern] = {}
        self.error_history: List[Dict[str, Any]] = []
        self.learning_data: Dict[str, Any] = {}
        self._initialize_trading_patterns()
        
        # Setup logging
        self.logger = logging.getLogger(f"ai_brain_error_dna_{service_name}")
        
    def _initialize_trading_patterns(self):
        """Initialize known trading error patterns"""
        patterns = [
            TradingErrorPattern(
                error_id="DATA_QUALITY_001",
                category=TradingErrorCategory.DATA_QUALITY,
                pattern="Missing or invalid tick data",
                description="Tick data stream interrupted or contains invalid values",
                solution_confidence=0.92,
                solution_steps=[
                    "Validate data source connection",
                    "Check data format consistency",
                    "Implement data quality filters",
                    "Setup backup data sources"
                ],
                prevention_strategy="Implement real-time data validation with redundant sources",
                related_patterns=["DATA_QUALITY_002", "EXECUTION_FAILURE_001"],
                trading_context={"impact": "high", "urgency": "immediate"}
            ),
            
            TradingErrorPattern(
                error_id="MODEL_PREDICTION_001", 
                category=TradingErrorCategory.MODEL_PREDICTION,
                pattern="Model confidence below threshold",
                description="AI/ML model prediction confidence drops below acceptable levels",
                solution_confidence=0.88,
                solution_steps=[
                    "Check model input data quality",
                    "Verify model calibration",
                    "Assess market regime changes",
                    "Consider model retraining"
                ],
                prevention_strategy="Implement confidence monitoring with automatic model validation",
                related_patterns=["PERFORMANCE_DEGRADATION_001", "MARKET_CONDITIONS_001"],
                trading_context={"impact": "high", "urgency": "high"}
            ),
            
            TradingErrorPattern(
                error_id="RISK_MANAGEMENT_001",
                category=TradingErrorCategory.RISK_MANAGEMENT, 
                pattern="Position size exceeds risk limits",
                description="Calculated position size violates risk management rules",
                solution_confidence=0.95,
                solution_steps=[
                    "Recalculate position size with current risk parameters",
                    "Verify risk management settings",
                    "Check account balance and leverage",
                    "Implement position size caps"
                ],
                prevention_strategy="Real-time risk validation before order execution",
                related_patterns=["EXECUTION_FAILURE_002", "CONFIGURATION_001"],
                trading_context={"impact": "critical", "urgency": "immediate"}
            ),
            
            TradingErrorPattern(
                error_id="MARKET_CONDITIONS_001",
                category=TradingErrorCategory.MARKET_CONDITIONS,
                pattern="Extreme market volatility detected",
                description="Market conditions exceed normal trading parameters",
                solution_confidence=0.85,
                solution_steps=[
                    "Adjust risk parameters for high volatility",
                    "Reduce position sizes temporarily", 
                    "Increase stop-loss margins",
                    "Consider trading suspension"
                ],
                prevention_strategy="Continuous market regime monitoring with adaptive parameters",
                related_patterns=["RISK_MANAGEMENT_001", "MODEL_PREDICTION_001"],
                trading_context={"impact": "high", "urgency": "high"}
            ),
            
            TradingErrorPattern(
                error_id="EXECUTION_FAILURE_001",
                category=TradingErrorCategory.EXECUTION_FAILURE,
                pattern="Order execution timeout or rejection",
                description="Trading order fails to execute within expected timeframe",
                solution_confidence=0.90,
                solution_steps=[
                    "Check broker connection status",
                    "Verify account permissions and balance",
                    "Assess market liquidity conditions",
                    "Implement retry logic with exponential backoff"
                ],
                prevention_strategy="Pre-execution validation with connection monitoring",
                related_patterns=["SYSTEM_INTEGRATION_001", "MARKET_CONDITIONS_001"],
                trading_context={"impact": "high", "urgency": "immediate"}
            )
        ]
        
        for pattern in patterns:
            self.error_patterns[pattern.error_id] = pattern
    
    def analyze_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Perform surgical precision error analysis
        
        Args:
            error: The exception that occurred
            context: Additional context about the error
            
        Returns:
            Comprehensive error analysis with solution guidance
        """
        error_signature = self._generate_error_signature(error, context)
        matched_pattern = self._match_error_pattern(error, context)
        
        analysis = {
            "timestamp": time.time(),
            "service": self.service_name,
            "error_signature": error_signature,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "stack_trace": traceback.format_exc(),
            "context": context or {},
            "matched_pattern": None,
            "solution_confidence": 0.0,
            "recommended_actions": [],
            "prevention_strategy": "",
            "trading_impact": "unknown",
            "urgency_level": "medium"
        }
        
        if matched_pattern:
            analysis.update({
                "matched_pattern": matched_pattern.error_id,
                "pattern_description": matched_pattern.description,
                "solution_confidence": matched_pattern.solution_confidence,
                "recommended_actions": matched_pattern.solution_steps,
                "prevention_strategy": matched_pattern.prevention_strategy,
                "trading_impact": matched_pattern.trading_context.get("impact", "unknown"),
                "urgency_level": matched_pattern.trading_context.get("urgency", "medium"),
                "related_patterns": matched_pattern.related_patterns
            })
        
        # Learn from this error
        self._learn_from_error(analysis)
        
        # Log the analysis
        self.logger.error(f"AI Brain Error DNA Analysis: {json.dumps(analysis, indent=2, default=str)}")
        
        return analysis
    
    def _generate_error_signature(self, error: Exception, context: Dict[str, Any] = None) -> str:
        """Generate unique signature for error pattern matching"""
        signature_data = {
            "error_type": type(error).__name__,
            "error_message": str(error)[:100],  # First 100 chars
            "service": self.service_name
        }
        
        if context:
            # Add trading-specific context
            if "symbol" in context:
                signature_data["symbol"] = context["symbol"]
            if "operation" in context:
                signature_data["operation"] = context["operation"]
            if "model_type" in context:
                signature_data["model_type"] = context["model_type"]
        
        signature_str = json.dumps(signature_data, sort_keys=True)
        return hashlib.md5(signature_str.encode()).hexdigest()[:12]
    
    def _match_error_pattern(self, error: Exception, context: Dict[str, Any] = None) -> Optional[TradingErrorPattern]:
        """Match error against known patterns"""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # Pattern matching logic
        for pattern_id, pattern in self.error_patterns.items():
            pattern_keywords = pattern.pattern.lower().split()
            
            # Check if error matches pattern keywords
            matches = 0
            for keyword in pattern_keywords:
                if keyword in error_str or keyword in error_type:
                    matches += 1
            
            # If more than 50% keywords match, consider it a match
            if matches / len(pattern_keywords) > 0.5:
                return pattern
        
        return None
    
    def _learn_from_error(self, analysis: Dict[str, Any]):
        """Learn from error occurrence to improve future analysis"""
        error_signature = analysis["error_signature"]
        
        # Update learning data
        if error_signature not in self.learning_data:
            self.learning_data[error_signature] = {
                "occurrence_count": 0,
                "last_seen": None,
                "resolution_attempts": [],
                "success_rate": 0.0
            }
        
        self.learning_data[error_signature]["occurrence_count"] += 1
        self.learning_data[error_signature]["last_seen"] = time.time()
        
        # Store in error history
        self.error_history.append(analysis)
        
        # Keep only last 1000 errors to manage memory
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]
    
    def suggest_preventive_actions(self, service_context: Dict[str, Any]) -> List[str]:
        """Suggest preventive actions based on error history"""
        suggestions = []
        
        # Analyze recent error patterns
        recent_errors = [e for e in self.error_history if time.time() - e["timestamp"] < 86400]  # Last 24 hours
        
        if len(recent_errors) > 10:
            suggestions.append("High error frequency detected - review system health")
        
        # Category-based suggestions
        category_counts = {}
        for error in recent_errors:
            if error.get("matched_pattern"):
                pattern = self.error_patterns.get(error["matched_pattern"])
                if pattern:
                    category = pattern.category.value
                    category_counts[category] = category_counts.get(category, 0) + 1
        
        for category, count in category_counts.items():
            if count > 3:
                suggestions.append(f"Frequent {category} errors - implement {category} monitoring")
        
        return suggestions
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error statistics"""
        total_errors = len(self.error_history)
        recent_errors = [e for e in self.error_history if time.time() - e["timestamp"] < 86400]
        
        category_stats = {}
        for error in self.error_history:
            if error.get("matched_pattern"):
                pattern = self.error_patterns.get(error["matched_pattern"])
                if pattern:
                    category = pattern.category.value
                    category_stats[category] = category_stats.get(category, 0) + 1
        
        return {
            "total_errors": total_errors,
            "recent_errors_24h": len(recent_errors),
            "error_rate_24h": len(recent_errors) / 24.0 if recent_errors else 0,
            "category_breakdown": category_stats,
            "pattern_coverage": len([e for e in self.error_history if e.get("matched_pattern")]) / max(total_errors, 1),
            "average_solution_confidence": sum([e.get("solution_confidence", 0) for e in self.error_history]) / max(total_errors, 1)
        }
    
    def export_error_patterns(self) -> Dict[str, Any]:
        """Export error patterns for sharing across services"""
        return {
            "service": self.service_name,
            "patterns": {pid: asdict(pattern) for pid, pattern in self.error_patterns.items()},
            "learning_data": self.learning_data,
            "statistics": self.get_error_statistics()
        }