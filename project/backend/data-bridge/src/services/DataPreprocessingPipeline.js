/**
 * Level 3 Data Preprocessing Pipeline
 * High-performance real-time data preprocessing for AI consumption
 * Transforms MT5 tick data into AI-ready features with <50ms latency
 */

const EventEmitter = require('events');
const logger = require('../utils/logger');

class DataPreprocessingPipeline extends EventEmitter {
  constructor(config = {}) {
    super();
    this.config = {
      targetLatency: 10, // ms - Level 3 target: sub-10ms processing
      batchSize: 100,
      processingWindow: 1000, // ms
      maxCacheSize: 10000,
      enableRealTimeValidation: true,
      enableFeatureExtraction: true,
      enableAnomalyDetection: true,
      multiTenantIsolation: true,
      performanceTracking: true,
      ...config
    };

    this.isRunning = false;
    this.processingQueue = [];
    this.cache = new Map();
    this.tenantData = new Map();
    this.performanceMetrics = {
      processedTicks: 0,
      averageLatency: 0,
      maxLatency: 0,
      throughput: 0,
      errorRate: 0,
      cacheHitRate: 0,
      validationRate: 100,
      processingErrors: 0,
      lastProcessingTime: Date.now()
    };

    this.processors = {
      priceNormalization: this.createPriceNormalizer(),
      technicalIndicators: this.createTechnicalIndicatorProcessor(),
      volumeAnalysis: this.createVolumeAnalyzer(),
      marketSentiment: this.createSentimentAnalyzer(),
      patternDetection: this.createPatternDetector(),
      anomalyDetection: this.createAnomalyDetector()
    };

    this.validator = this.createDataValidator();
    this.featureExtractor = this.createFeatureExtractor();
    this.tenantIsolator = this.createTenantIsolator();
  }

  /**
   * Start the preprocessing pipeline
   */
  async start() {
    if (this.isRunning) {
      logger.warn('Data preprocessing pipeline is already running');
      return;
    }

    logger.info('Starting Level 3 data preprocessing pipeline...');
    this.isRunning = true;
    this.startPerformanceMonitoring();
    this.startProcessingLoop();

    this.emit('started', {
      timestamp: new Date().toISOString(),
      config: this.config
    });

    logger.info('Level 3 data preprocessing pipeline started successfully');
  }

  /**
   * Stop the preprocessing pipeline
   */
  async stop() {
    if (!this.isRunning) {
      return;
    }

    logger.info('Stopping Level 3 data preprocessing pipeline...');
    this.isRunning = false;

    if (this.processingInterval) {
      clearInterval(this.processingInterval);
    }
    if (this.performanceInterval) {
      clearInterval(this.performanceInterval);
    }

    this.emit('stopped', {
      timestamp: new Date().toISOString(),
      metrics: this.getMetrics()
    });

    logger.info('Level 3 data preprocessing pipeline stopped');
  }

  /**
   * Process incoming tick data with performance optimization
   */
  async processTickData(tickData, tenantId = 'default') {
    const startTime = process.hrtime.bigint();

    try {
      // Multi-tenant data isolation
      if (this.config.multiTenantIsolation) {
        tickData = this.tenantIsolator.isolateData(tickData, tenantId);
      }

      // Real-time validation
      if (this.config.enableRealTimeValidation) {
        const validationResult = await this.validator.validate(tickData);
        if (!validationResult.isValid) {
          this.recordProcessingError('validation_failed', validationResult.errors);
          return null;
        }
      }

      // Check cache for processed features
      const cacheKey = this.generateCacheKey(tickData, tenantId);
      if (this.cache.has(cacheKey)) {
        this.updateCacheHitRate(true);
        return this.cache.get(cacheKey);
      }

      // Process data through pipeline
      const processedData = await this.executeProcessingPipeline(tickData, tenantId);

      // Cache results for performance
      this.cache.set(cacheKey, processedData);
      this.maintainCache();
      this.updateCacheHitRate(false);

      // Record performance metrics
      const endTime = process.hrtime.bigint();
      const latency = Number(endTime - startTime) / 1000000; // Convert to ms
      this.recordProcessingMetrics(latency);

      // Emit processing event
      this.emit('dataProcessed', {
        tenantId,
        symbol: tickData.symbol,
        latency,
        features: Object.keys(processedData.features || {}).length,
        timestamp: new Date().toISOString()
      });

      return processedData;

    } catch (error) {
      const endTime = process.hrtime.bigint();
      const latency = Number(endTime - startTime) / 1000000;

      this.recordProcessingError('processing_failed', error.message);
      this.recordProcessingMetrics(latency, true);

      logger.error('Data processing failed:', error);
      return null;
    }
  }

