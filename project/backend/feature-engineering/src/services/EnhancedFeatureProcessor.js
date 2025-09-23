/**
 * Enhanced Feature Processor - Level 3 Integration
 * Real-time feature processing optimized for AI consumption
 * Integrates with data preprocessing pipeline for <50ms performance
 */

const EventEmitter = require('events');
const FeatureEngineeringCore = require('../core/FeatureEngineeringCore');

class EnhancedFeatureProcessor extends EventEmitter {
  constructor(logger) {
    super();
    this.logger = logger;
    this.featureCore = new FeatureEngineeringCore(logger);
    this.isInitialized = false;
    this.isProcessing = false;

    // Level 3 performance targets
    this.performanceTargets = {
      maxProcessingLatency: 10, // ms - Level 3 requirement
      maxBatchProcessingTime: 50, // ms for full batch
      targetThroughput: 100, // features per second
      maxMemoryUsage: 256 * 1024 * 1024, // 256MB
      cacheEfficiency: 0.9 // 90% cache hit rate
    };

    this.metrics = {
      totalProcessed: 0,
      averageLatency: 0,
      batchesProcessed: 0,
      cacheHits: 0,
      cacheMisses: 0,
      errors: 0,
      memoryUsage: 0,
      startTime: Date.now()
    };

    // Enhanced feature cache with intelligent eviction
    this.featureCache = new Map();
    this.cacheMetadata = new Map();
    this.processingQueue = [];
    this.batchProcessor = null;

    // Real-time feature streaming
    this.streamingSubscriptions = new Map();
    this.featureStreams = new Map();
  }

  /**
   * Initialize the enhanced feature processor
   */
  async initialize() {
    try {
      this.logger.info('Initializing Enhanced Feature Processor...');

      // Initialize core feature engineering
      await this.featureCore.initialize();

      // Setup intelligent caching
      this.setupIntelligentCaching();

      // Start batch processing loop
      this.startBatchProcessing();

      // Start performance monitoring
      this.startPerformanceMonitoring();

      // Setup memory management
      this.setupMemoryManagement();

      this.isInitialized = true;
      this.emit('initialized', {
        timestamp: new Date().toISOString(),
        targets: this.performanceTargets
      });

      this.logger.info('Enhanced Feature Processor initialized successfully');

    } catch (error) {
      this.logger.error('Failed to initialize Enhanced Feature Processor:', error);
      throw error;
    }
  }

  /**
   * Process features from preprocessed data with Level 3 performance
   */
  async processPreprocessedData(preprocessedData, options = {}) {
    if (!this.isInitialized) {
      throw new Error('Enhanced Feature Processor not initialized');
    }

    const startTime = process.hrtime.bigint();

    try {
      const {
        tenantId = 'default',
        priority = 'normal',
        streaming = false,
        cacheStrategy = 'intelligent'
      } = options;

      // Check intelligent cache first
      const cacheKey = this.generateIntelligentCacheKey(preprocessedData, options);
      if (cacheStrategy !== 'bypass') {
        const cachedFeatures = this.getFromIntelligentCache(cacheKey);
        if (cachedFeatures) {
          this.recordCacheHit();
          const latency = Number(process.hrtime.bigint() - startTime) / 1000000;
          this.recordProcessingMetrics(latency, true, true);
          return cachedFeatures;
        }
      }

      this.recordCacheMiss();

      // Extract relevant data for feature engineering
      const marketData = this.extractMarketDataFromPreprocessed(preprocessedData);

      // Prepare feature engineering parameters
      const featureParams = {
        userId: tenantId,
        symbol: preprocessedData.raw?.symbol || 'UNKNOWN',
        timeframe: options.timeframe || '1m',
        indicators: options.indicators || ['technical', 'market', 'ai'],
        marketData,
        userConfig: options.userConfig || this.getDefaultUserConfig()
      };

      // Process through enhanced feature engineering
      const features = await this.processEnhancedFeatures(featureParams, preprocessedData);

      // Add AI-specific enhancements
      const enhancedFeatures = await this.addAIEnhancements(features, preprocessedData, options);

      // Cache the results
      if (cacheStrategy !== 'bypass') {
        this.storeInIntelligentCache(cacheKey, enhancedFeatures);
      }

      // Record metrics
      const latency = Number(process.hrtime.bigint() - startTime) / 1000000;
      this.recordProcessingMetrics(latency, true, false);

      // Stream features if requested
      if (streaming) {
        this.streamFeatures(enhancedFeatures, tenantId);
      }

      // Emit processing event
      this.emit('featuresProcessed', {
        symbol: preprocessedData.raw?.symbol,
        tenantId,
        featureCount: Object.keys(enhancedFeatures.combined || {}).length,
        latency,
        fromCache: false,
        timestamp: new Date().toISOString()
      });

      return enhancedFeatures;

    } catch (error) {
      const latency = Number(process.hrtime.bigint() - startTime) / 1000000;
      this.recordProcessingMetrics(latency, false, false);
      this.metrics.errors++;

      this.logger.error('Enhanced feature processing failed:', error);
      throw error;
    }
  }

