/**
 * User-management Server
 * AI Trading Platform - User Management
 * Port: 8010
 */

require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const winston = require('winston');

const app = express();
const PORT = process.env.USER_MANAGEMENT_PORT || 8010;
const SERVICE_NAME = 'user-management';

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
    service: 'User Management Service',
    description: 'User Management for AI Trading Platform',
    port: PORT,
    version: '1.0.0'
  });
});

app.listen(PORT, () => {
  logger.info(`User Management service running on port ${PORT}`);
});

module.exports = app;
