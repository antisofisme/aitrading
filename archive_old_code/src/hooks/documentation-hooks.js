const { SystemArchitectureDiagrammer } = require('../diagrams/system-architecture');
const { CodeAnalyzer } = require('../analysis/code-analyzer');
const { FileWatcher } = require('../workflow/file-watcher');
const path = require('path');
const fs = require('fs').promises;
const crypto = require('crypto');

class DocumentationHooks {
  constructor(options = {}) {
    this.projectRoot = options.projectRoot || process.cwd();
    this.enabled = options.enabled !== false;
    this.debounceMs = options.debounceMs || 2000;
    this.cachePath = path.join(this.projectRoot, '.claude-flow/cache/diagrams.json');
    
    this.diagrammer = new SystemArchitectureDiagrammer({ projectRoot: this.projectRoot });
    this.analyzer = new CodeAnalyzer({ projectRoot: this.projectRoot });
    this.watcher = new FileWatcher({ projectRoot: this.projectRoot });
    
    this.pendingUpdates = new Set();
    this.lastUpdate = 0;
    this.updateTimer = null;
    
    this._setupHooks();
  }

  _setupHooks() {
    if (!this.enabled) return;
    
    // File change hooks
    this.watcher.on('change', (filePath, changeType) => {
      this._scheduleUpdate(filePath, changeType);
    });
    
    // Claude Flow integration hooks
    this._setupClaudeFlowHooks();
    
    // Git hooks integration
    this._setupGitHooks();
  }

  async _setupClaudeFlowHooks() {
    try {
      const hooksPath = path.join(this.projectRoot, '.claude-flow/hooks');
      await fs.mkdir(hooksPath, { recursive: true });
      
      // Pre-task hook
      await this._createHookScript(path.join(hooksPath, 'pre-task.js'), this._preTaskHook());
      
      // Post-edit hook
      await this._createHookScript(path.join(hooksPath, 'post-edit.js'), this._postEditHook());
      
      // Post-task hook
      await this._createHookScript(path.join(hooksPath, 'post-task.js'), this._postTaskHook());
      
      // Session end hook
      await this._createHookScript(path.join(hooksPath, 'session-end.js'), this._sessionEndHook());
      
    } catch (error) {
      console.warn('Failed to setup Claude Flow hooks:', error.message);
    }
  }

  async _setupGitHooks() {
    try {
      const gitHooksPath = path.join(this.projectRoot, '.git/hooks');
      
      // Pre-commit hook
      const preCommitHook = `#!/bin/sh
# Auto-update documentation diagrams
node -e "require('${__filename.replace(/\\/g, '/')}').updateDiagrams().catch(console.error)"
`;
      
      await fs.writeFile(path.join(gitHooksPath, 'pre-commit'), preCommitHook, { mode: 0o755 });
      
      // Post-merge hook
      const postMergeHook = `#!/bin/sh
# Regenerate diagrams after merge
node -e "require('${__filename.replace(/\\/g, '/')}').fullUpdate().catch(console.error)"
`;
      
      await fs.writeFile(path.join(gitHooksPath, 'post-merge'), postMergeHook, { mode: 0o755 });
      
    } catch (error) {
      console.warn('Failed to setup Git hooks:', error.message);
    }
  }

  _scheduleUpdate(filePath, changeType) {
    if (!this._shouldProcessFile(filePath)) return;
    
    this.pendingUpdates.add({ filePath, changeType, timestamp: Date.now() });
    
    // Debounce updates
    if (this.updateTimer) {
      clearTimeout(this.updateTimer);
    }
    
    this.updateTimer = setTimeout(() => {
      this._processUpdates().catch(console.error);
    }, this.debounceMs);
  }

  async _processUpdates() {
    if (this.pendingUpdates.size === 0) return;
    
    const updates = Array.from(this.pendingUpdates);
    this.pendingUpdates.clear();
    
    const significantChanges = updates.filter(update => 
      this._isSignificantChange(update.filePath, update.changeType)
    );
    
    if (significantChanges.length === 0) return;
    
    console.log(`📊 Processing ${significantChanges.length} significant changes for documentation update...`);
    
    try {
      await this._updateDiagrams(significantChanges);
      await this._updateCache(significantChanges);
      
      console.log('✅ Documentation diagrams updated successfully');
    } catch (error) {
      console.error('❌ Failed to update documentation:', error.message);
    }
  }

