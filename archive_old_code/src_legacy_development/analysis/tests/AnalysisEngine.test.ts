/**
 * Test suite for the Analysis Engine
 * Comprehensive tests for core functionality
 */

import { describe, test, expect, beforeEach, afterEach, jest } from '@jest/globals';
import { promises as fs } from 'fs';
import * as path from 'path';
import { AnalysisEngine } from '../core/AnalysisEngine';
import { createAnalysisEngine, defaultConfig, defaultLogger } from '../index';
import {
  AnalysisConfig,
  ElementType,
  RelationshipType,
  DiagramType
} from '../types';

// Mock file system
jest.mock('fs', () => ({
  promises: {
    readFile: jest.fn(),
    writeFile: jest.fn(),
    mkdir: jest.fn(),
    access: jest.fn(),
    stat: jest.fn(),
    readdir: jest.fn(),
    unlink: jest.fn(),
    rm: jest.fn()
  }
}));

// Mock external dependencies
jest.mock('chokidar');
jest.mock('glob');
jest.mock('child_process');

const mockFs = fs as jest.Mocked<typeof fs>;

describe('AnalysisEngine', () => {
  let engine: AnalysisEngine;
  let testConfig: AnalysisConfig;

  beforeEach(() => {
    testConfig = {
      ...defaultConfig,
      cache: { ...defaultConfig.cache, enabled: false },
      hooks: { ...defaultConfig.hooks, enabled: false }
    };

    engine = createAnalysisEngine(testConfig, defaultLogger);

    // Reset mocks
    jest.clearAllMocks();
  });

  afterEach(async () => {
    if (engine) {
      await engine.dispose();
    }
  });

  describe('Initialization', () => {
    test('should initialize successfully', async () => {
      await expect(engine.initialize()).resolves.not.toThrow();
    });

    test('should initialize with custom configuration', async () => {
      const customConfig = {
        ...testConfig,
        include: ['custom/**/*.ts'],
        exclude: ['custom/**/test/**']
      };

      const customEngine = createAnalysisEngine(customConfig, defaultLogger);
      await expect(customEngine.initialize()).resolves.not.toThrow();
      await customEngine.dispose();
    });
  });

  describe('File Analysis', () => {
    beforeEach(async () => {
      await engine.initialize();
    });

    test('should analyze TypeScript class', async () => {
      const testCode = `
        export class TradingStrategy {
          private name: string;

          constructor(name: string) {
            this.name = name;
          }

          execute(data: MarketData): Signal {
            return this.generateSignal(data);
          }

          private generateSignal(data: MarketData): Signal {
            // Strategy logic
            return new Signal();
          }
        }

        interface MarketData {
          price: number;
          volume: number;
        }

        class Signal {
          action: 'BUY' | 'SELL' | 'HOLD';
        }
      `;

      mockFs.readFile.mockResolvedValue(testCode);
      mockFs.access.mockResolvedValue(undefined);
      mockFs.stat.mockResolvedValue({ mtime: new Date() } as any);

      const result = await engine.analyze('/test/trading-strategy.ts');

      expect(result.graph.elements.size).toBeGreaterThan(0);
      expect(result.graph.relationships.size).toBeGreaterThan(0);

      // Check for trading strategy element
      const strategyElement = Array.from(result.graph.elements.values())
        .find(e => e.name === 'TradingStrategy');
      expect(strategyElement).toBeDefined();
      expect(strategyElement?.type).toBe(ElementType.TRADING_STRATEGY);
    });

    test('should extract relationships correctly', async () => {
      const testCode = `
        class OrderManager {
          private riskManager: RiskManager;

          constructor(riskManager: RiskManager) {
            this.riskManager = riskManager;
          }

          placeOrder(order: Order): void {
            this.riskManager.validateOrder(order);
          }
        }

        class RiskManager {
          validateOrder(order: Order): boolean {
            return true;
          }
        }
      `;

      mockFs.readFile.mockResolvedValue(testCode);
      mockFs.access.mockResolvedValue(undefined);
      mockFs.stat.mockResolvedValue({ mtime: new Date() } as any);

      const result = await engine.analyze('/test/order-manager.ts');

      // Check for dependency relationship
      const dependencyRel = Array.from(result.graph.relationships.values())
        .find(r => r.type === RelationshipType.DEPENDS_ON || r.type === RelationshipType.COMPOSITION);
      expect(dependencyRel).toBeDefined();

      // Check for method call relationship
      const callRel = Array.from(result.graph.relationships.values())
        .find(r => r.type === RelationshipType.CALLS);
      expect(callRel).toBeDefined();
    });

    test('should handle JavaScript files', async () => {
      const testCode = `
        const MovingAverageStrategy = {
          calculate: function(prices, period) {
            return prices.slice(-period).reduce((a, b) => a + b, 0) / period;
          },

          generateSignal: function(currentPrice, movingAverage) {
            if (currentPrice > movingAverage) {
              return 'BUY';
            }
            return 'SELL';
          }
        };

        module.exports = MovingAverageStrategy;
      `;

      mockFs.readFile.mockResolvedValue(testCode);
      mockFs.access.mockResolvedValue(undefined);
      mockFs.stat.mockResolvedValue({ mtime: new Date() } as any);

      const result = await engine.analyze('/test/ma-strategy.js');

      expect(result.graph.elements.size).toBeGreaterThan(0);

      const variableElement = Array.from(result.graph.elements.values())
        .find(e => e.name === 'MovingAverageStrategy');
      expect(variableElement).toBeDefined();
    });
  });

  describe('Trading Pattern Recognition', () => {
    beforeEach(async () => {
      await engine.initialize();
    });

    test('should identify trading strategies', async () => {
      const testCode = `
        export class RSIStrategy implements TradingStrategy {
          private period: number = 14;

          calculateRSI(prices: number[]): number {
            // RSI calculation logic
            return 50;
          }

          execute(data: MarketData): Signal {
            const rsi = this.calculateRSI(data.prices);
            if (rsi > 70) return new Signal('SELL');
            if (rsi < 30) return new Signal('BUY');
            return new Signal('HOLD');
          }
        }
      `;

      mockFs.readFile.mockResolvedValue(testCode);
      mockFs.access.mockResolvedValue(undefined);
      mockFs.stat.mockResolvedValue({ mtime: new Date() } as any);

      const result = await engine.analyze('/test/rsi-strategy.ts');

      const rsiStrategy = Array.from(result.graph.elements.values())
        .find(e => e.name === 'RSIStrategy');
      expect(rsiStrategy?.type).toBe(ElementType.TRADING_STRATEGY);
    });

    test('should identify risk management components', async () => {
      const testCode = `
        export class PositionSizer {
          calculatePositionSize(signal: Signal, account: Account): number {
            const riskAmount = account.balance * 0.02; // 2% risk
            const stopLossDistance = signal.price - signal.stopLoss;
            return riskAmount / stopLossDistance;
          }
        }

        export class StopLossManager {
          private stopLosses: Map<string, number> = new Map();

          setStopLoss(orderId: string, price: number): void {
            this.stopLosses.set(orderId, price);
          }

          checkStopLoss(orderId: string, currentPrice: number): boolean {
            const stopPrice = this.stopLosses.get(orderId);
            return stopPrice ? currentPrice <= stopPrice : false;
          }
        }
      `;

      mockFs.readFile.mockResolvedValue(testCode);
      mockFs.access.mockResolvedValue(undefined);
      mockFs.stat.mockResolvedValue({ mtime: new Date() } as any);

      const result = await engine.analyze('/test/risk-components.ts');

      const positionSizer = Array.from(result.graph.elements.values())
        .find(e => e.name === 'PositionSizer');
      expect(positionSizer?.type).toBe(ElementType.RISK_COMPONENT);

      const stopLossManager = Array.from(result.graph.elements.values())
        .find(e => e.name === 'StopLossManager');
      expect(stopLossManager?.type).toBe(ElementType.RISK_COMPONENT);
    });
  });

  describe('Diagram Generation', () => {
    beforeEach(async () => {
      await engine.initialize();
    });

    test('should generate class diagram', async () => {
      const testCode = `
        export class OrderBook {
          private bids: Order[] = [];
          private asks: Order[] = [];

          addBid(order: Order): void {
            this.bids.push(order);
          }

          addAsk(order: Order): void {
            this.asks.push(order);
          }
        }

        interface Order {
          id: string;
          price: number;
          quantity: number;
        }
      `;

      mockFs.readFile.mockResolvedValue(testCode);
      mockFs.access.mockResolvedValue(undefined);
      mockFs.stat.mockResolvedValue({ mtime: new Date() } as any);

      const result = await engine.analyze('/test/order-book.ts');

      const classDiagram = result.diagrams.find(d => d.type === DiagramType.CLASS_DIAGRAM);
      expect(classDiagram).toBeDefined();
      expect(classDiagram?.content).toContain('classDiagram');
      expect(classDiagram?.content).toContain('OrderBook');
    });

    test('should generate trading flow diagram', async () => {
      const testCode = `
        export class MarketDataFeed {
          subscribe(callback: (data: MarketData) => void): void {}
        }

        export class TradingEngine {
          private strategy: TradingStrategy;
          private riskManager: RiskManager;

          processMarketData(data: MarketData): void {
            const signal = this.strategy.execute(data);
            if (this.riskManager.validateSignal(signal)) {
              this.executeOrder(signal);
            }
          }
        }
      `;

      mockFs.readFile.mockResolvedValue(testCode);
      mockFs.access.mockResolvedValue(undefined);
      mockFs.stat.mockResolvedValue({ mtime: new Date() } as any);

      const result = await engine.analyze('/test/trading-engine.ts');

      const tradingFlowDiagram = result.diagrams.find(d => d.type === DiagramType.TRADING_FLOW);
      expect(tradingFlowDiagram).toBeDefined();
      expect(tradingFlowDiagram?.content).toContain('flowchart');
    });
  });

  describe('Trading Metrics', () => {
    beforeEach(async () => {
      await engine.initialize();
    });

    test('should calculate trading system metrics', async () => {
      const testCode = `
        export class MovingAverageStrategy {}
        export class RSIStrategy {}
        export class RiskManager {}
        export class PositionSizer {}
        export class OrderManager {}

        export interface MarketDataAPI {
          getPrice(): Promise<number>;
        }
      `;

      mockFs.readFile.mockResolvedValue(testCode);
      mockFs.access.mockResolvedValue(undefined);
      mockFs.stat.mockResolvedValue({ mtime: new Date() } as any);

      const metrics = await engine.getTradingMetrics();

      expect(metrics.strategyCount).toBeGreaterThan(0);
      expect(metrics.riskComponentCount).toBeGreaterThan(0);
      expect(metrics.complexityScore).toBeGreaterThan(0);
      expect(metrics.riskScore).toBeGreaterThan(0);
    });
  });

  describe('Error Handling', () => {
    beforeEach(async () => {
      await engine.initialize();
    });

    test('should handle invalid TypeScript code gracefully', async () => {
      const invalidCode = `
        export class InvalidClass {
          // Missing closing brace
      `;

      mockFs.readFile.mockResolvedValue(invalidCode);
      mockFs.access.mockResolvedValue(undefined);
      mockFs.stat.mockResolvedValue({ mtime: new Date() } as any);

      await expect(engine.analyze('/test/invalid.ts')).resolves.not.toThrow();
    });

    test('should handle missing files gracefully', async () => {
      mockFs.access.mockRejectedValue(new Error('File not found'));

      await expect(engine.analyze('/test/missing.ts')).resolves.not.toThrow();
    });

    test('should handle filesystem errors gracefully', async () => {
      mockFs.readFile.mockRejectedValue(new Error('Permission denied'));
      mockFs.access.mockResolvedValue(undefined);

      await expect(engine.analyze('/test/permission-denied.ts')).resolves.not.toThrow();
    });
  });

  describe('Incremental Analysis', () => {
    beforeEach(async () => {
      await engine.initialize();
    });

    test('should analyze single file', async () => {
      const testCode = `
        export class QuickStrategy {
          execute(): void {}
        }
      `;

      mockFs.readFile.mockResolvedValue(testCode);
      mockFs.access.mockResolvedValue(undefined);
      mockFs.stat.mockResolvedValue({ mtime: new Date() } as any);

      await expect(engine.analyzeFile('/test/quick.ts')).resolves.not.toThrow();
    });
  });

  describe('Summary Generation', () => {
    beforeEach(async () => {
      await engine.initialize();
    });

    test('should generate analysis summary', async () => {
      const testCode = `
        export class TestStrategy {}
        export class TestRiskManager {}
      `;

      mockFs.readFile.mockResolvedValue(testCode);
      mockFs.access.mockResolvedValue(undefined);
      mockFs.stat.mockResolvedValue({ mtime: new Date() } as any);

      const summary = await engine.generateSummary();

      expect(summary).toContain('AI Trading System Analysis Summary');
      expect(summary).toContain('Elements');
      expect(summary).toContain('Relationships');
      expect(summary).toContain('Trading System Metrics');
    });
  });
});

