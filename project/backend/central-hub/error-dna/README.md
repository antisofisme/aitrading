# ErrorDNA - Intelligent Error Management System

ErrorDNA is a comprehensive error management system designed for the AI Trading Platform's Phase 1 implementation. It provides intelligent error categorization, pattern detection, automated recovery, and seamless integration with the Central Hub and Import Manager.

## Features

### Core Capabilities
- **Error Categorization**: Automatic classification of errors into predefined categories (SYSTEM, API, TRADING, AI_ML, USER)
- **Pattern Detection**: Simple pattern recognition to identify recurring error patterns
- **Error Recovery**: Basic recovery mechanisms including retry, fallback, and circuit breaker patterns
- **Notification System**: Multi-channel notification support (webhook, email, Slack)
- **Storage & Logging**: Persistent error storage with retention policies and comprehensive logging
- **Integration**: Seamless integration with Central Hub and Import Manager

### Error Categories

| Category | Severity | Description | Subcategories |
|----------|----------|-------------|---------------|
| SYSTEM | HIGH | Infrastructure and system-level errors | DATABASE, NETWORK, MEMORY, CPU, DISK |
| API | MEDIUM | API-related errors and failures | AUTHENTICATION, VALIDATION, RATE_LIMIT, TIMEOUT, EXTERNAL |
| TRADING | CRITICAL | Trading-specific errors and market issues | ORDER, MARKET_DATA, RISK, SETTLEMENT, COMPLIANCE |
| AI_ML | HIGH | AI and machine learning related errors | MODEL, DATA, PREDICTION, PIPELINE, RESOURCE |
| USER | LOW | User-initiated errors and input issues | INPUT, PERMISSION, SESSION, PREFERENCE, WORKFLOW |

## Installation

```bash
# Install dependencies
npm install

# Development mode
npm run dev

# Production mode
npm start

# Run tests
npm test

# Run tests with coverage
npm run test:coverage
```

## Configuration

ErrorDNA uses a hierarchical configuration system with defaults in `/config/config.js`. Override values using environment variables:

### Environment Variables

```bash
# Service Configuration
NODE_ENV=production
ERROR_DNA_PORT=3005
LOG_LEVEL=info

# Storage Configuration
ERROR_STORAGE_DIR=/var/lib/error-dna
ERROR_RETENTION_DAYS=30

# Integration Configuration
CENTRAL_HUB_URL=http://localhost:3001
CENTRAL_HUB_API_KEY=your_api_key
IMPORT_MANAGER_URL=http://localhost:3003
IMPORT_MANAGER_API_KEY=your_api_key

# Notification Configuration
WEBHOOK_URL=http://localhost:3001/api/notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SMTP_HOST=smtp.example.com
SMTP_USER=notifications@example.com
SMTP_PASS=password
```

### Configuration Sections

#### Pattern Detection
```javascript
patternDetection: {
  enabled: true,
  windowSize: 100,           // Number of recent errors to analyze
  similarityThreshold: 0.8,  // Threshold for pattern matching
  minOccurrences: 3,         // Minimum occurrences to establish a pattern
  analysisInterval: 300000,  // Analysis interval in milliseconds
  maxPatterns: 1000          // Maximum patterns to store
}
```

#### Recovery Strategies
```javascript
recovery: {
  enabled: true,
  strategies: {
    retry: {
      enabled: true,
      maxAttempts: 3,
      backoffMultiplier: 2,
      initialDelay: 1000
    },
    fallback: {
      enabled: true,
      timeout: 30000
    },
    circuit_breaker: {
      enabled: true,
      threshold: 5,
      timeout: 60000,
      resetTimeout: 300000
    }
  }
}
```

## API Reference

### Error Processing

#### POST /api/errors
Process an error through the ErrorDNA pipeline.

**Request:**
```json
{
  "error": {
    "message": "Database connection failed",
    "stack": "Error: ECONNREFUSED...",
    "code": "ECONNREFUSED",
    "type": "DatabaseError"
  },
  "context": {
    "operation": "database_connect",
    "userId": "user123",
    "retryFunction": "function reference"
  }
}
```

