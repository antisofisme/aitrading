// 28 Major Forex Pairs Configuration for Indonesian Market
const FOREX_PAIRS = {
  // Major Pairs (7)
  EURUSD: {
    symbol: 'EURUSD',
    name: 'Euro vs US Dollar',
    base: 'EUR',
    quote: 'USD',
    category: 'major',
    pipValue: 0.0001,
    spread: { min: 0.1, avg: 0.5, max: 2.0 },
    sessionVolume: {
      asia: 'medium',
      europe: 'high',
      us: 'high'
    },
    tradingHours: '24/5',
    islamicSwapFree: true,
    correlation: {
      GBPUSD: 0.85,
      XAUUSD: -0.3,
      USDCHF: -0.95
    }
  },
  GBPUSD: {
    symbol: 'GBPUSD',
    name: 'British Pound vs US Dollar',
    base: 'GBP',
    quote: 'USD',
    category: 'major',
    pipValue: 0.0001,
    spread: { min: 0.2, avg: 0.8, max: 3.0 },
    sessionVolume: {
      asia: 'low',
      europe: 'high',
      us: 'high'
    },
    tradingHours: '24/5',
    islamicSwapFree: true,
    correlation: {
      EURUSD: 0.85,
      EURGBP: -0.6,
      XAUUSD: -0.25
    }
  },
  USDJPY: {
    symbol: 'USDJPY',
    name: 'US Dollar vs Japanese Yen',
    base: 'USD',
    quote: 'JPY',
    category: 'major',
    pipValue: 0.01,
    spread: { min: 0.1, avg: 0.3, max: 1.5 },
    sessionVolume: {
      asia: 'high',
      europe: 'medium',
      us: 'medium'
    },
    tradingHours: '24/5',
    islamicSwapFree: true,
    correlation: {
      USDCHF: 0.7,
      EURJPY: 0.8,
      XAUUSD: -0.4
    }
  },
  USDCHF: {
    symbol: 'USDCHF',
    name: 'US Dollar vs Swiss Franc',
    base: 'USD',
    quote: 'CHF',
    category: 'major',
    pipValue: 0.0001,
    spread: { min: 0.2, avg: 0.6, max: 2.5 },
    sessionVolume: {
      asia: 'low',
      europe: 'high',
      us: 'medium'
    },
    tradingHours: '24/5',
    islamicSwapFree: true,
    correlation: {
      EURUSD: -0.95,
      USDJPY: 0.7,
      XAUUSD: 0.2
    }
  },
  AUDUSD: {
    symbol: 'AUDUSD',
    name: 'Australian Dollar vs US Dollar',
    base: 'AUD',
    quote: 'USD',
    category: 'major',
    pipValue: 0.0001,
    spread: { min: 0.2, avg: 0.7, max: 3.0 },
    sessionVolume: {
      asia: 'high',
      europe: 'medium',
      us: 'medium'
    },
    tradingHours: '24/5',
    islamicSwapFree: true,
    correlation: {
      NZDUSD: 0.8,
      XAUUSD: 0.7,
      USDCAD: -0.6
    }
  },
  USDCAD: {
    symbol: 'USDCAD',
    name: 'US Dollar vs Canadian Dollar',
    base: 'USD',
    quote: 'CAD',
    category: 'major',
    pipValue: 0.0001,
    spread: { min: 0.2, avg: 0.8, max: 2.5 },
    sessionVolume: {
      asia: 'low',
      europe: 'medium',
      us: 'high'
    },
    tradingHours: '24/5',
    islamicSwapFree: true,
    correlation: {
      AUDUSD: -0.6,
      USDCHF: 0.5,
      XAUUSD: -0.5
    }
  },
  NZDUSD: {
    symbol: 'NZDUSD',
    name: 'New Zealand Dollar vs US Dollar',
    base: 'NZD',
    quote: 'USD',
    category: 'major',
    pipValue: 0.0001,
    spread: { min: 0.3, avg: 1.2, max: 4.0 },
    sessionVolume: {
      asia: 'high',
      europe: 'low',
      us: 'low'
    },
    tradingHours: '24/5',
    islamicSwapFree: true,
    correlation: {
      AUDUSD: 0.8,
      XAUUSD: 0.6,
      USDJPY: -0.4
    }
  },

  // Minor Pairs (14)
  EURGBP: {
    symbol: 'EURGBP',
    name: 'Euro vs British Pound',
    base: 'EUR',
    quote: 'GBP',
    category: 'minor',
    pipValue: 0.0001,
    spread: { min: 0.3, avg: 1.0, max: 3.5 },
    sessionVolume: {
      asia: 'low',
      europe: 'high',
      us: 'medium'
    },
    tradingHours: '24/5',
    islamicSwapFree: true,
    correlation: {
      GBPUSD: -0.6,
      EURUSD: 0.4
    }
  },
  EURJPY: {
    symbol: 'EURJPY',
    name: 'Euro vs Japanese Yen',
    base: 'EUR',
    quote: 'JPY',
    category: 'minor',
    pipValue: 0.01,
    spread: { min: 0.2, avg: 0.8, max: 3.0 },
    sessionVolume: {
      asia: 'medium',
      europe: 'high',
      us: 'medium'
    },
    tradingHours: '24/5',
    islamicSwapFree: true,
    correlation: {
      USDJPY: 0.8,
      EURUSD: 0.9
    }
  },
  EURCHF: {
    symbol: 'EURCHF',
    name: 'Euro vs Swiss Franc',
    base: 'EUR',
    quote: 'CHF',
    category: 'minor',
    pipValue: 0.0001,
    spread: { min: 0.3, avg: 1.2, max: 4.0 },
    sessionVolume: {
      asia: 'low',
      europe: 'high',
      us: 'low'
    },
    tradingHours: '24/5',
    islamicSwapFree: true,
    correlation: {
      EURUSD: 0.8,
      USDCHF: -0.7
    }
  },
  EURAUD: {
    symbol: 'EURAUD',
    name: 'Euro vs Australian Dollar',
    base: 'EUR',
    quote: 'AUD',
    category: 'minor',
    pipValue: 0.0001,
    spread: { min: 0.5, avg: 1.5, max: 5.0 },
    sessionVolume: {
      asia: 'medium',
      europe: 'high',
      us: 'low'
    },
    tradingHours: '24/5',
    islamicSwapFree: true,
    correlation: {
      EURUSD: 0.7,
      AUDUSD: -0.3
    }
  },
  EURCAD: {
    symbol: 'EURCAD',
    name: 'Euro vs Canadian Dollar',
    base: 'EUR',
    quote: 'CAD',
    category: 'minor',
    pipValue: 0.0001,
    spread: { min: 0.4, avg: 1.3, max: 4.5 },
    sessionVolume: {
      asia: 'low',
      europe: 'high',
      us: 'medium'
    },
    tradingHours: '24/5',
    islamicSwapFree: true,
    correlation: {
      EURUSD: 0.8,
      USDCAD: -0.6
    }
  },
  GBPJPY: {
    symbol: 'GBPJPY',
    name: 'British Pound vs Japanese Yen',
    base: 'GBP',
    quote: 'JPY',
    category: 'minor',
    pipValue: 0.01,
    spread: { min: 0.4, avg: 1.5, max: 5.0 },
    sessionVolume: {
      asia: 'medium',
      europe: 'high',
      us: 'medium'
    },
    tradingHours: '24/5',
    islamicSwapFree: true,
    correlation: {
      GBPUSD: 0.7,
      USDJPY: 0.5
    }
  },
  GBPCHF: {
    symbol: 'GBPCHF',
    name: 'British Pound vs Swiss Franc',
    base: 'GBP',
    quote: 'CHF',
    category: 'minor',
    pipValue: 0.0001,
    spread: { min: 0.5, avg: 1.8, max: 6.0 },
    sessionVolume: {
      asia: 'low',
      europe: 'high',
      us: 'low'
    },
    tradingHours: '24/5',
    islamicSwapFree: true,
    correlation: {
      GBPUSD: 0.8,
      USDCHF: -0.6
    }
  },
  GBPAUD: {
    symbol: 'GBPAUD',
    name: 'British Pound vs Australian Dollar',
    base: 'GBP',
    quote: 'AUD',
    category: 'minor',
    pipValue: 0.0001,
    spread: { min: 0.6, avg: 2.0, max: 7.0 },
    sessionVolume: {
      asia: 'medium',
      europe: 'high',
      us: 'low'
    },
    tradingHours: '24/5',
    islamicSwapFree: true,
    correlation: {
      GBPUSD: 0.6,
      AUDUSD: -0.2
    }
  },
  GBPCAD: {
    symbol: 'GBPCAD',
    name: 'British Pound vs Canadian Dollar',
    base: 'GBP',
    quote: 'CAD',
    category: 'minor',
    pipValue: 0.0001,
    spread: { min: 0.5, avg: 1.7, max: 6.0 },
    sessionVolume: {
      asia: 'low',
      europe: 'high',
      us: 'medium'
    },
    tradingHours: '24/5',
    islamicSwapFree: true,
    correlation: {
      GBPUSD: 0.7,
      USDCAD: -0.5
    }
  },
  AUDCAD: {
    symbol: 'AUDCAD',
    name: 'Australian Dollar vs Canadian Dollar',
    base: 'AUD',
    quote: 'CAD',
    category: 'minor',
    pipValue: 0.0001,
    spread: { min: 0.4, avg: 1.4, max: 5.0 },
    sessionVolume: {
      asia: 'medium',
      europe: 'medium',
      us: 'medium'
    },
    tradingHours: '24/5',
    islamicSwapFree: true,
    correlation: {
      AUDUSD: 0.6,
      USDCAD: -0.7
    }
  },
  AUDCHF: {
    symbol: 'AUDCHF',
    name: 'Australian Dollar vs Swiss Franc',
    base: 'AUD',
    quote: 'CHF',
    category: 'minor',
    pipValue: 0.0001,
    spread: { min: 0.4, avg: 1.5, max: 5.5 },
    sessionVolume: {
      asia: 'medium',
      europe: 'medium',
      us: 'low'
    },
    tradingHours: '24/5',
    islamicSwapFree: true,
    correlation: {
      AUDUSD: 0.7,
      USDCHF: -0.5
    }
  },
  AUDJPY: {
    symbol: 'AUDJPY',
    name: 'Australian Dollar vs Japanese Yen',
    base: 'AUD',
    quote: 'JPY',
    category: 'minor',
    pipValue: 0.01,
    spread: { min: 0.3, avg: 1.2, max: 4.0 },
    sessionVolume: {
      asia: 'high',
      europe: 'medium',
      us: 'low'
    },
    tradingHours: '24/5',
    islamicSwapFree: true,
    correlation: {
      AUDUSD: 0.8,
      USDJPY: 0.6
    }
  },
  CADJPY: {
    symbol: 'CADJPY',
    name: 'Canadian Dollar vs Japanese Yen',
    base: 'CAD',
    quote: 'JPY',
    category: 'minor',
    pipValue: 0.01,
    spread: { min: 0.4, avg: 1.6, max: 5.0 },
    sessionVolume: {
      asia: 'medium',
      europe: 'low',
      us: 'medium'
    },
    tradingHours: '24/5',
    islamicSwapFree: true,
    correlation: {
      USDCAD: -0.7,
      USDJPY: 0.5
    }
  },
  CADCHF: {
    symbol: 'CADCHF',
    name: 'Canadian Dollar vs Swiss Franc',
    base: 'CAD',
    quote: 'CHF',
    category: 'minor',
    pipValue: 0.0001,
    spread: { min: 0.5, avg: 1.8, max: 6.0 },
    sessionVolume: {
      asia: 'low',
      europe: 'medium',
      us: 'medium'
    },
    tradingHours: '24/5',
    islamicSwapFree: true,
    correlation: {
      USDCAD: -0.6,
      USDCHF: 0.4
    }
  },

  // Exotic Pairs (7) - Popular in Indonesian Market
  EURSGD: {
    symbol: 'EURSGD',
    name: 'Euro vs Singapore Dollar',
    base: 'EUR',
    quote: 'SGD',
    category: 'exotic',
    pipValue: 0.0001,
    spread: { min: 1.0, avg: 3.5, max: 10.0 },
    sessionVolume: {
      asia: 'high',
      europe: 'medium',
      us: 'low'
    },
    tradingHours: '24/5',
    islamicSwapFree: true,
    correlation: {
      EURUSD: 0.6,
      USDSGD: -0.4
    }
  },
  USDSGD: {
    symbol: 'USDSGD',
    name: 'US Dollar vs Singapore Dollar',
    base: 'USD',
    quote: 'SGD',
    category: 'exotic',
    pipValue: 0.0001,
    spread: { min: 0.8, avg: 2.5, max: 8.0 },
    sessionVolume: {
      asia: 'high',
      europe: 'low',
      us: 'medium'
    },
    tradingHours: '24/5',
    islamicSwapFree: true,
    correlation: {
      USDJPY: 0.5,
      EURSGD: -0.4
    }
  },
  USDHKD: {
    symbol: 'USDHKD',
    name: 'US Dollar vs Hong Kong Dollar',
    base: 'USD',
    quote: 'HKD',
    category: 'exotic',
    pipValue: 0.0001,
    spread: { min: 1.5, avg: 4.0, max: 12.0 },
    sessionVolume: {
      asia: 'high',
      europe: 'low',
      us: 'low'
    },
    tradingHours: '24/5',
    islamicSwapFree: true,
    correlation: {
      USDJPY: 0.3,
      USDSGD: 0.6
    }
  },
  EURNOK: {
    symbol: 'EURNOK',
    name: 'Euro vs Norwegian Krone',
    base: 'EUR',
    quote: 'NOK',
    category: 'exotic',
    pipValue: 0.0001,
    spread: { min: 2.0, avg: 6.0, max: 15.0 },
    sessionVolume: {
      asia: 'low',
      europe: 'high',
      us: 'low'
    },
    tradingHours: '24/5',
    islamicSwapFree: true,
    correlation: {
      EURUSD: 0.7,
      USDNOK: -0.6
    }
  },
  EURSEK: {
    symbol: 'EURSEK',
    name: 'Euro vs Swedish Krona',
    base: 'EUR',
    quote: 'SEK',
    category: 'exotic',
    pipValue: 0.0001,
    spread: { min: 2.5, avg: 7.0, max: 18.0 },
    sessionVolume: {
      asia: 'low',
      europe: 'high',
      us: 'low'
    },
    tradingHours: '24/5',
    islamicSwapFree: true,
    correlation: {
      EURUSD: 0.8,
      EURNOK: 0.9
    }
  },
  USDZAR: {
    symbol: 'USDZAR',
    name: 'US Dollar vs South African Rand',
    base: 'USD',
    quote: 'ZAR',
    category: 'exotic',
    pipValue: 0.0001,
    spread: { min: 3.0, avg: 8.0, max: 20.0 },
    sessionVolume: {
      asia: 'low',
      europe: 'medium',
      us: 'low'
    },
    tradingHours: '24/5',
    islamicSwapFree: true,
    correlation: {
      XAUUSD: 0.5,
      AUDUSD: 0.4
    }
  },
  USDTRY: {
    symbol: 'USDTRY',
    name: 'US Dollar vs Turkish Lira',
    base: 'USD',
    quote: 'TRY',
    category: 'exotic',
    pipValue: 0.0001,
    spread: { min: 5.0, avg: 15.0, max: 50.0 },
    sessionVolume: {
      asia: 'low',
      europe: 'medium',
      us: 'low'
    },
    tradingHours: '24/5',
    islamicSwapFree: true,
    correlation: {
      EURUSD: -0.3,
      USDZAR: 0.4
    }
  }
};

