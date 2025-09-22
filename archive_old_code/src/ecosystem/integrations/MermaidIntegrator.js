/**
 * MermaidIntegrator - Integration layer for Mermaid.js diagram generation
 * Connects with MCP system for real-time diagram creation and updates
 */

const fs = require('fs').promises;
const path = require('path');
const { exec } = require('child_process');
const { promisify } = require('util');

const execAsync = promisify(exec);

class MermaidIntegrator {
  constructor(config = {}) {
    this.config = {
      outputDir: config.outputDir || path.join(process.cwd(), 'docs', 'diagrams'),
      templateDir: config.templateDir || path.join(__dirname, 'templates'),
      mcpEnabled: config.mcpEnabled !== false,
      autoGenerate: config.autoGenerate !== false,
      maxDiagramComplexity: config.maxDiagramComplexity || 50,
      ...config
    };

    this.diagramTemplates = new Map();
    this.generatedDiagrams = new Map();
    this.isInitialized = false;
  }

  /**
   * Initialize the Mermaid integrator
   */
  async initialize() {
    if (this.isInitialized) return;

    try {
      // Ensure output directory exists
      await fs.mkdir(this.config.outputDir, { recursive: true });

      // Load diagram templates
      await this.loadDiagramTemplates();

      // Initialize MCP connection if enabled
      if (this.config.mcpEnabled) {
        await this.initializeMcpConnection();
      }

      this.isInitialized = true;
      console.log('🎨 Mermaid integrator initialized successfully');
    } catch (error) {
      console.error('❌ Failed to initialize Mermaid integrator:', error);
      throw error;
    }
  }

  /**
   * Generate Mermaid diagram based on context and data
   */
  async generateDiagram(diagramRequest) {
    const {
      type,
      title,
      data,
      context,
      projectType,
      outputPath,
      template
    } = diagramRequest;

    try {
      console.log(`🎨 Generating ${type} diagram: ${title}`);

      // Select appropriate diagram generator
      const generator = this.getDiagramGenerator(type);
      if (!generator) {
        throw new Error(`Unsupported diagram type: ${type}`);
      }

      // Generate diagram content
      const diagramContent = await generator.call(this, {
        title,
        data,
        context,
        projectType,
        template
      });

      // Save diagram to file
      const filePath = outputPath || this.generateOutputPath(type, title);
      await this.saveDiagram(filePath, diagramContent, type);

      // Store diagram metadata
      this.generatedDiagrams.set(filePath, {
        type,
        title,
        generatedAt: new Date().toISOString(),
        complexity: this.calculateComplexity(diagramContent),
        context
      });

      // Notify MCP system if enabled
      if (this.config.mcpEnabled) {
        await this.notifyMcpDiagramGenerated(type, title, filePath);
      }

      console.log(`✅ Diagram generated successfully: ${filePath}`);
      return { filePath, content: diagramContent };
    } catch (error) {
      console.error(`❌ Failed to generate ${type} diagram:`, error);
      throw error;
    }
  }

  /**
   * Generate architecture diagram for system components
   */
  async generateArchitectureDiagram({ title, data, context, projectType, template }) {
    const components = data.components || [];
    const relationships = data.relationships || [];

    let mermaidContent = `graph TB\n`;
    mermaidContent += `    %% ${title}\n`;
    mermaidContent += `    %% Generated: ${new Date().toISOString()}\n\n`;

    // Add components
    components.forEach((component, index) => {
      const nodeId = this.sanitizeNodeId(component.name);
      const nodeType = this.getComponentNodeType(component.type);
      mermaidContent += `    ${nodeId}${nodeType}["${component.name}"]\n`;

      if (component.description) {
        mermaidContent += `    %% ${component.description}\n`;
      }
    });

    mermaidContent += '\n';

    // Add relationships
    relationships.forEach(rel => {
      const fromId = this.sanitizeNodeId(rel.from);
      const toId = this.sanitizeNodeId(rel.to);
      const arrowType = this.getRelationshipArrow(rel.type);

      mermaidContent += `    ${fromId} ${arrowType} ${toId}\n`;
      if (rel.label) {
        mermaidContent += `    ${fromId} -.->|"${rel.label}"| ${toId}\n`;
      }
    });

    // Add AI trading specific styling if applicable
    if (projectType === 'ai-trading') {
      mermaidContent += this.getAiTradingArchitectureStyles();
    }

    return mermaidContent;
  }

