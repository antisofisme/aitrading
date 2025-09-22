"""
Embedded Chain Mapping System - Chain Registry
===============================================

The ChainRegistry is the central component responsible for managing chain definitions,
relationships, and metadata. It provides a unified interface for all chain operations
and integrates with the existing database infrastructure.

Key Features:
- Thread-safe chain management
- Automatic validation and consistency checking
- Caching for performance optimization
- Integration with existing database services
- Real-time change notifications
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Tuple
from uuid import uuid4
import json

from sqlalchemy import create_engine, select, update, delete, and_, or_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from redis import Redis
from pydantic import ValidationError

from .models import (
    ChainDefinition, ChainDefinitionCreate, ChainDefinitionUpdate,
    ChainCategory, ChainStatus, ValidationResult, DiscoveredChain,
    ChainNode, ChainEdge, ChainDependency
)


logger = logging.getLogger(__name__)


class ChainRegistryError(Exception):
    """Base exception for chain registry operations."""
    pass


class ChainNotFoundError(ChainRegistryError):
    """Raised when a requested chain is not found."""
    pass


class ChainValidationError(ChainRegistryError):
    """Raised when chain validation fails."""
    pass


class DependencyGraphNode:
    """Represents a node in the dependency graph."""

    def __init__(self, chain_id: str, chain_def: ChainDefinition):
        self.chain_id = chain_id
        self.chain_def = chain_def
        self.dependencies: Set[str] = set()
        self.dependents: Set[str] = set()

    def add_dependency(self, dependency_chain_id: str):
        """Add a dependency to this chain."""
        self.dependencies.add(dependency_chain_id)

    def add_dependent(self, dependent_chain_id: str):
        """Add a dependent to this chain."""
        self.dependents.add(dependent_chain_id)


class DependencyGraph:
    """Manages the dependency relationships between chains."""

    def __init__(self):
        self.nodes: Dict[str, DependencyGraphNode] = {}

    def add_chain(self, chain_def: ChainDefinition):
        """Add a chain to the dependency graph."""
        if chain_def.id not in self.nodes:
            self.nodes[chain_def.id] = DependencyGraphNode(chain_def.id, chain_def)

    def add_dependency(self, chain_id: str, dependency_id: str):
        """Add a dependency relationship."""
        if chain_id in self.nodes and dependency_id in self.nodes:
            self.nodes[chain_id].add_dependency(dependency_id)
            self.nodes[dependency_id].add_dependent(chain_id)

    def get_dependencies(self, chain_id: str, recursive: bool = False) -> Set[str]:
        """Get dependencies for a chain."""
        if chain_id not in self.nodes:
            return set()

        dependencies = self.nodes[chain_id].dependencies.copy()

        if recursive:
            visited = {chain_id}
            queue = list(dependencies)

            while queue:
                dep_id = queue.pop(0)
                if dep_id in visited or dep_id not in self.nodes:
                    continue

                visited.add(dep_id)
                indirect_deps = self.nodes[dep_id].dependencies
                for indirect_dep in indirect_deps:
                    if indirect_dep not in dependencies:
                        dependencies.add(indirect_dep)
                        queue.append(indirect_dep)

        return dependencies

    def get_dependents(self, chain_id: str, recursive: bool = False) -> Set[str]:
        """Get dependents for a chain."""
        if chain_id not in self.nodes:
            return set()

        dependents = self.nodes[chain_id].dependents.copy()

        if recursive:
            visited = {chain_id}
            queue = list(dependents)

            while queue:
                dep_id = queue.pop(0)
                if dep_id in visited or dep_id not in self.nodes:
                    continue

                visited.add(dep_id)
                indirect_deps = self.nodes[dep_id].dependents
                for indirect_dep in indirect_deps:
                    if indirect_dep not in dependents:
                        dependents.add(indirect_dep)
                        queue.append(indirect_dep)

        return dependents

    def detect_circular_dependencies(self) -> List[List[str]]:
        """Detect circular dependencies in the graph."""
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node_id: str, path: List[str]) -> bool:
            if node_id in rec_stack:
                # Found a cycle
                cycle_start = path.index(node_id)
                cycles.append(path[cycle_start:] + [node_id])
                return True

            if node_id in visited:
                return False

            visited.add(node_id)
            rec_stack.add(node_id)

            if node_id in self.nodes:
                for dep_id in self.nodes[node_id].dependencies:
                    if dfs(dep_id, path + [node_id]):
                        return True

            rec_stack.remove(node_id)
            return False

        for node_id in self.nodes:
            if node_id not in visited:
                dfs(node_id, [])

        return cycles


class ChainRegistry:
    """
    Central registry for managing chain definitions and relationships.

    This class provides the main interface for all chain operations including
    creation, retrieval, updating, and deletion of chain definitions.
    """

    def __init__(
        self,
        database_url: str,
        redis_url: Optional[str] = None,
        cache_ttl: int = 300  # 5 minutes
    ):
        """
        Initialize the chain registry.

        Args:
            database_url: Database connection URL
            redis_url: Redis connection URL for caching (optional)
            cache_ttl: Cache time-to-live in seconds
        """
        self.database_url = database_url
        self.redis_url = redis_url
        self.cache_ttl = cache_ttl

        # Database connections
        self.engine = create_async_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        # Cache setup
        self.cache: Optional[Redis] = None
        if redis_url:
            try:
                self.cache = Redis.from_url(redis_url, decode_responses=True)
                self.cache.ping()  # Test connection
                logger.info("Redis cache connected successfully")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis cache: {e}")
                self.cache = None

        # In-memory structures
        self.dependency_graph = DependencyGraph()
        self._chain_cache: Dict[str, ChainDefinition] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()

        # Event callbacks
        self._event_callbacks: Dict[str, List[callable]] = {
            'chain_created': [],
            'chain_updated': [],
            'chain_deleted': [],
            'dependency_added': [],
            'dependency_removed': []
        }

    async def initialize(self):
        """Initialize the registry and load existing chains."""
        async with self._lock:
            await self._load_existing_chains()
            await self._build_dependency_graph()
            logger.info(f"Chain registry initialized with {len(self._chain_cache)} chains")

    async def _load_existing_chains(self):
        """Load existing chains from the database."""
        try:
            async with self.SessionLocal() as session:
                # This would use actual SQLAlchemy models in implementation
                # For now, we'll simulate the database query
                chains = await self._fetch_chains_from_db(session)

                for chain_data in chains:
                    try:
                        chain_def = ChainDefinition(**chain_data)
                        self._chain_cache[chain_def.id] = chain_def
                        self._cache_timestamps[chain_def.id] = datetime.utcnow()
                    except ValidationError as e:
                        logger.error(f"Failed to load chain {chain_data.get('id', 'unknown')}: {e}")

        except Exception as e:
            logger.error(f"Failed to load existing chains: {e}")
            raise ChainRegistryError(f"Database initialization failed: {e}")

    async def _fetch_chains_from_db(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """Fetch chains from database (placeholder implementation)."""
        # In actual implementation, this would use SQLAlchemy models
        # and perform proper database queries
        return []

    async def _build_dependency_graph(self):
        """Build the dependency graph from loaded chains."""
        # Clear existing graph
        self.dependency_graph = DependencyGraph()

        # Add all chains to the graph
        for chain_def in self._chain_cache.values():
            self.dependency_graph.add_chain(chain_def)

        # Analyze dependencies based on service relationships
        await self._analyze_service_dependencies()

    async def _analyze_service_dependencies(self):
        """Analyze and build service-based dependencies."""
        service_to_chains: Dict[str, List[str]] = {}

        # Map services to chains
        for chain_id, chain_def in self._chain_cache.items():
            for service in chain_def.involved_services:
                if service not in service_to_chains:
                    service_to_chains[service] = []
                service_to_chains[service].append(chain_id)

        # Create dependencies for chains sharing services
        for service, chain_ids in service_to_chains.items():
            if len(chain_ids) > 1:
                # Create dependencies between chains using the same service
                for i, chain_id1 in enumerate(chain_ids):
                    for chain_id2 in chain_ids[i+1:]:
                        # Add bidirectional soft dependencies
                        self.dependency_graph.add_dependency(chain_id1, chain_id2)
                        self.dependency_graph.add_dependency(chain_id2, chain_id1)

    async def register_chain(self, chain_create: ChainDefinitionCreate) -> str:
        """
        Register a new chain definition.

        Args:
            chain_create: Chain creation data

        Returns:
            The assigned chain ID

        Raises:
            ChainValidationError: If validation fails
            ChainRegistryError: If registration fails
        """
        async with self._lock:
            # Generate chain ID based on category
            chain_id = await self._generate_chain_id(chain_create.category)

            # Create full chain definition
            chain_def = ChainDefinition(
                id=chain_id,
                **chain_create.model_dump(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            # Validate the chain
            validation_result = await self.validate_chain(chain_def)
            if not validation_result.valid:
                error_msg = "; ".join([error['message'] for error in validation_result.errors])
                raise ChainValidationError(f"Chain validation failed: {error_msg}")

            try:
                # Save to database
                await self._save_chain_to_db(chain_def)

                # Update in-memory cache
                self._chain_cache[chain_id] = chain_def
                self._cache_timestamps[chain_id] = datetime.utcnow()

                # Update dependency graph
                self.dependency_graph.add_chain(chain_def)
                await self._update_dependencies_for_chain(chain_def)

                # Clear related cache entries
                await self._invalidate_cache_patterns([f"chains:*", f"services:*"])

                # Trigger events
                await self._trigger_event('chain_created', chain_def)

                logger.info(f"Successfully registered chain {chain_id}")
                return chain_id

            except Exception as e:
                logger.error(f"Failed to register chain {chain_id}: {e}")
                raise ChainRegistryError(f"Failed to register chain: {e}")

    async def _generate_chain_id(self, category: ChainCategory) -> str:
        """Generate a unique chain ID for the given category."""
        category_prefix = {
            ChainCategory.DATA_FLOW: 'A',
            ChainCategory.SERVICE_COMMUNICATION: 'B',
            ChainCategory.USER_EXPERIENCE: 'C',
            ChainCategory.AI_ML_PROCESSING: 'D',
            ChainCategory.INFRASTRUCTURE: 'E'
        }

        prefix = category_prefix[category]

        # Find the highest existing number for this category
        existing_numbers = []
        for chain_id in self._chain_cache.keys():
            if chain_id.startswith(prefix):
                try:
                    number = int(chain_id[1:])
                    existing_numbers.append(number)
                except ValueError:
                    continue

        next_number = max(existing_numbers, default=0) + 1
        return f"{prefix}{next_number}"

    async def get_chain(self, chain_id: str) -> ChainDefinition:
        """
        Retrieve a chain definition by ID.

        Args:
            chain_id: Chain identifier

        Returns:
            Chain definition

        Raises:
            ChainNotFoundError: If chain is not found
        """
        # Check in-memory cache first
        if chain_id in self._chain_cache:
            cache_time = self._cache_timestamps.get(chain_id)
            if cache_time and (datetime.utcnow() - cache_time).seconds < self.cache_ttl:
                return self._chain_cache[chain_id]

        # Check Redis cache
        if self.cache:
            try:
                cached_data = self.cache.get(f"chain:{chain_id}")
                if cached_data:
                    chain_data = json.loads(cached_data)
                    chain_def = ChainDefinition(**chain_data)
                    self._chain_cache[chain_id] = chain_def
                    self._cache_timestamps[chain_id] = datetime.utcnow()
                    return chain_def
            except Exception as e:
                logger.warning(f"Failed to retrieve from Redis cache: {e}")

        # Load from database
        try:
            async with self.SessionLocal() as session:
                chain_data = await self._fetch_chain_from_db(session, chain_id)
                if not chain_data:
                    raise ChainNotFoundError(f"Chain {chain_id} not found")

                chain_def = ChainDefinition(**chain_data)

                # Update caches
                self._chain_cache[chain_id] = chain_def
                self._cache_timestamps[chain_id] = datetime.utcnow()

                if self.cache:
                    try:
                        self.cache.setex(
                            f"chain:{chain_id}",
                            self.cache_ttl,
                            chain_def.model_dump_json()
                        )
                    except Exception as e:
                        logger.warning(f"Failed to cache in Redis: {e}")

                return chain_def

        except ChainNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve chain {chain_id}: {e}")
            raise ChainRegistryError(f"Failed to retrieve chain: {e}")

    async def _fetch_chain_from_db(self, session: AsyncSession, chain_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single chain from database (placeholder implementation)."""
        # In actual implementation, this would use SQLAlchemy models
        return None

    async def update_chain(self, chain_id: str, updates: ChainDefinitionUpdate) -> bool:
        """
        Update an existing chain definition.

        Args:
            chain_id: Chain identifier
            updates: Update data

        Returns:
            True if successful

        Raises:
            ChainNotFoundError: If chain is not found
            ChainValidationError: If validation fails
        """
        async with self._lock:
            # Get existing chain
            existing_chain = await self.get_chain(chain_id)

            # Apply updates
            update_data = updates.model_dump(exclude_unset=True)
            update_data['updated_at'] = datetime.utcnow()
            update_data['version'] = existing_chain.version + 1

            # Create updated chain definition
            updated_data = existing_chain.model_dump()
            updated_data.update(update_data)

            try:
                updated_chain = ChainDefinition(**updated_data)
            except ValidationError as e:
                raise ChainValidationError(f"Update validation failed: {e}")

            # Validate the updated chain
            validation_result = await self.validate_chain(updated_chain)
            if not validation_result.valid:
                error_msg = "; ".join([error['message'] for error in validation_result.errors])
                raise ChainValidationError(f"Updated chain validation failed: {error_msg}")

            try:
                # Save to database
                await self._update_chain_in_db(updated_chain)

                # Update caches
                self._chain_cache[chain_id] = updated_chain
                self._cache_timestamps[chain_id] = datetime.utcnow()

                # Update dependency graph
                self.dependency_graph.add_chain(updated_chain)
                await self._update_dependencies_for_chain(updated_chain)

                # Clear related cache entries
                await self._invalidate_cache_patterns([f"chains:*", f"services:*"])

                # Trigger events
                await self._trigger_event('chain_updated', updated_chain, existing_chain)

                logger.info(f"Successfully updated chain {chain_id} to version {updated_chain.version}")
                return True

            except Exception as e:
                logger.error(f"Failed to update chain {chain_id}: {e}")
                raise ChainRegistryError(f"Failed to update chain: {e}")

    async def _save_chain_to_db(self, chain_def: ChainDefinition):
        """Save chain to database (placeholder implementation)."""
        # In actual implementation, this would use SQLAlchemy models
        pass

    async def _update_chain_in_db(self, chain_def: ChainDefinition):
        """Update chain in database (placeholder implementation)."""
        # In actual implementation, this would use SQLAlchemy models
        pass

    async def delete_chain(self, chain_id: str, force: bool = False) -> bool:
        """
        Delete a chain definition.

        Args:
            chain_id: Chain identifier
            force: Force deletion even if there are dependents

        Returns:
            True if successful

        Raises:
            ChainNotFoundError: If chain is not found
            ChainRegistryError: If deletion fails due to dependencies
        """
        async with self._lock:
            # Check if chain exists
            existing_chain = await self.get_chain(chain_id)

            # Check for dependents
            dependents = self.dependency_graph.get_dependents(chain_id)
            if dependents and not force:
                raise ChainRegistryError(
                    f"Cannot delete chain {chain_id}. "
                    f"It has dependents: {', '.join(dependents)}. "
                    f"Use force=True to override."
                )

            try:
                # Delete from database
                await self._delete_chain_from_db(chain_id)

                # Remove from caches
                self._chain_cache.pop(chain_id, None)
                self._cache_timestamps.pop(chain_id, None)

                # Remove from dependency graph
                if chain_id in self.dependency_graph.nodes:
                    del self.dependency_graph.nodes[chain_id]

                # Clear related cache entries
                await self._invalidate_cache_patterns([f"chains:*", f"services:*"])

                # Trigger events
                await self._trigger_event('chain_deleted', existing_chain)

                logger.info(f"Successfully deleted chain {chain_id}")
                return True

            except Exception as e:
                logger.error(f"Failed to delete chain {chain_id}: {e}")
                raise ChainRegistryError(f"Failed to delete chain: {e}")

    async def _delete_chain_from_db(self, chain_id: str):
        """Delete chain from database (placeholder implementation)."""
        # In actual implementation, this would use SQLAlchemy models
        pass

    async def list_chains(
        self,
        category: Optional[ChainCategory] = None,
        status: Optional[ChainStatus] = None,
        service: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> Tuple[List[ChainDefinition], int]:
        """
        List chains with optional filtering.

        Args:
            category: Filter by category
            status: Filter by status
            service: Filter by service involvement
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Tuple of (chains, total_count)
        """
        # Build cache key
        cache_key = f"chains:list:{category}:{status}:{service}:{limit}:{offset}"

        if self.cache:
            try:
                cached_result = self.cache.get(cache_key)
                if cached_result:
                    data = json.loads(cached_result)
                    chains = [ChainDefinition(**chain_data) for chain_data in data['chains']]
                    return chains, data['total']
            except Exception as e:
                logger.warning(f"Failed to retrieve from cache: {e}")

        # Filter chains
        filtered_chains = []
        for chain_def in self._chain_cache.values():
            if category and chain_def.category != category:
                continue
            if status and chain_def.status != status:
                continue
            if service and service not in chain_def.involved_services:
                continue
            filtered_chains.append(chain_def)

        # Sort by ID for consistent ordering
        filtered_chains.sort(key=lambda x: x.id)

        total_count = len(filtered_chains)

        # Apply pagination
        if limit:
            end_idx = offset + limit
            filtered_chains = filtered_chains[offset:end_idx]
        else:
            filtered_chains = filtered_chains[offset:]

        # Cache result
        if self.cache:
            try:
                cache_data = {
                    'chains': [chain.model_dump() for chain in filtered_chains],
                    'total': total_count
                }
                self.cache.setex(cache_key, self.cache_ttl, json.dumps(cache_data))
            except Exception as e:
                logger.warning(f"Failed to cache result: {e}")

        return filtered_chains, total_count

    async def find_chains_by_service(self, service_name: str) -> List[ChainDefinition]:
        """Find all chains involving a specific service."""
        chains = []
        for chain_def in self._chain_cache.values():
            if service_name in chain_def.involved_services:
                chains.append(chain_def)
        return sorted(chains, key=lambda x: x.id)

    async def get_dependency_graph(self, chain_id: str) -> Dict[str, Any]:
        """Get complete dependency graph for a chain."""
        if chain_id not in self.dependency_graph.nodes:
            raise ChainNotFoundError(f"Chain {chain_id} not found in dependency graph")

        dependencies = self.dependency_graph.get_dependencies(chain_id, recursive=True)
        dependents = self.dependency_graph.get_dependents(chain_id, recursive=True)

        return {
            'chain_id': chain_id,
            'dependencies': list(dependencies),
            'dependents': list(dependents),
            'dependency_count': len(dependencies),
            'dependent_count': len(dependents)
        }

    async def validate_chain(self, chain_def: ChainDefinition) -> ValidationResult:
        """
        Validate a chain definition for consistency and correctness.

        Args:
            chain_def: Chain definition to validate

        Returns:
            Validation result with errors and warnings
        """
        errors = []
        warnings = []
        suggestions = []

        try:
            # Basic model validation (handled by Pydantic)
            # Additional business logic validation

            # Check connectivity
            connectivity_issues = chain_def.validate_connectivity()
            for issue in connectivity_issues:
                warnings.append({
                    'field': 'connectivity',
                    'message': issue,
                    'severity': 'warning'
                })

            # Check for circular dependencies
            cycles = self.dependency_graph.detect_circular_dependencies()
            for cycle in cycles:
                if chain_def.id in cycle:
                    errors.append({
                        'field': 'dependencies',
                        'message': f"Circular dependency detected: {' -> '.join(cycle)}",
                        'severity': 'error'
                    })

            # Check service name validity
            for node in chain_def.nodes:
                if node.service_name and not await self._validate_service_name(node.service_name):
                    warnings.append({
                        'field': f'nodes.{node.id}.service_name',
                        'message': f"Service '{node.service_name}' not found in service registry",
                        'severity': 'warning'
                    })

            # Performance suggestions
            if len(chain_def.nodes) > 10:
                suggestions.append("Consider breaking this chain into smaller, more manageable chains")

            if len(chain_def.edges) == 0 and len(chain_def.nodes) > 1:
                suggestions.append("Consider adding edges to connect the nodes in this chain")

        except Exception as e:
            errors.append({
                'field': 'general',
                'message': f"Validation error: {str(e)}",
                'severity': 'error'
            })

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )

    async def _validate_service_name(self, service_name: str) -> bool:
        """Validate if a service name exists in the service registry."""
        # In actual implementation, this would check against the service registry
        known_services = {
            'api-gateway', 'data-bridge', 'ai-orchestration', 'deep-learning',
            'ai-provider', 'ml-processing', 'trading-engine', 'database-service',
            'user-service', 'strategy-optimization', 'performance-analytics'
        }
        return service_name in known_services

    async def _update_dependencies_for_chain(self, chain_def: ChainDefinition):
        """Update dependency relationships for a chain."""
        # Remove existing dependencies for this chain
        if chain_def.id in self.dependency_graph.nodes:
            node = self.dependency_graph.nodes[chain_def.id]
            node.dependencies.clear()
            node.dependents.clear()

        # Re-analyze dependencies
        await self._analyze_service_dependencies()

    async def _invalidate_cache_patterns(self, patterns: List[str]):
        """Invalidate cache entries matching patterns."""
        if not self.cache:
            return

        try:
            for pattern in patterns:
                keys = self.cache.keys(pattern)
                if keys:
                    self.cache.delete(*keys)
        except Exception as e:
            logger.warning(f"Failed to invalidate cache: {e}")

    async def _trigger_event(self, event_type: str, *args):
        """Trigger event callbacks."""
        callbacks = self._event_callbacks.get(event_type, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(*args)
                else:
                    callback(*args)
            except Exception as e:
                logger.error(f"Event callback failed for {event_type}: {e}")

    def register_event_callback(self, event_type: str, callback: callable):
        """Register an event callback."""
        if event_type not in self._event_callbacks:
            self._event_callbacks[event_type] = []
        self._event_callbacks[event_type].append(callback)

    async def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        total_chains = len(self._chain_cache)
        category_counts = {}
        status_counts = {}
        service_counts = {}

        for chain_def in self._chain_cache.values():
            # Category counts
            category = chain_def.category.value
            category_counts[category] = category_counts.get(category, 0) + 1

            # Status counts
            status = chain_def.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

            # Service involvement
            for service in chain_def.involved_services:
                service_counts[service] = service_counts.get(service, 0) + 1

        return {
            'total_chains': total_chains,
            'category_distribution': category_counts,
            'status_distribution': status_counts,
            'service_involvement': service_counts,
            'dependency_graph_size': len(self.dependency_graph.nodes),
            'cache_hit_ratio': self._calculate_cache_hit_ratio(),
            'last_updated': max(self._cache_timestamps.values()) if self._cache_timestamps else None
        }

    def _calculate_cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio (placeholder implementation)."""
        # In actual implementation, this would track cache hits/misses
        return 0.95

    async def cleanup(self):
        """Cleanup resources."""
        try:
            if self.cache:
                self.cache.close()
            await self.engine.dispose()
            logger.info("Chain registry cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Export the main class
__all__ = ['ChainRegistry', 'ChainRegistryError', 'ChainNotFoundError', 'ChainValidationError']