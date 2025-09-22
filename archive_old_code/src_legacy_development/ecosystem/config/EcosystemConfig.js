/**
 * EcosystemConfig - Centralized configuration management for the collaborative ecosystem
 * Manages settings for all agents, integrations, and coordination systems
 */

const fs = require('fs').promises;
const path = require('path');

class EcosystemConfig {
  constructor(configPath = null) {
    this.configPath = configPath || path.join(process.cwd(), '.swarm', 'ecosystem-config.json');
    this.config = null;
    this.defaultConfig = this.getDefaultConfig();
    this.watchers = new Map();
  }

  /**
   * Get default ecosystem configuration
   */
  getDefaultConfig() {
    return {
      version: '1.0.0',
      ecosystem: {
        name: 'collaborative-docs-ecosystem',
        description: 'Collaborative documentation ecosystem with specialized agents',
        autoStart: true,
        maxConcurrentAgents: 8,
        coordinationMode: 'adaptive'
      },

      // Agent configurations
      agents: {
        'api-agent': {
          type: 'api-documenter',
          enabled: true,
          priority: 'high',
          patterns: ['**/routes/**', '**/api/**', '**/controllers/**'],
          capabilities: ['openapi-generation', 'endpoint-documentation'],
          config: {
            outputFormat: 'openapi',
            includeExamples: true,
            validateSchemas: true
          }
        },
        'architecture-agent': {
          type: 'architecture-documenter',
          enabled: true,
          priority: 'high',
          patterns: ['**/src/**', '**/lib/**', '**/modules/**'],
          capabilities: ['system-diagrams', 'component-mapping'],
          config: {
            diagramTypes: ['component', 'system', 'deployment'],
            includeDataFlow: true,
            maxComplexity: 50
          }
        },
        'algorithm-agent': {
          type: 'algorithm-documenter',
          enabled: true,
          priority: 'medium',
          patterns: ['**/strategies/**', '**/algorithms/**', '**/indicators/**'],
          capabilities: ['algorithm-analysis', 'flow-diagrams'],
          config: {
            includeComplexity: true,
            generateFlowcharts: true,
            analyzePerformance: true
          }
        },
        'user-guide-agent': {
          type: 'user-guide-documenter',
          enabled: true,
          priority: 'medium',
          patterns: ['**/examples/**', '**/tutorials/**', '**/guides/**'],
          capabilities: ['user-documentation', 'tutorial-generation'],
          config: {
            includeCodeExamples: true,
            generateTutorials: true,
            validateExamples: true
          }
        }
      },

      // Change monitoring configuration
      monitoring: {
        enabled: true,
        watchPaths: [
          'src/**',
          'lib/**',
          'api/**',
          'routes/**',
          'strategies/**',
          'algorithms/**',
          'indicators/**'
        ],
        ignorePaths: [
          'node_modules/**',
          '.git/**',
          'dist/**',
          'build/**',
          'coverage/**',
          '.swarm/**'
        ],
        debounceDelay: 1000,
        batchChanges: true,
        maxBatchSize: 10
      },

      // Context detection settings
      contextDetection: {
        enabled: true,
        cacheTimeout: 300000, // 5 minutes
        maxFileAnalysis: 100,
        projectTypeDetection: true,
        aiTradingDetection: {
          enabled: true,
          confidenceThreshold: 50,
          keywordAnalysis: true,
          dependencyAnalysis: true
        }
      },

      // Mermaid integration settings
      mermaid: {
        enabled: true,
        outputDir: 'docs/diagrams',
        autoGenerate: true,
        generatePreview: false,
        maxDiagramComplexity: 50,
        diagramTypes: {
          architecture: true,
          algorithm: true,
          api: true,
          userJourney: true,
          sequence: true
        },
        styling: {
          aiTrading: true,
          customThemes: false
        }
      },

      // Hook management configuration
      hooks: {
        enabled: true,
        timeout: 5000,
        retryAttempts: 3,
        retryDelay: 1000,
        enableBatching: true,
        batchSize: 10,
        batchTimeout: 2000,
        types: {
          'pre-task': { enabled: true, critical: true },
          'post-task': { enabled: true, critical: true },
          'post-edit': { enabled: true, critical: false },
          'notify': { enabled: true, critical: false },
          'session-restore': { enabled: true, critical: false },
          'session-end': { enabled: true, critical: true }
        }
      },

      // MCP system integration
      mcp: {
        enabled: true,
        servers: {
          'claude-flow': {
            command: 'npx claude-flow@alpha mcp start',
            required: true,
            features: ['swarm', 'agent-spawn', 'task-orchestrate', 'hooks']
          },
          'ruv-swarm': {
            command: 'npx ruv-swarm mcp start',
            required: false,
            features: ['enhanced-coordination', 'neural', 'daa']
          },
          'flow-nexus': {
            command: 'npx flow-nexus@latest mcp start',
            required: false,
            features: ['cloud-execution', 'templates', 'storage']
          }
        },
        topology: 'mesh',
        maxAgents: 8,
        strategy: 'adaptive'
      },

      // Memory and coordination settings
      memory: {
        enabled: true,
        storePath: '.swarm/memory.db',
        namespaces: {
          'project-context': { ttl: 3600000 }, // 1 hour
          'agent-state': { ttl: 1800000 },     // 30 minutes
          'file-changes': { ttl: 600000 },     // 10 minutes
          'diagrams': { ttl: 7200000 }         // 2 hours
        },
        cleanup: {
          interval: 300000, // 5 minutes
          maxSize: 100      // MB
        }
      },

      // Project-specific configurations
      projects: {
        'ai-trading': {
          enabled: true,
          agents: ['algorithm-agent', 'api-agent', 'architecture-agent'],
          specialFeatures: {
            tradingAnalysis: true,
            performanceMetrics: true,
            backtestingDocs: true,
            riskAnalysis: true
          },
          monitoring: {
            extraPaths: ['backtests/**', 'data/**', 'models/**'],
            tradingKeywords: ['strategy', 'indicator', 'signal', 'portfolio']
          }
        },
        'web-api': {
          enabled: true,
          agents: ['api-agent', 'architecture-agent', 'user-guide-agent'],
          specialFeatures: {
            openApiGeneration: true,
            endpointTesting: true,
            securityDocs: true
          }
        },
        'frontend': {
          enabled: true,
          agents: ['architecture-agent', 'user-guide-agent'],
          specialFeatures: {
            componentDocs: true,
            storybook: true,
            accessibilityDocs: true
          }
        }
      },

      // Performance and optimization
      performance: {
        maxConcurrentTasks: 5,
        taskTimeout: 30000,
        memoryLimit: 512, // MB
        enableProfiling: false,
        optimizations: {
          fileAnalysisCache: true,
          diagramCache: true,
          contextCache: true
        }
      },

      // Logging and debugging
      logging: {
        level: 'info', // error, warn, info, debug
        enableFileLogging: false,
        logPath: '.swarm/logs',
        maxLogSize: 10, // MB
        maxLogFiles: 5,
        enableMetrics: true
      },

      // Security settings
      security: {
        enableSandboxing: false,
        allowFileSystem: true,
        allowNetworking: true,
        trustedPaths: ['src/**', 'docs/**'],
        blockedPaths: ['node_modules/**', '.git/**']
      }
    };
  }

