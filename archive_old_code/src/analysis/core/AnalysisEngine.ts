/**
 * Core Analysis Engine - Orchestrates the entire code analysis process
 * Implements hooks integration for Claude Flow coordination
 */

import { EventEmitter } from 'events';
import { promises as fs } from 'fs';
import * as path from 'path';
import { glob } from 'glob';
import chokidar from 'chokidar';
import { ParserManager } from '../parsers/ParserManager';
import { AnalyzerManager } from './AnalyzerManager';
import { DiagramGenerator } from '../generators/DiagramGenerator';
import { CacheManager } from '../cache/CacheManager';
import { HooksIntegration } from '../hooks/HooksIntegration';
import {
  AnalysisConfig,
  AnalysisResult,
  AnalysisGraph,
  CodeElement,
  Relationship,
  Logger,
  AnalysisMetrics,
  TradingSystemMetrics,
  Recommendation
} from '../types';

export class AnalysisEngine extends EventEmitter {
  private parserManager: ParserManager;
  private analyzerManager: AnalyzerManager;
  private diagramGenerator: DiagramGenerator;
  private cacheManager: CacheManager;
  private hooksIntegration: HooksIntegration;
  private config: AnalysisConfig;
  private logger: Logger;
  private isWatching: boolean = false;
  private watcher?: chokidar.FSWatcher;

  constructor(config: AnalysisConfig, logger: Logger) {
    super();
    this.config = config;
    this.logger = logger;

    this.parserManager = new ParserManager(config.parsers, logger);
    this.analyzerManager = new AnalyzerManager(config.analyzers, logger);
    this.diagramGenerator = new DiagramGenerator(logger);
    this.cacheManager = new CacheManager(config.cache, logger);
    this.hooksIntegration = new HooksIntegration(config.hooks, logger);

    this.setupEventHandlers();
  }

  /**
   * Initialize the analysis engine with Claude Flow hooks
   */
  async initialize(): Promise<void> {
    this.logger.info('Initializing Analysis Engine...');

    try {
      // Initialize hooks integration first
      await this.hooksIntegration.initialize();

      // Pre-task hook for coordination
      await this.hooksIntegration.preTask('analysis-engine-initialization');

      // Initialize components
      await this.cacheManager.initialize();
      await this.parserManager.initialize();
      await this.analyzerManager.initialize();
      await this.diagramGenerator.initialize();

      // Store initialization in memory
      await this.hooksIntegration.storeMemory('analysis/engine/status', {
        initialized: true,
        timestamp: new Date().toISOString(),
        config: this.config
      });

      this.logger.info('Analysis Engine initialized successfully');
      this.emit('initialized');

    } catch (error) {
      this.logger.error('Failed to initialize Analysis Engine:', error);
      throw error;
    }
  }

  /**
   * Perform comprehensive analysis of the codebase
   */
  async analyze(targetPath?: string): Promise<AnalysisResult> {
    const startTime = Date.now();
    this.logger.info('Starting comprehensive code analysis...');

    try {
      // Pre-analysis hook
      await this.hooksIntegration.preTask('comprehensive-analysis');

      // Discover files to analyze
      const files = await this.discoverFiles(targetPath);
      this.logger.info(`Discovered ${files.length} files for analysis`);

      // Check cache for recent analysis
      const cacheKey = this.generateCacheKey(files);
      const cachedResult = await this.cacheManager.get<AnalysisResult>(cacheKey);

      if (cachedResult && this.isCacheValid(cachedResult)) {
        this.logger.info('Using cached analysis result');
        return cachedResult;
      }

      // Parse files and build initial graph
      const graph = await this.parseFiles(files);

      // Run analyzers to enhance the graph
      await this.runAnalyzers(graph);

      // Generate diagrams
      const diagrams = await this.diagramGenerator.generateAll(graph);

      // Calculate metrics
      const metrics = this.calculateMetrics(startTime, files.length);

      // Generate recommendations
      const recommendations = await this.generateRecommendations(graph);

      const result: AnalysisResult = {
        graph,
        diagrams,
        metrics,
        recommendations,
        timestamp: new Date()
      };

      // Cache the result
      await this.cacheManager.set(cacheKey, result);

      // Store in Claude Flow memory
      await this.hooksIntegration.storeMemory('analysis/latest-result', {
        timestamp: result.timestamp.toISOString(),
        elementCount: graph.elements.size,
        relationshipCount: graph.relationships.size,
        diagramCount: diagrams.length,
        recommendationCount: recommendations.length
      });

      // Post-analysis hook
      await this.hooksIntegration.postTask('comprehensive-analysis', {
        filesAnalyzed: files.length,
        elementsFound: graph.elements.size,
        relationshipsFound: graph.relationships.size
      });

      this.logger.info(`Analysis completed in ${metrics.parseTime + metrics.analysisTime}ms`);
      this.emit('analysisComplete', result);

      return result;

    } catch (error) {
      this.logger.error('Analysis failed:', error);
      await this.hooksIntegration.notify('Analysis failed: ' + error.message);
      throw error;
    }
  }

