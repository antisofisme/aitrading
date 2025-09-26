/**
 * Test Suite for Corrected Data Flow
 *
 * Validates that the API Gateway follows the correct input/output contract structure:
 * - INPUTS: Data masuk ke API Gateway (dari mana saja)
 * - OUTPUTS: Data keluar dari API Gateway (ke mana saja)
 * - INTERNAL: Proses internal dalam API Gateway
 */

const BidirectionalRouter = require('../src/routing/bidirectional-router');
const ClientMT5Handler = require('../src/websocket/client-mt5-handler');
const { SuhoBinaryProtocol } = require('../src/protocols/suho-binary-protocol');

describe('Corrected Data Flow Tests', () => {
    let router;
    let mt5Handler;
    let binaryProtocol;

    beforeEach(() => {
        router = new BidirectionalRouter();
        mt5Handler = new ClientMT5Handler();
        binaryProtocol = new SuhoBinaryProtocol();
    });

    afterEach(() => {
        if (router) router.shutdown();
        if (mt5Handler) mt5Handler.shutdown();
    });

    describe('INPUT Flow: Client-MT5 → API Gateway', () => {
        test('should route price stream input to correct outputs', async () => {
            const routedOutputs = [];

            // Mock output destinations
            router.on('to-ml-processing', ({ message, metadata }) => {
                routedOutputs.push('to-ml-processing');
            });

            router.on('to-analytics-service', ({ message, metadata }) => {
                routedOutputs.push('to-analytics-service');
            });

            // Simulate price stream input from Client-MT5
            const priceStreamMessage = {
                type: 'price_stream',
                timestamp: Date.now() * 1000,
                prices: [
                    { symbol: 'EURUSD', bid: 1.09551, ask: 1.09553, spread: 0.00002 }
                ]
            };

            const metadata = {
                userId: 'user123',
                source: 'client-mt5',
                channel: 'price-stream'
            };

            // Route input
            await router.routeInput('client-mt5', priceStreamMessage, metadata);

            // Verify correct outputs were triggered
            expect(routedOutputs).toContain('to-ml-processing');
            expect(routedOutputs).toContain('to-analytics-service');
            expect(routedOutputs).toHaveLength(2);
        });

        test('should route trading command input to correct outputs', async () => {
            const routedOutputs = [];

            // Mock output destinations
            router.on('to-trading-engine', ({ message, metadata }) => {
                routedOutputs.push('to-trading-engine');
            });

            router.on('to-analytics-service', ({ message, metadata }) => {
                routedOutputs.push('to-analytics-service');
            });

            // Simulate trading command input from Client-MT5
            const tradingCommandMessage = {
                type: 'trading_command',
                commandId: 12345,
                symbol: 'EURUSD',
                action: 'BUY',
                volume: 0.1,
                price: 1.09551
            };

            const metadata = {
                userId: 'user123',
                source: 'client-mt5',
                channel: 'trading'
            };

            // Route input
            await router.routeInput('client-mt5', tradingCommandMessage, metadata);

            // Verify correct outputs were triggered
            expect(routedOutputs).toContain('to-trading-engine');
            expect(routedOutputs).toContain('to-analytics-service');
            expect(routedOutputs).toHaveLength(2);
        });

        test('should route account profile input to correct outputs', async () => {
            const routedOutputs = [];

            // Mock output destinations
            router.on('to-analytics-service', ({ message, metadata }) => {
                routedOutputs.push('to-analytics-service');
            });

            // Simulate account profile input from Client-MT5
            const accountProfileMessage = {
                type: 'account_profile',
                userId: 'user123',
                balance: 10000.00,
                equity: 10015.00,
                margin: 500.00
            };

            const metadata = {
                userId: 'user123',
                source: 'client-mt5',
                channel: 'trading'
            };

            // Route input
            await router.routeInput('client-mt5', accountProfileMessage, metadata);

            // Verify correct outputs were triggered
            expect(routedOutputs).toContain('to-analytics-service');
            expect(routedOutputs).toHaveLength(1);
        });
    });

    describe('INPUT Flow: Backend Services → API Gateway', () => {
        test('should route trading engine input to correct outputs', async () => {
            const routedOutputs = [];

            // Mock output destinations
            router.on('to-client-mt5-execution', ({ message, metadata }) => {
                routedOutputs.push('to-client-mt5-execution');
            });

            router.on('to-frontend-websocket', ({ message, metadata }) => {
                routedOutputs.push('to-frontend-websocket');
            });

            router.on('to-telegram-webhook', ({ message, metadata }) => {
                routedOutputs.push('to-telegram-webhook');
            });

            // Simulate trading engine input
            const tradingEngineMessage = {
                type: 'TradingOutput',
                user_id: 'user123',
                signals: [
                    { symbol: 'EURUSD', signal: 'BUY', confidence: 0.85 }
                ]
            };

            const metadata = {
                userId: 'user123',
                source: 'trading-engine',
                hasSignals: true
            };

            // Route input
            await router.routeInput('trading-engine', tradingEngineMessage, metadata);

            // Verify correct outputs were triggered
            expect(routedOutputs).toContain('to-client-mt5-execution');
            expect(routedOutputs).toContain('to-frontend-websocket');
            expect(routedOutputs).toContain('to-telegram-webhook'); // Because hasSignals = true
            expect(routedOutputs).toHaveLength(3);
        });

        test('should route analytics service input to correct outputs', async () => {
            const routedOutputs = [];

            // Mock output destinations
            router.on('to-frontend-websocket', ({ message, metadata }) => {
                routedOutputs.push('to-frontend-websocket');
            });

            router.on('to-notification-channels', ({ message, metadata }) => {
                routedOutputs.push('to-notification-channels');
            });

            // Simulate analytics service input with alert
            const analyticsMessage = {
                type: 'AnalyticsOutput',
                user_id: 'user123',
                performance: {
                    win_rate: 0.72,
                    profit_factor: 1.45
                }
            };

            const metadata = {
                userId: 'user123',
                source: 'analytics-service',
                alertLevel: 'warning' // Triggers notification
            };

            // Route input
            await router.routeInput('analytics-service', analyticsMessage, metadata);

            // Verify correct outputs were triggered
            expect(routedOutputs).toContain('to-frontend-websocket');
            expect(routedOutputs).toContain('to-notification-channels'); // Because alertLevel = warning
            expect(routedOutputs).toHaveLength(2);
        });

        test('should route ML processing input to correct outputs', async () => {
            const routedOutputs = [];

            // Mock output destinations
            router.on('to-trading-engine', ({ message, metadata }) => {
                routedOutputs.push('to-trading-engine');
            });

            router.on('to-frontend-websocket', ({ message, metadata }) => {
                routedOutputs.push('to-frontend-websocket');
            });

            // Simulate ML processing input
            const mlMessage = {
                type: 'MLOutput',
                user_id: 'user123',
                predictions: [
                    { symbol: 'EURUSD', confidence: 0.85, predicted_value: 1.0955 }
                ]
            };

            const metadata = {
                userId: 'user123',
                source: 'ml-processing'
            };

            // Route input
            await router.routeInput('ml-processing', mlMessage, metadata);

            // Verify correct outputs were triggered
            expect(routedOutputs).toContain('to-trading-engine');
            expect(routedOutputs).toContain('to-frontend-websocket');
            expect(routedOutputs).toHaveLength(2);
        });
    });

    describe('OUTPUT Flow: API Gateway → Destinations', () => {
        test('should emit correct events for each output destination', async () => {
            const emittedEvents = [];

            // Mock all possible output events
            const outputEvents = [
                'to-client-mt5-execution',
                'to-frontend-websocket',
                'to-telegram-webhook',
                'to-notification-channels',
                'to-trading-engine',
                'to-ml-processing',
                'to-analytics-service',
                'to-notification-hub'
            ];

            outputEvents.forEach(eventName => {
                router.on(eventName, ({ message, metadata }) => {
                    emittedEvents.push(eventName);
                });
            });

            // Test each output destination
            const testMessage = { type: 'test', data: 'test data' };
            const testMetadata = { userId: 'user123', timestamp: Date.now() };

            for (const outputDest of outputEvents) {
                await router.routeToOutput(outputDest, testMessage, testMetadata);
            }

            // Verify all output events were emitted
            expect(emittedEvents).toHaveLength(outputEvents.length);
            outputEvents.forEach(eventName => {
                expect(emittedEvents).toContain(eventName);
            });
        });
    });

    describe('Message Transformation', () => {
        test('should transform binary to protobuf for client-mt5 input', async () => {
            // Create binary price stream message
            const binaryMessage = {
                type: 'price_stream',
                prices: [
                    { symbol: 'EURUSD', bid: 1.09551, ask: 1.09553 }
                ]
            };

            // Transform using binary-to-protobuf
            const transformed = await router.transformMessage(binaryMessage, 'binary-to-protobuf', 'to_internal');

            // Should be converted to protobuf format
            expect(transformed).toBeDefined();
            expect(typeof transformed).toBe('object');
        });

        test('should transform protobuf to binary for client-mt5 output', async () => {
            const protobufMessage = {
                type: 'trading_command',
                symbol: 'EURUSD',
                action: 'BUY',
                volume: 0.1
            };

            // Transform using protobuf-to-binary
            const transformed = await router.transformMessage(protobufMessage, 'protobuf-to-binary', 'to_output');

            // Should be converted to binary format
            expect(transformed).toBeDefined();
        });

        test('should pass through protobuf messages for backend services', async () => {
            const protobufMessage = {
                type: 'TradingOutput',
                user_id: 'user123',
                signals: []
            };

            // Transform using protobuf-passthrough
            const transformed = await router.transformMessage(protobufMessage, 'protobuf-passthrough', 'to_internal');

            // Should be the same object (pass through)
            expect(transformed).toBe(protobufMessage);
        });
    });

    describe('Integration Flow Tests', () => {
        test('should handle complete Client-MT5 to Backend flow', async () => {
            const flowEvents = [];

            // Track the complete flow
            router.on('to-trading-engine', ({ message, metadata }) => {
                flowEvents.push('backend-call-trading-engine');
            });

            router.on('to-analytics-service', ({ message, metadata }) => {
                flowEvents.push('backend-call-analytics-service');
            });

            // Simulate Client-MT5 sending trading command
            const tradingCommand = {
                type: 'trading_command',
                commandId: 12345,
                symbol: 'EURUSD',
                action: 'BUY',
                volume: 0.1,
                price: 1.09551
            };

            const metadata = {
                userId: 'user123',
                source: 'client-mt5',
                channel: 'trading',
                timestamp: Date.now()
            };

            // Process as input from client-mt5
            await router.routeInput('client-mt5', tradingCommand, metadata);

            // Verify complete flow executed
            expect(flowEvents).toContain('backend-call-trading-engine');
            expect(flowEvents).toContain('backend-call-analytics-service');
        });

        test('should handle complete Backend to Client-MT5 flow', async () => {
            const flowEvents = [];

            // Track the complete flow
            router.on('to-client-mt5-execution', ({ message, metadata }) => {
                flowEvents.push('client-mt5-execution');
            });

            router.on('to-frontend-websocket', ({ message, metadata }) => {
                flowEvents.push('frontend-update');
            });

            // Simulate Trading Engine sending execution command
            const executionCommand = {
                type: 'TradingOutput',
                user_id: 'user123',
                signals: [
                    { symbol: 'EURUSD', signal: 'BUY', confidence: 0.85 }
                ]
            };

            const metadata = {
                userId: 'user123',
                source: 'trading-engine',
                hasSignals: false // No Telegram notification
            };

            // Process as input from trading-engine
            await router.routeInput('trading-engine', executionCommand, metadata);

            // Verify complete flow executed
            expect(flowEvents).toContain('client-mt5-execution');
            expect(flowEvents).toContain('frontend-update');
            expect(flowEvents).toHaveLength(2); // Should not include telegram
        });
    });

    describe('Error Handling', () => {
        test('should handle unknown input source gracefully', async () => {
            const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();

            const message = { type: 'test' };
            const metadata = { userId: 'user123' };

            await router.routeInput('unknown-source', message, metadata);

            expect(consoleSpy).toHaveBeenCalledWith(
                expect.stringContaining('No input route found for: unknown-source')
            );

            consoleSpy.mockRestore();
        });

        test('should handle unknown output destination gracefully', async () => {
            const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();

            const message = { type: 'test' };
            const metadata = { userId: 'user123' };

            await router.routeToOutput('unknown-output', message, metadata);

            expect(consoleSpy).toHaveBeenCalledWith(
                expect.stringContaining('No output route found for: unknown-output')
            );

            consoleSpy.mockRestore();
        });

        test('should handle invalid message types gracefully', async () => {
            const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();

            const invalidMessage = { type: 'invalid_type' };
            const metadata = { userId: 'user123' };

            await router.routeInput('client-mt5', invalidMessage, metadata);

            expect(consoleSpy).toHaveBeenCalledWith(
                expect.stringContaining('Invalid message type for client-mt5')
            );

            consoleSpy.mockRestore();
        });
    });

    describe('Performance Tests', () => {
        test('should route messages efficiently', async () => {
            const iterations = 1000;
            const startTime = Date.now();

            const message = {
                type: 'price_stream',
                prices: [{ symbol: 'EURUSD', bid: 1.09551, ask: 1.09553 }]
            };

            const metadata = { userId: 'user123', source: 'client-mt5' };

            // Route many messages
            for (let i = 0; i < iterations; i++) {
                await router.routeInput('client-mt5', message, metadata);
            }

            const endTime = Date.now();
            const totalTime = endTime - startTime;
            const avgTime = totalTime / iterations;

            // Should average less than 1ms per routing operation
            expect(avgTime).toBeLessThan(1);
        });
    });
});