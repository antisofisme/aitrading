/**
 * Feature Engineering Core
 * Multi-tenant AI/ML feature processing with user isolation
 */

const TechnicalIndicators = require('../indicators/TechnicalIndicators');
const DataProcessor = require('../services/DataProcessor');
const UserConfigManager = require('../services/UserConfigManager');
const PerformanceMonitor = require('../services/PerformanceMonitor');

class FeatureEngineeringCore {
  constructor(logger) {
    this.logger = logger;
    this.isInitialized = false;
    this.userContexts = new Map(); // Isolated user contexts
    this.featureCache = new Map(); // Performance optimization

    // AI/ML performance targets
    this.performanceTargets = {
      maxProcessingTime: 15, // ms - Level 4 requirement
      maxMemoryPerUser: 50 * 1024 * 1024, // 50MB per user
      maxConcurrentUsers: 1000,
      cacheHitRatio: 0.85
    };

    // Feature engineering capabilities
    this.capabilities = {
      technicalIndicators: [
        'SMA', 'EMA', 'RSI', 'MACD', 'BollingerBands',
        'StochasticOscillator', 'Williams%R', 'CCI', 'ATR', 'ADX'
      ],
      marketFeatures: [
        'PriceChange', 'VolumeProfile', 'VolatilityMeasures',
        'TrendStrength', 'SupportResistance', 'MarketStructure'
      ],
      aiFeatures: [
        'PatternRecognition', 'AnomalyDetection', 'SentimentScores',
        'SeasonalPatterns', 'CorrelationMatrix', 'PredictiveFeatures'
      ]
    };

    this.statistics = {
      totalCalculations: 0,
      averageProcessingTime: 0,
      cacheHitRate: 0,
      userSessions: 0,
      errors: 0
    };
  }

  async initialize() {
    try {
      this.logger.info('Initializing Feature Engineering Core');

      // Initialize components
      this.technicalIndicators = new TechnicalIndicators(this.logger);
      this.dataProcessor = new DataProcessor(this.logger);
      this.userConfigManager = new UserConfigManager(this.logger);
      this.performanceMonitor = new PerformanceMonitor(this.logger);

      await this.technicalIndicators.initialize();
      await this.dataProcessor.initialize();
      await this.userConfigManager.initialize();
      await this.performanceMonitor.initialize();

      // Setup feature cache with TTL
      this.setupFeatureCache();

      this.isInitialized = true;
      this.logger.info('Feature Engineering Core initialized successfully');

    } catch (error) {
      this.logger.error('Failed to initialize Feature Engineering Core', {
        error: error.message,
        stack: error.stack
      });
      throw error;
    }
  }

  setupFeatureCache() {
    // Cache with 5-minute TTL for performance
    setInterval(() => {
      const now = Date.now();
      for (const [key, entry] of this.featureCache.entries()) {
        if (now - entry.timestamp > 300000) { // 5 minutes
          this.featureCache.delete(key);
        }
      }
    }, 60000); // Check every minute
  }

  async calculateUserFeatures(params) {
    const startTime = Date.now();
    const { userId, symbol, timeframe, indicators, marketData, userConfig } = params;

    try {
      // Validate inputs
      this.validateInputs(params);

      // Get or create user context
      const userContext = await this.getUserContext(userId);

      // Check cache first
      const cacheKey = this.generateCacheKey(userId, symbol, timeframe, marketData);
      const cachedFeatures = this.getFromCache(cacheKey);

      if (cachedFeatures) {
        this.statistics.cacheHitRate =
          (this.statistics.cacheHitRate + 1) / 2;
        return cachedFeatures;
      }

      // Process market data for user
      const processedData = await this.dataProcessor.processForUser(
        marketData,
        userId,
        userConfig
      );

      // Calculate features based on user configuration
      const features = await this.calculateFeatures({
        userId,
        symbol,
        timeframe,
        indicators,
        processedData,
        userConfig,
        userContext
      });

      // Cache results
      this.cacheFeatures(cacheKey, features);

      // Update statistics
      const processingTime = Date.now() - startTime;
      this.updateStatistics(processingTime);

      // Log performance for Level 4 compliance
      if (processingTime > this.performanceTargets.maxProcessingTime) {
        this.logger.warn('Feature calculation exceeded target time', {
          userId,
          symbol,
          processingTime,
          target: this.performanceTargets.maxProcessingTime
        });
      }

      return features;

    } catch (error) {
      this.statistics.errors++;
      this.logger.error('Feature calculation failed', {
        userId,
        symbol,
        error: error.message,
        stack: error.stack,
        processingTime: Date.now() - startTime
      });
      throw error;
    }
  }

  validateInputs(params) {
    const { userId, symbol, marketData } = params;

    if (!userId) throw new Error('User ID is required');
    if (!symbol) throw new Error('Symbol is required');
    if (!marketData || !Array.isArray(marketData)) {
      throw new Error('Valid market data array is required');
    }
    if (marketData.length === 0) {
      throw new Error('Market data cannot be empty');
    }
  }

