const express = require('express');
const http = require('http');
const WebSocket = require('ws');

const app = express();
const port = process.env.PORT || 8000;

// Middleware
app.use(express.json());

// Health endpoint
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        service: 'api-gateway',
        version: '1.0.0',
        timestamp: new Date().toISOString()
    });
});

// Root endpoint
app.get('/', (req, res) => {
    res.json({
        message: 'Suho Trading API Gateway',
        status: 'running',
        endpoints: {
            health: '/health',
            trading: 'ws://localhost:8001/ws/trading',
            priceStream: 'ws://localhost:8002/ws/price-stream'
        }
    });
});

// Client-MT5 endpoint
app.post('/api/client-mt5/input', (req, res) => {
    console.log('📥 Client-MT5 input received:', req.headers);
    res.json({
        success: true,
        message: 'Data received from Client-MT5',
        timestamp: new Date().toISOString()
    });
});

// Start HTTP server
const server = http.createServer(app);

// WebSocket servers
const tradingWss = new WebSocket.Server({ port: 8001 });
const priceWss = new WebSocket.Server({ port: 8002 });

tradingWss.on('connection', (ws) => {
    console.log('🔌 Trading WebSocket connected');
    ws.send(JSON.stringify({
        type: 'connection',
        message: 'Trading channel connected'
    }));
});

priceWss.on('connection', (ws) => {
    console.log('📈 Price stream WebSocket connected');
    ws.send(JSON.stringify({
        type: 'connection',
        message: 'Price stream connected'
    }));
});

server.listen(port, '0.0.0.0', () => {
    console.log(`🚀 API Gateway running on port ${port}`);
    console.log(`📊 Trading WebSocket on port 8001`);
    console.log(`📈 Price WebSocket on port 8002`);
});

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('🛑 Shutting down API Gateway...');
    server.close(() => {
        process.exit(0);
    });
});