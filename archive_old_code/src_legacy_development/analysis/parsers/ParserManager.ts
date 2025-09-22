/**
 * Parser Manager - Coordinates AST parsing across different file types
 * Supports TypeScript, JavaScript, and trading system specific patterns
 */

import { promises as fs } from 'fs';
import * as path from 'path';
import { TypeScriptParser } from './TypeScriptParser';
import { JavaScriptParser } from './JavaScriptParser';
import { TradingPatternParser } from './TradingPatternParser';
import { DatabaseSchemaParser } from './DatabaseSchemaParser';
import { APIEndpointParser } from './APIEndpointParser';
import {
  ParserConfig,
  CodeElement,
  Relationship,
  ParserContext,
  Logger,
  ElementType,
  RelationshipType
} from '../types';

export interface Parser {
  name: string;
  supportedExtensions: string[];
  canParse(filePath: string): boolean;
  parse(context: ParserContext): Promise<CodeElement[]>;
  extractRelationships(context: ParserContext, elements: CodeElement[]): Promise<Relationship[]>;
}

export class ParserManager {
  private parsers: Map<string, Parser> = new Map();
  private config: ParserConfig[];
  private logger: Logger;

  constructor(config: ParserConfig[], logger: Logger) {
    this.config = config;
    this.logger = logger;
  }

  async initialize(): Promise<void> {
    this.logger.info('Initializing Parser Manager...');

    // Register core parsers
    this.registerParser(new TypeScriptParser(this.logger));
    this.registerParser(new JavaScriptParser(this.logger));
    this.registerParser(new TradingPatternParser(this.logger));
    this.registerParser(new DatabaseSchemaParser(this.logger));
    this.registerParser(new APIEndpointParser(this.logger));

    this.logger.info(`Registered ${this.parsers.size} parsers`);
  }

  registerParser(parser: Parser): void {
    this.parsers.set(parser.name, parser);
    this.logger.debug(`Registered parser: ${parser.name}`);
  }

  async parseFile(filePath: string): Promise<CodeElement[]> {
    const absolutePath = path.resolve(filePath);

    try {
      // Check if file exists
      await fs.access(absolutePath);

      // Read file content
      const content = await fs.readFile(absolutePath, 'utf-8');

      // Find appropriate parser
      const parser = this.findParser(absolutePath);
      if (!parser) {
        this.logger.warn(`No parser found for file: ${absolutePath}`);
        return [];
      }

      // Create parser context
      const context: ParserContext = {
        filePath: absolutePath,
        content,
        ast: null,
        sourceFile: null,
        metadata: {
          size: content.length,
          extension: path.extname(absolutePath),
          lastModified: (await fs.stat(absolutePath)).mtime
        }
      };

      // Parse the file
      const elements = await parser.parse(context);

      // Add file metadata to elements
      elements.forEach(element => {
        element.filePath = absolutePath;
        element.metadata = {
          ...element.metadata,
          parser: parser.name,
          fileSize: content.length
        };
      });

      this.logger.debug(`Parsed ${elements.length} elements from ${path.basename(absolutePath)}`);
      return elements;

    } catch (error) {
      this.logger.error(`Failed to parse file ${absolutePath}:`, error);
      return [];
    }
  }

  async extractRelationships(filePath: string, elements: CodeElement[]): Promise<Relationship[]> {
    const absolutePath = path.resolve(filePath);

    try {
      const content = await fs.readFile(absolutePath, 'utf-8');
      const parser = this.findParser(absolutePath);

      if (!parser) {
        return [];
      }

      const context: ParserContext = {
        filePath: absolutePath,
        content,
        ast: null,
        sourceFile: null,
        metadata: {}
      };

      const relationships = await parser.extractRelationships(context, elements);

      this.logger.debug(`Extracted ${relationships.length} relationships from ${path.basename(absolutePath)}`);
      return relationships;

    } catch (error) {
      this.logger.error(`Failed to extract relationships from ${absolutePath}:`, error);
      return [];
    }
  }

  async parseMultipleFiles(filePaths: string[]): Promise<Map<string, CodeElement[]>> {
    const results = new Map<string, CodeElement[]>();

    // Parse files in parallel for better performance
    const parsePromises = filePaths.map(async (filePath) => {
      const elements = await this.parseFile(filePath);
      return { filePath, elements };
    });

    const parseResults = await Promise.allSettled(parsePromises);

    parseResults.forEach((result, index) => {
      const filePath = filePaths[index];
      if (result.status === 'fulfilled') {
        results.set(filePath, result.value.elements);
      } else {
        this.logger.error(`Failed to parse ${filePath}:`, result.reason);
        results.set(filePath, []);
      }
    });

    return results;
  }

