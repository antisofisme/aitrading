const ErrorCategorizer = require('../src/categorizer');
const path = require('path');

describe('ErrorCategorizer', () => {
  let categorizer;

  beforeEach(async () => {
    categorizer = new ErrorCategorizer();
    await categorizer.init();
  });

  describe('initialization', () => {
    test('should initialize with default config', async () => {
      expect(categorizer.categories).toBeDefined();
      expect(categorizer.severityLevels).toBeDefined();
      expect(Object.keys(categorizer.categories)).toContain('SYSTEM');
      expect(Object.keys(categorizer.categories)).toContain('API');
      expect(Object.keys(categorizer.categories)).toContain('TRADING');
    });

    test('should load categories from config file', () => {
      expect(categorizer.categories.SYSTEM).toBeDefined();
      expect(categorizer.categories.SYSTEM.severity).toBe('HIGH');
      expect(categorizer.categories.TRADING.severity).toBe('CRITICAL');
    });
  });

  describe('error categorization', () => {
    test('should categorize database errors as SYSTEM', () => {
      const error = {
        message: 'Database connection failed',
        stack: 'Error: ECONNREFUSED localhost:5432',
        code: 'ECONNREFUSED'
      };

      const result = categorizer.categorize(error);

      expect(result.category).toBe('SYSTEM');
      expect(result.subcategory).toBe('DATABASE');
      expect(result.severity).toBe('HIGH');
      expect(result.confidence).toBeGreaterThan(0.5);
    });

    test('should categorize API timeout errors as API', () => {
      const error = {
        message: 'Request timeout',
        code: '408',
        type: 'TimeoutError'
      };

      const result = categorizer.categorize(error);

      expect(result.category).toBe('API');
      expect(result.subcategory).toBe('TIMEOUT');
      expect(result.confidence).toBeGreaterThan(0.5);
    });

    test('should categorize trading errors as TRADING', () => {
      const error = {
        message: 'Order execution failed',
        stack: 'TradingError: Insufficient liquidity',
        type: 'TradingError'
      };

      const result = categorizer.categorize(error);

      expect(result.category).toBe('TRADING');
      expect(result.subcategory).toBe('ORDER');
      expect(result.severity).toBe('CRITICAL');
    });

    test('should categorize AI/ML errors as AI_ML', () => {
      const error = {
        message: 'Model prediction failed',
        stack: 'ModelError: Invalid input tensor shape',
        type: 'MLError'
      };

      const result = categorizer.categorize(error);

      expect(result.category).toBe('AI_ML');
      expect(result.subcategory).toBe('PREDICTION');
      expect(result.severity).toBe('HIGH');
    });

    test('should categorize user input errors as USER', () => {
      const error = {
        message: 'Invalid user input: email format',
        code: '400',
        type: 'ValidationError'
      };

      const result = categorizer.categorize(error);

      expect(result.category).toBe('USER');
      expect(result.severity).toBe('LOW');
    });

    test('should handle unknown errors gracefully', () => {
      const error = {
        message: 'Something completely unknown happened'
      };

      const result = categorizer.categorize(error);

      expect(result.category).toBeDefined();
      expect(result.severity).toBeDefined();
      expect(result.confidence).toBeLessThan(1.0);
    });

    test('should assign higher severity for critical keywords', () => {
      const error = {
        message: 'Fatal system crash - data corruption detected',
        type: 'CriticalError'
      };

      const result = categorizer.categorize(error);

      expect(result.severity).toBe('CRITICAL');
    });

    test('should extract and include relevant tags', () => {
      const error = {
        message: 'Database connection timeout error',
        stack: 'Error at pg.connect()',
        code: 'ETIMEDOUT'
      };

      const result = categorizer.categorize(error);

      expect(result.tags).toContain('has-stack');
      expect(result.tags).toContain('has-code');
      expect(result.tags.some(tag => tag.startsWith('keyword:'))).toBe(true);
    });

    test('should calculate confidence based on keyword matches', () => {
      const specificError = {
        message: 'PostgreSQL database connection failed',
        stack: 'Error: ECONNREFUSED at Database.connect()',
        code: 'ECONNREFUSED'
      };

      const vagueError = {
        message: 'Something went wrong'
      };

      const specificResult = categorizer.categorize(specificError);
      const vagueResult = categorizer.categorize(vagueError);

      expect(specificResult.confidence).toBeGreaterThan(vagueResult.confidence);
    });
  });

  describe('severity determination', () => {
    test('should assign CRITICAL for system-breaking errors', () => {
      const criticalErrors = [
        { message: 'System crash detected' },
        { message: 'Data corruption in database' },
        { message: 'Security breach alert' }
      ];

      criticalErrors.forEach(error => {
        const result = categorizer.categorize(error);
        expect(result.severity).toBe('CRITICAL');
      });
    });

    test('should map HTTP status codes to appropriate severity', () => {
      const statusTests = [
        { code: '500', expectedSeverity: 'HIGH' },
        { code: '404', expectedSeverity: 'MEDIUM' },
        { code: '400', expectedSeverity: 'MEDIUM' },
        { code: '401', expectedSeverity: 'MEDIUM' }
      ];

      statusTests.forEach(({ code, expectedSeverity }) => {
        const error = { message: 'HTTP error', code };
        const result = categorizer.categorize(error);
        expect(result.severity).toBe(expectedSeverity);
      });
    });
  });

  describe('subcategory determination', () => {
    test('should correctly identify database subcategory', () => {
      const dbErrors = [
        { message: 'SQL query failed', expected: 'DATABASE' },
        { message: 'PostgreSQL connection error', expected: 'DATABASE' },
        { message: 'Database timeout', expected: 'DATABASE' }
      ];

      dbErrors.forEach(({ message, expected }) => {
        const error = { message };
        const result = categorizer.categorize(error);
        if (result.category === 'SYSTEM') {
          expect(result.subcategory).toBe(expected);
        }
      });
    });

    test('should correctly identify network subcategory', () => {
      const networkErrors = [
        { message: 'Network connection failed', expected: 'NETWORK' },
        { message: 'Connection refused', expected: 'NETWORK' },
        { message: 'Network timeout', expected: 'NETWORK' }
      ];

      networkErrors.forEach(({ message, expected }) => {
        const error = { message };
        const result = categorizer.categorize(error);
        if (result.category === 'SYSTEM') {
          expect(result.subcategory).toBe(expected);
        }
      });
    });
  });

  describe('metadata generation', () => {
    test('should include proper metadata', () => {
      const error = {
        message: 'Test error',
        type: 'TestError'
      };

      const result = categorizer.categorize(error);

      expect(result.metadata).toBeDefined();
      expect(result.metadata.timestamp).toBeDefined();
      expect(result.metadata.analyzed).toBe(true);
      expect(result.metadata.errorType).toBeDefined();
      expect(result.metadata.source).toBeDefined();
    });

    test('should identify error source from stack trace', () => {
      const error = {
        message: 'Error in dependency',
        stack: 'Error at /app/node_modules/some-package/index.js'
      };

      const result = categorizer.categorize(error);

      expect(result.metadata.source).toBe('dependency');
    });
  });

  describe('edge cases', () => {
    test('should handle empty error object', () => {
      const result = categorizer.categorize({});

      expect(result.category).toBeDefined();
      expect(result.severity).toBeDefined();
      expect(result.confidence).toBeLessThan(0.5);
    });

    test('should handle null error', () => {
      const result = categorizer.categorize(null);

      expect(result.category).toBeDefined();
      expect(result.severity).toBeDefined();
    });

    test('should handle error with only message', () => {
      const error = { message: 'Simple error message' };
      const result = categorizer.categorize(error);

      expect(result.category).toBeDefined();
      expect(result.severity).toBeDefined();
      expect(result.tags).toBeDefined();
    });

    test('should handle very long error messages', () => {
      const longMessage = 'This is a very long error message that repeats itself. '.repeat(100);
      const error = { message: longMessage };
      const result = categorizer.categorize(error);

      expect(result.category).toBeDefined();
      expect(result.severity).toBeDefined();
      // Should limit keywords to prevent performance issues
      expect(result.tags.filter(tag => tag.startsWith('keyword:')).length).toBeLessThanOrEqual(5);
    });
  });

  describe('configuration methods', () => {
    test('should return categories configuration', () => {
      const categories = categorizer.getCategories();

      expect(categories).toBeDefined();
      expect(categories.SYSTEM).toBeDefined();
      expect(categories.API).toBeDefined();
      expect(categories.TRADING).toBeDefined();
    });

    test('should return severity levels configuration', () => {
      const severityLevels = categorizer.getSeverityLevels();

      expect(severityLevels).toBeDefined();
      expect(severityLevels.CRITICAL).toBeDefined();
      expect(severityLevels.HIGH).toBeDefined();
      expect(severityLevels.MEDIUM).toBeDefined();
      expect(severityLevels.LOW).toBeDefined();
    });
  });
});