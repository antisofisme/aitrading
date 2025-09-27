/**
 * Test Client-MT5 untuk testing API Gateway
 *
 * Simulasi Client-MT5 yang mengirim binary data menggunakan Suho Binary Protocol
 * Test WebSocket dan HTTP connections
 */

const WebSocket = require('ws');
const http = require('http');
const https = require('https');

class TestClientMT5 {
    constructor(options = {}) {
        this.options = {
            apiGatewayUrl: options.apiGatewayUrl || 'http://localhost:8000',
            websocketTradingUrl: options.websocketTradingUrl || 'ws://localhost:8001/ws/trading',
            websocketPriceUrl: options.websocketPriceUrl || 'ws://localhost:8002/ws/price-stream',
            tenantId: options.tenantId || 'test_tenant_123',
            userId: options.userId || 'test_user_456',
            ...options
        };

        this.tradingWs = null;
        this.priceWs = null;
        this.testResults = [];
    }

    /**
     * Create Suho Binary Protocol packet
     */
    createSuhoBinaryPacket(messageType, data) {
        const magic = 0x53554854; // "SUHT" (SUHO Trading)
        const version = 1;
        const timestamp = Date.now();

        // Convert data to JSON string first
        const jsonData = JSON.stringify(data);
        const dataBuffer = Buffer.from(jsonData, 'utf8');

        // Create header (16 bytes)
        const header = Buffer.allocUnsafe(16);
        header.writeUInt32LE(magic, 0);      // Magic number
        header.writeUInt16LE(version, 4);    // Version
        header.writeUInt8(messageType, 6);   // Message type
        header.writeUInt8(0, 7);            // Reserved
        header.writeUInt32LE(dataBuffer.length, 8); // Data length
        header.writeUInt32LE(timestamp & 0xFFFFFFFF, 12); // Timestamp (lower 32 bits)

        // Combine header and data
        return Buffer.concat([header, dataBuffer]);
    }

    /**
     * Test HTTP API endpoint
     */
    async testHttpApi() {
        console.log('🌐 Testing HTTP API...');

        const testData = {
            symbol: 'EURUSD',
            bid: 1.08955,
            ask: 1.08957,
            volume: 1000,
            timestamp: Date.now(),
            mt5_account_id: 12345
        };

        // Create Suho binary packet
        const binaryPacket = this.createSuhoBinaryPacket(1, testData); // Message type 1 = price_stream

        const options = {
            hostname: 'localhost',
            port: 8000,
            path: '/api/client-mt5/input',
            method: 'POST',
            headers: {
                'Content-Type': 'application/octet-stream',
                'Content-Length': binaryPacket.length,
                'X-Tenant-ID': this.options.tenantId,
                'X-User-ID': this.options.userId,
                'X-Session-ID': `http_test_${Date.now()}`,
                'X-Correlation-ID': `test_corr_${Date.now()}`
            }
        };

        return new Promise((resolve, reject) => {
            const req = http.request(options, (res) => {
                let data = '';

                res.on('data', (chunk) => {
                    data += chunk;
                });

                res.on('end', () => {
                    try {
                        const response = JSON.parse(data);
                        console.log('✅ HTTP API Response:', {
                            status: res.statusCode,
                            success: response.success,
                            message: response.message,
                            routingTargets: response.routing_targets?.length || 0
                        });

                        this.testResults.push({
                            test: 'HTTP API',
                            status: res.statusCode === 200 ? 'PASS' : 'FAIL',
                            response: response
                        });

                        resolve(response);
                    } catch (error) {
                        console.error('❌ HTTP API Parse Error:', error);
                        reject(error);
                    }
                });
            });

            req.on('error', (error) => {
                console.error('❌ HTTP API Error:', error);
                this.testResults.push({
                    test: 'HTTP API',
                    status: 'ERROR',
                    error: error.message
                });
                reject(error);
            });

            // Send binary data
            req.write(binaryPacket);
            req.end();
        });
    }

