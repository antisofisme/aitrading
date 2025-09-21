/**
 * Password Utility Functions
 * Secure password hashing and validation using bcrypt
 */

const bcrypt = require('bcryptjs');
const jwtConfig = require('../config/jwt');

class PasswordService {
  /**
   * Hash a password using bcrypt
   */
  async hashPassword(password) {
    try {
      this.validatePasswordStrength(password);
      const salt = await bcrypt.genSalt(jwtConfig.bcryptRounds);
      return await bcrypt.hash(password, salt);
    } catch (error) {
      throw new Error(`Password hashing failed: ${error.message}`);
    }
  }

  /**
   * Compare password with hash
   */
  async comparePassword(password, hash) {
    try {
      if (!password || !hash) return false;
      return await bcrypt.compare(password, hash);
    } catch (error) {
      throw new Error(`Password comparison failed: ${error.message}`);
    }
  }

  /**
   * Validate password strength
   */
  validatePasswordStrength(password) {
    if (!password) throw new Error('Password is required');
    if (password.length < 8) throw new Error('Password must be at least 8 characters long');
    if (password.length > 128) throw new Error('Password must be less than 128 characters');
    if (!/[a-z]/.test(password)) throw new Error('Password must contain at least one lowercase letter');
    if (!/[A-Z]/.test(password)) throw new Error('Password must contain at least one uppercase letter');
    if (!/\d/.test(password)) throw new Error('Password must contain at least one number');
    if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
      throw new Error('Password must contain at least one special character');
    }

    const commonPasswords = ['password', 'password123', '123456', 'admin', 'qwerty'];
    if (commonPasswords.includes(password.toLowerCase())) {
      throw new Error('Password is too common and not secure');
    }
  }
}

module.exports = new PasswordService();