/**
 * Diagram Generator - Creates Mermaid.js diagrams from analysis graphs
 * Supports multiple diagram types including trading-specific visualizations
 */

import {
  AnalysisGraph,
  CodeElement,
  Relationship,
  DiagramConfig,
  DiagramType,
  GeneratedDiagram,
  DiagramMetadata,
  ElementType,
  RelationshipType,
  GroupingStrategy,
  Logger
} from '../types';

export class DiagramGenerator {
  private readonly mermaidThemes = {
    default: '',
    dark: '%%{init: {"theme": "dark"}}%%',
    forest: '%%{init: {"theme": "forest"}}%%',
    neutral: '%%{init: {"theme": "neutral"}}%%'
  };

  constructor(private logger: Logger) {}

  async initialize(): Promise<void> {
    this.logger.info('Initializing Diagram Generator...');
  }

  async generateAll(graph: AnalysisGraph): Promise<GeneratedDiagram[]> {
    const diagrams: GeneratedDiagram[] = [];

    try {
      // Generate different types of diagrams
      diagrams.push(await this.generateClassDiagram(graph));
      diagrams.push(await this.generateFlowChart(graph));
      diagrams.push(await this.generateTradingFlowDiagram(graph));
      diagrams.push(await this.generateRiskDiagram(graph));
      diagrams.push(await this.generateDataFlowDiagram(graph));
      diagrams.push(await this.generateERDiagram(graph));
      diagrams.push(await this.generateSequenceDiagram(graph));

      this.logger.info(`Generated ${diagrams.length} diagrams`);

    } catch (error) {
      this.logger.error('Failed to generate diagrams:', error);
    }

    return diagrams;
  }

  async generateDiagram(graph: AnalysisGraph, config: DiagramConfig): Promise<GeneratedDiagram> {
    const startTime = Date.now();

    try {
      let content: string;

      switch (config.type) {
        case DiagramType.CLASS_DIAGRAM:
          content = this.generateClassDiagramContent(graph, config);
          break;
        case DiagramType.FLOW_CHART:
          content = this.generateFlowChartContent(graph, config);
          break;
        case DiagramType.TRADING_FLOW:
          content = this.generateTradingFlowContent(graph, config);
          break;
        case DiagramType.RISK_DIAGRAM:
          content = this.generateRiskDiagramContent(graph, config);
          break;
        case DiagramType.DATA_FLOW:
          content = this.generateDataFlowContent(graph, config);
          break;
        case DiagramType.ER_DIAGRAM:
          content = this.generateERDiagramContent(graph, config);
          break;
        case DiagramType.SEQUENCE_DIAGRAM:
          content = this.generateSequenceDiagramContent(graph, config);
          break;
        default:
          throw new Error(`Unsupported diagram type: ${config.type}`);
      }

      const filteredGraph = this.applyFilters(graph, config.filters);
      const metadata = this.calculateDiagramMetadata(filteredGraph, Date.now() - startTime);

      return {
        id: this.generateDiagramId(config),
        type: config.type,
        title: config.title,
        content,
        metadata
      };

    } catch (error) {
      this.logger.error(`Failed to generate ${config.type} diagram:`, error);
      throw error;
    }
  }

  // Specific diagram generators

  private async generateClassDiagram(graph: AnalysisGraph): Promise<GeneratedDiagram> {
    const config: DiagramConfig = {
      type: DiagramType.CLASS_DIAGRAM,
      title: 'AI Trading System - Class Diagram',
      direction: 'TB',
      theme: 'default',
      filters: [],
      groupBy: GroupingStrategy.BY_MODULE,
      showMetrics: true
    };

    return this.generateDiagram(graph, config);
  }

  private async generateFlowChart(graph: AnalysisGraph): Promise<GeneratedDiagram> {
    const config: DiagramConfig = {
      type: DiagramType.FLOW_CHART,
      title: 'AI Trading System - Component Flow',
      direction: 'TD',
      theme: 'default',
      filters: [{ elementTypes: [ElementType.CLASS, ElementType.FUNCTION] }],
      groupBy: GroupingStrategy.BY_LAYER
    };

    return this.generateDiagram(graph, config);
  }

