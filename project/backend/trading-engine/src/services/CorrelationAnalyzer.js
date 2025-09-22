const EventEmitter = require('events');
const { FOREX_PAIRS } = require('../config/forexPairs');
const { PRECIOUS_METALS } = require('../config/goldConfig');
const math = require('mathjs');
const logger = require('../utils/logger');

class CorrelationAnalyzer extends EventEmitter {
  constructor(options = {}) {
    super();
    this.priceHistory = new Map(); // Store price history for each symbol
    this.correlationMatrix = new Map();
    this.updateInterval = options.updateInterval || 60000; // 1 minute
    this.historyLength = options.historyLength || 100; // 100 periods
    this.minDataPoints = options.minDataPoints || 20;
    this.correlationThreshold = options.correlationThreshold || 0.7;
    
    this.startCorrelationUpdates();
  }

  /**
   * Add price data for correlation analysis
   */
  addPriceData(symbol, price, timestamp = Date.now()) {
    if (!this.priceHistory.has(symbol)) {
      this.priceHistory.set(symbol, []);
    }

    const history = this.priceHistory.get(symbol);
    history.push({ price, timestamp });

    // Maintain history length
    if (history.length > this.historyLength) {
      history.shift();
    }

    // Update correlations if we have enough data
    if (history.length >= this.minDataPoints) {
      this.updateCorrelations(symbol);
    }
  }

  /**
   * Calculate correlation between two price series
   */
  calculateCorrelation(series1, series2) {
    if (series1.length !== series2.length || series1.length < this.minDataPoints) {
      return null;
    }

    try {
      // Calculate returns
      const returns1 = this.calculateReturns(series1);
      const returns2 = this.calculateReturns(series2);

      if (returns1.length === 0 || returns2.length === 0) {
        return null;
      }

      // Calculate correlation coefficient
      const correlation = this.pearsonCorrelation(returns1, returns2);
      return correlation;
    } catch (error) {
      logger.error('Error calculating correlation:', error);
      return null;
    }
  }

  /**
   * Calculate price returns from price series
   */
  calculateReturns(priceSeries) {
    const returns = [];
    for (let i = 1; i < priceSeries.length; i++) {
      const currentPrice = priceSeries[i].price;
      const previousPrice = priceSeries[i - 1].price;
      
      if (previousPrice && previousPrice !== 0) {
        const returnValue = (currentPrice - previousPrice) / previousPrice;
        returns.push(returnValue);
      }
    }
    return returns;
  }

  /**
   * Calculate Pearson correlation coefficient
   */
  pearsonCorrelation(x, y) {
    const n = Math.min(x.length, y.length);
    if (n === 0) return 0;

    const sumX = x.slice(0, n).reduce((a, b) => a + b, 0);
    const sumY = y.slice(0, n).reduce((a, b) => a + b, 0);
    const sumXY = x.slice(0, n).reduce((sum, xi, i) => sum + xi * y[i], 0);
    const sumX2 = x.slice(0, n).reduce((sum, xi) => sum + xi * xi, 0);
    const sumY2 = y.slice(0, n).reduce((sum, yi) => sum + yi * yi, 0);

    const numerator = n * sumXY - sumX * sumY;
    const denominator = Math.sqrt((n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY));

    return denominator === 0 ? 0 : numerator / denominator;
  }

  /**
   * Update correlations for a specific symbol
   */
  updateCorrelations(symbol) {
    const symbolHistory = this.priceHistory.get(symbol);
    if (!symbolHistory || symbolHistory.length < this.minDataPoints) {
      return;
    }

    // Calculate correlations with all other symbols
    for (const [otherSymbol, otherHistory] of this.priceHistory.entries()) {
      if (symbol !== otherSymbol && otherHistory.length >= this.minDataPoints) {
        const correlation = this.calculateCorrelation(symbolHistory, otherHistory);
        
        if (correlation !== null) {
          const pairKey = this.getPairKey(symbol, otherSymbol);
          const previousCorrelation = this.correlationMatrix.get(pairKey);
          
          this.correlationMatrix.set(pairKey, {
            correlation,
            symbol1: symbol,
            symbol2: otherSymbol,
            lastUpdated: Date.now(),
            strength: this.getCorrelationStrength(correlation),
            direction: correlation > 0 ? 'positive' : 'negative'
          });

          // Emit correlation change event if significant
          if (previousCorrelation && Math.abs(correlation - previousCorrelation.correlation) > 0.1) {
            this.emit('correlationChange', {
              symbol1: symbol,
              symbol2: otherSymbol,
              oldCorrelation: previousCorrelation.correlation,
              newCorrelation: correlation,
              change: correlation - previousCorrelation.correlation
            });
          }

          // Emit high correlation alert
          if (Math.abs(correlation) > this.correlationThreshold) {
            this.emit('highCorrelation', {
              symbol1: symbol,
              symbol2: otherSymbol,
              correlation,
              strength: this.getCorrelationStrength(correlation)
            });
          }
        }
      }
    }
  }

