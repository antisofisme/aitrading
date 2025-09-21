// Type definitions and constants for the data bridge service

// MT5 Connection States
const MT5_CONNECTION_STATES = {
  DISCONNECTED: 'disconnected',
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  RECONNECTING: 'reconnecting',
  ERROR: 'error'
};

// WebSocket Message Types
const WS_MESSAGE_TYPES = {
  WELCOME: 'welcome',
  SUBSCRIBE: 'subscribe',
  UNSUBSCRIBE: 'unsubscribe',
  SUBSCRIBED: 'subscribed',
  UNSUBSCRIBED: 'unsubscribed',
  DATA: 'data',
  ERROR: 'error',
  PING: 'ping',
  PONG: 'pong'
};

// Data Types
const DATA_TYPES = {
  TICK: 'tick',
  QUOTE: 'quote',
  BAR: 'bar',
  BOOK: 'book'
};

// Time Intervals for Bar Data
const TIME_INTERVALS = {
  M1: 'M1',    // 1 minute
  M5: 'M5',    // 5 minutes
  M15: 'M15',  // 15 minutes
  M30: 'M30',  // 30 minutes
  H1: 'H1',    // 1 hour
  H4: 'H4',    // 4 hours
  D1: 'D1'     // 1 day
};

// Error Codes
const ERROR_CODES = {
  INVALID_MESSAGE: 'INVALID_MESSAGE',
  INVALID_SYMBOL: 'INVALID_SYMBOL',
  INVALID_DATA_TYPE: 'INVALID_DATA_TYPE',
  SUBSCRIPTION_EXISTS: 'SUBSCRIPTION_EXISTS',
  SUBSCRIPTION_NOT_FOUND: 'SUBSCRIPTION_NOT_FOUND',
  MT5_DISCONNECTED: 'MT5_DISCONNECTED',
  RATE_LIMIT_EXCEEDED: 'RATE_LIMIT_EXCEEDED',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  INTERNAL_ERROR: 'INTERNAL_ERROR'
};

// Service Status
const SERVICE_STATUS = {
  STARTING: 'starting',
  HEALTHY: 'healthy',
  DEGRADED: 'degraded',
  UNHEALTHY: 'unhealthy',
  STOPPING: 'stopping'
};

/**
 * Tick data structure
 * @typedef {Object} TickData
 * @property {number} bid - Bid price
 * @property {number} ask - Ask price
 * @property {number} volume - Tick volume
 * @property {number} timestamp - Unix timestamp
 */

/**
 * Quote data structure
 * @typedef {Object} QuoteData
 * @property {number} bid - Bid price
 * @property {number} ask - Ask price
 * @property {number} timestamp - Unix timestamp
 */

/**
 * Bar/Candlestick data structure
 * @typedef {Object} BarData
 * @property {number} open - Opening price
 * @property {number} high - Highest price
 * @property {number} low - Lowest price
 * @property {number} close - Closing price
 * @property {number} volume - Volume
 * @property {number} timestamp - Unix timestamp
 */

/**
 * Market depth/book data structure
 * @typedef {Object} BookData
 * @property {Array<Object>} bids - Array of bid levels [{price, volume}]
 * @property {Array<Object>} asks - Array of ask levels [{price, volume}]
 * @property {number} timestamp - Unix timestamp
 */

/**
 * Symbol information
 * @typedef {Object} SymbolInfo
 * @property {string} symbol - Symbol name (e.g., EURUSD)
 * @property {string} description - Symbol description
 * @property {number} digits - Number of decimal places
 * @property {number} point - Point value
 * @property {number} spread - Current spread
 * @property {boolean} tradeAllowed - Whether trading is allowed
 */

/**
 * WebSocket client information
 * @typedef {Object} ClientInfo
 * @property {WebSocket} ws - WebSocket connection
 * @property {Set<string>} subscriptions - Set of subscriptions
 * @property {number} lastPing - Last ping timestamp
 * @property {string} ip - Client IP address
 * @property {string} userAgent - Client user agent
 */

/**
 * Subscription information
 * @typedef {Object} Subscription
 * @property {string} symbol - Symbol name
 * @property {string} dataType - Data type (tick, quote, bar, book)
 * @property {string} interval - Time interval (for bar data)
 * @property {Date} subscribedAt - Subscription timestamp
 * @property {Date} lastUpdate - Last data update timestamp
 */

/**
 * WebSocket message structure
 * @typedef {Object} WebSocketMessage
 * @property {string} type - Message type
 * @property {string} [symbol] - Symbol (for subscription messages)
 * @property {string} [dataType] - Data type (for subscription messages)
 * @property {string} [interval] - Time interval (for bar subscriptions)
 * @property {Object} [data] - Message data
 * @property {string} [error] - Error message
 * @property {string} timestamp - Message timestamp
 */

/**
 * API Response structure
 * @typedef {Object} ApiResponse
 * @property {boolean} success - Success flag
 * @property {Object} [data] - Response data
 * @property {string} [error] - Error message
 * @property {string} timestamp - Response timestamp
 */

/**
 * Health check result
 * @typedef {Object} HealthCheck
 * @property {string} status - Overall status (healthy, unhealthy, degraded)
 * @property {Object} checks - Individual check results
 * @property {string} timestamp - Check timestamp
 */

/**
 * Metrics data
 * @typedef {Object} Metrics
 * @property {number} uptime - Process uptime in seconds
 * @property {Object} memory - Memory usage statistics
 * @property {Object} cpu - CPU usage statistics
 * @property {Object} [mt5] - MT5 connection metrics
 * @property {number} activeConnections - Number of active WebSocket connections
 * @property {string} timestamp - Metrics timestamp
 */

// Validation helper functions
const isValidSymbol = (symbol) => {
  return typeof symbol === 'string' && /^[A-Z]{6}$/.test(symbol);
};

const isValidDataType = (dataType) => {
  return Object.values(DATA_TYPES).includes(dataType);
};

const isValidInterval = (interval) => {
  return Object.values(TIME_INTERVALS).includes(interval);
};

const isValidMessageType = (type) => {
  return Object.values(WS_MESSAGE_TYPES).includes(type);
};

// Data transformation utilities
const formatPrice = (price, digits = 5) => {
  return Number(price.toFixed(digits));
};

const formatTimestamp = (timestamp) => {
  return new Date(timestamp).toISOString();
};

const createErrorResponse = (code, message, details = null) => {
  return {
    success: false,
    error: {
      code,
      message,
      details,
      timestamp: new Date().toISOString()
    }
  };
};

const createSuccessResponse = (data, metadata = null) => {
  return {
    success: true,
    data,
    metadata,
    timestamp: new Date().toISOString()
  };
};

module.exports = {
  // Constants
  MT5_CONNECTION_STATES,
  WS_MESSAGE_TYPES,
  DATA_TYPES,
  TIME_INTERVALS,
  ERROR_CODES,
  SERVICE_STATUS,

  // Validation functions
  isValidSymbol,
  isValidDataType,
  isValidInterval,
  isValidMessageType,

  // Utility functions
  formatPrice,
  formatTimestamp,
  createErrorResponse,
  createSuccessResponse
};