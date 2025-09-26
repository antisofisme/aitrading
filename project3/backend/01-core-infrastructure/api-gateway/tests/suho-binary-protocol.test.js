/**
 * Test Suite for Suho Binary Protocol
 *
 * Comprehensive tests for binary protocol parsing, serialization,
 * and conversion to/from Protocol Buffers.
 */

const { SuhoBinaryProtocol, PROTOCOL_CONSTANTS, MESSAGE_TYPES, TRADING_SYMBOLS } = require('../src/protocols/suho-binary-protocol');

describe('SuhoBinaryProtocol', () => {
    let protocol;
    let validPriceStreamBuffer;
    let validAccountProfileBuffer;

    beforeEach(() => {
        protocol = new SuhoBinaryProtocol();

        // Create valid price stream buffer for testing
        validPriceStreamBuffer = Buffer.alloc(PROTOCOL_CONSTANTS.HEADER_SIZE + PROTOCOL_CONSTANTS.PRICE_PACKET_SIZE);

        // Header
        validPriceStreamBuffer.writeUInt32LE(PROTOCOL_CONSTANTS.BINARY_MAGIC, 0);
        validPriceStreamBuffer.writeUInt16LE(PROTOCOL_CONSTANTS.BINARY_VERSION, 4);
        validPriceStreamBuffer.writeUInt8(MESSAGE_TYPES.PRICE_STREAM, 6);
        validPriceStreamBuffer.writeUInt8(1, 7); // 1 price packet
        validPriceStreamBuffer.writeBigUInt64LE(BigInt(Date.now() * 1000), 8); // Current timestamp

        // Price packet (EURUSD at 1.09551/1.09553)
        let offset = PROTOCOL_CONSTANTS.HEADER_SIZE;
        validPriceStreamBuffer.writeUInt32LE(TRADING_SYMBOLS.EURUSD, offset);
        validPriceStreamBuffer.writeUInt32LE(109551, offset + 4); // bid * 100000
        validPriceStreamBuffer.writeUInt32LE(109553, offset + 8); // ask * 100000
        validPriceStreamBuffer.writeUInt32LE(0x00010001, offset + 12); // meta flags

        // Create valid account profile buffer
        validAccountProfileBuffer = Buffer.alloc(PROTOCOL_CONSTANTS.HEADER_SIZE + PROTOCOL_CONSTANTS.ACCOUNT_SNAPSHOT_SIZE);

        // Header
        validAccountProfileBuffer.writeUInt32LE(PROTOCOL_CONSTANTS.BINARY_MAGIC, 0);
        validAccountProfileBuffer.writeUInt16LE(PROTOCOL_CONSTANTS.BINARY_VERSION, 4);
        validAccountProfileBuffer.writeUInt8(MESSAGE_TYPES.ACCOUNT_PROFILE, 6);
        validAccountProfileBuffer.writeUInt8(1, 7);
        validAccountProfileBuffer.writeBigUInt64LE(BigInt(Date.now() * 1000), 8);

        // Account data
        offset = PROTOCOL_CONSTANTS.HEADER_SIZE;
        validAccountProfileBuffer.write('user123\0\0\0\0\0\0\0\0\0', offset, 16); // user_id
        validAccountProfileBuffer.write('MetaQuotes\0\0\0\0\0\0', offset + 16, 16); // broker
        validAccountProfileBuffer.writeUInt32LE(12345678, offset + 32); // account_num
        validAccountProfileBuffer.writeUInt32LE(1000000, offset + 36); // balance * 100
        validAccountProfileBuffer.writeUInt32LE(1001500, offset + 40); // equity * 100
        validAccountProfileBuffer.writeUInt32LE(50000, offset + 44); // margin * 100
        validAccountProfileBuffer.writeUInt32LE(951500, offset + 48); // free_margin * 100
        validAccountProfileBuffer.writeUInt16LE(100, offset + 52); // leverage
        validAccountProfileBuffer.write('USD', offset + 54, 3); // currency
        validAccountProfileBuffer.writeBigUInt64LE(BigInt(Date.now() * 1000), offset + 58); // snapshot_time
    });

    describe('Packet Validation', () => {
        test('should validate correct magic number', () => {
            expect(protocol.validatePacket(validPriceStreamBuffer)).toBe(true);
        });

        test('should reject invalid magic number', () => {
            const invalidBuffer = Buffer.from(validPriceStreamBuffer);
            invalidBuffer.writeUInt32LE(0x12345678, 0); // Wrong magic
            expect(protocol.validatePacket(invalidBuffer)).toBe(false);
        });

        test('should reject invalid protocol version', () => {
            const invalidBuffer = Buffer.from(validPriceStreamBuffer);
            invalidBuffer.writeUInt16LE(0x9999, 4); // Wrong version
            expect(protocol.validatePacket(invalidBuffer)).toBe(false);
        });

        test('should reject packets with old timestamps', () => {
            const oldBuffer = Buffer.from(validPriceStreamBuffer);
            const oldTimestamp = BigInt((Date.now() - 120000) * 1000); // 2 minutes ago
            oldBuffer.writeBigUInt64LE(oldTimestamp, 8);
            expect(protocol.validatePacket(oldBuffer)).toBe(false);
        });

        test('should reject packets that are too small', () => {
            const tinyBuffer = Buffer.alloc(8);
            expect(protocol.validatePacket(tinyBuffer)).toBe(false);
        });
    });

    describe('Header Parsing', () => {
        test('should parse header correctly', () => {
            const header = protocol.parseHeader(validPriceStreamBuffer);

            expect(header.magic).toBe(PROTOCOL_CONSTANTS.BINARY_MAGIC);
            expect(header.version).toBe(PROTOCOL_CONSTANTS.BINARY_VERSION);
            expect(header.msgType).toBe(MESSAGE_TYPES.PRICE_STREAM);
            expect(header.dataCount).toBe(1);
            expect(typeof header.timestamp).toBe('bigint');
        });
    });

    describe('Price Stream Parsing', () => {
        test('should parse price stream packet correctly', () => {
            const result = protocol.parsePacket(validPriceStreamBuffer);

            expect(result.type).toBe('price_stream');
            expect(result.prices).toHaveLength(1);

            const price = result.prices[0];
            expect(price.symbol).toBe('EURUSD');
            expect(price.symbolId).toBe(TRADING_SYMBOLS.EURUSD);
            expect(price.bid).toBe(1.09551);
            expect(price.ask).toBe(1.09553);
            expect(price.spread).toBe(0.00002);
            expect(typeof price.timestamp).toBe('number');
        });

        test('should handle multiple symbols in price stream', () => {
            // Create buffer with 2 price packets
            const multiPriceBuffer = Buffer.alloc(PROTOCOL_CONSTANTS.HEADER_SIZE + 2 * PROTOCOL_CONSTANTS.PRICE_PACKET_SIZE);

            // Copy header and update data count
            validPriceStreamBuffer.copy(multiPriceBuffer, 0, 0, PROTOCOL_CONSTANTS.HEADER_SIZE);
            multiPriceBuffer.writeUInt8(2, 7); // 2 price packets

            // First symbol (EURUSD)
            let offset = PROTOCOL_CONSTANTS.HEADER_SIZE;
            multiPriceBuffer.writeUInt32LE(TRADING_SYMBOLS.EURUSD, offset);
            multiPriceBuffer.writeUInt32LE(109551, offset + 4);
            multiPriceBuffer.writeUInt32LE(109553, offset + 8);
            multiPriceBuffer.writeUInt32LE(0x00010001, offset + 12);

            // Second symbol (GBPUSD)
            offset += PROTOCOL_CONSTANTS.PRICE_PACKET_SIZE;
            multiPriceBuffer.writeUInt32LE(TRADING_SYMBOLS.GBPUSD, offset);
            multiPriceBuffer.writeUInt32LE(127082, offset + 4);
            multiPriceBuffer.writeUInt32LE(127085, offset + 8);
            multiPriceBuffer.writeUInt32LE(0x00020002, offset + 12);

            const result = protocol.parsePacket(multiPriceBuffer);

            expect(result.prices).toHaveLength(2);
            expect(result.prices[0].symbol).toBe('EURUSD');
            expect(result.prices[1].symbol).toBe('GBPUSD');
            expect(result.prices[1].bid).toBe(1.27082);
        });
    });

    describe('Account Profile Parsing', () => {
        test('should parse account profile packet correctly', () => {
            const result = protocol.parsePacket(validAccountProfileBuffer);

            expect(result.type).toBe('account_profile');
            expect(result.userId).toBe('user123');
            expect(result.broker).toBe('MetaQuotes');
            expect(result.accountNum).toBe(12345678);
            expect(result.balance).toBe(10000.00);
            expect(result.equity).toBe(10015.00);
            expect(result.margin).toBe(500.00);
            expect(result.freeMargin).toBe(9515.00);
            expect(result.leverage).toBe(100);
            expect(result.currency).toBe('USD');
            expect(typeof result.snapshotTime).toBe('number');
        });
    });

    describe('Trading Command Creation', () => {
        test('should create trading command packet correctly', () => {
            const commandData = {
                type: 'trading_command',
                commandId: 12345,
                symbol: 'EURUSD',
                action: 'BUY',
                volume: 0.1,
                price: 1.09551,
                stopLoss: 1.09500,
                takeProfit: 1.09600,
                magic: 20241226
            };

            const packet = protocol.createPacket(commandData);

            expect(packet).toBeInstanceOf(Buffer);
            expect(packet.length).toBeGreaterThan(PROTOCOL_CONSTANTS.HEADER_SIZE);

            // Verify header
            expect(packet.readUInt32LE(0)).toBe(PROTOCOL_CONSTANTS.BINARY_MAGIC);
            expect(packet.readUInt8(6)).toBe(MESSAGE_TYPES.TRADING_COMMAND);
        });
    });

    describe('Price Conversion Functions', () => {
        test('should convert price to fixed-point correctly', () => {
            expect(protocol.priceToFixedPoint(1.09551)).toBe(109551);
            expect(protocol.priceToFixedPoint(1.27082)).toBe(127082);
            expect(protocol.priceToFixedPoint(150.123)).toBe(15012300);
        });

        test('should convert fixed-point to price correctly', () => {
            expect(protocol.fixedPointToPrice(109551)).toBe(1.09551);
            expect(protocol.fixedPointToPrice(127082)).toBe(1.27082);
            expect(protocol.fixedPointToPrice(15012300)).toBe(150.123);
        });

        test('should handle price conversion roundtrip', () => {
            const testPrices = [1.09551, 1.27082, 150.123, 0.95432];

            testPrices.forEach(price => {
                const fixedPoint = protocol.priceToFixedPoint(price);
                const convertedBack = protocol.fixedPointToPrice(fixedPoint);
                expect(Math.abs(price - convertedBack)).toBeLessThan(0.000001);
            });
        });
    });

    describe('Symbol ID Functions', () => {
        test('should get correct symbol ID', () => {
            expect(protocol.getSymbolId('EURUSD')).toBe(TRADING_SYMBOLS.EURUSD);
            expect(protocol.getSymbolId('GBPUSD')).toBe(TRADING_SYMBOLS.GBPUSD);
            expect(protocol.getSymbolId('XAUUSD')).toBe(TRADING_SYMBOLS.XAUUSD);
            expect(protocol.getSymbolId('INVALID')).toBe(TRADING_SYMBOLS.UNKNOWN);
        });

        test('should get correct action ID', () => {
            expect(protocol.getActionId('BUY')).toBe(0);
            expect(protocol.getActionId('SELL')).toBe(1);
            expect(protocol.getActionId('CLOSE')).toBe(2);
            expect(protocol.getActionId('INVALID')).toBe(0);
        });
    });

    describe('Protocol Buffer Conversion', () => {
        test('should convert price stream to Protocol Buffer format', () => {
            const parsedData = protocol.parsePacket(validPriceStreamBuffer);
            const protoBuffer = protocol.toProtocolBuffer(parsedData);

            expect(protoBuffer.market_data).toBeDefined();
            expect(protoBuffer.market_data.symbols).toHaveLength(1);
            expect(protoBuffer.market_data.symbols[0].symbol).toBe('EURUSD');
            expect(protoBuffer.market_data.symbols[0].bid).toBe(1.09551);
            expect(protoBuffer.correlation_id).toContain('suho_');
        });

        test('should convert account profile to Protocol Buffer format', () => {
            const parsedData = protocol.parsePacket(validAccountProfileBuffer);
            const protoBuffer = protocol.toProtocolBuffer(parsedData);

            expect(protoBuffer.user_id).toBe('user123');
            expect(protoBuffer.company_id).toBe('MetaQuotes');
            expect(protoBuffer.account_data).toBeDefined();
            expect(protoBuffer.account_data.balance).toBe(10000.00);
            expect(protoBuffer.account_data.leverage).toBe(100);
        });

        test('should generate valid correlation IDs', () => {
            const correlationId = protocol.generateCorrelationId();

            expect(correlationId).toMatch(/^suho_\d+_[a-z0-9]+$/);
            expect(correlationId.length).toBeGreaterThan(10);
        });
    });

    describe('Market Session Detection', () => {
        test('should detect market session correctly', () => {
            const session = protocol.getMarketSession();

            expect(['asian_session', 'london_session', 'ny_session', 'overlap_session'])
                .toContain(session);
        });
    });

    describe('Error Handling', () => {
        test('should throw error for invalid packet type', () => {
            const invalidBuffer = Buffer.from(validPriceStreamBuffer);
            invalidBuffer.writeUInt8(99, 6); // Invalid message type

            expect(() => {
                protocol.parsePacket(invalidBuffer);
            }).toThrow('Unknown message type: 99');
        });

        test('should throw error for unsupported Protocol Buffer conversion', () => {
            const unsupportedData = { type: 'unsupported_type' };

            expect(() => {
                protocol.toProtocolBuffer(unsupportedData);
            }).toThrow('Cannot convert type unsupported_type to Protocol Buffer');
        });

        test('should throw error for unknown packet creation type', () => {
            const invalidData = { type: 'unknown_type' };

            expect(() => {
                protocol.createPacket(invalidData);
            }).toThrow('Cannot create packet for type: unknown_type');
        });
    });

    describe('Performance Tests', () => {
        test('should parse packets efficiently', () => {
            const startTime = Date.now();
            const iterations = 1000;

            for (let i = 0; i < iterations; i++) {
                protocol.parsePacket(validPriceStreamBuffer);
            }

            const endTime = Date.now();
            const totalTime = endTime - startTime;
            const avgTime = totalTime / iterations;

            // Should average less than 1ms per packet
            expect(avgTime).toBeLessThan(1);
        });

        test('should create packets efficiently', () => {
            const commandData = {
                type: 'trading_command',
                commandId: 12345,
                symbol: 'EURUSD',
                action: 'BUY',
                volume: 0.1,
                price: 1.09551,
                stopLoss: 1.09500,
                takeProfit: 1.09600,
                magic: 20241226
            };

            const startTime = Date.now();
            const iterations = 1000;

            for (let i = 0; i < iterations; i++) {
                protocol.createPacket(commandData);
            }

            const endTime = Date.now();
            const totalTime = endTime - startTime;
            const avgTime = totalTime / iterations;

            // Should average less than 0.5ms per packet creation
            expect(avgTime).toBeLessThan(0.5);
        });
    });
});