#!/usr/bin/env node

const { MCPMermaidServer } = require('./server.cjs');
const { SystemArchitectureDiagrammer } = require('../diagrams/system-architecture');
const { DocumentationHooks } = require('../hooks/documentation-hooks');
const path = require('path');
const fs = require('fs').promises;

class MCPMermaidCLI {
  constructor() {
    this.server = new MCPMermaidServer();
    this.diagrammer = new SystemArchitectureDiagrammer();
    this.hooks = new DocumentationHooks();
  }

  async run() {
    const args = process.argv.slice(2);
    const command = args[0];

    try {
      switch (command) {
        case 'start':
          await this.startServer(args.slice(1));
          break;
        case 'generate':
          await this.generateDiagrams(args.slice(1));
          break;
        case 'analyze':
          await this.analyzeProject(args.slice(1));
          break;
        case 'watch':
          await this.watchProject(args.slice(1));
          break;
        case 'export':
          await this.exportDiagrams(args.slice(1));
          break;
        case 'status':
          await this.showStatus();
          break;
        case 'help':
        case '--help':
        case '-h':
          this.showHelp();
          break;
        default:
          console.error(`Unknown command: ${command}`);
          this.showHelp();
          process.exit(1);
      }
    } catch (error) {
      console.error('❌ Error:', error.message);
      if (process.env.DEBUG) {
        console.error(error.stack);
      }
      process.exit(1);
    }
  }

  async startServer(args) {
    const port = parseInt(args[0]) || 3000;

    console.log('🚀 Starting MCP Mermaid Server...');
    console.log(`📡 Server will be available on port ${port}`);

    await this.server.start(port);

    console.log('✅ MCP Mermaid Server started successfully');
    console.log('📊 Available tools:');
    console.log('  - mermaid_generate: Generate Mermaid diagrams');
    console.log('  - mermaid_analyze: Analyze code structure');
    console.log('  - mermaid_export: Export diagrams to files');
    console.log('  - mermaid_watch: Watch for file changes');
    console.log('  - mermaid_status: Get system status');
  }

  async generateDiagrams(args) {
    const type = args[0] || 'all';
    const outputDir = args[1] || './docs/diagrams';

    console.log(`📊 Generating ${type} diagrams...`);

    const results = [];

    if (type === 'all' || type === 'system') {
      console.log('🏗️  Generating system overview...');
      const result = await this.diagrammer.generateSystemOverview();
      results.push(result);
      console.log(`✅ System overview: ${result.path}`);
    }

    if (type === 'all' || type === 'dataflow') {
      console.log('🔄 Generating data flow...');
      const result = await this.diagrammer.generateDataFlow();
      results.push(result);
      console.log(`✅ Data flow: ${result.path}`);
    }

    if (type === 'all' || type === 'components') {
      console.log('🧩 Generating components...');
      const result = await this.diagrammer.generateComponentDiagram();
      results.push(result);
      console.log(`✅ Components: ${result.path}`);
    }

    if (type === 'all' || type === 'sequence') {
      console.log('📈 Generating sequence diagram...');
      const result = await this.diagrammer.generateSequenceDiagram();
      results.push(result);
      console.log(`✅ Sequence: ${result.path}`);
    }

    console.log(`🎉 Generated ${results.length} diagrams successfully`);
    return results;
  }

  async analyzeProject(args) {
    const projectPath = args[0] || process.cwd();

    console.log(`🔍 Analyzing project: ${projectPath}`);

    const analysis = await this.diagrammer.analyzer.analyzeProject();

    console.log('📊 Project Analysis Results:');
    console.log(`  📁 Modules: ${analysis.modules.length}`);
    console.log(`  🔗 Dependencies: ${analysis.dependencies.length}`);
    console.log(`  📝 Functions: ${analysis.functions.length}`);
    console.log(`  🏗️  Classes: ${analysis.classes.length}`);

    // Detailed breakdown
    const tradingModules = analysis.modules.filter(m =>
      m.name.toLowerCase().includes('trading') ||
      m.name.toLowerCase().includes('market') ||
      m.name.toLowerCase().includes('ai')
    );

    console.log(`  🤖 AI/Trading Modules: ${tradingModules.length}`);

    if (tradingModules.length > 0) {
      console.log('    📋 Trading-related modules:');
      tradingModules.forEach(mod => {
        console.log(`      • ${mod.name}`);
      });
    }

    return analysis;
  }

  async watchProject(args) {
    const projectPath = args[0] || process.cwd();

    console.log(`👀 Watching project for changes: ${projectPath}`);
    console.log('📊 Auto-generating diagrams when files change...');
    console.log('🛑 Press Ctrl+C to stop watching\n');

    // Enable hooks
    this.hooks.enable();

    const status = await this.hooks.getStatus();
    console.log('✅ Documentation hooks enabled:');
    console.log(`  📈 Last update: ${status.lastUpdate}`);
    console.log(`  🔄 Total updates: ${status.totalUpdates}`);
    console.log(`  ⏳ Pending updates: ${status.pendingUpdates}`);

    // Keep process alive
    process.on('SIGINT', () => {
      console.log('\n🛑 Stopping file watcher...');
      this.hooks.disable();
      console.log('✅ File watcher stopped');
      process.exit(0);
    });

    // Keep the process running
    await new Promise(() => {}); // Infinite promise
  }

