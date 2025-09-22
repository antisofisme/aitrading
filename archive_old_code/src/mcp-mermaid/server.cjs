const express = require('express');
const WebSocket = require('ws');
const { SystemArchitectureDiagrammer } = require('../diagrams/system-architecture');
const { DiagramGenerator } = require('../diagrams/generator');
const { TradingTemplates } = require('../templates/trading-templates');
const { CodeAnalyzer } = require('../analysis/code-analyzer');
const path = require('path');
const fs = require('fs').promises;

class MCPMermaidServer {
  constructor(options = {}) {
    this.port = options.port || 3000;
    this.projectRoot = options.projectRoot || process.cwd();
    this.app = express();
    this.server = null;
    this.wss = null;
    this.isRunning = false;

    this.diagrammer = new SystemArchitectureDiagrammer({ projectRoot: this.projectRoot });
    this.generator = new DiagramGenerator();
    this.templates = new TradingTemplates();
    this.analyzer = new CodeAnalyzer({ projectRoot: this.projectRoot });

    this._setupMiddleware();
    this._setupRoutes();
    this._setupMCPTools();
  }

  _setupMiddleware() {
    this.app.use(express.json());
    this.app.use(express.static(path.join(this.projectRoot, 'docs/diagrams')));

    // CORS for Claude Flow integration
    this.app.use((req, res, next) => {
      res.header('Access-Control-Allow-Origin', '*');
      res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
      res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization, Claude-Flow-Session');
      if (req.method === 'OPTIONS') {
        res.sendStatus(200);
      } else {
        next();
      }
    });
  }