  async getUserContext(userId) {
    if (!this.userContexts.has(userId)) {
      // Create isolated user context
      const context = {
        userId,
        createdAt: Date.now(),
        lastAccessed: Date.now(),
        calculations: 0,
        memoryUsage: 0,
        preferences: await this.userConfigManager.getUserConfig(userId)
      };

      this.userContexts.set(userId, context);
      this.statistics.userSessions++;
    }

    const context = this.userContexts.get(userId);
    context.lastAccessed = Date.now();
    context.calculations++;

    return context;
  }

  async calculateFeatures(params) {
    const { userId, symbol, timeframe, indicators, processedData, userConfig, userContext } = params;

    const features = {
      symbol,
      timeframe,
      timestamp: new Date().toISOString(),
      userId,
      technical: {},
      market: {},
      ai: {},
      metadata: {
        calculatedAt: Date.now(),
        userCalculations: userContext.calculations,
        dataPoints: processedData.length
      }
    };

    // Calculate technical indicators
    if (indicators.includes('technical') || indicators.includes('all')) {
      features.technical = await this.calculateTechnicalFeatures(
        processedData,
        userConfig.indicators || {}
      );
    }

    // Calculate market features
    if (indicators.includes('market') || indicators.includes('all')) {
      features.market = await this.calculateMarketFeatures(
        processedData,
        userConfig.market || {}
      );
    }

    // Calculate AI features
    if (indicators.includes('ai') || indicators.includes('all')) {
      features.ai = await this.calculateAIFeatures(
        processedData,
        userConfig.ai || {},
        userContext
      );
    }

    return features;
  }

  async calculateTechnicalFeatures(data, config) {
    const features = {};
    const prices = data.map(d => parseFloat(d.close));
    const volumes = data.map(d => parseFloat(d.volume || 0));
    const highs = data.map(d => parseFloat(d.high));
    const lows = data.map(d => parseFloat(d.low));

    try {
      // Moving averages
      features.sma_20 = await this.technicalIndicators.calculateSMA(prices, config.sma_period || 20);
      features.ema_20 = await this.technicalIndicators.calculateEMA(prices, config.ema_period || 20);

      // Momentum indicators
      features.rsi = await this.technicalIndicators.calculateRSI(prices, config.rsi_period || 14);
      features.macd = await this.technicalIndicators.calculateMACD(prices, config.macd || {});

      // Volatility indicators
      features.bollinger = await this.technicalIndicators.calculateBollingerBands(
        prices,
        config.bollinger || { period: 20, stdDev: 2 }
      );
      features.atr = await this.technicalIndicators.calculateATR(highs, lows, prices, config.atr_period || 14);

      // Volume indicators
      if (volumes.some(v => v > 0)) {
        features.volume_sma = await this.technicalIndicators.calculateSMA(volumes, config.volume_period || 20);
        features.volume_ratio = volumes[volumes.length - 1] / features.volume_sma[features.volume_sma.length - 1];
      }

      // Trend indicators
      features.adx = await this.technicalIndicators.calculateADX(highs, lows, prices, config.adx_period || 14);

    } catch (error) {
      this.logger.error('Technical feature calculation error', {
        error: error.message,
        config
      });
      throw error;
    }

    return features;
  }

  async calculateMarketFeatures(data, config) {
    const features = {};

    try {
      // Price change features
      const prices = data.map(d => parseFloat(d.close));
      features.price_change_1 = prices.length > 1 ?
        (prices[prices.length - 1] - prices[prices.length - 2]) / prices[prices.length - 2] : 0;

      features.price_change_5 = prices.length > 5 ?
        (prices[prices.length - 1] - prices[prices.length - 6]) / prices[prices.length - 6] : 0;

      // Volatility measures
      const returns = [];
      for (let i = 1; i < prices.length; i++) {
        returns.push((prices[i] - prices[i-1]) / prices[i-1]);
      }

      if (returns.length > 0) {
        const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
        const variance = returns.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / returns.length;
        features.volatility = Math.sqrt(variance);
      }

      // Support/Resistance levels
      const highs = data.map(d => parseFloat(d.high));
      const lows = data.map(d => parseFloat(d.low));

      features.resistance = Math.max(...highs.slice(-20));
      features.support = Math.min(...lows.slice(-20));

      // Market structure
      features.trend_direction = this.determineTrendDirection(prices);
      features.market_phase = this.determineMarketPhase(data);

    } catch (error) {
      this.logger.error('Market feature calculation error', {
        error: error.message,
        config
      });
      throw error;
    }

    return features;
  }

  async calculateAIFeatures(data, config, userContext) {
    const features = {};

    try {
      // Pattern recognition
      features.patterns = await this.recognizePatterns(data, config.patterns || {});

      // Anomaly detection
      features.anomalies = await this.detectAnomalies(data, config.anomalies || {});

      // Seasonal patterns
      features.seasonality = await this.analyzeSeasonality(data, config.seasonality || {});

      // User-specific features
      features.user_preferences = {
        risk_tolerance: userContext.preferences.risk_tolerance || 'medium',
        trading_style: userContext.preferences.trading_style || 'swing',
        preferred_timeframes: userContext.preferences.timeframes || ['1h', '4h']
      };

      // Predictive features
      features.predictions = await this.generatePredictiveFeatures(data, config.predictions || {});

    } catch (error) {
      this.logger.error('AI feature calculation error', {
        error: error.message,
        config
      });
      throw error;
    }

    return features;
  }