  /**
   * Execute the complete processing pipeline
   */
  async executeProcessingPipeline(tickData, tenantId) {
    const pipelineStartTime = process.hrtime.bigint();

    // Step 1: Price normalization and standardization
    const normalizedData = await this.processors.priceNormalization.process(tickData);

    // Step 2: Technical indicators calculation
    const technicalData = await this.processors.technicalIndicators.process(normalizedData, tenantId);

    // Step 3: Volume analysis
    const volumeData = await this.processors.volumeAnalysis.process(normalizedData, tenantId);

    // Step 4: Market sentiment analysis
    const sentimentData = await this.processors.marketSentiment.process(normalizedData, tenantId);

    // Step 5: Pattern detection
    const patternData = await this.processors.patternDetection.process(normalizedData, tenantId);

    // Step 6: Anomaly detection
    let anomalyData = null;
    if (this.config.enableAnomalyDetection) {
      anomalyData = await this.processors.anomalyDetection.process(normalizedData, tenantId);
    }

    // Step 7: Feature extraction for AI models
    const aiFeatures = await this.featureExtractor.extractFeatures({
      normalized: normalizedData,
      technical: technicalData,
      volume: volumeData,
      sentiment: sentimentData,
      patterns: patternData,
      anomalies: anomalyData
    }, tenantId);

    const pipelineEndTime = process.hrtime.bigint();
    const pipelineLatency = Number(pipelineEndTime - pipelineStartTime) / 1000000;

    return {
      raw: tickData,
      normalized: normalizedData,
      technical: technicalData,
      volume: volumeData,
      sentiment: sentimentData,
      patterns: patternData,
      anomalies: anomalyData,
      features: aiFeatures,
      metadata: {
        tenantId,
        processingLatency: pipelineLatency,
        timestamp: new Date().toISOString(),
        pipeline: 'level3-preprocessing'
      }
    };
  }

  /**
   * Create price normalization processor
   */
  createPriceNormalizer() {
    return {
      process: async (tickData) => {
        const spread = tickData.ask - tickData.bid;
        const midPrice = (tickData.ask + tickData.bid) / 2;
        const spreadPercentage = (spread / midPrice) * 100;

        return {
          ...tickData,
          midPrice,
          spread,
          spreadPercentage,
          normalizedBid: this.normalizePrice(tickData.bid, tickData.symbol),
          normalizedAsk: this.normalizePrice(tickData.ask, tickData.symbol),
          priceDirection: this.calculatePriceDirection(tickData, tickData.symbol)
        };
      }
    };
  }

  /**
   * Create technical indicators processor
   */
  createTechnicalIndicatorProcessor() {
    return {
      process: async (normalizedData, tenantId) => {
        const symbol = normalizedData.symbol;
        const historicalData = this.getHistoricalData(symbol, tenantId, 20);

        if (historicalData.length < 5) {
          return { indicators: 'insufficient_data' };
        }

        return {
          sma5: this.calculateSMA(historicalData, 5),
          sma10: this.calculateSMA(historicalData, 10),
          sma20: this.calculateSMA(historicalData, 20),
          ema5: this.calculateEMA(historicalData, 5),
          ema12: this.calculateEMA(historicalData, 12),
          rsi: this.calculateRSI(historicalData, 14),
          macd: this.calculateMACD(historicalData),
          bollinger: this.calculateBollingerBands(historicalData, 20),
          momentum: this.calculateMomentum(historicalData, 10),
          stochastic: this.calculateStochastic(historicalData, 14)
        };
      }
    };
  }

  /**
   * Create volume analysis processor
   */
  createVolumeAnalyzer() {
    return {
      process: async (normalizedData, tenantId) => {
        const symbol = normalizedData.symbol;
        const volumeHistory = this.getVolumeHistory(symbol, tenantId, 10);

        return {
          currentVolume: normalizedData.volume || 0,
          averageVolume: this.calculateAverageVolume(volumeHistory),
          volumeRatio: this.calculateVolumeRatio(normalizedData.volume, volumeHistory),
          volumeTrend: this.calculateVolumeTrend(volumeHistory),
          vwap: this.calculateVWAP(symbol, tenantId)
        };
      }
    };
  }

