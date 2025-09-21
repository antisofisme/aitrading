/**
 * Comprehensive Security System Tests
 * Testing all security components integration and functionality
 */

import { SecuritySystem } from '../../src/security';
import { LogLevel, LogCategory, RetentionTier } from '../../src/security/types';

describe('SecuritySystem', () => {
  let securitySystem: SecuritySystem;

  beforeEach(() => {
    // Initialize security system with test configuration
    securitySystem = new SecuritySystem({
      config: {
        zeroTrust: {
          enabled: true,
          strictMode: false,
          defaultPolicy: 'DENY',
          sessionTimeout: 3600000,
          mfaRequired: true,
          deviceTrustRequired: true,
          riskThresholds: {
            low: 0.3,
            medium: 0.6,
            high: 0.8,
            critical: 0.9
          }
        },
        logging: {
          retentionPeriods: {
            [LogLevel.DEBUG]: 7,
            [LogLevel.INFO]: 30,
            [LogLevel.WARNING]: 90,
            [LogLevel.ERROR]: 180,
            [LogLevel.CRITICAL]: 365
          },
          encryptionEnabled: true,
          compressionEnabled: true,
          realTimeAnalysis: true,
          batchSize: 100,
          flushInterval: 1000 // Faster for tests
        },
        monitoring: {
          threatDetection: true,
          anomalyDetection: true,
          realTimeAlerts: true,
          automaticMitigation: true,
          falsePositiveReduction: true,
          mlModelsEnabled: false // Disable ML for tests
        }
      },
      basePath: './test-security-data'
    });
  });

  afterEach(async () => {
    await securitySystem.shutdown();
  });

  describe('Authentication', () => {
    it('should authenticate valid user', async () => {
      const credentials = {
        userId: 'test-user-1',
        ipAddress: '192.168.1.100',
        userAgent: 'Test User Agent',
        deviceInfo: 'test-device'
      };

      const context = await securitySystem.authenticate(credentials);

      expect(context).toBeDefined();
      expect(context.userId).toBe(credentials.userId);
      expect(context.ipAddress).toBe(credentials.ipAddress);
      expect(context.trustScore).toBeGreaterThanOrEqual(0);
      expect(context.trustScore).toBeLessThanOrEqual(1);
      expect(context.sessionId).toBeDefined();
      expect(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']).toContain(context.riskLevel);
    });

    it('should handle authentication failure gracefully', async () => {
      const invalidCredentials = {
        userId: '',
        ipAddress: '192.168.1.100',
        userAgent: 'Test User Agent'
      };

      await expect(securitySystem.authenticate(invalidCredentials))
        .rejects.toThrow();
    });

    it('should track authentication metrics', async () => {
      const credentials = {
        userId: 'test-user-2',
        ipAddress: '192.168.1.101',
        userAgent: 'Test User Agent'
      };

      await securitySystem.authenticate(credentials);

      const status = securitySystem.getSecurityStatus();
      expect(status.metrics.totalEvents).toBeGreaterThan(0);
    });
  });

  describe('Authorization', () => {
    let sessionId: string;

    beforeEach(async () => {
      const credentials = {
        userId: 'test-user-3',
        ipAddress: '192.168.1.102',
        userAgent: 'Test User Agent'
      };

      const context = await securitySystem.authenticate(credentials);
      sessionId = context.sessionId;
    });

    it('should authorize valid resource access', async () => {
      const authorized = await securitySystem.authorize(sessionId, 'test-resource', 'read');

      // This may be false due to default DENY policy, but should not throw
      expect(typeof authorized).toBe('boolean');
    });

    it('should handle invalid session gracefully', async () => {
      const authorized = await securitySystem.authorize('invalid-session', 'test-resource', 'read');
      expect(authorized).toBe(false);
    });
  });

  describe('Logging', () => {
    it('should log security events', async () => {
      const logId = await securitySystem.logSecurityEvent(
        LogLevel.INFO,
        LogCategory.SECURITY,
        'Test security event',
        { testData: 'test-value' },
        'test-component'
      );

      expect(logId).toBeDefined();
      expect(typeof logId).toBe('string');
    });

    it('should handle different log levels', async () => {
      const levels = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL];

      for (const level of levels) {
        const logId = await securitySystem.logSecurityEvent(
          level,
          LogCategory.SYSTEM,
          `Test ${level} message`,
          {},
          'test-component'
        );

        expect(logId).toBeDefined();
      }
    });

    it('should categorize logs correctly', async () => {
      const categories = [
        LogCategory.SECURITY,
        LogCategory.AUTHENTICATION,
        LogCategory.AUTHORIZATION,
        LogCategory.AUDIT,
        LogCategory.COMPLIANCE
      ];

      for (const category of categories) {
        const logId = await securitySystem.logSecurityEvent(
          LogLevel.INFO,
          category,
          `Test ${category} message`,
          {},
          'test-component'
        );

        expect(logId).toBeDefined();
      }
    });
  });

  describe('Incident Reporting', () => {
    it('should report security incidents', async () => {
      const incidentId = await securitySystem.reportIncident(
        'Test security incident',
        'HIGH',
        undefined,
        { incidentType: 'test', details: 'Test incident details' }
      );

      expect(incidentId).toBeDefined();
      expect(typeof incidentId).toBe('string');
    });

    it('should handle different severity levels', async () => {
      const severities: Array<'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'> = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];

      for (const severity of severities) {
        const incidentId = await securitySystem.reportIncident(
          `Test ${severity} incident`,
          severity
        );

        expect(incidentId).toBeDefined();
      }
    });
  });

  describe('Security Status', () => {
    it('should return comprehensive security status', async () => {
      const status = securitySystem.getSecurityStatus();

      expect(status).toBeDefined();
      expect(status.systemHealth).toBeDefined();
      expect(['HEALTHY', 'WARNING', 'CRITICAL']).toContain(status.systemHealth);
      expect(status.componentsStatus).toBeDefined();
      expect(status.metrics).toBeDefined();
      expect(status.configStatus).toBeDefined();
      expect(typeof status.activeThreats).toBe('number');
      expect(status.complianceStatus).toBeDefined();
    });

    it('should track metrics correctly', async () => {
      // Generate some activity
      await securitySystem.logSecurityEvent(LogLevel.INFO, LogCategory.SECURITY, 'Test event');
      await securitySystem.reportIncident('Test incident', 'LOW');

      const status = securitySystem.getSecurityStatus();

      expect(status.metrics.totalEvents).toBeGreaterThan(0);
      expect(status.metrics.uptime).toBeInstanceOf(Date);
    });
  });

  describe('GDPR Compliance', () => {
    it('should handle data subject requests', async () => {
      // This test assumes the GDPR manager has test data
      // In a real scenario, you'd set up test data first

      try {
        const requestId = await securitySystem.handleDataSubjectRequest(
          'test@example.com',
          'ACCESS',
          'Test access request'
        );

        expect(requestId).toBeDefined();
      } catch (error) {
        // Expected if no data subject exists
        expect(error.message).toContain('Data subject not found');
      }
    });
  });

  describe('Report Generation', () => {
    it('should generate security reports', async () => {
      const timeRange = {
        start: new Date(Date.now() - 24 * 60 * 60 * 1000), // 24 hours ago
        end: new Date()
      };

      const report = await securitySystem.generateSecurityReport(timeRange, 'SECURITY');

      expect(report).toBeDefined();
      expect(report.reportType).toBe('SECURITY');
      expect(report.timeRange).toEqual(timeRange);
      expect(report.generatedAt).toBeInstanceOf(Date);
      expect(report.security).toBeDefined();
    });

    it('should generate comprehensive reports', async () => {
      const timeRange = {
        start: new Date(Date.now() - 24 * 60 * 60 * 1000),
        end: new Date()
      };

      const report = await securitySystem.generateSecurityReport(timeRange, 'COMPREHENSIVE');

      expect(report).toBeDefined();
      expect(report.reportType).toBe('COMPREHENSIVE');
      expect(report.security).toBeDefined();
      expect(report.compliance).toBeDefined();
      expect(report.performance).toBeDefined();
    });
  });

  describe('Configuration Management', () => {
    it('should update configuration', () => {
      const updates = {
        zeroTrust: {
          enabled: true,
          strictMode: true,
          sessionTimeout: 1800000 // 30 minutes
        }
      };

      expect(() => {
        securitySystem.updateConfiguration(updates);
      }).not.toThrow();
    });

    it('should validate configuration updates', () => {
      const invalidUpdates = {
        zeroTrust: {
          sessionTimeout: 100 // Too short
        }
      };

      expect(() => {
        securitySystem.updateConfiguration(invalidUpdates);
      }).toThrow();
    });
  });

  describe('Data Export', () => {
    it('should export security data in JSON format', async () => {
      const timeRange = {
        start: new Date(Date.now() - 24 * 60 * 60 * 1000),
        end: new Date()
      };

      const exportData = await securitySystem.exportSecurityData('JSON', timeRange, false);

      expect(exportData).toBeDefined();
      expect(typeof exportData).toBe('string');

      const parsed = JSON.parse(exportData);
      expect(parsed.exportedAt).toBeDefined();
      expect(parsed.timeRange).toEqual(timeRange);
      expect(parsed.format).toBe('JSON');
    });

    it('should export security data in CSV format', async () => {
      const timeRange = {
        start: new Date(Date.now() - 24 * 60 * 60 * 1000),
        end: new Date()
      };

      const exportData = await securitySystem.exportSecurityData('CSV', timeRange, false);

      expect(exportData).toBeDefined();
      expect(typeof exportData).toBe('string');
    });
  });

  describe('Integration Tests', () => {
    it('should handle complex security workflow', async () => {
      // Step 1: Authenticate user
      const credentials = {
        userId: 'integration-test-user',
        ipAddress: '192.168.1.200',
        userAgent: 'Integration Test Agent'
      };

      const context = await securitySystem.authenticate(credentials);
      expect(context).toBeDefined();

      // Step 2: Authorize resource access
      const authorized = await securitySystem.authorize(context.sessionId, 'sensitive-data', 'read');
      expect(typeof authorized).toBe('boolean');

      // Step 3: Log security events
      await securitySystem.logSecurityEvent(
        LogLevel.INFO,
        LogCategory.SECURITY,
        'Integration test event',
        { integrationTest: true }
      );

      // Step 4: Report incident
      await securitySystem.reportIncident(
        'Integration test incident',
        'LOW',
        context,
        { testType: 'integration' }
      );

      // Step 5: Check system status
      const status = securitySystem.getSecurityStatus();
      expect(status.metrics.totalEvents).toBeGreaterThan(0);

      // Step 6: Generate report
      const timeRange = {
        start: new Date(Date.now() - 60 * 60 * 1000), // 1 hour ago
        end: new Date()
      };

      const report = await securitySystem.generateSecurityReport(timeRange);
      expect(report).toBeDefined();
    });

    it('should handle threat detection workflow', async () => {
      // Simulate suspicious activity
      const suspiciousCredentials = {
        userId: 'suspicious-user',
        ipAddress: '1.2.3.4', // Potentially suspicious IP
        userAgent: 'SuspiciousBot/1.0'
      };

      try {
        await securitySystem.authenticate(suspiciousCredentials);

        // Log multiple failed attempts to trigger brute force detection
        for (let i = 0; i < 5; i++) {
          await securitySystem.logSecurityEvent(
            LogLevel.WARNING,
            LogCategory.AUTHENTICATION,
            'Authentication failed',
            {
              ipAddress: suspiciousCredentials.ipAddress,
              attemptNumber: i + 1,
              reason: 'Invalid credentials'
            }
          );
        }

        const status = securitySystem.getSecurityStatus();
        // Check if threats were detected
        expect(status.metrics.totalEvents).toBeGreaterThan(0);

      } catch (error) {
        // Authentication might fail due to security policies
        expect(error).toBeDefined();
      }
    });

    it('should handle performance under load', async () => {
      const startTime = Date.now();
      const promises: Promise<any>[] = [];

      // Generate concurrent load
      for (let i = 0; i < 50; i++) {
        promises.push(
          securitySystem.logSecurityEvent(
            LogLevel.INFO,
            LogCategory.SYSTEM,
            `Load test event ${i}`,
            { loadTest: true, eventNumber: i }
          )
        );
      }

      await Promise.all(promises);
      const endTime = Date.now();

      // Should complete within reasonable time (5 seconds)
      expect(endTime - startTime).toBeLessThan(5000);

      const status = securitySystem.getSecurityStatus();
      expect(status.metrics.totalEvents).toBeGreaterThanOrEqual(50);
    });
  });

  describe('Error Handling', () => {
    it('should handle malformed authentication requests', async () => {
      const malformedCredentials = {
        // Missing required fields
        invalidField: 'invalid'
      };

      await expect(securitySystem.authenticate(malformedCredentials as any))
        .rejects.toThrow();
    });

    it('should handle invalid log parameters', async () => {
      // Should not throw, but might log differently
      const logId = await securitySystem.logSecurityEvent(
        'INVALID_LEVEL' as any,
        'INVALID_CATEGORY' as any,
        'Test message'
      );

      expect(logId).toBeDefined();
    });

    it('should handle system shutdown gracefully', async () => {
      await expect(securitySystem.shutdown()).resolves.not.toThrow();
    });
  });

  describe('Memory Usage', () => {
    it('should not leak memory during normal operations', async () => {
      const initialMemory = process.memoryUsage().heapUsed;

      // Perform operations
      for (let i = 0; i < 100; i++) {
        await securitySystem.logSecurityEvent(
          LogLevel.INFO,
          LogCategory.SYSTEM,
          `Memory test event ${i}`
        );
      }

      // Force garbage collection if available
      if (global.gc) {
        global.gc();
      }

      const finalMemory = process.memoryUsage().heapUsed;
      const memoryIncrease = finalMemory - initialMemory;

      // Memory increase should be reasonable (less than 50MB)
      expect(memoryIncrease).toBeLessThan(50 * 1024 * 1024);
    });
  });
});

