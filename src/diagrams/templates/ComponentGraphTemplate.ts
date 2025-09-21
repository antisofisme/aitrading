import { DiagramTemplate } from './DiagramTemplate';
import { DiagramType, TemplateContext, DiagramNode, DiagramRelationship } from '../core/types';

export class ComponentGraphTemplate extends DiagramTemplate {
  readonly type: DiagramType = 'component-graph';
  readonly name = 'Component Graph';
  readonly description = 'Generate component relationship graphs showing dependencies and interactions';

  async generate(context: TemplateContext): Promise<string> {
    const { nodes, relationships, options } = this.preprocess(context);

    const direction = this.optimizeLayout(context);
    let mermaidCode = `graph ${direction}\n`;

    // Generate component nodes with clustering
    const clusters = this.generateClusters(nodes);
    mermaidCode += clusters;

    // Generate nodes outside of clusters
    const standaloneNodes = this.generateStandaloneNodes(nodes);
    mermaidCode += standaloneNodes;

    // Generate dependencies and relationships
    const dependencies = this.generateDependencies(relationships);
    mermaidCode += dependencies;

    // Apply component-specific styling
    const styling = this.generateComponentStyling(nodes, options);
    mermaidCode += styling;

    // Add click events for component details
    const clickEvents = this.generateClickEvents(nodes, options);
    mermaidCode += clickEvents;

    return this.applyTheme(mermaidCode, options);
  }

  validate(context: TemplateContext): boolean {
    const { nodes, relationships } = context;

    // Must have at least 1 component
    if (!nodes || nodes.length < 1) return false;

    // Should have dependency relationships
    if (relationships && relationships.length > 0) {
      const hasDependencies = relationships.some(rel =>
        ['depends', 'uses', 'imports', 'extends', 'implements', 'calls'].includes(rel.type)
      );
      return hasDependencies;
    }

    return true; // Allow single component diagrams
  }

  getVariables(): string[] {
    return [
      'clusterByModule',
      'showVersions',
      'includeDependencies',
      'dependencyStyle',
      'componentShape',
      'versionDisplay',
      'moduleGrouping'
    ];
  }

  private generateClusters(nodes: DiagramNode[]): string {
    const clusters = this.groupByModule(nodes);
    let clusterCode = '';

    Object.entries(clusters).forEach(([moduleName, moduleNodes]) => {
      if (moduleNodes.length < 2) return; // Don't cluster single components

      const clusterId = this.generateNodeId(`cluster_${moduleName}`);
      const clusterLabel = this.formatModuleName(moduleName);

      clusterCode += `    subgraph ${clusterId}["${clusterLabel}"]\n`;

      moduleNodes.forEach(node => {
        const nodeDefinition = this.generateComponentNode(node);
        clusterCode += `        ${nodeDefinition}\n`;
      });

      clusterCode += '    end\n\n';
    });

    return clusterCode;
  }

  private generateStandaloneNodes(nodes: DiagramNode[]): string {
    const clusteredModules = this.groupByModule(nodes);
    const standaloneNodes = nodes.filter(node => {
      const module = this.getNodeModule(node);
      return !clusteredModules[module] || clusteredModules[module].length < 2;
    });

    return standaloneNodes.map(node => {
      const nodeDefinition = this.generateComponentNode(node);
      return `    ${nodeDefinition}`;
    }).join('\n') + (standaloneNodes.length > 0 ? '\n\n' : '');
  }

  private generateComponentNode(node: DiagramNode): string {
    const nodeId = this.generateNodeId(node.id);
    const label = this.generateComponentLabel(node);
    const shape = this.getComponentShape(node.type);

    return `${nodeId}${shape.start}"${label}"${shape.end}`;
  }

  private generateComponentLabel(node: DiagramNode): string {
    let label = this.escapeLabel(node.label);

    // Add version if available
    if (node.properties?.version) {
      label += `<br/>v${node.properties.version}`;
    }

    // Add component type badge
    if (node.type && node.type !== 'component') {
      label += `<br/>[${node.type.toUpperCase()}]`;
    }

    // Add status indicator
    if (node.properties?.status) {
      const statusEmoji = this.getStatusEmoji(node.properties.status);
      label += `<br/>${statusEmoji} ${node.properties.status}`;
    }

    return label;
  }

  private generateDependencies(relationships: DiagramRelationship[]): string {
    return relationships.map(rel => {
      const sourceId = this.generateNodeId(rel.source);
      const targetId = this.generateNodeId(rel.target);
      const arrow = this.getDependencyArrow(rel.type);
      const label = rel.label ? `|${this.escapeLabel(rel.label)}|` : '';

      // Add dependency type styling
      const styleClass = this.getDependencyStyleClass(rel.type);

      return `    ${sourceId} ${arrow}${label} ${targetId}${styleClass}`;
    }).join('\n') + '\n';
  }

  private generateComponentStyling(nodes: DiagramNode[], options: any): string {
    let styling = '\n';

    nodes.forEach(node => {
      const nodeId = this.generateNodeId(node.id);
      const componentType = node.type || 'component';

      // Apply type-based styling
      const typeColor = this.getComponentTypeColor(componentType);
      styling += `    style ${nodeId} fill:${typeColor}\n`;

      // Apply status-based styling
      if (node.properties?.status) {
        const statusStyle = this.getStatusStyle(node.properties.status);
        styling += `    style ${nodeId} ${statusStyle}\n`;
      }

      // Apply custom styling
      if (node.style) {
        styling += this.applyNodeStyling(nodeId, node.style);
      }
    });

    // Add dependency type styling
    styling += this.generateDependencyTypeStyles();

    return styling;
  }

