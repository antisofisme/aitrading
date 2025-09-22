const fs = require('fs').promises;
const path = require('path');
const EventEmitter = require('events');
const axios = require('axios');
const logger = require('../utils/logger');

class ConfigManager extends EventEmitter {
  constructor() {
    super();
    this.config = new Map();
    this.configFile = path.join(__dirname, '../../config/client-config.json');
    this.backupFile = path.join(__dirname, '../../config/client-config.backup.json');
    this.isInitialized = false;
    this.isDirty = false;
    this.autoSaveInterval = null;
    this.backendSyncInterval = null;

    // Default configuration
    this.defaultConfig = {
      mt5: {
        server: '',
        login: '',
        password: '',
        maxConnections: 5,
        targetTicksPerSecond: 50,
        symbols: ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD'],
        timeframes: ['M1', 'M5', 'M15', 'H1'],
        reconnectDelay: 5000,
        maxReconnectAttempts: 10
      },
      dataCollector: {
        backendUrl: 'ws://localhost:3001/ws',
        bufferSize: 1000,
        aggregationInterval: 100,
        cacheMaxAge: 300000, // 5 minutes
        reconnectDelay: 3000,
        maxReconnectAttempts: 10
      },
      backend: {
        apiGateway: 'http://localhost:8000',
        dataBridge: 'ws://localhost:3001/ws',
        centralHub: 'http://localhost:7000',
        authEndpoint: '/api/auth',
        timeout: 30000,
        retries: 3
      },
      performance: {
        targetTicksPerSecond: 50,
        maxLatencyMs: 50,
        monitoringInterval: 1000,
        alertThresholds: {
          highLatency: 100,
          lowThroughput: 25,
          connectionLoss: 5000
        }
      },
      security: {
        encryptionEnabled: true,
        certificatePinning: true,
        tlsMinVersion: 'TLSv1.3',
        tokenRefreshInterval: 3600000 // 1 hour
      },
      ui: {
        theme: 'dark',
        refreshInterval: 1000,
        chartUpdateInterval: 500,
        notificationsEnabled: true,
        soundEnabled: false
      },
      logging: {
        level: 'info',
        maxFiles: 5,
        maxSize: '10m',
        enableConsole: true,
        enableFile: true
      }
    };
  }

  async initialize() {
    try {
      logger.info('Initializing Configuration Manager...');

      // Ensure config directory exists
      await this.ensureConfigDirectory();

      // Load configuration
      await this.loadConfig();

      // Validate configuration
      this.validateConfig();

      // Setup auto-save
      this.setupAutoSave();

      // Setup backend synchronization
      this.setupBackendSync();

      this.isInitialized = true;
      logger.info('Configuration Manager initialized successfully');

      this.emit('initialized');

    } catch (error) {
      logger.error('Failed to initialize Configuration Manager:', error);
      throw error;
    }
  }

  async ensureConfigDirectory() {
    const configDir = path.dirname(this.configFile);

    try {
      await fs.access(configDir);
    } catch (error) {
      logger.info('Creating config directory:', configDir);
      await fs.mkdir(configDir, { recursive: true });
    }
  }

  async loadConfig() {
    try {
      // Try to load existing config
      const configData = await fs.readFile(this.configFile, 'utf8');
      const parsedConfig = JSON.parse(configData);

      // Merge with defaults (in case new config options were added)
      this.config = new Map(Object.entries(this.mergeConfig(this.defaultConfig, parsedConfig)));

      logger.info('Configuration loaded from file');

    } catch (error) {
      if (error.code === 'ENOENT') {
        // Config file doesn't exist, use defaults
        logger.info('Config file not found, using defaults');
        this.config = new Map(Object.entries(this.defaultConfig));
        await this.saveConfig();
      } else {
        logger.error('Error loading config:', error);

        // Try to load backup
        try {
          const backupData = await fs.readFile(this.backupFile, 'utf8');
          const parsedBackup = JSON.parse(backupData);
          this.config = new Map(Object.entries(this.mergeConfig(this.defaultConfig, parsedBackup)));
          logger.warn('Loaded configuration from backup file');
        } catch (backupError) {
          logger.error('Backup config also failed, using defaults');
          this.config = new Map(Object.entries(this.defaultConfig));
        }
      }
    }
  }

