// Gold Trading Configuration (XAUUSD, XAGUSD) Optimization
const PRECIOUS_METALS = {
  XAUUSD: {
    symbol: 'XAUUSD',
    name: 'Gold vs US Dollar',
    metal: 'Gold',
    currency: 'USD',
    category: 'precious_metal',
    unit: 'oz',
    pipValue: 0.01,
    contractSize: 100, // 100 oz
    spread: { min: 0.2, avg: 0.5, max: 1.5 },
    volatility: {
      avg: 1.2, // Average daily range %
      high: 3.0, // High volatility range %
      vix: 'high' // Volatility index classification
    },
    sessionVolume: {
      asia: 'medium',
      europe: 'high',
      us: 'very_high'
    },
    tradingHours: '24/5',
    islamicSwapFree: true,
    hedgeInstrument: true,
    safeHaven: true,
    correlations: {
      DXY: -0.8, // US Dollar Index
      SP500: -0.3,
      BONDS_10Y: -0.4,
      INFLATION: 0.7,
      EURUSD: 0.3,
      AUDUSD: 0.7,
      USDCHF: -0.2,
      OIL_WTI: 0.4
    },
    fundamentalFactors: {
      inflation: { weight: 0.8, direction: 'positive' },
      dollarStrength: { weight: 0.9, direction: 'negative' },
      geopolitical: { weight: 0.7, direction: 'positive' },
      interestRates: { weight: 0.6, direction: 'negative' },
      economicUncertainty: { weight: 0.8, direction: 'positive' }
    },
    technicalPatterns: {
      support: [1950, 1900, 1850],
      resistance: [2100, 2150, 2200],
      trendlines: 'bullish_long_term',
      fibonacciLevels: [1618, 1732, 1850, 1968, 2085]
    },
    volatilityHandling: {
      dynamicSpreads: true,
      gapProtection: true,
      newsFiltering: true,
      sessionAdjustment: true,
      riskMultiplier: 1.5
    },
    optimalTradingTimes: {
      best: ['08:00-12:00 UTC', '13:00-17:00 UTC'], // London/NY overlap
      avoid: ['22:00-02:00 UTC'], // Low liquidity
      news: ['13:30 UTC', '15:00 UTC', '19:00 UTC'] // Key news times
    }
  },
  
  XAGUSD: {
    symbol: 'XAGUSD',
    name: 'Silver vs US Dollar',
    metal: 'Silver',
    currency: 'USD',
    category: 'precious_metal',
    unit: 'oz',
    pipValue: 0.001,
    contractSize: 5000, // 5000 oz
    spread: { min: 0.02, avg: 0.05, max: 0.15 },
    volatility: {
      avg: 2.5, // Higher volatility than gold
      high: 6.0,
      vix: 'very_high'
    },
    sessionVolume: {
      asia: 'low',
      europe: 'medium',
      us: 'high'
    },
    tradingHours: '24/5',
    islamicSwapFree: true,
    hedgeInstrument: false,
    safeHaven: false,
    correlations: {
      XAUUSD: 0.85, // High correlation with gold
      DXY: -0.7,
      SP500: 0.2,
      INDUSTRIAL_METALS: 0.6,
      SOLAR_DEMAND: 0.4
    },
    fundamentalFactors: {
      inflation: { weight: 0.6, direction: 'positive' },
      dollarStrength: { weight: 0.8, direction: 'negative' },
      industrialDemand: { weight: 0.7, direction: 'positive' },
      goldPremium: { weight: 0.9, direction: 'positive' },
      solarDemand: { weight: 0.5, direction: 'positive' }
    },
    technicalPatterns: {
      support: [22.0, 20.5, 19.0],
      resistance: [26.0, 28.0, 30.0],
      trendlines: 'range_bound',
      fibonacciLevels: [19.5, 21.2, 23.1, 25.0, 27.3]
    },
    volatilityHandling: {
      dynamicSpreads: true,
      gapProtection: true,
      newsFiltering: true,
      sessionAdjustment: true,
      riskMultiplier: 2.0 // Higher risk due to volatility
    },
    optimalTradingTimes: {
      best: ['13:00-17:00 UTC'], // NY session
      avoid: ['00:00-06:00 UTC'], // Asian night
      news: ['13:30 UTC', '15:00 UTC'] // Following gold news
    }
  }
};

// Gold-specific trading strategies
const GOLD_STRATEGIES = {
  SAFE_HAVEN: {
    name: 'Safe Haven Strategy',
    description: 'Buy gold during market uncertainty',
    triggers: {
      vix_above: 25,
      sp500_drop: -2.0,
      geopolitical_events: true,
      dollar_weakness: true
    },
    riskManagement: {
      stopLoss: 0.5, // 0.5% of account
      takeProfit: 1.5, // 1.5% target
      trailingStop: true
    }
  },
  
  INFLATION_HEDGE: {
    name: 'Inflation Hedge Strategy',
    description: 'Long gold during high inflation periods',
    triggers: {
      cpi_above: 3.0,
      real_rates_negative: true,
      dollar_debasement: true
    },
    riskManagement: {
      stopLoss: 0.8,
      takeProfit: 2.0,
      positionSize: 'large'
    }
  },
  
  CORRELATION_BREAKOUT: {
    name: 'Correlation Breakout',
    description: 'Trade when gold breaks correlation with USD',
    triggers: {
      correlation_break: 0.3, // When correlation drops
      momentum_confirmation: true,
      volume_spike: true
    },
    riskManagement: {
      stopLoss: 0.3,
      takeProfit: 1.0,
      quickExit: true
    }
  },
  
  SESSION_MOMENTUM: {
    name: 'Session Momentum Strategy',
    description: 'Trade gold momentum during optimal sessions',
    triggers: {
      london_open: true,
      ny_open: true,
      high_volume: true,
      trend_confirmation: true
    },
    riskManagement: {
      stopLoss: 0.4,
      takeProfit: 1.2,
      sessionExit: true
    }
  }
};

