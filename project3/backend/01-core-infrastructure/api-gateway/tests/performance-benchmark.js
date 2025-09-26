/**
 * Performance Benchmark for Suho Binary Protocol vs JSON
 *
 * Measures and compares performance metrics:
 * - Processing time (serialization/deserialization)
 * - Memory usage
 * - Bandwidth efficiency
 * - Error rates
 *
 * Based on Client-MT5 specifications showing 92% bandwidth reduction
 * and 80% processing speed improvement.
 */

const { SuhoBinaryProtocol, PROTOCOL_CONSTANTS, MESSAGE_TYPES, TRADING_SYMBOLS } = require('../src/protocols/suho-binary-protocol');

/**
 * Performance Benchmark Runner
 */
class PerformanceBenchmark {
    constructor() {
        this.binaryProtocol = new SuhoBinaryProtocol();
        this.results = {
            binary: {
                serializationTime: 0,
                deserializationTime: 0,
                totalTime: 0,
                memoryUsage: 0,
                packetSize: 0,
                errorCount: 0
            },
            json: {
                serializationTime: 0,
                deserializationTime: 0,
                totalTime: 0,
                memoryUsage: 0,
                packetSize: 0,
                errorCount: 0
            },
            comparison: {}
        };
    }

    /**
     * Create test data for benchmarking
     */
    createTestData() {
        return {
            // Price stream data (8 symbols)
            priceStream: {
                type: 'price_stream',
                userId: 'user123',
                timestamp: Date.now() * 1000,
                prices: [
                    { symbol: 'EURUSD', bid: 1.09551, ask: 1.09553, spread: 0.00002 },
                    { symbol: 'GBPUSD', bid: 1.27082, ask: 1.27085, spread: 0.00003 },
                    { symbol: 'USDJPY', bid: 150.123, ask: 150.126, spread: 0.003 },
                    { symbol: 'USDCHF', bid: 0.95432, ask: 0.95435, spread: 0.00003 },
                    { symbol: 'AUDUSD', bid: 0.68745, ask: 0.68748, spread: 0.00003 },
                    { symbol: 'USDCAD', bid: 1.32456, ask: 1.32459, spread: 0.00003 },
                    { symbol: 'NZDUSD', bid: 0.62134, ask: 0.62137, spread: 0.00003 },
                    { symbol: 'XAUUSD', bid: 1978.45, ask: 1978.85, spread: 0.40 }
                ]
            },

            // Account profile data
            accountProfile: {
                type: 'account_profile',
                userId: 'user123',
                broker: 'MetaQuotes',
                accountNum: 12345678,
                balance: 10000.00,
                equity: 10015.00,
                margin: 500.00,
                freeMargin: 9515.00,
                leverage: 100,
                currency: 'USD',
                snapshotTime: Date.now() * 1000
            },

            // Trading command data
            tradingCommand: {
                type: 'trading_command',
                commandId: 12345,
                symbol: 'EURUSD',
                action: 'BUY',
                volume: 0.1,
                price: 1.09551,
                stopLoss: 1.09500,
                takeProfit: 1.09600,
                magic: 20241226
            }
        };
    }

    /**
     * Create binary packet for testing
     */
    createBinaryPacket(data) {
        if (data.type === 'price_stream') {
            return this.createPriceStreamPacket(data);
        } else if (data.type === 'account_profile') {
            return this.createAccountProfilePacket(data);
        } else if (data.type === 'trading_command') {
            return this.binaryProtocol.createPacket(data);
        }
        throw new Error(`Unsupported data type: ${data.type}`);
    }

    /**
     * Create price stream binary packet
     */
    createPriceStreamPacket(data) {
        const packetSize = PROTOCOL_CONSTANTS.HEADER_SIZE + (data.prices.length * PROTOCOL_CONSTANTS.PRICE_PACKET_SIZE);
        const buffer = Buffer.alloc(packetSize);

        // Header
        buffer.writeUInt32LE(PROTOCOL_CONSTANTS.BINARY_MAGIC, 0);
        buffer.writeUInt16LE(PROTOCOL_CONSTANTS.BINARY_VERSION, 4);
        buffer.writeUInt8(MESSAGE_TYPES.PRICE_STREAM, 6);
        buffer.writeUInt8(data.prices.length, 7);
        buffer.writeBigUInt64LE(BigInt(data.timestamp), 8);

        // Price packets
        let offset = PROTOCOL_CONSTANTS.HEADER_SIZE;
        for (const price of data.prices) {
            const symbolId = this.binaryProtocol.getSymbolId(price.symbol);
            buffer.writeUInt32LE(symbolId, offset);
            buffer.writeUInt32LE(this.binaryProtocol.priceToFixedPoint(price.bid), offset + 4);
            buffer.writeUInt32LE(this.binaryProtocol.priceToFixedPoint(price.ask), offset + 8);
            buffer.writeUInt32LE(0x00010001, offset + 12); // meta flags
            offset += PROTOCOL_CONSTANTS.PRICE_PACKET_SIZE;
        }

        return buffer;
    }

