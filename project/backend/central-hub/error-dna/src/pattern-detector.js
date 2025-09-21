const _ = require('lodash');

class PatternDetector {
  constructor(config = {}) {
    this.config = {
      windowSize: config.windowSize || 100,
      similarityThreshold: config.similarityThreshold || 0.8,
      minOccurrences: config.minOccurrences || 3,
      maxPatterns: config.maxPatterns || 1000,
      ...config
    };

    this.errorHistory = [];
    this.patterns = new Map();
    this.patternStats = new Map();
  }

  /**
   * Add error to history and detect patterns
   * @param {Object} categorizedError - Categorized error object
   * @returns {Object} - Pattern detection result
   */
  addError(categorizedError) {
    // Add to error history
    this.errorHistory.push({
      ...categorizedError,
      timestamp: new Date().toISOString(),
      id: this._generateErrorId(categorizedError)
    });

    // Maintain window size
    if (this.errorHistory.length > this.config.windowSize) {
      this.errorHistory = this.errorHistory.slice(-this.config.windowSize);
    }

    // Detect patterns
    const detectionResult = this._detectPatterns(categorizedError);

    return detectionResult;
  }

  /**
   * Detect patterns in recent error history
   * @param {Object} newError - Newly added error
   * @returns {Object} - Detection result
   */
  _detectPatterns(newError) {
    const result = {
      newPatterns: [],
      existingPatterns: [],
      anomalies: [],
      recommendations: []
    };

    try {
      // Find similar errors
      const similarErrors = this._findSimilarErrors(newError);

      if (similarErrors.length >= this.config.minOccurrences) {
        const pattern = this._createOrUpdatePattern(similarErrors);

        if (pattern.isNew) {
          result.newPatterns.push(pattern);
        } else {
          result.existingPatterns.push(pattern);
        }
      }

      // Check for anomalies
      const anomaly = this._detectAnomaly(newError);
      if (anomaly) {
        result.anomalies.push(anomaly);
      }

      // Generate recommendations
      result.recommendations = this._generateRecommendations(newError, result);

    } catch (error) {
      console.error('Error during pattern detection:', error);
    }

    return result;
  }

  /**
   * Find errors similar to the given error
   * @param {Object} targetError - Error to find similarities for
   * @returns {Array} - Array of similar errors
   */
  _findSimilarErrors(targetError) {
    return this.errorHistory.filter(error => {
      const similarity = this._calculateSimilarity(targetError, error);
      return similarity >= this.config.similarityThreshold;
    });
  }

  /**
   * Calculate similarity between two errors
   * @param {Object} error1 - First error
   * @param {Object} error2 - Second error
   * @returns {number} - Similarity score (0-1)
   */
  _calculateSimilarity(error1, error2) {
    let score = 0;
    let factors = 0;

    // Category similarity (high weight)
    if (error1.category === error2.category) {
      score += 0.4;
    }
    factors += 0.4;

    // Subcategory similarity
    if (error1.subcategory === error2.subcategory) {
      score += 0.2;
    }
    factors += 0.2;

    // Severity similarity
    if (error1.severity === error2.severity) {
      score += 0.1;
    }
    factors += 0.1;

    // Message similarity (using keyword overlap)
    const messageSimilarity = this._calculateMessageSimilarity(
      error1.originalError?.message || '',
      error2.originalError?.message || ''
    );
    score += messageSimilarity * 0.2;
    factors += 0.2;

    // Tag similarity
    const tagSimilarity = this._calculateTagSimilarity(error1.tags || [], error2.tags || []);
    score += tagSimilarity * 0.1;
    factors += 0.1;

    return factors > 0 ? score / factors : 0;
  }

  /**
   * Calculate message similarity using keyword overlap
   * @param {string} message1 - First message
   * @param {string} message2 - Second message
   * @returns {number} - Similarity score (0-1)
   */
  _calculateMessageSimilarity(message1, message2) {
    if (!message1 || !message2) return 0;

    const words1 = this._extractWords(message1);
    const words2 = this._extractWords(message2);

    if (words1.length === 0 && words2.length === 0) return 1;
    if (words1.length === 0 || words2.length === 0) return 0;

    const intersection = _.intersection(words1, words2);
    const union = _.union(words1, words2);

    return intersection.length / union.length;
  }

  /**
   * Calculate tag similarity
   * @param {Array} tags1 - First set of tags
   * @param {Array} tags2 - Second set of tags
   * @returns {number} - Similarity score (0-1)
   */
  _calculateTagSimilarity(tags1, tags2) {
    if (tags1.length === 0 && tags2.length === 0) return 1;
    if (tags1.length === 0 || tags2.length === 0) return 0;

    const intersection = _.intersection(tags1, tags2);
    const union = _.union(tags1, tags2);

    return intersection.length / union.length;
  }

  /**
   * Extract meaningful words from text
   * @param {string} text - Input text
   * @returns {Array} - Array of words
   */
  _extractWords(text) {
    const stopWords = new Set(['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an']);

    return text
      .toLowerCase()
      .replace(/[^\w\s]/g, ' ')
      .split(/\s+/)
      .filter(word => word.length > 2 && !stopWords.has(word));
  }

