/**
 * Data Bridge Server
 * AI Trading Platform - Real-time Market Data Ingestion and Distribution
 * Port: 5001
 */

require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const winston = require('winston');

const app = express();
const PORT = process.env.DATA_BRIDGE_PORT || 5001;
const SERVICE_NAME = 'data-bridge';

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
    service: 'Data Bridge Service',
    description: 'Real-time market data ingestion',
    port: PORT,
    capabilities: ['real-time-streaming', 'data-normalization']
  });
});

app.listen(PORT, () => {
  logger.info(`Data Bridge service running on port ${PORT}`);
});

module.exports = app;
