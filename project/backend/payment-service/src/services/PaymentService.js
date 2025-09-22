const Payment = require('../models/Payment');
const MidtransService = require('./MidtransService');
const SubscriptionService = require('./SubscriptionService');
const IntegrationService = require('./IntegrationService');
const logger = require('../config/logger');
const redisConnection = require('../config/redis');

class PaymentService {
  constructor() {
    this.midtrans = MidtransService;
    this.subscription = SubscriptionService;
    this.integration = IntegrationService;
  }

  /**
   * Create new payment transaction
   * @param {Object} paymentData - Payment request data
   * @returns {Promise<Object>} Payment result
   */
  async createPayment(paymentData) {
    try {
      const {
        userId,
        amount,
        currency = 'IDR',
        paymentType,
        paymentMethods = [],
        customerDetails,
        itemDetails,
        subscriptionId = null,
        planId = null,
        metadata = {}
      } = paymentData;

      // Validate user exists
      const userValidation = await this.integration.validateUser(userId);
      if (!userValidation.isValid) {
        throw new Error('Invalid user ID');
      }

      // Calculate tax and fees
      const taxCalculation = this.midtrans.calculateTax(amount);

      // Generate unique order ID
      const orderId = this.midtrans.generateOrderId('PAY');

      // Create payment record
      const payment = new Payment({
        orderId,
        userId,
        subscriptionId,
        planId,
        amount: taxCalculation.baseAmount,
        currency,
        grossAmount: taxCalculation.grossAmount,
        tax: taxCalculation.tax,
        paymentType: paymentType || 'credit_card',
        customerDetails: this.formatCustomerDetails(customerDetails, userValidation.user),
        itemDetails: itemDetails || this.generateDefaultItemDetails(taxCalculation.baseAmount, planId),
        metadata,
        status: 'pending'
      });

      await payment.save();

      logger.info('💰 Payment record created', {
        orderId,
        userId,
        amount: taxCalculation.grossAmount,
        currency
      });

      // Create Midtrans transaction
      let transactionResult;

      if (paymentMethods.length === 1 && paymentMethods[0] !== 'credit_card') {
        // Direct payment for specific method
        transactionResult = await this.midtrans.createDirectTransaction({
          orderId,
          grossAmount: taxCalculation.grossAmount,
          paymentType: paymentMethods[0],
          customerDetails: payment.customerDetails,
          itemDetails: payment.itemDetails,
          paymentDetails: metadata.paymentDetails || {}
        });
      } else {
        // Snap payment for multiple methods or credit card
        transactionResult = await this.midtrans.createSnapTransaction({
          orderId,
          grossAmount: taxCalculation.grossAmount,
          customerDetails: payment.customerDetails,
          itemDetails: payment.itemDetails,
          paymentMethods: paymentMethods.length > 0 ? paymentMethods : undefined,
          customExpiry: metadata.customExpiry
        });
      }

      if (!transactionResult.success) {
        payment.status = 'failure';
        payment.lastError = {
          code: transactionResult.error.code,
          message: transactionResult.error.message,
          timestamp: new Date()
        };
        await payment.save();

        throw new Error(transactionResult.error.message);
      }

      // Update payment with Midtrans response
      payment.midtransResponse = {
        snapToken: transactionResult.data.token,
        snapRedirectUrl: transactionResult.data.redirectUrl,
        transactionTime: new Date()
      };

      await payment.save();

      // Cache payment for quick lookup
      await this.cachePayment(payment);

      // Notify integration services
      await this.integration.notifyPaymentCreated(payment);

      logger.info('✅ Payment transaction created successfully', {
        orderId,
        token: transactionResult.data.token
      });

      return {
        success: true,
        data: {
          orderId,
          token: transactionResult.data.token,
          redirectUrl: transactionResult.data.redirectUrl,
          grossAmount: taxCalculation.grossAmount,
          tax: taxCalculation.tax,
          expiry: metadata.customExpiry || '1 hour'
        }
      };

    } catch (error) {
      logger.error('❌ Failed to create payment', {
        error: error.message,
        userId: paymentData.userId
      });

      throw error;
    }
  }

