/**
 * Configuration System for Mermaid.js Integration
 * Handles different output formats and system settings
 */

import fs from 'fs/promises';
import path from 'path';

export class MermaidConfig {
  constructor(configPath = './config/mermaid-config.json') {
    this.configPath = configPath;
    this.defaultConfig = {
      // Output Configuration
      output: {
        formats: ['mermaid', 'svg', 'png', 'pdf'],
        defaultFormat: 'mermaid',
        outputDirectory: './docs/diagrams',
        createSubdirectories: true,
        filenameTemplate: '{type}_{timestamp}',
        includeTimestamp: true
      },

      // Diagram Generation Settings
      generation: {
        autoGenerate: true,
        watchPaths: ['./src'],
        excludePaths: ['node_modules', '.git', 'dist', 'build'],
        filePatterns: ['**/*.{js,ts,jsx,tsx,py,java,cs}'],
        debounceDelay: 2000,
        maxFileSize: 1048576, // 1MB
        enableParallelProcessing: true
      },

      // Diagram Types Configuration
      diagramTypes: {
        enabled: ['flowchart', 'class', 'sequence', 'er'],
        flowchart: {
          direction: 'TD',
          nodeSpacing: 50,
          rankSpacing: 50,
          styling: {
            theme: 'default',
            customCSS: ''
          }
        },
        class: {
          showMethods: true,
          showProperties: true,
          showInheritance: true,
          showAssociations: true,
          maxMethodsPerClass: 10
        },
        sequence: {
          showActivations: true,
          showNotes: true,
          participantSpacing: 100,
          messageSpacing: 50
        },
        er: {
          showAttributes: true,
          showRelationships: true,
          entitySpacing: 150
        }
      },

      // Trading System Specific Settings
      trading: {
        enableTradingTemplates: true,
        autoDetectTradingComponents: true,
        tradingKeywords: [
          'trade', 'strategy', 'market', 'risk', 'portfolio',
          'order', 'signal', 'execution', 'backtest', 'performance'
        ],
        componentCategories: {
          strategy: ['strategy', 'signal', 'algorithm', 'indicator'],
          data: ['market', 'price', 'feed', 'ticker', 'ohlc', 'quote'],
          risk: ['risk', 'position', 'size', 'stop', 'limit', 'var'],
          execution: ['order', 'trade', 'execute', 'broker', 'fill'],
          portfolio: ['portfolio', 'asset', 'allocation', 'balance']
        },
        templates: {
          tradingPipeline: true,
          riskManagement: true,
          dataFlow: true,
          microservices: true,
          mlPipeline: true
        }
      },

      // Code Analysis Settings
      analysis: {
        enableDeepAnalysis: true,
        analyzeComments: true,
        extractDocstrings: true,
        followImports: true,
        maxDepth: 5,
        ignoreTestFiles: false,
        customParsers: {},
        complexity: {
          enableCalculation: true,
          maxComplexity: 100,
          warnThreshold: 50
        }
      },

      // Claude Flow Integration
      claudeFlow: {
        enabled: true,
        sessionId: '',
        memoryNamespace: 'mermaid-diagrams',
        enableHooks: true,
        hookTimeout: 30000,
        autoRegisterHooks: true,
        syncInterval: 5000
      },

      // MCP Server Settings
      mcpServer: {
        enabled: true,
        port: 3000,
        host: 'localhost',
        enableCORS: true,
        enableLogging: true,
        logLevel: 'info',
        timeout: 60000
      },

      // Performance Settings
      performance: {
        enableCaching: true,
        cacheTimeout: 300000, // 5 minutes
        maxCacheSize: 100,
        enableCompression: true,
        enableLazyLoading: true,
        batchSize: 10
      },

      // Documentation Settings
      documentation: {
        autoGenerateReadme: true,
        includeMetadata: true,
        addTimestamps: true,
        generateIndex: true,
        markdownFormat: 'github',
        includeSourceLinks: true
      },

      // Error Handling
      errorHandling: {
        continueOnError: true,
        logErrors: true,
        errorLogPath: './logs/mermaid-errors.log',
        maxRetries: 3,
        retryDelay: 1000
      },

      // Security Settings
      security: {
        enableSandbox: true,
        allowedCommands: ['mermaid-cli', 'npx @mermaid-js/mermaid-cli'],
        maxExecutionTime: 30000,
        maxMemoryUsage: 512 // MB
      },

      // Monitoring and Metrics
      monitoring: {
        enableMetrics: true,
        metricsInterval: 60000,
        trackPerformance: true,
        enableAlerts: true,
        alertThresholds: {
          generationTime: 10000, // ms
          errorRate: 0.1, // 10%
          memoryUsage: 0.8 // 80%
        }
      }
    };

    this.config = { ...this.defaultConfig };
    this.watchers = new Set();
  }

