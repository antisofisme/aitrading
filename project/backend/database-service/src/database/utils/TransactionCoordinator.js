/**
 * Cross-Database Transaction Coordinator
 * Manages distributed transactions across multiple database types
 */

const EventEmitter = require('events');
const { v4: uuidv4 } = require('uuid');
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'logs/transaction-coordinator.log' })
  ]
});

class TransactionCoordinator extends EventEmitter {
  constructor(databaseFactory) {
    super();
    this.databaseFactory = databaseFactory;
    this.activeTransactions = new Map();
    this.transactionTimeout = 300000; // 5 minutes default
    this.maxRetries = 3;
  }

  /**
   * Begin distributed transaction
   * @param {Array} databases - List of database types to include
   * @param {Object} options - Transaction options
   */
  async beginDistributedTransaction(databases, options = {}) {
    const transactionId = uuidv4();
    const timeout = options.timeout || this.transactionTimeout;

    const transaction = {
      id: transactionId,
      databases: databases,
      participants: new Map(),
      status: 'preparing',
      startTime: Date.now(),
      timeout: timeout,
      operations: [],
      compensations: [],
      retryCount: 0,
      maxRetries: options.maxRetries || this.maxRetries
    };

    try {
      logger.info('Beginning distributed transaction', {
        transactionId,
        databases,
        timeout
      });

      // Prepare phase - begin transaction on each database
      for (const dbType of databases) {
        const database = this.databaseFactory.getDatabase(dbType);
        if (!database) {
          throw new Error(`Database ${dbType} not available`);
        }

        try {
          let dbTransaction;

          // Handle database-specific transaction mechanisms
          if (this.supportsTransactions(dbType)) {
            dbTransaction = await database.beginTransaction();
          } else {
            // For databases that don't support transactions, use compensation patterns
            dbTransaction = new CompensationTransaction(database, dbType);
          }

          transaction.participants.set(dbType, {
            database,
            transaction: dbTransaction,
            status: 'prepared',
            operations: []
          });

          logger.debug(`Prepared transaction for ${dbType}`, { transactionId });
        } catch (error) {
          logger.error(`Failed to prepare transaction for ${dbType}:`, error);

          // Rollback already prepared transactions
          await this.rollbackTransaction(transactionId);
          throw error;
        }
      }

      transaction.status = 'active';
      this.activeTransactions.set(transactionId, transaction);

      // Set timeout
      setTimeout(() => {
        this.handleTransactionTimeout(transactionId);
      }, timeout);

      logger.info('Distributed transaction prepared successfully', { transactionId });
      this.emit('transaction_began', { transactionId, databases });

      return transactionId;
    } catch (error) {
      logger.error('Failed to begin distributed transaction:', error);
      throw error;
    }
  }

  /**
   * Add operation to transaction
   * @param {string} transactionId - Transaction ID
   * @param {string} database - Database type
   * @param {Function} operation - Operation function
   * @param {Function} compensation - Compensation function (for rollback)
   */
  async addOperation(transactionId, database, operation, compensation = null) {
    const transaction = this.activeTransactions.get(transactionId);
    if (!transaction) {
      throw new Error(`Transaction ${transactionId} not found`);
    }

    if (transaction.status !== 'active') {
      throw new Error(`Transaction ${transactionId} is not active`);
    }

    const participant = transaction.participants.get(database);
    if (!participant) {
      throw new Error(`Database ${database} not part of transaction ${transactionId}`);
    }

    const operationId = uuidv4();
    const operationRecord = {
      id: operationId,
      database,
      operation,
      compensation,
      timestamp: Date.now(),
      status: 'pending'
    };

    try {
      logger.debug('Executing operation in transaction', {
        transactionId,
        operationId,
        database
      });

      // Execute the operation
      const result = await operation(participant.transaction, participant.database);

      operationRecord.result = result;
      operationRecord.status = 'completed';

      // Store operation and compensation
      transaction.operations.push(operationRecord);
      participant.operations.push(operationRecord);

      if (compensation) {
        transaction.compensations.unshift({
          id: operationId,
          database,
          compensation,
          timestamp: Date.now()
        });
      }

      logger.debug('Operation completed successfully', {
        transactionId,
        operationId,
        database
      });

      this.emit('operation_completed', {
        transactionId,
        operationId,
        database,
        result
      });

      return result;
    } catch (error) {
      operationRecord.error = error.message;
      operationRecord.status = 'failed';
      transaction.operations.push(operationRecord);

      logger.error('Operation failed in transaction', {
        transactionId,
        operationId,
        database,
        error: error.message
      });

      this.emit('operation_failed', {
        transactionId,
        operationId,
        database,
        error: error.message
      });

      throw error;
    }
  }

