"""
Central Hub Service Discovery API
Enhanced with contract validation and transport routing
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import time

import sys
from pathlib import Path

# Add shared directory to Python path
shared_dir = Path(__file__).parent.parent.parent / "shared"
sys.path.insert(0, str(shared_dir))

from components.utils.contract_bridge import ContractProcessorIntegration

discovery_router = APIRouter()
contract_processor = ContractProcessorIntegration()


class ServiceRegistration(BaseModel):
    """Service registration model"""
    name: str
    host: str
    port: int
    protocol: str = "http"
    health_endpoint: str = "/health"
    version: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ServiceUpdate(BaseModel):
    """Service update model"""
    host: Optional[str] = None
    port: Optional[int] = None
    health_endpoint: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@discovery_router.post("/register")
async def register_service(registration: ServiceRegistration, request: Request) -> Dict[str, Any]:
    """Register a service dengan Central Hub - Enhanced with contract validation"""
    # Import service instance
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from app import central_hub_service

    # Convert Pydantic model to dict for contract processing
    registration_data = {
        "name": registration.name,
        "host": registration.host,
        "port": registration.port,
        "protocol": registration.protocol,
        "health_endpoint": registration.health_endpoint,
        "version": registration.version,
        "metadata": registration.metadata or {},
        "timestamp": int(time.time() * 1000)
    }

    # Process through contract validation if available
    try:
        # Check if contract validation was already done by middleware
        if hasattr(request.state, 'contract_validation'):
            # Use pre-validated data from middleware
            validated_data = request.state.contract_validation.get('validated_data', registration_data)
            transport_info = request.state.contract_validation.get('transport_info', {})
            central_hub_service.logger.info(f"Using contract-validated data with transport: {transport_info.get('primary', 'http')}")
        else:
            # Manual contract processing if middleware not available
            contract_result = await contract_processor.process_inbound_message('service_registration', registration_data)
            validated_data = contract_result.get('validated_data', registration_data)
            transport_info = contract_result.get('transport_info', {})
    except Exception as e:
        central_hub_service.logger.warning(f"Contract validation failed, using direct data: {str(e)}")
        validated_data = registration_data
        transport_info = {}

    # Use validated data for service info
    service_info = {
        "name": validated_data.get("name", registration.name),
        "host": validated_data.get("host", registration.host),
        "port": validated_data.get("port", registration.port),
        "protocol": validated_data.get("protocol", registration.protocol),
        "health_endpoint": validated_data.get("health_endpoint", registration.health_endpoint),
        "version": validated_data.get("version", registration.version),
        "metadata": validated_data.get("metadata", registration.metadata or {}),
        "registered_at": int(time.time() * 1000),
        "last_seen": int(time.time() * 1000),
        "status": "active",
        "transport_preferences": transport_info
    }

    # Store in service registry using proper method
    registration_result = await central_hub_service.service_registry.register(validated_data)

    central_hub_service.logger.info(
        f"✅ Service registered: {registration.name} at {registration.host}:{registration.port} "
        f"(transport: {transport_info.get('primary', 'http')})"
    )

    return {
        "status": "registered",
        "service": registration.name,
        "registered_at": service_info["registered_at"],
        "transport_method": transport_info.get('primary', 'http'),
        "contract_validated": hasattr(request.state, 'contract_validation') or 'validated_data' in locals()
    }


@discovery_router.get("/{service_name}")
async def get_service(service_name: str, request: Request) -> Dict[str, Any]:
    """Get service information by name - Enhanced with contract-based response formatting"""
    from ..app import central_hub_service

    if service_name not in central_hub_service.service_registry:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")

    service_info = central_hub_service.service_registry[service_name]

    # Prepare response data for contract formatting
    response_data = {
        "service": service_name,
        "info": service_info,
        "url": f"{service_info['protocol']}://{service_info['host']}:{service_info['port']}",
        "transport_preferences": service_info.get("transport_preferences", {}),
        "retrieved_at": int(time.time() * 1000)
    }

    # Apply contract-based response formatting if available
    try:
        format_result = await contract_processor.process_outbound_message('service_discovery_response', response_data)
        formatted_data = format_result.get('formatted_data', response_data)
        transport_info = format_result.get('transport_info', {})

        # Add contract metadata
        formatted_data['_transport_method'] = transport_info.get('primary', 'http')
        formatted_data['_contract_formatted'] = True

        return formatted_data

    except Exception as e:
        central_hub_service.logger.warning(f"Contract formatting failed for service discovery: {str(e)}")
        # Return original response if contract formatting fails
        response_data['_contract_formatted'] = False
        return response_data


@discovery_router.get("/")
async def list_services() -> Dict[str, Any]:
    """List all registered services"""
    from ..app import central_hub_service

    services = {}
    for name, info in central_hub_service.service_registry.items():
        services[name] = {
            "host": info["host"],
            "port": info["port"],
            "protocol": info["protocol"],
            "status": info["status"],
            "last_seen": info["last_seen"],
            "url": f"{info['protocol']}://{info['host']}:{info['port']}"
        }

    return {
        "services": services,
        "count": len(services)
    }


@discovery_router.put("/{service_name}")
async def update_service(service_name: str, update: ServiceUpdate) -> Dict[str, Any]:
    """Update service information"""
    from ..app import central_hub_service

    if service_name not in central_hub_service.service_registry:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")

    service_info = central_hub_service.service_registry[service_name]

    # Update provided fields
    if update.host is not None:
        service_info["host"] = update.host
    if update.port is not None:
        service_info["port"] = update.port
    if update.health_endpoint is not None:
        service_info["health_endpoint"] = update.health_endpoint
    if update.metadata is not None:
        service_info["metadata"].update(update.metadata)

    service_info["last_seen"] = int(time.time() * 1000)

    central_hub_service.logger.info(f"Service updated: {service_name}")

    return {
        "status": "updated",
        "service": service_name,
        "updated_at": service_info["last_seen"]
    }


@discovery_router.delete("/{service_name}")
async def deregister_service(service_name: str) -> Dict[str, Any]:
    """Deregister service from Central Hub"""
    from ..app import central_hub_service

    if service_name not in central_hub_service.service_registry:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")

    del central_hub_service.service_registry[service_name]

    central_hub_service.logger.info(f"Service deregistered: {service_name}")

    return {
        "status": "deregistered",
        "service": service_name,
        "deregistered_at": int(time.time() * 1000)
    }


@discovery_router.post("/{service_name}/heartbeat")
async def service_heartbeat(service_name: str) -> Dict[str, Any]:
    """Update service heartbeat"""
    from ..app import central_hub_service

    if service_name not in central_hub_service.service_registry:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")

    central_hub_service.service_registry[service_name]["last_seen"] = int(time.time() * 1000)
    central_hub_service.service_registry[service_name]["status"] = "active"

    return {
        "status": "heartbeat_received",
        "service": service_name,
        "last_seen": central_hub_service.service_registry[service_name]["last_seen"]
    }