    /**
     * Create account profile binary packet
     */
    createAccountProfilePacket(data) {
        const buffer = Buffer.alloc(PROTOCOL_CONSTANTS.HEADER_SIZE + PROTOCOL_CONSTANTS.ACCOUNT_SNAPSHOT_SIZE);

        // Header
        buffer.writeUInt32LE(PROTOCOL_CONSTANTS.BINARY_MAGIC, 0);
        buffer.writeUInt16LE(PROTOCOL_CONSTANTS.BINARY_VERSION, 4);
        buffer.writeUInt8(MESSAGE_TYPES.ACCOUNT_PROFILE, 6);
        buffer.writeUInt8(1, 7);
        buffer.writeBigUInt64LE(BigInt(data.timestamp || Date.now() * 1000), 8);

        // Account data
        let offset = PROTOCOL_CONSTANTS.HEADER_SIZE;
        buffer.write(data.userId.padEnd(16, '\0'), offset, 16);
        buffer.write(data.broker.padEnd(16, '\0'), offset + 16, 16);
        buffer.writeUInt32LE(data.accountNum, offset + 32);
        buffer.writeUInt32LE(Math.round(data.balance * 100), offset + 36);
        buffer.writeUInt32LE(Math.round(data.equity * 100), offset + 40);
        buffer.writeUInt32LE(Math.round(data.margin * 100), offset + 44);
        buffer.writeUInt32LE(Math.round(data.freeMargin * 100), offset + 48);
        buffer.writeUInt16LE(data.leverage, offset + 52);
        buffer.write(data.currency.padEnd(3, '\0'), offset + 54, 3);
        buffer.writeBigUInt64LE(BigInt(data.snapshotTime), offset + 58);

        return buffer;
    }

    /**
     * Run binary protocol benchmark
     */
    async runBinaryBenchmark(testData, iterations = 10000) {
        console.log(`\n🔥 Running Binary Protocol Benchmark (${iterations} iterations)...`);

        const memoryBefore = process.memoryUsage().heapUsed;
        let totalSerializationTime = 0;
        let totalDeserializationTime = 0;
        let totalPacketSize = 0;
        let errorCount = 0;

        for (let i = 0; i < iterations; i++) {
            try {
                // Serialization benchmark
                const serializationStart = process.hrtime.bigint();
                const binaryPacket = this.createBinaryPacket(testData.priceStream);
                const serializationEnd = process.hrtime.bigint();

                totalSerializationTime += Number(serializationEnd - serializationStart) / 1000000; // Convert to ms
                totalPacketSize += binaryPacket.length;

                // Deserialization benchmark
                const deserializationStart = process.hrtime.bigint();
                const parsedData = this.binaryProtocol.parsePacket(binaryPacket);
                const deserializationEnd = process.hrtime.bigint();

                totalDeserializationTime += Number(deserializationEnd - deserializationStart) / 1000000;

                // Validate roundtrip
                if (parsedData.type !== testData.priceStream.type) {
                    errorCount++;
                }

            } catch (error) {
                errorCount++;
            }
        }

        const memoryAfter = process.memoryUsage().heapUsed;

        this.results.binary = {
            serializationTime: totalSerializationTime / iterations,
            deserializationTime: totalDeserializationTime / iterations,
            totalTime: (totalSerializationTime + totalDeserializationTime) / iterations,
            memoryUsage: memoryAfter - memoryBefore,
            packetSize: totalPacketSize / iterations,
            errorCount: errorCount,
            errorRate: (errorCount / iterations) * 100
        };

        console.log('✅ Binary Protocol Benchmark Complete');
    }