  /**
   * Generate algorithm flow diagram for trading strategies
   */
  async generateAlgorithmDiagram({ title, data, context, projectType, template }) {
    const steps = data.steps || [];
    const decisions = data.decisions || [];
    const loops = data.loops || [];

    let mermaidContent = `flowchart TD\n`;
    mermaidContent += `    %% ${title}\n`;
    mermaidContent += `    %% Algorithm Flow Diagram\n\n`;

    // Start node
    mermaidContent += `    Start([Start])\n`;

    // Add algorithm steps
    steps.forEach((step, index) => {
      const stepId = `step${index + 1}`;
      const nodeType = step.type === 'decision' ? '{' : '[';
      const nodeClose = step.type === 'decision' ? '}' : ']';

      mermaidContent += `    ${stepId}${nodeType}"${step.description}"${nodeClose}\n`;
    });

    // Add decision nodes
    decisions.forEach((decision, index) => {
      const decisionId = `decision${index + 1}`;
      mermaidContent += `    ${decisionId}{"${decision.condition}"}\n`;

      if (decision.trueStep) {
        mermaidContent += `    ${decisionId} -->|Yes| ${decision.trueStep}\n`;
      }
      if (decision.falseStep) {
        mermaidContent += `    ${decisionId} -->|No| ${decision.falseStep}\n`;
      }
    });

    // End node
    mermaidContent += `    End([End])\n\n`;

    // Connect flow
    mermaidContent += this.generateFlowConnections(steps, decisions);

    // Add trading-specific styling
    if (projectType === 'ai-trading') {
      mermaidContent += this.getAlgorithmStyles();
    }

    return mermaidContent;
  }

  /**
   * Generate API documentation diagram
   */
  async generateApiDiagram({ title, data, context, projectType, template }) {
    const endpoints = data.endpoints || [];
    const services = data.services || [];

    let mermaidContent = `graph LR\n`;
    mermaidContent += `    %% ${title}\n`;
    mermaidContent += `    %% API Architecture Diagram\n\n`;

    // Client node
    mermaidContent += `    Client[Client Application]\n`;

    // API Gateway (if present)
    if (data.hasGateway) {
      mermaidContent += `    Gateway[API Gateway]\n`;
      mermaidContent += `    Client --> Gateway\n`;
    }

    // Group endpoints by service
    const endpointsByService = this.groupEndpointsByService(endpoints);

    Object.entries(endpointsByService).forEach(([serviceName, serviceEndpoints]) => {
      const serviceId = this.sanitizeNodeId(serviceName);
      mermaidContent += `    ${serviceId}[${serviceName}]\n`;

      serviceEndpoints.forEach((endpoint, index) => {
        const endpointId = `${serviceId}_ep${index + 1}`;
        const method = endpoint.method.toUpperCase();

        mermaidContent += `    ${endpointId}["${method} ${endpoint.path}"]\n`;
        mermaidContent += `    ${serviceId} --> ${endpointId}\n`;
      });
    });

    // Add database connections
    if (data.databases) {
      data.databases.forEach(db => {
        const dbId = this.sanitizeNodeId(db.name);
        mermaidContent += `    ${dbId}[(${db.name})]\n`;

        db.connectedServices?.forEach(service => {
          const serviceId = this.sanitizeNodeId(service);
          mermaidContent += `    ${serviceId} --> ${dbId}\n`;
        });
      });
    }

    // Add API styling
    mermaidContent += this.getApiDiagramStyles();

    return mermaidContent;
  }

