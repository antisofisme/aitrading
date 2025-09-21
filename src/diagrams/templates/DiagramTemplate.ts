import { DiagramType, TemplateContext, MermaidTemplate, DiagramOptions } from '../core/types';

export abstract class DiagramTemplate {
  abstract readonly type: DiagramType;
  abstract readonly name: string;
  abstract readonly description: string;

  /**
   * Generate Mermaid code from template context
   */
  abstract generate(context: TemplateContext): Promise<string>;

  /**
   * Validate if context is suitable for this template
   */
  abstract validate(context: TemplateContext): boolean;

  /**
   * Get template variables that can be customized
   */
  abstract getVariables(): string[];

  /**
   * Preprocess context before generation
   */
  protected preprocess(context: TemplateContext): TemplateContext {
    return context;
  }

  /**
   * Apply theme-specific styling
   */
  protected applyTheme(mermaidCode: string, options: DiagramOptions): string {
    if (!options.theme || options.theme === 'default') {
      return mermaidCode;
    }

    // Apply theme-specific modifications
    const themePrefix = this.getThemePrefix(options.theme);
    return `${themePrefix}\n${mermaidCode}`;
  }

  /**
   * Get theme configuration prefix
   */
  private getThemePrefix(theme: string): string {
    const themeConfigs = {
      'dark': '%%{init: {"theme": "dark"}}%%',
      'forest': '%%{init: {"theme": "forest"}}%%',
      'neutral': '%%{init: {"theme": "neutral"}}%%',
      'trading-dark': '%%{init: {"theme": "dark", "themeVariables": {"primaryColor": "#1a1a1a", "primaryTextColor": "#00ff88", "primaryBorderColor": "#00ff88", "lineColor": "#666", "sectionBkgColor": "#2a2a2a", "altSectionBkgColor": "#1a1a1a"}}}%%',
      'trading-light': '%%{init: {"theme": "base", "themeVariables": {"primaryColor": "#f8f9fa", "primaryTextColor": "#1a7f64", "primaryBorderColor": "#1a7f64", "lineColor": "#28a745", "sectionBkgColor": "#e8f5e8", "altSectionBkgColor": "#f8f9fa"}}}%%'
    };

    return themeConfigs[theme] || '%%{init: {"theme": "default"}}%%';
  }

  /**
   * Escape special characters for Mermaid
   */
  protected escapeLabel(label: string): string {
    return label
      .replace(/"/g, '#quot;')
      .replace(/\n/g, '<br>')
      .replace(/\[/g, '#91;')
      .replace(/\]/g, '#93;')
      .replace(/\(/g, '#40;')
      .replace(/\)/g, '#41;');
  }

  /**
   * Generate node ID that's safe for Mermaid
   */
  protected generateNodeId(label: string): string {
    return label
      .toLowerCase()
      .replace(/[^a-z0-9]/g, '_')
      .replace(/_+/g, '_')
      .replace(/^_|_$/g, '');
  }

  /**
   * Apply styling to node or edge
   */
  protected applyNodeStyling(nodeId: string, style: any): string {
    if (!style) return '';

    const styleProps = [];
    if (style.fill) styleProps.push(`fill:${style.fill}`);
    if (style.stroke) styleProps.push(`stroke:${style.stroke}`);
    if (style.strokeWidth) styleProps.push(`stroke-width:${style.strokeWidth}px`);
    if (style.fontColor) styleProps.push(`color:${style.fontColor}`);

    return styleProps.length > 0
      ? `\n    style ${nodeId} ${styleProps.join(',')}`
      : '';
  }

  /**
   * Generate click events for interactive diagrams
   */
  protected generateClickEvents(nodes: any[], options: DiagramOptions): string {
    if (!options.interactive) return '';

    return nodes
      .filter(node => node.properties?.clickable)
      .map(node => `    click ${this.generateNodeId(node.id)} "${node.properties.clickUrl || '#'}"`)
      .join('\n');
  }

  /**
   * Generate subgraph for grouping related nodes
   */
  protected generateSubgraph(
    groupId: string,
    groupLabel: string,
    nodes: any[]
  ): string {
    const nodeIds = nodes.map(node => this.generateNodeId(node.id));
    return `
    subgraph ${groupId}["${this.escapeLabel(groupLabel)}"]
        ${nodeIds.join('\n        ')}
    end`;
  }

  /**
   * Add animation directives
   */
  protected addAnimations(mermaidCode: string, options: DiagramOptions): string {
    if (!options.animations) return mermaidCode;

    return mermaidCode + '\n    %%{wrap}%%';
  }

  /**
   * Optimize layout based on node count and complexity
   */
  protected optimizeLayout(context: TemplateContext): string {
    const nodeCount = context.nodes.length;
    const edgeCount = context.relationships.length;

    // Suggest layout direction based on complexity
    if (nodeCount > 15 || edgeCount > 20) {
      return 'TD'; // Top-down for complex diagrams
    } else if (edgeCount > nodeCount) {
      return 'LR'; // Left-right for relationship-heavy diagrams
    }

    return context.options.layout?.direction || 'TD';
  }
}