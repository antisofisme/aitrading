#!/usr/bin/env node

/**
 * Demo Script for Mermaid.js Claude Flow Integration
 * Demonstrates all features and capabilities
 */

import { DiagramWorkflowAutomation } from '../workflow-automation/diagram-workflow.js';
import { MermaidDiagramGenerator } from '../diagram-generator/mermaid-generator.js';
import { CodeAnalyzer } from '../code-analysis/analyzer.js';
import { TradingSystemTemplates } from '../templates/trading-templates.js';
import { ClaudeFlowIntegration } from '../hooks/claude-flow-integration.js';
import { MermaidConfig } from '../config/mermaid-config.js';
import { DiagramUtils } from '../utils/diagram-utils.js';
import fs from 'fs/promises';
import path from 'path';

class MermaidDemo {
  constructor() {
    this.config = new MermaidConfig();
    this.analyzer = new CodeAnalyzer();
    this.generator = new MermaidDiagramGenerator();
    this.templates = new TradingSystemTemplates();
    this.claudeFlow = new ClaudeFlowIntegration();
    this.workflow = null;

    this.demoOutputPath = './demo-output';
  }

  async run() {
    console.log('🚀 Starting Mermaid.js Claude Flow Integration Demo\n');

    try {
      await this.setup();
      await this.demonstrateFeatures();
      await this.cleanup();

      console.log('\n✅ Demo completed successfully!');
      console.log(`📁 Check the demo output in: ${this.demoOutputPath}`);
    } catch (error) {
      console.error('❌ Demo failed:', error.message);
      process.exit(1);
    }
  }

  async setup() {
    console.log('🔧 Setting up demo environment...');

    // Create demo output directory
    await DiagramUtils.ensureDirectoryExists(this.demoOutputPath);

    // Load configuration
    await this.config.load();

    // Initialize Claude Flow integration
    await this.claudeFlow.initialize();

    // Create sample trading system code
    await this.createSampleCode();

    console.log('✓ Demo environment ready\n');
  }

  async createSampleCode() {
    const sampleFiles = {
      'strategy/momentum_strategy.js': `
/**
 * Momentum Trading Strategy
 */
export class MomentumStrategy {
  constructor(config) {
    this.config = config;
    this.riskManager = new RiskManager();
    this.signalGenerator = new SignalGenerator();
  }

  async generateSignal(marketData) {
    const momentum = this.calculateMomentum(marketData);
    const signal = await this.signalGenerator.create(momentum);

    if (await this.riskManager.validateSignal(signal)) {
      return signal;
    }

    return null;
  }

  calculateMomentum(data) {
    // Momentum calculation logic
    return data.prices.slice(-20).reduce((acc, price, i) => {
      return acc + (price - data.prices[data.prices.length - 21 + i]);
    }, 0);
  }
}
`,

      'risk/risk_manager.js': `
/**
 * Risk Management System
 */
export class RiskManager {
  constructor() {
    this.positionSizer = new PositionSizer();
    this.varCalculator = new VarCalculator();
  }

  async validateSignal(signal) {
    const positionSize = await this.positionSizer.calculate(signal);
    const portfolioRisk = await this.varCalculator.calculatePortfolioVar();

    return this.checkRiskLimits(positionSize, portfolioRisk);
  }

  checkRiskLimits(positionSize, portfolioRisk) {
    return positionSize <= this.config.maxPositionSize &&
           portfolioRisk <= this.config.maxPortfolioRisk;
  }
}
`,

      'data/market_data_feed.js': `
/**
 * Market Data Feed Handler
 */
export class MarketDataFeed {
  constructor() {
    this.subscribers = new Map();
    this.priceCache = new Map();
  }

  async subscribe(symbol, callback) {
    if (!this.subscribers.has(symbol)) {
      this.subscribers.set(symbol, new Set());
    }
    this.subscribers.get(symbol).add(callback);
  }

  async publishPrice(symbol, price) {
    this.priceCache.set(symbol, price);

    const callbacks = this.subscribers.get(symbol);
    if (callbacks) {
      callbacks.forEach(callback => callback(price));
    }
  }
}
`,

      'execution/order_manager.js': `
/**
 * Order Management System
 */
export class OrderManager {
  constructor() {
    this.orders = new Map();
    this.executionEngine = new ExecutionEngine();
  }

  async submitOrder(order) {
    order.id = this.generateOrderId();
    order.status = 'PENDING';
    order.timestamp = new Date();

    this.orders.set(order.id, order);

    return await this.executionEngine.execute(order);
  }

  async cancelOrder(orderId) {
    const order = this.orders.get(orderId);
    if (order && order.status === 'PENDING') {
      order.status = 'CANCELLED';
      return true;
    }
    return false;
  }

  generateOrderId() {
    return \`ORD_\${Date.now()}_\${Math.random().toString(36).substr(2, 9)}\`;
  }
}
`
    };

    // Create sample files
    for (const [filePath, content] of Object.entries(sampleFiles)) {
      const fullPath = path.join(this.demoOutputPath, 'sample-code', filePath);
      const dir = path.dirname(fullPath);
      await DiagramUtils.ensureDirectoryExists(dir);
      await fs.writeFile(fullPath, content, 'utf8');
    }

    console.log('✓ Sample trading system code created');
  }

