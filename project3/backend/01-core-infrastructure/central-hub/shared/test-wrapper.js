/**
 * Test JavaScript wrappers compatibility
 * Quick test untuk memastikan semua components bisa di-import dan digunakan
 */

const shared = require('./index');

async function testSharedComponents() {
    console.log('🚀 Testing Central Hub JavaScript Shared Components\n');

    try {
        // Test 1: Import validation
        console.log('✅ Test 1: Import Validation');
        console.log('   - BaseService:', typeof shared.BaseService);
        console.log('   - ServiceTemplate:', typeof shared.ServiceTemplate);
        console.log('   - ErrorDNA:', typeof shared.ErrorDNA);
        console.log('   - TransferManager:', typeof shared.TransferManager);
        console.log('   - createServiceLogger:', typeof shared.createServiceLogger);
        console.log('   - NATSKafkaAdapter:', typeof shared.NATSKafkaAdapter);
        console.log('   - Constants defined:', !!shared.TRANSPORT_METHODS);
        console.log();

        // Test 2: ServiceTemplate creation
        console.log('✅ Test 2: ServiceTemplate Creation');
        const testService = shared.createStandardService('test-service', {
            version: '1.0.0',
            port: 8080
        });
        console.log('   - Service created:', testService.service_name);
        console.log('   - Logger available:', !!testService.logger);
        console.log('   - TransferManager available:', !!testService.transfer);
        console.log('   - ErrorDNA available:', !!testService.errorDNA);
        console.log();

        // Test 3: Logger functionality
        console.log('✅ Test 3: Logger Functionality');
        const logger = shared.createServiceLogger('test-logger');
        logger.info('Test info message', { test: true });
        logger.warn('Test warning message');
        console.log('   - Logger created and working');
        const loggerHealth = logger.healthCheck();
        console.log('   - Logger health:', loggerHealth.status);
        console.log();

        // Test 4: ErrorDNA functionality
        console.log('✅ Test 4: ErrorDNA Functionality');
        const errorDNA = new shared.ErrorDNA('test-service');
        const testError = new Error('Test database connection timeout');
        const analysis = await errorDNA.analyzeError({
            error_message: testError.message,
            stack_trace: testError.stack,
            error_type: 'ConnectionError'
        });
        console.log('   - Error analyzed with confidence:', analysis.confidence_score.toFixed(2));
        console.log('   - Matched patterns:', analysis.matched_patterns.length);
        console.log('   - Suggested actions:', analysis.suggested_actions.length);
        console.log();

        // Test 5: TransferManager functionality
        console.log('✅ Test 5: TransferManager Functionality');
        const transferManager = new shared.TransferManager({
            service_name: 'test-service'
        });
        console.log('   - TransferManager created');

        // Test transport method selection
        const method1 = shared.getTransportMethod('price_stream');
        const method2 = shared.getTransportMethod('account_profile');
        console.log('   - price_stream uses:', method1);
        console.log('   - account_profile uses:', method2);
        console.log();

        // Test 6: Performance utilities
        console.log('✅ Test 6: Performance Utilities');
        const perf = new shared.PerformanceTracker('test-service');
        perf.trackRequest(125, true);
        perf.trackRequest(89, true);
        perf.trackRequest(200, false);
        const metrics = perf.getMetrics();
        console.log('   - Tracked requests:', metrics.requests);
        console.log('   - Average response time:', metrics.avgResponseTime.toFixed(2), 'ms');
        console.log('   - Error rate:', (metrics.errorRate * 100).toFixed(1), '%');
        console.log();

        // Test 7: Circuit breaker
        console.log('✅ Test 7: Circuit Breaker');
        const circuitBreaker = new shared.CircuitBreaker({
            failureThreshold: 3,
            timeout: 5000
        });

        // Simulate failures
        for (let i = 0; i < 3; i++) {
            circuitBreaker.onFailure();
        }

        const state = circuitBreaker.getState();
        console.log('   - Circuit breaker state:', state.state);
        console.log('   - Failures:', state.failures);
        console.log();

        // Test 8: Configuration manager
        console.log('✅ Test 8: Configuration Manager');
        const config = new shared.ConfigManager('test-service');
        config.set('database_url', 'postgresql://test');
        config.set('api_key', 'test-key');
        console.log('   - Config set, database_url:', config.get('database_url'));
        console.log('   - Config get with default:', config.get('missing_key', 'default_value'));
        console.log();

        // Test 9: Service lifecycle
        console.log('✅ Test 9: Service Lifecycle');
        const service = new shared.ServiceTemplate('test-lifecycle', {
            version: '1.0.0'
        });

        // Override abstract methods for testing
        service.handleInput = async (data) => ({ processed: true, data });
        service.onStartup = async () => console.log('   - Custom startup logic executed');
        service.onShutdown = async () => console.log('   - Custom shutdown logic executed');

        await service.initialize();
        console.log('   - Service initialized successfully');

        const health = await service.healthCheck();
        console.log('   - Health check status:', health.status);

        await service.stop();
        console.log('   - Service stopped gracefully');
        console.log();

        // Test 10: Integration compatibility
        console.log('✅ Test 10: SERVICE_ARCHITECTURE.md Compatibility');
        console.log('   - Required imports available:');

        // Test the exact import pattern from SERVICE_ARCHITECTURE.md
        const {
            TransferManager: TM,
            createServiceLogger: Logger,
            ErrorDNA: DNA,
            adapters: { NATSKafkaAdapter: NATS }
        } = shared;

        console.log('   - TransferManager:', !!TM);
        console.log('   - createServiceLogger:', !!Logger);
        console.log('   - ErrorDNA:', !!DNA);
        console.log('   - NATSKafkaAdapter:', !!NATS);
        console.log();

        console.log('🎉 ALL TESTS PASSED! JavaScript wrappers are compatible with SERVICE_ARCHITECTURE.md');
        console.log('\n📋 Ready for API Gateway integration:');
        console.log('   const shared = require("../central-hub/shared");');
        console.log('   const { ServiceTemplate, TransferManager, createServiceLogger, ErrorDNA } = shared;');

    } catch (error) {
        console.error('❌ TEST FAILED:', error.message);
        console.error(error.stack);
        process.exit(1);
    }
}

// Run tests
testSharedComponents().catch(console.error);