  mergeConfig(defaults, loaded) {
    const merged = { ...defaults };

    Object.keys(loaded).forEach(key => {
      if (typeof loaded[key] === 'object' && !Array.isArray(loaded[key])) {
        merged[key] = { ...defaults[key], ...loaded[key] };
      } else {
        merged[key] = loaded[key];
      }
    });

    return merged;
  }

  validateConfig() {
    // Validate critical configuration values
    const validation = {
      'mt5.maxConnections': (value) => value > 0 && value <= 10,
      'mt5.targetTicksPerSecond': (value) => value > 0 && value <= 1000,
      'dataCollector.bufferSize': (value) => value > 0 && value <= 10000,
      'performance.targetTicksPerSecond': (value) => value > 0 && value <= 1000,
      'performance.maxLatencyMs': (value) => value > 0 && value <= 1000
    };

    Object.keys(validation).forEach(path => {
      const value = this.getNestedValue(path);
      if (value !== undefined && !validation[path](value)) {
        logger.warn(`Invalid configuration value for ${path}: ${value}`);
        // Reset to default
        const defaultValue = this.getNestedValue(path, this.defaultConfig);
        this.setNestedValue(path, defaultValue);
      }
    });
  }

  getNestedValue(path, source = null) {
    const obj = source || Object.fromEntries(this.config);
    return path.split('.').reduce((current, key) => current?.[key], obj);
  }

  setNestedValue(path, value) {
    const keys = path.split('.');
    const lastKey = keys.pop();
    const target = keys.reduce((current, key) => {
      if (!current[key]) current[key] = {};
      return current[key];
    }, Object.fromEntries(this.config));

    target[lastKey] = value;
    this.markDirty();
  }

  setupAutoSave() {
    // Auto-save every 30 seconds if there are changes
    this.autoSaveInterval = setInterval(async () => {
      if (this.isDirty) {
        try {
          await this.saveConfig();
        } catch (error) {
          logger.error('Auto-save failed:', error);
        }
      }
    }, 30000);
  }

  setupBackendSync() {
    // Sync with backend every 5 minutes
    this.backendSyncInterval = setInterval(async () => {
      try {
        await this.syncWithBackend();
      } catch (error) {
        logger.error('Backend sync failed:', error);
      }
    }, 5 * 60 * 1000);
  }

  async syncWithBackend() {
    try {
      const backendConfig = this.config.get('backend');

      if (!backendConfig || !backendConfig.apiGateway) {
        return; // No backend configured
      }

      // Get backend configuration
      const response = await axios.get(`${backendConfig.apiGateway}/api/client-config`, {
        timeout: backendConfig.timeout || 30000,
        headers: {
          'X-Client-Type': 'desktop',
          'X-Client-Version': '1.0.0'
        }
      });

      if (response.data && response.data.config) {
        const serverConfig = response.data.config;

        // Merge server configuration with local config
        const updated = this.mergeServerConfig(serverConfig);

        if (updated) {
          logger.info('Configuration updated from backend');
          this.emit('configUpdated', { source: 'backend' });
        }
      }

    } catch (error) {
      logger.debug('Backend sync failed (this is normal if backend is not available):', error.message);
    }
  }

  mergeServerConfig(serverConfig) {
    let updated = false;

    // Only allow certain configs to be updated from server
    const allowedUpdates = [
      'dataCollector.backendUrl',
      'backend.apiGateway',
      'backend.dataBridge',
      'backend.centralHub',
      'performance.targetTicksPerSecond',
      'performance.alertThresholds'
    ];

    allowedUpdates.forEach(path => {
      const serverValue = this.getNestedValue(path, serverConfig);
      const currentValue = this.getNestedValue(path);

      if (serverValue !== undefined && serverValue !== currentValue) {
        this.setNestedValue(path, serverValue);
        updated = true;
        logger.info(`Updated ${path} from backend: ${serverValue}`);
      }
    });

    return updated;
  }

