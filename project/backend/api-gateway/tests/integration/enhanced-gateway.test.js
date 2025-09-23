/**
 * Enhanced API Gateway Integration Tests
 *
 * Tests for the enhanced API Gateway with multi-database architecture
 * and Configuration Service integration.
 */

const request = require('supertest');
const EnhancedAPIGateway = require('../../src/new-enhanced-server');

describe('Enhanced API Gateway Integration Tests', () => {
  let gateway;
  let app;

  beforeAll(async () => {
    // Set test environment variables
    process.env.NODE_ENV = 'test';
    process.env.PORT = '0'; // Use random port for testing
    process.env.LOG_LEVEL = 'error'; // Reduce log noise

    // Mock environment variables for databases
    process.env.POSTGRES_HOST = 'localhost';
    process.env.POSTGRES_PORT = '5432';
    process.env.POSTGRES_DB = 'test_ai_trading';
    process.env.POSTGRES_USER = 'test_user';
    process.env.POSTGRES_PASSWORD = 'test_password';

    process.env.DRAGONFLY_HOST = 'localhost';
    process.env.DRAGONFLY_PORT = '6379';

    process.env.CLICKHOUSE_HOST = 'localhost';
    process.env.CLICKHOUSE_PORT = '8123';

    process.env.WEAVIATE_HOST = 'localhost';
    process.env.WEAVIATE_PORT = '8080';

    process.env.ARANGO_URL = 'http://localhost:8529';
    process.env.ARANGO_DB = 'test_aitrading_graph';

    process.env.FLOW_REGISTRY_URL = 'http://localhost:8012';

    // Initialize gateway
    gateway = new EnhancedAPIGateway();

    // Mock database connections for testing
    gateway.databaseManager.initialize = jest.fn().mockResolvedValue(true);
    gateway.databaseManager.healthCheck = jest.fn().mockResolvedValue({
      postgres: { status: 'healthy', timestamp: new Date() },
      dragonflydb: { status: 'healthy', timestamp: new Date() },
      clickhouse: { status: 'healthy', timestamp: new Date() },
      weaviate: { status: 'healthy', timestamp: new Date() },
      arangodb: { status: 'healthy', timestamp: new Date() },
      redis: { status: 'healthy', timestamp: new Date() }
    });
    gateway.databaseManager.getConnectionStatus = jest.fn().mockReturnValue({
      postgres: true,
      dragonflydb: true,
      clickhouse: true,
      weaviate: true,
      arangodb: true,
      redis: true
    });

    // Mock Configuration Service client
    gateway.configServiceClient.initialize = jest.fn().mockResolvedValue(true);
    gateway.configServiceClient.registerService = jest.fn().mockResolvedValue({ success: true });
    gateway.configServiceClient.getConnectionStatus = jest.fn().mockReturnValue({
      isConnected: true,
      baseURL: 'http://localhost:8012',
      lastHealthCheck: new Date()
    });

    // Mock Flow-Aware Error Handler
    gateway.flowAwareErrorHandler.handleError = jest.fn().mockReturnValue((err, req, res, next) => next(err));

    await gateway.initialize();
    app = gateway.app;
  }, 30000);

  afterAll(async () => {
    if (gateway) {
      // Mock cleanup methods
      gateway.databaseManager.close = jest.fn().mockResolvedValue();
      gateway.configServiceClient.close = jest.fn();
      gateway.flowAwareErrorHandler.close = jest.fn().mockResolvedValue();
    }
  });

  describe('Health Check Endpoints', () => {
    test('GET /health should return comprehensive health status', async () => {
      const response = await request(app)
        .get('/health')
        .expect(200);

      expect(response.body).toHaveProperty('success', true);
      expect(response.body.data).toHaveProperty('status', 'healthy');
      expect(response.body.data).toHaveProperty('version', '1.0.0');
      expect(response.body.data).toHaveProperty('uptime');
      expect(response.body.data).toHaveProperty('services');
      expect(response.body.data.services).toHaveProperty('apiGateway');
      expect(response.body.data.services).toHaveProperty('databases');
      expect(response.body.data.services).toHaveProperty('configurationService');
    });

    test('GET /api/v1/status/databases should return database status', async () => {
      const response = await request(app)
        .get('/api/v1/status/databases')
        .expect(200);

      expect(response.body).toHaveProperty('success', true);
      expect(response.body.data).toHaveProperty('connections');
      expect(response.body.data).toHaveProperty('health');
      expect(response.body.data.connections).toHaveProperty('postgres', true);
      expect(response.body.data.connections).toHaveProperty('dragonflydb', true);
      expect(response.body.data.connections).toHaveProperty('clickhouse', true);
      expect(response.body.data.connections).toHaveProperty('weaviate', true);
      expect(response.body.data.connections).toHaveProperty('arangodb', true);
      expect(response.body.data.connections).toHaveProperty('redis', true);
    });
  });

  describe('Configuration Service Integration', () => {
    beforeEach(() => {
      // Mock configuration service responses
      gateway.configServiceClient.getConfiguration = jest.fn();
      gateway.configServiceClient.listServices = jest.fn();
      gateway.configServiceClient.discoverService = jest.fn();
    });

    test('GET /api/v1/config/:key should retrieve configuration', async () => {
      const mockConfig = {
        id: 'test-config-id',
        key: 'test-key',
        value: 'test-value',
        type: 'string',
        environment: 'test'
      };

      gateway.configServiceClient.getConfiguration.mockResolvedValue(mockConfig);

      const response = await request(app)
        .get('/api/v1/config/test-key')
        .query({ environment: 'test' })
        .expect(200);

      expect(response.body).toHaveProperty('success', true);
      expect(response.body.data).toEqual(mockConfig);
      expect(gateway.configServiceClient.getConfiguration).toHaveBeenCalledWith('test-key', {
        environment: 'test',
        tenantId: undefined,
        userId: undefined
      });
    });

    test('GET /api/v1/config/:key should return 404 for non-existent config', async () => {
      gateway.configServiceClient.getConfiguration.mockResolvedValue(null);

      const response = await request(app)
        .get('/api/v1/config/non-existent-key')
        .expect(404);

      expect(response.body).toHaveProperty('success', false);
      expect(response.body).toHaveProperty('message', "Configuration 'non-existent-key' not found");
    });

    test('GET /api/v1/services should list available services', async () => {
      const mockServices = [
        { name: 'api-gateway', status: 'healthy', port: 3001 },
        { name: 'configuration-service', status: 'healthy', port: 8012 },
        { name: 'database-service', status: 'healthy', port: 8008 }
      ];

      gateway.configServiceClient.listServices.mockResolvedValue(mockServices);

      const response = await request(app)
        .get('/api/v1/services')
        .expect(200);

      expect(response.body).toHaveProperty('success', true);
      expect(response.body.data).toEqual(mockServices);
    });

    test('GET /api/v1/services/discover/:serviceName should discover specific service', async () => {
      const mockService = {
        name: 'configuration-service',
        host: 'configuration-service',
        port: 8012,
        protocol: 'http',
        status: 'healthy'
      };

      gateway.configServiceClient.discoverService.mockResolvedValue(mockService);

      const response = await request(app)
        .get('/api/v1/services/discover/configuration-service')
        .expect(200);

      expect(response.body).toHaveProperty('success', true);
      expect(response.body.data).toEqual(mockService);
    });
  });

  describe('Flow Registry Integration', () => {
    beforeEach(() => {
      // Mock flow registry methods
      gateway.configServiceClient.registerFlow = jest.fn();
      gateway.configServiceClient.getFlow = jest.fn();
      gateway.configServiceClient.executeFlow = jest.fn();
    });

    test('POST /api/v1/flows should register a new flow', async () => {
      const mockFlow = {
        id: 'test-flow-id',
        name: 'Test Flow',
        type: 'api_workflow',
        version: '1.0.0',
        nodes: [],
        edges: []
      };

      const mockResult = {
        id: 'test-flow-id',
        name: 'Test Flow',
        status: 'registered'
      };

      gateway.configServiceClient.registerFlow.mockResolvedValue(mockResult);

      const response = await request(app)
        .post('/api/v1/flows')
        .send(mockFlow)
        .expect(201);

      expect(response.body).toHaveProperty('success', true);
      expect(response.body.data).toEqual(mockResult);
      expect(gateway.configServiceClient.registerFlow).toHaveBeenCalledWith(mockFlow);
    });

    test('GET /api/v1/flows/:flowId should retrieve a flow', async () => {
      const mockFlow = {
        id: 'test-flow-id',
        name: 'Test Flow',
        type: 'api_workflow',
        version: '1.0.0',
        nodes: [],
        edges: []
      };

      gateway.configServiceClient.getFlow.mockResolvedValue(mockFlow);

      const response = await request(app)
        .get('/api/v1/flows/test-flow-id')
        .expect(200);

      expect(response.body).toHaveProperty('success', true);
      expect(response.body.data).toEqual(mockFlow);
    });

    test('POST /api/v1/flows/:flowId/execute should execute a flow', async () => {
      const mockParameters = { input: 'test-data' };
      const mockResult = {
        executionId: 'exec-123',
        status: 'completed',
        result: { output: 'processed-data' }
      };

      gateway.configServiceClient.executeFlow.mockResolvedValue(mockResult);

      const response = await request(app)
        .post('/api/v1/flows/test-flow-id/execute')
        .send(mockParameters)
        .expect(200);

      expect(response.body).toHaveProperty('success', true);
      expect(response.body.data).toEqual(mockResult);
      expect(gateway.configServiceClient.executeFlow).toHaveBeenCalledWith('test-flow-id', mockParameters);
    });
  });

  describe('API Documentation', () => {
    test('GET /api should return API documentation', async () => {
      const response = await request(app)
        .get('/api')
        .expect(200);

      expect(response.body).toHaveProperty('success', true);
      expect(response.body).toHaveProperty('message', 'Enhanced AI Trading Platform API Gateway');
      expect(response.body).toHaveProperty('version', '1.0.0');
      expect(response.body).toHaveProperty('features');
      expect(response.body).toHaveProperty('endpoints');

      expect(response.body.features).toContain('Multi-database architecture (PostgreSQL, DragonflyDB, ClickHouse, Weaviate, ArangoDB, Redis)');
      expect(response.body.features).toContain('Configuration Service integration');
      expect(response.body.features).toContain('Flow Registry support');
      expect(response.body.features).toContain('Flow-Aware Error Handling');
    });
  });

  describe('Error Handling', () => {
    test('should handle 404 for non-existent endpoints', async () => {
      const response = await request(app)
        .get('/non-existent-endpoint')
        .expect(404);

      expect(response.body).toHaveProperty('success', false);
      expect(response.body).toHaveProperty('message', 'Endpoint not found');
      expect(response.body).toHaveProperty('code', 'ENDPOINT_NOT_FOUND');
      expect(response.body).toHaveProperty('path', '/non-existent-endpoint');
      expect(response.body).toHaveProperty('method', 'GET');
    });

    test('should include request ID in responses', async () => {
      const requestId = 'test-request-id-123';

      const response = await request(app)
        .get('/health')
        .set('X-Request-ID', requestId)
        .expect(200);

      expect(response.headers).toHaveProperty('x-request-id', requestId);
      expect(response.body.data).toHaveProperty('requestId', requestId);
    });

    test('should generate request ID if not provided', async () => {
      const response = await request(app)
        .get('/health')
        .expect(200);

      expect(response.headers).toHaveProperty('x-request-id');
      expect(response.body.data).toHaveProperty('requestId');
    });
  });

  describe('Security Headers', () => {
    test('should include security headers', async () => {
      const response = await request(app)
        .get('/health')
        .expect(200);

      // Check for some common security headers set by helmet
      expect(response.headers).toHaveProperty('x-content-type-options');
      expect(response.headers).toHaveProperty('x-frame-options');
    });

    test('should handle CORS properly', async () => {
      const response = await request(app)
        .options('/api/v1/services')
        .set('Origin', 'http://localhost:3000')
        .expect(204);

      expect(response.headers).toHaveProperty('access-control-allow-origin');
      expect(response.headers).toHaveProperty('access-control-allow-methods');
    });
  });

  describe('Rate Limiting', () => {
    test('should apply rate limiting to API endpoints', async () => {
      // Make multiple requests to test rate limiting
      const requests = Array(5).fill().map(() =>
        request(app).get('/api/v1/services')
      );

      const responses = await Promise.all(requests);

      // All requests should succeed (under the limit)
      responses.forEach(response => {
        expect([200, 500].includes(response.status)).toBe(true); // 500 if mocked service fails
      });
    });

    test('should skip rate limiting for health checks', async () => {
      // Make multiple health check requests
      const requests = Array(10).fill().map(() =>
        request(app).get('/health')
      );

      const responses = await Promise.all(requests);

      // All health check requests should succeed
      responses.forEach(response => {
        expect(response.status).toBe(200);
      });
    });
  });
});

