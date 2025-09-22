const EventEmitter = require('events');
const { ISLAMIC_TRADING } = require('../config/forexPairs');
const logger = require('../utils/logger');

class IslamicTradingService extends EventEmitter {
  constructor(options = {}) {
    super();
    this.enabled = options.enabled !== false; // Default enabled
    this.swapFreeAccounts = new Map();
    this.islamicCompliantPairs = new Set();
    this.restrictions = new Map();
    this.auditLog = [];
    
    this.initializeIslamicTrading();
  }

  /**
   * Initialize Islamic trading compliance system
   */
  initializeIslamicTrading() {
    if (!this.enabled) {
      logger.info('Islamic trading service disabled');
      return;
    }

    // Initialize compliant pairs
    ISLAMIC_TRADING.supportedPairs.forEach(pair => {
      this.islamicCompliantPairs.add(pair);
    });

    // Set up audit logging
    this.setupAuditLogging();

    logger.info('Islamic trading service initialized', {
      supportedPairs: ISLAMIC_TRADING.supportedPairs.length,
      swapFreeEnabled: ISLAMIC_TRADING.swapFreeEnabled,
      shariahCompliant: ISLAMIC_TRADING.requirements.shariahCompliant
    });
  }

  /**
   * Register an Islamic (swap-free) account
   */
  registerIslamicAccount(accountId, accountDetails) {
    const islamicAccount = {
      accountId,
      accountType: 'islamic',
      swapFree: true,
      registeredAt: Date.now(),
      compliance: {
        shariahCompliant: true,
        noRiba: true,
        noGharar: true,
        noMaysir: true
      },
      restrictions: {
        carryTrading: false,
        longTermPositions: 'limited',
        rolloverFees: false,
        interestBasedInstruments: false
      },
      tradingLimits: {
        maxPositionSize: accountDetails.maxPositionSize || 100000,
        maxDailyVolume: accountDetails.maxDailyVolume || 1000000,
        allowedPairs: ISLAMIC_TRADING.supportedPairs,
        positionHoldingPeriod: accountDetails.maxHoldingDays || 30 // days
      },
      verification: {
        religionVerified: accountDetails.religionVerified || false,
        documentationComplete: accountDetails.documentationComplete || false,
        shariahBoardApproval: accountDetails.shariahBoardApproval || false
      },
      ...accountDetails
    };

    this.swapFreeAccounts.set(accountId, islamicAccount);

    this.auditLog.push({
      action: 'ISLAMIC_ACCOUNT_REGISTERED',
      accountId,
      timestamp: Date.now(),
      details: { accountType: 'islamic', swapFree: true }
    });

    this.emit('islamicAccountRegistered', {
      accountId,
      account: islamicAccount,
      timestamp: Date.now()
    });

    logger.info('Islamic account registered', {
      accountId,
      compliance: islamicAccount.compliance
    });

    return islamicAccount;
  }

  /**
   * Verify if an account is Islamic compliant
   */
  isIslamicAccount(accountId) {
    return this.swapFreeAccounts.has(accountId);
  }

  /**
   * Get Islamic account details
   */
  getIslamicAccount(accountId) {
    return this.swapFreeAccounts.get(accountId);
  }

  /**
   * Validate if a trading pair is Islamic compliant
   */
  isCompliantPair(symbol) {
    return this.islamicCompliantPairs.has(symbol);
  }

  /**
   * Validate Islamic trading compliance for a trade
   */
  validateTrade(accountId, tradeRequest) {
    const validation = {
      isValid: true,
      violations: [],
      warnings: [],
      restrictions: []
    };

    const islamicAccount = this.getIslamicAccount(accountId);
    if (!islamicAccount) {
      validation.isValid = false;
      validation.violations.push('Account is not registered as Islamic');
      return validation;
    }

    // Check pair compliance
    if (!this.isCompliantPair(tradeRequest.symbol)) {
      validation.isValid = false;
      validation.violations.push(`Trading pair ${tradeRequest.symbol} is not Shariah compliant`);
    }

    // Check for interest-based restrictions
    if (tradeRequest.type === 'carry_trade') {
      validation.isValid = false;
      validation.violations.push('Carry trading is prohibited for Islamic accounts');
    }

    // Check position holding period
    if (tradeRequest.holdingPeriod && tradeRequest.holdingPeriod > islamicAccount.tradingLimits.positionHoldingPeriod) {
      validation.warnings.push(`Position holding period exceeds recommended limit of ${islamicAccount.tradingLimits.positionHoldingPeriod} days`);
    }

    // Check position size limits
    if (tradeRequest.positionSize > islamicAccount.tradingLimits.maxPositionSize) {
      validation.isValid = false;
      validation.violations.push(`Position size exceeds maximum limit of ${islamicAccount.tradingLimits.maxPositionSize}`);
    }

    // Check for gambling (Maysir) indicators
    if (this.detectGamblingPattern(tradeRequest)) {
      validation.isValid = false;
      validation.violations.push('Trade pattern resembles gambling (Maysir), which is prohibited');
    }

    // Check for excessive uncertainty (Gharar)
    if (this.detectExcessiveUncertainty(tradeRequest)) {
      validation.warnings.push('Trade involves high uncertainty (Gharar) - proceed with caution');
    }

    // Log validation
    this.auditLog.push({
      action: 'TRADE_VALIDATION',
      accountId,
      tradeRequest: {
        symbol: tradeRequest.symbol,
        type: tradeRequest.type,
        positionSize: tradeRequest.positionSize
      },
      validation,
      timestamp: Date.now()
    });

    return validation;
  }

