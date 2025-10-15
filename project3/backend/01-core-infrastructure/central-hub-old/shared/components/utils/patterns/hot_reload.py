"""
Hot Reload Manager untuk semua services
Menyediakan generic hot reload untuk config, routes, modules, dan custom resources
"""

import asyncio
import logging as python_logging
import hashlib
import time
from typing import Any, Dict, Optional, Callable, List, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import json
import yaml


class ReloadType(Enum):
    """Type of resource to reload"""
    CONFIG = "config"
    ROUTES = "routes"
    MODULE = "module"
    STRATEGY = "strategy"
    CUSTOM = "custom"


@dataclass
class WatchConfig:
    """Configuration for file watcher"""
    path: Union[str, Path]
    reload_type: ReloadType
    callback: Callable
    watch_interval: float = 2.0
    file_pattern: Optional[str] = None  # e.g., "*.py", "*.json", "*.yaml"


class HotReloadManager:
    """
    Generic hot reload manager
    Watches files/directories and triggers callbacks on changes
    """

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.watchers: Dict[str, WatchConfig] = {}
        self.file_hashes: Dict[str, str] = {}
        self.watch_tasks: Dict[str, asyncio.Task] = {}
        self.logger = python_logging.getLogger(f"{service_name}.hot_reload")
        self.running = False

    def register_watcher(self, name: str, config: WatchConfig):
        """
        Register a file/directory watcher

        Args:
            name: Watcher name (unique identifier)
            config: Watch configuration
        """
        self.watchers[name] = config
        self.logger.info(f"Registered watcher '{name}' for {config.path} ({config.reload_type.value})")

    def unregister_watcher(self, name: str):
        """
        Unregister a watcher

        Args:
            name: Watcher name
        """
        if name in self.watchers:
            # Cancel watch task if running
            if name in self.watch_tasks:
                self.watch_tasks[name].cancel()
                del self.watch_tasks[name]

            del self.watchers[name]
            self.logger.info(f"Unregistered watcher '{name}'")

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            self.logger.error(f"Error calculating hash for {file_path}: {str(e)}")
            return ""

    def _calculate_directory_hash(self, dir_path: Path, pattern: Optional[str] = None) -> Dict[str, str]:
        """
        Calculate hashes for all files in directory

        Args:
            dir_path: Directory path
            pattern: Optional file pattern (e.g., "*.py")

        Returns:
            Dict mapping file paths to hashes
        """
        hashes = {}

        try:
            if pattern:
                files = dir_path.glob(pattern)
            else:
                files = dir_path.rglob("*")

            for file_path in files:
                if file_path.is_file():
                    rel_path = str(file_path.relative_to(dir_path))
                    hashes[rel_path] = self._calculate_file_hash(file_path)

        except Exception as e:
            self.logger.error(f"Error calculating directory hash for {dir_path}: {str(e)}")

        return hashes

    def _load_file_content(self, file_path: Path) -> Any:
        """
        Load file content based on extension

        Args:
            file_path: Path to file

        Returns:
            Parsed file content
        """
        try:
            suffix = file_path.suffix.lower()

            with open(file_path, 'r') as f:
                if suffix == '.json':
                    return json.load(f)
                elif suffix in ['.yaml', '.yml']:
                    return yaml.safe_load(f)
                else:
                    return f.read()

        except Exception as e:
            self.logger.error(f"Error loading file {file_path}: {str(e)}")
            return None

    async def _watch_file(self, name: str, config: WatchConfig):
        """
        Watch a single file for changes

        Args:
            name: Watcher name
            config: Watch configuration
        """
        file_path = Path(config.path)

        if not file_path.exists():
            self.logger.warning(f"Watch file does not exist: {file_path}")
            return

        # Initial hash
        current_hash = self._calculate_file_hash(file_path)
        self.file_hashes[name] = current_hash

        self.logger.info(f"Started watching file: {file_path}")

        while self.running:
            try:
                await asyncio.sleep(config.watch_interval)

                # Check if file still exists
                if not file_path.exists():
                    self.logger.warning(f"Watch file disappeared: {file_path}")
                    continue

                # Calculate new hash
                new_hash = self._calculate_file_hash(file_path)

                # Check for changes
                if new_hash != current_hash:
                    self.logger.info(f"File changed: {file_path}")

                    # Load new content
                    content = self._load_file_content(file_path)

                    # Trigger callback
                    try:
                        if asyncio.iscoroutinefunction(config.callback):
                            await config.callback(content, file_path)
                        else:
                            config.callback(content, file_path)

                        self.logger.info(f"Reloaded {config.reload_type.value}: {file_path}")
                        current_hash = new_hash
                        self.file_hashes[name] = current_hash

                    except Exception as e:
                        self.logger.error(f"Error in reload callback for {file_path}: {str(e)}")

            except asyncio.CancelledError:
                self.logger.info(f"File watch cancelled: {file_path}")
                break
            except Exception as e:
                self.logger.error(f"Error watching file {file_path}: {str(e)}")
                await asyncio.sleep(config.watch_interval)

    async def _watch_directory(self, name: str, config: WatchConfig):
        """
        Watch a directory for changes

        Args:
            name: Watcher name
            config: Watch configuration
        """
        dir_path = Path(config.path)

        if not dir_path.exists():
            self.logger.warning(f"Watch directory does not exist: {dir_path}")
            return

        # Initial hashes
        current_hashes = self._calculate_directory_hash(dir_path, config.file_pattern)
        self.file_hashes[name] = json.dumps(current_hashes)

        self.logger.info(f"Started watching directory: {dir_path}" +
                        (f" (pattern: {config.file_pattern})" if config.file_pattern else ""))

        while self.running:
            try:
                await asyncio.sleep(config.watch_interval)

                # Check if directory still exists
                if not dir_path.exists():
                    self.logger.warning(f"Watch directory disappeared: {dir_path}")
                    continue

                # Calculate new hashes
                new_hashes = self._calculate_directory_hash(dir_path, config.file_pattern)

                # Find changed files
                changed_files = []
                for file_rel_path, new_hash in new_hashes.items():
                    old_hash = current_hashes.get(file_rel_path)
                    if old_hash != new_hash:
                        changed_files.append(file_rel_path)

                # Find deleted files
                deleted_files = set(current_hashes.keys()) - set(new_hashes.keys())

                # Find new files
                new_files = set(new_hashes.keys()) - set(current_hashes.keys())

                # Trigger callback if changes detected
                if changed_files or deleted_files or new_files:
                    changes = {
                        "changed": changed_files,
                        "deleted": list(deleted_files),
                        "new": list(new_files)
                    }

                    self.logger.info(f"Directory changes detected in {dir_path}: "
                                   f"{len(changed_files)} changed, {len(new_files)} new, {len(deleted_files)} deleted")

                    try:
                        if asyncio.iscoroutinefunction(config.callback):
                            await config.callback(changes, dir_path)
                        else:
                            config.callback(changes, dir_path)

                        self.logger.info(f"Reloaded {config.reload_type.value}: {dir_path}")
                        current_hashes = new_hashes
                        self.file_hashes[name] = json.dumps(current_hashes)

                    except Exception as e:
                        self.logger.error(f"Error in reload callback for {dir_path}: {str(e)}")

            except asyncio.CancelledError:
                self.logger.info(f"Directory watch cancelled: {dir_path}")
                break
            except Exception as e:
                self.logger.error(f"Error watching directory {dir_path}: {str(e)}")
                await asyncio.sleep(config.watch_interval)

    async def start_watching(self):
        """Start all watchers"""
        if self.running:
            self.logger.warning("Hot reload already running")
            return

        self.running = True

        for name, config in self.watchers.items():
            path = Path(config.path)

            if path.is_file():
                task = asyncio.create_task(self._watch_file(name, config))
            elif path.is_dir():
                task = asyncio.create_task(self._watch_directory(name, config))
            else:
                self.logger.warning(f"Path does not exist or is invalid: {path}")
                continue

            self.watch_tasks[name] = task

        self.logger.info(f"Started {len(self.watch_tasks)} hot reload watchers")

    async def stop_watching(self):
        """Stop all watchers"""
        if not self.running:
            return

        self.running = False

        # Cancel all watch tasks
        for name, task in self.watch_tasks.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self.watch_tasks.clear()
        self.logger.info("Stopped all hot reload watchers")

    def is_watching(self) -> bool:
        """Check if watchers are running"""
        return self.running

    def get_watchers(self) -> List[str]:
        """Get list of registered watchers"""
        return list(self.watchers.keys())


