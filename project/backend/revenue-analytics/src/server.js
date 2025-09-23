/**
 * Revenue-analytics Server
 * AI Trading Platform - Revenue Analytics
 * Port: 9102
 */

require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const winston = require('winston');

const app = express();
const PORT = process.env.REVENUE_ANALYTICS_PORT || 9102;
const SERVICE_NAME = 'revenue-analytics';

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
    service: 'Revenue Analytics Service',
    description: 'Revenue Analytics for AI Trading Platform',
    port: PORT,
    version: '1.0.0'
  });
});

app.listen(PORT, () => {
  logger.info(`Revenue Analytics service running on port ${PORT}`);
});

module.exports = app;
