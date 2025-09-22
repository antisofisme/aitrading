const crypto = require('crypto');
const { promisify } = require('util');
const logger = require('../utils/logger');

// Windows DPAPI wrapper for credential encryption
let dpapi;
try {
  dpapi = require('win-dpapi');
} catch (error) {
  logger.warn('Windows DPAPI not available, using fallback encryption');
}

class SecurityManager {
  constructor() {
    this.credentials = new Map();
    this.encryptionKey = null;
    this.isInitialized = false;
    this.fallbackEncryption = !dpapi;

    // Certificate pinning configuration
    this.pinnedCertificates = new Map();
    this.tlsConfig = {
      minVersion: 'TLSv1.3',
      ciphers: [
        'TLS_AES_256_GCM_SHA384',
        'TLS_CHACHA20_POLY1305_SHA256',
        'TLS_AES_128_GCM_SHA256'
      ].join(':'),
      honorCipherOrder: true,
      secureProtocol: 'TLSv1_3_method'
    };
  }

  async initialize() {
    try {
      logger.info('Initializing Security Manager...');

      if (this.fallbackEncryption) {
        await this.initializeFallbackEncryption();
      } else {
        await this.initializeDPAPI();
      }

      // Initialize certificate pinning
      this.initializeCertificatePinning();

      this.isInitialized = true;
      logger.info('Security Manager initialized successfully');

    } catch (error) {
      logger.error('Failed to initialize Security Manager:', error);
      throw error;
    }
  }

  async initializeDPAPI() {
    logger.info('Initializing Windows DPAPI for credential encryption...');

    try {
      // Test DPAPI availability
      const testData = 'test_encryption';
      const encrypted = dpapi.protectData(Buffer.from(testData), null, 'CurrentUser');
      const decrypted = dpapi.unprotectData(encrypted, null, 'CurrentUser');

      if (decrypted.toString() !== testData) {
        throw new Error('DPAPI test failed');
      }

      logger.info('Windows DPAPI initialized successfully');

    } catch (error) {
      logger.error('DPAPI initialization failed:', error);
      this.fallbackEncryption = true;
      await this.initializeFallbackEncryption();
    }
  }

  async initializeFallbackEncryption() {
    logger.info('Initializing fallback encryption...');

    // Generate or load encryption key
    this.encryptionKey = await this.generateOrLoadEncryptionKey();

    logger.info('Fallback encryption initialized');
  }

  async generateOrLoadEncryptionKey() {
    const keyFile = './security/encryption.key';
    const fs = require('fs').promises;
    const path = require('path');

    try {
      // Try to load existing key
      const keyData = await fs.readFile(keyFile);
      return keyData;

    } catch (error) {
      // Generate new key
      logger.info('Generating new encryption key...');

      const key = crypto.randomBytes(32); // 256-bit key

      // Ensure directory exists
      await fs.mkdir(path.dirname(keyFile), { recursive: true });

      // Save key securely
      await fs.writeFile(keyFile, key, { mode: 0o600 });

      logger.info('New encryption key generated and saved');
      return key;
    }
  }

  initializeCertificatePinning() {
    logger.info('Initializing certificate pinning...');

    // Add pinned certificates for backend services
    this.pinnedCertificates.set('localhost:3001', {
      fingerprint: null, // To be set when connecting
      algorithm: 'sha256'
    });

    this.pinnedCertificates.set('localhost:8000', {
      fingerprint: null, // To be set when connecting
      algorithm: 'sha256'
    });

    logger.info('Certificate pinning initialized');
  }

  async storeCredentials(service, credentials) {
    try {
      logger.info(`Storing credentials for service: ${service}`);

      const credentialData = JSON.stringify(credentials);

      let encryptedData;

      if (this.fallbackEncryption) {
        encryptedData = await this.encryptWithFallback(credentialData);
      } else {
        encryptedData = this.encryptWithDPAPI(credentialData);
      }

      this.credentials.set(service, {
        encrypted: encryptedData,
        timestamp: Date.now(),
        method: this.fallbackEncryption ? 'fallback' : 'dpapi'
      });

      logger.info(`Credentials for ${service} stored successfully`);

    } catch (error) {
      logger.error(`Failed to store credentials for ${service}:`, error);
      throw error;
    }
  }

  async getCredentials(service) {
    try {
      const storedData = this.credentials.get(service);

      if (!storedData) {
        logger.warn(`No credentials found for service: ${service}`);
        return null;
      }

      let decryptedData;

      if (storedData.method === 'fallback') {
        decryptedData = await this.decryptWithFallback(storedData.encrypted);
      } else {
        decryptedData = this.decryptWithDPAPI(storedData.encrypted);
      }

      const credentials = JSON.parse(decryptedData);

      logger.info(`Retrieved credentials for service: ${service}`);
      return credentials;

    } catch (error) {
      logger.error(`Failed to retrieve credentials for ${service}:`, error);
      throw error;
    }
  }

  encryptWithDPAPI(data) {
    try {
      const buffer = Buffer.from(data, 'utf8');
      const encrypted = dpapi.protectData(buffer, null, 'CurrentUser');
      return encrypted;

    } catch (error) {
      logger.error('DPAPI encryption failed:', error);
      throw error;
    }
  }

