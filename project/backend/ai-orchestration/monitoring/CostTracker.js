/**
 * CostTracker - Cost tracking and budget management for AI providers
 */

class CostTracker {
    constructor(options = {}) {
        this.costs = new Map(); // provider -> cost data
        this.tenantCosts = new Map(); // tenant -> cost data
        this.budgets = new Map(); // tenant -> budget limits
        this.alertThresholds = options.alertThresholds || {
            warning: 0.8, // 80%
            critical: 0.95 // 95%
        };
        this.costHistory = new Map(); // Historical cost data
        this.maxHistoryDays = options.maxHistoryDays || 30;
    }

    /**
     * Record cost for a provider request
     */
    recordCost(provider, tenant, model, cost, tokens, requestType) {
        const timestamp = new Date().toISOString();
        const date = timestamp.split('T')[0];

        // Record provider-level cost
        this.addProviderCost(provider, cost, tokens, requestType, timestamp);

        // Record tenant-level cost
        this.addTenantCost(tenant, provider, model, cost, tokens, requestType, timestamp);

        // Record daily history
        this.addDailyHistory(date, tenant, provider, model, cost, tokens, requestType);

        // Check budget alerts
        this.checkBudgetAlerts(tenant);
    }

    /**
     * Add cost data for a provider
     */
    addProviderCost(provider, cost, tokens, requestType, timestamp) {
        if (!this.costs.has(provider)) {
            this.costs.set(provider, {
                totalCost: 0,
                totalTokens: 0,
                requestCounts: {},
                lastUpdate: timestamp,
                dailyCosts: new Map()
            });
        }

        const providerData = this.costs.get(provider);
        providerData.totalCost += cost;
        providerData.totalTokens += tokens;
        providerData.requestCounts[requestType] = (providerData.requestCounts[requestType] || 0) + 1;
        providerData.lastUpdate = timestamp;

        // Daily costs
        const date = timestamp.split('T')[0];
        if (!providerData.dailyCosts.has(date)) {
            providerData.dailyCosts.set(date, { cost: 0, tokens: 0, requests: 0 });
        }
        const dailyData = providerData.dailyCosts.get(date);
        dailyData.cost += cost;
        dailyData.tokens += tokens;
        dailyData.requests += 1;
    }

    /**
     * Add cost data for a tenant
     */
    addTenantCost(tenant, provider, model, cost, tokens, requestType, timestamp) {
        if (!this.tenantCosts.has(tenant)) {
            this.tenantCosts.set(tenant, {
                totalCost: 0,
                totalTokens: 0,
                providers: new Map(),
                models: new Map(),
                requestTypes: new Map(),
                lastUpdate: timestamp,
                dailyCosts: new Map()
            });
        }

        const tenantData = this.tenantCosts.get(tenant);
        tenantData.totalCost += cost;
        tenantData.totalTokens += tokens;
        tenantData.lastUpdate = timestamp;

        // Provider breakdown
        if (!tenantData.providers.has(provider)) {
            tenantData.providers.set(provider, { cost: 0, tokens: 0, requests: 0 });
        }
        const providerData = tenantData.providers.get(provider);
        providerData.cost += cost;
        providerData.tokens += tokens;
        providerData.requests += 1;

        // Model breakdown
        if (!tenantData.models.has(model)) {
            tenantData.models.set(model, { cost: 0, tokens: 0, requests: 0 });
        }
        const modelData = tenantData.models.get(model);
        modelData.cost += cost;
        modelData.tokens += tokens;
        modelData.requests += 1;

        // Request type breakdown
        if (!tenantData.requestTypes.has(requestType)) {
            tenantData.requestTypes.set(requestType, { cost: 0, tokens: 0, requests: 0 });
        }
        const requestData = tenantData.requestTypes.get(requestType);
        requestData.cost += cost;
        requestData.tokens += tokens;
        requestData.requests += 1;

        // Daily costs
        const date = timestamp.split('T')[0];
        if (!tenantData.dailyCosts.has(date)) {
            tenantData.dailyCosts.set(date, { cost: 0, tokens: 0, requests: 0 });
        }
        const dailyData = tenantData.dailyCosts.get(date);
        dailyData.cost += cost;
        dailyData.tokens += tokens;
        dailyData.requests += 1;
    }