  async _updateDiagrams(changes) {
    const structuralChanges = changes.filter(change => 
      this._isStructuralChange(change.filePath)
    );
    
    const dataFlowChanges = changes.filter(change => 
      this._isDataFlowChange(change.filePath)
    );
    
    const updates = [];
    
    // Update system overview if structural changes
    if (structuralChanges.length > 0) {
      updates.push(this.diagrammer.generateSystemOverview());
      updates.push(this.diagrammer.generateComponentDiagram());
    }
    
    // Update data flow if trading logic changes
    if (dataFlowChanges.length > 0) {
      updates.push(this.diagrammer.generateDataFlow());
      updates.push(this.diagrammer.generateSequenceDiagram());
    }
    
    // Always update if major changes
    if (changes.length > 5) {
      updates.push(
        this.diagrammer.generateSystemOverview(),
        this.diagrammer.generateDataFlow(),
        this.diagrammer.generateComponentDiagram(),
        this.diagrammer.generateSequenceDiagram()
      );
    }
    
    if (updates.length > 0) {
      await Promise.all(updates);
    }
  }

  async _updateCache(changes) {
    const cache = await this._loadCache();
    
    cache.lastUpdate = Date.now();
    cache.totalUpdates = (cache.totalUpdates || 0) + 1;
    cache.recentChanges = [
      ...changes.map(c => ({
        file: c.filePath,
        type: c.changeType,
        timestamp: c.timestamp
      })),
      ...(cache.recentChanges || []).slice(0, 50)
    ].slice(0, 100);
    
    // Calculate file hash for change detection
    for (const change of changes) {
      try {
        const content = await fs.readFile(change.filePath, 'utf8');
        cache.fileHashes = cache.fileHashes || {};
        cache.fileHashes[change.filePath] = crypto
          .createHash('md5')
          .update(content)
          .digest('hex');
      } catch (error) {
        // File might be deleted
        if (cache.fileHashes) {
          delete cache.fileHashes[change.filePath];
        }
      }
    }
    
    await this._saveCache(cache);
  }

  async _loadCache() {
    try {
      const content = await fs.readFile(this.cachePath, 'utf8');
      return JSON.parse(content);
    } catch (error) {
      return {
        lastUpdate: 0,
        totalUpdates: 0,
        recentChanges: [],
        fileHashes: {}
      };
    }
  }

  async _saveCache(cache) {
    await fs.mkdir(path.dirname(this.cachePath), { recursive: true });
    await fs.writeFile(this.cachePath, JSON.stringify(cache, null, 2), 'utf8');
  }

  _shouldProcessFile(filePath) {
    const ext = path.extname(filePath).toLowerCase();
    const processableExts = ['.js', '.ts', '.jsx', '.tsx', '.py', '.java', '.go', '.rs'];
    
    if (!processableExts.includes(ext)) return false;
    
    // Skip node_modules, build directories, etc.
    const skipPatterns = [
      'node_modules',
      'dist',
      'build',
      '.git',
      '.claude-flow/cache',
      'docs/diagrams'
    ];
    
    return !skipPatterns.some(pattern => filePath.includes(pattern));
  }

  _isSignificantChange(filePath, changeType) {
    if (changeType === 'deleted') return true;
    if (changeType === 'added') return true;
    
    // For modifications, check if it's a structural change
    return this._isStructuralChange(filePath) || this._isDataFlowChange(filePath);
  }

  _isStructuralChange(filePath) {
    const fileName = path.basename(filePath).toLowerCase();
    const structuralPatterns = [
      'index',
      'main',
      'app',
      'server',
      'router',
      'controller',
      'service',
      'model',
      'config'
    ];
    
    return structuralPatterns.some(pattern => fileName.includes(pattern));
  }

  _isDataFlowChange(filePath) {
    const fileName = path.basename(filePath).toLowerCase();
    const dataFlowPatterns = [
      'trading',
      'market',
      'order',
      'data',
      'stream',
      'feed',
      'signal',
      'strategy',
      'algorithm'
    ];
    
    return dataFlowPatterns.some(pattern => fileName.includes(pattern));
  }

  async _createHookScript(filePath, content) {
    await fs.writeFile(filePath, content, { mode: 0o755 });
  }

