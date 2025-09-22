import { DiagramTemplate } from './DiagramTemplate';
import { DiagramType, TemplateContext } from '../core/types';

export class UserJourneyTemplate extends DiagramTemplate {
  readonly type: DiagramType = 'user-journey';
  readonly name = 'User Journey';
  readonly description = 'Generate user journey diagrams showing user interactions and experiences';

  async generate(context: TemplateContext): Promise<string> {
    const { nodes, relationships, options, metadata } = this.preprocess(context);

    let mermaidCode = 'journey\n';

    // Add title if available
    const title = metadata?.title || options?.title || 'User Journey';
    mermaidCode += `    title ${this.escapeLabel(title)}\n\n`;

    // Generate journey sections
    const sections = this.generateJourneySections(nodes, relationships, metadata);
    mermaidCode += sections;

    return this.applyTheme(mermaidCode, options);
  }

  validate(context: TemplateContext): boolean {
    const { nodes, metadata } = context;

    // Must have at least 1 journey step
    if (!nodes || nodes.length < 1) return false;

    // Should have journey-related content
    const hasJourneyContent = nodes.some(node =>
      node.type === 'step' ||
      node.type === 'touchpoint' ||
      node.label.toLowerCase().includes('step') ||
      node.label.toLowerCase().includes('journey')
    ) || (metadata && (metadata.journey || metadata.steps));

    return hasJourneyContent;
  }

  getVariables(): string[] {
    return [
      'showEmotions',
      'includeTouchpoints',
      'groupByPhase',
      'showSatisfactionScore',
      'includeActions',
      'showPainPoints',
      'displayMetrics'
    ];
  }

  private generateJourneySections(nodes: any[], relationships: any[], metadata: any): string {
    // Group nodes by journey phases or sections
    const phases = this.groupByPhase(nodes, metadata);

    return Object.entries(phases).map(([phaseName, phaseSteps]) => {
      const phaseLabel = this.formatPhaseLabel(phaseName);
      let sectionCode = `    section ${phaseLabel}\n`;

      // Sort steps by sequence
      const sortedSteps = this.sortSteps(phaseSteps);

      sortedSteps.forEach(step => {
        const stepDefinition = this.generateJourneyStep(step);
        sectionCode += `      ${stepDefinition}\n`;
      });

      return sectionCode;
    }).join('\n') + '\n';
  }

  private generateJourneyStep(step: any): string {
    const stepName = this.escapeLabel(step.label);
    const actors = this.getStepActors(step);
    const satisfaction = this.getStepSatisfaction(step);

    // Format: stepName: score: actor1, actor2
    return `${stepName}: ${satisfaction}: ${actors}`;
  }

  private groupByPhase(nodes: any[], metadata: any): Record<string, any[]> {
    // Use predefined phases from metadata if available
    if (metadata?.phases) {
      const phaseGroups: Record<string, any[]> = {};

      metadata.phases.forEach((phase: any) => {
        phaseGroups[phase.name] = nodes.filter(node =>
          phase.steps.includes(node.id) || phase.steps.includes(node.label)
        );
      });

      return phaseGroups;
    }

    // Auto-group by phase property or infer from labels
    return nodes.reduce((groups, node) => {
      const phase = this.inferPhase(node);
      if (!groups[phase]) groups[phase] = [];
      groups[phase].push(node);
      return groups;
    }, {} as Record<string, any[]>);
  }

  private inferPhase(node: any): string {
    // Check for explicit phase property
    if (node.properties?.phase) {
      return node.properties.phase;
    }

    // Infer phase from label or type
    const label = node.label.toLowerCase();

    if (label.includes('sign') || label.includes('register') || label.includes('login')) {
      return 'Authentication';
    }
    if (label.includes('browse') || label.includes('search') || label.includes('discover')) {
      return 'Discovery';
    }
    if (label.includes('order') || label.includes('trade') || label.includes('buy') || label.includes('sell')) {
      return 'Trading';
    }
    if (label.includes('portfolio') || label.includes('balance') || label.includes('history')) {
      return 'Portfolio Management';
    }
    if (label.includes('setting') || label.includes('profile') || label.includes('account')) {
      return 'Account Management';
    }
    if (label.includes('support') || label.includes('help') || label.includes('contact')) {
      return 'Support';
    }

    return 'General';
  }

