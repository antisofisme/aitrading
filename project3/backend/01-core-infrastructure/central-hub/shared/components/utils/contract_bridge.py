"""
Contract Bridge Implementation untuk Central Hub
Menyediakan validasi contract dan transport method selection
"""

import asyncio
import subprocess
import json
import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from enum import Enum
from dataclasses import dataclass


class TransportMethod(Enum):
    """Available transport methods"""
    HTTP = "http"
    GRPC = "grpc"
    NATS_KAFKA = "nats-kafka"
    INTERNAL = "internal"


@dataclass
class ContractValidationResult:
    """Result of contract validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    validated_data: Optional[Dict[str, Any]] = None
    contract_name: Optional[str] = None
    transport_method: Optional[TransportMethod] = None


@dataclass
class TransportSelection:
    """Transport method selection result"""
    primary_method: TransportMethod
    fallback_method: TransportMethod
    timeout_ms: int
    reason: str


class ContractValidationBridge:
    """
    Bridge untuk validasi contract menggunakan Node.js Joi schemas
    Mengintegrasikan Python dengan JavaScript contract validation
    """

    def __init__(self, contracts_path: str = None):
        self.logger = logging.getLogger("central-hub.contract-bridge")
        self.contracts_path = Path(contracts_path) if contracts_path else Path(__file__).parent.parent.parent / "contracts"
        self.validation_cache = {}
        self.cache_ttl = 300  # 5 minutes

    async def validate_contract(self, 
                              contract_name: str, 
                              data: Dict[str, Any], 
                              direction: str = "input") -> ContractValidationResult:
        """
        Validate data against JavaScript Joi contract
        
        Args:
            contract_name: Name of contract file (without .js)
            data: Data to validate
            direction: 'input' or 'output'
        """
        try:
            # Check cache first
            cache_key = f"{contract_name}:{direction}:{hash(str(data))}"
            if cache_key in self.validation_cache:
                cached_result, timestamp = self.validation_cache[cache_key]
                if time.time() - timestamp < self.cache_ttl:
                    return cached_result

            # Find contract file
            contract_file = self._find_contract_file(contract_name)
            if not contract_file:
                return ContractValidationResult(
                    is_valid=False,
                    errors=[f"Contract file not found: {contract_name}"],
                    warnings=[]
                )

            # Validate using Node.js subprocess
            validation_result = await self._validate_with_nodejs(contract_file, data, direction)
            
            # Cache result
            self.validation_cache[cache_key] = (validation_result, time.time())
            
            return validation_result

        except Exception as e:
            self.logger.error(f"Contract validation error: {str(e)}")
            return ContractValidationResult(
                is_valid=False,
                errors=[f"Validation system error: {str(e)}"],
                warnings=[]
            )

    def _find_contract_file(self, contract_name: str) -> Optional[Path]:
        """Find contract file in contracts directory"""
        # Try exact match first
        exact_file = self.contracts_path / f"{contract_name}.js"
        if exact_file.exists():
            return exact_file

        # Try with common patterns
        patterns = [
            f"{contract_name}-to-central-hub.js",
            f"{contract_name}-from-central-hub.js",
            f"central-hub-{contract_name}.js"
        ]
        
        for pattern in patterns:
            file_path = self.contracts_path / pattern
            if file_path.exists():
                return file_path

        # Search in subdirectories
        for subdir in ["inputs", "outputs", "grpc", "nats-kafka", "internal"]:
            subdir_path = self.contracts_path / subdir
            if subdir_path.exists():
                for pattern in [f"{contract_name}.js"] + patterns:
                    file_path = subdir_path / pattern
                    if file_path.exists():
                        return file_path

        return None

    async def _validate_with_nodejs(self, 
                                   contract_file: Path, 
                                   data: Dict[str, Any], 
                                   direction: str) -> ContractValidationResult:
        """Validate data using Node.js subprocess"""
        # Create validation script
        validation_script = f"""
const fs = require('fs');
const path = require('path');

