/**
 * TypeScript Parser - Advanced AST parsing for TypeScript files
 * Extracts classes, interfaces, functions, imports, exports, and relationships
 */

import * as ts from 'typescript';
import { Project, SourceFile, SyntaxKind, Node } from 'ts-morph';
import {
  Parser,
  CodeElement,
  Relationship,
  ParserContext,
  Logger,
  ElementType,
  RelationshipType
} from '../types';

export class TypeScriptParser implements Parser {
  name = 'typescript';
  supportedExtensions = ['.ts', '.tsx'];
  private project: Project;

  constructor(private logger: Logger) {
    this.project = new Project({
      compilerOptions: {
        target: ts.ScriptTarget.ES2020,
        module: ts.ModuleKind.ESNext,
        lib: ['ES2020', 'DOM'],
        allowJs: true,
        declaration: true,
        strict: false
      }
    });
  }

  canParse(filePath: string): boolean {
    return this.supportedExtensions.some(ext => filePath.endsWith(ext));
  }

  async parse(context: ParserContext): Promise<CodeElement[]> {
    try {
      const sourceFile = this.project.addSourceFileAtPath(context.filePath);
      context.sourceFile = sourceFile;

      const elements: CodeElement[] = [];

      // Extract different types of elements
      elements.push(...this.extractClasses(sourceFile, context));
      elements.push(...this.extractInterfaces(sourceFile, context));
      elements.push(...this.extractFunctions(sourceFile, context));
      elements.push(...this.extractVariables(sourceFile, context));
      elements.push(...this.extractEnums(sourceFile, context));
      elements.push(...this.extractTypeAliases(sourceFile, context));
      elements.push(...this.extractImports(sourceFile, context));
      elements.push(...this.extractExports(sourceFile, context));
      elements.push(...this.extractDecorators(sourceFile, context));

      // Remove source file to avoid memory leaks
      this.project.removeSourceFile(sourceFile);

      return elements;

    } catch (error) {
      this.logger.error(`Failed to parse TypeScript file ${context.filePath}:`, error);
      return [];
    }
  }

  async extractRelationships(context: ParserContext, elements: CodeElement[]): Promise<Relationship[]> {
    try {
      const sourceFile = this.project.addSourceFileAtPath(context.filePath);
      const relationships: Relationship[] = [];

      // Extract inheritance relationships
      relationships.push(...this.extractInheritanceRelationships(sourceFile, elements));

      // Extract method call relationships
      relationships.push(...this.extractCallRelationships(sourceFile, elements));

      // Extract dependency relationships
      relationships.push(...this.extractDependencyRelationships(sourceFile, elements));

      // Extract composition/aggregation relationships
      relationships.push(...this.extractCompositionRelationships(sourceFile, elements));

      this.project.removeSourceFile(sourceFile);
      return relationships;

    } catch (error) {
      this.logger.error(`Failed to extract relationships from ${context.filePath}:`, error);
      return [];
    }
  }

