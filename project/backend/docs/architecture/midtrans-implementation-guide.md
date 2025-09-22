# Midtrans Payment Gateway Implementation Guide

## Implementation Overview

This guide provides step-by-step implementation instructions for the unified Midtrans payment gateway, including code samples, configuration examples, and deployment procedures.

## Prerequisites

### 1. Midtrans Account Setup
- Create Midtrans merchant account
- Obtain Server Key and Client Key
- Configure webhook URLs
- Set up payment methods

### 2. Environment Configuration
```bash
# Midtrans Configuration
MIDTRANS_SERVER_KEY=SB-Mid-server-your-server-key
MIDTRANS_CLIENT_KEY=SB-Mid-client-your-client-key
MIDTRANS_IS_PRODUCTION=false
MIDTRANS_API_URL=https://api.sandbox.midtrans.com

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=payment_service
DB_USER=payment_user
DB_PASSWORD=secure_password

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=redis_password

# Service Configuration
PAYMENT_SERVICE_PORT=8080
WEBHOOK_SECRET=your-webhook-secret
JWT_SECRET=your-jwt-secret
```

## Core Service Implementation

### 1. Payment Service Bootstrap

**File: `/src/services/payment-service/index.js`**
```javascript
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const { createProxyMiddleware } = require('http-proxy-middleware');

const PaymentOrchestrator = require('./orchestrator/PaymentOrchestrator');
const SubscriptionManager = require('./subscription/SubscriptionManager');
const WebhookHandler = require('./webhook/WebhookHandler');
const MidtransClient = require('./clients/MidtransClient');
const DatabaseConnection = require('./database/Connection');
const RedisClient = require('./cache/RedisClient');

class PaymentService {
  constructor() {
    this.app = express();
    this.setupMiddleware();
    this.initializeServices();
    this.setupRoutes();
    this.setupErrorHandling();
  }

  setupMiddleware() {
    // Security middleware
    this.app.use(helmet());
    this.app.use(cors({
      origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'],
      methods: ['GET', 'POST', 'PUT', 'DELETE'],
      allowedHeaders: ['Content-Type', 'Authorization']
    }));

    // Rate limiting
    const limiter = rateLimit({
      windowMs: 15 * 60 * 1000, // 15 minutes
      max: 100, // limit each IP to 100 requests per windowMs
      message: 'Too many requests from this IP'
    });
    this.app.use('/api', limiter);

    // Body parsing
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true }));

    // Request logging
    this.app.use((req, res, next) => {
      console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
      next();
    });
  }

  async initializeServices() {
    // Database connection
    this.database = new DatabaseConnection();
    await this.database.connect();

    // Redis connection
    this.redis = new RedisClient();
    await this.redis.connect();

    // Midtrans client
    this.midtransClient = new MidtransClient({
      serverKey: process.env.MIDTRANS_SERVER_KEY,
      clientKey: process.env.MIDTRANS_CLIENT_KEY,
      isProduction: process.env.MIDTRANS_IS_PRODUCTION === 'true'
    });

    // Core services
    this.paymentOrchestrator = new PaymentOrchestrator(
      this.midtransClient,
      this.database,
      this.redis
    );

    this.subscriptionManager = new SubscriptionManager(
      this.paymentOrchestrator,
      this.database,
      this.redis
    );

    this.webhookHandler = new WebhookHandler(
      this.paymentOrchestrator,
      this.subscriptionManager,
      this.database
    );
  }

  setupRoutes() {
    // Health check
    this.app.get('/health', (req, res) => {
      res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: process.env.npm_package_version || '1.0.0'
      });
    });

    // Payment routes
    this.app.use('/api/v1/payments', require('./routes/payments')(this.paymentOrchestrator));

    // Subscription routes
    this.app.use('/api/v1/subscriptions', require('./routes/subscriptions')(this.subscriptionManager));

    // Webhook routes
    this.app.use('/api/v1/webhooks', require('./routes/webhooks')(this.webhookHandler));
  }

  setupErrorHandling() {
    // 404 handler
    this.app.use('*', (req, res) => {
      res.status(404).json({
        error: 'Route not found',
        path: req.originalUrl
      });
    });

    // Global error handler
    this.app.use((error, req, res, next) => {
      console.error('Global error handler:', error);
      res.status(error.statusCode || 500).json({
        error: error.message || 'Internal server error',
        ...(process.env.NODE_ENV === 'development' && { stack: error.stack })
      });
    });
  }

  async start() {
    const port = process.env.PAYMENT_SERVICE_PORT || 8080;

    this.server = this.app.listen(port, () => {
      console.log(`Payment service running on port ${port}`);
    });

    // Graceful shutdown
    process.on('SIGTERM', () => this.stop());
    process.on('SIGINT', () => this.stop());
  }

  async stop() {
    console.log('Shutting down payment service...');

    if (this.server) {
      this.server.close();
    }

    await this.database.disconnect();
    await this.redis.disconnect();

    process.exit(0);
  }
}

module.exports = PaymentService;

// Start service if called directly
if (require.main === module) {
  const service = new PaymentService();
  service.start().catch(console.error);
}
```

