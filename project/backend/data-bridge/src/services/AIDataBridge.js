/**
 * AI Data Bridge - Level 3 Component
 * Connects MT5 data pipeline with AI Orchestration Service
 * Handles real-time data streaming, feature preparation, and AI model integration
 */

const EventEmitter = require('events');
const logger = require('../utils/logger');

class AIDataBridge extends EventEmitter {
  constructor(config = {}) {
    super();
    this.config = {
      aiOrchestrationUrl: process.env.AI_ORCHESTRATION_URL || 'http://localhost:8008',
      streamingEnabled: true,
      batchSize: 50,
      maxRetries: 3,
      retryDelay: 1000,
      healthCheckInterval: 30000,
      dataBufferSize: 1000,
      performanceTargets: {
        maxLatency: 50, // ms - Level 3 requirement
        minThroughput: 50, // TPS
        maxErrorRate: 0.1 // %
      },
      aiModelEndpoints: {
        prediction: '/api/predict',
        inference: '/api/inference',
        model_health: '/api/health',
        model_metrics: '/api/metrics'
      },
      featureConfig: {
        enableRealTimeFeatures: true,
        enableHistoricalContext: true,
        enableMarketIndicators: true,
        enablePatternRecognition: true,
        maxFeatureCount: 100
      },
      ...config
    };

    this.isConnected = false;
    this.isStreaming = false;
    this.aiConnectionStatus = 'disconnected';
    this.dataBuffer = [];
    this.metrics = {
      totalDataSent: 0,
      totalPredictions: 0,
      averageLatency: 0,
      errorCount: 0,
      successRate: 100,
      aiResponseTimes: [],
      lastStreamTime: null,
      connectionUptime: 0
    };

    this.aiModels = new Map();
    this.activeSubscriptions = new Map();
    this.streamingConnections = new Map();
  }

  /**
   * Initialize the AI Data Bridge
   */
  async initialize() {
    try {
      logger.info('Initializing AI Data Bridge...');

      // Test AI Orchestration Service connection
      await this.testAIConnection();

      // Initialize streaming capabilities
      this.initializeStreaming();

      // Start health monitoring
      this.startHealthMonitoring();

      // Start performance monitoring
      this.startPerformanceMonitoring();

      this.isConnected = true;
      this.emit('initialized', {
        timestamp: new Date().toISOString(),
        config: this.config
      });

      logger.info('AI Data Bridge initialized successfully');
      return { success: true, message: 'AI Data Bridge initialized' };

    } catch (error) {
      logger.error('Failed to initialize AI Data Bridge:', error);
      throw error;
    }
  }

  /**
   * Start streaming processed data to AI services
   */
  async startStreaming() {
    if (this.isStreaming) {
      logger.warn('AI Data Bridge is already streaming');
      return;
    }

    if (!this.isConnected) {
      throw new Error('AI Data Bridge must be initialized before streaming');
    }

    logger.info('Starting AI data streaming...');
    this.isStreaming = true;
    this.metrics.lastStreamTime = Date.now();

    this.emit('streamingStarted', {
      timestamp: new Date().toISOString(),
      targets: this.config.performanceTargets
    });

    logger.info('AI data streaming started successfully');
  }

  /**
   * Stop streaming data to AI services
   */
  async stopStreaming() {
    if (!this.isStreaming) {
      return;
    }

    logger.info('Stopping AI data streaming...');
    this.isStreaming = false;

    // Close active streaming connections
    this.streamingConnections.forEach((connection, connectionId) => {
      if (connection.close) {
        connection.close();
      }
    });
    this.streamingConnections.clear();

    this.emit('streamingStopped', {
      timestamp: new Date().toISOString(),
      metrics: this.getMetrics()
    });

    logger.info('AI data streaming stopped');
  }

  /**
   * Send processed data to AI models for prediction/inference
   */
  async sendToAI(processedData, modelType = 'default', options = {}) {
    if (!this.isStreaming) {
      throw new Error('Streaming must be started before sending data to AI');
    }

    const startTime = Date.now();

    try {
      // Prepare AI-ready data format
      const aiReadyData = await this.prepareAIData(processedData, modelType, options);

      // Validate data before sending
      const validation = this.validateAIData(aiReadyData);
      if (!validation.isValid) {
        throw new Error(`Invalid AI data: ${validation.errors.join(', ')}`);
      }

      // Select appropriate AI model/endpoint
      const endpoint = this.selectAIEndpoint(modelType, options);

      // Send data to AI service
      const response = await this.callAIService(endpoint, aiReadyData, options);

      // Process AI response
      const processedResponse = await this.processAIResponse(response, processedData, options);

      // Record metrics
      const latency = Date.now() - startTime;
      this.recordMetrics(latency, true);

      // Emit success event
      this.emit('aiPrediction', {
        symbol: processedData.raw?.symbol,
        tenantId: processedData.metadata?.tenantId,
        modelType,
        latency,
        response: processedResponse,
        timestamp: new Date().toISOString()
      });

      return processedResponse;

    } catch (error) {
      const latency = Date.now() - startTime;
      this.recordMetrics(latency, false);

      logger.error('Failed to send data to AI:', error);

      this.emit('aiError', {
        symbol: processedData.raw?.symbol,
        tenantId: processedData.metadata?.tenantId,
        modelType,
        error: error.message,
        latency,
        timestamp: new Date().toISOString()
      });

      throw error;
    }
  }

