const axios = require('axios');
const logger = require('../config/logger');
const redisConnection = require('../config/redis');

class IntegrationService {
  constructor() {
    this.services = {
      userManagement: process.env.USER_MANAGEMENT_URL || 'http://localhost:3001',
      subscriptionService: process.env.SUBSCRIPTION_SERVICE_URL || 'http://localhost:3002',
      billingService: process.env.BILLING_SERVICE_URL || 'http://localhost:3004',
      notificationService: process.env.NOTIFICATION_SERVICE_URL || 'http://localhost:3005'
    };

    this.timeout = 5000; // 5 seconds
    this.retryCount = 3;
  }

  /**
   * Validate user exists and get user details
   * @param {string} userId - User ID
   * @returns {Promise<Object>} User validation result
   */
  async validateUser(userId) {
    try {
      // Try cache first
      const cached = await this.getCachedUser(userId);
      if (cached) {
        return { isValid: true, user: cached };
      }

      const response = await this.makeRequest('GET', `${this.services.userManagement}/api/users/${userId}`);

      if (response.success && response.data) {
        // Cache user data for 30 minutes
        await this.cacheUser(userId, response.data);

        return {
          isValid: true,
          user: response.data
        };
      }

      return { isValid: false, user: null };

    } catch (error) {
      if (error.response?.status === 404) {
        return { isValid: false, user: null };
      }

      logger.error('❌ Failed to validate user', {
        error: error.message,
        userId
      });

      // Return cached data if available during service failure
      const cached = await this.getCachedUser(userId);
      if (cached) {
        return { isValid: true, user: cached };
      }

      throw error;
    }
  }

  /**
   * Notify payment created
   * @param {Object} payment - Payment document
   * @returns {Promise<void>}
   */
  async notifyPaymentCreated(payment) {
    try {
      const notifications = [
        // Update billing service
        this.makeRequest('POST', `${this.services.billingService}/api/billing/payment-created`, {
          orderId: payment.orderId,
          userId: payment.userId,
          amount: payment.grossAmount,
          currency: payment.currency,
          subscriptionId: payment.subscriptionId,
          planId: payment.planId,
          status: payment.status
        }),

        // Send notification
        this.makeRequest('POST', `${this.services.notificationService}/api/notifications/payment-created`, {
          userId: payment.userId,
          orderId: payment.orderId,
          amount: payment.grossAmount,
          currency: payment.currency,
          paymentType: payment.paymentType
        })
      ];

      await Promise.allSettled(notifications);

      logger.info('📢 Payment creation notifications sent', {
        orderId: payment.orderId
      });

    } catch (error) {
      logger.error('❌ Failed to send payment creation notifications', {
        error: error.message,
        orderId: payment.orderId
      });
      // Don't throw - notifications are not critical
    }
  }

  /**
   * Notify payment status changed
   * @param {Object} payment - Payment document
   * @param {string} oldStatus - Previous status
   * @returns {Promise<void>}
   */
  async notifyPaymentStatusChanged(payment, oldStatus) {
    try {
      const notifications = [
        // Update billing service
        this.makeRequest('PUT', `${this.services.billingService}/api/billing/payment-status`, {
          orderId: payment.orderId,
          userId: payment.userId,
          oldStatus,
          newStatus: payment.status,
          paidAt: payment.paidAt,
          transactionId: payment.transactionId
        }),

        // Send notification for important status changes
        ...(this.shouldNotifyStatusChange(payment.status) ? [
          this.makeRequest('POST', `${this.services.notificationService}/api/notifications/payment-status`, {
            userId: payment.userId,
            orderId: payment.orderId,
            status: payment.status,
            amount: payment.grossAmount,
            currency: payment.currency
          })
        ] : [])
      ];

      await Promise.allSettled(notifications);

      logger.info('📢 Payment status notifications sent', {
        orderId: payment.orderId,
        oldStatus,
        newStatus: payment.status
      });

    } catch (error) {
      logger.error('❌ Failed to send payment status notifications', {
        error: error.message,
        orderId: payment.orderId
      });
    }
  }

