const { FOREX_PAIRS, TRADING_SESSIONS } = require('../config/forexPairs');
const { PRECIOUS_METALS, GOLD_STRATEGIES } = require('../config/goldConfig');
const logger = require('../utils/logger');

class ForexStrategies {
  constructor(options = {}) {
    this.correlationAnalyzer = options.correlationAnalyzer;
    this.sessionManager = options.sessionManager;
    this.orderExecutor = options.orderExecutor;
    this.riskParameters = {
      maxRiskPerTrade: 0.02, // 2%
      maxDailyRisk: 0.05, // 5%
      maxCorrelationExposure: 0.3, // 30%
      maxDrawdown: 0.10 // 10%
    };
  }

  /**
   * Analyze market and recommend trading strategies
   */
  analyzeMarket(marketData) {
    const analysis = {
      timestamp: Date.now(),
      session: this.sessionManager?.getCurrentSession(),
      strategies: [],
      riskLevel: 'medium',
      recommendations: []
    };

    // Session-based strategy selection
    if (analysis.session) {
      analysis.strategies.push(...this.getSessionStrategies(analysis.session));
    }

    // Correlation-based strategies
    if (this.correlationAnalyzer) {
      analysis.strategies.push(...this.getCorrelationStrategies());
    }

    // Volatility-based strategies
    analysis.strategies.push(...this.getVolatilityStrategies(marketData));

    // Currency strength strategies
    analysis.strategies.push(...this.getCurrencyStrengthStrategies(marketData));

    // Gold-specific strategies
    analysis.strategies.push(...this.getGoldStrategies(marketData));

    return analysis;
  }

  /**
   * Get session-specific trading strategies
   */
  getSessionStrategies(session) {
    const strategies = [];
    const sessionName = session.name || 'UNKNOWN';
    const sessionConfig = TRADING_SESSIONS[sessionName];

    if (!sessionConfig) return strategies;

    switch (sessionName) {
      case 'ASIA':
        strategies.push({
          name: 'Asian Range Trading',
          type: 'range',
          description: 'Trade ranges during low volatility Asian session',
          pairs: ['USDJPY', 'AUDUSD', 'NZDUSD'],
          characteristics: {
            volatility: 'low',
            volume: 'medium',
            spreads: 'medium'
          },
          riskLevel: 'low',
          confidence: 0.75,
          parameters: {
            entryMethod: 'support_resistance',
            stopLoss: 0.3, // 30 pips
            takeProfit: 0.6, // 60 pips
            riskReward: 2.0
          }
        });
        break;

      case 'EUROPE':
        strategies.push({
          name: 'European Breakout',
          type: 'breakout',
          description: 'Capture breakouts during high volatility European session',
          pairs: ['EURUSD', 'GBPUSD', 'EURGBP'],
          characteristics: {
            volatility: 'high',
            volume: 'high',
            spreads: 'tight'
          },
          riskLevel: 'medium',
          confidence: 0.85,
          parameters: {
            entryMethod: 'breakout_confirmation',
            stopLoss: 0.4, // 40 pips
            takeProfit: 1.2, // 120 pips
            riskReward: 3.0
          }
        });
        break;

      case 'US':
        strategies.push({
          name: 'NY News Trading',
          type: 'news',
          description: 'Trade news events during US session',
          pairs: ['EURUSD', 'GBPUSD', 'USDCAD'],
          characteristics: {
            volatility: 'very_high',
            volume: 'high',
            spreads: 'tight'
          },
          riskLevel: 'high',
          confidence: 0.70,
          parameters: {
            entryMethod: 'news_spike',
            stopLoss: 0.5, // 50 pips
            takeProfit: 1.0, // 100 pips
            riskReward: 2.0
          }
        });
        break;

      case 'SYDNEY':
        strategies.push({
          name: 'Sydney Gap Trading',
          type: 'gap',
          description: 'Trade weekend gaps during Sydney open',
          pairs: ['AUDUSD', 'NZDUSD'],
          characteristics: {
            volatility: 'low',
            volume: 'low',
            spreads: 'wide'
          },
          riskLevel: 'medium',
          confidence: 0.60,
          parameters: {
            entryMethod: 'gap_fill',
            stopLoss: 0.6, // 60 pips
            takeProfit: 0.8, // 80 pips
            riskReward: 1.3
          }
        });
        break;
    }

    return strategies;
  }

