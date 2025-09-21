/**
 * Utility Functions for Mermaid Diagram Processing
 * Common utilities for diagram generation and manipulation
 */

import fs from 'fs/promises';
import path from 'path';
import crypto from 'crypto';

export class DiagramUtils {
  static DIAGRAM_TYPES = [
    'flowchart', 'sequence', 'class', 'er', 'gitgraph',
    'gantt', 'mindmap', 'timeline', 'sankey', 'pie'
  ];

  static TRADING_COMPONENTS = {
    strategy: /strategy|signal|algorithm|indicator/i,
    data: /market|price|feed|ticker|ohlc|quote|data/i,
    risk: /risk|position|size|stop|limit|var|volatility/i,
    execution: /order|trade|execute|broker|fill|execution/i,
    portfolio: /portfolio|asset|allocation|balance|wealth/i,
    analytics: /analytics|metrics|performance|backtest/i
  };

  /**
   * Validate Mermaid diagram syntax
   */
  static validateDiagramSyntax(diagramContent) {
    const errors = [];
    const lines = diagramContent.split('\n');

    // Basic syntax validation
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line || line.startsWith('%%')) continue; // Skip empty lines and comments

      // Check for balanced brackets
      const openBrackets = (line.match(/\[/g) || []).length;
      const closeBrackets = (line.match(/\]/g) || []).length;
      const openParens = (line.match(/\(/g) || []).length;
      const closeParens = (line.match(/\)/g) || []).length;
      const openBraces = (line.match(/\{/g) || []).length;
      const closeBraces = (line.match(/\}/g) || []).length;