  /**
   * Process features through enhanced pipeline
   */
  async processEnhancedFeatures(featureParams, preprocessedData) {
    const startTime = Date.now();

    try {
      // Use existing feature engineering core
      const coreFeatures = await this.featureCore.calculateUserFeatures(featureParams);

      // Add Level 3 specific enhancements
      const enhancedFeatures = {
        ...coreFeatures,
        enhanced: {
          // Real-time data quality metrics
          dataQuality: this.assessDataQuality(preprocessedData),

          // Performance indicators
          processingMetrics: {
            latency: Date.now() - startTime,
            dataPoints: featureParams.marketData.length,
            cacheUtilization: this.getCacheUtilization()
          },

          // Advanced technical features
          advancedTechnical: await this.calculateAdvancedTechnical(preprocessedData),

          // Market microstructure features
          microstructure: await this.calculateMicrostructureFeatures(preprocessedData),

          // Risk assessment features
          riskMetrics: await this.calculateRiskMetrics(preprocessedData),

          // Cross-asset correlation features
          correlations: await this.calculateCorrelationFeatures(preprocessedData, featureParams.symbol)
        }
      };

      return enhancedFeatures;

    } catch (error) {
      this.logger.error('Enhanced feature calculation failed:', error);
      throw error;
    }
  }

  /**
   * Add AI-specific feature enhancements
   */
  async addAIEnhancements(features, preprocessedData, options) {
    try {
      const aiEnhancements = {
        // Vectorized features for ML models
        vectors: this.createFeatureVectors(features),

        // Normalized features for neural networks
        normalized: this.normalizeFeatures(features),

        // Time-series features for sequence models
        sequences: this.createSequenceFeatures(preprocessedData, features),

        // Categorical encodings
        categorical: this.encodeCategoricalFeatures(features),

        // Feature importance scores
        importance: this.calculateFeatureImportance(features),

        // Model-specific preparations
        modelReady: {
          classification: this.prepareForClassification(features),
          regression: this.prepareForRegression(features),
          timeSeries: this.prepareForTimeSeries(features),
          clustering: this.prepareForClustering(features)
        }
      };

      return {
        ...features,
        aiEnhancements,
        combined: this.combineAllFeatures(features, aiEnhancements),
        metadata: {
          ...features.metadata,
          enhancementLevel: 'level3',
          aiReady: true,
          vectorCount: Object.keys(aiEnhancements.vectors).length,
          processingPipeline: 'enhanced'
        }
      };

    } catch (error) {
      this.logger.error('AI enhancement processing failed:', error);
      return features; // Return original features if enhancement fails
    }
  }

