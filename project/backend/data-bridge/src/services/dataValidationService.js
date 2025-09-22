/**
 * Level 3 Data Validation Service
 * Comprehensive data validation and quality assurance for Level 3 requirements
 */

const EventEmitter = require('events');
const logger = require('../utils/logger');

class DataValidationService extends EventEmitter {
  constructor(config = {}) {
    super();
    this.config = {
      enableRealTimeValidation: true,
      enableAnomalyDetection: true,
      maxInvalidDataThreshold: 10, // Max invalid data points before alert
      dataFreshnessThreshold: 2000, // 2 seconds
      priceVolatilityThreshold: 0.05, // 5% price volatility threshold
      ...config
    };

    this.validationMetrics = {
      totalValidations: 0,
      invalidDataCount: 0,
      anomaliesDetected: 0,
      lastValidation: null,
      validationRate: 0
    };

    this.dataQualityHistory = [];
    this.priceHistory = new Map(); // Symbol -> recent prices
    this.alertThresholds = new Map(); // Symbol -> thresholds

    this.initializeValidationRules();
  }

  initializeValidationRules() {
    // Level 3: Define validation rules for different data types
    this.validationRules = {
      tick: {
        required: ['symbol', 'bid', 'ask', 'timestamp'],
        validators: [
          this.validatePriceFormat.bind(this),
          this.validateSpread.bind(this),
          this.validateTimestamp.bind(this),
          this.validatePriceMovement.bind(this)
        ]
      },
      quote: {
        required: ['symbol', 'bid', 'ask', 'timestamp'],
        validators: [
          this.validatePriceFormat.bind(this),
          this.validateSpread.bind(this),
          this.validateTimestamp.bind(this)
        ]
      },
      bar: {
        required: ['symbol', 'open', 'high', 'low', 'close', 'volume', 'timestamp'],
        validators: [
          this.validateOHLCConsistency.bind(this),
          this.validateVolume.bind(this),
          this.validateTimestamp.bind(this)
        ]
      }
    };

    // Initialize price thresholds for major currency pairs
    this.initializePriceThresholds();
  }

  initializePriceThresholds() {
    const defaultThresholds = {
      'EURUSD': { min: 0.9000, max: 1.5000, maxSpread: 0.0050 },
      'GBPUSD': { min: 1.0000, max: 2.0000, maxSpread: 0.0050 },
      'USDJPY': { min: 100.00, max: 200.00, maxSpread: 0.050 },
      'AUDUSD': { min: 0.5000, max: 1.0000, maxSpread: 0.0050 },
      'USDCAD': { min: 1.0000, max: 1.8000, maxSpread: 0.0050 },
      'XAUUSD': { min: 1500.00, max: 3000.00, maxSpread: 1.00 },
      'BTCUSD': { min: 20000.00, max: 100000.00, maxSpread: 50.00 }
    };

    Object.entries(defaultThresholds).forEach(([symbol, thresholds]) => {
      this.alertThresholds.set(symbol, thresholds);
    });
  }

  /**
   * Level 3: Validate incoming market data
   * @param {Object} data - Market data to validate
   * @param {string} dataType - Type of data (tick, quote, bar)
   * @returns {Object} Validation result
   */
  async validateData(data, dataType = 'tick') {
    const startTime = process.hrtime.bigint();

    try {
      this.validationMetrics.totalValidations++;

      const validationResult = {
        isValid: true,
        errors: [],
        warnings: [],
        dataType,
        timestamp: new Date().toISOString(),
        processingTime: 0
      };

      // Check if data type is supported
      if (!this.validationRules[dataType]) {
        validationResult.isValid = false;
        validationResult.errors.push(`Unsupported data type: ${dataType}`);
        return validationResult;
      }

      const rules = this.validationRules[dataType];

      // Validate required fields
      const missingFields = rules.required.filter(field =>
        data[field] === undefined || data[field] === null
      );

      if (missingFields.length > 0) {
        validationResult.isValid = false;
        validationResult.errors.push(`Missing required fields: ${missingFields.join(', ')}`);
      }

      // Run specific validators
      for (const validator of rules.validators) {
        try {
          const result = await validator(data);
          if (!result.isValid) {
            validationResult.isValid = false;
            validationResult.errors.push(...result.errors);
            validationResult.warnings.push(...result.warnings);
          }
        } catch (error) {
          logger.error(`Validation error in ${validator.name}:`, error);
          validationResult.warnings.push(`Validator ${validator.name} failed: ${error.message}`);
        }
      }

      // Real-time anomaly detection
      if (this.config.enableAnomalyDetection) {
        const anomalyResult = this.detectAnomalies(data, dataType);
        if (anomalyResult.hasAnomalies) {
          validationResult.warnings.push(...anomalyResult.anomalies);
          this.validationMetrics.anomaliesDetected++;
        }
      }

      // Update validation metrics
      if (!validationResult.isValid) {
        this.validationMetrics.invalidDataCount++;
      }

      // Calculate processing time
      const endTime = process.hrtime.bigint();
      validationResult.processingTime = Number(endTime - startTime) / 1000000; // Convert to milliseconds

      // Update price history for trend analysis
      this.updatePriceHistory(data);

      // Check validation rate and emit alerts if needed
      this.checkValidationThresholds(validationResult);

      this.validationMetrics.lastValidation = validationResult;

      // Emit validation event
      this.emit('dataValidated', {
        data,
        validationResult,
        metrics: this.getValidationMetrics()
      });

      return validationResult;

    } catch (error) {
      logger.error('Data validation error:', error);
      this.validationMetrics.invalidDataCount++;

      return {
        isValid: false,
        errors: [`Validation system error: ${error.message}`],
        warnings: [],
        dataType,
        timestamp: new Date().toISOString(),
        processingTime: 0
      };
    }
  }

