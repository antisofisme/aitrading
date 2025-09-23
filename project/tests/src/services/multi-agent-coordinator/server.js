const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
const morgan = require('morgan');
const { createServer } = require('http');
const { Server } = require('socket.io');

const agentRoutes = require('./routes/agentRoutes');
const coordinationRoutes = require('./routes/coordinationRoutes');
const consensusRoutes = require('./routes/consensusRoutes');
const { errorHandler, notFound } = require('./middleware/errorMiddleware');
const logger = require('./utils/logger');
const { connectDatabase, connectRedis } = require('./config/database');
const AgentCoordinator = require('./services/AgentCoordinator');

const app = express();
const server = createServer(app);
const io = new Server(server, {
  cors: {
    origin: process.env.CORS_ORIGINS ? process.env.CORS_ORIGINS.split(',') : ['http://localhost:3000'],
    methods: ['GET', 'POST']
  }
});

const PORT = process.env.PORT || 8030;

// Security middleware
app.use(helmet());
app.use(cors({
  origin: process.env.CORS_ORIGINS ? process.env.CORS_ORIGINS.split(',') : ['http://localhost:3000'],
  credentials: true
}));

// Compression and logging
app.use(compression());
app.use(morgan('combined', { stream: { write: message => logger.info(message.trim()) } }));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: process.env.NODE_ENV === 'production' ? 1000 : 5000, // High limit for agent coordination
  message: 'Too many coordination requests, please try again later.',
  standardHeaders: true,
  legacyHeaders: false,
});
app.use(limiter);

// Body parsing
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Initialize agent coordinator
const agentCoordinator = new AgentCoordinator(io);

// Make coordinator available to routes
app.locals.agentCoordinator = agentCoordinator;

// Health check
app.get('/health', (req, res) => {
  const coordinatorStatus = agentCoordinator.getStatus();

  res.json({
    status: 'healthy',
    service: 'multi-agent-coordinator',
    port: PORT,
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    version: '1.0.0',
    coordination: {
      activeAgents: coordinatorStatus.activeAgents,
      totalDecisions: coordinatorStatus.totalDecisions,
      averageDecisionTime: coordinatorStatus.averageDecisionTime,
      consensusAccuracy: coordinatorStatus.consensusAccuracy
    },
    capabilities: {
      multiAgentConsensus: true,
      realTimeCoordination: true,
      decisionAggregation: true,
      performanceTarget: 'Sub-100ms coordination'
    }
  });
});

// API routes
app.use('/api/v1/agents', agentRoutes);
app.use('/api/v1/coordination', coordinationRoutes);
app.use('/api/v1/consensus', consensusRoutes);

// Socket.IO connection handling
io.on('connection', (socket) => {
  logger.info(`Agent connected: ${socket.id}`);

  socket.on('register-agent', (agentData) => {
    agentCoordinator.registerAgent(socket.id, agentData);
    logger.info(`Agent registered: ${agentData.type} - ${socket.id}`);
  });

  socket.on('agent-decision', (decisionData) => {
    agentCoordinator.processAgentDecision(socket.id, decisionData);
  });

  socket.on('request-coordination', (requestData) => {
    agentCoordinator.handleCoordinationRequest(socket.id, requestData);
  });

  socket.on('disconnect', () => {
    agentCoordinator.unregisterAgent(socket.id);
    logger.info(`Agent disconnected: ${socket.id}`);
  });
});

// Error handling
app.use(notFound);
app.use(errorHandler);

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  agentCoordinator.shutdown();
  server.close(() => {
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully');
  agentCoordinator.shutdown();
  server.close(() => {
    process.exit(0);
  });
});

// Initialize connections and start server
async function startServer() {
  try {
    await connectDatabase();
    await connectRedis();
    await agentCoordinator.initialize();

    server.listen(PORT, () => {
      logger.info(`Multi-Agent Coordinator running on port ${PORT}`);
      logger.info(`Environment: ${process.env.NODE_ENV || 'development'}`);
      logger.info(`Process ID: ${process.pid}`);
      logger.info('Agent coordination hub ready for real-time decision making');
    });
  } catch (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
}

startServer();

module.exports = { app, server, io };