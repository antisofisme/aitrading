// Simple WebSocket test to monitor tick data
const WebSocket = require('ws');

const ws = new WebSocket('ws://localhost:8000/api/v1/ws/mt5');

let tickCount = 0;
let lastTickTime = null;

ws.on('open', function open() {
    console.log('✅ Connected to WebSocket server');
    console.log('📊 Monitoring for tick data...\n');
});

ws.on('message', function message(data) {
    try {
        const msg = JSON.parse(data);
        
        // Count tick messages
        if (msg.type === 'tick_data') {
            tickCount++;
            lastTickTime = new Date();
            
            console.log(`📈 Tick #${tickCount} received:`);
            console.log(`   Symbol: ${msg.symbol}`);
            console.log(`   Bid: ${msg.bid}`);
            console.log(`   Ask: ${msg.ask}`);
            console.log(`   Spread: ${msg.spread}`);
            console.log(`   Time: ${msg.timestamp}`);
            console.log('');
        } else {
            console.log(`📨 Other message type: ${msg.type}`);
        }
    } catch (e) {
        console.error('Error parsing message:', e);
    }
});

ws.on('error', function error(err) {
    console.error('❌ WebSocket error:', err);
});

ws.on('close', function close() {
    console.log('🔌 Disconnected from server');
    console.log(`\n📊 Summary:`);
    console.log(`   Total ticks received: ${tickCount}`);
    if (lastTickTime) {
        console.log(`   Last tick at: ${lastTickTime}`);
    }
});

// Print summary every 10 seconds
setInterval(() => {
    if (tickCount === 0) {
        console.log(`⚠️  No tick data received yet (${new Date().toLocaleTimeString()})`);
    } else {
        const timeSinceLastTick = lastTickTime ? (new Date() - lastTickTime) / 1000 : null;
        console.log(`📊 Status: ${tickCount} ticks received, last tick ${timeSinceLastTick ? timeSinceLastTick.toFixed(1) + 's ago' : 'unknown'}`);
    }
}, 10000);

console.log('Press Ctrl+C to exit\n');