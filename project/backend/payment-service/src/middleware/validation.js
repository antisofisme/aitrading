const { body, param, query } = require('express-validator');

/**
 * Validation middleware for payment service endpoints
 */

/**
 * Payment creation validation
 */
const validatePaymentCreation = [
  body('amount')
    .isNumeric()
    .withMessage('Amount must be a number')
    .isFloat({ min: 1000 }) // Minimum IDR 1,000
    .withMessage('Amount must be at least IDR 1,000')
    .isFloat({ max: 1000000000 }) // Maximum IDR 1 billion
    .withMessage('Amount cannot exceed IDR 1,000,000,000'),

  body('currency')
    .optional()
    .isIn(['IDR', 'USD'])
    .withMessage('Currency must be IDR or USD'),

  body('paymentType')
    .optional()
    .isIn([
      'credit_card', 'bank_transfer', 'echannel', 'bca_va', 'bni_va', 'bri_va',
      'permata_va', 'mandiri_va', 'cimb_va', 'gopay', 'ovo', 'dana', 'linkaja',
      'shopeepay', 'cstore', 'akulaku', 'qris'
    ])
    .withMessage('Invalid payment type'),

  body('paymentMethods')
    .optional()
    .isArray()
    .withMessage('Payment methods must be an array'),

  body('customerDetails.firstName')
    .notEmpty()
    .withMessage('Customer first name is required')
    .isLength({ max: 50 })
    .withMessage('First name cannot exceed 50 characters')
    .matches(/^[a-zA-Z\s]+$/)
    .withMessage('First name can only contain letters and spaces'),

  body('customerDetails.lastName')
    .optional()
    .isLength({ max: 50 })
    .withMessage('Last name cannot exceed 50 characters')
    .matches(/^[a-zA-Z\s]*$/)
    .withMessage('Last name can only contain letters and spaces'),

  body('customerDetails.email')
    .isEmail()
    .withMessage('Valid email is required')
    .normalizeEmail(),

  body('customerDetails.phone')
    .matches(/^\+?[1-9]\d{1,14}$/)
    .withMessage('Valid phone number is required (E.164 format)')
    .isLength({ min: 10, max: 15 })
    .withMessage('Phone number must be between 10-15 digits'),

  body('customerDetails.billingAddress.address')
    .optional()
    .isLength({ max: 255 })
    .withMessage('Address cannot exceed 255 characters'),

  body('customerDetails.billingAddress.city')
    .optional()
    .isLength({ max: 50 })
    .withMessage('City cannot exceed 50 characters')
    .matches(/^[a-zA-Z\s]+$/)
    .withMessage('City can only contain letters and spaces'),

  body('customerDetails.billingAddress.postalCode')
    .optional()
    .matches(/^\d{5}$/)
    .withMessage('Indonesian postal code must be 5 digits'),

  body('itemDetails')
    .optional()
    .isArray()
    .withMessage('Item details must be an array'),

  body('itemDetails.*.id')
    .if(body('itemDetails').exists())
    .notEmpty()
    .withMessage('Item ID is required'),

  body('itemDetails.*.name')
    .if(body('itemDetails').exists())
    .notEmpty()
    .withMessage('Item name is required')
    .isLength({ max: 50 })
    .withMessage('Item name cannot exceed 50 characters'),

  body('itemDetails.*.price')
    .if(body('itemDetails').exists())
    .isNumeric()
    .withMessage('Item price must be a number')
    .isFloat({ min: 0 })
    .withMessage('Item price must be positive'),

  body('itemDetails.*.quantity')
    .if(body('itemDetails').exists())
    .isInt({ min: 1 })
    .withMessage('Item quantity must be at least 1'),

  body('subscriptionId')
    .optional()
    .isUUID()
    .withMessage('Subscription ID must be a valid UUID'),

  body('planId')
    .optional()
    .isIn(['basic', 'premium', 'professional', 'enterprise'])
    .withMessage('Invalid plan ID'),

  body('metadata.billingCycle')
    .if(body('planId').exists())
    .isIn(['monthly', 'quarterly', 'yearly'])
    .withMessage('Invalid billing cycle'),

  body('metadata.startDate')
    .optional()
    .isISO8601()
    .withMessage('Start date must be a valid ISO 8601 date'),

  body('metadata.customExpiry.duration')
    .optional()
    .isInt({ min: 1, max: 1440 })
    .withMessage('Expiry duration must be between 1 and 1440 minutes'),

  body('metadata.customExpiry.unit')
    .optional()
    .isIn(['minute', 'hour', 'day'])
    .withMessage('Expiry unit must be minute, hour, or day')
];