  /**
   * Get correlation-based strategies
   */
  getCorrelationStrategies() {
    const strategies = [];

    if (!this.correlationAnalyzer) return strategies;

    // Find pairs with broken correlations for pair trading
    const correlationMatrix = this.correlationAnalyzer.getCorrelationMatrix();
    const brokenCorrelations = this.findBrokenCorrelations(correlationMatrix);

    if (brokenCorrelations.length > 0) {
      strategies.push({
        name: 'Correlation Divergence',
        type: 'statistical_arbitrage',
        description: 'Trade pairs with broken historical correlations',
        pairs: brokenCorrelations.map(bc => [bc.pair1, bc.pair2]),
        riskLevel: 'medium',
        confidence: 0.80,
        parameters: {
          entryMethod: 'correlation_divergence',
          correlationThreshold: 0.3,
          stopLoss: 0.4,
          takeProfit: 0.8,
          riskReward: 2.0
        }
      });
    }

    // Currency basket strategies
    const basketAnalysis = this.analyzeCurrencyBaskets();
    if (basketAnalysis.opportunities.length > 0) {
      strategies.push({
        name: 'Currency Basket Arbitrage',
        type: 'basket',
        description: 'Trade currency strength/weakness baskets',
        pairs: basketAnalysis.opportunities,
        riskLevel: 'low',
        confidence: 0.75,
        parameters: {
          entryMethod: 'basket_strength',
          diversification: 'high',
          stopLoss: 0.3,
          takeProfit: 0.9,
          riskReward: 3.0
        }
      });
    }

    return strategies;
  }

  /**
   * Get volatility-based strategies
   */
  getVolatilityStrategies(marketData) {
    const strategies = [];

    // Calculate average volatility across major pairs
    const volatilityLevels = this.calculateVolatilityLevels(marketData);

    if (volatilityLevels.average > 1.5) {
      // High volatility - breakout strategies
      strategies.push({
        name: 'High Volatility Breakout',
        type: 'volatility_breakout',
        description: 'Capture momentum during high volatility periods',
        pairs: ['EURUSD', 'GBPUSD', 'USDJPY'],
        riskLevel: 'high',
        confidence: 0.70,
        parameters: {
          entryMethod: 'volatility_spike',
          volatilityThreshold: 1.5,
          stopLoss: 0.6,
          takeProfit: 1.8,
          riskReward: 3.0
        }
      });
    } else if (volatilityLevels.average < 0.8) {
      // Low volatility - range strategies
      strategies.push({
        name: 'Low Volatility Range',
        type: 'range_trading',
        description: 'Trade ranges during low volatility compression',
        pairs: ['EURUSD', 'USDCHF', 'EURCHF'],
        riskLevel: 'low',
        confidence: 0.80,
        parameters: {
          entryMethod: 'range_boundaries',
          volatilityThreshold: 0.8,
          stopLoss: 0.2,
          takeProfit: 0.4,
          riskReward: 2.0
        }
      });
    }

    return strategies;
  }

  /**
   * Get currency strength strategies
   */
  getCurrencyStrengthStrategies(marketData) {
    const strategies = [];
    const currencyStrength = this.calculateCurrencyStrength(marketData);

    const strongCurrencies = currencyStrength.filter(c => c.strength > 0.7);
    const weakCurrencies = currencyStrength.filter(c => c.strength < -0.7);

    if (strongCurrencies.length > 0 && weakCurrencies.length > 0) {
      const tradingPairs = this.generateStrengthPairs(strongCurrencies, weakCurrencies);

      strategies.push({
        name: 'Currency Strength Momentum',
        type: 'strength_momentum',
        description: 'Trade strong currencies against weak currencies',
        pairs: tradingPairs,
        riskLevel: 'medium',
        confidence: 0.85,
        parameters: {
          entryMethod: 'strength_divergence',
          strengthThreshold: 0.7,
          stopLoss: 0.4,
          takeProfit: 1.2,
          riskReward: 3.0
        }
      });
    }

    return strategies;
  }