### 2. Midtrans Client Implementation

**File: `/src/services/payment-service/clients/MidtransClient.js`**
```javascript
const axios = require('axios');
const crypto = require('crypto');

class MidtransClient {
  constructor(config) {
    this.serverKey = config.serverKey;
    this.clientKey = config.clientKey;
    this.isProduction = config.isProduction;
    this.baseURL = this.isProduction
      ? 'https://api.midtrans.com'
      : 'https://api.sandbox.midtrans.com';
    this.snapURL = this.isProduction
      ? 'https://app.midtrans.com'
      : 'https://app.sandbox.midtrans.com';

    // Create axios instance with auth
    this.apiClient = axios.create({
      baseURL: this.baseURL,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Basic ${Buffer.from(this.serverKey + ':').toString('base64')}`
      },
      timeout: 30000
    });

    this.setupInterceptors();
  }

  setupInterceptors() {
    // Request interceptor
    this.apiClient.interceptors.request.use(
      (config) => {
        console.log(`Midtrans API Request: ${config.method.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.apiClient.interceptors.response.use(
      (response) => {
        console.log(`Midtrans API Response: ${response.status} ${response.config.url}`);
        return response;
      },
      (error) => {
        console.error('Midtrans API Error:', error.response?.data || error.message);
        return Promise.reject(this.formatError(error));
      }
    );
  }

  formatError(error) {
    if (error.response) {
      return {
        status: error.response.status,
        message: error.response.data?.error_messages?.[0] || error.response.data?.message || 'API Error',
        code: error.response.data?.status_code || error.response.status,
        details: error.response.data
      };
    }

    return {
      status: 500,
      message: error.message || 'Network Error',
      code: 'NETWORK_ERROR'
    };
  }

  async createSnapTransaction(transactionData) {
    try {
      const response = await this.apiClient.post('/v1/transactions', transactionData);

      return {
        token: response.data.token,
        redirectUrl: response.data.redirect_url,
        orderId: transactionData.transaction_details.order_id
      };
    } catch (error) {
      throw new Error(`Failed to create Snap transaction: ${error.message}`);
    }
  }

  async charge(chargeData) {
    try {
      const response = await this.apiClient.post('/v2/charge', chargeData);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to charge: ${error.message}`);
    }
  }

  async getTransactionStatus(orderId) {
    try {
      const response = await this.apiClient.get(`/v2/${orderId}/status`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to get transaction status: ${error.message}`);
    }
  }

  async cancelTransaction(orderId) {
    try {
      const response = await this.apiClient.post(`/v2/${orderId}/cancel`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to cancel transaction: ${error.message}`);
    }
  }

  async refundTransaction(orderId, refundData) {
    try {
      const response = await this.apiClient.post(`/v2/${orderId}/refund`, refundData);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to refund transaction: ${error.message}`);
    }
  }

  verifyNotificationSignature(notification) {
    const { order_id, status_code, gross_amount } = notification;
    const signatureKey = order_id + status_code + gross_amount + this.serverKey;
    const signature = crypto.createHash('sha512').update(signatureKey).digest('hex');

    return signature === notification.signature_key;
  }

  // Payment method specific implementations
  async createCreditCardPayment(paymentData) {
    const transactionData = {
      transaction_details: {
        order_id: paymentData.orderId,
        gross_amount: paymentData.amount
      },
      credit_card: {
        secure: true,
        authentication: true,
        save_card: paymentData.saveCard || false,
        type: paymentData.cardType || 'normal'
      },
      customer_details: paymentData.customerDetails,
      item_details: paymentData.items,
      custom_expiry: {
        expiry_duration: paymentData.expiryDuration || 60,
        unit: "minute"
      }
    };

    return await this.createSnapTransaction(transactionData);
  }

  async createBankTransferPayment(paymentData) {
    const chargeData = {
      transaction_details: {
        order_id: paymentData.orderId,
        gross_amount: paymentData.amount
      },
      payment_type: 'bank_transfer',
      bank_transfer: {
        bank: paymentData.bank
      },
      customer_details: paymentData.customerDetails,
      item_details: paymentData.items
    };

    return await this.charge(chargeData);
  }

  async createEWalletPayment(paymentData) {
    const { walletType } = paymentData;

    const chargeData = {
      transaction_details: {
        order_id: paymentData.orderId,
        gross_amount: paymentData.amount
      },
      payment_type: walletType,
      customer_details: paymentData.customerDetails,
      item_details: paymentData.items
    };

    // Add wallet-specific configurations
    switch (walletType) {
      case 'gopay':
        chargeData.gopay = {
          enable_callback: true,
          callback_url: paymentData.callbackUrl
        };
        break;
      case 'shopeepay':
        chargeData.shopeepay = {
          callback_url: paymentData.callbackUrl
        };
        break;
    }

    return await this.charge(chargeData);
  }

  async createVirtualAccountPayment(paymentData) {
    const chargeData = {
      transaction_details: {
        order_id: paymentData.orderId,
        gross_amount: paymentData.amount
      },
      payment_type: 'bank_transfer',
      bank_transfer: {
        bank: paymentData.bank,
        va_number: paymentData.vaNumber
      },
      customer_details: paymentData.customerDetails,
      item_details: paymentData.items,
      custom_expiry: {
        expiry_duration: paymentData.expiryDuration || 24,
        unit: "hour"
      }
    };

    return await this.charge(chargeData);
  }
}

module.exports = MidtransClient;
```

### 3. Payment Orchestrator Implementation

**File: `/src/services/payment-service/orchestrator/PaymentOrchestrator.js`**
```javascript
const { v4: uuidv4 } = require('uuid');
const PaymentMethodFactory = require('./PaymentMethodFactory');
const TransactionStateMachine = require('./TransactionStateMachine');

class PaymentOrchestrator {
  constructor(midtransClient, database, redis) {
    this.midtransClient = midtransClient;
    this.database = database;
    this.redis = redis;
    this.stateMachine = new TransactionStateMachine(database);
    this.paymentMethodFactory = new PaymentMethodFactory(midtransClient);
  }

  async createPayment(paymentRequest) {
    const {
      customerId,
      amount,
      currency = 'IDR',
      paymentMethod,
      subscriptionId,
      metadata = {}
    } = paymentRequest;

    // Generate unique order ID
    const orderId = this.generateOrderId();

    try {
      // Validate payment request
      await this.validatePaymentRequest(paymentRequest);

      // Create payment record
      const payment = await this.createPaymentRecord({
        orderId,
        customerId,
        amount,
        currency,
        paymentMethod,
        subscriptionId,
        metadata
      });

      // Get payment method handler
      const paymentHandler = this.paymentMethodFactory.createPaymentMethod(paymentMethod);

      // Create payment with Midtrans
      const midtransResponse = await paymentHandler.createPayment({
        orderId,
        amount,
        currency,
        customerDetails: await this.getCustomerDetails(customerId),
        items: this.formatItems(metadata.items),
        callbackUrl: `${process.env.BASE_URL}/api/v1/callbacks/${paymentMethod}`
      });

      // Update payment record with Midtrans response
      await this.updatePaymentRecord(payment.id, {
        midtransTransactionId: midtransResponse.transactionId,
        paymentUrl: midtransResponse.redirectUrl || midtransResponse.paymentUrl,
        token: midtransResponse.token,
        status: 'pending'
      });

      // Cache payment for quick access
      await this.cachePayment(orderId, payment);

      return {
        paymentId: payment.id,
        orderId,
        amount,
        currency,
        paymentUrl: midtransResponse.redirectUrl || midtransResponse.paymentUrl,
        token: midtransResponse.token,
        expiryTime: this.calculateExpiryTime(paymentMethod),
        supportedMethods: await this.getSupportedPaymentMethods(amount)
      };

    } catch (error) {
      console.error('Payment creation failed:', error);

      // Update payment status to failed if record was created
      if (orderId) {
        await this.updatePaymentStatus(orderId, 'failed', {
          errorMessage: error.message,
          errorCode: error.code
        });
      }

      throw error;
    }
  }

  async getPaymentStatus(paymentId) {
    try {
      // Try cache first
      const cachedPayment = await this.getCachedPayment(paymentId);
      if (cachedPayment && this.isCacheValid(cachedPayment)) {
        return cachedPayment;
      }

      // Get from database
      const payment = await this.getPaymentRecord(paymentId);
      if (!payment) {
        throw new Error('Payment not found');
      }

      // Get latest status from Midtrans if payment is not terminal
      if (!this.isTerminalStatus(payment.status)) {
        const midtransStatus = await this.midtransClient.getTransactionStatus(payment.orderId);

        // Update local status if different
        if (midtransStatus.transaction_status !== payment.status) {
          await this.updatePaymentStatus(
            payment.orderId,
            midtransStatus.transaction_status,
            {
              midtransData: midtransStatus,
              syncedAt: new Date()
            }
          );
          payment.status = midtransStatus.transaction_status;
        }
      }

      // Update cache
      await this.cachePayment(payment.orderId, payment);

      return {
        paymentId: payment.id,
        orderId: payment.orderId,
        status: payment.status,
        amount: payment.amount,
        currency: payment.currency,
        paymentMethod: payment.paymentMethod,
        createdAt: payment.createdAt,
        updatedAt: payment.updatedAt,
        metadata: payment.metadata
      };

    } catch (error) {
      console.error('Failed to get payment status:', error);
      throw error;
    }
  }

  async processRefund(paymentId, refundData) {
    const { amount, reason } = refundData;

    try {
      const payment = await this.getPaymentRecord(paymentId);
      if (!payment) {
        throw new Error('Payment not found');
      }

      if (payment.status !== 'completed') {
        throw new Error('Can only refund completed payments');
      }

      // Process refund with Midtrans
      const refundResponse = await this.midtransClient.refundTransaction(
        payment.orderId,
        {
          amount,
          reason
        }
      );

      // Create refund record
      const refund = await this.createRefundRecord({
        paymentId: payment.id,
        amount,
        reason,
        midtransRefundId: refundResponse.refund_id,
        status: refundResponse.status
      });

      // Update payment status
      const newStatus = amount >= payment.amount ? 'refunded' : 'partially_refunded';
      await this.updatePaymentStatus(payment.orderId, newStatus, {
        refundId: refund.id,
        refundAmount: amount,
        refundReason: reason
      });

      return {
        refundId: refund.id,
        status: refundResponse.status,
        amount,
        refundedAt: new Date()
      };

    } catch (error) {
      console.error('Refund processing failed:', error);
      throw error;
    }
  }

  async validatePaymentRequest(request) {
    const { customerId, amount, currency, paymentMethod } = request;

    // Validate required fields
    if (!customerId || !amount || !paymentMethod) {
      throw new Error('Missing required payment fields');
    }

    // Validate amount
    if (amount <= 0) {
      throw new Error('Payment amount must be positive');
    }

    // Validate currency
    if (currency && currency !== 'IDR') {
      throw new Error('Only IDR currency is supported');
    }

    // Validate payment method
    const supportedMethods = await this.getSupportedPaymentMethods(amount);
    if (!supportedMethods.includes(paymentMethod)) {
      throw new Error(`Payment method ${paymentMethod} not supported for amount ${amount}`);
    }

    // Validate customer exists
    const customer = await this.getCustomerDetails(customerId);
    if (!customer) {
      throw new Error('Customer not found');
    }

    return true;
  }

  generateOrderId() {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 8);
    return `PAY_${timestamp}_${random}`.toUpperCase();
  }

  calculateExpiryTime(paymentMethod) {
    const expiryMinutes = {
      credit_card: 60,
      bank_transfer: 1440, // 24 hours
      e_wallet: 60,
      virtual_account: 1440
    };

    const minutes = expiryMinutes[paymentMethod] || 60;
    return new Date(Date.now() + minutes * 60 * 1000).toISOString();
  }

  isTerminalStatus(status) {
    return ['completed', 'failed', 'cancelled', 'refunded'].includes(status);
  }

  async getSupportedPaymentMethods(amount) {
    const methods = ['credit_card', 'bank_transfer', 'virtual_account'];

    // E-wallets have lower limits
    if (amount <= 10000000) { // IDR 10 million
      methods.push('e_wallet');
    }

    return methods;
  }

  async getCustomerDetails(customerId) {
    // This would typically fetch from user service or database
    // For now, return mock data
    return {
      first_name: "Customer",
      last_name: customerId,
      email: `customer${customerId}@example.com`,
      phone: "+628123456789"
    };
  }

  formatItems(items) {
    if (!items || !Array.isArray(items)) {
      return [{
        id: "default",
        price: 1,
        quantity: 1,
        name: "Payment"
      }];
    }

    return items.map(item => ({
      id: item.id || 'item',
      price: item.price || 0,
      quantity: item.quantity || 1,
      name: item.name || 'Item'
    }));
  }

  // Database operations
  async createPaymentRecord(data) {
    const query = `
      INSERT INTO payments (
        id, order_id, customer_id, subscription_id, amount, currency,
        payment_method, status, metadata, created_at, updated_at
      ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(), NOW()
      ) RETURNING *
    `;

    const values = [
      uuidv4(),
      data.orderId,
      data.customerId,
      data.subscriptionId,
      data.amount,
      data.currency,
      data.paymentMethod,
      'initiated',
      JSON.stringify(data.metadata)
    ];

    const result = await this.database.query(query, values);
    return result.rows[0];
  }

  async updatePaymentRecord(paymentId, updates) {
    const setClause = Object.keys(updates)
      .map((key, index) => `${key} = $${index + 2}`)
      .join(', ');

    const query = `
      UPDATE payments
      SET ${setClause}, updated_at = NOW()
      WHERE id = $1
      RETURNING *
    `;

    const values = [paymentId, ...Object.values(updates)];
    const result = await this.database.query(query, values);
    return result.rows[0];
  }

  async getPaymentRecord(paymentId) {
    const query = 'SELECT * FROM payments WHERE id = $1 OR order_id = $1';
    const result = await this.database.query(query, [paymentId]);
    return result.rows[0];
  }

  async updatePaymentStatus(orderId, status, metadata = {}) {
    const query = `
      UPDATE payments
      SET status = $2, metadata = metadata || $3, updated_at = NOW()
      WHERE order_id = $1
      RETURNING *
    `;

    const result = await this.database.query(query, [
      orderId,
      status,
      JSON.stringify(metadata)
    ]);

    return result.rows[0];
  }

  // Cache operations
  async cachePayment(orderId, payment) {
    const key = `payment:${orderId}`;
    await this.redis.setex(key, 300, JSON.stringify(payment)); // 5 minutes cache
  }

  async getCachedPayment(paymentId) {
    const key = `payment:${paymentId}`;
    const cached = await this.redis.get(key);
    return cached ? JSON.parse(cached) : null;
  }

  isCacheValid(cachedPayment) {
    // Cache is valid for non-terminal statuses for 5 minutes
    if (this.isTerminalStatus(cachedPayment.status)) {
      return true; // Terminal statuses don't change
    }

    const cacheAge = Date.now() - new Date(cachedPayment.updatedAt).getTime();
    return cacheAge < 300000; // 5 minutes
  }
}

module.exports = PaymentOrchestrator;
```

### 4. Webhook Handler Implementation

**File: `/src/services/payment-service/webhook/WebhookHandler.js`**
```javascript
const crypto = require('crypto');

class WebhookHandler {
  constructor(paymentOrchestrator, subscriptionManager, database) {
    this.paymentOrchestrator = paymentOrchestrator;
    this.subscriptionManager = subscriptionManager;
    this.database = database;
    this.processedWebhooks = new Set();
  }

  async handleMidtransWebhook(webhookData, signature) {
    const webhookId = this.generateWebhookId(webhookData);

    try {
      // Check for duplicate webhook
      if (await this.isWebhookProcessed(webhookId)) {
        return { status: 'already_processed', webhookId };
      }

      // Verify webhook signature
      if (!this.verifyWebhookSignature(webhookData, signature)) {
        throw new Error('Invalid webhook signature');
      }

      // Store webhook event
      await this.storeWebhookEvent(webhookId, webhookData);

      // Process webhook based on transaction status
      const result = await this.processWebhookEvent(webhookData);

      // Mark webhook as processed
      await this.markWebhookProcessed(webhookId);

      return { status: 'success', result, webhookId };

    } catch (error) {
      console.error('Webhook processing failed:', error);

      // Store failed webhook for manual review
      await this.storeFailedWebhook(webhookId, webhookData, error.message);

      throw error;
    }
  }

  async processWebhookEvent(webhookData) {
    const {
      order_id,
      transaction_status,
      transaction_id,
      payment_type,
      gross_amount,
      fraud_status
    } = webhookData;

    console.log(`Processing webhook for order ${order_id} with status ${transaction_status}`);

    switch (transaction_status) {
      case 'capture':
      case 'settlement':
        return await this.handleSuccessfulPayment(webhookData);

      case 'pending':
        return await this.handlePendingPayment(webhookData);

      case 'deny':
      case 'cancel':
      case 'expire':
      case 'failure':
        return await this.handleFailedPayment(webhookData);

      default:
        console.warn(`Unknown transaction status: ${transaction_status}`);
        return { action: 'unknown_status', orderId: order_id };
    }
  }

  async handleSuccessfulPayment(webhookData) {
    const {
      order_id,
      transaction_id,
      payment_type,
      gross_amount,
      transaction_time,
      fraud_status
    } = webhookData;

    try {
      // Update payment status
      const payment = await this.paymentOrchestrator.updatePaymentStatus(
        order_id,
        'completed',
        {
          midtransTransactionId: transaction_id,
          paymentType: payment_type,
          settlementAmount: gross_amount,
          settlementTime: transaction_time,
          fraudStatus: fraud_status,
          webhookProcessedAt: new Date()
        }
      );

      // If this is a subscription payment, handle subscription renewal
      if (payment && payment.subscriptionId) {
        await this.subscriptionManager.handleSuccessfulRenewal(
          payment.subscriptionId,
          payment.id
        );
      }

      // Trigger success notifications
      await this.triggerPaymentSuccessNotifications(payment);

      return {
        action: 'payment_completed',
        orderId: order_id,
        paymentId: payment?.id,
        amount: gross_amount
      };

    } catch (error) {
      console.error('Failed to handle successful payment:', error);
      throw error;
    }
  }

  async handlePendingPayment(webhookData) {
    const { order_id, payment_type, va_numbers, bill_key, biller_code } = webhookData;

    try {
      const metadata = {
        paymentType: payment_type,
        webhookProcessedAt: new Date()
      };

      // Add payment method specific data
      if (va_numbers) {
        metadata.virtualAccountNumbers = va_numbers;
      }
      if (bill_key) {
        metadata.billKey = bill_key;
      }
      if (biller_code) {
        metadata.billerCode = biller_code;
      }

      await this.paymentOrchestrator.updatePaymentStatus(
        order_id,
        'pending',
        metadata
      );

      return {
        action: 'payment_pending',
        orderId: order_id,
        paymentInstructions: this.generatePaymentInstructions(webhookData)
      };

    } catch (error) {
      console.error('Failed to handle pending payment:', error);
      throw error;
    }
  }

  async handleFailedPayment(webhookData) {
    const {
      order_id,
      transaction_status,
      status_message,
      fraud_status
    } = webhookData;

    try {
      const payment = await this.paymentOrchestrator.updatePaymentStatus(
        order_id,
        'failed',
        {
          failureReason: status_message,
          failureStatus: transaction_status,
          fraudStatus: fraud_status,
          webhookProcessedAt: new Date()
        }
      );

      // If this is a subscription payment, handle dunning
      if (payment && payment.subscriptionId) {
        await this.subscriptionManager.handleFailedRenewal(
          payment.subscriptionId,
          payment.id,
          status_message
        );
      }

      // Trigger failure notifications
      await this.triggerPaymentFailureNotifications(payment, status_message);

      return {
        action: 'payment_failed',
        orderId: order_id,
        paymentId: payment?.id,
        reason: status_message
      };

    } catch (error) {
      console.error('Failed to handle failed payment:', error);
      throw error;
    }
  }

  verifyWebhookSignature(webhookData, receivedSignature) {
    const { order_id, status_code, gross_amount } = webhookData;
    const serverKey = process.env.MIDTRANS_SERVER_KEY;

    const signatureString = order_id + status_code + gross_amount + serverKey;
    const expectedSignature = crypto
      .createHash('sha512')
      .update(signatureString)
      .digest('hex');

    return crypto.timingSafeEqual(
      Buffer.from(receivedSignature, 'hex'),
      Buffer.from(expectedSignature, 'hex')
    );
  }

  generateWebhookId(webhookData) {
    const { order_id, transaction_status, gross_amount } = webhookData;
    const data = `${order_id}-${transaction_status}-${gross_amount}`;
    return crypto.createHash('md5').update(data).digest('hex');
  }

  generatePaymentInstructions(webhookData) {
    const { payment_type, va_numbers, bill_key, biller_code } = webhookData;

    switch (payment_type) {
      case 'bank_transfer':
        if (va_numbers) {
          return {
            type: 'virtual_account',
            instructions: va_numbers.map(va => ({
              bank: va.bank,
              vaNumber: va.va_number,
              message: `Transfer to Virtual Account ${va.va_number} (${va.bank.toUpperCase()})`
            }))
          };
        }
        break;

      case 'echannel':
        return {
          type: 'mandiri_bill',
          billKey: bill_key,
          billerCode: biller_code,
          message: `Pay via Mandiri Bill Payment with Biller Code: ${biller_code} and Bill Key: ${bill_key}`
        };

      case 'gopay':
        return {
          type: 'qr_code',
          message: 'Scan QR code with GoPay app or complete payment in the app'
        };

      default:
        return {
          type: 'generic',
          message: 'Complete payment using your chosen payment method'
        };
    }
  }

  async storeWebhookEvent(webhookId, webhookData) {
    const query = `
      INSERT INTO webhook_events (
        id, webhook_id, source, event_type, order_id,
        transaction_id, status, raw_payload, created_at
      ) VALUES (
        gen_random_uuid(), $1, 'midtrans', 'payment_notification',
        $2, $3, $4, $5, NOW()
      )
    `;

    const values = [
      webhookId,
      webhookData.order_id,
      webhookData.transaction_id,
      webhookData.transaction_status,
      JSON.stringify(webhookData)
    ];

    await this.database.query(query, values);
  }

  async isWebhookProcessed(webhookId) {
    const query = 'SELECT processed FROM webhook_events WHERE webhook_id = $1';
    const result = await this.database.query(query, [webhookId]);

    return result.rows.length > 0 && result.rows[0].processed;
  }

  async markWebhookProcessed(webhookId) {
    const query = `
      UPDATE webhook_events
      SET processed = true, processed_at = NOW()
      WHERE webhook_id = $1
    `;

    await this.database.query(query, [webhookId]);
  }

  async storeFailedWebhook(webhookId, webhookData, errorMessage) {
    const query = `
      INSERT INTO webhook_events (
        id, webhook_id, source, event_type, order_id,
        status, raw_payload, processed, error_message, created_at
      ) VALUES (
        gen_random_uuid(), $1, 'midtrans', 'payment_notification',
        $2, 'failed', $3, false, $4, NOW()
      )
    `;

    const values = [
      webhookId,
      webhookData.order_id || 'unknown',
      JSON.stringify(webhookData),
      errorMessage
    ];

    await this.database.query(query, values);
  }

  async triggerPaymentSuccessNotifications(payment) {
    // This would integrate with notification service
    console.log(`Payment success notification for payment ${payment.id}`);

    // Example: Send email, SMS, push notification
    // await this.notificationService.sendPaymentSuccess(payment.customerId, payment);
  }

  async triggerPaymentFailureNotifications(payment, reason) {
    // This would integrate with notification service
    console.log(`Payment failure notification for payment ${payment.id}: ${reason}`);

    // Example: Send failure notification
    // await this.notificationService.sendPaymentFailure(payment.customerId, payment, reason);
  }
}

module.exports = WebhookHandler;
```

### 5. Route Implementations

**File: `/src/services/payment-service/routes/payments.js`**
```javascript
const express = require('express');
const router = express.Router();
const { body, param, validationResult } = require('express-validator');
const authenticateToken = require('../middleware/auth');

module.exports = (paymentOrchestrator) => {
  // Create payment
  router.post('/',
    authenticateToken,
    [
      body('amount').isNumeric().isFloat({ min: 1 }),
      body('currency').optional().isIn(['IDR']),
      body('paymentMethod').isIn(['credit_card', 'bank_transfer', 'e_wallet', 'virtual_account']),
      body('customerId').notEmpty(),
      body('subscriptionId').optional().isUUID()
    ],
    async (req, res, next) => {
      try {
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
          return res.status(400).json({
            error: 'Validation failed',
            details: errors.array()
          });
        }

        const payment = await paymentOrchestrator.createPayment(req.body);

        res.status(201).json({
          status: 'success',
          data: payment
        });
      } catch (error) {
        next(error);
      }
    }
  );

  // Get payment status
  router.get('/:paymentId',
    authenticateToken,
    [
      param('paymentId').notEmpty()
    ],
    async (req, res, next) => {
      try {
        const payment = await paymentOrchestrator.getPaymentStatus(req.params.paymentId);

        res.json({
          status: 'success',
          data: payment
        });
      } catch (error) {
        if (error.message === 'Payment not found') {
          return res.status(404).json({
            error: 'Payment not found'
          });
        }
        next(error);
      }
    }
  );

  // Process refund
  router.post('/:paymentId/refund',
    authenticateToken,
    [
      param('paymentId').notEmpty(),
      body('amount').isNumeric().isFloat({ min: 1 }),
      body('reason').notEmpty()
    ],
    async (req, res, next) => {
      try {
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
          return res.status(400).json({
            error: 'Validation failed',
            details: errors.array()
          });
        }

        const refund = await paymentOrchestrator.processRefund(
          req.params.paymentId,
          req.body
        );

        res.json({
          status: 'success',
          data: refund
        });
      } catch (error) {
        next(error);
      }
    }
  );

  // Get supported payment methods
  router.get('/methods/supported',
    authenticateToken,
    async (req, res, next) => {
      try {
        const { amount = 100000 } = req.query;

        const methods = await paymentOrchestrator.getSupportedPaymentMethods(
          parseInt(amount)
        );

        res.json({
          status: 'success',
          data: {
            supportedMethods: methods,
            amount: parseInt(amount),
            currency: 'IDR'
          }
        });
      } catch (error) {
        next(error);
      }
    }
  );

  return router;
};
```

**File: `/src/services/payment-service/routes/webhooks.js`**
```javascript
const express = require('express');
const router = express.Router();
const crypto = require('crypto');

module.exports = (webhookHandler) => {
  // Midtrans webhook endpoint
  router.post('/midtrans',
    express.raw({ type: 'application/json' }),
    async (req, res, next) => {
      try {
        const signature = req.headers['x-signature'] || req.headers['signature'];
        const webhookData = JSON.parse(req.body.toString());

        // Process webhook
        const result = await webhookHandler.handleMidtransWebhook(
          webhookData,
          signature
        );

        res.json({
          status: 'success',
          message: 'Webhook processed successfully',
          data: result
        });

      } catch (error) {
        console.error('Webhook processing error:', error);

        // Always return 200 to Midtrans to prevent retries for invalid webhooks
        res.status(200).json({
          status: 'error',
          message: error.message
        });
      }
    }
  );

  return router;
};
```

## Deployment Configuration

### 1. Docker Configuration

**File: `/Dockerfile`**
```dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY src/ ./src/
COPY docs/ ./docs/

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S payment -u 1001
USER payment

EXPOSE 8080

CMD ["node", "src/services/payment-service/index.js"]
```

### 2. Kubernetes Deployment

**File: `/k8s/payment-service-deployment.yaml`**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-service
  labels:
    app: payment-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: payment-service
  template:
    metadata:
      labels:
        app: payment-service
    spec:
      containers:
      - name: payment-service
        image: payment-service:latest
        ports:
        - containerPort: 8080
        env:
        - name: NODE_ENV
          value: "production"
        - name: MIDTRANS_SERVER_KEY
          valueFrom:
            secretKeyRef:
              name: midtrans-secrets
              key: server-key
        - name: MIDTRANS_CLIENT_KEY
          valueFrom:
            secretKeyRef:
              name: midtrans-secrets
              key: client-key
        - name: DB_HOST
          value: "postgresql-service"
        - name: DB_NAME
          value: "payment_service"
        - name: DB_USER
          valueFrom:
            secretKeyRef:
              name: db-secrets
              key: username
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-secrets
              key: password
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: payment-service
spec:
  selector:
    app: payment-service
  ports:
  - port: 8080
    targetPort: 8080
  type: ClusterIP
```

This implementation guide provides a complete foundation for the unified Midtrans payment gateway, including all core components, API implementations, security measures, and deployment configurations.