/**
 * Order ID parameter validation
 */
const validateOrderId = [
  param('orderId')
    .matches(/^[A-Z0-9\-]+$/)
    .withMessage('Invalid order ID format')
    .isLength({ min: 5, max: 50 })
    .withMessage('Order ID must be between 5-50 characters')
];

/**
 * Pagination validation
 */
const validatePagination = [
  query('page')
    .optional()
    .isInt({ min: 1 })
    .withMessage('Page must be a positive integer'),

  query('limit')
    .optional()
    .isInt({ min: 1, max: 100 })
    .withMessage('Limit must be between 1 and 100'),

  query('status')
    .optional()
    .isIn([
      'pending', 'authorize', 'capture', 'settlement', 'deny', 'cancel',
      'expire', 'failure', 'refund', 'partial_refund', 'chargeback'
    ])
    .withMessage('Invalid status filter'),

  query('paymentType')
    .optional()
    .isIn([
      'credit_card', 'bank_transfer', 'echannel', 'bca_va', 'bni_va', 'bri_va',
      'permata_va', 'mandiri_va', 'cimb_va', 'gopay', 'ovo', 'dana', 'linkaja',
      'shopeepay', 'cstore', 'akulaku', 'qris'
    ])
    .withMessage('Invalid payment type filter'),

  query('dateFrom')
    .optional()
    .isISO8601()
    .withMessage('Date from must be a valid ISO 8601 date'),

  query('dateTo')
    .optional()
    .isISO8601()
    .withMessage('Date to must be a valid ISO 8601 date')
];

/**
 * Payment cancellation validation
 */
const validatePaymentCancellation = [
  body('reason')
    .optional()
    .isLength({ max: 255 })
    .withMessage('Cancellation reason cannot exceed 255 characters')
    .trim()
];

/**
 * Payment refund validation
 */
const validatePaymentRefund = [
  body('amount')
    .optional()
    .isNumeric()
    .withMessage('Refund amount must be a number')
    .isFloat({ min: 1 })
    .withMessage('Refund amount must be positive'),

  body('reason')
    .notEmpty()
    .withMessage('Refund reason is required')
    .isLength({ max: 255 })
    .withMessage('Refund reason cannot exceed 255 characters')
    .trim()
];

/**
 * Webhook validation
 */
const validateWebhook = [
  body('order_id')
    .notEmpty()
    .withMessage('Order ID is required'),

  body('transaction_status')
    .notEmpty()
    .withMessage('Transaction status is required')
    .isIn([
      'capture', 'settlement', 'pending', 'deny', 'cancel', 'expire',
      'failure', 'refund', 'partial_refund', 'authorize'
    ])
    .withMessage('Invalid transaction status'),

  body('fraud_status')
    .optional()
    .isIn(['accept', 'deny', 'challenge'])
    .withMessage('Invalid fraud status'),

  body('gross_amount')
    .notEmpty()
    .withMessage('Gross amount is required')
    .isNumeric()
    .withMessage('Gross amount must be numeric'),

  body('signature_key')
    .notEmpty()
    .withMessage('Signature key is required'),

  body('status_code')
    .notEmpty()
    .withMessage('Status code is required')
    .isNumeric()
    .withMessage('Status code must be numeric')
];

/**
 * Subscription validation
 */
const validateSubscription = [
  body('planType')
    .notEmpty()
    .withMessage('Plan type is required')
    .isIn(['basic', 'premium', 'professional', 'enterprise'])
    .withMessage('Invalid plan type'),

  body('billingCycle')
    .notEmpty()
    .withMessage('Billing cycle is required')
    .isIn(['monthly', 'quarterly', 'yearly'])
    .withMessage('Invalid billing cycle'),

  body('startDate')
    .optional()
    .isISO8601()
    .withMessage('Start date must be a valid ISO 8601 date'),

  body('customAmount')
    .optional()
    .isNumeric()
    .withMessage('Custom amount must be a number')
    .isFloat({ min: 1000 })
    .withMessage('Custom amount must be at least IDR 1,000')
];

