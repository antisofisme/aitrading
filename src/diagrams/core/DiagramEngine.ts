import mermaid from 'mermaid';
import { DiagramTemplate } from '../templates/DiagramTemplate';
import { DiagramGenerator } from '../generators/DiagramGenerator';
import { OutputFormatter } from '../formats/OutputFormatter';
import { ThemeManager } from '../themes/ThemeManager';
import { MCPIntegration } from '../mcp/MCPIntegration';
import {
  DiagramType,
  DiagramConfig,
  GenerationResult,
  OutputFormat,
  AnalysisData,
  DiagramOptions
} from './types';

export class DiagramEngine {
  private mermaidInstance: typeof mermaid;
  private templates: Map<DiagramType, DiagramTemplate>;
  private generators: Map<DiagramType, DiagramGenerator>;
  private formatter: OutputFormatter;
  private themeManager: ThemeManager;
  private mcpIntegration: MCPIntegration;
  private initialized: boolean = false;

  constructor(config?: DiagramConfig) {
    this.mermaidInstance = mermaid;
    this.templates = new Map();
    this.generators = new Map();
    this.formatter = new OutputFormatter();
    this.themeManager = new ThemeManager(config?.themes);
    this.mcpIntegration = new MCPIntegration();

    this.initialize(config);
  }

  /**
   * Initialize the diagram engine with Mermaid configuration
   */
  private async initialize(config?: DiagramConfig): Promise<void> {
    if (this.initialized) return;

    // Configure Mermaid with optimized settings
    this.mermaidInstance.initialize({
      startOnLoad: false,
      theme: config?.defaultTheme || 'default',
      themeVariables: this.themeManager.getThemeVariables(),
      flowchart: {
        useMaxWidth: false,
        htmlLabels: true,
        curve: 'basis'
      },
      sequence: {
        diagramMarginX: 50,
        diagramMarginY: 10,
        actorMargin: 50,
        width: 150,
        height: 65,
        boxMargin: 10,
        boxTextMargin: 5,
        noteMargin: 10,
        messageMargin: 35
      },
      gantt: {
        titleTopMargin: 25,
        barHeight: 20,
        gridLineStartPadding: 35,
        fontSize: 11,
        fontFamily: '"Open Sans", sans-serif'
      },
      journey: {
        diagramMarginX: 50,
        diagramMarginY: 10,
        leftMargin: 150,
        width: 150,
        height: 50,
        boxMargin: 10,
        boxTextMargin: 5,
        noteMargin: 10,
        messageMargin: 35
      }
    });

    // Load templates and generators
    await this.loadTemplates();
    await this.loadGenerators();

    // Initialize MCP integration
    await this.mcpIntegration.initialize();

    this.initialized = true;
  }

  /**
   * Generate diagram from analysis data
   */
  async generateDiagram(
    analysisData: AnalysisData,
    diagramType: DiagramType,
    options?: DiagramOptions
  ): Promise<GenerationResult> {
    await this.initialize();

    try {
      // Get appropriate generator
      const generator = this.generators.get(diagramType);
      if (!generator) {
        throw new Error(`No generator found for diagram type: ${diagramType}`);
      }

      // Apply theme if specified
      if (options?.theme) {
        await this.themeManager.applyTheme(options.theme);
      }

      // Generate Mermaid code
      const mermaidCode = await generator.generate(analysisData, options);

      // Validate Mermaid syntax
      const isValid = await this.validateMermaidSyntax(mermaidCode);
      if (!isValid) {
        throw new Error('Generated Mermaid code is invalid');
      }

      // Generate outputs in requested formats
      const outputs = await this.generateOutputs(mermaidCode, options?.formats || ['svg']);

      // Store in MCP memory for coordination
      await this.mcpIntegration.storeDiagramResult({
        type: diagramType,
        mermaidCode,
        outputs,
        metadata: {
          generatedAt: new Date().toISOString(),
          analysisData: analysisData.id,
          options
        }
      });

      return {
        success: true,
        diagramType,
        mermaidCode,
        outputs,
        metadata: {
          generatedAt: new Date().toISOString(),
          performance: await this.getPerformanceMetrics()
        }
      };

    } catch (error) {
      console.error('Diagram generation failed:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        diagramType
      };
    }
  }