# Convenience functions for common reload scenarios

async def reload_config(service_name: str, config_path: Union[str, Path],
                       config_manager, watch_interval: float = 5.0):
    """
    Create hot reload for configuration files

    Args:
        service_name: Service name
        config_path: Path to config file or directory
        config_manager: ConfigManager instance to reload
        watch_interval: Check interval in seconds
    """
    hot_reload = HotReloadManager(service_name)

    async def config_callback(content, path):
        """Reload config callback"""
        await config_manager.reload()

    hot_reload.register_watcher(
        "config",
        WatchConfig(
            path=config_path,
            reload_type=ReloadType.CONFIG,
            callback=config_callback,
            watch_interval=watch_interval,
            file_pattern="*.json" if Path(config_path).is_dir() else None
        )
    )

    await hot_reload.start_watching()
    return hot_reload


async def reload_routes(service_name: str, routes_path: Union[str, Path],
                       route_loader_callback: Callable, watch_interval: float = 5.0):
    """
    Create hot reload for API routes

    Args:
        service_name: Service name
        routes_path: Path to routes file or directory
        route_loader_callback: Function to reload routes
        watch_interval: Check interval in seconds
    """
    hot_reload = HotReloadManager(service_name)

    async def routes_callback(content, path):
        """Reload routes callback"""
        if asyncio.iscoroutinefunction(route_loader_callback):
            await route_loader_callback(content, path)
        else:
            route_loader_callback(content, path)

    hot_reload.register_watcher(
        "routes",
        WatchConfig(
            path=routes_path,
            reload_type=ReloadType.ROUTES,
            callback=routes_callback,
            watch_interval=watch_interval,
            file_pattern="*.py" if Path(routes_path).is_dir() else None
        )
    )

    await hot_reload.start_watching()
    return hot_reload


async def reload_strategy(service_name: str, strategy_path: Union[str, Path],
                         strategy_loader_callback: Callable, watch_interval: float = 5.0):
    """
    Create hot reload for trading strategies

    Args:
        service_name: Service name
        strategy_path: Path to strategy file or directory
        strategy_loader_callback: Function to reload strategy
        watch_interval: Check interval in seconds
    """
    hot_reload = HotReloadManager(service_name)

    async def strategy_callback(content, path):
        """Reload strategy callback"""
        if asyncio.iscoroutinefunction(strategy_loader_callback):
            await strategy_loader_callback(content, path)
        else:
            strategy_loader_callback(content, path)

    hot_reload.register_watcher(
        "strategy",
        WatchConfig(
            path=strategy_path,
            reload_type=ReloadType.STRATEGY,
            callback=strategy_callback,
            watch_interval=watch_interval,
            file_pattern="*.py" if Path(strategy_path).is_dir() else None
        )
    )

    await hot_reload.start_watching()
    return hot_reload
