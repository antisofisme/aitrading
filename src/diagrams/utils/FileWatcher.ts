import { watch, FSWatcher } from 'chokidar';
import { DiagramEngine } from '../core/DiagramEngine';
import { MCPIntegration } from '../mcp/MCPIntegration';
import {
  DiagramType,
  DiagramOptions,
  FileWatcherConfig,
  DiagramEvent,
  HookConfiguration
} from '../core/types';

export class FileWatcher {
  private watchers: Map<string, FSWatcher> = new Map();
  private configs: Map<string, FileWatcherConfig> = new Map();
  private engine: DiagramEngine;
  private mcpIntegration: MCPIntegration;
  private hooks: HookConfiguration = {};
  private debounceTimers: Map<string, NodeJS.Timeout> = new Map();

  constructor(engine: DiagramEngine, mcpIntegration: MCPIntegration) {
    this.engine = engine;
    this.mcpIntegration = mcpIntegration;
  }

  /**
   * Watch a file for changes and auto-regenerate diagrams
   */
  async watchFile(
    filePath: string,
    diagramType: DiagramType,
    options?: DiagramOptions
  ): Promise<void> {
    const config: FileWatcherConfig = {
      filePath,
      diagramType,
      options,
      autoRegenerate: true,
      debounceMs: 1000
    };

    this.configs.set(filePath, config);

    // Create file watcher
    const watcher = watch(filePath, {
      persistent: true,
      ignoreInitial: true
    });

    // Set up event handlers
    watcher.on('change', () => this.handleFileChange(filePath));
    watcher.on('unlink', () => this.handleFileDelete(filePath));
    watcher.on('error', (error) => this.handleWatchError(filePath, error));

    this.watchers.set(filePath, watcher);

    console.log(`File watcher started for: ${filePath}`);

    // Register with MCP integration
    await this.mcpIntegration.registerFileWatcher(filePath, diagramType, options);
  }

  /**
   * Watch a directory for file changes
   */
  async watchDirectory(
    directoryPath: string,
    filePattern: string = '**/*',
    diagramType: DiagramType,
    options?: DiagramOptions
  ): Promise<void> {
    const watchPattern = `${directoryPath}/${filePattern}`;

    const watcher = watch(watchPattern, {
      persistent: true,
      ignoreInitial: true,
      ignored: [
        '**/node_modules/**',
        '**/.git/**',
        '**/dist/**',
        '**/build/**'
      ]
    });

    watcher.on('change', (filePath) => this.handleFileChange(filePath));
    watcher.on('add', (filePath) => this.handleFileAdd(filePath, diagramType, options));
    watcher.on('unlink', (filePath) => this.handleFileDelete(filePath));

    this.watchers.set(directoryPath, watcher);

    console.log(`Directory watcher started for: ${directoryPath}`);
  }

  /**
   * Handle file change events
   */
  private async handleFileChange(filePath: string): Promise<void> {
    const config = this.configs.get(filePath);
    if (!config) return;

    // Debounce rapid changes
    this.debounceAction(filePath, async () => {
      try {
        await this.triggerPreChangeHook(filePath);

        if (config.autoRegenerate) {
          await this.regenerateDiagram(filePath, config);
        }

        await this.triggerPostChangeHook(filePath);

      } catch (error) {
        await this.triggerErrorHook(filePath, error);
        console.error(`Error handling file change for ${filePath}:`, error);
      }
    }, config.debounceMs || 1000);
  }

  /**
   * Handle file addition
   */
  private async handleFileAdd(
    filePath: string,
    diagramType: DiagramType,
    options?: DiagramOptions
  ): Promise<void> {
    // Automatically start watching new files if they match criteria
    if (this.shouldWatchFile(filePath)) {
      await this.watchFile(filePath, diagramType, options);
    }
  }

  /**
   * Handle file deletion
   */
  private async handleFileDelete(filePath: string): Promise<void> {
    // Stop watching deleted files
    await this.stopWatching(filePath);

    // Clean up related diagram outputs
    await this.cleanupDiagramOutputs(filePath);
  }

  /**
   * Handle watch errors
   */
  private async handleWatchError(filePath: string, error: Error): Promise<void> {
    console.error(`File watcher error for ${filePath}:`, error);
    await this.triggerErrorHook(filePath, error);

    // Attempt to restart the watcher
    setTimeout(() => {
      const config = this.configs.get(filePath);
      if (config) {
        this.restartWatcher(filePath, config);
      }
    }, 5000);
  }

  /**
   * Regenerate diagram for changed file
   */
  private async regenerateDiagram(
    filePath: string,
    config: FileWatcherConfig
  ): Promise<void> {
    try {
      // Read and analyze the changed file
      const analysisData = await this.analyzeChangedFile(filePath);

      // Generate new diagram
      const result = await this.engine.generateDiagram(
        analysisData,
        config.diagramType,
        config.options
      );

      if (result.success) {
        console.log(`Diagram regenerated for: ${filePath}`);
        await this.notifyDiagramUpdate(filePath, result);
      } else {
        console.error(`Diagram regeneration failed for ${filePath}:`, result.error);
      }

    } catch (error) {
      console.error(`Error regenerating diagram for ${filePath}:`, error);
    }
  }