  /**
   * Commit distributed transaction
   * @param {string} transactionId - Transaction ID
   */
  async commitTransaction(transactionId) {
    const transaction = this.activeTransactions.get(transactionId);
    if (!transaction) {
      throw new Error(`Transaction ${transactionId} not found`);
    }

    if (transaction.status !== 'active') {
      throw new Error(`Transaction ${transactionId} is not active (status: ${transaction.status})`);
    }

    transaction.status = 'committing';
    logger.info('Committing distributed transaction', { transactionId });

    try {
      // Two-phase commit protocol

      // Phase 1: Prepare all participants
      const preparePromises = [];
      transaction.participants.forEach((participant, dbType) => {
        preparePromises.push(this.prepareCommit(transactionId, dbType, participant));
      });

      const prepareResults = await Promise.allSettled(preparePromises);
      const failedPrepares = prepareResults.filter(result => result.status === 'rejected');

      if (failedPrepares.length > 0) {
        logger.error('Prepare phase failed, rolling back transaction', {
          transactionId,
          failures: failedPrepares.map(f => f.reason?.message)
        });

        await this.rollbackTransaction(transactionId);
        throw new Error('Transaction prepare phase failed');
      }

      // Phase 2: Commit all participants
      const commitPromises = [];
      transaction.participants.forEach((participant, dbType) => {
        commitPromises.push(this.commitParticipant(transactionId, dbType, participant));
      });

      const commitResults = await Promise.allSettled(commitPromises);
      const failedCommits = commitResults.filter(result => result.status === 'rejected');

      if (failedCommits.length > 0) {
        logger.error('Commit phase failed for some participants', {
          transactionId,
          failures: failedCommits.map(f => f.reason?.message)
        });

        // This is a critical state - some databases committed, others didn't
        transaction.status = 'partially_committed';
        this.emit('transaction_partially_committed', {
          transactionId,
          failures: failedCommits
        });

        throw new Error('Transaction partially committed');
      }

      // Success
      transaction.status = 'committed';
      transaction.endTime = Date.now();

      logger.info('Distributed transaction committed successfully', {
        transactionId,
        duration: transaction.endTime - transaction.startTime,
        operations: transaction.operations.length
      });

      this.emit('transaction_committed', { transactionId, transaction });

      // Clean up after delay to allow for auditing
      setTimeout(() => {
        this.activeTransactions.delete(transactionId);
      }, 60000); // Keep for 1 minute

      return {
        transactionId,
        status: 'committed',
        duration: transaction.endTime - transaction.startTime,
        operations: transaction.operations.length
      };
    } catch (error) {
      transaction.status = 'commit_failed';
      logger.error('Failed to commit distributed transaction:', error);
      throw error;
    }
  }

  /**
   * Rollback distributed transaction
   * @param {string} transactionId - Transaction ID
   */
  async rollbackTransaction(transactionId) {
    const transaction = this.activeTransactions.get(transactionId);
    if (!transaction) {
      throw new Error(`Transaction ${transactionId} not found`);
    }

    transaction.status = 'rolling_back';
    logger.info('Rolling back distributed transaction', { transactionId });

    try {
      // Execute compensations in reverse order
      const compensationPromises = transaction.compensations.map(async (comp) => {
        try {
          const participant = transaction.participants.get(comp.database);
          await comp.compensation(participant.transaction, participant.database);

          logger.debug('Compensation executed', {
            transactionId,
            operationId: comp.id,
            database: comp.database
          });
        } catch (error) {
          logger.error('Compensation failed', {
            transactionId,
            operationId: comp.id,
            database: comp.database,
            error: error.message
          });
          // Continue with other compensations
        }
      });

      await Promise.allSettled(compensationPromises);

      // Rollback database transactions
      const rollbackPromises = [];
      transaction.participants.forEach((participant, dbType) => {
        rollbackPromises.push(this.rollbackParticipant(transactionId, dbType, participant));
      });

      await Promise.allSettled(rollbackPromises);

      transaction.status = 'rolled_back';
      transaction.endTime = Date.now();

      logger.info('Distributed transaction rolled back', {
        transactionId,
        duration: transaction.endTime - transaction.startTime
      });

      this.emit('transaction_rolled_back', { transactionId, transaction });

      // Clean up
      setTimeout(() => {
        this.activeTransactions.delete(transactionId);
      }, 30000);

      return {
        transactionId,
        status: 'rolled_back',
        duration: transaction.endTime - transaction.startTime
      };
    } catch (error) {
      transaction.status = 'rollback_failed';
      logger.error('Failed to rollback distributed transaction:', error);
      throw error;
    }
  }

  /**
   * Prepare commit for a participant
   */
  async prepareCommit(transactionId, dbType, participant) {
    try {
      if (this.supportsTransactions(dbType)) {
        // For databases with native transactions, prepare is implicit
        return { dbType, status: 'prepared' };
      } else {
        // For databases without transactions, validate operations
        return await this.validateOperations(transactionId, dbType, participant);
      }
    } catch (error) {
      logger.error(`Prepare failed for ${dbType} in transaction ${transactionId}:`, error);
      throw error;
    }
  }

