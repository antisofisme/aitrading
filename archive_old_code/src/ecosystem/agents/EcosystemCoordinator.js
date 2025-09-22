/**
 * EcosystemCoordinator - Orchestrates collaborative documentation agents
 * Integrates with Claude Flow MCP system for real-time coordination
 */

const fs = require('fs').promises;
const path = require('path');
const { EventEmitter } = require('events');
const { exec } = require('child_process');
const { promisify } = require('util');

const execAsync = promisify(exec);

class EcosystemCoordinator extends EventEmitter {
  constructor(config = {}) {
    super();
    this.config = {
      swarmId: config.swarmId || process.env.CLAUDE_FLOW_SWARM_ID,
      memoryKey: 'collab/agents',
      hookTimeout: 5000,
      maxConcurrentAgents: 4,
      ...config
    };

    this.activeAgents = new Map();
    this.projectContext = null;
    this.isInitialized = false;
  }

  /**
   * Initialize the ecosystem coordinator
   */
  async initialize() {
    if (this.isInitialized) return;

    try {
      // Restore session context from memory
      await this.restoreSessionContext();

      // Detect current project context
      this.projectContext = await this.detectProjectContext();

      // Initialize specialized agents
      await this.initializeSpecializedAgents();

      // Setup event listeners
      this.setupEventListeners();

      this.isInitialized = true;
      await this.notifyHook('ecosystem-initialized', { projectContext: this.projectContext });

      console.log('🚀 Ecosystem Coordinator initialized successfully');
    } catch (error) {
      console.error('❌ Failed to initialize ecosystem coordinator:', error);
      throw error;
    }
  }

  /**
   * Detect project context and type
   */
  async detectProjectContext() {
    const projectRoot = process.cwd();
    const context = {
      type: 'unknown',
      features: [],
      technologies: [],
      rootPath: projectRoot
    };

    try {
      // Check for AI trading specific files
      const aiTradingIndicators = [
        'trading',
        'strategy',
        'algorithm',
        'portfolio',
        'market',
        'indicator'
      ];

      // Analyze package.json
      const packagePath = path.join(projectRoot, 'package.json');
      if (await this.fileExists(packagePath)) {
        const packageContent = await fs.readFile(packagePath, 'utf8');
        const packageJson = JSON.parse(packageContent);

        context.name = packageJson.name;
        context.version = packageJson.version;
        context.technologies.push('nodejs');

        // Check dependencies for AI/trading libraries
        const deps = { ...packageJson.dependencies, ...packageJson.devDependencies };
        const depNames = Object.keys(deps).join(' ').toLowerCase();

        if (aiTradingIndicators.some(indicator => depNames.includes(indicator))) {
          context.type = 'ai-trading';
          context.features.push('algorithmic-trading', 'financial-analysis');
        }

        // Check for common frameworks
        if (deps.express) context.technologies.push('express');
        if (deps.react) context.technologies.push('react');
        if (deps.tensorflow || deps['@tensorflow/tfjs']) {
          context.technologies.push('tensorflow');
          context.features.push('machine-learning');
        }
      }

      // Analyze directory structure
      const items = await fs.readdir(projectRoot);
      for (const item of items) {
        const itemLower = item.toLowerCase();
        if (aiTradingIndicators.some(indicator => itemLower.includes(indicator))) {
          context.type = 'ai-trading';
          break;
        }
      }

      // Store context in memory
      await this.storeInMemory('project-context', context);

      return context;
    } catch (error) {
      console.warn('⚠️ Failed to detect project context:', error.message);
      return context;
    }
  }

  /**
   * Initialize specialized documentation agents
   */
  async initializeSpecializedAgents() {
    const agentConfigs = [
      {
        id: 'api-agent',
        type: 'api-documenter',
        patterns: ['**/routes/**', '**/api/**', '**/controllers/**'],
        capabilities: ['openapi-generation', 'endpoint-documentation']
      },
      {
        id: 'architecture-agent',
        type: 'architecture-documenter',
        patterns: ['**/src/**', '**/lib/**', '**/modules/**'],
        capabilities: ['system-diagrams', 'component-mapping']
      },
      {
        id: 'algorithm-agent',
        type: 'algorithm-documenter',
        patterns: ['**/strategies/**', '**/algorithms/**', '**/indicators/**'],
        capabilities: ['algorithm-analysis', 'flow-diagrams']
      },
      {
        id: 'user-guide-agent',
        type: 'user-guide-documenter',
        patterns: ['**/examples/**', '**/tutorials/**', '**/guides/**'],
        capabilities: ['user-documentation', 'tutorial-generation']
      }
    ];

    for (const config of agentConfigs) {
      try {
        const agent = await this.spawnAgent(config);
        this.activeAgents.set(config.id, agent);
      } catch (error) {
        console.warn(`⚠️ Failed to spawn ${config.id}:`, error.message);
      }
    }
  }

  /**
   * Spawn a specialized agent using Claude Flow
   */
  async spawnAgent(config) {
    try {
      const spawnResult = await execAsync(
        `npx claude-flow@alpha agent spawn ${config.type} --capabilities "${config.capabilities.join(',')}" --patterns "${config.patterns.join(',')}"`,
        { timeout: this.config.hookTimeout }
      );

      const agent = {
        ...config,
        status: 'active',
        spawnedAt: new Date().toISOString(),
        result: spawnResult
      };

      await this.storeInMemory(`agents/${config.id}`, agent);
      return agent;
    } catch (error) {
      console.warn(`Failed to spawn agent ${config.id}:`, error.message);
      return { ...config, status: 'failed', error: error.message };
    }
  }

