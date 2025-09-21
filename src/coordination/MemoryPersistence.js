/**
 * MemoryPersistence - Persistent storage layer for agent coordination memory
 * Handles serialization, compression, and cross-session state management
 */

const fs = require('fs').promises;
const path = require('path');
const zlib = require('zlib');
const { promisify } = require('util');

const gzip = promisify(zlib.gzip);
const gunzip = promisify(zlib.gunzip);

class MemoryPersistence {
  constructor(memoryCoordination) {
    this.memoryCoordination = memoryCoordination;
    this.persistencePath = process.env.COORDINATION_PERSISTENCE_PATH || './.swarm/coordination';
    this.compressionEnabled = true;
    this.encryptionEnabled = false;
    this.backupRetentionDays = 7;
    this.autoSaveInterval = 300000; // 5 minutes
    this.autoSaveTimer = null;
    this.pendingWrites = new Map();
    this.writeQueue = [];
    this.isInitialized = false;
  }

  /**
   * Initialize persistence system
   */
  async initialize() {
    if (this.isInitialized) return;

    try {
      // Ensure persistence directory exists
      await this.ensureDirectoryStructure();

      // Load existing state if available
      await this.loadPersistedState();

      // Start auto-save timer
      this.startAutoSave();

      // Setup graceful shutdown handlers
      this.setupShutdownHandlers();

      this.isInitialized = true;

      console.log(`Memory persistence initialized at: ${this.persistencePath}`);

    } catch (error) {
      console.error('Failed to initialize memory persistence:', error);
      throw error;
    }
  }

  /**
   * Persist memory state to storage
   */
  async persistMemoryState(namespace = null, force = false) {
    if (!this.isInitialized && !force) return;

    const persistenceId = `persist_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    try {
      const state = await this.captureMemoryState(namespace);
      const serialized = await this.serializeState(state);
      const compressed = this.compressionEnabled ? await gzip(serialized) : serialized;

      const filename = namespace
        ? `${namespace}_${Date.now()}.json${this.compressionEnabled ? '.gz' : ''}`
        : `full_state_${Date.now()}.json${this.compressionEnabled ? '.gz' : ''}`;

      const filepath = path.join(this.persistencePath, 'snapshots', filename);

      // Queue write operation
      const writeOperation = {
        id: persistenceId,
        filepath,
        data: compressed,
        namespace,
        timestamp: Date.now(),
        metadata: {
          originalSize: serialized.length,
          compressedSize: compressed.length,
          compressionRatio: this.compressionEnabled ? compressed.length / serialized.length : 1
        }
      };

      this.writeQueue.push(writeOperation);
      await this.processWriteQueue();

      // Store persistence record in memory
      await this.memoryCoordination.store(
        'coord/persistence',
        persistenceId,
        {
          id: persistenceId,
          type: 'state_snapshot',
          namespace,
          filename,
          metadata: writeOperation.metadata,
          timestamp: Date.now()
        },
        'system'
      );

      return persistenceId;

    } catch (error) {
      console.error('Failed to persist memory state:', error);
      throw error;
    }
  }

  /**
   * Load persisted state into memory
   */
  async loadPersistedState(persistenceId = null) {
    try {
      let stateFile;

      if (persistenceId) {
        // Load specific state
        const record = await this.memoryCoordination.retrieve(
          'coord/persistence',
          persistenceId,
          'system'
        );
        if (!record) {
          throw new Error(`Persistence record ${persistenceId} not found`);
        }
        stateFile = path.join(this.persistencePath, 'snapshots', record.filename);
      } else {
        // Load latest state
        stateFile = await this.findLatestStateFile();
      }

      if (!stateFile || !(await this.fileExists(stateFile))) {
        console.log('No persisted state found, starting with clean memory');
        return null;
      }

      const compressed = await fs.readFile(stateFile);
      const serialized = this.compressionEnabled ? await gunzip(compressed) : compressed;
      const state = await this.deserializeState(serialized);

      await this.restoreMemoryState(state);

      console.log(`Loaded persisted state from: ${stateFile}`);
      return state;

    } catch (error) {
      console.error('Failed to load persisted state:', error);
      throw error;
    }
  }

  /**
   * Create backup of current memory state
   */
  async createBackup(name = null) {
    const backupId = `backup_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const backupName = name || `backup_${new Date().toISOString().split('T')[0]}`;

    try {
      const state = await this.captureMemoryState();
      const metadata = {
        id: backupId,
        name: backupName,
        created: Date.now(),
        createdBy: 'system',
        type: 'full_backup',
        size: JSON.stringify(state).length
      };

      // Serialize and compress
      const serialized = await this.serializeState({ state, metadata });
      const compressed = this.compressionEnabled ? await gzip(serialized) : serialized;

      const filename = `${backupName}_${Date.now()}.backup${this.compressionEnabled ? '.gz' : ''}`;
      const filepath = path.join(this.persistencePath, 'backups', filename);

      await fs.writeFile(filepath, compressed);

      // Store backup record
      await this.memoryCoordination.store(
        'coord/backups',
        backupId,
        {
          ...metadata,
          filename,
          filepath,
          compressed: this.compressionEnabled,
          compressedSize: compressed.length
        },
        'system'
      );

      console.log(`Backup created: ${filename}`);
      return backupId;

    } catch (error) {
      console.error('Failed to create backup:', error);
      throw error;
    }
  }