  private async generateTradingFlowDiagram(graph: AnalysisGraph): Promise<GeneratedDiagram> {
    const config: DiagramConfig = {
      type: DiagramType.TRADING_FLOW,
      title: 'Trading System - Execution Flow',
      direction: 'LR',
      theme: 'forest',
      filters: [{
        elementTypes: [ElementType.TRADING_STRATEGY, ElementType.RISK_COMPONENT],
        relationshipTypes: [RelationshipType.STRATEGY_USAGE, RelationshipType.RISK_MONITORING]
      }],
      groupBy: GroupingStrategy.BY_TRADING_COMPONENT
    };

    return this.generateDiagram(graph, config);
  }

  private async generateRiskDiagram(graph: AnalysisGraph): Promise<GeneratedDiagram> {
    const config: DiagramConfig = {
      type: DiagramType.RISK_DIAGRAM,
      title: 'Risk Management - Component Diagram',
      direction: 'TB',
      theme: 'neutral',
      filters: [{
        elementTypes: [ElementType.RISK_COMPONENT],
        relationshipTypes: [RelationshipType.RISK_MONITORING]
      }]
    };

    return this.generateDiagram(graph, config);
  }

  private async generateDataFlowDiagram(graph: AnalysisGraph): Promise<GeneratedDiagram> {
    const config: DiagramConfig = {
      type: DiagramType.DATA_FLOW,
      title: 'Market Data Flow',
      direction: 'LR',
      theme: 'default',
      filters: [{
        relationshipTypes: [RelationshipType.DATA_FLOW, RelationshipType.API_CALL]
      }]
    };

    return this.generateDiagram(graph, config);
  }

  private async generateERDiagram(graph: AnalysisGraph): Promise<GeneratedDiagram> {
    const config: DiagramConfig = {
      type: DiagramType.ER_DIAGRAM,
      title: 'Database Schema',
      theme: 'default',
      filters: [{
        elementTypes: [ElementType.DATABASE_ENTITY],
        relationshipTypes: [RelationshipType.DATABASE_RELATION]
      }]
    };

    return this.generateDiagram(graph, config);
  }

  private async generateSequenceDiagram(graph: AnalysisGraph): Promise<GeneratedDiagram> {
    const config: DiagramConfig = {
      type: DiagramType.SEQUENCE_DIAGRAM,
      title: 'Trading Execution Sequence',
      theme: 'default',
      filters: [{
        relationshipTypes: [RelationshipType.CALLS, RelationshipType.API_CALL]
      }]
    };

    return this.generateDiagram(graph, config);
  }

  // Content generators for each diagram type