  async extractAllRelationships(fileElementMap: Map<string, CodeElement[]>): Promise<Relationship[]> {
    const allRelationships: Relationship[] = [];

    // Extract relationships for each file
    for (const [filePath, elements] of fileElementMap) {
      try {
        const relationships = await this.extractRelationships(filePath, elements);
        allRelationships.push(...relationships);
      } catch (error) {
        this.logger.error(`Failed to extract relationships from ${filePath}:`, error);
      }
    }

    // Add cross-file relationships
    const crossFileRelationships = await this.extractCrossFileRelationships(fileElementMap);
    allRelationships.push(...crossFileRelationships);

    return allRelationships;
  }

  getSupportedExtensions(): string[] {
    const extensions = new Set<string>();

    for (const parser of this.parsers.values()) {
      parser.supportedExtensions.forEach(ext => extensions.add(ext));
    }

    return Array.from(extensions);
  }

  getParserStats(): Record<string, any> {
    const stats: Record<string, any> = {};

    for (const [name, parser] of this.parsers) {
      stats[name] = {
        supportedExtensions: parser.supportedExtensions,
        enabled: this.isParserEnabled(name)
      };
    }

    return stats;
  }

  private findParser(filePath: string): Parser | null {
    const extension = path.extname(filePath).toLowerCase();

    for (const parser of this.parsers.values()) {
      if (parser.supportedExtensions.includes(extension) &&
          parser.canParse(filePath) &&
          this.isParserEnabled(parser.name)) {
        return parser;
      }
    }

    return null;
  }

  private isParserEnabled(parserName: string): boolean {
    const config = this.config.find(c => c.name === parserName);
    return config ? config.enabled : true;
  }

  private async extractCrossFileRelationships(fileElementMap: Map<string, CodeElement[]>): Promise<Relationship[]> {
    const relationships: Relationship[] = [];
    const allElements = new Map<string, CodeElement>();

    // Create a global element map
    for (const elements of fileElementMap.values()) {
      elements.forEach(element => {
        allElements.set(element.id, element);
      });
    }

    // Find import/export relationships
    for (const [filePath, elements] of fileElementMap) {
      const imports = elements.filter(e => e.type === ElementType.IMPORT);
      const exports = elements.filter(e => e.type === ElementType.EXPORT);

      // Match imports with exports
      for (const importElement of imports) {
        const importPath = this.resolveImportPath(filePath, importElement.metadata.from);
        const exportingElements = this.findExportingElements(importPath, fileElementMap);

        for (const exportElement of exportingElements) {
          if (this.isMatchingImportExport(importElement, exportElement)) {
            const relationship: Relationship = {
              id: `${importElement.id}-imports-${exportElement.id}`,
              sourceId: importElement.id,
              targetId: exportElement.id,
              type: RelationshipType.IMPORTS,
              weight: 1,
              metadata: {
                confidence: 0.9,
                direction: 'unidirectional',
                category: 'structural',
                tags: ['import', 'dependency']
              }
            };
            relationships.push(relationship);
          }
        }
      }

      // Find API endpoint relationships
      relationships.push(...this.extractAPIRelationships(elements, allElements));

      // Find database relationships
      relationships.push(...this.extractDatabaseRelationships(elements, allElements));

      // Find trading system relationships
      relationships.push(...this.extractTradingRelationships(elements, allElements));
    }

    return relationships;
  }

  private resolveImportPath(currentFile: string, importPath: string): string {
    if (importPath.startsWith('.')) {
      return path.resolve(path.dirname(currentFile), importPath);
    }
    return importPath;
  }

  private findExportingElements(importPath: string, fileElementMap: Map<string, CodeElement[]>): CodeElement[] {
    const possibleFiles = Array.from(fileElementMap.keys()).filter(filePath => {
      const normalized = path.resolve(filePath);
      return normalized.includes(importPath) || importPath.includes(path.basename(filePath, path.extname(filePath)));
    });

    const exportElements: CodeElement[] = [];
    for (const filePath of possibleFiles) {
      const elements = fileElementMap.get(filePath) || [];
      exportElements.push(...elements.filter(e => e.type === ElementType.EXPORT));
    }

    return exportElements;
  }