  /**
   * Prepare data in AI-compatible format
   */
  async prepareAIData(processedData, modelType, options) {
    const aiData = {
      modelType,
      timestamp: new Date().toISOString(),
      metadata: {
        symbol: processedData.raw?.symbol,
        tenantId: processedData.metadata?.tenantId,
        processingLatency: processedData.metadata?.processingLatency,
        dataSource: 'mt5_enhanced'
      },
      features: {},
      context: {}
    };

    // Include processed features
    if (processedData.features) {
      aiData.features = { ...processedData.features };
    }

    // Add real-time context
    if (this.config.featureConfig.enableRealTimeFeatures) {
      aiData.context.realTime = {
        marketPhase: processedData.sentiment?.marketPhase,
        volatility: processedData.sentiment?.volatility,
        trendStrength: processedData.sentiment?.trendStrength,
        anomalyRisk: processedData.anomalies?.overallRisk || 0
      };
    }

    // Add historical context
    if (this.config.featureConfig.enableHistoricalContext) {
      aiData.context.historical = await this.getHistoricalContext(
        processedData.raw?.symbol,
        processedData.metadata?.tenantId
      );
    }

    // Add market indicators
    if (this.config.featureConfig.enableMarketIndicators) {
      aiData.context.indicators = this.extractMarketIndicators(processedData);
    }

    // Add pattern recognition data
    if (this.config.featureConfig.enablePatternRecognition && processedData.patterns) {
      aiData.context.patterns = processedData.patterns;
    }

    // Optimize feature count if needed
    if (Object.keys(aiData.features).length > this.config.featureConfig.maxFeatureCount) {
      aiData.features = this.optimizeFeatures(aiData.features);
    }

    return aiData;
  }

  /**
   * Validate AI data before sending
   */
  validateAIData(aiData) {
    const errors = [];

    // Required fields validation
    if (!aiData.modelType) errors.push('Missing modelType');
    if (!aiData.features || Object.keys(aiData.features).length === 0) {
      errors.push('Missing or empty features');
    }
    if (!aiData.metadata?.symbol) errors.push('Missing symbol in metadata');

    // Feature validation
    Object.entries(aiData.features).forEach(([key, value]) => {
      if (typeof value !== 'number' || isNaN(value) || !isFinite(value)) {
        errors.push(`Invalid feature value for ${key}: ${value}`);
      }
    });

    // Data size validation
    const dataSize = JSON.stringify(aiData).length;
    if (dataSize > 1024 * 1024) { // 1MB limit
      errors.push('Data size exceeds 1MB limit');
    }

    return {
      isValid: errors.length === 0,
      errors,
      dataSize
    };
  }

  /**
   * Select appropriate AI endpoint based on model type and options
   */
  selectAIEndpoint(modelType, options) {
    const baseUrl = this.config.aiOrchestrationUrl;

    switch (modelType) {
      case 'prediction':
        return `${baseUrl}${this.config.aiModelEndpoints.prediction}`;
      case 'inference':
        return `${baseUrl}${this.config.aiModelEndpoints.inference}`;
      default:
        return `${baseUrl}${this.config.aiModelEndpoints.prediction}`;
    }
  }

