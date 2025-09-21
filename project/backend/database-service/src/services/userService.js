const bcrypt = require('bcrypt');
const Joi = require('joi');
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

class UserService {
  constructor(db) {
    this.db = db;
    this.saltRounds = 12;

    // Validation schemas
    this.createUserSchema = Joi.object({
      email: Joi.string().email().required(),
      password: Joi.string().min(8).required(),
      first_name: Joi.string().min(2).max(50).required(),
      last_name: Joi.string().min(2).max(50).required(),
      role: Joi.string().valid('user', 'admin', 'trader').default('user')
    });

    this.authSchema = Joi.object({
      email: Joi.string().email().required(),
      password: Joi.string().required()
    });
  }

  async createUser(userData) {
    try {
      // Validate input
      const { error, value } = this.createUserSchema.validate(userData);
      if (error) {
        throw new Error(`Validation error: ${error.details[0].message}`);
      }

      const { email, password, first_name, last_name, role } = value;

      // Check if user already exists
      const existingUser = await this.getUserByEmail(email);
      if (existingUser) {
        throw new Error('User with this email already exists');
      }

      // Hash password
      const hashedPassword = await bcrypt.hash(password, this.saltRounds);

      // Create user
      const query = `
        INSERT INTO users (email, password_hash, first_name, last_name, role, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
        RETURNING id, email, first_name, last_name, role, created_at, is_active
      `;

      const result = await this.db.query(query, [
        email,
        hashedPassword,
        first_name,
        last_name,
        role
      ]);

      logger.info(`User created successfully: ${email}`);
      return result.rows[0];
    } catch (error) {
      logger.error('Create user error:', error);
      throw error;
    }
  }

  async getUserById(userId) {
    try {
      const query = `
        SELECT id, email, first_name, last_name, role, created_at, updated_at, is_active, last_login
        FROM users
        WHERE id = $1 AND is_active = true
      `;

      const result = await this.db.query(query, [userId]);
      return result.rows[0] || null;
    } catch (error) {
      logger.error('Get user by ID error:', error);
      throw error;
    }
  }

  async getUserByEmail(email) {
    try {
      const query = `
        SELECT id, email, first_name, last_name, role, created_at, updated_at, is_active, last_login
        FROM users
        WHERE email = $1 AND is_active = true
      `;

      const result = await this.db.query(query, [email]);
      return result.rows[0] || null;
    } catch (error) {
      logger.error('Get user by email error:', error);
      throw error;
    }
  }

  async authenticateUser(email, password) {
    try {
      // Validate input
      const { error } = this.authSchema.validate({ email, password });
      if (error) {
        throw new Error(`Validation error: ${error.details[0].message}`);
      }

      // Get user with password hash
      const query = `
        SELECT id, email, password_hash, first_name, last_name, role, is_active
        FROM users
        WHERE email = $1 AND is_active = true
      `;

      const result = await this.db.query(query, [email]);
      const user = result.rows[0];

      if (!user) {
        throw new Error('Invalid email or password');
      }

      // Verify password
      const isValidPassword = await bcrypt.compare(password, user.password_hash);
      if (!isValidPassword) {
        throw new Error('Invalid email or password');
      }

      // Update last login
      await this.updateLastLogin(user.id);

      // Return user without password hash
      const { password_hash, ...userWithoutPassword } = user;

      logger.info(`User authenticated successfully: ${email}`);
      return userWithoutPassword;
    } catch (error) {
      logger.error('Authentication error:', error);
      throw error;
    }
  }

  async updateLastLogin(userId) {
    try {
      const query = `
        UPDATE users
        SET last_login = NOW(), updated_at = NOW()
        WHERE id = $1
      `;

      await this.db.query(query, [userId]);
    } catch (error) {
      logger.error('Update last login error:', error);
      // Don't throw error for this non-critical operation
    }
  }

  async updateUser(userId, updateData) {
    try {
      const allowedFields = ['first_name', 'last_name', 'role'];
      const updates = [];
      const values = [];
      let paramCount = 1;

      for (const [key, value] of Object.entries(updateData)) {
        if (allowedFields.includes(key) && value !== undefined) {
          updates.push(`${key} = $${paramCount}`);
          values.push(value);
          paramCount++;
        }
      }

      if (updates.length === 0) {
        throw new Error('No valid fields to update');
      }

      updates.push(`updated_at = NOW()`);
      values.push(userId);

      const query = `
        UPDATE users
        SET ${updates.join(', ')}
        WHERE id = $${paramCount} AND is_active = true
        RETURNING id, email, first_name, last_name, role, updated_at
      `;

      const result = await this.db.query(query, values);

      if (result.rows.length === 0) {
        throw new Error('User not found or inactive');
      }

      logger.info(`User updated successfully: ${userId}`);
      return result.rows[0];
    } catch (error) {
      logger.error('Update user error:', error);
      throw error;
    }
  }

  async deactivateUser(userId) {
    try {
      const query = `
        UPDATE users
        SET is_active = false, updated_at = NOW()
        WHERE id = $1
        RETURNING id, email, is_active
      `;

      const result = await this.db.query(query, [userId]);

      if (result.rows.length === 0) {
        throw new Error('User not found');
      }

      logger.info(`User deactivated successfully: ${userId}`);
      return result.rows[0];
    } catch (error) {
      logger.error('Deactivate user error:', error);
      throw error;
    }
  }

  async getAllUsers(limit = 50, offset = 0) {
    try {
      const query = `
        SELECT id, email, first_name, last_name, role, created_at, last_login, is_active
        FROM users
        WHERE is_active = true
        ORDER BY created_at DESC
        LIMIT $1 OFFSET $2
      `;

      const result = await this.db.query(query, [limit, offset]);
      return result.rows;
    } catch (error) {
      logger.error('Get all users error:', error);
      throw error;
    }
  }
}

module.exports = UserService;