  private isMatchingImportExport(importElement: CodeElement, exportElement: CodeElement): boolean {
    const importName = importElement.metadata.imported || importElement.name;
    const exportName = exportElement.metadata.exported || exportElement.name;
    return importName === exportName;
  }

  private extractAPIRelationships(elements: CodeElement[], allElements: Map<string, CodeElement>): Relationship[] {
    const relationships: Relationship[] = [];
    const apiElements = elements.filter(e => e.type === ElementType.API_ENDPOINT);

    for (const apiElement of apiElements) {
      // Find elements that call this API
      const callers = Array.from(allElements.values()).filter(element => {
        return element.metadata.apiCalls &&
               element.metadata.apiCalls.includes(apiElement.name);
      });

      for (const caller of callers) {
        const relationship: Relationship = {
          id: `${caller.id}-calls-api-${apiElement.id}`,
          sourceId: caller.id,
          targetId: apiElement.id,
          type: RelationshipType.API_CALL,
          weight: 1,
          metadata: {
            confidence: 0.8,
            direction: 'unidirectional',
            category: 'behavioral',
            tags: ['api', 'http']
          }
        };
        relationships.push(relationship);
      }
    }

    return relationships;
  }

  private extractDatabaseRelationships(elements: CodeElement[], allElements: Map<string, CodeElement>): Relationship[] {
    const relationships: Relationship[] = [];
    const dbElements = elements.filter(e => e.type === ElementType.DATABASE_ENTITY);

    for (const dbElement of dbElements) {
      // Find foreign key relationships
      if (dbElement.metadata.foreignKeys) {
        for (const fk of dbElement.metadata.foreignKeys) {
          const referencedEntity = Array.from(allElements.values()).find(e =>
            e.type === ElementType.DATABASE_ENTITY && e.name === fk.referencedTable
          );

          if (referencedEntity) {
            const relationship: Relationship = {
              id: `${dbElement.id}-references-${referencedEntity.id}`,
              sourceId: dbElement.id,
              targetId: referencedEntity.id,
              type: RelationshipType.DATABASE_RELATION,
              weight: 1,
              metadata: {
                confidence: 1.0,
                direction: 'unidirectional',
                category: 'data',
                tags: ['foreign-key', 'database'],
                description: `Foreign key: ${fk.column} -> ${fk.referencedColumn}`
              }
            };
            relationships.push(relationship);
          }
        }
      }
    }

    return relationships;
  }

  private extractTradingRelationships(elements: CodeElement[], allElements: Map<string, CodeElement>): Relationship[] {
    const relationships: Relationship[] = [];
    const tradingElements = elements.filter(e =>
      e.type === ElementType.TRADING_STRATEGY ||
      e.type === ElementType.RISK_COMPONENT
    );

    for (const tradingElement of tradingElements) {
      // Find strategy usage relationships
      if (tradingElement.type === ElementType.TRADING_STRATEGY) {
        const users = Array.from(allElements.values()).filter(element => {
          return element.metadata.strategies &&
                 element.metadata.strategies.includes(tradingElement.name);
        });

        for (const user of users) {
          const relationship: Relationship = {
            id: `${user.id}-uses-strategy-${tradingElement.id}`,
            sourceId: user.id,
            targetId: tradingElement.id,
            type: RelationshipType.STRATEGY_USAGE,
            weight: 1,
            metadata: {
              confidence: 0.9,
              direction: 'unidirectional',
              category: 'trading',
              tags: ['strategy', 'trading']
            }
          };
          relationships.push(relationship);
        }
      }

      // Find risk monitoring relationships
      if (tradingElement.type === ElementType.RISK_COMPONENT) {
        const monitored = Array.from(allElements.values()).filter(element => {
          return element.metadata.riskMonitoring &&
                 element.metadata.riskMonitoring.includes(tradingElement.name);
        });

        for (const monitoredElement of monitored) {
          const relationship: Relationship = {
            id: `${tradingElement.id}-monitors-${monitoredElement.id}`,
            sourceId: tradingElement.id,
            targetId: monitoredElement.id,
            type: RelationshipType.RISK_MONITORING,
            weight: 1,
            metadata: {
              confidence: 0.8,
              direction: 'unidirectional',
              category: 'trading',
              tags: ['risk', 'monitoring']
            }
          };
          relationships.push(relationship);
        }
      }
    }

    return relationships;
  }
}