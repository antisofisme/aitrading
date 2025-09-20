"""
🛡️ AI Brain Trading Decision Validator
Comprehensive decision validation system preventing the 80%+ AI project failure rate

KEY FEATURES:
- Systematic validation of all trading decisions using AI Brain patterns
- Multi-layered decision analysis with confidence thresholds
- Risk-based decision classification and validation
- Pattern compatibility checking for trading strategies
- Architectural flow validation for trading pipeline
- Comprehensive decision history tracking for learning

VALIDATION LAYERS:
1. Basic Requirements Validation (required fields, data types)
2. Confidence Threshold Validation (model certainty requirements)
3. Risk Management Validation (position sizing, exposure limits)
4. Pattern Compatibility Validation (strategy alignment)
5. Market Condition Validation (trading environment suitability)
6. Historical Performance Validation (track record consistency)

INTEGRATION WITH AI BRAIN:
- Uses core decision validator with trading-specific enhancements
- Implements trading-specific validation rules and thresholds
- Provides surgical precision error analysis for validation failures
- Includes real-time decision calibration and improvement
"""

import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
import statistics
import numpy as np

# Import AI Brain Components
import sys
from pathlib import Path

# Add AI Brain path to sys.path
ai_brain_path = Path(__file__).parent.parent.parent.parent.parent / "ai-brain"
if str(ai_brain_path) not in sys.path:
    sys.path.insert(0, str(ai_brain_path))

try:
    from foundation.decision_validator import AIDecisionValidator
    from foundation.error_dna import ErrorDNASystem
    AI_BRAIN_AVAILABLE = True
except ImportError:
    AI_BRAIN_AVAILABLE = False
    print("AI Brain decision validator not available, using standalone implementation")


class TradingDecisionType(Enum):
    """Types of trading decisions that require validation"""
    OPEN_POSITION = "open_position"
    CLOSE_POSITION = "close_position"
    MODIFY_POSITION = "modify_position"
    RISK_ADJUSTMENT = "risk_adjustment"
    STRATEGY_CHANGE = "strategy_change"
    EMERGENCY_STOP = "emergency_stop"
    PORTFOLIO_REBALANCE = "portfolio_rebalance"


class ValidationSeverity(Enum):
    """Severity levels for validation requirements"""
    LOW = "low"           # Minor issues, decision can proceed with warnings
    MEDIUM = "medium"     # Moderate issues, decision should be reviewed
    HIGH = "high"         # Significant issues, decision should be modified
    CRITICAL = "critical" # Critical issues, decision must be blocked


@dataclass
class TradingDecision:
    """Comprehensive trading decision model"""
    decision_type: TradingDecisionType
    symbol: str
    action: str  # "buy", "sell", "hold", "close"
    position_size: float
    confidence: float
    reasoning: str
    
    # Risk parameters
    risk_per_trade: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    # Strategy context
    strategy_id: Optional[str] = None
    timeframe: Optional[str] = None
    
    # Model predictions
    ml_prediction: Optional[Dict[str, Any]] = None
    dl_prediction: Optional[Dict[str, Any]] = None
    ai_evaluation: Optional[Dict[str, Any]] = None
    
    # Market context
    market_conditions: Optional[Dict[str, Any]] = None
    
    # Metadata
    timestamp: str = ""
    decision_id: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if not self.decision_id:
            self.decision_id = f"decision_{int(datetime.now().timestamp() * 1000)}"


