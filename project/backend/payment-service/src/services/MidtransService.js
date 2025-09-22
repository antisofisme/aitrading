const midtransConfig = require('../config/midtrans');
const logger = require('../config/logger');
const crypto = require('crypto');
const { v4: uuidv4 } = require('uuid');

class MidtransService {
  constructor() {
    this.coreApi = midtransConfig.getCoreApi();
    this.snap = midtransConfig.getSnap();
    this.iris = midtransConfig.getIris();
    this.paymentMethods = midtransConfig.getPaymentMethods();
    this.indonesianConfig = midtransConfig.getIndonesianConfig();
  }

  /**
   * Create payment transaction with Snap
   * @param {Object} paymentData - Payment details
   * @returns {Promise<Object>} Snap transaction result
   */
  async createSnapTransaction(paymentData) {
    try {
      const {
        orderId,
        grossAmount,
        customerDetails,
        itemDetails,
        paymentMethods = [],
        customExpiry = null
      } = paymentData;

      const parameter = {
        transaction_details: {
          order_id: orderId,
          gross_amount: grossAmount
        },
        credit_card: this.paymentMethods.credit_card,
        customer_details: this.formatCustomerDetails(customerDetails),
        item_details: itemDetails,
        enabled_payments: paymentMethods.length > 0 ? paymentMethods : this.getDefaultPaymentMethods(),
        callbacks: this.indonesianConfig.webhooks,
        expiry: customExpiry || this.getDefaultExpiry(),
        custom_field1: `user_${customerDetails.userId}`,
        custom_field2: paymentData.metadata?.planId || '',
        custom_field3: paymentData.metadata?.subscriptionId || ''
      };

      // Add Indonesian-specific configurations
      if (paymentMethods.includes('bank_transfer')) {
        parameter.bank_transfer = this.paymentMethods.bank_transfer;
      }

      if (paymentMethods.includes('gopay')) {
        parameter.gopay = this.paymentMethods.gopay;
      }

      if (paymentMethods.includes('ovo')) {
        parameter.ovo = this.paymentMethods.ovo;
      }

      if (paymentMethods.includes('dana')) {
        parameter.dana = this.paymentMethods.dana;
      }

      if (paymentMethods.includes('linkaja')) {
        parameter.linkaja = this.paymentMethods.linkaja;
      }

      if (paymentMethods.includes('shopeepay')) {
        parameter.shopeepay = this.paymentMethods.shopeepay;
      }

      const transaction = await this.snap.createTransaction(parameter);

      logger.info('✅ Snap transaction created successfully', {
        orderId,
        token: transaction.token,
        redirectUrl: transaction.redirect_url
      });

      return {
        success: true,
        data: {
          token: transaction.token,
          redirectUrl: transaction.redirect_url,
          orderId: orderId
        }
      };

    } catch (error) {
      logger.error('❌ Failed to create Snap transaction', {
        error: error.message,
        orderId: paymentData.orderId
      });

      return {
        success: false,
        error: {
          code: error.ApiResponse?.error_messages?.[0] || 'TRANSACTION_FAILED',
          message: error.message
        }
      };
    }
  }

