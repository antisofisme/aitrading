"""
Trading Engine Change Analyzer - AI Brain Enhanced Change Management System
Comprehensive change impact analysis with versioning, validation, and rollback capabilities
"""
import asyncio
import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import structlog
from pathlib import Path
import yaml

logger = structlog.get_logger(__name__)


class ChangeType(Enum):
    """Types of changes that can be analyzed"""
    STRATEGY_PARAMETER = "strategy_parameter"
    RISK_CONFIGURATION = "risk_configuration"
    TRADING_LOGIC = "trading_logic"
    SYSTEM_CONFIGURATION = "system_configuration"
    AI_MODEL_UPDATE = "ai_model_update"
    DEPENDENCY_UPDATE = "dependency_update"


class ChangeRiskLevel(Enum):
    """Risk levels for changes"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ChangeStatus(Enum):
    """Status of changes"""
    PROPOSED = "proposed"
    VALIDATED = "validated"
    APPROVED = "approved"
    DEPLOYED = "deployed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


@dataclass
class ChangeRequest:
    """Change request data structure"""
    change_id: str
    change_type: ChangeType
    description: str
    proposed_by: str
    timestamp: datetime
    old_config: Dict[str, Any]
    new_config: Dict[str, Any]
    risk_level: ChangeRiskLevel
    status: ChangeStatus
    approval_required: bool
    test_results: Dict[str, Any] = None
    impact_analysis: Dict[str, Any] = None
    dependencies: List[str] = None
    rollback_plan: Dict[str, Any] = None


@dataclass
class ChangeImpactAnalysis:
    """Comprehensive change impact analysis results"""
    change_id: str
    impact_score: float  # 0-100
    affected_components: List[str]
    performance_impact: Dict[str, float]
    risk_factors: List[str]
    mitigation_strategies: List[str]
    estimated_downtime: float  # seconds
    rollback_complexity: int  # 1-10
    dependency_conflicts: List[str]
    ai_brain_confidence: float  # 0-1


class ConfigurationVersionManager:
    """Manages configuration versions and rollback capabilities"""
    
    def __init__(self, config_path: str = "config_versions"):
        self.config_path = Path(config_path)
        self.config_path.mkdir(exist_ok=True)
        self.current_version = self._get_current_version()
        
    async def create_version(self, config: Dict[str, Any], change_id: str) -> str:
        """Create new configuration version"""
        try:
            version_id = f"v{int(time.time())}_{change_id[:8]}"
            version_file = self.config_path / f"{version_id}.yaml"
            
            version_data = {
                "version_id": version_id,
                "change_id": change_id,
                "timestamp": datetime.now().isoformat(),
                "config": config,
                "checksum": hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
            }
            
            with open(version_file, 'w') as f:
                yaml.dump(version_data, f, default_flow_style=False)
                
            logger.info("Configuration version created", version_id=version_id, change_id=change_id)
            return version_id
            
        except Exception as e:
            logger.error("Failed to create configuration version", error=str(e), change_id=change_id)
            raise
    
    async def get_version(self, version_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve specific configuration version"""
        try:
            version_file = self.config_path / f"{version_id}.yaml"
            if not version_file.exists():
                return None
                
            with open(version_file, 'r') as f:
                return yaml.safe_load(f)
                
        except Exception as e:
            logger.error("Failed to retrieve configuration version", error=str(e), version_id=version_id)
            return None
    
    async def list_versions(self) -> List[Dict[str, Any]]:
        """List all configuration versions"""
        try:
            versions = []
            for version_file in self.config_path.glob("*.yaml"):
                with open(version_file, 'r') as f:
                    version_data = yaml.safe_load(f)
                    versions.append({
                        "version_id": version_data["version_id"],
                        "change_id": version_data["change_id"],
                        "timestamp": version_data["timestamp"]
                    })
            
            return sorted(versions, key=lambda x: x["timestamp"], reverse=True)
            
        except Exception as e:
            logger.error("Failed to list configuration versions", error=str(e))
            return []
    
    def _get_current_version(self) -> str:
        """Get current configuration version"""
        try:
            current_file = self.config_path / "current.txt"
            if current_file.exists():
                with open(current_file, 'r') as f:
                    return f.read().strip()
            return "v0_initial"
        except Exception:
            return "v0_initial"


