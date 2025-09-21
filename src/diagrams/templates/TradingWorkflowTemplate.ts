import { DiagramTemplate } from './DiagramTemplate';
import { DiagramType, TemplateContext } from '../core/types';

export class TradingWorkflowTemplate extends DiagramTemplate {
  readonly type: DiagramType = 'trading-workflow';
  readonly name = 'Trading Workflow';
  readonly description = 'Generate sequence diagrams for trading workflows and processes';

  async generate(context: TemplateContext): Promise<string> {
    const { nodes, relationships, options, metadata } = this.preprocess(context);

    let mermaidCode = 'sequenceDiagram\n';

    // Add participants (actors in the trading system)
    const participants = this.extractParticipants(nodes);
    mermaidCode += this.generateParticipants(participants);

    // Add autonumbering for step tracking
    mermaidCode += '    autonumber\n\n';

    // Generate sequence interactions
    const sequences = this.generateSequences(relationships, metadata);
    mermaidCode += sequences;

    // Add notes and annotations
    const notes = this.generateNotes(metadata);
    mermaidCode += notes;

    // Add loops and conditionals
    const loops = this.generateLoops(metadata);
    mermaidCode += loops;

    return this.applyTheme(mermaidCode, options);
  }

  validate(context: TemplateContext): boolean {
    const { nodes, relationships } = context;

    // Must have at least 2 participants
    if (!nodes || nodes.length < 2) return false;

    // Must have at least 1 interaction
    if (!relationships || relationships.length < 1) return false;

    // Check if it's a sequence-type relationship structure
    return relationships.some(rel =>
      ['message', 'call', 'response', 'event', 'notification'].includes(rel.type)
    );
  }

  getVariables(): string[] {
    return [
      'includeTimestamps',
      'showActivation',
      'includeNotes',
      'autonumber',
      'participantOrder',
      'messageStyle',
      'includeLoops',
      'includeConditions'
    ];
  }

  private extractParticipants(nodes: any[]): any[] {
    return nodes.filter(node =>
      ['trader', 'system', 'exchange', 'broker', 'client', 'api', 'service'].includes(node.type) ||
      node.label.toLowerCase().includes('trader') ||
      node.label.toLowerCase().includes('system') ||
      node.label.toLowerCase().includes('exchange')
    );
  }

  private generateParticipants(participants: any[]): string {
    return participants.map(participant => {
      const participantId = this.generateNodeId(participant.id);
      const label = this.escapeLabel(participant.label);
      const alias = participant.properties?.alias || participantId;

      return `    participant ${alias} as ${label}`;
    }).join('\n') + '\n\n';
  }

  private generateSequences(relationships: any[], metadata: any): string {
    // Sort relationships by timestamp or sequence order
    const sortedRelationships = this.sortBySequence(relationships, metadata);

    return sortedRelationships.map(rel => {
      const source = this.generateNodeId(rel.source);
      const target = this.generateNodeId(rel.target);
      const message = this.escapeLabel(rel.label || rel.type);
      const arrow = this.getSequenceArrow(rel.type);

      // Add timing information if available
      const timing = rel.properties?.timing ? ` (${rel.properties.timing}ms)` : '';
      const fullMessage = `${message}${timing}`;

      return `    ${source}${arrow}${target}: ${fullMessage}`;
    }).join('\n') + '\n';
  }

  private generateNotes(metadata: any): string {
    if (!metadata?.notes) return '';

    return metadata.notes.map((note: any) => {
      const participant = this.generateNodeId(note.participant || 'system');
      const noteText = this.escapeLabel(note.text);
      const position = note.position === 'left' ? 'left of' : 'right of';

      return `    Note ${position} ${participant}: ${noteText}`;
    }).join('\n') + '\n';
  }

  private generateLoops(metadata: any): string {
    if (!metadata?.loops) return '';

    return metadata.loops.map((loop: any) => {
      const condition = this.escapeLabel(loop.condition);
      const content = loop.content || '';

      return `    loop ${condition}\n${content}\n    end`;
    }).join('\n') + '\n';
  }

  private getSequenceArrow(messageType: string): string {
    const arrows = {
      'call': '->>',
      'response': '-->>',
      'async': '->>+',
      'sync': '->>',
      'event': '-))',
      'notification': '->>',
      'request': '->>',
      'reply': '-->>',
      'broadcast': '->)',
      'callback': '-->>',
      'trigger': '-))',
      'publish': '->>',
      'subscribe': '-->>',
      'order': '->>',
      'fill': '-->>',
      'cancel': '->x',
      'reject': '--x',
      'confirm': '-->>',
      'error': '--x'
    };

    return arrows[messageType] || '->';
  }

  private sortBySequence(relationships: any[], metadata: any): any[] {
    return relationships.sort((a, b) => {
      // Sort by sequence number if available
      if (a.properties?.sequence && b.properties?.sequence) {
        return a.properties.sequence - b.properties.sequence;
      }

      // Sort by timestamp if available
      if (a.properties?.timestamp && b.properties?.timestamp) {
        return new Date(a.properties.timestamp).getTime() - new Date(b.properties.timestamp).getTime();
      }

      // Default order
      return 0;
    });
  }

  protected preprocess(context: TemplateContext): TemplateContext {
    // Enhance context with trading-specific sequence patterns
    const enhancedNodes = context.nodes.map(node => {
      // Add trading system roles
      if (node.label.toLowerCase().includes('trader')) {
        return { ...node, type: 'trader' };
      }
      if (node.label.toLowerCase().includes('exchange')) {
        return { ...node, type: 'exchange' };
      }
      if (node.label.toLowerCase().includes('broker')) {
        return { ...node, type: 'broker' };
      }
      if (node.label.toLowerCase().includes('order')) {
        return { ...node, type: 'system' };
      }
      return node;
    });

    // Enhance relationships with trading message types
    const enhancedRelationships = context.relationships.map(rel => {
      if (rel.label && rel.label.toLowerCase().includes('order')) {
        return { ...rel, type: 'order' };
      }
      if (rel.label && rel.label.toLowerCase().includes('fill')) {
        return { ...rel, type: 'fill' };
      }
      if (rel.label && rel.label.toLowerCase().includes('cancel')) {
        return { ...rel, type: 'cancel' };
      }
      if (rel.label && rel.label.toLowerCase().includes('market data')) {
        return { ...rel, type: 'event' };
      }
      return rel;
    });

    // Add trading-specific metadata
    const tradingMetadata = {
      ...context.metadata,
      notes: context.metadata?.notes || [
        {
          participant: 'trader',
          text: 'Initiates trading decisions',
          position: 'right'
        },
        {
          participant: 'exchange',
          text: 'Processes orders and provides market data',
          position: 'left'
        }
      ]
    };

    return {
      ...context,
      nodes: enhancedNodes,
      relationships: enhancedRelationships,
      metadata: tradingMetadata
    };
  }
}