const Payment = require('../models/Payment');
const logger = require('../config/logger');
const cron = require('node-cron');
const moment = require('moment-timezone');

class SubscriptionService {
  constructor() {
    this.timezone = 'Asia/Jakarta';
    this.setupRecurringBilling();
  }

  /**
   * Create subscription payment
   * @param {Object} subscriptionData - Subscription details
   * @returns {Promise<Object>} Subscription result
   */
  async createSubscription(subscriptionData) {
    try {
      const {
        userId,
        planType,
        billingCycle,
        startDate = new Date(),
        customAmount = null
      } = subscriptionData;

      // Get plan details
      const planDetails = this.getPlanDetails(planType, billingCycle);
      const amount = customAmount || planDetails.amount;

      // Calculate billing dates
      const dates = this.calculateBillingDates(startDate, billingCycle);

      // Prepare subscription details
      const subscriptionDetails = {
        planType,
        billingCycle,
        startDate: dates.startDate,
        endDate: dates.endDate,
        isRecurring: true,
        nextBillingDate: dates.nextBillingDate
      };

      logger.info('📋 Creating subscription', {
        userId,
        planType,
        billingCycle,
        amount,
        nextBillingDate: dates.nextBillingDate
      });

      return {
        success: true,
        subscriptionDetails,
        amount,
        planDetails
      };

    } catch (error) {
      logger.error('❌ Failed to create subscription', {
        error: error.message,
        userId: subscriptionData.userId
      });

      throw error;
    }
  }

  /**
   * Activate subscription after successful payment
   * @param {Object} payment - Payment document
   * @returns {Promise<void>}
   */
  async activateSubscription(payment) {
    try {
      if (!payment.subscriptionId || !payment.subscriptionDetails.isRecurring) {
        return;
      }

      const { userId, subscriptionDetails, planId } = payment;

      // Update user subscription status via integration service
      const IntegrationService = require('./IntegrationService');
      await IntegrationService.activateUserSubscription({
        userId,
        subscriptionId: payment.subscriptionId,
        planType: subscriptionDetails.planType,
        billingCycle: subscriptionDetails.billingCycle,
        startDate: subscriptionDetails.startDate,
        endDate: subscriptionDetails.endDate,
        status: 'active'
      });

      // Schedule next billing
      await this.scheduleNextBilling(payment);

      logger.info('✅ Subscription activated', {
        userId,
        subscriptionId: payment.subscriptionId,
        planType: subscriptionDetails.planType,
        nextBilling: subscriptionDetails.nextBillingDate
      });

    } catch (error) {
      logger.error('❌ Failed to activate subscription', {
        error: error.message,
        orderId: payment.orderId
      });

      throw error;
    }
  }

  /**
   * Process recurring billing
   * @returns {Promise<void>}
   */
  async processRecurringBilling() {
    try {
      logger.info('🔄 Processing recurring billing...');

      // Find subscriptions due for billing
      const dueSubscriptions = await Payment.findPendingSubscriptions();

      logger.info(`📋 Found ${dueSubscriptions.length} subscriptions due for billing`);

      for (const subscription of dueSubscriptions) {
        try {
          await this.processSubscriptionRenewal(subscription);
        } catch (error) {
          logger.error('❌ Failed to process subscription renewal', {
            error: error.message,
            subscriptionId: subscription.subscriptionId,
            userId: subscription.userId
          });

          // Mark subscription for manual review
          await this.markSubscriptionForReview(subscription, error.message);
        }
      }

      logger.info('✅ Recurring billing processing completed');

    } catch (error) {
      logger.error('❌ Failed to process recurring billing', {
        error: error.message
      });
    }
  }

