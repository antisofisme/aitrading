/**
 * Cost tracking and usage monitoring utilities
 */

import { AIOutput, UsageMetrics } from '../core/types.js';

export interface CostBreakdown {
  provider: string;
  model: string;
  inputTokens: number;
  outputTokens: number;
  inputCost: number;
  outputCost: number;
  totalCost: number;
  timestamp: Date;
  requestId?: string;
}

export interface BudgetAlert {
  id: string;
  threshold: number;
  currentSpend: number;
  percentage: number;
  triggered: Date;
  message: string;
}

export interface CostTrackerConfig {
  /** Monthly budget limit in USD */
  monthlyBudget?: number;
  /** Daily budget limit in USD */
  dailyBudget?: number;
  /** Alert thresholds as percentages (e.g., [50, 75, 90]) */
  alertThresholds?: number[];
  /** Enable detailed cost tracking */
  detailed?: boolean;
  /** Custom cost calculation hooks */
  customCostCalculator?: (provider: string, model: string, usage: any) => number;
}

export class CostTracker {
  private costs: CostBreakdown[] = [];
  private alerts: BudgetAlert[] = [];
  private config: CostTrackerConfig;

  constructor(config: CostTrackerConfig = {}) {
    this.config = {
      alertThresholds: [50, 75, 90, 95],
      detailed: true,
      ...config
    };
  }

  /**
   * Record a cost transaction
   */
  recordCost(
    provider: string,
    model: string,
    output: AIOutput,
    totalCost: number,
    requestId?: string
  ): CostBreakdown {
    const breakdown: CostBreakdown = {
      provider,
      model,
      inputTokens: output.usage?.promptTokens || 0,
      outputTokens: output.usage?.completionTokens || 0,
      inputCost: 0, // Will be calculated if detailed
      outputCost: 0, // Will be calculated if detailed
      totalCost,
      timestamp: new Date(),
      requestId
    };

    if (this.config.detailed) {
      // Try to break down input/output costs if possible
      const totalTokens = breakdown.inputTokens + breakdown.outputTokens;
      if (totalTokens > 0) {
        // Estimate based on typical input/output ratios
        const inputRatio = breakdown.inputTokens / totalTokens;
        breakdown.inputCost = totalCost * inputRatio;
        breakdown.outputCost = totalCost * (1 - inputRatio);
      }
    }

    this.costs.push(breakdown);
    this.checkBudgetAlerts();

    return breakdown;
  }

  /**
   * Get total costs for a time period
   */
  getTotalCosts(
    startDate?: Date,
    endDate?: Date,
    filters?: {
      provider?: string;
      model?: string;
    }
  ): number {
    const costs = this.getFilteredCosts(startDate, endDate, filters);
    return costs.reduce((total, cost) => total + cost.totalCost, 0);
  }

  /**
   * Get cost breakdown by provider
   */
  getCostsByProvider(startDate?: Date, endDate?: Date): Record<string, number> {
    const costs = this.getFilteredCosts(startDate, endDate);
    const breakdown: Record<string, number> = {};

    for (const cost of costs) {
      breakdown[cost.provider] = (breakdown[cost.provider] || 0) + cost.totalCost;
    }

    return breakdown;
  }

  /**
   * Get cost breakdown by model
   */
  getCostsByModel(startDate?: Date, endDate?: Date): Record<string, number> {
    const costs = this.getFilteredCosts(startDate, endDate);
    const breakdown: Record<string, number> = {};

    for (const cost of costs) {
      const key = `${cost.provider}/${cost.model}`;
      breakdown[key] = (breakdown[key] || 0) + cost.totalCost;
    }

    return breakdown;
  }