  /**
   * Generate user journey diagram
   */
  async generateUserJourneyDiagram({ title, data, context, projectType, template }) {
    const journey = data.journey || [];
    const actors = data.actors || ['User'];

    let mermaidContent = `journey\n`;
    mermaidContent += `    title ${title}\n\n`;

    journey.forEach(step => {
      mermaidContent += `    section ${step.section}\n`;

      step.tasks.forEach(task => {
        const satisfaction = task.satisfaction || 3;
        const actorsStr = actors.join(', ');
        mermaidContent += `      ${task.description}: ${satisfaction}: ${actorsStr}\n`;
      });
    });

    return mermaidContent;
  }

  /**
   * Generate sequence diagram for interactions
   */
  async generateSequenceDiagram({ title, data, context, projectType, template }) {
    const participants = data.participants || [];
    const interactions = data.interactions || [];

    let mermaidContent = `sequenceDiagram\n`;
    mermaidContent += `    %% ${title}\n\n`;

    // Add participants
    participants.forEach(participant => {
      mermaidContent += `    participant ${participant.id} as ${participant.name}\n`;
    });

    mermaidContent += '\n';

    // Add interactions
    interactions.forEach(interaction => {
      const { from, to, message, type } = interaction;

      switch (type) {
        case 'sync':
          mermaidContent += `    ${from}->>+${to}: ${message}\n`;
          break;
        case 'async':
          mermaidContent += `    ${from}-->>+${to}: ${message}\n`;
          break;
        case 'response':
          mermaidContent += `    ${to}-->>-${from}: ${message}\n`;
          break;
        default:
          mermaidContent += `    ${from}->${to}: ${message}\n`;
      }
    });

    return mermaidContent;
  }

  /**
   * Helper methods for diagram generation
   */
  getDiagramGenerator(type) {
    const generators = {
      'architecture': this.generateArchitectureDiagram,
      'algorithm': this.generateAlgorithmDiagram,
      'api': this.generateApiDiagram,
      'user-journey': this.generateUserJourneyDiagram,
      'sequence': this.generateSequenceDiagram,
      'flowchart': this.generateAlgorithmDiagram, // Alias
      'system': this.generateArchitectureDiagram  // Alias
    };

    return generators[type];
  }

  sanitizeNodeId(name) {
    return name.replace(/[^a-zA-Z0-9]/g, '').substring(0, 20);
  }

  getComponentNodeType(componentType) {
    const nodeTypes = {
      'service': '[]',
      'database': '[()]',
      'api': '{}',
      'client': '()',
      'external': '<>',
      'queue': '[]'
    };

    return nodeTypes[componentType] || '[]';
  }

  getRelationshipArrow(relType) {
    const arrows = {
      'uses': '-->',
      'calls': '->>',
      'includes': '-.->',
      'extends': '==>'
    };

    return arrows[relType] || '-->';
  }

  groupEndpointsByService(endpoints) {
    const grouped = {};

    endpoints.forEach(endpoint => {
      const service = endpoint.service || 'API';
      if (!grouped[service]) {
        grouped[service] = [];
      }
      grouped[service].push(endpoint);
    });

    return grouped;
  }

  generateFlowConnections(steps, decisions) {
    let connections = '';

    // Connect sequential steps
    for (let i = 0; i < steps.length - 1; i++) {
      connections += `    step${i + 1} --> step${i + 2}\n`;
    }

    // Connect to end
    if (steps.length > 0) {
      connections += `    step${steps.length} --> End\n`;
    }

    return connections;
  }

  /**
   * Styling methods
   */
  getAiTradingArchitectureStyles() {
    return `
    %% AI Trading Architecture Styles
    classDef strategy fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef data fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef ml fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef api fill:#fff3e0,stroke:#e65100,stroke-width:2px
    `;
  }

