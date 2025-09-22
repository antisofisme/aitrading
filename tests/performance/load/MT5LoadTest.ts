import { PerformanceTestBase, TestConfig } from '../infrastructure/PerformanceTestBase';
import { MT5TestHelper, MT5ConnectionConfig, MT5ConnectionPool } from '../infrastructure/MT5TestHelper';

export interface LoadTestConfig extends TestConfig {
  loadPatterns: LoadPattern[];
  rampUpDuration: number; // Time to reach peak load
  peakDuration: number; // Time to maintain peak load
  rampDownDuration: number; // Time to decrease load
  targetUsersPerSecond: number;
  maxConcurrentUsers: number;
  loadDistribution: 'linear' | 'exponential' | 'spike' | 'step';
  scenarios: LoadScenario[];
}

export interface LoadPattern {
  name: string;
  description: string;
  userCount: number;
  duration: number;
  operations: LoadOperation[];
}

export interface LoadOperation {
  type: 'order' | 'tick' | 'account' | 'positions';
  weight: number; // Probability weight (0-1)
  parameters?: any;
}

export interface LoadScenario {
  name: string;
  userPercentage: number; // What percentage of users follow this scenario
  operations: LoadOperation[];
  thinkTime: number; // Delay between operations in ms
}

export class MT5LoadTest extends PerformanceTestBase {
  private connectionPool: MT5ConnectionPool;
  private testConfig: LoadTestConfig;
  private activeUsers: Map<string, UserSession> = new Map();
  private loadResults: Map<string, LoadTestResult> = new Map();
  private currentLoad: number = 0;
  private userIdCounter: number = 0;

  constructor(
    mt5Config: MT5ConnectionConfig,
    testConfig: Partial<LoadTestConfig> = {}
  ) {
    const defaultScenarios: LoadScenario[] = [
      {
        name: 'trader',
        userPercentage: 0.6,
        operations: [
          { type: 'account', weight: 0.1 },
          { type: 'positions', weight: 0.2 },
          { type: 'tick', weight: 0.5 },
          { type: 'order', weight: 0.2 }
        ],
        thinkTime: 2000
      },
      {
        name: 'monitor',
        userPercentage: 0.3,
        operations: [
          { type: 'account', weight: 0.2 },
          { type: 'positions', weight: 0.3 },
          { type: 'tick', weight: 0.5 }
        ],
        thinkTime: 5000
      },
      {
        name: 'scalper',
        userPercentage: 0.1,
        operations: [
          { type: 'tick', weight: 0.7 },
          { type: 'order', weight: 0.3 }
        ],
        thinkTime: 500
      }
    ];

    const config: LoadTestConfig = {
      duration: 1800000, // 30 minutes
      concurrency: 100,
      warmupTime: 120000, // 2 minutes
      cooldownTime: 60000, // 1 minute
      sampleInterval: 5000,
      maxMemoryUsage: 2048,
      maxLatency: 3000, // 3 seconds under load
      minThroughput: 500,
      loadPatterns: [],
      rampUpDuration: 300000, // 5 minutes ramp up
      peakDuration: 900000, // 15 minutes peak
      rampDownDuration: 180000, // 3 minutes ramp down
      targetUsersPerSecond: 2,
      maxConcurrentUsers: 200,
      loadDistribution: 'linear',
      scenarios: defaultScenarios,
      ...testConfig
    };

    super(config);
    this.testConfig = config;
    this.connectionPool = new MT5ConnectionPool(mt5Config);
  }

  protected async warmup(): Promise<void> {
    this.emit('message', 'Starting MT5 load test warmup...');

    // Initialize connection pool with baseline connections
    const baselineConnections = Math.min(10, this.testConfig.maxConcurrentUsers);
    await this.connectionPool.createMultipleConnections(baselineConnections);

    // Create initial user sessions for warmup
    for (let i = 0; i < 5; i++) {
      await this.createUserSession();
    }

    // Execute warmup operations
    const warmupPromises = Array.from(this.activeUsers.values()).map(user =>
      this.executeUserOperations(user, 10) // 10 warmup operations per user
    );

    await Promise.all(warmupPromises);

    this.emit('message', `Load test warmup completed with ${this.activeUsers.size} users`);
  }

  protected async executeTest(): Promise<void> {
    this.emit('message', 'Starting load test execution...');

    // Execute load test phases
    await this.executeRampUp();
    await this.executePeakLoad();
    await this.executeRampDown();

    this.emit('message', 'Load test execution completed');
  }