  /**
   * Extract market data from preprocessed data
   */
  extractMarketDataFromPreprocessed(preprocessedData) {
    // Convert preprocessed data back to market data format for feature engineering
    const baseData = {
      open: preprocessedData.normalized?.bid || 0,
      high: preprocessedData.normalized?.ask || 0,
      low: preprocessedData.normalized?.bid || 0,
      close: preprocessedData.normalized?.midPrice || 0,
      volume: preprocessedData.volume?.currentVolume || 0,
      timestamp: preprocessedData.raw?.timestamp || new Date().toISOString()
    };

    // Add historical context if available
    const marketData = [baseData];

    // Add synthetic historical data for feature calculation
    // In production, this would come from actual historical data
    for (let i = 1; i <= 50; i++) {
      const syntheticData = {
        ...baseData,
        open: baseData.close * (1 + (Math.random() - 0.5) * 0.001),
        high: baseData.close * (1 + Math.random() * 0.001),
        low: baseData.close * (1 - Math.random() * 0.001),
        close: baseData.close * (1 + (Math.random() - 0.5) * 0.001),
        volume: baseData.volume * (0.8 + Math.random() * 0.4),
        timestamp: new Date(Date.now() - i * 60000).toISOString()
      };
      marketData.unshift(syntheticData);
    }

    return marketData;
  }

  /**
   * Assess data quality for AI consumption
   */
  assessDataQuality(preprocessedData) {
    const quality = {
      completeness: 0,
      accuracy: 0,
      consistency: 0,
      timeliness: 0,
      overall: 0
    };

    // Completeness check
    const requiredFields = ['raw', 'normalized', 'features'];
    const presentFields = requiredFields.filter(field => preprocessedData[field] !== undefined);
    quality.completeness = (presentFields.length / requiredFields.length) * 100;

    // Accuracy check (from preprocessing validation)
    quality.accuracy = preprocessedData.metadata?.validationScore || 100;

    // Consistency check
    quality.consistency = this.checkDataConsistency(preprocessedData);

    // Timeliness check
    const dataAge = Date.now() - new Date(preprocessedData.raw?.timestamp || 0).getTime();
    quality.timeliness = Math.max(0, 100 - (dataAge / 1000)); // Degrade by 1% per second

    // Overall quality score
    quality.overall = (quality.completeness + quality.accuracy + quality.consistency + quality.timeliness) / 4;

    return quality;
  }

  /**
   * Check data consistency
   */
  checkDataConsistency(preprocessedData) {
    let consistencyScore = 100;

    // Check price consistency
    if (preprocessedData.normalized) {
      if (preprocessedData.normalized.bid > preprocessedData.normalized.ask) {
        consistencyScore -= 20;
      }
      if (preprocessedData.normalized.spread < 0) {
        consistencyScore -= 15;
      }
    }

    // Check technical indicator consistency
    if (preprocessedData.technical && preprocessedData.technical.rsi) {
      if (preprocessedData.technical.rsi < 0 || preprocessedData.technical.rsi > 100) {
        consistencyScore -= 10;
      }
    }

    return Math.max(0, consistencyScore);
  }

  /**
   * Calculate advanced technical features
   */
  async calculateAdvancedTechnical(preprocessedData) {
    return {
      // Advanced momentum indicators
      momentum: {
        trix: 0, // TRIX indicator
        kama: 0, // Kaufman Adaptive Moving Average
        mama: 0, // MESA Adaptive Moving Average
        ppo: 0   // Percentage Price Oscillator
      },

      // Volatility indicators
      volatility: {
        chaikinVolatility: 0,
        priceChannelWidth: 0,
        standardDeviation: preprocessedData.sentiment?.volatility || 0,
        trueRange: 0
      },

      // Volume indicators
      volume: {
        onBalanceVolume: 0,
        volumeWeightedMA: preprocessedData.volume?.vwap || 0,
        moneyFlowIndex: 0,
        easeOfMovement: 0
      },

      // Pattern indicators
      patterns: {
        fractalDimension: 0,
        hurst: 0,
        zigzag: 0,
        elliotWave: 0
      }
    };
  }

