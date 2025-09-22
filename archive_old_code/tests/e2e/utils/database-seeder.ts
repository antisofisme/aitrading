import { exec } from 'child_process';
import { promisify } from 'util';
import * as fs from 'fs/promises';
import * as path from 'path';

const execAsync = promisify(exec);

/**
 * Database seeder for E2E test environment
 */
export class DatabaseSeeder {
  private databaseUrl: string;
  private seedsDir: string;

  constructor() {
    this.databaseUrl = process.env.DATABASE_URL || 'postgresql://test:test@localhost:5432/aitrading_test';
    this.seedsDir = path.join(__dirname, '../data/seeds');
  }

  /**
   * Setup database schema and initial data
   */
  async setupDatabase(): Promise<void> {
    console.log('Setting up test database...');

    try {
      await this.createSchema();
      await this.seedInitialData();
      await this.createIndexes();
      await this.setupTriggers();

      console.log('✅ Database setup completed');
    } catch (error) {
      console.error('❌ Database setup failed:', error);
      throw error;
    }
  }

  /**
   * Create database schema
   */
  private async createSchema(): Promise<void> {
    const schemaSQL = `
      -- Users table
      CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        first_name VARCHAR(100),
        last_name VARCHAR(100),
        role VARCHAR(50) NOT NULL DEFAULT 'trader',
        status VARCHAR(20) NOT NULL DEFAULT 'active',
        email_verified BOOLEAN DEFAULT false,
        two_factor_enabled BOOLEAN DEFAULT false,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
      );

      -- Portfolios table
      CREATE TABLE IF NOT EXISTS portfolios (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID REFERENCES users(id) ON DELETE CASCADE,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        balance DECIMAL(15,2) NOT NULL DEFAULT 0,
        equity DECIMAL(15,2) NOT NULL DEFAULT 0,
        margin_used DECIMAL(15,2) NOT NULL DEFAULT 0,
        margin_available DECIMAL(15,2) NOT NULL DEFAULT 0,
        total_pnl DECIMAL(15,2) NOT NULL DEFAULT 0,
        day_pnl DECIMAL(15,2) NOT NULL DEFAULT 0,
        currency VARCHAR(3) NOT NULL DEFAULT 'USD',
        leverage INTEGER NOT NULL DEFAULT 1,
        risk_level VARCHAR(20) NOT NULL DEFAULT 'moderate',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );

      -- Strategies table
      CREATE TABLE IF NOT EXISTS strategies (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID REFERENCES users(id) ON DELETE CASCADE,
        name VARCHAR(255) NOT NULL,
        type VARCHAR(50) NOT NULL,
        description TEXT,
        parameters JSONB,
        status VARCHAR(20) NOT NULL DEFAULT 'draft',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );

      -- Orders table
      CREATE TABLE IF NOT EXISTS orders (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID REFERENCES users(id) ON DELETE CASCADE,
        strategy_id UUID REFERENCES strategies(id) ON DELETE SET NULL,
        symbol VARCHAR(20) NOT NULL,
        side VARCHAR(10) NOT NULL,
        type VARCHAR(20) NOT NULL,
        quantity DECIMAL(15,2) NOT NULL,
        price DECIMAL(15,5),
        stop_loss DECIMAL(15,5),
        take_profit DECIMAL(15,5),
        status VARCHAR(20) NOT NULL DEFAULT 'pending',
        executed_price DECIMAL(15,5),
        executed_quantity DECIMAL(15,2),
        commission DECIMAL(15,2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        executed_at TIMESTAMP
      );

      -- Positions table
      CREATE TABLE IF NOT EXISTS positions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID REFERENCES users(id) ON DELETE CASCADE,
        strategy_id UUID REFERENCES strategies(id) ON DELETE SET NULL,
        symbol VARCHAR(20) NOT NULL,
        side VARCHAR(10) NOT NULL,
        quantity DECIMAL(15,2) NOT NULL,
        entry_price DECIMAL(15,5) NOT NULL,
        current_price DECIMAL(15,5) NOT NULL,
        unrealized_pnl DECIMAL(15,2) NOT NULL DEFAULT 0,
        stop_loss DECIMAL(15,5),
        take_profit DECIMAL(15,5),
        status VARCHAR(20) NOT NULL DEFAULT 'open',
        opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        closed_at TIMESTAMP,
        last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );

      -- Market data table
      CREATE TABLE IF NOT EXISTS market_data (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        symbol VARCHAR(20) NOT NULL,
        timestamp TIMESTAMP NOT NULL,
        open_price DECIMAL(15,5) NOT NULL,
        high_price DECIMAL(15,5) NOT NULL,
        low_price DECIMAL(15,5) NOT NULL,
        close_price DECIMAL(15,5) NOT NULL,
        volume BIGINT NOT NULL,
        spread DECIMAL(15,5) NOT NULL
      );

      -- Transactions table
      CREATE TABLE IF NOT EXISTS transactions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID REFERENCES users(id) ON DELETE CASCADE,
        portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
        type VARCHAR(50) NOT NULL,
        amount DECIMAL(15,2) NOT NULL,
        currency VARCHAR(3) NOT NULL DEFAULT 'USD',
        description TEXT,
        reference VARCHAR(100),
        status VARCHAR(20) NOT NULL DEFAULT 'completed',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        processed_at TIMESTAMP
      );

      -- Reports table
      CREATE TABLE IF NOT EXISTS reports (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID REFERENCES users(id) ON DELETE CASCADE,
        type VARCHAR(50) NOT NULL,
        title VARCHAR(255) NOT NULL,
        description TEXT,
        date_from DATE NOT NULL,
        date_to DATE NOT NULL,
        data JSONB,
        format VARCHAR(20) NOT NULL DEFAULT 'pdf',
        status VARCHAR(20) NOT NULL DEFAULT 'pending',
        file_path VARCHAR(500),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        generated_at TIMESTAMP
      );

      -- Audit logs table
      CREATE TABLE IF NOT EXISTS audit_logs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID REFERENCES users(id) ON DELETE SET NULL,
        action VARCHAR(100) NOT NULL,
        entity_type VARCHAR(50),
        entity_id UUID,
        old_values JSONB,
        new_values JSONB,
        ip_address INET,
        user_agent TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );

      -- Sessions table
      CREATE TABLE IF NOT EXISTS sessions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID REFERENCES users(id) ON DELETE CASCADE,
        token_hash VARCHAR(255) NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );

      -- Settings table
      CREATE TABLE IF NOT EXISTS settings (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID REFERENCES users(id) ON DELETE CASCADE,
        category VARCHAR(50) NOT NULL,
        key VARCHAR(100) NOT NULL,
        value JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, category, key)
      );
    `;

    await this.executeSQL(schemaSQL);
  }

