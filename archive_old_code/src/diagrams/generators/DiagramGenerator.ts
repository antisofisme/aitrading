import { DiagramTemplate } from '../templates/DiagramTemplate';
import {
  DiagramType,
  AnalysisData,
  DiagramOptions,
  TemplateContext,
  DiagramNode,
  DiagramRelationship
} from '../core/types';

export abstract class DiagramGenerator {
  abstract readonly type: DiagramType;
  abstract readonly template: DiagramTemplate;

  /**
   * Generate diagram from analysis data
   */
  async generate(analysisData: AnalysisData, options?: DiagramOptions): Promise<string> {
    // Convert analysis data to template context
    const context = await this.transformToContext(analysisData, options);

    // Validate context for this generator
    if (!this.template.validate(context)) {
      throw new Error(`Invalid context for ${this.type} diagram generation`);
    }

    // Generate the diagram
    return await this.template.generate(context);
  }

  /**
   * Transform analysis data into template context
   */
  protected abstract transformToContext(
    analysisData: AnalysisData,
    options?: DiagramOptions
  ): Promise<TemplateContext>;

  /**
   * Extract nodes from analysis data
   */
  protected extractNodes(analysisData: AnalysisData): DiagramNode[] {
    // Use explicit nodes if available
    if (analysisData.nodes) {
      return analysisData.nodes;
    }

    // Extract nodes from structure or content
    return this.inferNodesFromContent(analysisData);
  }

  /**
   * Extract relationships from analysis data
   */
  protected extractRelationships(analysisData: AnalysisData): DiagramRelationship[] {
    // Use explicit relationships if available
    if (analysisData.relationships) {
      return analysisData.relationships;
    }

    // Infer relationships from structure
    return this.inferRelationshipsFromContent(analysisData);
  }

  /**
   * Infer nodes from content when not explicitly provided
   */
  protected inferNodesFromContent(analysisData: AnalysisData): DiagramNode[] {
    const { structure, metadata } = analysisData;
    const nodes: DiagramNode[] = [];

    // Extract from structure array
    structure.forEach((item, index) => {
      nodes.push({
        id: `node_${index}`,
        label: item,
        type: this.inferNodeType(item, metadata),
        properties: {}
      });
    });

    // Extract from metadata entities
    if (metadata?.entities) {
      metadata.entities.forEach((entity: any) => {
        nodes.push({
          id: entity.id || entity.name,
          label: entity.name || entity.label,
          type: entity.type || 'entity',
          properties: entity.properties || {}
        });
      });
    }

    return nodes;
  }

  /**
   * Infer relationships from content when not explicitly provided
   */
  protected inferRelationshipsFromContent(analysisData: AnalysisData): DiagramRelationship[] {
    const relationships: DiagramRelationship[] = [];
    const { metadata } = analysisData;

    // Extract from metadata connections
    if (metadata?.connections) {
      metadata.connections.forEach((connection: any, index: number) => {
        relationships.push({
          id: `rel_${index}`,
          source: connection.from || connection.source,
          target: connection.to || connection.target,
          type: connection.type || 'connects',
          label: connection.label,
          properties: connection.properties || {}
        });
      });
    }

    // Infer relationships from patterns in structure
    const nodes = this.extractNodes(analysisData);
    const inferredRelationships = this.inferRelationshipPatterns(nodes, analysisData);
    relationships.push(...inferredRelationships);

    return relationships;
  }

  /**
   * Infer node type from content
   */
  protected inferNodeType(content: string, metadata?: any): string {
    const contentLower = content.toLowerCase();

    // Database/Storage patterns
    if (contentLower.includes('table') || contentLower.includes('database')) {
      return 'database';
    }

    // API patterns
    if (contentLower.includes('api') || contentLower.includes('endpoint')) {
      return 'api';
    }

    // Service patterns
    if (contentLower.includes('service') || contentLower.includes('microservice')) {
      return 'service';
    }

    // UI patterns
    if (contentLower.includes('ui') || contentLower.includes('frontend') || contentLower.includes('component')) {
      return 'frontend';
    }

    // User patterns
    if (contentLower.includes('user') || contentLower.includes('actor')) {
      return 'user';
    }

    // Trading-specific patterns
    if (contentLower.includes('trading') || contentLower.includes('trade')) {
      return 'trading-engine';
    }

    if (contentLower.includes('order') || contentLower.includes('execution')) {
      return 'order-management';
    }

    if (contentLower.includes('market') || contentLower.includes('price')) {
      return 'market-data';
    }

    if (contentLower.includes('portfolio') || contentLower.includes('position')) {
      return 'portfolio';
    }

    // Default
    return 'system';
  }