class ChangeValidationPipeline:
    """Automated change validation and testing pipeline"""
    
    def __init__(self):
        self.validators = []
        self.test_suites = []
        
    async def validate_change(self, change_request: ChangeRequest) -> Dict[str, Any]:
        """Run comprehensive validation on change request"""
        try:
            validation_results = {
                "change_id": change_request.change_id,
                "overall_valid": True,
                "validation_score": 0.0,
                "checks": [],
                "warnings": [],
                "errors": []
            }
            
            # Syntax validation
            syntax_result = await self._validate_syntax(change_request)
            validation_results["checks"].append(syntax_result)
            
            # Dependency validation
            dependency_result = await self._validate_dependencies(change_request)
            validation_results["checks"].append(dependency_result)
            
            # Risk assessment validation
            risk_result = await self._validate_risk_level(change_request)
            validation_results["checks"].append(risk_result)
            
            # Performance impact validation
            performance_result = await self._validate_performance_impact(change_request)
            validation_results["checks"].append(performance_result)
            
            # Calculate overall validation score
            total_score = sum(check["score"] for check in validation_results["checks"])
            validation_results["validation_score"] = total_score / len(validation_results["checks"])
            validation_results["overall_valid"] = validation_results["validation_score"] >= 0.8
            
            logger.info("Change validation completed", 
                       change_id=change_request.change_id,
                       score=validation_results["validation_score"],
                       valid=validation_results["overall_valid"])
            
            return validation_results
            
        except Exception as e:
            logger.error("Change validation failed", error=str(e), change_id=change_request.change_id)
            return {
                "change_id": change_request.change_id,
                "overall_valid": False,
                "validation_score": 0.0,
                "errors": [f"Validation pipeline error: {str(e)}"]
            }
    
    async def _validate_syntax(self, change_request: ChangeRequest) -> Dict[str, Any]:
        """Validate configuration syntax"""
        try:
            # Validate JSON/YAML structure
            json.dumps(change_request.new_config)
            return {
                "check": "syntax_validation",
                "passed": True,
                "score": 1.0,
                "message": "Configuration syntax is valid"
            }
        except Exception as e:
            return {
                "check": "syntax_validation",
                "passed": False,
                "score": 0.0,
                "message": f"Syntax error: {str(e)}"
            }
    
    async def _validate_dependencies(self, change_request: ChangeRequest) -> Dict[str, Any]:
        """Validate change dependencies"""
        try:
            # Check for dependency conflicts
            conflicts = []
            if change_request.dependencies:
                # Simulate dependency checking
                for dep in change_request.dependencies:
                    if "conflict" in dep.lower():
                        conflicts.append(dep)
            
            score = 1.0 if not conflicts else max(0.0, 1.0 - len(conflicts) * 0.2)
            return {
                "check": "dependency_validation",
                "passed": len(conflicts) == 0,
                "score": score,
                "message": f"Found {len(conflicts)} dependency conflicts" if conflicts else "No dependency conflicts"
            }
        except Exception as e:
            return {
                "check": "dependency_validation",
                "passed": False,
                "score": 0.0,
                "message": f"Dependency validation error: {str(e)}"
            }
    
    async def _validate_risk_level(self, change_request: ChangeRequest) -> Dict[str, Any]:
        """Validate risk level assessment"""
        try:
            # Risk level validation based on change type
            risk_scores = {
                ChangeRiskLevel.LOW: 1.0,
                ChangeRiskLevel.MEDIUM: 0.8,
                ChangeRiskLevel.HIGH: 0.6,
                ChangeRiskLevel.CRITICAL: 0.4
            }
            
            score = risk_scores.get(change_request.risk_level, 0.5)
            return {
                "check": "risk_level_validation",
                "passed": True,
                "score": score,
                "message": f"Risk level: {change_request.risk_level.value}"
            }
        except Exception as e:
            return {
                "check": "risk_level_validation",
                "passed": False,
                "score": 0.0,
                "message": f"Risk validation error: {str(e)}"
            }
    
    async def _validate_performance_impact(self, change_request: ChangeRequest) -> Dict[str, Any]:
        """Validate performance impact"""
        try:
            # Estimate performance impact
            impact_factors = {
                ChangeType.STRATEGY_PARAMETER: 0.1,
                ChangeType.RISK_CONFIGURATION: 0.2,
                ChangeType.TRADING_LOGIC: 0.4,
                ChangeType.SYSTEM_CONFIGURATION: 0.3,
                ChangeType.AI_MODEL_UPDATE: 0.5,
                ChangeType.DEPENDENCY_UPDATE: 0.6
            }
            
            impact = impact_factors.get(change_request.change_type, 0.3)
            score = max(0.0, 1.0 - impact)
            
            return {
                "check": "performance_impact_validation",
                "passed": impact < 0.5,
                "score": score,
                "message": f"Estimated performance impact: {impact:.1%}"
            }
        except Exception as e:
            return {
                "check": "performance_impact_validation",
                "passed": False,
                "score": 0.0,
                "message": f"Performance validation error: {str(e)}"
            }