    /**
     * Test WebSocket Trading Channel
     */
    async testWebSocketTrading() {
        console.log('🔌 Testing WebSocket Trading Channel...');

        return new Promise((resolve, reject) => {
            try {
                this.tradingWs = new WebSocket(this.options.websocketTradingUrl);

                this.tradingWs.on('open', () => {
                    console.log('✅ Trading WebSocket Connected');

                    // Send trading command
                    const tradingCommand = {
                        command: 'place_order',
                        symbol: 'GBPUSD',
                        volume: 0.1,
                        order_type: 'buy',
                        price: 1.26543,
                        mt5_account_id: 12345,
                        timestamp: Date.now()
                    };

                    const binaryPacket = this.createSuhoBinaryPacket(2, tradingCommand); // Message type 2 = trading_command
                    this.tradingWs.send(binaryPacket);
                });

                this.tradingWs.on('message', (data) => {
                    try {
                        const response = JSON.parse(data.toString());
                        console.log('📩 Trading WebSocket Response:', response);

                        this.testResults.push({
                            test: 'WebSocket Trading',
                            status: 'PASS',
                            response: response
                        });

                        resolve(response);
                    } catch (error) {
                        console.log('📩 Trading WebSocket Binary Response received (length:', data.length, ')');

                        this.testResults.push({
                            test: 'WebSocket Trading',
                            status: 'PASS',
                            response: 'Binary data received'
                        });

                        resolve({ binary: true, length: data.length });
                    }
                });

                this.tradingWs.on('error', (error) => {
                    console.error('❌ Trading WebSocket Error:', error);
                    this.testResults.push({
                        test: 'WebSocket Trading',
                        status: 'ERROR',
                        error: error.message
                    });
                    reject(error);
                });

                // Timeout after 10 seconds
                setTimeout(() => {
                    if (this.tradingWs.readyState === WebSocket.OPEN) {
                        this.tradingWs.close();
                        console.log('⏰ Trading WebSocket Timeout - closing connection');
                        resolve({ timeout: true });
                    }
                }, 10000);

            } catch (error) {
                console.error('❌ Trading WebSocket Setup Error:', error);
                reject(error);
            }
        });
    }

    /**
     * Test WebSocket Price Stream Channel
     */
    async testWebSocketPriceStream() {
        console.log('📊 Testing WebSocket Price Stream Channel...');

        return new Promise((resolve, reject) => {
            try {
                this.priceWs = new WebSocket(this.options.websocketPriceUrl);

                this.priceWs.on('open', () => {
                    console.log('✅ Price Stream WebSocket Connected');

                    // Send price data
                    const priceData = {
                        symbol: 'EURUSD',
                        bid: 1.08960,
                        ask: 1.08962,
                        volume: 2000,
                        spread: 0.00002,
                        mt5_account_id: 12345,
                        timestamp: Date.now()
                    };

                    const binaryPacket = this.createSuhoBinaryPacket(1, priceData); // Message type 1 = price_stream
                    this.priceWs.send(binaryPacket);
                });

                this.priceWs.on('message', (data) => {
                    try {
                        const response = JSON.parse(data.toString());
                        console.log('📈 Price Stream WebSocket Response:', response);

                        this.testResults.push({
                            test: 'WebSocket Price Stream',
                            status: 'PASS',
                            response: response
                        });

                        resolve(response);
                    } catch (error) {
                        console.log('📈 Price Stream WebSocket Binary Response received (length:', data.length, ')');

                        this.testResults.push({
                            test: 'WebSocket Price Stream',
                            status: 'PASS',
                            response: 'Binary data received'
                        });

                        resolve({ binary: true, length: data.length });
                    }
                });

                this.priceWs.on('error', (error) => {
                    console.error('❌ Price Stream WebSocket Error:', error);
                    this.testResults.push({
                        test: 'WebSocket Price Stream',
                        status: 'ERROR',
                        error: error.message
                    });
                    reject(error);
                });

                // Timeout after 10 seconds
                setTimeout(() => {
                    if (this.priceWs.readyState === WebSocket.OPEN) {
                        this.priceWs.close();
                        console.log('⏰ Price Stream WebSocket Timeout - closing connection');
                        resolve({ timeout: true });
                    }
                }, 10000);

            } catch (error) {
                console.error('❌ Price Stream WebSocket Setup Error:', error);
                reject(error);
            }
        });
    }