      if (openBrackets !== closeBrackets) {
        errors.push(`Line ${i + 1}: Unbalanced square brackets`);
      }
      if (openParens !== closeParens) {
        errors.push(`Line ${i + 1}: Unbalanced parentheses`);
      }
      if (openBraces !== closeBraces) {
        errors.push(`Line ${i + 1}: Unbalanced curly braces`);
      }
    }

    // Check diagram type declaration
    const firstLine = lines.find(line => line.trim() && !line.trim().startsWith('%%'));
    if (firstLine && !this.isValidDiagramType(firstLine.trim())) {
      errors.push('Invalid or missing diagram type declaration');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * Check if diagram type is valid
   */
  static isValidDiagramType(line) {
    return this.DIAGRAM_TYPES.some(type => line.toLowerCase().includes(type));
  }

  /**
   * Sanitize node IDs and labels
   */
  static sanitizeNodeId(id) {
    return id
      .replace(/[^a-zA-Z0-9_]/g, '_')
      .replace(/^(\d)/, '_$1') // Prefix with underscore if starts with number
      .substring(0, 50); // Limit length
  }

  static sanitizeNodeLabel(label) {
    return label
      .replace(/"/g, '\\"')
      .replace(/\n/g, '\\n')
      .substring(0, 100); // Limit length
  }

  /**
   * Generate unique node ID
   */
  static generateNodeId(prefix = 'node', suffix = '') {
    const timestamp = Date.now().toString(36);
    const random = Math.random().toString(36).substring(2, 7);
    return this.sanitizeNodeId(`${prefix}_${timestamp}_${random}${suffix}`);
  }

  /**
   * Extract trading components from code analysis
   */
  static identifyTradingComponents(analysis) {
    const components = {
      strategy: [],
      data: [],
      risk: [],
      execution: [],
      portfolio: [],
      analytics: []
    };

    // Analyze classes
    analysis.classes?.forEach(cls => {
      const className = cls.name.toLowerCase();
      for (const [category, pattern] of Object.entries(this.TRADING_COMPONENTS)) {
        if (pattern.test(className)) {
          components[category].push({
            type: 'class',
            name: cls.name,
            file: cls.file,
            methods: cls.methods?.length || 0
          });
        }
      }
    });

    // Analyze functions
    analysis.functions?.forEach(func => {
      const funcName = func.name.toLowerCase();
      for (const [category, pattern] of Object.entries(this.TRADING_COMPONENTS)) {
        if (pattern.test(funcName)) {
          components[category].push({
            type: 'function',
            name: func.name,
            file: func.file,
            parameters: func.parameters?.length || 0
          });
        }
      }
    });

    return components;
  }

  /**
   * Calculate diagram complexity score
   */
  static calculateComplexity(diagramContent) {
    const lines = diagramContent.split('\n').filter(line =>
      line.trim() && !line.trim().startsWith('%%')
    );

    const metrics = {
      totalLines: lines.length,
      nodes: 0,
      connections: 0,
      subgraphs: 0,
      complexity: 0
    };

    lines.forEach(line => {
      const trimmed = line.trim();

      // Count nodes (simple heuristic)
      if (trimmed.match(/^\s*\w+\[.*\]/) || trimmed.match(/^\s*\w+\(.*\)/)) {
        metrics.nodes++;
      }

      // Count connections
      if (trimmed.includes('-->') || trimmed.includes('---') ||
          trimmed.includes('-.->') || trimmed.includes('==>')) {
        metrics.connections++;
      }

      // Count subgraphs
      if (trimmed.startsWith('subgraph')) {
        metrics.subgraphs++;
      }
    });

    // Calculate complexity score
    metrics.complexity = (metrics.nodes * 1) + (metrics.connections * 2) + (metrics.subgraphs * 3);

    return metrics;
  }

  /**
   * Optimize diagram for better rendering
   */
  static optimizeDiagram(diagramContent, options = {}) {
    let optimized = diagramContent;

    if (options.removeComments) {
      optimized = optimized.replace(/%%.*$/gm, '');
    }

    if (options.removeEmptyLines) {
      optimized = optimized.replace(/^\s*$/gm, '').replace(/\n\n+/g, '\n');
    }

    if (options.sortNodes) {
      // Basic node sorting by type
      const lines = optimized.split('\n');
      const nodeLines = [];
      const connectionLines = [];
      const otherLines = [];

      lines.forEach(line => {
        const trimmed = line.trim();
        if (trimmed.includes('-->') || trimmed.includes('---')) {
          connectionLines.push(line);
        } else if (trimmed.match(/^\s*\w+\[.*\]/)) {
          nodeLines.push(line);
        } else {
          otherLines.push(line);
        }
      });

      optimized = [...otherLines, ...nodeLines, ...connectionLines].join('\n');
    }

    if (options.addStyling) {
      optimized += '\n\n' + this.generateDefaultStyling();
    }

    return optimized;
  }

  /**
   * Generate default styling for diagrams
   */
  static generateDefaultStyling() {
    return `%% Default Styling
classDef default fill:#f9f9f9,stroke:#333,stroke-width:2px
classDef highlight fill:#e1f5fe,stroke:#01579b,stroke-width:3px
classDef warning fill:#fff3e0,stroke:#f57c00,stroke-width:2px
classDef error fill:#ffebee,stroke:#c62828,stroke-width:2px
classDef success fill:#e8f5e8,stroke:#388e3c,stroke-width:2px`;
  }

  /**
   * Convert diagram to different format using CLI
   */
  static async convertDiagram(inputPath, outputPath, format = 'svg') {
    try {
      const { execSync } = await import('child_process');
      const command = `npx @mermaid-js/mermaid-cli -i "${inputPath}" -o "${outputPath}" -t ${format}`;

      execSync(command, {
        stdio: 'inherit',
        timeout: 30000 // 30 second timeout
      });

      return true;
    } catch (error) {
      console.error(`Failed to convert diagram to ${format}:`, error.message);
      return false;
    }
  }

  /**
   * Generate diagram metadata
   */
  static generateMetadata(diagramContent, analysis = null) {
    const complexity = this.calculateComplexity(diagramContent);
    const hash = crypto.createHash('md5').update(diagramContent).digest('hex');

    const metadata = {
      hash,
      generated: new Date().toISOString(),
      complexity,
      lineCount: diagramContent.split('\n').length,
      characterCount: diagramContent.length,
      type: this.extractDiagramType(diagramContent),
      tradingComponents: null
    };

    if (analysis) {
      metadata.tradingComponents = this.identifyTradingComponents(analysis);
      metadata.sourceFiles = analysis.files?.length || 0;
      metadata.classes = analysis.classes?.length || 0;
      metadata.functions = analysis.functions?.length || 0;
    }

    return metadata;
  }

  /**
   * Extract diagram type from content
   */
  static extractDiagramType(content) {
    const firstLine = content.split('\n').find(line =>
      line.trim() && !line.trim().startsWith('%%')
    );

    if (!firstLine) return 'unknown';

    for (const type of this.DIAGRAM_TYPES) {
      if (firstLine.toLowerCase().includes(type)) {
        return type;
      }
    }

    return 'unknown';
  }

  /**
   * Create diagram index/catalog
   */
  static async createDiagramIndex(diagramsPath, outputPath = null) {
    const index = {
      generated: new Date().toISOString(),
      totalDiagrams: 0,
      diagrams: [],
      byType: {},
      byComplexity: { low: 0, medium: 0, high: 0 }
    };

    try {
      const files = await fs.readdir(diagramsPath);
      const diagramFiles = files.filter(file => file.endsWith('.mmd') || file.endsWith('.mermaid'));

      for (const file of diagramFiles) {
        const filePath = path.join(diagramsPath, file);
        const content = await fs.readFile(filePath, 'utf8');
        const metadata = this.generateMetadata(content);

        const diagramInfo = {
          filename: file,
          path: filePath,
          ...metadata
        };

        index.diagrams.push(diagramInfo);
        index.totalDiagrams++;

        // Group by type
        if (!index.byType[metadata.type]) {
          index.byType[metadata.type] = [];
        }
        index.byType[metadata.type].push(diagramInfo);

        // Group by complexity
        const complexityLevel = metadata.complexity.complexity < 20 ? 'low' :
                               metadata.complexity.complexity < 50 ? 'medium' : 'high';
        index.byComplexity[complexityLevel]++;
      }

      if (outputPath) {
        await fs.writeFile(outputPath, JSON.stringify(index, null, 2), 'utf8');
      }

      return index;
    } catch (error) {
      console.error('Failed to create diagram index:', error.message);
      return index;
    }
  }

  /**
   * Validate file paths and create directories
   */
  static async ensureDirectoryExists(dirPath) {
    try {
      await fs.mkdir(dirPath, { recursive: true });
      return true;
    } catch (error) {
      console.error(`Failed to create directory ${dirPath}:`, error.message);
      return false;
    }
  }

  /**
   * Safe file write with backup
   */
  static async safeWriteFile(filePath, content, options = {}) {
    try {
      const dir = path.dirname(filePath);
      await this.ensureDirectoryExists(dir);

      // Create backup if file exists
      if (options.createBackup) {
        try {
          await fs.access(filePath);
          const backupPath = `${filePath}.backup.${Date.now()}`;
          await fs.copyFile(filePath, backupPath);
        } catch {
          // File doesn't exist, no backup needed
        }
      }

      await fs.writeFile(filePath, content, 'utf8');
      return true;
    } catch (error) {
      console.error(`Failed to write file ${filePath}:`, error.message);
      return false;
    }
  }

  /**
   * Get file statistics
   */
  static async getFileStats(filePath) {
    try {
      const stats = await fs.stat(filePath);
      return {
        size: stats.size,
        created: stats.birthtime,
        modified: stats.mtime,
        isFile: stats.isFile(),
        isDirectory: stats.isDirectory()
      };
    } catch (error) {
      return null;
    }
  }

  /**
   * Clean up old diagram files
   */
  static async cleanupOldDiagrams(diagramsPath, maxAge = 7 * 24 * 60 * 60 * 1000) { // 7 days
    try {
      const files = await fs.readdir(diagramsPath);
      const now = Date.now();
      let deletedCount = 0;

      for (const file of files) {
        const filePath = path.join(diagramsPath, file);
        const stats = await this.getFileStats(filePath);

        if (stats && stats.isFile && (now - stats.modified.getTime()) > maxAge) {
          await fs.unlink(filePath);
          deletedCount++;
        }
      }

      return { deletedCount, totalChecked: files.length };
    } catch (error) {
      console.error('Failed to cleanup old diagrams:', error.message);
      return { deletedCount: 0, totalChecked: 0 };
    }
  }

  /**
   * Merge multiple diagrams into one
   */
  static mergeDiagrams(diagrams, type = 'flowchart') {
    let merged = `${type} TD\n`;
    merged += '%% Merged diagram from multiple sources\n\n';

    let nodeCounter = 0;
    const nodeMapping = new Map();

    diagrams.forEach((diagram, index) => {
      merged += `%% Source ${index + 1}\n`;

      const lines = diagram.split('\n');
      lines.forEach(line => {
        const trimmed = line.trim();
        if (trimmed && !trimmed.startsWith('%%') && !this.isValidDiagramType(trimmed)) {
          // Remap node IDs to avoid conflicts
          let processedLine = trimmed;

          // Simple node ID remapping
          const nodeMatches = processedLine.match(/\b\w+\b/g);
          if (nodeMatches) {
            nodeMatches.forEach(match => {
              if (!nodeMapping.has(match)) {
                nodeMapping.set(match, `N${nodeCounter++}`);
              }
              processedLine = processedLine.replace(new RegExp(`\\b${match}\\b`, 'g'), nodeMapping.get(match));
            });
          }

          merged += `    ${processedLine}\n`;
        }
      });

      merged += '\n';
    });

    return merged;
  }

  /**
   * Performance monitoring utilities
   */
  static startTimer(label) {
    return {
      label,
      start: process.hrtime.bigint()
    };
  }

  static endTimer(timer) {
    const end = process.hrtime.bigint();
    const duration = Number(end - timer.start) / 1000000; // Convert to milliseconds

    return {
      label: timer.label,
      duration,
      formattedDuration: `${duration.toFixed(2)}ms`
    };
  }

  /**
   * Memory usage tracking
   */
  static getMemoryUsage() {
    const usage = process.memoryUsage();
    return {
      rss: Math.round(usage.rss / 1024 / 1024), // MB
      heapTotal: Math.round(usage.heapTotal / 1024 / 1024), // MB
      heapUsed: Math.round(usage.heapUsed / 1024 / 1024), // MB
      external: Math.round(usage.external / 1024 / 1024), // MB
      arrayBuffers: Math.round(usage.arrayBuffers / 1024 / 1024) // MB
    };
  }
}