  /**
   * Load configuration from file or use defaults
   */
  async loadConfig() {
    try {
      if (await this.fileExists(this.configPath)) {
        const configContent = await fs.readFile(this.configPath, 'utf8');
        const loadedConfig = JSON.parse(configContent);

        // Merge with defaults
        this.config = this.deepMerge(this.defaultConfig, loadedConfig);

        console.log(`📋 Configuration loaded from ${this.configPath}`);
      } else {
        // Use default configuration
        this.config = { ...this.defaultConfig };

        // Save default configuration
        await this.saveConfig();

        console.log('📋 Using default configuration (saved to file)');
      }

      // Validate configuration
      this.validateConfig();

      return this.config;
    } catch (error) {
      console.error('❌ Failed to load configuration:', error);
      throw error;
    }
  }

  /**
   * Save current configuration to file
   */
  async saveConfig() {
    try {
      // Ensure directory exists
      const configDir = path.dirname(this.configPath);
      await fs.mkdir(configDir, { recursive: true });

      // Save configuration
      await fs.writeFile(
        this.configPath,
        JSON.stringify(this.config, null, 2),
        'utf8'
      );

      console.log(`💾 Configuration saved to ${this.configPath}`);
    } catch (error) {
      console.error('❌ Failed to save configuration:', error);
      throw error;
    }
  }

  /**
   * Update configuration values
   */
  async updateConfig(updates) {
    try {
      this.config = this.deepMerge(this.config, updates);
      await this.saveConfig();

      // Notify watchers
      this.notifyWatchers('config-updated', updates);

      console.log('📝 Configuration updated successfully');
    } catch (error) {
      console.error('❌ Failed to update configuration:', error);
      throw error;
    }
  }