**Response:**
```json
{
  "success": true,
  "errorId": "error_1234567890_abc123",
  "categorization": {
    "category": "SYSTEM",
    "subcategory": "DATABASE",
    "severity": "HIGH",
    "confidence": 0.92,
    "tags": ["database", "connection", "has-stack"]
  },
  "patterns": {
    "newPatterns": [],
    "existingPatterns": [{ "id": "pattern_123", "occurrences": 5 }],
    "anomalies": [],
    "recommendations": []
  },
  "recovery": {
    "strategy": "retry",
    "success": true,
    "attempts": 2
  },
  "processingTime": 245
}
```

#### GET /api/errors
Retrieve stored errors with optional filtering.

**Query Parameters:**
- `category`: Filter by error category
- `severity`: Filter by severity level
- `startTime`: Filter errors after this timestamp
- `endTime`: Filter errors before this timestamp
- `hasPatterns`: Filter errors with/without patterns

### Pattern Management

#### GET /api/patterns
Retrieve detected error patterns.

**Response:**
```json
{
  "success": true,
  "patterns": [
    {
      "id": "pattern_123",
      "signature": "SYSTEM::DATABASE::HIGH::connection-timeout",
      "category": "SYSTEM",
      "subcategory": "DATABASE",
      "severity": "HIGH",
      "occurrences": 15,
      "description": "Frequent high system errors in database",
      "riskLevel": "MEDIUM",
      "firstSeen": "2024-01-01T00:00:00Z",
      "lastSeen": "2024-01-02T12:00:00Z"
    }
  ]
}
```

### System Health

#### GET /health
Get comprehensive system health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-02T12:00:00Z",
  "uptime": 86400000,
  "metrics": {
    "errorsProcessed": 1234,
    "patternsDetected": 45,
    "recoveriesAttempted": 567,
    "notificationsSent": 89
  },
  "components": {
    "storage": { "status": "healthy" },
    "patternDetector": { "status": "healthy" },
    "recovery": { "status": "healthy" },
    "notifier": { "status": "healthy" }
  },
  "integrations": {
    "centralHub": { "status": "healthy", "latency": 120 },
    "importManager": { "status": "healthy", "latency": 95 }
  }
}
```

### Import Integration

#### POST /api/import-errors
Handle errors from the Import Manager.

**Request:**
```json
{
  "id": "import_error_123",
  "message": "CSV parsing failed on line 42",
  "code": "PARSE_ERROR",
  "source": "csv_importer",
  "file": "data.csv",
  "lineNumber": 42,
  "importId": "import_456",
  "timestamp": "2024-01-02T12:00:00Z"
}
```

## Usage Examples

### Basic Error Processing

```javascript
const ErrorDNA = require('@aitrading/error-dna');

// Initialize ErrorDNA
const errorDNA = new ErrorDNA();
await errorDNA.init();
await errorDNA.start();

// Process an error
try {
  // Your application code
  await riskyOperation();
} catch (error) {
  const result = await errorDNA.processError(error, {
    operation: 'risky_operation',
    userId: 'user123',
    retryFunction: async () => await riskyOperation(),
    fallbackValue: { status: 'degraded', data: null }
  });

  if (result.success && result.recovery?.success) {
    console.log('Error recovered successfully');
  } else {
    console.log('Error processing completed, check result for details');
  }
}
```

### Integration with Express.js

```javascript
const express = require('express');
const ErrorDNA = require('@aitrading/error-dna');

const app = express();
const errorDNA = new ErrorDNA();

// Initialize ErrorDNA
await errorDNA.init();