  private formatPhaseLabel(phaseName: string): string {
    return phaseName.replace(/[^a-zA-Z0-9\s]/g, '').trim();
  }

  private sortSteps(steps: any[]): any[] {
    return steps.sort((a, b) => {
      // Sort by sequence number if available
      if (a.properties?.sequence && b.properties?.sequence) {
        return a.properties.sequence - b.properties.sequence;
      }

      // Sort by timestamp if available
      if (a.properties?.timestamp && b.properties?.timestamp) {
        return new Date(a.properties.timestamp).getTime() - new Date(b.properties.timestamp).getTime();
      }

      // Sort alphabetically as fallback
      return a.label.localeCompare(b.label);
    });
  }

  private getStepActors(step: any): string {
    // Extract actors/personas involved in this step
    const actors = step.properties?.actors || ['User'];

    // Map to journey-friendly actor names
    const actorMap = {
      'user': 'User',
      'trader': 'Trader',
      'system': 'System',
      'support': 'Support',
      'admin': 'Admin',
      'api': 'API',
      'exchange': 'Exchange',
      'broker': 'Broker'
    };

    return actors.map((actor: string) =>
      actorMap[actor.toLowerCase()] || actor
    ).join(', ');
  }

  private getStepSatisfaction(step: any): number {
    // Get satisfaction score (1-5 scale for journey diagrams)
    if (step.properties?.satisfaction) {
      return Math.max(1, Math.min(5, step.properties.satisfaction));
    }

    // Infer satisfaction from step characteristics
    if (step.properties?.isPainPoint) {
      return 2;
    }

    if (step.properties?.isDelightful) {
      return 5;
    }

    if (step.type === 'error' || step.label.toLowerCase().includes('error')) {
      return 1;
    }

    if (step.type === 'success' || step.label.toLowerCase().includes('success')) {
      return 5;
    }

    // Default neutral satisfaction
    return 3;
  }

  protected preprocess(context: TemplateContext): TemplateContext {
    // Enhance context with trading user journey patterns
    const enhancedNodes = context.nodes.map(node => {
      // Add trading-specific journey steps
      const label = node.label.toLowerCase();

      if (label.includes('login') || label.includes('authenticate')) {
        return {
          ...node,
          type: 'step',
          properties: {
            ...node.properties,
            phase: 'Authentication',
            actors: ['User', 'System'],
            satisfaction: 3
          }
        };
      }

      if (label.includes('market') || label.includes('price')) {
        return {
          ...node,
          type: 'step',
          properties: {
            ...node.properties,
            phase: 'Discovery',
            actors: ['Trader', 'System'],
            satisfaction: 4
          }
        };
      }

      if (label.includes('order') || label.includes('trade')) {
        return {
          ...node,
          type: 'step',
          properties: {
            ...node.properties,
            phase: 'Trading',
            actors: ['Trader', 'Exchange'],
            satisfaction: 4
          }
        };
      }

      if (label.includes('portfolio') || label.includes('balance')) {
        return {
          ...node,
          type: 'step',
          properties: {
            ...node.properties,
            phase: 'Portfolio Management',
            actors: ['User', 'System'],
            satisfaction: 4
          }
        };
      }

      return {
        ...node,
        type: node.type || 'step',
        properties: {
          ...node.properties,
          actors: node.properties?.actors || ['User'],
          satisfaction: node.properties?.satisfaction || 3
        }
      };
    });

    // Add trading-specific metadata if not present
    const tradingMetadata = {
      ...context.metadata,
      title: context.metadata?.title || 'Trading Platform User Journey',
      phases: context.metadata?.phases || [
        {
          name: 'Authentication',
          description: 'User login and account verification'
        },
        {
          name: 'Discovery',
          description: 'Market exploration and research'
        },
        {
          name: 'Trading',
          description: 'Order placement and execution'
        },
        {
          name: 'Portfolio Management',
          description: 'Account and portfolio monitoring'
        },
        {
          name: 'Support',
          description: 'Help and customer service'
        }
      ]
    };

    return {
      ...context,
      nodes: enhancedNodes,
      metadata: tradingMetadata
    };
  }
}