  /**
   * Create direct payment transaction (Core API)
   * @param {Object} paymentData - Payment details
   * @returns {Promise<Object>} Transaction result
   */
  async createDirectTransaction(paymentData) {
    try {
      const {
        orderId,
        grossAmount,
        paymentType,
        customerDetails,
        itemDetails,
        paymentDetails = {}
      } = paymentData;

      const parameter = {
        payment_type: paymentType,
        transaction_details: {
          order_id: orderId,
          gross_amount: grossAmount
        },
        customer_details: this.formatCustomerDetails(customerDetails),
        item_details: itemDetails
      };

      // Add payment method specific parameters
      switch (paymentType) {
        case 'credit_card':
          parameter.credit_card = {
            token_id: paymentDetails.tokenId,
            authentication: paymentDetails.authentication || true,
            ...this.paymentMethods.credit_card
          };
          break;

        case 'bank_transfer':
          parameter.bank_transfer = {
            bank: paymentDetails.bank,
            ...this.paymentMethods.bank_transfer
          };
          break;

        case 'echannel':
          parameter.echannel = {
            bill_info1: this.paymentMethods.echannel.bill_info1,
            bill_info2: this.paymentMethods.echannel.bill_info2
          };
          break;

        case 'gopay':
          parameter.gopay = {
            enable_callback: true,
            callback_url: this.paymentMethods.gopay.callback_url
          };
          break;

        case 'ovo':
          parameter.ovo = {
            enable_callback: true,
            callback_url: this.paymentMethods.ovo.callback_url
          };
          break;

        case 'dana':
          parameter.dana = {
            enable_callback: true,
            callback_url: this.paymentMethods.dana.callback_url
          };
          break;

        case 'linkaja':
          parameter.linkaja = {
            enable_callback: true,
            callback_url: this.paymentMethods.linkaja.callback_url
          };
          break;

        case 'shopeepay':
          parameter.shopeepay = {
            enable_callback: true,
            callback_url: this.paymentMethods.shopeepay.callback_url
          };
          break;

        case 'cstore':
          parameter.cstore = {
            store: paymentDetails.store || 'indomaret',
            message: this.paymentMethods.cstore.message
          };
          break;
      }

      const transaction = await this.coreApi.charge(parameter);

      logger.info('✅ Direct transaction created successfully', {
        orderId,
        transactionId: transaction.transaction_id,
        status: transaction.transaction_status
      });

      return {
        success: true,
        data: transaction
      };

    } catch (error) {
      logger.error('❌ Failed to create direct transaction', {
        error: error.message,
        orderId: paymentData.orderId
      });

      return {
        success: false,
        error: {
          code: error.ApiResponse?.error_messages?.[0] || 'TRANSACTION_FAILED',
          message: error.message
        }
      };
    }
  }

  /**
   * Check transaction status
   * @param {string} orderId - Order ID
   * @returns {Promise<Object>} Transaction status
   */
  async checkTransactionStatus(orderId) {
    try {
      const status = await this.coreApi.transaction.status(orderId);

      logger.info('✅ Transaction status checked', {
        orderId,
        status: status.transaction_status,
        fraudStatus: status.fraud_status
      });

      return {
        success: true,
        data: status
      };

    } catch (error) {
      logger.error('❌ Failed to check transaction status', {
        error: error.message,
        orderId
      });

      return {
        success: false,
        error: {
          code: 'STATUS_CHECK_FAILED',
          message: error.message
        }
      };
    }
  }

  /**
   * Approve transaction (for challenge fraud status)
   * @param {string} orderId - Order ID
   * @returns {Promise<Object>} Approval result
   */
  async approveTransaction(orderId) {
    try {
      const result = await this.coreApi.transaction.approve(orderId);

      logger.info('✅ Transaction approved', { orderId });

      return {
        success: true,
        data: result
      };

    } catch (error) {
      logger.error('❌ Failed to approve transaction', {
        error: error.message,
        orderId
      });

      return {
        success: false,
        error: {
          code: 'APPROVAL_FAILED',
          message: error.message
        }
      };
    }
  }

  /**
   * Cancel transaction
   * @param {string} orderId - Order ID
   * @returns {Promise<Object>} Cancellation result
   */
  async cancelTransaction(orderId) {
    try {
      const result = await this.coreApi.transaction.cancel(orderId);

      logger.info('✅ Transaction cancelled', { orderId });

      return {
        success: true,
        data: result
      };

    } catch (error) {
      logger.error('❌ Failed to cancel transaction', {
        error: error.message,
        orderId
      });

      return {
        success: false,
        error: {
          code: 'CANCELLATION_FAILED',
          message: error.message
        }
      };
    }
  }

  /**
   * Refund transaction
   * @param {string} orderId - Order ID
   * @param {number} amount - Refund amount (optional for partial refund)
   * @param {string} reason - Refund reason
   * @returns {Promise<Object>} Refund result
   */
  async refundTransaction(orderId, amount = null, reason = 'Customer request') {
    try {
      const parameter = {
        amount: amount,
        reason: reason
      };

      const result = await this.coreApi.transaction.refund(orderId, parameter);

      logger.info('✅ Transaction refunded', {
        orderId,
        amount: amount || 'full',
        reason
      });

      return {
        success: true,
        data: result
      };

    } catch (error) {
      logger.error('❌ Failed to refund transaction', {
        error: error.message,
        orderId,
        amount
      });

      return {
        success: false,
        error: {
          code: 'REFUND_FAILED',
          message: error.message
        }
      };
    }
  }