  private groupByModule(nodes: DiagramNode[]): Record<string, DiagramNode[]> {
    return nodes.reduce((groups, node) => {
      const module = this.getNodeModule(node);
      if (!groups[module]) groups[module] = [];
      groups[module].push(node);
      return groups;
    }, {} as Record<string, DiagramNode[]>);
  }

  private getNodeModule(node: DiagramNode): string {
    // Extract module from properties or infer from label
    if (node.properties?.module) {
      return node.properties.module;
    }

    // Infer module from namespace or package
    if (node.properties?.namespace) {
      return node.properties.namespace;
    }

    // Infer from label structure (e.g., "auth.UserService" -> "auth")
    const parts = node.label.split('.');
    if (parts.length > 1) {
      return parts[0];
    }

    // Default module
    return 'core';
  }

  private formatModuleName(moduleName: string): string {
    return moduleName.charAt(0).toUpperCase() + moduleName.slice(1);
  }

  private getComponentShape(componentType: string): { start: string; end: string } {
    const shapes = {
      'service': { start: '(', end: ')' },
      'controller': { start: '[', end: ']' },
      'repository': { start: '[(', end: ')]' },
      'model': { start: '{{', end: '}}' },
      'interface': { start: '((', end: '))' },
      'enum': { start: '{', end: '}' },
      'utility': { start: '[/', end: '/]' },
      'config': { start: '[\\', end: '\\]' },
      'middleware': { start: '>>', end: '>>>>' },
      'component': { start: '[', end: ']' },
      'module': { start: '[[', end: ']]' },
      'library': { start: '(((', end: ')))' },
      'api': { start: '[', end: ']' },
      'database': { start: '[(', end: ')]' }
    };

    return shapes[componentType] || { start: '[', end: ']' };
  }

  private getDependencyArrow(dependencyType: string): string {
    const arrows = {
      'depends': '-->',
      'uses': '-.->',
      'imports': '-->',
      'extends': '==>',
      'implements': '-.->',
      'calls': '-->',
      'contains': '-->',
      'aggregates': 'o-->',
      'composes': '*-->',
      'inherits': '==>',
      'realizes': '-.->',
      'associates': '---'
    };

    return arrows[dependencyType] || '-->';
  }

  private getDependencyStyleClass(dependencyType: string): string {
    const styleClasses = {
      'extends': ':::inheritance',
      'implements': ':::realization',
      'depends': ':::dependency',
      'uses': ':::usage',
      'aggregates': ':::aggregation',
      'composes': ':::composition'
    };

    return styleClasses[dependencyType] || '';
  }

  private getComponentTypeColor(componentType: string): string {
    const colors = {
      'service': '#e3f2fd',
      'controller': '#f3e5f5',
      'repository': '#e8f5e8',
      'model': '#fff3e0',
      'interface': '#f1f8e9',
      'enum': '#fce4ec',
      'utility': '#e0f2f1',
      'config': '#fff8e1',
      'middleware': '#e1f5fe',
      'component': '#f5f5f5',
      'module': '#e8eaf6',
      'library': '#fff9c4',
      'api': '#e3f2fd',
      'database': '#e8f5e8'
    };

    return colors[componentType] || '#f5f5f5';
  }

  private getStatusEmoji(status: string): string {
    const emojis = {
      'stable': '✅',
      'beta': '🚧',
      'alpha': '⚠️',
      'deprecated': '🚫',
      'experimental': '🧪',
      'legacy': '📦'
    };

    return emojis[status] || '';
  }

  private getStatusStyle(status: string): string {
    const styles = {
      'stable': 'stroke:#4caf50,stroke-width:2px',
      'beta': 'stroke:#ff9800,stroke-width:2px',
      'alpha': 'stroke:#f44336,stroke-width:2px',
      'deprecated': 'stroke:#9e9e9e,stroke-width:2px,stroke-dasharray: 5 5',
      'experimental': 'stroke:#9c27b0,stroke-width:2px',
      'legacy': 'stroke:#795548,stroke-width:2px'
    };

    return styles[status] || '';
  }

  private generateDependencyTypeStyles(): string {
    return `
    classDef inheritance stroke:#2196f3,stroke-width:2px
    classDef realization stroke:#4caf50,stroke-width:2px,stroke-dasharray: 5 5
    classDef dependency stroke:#ff9800,stroke-width:2px
    classDef usage stroke:#9c27b0,stroke-width:2px,stroke-dasharray: 3 3
    classDef aggregation stroke:#00bcd4,stroke-width:2px
    classDef composition stroke:#f44336,stroke-width:3px
`;
  }

  protected preprocess(context: TemplateContext): TemplateContext {
    // Enhance context with trading component patterns
    const enhancedNodes = context.nodes.map(node => {
      // Classify trading components
      if (node.label.toLowerCase().includes('trading')) {
        return { ...node, type: 'service', properties: { ...node.properties, module: 'trading' } };
      }
      if (node.label.toLowerCase().includes('order')) {
        return { ...node, type: 'service', properties: { ...node.properties, module: 'order' } };
      }
      if (node.label.toLowerCase().includes('market')) {
        return { ...node, type: 'service', properties: { ...node.properties, module: 'market' } };
      }
      if (node.label.toLowerCase().includes('portfolio')) {
        return { ...node, type: 'service', properties: { ...node.properties, module: 'portfolio' } };
      }
      if (node.label.toLowerCase().includes('auth')) {
        return { ...node, type: 'service', properties: { ...node.properties, module: 'auth' } };
      }

      return { ...node, type: node.type || 'component' };
    });

    return {
      ...context,
      nodes: enhancedNodes
    };
  }
}