/**
 * CollaborativeEcosystem - Main orchestrator for the collaborative documentation ecosystem
 * Coordinates all agents, integrations, and real-time responses
 */

const EcosystemCoordinator = require('./agents/EcosystemCoordinator');
const ChangeMonitor = require('./triggers/ChangeMonitor');
const ContextDetector = require('./detectors/ContextDetector');
const MermaidIntegrator = require('./integrations/MermaidIntegrator');
const HookManager = require('./hooks/HookManager');
const EcosystemConfig = require('./config/EcosystemConfig');

const { EventEmitter } = require('events');
const fs = require('fs').promises;
const path = require('path');

class CollaborativeEcosystem extends EventEmitter {
  constructor(config = {}) {
    super();

    this.config = new EcosystemConfig(config.configPath);
    this.coordinator = null;
    this.changeMonitor = null;
    this.contextDetector = null;
    this.mermaidIntegrator = null;
    this.hookManager = null;

    this.isRunning = false;
    this.initializationPromise = null;
    this.projectContext = null;
    this.statistics = {
      startTime: null,
      tasksProcessed: 0,
      diagramsGenerated: 0,
      agentsTriggered: 0,
      errorsEncountered: 0
    };
  }

  /**
   * Initialize the collaborative ecosystem
   */
  async initialize() {
    if (this.initializationPromise) {
      return this.initializationPromise;
    }

    this.initializationPromise = this._performInitialization();
    return this.initializationPromise;
  }

  async _performInitialization() {
    try {
      console.log('🚀 Initializing Collaborative Documentation Ecosystem...');

      // Load configuration
      await this.config.loadConfig();

      // Initialize hook manager first (needed for coordination)
      this.hookManager = new HookManager(this.config.get('hooks'));
      await this.hookManager.initialize();

      // Execute pre-task hook for ecosystem setup
      await this.hookManager.executePreTaskHook(
        'Initialize collaborative documentation ecosystem'
      );

      // Initialize context detector
      this.contextDetector = new ContextDetector(this.config.get('contextDetection'));
      this.projectContext = await this.contextDetector.detectProjectContext();

      // Initialize components based on configuration
      await this.initializeComponents();

      // Setup event coordination
      this.setupEventCoordination();

      // Setup ecosystem monitoring
      this.setupMonitoring();

      this.statistics.startTime = new Date().toISOString();

      console.log('✅ Collaborative Documentation Ecosystem initialized successfully');
      console.log(`📊 Project Type: ${this.projectContext.type} (Confidence: ${this.projectContext.confidence}%)`);

      // Emit initialization complete event
      this.emit('ecosystem-initialized', {
        projectContext: this.projectContext,
        enabledAgents: this.config.getEnabledAgents().map(a => a.id)
      });

      return true;
    } catch (error) {
      console.error('❌ Failed to initialize collaborative ecosystem:', error);
      this.emit('error', error);
      throw error;
    }
  }

  /**
   * Initialize ecosystem components
   */
  async initializeComponents() {
    console.log('🔧 Initializing ecosystem components...');

    // Initialize coordinator
    this.coordinator = new EcosystemCoordinator({
      swarmId: this.config.get('mcp.swarmId'),
      projectContext: this.projectContext,
      config: this.config.get('ecosystem')
    });
    await this.coordinator.initialize();

    // Initialize change monitor if enabled
    if (this.config.get('monitoring.enabled')) {
      this.changeMonitor = new ChangeMonitor(this.config.get('monitoring'));
      await this.changeMonitor.startMonitoring();
    }

    // Initialize Mermaid integrator if enabled
    if (this.config.get('mermaid.enabled')) {
      this.mermaidIntegrator = new MermaidIntegrator(this.config.get('mermaid'));
      await this.mermaidIntegrator.initialize();
    }

    console.log('✅ All components initialized successfully');
  }