  /**
   * Seed initial test data
   */
  private async seedInitialData(): Promise<void> {
    // Create test users
    await this.seedUsers();

    // Create portfolios
    await this.seedPortfolios();

    // Create sample strategies
    await this.seedStrategies();

    // Create market data
    await this.seedMarketData();

    // Create sample orders and positions
    await this.seedTradingData();

    // Create sample reports
    await this.seedReports();
  }

  /**
   * Seed test users
   */
  private async seedUsers(): Promise<void> {
    const usersSQL = `
      INSERT INTO users (id, email, password_hash, first_name, last_name, role, status, email_verified, two_factor_enabled) VALUES
      ('00000000-0000-0000-0000-000000000001', 'admin@test.com', '$2b$10$rGkz8QZ9uBz7vVHX8mKpnO8mKpnO8mKpnO8mKpnO8mKpnO8mKpnO', 'Admin', 'User', 'admin', 'active', true, false),
      ('00000000-0000-0000-0000-000000000002', 'trader1@test.com', '$2b$10$rGkz8QZ9uBz7vVHX8mKpnO8mKpnO8mKpnO8mKpnO8mKpnO8mKpnO', 'John', 'Trader', 'trader', 'active', true, false),
      ('00000000-0000-0000-0000-000000000003', 'premium1@test.com', '$2b$10$rGkz8QZ9uBz7vVHX8mKpnO8mKpnO8mKpnO8mKpnO8mKpnO8mKpnO', 'Jane', 'Premium', 'premium_trader', 'active', true, true),
      ('00000000-0000-0000-0000-000000000004', 'suspended@test.com', '$2b$10$rGkz8QZ9uBz7vVHX8mKpnO8mKpnO8mKpnO8mKpnO8mKpnO8mKpnO', 'Suspended', 'User', 'trader', 'suspended', true, false),
      ('00000000-0000-0000-0000-000000000005', 'trader2@test.com', '$2b$10$rGkz8QZ9uBz7vVHX8mKpnO8mKpnO8mKpnO8mKpnO8mKpnO8mKpnO', 'Bob', 'Wilson', 'trader', 'active', true, false)
      ON CONFLICT (email) DO NOTHING;
    `;

    await this.executeSQL(usersSQL);
  }

