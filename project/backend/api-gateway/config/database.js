/**
 * In-Memory Database Configuration for Phase 1
 * Simple user storage for development and testing
 * Production will use PostgreSQL/MongoDB
 */

class InMemoryDatabase {
  constructor() {
    this.users = new Map();
    this.sessions = new Map();
    this.initializeDefaultUsers();
  }

  initializeDefaultUsers() {
    // Default admin user
    this.users.set('admin@aitrading.com', {
      id: 'admin-001',
      email: 'admin@aitrading.com',
      password: null, // Will be hashed
      role: 'admin',
      firstName: 'Admin',
      lastName: 'User',
      isActive: true,
      createdAt: new Date(),
      updatedAt: new Date(),
      lastLogin: null
    });

    // Default test user
    this.users.set('user@aitrading.com', {
      id: 'user-001',
      email: 'user@aitrading.com',
      password: null, // Will be hashed
      role: 'user',
      firstName: 'Test',
      lastName: 'User',
      isActive: true,
      createdAt: new Date(),
      updatedAt: new Date(),
      lastLogin: null
    });
  }

  // User operations
  async createUser(userData) {
    const user = {
      id: `user-${Date.now()}`,
      ...userData,
      createdAt: new Date(),
      updatedAt: new Date(),
      lastLogin: null
    };

    this.users.set(userData.email, user);
    return user;
  }

  async getUserByEmail(email) {
    return this.users.get(email) || null;
  }

  async getUserById(id) {
    for (const user of this.users.values()) {
      if (user.id === id) {
        return user;
      }
    }
    return null;
  }

  async updateUser(email, updates) {
    const user = this.users.get(email);
    if (!user) return null;

    const updatedUser = {
      ...user,
      ...updates,
      updatedAt: new Date()
    };

    this.users.set(email, updatedUser);
    return updatedUser;
  }

  async deleteUser(email) {
    return this.users.delete(email);
  }

  async getAllUsers() {
    return Array.from(this.users.values());
  }

  // Session operations
  async createSession(userId, sessionData) {
    const sessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const session = {
      id: sessionId,
      userId,
      ...sessionData,
      createdAt: new Date(),
      lastAccessed: new Date()
    };

    this.sessions.set(sessionId, session);
    return session;
  }

  async getSession(sessionId) {
    const session = this.sessions.get(sessionId);
    if (session) {
      session.lastAccessed = new Date();
      this.sessions.set(sessionId, session);
    }
    return session || null;
  }

  async deleteSession(sessionId) {
    return this.sessions.delete(sessionId);
  }

  async deleteUserSessions(userId) {
    let deletedCount = 0;
    for (const [sessionId, session] of this.sessions.entries()) {
      if (session.userId === userId) {
        this.sessions.delete(sessionId);
        deletedCount++;
      }
    }
    return deletedCount;
  }

  // Cleanup expired sessions
  async cleanupExpiredSessions() {
    const now = new Date();
    let cleanedCount = 0;

    for (const [sessionId, session] of this.sessions.entries()) {
      const hoursSinceLastAccess = (now - session.lastAccessed) / (1000 * 60 * 60);
      if (hoursSinceLastAccess > 24) { // 24 hours expiry
        this.sessions.delete(sessionId);
        cleanedCount++;
      }
    }

    return cleanedCount;
  }
}

// Singleton instance
const database = new InMemoryDatabase();

module.exports = {
  database,
  InMemoryDatabase
};