  private generateClassDiagramContent(graph: AnalysisGraph, config: DiagramConfig): string {
    const filteredGraph = this.applyFilters(graph, config.filters);
    const theme = this.mermaidThemes[config.theme || 'default'];

    let content = `${theme}\nclassDiagram\n`;

    // Add classes
    const classes = Array.from(filteredGraph.elements.values())
      .filter(e => e.type === ElementType.CLASS || e.type === ElementType.TRADING_STRATEGY || e.type === ElementType.RISK_COMPONENT);

    classes.forEach(cls => {
      content += `    class ${this.sanitizeName(cls.name)} {\n`;

      // Add properties
      if (cls.metadata.properties) {
        cls.metadata.properties.forEach((prop: any) => {
          const visibility = prop.isPrivate ? '-' : prop.isProtected ? '#' : '+';
          content += `        ${visibility}${prop.name} : ${prop.type || 'any'}\n`;
        });
      }

      // Add methods
      if (cls.metadata.methods) {
        cls.metadata.methods.forEach((method: any) => {
          const visibility = method.isPrivate ? '-' : method.isProtected ? '#' : '+';
          const params = method.parameters?.map((p: any) => `${p.name}: ${p.type || 'any'}`).join(', ') || '';
          content += `        ${visibility}${method.name}(${params}) : ${method.returnType || 'void'}\n`;
        });
      }

      content += `    }\n`;

      // Add styling for trading components
      if (cls.type === ElementType.TRADING_STRATEGY) {
        content += `    class ${this.sanitizeName(cls.name)} {\n        <<Strategy>>\n    }\n`;
      } else if (cls.type === ElementType.RISK_COMPONENT) {
        content += `    class ${this.sanitizeName(cls.name)} {\n        <<Risk>>\n    }\n`;
      }
    });

    // Add relationships
    const relationships = Array.from(filteredGraph.relationships.values())
      .filter(r => [RelationshipType.INHERITS, RelationshipType.IMPLEMENTS, RelationshipType.COMPOSITION].includes(r.type));

    relationships.forEach(rel => {
      const source = filteredGraph.elements.get(rel.sourceId);
      const target = filteredGraph.elements.get(rel.targetId);

      if (source && target) {
        const sourceName = this.sanitizeName(source.name);
        const targetName = this.sanitizeName(target.name);

        switch (rel.type) {
          case RelationshipType.INHERITS:
            content += `    ${targetName} <|-- ${sourceName}\n`;
            break;
          case RelationshipType.IMPLEMENTS:
            content += `    ${targetName} <|.. ${sourceName}\n`;
            break;
          case RelationshipType.COMPOSITION:
            content += `    ${sourceName} *-- ${targetName}\n`;
            break;
        }
      }
    });

    return content;
  }

  private generateFlowChartContent(graph: AnalysisGraph, config: DiagramConfig): string {
    const filteredGraph = this.applyFilters(graph, config.filters);
    const theme = this.mermaidThemes[config.theme || 'default'];
    const direction = config.direction || 'TD';

    let content = `${theme}\nflowchart ${direction}\n`;

    // Add nodes
    const elements = Array.from(filteredGraph.elements.values());
    elements.forEach(element => {
      const nodeId = this.sanitizeName(element.name);
      const nodeShape = this.getNodeShape(element.type);
      content += `    ${nodeId}${nodeShape}\n`;
    });

    // Add edges
    const relationships = Array.from(filteredGraph.relationships.values());
    relationships.forEach(rel => {
      const source = filteredGraph.elements.get(rel.sourceId);
      const target = filteredGraph.elements.get(rel.targetId);

      if (source && target) {
        const sourceName = this.sanitizeName(source.name);
        const targetName = this.sanitizeName(target.name);
        const edgeStyle = this.getEdgeStyle(rel.type);

        content += `    ${sourceName} ${edgeStyle} ${targetName}\n`;
      }
    });

    // Add styling
    content += this.addFlowChartStyling();

    return content;
  }

