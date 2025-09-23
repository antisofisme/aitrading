/**
 * Backtesting-engine Server
 * AI Trading Platform - Backtesting Engine
 * Port: 8015
 */

require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const winston = require('winston');

const app = express();
const PORT = process.env.BACKTESTING_ENGINE_PORT || 8015;
const SERVICE_NAME = 'backtesting-engine';

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
    service: 'Backtesting Engine Service',
    description: 'Backtesting Engine for AI Trading Platform',
    port: PORT,
    version: '1.0.0'
  });
});

app.listen(PORT, () => {
  logger.info(`Backtesting Engine service running on port ${PORT}`);
});

module.exports = app;
