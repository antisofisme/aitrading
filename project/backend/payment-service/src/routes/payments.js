const express = require('express');
const PaymentController = require('../controllers/PaymentController');
const security = require('../middleware/security');
const validation = require('../middleware/validation');

const router = express.Router();

/**
 * Payment Routes
 */

// Create new payment
router.post('/',
  security.paymentRateLimit,
  security.authenticateToken,
  security.validateSensitiveInput,
  validation.validatePaymentCreation,
  validation.validateIndonesianCompliance,
  validation.validateSecurity,
  PaymentController.createPayment
);

// Get payment details
router.get('/:orderId',
  security.apiRateLimit,
  validation.validateOrderId,
  PaymentController.getPayment
);

// Get user payment history
router.get('/user/history',
  security.apiRateLimit,
  security.authenticateToken,
  validation.validatePagination,
  validation.validateDateRange,
  PaymentController.getUserPayments
);

// Get payment statistics
router.get('/user/stats',
  security.apiRateLimit,
  security.authenticateToken,
  validation.validateDateRange,
  PaymentController.getPaymentStats
);

// Cancel payment
router.put('/:orderId/cancel',
  security.paymentRateLimit,
  security.authenticateToken,
  validation.validateOrderId,
  validation.validatePaymentCancellation,
  PaymentController.cancelPayment
);

// Check payment status
router.get('/:orderId/status',
  security.apiRateLimit,
  validation.validateOrderId,
  PaymentController.checkPaymentStatus
);

// Refund payment (admin only)
router.post('/:orderId/refund',
  security.paymentRateLimit,
  security.authenticateToken,
  security.requireAdmin,
  security.ipWhitelist,
  validation.validateOrderId,
  validation.validatePaymentRefund,
  PaymentController.refundPayment
);

// Get available payment methods
router.get('/methods/available',
  security.apiRateLimit,
  PaymentController.getPaymentMethods
);

// Process webhook
router.post('/webhook',
  security.webhookRateLimit,
  security.verifyWebhookSignature,
  validation.validateWebhook,
  PaymentController.processWebhook
);

module.exports = router;