  /**
   * Process individual subscription renewal
   * @param {Object} subscription - Subscription payment record
   * @returns {Promise<void>}
   */
  async processSubscriptionRenewal(subscription) {
    try {
      const { userId, subscriptionDetails, amount, currency, customerDetails, planId } = subscription;

      // Check if user subscription is still active
      const IntegrationService = require('./IntegrationService');
      const userSubscription = await IntegrationService.getUserSubscription(userId, subscription.subscriptionId);

      if (!userSubscription.isActive) {
        logger.warn('⚠️ Skipping renewal for inactive subscription', {
          userId,
          subscriptionId: subscription.subscriptionId
        });
        return;
      }

      // Create renewal payment
      const PaymentService = require('./PaymentService');
      const renewalResult = await PaymentService.createPayment({
        userId,
        amount,
        currency,
        paymentType: subscription.paymentType || 'credit_card',
        customerDetails,
        itemDetails: this.generateRenewalItemDetails(subscriptionDetails, amount),
        subscriptionId: subscription.subscriptionId,
        planId,
        metadata: {
          isRenewal: true,
          originalOrderId: subscription.orderId,
          billingCycle: subscriptionDetails.billingCycle
        }
      });

      // Update next billing date
      const nextBillingDate = this.calculateNextBillingDate(
        subscriptionDetails.nextBillingDate,
        subscriptionDetails.billingCycle
      );

      subscription.subscriptionDetails.nextBillingDate = nextBillingDate;
      await subscription.save();

      logger.info('🔄 Subscription renewal processed', {
        userId,
        subscriptionId: subscription.subscriptionId,
        renewalOrderId: renewalResult.data.orderId,
        nextBillingDate
      });

    } catch (error) {
      logger.error('❌ Failed to process subscription renewal', {
        error: error.message,
        subscriptionId: subscription.subscriptionId
      });

      throw error;
    }
  }

  /**
   * Cancel subscription
   * @param {string} userId - User ID
   * @param {string} subscriptionId - Subscription ID
   * @param {string} reason - Cancellation reason
   * @returns {Promise<Object>} Cancellation result
   */
  async cancelSubscription(userId, subscriptionId, reason = 'User cancellation') {
    try {
      // Find active subscription payments
      const subscriptions = await Payment.find({
        userId,
        subscriptionId,
        'subscriptionDetails.isRecurring': true,
        status: { $in: ['settlement', 'capture'] }
      }).sort({ createdAt: -1 });

      if (subscriptions.length === 0) {
        throw new Error('No active subscription found');
      }

      // Update subscription status
      for (const subscription of subscriptions) {
        subscription.subscriptionDetails.isRecurring = false;
        subscription.metadata.cancellationReason = reason;
        subscription.metadata.cancelledAt = new Date();
        await subscription.save();
      }

      // Update user subscription status via integration service
      const IntegrationService = require('./IntegrationService');
      await IntegrationService.cancelUserSubscription(userId, subscriptionId, reason);

      logger.info('🚫 Subscription cancelled', {
        userId,
        subscriptionId,
        reason
      });

      return {
        success: true,
        message: 'Subscription cancelled successfully',
        cancelledAt: new Date()
      };

    } catch (error) {
      logger.error('❌ Failed to cancel subscription', {
        error: error.message,
        userId,
        subscriptionId
      });

      throw error;
    }
  }

  /**
   * Handle subscription refund
   * @param {Object} payment - Payment document
   * @returns {Promise<void>}
   */
  async handleRefund(payment) {
    try {
      if (!payment.subscriptionId) {
        return;
      }

      // Calculate refund amount based on remaining subscription time
      const refundDetails = this.calculateProRatedRefund(payment);

      // Update user subscription status
      const IntegrationService = require('./IntegrationService');
      await IntegrationService.handleSubscriptionRefund({
        userId: payment.userId,
        subscriptionId: payment.subscriptionId,
        refundAmount: payment.metadata.refundAmount,
        proRatedAmount: refundDetails.proRatedAmount,
        remainingDays: refundDetails.remainingDays
      });

      // Cancel recurring billing
      payment.subscriptionDetails.isRecurring = false;
      payment.metadata.refundProcessedAt = new Date();
      await payment.save();

      logger.info('💸 Subscription refund processed', {
        userId: payment.userId,
        subscriptionId: payment.subscriptionId,
        refundAmount: payment.metadata.refundAmount,
        proRatedAmount: refundDetails.proRatedAmount
      });

    } catch (error) {
      logger.error('❌ Failed to handle subscription refund', {
        error: error.message,
        orderId: payment.orderId
      });

      throw error;
    }
  }

  /**
   * Get user subscriptions
   * @param {string} userId - User ID
   * @returns {Promise<Array>} User subscriptions
   */
  async getUserSubscriptions(userId) {
    try {
      const subscriptions = await Payment.find({
        userId,
        subscriptionId: { $exists: true },
        'subscriptionDetails.isRecurring': true
      })
      .sort({ createdAt: -1 })
      .select('subscriptionId subscriptionDetails status createdAt paidAt amount currency planId');

      const formattedSubscriptions = subscriptions.map(sub => ({
        subscriptionId: sub.subscriptionId,
        planType: sub.subscriptionDetails.planType,
        billingCycle: sub.subscriptionDetails.billingCycle,
        status: sub.status,
        amount: sub.amount,
        currency: sub.currency,
        startDate: sub.subscriptionDetails.startDate,
        endDate: sub.subscriptionDetails.endDate,
        nextBillingDate: sub.subscriptionDetails.nextBillingDate,
        isActive: sub.subscriptionDetails.isRecurring && ['settlement', 'capture'].includes(sub.status),
        createdAt: sub.createdAt
      }));

      return formattedSubscriptions;

    } catch (error) {
      logger.error('❌ Failed to get user subscriptions', {
        error: error.message,
        userId
      });

      throw error;
    }
  }