  /**
   * Seed test portfolios
   */
  private async seedPortfolios(): Promise<void> {
    const portfoliosSQL = `
      INSERT INTO portfolios (id, user_id, name, balance, equity, margin_used, margin_available, currency, leverage) VALUES
      ('00000000-0000-0000-0000-000000000101', '00000000-0000-0000-0000-000000000002', 'Main Portfolio', 100000.00, 105000.00, 15000.00, 85000.00, 'USD', 50),
      ('00000000-0000-0000-0000-000000000102', '00000000-0000-0000-0000-000000000003', 'Premium Portfolio', 250000.00, 268000.00, 45000.00, 205000.00, 'USD', 100),
      ('00000000-0000-0000-0000-000000000103', '00000000-0000-0000-0000-000000000005', 'Conservative Portfolio', 50000.00, 52000.00, 5000.00, 45000.00, 'USD', 10)
      ON CONFLICT (id) DO NOTHING;
    `;

    await this.executeSQL(portfoliosSQL);
  }

  /**
   * Seed test strategies
   */
  private async seedStrategies(): Promise<void> {
    const strategiesSQL = `
      INSERT INTO strategies (id, user_id, name, type, description, parameters, status) VALUES
      ('00000000-0000-0000-0000-000000000201', '00000000-0000-0000-0000-000000000002', 'Momentum Strategy', 'momentum', 'Trend following strategy', '{"timeframe": "1h", "rsi_period": 14, "ma_period": 20}', 'active'),
      ('00000000-0000-0000-0000-000000000202', '00000000-0000-0000-0000-000000000003', 'Mean Reversion', 'mean_reversion', 'Counter-trend strategy', '{"timeframe": "15m", "bollinger_period": 20, "rsi_oversold": 30}', 'active'),
      ('00000000-0000-0000-0000-000000000203', '00000000-0000-0000-0000-000000000005', 'Scalping Strategy', 'scalping', 'Quick profit strategy', '{"timeframe": "1m", "profit_target": 5, "stop_loss": 3}', 'paused')
      ON CONFLICT (id) DO NOTHING;
    `;

    await this.executeSQL(strategiesSQL);
  }

