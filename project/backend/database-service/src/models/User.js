const bcrypt = require('bcrypt');
const { v4: uuidv4 } = require('uuid');

class User {
  constructor(db) {
    this.db = db;
  }

  async create({ email, password, username, role = 'user' }) {
    const id = uuidv4();
    const hashedPassword = await bcrypt.hash(password, 10);
    const createdAt = new Date();

    const query = `
      INSERT INTO users (id, email, username, password_hash, role, created_at, updated_at)
      VALUES ($1, $2, $3, $4, $5, $6, $6)
      RETURNING id, email, username, role, created_at, updated_at
    `;

    const values = [id, email, username, hashedPassword, role, createdAt];
    const result = await this.db.query(query, values);
    return result.rows[0];
  }

  async findByEmail(email) {
    const query = `
      SELECT id, email, username, password_hash, role, created_at, updated_at, last_login
      FROM users
      WHERE email = $1 AND active = true
    `;

    const result = await this.db.query(query, [email]);
    return result.rows[0] || null;
  }

  async findById(id) {
    const query = `
      SELECT id, email, username, role, created_at, updated_at, last_login
      FROM users
      WHERE id = $1 AND active = true
    `;

    const result = await this.db.query(query, [id]);
    return result.rows[0] || null;
  }

  async validatePassword(password, hashedPassword) {
    return await bcrypt.compare(password, hashedPassword);
  }

  async updateLastLogin(id) {
    const query = `
      UPDATE users
      SET last_login = NOW(), updated_at = NOW()
      WHERE id = $1
      RETURNING last_login
    `;

    const result = await this.db.query(query, [id]);
    return result.rows[0];
  }

  async updateProfile(id, updates) {
    const allowedFields = ['username', 'email'];
    const fields = Object.keys(updates).filter(field => allowedFields.includes(field));

    if (fields.length === 0) {
      throw new Error('No valid fields to update');
    }

    const setClause = fields.map((field, index) => `${field} = $${index + 2}`).join(', ');
    const query = `
      UPDATE users
      SET ${setClause}, updated_at = NOW()
      WHERE id = $1 AND active = true
      RETURNING id, email, username, role, updated_at
    `;

    const values = [id, ...fields.map(field => updates[field])];
    const result = await this.db.query(query, values);
    return result.rows[0];
  }

  async deactivate(id) {
    const query = `
      UPDATE users
      SET active = false, updated_at = NOW()
      WHERE id = $1
      RETURNING id
    `;

    const result = await this.db.query(query, [id]);
    return result.rows[0];
  }

  async list({ limit = 50, offset = 0, role = null }) {
    let query = `
      SELECT id, email, username, role, created_at, updated_at, last_login
      FROM users
      WHERE active = true
    `;

    const values = [];
    let paramCount = 0;

    if (role) {
      paramCount++;
      query += ` AND role = $${paramCount}`;
      values.push(role);
    }

    query += ` ORDER BY created_at DESC LIMIT $${++paramCount} OFFSET $${++paramCount}`;
    values.push(limit, offset);

    const result = await this.db.query(query, values);
    return result.rows;
  }

  async count({ role = null }) {
    let query = 'SELECT COUNT(*) as total FROM users WHERE active = true';
    const values = [];

    if (role) {
      query += ' AND role = $1';
      values.push(role);
    }

    const result = await this.db.query(query, values);
    return parseInt(result.rows[0].total);
  }
}

module.exports = User;