const express = require('express');
const User = require('../models/User');
const QueryService = require('../services/QueryService');
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console()
  ]
});

function createApiRoutes(db) {
  const router = express.Router();
  const userModel = new User(db);
  const queryService = new QueryService(db);

  // Middleware for logging requests
  router.use((req, res, next) => {
    logger.info('API Request', {
      method: req.method,
      path: req.path,
      ip: req.ip,
      userAgent: req.get('User-Agent')
    });
    next();
  });

  // User Management Routes
  router.post('/users', async (req, res) => {
    try {
      const { email, password, username, role } = req.body;

      if (!email || !password || !username) {
        return res.status(400).json({
          error: 'Missing required fields: email, password, username'
        });
      }

      const user = await userModel.create({ email, password, username, role });
      res.status(201).json({
        success: true,
        user: {
          id: user.id,
          email: user.email,
          username: user.username,
          role: user.role,
          created_at: user.created_at
        }
      });

    } catch (error) {
      logger.error('User creation failed:', error);
      res.status(500).json({
        error: error.message.includes('duplicate') ?
          'User already exists' : 'Failed to create user'
      });
    }
  });

  router.get('/users/:id', async (req, res) => {
    try {
      const user = await userModel.findById(req.params.id);

      if (!user) {
        return res.status(404).json({ error: 'User not found' });
      }

      res.json({
        success: true,
        user
      });

    } catch (error) {
      logger.error('User fetch failed:', error);
      res.status(500).json({ error: 'Failed to fetch user' });
    }
  });

  router.get('/users', async (req, res) => {
    try {
      const {
        limit = 50,
        offset = 0,
        role
      } = req.query;

      const users = await userModel.list({
        limit: parseInt(limit),
        offset: parseInt(offset),
        role
      });

      const total = await userModel.count({ role });

      res.json({
        success: true,
        users,
        pagination: {
          total,
          limit: parseInt(limit),
          offset: parseInt(offset),
          hasMore: (parseInt(offset) + parseInt(limit)) < total
        }
      });

    } catch (error) {
      logger.error('User list failed:', error);
      res.status(500).json({ error: 'Failed to fetch users' });
    }
  });

  router.put('/users/:id', async (req, res) => {
    try {
      const updates = req.body;
      const user = await userModel.updateProfile(req.params.id, updates);

      if (!user) {
        return res.status(404).json({ error: 'User not found' });
      }

      res.json({
        success: true,
        user
      });

    } catch (error) {
      logger.error('User update failed:', error);
      res.status(500).json({ error: 'Failed to update user' });
    }
  });

  router.delete('/users/:id', async (req, res) => {
    try {
      const user = await userModel.deactivate(req.params.id);

      if (!user) {
        return res.status(404).json({ error: 'User not found' });
      }

      res.json({
        success: true,
        message: 'User deactivated successfully'
      });

    } catch (error) {
      logger.error('User deactivation failed:', error);
      res.status(500).json({ error: 'Failed to deactivate user' });
    }
  });

  // Authentication Routes
  router.post('/auth/login', async (req, res) => {
    try {
      const { email, password } = req.body;

      if (!email || !password) {
        return res.status(400).json({
          error: 'Email and password are required'
        });
      }

      const user = await userModel.findByEmail(email);

      if (!user) {
        return res.status(401).json({ error: 'Invalid credentials' });
      }

      const isValid = await userModel.validatePassword(password, user.password_hash);

      if (!isValid) {
        return res.status(401).json({ error: 'Invalid credentials' });
      }

      await userModel.updateLastLogin(user.id);

      res.json({
        success: true,
        user: {
          id: user.id,
          email: user.email,
          username: user.username,
          role: user.role
        },
        message: 'Login successful'
      });

    } catch (error) {
      logger.error('Login failed:', error);
      res.status(500).json({ error: 'Login failed' });
    }
  });

  // Query Execution Routes
  router.post('/query', async (req, res) => {
    try {
      const { query, params = [] } = req.body;

      if (!query) {
        return res.status(400).json({ error: 'Query is required' });
      }

      // Validate query for safety
      const validation = await queryService.validateQuery(query);
      if (!validation.valid) {
        return res.status(400).json({ error: validation.error });
      }

      const result = await queryService.executeQuery(query, params);
      res.json(result);

    } catch (error) {
      logger.error('Query execution failed:', error);
      res.status(500).json({ error: 'Query execution failed' });
    }
  });

  router.post('/transaction', async (req, res) => {
    try {
      const { queries } = req.body;

      if (!queries || !Array.isArray(queries)) {
        return res.status(400).json({ error: 'Queries array is required' });
      }

      // Validate all queries
      for (const { query } of queries) {
        const validation = await queryService.validateQuery(query);
        if (!validation.valid) {
          return res.status(400).json({ error: validation.error });
        }
      }

      const result = await queryService.executeTransaction(queries);
      res.json(result);

    } catch (error) {
      logger.error('Transaction execution failed:', error);
      res.status(500).json({ error: 'Transaction execution failed' });
    }
  });

  // Database Information Routes
  router.get('/tables', async (req, res) => {
    try {
      const result = await queryService.listTables();
      res.json(result);
    } catch (error) {
      logger.error('Table listing failed:', error);
      res.status(500).json({ error: 'Failed to list tables' });
    }
  });

  router.get('/tables/:tableName', async (req, res) => {
    try {
      const result = await queryService.getTableInfo(req.params.tableName);
      res.json(result);
    } catch (error) {
      logger.error('Table info failed:', error);
      res.status(500).json({ error: 'Failed to get table info' });
    }
  });

  router.post('/explain', async (req, res) => {
    try {
      const { query, params = [] } = req.body;

      if (!query) {
        return res.status(400).json({ error: 'Query is required' });
      }

      const result = await queryService.getQueryPlan(query, params);
      res.json(result);

    } catch (error) {
      logger.error('Query explanation failed:', error);
      res.status(500).json({ error: 'Query explanation failed' });
    }
  });

  return router;
}

module.exports = createApiRoutes;