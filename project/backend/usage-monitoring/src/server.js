/**
 * Usage-monitoring Server
 * AI Trading Platform - Usage Monitoring
 * Port: 9101
 */

require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const winston = require('winston');

const app = express();
const PORT = process.env.USAGE_MONITORING_PORT || 9101;
const SERVICE_NAME = 'usage-monitoring';

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
    service: 'Usage Monitoring Service',
    description: 'Usage Monitoring for AI Trading Platform',
    port: PORT,
    version: '1.0.0'
  });
});

app.listen(PORT, () => {
  logger.info(`Usage Monitoring service running on port ${PORT}`);
});

module.exports = app;
