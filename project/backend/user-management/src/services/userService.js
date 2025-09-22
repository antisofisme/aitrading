const { Pool } = require('pg');
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  defaultMeta: { service: 'user-management-userService' }
});

// Database connection
const pool = new Pool({
  host: process.env.POSTGRES_HOST || 'localhost',
  port: process.env.POSTGRES_PORT || 5432,
  database: process.env.POSTGRES_DB || 'aitrading',
  user: process.env.POSTGRES_USER || 'postgres',
  password: process.env.POSTGRES_PASSWORD || 'aitrading2024',
  max: 10,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

/**
 * Get user by email
 */
async function getUserByEmail(email) {
  try {
    const query = 'SELECT * FROM users WHERE email = $1';
    const result = await pool.query(query, [email]);
    return result.rows[0] || null;
  } catch (error) {
    logger.error('Error getting user by email:', error);
    throw error;
  }
}

/**
 * Get user by ID
 */
async function getUserById(id) {
  try {
    const query = 'SELECT * FROM users WHERE id = $1';
    const result = await pool.query(query, [id]);
    return result.rows[0] || null;
  } catch (error) {
    logger.error('Error getting user by ID:', error);
    throw error;
  }
}

/**
 * Create new user
 */
async function createUser(userData) {
  try {
    const query = `
      INSERT INTO users (
        id, email, password, first_name, last_name, phone_number,
        email_verified, is_active, subscription, accept_terms,
        created_at, updated_at
      ) VALUES (
        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
      ) RETURNING *
    `;

    const values = [
      userData.id,
      userData.email,
      userData.password,
      userData.firstName,
      userData.lastName,
      userData.phoneNumber,
      userData.emailVerified,
      userData.isActive,
      userData.subscription,
      userData.acceptTerms,
      userData.createdAt,
      userData.updatedAt
    ];

    const result = await pool.query(query, values);
    return mapUserFromDb(result.rows[0]);
  } catch (error) {
    logger.error('Error creating user:', error);
    throw error;
  }
}

/**
 * Update user last login
 */
async function updateUserLastLogin(userId) {
  try {
    const query = `
      UPDATE users
      SET last_login = $1, updated_at = $1
      WHERE id = $2
      RETURNING *
    `;

    const now = new Date();
    const result = await pool.query(query, [now, userId]);
    return mapUserFromDb(result.rows[0]);
  } catch (error) {
    logger.error('Error updating user last login:', error);
    throw error;
  }
}

/**
 * Update user email verification status
 */
async function updateUserEmailVerification(userId, verified = true) {
  try {
    const query = `
      UPDATE users
      SET email_verified = $1, updated_at = $2
      WHERE id = $3
      RETURNING *
    `;

    const now = new Date();
    const result = await pool.query(query, [verified, now, userId]);
    return mapUserFromDb(result.rows[0]);
  } catch (error) {
    logger.error('Error updating user email verification:', error);
    throw error;
  }
}

/**
 * Update user profile
 */
async function updateUserProfile(userId, profileData) {
  try {
    const fields = [];
    const values = [];
    let paramIndex = 1;

    // Build dynamic update query
    Object.keys(profileData).forEach(key => {
      if (profileData[key] !== undefined) {
        const dbField = camelToSnake(key);
        fields.push(`${dbField} = $${paramIndex}`);
        values.push(profileData[key]);
        paramIndex++;
      }
    });

    if (fields.length === 0) {
      throw new Error('No fields to update');
    }

    // Add updated_at
    fields.push(`updated_at = $${paramIndex}`);
    values.push(new Date());
    paramIndex++;

    // Add user ID
    values.push(userId);

    const query = `
      UPDATE users
      SET ${fields.join(', ')}
      WHERE id = $${paramIndex}
      RETURNING *
    `;

    const result = await pool.query(query, values);
    return mapUserFromDb(result.rows[0]);
  } catch (error) {
    logger.error('Error updating user profile:', error);
    throw error;
  }
}

/**
 * Update user subscription
 */
async function updateUserSubscription(userId, subscriptionTier) {
  try {
    const query = `
      UPDATE users
      SET subscription = $1, updated_at = $2
      WHERE id = $3
      RETURNING *
    `;

    const now = new Date();
    const result = await pool.query(query, [subscriptionTier, now, userId]);
    return mapUserFromDb(result.rows[0]);
  } catch (error) {
    logger.error('Error updating user subscription:', error);
    throw error;
  }
}

/**
 * Deactivate user account
 */
async function deactivateUser(userId) {
  try {
    const query = `
      UPDATE users
      SET is_active = false, updated_at = $1
      WHERE id = $2
      RETURNING *
    `;

    const now = new Date();
    const result = await pool.query(query, [now, userId]);
    return mapUserFromDb(result.rows[0]);
  } catch (error) {
    logger.error('Error deactivating user:', error);
    throw error;
  }
}

/**
 * Get users with filters
 */
async function getUsers(filters = {}, limit = 50, offset = 0) {
  try {
    let query = 'SELECT * FROM users WHERE 1=1';
    const values = [];
    let paramIndex = 1;

    // Apply filters
    if (filters.subscription) {
      query += ` AND subscription = $${paramIndex}`;
      values.push(filters.subscription);
      paramIndex++;
    }

    if (filters.isActive !== undefined) {
      query += ` AND is_active = $${paramIndex}`;
      values.push(filters.isActive);
      paramIndex++;
    }

    if (filters.emailVerified !== undefined) {
      query += ` AND email_verified = $${paramIndex}`;
      values.push(filters.emailVerified);
      paramIndex++;
    }

    if (filters.search) {
      query += ` AND (first_name ILIKE $${paramIndex} OR last_name ILIKE $${paramIndex} OR email ILIKE $${paramIndex})`;
      values.push(`%${filters.search}%`);
      paramIndex++;
    }

    // Add pagination
    query += ` ORDER BY created_at DESC LIMIT $${paramIndex} OFFSET $${paramIndex + 1}`;
    values.push(limit, offset);

    const result = await pool.query(query, values);
    return result.rows.map(mapUserFromDb);
  } catch (error) {
    logger.error('Error getting users:', error);
    throw error;
  }
}

/**
 * Get user count with filters
 */
async function getUserCount(filters = {}) {
  try {
    let query = 'SELECT COUNT(*) FROM users WHERE 1=1';
    const values = [];
    let paramIndex = 1;

    // Apply same filters as getUsers
    if (filters.subscription) {
      query += ` AND subscription = $${paramIndex}`;
      values.push(filters.subscription);
      paramIndex++;
    }

    if (filters.isActive !== undefined) {
      query += ` AND is_active = $${paramIndex}`;
      values.push(filters.isActive);
      paramIndex++;
    }

    if (filters.emailVerified !== undefined) {
      query += ` AND email_verified = $${paramIndex}`;
      values.push(filters.emailVerified);
      paramIndex++;
    }

    if (filters.search) {
      query += ` AND (first_name ILIKE $${paramIndex} OR last_name ILIKE $${paramIndex} OR email ILIKE $${paramIndex})`;
      values.push(`%${filters.search}%`);
      paramIndex++;
    }

    const result = await pool.query(query, values);
    return parseInt(result.rows[0].count);
  } catch (error) {
    logger.error('Error getting user count:', error);
    throw error;
  }
}

// Helper functions
function mapUserFromDb(dbUser) {
  if (!dbUser) return null;

  return {
    id: dbUser.id,
    email: dbUser.email,
    password: dbUser.password, // Only included for auth, remove in responses
    firstName: dbUser.first_name,
    lastName: dbUser.last_name,
    phoneNumber: dbUser.phone_number,
    emailVerified: dbUser.email_verified,
    isActive: dbUser.is_active,
    subscription: dbUser.subscription,
    acceptTerms: dbUser.accept_terms,
    createdAt: dbUser.created_at,
    updatedAt: dbUser.updated_at,
    lastLogin: dbUser.last_login
  };
}

function camelToSnake(str) {
  return str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
}

module.exports = {
  getUserByEmail,
  getUserById,
  createUser,
  updateUserLastLogin,
  updateUserEmailVerification,
  updateUserProfile,
  updateUserSubscription,
  deactivateUser,
  getUsers,
  getUserCount
};