  /**
   * Get correlation strength classification
   */
  getCorrelationStrength(correlation) {
    const abs = Math.abs(correlation);
    if (abs >= 0.8) return 'very_strong';
    if (abs >= 0.6) return 'strong';
    if (abs >= 0.4) return 'moderate';
    if (abs >= 0.2) return 'weak';
    return 'very_weak';
  }

  /**
   * Generate unique pair key for correlation matrix
   */
  getPairKey(symbol1, symbol2) {
    return [symbol1, symbol2].sort().join('-');
  }

  /**
   * Get correlation between two symbols
   */
  getCorrelation(symbol1, symbol2) {
    const pairKey = this.getPairKey(symbol1, symbol2);
    return this.correlationMatrix.get(pairKey);
  }

  /**
   * Get all correlations for a symbol
   */
  getSymbolCorrelations(symbol) {
    const correlations = [];
    
    for (const [pairKey, correlationData] of this.correlationMatrix.entries()) {
      if (correlationData.symbol1 === symbol || correlationData.symbol2 === symbol) {
        correlations.push({
          ...correlationData,
          otherSymbol: correlationData.symbol1 === symbol ? correlationData.symbol2 : correlationData.symbol1
        });
      }
    }

    return correlations.sort((a, b) => Math.abs(b.correlation) - Math.abs(a.correlation));
  }

  /**
   * Get correlation matrix for all symbols
   */
  getCorrelationMatrix() {
    const matrix = {};
    const symbols = Array.from(this.priceHistory.keys());

    symbols.forEach(symbol1 => {
      matrix[symbol1] = {};
      symbols.forEach(symbol2 => {
        if (symbol1 === symbol2) {
          matrix[symbol1][symbol2] = 1.0;
        } else {
          const correlation = this.getCorrelation(symbol1, symbol2);
          matrix[symbol1][symbol2] = correlation ? correlation.correlation : null;
        }
      });
    });

    return matrix;
  }

  /**
   * Find highly correlated pairs
   */
  getHighlyCorrelatedPairs(threshold = 0.7) {
    const highCorrelations = [];
    
    for (const [pairKey, correlationData] of this.correlationMatrix.entries()) {
      if (Math.abs(correlationData.correlation) >= threshold) {
        highCorrelations.push(correlationData);
      }
    }

    return highCorrelations.sort((a, b) => Math.abs(b.correlation) - Math.abs(a.correlation));
  }

  /**
   * Analyze currency basket correlations
   */
  analyzeCurrencyBasket(currencies) {
    const analysis = {
      avgCorrelation: 0,
      maxCorrelation: -1,
      minCorrelation: 1,
      diversificationScore: 0,
      riskFactors: []
    };

    const correlations = [];
    
    for (let i = 0; i < currencies.length; i++) {
      for (let j = i + 1; j < currencies.length; j++) {
        const correlation = this.getCorrelation(currencies[i], currencies[j]);
        if (correlation) {
          const corr = correlation.correlation;
          correlations.push(corr);
          
          analysis.maxCorrelation = Math.max(analysis.maxCorrelation, Math.abs(corr));
          analysis.minCorrelation = Math.min(analysis.minCorrelation, Math.abs(corr));
          
          if (Math.abs(corr) > 0.8) {
            analysis.riskFactors.push({
              pair: [currencies[i], currencies[j]],
              correlation: corr,
              risk: 'high_correlation'
            });
          }
        }
      }
    }

    if (correlations.length > 0) {
      analysis.avgCorrelation = correlations.reduce((sum, corr) => sum + Math.abs(corr), 0) / correlations.length;
      analysis.diversificationScore = 1 - analysis.avgCorrelation; // Higher score = better diversification
    }

    return analysis;
  }