  /**
   * Detect gambling patterns (Maysir)
   */
  detectGamblingPattern(tradeRequest) {
    // Check for high-risk, speculative patterns
    const riskIndicators = [
      tradeRequest.leverage && tradeRequest.leverage > 100, // Very high leverage
      tradeRequest.stopLoss && tradeRequest.stopLoss < 0.01, // Very tight stop loss
      tradeRequest.type === 'scalping' && tradeRequest.frequency > 50, // Excessive scalping
      tradeRequest.riskReward && tradeRequest.riskReward > 10 // Unrealistic risk/reward
    ];

    return riskIndicators.filter(Boolean).length >= 2;
  }

  /**
   * Detect excessive uncertainty (Gharar)
   */
  detectExcessiveUncertainty(tradeRequest) {
    const uncertaintyIndicators = [
      !tradeRequest.stopLoss, // No stop loss
      !tradeRequest.takeProfit, // No take profit
      tradeRequest.type === 'binary_option', // Binary options
      tradeRequest.expiry && tradeRequest.expiry < 300000 // Very short expiry (< 5 minutes)
    ];

    return uncertaintyIndicators.filter(Boolean).length >= 2;
  }

  /**
   * Calculate swap-free overnight fees (should be zero)
   */
  calculateSwapFee(accountId, position) {
    const islamicAccount = this.getIslamicAccount(accountId);
    
    if (!islamicAccount) {
      // Regular account - calculate normal swap
      return this.calculateRegularSwap(position);
    }

    // Islamic account - no swap fees
    this.auditLog.push({
      action: 'SWAP_FREE_CALCULATION',
      accountId,
      positionId: position.id,
      swapFee: 0,
      timestamp: Date.now()
    });

    return {
      swapFee: 0,
      reason: 'Islamic account - swap-free',
      calculation: {
        baseSwap: this.calculateRegularSwap(position).swapFee,
        islamicDiscount: '100%',
        finalSwap: 0
      }
    };
  }

  /**
   * Calculate regular swap for comparison
   */
  calculateRegularSwap(position) {
    // Simplified swap calculation
    const interestRateDiff = position.interestRateDiff || 0.001; // 0.1%
    const positionValue = position.size * position.price;
    const dailySwap = positionValue * interestRateDiff / 365;
    
    return {
      swapFee: position.type === 'long' ? dailySwap : -dailySwap,
      interestRateDiff,
      positionValue,
      calculation: 'Standard swap calculation'
    };
  }

  /**
   * Generate Islamic trading compliance report
   */
  generateComplianceReport(accountId, period = 30) {
    const islamicAccount = this.getIslamicAccount(accountId);
    if (!islamicAccount) {
      throw new Error('Account is not registered as Islamic');
    }

    const periodStart = Date.now() - (period * 24 * 60 * 60 * 1000);
    const relevantAuditLogs = this.auditLog.filter(log => 
      log.accountId === accountId && log.timestamp >= periodStart
    );

    const report = {
      accountId,
      reportPeriod: {
        days: period,
        startDate: new Date(periodStart).toISOString(),
        endDate: new Date().toISOString()
      },
      compliance: {
        totalTrades: relevantAuditLogs.filter(log => log.action === 'TRADE_VALIDATION').length,
        complianceViolations: relevantAuditLogs.filter(log => 
          log.action === 'TRADE_VALIDATION' && !log.validation.isValid
        ).length,
        swapFeesCharged: 0, // Always 0 for Islamic accounts
        prohibitedInstruments: 0
      },
      shariahPrinciples: {
        noRiba: {
          compliant: true,
          interestCharges: 0,
          swapFees: 0
        },
        noGharar: {
          compliant: true,
          uncertaintyWarnings: relevantAuditLogs.filter(log => 
            log.validation && log.validation.warnings.some(w => w.includes('Gharar'))
          ).length
        },
        noMaysir: {
          compliant: true,
          gamblingViolations: relevantAuditLogs.filter(log => 
            log.validation && log.validation.violations.some(v => v.includes('Maysir'))
          ).length
        }
      },
      recommendations: this.generateComplianceRecommendations(relevantAuditLogs),
      auditTrail: relevantAuditLogs.slice(-50) // Last 50 audit entries
    };

    // Calculate overall compliance score
    report.complianceScore = this.calculateComplianceScore(report);

    return report;
  }

