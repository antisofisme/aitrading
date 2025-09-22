import { DiagramTemplate } from './DiagramTemplate';
import { DiagramType, TemplateContext, DiagramNode, DiagramRelationship } from '../core/types';

export class SystemArchitectureTemplate extends DiagramTemplate {
  readonly type: DiagramType = 'system-architecture';
  readonly name = 'System Architecture';
  readonly description = 'Generate system architecture diagrams showing components and their relationships';

  async generate(context: TemplateContext): Promise<string> {
    const { nodes, relationships, options } = this.preprocess(context);

    const direction = this.optimizeLayout(context);
    let mermaidCode = `graph ${direction}\n`;

    // Generate nodes with proper styling
    const nodeDefinitions = this.generateNodes(nodes);
    mermaidCode += nodeDefinitions;

    // Generate relationships
    const relationshipDefinitions = this.generateRelationships(relationships);
    mermaidCode += relationshipDefinitions;

    // Add subgraphs for logical grouping
    const subgraphs = this.generateSubgraphs(nodes);
    mermaidCode += subgraphs;

    // Apply styling
    const styling = this.generateStyling(nodes, options);
    mermaidCode += styling;

    // Add click events for interactivity
    const clickEvents = this.generateClickEvents(nodes, options);
    mermaidCode += clickEvents;

    return this.applyTheme(mermaidCode, options);
  }

  validate(context: TemplateContext): boolean {
    const { nodes, relationships } = context;

    // Must have at least 2 nodes
    if (!nodes || nodes.length < 2) return false;

    // Must have at least 1 relationship
    if (!relationships || relationships.length < 1) return false;

    // All relationships must reference valid nodes
    const nodeIds = new Set(nodes.map(n => n.id));
    return relationships.every(rel =>
      nodeIds.has(rel.source) && nodeIds.has(rel.target)
    );
  }

  getVariables(): string[] {
    return [
      'direction',
      'groupByType',
      'showLabels',
      'includeMetadata',
      'colorScheme',
      'nodeShape',
      'edgeStyle'
    ];
  }

  private generateNodes(nodes: DiagramNode[]): string {
    return nodes.map(node => {
      const nodeId = this.generateNodeId(node.id);
      const label = this.escapeLabel(node.label);
      const shape = this.getNodeShape(node.type);

      return `    ${nodeId}${shape.start}"${label}"${shape.end}`;
    }).join('\n') + '\n';
  }

  private generateRelationships(relationships: DiagramRelationship[]): string {
    return relationships.map(rel => {
      const sourceId = this.generateNodeId(rel.source);
      const targetId = this.generateNodeId(rel.target);
      const arrow = this.getArrowStyle(rel.type);
      const label = rel.label ? `|${this.escapeLabel(rel.label)}|` : '';

      return `    ${sourceId} ${arrow}${label} ${targetId}`;
    }).join('\n') + '\n';
  }

  private generateSubgraphs(nodes: DiagramNode[]): string {
    // Group nodes by type or layer
    const groups = this.groupNodesByType(nodes);

    return Object.entries(groups).map(([groupType, groupNodes]) => {
      if (groupNodes.length < 2) return ''; // Don't create subgraph for single nodes

      const groupId = this.generateNodeId(`group_${groupType}`);
      const groupLabel = this.formatGroupLabel(groupType);

      return this.generateSubgraph(groupId, groupLabel, groupNodes);
    }).filter(Boolean).join('\n');
  }

  private generateStyling(nodes: DiagramNode[], options: any): string {
    let styling = '\n';

    // Apply color scheme
    if (options.colorScheme) {
      nodes.forEach(node => {
        const nodeId = this.generateNodeId(node.id);
        const color = options.colorScheme[node.type] || options.colorScheme[node.id];
        if (color) {
          styling += `    style ${nodeId} fill:${color}\n`;
        }
      });
    }

    // Apply custom node styles
    nodes.forEach(node => {
      if (node.style) {
        const nodeId = this.generateNodeId(node.id);
        styling += this.applyNodeStyling(nodeId, node.style);
      }
    });

    return styling;
  }

  private getNodeShape(nodeType: string): { start: string; end: string } {
    const shapes = {
      'api': { start: '[', end: ']' },
      'database': { start: '[(', end: ')]' },
      'service': { start: '(', end: ')' },
      'external': { start: '{{', end: '}}' },
      'user': { start: '((', end: '))' },
      'queue': { start: '>>', end: '>>>' },
      'cache': { start: '[/', end: '/]' },
      'storage': { start: '[\\', end: '\\]' },
      'gateway': { start: '{', end: '}' },
      'microservice': { start: '(', end: ')' },
      'frontend': { start: '[', end: ']' },
      'backend': { start: '[[', end: ']]' }
    };

    return shapes[nodeType] || { start: '[', end: ']' };
  }

  private getArrowStyle(relationshipType: string): string {
    const arrows = {
      'depends': '-->',
      'calls': '-->',
      'uses': '-.->',
      'contains': '==>',
      'inherits': '-.->',
      'implements': '-.->',
      'communicates': '<-->',
      'publishes': '-->',
      'subscribes': '<--',
      'synchronous': '-->',
      'asynchronous': '-.->',
      'dataflow': '==>',
      'controlflow': '-->',
      'triggers': '-.->',
      'includes': '-->'
    };

    return arrows[relationshipType] || '-->';
  }

  private groupNodesByType(nodes: DiagramNode[]): Record<string, DiagramNode[]> {
    return nodes.reduce((groups, node) => {
      const type = node.type || 'other';
      if (!groups[type]) groups[type] = [];
      groups[type].push(node);
      return groups;
    }, {} as Record<string, DiagramNode[]>);
  }

  private formatGroupLabel(groupType: string): string {
    // Convert snake_case or camelCase to Title Case
    return groupType
      .replace(/[_-]/g, ' ')
      .replace(/([a-z])([A-Z])/g, '$1 $2')
      .replace(/\b\w/g, l => l.toUpperCase());
  }

  protected preprocess(context: TemplateContext): TemplateContext {
    // Add trading-specific node types if not present
    const processedNodes = context.nodes.map(node => {
      if (!node.type && node.label.toLowerCase().includes('trading')) {
        return { ...node, type: 'trading-engine' };
      }
      if (!node.type && node.label.toLowerCase().includes('market')) {
        return { ...node, type: 'market-data' };
      }
      if (!node.type && node.label.toLowerCase().includes('order')) {
        return { ...node, type: 'order-management' };
      }
      return node;
    });

    return {
      ...context,
      nodes: processedNodes
    };
  }
}