class ABTestingFramework:
    """A/B testing framework for strategy changes"""
    
    def __init__(self):
        self.active_tests = {}
        self.test_history = []
        
    async def create_ab_test(self, change_request: ChangeRequest, 
                           traffic_split: float = 0.1) -> str:
        """Create A/B test for strategy change"""
        try:
            test_id = f"ab_{change_request.change_id}_{int(time.time())}"
            
            ab_test = {
                "test_id": test_id,
                "change_id": change_request.change_id,
                "start_time": datetime.now(),
                "end_time": datetime.now() + timedelta(days=7),  # Default 7 day test
                "traffic_split": traffic_split,
                "control_config": change_request.old_config,
                "treatment_config": change_request.new_config,
                "status": "running",
                "metrics": {
                    "control": {"trades": 0, "profit": 0.0, "drawdown": 0.0},
                    "treatment": {"trades": 0, "profit": 0.0, "drawdown": 0.0}
                }
            }
            
            self.active_tests[test_id] = ab_test
            
            logger.info("A/B test created", test_id=test_id, 
                       change_id=change_request.change_id, 
                       traffic_split=traffic_split)
            
            return test_id
            
        except Exception as e:
            logger.error("Failed to create A/B test", error=str(e), 
                        change_id=change_request.change_id)
            raise
    
    async def update_test_metrics(self, test_id: str, variant: str, 
                                 metrics: Dict[str, float]) -> bool:
        """Update A/B test metrics"""
        try:
            if test_id not in self.active_tests:
                return False
                
            test = self.active_tests[test_id]
            if variant in test["metrics"]:
                for metric, value in metrics.items():
                    if metric in test["metrics"][variant]:
                        test["metrics"][variant][metric] += value
                    else:
                        test["metrics"][variant][metric] = value
                        
            logger.debug("A/B test metrics updated", test_id=test_id, 
                        variant=variant, metrics=metrics)
            return True
            
        except Exception as e:
            logger.error("Failed to update A/B test metrics", error=str(e), 
                        test_id=test_id)
            return False
    
    async def analyze_ab_test(self, test_id: str) -> Dict[str, Any]:
        """Analyze A/B test results"""
        try:
            if test_id not in self.active_tests:
                return {"error": "Test not found"}
                
            test = self.active_tests[test_id]
            control = test["metrics"]["control"]
            treatment = test["metrics"]["treatment"]
            
            # Calculate performance differences
            profit_improvement = ((treatment["profit"] - control["profit"]) / 
                                max(abs(control["profit"]), 0.01)) * 100
            drawdown_change = treatment["drawdown"] - control["drawdown"]
            
            # Statistical significance (simplified)
            sample_size = control["trades"] + treatment["trades"]
            significance = min(0.99, sample_size / 1000.0)  # Simplified calculation
            
            analysis = {
                "test_id": test_id,
                "status": test["status"],
                "duration_days": (datetime.now() - test["start_time"]).days,
                "control_metrics": control,
                "treatment_metrics": treatment,
                "performance_delta": {
                    "profit_improvement_percent": profit_improvement,
                    "drawdown_change": drawdown_change,
                    "trade_count_delta": treatment["trades"] - control["trades"]
                },
                "statistical_significance": significance,
                "recommendation": self._get_ab_recommendation(profit_improvement, 
                                                            drawdown_change, 
                                                            significance)
            }
            
            logger.info("A/B test analysis completed", test_id=test_id, 
                       recommendation=analysis["recommendation"])
            
            return analysis
            
        except Exception as e:
            logger.error("A/B test analysis failed", error=str(e), test_id=test_id)
            return {"error": str(e)}
    
    def _get_ab_recommendation(self, profit_improvement: float, 
                              drawdown_change: float, significance: float) -> str:
        """Get recommendation based on A/B test results"""
        if significance < 0.8:
            return "insufficient_data"
        elif profit_improvement > 5 and drawdown_change < 2:
            return "deploy_treatment"
        elif profit_improvement < -5 or drawdown_change > 5:
            return "reject_treatment"
        else:
            return "continue_testing"