  /**
   * Commit a participant
   */
  async commitParticipant(transactionId, dbType, participant) {
    try {
      if (this.supportsTransactions(dbType)) {
        await participant.database.commitTransaction(participant.transaction);
      } else {
        // For databases without transactions, commit is implicit
        // Operations were already executed
      }

      logger.debug(`Committed participant ${dbType} in transaction ${transactionId}`);
      return { dbType, status: 'committed' };
    } catch (error) {
      logger.error(`Commit failed for ${dbType} in transaction ${transactionId}:`, error);
      throw error;
    }
  }

  /**
   * Rollback a participant
   */
  async rollbackParticipant(transactionId, dbType, participant) {
    try {
      if (this.supportsTransactions(dbType)) {
        await participant.database.rollbackTransaction(participant.transaction);
      }
      // Compensations are handled separately

      logger.debug(`Rolled back participant ${dbType} in transaction ${transactionId}`);
      return { dbType, status: 'rolled_back' };
    } catch (error) {
      logger.error(`Rollback failed for ${dbType} in transaction ${transactionId}:`, error);
      // Don't throw - continue with other rollbacks
      return { dbType, status: 'rollback_failed', error: error.message };
    }
  }

  /**
   * Check if database supports native transactions
   */
  supportsTransactions(dbType) {
    const transactionSupport = {
      postgresql: true,
      arangodb: true,
      clickhouse: false,
      weaviate: false,
      dragonflydb: true // MULTI/EXEC
    };

    return transactionSupport[dbType] || false;
  }

  /**
   * Validate operations for databases without native transactions
   */
  async validateOperations(transactionId, dbType, participant) {
    // This would implement database-specific validation logic
    // For now, assume operations are valid if they were executed successfully
    const failedOps = participant.operations.filter(op => op.status === 'failed');

    if (failedOps.length > 0) {
      throw new Error(`Operations failed for ${dbType}: ${failedOps.map(op => op.id).join(', ')}`);
    }

    return { dbType, status: 'validated' };
  }

  /**
   * Handle transaction timeout
   */
  async handleTransactionTimeout(transactionId) {
    const transaction = this.activeTransactions.get(transactionId);
    if (!transaction || transaction.status !== 'active') {
      return;
    }

    logger.warn('Transaction timeout, rolling back', { transactionId });

    try {
      await this.rollbackTransaction(transactionId);
    } catch (error) {
      logger.error('Failed to rollback timed out transaction:', error);
    }

    this.emit('transaction_timeout', { transactionId });
  }

  /**
   * Get transaction status
   */
  getTransactionStatus(transactionId) {
    const transaction = this.activeTransactions.get(transactionId);
    if (!transaction) {
      return null;
    }

    return {
      id: transaction.id,
      status: transaction.status,
      databases: transaction.databases,
      startTime: transaction.startTime,
      endTime: transaction.endTime,
      operationCount: transaction.operations.length,
      duration: transaction.endTime ?
        transaction.endTime - transaction.startTime :
        Date.now() - transaction.startTime
    };
  }

  /**
   * Get all active transactions
   */
  getActiveTransactions() {
    const transactions = {};
    this.activeTransactions.forEach((transaction, id) => {
      transactions[id] = this.getTransactionStatus(id);
    });
    return transactions;
  }

  /**
   * Force rollback of transaction (admin operation)
   */
  async forceRollback(transactionId) {
    logger.warn('Force rolling back transaction', { transactionId });
    return await this.rollbackTransaction(transactionId);
  }

  /**
   * Clean up stale transactions
   */
  cleanupStaleTransactions() {
    const staleThreshold = Date.now() - (this.transactionTimeout * 2);
    const staleTransactions = [];

    this.activeTransactions.forEach((transaction, id) => {
      if (transaction.startTime < staleThreshold) {
        staleTransactions.push(id);
      }
    });

    logger.info('Cleaning up stale transactions', { count: staleTransactions.length });

    staleTransactions.forEach(async (id) => {
      try {
        await this.rollbackTransaction(id);
      } catch (error) {
        logger.error(`Failed to cleanup stale transaction ${id}:`, error);
        this.activeTransactions.delete(id);
      }
    });
  }
}

/**
 * Compensation Transaction for databases without native transaction support
 */
class CompensationTransaction {
  constructor(database, dbType) {
    this.database = database;
    this.dbType = dbType;
    this.operations = [];
  }

  addOperation(operation, compensation) {
    this.operations.push({ operation, compensation });
  }

  async compensate() {
    // Execute compensations in reverse order
    for (let i = this.operations.length - 1; i >= 0; i--) {
      const { compensation } = this.operations[i];
      if (compensation) {
        try {
          await compensation();
        } catch (error) {
          logger.error('Compensation operation failed:', error);
          // Continue with other compensations
        }
      }
    }
  }
}

module.exports = TransactionCoordinator;