  /**
   * Analyze changed file content
   */
  private async analyzeChangedFile(filePath: string): Promise<any> {
    // This would integrate with your analysis engine
    // For now, return a mock analysis data structure
    return {
      id: `file_${Date.now()}`,
      contentType: this.inferContentType(filePath),
      structure: [`File: ${filePath}`, 'Modified content'],
      complexity: 0.5,
      timestamp: new Date().toISOString(),
      metadata: {
        filePath,
        lastModified: new Date().toISOString()
      }
    };
  }

  /**
   * Infer content type from file path
   */
  private inferContentType(filePath: string): string {
    const extension = filePath.split('.').pop()?.toLowerCase();

    switch (extension) {
      case 'js':
      case 'ts':
      case 'jsx':
      case 'tsx':
        return 'code-architecture';
      case 'sql':
        return 'database';
      case 'md':
        return 'documentation';
      case 'json':
        return 'configuration';
      case 'yml':
      case 'yaml':
        return 'configuration';
      default:
        return 'general';
    }
  }

  /**
   * Debounce rapid file changes
   */
  private debounceAction(
    key: string,
    action: () => Promise<void>,
    delay: number
  ): void {
    // Clear existing timer
    const existingTimer = this.debounceTimers.get(key);
    if (existingTimer) {
      clearTimeout(existingTimer);
    }

    // Set new timer
    const timer = setTimeout(async () => {
      try {
        await action();
      } finally {
        this.debounceTimers.delete(key);
      }
    }, delay);

    this.debounceTimers.set(key, timer);
  }

  /**
   * Check if file should be watched
   */
  private shouldWatchFile(filePath: string): boolean {
    // Skip binary files, temporary files, etc.
    const skipPatterns = [
      /\.log$/,
      /\.tmp$/,
      /\.swp$/,
      /~$/,
      /node_modules/,
      /\.git/,
      /dist/,
      /build/
    ];

    return !skipPatterns.some(pattern => pattern.test(filePath));
  }

  /**
   * Stop watching a specific file
   */
  async stopWatching(filePath: string): Promise<void> {
    const watcher = this.watchers.get(filePath);
    if (watcher) {
      await watcher.close();
      this.watchers.delete(filePath);
    }

    this.configs.delete(filePath);

    // Clear any pending debounced actions
    const timer = this.debounceTimers.get(filePath);
    if (timer) {
      clearTimeout(timer);
      this.debounceTimers.delete(filePath);
    }

    console.log(`Stopped watching: ${filePath}`);
  }

  /**
   * Stop all watchers
   */
  async stopAll(): Promise<void> {
    const promises = Array.from(this.watchers.keys()).map(filePath =>
      this.stopWatching(filePath)
    );

    await Promise.all(promises);
    console.log('All file watchers stopped');
  }

  /**
   * Restart a watcher after error
   */
  private async restartWatcher(
    filePath: string,
    config: FileWatcherConfig
  ): Promise<void> {
    console.log(`Restarting watcher for: ${filePath}`);

    try {
      await this.stopWatching(filePath);
      await this.watchFile(filePath, config.diagramType, config.options);
    } catch (error) {
      console.error(`Failed to restart watcher for ${filePath}:`, error);
    }
  }

  /**
   * Clean up diagram outputs for deleted file
   */
  private async cleanupDiagramOutputs(filePath: string): Promise<void> {
    // This would clean up any generated diagram files
    // related to the deleted source file
    console.log(`Cleaning up diagram outputs for: ${filePath}`);
  }

  /**
   * Set up event hooks
   */
  setHooks(hooks: HookConfiguration): void {
    this.hooks = { ...hooks };
  }

  /**
   * Trigger pre-change hook
   */
  private async triggerPreChangeHook(filePath: string): Promise<void> {
    if (this.hooks.preGeneration) {
      const event: DiagramEvent = {
        type: 'file-change',
        diagramType: 'unknown' as DiagramType,
        data: { filePath },
        timestamp: new Date().toISOString()
      };

      await this.hooks.preGeneration(event);
    }
  }

  /**
   * Trigger post-change hook
   */
  private async triggerPostChangeHook(filePath: string): Promise<void> {
    if (this.hooks.onFileChange) {
      const event: DiagramEvent = {
        type: 'file-change',
        diagramType: 'unknown' as DiagramType,
        data: { filePath },
        timestamp: new Date().toISOString()
      };

      await this.hooks.onFileChange(event);
    }
  }

  /**
   * Trigger error hook
   */
  private async triggerErrorHook(filePath: string, error: Error): Promise<void> {
    if (this.hooks.onError) {
      const event: DiagramEvent = {
        type: 'generation-error',
        diagramType: 'unknown' as DiagramType,
        data: { filePath, error: error.message },
        timestamp: new Date().toISOString()
      };

      await this.hooks.onError(event);
    }
  }

  /**
   * Notify about diagram update
   */
  private async notifyDiagramUpdate(filePath: string, result: any): Promise<void> {
    // Notify MCP integration about the update
    await this.mcpIntegration.handleFileChange(filePath);

    console.log(`Diagram updated for ${filePath}:`, result.metadata?.generatedAt);
  }

  /**
   * Get current watch status
   */
  getWatchStatus(): {
    watchedFiles: string[];
    activeWatchers: number;
    totalConfigs: number;
  } {
    return {
      watchedFiles: Array.from(this.configs.keys()),
      activeWatchers: this.watchers.size,
      totalConfigs: this.configs.size
    };
  }
}