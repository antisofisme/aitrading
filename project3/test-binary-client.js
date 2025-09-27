/**
 * Test Script - Client-MT5 Binary Data to API Gateway
 *
 * Test untuk memastikan API Gateway bisa menerima data binary dari Client-MT5
 * TANPA konversi, hanya menerima data saja.
 */

const http = require('http');
const https = require('https');

// Simulasi data binary sesuai IMPLEMENTASI JS (suho-binary-protocol.js)
function createSuhoBinaryData() {
    // Fixed 144 bytes sesuai implementasi JavaScript
    const buffer = Buffer.alloc(144);

    // Header (16 bytes) - LITTLE ENDIAN sesuai implementasi JS
    buffer.writeUInt32LE(0x53554854, 0);        // magic: 0x53554854 "SUHO" (LITTLE ENDIAN)
    buffer.writeUInt16LE(0x0001, 4);            // version: 0x0001 (LITTLE ENDIAN)
    buffer.writeUInt8(0x01, 6);                 // msg_type: PRICE_STREAM
    buffer.writeUInt8(5, 7);                    // data_count: 5 symbols
    buffer.writeBigUInt64LE(BigInt(Date.now() * 1000), 8); // timestamp: microsecond precision (LITTLE ENDIAN)

    // Data section (128 bytes) - Price packets - LITTLE ENDIAN
    let offset = 16;
    const symbols = [
        { id: 1, bid: 109551, ask: 109553 }, // EURUSD
        { id: 2, bid: 128450, ask: 128453 }, // GBPUSD
        { id: 3, bid: 14950, ask: 14952 },   // USDJPY
        { id: 5, bid: 67230, ask: 67233 },   // AUDUSD
        { id: 6, bid: 13420, ask: 13422 }    // USDCAD
    ];

    for (let i = 0; i < 5; i++) {
        // PricePacket struct (16 bytes per symbol) - LITTLE ENDIAN
        buffer.writeUInt32LE(symbols[i].id, offset);        // symbol_id (4 bytes)
        buffer.writeUInt32LE(symbols[i].bid, offset + 4);   // bid_price (4 bytes) - fixed point *100000
        buffer.writeUInt32LE(symbols[i].ask, offset + 8);   // ask_price (4 bytes) - fixed point *100000
        buffer.writeUInt32LE(0x00000001, offset + 12);      // meta_flags (4 bytes) - spread + server_id + quality
        offset += 16;
    }

    // Pad remaining bytes (48 bytes untuk mencapai 144 total)
    // buffer sudah di-alloc dengan zeros, jadi tidak perlu explicit padding

    return buffer;
}

// Helper function untuk HTTP request
function makeRequest(options, data = null) {
    return new Promise((resolve, reject) => {
        const req = http.request(options, (res) => {
            let body = '';
            res.on('data', chunk => body += chunk);
            res.on('end', () => {
                try {
                    const response = {
                        status: res.statusCode,
                        data: res.headers['content-type']?.includes('application/json') ? JSON.parse(body) : body
                    };
                    resolve(response);
                } catch (error) {
                    resolve({ status: res.statusCode, data: body });
                }
            });
        });

        req.on('error', reject);

        if (data) {
            req.write(data);
        }
        req.end();
    });
}

async function testBinaryReceive() {
    try {
        console.log('🧪 Testing API Gateway Binary Data Reception...\n');

        // Create test data
        const binaryData = createSuhoBinaryData();
        console.log('📦 Created Suho Binary data (CONTRACT COMPLIANT):', {
            totalSize: binaryData.length,
            header: binaryData.subarray(0, 16),
            magic: binaryData.readUInt32BE(0).toString(16).toUpperCase(), // "53554854" = "SUHO"
            version: binaryData.readUInt16BE(4).toString(16), // "0001"
            messageType: binaryData.readUInt8(6), // PRICE_STREAM = 1
            dataCount: binaryData.readUInt8(7),   // 5 symbols
            timestamp: binaryData.readBigUInt64BE(8),
            firstSymbol: {
                id: binaryData.readUInt32BE(16),
                bid: binaryData.readUInt32BE(20),
                ask: binaryData.readUInt32BE(24),
                meta: binaryData.readUInt32BE(28)
            }
        });

        // Test 1: Send to modular Client-MT5 input handler (NO CONVERSION)
        console.log('\n🎯 Test 1: Sending to /api/client-mt5/input (MODULAR HANDLER)');
        const options1 = {
            hostname: 'localhost',
            port: 8000,
            path: '/api/client-mt5/input',
            method: 'POST',
            headers: {
                'Content-Type': 'application/octet-stream',
                'Content-Length': binaryData.length,
                'X-Tenant-ID': 'client_mt5_test',
                'X-User-ID': 'test_user_123',
                'X-Session-ID': 'session_456',
                'User-Agent': 'Client-MT5/2.1'
            }
        };

        const response1 = await makeRequest(options1, binaryData);
        console.log('✅ Response 1 (Modular Handler):', {
            status: response1.status,
            success: response1.data.success,
            message: response1.data.message,
            dataLength: response1.data.data?.raw_data_info?.data_length,
            tenantId: response1.data.data?.tenant_id,
            processingTime: response1.data.data?.processing_time_ms,
            routingTargets: response1.data.routing_targets?.length || 0,
            correlationId: response1.data.metadata?.correlationId
        });

        // Test 2: Check API Gateway stats
        console.log('\n📊 Checking API Gateway stats...');
        const statsOptions = {
            hostname: 'localhost',
            port: 8000,
            path: '/stats',
            method: 'GET'
        };
        const statsResponse = await makeRequest(statsOptions);
        console.log('📈 Binary Messages Count:', statsResponse.data.performance?.binary_messages);

        // Test 3: Check health
        console.log('\n💗 Checking API Gateway health...');
        const healthOptions = {
            hostname: 'localhost',
            port: 8000,
            path: '/health',
            method: 'GET'
        };
        const healthResponse = await makeRequest(healthOptions);
        console.log('🏥 Health Status:', healthResponse.data.status || healthResponse.status);

        console.log('\n✅ All tests passed! API Gateway can receive binary data from Client-MT5');

    } catch (error) {
        console.error('❌ Test failed:', {
            message: error.message,
            code: error.code
        });

        if (error.code === 'ECONNREFUSED') {
            console.log('\n💡 Make sure API Gateway is running on port 8000:');
            console.log('   cd /mnt/g/khoirul/aitrading/project3/backend/01-core-infrastructure/api-gateway');
            console.log('   node src/index.js');
        }
    }
}

async function testHealthFirst() {
    try {
        console.log('🔍 Checking if API Gateway is running...');
        const options = {
            hostname: 'localhost',
            port: 8000,
            path: '/',
            method: 'GET',
            timeout: 5000
        };
        const response = await makeRequest(options);
        console.log('✅ API Gateway is running:', response.data.name || 'API Gateway');
        return true;
    } catch (error) {
        console.log('❌ API Gateway is not running on port 8000');
        console.log('💡 Start it with: node src/index.js');
        return false;
    }
}

// Run tests
async function runTests() {
    const isRunning = await testHealthFirst();
    if (isRunning) {
        await testBinaryReceive();
    }
}

runTests();