/**
 * Subscription cancellation validation
 */
const validateSubscriptionCancellation = [
  param('subscriptionId')
    .isUUID()
    .withMessage('Subscription ID must be a valid UUID'),

  body('reason')
    .optional()
    .isLength({ max: 255 })
    .withMessage('Cancellation reason cannot exceed 255 characters')
    .trim()
];

/**
 * User ID validation
 */
const validateUserId = [
  param('userId')
    .isUUID()
    .withMessage('User ID must be a valid UUID')
];

/**
 * Date range validation
 */
const validateDateRange = [
  query('dateFrom')
    .optional()
    .isISO8601()
    .withMessage('Date from must be a valid ISO 8601 date'),

  query('dateTo')
    .optional()
    .isISO8601()
    .withMessage('Date to must be a valid ISO 8601 date')
    .custom((value, { req }) => {
      if (req.query.dateFrom && new Date(value) <= new Date(req.query.dateFrom)) {
        throw new Error('Date to must be after date from');
      }
      return true;
    })
];

/**
 * Indonesian-specific validations
 */
const validateIndonesianCompliance = [
  // Phone number validation for Indonesian format
  body('customerDetails.phone')
    .custom((value) => {
      // Indonesian phone number: +62 or 0 followed by 8-12 digits
      const indonesianPhoneRegex = /^(\+62|62|0)[8-9][0-9]{7,11}$/;
      if (!indonesianPhoneRegex.test(value.replace(/[\s\-]/g, ''))) {
        throw new Error('Phone number must be a valid Indonesian number');
      }
      return true;
    }),

  // Postal code validation for Indonesia
  body('customerDetails.billingAddress.postalCode')
    .optional()
    .matches(/^\d{5}$/)
    .withMessage('Indonesian postal code must be exactly 5 digits'),

  // City validation for Indonesia
  body('customerDetails.billingAddress.city')
    .optional()
    .isIn([
      'Jakarta', 'Surabaya', 'Bandung', 'Bekasi', 'Medan', 'Tangerang',
      'Depok', 'Semarang', 'Palembang', 'Makassar', 'South Tangerang',
      'Batam', 'Bogor', 'Pekanbaru', 'Bandar Lampung', 'Malang',
      'Padang', 'Yogyakarta', 'Denpasar', 'Balikpapan'
      // Add more Indonesian cities as needed
    ])
    .withMessage('Please select a valid Indonesian city'),

  // Amount validation for Indonesian Rupiah
  body('amount')
    .custom((value, { req }) => {
      if (req.body.currency === 'IDR') {
        // IDR amounts should be multiples of 100 (no cents)
        if (value % 100 !== 0) {
          throw new Error('IDR amounts must be in whole hundreds (no cents)');
        }
      }
      return true;
    })
];

/**
 * Security validations
 */
const validateSecurity = [
  // Prevent common injection patterns
  body('*')
    .custom((value) => {
      if (typeof value === 'string') {
        // Check for SQL injection patterns
        const sqlPatterns = [
          /(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE)\b)/i,
          /(\-\-)/,
          /(\;)/,
          /(\bOR\b.*=.*)/i,
          /(\bAND\b.*=.*)/i
        ];

        // Check for XSS patterns
        const xssPatterns = [
          /<script/i,
          /javascript:/i,
          /data:text\/html/i,
          /vbscript:/i,
          /onclick/i,
          /onerror/i,
          /onload/i
        ];

        for (const pattern of [...sqlPatterns, ...xssPatterns]) {
          if (pattern.test(value)) {
            throw new Error('Invalid characters detected');
          }
        }
      }
      return true;
    })
];

module.exports = {
  validatePaymentCreation,
  validateOrderId,
  validatePagination,
  validatePaymentCancellation,
  validatePaymentRefund,
  validateWebhook,
  validateSubscription,
  validateSubscriptionCancellation,
  validateUserId,
  validateDateRange,
  validateIndonesianCompliance,
  validateSecurity
};