  async saveConfig() {
    try {
      // Create backup first
      try {
        await fs.copyFile(this.configFile, this.backupFile);
      } catch (error) {
        // Ignore backup errors
      }

      // Save current config
      const configData = JSON.stringify(Object.fromEntries(this.config), null, 2);
      await fs.writeFile(this.configFile, configData, 'utf8');

      this.isDirty = false;
      logger.debug('Configuration saved to file');

    } catch (error) {
      logger.error('Failed to save configuration:', error);
      throw error;
    }
  }

  markDirty() {
    this.isDirty = true;
    this.emit('configChanged');
  }

  // Public interface methods
  get(section, key = null) {
    const sectionConfig = this.config.get(section);

    if (key) {
      return sectionConfig?.[key];
    }

    return sectionConfig;
  }

  set(section, keyOrConfig, value = null) {
    let sectionConfig = this.config.get(section) || {};

    if (typeof keyOrConfig === 'object') {
      // Setting entire section
      sectionConfig = { ...sectionConfig, ...keyOrConfig };
    } else {
      // Setting individual key
      sectionConfig[keyOrConfig] = value;
    }

    this.config.set(section, sectionConfig);
    this.markDirty();

    this.emit('configUpdated', { section, key: keyOrConfig, value });
  }

  async update(updates) {
    Object.keys(updates).forEach(section => {
      if (typeof updates[section] === 'object') {
        this.set(section, updates[section]);
      }
    });

    // Validate after updates
    this.validateConfig();

    // Save immediately for user-initiated updates
    await this.saveConfig();

    this.emit('configUpdated', { source: 'user', updates });
  }

  getAll() {
    return Object.fromEntries(this.config);
  }

  // Configuration presets
  async loadPreset(presetName) {
    const presets = {
      development: {
        logging: { level: 'debug', enableConsole: true },
        performance: { monitoringInterval: 500 },
        ui: { refreshInterval: 500 }
      },
      production: {
        logging: { level: 'info', enableConsole: false },
        performance: { monitoringInterval: 1000 },
        ui: { refreshInterval: 1000 }
      },
      testing: {
        mt5: { targetTicksPerSecond: 10 },
        performance: { targetTicksPerSecond: 10 },
        dataCollector: { bufferSize: 100 }
      }
    };

    const preset = presets[presetName];
    if (!preset) {
      throw new Error(`Unknown preset: ${presetName}`);
    }

    await this.update(preset);
    logger.info(`Loaded configuration preset: ${presetName}`);
  }

  // Export/Import configuration
  async exportConfig(filePath) {
    const configData = JSON.stringify(this.getAll(), null, 2);
    await fs.writeFile(filePath, configData, 'utf8');
    logger.info(`Configuration exported to: ${filePath}`);
  }

  async importConfig(filePath) {
    const configData = await fs.readFile(filePath, 'utf8');
    const importedConfig = JSON.parse(configData);

    // Merge with current config
    const merged = this.mergeConfig(this.getAll(), importedConfig);
    this.config = new Map(Object.entries(merged));

    this.validateConfig();
    await this.saveConfig();

    logger.info(`Configuration imported from: ${filePath}`);
    this.emit('configUpdated', { source: 'import', file: filePath });
  }

  // Cleanup
  async shutdown() {
    logger.info('Shutting down Configuration Manager...');

    // Clear intervals
    if (this.autoSaveInterval) {
      clearInterval(this.autoSaveInterval);
      this.autoSaveInterval = null;
    }

    if (this.backendSyncInterval) {
      clearInterval(this.backendSyncInterval);
      this.backendSyncInterval = null;
    }

    // Final save
    if (this.isDirty) {
      try {
        await this.saveConfig();
      } catch (error) {
        logger.error('Failed to save config during shutdown:', error);
      }
    }

    logger.info('Configuration Manager shutdown complete');
  }

  // Status and diagnostics
  getStatus() {
    return {
      initialized: this.isInitialized,
      isDirty: this.isDirty,
      configFile: this.configFile,
      sectionsLoaded: Array.from(this.config.keys()),
      lastSaved: this.isDirty ? 'pending' : 'saved'
    };
  }
}

module.exports = ConfigManager;