// Trading Sessions Configuration
const TRADING_SESSIONS = {
  ASIA: {
    name: 'Asian Session',
    timezone: 'Asia/Tokyo',
    start: '00:00',
    end: '09:00',
    utcOffset: '+09:00',
    majorPairs: ['USDJPY', 'AUDUSD', 'NZDUSD', 'EURJPY', 'GBPJPY'],
    characteristics: {
      volatility: 'low-medium',
      volume: 'medium',
      spreads: 'medium'
    }
  },
  EUROPE: {
    name: 'European Session',
    timezone: 'Europe/London',
    start: '08:00',
    end: '17:00',
    utcOffset: '+00:00',
    majorPairs: ['EURUSD', 'GBPUSD', 'EURGBP', 'USDCHF'],
    characteristics: {
      volatility: 'high',
      volume: 'high',
      spreads: 'tight'
    }
  },
  US: {
    name: 'US Session',
    timezone: 'America/New_York',
    start: '13:00',
    end: '22:00',
    utcOffset: '-05:00',
    majorPairs: ['EURUSD', 'GBPUSD', 'USDCAD', 'USDCHF'],
    characteristics: {
      volatility: 'high',
      volume: 'high',
      spreads: 'tight'
    }
  },
  SYDNEY: {
    name: 'Sydney Session',
    timezone: 'Australia/Sydney',
    start: '22:00',
    end: '07:00',
    utcOffset: '+11:00',
    majorPairs: ['AUDUSD', 'NZDUSD', 'AUDNZD'],
    characteristics: {
      volatility: 'low',
      volume: 'low',
      spreads: 'wide'
    }
  }
};

