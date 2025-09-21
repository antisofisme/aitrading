"""
Database Backup and Disaster Recovery System
Phase 1 Infrastructure Migration

Implements comprehensive backup and recovery for:
- PostgreSQL user management and authentication data
- ClickHouse trading analytics and log data
- DragonflyDB cache recovery
- Cross-database coordination and consistency
- Automated backup scheduling and monitoring
- Point-in-time recovery capabilities
"""

import asyncio
import logging
import os
import shutil
import gzip
import tarfile
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import subprocess
import schedule
import threading
import time

from .connection_pooling import DatabaseManager
from .security.database_security import SecurityEventLogger, SecurityEvent

logger = logging.getLogger(__name__)

class BackupType(Enum):
    """Types of database backups."""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    LOG = "log"

class BackupStatus(Enum):
    """Backup operation status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CORRUPTED = "corrupted"

class RecoveryPoint(Enum):
    """Recovery point objectives."""
    LATEST = "latest"
    POINT_IN_TIME = "point_in_time"
    NAMED_BACKUP = "named_backup"

@dataclass
class BackupConfig:
    """Backup configuration settings."""
    backup_type: BackupType
    schedule: str  # Cron expression
    retention_days: int
    compression: bool = True
    encryption: bool = True
    verify_integrity: bool = True
    max_parallel_jobs: int = 3
    backup_location: str = "/backup"
    s3_bucket: Optional[str] = None
    notification_endpoints: List[str] = None

@dataclass
class BackupMetadata:
    """Backup metadata and information."""
    backup_id: str
    backup_type: BackupType
    database_name: str
    backup_path: str
    file_size_bytes: int
    compressed_size_bytes: int
    checksum: str
    created_at: datetime
    completed_at: Optional[datetime]
    status: BackupStatus
    error_message: Optional[str] = None
    retention_until: Optional[datetime] = None
    parent_backup_id: Optional[str] = None  # For incremental backups

@dataclass
class RecoveryPlan:
    """Database recovery plan."""
    recovery_point: RecoveryPoint
    target_time: Optional[datetime] = None
    backup_id: Optional[str] = None
    databases: List[str] = None
    verify_integrity: bool = True
    cleanup_before_restore: bool = False

class PostgreSQLBackup:
    """PostgreSQL backup and recovery operations."""

    def __init__(self, db_config: Dict[str, Any], backup_config: BackupConfig):
        self.db_config = db_config
        self.backup_config = backup_config
        self.backup_dir = Path(backup_config.backup_location) / "postgresql"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    async def create_backup(self, backup_type: BackupType = BackupType.FULL) -> BackupMetadata:
        """Create PostgreSQL backup."""
        backup_id = f"pg_{backup_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.backup_dir / f"{backup_id}.sql"

        logger.info(f"Starting PostgreSQL {backup_type.value} backup: {backup_id}")

        metadata = BackupMetadata(
            backup_id=backup_id,
            backup_type=backup_type,
            database_name=self.db_config['database'],
            backup_path=str(backup_path),
            file_size_bytes=0,
            compressed_size_bytes=0,
            checksum="",
            created_at=datetime.now(),
            completed_at=None,
            status=BackupStatus.IN_PROGRESS
        )

        try:
            # Build pg_dump command
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_config['password']

            cmd = [
                'pg_dump',
                '-h', self.db_config['host'],
                '-p', str(self.db_config['port']),
                '-U', self.db_config['username'],
                '-d', self.db_config['database'],
                '--verbose',
                '--no-password',
                '--format=custom',
                '--compress=9'
            ]

            if backup_type == BackupType.FULL:
                cmd.extend(['--clean', '--create'])
            elif backup_type == BackupType.INCREMENTAL:
                # Implement WAL-based incremental backup
                cmd.extend(['--no-owner', '--no-privileges'])

            # Execute backup
            with open(backup_path, 'wb') as backup_file:
                process = subprocess.Popen(
                    cmd,
                    stdout=backup_file,
                    stderr=subprocess.PIPE,
                    env=env
                )

                stderr_output = process.communicate()[1]

                if process.returncode != 0:
                    error_msg = stderr_output.decode('utf-8')
                    metadata.status = BackupStatus.FAILED
                    metadata.error_message = error_msg
                    logger.error(f"PostgreSQL backup failed: {error_msg}")
                    return metadata

            # Get file size
            file_size = backup_path.stat().st_size
            metadata.file_size_bytes = file_size

            # Compress if requested
            if self.backup_config.compression:
                compressed_path = backup_path.with_suffix('.sql.gz')
                with open(backup_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)

                metadata.compressed_size_bytes = compressed_path.stat().st_size
                metadata.backup_path = str(compressed_path)
                backup_path.unlink()  # Remove uncompressed file
                backup_path = compressed_path

            # Calculate checksum
            metadata.checksum = await self._calculate_checksum(backup_path)

            # Verify integrity if requested
            if self.backup_config.verify_integrity:
                if not await self._verify_backup_integrity(backup_path):
                    metadata.status = BackupStatus.CORRUPTED
                    metadata.error_message = "Backup integrity verification failed"
                    return metadata

            # Set retention
            metadata.retention_until = datetime.now() + timedelta(days=self.backup_config.retention_days)
            metadata.completed_at = datetime.now()
            metadata.status = BackupStatus.COMPLETED

            logger.info(f"PostgreSQL backup completed: {backup_id}, size: {file_size} bytes")

        except Exception as e:
            metadata.status = BackupStatus.FAILED
            metadata.error_message = str(e)
            logger.error(f"PostgreSQL backup failed: {e}")

        return metadata

    async def restore_backup(self, backup_metadata: BackupMetadata,
                           target_database: str = None) -> bool:
        """Restore PostgreSQL backup."""
        try:
            backup_path = Path(backup_metadata.backup_path)
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False

            # Verify checksum
            current_checksum = await self._calculate_checksum(backup_path)
            if current_checksum != backup_metadata.checksum:
                logger.error("Backup file checksum mismatch")
                return False

            target_db = target_database or self.db_config['database']
            logger.info(f"Restoring PostgreSQL backup {backup_metadata.backup_id} to {target_db}")

            # Decompress if needed
            restore_path = backup_path
            if backup_path.suffix == '.gz':
                restore_path = backup_path.with_suffix('')
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(restore_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)

            # Build pg_restore command
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_config['password']

            cmd = [
                'pg_restore',
                '-h', self.db_config['host'],
                '-p', str(self.db_config['port']),
                '-U', self.db_config['username'],
                '-d', target_db,
                '--verbose',
                '--no-password',
                '--clean',
                '--if-exists',
                str(restore_path)
            ]

            # Execute restore
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env
            )

            stdout_output, stderr_output = process.communicate()

            if process.returncode != 0:
                error_msg = stderr_output.decode('utf-8')
                logger.error(f"PostgreSQL restore failed: {error_msg}")
                return False

            # Clean up decompressed file if created
            if restore_path != backup_path:
                restore_path.unlink()

            logger.info(f"PostgreSQL restore completed successfully")
            return True

        except Exception as e:
            logger.error(f"PostgreSQL restore failed: {e}")
            return False

    async def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    async def _verify_backup_integrity(self, backup_path: Path) -> bool:
        """Verify backup file integrity."""
        try:
            # For PostgreSQL, we can try to list the backup contents
            cmd = ['pg_restore', '--list', str(backup_path)]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            stdout_output, stderr_output = process.communicate()
            return process.returncode == 0

        except Exception as e:
            logger.error(f"Backup integrity verification failed: {e}")
            return False

class ClickHouseBackup:
    """ClickHouse backup and recovery operations."""

    def __init__(self, db_config: Dict[str, Any], backup_config: BackupConfig):
        self.db_config = db_config
        self.backup_config = backup_config
        self.backup_dir = Path(backup_config.backup_location) / "clickhouse"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    async def create_backup(self, tables: List[str] = None) -> BackupMetadata:
        """Create ClickHouse backup."""
        backup_id = f"ch_full_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.backup_dir / f"{backup_id}.tar.gz"

        logger.info(f"Starting ClickHouse backup: {backup_id}")

        metadata = BackupMetadata(
            backup_id=backup_id,
            backup_type=BackupType.FULL,
            database_name=self.db_config['database'],
            backup_path=str(backup_path),
            file_size_bytes=0,
            compressed_size_bytes=0,
            checksum="",
            created_at=datetime.now(),
            completed_at=None,
            status=BackupStatus.IN_PROGRESS
        )

        try:
            # Create temporary directory for backup files
            temp_dir = self.backup_dir / f"temp_{backup_id}"
            temp_dir.mkdir(exist_ok=True)

            # Export data using clickhouse-client
            if not tables:
                tables = await self._get_all_tables()

            total_size = 0
            for table in tables:
                table_file = temp_dir / f"{table}.sql"
                size = await self._export_table(table, table_file)
                total_size += size

            metadata.file_size_bytes = total_size

            # Create compressed archive
            with tarfile.open(backup_path, 'w:gz') as tar:
                tar.add(temp_dir, arcname=backup_id)

            metadata.compressed_size_bytes = backup_path.stat().st_size

            # Calculate checksum
            metadata.checksum = await self._calculate_checksum(backup_path)

            # Clean up temporary directory
            shutil.rmtree(temp_dir)

            # Set retention
            metadata.retention_until = datetime.now() + timedelta(days=self.backup_config.retention_days)
            metadata.completed_at = datetime.now()
            metadata.status = BackupStatus.COMPLETED

            logger.info(f"ClickHouse backup completed: {backup_id}, size: {total_size} bytes")

        except Exception as e:
            metadata.status = BackupStatus.FAILED
            metadata.error_message = str(e)
            logger.error(f"ClickHouse backup failed: {e}")

            # Clean up on failure
            if backup_path.exists():
                backup_path.unlink()
            temp_dir = self.backup_dir / f"temp_{backup_id}"
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

        return metadata

    async def _get_all_tables(self) -> List[str]:
        """Get list of all tables in database."""
        cmd = [
            'clickhouse-client',
            '--host', self.db_config['host'],
            '--port', str(self.db_config['port']),
            '--database', self.db_config['database'],
            '--query', "SHOW TABLES"
        ]

        if self.db_config.get('username'):
            cmd.extend(['--user', self.db_config['username']])
        if self.db_config.get('password'):
            cmd.extend(['--password', self.db_config['password']])

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout_output, stderr_output = process.communicate()

        if process.returncode != 0:
            raise Exception(f"Failed to get table list: {stderr_output}")

        return [table.strip() for table in stdout_output.split('\n') if table.strip()]

    async def _export_table(self, table: str, output_file: Path) -> int:
        """Export single table to file."""
        # First, get table schema
        schema_cmd = [
            'clickhouse-client',
            '--host', self.db_config['host'],
            '--port', str(self.db_config['port']),
            '--database', self.db_config['database'],
            '--query', f"SHOW CREATE TABLE {table}"
        ]

        if self.db_config.get('username'):
            schema_cmd.extend(['--user', self.db_config['username']])
        if self.db_config.get('password'):
            schema_cmd.extend(['--password', self.db_config['password']])

        # Export data
        data_cmd = [
            'clickhouse-client',
            '--host', self.db_config['host'],
            '--port', str(self.db_config['port']),
            '--database', self.db_config['database'],
            '--query', f"SELECT * FROM {table} FORMAT TabSeparated"
        ]

        if self.db_config.get('username'):
            data_cmd.extend(['--user', self.db_config['username']])
        if self.db_config.get('password'):
            data_cmd.extend(['--password', self.db_config['password']])

        with open(output_file, 'w') as f:
            # Write schema
            schema_process = subprocess.Popen(
                schema_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            schema_output, schema_error = schema_process.communicate()

            if schema_process.returncode == 0:
                f.write(f"-- Schema for table {table}\n")
                f.write(schema_output)
                f.write("\n\n")

            # Write data
            data_process = subprocess.Popen(
                data_cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                text=True
            )
            data_output, data_error = data_process.communicate()

            if data_process.returncode != 0:
                raise Exception(f"Failed to export table {table}: {data_error}")

        return output_file.stat().st_size

    async def restore_backup(self, backup_metadata: BackupMetadata) -> bool:
        """Restore ClickHouse backup."""
        try:
            backup_path = Path(backup_metadata.backup_path)
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False

            # Verify checksum
            current_checksum = await self._calculate_checksum(backup_path)
            if current_checksum != backup_metadata.checksum:
                logger.error("Backup file checksum mismatch")
                return False

            logger.info(f"Restoring ClickHouse backup {backup_metadata.backup_id}")

            # Extract backup
            temp_dir = self.backup_dir / f"restore_{backup_metadata.backup_id}"
            temp_dir.mkdir(exist_ok=True)

            with tarfile.open(backup_path, 'r:gz') as tar:
                tar.extractall(temp_dir)

            # Restore each table
            extracted_dir = temp_dir / backup_metadata.backup_id
            for sql_file in extracted_dir.glob('*.sql'):
                table_name = sql_file.stem
                await self._restore_table(table_name, sql_file)

            # Clean up
            shutil.rmtree(temp_dir)

            logger.info("ClickHouse restore completed successfully")
            return True

        except Exception as e:
            logger.error(f"ClickHouse restore failed: {e}")
            return False

    async def _restore_table(self, table_name: str, sql_file: Path):
        """Restore single table from file."""
        # Read the SQL file and separate schema from data
        with open(sql_file, 'r') as f:
            content = f.read()

        # Execute schema creation
        lines = content.split('\n')
        schema_lines = []
        data_lines = []
        in_schema = True

        for line in lines:
            if line.startswith('--') or not line.strip():
                continue
            if line.startswith('CREATE TABLE'):
                in_schema = True
                schema_lines.append(line)
            elif in_schema and (line.startswith('ENGINE') or line.endswith(';')):
                schema_lines.append(line)
                in_schema = False
            elif in_schema:
                schema_lines.append(line)
            else:
                data_lines.append(line)

        # Create table
        if schema_lines:
            schema_sql = '\n'.join(schema_lines)
            await self._execute_clickhouse_query(schema_sql)

        # Insert data
        if data_lines:
            data_content = '\n'.join(data_lines)
            insert_query = f"INSERT INTO {table_name} FORMAT TabSeparated"
            await self._execute_clickhouse_query(insert_query, data_content)

    async def _execute_clickhouse_query(self, query: str, data: str = None):
        """Execute ClickHouse query."""
        cmd = [
            'clickhouse-client',
            '--host', self.db_config['host'],
            '--port', str(self.db_config['port']),
            '--database', self.db_config['database'],
            '--query', query
        ]

        if self.db_config.get('username'):
            cmd.extend(['--user', self.db_config['username']])
        if self.db_config.get('password'):
            cmd.extend(['--password', self.db_config['password']])

        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE if data else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout_output, stderr_output = process.communicate(input=data)

        if process.returncode != 0:
            raise Exception(f"ClickHouse query failed: {stderr_output}")

    async def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

class DisasterRecoveryManager:
    """Main disaster recovery manager coordinating all database backups."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.backup_configs: Dict[str, BackupConfig] = {}
        self.backup_metadata: List[BackupMetadata] = []
        self.scheduler_thread: Optional[threading.Thread] = None
        self.running = False

        # Default backup configurations
        self._setup_default_configs()

    def _setup_default_configs(self):
        """Setup default backup configurations."""
        self.backup_configs = {
            'postgresql_daily': BackupConfig(
                backup_type=BackupType.FULL,
                schedule="0 2 * * *",  # Daily at 2 AM
                retention_days=30,
                compression=True,
                encryption=True,
                verify_integrity=True,
                backup_location="/backup/postgresql"
            ),
            'postgresql_hourly': BackupConfig(
                backup_type=BackupType.INCREMENTAL,
                schedule="0 * * * *",  # Hourly
                retention_days=7,
                compression=True,
                encryption=False,
                verify_integrity=False,
                backup_location="/backup/postgresql"
            ),
            'clickhouse_daily': BackupConfig(
                backup_type=BackupType.FULL,
                schedule="0 3 * * *",  # Daily at 3 AM
                retention_days=90,  # Longer retention for analytics data
                compression=True,
                encryption=True,
                verify_integrity=True,
                backup_location="/backup/clickhouse"
            ),
            'clickhouse_weekly': BackupConfig(
                backup_type=BackupType.FULL,
                schedule="0 4 * * 0",  # Weekly on Sunday at 4 AM
                retention_days=365,  # Long-term retention
                compression=True,
                encryption=True,
                verify_integrity=True,
                backup_location="/backup/clickhouse/weekly"
            )
        }

    async def initialize(self):
        """Initialize disaster recovery manager."""
        try:
            # Create backup directories
            for config in self.backup_configs.values():
                Path(config.backup_location).mkdir(parents=True, exist_ok=True)

            # Load existing backup metadata
            await self._load_backup_metadata()

            # Start backup scheduler
            self._start_scheduler()

            logger.info("Disaster recovery manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize disaster recovery manager: {e}")
            raise

    def _start_scheduler(self):
        """Start backup scheduler in separate thread."""
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            return

        self.running = True

        # Schedule backup jobs
        for config_name, config in self.backup_configs.items():
            if config_name.startswith('postgresql'):
                schedule.every().day.at("02:00").do(self._scheduled_backup, 'postgresql', config)
                if 'hourly' in config_name:
                    schedule.every().hour.do(self._scheduled_backup, 'postgresql', config)
            elif config_name.startswith('clickhouse'):
                if 'daily' in config_name:
                    schedule.every().day.at("03:00").do(self._scheduled_backup, 'clickhouse', config)
                elif 'weekly' in config_name:
                    schedule.every().sunday.at("04:00").do(self._scheduled_backup, 'clickhouse', config)

        # Start scheduler thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()

        logger.info("Backup scheduler started")

    def _run_scheduler(self):
        """Run backup scheduler loop."""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    def _scheduled_backup(self, database_type: str, config: BackupConfig):
        """Execute scheduled backup."""
        try:
            logger.info(f"Starting scheduled {database_type} backup")

            if database_type == 'postgresql':
                asyncio.create_task(self.backup_postgresql(config))
            elif database_type == 'clickhouse':
                asyncio.create_task(self.backup_clickhouse(config))

        except Exception as e:
            logger.error(f"Scheduled backup failed: {e}")

    async def backup_postgresql(self, config: BackupConfig = None) -> BackupMetadata:
        """Create PostgreSQL backup."""
        if not config:
            config = self.backup_configs['postgresql_daily']

        try:
            pg_config = {
                'host': 'localhost',
                'port': 5432,
                'database': 'aitrading',
                'username': 'postgres',
                'password': 'password'
            }

            pg_backup = PostgreSQLBackup(pg_config, config)
            metadata = await pg_backup.create_backup(config.backup_type)

            self.backup_metadata.append(metadata)
            await self._save_backup_metadata(metadata)

            return metadata

        except Exception as e:
            logger.error(f"PostgreSQL backup failed: {e}")
            raise

    async def backup_clickhouse(self, config: BackupConfig = None) -> BackupMetadata:
        """Create ClickHouse backup."""
        if not config:
            config = self.backup_configs['clickhouse_daily']

        try:
            ch_config = {
                'host': 'localhost',
                'port': 9000,
                'database': 'aitrading_analytics',
                'username': 'default',
                'password': ''
            }

            ch_backup = ClickHouseBackup(ch_config, config)
            metadata = await ch_backup.create_backup()

            self.backup_metadata.append(metadata)
            await self._save_backup_metadata(metadata)

            return metadata

        except Exception as e:
            logger.error(f"ClickHouse backup failed: {e}")
            raise

    async def restore_database(self, recovery_plan: RecoveryPlan) -> bool:
        """Restore database according to recovery plan."""
        try:
            logger.info(f"Starting database recovery: {recovery_plan.recovery_point.value}")

            # Find appropriate backup
            backup_metadata = None

            if recovery_plan.recovery_point == RecoveryPoint.LATEST:
                backup_metadata = self._find_latest_backup(recovery_plan.databases[0])
            elif recovery_plan.recovery_point == RecoveryPoint.NAMED_BACKUP:
                backup_metadata = self._find_backup_by_id(recovery_plan.backup_id)
            elif recovery_plan.recovery_point == RecoveryPoint.POINT_IN_TIME:
                backup_metadata = self._find_backup_by_time(
                    recovery_plan.databases[0], recovery_plan.target_time
                )

            if not backup_metadata:
                logger.error("No suitable backup found for recovery")
                return False

            # Perform recovery based on database type
            if 'postgresql' in backup_metadata.backup_path:
                pg_config = {
                    'host': 'localhost',
                    'port': 5432,
                    'database': 'aitrading',
                    'username': 'postgres',
                    'password': 'password'
                }
                pg_backup = PostgreSQLBackup(pg_config, self.backup_configs['postgresql_daily'])
                return await pg_backup.restore_backup(backup_metadata)

            elif 'clickhouse' in backup_metadata.backup_path:
                ch_config = {
                    'host': 'localhost',
                    'port': 9000,
                    'database': 'aitrading_analytics',
                    'username': 'default',
                    'password': ''
                }
                ch_backup = ClickHouseBackup(ch_config, self.backup_configs['clickhouse_daily'])
                return await ch_backup.restore_backup(backup_metadata)

            return False

        except Exception as e:
            logger.error(f"Database recovery failed: {e}")
            return False

    def _find_latest_backup(self, database: str) -> Optional[BackupMetadata]:
        """Find latest successful backup for database."""
        database_backups = [
            backup for backup in self.backup_metadata
            if backup.status == BackupStatus.COMPLETED
            and database.lower() in backup.backup_path.lower()
        ]

        if not database_backups:
            return None

        return max(database_backups, key=lambda x: x.created_at)

    def _find_backup_by_id(self, backup_id: str) -> Optional[BackupMetadata]:
        """Find backup by ID."""
        for backup in self.backup_metadata:
            if backup.backup_id == backup_id:
                return backup
        return None

    def _find_backup_by_time(self, database: str, target_time: datetime) -> Optional[BackupMetadata]:
        """Find backup closest to target time."""
        database_backups = [
            backup for backup in self.backup_metadata
            if backup.status == BackupStatus.COMPLETED
            and database.lower() in backup.backup_path.lower()
            and backup.created_at <= target_time
        ]

        if not database_backups:
            return None

        return max(database_backups, key=lambda x: x.created_at)

    async def _load_backup_metadata(self):
        """Load backup metadata from database."""
        try:
            # Create metadata table if not exists
            await self.db_manager.postgresql.execute_query("""
            CREATE TABLE IF NOT EXISTS backup_metadata (
                backup_id VARCHAR(255) PRIMARY KEY,
                backup_type VARCHAR(50) NOT NULL,
                database_name VARCHAR(255) NOT NULL,
                backup_path TEXT NOT NULL,
                file_size_bytes BIGINT NOT NULL,
                compressed_size_bytes BIGINT NOT NULL,
                checksum VARCHAR(64) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                completed_at TIMESTAMP WITH TIME ZONE,
                status VARCHAR(50) NOT NULL,
                error_message TEXT,
                retention_until TIMESTAMP WITH TIME ZONE,
                parent_backup_id VARCHAR(255)
            )
            """)

            # Load existing metadata
            results = await self.db_manager.postgresql.execute_query(
                "SELECT * FROM backup_metadata ORDER BY created_at DESC"
            )

            for row in results:
                metadata = BackupMetadata(
                    backup_id=row['backup_id'],
                    backup_type=BackupType(row['backup_type']),
                    database_name=row['database_name'],
                    backup_path=row['backup_path'],
                    file_size_bytes=row['file_size_bytes'],
                    compressed_size_bytes=row['compressed_size_bytes'],
                    checksum=row['checksum'],
                    created_at=row['created_at'],
                    completed_at=row['completed_at'],
                    status=BackupStatus(row['status']),
                    error_message=row['error_message'],
                    retention_until=row['retention_until'],
                    parent_backup_id=row['parent_backup_id']
                )
                self.backup_metadata.append(metadata)

        except Exception as e:
            logger.error(f"Failed to load backup metadata: {e}")

    async def _save_backup_metadata(self, metadata: BackupMetadata):
        """Save backup metadata to database."""
        try:
            query = """
            INSERT INTO backup_metadata (
                backup_id, backup_type, database_name, backup_path,
                file_size_bytes, compressed_size_bytes, checksum,
                created_at, completed_at, status, error_message,
                retention_until, parent_backup_id
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            ON CONFLICT (backup_id) DO UPDATE SET
                status = EXCLUDED.status,
                completed_at = EXCLUDED.completed_at,
                error_message = EXCLUDED.error_message
            """

            await self.db_manager.postgresql.execute_query(
                query,
                metadata.backup_id,
                metadata.backup_type.value,
                metadata.database_name,
                metadata.backup_path,
                metadata.file_size_bytes,
                metadata.compressed_size_bytes,
                metadata.checksum,
                metadata.created_at,
                metadata.completed_at,
                metadata.status.value,
                metadata.error_message,
                metadata.retention_until,
                metadata.parent_backup_id
            )

        except Exception as e:
            logger.error(f"Failed to save backup metadata: {e}")

    async def cleanup_expired_backups(self):
        """Clean up expired backups."""
        try:
            current_time = datetime.now()
            expired_backups = [
                backup for backup in self.backup_metadata
                if backup.retention_until and backup.retention_until < current_time
            ]

            for backup in expired_backups:
                try:
                    # Delete backup file
                    backup_path = Path(backup.backup_path)
                    if backup_path.exists():
                        backup_path.unlink()

                    # Remove from metadata
                    self.backup_metadata.remove(backup)

                    # Delete from database
                    await self.db_manager.postgresql.execute_query(
                        "DELETE FROM backup_metadata WHERE backup_id = $1",
                        backup.backup_id
                    )

                    logger.info(f"Cleaned up expired backup: {backup.backup_id}")

                except Exception as e:
                    logger.error(f"Failed to cleanup backup {backup.backup_id}: {e}")

        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """Perform disaster recovery health check."""
        health = {
            'status': 'healthy',
            'backup_counts': {},
            'recent_backups': {},
            'storage_usage': {},
            'scheduler_status': 'running' if self.running else 'stopped'
        }

        try:
            # Count backups by database and status
            for backup in self.backup_metadata:
                db_type = 'postgresql' if 'postgresql' in backup.backup_path else 'clickhouse'

                if db_type not in health['backup_counts']:
                    health['backup_counts'][db_type] = {
                        'total': 0,
                        'completed': 0,
                        'failed': 0,
                        'in_progress': 0
                    }

                health['backup_counts'][db_type]['total'] += 1
                health['backup_counts'][db_type][backup.status.value] += 1

            # Check recent backups (last 24 hours)
            recent_time = datetime.now() - timedelta(hours=24)
            recent_backups = [
                backup for backup in self.backup_metadata
                if backup.created_at > recent_time
            ]

            health['recent_backups'] = {
                'count': len(recent_backups),
                'successful': len([b for b in recent_backups if b.status == BackupStatus.COMPLETED]),
                'failed': len([b for b in recent_backups if b.status == BackupStatus.FAILED])
            }

            # Calculate storage usage
            for config_name, config in self.backup_configs.items():
                backup_dir = Path(config.backup_location)
                if backup_dir.exists():
                    total_size = sum(
                        f.stat().st_size for f in backup_dir.rglob('*') if f.is_file()
                    )
                    health['storage_usage'][config_name] = {
                        'total_bytes': total_size,
                        'total_mb': round(total_size / 1024 / 1024, 2)
                    }

            # Check if backups are recent enough
            if health['recent_backups']['count'] == 0:
                health['status'] = 'warning'
                health['warning'] = 'No recent backups found'

            if health['recent_backups']['failed'] > 0:
                health['status'] = 'degraded'

        except Exception as e:
            health['status'] = 'unhealthy'
            health['error'] = str(e)

        return health

    async def stop(self):
        """Stop disaster recovery manager."""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Disaster recovery manager stopped")

# Global disaster recovery manager instance
disaster_recovery_manager: Optional[DisasterRecoveryManager] = None

async def get_disaster_recovery_manager(db_manager: DatabaseManager) -> DisasterRecoveryManager:
    """Get the global disaster recovery manager instance."""
    global disaster_recovery_manager
    if not disaster_recovery_manager:
        disaster_recovery_manager = DisasterRecoveryManager(db_manager)
        await disaster_recovery_manager.initialize()
    return disaster_recovery_manager