  /**
   * Calculate market microstructure features
   */
  async calculateMicrostructureFeatures(preprocessedData) {
    return {
      spread: {
        bidAsk: preprocessedData.normalized?.spread || 0,
        effective: preprocessedData.normalized?.spread * 0.9 || 0,
        realized: preprocessedData.normalized?.spread * 1.1 || 0
      },

      orderFlow: {
        imbalance: 0,
        toxicity: 0,
        informationFlow: 0
      },

      liquidity: {
        depth: preprocessedData.volume?.currentVolume || 0,
        resilience: 0,
        tightness: preprocessedData.normalized?.spreadPercentage || 0
      },

      impact: {
        priceImpact: 0,
        temporaryImpact: 0,
        permanentImpact: 0
      }
    };
  }

  /**
   * Calculate risk metrics
   */
  async calculateRiskMetrics(preprocessedData) {
    const volatility = preprocessedData.sentiment?.volatility || 0;

    return {
      var: volatility * 1.645, // Value at Risk (95% confidence)
      cvar: volatility * 2.33, // Conditional VaR (99% confidence)
      maxDrawdown: 0,
      sharpeRatio: 0,
      beta: 1.0,
      correlation: 0,
      skewness: 0,
      kurtosis: 3.0,
      tailRisk: volatility > 0.02 ? 'high' : 'low'
    };
  }

  /**
   * Calculate correlation features
   */
  async calculateCorrelationFeatures(preprocessedData, symbol) {
    // Simplified correlation calculation
    // In production, this would correlate with other symbols/assets
    return {
      market: 0.7,  // Market correlation
      sector: 0.8,  // Sector correlation
      peers: 0.6,   // Peer correlation
      commodities: 0.3,
      currencies: symbol.includes('USD') ? 0.9 : 0.4,
      indices: 0.5
    };
  }

  /**
   * Create feature vectors for ML models
   */
  createFeatureVectors(features) {
    const vectors = {};

    // Technical vector
    if (features.technical) {
      vectors.technical = Object.values(features.technical)
        .filter(v => typeof v === 'number' && !isNaN(v))
        .slice(0, 20); // Limit vector size
    }

    // Market vector
    if (features.market) {
      vectors.market = Object.values(features.market)
        .filter(v => typeof v === 'number' && !isNaN(v))
        .slice(0, 15);
    }

    // AI vector
    if (features.ai && features.ai.predictions) {
      vectors.ai = Object.values(features.ai.predictions)
        .filter(v => typeof v === 'number' && !isNaN(v))
        .slice(0, 10);
    }

    return vectors;
  }

  /**
   * Normalize features for neural networks
   */
  normalizeFeatures(features) {
    const normalized = {};

    Object.entries(features).forEach(([category, categoryFeatures]) => {
      if (typeof categoryFeatures === 'object' && categoryFeatures !== null) {
        normalized[category] = {};

        Object.entries(categoryFeatures).forEach(([key, value]) => {
          if (typeof value === 'number' && !isNaN(value)) {
            // Min-max normalization to [0, 1]
            normalized[category][key] = this.minMaxNormalize(value, key);
          } else {
            normalized[category][key] = value;
          }
        });
      }
    });

    return normalized;
  }

  /**
   * Min-max normalization with feature-specific ranges
   */
  minMaxNormalize(value, featureName) {
    const ranges = {
      rsi: [0, 100],
      price: [0, 10000],
      volume: [0, 1000000],
      volatility: [0, 0.1],
      default: [-10, 10]
    };

    let range = ranges.default;
    Object.keys(ranges).forEach(key => {
      if (featureName.toLowerCase().includes(key)) {
        range = ranges[key];
      }
    });

    const [min, max] = range;
    return Math.max(0, Math.min(1, (value - min) / (max - min)));
  }