describe('Integration Tests', () => {
  test('should create engine with default configuration', () => {
    const engine = createAnalysisEngine();
    expect(engine).toBeInstanceOf(AnalysisEngine);
  });

  test('should create engine with custom configuration', () => {
    const customConfig = {
      include: ['custom/**/*.ts'],
      cache: { enabled: false, ttl: 0, strategy: 'memory' as const, namespace: 'test' },
      hooks: { enabled: false, events: [], incremental: false, notificationThreshold: 0 }
    };

    const engine = createAnalysisEngine(customConfig);
    expect(engine).toBeInstanceOf(AnalysisEngine);
  });

  test('should handle configuration merging correctly', () => {
    const partialConfig = {
      include: ['custom/**/*.ts'],
      cache: { enabled: false }
    };

    const engine = createAnalysisEngine(partialConfig);
    expect(engine).toBeInstanceOf(AnalysisEngine);
  });
});

describe('Performance Tests', () => {
  test('should handle large codebases efficiently', async () => {
    const engine = createAnalysisEngine({
      ...defaultConfig,
      cache: { enabled: false, ttl: 0, strategy: 'memory', namespace: 'test' },
      hooks: { enabled: false, events: [], incremental: false, notificationThreshold: 0 }
    });

    await engine.initialize();

    // Mock multiple large files
    const largeCode = `
      export class LargeClass {
        ${Array(100).fill(0).map((_, i) => `
          method${i}(): void {
            // Some complex logic
            if (Math.random() > 0.5) {
              this.method${(i + 1) % 100}();
            }
          }
        `).join('')}
      }
    `;

    mockFs.readFile.mockResolvedValue(largeCode);
    mockFs.access.mockResolvedValue(undefined);
    mockFs.stat.mockResolvedValue({ mtime: new Date() } as any);

    const startTime = Date.now();
    const result = await engine.analyze('/test/large.ts');
    const duration = Date.now() - startTime;

    expect(duration).toBeLessThan(5000); // Should complete within 5 seconds
    expect(result.graph.elements.size).toBeGreaterThan(0);

    await engine.dispose();
  });
});

