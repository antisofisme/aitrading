/**
 * JavaScript Parser - AST parsing for JavaScript files
 * Uses Babel parser for comprehensive JavaScript analysis
 */

import * as babel from '@babel/parser';
import traverse from '@babel/traverse';
import * as t from '@babel/types';
import {
  Parser,
  CodeElement,
  Relationship,
  ParserContext,
  Logger,
  ElementType,
  RelationshipType
} from '../types';

export class JavaScriptParser implements Parser {
  name = 'javascript';
  supportedExtensions = ['.js', '.jsx', '.mjs'];

  constructor(private logger: Logger) {}

  canParse(filePath: string): boolean {
    return this.supportedExtensions.some(ext => filePath.endsWith(ext));
  }

  async parse(context: ParserContext): Promise<CodeElement[]> {
    try {
      const ast = babel.parse(context.content, {
        sourceType: 'module',
        plugins: [
          'jsx',
          'decorators-legacy',
          'classProperties',
          'objectRestSpread',
          'asyncGenerators',
          'functionBind',
          'exportDefaultFrom',
          'exportNamespaceFrom',
          'dynamicImport'
        ]
      });

      context.ast = ast;
      const elements: CodeElement[] = [];

      // Extract different types of elements
      elements.push(...this.extractClasses(ast, context));
      elements.push(...this.extractFunctions(ast, context));
      elements.push(...this.extractVariables(ast, context));
      elements.push(...this.extractImports(ast, context));
      elements.push(...this.extractExports(ast, context));

      return elements;

    } catch (error) {
      this.logger.error(`Failed to parse JavaScript file ${context.filePath}:`, error);
      return [];
    }
  }

  async extractRelationships(context: ParserContext, elements: CodeElement[]): Promise<Relationship[]> {
    try {
      const ast = context.ast || babel.parse(context.content, {
        sourceType: 'module',
        plugins: ['jsx', 'decorators-legacy', 'classProperties', 'objectRestSpread']
      });

      const relationships: Relationship[] = [];

      // Extract call relationships
      relationships.push(...this.extractCallRelationships(ast, elements));

      // Extract class relationships
      relationships.push(...this.extractClassRelationships(ast, elements));

      // Extract variable dependencies
      relationships.push(...this.extractVariableDependencies(ast, elements));

      return relationships;

    } catch (error) {
      this.logger.error(`Failed to extract relationships from ${context.filePath}:`, error);
      return [];
    }
  }

  private extractClasses(ast: any, context: ParserContext): CodeElement[] {
    const elements: CodeElement[] = [];

    traverse(ast, {
      ClassDeclaration: (path) => {
        const node = path.node;
        const className = node.id?.name || 'AnonymousClass';

        const element: CodeElement = {
          id: this.generateId(context.filePath, className),
          name: className,
          type: ElementType.CLASS,
          filePath: context.filePath,
          startLine: node.loc?.start.line || 1,
          endLine: node.loc?.end.line || 1,
          metadata: {
            isExported: this.isExported(path),
            superClass: node.superClass ? this.extractExpression(node.superClass) : null,
            methods: this.extractClassMethods(node),
            properties: this.extractClassProperties(node),
            constructors: this.extractConstructors(node),
            complexity: this.calculateClassComplexity(node)
          }
        };

        // Check for trading patterns
        if (this.isTradingStrategy(element)) {
          element.type = ElementType.TRADING_STRATEGY;
          element.metadata.tradingType = 'strategy';
        } else if (this.isRiskComponent(element)) {
          element.type = ElementType.RISK_COMPONENT;
          element.metadata.tradingType = 'risk_management';
        }

        elements.push(element);
      }
    });

    return elements;
  }

  private extractFunctions(ast: any, context: ParserContext): CodeElement[] {
    const elements: CodeElement[] = [];

    traverse(ast, {
      FunctionDeclaration: (path) => {
        const node = path.node;
        const functionName = node.id?.name || 'AnonymousFunction';

        const element: CodeElement = {
          id: this.generateId(context.filePath, functionName),
          name: functionName,
          type: ElementType.FUNCTION,
          filePath: context.filePath,
          startLine: node.loc?.start.line || 1,
          endLine: node.loc?.end.line || 1,
          metadata: {
            isExported: this.isExported(path),
            isAsync: node.async,
            isGenerator: node.generator,
            parameters: this.extractFunctionParameters(node),
            complexity: this.calculateFunctionComplexity(node),
            calls: this.extractFunctionCalls(node)
          }
        };

        elements.push(element);
      },

      ArrowFunctionExpression: (path) => {
        // Handle arrow functions assigned to variables
        const parent = path.parent;
        if (t.isVariableDeclarator(parent) && t.isIdentifier(parent.id)) {
          const functionName = parent.id.name;
          const node = path.node;

          const element: CodeElement = {
            id: this.generateId(context.filePath, functionName),
            name: functionName,
            type: ElementType.FUNCTION,
            filePath: context.filePath,
            startLine: node.loc?.start.line || 1,
            endLine: node.loc?.end.line || 1,
            metadata: {
              isArrowFunction: true,
              isAsync: node.async,
              parameters: this.extractFunctionParameters(node),
              complexity: this.calculateFunctionComplexity(node)
            }
          };

          elements.push(element);
        }
      }
    });

    return elements;
  }

