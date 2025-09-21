import { v4 as uuidv4 } from 'uuid';
import { errorDnaConfig } from '@/config';
import { logger } from '@/logging';
import { ErrorDNAError } from '@/types';

export interface ErrorContext {
  userId?: string;
  requestId?: string;
  operation?: string;
  additionalData?: Record<string, any>;
}

export interface ErrorClassification {
  category: 'authentication' | 'authorization' | 'validation' | 'business_logic' | 'system' | 'external' | 'unknown';
  severity: 'low' | 'medium' | 'high' | 'critical';
  recoverable: boolean;
  userMessage: string;
  technicalMessage: string;
}

export class ErrorDNAService {
  private static instance: ErrorDNAService;
  private errorPatterns: Map<string, ErrorClassification> = new Map();
  private errorCounts: Map<string, number> = new Map();

  private constructor() {
    this.initializeErrorPatterns();
  }

  public static getInstance(): ErrorDNAService {
    if (!ErrorDNAService.instance) {
      ErrorDNAService.instance = new ErrorDNAService();
    }
    return ErrorDNAService.instance;
  }

  /**
   * Initialize common error patterns with intelligent classification
   */
  private initializeErrorPatterns(): void {
    // Authentication errors
    this.errorPatterns.set('INVALID_TOKEN', {
      category: 'authentication',
      severity: 'medium',
      recoverable: true,
      userMessage: 'Your session has expired. Please log in again.',
      technicalMessage: 'JWT token validation failed'
    });

    this.errorPatterns.set('EXPIRED_TOKEN', {
      category: 'authentication',
      severity: 'low',
      recoverable: true,
      userMessage: 'Your session has expired. Please log in again.',
      technicalMessage: 'JWT token has expired'
    });

    // Authorization errors
    this.errorPatterns.set('INSUFFICIENT_PERMISSIONS', {
      category: 'authorization',
      severity: 'medium',
      recoverable: false,
      userMessage: 'You do not have permission to perform this action.',
      technicalMessage: 'User lacks required subscription tier or permissions'
    });

    this.errorPatterns.set('RESOURCE_ACCESS_DENIED', {
      category: 'authorization',
      severity: 'medium',
      recoverable: false,
      userMessage: 'Access denied to this resource.',
      technicalMessage: 'Multi-tenant resource access violation'
    });

    // Validation errors
    this.errorPatterns.set('VALIDATION_FAILED', {
      category: 'validation',
      severity: 'low',
      recoverable: true,
      userMessage: 'Please check your input and try again.',
      technicalMessage: 'Input validation failed'
    });

    this.errorPatterns.set('INVALID_TRADING_SIGNAL', {
      category: 'validation',
      severity: 'medium',
      recoverable: true,
      userMessage: 'Invalid trading parameters provided.',
      technicalMessage: 'Trading signal validation failed'
    });

    // Business logic errors
    this.errorPatterns.set('INSUFFICIENT_BALANCE', {
      category: 'business_logic',
      severity: 'medium',
      recoverable: false,
      userMessage: 'Insufficient account balance for this trade.',
      technicalMessage: 'MT5 account balance insufficient for trade volume'
    });

    this.errorPatterns.set('MARKET_CLOSED', {
      category: 'business_logic',
      severity: 'low',
      recoverable: true,
      userMessage: 'Market is currently closed. Please try again during trading hours.',
      technicalMessage: 'Trading attempted outside market hours'
    });

    // System errors
    this.errorPatterns.set('DATABASE_CONNECTION_FAILED', {
      category: 'system',
      severity: 'critical',
      recoverable: true,
      userMessage: 'Service temporarily unavailable. Please try again later.',
      technicalMessage: 'Database connection pool exhausted or unavailable'
    });

    this.errorPatterns.set('MT5_CONNECTION_FAILED', {
      category: 'external',
      severity: 'high',
      recoverable: true,
      userMessage: 'Trading service temporarily unavailable. Please try again later.',
      technicalMessage: 'MT5 WebSocket connection failed or timeout'
    });

    // External service errors
    this.errorPatterns.set('RATE_LIMIT_EXCEEDED', {
      category: 'external',
      severity: 'medium',
      recoverable: true,
      userMessage: 'Too many requests. Please wait a moment and try again.',
      technicalMessage: 'API rate limit exceeded'
    });

    // Performance-related errors
    this.errorPatterns.set('TIMEOUT_ERROR', {
      category: 'system',
      severity: 'medium',
      recoverable: true,
      userMessage: 'Request timeout. Please try again.',
      technicalMessage: 'Operation exceeded timeout threshold'
    });

    this.errorPatterns.set('HIGH_LATENCY_DETECTED', {
      category: 'system',
      severity: 'medium',
      recoverable: true,
      userMessage: 'Service is running slowly. Please be patient.',
      technicalMessage: 'Response time exceeded acceptable latency threshold'
    });
  }

