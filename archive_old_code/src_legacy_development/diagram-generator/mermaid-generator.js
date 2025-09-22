/**
 * Mermaid.js Diagram Generator
 * Auto-generates various diagram types from code analysis
 */

export class MermaidDiagramGenerator {
  constructor() {
    this.diagramTypes = {
      flowchart: this.generateFlowchart.bind(this),
      sequence: this.generateSequenceDiagram.bind(this),
      class: this.generateClassDiagram.bind(this),
      er: this.generateERDiagram.bind(this),
      gitgraph: this.generateGitGraph.bind(this),
      gantt: this.generateGanttChart.bind(this),
      mindmap: this.generateMindmap.bind(this),
      timeline: this.generateTimeline.bind(this),
      sankey: this.generateSankeyDiagram.bind(this)
    };
  }

  async generateFromAnalysis(type, analysis) {
    const generator = this.diagramTypes[type];
    if (!generator) {
      throw new Error(`Unsupported diagram type: ${type}`);
    }
    return await generator(analysis);
  }

  async generateFromSource(type, source) {
    // Simple text-based generation for when no analysis is provided
    const generator = this.diagramTypes[type];
    if (!generator) {
      throw new Error(`Unsupported diagram type: ${type}`);
    }

    // Create a basic analysis structure from source text
    const basicAnalysis = this.parseSourceText(source);
    return await generator(basicAnalysis);
  }

  parseSourceText(source) {
    // Basic parsing for when we don't have full code analysis
    const lines = source.split('\n');
    const analysis = {
      files: [],
      classes: [],
      functions: [],
      dependencies: [],
      relationships: []
    };

    // Extract basic information from text
    lines.forEach(line => {
      if (line.includes('class ') || line.includes('Class ')) {
        const className = line.match(/class\s+(\w+)/i)?.[1];
        if (className) {
          analysis.classes.push({ name: className, methods: [], properties: [] });
        }
      }
      if (line.includes('function ') || line.includes('def ')) {
        const funcName = line.match(/(?:function|def)\s+(\w+)/i)?.[1];
        if (funcName) {
          analysis.functions.push({ name: funcName, parameters: [], calls: [] });
        }
      }
    });

    return analysis;
  }

  generateFlowchart(analysis) {
    let diagram = 'flowchart TD\n';

    // Add nodes for main components
    const nodes = new Set();
    const connections = [];

    // Add file nodes
    analysis.files?.forEach((file, index) => {
      const nodeId = `F${index}`;
      const fileName = file.path?.split('/').pop() || file.name || `File${index}`;
      diagram += `    ${nodeId}[${fileName}]\n`;
      nodes.add(nodeId);
    });

    // Add class nodes
    analysis.classes?.forEach((cls, index) => {
      const nodeId = `C${index}`;
      diagram += `    ${nodeId}[${cls.name}]\n`;
      nodes.add(nodeId);

      // Connect classes to their files
      if (cls.file && analysis.files) {
        const fileIndex = analysis.files.findIndex(f => f.path === cls.file);
        if (fileIndex >= 0) {
          connections.push(`F${fileIndex} --> ${nodeId}`);
        }
      }
    });

    // Add function nodes
    analysis.functions?.forEach((func, index) => {
      const nodeId = `FN${index}`;
      diagram += `    ${nodeId}(${func.name})\n`;
      nodes.add(nodeId);

      // Connect functions to classes
      if (func.className && analysis.classes) {
        const classIndex = analysis.classes.findIndex(c => c.name === func.className);
        if (classIndex >= 0) {
          connections.push(`C${classIndex} --> ${nodeId}`);
        }
      }
    });

    // Add dependencies
    analysis.dependencies?.forEach(dep => {
      const fromIndex = analysis.files?.findIndex(f => f.path === dep.from);
      const toIndex = analysis.files?.findIndex(f => f.path === dep.to);
      if (fromIndex >= 0 && toIndex >= 0) {
        connections.push(`F${fromIndex} -.-> F${toIndex}`);
      }
    });

    // Add all connections
    connections.forEach(conn => {
      diagram += `    ${conn}\n`;
    });

    // Add styling for trading systems
    diagram += '\n    classDef tradingClass fill:#e1f5fe,stroke:#01579b,stroke-width:2px\n';
    diagram += '    classDef dataClass fill:#f3e5f5,stroke:#4a148c,stroke-width:2px\n';
    diagram += '    classDef apiClass fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px\n';

    return diagram;
  }