  /**
   * Create market sentiment analyzer
   */
  createSentimentAnalyzer() {
    return {
      process: async (normalizedData, tenantId) => {
        return {
          priceVelocity: this.calculatePriceVelocity(normalizedData, tenantId),
          trendStrength: this.calculateTrendStrength(normalizedData, tenantId),
          volatility: this.calculateVolatility(normalizedData, tenantId),
          marketPhase: this.determineMarketPhase(normalizedData, tenantId)
        };
      }
    };
  }

  /**
   * Create pattern detection processor
   */
  createPatternDetector() {
    return {
      process: async (normalizedData, tenantId) => {
        const historicalData = this.getHistoricalData(normalizedData.symbol, tenantId, 50);

        return {
          candlestickPatterns: this.detectCandlestickPatterns(historicalData),
          chartPatterns: this.detectChartPatterns(historicalData),
          supportResistance: this.calculateSupportResistance(historicalData),
          fibonacci: this.calculateFibonacciLevels(historicalData)
        };
      }
    };
  }

  /**
   * Create anomaly detection processor
   */
  createAnomalyDetector() {
    return {
      process: async (normalizedData, tenantId) => {
        const historicalData = this.getHistoricalData(normalizedData.symbol, tenantId, 100);

        const priceAnomaly = this.detectPriceAnomaly(normalizedData, historicalData);
        const volumeAnomaly = this.detectVolumeAnomaly(normalizedData, historicalData);
        const spreadAnomaly = this.detectSpreadAnomaly(normalizedData, historicalData);

        return {
          priceAnomaly,
          volumeAnomaly,
          spreadAnomaly,
          overallRisk: Math.max(priceAnomaly.score, volumeAnomaly.score, spreadAnomaly.score),
          anomalyCount: [priceAnomaly, volumeAnomaly, spreadAnomaly].filter(a => a.detected).length
        };
      }
    };
  }

  /**
   * Create data validator
   */
  createDataValidator() {
    return {
      validate: async (tickData) => {
        const errors = [];

        // Basic structure validation
        if (!tickData.symbol) errors.push('Missing symbol');
        if (!tickData.bid || !tickData.ask) errors.push('Missing bid/ask prices');
        if (!tickData.timestamp) errors.push('Missing timestamp');

        // Price validation
        if (tickData.bid >= tickData.ask) errors.push('Bid >= Ask (invalid spread)');
        if (tickData.bid <= 0 || tickData.ask <= 0) errors.push('Invalid price values');

        // Timestamp validation
        const now = Date.now();
        const tickTime = new Date(tickData.timestamp).getTime();
        if (Math.abs(now - tickTime) > 60000) errors.push('Timestamp too old or future');

        // Symbol validation
        if (!/^[A-Z]{6}$/.test(tickData.symbol) && !/^[A-Z]{3,6}$/.test(tickData.symbol)) {
          errors.push('Invalid symbol format');
        }

        return {
          isValid: errors.length === 0,
          errors,
          score: Math.max(0, 100 - (errors.length * 25))
        };
      }
    };
  }