  /**
   * Infer relationship patterns between nodes
   */
  protected inferRelationshipPatterns(
    nodes: DiagramNode[],
    analysisData: AnalysisData
  ): DiagramRelationship[] {
    const relationships: DiagramRelationship[] = [];

    // Create relationships based on common patterns
    for (let i = 0; i < nodes.length - 1; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const relationship = this.inferRelationshipBetweenNodes(nodes[i], nodes[j], analysisData);
        if (relationship) {
          relationships.push(relationship);
        }
      }
    }

    return relationships;
  }

  /**
   * Infer relationship between two specific nodes
   */
  protected inferRelationshipBetweenNodes(
    nodeA: DiagramNode,
    nodeB: DiagramNode,
    analysisData: AnalysisData
  ): DiagramRelationship | null {
    const typeA = nodeA.type;
    const typeB = nodeB.type;

    // User -> System relationships
    if (typeA === 'user' && typeB !== 'user') {
      return {
        id: `${nodeA.id}_uses_${nodeB.id}`,
        source: nodeA.id,
        target: nodeB.id,
        type: 'uses',
        label: 'uses'
      };
    }

    // API -> Service relationships
    if (typeA === 'api' && typeB === 'service') {
      return {
        id: `${nodeA.id}_calls_${nodeB.id}`,
        source: nodeA.id,
        target: nodeB.id,
        type: 'calls',
        label: 'calls'
      };
    }

    // Service -> Database relationships
    if (typeA === 'service' && typeB === 'database') {
      return {
        id: `${nodeA.id}_reads_${nodeB.id}`,
        source: nodeA.id,
        target: nodeB.id,
        type: 'reads',
        label: 'reads/writes'
      };
    }

    // Frontend -> API relationships
    if (typeA === 'frontend' && typeB === 'api') {
      return {
        id: `${nodeA.id}_calls_${nodeB.id}`,
        source: nodeA.id,
        target: nodeB.id,
        type: 'calls',
        label: 'calls'
      };
    }

    // Trading-specific relationships
    if (typeA === 'trading-engine' && typeB === 'market-data') {
      return {
        id: `${nodeA.id}_consumes_${nodeB.id}`,
        source: nodeA.id,
        target: nodeB.id,
        type: 'consumes',
        label: 'consumes market data'
      };
    }

    if (typeA === 'order-management' && typeB === 'trading-engine') {
      return {
        id: `${nodeA.id}_sends_${nodeB.id}`,
        source: nodeA.id,
        target: nodeB.id,
        type: 'sends',
        label: 'sends orders'
      };
    }

    // No clear relationship found
    return null;
  }

  /**
   * Apply generator-specific optimizations
   */
  protected optimizeForDiagramType(context: TemplateContext): TemplateContext {
    return context;
  }

  /**
   * Validate if analysis data is suitable for this generator
   */
  canGenerate(analysisData: AnalysisData): boolean {
    try {
      const context = this.transformToContext(analysisData);
      return this.template.validate(context as TemplateContext);
    } catch {
      return false;
    }
  }

  /**
   * Get complexity score for the diagram
   */
  getComplexityScore(analysisData: AnalysisData): number {
    const nodeCount = analysisData.nodes?.length || this.extractNodes(analysisData).length;
    const relationshipCount = analysisData.relationships?.length || 0;

    // Simple scoring algorithm
    let complexity = 0;
    complexity += nodeCount * 0.1;
    complexity += relationshipCount * 0.15;

    // Normalize to 0-1 scale
    return Math.min(1, complexity / 10);
  }

  /**
   * Get estimated rendering time in milliseconds
   */
  getEstimatedRenderTime(analysisData: AnalysisData): number {
    const complexity = this.getComplexityScore(analysisData);
    const baseTime = 100; // Base rendering time in ms

    return baseTime + (complexity * 2000); // Scale up to 2 seconds for complex diagrams
  }
}