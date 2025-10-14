"""
Repository Pattern untuk data access abstraction
Provides clean separation between business logic and data persistence
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime


class ServiceRepository(ABC):
    """
    Abstract repository for service registry data

    Provides clean interface for service data persistence
    Can be implemented with different backends:
    - InMemoryServiceRepository (for testing/development)
    - PostgreSQLServiceRepository (for production)
    - RedisServiceRepository (for caching)
    """

    @abstractmethod
    async def save(self, service_id: str, service_data: Dict[str, Any]) -> None:
        """
        Save or update service data

        Args:
            service_id: Unique service identifier
            service_data: Service registration data
        """
        pass

    @abstractmethod
    async def find(self, service_id: str) -> Optional[Dict[str, Any]]:
        """
        Find service by ID

        Args:
            service_id: Service identifier

        Returns:
            Service data or None if not found
        """
        pass

    @abstractmethod
    async def find_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all registered services

        Returns:
            Dictionary mapping service IDs to service data
        """
        pass

    @abstractmethod
    async def delete(self, service_id: str) -> bool:
        """
        Delete service from registry

        Args:
            service_id: Service identifier

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def exists(self, service_id: str) -> bool:
        """
        Check if service exists

        Args:
            service_id: Service identifier

        Returns:
            True if service exists
        """
        pass

    @abstractmethod
    async def find_by_type(self, service_type: str) -> List[Dict[str, Any]]:
        """
        Find services by type

        Args:
            service_type: Service type (e.g., "api-gateway", "data-collector")

        Returns:
            List of matching services
        """
        pass

    @abstractmethod
    async def find_healthy(self) -> List[Dict[str, Any]]:
        """
        Find all healthy services

        Returns:
            List of healthy services
        """
        pass

    @abstractmethod
    async def update_last_seen(self, service_id: str) -> None:
        """
        Update service last_seen timestamp (heartbeat)

        Args:
            service_id: Service identifier
        """
        pass

    @abstractmethod
    async def count(self) -> int:
        """
        Count total registered services

        Returns:
            Number of services
        """
        pass


class InMemoryServiceRepository(ServiceRepository):
    """
    In-memory implementation of service repository

    Fast, simple, but data is lost on restart
    Good for development and testing
    """

    def __init__(self):
        self._storage: Dict[str, Dict[str, Any]] = {}

    async def save(self, service_id: str, service_data: Dict[str, Any]) -> None:
        """Save service to memory"""
        service_data["last_seen"] = datetime.now().isoformat()
        if service_id not in self._storage:
            service_data["registered_at"] = datetime.now().isoformat()
        self._storage[service_id] = service_data.copy()

    async def find(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Find service in memory"""
        return self._storage.get(service_id)

    async def find_all(self) -> Dict[str, Dict[str, Any]]:
        """Get all services from memory"""
        return self._storage.copy()

    async def delete(self, service_id: str) -> bool:
        """Delete service from memory"""
        if service_id in self._storage:
            del self._storage[service_id]
            return True
        return False

    async def exists(self, service_id: str) -> bool:
        """Check if service exists in memory"""
        return service_id in self._storage

    async def find_by_type(self, service_type: str) -> List[Dict[str, Any]]:
        """Find services by type"""
        return [
            service for service in self._storage.values()
            if service.get("metadata", {}).get("type") == service_type
        ]

    async def find_healthy(self) -> List[Dict[str, Any]]:
        """Find healthy services"""
        return [
            service for service in self._storage.values()
            if service.get("status") == "healthy" or service.get("status") == "active"
        ]

    async def update_last_seen(self, service_id: str) -> None:
        """Update last_seen timestamp"""
        if service_id in self._storage:
            self._storage[service_id]["last_seen"] = datetime.now().isoformat()

    async def count(self) -> int:
        """Count services"""
        return len(self._storage)