    /**
     * Add to daily history for analytics
     */
    addDailyHistory(date, tenant, provider, model, cost, tokens, requestType) {
        if (!this.costHistory.has(date)) {
            this.costHistory.set(date, {
                totalCost: 0,
                totalTokens: 0,
                totalRequests: 0,
                tenants: new Map(),
                providers: new Map(),
                models: new Map()
            });
        }

        const dayData = this.costHistory.get(date);
        dayData.totalCost += cost;
        dayData.totalTokens += tokens;
        dayData.totalRequests += 1;

        // Tenant breakdown
        if (!dayData.tenants.has(tenant)) {
            dayData.tenants.set(tenant, { cost: 0, tokens: 0, requests: 0 });
        }
        const tenantData = dayData.tenants.get(tenant);
        tenantData.cost += cost;
        tenantData.tokens += tokens;
        tenantData.requests += 1;

        // Provider breakdown
        if (!dayData.providers.has(provider)) {
            dayData.providers.set(provider, { cost: 0, tokens: 0, requests: 0 });
        }
        const providerData = dayData.providers.get(provider);
        providerData.cost += cost;
        providerData.tokens += tokens;
        providerData.requests += 1;

        // Model breakdown
        if (!dayData.models.has(model)) {
            dayData.models.set(model, { cost: 0, tokens: 0, requests: 0 });
        }
        const modelData = dayData.models.get(model);
        modelData.cost += cost;
        modelData.tokens += tokens;
        modelData.requests += 1;

        // Cleanup old history
        this.cleanupOldHistory();
    }

    /**
     * Set budget for a tenant
     */
    setBudget(tenant, budget) {
        this.budgets.set(tenant, {
            daily: budget.daily || null,
            monthly: budget.monthly || null,
            total: budget.total || null,
            alertEmails: budget.alertEmails || [],
            enforceHardLimit: budget.enforceHardLimit || false,
            lastAlertSent: null
        });
    }

    /**
     * Get budget for a tenant
     */
    getBudget(tenant) {
        return this.budgets.get(tenant) || null;
    }

    /**
     * Check budget alerts for a tenant
     */
    checkBudgetAlerts(tenant) {
        const budget = this.budgets.get(tenant);
        if (!budget) return;

        const tenantCosts = this.getTenantCosts(tenant);
        const alerts = [];

        // Check daily budget
        if (budget.daily) {
            const dailyCost = this.getDailyCost(tenant);
            const dailyUsage = dailyCost / budget.daily;

            if (dailyUsage >= this.alertThresholds.critical) {
                alerts.push({
                    type: 'daily',
                    level: 'critical',
                    usage: dailyUsage,
                    cost: dailyCost,
                    budget: budget.daily
                });
            } else if (dailyUsage >= this.alertThresholds.warning) {
                alerts.push({
                    type: 'daily',
                    level: 'warning',
                    usage: dailyUsage,
                    cost: dailyCost,
                    budget: budget.daily
                });
            }
        }

        // Check monthly budget
        if (budget.monthly) {
            const monthlyCost = this.getMonthlyCost(tenant);
            const monthlyUsage = monthlyCost / budget.monthly;

            if (monthlyUsage >= this.alertThresholds.critical) {
                alerts.push({
                    type: 'monthly',
                    level: 'critical',
                    usage: monthlyUsage,
                    cost: monthlyCost,
                    budget: budget.monthly
                });
            } else if (monthlyUsage >= this.alertThresholds.warning) {
                alerts.push({
                    type: 'monthly',
                    level: 'warning',
                    usage: monthlyUsage,
                    cost: monthlyCost,
                    budget: budget.monthly
                });
            }
        }

        // Check total budget
        if (budget.total) {
            const totalUsage = tenantCosts.totalCost / budget.total;

            if (totalUsage >= this.alertThresholds.critical) {
                alerts.push({
                    type: 'total',
                    level: 'critical',
                    usage: totalUsage,
                    cost: tenantCosts.totalCost,
                    budget: budget.total
                });
            } else if (totalUsage >= this.alertThresholds.warning) {
                alerts.push({
                    type: 'total',
                    level: 'warning',
                    usage: totalUsage,
                    cost: tenantCosts.totalCost,
                    budget: budget.total
                });
            }
        }

        if (alerts.length > 0) {
            this.triggerBudgetAlerts(tenant, alerts);
        }
    }