  /**
   * Get usage statistics
   */
  getUsageStats(startDate?: Date, endDate?: Date): {
    totalRequests: number;
    totalTokens: number;
    totalCost: number;
    averageCostPerRequest: number;
    averageCostPerToken: number;
    topProviders: Array<{ provider: string; cost: number; requests: number }>;
    topModels: Array<{ model: string; cost: number; requests: number }>;
  } {
    const costs = this.getFilteredCosts(startDate, endDate);

    const totalRequests = costs.length;
    const totalTokens = costs.reduce((sum, c) => sum + c.inputTokens + c.outputTokens, 0);
    const totalCost = costs.reduce((sum, c) => sum + c.totalCost, 0);

    // Calculate top providers
    const providerStats: Record<string, { cost: number; requests: number }> = {};
    for (const cost of costs) {
      if (!providerStats[cost.provider]) {
        providerStats[cost.provider] = { cost: 0, requests: 0 };
      }
      providerStats[cost.provider].cost += cost.totalCost;
      providerStats[cost.provider].requests++;
    }

    const topProviders = Object.entries(providerStats)
      .map(([provider, stats]) => ({ provider, ...stats }))
      .sort((a, b) => b.cost - a.cost);

    // Calculate top models
    const modelStats: Record<string, { cost: number; requests: number }> = {};
    for (const cost of costs) {
      const key = `${cost.provider}/${cost.model}`;
      if (!modelStats[key]) {
        modelStats[key] = { cost: 0, requests: 0 };
      }
      modelStats[key].cost += cost.totalCost;
      modelStats[key].requests++;
    }

    const topModels = Object.entries(modelStats)
      .map(([model, stats]) => ({ model, ...stats }))
      .sort((a, b) => b.cost - a.cost);

    return {
      totalRequests,
      totalTokens,
      totalCost,
      averageCostPerRequest: totalRequests > 0 ? totalCost / totalRequests : 0,
      averageCostPerToken: totalTokens > 0 ? totalCost / totalTokens : 0,
      topProviders,
      topModels
    };
  }

