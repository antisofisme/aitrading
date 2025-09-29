"""
Central Hub - Contract Validation Middleware
FastAPI middleware for automatic contract validation
"""

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import json
import time
from typing import Dict, Any, Optional
import logging

import sys
from pathlib import Path

# Add shared directory to Python path
shared_dir = Path(__file__).parent.parent.parent / "shared"
sys.path.insert(0, str(shared_dir))

from utils.contract_bridge import ContractProcessorIntegration


class ContractValidationMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for automatic contract validation"""

    def __init__(self, app, enable_validation: bool = True, enable_response_formatting: bool = True):
        super().__init__(app)
        self.enable_validation = enable_validation
        self.enable_response_formatting = enable_response_formatting
        self.contract_processor = ContractProcessorIntegration()
        self.logger = logging.getLogger("central-hub.validation-middleware")

        # Route to contract mapping
        self.route_contract_map = {
            '/api/discovery/register': 'service_registration',
            '/api/discovery/': 'service_discovery',
            '/api/config/': 'configuration_request',
            '/api/health/report': 'health_report',
            '/api/metrics/stream': 'health_stream'
        }

        # Response contract mapping
        self.response_contract_map = {
            '/api/discovery/': 'service_discovery_response',
            '/api/config/update': 'configuration_update'
        }

    async def dispatch(self, request: Request, call_next):
        """Process request through contract validation"""

        if not self.enable_validation:
            return await call_next(request)

        # Get route pattern
        route_path = request.url.path
        method = request.method.upper()

        # Skip validation for certain routes
        if self._should_skip_validation(route_path, method):
            return await call_next(request)

        # Process request validation
        try:
            if method in ['POST', 'PUT', 'PATCH']:
                await self._validate_request(request, route_path)
        except Exception as e:
            self.logger.error(f"Request validation failed for {route_path}: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={
                    "error": "contract_validation_failed",
                    "message": str(e),
                    "path": route_path,
                    "timestamp": int(time.time() * 1000)
                }
            )

        # Process the request
        response = await call_next(request)

        # Process response formatting
        if self.enable_response_formatting and response.status_code < 400:
            try:
                response = await self._format_response(response, route_path)
            except Exception as e:
                self.logger.error(f"Response formatting failed for {route_path}: {str(e)}")
                # Continue with original response if formatting fails

        return response

    async def _validate_request(self, request: Request, route_path: str):
        """Validate request against contract schema"""

        # Determine contract type
        contract_type = self._get_contract_type(route_path)
        if not contract_type:
            return  # No contract validation needed

        # Read request body
        body = await request.body()
        if not body:
            return  # No body to validate

        try:
            request_data = json.loads(body)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in request body: {str(e)}")

        # Add request metadata
        request_context = {
            'path': route_path,
            'method': request.method,
            'client_ip': request.client.host if request.client else 'unknown',
            'user_agent': request.headers.get('user-agent', 'unknown'),
            'timestamp': int(time.time() * 1000)
        }

        # Validate using contract processor
        validation_result = await self.contract_processor.process_inbound_message(
            contract_type,
            request_data,
            request_context
        )

        # Store validation result for later use
        request.state.contract_validation = validation_result

        self.logger.info(f"✅ Contract validation passed for {contract_type} on {route_path}")

    async def _format_response(self, response: Response, route_path: str) -> Response:
        """Format response using contract specifications"""

        # Determine response contract type
        response_contract_type = self._get_response_contract_type(route_path)
        if not response_contract_type:
            return response

        # Read response body
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk

        if not response_body:
            return response

        try:
            response_data = json.loads(response_body)
        except json.JSONDecodeError:
            return response  # Return original response if not JSON

        # Format using contract processor
        format_result = await self.contract_processor.process_outbound_message(
            response_contract_type,
            response_data
        )

        formatted_data = format_result.get('formatted_data', response_data)

        # Add contract metadata to response
        formatted_data['_contract_metadata'] = {
            'contract_type': response_contract_type,
            'transport_method': format_result.get('transport_info', {}).get('primary', 'http'),
            'formatted_at': int(time.time() * 1000)
        }

        # Create new response with formatted data
        new_response = JSONResponse(
            content=formatted_data,
            status_code=response.status_code,
            headers=dict(response.headers)
        )

        self.logger.info(f"✅ Response formatted using {response_contract_type} contract")

        return new_response

    def _should_skip_validation(self, route_path: str, method: str) -> bool:
        """Determine if route should skip contract validation"""

        # Skip validation for specific routes
        skip_routes = [
            '/health',
            '/docs',
            '/openapi.json',
            '/favicon.ico'
        ]

        for skip_route in skip_routes:
            if route_path.startswith(skip_route):
                return True

        # Skip validation for GET requests by default
        if method == 'GET':
            return True

        return False

    def _get_contract_type(self, route_path: str) -> Optional[str]:
        """Get contract type for request validation"""

        for route_pattern, contract_type in self.route_contract_map.items():
            if route_path.startswith(route_pattern.rstrip('/')):
                return contract_type

        return None

    def _get_response_contract_type(self, route_path: str) -> Optional[str]:
        """Get contract type for response formatting"""

        for route_pattern, contract_type in self.response_contract_map.items():
            if route_path.startswith(route_pattern.rstrip('/')):
                return contract_type

        return None


class ContractHealthMiddleware(BaseHTTPMiddleware):
    """Middleware for contract validation health monitoring"""

    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger("central-hub.contract-health")
        self.validation_stats = {
            'total_requests': 0,
            'validated_requests': 0,
            'validation_failures': 0,
            'formatting_successes': 0,
            'formatting_failures': 0
        }

    async def dispatch(self, request: Request, call_next):
        """Track contract validation statistics"""

        start_time = time.time()
        self.validation_stats['total_requests'] += 1

        response = await call_next(request)

        # Track validation results
        if hasattr(request.state, 'contract_validation'):
            self.validation_stats['validated_requests'] += 1

        # Log performance metrics
        duration_ms = (time.time() - start_time) * 1000
        if duration_ms > 100:  # Log slow requests
            self.logger.warning(f"Slow contract processing: {request.url.path} took {duration_ms:.2f}ms")

        return response

    def get_health_stats(self) -> Dict[str, Any]:
        """Get contract validation health statistics"""

        total = self.validation_stats['total_requests']
        validated = self.validation_stats['validated_requests']

        return {
            'contract_validation_health': {
                'total_requests': total,
                'validated_requests': validated,
                'validation_rate': (validated / total * 100) if total > 0 else 0,
                'validation_failures': self.validation_stats['validation_failures'],
                'formatting_successes': self.validation_stats['formatting_successes'],
                'formatting_failures': self.validation_stats['formatting_failures'],
                'status': 'healthy' if total == 0 or (validated / total) > 0.95 else 'degraded'
            }
        }