  private extractVariables(ast: any, context: ParserContext): CodeElement[] {
    const elements: CodeElement[] = [];

    traverse(ast, {
      VariableDeclaration: (path) => {
        const node = path.node;

        node.declarations.forEach((declaration) => {
          if (t.isIdentifier(declaration.id)) {
            const variableName = declaration.id.name;

            const element: CodeElement = {
              id: this.generateId(context.filePath, variableName),
              name: variableName,
              type: ElementType.VARIABLE,
              filePath: context.filePath,
              startLine: declaration.loc?.start.line || 1,
              endLine: declaration.loc?.end.line || 1,
              metadata: {
                isExported: this.isExported(path),
                kind: node.kind, // const, let, var
                hasInitializer: !!declaration.init,
                initializerType: declaration.init ? declaration.init.type : null
              }
            };

            elements.push(element);
          }
        });
      }
    });

    return elements;
  }

  private extractImports(ast: any, context: ParserContext): CodeElement[] {
    const elements: CodeElement[] = [];

    traverse(ast, {
      ImportDeclaration: (path) => {
        const node = path.node;
        const source = node.source.value;

        const element: CodeElement = {
          id: this.generateId(context.filePath, `import-${source}`),
          name: `import-${source}`,
          type: ElementType.IMPORT,
          filePath: context.filePath,
          startLine: node.loc?.start.line || 1,
          endLine: node.loc?.end.line || 1,
          metadata: {
            from: source,
            importedNames: node.specifiers.map(spec => {
              if (t.isImportDefaultSpecifier(spec)) {
                return { type: 'default', local: spec.local.name };
              } else if (t.isImportNamespaceSpecifier(spec)) {
                return { type: 'namespace', local: spec.local.name };
              } else if (t.isImportSpecifier(spec)) {
                return {
                  type: 'named',
                  imported: t.isIdentifier(spec.imported) ? spec.imported.name : spec.imported.value,
                  local: spec.local.name
                };
              }
              return null;
            }).filter(Boolean)
          }
        };

        elements.push(element);
      }
    });

    return elements;
  }

  private extractExports(ast: any, context: ParserContext): CodeElement[] {
    const elements: CodeElement[] = [];

    traverse(ast, {
      ExportDeclaration: (path) => {
        const node = path.node;
        let exportName = 'export';
        let exportedNames: string[] = [];

        if (t.isExportNamedDeclaration(node)) {
          if (node.declaration) {
            // export const x = ...
            if (t.isVariableDeclaration(node.declaration)) {
              exportedNames = node.declaration.declarations
                .map(decl => t.isIdentifier(decl.id) ? decl.id.name : null)
                .filter(Boolean) as string[];
            } else if (t.isFunctionDeclaration(node.declaration) && node.declaration.id) {
              exportedNames = [node.declaration.id.name];
            } else if (t.isClassDeclaration(node.declaration) && node.declaration.id) {
              exportedNames = [node.declaration.id.name];
            }
          } else if (node.specifiers) {
            // export { x, y }
            exportedNames = node.specifiers.map(spec => {
              if (t.isExportSpecifier(spec)) {
                return t.isIdentifier(spec.exported) ? spec.exported.name : spec.exported.value;
              }
              return null;
            }).filter(Boolean) as string[];
          }

          exportName = `export-${exportedNames.join('-') || 'named'}`;
        } else if (t.isExportDefaultDeclaration(node)) {
          exportName = 'export-default';
          exportedNames = ['default'];
        } else if (t.isExportAllDeclaration(node)) {
          exportName = `export-all-${node.source.value}`;
          exportedNames = ['*'];
        }

        const element: CodeElement = {
          id: this.generateId(context.filePath, exportName),
          name: exportName,
          type: ElementType.EXPORT,
          filePath: context.filePath,
          startLine: node.loc?.start.line || 1,
          endLine: node.loc?.end.line || 1,
          metadata: {
            exportedNames,
            from: t.isExportAllDeclaration(node) || (t.isExportNamedDeclaration(node) && node.source)
              ? node.source?.value
              : undefined
          }
        };

        elements.push(element);
      }
    });

    return elements;
  }

