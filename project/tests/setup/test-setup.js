/**
 * Test Setup Configuration
 * Global setup for all AI pipeline tests
 */

// Extend Jest matchers for performance testing
expect.extend({
  toBeWithinPerformanceThreshold(received, threshold, unit = 'ms') {
    const pass = received <= threshold;

    if (pass) {
      return {
        message: () => `expected ${received}${unit} not to be within threshold ${threshold}${unit}`,
        pass: true
      };
    } else {
      return {
        message: () => `expected ${received}${unit} to be within threshold ${threshold}${unit}`,
        pass: false
      };
    }
  },

  toHaveValidTradingSignal(received) {
    const validSignals = ['BUY', 'SELL', 'HOLD'];
    const hasValidSignal = received.signal && validSignals.includes(received.signal);
    const hasConfidence = typeof received.confidence === 'number' && received.confidence >= 0 && received.confidence <= 1;

    const pass = hasValidSignal && hasConfidence;

    if (pass) {
      return {
        message: () => `expected trading signal to be invalid`,
        pass: true
      };
    } else {
      return {
        message: () => `expected valid trading signal with signal in [${validSignals.join(', ')}] and confidence 0-1, but got ${JSON.stringify(received)}`,
        pass: false
      };
    }
  },

  toMeetIsolationRequirements(received, tenantId) {
    const hasCorrectTenant = received.tenantId === tenantId;
    const hasTimestamp = received.timestamp && !isNaN(new Date(received.timestamp));
    const hasProcessingTime = typeof received.processingTime === 'number' && received.processingTime > 0;

    const pass = hasCorrectTenant && hasTimestamp && hasProcessingTime;

    if (pass) {
      return {
        message: () => `expected data to not meet isolation requirements`,
        pass: true
      };
    } else {
      return {
        message: () => `expected data to meet isolation requirements for tenant ${tenantId}`,
        pass: false
      };
    }
  }
});

// Global test configuration
global.testConfig = {
  performanceTargets: {
    maxAIDecisionLatency: 15, // ms
    maxDataProcessingLatency: 50, // ms
    minThroughput: 50, // ticks per second
    maxErrorRate: 0.05 // 5%
  },

  testTimeouts: {
    unit: 5000,
    integration: 30000,
    e2e: 60000,
    performance: 120000
  },

  mockDelays: {
    fast: 5,
    normal: 10,
    slow: 20
  }
};

// Global cleanup function
global.testCleanup = async () => {
  // Clear any global state
  if (global.gc) {
    global.gc();
  }
};

// Console override for cleaner test output
const originalConsoleLog = console.log;
const originalConsoleError = console.error;

// Only show test logs in verbose mode
if (!process.env.VERBOSE_TESTS) {
  console.log = jest.fn();
  console.error = jest.fn();
}

// Restore console for specific test patterns
beforeEach(() => {
  if (expect.getState().currentTestName?.includes('benchmark') ||
      expect.getState().currentTestName?.includes('performance')) {
    console.log = originalConsoleLog;
    console.error = originalConsoleError;
  }
});

// Global error handler for unhandled promises
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

// Performance monitoring
global.performanceMonitor = {
  startTime: null,
  endTime: null,

  start() {
    this.startTime = process.hrtime.bigint();
  },

  end() {
    this.endTime = process.hrtime.bigint();
    return Number(this.endTime - this.startTime) / 1000000; // Convert to milliseconds
  }
};