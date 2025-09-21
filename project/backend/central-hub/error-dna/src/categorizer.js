const fs = require('fs-extra');
const path = require('path');
const _ = require('lodash');

class ErrorCategorizer {
  constructor(configPath = null) {
    this.configPath = configPath || path.join(__dirname, '..', 'config', 'error-categories.json');
    this.categories = {};
    this.severityLevels = {};
    this.init();
  }

  async init() {
    try {
      const config = await fs.readJson(this.configPath);
      this.categories = config.categories;
      this.severityLevels = config.severity_levels;
      console.log('ErrorCategorizer initialized with', Object.keys(this.categories).length, 'categories');
    } catch (error) {
      console.error('Failed to initialize ErrorCategorizer:', error.message);
      throw error;
    }
  }

  /**
   * Categorize an error based on its properties
   * @param {Object} error - Error object containing message, stack, code, etc.
   * @returns {Object} - Categorization result
   */
  categorize(error) {
    try {
      const analysis = this._analyzeError(error);
      const category = this._determineCategory(analysis);
      const subcategory = this._determineSubcategory(category, analysis);
      const severity = this._determineSeverity(category, analysis);

      return {
        category: category?.id || 'UNKNOWN',
        categoryName: category?.name || 'Unknown',
        subcategory: subcategory || 'GENERAL',
        severity: severity || 'MEDIUM',
        confidence: this._calculateConfidence(category, analysis),
        tags: this._generateTags(analysis),
        metadata: {
          timestamp: new Date().toISOString(),
          analyzed: true,
          errorType: analysis.type,
          source: analysis.source
        }
      };
    } catch (categorizationError) {
      console.error('Error during categorization:', categorizationError);
      return this._getDefaultCategorization();
    }
  }

  /**
   * Analyze error properties to extract classification features
   * @param {Object} error - Error object
   * @returns {Object} - Analysis result
   */
  _analyzeError(error) {
    const message = error.message || error.description || '';
    const stack = error.stack || '';
    const code = error.code || error.statusCode || '';
    const type = error.type || error.name || '';

    return {
      message: message.toLowerCase(),
      stack: stack.toLowerCase(),
      code: String(code).toLowerCase(),
      type: type.toLowerCase(),
      source: this._identifySource(error),
      keywords: this._extractKeywords(message + ' ' + stack),
      hasStack: Boolean(stack),
      hasCode: Boolean(code),
      timestamp: error.timestamp || new Date().toISOString()
    };
  }

  /**
   * Determine the primary category for an error
   * @param {Object} analysis - Error analysis result
   * @returns {Object} - Category object
   */
  _determineCategory(analysis) {
    const { message, stack, code, keywords, source } = analysis;

    // System errors
    if (this._matchesPatterns(message + stack, [
      'database', 'connection', 'timeout', 'network', 'memory', 'cpu', 'disk',
      'econnrefused', 'etimedout', 'enotfound', 'enoent', 'emfile'
    ])) {
      return this.categories.SYSTEM;
    }

    // Trading errors
    if (this._matchesPatterns(message + stack, [
      'order', 'trade', 'market', 'price', 'position', 'risk', 'settlement',
      'execution', 'liquidity', 'spread', 'slippage'
    ])) {
      return this.categories.TRADING;
    }

    // AI/ML errors
    if (this._matchesPatterns(message + stack, [
      'model', 'prediction', 'training', 'inference', 'tensorflow', 'pytorch',
      'cuda', 'gpu', 'neural', 'algorithm', 'feature'
    ])) {
      return this.categories.AI_ML;
    }

    // API errors
    if (this._matchesPatterns(message + stack, [
      'api', 'http', 'request', 'response', 'authentication', 'authorization',
      'validation', 'rate limit', 'quota', 'forbidden', 'unauthorized'
    ]) || code.match(/^[45]\d{2}$/)) {
      return this.categories.API;
    }

    // User errors
    if (this._matchesPatterns(message + stack, [
      'user', 'input', 'validation', 'permission', 'access', 'session',
      'login', 'password', 'profile'
    ])) {
      return this.categories.USER;
    }

    // Default to system if uncertain
    return this.categories.SYSTEM;
  }

  /**
   * Determine subcategory within a category
   * @param {Object} category - Primary category
   * @param {Object} analysis - Error analysis
   * @returns {string} - Subcategory name
   */
  _determineSubcategory(category, analysis) {
    if (!category || !category.subcategories) return 'GENERAL';

    const { message, stack, code } = analysis;
    const text = message + ' ' + stack;

    // Check each subcategory for matches
    for (const [subcat, description] of Object.entries(category.subcategories)) {
      const subcatKeywords = description.toLowerCase().split(' ');
      if (this._matchesPatterns(text, subcatKeywords)) {
        return subcat;
      }
    }

    // Category-specific subcategory logic
    switch (category.id) {
      case 'SYSTEM':
        if (text.includes('database') || text.includes('sql')) return 'DATABASE';
        if (text.includes('network') || text.includes('connection')) return 'NETWORK';
        if (text.includes('memory') || text.includes('heap')) return 'MEMORY';
        if (text.includes('cpu') || text.includes('processing')) return 'CPU';
        if (text.includes('disk') || text.includes('storage')) return 'DISK';
        break;

      case 'API':
        if (text.includes('auth') || code.includes('401')) return 'AUTHENTICATION';
        if (text.includes('validation') || code.includes('400')) return 'VALIDATION';
        if (text.includes('rate') || code.includes('429')) return 'RATE_LIMIT';
        if (text.includes('timeout') || code.includes('408')) return 'TIMEOUT';
        if (text.includes('external') || text.includes('third-party')) return 'EXTERNAL';
        break;

      case 'TRADING':
        if (text.includes('order')) return 'ORDER';
        if (text.includes('market') || text.includes('data')) return 'MARKET_DATA';
        if (text.includes('risk')) return 'RISK';
        if (text.includes('settlement')) return 'SETTLEMENT';
        if (text.includes('compliance')) return 'COMPLIANCE';
        break;
    }

    return 'GENERAL';
  }

