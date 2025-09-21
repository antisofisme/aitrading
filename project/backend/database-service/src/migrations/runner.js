const fs = require('fs').promises;
const path = require('path');
const DatabaseConfig = require('../config/database');
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console()
  ]
});

class MigrationRunner {
  constructor() {
    this.db = new DatabaseConfig();
    this.migrationDir = path.join(__dirname, '../../migrations');
  }

  async initialize() {
    await this.db.initialize();
    await this.createMigrationsTable();
  }

  async createMigrationsTable() {
    const query = `
      CREATE TABLE IF NOT EXISTS migrations (
        id SERIAL PRIMARY KEY,
        filename VARCHAR(255) UNIQUE NOT NULL,
        applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
      )
    `;

    await this.db.query(query);
    logger.info('Migrations table ready');
  }

  async getAppliedMigrations() {
    const query = 'SELECT filename FROM migrations ORDER BY id';
    const result = await this.db.query(query);
    return result.rows.map(row => row.filename);
  }

  async getMigrationFiles() {
    try {
      const files = await fs.readdir(this.migrationDir);
      return files
        .filter(file => file.endsWith('.sql'))
        .sort();
    } catch (error) {
      logger.error('Error reading migration directory:', error);
      return [];
    }
  }

  async runMigration(filename) {
    const filePath = path.join(this.migrationDir, filename);

    try {
      const sql = await fs.readFile(filePath, 'utf8');

      // Execute migration in transaction
      const client = await this.db.getClient();

      try {
        await client.query('BEGIN');

        // Execute the migration SQL
        await client.query(sql);

        // Record migration as applied
        await client.query(
          'INSERT INTO migrations (filename) VALUES ($1)',
          [filename]
        );

        await client.query('COMMIT');
        logger.info(`Migration applied: ${filename}`);

      } catch (error) {
        await client.query('ROLLBACK');
        throw error;
      } finally {
        client.release();
      }

    } catch (error) {
      logger.error(`Failed to apply migration ${filename}:`, error);
      throw error;
    }
  }

  async migrate() {
    try {
      await this.initialize();

      const appliedMigrations = await this.getAppliedMigrations();
      const migrationFiles = await this.getMigrationFiles();

      const pendingMigrations = migrationFiles.filter(
        file => !appliedMigrations.includes(file)
      );

      if (pendingMigrations.length === 0) {
        logger.info('No pending migrations');
        return;
      }

      logger.info(`Found ${pendingMigrations.length} pending migrations`);

      for (const migration of pendingMigrations) {
        await this.runMigration(migration);
      }

      logger.info('All migrations completed successfully');

    } catch (error) {
      logger.error('Migration failed:', error);
      process.exit(1);
    } finally {
      await this.db.close();
    }
  }

  async rollback(count = 1) {
    try {
      await this.initialize();

      const appliedMigrations = await this.getAppliedMigrations();

      if (appliedMigrations.length === 0) {
        logger.info('No migrations to rollback');
        return;
      }

      const toRollback = appliedMigrations.slice(-count);

      for (const migration of toRollback.reverse()) {
        const rollbackFile = migration.replace('.sql', '_rollback.sql');
        const rollbackPath = path.join(this.migrationDir, rollbackFile);

        try {
          const rollbackSql = await fs.readFile(rollbackPath, 'utf8');

          const client = await this.db.getClient();

          try {
            await client.query('BEGIN');
            await client.query(rollbackSql);
            await client.query(
              'DELETE FROM migrations WHERE filename = $1',
              [migration]
            );
            await client.query('COMMIT');

            logger.info(`Rolled back migration: ${migration}`);

          } catch (error) {
            await client.query('ROLLBACK');
            throw error;
          } finally {
            client.release();
          }

        } catch (error) {
          logger.warn(`No rollback file found for ${migration}, skipping`);
        }
      }

    } catch (error) {
      logger.error('Rollback failed:', error);
      process.exit(1);
    } finally {
      await this.db.close();
    }
  }
}

// CLI interface
if (require.main === module) {
  const runner = new MigrationRunner();
  const command = process.argv[2];

  switch (command) {
    case 'migrate':
      runner.migrate();
      break;
    case 'rollback':
      const count = parseInt(process.argv[3]) || 1;
      runner.rollback(count);
      break;
    default:
      console.log('Usage: node runner.js [migrate|rollback] [count]');
      process.exit(1);
  }
}

module.exports = MigrationRunner;