  private generateTradingFlowContent(graph: AnalysisGraph, config: DiagramConfig): string {
    const filteredGraph = this.applyFilters(graph, config.filters);
    const theme = this.mermaidThemes[config.theme || 'default'];

    let content = `${theme}\nflowchart LR\n`;

    // Define trading flow stages
    content += `    subgraph "Market Data"\n`;
    content += `        MD[Market Data Feed]\n`;
    content += `        RT[Real-time Prices]\n`;
    content += `        HIS[Historical Data]\n`;
    content += `    end\n\n`;

    content += `    subgraph "Strategy Engine"\n`;
    const strategies = Array.from(filteredGraph.elements.values())
      .filter(e => e.type === ElementType.TRADING_STRATEGY);

    strategies.forEach(strategy => {
      const strategyId = this.sanitizeName(strategy.name);
      content += `        ${strategyId}[${strategy.name}]\n`;
    });
    content += `    end\n\n`;

    content += `    subgraph "Risk Management"\n`;
    const riskComponents = Array.from(filteredGraph.elements.values())
      .filter(e => e.type === ElementType.RISK_COMPONENT);

    riskComponents.forEach(risk => {
      const riskId = this.sanitizeName(risk.name);
      content += `        ${riskId}[${risk.name}]\n`;
    });
    content += `    end\n\n`;

    content += `    subgraph "Execution"\n`;
    content += `        OE[Order Engine]\n`;
    content += `        EXE[Trade Executor]\n`;
    content += `        BROKER[Broker API]\n`;
    content += `    end\n\n`;

    // Add flow connections
    content += `    MD --> RT\n`;
    content += `    RT --> ${strategies.map(s => this.sanitizeName(s.name)).join('\n    RT --> ')}\n`;

    strategies.forEach(strategy => {
      const strategyId = this.sanitizeName(strategy.name);
      content += `    ${strategyId} --> OE\n`;
      riskComponents.forEach(risk => {
        content += `    ${strategyId} --> ${this.sanitizeName(risk.name)}\n`;
      });
    });

    content += `    OE --> EXE\n`;
    content += `    EXE --> BROKER\n`;

    return content;
  }

  private generateRiskDiagramContent(graph: AnalysisGraph, config: DiagramConfig): string {
    const filteredGraph = this.applyFilters(graph, config.filters);
    const theme = this.mermaidThemes[config.theme || 'default'];

    let content = `${theme}\nflowchart TB\n`;

    const riskComponents = Array.from(filteredGraph.elements.values())
      .filter(e => e.type === ElementType.RISK_COMPONENT);

    content += `    subgraph "Risk Monitoring"\n`;
    riskComponents.forEach(risk => {
      const riskId = this.sanitizeName(risk.name);
      const riskLevel = risk.metadata.riskLevel || 'medium';
      content += `        ${riskId}[${risk.name}]:::${riskLevel}Risk\n`;
    });
    content += `    end\n\n`;

    // Add risk connections
    const riskRelationships = Array.from(filteredGraph.relationships.values())
      .filter(r => r.type === RelationshipType.RISK_MONITORING);

    riskRelationships.forEach(rel => {
      const source = filteredGraph.elements.get(rel.sourceId);
      const target = filteredGraph.elements.get(rel.targetId);

      if (source && target) {
        content += `    ${this.sanitizeName(source.name)} -.-> ${this.sanitizeName(target.name)}\n`;
      }
    });

    // Add risk level styling
    content += `\n    classDef highRisk fill:#ff6b6b,stroke:#d63031,color:#fff\n`;
    content += `    classDef mediumRisk fill:#fdcb6e,stroke:#e17055,color:#000\n`;
    content += `    classDef lowRisk fill:#00b894,stroke:#00a085,color:#fff\n`;

    return content;
  }

  private generateDataFlowContent(graph: AnalysisGraph, config: DiagramConfig): string {
    const filteredGraph = this.applyFilters(graph, config.filters);
    const theme = this.mermaidThemes[config.theme || 'default'];

    let content = `${theme}\nflowchart LR\n`;

    // Find data sources
    const dataSources = Array.from(filteredGraph.elements.values())
      .filter(e => e.metadata.tradingCategory === 'market_data' || e.metadata.dataFlowType === 'stream');

    // Find data consumers
    const dataConsumers = Array.from(filteredGraph.elements.values())
      .filter(e => e.metadata.tradingCategory === 'strategy' || e.type === ElementType.TRADING_STRATEGY);

    content += `    subgraph "Data Sources"\n`;
    dataSources.forEach(source => {
      content += `        ${this.sanitizeName(source.name)}[(${source.name})]\n`;
    });
    content += `    end\n\n`;

    content += `    subgraph "Data Consumers"\n`;
    dataConsumers.forEach(consumer => {
      content += `        ${this.sanitizeName(consumer.name)}[${consumer.name}]\n`;
    });
    content += `    end\n\n`;

    // Add data flow relationships
    const dataFlowRels = Array.from(filteredGraph.relationships.values())
      .filter(r => r.type === RelationshipType.DATA_FLOW);

    dataFlowRels.forEach(rel => {
      const source = filteredGraph.elements.get(rel.sourceId);
      const target = filteredGraph.elements.get(rel.targetId);

      if (source && target) {
        content += `    ${this.sanitizeName(source.name)} -->|data| ${this.sanitizeName(target.name)}\n`;
      }
    });

    return content;
  }

