/**
 * Compliance Framework Integration Layer
 * Integrates compliance framework with existing AI trading architecture
 */

import { EventEmitter } from 'events';
import { ComplianceFramework, ComplianceConfiguration } from './ComplianceFramework';
import { getComplianceConfig } from '../config/compliance/ComplianceConfig';

export interface TradingSystemIntegration {
  // Trading Engine Integration
  onTradingDecision?: (decision: any) => Promise<void>;
  onPositionUpdate?: (position: any) => Promise<void>;
  onMarketData?: (marketData: any) => Promise<void>;

  // Risk Management Integration
  onRiskAssessment?: (assessment: any) => Promise<void>;
  onLimitBreach?: (breach: any) => Promise<void>;

  // Model Management Integration
  onModelUpdate?: (model: any) => Promise<void>;
  onModelValidation?: (validation: any) => Promise<void>;

  // System Integration
  onSystemHealth?: (health: any) => Promise<void>;
  onAlert?: (alert: any) => Promise<void>;
}

export interface MemoryCoordination {
  sessionId: string;
  complianceKey: string;
  riskKey: string;
  auditKey: string;
  reportingKey: string;
}

export class ComplianceIntegration extends EventEmitter {
  private complianceFramework: ComplianceFramework;
  private integration: TradingSystemIntegration;
  private memoryCoordination: MemoryCoordination;
  private isInitialized: boolean = false;

  constructor(
    config?: ComplianceConfiguration,
    integration?: TradingSystemIntegration,
    sessionId: string = 'compliance-session'
  ) {
    super();

    this.complianceFramework = new ComplianceFramework(
      config || getComplianceConfig()
    );

    this.integration = integration || {};

    this.memoryCoordination = {
      sessionId,
      complianceKey: `${sessionId}/compliance`,
      riskKey: `${sessionId}/risk`,
      auditKey: `${sessionId}/audit`,
      reportingKey: `${sessionId}/reporting`
    };

    this.initializeIntegration();
  }

  private async initializeIntegration(): Promise<void> {
    try {
      // Set up compliance framework event handlers
      this.setupComplianceHandlers();

      // Initialize memory coordination
      await this.initializeMemoryCoordination();

      // Set up trading system integration
      this.setupTradingIntegration();

      this.isInitialized = true;

      this.emit('integration:initialized', {
        timestamp: new Date().toISOString(),
        sessionId: this.memoryCoordination.sessionId
      });

    } catch (error) {
      this.emit('integration:error', {
        error: error.message,
        phase: 'initialization',
        timestamp: new Date().toISOString()
      });
      throw error;
    }
  }

  private setupComplianceHandlers(): void {
    // Human oversight events
    this.complianceFramework.on('compliance:human_oversight_required', async (data) => {
      await this.storeInMemory('oversight_required', data);
      this.emit('integration:human_oversight_required', data);
    });

    // Circuit breaker events
    this.complianceFramework.on('compliance:circuit_breaker', async (data) => {
      await this.storeInMemory('circuit_breaker_triggered', data);
      this.emit('integration:circuit_breaker_triggered', data);
    });

    // Compliance violations
    this.complianceFramework.on('compliance:violation', async (data) => {
      await this.storeInMemory('violation', data);
      this.emit('integration:compliance_violation', data);
    });

    // Stress test results
    this.complianceFramework.on('stress_test:completed', async (data) => {
      await this.storeInMemory('stress_test_result', data);
      this.emit('integration:stress_test_completed', data);
    });
  }

  private async initializeMemoryCoordination(): Promise<void> {
    // Store initial compliance status in memory for coordination
    const status = this.complianceFramework.getComplianceStatus();
    await this.storeInMemory('compliance_status', status);

    // Initialize coordination keys
    await this.storeInMemory('session_info', {
      sessionId: this.memoryCoordination.sessionId,
      initialized: new Date().toISOString(),
      components: ['compliance', 'audit', 'risk', 'reporting']
    });
  }

  private setupTradingIntegration(): void {
    // Set up default integration handlers if not provided
    if (!this.integration.onTradingDecision) {
      this.integration.onTradingDecision = this.defaultTradingDecisionHandler.bind(this);
    }

    if (!this.integration.onMarketData) {
      this.integration.onMarketData = this.defaultMarketDataHandler.bind(this);
    }

    if (!this.integration.onRiskAssessment) {
      this.integration.onRiskAssessment = this.defaultRiskAssessmentHandler.bind(this);
    }
  }