  _setupRoutes() {
    // Health check
    this.app.get('/health', (req, res) => {
      res.json({
        status: 'ok',
        server: 'MCP Mermaid',
        version: '1.0.0',
        uptime: process.uptime(),
        memory: process.memoryUsage()
      });
    });

    // Generate diagram endpoint
    this.app.post('/generate', async (req, res) => {
      try {
        const { type = 'system', options = {} } = req.body;
        const result = await this._generateDiagram(type, options);
        res.json(result);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    // Analyze project endpoint
    this.app.get('/analyze', async (req, res) => {
      try {
        const analysis = await this.analyzer.analyzeProject();
        res.json(analysis);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    // Get templates
    this.app.get('/templates', (req, res) => {
      res.json({
        available: Object.keys(this.templates.templates),
        templates: this.templates.templates
      });
    });

    // Export diagram
    this.app.post('/export', async (req, res) => {
      try {
        const { diagram, format = 'svg', filename } = req.body;
        const result = await this._exportDiagram(diagram, format, filename);
        res.json(result);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    // Get status
    this.app.get('/status', async (req, res) => {
      try {
        const status = await this._getSystemStatus();
        res.json(status);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });
  }

  _setupMCPTools() {
    // MCP tool definitions for Claude Flow
    this.mcpTools = {
      mermaid_generate: {
        name: 'mermaid_generate',
        description: 'Generate Mermaid diagrams for AI trading system architecture',
        inputSchema: {
          type: 'object',
          properties: {
            type: {
              type: 'string',
              enum: ['system', 'dataflow', 'components', 'sequence', 'all'],
              description: 'Type of diagram to generate'
            },
            output_dir: {
              type: 'string',
              description: 'Output directory for diagrams (default: ./docs/diagrams)'
            },
            format: {
              type: 'string',
              enum: ['mermaid', 'svg', 'png', 'pdf'],
              description: 'Output format'
            }
          },
          required: ['type']
        },
        handler: this._handleGenerateTool.bind(this)
      },

      mermaid_analyze: {
        name: 'mermaid_analyze',
        description: 'Analyze project structure for diagram generation',
        inputSchema: {
          type: 'object',
          properties: {
            path: {
              type: 'string',
              description: 'Project path to analyze (default: current directory)'
            },
            include_patterns: {
              type: 'array',
              items: { type: 'string' },
              description: 'File patterns to include in analysis'
            }
          }
        },
        handler: this._handleAnalyzeTool.bind(this)
      },

      mermaid_export: {
        name: 'mermaid_export',
        description: 'Export Mermaid diagrams to various formats',
        inputSchema: {
          type: 'object',
          properties: {
            input_file: {
              type: 'string',
              description: 'Input Mermaid file path'
            },
            format: {
              type: 'string',
              enum: ['svg', 'png', 'pdf', 'html'],
              description: 'Export format'
            },
            output_file: {
              type: 'string',
              description: 'Output file path'
            }
          },
          required: ['input_file', 'format']
        },
        handler: this._handleExportTool.bind(this)
      },

      mermaid_watch: {
        name: 'mermaid_watch',
        description: 'Watch for file changes and auto-update diagrams',
        inputSchema: {
          type: 'object',
          properties: {
            enabled: {
              type: 'boolean',
              description: 'Enable or disable file watching'
            },
            patterns: {
              type: 'array',
              items: { type: 'string' },
              description: 'File patterns to watch'
            }
          },
          required: ['enabled']
        },
        handler: this._handleWatchTool.bind(this)
      },

      mermaid_status: {
        name: 'mermaid_status',
        description: 'Get system status and available diagrams',
        inputSchema: {
          type: 'object',
          properties: {
            detailed: {
              type: 'boolean',
              description: 'Include detailed status information'
            }
          }
        },
        handler: this._handleStatusTool.bind(this)
      }
    };
  }

  async _handleGenerateTool(params) {
    try {
      const { type, output_dir, format = 'mermaid' } = params;
      const result = await this._generateDiagram(type, { output_dir, format });

      return {
        success: true,
        type: type,
        result: result,
        message: `Generated ${type} diagram successfully`
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  async _handleAnalyzeTool(params) {
    try {
      const { path: projectPath, include_patterns } = params;
      const analysis = await this.analyzer.analyzeProject(projectPath, include_patterns);

      return {
        success: true,
        analysis: analysis,
        summary: {
          modules: analysis.modules.length,
          functions: analysis.functions.length,
          classes: analysis.classes.length,
          dependencies: analysis.dependencies.length
        }
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  async _handleExportTool(params) {
    try {
      const { input_file, format, output_file } = params;
      const result = await this._exportDiagram(input_file, format, output_file);

      return {
        success: true,
        input: input_file,
        output: result.path,
        format: format
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  async _handleWatchTool(params) {
    try {
      const { enabled, patterns } = params;

      if (enabled) {
        await this._startWatching(patterns);
        return {
          success: true,
          watching: true,
          patterns: patterns || ['**/*.js', '**/*.ts', '**/*.py']
        };
      } else {
        await this._stopWatching();
        return {
          success: true,
          watching: false
        };
      }
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  async _handleStatusTool(params) {
    try {
      const { detailed = false } = params;
      const status = await this._getSystemStatus(detailed);

      return {
        success: true,
        status: status
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  async _generateDiagram(type, options = {}) {
    const { output_dir, format = 'mermaid' } = options;

    switch (type) {
      case 'system':
        return await this.diagrammer.generateSystemOverview();
      case 'dataflow':
        return await this.diagrammer.generateDataFlow();
      case 'components':
        return await this.diagrammer.generateComponentDiagram();
      case 'sequence':
        return await this.diagrammer.generateSequenceDiagram();
      case 'all':
        const results = await Promise.all([
          this.diagrammer.generateSystemOverview(),
          this.diagrammer.generateDataFlow(),
          this.diagrammer.generateComponentDiagram(),
          this.diagrammer.generateSequenceDiagram()
        ]);
        return {
          system: results[0],
          dataflow: results[1],
          components: results[2],
          sequence: results[3],
          total: results.length
        };
      default:
        throw new Error(`Unknown diagram type: ${type}`);
    }
  }

  async _exportDiagram(input, format, output) {
    // In a real implementation, you would use mermaid-cli or similar
    // For now, we'll create placeholder exports
    const content = typeof input === 'string' ?
      await fs.readFile(input, 'utf8') : input;

    const outputPath = output || `./docs/diagrams/export.${format}`;

    if (format === 'html') {
      const htmlContent = `<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
  <title>Mermaid Diagram</title>
</head>
<body>
  <div class="mermaid">
${content}
  </div>
  <script>
    mermaid.initialize({startOnLoad:true});
  </script>
</body>
</html>`;
      await fs.writeFile(outputPath, htmlContent, 'utf8');
    } else {
      await fs.writeFile(outputPath, content, 'utf8');
    }

    return { path: outputPath, format };
  }

  async _getSystemStatus(detailed = false) {
    const status = {
      server: {
        running: this.isRunning,
        port: this.port,
        uptime: process.uptime()
      },
      diagrams: {
        available: [],
        count: 0
      },
      project: {
        root: this.projectRoot,
        analyzed: false
      }
    };

    try {
      const diagramsDir = path.join(this.projectRoot, 'docs/diagrams');
      const files = await fs.readdir(diagramsDir);
      status.diagrams.available = files.filter(f => f.endsWith('.mmd') || f.endsWith('.md'));
      status.diagrams.count = status.diagrams.available.length;
    } catch (error) {
      // Directory doesn't exist
    }

    if (detailed) {
      try {
        const analysis = await this.analyzer.analyzeProject();
        status.project.analyzed = true;
        status.project.modules = analysis.modules.length;
        status.project.functions = analysis.functions.length;
        status.project.classes = analysis.classes.length;
      } catch (error) {
        status.project.error = error.message;
      }
    }

    return status;
  }

  async _startWatching(patterns) {
    // File watching implementation would go here
    console.log('📁 File watching enabled for patterns:', patterns);
  }

  async _stopWatching() {
    // Stop file watching implementation would go here
    console.log('🛑 File watching disabled');
  }

  async start(port = this.port) {
    this.port = port;

    return new Promise((resolve, reject) => {
      this.server = this.app.listen(port, (err) => {
        if (err) {
          reject(err);
          return;
        }

        this.isRunning = true;

        // Setup WebSocket server for real-time updates
        this.wss = new WebSocket.Server({ server: this.server });

        this.wss.on('connection', (ws) => {
          console.log('🔗 WebSocket client connected');

          ws.on('message', async (message) => {
            try {
              const data = JSON.parse(message);
              const result = await this._handleWebSocketMessage(data);
              ws.send(JSON.stringify(result));
            } catch (error) {
              ws.send(JSON.stringify({ error: error.message }));
            }
          });

          ws.on('close', () => {
            console.log('🔗 WebSocket client disconnected');
          });
        });

        console.log(`🚀 MCP Mermaid Server started on port ${port}`);
        resolve();
      });
    });
  }

  async _handleWebSocketMessage(data) {
    const { tool, params } = data;

    if (this.mcpTools[tool]) {
      return await this.mcpTools[tool].handler(params);
    } else {
      throw new Error(`Unknown tool: ${tool}`);
    }
  }

  async stop() {
    if (this.server) {
      return new Promise((resolve) => {
        this.server.close(() => {
          this.isRunning = false;
          console.log('🛑 MCP Mermaid Server stopped');
          resolve();
        });
      });
    }
  }

  // MCP Tool Registration for Claude Flow
  getMCPTools() {
    return Object.values(this.mcpTools);
  }

  // Claude Flow Integration
  async handleClaudeFlowRequest(toolName, params) {
    if (this.mcpTools[toolName]) {
      return await this.mcpTools[toolName].handler(params);
    } else {
      throw new Error(`Tool not found: ${toolName}`);
    }
  }
}

// Export for CLI usage
if (require.main === module) {
  const server = new MCPMermaidServer();
  const port = parseInt(process.argv[2]) || 3000;

  server.start(port).catch(error => {
    console.error('❌ Failed to start server:', error.message);
    process.exit(1);
  });

  // Graceful shutdown
  process.on('SIGINT', async () => {
    console.log('\n🛑 Shutting down server...');
    await server.stop();
    process.exit(0);
  });
}

module.exports = { MCPMermaidServer };