    /**
     * Run JSON protocol benchmark
     */
    async runJSONBenchmark(testData, iterations = 10000) {
        console.log(`\n📄 Running JSON Protocol Benchmark (${iterations} iterations)...`);

        const memoryBefore = process.memoryUsage().heapUsed;
        let totalSerializationTime = 0;
        let totalDeserializationTime = 0;
        let totalPacketSize = 0;
        let errorCount = 0;

        for (let i = 0; i < iterations; i++) {
            try {
                // Serialization benchmark
                const serializationStart = process.hrtime.bigint();
                const jsonString = JSON.stringify(testData.priceStream);
                const serializationEnd = process.hrtime.bigint();

                totalSerializationTime += Number(serializationEnd - serializationStart) / 1000000;
                totalPacketSize += Buffer.byteLength(jsonString, 'utf8');

                // Deserialization benchmark
                const deserializationStart = process.hrtime.bigint();
                const parsedData = JSON.parse(jsonString);
                const deserializationEnd = process.hrtime.bigint();

                totalDeserializationTime += Number(deserializationEnd - deserializationStart) / 1000000;

                // Validate roundtrip
                if (parsedData.type !== testData.priceStream.type) {
                    errorCount++;
                }

            } catch (error) {
                errorCount++;
            }
        }

        const memoryAfter = process.memoryUsage().heapUsed;

        this.results.json = {
            serializationTime: totalSerializationTime / iterations,
            deserializationTime: totalDeserializationTime / iterations,
            totalTime: (totalSerializationTime + totalDeserializationTime) / iterations,
            memoryUsage: memoryAfter - memoryBefore,
            packetSize: totalPacketSize / iterations,
            errorCount: errorCount,
            errorRate: (errorCount / iterations) * 100
        };

        console.log('✅ JSON Protocol Benchmark Complete');
    }

    /**
     * Calculate performance comparison
     */
    calculateComparison() {
        const binary = this.results.binary;
        const json = this.results.json;

        this.results.comparison = {
            serializationSpeedup: ((json.serializationTime - binary.serializationTime) / json.serializationTime * 100).toFixed(1),
            deserializationSpeedup: ((json.deserializationTime - binary.deserializationTime) / json.deserializationTime * 100).toFixed(1),
            totalSpeedup: ((json.totalTime - binary.totalTime) / json.totalTime * 100).toFixed(1),
            bandwidthReduction: ((json.packetSize - binary.packetSize) / json.packetSize * 100).toFixed(1),
            memoryReduction: ((json.memoryUsage - binary.memoryUsage) / json.memoryUsage * 100).toFixed(1),
            reliabilityImprovement: ((json.errorRate - binary.errorRate) / json.errorRate * 100).toFixed(1)
        };
    }

