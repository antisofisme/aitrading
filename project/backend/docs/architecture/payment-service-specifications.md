# Payment Service Technical Specifications

## Service Architecture Specifications

### 1. Payment Orchestrator Service

#### Component Overview
The Payment Orchestrator is the central coordination hub for all payment operations, implementing business logic and managing payment flows.

#### Technical Specifications

**Runtime Environment:**
- Node.js 18+ with Express.js framework
- TypeScript for type safety
- Docker containerization
- Kubernetes deployment

**Core Dependencies:**
```json
{
  "express": "^4.18.2",
  "axios": "^1.6.0",
  "redis": "^4.6.0",
  "pg": "^8.11.0",
  "joi": "^17.9.0",
  "winston": "^3.11.0",
  "bull": "^4.12.0",
  "crypto": "^1.0.1"
}
```

**Service Configuration:**
```javascript
const config = {
  service: {
    name: 'payment-orchestrator',
    port: 8080,
    version: '1.0.0'
  },
  midtrans: {
    serverKey: process.env.MIDTRANS_SERVER_KEY,
    clientKey: process.env.MIDTRANS_CLIENT_KEY,
    isProduction: process.env.NODE_ENV === 'production',
    apiUrl: process.env.MIDTRANS_API_URL || 'https://api.sandbox.midtrans.com'
  },
  database: {
    host: process.env.DB_HOST,
    port: process.env.DB_PORT,
    database: process.env.DB_NAME,
    username: process.env.DB_USER,
    password: process.env.DB_PASSWORD
  },
  redis: {
    host: process.env.REDIS_HOST,
    port: process.env.REDIS_PORT,
    password: process.env.REDIS_PASSWORD
  }
};
```

#### API Endpoints

**1. Create Payment Transaction**
```javascript
POST /api/v1/payments
Content-Type: application/json
Authorization: Bearer {jwt_token}

Request Body:
{
  "amount": 99000,
  "currency": "IDR",
  "paymentMethod": "credit_card", // credit_card, bank_transfer, e_wallet, virtual_account
  "customerId": "customer_123",
  "orderId": "order_456",
  "subscriptionId": "sub_789", // optional for subscription payments
  "metadata": {
    "description": "Premium subscription payment",
    "items": [
      {
        "id": "premium_plan",
        "price": 99000,
        "quantity": 1,
        "name": "Premium Trading Plan"
      }
    ]
  }
}

Response:
{
  "status": "success",
  "data": {
    "paymentId": "pay_123456789",
    "orderId": "order_456",
    "amount": 99000,
    "currency": "IDR",
    "paymentUrl": "https://app.sandbox.midtrans.com/snap/v1/transactions/...",
    "token": "snap_token_123",
    "expiryTime": "2024-09-22T11:30:00Z",
    "paymentMethods": ["credit_card", "bank_transfer", "e_wallet"]
  }
}
```

**2. Get Payment Status**
```javascript
GET /api/v1/payments/{paymentId}
Authorization: Bearer {jwt_token}

Response:
{
  "status": "success",
  "data": {
    "paymentId": "pay_123456789",
    "orderId": "order_456",
    "transactionStatus": "settlement", // pending, settlement, capture, deny, cancel, expire, failure
    "paymentType": "credit_card",
    "amount": 99000,
    "currency": "IDR",
    "transactionTime": "2024-09-22T10:30:00Z",
    "settlementTime": "2024-09-22T10:32:00Z",
    "fraudStatus": "accept", // accept, challenge, deny
    "metadata": {
      "cardType": "visa",
      "bank": "bni",
      "lastFourDigits": "1234"
    }
  }
}
```

#### Business Logic Implementation

**Payment Method Selection Logic:**
```javascript
class PaymentMethodSelector {
  selectOptimalMethod(amount, customerPreferences, availableMethods) {
    const criteria = {
      cost: this.calculateTransactionCost(amount, availableMethods),
      reliability: this.getMethodReliability(availableMethods),
      userPreference: customerPreferences.preferredMethod,
      amountLimits: this.checkAmountLimits(amount, availableMethods)
    };

    return this.rankMethods(availableMethods, criteria);
  }

  calculateTransactionCost(amount, methods) {
    const costs = {
      credit_card: amount * 0.029 + 2000, // 2.9% + IDR 2,000
      bank_transfer: 4000, // Flat IDR 4,000
      e_wallet: amount * 0.015, // 1.5%
      virtual_account: 4000 // Flat IDR 4,000
    };

    return methods.map(method => ({
      method,
      cost: costs[method] || 0
    }));
  }
}
```

