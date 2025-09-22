/**
 * Anomaly
 * Data model for detected anomalies
 */

export class Anomaly {
  constructor({
    id = null,
    chainId,
    type,
    severity = 'medium',
    description,
    affectedMetric = null,
    currentValue = null,
    baselineValue = null,
    confidence = 0.5,
    timestamp = new Date(),
    detectionMethod = 'unknown',
    affectedServices = [],
    rawData = {}
  }) {
    this.id = id;
    this.chainId = chainId;
    this.type = type;
    this.severity = severity;
    this.description = description;
    this.affectedMetric = affectedMetric;
    this.currentValue = currentValue;
    this.baselineValue = baselineValue;
    this.confidence = confidence;
    this.timestamp = timestamp;
    this.detectionMethod = detectionMethod;
    this.affectedServices = affectedServices;
    this.rawData = rawData;

    // Calculated fields
    this.deviation = this.calculateDeviation();
    this.priority = this.calculatePriority();
    this.category = this.categorizeAnomaly();
  }

  calculateDeviation() {
    if (this.currentValue == null || this.baselineValue == null || this.baselineValue === 0) {
      return null;
    }

    return ((this.currentValue - this.baselineValue) / this.baselineValue) * 100;
  }

  calculatePriority() {
    const severityMap = {
      'critical': 4,
      'high': 3,
      'medium': 2,
      'low': 1
    };

    const basePriority = severityMap[this.severity] || 2;
    const confidenceBoost = this.confidence > 0.8 ? 1 : 0;
    const deviationBoost = Math.abs(this.deviation || 0) > 200 ? 1 : 0;

    return Math.min(4, basePriority + confidenceBoost + deviationBoost);
  }

  categorizeAnomaly() {
    if (this.type.includes('performance') || this.type.includes('duration')) {
      return 'performance';
    }
    if (this.type.includes('error') || this.type.includes('failure')) {
      return 'reliability';
    }
    if (this.type.includes('dependency') || this.type.includes('cascade')) {
      return 'dependency';
    }
    if (this.type.includes('resource') || this.type.includes('memory') || this.type.includes('cpu')) {
      return 'resource';
    }
    return 'other';
  }

  isRecent(timeWindow = 300000) { // 5 minutes default
    return Date.now() - this.timestamp.getTime() < timeWindow;
  }

  isCritical() {
    return this.severity === 'critical' || this.priority >= 4;
  }

  toJSON() {
    return {
      id: this.id,
      chainId: this.chainId,
      type: this.type,
      severity: this.severity,
      description: this.description,
      affectedMetric: this.affectedMetric,
      currentValue: this.currentValue,
      baselineValue: this.baselineValue,
      confidence: this.confidence,
      timestamp: this.timestamp,
      detectionMethod: this.detectionMethod,
      affectedServices: this.affectedServices,
      deviation: this.deviation,
      priority: this.priority,
      category: this.category,
      rawData: this.rawData
    };
  }

  static fromDatabase(row) {
    return new Anomaly({
      id: row.id,
      chainId: row.chain_id,
      type: row.type,
      severity: row.severity,
      description: row.description,
      affectedMetric: row.affected_metric,
      currentValue: row.current_value,
      baselineValue: row.baseline_value,
      confidence: row.confidence,
      timestamp: row.timestamp,
      detectionMethod: row.detection_method,
      affectedServices: row.affected_services || [],
      rawData: row.raw_data || {}
    });
  }
}