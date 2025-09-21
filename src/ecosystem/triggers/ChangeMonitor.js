/**
 * ChangeMonitor - Auto-trigger system for code changes
 * Monitors file system changes and triggers appropriate documentation agents
 */

const fs = require('fs');
const path = require('path');
const chokidar = require('chokidar');
const { EventEmitter } = require('events');
const { debounce } = require('lodash');

class ChangeMonitor extends EventEmitter {
  constructor(config = {}) {
    super();
    this.config = {
      watchPaths: config.watchPaths || ['src/**', 'lib/**', 'api/**', 'routes/**'],
      ignorePaths: config.ignorePaths || ['node_modules/**', '.git/**', 'dist/**', 'build/**'],
      debounceDelay: config.debounceDelay || 1000,
      batchChanges: config.batchChanges !== false,
      maxBatchSize: config.maxBatchSize || 10,
      ...config
    };

    this.watcher = null;
    this.changeQueue = [];
    this.isMonitoring = false;

    // Debounced change handler to batch rapid changes
    this.debouncedProcessChanges = debounce(
      this.processChangeQueue.bind(this),
      this.config.debounceDelay
    );
  }

  /**
   * Start monitoring file system changes
   */
  async startMonitoring() {
    if (this.isMonitoring) {
      console.warn('⚠️ Change monitor is already running');
      return;
    }

    try {
      console.log('🔍 Starting file system monitoring...');

      this.watcher = chokidar.watch(this.config.watchPaths, {
        ignored: this.config.ignorePaths,
        persistent: true,
        ignoreInitial: true,
        atomic: true,
        awaitWriteFinish: {
          stabilityThreshold: 300,
          pollInterval: 100
        }
      });

      this.setupWatcherEvents();
      this.isMonitoring = true;

      console.log('✅ File system monitoring started successfully');
      this.emit('monitoring-started');
    } catch (error) {
      console.error('❌ Failed to start file system monitoring:', error);
      throw error;
    }
  }

  /**
   * Stop monitoring file system changes
   */
  async stopMonitoring() {
    if (!this.isMonitoring) return;

    try {
      if (this.watcher) {
        await this.watcher.close();
        this.watcher = null;
      }

      this.isMonitoring = false;
      this.changeQueue = [];

      console.log('⏹️ File system monitoring stopped');
      this.emit('monitoring-stopped');
    } catch (error) {
      console.error('❌ Failed to stop monitoring:', error);
      throw error;
    }
  }

  /**
   * Setup file watcher event handlers
   */
  setupWatcherEvents() {
    this.watcher
      .on('add', (filePath) => this.handleFileChange('add', filePath))
      .on('change', (filePath) => this.handleFileChange('change', filePath))
      .on('unlink', (filePath) => this.handleFileChange('delete', filePath))
      .on('addDir', (dirPath) => this.handleFileChange('addDir', dirPath))
      .on('unlinkDir', (dirPath) => this.handleFileChange('deleteDir', dirPath))
      .on('error', (error) => {
        console.error('❌ File watcher error:', error);
        this.emit('error', error);
      })
      .on('ready', () => {
        console.log('🚀 File watcher is ready');
        this.emit('ready');
      });
  }

  /**
   * Handle individual file change events
   */
  async handleFileChange(changeType, filePath) {
    try {
      // Filter out irrelevant files
      if (!this.isRelevantFile(filePath)) {
        return;
      }

      const changeEvent = {
        id: this.generateChangeId(),
        type: changeType,
        filePath: path.resolve(filePath),
        relativePath: path.relative(process.cwd(), filePath),
        timestamp: new Date().toISOString(),
        fileExtension: path.extname(filePath),
        directory: path.dirname(filePath)
      };

      // Add file content for change/add events
      if (['add', 'change'].includes(changeType)) {
        changeEvent.content = await this.readFileContent(filePath);
        changeEvent.fileSize = (await fs.promises.stat(filePath)).size;
      }

      // Add to change queue
      this.changeQueue.push(changeEvent);

      // Limit queue size
      if (this.changeQueue.length > this.config.maxBatchSize) {
        this.changeQueue = this.changeQueue.slice(-this.config.maxBatchSize);
      }

      console.log(`📝 File change detected: ${changeType} - ${changeEvent.relativePath}`);

      // Process changes (debounced)
      if (this.config.batchChanges) {
        this.debouncedProcessChanges();
      } else {
        await this.processChangeEvent(changeEvent);
      }
    } catch (error) {
      console.error(`❌ Failed to handle file change for ${filePath}:`, error);
      this.emit('error', error);
    }
  }

  /**
   * Process queued changes in batch
   */
  async processChangeQueue() {
    if (this.changeQueue.length === 0) return;

    const changes = [...this.changeQueue];
    this.changeQueue = [];

    console.log(`🔄 Processing ${changes.length} file changes...`);

    try {
      // Group changes by type and directory for efficient processing
      const groupedChanges = this.groupChanges(changes);

      // Emit batch change event
      this.emit('batch-changes', groupedChanges);

      // Process each group
      for (const [groupKey, groupChanges] of groupedChanges.entries()) {
        await this.processChangeGroup(groupKey, groupChanges);
      }

      console.log('✅ Batch change processing completed');
    } catch (error) {
      console.error('❌ Failed to process change queue:', error);
      this.emit('error', error);
    }
  }

  /**
   * Process individual change event
   */
  async processChangeEvent(changeEvent) {
    try {
      // Determine documentation impact
      const impact = await this.analyzeDocumentationImpact(changeEvent);

      // Emit change event with impact analysis
      this.emit('code-change', {
        ...changeEvent,
        impact
      });

      console.log(`📊 Change impact analyzed for ${changeEvent.relativePath}: ${impact.join(', ')}`);
    } catch (error) {
      console.error(`❌ Failed to process change event:`, error);
      this.emit('error', error);
    }
  }