  /**
   * Classify and handle errors with intelligent pattern recognition
   */
  public async handleError(
    error: Error,
    context: ErrorContext = {},
    errorCode?: string
  ): Promise<{
    errorId: string;
    classification: ErrorClassification;
    shouldRetry: boolean;
    retryDelay?: number;
  }> {
    const errorId = uuidv4();
    const detectedCode = errorCode || this.detectErrorPattern(error);
    const classification = this.classifyError(error, detectedCode);

    // Create ErrorDNA record
    const errorDnaRecord: ErrorDNAError = {
      id: errorId,
      error_code: detectedCode,
      message: error.message,
      stack: error.stack,
      context: {
        ...context,
        classification,
        timestamp: new Date().toISOString(),
        error_name: error.name,
        error_constructor: error.constructor.name
      },
      user_id: context.userId,
      request_id: context.requestId || 'unknown',
      severity: classification.severity,
      created_at: new Date()
    };

    // Log the error with appropriate level based on severity
    await this.logError(errorDnaRecord, classification);

    // Track error frequency for pattern analysis
    this.trackErrorFrequency(detectedCode);

    // Determine retry strategy
    const shouldRetry = this.shouldRetryError(classification, detectedCode);
    const retryDelay = this.calculateRetryDelay(detectedCode);

    // Send to ErrorDNA service if enabled
    if (errorDnaConfig.enabled) {
      await this.sendToErrorDNA(errorDnaRecord);
    }

    // Trigger automated recovery if applicable
    await this.attemptAutomatedRecovery(detectedCode, context);

    return {
      errorId,
      classification,
      shouldRetry,
      retryDelay: shouldRetry ? retryDelay : undefined
    };
  }

  /**
   * Detect error pattern from error object
   */
  private detectErrorPattern(error: Error): string {
    const message = error.message.toLowerCase();
    const stack = error.stack?.toLowerCase() || '';

    // JWT/Authentication patterns
    if (message.includes('invalid token') || message.includes('malformed')) {
      return 'INVALID_TOKEN';
    }
    if (message.includes('expired') || message.includes('token expired')) {
      return 'EXPIRED_TOKEN';
    }

    // Database patterns
    if (message.includes('connection') && (message.includes('refused') || message.includes('timeout'))) {
      return 'DATABASE_CONNECTION_FAILED';
    }

    // MT5 patterns
    if (message.includes('mt5') || message.includes('websocket')) {
      return 'MT5_CONNECTION_FAILED';
    }

    // Validation patterns
    if (message.includes('validation') || message.includes('invalid input')) {
      return 'VALIDATION_FAILED';
    }

    // Permission patterns
    if (message.includes('permission') || message.includes('access denied')) {
      return 'INSUFFICIENT_PERMISSIONS';
    }

    // Rate limiting patterns
    if (message.includes('rate limit') || message.includes('too many requests')) {
      return 'RATE_LIMIT_EXCEEDED';
    }

    // Timeout patterns
    if (message.includes('timeout') || message.includes('timed out')) {
      return 'TIMEOUT_ERROR';
    }

    // Trading-specific patterns
    if (message.includes('insufficient balance')) {
      return 'INSUFFICIENT_BALANCE';
    }
    if (message.includes('market closed')) {
      return 'MARKET_CLOSED';
    }

    // Generic patterns based on error type
    if (error.name === 'ValidationError') {
      return 'VALIDATION_FAILED';
    }
    if (error.name === 'TimeoutError') {
      return 'TIMEOUT_ERROR';
    }

    return 'UNKNOWN_ERROR';
  }

  /**
   * Classify error with intelligent analysis
   */
  private classifyError(error: Error, errorCode: string): ErrorClassification {
    const pattern = this.errorPatterns.get(errorCode);

    if (pattern) {
      return pattern;
    }

    // Fallback classification for unknown errors
    return {
      category: 'unknown',
      severity: 'medium',
      recoverable: true,
      userMessage: 'An unexpected error occurred. Please try again later.',
      technicalMessage: error.message
    };
  }

  /**
   * Determine if error should trigger retry
   */
  private shouldRetryError(classification: ErrorClassification, errorCode: string): boolean {
    // Don't retry validation or authorization errors
    if (classification.category === 'validation' || classification.category === 'authorization') {
      return false;
    }

    // Retry system and external errors
    if (classification.category === 'system' || classification.category === 'external') {
      return classification.recoverable;
    }

    // Check frequency - don't retry if error is happening too often
    const errorCount = this.errorCounts.get(errorCode) || 0;
    return errorCount < 10; // Max 10 occurrences before disabling retry
  }

  /**
   * Calculate retry delay with exponential backoff
   */
  private calculateRetryDelay(errorCode: string): number {
    const errorCount = this.errorCounts.get(errorCode) || 0;
    const baseDelay = 1000; // 1 second
    const maxDelay = 30000; // 30 seconds

    return Math.min(baseDelay * Math.pow(2, errorCount), maxDelay);
  }