  /**
   * Create or update a pattern
   * @param {Array} similarErrors - Array of similar errors
   * @returns {Object} - Pattern object
   */
  _createOrUpdatePattern(similarErrors) {
    const patternSignature = this._generatePatternSignature(similarErrors[0]);
    const existingPattern = this.patterns.get(patternSignature);

    if (existingPattern) {
      // Update existing pattern
      existingPattern.occurrences += 1;
      existingPattern.lastSeen = new Date().toISOString();
      existingPattern.examples = [
        ...existingPattern.examples.slice(0, 4), // Keep first 4 examples
        similarErrors[similarErrors.length - 1] // Add latest example
      ].slice(0, 5);

      // Update statistics
      this._updatePatternStats(existingPattern);

      return { ...existingPattern, isNew: false };
    } else {
      // Create new pattern
      const newPattern = {
        id: patternSignature,
        signature: patternSignature,
        category: similarErrors[0].category,
        subcategory: similarErrors[0].subcategory,
        severity: similarErrors[0].severity,
        occurrences: similarErrors.length,
        firstSeen: new Date().toISOString(),
        lastSeen: new Date().toISOString(),
        examples: similarErrors.slice(0, 5),
        commonTags: this._findCommonTags(similarErrors),
        description: this._generatePatternDescription(similarErrors),
        riskLevel: this._calculateRiskLevel(similarErrors),
        isNew: true
      };

      // Store pattern (with size limit)
      if (this.patterns.size >= this.config.maxPatterns) {
        this._pruneOldestPattern();
      }

      this.patterns.set(patternSignature, newPattern);
      this._initializePatternStats(newPattern);

      return newPattern;
    }
  }

  /**
   * Generate pattern signature for grouping similar errors
   * @param {Object} error - Error object
   * @returns {string} - Pattern signature
   */
  _generatePatternSignature(error) {
    const components = [
      error.category,
      error.subcategory,
      error.severity
    ];

    // Add message keywords for more specific grouping
    if (error.originalError?.message) {
      const keywords = this._extractWords(error.originalError.message)
        .slice(0, 3) // Top 3 keywords
        .sort()
        .join('-');
      if (keywords) components.push(keywords);
    }

    return components.join('::');
  }

  /**
   * Find common tags across similar errors
   * @param {Array} errors - Array of errors
   * @returns {Array} - Common tags
   */
  _findCommonTags(errors) {
    if (errors.length === 0) return [];

    const tagCounts = {};
    errors.forEach(error => {
      (error.tags || []).forEach(tag => {
        tagCounts[tag] = (tagCounts[tag] || 0) + 1;
      });
    });

    // Return tags that appear in at least 50% of errors
    const threshold = Math.ceil(errors.length * 0.5);
    return Object.entries(tagCounts)
      .filter(([tag, count]) => count >= threshold)
      .map(([tag]) => tag);
  }

  /**
   * Generate pattern description
   * @param {Array} errors - Array of similar errors
   * @returns {string} - Pattern description
   */
  _generatePatternDescription(errors) {
    const firstError = errors[0];
    const frequency = errors.length >= 5 ? 'Frequent' : 'Occasional';

    return `${frequency} ${firstError.severity.toLowerCase()} ${firstError.category.toLowerCase()} errors in ${firstError.subcategory.toLowerCase()}`;
  }

  /**
   * Calculate risk level for a pattern
   * @param {Array} errors - Array of similar errors
   * @returns {string} - Risk level
   */
  _calculateRiskLevel(errors) {
    const severityWeights = { CRITICAL: 4, HIGH: 3, MEDIUM: 2, LOW: 1 };
    const avgSeverity = errors.reduce((sum, error) =>
      sum + (severityWeights[error.severity] || 2), 0) / errors.length;

    const frequency = errors.length;

    if (avgSeverity >= 3.5 || frequency >= 10) return 'HIGH';
    if (avgSeverity >= 2.5 || frequency >= 5) return 'MEDIUM';
    return 'LOW';
  }

  /**
   * Detect anomalies in error patterns
   * @param {Object} error - Error to check for anomalies
   * @returns {Object|null} - Anomaly object or null
   */
  _detectAnomaly(error) {
    // Check for unusual combinations
    const unusualCombination = this._checkUnusualCombination(error);
    if (unusualCombination) {
      return {
        type: 'unusual_combination',
        description: 'Unusual error category/severity combination',
        error: error,
        details: unusualCombination
      };
    }

    // Check for sudden spikes
    const spike = this._checkErrorSpike(error);
    if (spike) {
      return {
        type: 'error_spike',
        description: 'Sudden increase in similar errors',
        error: error,
        details: spike
      };
    }

    return null;
  }