  /**
   * Process trading decision through compliance framework
   */
  public async processTradingDecision(decision: {
    symbol: string;
    action: 'BUY' | 'SELL' | 'HOLD';
    quantity: number;
    price: number;
    confidence: number;
    modelId: string;
    reasoning: string;
    riskScore: number;
    timestamp?: string;
    accountId?: string;
  }): Promise<{ approved: boolean; requiresOversight: boolean; violations: any[] }> {
    if (!this.isInitialized) {
      throw new Error('Compliance integration not initialized');
    }

    try {
      // Ensure timestamp is set
      if (!decision.timestamp) {
        decision.timestamp = new Date().toISOString();
      }

      // Store decision in memory for coordination
      await this.storeInMemory('pending_decision', decision);

      // Process through compliance framework
      await this.complianceFramework.logTradingDecision(decision);

      // Call integration handler
      if (this.integration.onTradingDecision) {
        await this.integration.onTradingDecision(decision);
      }

      // Determine if oversight is required
      const requiresOversight = decision.riskScore > 0.8; // Configurable threshold

      // Check for any active violations
      const complianceStatus = this.complianceFramework.getComplianceStatus();
      const violations = complianceStatus.monitor?.violations || [];

      // Store result in memory
      const result = {
        approved: !requiresOversight && violations.length === 0,
        requiresOversight,
        violations,
        timestamp: new Date().toISOString()
      };

      await this.storeInMemory('decision_result', result);

      return result;

    } catch (error) {
      this.emit('integration:error', {
        error: error.message,
        operation: 'process_trading_decision',
        decision,
        timestamp: new Date().toISOString()
      });
      throw error;
    }
  }

  /**
   * Process market data for circuit breaker monitoring
   */
  public async processMarketData(marketData: {
    symbol: string;
    price: number;
    volume: number;
    timestamp: string;
    volatility?: number;
  }): Promise<void> {
    if (!this.isInitialized) {
      throw new Error('Compliance integration not initialized');
    }

    try {
      // Store market data in memory
      await this.storeInMemory(`market_data_${marketData.symbol}`, marketData);

      // Call integration handler
      if (this.integration.onMarketData) {
        await this.integration.onMarketData(marketData);
      }

      this.emit('integration:market_data_processed', {
        symbol: marketData.symbol,
        timestamp: marketData.timestamp
      });

    } catch (error) {
      this.emit('integration:error', {
        error: error.message,
        operation: 'process_market_data',
        marketData,
        timestamp: new Date().toISOString()
      });
    }
  }

  /**
   * Execute stress test and coordinate results
   */
  public async executeStressTest(scenarioId?: string): Promise<any> {
    if (!this.isInitialized) {
      throw new Error('Compliance integration not initialized');
    }

    try {
      const result = await this.complianceFramework.executeStressTest(scenarioId);

      // Store stress test result in memory for coordination
      await this.storeInMemory('latest_stress_test', result);

      // Notify other agents through memory
      if (result.failed) {
        await this.storeInMemory('stress_test_failure', {
          testId: result.testId,
          scenario: result.scenario.id,
          violations: result.violations,
          recommendations: result.recommendations,
          timestamp: result.timestamp
        });
      }

      return result;

    } catch (error) {
      this.emit('integration:error', {
        error: error.message,
        operation: 'execute_stress_test',
        scenarioId,
        timestamp: new Date().toISOString()
      });
      throw error;
    }
  }

  /**
   * Generate and coordinate compliance report
   */
  public async generateComplianceReport(startDate: Date, endDate: Date): Promise<any> {
    if (!this.isInitialized) {
      throw new Error('Compliance integration not initialized');
    }

    try {
      const report = await this.complianceFramework.generateComplianceReport(startDate, endDate);

      // Store report in memory for coordination
      await this.storeInMemory('latest_compliance_report', {
        reportId: report.id,
        period: report.period,
        summary: report.summary,
        certifications: report.certifications,
        generatedAt: new Date().toISOString()
      });

      return report;

    } catch (error) {
      this.emit('integration:error', {
        error: error.message,
        operation: 'generate_compliance_report',
        startDate: startDate.toISOString(),
        endDate: endDate.toISOString(),
        timestamp: new Date().toISOString()
      });
      throw error;
    }
  }

