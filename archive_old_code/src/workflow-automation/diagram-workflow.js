/**
 * Visual Documentation Workflow Automation
 * Automates the generation and updating of architecture diagrams
 */

import { EventEmitter } from 'events';
import fs from 'fs/promises';
import path from 'path';
import chokidar from 'chokidar';
import { CodeAnalyzer } from '../code-analysis/analyzer.js';
import { MermaidDiagramGenerator } from '../diagram-generator/mermaid-generator.js';
import { TradingSystemTemplates } from '../templates/trading-templates.js';
import { ClaudeFlowIntegration } from '../hooks/claude-flow-integration.js';

export class DiagramWorkflowAutomation extends EventEmitter {
  constructor(config = {}) {
    super();

    this.config = {
      watchPaths: config.watchPaths || ['./src'],
      outputPath: config.outputPath || './docs/diagrams',
      autoGenerate: config.autoGenerate !== false,
      debounceDelay: config.debounceDelay || 2000,
      diagramTypes: config.diagramTypes || ['flowchart', 'class', 'sequence'],
      ...config
    };

    this.analyzer = new CodeAnalyzer();
    this.generator = new MermaidDiagramGenerator();
    this.templates = new TradingSystemTemplates();
    this.claudeFlow = new ClaudeFlowIntegration();

    this.watchers = new Map();
    this.debounceTimers = new Map();
    this.lastAnalysis = null;
    this.isProcessing = false;
  }

  async initialize() {
    // Create output directory
    await fs.mkdir(this.config.outputPath, { recursive: true });

    // Initialize Claude Flow integration
    await this.claudeFlow.initialize();

    // Setup event handlers
    this.setupEventHandlers();

    // Perform initial analysis and diagram generation
    await this.performInitialGeneration();

    // Start file watching if auto-generation is enabled
    if (this.config.autoGenerate) {
      await this.startWatching();
    }

    this.emit('initialized');
  }

  setupEventHandlers() {
    // Handle Claude Flow hooks
    this.claudeFlow.on('file-changed', (data) => {
      this.handleFileChange(data.filePath);
    });

    this.claudeFlow.on('pre-task', async (data) => {
      await this.storeWorkflowState('pre-task', data);
    });

    this.claudeFlow.on('post-task', async (data) => {
      await this.updateDiagramsAfterTask(data);
    });

    // Handle internal events
    this.on('analysis-complete', (analysis) => {
      this.emit('diagrams-generating', { analysis });
    });

    this.on('diagrams-complete', (diagrams) => {
      this.emit('workflow-complete', { diagrams });
    });
  }

  async performInitialGeneration() {
    console.log('Performing initial diagram generation...');

    try {
      // Analyze all watched paths
      const analysis = await this.analyzeAllPaths();

      // Generate all diagram types
      const diagrams = await this.generateAllDiagrams(analysis);

      // Save diagrams
      await this.saveDiagrams(diagrams);

      // Store in Claude Flow memory
      await this.claudeFlow.storeInMemory('initial_diagrams', {
        analysis,
        diagrams,
        timestamp: new Date().toISOString()
      });

      this.lastAnalysis = analysis;
      this.emit('diagrams-complete', diagrams);

      console.log(`Generated ${Object.keys(diagrams).length} diagrams`);
    } catch (error) {
      console.error('Failed to perform initial generation:', error);
      this.emit('error', error);
    }
  }