  /**
   * Process webhook notification
   * @param {Object} notification - Webhook data
   * @param {string} signature - Webhook signature
   * @returns {Promise<Object>} Processing result
   */
  async processWebhook(notification, signature) {
    try {
      const { order_id, transaction_status, fraud_status } = notification;

      // Verify signature
      const isValidSignature = this.midtrans.verifyWebhookSignature(notification, signature);
      if (!isValidSignature) {
        throw new Error('Invalid webhook signature');
      }

      // Find payment
      const payment = await Payment.findOne({ orderId: order_id });
      if (!payment) {
        throw new Error(`Payment not found for order ID: ${order_id}`);
      }

      // Add webhook data
      await payment.addWebhookData(notification, signature);

      // Process status update
      const oldStatus = payment.status;
      await this.updatePaymentStatus(payment, transaction_status, fraud_status, notification);

      logger.info('📢 Webhook processed successfully', {
        orderId: order_id,
        oldStatus,
        newStatus: payment.status,
        transactionStatus: transaction_status
      });

      // Handle subscription if applicable
      if (payment.subscriptionId && payment.status === 'settlement') {
        await this.subscription.activateSubscription(payment);
      }

      // Notify integration services
      await this.integration.notifyPaymentStatusChanged(payment, oldStatus);

      return {
        success: true,
        message: 'Webhook processed successfully'
      };

    } catch (error) {
      logger.error('❌ Failed to process webhook', {
        error: error.message,
        orderId: notification?.order_id
      });

      throw error;
    }
  }

  /**
   * Get payment details
   * @param {string} orderId - Order ID
   * @param {string} userId - User ID for authorization
   * @returns {Promise<Object>} Payment details
   */
  async getPayment(orderId, userId = null) {
    try {
      // Try cache first
      const cached = await this.getCachedPayment(orderId);
      if (cached) {
        if (userId && cached.userId !== userId) {
          throw new Error('Unauthorized access to payment');
        }
        return cached;
      }

      // Fetch from database
      const query = { orderId };
      if (userId) {
        query.userId = userId;
      }

      const payment = await Payment.findOne(query);
      if (!payment) {
        throw new Error('Payment not found');
      }

      // Update cache
      await this.cachePayment(payment);

      return payment;

    } catch (error) {
      logger.error('❌ Failed to get payment', {
        error: error.message,
        orderId,
        userId
      });

      throw error;
    }
  }

  /**
   * Get user payment history
   * @param {string} userId - User ID
   * @param {Object} options - Query options
   * @returns {Promise<Object>} Payment history
   */
  async getUserPayments(userId, options = {}) {
    try {
      const {
        page = 1,
        limit = 20,
        status = null,
        dateFrom = null,
        dateTo = null,
        paymentType = null
      } = options;

      const query = { userId };

      // Add filters
      if (status) {
        query.status = status;
      }

      if (paymentType) {
        query.paymentType = paymentType;
      }

      if (dateFrom || dateTo) {
        query.createdAt = {};
        if (dateFrom) query.createdAt.$gte = new Date(dateFrom);
        if (dateTo) query.createdAt.$lte = new Date(dateTo);
      }

      const skip = (page - 1) * limit;

      const [payments, total] = await Promise.all([
        Payment.find(query)
          .sort({ createdAt: -1 })
          .skip(skip)
          .limit(limit)
          .select('-webhookData -securityInfo'),
        Payment.countDocuments(query)
      ]);

      const totalPages = Math.ceil(total / limit);

      return {
        payments,
        pagination: {
          page,
          limit,
          total,
          totalPages,
          hasNext: page < totalPages,
          hasPrev: page > 1
        }
      };

    } catch (error) {
      logger.error('❌ Failed to get user payments', {
        error: error.message,
        userId
      });

      throw error;
    }
  }

  /**
   * Cancel payment
   * @param {string} orderId - Order ID
   * @param {string} userId - User ID for authorization
   * @param {string} reason - Cancellation reason
   * @returns {Promise<Object>} Cancellation result
   */
  async cancelPayment(orderId, userId, reason = 'User cancellation') {
    try {
      const payment = await this.getPayment(orderId, userId);

      // Check if payment can be cancelled
      if (!['pending', 'authorize'].includes(payment.status)) {
        throw new Error('Payment cannot be cancelled in current status');
      }

      // Cancel in Midtrans
      const cancelResult = await this.midtrans.cancelTransaction(orderId);
      if (!cancelResult.success) {
        throw new Error(cancelResult.error.message);
      }

      // Update payment status
      payment.status = 'cancel';
      payment.metadata.cancellationReason = reason;
      payment.metadata.cancelledAt = new Date();
      await payment.save();

      // Clear cache
      await this.clearPaymentCache(orderId);

      // Notify integration services
      await this.integration.notifyPaymentCancelled(payment, reason);

      logger.info('🚫 Payment cancelled successfully', {
        orderId,
        userId,
        reason
      });

      return {
        success: true,
        message: 'Payment cancelled successfully'
      };

    } catch (error) {
      logger.error('❌ Failed to cancel payment', {
        error: error.message,
        orderId,
        userId
      });

      throw error;
    }
  }