  /**
   * Check for unusual error combinations
   * @param {Object} error - Error to check
   * @returns {Object|null} - Unusual combination details or null
   */
  _checkUnusualCombination(error) {
    // Simple heuristics for unusual combinations
    if (error.category === 'USER' && error.severity === 'CRITICAL') {
      return { reason: 'User errors rarely critical' };
    }

    if (error.category === 'TRADING' && error.severity === 'LOW') {
      return { reason: 'Trading errors usually high severity' };
    }

    return null;
  }

  /**
   * Check for error spikes
   * @param {Object} error - Current error
   * @returns {Object|null} - Spike details or null
   */
  _checkErrorSpike(error) {
    const recentWindow = 10; // Last 10 errors
    const recentErrors = this.errorHistory.slice(-recentWindow);

    const similarRecentErrors = recentErrors.filter(e =>
      e.category === error.category && e.subcategory === error.subcategory
    );

    if (similarRecentErrors.length >= recentWindow * 0.5) {
      return {
        count: similarRecentErrors.length,
        window: recentWindow,
        percentage: (similarRecentErrors.length / recentWindow) * 100
      };
    }

    return null;
  }

  /**
   * Generate recommendations based on patterns and errors
   * @param {Object} error - Current error
   * @param {Object} detectionResult - Pattern detection result
   * @returns {Array} - Array of recommendations
   */
  _generateRecommendations(error, detectionResult) {
    const recommendations = [];

    // Pattern-based recommendations
    if (detectionResult.existingPatterns.length > 0) {
      recommendations.push({
        type: 'pattern_identified',
        priority: 'medium',
        action: 'investigate_pattern',
        description: `Pattern detected: ${detectionResult.existingPatterns[0].description}`,
        pattern: detectionResult.existingPatterns[0]
      });
    }

    // Severity-based recommendations
    if (error.severity === 'CRITICAL') {
      recommendations.push({
        type: 'immediate_action',
        priority: 'high',
        action: 'escalate_immediately',
        description: 'Critical error requires immediate attention'
      });
    }

    // Category-specific recommendations
    switch (error.category) {
      case 'TRADING':
        recommendations.push({
          type: 'trading_action',
          priority: 'high',
          action: 'check_positions',
          description: 'Verify all trading positions and risk exposure'
        });
        break;

      case 'SYSTEM':
        recommendations.push({
          type: 'system_action',
          priority: 'medium',
          action: 'monitor_resources',
          description: 'Monitor system resources and health metrics'
        });
        break;
    }

    // Anomaly-based recommendations
    if (detectionResult.anomalies.length > 0) {
      recommendations.push({
        type: 'anomaly_action',
        priority: 'high',
        action: 'investigate_anomaly',
        description: 'Unusual error pattern detected - investigate root cause'
      });
    }

    return recommendations;
  }

  /**
   * Generate unique error ID
   * @param {Object} error - Error object
   * @returns {string} - Unique error ID
   */
  _generateErrorId(error) {
    const timestamp = Date.now();
    const hash = require('crypto')
      .createHash('md5')
      .update(JSON.stringify(error))
      .digest('hex')
      .substring(0, 8);

    return `error_${timestamp}_${hash}`;
  }

  /**
   * Update pattern statistics
   * @param {Object} pattern - Pattern to update stats for
   */
  _updatePatternStats(pattern) {
    const stats = this.patternStats.get(pattern.id) || {
      totalOccurrences: 0,
      avgTimeBetween: 0,
      lastUpdated: new Date().toISOString()
    };

    stats.totalOccurrences = pattern.occurrences;
    stats.lastUpdated = new Date().toISOString();

    this.patternStats.set(pattern.id, stats);
  }

  /**
   * Initialize pattern statistics
   * @param {Object} pattern - New pattern
   */
  _initializePatternStats(pattern) {
    this.patternStats.set(pattern.id, {
      totalOccurrences: pattern.occurrences,
      avgTimeBetween: 0,
      created: new Date().toISOString(),
      lastUpdated: new Date().toISOString()
    });
  }

  /**
   * Prune oldest pattern to maintain size limit
   */
  _pruneOldestPattern() {
    let oldestPattern = null;
    let oldestTime = Date.now();

    for (const [id, pattern] of this.patterns) {
      const patternTime = new Date(pattern.firstSeen).getTime();
      if (patternTime < oldestTime) {
        oldestTime = patternTime;
        oldestPattern = id;
      }
    }

    if (oldestPattern) {
      this.patterns.delete(oldestPattern);
      this.patternStats.delete(oldestPattern);
    }
  }

  /**
   * Get all detected patterns
   * @returns {Array} - Array of patterns
   */
  getPatterns() {
    return Array.from(this.patterns.values());
  }

  /**
   * Get pattern statistics
   * @returns {Object} - Pattern statistics
   */
  getPatternStats() {
    return Object.fromEntries(this.patternStats);
  }

  /**
   * Get recent error history
   * @returns {Array} - Array of recent errors
   */
  getErrorHistory() {
    return this.errorHistory;
  }

  /**
   * Clear all patterns and history
   */
  clear() {
    this.errorHistory = [];
    this.patterns.clear();
    this.patternStats.clear();
  }
}

module.exports = PatternDetector;