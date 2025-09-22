const express = require('express');
const SubscriptionService = require('../services/SubscriptionService');
const security = require('../middleware/security');
const validation = require('../middleware/validation');
const logger = require('../config/logger');

const router = express.Router();

/**
 * Subscription Routes
 */

// Get subscription plans and pricing
router.get('/plans',
  security.apiRateLimit,
  async (req, res) => {
    try {
      const plans = {
        basic: SubscriptionService.getPlanDetails('basic', 'monthly'),
        premium: SubscriptionService.getPlanDetails('premium', 'monthly'),
        professional: SubscriptionService.getPlanDetails('professional', 'monthly'),
        enterprise: SubscriptionService.getPlanDetails('enterprise', 'monthly')
      };

      // Add pricing for all billing cycles
      Object.keys(plans).forEach(planType => {
        plans[planType].pricing = {
          monthly: SubscriptionService.getPlanDetails(planType, 'monthly').amount,
          quarterly: SubscriptionService.getPlanDetails(planType, 'quarterly').amount,
          yearly: SubscriptionService.getPlanDetails(planType, 'yearly').amount
        };
      });

      res.json({
        success: true,
        data: plans
      });

    } catch (error) {
      logger.error('❌ Failed to get subscription plans', {
        error: error.message
      });

      res.status(500).json({
        success: false,
        message: error.message
      });
    }
  }
);

// Get user subscriptions
router.get('/user/active',
  security.apiRateLimit,
  security.authenticateToken,
  async (req, res) => {
    try {
      const userId = req.user?.id || req.headers['x-user-id'];
      if (!userId) {
        return res.status(401).json({
          success: false,
          message: 'User authentication required'
        });
      }

      const subscriptions = await SubscriptionService.getUserSubscriptions(userId);

      res.json({
        success: true,
        data: subscriptions
      });

    } catch (error) {
      logger.error('❌ Failed to get user subscriptions', {
        error: error.message,
        userId: req.user?.id
      });

      res.status(500).json({
        success: false,
        message: error.message
      });
    }
  }
);

// Create subscription (returns payment data)
router.post('/create',
  security.paymentRateLimit,
  security.authenticateToken,
  validation.validateSubscription,
  async (req, res) => {
    try {
      const userId = req.user?.id || req.headers['x-user-id'];
      if (!userId) {
        return res.status(401).json({
          success: false,
          message: 'User authentication required'
        });
      }

      const {
        planType,
        billingCycle,
        startDate,
        customAmount
      } = req.body;

      const subscriptionData = {
        userId,
        planType,
        billingCycle,
        startDate: startDate ? new Date(startDate) : new Date(),
        customAmount
      };

      const result = await SubscriptionService.createSubscription(subscriptionData);

      logger.info('📋 Subscription created', {
        userId,
        planType,
        billingCycle,
        amount: result.amount
      });

      res.status(201).json({
        success: true,
        message: 'Subscription created successfully',
        data: {
          subscriptionDetails: result.subscriptionDetails,
          amount: result.amount,
          planDetails: result.planDetails,
          nextStep: 'Create payment using returned subscription details'
        }
      });

    } catch (error) {
      logger.error('❌ Failed to create subscription', {
        error: error.message,
        userId: req.user?.id
      });

      res.status(500).json({
        success: false,
        message: error.message
      });
    }
  }
);

// Cancel subscription
router.put('/:subscriptionId/cancel',
  security.paymentRateLimit,
  security.authenticateToken,
  validation.validateSubscriptionCancellation,
  async (req, res) => {
    try {
      const userId = req.user?.id || req.headers['x-user-id'];
      if (!userId) {
        return res.status(401).json({
          success: false,
          message: 'User authentication required'
        });
      }

      const { subscriptionId } = req.params;
      const { reason = 'User cancellation' } = req.body;

      const result = await SubscriptionService.cancelSubscription(userId, subscriptionId, reason);

      logger.info('🚫 Subscription cancelled', {
        userId,
        subscriptionId,
        reason
      });

      res.json({
        success: true,
        message: result.message,
        data: {
          cancelledAt: result.cancelledAt
        }
      });

    } catch (error) {
      logger.error('❌ Failed to cancel subscription', {
        error: error.message,
        userId: req.user?.id,
        subscriptionId: req.params.subscriptionId
      });

      const statusCode = error.message.includes('not found') ? 404 : 500;

      res.status(statusCode).json({
        success: false,
        message: error.message
      });
    }
  }
);