class PostgreSQLServiceRepository(ServiceRepository):
    """
    PostgreSQL implementation of service repository

    Persistent storage with transaction support
    Production-ready
    """

    def __init__(self, db_manager):
        """
        Initialize with database manager

        Args:
            db_manager: DatabaseManager instance
        """
        self.db_manager = db_manager

    async def save(self, service_id: str, service_data: Dict[str, Any]) -> None:
        """Save service to PostgreSQL"""
        # Check if exists
        exists = await self.exists(service_id)

        if exists:
            # Update
            query = """
                UPDATE service_registry
                SET host = $1, port = $2, protocol = $3, health_endpoint = $4,
                    version = $5, metadata = $6, status = $7, last_seen = NOW()
                WHERE service_name = $8
            """
            await self.db_manager.execute(
                query,
                service_data.get("host"),
                service_data.get("port"),
                service_data.get("protocol", "http"),
                service_data.get("health_endpoint", "/health"),
                service_data.get("version"),
                service_data.get("metadata", {}),
                service_data.get("status", "active"),
                service_id
            )
        else:
            # Insert
            query = """
                INSERT INTO service_registry
                (service_name, host, port, protocol, health_endpoint, version, metadata, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """
            await self.db_manager.execute(
                query,
                service_id,
                service_data.get("host"),
                service_data.get("port"),
                service_data.get("protocol", "http"),
                service_data.get("health_endpoint", "/health"),
                service_data.get("version"),
                service_data.get("metadata", {}),
                service_data.get("status", "active")
            )

    async def find(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Find service in PostgreSQL"""
        query = """
            SELECT service_name, host, port, protocol, health_endpoint, version,
                   metadata, status, registered_at, last_seen
            FROM service_registry
            WHERE service_name = $1
        """
        result = await self.db_manager.fetch_one(query, service_id)

        if result:
            return dict(result)
        return None

    async def find_all(self) -> Dict[str, Dict[str, Any]]:
        """Get all services from PostgreSQL"""
        query = """
            SELECT service_name, host, port, protocol, health_endpoint, version,
                   metadata, status, registered_at, last_seen
            FROM service_registry
            ORDER BY registered_at DESC
        """
        results = await self.db_manager.fetch_all(query)

        services = {}
        for row in results:
            service_data = dict(row)
            service_name = service_data.pop("service_name")
            services[service_name] = service_data

        return services

    async def delete(self, service_id: str) -> bool:
        """Delete service from PostgreSQL"""
        query = "DELETE FROM service_registry WHERE service_name = $1"
        result = await self.db_manager.execute(query, service_id)
        return result > 0

    async def exists(self, service_id: str) -> bool:
        """Check if service exists in PostgreSQL"""
        query = "SELECT 1 FROM service_registry WHERE service_name = $1"
        result = await self.db_manager.fetch_one(query, service_id)
        return result is not None

    async def find_by_type(self, service_type: str) -> List[Dict[str, Any]]:
        """Find services by type"""
        query = """
            SELECT service_name, host, port, protocol, health_endpoint, version,
                   metadata, status, registered_at, last_seen
            FROM service_registry
            WHERE metadata->>'type' = $1
            ORDER BY registered_at DESC
        """
        results = await self.db_manager.fetch_all(query, service_type)
        return [dict(row) for row in results]

    async def find_healthy(self) -> List[Dict[str, Any]]:
        """Find healthy services"""
        query = """
            SELECT service_name, host, port, protocol, health_endpoint, version,
                   metadata, status, registered_at, last_seen
            FROM service_registry
            WHERE status IN ('healthy', 'active')
            ORDER BY last_seen DESC
        """
        results = await self.db_manager.fetch_all(query)
        return [dict(row) for row in results]

    async def update_last_seen(self, service_id: str) -> None:
        """Update last_seen timestamp"""
        query = "UPDATE service_registry SET last_seen = NOW() WHERE service_name = $1"
        await self.db_manager.execute(query, service_id)

    async def count(self) -> int:
        """Count services"""
        query = "SELECT COUNT(*) as count FROM service_registry"
        result = await self.db_manager.fetch_one(query)
        return result["count"] if result else 0


# Convenience function for creating repositories
def create_service_repository(backend: str = "memory", **kwargs) -> ServiceRepository:
    """
    Factory function for creating service repositories

    Args:
        backend: Repository backend ("memory" or "postgresql")
        **kwargs: Backend-specific arguments

    Returns:
        ServiceRepository instance

    Examples:
        # In-memory (development)
        repo = create_service_repository("memory")

        # PostgreSQL (production)
        repo = create_service_repository("postgresql", db_manager=db_manager)
    """
    if backend == "memory":
        return InMemoryServiceRepository()
    elif backend == "postgresql":
        if "db_manager" not in kwargs:
            raise ValueError("PostgreSQL repository requires 'db_manager' argument")
        return PostgreSQLServiceRepository(kwargs["db_manager"])
    else:
        raise ValueError(f"Unknown repository backend: {backend}")