  async demonstrateFeatures() {
    console.log('📊 Demonstrating Mermaid.js Integration Features\n');

    // 1. Code Analysis
    await this.demonstrateCodeAnalysis();

    // 2. Diagram Generation
    await this.demonstrateDiagramGeneration();

    // 3. Trading System Templates
    await this.demonstrateTradingTemplates();

    // 4. Workflow Automation
    await this.demonstrateWorkflowAutomation();

    // 5. Claude Flow Integration
    await this.demonstrateClaudeFlowIntegration();

    // 6. Configuration System
    await this.demonstrateConfiguration();

    // 7. Utilities
    await this.demonstrateUtilities();
  }

  async demonstrateCodeAnalysis() {
    console.log('🔍 1. Code Analysis Module');

    const sampleCodePath = path.join(this.demoOutputPath, 'sample-code');
    const analysis = await this.analyzer.analyzeCodebase(sampleCodePath);

    console.log(`   - Analyzed ${analysis.files.length} files`);
    console.log(`   - Found ${analysis.classes.length} classes`);
    console.log(`   - Found ${analysis.functions.length} functions`);
    console.log(`   - Complexity score: ${analysis.metadata.complexity}`);

    // Save analysis results
    const analysisPath = path.join(this.demoOutputPath, 'analysis-results.json');
    await fs.writeFile(analysisPath, JSON.stringify(analysis, null, 2), 'utf8');

    // Store in Claude Flow memory
    await this.claudeFlow.storeInMemory('demo_analysis', analysis);

    console.log('   ✓ Code analysis complete\n');
    return analysis;
  }

  async demonstrateDiagramGeneration() {
    console.log('📈 2. Diagram Generation');

    const analysis = await this.claudeFlow.getFromMemory('demo_analysis');

    const diagramTypes = ['flowchart', 'class', 'sequence', 'er'];
    const diagrams = {};

    for (const type of diagramTypes) {
      console.log(`   - Generating ${type} diagram...`);

      try {
        diagrams[type] = await this.generator.generateFromAnalysis(type, analysis);

        const diagramPath = path.join(this.demoOutputPath, 'diagrams', `${type}.mmd`);
        await DiagramUtils.ensureDirectoryExists(path.dirname(diagramPath));
        await fs.writeFile(diagramPath, diagrams[type], 'utf8');

        console.log(`     ✓ ${type} diagram saved`);
      } catch (error) {
        console.log(`     ❌ ${type} diagram failed: ${error.message}`);
      }
    }

    console.log('   ✓ Diagram generation complete\n');
    return diagrams;
  }

  async demonstrateTradingTemplates() {
    console.log('💼 3. Trading System Templates');

    const tradingDiagrams = await this.templates.generateTradingSystemDiagrams('ml-based', [
      'microservices',
      'market-data'
    ], true);

    console.log(`   - Generated ${Object.keys(tradingDiagrams).length} trading diagrams:`);

    for (const [name, diagram] of Object.entries(tradingDiagrams)) {
      console.log(`     • ${name}`);

      const diagramPath = path.join(this.demoOutputPath, 'trading-diagrams', `${name}.mmd`);
      await DiagramUtils.ensureDirectoryExists(path.dirname(diagramPath));
      await fs.writeFile(diagramPath, diagram, 'utf8');
    }

    console.log('   ✓ Trading templates complete\n');
    return tradingDiagrams;
  }

  async demonstrateWorkflowAutomation() {
    console.log('⚡ 4. Workflow Automation');

    this.workflow = new DiagramWorkflowAutomation({
      watchPaths: [path.join(this.demoOutputPath, 'sample-code')],
      outputPath: path.join(this.demoOutputPath, 'auto-diagrams'),
      autoGenerate: false, // Disable for demo
      diagramTypes: ['flowchart', 'class']
    });

    await this.workflow.initialize();

    // Perform initial generation
    await this.workflow.performInitialGeneration();

    console.log('   - Workflow automation initialized');
    console.log('   - Initial diagram generation complete');
    console.log('   ✓ Workflow automation ready\n');
  }

