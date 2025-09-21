#!/usr/bin/env node

/**
 * Migration Runner for Database Service
 * Handles running and tracking database migrations
 */

const fs = require('fs').promises;
const path = require('path');
require('dotenv').config();

const DatabaseConnection = require('../src/database/connection');
const winston = require('winston');

// Logger setup
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.colorize(),
    winston.format.simple()
  ),
  transports: [
    new winston.transports.Console()
  ]
});

class MigrationRunner {
  constructor() {
    this.db = new DatabaseConnection();
    this.migrationsPath = __dirname;
  }

  async initialize() {
    try {
      await this.db.connect();
      await this.createMigrationsTable();
      logger.info('Migration runner initialized');
    } catch (error) {
      logger.error('Failed to initialize migration runner:', error);
      throw error;
    }
  }

  async createMigrationsTable() {
    const query = `
      CREATE TABLE IF NOT EXISTS schema_migrations (
        id SERIAL PRIMARY KEY,
        filename VARCHAR(255) NOT NULL UNIQUE,
        checksum VARCHAR(64),
        executed_at TIMESTAMP NOT NULL DEFAULT NOW(),
        execution_time_ms INTEGER,
        success BOOLEAN NOT NULL DEFAULT true
      )
    `;

    await this.db.query(query);
    logger.info('Schema migrations table ready');
  }

  async getMigrationFiles() {
    try {
      const files = await fs.readdir(this.migrationsPath);
      return files
        .filter(file => file.endsWith('.sql') && file !== 'migrate.js')
        .sort(); // Execute in alphabetical order
    } catch (error) {
      logger.error('Error reading migrations directory:', error);
      return [];
    }
  }

  async getCompletedMigrations() {
    try {
      const result = await this.db.query(
        'SELECT filename, executed_at, success FROM schema_migrations ORDER BY executed_at'
      );
      return result.rows;
    } catch (error) {
      logger.warn('Could not fetch completed migrations:', error.message);
      return [];
    }
  }

  async calculateChecksum(content) {
    const crypto = require('crypto');
    return crypto.createHash('sha256').update(content).digest('hex');
  }

  async runMigration(filename) {
    const migrationPath = path.join(this.migrationsPath, filename);
    const startTime = Date.now();

    try {
      logger.info(`Running migration: ${filename}`);

      const migrationContent = await fs.readFile(migrationPath, 'utf8');
      const checksum = await this.calculateChecksum(migrationContent);

      // Execute migration in transaction
      await this.db.transaction(async (client) => {
        // Execute the migration SQL
        await client.query(migrationContent);

        // Record successful migration
        const executionTime = Date.now() - startTime;
        await client.query(
          `INSERT INTO schema_migrations (filename, checksum, executed_at, execution_time_ms, success)
           VALUES ($1, $2, NOW(), $3, true)`,
          [filename, checksum, executionTime]
        );

        logger.info(`Migration ${filename} completed successfully (${executionTime}ms)`);
      });

      return {
        filename,
        status: 'completed',
        executionTime: Date.now() - startTime
      };

    } catch (error) {
      const executionTime = Date.now() - startTime;

      // Record failed migration
      try {
        await this.db.query(
          `INSERT INTO schema_migrations (filename, executed_at, execution_time_ms, success)
           VALUES ($1, NOW(), $2, false)`,
          [filename, executionTime]
        );
      } catch (logError) {
        logger.error('Failed to log migration failure:', logError);
      }

      logger.error(`Migration ${filename} failed:`, error);
      throw error;
    }
  }

  async runAllMigrations() {
    try {
      await this.initialize();

      const migrationFiles = await this.getMigrationFiles();
      const completedMigrations = await this.getCompletedMigrations();

      // Get successful migrations only
      const completedSet = new Set(
        completedMigrations
          .filter(m => m.success)
          .map(m => m.filename)
      );

      const pendingMigrations = migrationFiles.filter(file => !completedSet.has(file));

      if (pendingMigrations.length === 0) {
        logger.info('No pending migrations found');
        return { status: 'up_to_date', migrations: [] };
      }

      logger.info(`Found ${pendingMigrations.length} pending migrations`);

      const results = [];
      for (const filename of pendingMigrations) {
        try {
          const result = await this.runMigration(filename);
          results.push(result);
        } catch (error) {
          logger.error(`Stopping migration process due to failure in ${filename}`);
          break;
        }
      }

      logger.info(`Migration process completed. Ran ${results.length} migrations.`);

      return {
        status: 'completed',
        migrations: results
      };

    } catch (error) {
      logger.error('Migration process failed:', error);
      throw error;
    } finally {
      await this.db.disconnect();
    }
  }

  async getMigrationStatus() {
    try {
      await this.initialize();

      const migrationFiles = await this.getMigrationFiles();
      const completedMigrations = await this.getCompletedMigrations();

      const status = migrationFiles.map(filename => {
        const completed = completedMigrations.find(m => m.filename === filename);
        return {
          filename,
          status: completed ? (completed.success ? 'completed' : 'failed') : 'pending',
          executedAt: completed?.executed_at || null,
          success: completed?.success || null
        };
      });

      return status;

    } finally {
      await this.db.disconnect();
    }
  }
}

// CLI interface
async function main() {
  const command = process.argv[2];
  const runner = new MigrationRunner();

  try {
    switch (command) {
      case 'status':
        const status = await runner.getMigrationStatus();
        console.log('\nMigration Status:');
        console.log('================');
        status.forEach(migration => {
          const statusIcon = migration.status === 'completed' ? '✅' :
                           migration.status === 'failed' ? '❌' : '⏳';
          console.log(`${statusIcon} ${migration.filename} - ${migration.status}`);
          if (migration.executedAt) {
            console.log(`   Executed: ${migration.executedAt}`);
          }
        });
        break;

      case 'up':
      case undefined:
        const result = await runner.runAllMigrations();
        if (result.status === 'up_to_date') {
          console.log('✅ Database is up to date');
        } else {
          console.log(`✅ Completed ${result.migrations.length} migrations`);
        }
        break;

      default:
        console.log('Usage: node migrate.js [command]');
        console.log('Commands:');
        console.log('  up       Run pending migrations (default)');
        console.log('  status   Show migration status');
        process.exit(1);
    }
  } catch (error) {
    logger.error('Migration failed:', error);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = MigrationRunner;