  async analyzeAllPaths() {
    const combinedAnalysis = {
      files: [],
      classes: [],
      functions: [],
      dependencies: [],
      relationships: [],
      imports: [],
      exports: [],
      metadata: {
        totalFiles: 0,
        totalLines: 0,
        languages: {},
        complexity: 0,
        paths: this.config.watchPaths,
        timestamp: new Date().toISOString()
      }
    };

    for (const watchPath of this.config.watchPaths) {
      try {
        const analysis = await this.analyzer.analyzeCodebase(
          watchPath,
          ['**/*.{js,ts,jsx,tsx,py,java,cs}'],
          ['node_modules/**', '.git/**', 'dist/**', 'build/**']
        );

        // Merge analyses
        combinedAnalysis.files.push(...analysis.files);
        combinedAnalysis.classes.push(...analysis.classes);
        combinedAnalysis.functions.push(...analysis.functions);
        combinedAnalysis.dependencies.push(...analysis.dependencies);
        combinedAnalysis.relationships.push(...analysis.relationships);
        combinedAnalysis.imports.push(...analysis.imports);
        combinedAnalysis.exports.push(...analysis.exports);

        combinedAnalysis.metadata.totalFiles += analysis.metadata.totalFiles;
        combinedAnalysis.metadata.totalLines += analysis.metadata.totalLines;
        combinedAnalysis.metadata.complexity += analysis.metadata.complexity;

        // Merge language counts
        Object.entries(analysis.metadata.languages).forEach(([lang, count]) => {
          combinedAnalysis.metadata.languages[lang] =
            (combinedAnalysis.metadata.languages[lang] || 0) + count;
        });

      } catch (error) {
        console.warn(`Failed to analyze path ${watchPath}:`, error.message);
      }
    }

    this.emit('analysis-complete', combinedAnalysis);
    return combinedAnalysis;
  }

  async generateAllDiagrams(analysis) {
    const diagrams = {};

    // Generate standard diagrams
    for (const diagramType of this.config.diagramTypes) {
      try {
        diagrams[diagramType] = await this.generator.generateFromAnalysis(diagramType, analysis);
      } catch (error) {
        console.warn(`Failed to generate ${diagramType} diagram:`, error.message);
      }
    }

    // Generate trading-specific diagrams if this is a trading system
    if (this.isTradingSystem(analysis)) {
      const tradingDiagrams = await this.generateTradingDiagrams(analysis);
      Object.assign(diagrams, tradingDiagrams);
    }

    return diagrams;
  }

  async generateTradingDiagrams(analysis) {
    const tradingDiagrams = {};

    try {
      // Data flow diagram
      tradingDiagrams['trading-data-flow'] = await this.templates.generateDataFlowDiagram(analysis);

      // Risk management flow
      tradingDiagrams['risk-management'] = await this.templates.generateRiskManagementDiagram(analysis);

      // Trading pipeline
      tradingDiagrams['trading-pipeline'] = await this.templates.generateTradingPipelineDiagram(analysis);

      // System architecture
      tradingDiagrams['system-architecture'] = await this.templates.generateSystemArchitectureDiagram(analysis);

    } catch (error) {
      console.warn('Failed to generate trading diagrams:', error.message);
    }

    return tradingDiagrams;
  }

  async saveDiagrams(diagrams) {
    const savedFiles = [];

    for (const [name, definition] of Object.entries(diagrams)) {
      try {
        const fileName = `${name}.mmd`;
        const filePath = path.join(this.config.outputPath, fileName);

        await fs.writeFile(filePath, definition, 'utf8');
        savedFiles.push(filePath);

        // Also generate markdown documentation
        const docFileName = `${name}.md`;
        const docFilePath = path.join(this.config.outputPath, docFileName);
        const docContent = this.generateDiagramDocumentation(name, definition);

        await fs.writeFile(docFilePath, docContent, 'utf8');
        savedFiles.push(docFilePath);

      } catch (error) {
        console.warn(`Failed to save diagram ${name}:`, error.message);
      }
    }

    return savedFiles;
  }