  /**
   * Get gold-specific strategies
   */
  getGoldStrategies(marketData) {
    const strategies = [];
    const goldData = marketData.XAUUSD || marketData.XAGUSD;

    if (!goldData) return strategies;

    // Safe haven strategy
    const marketRisk = this.assessMarketRisk(marketData);
    if (marketRisk.level === 'high') {
      strategies.push({
        name: 'Gold Safe Haven',
        type: 'safe_haven',
        description: 'Buy gold during market uncertainty',
        pairs: ['XAUUSD'],
        riskLevel: 'low',
        confidence: 0.90,
        parameters: {
          entryMethod: 'risk_on_off',
          riskThreshold: marketRisk.score,
          stopLoss: 0.5, // $50
          takeProfit: 1.5, // $150
          riskReward: 3.0
        }
      });
    }

    // Dollar correlation strategy
    const dxyCorrelation = this.correlationAnalyzer?.getCorrelation('XAUUSD', 'DXY');
    if (dxyCorrelation && Math.abs(dxyCorrelation.correlation) < 0.3) {
      strategies.push({
        name: 'Gold-Dollar Divergence',
        type: 'correlation_break',
        description: 'Trade gold when correlation with dollar breaks',
        pairs: ['XAUUSD'],
        riskLevel: 'medium',
        confidence: 0.75,
        parameters: {
          entryMethod: 'correlation_breakdown',
          correlationThreshold: 0.3,
          stopLoss: 0.8,
          takeProfit: 2.0,
          riskReward: 2.5
        }
      });
    }

    return strategies;
  }

  /**
   * Generate trading signals based on strategies
   */
  generateSignals(strategies, marketData) {
    const signals = [];

    strategies.forEach(strategy => {
      const strategySignals = this.evaluateStrategy(strategy, marketData);
      signals.push(...strategySignals);
    });

    // Sort by confidence and filter by risk parameters
    return signals
      .sort((a, b) => b.confidence - a.confidence)
      .filter(signal => this.passesRiskCheck(signal))
      .slice(0, 10); // Top 10 signals
  }

  /**
   * Evaluate individual strategy for signals
   */
  evaluateStrategy(strategy, marketData) {
    const signals = [];

    strategy.pairs.forEach(pair => {
      const pairData = marketData[pair];
      if (!pairData) return;

      const signal = this.analyzeStrategyForPair(strategy, pair, pairData);
      if (signal) {
        signals.push({
          ...signal,
          strategy: strategy.name,
          confidence: strategy.confidence * signal.strength,
          timestamp: Date.now()
        });
      }
    });

    return signals;
  }

  /**
   * Analyze strategy for specific pair
   */
  analyzeStrategyForPair(strategy, pair, pairData) {
    switch (strategy.type) {
      case 'breakout':
        return this.analyzeBreakoutSignal(pair, pairData, strategy.parameters);
      case 'range':
        return this.analyzeRangeSignal(pair, pairData, strategy.parameters);
      case 'news':
        return this.analyzeNewsSignal(pair, pairData, strategy.parameters);
      case 'correlation_break':
        return this.analyzeCorrelationBreakSignal(pair, pairData, strategy.parameters);
      case 'strength_momentum':
        return this.analyzeStrengthMomentumSignal(pair, pairData, strategy.parameters);
      default:
        return null;
    }
  }

  /**
   * Analyze breakout signals
   */
  analyzeBreakoutSignal(pair, pairData, parameters) {
    // Simplified breakout analysis
    const currentPrice = pairData.bid;
    const high24h = pairData.high24h || currentPrice * 1.01;
    const low24h = pairData.low24h || currentPrice * 0.99;
    
    const range = high24h - low24h;
    const position = (currentPrice - low24h) / range;

    if (position > 0.8) {
      return {
        pair,
        direction: 'buy',
        price: currentPrice,
        strength: 0.8,
        stopLoss: currentPrice - (parameters.stopLoss * 0.0001),
        takeProfit: currentPrice + (parameters.takeProfit * 0.0001),
        reason: 'Breakout above resistance'
      };
    } else if (position < 0.2) {
      return {
        pair,
        direction: 'sell',
        price: currentPrice,
        strength: 0.8,
        stopLoss: currentPrice + (parameters.stopLoss * 0.0001),
        takeProfit: currentPrice - (parameters.takeProfit * 0.0001),
        reason: 'Breakdown below support'
      };
    }

    return null;
  }