  /**
   * Seed market data
   */
  private async seedMarketData(): Promise<void> {
    const symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD'];
    let marketDataSQL = 'INSERT INTO market_data (symbol, timestamp, open_price, high_price, low_price, close_price, volume, spread) VALUES ';

    const values = [];
    const now = new Date();

    for (let i = 0; i < 1000; i++) {
      const timestamp = new Date(now.getTime() - (i * 60000)); // 1 minute intervals

      for (const symbol of symbols) {
        const basePrice = this.getBasePrice(symbol);
        const open = basePrice + (Math.random() - 0.5) * 0.01;
        const close = open + (Math.random() - 0.5) * 0.005;
        const high = Math.max(open, close) + Math.random() * 0.002;
        const low = Math.min(open, close) - Math.random() * 0.002;
        const volume = Math.floor(Math.random() * 100000) + 10000;
        const spread = Math.random() * 0.0001 + 0.00001;

        values.push(
          `('${symbol}', '${timestamp.toISOString()}', ${open.toFixed(5)}, ${high.toFixed(5)}, ${low.toFixed(5)}, ${close.toFixed(5)}, ${volume}, ${spread.toFixed(5)})`
        );
      }
    }

    marketDataSQL += values.join(', ') + ' ON CONFLICT DO NOTHING;';
    await this.executeSQL(marketDataSQL);
  }

  /**
   * Seed trading data (orders and positions)
   */
  private async seedTradingData(): Promise<void> {
    // Sample orders
    const ordersSQL = `
      INSERT INTO orders (id, user_id, strategy_id, symbol, side, type, quantity, price, status, executed_price, executed_quantity, commission, executed_at) VALUES
      ('00000000-0000-0000-0000-000000000301', '00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000201', 'EURUSD', 'buy', 'market', 10000, NULL, 'filled', 1.08450, 10000, 5.00, NOW() - INTERVAL '1 hour'),
      ('00000000-0000-0000-0000-000000000302', '00000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000202', 'GBPUSD', 'sell', 'limit', 15000, 1.25000, 'filled', 1.24980, 15000, 7.50, NOW() - INTERVAL '30 minutes'),
      ('00000000-0000-0000-0000-000000000303', '00000000-0000-0000-0000-000000000005', NULL, 'USDJPY', 'buy', 'market', 8000, NULL, 'pending', NULL, NULL, NULL, NULL)
      ON CONFLICT (id) DO NOTHING;
    `;

    // Sample positions
    const positionsSQL = `
      INSERT INTO positions (id, user_id, strategy_id, symbol, side, quantity, entry_price, current_price, unrealized_pnl, status) VALUES
      ('00000000-0000-0000-0000-000000000401', '00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000201', 'EURUSD', 'buy', 10000, 1.08450, 1.08520, 70.00, 'open'),
      ('00000000-0000-0000-0000-000000000402', '00000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000202', 'GBPUSD', 'sell', 15000, 1.24980, 1.24950, 45.00, 'open')
      ON CONFLICT (id) DO NOTHING;
    `;

    await this.executeSQL(ordersSQL);
    await this.executeSQL(positionsSQL);
  }

  /**
   * Seed sample reports
   */
  private async seedReports(): Promise<void> {
    const reportsSQL = `
      INSERT INTO reports (id, user_id, type, title, date_from, date_to, data, status, generated_at) VALUES
      ('00000000-0000-0000-0000-000000000501', '00000000-0000-0000-0000-000000000002', 'daily_pnl', 'Daily P&L Report', CURRENT_DATE, CURRENT_DATE, '{"total_pnl": 150.00, "trades": 5, "win_rate": 0.6}', 'completed', NOW()),
      ('00000000-0000-0000-0000-000000000502', '00000000-0000-0000-0000-000000000003', 'monthly_summary', 'Monthly Performance', CURRENT_DATE - INTERVAL '30 days', CURRENT_DATE, '{"monthly_return": 0.08, "sharpe_ratio": 1.2}', 'completed', NOW() - INTERVAL '1 day')
      ON CONFLICT (id) DO NOTHING;
    `;

    await this.executeSQL(reportsSQL);
  }