### 2. Subscription Manager Service

#### Component Overview
Manages recurring payments, subscription lifecycles, and billing cycles with automated dunning management.

#### Technical Specifications

**Subscription State Machine:**
```javascript
const subscriptionStates = {
  ACTIVE: 'active',
  PAST_DUE: 'past_due',
  CANCELED: 'canceled',
  INCOMPLETE: 'incomplete',
  INCOMPLETE_EXPIRED: 'incomplete_expired',
  TRIALING: 'trialing',
  UNPAID: 'unpaid'
};

const stateTransitions = {
  [subscriptionStates.TRIALING]: [subscriptionStates.ACTIVE, subscriptionStates.PAST_DUE],
  [subscriptionStates.ACTIVE]: [subscriptionStates.PAST_DUE, subscriptionStates.CANCELED],
  [subscriptionStates.PAST_DUE]: [subscriptionStates.ACTIVE, subscriptionStates.CANCELED, subscriptionStates.UNPAID],
  [subscriptionStates.INCOMPLETE]: [subscriptionStates.ACTIVE, subscriptionStates.INCOMPLETE_EXPIRED],
  [subscriptionStates.UNPAID]: [subscriptionStates.CANCELED]
};
```

#### API Endpoints

**1. Create Subscription**
```javascript
POST /api/v1/subscriptions
Content-Type: application/json
Authorization: Bearer {jwt_token}

Request Body:
{
  "customerId": "customer_123",
  "planId": "premium_monthly",
  "paymentMethodId": "pm_123",
  "trialPeriodDays": 7,
  "couponId": "DISCOUNT20", // optional
  "metadata": {
    "source": "web",
    "campaign": "summer_promo"
  }
}

Response:
{
  "status": "success",
  "data": {
    "subscriptionId": "sub_123456789",
    "customerId": "customer_123",
    "planId": "premium_monthly",
    "status": "trialing",
    "currentPeriodStart": "2024-09-22T10:30:00Z",
    "currentPeriodEnd": "2024-10-22T10:30:00Z",
    "trialEnd": "2024-09-29T10:30:00Z",
    "amount": 99000,
    "currency": "IDR",
    "interval": "month",
    "nextPaymentDate": "2024-09-29T10:30:00Z"
  }
}
```

**2. Update Subscription**
```javascript
PUT /api/v1/subscriptions/{subscriptionId}
Content-Type: application/json
Authorization: Bearer {jwt_token}

Request Body:
{
  "planId": "enterprise_monthly", // plan upgrade/downgrade
  "paymentMethodId": "pm_456", // change payment method
  "prorationBehavior": "create_prorations", // create_prorations, none, always_invoice
  "effectiveDate": "2024-10-01T00:00:00Z" // when change takes effect
}

Response:
{
  "status": "success",
  "data": {
    "subscriptionId": "sub_123456789",
    "changes": {
      "previousPlan": "premium_monthly",
      "newPlan": "enterprise_monthly",
      "prorationAmount": 133000,
      "effectiveDate": "2024-10-01T00:00:00Z"
    },
    "nextInvoice": {
      "amount": 133000,
      "dueDate": "2024-10-01T00:00:00Z",
      "description": "Proration for plan upgrade"
    }
  }
}
```

#### Recurring Payment Processing

**Subscription Renewal Scheduler:**
```javascript
class SubscriptionScheduler {
  constructor(paymentOrchestrator, notificationService) {
    this.paymentOrchestrator = paymentOrchestrator;
    this.notificationService = notificationService;
    this.queue = new Bull('subscription-renewal');
  }

  async scheduleRenewal(subscription) {
    const renewalDate = subscription.currentPeriodEnd;
    const jobOptions = {
      delay: new Date(renewalDate).getTime() - Date.now(),
      attempts: 3,
      backoff: {
        type: 'exponential',
        delay: 60000 // 1 minute
      }
    };

    await this.queue.add('process-renewal', {
      subscriptionId: subscription.id,
      customerId: subscription.customerId,
      amount: subscription.amount,
      paymentMethodId: subscription.paymentMethodId
    }, jobOptions);
  }

  async processRenewal(job) {
    const { subscriptionId, customerId, amount, paymentMethodId } = job.data;

    try {
      const paymentResult = await this.paymentOrchestrator.createPayment({
        customerId,
        amount,
        paymentMethodId,
        subscriptionId,
        type: 'subscription_renewal'
      });

      if (paymentResult.status === 'success') {
        await this.updateSubscriptionStatus(subscriptionId, 'active');
        await this.scheduleNextRenewal(subscriptionId);
        await this.notificationService.sendRenewalSuccess(customerId);
      } else {
        await this.handleRenewalFailure(subscriptionId, paymentResult);
      }
    } catch (error) {
      await this.handleRenewalError(subscriptionId, error);
    }
  }
}
```