  async load() {
    try {
      const configExists = await this.fileExists(this.configPath);

      if (configExists) {
        const configContent = await fs.readFile(this.configPath, 'utf8');
        const userConfig = JSON.parse(configContent);
        this.config = this.mergeConfigs(this.defaultConfig, userConfig);
      } else {
        // Create default config file
        await this.save();
      }

      return this.config;
    } catch (error) {
      console.warn(`Failed to load config from ${this.configPath}:`, error.message);
      console.log('Using default configuration');
      return this.config;
    }
  }

  async save() {
    try {
      const configDir = path.dirname(this.configPath);
      await fs.mkdir(configDir, { recursive: true });
      await fs.writeFile(this.configPath, JSON.stringify(this.config, null, 2), 'utf8');
      return true;
    } catch (error) {
      console.error(`Failed to save config to ${this.configPath}:`, error.message);
      return false;
    }
  }

  async fileExists(filePath) {
    try {
      await fs.access(filePath);
      return true;
    } catch {
      return false;
    }
  }

  mergeConfigs(defaultConfig, userConfig) {
    const merged = { ...defaultConfig };

    for (const [key, value] of Object.entries(userConfig)) {
      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        merged[key] = this.mergeConfigs(merged[key] || {}, value);
      } else {
        merged[key] = value;
      }
    }

