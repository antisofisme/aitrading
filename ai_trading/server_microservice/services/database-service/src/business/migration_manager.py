"""
Migration Manager - Enterprise database schema migration system
Handles schema versioning, migration execution, and rollback for all database types
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

# Infrastructure integration
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))
from shared.infrastructure.core.logger_core import get_logger
from shared.infrastructure.core.config_core import get_config
from shared.infrastructure.core.error_core import get_error_handler


class MigrationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class Migration:
    """Migration metadata"""
    id: str
    version: str
    description: str
    database_type: str
    up_sql: str
    down_sql: str
    created_at: datetime
    executed_at: Optional[datetime] = None
    status: MigrationStatus = MigrationStatus.PENDING
    execution_time_ms: Optional[float] = None
    error_message: Optional[str] = None


class MigrationManager:
    """Centralized migration management for all database types"""
    
    def __init__(self, database_manager: Optional[Any] = None):
        self.logger = get_logger("database-service", "migration-manager")
        self.config = get_config("database-service")
        self.error_handler = get_error_handler("database-service")
        self.database_manager = database_manager
        
        # Migration configuration
        self.migrations_dir = Path("migrations")
        self.migration_history_file = self.migrations_dir / "migration_history.json"
        self.schema_versions_file = self.migrations_dir / "schema_versions.json"
        
        # In-memory migration state
        self._migrations_cache = {}
        self._schema_versions = {}
        
        # Ensure migrations directory exists
        self.migrations_dir.mkdir(exist_ok=True)
        
        self.logger.info("MigrationManager initialized")
    
    async def initialize(self):
        """Initialize migration system"""
        try:
            self.logger.info("Initializing migration system")
            
            # Load existing migration history
            await self._load_migration_history()
            
            # Load schema versions
            await self._load_schema_versions()
            
            # Discover available migrations
            await self._discover_migrations()
            
            self.logger.info(f"Migration system initialized - {len(self._migrations_cache)} migrations found")
            
        except Exception as e:
            self.logger.error(f"Migration system initialization failed: {e}")
            raise
    
    async def get_pending_migrations(self, database_type: Optional[str] = None) -> List[Migration]:
        """Get list of pending migrations"""
        try:
            pending_migrations = []
            
            for migration_id, migration in self._migrations_cache.items():
                if migration.status == MigrationStatus.PENDING:
                    if not database_type or migration.database_type == database_type:
                        pending_migrations.append(migration)
            
            # Sort by version
            pending_migrations.sort(key=lambda m: m.version)
            
            self.logger.info(f"Found {len(pending_migrations)} pending migrations for {database_type or 'all databases'}")
            
            return pending_migrations
            
        except Exception as e:
            self.logger.error(f"Failed to get pending migrations: {e}")
            raise
    
    async def execute_migration(self, migration: Migration) -> bool:
        """Execute a single migration"""
        try:
            self.logger.info(f"Executing migration {migration.id} for {migration.database_type}")
            
            # Update migration status
            migration.status = MigrationStatus.RUNNING
            await self._save_migration_history()
            
            start_time = asyncio.get_event_loop().time()
            
            # Execute migration based on database type
            success = await self._execute_database_migration(migration)
            
            execution_time_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            migration.execution_time_ms = execution_time_ms
            migration.executed_at = datetime.utcnow()
            
            if success:
                migration.status = MigrationStatus.COMPLETED
                await self._update_schema_version(migration.database_type, migration.version)
                self.logger.info(f"Migration {migration.id} completed successfully in {execution_time_ms:.2f}ms")
            else:
                migration.status = MigrationStatus.FAILED
                migration.error_message = "Migration execution failed"
                self.logger.error(f"Migration {migration.id} failed")
            
            # Update migration cache and save history
            self._migrations_cache[migration.id] = migration
            await self._save_migration_history()
            
            return success
            
        except Exception as e:
            migration.status = MigrationStatus.FAILED
            migration.error_message = str(e)
            migration.executed_at = datetime.utcnow()
            
            self._migrations_cache[migration.id] = migration
            await self._save_migration_history()
            
            self.logger.error(f"Migration {migration.id} execution failed: {e}")
            return False
    
    async def execute_all_pending_migrations(self, database_type: Optional[str] = None) -> Dict[str, bool]:
        """Execute all pending migrations for specified database type"""
        try:
            self.logger.info(f"Executing all pending migrations for {database_type or 'all databases'}")
            
            pending_migrations = await self.get_pending_migrations(database_type)
            
            results = {}
            
            for migration in pending_migrations:
                success = await self.execute_migration(migration)
                results[migration.id] = success
                
                if not success:
                    self.logger.error(f"Migration {migration.id} failed, stopping execution")
                    break
            
            successful_count = sum(1 for success in results.values() if success)
            
            self.logger.info(f"Migration execution completed - {successful_count}/{len(pending_migrations)} successful")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to execute pending migrations: {e}")
            raise
    
    async def rollback_migration(self, migration: Migration) -> bool:
        """Rollback a specific migration"""
        try:
            self.logger.info(f"Rolling back migration {migration.id}")
            
            if migration.status != MigrationStatus.COMPLETED:
                raise ValueError(f"Cannot rollback migration {migration.id} - not in completed state")
            
            # Execute rollback SQL
            success = await self._execute_database_rollback(migration)
            
            if success:
                migration.status = MigrationStatus.ROLLED_BACK
                migration.executed_at = datetime.utcnow()
                
                # Update schema version (find previous version)
                await self._rollback_schema_version(migration.database_type, migration.version)
                
                self.logger.info(f"Migration {migration.id} rolled back successfully")
            else:
                self.logger.error(f"Migration {migration.id} rollback failed")
            
            # Update migration cache and save history
            self._migrations_cache[migration.id] = migration
            await self._save_migration_history()
            
            return success
            
        except Exception as e:
            self.logger.error(f"Migration rollback failed: {e}")
            return False
    
    async def create_migration(self, 
                             version: str,
                             description: str,
                             database_type: str,
                             up_sql: str,
                             down_sql: str) -> Migration:
        """Create a new migration"""
        try:
            migration_id = f"{database_type}_{version}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            migration = Migration(
                id=migration_id,
                version=version,
                description=description,
                database_type=database_type,
                up_sql=up_sql,
                down_sql=down_sql,
                created_at=datetime.utcnow()
            )
            
            # Save migration to file
            migration_file = self.migrations_dir / f"{migration_id}.yaml"
            await self._save_migration_to_file(migration, migration_file)
            
            # Add to cache
            self._migrations_cache[migration_id] = migration
            
            # Save history
            await self._save_migration_history()
            
            self.logger.info(f"Migration {migration_id} created successfully")
            
            return migration
            
        except Exception as e:
            self.logger.error(f"Failed to create migration: {e}")
            raise
    
    async def get_migration_status(self, migration_id: str) -> Optional[Migration]:
        """Get status of specific migration"""
        return self._migrations_cache.get(migration_id)
    
    async def get_schema_version(self, database_type: str) -> Optional[str]:
        """Get current schema version for database type"""
        return self._schema_versions.get(database_type)
    
    async def get_migration_history(self, database_type: Optional[str] = None) -> List[Migration]:
        """Get migration history"""
        migrations = list(self._migrations_cache.values())
        
        if database_type:
            migrations = [m for m in migrations if m.database_type == database_type]
        
        # Sort by execution date
        migrations.sort(key=lambda m: m.executed_at or datetime.min)
        
        return migrations
    
    # ===== PRIVATE METHODS =====
    
    async def _execute_database_migration(self, migration: Migration) -> bool:
        """Execute migration SQL for specific database type"""
        try:
            if not self.database_manager:
                # Simulate execution in test environment
                await asyncio.sleep(0.1)
                return True
            
            if migration.database_type == "clickhouse":
                return await self._execute_clickhouse_migration(migration)
            elif migration.database_type == "postgresql":
                return await self._execute_postgresql_migration(migration)
            elif migration.database_type == "arangodb":
                return await self._execute_arangodb_migration(migration)
            else:
                self.logger.warning(f"Unsupported database type for migration: {migration.database_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Database migration execution failed: {e}")
            return False
    
    async def _execute_database_rollback(self, migration: Migration) -> bool:
        """Execute migration rollback SQL"""
        try:
            if not self.database_manager:
                # Simulate rollback in test environment
                await asyncio.sleep(0.1)
                return True
            
            if migration.database_type == "clickhouse":
                return await self._rollback_clickhouse_migration(migration)
            elif migration.database_type == "postgresql":
                return await self._rollback_postgresql_migration(migration)
            elif migration.database_type == "arangodb":
                return await self._rollback_arangodb_migration(migration)
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Database migration rollback failed: {e}")
            return False
    
    async def _execute_clickhouse_migration(self, migration: Migration) -> bool:
        """Execute ClickHouse migration"""
        try:
            # Split SQL by semicolons and execute each statement
            statements = [stmt.strip() for stmt in migration.up_sql.split(';') if stmt.strip()]
            
            for statement in statements:
                await self.database_manager.execute_clickhouse_query(statement, "trading_data")
            
            return True
            
        except Exception as e:
            self.logger.error(f"ClickHouse migration failed: {e}")
            return False
    
    async def _rollback_clickhouse_migration(self, migration: Migration) -> bool:
        """Rollback ClickHouse migration"""
        try:
            statements = [stmt.strip() for stmt in migration.down_sql.split(';') if stmt.strip()]
            
            for statement in statements:
                await self.database_manager.execute_clickhouse_query(statement, "trading_data")
            
            return True
            
        except Exception as e:
            self.logger.error(f"ClickHouse migration rollback failed: {e}")
            return False
    
    async def _execute_postgresql_migration(self, migration: Migration) -> bool:
        """Execute PostgreSQL migration"""
        try:
            statements = [stmt.strip() for stmt in migration.up_sql.split(';') if stmt.strip()]
            
            for statement in statements:
                await self.database_manager.execute_postgresql_command(statement, {}, "ai_trading_auth")
            
            return True
            
        except Exception as e:
            self.logger.error(f"PostgreSQL migration failed: {e}")
            return False
    
    async def _rollback_postgresql_migration(self, migration: Migration) -> bool:
        """Rollback PostgreSQL migration"""
        try:
            statements = [stmt.strip() for stmt in migration.down_sql.split(';') if stmt.strip()]
            
            for statement in statements:
                await self.database_manager.execute_postgresql_command(statement, {}, "ai_trading_auth")
            
            return True
            
        except Exception as e:
            self.logger.error(f"PostgreSQL migration rollback failed: {e}")
            return False
    
    async def _execute_arangodb_migration(self, migration: Migration) -> bool:
        """Execute ArangoDB migration"""
        try:
            # ArangoDB migrations would typically use AQL or HTTP API calls
            await self.database_manager.execute_arangodb_query(migration.up_sql, "trading_system")
            
            return True
            
        except Exception as e:
            self.logger.error(f"ArangoDB migration failed: {e}")
            return False
    
    async def _rollback_arangodb_migration(self, migration: Migration) -> bool:
        """Rollback ArangoDB migration"""
        try:
            await self.database_manager.execute_arangodb_query(migration.down_sql, "trading_system")
            
            return True
            
        except Exception as e:
            self.logger.error(f"ArangoDB migration rollback failed: {e}")
            return False
    
    async def _load_migration_history(self):
        """Load migration history from file"""
        try:
            if self.migration_history_file.exists():
                with open(self.migration_history_file, 'r') as f:
                    history_data = json.load(f)
                
                for migration_data in history_data:
                    migration = Migration(
                        id=migration_data['id'],
                        version=migration_data['version'],
                        description=migration_data['description'],
                        database_type=migration_data['database_type'],
                        up_sql=migration_data['up_sql'],
                        down_sql=migration_data['down_sql'],
                        created_at=datetime.fromisoformat(migration_data['created_at']),
                        executed_at=datetime.fromisoformat(migration_data['executed_at']) if migration_data.get('executed_at') else None,
                        status=MigrationStatus(migration_data['status']),
                        execution_time_ms=migration_data.get('execution_time_ms'),
                        error_message=migration_data.get('error_message')
                    )
                    
                    self._migrations_cache[migration.id] = migration
                
                self.logger.info(f"Loaded {len(self._migrations_cache)} migrations from history")
            
        except Exception as e:
            self.logger.error(f"Failed to load migration history: {e}")
    
    async def _save_migration_history(self):
        """Save migration history to file"""
        try:
            history_data = []
            
            for migration in self._migrations_cache.values():
                migration_dict = asdict(migration)
                # Convert datetime objects to ISO format
                migration_dict['created_at'] = migration.created_at.isoformat()
                if migration.executed_at:
                    migration_dict['executed_at'] = migration.executed_at.isoformat()
                migration_dict['status'] = migration.status.value
                
                history_data.append(migration_dict)
            
            with open(self.migration_history_file, 'w') as f:
                json.dump(history_data, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Failed to save migration history: {e}")
    
    async def _load_schema_versions(self):
        """Load schema versions from file"""
        try:
            if self.schema_versions_file.exists():
                with open(self.schema_versions_file, 'r') as f:
                    self._schema_versions = json.load(f)
                
                self.logger.info(f"Loaded schema versions: {self._schema_versions}")
            
        except Exception as e:
            self.logger.error(f"Failed to load schema versions: {e}")
    
    async def _save_schema_versions(self):
        """Save schema versions to file"""
        try:
            with open(self.schema_versions_file, 'w') as f:
                json.dump(self._schema_versions, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Failed to save schema versions: {e}")
    
    async def _update_schema_version(self, database_type: str, version: str):
        """Update schema version for database type"""
        self._schema_versions[database_type] = version
        await self._save_schema_versions()
    
    async def _rollback_schema_version(self, database_type: str, current_version: str):
        """Rollback schema version to previous version"""
        # Find previous version from migration history
        migrations = [m for m in self._migrations_cache.values() 
                     if m.database_type == database_type and m.status == MigrationStatus.COMPLETED]
        
        migrations.sort(key=lambda m: m.version)
        
        previous_version = None
        for i, migration in enumerate(migrations):
            if migration.version == current_version and i > 0:
                previous_version = migrations[i-1].version
                break
        
        if previous_version:
            self._schema_versions[database_type] = previous_version
        else:
            # Remove version if no previous version exists
            self._schema_versions.pop(database_type, None)
        
        await self._save_schema_versions()
    
    async def _discover_migrations(self):
        """Discover migration files in migrations directory"""
        try:
            migration_files = list(self.migrations_dir.glob("*.yaml"))
            
            for migration_file in migration_files:
                if migration_file != self.migration_history_file and migration_file != self.schema_versions_file:
                    await self._load_migration_from_file(migration_file)
            
            self.logger.info(f"Discovered {len(migration_files)} migration files")
            
        except Exception as e:
            self.logger.error(f"Failed to discover migrations: {e}")
    
    async def _load_migration_from_file(self, migration_file: Path):
        """Load migration from YAML file"""
        try:
            import yaml
            
            with open(migration_file, 'r') as f:
                migration_data = yaml.safe_load(f)
            
            migration = Migration(
                id=migration_data['id'],
                version=migration_data['version'],
                description=migration_data['description'],
                database_type=migration_data['database_type'],
                up_sql=migration_data['up_sql'],
                down_sql=migration_data['down_sql'],
                created_at=datetime.fromisoformat(migration_data['created_at'])
            )
            
            # Only add if not already in cache (history takes precedence)
            if migration.id not in self._migrations_cache:
                self._migrations_cache[migration.id] = migration
            
        except Exception as e:
            self.logger.error(f"Failed to load migration from {migration_file}: {e}")
    
    async def _save_migration_to_file(self, migration: Migration, migration_file: Path):
        """Save migration to YAML file"""
        try:
            import yaml
            
            migration_data = {
                'id': migration.id,
                'version': migration.version,
                'description': migration.description,
                'database_type': migration.database_type,
                'up_sql': migration.up_sql,
                'down_sql': migration.down_sql,
                'created_at': migration.created_at.isoformat()
            }
            
            with open(migration_file, 'w') as f:
                yaml.dump(migration_data, f, default_flow_style=False)
            
        except Exception as e:
            self.logger.error(f"Failed to save migration to {migration_file}: {e}")
            raise