  private extractCallRelationships(ast: any, elements: CodeElement[]): Relationship[] {
    const relationships: Relationship[] = [];

    traverse(ast, {
      CallExpression: (path) => {
        const node = path.node;
        const caller = this.findContainingFunction(path, elements);
        const calledFunction = this.extractCalledFunction(node);

        if (caller && calledFunction) {
          const target = elements.find(e => e.name === calledFunction);

          if (target) {
            const relationship: Relationship = {
              id: `${caller.id}-calls-${target.id}`,
              sourceId: caller.id,
              targetId: target.id,
              type: RelationshipType.CALLS,
              weight: 1,
              metadata: {
                confidence: 0.8,
                direction: 'unidirectional',
                category: 'behavioral',
                tags: ['function-call', 'invocation']
              }
            };

            relationships.push(relationship);
          }
        }
      }
    });

    return relationships;
  }

  private extractClassRelationships(ast: any, elements: CodeElement[]): Relationship[] {
    const relationships: Relationship[] = [];

    traverse(ast, {
      ClassDeclaration: (path) => {
        const node = path.node;
        const className = node.id?.name;

        if (!className) return;

        const sourceElement = elements.find(e => e.name === className && e.type === ElementType.CLASS);
        if (!sourceElement) return;

        // Inheritance relationship
        if (node.superClass) {
          const superClassName = this.extractExpression(node.superClass);
          const targetElement = elements.find(e => e.name === superClassName);

          if (targetElement) {
            relationships.push({
              id: `${sourceElement.id}-extends-${targetElement.id}`,
              sourceId: sourceElement.id,
              targetId: targetElement.id,
              type: RelationshipType.INHERITS,
              weight: 1,
              metadata: {
                confidence: 1.0,
                direction: 'unidirectional',
                category: 'structural',
                tags: ['inheritance', 'extends']
              }
            });
          }
        }
      }
    });

    return relationships;
  }

  private extractVariableDependencies(ast: any, elements: CodeElement[]): Relationship[] {
    const relationships: Relationship[] = [];

    traverse(ast, {
      VariableDeclarator: (path) => {
        const node = path.node;

        if (t.isIdentifier(node.id) && node.init) {
          const variableName = node.id.name;
          const sourceElement = elements.find(e => e.name === variableName && e.type === ElementType.VARIABLE);

          if (sourceElement) {
            // Check if initializer references other elements
            const dependencies = this.extractDependenciesFromExpression(node.init);

            dependencies.forEach(dep => {
              const targetElement = elements.find(e => e.name === dep);
              if (targetElement) {
                relationships.push({
                  id: `${sourceElement.id}-depends-on-${targetElement.id}`,
                  sourceId: sourceElement.id,
                  targetId: targetElement.id,
                  type: RelationshipType.DEPENDS_ON,
                  weight: 1,
                  metadata: {
                    confidence: 0.7,
                    direction: 'unidirectional',
                    category: 'structural',
                    tags: ['variable-dependency']
                  }
                });
              }
            });
          }
        }
      }
    });

    return relationships;
  }

  // Helper methods

  private generateId(filePath: string, name: string): string {
    const fileName = filePath.split('/').pop()?.replace(/\.[^/.]+$/, '') || 'unknown';
    return `${fileName}:${name}`;
  }

  private isExported(path: any): boolean {
    const parent = path.parent;
    return t.isExportNamedDeclaration(parent) || t.isExportDefaultDeclaration(parent);
  }

  private extractExpression(node: any): string {
    if (t.isIdentifier(node)) {
      return node.name;
    } else if (t.isMemberExpression(node)) {
      return `${this.extractExpression(node.object)}.${this.extractExpression(node.property)}`;
    }
    return 'unknown';
  }

  private extractClassMethods(classNode: any): any[] {
    return classNode.body.body
      .filter((node: any) => t.isMethodDefinition(node) || t.isClassMethod(node))
      .map((method: any) => ({
        name: t.isIdentifier(method.key) ? method.key.name : 'unknown',
        kind: method.kind, // method, constructor, get, set
        isStatic: method.static,
        isAsync: method.async,
        parameters: this.extractFunctionParameters(method)
      }));
  }

  private extractClassProperties(classNode: any): any[] {
    return classNode.body.body
      .filter((node: any) => t.isClassProperty(node) || t.isPropertyDefinition(node))
      .map((prop: any) => ({
        name: t.isIdentifier(prop.key) ? prop.key.name : 'unknown',
        isStatic: prop.static,
        hasValue: !!prop.value
      }));
  }