  /**
   * Setup event coordination between components
   */
  setupEventCoordination() {
    console.log('🔗 Setting up event coordination...');

    // Change monitor events
    if (this.changeMonitor) {
      this.changeMonitor.on('code-change', this.handleCodeChange.bind(this));
      this.changeMonitor.on('batch-changes', this.handleBatchChanges.bind(this));
      this.changeMonitor.on('group-changes', this.handleGroupChanges.bind(this));
      this.changeMonitor.on('error', this.handleComponentError.bind(this));
    }

    // Coordinator events
    if (this.coordinator) {
      this.coordinator.on('agent-spawned', this.handleAgentSpawned.bind(this));
      this.coordinator.on('task-completed', this.handleTaskCompleted.bind(this));
      this.coordinator.on('mermaid-generation', this.handleMermaidRequest.bind(this));
      this.coordinator.on('error', this.handleComponentError.bind(this));
    }

    // Hook manager events
    if (this.hookManager) {
      this.hookManager.on('hook-executed', this.handleHookExecuted.bind(this));
      this.hookManager.on('hook-error', this.handleHookError.bind(this));
    }

    // Mermaid integrator events
    if (this.mermaidIntegrator) {
      this.mermaidIntegrator.on('diagram-generated', this.handleDiagramGenerated.bind(this));
      this.mermaidIntegrator.on('error', this.handleComponentError.bind(this));
    }
  }

  /**
   * Setup ecosystem monitoring and health checks
   */
  setupMonitoring() {
    // Health check interval
    setInterval(() => {
      this.performHealthCheck();
    }, 60000); // Every minute

    // Statistics update interval
    setInterval(() => {
      this.updateStatistics();
    }, 30000); // Every 30 seconds

    // Memory cleanup interval
    setInterval(() => {
      this.performCleanup();
    }, 300000); // Every 5 minutes
  }

  /**
   * Start the collaborative ecosystem
   */
  async start() {
    if (this.isRunning) {
      console.warn('⚠️ Ecosystem is already running');
      return;
    }

    try {
      // Ensure initialization is complete
      await this.initialize();

      console.log('🎯 Starting collaborative documentation ecosystem...');

      // Start components
      if (this.changeMonitor) {
        await this.changeMonitor.startMonitoring();
      }

      this.isRunning = true;

      // Notify about startup
      await this.hookManager.executeNotificationHook(
        'Collaborative ecosystem started successfully'
      );

      console.log('🚀 Collaborative ecosystem is now running');
      this.emit('ecosystem-started');

      // Process any initial tasks based on project context
      await this.processInitialTasks();

    } catch (error) {
      console.error('❌ Failed to start ecosystem:', error);
      this.emit('error', error);
      throw error;
    }
  }

  /**
   * Stop the collaborative ecosystem
   */
  async stop() {
    if (!this.isRunning) {
      console.warn('⚠️ Ecosystem is not running');
      return;
    }

    try {
      console.log('⏹️ Stopping collaborative ecosystem...');

      // Stop change monitoring
      if (this.changeMonitor) {
        await this.changeMonitor.stopMonitoring();
      }

      // Execute session end hook
      if (this.hookManager) {
        await this.hookManager.executeSessionEndHook(true);
      }

      this.isRunning = false;

      console.log('✅ Collaborative ecosystem stopped successfully');
      this.emit('ecosystem-stopped');

    } catch (error) {
      console.error('❌ Failed to stop ecosystem gracefully:', error);
      this.emit('error', error);
      throw error;
    }
  }

  /**
   * Event handlers
   */
  async handleCodeChange(changeEvent) {
    try {
      this.statistics.tasksProcessed++;

      console.log(`📝 Processing code change: ${changeEvent.relativePath}`);

      // Route to coordinator for agent handling
      await this.coordinator.handleCodeChange(changeEvent);

      // Execute post-edit hook
      await this.hookManager.executePostEditHook(
        changeEvent.filePath,
        `ecosystem/changes/${changeEvent.id}`,
        { changeType: changeEvent.type, impact: changeEvent.impact }
      );

      // Check if Mermaid diagram update is needed
      if (changeEvent.impact?.includes('mermaid-diagram')) {
        await this.handleMermaidRequest({
          type: 'auto-update',
          changeEvent
        });
      }

      this.emit('change-processed', changeEvent);

    } catch (error) {
      this.statistics.errorsEncountered++;
      console.error('❌ Failed to handle code change:', error);
      this.emit('error', error);
    }
  }