  /**
   * Restore from backup
   */
  async restoreFromBackup(backupId) {
    try {
      const backupRecord = await this.memoryCoordination.retrieve(
        'coord/backups',
        backupId,
        'system'
      );

      if (!backupRecord) {
        throw new Error(`Backup ${backupId} not found`);
      }

      const filepath = backupRecord.filepath;
      if (!(await this.fileExists(filepath))) {
        throw new Error(`Backup file not found: ${filepath}`);
      }

      const compressed = await fs.readFile(filepath);
      const serialized = backupRecord.compressed ? await gunzip(compressed) : compressed;
      const backupData = await this.deserializeState(serialized);

      // Clear current memory state
      this.memoryCoordination.cleanup();

      // Restore from backup
      await this.restoreMemoryState(backupData.state);

      console.log(`Restored from backup: ${backupRecord.name}`);
      return backupData.metadata;

    } catch (error) {
      console.error('Failed to restore from backup:', error);
      throw error;
    }
  }

  /**
   * Incremental save - only save changes since last save
   */
  async incrementalSave() {
    const lastSaveTime = await this.getLastSaveTime();
    const changes = await this.captureChangesSince(lastSaveTime);

    if (Object.keys(changes).length === 0) {
      return null; // No changes to save
    }

    const incrementalId = `incremental_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    try {
      const changeSet = {
        id: incrementalId,
        timestamp: Date.now(),
        baseSaveTime: lastSaveTime,
        changes,
        type: 'incremental'
      };

      const serialized = await this.serializeState(changeSet);
      const compressed = this.compressionEnabled ? await gzip(serialized) : serialized;

      const filename = `incremental_${Date.now()}.json${this.compressionEnabled ? '.gz' : ''}`;
      const filepath = path.join(this.persistencePath, 'incremental', filename);

      await fs.writeFile(filepath, compressed);

      // Update last save time
      await this.updateLastSaveTime(Date.now());

      // Store incremental record
      await this.memoryCoordination.store(
        'coord/incremental_saves',
        incrementalId,
        {
          id: incrementalId,
          filename,
          changeCount: Object.keys(changes).length,
          timestamp: Date.now()
        },
        'system'
      );

      return incrementalId;

    } catch (error) {
      console.error('Failed to perform incremental save:', error);
      throw error;
    }
  }

  /**
   * Compact persistence files by merging incremental saves
   */
  async compactPersistenceFiles() {
    try {
      // Get all incremental saves
      const incrementalDir = path.join(this.persistencePath, 'incremental');
      const incrementalFiles = await this.getDirectoryFiles(incrementalDir);

      if (incrementalFiles.length === 0) {
        return null; // Nothing to compact
      }

      // Load and merge all incremental changes
      const mergedChanges = {};
      for (const file of incrementalFiles) {
        const filepath = path.join(incrementalDir, file);
        const compressed = await fs.readFile(filepath);
        const serialized = this.compressionEnabled ? await gunzip(compressed) : compressed;
        const changeSet = await this.deserializeState(serialized);

        Object.assign(mergedChanges, changeSet.changes);
      }

      // Create new full snapshot with merged changes
      const fullState = await this.captureMemoryState();
      Object.assign(fullState, mergedChanges);

      const snapshotId = await this.persistMemoryState(null, true);

      // Clean up incremental files
      for (const file of incrementalFiles) {
        await fs.unlink(path.join(incrementalDir, file));
      }

      console.log(`Compacted ${incrementalFiles.length} incremental saves into snapshot ${snapshotId}`);
      return snapshotId;

    } catch (error) {
      console.error('Failed to compact persistence files:', error);
      throw error;
    }
  }

  /**
   * Cleanup old backups and snapshots
   */
  async cleanupOldFiles() {
    const cutoffDate = Date.now() - (this.backupRetentionDays * 24 * 60 * 60 * 1000);

    try {
      // Cleanup old snapshots
      const snapshotsDir = path.join(this.persistencePath, 'snapshots');
      await this.cleanupDirectoryByAge(snapshotsDir, cutoffDate);

      // Cleanup old backups
      const backupsDir = path.join(this.persistencePath, 'backups');
      await this.cleanupDirectoryByAge(backupsDir, cutoffDate);

      // Cleanup old incremental saves (keep only recent ones)
      const incrementalDir = path.join(this.persistencePath, 'incremental');
      const recentCutoff = Date.now() - (2 * 24 * 60 * 60 * 1000); // 2 days
      await this.cleanupDirectoryByAge(incrementalDir, recentCutoff);

    } catch (error) {
      console.error('Failed to cleanup old files:', error);
    }
  }

  /**
   * Export memory state to external format
   */
  async exportMemoryState(format = 'json', outputPath = null) {
    const state = await this.captureMemoryState();
    const exportId = `export_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    try {
      let exportData;
      let filename;

      switch (format.toLowerCase()) {
        case 'json':
          exportData = JSON.stringify(state, null, 2);
          filename = `memory_export_${Date.now()}.json`;
          break;

        case 'csv':
          exportData = await this.convertToCSV(state);
          filename = `memory_export_${Date.now()}.csv`;
          break;

        case 'yaml':
          // Would need yaml library
          throw new Error('YAML export not implemented');

        default:
          throw new Error(`Unsupported export format: ${format}`);
      }

      const filepath = outputPath || path.join(this.persistencePath, 'exports', filename);
      await this.ensureDirectoryExists(path.dirname(filepath));
      await fs.writeFile(filepath, exportData);

      return {
        exportId,
        filepath,
        format,
        size: exportData.length,
        timestamp: Date.now()
      };

    } catch (error) {
      console.error('Failed to export memory state:', error);
      throw error;
    }
  }