  /**
   * Notify payment cancelled
   * @param {Object} payment - Payment document
   * @param {string} reason - Cancellation reason
   * @returns {Promise<void>}
   */
  async notifyPaymentCancelled(payment, reason) {
    try {
      const notifications = [
        // Update billing service
        this.makeRequest('PUT', `${this.services.billingService}/api/billing/payment-cancelled`, {
          orderId: payment.orderId,
          userId: payment.userId,
          reason,
          cancelledAt: payment.metadata.cancelledAt
        }),

        // Send notification
        this.makeRequest('POST', `${this.services.notificationService}/api/notifications/payment-cancelled`, {
          userId: payment.userId,
          orderId: payment.orderId,
          reason,
          amount: payment.grossAmount,
          currency: payment.currency
        })
      ];

      await Promise.allSettled(notifications);

      logger.info('📢 Payment cancellation notifications sent', {
        orderId: payment.orderId,
        reason
      });

    } catch (error) {
      logger.error('❌ Failed to send payment cancellation notifications', {
        error: error.message,
        orderId: payment.orderId
      });
    }
  }

  /**
   * Notify payment refunded
   * @param {Object} payment - Payment document
   * @param {number} amount - Refund amount
   * @param {string} reason - Refund reason
   * @returns {Promise<void>}
   */
  async notifyPaymentRefunded(payment, amount, reason) {
    try {
      const notifications = [
        // Update billing service
        this.makeRequest('PUT', `${this.services.billingService}/api/billing/payment-refunded`, {
          orderId: payment.orderId,
          userId: payment.userId,
          refundAmount: amount,
          reason,
          refundedAt: payment.refundedAt
        }),

        // Send notification
        this.makeRequest('POST', `${this.services.notificationService}/api/notifications/payment-refunded`, {
          userId: payment.userId,
          orderId: payment.orderId,
          refundAmount: amount,
          reason,
          currency: payment.currency
        })
      ];

      await Promise.allSettled(notifications);

      logger.info('📢 Payment refund notifications sent', {
        orderId: payment.orderId,
        refundAmount: amount,
        reason
      });

    } catch (error) {
      logger.error('❌ Failed to send payment refund notifications', {
        error: error.message,
        orderId: payment.orderId
      });
    }
  }

  /**
   * Activate user subscription
   * @param {Object} subscriptionData - Subscription data
   * @returns {Promise<void>}
   */
  async activateUserSubscription(subscriptionData) {
    try {
      const {
        userId,
        subscriptionId,
        planType,
        billingCycle,
        startDate,
        endDate,
        status
      } = subscriptionData;

      const requests = [
        // Update subscription service
        this.makeRequest('PUT', `${this.services.subscriptionService}/api/subscriptions/${subscriptionId}/activate`, {
          userId,
          planType,
          billingCycle,
          startDate,
          endDate,
          status,
          activatedAt: new Date()
        }),

        // Update user management
        this.makeRequest('PUT', `${this.services.userManagement}/api/users/${userId}/subscription`, {
          subscriptionId,
          planType,
          status: 'active',
          startDate,
          endDate
        }),

        // Send welcome notification
        this.makeRequest('POST', `${this.services.notificationService}/api/notifications/subscription-activated`, {
          userId,
          subscriptionId,
          planType,
          billingCycle,
          startDate,
          endDate
        })
      ];

      await Promise.allSettled(requests);

      // Clear user cache to ensure fresh data
      await this.clearUserCache(userId);

      logger.info('✅ Subscription activation notifications sent', {
        userId,
        subscriptionId,
        planType
      });

    } catch (error) {
      logger.error('❌ Failed to activate user subscription', {
        error: error.message,
        userId: subscriptionData.userId,
        subscriptionId: subscriptionData.subscriptionId
      });

      throw error;
    }
  }