  validatePriceFormat(data) {
    const result = { isValid: true, errors: [], warnings: [] };

    // Validate bid/ask are numbers and positive
    if (data.bid !== undefined) {
      if (typeof data.bid !== 'number' || data.bid <= 0) {
        result.isValid = false;
        result.errors.push('Bid price must be a positive number');
      }
    }

    if (data.ask !== undefined) {
      if (typeof data.ask !== 'number' || data.ask <= 0) {
        result.isValid = false;
        result.errors.push('Ask price must be a positive number');
      }
    }

    // Validate OHLC for bar data
    if (data.open !== undefined && (typeof data.open !== 'number' || data.open <= 0)) {
      result.isValid = false;
      result.errors.push('Open price must be a positive number');
    }

    return result;
  }

  validateSpread(data) {
    const result = { isValid: true, errors: [], warnings: [] };

    if (data.bid !== undefined && data.ask !== undefined) {
      const spread = data.ask - data.bid;

      // Basic spread validation
      if (spread < 0) {
        result.isValid = false;
        result.errors.push('Ask price cannot be lower than bid price');
      }

      // Check against symbol-specific thresholds
      const thresholds = this.alertThresholds.get(data.symbol);
      if (thresholds && spread > thresholds.maxSpread) {
        result.warnings.push(`Spread ${spread.toFixed(5)} exceeds threshold ${thresholds.maxSpread}`);
      }

      // Check for zero spread (suspicious)
      if (spread === 0) {
        result.warnings.push('Zero spread detected - may indicate stale data');
      }
    }

    return result;
  }

  validateTimestamp(data) {
    const result = { isValid: true, errors: [], warnings: [] };
    const now = Date.now();

    if (data.timestamp) {
      const tickTime = new Date(data.timestamp).getTime();

      if (isNaN(tickTime)) {
        result.isValid = false;
        result.errors.push('Invalid timestamp format');
        return result;
      }

      const timeDiff = Math.abs(now - tickTime);

      // Check for future timestamps
      if (tickTime > now + 1000) { // 1 second tolerance
        result.isValid = false;
        result.errors.push('Timestamp cannot be in the future');
      }

      // Check for stale data
      if (timeDiff > this.config.dataFreshnessThreshold) {
        result.warnings.push(`Data is ${timeDiff}ms old (threshold: ${this.config.dataFreshnessThreshold}ms)`);
      }
    }

    return result;
  }

  validatePriceMovement(data) {
    const result = { isValid: true, errors: [], warnings: [] };

    if (!data.symbol || !this.priceHistory.has(data.symbol)) {
      return result; // No history to compare against
    }

    const history = this.priceHistory.get(data.symbol);
    if (history.length === 0) {
      return result;
    }

    const lastPrice = history[history.length - 1];
    const currentPrice = data.bid || data.close || data.open;

    if (lastPrice && currentPrice) {
      const priceChange = Math.abs(currentPrice - lastPrice) / lastPrice;

      if (priceChange > this.config.priceVolatilityThreshold) {
        result.warnings.push(
          `High price volatility detected: ${(priceChange * 100).toFixed(2)}% change`
        );
      }

      // Check for suspicious price jumps (>10% instant change)
      if (priceChange > 0.10) {
        result.warnings.push(
          `Suspicious price jump: ${(priceChange * 100).toFixed(2)}% change`
        );
      }
    }

    return result;
  }