  /**
   * Start watching for file changes and perform incremental analysis
   */
  async startWatching(targetPath?: string): Promise<void> {
    if (this.isWatching) {
      this.logger.warn('Already watching for changes');
      return;
    }

    const watchPaths = targetPath ? [targetPath] : this.config.include;

    this.watcher = chokidar.watch(watchPaths, {
      ignored: this.config.exclude,
      persistent: true,
      ignoreInitial: true
    });

    this.watcher
      .on('add', (filePath) => this.handleFileChange('add', filePath))
      .on('change', (filePath) => this.handleFileChange('change', filePath))
      .on('unlink', (filePath) => this.handleFileChange('unlink', filePath));

    this.isWatching = true;
    this.logger.info('Started watching for file changes');

    await this.hooksIntegration.notify('Analysis engine started watching for changes');
  }

  /**
   * Stop watching for file changes
   */
  async stopWatching(): Promise<void> {
    if (this.watcher) {
      await this.watcher.close();
      this.watcher = undefined;
    }
    this.isWatching = false;
    this.logger.info('Stopped watching for file changes');
  }

  /**
   * Perform incremental analysis on a specific file
   */
  async analyzeFile(filePath: string): Promise<void> {
    this.logger.info(`Analyzing file: ${filePath}`);

    try {
      await this.hooksIntegration.preEdit(filePath);

      // Parse the single file
      const elements = await this.parserManager.parseFile(filePath);

      // Update cache and memory
      await this.cacheManager.invalidatePattern(`file:${filePath}*`);
      await this.hooksIntegration.storeMemory(`analysis/files/${filePath}`, {
        lastAnalyzed: new Date().toISOString(),
        elementCount: elements.length
      });

      // Post-edit hook
      await this.hooksIntegration.postEdit(filePath, `analysis/files/${filePath}`);

      this.emit('fileAnalyzed', filePath, elements);

    } catch (error) {
      this.logger.error(`Failed to analyze file ${filePath}:`, error);
      throw error;
    }
  }

  /**
   * Get trading system specific metrics
   */
  async getTradingMetrics(): Promise<TradingSystemMetrics> {
    const cachedMetrics = await this.cacheManager.get<TradingSystemMetrics>('trading-metrics');
    if (cachedMetrics) {
      return cachedMetrics;
    }

    // Calculate trading-specific metrics
    const result = await this.analyze();
    const graph = result.graph;

    const tradingMetrics: TradingSystemMetrics = {
      strategyCount: this.countElementsByPattern(graph, /strategy|trading.*strategy/i),
      riskComponentCount: this.countElementsByPattern(graph, /risk|risk.*management/i),
      apiEndpointCount: this.countElementsByPattern(graph, /endpoint|route|controller/i),
      dataSourceCount: this.countElementsByPattern(graph, /data.*source|feed|stream/i),
      notificationHandlerCount: this.countElementsByPattern(graph, /notification|alert|notify/i),
      complexityScore: this.calculateComplexityScore(graph),
      riskScore: this.calculateRiskScore(graph)
    };

    await this.cacheManager.set('trading-metrics', tradingMetrics, 300); // 5 minute cache
    return tradingMetrics;
  }