@dataclass
class ValidationResult:
    """Result of trading decision validation"""
    is_valid: bool
    confidence_score: float
    validation_details: Dict[str, Any]
    issues: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    requirements: List[Dict[str, Any]]
    recommendations: List[str]
    fallback_required: bool
    validation_time: float
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class AIBrainTradingDecisionValidator:
    """
    AI Brain enhanced trading decision validator
    Implements systematic validation preventing AI project failures
    """
    
    def __init__(self):
        # Initialize AI Brain components if available
        if AI_BRAIN_AVAILABLE:
            self.core_validator = AIDecisionValidator()
            self.error_dna = ErrorDNASystem()
        else:
            self.core_validator = None
            self.error_dna = None
        
        # Trading-specific confidence thresholds
        self.confidence_thresholds = {
            TradingDecisionType.OPEN_POSITION: 0.75,
            TradingDecisionType.CLOSE_POSITION: 0.65,
            TradingDecisionType.MODIFY_POSITION: 0.70,
            TradingDecisionType.RISK_ADJUSTMENT: 0.80,
            TradingDecisionType.STRATEGY_CHANGE: 0.85,
            TradingDecisionType.EMERGENCY_STOP: 0.95,
            TradingDecisionType.PORTFOLIO_REBALANCE: 0.80
        }
        
        # Risk limits for validation
        self.risk_limits = {
            "max_position_size": 0.2,      # 20% of account
            "max_risk_per_trade": 0.05,    # 5% risk per trade
            "max_daily_risk": 0.10,        # 10% daily risk
            "max_portfolio_exposure": 0.8,  # 80% portfolio exposure
            "max_correlation_exposure": 0.3 # 30% in correlated positions
        }
        
        # Market condition requirements
        self.market_condition_requirements = {
            "minimum_liquidity": 0.6,
            "maximum_volatility": 0.9,
            "minimum_data_quality": 0.8,
            "maximum_spread_ratio": 0.05
        }
        
        # Decision history for pattern analysis
        self.decision_history = []
        self.validation_statistics = {
            "total_validations": 0,
            "successful_validations": 0,
            "failed_validations": 0,
            "average_confidence": 0.0,
            "common_issues": {},
            "decision_type_stats": {}
        }
        
        # Pattern compatibility rules
        self._initialize_pattern_rules()
    
    def _initialize_pattern_rules(self):
        """Initialize trading pattern compatibility rules"""
        
        self.pattern_rules = {
            "momentum_strategy": {
                "required_confidence": 0.8,
                "preferred_market_conditions": ["trending", "high_volume"],
                "incompatible_with": ["mean_reversion_strategy"],
                "risk_multiplier": 1.2
            },
            "mean_reversion_strategy": {
                "required_confidence": 0.75,
                "preferred_market_conditions": ["ranging", "low_volatility"],
                "incompatible_with": ["momentum_strategy"],
                "risk_multiplier": 1.0
            },
            "scalping_strategy": {
                "required_confidence": 0.85,
                "preferred_market_conditions": ["high_liquidity", "low_spread"],
                "risk_multiplier": 0.8,
                "max_position_hold_time": "5_minutes"
            },
            "swing_strategy": {
                "required_confidence": 0.70,
                "preferred_market_conditions": ["trending", "medium_volatility"],
                "risk_multiplier": 1.1,
                "min_position_hold_time": "4_hours"
            }
        }
    
    async def validate_trading_decision(
        self,
        decision: TradingDecision,
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Comprehensive validation of trading decision using AI Brain methodology
        
        Args:
            decision: Trading decision to validate
            context: Additional context for validation
            
        Returns:
            Detailed validation result with recommendations
        """
        
        start_time = datetime.now()
        validation_issues = []
        validation_warnings = []
        validation_requirements = []
        recommendations = []
        
        try:
            # Layer 1: Basic Requirements Validation
            await self._validate_basic_requirements(decision, validation_issues, validation_warnings)
            
            # Layer 2: Confidence Threshold Validation
            await self._validate_confidence_thresholds(decision, validation_issues, validation_warnings)
            
            # Layer 3: Risk Management Validation
            await self._validate_risk_management(decision, context, validation_issues, validation_warnings)
            
            # Layer 4: Pattern Compatibility Validation
            await self._validate_pattern_compatibility(decision, validation_issues, validation_warnings)
            
            # Layer 5: Market Condition Validation
            await self._validate_market_conditions(decision, validation_issues, validation_warnings)
            
            # Layer 6: Historical Performance Validation
            await self._validate_historical_consistency(decision, context, validation_issues, validation_warnings)
            
            # AI Brain Core Validation (if available)
            if self.core_validator and AI_BRAIN_AVAILABLE:
                try:
                    core_validation = await self._run_ai_brain_validation(decision, context)
                    if not core_validation["isValid"]:
                        validation_issues.extend(core_validation.get("issues", []))
                    validation_warnings.extend(core_validation.get("warnings", []))
                    validation_requirements.extend(core_validation.get("requirements", []))
                except Exception as e:
                    validation_warnings.append({
                        "type": "AI_BRAIN_VALIDATION_ERROR",
                        "message": f"AI Brain validation failed: {str(e)}",
                        "suggestion": "Proceeding with local validation only"
                    })
            
            # Determine overall validation result
            is_valid = len([issue for issue in validation_issues if issue.get("severity") in ["HIGH", "CRITICAL"]]) == 0
            
            # Calculate validation confidence
            confidence_factors = []
            confidence_factors.append(min(1.0, decision.confidence * 1.2))  # Decision confidence
            confidence_factors.append(1.0 - (len(validation_issues) * 0.1))  # Issue penalty
            confidence_factors.append(1.0 - (len(validation_warnings) * 0.05))  # Warning penalty
            
            validation_confidence = max(0.0, min(1.0, statistics.mean(confidence_factors)))
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(
                decision, validation_issues, validation_warnings, context
            )
            
            # Check if fallback is required
            fallback_required = (
                not is_valid or 
                validation_confidence < 0.5 or
                len([issue for issue in validation_issues if issue.get("severity") == "CRITICAL"]) > 0
            )
            
            # Create validation result
            validation_time = (datetime.now() - start_time).total_seconds()
            
            result = ValidationResult(
                is_valid=is_valid,
                confidence_score=validation_confidence,
                validation_details={
                    "decision_type": decision.decision_type.value,
                    "symbol": decision.symbol,
                    "action": decision.action,
                    "validation_layers": {
                        "basic_requirements": len([i for i in validation_issues if i.get("layer") == "basic"]) == 0,
                        "confidence_thresholds": len([i for i in validation_issues if i.get("layer") == "confidence"]) == 0,
                        "risk_management": len([i for i in validation_issues if i.get("layer") == "risk"]) == 0,
                        "pattern_compatibility": len([i for i in validation_issues if i.get("layer") == "pattern"]) == 0,
                        "market_conditions": len([i for i in validation_issues if i.get("layer") == "market"]) == 0,
                        "historical_consistency": len([i for i in validation_issues if i.get("layer") == "history"]) == 0
                    },
                    "ai_brain_enhanced": AI_BRAIN_AVAILABLE
                },
                issues=validation_issues,
                warnings=validation_warnings,
                requirements=validation_requirements,
                recommendations=recommendations,
                fallback_required=fallback_required,
                validation_time=validation_time
            )
            
            # Store for learning and improvement
            await self._update_validation_statistics(decision, result)
            
            # Log validation with AI Brain if available
            if self.error_dna and AI_BRAIN_AVAILABLE:
                await self.error_dna.logDecision(
                    f"Trading decision validation: {decision.action} {decision.symbol}",
                    validation_confidence,
                    f"Decision validation completed with {len(validation_issues)} issues and {len(validation_warnings)} warnings",
                    {
                        "decision_id": decision.decision_id,
                        "is_valid": is_valid,
                        "confidence": validation_confidence,
                        "decision_type": decision.decision_type.value
                    }
                )
            
            return result
            
        except Exception as e:
            # Validation itself failed - critical error
            fallback_result = ValidationResult(
                is_valid=False,
                confidence_score=0.0,
                validation_details={
                    "validation_error": str(e),
                    "fallback_mode": True
                },
                issues=[{
                    "type": "VALIDATION_SYSTEM_ERROR",
                    "severity": "CRITICAL",
                    "message": f"Decision validation system failed: {str(e)}",
                    "suggestion": "Manual review required - validation system needs attention"
                }],
                warnings=[],
                requirements=[{
                    "type": "MANUAL_REVIEW_REQUIRED",
                    "message": "Validation system failure requires manual decision review",
                    "priority": "CRITICAL"
                }],
                recommendations=["Immediate manual review required", "Fix validation system before proceeding"],
                fallback_required=True,
                validation_time=(datetime.now() - start_time).total_seconds()
            )
            
            return fallback_result
    
    async def _validate_basic_requirements(
        self,
        decision: TradingDecision,
        issues: List[Dict[str, Any]],
        warnings: List[Dict[str, Any]]
    ):
        """Layer 1: Validate basic decision requirements"""
        
        # Required fields validation
        required_fields = ["symbol", "action", "position_size", "confidence", "reasoning"]
        for field in required_fields:
            if not hasattr(decision, field) or getattr(decision, field) is None:
                issues.append({
                    "type": "MISSING_REQUIRED_FIELD",
                    "severity": "CRITICAL",
                    "layer": "basic",
                    "message": f"Required field '{field}' is missing",
                    "suggestion": f"Provide {field} value for the decision"
                })
        
        # Data type validation
        if hasattr(decision, 'position_size'):
            if not isinstance(decision.position_size, (int, float)) or decision.position_size <= 0:
                issues.append({
                    "type": "INVALID_POSITION_SIZE",
                    "severity": "HIGH",
                    "layer": "basic",
                    "message": f"Position size {decision.position_size} is invalid",
                    "suggestion": "Position size must be a positive number"
                })
        
        if hasattr(decision, 'confidence'):
            if not isinstance(decision.confidence, (int, float)) or not (0 <= decision.confidence <= 1):
                issues.append({
                    "type": "INVALID_CONFIDENCE",
                    "severity": "HIGH",
                    "layer": "basic",
                    "message": f"Confidence {decision.confidence} is invalid",
                    "suggestion": "Confidence must be between 0 and 1"
                })
        
        # Action validation
        valid_actions = ["buy", "sell", "hold", "close"]
        if hasattr(decision, 'action') and decision.action not in valid_actions:
            issues.append({
                "type": "INVALID_ACTION",
                "severity": "HIGH",
                "layer": "basic",
                "message": f"Action '{decision.action}' is not valid",
                "suggestion": f"Action must be one of: {', '.join(valid_actions)}"
            })
        
        # Symbol validation
        if hasattr(decision, 'symbol'):
            if not isinstance(decision.symbol, str) or len(decision.symbol) < 2:
                issues.append({
                    "type": "INVALID_SYMBOL",
                    "severity": "MEDIUM",
                    "layer": "basic",
                    "message": f"Symbol '{decision.symbol}' appears invalid",
                    "suggestion": "Ensure symbol follows standard format (e.g., EURUSD, AAPL)"
                })
    
    async def _validate_confidence_thresholds(
        self,
        decision: TradingDecision,
        issues: List[Dict[str, Any]],
        warnings: List[Dict[str, Any]]
    ):
        """Layer 2: Validate confidence thresholds"""
        
        required_confidence = self.confidence_thresholds.get(decision.decision_type, 0.7)
        
        if decision.confidence < required_confidence:
            severity = "CRITICAL" if required_confidence - decision.confidence > 0.2 else "HIGH"
            issues.append({
                "type": "INSUFFICIENT_CONFIDENCE",
                "severity": severity,
                "layer": "confidence",
                "message": f"Decision confidence {decision.confidence:.2%} below required {required_confidence:.2%}",
                "suggestion": f"Improve prediction quality or reduce position size",
                "confidence_gap": required_confidence - decision.confidence
            })
        elif decision.confidence < required_confidence + 0.05:
            warnings.append({
                "type": "LOW_CONFIDENCE_MARGIN",
                "layer": "confidence",
                "message": f"Confidence barely meets threshold ({decision.confidence:.2%} vs {required_confidence:.2%})",
                "suggestion": "Consider additional validation or smaller position size"
            })
        
        # Validate individual model confidences if available
        if decision.ml_prediction and "confidence" in decision.ml_prediction:
            ml_conf = decision.ml_prediction["confidence"]
            if ml_conf < 0.5:
                warnings.append({
                    "type": "LOW_ML_CONFIDENCE",
                    "layer": "confidence",
                    "message": f"ML model confidence is low: {ml_conf:.2%}",
                    "suggestion": "Review ML model inputs and feature quality"
                })
        
        if decision.dl_prediction and "confidence" in decision.dl_prediction:
            dl_conf = decision.dl_prediction["confidence"]
            if dl_conf < 0.5:
                warnings.append({
                    "type": "LOW_DL_CONFIDENCE",
                    "layer": "confidence",
                    "message": f"Deep learning confidence is low: {dl_conf:.2%}",
                    "suggestion": "Review DL model inputs and training data"
                })
    
    async def _validate_risk_management(
        self,
        decision: TradingDecision,
        context: Optional[Dict[str, Any]],
        issues: List[Dict[str, Any]],
        warnings: List[Dict[str, Any]]
    ):
        """Layer 3: Validate risk management parameters"""
        
        # Position size validation
        if decision.position_size > self.risk_limits["max_position_size"]:
            issues.append({
                "type": "EXCESSIVE_POSITION_SIZE",
                "severity": "CRITICAL",
                "layer": "risk",
                "message": f"Position size {decision.position_size:.2%} exceeds limit {self.risk_limits['max_position_size']:.2%}",
                "suggestion": "Reduce position size to comply with risk limits"
            })
        
        # Risk per trade validation
        if decision.risk_per_trade > self.risk_limits["max_risk_per_trade"]:
            issues.append({
                "type": "EXCESSIVE_RISK_PER_TRADE",
                "severity": "HIGH",
                "layer": "risk",
                "message": f"Risk per trade {decision.risk_per_trade:.2%} exceeds limit {self.risk_limits['max_risk_per_trade']:.2%}",
                "suggestion": "Reduce risk per trade or tighten stop loss"
            })
        
        # Stop loss validation
        if decision.decision_type == TradingDecisionType.OPEN_POSITION:
            if not decision.stop_loss:
                warnings.append({
                    "type": "MISSING_STOP_LOSS",
                    "layer": "risk",
                    "message": "No stop loss specified for position opening",
                    "suggestion": "Consider adding stop loss for risk management"
                })
        
        # Context-based risk validation
        if context:
            account_balance = context.get("account_balance", 10000)
            open_positions = context.get("open_positions", 0)
            daily_pnl = context.get("daily_pnl", 0)
            
            # Portfolio exposure validation
            if open_positions > 10:
                warnings.append({
                    "type": "HIGH_PORTFOLIO_EXPOSURE",
                    "layer": "risk",
                    "message": f"High number of open positions: {open_positions}",
                    "suggestion": "Consider reducing portfolio exposure"
                })
            
            # Daily loss limit
            daily_loss_pct = abs(daily_pnl) / account_balance if account_balance > 0 else 0
            if daily_pnl < 0 and daily_loss_pct > self.risk_limits["max_daily_risk"]:
                issues.append({
                    "type": "DAILY_LOSS_LIMIT_EXCEEDED",
                    "severity": "CRITICAL",
                    "layer": "risk",
                    "message": f"Daily loss {daily_loss_pct:.2%} exceeds limit {self.risk_limits['max_daily_risk']:.2%}",
                    "suggestion": "Stop trading for today to prevent further losses"
                })
    
    async def _validate_pattern_compatibility(
        self,
        decision: TradingDecision,
        issues: List[Dict[str, Any]],
        warnings: List[Dict[str, Any]]
    ):
        """Layer 4: Validate pattern compatibility"""
        
        if not decision.strategy_id:
            warnings.append({
                "type": "MISSING_STRATEGY_ID",
                "layer": "pattern",
                "message": "No strategy ID specified",
                "suggestion": "Specify strategy for better pattern validation"
            })
            return
        
        # Check if strategy exists in pattern rules
        pattern_rule = self.pattern_rules.get(decision.strategy_id)
        if not pattern_rule:
            warnings.append({
                "type": "UNKNOWN_STRATEGY_PATTERN",
                "layer": "pattern",
                "message": f"Unknown strategy pattern: {decision.strategy_id}",
                "suggestion": "Ensure strategy is properly configured"
            })
            return
        
        # Validate required confidence for strategy
        required_confidence = pattern_rule.get("required_confidence", 0.7)
        if decision.confidence < required_confidence:
            issues.append({
                "type": "STRATEGY_CONFIDENCE_MISMATCH",
                "severity": "HIGH",
                "layer": "pattern",
                "message": f"Strategy {decision.strategy_id} requires {required_confidence:.2%} confidence, got {decision.confidence:.2%}",
                "suggestion": f"Increase confidence or use different strategy"
            })
        
        # Validate market conditions for strategy
        if decision.market_conditions and "preferred_market_conditions" in pattern_rule:
            preferred_conditions = pattern_rule["preferred_market_conditions"]
            current_conditions = decision.market_conditions.get("conditions", [])
            
            if not any(condition in current_conditions for condition in preferred_conditions):
                warnings.append({
                    "type": "SUBOPTIMAL_MARKET_CONDITIONS",
                    "layer": "pattern",
                    "message": f"Current conditions {current_conditions} not ideal for {decision.strategy_id}",
                    "suggestion": f"Strategy works best in: {', '.join(preferred_conditions)}"
                })
    
    async def _validate_market_conditions(
        self,
        decision: TradingDecision,
        issues: List[Dict[str, Any]],
        warnings: List[Dict[str, Any]]
    ):
        """Layer 5: Validate market conditions"""
        
        if not decision.market_conditions:
            warnings.append({
                "type": "MISSING_MARKET_CONDITIONS",
                "layer": "market",
                "message": "No market condition data available",
                "suggestion": "Include market condition analysis for better validation"
            })
            return
        
        market_data = decision.market_conditions
        
        # Liquidity validation
        liquidity = market_data.get("liquidity", 0.5)
        if liquidity < self.market_condition_requirements["minimum_liquidity"]:
            issues.append({
                "type": "INSUFFICIENT_LIQUIDITY",
                "severity": "HIGH",
                "layer": "market",
                "message": f"Market liquidity {liquidity:.2%} below minimum {self.market_condition_requirements['minimum_liquidity']:.2%}",
                "suggestion": "Wait for better liquidity or reduce position size"
            })
        
        # Volatility validation
        volatility = market_data.get("volatility", 0.5)
        if volatility > self.market_condition_requirements["maximum_volatility"]:
            warnings.append({
                "type": "HIGH_VOLATILITY",
                "layer": "market",
                "message": f"High market volatility: {volatility:.2%}",
                "suggestion": "Consider reducing position size due to increased risk"
            })
        
        # Data quality validation
        data_quality = market_data.get("data_quality", 0.8)
        if data_quality < self.market_condition_requirements["minimum_data_quality"]:
            issues.append({
                "type": "POOR_DATA_QUALITY",
                "severity": "MEDIUM",
                "layer": "market",
                "message": f"Data quality {data_quality:.2%} below minimum {self.market_condition_requirements['minimum_data_quality']:.2%}",
                "suggestion": "Wait for better data quality or proceed with caution"
            })
        
        # Spread validation
        spread_ratio = market_data.get("spread_ratio", 0.01)
        if spread_ratio > self.market_condition_requirements["maximum_spread_ratio"]:
            warnings.append({
                "type": "WIDE_SPREAD",
                "layer": "market",
                "message": f"Wide spread ratio: {spread_ratio:.4f}",
                "suggestion": "Wide spreads may impact trade profitability"
            })
    
    async def _validate_historical_consistency(
        self,
        decision: TradingDecision,
        context: Optional[Dict[str, Any]],
        issues: List[Dict[str, Any]],
        warnings: List[Dict[str, Any]]
    ):
        """Layer 6: Validate against historical performance"""
        
        if not context or "historical_performance" not in context:
            warnings.append({
                "type": "MISSING_HISTORICAL_DATA",
                "layer": "history",
                "message": "No historical performance data available",
                "suggestion": "Include historical analysis for better validation"
            })
            return
        
        historical = context["historical_performance"]
        
        # Win rate validation
        win_rate = historical.get("win_rate", 0.5)
        if win_rate < 0.4:
            issues.append({
                "type": "POOR_HISTORICAL_WIN_RATE",
                "severity": "MEDIUM",
                "layer": "history",
                "message": f"Low historical win rate: {win_rate:.2%}",
                "suggestion": "Review and improve strategy before proceeding"
            })
        
        # Profit factor validation
        profit_factor = historical.get("profit_factor", 1.0)
        if profit_factor < 1.2:
            warnings.append({
                "type": "LOW_PROFIT_FACTOR",
                "layer": "history",
                "message": f"Low profit factor: {profit_factor:.2f}",
                "suggestion": "Strategy profitability may be marginal"
            })
        
        # Drawdown validation
        max_drawdown = historical.get("max_drawdown", -0.1)
        if max_drawdown < -0.2:  # More than 20% drawdown
            warnings.append({
                "type": "HIGH_HISTORICAL_DRAWDOWN",
                "layer": "history",
                "message": f"High historical drawdown: {max_drawdown:.2%}",
                "suggestion": "Strategy has experienced significant losses in the past"
            })
        
        # Recent performance validation
        recent_performance = historical.get("recent_30_day_performance", 0.0)
        if recent_performance < -0.05:  # Recent 5% loss
            warnings.append({
                "type": "POOR_RECENT_PERFORMANCE",
                "layer": "history",
                "message": f"Poor recent performance: {recent_performance:.2%}",
                "suggestion": "Strategy may be going through a difficult period"
            })
    
    async def _run_ai_brain_validation(
        self,
        decision: TradingDecision,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Run AI Brain core validation"""
        
        # Convert trading decision to AI Brain format
        ai_brain_decision = {
            "type": "TRADING_DECISION",
            "confidence": decision.confidence,
            "reasoning": decision.reasoning,
            "serviceName": None,  # Not applicable for trading decisions
            "patterns": [decision.strategy_id] if decision.strategy_id else [],
            "category": decision.decision_type.value,
            "symbol": decision.symbol,
            "action": decision.action,
            "position_size": decision.position_size,
            "risk_per_trade": decision.risk_per_trade
        }
        
        # Run core validation
        validation_result = await self.core_validator.validateDecision(ai_brain_decision, context or {})
        
        return validation_result
    
    async def _generate_recommendations(
        self,
        decision: TradingDecision,
        issues: List[Dict[str, Any]],
        warnings: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate specific recommendations based on validation results"""
        
        recommendations = []
        
        # Critical issue recommendations
        critical_issues = [issue for issue in issues if issue.get("severity") == "CRITICAL"]
        if critical_issues:
            recommendations.append("CRITICAL ISSUES DETECTED - Manual review required before proceeding")
            for issue in critical_issues:
                recommendations.append(f"- {issue.get('suggestion', 'Address critical issue')}")
        
        # High severity recommendations
        high_issues = [issue for issue in issues if issue.get("severity") == "HIGH"]
        if high_issues:
            recommendations.append("High priority issues require attention:")
            for issue in high_issues[:3]:  # Limit to top 3
                recommendations.append(f"- {issue.get('suggestion', 'Address high priority issue')}")
        
        # Confidence-based recommendations
        if decision.confidence < 0.7:
            recommendations.append("Consider improving prediction confidence through:")
            recommendations.append("- Using ensemble models for better accuracy")
            recommendations.append("- Waiting for more favorable market conditions")
            recommendations.append("- Reducing position size to compensate for uncertainty")
        
        # Risk-based recommendations
        if decision.risk_per_trade > 0.03:
            recommendations.append("High risk detected - consider:")
            recommendations.append("- Reducing position size")
            recommendations.append("- Tightening stop loss")
            recommendations.append("- Using smaller timeframes for entry")
        
        # Pattern-based recommendations
        if decision.strategy_id and warnings:
            pattern_warnings = [w for w in warnings if w.get("layer") == "pattern"]
            if pattern_warnings:
                recommendations.append("Strategy optimization suggestions:")
                for warning in pattern_warnings[:2]:
                    recommendations.append(f"- {warning.get('suggestion', 'Review strategy settings')}")
        
        # Market condition recommendations
        market_warnings = [w for w in warnings if w.get("layer") == "market"]
        if market_warnings:
            recommendations.append("Market condition considerations:")
            for warning in market_warnings[:2]:
                recommendations.append(f"- {warning.get('suggestion', 'Monitor market conditions')}")
        
        # General recommendations
        if not recommendations:
            if decision.confidence > 0.8:
                recommendations.append("Decision appears well-validated - proceed with confidence")
                recommendations.append("Consider slightly larger position size if risk allows")
            else:
                recommendations.append("Decision meets minimum requirements")
                recommendations.append("Monitor position closely after entry")
                recommendations.append("Be prepared for early exit if conditions change")
        
        return recommendations
    
    async def _update_validation_statistics(
        self,
        decision: TradingDecision,
        result: ValidationResult
    ):
        """Update validation statistics for learning"""
        
        self.validation_statistics["total_validations"] += 1
        
        if result.is_valid:
            self.validation_statistics["successful_validations"] += 1
        else:
            self.validation_statistics["failed_validations"] += 1
        
        # Update average confidence
        total = self.validation_statistics["total_validations"]
        current_avg = self.validation_statistics["average_confidence"]
        new_confidence = result.confidence_score
        self.validation_statistics["average_confidence"] = ((current_avg * (total - 1)) + new_confidence) / total
        
        # Update decision type statistics
        decision_type = decision.decision_type.value
        if decision_type not in self.validation_statistics["decision_type_stats"]:
            self.validation_statistics["decision_type_stats"][decision_type] = {
                "total": 0, "successful": 0, "failed": 0, "avg_confidence": 0.0
            }
        
        stats = self.validation_statistics["decision_type_stats"][decision_type]
        stats["total"] += 1
        if result.is_valid:
            stats["successful"] += 1
        else:
            stats["failed"] += 1
        
        # Update decision type average confidence
        stats["avg_confidence"] = ((stats["avg_confidence"] * (stats["total"] - 1)) + new_confidence) / stats["total"]
        
        # Update common issues
        for issue in result.issues:
            issue_type = issue.get("type", "UNKNOWN")
            if issue_type not in self.validation_statistics["common_issues"]:
                self.validation_statistics["common_issues"][issue_type] = 0
            self.validation_statistics["common_issues"][issue_type] += 1
        
        # Store decision for pattern analysis
        self.decision_history.append({
            "decision": asdict(decision),
            "validation_result": asdict(result),
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only recent history (last 1000 decisions)
        if len(self.decision_history) > 1000:
            self.decision_history = self.decision_history[-1000:]
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get comprehensive validation statistics"""
        
        return {
            "validation_statistics": self.validation_statistics,
            "confidence_thresholds": {k.value: v for k, v in self.confidence_thresholds.items()},
            "risk_limits": self.risk_limits,
            "market_requirements": self.market_condition_requirements,
            "pattern_rules": self.pattern_rules,
            "recent_decisions": len(self.decision_history),
            "ai_brain_integration": AI_BRAIN_AVAILABLE,
            "last_updated": datetime.now().isoformat()
        }
    
    def get_decision_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in validated decisions"""
        
        if not self.decision_history:
            return {"error": "No decision history available"}
        
        recent_decisions = self.decision_history[-100:]  # Last 100 decisions
        
        # Analyze success patterns
        successful_decisions = [d for d in recent_decisions if d["validation_result"]["is_valid"]]
        failed_decisions = [d for d in recent_decisions if not d["validation_result"]["is_valid"]]
        
        # Confidence analysis
        success_confidences = [d["decision"]["confidence"] for d in successful_decisions]
        failed_confidences = [d["decision"]["confidence"] for d in failed_decisions]
        
        patterns = {
            "total_recent_decisions": len(recent_decisions),
            "success_rate": len(successful_decisions) / len(recent_decisions) if recent_decisions else 0,
            "confidence_patterns": {
                "successful_avg_confidence": statistics.mean(success_confidences) if success_confidences else 0,
                "failed_avg_confidence": statistics.mean(failed_confidences) if failed_confidences else 0,
                "confidence_success_correlation": self._calculate_confidence_correlation(recent_decisions)
            },
            "common_failure_reasons": self._analyze_common_failures(failed_decisions),
            "success_factors": self._analyze_success_factors(successful_decisions),
            "recommendations": self._generate_pattern_recommendations(recent_decisions)
        }
        
        return patterns
    
    def _calculate_confidence_correlation(self, decisions: List[Dict[str, Any]]) -> float:
        """Calculate correlation between confidence and success"""
        
        if len(decisions) < 5:
            return 0.0
        
        confidences = [d["decision"]["confidence"] for d in decisions]
        successes = [1 if d["validation_result"]["is_valid"] else 0 for d in decisions]
        
        try:
            correlation = np.corrcoef(confidences, successes)[0, 1]
            return correlation if not np.isnan(correlation) else 0.0
        except:
            return 0.0
    
    def _analyze_common_failures(self, failed_decisions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze common reasons for validation failures"""
        
        failure_reasons = {}
        
        for decision in failed_decisions:
            for issue in decision["validation_result"].get("issues", []):
                reason = issue.get("type", "UNKNOWN")
                if reason not in failure_reasons:
                    failure_reasons[reason] = 0
                failure_reasons[reason] += 1
        
        # Sort by frequency
        sorted_reasons = sorted(failure_reasons.items(), key=lambda x: x[1], reverse=True)
        
        return [{"reason": reason, "count": count} for reason, count in sorted_reasons[:5]]
    
    def _analyze_success_factors(self, successful_decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze factors contributing to validation success"""
        
        if not successful_decisions:
            return {}
        
        # Confidence distribution
        confidences = [d["decision"]["confidence"] for d in successful_decisions]
        
        # Strategy distribution
        strategies = [d["decision"].get("strategy_id") for d in successful_decisions if d["decision"].get("strategy_id")]
        strategy_counts = {}
        for strategy in strategies:
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        return {
            "average_confidence": statistics.mean(confidences),
            "confidence_range": {"min": min(confidences), "max": max(confidences)},
            "successful_strategies": sorted(strategy_counts.items(), key=lambda x: x[1], reverse=True)[:3],
            "success_patterns": "High confidence decisions with proper risk management tend to succeed"
        }
    
    def _generate_pattern_recommendations(self, decisions: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on decision patterns"""
        
        recommendations = []
        
        if not decisions:
            return ["No decision history available for pattern analysis"]
        
        # Calculate success rate
        success_rate = len([d for d in decisions if d["validation_result"]["is_valid"]]) / len(decisions)
        
        if success_rate < 0.7:
            recommendations.append("Low validation success rate - review decision criteria")
            recommendations.append("Consider tightening confidence thresholds")
        elif success_rate > 0.9:
            recommendations.append("High validation success rate - criteria appear well-calibrated")
            recommendations.append("Consider slightly relaxing thresholds for more opportunities")
        
        # Confidence analysis
        avg_confidence = statistics.mean([d["decision"]["confidence"] for d in decisions])
        if avg_confidence < 0.6:
            recommendations.append("Average decision confidence is low - improve prediction models")
        elif avg_confidence > 0.85:
            recommendations.append("High average confidence - ensure not over-fitting")
        
        # Common issues analysis
        all_issues = []
        for decision in decisions:
            all_issues.extend([issue.get("type", "UNKNOWN") for issue in decision["validation_result"].get("issues", [])])
        
        if all_issues:
            most_common_issue = max(set(all_issues), key=all_issues.count)
            recommendations.append(f"Most common issue: {most_common_issue} - focus on addressing this")
        
        return recommendations


# Global instance for easy import
ai_brain_trading_validator = AIBrainTradingDecisionValidator()