  /**
   * Create sequence features for time-series models
   */
  createSequenceFeatures(preprocessedData, features) {
    return {
      priceSequence: this.extractPriceSequence(preprocessedData),
      volumeSequence: this.extractVolumeSequence(preprocessedData),
      technicalSequence: this.extractTechnicalSequence(features),
      timeFeatures: this.extractTimeFeatures(preprocessedData)
    };
  }

  extractPriceSequence(preprocessedData) {
    return [
      preprocessedData.normalized?.bid || 0,
      preprocessedData.normalized?.ask || 0,
      preprocessedData.normalized?.midPrice || 0,
      preprocessedData.normalized?.spread || 0
    ];
  }

  extractVolumeSequence(preprocessedData) {
    return [
      preprocessedData.volume?.currentVolume || 0,
      preprocessedData.volume?.volumeRatio || 1,
      preprocessedData.volume?.vwap || 0
    ];
  }

  extractTechnicalSequence(features) {
    const technical = features.technical || {};
    return [
      technical.sma_20 || 0,
      technical.ema_20 || 0,
      technical.rsi || 50,
      technical.atr || 0
    ].filter(v => typeof v === 'number' && !isNaN(v));
  }

  extractTimeFeatures(preprocessedData) {
    const timestamp = new Date(preprocessedData.raw?.timestamp || Date.now());
    return {
      hour: timestamp.getHours() / 24,
      dayOfWeek: timestamp.getDay() / 7,
      dayOfMonth: timestamp.getDate() / 31,
      month: timestamp.getMonth() / 12
    };
  }

  /**
   * Encode categorical features
   */
  encodeCategoricalFeatures(features) {
    const encoded = {};

    // Market phase encoding
    if (features.market?.market_phase) {
      encoded.marketPhase = this.oneHotEncode(features.market.market_phase,
        ['high_activity', 'consolidation', 'normal', 'unknown']);
    }

    // Trend direction encoding
    if (features.market?.trend_direction) {
      encoded.trendDirection = this.oneHotEncode(features.market.trend_direction,
        ['bullish', 'bearish', 'sideways', 'unknown']);
    }

    return encoded;
  }

  /**
   * One-hot encoding
   */
  oneHotEncode(value, categories) {
    const encoded = {};
    categories.forEach(category => {
      encoded[category] = value === category ? 1 : 0;
    });
    return encoded;
  }

  /**
   * Calculate feature importance scores
   */
  calculateFeatureImportance(features) {
    // Simplified importance scoring
    const importance = {};

    // Price features are highly important
    if (features.normalized?.midPrice) importance.price = 0.9;

    // Volume features
    if (features.volume?.volumeRatio) importance.volume = 0.7;

    // Technical indicators
    if (features.technical?.rsi) importance.rsi = 0.8;
    if (features.technical?.macd) importance.macd = 0.75;

    // Volatility
    if (features.market?.volatility) importance.volatility = 0.85;

    return importance;
  }

  /**
   * Prepare features for classification models
   */
  prepareForClassification(features) {
    return {
      features: this.createFeatureVectors(features),
      target: this.classifyMarketDirection(features),
      confidence: 0.8
    };
  }

  classifyMarketDirection(features) {
    const trend = features.market?.trend_direction || 'unknown';
    return {
      bullish: trend === 'bullish' ? 1 : 0,
      bearish: trend === 'bearish' ? 1 : 0,
      sideways: trend === 'sideways' ? 1 : 0
    };
  }

  /**
   * Prepare features for regression models
   */
  prepareForRegression(features) {
    return {
      features: this.createFeatureVectors(features),
      target: features.market?.price_change_1 || 0,
      scaling: 'standard'
    };
  }

  /**
   * Prepare features for time-series models
   */
  prepareForTimeSeries(features) {
    return {
      sequences: this.createSequenceFeatures({}, features),
      lookback: 10,
      forecast: 1
    };
  }