  /**
   * Create database indexes
   */
  private async createIndexes(): Promise<void> {
    const indexesSQL = `
      -- User indexes
      CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
      CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
      CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);

      -- Portfolio indexes
      CREATE INDEX IF NOT EXISTS idx_portfolios_user_id ON portfolios(user_id);

      -- Strategy indexes
      CREATE INDEX IF NOT EXISTS idx_strategies_user_id ON strategies(user_id);
      CREATE INDEX IF NOT EXISTS idx_strategies_type ON strategies(type);
      CREATE INDEX IF NOT EXISTS idx_strategies_status ON strategies(status);

      -- Order indexes
      CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
      CREATE INDEX IF NOT EXISTS idx_orders_strategy_id ON orders(strategy_id);
      CREATE INDEX IF NOT EXISTS idx_orders_symbol ON orders(symbol);
      CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
      CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);

      -- Position indexes
      CREATE INDEX IF NOT EXISTS idx_positions_user_id ON positions(user_id);
      CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol);
      CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status);

      -- Market data indexes
      CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timestamp ON market_data(symbol, timestamp);
      CREATE INDEX IF NOT EXISTS idx_market_data_timestamp ON market_data(timestamp);

      -- Transaction indexes
      CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
      CREATE INDEX IF NOT EXISTS idx_transactions_portfolio_id ON transactions(portfolio_id);
      CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type);
      CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at);

      -- Report indexes
      CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id);
      CREATE INDEX IF NOT EXISTS idx_reports_type ON reports(type);
      CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);

      -- Audit log indexes
      CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
      CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
      CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
    `;

    await this.executeSQL(indexesSQL);
  }

  /**
   * Setup database triggers
   */
  private async setupTriggers(): Promise<void> {
    const triggersSQL = `
      -- Update timestamp trigger function
      CREATE OR REPLACE FUNCTION update_updated_at_column()
      RETURNS TRIGGER AS $$
      BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
      END;
      $$ language 'plpgsql';

      -- Apply update triggers
      DROP TRIGGER IF EXISTS update_users_updated_at ON users;
      CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

      DROP TRIGGER IF EXISTS update_portfolios_updated_at ON portfolios;
      CREATE TRIGGER update_portfolios_updated_at BEFORE UPDATE ON portfolios FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

      DROP TRIGGER IF EXISTS update_strategies_updated_at ON strategies;
      CREATE TRIGGER update_strategies_updated_at BEFORE UPDATE ON strategies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

      -- Audit trigger function
      CREATE OR REPLACE FUNCTION audit_trigger()
      RETURNS TRIGGER AS $$
      BEGIN
        IF TG_OP = 'INSERT' THEN
          INSERT INTO audit_logs (action, entity_type, entity_id, new_values)
          VALUES (TG_OP, TG_TABLE_NAME, NEW.id, row_to_json(NEW));
          RETURN NEW;
        ELSIF TG_OP = 'UPDATE' THEN
          INSERT INTO audit_logs (action, entity_type, entity_id, old_values, new_values)
          VALUES (TG_OP, TG_TABLE_NAME, NEW.id, row_to_json(OLD), row_to_json(NEW));
          RETURN NEW;
        ELSIF TG_OP = 'DELETE' THEN
          INSERT INTO audit_logs (action, entity_type, entity_id, old_values)
          VALUES (TG_OP, TG_TABLE_NAME, OLD.id, row_to_json(OLD));
          RETURN OLD;
        END IF;
        RETURN NULL;
      END;
      $$ language 'plpgsql';

      -- Apply audit triggers to sensitive tables
      DROP TRIGGER IF EXISTS audit_users ON users;
      CREATE TRIGGER audit_users AFTER INSERT OR UPDATE OR DELETE ON users FOR EACH ROW EXECUTE FUNCTION audit_trigger();

      DROP TRIGGER IF EXISTS audit_orders ON orders;
      CREATE TRIGGER audit_orders AFTER INSERT OR UPDATE OR DELETE ON orders FOR EACH ROW EXECUTE FUNCTION audit_trigger();

      DROP TRIGGER IF EXISTS audit_positions ON positions;
      CREATE TRIGGER audit_positions AFTER INSERT OR UPDATE OR DELETE ON positions FOR EACH ROW EXECUTE FUNCTION audit_trigger();
    `;

    await this.executeSQL(triggersSQL);
  }