  getAlgorithmStyles() {
    return `
    %% Algorithm Flow Styles
    classDef decision fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef process fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef data fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    `;
  }

  getApiDiagramStyles() {
    return `
    %% API Diagram Styles
    classDef client fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    classDef service fill:#e0f2f1,stroke:#00695c,stroke-width:2px
    classDef database fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    `;
  }

  /**
   * File operations
   */
  async saveDiagram(filePath, content, type) {
    try {
      const dir = path.dirname(filePath);
      await fs.mkdir(dir, { recursive: true });

      // Save Mermaid content
      await fs.writeFile(filePath, content, 'utf8');

      // Also save as HTML preview if possible
      if (this.config.generatePreview) {
        await this.generateHtmlPreview(filePath, content, type);
      }

    } catch (error) {
      console.error(`Failed to save diagram: ${filePath}`, error);
      throw error;
    }
  }

  generateOutputPath(type, title) {
    const sanitizedTitle = title.replace(/[^a-zA-Z0-9]/g, '-').toLowerCase();
    const timestamp = new Date().toISOString().split('T')[0];
    return path.join(this.config.outputDir, `${type}-${sanitizedTitle}-${timestamp}.mmd`);
  }

  calculateComplexity(content) {
    // Simple complexity calculation based on content length and structure
    const lines = content.split('\n').length;
    const nodes = (content.match(/\[|\{|\(/g) || []).length;
    const connections = (content.match(/-->|->|==>/g) || []).length;

    return Math.min(lines + nodes + connections, this.config.maxDiagramComplexity);
  }

  /**
   * MCP integration methods
   */
  async initializeMcpConnection() {
    try {
      console.log('🔗 Initializing MCP connection for Mermaid integration...');
      // Implementation would connect to MCP system
      // This is a placeholder for the actual MCP connection logic
    } catch (error) {
      console.warn('Failed to initialize MCP connection:', error.message);
    }
  }

  async notifyMcpDiagramGenerated(type, title, filePath) {
    try {
      await execAsync(
        `npx claude-flow@alpha hooks notify --message "Mermaid diagram generated: ${type} - ${title} at ${filePath}"`,
        { timeout: 5000 }
      );
    } catch (error) {
      console.warn('Failed to notify MCP system:', error.message);
    }
  }

  /**
   * Template management
   */
  async loadDiagramTemplates() {
    try {
      if (await this.directoryExists(this.config.templateDir)) {
        const templateFiles = await fs.readdir(this.config.templateDir);

        for (const file of templateFiles) {
          if (file.endsWith('.mmd')) {
            const templateName = path.basename(file, '.mmd');
            const templatePath = path.join(this.config.templateDir, file);
            const templateContent = await fs.readFile(templatePath, 'utf8');

            this.diagramTemplates.set(templateName, templateContent);
          }
        }

        console.log(`📋 Loaded ${this.diagramTemplates.size} diagram templates`);
      }
    } catch (error) {
      console.warn('Failed to load diagram templates:', error.message);
    }
  }

  async directoryExists(dirPath) {
    try {
      const stats = await fs.stat(dirPath);
      return stats.isDirectory();
    } catch {
      return false;
    }
  }

  /**
   * Public API methods
   */
  getGeneratedDiagrams() {
    return Array.from(this.generatedDiagrams.entries()).map(([path, metadata]) => ({
      path,
      ...metadata
    }));
  }

  async regenerateDiagram(filePath, newData) {
    const metadata = this.generatedDiagrams.get(filePath);
    if (!metadata) {
      throw new Error(`Diagram not found: ${filePath}`);
    }

    return this.generateDiagram({
      type: metadata.type,
      title: metadata.title,
      data: newData,
      context: metadata.context,
      outputPath: filePath
    });
  }
}

module.exports = MermaidIntegrator;