  /**
   * Refund payment
   * @param {string} orderId - Order ID
   * @param {number} amount - Refund amount (null for full refund)
   * @param {string} reason - Refund reason
   * @returns {Promise<Object>} Refund result
   */
  async refundPayment(orderId, amount = null, reason = 'Customer request') {
    try {
      const payment = await this.getPayment(orderId);

      // Check if payment can be refunded
      if (!['settlement', 'capture'].includes(payment.status)) {
        throw new Error('Payment cannot be refunded in current status');
      }

      // Validate refund amount
      if (amount && amount > payment.grossAmount) {
        throw new Error('Refund amount cannot exceed payment amount');
      }

      // Process refund in Midtrans
      const refundResult = await this.midtrans.refundTransaction(orderId, amount, reason);
      if (!refundResult.success) {
        throw new Error(refundResult.error.message);
      }

      // Update payment status
      const isPartialRefund = amount && amount < payment.grossAmount;
      payment.status = isPartialRefund ? 'partial_refund' : 'refund';
      payment.refundedAt = new Date();
      payment.metadata.refundReason = reason;
      payment.metadata.refundAmount = amount || payment.grossAmount;

      await payment.save();

      // Clear cache
      await this.clearPaymentCache(orderId);

      // Handle subscription if applicable
      if (payment.subscriptionId && !isPartialRefund) {
        await this.subscription.handleRefund(payment);
      }

      // Notify integration services
      await this.integration.notifyPaymentRefunded(payment, amount, reason);

      logger.info('💸 Payment refunded successfully', {
        orderId,
        amount: amount || payment.grossAmount,
        reason
      });

      return {
        success: true,
        message: 'Payment refunded successfully',
        refundAmount: amount || payment.grossAmount
      };

    } catch (error) {
      logger.error('❌ Failed to refund payment', {
        error: error.message,
        orderId
      });

      throw error;
    }
  }

  /**
   * Check payment status and sync with Midtrans
   * @param {string} orderId - Order ID
   * @returns {Promise<Object>} Current status
   */
  async checkPaymentStatus(orderId) {
    try {
      const payment = await this.getPayment(orderId);

      // Get latest status from Midtrans
      const statusResult = await this.midtrans.checkTransactionStatus(orderId);
      if (!statusResult.success) {
        throw new Error(statusResult.error.message);
      }

      const midtransData = statusResult.data;

      // Update payment if status changed
      if (payment.status !== midtransData.transaction_status) {
        await this.updatePaymentStatus(
          payment,
          midtransData.transaction_status,
          midtransData.fraud_status,
          midtransData
        );
      }

      return {
        orderId,
        status: payment.status,
        fraudStatus: payment.fraudStatus,
        transactionId: payment.transactionId,
        amount: payment.grossAmount,
        currency: payment.currency,
        paymentType: payment.paymentType,
        updatedAt: payment.updatedAt
      };

    } catch (error) {
      logger.error('❌ Failed to check payment status', {
        error: error.message,
        orderId
      });

      throw error;
    }
  }

  /**
   * Update payment status based on Midtrans response
   * @param {Object} payment - Payment document
   * @param {string} transactionStatus - Transaction status from Midtrans
   * @param {string} fraudStatus - Fraud status from Midtrans
   * @param {Object} responseData - Full response data
   * @returns {Promise<void>}
   */
  async updatePaymentStatus(payment, transactionStatus, fraudStatus, responseData) {
    try {
      const oldStatus = payment.status;

      // Map Midtrans status to our status
      payment.status = this.mapMidtransStatus(transactionStatus, fraudStatus);
      payment.fraudStatus = fraudStatus;

      // Update transaction details
      if (responseData.transaction_id) {
        payment.transactionId = responseData.transaction_id;
      }

      // Update Midtrans response data
      payment.midtransResponse = {
        ...payment.midtransResponse,
        transactionStatus: transactionStatus,
        statusMessage: responseData.status_message,
        merchantId: responseData.merchant_id,
        paymentChannel: responseData.payment_type,
        bankCode: responseData.bank,
        approvalCode: responseData.approval_code,
        signatureKey: responseData.signature_key
      };

      // Handle specific statuses
      if (['settlement', 'capture'].includes(payment.status)) {
        payment.paidAt = new Date();
      }

      if (payment.status === 'expire') {
        payment.expiredAt = new Date();
      }

      await payment.save();

      // Clear cache to ensure fresh data
      await this.clearPaymentCache(payment.orderId);

      logger.info('🔄 Payment status updated', {
        orderId: payment.orderId,
        oldStatus,
        newStatus: payment.status,
        fraudStatus
      });

    } catch (error) {
      logger.error('❌ Failed to update payment status', {
        error: error.message,
        orderId: payment.orderId
      });

      throw error;
    }
  }