  async handleBatchChanges(batchData) {
    try {
      console.log(`📦 Processing batch of ${batchData.changes?.length || 0} changes`);

      // Process batch through coordinator
      for (const [groupKey, changes] of batchData.entries()) {
        await this.coordinator.handleCodeChange({
          type: 'batch',
          groupKey,
          changes,
          impact: batchData.impact || []
        });
      }

      this.statistics.tasksProcessed += batchData.changes?.length || 0;
      this.emit('batch-processed', batchData);

    } catch (error) {
      this.statistics.errorsEncountered++;
      console.error('❌ Failed to handle batch changes:', error);
      this.emit('error', error);
    }
  }

  async handleGroupChanges(groupData) {
    try {
      console.log(`🔄 Processing grouped changes: ${groupData.groupKey}`);

      // Process group changes with specialized handling
      await this.coordinator.handleCodeChange({
        type: 'group',
        ...groupData
      });

      this.emit('group-processed', groupData);

    } catch (error) {
      this.statistics.errorsEncountered++;
      console.error('❌ Failed to handle group changes:', error);
      this.emit('error', error);
    }
  }

  async handleAgentSpawned(agentData) {
    try {
      this.statistics.agentsTriggered++;

      console.log(`🤖 Agent spawned: ${agentData.type} (${agentData.id})`);

      // Notify hook manager
      this.hookManager.emit('agent-spawned', agentData);

      this.emit('agent-spawned', agentData);

    } catch (error) {
      console.error('❌ Failed to handle agent spawned event:', error);
      this.emit('error', error);
    }
  }

  async handleTaskCompleted(taskData) {
    try {
      console.log(`✅ Task completed: ${taskData.id}`);

      // Notify hook manager
      this.hookManager.emit('task-completed', taskData);

      this.emit('task-completed', taskData);

    } catch (error) {
      console.error('❌ Failed to handle task completed event:', error);
      this.emit('error', error);
    }
  }

  async handleMermaidRequest(requestData) {
    try {
      if (!this.mermaidIntegrator) {
        console.warn('⚠️ Mermaid integrator not available');
        return;
      }

      console.log(`🎨 Processing Mermaid request: ${requestData.type}`);

      const diagramResult = await this.mermaidIntegrator.generateDiagram({
        type: requestData.type,
        title: requestData.title || 'Auto-generated Diagram',
        data: requestData.data || {},
        context: this.projectContext,
        projectType: this.projectContext.type
      });

      this.statistics.diagramsGenerated++;
      this.emit('diagram-generated', diagramResult);

    } catch (error) {
      this.statistics.errorsEncountered++;
      console.error('❌ Failed to handle Mermaid request:', error);
      this.emit('error', error);
    }
  }

  async handleDiagramGenerated(diagramData) {
    try {
      console.log(`📊 Diagram generated: ${diagramData.type} - ${diagramData.title}`);

      // Store diagram metadata in memory
      await this.hookManager.executePostEditHook(
        diagramData.filePath,
        `ecosystem/diagrams/${Date.now()}`,
        { diagramType: diagramData.type, generatedAt: new Date().toISOString() }
      );

      this.emit('diagram-completed', diagramData);

    } catch (error) {
      console.error('❌ Failed to handle diagram generated event:', error);
      this.emit('error', error);
    }
  }

  async handleComponentError(error) {
    this.statistics.errorsEncountered++;
    console.error('⚠️ Component error:', error);
    this.emit('component-error', error);
  }

