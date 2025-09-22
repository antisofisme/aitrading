/**
 * Code Analysis Module for Relationship Mapping
 * Analyzes codebases to extract structure and relationships
 */

import fs from 'fs/promises';
import path from 'path';
import { glob } from 'glob';
import { parse } from '@babel/parser';
import traverse from '@babel/traverse';
import * as t from '@babel/types';

export class CodeAnalyzer {
  constructor() {
    this.supportedExtensions = ['.js', '.ts', '.jsx', '.tsx', '.py', '.java', '.cs'];
    this.analysisCache = new Map();
  }

  async analyzeCodebase(rootPath, includePatterns = ['**/*.{js,ts,jsx,tsx}'], excludePatterns = ['node_modules/**', '.git/**', 'dist/**', 'build/**']) {
    const analysis = {
      files: [],
      classes: [],
      functions: [],
      dependencies: [],
      relationships: [],
      imports: [],
      exports: [],
      metadata: {
        totalFiles: 0,
        totalLines: 0,
        languages: {},
        complexity: 0,
        timestamp: new Date().toISOString()
      }
    };

    try {
      // Get all files matching patterns
      const files = await this.getFilesToAnalyze(rootPath, includePatterns, excludePatterns);
      analysis.metadata.totalFiles = files.length;

      // Analyze each file
      for (const filePath of files) {
        try {
          const fileAnalysis = await this.analyzeFile(filePath);

          analysis.files.push(fileAnalysis.file);
          analysis.classes.push(...fileAnalysis.classes);
          analysis.functions.push(...fileAnalysis.functions);
          analysis.dependencies.push(...fileAnalysis.dependencies);
          analysis.imports.push(...fileAnalysis.imports);
          analysis.exports.push(...fileAnalysis.exports);

          analysis.metadata.totalLines += fileAnalysis.file.lines;
          analysis.metadata.complexity += fileAnalysis.file.complexity;

          const ext = path.extname(filePath);
          analysis.metadata.languages[ext] = (analysis.metadata.languages[ext] || 0) + 1;

        } catch (error) {
          console.warn(`Failed to analyze ${filePath}:`, error.message);
        }
      }

      // Generate relationships
      analysis.relationships = this.generateRelationships(analysis);

      // Cache the analysis
      this.analysisCache.set(rootPath, analysis);

      return analysis;
    } catch (error) {
      throw new Error(`Failed to analyze codebase: ${error.message}`);
    }
  }

  async analyzeCode(source, filePath = 'unknown.js') {
    try {
      const fileAnalysis = await this.analyzeFileContent(source, filePath);

      return {
        files: [fileAnalysis.file],
        classes: fileAnalysis.classes,
        functions: fileAnalysis.functions,
        dependencies: fileAnalysis.dependencies,
        relationships: this.generateRelationships({
          classes: fileAnalysis.classes,
          functions: fileAnalysis.functions,
          dependencies: fileAnalysis.dependencies
        }),
        imports: fileAnalysis.imports,
        exports: fileAnalysis.exports,
        metadata: {
          totalFiles: 1,
          totalLines: fileAnalysis.file.lines,
          complexity: fileAnalysis.file.complexity,
          timestamp: new Date().toISOString()
        }
      };
    } catch (error) {
      throw new Error(`Failed to analyze code: ${error.message}`);
    }
  }

  async getFilesToAnalyze(rootPath, includePatterns, excludePatterns) {
    const files = [];

    for (const pattern of includePatterns) {
      const matchedFiles = await glob(pattern, {
        cwd: rootPath,
        absolute: true,
        ignore: excludePatterns
      });
      files.push(...matchedFiles);
    }

    return [...new Set(files)]; // Remove duplicates
  }

  async analyzeFile(filePath) {
    const content = await fs.readFile(filePath, 'utf8');
    return this.analyzeFileContent(content, filePath);
  }

