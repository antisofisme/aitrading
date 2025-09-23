/**
 * Central Hub Server
 * AI Trading Platform - Core Orchestration and Service Coordination
 * Port: 7000
 */

require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const winston = require('winston');

const app = express();
const PORT = process.env.CENTRAL_HUB_PORT || 7000;
const SERVICE_NAME = 'central-hub';

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
    service: 'Central Hub Service',
    description: 'Core orchestration and service coordination',
    port: PORT,
    capabilities: ['service-discovery', 'request-routing', 'orchestration']
  });
});

app.listen(PORT, () => {
  logger.info(`Central Hub service running on port ${PORT}`);
});

module.exports = app;
