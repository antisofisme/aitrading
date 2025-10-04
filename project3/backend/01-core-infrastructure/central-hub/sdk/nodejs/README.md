# Central Hub SDK - Node.js

Official Node.js/TypeScript client library for integrating services with Suho Central Hub.

## 🚀 Installation

### From Local Source (Development)

```bash
cd /path/to/central-hub/sdk/nodejs
npm install
npm link
```

Then in your service:

```bash
npm link @suho/central-hub-sdk
```

### From Package (Production)

```bash
npm install @suho/central-hub-sdk
```

## 📖 Quick Start

```javascript
const { CentralHubClient } = require('@suho/central-hub-sdk');

async function main() {
    // Initialize client
    const client = new CentralHubClient({
        serviceName: 'api-gateway',
        baseURL: 'http://suho-central-hub:7000',
        retryAttempts: 5,
        retryDelay: 2000
    });

    // Register service
    const serviceInfo = {
        name: 'api-gateway',
        host: 'api-gateway',
        port: 3000,
        version: '1.0.0',
        capabilities: ['http', 'websocket'],
        metadata: {
            protocol: 'suho-binary'
        }
    };

    await client.register(serviceInfo);

    // Heartbeat starts automatically

    // Listen to events
    client.on('registered', (data) => {
        console.log('✅ Registered:', data.service_id);
    });

    client.on('connection_lost', () => {
        console.error('❌ Lost connection to Central Hub');
    });

    // Your service logic...
    await new Promise(resolve => setTimeout(resolve, 3600000));

    // Cleanup on shutdown
    await client.unregister();
}

main().catch(console.error);
```

## 🔧 Configuration

### Client Options

```javascript
const client = new CentralHubClient({
    serviceName: 'my-service',      // Required: Service name
    baseURL: 'http://...',           // Optional: Central Hub URL
    retryAttempts: 5,                // Optional: Max retry attempts
    retryDelay: 2000,                // Optional: Initial retry delay (ms)
    timeout: 10000                   // Optional: Request timeout (ms)
});
```

### Environment Variables

```bash
CENTRAL_HUB_URL=http://suho-central-hub:7000  # Central Hub base URL
```

## 📋 API Reference

### Registration

```javascript
// Register service
const result = await client.register({
    name: 'my-service',
    host: 'my-service',
    port: 3000,
    version: '1.0.0',
    capabilities: ['http'],
    metadata: {}
});

// Unregister service
await client.unregister();
```

### Service Discovery

```javascript
// Discover specific service
const service = await client.discoverService('trading-engine');

// Get all registered services
const services = await client.getAllServices();
```

### Configuration Management

```javascript
// Get service configuration
const config = await client.getConfiguration('my-service');

// Validate configuration
const isValid = await client.validateConfiguration(config);
```

### Health & Monitoring

```javascript
// Report health status
await client.reportHealth({
    cpu_usage: process.cpuUsage(),
    memory_usage: process.memoryUsage(),
    uptime: process.uptime()
});

// Check Central Hub health
const health = await client.checkHealth();
```

### Events

```javascript
client.on('registered', (data) => {
    console.log('Service registered:', data);
});

client.on('unregistered', () => {
    console.log('Service unregistered');
});

client.on('connection_lost', () => {
    console.error('Connection lost to Central Hub');
});

client.on('config_loaded', (config) => {
    console.log('Configuration loaded:', config);
});
```

## 🏗️ Architecture

```
Your Service (Node.js)
    ↓
CentralHubClient (SDK)
    ↓ HTTP/REST
Central Hub Service
    ↓
Service Registry
```

## 🔍 Error Handling

```javascript
try {
    await client.register(serviceInfo);
} catch (error) {
    console.error('Registration failed:', error.message);
    // Service continues without Central Hub (optional)
}
```

## 📊 Metrics & Monitoring

Automatic features:

- ✅ Heartbeat every 30 seconds
- ✅ Automatic retry with exponential backoff
- ✅ Connection status monitoring
- ✅ Event-driven architecture

## 🛡️ Best Practices

1. **Always unregister on shutdown**:
   ```javascript
   process.on('SIGTERM', async () => {
       await client.unregister();
       process.exit(0);
   });
   ```

2. **Handle events for monitoring**:
   ```javascript
   client.on('connection_lost', () => {
       metrics.increment('central_hub.connection_lost');
   });
   ```

3. **Use with Express.js**:
   ```javascript
   const app = express();

   app.on('listening', async () => {
       await client.register({
           name: 'my-api',
           port: 3000
       });
   });
   ```

## 🐛 Debugging

Enable debug logging:

```javascript
const client = new CentralHubClient({
    serviceName: 'my-service',
    debug: true  // Enable verbose logging
});
```

## 📝 Changelog

### v1.0.0 (2025-10-04)
- Initial release
- Service registration & discovery
- Automatic heartbeat
- Health reporting
- Event-driven architecture
- Automatic retry with exponential backoff

## 📄 License

MIT License - Copyright (c) 2025 Suho Trading System

## 🤝 Support

For issues and questions:
- GitHub Issues: https://github.com/suho-trading/central-hub-sdk/issues
- Documentation: https://docs.suho-trading.com/central-hub-sdk
