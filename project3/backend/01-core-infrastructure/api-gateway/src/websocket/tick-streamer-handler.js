/**
 * WebSocket Tick Streamer Handler
 *
 * Handles real-time tick streaming from MT5 EA via WebSocket
 * - Accepts both text (JSON) and binary frames
 * - Routes ticks to NATS → Data Bridge → ClickHouse
 * - Ultra-low latency (<20ms)
 * - Supports compact JSON format from OptimizedWebSocket
 */

const WebSocket = require('ws');
const logger = require('../utils/logger');

class TickStreamerHandler {
    constructor(options = {}) {
        this.options = {
            port: options.port || 8001,
            pingInterval: options.pingInterval || 30000, // 30s
            maxPayloadSize: options.maxPayloadSize || 1024 * 64, // 64KB
            ...options
        };

        this.wss = null;
        this.clients = new Map(); // clientId → { ws, broker, account, connectedAt, stats }
        this.stats = {
            totalConnections: 0,
            activeConnections: 0,
            ticksReceived: 0,
            ticksPublished: 0,
            errors: 0,
            bytesReceived: 0
        };

        this.natsClient = null; // Will be injected
        this.pingIntervalTimer = null;
    }

    /**
     * Initialize WebSocket server
     * @param {http.Server} httpServer - HTTP server to attach to
     */
    initialize(httpServer) {
        this.wss = new WebSocket.Server({
            server: httpServer,
            path: '/ws/ticks',
            maxPayload: this.options.maxPayloadSize,
            perMessageDeflate: false // Disable compression for low latency
        });

        this.wss.on('connection', (ws, req) => this.handleConnection(ws, req));
        this.wss.on('error', (error) => {
            logger.error('WebSocket server error', { error: error.message });
            this.stats.errors++;
        });

        // Start ping interval
        this.startPingInterval();

        logger.info('Tick Streamer WebSocket initialized', {
            path: '/ws/ticks',
            port: this.options.port,
            maxPayloadSize: this.options.maxPayloadSize
        });
    }

    /**
     * Set NATS client for publishing ticks
     */
    setNatsClient(natsClient) {
        this.natsClient = natsClient;
    }