  /**
   * Get comprehensive compliance status for coordination
   */
  public async getComplianceStatus(): Promise<any> {
    if (!this.isInitialized) {
      throw new Error('Compliance integration not initialized');
    }

    const status = this.complianceFramework.getComplianceStatus();

    // Store current status in memory
    await this.storeInMemory('current_status', {
      ...status,
      lastUpdated: new Date().toISOString(),
      sessionId: this.memoryCoordination.sessionId
    });

    return status;
  }

  /**
   * Store data in memory for cross-agent coordination
   */
  private async storeInMemory(key: string, data: any): Promise<void> {
    try {
      // This would integrate with the actual memory system
      // For now, emit event for coordination
      this.emit('integration:memory_store', {
        key: `${this.memoryCoordination.complianceKey}/${key}`,
        data,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      // Log but don't fail on memory storage errors
      this.emit('integration:memory_error', {
        error: error.message,
        key,
        timestamp: new Date().toISOString()
      });
    }
  }

  /**
   * Retrieve data from memory for coordination
   */
  private async retrieveFromMemory(key: string): Promise<any> {
    try {
      // This would integrate with the actual memory system
      // For now, emit event and return null
      this.emit('integration:memory_retrieve', {
        key: `${this.memoryCoordination.complianceKey}/${key}`,
        timestamp: new Date().toISOString()
      });
      return null;
    } catch (error) {
      this.emit('integration:memory_error', {
        error: error.message,
        key,
        timestamp: new Date().toISOString()
      });
      return null;
    }
  }

  // Default integration handlers
  private async defaultTradingDecisionHandler(decision: any): Promise<void> {
    // Default implementation - just log the decision
    this.emit('integration:trading_decision_processed', {
      symbol: decision.symbol,
      action: decision.action,
      riskScore: decision.riskScore,
      timestamp: decision.timestamp
    });
  }

  private async defaultMarketDataHandler(marketData: any): Promise<void> {
    // Default implementation - just log the market data
    this.emit('integration:market_data_received', {
      symbol: marketData.symbol,
      price: marketData.price,
      volume: marketData.volume,
      timestamp: marketData.timestamp
    });
  }

  private async defaultRiskAssessmentHandler(assessment: any): Promise<void> {
    // Default implementation - just log the risk assessment
    this.emit('integration:risk_assessment_processed', {
      riskLevel: assessment.riskLevel,
      timestamp: assessment.timestamp
    });
  }

  /**
   * Update integration configuration
   */
  public updateIntegration(integration: Partial<TradingSystemIntegration>): void {
    this.integration = { ...this.integration, ...integration };
    this.emit('integration:configuration_updated', {
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Get integration status
   */
  public getIntegrationStatus(): any {
    return {
      initialized: this.isInitialized,
      sessionId: this.memoryCoordination.sessionId,
      complianceStatus: this.isInitialized ? this.complianceFramework.getComplianceStatus() : null,
      memoryCoordination: this.memoryCoordination,
      integrationHandlers: {
        onTradingDecision: !!this.integration.onTradingDecision,
        onPositionUpdate: !!this.integration.onPositionUpdate,
        onMarketData: !!this.integration.onMarketData,
        onRiskAssessment: !!this.integration.onRiskAssessment,
        onLimitBreach: !!this.integration.onLimitBreach,
        onModelUpdate: !!this.integration.onModelUpdate,
        onModelValidation: !!this.integration.onModelValidation,
        onSystemHealth: !!this.integration.onSystemHealth,
        onAlert: !!this.integration.onAlert
      }
    };
  }

  /**
   * Shutdown integration and cleanup
   */
  public async shutdown(): Promise<void> {
    if (this.isInitialized) {
      await this.complianceFramework.shutdown();

      // Store shutdown status in memory
      await this.storeInMemory('shutdown', {
        timestamp: new Date().toISOString(),
        sessionId: this.memoryCoordination.sessionId
      });

      this.isInitialized = false;

      this.emit('integration:shutdown', {
        timestamp: new Date().toISOString(),
        sessionId: this.memoryCoordination.sessionId
      });
    }
  }
}

export default ComplianceIntegration;