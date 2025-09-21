import { Router, Response } from 'express';
import Joi from 'joi';
import { v4 as uuidv4 } from 'uuid';
import { DatabaseService } from '@/database';
import { MT5ConnectionManager } from '@/mt5';
import { createSecurityMiddleware } from '@/security';
import { logger, logTrading } from '@/logging';
import { handleError } from '@/utils/errorDna';
import { AuthenticatedRequest, ApiResponse, TradingSignal, SubscriptionTier } from '@/types';

const router = Router();

// Validation schemas
const createSignalSchema = Joi.object({
  symbol: Joi.string().min(1).max(10).required(),
  type: Joi.string().valid('buy', 'sell').required(),
  entry_price: Joi.number().positive().required(),
  stop_loss: Joi.number().positive().optional(),
  take_profit: Joi.number().positive().optional(),
  volume: Joi.number().positive().max(100).required(),
  confidence: Joi.number().min(0).max(100).required(),
  reasoning: Joi.string().max(500).required(),
  expires_in_minutes: Joi.number().min(1).max(1440).default(60) // 1 minute to 24 hours
});

const executeSignalSchema = Joi.object({
  signal_id: Joi.string().uuid().required(),
  mt5_account_id: Joi.string().uuid().required()
});

const addMT5AccountSchema = Joi.object({
  login: Joi.string().required(),
  server: Joi.string().required(),
  name: Joi.string().max(100).required()
});

