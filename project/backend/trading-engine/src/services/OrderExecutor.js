const EventEmitter = require('events');
const { performance } = require('perf_hooks');
const Queue = require('bull');
const NodeCache = require('node-cache');
const logger = require('../utils/logger');

class OrderExecutor extends EventEmitter {
  constructor(options = {}) {
    super();
    
    // Performance targets
    this.targetLatency = options.targetLatency || 10; // 10ms target
    this.maxLatency = options.maxLatency || 50; // 50ms maximum
    
    // Order processing
    this.orderQueue = new Queue('order processing', {
      redis: options.redis || { host: 'localhost', port: 6379 },
      defaultJobOptions: {
        removeOnComplete: 100,
        removeOnFail: 50
      }
    });
    
    // Caching for fast lookups
    this.marketDataCache = new NodeCache({ 
      stdTTL: 1, // 1 second TTL for market data
      checkperiod: 0.1 // Check every 100ms
    });
    
    this.instrumentCache = new NodeCache({ 
      stdTTL: 300, // 5 minutes for instrument data
      checkperiod: 60
    });
    
    // Performance monitoring
    this.metrics = {
      totalOrders: 0,
      successfulOrders: 0,
      failedOrders: 0,
      averageLatency: 0,
      maxLatency: 0,
      minLatency: Infinity,
      ordersPerSecond: 0,
      lastSecondOrders: 0,
      latencyHistory: [],
      performanceAlerts: []
    };
    
    // Order states
    this.pendingOrders = new Map();
    this.executedOrders = new Map();
    this.rejectedOrders = new Map();
    
    // Circuit breaker for market disruptions
    this.circuitBreaker = {
      isOpen: false,
      failureCount: 0,
      threshold: options.circuitBreakerThreshold || 10,
      timeout: options.circuitBreakerTimeout || 30000
    };
    
    this.initializeOrderProcessor();
    this.startPerformanceMonitoring();
  }

  /**
   * Initialize high-performance order processor
   */
  initializeOrderProcessor() {
    // Process orders with high concurrency
    this.orderQueue.process('market_order', 10, this.processMarketOrder.bind(this));
    this.orderQueue.process('limit_order', 5, this.processLimitOrder.bind(this));
    this.orderQueue.process('stop_order', 5, this.processStopOrder.bind(this));
    
    // Handle queue events
    this.orderQueue.on('completed', this.onOrderCompleted.bind(this));
    this.orderQueue.on('failed', this.onOrderFailed.bind(this));
    this.orderQueue.on('stalled', this.onOrderStalled.bind(this));
    
    logger.info('High-performance order executor initialized', {
      targetLatency: this.targetLatency,
      maxLatency: this.maxLatency,
      circuitBreakerThreshold: this.circuitBreaker.threshold
    });
  }

  /**
   * Execute order with performance optimization
   */
  async executeOrder(order) {
    const startTime = performance.now();
    const orderId = this.generateOrderId();
    
    try {
      // Validate order
      const validation = await this.validateOrder(order);
      if (!validation.isValid) {
        throw new Error(`Order validation failed: ${validation.errors.join(', ')}`);
      }
      
      // Check circuit breaker
      if (this.circuitBreaker.isOpen) {
        throw new Error('Order execution suspended due to market disruption');
      }
      
      // Pre-process order
      const processedOrder = {
        ...order,
        id: orderId,
        timestamp: Date.now(),
        startTime,
        status: 'pending',
        executionMethod: this.determineExecutionMethod(order)
      };
      
      this.pendingOrders.set(orderId, processedOrder);
      
      // Add to appropriate queue based on order type
      const jobOptions = {
        priority: this.calculateOrderPriority(order),
        attempts: 3,
        backoff: { type: 'exponential', settings: { delay: 100 } }
      };
      
      let job;
      switch (order.type.toLowerCase()) {
        case 'market':
          job = await this.orderQueue.add('market_order', processedOrder, jobOptions);
          break;
        case 'limit':
          job = await this.orderQueue.add('limit_order', processedOrder, jobOptions);
          break;
        case 'stop':
        case 'stop_loss':
        case 'take_profit':
          job = await this.orderQueue.add('stop_order', processedOrder, jobOptions);
          break;
        default:
          throw new Error(`Unsupported order type: ${order.type}`);
      }
      
      processedOrder.jobId = job.id;
      
      // Return immediately for async processing
      return {
        orderId,
        status: 'queued',
        jobId: job.id,
        estimatedExecution: Date.now() + 100, // 100ms estimate
        queuePosition: await this.getQueuePosition(job.id)
      };
      
    } catch (error) {
      const endTime = performance.now();
      const latency = endTime - startTime;
      
      this.recordFailedOrder(orderId, error, latency);
      
      throw error;
    }
  }

