/**
 * CascadeRisk
 * Data model for cascade risk assessment
 */

export class CascadeRisk {
  constructor({
    riskScore = 0,
    cascadePaths = [],
    mitigationStrategies = [],
    affectedServices = [],
    timestamp = new Date(),
    metadata = {}
  }) {
    this.riskScore = riskScore;
    this.cascadePaths = cascadePaths;
    this.mitigationStrategies = mitigationStrategies;
    this.affectedServices = affectedServices;
    this.timestamp = timestamp;
    this.metadata = metadata;

    // Calculated fields
    this.severity = this.calculateSeverity();
    this.cascadePathCount = cascadePaths.length;
    this.highRiskPaths = this.getHighRiskPaths();
    this.criticalServices = this.getCriticalServices();
  }

  calculateSeverity() {
    if (this.riskScore > 0.8) return 'critical';
    if (this.riskScore > 0.6) return 'high';
    if (this.riskScore > 0.3) return 'medium';
    return 'low';
  }

  getHighRiskPaths() {
    return this.cascadePaths.filter(path => path.probability > 0.7);
  }

  getCriticalServices() {
    const criticalServices = new Set();

    for (const path of this.cascadePaths) {
      if (path.probability > 0.7 || path.impactSeverity > 0.8) {
        criticalServices.add(path.sourceService);
        criticalServices.add(path.targetService);
      }
    }

    return Array.from(criticalServices);
  }

  hasHighRisk() {
    return this.riskScore > 0.7 || this.highRiskPaths.length > 0;
  }

  hasCriticalPath() {
    return this.cascadePaths.some(path =>
      path.probability > 0.8 && path.impactSeverity > 0.8
    );
  }

  getTopRiskPaths(limit = 5) {
    return this.cascadePaths
      .sort((a, b) => (b.probability * b.impactSeverity) - (a.probability * a.impactSeverity))
      .slice(0, limit);
  }

  getPrimaryMitigationStrategy() {
    return this.mitigationStrategies
      .sort((a, b) => {
        const priorityOrder = { critical: 3, high: 2, medium: 1, low: 0 };
        return priorityOrder[b.priority] - priorityOrder[a.priority];
      })[0] || null;
  }

  toJSON() {
    return {
      riskScore: this.riskScore,
      severity: this.severity,
      cascadePathCount: this.cascadePathCount,
      highRiskPathCount: this.highRiskPaths.length,
      criticalServices: this.criticalServices,
      cascadePaths: this.cascadePaths,
      mitigationStrategies: this.mitigationStrategies,
      affectedServices: this.affectedServices,
      timestamp: this.timestamp,
      metadata: this.metadata
    };
  }

  static fromDatabase(row) {
    return new CascadeRisk({
      riskScore: row.risk_score || 0,
      cascadePaths: row.cascade_paths || [],
      mitigationStrategies: row.mitigation_strategies || [],
      affectedServices: row.affected_services || [],
      timestamp: row.timestamp || new Date(),
      metadata: row.metadata || {}
    });
  }
}