  /**
   * Cancel user subscription
   * @param {string} userId - User ID
   * @param {string} subscriptionId - Subscription ID
   * @param {string} reason - Cancellation reason
   * @returns {Promise<void>}
   */
  async cancelUserSubscription(userId, subscriptionId, reason) {
    try {
      const requests = [
        // Update subscription service
        this.makeRequest('PUT', `${this.services.subscriptionService}/api/subscriptions/${subscriptionId}/cancel`, {
          userId,
          reason,
          cancelledAt: new Date()
        }),

        // Update user management
        this.makeRequest('PUT', `${this.services.userManagement}/api/users/${userId}/subscription`, {
          subscriptionId,
          status: 'cancelled',
          cancelledAt: new Date(),
          cancellationReason: reason
        }),

        // Send cancellation notification
        this.makeRequest('POST', `${this.services.notificationService}/api/notifications/subscription-cancelled`, {
          userId,
          subscriptionId,
          reason,
          cancelledAt: new Date()
        })
      ];

      await Promise.allSettled(requests);

      // Clear user cache
      await this.clearUserCache(userId);

      logger.info('🚫 Subscription cancellation notifications sent', {
        userId,
        subscriptionId,
        reason
      });

    } catch (error) {
      logger.error('❌ Failed to cancel user subscription', {
        error: error.message,
        userId,
        subscriptionId
      });

      throw error;
    }
  }

  /**
   * Handle subscription refund
   * @param {Object} refundData - Refund data
   * @returns {Promise<void>}
   */
  async handleSubscriptionRefund(refundData) {
    try {
      const {
        userId,
        subscriptionId,
        refundAmount,
        proRatedAmount,
        remainingDays
      } = refundData;

      const requests = [
        // Update subscription service
        this.makeRequest('PUT', `${this.services.subscriptionService}/api/subscriptions/${subscriptionId}/refund`, {
          userId,
          refundAmount,
          proRatedAmount,
          remainingDays,
          refundedAt: new Date()
        }),

        // Update billing service
        this.makeRequest('POST', `${this.services.billingService}/api/billing/subscription-refund`, {
          userId,
          subscriptionId,
          refundAmount,
          proRatedAmount,
          remainingDays
        }),

        // Send refund notification
        this.makeRequest('POST', `${this.services.notificationService}/api/notifications/subscription-refunded`, {
          userId,
          subscriptionId,
          refundAmount,
          remainingDays
        })
      ];

      await Promise.allSettled(requests);

      logger.info('💸 Subscription refund notifications sent', {
        userId,
        subscriptionId,
        refundAmount
      });

    } catch (error) {
      logger.error('❌ Failed to handle subscription refund', {
        error: error.message,
        userId: refundData.userId,
        subscriptionId: refundData.subscriptionId
      });

      throw error;
    }
  }

  /**
   * Get user subscription details
   * @param {string} userId - User ID
   * @param {string} subscriptionId - Subscription ID
   * @returns {Promise<Object>} Subscription details
   */
  async getUserSubscription(userId, subscriptionId) {
    try {
      const response = await this.makeRequest('GET',
        `${this.services.subscriptionService}/api/subscriptions/${subscriptionId}/user/${userId}`
      );

      return response.data || { isActive: false };

    } catch (error) {
      if (error.response?.status === 404) {
        return { isActive: false };
      }

      logger.error('❌ Failed to get user subscription', {
        error: error.message,
        userId,
        subscriptionId
      });

      return { isActive: false };
    }
  }

  /**
   * Notify subscription review required
   * @param {Object} subscription - Subscription document
   * @param {string} reason - Review reason
   * @returns {Promise<void>}
   */
  async notifySubscriptionReview(subscription, reason) {
    try {
      const requests = [
        // Alert billing service
        this.makeRequest('POST', `${this.services.billingService}/api/billing/subscription-review`, {
          subscriptionId: subscription.subscriptionId,
          userId: subscription.userId,
          reason,
          requestedAt: new Date()
        }),

        // Send admin notification
        this.makeRequest('POST', `${this.services.notificationService}/api/notifications/admin/subscription-review`, {
          subscriptionId: subscription.subscriptionId,
          userId: subscription.userId,
          reason,
          planType: subscription.subscriptionDetails.planType,
          amount: subscription.amount
        })
      ];

      await Promise.allSettled(requests);

      logger.warn('⚠️ Subscription review notifications sent', {
        subscriptionId: subscription.subscriptionId,
        reason
      });

    } catch (error) {
      logger.error('❌ Failed to send subscription review notifications', {
        error: error.message,
        subscriptionId: subscription.subscriptionId
      });
    }
  }

