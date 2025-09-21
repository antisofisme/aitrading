#!/usr/bin/env node

/**
 * Ecosystem Setup Script
 * Quick setup and testing script for the collaborative documentation ecosystem
 */

const path = require('path');
const { execSync } = require('child_process');

// Import the ecosystem
const {
  createEcosystem,
  startEcosystem,
  setupAiTradingEcosystem,
  stopEcosystem
} = require('./src/ecosystem');

async function main() {
  try {
    console.log('🎯 Setting up Collaborative Documentation Ecosystem...');
    console.log('📁 Project:', process.cwd());

    // Check if this is an AI trading project
    const isAiTrading = await detectAiTradingProject();

    if (isAiTrading) {
      console.log('🤖 AI Trading project detected, using specialized setup...');

      // Setup AI trading ecosystem
      const ecosystem = await setupAiTradingEcosystem();

      // Start the ecosystem
      await ecosystem.start();

      console.log('✅ AI Trading ecosystem is now running');
      console.log('📊 Monitoring:', ecosystem.getStatus());

      // Simulate some changes for testing
      await simulateAiTradingChanges(ecosystem);

    } else {
      console.log('📝 Setting up general documentation ecosystem...');

      // Setup general ecosystem
      const ecosystem = await createEcosystem();
      await ecosystem.start();

      console.log('✅ General ecosystem is now running');
      console.log('📊 Status:', ecosystem.getStatus());
    }

    // Keep running for demonstration
    console.log('🔄 Ecosystem is running. Press Ctrl+C to stop.');

    process.on('SIGINT', async () => {
      console.log('\n⏹️ Stopping ecosystem...');
      await stopEcosystem();
      console.log('✅ Ecosystem stopped successfully');
      process.exit(0);
    });

  } catch (error) {
    console.error('❌ Setup failed:', error);
    process.exit(1);
  }
}

/**
 * Detect if this is an AI trading project
 */
async function detectAiTradingProject() {
  const fs = require('fs').promises;

  try {
    // Check package.json for trading dependencies
    const packagePath = path.join(process.cwd(), 'package.json');
    if (await fileExists(packagePath)) {
      const packageContent = await fs.readFile(packagePath, 'utf8');
      const packageJson = JSON.parse(packageContent);

      const deps = { ...packageJson.dependencies, ...packageJson.devDependencies };
      const tradingLibs = ['ccxt', 'binance', 'alpaca', 'trading', 'strategy'];

      if (tradingLibs.some(lib => Object.keys(deps).some(dep => dep.includes(lib)))) {
        return true;
      }
    }

    // Check for trading-related directories
    const items = await fs.readdir(process.cwd());
    const tradingDirs = ['strategies', 'algorithms', 'trading', 'indicators'];

    return tradingDirs.some(dir => items.includes(dir));

  } catch (error) {
    console.warn('⚠️ Could not detect project type:', error.message);
    return false;
  }
}

/**
 * Simulate AI trading changes for testing
 */
async function simulateAiTradingChanges(ecosystem) {
  const fs = require('fs').promises;

  console.log('🧪 Simulating AI trading changes for testing...');

  // Create a sample strategy file
  const strategyDir = path.join(process.cwd(), 'src', 'strategies');
  await fs.mkdir(strategyDir, { recursive: true });

  const strategyContent = `
/**
 * Sample Moving Average Strategy
 * Demonstrates automated documentation generation
 */

class MovingAverageStrategy {
  constructor(shortPeriod = 10, longPeriod = 20) {
    this.shortPeriod = shortPeriod;
    this.longPeriod = longPeriod;
    this.positions = [];
  }

  /**
   * Calculate moving average
   * @param {number[]} prices - Array of prices
   * @param {number} period - Period for MA calculation
   * @returns {number} Moving average value
   */
  calculateMA(prices, period) {
    if (prices.length < period) return null;

    const sum = prices.slice(-period).reduce((a, b) => a + b, 0);
    return sum / period;
  }

  /**
   * Generate trading signal
   * @param {number[]} prices - Historical prices
   * @returns {string} 'BUY', 'SELL', or 'HOLD'
   */
  generateSignal(prices) {
    const shortMA = this.calculateMA(prices, this.shortPeriod);
    const longMA = this.calculateMA(prices, this.longPeriod);

    if (!shortMA || !longMA) return 'HOLD';

    if (shortMA > longMA) return 'BUY';
    if (shortMA < longMA) return 'SELL';
    return 'HOLD';
  }

  /**
   * Execute strategy
   * @param {Object} marketData - Current market data
   * @returns {Object} Trading decision
   */
  execute(marketData) {
    const signal = this.generateSignal(marketData.prices);

    return {
      signal,
      timestamp: new Date().toISOString(),
      price: marketData.currentPrice,
      strategy: 'MovingAverage',
      parameters: {
        shortPeriod: this.shortPeriod,
        longPeriod: this.longPeriod
      }
    };
  }
}

module.exports = MovingAverageStrategy;
`;

  const strategyPath = path.join(strategyDir, 'MovingAverageStrategy.js');
  await fs.writeFile(strategyPath, strategyContent, 'utf8');

  console.log(`📝 Created sample strategy: ${strategyPath}`);

  // Wait a moment for the ecosystem to detect the change
  await new Promise(resolve => setTimeout(resolve, 2000));

  // Create an API endpoint
  const apiDir = path.join(process.cwd(), 'src', 'api');
  await fs.mkdir(apiDir, { recursive: true });

  const apiContent = `
/**
 * Trading API Routes
 * RESTful endpoints for trading operations
 */

const express = require('express');
const router = express.Router();
const MovingAverageStrategy = require('../strategies/MovingAverageStrategy');

/**
 * @route GET /api/strategies
 * @desc Get available trading strategies
 * @access Public
 */
router.get('/strategies', (req, res) => {
  res.json({
    strategies: [
      {
        name: 'MovingAverage',
        description: 'Moving Average Crossover Strategy',
        parameters: ['shortPeriod', 'longPeriod']
      }
    ]
  });
});

/**
 * @route POST /api/signals
 * @desc Generate trading signal
 * @access Public
 */
router.post('/signals', (req, res) => {
  try {
    const { strategy, marketData, parameters } = req.body;

    if (strategy === 'MovingAverage') {
      const ma = new MovingAverageStrategy(
        parameters?.shortPeriod,
        parameters?.longPeriod
      );

      const result = ma.execute(marketData);
      res.json(result);
    } else {
      res.status(400).json({ error: 'Unknown strategy' });
    }
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;
`;

  const apiPath = path.join(apiDir, 'trading.js');
  await fs.writeFile(apiPath, apiContent, 'utf8');

  console.log(`🔗 Created sample API: ${apiPath}`);

  // Wait for ecosystem to process
  await new Promise(resolve => setTimeout(resolve, 3000));

  console.log('✅ Test simulation completed');
}

/**
 * Utility function to check if file exists
 */
async function fileExists(filePath) {
  const fs = require('fs').promises;
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

// Run the setup if called directly
if (require.main === module) {
  main();
}

module.exports = { main, detectAiTradingProject, simulateAiTradingChanges };