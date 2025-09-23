/**
 * Compliance-monitor Server
 * AI Trading Platform - Compliance Monitor
 * Port: 8014
 */

require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const winston = require('winston');

const app = express();
const PORT = process.env.COMPLIANCE_MONITOR_PORT || 8014;
const SERVICE_NAME = 'compliance-monitor';

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
    service: 'Compliance Monitor Service',
    description: 'Compliance Monitor for AI Trading Platform',
    port: PORT,
    version: '1.0.0'
  });
});

app.listen(PORT, () => {
  logger.info(`Compliance Monitor service running on port ${PORT}`);
});

module.exports = app;
