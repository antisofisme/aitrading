const midtransClient = require('midtrans-client');
const winston = require('winston');
const crypto = require('crypto');
const { v4: uuidv4 } = require('uuid');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  defaultMeta: { service: 'payment-gateway-midtrans' }
});

// Midtrans configuration
const MIDTRANS_CONFIG = {
  isProduction: process.env.MIDTRANS_IS_PRODUCTION === 'true',
  serverKey: process.env.MIDTRANS_SERVER_KEY || 'your-server-key',
  clientKey: process.env.MIDTRANS_CLIENT_KEY || 'your-client-key'
};

let snap;
let coreApi;

/**
 * Initialize Midtrans services
 */
function initializeMidtrans() {
  try {
    // Initialize Snap (for payment UI)
    snap = new midtransClient.Snap(MIDTRANS_CONFIG);

    // Initialize Core API (for payment operations)
    coreApi = new midtransClient.CoreApi(MIDTRANS_CONFIG);

    logger.info('Midtrans services initialized successfully');
    logger.info(`Environment: ${MIDTRANS_CONFIG.isProduction ? 'Production' : 'Sandbox'}`);

    return { snap, coreApi };
  } catch (error) {
    logger.error('Failed to initialize Midtrans:', error);
    throw error;
  }
}

/**
 * Create Midtrans payment transaction
 */
async function createPaymentTransaction(paymentData) {
  try {
    const {
      orderId,
      amount,
      currency = 'IDR',
      customerDetails,
      itemDetails,
      paymentMethod,
      subscriptionId
    } = paymentData;

    // Generate unique transaction ID
    const transactionId = orderId || `TXN-${Date.now()}-${uuidv4().substring(0, 8)}`;

    // Prepare transaction details
    const parameter = {
      transaction_details: {
        order_id: transactionId,
        gross_amount: amount
      },
      credit_card: {
        secure: true,
        // Enable 3D Secure for all transactions
        authentication: true,
        // Save card token for future use (with customer consent)
        save_card: false
      },
      customer_details: {
        first_name: customerDetails.firstName,
        last_name: customerDetails.lastName,
        email: customerDetails.email,
        phone: customerDetails.phone,
        billing_address: customerDetails.billingAddress || {},
        shipping_address: customerDetails.shippingAddress || {}
      },
      item_details: itemDetails || [{
        id: subscriptionId || 'SUBSCRIPTION',
        price: amount,
        quantity: 1,
        name: 'AI Trading Platform Subscription',
        category: 'digital_service'
      }],
      callbacks: {
        finish: process.env.PAYMENT_FINISH_URL || 'https://aitrading.app/payment/finish',
        error: process.env.PAYMENT_ERROR_URL || 'https://aitrading.app/payment/error',
        pending: process.env.PAYMENT_PENDING_URL || 'https://aitrading.app/payment/pending'
      },
      expiry: {
        // Payment expires in 24 hours
        start_time: new Date().toISOString().replace(/\.\d{3}Z$/, '+07:00'),
        unit: 'hour',
        duration: 24
      },
      custom_field1: subscriptionId || '',
      custom_field2: customerDetails.userId || '',
      custom_field3: paymentMethod || 'auto'
    };

    // Add payment method specific configurations
    if (paymentMethod) {
      switch (paymentMethod) {
        case 'bank_transfer':
          parameter.payment_type = 'bank_transfer';
          parameter.bank_transfer = {
            bank: 'bca', // Default to BCA, can be configured
            va_number: transactionId.replace(/[^0-9]/g, '').substring(0, 10)
          };
          break;

        case 'e_wallet':
          parameter.payment_type = 'gopay';
          parameter.gopay = {
            enable_callback: true,
            callback_url: `${process.env.BASE_URL}/api/webhooks/midtrans`
          };
          break;

        case 'virtual_account':
          parameter.payment_type = 'bank_transfer';
          parameter.bank_transfer = {
            bank: 'bni', // BNI Virtual Account
            va_number: transactionId.replace(/[^0-9]/g, '').substring(0, 16)
          };
          break;

        case 'convenience_store':
          parameter.payment_type = 'cstore';
          parameter.cstore = {
            store: 'indomaret',
            message: `AI Trading Subscription - ${transactionId}`
          };
          break;

        default:
          // Auto payment method selection
          break;
      }
    }

    // Create transaction using Snap
    const transaction = await snap.createTransaction(parameter);

    logger.info(`Payment transaction created: ${transactionId}`);

    return {
      transactionId,
      token: transaction.token,
      redirectUrl: transaction.redirect_url,
      paymentUrl: `https://app.${MIDTRANS_CONFIG.isProduction ? '' : 'sandbox.'}midtrans.com/snap/v2/vtweb/${transaction.token}`,
      parameter
    };

  } catch (error) {
    logger.error('Create payment transaction error:', error);
    throw error;
  }
}

/**
 * Check payment transaction status
 */