  /**
   * Generate multiple diagrams in batch
   */
  async generateBatch(
    requests: Array<{
      analysisData: AnalysisData;
      diagramType: DiagramType;
      options?: DiagramOptions;
    }>
  ): Promise<GenerationResult[]> {
    await this.initialize();

    // Use Promise.allSettled for parallel generation
    const results = await Promise.allSettled(
      requests.map(request =>
        this.generateDiagram(request.analysisData, request.diagramType, request.options)
      )
    );

    return results.map(result =>
      result.status === 'fulfilled' ? result.value : {
        success: false,
        error: result.reason?.message || 'Generation failed',
        diagramType: 'unknown' as DiagramType
      }
    );
  }

  /**
   * Auto-select diagram type based on analysis data
   */
  async autoSelectDiagramType(analysisData: AnalysisData): Promise<DiagramType> {
    const { contentType, structure, complexity } = analysisData;

    // Algorithm to select best diagram type
    if (contentType === 'system-architecture') {
      return complexity > 0.7 ? 'component-graph' : 'system-architecture';
    }

    if (contentType === 'workflow' || contentType === 'trading-sequence') {
      return 'sequence-diagram';
    }

    if (contentType === 'database' || structure.includes('table')) {
      return 'er-diagram';
    }

    if (contentType === 'user-journey' || contentType === 'process-flow') {
      return 'user-journey';
    }

    // Default fallback
    return 'component-graph';
  }

  /**
   * Generate optimized layout suggestions
   */
  async optimizeLayout(
    diagramType: DiagramType,
    analysisData: AnalysisData
  ): Promise<DiagramOptions> {
    const baseOptions: DiagramOptions = {};

    // Analyze data complexity for layout optimization
    const nodeCount = analysisData.nodes?.length || 0;
    const relationshipCount = analysisData.relationships?.length || 0;

    if (nodeCount > 20) {
      baseOptions.layout = {
        direction: 'TB',
        spacing: 'compact',
        grouping: 'clustered'
      };
    } else if (relationshipCount > nodeCount * 1.5) {
      baseOptions.layout = {
        direction: 'LR',
        spacing: 'wide',
        grouping: 'hierarchical'
      };
    }

    // Color coding based on component types
    baseOptions.colorScheme = this.generateColorScheme(analysisData);

    return baseOptions;
  }

  /**
   * Validate Mermaid syntax
   */
  private async validateMermaidSyntax(mermaidCode: string): Promise<boolean> {
    try {
      await this.mermaidInstance.parse(mermaidCode);
      return true;
    } catch (error) {
      console.error('Mermaid syntax validation failed:', error);
      return false;
    }
  }

  /**
   * Generate outputs in multiple formats
   */
  private async generateOutputs(
    mermaidCode: string,
    formats: OutputFormat[]
  ): Promise<Record<OutputFormat, string | Buffer>> {
    const outputs: Record<OutputFormat, string | Buffer> = {};

    for (const format of formats) {
      try {
        outputs[format] = await this.formatter.convert(mermaidCode, format);
      } catch (error) {
        console.error(`Failed to generate ${format} output:`, error);
        // Continue with other formats
      }
    }

    return outputs;
  }

  /**
   * Generate color scheme based on analysis data
   */
  private generateColorScheme(analysisData: AnalysisData): Record<string, string> {
    const scheme: Record<string, string> = {};

    // Component type color mapping
    const colorMap = {
      'api': '#4CAF50',
      'database': '#2196F3',
      'frontend': '#FF9800',
      'backend': '#9C27B0',
      'service': '#607D8B',
      'external': '#F44336',
      'user': '#00BCD4',
      'system': '#795548'
    };

    analysisData.nodes?.forEach(node => {
      const type = node.type || 'system';
      scheme[node.id] = colorMap[type] || '#757575';
    });

    return scheme;
  }

  /**
   * Load all diagram templates
   */
  private async loadTemplates(): Promise<void> {
    // Implementation will be completed with template files
    // Templates will be loaded dynamically
  }

  /**
   * Load all diagram generators
   */
  private async loadGenerators(): Promise<void> {
    // Implementation will be completed with generator files
    // Generators will be loaded dynamically
  }

  /**
   * Get performance metrics
   */
  private async getPerformanceMetrics(): Promise<Record<string, number>> {
    return {
      memoryUsage: process.memoryUsage().heapUsed,
      timestamp: Date.now()
    };
  }

  /**
   * Register file change hooks for auto-regeneration
   */
  async registerFileWatcher(
    filePath: string,
    diagramType: DiagramType,
    options?: DiagramOptions
  ): Promise<void> {
    await this.mcpIntegration.registerFileWatcher(filePath, diagramType, options);
  }

  /**
   * Clean up resources
   */
  async dispose(): Promise<void> {
    await this.mcpIntegration.dispose();
  }
}