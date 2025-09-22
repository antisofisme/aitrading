const express = require('express');
const { body, validationResult, param } = require('express-validator');
const winston = require('winston');

const {
  getUserSubscription,
  createSubscription,
  updateSubscription,
  cancelSubscription,
  getSubscriptionHistory,
  getSubscriptionUsage
} = require('../services/subscriptionService');

const {
  SUBSCRIPTION_TIERS,
  validateTierUpgrade,
  calculateProration
} = require('../config/tiers');

const router = express.Router();

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  defaultMeta: { service: 'subscription-service-routes' }
});

// Validation rules
const subscriptionValidation = [
  body('tier')
    .isIn(Object.keys(SUBSCRIPTION_TIERS))
    .withMessage(`Tier must be one of: ${Object.keys(SUBSCRIPTION_TIERS).join(', ')}`),
  body('paymentMethodId')
    .optional()
    .isString()
    .withMessage('Payment method ID must be a string')
];

const updateSubscriptionValidation = [
  param('subscriptionId')
    .isUUID()
    .withMessage('Valid subscription ID is required'),
  body('tier')
    .optional()
    .isIn(Object.keys(SUBSCRIPTION_TIERS))
    .withMessage(`Tier must be one of: ${Object.keys(SUBSCRIPTION_TIERS).join(', ')}`),
  body('autoRenewal')
    .optional()
    .isBoolean()
    .withMessage('Auto renewal must be a boolean')
];

// GET /api/subscriptions/current - Get current user subscription
router.get('/current', async (req, res) => {
  try {
    const subscription = await getUserSubscription(req.user.id);

    if (!subscription) {
      return res.status(404).json({
        success: false,
        error: 'No subscription found',
        message: 'User does not have an active subscription'
      });
    }

    res.json({
      success: true,
      data: {
        subscription: {
          id: subscription.id,
          tier: subscription.tier,
          status: subscription.status,
          currentPeriodStart: subscription.currentPeriodStart,
          currentPeriodEnd: subscription.currentPeriodEnd,
          autoRenewal: subscription.autoRenewal,
          createdAt: subscription.createdAt,
          updatedAt: subscription.updatedAt,
          tierDetails: SUBSCRIPTION_TIERS[subscription.tier]
        }
      }
    });

  } catch (error) {
    logger.error('Get current subscription error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get subscription',
      message: 'An error occurred while retrieving subscription information'
    });
  }
});

// POST /api/subscriptions - Create new subscription
router.post('/', subscriptionValidation, async (req, res) => {
  try {
    // Check for validation errors
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        success: false,
        error: 'Validation failed',
        details: errors.array()
      });
    }

    const { tier, paymentMethodId } = req.body;

    // Check if user already has a subscription
    const existingSubscription = await getUserSubscription(req.user.id);
    if (existingSubscription && existingSubscription.status === 'active') {
      return res.status(409).json({
        success: false,
        error: 'Subscription already exists',
        message: 'User already has an active subscription. Use update endpoint to change tier.'
      });
    }

    // Validate tier (can't start with ENTERPRISE without approval)
    if (tier === 'ENTERPRISE') {
      return res.status(403).json({
        success: false,
        error: 'Enterprise subscription requires approval',
        message: 'Please contact sales for ENTERPRISE tier subscription'
      });
    }

    // Create subscription
    const subscriptionData = {
      userId: req.user.id,
      tier,
      paymentMethodId,
      autoRenewal: true,
      status: 'active'
    };

    const subscription = await createSubscription(subscriptionData);

    logger.info(`Subscription created for user ${req.user.id}: ${tier}`);

    res.status(201).json({
      success: true,
      message: 'Subscription created successfully',
      data: {
        subscription: {
          id: subscription.id,
          tier: subscription.tier,
          status: subscription.status,
          currentPeriodStart: subscription.currentPeriodStart,
          currentPeriodEnd: subscription.currentPeriodEnd,
          autoRenewal: subscription.autoRenewal,
          tierDetails: SUBSCRIPTION_TIERS[subscription.tier]
        }
      }
    });

  } catch (error) {
    logger.error('Create subscription error:', error);
    res.status(500).json({
      success: false,
      error: 'Subscription creation failed',
      message: 'An error occurred while creating the subscription'
    });
  }
});

