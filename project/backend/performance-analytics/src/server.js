/**
 * Performance-analytics Server
 * AI Trading Platform - Performance Analytics
 * Port: 9100
 */

require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const winston = require('winston');

const app = express();
const PORT = process.env.PERFORMANCE_ANALYTICS_PORT || 9100;
const SERVICE_NAME = 'performance-analytics';

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.simple(),
  transports: [new winston.transports.Console()]
});

app.use(helmet());
app.use(cors());
app.use(express.json());

app.get('/health', (req, res) => {
  res.json({
    success: true,
    service: SERVICE_NAME,
    status: 'healthy',
    port: PORT,
    timestamp: new Date().toISOString()
  });
});

app.get('/', (req, res) => {
  res.json({
    service: 'Performance Analytics Service',
    description: 'Performance Analytics for AI Trading Platform',
    port: PORT,
    version: '1.0.0'
  });
});

app.listen(PORT, () => {
  logger.info(`Performance Analytics service running on port ${PORT}`);
});

module.exports = app;
