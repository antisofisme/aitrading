"""
Trading Engine Change Management API Endpoints
AI Brain Enhanced Change Management REST API
"""
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field, validator
import structlog

from ..business.change_analyzer import (
    TradingEngineChangeAnalyzer,
    ChangeRequest,
    ChangeType,
    ChangeRiskLevel,
    ChangeStatus,
    ChangeImpactAnalysis
)

logger = structlog.get_logger(__name__)

# Initialize Change Management Router
router = APIRouter(prefix="/api/v1/change-management", tags=["Change Management"])

# Initialize Change Analyzer
change_analyzer = TradingEngineChangeAnalyzer()


# Pydantic Models for API
class ChangeRequestModel(BaseModel):
    """Change request input model"""
    change_type: str = Field(..., description="Type of change")
    description: str = Field(..., min_length=10, max_length=500, description="Change description")
    proposed_by: str = Field(..., description="User proposing the change")
    old_config: Dict[str, Any] = Field(..., description="Current configuration")
    new_config: Dict[str, Any] = Field(..., description="New configuration")
    dependencies: Optional[List[str]] = Field(default=[], description="Change dependencies")
    
    @validator('change_type')
    def validate_change_type(cls, v):
        valid_types = [ct.value for ct in ChangeType]
        if v not in valid_types:
            raise ValueError(f'change_type must be one of: {valid_types}')
        return v


class ABTestRequestModel(BaseModel):
    """A/B test request model"""
    change_id: str = Field(..., description="Change ID to test")
    traffic_split: float = Field(default=0.1, ge=0.01, le=0.5, description="Traffic split for test")
    duration_days: int = Field(default=7, ge=1, le=30, description="Test duration in days")


class ChangeApprovalModel(BaseModel):
    """Change approval model"""
    change_id: str = Field(..., description="Change ID to approve")
    approved_by: str = Field(..., description="User approving the change")
    approval_reason: str = Field(..., description="Reason for approval")


class ChangeHistoryFilter(BaseModel):
    """Change history filter model"""
    limit: int = Field(default=50, ge=1, le=1000, description="Number of records to return")
    change_type: Optional[str] = Field(default=None, description="Filter by change type")
    status: Optional[str] = Field(default=None, description="Filter by status")
    date_from: Optional[datetime] = Field(default=None, description="Filter from date")
    date_to: Optional[datetime] = Field(default=None, description="Filter to date")


# Change Management Endpoints

@router.post("/analyze-change", response_model=Dict[str, Any])
async def analyze_change(change_request: ChangeRequestModel) -> Dict[str, Any]:
    """
    Analyze change request with comprehensive impact analysis
    """
    try:
        logger.info("Analyzing change request", 
                   change_type=change_request.change_type,
                   proposed_by=change_request.proposed_by)
        
        # Convert to internal change request
        internal_change = ChangeRequest(
            change_id=f"CHG_{int(datetime.now().timestamp())}",
            change_type=ChangeType(change_request.change_type),
            description=change_request.description,
            proposed_by=change_request.proposed_by,
            timestamp=datetime.now(),
            old_config=change_request.old_config,
            new_config=change_request.new_config,
            risk_level=ChangeRiskLevel.LOW,  # Will be assessed
            status=ChangeStatus.PROPOSED,
            approval_required=False,  # Will be determined by risk assessment
            dependencies=change_request.dependencies or []
        )
        
        # Perform comprehensive analysis
        impact_analysis = await change_analyzer.analyze_change(internal_change)
        
        # Format response
        response = {
            "change_id": impact_analysis.change_id,
            "analysis_timestamp": datetime.now().isoformat(),
            "impact_analysis": {
                "impact_score": impact_analysis.impact_score,
                "ai_brain_confidence": impact_analysis.ai_brain_confidence,
                "affected_components": impact_analysis.affected_components,
                "performance_impact": impact_analysis.performance_impact,
                "estimated_downtime_seconds": impact_analysis.estimated_downtime,
                "rollback_complexity": impact_analysis.rollback_complexity
            },
            "risk_assessment": {
                "risk_factors": impact_analysis.risk_factors,
                "mitigation_strategies": impact_analysis.mitigation_strategies,
                "dependency_conflicts": impact_analysis.dependency_conflicts
            },
            "recommendations": {
                "proceed": impact_analysis.ai_brain_confidence >= 0.8,
                "requires_approval": impact_analysis.impact_score >= 60,
                "requires_ab_test": impact_analysis.impact_score >= 40,
                "deployment_window": "off_hours" if impact_analysis.impact_score >= 50 else "any_time"
            },
            "next_steps": _get_next_steps(impact_analysis)
        }
        
        logger.info("Change analysis completed", 
                   change_id=impact_analysis.change_id,
                   impact_score=impact_analysis.impact_score,
                   ai_brain_confidence=impact_analysis.ai_brain_confidence)
        
        return response
        
    except Exception as e:
        logger.error("Change analysis failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Change analysis failed: {str(e)}"
        )