  /**
   * Get plan details and pricing
   * @param {string} planType - Plan type
   * @param {string} billingCycle - Billing cycle
   * @returns {Object} Plan details
   */
  getPlanDetails(planType, billingCycle) {
    const plans = {
      basic: {
        name: 'Basic Trading Plan',
        features: ['Real-time market data', 'Basic analytics', 'Mobile app access'],
        limits: { trades: 100, watchlists: 5 },
        pricing: {
          monthly: 99000,   // IDR 99,000
          quarterly: 267300, // IDR 267,300 (10% discount)
          yearly: 950400    // IDR 950,400 (20% discount)
        }
      },
      premium: {
        name: 'Premium Trading Plan',
        features: ['Advanced analytics', 'AI signals', 'Portfolio management', 'Priority support'],
        limits: { trades: 500, watchlists: 20 },
        pricing: {
          monthly: 199000,   // IDR 199,000
          quarterly: 537300, // IDR 537,300 (10% discount)
          yearly: 1910400   // IDR 1,910,400 (20% discount)
        }
      },
      professional: {
        name: 'Professional Trading Plan',
        features: ['All premium features', 'Advanced algorithms', 'Custom indicators', 'API access'],
        limits: { trades: 2000, watchlists: 50 },
        pricing: {
          monthly: 399000,   // IDR 399,000
          quarterly: 1077300, // IDR 1,077,300 (10% discount)
          yearly: 3830400   // IDR 3,830,400 (20% discount)
        }
      },
      enterprise: {
        name: 'Enterprise Trading Plan',
        features: ['All professional features', 'Dedicated support', 'Custom integrations', 'White-label'],
        limits: { trades: 'unlimited', watchlists: 'unlimited' },
        pricing: {
          monthly: 999000,   // IDR 999,000
          quarterly: 2697300, // IDR 2,697,300 (10% discount)
          yearly: 9590400   // IDR 9,590,400 (20% discount)
        }
      }
    };

    const plan = plans[planType];
    if (!plan) {
      throw new Error(`Invalid plan type: ${planType}`);
    }

    const amount = plan.pricing[billingCycle];
    if (!amount) {
      throw new Error(`Invalid billing cycle: ${billingCycle}`);
    }

    return {
      ...plan,
      amount,
      planType,
      billingCycle
    };
  }

  /**
   * Calculate billing dates
   * @param {Date} startDate - Subscription start date
   * @param {string} billingCycle - Billing cycle
   * @returns {Object} Billing dates
   */
  calculateBillingDates(startDate, billingCycle) {
    const start = moment.tz(startDate, this.timezone);
    let end, nextBilling;

    switch (billingCycle) {
      case 'monthly':
        end = start.clone().add(1, 'month');
        nextBilling = start.clone().add(1, 'month');
        break;
      case 'quarterly':
        end = start.clone().add(3, 'months');
        nextBilling = start.clone().add(3, 'months');
        break;
      case 'yearly':
        end = start.clone().add(1, 'year');
        nextBilling = start.clone().add(1, 'year');
        break;
      default:
        throw new Error(`Invalid billing cycle: ${billingCycle}`);
    }

    return {
      startDate: start.toDate(),
      endDate: end.toDate(),
      nextBillingDate: nextBilling.toDate()
    };
  }

  /**
   * Calculate next billing date
   * @param {Date} currentBillingDate - Current billing date
   * @param {string} billingCycle - Billing cycle
   * @returns {Date} Next billing date
   */
  calculateNextBillingDate(currentBillingDate, billingCycle) {
    const current = moment.tz(currentBillingDate, this.timezone);

    switch (billingCycle) {
      case 'monthly':
        return current.add(1, 'month').toDate();
      case 'quarterly':
        return current.add(3, 'months').toDate();
      case 'yearly':
        return current.add(1, 'year').toDate();
      default:
        throw new Error(`Invalid billing cycle: ${billingCycle}`);
    }
  }

