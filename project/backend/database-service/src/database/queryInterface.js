const winston = require('winston');
const fs = require('fs').promises;
const path = require('path');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

class QueryInterface {
  constructor(db) {
    this.db = db;
    this.migrationsPath = path.join(__dirname, '../../migrations');
  }

  async executeQuery(query, params = []) {
    try {
      // Basic security check - prevent dangerous operations in production
      if (process.env.NODE_ENV === 'production') {
        const dangerousKeywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER'];
        const upperQuery = query.toUpperCase();

        for (const keyword of dangerousKeywords) {
          if (upperQuery.includes(keyword)) {
            throw new Error(`Dangerous operation '${keyword}' not allowed in production`);
          }
        }
      }

      const result = await this.db.query(query, params);

      logger.info(`Query executed successfully, returned ${result.rowCount} rows`);

      return {
        rows: result.rows,
        rowCount: result.rowCount,
        fields: result.fields?.map(f => ({
          name: f.name,
          dataTypeID: f.dataTypeID
        })) || [],
        command: result.command
      };
    } catch (error) {
      logger.error('Query execution error:', error);
      throw error;
    }
  }

  async executeTransaction(queries) {
    try {
      return await this.db.transaction(async (client) => {
        const results = [];

        for (const { query, params = [] } of queries) {
          const result = await client.query(query, params);
          results.push({
            rows: result.rows,
            rowCount: result.rowCount,
            command: result.command
          });
        }

        return results;
      });
    } catch (error) {
      logger.error('Transaction execution error:', error);
      throw error;
    }
  }

  async runMigrations() {
    try {
      // Ensure migrations table exists
      await this.createMigrationsTable();

      // Get migration files
      const migrationFiles = await this.getMigrationFiles();

      // Get completed migrations
      const completedMigrations = await this.getCompletedMigrations();
      const completedSet = new Set(completedMigrations.map(m => m.filename));

      const results = [];

      for (const filename of migrationFiles) {
        if (!completedSet.has(filename)) {
          logger.info(`Running migration: ${filename}`);

          const migrationPath = path.join(this.migrationsPath, filename);
          const migrationContent = await fs.readFile(migrationPath, 'utf8');

          await this.db.transaction(async (client) => {
            // Execute migration
            await client.query(migrationContent);

            // Record migration
            await client.query(
              'INSERT INTO schema_migrations (filename, executed_at) VALUES ($1, NOW())',
              [filename]
            );
          });

          results.push({ filename, status: 'completed' });
          logger.info(`Migration completed: ${filename}`);
        } else {
          results.push({ filename, status: 'already_executed' });
        }
      }

      return results;
    } catch (error) {
      logger.error('Migration error:', error);
      throw error;
    }
  }

  async createMigrationsTable() {
    const query = `
      CREATE TABLE IF NOT EXISTS schema_migrations (
        id SERIAL PRIMARY KEY,
        filename VARCHAR(255) NOT NULL UNIQUE,
        executed_at TIMESTAMP NOT NULL DEFAULT NOW()
      )
    `;

    await this.db.query(query);
  }

  async getMigrationFiles() {
    try {
      const files = await fs.readdir(this.migrationsPath);
      return files
        .filter(file => file.endsWith('.sql'))
        .sort(); // Execute in alphabetical order
    } catch (error) {
      logger.warn('No migrations directory found, creating it');
      await fs.mkdir(this.migrationsPath, { recursive: true });
      return [];
    }
  }

  async getCompletedMigrations() {
    try {
      const result = await this.db.query(
        'SELECT filename, executed_at FROM schema_migrations ORDER BY executed_at'
      );
      return result.rows;
    } catch (error) {
      // Table doesn't exist yet
      return [];
    }
  }

  async rollbackMigration(filename) {
    try {
      const rollbackPath = path.join(this.migrationsPath, 'rollbacks', filename);
      const rollbackContent = await fs.readFile(rollbackPath, 'utf8');

      await this.db.transaction(async (client) => {
        // Execute rollback
        await client.query(rollbackContent);

        // Remove migration record
        await client.query(
          'DELETE FROM schema_migrations WHERE filename = $1',
          [filename]
        );
      });

      logger.info(`Rollback completed: ${filename}`);
      return { filename, status: 'rolled_back' };
    } catch (error) {
      logger.error('Rollback error:', error);
      throw error;
    }
  }

  async getTableInfo(tableName) {
    try {
      const query = `
        SELECT
          column_name,
          data_type,
          is_nullable,
          column_default,
          character_maximum_length
        FROM information_schema.columns
        WHERE table_name = $1
        ORDER BY ordinal_position
      `;

      const result = await this.db.query(query, [tableName]);
      return result.rows;
    } catch (error) {
      logger.error('Get table info error:', error);
      throw error;
    }
  }

  async listTables() {
    try {
      const query = `
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
      `;

      const result = await this.db.query(query);
      return result.rows.map(row => row.table_name);
    } catch (error) {
      logger.error('List tables error:', error);
      throw error;
    }
  }

  async getConnectionStats() {
    try {
      const pool = this.db.getPool();
      return {
        totalCount: pool.totalCount,
        idleCount: pool.idleCount,
        waitingCount: pool.waitingCount
      };
    } catch (error) {
      logger.error('Get connection stats error:', error);
      throw error;
    }
  }
}

module.exports = QueryInterface;