**Dunning Management System:**
```javascript
class DunningManager {
  constructor() {
    this.dunningSchedule = [
      { days: 1, action: 'email_reminder' },
      { days: 3, action: 'email_warning' },
      { days: 7, action: 'email_final_notice' },
      { days: 10, action: 'suspend_service' },
      { days: 30, action: 'cancel_subscription' }
    ];
  }

  async handleFailedPayment(subscriptionId, failureReason) {
    const subscription = await this.getSubscription(subscriptionId);

    // Update subscription status
    await this.updateSubscriptionStatus(subscriptionId, 'past_due');

    // Schedule dunning actions
    for (const step of this.dunningSchedule) {
      await this.scheduleDunningAction(subscriptionId, step);
    }

    // Immediate notification
    await this.notificationService.sendPaymentFailureNotification(
      subscription.customerId,
      failureReason
    );
  }

  async scheduleDunningAction(subscriptionId, step) {
    const delay = step.days * 24 * 60 * 60 * 1000; // Convert days to milliseconds

    await this.queue.add('dunning-action', {
      subscriptionId,
      action: step.action,
      scheduledFor: new Date(Date.now() + delay)
    }, { delay });
  }
}
```

### 3. Transaction Coordinator Service

#### Component Overview
Manages transaction states, provides real-time tracking, and handles reconciliation with Midtrans.

#### Technical Specifications

**Transaction State Management:**
```javascript
const transactionStates = {
  INITIATED: 'initiated',
  PENDING: 'pending',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled',
  REFUNDED: 'refunded',
  PARTIALLY_REFUNDED: 'partially_refunded'
};

class TransactionStateMachine {
  constructor() {
    this.transitions = {
      [transactionStates.INITIATED]: [transactionStates.PENDING, transactionStates.FAILED],
      [transactionStates.PENDING]: [transactionStates.PROCESSING, transactionStates.FAILED, transactionStates.CANCELLED],
      [transactionStates.PROCESSING]: [transactionStates.COMPLETED, transactionStates.FAILED],
      [transactionStates.COMPLETED]: [transactionStates.REFUNDED, transactionStates.PARTIALLY_REFUNDED],
      [transactionStates.FAILED]: [], // Terminal state
      [transactionStates.CANCELLED]: [], // Terminal state
      [transactionStates.REFUNDED]: [], // Terminal state
      [transactionStates.PARTIALLY_REFUNDED]: [transactionStates.REFUNDED]
    };
  }

  canTransition(fromState, toState) {
    return this.transitions[fromState]?.includes(toState) || false;
  }

  async transitionState(transactionId, newState, metadata = {}) {
    const transaction = await this.getTransaction(transactionId);

    if (!this.canTransition(transaction.status, newState)) {
      throw new Error(`Invalid state transition from ${transaction.status} to ${newState}`);
    }

    const updatedTransaction = await this.updateTransaction(transactionId, {
      status: newState,
      statusUpdatedAt: new Date(),
      metadata: { ...transaction.metadata, ...metadata }
    });

    // Emit state change event
    await this.eventEmitter.emit('transaction.state.changed', {
      transactionId,
      previousState: transaction.status,
      newState,
      timestamp: new Date(),
      metadata
    });

    return updatedTransaction;
  }
}
```

#### Real-time Transaction Tracking