  async handleHookExecuted(hookData) {
    // Hook execution logging and monitoring
    if (hookData.type === 'post-task') {
      this.statistics.tasksProcessed++;
    }
  }

  async handleHookError(errorData) {
    this.statistics.errorsEncountered++;
    console.warn(`⚠️ Hook error: ${errorData.type}`, errorData.error);
  }

  /**
   * Process initial tasks based on project context
   */
  async processInitialTasks() {
    try {
      console.log('🎯 Processing initial tasks based on project context...');

      const recommendations = this.projectContext.recommendations || [];

      for (const recommendation of recommendations) {
        if (recommendation.priority === 'high') {
          console.log(`📋 Processing high-priority recommendation: ${recommendation.description}`);

          // Trigger appropriate agent
          await this.coordinator.triggerAgent(
            recommendation.agent,
            {
              type: 'initial-analysis',
              description: recommendation.description,
              projectContext: this.projectContext
            }
          );
        }
      }

    } catch (error) {
      console.warn('⚠️ Failed to process initial tasks:', error.message);
    }
  }

  /**
   * Monitoring and maintenance
   */
  async performHealthCheck() {
    try {
      const health = {
        ecosystem: this.isRunning,
        coordinator: this.coordinator?.isInitialized || false,
        changeMonitor: this.changeMonitor?.isMonitoring || false,
        mermaidIntegrator: this.mermaidIntegrator?.isInitialized || false,
        hookManager: this.hookManager?.isInitialized || false,
        timestamp: new Date().toISOString()
      };

      // Check for any unhealthy components
      const unhealthyComponents = Object.entries(health)
        .filter(([key, value]) => key !== 'timestamp' && !value)
        .map(([key]) => key);

      if (unhealthyComponents.length > 0) {
        console.warn(`⚠️ Unhealthy components detected: ${unhealthyComponents.join(', ')}`);
        this.emit('health-warning', { unhealthyComponents, health });
      }

      this.emit('health-check', health);

    } catch (error) {
      console.error('❌ Health check failed:', error);
      this.emit('error', error);
    }
  }

  updateStatistics() {
    const currentTime = new Date().toISOString();
    const uptime = this.statistics.startTime ?
      Date.now() - new Date(this.statistics.startTime).getTime() : 0;

    this.statistics.uptime = uptime;
    this.statistics.lastUpdate = currentTime;

    this.emit('statistics-updated', this.statistics);
  }

  async performCleanup() {
    try {
      // Cleanup old change events, hook history, etc.
      console.log('🧹 Performing ecosystem cleanup...');

      // Implementation for cleanup would go here

    } catch (error) {
      console.warn('⚠️ Cleanup failed:', error.message);
    }
  }

  /**
   * Public API methods
   */
  getStatus() {
    return {
      isRunning: this.isRunning,
      projectContext: this.projectContext,
      statistics: this.statistics,
      enabledAgents: this.config.getEnabledAgents().map(a => a.id),
      components: {
        coordinator: !!this.coordinator,
        changeMonitor: !!this.changeMonitor,
        mermaidIntegrator: !!this.mermaidIntegrator,
        hookManager: !!this.hookManager
      }
    };
  }

  getStatistics() {
    return { ...this.statistics };
  }

  getProjectContext() {
    return this.projectContext;
  }

  getConfiguration() {
    return this.config.exportConfig();
  }

  async updateConfiguration(updates) {
    await this.config.updateConfig(updates);
    this.emit('configuration-updated', updates);
  }

  // Method to manually trigger agents
  async triggerAgent(agentId, taskData) {
    if (!this.coordinator) {
      throw new Error('Coordinator not initialized');
    }

    return this.coordinator.triggerAgent(agentId, taskData);
  }

  // Method to manually generate diagrams
  async generateDiagram(diagramRequest) {
    if (!this.mermaidIntegrator) {
      throw new Error('Mermaid integrator not available');
    }

    return this.mermaidIntegrator.generateDiagram(diagramRequest);
  }
}

module.exports = CollaborativeEcosystem;