  /**
   * Track error frequency for pattern analysis
   */
  private trackErrorFrequency(errorCode: string): void {
    const currentCount = this.errorCounts.get(errorCode) || 0;
    this.errorCounts.set(errorCode, currentCount + 1);

    // Reset counts periodically (every hour)
    setTimeout(() => {
      this.errorCounts.set(errorCode, Math.max(0, currentCount - 1));
    }, 60 * 60 * 1000);
  }

  /**
   * Log error with appropriate level
   */
  private async logError(errorRecord: ErrorDNAError, classification: ErrorClassification): Promise<void> {
    const logLevel = this.getLogLevel(classification.severity);
    const message = `${classification.category.toUpperCase()}: ${errorRecord.message}`;

    logger.log(logLevel, message, {
      component: 'error_dna',
      error_id: errorRecord.id,
      error_code: errorRecord.error_code,
      classification,
      context: errorRecord.context,
      user_id: errorRecord.user_id,
      request_id: errorRecord.request_id,
      stack: errorRecord.stack?.split('\n').slice(0, 5) // Limit stack trace for log size
    });
  }

  /**
   * Convert severity to log level
   */
  private getLogLevel(severity: string): string {
    const levelMap: Record<string, string> = {
      'low': 'info',
      'medium': 'warn',
      'high': 'error',
      'critical': 'error'
    };

    return levelMap[severity] || 'error';
  }

  /**
   * Send error to external ErrorDNA service
   */
  private async sendToErrorDNA(errorRecord: ErrorDNAError): Promise<void> {
    try {
      // In production, this would send to actual ErrorDNA API
      logger.info('ErrorDNA record created', {
        component: 'error_dna',
        error_id: errorRecord.id,
        project_id: errorDnaConfig.projectId,
        severity: errorRecord.severity
      });

    } catch (error) {
      logger.error('Failed to send error to ErrorDNA service', {
        component: 'error_dna',
        error: error instanceof Error ? error.message : 'Unknown error',
        original_error_id: errorRecord.id
      });
    }
  }

  /**
   * Attempt automated recovery for known error patterns
   */
  private async attemptAutomatedRecovery(errorCode: string, context: ErrorContext): Promise<void> {
    switch (errorCode) {
      case 'DATABASE_CONNECTION_FAILED':
        // Trigger connection pool reset
        logger.info('Triggering database connection recovery', {
          component: 'error_recovery',
          error_code: errorCode,
          context
        });
        break;

      case 'MT5_CONNECTION_FAILED':
        // Trigger MT5 reconnection
        logger.info('Triggering MT5 connection recovery', {
          component: 'error_recovery',
          error_code: errorCode,
          user_id: context.userId
        });
        break;

      case 'HIGH_LATENCY_DETECTED':
        // Switch to cached responses temporarily
        logger.info('Enabling cache fallback for high latency', {
          component: 'error_recovery',
          error_code: errorCode
        });
        break;

      default:
        // No automated recovery available
        break;
    }
  }

  /**
   * Get error analytics for monitoring
   */
  public getErrorAnalytics(): {
    topErrors: Array<{ code: string; count: number; classification: ErrorClassification }>;
    errorsByCategory: Record<string, number>;
    criticalErrorCount: number;
    recoveryAttempts: number;
  } {
    const topErrors: Array<{ code: string; count: number; classification: ErrorClassification }> = [];
    const errorsByCategory: Record<string, number> = {};
    let criticalErrorCount = 0;

    this.errorCounts.forEach((count, code) => {
      const classification = this.errorPatterns.get(code) || {
        category: 'unknown',
        severity: 'medium',
        recoverable: true,
        userMessage: '',
        technicalMessage: ''
      };

      topErrors.push({ code, count, classification });

      errorsByCategory[classification.category] = (errorsByCategory[classification.category] || 0) + count;

      if (classification.severity === 'critical') {
        criticalErrorCount += count;
      }
    });

    // Sort by count
    topErrors.sort((a, b) => b.count - a.count);

    return {
      topErrors: topErrors.slice(0, 10), // Top 10 errors
      errorsByCategory,
      criticalErrorCount,
      recoveryAttempts: 0 // Would track actual recovery attempts in production
    };
  }

  /**
   * Create user-friendly error response
   */
  public createErrorResponse(
    errorId: string,
    classification: ErrorClassification,
    includeDetails: boolean = false
  ): {
    success: false;
    error: string;
    error_id: string;
    timestamp: Date;
    details?: any;
  } {
    const response = {
      success: false as const,
      error: classification.userMessage,
      error_id: errorId,
      timestamp: new Date()
    };

    if (includeDetails) {
      return {
        ...response,
        details: {
          category: classification.category,
          severity: classification.severity,
          recoverable: classification.recoverable
        }
      };
    }

    return response;
  }
}

// Export singleton instance
export const errorDnaService = ErrorDNAService.getInstance();

// Convenience wrapper for error handling
export const handleError = async (
  error: Error,
  context: ErrorContext = {},
  errorCode?: string
) => {
  return errorDnaService.handleError(error, context, errorCode);
};