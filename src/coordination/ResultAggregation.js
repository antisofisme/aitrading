/**
 * ResultAggregation - Aggregates and processes results from parallel agents
 * Implements conflict resolution and result merging strategies
 */

class ResultAggregation {
  constructor(memoryCoordination) {
    this.memoryCoordination = memoryCoordination;
    this.aggregationStrategies = new Map();
    this.conflictResolvers = new Map();
    this.resultCache = new Map();
    this.aggregationHistory = [];
    this.setupDefaultStrategies();
  }

  /**
   * Setup default aggregation strategies
   */
  setupDefaultStrategies() {
    // Merge strategy for combining results
    this.aggregationStrategies.set('merge', this.mergeStrategy.bind(this));

    // Voting strategy for consensus
    this.aggregationStrategies.set('vote', this.votingStrategy.bind(this));

    // Priority strategy based on agent capabilities
    this.aggregationStrategies.set('priority', this.priorityStrategy.bind(this));

    // Latest strategy using timestamps
    this.aggregationStrategies.set('latest', this.latestStrategy.bind(this));

    // Quality strategy based on result quality metrics
    this.aggregationStrategies.set('quality', this.qualityStrategy.bind(this));

    // Setup default conflict resolvers
    this.conflictResolvers.set('override', this.overrideResolver.bind(this));
    this.conflictResolvers.set('merge', this.mergeResolver.bind(this));
    this.conflictResolvers.set('vote', this.voteResolver.bind(this));
    this.conflictResolvers.set('escalate', this.escalateResolver.bind(this));
  }

