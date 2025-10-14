/**
 * Minimal WebSocket Server for Tick Passthrough Testing
 *
 * Simple standalone server untuk test WebSocket + Suho Binary Protocol
 * MT5 → WebSocket → NATS → Data Bridge
 */

const express = require('express');
const http = require('http');
const WebSocket = require('ws');

// Simple console logger for testing
const logger = {
    info: (msg, ...args) => console.log(`[INFO] ${msg}`, ...args),
    warn: (msg, ...args) => console.warn(`[WARN] ${msg}`, ...args),
    error: (msg, ...args) => console.error(`[ERROR] ${msg}`, ...args),
    debug: (msg, ...args) => console.log(`[DEBUG] ${msg}`, ...args)
};

// Mock NATS client untuk testing
class MockNatsClient {
    constructor() {
        this.status = {
            nats: { connected: true }
        };
    }

    async publishViaNATS(subject, payload) {
        console.log('📤 [MOCK-NATS] Published to:', subject);
        console.log('   Data size:', payload.data?.length || 0, 'bytes');
        console.log('   Metadata:', payload.metadata);
        return true;
    }
}

class WebSocketTestServer {
    constructor() {
        this.app = express();
        this.server = null;
        this.wss = null;
        this.mockNatsClient = new MockNatsClient();
        this.stats = {
            totalClients: 0,
            totalFramesReceived: 0,
            totalBytesReceived: 0,
            clients: new Map()
        };
    }

    initialize() {
        // Basic middleware
        this.app.use(express.json());

        // Health check
        this.app.get('/health', (req, res) => {
            res.json({
                status: 'healthy',
                websocket: this.wss ? 'initialized' : 'not_initialized',
                timestamp: new Date().toISOString()
            });
        });

        // Stats endpoint
        this.app.get('/stats', (req, res) => {
            res.json({
                totalClients: this.stats.totalClients,
                totalFramesReceived: this.stats.totalFramesReceived,
                totalBytesReceived: this.stats.totalBytesReceived,
                activeClients: this.stats.clients.size,
                clients: Array.from(this.stats.clients.values())
            });
        });

        // Welcome
        this.app.get('/', (req, res) => {
            res.json({
                name: 'WebSocket Tick Passthrough Test Server',
                version: '1.0.0',
                endpoint: 'ws://localhost:8001/ws/ticks',
                protocol: 'suho-binary-v1',
                status: 'ready'
            });
        });

        logger.info('Express app initialized');
    }

    async start() {
        try {
            this.initialize();

            // Create HTTP server
            this.server = http.createServer(this.app);

            // Start HTTP server (bind to 0.0.0.0 for Windows access)
            await new Promise((resolve, reject) => {
                this.server.listen(8003, '0.0.0.0', (error) => {
                    if (error) reject(error);
                    else resolve();
                });
            });

            // Initialize WebSocket Server
            this.wss = new WebSocket.Server({
                server: this.server,
                path: '/ws/ticks'
            });

            // Handle WebSocket connections
            this.wss.on('connection', (ws, req) => {
                const clientId = `client-${Date.now()}`;
                this.stats.totalClients++;
                this.stats.clients.set(clientId, {
                    id: clientId,
                    connectedAt: new Date().toISOString(),
                    framesReceived: 0
                });

                console.log(`🔌 [WS-TICK] Client connected: ${clientId}`);

                ws.on('message', (data, isBinary) => {
                    if (!isBinary) {
                        logger.warn('Received non-binary frame, ignoring');
                        return;
                    }

                    this.handleBinaryFrame(clientId, data);
                });

                ws.on('close', () => {
                    console.log(`📪 [WS-TICK] Client disconnected: ${clientId}`);
                    this.stats.clients.delete(clientId);
                });

                ws.on('error', (error) => {
                    logger.error(`WebSocket error for ${clientId}:`, error.message);
                });
            });

            // Get WSL IP for Windows access
            const { execSync } = require('child_process');
            let wslIp = '172.24.56.226'; // fallback
            try {
                wslIp = execSync("ip addr show eth0 | grep 'inet ' | awk '{print $2}' | cut -d/ -f1").toString().trim();
            } catch (e) {}

            console.log('');
            console.log('═'.repeat(70));
            console.log('🚀 WebSocket Tick Passthrough Server - STARTED');
            console.log('═'.repeat(70));
            console.log('📡 Listening on: 0.0.0.0:8003 (all interfaces)');
            console.log('');
            console.log('🔌 Access from:');
            console.log(`   WSL/Linux:  ws://localhost:8003/ws/ticks`);
            console.log(`   Windows MT5: ws://${wslIp}:8003/ws/ticks`);
            console.log('');
            console.log('📊 Stats: http://' + wslIp + ':8003/stats');
            console.log('💚 Health: http://' + wslIp + ':8003/health');
            console.log('');
            console.log('Protocol: Suho Binary Protocol v1');
            console.log('Mode: PASSTHROUGH (No parsing, direct to NATS)');
            console.log('NATS: MOCK (for testing)');
            console.log('═'.repeat(70));
            console.log('✅ Ready to receive binary frames from MT5!');
            console.log('');

        } catch (error) {
            console.error('❌ Failed to start server:', error);
            throw error;
        }
    }

    handleBinaryFrame(clientId, data) {
        try {
            // Validate minimum size (32 bytes)
            if (data.length < 32) {
                throw new Error(`Invalid binary frame size: ${data.length}`);
            }

            // Quick validation: Check magic number (0x53554854 = "SUHO")
            const magic = data.readUInt32LE(0);
            if (magic !== 0x53554854) {
                throw new Error(`Invalid magic number: 0x${magic.toString(16)}`);
            }

            // Update stats
            this.stats.totalFramesReceived++;
            this.stats.totalBytesReceived += data.length;
            const clientStats = this.stats.clients.get(clientId);
            if (clientStats) {
                clientStats.framesReceived++;
                clientStats.lastFrameAt = new Date().toISOString();
            }

            // Log every 100 frames
            if (this.stats.totalFramesReceived % 100 === 0) {
                console.log(`📥 [WS-TICK] Binary frame received: ${data.length} bytes`);
                console.log(`🔍 [WS-TICK] Magic: 0x${magic.toString(16)} ✅ (SUHO)`);
            }

            // Passthrough to NATS (mock)
            this.mockNatsClient.publishViaNATS('market.ticks.raw.binary', {
                data: data,
                metadata: {
                    source: 'mt5_websocket',
                    clientId: clientId,
                    timestamp: Date.now(),
                    size: data.length
                }
            });

        } catch (error) {
            logger.error(`Error handling binary frame from ${clientId}:`, error.message);
        }
    }

    async shutdown() {
        console.log('\n🔄 Shutting down server...');

        if (this.wss) {
            this.wss.close();
            console.log('✅ WebSocket server shutdown');
        }

        if (this.server) {
            await new Promise((resolve) => {
                this.server.close(resolve);
            });
            console.log('✅ HTTP server shutdown');
        }

        console.log('👋 Server stopped');
        process.exit(0);
    }
}

// Start server
const server = new WebSocketTestServer();

// Handle graceful shutdown
process.on('SIGTERM', () => {
    console.log('\n📨 Received SIGTERM');
    server.shutdown();
});

process.on('SIGINT', () => {
    console.log('\n📨 Received SIGINT (Ctrl+C)');
    server.shutdown();
});

// Start
server.start().catch((error) => {
    console.error('💥 Fatal error:', error);
    process.exit(1);
});

module.exports = WebSocketTestServer;