  decryptWithDPAPI(encryptedData) {
    try {
      const decrypted = dpapi.unprotectData(encryptedData, null, 'CurrentUser');
      return decrypted.toString('utf8');

    } catch (error) {
      logger.error('DPAPI decryption failed:', error);
      throw error;
    }
  }

  async encryptWithFallback(data) {
    try {
      const iv = crypto.randomBytes(16);
      const cipher = crypto.createCipher('aes-256-gcm', this.encryptionKey);

      cipher.setAAD(Buffer.from('ai-trading-client'));

      let encrypted = cipher.update(data, 'utf8', 'base64');
      encrypted += cipher.final('base64');

      const authTag = cipher.getAuthTag();

      return {
        encrypted,
        iv: iv.toString('base64'),
        authTag: authTag.toString('base64')
      };

    } catch (error) {
      logger.error('Fallback encryption failed:', error);
      throw error;
    }
  }

  async decryptWithFallback(encryptedData) {
    try {
      const { encrypted, iv, authTag } = encryptedData;

      const decipher = crypto.createDecipher('aes-256-gcm', this.encryptionKey);

      decipher.setAAD(Buffer.from('ai-trading-client'));
      decipher.setAuthTag(Buffer.from(authTag, 'base64'));

      let decrypted = decipher.update(encrypted, 'base64', 'utf8');
      decrypted += decipher.final('utf8');

      return decrypted;

    } catch (error) {
      logger.error('Fallback decryption failed:', error);
      throw error;
    }
  }

  // TLS Configuration methods
  getTLSConfig() {
    return {
      ...this.tlsConfig,
      checkServerIdentity: this.checkServerIdentity.bind(this),
      // Custom certificate verification
      rejectUnauthorized: true
    };
  }

  checkServerIdentity(hostname, cert) {
    const expectedFingerprint = this.pinnedCertificates.get(hostname);

    if (expectedFingerprint && expectedFingerprint.fingerprint) {
      const actualFingerprint = crypto
        .createHash(expectedFingerprint.algorithm)
        .update(cert.raw)
        .digest('hex');

      if (actualFingerprint !== expectedFingerprint.fingerprint) {
        logger.error(`Certificate pinning failed for ${hostname}`);
        throw new Error('Certificate pinning validation failed');
      }

      logger.info(`Certificate pinning validated for ${hostname}`);
    } else {
      // Store fingerprint on first connection
      const fingerprint = crypto
        .createHash('sha256')
        .update(cert.raw)
        .digest('hex');

      this.pinnedCertificates.set(hostname, {
        fingerprint,
        algorithm: 'sha256'
      });

      logger.info(`Certificate fingerprint stored for ${hostname}: ${fingerprint}`);
    }

    return undefined; // Let default verification continue
  }

  // WebSocket security configuration
  getWebSocketSecurityConfig() {
    return {
      ...this.getTLSConfig(),
      headers: {
        'X-Client-Auth': this.generateClientAuth(),
        'X-Client-Version': '1.0.0',
        'X-Security-Level': 'high'
      }
    };
  }

  generateClientAuth() {
    // Generate client authentication token
    const timestamp = Date.now();
    const nonce = crypto.randomBytes(16).toString('hex');

    const payload = JSON.stringify({
      timestamp,
      nonce,
      client: 'ai-trading-client'
    });

    const signature = crypto
      .createHmac('sha256', this.encryptionKey || 'fallback-key')
      .update(payload)
      .digest('hex');

    return Buffer.from(JSON.stringify({
      payload,
      signature
    })).toString('base64');
  }

  // Credential validation
  async validateCredentials(service, credentials) {
    const requiredFields = {
      'mt5': ['server', 'login', 'password'],
      'backend': ['apiKey', 'secret']
    };

    const required = requiredFields[service] || [];

    for (const field of required) {
      if (!credentials[field]) {
        throw new Error(`Missing required field: ${field}`);
      }
    }

    // Additional validation for MT5 credentials
    if (service === 'mt5') {
      if (!/^\d+$/.test(credentials.login)) {
        throw new Error('Invalid MT5 login format');
      }

      if (credentials.password.length < 6) {
        throw new Error('MT5 password too short');
      }
    }

    return true;
  }

  // Security utilities
  generateSecureId(length = 32) {
    return crypto.randomBytes(length).toString('hex');
  }

  hashData(data, algorithm = 'sha256') {
    return crypto.createHash(algorithm).update(data).digest('hex');
  }

  secureCompare(a, b) {
    return crypto.timingSafeEqual(
      Buffer.from(a),
      Buffer.from(b)
    );
  }

  // Cleanup and security
  async clearCredentials(service) {
    if (this.credentials.has(service)) {
      this.credentials.delete(service);
      logger.info(`Credentials cleared for service: ${service}`);
    }
  }

  async clearAllCredentials() {
    this.credentials.clear();
    logger.info('All credentials cleared');
  }

  getSecurityStatus() {
    return {
      initialized: this.isInitialized,
      encryptionMethod: this.fallbackEncryption ? 'fallback' : 'dpapi',
      storedCredentials: Array.from(this.credentials.keys()),
      pinnedCertificates: Array.from(this.pinnedCertificates.keys()),
      tlsVersion: this.tlsConfig.minVersion
    };
  }
}

module.exports = SecurityManager;