  /**
   * Import memory state from external file
   */
  async importMemoryState(filepath, format = 'json', merge = false) {
    try {
      if (!(await this.fileExists(filepath))) {
        throw new Error(`Import file not found: ${filepath}`);
      }

      const rawData = await fs.readFile(filepath, 'utf8');
      let importedState;

      switch (format.toLowerCase()) {
        case 'json':
          importedState = JSON.parse(rawData);
          break;

        case 'csv':
          importedState = await this.convertFromCSV(rawData);
          break;

        default:
          throw new Error(`Unsupported import format: ${format}`);
      }

      if (!merge) {
        // Replace current state
        this.memoryCoordination.cleanup();
      }

      await this.restoreMemoryState(importedState);

      console.log(`Imported memory state from: ${filepath}`);
      return {
        imported: true,
        filepath,
        format,
        merge,
        timestamp: Date.now()
      };

    } catch (error) {
      console.error('Failed to import memory state:', error);
      throw error;
    }
  }

  /**
   * Get persistence statistics
   */
  async getPersistenceStatistics() {
    try {
      const stats = {
        initialized: this.isInitialized,
        persistencePath: this.persistencePath,
        compressionEnabled: this.compressionEnabled,
        autoSaveInterval: this.autoSaveInterval,
        storage: {
          snapshots: 0,
          backups: 0,
          incremental: 0,
          exports: 0,
          totalSize: 0
        },
        operations: {
          pendingWrites: this.pendingWrites.size,
          queuedWrites: this.writeQueue.length
        }
      };

      // Calculate storage usage
      const directories = ['snapshots', 'backups', 'incremental', 'exports'];

      for (const dir of directories) {
        const dirPath = path.join(this.persistencePath, dir);
        if (await this.fileExists(dirPath)) {
          const files = await this.getDirectoryFiles(dirPath);
          stats.storage[dir] = files.length;

          for (const file of files) {
            const filePath = path.join(dirPath, file);
            const fileStat = await fs.stat(filePath);
            stats.storage.totalSize += fileStat.size;
          }
        }
      }

      return stats;

    } catch (error) {
      console.error('Failed to get persistence statistics:', error);
      return null;
    }
  }

