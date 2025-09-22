const midtransClient = require('midtrans-client');
const logger = require('./logger');

class MidtransConfig {
  constructor() {
    this.isProduction = process.env.NODE_ENV === 'production';
    this.serverKey = this.isProduction
      ? process.env.MIDTRANS_SERVER_KEY_PROD
      : process.env.MIDTRANS_SERVER_KEY_SANDBOX;
    this.clientKey = this.isProduction
      ? process.env.MIDTRANS_CLIENT_KEY_PROD
      : process.env.MIDTRANS_CLIENT_KEY_SANDBOX;

    if (!this.serverKey || !this.clientKey) {
      throw new Error('Midtrans credentials not configured properly');
    }

    this.initializeClients();
  }

  initializeClients() {
    try {
      // Core API for payment processing
      this.coreApi = new midtransClient.CoreApi({
        isProduction: this.isProduction,
        serverKey: this.serverKey,
        clientKey: this.clientKey
      });

      // Snap API for payment page
      this.snap = new midtransClient.Snap({
        isProduction: this.isProduction,
        serverKey: this.serverKey,
        clientKey: this.clientKey
      });

      // Iris API for payouts (optional)
      this.iris = new midtransClient.Iris({
        isProduction: this.isProduction,
        serverKey: process.env.MIDTRANS_IRIS_KEY || this.serverKey,
        clientKey: this.clientKey
      });

      logger.info('✅ Midtrans clients initialized successfully', {
        environment: this.isProduction ? 'production' : 'sandbox'
      });
    } catch (error) {
      logger.error('❌ Failed to initialize Midtrans clients', { error: error.message });
      throw error;
    }
  }

  // Payment method configurations for Indonesian market
  getPaymentMethods() {
    return {
      // Credit/Debit Cards
      credit_card: {
        enabled: true,
        secure: true,
        channel: 'migs',
        bank: 'bni',
        installment: {
          required: false,
          terms: {
            bni: [3, 6, 12],
            mandiri: [3, 6, 12],
            cimb: [3, 6, 12],
            bca: [3, 6, 12]
          }
        }
      },

      // Bank Transfer
      bank_transfer: {
        enabled: true,
        bank: ['bca', 'bni', 'bri', 'cimb', 'permata', 'mandiri'],
        va_numbers: true
      },

      // E-Wallets
      echannel: {
        enabled: true,
        bill_info1: 'Payment for Trading Platform',
        bill_info2: 'Subscription'
      },

      // Indonesian E-Wallets
      gopay: {
        enabled: true,
        enable_callback: true,
        callback_url: process.env.GOPAY_CALLBACK_URL
      },

      ovo: {
        enabled: true,
        enable_callback: true,
        callback_url: process.env.OVO_CALLBACK_URL
      },

      dana: {
        enabled: true,
        enable_callback: true,
        callback_url: process.env.DANA_CALLBACK_URL
      },

      linkaja: {
        enabled: true,
        enable_callback: true,
        callback_url: process.env.LINKAJA_CALLBACK_URL
      },

      shopeepay: {
        enabled: true,
        enable_callback: true,
        callback_url: process.env.SHOPEEPAY_CALLBACK_URL
      },

      // Convenience Store
      cstore: {
        enabled: true,
        store: 'indomaret',
        message: 'Trading Platform Payment'
      },

      // Cardless Credit
      akulaku: {
        enabled: true
      }
    };
  }

  // Indonesian-specific payment configuration
  getIndonesianConfig() {
    return {
      currency: 'IDR',
      country_code: 'ID',
      locale: 'id',
      timezone: 'Asia/Jakarta',

      // PCI DSS compliance settings
      security: {
        fraud_detection: true,
        secure_3d: true,
        whitelist_bins: [],
        blacklist_bins: []
      },

      // Indonesian regulatory compliance
      compliance: {
        customer_details_required: true,
        billing_address_required: true,
        shipping_address_required: false,
        item_details_required: true
      },

      // Webhook configuration
      webhooks: {
        notification_url: process.env.MIDTRANS_WEBHOOK_URL,
        finish_url: process.env.PAYMENT_FINISH_URL,
        unfinish_url: process.env.PAYMENT_UNFINISH_URL,
        error_url: process.env.PAYMENT_ERROR_URL
      }
    };
  }

  getCoreApi() {
    return this.coreApi;
  }

  getSnap() {
    return this.snap;
  }

  getIris() {
    return this.iris;
  }

  getEnvironment() {
    return {
      isProduction: this.isProduction,
      serverKey: this.serverKey ? '***' + this.serverKey.slice(-4) : 'not_set',
      clientKey: this.clientKey ? '***' + this.clientKey.slice(-4) : 'not_set'
    };
  }
}

module.exports = new MidtransConfig();