@router.post("/create-ab-test", response_model=Dict[str, Any])
async def create_ab_test(ab_request: ABTestRequestModel) -> Dict[str, Any]:
    """
    Create A/B test for change validation
    """
    try:
        logger.info("Creating A/B test", 
                   change_id=ab_request.change_id,
                   traffic_split=ab_request.traffic_split)
        
        # Get change request from active changes
        if ab_request.change_id not in change_analyzer.active_changes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Change {ab_request.change_id} not found"
            )
        
        change_request = change_analyzer.active_changes[ab_request.change_id]
        
        # Create A/B test
        test_id = await change_analyzer.create_ab_test(change_request, ab_request.traffic_split)
        
        response = {
            "test_id": test_id,
            "change_id": ab_request.change_id,
            "traffic_split": ab_request.traffic_split,
            "duration_days": ab_request.duration_days,
            "start_time": datetime.now().isoformat(),
            "status": "active",
            "monitoring": {
                "metrics_endpoint": f"/api/v1/change-management/ab-test/{test_id}/metrics",
                "analysis_endpoint": f"/api/v1/change-management/ab-test/{test_id}/analyze"
            }
        }
        
        logger.info("A/B test created successfully", 
                   test_id=test_id, change_id=ab_request.change_id)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("A/B test creation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"A/B test creation failed: {str(e)}"
        )


@router.get("/ab-test/{test_id}/analyze", response_model=Dict[str, Any])
async def analyze_ab_test(test_id: str) -> Dict[str, Any]:
    """
    Analyze A/B test results
    """
    try:
        logger.info("Analyzing A/B test", test_id=test_id)
        
        # Analyze test results
        analysis = await change_analyzer.ab_testing.analyze_ab_test(test_id)
        
        if "error" in analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=analysis["error"]
            )
        
        # Add interpretation and recommendations
        analysis["interpretation"] = _interpret_ab_results(analysis)
        analysis["analysis_timestamp"] = datetime.now().isoformat()
        
        logger.info("A/B test analysis completed", 
                   test_id=test_id, 
                   recommendation=analysis["recommendation"])
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("A/B test analysis failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"A/B test analysis failed: {str(e)}"
        )


