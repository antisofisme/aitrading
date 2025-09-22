const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const logger = require('./utils/logger');
const ConfigManager = require('./services/config-manager');
const MetaTraderConnector = require('./services/mt5-connector');
const DataCollector = require('./services/data-collector');
const SecurityManager = require('./security/security-manager');
const PerformanceMonitor = require('./monitoring/performance-monitor');

class AITradingClient {
  constructor() {
    this.mainWindow = null;
    this.configManager = new ConfigManager();
    this.securityManager = new SecurityManager();
    this.mt5Connector = null;
    this.dataCollector = null;
    this.performanceMonitor = new PerformanceMonitor();
    this.isShuttingDown = false;
  }

  async initialize() {
    try {
      logger.info('Initializing AI Trading Client...');

      // Initialize configuration
      await this.configManager.initialize();

      // Initialize security manager
      await this.securityManager.initialize();

      // Initialize performance monitoring
      await this.performanceMonitor.initialize();

      // Initialize MT5 connector with configuration
      const mt5Config = await this.configManager.get('mt5');
      this.mt5Connector = new MetaTraderConnector(mt5Config, this.securityManager);

      // Initialize data collector
      const dataConfig = await this.configManager.get('dataCollector');
      this.dataCollector = new DataCollector(dataConfig, this.performanceMonitor);

      // Connect services
      await this.connectServices();

      logger.info('AI Trading Client initialized successfully');

    } catch (error) {
      logger.error('Failed to initialize client:', error);
      throw error;
    }
  }

  async connectServices() {
    logger.info('Connecting to backend services...');

    try {
      // Connect MT5 first
      await this.mt5Connector.connect();
      logger.info('MT5 connector established');

      // Connect data collector to backend
      await this.dataCollector.connect();
      logger.info('Data collector connected to backend');

      // Setup data flow pipeline
      this.setupDataFlow();

      // Start performance monitoring
      this.performanceMonitor.startMonitoring();

    } catch (error) {
      logger.error('Failed to connect services:', error);
      throw error;
    }
  }

  setupDataFlow() {
    // Setup real-time data flow: MT5 -> DataCollector -> Backend
    this.mt5Connector.on('tick', (tickData) => {
      this.dataCollector.processTickData(tickData);
    });

    this.mt5Connector.on('marketData', (marketData) => {
      this.dataCollector.processMarketData(marketData);
    });

    // Setup performance monitoring
    this.dataCollector.on('dataProcessed', (metrics) => {
      this.performanceMonitor.recordDataMetrics(metrics);
    });

    // Setup error handling
    this.mt5Connector.on('error', (error) => {
      logger.error('MT5 connector error:', error);
      this.handleConnectorError(error);
    });

    this.dataCollector.on('error', (error) => {
      logger.error('Data collector error:', error);
      this.handleDataCollectorError(error);
    });
  }

  createWindow() {
    this.mainWindow = new BrowserWindow({
      width: 1200,
      height: 800,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        preload: path.join(__dirname, 'preload.js')
      },
      icon: path.join(__dirname, '../assets/icon.png'),
      title: 'AI Trading Platform - Client'
    });

    this.mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'));

    if (process.env.NODE_ENV === 'development') {
      this.mainWindow.webContents.openDevTools();
    }

    this.mainWindow.on('closed', () => {
      this.mainWindow = null;
    });

    this.setupIPC();
  }

  setupIPC() {
    // IPC handlers for renderer communication
    ipcMain.handle('get-status', async () => {
      return {
        mt5Connected: this.mt5Connector?.isConnected() || false,
        dataCollectorConnected: this.dataCollector?.isConnected() || false,
        performanceMetrics: await this.performanceMonitor.getMetrics(),
        config: await this.configManager.getAll()
      };
    });

    ipcMain.handle('get-performance-metrics', async () => {
      return await this.performanceMonitor.getDetailedMetrics();
    });

    ipcMain.handle('update-config', async (event, updates) => {
      await this.configManager.update(updates);
      return { success: true };
    });

    ipcMain.handle('restart-connections', async () => {
      await this.restartConnections();
      return { success: true };
    });
  }

  async restartConnections() {
    logger.info('Restarting connections...');

    try {
      // Disconnect current connections
      if (this.dataCollector) {
        await this.dataCollector.disconnect();
      }

      if (this.mt5Connector) {
        await this.mt5Connector.disconnect();
      }

      // Reconnect with updated configuration
      await this.connectServices();

      logger.info('Connections restarted successfully');

    } catch (error) {
      logger.error('Failed to restart connections:', error);
      throw error;
    }
  }

  async handleConnectorError(error) {
    logger.error('Handling MT5 connector error:', error);

    // Attempt reconnection with exponential backoff
    if (!this.isShuttingDown) {
      setTimeout(async () => {
        try {
          await this.mt5Connector.reconnect();
        } catch (reconnectError) {
          logger.error('Failed to reconnect MT5:', reconnectError);
        }
      }, 5000);
    }
  }

  async handleDataCollectorError(error) {
    logger.error('Handling data collector error:', error);

    // Attempt reconnection to backend
    if (!this.isShuttingDown) {
      setTimeout(async () => {
        try {
          await this.dataCollector.reconnect();
        } catch (reconnectError) {
          logger.error('Failed to reconnect data collector:', reconnectError);
        }
      }, 3000);
    }
  }

  async shutdown() {
    this.isShuttingDown = true;
    logger.info('Shutting down AI Trading Client...');

    try {
      // Stop performance monitoring
      if (this.performanceMonitor) {
        await this.performanceMonitor.stop();
      }

      // Disconnect data collector
      if (this.dataCollector) {
        await this.dataCollector.disconnect();
      }

      // Disconnect MT5
      if (this.mt5Connector) {
        await this.mt5Connector.disconnect();
      }

      // Save configuration
      if (this.configManager) {
        await this.configManager.save();
      }

      logger.info('Client shutdown complete');

    } catch (error) {
      logger.error('Error during shutdown:', error);
    }
  }
}

// Application lifecycle
const client = new AITradingClient();

app.whenReady().then(async () => {
  try {
    await client.initialize();
    client.createWindow();
  } catch (error) {
    logger.error('Failed to start application:', error);
    app.quit();
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    client.createWindow();
  }
});

app.on('before-quit', async (event) => {
  if (!client.isShuttingDown) {
    event.preventDefault();
    await client.shutdown();
    app.quit();
  }
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  logger.error('Uncaught exception:', error);
  client.shutdown().then(() => process.exit(1));
});

process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled rejection at:', promise, 'reason:', reason);
});

module.exports = AITradingClient;