  /**
   * Create feature extractor for AI models
   */
  createFeatureExtractor() {
    return {
      extractFeatures: async (processedData, tenantId) => {
        const features = {};

        // Price features
        features.price_bid = processedData.normalized.bid;
        features.price_ask = processedData.normalized.ask;
        features.price_mid = processedData.normalized.midPrice;
        features.price_spread = processedData.normalized.spread;
        features.price_spread_pct = processedData.normalized.spreadPercentage;
        features.price_direction = processedData.normalized.priceDirection;

        // Technical indicator features
        if (processedData.technical && processedData.technical !== 'insufficient_data') {
          features.sma5 = processedData.technical.sma5;
          features.sma10 = processedData.technical.sma10;
          features.ema5 = processedData.technical.ema5;
          features.rsi = processedData.technical.rsi;
          features.macd_line = processedData.technical.macd?.line || 0;
          features.macd_signal = processedData.technical.macd?.signal || 0;
          features.bollinger_upper = processedData.technical.bollinger?.upper || 0;
          features.bollinger_lower = processedData.technical.bollinger?.lower || 0;
        }

        // Volume features
        if (processedData.volume) {
          features.volume_current = processedData.volume.currentVolume;
          features.volume_ratio = processedData.volume.volumeRatio;
          features.volume_trend = processedData.volume.volumeTrend;
          features.vwap = processedData.volume.vwap;
        }

        // Sentiment features
        if (processedData.sentiment) {
          features.price_velocity = processedData.sentiment.priceVelocity;
          features.trend_strength = processedData.sentiment.trendStrength;
          features.volatility = processedData.sentiment.volatility;
          features.market_phase = this.encodeMarketPhase(processedData.sentiment.marketPhase);
        }

        // Pattern features
        if (processedData.patterns) {
          features.pattern_count = Object.keys(processedData.patterns.candlestickPatterns || {}).length;
          features.support_level = processedData.patterns.supportResistance?.support || 0;
          features.resistance_level = processedData.patterns.supportResistance?.resistance || 0;
        }

        // Anomaly features
        if (processedData.anomalies) {
          features.anomaly_risk = processedData.anomalies.overallRisk;
          features.anomaly_count = processedData.anomalies.anomalyCount;
        }

        // Time-based features
        const timestamp = new Date(processedData.raw.timestamp);
        features.hour_of_day = timestamp.getHours();
        features.day_of_week = timestamp.getDay();
        features.is_market_open = this.isMarketOpen(timestamp, processedData.raw.symbol);

        return features;
      }
    };
  }

  /**
   * Create tenant data isolator
   */
  createTenantIsolator() {
    return {
      isolateData: (tickData, tenantId) => {
        // Add tenant context to data
        return {
          ...tickData,
          tenantId,
          tenantTimestamp: new Date().toISOString()
        };
      }
    };
  }

  // Helper methods for calculations
  normalizePrice(price, symbol) {
    // Simple normalization - can be enhanced with symbol-specific logic
    const basePrices = {
      'EURUSD': 1.0,
      'GBPUSD': 1.2,
      'USDJPY': 150,
      'AUDUSD': 0.67
    };
    const basePrice = basePrices[symbol] || 1.0;
    return price / basePrice;
  }

  calculatePriceDirection(tickData, symbol) {
    const historical = this.getHistoricalData(symbol, 'default', 2);
    if (historical.length < 2) return 0;

    const previous = historical[historical.length - 2];
    const current = tickData.midPrice || (tickData.bid + tickData.ask) / 2;
    const previousMid = (previous.bid + previous.ask) / 2;

    return current > previousMid ? 1 : (current < previousMid ? -1 : 0);
  }

  calculateSMA(data, periods) {
    if (data.length < periods) return null;
    const values = data.slice(-periods).map(d => (d.bid + d.ask) / 2);
    return values.reduce((a, b) => a + b, 0) / periods;
  }

  calculateEMA(data, periods) {
    if (data.length < periods) return null;
    const multiplier = 2 / (periods + 1);
    let ema = this.calculateSMA(data.slice(0, periods), periods);

    for (let i = periods; i < data.length; i++) {
      const price = (data[i].bid + data[i].ask) / 2;
      ema = (price * multiplier) + (ema * (1 - multiplier));
    }

    return ema;
  }

  calculateRSI(data, periods) {
    if (data.length < periods + 1) return null;

    const prices = data.map(d => (d.bid + d.ask) / 2);
    const gains = [];
    const losses = [];

    for (let i = 1; i < prices.length; i++) {
      const change = prices[i] - prices[i - 1];
      gains.push(change > 0 ? change : 0);
      losses.push(change < 0 ? Math.abs(change) : 0);
    }

    const avgGain = gains.slice(-periods).reduce((a, b) => a + b, 0) / periods;
    const avgLoss = losses.slice(-periods).reduce((a, b) => a + b, 0) / periods;

    if (avgLoss === 0) return 100;
    const rs = avgGain / avgLoss;
    return 100 - (100 / (1 + rs));
  }

  calculateMACD(data) {
    const ema12 = this.calculateEMA(data, 12);
    const ema26 = this.calculateEMA(data, 26);

    if (!ema12 || !ema26) return null;

    const macdLine = ema12 - ema26;
    return {
      line: macdLine,
      signal: macdLine * 0.9, // Simplified signal line
      histogram: macdLine * 0.1
    };
  }