// Get subscription billing history
router.get('/:subscriptionId/billing-history',
  security.apiRateLimit,
  security.authenticateToken,
  validation.validateSubscriptionCancellation, // Reuse for subscriptionId validation
  validation.validatePagination,
  async (req, res) => {
    try {
      const userId = req.user?.id || req.headers['x-user-id'];
      if (!userId) {
        return res.status(401).json({
          success: false,
          message: 'User authentication required'
        });
      }

      const { subscriptionId } = req.params;
      const {
        page = 1,
        limit = 20
      } = req.query;

      const Payment = require('../models/Payment');

      const query = {
        userId,
        subscriptionId,
        status: { $in: ['settlement', 'capture', 'refund', 'partial_refund'] }
      };

      const skip = (page - 1) * limit;

      const [payments, total] = await Promise.all([
        Payment.find(query)
          .sort({ createdAt: -1 })
          .skip(skip)
          .limit(parseInt(limit))
          .select('orderId amount grossAmount currency status paidAt createdAt subscriptionDetails'),
        Payment.countDocuments(query)
      ]);

      const totalPages = Math.ceil(total / limit);

      const billingHistory = payments.map(payment => ({
        orderId: payment.orderId,
        amount: payment.amount,
        grossAmount: payment.grossAmount,
        currency: payment.currency,
        status: payment.status,
        planType: payment.subscriptionDetails?.planType,
        billingCycle: payment.subscriptionDetails?.billingCycle,
        paidAt: payment.paidAt,
        createdAt: payment.createdAt,
        displayAmount: payment.displayAmount
      }));

      res.json({
        success: true,
        data: billingHistory,
        pagination: {
          page: parseInt(page),
          limit: parseInt(limit),
          total,
          totalPages,
          hasNext: page < totalPages,
          hasPrev: page > 1
        }
      });

    } catch (error) {
      logger.error('❌ Failed to get subscription billing history', {
        error: error.message,
        userId: req.user?.id,
        subscriptionId: req.params.subscriptionId
      });

      res.status(500).json({
        success: false,
        message: error.message
      });
    }
  }
);

// Get upcoming billing dates
router.get('/user/upcoming-billing',
  security.apiRateLimit,
  security.authenticateToken,
  async (req, res) => {
    try {
      const userId = req.user?.id || req.headers['x-user-id'];
      if (!userId) {
        return res.status(401).json({
          success: false,
          message: 'User authentication required'
        });
      }

      const Payment = require('../models/Payment');

      const upcomingBilling = await Payment.find({
        userId,
        'subscriptionDetails.isRecurring': true,
        'subscriptionDetails.nextBillingDate': { $gte: new Date() },
        status: { $in: ['settlement', 'capture'] }
      })
      .sort({ 'subscriptionDetails.nextBillingDate': 1 })
      .select('subscriptionId subscriptionDetails amount currency planId')
      .limit(10);

      const formattedBilling = upcomingBilling.map(payment => ({
        subscriptionId: payment.subscriptionId,
        planType: payment.subscriptionDetails.planType,
        billingCycle: payment.subscriptionDetails.billingCycle,
        amount: payment.amount,
        currency: payment.currency,
        nextBillingDate: payment.subscriptionDetails.nextBillingDate,
        displayAmount: payment.displayAmount
      }));

      res.json({
        success: true,
        data: formattedBilling
      });

    } catch (error) {
      logger.error('❌ Failed to get upcoming billing', {
        error: error.message,
        userId: req.user?.id
      });

      res.status(500).json({
        success: false,
        message: error.message
      });
    }
  }
);

// Admin: Process recurring billing manually
router.post('/admin/process-recurring',
  security.paymentRateLimit,
  security.authenticateToken,
  security.requireAdmin,
  security.ipWhitelist,
  async (req, res) => {
    try {
      logger.info('🔄 Manual recurring billing triggered', {
        adminId: req.user.id
      });

      // Run recurring billing process
      await SubscriptionService.processRecurringBilling();

      res.json({
        success: true,
        message: 'Recurring billing process completed'
      });

    } catch (error) {
      logger.error('❌ Failed to process recurring billing', {
        error: error.message,
        adminId: req.user?.id
      });

      res.status(500).json({
        success: false,
        message: error.message
      });
    }
  }
);

// Admin: Get subscription statistics
router.get('/admin/stats',
  security.apiRateLimit,
  security.authenticateToken,
  security.requireAdmin,
  validation.validateDateRange,
  async (req, res) => {
    try {
      const { dateFrom, dateTo } = req.query;
      const Payment = require('../models/Payment');

      const matchQuery = {
        subscriptionId: { $exists: true }
      };

      if (dateFrom || dateTo) {
        matchQuery.createdAt = {};
        if (dateFrom) matchQuery.createdAt.$gte = new Date(dateFrom);
        if (dateTo) matchQuery.createdAt.$lte = new Date(dateTo);
      }

      const stats = await Payment.aggregate([
        { $match: matchQuery },
        {
          $group: {
            _id: {
              planType: '$subscriptionDetails.planType',
              billingCycle: '$subscriptionDetails.billingCycle',
              status: '$status'
            },
            count: { $sum: 1 },
            totalAmount: { $sum: '$amount' },
            avgAmount: { $avg: '$amount' }
          }
        },
        {
          $group: {
            _id: {
              planType: '$_id.planType',
              billingCycle: '$_id.billingCycle'
            },
            statuses: {
              $push: {
                status: '$_id.status',
                count: '$count',
                totalAmount: '$totalAmount'
              }
            },
            totalSubscriptions: { $sum: '$count' },
            totalRevenue: { $sum: '$totalAmount' }
          }
        }
      ]);

      res.json({
        success: true,
        data: stats
      });

    } catch (error) {
      logger.error('❌ Failed to get subscription stats', {
        error: error.message,
        adminId: req.user?.id
      });

      res.status(500).json({
        success: false,
        message: error.message
      });
    }
  }
);

module.exports = router;