  /**
   * Call AI service with retry logic
   */
  async callAIService(endpoint, data, options) {
    let lastError;

    for (let attempt = 1; attempt <= this.config.maxRetries; attempt++) {
      try {
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${process.env.AI_SERVICE_TOKEN || 'default-token'}`,
            'X-Tenant-ID': data.metadata?.tenantId || 'default',
            'X-Request-ID': this.generateRequestId()
          },
          body: JSON.stringify(data),
          timeout: options.timeout || 30000
        });

        if (!response.ok) {
          throw new Error(`AI service error: ${response.status} ${response.statusText}`);
        }

        const responseData = await response.json();
        return responseData;

      } catch (error) {
        lastError = error;
        logger.warn(`AI service call attempt ${attempt} failed:`, error.message);

        if (attempt < this.config.maxRetries) {
          await new Promise(resolve =>
            setTimeout(resolve, this.config.retryDelay * attempt)
          );
        }
      }
    }

    throw lastError;
  }

  /**
   * Process AI service response
   */
  async processAIResponse(response, originalData, options) {
    return {
      success: true,
      predictions: response.predictions || [],
      confidence: response.confidence || 0,
      recommendations: response.recommendations || [],
      signals: response.signals || [],
      metadata: {
        modelVersion: response.modelVersion,
        responseTime: response.responseTime,
        originalSymbol: originalData.raw?.symbol,
        tenantId: originalData.metadata?.tenantId,
        timestamp: new Date().toISOString()
      }
    };
  }

  /**
   * Get historical context for AI models
   */
  async getHistoricalContext(symbol, tenantId) {
    // This would integrate with historical data storage
    // For now, return mock historical context
    return {
      priceHistory: {
        last24h: { high: 0, low: 0, volatility: 0 },
        last7d: { trend: 0, support: 0, resistance: 0 },
        last30d: { performance: 0, correlation: 0 }
      },
      volumeHistory: {
        averageVolume: 0,
        volumeTrend: 0,
        unusualActivity: false
      },
      marketEvents: {
        economicEvents: [],
        technicalBreakouts: [],
        newsImpact: 0
      }
    };
  }

  /**
   * Extract market indicators for AI context
   */
  extractMarketIndicators(processedData) {
    return {
      technical: {
        rsi: processedData.technical?.rsi || 50,
        macd: processedData.technical?.macd?.line || 0,
        bollinger: {
          position: 0, // Price position within Bollinger Bands
          squeeze: false // Band squeeze indicator
        }
      },
      sentiment: {
        overall: processedData.sentiment?.marketPhase || 'neutral',
        momentum: processedData.sentiment?.priceVelocity || 0,
        strength: processedData.sentiment?.trendStrength || 0
      },
      volume: {
        ratio: processedData.volume?.volumeRatio || 1,
        trend: processedData.volume?.volumeTrend || 0,
        vwap: processedData.volume?.vwap || 0
      }
    };
  }

  /**
   * Optimize features by selecting most important ones
   */
  optimizeFeatures(features) {
    // Simple feature selection - keep most important features
    const importantFeatures = [
      'price_bid', 'price_ask', 'price_mid', 'price_spread',
      'sma5', 'sma10', 'ema5', 'rsi', 'macd_line',
      'volume_ratio', 'volatility', 'trend_strength',
      'anomaly_risk', 'hour_of_day', 'is_market_open'
    ];

    const optimized = {};
    importantFeatures.forEach(key => {
      if (features.hasOwnProperty(key)) {
        optimized[key] = features[key];
      }
    });

    return optimized;
  }

  /**
   * Stream data continuously to AI services
   */
  async streamDataToAI(dataStream, modelType = 'default', options = {}) {
    if (!this.isStreaming) {
      throw new Error('Streaming is not active');
    }

    const connectionId = this.generateConnectionId();
    logger.info(`Starting AI data stream connection: ${connectionId}`);

    try {
      // Buffer for batch processing
      const buffer = [];
      let lastSendTime = Date.now();

      // Process data stream
      for await (const data of dataStream) {
        buffer.push(data);

        // Send batch when buffer is full or time threshold reached
        const now = Date.now();
        if (buffer.length >= this.config.batchSize ||
            (now - lastSendTime) >= 1000) { // 1 second threshold

          const batch = buffer.splice(0, this.config.batchSize);
          await this.sendBatchToAI(batch, modelType, options);
          lastSendTime = now;
        }

        // Emit streaming progress
        this.emit('streamProgress', {
          connectionId,
          bufferedItems: buffer.length,
          totalProcessed: this.metrics.totalDataSent,
          timestamp: new Date().toISOString()
        });
      }

      // Send remaining buffer
      if (buffer.length > 0) {
        await this.sendBatchToAI(buffer, modelType, options);
      }

      logger.info(`AI data stream connection completed: ${connectionId}`);

    } catch (error) {
      logger.error(`AI data stream error [${connectionId}]:`, error);
      throw error;
    } finally {
      this.streamingConnections.delete(connectionId);
    }
  }

  /**
   * Send batch of data to AI service
   */
  async sendBatchToAI(batch, modelType, options) {
    if (batch.length === 0) return;

    const startTime = Date.now();

    try {
      // Prepare batch for AI processing
      const batchData = {
        modelType,
        batchSize: batch.length,
        timestamp: new Date().toISOString(),
        items: await Promise.all(
          batch.map(item => this.prepareAIData(item, modelType, options))
        )
      };

      // Send batch to AI service
      const endpoint = this.selectAIEndpoint('batch', options);
      const response = await this.callAIService(endpoint, batchData, options);

      // Process batch response
      const processedResults = await this.processBatchResponse(response, batch, options);

      // Record metrics
      const latency = Date.now() - startTime;
      this.recordBatchMetrics(batch.length, latency, true);

      this.emit('batchProcessed', {
        batchSize: batch.length,
        latency,
        results: processedResults.length,
        timestamp: new Date().toISOString()
      });

      return processedResults;

    } catch (error) {
      const latency = Date.now() - startTime;
      this.recordBatchMetrics(batch.length, latency, false);

      logger.error('Batch processing failed:', error);
      throw error;
    }
  }

  /**
   * Process batch response from AI service
   */
  async processBatchResponse(response, originalBatch, options) {
    if (!response.results || !Array.isArray(response.results)) {
      throw new Error('Invalid batch response format');
    }

    return response.results.map((result, index) => ({
      ...result,
      originalData: originalBatch[index],
      batchIndex: index,
      processed: true
    }));
  }

  /**
   * Test AI Orchestration Service connection
   */
  async testAIConnection() {
    try {
      const healthEndpoint = `${this.config.aiOrchestrationUrl}${this.config.aiModelEndpoints.model_health}`;

      const response = await fetch(healthEndpoint, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${process.env.AI_SERVICE_TOKEN || 'default-token'}`
        },
        timeout: 10000
      });

