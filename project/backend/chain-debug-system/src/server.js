/**
 * Chain-debug-system Server
 * AI Trading Platform - Chain Debug System
 * Port: 8030
 */

require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const winston = require('winston');

const app = express();
const PORT = process.env.CHAIN_DEBUG_SYSTEM_PORT || 8030;
const SERVICE_NAME = 'chain-debug-system';

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
    service: 'Chain Debug System Service',
    description: 'Chain Debug System for AI Trading Platform',
    port: PORT,
    version: '1.0.0'
  });
});

app.listen(PORT, () => {
  logger.info(`Chain Debug System service running on port ${PORT}`);
});

module.exports = app;
