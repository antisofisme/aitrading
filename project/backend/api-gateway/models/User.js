/**
 * User Model
 * User data structure and validation for Phase 1
 */

const { v4: uuidv4 } = require('uuid');
const passwordService = require('../utils/password');
const { database } = require('../config/database');

class User {
  constructor(userData) {
    this.id = userData.id || `user-${Date.now()}-${uuidv4().substr(0, 8)}`;
    this.email = userData.email;
    this.password = userData.password;
    this.firstName = userData.firstName || '';
    this.lastName = userData.lastName || '';
    this.role = userData.role || 'user';
    this.isActive = userData.isActive !== undefined ? userData.isActive : true;
    this.emailVerified = userData.emailVerified || false;
    this.createdAt = userData.createdAt || new Date();
    this.updatedAt = userData.updatedAt || new Date();
    this.lastLogin = userData.lastLogin || null;
    this.metadata = userData.metadata || {};
  }

  static validate(userData, isUpdate = false) {
    const errors = [];

    if (!isUpdate || userData.email !== undefined) {
      if (!userData.email) {
        errors.push('Email is required');
      } else if (!this.isValidEmail(userData.email)) {
        errors.push('Invalid email format');
      }
    }

    if (!isUpdate || userData.password !== undefined) {
      if (!userData.password) {
        errors.push('Password is required');
      } else {
        try {
          passwordService.validatePasswordStrength(userData.password);
        } catch (error) {
          errors.push(error.message);
        }
      }
    }

    if (userData.role !== undefined) {
      const validRoles = ['admin', 'user'];
      if (!validRoles.includes(userData.role)) {
        errors.push(`Role must be one of: ${validRoles.join(', ')}`);
      }
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  static async create(userData) {
    const validation = this.validate(userData);
    if (!validation.isValid) {
      throw new Error(`Validation failed: ${validation.errors.join(', ')}`);
    }

    const existingUser = await database.getUserByEmail(userData.email);
    if (existingUser) {
      throw new Error('User with this email already exists');
    }

    const hashedPassword = await passwordService.hashPassword(userData.password);
    const user = new User({ ...userData, password: hashedPassword });
    const savedUser = await database.createUser(user);

    return this.sanitize(savedUser);
  }

  static async findByEmail(email) {
    if (!email || !this.isValidEmail(email)) {
      return null;
    }

    const user = await database.getUserByEmail(email.toLowerCase());
    return user ? this.sanitize(user) : null;
  }

  static async findById(id) {
    if (!id) return null;

    const user = await database.getUserById(id);
    return user ? this.sanitize(user) : null;
  }

  static async update(id, updateData) {
    const user = await database.getUserById(id);
    if (!user) {
      throw new Error('User not found');
    }

    const validation = this.validate(updateData, true);
    if (!validation.isValid) {
      throw new Error(`Validation failed: ${validation.errors.join(', ')}`);
    }

    if (updateData.password) {
      updateData.password = await passwordService.hashPassword(updateData.password);
    }

    const updatedUser = await database.updateUser(user.email, {
      ...updateData,
      updatedAt: new Date()
    });

    return this.sanitize(updatedUser);
  }

  static async delete(id) {
    const user = await database.getUserById(id);
    if (!user) {
      throw new Error('User not found');
    }

    await database.deleteUser(user.email);
    return true;
  }

  static async authenticate(email, password) {
    if (!email || !password) {
      throw new Error('Email and password are required');
    }

    const user = await database.getUserByEmail(email.toLowerCase());
    if (!user) {
      throw new Error('Invalid credentials');
    }

    if (!user.isActive) {
      throw new Error('Account is deactivated');
    }

    const isValidPassword = await passwordService.comparePassword(password, user.password);
    if (!isValidPassword) {
      throw new Error('Invalid credentials');
    }

    await database.updateUser(user.email, { lastLogin: new Date() });

    return this.sanitize(user);
  }

  static async findAll(filters = {}) {
    const users = await database.getAllUsers();
    let filteredUsers = users;

    if (filters.role) {
      filteredUsers = filteredUsers.filter(user => user.role === filters.role);
    }

    if (filters.isActive !== undefined) {
      filteredUsers = filteredUsers.filter(user => user.isActive === filters.isActive);
    }

    if (filters.search) {
      const searchTerm = filters.search.toLowerCase();
      filteredUsers = filteredUsers.filter(user =>
        user.email.toLowerCase().includes(searchTerm) ||
        user.firstName.toLowerCase().includes(searchTerm) ||
        user.lastName.toLowerCase().includes(searchTerm)
      );
    }

    return filteredUsers.map(user => this.sanitize(user));
  }

  static sanitize(user) {
    if (!user) return null;

    const { password, ...sanitizedUser } = user;
    return sanitizedUser;
  }

  static isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  static async initializeDefaultUsers() {
    try {
      const adminUser = await database.getUserByEmail('admin@aitrading.com');
      if (!adminUser.password) {
        const hashedPassword = await passwordService.hashPassword('Admin123!');
        await database.updateUser('admin@aitrading.com', { password: hashedPassword });
      }

      const testUser = await database.getUserByEmail('user@aitrading.com');
      if (!testUser.password) {
        const hashedPassword = await passwordService.hashPassword('User123!');
        await database.updateUser('user@aitrading.com', { password: hashedPassword });
      }

      console.log('Default users initialized successfully');
    } catch (error) {
      console.error('Error initializing default users:', error.message);
    }
  }
}

module.exports = User;