      if (!response.ok) {
        throw new Error(`AI service health check failed: ${response.status}`);
      }

      const healthData = await response.json();
      this.aiConnectionStatus = 'connected';

      logger.info('AI Orchestration Service connection verified', healthData);
      return healthData;

    } catch (error) {
      this.aiConnectionStatus = 'error';
      logger.error('AI Orchestration Service connection failed:', error);
      throw error;
    }
  }

  /**
   * Initialize streaming capabilities
   */
  initializeStreaming() {
    // Set up event listeners for data processing
    this.on('dataReceived', async (data) => {
      if (this.isStreaming) {
        this.dataBuffer.push(data);

        // Process buffer when it reaches batch size
        if (this.dataBuffer.length >= this.config.batchSize) {
          const batch = this.dataBuffer.splice(0, this.config.batchSize);
          try {
            await this.sendBatchToAI(batch, 'default', {});
          } catch (error) {
            logger.error('Auto-batch processing failed:', error);
          }
        }
      }
    });

    logger.info('Streaming capabilities initialized');
  }

  /**
   * Start health monitoring
   */
  startHealthMonitoring() {
    this.healthInterval = setInterval(async () => {
      try {
        await this.testAIConnection();
        this.emit('healthCheck', {
          status: 'healthy',
          aiConnection: this.aiConnectionStatus,
          timestamp: new Date().toISOString()
        });
      } catch (error) {
        this.emit('healthCheck', {
          status: 'unhealthy',
          aiConnection: this.aiConnectionStatus,
          error: error.message,
          timestamp: new Date().toISOString()
        });
      }
    }, this.config.healthCheckInterval);

    logger.info('Health monitoring started');
  }

  /**
   * Start performance monitoring
   */
  startPerformanceMonitoring() {
    this.performanceInterval = setInterval(() => {
      const performance = this.calculatePerformance();

      this.emit('performanceUpdate', {
        ...performance,
        targets: this.config.performanceTargets,
        timestamp: new Date().toISOString()
      });

      // Check if performance targets are met
      this.checkPerformanceTargets(performance);

    }, 5000); // Every 5 seconds

    logger.info('Performance monitoring started');
  }

  /**
   * Calculate current performance metrics
   */
  calculatePerformance() {
    const now = Date.now();
    const uptimeMs = this.metrics.lastStreamTime ? now - this.metrics.lastStreamTime : 0;

    return {
      averageLatency: this.metrics.averageLatency,
      throughput: this.calculateThroughput(),
      errorRate: this.calculateErrorRate(),
      successRate: this.metrics.successRate,
      uptime: uptimeMs / 1000, // in seconds
      totalDataSent: this.metrics.totalDataSent,
      totalPredictions: this.metrics.totalPredictions,
      aiConnectionStatus: this.aiConnectionStatus
    };
  }

  /**
   * Calculate throughput (data points per second)
   */
  calculateThroughput() {
    const now = Date.now();
    if (!this.metrics.lastStreamTime || this.metrics.totalDataSent === 0) {
      return 0;
    }

    const timeElapsed = (now - this.metrics.lastStreamTime) / 1000; // seconds
    return this.metrics.totalDataSent / timeElapsed;
  }

  /**
   * Calculate error rate percentage
   */
  calculateErrorRate() {
    const totalRequests = this.metrics.totalDataSent + this.metrics.errorCount;
    if (totalRequests === 0) return 0;

    return (this.metrics.errorCount / totalRequests) * 100;
  }

  /**
   * Check if performance targets are being met
   */
  checkPerformanceTargets(performance) {
    const targets = this.config.performanceTargets;
    const alerts = [];

    if (performance.averageLatency > targets.maxLatency) {
      alerts.push({
        type: 'latency',
        message: `Average latency (${performance.averageLatency}ms) exceeds target (${targets.maxLatency}ms)`,
        current: performance.averageLatency,
        target: targets.maxLatency
      });
    }

    if (performance.throughput < targets.minThroughput) {
      alerts.push({
        type: 'throughput',
        message: `Throughput (${performance.throughput} TPS) below target (${targets.minThroughput} TPS)`,
        current: performance.throughput,
        target: targets.minThroughput
      });
    }

    if (performance.errorRate > targets.maxErrorRate) {
      alerts.push({
        type: 'error_rate',
        message: `Error rate (${performance.errorRate}%) exceeds target (${targets.maxErrorRate}%)`,
        current: performance.errorRate,
        target: targets.maxErrorRate
      });
    }

    if (alerts.length > 0) {
      this.emit('performanceAlert', {
        alerts,
        performance,
        timestamp: new Date().toISOString()
      });
    }
  }

  /**
   * Record metrics for individual requests
   */
  recordMetrics(latency, success) {
    this.metrics.totalDataSent++;

    if (success) {
      this.metrics.totalPredictions++;

      // Update average latency with exponential moving average
      const alpha = 0.1;
      this.metrics.averageLatency =
        (this.metrics.averageLatency * (1 - alpha)) + (latency * alpha);
    } else {
      this.metrics.errorCount++;
    }

    // Update success rate
    const totalRequests = this.metrics.totalDataSent + this.metrics.errorCount;
    this.metrics.successRate = (this.metrics.totalPredictions / totalRequests) * 100;

    // Track AI response times
    this.metrics.aiResponseTimes.push(latency);
    if (this.metrics.aiResponseTimes.length > 100) {
      this.metrics.aiResponseTimes.shift();
    }
  }

  /**
   * Record metrics for batch requests
   */
  recordBatchMetrics(batchSize, latency, success) {
    if (success) {
      this.metrics.totalDataSent += batchSize;
      this.metrics.totalPredictions += batchSize;
    } else {
      this.metrics.errorCount += batchSize;
    }

    this.recordMetrics(latency / batchSize, success); // Average per item
  }

  /**
   * Generate unique request ID
   */
  generateRequestId() {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Generate unique connection ID
   */
  generateConnectionId() {
    return `conn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get current metrics
   */
  getMetrics() {
    return {
      ...this.metrics,
      performance: this.calculatePerformance(),
      connectionStatus: this.aiConnectionStatus,
      isConnected: this.isConnected,
      isStreaming: this.isStreaming,
      bufferSize: this.dataBuffer.length,
      activeConnections: this.streamingConnections.size
    };
  }

  /**
   * Get bridge status
   */
  getStatus() {
    const performance = this.calculatePerformance();
    const targets = this.config.performanceTargets;

    return {
      isConnected: this.isConnected,
      isStreaming: this.isStreaming,
      aiConnectionStatus: this.aiConnectionStatus,
      performance,
      targets,
      targetsMet: {
        latency: performance.averageLatency <= targets.maxLatency,
        throughput: performance.throughput >= targets.minThroughput,
        errorRate: performance.errorRate <= targets.maxErrorRate,
        overall: false
      },
      metrics: this.getMetrics(),
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Shutdown the bridge
   */
  async shutdown() {
    logger.info('Shutting down AI Data Bridge...');

    await this.stopStreaming();

    if (this.healthInterval) {
      clearInterval(this.healthInterval);
    }

    if (this.performanceInterval) {
      clearInterval(this.performanceInterval);
    }

    this.isConnected = false;
    this.aiConnectionStatus = 'disconnected';

    this.emit('shutdown', {
      timestamp: new Date().toISOString(),
      finalMetrics: this.getMetrics()
    });

    logger.info('AI Data Bridge shutdown complete');
  }
}

module.exports = AIDataBridge;