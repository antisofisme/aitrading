/**
 * Stress Testing Framework for AI Trading Models
 * Implements regulatory stress testing requirements
 */

import { EventEmitter } from 'events';

export interface StressTestConfig {
  frequency: 'daily' | 'weekly' | 'monthly';
  scenarios: string[];
  confidenceThreshold: number;
  maxDrawdown: number;
  modelTimeout?: number; // milliseconds
  portfolioSize?: number;
  timeHorizon?: number; // days
}

export interface StressTestScenario {
  id: string;
  name: string;
  description: string;
  parameters: {
    marketShock?: number; // percentage
    volatilityMultiplier?: number;
    liquidityReduction?: number; // percentage
    correlationIncrease?: number; // percentage
    duration?: number; // days
  };
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'EXTREME';
}

export interface StressTestResult {
  testId: string;
  scenario: StressTestScenario;
  timestamp: string;
  duration: number; // milliseconds
  metrics: {
    maxDrawdown: number;
    volatility: number;
    sharpeRatio: number;
    valueAtRisk95: number;
    valueAtRisk99: number;
    expectedShortfall: number;
    profitLoss: number;
    successRate: number;
  };
  passed: boolean;
  failed: boolean;
  violations: string[];
  recommendations: string[];
}

export interface PortfolioPosition {
  symbol: string;
  quantity: number;
  price: number;
  value: number;
  weight: number;
}

export class StressTesting extends EventEmitter {
  private config: StressTestConfig;
  private scenarios: Map<string, StressTestScenario> = new Map();
  private testHistory: StressTestResult[] = [];
  private isRunning: boolean = false;

  constructor(config: StressTestConfig) {
    super();
    this.config = {
      modelTimeout: 30000, // 30 seconds default
      portfolioSize: 1000000, // $1M default
      timeHorizon: 252, // 1 year trading days
      ...config
    };

    this.initializeScenarios();
    this.schedulePeriodicTests();
  }

  private initializeScenarios(): void {
    const defaultScenarios: StressTestScenario[] = [
      {
        id: 'market_crash_2008',
        name: '2008 Financial Crisis',
        description: 'Simulate 2008-style market crash with high correlation and liquidity dry-up',
        parameters: {
          marketShock: -40,
          volatilityMultiplier: 3.5,
          liquidityReduction: 60,
          correlationIncrease: 80,
          duration: 30
        },
        severity: 'EXTREME'
      },
      {
        id: 'flash_crash_2010',
        name: '2010 Flash Crash',
        description: 'Rapid market decline with extreme volatility',
        parameters: {
          marketShock: -9,
          volatilityMultiplier: 10,
          liquidityReduction: 90,
          correlationIncrease: 95,
          duration: 1
        },
        severity: 'EXTREME'
      },
      {
        id: 'covid_crash_2020',
        name: 'COVID-19 Market Crash',
        description: 'Pandemic-induced market volatility and uncertainty',
        parameters: {
          marketShock: -34,
          volatilityMultiplier: 4,
          liquidityReduction: 40,
          correlationIncrease: 70,
          duration: 21
        },
        severity: 'HIGH'
      },
      {
        id: 'interest_rate_shock',
        name: 'Interest Rate Shock',
        description: 'Sudden central bank rate hike scenario',
        parameters: {
          marketShock: -15,
          volatilityMultiplier: 2,
          liquidityReduction: 20,
          correlationIncrease: 30,
          duration: 7
        },
        severity: 'MEDIUM'
      },
      {
        id: 'geopolitical_crisis',
        name: 'Geopolitical Crisis',
        description: 'Major geopolitical event affecting global markets',
        parameters: {
          marketShock: -25,
          volatilityMultiplier: 2.5,
          liquidityReduction: 35,
          correlationIncrease: 60,
          duration: 14
        },
        severity: 'HIGH'
      },
      {
        id: 'cyber_attack',
        name: 'Major Cyber Attack',
        description: 'Systemic cyber attack on financial infrastructure',
        parameters: {
          marketShock: -12,
          volatilityMultiplier: 3,
          liquidityReduction: 70,
          correlationIncrease: 50,
          duration: 3
        },
        severity: 'HIGH'
      }
    ];

    defaultScenarios.forEach(scenario => {
      this.scenarios.set(scenario.id, scenario);
    });

    // Add custom scenarios from config
    this.config.scenarios.forEach(scenarioId => {
      if (!this.scenarios.has(scenarioId)) {
        // Create basic scenario if not found
        this.scenarios.set(scenarioId, {
          id: scenarioId,
          name: scenarioId.replace(/_/g, ' ').toUpperCase(),
          description: `Custom stress test scenario: ${scenarioId}`,
          parameters: {
            marketShock: -20,
            volatilityMultiplier: 2,
            liquidityReduction: 30,
            correlationIncrease: 40,
            duration: 10
          },
          severity: 'MEDIUM'
        });
      }
    });
  }