  private generateERDiagramContent(graph: AnalysisGraph, config: DiagramConfig): string {
    const filteredGraph = this.applyFilters(graph, config.filters);
    const theme = this.mermaidThemes[config.theme || 'default'];

    let content = `${theme}\nerDiagram\n`;

    const entities = Array.from(filteredGraph.elements.values())
      .filter(e => e.type === ElementType.DATABASE_ENTITY);

    entities.forEach(entity => {
      content += `    ${this.sanitizeName(entity.name)} {\n`;

      if (entity.metadata.columns) {
        entity.metadata.columns.forEach((column: any) => {
          const type = column.type || 'string';
          const constraint = column.primaryKey ? 'PK' : column.foreignKey ? 'FK' : '';
          content += `        ${type} ${column.name} ${constraint}\n`;
        });
      }

      content += `    }\n`;
    });

    // Add relationships
    const dbRelationships = Array.from(filteredGraph.relationships.values())
      .filter(r => r.type === RelationshipType.DATABASE_RELATION);

    dbRelationships.forEach(rel => {
      const source = filteredGraph.elements.get(rel.sourceId);
      const target = filteredGraph.elements.get(rel.targetId);

      if (source && target) {
        content += `    ${this.sanitizeName(source.name)} ||--o{ ${this.sanitizeName(target.name)} : "has"\n`;
      }
    });

    return content;
  }

  private generateSequenceDiagramContent(graph: AnalysisGraph, config: DiagramConfig): string {
    const filteredGraph = this.applyFilters(graph, config.filters);
    const theme = this.mermaidThemes[config.theme || 'default'];

    let content = `${theme}\nsequenceDiagram\n`;

    // Find main actors
    const actors = Array.from(filteredGraph.elements.values())
      .filter(e => e.type === ElementType.CLASS || e.type === ElementType.TRADING_STRATEGY)
      .slice(0, 5); // Limit to avoid clutter

    actors.forEach(actor => {
      content += `    participant ${this.sanitizeName(actor.name)}\n`;
    });

    content += `\n`;

    // Add interactions based on call relationships
    const callRelationships = Array.from(filteredGraph.relationships.values())
      .filter(r => r.type === RelationshipType.CALLS || r.type === RelationshipType.API_CALL);

    callRelationships.slice(0, 10).forEach(rel => { // Limit to avoid clutter
      const source = filteredGraph.elements.get(rel.sourceId);
      const target = filteredGraph.elements.get(rel.targetId);

      if (source && target && actors.includes(source) && actors.includes(target)) {
        const action = rel.type === RelationshipType.API_CALL ? 'API call' : 'method call';
        content += `    ${this.sanitizeName(source.name)}->>+${this.sanitizeName(target.name)}: ${action}\n`;
        content += `    ${this.sanitizeName(target.name)}-->>-${this.sanitizeName(source.name)}: response\n`;
      }
    });

    return content;
  }

  // Helper methods

  private applyFilters(graph: AnalysisGraph, filters: any[]): AnalysisGraph {
    if (!filters || filters.length === 0) {
      return graph;
    }

    const filteredElements = new Map();
    const filteredRelationships = new Map();

    for (const element of graph.elements.values()) {
      if (this.elementMatchesFilters(element, filters)) {
        filteredElements.set(element.id, element);
      }
    }

    for (const relationship of graph.relationships.values()) {
      if (this.relationshipMatchesFilters(relationship, filters) &&
          filteredElements.has(relationship.sourceId) &&
          filteredElements.has(relationship.targetId)) {
        filteredRelationships.set(relationship.id, relationship);
      }
    }

    return {
      elements: filteredElements,
      relationships: filteredRelationships,
      metadata: graph.metadata
    };
  }