  generateDiagramDocumentation(name, definition) {
    const title = name.split('-').map(word =>
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');

    return `# ${title}

**Auto-generated on:** ${new Date().toISOString()}

**Source:** Automatic code analysis

## Diagram

\`\`\`mermaid
${definition}
\`\`\`

## Description

This diagram was automatically generated from the codebase analysis. It represents the ${name.replace('-', ' ')} structure of the system.

---

*This documentation is automatically updated when code changes. Do not edit manually.*
`;
  }

  async startWatching() {
    for (const watchPath of this.config.watchPaths) {
      const watcher = chokidar.watch(watchPath, {
        ignored: /node_modules|\.git|dist|build/,
        persistent: true,
        ignoreInitial: true
      });

      watcher.on('change', (filePath) => this.handleFileChange(filePath));
      watcher.on('add', (filePath) => this.handleFileChange(filePath));
      watcher.on('unlink', (filePath) => this.handleFileChange(filePath));

      this.watchers.set(watchPath, watcher);
    }

    console.log(`Started watching ${this.config.watchPaths.length} paths for changes`);
  }

  handleFileChange(filePath) {
    if (this.isProcessing) {
      return; // Avoid concurrent processing
    }

    // Debounce rapid file changes
    const timerId = this.debounceTimers.get(filePath);
    if (timerId) {
      clearTimeout(timerId);
    }

    this.debounceTimers.set(filePath, setTimeout(async () => {
      await this.processFileChange(filePath);
      this.debounceTimers.delete(filePath);
    }, this.config.debounceDelay));
  }

  async processFileChange(filePath) {
    if (this.isProcessing) return;

    this.isProcessing = true;

    try {
      console.log(`Processing file change: ${filePath}`);

      // Re-analyze affected paths
      const analysis = await this.analyzeAllPaths();

      // Check if analysis significantly changed
      if (this.hasSignificantChanges(analysis)) {
        // Regenerate diagrams
        const diagrams = await this.generateAllDiagrams(analysis);

        // Save updated diagrams
        await this.saveDiagrams(diagrams);

        // Update Claude Flow memory
        await this.claudeFlow.storeInMemory('updated_diagrams', {
          trigger: 'file-change',
          filePath,
          analysis,
          diagrams,
          timestamp: new Date().toISOString()
        });

        this.lastAnalysis = analysis;
        this.emit('diagrams-updated', { filePath, diagrams });

        console.log(`Updated diagrams due to changes in ${filePath}`);
      }

    } catch (error) {
      console.error(`Failed to process file change ${filePath}:`, error);
      this.emit('error', error);
    } finally {
      this.isProcessing = false;
    }
  }

  hasSignificantChanges(newAnalysis) {
    if (!this.lastAnalysis) return true;

    // Compare key metrics
    const oldMetrics = this.lastAnalysis.metadata;
    const newMetrics = newAnalysis.metadata;

    return (
      Math.abs(oldMetrics.totalFiles - newMetrics.totalFiles) > 0 ||
      Math.abs(oldMetrics.complexity - newMetrics.complexity) > 5 ||
      this.lastAnalysis.classes.length !== newAnalysis.classes.length ||
      this.lastAnalysis.functions.length !== newAnalysis.functions.length
    );
  }

  async updateDiagramsAfterTask(taskData) {
    // Trigger diagram update after significant tasks
    if (taskData.type === 'code-generation' || taskData.type === 'refactoring') {
      await this.performInitialGeneration();
    }
  }

  async storeWorkflowState(event, data) {
    await this.claudeFlow.storeInMemory(`workflow_${event}`, {
      event,
      data,
      timestamp: new Date().toISOString()
    });
  }

  isTradingSystem(analysis) {
    const tradingKeywords = ['trade', 'strategy', 'market', 'risk', 'portfolio', 'order', 'signal'];
    const codeText = JSON.stringify(analysis).toLowerCase();
    return tradingKeywords.some(keyword => codeText.includes(keyword));
  }

  async stopWatching() {
    for (const [path, watcher] of this.watchers) {
      await watcher.close();
      console.log(`Stopped watching ${path}`);
    }
    this.watchers.clear();
  }

  async shutdown() {
    await this.stopWatching();

    // Clear debounce timers
    for (const [filePath, timerId] of this.debounceTimers) {
      clearTimeout(timerId);
    }
    this.debounceTimers.clear();

    this.emit('shutdown');
  }

  // Manual trigger methods
  async regenerateAllDiagrams() {
    await this.performInitialGeneration();
  }

  async generateDiagramForFile(filePath) {
    try {
      const analysis = await this.analyzer.analyzeCode(
        await fs.readFile(filePath, 'utf8'),
        filePath
      );

      const diagrams = await this.generateAllDiagrams(analysis);
      return diagrams;
    } catch (error) {
      throw new Error(`Failed to generate diagram for ${filePath}: ${error.message}`);
    }
  }

  // Configuration methods
  updateConfig(newConfig) {
    Object.assign(this.config, newConfig);
    this.emit('config-updated', this.config);
  }

  getConfig() {
    return { ...this.config };
  }

  getStatus() {
    return {
      isProcessing: this.isProcessing,
      watchedPaths: this.config.watchPaths,
      watchersCount: this.watchers.size,
      lastAnalysis: this.lastAnalysis?.metadata || null,
      config: this.config
    };
  }
}