  /**
   * Reset database to clean state
   */
  async resetDatabase(): Promise<void> {
    console.log('Resetting test database...');

    const resetSQL = `
      -- Truncate all tables in correct order (respecting foreign keys)
      TRUNCATE TABLE audit_logs CASCADE;
      TRUNCATE TABLE sessions CASCADE;
      TRUNCATE TABLE settings CASCADE;
      TRUNCATE TABLE reports CASCADE;
      TRUNCATE TABLE transactions CASCADE;
      TRUNCATE TABLE market_data CASCADE;
      TRUNCATE TABLE positions CASCADE;
      TRUNCATE TABLE orders CASCADE;
      TRUNCATE TABLE strategies CASCADE;
      TRUNCATE TABLE portfolios CASCADE;
      TRUNCATE TABLE users CASCADE;

      -- Reset sequences if any
      -- (PostgreSQL will auto-handle UUID generation)
    `;

    await this.executeSQL(resetSQL);

    // Re-seed initial data
    await this.seedInitialData();

    console.log('✅ Database reset completed');
  }

  /**
   * Execute SQL commands
   */
  private async executeSQL(sql: string): Promise<void> {
    try {
      await execAsync(`psql "${this.databaseUrl}" -c "${sql.replace(/"/g, '\\"')}"`);
    } catch (error) {
      console.error('SQL execution failed:', error);
      throw error;
    }
  }

  /**
   * Get base price for symbol
   */
  private getBasePrice(symbol: string): number {
    const basePrices: Record<string, number> = {
      'EURUSD': 1.0850,
      'GBPUSD': 1.2500,
      'USDJPY': 149.50,
      'USDCHF': 0.9150,
      'AUDUSD': 0.6750
    };

    return basePrices[symbol] || 1.0000;
  }

  /**
   * Backup current database state
   */
  async backupDatabase(backupName: string): Promise<string> {
    const backupPath = path.join(this.seedsDir, `${backupName}.sql`);

    try {
      await execAsync(`pg_dump "${this.databaseUrl}" > "${backupPath}"`);
      console.log(`✅ Database backed up to ${backupPath}`);
      return backupPath;
    } catch (error) {
      console.error('Database backup failed:', error);
      throw error;
    }
  }

  /**
   * Restore database from backup
   */
  async restoreDatabase(backupPath: string): Promise<void> {
    try {
      // Drop and recreate database
      await this.resetDatabase();

      // Restore from backup
      await execAsync(`psql "${this.databaseUrl}" < "${backupPath}"`);

      console.log(`✅ Database restored from ${backupPath}`);
    } catch (error) {
      console.error('Database restore failed:', error);
      throw error;
    }
  }

  /**
   * Get database statistics
   */
  async getDatabaseStats(): Promise<any> {
    const statsSQL = `
      SELECT
        schemaname,
        tablename,
        n_tup_ins as inserts,
        n_tup_upd as updates,
        n_tup_del as deletes,
        n_live_tup as live_tuples,
        n_dead_tup as dead_tuples
      FROM pg_stat_user_tables
      ORDER BY tablename;
    `;

    try {
      const { stdout } = await execAsync(`psql "${this.databaseUrl}" -t -c "${statsSQL}"`);
      return stdout.trim().split('\n').map(line => {
        const parts = line.trim().split('|').map(p => p.trim());
        return {
          schema: parts[0],
          table: parts[1],
          inserts: parseInt(parts[2]) || 0,
          updates: parseInt(parts[3]) || 0,
          deletes: parseInt(parts[4]) || 0,
          liveTuples: parseInt(parts[5]) || 0,
          deadTuples: parseInt(parts[6]) || 0
        };
      });
    } catch (error) {
      console.error('Failed to get database stats:', error);
      return [];
    }
  }
}