**WebSocket Integration:**
```javascript
class TransactionTracker {
  constructor(websocketServer) {
    this.ws = websocketServer;
    this.subscribedClients = new Map();
  }

  subscribeToTransaction(clientId, transactionId) {
    if (!this.subscribedClients.has(transactionId)) {
      this.subscribedClients.set(transactionId, new Set());
    }
    this.subscribedClients.get(transactionId).add(clientId);
  }

  async broadcastTransactionUpdate(transactionId, update) {
    const subscribers = this.subscribedClients.get(transactionId);
    if (subscribers) {
      const message = {
        type: 'transaction_update',
        transactionId,
        data: update,
        timestamp: new Date().toISOString()
      };

      subscribers.forEach(clientId => {
        this.ws.send(clientId, JSON.stringify(message));
      });
    }
  }

  async handleTransactionStatusChange(event) {
    await this.broadcastTransactionUpdate(event.transactionId, {
      status: event.newState,
      previousStatus: event.previousState,
      metadata: event.metadata
    });
  }
}
```

### 4. Webhook Handler Service

#### Component Overview
Processes webhooks from Midtrans, ensures idempotency, and triggers appropriate business logic.

#### Technical Specifications

**Webhook Security:**
```javascript
class WebhookSecurity {
  constructor(serverKey) {
    this.serverKey = serverKey;
  }

  validateSignature(payload, signature) {
    const expectedSignature = crypto
      .createHmac('sha512', this.serverKey)
      .update(payload)
      .digest('hex');

    return crypto.timingSafeEqual(
      Buffer.from(signature, 'hex'),
      Buffer.from(expectedSignature, 'hex')
    );
  }

  verifyWebhookAuth(orderId, statusCode, grossAmount, serverKey) {
    const signatureString = orderId + statusCode + grossAmount + serverKey;
    return crypto.createHash('sha512').update(signatureString).digest('hex');
  }
}
```

**Webhook Processing:**
```javascript
class WebhookProcessor {
  constructor(transactionCoordinator, subscriptionManager) {
    this.transactionCoordinator = transactionCoordinator;
    this.subscriptionManager = subscriptionManager;
    this.processedWebhooks = new Set(); // For idempotency
  }

  async processWebhook(webhookData) {
    const webhookId = this.generateWebhookId(webhookData);

    // Check idempotency
    if (this.processedWebhooks.has(webhookId)) {
      return { status: 'already_processed', webhookId };
    }

    try {
      // Validate webhook signature
      if (!this.validateWebhook(webhookData)) {
        throw new Error('Invalid webhook signature');
      }

      // Process based on transaction status
      const result = await this.processTransactionStatus(webhookData);

      // Mark as processed
      this.processedWebhooks.add(webhookId);

      return { status: 'success', result, webhookId };
    } catch (error) {
      console.error('Webhook processing failed:', error);
      throw error;
    }
  }

  async processTransactionStatus(webhookData) {
    const { order_id, transaction_status, payment_type, gross_amount } = webhookData;

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
        throw new Error(`Unknown transaction status: ${transaction_status}`);
    }
  }

  async handleSuccessfulPayment(webhookData) {
    const { order_id, transaction_id, payment_type, gross_amount } = webhookData;

    // Update transaction status
    await this.transactionCoordinator.transitionState(
      order_id,
      transactionStates.COMPLETED,
      {
        midtransTransactionId: transaction_id,
        paymentType: payment_type,
        settlementAmount: gross_amount,
        settlementTime: new Date()
      }
    );

    // Check if this is a subscription payment
    const transaction = await this.transactionCoordinator.getTransaction(order_id);
    if (transaction.subscriptionId) {
      await this.subscriptionManager.handleSuccessfulRenewal(transaction.subscriptionId);
    }

    return { action: 'payment_completed', orderId: order_id };
  }
}
```

### 5. Payment Method Abstraction Layer

#### Component Overview
Provides a uniform interface for all payment methods while handling method-specific logic.

#### Technical Specifications

**Payment Method Factory:**
```javascript
class PaymentMethodFactory {
  static createPaymentMethod(type, config) {
    switch (type) {
      case 'credit_card':
        return new CreditCardPayment(config);
      case 'bank_transfer':
        return new BankTransferPayment(config);
      case 'e_wallet':
        return new EWalletPayment(config);
      case 'virtual_account':
        return new VirtualAccountPayment(config);
      default:
        throw new Error(`Unsupported payment method: ${type}`);
    }
  }
}

// Base Payment Method Interface
class PaymentMethod {
  async createPayment(params) {
    throw new Error('createPayment method must be implemented');
  }

  async getPaymentStatus(transactionId) {
    throw new Error('getPaymentStatus method must be implemented');
  }

  async cancelPayment(transactionId) {
    throw new Error('cancelPayment method must be implemented');
  }

  validateAmount(amount) {
    return amount > 0 && amount <= this.getMaxAmount();
  }

  getMaxAmount() {
    return 50000000; // IDR 50 million default
  }
}
```