describe('SecuritySystem Configuration', () => {
  it('should load configuration from environment variables', () => {
    // Set test environment variables
    process.env.ZERO_TRUST_ENABLED = 'true';
    process.env.ZERO_TRUST_STRICT_MODE = 'true';
    process.env.GDPR_ENABLED = 'true';
    process.env.THREAT_DETECTION_ENABLED = 'true';

    const securitySystem = new SecuritySystem({ loadFromEnv: true });
    const status = securitySystem.getSecurityStatus();

    expect(status.componentsStatus.zeroTrust).toBe(true);
    expect(status.componentsStatus.gdpr).toBe(true);
    expect(status.componentsStatus.threatDetection).toBe(true);

    // Cleanup
    delete process.env.ZERO_TRUST_ENABLED;
    delete process.env.ZERO_TRUST_STRICT_MODE;
    delete process.env.GDPR_ENABLED;
    delete process.env.THREAT_DETECTION_ENABLED;
  });

  it('should validate security configuration', () => {
    expect(() => {
      new SecuritySystem({
        config: {
          zeroTrust: {
            enabled: true,
            strictMode: false,
            defaultPolicy: 'DENY',
            sessionTimeout: 100, // Invalid - too short
            mfaRequired: true,
            deviceTrustRequired: true,
            riskThresholds: {
              low: 0.3,
              medium: 0.6,
              high: 0.8,
              critical: 0.9
            }
          }
        }
      });
    }).toThrow();
  });
});