  /**
   * Verify webhook notification signature
   * @param {Object} notification - Webhook notification data
   * @param {string} signature - Signature from header
   * @returns {boolean} Verification result
   */
  verifyWebhookSignature(notification, signature) {
    try {
      const {
        order_id,
        status_code,
        gross_amount,
        signature_key
      } = notification;

      const serverKey = midtransConfig.serverKey;
      const input = order_id + status_code + gross_amount + serverKey;
      const hash = crypto.createHash('sha512').update(input).digest('hex');

      const isValid = hash === signature_key;

      if (!isValid) {
        logger.warn('⚠️ Invalid webhook signature', {
          orderId: order_id,
          expected: hash,
          received: signature_key
        });
      }

      return isValid;

    } catch (error) {
      logger.error('❌ Error verifying webhook signature', {
        error: error.message
      });
      return false;
    }
  }

  /**
   * Format customer details for Indonesian compliance
   * @param {Object} customerDetails - Raw customer details
   * @returns {Object} Formatted customer details
   */
  formatCustomerDetails(customerDetails) {
    return {
      first_name: customerDetails.firstName,
      last_name: customerDetails.lastName || '',
      email: customerDetails.email,
      phone: this.formatPhoneNumber(customerDetails.phone),
      billing_address: customerDetails.billingAddress ? {
        first_name: customerDetails.billingAddress.firstName,
        last_name: customerDetails.billingAddress.lastName || '',
        address: customerDetails.billingAddress.address,
        city: customerDetails.billingAddress.city,
        postal_code: customerDetails.billingAddress.postalCode,
        phone: this.formatPhoneNumber(customerDetails.billingAddress.phone),
        country_code: customerDetails.billingAddress.countryCode || 'IDN'
      } : undefined,
      shipping_address: customerDetails.shippingAddress ? {
        first_name: customerDetails.shippingAddress.firstName,
        last_name: customerDetails.shippingAddress.lastName || '',
        address: customerDetails.shippingAddress.address,
        city: customerDetails.shippingAddress.city,
        postal_code: customerDetails.shippingAddress.postalCode,
        phone: this.formatPhoneNumber(customerDetails.shippingAddress.phone),
        country_code: customerDetails.shippingAddress.countryCode || 'IDN'
      } : undefined
    };
  }

  /**
   * Format phone number for Indonesian standard
   * @param {string} phone - Phone number
   * @returns {string} Formatted phone number
   */
  formatPhoneNumber(phone) {
    if (!phone) return '';

    // Remove all non-numeric characters
    const cleaned = phone.replace(/\D/g, '');

    // Convert to Indonesian format (+62)
    if (cleaned.startsWith('0')) {
      return '+62' + cleaned.substring(1);
    }
    if (cleaned.startsWith('62')) {
      return '+' + cleaned;
    }
    if (!cleaned.startsWith('+62')) {
      return '+62' + cleaned;
    }

    return cleaned;
  }

  /**
   * Get default payment methods for Indonesian market
   * @returns {Array} Default payment methods
   */
  getDefaultPaymentMethods() {
    return [
      'credit_card',
      'bca_va',
      'bni_va',
      'bri_va',
      'mandiri_va',
      'permata_va',
      'cimb_va',
      'gopay',
      'ovo',
      'dana',
      'linkaja',
      'shopeepay',
      'indomaret',
      'akulaku'
    ];
  }

  /**
   * Get default expiry settings
   * @returns {Object} Expiry settings
   */
  getDefaultExpiry() {
    return {
      start_time: new Date().toISOString(),
      unit: 'minute',
      duration: 60 // 1 hour
    };
  }

  /**
   * Generate unique order ID
   * @param {string} prefix - Order ID prefix
   * @returns {string} Unique order ID
   */
  generateOrderId(prefix = 'TRD') {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 8);
    return `${prefix}-${timestamp}-${random}`.toUpperCase();
  }

  /**
   * Calculate Indonesian tax (PPN 11%)
   * @param {number} amount - Base amount
   * @returns {Object} Amount breakdown
   */
  calculateTax(amount) {
    const taxRate = 0.11; // 11% PPN
    const tax = Math.round(amount * taxRate);
    const grossAmount = amount + tax;

    return {
      baseAmount: amount,
      tax: tax,
      grossAmount: grossAmount
    };
  }
}

module.exports = new MidtransService();