// PUT /api/subscriptions/:subscriptionId - Update subscription
router.put('/:subscriptionId', updateSubscriptionValidation, async (req, res) => {
  try {
    // Check for validation errors
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        success: false,
        error: 'Validation failed',
        details: errors.array()
      });
    }

    const { subscriptionId } = req.params;
    const { tier, autoRenewal } = req.body;

    // Get current subscription
    const currentSubscription = await getUserSubscription(req.user.id);
    if (!currentSubscription || currentSubscription.id !== subscriptionId) {
      return res.status(404).json({
        success: false,
        error: 'Subscription not found',
        message: 'Subscription not found or does not belong to user'
      });
    }

    // Validate tier upgrade/downgrade
    if (tier && tier !== currentSubscription.tier) {
      const validation = validateTierUpgrade(currentSubscription.tier, tier);
      if (!validation.allowed) {
        return res.status(400).json({
          success: false,
          error: 'Invalid tier change',
          message: validation.reason
        });
      }

      // Calculate proration for tier changes
      const proration = calculateProration(
        currentSubscription.tier,
        tier,
        currentSubscription.currentPeriodStart,
        currentSubscription.currentPeriodEnd
      );

      // Update subscription with new tier
      const updatedSubscription = await updateSubscription(subscriptionId, {
        tier,
        autoRenewal,
        proration
      });

      logger.info(`Subscription updated for user ${req.user.id}: ${currentSubscription.tier} -> ${tier}`);

      return res.json({
        success: true,
        message: 'Subscription updated successfully',
        data: {
          subscription: {
            id: updatedSubscription.id,
            tier: updatedSubscription.tier,
            status: updatedSubscription.status,
            currentPeriodStart: updatedSubscription.currentPeriodStart,
            currentPeriodEnd: updatedSubscription.currentPeriodEnd,
            autoRenewal: updatedSubscription.autoRenewal,
            tierDetails: SUBSCRIPTION_TIERS[updatedSubscription.tier]
          },
          proration: proration.amount !== 0 ? {
            amount: proration.amount,
            description: proration.description
          } : null
        }
      });
    }

    // Update auto-renewal only
    if (autoRenewal !== undefined) {
      const updatedSubscription = await updateSubscription(subscriptionId, {
        autoRenewal
      });

      return res.json({
        success: true,
        message: 'Subscription updated successfully',
        data: {
          subscription: {
            id: updatedSubscription.id,
            tier: updatedSubscription.tier,
            status: updatedSubscription.status,
            currentPeriodStart: updatedSubscription.currentPeriodStart,
            currentPeriodEnd: updatedSubscription.currentPeriodEnd,
            autoRenewal: updatedSubscription.autoRenewal,
            tierDetails: SUBSCRIPTION_TIERS[updatedSubscription.tier]
          }
        }
      });
    }

    // No changes specified
    res.status(400).json({
      success: false,
      error: 'No changes specified',
      message: 'Please specify tier or autoRenewal to update'
    });

  } catch (error) {
    logger.error('Update subscription error:', error);
    res.status(500).json({
      success: false,
      error: 'Subscription update failed',
      message: 'An error occurred while updating the subscription'
    });
  }
});

// DELETE /api/subscriptions/:subscriptionId - Cancel subscription
router.delete('/:subscriptionId', async (req, res) => {
  try {
    const { subscriptionId } = req.params;

    // Get current subscription
    const currentSubscription = await getUserSubscription(req.user.id);
    if (!currentSubscription || currentSubscription.id !== subscriptionId) {
      return res.status(404).json({
        success: false,
        error: 'Subscription not found',
        message: 'Subscription not found or does not belong to user'
      });
    }

    // Cancel subscription (will remain active until period end)
    const cancelledSubscription = await cancelSubscription(subscriptionId);

    logger.info(`Subscription cancelled for user ${req.user.id}: ${currentSubscription.tier}`);

    res.json({
      success: true,
      message: 'Subscription cancelled successfully. It will remain active until the end of the current billing period.',
      data: {
        subscription: {
          id: cancelledSubscription.id,
          tier: cancelledSubscription.tier,
          status: cancelledSubscription.status,
          currentPeriodStart: cancelledSubscription.currentPeriodStart,
          currentPeriodEnd: cancelledSubscription.currentPeriodEnd,
          cancelledAt: cancelledSubscription.cancelledAt,
          tierDetails: SUBSCRIPTION_TIERS[cancelledSubscription.tier]
        }
      }
    });

  } catch (error) {
    logger.error('Cancel subscription error:', error);
    res.status(500).json({
      success: false,
      error: 'Subscription cancellation failed',
      message: 'An error occurred while cancelling the subscription'
    });
  }
});

// GET /api/subscriptions/history - Get subscription history
router.get('/history', async (req, res) => {
  try {
    const { page = 1, limit = 10 } = req.query;
    const offset = (parseInt(page) - 1) * parseInt(limit);

    const history = await getSubscriptionHistory(req.user.id, parseInt(limit), offset);

    res.json({
      success: true,
      data: {
        history: history.map(sub => ({
          id: sub.id,
          tier: sub.tier,
          status: sub.status,
          currentPeriodStart: sub.currentPeriodStart,
          currentPeriodEnd: sub.currentPeriodEnd,
          createdAt: sub.createdAt,
          cancelledAt: sub.cancelledAt,
          tierDetails: SUBSCRIPTION_TIERS[sub.tier]
        })),
        pagination: {
          page: parseInt(page),
          limit: parseInt(limit),
          hasMore: history.length === parseInt(limit)
        }
      }
    });

  } catch (error) {
    logger.error('Get subscription history error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get subscription history',
      message: 'An error occurred while retrieving subscription history'
    });
  }
});

// GET /api/subscriptions/usage - Get current subscription usage
router.get('/usage', async (req, res) => {
  try {
    const usage = await getSubscriptionUsage(req.user.id);

    res.json({
      success: true,
      data: {
        usage
      }
    });

  } catch (error) {
    logger.error('Get subscription usage error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get subscription usage',
      message: 'An error occurred while retrieving subscription usage'
    });
  }
});

module.exports = router;