  /**
   * Helper methods for persistence operations
   */

  async ensureDirectoryStructure() {
    const directories = [
      this.persistencePath,
      path.join(this.persistencePath, 'snapshots'),
      path.join(this.persistencePath, 'backups'),
      path.join(this.persistencePath, 'incremental'),
      path.join(this.persistencePath, 'exports')
    ];

    for (const dir of directories) {
      await this.ensureDirectoryExists(dir);
    }
  }

  async ensureDirectoryExists(dirPath) {
    try {
      await fs.access(dirPath);
    } catch {
      await fs.mkdir(dirPath, { recursive: true });
    }
  }

  async captureMemoryState(namespace = null) {
    const memoryStats = this.memoryCoordination.getMemoryStatistics();

    if (namespace) {
      // Capture specific namespace
      const namespaceData = await this.memoryCoordination.retrieve(namespace, '*', 'system');
      return {
        namespace,
        data: namespaceData,
        timestamp: Date.now()
      };
    } else {
      // Capture full state
      return {
        globalMemory: this.memoryCoordination.globalMemory,
        agentMemories: this.memoryCoordination.agentMemories,
        sharedNamespaces: this.memoryCoordination.sharedNamespaces,
        statistics: memoryStats,
        timestamp: Date.now()
      };
    }
  }

  async restoreMemoryState(state) {
    if (state.namespace) {
      // Restore specific namespace
      await this.memoryCoordination.store(
        state.namespace,
        'restored_state',
        state.data,
        'system'
      );
    } else {
      // Restore full state
      if (state.globalMemory) {
        this.memoryCoordination.globalMemory = new Map(state.globalMemory);
      }
      if (state.agentMemories) {
        this.memoryCoordination.agentMemories = new Map(state.agentMemories);
      }
      if (state.sharedNamespaces) {
        this.memoryCoordination.sharedNamespaces = new Map(state.sharedNamespaces);
      }
    }
  }

  async serializeState(state) {
    // Convert Maps and Sets to serializable format
    const serializable = this.convertForSerialization(state);
    return JSON.stringify(serializable);
  }

  async deserializeState(serialized) {
    const parsed = JSON.parse(serialized.toString());
    return this.convertFromSerialization(parsed);
  }

  convertForSerialization(obj) {
    if (obj instanceof Map) {
      return { __type: 'Map', data: Array.from(obj.entries()) };
    } else if (obj instanceof Set) {
      return { __type: 'Set', data: Array.from(obj) };
    } else if (Array.isArray(obj)) {
      return obj.map(item => this.convertForSerialization(item));
    } else if (obj && typeof obj === 'object') {
      const converted = {};
      for (const [key, value] of Object.entries(obj)) {
        converted[key] = this.convertForSerialization(value);
      }
      return converted;
    }
    return obj;
  }

  convertFromSerialization(obj) {
    if (obj && obj.__type === 'Map') {
      const map = new Map();
      obj.data.forEach(([key, value]) => {
        map.set(key, this.convertFromSerialization(value));
      });
      return map;
    } else if (obj && obj.__type === 'Set') {
      return new Set(obj.data.map(item => this.convertFromSerialization(item)));
    } else if (Array.isArray(obj)) {
      return obj.map(item => this.convertFromSerialization(item));
    } else if (obj && typeof obj === 'object') {
      const converted = {};
      for (const [key, value] of Object.entries(obj)) {
        converted[key] = this.convertFromSerialization(value);
      }
      return converted;
    }
    return obj;
  }

