const PatternDetector = require('../src/pattern-detector');

describe('PatternDetector', () => {
  let detector;

  beforeEach(() => {
    detector = new PatternDetector({
      windowSize: 10,
      similarityThreshold: 0.8,
      minOccurrences: 3,
      maxPatterns: 100
    });
  });

  describe('initialization', () => {
    test('should initialize with default config', () => {
      const defaultDetector = new PatternDetector();
      expect(defaultDetector.config.windowSize).toBe(100);
      expect(defaultDetector.config.similarityThreshold).toBe(0.8);
      expect(defaultDetector.config.minOccurrences).toBe(3);
    });

    test('should initialize with custom config', () => {
      expect(detector.config.windowSize).toBe(10);
      expect(detector.config.similarityThreshold).toBe(0.8);
      expect(detector.config.minOccurrences).toBe(3);
    });

    test('should start with empty state', () => {
      expect(detector.errorHistory).toHaveLength(0);
      expect(detector.patterns.size).toBe(0);
      expect(detector.patternStats.size).toBe(0);
    });
  });

  describe('error similarity calculation', () => {
    test('should calculate high similarity for identical errors', () => {
      const error1 = {
        category: 'SYSTEM',
        subcategory: 'DATABASE',
        severity: 'HIGH',
        originalError: { message: 'Connection failed' },
        tags: ['database', 'connection']
      };

      const error2 = {
        category: 'SYSTEM',
        subcategory: 'DATABASE',
        severity: 'HIGH',
        originalError: { message: 'Connection failed' },
        tags: ['database', 'connection']
      };

      const similarity = detector._calculateSimilarity(error1, error2);
      expect(similarity).toBeGreaterThan(0.9);
    });

    test('should calculate low similarity for different errors', () => {
      const error1 = {
        category: 'SYSTEM',
        subcategory: 'DATABASE',
        severity: 'HIGH',
        originalError: { message: 'Database connection failed' },
        tags: ['database']
      };

      const error2 = {
        category: 'TRADING',
        subcategory: 'ORDER',
        severity: 'CRITICAL',
        originalError: { message: 'Order execution failed' },
        tags: ['trading']
      };

      const similarity = detector._calculateSimilarity(error1, error2);
      expect(similarity).toBeLessThan(0.3);
    });

    test('should handle empty or missing fields', () => {
      const error1 = { category: 'SYSTEM' };
      const error2 = { category: 'SYSTEM' };

      const similarity = detector._calculateSimilarity(error1, error2);
      expect(similarity).toBeGreaterThan(0);
      expect(similarity).toBeLessThan(1);
    });
  });

  describe('pattern detection', () => {
    test('should detect new pattern when enough similar errors occur', () => {
      const baseError = {
        category: 'SYSTEM',
        subcategory: 'DATABASE',
        severity: 'HIGH',
        originalError: { message: 'Database connection timeout' },
        tags: ['database', 'timeout']
      };

      // Add similar errors
      for (let i = 0; i < 4; i++) {
        const result = detector.addError({
          ...baseError,
          id: `error_${i}`,
          timestamp: new Date().toISOString()
        });

        if (i >= 2) { // After 3rd occurrence (minOccurrences = 3)
          expect(result.newPatterns.length).toBeGreaterThan(0);
        }
      }

      expect(detector.patterns.size).toBe(1);
    });

    test('should update existing pattern when similar error occurs', () => {
      const baseError = {
        category: 'API',
        subcategory: 'TIMEOUT',
        severity: 'MEDIUM',
        originalError: { message: 'API request timeout' },
        tags: ['api', 'timeout']
      };

      // Create initial pattern
      for (let i = 0; i < 3; i++) {
        detector.addError({
          ...baseError,
          id: `error_${i}`,
          timestamp: new Date().toISOString()
        });
      }

      const initialPatternCount = detector.patterns.size;

      // Add another similar error
      const result = detector.addError({
        ...baseError,
        id: 'error_new',
        timestamp: new Date().toISOString()
      });

      expect(detector.patterns.size).toBe(initialPatternCount);
      expect(result.existingPatterns.length).toBeGreaterThan(0);
    });

    test('should maintain window size limit', () => {
      const baseError = {
        category: 'USER',
        subcategory: 'INPUT',
        severity: 'LOW',
        originalError: { message: 'Invalid input' },
        tags: ['user', 'validation']
      };

      // Add more errors than window size
      for (let i = 0; i < 15; i++) {
        detector.addError({
          ...baseError,
          id: `error_${i}`,
          timestamp: new Date().toISOString()
        });
      }

      expect(detector.errorHistory.length).toBeLessThanOrEqual(detector.config.windowSize);
    });

    test('should respect max patterns limit', () => {
      // Create many different error types to exceed pattern limit
      for (let i = 0; i < 50; i++) {
        const errorType = {
          category: 'SYSTEM',
          subcategory: 'GENERAL',
          severity: 'MEDIUM',
          originalError: { message: `Unique error type ${i}` },
          tags: [`type${i}`]
        };

        // Add enough similar errors to create a pattern
        for (let j = 0; j < 3; j++) {
          detector.addError({
            ...errorType,
            id: `error_${i}_${j}`,
            timestamp: new Date().toISOString()
          });
        }
      }

      expect(detector.patterns.size).toBeLessThanOrEqual(detector.config.maxPatterns);
    });
  });

  describe('anomaly detection', () => {
    test('should detect unusual error combinations', () => {
      const unusualError = {
        category: 'USER',
        subcategory: 'INPUT',
        severity: 'CRITICAL', // Unusual: user errors are rarely critical
        originalError: { message: 'User input validation failed' },
        tags: ['user']
      };

      const result = detector.addError(unusualError);

      expect(result.anomalies.length).toBeGreaterThan(0);
      expect(result.anomalies[0].type).toBe('unusual_combination');
    });

    test('should detect error spikes', () => {
      const baseError = {
        category: 'API',
        subcategory: 'TIMEOUT',
        severity: 'MEDIUM',
        originalError: { message: 'API timeout' },
        tags: ['api']
      };

      // Fill history with same error type to simulate spike
      for (let i = 0; i < 8; i++) {
        const result = detector.addError({
          ...baseError,
          id: `error_${i}`,
          timestamp: new Date().toISOString()
        });

        if (i >= 4) { // After enough errors for spike detection
          expect(result.anomalies.some(a => a.type === 'error_spike')).toBe(true);
        }
      }
    });
  });

  describe('pattern generation', () => {
    test('should generate appropriate pattern signatures', () => {
      const error = {
        category: 'TRADING',
        subcategory: 'ORDER',
        severity: 'HIGH',
        originalError: { message: 'Order placement failed insufficient funds' }
      };

      const signature = detector._generatePatternSignature(error);

      expect(signature).toContain('TRADING');
      expect(signature).toContain('ORDER');
      expect(signature).toContain('HIGH');
    });

    test('should find common tags across similar errors', () => {
      const errors = [
        { tags: ['api', 'timeout', 'external'] },
        { tags: ['api', 'timeout', 'internal'] },
        { tags: ['api', 'timeout', 'external'] }
      ];

      const commonTags = detector._findCommonTags(errors);

      expect(commonTags).toContain('api');
      expect(commonTags).toContain('timeout');
      // 'external' appears in 2/3 errors, should be included (>= 50%)
      expect(commonTags).toContain('external');
    });

    test('should generate meaningful pattern descriptions', () => {
      const errors = [
        {
          category: 'SYSTEM',
          subcategory: 'DATABASE',
          severity: 'HIGH'
        }
      ];

      const description = detector._generatePatternDescription(errors);

      expect(description.toLowerCase()).toContain('high');
      expect(description.toLowerCase()).toContain('system');
      expect(description.toLowerCase()).toContain('database');
    });

    test('should calculate appropriate risk levels', () => {
      const criticalErrors = [
        { severity: 'CRITICAL' },
        { severity: 'CRITICAL' },
        { severity: 'HIGH' }
      ];

      const lowRiskErrors = [
        { severity: 'LOW' },
        { severity: 'LOW' }
      ];

      const highRisk = detector._calculateRiskLevel(criticalErrors);
      const lowRisk = detector._calculateRiskLevel(lowRiskErrors);

      expect(highRisk).toBe('HIGH');
      expect(lowRisk).toBe('LOW');
    });
  });

  describe('recommendations', () => {
    test('should generate pattern-based recommendations', () => {
      const error = {
        category: 'TRADING',
        subcategory: 'ORDER',
        severity: 'CRITICAL',
        originalError: { message: 'Order failed' }
      };

      const detectionResult = {
        newPatterns: [],
        existingPatterns: [{
          description: 'Frequent trading errors',
          occurrences: 5
        }],
        anomalies: []
      };

      const recommendations = detector._generateRecommendations(error, detectionResult);

      expect(recommendations.length).toBeGreaterThan(0);
      expect(recommendations.some(r => r.type === 'immediate_action')).toBe(true);
      expect(recommendations.some(r => r.type === 'trading_action')).toBe(true);
    });

    test('should recommend immediate action for critical errors', () => {
      const criticalError = {
        category: 'SYSTEM',
        severity: 'CRITICAL'
      };

      const recommendations = detector._generateRecommendations(criticalError, {
        newPatterns: [],
        existingPatterns: [],
        anomalies: []
      });

      const immediateAction = recommendations.find(r => r.type === 'immediate_action');
      expect(immediateAction).toBeDefined();
      expect(immediateAction.priority).toBe('high');
    });

    test('should recommend anomaly investigation', () => {
      const error = {
        category: 'API',
        severity: 'MEDIUM'
      };

      const detectionResult = {
        newPatterns: [],
        existingPatterns: [],
        anomalies: [{ type: 'unusual_combination' }]
      };

      const recommendations = detector._generateRecommendations(error, detectionResult);

      const anomalyAction = recommendations.find(r => r.type === 'anomaly_action');
      expect(anomalyAction).toBeDefined();
      expect(anomalyAction.priority).toBe('high');
    });
  });

  describe('utility methods', () => {
    test('should return all patterns', () => {
      // Create some patterns first
      const baseError = {
        category: 'SYSTEM',
        subcategory: 'DATABASE',
        severity: 'HIGH',
        originalError: { message: 'DB error' }
      };

      for (let i = 0; i < 3; i++) {
        detector.addError({
          ...baseError,
          id: `error_${i}`
        });
      }

      const patterns = detector.getPatterns();
      expect(Array.isArray(patterns)).toBe(true);
      expect(patterns.length).toBeGreaterThan(0);
    });

    test('should return pattern statistics', () => {
      const stats = detector.getPatternStats();
      expect(typeof stats).toBe('object');
    });

    test('should return error history', () => {
      const history = detector.getErrorHistory();
      expect(Array.isArray(history)).toBe(true);
    });

    test('should clear all data', () => {
      // Add some data first
      detector.addError({
        category: 'SYSTEM',
        id: 'test_error'
      });

      detector.clear();

      expect(detector.errorHistory).toHaveLength(0);
      expect(detector.patterns.size).toBe(0);
      expect(detector.patternStats.size).toBe(0);
    });
  });

  describe('message similarity', () => {
    test('should calculate message similarity correctly', () => {
      const message1 = 'Database connection timeout error occurred';
      const message2 = 'Database connection timeout error happened';

      const similarity = detector._calculateMessageSimilarity(message1, message2);
      expect(similarity).toBeGreaterThan(0.7); // High similarity due to common words
    });

    test('should handle empty messages', () => {
      const similarity1 = detector._calculateMessageSimilarity('', '');
      const similarity2 = detector._calculateMessageSimilarity('test', '');
      const similarity3 = detector._calculateMessageSimilarity('', 'test');

      expect(similarity1).toBe(1); // Both empty
      expect(similarity2).toBe(0); // One empty
      expect(similarity3).toBe(0); // One empty
    });

    test('should extract meaningful words', () => {
      const text = 'The database connection to the server failed with timeout error';
      const words = detector._extractWords(text);

      expect(words).toContain('database');
      expect(words).toContain('connection');
      expect(words).toContain('server');
      expect(words).toContain('failed');
      expect(words).toContain('timeout');
      expect(words).toContain('error');

      // Should not contain stop words
      expect(words).not.toContain('the');
      expect(words).not.toContain('to');
      expect(words).not.toContain('with');
    });
  });
});