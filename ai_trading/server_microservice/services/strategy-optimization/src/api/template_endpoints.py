"""
Strategy Template API Endpoints
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import HTTPException
from pydantic import BaseModel, Field

from ..business.strategy_templates import StrategyTemplateManager
from ..models.strategy_models import StrategyType

logger = logging.getLogger(__name__)


class CreateFromTemplateRequest(BaseModel):
    """Request to create strategy from template"""
    template_id: str = Field(description="Template ID to use")
    strategy_name: str = Field(description="Name for new strategy")
    symbols: List[str] = Field(description="Trading symbols")
    customizations: Optional[Dict[str, Any]] = Field(None, description="Parameter customizations")


class TemplateEndpoints:
    """Template management API endpoints"""
    
    def __init__(self, template_manager: StrategyTemplateManager):
        self.template_manager = template_manager
    
    async def list_templates(
        self,
        strategy_type: Optional[StrategyType] = None,
        complexity_max: Optional[float] = None
    ) -> Dict[str, Any]:
        """List available strategy templates"""
        
        try:
            templates = self.template_manager.list_templates(
                strategy_type=strategy_type,
                complexity_max=complexity_max
            )
            
            template_summaries = []
            for template in templates:
                summary = {
                    "template_id": template.template_id,
                    "name": template.name,
                    "strategy_type": template.strategy_type.value,
                    "description": template.description,
                    "complexity_score": template.complexity_score,
                    "minimum_capital": template.minimum_capital,
                    "expected_sharpe": template.expected_sharpe,
                    "expected_win_rate": template.expected_win_rate
                }
                template_summaries.append(summary)
            
            return {
                "success": True,
                "templates": template_summaries,
                "total_count": len(template_summaries)
            }
            
        except Exception as e:
            logger.error(f"Failed to list templates: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def get_template(self, template_id: str) -> Dict[str, Any]:
        """Get detailed template information"""
        
        try:
            template = self.template_manager.get_template(template_id)
            
            if not template:
                raise HTTPException(status_code=404, detail="Template not found")
            
            return {
                "success": True,
                "template": template.dict()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get template {template_id}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def create_strategy_from_template(
        self,
        request: CreateFromTemplateRequest
    ) -> Dict[str, Any]:
        """Create strategy instance from template"""
        
        try:
            strategy = self.template_manager.create_strategy_from_template(
                template_id=request.template_id,
                strategy_name=request.strategy_name,
                symbols=request.symbols,
                customizations=request.customizations
            )
            
            if not strategy:
                raise HTTPException(status_code=400, detail="Failed to create strategy from template")
            
            return {
                "success": True,
                "message": "Strategy created from template successfully",
                "strategy": strategy.dict()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create strategy from template: {e}")
            raise HTTPException(status_code=400, detail=str(e))