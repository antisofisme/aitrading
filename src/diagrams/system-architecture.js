const { DiagramGenerator } = require('./generator');
const { CodeAnalyzer } = require('../analysis/code-analyzer');
const path = require('path');
const fs = require('fs').promises;

class SystemArchitectureDiagrammer {
  constructor(options = {}) {
    this.projectRoot = options.projectRoot || process.cwd();
    this.outputDir = options.outputDir || path.join(this.projectRoot, 'docs/diagrams');
    this.analyzer = new CodeAnalyzer({ projectRoot: this.projectRoot });
    this.generator = new DiagramGenerator();
  }

  async generateSystemOverview() {
    const analysis = await this.analyzer.analyzeProject();
    
    const diagram = {
      type: 'graph',
      direction: 'TD',
      title: 'AI Trading System Architecture',
      nodes: this._createSystemNodes(analysis),
      edges: this._createSystemEdges(analysis),
      styling: {
        theme: 'base',
        primaryColor: '#1f2937',
        primaryTextColor: '#f9fafb',
        primaryBorderColor: '#374151',
        lineColor: '#6b7280'
      }
    };

    const mermaidCode = this.generator.generateMermaid(diagram);
    await this._saveDiagram('system-overview', mermaidCode);
    
    return {
      diagram: mermaidCode,
      path: path.join(this.outputDir, 'system-overview.mmd'),
      analysis: {
        components: analysis.modules.length,
        dependencies: analysis.dependencies.length,
        complexity: this._calculateComplexity(analysis)
      }
    };
  }

  async generateDataFlow() {
    const analysis = await this.analyzer.analyzeProject();
    const tradingModules = this._identifyTradingModules(analysis);
    
    const diagram = {
      type: 'flowchart',
      direction: 'LR',
      title: 'Trading Data Flow',
      nodes: this._createDataFlowNodes(tradingModules),
      edges: this._createDataFlowEdges(tradingModules),
      styling: {
        theme: 'base',
        primaryColor: '#059669',
        primaryTextColor: '#ffffff',
        primaryBorderColor: '#047857'
      }
    };

    const mermaidCode = this.generator.generateMermaid(diagram);
    await this._saveDiagram('data-flow', mermaidCode);
    
    return {
      diagram: mermaidCode,
      path: path.join(this.outputDir, 'data-flow.mmd'),
      modules: tradingModules.length
    };
  }

  async generateComponentDiagram() {
    const analysis = await this.analyzer.analyzeProject();
    
    const diagram = {
      type: 'classDiagram',
      title: 'Component Architecture',
      classes: this._createComponentClasses(analysis),
      relationships: this._createComponentRelationships(analysis)
    };

    const mermaidCode = this.generator.generateMermaid(diagram);
    await this._saveDiagram('components', mermaidCode);
    
    return {
      diagram: mermaidCode,
      path: path.join(this.outputDir, 'components.mmd'),
      classes: diagram.classes.length
    };
  }

  async generateSequenceDiagram() {
    const analysis = await this.analyzer.analyzeProject();
    const tradingFlow = this._analyzeTradingFlow(analysis);
    
    const diagram = {
      type: 'sequenceDiagram',
      title: 'Trading Execution Sequence',
      participants: this._createSequenceParticipants(tradingFlow),
      interactions: this._createSequenceInteractions(tradingFlow)
    };

    const mermaidCode = this.generator.generateMermaid(diagram);
    await this._saveDiagram('sequence', mermaidCode);
    
    return {
      diagram: mermaidCode,
      path: path.join(this.outputDir, 'sequence.mmd'),
      interactions: diagram.interactions.length
    };
  }

  _createSystemNodes(analysis) {
    const nodes = [];
    
    // Core system components
    nodes.push({
      id: 'market_data',
      label: 'Market Data\nIngestion',
      type: 'rect',
      style: 'fill:#1e40af,stroke:#1e3a8a,color:#ffffff'
    });
    
    nodes.push({
      id: 'ai_engine',
      label: 'AI Trading\nEngine',
      type: 'rect',
      style: 'fill:#dc2626,stroke:#b91c1c,color:#ffffff'
    });
    
    nodes.push({
      id: 'risk_mgmt',
      label: 'Risk\nManagement',
      type: 'rect',
      style: 'fill:#ea580c,stroke:#c2410c,color:#ffffff'
    });
    
    nodes.push({
      id: 'execution',
      label: 'Order\nExecution',
      type: 'rect',
      style: 'fill:#059669,stroke:#047857,color:#ffffff'
    });
    
    // Add module-based nodes
    analysis.modules.forEach((module, index) => {
      if (this._isCoreModule(module)) {
        nodes.push({
          id: `module_${index}`,
          label: module.name.replace(/\.(js|ts)$/, ''),
          type: 'rect',
          style: 'fill:#6b7280,stroke:#4b5563,color:#ffffff'
        });
      }
    });
    
    return nodes;
  }

  _createSystemEdges(analysis) {
    const edges = [];
    
    // Core system flow
    edges.push({ from: 'market_data', to: 'ai_engine', label: 'Real-time Data' });
    edges.push({ from: 'ai_engine', to: 'risk_mgmt', label: 'Trading Signals' });
    edges.push({ from: 'risk_mgmt', to: 'execution', label: 'Validated Orders' });
    edges.push({ from: 'execution', to: 'ai_engine', label: 'Execution Feedback' });
    
    // Add dependency edges
    analysis.dependencies.forEach(dep => {
      if (this._isInternalDependency(dep)) {
        edges.push({
          from: this._moduleToNodeId(dep.source),
          to: this._moduleToNodeId(dep.target),
          label: dep.type || 'depends'
        });
      }
    });
    
    return edges;
  }

