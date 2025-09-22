import * as fs from 'fs/promises';
import * as path from 'path';
import faker from 'faker';
import { createReadStream } from 'fs';
import csv from 'csv-parser';

/**
 * Manages test data creation, seeding, and cleanup
 */
export class TestDataManager {
  private fixturesPath = path.join(__dirname, '../data/fixtures');
  private testDataSets: Record<string, any[]> = {};

  /**
   * Seed all test data
   */
  async seedTestData(): Promise<void> {
    console.log('Seeding test data...');

    await Promise.all([
      this.seedUserData(),
      this.seedTradingData(),
      this.seedMarketData(),
      this.seedPortfolioData(),
      this.seedTransactionData(),
      this.seedReportData()
    ]);

    console.log('Test data seeded successfully');
  }

  /**
   * Generate and seed user test data
   */
  async seedUserData(): Promise<void> {
    const users = [];

    // Admin user
    users.push({
      id: 'admin-001',
      email: 'admin@test.com',
      password: 'Admin123!',
      firstName: 'Admin',
      lastName: 'User',
      role: 'admin',
      status: 'active',
      emailVerified: true,
      twoFactorEnabled: false,
      createdAt: new Date('2024-01-01'),
      lastLogin: new Date()
    });

    // Standard trader users
    for (let i = 1; i <= 10; i++) {
      users.push({
        id: `trader-${i.toString().padStart(3, '0')}`,
        email: `trader${i}@test.com`,
        password: 'Trader123!',
        firstName: faker.name.firstName(),
        lastName: faker.name.lastName(),
        role: 'trader',
        status: 'active',
        emailVerified: true,
        twoFactorEnabled: i % 3 === 0, // Every 3rd user has 2FA
        createdAt: faker.date.past(1),
        lastLogin: faker.date.recent(7)
      });
    }

    // Premium trader users
    for (let i = 1; i <= 5; i++) {
      users.push({
        id: `premium-${i.toString().padStart(3, '0')}`,
        email: `premium${i}@test.com`,
        password: 'Premium123!',
        firstName: faker.name.firstName(),
        lastName: faker.name.lastName(),
        role: 'premium_trader',
        status: 'active',
        emailVerified: true,
        twoFactorEnabled: true,
        createdAt: faker.date.past(1),
        lastLogin: faker.date.recent(1)
      });
    }

    // Inactive/suspended users for negative testing
    users.push({
      id: 'suspended-001',
      email: 'suspended@test.com',
      password: 'Suspended123!',
      firstName: 'Suspended',
      lastName: 'User',
      role: 'trader',
      status: 'suspended',
      emailVerified: true,
      twoFactorEnabled: false,
      createdAt: faker.date.past(1),
      lastLogin: faker.date.past(30)
    });

    this.testDataSets.users = users;
    await this.saveToFixtures('users.json', users);
  }