    /**
     * Generate performance report
     */
    generateReport() {
        console.log('\n' + '='.repeat(80));
        console.log('🚀 SUHO BINARY PROTOCOL PERFORMANCE REPORT');
        console.log('='.repeat(80));

        console.log('\n📊 PROCESSING PERFORMANCE:');
        console.log('─'.repeat(50));
        console.log(`Binary Serialization:    ${this.results.binary.serializationTime.toFixed(4)} ms`);
        console.log(`JSON Serialization:      ${this.results.json.serializationTime.toFixed(4)} ms`);
        console.log(`Serialization Speedup:   ${this.results.comparison.serializationSpeedup}%`);
        console.log('');
        console.log(`Binary Deserialization:  ${this.results.binary.deserializationTime.toFixed(4)} ms`);
        console.log(`JSON Deserialization:    ${this.results.json.deserializationTime.toFixed(4)} ms`);
        console.log(`Deserialization Speedup: ${this.results.comparison.deserializationSpeedup}%`);
        console.log('');
        console.log(`Binary Total Time:       ${this.results.binary.totalTime.toFixed(4)} ms`);
        console.log(`JSON Total Time:         ${this.results.json.totalTime.toFixed(4)} ms`);
        console.log(`🔥 TOTAL SPEEDUP:        ${this.results.comparison.totalSpeedup}%`);

        console.log('\n📡 BANDWIDTH EFFICIENCY:');
        console.log('─'.repeat(50));
        console.log(`Binary Packet Size:      ${this.results.binary.packetSize.toFixed(0)} bytes`);
        console.log(`JSON Packet Size:        ${this.results.json.packetSize.toFixed(0)} bytes`);
        console.log(`🚀 BANDWIDTH REDUCTION:  ${this.results.comparison.bandwidthReduction}%`);

        console.log('\n💾 MEMORY USAGE:');
        console.log('─'.repeat(50));
        console.log(`Binary Memory:           ${(this.results.binary.memoryUsage / 1024).toFixed(1)} KB`);
        console.log(`JSON Memory:             ${(this.results.json.memoryUsage / 1024).toFixed(1)} KB`);
        console.log(`Memory Efficiency:       ${this.results.comparison.memoryReduction}%`);

        console.log('\n🛡️ RELIABILITY:');
        console.log('─'.repeat(50));
        console.log(`Binary Error Rate:       ${this.results.binary.errorRate.toFixed(4)}%`);
        console.log(`JSON Error Rate:         ${this.results.json.errorRate.toFixed(4)}%`);
        console.log(`Reliability Improvement: ${this.results.comparison.reliabilityImprovement}%`);

        console.log('\n🎯 PRODUCTION IMPACT (Daily Trading - 86,400 messages):');
        console.log('─'.repeat(60));
        const dailyMessages = 86400;
        const binaryDaily = (this.results.binary.packetSize * dailyMessages) / (1024 * 1024 * 1024);
        const jsonDaily = (this.results.json.packetSize * dailyMessages) / (1024 * 1024 * 1024);
        const dailySavings = jsonDaily - binaryDaily;

        console.log(`Binary Daily Bandwidth:  ${binaryDaily.toFixed(2)} GB`);
        console.log(`JSON Daily Bandwidth:    ${jsonDaily.toFixed(2)} GB`);
        console.log(`Daily Bandwidth Savings: ${dailySavings.toFixed(2)} GB`);
        console.log(`Monthly Savings:         ${(dailySavings * 30).toFixed(1)} GB`);
        console.log(`Cost Savings (@ $0.10/GB): $${(dailySavings * 30 * 0.10).toFixed(2)}/month`);

        console.log('\n🏆 ACHIEVEMENT VERIFICATION:');
        console.log('─'.repeat(50));
        const targetBandwidthReduction = 92;
        const targetSpeedImprovement = 80;

        const bandwidthAchieved = parseFloat(this.results.comparison.bandwidthReduction);
        const speedAchieved = parseFloat(this.results.comparison.totalSpeedup);

        console.log(`Target Bandwidth Reduction: ${targetBandwidthReduction}%`);
        console.log(`Achieved Bandwidth Reduction: ${bandwidthAchieved}%`);
        console.log(`${bandwidthAchieved >= targetBandwidthReduction ? '✅' : '❌'} Bandwidth Target ${bandwidthAchieved >= targetBandwidthReduction ? 'MET' : 'MISSED'}`);
        console.log('');
        console.log(`Target Speed Improvement: ${targetSpeedImprovement}%`);
        console.log(`Achieved Speed Improvement: ${speedAchieved}%`);
        console.log(`${speedAchieved >= targetSpeedImprovement ? '✅' : '❌'} Speed Target ${speedAchieved >= targetSpeedImprovement ? 'MET' : 'MISSED'}`);

        console.log('\n' + '='.repeat(80));
        console.log('🎉 SUHO BINARY PROTOCOL PERFORMANCE VALIDATION COMPLETE!');
        console.log('='.repeat(80));

        return this.results;
    }

    /**
     * Run complete benchmark suite
     */
    async runFullBenchmark(iterations = 10000) {
        console.log('🚀 Starting Suho Binary Protocol Performance Benchmark...');
        console.log(`📊 Running ${iterations.toLocaleString()} iterations per test`);

        const testData = this.createTestData();

        // Run binary protocol benchmark
        await this.runBinaryBenchmark(testData, iterations);

        // Run JSON protocol benchmark
        await this.runJSONBenchmark(testData, iterations);

        // Calculate comparisons
        this.calculateComparison();

        // Generate and display report
        return this.generateReport();
    }
}

// Run benchmark if this file is executed directly
if (require.main === module) {
    const benchmark = new PerformanceBenchmark();

    benchmark.runFullBenchmark(10000).then(() => {
        console.log('\n✅ Benchmark completed successfully');
        process.exit(0);
    }).catch((error) => {
        console.error('\n❌ Benchmark failed:', error);
        process.exit(1);
    });
}

module.exports = PerformanceBenchmark;