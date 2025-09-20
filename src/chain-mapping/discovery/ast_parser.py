"""
Embedded Chain Mapping System - AST Parser for Automated Discovery
==================================================================

This module provides automated chain discovery through Abstract Syntax Tree (AST)
analysis of Python service code. It identifies chain patterns by analyzing:

- API endpoint definitions (FastAPI, Flask)
- Function calls and service interactions
- Database operations and queries
- WebSocket handlers and message flows
- Import dependencies and service relationships

Key Features:
- Multi-framework support (FastAPI, Flask, Django)
- Deep code analysis with confidence scoring
- Pattern recognition for common service patterns
- Integration with existing microservice architecture
"""

import ast
import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field
from collections import defaultdict
import importlib.util

from ..core.models import (
    ChainNode, ChainEdge, ChainDependency, DiscoveredChain,
    NodeType, EdgeType, DependencyType, ChainCategory,
    DiscoveryMethod, CriticalityLevel
)


logger = logging.getLogger(__name__)


@dataclass
class CodeLocation:
    """Represents a location in source code."""
    file_path: str
    line_number: int
    column_offset: int
    end_line_number: Optional[int] = None
    end_column_offset: Optional[int] = None


@dataclass
class APIEndpoint:
    """Represents a discovered API endpoint."""
    path: str
    method: str
    function_name: str
    location: CodeLocation
    parameters: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)


@dataclass
class FunctionCall:
    """Represents a function call in the code."""
    caller: str
    callee: str
    location: CodeLocation
    arguments: List[str] = field(default_factory=list)
    is_async: bool = False
    is_external: bool = False
    service_target: Optional[str] = None


@dataclass
class DatabaseOperation:
    """Represents a database operation."""
    operation_type: str  # select, insert, update, delete
    table_name: Optional[str]
    location: CodeLocation
    query_type: str  # raw_sql, orm, query_builder
    is_async: bool = False


@dataclass
class WebSocketHandler:
    """Represents a WebSocket message handler."""
    endpoint: str
    event_type: Optional[str]
    function_name: str
    location: CodeLocation
    is_async: bool = True


@dataclass
class ImportDependency:
    """Represents an import dependency."""
    module_name: str
    imported_names: List[str]
    location: CodeLocation
    is_local: bool = False
    service_reference: Optional[str] = None