  /**
   * Generate and seed trading data
   */
  async seedTradingData(): Promise<void> {
    const strategies = [];
    const orders = [];
    const positions = [];

    // Trading strategies
    const strategyTypes = ['momentum', 'mean_reversion', 'arbitrage', 'scalping', 'swing'];
    for (let i = 1; i <= 20; i++) {
      strategies.push({
        id: `strategy-${i.toString().padStart(3, '0')}`,
        name: `${faker.commerce.productName()} Strategy`,
        type: faker.random.arrayElement(strategyTypes),
        description: faker.lorem.sentence(),
        userId: `trader-${faker.random.number({ min: 1, max: 10 }).toString().padStart(3, '0')}`,
        parameters: {
          riskLevel: faker.random.arrayElement(['low', 'medium', 'high']),
          timeframe: faker.random.arrayElement(['1m', '5m', '15m', '1h', '4h', '1d']),
          maxPositions: faker.random.number({ min: 1, max: 10 }),
          stopLoss: faker.random.number({ min: 1, max: 5 }),
          takeProfit: faker.random.number({ min: 2, max: 10 })
        },
        status: faker.random.arrayElement(['active', 'paused', 'draft']),
        createdAt: faker.date.past(6),
        lastModified: faker.date.recent(30)
      });
    }

    // Trading orders
    const symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD'];
    const orderTypes = ['market', 'limit', 'stop', 'stop_limit'];
    const sides = ['buy', 'sell'];

    for (let i = 1; i <= 100; i++) {
      const side = faker.random.arrayElement(sides);
      const symbol = faker.random.arrayElement(symbols);

      orders.push({
        id: `order-${i.toString().padStart(3, '0')}`,
        userId: `trader-${faker.random.number({ min: 1, max: 10 }).toString().padStart(3, '0')}`,
        strategyId: `strategy-${faker.random.number({ min: 1, max: 20 }).toString().padStart(3, '0')}`,
        symbol,
        side,
        type: faker.random.arrayElement(orderTypes),
        quantity: faker.random.number({ min: 1000, max: 100000 }),
        price: faker.random.number({ min: 1.0, max: 2.0, precision: 0.00001 }),
        stopLoss: faker.random.number({ min: 0.9, max: 1.1, precision: 0.00001 }),
        takeProfit: faker.random.number({ min: 1.1, max: 2.1, precision: 0.00001 }),
        status: faker.random.arrayElement(['pending', 'filled', 'cancelled', 'rejected']),
        executedPrice: faker.random.number({ min: 1.0, max: 2.0, precision: 0.00001 }),
        executedQuantity: faker.random.number({ min: 0, max: 100000 }),
        commission: faker.random.number({ min: 0, max: 50, precision: 0.01 }),
        createdAt: faker.date.past(1),
        executedAt: faker.date.recent(7)
      });
    }

    // Open positions
    for (let i = 1; i <= 50; i++) {
      const symbol = faker.random.arrayElement(symbols);
      const side = faker.random.arrayElement(sides);

      positions.push({
        id: `position-${i.toString().padStart(3, '0')}`,
        userId: `trader-${faker.random.number({ min: 1, max: 10 }).toString().padStart(3, '0')}`,
        strategyId: `strategy-${faker.random.number({ min: 1, max: 20 }).toString().padStart(3, '0')}`,
        symbol,
        side,
        quantity: faker.random.number({ min: 1000, max: 100000 }),
        entryPrice: faker.random.number({ min: 1.0, max: 2.0, precision: 0.00001 }),
        currentPrice: faker.random.number({ min: 1.0, max: 2.0, precision: 0.00001 }),
        unrealizedPnL: faker.random.number({ min: -1000, max: 1000, precision: 0.01 }),
        stopLoss: faker.random.number({ min: 0.9, max: 1.1, precision: 0.00001 }),
        takeProfit: faker.random.number({ min: 1.1, max: 2.1, precision: 0.00001 }),
        status: 'open',
        openedAt: faker.date.past(30),
        lastUpdate: faker.date.recent(1)
      });
    }

    this.testDataSets.strategies = strategies;
    this.testDataSets.orders = orders;
    this.testDataSets.positions = positions;

    await this.saveToFixtures('strategies.json', strategies);
    await this.saveToFixtures('orders.json', orders);
    await this.saveToFixtures('positions.json', positions);
  }

  /**
   * Generate and seed market data
   */
  async seedMarketData(): Promise<void> {
    const marketData = [];
    const symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD'];

    // Generate historical market data
    for (const symbol of symbols) {
      for (let i = 0; i < 1000; i++) {
        const timestamp = new Date(Date.now() - (i * 60000)); // 1 minute intervals
        const basePrice = faker.random.number({ min: 1.0, max: 2.0, precision: 0.00001 });

        marketData.push({
          symbol,
          timestamp,
          open: basePrice,
          high: basePrice + faker.random.number({ min: 0, max: 0.001, precision: 0.00001 }),
          low: basePrice - faker.random.number({ min: 0, max: 0.001, precision: 0.00001 }),
          close: basePrice + faker.random.number({ min: -0.0005, max: 0.0005, precision: 0.00001 }),
          volume: faker.random.number({ min: 1000, max: 100000 }),
          spread: faker.random.number({ min: 0.00001, max: 0.0001, precision: 0.00001 })
        });
      }
    }

    this.testDataSets.marketData = marketData;
    await this.saveToFixtures('market-data.json', marketData);
  }

  /**
   * Generate and seed portfolio data
   */
  async seedPortfolioData(): Promise<void> {
    const portfolios = [];

    for (let i = 1; i <= 15; i++) {
      portfolios.push({
        id: `portfolio-${i.toString().padStart(3, '0')}`,
        userId: `trader-${faker.random.number({ min: 1, max: 10 }).toString().padStart(3, '0')}`,
        name: `${faker.commerce.productName()} Portfolio`,
        description: faker.lorem.sentence(),
        balance: faker.random.number({ min: 10000, max: 1000000, precision: 0.01 }),
        equity: faker.random.number({ min: 10000, max: 1000000, precision: 0.01 }),
        marginUsed: faker.random.number({ min: 0, max: 50000, precision: 0.01 }),
        marginAvailable: faker.random.number({ min: 10000, max: 500000, precision: 0.01 }),
        totalPnL: faker.random.number({ min: -10000, max: 50000, precision: 0.01 }),
        dayPnL: faker.random.number({ min: -1000, max: 5000, precision: 0.01 }),
        currency: 'USD',
        leverage: faker.random.arrayElement([1, 10, 50, 100, 200, 500]),
        riskLevel: faker.random.arrayElement(['conservative', 'moderate', 'aggressive']),
        createdAt: faker.date.past(1),
        lastUpdate: faker.date.recent(1)
      });
    }

    this.testDataSets.portfolios = portfolios;
    await this.saveToFixtures('portfolios.json', portfolios);
  }

