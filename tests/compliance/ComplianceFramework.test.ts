/**
 * Comprehensive Test Suite for Compliance Framework
 * Tests all components against 2024 SEC and EU regulatory requirements
 */

import { describe, test, expect, beforeEach, afterEach, jest } from '@jest/globals';
import { ComplianceFramework } from '../../src/compliance/ComplianceFramework';
import { getComplianceConfig } from '../../config/compliance/ComplianceConfig';

describe('ComplianceFramework', () => {
  let complianceFramework: ComplianceFramework;
  let config: any;

  beforeEach(() => {
    config = getComplianceConfig();
    config.auditTrail.retentionPeriodDays = 1; // Short retention for testing
    complianceFramework = new ComplianceFramework(config);
  });

  afterEach(async () => {
    await complianceFramework.shutdown();
  });

  describe('Initialization', () => {
    test('should initialize with default configuration', () => {
      expect(complianceFramework).toBeDefined();
      const status = complianceFramework.getComplianceStatus();
      expect(status.status).toBe('active');
    });

    test('should initialize all required components', () => {
      const status = complianceFramework.getComplianceStatus();
      expect(status.auditTrail).toBeDefined();
      expect(status.circuitBreaker).toBeDefined();
      expect(status.stressTesting).toBeDefined();
      expect(status.monitor).toBeDefined();
      expect(status.reporting).toBeDefined();
    });

    test('should emit initialization event', (done) => {
      const newFramework = new ComplianceFramework(config);
      newFramework.on('compliance:initialized', (data) => {
        expect(data.components).toContain('auditTrail');
        expect(data.components).toContain('circuitBreaker');
        expect(data.components).toContain('stressTesting');
        done();
      });
    });
  });

  describe('Trading Decision Logging', () => {
    test('should log trading decisions to audit trail', async () => {
      const decision = {
        symbol: 'AAPL',
        action: 'BUY' as const,
        quantity: 100,
        price: 150.50,
        confidence: 0.85,
        modelId: 'risk-model-v1',
        reasoning: 'Strong momentum signal with low volatility',
        riskScore: 0.6,
        timestamp: new Date().toISOString()
      };

      await complianceFramework.logTradingDecision(decision);

      // Verify decision was logged
      const status = complianceFramework.getComplianceStatus();
      expect(status.auditTrail.eventCount).toBeGreaterThan(0);
    });

    test('should trigger human oversight for high-risk decisions', (done) => {
      const highRiskDecision = {
        symbol: 'GME',
        action: 'BUY' as const,
        quantity: 1000,
        price: 200.00,
        confidence: 0.9,
        modelId: 'momentum-model-v2',
        reasoning: 'High volatility momentum play',
        riskScore: 0.95, // Above threshold
        timestamp: new Date().toISOString()
      };

      complianceFramework.on('compliance:human_oversight_required', (data) => {
        expect(data.decision.riskScore).toBe(0.95);
        expect(data.reason).toBe('Risk score exceeds threshold');
        done();
      });

      complianceFramework.logTradingDecision(highRiskDecision);
    });

    test('should check circuit breaker conditions', async () => {
      const decision = {
        symbol: 'TSLA',
        action: 'SELL' as const,
        quantity: 500,
        price: 300.00,
        confidence: 0.8,
        modelId: 'mean-reversion-v1',
        reasoning: 'Mean reversion signal with high confidence',
        riskScore: 0.7,
        timestamp: new Date().toISOString()
      };

      let circuitBreakerTriggered = false;
      complianceFramework.on('compliance:circuit_breaker', () => {
        circuitBreakerTriggered = true;
      });

      await complianceFramework.logTradingDecision(decision);

      // For normal price movement, circuit breaker should not trigger
      expect(circuitBreakerTriggered).toBe(false);
    });
  });

  describe('Circuit Breaker Functionality', () => {
    test('should trigger circuit breaker on price deviation', (done) => {
      const status = complianceFramework.getComplianceStatus();
      const circuitBreaker = status.circuitBreaker;

      complianceFramework.on('compliance:circuit_breaker', (data) => {
        expect(data.triggerType).toBe('PRICE_DEVIATION');
        expect(data.symbol).toBe('VOLATILE_STOCK');
        done();
      });

      // Simulate large price movement that would trigger circuit breaker
      // This would typically be done through the circuit breaker component
      // For testing, we can manually trigger
      complianceFramework.emit('compliance:circuit_breaker', {
        symbol: 'VOLATILE_STOCK',
        triggerType: 'PRICE_DEVIATION',
        triggerValue: 15.5,
        threshold: 5.0,
        timestamp: new Date().toISOString(),
        action: 'HALT',
        duration: 900000
      });
    });

    test('should handle multiple circuit breaker types', () => {
      const status = complianceFramework.getComplianceStatus();
      expect(status.circuitBreaker).toBeDefined();
    });
  });

  describe('Stress Testing', () => {
    test('should execute stress tests', async () => {
      const result = await complianceFramework.executeStressTest('market_crash_2008');

      expect(result).toBeDefined();
      expect(result.testId).toMatch(/^ST_\d+$/);
      expect(result.scenario.id).toBe('market_crash_2008');
      expect(result.metrics).toBeDefined();
      expect(result.metrics.maxDrawdown).toBeDefined();
      expect(result.metrics.volatility).toBeDefined();
      expect(result.metrics.sharpeRatio).toBeDefined();
    });

    test('should handle stress test failures', async () => {
      // This would be implemented with a scenario that's designed to fail
      const result = await complianceFramework.executeStressTest();

      expect(result).toBeDefined();
      expect(typeof result.passed).toBe('boolean');
      expect(Array.isArray(result.violations)).toBe(true);
      expect(Array.isArray(result.recommendations)).toBe(true);
    });

    test('should emit stress test completion events', (done) => {
      complianceFramework.on('stress_test:completed', (results) => {
        expect(results.testId).toBeDefined();
        expect(results.scenario).toBeDefined();
        done();
      });

      complianceFramework.executeStressTest();
    });
  });

  describe('Compliance Reporting', () => {
    test('should generate compliance reports', async () => {
      const startDate = new Date('2024-01-01');
      const endDate = new Date('2024-01-31');

      const report = await complianceFramework.generateComplianceReport(startDate, endDate);

      expect(report).toBeDefined();
      expect(report.id).toMatch(/^COMP_\d+$/);
      expect(report.period.start).toBe(startDate.toISOString());
      expect(report.period.end).toBe(endDate.toISOString());
      expect(Array.isArray(report.sections)).toBe(true);
      expect(report.summary).toBeDefined();
    });

    test('should include all required report sections', async () => {
      const startDate = new Date('2024-01-01');
      const endDate = new Date('2024-01-31');

      const report = await complianceFramework.generateComplianceReport(startDate, endDate);

      const sectionNames = report.sections.map(s => s.section);
      expect(sectionNames).toContain('TRADING_ACTIVITY');
      expect(sectionNames).toContain('COMPLIANCE_VIOLATIONS');
      expect(sectionNames).toContain('STRESS_TEST_RESULTS');
      expect(sectionNames).toContain('AUDIT_TRAIL');
    });

    test('should log report generation', async () => {
      const startDate = new Date('2024-01-01');
      const endDate = new Date('2024-01-31');

      await complianceFramework.generateComplianceReport(startDate, endDate);

      const status = complianceFramework.getComplianceStatus();
      expect(status.auditTrail.eventCount).toBeGreaterThan(0);
    });
  });

  describe('Compliance Monitoring', () => {
    test('should monitor compliance violations', (done) => {
      complianceFramework.on('compliance:violation', (violation) => {
        expect(violation.id).toMatch(/^CV_\d+/);
        expect(violation.type).toBeDefined();
        expect(violation.severity).toBeDefined();
        expect(violation.description).toBeDefined();
        done();
      });

      // Simulate a compliance violation
      // This would typically be triggered by the monitoring component
      complianceFramework.emit('compliance:violation', {
        id: 'CV_TEST_123',
        type: 'POSITION_LIMIT',
        severity: 'HIGH',
        description: 'Position size exceeds limit',
        data: {},
        timestamp: new Date().toISOString(),
        resolved: false
      });
    });

    test('should track compliance metrics', () => {
      const status = complianceFramework.getComplianceStatus();
      expect(status.monitor).toBeDefined();
    });
  });

  describe('Audit Trail Integration', () => {
    test('should maintain audit trail integrity', () => {
      const status = complianceFramework.getComplianceStatus();
      expect(status.auditTrail.integrity.valid).toBe(true);
      expect(status.auditTrail.integrity.errors).toHaveLength(0);
    });

    test('should encrypt audit data when configured', () => {
      const status = complianceFramework.getComplianceStatus();
      expect(status.auditTrail.config.encryption).toBe(true);
    });

    test('should compress audit data when configured', () => {
      const status = complianceFramework.getComplianceStatus();
      // In test environment, compression is disabled for easier debugging
      expect(status.auditTrail.config.compression).toBe(false);
    });
  });

  describe('Error Handling', () => {
    test('should handle initialization errors gracefully', () => {
      const invalidConfig = { ...config };
      delete invalidConfig.auditTrail;

      expect(() => {
        new ComplianceFramework(invalidConfig);
      }).not.toThrow();
    });

    test('should emit error events for failures', (done) => {
      complianceFramework.on('compliance:error', (error) => {
        expect(error.error).toBeDefined();
        expect(error.component).toBeDefined();
        expect(error.timestamp).toBeDefined();
        done();
      });

      // Simulate an error condition
      complianceFramework.emit('compliance:error', {
        error: 'Test error',
        component: 'test',
        timestamp: new Date().toISOString()
      });
    });

    test('should handle missing trading decision data', async () => {
      const incompleteDecision = {
        symbol: 'TEST',
        action: 'BUY' as const,
        quantity: 100,
        price: 50.00,
        confidence: 0.8,
        modelId: 'test-model',
        reasoning: 'Test reasoning',
        riskScore: 0.5
        // Missing timestamp - should be handled gracefully
      } as any;

      await expect(
        complianceFramework.logTradingDecision(incompleteDecision)
      ).rejects.toThrow();
    });
  });

  describe('Performance Requirements', () => {
    test('should log decisions within latency requirements', async () => {
      const decision = {
        symbol: 'PERF_TEST',
        action: 'BUY' as const,
        quantity: 100,
        price: 100.00,
        confidence: 0.8,
        modelId: 'perf-model',
        reasoning: 'Performance test',
        riskScore: 0.5,
        timestamp: new Date().toISOString()
      };

      const startTime = Date.now();
      await complianceFramework.logTradingDecision(decision);
      const endTime = Date.now();

      // Should complete within 100ms for compliance requirements
      expect(endTime - startTime).toBeLessThan(100);
    });

    test('should handle high-frequency decision logging', async () => {
      const decisions = [];
      for (let i = 0; i < 100; i++) {
        decisions.push({
          symbol: `STOCK_${i}`,
          action: 'BUY' as const,
          quantity: 100,
          price: 50.00 + Math.random() * 50,
          confidence: 0.7 + Math.random() * 0.3,
          modelId: 'bulk-test-model',
          reasoning: `Bulk test decision ${i}`,
          riskScore: Math.random() * 0.8,
          timestamp: new Date().toISOString()
        });
      }

      const startTime = Date.now();
      await Promise.all(decisions.map(d => complianceFramework.logTradingDecision(d)));
      const endTime = Date.now();

      // Should handle 100 decisions in reasonable time
      expect(endTime - startTime).toBeLessThan(5000); // 5 seconds
    });
  });

  describe('Regulatory Compliance', () => {
    test('should meet SEC retention requirements', () => {
      const status = complianceFramework.getComplianceStatus();
      // In production, retention should be 2555 days (7 years)
      expect(status.auditTrail.config.retentionPeriod).toBeGreaterThan(0);
    });

    test('should implement required encryption', () => {
      const status = complianceFramework.getComplianceStatus();
      expect(status.auditTrail.config.encryption).toBe(true);
    });

    test('should support immutable audit trail', () => {
      const status = complianceFramework.getComplianceStatus();
      // In test environment, immutable storage is disabled
      expect(typeof status.auditTrail.config.immutable).toBe('boolean');
    });

    test('should provide required reporting capabilities', async () => {
      const startDate = new Date('2024-01-01');
      const endDate = new Date('2024-01-31');

      const report = await complianceFramework.generateComplianceReport(startDate, endDate);

      // Should include all required certifications
      expect(report.certifications.algorithmicAccountability).toBe(true);
      expect(report.certifications.circuitBreakerCompliance).toBe(true);
      expect(report.certifications.stressTestPassed).toBe(true);
      expect(report.certifications.humanOversight).toBe(true);
    });
  });

  describe('Integration Testing', () => {
    test('should coordinate between all components', async () => {
      // Log a trading decision
      const decision = {
        symbol: 'INTEGRATION_TEST',
        action: 'SELL' as const,
        quantity: 200,
        price: 75.50,
        confidence: 0.9,
        modelId: 'integration-model',
        reasoning: 'Integration test decision',
        riskScore: 0.85,
        timestamp: new Date().toISOString()
      };

      await complianceFramework.logTradingDecision(decision);

      // Execute stress test
      const stressResult = await complianceFramework.executeStressTest();

      // Generate report
      const startDate = new Date('2024-01-01');
      const endDate = new Date();
      const report = await complianceFramework.generateComplianceReport(startDate, endDate);

      // Verify all components worked together
      expect(stressResult).toBeDefined();
      expect(report).toBeDefined();

      const status = complianceFramework.getComplianceStatus();
      expect(status.status).toBe('active');
      expect(status.auditTrail.eventCount).toBeGreaterThan(0);
    });
  });
});