  calculateBollingerBands(data, periods) {
    if (data.length < periods) return null;

    const sma = this.calculateSMA(data, periods);
    const prices = data.slice(-periods).map(d => (d.bid + d.ask) / 2);
    const variance = prices.reduce((sum, price) => sum + Math.pow(price - sma, 2), 0) / periods;
    const stdDev = Math.sqrt(variance);

    return {
      upper: sma + (stdDev * 2),
      middle: sma,
      lower: sma - (stdDev * 2)
    };
  }

  calculateMomentum(data, periods) {
    if (data.length < periods + 1) return null;
    const current = (data[data.length - 1].bid + data[data.length - 1].ask) / 2;
    const previous = (data[data.length - 1 - periods].bid + data[data.length - 1 - periods].ask) / 2;
    return ((current / previous) - 1) * 100;
  }

  calculateStochastic(data, periods) {
    if (data.length < periods) return null;

    const recentData = data.slice(-periods);
    const currentPrice = (data[data.length - 1].bid + data[data.length - 1].ask) / 2;
    const highest = Math.max(...recentData.map(d => d.ask));
    const lowest = Math.min(...recentData.map(d => d.bid));

    if (highest === lowest) return 50;
    return ((currentPrice - lowest) / (highest - lowest)) * 100;
  }

  // Additional helper methods
  getHistoricalData(symbol, tenantId, count) {
    const key = `${tenantId}:${symbol}:history`;
    if (!this.tenantData.has(key)) {
      this.tenantData.set(key, []);
    }
    return this.tenantData.get(key).slice(-count);
  }

  updateHistoricalData(tickData, tenantId) {
    const key = `${tenantId}:${tickData.symbol}:history`;
    if (!this.tenantData.has(key)) {
      this.tenantData.set(key, []);
    }
    const history = this.tenantData.get(key);
    history.push(tickData);
    if (history.length > 1000) {
      history.splice(0, 100); // Keep reasonable size
    }
  }

  generateCacheKey(tickData, tenantId) {
    return `${tenantId}:${tickData.symbol}:${tickData.timestamp}`;
  }

  maintainCache() {
    if (this.cache.size > this.config.maxCacheSize) {
      const keys = Array.from(this.cache.keys());
      const keysToDelete = keys.slice(0, Math.floor(this.config.maxCacheSize * 0.2));
      keysToDelete.forEach(key => this.cache.delete(key));
    }
  }

  recordProcessingMetrics(latency, isError = false) {
    this.performanceMetrics.processedTicks++;
    this.performanceMetrics.maxLatency = Math.max(this.performanceMetrics.maxLatency, latency);

    // Calculate rolling average latency
    const alpha = 0.1; // Smoothing factor
    this.performanceMetrics.averageLatency =
      (this.performanceMetrics.averageLatency * (1 - alpha)) + (latency * alpha);

    if (isError) {
      this.performanceMetrics.processingErrors++;
    }

    this.performanceMetrics.errorRate =
      (this.performanceMetrics.processingErrors / this.performanceMetrics.processedTicks) * 100;
  }

  updateCacheHitRate(wasHit) {
    const totalRequests = this.performanceMetrics.processedTicks;
    if (totalRequests === 0) return;

    // Update cache hit rate using exponential moving average
    const alpha = 0.1;
    const currentHitRate = wasHit ? 100 : 0;
    this.performanceMetrics.cacheHitRate =
      (this.performanceMetrics.cacheHitRate * (1 - alpha)) + (currentHitRate * alpha);
  }

  recordProcessingError(type, message) {
    logger.error(`Processing error [${type}]:`, message);
    this.performanceMetrics.processingErrors++;
  }

  startPerformanceMonitoring() {
    this.performanceInterval = setInterval(() => {
      const now = Date.now();
      const timeDiff = now - this.performanceMetrics.lastProcessingTime;

      if (timeDiff > 0) {
        this.performanceMetrics.throughput =
          (this.performanceMetrics.processedTicks / timeDiff) * 1000; // per second
      }

      this.emit('performanceMetrics', this.getMetrics());
      this.performanceMetrics.lastProcessingTime = now;
    }, 5000); // Every 5 seconds
  }

  startProcessingLoop() {
    this.processingInterval = setInterval(async () => {
      if (this.processingQueue.length > 0) {
        const batch = this.processingQueue.splice(0, this.config.batchSize);
        await this.processBatch(batch);
      }
    }, 10); // Process every 10ms for high frequency
  }

