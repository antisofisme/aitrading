const OrderExecutor = require('../../src/services/OrderExecutor');
const logger = require('../../src/utils/logger');

// Mock dependencies
jest.mock('bull', () => {
  return jest.fn().mockImplementation(() => ({
    add: jest.fn().mockResolvedValue({ id: 'job-123' }),
    process: jest.fn(),
    on: jest.fn(),
    getWaiting: jest.fn().mockResolvedValue([])
  }));
});

jest.mock('node-cache');
jest.mock('../../src/utils/logger');

describe('OrderExecutor', () => {
  let orderExecutor;
  const mockOptions = {
    targetLatency: 10,
    maxLatency: 50,
    redis: { host: 'localhost', port: 6379 }
  };

  beforeEach(() => {
    orderExecutor = new OrderExecutor(mockOptions);
    jest.clearAllMocks();
  });

  afterEach(() => {
    if (orderExecutor) {
      // Clean up any intervals or timers
    }
  });

  describe('Constructor', () => {
    it('should initialize with default options', () => {
      const executor = new OrderExecutor();
      expect(executor.targetLatency).toBe(10);
      expect(executor.maxLatency).toBe(50);
    });

    it('should initialize with custom options', () => {
      expect(orderExecutor.targetLatency).toBe(10);
      expect(orderExecutor.maxLatency).toBe(50);
    });

    it('should initialize metrics', () => {
      expect(orderExecutor.metrics).toBeDefined();
      expect(orderExecutor.metrics.totalOrders).toBe(0);
      expect(orderExecutor.metrics.successfulOrders).toBe(0);
      expect(orderExecutor.metrics.failedOrders).toBe(0);
    });
  });

  describe('executeOrder', () => {
    const validOrder = {
      symbol: 'EURUSD',
      side: 'buy',
      quantity: 10000,
      type: 'market'
    };

    it('should execute a valid market order', async () => {
      const result = await orderExecutor.executeOrder(validOrder);
      
      expect(result).toBeDefined();
      expect(result.orderId).toBeDefined();
      expect(result.status).toBe('queued');
      expect(result.jobId).toBe('job-123');
    });

    it('should reject invalid orders', async () => {
      const invalidOrder = {
        symbol: '',
        side: 'buy',
        quantity: -1000,
        type: 'market'
      };

      await expect(orderExecutor.executeOrder(invalidOrder))
        .rejects.toThrow('Order validation failed');
    });

    it('should reject orders when circuit breaker is open', async () => {
      // Open circuit breaker
      orderExecutor.circuitBreaker.isOpen = true;

      await expect(orderExecutor.executeOrder(validOrder))
        .rejects.toThrow('Order execution suspended due to market disruption');
    });

    it('should calculate order priority correctly', () => {
      const marketOrder = { type: 'market', quantity: 100000, urgency: 'high', accountType: 'vip' };
      const priority = orderExecutor.calculateOrderPriority(marketOrder);
      
      expect(priority).toBe(38); // 10 + 5 + 15 + 8
    });
  });

  describe('validateOrder', () => {
    it('should validate correct orders', async () => {
      const validOrder = {
        symbol: 'EURUSD',
        side: 'buy',
        quantity: 10000,
        type: 'market'
      };

      const validation = await orderExecutor.validateOrder(validOrder);
      expect(validation.isValid).toBe(true);
      expect(validation.errors).toHaveLength(0);
    });

    it('should reject orders with missing required fields', async () => {
      const invalidOrder = {
        side: 'buy',
        quantity: 10000
        // missing symbol and type
      };

      const validation = await orderExecutor.validateOrder(invalidOrder);
      expect(validation.isValid).toBe(false);
      expect(validation.errors).toContain('Symbol is required');
      expect(validation.errors).toContain('Order type is required');
    });

    it('should reject orders with invalid quantity', async () => {
      const invalidOrder = {
        symbol: 'EURUSD',
        side: 'buy',
        quantity: -1000,
        type: 'market'
      };

      const validation = await orderExecutor.validateOrder(invalidOrder);
      expect(validation.isValid).toBe(false);
      expect(validation.errors).toContain('Valid quantity is required');
    });

    it('should reject orders with excessive quantity', async () => {
      const invalidOrder = {
        symbol: 'EURUSD',
        side: 'buy',
        quantity: 20000000, // Exceeds 10M limit
        type: 'market'
      };

      const validation = await orderExecutor.validateOrder(invalidOrder);
      expect(validation.isValid).toBe(false);
      expect(validation.errors).toContain('Quantity exceeds maximum limit');
    });

    it('should require price for limit orders', async () => {
      const limitOrder = {
        symbol: 'EURUSD',
        side: 'buy',
        quantity: 10000,
        type: 'limit'
        // missing price
      };

      const validation = await orderExecutor.validateOrder(limitOrder);
      expect(validation.isValid).toBe(false);
      expect(validation.errors).toContain('Limit orders require a valid price');
    });

    it('should require stop price for stop orders', async () => {
      const stopOrder = {
        symbol: 'EURUSD',
        side: 'buy',
        quantity: 10000,
        type: 'stop'
        // missing stopPrice
      };

      const validation = await orderExecutor.validateOrder(stopOrder);
      expect(validation.isValid).toBe(false);
      expect(validation.errors).toContain('Stop orders require a valid stop price');
    });
  });

  describe('Performance Metrics', () => {
    it('should track successful orders', () => {
      const orderId = 'test-order-1';
      const execution = {
        id: 'exec-1',
        symbol: 'EURUSD',
        side: 'buy',
        quantity: 10000,
        price: 1.0500
      };
      const latency = 15;

      orderExecutor.recordSuccessfulOrder(orderId, execution, latency);

      expect(orderExecutor.metrics.totalOrders).toBe(1);
      expect(orderExecutor.metrics.successfulOrders).toBe(1);
      expect(orderExecutor.metrics.failedOrders).toBe(0);
    });

    it('should track failed orders', () => {
      const orderId = 'test-order-2';
      const error = new Error('Market closed');
      const latency = 5;

      orderExecutor.recordFailedOrder(orderId, error, latency);

      expect(orderExecutor.metrics.totalOrders).toBe(1);
      expect(orderExecutor.metrics.successfulOrders).toBe(0);
      expect(orderExecutor.metrics.failedOrders).toBe(1);
    });

    it('should update latency metrics', () => {
      const latencies = [10, 15, 20, 12, 8];
      
      latencies.forEach(latency => {
        orderExecutor.updateLatencyMetrics(latency);
      });

      expect(orderExecutor.metrics.latencyHistory).toEqual(latencies);
      expect(orderExecutor.metrics.averageLatency).toBe(13); // (10+15+20+12+8)/5
      expect(orderExecutor.metrics.maxLatency).toBe(20);
      expect(orderExecutor.metrics.minLatency).toBe(8);
    });

    it('should generate performance alerts for high latency', () => {
      const highLatency = 25; // Above target of 10ms
      
      orderExecutor.updateLatencyMetrics(highLatency);

      expect(orderExecutor.metrics.performanceAlerts).toHaveLength(1);
      expect(orderExecutor.metrics.performanceAlerts[0].type).toBe('high_latency');
      expect(orderExecutor.metrics.performanceAlerts[0].latency).toBe(25);
    });

    it('should calculate success rate correctly', () => {
      // Add some orders
      orderExecutor.metrics.totalOrders = 10;
      orderExecutor.metrics.successfulOrders = 8;
      orderExecutor.metrics.failedOrders = 2;

      const metrics = orderExecutor.getPerformanceMetrics();
      expect(metrics.successRate).toBe(80); // 8/10 * 100
    });

    it('should determine performance status', () => {
      // Test excellent performance
      orderExecutor.metrics.averageLatency = 8;
      expect(orderExecutor.getPerformanceStatus()).toBe('excellent');

      // Test good performance
      orderExecutor.metrics.averageLatency = 30;
      expect(orderExecutor.getPerformanceStatus()).toBe('good');

      // Test degraded performance
      orderExecutor.metrics.averageLatency = 60;
      expect(orderExecutor.getPerformanceStatus()).toBe('degraded');
    });
  });

  describe('Circuit Breaker', () => {
    it('should open circuit breaker after threshold failures', () => {
      const threshold = orderExecutor.circuitBreaker.threshold;
      
      // Simulate failures up to threshold
      for (let i = 0; i < threshold; i++) {
        orderExecutor.recordFailedOrder(`order-${i}`, new Error('Test error'), 10);
      }

      expect(orderExecutor.circuitBreaker.isOpen).toBe(true);
    });

    it('should close circuit breaker after timeout', (done) => {
      // Set short timeout for testing
      orderExecutor.circuitBreaker.timeout = 100;
      
      // Open circuit breaker
      orderExecutor.circuitBreaker.isOpen = true;
      orderExecutor.circuitBreaker.failureCount = orderExecutor.circuitBreaker.threshold;
      
      orderExecutor.openCircuitBreaker();

      // Wait for timeout
      setTimeout(() => {
        expect(orderExecutor.circuitBreaker.isOpen).toBe(false);
        expect(orderExecutor.circuitBreaker.failureCount).toBe(0);
        done();
      }, 150);
    });
  });

  describe('Order Processing', () => {
    it('should process market orders', async () => {
      const order = {
        id: 'test-order',
        symbol: 'EURUSD',
        side: 'buy',
        quantity: 10000,
        type: 'market',
        startTime: Date.now()
      };

      // Mock market data
      orderExecutor.getMarketData = jest.fn().mockResolvedValue({
        symbol: 'EURUSD',
        bid: 1.0500,
        ask: 1.0502,
        timestamp: Date.now()
      });

      orderExecutor.executeAtMarket = jest.fn().mockResolvedValue({
        id: 'exec-1',
        price: 1.0502,
        quantity: 10000,
        commission: 2.1
      });

      const job = { data: order };
      const result = await orderExecutor.processMarketOrder(job);

      expect(result.orderId).toBe('test-order');
      expect(result.price).toBe(1.0502);
      expect(orderExecutor.executeAtMarket).toHaveBeenCalled();
    });

    it('should handle slippage tolerance', async () => {
      const order = {
        id: 'test-order',
        symbol: 'EURUSD',
        side: 'buy',
        quantity: 10000,
        type: 'market',
        price: 1.0500,
        maxSlippage: 0.0001, // 1 pip
        startTime: Date.now()
      };

      // Mock market data with high slippage
      orderExecutor.getMarketData = jest.fn().mockResolvedValue({
        symbol: 'EURUSD',
        bid: 1.0500,
        ask: 1.0505, // 5 pips slippage
        timestamp: Date.now()
      });

      const job = { data: order };
      
      await expect(orderExecutor.processMarketOrder(job))
        .rejects.toThrow('Slippage exceeds maximum tolerance');
    });
  });

  describe('Helper Functions', () => {
    it('should generate unique order IDs', () => {
      const id1 = orderExecutor.generateOrderId();
      const id2 = orderExecutor.generateOrderId();
      
      expect(id1).toMatch(/^ORD_\d+_[a-z0-9]+$/);
      expect(id2).toMatch(/^ORD_\d+_[a-z0-9]+$/);
      expect(id1).not.toBe(id2);
    });

    it('should generate unique execution IDs', () => {
      const id1 = orderExecutor.generateExecutionId();
      const id2 = orderExecutor.generateExecutionId();
      
      expect(id1).toMatch(/^EXE_\d+_[a-z0-9]+$/);
      expect(id2).toMatch(/^EXE_\d+_[a-z0-9]+$/);
      expect(id1).not.toBe(id2);
    });

    it('should validate symbols correctly', () => {
      expect(orderExecutor.isValidSymbol('EURUSD')).toBe(true);
      expect(orderExecutor.isValidSymbol('GBPUSD')).toBe(true);
      expect(orderExecutor.isValidSymbol('XAUUSD')).toBe(true);
      expect(orderExecutor.isValidSymbol('INVALID')).toBe(false);
    });

    it('should calculate slippage correctly', () => {
      const expectedPrice = 1.0500;
      const executionPrice = 1.0505;
      
      const slippage = orderExecutor.calculateSlippage(expectedPrice, executionPrice);
      expect(slippage).toBeCloseTo(0.476, 2); // ~0.48%
    });

    it('should calculate commission correctly', () => {
      const order = { quantity: 100000 };
      const price = 1.0500;
      
      const commission = orderExecutor.calculateCommission(order, price);
      expect(commission).toBe(21); // 100000 * 1.0500 * 0.0002
    });

    it('should get base price for symbols', () => {
      expect(orderExecutor.getBasePrice('EURUSD')).toBe(1.0500);
      expect(orderExecutor.getBasePrice('XAUUSD')).toBe(2000.00);
      expect(orderExecutor.getBasePrice('UNKNOWN')).toBe(1.0000);
    });

    it('should get spread for symbols', () => {
      expect(orderExecutor.getSpread('EURUSD')).toBe(0.0001);
      expect(orderExecutor.getSpread('XAUUSD')).toBe(0.5);
      expect(orderExecutor.getSpread('UNKNOWN')).toBe(0.0001);
    });
  });
});