  private elementMatchesFilters(element: CodeElement, filters: any[]): boolean {
    return filters.every(filter => {
      if (filter.elementTypes && !filter.elementTypes.includes(element.type)) {
        return false;
      }
      if (filter.filePatterns && !filter.filePatterns.some((pattern: string) =>
        element.filePath.includes(pattern))) {
        return false;
      }
      if (filter.complexity) {
        const complexity = element.metadata.complexity || 0;
        if (filter.complexity.min && complexity < filter.complexity.min) return false;
        if (filter.complexity.max && complexity > filter.complexity.max) return false;
      }
      return true;
    });
  }

  private relationshipMatchesFilters(relationship: Relationship, filters: any[]): boolean {
    return filters.every(filter => {
      if (filter.relationshipTypes && !filter.relationshipTypes.includes(relationship.type)) {
        return false;
      }
      return true;
    });
  }

  private sanitizeName(name: string): string {
    return name.replace(/[^a-zA-Z0-9_]/g, '_');
  }

  private getNodeShape(elementType: ElementType): string {
    switch (elementType) {
      case ElementType.CLASS:
      case ElementType.TRADING_STRATEGY:
        return '[' + elementType + ']';
      case ElementType.INTERFACE:
        return '(' + elementType + ')';
      case ElementType.FUNCTION:
        return '[[' + elementType + ']]';
      case ElementType.DATABASE_ENTITY:
        return '[(Database)]';
      case ElementType.API_ENDPOINT:
        return '{{API}}';
      case ElementType.RISK_COMPONENT:
        return '{Risk}';
      default:
        return '[' + elementType + ']';
    }
  }

  private getEdgeStyle(relationshipType: RelationshipType): string {
    switch (relationshipType) {
      case RelationshipType.INHERITS:
        return '---|>';
      case RelationshipType.IMPLEMENTS:
        return '-..->';
      case RelationshipType.CALLS:
        return '-->';
      case RelationshipType.DATA_FLOW:
        return '==>';
      case RelationshipType.API_CALL:
        return '-.->';
      case RelationshipType.RISK_MONITORING:
        return '-.->|monitors|';
      default:
        return '-->';
    }
  }

  private addFlowChartStyling(): string {
    return `
    classDef strategy fill:#e1f5fe,stroke:#0288d1,color:#000
    classDef risk fill:#fff3e0,stroke:#ff9800,color:#000
    classDef data fill:#f3e5f5,stroke:#9c27b0,color:#000
    classDef api fill:#e8f5e8,stroke:#4caf50,color:#000
    `;
  }

  private calculateDiagramMetadata(graph: AnalysisGraph, renderTime: number): DiagramMetadata {
    return {
      elementCount: graph.elements.size,
      relationshipCount: graph.relationships.size,
      complexity: this.calculateDiagramComplexity(graph),
      renderTime,
      estimatedSize: this.estimateDiagramSize(graph)
    };
  }

  private calculateDiagramComplexity(graph: AnalysisGraph): number {
    const elementCount = graph.elements.size;
    const relationshipCount = graph.relationships.size;

    if (elementCount === 0) return 0;

    return (relationshipCount / elementCount) * 10;
  }

  private estimateDiagramSize(graph: AnalysisGraph): string {
    const totalItems = graph.elements.size + graph.relationships.size;

    if (totalItems < 10) return 'small';
    if (totalItems < 50) return 'medium';
    if (totalItems < 100) return 'large';
    return 'very large';
  }

  private generateDiagramId(config: DiagramConfig): string {
    const timestamp = Date.now();
    const typePrefix = config.type.replace(/([A-Z])/g, '-$1').toLowerCase();
    return `${typePrefix}-${timestamp}`;
  }
}