  async analyzeFileContent(content, filePath) {
    const ext = path.extname(filePath);
    const fileName = path.basename(filePath);
    const lines = content.split('\n').length;

    const analysis = {
      file: {
        path: filePath,
        name: fileName,
        extension: ext,
        lines,
        size: content.length,
        complexity: 0
      },
      classes: [],
      functions: [],
      dependencies: [],
      imports: [],
      exports: []
    };

    if (['.js', '.ts', '.jsx', '.tsx'].includes(ext)) {
      await this.analyzeJavaScript(content, analysis, filePath);
    } else if (ext === '.py') {
      await this.analyzePython(content, analysis, filePath);
    } else if (ext === '.java') {
      await this.analyzeJava(content, analysis, filePath);
    } else if (ext === '.cs') {
      await this.analyzeCSharp(content, analysis, filePath);
    }

    return analysis;
  }

  async analyzeJavaScript(content, analysis, filePath) {
    try {
      const ast = parse(content, {
        sourceType: 'module',
        allowImportExportEverywhere: true,
        allowReturnOutsideFunction: true,
        plugins: [
          'jsx',
          'typescript',
          'decorators-legacy',
          'classProperties',
          'objectRestSpread',
          'functionBind',
          'exportDefaultFrom',
          'exportNamespaceFrom',
          'dynamicImport',
          'nullishCoalescingOperator',
          'optionalChaining'
        ]
      });

      traverse.default(ast, {
        // Import declarations
        ImportDeclaration(path) {
          analysis.imports.push({
            source: path.node.source.value,
            specifiers: path.node.specifiers.map(spec => ({
              imported: spec.imported?.name || 'default',
              local: spec.local.name
            })),
            file: filePath
          });

          analysis.dependencies.push({
            from: filePath,
            to: path.node.source.value,
            type: 'import'
          });
        },

        // Export declarations
        ExportNamedDeclaration(path) {
          if (path.node.declaration) {
            analysis.exports.push({
              name: path.node.declaration.id?.name || 'anonymous',
              type: path.node.declaration.type,
              file: filePath
            });
          }
        },

        ExportDefaultDeclaration(path) {
          analysis.exports.push({
            name: 'default',
            type: path.node.declaration.type,
            file: filePath
          });
        },

        // Class declarations
        ClassDeclaration(path) {
          const className = path.node.id.name;
          const classInfo = {
            name: className,
            file: filePath,
            extends: path.node.superClass?.name,
            implements: [],
            methods: [],
            properties: [],
            abstract: false,
            static: false
          };

          // Get class methods and properties
          path.node.body.body.forEach(member => {
            if (t.isMethodDefinition(member)) {
              classInfo.methods.push({
                name: member.key.name,
                static: member.static,
                async: member.value.async,
                parameters: member.value.params.map(param => ({
                  name: param.name,
                  type: param.typeAnnotation?.typeAnnotation?.type || 'any'
                })),
                returnType: member.value.returnType?.typeAnnotation?.type || 'void'
              });
            } else if (t.isClassProperty(member)) {
              classInfo.properties.push({
                name: member.key.name,
                static: member.static,
                type: member.typeAnnotation?.typeAnnotation?.type || 'any'
              });
            }
          });

          analysis.classes.push(classInfo);
          analysis.file.complexity += classInfo.methods.length * 2;
        },

        // Function declarations
        FunctionDeclaration(path) {
          const funcInfo = {
            name: path.node.id.name,
            file: filePath,
            async: path.node.async,
            parameters: path.node.params.map(param => ({
              name: param.name,
              type: param.typeAnnotation?.typeAnnotation?.type || 'any'
            })),
            returnType: path.node.returnType?.typeAnnotation?.type || 'void',
            calls: []
          };

          // Find function calls within this function
          path.traverse({
            CallExpression(callPath) {
              if (t.isIdentifier(callPath.node.callee)) {
                funcInfo.calls.push({
                  name: callPath.node.callee.name,
                  arguments: callPath.node.arguments.length
                });
              } else if (t.isMemberExpression(callPath.node.callee)) {
                funcInfo.calls.push({
                  name: callPath.node.callee.property.name,
                  target: callPath.node.callee.object.name,
                  arguments: callPath.node.arguments.length
                });
              }
            }
          });

          analysis.functions.push(funcInfo);
          analysis.file.complexity += funcInfo.calls.length;
        },

        // Arrow functions and function expressions
        ArrowFunctionExpression(path) {
          if (path.parent.type === 'VariableDeclarator' && path.parent.id.name) {
            const funcInfo = {
              name: path.parent.id.name,
              file: filePath,
              async: path.node.async,
              parameters: path.node.params.map(param => ({
                name: param.name,
                type: param.typeAnnotation?.typeAnnotation?.type || 'any'
              })),
              returnType: 'any',
              calls: [],
              arrow: true
            };

            analysis.functions.push(funcInfo);
          }
        }
      });

    } catch (error) {
      console.warn(`Failed to parse JavaScript file ${filePath}:`, error.message);
    }
  }