class ChainASTParser:
    """
    AST parser for automatic chain discovery from Python source code.

    Analyzes service code to identify chain patterns and relationships
    between different components and services.
    """

    def __init__(self, service_map: Optional[Dict[str, str]] = None):
        """
        Initialize the AST parser.

        Args:
            service_map: Mapping of module patterns to service names
        """
        self.service_map = service_map or self._default_service_map()
        self.framework_patterns = self._init_framework_patterns()
        self.discovered_endpoints: List[APIEndpoint] = []
        self.discovered_calls: List[FunctionCall] = []
        self.discovered_db_ops: List[DatabaseOperation] = []
        self.discovered_websockets: List[WebSocketHandler] = []
        self.discovered_imports: List[ImportDependency] = []

    def _default_service_map(self) -> Dict[str, str]:
        """Default mapping of module patterns to service names."""
        return {
            r'.*api[_-]gateway.*': 'api-gateway',
            r'.*data[_-]bridge.*': 'data-bridge',
            r'.*ai[_-]orchestration.*': 'ai-orchestration',
            r'.*deep[_-]learning.*': 'deep-learning',
            r'.*ai[_-]provider.*': 'ai-provider',
            r'.*ml[_-]processing.*': 'ml-processing',
            r'.*trading[_-]engine.*': 'trading-engine',
            r'.*database[_-]service.*': 'database-service',
            r'.*user[_-]service.*': 'user-service',
            r'.*strategy[_-]optimization.*': 'strategy-optimization',
            r'.*performance[_-]analytics.*': 'performance-analytics'
        }

    def _init_framework_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize framework-specific patterns for detection."""
        return {
            'fastapi': {
                'decorators': ['app.get', 'app.post', 'app.put', 'app.delete', 'app.patch', 'app.options'],
                'route_patterns': [r'@app\.(get|post|put|delete|patch|options)\([\'"]([^\'"]+)[\'"]'],
                'websocket_patterns': [r'@app\.websocket\([\'"]([^\'"]+)[\'"]'],
                'dependency_injection': ['Depends', 'Security', 'BackgroundTasks']
            },
            'flask': {
                'decorators': ['app.route', 'bp.route', 'blueprint.route'],
                'route_patterns': [r'@[^.]+\.route\([\'"]([^\'"]+)[\'"].*methods=\[([^\]]+)\]'],
                'websocket_patterns': [r'@[^.]+\.websocket\([\'"]([^\'"]+)[\'"]'],
                'dependency_injection': ['request', 'session', 'g']
            },
            'django': {
                'decorators': ['api_view', 'require_http_methods'],
                'route_patterns': [r'path\([\'"]([^\'"]+)[\'"]'],
                'websocket_patterns': [r'ws_path\([\'"]([^\'"]+)[\'"]'],
                'dependency_injection': ['csrf_exempt', 'login_required']
            }
        }

    async def parse_service_directory(self, service_path: str) -> List[DiscoveredChain]:
        """
        Parse entire service directory for chain patterns.

        Args:
            service_path: Path to the service directory

        Returns:
            List of discovered chain candidates
        """
        service_path = Path(service_path)
        if not service_path.exists():
            logger.error(f"Service path does not exist: {service_path}")
            return []

        service_name = self._identify_service_name(str(service_path))
        logger.info(f"Parsing service directory: {service_path} (identified as: {service_name})")

        # Clear previous discoveries
        self._clear_discoveries()

        # Find all Python files
        python_files = list(service_path.rglob("*.py"))
        logger.info(f"Found {len(python_files)} Python files to analyze")

        # Parse each file
        for file_path in python_files:
            try:
                await self._parse_python_file(file_path, service_name)
            except Exception as e:
                logger.warning(f"Failed to parse file {file_path}: {e}")

        # Analyze discovered patterns
        discovered_chains = await self._analyze_discovered_patterns(service_name)

        logger.info(f"Discovered {len(discovered_chains)} chain candidates in {service_name}")
        return discovered_chains

    def _identify_service_name(self, path: str) -> str:
        """Identify service name from path."""
        for pattern, service_name in self.service_map.items():
            if re.search(pattern, path, re.IGNORECASE):
                return service_name

        # Fallback: extract from path
        path_parts = Path(path).parts
        for part in reversed(path_parts):
            if 'service' in part.lower() or 'microservice' in part.lower():
                return part.lower().replace('_', '-')

        return 'unknown-service'

    def _clear_discoveries(self):
        """Clear previous discovery results."""
        self.discovered_endpoints.clear()
        self.discovered_calls.clear()
        self.discovered_db_ops.clear()
        self.discovered_websockets.clear()
        self.discovered_imports.clear()

    async def _parse_python_file(self, file_path: Path, service_name: str):
        """Parse a single Python file for chain patterns."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            # Parse AST
            tree = ast.parse(content, filename=str(file_path))

            # Create visitor for this file
            visitor = ChainPatternVisitor(str(file_path), service_name, self.framework_patterns)
            visitor.visit(tree)

            # Collect discoveries
            self.discovered_endpoints.extend(visitor.endpoints)
            self.discovered_calls.extend(visitor.function_calls)
            self.discovered_db_ops.extend(visitor.db_operations)
            self.discovered_websockets.extend(visitor.websocket_handlers)
            self.discovered_imports.extend(visitor.import_dependencies)

        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")

    async def _analyze_discovered_patterns(self, service_name: str) -> List[DiscoveredChain]:
        """Analyze discovered patterns to create chain candidates."""
        chains = []

        # Analyze API request chains
        api_chains = await self._analyze_api_chains(service_name)
        chains.extend(api_chains)

        # Analyze data flow chains
        data_chains = await self._analyze_data_flow_chains(service_name)
        chains.extend(data_chains)

        # Analyze WebSocket chains
        ws_chains = await self._analyze_websocket_chains(service_name)
        chains.extend(ws_chains)

        # Analyze service communication chains
        comm_chains = await self._analyze_communication_chains(service_name)
        chains.extend(comm_chains)

        return chains

    async def _analyze_api_chains(self, service_name: str) -> List[DiscoveredChain]:
        """Analyze API endpoints to discover request-response chains."""
        chains = []

        for endpoint in self.discovered_endpoints:
            # Create chain for this endpoint
            chain_id = f"B{len(chains) + 1}"  # Service communication category

            # Create nodes
            nodes = [
                ChainNode(
                    id="api_entry",
                    type=NodeType.API_ENDPOINT,
                    service_name=service_name,
                    component_name=endpoint.function_name,
                    config={
                        "path": endpoint.path,
                        "method": endpoint.method,
                        "parameters": endpoint.parameters
                    }
                )
            ]

            # Add dependency nodes
            for dep in endpoint.dependencies:
                if self._is_database_dependency(dep):
                    nodes.append(ChainNode(
                        id=f"db_{dep}",
                        type=NodeType.DATABASE,
                        service_name="database-service",
                        component_name=dep
                    ))
                elif self._is_external_service(dep):
                    service = self._identify_service_from_dependency(dep)
                    nodes.append(ChainNode(
                        id=f"service_{dep}",
                        type=NodeType.SERVICE,
                        service_name=service,
                        component_name=dep
                    ))

            # Create edges
            edges = []
            for i, dep_node in enumerate(nodes[1:], 1):
                edges.append(ChainEdge(
                    source_node="api_entry",
                    target_node=dep_node.id,
                    type=self._determine_edge_type(dep_node.type),
                    latency_sla=self._estimate_latency_sla(dep_node.type)
                ))

            # Create discovered chain
            chain = DiscoveredChain(
                proposed_chain_id=chain_id,
                name=f"{service_name.title()} API Chain - {endpoint.path}",
                category=ChainCategory.SERVICE_COMMUNICATION,
                description=f"API request chain for {endpoint.method} {endpoint.path}",
                discovery_method=DiscoveryMethod.AST_PARSER,
                confidence_score=self._calculate_confidence_score(nodes, edges),
                nodes=nodes,
                edges=edges,
                evidence={
                    "source_file": endpoint.location.file_path,
                    "line_number": endpoint.location.line_number,
                    "endpoint_details": {
                        "path": endpoint.path,
                        "method": endpoint.method,
                        "function": endpoint.function_name,
                        "decorators": endpoint.decorators
                    },
                    "dependencies": endpoint.dependencies
                }
            )

            chains.append(chain)

        return chains

    async def _analyze_data_flow_chains(self, service_name: str) -> List[DiscoveredChain]:
        """Analyze database operations to discover data flow chains."""
        chains = []

        # Group database operations by type and table
        db_groups = defaultdict(list)
        for db_op in self.discovered_db_ops:
            key = f"{db_op.operation_type}_{db_op.table_name or 'unknown'}"
            db_groups[key].append(db_op)

        for group_key, operations in db_groups.items():
            if len(operations) < 2:  # Need at least 2 operations for a chain
                continue

            chain_id = f"A{len(chains) + 1}"  # Data flow category

            # Create nodes for data pipeline
            nodes = [
                ChainNode(
                    id="data_source",
                    type=NodeType.SERVICE,
                    service_name=service_name,
                    component_name="data_processor"
                ),
                ChainNode(
                    id="data_validation",
                    type=NodeType.SERVICE,
                    service_name=service_name,
                    component_name="data_validator"
                ),
                ChainNode(
                    id="data_storage",
                    type=NodeType.DATABASE,
                    service_name="database-service",
                    component_name=operations[0].table_name or "unknown_table"
                )
            ]

            # Create edges
            edges = [
                ChainEdge(
                    source_node="data_source",
                    target_node="data_validation",
                    type=EdgeType.HTTP_REQUEST,
                    latency_sla=100
                ),
                ChainEdge(
                    source_node="data_validation",
                    target_node="data_storage",
                    type=EdgeType.DATABASE_QUERY,
                    latency_sla=50
                )
            ]

            # Create discovered chain
            chain = DiscoveredChain(
                proposed_chain_id=chain_id,
                name=f"{service_name.title()} Data Flow - {group_key}",
                category=ChainCategory.DATA_FLOW,
                description=f"Data flow chain for {group_key} operations",
                discovery_method=DiscoveryMethod.AST_PARSER,
                confidence_score=self._calculate_confidence_score(nodes, edges),
                nodes=nodes,
                edges=edges,
                evidence={
                    "database_operations": [
                        {
                            "operation": op.operation_type,
                            "table": op.table_name,
                            "file": op.location.file_path,
                            "line": op.location.line_number
                        }
                        for op in operations
                    ]
                }
            )

            chains.append(chain)

        return chains

    async def _analyze_websocket_chains(self, service_name: str) -> List[DiscoveredChain]:
        """Analyze WebSocket handlers to discover real-time communication chains."""
        chains = []

        for ws_handler in self.discovered_websockets:
            chain_id = f"C{len(chains) + 1}"  # User experience category

            # Create nodes for WebSocket chain
            nodes = [
                ChainNode(
                    id="ws_connection",
                    type=NodeType.WEBSOCKET,
                    service_name=service_name,
                    component_name="connection_manager"
                ),
                ChainNode(
                    id="ws_handler",
                    type=NodeType.SERVICE,
                    service_name=service_name,
                    component_name=ws_handler.function_name
                ),
                ChainNode(
                    id="ws_broadcast",
                    type=NodeType.WEBSOCKET,
                    service_name=service_name,
                    component_name="message_broadcaster"
                )
            ]

            # Create edges
            edges = [
                ChainEdge(
                    source_node="ws_connection",
                    target_node="ws_handler",
                    type=EdgeType.WEBSOCKET_MESSAGE,
                    latency_sla=25
                ),
                ChainEdge(
                    source_node="ws_handler",
                    target_node="ws_broadcast",
                    type=EdgeType.WEBSOCKET_MESSAGE,
                    latency_sla=10
                )
            ]

            # Create discovered chain
            chain = DiscoveredChain(
                proposed_chain_id=chain_id,
                name=f"{service_name.title()} WebSocket Chain - {ws_handler.endpoint}",
                category=ChainCategory.USER_EXPERIENCE,
                description=f"WebSocket communication chain for {ws_handler.endpoint}",
                discovery_method=DiscoveryMethod.AST_PARSER,
                confidence_score=self._calculate_confidence_score(nodes, edges),
                nodes=nodes,
                edges=edges,
                evidence={
                    "websocket_handler": {
                        "endpoint": ws_handler.endpoint,
                        "event_type": ws_handler.event_type,
                        "function": ws_handler.function_name,
                        "file": ws_handler.location.file_path,
                        "line": ws_handler.location.line_number
                    }
                }
            )

            chains.append(chain)

        return chains

    async def _analyze_communication_chains(self, service_name: str) -> List[DiscoveredChain]:
        """Analyze function calls to discover inter-service communication chains."""
        chains = []

        # Group external function calls by target service
        external_calls = [call for call in self.discovered_calls if call.is_external]
        service_calls = defaultdict(list)

        for call in external_calls:
            target_service = call.service_target or self._identify_service_from_call(call)
            service_calls[target_service].append(call)

        for target_service, calls in service_calls.items():
            if target_service == service_name:  # Skip self-calls
                continue

            chain_id = f"B{len(chains) + 10}"  # Service communication category

            # Create nodes for service communication
            nodes = [
                ChainNode(
                    id="source_service",
                    type=NodeType.SERVICE,
                    service_name=service_name,
                    component_name="service_client"
                ),
                ChainNode(
                    id="target_service",
                    type=NodeType.SERVICE,
                    service_name=target_service,
                    component_name="service_handler"
                )
            ]

            # Create edge
            edges = [
                ChainEdge(
                    source_node="source_service",
                    target_node="target_service",
                    type=EdgeType.HTTP_REQUEST,
                    latency_sla=200
                )
            ]

            # Create discovered chain
            chain = DiscoveredChain(
                proposed_chain_id=chain_id,
                name=f"{service_name.title()} to {target_service.title()} Communication",
                category=ChainCategory.SERVICE_COMMUNICATION,
                description=f"Inter-service communication from {service_name} to {target_service}",
                discovery_method=DiscoveryMethod.AST_PARSER,
                confidence_score=self._calculate_confidence_score(nodes, edges),
                nodes=nodes,
                edges=edges,
                evidence={
                    "function_calls": [
                        {
                            "caller": call.caller,
                            "callee": call.callee,
                            "file": call.location.file_path,
                            "line": call.location.line_number,
                            "is_async": call.is_async
                        }
                        for call in calls
                    ]
                }
            )

            chains.append(chain)

        return chains

    def _is_database_dependency(self, dependency: str) -> bool:
        """Check if a dependency is database-related."""
        db_patterns = ['db', 'database', 'session', 'query', 'sql', 'orm', 'model']
        return any(pattern in dependency.lower() for pattern in db_patterns)

    def _is_external_service(self, dependency: str) -> bool:
        """Check if a dependency is an external service."""
        service_patterns = ['client', 'service', 'api', 'http', 'request']
        return any(pattern in dependency.lower() for pattern in service_patterns)

    def _identify_service_from_dependency(self, dependency: str) -> str:
        """Identify service name from dependency string."""
        for pattern, service_name in self.service_map.items():
            if re.search(pattern, dependency, re.IGNORECASE):
                return service_name
        return 'external-service'

    def _identify_service_from_call(self, call: FunctionCall) -> str:
        """Identify target service from function call."""
        # Analyze the callee to determine target service
        callee_lower = call.callee.lower()

        for pattern, service_name in self.service_map.items():
            pattern_clean = pattern.replace(r'.*', '').replace(r'[_-]', '').replace('.*', '')
            if pattern_clean in callee_lower:
                return service_name

        return 'unknown-service'

    def _determine_edge_type(self, node_type: NodeType) -> EdgeType:
        """Determine edge type based on target node type."""
        mapping = {
            NodeType.DATABASE: EdgeType.DATABASE_QUERY,
            NodeType.CACHE: EdgeType.CACHE_OPERATION,
            NodeType.QUEUE: EdgeType.EVENT_PUBLISH,
            NodeType.AI_MODEL: EdgeType.AI_INFERENCE,
            NodeType.WEBSOCKET: EdgeType.WEBSOCKET_MESSAGE,
            NodeType.EXTERNAL_API: EdgeType.HTTP_REQUEST
        }
        return mapping.get(node_type, EdgeType.HTTP_REQUEST)

    def _estimate_latency_sla(self, node_type: NodeType) -> int:
        """Estimate appropriate latency SLA based on node type."""
        sla_mapping = {
            NodeType.DATABASE: 50,
            NodeType.CACHE: 5,
            NodeType.QUEUE: 10,
            NodeType.AI_MODEL: 500,
            NodeType.WEBSOCKET: 25,
            NodeType.EXTERNAL_API: 1000,
            NodeType.SERVICE: 200
        }
        return sla_mapping.get(node_type, 100)

    def _calculate_confidence_score(self, nodes: List[ChainNode], edges: List[ChainEdge]) -> float:
        """Calculate confidence score for discovered chain."""
        base_score = 0.7  # Base confidence

        # Adjust based on evidence quality
        if len(nodes) >= 2:
            base_score += 0.1
        if len(edges) >= 1:
            base_score += 0.1

        # Penalize if too simple or too complex
        if len(nodes) == 1:
            base_score -= 0.2
        elif len(nodes) > 10:
            base_score -= 0.1

        return min(max(base_score, 0.0), 1.0)


