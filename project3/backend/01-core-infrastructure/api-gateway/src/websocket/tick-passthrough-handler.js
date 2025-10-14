/**
 * WebSocket Tick Passthrough Handler
 *
 * Simple passthrough for Suho Binary Protocol from MT5 → NATS
 * - NO PARSING (Data Bridge akan parse)
 * - NO CONVERSION (terima binary → forward binary)
 * - Ultra-low latency (<5ms)
 */

const WebSocket = require('ws');
const logger = require('../utils/logger');

class TickPassthroughHandler {
    constructor(options = {}) {
        this.options = {
            port: options.port || 8001,
            pingInterval: options.pingInterval || 30000, // 30s
            maxPayloadSize: options.maxPayloadSize || 1024 * 64, // 64KB
            ...options
        };

        this.wss = null;
        this.clients = new Map(); // clientId → { ws, connectedAt, stats }
        this.stats = {
            totalConnections: 0,
            activeConnections: 0,
            binaryFramesReceived: 0,
            bytesReceived: 0,
            natsPublished: 0,
            errors: 0
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

        logger.info('Tick Passthrough WebSocket initialized', {
            path: '/ws/ticks',
            port: this.options.port,
            mode: 'binary-passthrough'
        });
    }

    /**
     * Set NATS client for publishing binary frames
     */
    setNatsClient(natsClient) {
        this.natsClient = natsClient;
    }

    /**
     * Handle new WebSocket connection
     */
    handleConnection(ws, req) {
        const clientId = `mt5_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const clientIp = req.headers['x-forwarded-for'] || req.socket.remoteAddress;

        // Initialize client metadata
        const client = {
            ws,
            clientId,
            ip: clientIp,
            connectedAt: Date.now(),
            stats: {
                binaryFramesReceived: 0,
                bytesReceived: 0,
                natsPublished: 0,
                errors: 0
            }
        };

        this.clients.set(clientId, client);
        this.stats.totalConnections++;
        this.stats.activeConnections++;

        logger.info('MT5 WebSocket client connected', {
            clientId,
            ip: clientIp,
            activeConnections: this.stats.activeConnections
        });

        // Handle binary messages (Suho Binary Protocol)
        ws.on('message', (data, isBinary) => {
            this.handleBinaryFrame(clientId, data, isBinary);
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
            message: 'Suho WebSocket Tick Passthrough - Ready',
            protocol: 'suho-binary-v1'
        });
    }

    /**
     * Handle incoming binary frame (Suho Binary Protocol)
     * NO PARSING - Just passthrough to NATS
     */
    async handleBinaryFrame(clientId, data, isBinary) {
        const client = this.clients.get(clientId);
        if (!client) return;

        try {
            // Only accept binary frames
            if (!isBinary) {
                logger.warn('Received non-binary frame, ignoring', { clientId });
                return;
            }

            // Update stats
            this.stats.bytesReceived += data.length;
            this.stats.binaryFramesReceived++;
            client.stats.bytesReceived += data.length;
            client.stats.binaryFramesReceived++;

            // Validate minimum size (32 bytes for single tick)
            if (data.length < 32) {
                throw new Error(`Invalid binary frame size: ${data.length} bytes (expected >= 32)`);
            }

            // Quick validation: Check magic number (0x53554854 = "SUHO")
            const magic = data.readUInt32LE(0);
            if (magic !== 0x53554854) {
                throw new Error(`Invalid magic number: 0x${magic.toString(16)} (expected 0x53554854)`);
            }

            // Passthrough to NATS (no parsing!)
            if (this.natsClient && this.natsClient.status?.nats?.connected) {
                // Publish binary data directly to NATS
                const subject = 'market.ticks.raw.binary';

                await this.natsClient.publishViaNATS(subject, {
                    data: data, // Send binary buffer as-is
                    metadata: {
                        source: 'mt5_websocket',
                        clientId: clientId,
                        timestamp: Date.now(),
                        size: data.length
                    }
                });

                client.stats.natsPublished++;
                this.stats.natsPublished++;
            }

        } catch (error) {
            logger.error('Error processing binary frame', {
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

        logger.info('MT5 WebSocket client disconnected', {
            clientId,
            sessionDuration,
            binaryFramesReceived: client.stats.binaryFramesReceived,
            natsPublished: client.stats.natsPublished,
            code,
            reason: reason.toString()
        });

        this.clients.delete(clientId);
        this.stats.activeConnections--;
    }

    /**
     * Send JSON message to client
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
        logger.info('Shutting down Tick Passthrough WebSocket...');

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

        logger.info('Tick Passthrough WebSocket shutdown complete');
    }
}

module.exports = TickPassthroughHandler;
