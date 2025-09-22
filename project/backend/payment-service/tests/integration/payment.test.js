const request = require('supertest');
const mongoose = require('mongoose');
const { MongoMemoryServer } = require('mongodb-memory-server');
const PaymentServiceApp = require('../../src/app');

describe('Payment Integration Tests', () => {
  let app;
  let mongoServer;
  let authToken;

  beforeAll(async () => {
    // Start MongoDB Memory Server
    mongoServer = await MongoMemoryServer.create();
    const mongoUri = mongoServer.getUri();

    // Set test environment
    process.env.NODE_ENV = 'test';
    process.env.MONGODB_URI = mongoUri;
    process.env.REDIS_HOST = 'localhost';
    process.env.JWT_SECRET = 'test-secret';
    process.env.SERVICE_TOKEN = 'test-service-token';

    // Mock Midtrans credentials
    process.env.MIDTRANS_SERVER_KEY_SANDBOX = 'test-server-key';
    process.env.MIDTRANS_CLIENT_KEY_SANDBOX = 'test-client-key';

    // Initialize app
    const paymentService = new PaymentServiceApp();
    app = paymentService.getApp();

    // Mock authentication token
    const jwt = require('jsonwebtoken');
    authToken = jwt.sign(
      { id: 'user-123', email: 'test@example.com' },
      process.env.JWT_SECRET,
      { expiresIn: '1h' }
    );
  });

  afterAll(async () => {
    await mongoose.connection.close();
    await mongoServer.stop();
  });

  beforeEach(async () => {
    // Clear database before each test
    const collections = mongoose.connection.collections;
    for (const key in collections) {
      await collections[key].deleteMany({});
    }
  });

  describe('POST /api/payments', () => {
    const validPaymentData = {
      amount: 100000,
      currency: 'IDR',
      paymentType: 'credit_card',
      customerDetails: {
        firstName: 'John',
        lastName: 'Doe',
        email: 'john@example.com',
        phone: '+6281234567890',
        billingAddress: {
          firstName: 'John',
          lastName: 'Doe',
          address: 'Jl. Sudirman No. 1',
          city: 'Jakarta',
          postalCode: '10110',
          phone: '+6281234567890',
          countryCode: 'IDN'
        }
      },
      itemDetails: [{
        id: 'plan-basic',
        name: 'Basic Trading Plan',
        price: 100000,
        quantity: 1
      }]
    };

    it('should create payment successfully with valid data', async () => {
      // Mock Midtrans service for this test
      const MidtransService = require('../../src/services/MidtransService');
      jest.spyOn(MidtransService, 'calculateTax').mockReturnValue({
        baseAmount: 100000,
        tax: 11000,
        grossAmount: 111000
      });
      jest.spyOn(MidtransService, 'generateOrderId').mockReturnValue('PAY-TEST-123');
      jest.spyOn(MidtransService, 'createSnapTransaction').mockResolvedValue({
        success: true,
        data: {
          token: 'snap-token-test',
          redirectUrl: 'https://app.sandbox.midtrans.com/snap/v2/vtweb/test'
        }
      });

      // Mock integration service
      const IntegrationService = require('../../src/services/IntegrationService');
      jest.spyOn(IntegrationService, 'validateUser').mockResolvedValue({
        isValid: true,
        user: { id: 'user-123', email: 'test@example.com' }
      });
      jest.spyOn(IntegrationService, 'notifyPaymentCreated').mockResolvedValue();

      const response = await request(app)
        .post('/api/payments')
        .set('Authorization', `Bearer ${authToken}`)
        .send(validPaymentData)
        .expect(201);

      expect(response.body.success).toBe(true);
      expect(response.body.data.orderId).toBe('PAY-TEST-123');
      expect(response.body.data.token).toBe('snap-token-test');
      expect(response.body.data.grossAmount).toBe(111000);
    });

    it('should reject payment with invalid amount', async () => {
      const invalidData = {
        ...validPaymentData,
        amount: 500 // Below minimum IDR 1,000
      };

      const response = await request(app)
        .post('/api/payments')
        .set('Authorization', `Bearer ${authToken}`)
        .send(invalidData)
        .expect(400);

      expect(response.body.success).toBe(false);
      expect(response.body.errors).toBeDefined();
    });

    it('should reject payment without authentication', async () => {
      const response = await request(app)
        .post('/api/payments')
        .send(validPaymentData)
        .expect(401);

      expect(response.body.success).toBe(false);
      expect(response.body.message).toContain('authentication');
    });

    it('should reject payment with invalid phone number', async () => {
      const invalidData = {
        ...validPaymentData,
        customerDetails: {
          ...validPaymentData.customerDetails,
          phone: '123' // Invalid phone format
        }
      };

      const response = await request(app)
        .post('/api/payments')
        .set('Authorization', `Bearer ${authToken}`)
        .send(invalidData)
        .expect(400);

      expect(response.body.success).toBe(false);
      expect(response.body.errors).toBeDefined();
    });

    it('should reject payment with XSS attempt', async () => {
      const xssData = {
        ...validPaymentData,
        customerDetails: {
          ...validPaymentData.customerDetails,
          firstName: '<script>alert("xss")</script>'
        }
      };

      const response = await request(app)
        .post('/api/payments')
        .set('Authorization', `Bearer ${authToken}`)
        .send(xssData)
        .expect(400);

      expect(response.body.success).toBe(false);
      expect(response.body.message).toContain('Invalid characters detected');
    });
  });

  describe('POST /api/payments/webhook', () => {
    const validWebhookData = {
      order_id: 'PAY-TEST-123',
      transaction_status: 'settlement',
      fraud_status: 'accept',
      gross_amount: '111000.00',
      signature_key: 'test-signature',
      status_code: '200',
      transaction_id: 'midtrans-txn-123',
      payment_type: 'credit_card'
    };

    beforeEach(async () => {
      // Create a test payment in database
      const Payment = require('../../src/models/Payment');
      await new Payment({
        orderId: 'PAY-TEST-123',
        userId: 'user-123',
        amount: 100000,
        grossAmount: 111000,
        currency: 'IDR',
        status: 'pending',
        paymentType: 'credit_card',
        customerDetails: {
          firstName: 'John',
          lastName: 'Doe',
          email: 'john@example.com',
          phone: '+6281234567890'
        },
        itemDetails: [{
          id: 'plan-basic',
          name: 'Basic Trading Plan',
          price: 100000,
          quantity: 1
        }]
      }).save();
    });

    it('should process valid webhook successfully', async () => {
      // Mock Midtrans signature verification
      const MidtransService = require('../../src/services/MidtransService');
      jest.spyOn(MidtransService, 'verifyWebhookSignature').mockReturnValue(true);

      // Mock integration service
      const IntegrationService = require('../../src/services/IntegrationService');
      jest.spyOn(IntegrationService, 'notifyPaymentStatusChanged').mockResolvedValue();

      const response = await request(app)
        .post('/api/payments/webhook')
        .set('X-Midtrans-Signature', 'test-signature')
        .send(validWebhookData)
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.message).toContain('processed successfully');

      // Verify payment was updated
      const Payment = require('../../src/models/Payment');
      const updatedPayment = await Payment.findOne({ orderId: 'PAY-TEST-123' });
      expect(updatedPayment.status).toBe('settlement');
    });

    it('should reject webhook with invalid signature', async () => {
      const MidtransService = require('../../src/services/MidtransService');
      jest.spyOn(MidtransService, 'verifyWebhookSignature').mockReturnValue(false);

      const response = await request(app)
        .post('/api/payments/webhook')
        .set('X-Midtrans-Signature', 'invalid-signature')
        .send(validWebhookData)
        .expect(200); // Returns 200 to prevent Midtrans retries

      expect(response.body.success).toBe(false);
      expect(response.body.message).toContain('Invalid webhook signature');
    });

    it('should reject webhook without signature header', async () => {
      const response = await request(app)
        .post('/api/payments/webhook')
        .send(validWebhookData)
        .expect(400);

      expect(response.body.success).toBe(false);
      expect(response.body.message).toContain('signature required');
    });
  });

  describe('GET /api/payments/:orderId', () => {
    beforeEach(async () => {
      // Create test payment
      const Payment = require('../../src/models/Payment');
      await new Payment({
        orderId: 'PAY-TEST-GET',
        userId: 'user-123',
        amount: 100000,
        grossAmount: 111000,
        currency: 'IDR',
        status: 'settlement',
        paymentType: 'credit_card',
        customerDetails: {
          firstName: 'John',
          lastName: 'Doe',
          email: 'john@example.com',
          phone: '+6281234567890'
        },
        itemDetails: [{
          id: 'plan-basic',
          name: 'Basic Trading Plan',
          price: 100000,
          quantity: 1
        }]
      }).save();
    });

    it('should get payment details successfully', async () => {
      const response = await request(app)
        .get('/api/payments/PAY-TEST-GET')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.data.orderId).toBe('PAY-TEST-GET');
      expect(response.body.data.status).toBe('settlement');
      expect(response.body.data.grossAmount).toBe(111000);

      // Ensure sensitive data is not exposed
      expect(response.body.data.webhookData).toBeUndefined();
      expect(response.body.data.securityInfo).toBeUndefined();
    });

    it('should return 404 for non-existent payment', async () => {
      const response = await request(app)
        .get('/api/payments/NONEXISTENT')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(404);

      expect(response.body.success).toBe(false);
      expect(response.body.message).toContain('not found');
    });
  });

  describe('PUT /api/payments/:orderId/cancel', () => {
    beforeEach(async () => {
      // Create cancellable payment
      const Payment = require('../../src/models/Payment');
      await new Payment({
        orderId: 'PAY-TEST-CANCEL',
        userId: 'user-123',
        amount: 100000,
        grossAmount: 111000,
        currency: 'IDR',
        status: 'pending', // Cancellable status
        paymentType: 'credit_card',
        customerDetails: {
          firstName: 'John',
          lastName: 'Doe',
          email: 'john@example.com',
          phone: '+6281234567890'
        },
        itemDetails: [{
          id: 'plan-basic',
          name: 'Basic Trading Plan',
          price: 100000,
          quantity: 1
        }]
      }).save();
    });

    it('should cancel payment successfully', async () => {
      // Mock Midtrans cancellation
      const MidtransService = require('../../src/services/MidtransService');
      jest.spyOn(MidtransService, 'cancelTransaction').mockResolvedValue({ success: true });

      // Mock integration service
      const IntegrationService = require('../../src/services/IntegrationService');
      jest.spyOn(IntegrationService, 'notifyPaymentCancelled').mockResolvedValue();

      const response = await request(app)
        .put('/api/payments/PAY-TEST-CANCEL/cancel')
        .set('Authorization', `Bearer ${authToken}`)
        .send({ reason: 'Customer request' })
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.message).toContain('cancelled successfully');

      // Verify payment was cancelled
      const Payment = require('../../src/models/Payment');
      const cancelledPayment = await Payment.findOne({ orderId: 'PAY-TEST-CANCEL' });
      expect(cancelledPayment.status).toBe('cancel');
    });
  });

  describe('GET /api/payments/user/history', () => {
    beforeEach(async () => {
      // Create multiple test payments
      const Payment = require('../../src/models/Payment');
      const payments = [];

      for (let i = 1; i <= 5; i++) {
        payments.push(new Payment({
          orderId: `PAY-HISTORY-${i}`,
          userId: 'user-123',
          amount: 100000 * i,
          grossAmount: 111000 * i,
          currency: 'IDR',
          status: i % 2 === 0 ? 'settlement' : 'pending',
          paymentType: 'credit_card',
          customerDetails: {
            firstName: 'John',
            lastName: 'Doe',
            email: 'john@example.com',
            phone: '+6281234567890'
          },
          itemDetails: [{
            id: `plan-${i}`,
            name: `Plan ${i}`,
            price: 100000 * i,
            quantity: 1
          }],
          createdAt: new Date(Date.now() - i * 24 * 60 * 60 * 1000) // i days ago
        }));
      }

      await Payment.insertMany(payments);
    });

    it('should get user payment history with pagination', async () => {
      const response = await request(app)
        .get('/api/payments/user/history?page=1&limit=3')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.data.length).toBe(3);
      expect(response.body.pagination.total).toBe(5);
      expect(response.body.pagination.totalPages).toBe(2);
      expect(response.body.pagination.hasNext).toBe(true);

      // Verify sorting (newest first)
      const payments = response.body.data;
      expect(payments[0].orderId).toBe('PAY-HISTORY-1');
    });

    it('should filter payments by status', async () => {
      const response = await request(app)
        .get('/api/payments/user/history?status=settlement')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.data.length).toBe(2); // Only even numbered payments
      response.body.data.forEach(payment => {
        expect(payment.status).toBe('settlement');
      });
    });
  });

  describe('Rate Limiting', () => {
    it('should enforce payment rate limiting', async () => {
      const paymentData = {
        amount: 100000,
        customerDetails: {
          firstName: 'John',
          email: 'john@example.com',
          phone: '+6281234567890'
        }
      };

      // Mock services to prevent actual API calls
      const MidtransService = require('../../src/services/MidtransService');
      const IntegrationService = require('../../src/services/IntegrationService');

      jest.spyOn(MidtransService, 'calculateTax').mockReturnValue({
        baseAmount: 100000,
        tax: 11000,
        grossAmount: 111000
      });
      jest.spyOn(IntegrationService, 'validateUser').mockResolvedValue({
        isValid: true,
        user: { id: 'user-123' }
      });

      // Make multiple rapid requests
      const requests = [];
      for (let i = 0; i < 12; i++) { // Exceed limit of 10
        requests.push(
          request(app)
            .post('/api/payments')
            .set('Authorization', `Bearer ${authToken}`)
            .send(paymentData)
        );
      }

      const responses = await Promise.all(requests);
      const rateLimitedResponses = responses.filter(res => res.status === 429);

      expect(rateLimitedResponses.length).toBeGreaterThan(0);
    });
  });

  describe('Error Handling', () => {
    it('should handle database connection errors gracefully', async () => {
      // Close database connection to simulate error
      await mongoose.connection.close();

      const response = await request(app)
        .get('/api/payments/PAY-TEST-ERROR')
        .set('Authorization', `Bearer ${authToken}`)
        .expect(500);

      expect(response.body.success).toBe(false);
      expect(response.body.message).toBeDefined();
    });
  });
});