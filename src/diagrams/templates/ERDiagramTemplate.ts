import { DiagramTemplate } from './DiagramTemplate';
import { DiagramType, TemplateContext, DiagramNode, DiagramRelationship } from '../core/types';

export class ERDiagramTemplate extends DiagramTemplate {
  readonly type: DiagramType = 'er-diagram';
  readonly name = 'Entity Relationship Diagram';
  readonly description = 'Generate ER diagrams for database schema visualization';

  async generate(context: TemplateContext): Promise<string> {
    const { nodes, relationships, options } = this.preprocess(context);

    let mermaidCode = 'erDiagram\n';

    // Generate entities with attributes
    const entityDefinitions = this.generateEntities(nodes);
    mermaidCode += entityDefinitions;

    // Generate relationships
    const relationshipDefinitions = this.generateERRelationships(relationships);
    mermaidCode += relationshipDefinitions;

    return this.applyTheme(mermaidCode, options);
  }

  validate(context: TemplateContext): boolean {
    const { nodes, relationships } = context;

    // Must have at least 1 entity
    if (!nodes || nodes.length < 1) return false;

    // Nodes should represent database entities
    const hasValidEntities = nodes.some(node =>
      node.type === 'table' ||
      node.type === 'entity' ||
      node.properties?.attributes ||
      node.label.toLowerCase().includes('table')
    );

    return hasValidEntities;
  }

  getVariables(): string[] {
    return [
      'showAttributes',
      'showDataTypes',
      'showKeys',
      'includeIndexes',
      'groupBySchema',
      'showConstraints',
      'attributeStyle'
    ];
  }

  private generateEntities(nodes: DiagramNode[]): string {
    return nodes.map(node => {
      const entityName = this.generateEntityName(node.label);
      const attributes = this.generateAttributes(node);

      if (attributes.length === 0) {
        return `    ${entityName} {\n    }\n`;
      }

      return `    ${entityName} {\n${attributes.join('\n')}\n    }\n`;
    }).join('\n') + '\n';
  }

  private generateAttributes(node: DiagramNode): string[] {
    const attributes = node.properties?.attributes || [];

    return attributes.map((attr: any) => {
      const dataType = attr.dataType || 'string';
      const constraints = this.formatConstraints(attr);
      const comment = attr.description ? ` "Comment: ${attr.description}"` : '';

      return `        ${dataType} ${attr.name}${constraints}${comment}`;
    });
  }

  private generateERRelationships(relationships: DiagramRelationship[]): string {
    return relationships.map(rel => {
      const source = this.generateEntityName(rel.source);
      const target = this.generateEntityName(rel.target);
      const cardinality = this.getCardinality(rel);
      const label = rel.label ? ` : "${this.escapeLabel(rel.label)}"` : '';

      return `    ${source} ${cardinality} ${target}${label}`;
    }).join('\n') + '\n';
  }

  private generateEntityName(label: string): string {
    // Convert to valid entity name (PascalCase)
    return label
      .replace(/[^a-zA-Z0-9]/g, '_')
      .replace(/_+/g, '_')
      .replace(/^_|_$/g, '')
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join('');
  }

  private formatConstraints(attribute: any): string {
    const constraints = [];

    if (attribute.primaryKey) constraints.push('PK');
    if (attribute.foreignKey) constraints.push('FK');
    if (attribute.unique) constraints.push('UK');
    if (attribute.notNull) constraints.push('NOT NULL');
    if (attribute.autoIncrement) constraints.push('AUTO_INCREMENT');

    return constraints.length > 0 ? ` ${constraints.join(' ')}` : '';
  }

  private getCardinality(relationship: DiagramRelationship): string {
    const type = relationship.type || 'one-to-many';
    const cardinalities = {
      'one-to-one': '||--||',
      'one-to-many': '||--o{',
      'many-to-one': '}o--||',
      'many-to-many': '}o--o{',
      'zero-to-one': '||--o|',
      'zero-to-many': '||--o{',
      'one-to-zero': '|o--||',
      'many-to-zero': '}o--||'
    };

    return cardinalities[type] || '||--o{';
  }

