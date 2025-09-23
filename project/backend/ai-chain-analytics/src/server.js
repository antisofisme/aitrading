/**
 * Ai-chain-analytics Server
 * AI Trading Platform - Ai Chain Analytics
 * Port: 8031
 */

require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const winston = require('winston');

const app = express();
const PORT = process.env.AI_CHAIN_ANALYTICS_PORT || 8031;
const SERVICE_NAME = 'ai-chain-analytics';

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
    service: 'Ai Chain Analytics Service',
    description: 'Ai Chain Analytics for AI Trading Platform',
    port: PORT,
    version: '1.0.0'
  });
});

app.listen(PORT, () => {
  logger.info(`Ai Chain Analytics service running on port ${PORT}`);
});

module.exports = app;