// Volatility handling for precious metals
const VOLATILITY_HANDLER = {
  DYNAMIC_SPREADS: {
    low_volatility: { multiplier: 1.0 },
    medium_volatility: { multiplier: 1.5 },
    high_volatility: { multiplier: 2.0 },
    extreme_volatility: { multiplier: 3.0 }
  },
  
  POSITION_SIZING: {
    low_volatility: { size: 1.0 },
    medium_volatility: { size: 0.7 },
    high_volatility: { size: 0.5 },
    extreme_volatility: { size: 0.3 }
  },
  
  RISK_PARAMETERS: {
    XAUUSD: {
      maxRiskPerTrade: 0.5, // 0.5% of account
      maxDailyRisk: 2.0, // 2% daily limit
      maxDrawdown: 5.0, // 5% max drawdown
      correlationLimit: 0.3 // Max correlation exposure
    },
    XAGUSD: {
      maxRiskPerTrade: 0.3, // Lower due to higher volatility
      maxDailyRisk: 1.5,
      maxDrawdown: 4.0,
      correlationLimit: 0.2
    }
  },
  
  NEWS_IMPACT: {
    FED_ANNOUNCEMENTS: { impact: 'very_high', duration: '2h' },
    INFLATION_DATA: { impact: 'high', duration: '1h' },
    GEOPOLITICAL: { impact: 'high', duration: '4h' },
    DOLLAR_INDEX: { impact: 'medium', duration: '30m' },
    MINING_DATA: { impact: 'low', duration: '15m' }
  }
};

// Market hours optimization for gold
const GOLD_MARKET_HOURS = {
  OPTIMAL_HOURS: {
    // London session (8 AM - 5 PM GMT)
    LONDON: {
      start: '08:00',
      end: '17:00',
      timezone: 'GMT',
      liquidity: 'high',
      volatility: 'medium-high',
      spreads: 'tight'
    },
    
    // New York session (1 PM - 10 PM GMT)
    NEW_YORK: {
      start: '13:00',
      end: '22:00',
      timezone: 'GMT',
      liquidity: 'very_high',
      volatility: 'high',
      spreads: 'tightest'
    },
    
    // London-NY overlap (1 PM - 5 PM GMT)
    OVERLAP: {
      start: '13:00',
      end: '17:00',
      timezone: 'GMT',
      liquidity: 'maximum',
      volatility: 'very_high',
      spreads: 'optimal'
    }
  },
  
  AVOID_HOURS: {
    ASIAN_NIGHT: {
      start: '22:00',
      end: '06:00',
      timezone: 'GMT',
      reason: 'low_liquidity'
    },
    
    WEEKEND_GAPS: {
      friday_close: '22:00',
      sunday_open: '22:00',
      timezone: 'GMT',
      reason: 'gap_risk'
    }
  }
};

module.exports = {
  PRECIOUS_METALS,
  GOLD_STRATEGIES,
  VOLATILITY_HANDLER,
  GOLD_MARKET_HOURS,
  
  // Helper functions
  getGoldConfig: () => PRECIOUS_METALS.XAUUSD,
  getSilverConfig: () => PRECIOUS_METALS.XAGUSD,
  
  calculateGoldVolatility: (priceData) => {
    // Calculate current volatility based on price data
    if (!priceData || priceData.length < 20) return 'medium';
    
    const returns = [];
    for (let i = 1; i < priceData.length; i++) {
      returns.push((priceData[i].close - priceData[i-1].close) / priceData[i-1].close);
    }
    
    const variance = returns.reduce((sum, ret) => sum + ret * ret, 0) / returns.length;
    const volatility = Math.sqrt(variance) * Math.sqrt(252) * 100; // Annualized volatility
    
    if (volatility < 15) return 'low';
    if (volatility < 25) return 'medium';
    if (volatility < 40) return 'high';
    return 'extreme';
  },
  
  getOptimalGoldStrategy: (marketConditions) => {
    const { vix, inflation, dollarIndex, geopolitical } = marketConditions;
    
    if (vix > 25 || geopolitical) return GOLD_STRATEGIES.SAFE_HAVEN;
    if (inflation > 3.0) return GOLD_STRATEGIES.INFLATION_HEDGE;
    if (Math.abs(dollarIndex.correlation) < 0.3) return GOLD_STRATEGIES.CORRELATION_BREAKOUT;
    
    return GOLD_STRATEGIES.SESSION_MOMENTUM;
  },
  
  adjustForVolatility: (basePosition, volatility, symbol) => {
    const riskParams = VOLATILITY_HANDLER.RISK_PARAMETERS[symbol];
    const volatilityMultiplier = VOLATILITY_HANDLER.POSITION_SIZING[volatility]?.size || 1.0;
    
    return {
      position: basePosition * volatilityMultiplier,
      stopLoss: riskParams.maxRiskPerTrade * volatilityMultiplier,
      maxDaily: riskParams.maxDailyRisk
    };
  }
};