class ChainPatternVisitor(ast.NodeVisitor):
    """AST visitor for identifying chain patterns in Python code."""

    def __init__(self, file_path: str, service_name: str, framework_patterns: Dict[str, Any]):
        self.file_path = file_path
        self.service_name = service_name
        self.framework_patterns = framework_patterns

        # Discovery collections
        self.endpoints: List[APIEndpoint] = []
        self.function_calls: List[FunctionCall] = []
        self.db_operations: List[DatabaseOperation] = []
        self.websocket_handlers: List[WebSocketHandler] = []
        self.import_dependencies: List[ImportDependency] = []

        # Analysis state
        self.current_function = None
        self.current_class = None
        self.imports = {}

    def visit_Import(self, node: ast.Import):
        """Visit import statements."""
        for alias in node.names:
            location = CodeLocation(self.file_path, node.lineno, node.col_offset)

            import_dep = ImportDependency(
                module_name=alias.name,
                imported_names=[alias.name],
                location=location,
                is_local=self._is_local_import(alias.name),
                service_reference=self._extract_service_reference(alias.name)
            )

            self.import_dependencies.append(import_dep)
            self.imports[alias.asname or alias.name] = alias.name

        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visit from-import statements."""
        if node.module:
            location = CodeLocation(self.file_path, node.lineno, node.col_offset)
            imported_names = [alias.name for alias in node.names]

            import_dep = ImportDependency(
                module_name=node.module,
                imported_names=imported_names,
                location=location,
                is_local=self._is_local_import(node.module),
                service_reference=self._extract_service_reference(node.module)
            )

            self.import_dependencies.append(import_dep)

            # Track imports for later reference
            for alias in node.names:
                self.imports[alias.asname or alias.name] = f"{node.module}.{alias.name}"

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit function definitions."""
        old_function = self.current_function
        self.current_function = node.name

        # Check for API endpoint decorators
        self._check_api_decorators(node)

        # Check for WebSocket decorators
        self._check_websocket_decorators(node)

        self.generic_visit(node)
        self.current_function = old_function

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit async function definitions."""
        old_function = self.current_function
        self.current_function = node.name

        # Check for API endpoint decorators
        self._check_api_decorators(node)

        # Check for WebSocket decorators
        self._check_websocket_decorators(node)

        self.generic_visit(node)
        self.current_function = old_function

    def visit_Call(self, node: ast.Call):
        """Visit function calls."""
        # Extract function call information
        call_info = self._extract_call_info(node)
        if call_info:
            self.function_calls.append(call_info)

        # Check for database operations
        db_op = self._extract_database_operation(node)
        if db_op:
            self.db_operations.append(db_op)

        self.generic_visit(node)

    def _check_api_decorators(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]):
        """Check for API endpoint decorators."""
        for decorator in node.decorator_list:
            decorator_info = self._analyze_decorator(decorator)
            if decorator_info and decorator_info.get('type') == 'api_endpoint':
                location = CodeLocation(self.file_path, node.lineno, node.col_offset)

                endpoint = APIEndpoint(
                    path=decorator_info.get('path', '/unknown'),
                    method=decorator_info.get('method', 'GET'),
                    function_name=node.name,
                    location=location,
                    parameters=self._extract_function_parameters(node),
                    decorators=[decorator_info.get('decorator', 'unknown')]
                )

                self.endpoints.append(endpoint)

    def _check_websocket_decorators(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]):
        """Check for WebSocket decorators."""
        for decorator in node.decorator_list:
            decorator_info = self._analyze_decorator(decorator)
            if decorator_info and decorator_info.get('type') == 'websocket':
                location = CodeLocation(self.file_path, node.lineno, node.col_offset)

                ws_handler = WebSocketHandler(
                    endpoint=decorator_info.get('path', '/ws'),
                    event_type=decorator_info.get('event_type'),
                    function_name=node.name,
                    location=location,
                    is_async=isinstance(node, ast.AsyncFunctionDef)
                )

                self.websocket_handlers.append(ws_handler)

    def _analyze_decorator(self, decorator: ast.expr) -> Optional[Dict[str, Any]]:
        """Analyze a decorator to extract routing information."""
        if isinstance(decorator, ast.Call):
            # Handle @app.route(), @app.get(), etc.
            if isinstance(decorator.func, ast.Attribute):
                method_name = decorator.func.attr

                # Check FastAPI patterns
                if method_name in ['get', 'post', 'put', 'delete', 'patch', 'options']:
                    path = self._extract_string_arg(decorator, 0)
                    return {
                        'type': 'api_endpoint',
                        'method': method_name.upper(),
                        'path': path,
                        'decorator': f"app.{method_name}"
                    }

                # Check Flask patterns
                elif method_name == 'route':
                    path = self._extract_string_arg(decorator, 0)
                    methods = self._extract_methods_from_decorator(decorator)
                    return {
                        'type': 'api_endpoint',
                        'method': methods[0] if methods else 'GET',
                        'path': path,
                        'decorator': 'route'
                    }

                # Check WebSocket patterns
                elif method_name == 'websocket':
                    path = self._extract_string_arg(decorator, 0)
                    return {
                        'type': 'websocket',
                        'path': path,
                        'decorator': 'websocket'
                    }

        return None

    def _extract_string_arg(self, call_node: ast.Call, arg_index: int) -> str:
        """Extract string argument from function call."""
        if len(call_node.args) > arg_index:
            arg = call_node.args[arg_index]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                return arg.value
            elif isinstance(arg, ast.Str):  # Python < 3.8 compatibility
                return arg.s
        return '/unknown'

    def _extract_methods_from_decorator(self, decorator: ast.Call) -> List[str]:
        """Extract HTTP methods from Flask route decorator."""
        methods = []
        for keyword in decorator.keywords:
            if keyword.arg == 'methods':
                if isinstance(keyword.value, ast.List):
                    for method_node in keyword.value.elts:
                        if isinstance(method_node, ast.Constant):
                            methods.append(method_node.value)
                        elif isinstance(method_node, ast.Str):
                            methods.append(method_node.s)
        return methods

    def _extract_function_parameters(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> List[str]:
        """Extract function parameter names."""
        parameters = []
        for arg in node.args.args:
            if arg.arg != 'self':  # Skip self parameter
                parameters.append(arg.arg)
        return parameters

    def _extract_call_info(self, node: ast.Call) -> Optional[FunctionCall]:
        """Extract function call information."""
        location = CodeLocation(self.file_path, node.lineno, node.col_offset)

        # Get caller (current function)
        caller = self.current_function or 'module_level'

        # Get callee
        callee = self._get_call_name(node.func)
        if not callee:
            return None

        # Check if it's an external call
        is_external = self._is_external_call(callee)
        service_target = None
        if is_external:
            service_target = self._identify_service_from_call_name(callee)

        # Extract arguments
        arguments = []
        for arg in node.args:
            if isinstance(arg, ast.Constant):
                arguments.append(str(arg.value))
            elif isinstance(arg, ast.Name):
                arguments.append(arg.id)

        return FunctionCall(
            caller=caller,
            callee=callee,
            location=location,
            arguments=arguments,
            is_async=self._is_async_context(),
            is_external=is_external,
            service_target=service_target
        )

    def _get_call_name(self, func_node: ast.expr) -> Optional[str]:
        """Get the full name of a function call."""
        if isinstance(func_node, ast.Name):
            return func_node.id
        elif isinstance(func_node, ast.Attribute):
            value_name = self._get_call_name(func_node.value)
            if value_name:
                return f"{value_name}.{func_node.attr}"
            return func_node.attr
        return None

    def _is_external_call(self, call_name: str) -> bool:
        """Check if a call is to an external service."""
        external_patterns = [
            'requests.', 'httpx.', 'aiohttp.', 'urllib.',
            'client.', 'service.', 'api.'
        ]
        return any(pattern in call_name for pattern in external_patterns)

    def _identify_service_from_call_name(self, call_name: str) -> Optional[str]:
        """Identify target service from call name."""
        # This is a simplified implementation
        # In practice, you'd have more sophisticated service discovery
        if 'database' in call_name.lower() or 'db' in call_name.lower():
            return 'database-service'
        elif 'ai' in call_name.lower() or 'ml' in call_name.lower():
            return 'ai-provider'
        elif 'trading' in call_name.lower():
            return 'trading-engine'
        return None

    def _extract_database_operation(self, node: ast.Call) -> Optional[DatabaseOperation]:
        """Extract database operation information."""
        call_name = self._get_call_name(node.func)
        if not call_name:
            return None

        # Check for common database operation patterns
        db_patterns = {
            'select': ['select', 'query', 'find', 'get'],
            'insert': ['insert', 'create', 'add'],
            'update': ['update', 'modify', 'set'],
            'delete': ['delete', 'remove', 'drop']
        }

        operation_type = None
        for op_type, patterns in db_patterns.items():
            if any(pattern in call_name.lower() for pattern in patterns):
                operation_type = op_type
                break

        if not operation_type:
            return None

        location = CodeLocation(self.file_path, node.lineno, node.col_offset)

        # Try to extract table name from arguments
        table_name = None
        for arg in node.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                # Simple heuristic: if it looks like a table name
                if '_' in arg.value or arg.value.islower():
                    table_name = arg.value
                    break

        return DatabaseOperation(
            operation_type=operation_type,
            table_name=table_name,
            location=location,
            query_type='orm',  # Assume ORM for now
            is_async=self._is_async_context()
        )

    def _is_async_context(self) -> bool:
        """Check if we're in an async context."""
        # This is a simplified check
        return self.current_function and 'async' in str(self.current_function)

    def _is_local_import(self, module_name: str) -> bool:
        """Check if an import is local to the project."""
        local_patterns = ['.', 'src', 'app', 'services', 'api', 'business', 'infrastructure']
        return any(pattern in module_name for pattern in local_patterns)

    def _extract_service_reference(self, module_name: str) -> Optional[str]:
        """Extract service reference from module name."""
        for pattern, service_name in {
            'database': 'database-service',
            'ai': 'ai-provider',
            'trading': 'trading-engine',
            'user': 'user-service'
        }.items():
            if pattern in module_name.lower():
                return service_name
        return None


# Export main classes
__all__ = ['ChainASTParser', 'APIEndpoint', 'FunctionCall', 'DatabaseOperation', 'WebSocketHandler', 'ImportDependency']