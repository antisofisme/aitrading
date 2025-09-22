const PaymentService = require('../../src/services/PaymentService');
const MidtransService = require('../../src/services/MidtransService');
const Payment = require('../../src/models/Payment');
const IntegrationService = require('../../src/services/IntegrationService');

// Mock dependencies
jest.mock('../../src/services/MidtransService');
jest.mock('../../src/models/Payment');
jest.mock('../../src/services/IntegrationService');
jest.mock('../../src/config/redis');

describe('PaymentService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('createPayment', () => {
    const mockPaymentData = {
      userId: 'user-123',
      amount: 100000,
      currency: 'IDR',
      paymentType: 'credit_card',
      customerDetails: {
        firstName: 'John',
        lastName: 'Doe',
        email: 'john@example.com',
        phone: '+6281234567890'
      },
      itemDetails: [{
        id: 'item-1',
        name: 'Trading Plan',
        price: 100000,
        quantity: 1
      }]
    };

    it('should create payment successfully', async () => {
      // Mock user validation
      IntegrationService.validateUser.mockResolvedValue({
        isValid: true,
        user: { id: 'user-123', email: 'john@example.com' }
      });

      // Mock tax calculation
      MidtransService.calculateTax.mockReturnValue({
        baseAmount: 100000,
        tax: 11000,
        grossAmount: 111000
      });

      // Mock order ID generation
      MidtransService.generateOrderId.mockReturnValue('PAY-1234567890-ABC123');

      // Mock payment save
      const mockPayment = {
        orderId: 'PAY-1234567890-ABC123',
        userId: 'user-123',
        amount: 100000,
        grossAmount: 111000,
        save: jest.fn().mockResolvedValue(true)
      };
      Payment.mockImplementation(() => mockPayment);

      // Mock Midtrans transaction
      MidtransService.createSnapTransaction.mockResolvedValue({
        success: true,
        data: {
          token: 'snap-token-123',
          redirectUrl: 'https://app.midtrans.com/snap/v2/vtweb/snap-token-123'
        }
      });

      // Mock integration notifications
      IntegrationService.notifyPaymentCreated.mockResolvedValue();

      const result = await PaymentService.createPayment(mockPaymentData);

      expect(result.success).toBe(true);
      expect(result.data.orderId).toBe('PAY-1234567890-ABC123');
      expect(result.data.token).toBe('snap-token-123');
      expect(result.data.grossAmount).toBe(111000);

      // Verify service calls
      expect(IntegrationService.validateUser).toHaveBeenCalledWith('user-123');
      expect(MidtransService.calculateTax).toHaveBeenCalledWith(100000);
      expect(MidtransService.generateOrderId).toHaveBeenCalledWith('PAY');
      expect(mockPayment.save).toHaveBeenCalledTimes(2); // Initial save and update with Midtrans response
    });

    it('should throw error for invalid user', async () => {
      IntegrationService.validateUser.mockResolvedValue({
        isValid: false,
        user: null
      });

      await expect(PaymentService.createPayment(mockPaymentData))
        .rejects.toThrow('Invalid user ID');
    });

    it('should handle Midtrans transaction failure', async () => {
      IntegrationService.validateUser.mockResolvedValue({
        isValid: true,
        user: { id: 'user-123' }
      });

      MidtransService.calculateTax.mockReturnValue({
        baseAmount: 100000,
        tax: 11000,
        grossAmount: 111000
      });

      MidtransService.generateOrderId.mockReturnValue('PAY-1234567890-ABC123');

      const mockPayment = {
        orderId: 'PAY-1234567890-ABC123',
        status: 'pending',
        save: jest.fn().mockResolvedValue(true)
      };
      Payment.mockImplementation(() => mockPayment);

      MidtransService.createSnapTransaction.mockResolvedValue({
        success: false,
        error: {
          code: 'TRANSACTION_FAILED',
          message: 'Payment gateway error'
        }
      });

      await expect(PaymentService.createPayment(mockPaymentData))
        .rejects.toThrow('Payment gateway error');

      expect(mockPayment.status).toBe('failure');
    });
  });

  describe('processWebhook', () => {
    const mockNotification = {
      order_id: 'PAY-1234567890-ABC123',
      transaction_status: 'settlement',
      fraud_status: 'accept',
      gross_amount: '111000.00',
      signature_key: 'signature-key-123',
      status_code: '200'
    };

    it('should process webhook successfully', async () => {
      // Mock signature verification
      MidtransService.verifyWebhookSignature.mockReturnValue(true);

      // Mock payment find
      const mockPayment = {
        orderId: 'PAY-1234567890-ABC123',
        status: 'pending',
        subscriptionId: null,
        addWebhookData: jest.fn().mockResolvedValue(true),
        save: jest.fn().mockResolvedValue(true)
      };
      Payment.findOne.mockResolvedValue(mockPayment);

      // Mock status update
      PaymentService.updatePaymentStatus = jest.fn().mockResolvedValue();

      // Mock integration notification
      IntegrationService.notifyPaymentStatusChanged.mockResolvedValue();

      const result = await PaymentService.processWebhook(mockNotification, 'signature-123');

      expect(result.success).toBe(true);
      expect(result.message).toBe('Webhook processed successfully');

      expect(MidtransService.verifyWebhookSignature).toHaveBeenCalledWith(mockNotification, 'signature-123');
      expect(Payment.findOne).toHaveBeenCalledWith({ orderId: 'PAY-1234567890-ABC123' });
      expect(mockPayment.addWebhookData).toHaveBeenCalled();
    });

    it('should reject webhook with invalid signature', async () => {
      MidtransService.verifyWebhookSignature.mockReturnValue(false);

      await expect(PaymentService.processWebhook(mockNotification, 'invalid-signature'))
        .rejects.toThrow('Invalid webhook signature');
    });

    it('should reject webhook for non-existent payment', async () => {
      MidtransService.verifyWebhookSignature.mockReturnValue(true);
      Payment.findOne.mockResolvedValue(null);

      await expect(PaymentService.processWebhook(mockNotification, 'signature-123'))
        .rejects.toThrow('Payment not found for order ID: PAY-1234567890-ABC123');
    });
  });

  describe('getUserPayments', () => {
    it('should return user payments with pagination', async () => {
      const mockPayments = [
        {
          orderId: 'PAY-001',
          amount: 100000,
          status: 'settlement',
          createdAt: new Date()
        },
        {
          orderId: 'PAY-002',
          amount: 200000,
          status: 'pending',
          createdAt: new Date()
        }
      ];

      Payment.find.mockReturnValue({
        sort: jest.fn().mockReturnThis(),
        skip: jest.fn().mockReturnThis(),
        limit: jest.fn().mockReturnThis(),
        select: jest.fn().mockResolvedValue(mockPayments)
      });

      Payment.countDocuments.mockResolvedValue(25);

      const result = await PaymentService.getUserPayments('user-123', {
        page: 1,
        limit: 20
      });

      expect(result.payments).toEqual(mockPayments);
      expect(result.pagination.total).toBe(25);
      expect(result.pagination.totalPages).toBe(2);
      expect(result.pagination.hasNext).toBe(true);
    });
  });

  describe('cancelPayment', () => {
    it('should cancel payment successfully', async () => {
      const mockPayment = {
        orderId: 'PAY-1234567890-ABC123',
        userId: 'user-123',
        status: 'pending',
        metadata: {},
        save: jest.fn().mockResolvedValue(true)
      };

      PaymentService.getPayment = jest.fn().mockResolvedValue(mockPayment);
      MidtransService.cancelTransaction.mockResolvedValue({ success: true });
      PaymentService.clearPaymentCache = jest.fn().mockResolvedValue();
      IntegrationService.notifyPaymentCancelled.mockResolvedValue();

      const result = await PaymentService.cancelPayment('PAY-1234567890-ABC123', 'user-123', 'User cancellation');

      expect(result.success).toBe(true);
      expect(mockPayment.status).toBe('cancel');
      expect(mockPayment.metadata.cancellationReason).toBe('User cancellation');
    });

    it('should throw error for non-cancellable payment', async () => {
      const mockPayment = {
        status: 'settlement'
      };

      PaymentService.getPayment = jest.fn().mockResolvedValue(mockPayment);

      await expect(PaymentService.cancelPayment('PAY-1234567890-ABC123', 'user-123'))
        .rejects.toThrow('Payment cannot be cancelled in current status');
    });
  });

  describe('refundPayment', () => {
    it('should refund payment successfully', async () => {
      const mockPayment = {
        orderId: 'PAY-1234567890-ABC123',
        status: 'settlement',
        grossAmount: 111000,
        subscriptionId: null,
        metadata: {},
        save: jest.fn().mockResolvedValue(true)
      };

      PaymentService.getPayment = jest.fn().mockResolvedValue(mockPayment);
      MidtransService.refundTransaction.mockResolvedValue({ success: true });
      PaymentService.clearPaymentCache = jest.fn().mockResolvedValue();
      IntegrationService.notifyPaymentRefunded.mockResolvedValue();

      const result = await PaymentService.refundPayment('PAY-1234567890-ABC123', null, 'Customer request');

      expect(result.success).toBe(true);
      expect(result.refundAmount).toBe(111000);
      expect(mockPayment.status).toBe('refund');
    });

    it('should handle partial refund', async () => {
      const mockPayment = {
        orderId: 'PAY-1234567890-ABC123',
        status: 'settlement',
        grossAmount: 111000,
        metadata: {},
        save: jest.fn().mockResolvedValue(true)
      };

      PaymentService.getPayment = jest.fn().mockResolvedValue(mockPayment);
      MidtransService.refundTransaction.mockResolvedValue({ success: true });
      PaymentService.clearPaymentCache = jest.fn().mockResolvedValue();
      IntegrationService.notifyPaymentRefunded.mockResolvedValue();

      const result = await PaymentService.refundPayment('PAY-1234567890-ABC123', 50000, 'Partial refund');

      expect(result.refundAmount).toBe(50000);
      expect(mockPayment.status).toBe('partial_refund');
    });

    it('should throw error for excessive refund amount', async () => {
      const mockPayment = {
        grossAmount: 111000,
        status: 'settlement'
      };

      PaymentService.getPayment = jest.fn().mockResolvedValue(mockPayment);

      await expect(PaymentService.refundPayment('PAY-1234567890-ABC123', 200000))
        .rejects.toThrow('Refund amount cannot exceed payment amount');
    });
  });

  describe('mapMidtransStatus', () => {
    it('should map Midtrans statuses correctly', () => {
      expect(PaymentService.mapMidtransStatus('settlement', 'accept')).toBe('settlement');
      expect(PaymentService.mapMidtransStatus('capture', 'accept')).toBe('capture');
      expect(PaymentService.mapMidtransStatus('pending', 'accept')).toBe('pending');
      expect(PaymentService.mapMidtransStatus('settlement', 'deny')).toBe('deny');
      expect(PaymentService.mapMidtransStatus('settlement', 'challenge')).toBe('pending');
      expect(PaymentService.mapMidtransStatus('cancel', 'accept')).toBe('cancel');
      expect(PaymentService.mapMidtransStatus('expire', 'accept')).toBe('expire');
    });
  });
});