    /**
     * Trigger budget alerts
     */
    triggerBudgetAlerts(tenant, alerts) {
        console.warn(`Budget alerts for tenant ${tenant}:`, alerts);
        // Implementation would send emails, webhooks, etc.
    }

    /**
     * Get provider costs
     */
    getProviderCosts(provider) {
        return this.costs.get(provider) || {
            totalCost: 0,
            totalTokens: 0,
            requestCounts: {},
            lastUpdate: null,
            dailyCosts: new Map()
        };
    }

    /**
     * Get tenant costs
     */
    getTenantCosts(tenant) {
        const tenantData = this.tenantCosts.get(tenant);
        if (!tenantData) {
            return {
                totalCost: 0,
                totalTokens: 0,
                providers: {},
                models: {},
                requestTypes: {},
                lastUpdate: null
            };
        }

        return {
            totalCost: tenantData.totalCost,
            totalTokens: tenantData.totalTokens,
            providers: Object.fromEntries(tenantData.providers),
            models: Object.fromEntries(tenantData.models),
            requestTypes: Object.fromEntries(tenantData.requestTypes),
            lastUpdate: tenantData.lastUpdate
        };
    }

    /**
     * Get daily cost for a tenant
     */
    getDailyCost(tenant, date = null) {
        const targetDate = date || new Date().toISOString().split('T')[0];
        const tenantData = this.tenantCosts.get(tenant);

        if (!tenantData || !tenantData.dailyCosts.has(targetDate)) {
            return 0;
        }

        return tenantData.dailyCosts.get(targetDate).cost;
    }

    /**
     * Get monthly cost for a tenant
     */
    getMonthlyCost(tenant, month = null) {
        const targetMonth = month || new Date().toISOString().substring(0, 7); // YYYY-MM
        const tenantData = this.tenantCosts.get(tenant);

        if (!tenantData) return 0;

        let monthlyCost = 0;
        for (const [date, data] of tenantData.dailyCosts) {
            if (date.startsWith(targetMonth)) {
                monthlyCost += data.cost;
            }
        }

        return monthlyCost;
    }

    /**
     * Get cost analytics for a time period
     */
    getCostAnalytics(timeRange = '7d', tenant = null) {
        const now = new Date();
        const days = parseInt(timeRange);
        const startDate = new Date(now.getTime() - (days * 24 * 60 * 60 * 1000));

        const analytics = {
            timeRange,
            startDate: startDate.toISOString().split('T')[0],
            endDate: now.toISOString().split('T')[0],
            totalCost: 0,
            totalTokens: 0,
            totalRequests: 0,
            dailyBreakdown: [],
            topProviders: new Map(),
            topModels: new Map(),
            costTrends: []
        };

        // Iterate through the date range
        for (let d = new Date(startDate); d <= now; d.setDate(d.getDate() + 1)) {
            const date = d.toISOString().split('T')[0];
            const dayData = this.costHistory.get(date);

            if (dayData) {
                if (tenant) {
                    const tenantData = dayData.tenants.get(tenant);
                    if (tenantData) {
                        analytics.totalCost += tenantData.cost;
                        analytics.totalTokens += tenantData.tokens;
                        analytics.totalRequests += tenantData.requests;

                        analytics.dailyBreakdown.push({
                            date,
                            cost: tenantData.cost,
                            tokens: tenantData.tokens,
                            requests: tenantData.requests
                        });
                    }
                } else {
                    analytics.totalCost += dayData.totalCost;
                    analytics.totalTokens += dayData.totalTokens;
                    analytics.totalRequests += dayData.totalRequests;

                    analytics.dailyBreakdown.push({
                        date,
                        cost: dayData.totalCost,
                        tokens: dayData.totalTokens,
                        requests: dayData.totalRequests
                    });

                    // Aggregate provider and model data
                    for (const [provider, data] of dayData.providers) {
                        if (!analytics.topProviders.has(provider)) {
                            analytics.topProviders.set(provider, { cost: 0, tokens: 0, requests: 0 });
                        }
                        const providerData = analytics.topProviders.get(provider);
                        providerData.cost += data.cost;
                        providerData.tokens += data.tokens;
                        providerData.requests += data.requests;
                    }

                    for (const [model, data] of dayData.models) {
                        if (!analytics.topModels.has(model)) {
                            analytics.topModels.set(model, { cost: 0, tokens: 0, requests: 0 });
                        }
                        const modelData = analytics.topModels.get(model);
                        modelData.cost += data.cost;
                        modelData.tokens += data.tokens;
                        modelData.requests += data.requests;
                    }
                }
            } else {
                analytics.dailyBreakdown.push({
                    date,
                    cost: 0,
                    tokens: 0,
                    requests: 0
                });
            }
        }

        // Convert maps to sorted arrays
        analytics.topProviders = Array.from(analytics.topProviders.entries())
            .sort((a, b) => b[1].cost - a[1].cost)
            .slice(0, 10);

        analytics.topModels = Array.from(analytics.topModels.entries())
            .sort((a, b) => b[1].cost - a[1].cost)
            .slice(0, 10);

        return analytics;
    }

