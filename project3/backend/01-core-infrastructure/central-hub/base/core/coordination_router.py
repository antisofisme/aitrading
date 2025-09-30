"""
Central Hub - Coordination Router
Intelligent message routing and transport method selection
Enhanced with contract-based transport selection
"""

import time
from typing import Dict, List, Optional, Any, Tuple
import logging

import sys
from pathlib import Path

# Add shared directory to Python path
shared_dir = Path(__file__).parent.parent.parent / "shared"
sys.path.insert(0, str(shared_dir))

from components.utils.contract_bridge import TransportMethodSelector


class CoordinationRouter:
    """Handles intelligent routing and transport method selection"""

    def __init__(self):
        self.logger = logging.getLogger("central-hub.coordination-router")
        self.transport_configs = self._load_transport_configurations()
        self.routing_metrics: Dict[str, Dict[str, Any]] = {}
        self.contract_transport_selector = TransportMethodSelector()

    def _load_transport_configurations(self) -> Dict[str, Dict[str, Any]]:
        """Load transport method configurations"""
        return {
            # Service Discovery & Registration (gRPC - Strong typing, streaming)
            'service_registration': {
                'primary_method': 'grpc',
                'fallback_method': 'http',
                'volume': 'medium',
                'critical_path': True,
                'timeout_ms': 5000,
                'reasoning': 'Strong typing, streaming, load balancing'
            },
            'service_discovery': {
                'primary_method': 'grpc',
                'fallback_method': 'http',
                'volume': 'medium',
                'critical_path': True,
                'timeout_ms': 3000,
                'reasoning': 'Protocol Buffers efficiency, streaming'
            },

            # Configuration Management (HTTP for pulls, gRPC for pushes)
            'configuration_request': {
                'primary_method': 'http',
                'fallback_method': 'grpc',
                'volume': 'low',
                'critical_path': True,
                'timeout_ms': 10000,
                'reasoning': 'Simple, reliable, fallback-friendly'
            },
            'configuration_update': {
                'primary_method': 'grpc',
                'fallback_method': 'http',
                'volume': 'low',
                'critical_path': True,
                'timeout_ms': 5000,
                'reasoning': 'Real-time broadcasts, streaming'
            },

            # Monitoring & Metrics (NATS+Kafka - High throughput)
            'health_report': {
                'primary_method': 'nats-kafka',
                'fallback_method': 'http',
                'volume': 'high',
                'critical_path': False,
                'timeout_ms': 2000,
                'reasoning': 'High throughput, durability'
            },
            'metrics_stream': {
                'primary_method': 'nats-kafka',
                'fallback_method': 'grpc',
                'volume': 'high',
                'critical_path': False,
                'timeout_ms': 1000,
                'reasoning': 'Continuous streaming, persistence'
            },

            # Workflow Coordination (gRPC for planning, NATS+Kafka for execution)
            'workflow_coordination_request': {
                'primary_method': 'grpc',
                'fallback_method': 'http',
                'volume': 'medium',
                'critical_path': True,
                'timeout_ms': 15000,
                'reasoning': 'Strong typing, request-response'
            },
            'workflow_execution_command': {
                'primary_method': 'nats-kafka',
                'fallback_method': 'grpc',
                'volume': 'high',
                'critical_path': True,
                'timeout_ms': 3000,
                'reasoning': 'High-speed commands, audit trail'
            },

            # System Operations (NATS+Kafka - Real-time decisions)
            'circuit_breaker_status': {
                'primary_method': 'nats-kafka',
                'fallback_method': 'grpc',
                'volume': 'high',
                'critical_path': True,
                'timeout_ms': 1000,
                'reasoning': 'Real-time decisions, reliability'
            },
            'scaling_command': {
                'primary_method': 'nats-kafka',
                'fallback_method': 'grpc',
                'volume': 'medium',
                'critical_path': True,
                'timeout_ms': 5000,
                'reasoning': 'Command distribution, persistence'
            }
        }

    def select_transport_method(self, message_type: str, data: Dict[str, Any] = None,
                              target_service: str = None) -> Tuple[str, Dict[str, Any]]:
        """Intelligently select transport method for message - Enhanced with contract-based selection"""

        # First, try contract-based transport selection
        try:
            # Determine message characteristics from data
            message_characteristics = self._extract_message_characteristics(data, message_type)

            # Use contract-based transport selector
            contract_selection = self.contract_transport_selector.select_transport_method(
                message_type, message_characteristics
            )

            # Check if we should override based on our internal metrics
            selected_method = contract_selection['primary']
            if self._should_use_fallback(message_type, selected_method):
                selected_method = contract_selection['fallback']
                self.logger.info(f"Contract-based fallback for {message_type}: {selected_method}")

            # Create enhanced config combining contract and internal data
            enhanced_config = {
                'primary_method': contract_selection['primary'],
                'fallback_method': contract_selection['fallback'],
                'contract_reason': contract_selection['reason'],
                'contract_characteristics': contract_selection['characteristics'],
                'volume': self._estimate_volume(message_type, data),
                'critical_path': self._is_critical_path(message_type, data),
                'timeout_ms': self._get_timeout_for_method(selected_method),
                'selection_source': 'contract_based'
            }

            self.logger.info(f"✅ Contract-based transport selection for {message_type}: {selected_method} ({contract_selection['reason']})")
            return selected_method, enhanced_config

        except Exception as e:
            self.logger.warning(f"Contract-based selection failed for {message_type}: {str(e)}, falling back to internal selection")

        # Fallback to original internal logic
        config = self.transport_configs.get(message_type)

        if not config:
            # Auto-selection for unknown message types
            return self._auto_select_transport(message_type, data, target_service)

        # Check if fallback is needed based on metrics
        selected_method = config['primary_method']
        if self._should_use_fallback(message_type, selected_method):
            selected_method = config['fallback_method']
            self.logger.info(f"Using fallback transport for {message_type}: {selected_method}")

        # Mark as internal selection
        config['selection_source'] = 'internal_logic'
        return selected_method, config

    def _auto_select_transport(self, message_type: str, data: Dict[str, Any] = None,
                             target_service: str = None) -> Tuple[str, Dict[str, Any]]:
        """Auto-select transport method based on data characteristics"""
        data_size = self._estimate_data_size(data) if data else 0
        is_critical = self._is_critical_path(message_type, data)
        volume = self._estimate_volume(message_type, data)

        # Auto-selection logic
        if volume == 'high' and is_critical:
            method = 'nats-kafka'
            reasoning = 'High volume + critical path = NATS+Kafka for reliability'
        elif volume == 'medium' and is_critical:
            method = 'grpc'
            reasoning = 'Medium volume + critical path = gRPC for efficiency'
        elif data_size > 1024 * 1024:  # > 1MB
            method = 'nats-kafka'
            reasoning = 'Large data size = NATS+Kafka for throughput'
        else:
            method = 'http'
            reasoning = 'Default to HTTP for simplicity and reliability'

        config = {
            'primary_method': method,
            'fallback_method': 'http',
            'volume': volume,
            'critical_path': is_critical,
            'timeout_ms': 10000,
            'reasoning': reasoning,
            'auto_selected': True
        }

        self.logger.info(f"Auto-selected {method} for {message_type}: {reasoning}")
        return method, config

    def _should_use_fallback(self, message_type: str, primary_method: str) -> bool:
        """Determine if fallback method should be used based on metrics"""
        metrics = self.routing_metrics.get(f"{message_type}:{primary_method}", {})

        # Use fallback if primary method has high failure rate
        failure_rate = metrics.get('failure_rate', 0)
        if failure_rate > 0.2:  # 20% failure rate threshold
            return True

        # Use fallback if primary method has high latency
        avg_latency = metrics.get('avg_latency_ms', 0)
        config = self.transport_configs.get(message_type, {})
        timeout = config.get('timeout_ms', 10000)
        if avg_latency > timeout * 0.8:  # 80% of timeout threshold
            return True

        return False

    def _extract_message_characteristics(self, data: Dict[str, Any] = None, message_type: str = "") -> List[str]:
        """Extract message characteristics for contract-based transport selection"""
        characteristics = []

        # Analyze message type patterns
        message_lower = message_type.lower()

        if 'stream' in message_lower or 'metrics' in message_lower or 'health' in message_lower:
            characteristics.extend(['streaming', 'high-frequency'])

        if 'command' in message_lower or 'scaling' in message_lower or 'update' in message_lower:
            characteristics.extend(['broadcast', 'fire-and-forget'])

        if 'request' in message_lower or 'discovery' in message_lower or 'registration' in message_lower:
            characteristics.extend(['synchronous', 'request-response'])

        if 'config' in message_lower or 'coordination' in message_lower:
            characteristics.extend(['reliable-delivery', 'medium-frequency'])

        # Analyze data characteristics
        if data:
            data_size = self._estimate_data_size(data)
            if data_size > 1024 * 1024:  # > 1MB
                characteristics.append('high-throughput')
            elif data_size > 10 * 1024:  # > 10KB
                characteristics.append('medium-volume')
            else:
                characteristics.append('low-volume')

            # Check for urgency indicators
            if data.get('priority') in ['high', 'emergency', 'critical']:
                characteristics.append('urgent')

            # Check for batch processing indicators
            if data.get('batch_size', 0) > 1 or 'batch' in str(data).lower():
                characteristics.append('batch-processing')

        # Check critical path
        if self._is_critical_path(message_type, data):
            characteristics.append('critical-path')

        return list(set(characteristics))  # Remove duplicates

    def _get_timeout_for_method(self, transport_method: str) -> int:
        """Get appropriate timeout for transport method"""
        timeout_map = {
            'http': 10000,      # 10 seconds
            'grpc': 5000,       # 5 seconds
            'nats-kafka': 3000  # 3 seconds
        }
        return timeout_map.get(transport_method, 10000)

    def _estimate_data_size(self, data: Any) -> int:
        """Estimate data size in bytes"""
        if not data:
            return 0
        if isinstance(data, str):
            return len(data.encode('utf-8'))
        if isinstance(data, bytes):
            return len(data)
        if isinstance(data, dict):
            import json
            return len(json.dumps(data).encode('utf-8'))
        return 0

    def _is_critical_path(self, message_type: str, data: Dict[str, Any] = None) -> bool:
        """Determine if message is on critical path"""
        critical_keywords = [
            'registration', 'discovery', 'configuration', 'workflow',
            'circuit_breaker', 'scaling', 'auth', 'security'
        ]
        return any(keyword in message_type.lower() for keyword in critical_keywords)

    def _estimate_volume(self, message_type: str, data: Dict[str, Any] = None) -> str:
        """Estimate message volume based on type and characteristics"""
        high_volume_types = ['health', 'metrics', 'stream', 'execution', 'monitoring']
        low_volume_types = ['configuration', 'registration', 'auth']

        message_lower = message_type.lower()

        if any(keyword in message_lower for keyword in high_volume_types):
            return 'high'
        elif any(keyword in message_lower for keyword in low_volume_types):
            return 'low'
        else:
            return 'medium'

    def record_routing_metrics(self, message_type: str, transport_method: str,
                             success: bool, latency_ms: int):
        """Record routing performance metrics"""
        key = f"{message_type}:{transport_method}"

        if key not in self.routing_metrics:
            self.routing_metrics[key] = {
                'total_requests': 0,
                'successful_requests': 0,
                'total_latency_ms': 0,
                'failure_rate': 0,
                'avg_latency_ms': 0
            }

        metrics = self.routing_metrics[key]
        metrics['total_requests'] += 1
        metrics['total_latency_ms'] += latency_ms

        if success:
            metrics['successful_requests'] += 1

        # Update calculated metrics
        metrics['failure_rate'] = 1 - (metrics['successful_requests'] / metrics['total_requests'])
        metrics['avg_latency_ms'] = metrics['total_latency_ms'] / metrics['total_requests']

    def get_routing_statistics(self) -> Dict[str, Any]:
        """Get routing performance statistics"""
        total_requests = sum(m['total_requests'] for m in self.routing_metrics.values())
        total_failures = sum(m['total_requests'] - m['successful_requests']
                           for m in self.routing_metrics.values())

        return {
            'total_requests_routed': total_requests,
            'overall_failure_rate': total_failures / total_requests if total_requests > 0 else 0,
            'transport_method_usage': self._get_transport_usage_stats(),
            'routing_metrics_by_type': self.routing_metrics,
            'auto_selections': len([c for c in self.transport_configs.values()
                                  if c.get('auto_selected', False)])
        }

    def _get_transport_usage_stats(self) -> Dict[str, int]:
        """Get transport method usage statistics"""
        usage = {'grpc': 0, 'nats-kafka': 0, 'http': 0}

        for config in self.transport_configs.values():
            primary = config.get('primary_method', 'http')
            if primary in usage:
                usage[primary] += 1

        return usage

    async def health_check(self) -> Dict[str, Any]:
        """Health check for coordination router"""
        stats = self.get_routing_statistics()

        return {
            'status': 'operational',
            'configured_routes': len(self.transport_configs),
            'total_requests_routed': stats['total_requests_routed'],
            'overall_failure_rate': stats['overall_failure_rate'],
            'transport_methods': list(stats['transport_method_usage'].keys()),
            'auto_selections': stats['auto_selections']
        }