    /**
     * Handle new WebSocket connection
     */
    handleConnection(ws, req) {
        const clientId = `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const clientIp = req.headers['x-forwarded-for'] || req.socket.remoteAddress;

        // Initialize client metadata
        const client = {
            ws,
            clientId,
            ip: clientIp,
            broker: null,
            account: null,
            connectedAt: Date.now(),
            stats: {
                ticksReceived: 0,
                ticksPublished: 0,
                errors: 0,
                lastTickTime: null
            }
        };

        this.clients.set(clientId, client);
        this.stats.totalConnections++;
        this.stats.activeConnections++;

        logger.info('WebSocket client connected', {
            clientId,
            ip: clientIp,
            activeConnections: this.stats.activeConnections
        });

        // Handle messages
        ws.on('message', (data, isBinary) => {
            this.handleMessage(clientId, data, isBinary);
        });

        // Handle close
        ws.on('close', (code, reason) => {
            this.handleDisconnect(clientId, code, reason);
        });

        // Handle errors
        ws.on('error', (error) => {
            logger.error('WebSocket client error', {
                clientId,
                error: error.message
            });
            client.stats.errors++;
            this.stats.errors++;
        });

        // Handle pong (response to ping)
        ws.on('pong', () => {
            client.lastPong = Date.now();
        });

        // Send welcome message
        this.sendMessage(ws, {
            type: 'connected',
            clientId,
            timestamp: Date.now(),
            message: 'Suho WebSocket Tick Streamer - Connected'
        });
    }

    /**
     * Handle incoming message (tick data)
     */
    async handleMessage(clientId, data, isBinary) {
        const client = this.clients.get(clientId);
        if (!client) return;

        try {
            this.stats.bytesReceived += data.length;
            client.stats.ticksReceived++;
            this.stats.ticksReceived++;

            let tickData;

            // Parse message (support both text JSON and binary)
            if (isBinary) {
                // Binary frame - parse as JSON (from OptimizedWebSocket binary frame)
                tickData = JSON.parse(data.toString('utf8'));
            } else {
                // Text frame - parse as JSON
                tickData = JSON.parse(data.toString('utf8'));
            }

            // Extract tick data (compact format with 1-char keys)
            const tick = {
                broker: tickData.b || tickData.broker,
                account: tickData.a || tickData.account,
                symbol: tickData.s || tickData.symbol,
                timestamp: tickData.t || tickData.timestamp_ms || Date.now(),
                bid: tickData.p || tickData.bid,
                ask: tickData.q || tickData.ask,
                last: tickData.l || tickData.last || 0,
                volume: tickData.v || tickData.volume || 0
            };

            // Update client metadata on first tick
            if (!client.broker && tick.broker) {
                client.broker = tick.broker;
                client.account = tick.account;
            }

            // Validate required fields
            if (!tick.symbol || !tick.bid || !tick.ask) {
                throw new Error('Invalid tick data: missing required fields (symbol, bid, ask)');
            }

            // Publish to NATS
            if (this.natsClient && this.natsClient.status?.nats?.connected) {
                const subject = `market.ticks.${tick.symbol}`;
                const payload = {
                    data: {
                        symbol: tick.symbol,
                        timestamp: tick.timestamp,
                        bid: tick.bid,
                        ask: tick.ask,
                        last: tick.last,
                        volume: tick.volume,
                        broker: tick.broker,
                        account: tick.account,
                        source: 'mt5_ws'
                    }
                };

                await this.natsClient.publishViaNATS(subject, payload);
                client.stats.ticksPublished++;
                this.stats.ticksPublished++;
            }

            client.stats.lastTickTime = Date.now();

        } catch (error) {
            logger.error('Error processing tick message', {
                clientId,
                error: error.message,
                dataLength: data.length
            });
            client.stats.errors++;
            this.stats.errors++;

            // Send error response to client
            this.sendMessage(client.ws, {
                type: 'error',
                message: error.message,
                timestamp: Date.now()
            });
        }
    }

    /**
     * Handle client disconnect
     */
    handleDisconnect(clientId, code, reason) {
        const client = this.clients.get(clientId);
        if (!client) return;

        const sessionDuration = Date.now() - client.connectedAt;

        logger.info('WebSocket client disconnected', {
            clientId,
            broker: client.broker,
            account: client.account,
            sessionDuration,
            ticksReceived: client.stats.ticksReceived,
            ticksPublished: client.stats.ticksPublished,
            code,
            reason: reason.toString()
        });

        this.clients.delete(clientId);
        this.stats.activeConnections--;
    }

    /**
     * Send message to client
     */
    sendMessage(ws, message) {
        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify(message));
        }
    }

    /**
     * Start ping interval to keep connections alive
     */
    startPingInterval() {
        this.pingIntervalTimer = setInterval(() => {
            this.clients.forEach((client, clientId) => {
                if (client.ws.readyState === WebSocket.OPEN) {
                    client.ws.ping();
                } else {
                    // Remove dead connection
                    this.clients.delete(clientId);
                    this.stats.activeConnections--;
                }
            });
        }, this.options.pingInterval);

        logger.info('Ping interval started', { interval: this.options.pingInterval });
    }

    /**
     * Get connection statistics
     */
    getStats() {
        return {
            ...this.stats,
            clients: Array.from(this.clients.values()).map(client => ({
                clientId: client.clientId,
                broker: client.broker,
                account: client.account,
                connectedAt: client.connectedAt,
                uptime: Date.now() - client.connectedAt,
                stats: client.stats
            }))
        };
    }

    /**
     * Shutdown WebSocket server
     */
    async shutdown() {
        logger.info('Shutting down Tick Streamer WebSocket...');

        // Clear ping interval
        if (this.pingIntervalTimer) {
            clearInterval(this.pingIntervalTimer);
        }

        // Close all client connections
        this.clients.forEach((client, clientId) => {
            if (client.ws.readyState === WebSocket.OPEN) {
                client.ws.close(1000, 'Server shutdown');
            }
        });

        // Close WebSocket server
        if (this.wss) {
            await new Promise((resolve) => {
                this.wss.close(resolve);
            });
        }

        logger.info('Tick Streamer WebSocket shutdown complete');
    }
}

module.exports = TickStreamerHandler;