  /**
   * Analyze range trading signals
   */
  analyzeRangeSignal(pair, pairData, parameters) {
    const currentPrice = pairData.bid;
    const high24h = pairData.high24h || currentPrice * 1.005;
    const low24h = pairData.low24h || currentPrice * 0.995;
    
    const range = high24h - low24h;
    const position = (currentPrice - low24h) / range;

    if (position > 0.7) {
      return {
        pair,
        direction: 'sell',
        price: currentPrice,
        strength: 0.7,
        stopLoss: currentPrice + (parameters.stopLoss * 0.0001),
        takeProfit: currentPrice - (parameters.takeProfit * 0.0001),
        reason: 'Near range resistance - expecting reversal'
      };
    } else if (position < 0.3) {
      return {
        pair,
        direction: 'buy',
        price: currentPrice,
        strength: 0.7,
        stopLoss: currentPrice - (parameters.stopLoss * 0.0001),
        takeProfit: currentPrice + (parameters.takeProfit * 0.0001),
        reason: 'Near range support - expecting bounce'
      };
    }

    return null;
  }

  /**
   * Helper methods
   */
  findBrokenCorrelations(correlationMatrix) {
    const broken = [];
    const pairs = Object.keys(correlationMatrix);
    
    for (let i = 0; i < pairs.length; i++) {
      for (let j = i + 1; j < pairs.length; j++) {
        const pair1 = pairs[i];
        const pair2 = pairs[j];
        const correlation = correlationMatrix[pair1][pair2];
        
        // Historical correlation should be checked here
        const historicalCorrelation = 0.8; // Mock historical correlation
        
        if (Math.abs(correlation - historicalCorrelation) > 0.4) {
          broken.push({
            pair1,
            pair2,
            currentCorrelation: correlation,
            historicalCorrelation,
            divergence: Math.abs(correlation - historicalCorrelation)
          });
        }
      }
    }
    
    return broken;
  }

  analyzeCurrencyBaskets() {
    // Mock implementation
    return {
      opportunities: ['EURUSD', 'GBPUSD'],
      strength: {
        USD: 0.8,
        EUR: -0.3,
        GBP: -0.5
      }
    };
  }

  calculateVolatilityLevels(marketData) {
    const volatilities = Object.values(marketData)
      .map(data => data.volatility || 1.0)
      .filter(v => v > 0);
    
    return {
      average: volatilities.reduce((a, b) => a + b, 0) / volatilities.length,
      max: Math.max(...volatilities),
      min: Math.min(...volatilities)
    };
  }

  calculateCurrencyStrength(marketData) {
    // Mock currency strength calculation
    return [
      { currency: 'USD', strength: 0.8 },
      { currency: 'EUR', strength: -0.2 },
      { currency: 'GBP', strength: -0.5 },
      { currency: 'JPY', strength: 0.3 }
    ];
  }

  generateStrengthPairs(strongCurrencies, weakCurrencies) {
    const pairs = [];
    strongCurrencies.forEach(strong => {
      weakCurrencies.forEach(weak => {
        const pair = `${strong.currency}${weak.currency}`;
        if (FOREX_PAIRS[pair]) {
          pairs.push(pair);
        }
      });
    });
    return pairs;
  }

  assessMarketRisk(marketData) {
    // Mock risk assessment
    return {
      level: 'medium',
      score: 0.6,
      factors: ['volatility', 'correlation']
    };
  }

  analyzeNewsSignal(pair, pairData, parameters) {
    // Mock news signal analysis
    return null;
  }

  analyzeCorrelationBreakSignal(pair, pairData, parameters) {
    // Mock correlation break analysis
    return null;
  }

  analyzeStrengthMomentumSignal(pair, pairData, parameters) {
    // Mock strength momentum analysis
    return null;
  }

  passesRiskCheck(signal) {
    // Basic risk checks
    const riskAmount = Math.abs(signal.price - signal.stopLoss) / signal.price;
    return riskAmount <= this.riskParameters.maxRiskPerTrade;
  }
}

module.exports = ForexStrategies;