  private extractConstructors(classNode: any): any[] {
    return classNode.body.body
      .filter((node: any) => (t.isMethodDefinition(node) || t.isClassMethod(node)) && node.kind === 'constructor')
      .map((ctor: any) => ({
        parameters: this.extractFunctionParameters(ctor)
      }));
  }

  private extractFunctionParameters(functionNode: any): any[] {
    if (!functionNode.params) return [];

    return functionNode.params.map((param: any) => {
      if (t.isIdentifier(param)) {
        return { name: param.name, type: 'unknown' };
      } else if (t.isAssignmentPattern(param) && t.isIdentifier(param.left)) {
        return {
          name: param.left.name,
          type: 'unknown',
          hasDefault: true,
          defaultValue: this.extractExpression(param.right)
        };
      }
      return { name: 'unknown', type: 'unknown' };
    });
  }

  private extractFunctionCalls(functionNode: any): string[] {
    const calls: string[] = [];

    traverse(functionNode, {
      CallExpression: (path) => {
        const calledFunction = this.extractCalledFunction(path.node);
        if (calledFunction) {
          calls.push(calledFunction);
        }
      }
    }, path.scope);

    return calls;
  }

  private extractCalledFunction(callNode: any): string | null {
    if (t.isIdentifier(callNode.callee)) {
      return callNode.callee.name;
    } else if (t.isMemberExpression(callNode.callee)) {
      if (t.isIdentifier(callNode.callee.property)) {
        return callNode.callee.property.name;
      }
    }
    return null;
  }

  private findContainingFunction(path: any, elements: CodeElement[]): CodeElement | null {
    let current = path.parent;

    while (current) {
      if (t.isFunctionDeclaration(current) && current.id) {
        return elements.find(e => e.name === current.id.name && e.type === ElementType.FUNCTION) || null;
      } else if (t.isClassMethod(current) || t.isMethodDefinition(current)) {
        if (t.isIdentifier(current.key)) {
          return elements.find(e => e.name === current.key.name) || null;
        }
      }
      current = current.parent;
    }

    return null;
  }

  private extractDependenciesFromExpression(node: any): string[] {
    const dependencies: string[] = [];

    if (t.isIdentifier(node)) {
      dependencies.push(node.name);
    } else if (t.isCallExpression(node)) {
      const funcName = this.extractCalledFunction(node);
      if (funcName) {
        dependencies.push(funcName);
      }
    } else if (t.isMemberExpression(node)) {
      const objectName = this.extractExpression(node.object);
      dependencies.push(objectName);
    }

    return dependencies;
  }

  private calculateClassComplexity(classNode: any): number {
    let complexity = 1;

    // Add complexity for methods
    const methods = classNode.body.body.filter((node: any) => t.isMethodDefinition(node) || t.isClassMethod(node));
    complexity += methods.length * 2;

    // Add complexity for properties
    const properties = classNode.body.body.filter((node: any) => t.isClassProperty(node) || t.isPropertyDefinition(node));
    complexity += properties.length;

    // Add complexity for inheritance
    if (classNode.superClass) {
      complexity += 2;
    }

    return complexity;
  }

  private calculateFunctionComplexity(functionNode: any): number {
    let complexity = 1;

    // Add complexity for parameters
    if (functionNode.params) {
      complexity += functionNode.params.length * 0.5;
    }

    // Add complexity for control flow (simplified)
    traverse(functionNode, {
      IfStatement: () => complexity++,
      ForStatement: () => complexity++,
      WhileStatement: () => complexity++,
      SwitchStatement: () => complexity++,
      TryStatement: () => complexity++
    });

    return complexity;
  }

  private isTradingStrategy(element: CodeElement): boolean {
    const tradingPatterns = [
      /strategy/i,
      /trading.*strategy/i,
      /algorithm.*trading/i,
      /trade.*executor/i,
      /signal.*generator/i
    ];

    return tradingPatterns.some(pattern =>
      pattern.test(element.name) ||
      pattern.test(JSON.stringify(element.metadata))
    );
  }

  private isRiskComponent(element: CodeElement): boolean {
    const riskPatterns = [
      /risk/i,
      /risk.*management/i,
      /risk.*monitor/i,
      /position.*sizer/i,
      /stop.*loss/i,
      /risk.*calculator/i
    ];

    return riskPatterns.some(pattern =>
      pattern.test(element.name) ||
      pattern.test(JSON.stringify(element.metadata))
    );
  }
}