  /**
   * Calculate pro-rated refund amount
   * @param {Object} payment - Payment document
   * @returns {Object} Refund details
   */
  calculateProRatedRefund(payment) {
    const { subscriptionDetails, amount, paidAt } = payment;
    const now = moment.tz(this.timezone);
    const paidDate = moment.tz(paidAt, this.timezone);
    const endDate = moment.tz(subscriptionDetails.endDate, this.timezone);

    const totalDays = endDate.diff(paidDate, 'days');
    const usedDays = now.diff(paidDate, 'days');
    const remainingDays = Math.max(0, totalDays - usedDays);

    const proRatedAmount = Math.round((remainingDays / totalDays) * amount);

    return {
      totalDays,
      usedDays,
      remainingDays,
      proRatedAmount,
      originalAmount: amount
    };
  }

  /**
   * Generate renewal item details
   * @param {Object} subscriptionDetails - Subscription details
   * @param {number} amount - Amount
   * @returns {Array} Item details
   */
  generateRenewalItemDetails(subscriptionDetails, amount) {
    const { planType, billingCycle } = subscriptionDetails;

    return [{
      id: `renewal_${planType}_${billingCycle}`,
      price: amount,
      quantity: 1,
      name: `Trading Platform - ${planType.toUpperCase()} Plan Renewal (${billingCycle})`,
      brand: 'Neliti Trading',
      category: 'Subscription Renewal',
      merchantName: 'Neliti AI Trading Platform'
    }];
  }

  /**
   * Schedule next billing for subscription
   * @param {Object} payment - Payment document
   * @returns {Promise<void>}
   */
  async scheduleNextBilling(payment) {
    try {
      const nextBillingDate = this.calculateNextBillingDate(
        payment.subscriptionDetails.nextBillingDate,
        payment.subscriptionDetails.billingCycle
      );

      payment.subscriptionDetails.nextBillingDate = nextBillingDate;
      await payment.save();

      logger.info('📅 Next billing scheduled', {
        subscriptionId: payment.subscriptionId,
        nextBillingDate
      });

    } catch (error) {
      logger.error('❌ Failed to schedule next billing', {
        error: error.message,
        subscriptionId: payment.subscriptionId
      });
    }
  }

  /**
   * Mark subscription for manual review
   * @param {Object} subscription - Subscription document
   * @param {string} reason - Review reason
   * @returns {Promise<void>}
   */
  async markSubscriptionForReview(subscription, reason) {
    try {
      subscription.metadata.requiresReview = true;
      subscription.metadata.reviewReason = reason;
      subscription.metadata.reviewRequestedAt = new Date();
      await subscription.save();

      // Notify integration service for manual review
      const IntegrationService = require('./IntegrationService');
      await IntegrationService.notifySubscriptionReview(subscription, reason);

      logger.warn('⚠️ Subscription marked for review', {
        subscriptionId: subscription.subscriptionId,
        reason
      });

    } catch (error) {
      logger.error('❌ Failed to mark subscription for review', {
        error: error.message,
        subscriptionId: subscription.subscriptionId
      });
    }
  }

  /**
   * Setup recurring billing cron job
   * @private
   */
  setupRecurringBilling() {
    // Run every day at 9:00 AM Jakarta time
    cron.schedule('0 9 * * *', async () => {
      logger.info('⏰ Starting scheduled recurring billing process');
      await this.processRecurringBilling();
    }, {
      timezone: this.timezone
    });

    // Run every hour for failed retries
    cron.schedule('0 * * * *', async () => {
      await this.retryFailedSubscriptions();
    }, {
      timezone: this.timezone
    });

    logger.info('✅ Recurring billing cron jobs scheduled');
  }

  /**
   * Retry failed subscription renewals
   * @returns {Promise<void>}
   */
  async retryFailedSubscriptions() {
    try {
      const failedSubscriptions = await Payment.find({
        'subscriptionDetails.isRecurring': true,
        'metadata.requiresReview': { $ne: true },
        retryCount: { $lt: 3 },
        status: { $in: ['failure', 'deny'] },
        'subscriptionDetails.nextBillingDate': { $lte: new Date() }
      });

      for (const subscription of failedSubscriptions) {
        subscription.retryCount = (subscription.retryCount || 0) + 1;
        await subscription.save();

        try {
          await this.processSubscriptionRenewal(subscription);
        } catch (error) {
          if (subscription.retryCount >= 3) {
            await this.markSubscriptionForReview(subscription, 'Max retries exceeded');
          }
        }
      }

    } catch (error) {
      logger.error('❌ Failed to retry failed subscriptions', {
        error: error.message
      });
    }
  }
}

module.exports = new SubscriptionService();