try {{
    // Load contract
    const contractPath = '{contract_file}';
    delete require.cache[require.resolve(contractPath)];
    const contract = require(contractPath);
    
    // Get validation data
    const inputData = {json.dumps(data)};
    const direction = '{direction}';
    
    // Determine which schema to use
    let schema;
    if (direction === 'input') {{
        schema = contract.inputSchema || contract.schema;
    }} else {{
        schema = contract.outputSchema || contract.responseSchema || contract.schema;
    }}
    
    if (!schema) {{
        console.log(JSON.stringify({{
            is_valid: false,
            errors: ['No schema found in contract'],
            warnings: [],
            contract_name: path.basename(contractPath, '.js')
        }}));
        process.exit(0);
    }}
    
    // Validate
    const {{ error, value }} = schema.validate(inputData, {{ 
        abortEarly: false,
        allowUnknown: true,
        stripUnknown: true
    }});
    
    if (error) {{
        console.log(JSON.stringify({{
            is_valid: false,
            errors: error.details.map(d => d.message),
            warnings: [],
            contract_name: path.basename(contractPath, '.js')
        }}));
    }} else {{
        console.log(JSON.stringify({{
            is_valid: true,
            errors: [],
            warnings: [],
            validated_data: value,
            contract_name: path.basename(contractPath, '.js')
        }}));
    }}
    
}} catch (err) {{
    console.log(JSON.stringify({{
        is_valid: false,
        errors: [`Validation error: ${{err.message}}`],
        warnings: [],
        contract_name: 'unknown'
    }}));
}}
"""

        try:
            # Run Node.js validation
            process = await asyncio.create_subprocess_exec(
                'node', '-e', validation_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.contracts_path)
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10.0)
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Node.js validation failed"
                return ContractValidationResult(
                    is_valid=False,
                    errors=[f"Node.js execution error: {error_msg}"],
                    warnings=[]
                )
            
            # Parse result
            result_data = json.loads(stdout.decode())
            return ContractValidationResult(
                is_valid=result_data.get('is_valid', False),
                errors=result_data.get('errors', []),
                warnings=result_data.get('warnings', []),
                validated_data=result_data.get('validated_data'),
                contract_name=result_data.get('contract_name')
            )
            
        except asyncio.TimeoutError:
            return ContractValidationResult(
                is_valid=False,
                errors=["Contract validation timeout"],
                warnings=[]
            )
        except Exception as e:
            return ContractValidationResult(
                is_valid=False,
                errors=[f"Subprocess error: {str(e)}"],
                warnings=[]
            )

    async def get_available_contracts(self) -> List[str]:
        """Get list of available contract files"""
        contracts = []
        
        if not self.contracts_path.exists():
            return contracts
            
        # Scan for .js files
        for file_path in self.contracts_path.rglob("*.js"):
            contract_name = file_path.stem
            contracts.append(contract_name)
            
        return sorted(contracts)

    async def health_check(self) -> Dict[str, Any]:
        """Health check for contract validation system"""
        try:
            # Check Node.js availability
            process = await asyncio.create_subprocess_exec(
                'node', '--version',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5.0)
            
            if process.returncode != 0:
                return {
                    "status": "unhealthy",
                    "error": "Node.js not available",
                    "contracts_path": str(self.contracts_path),
                    "available_contracts": 0
                }
            
            node_version = stdout.decode().strip()
            available_contracts = await self.get_available_contracts()
            
            return {
                "status": "healthy",
                "node_version": node_version,
                "contracts_path": str(self.contracts_path),
                "available_contracts": len(available_contracts),
                "cache_size": len(self.validation_cache)
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "contracts_path": str(self.contracts_path),
                "available_contracts": 0
            }


class TransportMethodSelector:
    """
    Intelligent transport method selection berdasarkan karakteristik message
    Sesuai dengan SERVICE_ARCHITECTURE.md specifications
    """

    def __init__(self):
        self.logger = logging.getLogger("central-hub.transport-selector")
        self.selection_rules = self._load_selection_rules()

    def _load_selection_rules(self) -> Dict[str, Any]:
        """Load transport selection rules from configuration"""
        return {
            "service_registration": {
                "primary": TransportMethod.GRPC,
                "fallback": TransportMethod.HTTP,
                "timeout_ms": 5000,
                "reason": "Service registration needs reliable delivery"
            },
            "configuration_request": {
                "primary": TransportMethod.HTTP,
                "fallback": TransportMethod.GRPC,
                "timeout_ms": 10000,
                "reason": "Configuration requests need synchronous response"
            },
            "health_monitoring": {
                "primary": TransportMethod.NATS_KAFKA,
                "fallback": TransportMethod.HTTP,
                "timeout_ms": 2000,
                "reason": "Health monitoring needs high throughput"
            },
            "workflow_orchestration": {
                "primary": TransportMethod.NATS_KAFKA,
                "fallback": TransportMethod.HTTP,
                "timeout_ms": 15000,
                "reason": "Workflow needs asynchronous processing"
            },
            "data_synchronization": {
                "primary": TransportMethod.GRPC,
                "fallback": TransportMethod.HTTP,
                "timeout_ms": 30000,
                "reason": "Data sync needs efficient streaming"
            },
            "realtime_coordination": {
                "primary": TransportMethod.NATS_KAFKA,
                "fallback": TransportMethod.GRPC,
                "timeout_ms": 1000,
                "reason": "Real-time needs low latency"
            }
        }

    def select_transport_method(self, 
                              operation_type: str,
                              message_size: int = 0,
                              priority: str = "normal",
                              requires_response: bool = True,
                              target_service: Optional[str] = None) -> TransportSelection:
        """
        Select optimal transport method based on operation characteristics
        
        Args:
            operation_type: Type of operation (e.g., 'service_registration')
            message_size: Size of message in bytes
            priority: Message priority ('low', 'normal', 'high', 'critical')
            requires_response: Whether operation needs synchronous response
            target_service: Target service name (for service-specific rules)
        """
        
        # Check for exact operation type match
        if operation_type in self.selection_rules:
            rule = self.selection_rules[operation_type]
            return TransportSelection(
                primary_method=rule["primary"],
                fallback_method=rule["fallback"],
                timeout_ms=rule["timeout_ms"],
                reason=rule["reason"]
            )
        
        # Apply heuristic rules
        if message_size > 1024 * 1024:  # > 1MB
            # Large messages prefer gRPC streaming
            return TransportSelection(
                primary_method=TransportMethod.GRPC,
                fallback_method=TransportMethod.HTTP,
                timeout_ms=60000,
                reason="Large message size requires streaming"
            )
        
        if priority in ["high", "critical"]:
            # High priority prefers reliable delivery
            return TransportSelection(
                primary_method=TransportMethod.GRPC,
                fallback_method=TransportMethod.HTTP,
                timeout_ms=5000,
                reason="High priority requires reliable delivery"
            )
        
        if not requires_response:
            # Fire-and-forget prefers messaging
            return TransportSelection(
                primary_method=TransportMethod.NATS_KAFKA,
                fallback_method=TransportMethod.HTTP,
                timeout_ms=3000,
                reason="Asynchronous operation prefers messaging"
            )
        
        # Default to HTTP for simplicity
        return TransportSelection(
            primary_method=TransportMethod.HTTP,
            fallback_method=TransportMethod.GRPC,
            timeout_ms=10000,
            reason="Default selection for general operations"
        )

    def get_transport_config(self, method: TransportMethod) -> Dict[str, Any]:
        """Get configuration for specific transport method"""
        configs = {
            TransportMethod.HTTP: {
                "protocol": "http",
                "default_port": 80,
                "content_type": "application/json",
                "supports_streaming": False,
                "max_message_size": 10 * 1024 * 1024  # 10MB
            },
            TransportMethod.GRPC: {
                "protocol": "grpc",
                "default_port": 50051,
                "content_type": "application/grpc",
                "supports_streaming": True,
                "max_message_size": 100 * 1024 * 1024  # 100MB
            },
            TransportMethod.NATS_KAFKA: {
                "protocol": "nats-kafka",
                "nats_port": 4222,
                "kafka_port": 9092,
                "supports_streaming": True,
                "max_message_size": 50 * 1024 * 1024  # 50MB
            },
            TransportMethod.INTERNAL: {
                "protocol": "internal",
                "default_port": None,
                "content_type": "application/json",
                "supports_streaming": False,
                "max_message_size": 1024 * 1024  # 1MB
            }
        }
        
        return configs.get(method, configs[TransportMethod.HTTP])

    def health_check(self) -> Dict[str, Any]:
        """Health check for transport selector"""
        return {
            "status": "healthy",
            "available_methods": [method.value for method in TransportMethod],
            "selection_rules": len(self.selection_rules),
            "default_method": TransportMethod.HTTP.value
        }


class ContractProcessorIntegration:
    """
    Main integration class yang menggabungkan contract validation dan transport selection
    Menyediakan interface unified untuk Central Hub
    """

    def __init__(self, contracts_path: str = None):
        self.logger = logging.getLogger("central-hub.contract-processor")
        self.validation_bridge = ContractValidationBridge(contracts_path)
        self.transport_selector = TransportMethodSelector()
        self.is_initialized = False

    async def initialize(self):
        """Initialize contract processor integration"""
        try:
            # Test contract validation system
            health = await self.validation_bridge.health_check()
            if health["status"] != "healthy":
                raise Exception(f"Contract validation unhealthy: {health.get('error')}")
            
            # Test transport selector
            transport_health = self.transport_selector.health_check()
            if transport_health["status"] != "healthy":
                raise Exception("Transport selector unhealthy")
            
            self.is_initialized = True
            self.logger.info("✅ Contract processor integration initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Contract processor initialization failed: {str(e)}")
            raise

    async def process_request(self, 
                            operation_type: str,
                            data: Dict[str, Any],
                            target_service: Optional[str] = None) -> Tuple[ContractValidationResult, TransportSelection]:
        """
        Process incoming request dengan contract validation dan transport selection
        
        Returns:
            Tuple of (validation_result, transport_selection)
        """
        if not self.is_initialized:
            await self.initialize()

        # Step 1: Validate contract
        validation_result = await self.validation_bridge.validate_contract(
            contract_name=operation_type,
            data=data,
            direction="input"
        )

        # Step 2: Select transport method
        transport_selection = self.transport_selector.select_transport_method(
            operation_type=operation_type,
            message_size=len(json.dumps(data).encode()),
            requires_response=True,
            target_service=target_service
        )

        # Log processing results
        if validation_result.is_valid:
            self.logger.debug(f"✅ Request validated for {operation_type}")
        else:
            self.logger.warning(f"❌ Request validation failed for {operation_type}: {validation_result.errors}")

        self.logger.debug(f"🚀 Selected {transport_selection.primary_method.value} transport for {operation_type}")

        return validation_result, transport_selection

    async def process_response(self, 
                             operation_type: str,
                             response_data: Dict[str, Any]) -> ContractValidationResult:
        """
        Process outgoing response dengan contract validation
        """
        if not self.is_initialized:
            await self.initialize()

        validation_result = await self.validation_bridge.validate_contract(
            contract_name=operation_type,
            data=response_data,
            direction="output"
        )

        if validation_result.is_valid:
            self.logger.debug(f"✅ Response validated for {operation_type}")
        else:
            self.logger.warning(f"❌ Response validation failed for {operation_type}: {validation_result.errors}")

        return validation_result

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        validation_health = await self.validation_bridge.health_check()
        transport_health = self.transport_selector.health_check()
        available_contracts = await self.validation_bridge.get_available_contracts()

        return {
            "status": "healthy" if self.is_initialized else "not_initialized",
            "contract_validation": validation_health,
            "transport_selection": transport_health,
            "available_contracts": len(available_contracts),
            "contracts": available_contracts[:10],  # First 10 for overview
            "initialization_complete": self.is_initialized
        }

    async def health_check(self) -> Dict[str, Any]:
        """Health check untuk contract processor integration"""
        try:
            if not self.is_initialized:
                return {
                    "status": "not_initialized",
                    "error": "Contract processor not initialized"
                }

            status = await self.get_system_status()
            
            # Determine overall health
            validation_healthy = status["contract_validation"]["status"] == "healthy"
            transport_healthy = status["transport_selection"]["status"] == "healthy"
            
            overall_status = "healthy" if validation_healthy and transport_healthy else "degraded"
            
            return {
                "status": overall_status,
                "components": {
                    "contract_validation": validation_healthy,
                    "transport_selection": transport_healthy,
                    "initialization": self.is_initialized
                },
                "available_contracts": status["available_contracts"]
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