  /**
   * Make HTTP request with retry logic
   * @param {string} method - HTTP method
   * @param {string} url - Request URL
   * @param {Object} data - Request data
   * @param {number} retryAttempt - Current retry attempt
   * @returns {Promise<Object>} Response data
   */
  async makeRequest(method, url, data = null, retryAttempt = 0) {
    try {
      const config = {
        method,
        url,
        timeout: this.timeout,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${process.env.SERVICE_TOKEN}`,
          'X-Service-Name': 'payment-service'
        }
      };

      if (data && ['POST', 'PUT', 'PATCH'].includes(method.toUpperCase())) {
        config.data = data;
      }

      const response = await axios(config);

      return {
        success: true,
        data: response.data
      };

    } catch (error) {
      if (retryAttempt < this.retryCount && this.shouldRetry(error)) {
        logger.warn(`⚠️ Request failed, retrying (${retryAttempt + 1}/${this.retryCount})`, {
          url,
          error: error.message
        });

        // Exponential backoff
        await this.delay(Math.pow(2, retryAttempt) * 1000);
        return this.makeRequest(method, url, data, retryAttempt + 1);
      }

      logger.error('❌ Request failed after retries', {
        url,
        method,
        error: error.message,
        retryAttempt
      });

      throw error;
    }
  }

  /**
   * Check if request should be retried
   * @param {Error} error - Request error
   * @returns {boolean} Should retry
   */
  shouldRetry(error) {
    // Retry on network errors or 5xx status codes
    return !error.response ||
           (error.response.status >= 500 && error.response.status < 600) ||
           error.code === 'ECONNREFUSED' ||
           error.code === 'ENOTFOUND' ||
           error.code === 'ETIMEDOUT';
  }

  /**
   * Check if status change should trigger notification
   * @param {string} status - Payment status
   * @returns {boolean} Should notify
   */
  shouldNotifyStatusChange(status) {
    return ['settlement', 'capture', 'deny', 'expire', 'failure', 'refund'].includes(status);
  }

  /**
   * Delay execution
   * @param {number} ms - Milliseconds to delay
   * @returns {Promise<void>}
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Cache user data
   * @param {string} userId - User ID
   * @param {Object} userData - User data
   * @returns {Promise<void>}
   */
  async cacheUser(userId, userData) {
    try {
      const cacheKey = `user:${userId}`;
      await redisConnection.setCache(cacheKey, userData, 1800); // 30 minutes
    } catch (error) {
      logger.warn('⚠️ Failed to cache user data', {
        userId,
        error: error.message
      });
    }
  }

  /**
   * Get cached user data
   * @param {string} userId - User ID
   * @returns {Promise<Object|null>} User data or null
   */
  async getCachedUser(userId) {
    try {
      const cacheKey = `user:${userId}`;
      return await redisConnection.getCache(cacheKey);
    } catch (error) {
      logger.warn('⚠️ Failed to get cached user data', {
        userId,
        error: error.message
      });
      return null;
    }
  }

  /**
   * Clear cached user data
   * @param {string} userId - User ID
   * @returns {Promise<void>}
   */
  async clearUserCache(userId) {
    try {
      const cacheKey = `user:${userId}`;
      await redisConnection.deleteCache(cacheKey);
    } catch (error) {
      logger.warn('⚠️ Failed to clear user cache', {
        userId,
        error: error.message
      });
    }
  }
}

module.exports = new IntegrationService();