  generateSequenceDiagram(analysis) {
    let diagram = 'sequenceDiagram\n';

    // Add participants
    const participants = new Set();

    analysis.classes?.forEach(cls => {
      participants.add(cls.name);
      diagram += `    participant ${cls.name}\n`;
    });

    // Add function calls as sequence interactions
    analysis.functions?.forEach(func => {
      if (func.calls && func.calls.length > 0) {
        func.calls.forEach(call => {
          const from = func.className || 'User';
          const to = call.target || call.name;

          if (from && to) {
            diagram += `    ${from}->>+${to}: ${call.name}()\n`;
            diagram += `    ${to}-->>-${from}: response\n`;
          }
        });
      }
    });

    // Add trading-specific sequences
    if (this.isTradingSystem(analysis)) {
      diagram += '\n    Note over Market,Strategy: Trading Lifecycle\n';
      diagram += '    Market->>+Strategy: market_data\n';
      diagram += '    Strategy->>+RiskManager: check_risk()\n';
      diagram += '    RiskManager-->>-Strategy: approved\n';
      diagram += '    Strategy->>+Executor: execute_trade()\n';
      diagram += '    Executor-->>-Strategy: confirmation\n';
    }

    return diagram;
  }

  generateClassDiagram(analysis) {
    let diagram = 'classDiagram\n';

    // Add classes
    analysis.classes?.forEach(cls => {
      diagram += `    class ${cls.name} {\n`;

      // Add properties
      cls.properties?.forEach(prop => {
        diagram += `        +${prop.type || 'any'} ${prop.name}\n`;
      });

      // Add methods
      cls.methods?.forEach(method => {
        const params = method.parameters?.map(p => `${p.name}: ${p.type || 'any'}`).join(', ') || '';
        diagram += `        +${method.name}(${params}) ${method.returnType || 'void'}\n`;
      });

      diagram += '    }\n\n';
    });

    // Add relationships
    analysis.relationships?.forEach(rel => {
      const relationship = this.mapRelationshipType(rel.type);
      diagram += `    ${rel.from} ${relationship} ${rel.to}\n`;
    });

    // Add inheritance relationships
    analysis.classes?.forEach(cls => {
      if (cls.extends) {
        diagram += `    ${cls.extends} <|-- ${cls.name}\n`;
      }
      if (cls.implements) {
        cls.implements.forEach(iface => {
          diagram += `    ${iface} <|.. ${cls.name}\n`;
        });
      }
    });

    return diagram;
  }

  generateERDiagram(analysis) {
    let diagram = 'erDiagram\n';

    // Generate ER diagram from data models
    analysis.classes?.forEach(cls => {
      if (this.isDataModel(cls)) {
        diagram += `    ${cls.name} {\n`;

        cls.properties?.forEach(prop => {
          const type = this.mapToSQLType(prop.type);
          const constraint = prop.primaryKey ? 'PK' : prop.foreignKey ? 'FK' : '';
          diagram += `        ${type} ${prop.name} ${constraint}\n`;
        });

        diagram += '    }\n\n';
      }
    });

    // Add relationships between entities
    analysis.relationships?.forEach(rel => {
      if (rel.type === 'hasMany' || rel.type === 'belongsTo' || rel.type === 'hasOne') {
        const cardinality = this.mapERCardinality(rel.type);
        diagram += `    ${rel.from} ${cardinality} ${rel.to} : "${rel.description || 'relates to'}"\n`;
      }
    });

    return diagram;
  }

  generateGitGraph(analysis) {
    let diagram = 'gitgraph\n';

    // Generate a basic git flow for the project
    diagram += '    commit id: "Initial commit"\n';
    diagram += '    branch develop\n';
    diagram += '    checkout develop\n';
    diagram += '    commit id: "Add core trading logic"\n';
    diagram += '    branch feature/risk-management\n';
    diagram += '    checkout feature/risk-management\n';
    diagram += '    commit id: "Implement risk calculator"\n';
    diagram += '    commit id: "Add position sizing"\n';
    diagram += '    checkout develop\n';
    diagram += '    merge feature/risk-management\n';
    diagram += '    checkout main\n';
    diagram += '    merge develop\n';
    diagram += '    commit id: "Release v1.0"\n';

    return diagram;
  }

  generateGanttChart(analysis) {
    let diagram = 'gantt\n';
    diagram += '    title AI Trading System Development\n';
    diagram += '    dateFormat  YYYY-MM-DD\n';
    diagram += '    section Architecture\n';
    diagram += '    Design System       :done,    arch, 2024-01-01, 2024-01-15\n';
    diagram += '    Code Analysis       :active,  analysis, 2024-01-16, 2024-01-30\n';
    diagram += '    section Implementation\n';
    diagram += '    Core Trading        :         trading, 2024-02-01, 2024-02-28\n';
    diagram += '    Risk Management     :         risk, 2024-03-01, 2024-03-15\n';
    diagram += '    Backtesting         :         backtest, 2024-03-16, 2024-03-31\n';
    diagram += '    section Testing\n';
    diagram += '    Unit Tests          :         tests, 2024-04-01, 2024-04-15\n';
    diagram += '    Integration Tests   :         integration, 2024-04-16, 2024-04-30\n';

    return diagram;
  }