  protected preprocess(context: TemplateContext): TemplateContext {
    // Enhance context with trading database specific patterns
    const enhancedNodes = context.nodes.map(node => {
      // Add common trading database attributes if not present
      if (node.label.toLowerCase().includes('order') && !node.properties?.attributes) {
        return {
          ...node,
          type: 'table',
          properties: {
            ...node.properties,
            attributes: [
              { name: 'id', dataType: 'bigint', primaryKey: true, autoIncrement: true },
              { name: 'symbol', dataType: 'varchar(10)', notNull: true },
              { name: 'side', dataType: 'enum', notNull: true, description: 'BUY or SELL' },
              { name: 'quantity', dataType: 'decimal(18,8)', notNull: true },
              { name: 'price', dataType: 'decimal(18,8)' },
              { name: 'order_type', dataType: 'enum', notNull: true },
              { name: 'status', dataType: 'enum', notNull: true },
              { name: 'created_at', dataType: 'timestamp', notNull: true },
              { name: 'updated_at', dataType: 'timestamp', notNull: true },
              { name: 'user_id', dataType: 'bigint', foreignKey: true, notNull: true }
            ]
          }
        };
      }

      if (node.label.toLowerCase().includes('trade') && !node.properties?.attributes) {
        return {
          ...node,
          type: 'table',
          properties: {
            ...node.properties,
            attributes: [
              { name: 'id', dataType: 'bigint', primaryKey: true, autoIncrement: true },
              { name: 'order_id', dataType: 'bigint', foreignKey: true, notNull: true },
              { name: 'symbol', dataType: 'varchar(10)', notNull: true },
              { name: 'quantity', dataType: 'decimal(18,8)', notNull: true },
              { name: 'price', dataType: 'decimal(18,8)', notNull: true },
              { name: 'fee', dataType: 'decimal(18,8)', notNull: true },
              { name: 'trade_time', dataType: 'timestamp', notNull: true },
              { name: 'trade_id', dataType: 'varchar(50)', unique: true, notNull: true }
            ]
          }
        };
      }

      if (node.label.toLowerCase().includes('user') && !node.properties?.attributes) {
        return {
          ...node,
          type: 'table',
          properties: {
            ...node.properties,
            attributes: [
              { name: 'id', dataType: 'bigint', primaryKey: true, autoIncrement: true },
              { name: 'username', dataType: 'varchar(50)', unique: true, notNull: true },
              { name: 'email', dataType: 'varchar(255)', unique: true, notNull: true },
              { name: 'password_hash', dataType: 'varchar(255)', notNull: true },
              { name: 'api_key', dataType: 'varchar(64)', unique: true },
              { name: 'api_secret', dataType: 'varchar(64)' },
              { name: 'balance', dataType: 'decimal(18,8)', notNull: true, default: '0' },
              { name: 'created_at', dataType: 'timestamp', notNull: true },
              { name: 'updated_at', dataType: 'timestamp', notNull: true },
              { name: 'is_active', dataType: 'boolean', notNull: true, default: 'true' }
            ]
          }
        };
      }

      if (node.label.toLowerCase().includes('market') && !node.properties?.attributes) {
        return {
          ...node,
          type: 'table',
          properties: {
            ...node.properties,
            attributes: [
              { name: 'id', dataType: 'bigint', primaryKey: true, autoIncrement: true },
              { name: 'symbol', dataType: 'varchar(10)', unique: true, notNull: true },
              { name: 'base_asset', dataType: 'varchar(10)', notNull: true },
              { name: 'quote_asset', dataType: 'varchar(10)', notNull: true },
              { name: 'last_price', dataType: 'decimal(18,8)' },
              { name: 'volume_24h', dataType: 'decimal(18,8)' },
              { name: 'price_change_24h', dataType: 'decimal(5,2)' },
              { name: 'updated_at', dataType: 'timestamp', notNull: true },
              { name: 'is_active', dataType: 'boolean', notNull: true, default: 'true' }
            ]
          }
        };
      }

      return { ...node, type: node.type || 'table' };
    });

    // Enhance relationships with proper FK constraints
    const enhancedRelationships = context.relationships.map(rel => {
      // Infer relationship types based on table names
      if (rel.source.toLowerCase().includes('user') && rel.target.toLowerCase().includes('order')) {
        return { ...rel, type: 'one-to-many', label: 'places' };
      }
      if (rel.source.toLowerCase().includes('order') && rel.target.toLowerCase().includes('trade')) {
        return { ...rel, type: 'one-to-many', label: 'generates' };
      }
      if (rel.source.toLowerCase().includes('market') && rel.target.toLowerCase().includes('order')) {
        return { ...rel, type: 'one-to-many', label: 'contains' };
      }

      return { ...rel, type: rel.type || 'one-to-many' };
    });

    return {
      ...context,
      nodes: enhancedNodes,
      relationships: enhancedRelationships
    };
  }
}