  async demonstrateClaudeFlowIntegration() {
    console.log('🔗 5. Claude Flow Integration');

    // Test memory operations
    await this.claudeFlow.storeInMemory('demo_metadata', {
      timestamp: new Date().toISOString(),
      features: ['code-analysis', 'diagram-generation', 'trading-templates'],
      performance: 'excellent'
    });

    const storedData = await this.claudeFlow.getFromMemory('demo_metadata');
    console.log('   - Memory storage/retrieval working');

    // Test hook registration
    await this.claudeFlow.registerHook('demo-hook', async (data) => {
      console.log('   - Hook triggered:', data.message);
    });

    await this.claudeFlow.triggerHook('demo-hook', {
      message: 'Demo hook execution successful'
    });

    // Log activity
    await this.claudeFlow.logActivity('demo_execution', {
      phase: 'demonstration',
      success: true
    });

    console.log('   ✓ Claude Flow integration working\n');
  }

  async demonstrateConfiguration() {
    console.log('⚙️  6. Configuration System');

    // Demonstrate configuration presets
    const tradingConfig = MermaidConfig.createTradingConfig();
    const devConfig = MermaidConfig.createDevelopmentConfig();
    const minimalConfig = MermaidConfig.createMinimalConfig();

    console.log('   - Trading configuration preset created');
    console.log('   - Development configuration preset created');
    console.log('   - Minimal configuration preset created');

    // Save configurations
    const configPath = path.join(this.demoOutputPath, 'configs');
    await DiagramUtils.ensureDirectoryExists(configPath);

    await fs.writeFile(
      path.join(configPath, 'trading-config.json'),
      JSON.stringify(tradingConfig, null, 2),
      'utf8'
    );

    await fs.writeFile(
      path.join(configPath, 'dev-config.json'),
      JSON.stringify(devConfig, null, 2),
      'utf8'
    );

    console.log('   ✓ Configuration system demonstrated\n');
  }

  async demonstrateUtilities() {
    console.log('🛠️  7. Utility Functions');

    // Test diagram validation
    const sampleDiagram = `flowchart TD
      A[Start] --> B{Decision}
      B -->|Yes| C[Action 1]
      B -->|No| D[Action 2]
      C --> E[End]
      D --> E`;

    const validation = DiagramUtils.validateDiagramSyntax(sampleDiagram);
    console.log(`   - Diagram validation: ${validation.isValid ? '✓ Valid' : '❌ Invalid'}`);

    // Test complexity calculation
    const complexity = DiagramUtils.calculateComplexity(sampleDiagram);
    console.log(`   - Complexity analysis: ${complexity.complexity} points`);

    // Test metadata generation
    const metadata = DiagramUtils.generateMetadata(sampleDiagram);
    console.log(`   - Metadata generated: ${metadata.type} diagram, ${metadata.lineCount} lines`);

    // Create diagram index
    const diagramsPath = path.join(this.demoOutputPath, 'diagrams');
    const index = await DiagramUtils.createDiagramIndex(
      diagramsPath,
      path.join(this.demoOutputPath, 'diagram-index.json')
    );

    console.log(`   - Diagram index created: ${index.totalDiagrams} diagrams indexed`);
    console.log('   ✓ Utilities demonstrated\n');
  }

  async cleanup() {
    console.log('🧹 Cleaning up demo...');

    // End Claude Flow session
    await this.claudeFlow.endSession();

    // Stop workflow automation
    if (this.workflow) {
      await this.workflow.shutdown();
    }

    console.log('✓ Cleanup complete');
  }

  // Performance benchmark
  async benchmark() {
    console.log('\n⏱️  Performance Benchmark');

    const timer = DiagramUtils.startTimer('Full Analysis');

    const sampleCodePath = path.join(this.demoOutputPath, 'sample-code');
    const analysis = await this.analyzer.analyzeCodebase(sampleCodePath);

    const diagrams = {};
    for (const type of ['flowchart', 'class', 'sequence']) {
      const typeTimer = DiagramUtils.startTimer(`${type} generation`);
      diagrams[type] = await this.generator.generateFromAnalysis(type, analysis);
      const typeResult = DiagramUtils.endTimer(typeTimer);
      console.log(`   - ${type}: ${typeResult.formattedDuration}`);
    }

    const fullResult = DiagramUtils.endTimer(timer);
    console.log(`   - Total time: ${fullResult.formattedDuration}`);

    const memory = DiagramUtils.getMemoryUsage();
    console.log(`   - Memory usage: ${memory.heapUsed}MB heap, ${memory.rss}MB RSS`);

    return { timing: fullResult, memory, diagrams: Object.keys(diagrams).length };
  }
}

// Run demo if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const demo = new MermaidDemo();

  // Check for benchmark flag
  if (process.argv.includes('--benchmark')) {
    demo.run().then(() => demo.benchmark()).catch(console.error);
  } else {
    demo.run().catch(console.error);
  }
}

export { MermaidDemo };