// Error handling middleware
app.use(async (error, req, res, next) => {
  // Process error through ErrorDNA
  const result = await errorDNA.processError(error, {
    operation: req.path,
    method: req.method,
    userId: req.user?.id,
    requestId: req.id
  });

  // Send appropriate response
  const statusCode = error.status || 500;
  res.status(statusCode).json({
    error: {
      message: error.message,
      errorId: result.errorId,
      category: result.categorization?.category,
      severity: result.categorization?.severity
    }
  });
});
```

### Custom Recovery Functions

```javascript
// Database operation with custom recovery
async function queryDatabase(sql, params) {
  try {
    return await db.query(sql, params);
  } catch (error) {
    const result = await errorDNA.processError(error, {
      operation: 'database_query',
      retryFunction: async () => {
        // Wait for connection pool to recover
        await new Promise(resolve => setTimeout(resolve, 1000));
        return await db.query(sql, params);
      },
      fallbackFunction: async () => {
        // Use read replica or cached data
        return await readReplica.query(sql, params);
      }
    });

    if (result.recovery?.success) {
      return result.recovery.result;
    }

    throw error; // Re-throw if recovery failed
  }
}
```

## Integration Architecture

### Central Hub Integration

ErrorDNA automatically registers with the Central Hub and provides:

1. **Service Registration**: Announces capabilities and endpoints
2. **Error Reporting**: Sends processed errors with categorization
3. **Health Status**: Regular health status updates
4. **Configuration**: Receives configuration updates

### Import Manager Integration

ErrorDNA provides specialized handling for import errors:

1. **Error Processing**: Transforms import errors to standard format
2. **Pattern Analysis**: Identifies import-specific patterns
3. **Recovery Suggestions**: Provides import-optimized recovery strategies
4. **Acknowledgments**: Confirms error receipt and processing

## Monitoring and Alerting

### Built-in Metrics

- **Error Processing Rate**: Errors processed per minute
- **Pattern Detection Rate**: New patterns discovered
- **Recovery Success Rate**: Percentage of successful recoveries
- **Integration Health**: Status of external system connections

### Notification Channels

1. **Webhook**: Real-time notifications to Central Hub
2. **Email**: High-priority error notifications
3. **Slack**: Pattern alerts and system status
4. **Log Files**: Comprehensive logging for audit trails

### Alert Thresholds

| Severity | Alert Threshold | Escalation Time |
|----------|----------------|-----------------|
| CRITICAL | 1 occurrence | 5 minutes |
| HIGH | 3 occurrences | 15 minutes |
| MEDIUM | 10 occurrences | 30 minutes |
| LOW | 50 occurrences | 60 minutes |

## Development

### Running Tests

```bash
# Run all tests
npm test

# Run specific test suite
npm test -- categorizer.test.js

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch
```

### Project Structure

```
error-dna/
├── src/
│   ├── categorizer.js          # Error categorization logic
│   ├── pattern-detector.js     # Pattern detection engine
│   ├── storage.js              # Error storage and retrieval
│   ├── logger.js               # Logging system
│   ├── notifier.js             # Notification management
│   ├── recovery.js             # Error recovery strategies
│   ├── integration.js          # External system integration
│   └── index.js                # Main ErrorDNA service
├── config/
│   ├── config.js               # Configuration management
│   └── error-categories.json   # Error category definitions
├── tests/
│   ├── categorizer.test.js     # Categorizer tests
│   ├── pattern-detector.test.js # Pattern detection tests
│   ├── integration.test.js     # Integration tests
│   ├── setup.js                # Test setup utilities
│   └── jest.config.js          # Jest configuration
├── storage/                    # Runtime storage directory
├── package.json
└── README.md
```

### Contributing

1. **Code Style**: Follow ESLint configuration
2. **Testing**: Maintain >70% test coverage
3. **Documentation**: Update README for new features
4. **Error Categories**: Update category definitions in config

### Performance Considerations

- **Memory Usage**: Pattern storage is limited to 1000 patterns
- **Processing Time**: Target <500ms per error processing
- **Storage**: Automatic cleanup of old data based on retention policy
- **Concurrency**: Designed for concurrent error processing

## Troubleshooting

### Common Issues

1. **Storage Permissions**: Ensure write access to storage directory
2. **Integration Timeouts**: Check network connectivity to Central Hub/Import Manager
3. **Memory Issues**: Monitor pattern storage and adjust limits
4. **Notification Failures**: Verify webhook URLs and authentication

### Debug Mode

```bash
# Enable debug logging
LOG_LEVEL=debug npm start

# Check health status
curl http://localhost:3005/health

# View recent errors
curl http://localhost:3005/api/errors?limit=10

# Check pattern detection
curl http://localhost:3005/api/patterns
```

### Log Files

- **error-dna.log**: Service events and operations
- **error.log**: Error-level events only
- **combined.log**: All log levels
- **exceptions.log**: Uncaught exceptions
- **rejections.log**: Unhandled promise rejections

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Create an issue in the project repository
- Check the troubleshooting section above
- Review log files for detailed error information