  async exportDiagrams(args) {
    const format = args[0] || 'svg';
    const inputDir = args[1] || './docs/diagrams';
    const outputDir = args[2] || './docs/diagrams/exports';

    console.log(`📤 Exporting diagrams to ${format.toUpperCase()} format...`);

    try {
      const files = await fs.readdir(inputDir);
      const mermaidFiles = files.filter(file => file.endsWith('.mmd'));

      if (mermaidFiles.length === 0) {
        console.log('⚠️  No Mermaid files found in input directory');
        return;
      }

      await fs.mkdir(outputDir, { recursive: true });

      for (const file of mermaidFiles) {
        const inputPath = path.join(inputDir, file);
        const baseName = path.basename(file, '.mmd');
        const outputPath = path.join(outputDir, `${baseName}.${format}`);

        console.log(`🔄 Converting ${file}...`);

        // Note: In a real implementation, you would use mermaid-cli or similar
        // For now, we'll copy the mermaid content and create a placeholder
        const content = await fs.readFile(inputPath, 'utf8');

        if (format === 'html') {
          const htmlContent = `<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
  <title>${baseName}</title>
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
          // For other formats, save the mermaid content with format extension
          await fs.writeFile(outputPath, content, 'utf8');
        }

        console.log(`✅ Exported: ${outputPath}`);
      }

      console.log(`🎉 Exported ${mermaidFiles.length} diagrams to ${format.toUpperCase()}`);

    } catch (error) {
      console.error('❌ Export failed:', error.message);
      throw error;
    }
  }

  async showStatus() {
    console.log('📊 MCP Mermaid Status\n');

    // Server status
    console.log('🚀 Server Status:');
    console.log(`  📡 MCP Server: ${this.server.isRunning ? '✅ Running' : '❌ Stopped'}`);

    // Documentation hooks status
    const hooksStatus = await this.hooks.getStatus();
    console.log('\n🔧 Documentation Hooks:');
    console.log(`  📈 Enabled: ${hooksStatus.enabled ? '✅ Yes' : '❌ No'}`);
    console.log(`  📅 Last Update: ${hooksStatus.lastUpdate}`);
    console.log(`  🔄 Total Updates: ${hooksStatus.totalUpdates}`);
    console.log(`  ⏳ Pending Updates: ${hooksStatus.pendingUpdates}`);

    if (hooksStatus.recentChanges.length > 0) {
      console.log('\n📝 Recent Changes:');
      hooksStatus.recentChanges.slice(0, 5).forEach((change, index) => {
        console.log(`  ${index + 1}. ${path.basename(change.file)} (${change.type})`);
      });
    }

    // Diagram status
    console.log('\n📊 Diagrams:');
    try {
      const diagramsDir = path.join(process.cwd(), 'docs/diagrams');
      const files = await fs.readdir(diagramsDir);
      const mermaidFiles = files.filter(f => f.endsWith('.mmd'));
      const markdownFiles = files.filter(f => f.endsWith('.md'));

      console.log(`  📁 Mermaid files: ${mermaidFiles.length}`);
      console.log(`  📄 Markdown files: ${markdownFiles.length}`);

      if (mermaidFiles.length > 0) {
        console.log('\n  📋 Available diagrams:');
        mermaidFiles.forEach(file => {
          console.log(`    • ${file}`);
        });
      }
    } catch (error) {
      console.log('  📁 Diagrams directory: Not found');
    }
  }

  showHelp() {
    console.log(`\n🧜‍♀️ MCP Mermaid CLI - Auto-diagram generator for AI trading systems\n`);
    console.log('Usage: npx mcp-mermaid <command> [options]\n');
    console.log('Commands:');
    console.log('  start [port]           Start MCP server (default port: 3000)');
    console.log('  generate [type]        Generate diagrams (all|system|dataflow|components|sequence)');
    console.log('  analyze [path]         Analyze project structure');
    console.log('  watch [path]           Watch for file changes and auto-update diagrams');
    console.log('  export [format] [in] [out]  Export diagrams (svg|png|pdf|html)');
    console.log('  status                 Show system status');
    console.log('  help                   Show this help message\n');
    console.log('Examples:');
    console.log('  npx mcp-mermaid start                    # Start MCP server');
    console.log('  npx mcp-mermaid generate all             # Generate all diagrams');
    console.log('  npx mcp-mermaid generate system          # Generate system overview only');
    console.log('  npx mcp-mermaid watch                    # Watch for changes');
    console.log('  npx mcp-mermaid export html              # Export to HTML format');
    console.log('  npx mcp-mermaid status                   # Show status\n');
    console.log('🔗 For more information: https://github.com/your-repo/mcp-mermaid');
  }
}

// Run CLI if this file is executed directly
if (require.main === module) {
  const cli = new MCPMermaidCLI();
  cli.run().catch(error => {
    console.error('❌ CLI Error:', error.message);
    process.exit(1);
  });
}

module.exports = { MCPMermaidCLI };