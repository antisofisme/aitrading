const PaymentService = require('../services/PaymentService');
const SubscriptionService = require('../services/SubscriptionService');
const logger = require('../config/logger');
const { validationResult } = require('express-validator');

class PaymentController {
  /**
   * Create new payment
   * @param {Object} req - Express request
   * @param {Object} res - Express response
   */
  async createPayment(req, res) {
    try {
      // Validate request
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({
          success: false,
          message: 'Validation failed',
          errors: errors.array()
        });
      }

      const {
        amount,
        currency = 'IDR',
        paymentType = 'credit_card',
        paymentMethods = [],
        customerDetails,
        itemDetails,
        subscriptionId,
        planId,
        metadata = {}
      } = req.body;

      const userId = req.user?.id || req.headers['x-user-id'];
      if (!userId) {
        return res.status(401).json({
          success: false,
          message: 'User authentication required'
        });
      }

      // Handle subscription payments
      let subscriptionDetails = null;
      if (planId && !subscriptionId) {
        const subscriptionData = {
          userId,
          planType: planId,
          billingCycle: metadata.billingCycle || 'monthly',
          startDate: metadata.startDate
        };

        const subscriptionResult = await SubscriptionService.createSubscription(subscriptionData);
        if (subscriptionResult.success) {
          subscriptionDetails = subscriptionResult.subscriptionDetails;
          metadata.subscriptionId = subscriptionDetails.subscriptionId;
        }
      }

      // Create payment
      const paymentData = {
        userId,
        amount,
        currency,
        paymentType,
        paymentMethods,
        customerDetails,
        itemDetails,
        subscriptionId: subscriptionId || metadata.subscriptionId,
        planId,
        metadata: {
          ...metadata,
          ipAddress: req.ip,
          userAgent: req.get('User-Agent'),
          subscriptionDetails
        }
      };

      const result = await PaymentService.createPayment(paymentData);

      logger.info('✅ Payment created via API', {
        orderId: result.data.orderId,
        userId,
        amount: result.data.grossAmount
      });

      res.status(201).json({
        success: true,
        message: 'Payment created successfully',
        data: result.data
      });

    } catch (error) {
      logger.error('❌ Payment creation failed', {
        error: error.message,
        userId: req.user?.id,
        body: req.body
      });

      res.status(500).json({
        success: false,
        message: error.message || 'Failed to create payment'
      });
    }
  }

  /**
   * Get payment details
   * @param {Object} req - Express request
   * @param {Object} res - Express response
   */
  async getPayment(req, res) {
    try {
      const { orderId } = req.params;
      const userId = req.user?.id || req.headers['x-user-id'];

      const payment = await PaymentService.getPayment(orderId, userId);

      // Remove sensitive data
      const sanitizedPayment = {
        orderId: payment.orderId,
        transactionId: payment.transactionId,
        userId: payment.userId,
        amount: payment.amount,
        grossAmount: payment.grossAmount,
        tax: payment.tax,
        currency: payment.currency,
        status: payment.status,
        fraudStatus: payment.fraudStatus,
        paymentType: payment.paymentType,
        paymentMethod: payment.paymentMethod,
        customerDetails: {
          firstName: payment.customerDetails.firstName,
          lastName: payment.customerDetails.lastName,
          email: payment.customerDetails.email
        },
        itemDetails: payment.itemDetails,
        subscriptionDetails: payment.subscriptionDetails,
        displayAmount: payment.displayAmount,
        createdAt: payment.createdAt,
        updatedAt: payment.updatedAt,
        paidAt: payment.paidAt,
        expiredAt: payment.expiredAt,
        isExpired: payment.isExpired()
      };

      res.json({
        success: true,
        data: sanitizedPayment
      });

    } catch (error) {
      logger.error('❌ Failed to get payment', {
        error: error.message,
        orderId: req.params.orderId,
        userId: req.user?.id
      });

      const statusCode = error.message.includes('not found') ? 404 :
                        error.message.includes('Unauthorized') ? 403 : 500;

      res.status(statusCode).json({
        success: false,
        message: error.message
      });
    }
  }

  /**
   * Get user payment history
   * @param {Object} req - Express request
   * @param {Object} res - Express response
   */
  async getUserPayments(req, res) {
    try {
      const userId = req.user?.id || req.headers['x-user-id'];
      if (!userId) {
        return res.status(401).json({
          success: false,
          message: 'User authentication required'
        });
      }

      const {
        page = 1,
        limit = 20,
        status,
        dateFrom,
        dateTo,
        paymentType
      } = req.query;

      const options = {
        page: parseInt(page),
        limit: Math.min(parseInt(limit), 100), // Max 100 per page
        status,
        dateFrom,
        dateTo,
        paymentType
      };

      const result = await PaymentService.getUserPayments(userId, options);

      res.json({
        success: true,
        data: result.payments,
        pagination: result.pagination
      });

    } catch (error) {
      logger.error('❌ Failed to get user payments', {
        error: error.message,
        userId: req.user?.id
      });

      res.status(500).json({
        success: false,
        message: error.message
      });
    }
  }

  /**
   * Cancel payment
   * @param {Object} req - Express request
   * @param {Object} res - Express response
   */
  async cancelPayment(req, res) {
    try {
      const { orderId } = req.params;
      const { reason = 'User cancellation' } = req.body;
      const userId = req.user?.id || req.headers['x-user-id'];

      if (!userId) {
        return res.status(401).json({
          success: false,
          message: 'User authentication required'
        });
      }

      const result = await PaymentService.cancelPayment(orderId, userId, reason);

      logger.info('🚫 Payment cancelled via API', {
        orderId,
        userId,
        reason
      });

      res.json({
        success: true,
        message: result.message
      });

    } catch (error) {
      logger.error('❌ Payment cancellation failed', {
        error: error.message,
        orderId: req.params.orderId,
        userId: req.user?.id
      });

      const statusCode = error.message.includes('not found') ? 404 :
                        error.message.includes('cannot be cancelled') ? 400 : 500;

      res.status(statusCode).json({
        success: false,
        message: error.message
      });
    }
  }

  /**
   * Check payment status
   * @param {Object} req - Express request
   * @param {Object} res - Express response
   */
  async checkPaymentStatus(req, res) {
    try {
      const { orderId } = req.params;

      const status = await PaymentService.checkPaymentStatus(orderId);

      res.json({
        success: true,
        data: status
      });

    } catch (error) {
      logger.error('❌ Failed to check payment status', {
        error: error.message,
        orderId: req.params.orderId
      });

      const statusCode = error.message.includes('not found') ? 404 : 500;

      res.status(statusCode).json({
        success: false,
        message: error.message
      });
    }
  }

  /**
   * Process webhook notification
   * @param {Object} req - Express request
   * @param {Object} res - Express response
   */
  async processWebhook(req, res) {
    try {
      const notification = req.body;
      const signature = req.headers['x-midtrans-signature'] || req.headers['signature'];

      logger.info('📢 Webhook received', {
        orderId: notification.order_id,
        status: notification.transaction_status,
        fraudStatus: notification.fraud_status
      });

      const result = await PaymentService.processWebhook(notification, signature);

      res.json({
        success: true,
        message: result.message
      });

    } catch (error) {
      logger.error('❌ Webhook processing failed', {
        error: error.message,
        orderId: req.body?.order_id
      });

      // Return 200 to prevent Midtrans from retrying invalid webhooks
      res.status(200).json({
        success: false,
        message: error.message
      });
    }
  }

  /**
   * Refund payment (admin only)
   * @param {Object} req - Express request
   * @param {Object} res - Express response
   */
  async refundPayment(req, res) {
    try {
      const { orderId } = req.params;
      const { amount, reason = 'Admin refund' } = req.body;

      // Check admin permissions
      if (!req.user?.isAdmin) {
        return res.status(403).json({
          success: false,
          message: 'Admin access required'
        });
      }

      const result = await PaymentService.refundPayment(orderId, amount, reason);

      logger.info('💸 Payment refunded via API', {
        orderId,
        amount: result.refundAmount,
        reason,
        adminId: req.user.id
      });

      res.json({
        success: true,
        message: result.message,
        refundAmount: result.refundAmount
      });

    } catch (error) {
      logger.error('❌ Payment refund failed', {
        error: error.message,
        orderId: req.params.orderId,
        adminId: req.user?.id
      });

      const statusCode = error.message.includes('not found') ? 404 :
                        error.message.includes('cannot be refunded') ? 400 : 500;

      res.status(statusCode).json({
        success: false,
        message: error.message
      });
    }
  }

  /**
   * Get payment statistics
   * @param {Object} req - Express request
   * @param {Object} res - Express response
   */
  async getPaymentStats(req, res) {
    try {
      const userId = req.user?.id || req.headers['x-user-id'];
      if (!userId) {
        return res.status(401).json({
          success: false,
          message: 'User authentication required'
        });
      }

      const { dateFrom, dateTo } = req.query;
      const dateRange = {};

      if (dateFrom) dateRange.start = new Date(dateFrom);
      if (dateTo) dateRange.end = new Date(dateTo);

      const Payment = require('../models/Payment');
      const stats = await Payment.getPaymentStats(userId, dateRange);

      // Calculate totals
      const summary = stats.reduce((acc, stat) => {
        acc.totalTransactions += stat.count;
        acc.totalAmount += stat.totalAmount;

        if (['settlement', 'capture'].includes(stat._id)) {
          acc.successfulTransactions += stat.count;
          acc.successfulAmount += stat.totalAmount;
        }

        acc.byStatus[stat._id] = {
          count: stat.count,
          amount: stat.totalAmount
        };

        return acc;
      }, {
        totalTransactions: 0,
        totalAmount: 0,
        successfulTransactions: 0,
        successfulAmount: 0,
        byStatus: {}
      });

      res.json({
        success: true,
        data: summary
      });

    } catch (error) {
      logger.error('❌ Failed to get payment stats', {
        error: error.message,
        userId: req.user?.id
      });

      res.status(500).json({
        success: false,
        message: error.message
      });
    }
  }

  /**
   * Get available payment methods
   * @param {Object} req - Express request
   * @param {Object} res - Express response
   */
  async getPaymentMethods(req, res) {
    try {
      const MidtransService = require('../services/MidtransService');
      const paymentMethods = MidtransService.getPaymentMethods();
      const defaultMethods = MidtransService.getDefaultPaymentMethods();

      const formattedMethods = {
        available: defaultMethods,
        configurations: {
          creditCard: {
            enabled: paymentMethods.credit_card.enabled,
            secure: paymentMethods.credit_card.secure,
            installmentBanks: Object.keys(paymentMethods.credit_card.installment.terms)
          },
          bankTransfer: {
            enabled: paymentMethods.bank_transfer.enabled,
            banks: paymentMethods.bank_transfer.bank
          },
          eWallets: {
            gopay: paymentMethods.gopay.enabled,
            ovo: paymentMethods.ovo.enabled,
            dana: paymentMethods.dana.enabled,
            linkaja: paymentMethods.linkaja.enabled,
            shopeepay: paymentMethods.shopeepay.enabled
          },
          convenienceStore: {
            enabled: paymentMethods.cstore.enabled,
            stores: ['indomaret', 'alfamart']
          }
        }
      };

      res.json({
        success: true,
        data: formattedMethods
      });

    } catch (error) {
      logger.error('❌ Failed to get payment methods', {
        error: error.message
      });

      res.status(500).json({
        success: false,
        message: error.message
      });
    }
  }

  /**
   * Health check endpoint
   * @param {Object} req - Express request
   * @param {Object} res - Express response
   */
  async healthCheck(req, res) {
    try {
      const dbConnection = require('../config/database');
      const redisConnection = require('../config/redis');
      const midtransConfig = require('../config/midtrans');

      const health = {
        status: 'healthy',
        timestamp: new Date().toISOString(),
        services: {
          database: dbConnection.getConnectionStatus(),
          redis: redisConnection.getConnectionStatus(),
          midtrans: midtransConfig.getEnvironment()
        }
      };

      // Check if any service is unhealthy
      const isUnhealthy = !health.services.database.isConnected ||
                         !health.services.redis.isConnected;

      if (isUnhealthy) {
        health.status = 'unhealthy';
        return res.status(503).json(health);
      }

      res.json(health);

    } catch (error) {
      logger.error('❌ Health check failed', {
        error: error.message
      });

      res.status(503).json({
        status: 'unhealthy',
        error: error.message,
        timestamp: new Date().toISOString()
      });
    }
  }
}

module.exports = new PaymentController();