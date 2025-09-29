# Component Manager Service

Standalone service untuk mengelola hot reload shared components dari Central Hub ke services lain via NATS.

## Architecture

```
Central Hub (/shared) → Component Manager → NATS → Services (API Gateway, dll)
     ↑ File Changes        ↑ Watch           ↑ Publish   ↑ Subscribe & Auto Reload
```

## Features

- **File System Watcher**: Detect perubahan di Central Hub shared components
- **NATS Publisher**: Broadcast component updates ke semua services
- **Version Control**: Hash-based change detection dengan versioning
- **Event-Driven**: Real-time component distribution
- **Hot Reload**: Components di-reload tanpa restart service

## Environment Variables

```bash
PORT=7001                                    # Service port
NATS_URL=nats://suho-nats-server:4222      # NATS server URL
SHARED_ROOT=/app/shared                     # Central Hub shared directory
WATCH_ENABLED=true                          # Enable file watching
DEBOUNCE_MS=500                            # File change debounce
LOG_LEVEL=info                             # Logging level
```

## API Endpoints

- `GET /health` - Service health check
- `GET /components` - List all components
- `GET /components/versions` - Get component versions
- `GET /components/{path}` - Get specific component

## NATS Topics

### Published Topics
- `suho.components.update.{component.path}` - Component update events
- `suho.components.delete.{component.path}` - Component deletion events

### Subscribed Topics
- `suho.components.request.{component.path}` - Component requests from services

## Docker

```bash
# Build
docker build -t suho-component-manager .

# Run
docker run -d \
  --name suho-component-manager \
  -p 7001:7001 \
  -e NATS_URL=nats://nats-server:4222 \
  -v /path/to/central-hub/shared:/app/shared:rw \
  suho-component-manager
```

## Development

```bash
npm install
npm run dev
```

## Integration

Services yang ingin menggunakan hot reload harus:

1. **Subscribe to NATS**: `suho.components.update.*`
2. **Implement ComponentSubscriber**: Untuk auto-reload
3. **Handle Events**: Component update/delete events
4. **Cache Management**: Local component caching dengan versioning