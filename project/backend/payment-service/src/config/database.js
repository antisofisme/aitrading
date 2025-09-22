const mongoose = require('mongoose');
const logger = require('./logger');

class DatabaseConnection {
  constructor() {
    this.isConnected = false;
  }

  async connect() {
    try {
      const mongoUrl = process.env.MONGODB_URI || 'mongodb://localhost:27017/payment_service';

      const options = {
        useNewUrlParser: true,
        useUnifiedTopology: true,
        maxPoolSize: 10,
        serverSelectionTimeoutMS: 5000,
        socketTimeoutMS: 45000,
        family: 4
      };

      await mongoose.connect(mongoUrl, options);
      this.isConnected = true;

      logger.info('✅ MongoDB connected successfully', {
        service: 'payment-service',
        database: mongoUrl.split('@')[1] || 'localhost'
      });

      mongoose.connection.on('error', (err) => {
        logger.error('❌ MongoDB connection error', { error: err.message });
        this.isConnected = false;
      });

      mongoose.connection.on('disconnected', () => {
        logger.warn('⚠️ MongoDB disconnected');
        this.isConnected = false;
      });

      mongoose.connection.on('reconnected', () => {
        logger.info('🔄 MongoDB reconnected');
        this.isConnected = true;
      });

    } catch (error) {
      logger.error('❌ MongoDB connection failed', { error: error.message });
      throw error;
    }
  }

  async disconnect() {
    try {
      await mongoose.disconnect();
      this.isConnected = false;
      logger.info('📤 MongoDB disconnected gracefully');
    } catch (error) {
      logger.error('❌ Error disconnecting from MongoDB', { error: error.message });
      throw error;
    }
  }

  getConnectionStatus() {
    return {
      isConnected: this.isConnected,
      readyState: mongoose.connection.readyState,
      host: mongoose.connection.host,
      port: mongoose.connection.port,
      name: mongoose.connection.name
    };
  }
}

module.exports = new DatabaseConnection();