  /**
   * Determine error severity
   * @param {Object} category - Error category
   * @param {Object} analysis - Error analysis
   * @returns {string} - Severity level
   */
  _determineSeverity(category, analysis) {
    if (!category) return 'MEDIUM';

    // Base severity from category
    let baseSeverity = category.severity;

    // Adjust based on specific conditions
    const { message, code, stack } = analysis;
    const text = message + ' ' + stack;

    // Critical indicators
    if (this._matchesPatterns(text, [
      'crash', 'fatal', 'critical', 'emergency', 'panic', 'system down',
      'data loss', 'corruption', 'security breach'
    ])) {
      return 'CRITICAL';
    }

    // High severity indicators
    if (this._matchesPatterns(text, [
      'error', 'exception', 'failure', 'broken', 'unavailable', 'unreachable'
    ])) {
      baseSeverity = 'HIGH';
    }

    // HTTP status code severity mapping
    if (code) {
      const statusCode = parseInt(code);
      if (statusCode >= 500) return 'HIGH';
      if (statusCode >= 400) return 'MEDIUM';
      if (statusCode >= 300) return 'LOW';
    }

    return baseSeverity;
  }

  /**
   * Calculate confidence score for categorization
   * @param {Object} category - Assigned category
   * @param {Object} analysis - Error analysis
   * @returns {number} - Confidence score (0-1)
   */
  _calculateConfidence(category, analysis) {
    if (!category) return 0.1;

    let confidence = 0.5; // Base confidence

    // Increase confidence based on keyword matches
    const { keywords } = analysis;
    const categoryKeywords = this._getCategoryKeywords(category);
    const matches = keywords.filter(keyword =>
      categoryKeywords.some(catKeyword => keyword.includes(catKeyword))
    );

    confidence += (matches.length / keywords.length) * 0.3;

    // Increase confidence for specific error codes
    if (analysis.hasCode) confidence += 0.1;
    if (analysis.hasStack) confidence += 0.1;

    return Math.min(confidence, 1.0);
  }

  /**
   * Generate tags for error classification
   * @param {Object} analysis - Error analysis
   * @returns {Array} - Array of tags
   */
  _generateTags(analysis) {
    const tags = [];
    const { keywords, source, hasStack, hasCode } = analysis;

    // Add source tag
    if (source) tags.push(`source:${source}`);

    // Add structural tags
    if (hasStack) tags.push('has-stack');
    if (hasCode) tags.push('has-code');

    // Add keyword-based tags
    keywords.slice(0, 5).forEach(keyword => {
      if (keyword.length > 3) tags.push(`keyword:${keyword}`);
    });

    return tags;
  }

  /**
   * Extract keywords from error text
   * @param {string} text - Error text
   * @returns {Array} - Array of keywords
   */
  _extractKeywords(text) {
    const stopWords = new Set(['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']);

    return text
      .toLowerCase()
      .replace(/[^\w\s]/g, ' ')
      .split(/\s+/)
      .filter(word => word.length > 2 && !stopWords.has(word))
      .slice(0, 20); // Limit to top 20 keywords
  }

  /**
   * Identify error source from stack trace or properties
   * @param {Object} error - Error object
   * @returns {string} - Error source
   */
  _identifySource(error) {
    const stack = error.stack || '';

    if (stack.includes('node_modules')) return 'dependency';
    if (stack.includes('database')) return 'database';
    if (stack.includes('api')) return 'api';
    if (stack.includes('trading')) return 'trading';
    if (stack.includes('ml') || stack.includes('model')) return 'ml';

    return 'application';
  }

  /**
   * Check if text matches any of the given patterns
   * @param {string} text - Text to search
   * @param {Array} patterns - Patterns to match
   * @returns {boolean} - True if any pattern matches
   */
  _matchesPatterns(text, patterns) {
    return patterns.some(pattern => text.includes(pattern.toLowerCase()));
  }

  /**
   * Get keywords associated with a category
   * @param {Object} category - Category object
   * @returns {Array} - Array of category keywords
   */
  _getCategoryKeywords(category) {
    const keywords = [category.name.toLowerCase()];

    if (category.subcategories) {
      Object.values(category.subcategories).forEach(desc => {
        keywords.push(...desc.toLowerCase().split(' '));
      });
    }

    return keywords;
  }

  /**
   * Get default categorization for unknown errors
   * @returns {Object} - Default categorization
   */
  _getDefaultCategorization() {
    return {
      category: 'UNKNOWN',
      categoryName: 'Unknown',
      subcategory: 'GENERAL',
      severity: 'MEDIUM',
      confidence: 0.1,
      tags: ['uncategorized'],
      metadata: {
        timestamp: new Date().toISOString(),
        analyzed: false,
        errorType: 'unknown',
        source: 'unknown'
      }
    };
  }

  /**
   * Get all available categories
   * @returns {Object} - Categories configuration
   */
  getCategories() {
    return this.categories;
  }

  /**
   * Get severity levels configuration
   * @returns {Object} - Severity levels configuration
   */
  getSeverityLevels() {
    return this.severityLevels;
  }
}

module.exports = ErrorCategorizer;