  /**
   * Handle code change events and trigger appropriate agents
   */
  async handleCodeChange(changeEvent) {
    const { filePath, changeType, content } = changeEvent;

    try {
      // Analyze which agents should respond to this change
      const relevantAgents = await this.analyzeRelevantAgents(filePath, changeType);

      // Trigger agents in parallel
      const agentTasks = relevantAgents.map(agentId =>
        this.triggerAgent(agentId, { filePath, changeType, content })
      );

      const results = await Promise.allSettled(agentTasks);

      // Notify about completion
      await this.notifyHook('agents-triggered', {
        filePath,
        changeType,
        agents: relevantAgents,
        results: results.map(r => r.status)
      });

      return results;
    } catch (error) {
      console.error('❌ Failed to handle code change:', error);
      throw error;
    }
  }

  /**
   * Analyze which agents are relevant for a file change
   */
  async analyzeRelevantAgents(filePath, changeType) {
    const relevantAgents = [];
    const fileExt = path.extname(filePath);
    const fileDirPath = path.dirname(filePath);

    for (const [agentId, agent] of this.activeAgents) {
      if (agent.status !== 'active') continue;

      // Check if file matches agent patterns
      const isRelevant = agent.patterns.some(pattern => {
        const regex = new RegExp(pattern.replace(/\*\*/g, '.*').replace(/\*/g, '[^/]*'));
        return regex.test(filePath) || regex.test(fileDirPath);
      });

      if (isRelevant) {
        relevantAgents.push(agentId);
      }
    }

    // Special logic for AI trading projects
    if (this.projectContext?.type === 'ai-trading') {
      const tradingKeywords = ['strategy', 'algorithm', 'trading', 'indicator', 'portfolio'];
      if (tradingKeywords.some(keyword => filePath.includes(keyword))) {
        if (!relevantAgents.includes('algorithm-agent')) {
          relevantAgents.push('algorithm-agent');
        }
      }
    }

    return relevantAgents;
  }

  /**
   * Trigger a specific agent for a code change
   */
  async triggerAgent(agentId, changeData) {
    const agent = this.activeAgents.get(agentId);
    if (!agent || agent.status !== 'active') {
      throw new Error(`Agent ${agentId} is not available`);
    }

    try {
      // Use Claude Flow task orchestration
      const result = await execAsync(
        `npx claude-flow@alpha task orchestrate "${agent.type} analyze and document changes in ${changeData.filePath}" --strategy parallel --priority medium`,
        { timeout: this.config.hookTimeout }
      );

      // Store result in memory
      await this.storeInMemory(`tasks/${agentId}/${Date.now()}`, {
        agentId,
        changeData,
        result: result.stdout,
        timestamp: new Date().toISOString()
      });

      return result;
    } catch (error) {
      console.warn(`Failed to trigger agent ${agentId}:`, error.message);
      throw error;
    }
  }

  /**
   * Setup event listeners for ecosystem coordination
   */
  setupEventListeners() {
    this.on('code-change', this.handleCodeChange.bind(this));
    this.on('agent-request', this.handleAgentRequest.bind(this));
    this.on('mermaid-generation', this.handleMermaidGeneration.bind(this));
  }

  /**
   * Handle agent-specific requests
   */
  async handleAgentRequest(requestData) {
    const { agentId, requestType, data } = requestData;

    switch (requestType) {
      case 'context-update':
        await this.updateAgentContext(agentId, data);
        break;
      case 'collaboration-request':
        await this.facilitateCollaboration(agentId, data);
        break;
      case 'mermaid-diagram':
        await this.generateMermaidDiagram(data);
        break;
      default:
        console.warn(`Unknown request type: ${requestType}`);
    }
  }

  /**
   * Generate Mermaid diagrams based on agent data
   */
  async handleMermaidGeneration(diagramData) {
    try {
      const mermaidAgent = this.activeAgents.get('mermaid-integrator');
      if (!mermaidAgent) {
        console.warn('Mermaid integrator agent not available');
        return;
      }

      const result = await execAsync(
        `npx claude-flow@alpha task orchestrate "Generate Mermaid diagram for ${diagramData.type}" --strategy adaptive`,
        { timeout: this.config.hookTimeout }
      );

      await this.storeInMemory('mermaid/latest', {
        diagramData,
        result: result.stdout,
        timestamp: new Date().toISOString()
      });

      return result;
    } catch (error) {
      console.error('Failed to generate Mermaid diagram:', error);
      throw error;
    }
  }

  /**
   * Utility methods
   */
  async fileExists(filePath) {
    try {
      await fs.access(filePath);
      return true;
    } catch {
      return false;
    }
  }

  async storeInMemory(key, data) {
    try {
      await execAsync(
        `npx claude-flow@alpha hooks post-edit --memory-key "${this.config.memoryKey}/${key}" --data '${JSON.stringify(data)}'`,
        { timeout: this.config.hookTimeout }
      );
    } catch (error) {
      console.warn(`Failed to store in memory: ${key}`, error.message);
    }
  }

  async restoreSessionContext() {
    try {
      const result = await execAsync(
        `npx claude-flow@alpha hooks session-restore --session-id "${this.config.swarmId}"`,
        { timeout: this.config.hookTimeout }
      );
      return result.stdout;
    } catch (error) {
      console.warn('Failed to restore session context:', error.message);
      return null;
    }
  }

  async notifyHook(eventType, data) {
    try {
      await execAsync(
        `npx claude-flow@alpha hooks notify --message "${eventType}: ${JSON.stringify(data)}"`,
        { timeout: this.config.hookTimeout }
      );
    } catch (error) {
      console.warn(`Failed to notify hook: ${eventType}`, error.message);
    }
  }
}

module.exports = EcosystemCoordinator;