class ChangeRiskAssessment:
    """Comprehensive risk assessment for changes"""
    
    def __init__(self):
        self.risk_matrix = self._initialize_risk_matrix()
        
    async def assess_change_risk(self, change_request: ChangeRequest) -> Dict[str, Any]:
        """Assess comprehensive risk for change request"""
        try:
            risk_assessment = {
                "change_id": change_request.change_id,
                "overall_risk_score": 0.0,
                "risk_level": ChangeRiskLevel.LOW,
                "risk_factors": [],
                "mitigation_strategies": [],
                "approval_required": False
            }
            
            # Assess multiple risk dimensions
            risk_factors = []
            
            # Technical risk
            tech_risk = await self._assess_technical_risk(change_request)
            risk_factors.append(tech_risk)
            
            # Business risk
            business_risk = await self._assess_business_risk(change_request)
            risk_factors.append(business_risk)
            
            # Operational risk
            operational_risk = await self._assess_operational_risk(change_request)
            risk_factors.append(operational_risk)
            
            # Security risk
            security_risk = await self._assess_security_risk(change_request)
            risk_factors.append(security_risk)
            
            # Calculate overall risk score
            total_risk = sum(factor["score"] for factor in risk_factors)
            risk_assessment["overall_risk_score"] = total_risk / len(risk_factors)
            
            # Determine risk level
            if risk_assessment["overall_risk_score"] >= 0.8:
                risk_assessment["risk_level"] = ChangeRiskLevel.CRITICAL
                risk_assessment["approval_required"] = True
            elif risk_assessment["overall_risk_score"] >= 0.6:
                risk_assessment["risk_level"] = ChangeRiskLevel.HIGH
                risk_assessment["approval_required"] = True
            elif risk_assessment["overall_risk_score"] >= 0.4:
                risk_assessment["risk_level"] = ChangeRiskLevel.MEDIUM
            else:
                risk_assessment["risk_level"] = ChangeRiskLevel.LOW
            
            risk_assessment["risk_factors"] = [f["description"] for f in risk_factors]
            risk_assessment["mitigation_strategies"] = self._get_mitigation_strategies(
                risk_assessment["risk_level"], change_request.change_type
            )
            
            logger.info("Change risk assessment completed", 
                       change_id=change_request.change_id,
                       risk_score=risk_assessment["overall_risk_score"],
                       risk_level=risk_assessment["risk_level"].value)
            
            return risk_assessment
            
        except Exception as e:
            logger.error("Change risk assessment failed", error=str(e), 
                        change_id=change_request.change_id)
            return {
                "change_id": change_request.change_id,
                "overall_risk_score": 1.0,  # Assume maximum risk on error
                "risk_level": ChangeRiskLevel.CRITICAL,
                "risk_factors": [f"Assessment error: {str(e)}"],
                "approval_required": True
            }
    
    async def _assess_technical_risk(self, change_request: ChangeRequest) -> Dict[str, Any]:
        """Assess technical risk factors"""
        risk_score = 0.0
        factors = []
        
        # Change complexity
        if change_request.change_type in [ChangeType.TRADING_LOGIC, ChangeType.AI_MODEL_UPDATE]:
            risk_score += 0.3
            factors.append("Complex algorithmic changes")
        
        # Dependency impact
        if change_request.dependencies and len(change_request.dependencies) > 3:
            risk_score += 0.2
            factors.append("Multiple dependency changes")
        
        # Configuration size
        config_size = len(json.dumps(change_request.new_config))
        if config_size > 10000:  # Large configuration changes
            risk_score += 0.2
            factors.append("Large configuration changes")
        
        return {
            "category": "technical",
            "score": min(1.0, risk_score),
            "factors": factors,
            "description": f"Technical risk score: {risk_score:.2f}"
        }
    
    async def _assess_business_risk(self, change_request: ChangeRequest) -> Dict[str, Any]:
        """Assess business risk factors"""
        risk_score = 0.0
        factors = []
        
        # Trading hours impact
        current_hour = datetime.now().hour
        if 8 <= current_hour <= 17:  # Market hours
            risk_score += 0.3
            factors.append("Change during market hours")
        
        # Strategy impact
        if change_request.change_type == ChangeType.STRATEGY_PARAMETER:
            risk_score += 0.2
            factors.append("Direct trading strategy impact")
        
        # Risk configuration impact
        if change_request.change_type == ChangeType.RISK_CONFIGURATION:
            risk_score += 0.4
            factors.append("Risk management changes")
        
        return {
            "category": "business",
            "score": min(1.0, risk_score),
            "factors": factors,
            "description": f"Business risk score: {risk_score:.2f}"
        }
    
    async def _assess_operational_risk(self, change_request: ChangeRequest) -> Dict[str, Any]:
        """Assess operational risk factors"""
        risk_score = 0.0
        factors = []
        
        # System configuration changes
        if change_request.change_type == ChangeType.SYSTEM_CONFIGURATION:
            risk_score += 0.3
            factors.append("System-wide configuration changes")
        
        # Rollback complexity (if available in change request)
        if hasattr(change_request, 'rollback_complexity') and change_request.rollback_complexity > 7:
            risk_score += 0.3
            factors.append("Complex rollback procedure")
        
        return {
            "category": "operational",
            "score": min(1.0, risk_score),
            "factors": factors,
            "description": f"Operational risk score: {risk_score:.2f}"
        }
    
    async def _assess_security_risk(self, change_request: ChangeRequest) -> Dict[str, Any]:
        """Assess security risk factors"""
        risk_score = 0.0
        factors = []
        
        # Configuration contains sensitive data
        config_str = json.dumps(change_request.new_config).lower()
        sensitive_keywords = ["password", "key", "secret", "token", "credential"]
        
        for keyword in sensitive_keywords:
            if keyword in config_str:
                risk_score += 0.2
                factors.append(f"Contains sensitive data: {keyword}")
        
        return {
            "category": "security",
            "score": min(1.0, risk_score),
            "factors": factors,
            "description": f"Security risk score: {risk_score:.2f}"
        }
    
    def _get_mitigation_strategies(self, risk_level: ChangeRiskLevel, 
                                  change_type: ChangeType) -> List[str]:
        """Get mitigation strategies based on risk level and change type"""
        strategies = []
        
        if risk_level in [ChangeRiskLevel.HIGH, ChangeRiskLevel.CRITICAL]:
            strategies.extend([
                "Require senior approval before deployment",
                "Deploy during off-market hours",
                "Implement gradual rollout with monitoring",
                "Prepare detailed rollback plan"
            ])
        
        if risk_level == ChangeRiskLevel.CRITICAL:
            strategies.extend([
                "Conduct full system backup before deployment",
                "Implement blue-green deployment strategy",
                "Require multiple approvals from different teams"
            ])
        
        if change_type in [ChangeType.TRADING_LOGIC, ChangeType.AI_MODEL_UPDATE]:
            strategies.append("Conduct extensive backtesting before deployment")
        
        return strategies
    
    def _initialize_risk_matrix(self) -> Dict[str, Dict[str, float]]:
        """Initialize risk assessment matrix"""
        return {
            "change_types": {
                ChangeType.STRATEGY_PARAMETER.value: 0.3,
                ChangeType.RISK_CONFIGURATION.value: 0.6,
                ChangeType.TRADING_LOGIC.value: 0.8,
                ChangeType.SYSTEM_CONFIGURATION.value: 0.5,
                ChangeType.AI_MODEL_UPDATE.value: 0.7,
                ChangeType.DEPENDENCY_UPDATE.value: 0.4
            }
        }


