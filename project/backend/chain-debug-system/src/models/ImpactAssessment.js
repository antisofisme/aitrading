/**
 * ImpactAssessment
 * Data model for impact assessment results
 */

export class ImpactAssessment {
  constructor({
    id = null,
    chainId,
    affectedServices = [],
    userImpact,
    businessImpact,
    cascadeRisk,
    priorityLevel = 'medium',
    estimatedRecoveryTime = 300,
    timestamp = new Date(),
    anomalies = [],
    metadata = {}
  }) {
    this.id = id;
    this.chainId = chainId;
    this.affectedServices = affectedServices;
    this.userImpact = userImpact;
    this.businessImpact = businessImpact;
    this.cascadeRisk = cascadeRisk;
    this.priorityLevel = priorityLevel;
    this.estimatedRecoveryTime = estimatedRecoveryTime;
    this.timestamp = timestamp;
    this.anomalies = anomalies;
    this.metadata = metadata;

    // Calculated fields
    this.impactScore = this.calculateImpactScore();
    this.urgency = this.calculateUrgency();
    this.riskLevel = this.calculateRiskLevel();
  }

  calculateImpactScore() {
    let score = 0;

    // User impact weight (30%)
    if (this.userImpact) {
      const userScore = Math.min(1, (this.userImpact.totalAffectedUsers || 0) / 10000);
      score += userScore * 0.3;
    }

    // Business impact weight (40%)
    if (this.businessImpact) {
      const businessScore = Math.min(1, (this.businessImpact.estimatedLoss || 0) / 100000);
      score += businessScore * 0.4;
    }

    // Cascade risk weight (30%)
    if (this.cascadeRisk) {
      score += (this.cascadeRisk.riskScore || 0) * 0.3;
    }

    return Math.min(1, score);
  }

  calculateUrgency() {
    const priorityMap = {
      'critical': 4,
      'high': 3,
      'medium': 2,
      'low': 1
    };

    const basePriority = priorityMap[this.priorityLevel] || 2;
    const cascadeBoost = this.cascadeRisk?.riskScore > 0.8 ? 1 : 0;
    const userImpactBoost = (this.userImpact?.totalAffectedUsers || 0) > 5000 ? 1 : 0;

    return Math.min(4, basePriority + cascadeBoost + userImpactBoost);
  }

  calculateRiskLevel() {
    if (this.impactScore > 0.8 || this.urgency >= 4) return 'critical';
    if (this.impactScore > 0.6 || this.urgency >= 3) return 'high';
    if (this.impactScore > 0.3 || this.urgency >= 2) return 'medium';
    return 'low';
  }

  isHighPriority() {
    return this.priorityLevel === 'critical' || this.priorityLevel === 'high';
  }

  requiresImmediateAction() {
    return this.priorityLevel === 'critical' && this.cascadeRisk?.riskScore > 0.7;
  }

  getAffectedUserCount() {
    return this.userImpact?.totalAffectedUsers || 0;
  }

  getEstimatedLoss() {
    return this.businessImpact?.estimatedLoss || 0;
  }

  toJSON() {
    return {
      id: this.id,
      chainId: this.chainId,
      affectedServices: this.affectedServices,
      userImpact: this.userImpact,
      businessImpact: this.businessImpact,
      cascadeRisk: this.cascadeRisk,
      priorityLevel: this.priorityLevel,
      estimatedRecoveryTime: this.estimatedRecoveryTime,
      timestamp: this.timestamp,
      impactScore: this.impactScore,
      urgency: this.urgency,
      riskLevel: this.riskLevel,
      anomalyCount: this.anomalies.length,
      metadata: this.metadata
    };
  }

  static fromDatabase(row) {
    return new ImpactAssessment({
      id: row.id,
      chainId: row.chain_id,
      affectedServices: row.affected_services || [],
      userImpact: row.user_impact || {},
      businessImpact: row.business_impact || {},
      cascadeRisk: row.cascade_risk || {},
      priorityLevel: row.priority_level,
      estimatedRecoveryTime: row.estimated_recovery_time,
      timestamp: row.timestamp,
      anomalies: row.anomalies || [],
      metadata: row.raw_data || {}
    });
  }
}