  /**
   * Generate analysis summary for reporting
   */
  async generateSummary(): Promise<string> {
    const result = await this.analyze();
    const tradingMetrics = await this.getTradingMetrics();

    return `
# AI Trading System Analysis Summary

## Overview
- **Elements**: ${result.graph.elements.size}
- **Relationships**: ${result.graph.relationships.size}
- **Files Processed**: ${result.metrics.filesProcessed}
- **Analysis Time**: ${result.metrics.parseTime + result.metrics.analysisTime}ms

## Trading System Metrics
- **Trading Strategies**: ${tradingMetrics.strategyCount}
- **Risk Components**: ${tradingMetrics.riskComponentCount}
- **API Endpoints**: ${tradingMetrics.apiEndpointCount}
- **Data Sources**: ${tradingMetrics.dataSourceCount}
- **Notification Handlers**: ${tradingMetrics.notificationHandlerCount}
- **Complexity Score**: ${tradingMetrics.complexityScore.toFixed(2)}
- **Risk Score**: ${tradingMetrics.riskScore.toFixed(2)}

## Recommendations
${result.recommendations.map(r => `- **${r.severity.toUpperCase()}**: ${r.title}`).join('\n')}

## Generated Diagrams
${result.diagrams.map(d => `- ${d.type}: ${d.title} (${d.metadata.elementCount} elements)`).join('\n')}
    `.trim();
  }

  /**
   * Cleanup resources
   */
  async dispose(): Promise<void> {
    await this.stopWatching();
    await this.cacheManager.dispose();
    await this.hooksIntegration.dispose();
    this.removeAllListeners();
    this.logger.info('Analysis Engine disposed');
  }

  // Private methods

  private setupEventHandlers(): void {
    this.on('error', (error) => {
      this.logger.error('Analysis Engine error:', error);
    });
  }

  private async discoverFiles(targetPath?: string): Promise<string[]> {
    const patterns = targetPath ? [targetPath] : this.config.include;
    const files: string[] = [];

    for (const pattern of patterns) {
      const matches = await glob(pattern, {
        ignore: this.config.exclude,
        absolute: true
      });
      files.push(...matches);
    }

    return [...new Set(files)]; // Remove duplicates
  }

  private async parseFiles(files: string[]): Promise<AnalysisGraph> {
    const graph: AnalysisGraph = {
      elements: new Map(),
      relationships: new Map(),
      metadata: {
        projectName: path.basename(process.cwd()),
        analysisDate: new Date(),
        version: '1.0.0',
        filePaths: files,
        statistics: {
          totalElements: 0,
          totalRelationships: 0,
          elementsByType: {} as any,
          relationshipsByType: {} as any,
          cyclomaticComplexity: 0,
          cohesion: 0,
          coupling: 0
        },
        tradingSystemMetrics: {
          strategyCount: 0,
          riskComponentCount: 0,
          apiEndpointCount: 0,
          dataSourceCount: 0,
          notificationHandlerCount: 0,
          complexityScore: 0,
          riskScore: 0
        }
      }
    };

    for (const filePath of files) {
      try {
        const elements = await this.parserManager.parseFile(filePath);
        const relationships = await this.parserManager.extractRelationships(filePath, elements);

        // Add elements to graph
        elements.forEach(element => {
          graph.elements.set(element.id, element);
        });

        // Add relationships to graph
        relationships.forEach(relationship => {
          graph.relationships.set(relationship.id, relationship);
        });

      } catch (error) {
        this.logger.warn(`Failed to parse ${filePath}:`, error);
      }
    }

    // Update statistics
    this.updateGraphStatistics(graph);

    return graph;
  }

  private async runAnalyzers(graph: AnalysisGraph): Promise<void> {
    await this.analyzerManager.analyzeGraph(graph);
  }

  private calculateMetrics(startTime: number, fileCount: number): AnalysisMetrics {
    const totalTime = Date.now() - startTime;

    return {
      parseTime: totalTime * 0.4, // Estimate
      analysisTime: totalTime * 0.4, // Estimate
      diagramGenerationTime: totalTime * 0.2, // Estimate
      cacheHitRate: this.cacheManager.getHitRate(),
      memoryUsage: process.memoryUsage().heapUsed,
      filesProcessed: fileCount,
      errorsCount: 0,
      warningsCount: 0
    };
  }