  /**
   * Group changes for efficient batch processing
   */
  groupChanges(changes) {
    const groups = new Map();

    for (const change of changes) {
      // Group by directory and file type
      const groupKey = `${path.dirname(change.relativePath)}_${change.fileExtension}`;

      if (!groups.has(groupKey)) {
        groups.set(groupKey, []);
      }

      groups.get(groupKey).push(change);
    }

    return groups;
  }

  /**
   * Process a group of related changes
   */
  async processChangeGroup(groupKey, changes) {
    try {
      console.log(`🔄 Processing change group: ${groupKey} (${changes.length} changes)`);

      // Analyze collective impact
      const collectiveImpact = await this.analyzeCollectiveImpact(changes);

      // Emit group change event
      this.emit('group-changes', {
        groupKey,
        changes,
        impact: collectiveImpact
      });

    } catch (error) {
      console.error(`❌ Failed to process change group ${groupKey}:`, error);
      throw error;
    }
  }

  /**
   * Analyze documentation impact of a change
   */
  async analyzeDocumentationImpact(changeEvent) {
    const impact = [];
    const { filePath, type, fileExtension, content } = changeEvent;

    // API documentation impact
    if (this.isApiFile(filePath) || this.containsApiCode(content)) {
      impact.push('api-documentation');
    }

    // Architecture documentation impact
    if (this.isArchitectureFile(filePath) || this.containsArchitecturalCode(content)) {
      impact.push('architecture-documentation');
    }

    // Algorithm documentation impact (AI trading specific)
    if (this.isAlgorithmFile(filePath) || this.containsAlgorithmCode(content)) {
      impact.push('algorithm-documentation');
    }

    // User guide impact
    if (this.isUserFacingFile(filePath) || this.containsUserFacingCode(content)) {
      impact.push('user-guide-documentation');
    }

    // Mermaid diagram impact
    if (impact.length > 0) {
      impact.push('mermaid-diagram');
    }

    return impact;
  }

  /**
   * Analyze collective impact of multiple changes
   */
  async analyzeCollectiveImpact(changes) {
    const allImpacts = new Set();

    for (const change of changes) {
      const impact = await this.analyzeDocumentationImpact(change);
      impact.forEach(i => allImpacts.add(i));
    }

    return Array.from(allImpacts);
  }

  /**
   * File type analysis methods
   */
  isRelevantFile(filePath) {
    const ext = path.extname(filePath);
    const relevantExtensions = ['.js', '.ts', '.jsx', '.tsx', '.py', '.java', '.cpp', '.h', '.md'];

    return relevantExtensions.includes(ext) && !this.isIgnoredFile(filePath);
  }

  isIgnoredFile(filePath) {
    const ignoredPatterns = [
      /node_modules/,
      /\.git/,
      /dist/,
      /build/,
      /coverage/,
      /\.swarm/,
      /\.cache/
    ];

    return ignoredPatterns.some(pattern => pattern.test(filePath));
  }

  isApiFile(filePath) {
    const apiIndicators = ['route', 'api', 'endpoint', 'controller', 'service'];
    return apiIndicators.some(indicator => filePath.toLowerCase().includes(indicator));
  }

  isArchitectureFile(filePath) {
    const archIndicators = ['src/', 'lib/', 'module', 'component', 'service', 'util'];
    return archIndicators.some(indicator => filePath.toLowerCase().includes(indicator));
  }

  isAlgorithmFile(filePath) {
    const algoIndicators = ['strategy', 'algorithm', 'indicator', 'trading', 'signal', 'backtest'];
    return algoIndicators.some(indicator => filePath.toLowerCase().includes(indicator));
  }

  isUserFacingFile(filePath) {
    const userIndicators = ['example', 'tutorial', 'guide', 'demo', 'sample'];
    return userIndicators.some(indicator => filePath.toLowerCase().includes(indicator));
  }

  /**
   * Content analysis methods
   */
  containsApiCode(content) {
    if (!content) return false;
    const apiPatterns = [/app\.(get|post|put|delete)/, /router\./, /express/, /@route/i, /endpoint/i];
    return apiPatterns.some(pattern => pattern.test(content));
  }

  containsArchitecturalCode(content) {
    if (!content) return false;
    const archPatterns = [/class\s+\w+/, /interface\s+\w+/, /module\.exports/, /import.*from/, /extends/];
    return archPatterns.some(pattern => pattern.test(content));
  }

  containsAlgorithmCode(content) {
    if (!content) return false;
    const algoPatterns = [/strategy/i, /algorithm/i, /calculate/i, /indicator/i, /signal/i, /backtest/i];
    return algoPatterns.some(pattern => pattern.test(content));
  }

  containsUserFacingCode(content) {
    if (!content) return false;
    const userPatterns = [/example/i, /tutorial/i, /demo/i, /how to/i, /getting started/i];
    return userPatterns.some(pattern => pattern.test(content));
  }

  /**
   * Utility methods
   */
  async readFileContent(filePath) {
    try {
      const stats = await fs.promises.stat(filePath);
      if (stats.size > 1024 * 1024) { // Skip files larger than 1MB
        return null;
      }
      return await fs.promises.readFile(filePath, 'utf8');
    } catch (error) {
      console.warn(`Failed to read file content: ${filePath}`, error.message);
      return null;
    }
  }

  generateChangeId() {
    return `change_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get monitoring statistics
   */
  getStats() {
    return {
      isMonitoring: this.isMonitoring,
      queueSize: this.changeQueue.length,
      watchPaths: this.config.watchPaths,
      ignorePaths: this.config.ignorePaths
    };
  }
}

module.exports = ChangeMonitor;