  private extractClasses(sourceFile: SourceFile, context: ParserContext): CodeElement[] {
    const elements: CodeElement[] = [];

    sourceFile.getClasses().forEach(classDeclaration => {
      const element: CodeElement = {
        id: this.generateId(context.filePath, classDeclaration.getName() || 'AnonymousClass'),
        name: classDeclaration.getName() || 'AnonymousClass',
        type: ElementType.CLASS,
        filePath: context.filePath,
        startLine: classDeclaration.getStartLineNumber(),
        endLine: classDeclaration.getEndLineNumber(),
        metadata: {
          isAbstract: classDeclaration.isAbstract(),
          isExported: classDeclaration.isExported(),
          modifiers: classDeclaration.getModifiers().map(m => m.getKindName()),
          extends: classDeclaration.getExtends()?.getText(),
          implements: classDeclaration.getImplements().map(i => i.getText()),
          methods: classDeclaration.getMethods().map(method => ({
            name: method.getName(),
            isStatic: method.isStatic(),
            isPrivate: method.hasModifier(SyntaxKind.PrivateKeyword),
            isProtected: method.hasModifier(SyntaxKind.ProtectedKeyword),
            parameters: method.getParameters().map(p => ({
              name: p.getName(),
              type: p.getTypeNode()?.getText()
            })),
            returnType: method.getReturnTypeNode()?.getText()
          })),
          properties: classDeclaration.getProperties().map(prop => ({
            name: prop.getName(),
            type: prop.getTypeNode()?.getText(),
            isStatic: prop.isStatic(),
            isReadonly: prop.isReadonly(),
            isPrivate: prop.hasModifier(SyntaxKind.PrivateKeyword),
            isProtected: prop.hasModifier(SyntaxKind.ProtectedKeyword)
          })),
          constructors: classDeclaration.getConstructors().map(ctor => ({
            parameters: ctor.getParameters().map(p => ({
              name: p.getName(),
              type: p.getTypeNode()?.getText()
            }))
          })),
          decorators: classDeclaration.getDecorators().map(d => d.getName()),
          complexity: this.calculateClassComplexity(classDeclaration)
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
    });

    return elements;
  }

  private extractInterfaces(sourceFile: SourceFile, context: ParserContext): CodeElement[] {
    const elements: CodeElement[] = [];

    sourceFile.getInterfaces().forEach(interfaceDeclaration => {
      const element: CodeElement = {
        id: this.generateId(context.filePath, interfaceDeclaration.getName()),
        name: interfaceDeclaration.getName(),
        type: ElementType.INTERFACE,
        filePath: context.filePath,
        startLine: interfaceDeclaration.getStartLineNumber(),
        endLine: interfaceDeclaration.getEndLineNumber(),
        metadata: {
          isExported: interfaceDeclaration.isExported(),
          extends: interfaceDeclaration.getExtends().map(e => e.getText()),
          properties: interfaceDeclaration.getProperties().map(prop => ({
            name: prop.getName ? prop.getName() : 'unknown',
            type: prop.getTypeNode ? prop.getTypeNode()?.getText() : 'unknown',
            isOptional: prop.hasQuestionToken ? prop.hasQuestionToken() : false
          })),
          methods: interfaceDeclaration.getMethods().map(method => ({
            name: method.getName(),
            parameters: method.getParameters().map(p => ({
              name: p.getName(),
              type: p.getTypeNode()?.getText()
            })),
            returnType: method.getReturnTypeNode()?.getText()
          }))
        }
      };

      elements.push(element);
    });

    return elements;
  }

  private extractFunctions(sourceFile: SourceFile, context: ParserContext): CodeElement[] {
    const elements: CodeElement[] = [];

    sourceFile.getFunctions().forEach(functionDeclaration => {
      const element: CodeElement = {
        id: this.generateId(context.filePath, functionDeclaration.getName() || 'AnonymousFunction'),
        name: functionDeclaration.getName() || 'AnonymousFunction',
        type: ElementType.FUNCTION,
        filePath: context.filePath,
        startLine: functionDeclaration.getStartLineNumber(),
        endLine: functionDeclaration.getEndLineNumber(),
        metadata: {
          isExported: functionDeclaration.isExported(),
          isAsync: functionDeclaration.isAsync(),
          isGenerator: functionDeclaration.isGenerator(),
          parameters: functionDeclaration.getParameters().map(p => ({
            name: p.getName(),
            type: p.getTypeNode()?.getText(),
            isOptional: p.hasQuestionToken(),
            defaultValue: p.getInitializer()?.getText()
          })),
          returnType: functionDeclaration.getReturnTypeNode()?.getText(),
          complexity: this.calculateFunctionComplexity(functionDeclaration),
          calls: this.extractFunctionCalls(functionDeclaration)
        }
      };

      elements.push(element);
    });

    return elements;
  }

  private extractVariables(sourceFile: SourceFile, context: ParserContext): CodeElement[] {
    const elements: CodeElement[] = [];

    sourceFile.getVariableStatements().forEach(variableStatement => {
      variableStatement.getDeclarations().forEach(declaration => {
        const element: CodeElement = {
          id: this.generateId(context.filePath, declaration.getName()),
          name: declaration.getName(),
          type: ElementType.VARIABLE,
          filePath: context.filePath,
          startLine: declaration.getStartLineNumber(),
          endLine: declaration.getEndLineNumber(),
          metadata: {
            isExported: variableStatement.isExported(),
            type: declaration.getTypeNode()?.getText(),
            initializer: declaration.getInitializer()?.getText(),
            isConst: variableStatement.getDeclarationKind() === ts.VariableDeclarationKind.Const,
            isLet: variableStatement.getDeclarationKind() === ts.VariableDeclarationKind.Let
          }
        };

        elements.push(element);
      });
    });

    return elements;
  }

  private extractEnums(sourceFile: SourceFile, context: ParserContext): CodeElement[] {
    const elements: CodeElement[] = [];

    sourceFile.getEnums().forEach(enumDeclaration => {
      const element: CodeElement = {
        id: this.generateId(context.filePath, enumDeclaration.getName()),
        name: enumDeclaration.getName(),
        type: ElementType.ENUM,
        filePath: context.filePath,
        startLine: enumDeclaration.getStartLineNumber(),
        endLine: enumDeclaration.getEndLineNumber(),
        metadata: {
          isExported: enumDeclaration.isExported(),
          isConst: enumDeclaration.isConst(),
          members: enumDeclaration.getMembers().map(member => ({
            name: member.getName(),
            value: member.getValue()
          }))
        }
      };

      elements.push(element);
    });

    return elements;
  }

  private extractTypeAliases(sourceFile: SourceFile, context: ParserContext): CodeElement[] {
    const elements: CodeElement[] = [];

    sourceFile.getTypeAliases().forEach(typeAlias => {
      const element: CodeElement = {
        id: this.generateId(context.filePath, typeAlias.getName()),
        name: typeAlias.getName(),
        type: ElementType.TYPE_ALIAS,
        filePath: context.filePath,
        startLine: typeAlias.getStartLineNumber(),
        endLine: typeAlias.getEndLineNumber(),
        metadata: {
          isExported: typeAlias.isExported(),
          typeParameters: typeAlias.getTypeParameters().map(tp => tp.getName()),
          type: typeAlias.getTypeNode().getText()
        }
      };

      elements.push(element);
    });

    return elements;
  }

  private extractImports(sourceFile: SourceFile, context: ParserContext): CodeElement[] {
    const elements: CodeElement[] = [];

    sourceFile.getImportDeclarations().forEach(importDeclaration => {
      const moduleSpecifier = importDeclaration.getModuleSpecifierValue();
      const namedImports = importDeclaration.getNamedImports();
      const defaultImport = importDeclaration.getDefaultImport();
      const namespaceImport = importDeclaration.getNamespaceImport();

      const element: CodeElement = {
        id: this.generateId(context.filePath, `import-${moduleSpecifier}`),
        name: `import-${moduleSpecifier}`,
        type: ElementType.IMPORT,
        filePath: context.filePath,
        startLine: importDeclaration.getStartLineNumber(),
        endLine: importDeclaration.getEndLineNumber(),
        metadata: {
          from: moduleSpecifier,
          namedImports: namedImports.map(ni => ni.getName()),
          defaultImport: defaultImport?.getText(),
          namespaceImport: namespaceImport?.getText(),
          isTypeOnly: importDeclaration.isTypeOnly()
        }
      };

      elements.push(element);
    });

    return elements;
  }

  private extractExports(sourceFile: SourceFile, context: ParserContext): CodeElement[] {
    const elements: CodeElement[] = [];

    sourceFile.getExportDeclarations().forEach(exportDeclaration => {
      const moduleSpecifier = exportDeclaration.getModuleSpecifierValue();
      const namedExports = exportDeclaration.getNamedExports();

      const element: CodeElement = {
        id: this.generateId(context.filePath, `export-${moduleSpecifier || 'local'}`),
        name: `export-${moduleSpecifier || 'local'}`,
        type: ElementType.EXPORT,
        filePath: context.filePath,
        startLine: exportDeclaration.getStartLineNumber(),
        endLine: exportDeclaration.getEndLineNumber(),
        metadata: {
          from: moduleSpecifier,
          namedExports: namedExports.map(ne => ne.getName()),
          isTypeOnly: exportDeclaration.isTypeOnly()
        }
      };

      elements.push(element);
    });

    return elements;
  }

  private extractDecorators(sourceFile: SourceFile, context: ParserContext): CodeElement[] {
    const elements: CodeElement[] = [];
    const decorators = new Set<string>();

    // Find all decorators in the file
    sourceFile.forEachDescendant(node => {
      if (ts.isDecorator(node.compilerNode)) {
        const decoratorName = node.getText().replace('@', '');
        decorators.add(decoratorName);
      }
    });

    decorators.forEach(decoratorName => {
      const element: CodeElement = {
        id: this.generateId(context.filePath, `decorator-${decoratorName}`),
        name: decoratorName,
        type: ElementType.DECORATOR,
        filePath: context.filePath,
        startLine: 1,
        endLine: 1,
        metadata: {
          usage: 'decorator'
        }
      };

      elements.push(element);
    });

    return elements;
  }

  private extractInheritanceRelationships(sourceFile: SourceFile, elements: CodeElement[]): Relationship[] {
    const relationships: Relationship[] = [];

    sourceFile.getClasses().forEach(classDeclaration => {
      const className = classDeclaration.getName() || 'AnonymousClass';
      const sourceElement = elements.find(e => e.name === className && e.type === ElementType.CLASS);

      if (!sourceElement) return;

      // Inheritance (extends)
      const extendsClause = classDeclaration.getExtends();
      if (extendsClause) {
        const parentClassName = extendsClause.getExpression().getText();
        const targetElement = elements.find(e => e.name === parentClassName);

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

      // Implementation (implements)
      classDeclaration.getImplements().forEach(implementsClause => {
        const interfaceName = implementsClause.getExpression().getText();
        const targetElement = elements.find(e => e.name === interfaceName);

        if (targetElement) {
          relationships.push({
            id: `${sourceElement.id}-implements-${targetElement.id}`,
            sourceId: sourceElement.id,
            targetId: targetElement.id,
            type: RelationshipType.IMPLEMENTS,
            weight: 1,
            metadata: {
              confidence: 1.0,
              direction: 'unidirectional',
              category: 'structural',
              tags: ['implementation', 'interface']
            }
          });
        }
      });
    });

    return relationships;
  }

  private extractCallRelationships(sourceFile: SourceFile, elements: CodeElement[]): Relationship[] {
    const relationships: Relationship[] = [];

    sourceFile.forEachDescendant(node => {
      if (ts.isCallExpression(node.compilerNode)) {
        const callExpression = node.asKindOrThrow(SyntaxKind.CallExpression);
        const callerContext = this.findContainingElement(callExpression, elements);
        const calledFunction = this.extractCalledFunction(callExpression);

        if (callerContext && calledFunction) {
          const targetElement = elements.find(e => e.name === calledFunction);

          if (targetElement) {
            relationships.push({
              id: `${callerContext.id}-calls-${targetElement.id}`,
              sourceId: callerContext.id,
              targetId: targetElement.id,
              type: RelationshipType.CALLS,
              weight: 1,
              metadata: {
                confidence: 0.8,
                direction: 'unidirectional',
                category: 'behavioral',
                tags: ['method-call', 'invocation']
              }
            });
          }
        }
      }
    });

    return relationships;
  }

  private extractDependencyRelationships(sourceFile: SourceFile, elements: CodeElement[]): Relationship[] {
    const relationships: Relationship[] = [];

    // Property dependencies
    sourceFile.getClasses().forEach(classDeclaration => {
      const className = classDeclaration.getName() || 'AnonymousClass';
      const sourceElement = elements.find(e => e.name === className);

      if (!sourceElement) return;

      classDeclaration.getProperties().forEach(property => {
        const propertyType = property.getTypeNode()?.getText();
        if (propertyType) {
          const targetElement = elements.find(e => e.name === propertyType);

          if (targetElement) {
            relationships.push({
              id: `${sourceElement.id}-depends-on-${targetElement.id}`,
              sourceId: sourceElement.id,
              targetId: targetElement.id,
              type: RelationshipType.DEPENDS_ON,
              weight: 1,
              metadata: {
                confidence: 0.9,
                direction: 'unidirectional',
                category: 'structural',
                tags: ['property', 'type-dependency'],
                description: `Property: ${property.getName()}`
              }
            });
          }
        }
      });
    });

    return relationships;
  }

  private extractCompositionRelationships(sourceFile: SourceFile, elements: CodeElement[]): Relationship[] {
    const relationships: Relationship[] = [];

    sourceFile.getClasses().forEach(classDeclaration => {
      const className = classDeclaration.getName() || 'AnonymousClass';
      const sourceElement = elements.find(e => e.name === className);

      if (!sourceElement) return;

      // Constructor parameters often indicate composition
      classDeclaration.getConstructors().forEach(constructor => {
        constructor.getParameters().forEach(parameter => {
          const parameterType = parameter.getTypeNode()?.getText();
          if (parameterType) {
            const targetElement = elements.find(e => e.name === parameterType);

            if (targetElement) {
              relationships.push({
                id: `${sourceElement.id}-composes-${targetElement.id}`,
                sourceId: sourceElement.id,
                targetId: targetElement.id,
                type: RelationshipType.COMPOSITION,
                weight: 1,
                metadata: {
                  confidence: 0.7,
                  direction: 'unidirectional',
                  category: 'structural',
                  tags: ['composition', 'constructor-injection'],
                  description: `Constructor parameter: ${parameter.getName()}`
                }
              });
            }
          }
        });
      });
    });

    return relationships;
  }

  // Helper methods

  private generateId(filePath: string, name: string): string {
    const fileName = filePath.split('/').pop()?.replace(/\.[^/.]+$/, '') || 'unknown';
    return `${fileName}:${name}`;
  }

  private calculateClassComplexity(classDeclaration: any): number {
    let complexity = 1; // Base complexity

    // Add complexity for methods
    complexity += classDeclaration.getMethods().length * 2;

    // Add complexity for properties
    complexity += classDeclaration.getProperties().length;

    // Add complexity for inheritance
    if (classDeclaration.getExtends()) complexity += 2;
    complexity += classDeclaration.getImplements().length;

    return complexity;
  }

  private calculateFunctionComplexity(functionDeclaration: any): number {
    let complexity = 1; // Base complexity

    // Add complexity for parameters
    complexity += functionDeclaration.getParameters().length * 0.5;

    // Add complexity for control flow (this would need more detailed AST analysis)
    const body = functionDeclaration.getBody();
    if (body) {
      const text = body.getText();
      complexity += (text.match(/if|for|while|switch|catch/g) || []).length;
    }

    return complexity;
  }

  private extractFunctionCalls(functionDeclaration: any): string[] {
    const calls: string[] = [];

    functionDeclaration.forEachDescendant((node: any) => {
      if (node.getKind() === SyntaxKind.CallExpression) {
        const expression = node.getExpression();
        if (expression) {
          calls.push(expression.getText());
        }
      }
    });

    return calls;
  }

  private findContainingElement(node: any, elements: CodeElement[]): CodeElement | null {
    let current = node.getParent();

    while (current) {
      if (current.getKind() === SyntaxKind.ClassDeclaration ||
          current.getKind() === SyntaxKind.FunctionDeclaration ||
          current.getKind() === SyntaxKind.MethodDeclaration) {

        const name = current.getName ? current.getName() : 'unknown';
        const element = elements.find(e => e.name === name);
        if (element) {
          return element;
        }
      }
      current = current.getParent();
    }

    return null;
  }

  private extractCalledFunction(callExpression: any): string | null {
    const expression = callExpression.getExpression();
    if (!expression) return null;

    // Handle different call patterns
    if (expression.getKind() === SyntaxKind.Identifier) {
      return expression.getText();
    } else if (expression.getKind() === SyntaxKind.PropertyAccessExpression) {
      return expression.getName();
    }

    return expression.getText();
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