  private async executeRampUp(): Promise<void> {
    this.emit('message', 'Starting ramp-up phase...');

    const rampStartTime = performance.now();
    const userIncrement = this.testConfig.maxConcurrentUsers / (this.testConfig.rampUpDuration / 1000);

    while (
      performance.now() - rampStartTime < this.testConfig.rampUpDuration &&
      this.isRunning
    ) {
      const targetUsers = this.calculateTargetUsers(
        performance.now() - rampStartTime,
        this.testConfig.rampUpDuration,
        this.testConfig.maxConcurrentUsers
      );

      await this.adjustUserLoad(targetUsers);

      this.emit('loadUpdate', {
        phase: 'rampUp',
        currentUsers: this.activeUsers.size,
        targetUsers,
        progress: (performance.now() - rampStartTime) / this.testConfig.rampUpDuration * 100
      });

      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    this.emit('message', `Ramp-up completed with ${this.activeUsers.size} active users`);
  }

  private async executePeakLoad(): Promise<void> {
    this.emit('message', 'Starting peak load phase...');

    const peakStartTime = performance.now();

    // Maintain peak load
    while (
      performance.now() - peakStartTime < this.testConfig.peakDuration &&
      this.isRunning
    ) {
      await this.maintainPeakLoad();

      this.emit('loadUpdate', {
        phase: 'peak',
        currentUsers: this.activeUsers.size,
        targetUsers: this.testConfig.maxConcurrentUsers,
        progress: (performance.now() - peakStartTime) / this.testConfig.peakDuration * 100
      });

      await new Promise(resolve => setTimeout(resolve, 5000)); // Check every 5 seconds
    }

    this.emit('message', 'Peak load phase completed');
  }

  private async executeRampDown(): Promise<void> {
    this.emit('message', 'Starting ramp-down phase...');

    const rampDownStartTime = performance.now();

    while (
      performance.now() - rampDownStartTime < this.testConfig.rampDownDuration &&
      this.isRunning
    ) {
      const elapsed = performance.now() - rampDownStartTime;
      const progress = elapsed / this.testConfig.rampDownDuration;
      const targetUsers = Math.floor(this.testConfig.maxConcurrentUsers * (1 - progress));

      await this.adjustUserLoad(Math.max(0, targetUsers));

      this.emit('loadUpdate', {
        phase: 'rampDown',
        currentUsers: this.activeUsers.size,
        targetUsers,
        progress: progress * 100
      });

      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    this.emit('message', 'Ramp-down completed');
  }

  private calculateTargetUsers(elapsed: number, duration: number, maxUsers: number): number {
    const progress = elapsed / duration;

    switch (this.testConfig.loadDistribution) {
      case 'linear':
        return Math.floor(maxUsers * progress);
      case 'exponential':
        return Math.floor(maxUsers * Math.pow(progress, 0.5));
      case 'spike':
        return progress > 0.8 ? maxUsers : Math.floor(maxUsers * 0.2);
      case 'step':
        return Math.floor(maxUsers * Math.floor(progress * 4) / 4);
      default:
        return Math.floor(maxUsers * progress);
    }
  }

  private async adjustUserLoad(targetUsers: number): Promise<void> {
    const currentUsers = this.activeUsers.size;

    if (targetUsers > currentUsers) {
      // Add users
      const usersToAdd = targetUsers - currentUsers;
      for (let i = 0; i < usersToAdd; i++) {
        await this.createUserSession();
      }
    } else if (targetUsers < currentUsers) {
      // Remove users
      const usersToRemove = currentUsers - targetUsers;
      const usersToStop = Array.from(this.activeUsers.keys()).slice(0, usersToRemove);

      for (const userId of usersToStop) {
        await this.stopUserSession(userId);
      }
    }

    this.currentLoad = targetUsers;
  }

  private async maintainPeakLoad(): Promise<void> {
    // Check for dropped users and replace them
    const droppedUsers: string[] = [];

    for (const [userId, session] of this.activeUsers) {
      if (!session.isActive || session.errorCount > 10) {
        droppedUsers.push(userId);
      }
    }

    // Replace dropped users
    for (const userId of droppedUsers) {
      await this.stopUserSession(userId);
      await this.createUserSession();
    }

    // Ensure we maintain target user count
    while (this.activeUsers.size < this.testConfig.maxConcurrentUsers) {
      await this.createUserSession();
    }
  }

  private async createUserSession(): Promise<UserSession> {
    const userId = `user_${++this.userIdCounter}`;
    const scenario = this.selectScenario();

    try {
      const connection = await this.connectionPool.createConnection(userId);

      const session: UserSession = {
        id: userId,
        connection,
        scenario,
        isActive: true,
        startTime: performance.now(),
        operationCount: 0,
        errorCount: 0,
        lastOperationTime: performance.now()
      };

      this.activeUsers.set(userId, session);

      // Start user operation loop
      this.startUserOperationLoop(session);

      this.emit('userAdded', { userId, scenario: scenario.name, totalUsers: this.activeUsers.size });

      return session;
    } catch (error) {
      this.recordError(error);
      throw error;
    }
  }

  private async stopUserSession(userId: string): Promise<void> {
    const session = this.activeUsers.get(userId);
    if (!session) return;

    session.isActive = false;

    try {
      await session.connection.closeConnection();
    } catch (error) {
      this.recordError(error);
    }

    this.activeUsers.delete(userId);

    this.emit('userRemoved', { userId, totalUsers: this.activeUsers.size });
  }

  private selectScenario(): LoadScenario {
    const random = Math.random();
    let cumulativeWeight = 0;

    for (const scenario of this.testConfig.scenarios) {
      cumulativeWeight += scenario.userPercentage;
      if (random <= cumulativeWeight) {
        return scenario;
      }
    }

    return this.testConfig.scenarios[0]; // Fallback
  }

  private async startUserOperationLoop(session: UserSession): Promise<void> {
    while (session.isActive && this.isRunning) {
      try {
        await this.executeUserOperation(session);
        session.operationCount++;
        session.lastOperationTime = performance.now();
        this.metrics.throughput.totalRequests++;

        // Think time between operations
        await new Promise(resolve => setTimeout(resolve, session.scenario.thinkTime));
      } catch (error) {
        session.errorCount++;
        this.recordError(error);

        // Stop session if too many errors
        if (session.errorCount > 10) {
          session.isActive = false;
          break;
        }

        // Exponential backoff on errors
        await new Promise(resolve => setTimeout(resolve, Math.min(session.errorCount * 1000, 10000)));
      }
    }
  }

  private async executeUserOperation(session: UserSession): Promise<void> {
    const operation = this.selectOperation(session.scenario.operations);
    const startTime = performance.now();

    try {
      switch (operation.type) {
        case 'order':
          await session.connection.executeOrder({
            symbol: this.getRandomSymbol(),
            volume: 0.01,
            type: Math.random() > 0.5 ? 'BUY' : 'SELL',
            comment: `Load_${session.id}`
          });
          break;

        case 'tick':
          await session.connection.getTickData(this.getRandomSymbol());
          break;

        case 'account':
          await session.connection.getAccountInfo();
          break;

        case 'positions':
          await session.connection.getPositions();
          break;
      }

      const latency = performance.now() - startTime;
      this.recordLatency(latency);

    } catch (error) {
      throw error;
    }
  }

  private selectOperation(operations: LoadOperation[]): LoadOperation {
    const totalWeight = operations.reduce((sum, op) => sum + op.weight, 0);
    const random = Math.random() * totalWeight;

    let cumulativeWeight = 0;
    for (const operation of operations) {
      cumulativeWeight += operation.weight;
      if (random <= cumulativeWeight) {
        return operation;
      }
    }

    return operations[0]; // Fallback
  }

  private getRandomSymbol(): string {
    const symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD', 'AUDUSD'];
    return symbols[Math.floor(Math.random() * symbols.length)];
  }

  private async executeUserOperations(session: UserSession, count: number): Promise<void> {
    for (let i = 0; i < count; i++) {
      if (!session.isActive) break;

      try {
        await this.executeUserOperation(session);
        session.operationCount++;
      } catch (error) {
        session.errorCount++;
        this.recordError(error);
      }
    }
  }

  protected async cooldown(): Promise<void> {
    this.emit('message', 'Starting load test cooldown...');

    // Stop all user sessions
    const stopPromises = Array.from(this.activeUsers.keys()).map(userId =>
      this.stopUserSession(userId)
    );

    await Promise.all(stopPromises);

    // Close all connections
    await this.connectionPool.closeAllConnections();

    // Generate load test analysis
    this.generateLoadAnalysis();

    this.emit('message', 'Load test cooldown completed');
  }

  private generateLoadAnalysis(): void {
    const analysis = {
      testConfiguration: {
        maxConcurrentUsers: this.testConfig.maxConcurrentUsers,
        testDuration: this.config.duration / 1000 / 60, // minutes
        scenarios: this.testConfig.scenarios.map(s => ({
          name: s.name,
          percentage: s.userPercentage * 100
        }))
      },
      performance: {
        totalRequests: this.metrics.throughput.totalRequests,
        requestsPerSecond: this.metrics.throughput.requestsPerSecond,
        averageLatency: this.metrics.latency.avg,
        p95Latency: this.metrics.latency.p95,
        errorRate: (this.metrics.errors.count / Math.max(1, this.metrics.throughput.totalRequests)) * 100
      },
      scalability: {
        maxConcurrentUsers: this.testConfig.maxConcurrentUsers,
        sustainedLoad: this.currentLoad,
        loadDistribution: this.testConfig.loadDistribution,
        scalabilityScore: this.calculateScalabilityScore()
      },
      recommendations: this.generateLoadRecommendations()
    };

    // Store analysis
    (this.metrics as any).loadAnalysis = analysis;
    this.emit('loadAnalysis', analysis);
  }

  private calculateScalabilityScore(): number {
    const errorRate = (this.metrics.errors.count / Math.max(1, this.metrics.throughput.totalRequests)) * 100;
    const latencyScore = Math.max(0, 100 - (this.metrics.latency.p95 / 30)); // 30ms baseline
    const throughputScore = Math.min(100, (this.metrics.throughput.requestsPerSecond / this.config.minThroughput) * 100);
    const errorScore = Math.max(0, 100 - (errorRate * 10));

    return (latencyScore + throughputScore + errorScore) / 3;
  }

  private generateLoadRecommendations(): string[] {
    const recommendations: string[] = [];
    const errorRate = (this.metrics.errors.count / Math.max(1, this.metrics.throughput.totalRequests)) * 100;

    if (this.metrics.latency.p95 > 2000) {
      recommendations.push('High P95 latency detected - consider optimizing MT5 operations or increasing resources');
    }

    if (errorRate > 5) {
      recommendations.push('High error rate detected - review error handling and connection stability');
    }

    if (this.metrics.throughput.requestsPerSecond < this.config.minThroughput) {
      recommendations.push('Throughput below target - consider scaling infrastructure or optimizing operations');
    }

    if (this.calculateScalabilityScore() < 70) {
      recommendations.push('Poor scalability score - comprehensive performance review recommended');
    }

    return recommendations;
  }

  public generateLoadReport(): string {
    const analysis = (this.metrics as any).loadAnalysis || {};
    let report = '# MT5 Load Test Report\n\n';

    if (analysis.testConfiguration) {
      const config = analysis.testConfiguration;
      report += `## Test Configuration\n\n`;
      report += `- **Max Concurrent Users:** ${config.maxConcurrentUsers}\n`;
      report += `- **Test Duration:** ${config.testDuration.toFixed(1)} minutes\n`;
      report += `- **User Scenarios:**\n`;
      config.scenarios.forEach((scenario: any) => {
        report += `  - ${scenario.name}: ${scenario.percentage}%\n`;
      });
      report += '\n';
    }

    if (analysis.performance) {
      const perf = analysis.performance;
      report += `## Performance Results\n\n`;
      report += `- **Total Requests:** ${perf.totalRequests.toLocaleString()}\n`;
      report += `- **Requests/Second:** ${perf.requestsPerSecond.toFixed(2)}\n`;
      report += `- **Average Latency:** ${perf.averageLatency.toFixed(2)}ms\n`;
      report += `- **P95 Latency:** ${perf.p95Latency.toFixed(2)}ms\n`;
      report += `- **Error Rate:** ${perf.errorRate.toFixed(2)}%\n\n`;
    }

    if (analysis.scalability) {
      const scale = analysis.scalability;
      report += `## Scalability Assessment\n\n`;
      report += `- **Scalability Score:** ${scale.scalabilityScore.toFixed(1)}/100\n`;
      report += `- **Sustained Load:** ${scale.sustainedLoad} users\n`;

      if (scale.scalabilityScore >= 80) {
        report += '✅ **Excellent scalability**\n\n';
      } else if (scale.scalabilityScore >= 60) {
        report += '⚠️ **Good scalability**\n\n';
      } else {
        report += '❌ **Poor scalability - optimization needed**\n\n';
      }
    }

    if (analysis.recommendations?.length > 0) {
      report += `## Recommendations\n\n`;
      analysis.recommendations.forEach((rec: string, i: number) => {
        report += `${i + 1}. ${rec}\n`;
      });
      report += '\n';
    }

    return report;
  }
}

interface UserSession {
  id: string;
  connection: MT5TestHelper;
  scenario: LoadScenario;
  isActive: boolean;
  startTime: number;
  operationCount: number;
  errorCount: number;
  lastOperationTime: number;
}

interface LoadTestResult {
  pattern: string;
  userCount: number;
  duration: number;
  throughput: number;
  errorRate: number;
  averageLatency: number;
}