    /**
     * Test API Gateway Health
     */
    async testHealthCheck() {
        console.log('🏥 Testing API Gateway Health...');

        const options = {
            hostname: 'localhost',
            port: 8000,
            path: '/health',
            method: 'GET'
        };

        return new Promise((resolve, reject) => {
            const req = http.request(options, (res) => {
                let data = '';

                res.on('data', (chunk) => {
                    data += chunk;
                });

                res.on('end', () => {
                    try {
                        const response = JSON.parse(data);
                        console.log('✅ Health Check Response:', {
                            status: res.statusCode,
                            health: response.status,
                            uptime: response.uptime_ms
                        });

                        this.testResults.push({
                            test: 'Health Check',
                            status: res.statusCode === 200 ? 'PASS' : 'FAIL',
                            response: response
                        });

                        resolve(response);
                    } catch (error) {
                        console.error('❌ Health Check Parse Error:', error);
                        reject(error);
                    }
                });
            });

            req.on('error', (error) => {
                console.error('❌ Health Check Error:', error);
                this.testResults.push({
                    test: 'Health Check',
                    status: 'ERROR',
                    error: error.message
                });
                reject(error);
            });

            req.end();
        });
    }

    /**
     * Run all tests
     */
    async runAllTests() {
        console.log('🚀 Starting Client-MT5 Test Suite...');
        console.log('='.repeat(50));

        try {
            // Test 1: Health Check
            await this.testHealthCheck();
            await this.sleep(1000);

            // Test 2: HTTP API
            await this.testHttpApi();
            await this.sleep(1000);

            // Test 3: WebSocket Trading
            await this.testWebSocketTrading();
            await this.sleep(1000);

            // Test 4: WebSocket Price Stream
            await this.testWebSocketPriceStream();
            await this.sleep(1000);

        } catch (error) {
            console.error('🔥 Test Suite Error:', error);
        } finally {
            // Cleanup
            this.cleanup();

            // Print test results
            this.printTestResults();
        }
    }

    /**
     * Cleanup connections
     */
    cleanup() {
        if (this.tradingWs) {
            this.tradingWs.close();
            this.tradingWs = null;
        }

        if (this.priceWs) {
            this.priceWs.close();
            this.priceWs = null;
        }
    }

    /**
     * Print test results summary
     */
    printTestResults() {
        console.log('\n' + '='.repeat(50));
        console.log('📋 Test Results Summary');
        console.log('='.repeat(50));

        let passed = 0;
        let failed = 0;
        let errors = 0;

        this.testResults.forEach(result => {
            const icon = result.status === 'PASS' ? '✅' : result.status === 'FAIL' ? '❌' : '🔥';
            console.log(`${icon} ${result.test}: ${result.status}`);

            if (result.status === 'PASS') passed++;
            else if (result.status === 'FAIL') failed++;
            else errors++;
        });

        console.log('='.repeat(50));
        console.log(`📊 Total: ${this.testResults.length} | Passed: ${passed} | Failed: ${failed} | Errors: ${errors}`);
        console.log('='.repeat(50));

        if (passed === this.testResults.length) {
            console.log('🎉 All tests passed! API Gateway is working correctly.');
        } else {
            console.log('⚠️ Some tests failed. Check the logs above for details.');
        }
    }

    /**
     * Sleep utility
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Run tests if this file is executed directly
if (require.main === module) {
    const testClient = new TestClientMT5({
        tenantId: process.env.TENANT_ID || 'test_tenant_123',
        userId: process.env.USER_ID || 'test_user_456'
    });

    testClient.runAllTests().catch(error => {
        console.error('💥 Test execution failed:', error);
        process.exit(1);
    });
}

module.exports = TestClientMT5;