@router.post("/approve-change", response_model=Dict[str, Any])
async def approve_change(approval: ChangeApprovalModel) -> Dict[str, Any]:
    """
    Approve change for deployment
    """
    try:
        logger.info("Approving change", 
                   change_id=approval.change_id,
                   approved_by=approval.approved_by)
        
        # Get change request
        if approval.change_id not in change_analyzer.active_changes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Change {approval.change_id} not found"
            )
        
        change_request = change_analyzer.active_changes[approval.change_id]
        
        # Update change status
        change_request.status = ChangeStatus.APPROVED
        
        # Record approval
        if not hasattr(change_request, 'approval_history'):
            change_request.approval_history = []
        
        change_request.approval_history.append({
            "approved_by": approval.approved_by,
            "approval_reason": approval.approval_reason,
            "timestamp": datetime.now().isoformat()
        })
        
        response = {
            "change_id": approval.change_id,
            "status": "approved",
            "approved_by": approval.approved_by,
            "approval_timestamp": datetime.now().isoformat(),
            "next_steps": [
                "Change is approved for deployment",
                "Use /deploy-change endpoint to deploy",
                "Monitor performance after deployment"
            ],
            "deployment_endpoint": f"/api/v1/change-management/deploy-change/{approval.change_id}"
        }
        
        logger.info("Change approved successfully", 
                   change_id=approval.change_id,
                   approved_by=approval.approved_by)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Change approval failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Change approval failed: {str(e)}"
        )