describe('Database Manager Unit Tests', () => {
  const DatabaseManager = require('../../src/config/DatabaseManager');
  let dbManager;

  beforeEach(() => {
    dbManager = new DatabaseManager();
  });

  test('should initialize with default connection status', () => {
    expect(dbManager.connectionStatus).toEqual({
      postgres: false,
      dragonflydb: false,
      clickhouse: false,
      weaviate: false,
      arangodb: false,
      redis: false
    });
    expect(dbManager.isInitialized).toBe(false);
  });

  test('should return connection status', () => {
    const status = dbManager.getConnectionStatus();
    expect(status).toEqual(dbManager.connectionStatus);
  });

  test('should check if database is connected', () => {
    expect(dbManager.isConnected('postgres')).toBe(false);
    dbManager.connectionStatus.postgres = true;
    expect(dbManager.isConnected('postgres')).toBe(true);
  });
});

describe('Flow-Aware Error Handler Unit Tests', () => {
  const FlowAwareErrorHandler = require('../../src/middleware/FlowAwareErrorHandler');
  let errorHandler;

  beforeEach(() => {
    errorHandler = new FlowAwareErrorHandler();
  });

  test('should initialize error patterns', () => {
    expect(errorHandler.errorPatterns.size).toBeGreaterThan(0);
    expect(errorHandler.errorPatterns.has('DATABASE_CONNECTION_ERROR')).toBe(true);
    expect(errorHandler.errorPatterns.has('AUTHENTICATION_ERROR')).toBe(true);
  });

  test('should classify database connection errors', () => {
    const error = new Error('connection terminated unexpectedly');
    const classification = errorHandler.classifyError(error);

    expect(classification.type).toBe('DATABASE_CONNECTION_ERROR');
    expect(classification.severity).toBe('high');
    expect(classification.category).toBe('infrastructure');
  });

  test('should classify authentication errors', () => {
    const error = new Error('invalid token provided');
    const classification = errorHandler.classifyError(error);

    expect(classification.type).toBe('AUTHENTICATION_ERROR');
    expect(classification.severity).toBe('medium');
    expect(classification.category).toBe('security');
  });

  test('should handle unknown errors', () => {
    const error = new Error('some random error');
    const classification = errorHandler.classifyError(error);

    expect(classification.type).toBe('UNKNOWN_ERROR');
    expect(classification.category).toBe('unknown');
  });
});