**Credit Card Payment Implementation:**
```javascript
class CreditCardPayment extends PaymentMethod {
  constructor(midtransClient) {
    super();
    this.client = midtransClient;
    this.supportedCards = ['visa', 'mastercard', 'jcb', 'amex'];
  }

  async createPayment(params) {
    const { amount, currency, orderId, customerDetails, items } = params;

    const paymentData = {
      transaction_details: {
        order_id: orderId,
        gross_amount: amount
      },
      credit_card: {
        secure: true,
        authentication: true,
        save_card: false
      },
      customer_details: customerDetails,
      item_details: items,
      custom_expiry: {
        expiry_duration: 60,
        unit: "minute"
      }
    };

    return await this.client.createSnapTransaction(paymentData);
  }

  getMaxAmount() {
    return 50000000; // IDR 50 million for credit cards
  }

  getSupportedCurrencies() {
    return ['IDR'];
  }
}
```

**E-Wallet Payment Implementation:**
```javascript
class EWalletPayment extends PaymentMethod {
  constructor(midtransClient) {
    super();
    this.client = midtransClient;
    this.supportedWallets = ['gopay', 'ovo', 'dana', 'linkaja', 'shopeepay'];
  }

  async createPayment(params) {
    const { amount, currency, orderId, customerDetails, walletType } = params;

    if (!this.supportedWallets.includes(walletType)) {
      throw new Error(`Unsupported e-wallet type: ${walletType}`);
    }

    const paymentData = {
      transaction_details: {
        order_id: orderId,
        gross_amount: amount
      },
      payment_type: walletType,
      customer_details: customerDetails
    };

    // Add wallet-specific configurations
    if (walletType === 'gopay') {
      paymentData.gopay = {
        enable_callback: true,
        callback_url: `${process.env.BASE_URL}/api/v1/callbacks/gopay`
      };
    }

    return await this.client.charge(paymentData);
  }

  getMaxAmount() {
    return 10000000; // IDR 10 million for e-wallets
  }
}
```

## Database Schema

### Core Tables

**Payments Table:**
```sql
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id VARCHAR(255) UNIQUE NOT NULL,
    customer_id VARCHAR(255) NOT NULL,
    subscription_id UUID REFERENCES subscriptions(id),
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'IDR',
    payment_method VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    midtrans_transaction_id VARCHAR(255),
    payment_type VARCHAR(50),
    fraud_status VARCHAR(20),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    settled_at TIMESTAMP WITH TIME ZONE,

    INDEX idx_payments_customer_id (customer_id),
    INDEX idx_payments_subscription_id (subscription_id),
    INDEX idx_payments_status (status),
    INDEX idx_payments_created_at (created_at)
);
```

**Subscriptions Table:**
```sql
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id VARCHAR(255) NOT NULL,
    plan_id VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    current_period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    current_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    trial_start TIMESTAMP WITH TIME ZONE,
    trial_end TIMESTAMP WITH TIME ZONE,
    cancel_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'IDR',
    interval_unit VARCHAR(20) NOT NULL, -- month, year
    interval_count INTEGER DEFAULT 1,
    payment_method_id VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    INDEX idx_subscriptions_customer_id (customer_id),
    INDEX idx_subscriptions_status (status),
    INDEX idx_subscriptions_period_end (current_period_end)
);
```

**Webhook Events Table:**
```sql
CREATE TABLE webhook_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    webhook_id VARCHAR(255) UNIQUE NOT NULL,
    source VARCHAR(50) NOT NULL, -- 'midtrans'
    event_type VARCHAR(100) NOT NULL,
    order_id VARCHAR(255),
    transaction_id VARCHAR(255),
    status VARCHAR(50),
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP WITH TIME ZONE,
    raw_payload JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    INDEX idx_webhook_events_webhook_id (webhook_id),
    INDEX idx_webhook_events_order_id (order_id),
    INDEX idx_webhook_events_processed (processed)
);
```

This specification provides a comprehensive technical foundation for implementing the unified Midtrans payment gateway architecture with all necessary components, APIs, and database structures.