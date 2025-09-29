"""
Central Hub - Contract Bridge
Bridge between Python service implementation and JavaScript contract validation
"""

import subprocess
import json
import tempfile
import os
from typing import Dict, Any, Optional, List
import logging


class ContractValidationBridge:
    """Bridge for validating Python data against JavaScript contract schemas"""

    def __init__(self):
        self.logger = logging.getLogger("central-hub.contract-bridge")
        self.contracts_path = "/mnt/g/khoirul/aitrading/project3/backend/01-core-infrastructure/central-hub/contracts"

    def _run_node_validation(self, contract_file: str, data: Dict[str, Any], function_name: str) -> Dict[str, Any]:
        """Run JavaScript contract validation via Node.js"""
        try:
            # Create temporary file with data
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(data, temp_file)
                temp_file_path = temp_file.name

            # Create validation script
            validation_script = f"""
            const contract = require('{self.contracts_path}/{contract_file}');
            const fs = require('fs');

            try {{
                const data = JSON.parse(fs.readFileSync('{temp_file_path}', 'utf8'));
                const result = contract.{function_name}(data);
                console.log(JSON.stringify({{
                    success: true,
                    result: result
                }}));
            }} catch (error) {{
                console.log(JSON.stringify({{
                    success: false,
                    error: error.message,
                    stack: error.stack
                }}));
            }}
            """

            # Write validation script to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as script_file:
                script_file.write(validation_script)
                script_file_path = script_file.name

            # Execute Node.js validation
            result = subprocess.run(
                ['node', script_file_path],
                capture_output=True,
                text=True,
                timeout=10
            )

            # Cleanup temp files
            os.unlink(temp_file_path)
            os.unlink(script_file_path)

            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                self.logger.error(f"Node.js validation failed: {result.stderr}")
                return {"success": False, "error": result.stderr}

        except Exception as e:
            self.logger.error(f"Contract validation error: {str(e)}")
            return {"success": False, "error": str(e)}

    def validate_service_registration(self, registration_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate service registration against contract schema"""
        return self._run_node_validation(
            'http-rest/service-registration-to-central-hub.js',
            registration_data,
            'processServiceRegistration'
        )

    def validate_service_discovery(self, discovery_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate service discovery request against contract schema"""
        return self._run_node_validation(
            'http-rest/service-discovery-to-central-hub.js',
            discovery_data,
            'processServiceDiscovery'
        )

    def validate_configuration_request(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration request against contract schema"""
        return self._run_node_validation(
            'http-rest/configuration-request-to-central-hub.js',
            config_data,
            'processConfigurationRequest'
        )

    def validate_health_report(self, health_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate health report against contract schema"""
        return self._run_node_validation(
            'grpc/health-report-to-central-hub.js',
            health_data,
            'processHealthReport'
        )

    def validate_health_stream(self, stream_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate health stream data against contract schema"""
        return self._run_node_validation(
            'nats-kafka/health-stream-to-central-hub.js',
            stream_data,
            'processHealthStream'
        )

    def format_service_discovery_response(self, service_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format service discovery response using contract formatter"""
        return self._run_node_validation(
            'http-rest/service-discovery-response-from-central-hub.js',
            service_data,
            'formatServiceResponse'
        )

    def format_configuration_update(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format configuration update using contract formatter"""
        return self._run_node_validation(
            'grpc/configuration-update-from-central-hub.js',
            config_data,
            'formatConfigurationUpdate'
        )

    def format_scaling_command(self, scaling_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format scaling command using contract formatter"""
        return self._run_node_validation(
            'nats-kafka/scaling-command-from-central-hub.js',
            scaling_data,
            'formatScalingCommand'
        )


class TransportMethodSelector:
    """Select appropriate transport method based on message characteristics and contract specifications"""

    def __init__(self):
        self.logger = logging.getLogger("central-hub.transport-selector")

        # Transport method preferences from contracts
        self.transport_matrix = {
            'service_registration': {
                'primary': 'http',
                'fallback': 'grpc',
                'characteristics': ['synchronous', 'request-response', 'low-frequency']
            },
            'service_discovery': {
                'primary': 'http',
                'fallback': 'grpc',
                'characteristics': ['synchronous', 'request-response', 'medium-frequency']
            },
            'configuration_request': {
                'primary': 'http',
                'fallback': 'grpc',
                'characteristics': ['synchronous', 'request-response', 'low-frequency']
            },
            'configuration_update': {
                'primary': 'grpc',
                'fallback': 'http',
                'characteristics': ['broadcast', 'reliable-delivery', 'medium-frequency']
            },
            'health_report': {
                'primary': 'grpc',
                'fallback': 'http',
                'characteristics': ['streaming', 'real-time', 'high-frequency']
            },
            'health_stream': {
                'primary': 'nats-kafka',
                'fallback': 'grpc',
                'characteristics': ['streaming', 'high-throughput', 'continuous']
            },
            'scaling_command': {
                'primary': 'nats-kafka',
                'fallback': 'grpc',
                'characteristics': ['broadcast', 'fire-and-forget', 'urgent']
            },
            'metrics_aggregation': {
                'primary': 'nats-kafka',
                'fallback': 'http',
                'characteristics': ['streaming', 'batch-processing', 'high-volume']
            }
        }

    def select_transport_method(self, message_type: str, message_characteristics: List[str] = None) -> Dict[str, str]:
        """Select appropriate transport method for message type"""

        if message_type in self.transport_matrix:
            transport_config = self.transport_matrix[message_type]

            return {
                'primary': transport_config['primary'],
                'fallback': transport_config['fallback'],
                'reason': f"Contract specification for {message_type}",
                'characteristics': transport_config['characteristics']
            }

        # Default selection based on characteristics
        if message_characteristics:
            if 'streaming' in message_characteristics or 'high-frequency' in message_characteristics:
                return {
                    'primary': 'nats-kafka',
                    'fallback': 'grpc',
                    'reason': 'High-frequency streaming characteristics',
                    'characteristics': message_characteristics
                }
            elif 'broadcast' in message_characteristics:
                return {
                    'primary': 'nats-kafka',
                    'fallback': 'grpc',
                    'reason': 'Broadcast communication pattern',
                    'characteristics': message_characteristics
                }
            elif 'synchronous' in message_characteristics:
                return {
                    'primary': 'http',
                    'fallback': 'grpc',
                    'reason': 'Synchronous request-response pattern',
                    'characteristics': message_characteristics
                }

        # Default fallback
        return {
            'primary': 'http',
            'fallback': 'grpc',
            'reason': 'Default selection',
            'characteristics': message_characteristics or []
        }

    def should_use_fallback(self, primary_method: str, error_context: Dict[str, Any] = None) -> bool:
        """Determine if fallback transport method should be used"""
        if not error_context:
            return False

        # Network-related errors
        if 'timeout' in str(error_context).lower():
            return True
        if 'connection' in str(error_context).lower():
            return True
        if 'unavailable' in str(error_context).lower():
            return True

        # Service-specific fallback logic
        if primary_method == 'nats-kafka':
            # NATS/Kafka might be down, fallback to gRPC/HTTP
            return True
        elif primary_method == 'grpc':
            # gRPC might have version incompatibility, fallback to HTTP
            return True

        return False


class ContractProcessorIntegration:
    """Integration layer between Python services and JavaScript contract processors"""

    def __init__(self):
        self.validation_bridge = ContractValidationBridge()
        self.transport_selector = TransportMethodSelector()
        self.logger = logging.getLogger("central-hub.contract-processor")

    async def process_inbound_message(self, message_type: str, data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process inbound message using appropriate contract validator and processor"""

        # Select validation method based on message type
        validation_result = None

        if message_type == 'service_registration':
            validation_result = self.validation_bridge.validate_service_registration(data)
        elif message_type == 'service_discovery':
            validation_result = self.validation_bridge.validate_service_discovery(data)
        elif message_type == 'configuration_request':
            validation_result = self.validation_bridge.validate_configuration_request(data)
        elif message_type == 'health_report':
            validation_result = self.validation_bridge.validate_health_report(data)
        elif message_type == 'health_stream':
            validation_result = self.validation_bridge.validate_health_stream(data)

        if not validation_result or not validation_result.get('success'):
            error_msg = validation_result.get('error', 'Validation failed') if validation_result else 'Unknown validation error'
            self.logger.error(f"Contract validation failed for {message_type}: {error_msg}")
            raise ValueError(f"Contract validation failed: {error_msg}")

        # Return processed and validated data
        return {
            'validated_data': validation_result.get('result', {}),
            'transport_info': self.transport_selector.select_transport_method(message_type),
            'processing_metadata': {
                'message_type': message_type,
                'validation_success': True,
                'processed_at': data.get('timestamp') or int(__import__('time').time() * 1000)
            }
        }

    async def process_outbound_message(self, message_type: str, data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process outbound message using appropriate contract formatter"""

        # Select formatting method based on message type
        format_result = None

        if message_type == 'service_discovery_response':
            format_result = self.validation_bridge.format_service_discovery_response(data)
        elif message_type == 'configuration_update':
            format_result = self.validation_bridge.format_configuration_update(data)
        elif message_type == 'scaling_command':
            format_result = self.validation_bridge.format_scaling_command(data)

        if not format_result or not format_result.get('success'):
            error_msg = format_result.get('error', 'Formatting failed') if format_result else 'Unknown formatting error'
            self.logger.error(f"Contract formatting failed for {message_type}: {error_msg}")
            raise ValueError(f"Contract formatting failed: {error_msg}")

        # Return formatted data with transport selection
        return {
            'formatted_data': format_result.get('result', {}),
            'transport_info': self.transport_selector.select_transport_method(message_type),
            'routing_metadata': {
                'message_type': message_type,
                'formatting_success': True,
                'processed_at': data.get('timestamp') or int(__import__('time').time() * 1000)
            }
        }