  /**
   * Get forex-gold correlation analysis
   */
  getForexGoldCorrelation() {
    const goldSymbols = ['XAUUSD', 'XAGUSD'];
    const forexSymbols = Object.keys(FOREX_PAIRS);
    const analysis = {};

    goldSymbols.forEach(goldSymbol => {
      analysis[goldSymbol] = {
        strongPositive: [],
        strongNegative: [],
        moderate: [],
        weak: []
      };

      forexSymbols.forEach(forexSymbol => {
        const correlation = this.getCorrelation(goldSymbol, forexSymbol);
        if (correlation) {
          const corr = correlation.correlation;
          const abs = Math.abs(corr);
          
          if (abs >= 0.7) {
            if (corr > 0) {
              analysis[goldSymbol].strongPositive.push({ symbol: forexSymbol, correlation: corr });
            } else {
              analysis[goldSymbol].strongNegative.push({ symbol: forexSymbol, correlation: corr });
            }
          } else if (abs >= 0.4) {
            analysis[goldSymbol].moderate.push({ symbol: forexSymbol, correlation: corr });
          } else {
            analysis[goldSymbol].weak.push({ symbol: forexSymbol, correlation: corr });
          }
        }
      });
    });

    return analysis;
  }

  /**
   * Start automatic correlation updates
   */
  startCorrelationUpdates() {
    this.correlationUpdateInterval = setInterval(() => {
      this.updateAllCorrelations();
    }, this.updateInterval);

    logger.info('Correlation analyzer started', {
      updateInterval: this.updateInterval,
      historyLength: this.historyLength,
      minDataPoints: this.minDataPoints
    });
  }

  /**
   * Update all correlations
   */
  updateAllCorrelations() {
    const symbols = Array.from(this.priceHistory.keys());
    
    symbols.forEach(symbol => {
      this.updateCorrelations(symbol);
    });

    this.emit('correlationsUpdated', {
      symbolCount: symbols.length,
      correlationCount: this.correlationMatrix.size,
      timestamp: Date.now()
    });
  }

  /**
   * Stop correlation updates
   */
  stop() {
    if (this.correlationUpdateInterval) {
      clearInterval(this.correlationUpdateInterval);
      this.correlationUpdateInterval = null;
    }
    logger.info('Correlation analyzer stopped');
  }

  /**
   * Get real-time correlation statistics
   */
  getStatistics() {
    const symbols = Array.from(this.priceHistory.keys());
    const correlations = Array.from(this.correlationMatrix.values());
    
    const avgCorrelation = correlations.length > 0 
      ? correlations.reduce((sum, c) => sum + Math.abs(c.correlation), 0) / correlations.length 
      : 0;

    const strongCorrelations = correlations.filter(c => Math.abs(c.correlation) >= 0.7).length;
    const weakCorrelations = correlations.filter(c => Math.abs(c.correlation) < 0.3).length;

    return {
      symbolCount: symbols.length,
      correlationPairs: correlations.length,
      averageCorrelation: avgCorrelation,
      strongCorrelations,
      weakCorrelations,
      lastUpdate: Math.max(...correlations.map(c => c.lastUpdated), 0),
      dataQuality: this.assessDataQuality()
    };
  }

  /**
   * Assess data quality for correlation analysis
   */
  assessDataQuality() {
    const symbols = Array.from(this.priceHistory.keys());
    let totalDataPoints = 0;
    let sufficientData = 0;

    symbols.forEach(symbol => {
      const history = this.priceHistory.get(symbol);
      totalDataPoints += history.length;
      if (history.length >= this.minDataPoints) {
        sufficientData++;
      }
    });

    const avgDataPoints = symbols.length > 0 ? totalDataPoints / symbols.length : 0;
    const dataCompleteness = symbols.length > 0 ? sufficientData / symbols.length : 0;

    return {
      averageDataPoints: avgDataPoints,
      dataCompleteness: dataCompleteness,
      quality: dataCompleteness >= 0.8 ? 'high' : dataCompleteness >= 0.5 ? 'medium' : 'low'
    };
  }
}

module.exports = CorrelationAnalyzer;