    /**
     * Get cost summary
     */
    getCostSummary() {
        const summary = {
            totalCost: 0,
            totalTokens: 0,
            providers: {},
            tenants: {},
            dailyAverage: 0,
            monthlyProjection: 0
        };

        // Provider summary
        for (const [provider, data] of this.costs) {
            summary.totalCost += data.totalCost;
            summary.totalTokens += data.totalTokens;
            summary.providers[provider] = {
                cost: data.totalCost,
                tokens: data.totalTokens,
                requests: Object.values(data.requestCounts).reduce((a, b) => a + b, 0)
            };
        }

        // Tenant summary
        for (const [tenant, data] of this.tenantCosts) {
            summary.tenants[tenant] = {
                cost: data.totalCost,
                tokens: data.totalTokens
            };
        }

        // Calculate averages and projections
        const today = new Date().toISOString().split('T')[0];
        const last7Days = [];
        for (let i = 0; i < 7; i++) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            const dateStr = date.toISOString().split('T')[0];
            const dayData = this.costHistory.get(dateStr);
            if (dayData) {
                last7Days.push(dayData.totalCost);
            }
        }

        summary.dailyAverage = last7Days.length > 0
            ? last7Days.reduce((a, b) => a + b, 0) / last7Days.length
            : 0;

        summary.monthlyProjection = summary.dailyAverage * 30;

        return summary;
    }

    /**
     * Cleanup old history data
     */
    cleanupOldHistory() {
        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - this.maxHistoryDays);
        const cutoffStr = cutoffDate.toISOString().split('T')[0];

        for (const date of this.costHistory.keys()) {
            if (date < cutoffStr) {
                this.costHistory.delete(date);
            }
        }
    }

    /**
     * Export cost data
     */
    exportData(format = 'json') {
        const data = {
            providers: Object.fromEntries(this.costs),
            tenants: Object.fromEntries(this.tenantCosts),
            budgets: Object.fromEntries(this.budgets),
            history: Object.fromEntries(this.costHistory),
            exportDate: new Date().toISOString()
        };

        if (format === 'json') {
            return JSON.stringify(data, null, 2);
        }

        // Could add CSV, Excel export here
        return data;
    }

    /**
     * Import cost data
     */
    importData(data) {
        if (data.providers) {
            this.costs = new Map(Object.entries(data.providers));
        }
        if (data.tenants) {
            this.tenantCosts = new Map(Object.entries(data.tenants));
        }
        if (data.budgets) {
            this.budgets = new Map(Object.entries(data.budgets));
        }
        if (data.history) {
            this.costHistory = new Map(Object.entries(data.history));
        }
    }
}

module.exports = CostTracker;