  /**
   * Process market order with optimized execution
   */
  async processMarketOrder(job) {
    const order = job.data;
    const startTime = performance.now();
    
    try {
      // Get real-time market data
      const marketData = await this.getMarketData(order.symbol);
      if (!marketData) {
        throw new Error(`No market data available for ${order.symbol}`);
      }
      
      // Calculate execution price
      const executionPrice = order.side === 'buy' ? marketData.ask : marketData.bid;
      
      // Check slippage tolerance
      if (order.maxSlippage && this.calculateSlippage(order.price, executionPrice) > order.maxSlippage) {
        throw new Error('Slippage exceeds maximum tolerance');
      }
      
      // Execute order through MT5 bridge
      const execution = await this.executeAtMarket(order, executionPrice, marketData);
      
      const endTime = performance.now();
      const latency = endTime - startTime;
      
      // Record successful execution
      this.recordSuccessfulOrder(order.id, execution, latency);
      
      return {
        orderId: order.id,
        executionId: execution.id,
        price: execution.price,
        quantity: execution.quantity,
        commission: execution.commission,
        latency,
        timestamp: Date.now()
      };
      
    } catch (error) {
      const endTime = performance.now();
      const latency = endTime - startTime;
      
      this.recordFailedOrder(order.id, error, latency);
      throw error;
    }
  }

  /**
   * Process limit order
   */
  async processLimitOrder(job) {
    const order = job.data;
    const startTime = performance.now();
    
    try {
      const marketData = await this.getMarketData(order.symbol);
      const currentPrice = order.side === 'buy' ? marketData.ask : marketData.bid;
      
      // Check if limit price can be filled
      const canFill = order.side === 'buy' 
        ? currentPrice <= order.price
        : currentPrice >= order.price;
      
      if (canFill) {
        // Execute immediately
        const execution = await this.executeAtLimit(order, order.price, marketData);
        
        const endTime = performance.now();
        const latency = endTime - startTime;
        
        this.recordSuccessfulOrder(order.id, execution, latency);
        
        return {
          orderId: order.id,
          executionId: execution.id,
          price: execution.price,
          quantity: execution.quantity,
          commission: execution.commission,
          latency,
          timestamp: Date.now()
        };
      } else {
        // Place as pending limit order
        await this.placePendingLimitOrder(order);
        
        const endTime = performance.now();
        const latency = endTime - startTime;
        
        return {
          orderId: order.id,
          status: 'pending',
          limitPrice: order.price,
          currentPrice,
          latency,
          timestamp: Date.now()
        };
      }
      
    } catch (error) {
      const endTime = performance.now();
      const latency = endTime - startTime;
      
      this.recordFailedOrder(order.id, error, latency);
      throw error;
    }
  }

  /**
   * Process stop order
   */
  async processStopOrder(job) {
    const order = job.data;
    const startTime = performance.now();
    
    try {
      const marketData = await this.getMarketData(order.symbol);
      const currentPrice = order.side === 'buy' ? marketData.ask : marketData.bid;
      
      // Check if stop price is triggered
      const isTriggered = order.side === 'buy'
        ? currentPrice >= order.stopPrice
        : currentPrice <= order.stopPrice;
      
      if (isTriggered) {
        // Convert to market order and execute
        const execution = await this.executeAtMarket({
          ...order,
          type: 'market'
        }, currentPrice, marketData);
        
        const endTime = performance.now();
        const latency = endTime - startTime;
        
        this.recordSuccessfulOrder(order.id, execution, latency);
        
        return {
          orderId: order.id,
          executionId: execution.id,
          price: execution.price,
          quantity: execution.quantity,
          commission: execution.commission,
          triggerPrice: order.stopPrice,
          latency,
          timestamp: Date.now()
        };
      } else {
        // Place as pending stop order
        await this.placePendingStopOrder(order);
        
        const endTime = performance.now();
        const latency = endTime - startTime;
        
        return {
          orderId: order.id,
          status: 'pending',
          stopPrice: order.stopPrice,
          currentPrice,
          latency,
          timestamp: Date.now()
        };
      }
      
    } catch (error) {
      const endTime = performance.now();
      const latency = endTime - startTime;
      
      this.recordFailedOrder(order.id, error, latency);
      throw error;
    }
  }