// Islamic Trading Configuration
const ISLAMIC_TRADING = {
  swapFreeEnabled: true,
  supportedPairs: Object.keys(FOREX_PAIRS).filter(pair => FOREX_PAIRS[pair].islamicSwapFree),
  requirements: {
    noInterest: true,
    noSwapCharges: true,
    shariahCompliant: true,
    instantSettlement: false
  },
  restrictions: {
    carryTrade: false,
    longTermPositions: 'limited',
    rolloverFees: false
  }
};

module.exports = {
  FOREX_PAIRS,
  TRADING_SESSIONS,
  ISLAMIC_TRADING,
  getForexPair: (symbol) => FOREX_PAIRS[symbol],
  getAllPairs: () => Object.values(FOREX_PAIRS),
  getMajorPairs: () => Object.values(FOREX_PAIRS).filter(pair => pair.category === 'major'),
  getMinorPairs: () => Object.values(FOREX_PAIRS).filter(pair => pair.category === 'minor'),
  getExoticPairs: () => Object.values(FOREX_PAIRS).filter(pair => pair.category === 'exotic'),
  getIslamicPairs: () => Object.values(FOREX_PAIRS).filter(pair => pair.islamicSwapFree),
  getCurrentSession: () => {
    const now = new Date();
    const utcHour = now.getUTCHours();
    
    if (utcHour >= 0 && utcHour < 9) return 'ASIA';
    if (utcHour >= 8 && utcHour < 17) return 'EUROPE';
    if (utcHour >= 13 && utcHour < 22) return 'US';
    return 'SYDNEY';
  }
};