  async analyzePython(content, analysis, filePath) {
    // Basic Python analysis using regex patterns
    // For production, consider using a Python AST parser

    const lines = content.split('\n');

    lines.forEach((line, index) => {
      // Class definitions
      const classMatch = line.match(/^class\s+(\w+)(?:\(([^)]+)\))?:/);
      if (classMatch) {
        analysis.classes.push({
          name: classMatch[1],
          file: filePath,
          extends: classMatch[2],
          methods: [],
          properties: [],
          lineNumber: index + 1
        });
      }

      // Function definitions
      const funcMatch = line.match(/^(?:\s*)def\s+(\w+)\(([^)]*)\):/);
      if (funcMatch) {
        const params = funcMatch[2].split(',').map(p => ({
          name: p.trim().split('=')[0].trim(),
          type: 'any'
        })).filter(p => p.name);

        analysis.functions.push({
          name: funcMatch[1],
          file: filePath,
          parameters: params,
          lineNumber: index + 1,
          calls: []
        });
      }

      // Import statements
      const importMatch = line.match(/^(?:from\s+(\S+)\s+)?import\s+(.+)/);
      if (importMatch) {
        analysis.imports.push({
          source: importMatch[1] || importMatch[2].split(',')[0].trim(),
          specifiers: importMatch[2].split(',').map(s => ({
            imported: s.trim(),
            local: s.trim()
          })),
          file: filePath
        });
      }
    });

    analysis.file.complexity = analysis.functions.length + analysis.classes.length;
  }

  async analyzeJava(content, analysis, filePath) {
    // Basic Java analysis using regex patterns
    const lines = content.split('\n');

    lines.forEach((line, index) => {
      // Class definitions
      const classMatch = line.match(/(?:public|private|protected)?\s*class\s+(\w+)(?:\s+extends\s+(\w+))?/);
      if (classMatch) {
        analysis.classes.push({
          name: classMatch[1],
          file: filePath,
          extends: classMatch[2],
          methods: [],
          properties: [],
          lineNumber: index + 1
        });
      }

      // Method definitions
      const methodMatch = line.match(/(?:public|private|protected)?\s*(?:static)?\s*(\w+)\s+(\w+)\s*\(/);
      if (methodMatch) {
        analysis.functions.push({
          name: methodMatch[2],
          file: filePath,
          returnType: methodMatch[1],
          lineNumber: index + 1,
          calls: []
        });
      }

      // Import statements
      const importMatch = line.match(/^import\s+(.+);/);
      if (importMatch) {
        analysis.imports.push({
          source: importMatch[1],
          file: filePath
        });
      }
    });

    analysis.file.complexity = analysis.functions.length + analysis.classes.length;
  }

  async analyzeCSharp(content, analysis, filePath) {
    // Basic C# analysis using regex patterns
    const lines = content.split('\n');

    lines.forEach((line, index) => {
      // Class definitions
      const classMatch = line.match(/(?:public|private|protected|internal)?\s*class\s+(\w+)(?:\s*:\s*(\w+))?/);
      if (classMatch) {
        analysis.classes.push({
          name: classMatch[1],
          file: filePath,
          extends: classMatch[2],
          methods: [],
          properties: [],
          lineNumber: index + 1
        });
      }

      // Method definitions
      const methodMatch = line.match(/(?:public|private|protected|internal)?\s*(?:static)?\s*(\w+)\s+(\w+)\s*\(/);
      if (methodMatch) {
        analysis.functions.push({
          name: methodMatch[2],
          file: filePath,
          returnType: methodMatch[1],
          lineNumber: index + 1,
          calls: []
        });
      }

      // Using statements
      const usingMatch = line.match(/^using\s+(.+);/);
      if (usingMatch) {
        analysis.imports.push({
          source: usingMatch[1],
          file: filePath
        });
      }
    });

    analysis.file.complexity = analysis.functions.length + analysis.classes.length;
  }

  generateRelationships(analysis) {
    const relationships = [];

    // Class inheritance relationships
    analysis.classes?.forEach(cls => {
      if (cls.extends) {
        const parentClass = analysis.classes.find(c => c.name === cls.extends);
        if (parentClass) {
          relationships.push({
            from: cls.extends,
            to: cls.name,
            type: 'extends',
            description: `${cls.name} extends ${cls.extends}`
          });
        }
      }
    });

    // Function call relationships
    analysis.functions?.forEach(func => {
      func.calls?.forEach(call => {
        if (call.target) {
          relationships.push({
            from: func.name,
            to: call.target,
            type: 'uses',
            description: `${func.name} calls ${call.name} on ${call.target}`
          });
        }
      });
    });

    // Import/dependency relationships
    analysis.dependencies?.forEach(dep => {
      relationships.push({
        from: path.basename(dep.from),
        to: dep.to,
        type: 'imports',
        description: `${path.basename(dep.from)} imports ${dep.to}`
      });
    });

    // File-to-class relationships
    analysis.classes?.forEach(cls => {
      relationships.push({
        from: path.basename(cls.file),
        to: cls.name,
        type: 'contains',
        description: `${path.basename(cls.file)} contains class ${cls.name}`
      });
    });

    return relationships;
  }

  // Trading system specific analysis
  identifyTradingComponents(analysis) {
    const tradingKeywords = {
      strategy: ['strategy', 'signal', 'algorithm', 'indicator'],
      data: ['market', 'price', 'feed', 'ticker', 'ohlc'],
      risk: ['risk', 'position', 'size', 'stop', 'limit'],
      execution: ['order', 'trade', 'execute', 'broker', 'fill'],
      portfolio: ['portfolio', 'asset', 'allocation', 'balance']
    };

    const components = {
      strategy: [],
      data: [],
      risk: [],
      execution: [],
      portfolio: []
    };

    analysis.classes?.forEach(cls => {
      const className = cls.name.toLowerCase();

      Object.entries(tradingKeywords).forEach(([category, keywords]) => {
        if (keywords.some(keyword => className.includes(keyword))) {
          components[category].push(cls);
        }
      });
    });

    return components;
  }

  calculateComplexityMetrics(analysis) {
    return {
      cyclomaticComplexity: analysis.metadata.complexity,
      classCount: analysis.classes?.length || 0,
      functionCount: analysis.functions?.length || 0,
      dependencyCount: analysis.dependencies?.length || 0,
      averageMethodsPerClass: analysis.classes?.length > 0
        ? analysis.classes.reduce((sum, cls) => sum + (cls.methods?.length || 0), 0) / analysis.classes.length
        : 0,
      linesOfCode: analysis.metadata.totalLines
    };
  }
}