@router.post("/deploy-change/{change_id}", response_model=Dict[str, Any])
async def deploy_change(change_id: str, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    Deploy approved change
    """
    try:
        logger.info("Deploying change", change_id=change_id)
        
        # Deploy change
        success = await change_analyzer.deploy_change(change_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Change deployment failed"
            )
        
        # Schedule performance monitoring
        background_tasks.add_task(_monitor_change_performance, change_id)
        
        response = {
            "change_id": change_id,
            "deployment_status": "success",
            "deployment_timestamp": datetime.now().isoformat(),
            "monitoring": {
                "enabled": True,
                "endpoint": f"/api/v1/change-management/monitor-change/{change_id}"
            },
            "rollback": {
                "available": True,
                "endpoint": f"/api/v1/change-management/rollback-change/{change_id}"
            }
        }
        
        logger.info("Change deployed successfully", change_id=change_id)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Change deployment failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Change deployment failed: {str(e)}"
        )


@router.post("/rollback-change/{change_id}", response_model=Dict[str, Any])
async def rollback_change(change_id: str) -> Dict[str, Any]:
    """
    Rollback deployed change
    """
    try:
        logger.info("Rolling back change", change_id=change_id)
        
        # Rollback change
        success = await change_analyzer.rollback_change(change_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Change rollback failed"
            )
        
        response = {
            "change_id": change_id,
            "rollback_status": "success",
            "rollback_timestamp": datetime.now().isoformat(),
            "message": "Change has been successfully rolled back to previous configuration"
        }
        
        logger.info("Change rolled back successfully", change_id=change_id)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Change rollback failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Change rollback failed: {str(e)}"
        )


@router.get("/monitor-change/{change_id}", response_model=Dict[str, Any])
async def monitor_change_performance(change_id: str) -> Dict[str, Any]:
    """
    Monitor performance impact of deployed change
    """
    try:
        logger.info("Monitoring change performance", change_id=change_id)
        
        # Get performance monitoring data
        monitoring_data = await change_analyzer.monitor_change_performance(change_id)
        
        if "error" in monitoring_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=monitoring_data["error"]
            )
        
        # Add performance assessment
        monitoring_data["performance_assessment"] = _assess_performance_impact(monitoring_data)
        monitoring_data["query_timestamp"] = datetime.now().isoformat()
        
        logger.info("Change performance monitoring completed", change_id=change_id)
        
        return monitoring_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Change performance monitoring failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Performance monitoring failed: {str(e)}"
        )


@router.get("/history", response_model=List[Dict[str, Any]])
async def get_change_history(
    limit: int = 50,
    change_type: Optional[str] = None,
    status: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get change history with filtering
    """
    try:
        logger.info("Retrieving change history", 
                   limit=limit, change_type=change_type, status=status)
        
        # Get change history
        history = await change_analyzer.get_change_history(limit)
        
        # Apply filters if specified
        if change_type:
            history = [h for h in history if h.get("change_type") == change_type]
        
        if status:
            history = [h for h in history if h.get("status") == status]
        
        # Add summary statistics
        summary = {
            "total_changes": len(history),
            "recent_deployments": len([h for h in history if h["action"] == "deployed"]),
            "recent_rollbacks": len([h for h in history if h["action"] == "rolled_back"]),
            "query_timestamp": datetime.now().isoformat()
        }
        
        logger.info("Change history retrieved", 
                   total_records=len(history))
        
        return {
            "summary": summary,
            "history": history
        }
        
    except Exception as e:
        logger.error("Change history retrieval failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"History retrieval failed: {str(e)}"
        )


@router.get("/active-changes", response_model=Dict[str, Any])
async def get_active_changes() -> Dict[str, Any]:
    """
    Get currently active changes
    """
    try:
        logger.info("Retrieving active changes")
        
        active_changes = []
        for change_id, change_request in change_analyzer.active_changes.items():
            active_changes.append({
                "change_id": change_id,
                "change_type": change_request.change_type.value,
                "description": change_request.description,
                "proposed_by": change_request.proposed_by,
                "status": change_request.status.value,
                "risk_level": change_request.risk_level.value,
                "timestamp": change_request.timestamp.isoformat(),
                "approval_required": change_request.approval_required
            })
        
        # Sort by timestamp (most recent first)
        active_changes.sort(key=lambda x: x["timestamp"], reverse=True)
        
        response = {
            "active_changes": active_changes,
            "summary": {
                "total_active": len(active_changes),
                "pending_approval": len([c for c in active_changes if c["status"] == "proposed"]),
                "approved": len([c for c in active_changes if c["status"] == "approved"]),
                "deployed": len([c for c in active_changes if c["status"] == "deployed"])
            },
            "query_timestamp": datetime.now().isoformat()
        }
        
        logger.info("Active changes retrieved", total_active=len(active_changes))
        
        return response
        
    except Exception as e:
        logger.error("Active changes retrieval failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Active changes retrieval failed: {str(e)}"
        )


@router.get("/configuration-versions", response_model=Dict[str, Any])
async def get_configuration_versions() -> Dict[str, Any]:
    """
    Get configuration versions history
    """
    try:
        logger.info("Retrieving configuration versions")
        
        # Get configuration versions
        versions = await change_analyzer.version_manager.list_versions()
        
        response = {
            "versions": versions,
            "summary": {
                "total_versions": len(versions),
                "current_version": change_analyzer.version_manager.current_version
            },
            "query_timestamp": datetime.now().isoformat()
        }
        
        logger.info("Configuration versions retrieved", total_versions=len(versions))
        
        return response
        
    except Exception as e:
        logger.error("Configuration versions retrieval failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Configuration versions retrieval failed: {str(e)}"
        )


@router.get("/health", response_model=Dict[str, Any])
async def change_management_health() -> Dict[str, Any]:
    """
    Change management system health check
    """
    try:
        # Check system components
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "change_analyzer": "operational",
                "version_manager": "operational",
                "validation_pipeline": "operational",
                "ab_testing_framework": "operational",
                "risk_assessment": "operational"
            },
            "statistics": {
                "active_changes": len(change_analyzer.active_changes),
                "change_history_size": len(change_analyzer.change_history),
                "active_ab_tests": len(change_analyzer.ab_testing.active_tests)
            }
        }
        
        logger.info("Change management health check completed", status="healthy")
        
        return health_status
        
    except Exception as e:
        logger.error("Change management health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


# Helper Functions

def _get_next_steps(impact_analysis: ChangeImpactAnalysis) -> List[str]:
    """Generate next steps based on impact analysis"""
    next_steps = []
    
    if impact_analysis.ai_brain_confidence >= 0.8:
        next_steps.append("Change has high AI Brain confidence - proceed with deployment")
    else:
        next_steps.append("Change has low AI Brain confidence - consider additional validation")
    
    if impact_analysis.impact_score >= 60:
        next_steps.append("High impact change detected - approval required")
        next_steps.append("Schedule deployment during off-hours")
    
    if impact_analysis.impact_score >= 40:
        next_steps.append("Consider A/B testing before full deployment")
    
    if impact_analysis.rollback_complexity >= 7:
        next_steps.append("Prepare detailed rollback plan due to high complexity")
    
    if impact_analysis.dependency_conflicts:
        next_steps.append("Resolve dependency conflicts before deployment")
    
    return next_steps


def _interpret_ab_results(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Interpret A/B test results"""
    interpretation = {
        "confidence_level": "high" if analysis["statistical_significance"] >= 0.8 else "low",
        "performance_verdict": "improvement" if analysis["performance_delta"]["profit_improvement_percent"] > 5 else "decline",
        "risk_assessment": "low" if analysis["performance_delta"]["drawdown_change"] <= 2 else "high",
        "sample_size_adequacy": "adequate" if analysis["statistical_significance"] >= 0.8 else "inadequate"
    }
    
    # Overall recommendation interpretation
    recommendation_meanings = {
        "deploy_treatment": "Treatment shows significant improvement - recommended for deployment",
        "reject_treatment": "Treatment shows negative impact - reject change",
        "continue_testing": "Results are inconclusive - continue testing",
        "insufficient_data": "Not enough data for reliable conclusions - extend test duration"
    }
    
    interpretation["recommendation_meaning"] = recommendation_meanings.get(
        analysis["recommendation"], "Unknown recommendation"
    )
    
    return interpretation


def _assess_performance_impact(monitoring_data: Dict[str, Any]) -> Dict[str, Any]:
    """Assess performance impact from monitoring data"""
    metrics = monitoring_data.get("metrics", {})
    
    assessment = {
        "overall_impact": "neutral",
        "latency_assessment": "acceptable" if metrics.get("latency_ms", 0) < 100 else "concerning",
        "throughput_assessment": "good" if metrics.get("throughput_tps", 0) > 1000 else "degraded",
        "error_rate_assessment": "excellent" if metrics.get("error_rate_percent", 0) < 0.1 else "concerning",
        "resource_usage": "normal" if metrics.get("memory_usage_mb", 0) < 1000 else "elevated"
    }
    
    # Determine overall impact
    concerning_factors = sum(1 for v in assessment.values() if "concerning" in str(v) or "degraded" in str(v))
    
    if concerning_factors >= 2:
        assessment["overall_impact"] = "negative"
        assessment["recommendation"] = "Consider rollback"
    elif concerning_factors == 1:
        assessment["overall_impact"] = "mixed"
        assessment["recommendation"] = "Monitor closely"
    else:
        assessment["overall_impact"] = "positive"
        assessment["recommendation"] = "Performance is acceptable"
    
    return assessment


async def _monitor_change_performance(change_id: str):
    """Background task to monitor change performance"""
    try:
        logger.info("Starting background performance monitoring", change_id=change_id)
        
        # Monitor for the first hour after deployment
        for i in range(12):  # 12 times, every 5 minutes
            await asyncio.sleep(300)  # Wait 5 minutes
            
            monitoring_data = await change_analyzer.monitor_change_performance(change_id)
            
            if "error" not in monitoring_data:
                # Check for performance issues
                metrics = monitoring_data.get("metrics", {})
                
                if metrics.get("latency_ms", 0) > 150:  # High latency
                    logger.warning("High latency detected after change deployment", 
                                 change_id=change_id, 
                                 latency=metrics["latency_ms"])
                
                if metrics.get("error_rate_percent", 0) > 0.5:  # High error rate
                    logger.error("High error rate detected after change deployment", 
                               change_id=change_id, 
                               error_rate=metrics["error_rate_percent"])
        
        logger.info("Background performance monitoring completed", change_id=change_id)
        
    except Exception as e:
        logger.error("Background performance monitoring failed", 
                    error=str(e), change_id=change_id)