describe('Edge Cases', () => {
  let engine: AnalysisEngine;

  beforeEach(async () => {
    engine = createAnalysisEngine({
      ...defaultConfig,
      cache: { enabled: false, ttl: 0, strategy: 'memory', namespace: 'test' },
      hooks: { enabled: false, events: [], incremental: false, notificationThreshold: 0 }
    });
    await engine.initialize();
  });

  afterEach(async () => {
    await engine.dispose();
  });

  test('should handle empty files', async () => {
    mockFs.readFile.mockResolvedValue('');
    mockFs.access.mockResolvedValue(undefined);
    mockFs.stat.mockResolvedValue({ mtime: new Date() } as any);

    const result = await engine.analyze('/test/empty.ts');
    expect(result.graph.elements.size).toBe(0);
  });

  test('should handle files with only comments', async () => {
    const commentOnlyCode = `
      // This is just a comment file
      /*
       * Multiple line comment
       * with more details
       */
    `;

    mockFs.readFile.mockResolvedValue(commentOnlyCode);
    mockFs.access.mockResolvedValue(undefined);
    mockFs.stat.mockResolvedValue({ mtime: new Date() } as any);

    const result = await engine.analyze('/test/comments.ts');
    expect(result.graph.elements.size).toBe(0);
  });

  test('should handle complex nested structures', async () => {
    const nestedCode = `
      export namespace Trading {
        export namespace Strategies {
          export class NestedStrategy {
            execute(): void {
              const innerFunction = () => {
                class InnerClass {
                  method(): void {}
                }
                return new InnerClass();
              };
            }
          }
        }
      }
    `;

    mockFs.readFile.mockResolvedValue(nestedCode);
    mockFs.access.mockResolvedValue(undefined);
    mockFs.stat.mockResolvedValue({ mtime: new Date() } as any);

    const result = await engine.analyze('/test/nested.ts');
    expect(result.graph.elements.size).toBeGreaterThan(0);
  });
});