  /**
   * Aggregate results from multiple agents with conflict resolution
   */
  async aggregateResults(results, options = {}) {
    const aggregationId = `agg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    const aggregation = {
      id: aggregationId,
      results,
      options,
      timestamp: Date.now(),
      strategy: options.strategy || 'merge',
      conflicts: [],
      resolution: null,
      metadata: {
        totalResults: results.length,
        agentIds: results.map(r => r.agentId),
        resultTypes: [...new Set(results.map(r => r.type || 'unknown'))]
      }
    };

    try {
      // Detect conflicts between results
      aggregation.conflicts = await this.detectConflicts(results);

      // Resolve conflicts if any
      if (aggregation.conflicts.length > 0) {
        await this.resolveConflicts(aggregation);
      }

      // Apply aggregation strategy
      aggregation.resolution = await this.applyAggregationStrategy(
        results,
        aggregation.strategy,
        options
      );

      // Store aggregation in memory
      await this.memoryCoordination.store(
        'coord/aggregations',
        aggregationId,
        aggregation,
        'system'
      );

      // Cache result for future use
      this.resultCache.set(aggregationId, aggregation.resolution);

      // Record in history
      this.aggregationHistory.push(aggregation);

      return aggregation.resolution;

    } catch (error) {
      aggregation.error = error.message;
      aggregation.status = 'failed';
      throw error;
    }
  }

  /**
   * Detect conflicts between agent results
   */
  async detectConflicts(results) {
    const conflicts = [];
    const resultsByKey = new Map();

    // Group results by key/identifier
    results.forEach(result => {
      const key = result.key || result.identifier || 'default';
      if (!resultsByKey.has(key)) {
        resultsByKey.set(key, []);
      }
      resultsByKey.get(key).push(result);
    });

    // Check for conflicts within each key group
    resultsByKey.forEach((groupResults, key) => {
      if (groupResults.length > 1) {
        const conflict = this.analyzeResultGroup(key, groupResults);
        if (conflict) {
          conflicts.push(conflict);
        }
      }
    });

    return conflicts;
  }

  /**
   * Analyze a group of results for conflicts
   */
  analyzeResultGroup(key, results) {
    const conflict = {
      key,
      type: 'unknown',
      results,
      severity: 'low',
      resolution: null
    };

    // Check for value conflicts
    const values = results.map(r => r.value || r.data || r.content);
    const uniqueValues = [...new Set(values.map(v => JSON.stringify(v)))];

    if (uniqueValues.length > 1) {
      conflict.type = 'value_conflict';
      conflict.severity = this.calculateConflictSeverity(results);
      return conflict;
    }

    // Check for timestamp conflicts
    const timestamps = results.map(r => r.timestamp).filter(Boolean);
    if (timestamps.length > 1) {
      const timeDiff = Math.max(...timestamps) - Math.min(...timestamps);
      if (timeDiff > 30000) { // 30 seconds
        conflict.type = 'temporal_conflict';
        conflict.severity = 'medium';
        return conflict;
      }
    }

    // Check for agent capability conflicts
    const capabilities = results.map(r => r.agentCapability || r.agentType).filter(Boolean);
    const uniqueCapabilities = [...new Set(capabilities)];
    if (uniqueCapabilities.length > 1) {
      conflict.type = 'capability_conflict';
      conflict.severity = 'low';
      return conflict;
    }

    return null;
  }

  /**
   * Calculate conflict severity based on result differences
   */
  calculateConflictSeverity(results) {
    const priorities = results.map(r => r.priority || 0);
    const confidences = results.map(r => r.confidence || 0.5);

    const priorityRange = Math.max(...priorities) - Math.min(...priorities);
    const confidenceRange = Math.max(...confidences) - Math.min(...confidences);

    if (priorityRange > 0.7 || confidenceRange > 0.6) {
      return 'high';
    } else if (priorityRange > 0.4 || confidenceRange > 0.3) {
      return 'medium';
    } else {
      return 'low';
    }
  }

  /**
   * Resolve conflicts in aggregation
   */
  async resolveConflicts(aggregation) {
    const resolverType = aggregation.options.conflictResolver || 'merge';
    const resolver = this.conflictResolvers.get(resolverType);

    if (!resolver) {
      throw new Error(`Unknown conflict resolver: ${resolverType}`);
    }

    for (const conflict of aggregation.conflicts) {
      try {
        conflict.resolution = await resolver(conflict, aggregation.options);
        conflict.resolvedAt = Date.now();
        conflict.status = 'resolved';
      } catch (error) {
        conflict.error = error.message;
        conflict.status = 'failed';
        console.error(`Failed to resolve conflict for key ${conflict.key}:`, error);
      }
    }
  }

  /**
   * Apply aggregation strategy to results
   */
  async applyAggregationStrategy(results, strategy, options) {
    const strategyFunction = this.aggregationStrategies.get(strategy);

    if (!strategyFunction) {
      throw new Error(`Unknown aggregation strategy: ${strategy}`);
    }

    return await strategyFunction(results, options);
  }

  /**
   * Merge strategy - Combines all results into a single structure
   */
  async mergeStrategy(results, options) {
    const merged = {
      type: 'merged',
      timestamp: Date.now(),
      sources: results.map(r => r.agentId),
      data: {},
      metadata: {
        totalSources: results.length,
        mergeStrategy: 'deep_merge'
      }
    };

    // Deep merge all result data
    results.forEach(result => {
      const data = result.data || result.value || result.content;
      if (data && typeof data === 'object') {
        merged.data = this.deepMerge(merged.data, data);
      } else if (data !== undefined) {
        // Handle primitive values
        const key = result.key || result.agentId;
        merged.data[key] = data;
      }
    });

    // Merge metadata
    merged.metadata.confidence = this.calculateAverageConfidence(results);
    merged.metadata.priority = this.calculateAveragePriority(results);

    return merged;
  }

  /**
   * Voting strategy - Uses consensus to determine final result
   */
  async votingStrategy(results, options) {
    const votes = new Map();
    const weightedVotes = new Map();

    // Count votes and apply weights
    results.forEach(result => {
      const value = JSON.stringify(result.data || result.value || result.content);
      const weight = result.confidence || 0.5;

      votes.set(value, (votes.get(value) || 0) + 1);
      weightedVotes.set(value, (weightedVotes.get(value) || 0) + weight);
    });

    // Find winning result
    let winner = null;
    let maxVotes = 0;
    let maxWeight = 0;

    if (options.useWeights) {
      // Use weighted voting
      weightedVotes.forEach((weight, value) => {
        if (weight > maxWeight) {
          maxWeight = weight;
          winner = value;
        }
      });
    } else {
      // Use simple majority
      votes.forEach((count, value) => {
        if (count > maxVotes) {
          maxVotes = count;
          winner = value;
        }
      });
    }

    const winningResult = results.find(r =>
      JSON.stringify(r.data || r.value || r.content) === winner
    );

    return {
      type: 'voted',
      timestamp: Date.now(),
      result: JSON.parse(winner),
      winner: winningResult,
      votes: Object.fromEntries(votes),
      metadata: {
        totalVotes: results.length,
        winningVotes: maxVotes,
        winningWeight: maxWeight,
        consensus: maxVotes / results.length
      }
    };
  }

  /**
   * Priority strategy - Selects result based on agent priority
   */
  async priorityStrategy(results, options) {
    const sortedResults = results.sort((a, b) => {
      const priorityA = a.priority || 0;
      const priorityB = b.priority || 0;

      if (priorityA !== priorityB) {
        return priorityB - priorityA; // Higher priority first
      }

      // Tie-breaker: use confidence
      const confidenceA = a.confidence || 0.5;
      const confidenceB = b.confidence || 0.5;
      return confidenceB - confidenceA;
    });

    const selected = sortedResults[0];

    return {
      type: 'priority_selected',
      timestamp: Date.now(),
      result: selected.data || selected.value || selected.content,
      selected: selected,
      metadata: {
        totalResults: results.length,
        selectedPriority: selected.priority || 0,
        selectedConfidence: selected.confidence || 0.5,
        alternativeResults: sortedResults.slice(1).length
      }
    };
  }

  /**
   * Latest strategy - Uses most recent result
   */
  async latestStrategy(results, options) {
    const sortedResults = results.sort((a, b) => {
      const timestampA = a.timestamp || 0;
      const timestampB = b.timestamp || 0;
      return timestampB - timestampA; // Most recent first
    });

    const latest = sortedResults[0];

    return {
      type: 'latest_selected',
      timestamp: Date.now(),
      result: latest.data || latest.value || latest.content,
      selected: latest,
      metadata: {
        totalResults: results.length,
        latestTimestamp: latest.timestamp,
        ageRange: (latest.timestamp || 0) - (sortedResults[sortedResults.length - 1].timestamp || 0)
      }
    };
  }

  /**
   * Quality strategy - Selects based on quality metrics
   */
  async qualityStrategy(results, options) {
    const scoredResults = results.map(result => {
      const quality = this.calculateQualityScore(result, options);
      return { ...result, qualityScore: quality };
    });

    const bestResult = scoredResults.reduce((best, current) =>
      current.qualityScore > best.qualityScore ? current : best
    );

    return {
      type: 'quality_selected',
      timestamp: Date.now(),
      result: bestResult.data || bestResult.value || bestResult.content,
      selected: bestResult,
      metadata: {
        totalResults: results.length,
        qualityScore: bestResult.qualityScore,
        qualityMetrics: this.getQualityMetrics(bestResult),
        alternativeScores: scoredResults.map(r => r.qualityScore)
      }
    };
  }

  /**
   * Calculate quality score for a result
   */
  calculateQualityScore(result, options) {
    let score = 0;

    // Confidence factor
    score += (result.confidence || 0.5) * 0.3;

    // Completeness factor
    const data = result.data || result.value || result.content;
    if (data && typeof data === 'object') {
      const completeness = Object.keys(data).length / (options.expectedFields || 10);
      score += Math.min(completeness, 1) * 0.2;
    } else if (data !== undefined) {
      score += 0.2; // Some data is better than no data
    }

    // Freshness factor
    const age = Date.now() - (result.timestamp || 0);
    const freshness = Math.max(0, 1 - (age / (options.maxAge || 300000))); // 5 minute default
    score += freshness * 0.2;

    // Agent capability factor
    const capability = result.agentCapability || 0.5;
    score += capability * 0.15;

    // Priority factor
    const priority = (result.priority || 0) / 10; // Normalize to 0-1
    score += priority * 0.15;

    return Math.min(score, 1); // Cap at 1.0
  }

  /**
   * Get quality metrics for a result
   */
  getQualityMetrics(result) {
    return {
      confidence: result.confidence || 0.5,
      priority: result.priority || 0,
      timestamp: result.timestamp || 0,
      agentCapability: result.agentCapability || 0.5,
      dataCompleteness: this.calculateDataCompleteness(result.data || result.value || result.content)
    };
  }

  /**
   * Calculate data completeness score
   */
  calculateDataCompleteness(data) {
    if (!data) return 0;
    if (typeof data !== 'object') return data !== undefined ? 1 : 0;

    const totalFields = Object.keys(data).length;
    const populatedFields = Object.values(data).filter(v => v !== null && v !== undefined).length;

    return totalFields > 0 ? populatedFields / totalFields : 0;
  }

  /**
   * Override conflict resolver - Uses highest priority result
   */
  async overrideResolver(conflict, options) {
    const highestPriority = conflict.results.reduce((best, current) =>
      (current.priority || 0) > (best.priority || 0) ? current : best
    );

    return {
      strategy: 'override',
      selected: highestPriority,
      reason: `Selected result with highest priority: ${highestPriority.priority || 0}`
    };
  }

  /**
   * Merge conflict resolver - Attempts to merge conflicting results
   */
  async mergeResolver(conflict, options) {
    const merged = {};

    conflict.results.forEach(result => {
      const data = result.data || result.value || result.content;
      if (data && typeof data === 'object') {
        Object.assign(merged, data);
      }
    });

    return {
      strategy: 'merge',
      result: merged,
      reason: 'Merged all conflicting results'
    };
  }

  /**
   * Vote conflict resolver - Uses voting mechanism
   */
  async voteResolver(conflict, options) {
    const votingResult = await this.votingStrategy(conflict.results, options);

    return {
      strategy: 'vote',
      result: votingResult.result,
      reason: `Selected by vote with ${votingResult.metadata.consensus * 100}% consensus`
    };
  }

  /**
   * Escalate conflict resolver - Escalates for manual resolution
   */
  async escalateResolver(conflict, options) {
    // Store conflict for manual resolution
    await this.memoryCoordination.store(
      'coord/escalated_conflicts',
      `conflict_${Date.now()}`,
      conflict,
      'system'
    );

    return {
      strategy: 'escalate',
      result: null,
      reason: 'Conflict escalated for manual resolution',
      escalated: true
    };
  }

  /**
   * Deep merge utility function
   */
  deepMerge(target, source) {
    const output = Object.assign({}, target);

    if (this.isObject(target) && this.isObject(source)) {
      Object.keys(source).forEach(key => {
        if (this.isObject(source[key])) {
          if (!(key in target)) {
            Object.assign(output, { [key]: source[key] });
          } else {
            output[key] = this.deepMerge(target[key], source[key]);
          }
        } else {
          Object.assign(output, { [key]: source[key] });
        }
      });
    }

    return output;
  }

  /**
   * Check if value is object
   */
  isObject(item) {
    return item && typeof item === 'object' && !Array.isArray(item);
  }

  /**
   * Calculate average confidence from results
   */
  calculateAverageConfidence(results) {
    const confidences = results.map(r => r.confidence || 0.5);
    return confidences.reduce((sum, conf) => sum + conf, 0) / confidences.length;
  }

  /**
   * Calculate average priority from results
   */
  calculateAveragePriority(results) {
    const priorities = results.map(r => r.priority || 0);
    return priorities.reduce((sum, pri) => sum + pri, 0) / priorities.length;
  }

  /**
   * Get aggregation statistics
   */
  getAggregationStatistics() {
    return {
      totalAggregations: this.aggregationHistory.length,
      strategiesUsed: this.getStrategyUsage(),
      conflictStats: this.getConflictStatistics(),
      cacheSize: this.resultCache.size,
      averageResultsPerAggregation: this.getAverageResultsPerAggregation()
    };
  }

  /**
   * Get strategy usage statistics
   */
  getStrategyUsage() {
    const usage = {};
    this.aggregationHistory.forEach(agg => {
      usage[agg.strategy] = (usage[agg.strategy] || 0) + 1;
    });
    return usage;
  }

  /**
   * Get conflict statistics
   */
  getConflictStatistics() {
    let totalConflicts = 0;
    let resolvedConflicts = 0;

    this.aggregationHistory.forEach(agg => {
      totalConflicts += agg.conflicts.length;
      resolvedConflicts += agg.conflicts.filter(c => c.status === 'resolved').length;
    });

    return {
      total: totalConflicts,
      resolved: resolvedConflicts,
      resolutionRate: totalConflicts > 0 ? (resolvedConflicts / totalConflicts) * 100 : 0
    };
  }

  /**
   * Get average results per aggregation
   */
  getAverageResultsPerAggregation() {
    if (this.aggregationHistory.length === 0) return 0;

    const totalResults = this.aggregationHistory.reduce(
      (sum, agg) => sum + agg.metadata.totalResults, 0
    );

    return totalResults / this.aggregationHistory.length;
  }

  /**
   * Cleanup aggregation system
   */
  cleanup() {
    this.resultCache.clear();
    this.aggregationHistory = [];
  }
}

module.exports = ResultAggregation;