  /**
   * Generate compliance recommendations
   */
  generateComplianceRecommendations(auditLogs) {
    const recommendations = [];
    
    const violations = auditLogs.filter(log => 
      log.validation && !log.validation.isValid
    );

    const warnings = auditLogs.filter(log => 
      log.validation && log.validation.warnings.length > 0
    );

    if (violations.length > 0) {
      recommendations.push({
        priority: 'high',
        category: 'compliance_violation',
        message: `Address ${violations.length} compliance violations`,
        action: 'Review trading strategy to avoid prohibited practices'
      });
    }

    if (warnings.length > 5) {
      recommendations.push({
        priority: 'medium',
        category: 'risk_management',
        message: 'Multiple uncertainty warnings detected',
        action: 'Improve risk management and trade planning'
      });
    }

    if (recommendations.length === 0) {
      recommendations.push({
        priority: 'info',
        category: 'compliance',
        message: 'Excellent Shariah compliance maintained',
        action: 'Continue current trading practices'
      });
    }

    return recommendations;
  }

  /**
   * Calculate compliance score (0-100)
   */
  calculateComplianceScore(report) {
    let score = 100;
    
    // Deduct for violations
    score -= report.compliance.complianceViolations * 10;
    
    // Deduct for warnings
    const totalWarnings = report.shariahPrinciples.noGharar.uncertaintyWarnings +
                         report.shariahPrinciples.noMaysir.gamblingViolations;
    score -= totalWarnings * 2;
    
    // Ensure score doesn't go below 0
    return Math.max(0, score);
  }

  /**
   * Setup audit logging
   */
  setupAuditLogging() {
    // Keep audit log size manageable
    setInterval(() => {
      if (this.auditLog.length > 10000) {
        this.auditLog = this.auditLog.slice(-5000); // Keep last 5000 entries
      }
    }, 3600000); // Check every hour
  }

  /**
   * Get Islamic trading statistics
   */
  getStatistics() {
    const stats = {
      totalIslamicAccounts: this.swapFreeAccounts.size,
      supportedPairs: this.islamicCompliantPairs.size,
      auditLogEntries: this.auditLog.length,
      complianceFeatures: {
        swapFree: ISLAMIC_TRADING.swapFreeEnabled,
        shariahCompliant: ISLAMIC_TRADING.requirements.shariahCompliant,
        noInterest: ISLAMIC_TRADING.requirements.noInterest,
        instantSettlement: ISLAMIC_TRADING.requirements.instantSettlement
      },
      restrictions: {
        carryTrade: ISLAMIC_TRADING.restrictions.carryTrade,
        longTermPositions: ISLAMIC_TRADING.restrictions.longTermPositions,
        rolloverFees: ISLAMIC_TRADING.restrictions.rolloverFees
      }
    };

    return stats;
  }

  /**
   * Export audit log for external compliance systems
   */
  exportAuditLog(startDate, endDate, format = 'json') {
    const start = new Date(startDate).getTime();
    const end = new Date(endDate).getTime();
    
    const filteredLogs = this.auditLog.filter(log => 
      log.timestamp >= start && log.timestamp <= end
    );

    if (format === 'csv') {
      return this.convertToCSV(filteredLogs);
    }

    return {
      exportDate: new Date().toISOString(),
      period: { startDate, endDate },
      totalEntries: filteredLogs.length,
      auditLog: filteredLogs
    };
  }

  /**
   * Convert audit log to CSV format
   */
  convertToCSV(logs) {
    const headers = ['Timestamp', 'Account ID', 'Action', 'Details', 'Compliance Status'];
    const rows = logs.map(log => [
      new Date(log.timestamp).toISOString(),
      log.accountId || '',
      log.action,
      JSON.stringify(log.details || {}),
      log.validation ? (log.validation.isValid ? 'COMPLIANT' : 'VIOLATION') : 'N/A'
    ]);

    return [headers, ...rows].map(row => row.join(',')).join('\n');
  }

  /**
   * Update Islamic account settings
   */
  updateIslamicAccount(accountId, updates) {
    const account = this.getIslamicAccount(accountId);
    if (!account) {
      throw new Error('Islamic account not found');
    }

    // Validate updates don't compromise compliance
    if (updates.swapFree === false) {
      throw new Error('Cannot disable swap-free for Islamic account');
    }

    Object.assign(account, updates, {
      lastUpdated: Date.now()
    });

    this.auditLog.push({
      action: 'ISLAMIC_ACCOUNT_UPDATED',
      accountId,
      updates,
      timestamp: Date.now()
    });

    this.emit('islamicAccountUpdated', {
      accountId,
      account,
      updates,
      timestamp: Date.now()
    });

    return account;
  }
}

module.exports = IslamicTradingService;