  async processBatch(batch) {
    const batchPromises = batch.map(item =>
      this.processTickData(item.data, item.tenantId)
    );

    try {
      await Promise.all(batchPromises);
    } catch (error) {
      logger.error('Batch processing error:', error);
    }
  }

  // Additional calculation methods (simplified implementations)
  getVolumeHistory(symbol, tenantId, count) {
    return this.getHistoricalData(symbol, tenantId, count)
      .map(d => d.volume || 0)
      .filter(v => v > 0);
  }

  calculateAverageVolume(volumeHistory) {
    if (volumeHistory.length === 0) return 0;
    return volumeHistory.reduce((a, b) => a + b, 0) / volumeHistory.length;
  }

  calculateVolumeRatio(currentVolume, volumeHistory) {
    const avgVolume = this.calculateAverageVolume(volumeHistory);
    return avgVolume > 0 ? currentVolume / avgVolume : 1;
  }

  calculateVolumeTrend(volumeHistory) {
    if (volumeHistory.length < 3) return 0;
    const recent = volumeHistory.slice(-3);
    return recent[2] > recent[1] && recent[1] > recent[0] ? 1 :
           (recent[2] < recent[1] && recent[1] < recent[0] ? -1 : 0);
  }

  calculateVWAP(symbol, tenantId) {
    const history = this.getHistoricalData(symbol, tenantId, 20);
    if (history.length === 0) return 0;

    let volumeWeightedSum = 0;
    let totalVolume = 0;

    history.forEach(tick => {
      const price = (tick.bid + tick.ask) / 2;
      const volume = tick.volume || 1;
      volumeWeightedSum += price * volume;
      totalVolume += volume;
    });

    return totalVolume > 0 ? volumeWeightedSum / totalVolume : 0;
  }

  calculatePriceVelocity(normalizedData, tenantId) {
    const history = this.getHistoricalData(normalizedData.symbol, tenantId, 5);
    if (history.length < 2) return 0;

    const current = normalizedData.midPrice;
    const previous = (history[history.length - 1].bid + history[history.length - 1].ask) / 2;
    const timeDiff = new Date(normalizedData.timestamp).getTime() -
                     new Date(history[history.length - 1].timestamp).getTime();

    return timeDiff > 0 ? (current - previous) / (timeDiff / 1000) : 0;
  }

  calculateTrendStrength(normalizedData, tenantId) {
    const sma5 = this.calculateSMA(this.getHistoricalData(normalizedData.symbol, tenantId, 5), 5);
    const sma20 = this.calculateSMA(this.getHistoricalData(normalizedData.symbol, tenantId, 20), 20);

    if (!sma5 || !sma20) return 0;
    return Math.abs(sma5 - sma20) / sma20;
  }

  calculateVolatility(normalizedData, tenantId) {
    const history = this.getHistoricalData(normalizedData.symbol, tenantId, 20);
    if (history.length < 2) return 0;

    const prices = history.map(d => (d.bid + d.ask) / 2);
    const mean = prices.reduce((a, b) => a + b, 0) / prices.length;
    const variance = prices.reduce((sum, price) => sum + Math.pow(price - mean, 2), 0) / prices.length;

    return Math.sqrt(variance);
  }

  determineMarketPhase(normalizedData, tenantId) {
    const volatility = this.calculateVolatility(normalizedData, tenantId);
    const trendStrength = this.calculateTrendStrength(normalizedData, tenantId);

    if (volatility > 0.01 && trendStrength > 0.005) return 'trending_volatile';
    if (volatility > 0.01) return 'ranging_volatile';
    if (trendStrength > 0.005) return 'trending_stable';
    return 'ranging_stable';
  }

  encodeMarketPhase(phase) {
    const phases = {
      'trending_volatile': 3,
      'ranging_volatile': 2,
      'trending_stable': 1,
      'ranging_stable': 0
    };
    return phases[phase] || 0;
  }

  isMarketOpen(timestamp, symbol) {
    // Simplified market hours check
    const hour = timestamp.getHours();
    const day = timestamp.getDay();

    // Weekend check
    if (day === 0 || day === 6) return false;

    // Basic trading hours (can be enhanced per symbol)
    return hour >= 1 && hour <= 23; // 24-hour forex market
  }