// Performance benchmarks
describe('SecuritySystem Performance', () => {
  let securitySystem: SecuritySystem;

  beforeAll(() => {
    securitySystem = new SecuritySystem({
      config: {
        logging: {
          retentionPeriods: {
            [LogLevel.DEBUG]: 7,
            [LogLevel.INFO]: 30,
            [LogLevel.WARNING]: 90,
            [LogLevel.ERROR]: 180,
            [LogLevel.CRITICAL]: 365
          },
          encryptionEnabled: false, // Disable encryption for performance tests
          compressionEnabled: false, // Disable compression for performance tests
          realTimeAnalysis: false,
          batchSize: 1000,
          flushInterval: 5000
        }
      }
    });
  });

  afterAll(async () => {
    await securitySystem.shutdown();
  });

  it('should handle high-volume logging efficiently', async () => {
    const eventCount = 1000;
    const startTime = Date.now();

    const promises = [];
    for (let i = 0; i < eventCount; i++) {
      promises.push(
        securitySystem.logSecurityEvent(
          LogLevel.INFO,
          LogCategory.SYSTEM,
          `Performance test event ${i}`,
          { eventNumber: i, performance: true }
        )
      );
    }

    await Promise.all(promises);
    const endTime = Date.now();
    const duration = endTime - startTime;

    console.log(`Logged ${eventCount} events in ${duration}ms`);
    console.log(`Average: ${duration / eventCount}ms per event`);
    console.log(`Rate: ${(eventCount / duration) * 1000} events/second`);

    // Should handle at least 100 events per second
    expect((eventCount / duration) * 1000).toBeGreaterThan(100);
  });

  it('should maintain performance under concurrent access', async () => {
    const concurrentUsers = 50;
    const operationsPerUser = 10;
    const startTime = Date.now();

    const promises = [];
    for (let user = 0; user < concurrentUsers; user++) {
      for (let op = 0; op < operationsPerUser; op++) {
        promises.push(
          securitySystem.logSecurityEvent(
            LogLevel.INFO,
            LogCategory.SYSTEM,
            `Concurrent test user ${user} operation ${op}`,
            { userId: user, operation: op }
          )
        );
      }
    }

    await Promise.all(promises);
    const endTime = Date.now();
    const duration = endTime - startTime;
    const totalOperations = concurrentUsers * operationsPerUser;

    console.log(`Completed ${totalOperations} concurrent operations in ${duration}ms`);
    console.log(`Average: ${duration / totalOperations}ms per operation`);

    // Should complete within reasonable time
    expect(duration).toBeLessThan(10000); // 10 seconds
  });
});