class TradingEngineChangeAnalyzer:
    """
    Comprehensive Change Analyzer for Trading Engine
    AI Brain Enhanced Change Management System
    """
    
    def __init__(self):
        self.version_manager = ConfigurationVersionManager()
        self.validation_pipeline = ChangeValidationPipeline()
        self.ab_testing = ABTestingFramework()
        self.risk_assessment = ChangeRiskAssessment()
        self.change_history = []
        self.active_changes = {}
        
    async def analyze_change(self, change_request: ChangeRequest) -> ChangeImpactAnalysis:
        """
        Comprehensive change impact analysis
        """
        try:
            logger.info("Starting comprehensive change analysis", 
                       change_id=change_request.change_id,
                       change_type=change_request.change_type.value)
            
            # 1. Validate change request
            validation_results = await self.validation_pipeline.validate_change(change_request)
            
            # 2. Assess risk
            risk_results = await self.risk_assessment.assess_change_risk(change_request)
            
            # 3. Analyze dependencies
            dependency_analysis = await self._analyze_dependencies(change_request)
            
            # 4. Estimate performance impact
            performance_impact = await self._estimate_performance_impact(change_request)
            
            # 5. Calculate AI Brain confidence
            ai_brain_confidence = await self._calculate_ai_brain_confidence(
                validation_results, risk_results, dependency_analysis
            )
            
            # 6. Generate comprehensive impact analysis
            impact_analysis = ChangeImpactAnalysis(
                change_id=change_request.change_id,
                impact_score=self._calculate_impact_score(
                    validation_results["validation_score"],
                    risk_results["overall_risk_score"],
                    dependency_analysis["complexity_score"]
                ),
                affected_components=dependency_analysis["affected_components"],
                performance_impact=performance_impact,
                risk_factors=risk_results["risk_factors"],
                mitigation_strategies=risk_results["mitigation_strategies"],
                estimated_downtime=self._estimate_downtime(change_request),
                rollback_complexity=self._assess_rollback_complexity(change_request),
                dependency_conflicts=dependency_analysis["conflicts"],
                ai_brain_confidence=ai_brain_confidence
            )
            
            # Store analysis results
            change_request.impact_analysis = asdict(impact_analysis)
            self.active_changes[change_request.change_id] = change_request
            
            logger.info("Change analysis completed", 
                       change_id=change_request.change_id,
                       impact_score=impact_analysis.impact_score,
                       ai_brain_confidence=impact_analysis.ai_brain_confidence)
            
            return impact_analysis
            
        except Exception as e:
            logger.error("Change analysis failed", error=str(e), 
                        change_id=change_request.change_id)
            raise
    
    async def create_ab_test(self, change_request: ChangeRequest, 
                           traffic_split: float = 0.1) -> str:
        """Create A/B test for change validation"""
        try:
            test_id = await self.ab_testing.create_ab_test(change_request, traffic_split)
            
            # Update change request with A/B test information
            if not change_request.test_results:
                change_request.test_results = {}
            change_request.test_results["ab_test_id"] = test_id
            
            logger.info("A/B test created for change", 
                       change_id=change_request.change_id,
                       test_id=test_id)
            
            return test_id
            
        except Exception as e:
            logger.error("Failed to create A/B test for change", error=str(e), 
                        change_id=change_request.change_id)
            raise
    
    async def deploy_change(self, change_id: str) -> bool:
        """Deploy approved change with comprehensive monitoring"""
        try:
            if change_id not in self.active_changes:
                logger.error("Change not found", change_id=change_id)
                return False
            
            change_request = self.active_changes[change_id]
            
            # Verify change is approved and validated
            if change_request.status != ChangeStatus.APPROVED:
                logger.error("Change not approved for deployment", 
                           change_id=change_id, status=change_request.status.value)
                return False
            
            # Create configuration version backup
            current_version = await self.version_manager.create_version(
                change_request.old_config, change_id
            )
            
            # Deploy new configuration
            new_version = await self.version_manager.create_version(
                change_request.new_config, f"{change_id}_deployed"
            )
            
            # Update change status
            change_request.status = ChangeStatus.DEPLOYED
            
            # Record deployment in history
            self.change_history.append({
                "change_id": change_id,
                "action": "deployed",
                "timestamp": datetime.now(),
                "old_version": current_version,
                "new_version": new_version
            })
            
            logger.info("Change deployed successfully", 
                       change_id=change_id,
                       old_version=current_version,
                       new_version=new_version)
            
            return True
            
        except Exception as e:
            logger.error("Change deployment failed", error=str(e), change_id=change_id)
            return False
    
    async def rollback_change(self, change_id: str) -> bool:
        """Rollback deployed change"""
        try:
            if change_id not in self.active_changes:
                logger.error("Change not found for rollback", change_id=change_id)
                return False
            
            change_request = self.active_changes[change_id]
            
            if change_request.status != ChangeStatus.DEPLOYED:
                logger.error("Change not in deployed state", 
                           change_id=change_id, status=change_request.status.value)
                return False
            
            # Create rollback version
            rollback_version = await self.version_manager.create_version(
                change_request.old_config, f"{change_id}_rollback"
            )
            
            # Update change status
            change_request.status = ChangeStatus.ROLLED_BACK
            
            # Record rollback in history
            self.change_history.append({
                "change_id": change_id,
                "action": "rolled_back",
                "timestamp": datetime.now(),
                "rollback_version": rollback_version
            })
            
            logger.info("Change rolled back successfully", 
                       change_id=change_id,
                       rollback_version=rollback_version)
            
            return True
            
        except Exception as e:
            logger.error("Change rollback failed", error=str(e), change_id=change_id)
            return False
    
    async def get_change_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get change history with filtering"""
        try:
            # Return recent change history
            recent_history = sorted(
                self.change_history, 
                key=lambda x: x["timestamp"], 
                reverse=True
            )[:limit]
            
            # Format for API response
            formatted_history = []
            for entry in recent_history:
                formatted_entry = {
                    "change_id": entry["change_id"],
                    "action": entry["action"],
                    "timestamp": entry["timestamp"].isoformat(),
                }
                
                # Add version information if available
                if "old_version" in entry:
                    formatted_entry["old_version"] = entry["old_version"]
                if "new_version" in entry:
                    formatted_entry["new_version"] = entry["new_version"]
                if "rollback_version" in entry:
                    formatted_entry["rollback_version"] = entry["rollback_version"]
                
                formatted_history.append(formatted_entry)
            
            return formatted_history
            
        except Exception as e:
            logger.error("Failed to retrieve change history", error=str(e))
            return []
    
    async def monitor_change_performance(self, change_id: str) -> Dict[str, Any]:
        """Monitor performance impact of deployed changes"""
        try:
            if change_id not in self.active_changes:
                return {"error": "Change not found"}
            
            change_request = self.active_changes[change_id]
            
            if change_request.status != ChangeStatus.DEPLOYED:
                return {"error": "Change not deployed"}
            
            # Get deployment timestamp from history
            deployment_time = None
            for entry in self.change_history:
                if entry["change_id"] == change_id and entry["action"] == "deployed":
                    deployment_time = entry["timestamp"]
                    break
            
            if not deployment_time:
                return {"error": "Deployment time not found"}
            
            # Calculate monitoring period
            monitoring_duration = datetime.now() - deployment_time
            
            # Simulate performance monitoring (in real implementation, 
            # this would connect to actual monitoring systems)
            performance_metrics = {
                "change_id": change_id,
                "monitoring_duration_hours": monitoring_duration.total_seconds() / 3600,
                "deployment_time": deployment_time.isoformat(),
                "metrics": {
                    "latency_ms": 45.2 + (monitoring_duration.total_seconds() * 0.001),
                    "throughput_tps": 1250 - (monitoring_duration.total_seconds() * 0.01),
                    "error_rate_percent": 0.05,
                    "memory_usage_mb": 512 + (monitoring_duration.total_seconds() * 0.1),
                    "cpu_usage_percent": 15.5
                },
                "alerts": [],
                "recommendations": []
            }
            
            # Check for performance degradation
            if performance_metrics["metrics"]["latency_ms"] > 100:
                performance_metrics["alerts"].append({
                    "type": "performance",
                    "severity": "warning",
                    "message": "Latency increase detected after change deployment"
                })
                performance_metrics["recommendations"].append(
                    "Consider rollback if latency continues to increase"
                )
            
            return performance_metrics
            
        except Exception as e:
            logger.error("Performance monitoring failed", error=str(e), change_id=change_id)
            return {"error": str(e)}
    
    # Helper methods
    async def _analyze_dependencies(self, change_request: ChangeRequest) -> Dict[str, Any]:
        """Analyze change dependencies and conflicts"""
        try:
            affected_components = []
            conflicts = []
            complexity_score = 0.0
            
            # Analyze based on change type
            if change_request.change_type == ChangeType.STRATEGY_PARAMETER:
                affected_components.extend(["strategy_executor", "risk_manager", "performance_analytics"])
                complexity_score = 0.3
            elif change_request.change_type == ChangeType.RISK_CONFIGURATION:
                affected_components.extend(["risk_manager", "trading_engine", "portfolio_manager"])
                complexity_score = 0.5
            elif change_request.change_type == ChangeType.TRADING_LOGIC:
                affected_components.extend(["ai_trading_engine", "strategy_executor", "technical_analysis"])
                complexity_score = 0.8
            elif change_request.change_type == ChangeType.SYSTEM_CONFIGURATION:
                affected_components.extend(["core_system", "logging", "monitoring", "database"])
                complexity_score = 0.6
            elif change_request.change_type == ChangeType.AI_MODEL_UPDATE:
                affected_components.extend(["ai_models", "inference_engine", "feature_processing"])
                complexity_score = 0.7
            
            # Check for potential conflicts (simplified logic)
            if change_request.dependencies:
                for dep in change_request.dependencies:
                    if "conflict" in dep.lower() or "incompatible" in dep.lower():
                        conflicts.append(dep)
                        complexity_score += 0.2
            
            return {
                "affected_components": affected_components,
                "conflicts": conflicts,
                "complexity_score": min(1.0, complexity_score)
            }
            
        except Exception as e:
            logger.error("Dependency analysis failed", error=str(e))
            return {
                "affected_components": [],
                "conflicts": [],
                "complexity_score": 1.0  # Assume high complexity on error
            }
    
    async def _estimate_performance_impact(self, change_request: ChangeRequest) -> Dict[str, float]:
        """Estimate performance impact of change"""
        try:
            impact_factors = {
                ChangeType.STRATEGY_PARAMETER: {"latency": 0.05, "throughput": -0.02, "memory": 0.03},
                ChangeType.RISK_CONFIGURATION: {"latency": 0.03, "throughput": -0.01, "memory": 0.02},
                ChangeType.TRADING_LOGIC: {"latency": 0.15, "throughput": -0.08, "memory": 0.10},
                ChangeType.SYSTEM_CONFIGURATION: {"latency": 0.08, "throughput": -0.05, "memory": 0.06},
                ChangeType.AI_MODEL_UPDATE: {"latency": 0.20, "throughput": -0.10, "memory": 0.15},
                ChangeType.DEPENDENCY_UPDATE: {"latency": 0.10, "throughput": -0.05, "memory": 0.08}
            }
            
            base_impact = impact_factors.get(change_request.change_type, 
                                           {"latency": 0.05, "throughput": -0.03, "memory": 0.04})
            
            # Adjust based on configuration size
            config_size_factor = min(2.0, len(json.dumps(change_request.new_config)) / 5000)
            
            return {
                "latency_impact_percent": base_impact["latency"] * config_size_factor * 100,
                "throughput_impact_percent": base_impact["throughput"] * config_size_factor * 100,
                "memory_impact_percent": base_impact["memory"] * config_size_factor * 100,
                "overall_impact_score": ((abs(base_impact["latency"]) + 
                                        abs(base_impact["throughput"]) + 
                                        abs(base_impact["memory"])) / 3) * config_size_factor
            }
            
        except Exception as e:
            logger.error("Performance impact estimation failed", error=str(e))
            return {
                "latency_impact_percent": 10.0,
                "throughput_impact_percent": -5.0,
                "memory_impact_percent": 8.0,
                "overall_impact_score": 0.5
            }
    
    async def _calculate_ai_brain_confidence(self, validation_results: Dict[str, Any],
                                           risk_results: Dict[str, Any],
                                           dependency_analysis: Dict[str, Any]) -> float:
        """Calculate AI Brain confidence score for change"""
        try:
            # Weight different factors
            validation_weight = 0.4
            risk_weight = 0.3
            dependency_weight = 0.3
            
            # Calculate confidence components
            validation_confidence = validation_results["validation_score"]
            risk_confidence = 1.0 - risk_results["overall_risk_score"]  # Inverse of risk
            dependency_confidence = 1.0 - dependency_analysis["complexity_score"]  # Inverse of complexity
            
            # Calculate weighted confidence
            ai_brain_confidence = (
                validation_confidence * validation_weight +
                risk_confidence * risk_weight +
                dependency_confidence * dependency_weight
            )
            
            return max(0.0, min(1.0, ai_brain_confidence))
            
        except Exception as e:
            logger.error("AI Brain confidence calculation failed", error=str(e))
            return 0.5  # Default moderate confidence
    
    def _calculate_impact_score(self, validation_score: float, 
                               risk_score: float, complexity_score: float) -> float:
        """Calculate overall impact score (0-100)"""
        try:
            # Higher validation score reduces impact
            # Higher risk score increases impact
            # Higher complexity increases impact
            
            base_impact = 50.0  # Base impact score
            validation_adjustment = (1.0 - validation_score) * 20  # 0-20 point adjustment
            risk_adjustment = risk_score * 20  # 0-20 point adjustment
            complexity_adjustment = complexity_score * 10  # 0-10 point adjustment
            
            impact_score = base_impact + validation_adjustment + risk_adjustment + complexity_adjustment
            
            return max(0.0, min(100.0, impact_score))
            
        except Exception:
            return 50.0  # Default moderate impact
    
    def _estimate_downtime(self, change_request: ChangeRequest) -> float:
        """Estimate potential downtime in seconds"""
        try:
            downtime_estimates = {
                ChangeType.STRATEGY_PARAMETER: 5.0,  # 5 seconds
                ChangeType.RISK_CONFIGURATION: 10.0,  # 10 seconds
                ChangeType.TRADING_LOGIC: 30.0,  # 30 seconds
                ChangeType.SYSTEM_CONFIGURATION: 60.0,  # 1 minute
                ChangeType.AI_MODEL_UPDATE: 120.0,  # 2 minutes
                ChangeType.DEPENDENCY_UPDATE: 180.0  # 3 minutes
            }
            
            base_downtime = downtime_estimates.get(change_request.change_type, 30.0)
            
            # Adjust based on configuration complexity
            config_complexity = len(json.dumps(change_request.new_config)) / 1000.0
            complexity_multiplier = max(1.0, min(3.0, config_complexity))
            
            return base_downtime * complexity_multiplier
            
        except Exception:
            return 60.0  # Default 1 minute estimate
    
    def _assess_rollback_complexity(self, change_request: ChangeRequest) -> int:
        """Assess rollback complexity (1-10 scale)"""
        try:
            complexity_scores = {
                ChangeType.STRATEGY_PARAMETER: 2,
                ChangeType.RISK_CONFIGURATION: 3,
                ChangeType.TRADING_LOGIC: 7,
                ChangeType.SYSTEM_CONFIGURATION: 5,
                ChangeType.AI_MODEL_UPDATE: 8,
                ChangeType.DEPENDENCY_UPDATE: 6
            }
            
            base_complexity = complexity_scores.get(change_request.change_type, 5)
            
            # Adjust for dependencies
            if change_request.dependencies:
                dependency_adjustment = min(3, len(change_request.dependencies))
                base_complexity += dependency_adjustment
            
            return max(1, min(10, base_complexity))
            
        except Exception:
            return 5  # Default moderate complexity