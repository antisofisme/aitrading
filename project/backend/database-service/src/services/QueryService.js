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

class QueryService {
  constructor(db) {
    this.db = db;
  }

  async executeQuery(query, params = []) {
    try {
      logger.info('Executing query', {
        query: query.substring(0, 100),
        paramCount: params.length
      });

      const result = await this.db.query(query, params);
      return {
        success: true,
        data: result.rows,
        rowCount: result.rowCount,
        fields: result.fields?.map(f => ({ name: f.name, type: f.dataTypeID })) || []
      };
    } catch (error) {
      logger.error('Query execution failed', {
        error: error.message,
        query: query.substring(0, 100)
      });

      return {
        success: false,
        error: error.message,
        code: error.code
      };
    }
  }

  async executeTransaction(queries) {
    const client = await this.db.getClient();

    try {
      await client.query('BEGIN');
      logger.info('Transaction started', { queryCount: queries.length });

      const results = [];

      for (const { query, params = [] } of queries) {
        const result = await client.query(query, params);
        results.push({
          success: true,
          data: result.rows,
          rowCount: result.rowCount
        });
      }

      await client.query('COMMIT');
      logger.info('Transaction committed successfully');

      return {
        success: true,
        results
      };
    } catch (error) {
      await client.query('ROLLBACK');
      logger.error('Transaction rolled back', { error: error.message });

      return {
        success: false,
        error: error.message,
        code: error.code
      };
    } finally {
      client.release();
    }
  }

  async getTableInfo(tableName) {
    const query = `
      SELECT
        column_name,
        data_type,
        is_nullable,
        column_default,
        character_maximum_length
      FROM information_schema.columns
      WHERE table_name = $1
      AND table_schema = 'public'
      ORDER BY ordinal_position
    `;

    try {
      const result = await this.db.query(query, [tableName]);
      return {
        success: true,
        table: tableName,
        columns: result.rows
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  async listTables() {
    const query = `
      SELECT table_name, table_type
      FROM information_schema.tables
      WHERE table_schema = 'public'
      ORDER BY table_name
    `;

    try {
      const result = await this.db.query(query);
      return {
        success: true,
        tables: result.rows
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  async getQueryPlan(query, params = []) {
    try {
      const explainQuery = `EXPLAIN (FORMAT JSON, ANALYZE false) ${query}`;
      const result = await this.db.query(explainQuery, params);

      return {
        success: true,
        plan: result.rows[0]['QUERY PLAN']
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  async validateQuery(query) {
    // Basic query validation
    const forbiddenPatterns = [
      /DROP\s+TABLE/i,
      /DROP\s+DATABASE/i,
      /TRUNCATE/i,
      /DELETE\s+FROM\s+\w+\s*;?\s*$/i // DELETE without WHERE
    ];

    for (const pattern of forbiddenPatterns) {
      if (pattern.test(query)) {
        return {
          valid: false,
          error: 'Query contains forbidden operations'
        };
      }
    }

    // Check for balanced parentheses
    const openParens = (query.match(/\(/g) || []).length;
    const closeParens = (query.match(/\)/g) || []).length;

    if (openParens !== closeParens) {
      return {
        valid: false,
        error: 'Unbalanced parentheses in query'
      };
    }

    return { valid: true };
  }
}

module.exports = QueryService;