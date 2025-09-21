"""
Configuration API endpoints for Central Hub Service

Phase 1 Implementation: Configuration management endpoints
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter()


class ConfigUpdateRequest(BaseModel):
    """Configuration update request model"""
    key: str
    value: Any


class ConfigResponse(BaseModel):
    """Configuration response model"""
    key: str
    value: Any


class ConfigStatusResponse(BaseModel):
    """Configuration status response model"""
    initialized: bool
    cached_configs: int
    environment: str
    debug_mode: bool
    config_validation: Dict[str, Any]


@router.get("/")
async def get_all_config(request: Request):
    """Get all configuration values"""
    try:
        config_manager = request.app.state.config_manager

        if not config_manager:
            raise HTTPException(status_code=503, detail="Configuration manager not available")

        all_config = config_manager.get_all()

        return {
            "configurations": all_config,
            "count": len(all_config)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve configurations: {str(e)}")


@router.get("/{config_key}", response_model=ConfigResponse)
async def get_config(config_key: str, request: Request):
    """Get specific configuration value"""
    try:
        config_manager = request.app.state.config_manager

        if not config_manager:
            raise HTTPException(status_code=503, detail="Configuration manager not available")

        value = config_manager.get(config_key)

        if value is None:
            raise HTTPException(status_code=404, detail=f"Configuration key '{config_key}' not found")

        return ConfigResponse(key=config_key, value=value)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve configuration: {str(e)}")


@router.put("/{config_key}")
async def update_config(config_key: str, config_request: ConfigUpdateRequest, request: Request):
    """Update configuration value"""
    try:
        config_manager = request.app.state.config_manager
        logger = request.app.state.logger

        if not config_manager:
            raise HTTPException(status_code=503, detail="Configuration manager not available")

        # Get old value for logging
        old_value = config_manager.get(config_key)

        # Update configuration
        config_manager.set(config_key, config_request.value)

        if logger:
            logger.log_config_change(config_key, old_value, config_request.value)

        return {
            "message": f"Configuration '{config_key}' updated successfully",
            "key": config_key,
            "old_value": old_value,
            "new_value": config_request.value
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")


@router.post("/reload")
async def reload_config(request: Request):
    """Reload all configurations"""
    try:
        config_manager = request.app.state.config_manager
        logger = request.app.state.logger

        if not config_manager:
            raise HTTPException(status_code=503, detail="Configuration manager not available")

        # Reload configuration
        await config_manager.reload()

        if logger:
            logger.info("🔄 Configuration reloaded via API")

        return {
            "message": "Configuration reloaded successfully",
            "timestamp": request.app.state.health_monitor.get_current_timestamp()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload configuration: {str(e)}")


@router.get("/status/validation")
async def validate_config(request: Request):
    """Validate current configuration"""
    try:
        config_manager = request.app.state.config_manager

        if not config_manager:
            raise HTTPException(status_code=503, detail="Configuration manager not available")

        validation_results = config_manager.validate_config()

        return validation_results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Configuration validation failed: {str(e)}")


@router.get("/status/manager", response_model=ConfigStatusResponse)
async def get_config_manager_status(request: Request):
    """Get configuration manager status"""
    try:
        config_manager = request.app.state.config_manager

        if not config_manager:
            raise HTTPException(status_code=503, detail="Configuration manager not available")

        status = config_manager.get_status()

        return ConfigStatusResponse(**status)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve configuration status: {str(e)}")


@router.get("/service/info")
async def get_service_config(request: Request):
    """Get service-specific configuration"""
    try:
        config_manager = request.app.state.config_manager

        if not config_manager:
            raise HTTPException(status_code=503, detail="Configuration manager not available")

        service_config = config_manager.get_service_config()

        return {
            "service_configuration": service_config,
            "service": "central-hub",
            "port": 8010
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve service configuration: {str(e)}")


@router.get("/logging/info")
async def get_logging_config(request: Request):
    """Get logging configuration"""
    try:
        config_manager = request.app.state.config_manager

        if not config_manager:
            raise HTTPException(status_code=503, detail="Configuration manager not available")

        logging_config = config_manager.get_logging_config()

        return {
            "logging_configuration": logging_config,
            "logger_stats": request.app.state.logger.get_stats() if request.app.state.logger else None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve logging configuration: {str(e)}")


@router.get("/registry/info")
async def get_registry_config(request: Request):
    """Get service registry configuration"""
    try:
        config_manager = request.app.state.config_manager

        if not config_manager:
            raise HTTPException(status_code=503, detail="Configuration manager not available")

        registry_config = config_manager.get_registry_config()

        return {
            "registry_configuration": registry_config,
            "registry_stats": request.app.state.service_registry.get_registry_stats() if request.app.state.service_registry else None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve registry configuration: {str(e)}")


@router.get("/health/info")
async def get_health_config(request: Request):
    """Get health monitoring configuration"""
    try:
        config_manager = request.app.state.config_manager

        if not config_manager:
            raise HTTPException(status_code=503, detail="Configuration manager not available")

        health_config = config_manager.get_health_config()

        return {
            "health_configuration": health_config,
            "monitor_stats": request.app.state.health_monitor.get_monitor_stats() if request.app.state.health_monitor else None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve health configuration: {str(e)}")
"