  validateOHLCConsistency(data) {
    const result = { isValid: true, errors: [], warnings: [] };

    const { open, high, low, close } = data;

    if (open !== undefined && high !== undefined && low !== undefined && close !== undefined) {
      // High should be highest
      if (high < Math.max(open, close, low)) {
        result.isValid = false;
        result.errors.push('High price is not the highest value in OHLC');
      }

      // Low should be lowest
      if (low > Math.min(open, close, high)) {
        result.isValid = false;
        result.errors.push('Low price is not the lowest value in OHLC');
      }

      // Open and close should be within high/low range
      if (open < low || open > high) {
        result.isValid = false;
        result.errors.push('Open price is outside high/low range');
      }

      if (close < low || close > high) {
        result.isValid = false;
        result.errors.push('Close price is outside high/low range');
      }
    }

    return result;
  }

  validateVolume(data) {
    const result = { isValid: true, errors: [], warnings: [] };

    if (data.volume !== undefined) {
      if (typeof data.volume !== 'number' || data.volume < 0) {
        result.isValid = false;
        result.errors.push('Volume must be a non-negative number');
      }

      // Warning for zero volume
      if (data.volume === 0) {
        result.warnings.push('Zero volume detected');
      }
    }

    return result;
  }

  detectAnomalies(data, dataType) {
    const anomalies = [];

    // Price range anomaly detection
    if (data.symbol && this.alertThresholds.has(data.symbol)) {
      const thresholds = this.alertThresholds.get(data.symbol);
      const price = data.bid || data.ask || data.close || data.open;

      if (price && (price < thresholds.min || price > thresholds.max)) {
        anomalies.push(`Price ${price} outside expected range [${thresholds.min}, ${thresholds.max}]`);
      }
    }

    // Pattern-based anomaly detection
    if (this.priceHistory.has(data.symbol)) {
      const history = this.priceHistory.get(data.symbol);

      // Detect repeated identical prices (possible stuck feed)
      if (history.length >= 5) {
        const lastFive = history.slice(-5);
        if (lastFive.every(price => price === lastFive[0])) {
          anomalies.push('Possible stuck data feed - identical prices detected');
        }
      }
    }

    return {
      hasAnomalies: anomalies.length > 0,
      anomalies
    };
  }

  updatePriceHistory(data) {
    if (!data.symbol) return;

    const price = data.bid || data.close || data.open;
    if (!price) return;

    if (!this.priceHistory.has(data.symbol)) {
      this.priceHistory.set(data.symbol, []);
    }

    const history = this.priceHistory.get(data.symbol);
    history.push(price);

    // Keep only last 100 prices for efficiency
    if (history.length > 100) {
      history.shift();
    }
  }

  checkValidationThresholds(validationResult) {
    // Check if invalid data threshold is exceeded
    const invalidRate = this.validationMetrics.invalidDataCount / this.validationMetrics.totalValidations;

    if (invalidRate > (this.config.maxInvalidDataThreshold / 100)) {
      this.emit('validationThresholdExceeded', {
        invalidRate: invalidRate * 100,
        threshold: this.config.maxInvalidDataThreshold,
        totalValidations: this.validationMetrics.totalValidations,
        invalidCount: this.validationMetrics.invalidDataCount
      });
    }

    // Emit critical alert for severe validation failures
    if (!validationResult.isValid && validationResult.errors.length > 2) {
      this.emit('criticalValidationFailure', validationResult);
    }
  }

  getValidationMetrics() {
    const validationRate = this.validationMetrics.totalValidations > 0 ?
      ((this.validationMetrics.totalValidations - this.validationMetrics.invalidDataCount) /
       this.validationMetrics.totalValidations) * 100 : 100;

    return {
      ...this.validationMetrics,
      validationRate: Number(validationRate.toFixed(2)),
      invalidRate: Number(((this.validationMetrics.invalidDataCount /
                           (this.validationMetrics.totalValidations || 1)) * 100).toFixed(2))
    };
  }

  // Level 3: Real-time validation endpoint
  async validateRealTimeData(dataStream) {
    const results = [];

    for (const dataPoint of dataStream) {
      const result = await this.validateData(dataPoint.data, dataPoint.type);
      results.push({
        ...dataPoint,
        validation: result
      });
    }

    return {
      totalItems: results.length,
      validItems: results.filter(r => r.validation.isValid).length,
      invalidItems: results.filter(r => !r.validation.isValid).length,
      results,
      summary: this.getValidationMetrics()
    };
  }

  // Reset validation metrics
  resetMetrics() {
    this.validationMetrics = {
      totalValidations: 0,
      invalidDataCount: 0,
      anomaliesDetected: 0,
      lastValidation: null,
      validationRate: 0
    };

    this.dataQualityHistory = [];
    this.priceHistory.clear();
  }
}

module.exports = DataValidationService;