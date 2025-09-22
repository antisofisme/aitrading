#!/usr/bin/env node

/**
 * MCP Server for Mermaid.js Diagram Generation
 * Integrates with Claude Flow for AI Trading System Documentation
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import { execSync } from 'child_process';
import fs from 'fs/promises';
import path from 'path';
import { MermaidDiagramGenerator } from '../diagram-generator/mermaid-generator.js';
import { CodeAnalyzer } from '../code-analysis/analyzer.js';
import { TradingSystemTemplates } from '../templates/trading-templates.js';
import { ClaudeFlowIntegration } from '../hooks/claude-flow-integration.js';

class MermaidMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'mermaid-diagram-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.diagramGenerator = new MermaidDiagramGenerator();
    this.codeAnalyzer = new CodeAnalyzer();
    this.templates = new TradingSystemTemplates();
    this.claudeFlow = new ClaudeFlowIntegration();

    this.setupToolHandlers();
  }

  setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'generate_diagram',
          description: 'Generate Mermaid.js diagram from code or specifications',
          inputSchema: {
            type: 'object',
            properties: {
              type: {
                type: 'string',
                enum: ['flowchart', 'sequence', 'class', 'er', 'gitgraph', 'gantt', 'mindmap', 'timeline', 'sankey'],
                description: 'Type of diagram to generate'
              },
              source: {
                type: 'string',
                description: 'Source code, file path, or specification text'
              },
              template: {
                type: 'string',
                enum: ['trading-pipeline', 'risk-management', 'data-flow', 'microservices', 'ml-pipeline'],
                description: 'Trading system template to use'
              },
              outputPath: {
                type: 'string',
                description: 'Output path for generated diagram'
              },
              format: {
                type: 'string',
                enum: ['mermaid', 'svg', 'png', 'pdf'],
                description: 'Output format'
              },
              autoAnalyze: {
                type: 'boolean',
                description: 'Auto-analyze code for relationships'
              }
            },
            required: ['type']
          }
        },
        {
          name: 'analyze_codebase',
          description: 'Analyze entire codebase for system architecture',
          inputSchema: {
            type: 'object',
            properties: {
              rootPath: {
                type: 'string',
                description: 'Root path of codebase to analyze'
              },
              includePatterns: {
                type: 'array',
                items: { type: 'string' },
                description: 'File patterns to include'
              },
              excludePatterns: {
                type: 'array',
                items: { type: 'string' },
                description: 'File patterns to exclude'
              },
              diagramTypes: {
                type: 'array',
                items: { type: 'string' },
                description: 'Types of diagrams to generate'
              }
            },
            required: ['rootPath']
          }
        },
        {
          name: 'update_documentation',
          description: 'Update documentation with latest diagrams',
          inputSchema: {
            type: 'object',
            properties: {
              docPath: {
                type: 'string',
                description: 'Documentation directory path'
              },
              autoRefresh: {
                type: 'boolean',
                description: 'Auto-refresh on code changes'
              },
              integrateClaude: {
                type: 'boolean',
                description: 'Integrate with Claude Flow hooks'
              }
            },
            required: ['docPath']
          }
        },
        {
          name: 'setup_hooks',
          description: 'Setup Claude Flow hooks for automatic diagram generation',
          inputSchema: {
            type: 'object',
            properties: {
              hookTypes: {
                type: 'array',
                items: { type: 'string' },
                description: 'Types of hooks to setup'
              },
              watchPaths: {
                type: 'array',
                items: { type: 'string' },
                description: 'Paths to watch for changes'
              },
              triggerEvents: {
                type: 'array',
                items: { type: 'string' },
                description: 'Events that trigger diagram updates'
              }
            },
            required: ['hookTypes']
          }
        },
        {
          name: 'generate_trading_diagrams',
          description: 'Generate comprehensive trading system diagrams',
          inputSchema: {
            type: 'object',
            properties: {
              systemType: {
                type: 'string',
                enum: ['algorithmic', 'ml-based', 'risk-management', 'portfolio', 'backtesting'],
                description: 'Type of trading system'
              },
              components: {
                type: 'array',
                items: { type: 'string' },
                description: 'System components to include'
              },
              outputDir: {
                type: 'string',
                description: 'Output directory for diagrams'
              },
              includeMetrics: {
                type: 'boolean',
                description: 'Include performance metrics in diagrams'
              }
            },
            required: ['systemType']
          }
        }
      ]
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      try {
        const { name, arguments: args } = request.params;

        switch (name) {
          case 'generate_diagram':
            return await this.handleGenerateDiagram(args);
          case 'analyze_codebase':
            return await this.handleAnalyzeCodebase(args);
          case 'update_documentation':
            return await this.handleUpdateDocumentation(args);
          case 'setup_hooks':
            return await this.handleSetupHooks(args);
          case 'generate_trading_diagrams':
            return await this.handleGenerateTradingDiagrams(args);
          default:
            throw new McpError(ErrorCode.MethodNotFound, `Tool ${name} not found`);
        }
      } catch (error) {
        throw new McpError(ErrorCode.InternalError, error.message);
      }
    });
  }

  async handleGenerateDiagram(args) {
    const { type, source, template, outputPath, format = 'mermaid', autoAnalyze = false } = args;

    let diagramDefinition;

    if (autoAnalyze && source) {
      const analysis = await this.codeAnalyzer.analyzeCode(source);
      diagramDefinition = await this.diagramGenerator.generateFromAnalysis(type, analysis);
    } else if (template) {
      diagramDefinition = await this.templates.generateFromTemplate(type, template, source);
    } else {
      diagramDefinition = await this.diagramGenerator.generateFromSource(type, source);
    }

    if (outputPath) {
      await this.saveDiagram(diagramDefinition, outputPath, format);
    }

    // Store in Claude Flow memory
    await this.claudeFlow.storeInMemory(`diagram_${type}_${Date.now()}`, {
      type,
      definition: diagramDefinition,
      timestamp: new Date().toISOString(),
      source: source?.substring(0, 100) // Store first 100 chars for reference
    });

    return {
      content: [
        {
          type: 'text',
          text: `Generated ${type} diagram successfully${outputPath ? ` and saved to ${outputPath}` : ''}`
        },
        {
          type: 'text',
          text: `\`\`\`mermaid\n${diagramDefinition}\n\`\`\``
        }
      ]
    };
  }

  async handleAnalyzeCodebase(args) {
    const { rootPath, includePatterns = ['**/*.js', '**/*.ts', '**/*.py'], excludePatterns = ['node_modules/**', '.git/**'], diagramTypes = ['flowchart', 'class'] } = args;

    const analysis = await this.codeAnalyzer.analyzeCodebase(rootPath, includePatterns, excludePatterns);
    const diagrams = {};

    for (const diagramType of diagramTypes) {
      diagrams[diagramType] = await this.diagramGenerator.generateFromAnalysis(diagramType, analysis);
    }

    // Store analysis in Claude Flow memory
    await this.claudeFlow.storeInMemory('codebase_analysis', {
      rootPath,
      analysis,
      diagrams,
      timestamp: new Date().toISOString()
    });

    return {
      content: [
        {
          type: 'text',
          text: `Analyzed codebase at ${rootPath}. Found ${analysis.files.length} files, ${analysis.classes.length} classes, ${analysis.functions.length} functions.`
        },
        {
          type: 'text',
          text: `Generated ${Object.keys(diagrams).length} diagram types: ${Object.keys(diagrams).join(', ')}`
        }
      ]
    };
  }

  async handleUpdateDocumentation(args) {
    const { docPath, autoRefresh = false, integrateClaude = true } = args;

    // Get latest diagrams from memory
    const storedDiagrams = await this.claudeFlow.getFromMemory('codebase_analysis');

    if (!storedDiagrams) {
      throw new Error('No diagrams found in memory. Run analyze_codebase first.');
    }

    await fs.mkdir(docPath, { recursive: true });

    for (const [type, definition] of Object.entries(storedDiagrams.diagrams)) {
      const filePath = path.join(docPath, `${type}-diagram.md`);
      const content = this.generateDocumentationContent(type, definition);
      await fs.writeFile(filePath, content, 'utf8');
    }

    if (integrateClaude) {
      await this.claudeFlow.registerHook('post-edit', async (file) => {
        // Re-analyze and update diagrams when code changes
        await this.handleAnalyzeCodebase({ rootPath: path.dirname(file) });
        await this.handleUpdateDocumentation({ docPath, autoRefresh: false, integrateClaude: false });
      });
    }

    return {
      content: [
        {
          type: 'text',
          text: `Updated documentation at ${docPath} with ${Object.keys(storedDiagrams.diagrams).length} diagrams`
        }
      ]
    };
  }

  async handleSetupHooks(args) {
    const { hookTypes, watchPaths = [], triggerEvents = ['file-change', 'commit'] } = args;

    for (const hookType of hookTypes) {
      await this.claudeFlow.registerHook(hookType, async (data) => {
        // Auto-regenerate diagrams on specified events
        if (triggerEvents.includes(data.event)) {
          const analysis = await this.codeAnalyzer.analyzeCodebase(data.path || process.cwd());
          const diagrams = {};

          for (const diagramType of ['flowchart', 'class', 'sequence']) {
            diagrams[diagramType] = await this.diagramGenerator.generateFromAnalysis(diagramType, analysis);
          }

          await this.claudeFlow.storeInMemory('auto_generated_diagrams', {
            diagrams,
            trigger: data.event,
            timestamp: new Date().toISOString()
          });
        }
      });
    }

    return {
      content: [
        {
          type: 'text',
          text: `Setup ${hookTypes.length} Claude Flow hooks for automatic diagram generation`
        }
      ]
    };
  }

  async handleGenerateTradingDiagrams(args) {
    const { systemType, components = [], outputDir = './docs/diagrams', includeMetrics = false } = args;

    const tradingDiagrams = await this.templates.generateTradingSystemDiagrams(
      systemType,
      components,
      includeMetrics
    );

    await fs.mkdir(outputDir, { recursive: true });

    for (const [name, definition] of Object.entries(tradingDiagrams)) {
      await this.saveDiagram(definition, path.join(outputDir, `${name}.mmd`), 'mermaid');
    }

    // Store in Claude Flow memory with trading context
    await this.claudeFlow.storeInMemory(`trading_system_${systemType}`, {
      systemType,
      components,
      diagrams: tradingDiagrams,
      includeMetrics,
      timestamp: new Date().toISOString()
    });

    return {
      content: [
        {
          type: 'text',
          text: `Generated ${Object.keys(tradingDiagrams).length} trading system diagrams for ${systemType} system`
        },
        {
          type: 'text',
          text: `Diagrams saved to: ${outputDir}`
        }
      ]
    };
  }

  async saveDiagram(definition, outputPath, format) {
    const dir = path.dirname(outputPath);
    await fs.mkdir(dir, { recursive: true });

    if (format === 'mermaid') {
      await fs.writeFile(outputPath, definition, 'utf8');
    } else {
      // For other formats, use mermaid-cli if available
      try {
        const tempFile = `${outputPath}.mmd`;
        await fs.writeFile(tempFile, definition, 'utf8');

        const outputFile = outputPath.replace(/\.mmd$/, `.${format}`);
        execSync(`npx @mermaid-js/mermaid-cli -i ${tempFile} -o ${outputFile}`, {
          stdio: 'inherit'
        });

        await fs.unlink(tempFile);
      } catch (error) {
        console.warn(`Could not convert to ${format}:`, error.message);
        await fs.writeFile(outputPath, definition, 'utf8');
      }
    }
  }

  generateDocumentationContent(type, definition) {
    return `# ${type.charAt(0).toUpperCase() + type.slice(1)} Diagram

Auto-generated on: ${new Date().toISOString()}

\`\`\`mermaid
${definition}
\`\`\`

---
*This diagram is automatically updated when code changes. Do not edit manually.*
`;
  }

  async start() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Mermaid MCP Server started');
  }
}

// Start server if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const server = new MermaidMCPServer();
  server.start().catch(console.error);
}

export { MermaidMCPServer };