  // Pattern detection methods (simplified)
  detectCandlestickPatterns(historicalData) {
    // Simplified candlestick pattern detection
    return {
      doji: false,
      hammer: false,
      shootingStar: false,
      engulfing: false
    };
  }

  detectChartPatterns(historicalData) {
    return {
      doubleTop: false,
      doubleBottom: false,
      headAndShoulders: false,
      triangle: false
    };
  }

  calculateSupportResistance(historicalData) {
    if (historicalData.length < 10) return { support: 0, resistance: 0 };

    const prices = historicalData.map(d => (d.bid + d.ask) / 2);
    const support = Math.min(...prices);
    const resistance = Math.max(...prices);

    return { support, resistance };
  }

  calculateFibonacciLevels(historicalData) {
    if (historicalData.length < 2) return {};

    const prices = historicalData.map(d => (d.bid + d.ask) / 2);
    const high = Math.max(...prices);
    const low = Math.min(...prices);
    const diff = high - low;

    return {
      level_0: high,
      level_236: high - (diff * 0.236),
      level_382: high - (diff * 0.382),
      level_500: high - (diff * 0.500),
      level_618: high - (diff * 0.618),
      level_100: low
    };
  }

  detectPriceAnomaly(normalizedData, historicalData) {
    if (historicalData.length < 10) return { detected: false, score: 0 };

    const currentPrice = normalizedData.midPrice;
    const prices = historicalData.map(d => (d.bid + d.ask) / 2);
    const mean = prices.reduce((a, b) => a + b, 0) / prices.length;
    const stdDev = Math.sqrt(prices.reduce((sum, price) => sum + Math.pow(price - mean, 2), 0) / prices.length);

    const zScore = Math.abs((currentPrice - mean) / stdDev);
    const detected = zScore > 2; // 2 standard deviations

    return { detected, score: Math.min(100, zScore * 20) };
  }

  detectVolumeAnomaly(normalizedData, historicalData) {
    const currentVolume = normalizedData.volume || 0;
    const volumeHistory = historicalData.map(d => d.volume || 0).filter(v => v > 0);

    if (volumeHistory.length < 5) return { detected: false, score: 0 };

    const avgVolume = volumeHistory.reduce((a, b) => a + b, 0) / volumeHistory.length;
    const ratio = avgVolume > 0 ? currentVolume / avgVolume : 1;

    const detected = ratio > 3 || ratio < 0.1; // 3x higher or 10x lower
    return { detected, score: Math.min(100, Math.abs(ratio - 1) * 25) };
  }

  detectSpreadAnomaly(normalizedData, historicalData) {
    const currentSpread = normalizedData.spread;
    const spreads = historicalData.map(d => d.ask - d.bid);

    if (spreads.length < 5) return { detected: false, score: 0 };

    const avgSpread = spreads.reduce((a, b) => a + b, 0) / spreads.length;
    const ratio = avgSpread > 0 ? currentSpread / avgSpread : 1;

    const detected = ratio > 2 || ratio < 0.5; // 2x wider or 2x narrower
    return { detected, score: Math.min(100, Math.abs(ratio - 1) * 50) };
  }

  /**
   * Get current metrics
   */
  getMetrics() {
    return {
      ...this.performanceMetrics,
      isRunning: this.isRunning,
      queueSize: this.processingQueue.length,
      cacheSize: this.cache.size,
      tenantCount: this.tenantData.size,
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Add data to processing queue
   */
  queueForProcessing(tickData, tenantId = 'default') {
    this.processingQueue.push({ data: tickData, tenantId });

    // Update historical data immediately
    this.updateHistoricalData(tickData, tenantId);

    return this.processingQueue.length;
  }

  /**
   * Get processing status
   */
  getStatus() {
    return {
      isRunning: this.isRunning,
      metrics: this.getMetrics(),
      config: this.config,
      targets: {
        latency: this.config.targetLatency,
        throughput: 50, // TPS
        accuracy: 99.9, // %
        availability: 99.9 // %
      },
      performance: {
        latencyMet: this.performanceMetrics.averageLatency <= this.config.targetLatency,
        throughputMet: this.performanceMetrics.throughput >= 50,
        accuracyMet: this.performanceMetrics.errorRate <= 0.1,
        overallMet: false
      }
    };
  }
}

module.exports = DataPreprocessingPipeline;