  private async generateRecommendations(graph: AnalysisGraph): Promise<Recommendation[]> {
    // This would be implemented by specific analyzer modules
    return [];
  }

  private generateCacheKey(files: string[]): string {
    const hash = files.sort().join('|');
    return `analysis:${Buffer.from(hash).toString('base64').slice(0, 16)}`;
  }

  private isCacheValid(result: AnalysisResult): boolean {
    const maxAge = this.config.cache.ttl * 1000;
    return Date.now() - result.timestamp.getTime() < maxAge;
  }

  private async handleFileChange(event: string, filePath: string): Promise<void> {
    if (!this.config.hooks.incremental) {
      return;
    }

    this.logger.debug(`File ${event}: ${filePath}`);

    try {
      await this.analyzeFile(filePath);
      await this.hooksIntegration.notify(`File ${event}: ${path.basename(filePath)}`);
    } catch (error) {
      this.logger.error(`Error handling file change for ${filePath}:`, error);
    }
  }

  private countElementsByPattern(graph: AnalysisGraph, pattern: RegExp): number {
    let count = 0;
    for (const element of graph.elements.values()) {
      if (pattern.test(element.name) || pattern.test(element.type)) {
        count++;
      }
    }
    return count;
  }

  private calculateComplexityScore(graph: AnalysisGraph): number {
    const elementCount = graph.elements.size;
    const relationshipCount = graph.relationships.size;

    if (elementCount === 0) return 0;

    const density = relationshipCount / (elementCount * (elementCount - 1));
    const avgRelationships = relationshipCount / elementCount;

    return (density * 0.4 + avgRelationships * 0.6) * 10;
  }

  private calculateRiskScore(graph: AnalysisGraph): number {
    // Risk score based on coupling, complexity, and trading-specific patterns
    let riskScore = 0;

    // High coupling increases risk
    const avgCoupling = this.calculateAverageCoupling(graph);
    riskScore += avgCoupling * 2;

    // Complex components increase risk
    const complexityFactor = this.calculateComplexityScore(graph) / 10;
    riskScore += complexityFactor * 1.5;

    // Missing error handling in trading components
    const tradingElements = Array.from(graph.elements.values())
      .filter(e => /trading|strategy|risk/i.test(e.name));
    const errorHandlingRatio = this.calculateErrorHandlingRatio(tradingElements);
    riskScore += (1 - errorHandlingRatio) * 3;

    return Math.min(riskScore, 10); // Cap at 10
  }

  private calculateAverageCoupling(graph: AnalysisGraph): number {
    const couplingMap = new Map<string, Set<string>>();

    for (const relationship of graph.relationships.values()) {
      if (!couplingMap.has(relationship.sourceId)) {
        couplingMap.set(relationship.sourceId, new Set());
      }
      couplingMap.get(relationship.sourceId)!.add(relationship.targetId);
    }

    const totalCoupling = Array.from(couplingMap.values())
      .reduce((sum, deps) => sum + deps.size, 0);

    return graph.elements.size > 0 ? totalCoupling / graph.elements.size : 0;
  }

  private calculateErrorHandlingRatio(elements: CodeElement[]): number {
    if (elements.length === 0) return 1;

    const elementsWithErrorHandling = elements.filter(element =>
      /try|catch|error|exception/i.test(JSON.stringify(element.metadata))
    );

    return elementsWithErrorHandling.length / elements.length;
  }

  private updateGraphStatistics(graph: AnalysisGraph): void {
    graph.metadata.statistics.totalElements = graph.elements.size;
    graph.metadata.statistics.totalRelationships = graph.relationships.size;

    // Count by type
    const elementsByType: Record<string, number> = {};
    const relationshipsByType: Record<string, number> = {};

    for (const element of graph.elements.values()) {
      elementsByType[element.type] = (elementsByType[element.type] || 0) + 1;
    }

    for (const relationship of graph.relationships.values()) {
      relationshipsByType[relationship.type] = (relationshipsByType[relationship.type] || 0) + 1;
    }

    graph.metadata.statistics.elementsByType = elementsByType as any;
    graph.metadata.statistics.relationshipsByType = relationshipsByType as any;
    graph.metadata.statistics.coupling = this.calculateAverageCoupling(graph);
  }
}