  /**
   * Map Midtrans transaction status to our payment status
   * @param {string} transactionStatus - Midtrans transaction status
   * @param {string} fraudStatus - Midtrans fraud status
   * @returns {string} Mapped status
   */
  mapMidtransStatus(transactionStatus, fraudStatus) {
    // Handle fraud status first
    if (fraudStatus === 'deny') {
      return 'deny';
    }

    if (fraudStatus === 'challenge') {
      return 'pending'; // Requires manual review
    }

    // Map transaction status
    const statusMap = {
      'capture': 'capture',
      'settlement': 'settlement',
      'pending': 'pending',
      'deny': 'deny',
      'cancel': 'cancel',
      'expire': 'expire',
      'failure': 'failure',
      'refund': 'refund',
      'partial_refund': 'partial_refund',
      'authorize': 'authorize'
    };

    return statusMap[transactionStatus] || 'pending';
  }

  /**
   * Format customer details with defaults
   * @param {Object} customerDetails - Raw customer details
   * @param {Object} userDetails - User details from user service
   * @returns {Object} Formatted customer details
   */
  formatCustomerDetails(customerDetails, userDetails = {}) {
    return {
      firstName: customerDetails.firstName || userDetails.firstName || 'User',
      lastName: customerDetails.lastName || userDetails.lastName || '',
      email: customerDetails.email || userDetails.email,
      phone: customerDetails.phone || userDetails.phone,
      billingAddress: customerDetails.billingAddress || {
        firstName: customerDetails.firstName || userDetails.firstName || 'User',
        lastName: customerDetails.lastName || userDetails.lastName || '',
        address: customerDetails.address || 'Indonesia',
        city: customerDetails.city || 'Jakarta',
        postalCode: customerDetails.postalCode || '10110',
        phone: customerDetails.phone || userDetails.phone,
        countryCode: 'IDN'
      }
    };
  }

  /**
   * Generate default item details
   * @param {number} amount - Item amount
   * @param {string} planId - Plan ID if applicable
   * @returns {Array} Item details
   */
  generateDefaultItemDetails(amount, planId = null) {
    const itemName = planId
      ? `Trading Platform - ${planId.toUpperCase()} Plan`
      : 'Trading Platform Subscription';

    return [{
      id: planId || 'subscription',
      price: amount,
      quantity: 1,
      name: itemName,
      brand: 'Neliti Trading',
      category: 'Subscription',
      merchantName: 'Neliti AI Trading Platform'
    }];
  }

  /**
   * Cache payment data
   * @param {Object} payment - Payment document
   * @returns {Promise<void>}
   */
  async cachePayment(payment) {
    try {
      const cacheKey = `payment:${payment.orderId}`;
      await redisConnection.setCache(cacheKey, payment.toObject(), 3600); // 1 hour
    } catch (error) {
      logger.warn('⚠️ Failed to cache payment', {
        orderId: payment.orderId,
        error: error.message
      });
    }
  }

  /**
   * Get cached payment data
   * @param {string} orderId - Order ID
   * @returns {Promise<Object|null>} Cached payment or null
   */
  async getCachedPayment(orderId) {
    try {
      const cacheKey = `payment:${orderId}`;
      return await redisConnection.getCache(cacheKey);
    } catch (error) {
      logger.warn('⚠️ Failed to get cached payment', {
        orderId,
        error: error.message
      });
      return null;
    }
  }

  /**
   * Clear payment cache
   * @param {string} orderId - Order ID
   * @returns {Promise<void>}
   */
  async clearPaymentCache(orderId) {
    try {
      const cacheKey = `payment:${orderId}`;
      await redisConnection.deleteCache(cacheKey);
    } catch (error) {
      logger.warn('⚠️ Failed to clear payment cache', {
        orderId,
        error: error.message
      });
    }
  }
}

module.exports = new PaymentService();