  /**
   * Get current budget status
   */
  getBudgetStatus(): {
    monthly: {
      budget: number;
      spent: number;
      remaining: number;
      percentage: number;
    };
    daily: {
      budget: number;
      spent: number;
      remaining: number;
      percentage: number;
    };
  } {
    const now = new Date();
    const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);
    const dayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());

    const monthlySpent = this.getTotalCosts(monthStart);
    const dailySpent = this.getTotalCosts(dayStart);

    return {
      monthly: {
        budget: this.config.monthlyBudget || 0,
        spent: monthlySpent,
        remaining: Math.max(0, (this.config.monthlyBudget || 0) - monthlySpent),
        percentage: this.config.monthlyBudget ? (monthlySpent / this.config.monthlyBudget) * 100 : 0
      },
      daily: {
        budget: this.config.dailyBudget || 0,
        spent: dailySpent,
        remaining: Math.max(0, (this.config.dailyBudget || 0) - dailySpent),
        percentage: this.config.dailyBudget ? (dailySpent / this.config.dailyBudget) * 100 : 0
      }
    };
  }

  /**
   * Get budget alerts
   */
  getBudgetAlerts(): BudgetAlert[] {
    return [...this.alerts].sort((a, b) => b.triggered.getTime() - a.triggered.getTime());
  }

  /**
   * Clear old cost records
   */
  clearOldRecords(daysToKeep: number = 90): number {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - daysToKeep);

    const initialLength = this.costs.length;
    this.costs = this.costs.filter(cost => cost.timestamp >= cutoffDate);

    return initialLength - this.costs.length;
  }

  /**
   * Export cost data
   */
  exportCosts(format: 'json' | 'csv' = 'json'): string {
    if (format === 'csv') {
      const headers = [
        'timestamp',
        'provider',
        'model',
        'inputTokens',
        'outputTokens',
        'inputCost',
        'outputCost',
        'totalCost',
        'requestId'
      ];

      const rows = this.costs.map(cost => [
        cost.timestamp.toISOString(),
        cost.provider,
        cost.model,
        cost.inputTokens.toString(),
        cost.outputTokens.toString(),
        cost.inputCost.toFixed(6),
        cost.outputCost.toFixed(6),
        cost.totalCost.toFixed(6),
        cost.requestId || ''
      ]);

      return [headers.join(','), ...rows.map(row => row.join(','))].join('\n');
    }

    return JSON.stringify(this.costs, null, 2);
  }

  /**
   * Import cost data
   */
  importCosts(data: string, format: 'json' | 'csv' = 'json'): number {
    try {
      if (format === 'json') {
        const imported = JSON.parse(data) as CostBreakdown[];
        this.costs.push(...imported.map(cost => ({
          ...cost,
          timestamp: new Date(cost.timestamp)
        })));
        return imported.length;
      } else {
        // CSV import implementation
        const lines = data.split('\n');
        const headers = lines[0].split(',');
        let imported = 0;

        for (let i = 1; i < lines.length; i++) {
          if (!lines[i].trim()) continue;

          const values = lines[i].split(',');
          const cost: CostBreakdown = {
            timestamp: new Date(values[0]),
            provider: values[1],
            model: values[2],
            inputTokens: parseInt(values[3]),
            outputTokens: parseInt(values[4]),
            inputCost: parseFloat(values[5]),
            outputCost: parseFloat(values[6]),
            totalCost: parseFloat(values[7]),
            requestId: values[8] || undefined
          };

          this.costs.push(cost);
          imported++;
        }

        return imported;
      }
    } catch (error) {
      throw new Error(`Failed to import cost data: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Get filtered costs
   */
  private getFilteredCosts(
    startDate?: Date,
    endDate?: Date,
    filters?: {
      provider?: string;
      model?: string;
    }
  ): CostBreakdown[] {
    return this.costs.filter(cost => {
      if (startDate && cost.timestamp < startDate) return false;
      if (endDate && cost.timestamp > endDate) return false;
      if (filters?.provider && cost.provider !== filters.provider) return false;
      if (filters?.model && cost.model !== filters.model) return false;
      return true;
    });
  }

  /**
   * Check budget alerts
   */
  private checkBudgetAlerts(): void {
    const status = this.getBudgetStatus();
    const thresholds = this.config.alertThresholds || [];

    // Check monthly budget
    if (this.config.monthlyBudget && status.monthly.percentage > 0) {
      for (const threshold of thresholds) {
        if (status.monthly.percentage >= threshold) {
          const existingAlert = this.alerts.find(
            a => a.threshold === threshold &&
                 a.triggered.getMonth() === new Date().getMonth()
          );

          if (!existingAlert) {
            this.alerts.push({
              id: `monthly-${threshold}-${Date.now()}`,
              threshold,
              currentSpend: status.monthly.spent,
              percentage: status.monthly.percentage,
              triggered: new Date(),
              message: `Monthly budget ${threshold}% threshold reached ($${status.monthly.spent.toFixed(2)} of $${this.config.monthlyBudget.toFixed(2)})`
            });
          }
        }
      }
    }

    // Check daily budget
    if (this.config.dailyBudget && status.daily.percentage > 0) {
      for (const threshold of thresholds) {
        if (status.daily.percentage >= threshold) {
          const today = new Date().toDateString();
          const existingAlert = this.alerts.find(
            a => a.threshold === threshold &&
                 a.triggered.toDateString() === today
          );

          if (!existingAlert) {
            this.alerts.push({
              id: `daily-${threshold}-${Date.now()}`,
              threshold,
              currentSpend: status.daily.spent,
              percentage: status.daily.percentage,
              triggered: new Date(),
              message: `Daily budget ${threshold}% threshold reached ($${status.daily.spent.toFixed(2)} of $${this.config.dailyBudget.toFixed(2)})`
            });
          }
        }
      }
    }

    // Keep only recent alerts (last 30 days)
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - 30);
    this.alerts = this.alerts.filter(alert => alert.triggered >= cutoffDate);
  }
}