  /**
   * Generate and seed transaction data
   */
  async seedTransactionData(): Promise<void> {
    const transactions = [];
    const transactionTypes = ['deposit', 'withdrawal', 'trade', 'commission', 'swap', 'dividend'];

    for (let i = 1; i <= 200; i++) {
      transactions.push({
        id: `txn-${i.toString().padStart(5, '0')}`,
        userId: `trader-${faker.random.number({ min: 1, max: 10 }).toString().padStart(3, '0')}`,
        portfolioId: `portfolio-${faker.random.number({ min: 1, max: 15 }).toString().padStart(3, '0')}`,
        type: faker.random.arrayElement(transactionTypes),
        amount: faker.random.number({ min: -10000, max: 10000, precision: 0.01 }),
        currency: 'USD',
        description: faker.lorem.sentence(),
        reference: faker.random.alphaNumeric(10),
        status: faker.random.arrayElement(['completed', 'pending', 'failed']),
        createdAt: faker.date.past(1),
        processedAt: faker.date.recent(1)
      });
    }

    this.testDataSets.transactions = transactions;
    await this.saveToFixtures('transactions.json', transactions);
  }

  /**
   * Generate and seed report data
   */
  async seedReportData(): Promise<void> {
    const reports = [];
    const reportTypes = ['daily_pnl', 'monthly_summary', 'risk_analysis', 'performance_review', 'compliance_audit'];

    for (let i = 1; i <= 50; i++) {
      reports.push({
        id: `report-${i.toString().padStart(3, '0')}`,
        userId: `trader-${faker.random.number({ min: 1, max: 10 }).toString().padStart(3, '0')}`,
        type: faker.random.arrayElement(reportTypes),
        title: `${faker.commerce.productName()} Report`,
        description: faker.lorem.paragraph(),
        dateFrom: faker.date.past(30),
        dateTo: faker.date.recent(1),
        data: {
          totalTrades: faker.random.number({ min: 10, max: 1000 }),
          winRate: faker.random.number({ min: 40, max: 80, precision: 0.1 }),
          avgProfit: faker.random.number({ min: 10, max: 500, precision: 0.01 }),
          maxDrawdown: faker.random.number({ min: 5, max: 25, precision: 0.1 }),
          sharpeRatio: faker.random.number({ min: 0.5, max: 3.0, precision: 0.1 })
        },
        format: faker.random.arrayElement(['pdf', 'excel', 'json']),
        status: faker.random.arrayElement(['generated', 'pending', 'failed']),
        filePath: `/reports/report-${i.toString().padStart(3, '0')}.pdf`,
        createdAt: faker.date.past(30),
        generatedAt: faker.date.recent(1)
      });
    }

    this.testDataSets.reports = reports;
    await this.saveToFixtures('reports.json', reports);
  }

  /**
   * Get test data by type
   */
  getTestData(type: string): any[] {
    return this.testDataSets[type] || [];
  }

  /**
   * Get specific test user
   */
  getTestUser(role: string = 'trader'): any {
    const users = this.getTestData('users');
    return users.find(user => user.role === role);
  }

  /**
   * Get test credentials
   */
  getTestCredentials(role: string = 'trader'): { email: string; password: string } {
    const user = this.getTestUser(role);
    return {
      email: user.email,
      password: user.password
    };
  }

  /**
   * Load data from CSV file
   */
  async loadFromCSV(filename: string): Promise<any[]> {
    const filePath = path.join(this.fixturesPath, filename);
    const data: any[] = [];

    return new Promise((resolve, reject) => {
      createReadStream(filePath)
        .pipe(csv())
        .on('data', (row) => data.push(row))
        .on('end', () => resolve(data))
        .on('error', reject);
    });
  }

  /**
   * Save test data to fixtures
   */
  async saveToFixtures(filename: string, data: any[]): Promise<void> {
    const filePath = path.join(this.fixturesPath, filename);
    await fs.mkdir(this.fixturesPath, { recursive: true });
    await fs.writeFile(filePath, JSON.stringify(data, null, 2));
  }

  /**
   * Load test data from fixtures
   */
  async loadFromFixtures(filename: string): Promise<any[]> {
    const filePath = path.join(this.fixturesPath, filename);
    try {
      const content = await fs.readFile(filePath, 'utf8');
      return JSON.parse(content);
    } catch (error) {
      console.warn(`Failed to load fixtures from ${filename}:`, error);
      return [];
    }
  }

  /**
   * Cleanup all test data
   */
  async cleanupTestData(): Promise<void> {
    console.log('Cleaning up test data...');

    // Clear in-memory data
    this.testDataSets = {};

    // Clean up fixture files
    try {
      await fs.rm(this.fixturesPath, { recursive: true, force: true });
    } catch (error) {
      console.warn('Failed to cleanup fixtures:', error);
    }

    console.log('Test data cleanup completed');
  }

  /**
   * Reset test data to initial state
   */
  async resetTestData(): Promise<void> {
    console.log('Resetting test data...');
    await this.cleanupTestData();
    await this.seedTestData();
    console.log('Test data reset completed');
  }
}