  generateMindmap(analysis) {
    let diagram = 'mindmap\n';
    diagram += '  root((AI Trading System))\n';

    // Data Sources
    diagram += '    Data Sources\n';
    diagram += '      Market Data\n';
    diagram += '        Real-time Feeds\n';
    diagram += '        Historical Data\n';
    diagram += '      Alternative Data\n';
    diagram += '        News Sentiment\n';
    diagram += '        Social Media\n';

    // Strategy Engine
    diagram += '    Strategy Engine\n';
    diagram += '      Signal Generation\n';
    diagram += '      Machine Learning\n';
    diagram += '        Model Training\n';
    diagram += '        Prediction\n';

    // Risk Management
    diagram += '    Risk Management\n';
    diagram += '      Position Sizing\n';
    diagram += '      Stop Loss\n';
    diagram += '      Portfolio Risk\n';

    // Execution
    diagram += '    Execution\n';
    diagram += '      Order Management\n';
    diagram += '      Broker APIs\n';
    diagram += '      Trade Monitoring\n';

    return diagram;
  }

  generateTimeline(analysis) {
    let diagram = 'timeline\n';
    diagram += '    title Trading System Development Timeline\n';
    diagram += '    \n';
    diagram += '    Phase 1 : Research & Planning\n';
    diagram += '           : Market Research\n';
    diagram += '           : Technology Stack Selection\n';
    diagram += '           : Architecture Design\n';
    diagram += '    \n';
    diagram += '    Phase 2 : Core Development\n';
    diagram += '           : Data Pipeline\n';
    diagram += '           : Strategy Framework\n';
    diagram += '           : Risk Engine\n';
    diagram += '    \n';
    diagram += '    Phase 3 : Testing & Validation\n';
    diagram += '           : Backtesting\n';
    diagram += '           : Paper Trading\n';
    diagram += '           : Performance Analysis\n';
    diagram += '    \n';
    diagram += '    Phase 4 : Deployment\n';
    diagram += '           : Production Setup\n';
    diagram += '           : Monitoring\n';
    diagram += '           : Live Trading\n';

    return diagram;
  }

  generateSankeyDiagram(analysis) {
    let diagram = 'sankey-beta\n';
    diagram += '\n';
    diagram += 'Market Data,Data Processing,1000\n';
    diagram += 'Alternative Data,Data Processing,500\n';
    diagram += 'Data Processing,Feature Engineering,1200\n';
    diagram += 'Feature Engineering,ML Models,800\n';
    diagram += 'Feature Engineering,Rule-based Strategies,400\n';
    diagram += 'ML Models,Signal Generation,600\n';
    diagram += 'Rule-based Strategies,Signal Generation,300\n';
    diagram += 'Signal Generation,Risk Assessment,900\n';
    diagram += 'Risk Assessment,Order Generation,700\n';
    diagram += 'Risk Assessment,Risk Rejection,200\n';
    diagram += 'Order Generation,Trade Execution,700\n';

    return diagram;
  }

  // Helper methods
  isTradingSystem(analysis) {
    const tradingKeywords = ['trade', 'strategy', 'market', 'risk', 'portfolio', 'order', 'signal'];
    const codeText = JSON.stringify(analysis).toLowerCase();
    return tradingKeywords.some(keyword => codeText.includes(keyword));
  }

  isDataModel(cls) {
    return cls.name.toLowerCase().includes('model') ||
           cls.name.toLowerCase().includes('entity') ||
           cls.properties?.some(prop => prop.primaryKey || prop.foreignKey);
  }

  mapRelationshipType(type) {
    const mapping = {
      'hasMany': '||--o{',
      'belongsTo': '}o--||',
      'hasOne': '||--||',
      'uses': '-->',
      'implements': '..>',
      'extends': '--|>',
      'aggregates': 'o--',
      'composes': '*--'
    };
    return mapping[type] || '-->';
  }

  mapToSQLType(jsType) {
    const mapping = {
      'string': 'varchar',
      'number': 'int',
      'boolean': 'boolean',
      'Date': 'datetime',
      'Array': 'json',
      'Object': 'json'
    };
    return mapping[jsType] || 'varchar';
  }

  mapERCardinality(relType) {
    const mapping = {
      'hasMany': '||--o{',
      'belongsTo': '}o--||',
      'hasOne': '||--||'
    };
    return mapping[relType] || '||--||';
  }
}