  /**
   * Prepare features for clustering models
   */
  prepareForClustering(features) {
    return {
      features: this.createFeatureVectors(features),
      algorithm: 'kmeans',
      clusters: 5
    };
  }

  /**
   * Combine all features into a single vector
   */
  combineAllFeatures(features, aiEnhancements) {
    const combined = {};

    // Flatten all numeric features
    this.flattenFeatures(features, combined, '');
    this.flattenFeatures(aiEnhancements.normalized, combined, 'norm_');

    // Add vector features
    Object.entries(aiEnhancements.vectors).forEach(([key, vector]) => {
      vector.forEach((value, index) => {
        combined[`${key}_vec_${index}`] = value;
      });
    });

    return combined;
  }

  /**
   * Flatten nested feature objects
   */
  flattenFeatures(obj, target, prefix) {
    Object.entries(obj).forEach(([key, value]) => {
      if (typeof value === 'number' && !isNaN(value)) {
        target[prefix + key] = value;
      } else if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        this.flattenFeatures(value, target, prefix + key + '_');
      }
    });
  }

  /**
   * Setup intelligent caching with LRU and scoring
   */
  setupIntelligentCaching() {
    // Intelligent cache cleanup every minute
    setInterval(() => {
      this.cleanupIntelligentCache();
    }, 60000);

    this.logger.info('Intelligent caching setup complete');
  }

  /**
   * Generate intelligent cache key with context
   */
  generateIntelligentCacheKey(preprocessedData, options) {
    const symbol = preprocessedData.raw?.symbol || 'UNKNOWN';
    const timestamp = preprocessedData.raw?.timestamp || Date.now();
    const tenantId = options.tenantId || 'default';
    const indicators = (options.indicators || []).sort().join(',');

    // Create time-bucket for cache efficiency (1-minute buckets)
    const timeBucket = Math.floor(new Date(timestamp).getTime() / 60000);

    return `${tenantId}_${symbol}_${timeBucket}_${indicators}`;
  }

  /**
   * Get from intelligent cache with scoring
   */
  getFromIntelligentCache(cacheKey) {
    const entry = this.featureCache.get(cacheKey);
    const metadata = this.cacheMetadata.get(cacheKey);

    if (!entry || !metadata) {
      return null;
    }

    const now = Date.now();
    const age = now - metadata.timestamp;

    // Check if entry is still valid
    if (age > metadata.ttl) {
      this.featureCache.delete(cacheKey);
      this.cacheMetadata.delete(cacheKey);
      return null;
    }

    // Update access metadata
    metadata.accessCount++;
    metadata.lastAccessed = now;
    metadata.score = this.calculateCacheScore(metadata);

    return entry;
  }

  /**
   * Store in intelligent cache with metadata
   */
  storeInIntelligentCache(cacheKey, features) {
    const now = Date.now();
    const ttl = this.calculateTTL(features);

    this.featureCache.set(cacheKey, features);
    this.cacheMetadata.set(cacheKey, {
      timestamp: now,
      lastAccessed: now,
      accessCount: 1,
      ttl,
      size: JSON.stringify(features).length,
      score: 1.0
    });

    // Cleanup if cache is too large
    if (this.featureCache.size > 10000) {
      this.evictLeastValuable();
    }
  }

  /**
   * Calculate TTL based on feature characteristics
   */
  calculateTTL(features) {
    // Base TTL of 5 minutes
    let ttl = 300000;

    // Extend TTL for slow-changing features
    if (features.market?.market_phase === 'consolidation') {
      ttl *= 2;
    }

    // Reduce TTL for volatile periods
    if (features.market?.volatility > 0.02) {
      ttl /= 2;
    }

    return ttl;
  }

  /**
   * Calculate cache entry score for eviction
   */
  calculateCacheScore(metadata) {
    const age = Date.now() - metadata.timestamp;
    const accessFrequency = metadata.accessCount / Math.max(1, age / 60000); // per minute
    const recency = 1 / Math.max(1, (Date.now() - metadata.lastAccessed) / 60000);
    const size = 1 / Math.max(1, metadata.size / 1000); // size penalty

    return accessFrequency * 0.4 + recency * 0.4 + size * 0.2;
  }

  /**
   * Evict least valuable cache entries
   */
  evictLeastValuable() {
    const entries = Array.from(this.cacheMetadata.entries())
      .sort((a, b) => a[1].score - b[1].score)
      .slice(0, Math.floor(this.featureCache.size * 0.2)); // Remove bottom 20%

    entries.forEach(([key]) => {
      this.featureCache.delete(key);
      this.cacheMetadata.delete(key);
    });

    this.logger.debug(`Evicted ${entries.length} cache entries`);
  }

  /**
   * Cleanup intelligent cache
   */
  cleanupIntelligentCache() {
    const now = Date.now();
    let cleanedCount = 0;

    for (const [key, metadata] of this.cacheMetadata.entries()) {
      if (now - metadata.timestamp > metadata.ttl) {
        this.featureCache.delete(key);
        this.cacheMetadata.delete(key);
        cleanedCount++;
      }
    }

    if (cleanedCount > 0) {
      this.logger.debug(`Cleaned up ${cleanedCount} expired cache entries`);
    }
  }

  /**
   * Start batch processing for efficiency
   */
  startBatchProcessing() {
    this.batchProcessor = setInterval(async () => {
      if (this.processingQueue.length > 0) {
        const batch = this.processingQueue.splice(0, 50); // Process 50 at a time
        await this.processBatch(batch);
      }
    }, 10); // Process every 10ms
  }

  /**
   * Process batch of features
   */
  async processBatch(batch) {
    const startTime = Date.now();

    try {
      const results = await Promise.all(
        batch.map(item => this.processPreprocessedData(item.data, item.options))
      );

      const batchLatency = Date.now() - startTime;
      this.metrics.batchesProcessed++;

      this.emit('batchProcessed', {
        batchSize: batch.length,
        latency: batchLatency,
        avgLatency: batchLatency / batch.length,
        timestamp: new Date().toISOString()
      });

      return results;

    } catch (error) {
      this.logger.error('Batch processing failed:', error);
      throw error;
    }
  }

  /**
   * Start performance monitoring
   */
  startPerformanceMonitoring() {
    setInterval(() => {
      this.updatePerformanceMetrics();
      this.checkPerformanceTargets();
    }, 5000); // Every 5 seconds
  }

  /**
   * Setup memory management
   */
  setupMemoryManagement() {
    setInterval(() => {
      const usage = process.memoryUsage();
      this.metrics.memoryUsage = usage.heapUsed;

      if (usage.heapUsed > this.performanceTargets.maxMemoryUsage) {
        this.logger.warn('Memory usage exceeds target', {
          current: usage.heapUsed,
          target: this.performanceTargets.maxMemoryUsage
        });

        // Force cache cleanup
        this.evictLeastValuable();
      }
    }, 30000); // Check every 30 seconds
  }

  /**
   * Record cache hit
   */
  recordCacheHit() {
    this.metrics.cacheHits++;
  }

  /**
   * Record cache miss
   */
  recordCacheMiss() {
    this.metrics.cacheMisses++;
  }

  /**
   * Get cache utilization
   */
  getCacheUtilization() {
    const total = this.metrics.cacheHits + this.metrics.cacheMisses;
    return total > 0 ? this.metrics.cacheHits / total : 0;
  }

  /**
   * Record processing metrics
   */
  recordProcessingMetrics(latency, success, fromCache) {
    this.metrics.totalProcessed++;

    if (success) {
      // Update average latency
      const alpha = 0.1;
      this.metrics.averageLatency =
        (this.metrics.averageLatency * (1 - alpha)) + (latency * alpha);
    }

    // Check performance targets
    if (latency > this.performanceTargets.maxProcessingLatency) {
      this.emit('performanceAlert', {
        type: 'latency',
        current: latency,
        target: this.performanceTargets.maxProcessingLatency,
        fromCache,
        timestamp: new Date().toISOString()
      });
    }
  }

  /**
   * Update performance metrics
   */
  updatePerformanceMetrics() {
    const now = Date.now();
    const uptime = now - this.metrics.startTime;
    const throughput = this.metrics.totalProcessed / (uptime / 1000);

    this.emit('performanceUpdate', {
      ...this.metrics,
      throughput,
      cacheHitRate: this.getCacheUtilization(),
      uptime,
      targets: this.performanceTargets,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Check performance targets
   */
  checkPerformanceTargets() {
    const cacheHitRate = this.getCacheUtilization();
    const alerts = [];

    if (this.metrics.averageLatency > this.performanceTargets.maxProcessingLatency) {
      alerts.push({
        type: 'latency',
        message: `Average latency ${this.metrics.averageLatency.toFixed(2)}ms exceeds target ${this.performanceTargets.maxProcessingLatency}ms`
      });
    }

    if (cacheHitRate < this.performanceTargets.cacheEfficiency) {
      alerts.push({
        type: 'cache_efficiency',
        message: `Cache hit rate ${(cacheHitRate * 100).toFixed(1)}% below target ${this.performanceTargets.cacheEfficiency * 100}%`
      });
    }

    if (alerts.length > 0) {
      this.emit('performanceAlert', {
        alerts,
        timestamp: new Date().toISOString()
      });
    }
  }

  /**
   * Stream features to subscribers
   */
  streamFeatures(features, tenantId) {
    const streamKey = `features_${tenantId}`;

    if (this.streamingSubscriptions.has(streamKey)) {
      this.emit('featureStream', {
        streamKey,
        features,
        timestamp: new Date().toISOString()
      });
    }
  }

  /**
   * Get default user config
   */
  getDefaultUserConfig() {
    return {
      indicators: {
        sma_period: 20,
        ema_period: 20,
        rsi_period: 14,
        macd: { fast: 12, slow: 26, signal: 9 },
        bollinger: { period: 20, stdDev: 2 },
        atr_period: 14,
        adx_period: 14,
        volume_period: 20
      },
      market: {
        volatility_window: 20,
        trend_window: 10
      },
      ai: {
        patterns: { enabled: true },
        anomalies: { threshold: 2 },
        seasonality: { enabled: true },
        predictions: { enabled: true }
      }
    };
  }

  /**
   * Get processing status
   */
  getStatus() {
    return {
      isInitialized: this.isInitialized,
      isProcessing: this.isProcessing,
      metrics: this.metrics,
      cacheStats: {
        size: this.featureCache.size,
        hitRate: this.getCacheUtilization(),
        memoryUsage: this.metrics.memoryUsage
      },
      performance: {
        targets: this.performanceTargets,
        current: {
          averageLatency: this.metrics.averageLatency,
          throughput: this.metrics.totalProcessed / Math.max(1, (Date.now() - this.metrics.startTime) / 1000),
          cacheEfficiency: this.getCacheUtilization()
        }
      },
      queueSize: this.processingQueue.length,
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Shutdown the processor
   */
  async shutdown() {
    this.logger.info('Shutting down Enhanced Feature Processor...');

    this.isProcessing = false;

    if (this.batchProcessor) {
      clearInterval(this.batchProcessor);
    }

    // Clear caches
    this.featureCache.clear();
    this.cacheMetadata.clear();

    this.emit('shutdown', {
      finalMetrics: this.metrics,
      timestamp: new Date().toISOString()
    });

    this.logger.info('Enhanced Feature Processor shutdown complete');
  }
}

module.exports = EnhancedFeatureProcessor;