  _createDataFlowNodes(tradingModules) {
    return tradingModules.map((module, index) => ({
      id: `data_${index}`,
      label: module.name,
      type: module.type === 'input' ? 'circle' : module.type === 'process' ? 'rect' : 'diamond',
      style: this._getDataFlowStyle(module.type)
    }));
  }

  _createDataFlowEdges(tradingModules) {
    const edges = [];
    
    for (let i = 0; i < tradingModules.length - 1; i++) {
      edges.push({
        from: `data_${i}`,
        to: `data_${i + 1}`,
        label: tradingModules[i].output || 'data'
      });
    }
    
    return edges;
  }

  _createComponentClasses(analysis) {
    return analysis.classes.map(cls => ({
      name: cls.name,
      attributes: cls.properties.map(prop => `${prop.name}: ${prop.type || 'any'}`),
      methods: cls.methods.map(method => `${method.name}(${method.params.join(', ')})`),
      stereotype: this._getClassStereotype(cls)
    }));
  }

  _createComponentRelationships(analysis) {
    return analysis.relationships.map(rel => ({
      from: rel.source,
      to: rel.target,
      type: rel.type || 'association',
      label: rel.label || ''
    }));
  }

  _createSequenceParticipants(tradingFlow) {
    return tradingFlow.actors.map(actor => ({
      name: actor.name,
      type: actor.type || 'participant'
    }));
  }

  _createSequenceInteractions(tradingFlow) {
    return tradingFlow.interactions.map(interaction => ({
      from: interaction.from,
      to: interaction.to,
      message: interaction.message,
      type: interaction.type || 'sync',
      note: interaction.note
    }));
  }

  async _saveDiagram(name, content) {
    await fs.mkdir(this.outputDir, { recursive: true });
    const filePath = path.join(this.outputDir, `${name}.mmd`);
    await fs.writeFile(filePath, content, 'utf8');
    
    // Also save as markdown with embedded Mermaid
    const markdownContent = `# ${name.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase())}

\`\`\`mermaid
${content}
\`\`\`
`;
    await fs.writeFile(path.join(this.outputDir, `${name}.md`), markdownContent, 'utf8');
  }

  _identifyTradingModules(analysis) {
    return analysis.modules.filter(module => 
      module.name.toLowerCase().includes('trading') ||
      module.name.toLowerCase().includes('market') ||
      module.name.toLowerCase().includes('order') ||
      module.functions.some(fn => 
        fn.name.toLowerCase().includes('trade') ||
        fn.name.toLowerCase().includes('buy') ||
        fn.name.toLowerCase().includes('sell')
      )
    ).map((module, index) => ({
      ...module,
      type: this._inferModuleType(module),
      order: index
    }));
  }

  _analyzeTradingFlow(analysis) {
    return {
      actors: [
        { name: 'Market', type: 'participant' },
        { name: 'DataIngestion', type: 'participant' },
        { name: 'AIEngine', type: 'participant' },
        { name: 'RiskManager', type: 'participant' },
        { name: 'OrderExecutor', type: 'participant' }
      ],
      interactions: [
        { from: 'Market', to: 'DataIngestion', message: 'Price Updates', type: 'async' },
        { from: 'DataIngestion', to: 'AIEngine', message: 'Processed Data', type: 'sync' },
        { from: 'AIEngine', to: 'RiskManager', message: 'Trading Signal', type: 'sync' },
        { from: 'RiskManager', to: 'OrderExecutor', message: 'Validated Order', type: 'sync' },
        { from: 'OrderExecutor', to: 'Market', message: 'Execute Trade', type: 'async' },
        { from: 'Market', to: 'OrderExecutor', message: 'Execution Confirmation', type: 'async' }
      ]
    };
  }

  _calculateComplexity(analysis) {
    return {
      cyclomatic: analysis.functions.reduce((sum, fn) => sum + (fn.complexity || 1), 0),
      dependencies: analysis.dependencies.length,
      modularity: analysis.modules.length / Math.max(analysis.dependencies.length, 1)
    };
  }

  _isCoreModule(module) {
    const corePatterns = ['index', 'main', 'app', 'server', 'trading', 'market', 'ai', 'risk'];
    return corePatterns.some(pattern => 
      module.name.toLowerCase().includes(pattern)
    );
  }

  _isInternalDependency(dep) {
    return !dep.target.startsWith('node_modules') && 
           !dep.target.startsWith('http') &&
           dep.target.includes('./');
  }

  _moduleToNodeId(modulePath) {
    return modulePath.replace(/[^a-zA-Z0-9]/g, '_').toLowerCase();
  }

  _getDataFlowStyle(type) {
    const styles = {
      input: 'fill:#3b82f6,stroke:#2563eb,color:#ffffff',
      process: 'fill:#059669,stroke:#047857,color:#ffffff',
      output: 'fill:#dc2626,stroke:#b91c1c,color:#ffffff',
      decision: 'fill:#ea580c,stroke:#c2410c,color:#ffffff'
    };
    return styles[type] || styles.process;
  }

  _getClassStereotype(cls) {
    if (cls.methods.some(m => m.name.includes('trade'))) return 'trading';
    if (cls.methods.some(m => m.name.includes('analyze'))) return 'analyzer';
    if (cls.methods.some(m => m.name.includes('risk'))) return 'risk';
    return 'component';
  }

  _inferModuleType(module) {
    const name = module.name.toLowerCase();
    if (name.includes('input') || name.includes('data')) return 'input';
    if (name.includes('output') || name.includes('result')) return 'output';
    if (name.includes('decision') || name.includes('rule')) return 'decision';
    return 'process';
  }
}

module.exports = { SystemArchitectureDiagrammer };
