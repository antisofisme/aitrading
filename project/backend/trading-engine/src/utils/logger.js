const winston = require('winston');
const path = require('path');

// Custom format for trading logs
const tradingFormat = winston.format.combine(
  winston.format.timestamp({
    format: 'YYYY-MM-DD HH:mm:ss.SSS'
  }),
  winston.format.errors({ stack: true }),
  winston.format.json(),
  winston.format.printf(({ timestamp, level, message, ...meta }) => {
    return JSON.stringify({
      timestamp,
      level,
      service: 'trading-engine',
      message,
      ...meta
    });
  })
);

// Create logger with multiple transports
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: tradingFormat,
  transports: [
    // Console transport for development
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple()
      )
    }),
    
    // File transport for all logs
    new winston.transports.File({
      filename: path.join(__dirname, '../../logs/trading-engine.log'),
      maxsize: 50 * 1024 * 1024, // 50MB
      maxFiles: 10
    }),
    
    // Separate file for errors
    new winston.transports.File({
      filename: path.join(__dirname, '../../logs/trading-errors.log'),
      level: 'error',
      maxsize: 10 * 1024 * 1024, // 10MB
      maxFiles: 5
    }),
    
    // High-frequency trading logs
    new winston.transports.File({
      filename: path.join(__dirname, '../../logs/order-execution.log'),
      maxsize: 100 * 1024 * 1024, // 100MB
      maxFiles: 20,
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
      )
    })
  ]
});

// Add specialized logging methods for trading
logger.order = {
  executed: (orderId, execution, latency) => {
    logger.info('Order executed', {
      category: 'order_execution',
      orderId,
      symbol: execution.symbol,
      side: execution.side,
      quantity: execution.quantity,
      price: execution.price,
      latency,
      timestamp: Date.now()
    });
  },
  
  failed: (orderId, error, latency) => {
    logger.error('Order failed', {
      category: 'order_failure',
      orderId,
      error: error.message,
      latency,
      timestamp: Date.now()
    });
  },
  
  queued: (orderId, orderType, priority) => {
    logger.debug('Order queued', {
      category: 'order_queue',
      orderId,
      orderType,
      priority,
      timestamp: Date.now()
    });
  }
};

logger.performance = {
  latency: (operation, latency, target) => {
    const status = latency <= target ? 'within_target' : 'exceeded_target';
    logger.info('Performance metric', {
      category: 'performance',
      operation,
      latency,
      target,
      status,
      timestamp: Date.now()
    });
  },
  
  alert: (type, metric, threshold, current) => {
    logger.warn('Performance alert', {
      category: 'performance_alert',
      type,
      metric,
      threshold,
      current,
      timestamp: Date.now()
    });
  }
};

logger.correlation = {
  update: (symbol1, symbol2, correlation, strength) => {
    logger.debug('Correlation update', {
      category: 'correlation',
      symbol1,
      symbol2,
      correlation,
      strength,
      timestamp: Date.now()
    });
  },
  
  alert: (symbol1, symbol2, correlation, threshold) => {
    logger.info('High correlation detected', {
      category: 'correlation_alert',
      symbol1,
      symbol2,
      correlation,
      threshold,
      timestamp: Date.now()
    });
  }
};

logger.session = {
  start: (sessionName, characteristics) => {
    logger.info('Trading session started', {
      category: 'session',
      sessionName,
      characteristics,
      timestamp: Date.now()
    });
  },
  
  end: (sessionName, metrics) => {
    logger.info('Trading session ended', {
      category: 'session',
      sessionName,
      metrics,
      timestamp: Date.now()
    });
  },
  
  overlap: (sessions, recommendations) => {
    logger.info('Session overlap detected', {
      category: 'session_overlap',
      sessions,
      recommendations,
      timestamp: Date.now()
    });
  }
};

logger.islamic = {
  validation: (accountId, isValid, violations) => {
    logger.info('Islamic trading validation', {
      category: 'islamic_validation',
      accountId,
      isValid,
      violations,
      timestamp: Date.now()
    });
  },
  
  swapFree: (accountId, positionId, savedAmount) => {
    logger.info('Swap-free calculation applied', {
      category: 'islamic_swap_free',
      accountId,
      positionId,
      savedAmount,
      timestamp: Date.now()
    });
  }
};

logger.market = {
  data: (symbol, bid, ask, spread, latency) => {
    logger.debug('Market data received', {
      category: 'market_data',
      symbol,
      bid,
      ask,
      spread,
      latency,
      timestamp: Date.now()
    });
  },
  
  volatility: (symbol, volatility, classification) => {
    logger.info('Volatility update', {
      category: 'market_volatility',
      symbol,
      volatility,
      classification,
      timestamp: Date.now()
    });
  }
};

// Error handling for uncaught exceptions
process.on('uncaughtException', (error) => {
  logger.error('Uncaught Exception', {
    category: 'system_error',
    error: error.message,
    stack: error.stack,
    timestamp: Date.now()
  });
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled Rejection', {
    category: 'system_error',
    reason,
    promise,
    timestamp: Date.now()
  });
});

module.exports = logger;