    return merged;
  }

  // Configuration getters
  get(path) {
    return this.getNestedValue(this.config, path);
  }

  set(path, value) {
    this.setNestedValue(this.config, path, value);
  }

  getNestedValue(obj, path) {
    return path.split('.').reduce((current, key) => current?.[key], obj);
  }

  setNestedValue(obj, path, value) {
    const keys = path.split('.');
    const lastKey = keys.pop();
    const target = keys.reduce((current, key) => {
      if (!(key in current)) current[key] = {};
      return current[key];
    }, obj);
    target[lastKey] = value;
  }

  // Output format configuration
  getOutputFormats() {
    return this.get('output.formats') || ['mermaid'];
  }

  getOutputDirectory() {
    return this.get('output.outputDirectory') || './docs/diagrams';
  }

  getFilenameTemplate(type, timestamp = Date.now()) {
    const template = this.get('output.filenameTemplate') || '{type}_{timestamp}';
    return template
      .replace('{type}', type)
      .replace('{timestamp}', timestamp);
  }

  // Diagram type configuration
  getDiagramTypeConfig(type) {
    return this.get(`diagramTypes.${type}`) || {};
  }

  isTypeEnabled(type) {
    const enabledTypes = this.get('diagramTypes.enabled') || [];
    return enabledTypes.includes(type);
  }

  // Trading system configuration
  isTradingSystemEnabled() {
    return this.get('trading.enableTradingTemplates') || false;
  }

  getTradingKeywords() {
    return this.get('trading.tradingKeywords') || [];
  }

  getTradingComponentCategories() {
    return this.get('trading.componentCategories') || {};
  }

  // Analysis configuration
  getAnalysisConfig() {
    return this.get('analysis') || {};
  }

  getWatchPaths() {
    return this.get('generation.watchPaths') || ['./src'];
  }

  getExcludePaths() {
    return this.get('generation.excludePaths') || [];
  }

  getFilePatterns() {
    return this.get('generation.filePatterns') || ['**/*.js'];
  }

  // Claude Flow configuration
  getClaudeFlowConfig() {
    return this.get('claudeFlow') || {};
  }

  isClaudeFlowEnabled() {
    return this.get('claudeFlow.enabled') || false;
  }

  // Performance configuration
  getPerformanceConfig() {
    return this.get('performance') || {};
  }

  isCachingEnabled() {
    return this.get('performance.enableCaching') || false;
  }

  getCacheTimeout() {
    return this.get('performance.cacheTimeout') || 300000;
  }

  // Documentation configuration
  getDocumentationConfig() {
    return this.get('documentation') || {};
  }

  shouldAutoGenerateReadme() {
    return this.get('documentation.autoGenerateReadme') || false;
  }

  // Error handling configuration
  getErrorHandlingConfig() {
    return this.get('errorHandling') || {};
  }

  shouldContinueOnError() {
    return this.get('errorHandling.continueOnError') || true;
  }

  // Configuration validation
  validate() {
    const errors = [];

    // Check required paths
    const outputDir = this.getOutputDirectory();
    if (!outputDir) {
      errors.push('Output directory not specified');
    }

    // Check formats
    const formats = this.getOutputFormats();
    if (!Array.isArray(formats) || formats.length === 0) {
      errors.push('No output formats specified');
    }

    // Check diagram types
    const enabledTypes = this.get('diagramTypes.enabled');
    if (!Array.isArray(enabledTypes) || enabledTypes.length === 0) {
      errors.push('No diagram types enabled');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  // Configuration presets
  static createMinimalConfig() {
    return {
      output: {
        formats: ['mermaid'],
        outputDirectory: './docs/diagrams'
      },
      generation: {
        autoGenerate: false,
        watchPaths: ['./src']
      },
      diagramTypes: {
        enabled: ['flowchart']
      },
      claudeFlow: {
        enabled: false
      }
    };
  }

  static createTradingConfig() {
    return {
      output: {
        formats: ['mermaid', 'svg'],
        outputDirectory: './docs/trading-diagrams'
      },
      generation: {
        autoGenerate: true,
        watchPaths: ['./src', './strategies', './models']
      },
      diagramTypes: {
        enabled: ['flowchart', 'class', 'sequence']
      },
      trading: {
        enableTradingTemplates: true,
        autoDetectTradingComponents: true
      },
      claudeFlow: {
        enabled: true
      }
    };
  }

  static createDevelopmentConfig() {
    return {
      output: {
        formats: ['mermaid'],
        outputDirectory: './dev-diagrams'
      },
      generation: {
        autoGenerate: true,
        debounceDelay: 1000
      },
      diagramTypes: {
        enabled: ['flowchart', 'class']
      },
      monitoring: {
        enableMetrics: true,
        trackPerformance: true
      },
      errorHandling: {
        logErrors: true,
        continueOnError: true
      }
    };
  }

  // Configuration export/import
  async exportConfig(filePath) {
    try {
      await fs.writeFile(filePath, JSON.stringify(this.config, null, 2), 'utf8');
      return true;
    } catch (error) {
      console.error('Failed to export config:', error.message);
      return false;
    }
  }

  async importConfig(filePath) {
    try {
      const configContent = await fs.readFile(filePath, 'utf8');
      const importedConfig = JSON.parse(configContent);
      this.config = this.mergeConfigs(this.defaultConfig, importedConfig);
      return true;
    } catch (error) {
      console.error('Failed to import config:', error.message);
      return false;
    }
  }

  // Runtime configuration updates
  updateConfig(updates) {
    this.config = this.mergeConfigs(this.config, updates);
  }

  resetToDefaults() {
    this.config = { ...this.defaultConfig };
  }

  // Configuration backup
  createBackup() {
    return JSON.parse(JSON.stringify(this.config));
  }

  restoreBackup(backup) {
    this.config = JSON.parse(JSON.stringify(backup));
  }

  // Get current configuration
  getConfig() {
    return this.config;
  }

  // Environment-specific configuration
  static getEnvironmentConfig() {
    const env = process.env.NODE_ENV || 'development';

    const envConfigs = {
      development: {
        monitoring: { enableMetrics: true },
        errorHandling: { logErrors: true },
        performance: { enableCaching: false }
      },
      production: {
        monitoring: { enableMetrics: true, enableAlerts: true },
        errorHandling: { continueOnError: false },
        performance: { enableCaching: true },
        security: { enableSandbox: true }
      },
      test: {
        output: { outputDirectory: './test-output' },
        generation: { autoGenerate: false },
        monitoring: { enableMetrics: false }
      }
    };

    return envConfigs[env] || envConfigs.development;
  }
}