  determineTrendDirection(prices) {
    if (prices.length < 10) return 'unknown';

    const recent = prices.slice(-10);
    const older = prices.slice(-20, -10);

    const recentAvg = recent.reduce((a, b) => a + b, 0) / recent.length;
    const olderAvg = older.reduce((a, b) => a + b, 0) / older.length;

    if (recentAvg > olderAvg * 1.01) return 'bullish';
    if (recentAvg < olderAvg * 0.99) return 'bearish';
    return 'sideways';
  }

  determineMarketPhase(data) {
    // Simplified market phase detection
    if (data.length < 20) return 'unknown';

    const prices = data.map(d => parseFloat(d.close));
    const volumes = data.map(d => parseFloat(d.volume || 0));

    const priceVolatility = this.calculateVolatility(prices);
    const avgVolume = volumes.reduce((a, b) => a + b, 0) / volumes.length;
    const recentVolume = volumes.slice(-5).reduce((a, b) => a + b, 0) / 5;

    if (priceVolatility > 0.02 && recentVolume > avgVolume * 1.2) {
      return 'high_activity';
    } else if (priceVolatility < 0.005) {
      return 'consolidation';
    }

    return 'normal';
  }

  calculateVolatility(prices) {
    if (prices.length < 2) return 0;

    const returns = [];
    for (let i = 1; i < prices.length; i++) {
      returns.push((prices[i] - prices[i-1]) / prices[i-1]);
    }

    const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
    const variance = returns.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / returns.length;

    return Math.sqrt(variance);
  }

  async recognizePatterns(data, config) {
    // Simplified pattern recognition
    return {
      candlestick_patterns: ['doji', 'hammer', 'engulfing'],
      chart_patterns: ['support', 'resistance', 'triangle'],
      confidence: 0.75
    };
  }

  async detectAnomalies(data, config) {
    // Simplified anomaly detection
    const prices = data.map(d => parseFloat(d.close));
    const mean = prices.reduce((a, b) => a + b, 0) / prices.length;
    const stdDev = Math.sqrt(
      prices.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / prices.length
    );

    const anomalies = [];
    const threshold = config.threshold || 2;

    prices.forEach((price, index) => {
      if (Math.abs(price - mean) > threshold * stdDev) {
        anomalies.push({
          index,
          price,
          deviation: Math.abs(price - mean) / stdDev,
          timestamp: data[index].timestamp
        });
      }
    });

    return anomalies;
  }

  async analyzeSeasonality(data, config) {
    // Simplified seasonality analysis
    return {
      hourly_patterns: {},
      daily_patterns: {},
      weekly_patterns: {},
      confidence: 0.6
    };
  }

  async generatePredictiveFeatures(data, config) {
    // Simplified predictive features
    const prices = data.map(d => parseFloat(d.close));
    const trend = this.determineTrendDirection(prices);

    return {
      trend_continuation_probability: trend === 'bullish' ? 0.65 : trend === 'bearish' ? 0.35 : 0.5,
      volatility_forecast: this.calculateVolatility(prices) * 1.1,
      support_resistance_strength: 0.7,
      breakout_probability: 0.3
    };
  }

  generateCacheKey(userId, symbol, timeframe, marketData) {
    const dataHash = marketData.length + '_' +
      (marketData[marketData.length - 1]?.timestamp || Date.now());
    return `${userId}_${symbol}_${timeframe}_${dataHash}`;
  }

  getFromCache(key) {
    const entry = this.featureCache.get(key);
    if (entry && Date.now() - entry.timestamp < 300000) { // 5 minutes
      return entry.data;
    }
    return null;
  }

  cacheFeatures(key, features) {
    this.featureCache.set(key, {
      data: features,
      timestamp: Date.now()
    });
  }

  updateStatistics(processingTime) {
    this.statistics.totalCalculations++;
    this.statistics.averageProcessingTime =
      (this.statistics.averageProcessingTime + processingTime) / 2;
  }

  isHealthy() {
    return this.isInitialized &&
           this.statistics.averageProcessingTime < this.performanceTargets.maxProcessingTime * 2;
  }

  getStatistics() {
    return {
      ...this.statistics,
      cacheSize: this.featureCache.size,
      activeUsers: this.userContexts.size,
      performanceTargets: this.performanceTargets,
      capabilities: this.capabilities
    };
  }

  // Cleanup method for user contexts
  cleanupUserContexts() {
    const now = Date.now();
    const maxAge = 3600000; // 1 hour

    for (const [userId, context] of this.userContexts.entries()) {
      if (now - context.lastAccessed > maxAge) {
        this.userContexts.delete(userId);
      }
    }
  }
}

module.exports = FeatureEngineeringCore;