  async processWriteQueue() {
    while (this.writeQueue.length > 0) {
      const operation = this.writeQueue.shift();
      try {
        await this.ensureDirectoryExists(path.dirname(operation.filepath));
        await fs.writeFile(operation.filepath, operation.data);
        this.pendingWrites.delete(operation.id);
      } catch (error) {
        console.error(`Failed to write ${operation.filepath}:`, error);
        // Re-queue with retry count
        operation.retries = (operation.retries || 0) + 1;
        if (operation.retries < 3) {
          this.writeQueue.push(operation);
        }
      }
    }
  }

  async findLatestStateFile() {
    const snapshotsDir = path.join(this.persistencePath, 'snapshots');
    try {
      const files = await this.getDirectoryFiles(snapshotsDir);
      if (files.length === 0) return null;

      // Sort by modification time
      const fileStats = await Promise.all(
        files.map(async file => {
          const filepath = path.join(snapshotsDir, file);
          const stat = await fs.stat(filepath);
          return { file, filepath, mtime: stat.mtime };
        })
      );

      fileStats.sort((a, b) => b.mtime - a.mtime);
      return fileStats[0].filepath;

    } catch (error) {
      return null;
    }
  }

  async getDirectoryFiles(dirPath) {
    try {
      return await fs.readdir(dirPath);
    } catch {
      return [];
    }
  }

  async fileExists(filepath) {
    try {
      await fs.access(filepath);
      return true;
    } catch {
      return false;
    }
  }

  async cleanupDirectoryByAge(dirPath, cutoffDate) {
    const files = await this.getDirectoryFiles(dirPath);

    for (const file of files) {
      const filepath = path.join(dirPath, file);
      const stat = await fs.stat(filepath);

      if (stat.mtime.getTime() < cutoffDate) {
        await fs.unlink(filepath);
      }
    }
  }

  async getLastSaveTime() {
    try {
      const record = await this.memoryCoordination.retrieve(
        'coord/persistence',
        'last_save_time',
        'system'
      );
      return record || 0;
    } catch {
      return 0;
    }
  }

  async updateLastSaveTime(timestamp) {
    await this.memoryCoordination.store(
      'coord/persistence',
      'last_save_time',
      timestamp,
      'system'
    );
  }

  async captureChangesSince(lastSaveTime) {
    // Simplified implementation - in real system, would track changes
    const currentState = await this.captureMemoryState();
    return currentState; // Would contain only changes since lastSaveTime
  }

  async convertToCSV(state) {
    // Simplified CSV conversion
    let csv = 'namespace,key,value,timestamp\n';
    // Implementation would flatten the state into CSV format
    return csv;
  }

  async convertFromCSV(csvData) {
    // Simplified CSV parsing
    const lines = csvData.split('\n').slice(1); // Skip header
    const state = {};
    // Implementation would parse CSV into state format
    return state;
  }

  startAutoSave() {
    if (this.autoSaveTimer) {
      clearInterval(this.autoSaveTimer);
    }

    this.autoSaveTimer = setInterval(async () => {
      try {
        await this.incrementalSave();
      } catch (error) {
        console.error('Auto-save failed:', error);
      }
    }, this.autoSaveInterval);
  }

  setupShutdownHandlers() {
    const shutdown = async () => {
      console.log('Saving memory state before shutdown...');
      await this.persistMemoryState(null, true);
      process.exit(0);
    };

    process.on('SIGINT', shutdown);
    process.on('SIGTERM', shutdown);
  }

  /**
   * Cleanup persistence system
   */
  cleanup() {
    if (this.autoSaveTimer) {
      clearInterval(this.autoSaveTimer);
      this.autoSaveTimer = null;
    }

    this.pendingWrites.clear();
    this.writeQueue = [];
    this.isInitialized = false;
  }
}

module.exports = MemoryPersistence;