  private schedulePeriodicTests(): void {
    const intervals = {
      daily: 24 * 60 * 60 * 1000,
      weekly: 7 * 24 * 60 * 60 * 1000,
      monthly: 30 * 24 * 60 * 60 * 1000
    };

    const interval = intervals[this.config.frequency];

    setInterval(async () => {
      if (!this.isRunning) {
        await this.executeScheduledTest();
      }
    }, interval);
  }

  private async executeScheduledTest(): Promise<void> {
    try {
      const scenarios = Array.from(this.scenarios.values());
      const randomScenario = scenarios[Math.floor(Math.random() * scenarios.length)];

      await this.executeTest(randomScenario.id);

      this.emit('stress_test:scheduled_completed', {
        scenario: randomScenario.id,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      this.emit('stress_test:error', {
        error: error.message,
        type: 'scheduled_test',
        timestamp: new Date().toISOString()
      });
    }
  }

  /**
   * Execute stress test for specific scenario or random if not specified
   */
  public async executeTest(scenarioId?: string): Promise<StressTestResult> {
    if (this.isRunning) {
      throw new Error('Stress test already running');
    }

    this.isRunning = true;
    const startTime = Date.now();

    try {
      // Select scenario
      const scenario = scenarioId
        ? this.scenarios.get(scenarioId)
        : Array.from(this.scenarios.values())[Math.floor(Math.random() * this.scenarios.size)];

      if (!scenario) {
        throw new Error(`Scenario not found: ${scenarioId}`);
      }

      this.emit('stress_test:started', {
        scenario: scenario.id,
        timestamp: new Date().toISOString()
      });

      // Generate synthetic portfolio for testing
      const portfolio = this.generateTestPortfolio();

      // Apply stress scenario
      const stressedPortfolio = this.applyStressScenario(portfolio, scenario);

      // Calculate risk metrics
      const metrics = this.calculateRiskMetrics(portfolio, stressedPortfolio, scenario);

      // Evaluate test results
      const { passed, violations, recommendations } = this.evaluateResults(metrics);

      const result: StressTestResult = {
        testId: `ST_${Date.now()}`,
        scenario,
        timestamp: new Date().toISOString(),
        duration: Date.now() - startTime,
        metrics,
        passed,
        failed: !passed,
        violations,
        recommendations
      };

      // Store result
      this.testHistory.push(result);

      // Emit completion event
      this.emit('stress_test:completed', result);

      return result;

    } finally {
      this.isRunning = false;
    }
  }

  private generateTestPortfolio(): PortfolioPosition[] {
    // Generate diversified test portfolio
    const symbols = ['SPY', 'QQQ', 'IWM', 'EFA', 'EEM', 'TLT', 'GLD', 'VIX', 'AAPL', 'MSFT', 'GOOGL', 'AMZN'];
    const portfolio: PortfolioPosition[] = [];
    const totalValue = this.config.portfolioSize || 1000000;

    symbols.forEach((symbol, index) => {
      const weight = Math.random() * 0.15 + 0.05; // 5-20% weight
      const price = 100 + Math.random() * 200; // Random price $100-300
      const value = totalValue * weight;
      const quantity = value / price;

      portfolio.push({
        symbol,
        quantity,
        price,
        value,
        weight
      });
    });

    return portfolio;
  }

  private applyStressScenario(
    portfolio: PortfolioPosition[],
    scenario: StressTestScenario
  ): PortfolioPosition[] {
    const { parameters } = scenario;

    return portfolio.map(position => {
      // Apply market shock
      let newPrice = position.price;
      if (parameters.marketShock) {
        newPrice *= (1 + parameters.marketShock / 100);
      }

      // Apply additional volatility (random component)
      if (parameters.volatilityMultiplier) {
        const volatility = 0.02 * parameters.volatilityMultiplier; // Base 2% daily vol
        const randomShock = (Math.random() - 0.5) * 2 * volatility;
        newPrice *= (1 + randomShock);
      }

      // Apply liquidity impact (bid-ask spread widening)
      if (parameters.liquidityReduction) {
        const liquidityImpact = parameters.liquidityReduction / 100 * 0.005; // Max 0.5% impact
        newPrice *= (1 - liquidityImpact);
      }

      const newValue = position.quantity * newPrice;

      return {
        ...position,
        price: newPrice,
        value: newValue
      };
    });
  }

  private calculateRiskMetrics(
    originalPortfolio: PortfolioPosition[],
    stressedPortfolio: PortfolioPosition[],
    scenario: StressTestScenario
  ): StressTestResult['metrics'] {
    const originalValue = originalPortfolio.reduce((sum, pos) => sum + pos.value, 0);
    const stressedValue = stressedPortfolio.reduce((sum, pos) => sum + pos.value, 0);

    const profitLoss = stressedValue - originalValue;
    const returnPct = (profitLoss / originalValue) * 100;

    // Calculate drawdown
    const maxDrawdown = Math.abs(Math.min(0, returnPct));

    // Simulate historical returns for additional metrics
    const returns = this.simulateReturns(stressedPortfolio, scenario);

    // Calculate Value at Risk (95% and 99% confidence)
    const sortedReturns = returns.sort((a, b) => a - b);
    const var95Index = Math.floor(returns.length * 0.05);
    const var99Index = Math.floor(returns.length * 0.01);

    const valueAtRisk95 = Math.abs(sortedReturns[var95Index] || 0) * originalValue / 100;
    const valueAtRisk99 = Math.abs(sortedReturns[var99Index] || 0) * originalValue / 100;

    // Expected Shortfall (average of worst 5% returns)
    const worstReturns = sortedReturns.slice(0, var95Index + 1);
    const expectedShortfall = Math.abs(worstReturns.reduce((sum, ret) => sum + ret, 0) / worstReturns.length) * originalValue / 100;

    // Calculate volatility
    const meanReturn = returns.reduce((sum, ret) => sum + ret, 0) / returns.length;
    const variance = returns.reduce((sum, ret) => sum + Math.pow(ret - meanReturn, 2), 0) / returns.length;
    const volatility = Math.sqrt(variance);

    // Calculate Sharpe ratio (assuming 2% risk-free rate)
    const riskFreeRate = 2;
    const sharpeRatio = (meanReturn - riskFreeRate) / volatility;

    // Success rate (percentage of positive returns)
    const positiveReturns = returns.filter(ret => ret > 0).length;
    const successRate = (positiveReturns / returns.length) * 100;

    return {
      maxDrawdown,
      volatility,
      sharpeRatio,
      valueAtRisk95,
      valueAtRisk99,
      expectedShortfall,
      profitLoss,
      successRate
    };
  }

  private simulateReturns(portfolio: PortfolioPosition[], scenario: StressTestScenario): number[] {
    const returns: number[] = [];
    const days = scenario.parameters.duration || 10;
    const baseVol = 0.02; // 2% daily volatility
    const vol = baseVol * (scenario.parameters.volatilityMultiplier || 1);

    for (let i = 0; i < days; i++) {
      // Generate correlated returns
      const marketReturn = (Math.random() - 0.5) * 2 * vol;
      const portfolioReturn = marketReturn + (Math.random() - 0.5) * vol * 0.5;
      returns.push(portfolioReturn * 100); // Convert to percentage
    }

    return returns;
  }

  private evaluateResults(metrics: StressTestResult['metrics']): {
    passed: boolean;
    violations: string[];
    recommendations: string[];
  } {
    const violations: string[] = [];
    const recommendations: string[] = [];

    // Check maximum drawdown
    if (metrics.maxDrawdown > this.config.maxDrawdown) {
      violations.push(`Maximum drawdown ${metrics.maxDrawdown.toFixed(2)}% exceeds limit ${this.config.maxDrawdown}%`);
      recommendations.push('Consider reducing position sizes or implementing stop-loss mechanisms');
    }

    // Check Value at Risk
    if (metrics.valueAtRisk99 > this.config.portfolioSize * 0.1) {
      violations.push(`99% VaR $${metrics.valueAtRisk99.toLocaleString()} exceeds 10% of portfolio value`);
      recommendations.push('Diversify portfolio further or reduce leverage');
    }

    // Check Sharpe ratio
    if (metrics.sharpeRatio < 0.5) {
      violations.push(`Sharpe ratio ${metrics.sharpeRatio.toFixed(2)} below acceptable threshold 0.5`);
      recommendations.push('Optimize risk-return profile or review trading strategy');
    }

    // Check success rate
    if (metrics.successRate < 40) {
      violations.push(`Success rate ${metrics.successRate.toFixed(1)}% below 40% threshold`);
      recommendations.push('Review entry/exit criteria and model parameters');
    }

    const passed = violations.length === 0;

    // Add general recommendations
    if (!passed) {
      recommendations.push('Consider implementing additional risk controls');
      recommendations.push('Review and update model parameters based on stress test results');
    }

    return { passed, violations, recommendations };
  }

  /**
   * Add custom stress test scenario
   */
  public addScenario(scenario: StressTestScenario): void {
    this.scenarios.set(scenario.id, scenario);
    this.emit('stress_test:scenario_added', {
      scenarioId: scenario.id,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Get available stress test scenarios
   */
  public getScenarios(): StressTestScenario[] {
    return Array.from(this.scenarios.values());
  }

  /**
   * Get stress test history
   */
  public getTestHistory(limit?: number): StressTestResult[] {
    const history = [...this.testHistory].reverse();
    return limit ? history.slice(0, limit) : history;
  }

  /**
   * Get stress testing status
   */
  public getStatus(): any {
    const recentTests = this.getTestHistory(10);
    const passedTests = recentTests.filter(test => test.passed).length;
    const successRate = recentTests.length > 0 ? (passedTests / recentTests.length) * 100 : 0;

    return {
      isRunning: this.isRunning,
      config: this.config,
      scenarios: this.scenarios.size,
      totalTests: this.testHistory.length,
      recentSuccessRate: successRate,
      lastTest: recentTests[0]?.timestamp || 'Never'
    };
  }

  /**
   * Generate compliance report for stress testing
   */
  public generateComplianceReport(startDate: Date, endDate: Date): any {
    const relevantTests = this.testHistory.filter(test => {
      const testDate = new Date(test.timestamp);
      return testDate >= startDate && testDate <= endDate;
    });

    const passedTests = relevantTests.filter(test => test.passed);
    const failedTests = relevantTests.filter(test => !test.passed);

    return {
      reportId: `STRESS_${Date.now()}`,
      period: {
        start: startDate.toISOString(),
        end: endDate.toISOString()
      },
      summary: {
        totalTests: relevantTests.length,
        passedTests: passedTests.length,
        failedTests: failedTests.length,
        successRate: relevantTests.length > 0 ? (passedTests.length / relevantTests.length) * 100 : 0
      },
      scenarios: this.getScenarios().map(scenario => ({
        id: scenario.id,
        name: scenario.name,
        severity: scenario.severity,
        testsRun: relevantTests.filter(test => test.scenario.id === scenario.id).length
      })),
      violations: failedTests.flatMap(test => test.violations),
      recommendations: [...new Set(failedTests.flatMap(test => test.recommendations))],
      generatedAt: new Date().toISOString()
    };
  }
}

export default StressTesting;