async function checkTransactionStatus(transactionId) {
  try {
    const statusResponse = await coreApi.transaction.status(transactionId);

    return {
      transactionId,
      status: statusResponse.transaction_status,
      fraudStatus: statusResponse.fraud_status,
      paymentType: statusResponse.payment_type,
      grossAmount: statusResponse.gross_amount,
      transactionTime: statusResponse.transaction_time,
      settlementTime: statusResponse.settlement_time,
      currency: statusResponse.currency,
      vaNumbers: statusResponse.va_numbers,
      paymentCode: statusResponse.payment_code,
      statusCode: statusResponse.status_code,
      statusMessage: statusResponse.status_message
    };

  } catch (error) {
    logger.error('Check transaction status error:', error);
    throw error;
  }
}

/**
 * Cancel payment transaction
 */
async function cancelTransaction(transactionId) {
  try {
    const cancelResponse = await coreApi.transaction.cancel(transactionId);

    logger.info(`Transaction cancelled: ${transactionId}`);

    return {
      transactionId,
      status: cancelResponse.transaction_status,
      statusCode: cancelResponse.status_code,
      statusMessage: cancelResponse.status_message
    };

  } catch (error) {
    logger.error('Cancel transaction error:', error);
    throw error;
  }
}

/**
 * Refund payment transaction
 */
async function refundTransaction(transactionId, amount, reason) {
  try {
    const refundData = {
      refund_key: `REFUND-${transactionId}-${Date.now()}`,
      amount: amount,
      reason: reason || 'Customer request'
    };

    const refundResponse = await coreApi.transaction.refund(transactionId, refundData);

    logger.info(`Transaction refunded: ${transactionId}, Amount: ${amount}`);

    return {
      transactionId,
      refundKey: refundData.refund_key,
      status: refundResponse.transaction_status,
      refundAmount: refundResponse.refund_amount,
      statusCode: refundResponse.status_code,
      statusMessage: refundResponse.status_message
    };

  } catch (error) {
    logger.error('Refund transaction error:', error);
    throw error;
  }
}

/**
 * Verify webhook notification signature
 */
function verifyWebhookSignature(notification, signatureKey) {
  try {
    const {
      order_id,
      status_code,
      gross_amount,
      signature_key
    } = notification;

    // Create signature string
    const signatureString = `${order_id}${status_code}${gross_amount}${MIDTRANS_CONFIG.serverKey}`;

    // Generate SHA512 hash
    const calculatedSignature = crypto
      .createHash('sha512')
      .update(signatureString)
      .digest('hex');

    // Compare signatures
    const isValid = calculatedSignature === signature_key;

    if (!isValid) {
      logger.warn(`Invalid webhook signature for order: ${order_id}`);
    }

    return isValid;

  } catch (error) {
    logger.error('Webhook signature verification error:', error);
    return false;
  }
}

/**
 * Process webhook notification
 */
async function processWebhookNotification(notification) {
  try {
    const {
      transaction_status,
      fraud_status,
      order_id,
      payment_type,
      gross_amount,
      settlement_time
    } = notification;

    // Determine final payment status
    let paymentStatus = 'pending';

    if (transaction_status === 'capture') {
      if (fraud_status === 'challenge') {
        paymentStatus = 'challenge';
      } else if (fraud_status === 'accept') {
        paymentStatus = 'success';
      }
    } else if (transaction_status === 'settlement') {
      paymentStatus = 'success';
    } else if (transaction_status === 'deny' || transaction_status === 'cancel' || transaction_status === 'expire') {
      paymentStatus = 'failed';
    } else if (transaction_status === 'pending') {
      paymentStatus = 'pending';
    }

    logger.info(`Webhook processed for order ${order_id}: ${paymentStatus}`);

    return {
      orderId: order_id,
      status: paymentStatus,
      transactionStatus: transaction_status,
      fraudStatus: fraud_status,
      paymentType: payment_type,
      grossAmount: gross_amount,
      settlementTime: settlement_time,
      processedAt: new Date()
    };

  } catch (error) {
    logger.error('Process webhook notification error:', error);
    throw error;
  }
}

/**
 * Get available payment methods for Indonesian market
 */
function getAvailablePaymentMethods() {
  return {
    credit_card: {
      name: 'Credit Card',
      description: 'Visa, Mastercard, JCB',
      fees: '2.9% + IDR 2,000',
      processingTime: 'Instant'
    },
    bank_transfer: {
      name: 'Bank Transfer',
      description: 'BCA, BNI, BRI, Mandiri',
      fees: 'IDR 4,000',
      processingTime: '1-3 hours'
    },
    virtual_account: {
      name: 'Virtual Account',
      description: 'BCA VA, BNI VA, BRI VA',
      fees: 'IDR 4,000',
      processingTime: 'Instant'
    },
    e_wallet: {
      name: 'E-Wallet',
      description: 'GoPay, ShopeePay, OVO',
      fees: '2% + IDR 1,000',
      processingTime: 'Instant'
    },
    convenience_store: {
      name: 'Convenience Store',
      description: 'Indomaret, Alfamart',
      fees: 'IDR 2,500',
      processingTime: '1-24 hours'
    }
  };
}

module.exports = {
  initializeMidtrans,
  createPaymentTransaction,
  checkTransactionStatus,
  cancelTransaction,
  refundTransaction,
  verifyWebhookSignature,
  processWebhookNotification,
  getAvailablePaymentMethods
};