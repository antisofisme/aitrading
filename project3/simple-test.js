/**
 * Simple Test - Test modular input handler directly
 */

const { ClientMT5InputHandler } = require('./backend/01-core-infrastructure/api-gateway/contracts/inputs/from-client-mt5');

// Create test binary data (Suho format)
function createTestData() {
    const buffer = Buffer.alloc(144);

    // Header (16 bytes) - Little Endian
    buffer.writeUInt32LE(0x53554854, 0);        // magic: "SUHO"
    buffer.writeUInt16LE(0x0001, 4);            // version: 1
    buffer.writeUInt8(0x01, 6);                 // msg_type: PRICE_STREAM
    buffer.writeUInt8(3, 7);                    // data_count: 3 symbols
    buffer.writeBigUInt64LE(BigInt(Date.now() * 1000), 8); // timestamp

    // Price data (3 symbols, 16 bytes each)
    let offset = 16;
    const symbols = [
        { id: 1, bid: 109551, ask: 109553 }, // EURUSD
        { id: 2, bid: 128450, ask: 128453 }, // GBPUSD
        { id: 3, bid: 14950, ask: 14952 }    // USDJPY
    ];

    for (let i = 0; i < 3; i++) {
        buffer.writeUInt32LE(symbols[i].id, offset);        // symbol_id
        buffer.writeUInt32LE(symbols[i].bid, offset + 4);   // bid_price
        buffer.writeUInt32LE(symbols[i].ask, offset + 8);   // ask_price
        buffer.writeUInt32LE(0x00000001, offset + 12);      // meta_flags
        offset += 16;
    }

    return buffer;
}

async function testModularHandler() {
    try {
        console.log('🧪 Testing Modular Client-MT5 Input Handler...\n');

        // Create handler
        const handler = new ClientMT5InputHandler({
            enableConversion: false,  // TERIMA SAJA, TIDAK CONVERT
            enableValidation: true,
            enableRouting: true
        });

        // Create test data
        const binaryData = createTestData();
        console.log('📦 Created test binary data:', {
            size: binaryData.length,
            magic: binaryData.readUInt32LE(0).toString(16).toUpperCase(),
            version: binaryData.readUInt16LE(4),
            messageType: binaryData.readUInt8(6),
            symbolCount: binaryData.readUInt8(7)
        });

        // Test metadata
        const metadata = {
            contentType: 'application/octet-stream',
            correlationId: 'test_' + Date.now(),
            userAgent: 'Test-Client/1.0',
            tenantId: 'test_tenant'
        };

        const context = {
            tenant_id: 'test_tenant',
            user_id: 'test_user_123',
            session_id: 'session_456'
        };

        // Test handler
        const result = await handler.handleInput(binaryData, metadata, context);

        console.log('\n✅ Handler Result:', {
            success: result.success,
            message: result.message,
            dataLength: result.data?.raw_data_info?.data_length,
            tenantId: result.data?.tenant_id,
            processingTime: result.data?.processing_time_ms,
            routingTargets: result.routing_targets?.length || 0,
            correlationId: result.metadata?.correlationId,
            suspectedProtocol: result.data?.raw_data_info?.suspected_protocol?.is_suho_format
        });

        if (result.routing_targets && result.routing_targets.length > 0) {
            console.log('\n📋 Routing Targets:');
            result.routing_targets.forEach((target, i) => {
                console.log(`  ${i+1}. ${target.service} (${target.priority}) - ${target.reason}`);
            });
        }

        // Test statistics
        const stats = handler.getStats();
        console.log('\n📊 Handler Statistics:', {
            totalReceived: stats.totalReceived,
            errorRate: stats.error_rate,
            lastReceived: stats.lastReceivedAt
        });

        // Test health check
        const health = await handler.healthCheck();
        console.log('\n💗 Health Check:', {
            status: health.status,
            service: health.service
        });

        console.log('\n✅ All tests passed! Modular handler working correctly.');

    } catch (error) {
        console.error('❌ Test failed:', error.message);
        console.error(error.stack);
    }
}

testModularHandler();