  /**
   * Get market data with caching
   */
  async getMarketData(symbol) {
    // Check cache first
    let marketData = this.marketDataCache.get(symbol);
    
    if (!marketData) {
      // Fetch from MT5 bridge with timeout
      const timeout = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Market data timeout')), 1000)
      );
      
      const dataPromise = this.fetchMarketDataFromMT5(symbol);
      
      try {
        marketData = await Promise.race([dataPromise, timeout]);
        this.marketDataCache.set(symbol, marketData);
      } catch (error) {
        logger.error('Failed to fetch market data', { symbol, error: error.message });
        throw error;
      }
    }
    
    return marketData;
  }

  /**
   * Fetch market data from MT5 bridge
   */
  async fetchMarketDataFromMT5(symbol) {
    // This would integrate with the existing MT5 data-bridge
    // For now, return mock data with realistic properties
    const basePrice = this.getBasePrice(symbol);
    const spread = this.getSpread(symbol);
    
    return {
      symbol,
      bid: basePrice,
      ask: basePrice + spread,
      timestamp: Date.now(),
      volume: Math.floor(Math.random() * 1000) + 100,
      source: 'mt5_bridge'
    };
  }

  /**
   * Execute order at market price
   */
  async executeAtMarket(order, price, marketData) {
    // Simulate execution through MT5
    const execution = {
      id: this.generateExecutionId(),
      orderId: order.id,
      symbol: order.symbol,
      side: order.side,
      quantity: order.quantity,
      price: price,
      commission: this.calculateCommission(order, price),
      spread: Math.abs(marketData.ask - marketData.bid),
      timestamp: Date.now(),
      source: 'mt5_execution'
    };
    
    // In real implementation, this would call MT5 API
    // await this.mt5Bridge.executeOrder(execution);
    
    return execution;
  }

  /**
   * Execute order at limit price
   */
  async executeAtLimit(order, price, marketData) {
    const execution = {
      id: this.generateExecutionId(),
      orderId: order.id,
      symbol: order.symbol,
      side: order.side,
      quantity: order.quantity,
      price: price,
      commission: this.calculateCommission(order, price),
      executionType: 'limit',
      timestamp: Date.now(),
      source: 'mt5_execution'
    };
    
    return execution;
  }

  /**
   * Validate order before execution
   */
  async validateOrder(order) {
    const validation = {
      isValid: true,
      errors: [],
      warnings: []
    };
    
    // Required fields
    if (!order.symbol) validation.errors.push('Symbol is required');
    if (!order.side) validation.errors.push('Side (buy/sell) is required');
    if (!order.quantity || order.quantity <= 0) validation.errors.push('Valid quantity is required');
    if (!order.type) validation.errors.push('Order type is required');
    
    // Symbol validation
    if (order.symbol && !this.isValidSymbol(order.symbol)) {
      validation.errors.push(`Invalid symbol: ${order.symbol}`);
    }
    
    // Quantity limits
    if (order.quantity > 10000000) { // 10M max
      validation.errors.push('Quantity exceeds maximum limit');
    }
    
    // Price validation for limit orders
    if (order.type === 'limit' && (!order.price || order.price <= 0)) {
      validation.errors.push('Limit orders require a valid price');
    }
    
    // Stop price validation
    if ((order.type === 'stop' || order.type === 'stop_loss') && (!order.stopPrice || order.stopPrice <= 0)) {
      validation.errors.push('Stop orders require a valid stop price');
    }
    
    validation.isValid = validation.errors.length === 0;
    
    return validation;
  }

  /**
   * Determine optimal execution method
   */
  determineExecutionMethod(order) {
    if (order.quantity > 1000000) {
      return 'iceberg'; // Large orders use iceberg strategy
    }
    
    if (order.type === 'market' && order.urgency === 'high') {
      return 'direct'; // High priority direct execution
    }
    
    return 'standard';
  }

  /**
   * Calculate order priority for queue
   */
  calculateOrderPriority(order) {
    let priority = 0;
    
    // Market orders get higher priority
    if (order.type === 'market') priority += 10;
    
    // Larger orders get higher priority
    if (order.quantity > 100000) priority += 5;
    
    // Urgent orders
    if (order.urgency === 'high') priority += 15;
    
    // VIP accounts
    if (order.accountType === 'vip') priority += 8;
    
    return priority;
  }

  /**
   * Calculate slippage
   */
  calculateSlippage(expectedPrice, executionPrice) {
    return Math.abs((executionPrice - expectedPrice) / expectedPrice) * 100;
  }

  /**
   * Calculate commission
   */
  calculateCommission(order, price) {
    const notionalValue = order.quantity * price;
    const commissionRate = 0.0002; // 0.02%
    return notionalValue * commissionRate;
  }

  /**
   * Record successful order execution
   */
  recordSuccessfulOrder(orderId, execution, latency) {
    this.metrics.totalOrders++;
    this.metrics.successfulOrders++;
    
    this.updateLatencyMetrics(latency);
    
    // Move from pending to executed
    const pendingOrder = this.pendingOrders.get(orderId);
    if (pendingOrder) {
      this.pendingOrders.delete(orderId);
      this.executedOrders.set(orderId, {
        ...pendingOrder,
        execution,
        status: 'executed',
        latency,
        completedAt: Date.now()
      });
    }
    
    // Emit success event
    this.emit('orderExecuted', {
      orderId,
      execution,
      latency,
      timestamp: Date.now()
    });
  }

  /**
   * Record failed order
   */
  recordFailedOrder(orderId, error, latency) {
    this.metrics.totalOrders++;
    this.metrics.failedOrders++;
    
    this.updateLatencyMetrics(latency);
    
    // Update circuit breaker
    this.circuitBreaker.failureCount++;
    if (this.circuitBreaker.failureCount >= this.circuitBreaker.threshold) {
      this.openCircuitBreaker();
    }
    
    // Move from pending to rejected
    const pendingOrder = this.pendingOrders.get(orderId);
    if (pendingOrder) {
      this.pendingOrders.delete(orderId);
      this.rejectedOrders.set(orderId, {
        ...pendingOrder,
        error: error.message,
        status: 'rejected',
        latency,
        rejectedAt: Date.now()
      });
    }
    
    // Emit failure event
    this.emit('orderFailed', {
      orderId,
      error: error.message,
      latency,
      timestamp: Date.now()
    });
  }

  /**
   * Update latency metrics
   */
  updateLatencyMetrics(latency) {
    this.metrics.latencyHistory.push(latency);
    
    // Keep only last 1000 latency measurements
    if (this.metrics.latencyHistory.length > 1000) {
      this.metrics.latencyHistory.shift();
    }
    
    // Update statistics
    this.metrics.maxLatency = Math.max(this.metrics.maxLatency, latency);
    this.metrics.minLatency = Math.min(this.metrics.minLatency, latency);
    this.metrics.averageLatency = this.metrics.latencyHistory.reduce((a, b) => a + b, 0) / this.metrics.latencyHistory.length;
    
    // Check performance alerts
    if (latency > this.targetLatency) {
      this.metrics.performanceAlerts.push({
        type: 'high_latency',
        latency,
        target: this.targetLatency,
        timestamp: Date.now()
      });
      
      this.emit('performanceAlert', {
        type: 'high_latency',
        latency,
        target: this.targetLatency
      });
    }
  }

  /**
   * Open circuit breaker
   */
  openCircuitBreaker() {
    this.circuitBreaker.isOpen = true;
    
    logger.warn('Circuit breaker opened due to high failure rate', {
      failureCount: this.circuitBreaker.failureCount,
      threshold: this.circuitBreaker.threshold
    });
    
    // Close after timeout
    setTimeout(() => {
      this.circuitBreaker.isOpen = false;
      this.circuitBreaker.failureCount = 0;
      logger.info('Circuit breaker closed');
    }, this.circuitBreaker.timeout);
    
    this.emit('circuitBreakerOpen', {
      failureCount: this.circuitBreaker.failureCount,
      timestamp: Date.now()
    });
  }

  /**
   * Start performance monitoring
   */
  startPerformanceMonitoring() {
    // Monitor orders per second
    setInterval(() => {
      this.metrics.ordersPerSecond = this.metrics.lastSecondOrders;
      this.metrics.lastSecondOrders = 0;
    }, 1000);
    
    // Clean up old data
    setInterval(() => {
      this.cleanupOldOrders();
    }, 300000); // Every 5 minutes
  }

  /**
   * Clean up old orders
   */
  cleanupOldOrders() {
    const cutoff = Date.now() - (24 * 60 * 60 * 1000); // 24 hours ago
    
    for (const [orderId, order] of this.executedOrders.entries()) {
      if (order.completedAt < cutoff) {
        this.executedOrders.delete(orderId);
      }
    }
    
    for (const [orderId, order] of this.rejectedOrders.entries()) {
      if (order.rejectedAt < cutoff) {
        this.rejectedOrders.delete(orderId);
      }
    }
  }

  /**
   * Get performance metrics
   */
  getPerformanceMetrics() {
    return {
      ...this.metrics,
      successRate: this.metrics.totalOrders > 0 
        ? (this.metrics.successfulOrders / this.metrics.totalOrders) * 100 
        : 0,
      pendingOrders: this.pendingOrders.size,
      executedOrders: this.executedOrders.size,
      rejectedOrders: this.rejectedOrders.size,
      circuitBreakerStatus: this.circuitBreaker.isOpen ? 'open' : 'closed',
      targetLatency: this.targetLatency,
      performanceStatus: this.getPerformanceStatus()
    };
  }

  /**
   * Get performance status
   */
  getPerformanceStatus() {
    if (this.metrics.averageLatency <= this.targetLatency) {
      return 'excellent';
    } else if (this.metrics.averageLatency <= this.maxLatency) {
      return 'good';
    } else {
      return 'degraded';
    }
  }

  /**
   * Helper methods
   */
  generateOrderId() {
    return `ORD_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  generateExecutionId() {
    return `EXE_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  isValidSymbol(symbol) {
    // This would check against the forex pairs configuration
    const validSymbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'XAGUSD']; // Simplified
    return validSymbols.includes(symbol);
  }

  getBasePrice(symbol) {
    const basePrices = {
      'EURUSD': 1.0500,
      'GBPUSD': 1.2500,
      'USDJPY': 150.00,
      'XAUUSD': 2000.00,
      'XAGUSD': 25.00
    };
    return basePrices[symbol] || 1.0000;
  }

  getSpread(symbol) {
    const spreads = {
      'EURUSD': 0.0001,
      'GBPUSD': 0.0002,
      'USDJPY': 0.002,
      'XAUUSD': 0.5,
      'XAGUSD': 0.02
    };
    return spreads[symbol] || 0.0001;
  }

  async getQueuePosition(jobId) {
    const waiting = await this.orderQueue.getWaiting();
    return waiting.findIndex(job => job.id === jobId) + 1;
  }

  async placePendingLimitOrder(order) {
    // Implementation for pending limit orders
    logger.info('Placed pending limit order', { orderId: order.id, price: order.price });
  }

  async placePendingStopOrder(order) {
    // Implementation for pending stop orders
    logger.info('Placed pending stop order', { orderId: order.id, stopPrice: order.stopPrice });
  }

  // Event handlers
  onOrderCompleted(job, result) {
    this.metrics.lastSecondOrders++;
    logger.debug('Order completed', { jobId: job.id, orderId: result.orderId });
  }

  onOrderFailed(job, error) {
    logger.error('Order failed', { jobId: job.id, error: error.message });
  }

  onOrderStalled(job) {
    logger.warn('Order stalled', { jobId: job.id });
  }
}

module.exports = OrderExecutor;