  /**
   * Get configuration value by path
   */
  get(path, defaultValue = undefined) {
    return this.getNestedValue(this.config, path, defaultValue);
  }

  /**
   * Set configuration value by path
   */
  async set(path, value) {
    this.setNestedValue(this.config, path, value);
    await this.saveConfig();

    this.notifyWatchers('config-changed', { path, value });
  }

  /**
   * Get agent configuration
   */
  getAgentConfig(agentId) {
    return this.config.agents[agentId] || null;
  }

  /**
   * Get enabled agents
   */
  getEnabledAgents() {
    return Object.entries(this.config.agents)
      .filter(([id, config]) => config.enabled)
      .map(([id, config]) => ({ id, ...config }));
  }

  /**
   * Get project-specific configuration
   */
  getProjectConfig(projectType) {
    return this.config.projects[projectType] || {};
  }

  /**
   * Validate configuration
   */
  validateConfig() {
    const errors = [];

    // Validate required fields
    if (!this.config.ecosystem.name) {
      errors.push('ecosystem.name is required');
    }

    // Validate agent configurations
    Object.entries(this.config.agents).forEach(([agentId, agentConfig]) => {
      if (!agentConfig.type) {
        errors.push(`agents.${agentId}.type is required`);
      }
      if (!Array.isArray(agentConfig.patterns)) {
        errors.push(`agents.${agentId}.patterns must be an array`);
      }
    });

    // Validate monitoring paths
    if (!Array.isArray(this.config.monitoring.watchPaths)) {
      errors.push('monitoring.watchPaths must be an array');
    }

    // Validate MCP configuration
    if (this.config.mcp.enabled) {
      if (!this.config.mcp.servers['claude-flow']) {
        errors.push('claude-flow MCP server configuration is required');
      }
    }

    if (errors.length > 0) {
      throw new Error(`Configuration validation failed:\n${errors.join('\n')}`);
    }
  }

  /**
   * Watch for configuration changes
   */
  watchConfig(callback) {
    const watcherId = `watcher_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    this.watchers.set(watcherId, callback);

    return () => {
      this.watchers.delete(watcherId);
    };
  }

  /**
   * Notify configuration watchers
   */
  notifyWatchers(event, data) {
    this.watchers.forEach(callback => {
      try {
        callback(event, data);
      } catch (error) {
        console.warn('Configuration watcher error:', error);
      }
    });
  }

  /**
   * Utility methods
   */
  async fileExists(filePath) {
    try {
      await fs.access(filePath);
      return true;
    } catch {
      return false;
    }
  }

  deepMerge(target, source) {
    const result = { ...target };

    Object.keys(source).forEach(key => {
      if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
        result[key] = this.deepMerge(result[key] || {}, source[key]);
      } else {
        result[key] = source[key];
      }
    });

    return result;
  }

  getNestedValue(obj, path, defaultValue) {
    const keys = path.split('.');
    let current = obj;

    for (const key of keys) {
      if (current && typeof current === 'object' && key in current) {
        current = current[key];
      } else {
        return defaultValue;
      }
    }

    return current;
  }

  setNestedValue(obj, path, value) {
    const keys = path.split('.');
    const lastKey = keys.pop();
    let current = obj;

    for (const key of keys) {
      if (!(key in current) || typeof current[key] !== 'object') {
        current[key] = {};
      }
      current = current[key];
    }

    current[lastKey] = value;
  }

  /**
   * Export configuration for external use
   */
  exportConfig(format = 'json') {
    switch (format) {
      case 'json':
        return JSON.stringify(this.config, null, 2);
      case 'yaml':
        // Would require yaml library
        throw new Error('YAML export not implemented');
      default:
        throw new Error(`Unsupported export format: ${format}`);
    }
  }

  /**
   * Reset to default configuration
   */
  async resetToDefaults() {
    this.config = { ...this.defaultConfig };
    await this.saveConfig();

    this.notifyWatchers('config-reset', this.config);
    console.log('🔄 Configuration reset to defaults');
  }

  /**
   * Get configuration statistics
   */
  getStats() {
    const enabledAgents = this.getEnabledAgents().length;
    const totalAgents = Object.keys(this.config.agents).length;
    const enabledFeatures = Object.values(this.config.mcp.servers)
      .filter(server => server.required || this.config.mcp.enabled).length;

    return {
      configVersion: this.config.version,
      enabledAgents,
      totalAgents,
      enabledFeatures,
      monitoringPaths: this.config.monitoring.watchPaths.length,
      projectTypes: Object.keys(this.config.projects).length,
      watchers: this.watchers.size
    };
  }
}

module.exports = EcosystemConfig;