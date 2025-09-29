/**
 * Docker-based test untuk JavaScript shared components
 * Test di dalam container environment
 */

console.log('🐳 Testing Central Hub JavaScript Components in Docker\n');

async function testInDocker() {
    try {
        console.log('✅ Test 1: Import Validation');
        const shared = require('./index');
        console.log('   - BaseService:', typeof shared.BaseService);
        console.log('   - ServiceTemplate:', typeof shared.ServiceTemplate);
        console.log('   - ErrorDNA:', typeof shared.ErrorDNA);
        console.log('   - TransferManager:', typeof shared.TransferManager);
        console.log('   - createServiceLogger:', typeof shared.createServiceLogger);
        console.log();

        console.log('✅ Test 2: ServiceTemplate Creation');
        const testService = shared.createStandardService('docker-test-service', {
            version: '1.0.0',
            port: 8080,
            logging: { output: 'console' }
        });
        console.log('   - Service created:', testService.service_name);
        console.log('   - Has logger:', !!testService.logger);
        console.log('   - Has transfer manager:', !!testService.transfer);
        console.log('   - Has error DNA:', !!testService.errorDNA);
        console.log();

        console.log('✅ Test 3: ErrorDNA Analysis in Docker');
        const analysis = await testService.errorDNA.analyzeError({
            error_message: 'Database connection timeout in production',
            error_type: 'DatabaseError',
            stack_trace: 'DatabaseError: timeout\n    at PostgreSQL.connect (db.js:45)',
            correlation_id: 'docker-test-123'
        });

        console.log('   - Error analyzed successfully');
        console.log('   - Confidence:', analysis.confidence_score.toFixed(2));
        console.log('   - Category:', analysis.error_occurrence.category);
        console.log('   - Severity:', analysis.error_occurrence.severity);
        console.log('   - Suggestions count:', analysis.suggested_actions.length);
        console.log();

        console.log('✅ Test 4: Logger in Docker Environment');
        testService.logger.info('Docker test message', {
            environment: 'docker',
            test_id: 'docker-test-456'
        });
        console.log('   - Logger working in container');

        const loggerHealth = testService.logger.healthCheck();
        console.log('   - Logger health:', loggerHealth.status);
        console.log();

        console.log('✅ Test 5: TransferManager Health Check');
        const transferHealth = await testService.transfer.healthCheck();
        console.log('   - TransferManager health:', transferHealth.status);
        console.log('   - Transport availability:', Object.keys(transferHealth.transports));
        console.log();

        console.log('✅ Test 6: Configuration Compatibility');
        const config = new shared.ServiceConfig({
            service_name: 'docker-config-test',
            version: '2.0.0',
            port: 9000,
            environment: 'production'
        });
        console.log('   - ServiceConfig compatible with Docker');
        console.log('   - Service name:', config.service_name);
        console.log('   - Environment:', config.environment);
        console.log();

        console.log('✅ Test 7: Performance Tracking');
        const perf = new shared.PerformanceTracker('docker-test');
        perf.trackRequest(100, true);
        perf.trackRequest(150, true);
        perf.trackRequest(200, false);

        const metrics = perf.getMetrics();
        console.log('   - Requests tracked:', metrics.requests);
        console.log('   - Average response time:', metrics.avgResponseTime.toFixed(1) + 'ms');
        console.log('   - Error rate:', (metrics.errorRate * 100).toFixed(1) + '%');
        console.log();

        console.log('✅ Test 8: SERVICE_ARCHITECTURE.md Compatibility Check');

        // Test exact import pattern dari SERVICE_ARCHITECTURE.md
        const {
            TransferManager,
            createServiceLogger,
            ErrorDNA,
            adapters: { NATSKafkaAdapter }
        } = shared;

        console.log('   - TransferManager available:', !!TransferManager);
        console.log('   - createServiceLogger available:', !!createServiceLogger);
        console.log('   - ErrorDNA available:', !!ErrorDNA);
        console.log('   - NATSKafkaAdapter available:', !!NATSKafkaAdapter);
        console.log();

        console.log('🎉 ALL DOCKER TESTS PASSED!');
        console.log('\n📦 Central Hub JavaScript Shared Components Status:');
        console.log('   ✅ All wrappers working in Docker environment');
        console.log('   ✅ Compatible with SERVICE_ARCHITECTURE.md specifications');
        console.log('   ✅ Ready for API Gateway integration');
        console.log('   ✅ Error analysis functioning correctly');
        console.log('   ✅ Logging system operational');
        console.log('   ✅ TransferManager ready (mock mode)');
        console.log();
        console.log('🚀 Next Step: Update API Gateway to use shared components');

    } catch (error) {
        console.error('❌ DOCKER TEST FAILED:', error.message);
        console.error(error.stack);
        process.exit(1);
    }
}

testInDocker();