# ADR-002: Midtrans Payment Gateway Integration

**Status**: Recommended
**Date**: 2025-09-20
**Deciders**: System Architecture Team

## Context

The platform requires payment processing for the Indonesian market, supporting subscription billing for AI trading services with local payment methods compliance.

## Decision

We will integrate **Midtrans Core API** for payment processing with comprehensive webhook handling for subscription management.

## Rationale

### Market Fit
- **Indonesian Focus**: Native support for GoPay, QRIS, Bank Transfers
- **Regulatory Compliance**: OJK-approved payment processor
- **Market Penetration**: Established trust in Indonesian fintech ecosystem

### Technical Advantages
- **Subscription Support**: Native recurring billing capabilities
- **Security**: PCI DSS Level 1 certification with fraud detection
- **API Maturity**: Production-ready with comprehensive documentation
- **Integration Simplicity**: 1-2 week implementation timeline

### Implementation Architecture

```javascript
// Payment service abstraction
class PaymentService {
  constructor() {
    this.midtrans = new MidtransClient({
      isProduction: process.env.NODE_ENV === 'production',
      serverKey: process.env.MIDTRANS_SERVER_KEY
    });
  }

  async createSubscription(userId, planId) {
    const subscription = {
      payment_type: 'credit_card',
      transaction_details: {
        order_id: `sub-${userId}-${Date.now()}`,
        gross_amount: this.getPlanPrice(planId)
      },
      credit_card: {
        save_token_id: true // Enable recurring
      }
    };

    return await this.midtrans.charge(subscription);
  }

  async handleWebhook(payload) {
    // Webhook processing for subscription events
    const notification = new MidtransNotification(payload);

    switch(notification.transaction_status) {
      case 'settlement':
        await this.activateSubscription(notification.order_id);
        break;
      case 'expire':
        await this.suspendSubscription(notification.order_id);
        break;
    }
  }
}
```

## Alternatives Considered

1. **Xendit**: Good alternative but less Indonesian payment method coverage
2. **DOKU**: Limited subscription billing features
3. **Custom Implementation**: Rejected due to compliance complexity
4. **Stripe**: Limited Indonesian market support

## Consequences

### Positive
- ✅ 25+ local payment methods supported
- ✅ Automatic subscription billing
- ✅ Built-in fraud detection and security
- ✅ Comprehensive webhook system
- ✅ One-click payments for returning customers

### Negative
- ⚠️ Indonesia-specific solution (regional lock-in)
- ⚠️ Transaction fees (standard for payment processors)

### Neutral
- Requires webhook endpoint implementation
- Need payment reconciliation system

## Implementation Timeline

- **Week 3**: Core integration and testing environment
- **Week 4**: Subscription billing and webhook handling
- **Week 5**: Security validation and production setup

## Risk Mitigation

- Implement webhook redundancy for critical events
- Create payment reconciliation monitoring
- Establish fraud detection alerting
- Maintain payment method fallback options