  _preTaskHook() {
    return `#!/usr/bin/env node
// Auto-generated Claude Flow pre-task hook
const { DocumentationHooks } = require('${__filename.replace(/\\/g, '/')}');

async function main() {
  try {
    const hooks = new DocumentationHooks();
    console.log('📋 Pre-task: Documentation hooks initialized');
  } catch (error) {
    console.warn('Pre-task hook warning:', error.message);
  }
}

if (require.main === module) {
  main().catch(console.error);
}
`;
  }

  _postEditHook() {
    return `#!/usr/bin/env node
// Auto-generated Claude Flow post-edit hook
const { DocumentationHooks } = require('${__filename.replace(/\\/g, '/')}');

async function main() {
  const filePath = process.argv[2];
  if (!filePath) return;
  
  try {
    const hooks = new DocumentationHooks();
    hooks._scheduleUpdate(filePath, 'modified');
    console.log('📝 Post-edit: Scheduled documentation update for', filePath);
  } catch (error) {
    console.warn('Post-edit hook warning:', error.message);
  }
}

if (require.main === module) {
  main().catch(console.error);
}
`;
  }

  _postTaskHook() {
    return `#!/usr/bin/env node
// Auto-generated Claude Flow post-task hook
const { DocumentationHooks } = require('${__filename.replace(/\\/g, '/')}');

async function main() {
  try {
    const hooks = new DocumentationHooks();
    await hooks._processUpdates();
    console.log('✅ Post-task: Documentation updates completed');
  } catch (error) {
    console.warn('Post-task hook warning:', error.message);
  }
}

if (require.main === module) {
  main().catch(console.error);
}
`;
  }

  _sessionEndHook() {
    return `#!/usr/bin/env node
// Auto-generated Claude Flow session-end hook
const { DocumentationHooks } = require('${__filename.replace(/\\/g, '/')}');

async function main() {
  try {
    const hooks = new DocumentationHooks();
    await hooks.fullUpdate();
    console.log('🎯 Session-end: Full documentation update completed');
  } catch (error) {
    console.warn('Session-end hook warning:', error.message);
  }
}

if (require.main === module) {
  main().catch(console.error);
}
`;
  }

  // Public API methods
  async updateDiagrams() {
    console.log('📊 Starting diagram update...');
    await this._processUpdates();
  }

  async fullUpdate() {
    console.log('🔄 Starting full documentation update...');
    try {
      const results = await Promise.all([
        this.diagrammer.generateSystemOverview(),
        this.diagrammer.generateDataFlow(),
        this.diagrammer.generateComponentDiagram(),
        this.diagrammer.generateSequenceDiagram()
      ]);
      
      console.log('✅ Full update completed:', {
        systemOverview: results[0].path,
        dataFlow: results[1].path,
        components: results[2].path,
        sequence: results[3].path
      });
      
      return results;
    } catch (error) {
      console.error('❌ Full update failed:', error.message);
      throw error;
    }
  }

  async getStatus() {
    const cache = await this._loadCache();
    return {
      enabled: this.enabled,
      lastUpdate: new Date(cache.lastUpdate),
      totalUpdates: cache.totalUpdates,
      pendingUpdates: this.pendingUpdates.size,
      recentChanges: cache.recentChanges?.slice(0, 10) || []
    };
  }

  enable() {
    this.enabled = true;
    this._setupHooks();
  }

  disable() {
    this.enabled = false;
    if (this.updateTimer) {
      clearTimeout(this.updateTimer);
      this.updateTimer = null;
    }
  }
}

// Export for CLI usage
if (require.main === module) {
  const hooks = new DocumentationHooks();
  
  const command = process.argv[2];
  
  switch (command) {
    case 'update':
      hooks.updateDiagrams().catch(console.error);
      break;
    case 'full':
      hooks.fullUpdate().catch(console.error);
      break;
    case 'status':
      hooks.getStatus().then(console.log).catch(console.error);
      break;
    case 'enable':
      hooks.enable();
      console.log('✅ Documentation hooks enabled');
      break;
    case 'disable':
      hooks.disable();
      console.log('❌ Documentation hooks disabled');
      break;
    default:
      console.log('Usage: node documentation-hooks.js [update|full|status|enable|disable]');
  }
}

module.exports = { DocumentationHooks };