// Initialize services
export const createTradingRoutes = (
  databaseService: DatabaseService,
  mt5ConnectionManager: MT5ConnectionManager
): Router => {
  const security = createSecurityMiddleware(databaseService);

  /**
   * Get user's trading signals
   * GET /api/v1/trading/signals
   */
  router.get('/signals', [
    security.authenticate,
    security.requireBasic,
    security.rateLimiter
  ], async (req: AuthenticatedRequest, res: Response) => {
    const requestId = req.headers['x-request-id'] as string;

    try {
      const userId = req.user!.id;
      const limit = parseInt(req.query.limit as string) || 50;
      const status = req.query.status as string;

      const signals = await databaseService.getUserTradingSignals(userId, limit);

      // Filter by status if provided
      const filteredSignals = status
        ? signals.filter(signal => signal.status === status)
        : signals;

      const response: ApiResponse = {
        success: true,
        data: filteredSignals,
        timestamp: new Date(),
        request_id: requestId
      };

      res.json(response);

    } catch (error) {
      const errorResult = await handleError(error as Error, {
        operation: 'get_trading_signals',
        userId: req.user?.id,
        requestId
      });

      const response: ApiResponse = {
        success: false,
        error: errorResult.classification.userMessage,
        timestamp: new Date(),
        request_id: requestId
      };

      res.status(500).json(response);
    }
  });

  /**
   * Create new trading signal
   * POST /api/v1/trading/signals
   */
  router.post('/signals', [
    security.authenticate,
    security.requirePro, // Pro tier required for signal creation
    security.strictRateLimiter,
    security.validateInput(createSignalSchema)
  ], async (req: AuthenticatedRequest, res: Response) => {
    const requestId = req.headers['x-request-id'] as string;

    try {
      const userId = req.user!.id;
      const {
        symbol,
        type,
        entry_price,
        stop_loss,
        take_profit,
        volume,
        confidence,
        reasoning,
        expires_in_minutes
      } = req.body;

      // Validate trading parameters
      if (stop_loss && type === 'buy' && stop_loss >= entry_price) {
        return res.status(400).json({
          success: false,
          error: 'Stop loss must be below entry price for buy orders',
          timestamp: new Date(),
          request_id: requestId
        });
      }

      if (stop_loss && type === 'sell' && stop_loss <= entry_price) {
        return res.status(400).json({
          success: false,
          error: 'Stop loss must be above entry price for sell orders',
          timestamp: new Date(),
          request_id: requestId
        });
      }

      const signalId = uuidv4();
      const expiresAt = new Date(Date.now() + expires_in_minutes * 60 * 1000);

      const signal: TradingSignal = {
        id: signalId,
        user_id: userId,
        symbol,
        type,
        entry_price,
        stop_loss,
        take_profit,
        volume,
        confidence,
        reasoning,
        status: 'pending',
        expires_at: expiresAt,
        created_at: new Date()
      };

      await databaseService.createTradingSignal(signal);

      // Log trading signal creation
      logTrading('signal_created', userId, {
        signal_id: signalId,
        symbol,
        type,
        entry_price,
        volume,
        confidence
      });

      const response: ApiResponse = {
        success: true,
        data: signal,
        message: 'Trading signal created successfully',
        timestamp: new Date(),
        request_id: requestId
      };

      res.status(201).json(response);

    } catch (error) {
      const errorResult = await handleError(error as Error, {
        operation: 'create_trading_signal',
        userId: req.user?.id,
        requestId
      });

      const response: ApiResponse = {
        success: false,
        error: errorResult.classification.userMessage,
        timestamp: new Date(),
        request_id: requestId
      };

      res.status(500).json(response);
    }
  });

  /**
   * Execute trading signal
   * POST /api/v1/trading/signals/execute
   */
  router.post('/signals/execute', [
    security.authenticate,
    security.requireBasic,
    security.strictRateLimiter,
    security.validateInput(executeSignalSchema)
  ], async (req: AuthenticatedRequest, res: Response) => {
    const requestId = req.headers['x-request-id'] as string;

    try {
      const userId = req.user!.id;
      const { signal_id, mt5_account_id } = req.body;

      // Get signal and validate ownership
      const signals = await databaseService.getUserTradingSignals(userId, 1000);
      const signal = signals.find(s => s.id === signal_id);

      if (!signal) {
        return res.status(404).json({
          success: false,
          error: 'Trading signal not found',
          timestamp: new Date(),
          request_id: requestId
        });
      }

      if (signal.status !== 'pending') {
        return res.status(400).json({
          success: false,
          error: 'Signal has already been executed or expired',
          timestamp: new Date(),
          request_id: requestId
        });
      }

      if (signal.expires_at < new Date()) {
        return res.status(400).json({
          success: false,
          error: 'Trading signal has expired',
          timestamp: new Date(),
          request_id: requestId
        });
      }

      // Get MT5 connection
      const mt5Connection = await mt5ConnectionManager.getConnection(userId);

      // Execute trade
      const tradeResponse = await mt5Connection.executeTradingSignal(signal);

      if (!tradeResponse.success) {
        logTrading('signal_execution_failed', userId, {
          signal_id,
          mt5_account_id,
          error: tradeResponse.error,
          retcode: tradeResponse.retcode
        });

        return res.status(400).json({
          success: false,
          error: tradeResponse.error || 'Trade execution failed',
          timestamp: new Date(),
          request_id: requestId
        });
      }

      // Update signal status
      signal.status = 'executed';
      signal.executed_at = new Date();

      // Log successful execution
      logTrading('signal_executed', userId, {
        signal_id,
        mt5_account_id,
        ticket: tradeResponse.ticket,
        volume: tradeResponse.volume,
        price: tradeResponse.price
      });

      const response: ApiResponse = {
        success: true,
        data: {
          signal,
          execution_result: {
            ticket: tradeResponse.ticket,
            price: tradeResponse.price,
            volume: tradeResponse.volume,
            comment: tradeResponse.comment
          }
        },
        message: 'Trading signal executed successfully',
        timestamp: new Date(),
        request_id: requestId
      };

      res.json(response);

    } catch (error) {
      const errorResult = await handleError(error as Error, {
        operation: 'execute_trading_signal',
        userId: req.user?.id,
        requestId
      });

      // Log execution failure
      logTrading('signal_execution_error', req.user!.id, {
        signal_id: req.body.signal_id,
        error: errorResult.classification.technicalMessage
      });

      const response: ApiResponse = {
        success: false,
        error: errorResult.classification.userMessage,
        timestamp: new Date(),
        request_id: requestId
      };

      res.status(500).json(response);
    }
  });

  /**
   * Get MT5 accounts
   * GET /api/v1/trading/mt5-accounts
   */
  router.get('/mt5-accounts', [
    security.authenticate,
    security.requireBasic,
    security.rateLimiter
  ], async (req: AuthenticatedRequest, res: Response) => {
    const requestId = req.headers['x-request-id'] as string;

    try {
      const userId = req.user!.id;
      const accounts = await databaseService.getUserMT5Accounts(userId);

      const response: ApiResponse = {
        success: true,
        data: accounts,
        timestamp: new Date(),
        request_id: requestId
      };

      res.json(response);

    } catch (error) {
      const errorResult = await handleError(error as Error, {
        operation: 'get_mt5_accounts',
        userId: req.user?.id,
        requestId
      });

      const response: ApiResponse = {
        success: false,
        error: errorResult.classification.userMessage,
        timestamp: new Date(),
        request_id: requestId
      };

      res.status(500).json(response);
    }
  });

  /**
   * Add MT5 account
   * POST /api/v1/trading/mt5-accounts
   */
  router.post('/mt5-accounts', [
    security.authenticate,
    security.requireBasic,
    security.rateLimiter,
    security.validateInput(addMT5AccountSchema)
  ], async (req: AuthenticatedRequest, res: Response) => {
    const requestId = req.headers['x-request-id'] as string;

    try {
      const userId = req.user!.id;
      const { login, server, name } = req.body;

      // Create MT5 account record
      const accountId = uuidv4();
      const mt5Account = {
        id: accountId,
        user_id: userId,
        login,
        server,
        name,
        balance: 0,
        equity: 0,
        margin: 0,
        free_margin: 0,
        margin_level: 0,
        is_active: true,
        last_sync: new Date(),
        created_at: new Date(),
        updated_at: new Date()
      };

      await databaseService.createMT5Account(mt5Account);

      // Test connection to MT5
      try {
        const mt5Connection = await mt5ConnectionManager.getConnection(userId);
        const accountInfo = await mt5Connection.getAccountInfo();

        // Update account with real data
        mt5Account.balance = accountInfo.balance;
        mt5Account.equity = accountInfo.equity;
        mt5Account.margin = accountInfo.margin;
        mt5Account.free_margin = accountInfo.freeMargin;
        mt5Account.margin_level = accountInfo.marginLevel;
        mt5Account.last_sync = new Date();

      } catch (connectionError) {
        logger.warn('MT5 connection test failed during account creation', {
          user_id: userId,
          account_id: accountId,
          error: connectionError instanceof Error ? connectionError.message : 'Unknown error'
        });
      }

      logTrading('mt5_account_added', userId, {
        account_id: accountId,
        login,
        server,
        name
      });

      const response: ApiResponse = {
        success: true,
        data: mt5Account,
        message: 'MT5 account added successfully',
        timestamp: new Date(),
        request_id: requestId
      };

      res.status(201).json(response);

    } catch (error) {
      const errorResult = await handleError(error as Error, {
        operation: 'add_mt5_account',
        userId: req.user?.id,
        requestId
      });

      const response: ApiResponse = {
        success: false,
        error: errorResult.classification.userMessage,
        timestamp: new Date(),
        request_id: requestId
      };

      res.status(500).json(response);
    }
  });

  /**
   * Get MT5 account status and connection health
   * GET /api/v1/trading/mt5-accounts/:accountId/status
   */
  router.get('/mt5-accounts/:accountId/status', [
    security.authenticate,
    security.requireBasic,
    security.rateLimiter,
    security.authorizeResource('userId')
  ], async (req: AuthenticatedRequest, res: Response) => {
    const requestId = req.headers['x-request-id'] as string;

    try {
      const userId = req.user!.id;
      const accountId = req.params.accountId;

      // Verify account ownership
      const accounts = await databaseService.getUserMT5Accounts(userId);
      const account = accounts.find(acc => acc.id === accountId);

      if (!account) {
        return res.status(404).json({
          success: false,
          error: 'MT5 account not found',
          timestamp: new Date(),
          request_id: requestId
        });
      }

      // Get connection status
      try {
        const mt5Connection = await mt5ConnectionManager.getConnection(userId);
        const connectionStats = mt5Connection.getConnectionStats();
        const accountInfo = await mt5Connection.getAccountInfo();

        const response: ApiResponse = {
          success: true,
          data: {
            account: {
              ...account,
              balance: accountInfo.balance,
              equity: accountInfo.equity,
              margin: accountInfo.margin,
              free_margin: accountInfo.freeMargin,
              margin_level: accountInfo.marginLevel,
              last_sync: new Date()
            },
            connection: {
              is_connected: connectionStats.isConnected,
              average_latency: connectionStats.averageLatency,
              message_queue_size: connectionStats.messageQueueSize,
              reconnect_attempts: connectionStats.reconnectAttempts
            }
          },
          timestamp: new Date(),
          request_id: requestId
        };

        res.json(response);

      } catch (connectionError) {
        // Return account info without live data
        const response: ApiResponse = {
          success: true,
          data: {
            account,
            connection: {
              is_connected: false,
              error: 'Connection unavailable'
            }
          },
          message: 'Account found but MT5 connection unavailable',
          timestamp: new Date(),
          request_id: requestId
        };

        res.json(response);
      }

    } catch (error) {
      const errorResult = await handleError(error as Error, {
        operation: 'get_mt5_account_status',
        userId: req.user?.id,
        requestId
      });

      const response: ApiResponse = {
        success: false,
        error: errorResult.classification.userMessage,
        timestamp: new Date(),
        request_id: requestId
      };

      res.status(500).json(response);
    }
  });

  /**
   * Get trading performance metrics
   * GET /api/v1/trading/performance
   */
  router.get('/performance', [
    security.authenticate,
    security.requirePro, // Pro tier required for performance analytics
    security.rateLimiter
  ], async (req: AuthenticatedRequest, res: Response) => {
    const requestId = req.headers['x-request-id'] as string;

    try {
      const userId = req.user!.id;
      const days = parseInt(req.query.days as string) || 30;

      // Get trading signals from last N days
      const signals = await databaseService.getUserTradingSignals(userId, 1000);
      const recentSignals = signals.filter(signal =>
        signal.created_at >= new Date(Date.now() - days * 24 * 60 * 60 * 1000)
      );

      // Calculate performance metrics
      const totalSignals = recentSignals.length;
      const executedSignals = recentSignals.filter(s => s.status === 'executed').length;
      const expiredSignals = recentSignals.filter(s => s.status === 'expired').length;
      const pendingSignals = recentSignals.filter(s => s.status === 'pending').length;

      const executionRate = totalSignals > 0 ? (executedSignals / totalSignals) * 100 : 0;
      const averageConfidence = recentSignals.length > 0
        ? recentSignals.reduce((sum, signal) => sum + signal.confidence, 0) / recentSignals.length
        : 0;

      const response: ApiResponse = {
        success: true,
        data: {
          period_days: days,
          total_signals: totalSignals,
          executed_signals: executedSignals,
          expired_signals: expiredSignals,
          pending_signals: pendingSignals,
          execution_rate: Math.round(executionRate * 100) / 100,
          average_confidence: Math.round(averageConfidence * 100) / 100,
          signals_by_symbol: this.groupSignalsBySymbol(recentSignals),
          signals_by_type: this.groupSignalsByType(recentSignals)
        },
        timestamp: new Date(),
        request_id: requestId
      };

      res.json(response);

    } catch (error) {
      const errorResult = await handleError(error as Error, {
        operation: 'get_trading_performance',
        userId: req.user?.id,
        requestId
      });

      const response: ApiResponse = {
        success: false,
        error: errorResult.classification.userMessage,
        timestamp: new Date(),
        request_id: requestId
      };

      res.status(500).json(response);
    }
  });

  // Helper methods for performance analytics
  router.groupSignalsBySymbol = (signals: TradingSignal[]) => {
    return signals.reduce((acc, signal) => {
      acc[signal.symbol] = (acc[signal.symbol] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  };

  router.groupSignalsByType = (signals: TradingSignal[]) => {
    return signals.reduce((acc, signal) => {
      acc[signal.type] = (acc[signal.type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  };

  return router;
};

export default router;