const mongoose = require('mongoose');

const paymentSchema = new mongoose.Schema({
  // Payment Identification
  orderId: {
    type: String,
    required: true,
    unique: true,
    index: true
  },
  transactionId: {
    type: String,
    sparse: true,
    index: true
  },
  midtransOrderId: {
    type: String,
    sparse: true,
    index: true
  },

  // User and Service Information
  userId: {
    type: String,
    required: true,
    index: true
  },
  subscriptionId: {
    type: String,
    sparse: true,
    index: true
  },
  planId: {
    type: String,
    sparse: true
  },

  // Payment Details
  amount: {
    type: Number,
    required: true,
    min: 0
  },
  currency: {
    type: String,
    required: true,
    default: 'IDR',
    enum: ['IDR', 'USD']
  },
  grossAmount: {
    type: Number,
    required: true
  },
  tax: {
    type: Number,
    default: 0
  },
  fee: {
    type: Number,
    default: 0
  },

  // Payment Method
  paymentType: {
    type: String,
    required: true,
    enum: [
      'credit_card', 'bank_transfer', 'echannel', 'bca_va', 'bni_va', 'bri_va',
      'permata_va', 'mandiri_va', 'cimb_va', 'gopay', 'ovo', 'dana', 'linkaja',
      'shopeepay', 'cstore', 'akulaku', 'qris'
    ]
  },
  paymentMethod: {
    type: String,
    sparse: true
  },

  // Status Tracking
  status: {
    type: String,
    required: true,
    default: 'pending',
    enum: [
      'pending', 'authorize', 'capture', 'settlement', 'deny', 'cancel',
      'expire', 'failure', 'refund', 'partial_refund', 'chargeback'
    ],
    index: true
  },
  fraudStatus: {
    type: String,
    enum: ['accept', 'deny', 'challenge'],
    sparse: true
  },

  // Customer Information (Indonesian compliance)
  customerDetails: {
    firstName: { type: String, required: true },
    lastName: { type: String },
    email: { type: String, required: true },
    phone: { type: String, required: true },
    billingAddress: {
      firstName: String,
      lastName: String,
      address: String,
      city: String,
      postalCode: String,
      phone: String,
      countryCode: { type: String, default: 'IDN' }
    },
    shippingAddress: {
      firstName: String,
      lastName: String,
      address: String,
      city: String,
      postalCode: String,
      phone: String,
      countryCode: { type: String, default: 'IDN' }
    }
  },

  // Item Details (Indonesian regulatory requirement)
  itemDetails: [{
    id: { type: String, required: true },
    price: { type: Number, required: true },
    quantity: { type: Number, required: true, default: 1 },
    name: { type: String, required: true },
    brand: String,
    category: String,
    merchantName: String
  }],

  // Subscription Specific
  subscriptionDetails: {
    planType: {
      type: String,
      enum: ['basic', 'premium', 'professional', 'enterprise']
    },
    billingCycle: {
      type: String,
      enum: ['monthly', 'quarterly', 'yearly']
    },
    startDate: Date,
    endDate: Date,
    isRecurring: { type: Boolean, default: false },
    nextBillingDate: Date
  },

  // Midtrans Response Data
  midtransResponse: {
    snapToken: String,
    snapRedirectUrl: String,
    transactionTime: Date,
    transactionStatus: String,
    statusMessage: String,
    merchantId: String,
    paymentChannel: String,
    bankCode: String,
    vaNumbers: [{
      bank: String,
      vaNumber: String
    }],
    cardToken: String,
    savedCardToken: String,
    installmentTerm: Number,
    approvalCode: String,
    signatureKey: String
  },

  // Webhook Data
  webhookData: [{
    timestamp: { type: Date, default: Date.now },
    data: mongoose.Schema.Types.Mixed,
    signature: String,
    processed: { type: Boolean, default: false }
  }],

  // Security and Compliance
  securityInfo: {
    ipAddress: String,
    userAgent: String,
    riskScore: Number,
    fraudCheck: {
      performed: { type: Boolean, default: false },
      result: String,
      details: mongoose.Schema.Types.Mixed
    }
  },

  // Metadata
  metadata: {
    type: mongoose.Schema.Types.Mixed,
    default: {}
  },

  // Timestamps
  createdAt: {
    type: Date,
    default: Date.now,
    index: true
  },
  updatedAt: {
    type: Date,
    default: Date.now
  },
  paidAt: Date,
  expiredAt: Date,
  refundedAt: Date,

  // Retry and Error Handling
  retryCount: {
    type: Number,
    default: 0
  },
  lastError: {
    code: String,
    message: String,
    timestamp: Date
  }
}, {
  timestamps: true,
  versionKey: false
});

// Indexes for performance
paymentSchema.index({ userId: 1, status: 1 });
paymentSchema.index({ subscriptionId: 1, status: 1 });
paymentSchema.index({ createdAt: -1 });
paymentSchema.index({ 'subscriptionDetails.nextBillingDate': 1 });
paymentSchema.index({ paymentType: 1, status: 1 });

// Virtual for display amount in Rupiah
paymentSchema.virtual('displayAmount').get(function() {
  if (this.currency === 'IDR') {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR'
    }).format(this.amount);
  }
  return this.amount;
});

// Instance methods
paymentSchema.methods.updateStatus = function(newStatus, metadata = {}) {
  this.status = newStatus;
  this.updatedAt = new Date();

  if (newStatus === 'settlement' || newStatus === 'capture') {
    this.paidAt = new Date();
  }

  if (metadata) {
    this.metadata = { ...this.metadata, ...metadata };
  }

  return this.save();
};

paymentSchema.methods.addWebhookData = function(webhookData, signature) {
  this.webhookData.push({
    data: webhookData,
    signature: signature,
    timestamp: new Date(),
    processed: false
  });
  return this.save();
};

paymentSchema.methods.isExpired = function() {
  return this.expiredAt && new Date() > this.expiredAt;
};

paymentSchema.methods.canRetry = function() {
  return this.retryCount < 3 && ['failure', 'deny'].includes(this.status);
};

// Static methods
paymentSchema.statics.findByUserId = function(userId, options = {}) {
  const query = { userId };
  return this.find(query)
    .sort({ createdAt: -1 })
    .limit(options.limit || 50)
    .skip(options.skip || 0);
};

paymentSchema.statics.findPendingSubscriptions = function() {
  return this.find({
    'subscriptionDetails.isRecurring': true,
    'subscriptionDetails.nextBillingDate': { $lte: new Date() },
    status: { $in: ['settlement', 'capture'] }
  });
};

paymentSchema.statics.getPaymentStats = function(userId, dateRange = {}) {
  const match = { userId };

  if (dateRange.start || dateRange.end) {
    match.createdAt = {};
    if (dateRange.start) match.createdAt.$gte = dateRange.start;
    if (dateRange.end) match.createdAt.$lte = dateRange.end;
  }

  return this.aggregate([
    { $match: match },
    {
      $group: {
        _id: '$status',
        count: { $sum: 1 },
        totalAmount: { $sum: '$amount' }
      }
    }
  ]);
};

// Pre-save middleware
paymentSchema.pre('save', function(next) {
  this.updatedAt = new Date();
  next();
});

module.exports = mongoose.model('Payment', paymentSchema);