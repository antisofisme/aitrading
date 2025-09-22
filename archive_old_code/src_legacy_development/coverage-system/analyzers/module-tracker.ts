/**
 * Module and Component-Level Coverage Tracker
 * Provides detailed tracking and analysis at module and component levels
 */

import { promises as fs } from 'fs';
import * as path from 'path';
import { FileCoverage, CoverageSummary } from '../core/coverage-analyzer';
import { ModuleCoverageConfig } from '../config/coverage-config';

export interface ModuleTracker {
  id: string;
  name: string;
  path: string;
  type: ModuleType;
  files: Map<string, FileCoverage>;
  components: Map<string, ComponentCoverage>;
  coverage: ModuleCoverageData;
  dependencies: ModuleDependency[];
  metadata: ModuleMetadata;
  history: ModuleHistoryPoint[];
}

export type ModuleType =
  | 'business-logic'
  | 'data-access'
  | 'api-controller'
  | 'service'
  | 'utility'
  | 'component'
  | 'middleware'
  | 'configuration';

export interface ComponentCoverage {
  id: string;
  name: string;
  type: ComponentType;
  filePath: string;
  methods: MethodCoverage[];
  properties: PropertyCoverage[];
  coverage: CoverageSummary;
  complexity: ComponentComplexity;
  testability: TestabilityScore;
  dependencies: string[];
}

export type ComponentType =
  | 'class'
  | 'function'
  | 'interface'
  | 'type'
  | 'constant'
  | 'enum'
  | 'hook'
  | 'component';

export interface MethodCoverage {
  name: string;
  signature: string;
  coverage: {
    lines: number;
    branches: number;
    statements: number;
  };
  complexity: number;
  testCases: TestCase[];
  uncoveredPaths: CodePath[];
}

export interface PropertyCoverage {
  name: string;
  type: string;
  accessed: boolean;
  modified: boolean;
  testCoverage: number;
}

export interface ModuleCoverageData {
  summary: CoverageSummary;
  byType: Map<ComponentType, CoverageSummary>;
  byComplexity: Map<ComplexityLevel, CoverageSummary>;
  byTestability: Map<TestabilityLevel, CoverageSummary>;
  trends: ModuleTrend[];
}

export interface ModuleDependency {
  moduleId: string;
  type: DependencyType;
  strength: number; // 0-1 scale
  testCoupling: number; // 0-1 scale
  riskFactor: number; // 0-1 scale
}

export type DependencyType = 'import' | 'injection' | 'composition' | 'inheritance' | 'configuration';

export interface ModuleMetadata {
  owner: string;
  maintainers: string[];
  lastModified: Date;
  createdDate: Date;
  version: string;
  tags: string[];
  criticality: CriticalityLevel;
  businessValue: BusinessValueLevel;
  technicalDebt: TechnicalDebtLevel;
}

export type CriticalityLevel = 'low' | 'medium' | 'high' | 'critical';
export type BusinessValueLevel = 'low' | 'medium' | 'high' | 'strategic';
export type TechnicalDebtLevel = 'low' | 'medium' | 'high' | 'severe';
export type ComplexityLevel = 'simple' | 'moderate' | 'complex' | 'very-complex';
export type TestabilityLevel = 'easy' | 'moderate' | 'difficult' | 'very-difficult';

export interface ComponentComplexity {
  cyclomatic: number;
  cognitive: number;
  maintainability: number;
  readability: number;
}

export interface TestabilityScore {
  overall: number;
  isolation: number;
  mocking: number;
  setup: number;
  assertions: number;
  factors: TestabilityFactor[];
}

export interface TestabilityFactor {
  type: 'dependency-injection' | 'global-state' | 'external-dependencies' | 'side-effects' | 'complexity';
  impact: number;
  description: string;
}

export interface TestCase {
  name: string;
  type: 'unit' | 'integration' | 'functional' | 'performance';
  coverage: {
    lines: number[];
    branches: number[];
    statements: number[];
  };
  assertions: number;
  setup: string;
}

export interface CodePath {
  path: string;
  conditions: string[];
  probability: number;
  businessImpact: number;
}

export interface ModuleHistoryPoint {
  timestamp: Date;
  coverage: CoverageSummary;
  fileCount: number;
  componentCount: number;
  complexity: number;
  testability: number;
  version: string;
  commit: string;
}

export interface ModuleTrend {
  metric: string;
  direction: 'improving' | 'stable' | 'declining';
  velocity: number;
  confidence: number;
}

export interface ModuleInsight {
  type: 'strength' | 'weakness' | 'opportunity' | 'risk';
  title: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
  actionable: boolean;
  recommendations: string[];
}

export interface ModuleComparisonResult {
  modules: ModuleTracker[];
  rankings: ModuleRanking[];
  insights: ModuleInsight[];
  recommendations: ModuleRecommendation[];
}

export interface ModuleRanking {
  moduleId: string;
  rank: number;
  score: number;
  category: 'coverage' | 'quality' | 'testability' | 'maintainability';
  percentile: number;
}

export interface ModuleRecommendation {
  moduleId: string;
  type: 'improvement' | 'maintenance' | 'refactoring' | 'testing';
  priority: 'high' | 'medium' | 'low';
  description: string;
  effort: string;
  impact: string;
}

export class ModuleLevelTracker {
  private modules: Map<string, ModuleTracker> = new Map();
  private config: ModuleCoverageConfig[];

  constructor(moduleConfigs: ModuleCoverageConfig[]) {
    this.config = moduleConfigs;
  }

  async analyzeModule(
    moduleConfig: ModuleCoverageConfig,
    files: Map<string, FileCoverage>
  ): Promise<ModuleTracker> {
    const moduleId = this.generateModuleId(moduleConfig);

    // Filter files for this module
    const moduleFiles = new Map<string, FileCoverage>();
    for (const [filePath, fileCoverage] of files.entries()) {
      if (filePath.startsWith(moduleConfig.path)) {
        moduleFiles.set(filePath, fileCoverage);
      }
    }

    // Analyze components within the module
    const components = await this.analyzeComponents(moduleFiles);

    // Calculate module coverage
    const coverage = this.calculateModuleCoverage(moduleFiles, components);

    // Analyze dependencies
    const dependencies = await this.analyzeDependencies(moduleConfig, moduleFiles);

    // Generate metadata
    const metadata = await this.generateModuleMetadata(moduleConfig, moduleFiles);

    // Load historical data
    const history = await this.loadModuleHistory(moduleId);

    const moduleTracker: ModuleTracker = {
      id: moduleId,
      name: moduleConfig.name,
      path: moduleConfig.path,
      type: this.inferModuleType(moduleConfig),
      files: moduleFiles,
      components,
      coverage,
      dependencies,
      metadata,
      history
    };

    this.modules.set(moduleId, moduleTracker);
    return moduleTracker;
  }

  private async analyzeComponents(files: Map<string, FileCoverage>): Promise<Map<string, ComponentCoverage>> {
    const components = new Map<string, ComponentCoverage>();

    for (const [filePath, fileCoverage] of files.entries()) {
      const fileComponents = await this.extractComponentsFromFile(filePath, fileCoverage);
      for (const [componentId, component] of fileComponents.entries()) {
        components.set(componentId, component);
      }
    }

    return components;
  }

  private async extractComponentsFromFile(
    filePath: string,
    fileCoverage: FileCoverage
  ): Promise<Map<string, ComponentCoverage>> {
    const components = new Map<string, ComponentCoverage>();

    try {
      const sourceCode = await fs.readFile(filePath, 'utf-8');
      const parsedComponents = this.parseSourceCode(sourceCode, filePath);

      for (const parsed of parsedComponents) {
        const component: ComponentCoverage = {
          id: `${filePath}:${parsed.name}`,
          name: parsed.name,
          type: parsed.type,
          filePath,
          methods: parsed.methods.map(method => this.analyzeMethodCoverage(method, fileCoverage)),
          properties: parsed.properties.map(prop => this.analyzePropertyCoverage(prop, fileCoverage)),
          coverage: this.calculateComponentCoverage(parsed, fileCoverage),
          complexity: this.calculateComponentComplexity(parsed),
          testability: this.calculateTestabilityScore(parsed),
          dependencies: parsed.dependencies || []
        };

        components.set(component.id, component);
      }
    } catch (error) {
      console.warn(`Could not analyze components in ${filePath}:`, error.message);
    }

    return components;
  }

  private parseSourceCode(sourceCode: string, filePath: string): ParsedComponent[] {
    // This is a simplified parser - in practice, you'd use AST parsing
    const components: ParsedComponent[] = [];
    const ext = path.extname(filePath).toLowerCase();

    if (ext === '.ts' || ext === '.js') {
      components.push(...this.parseJavaScriptTypeScript(sourceCode));
    } else if (ext === '.py') {
      components.push(...this.parsePython(sourceCode));
    }

    return components;
  }

  private parseJavaScriptTypeScript(sourceCode: string): ParsedComponent[] {
    const components: ParsedComponent[] = [];

    // Simple regex-based parsing (in practice, use proper AST parsing)
    const classMatches = sourceCode.match(/class\s+(\w+)/g) || [];
    const functionMatches = sourceCode.match(/(?:function\s+(\w+)|const\s+(\w+)\s*=)/g) || [];
    const interfaceMatches = sourceCode.match(/interface\s+(\w+)/g) || [];

    classMatches.forEach(match => {
      const name = match.replace(/class\s+/, '');
      components.push({
        name,
        type: 'class',
        methods: this.extractMethods(sourceCode, name),
        properties: this.extractProperties(sourceCode, name),
        dependencies: this.extractDependencies(sourceCode)
      });
    });

    functionMatches.forEach(match => {
      const name = match.replace(/(?:function\s+|const\s+|\s*=.*)/g, '');
      if (name && name !== 'function') {
        components.push({
          name,
          type: 'function',
          methods: [],
          properties: [],
          dependencies: this.extractDependencies(sourceCode)
        });
      }
    });

    interfaceMatches.forEach(match => {
      const name = match.replace(/interface\s+/, '');
      components.push({
        name,
        type: 'interface',
        methods: [],
        properties: this.extractInterfaceProperties(sourceCode, name),
        dependencies: []
      });
    });

    return components;
  }

  private parsePython(sourceCode: string): ParsedComponent[] {
    const components: ParsedComponent[] = [];

    const classMatches = sourceCode.match(/class\s+(\w+)/g) || [];
    const functionMatches = sourceCode.match(/def\s+(\w+)/g) || [];

    classMatches.forEach(match => {
      const name = match.replace(/class\s+/, '');
      components.push({
        name,
        type: 'class',
        methods: this.extractPythonMethods(sourceCode, name),
        properties: this.extractPythonProperties(sourceCode, name),
        dependencies: this.extractPythonDependencies(sourceCode)
      });
    });

    functionMatches.forEach(match => {
      const name = match.replace(/def\s+/, '');
      components.push({
        name,
        type: 'function',
        methods: [],
        properties: [],
        dependencies: this.extractPythonDependencies(sourceCode)
      });
    });

    return components;
  }

  private extractMethods(sourceCode: string, className: string): ParsedMethod[] {
    // Simplified method extraction
    const methodRegex = new RegExp(`class\\s+${className}[\\s\\S]*?{([\\s\\S]*?)}`, 'm');
    const classBody = sourceCode.match(methodRegex)?.[1] || '';

    const methodMatches = classBody.match(/(\w+)\s*\([^)]*\)\s*{/g) || [];

    return methodMatches.map(match => {
      const name = match.replace(/\s*\([^)]*\)\s*{/, '');
      return {
        name,
        signature: match.replace(/\s*{$/, ''),
        complexity: this.estimateMethodComplexity(classBody, name)
      };
    });
  }

  private extractProperties(sourceCode: string, className: string): ParsedProperty[] {
    // Simplified property extraction
    const propertyMatches = sourceCode.match(/this\.(\w+)\s*=/g) || [];

    return propertyMatches.map(match => {
      const name = match.replace(/this\.|\s*=/g, '');
      return {
        name,
        type: 'unknown',
        isPublic: !name.startsWith('_')
      };
    });
  }

  private extractDependencies(sourceCode: string): string[] {
    const importMatches = sourceCode.match(/import\s+.*?from\s+['"]([^'"]+)['"]/g) || [];
    const requireMatches = sourceCode.match(/require\(['"]([^'"]+)['"]\)/g) || [];

    const imports = importMatches.map(match =>
      match.replace(/.*from\s+['"]([^'"]+)['"]/, '$1')
    );

    const requires = requireMatches.map(match =>
      match.replace(/require\(['"]([^'"]+)['"]\)/, '$1')
    );

    return [...imports, ...requires];
  }

  private extractInterfaceProperties(sourceCode: string, interfaceName: string): ParsedProperty[] {
    const interfaceRegex = new RegExp(`interface\\s+${interfaceName}\\s*{([\\s\\S]*?)}`, 'm');
    const interfaceBody = sourceCode.match(interfaceRegex)?.[1] || '';

    const propertyMatches = interfaceBody.match(/(\w+)\s*:\s*([^;]+);/g) || [];

    return propertyMatches.map(match => {
      const [, name, type] = match.match(/(\w+)\s*:\s*([^;]+);/) || [];
      return {
        name,
        type: type?.trim() || 'unknown',
        isPublic: true
      };
    });
  }

  private extractPythonMethods(sourceCode: string, className: string): ParsedMethod[] {
    const classRegex = new RegExp(`class\\s+${className}[\\s\\S]*?(?=class|$)`, 'm');
    const classBody = sourceCode.match(classRegex)?.[0] || '';

    const methodMatches = classBody.match(/def\s+(\w+)\s*\([^)]*\):/g) || [];

    return methodMatches.map(match => {
      const name = match.replace(/def\s+|\s*\([^)]*\):/, '');
      return {
        name,
        signature: match.replace(/:$/, ''),
        complexity: this.estimateMethodComplexity(classBody, name)
      };
    });
  }

  private extractPythonProperties(sourceCode: string, className: string): ParsedProperty[] {
    const classRegex = new RegExp(`class\\s+${className}[\\s\\S]*?(?=class|$)`, 'm');
    const classBody = sourceCode.match(classRegex)?.[0] || '';

    const propertyMatches = classBody.match(/self\.(\w+)\s*=/g) || [];

    return propertyMatches.map(match => {
      const name = match.replace(/self\.|\s*=/g, '');
      return {
        name,
        type: 'unknown',
        isPublic: !name.startsWith('_')
      };
    });
  }

  private extractPythonDependencies(sourceCode: string): string[] {
    const importMatches = sourceCode.match(/(?:import\s+(\w+)|from\s+(\w+)\s+import)/g) || [];

    return importMatches.map(match => {
      if (match.startsWith('import ')) {
        return match.replace('import ', '');
      } else {
        return match.replace(/from\s+(\w+)\s+import.*/, '$1');
      }
    });
  }

  private estimateMethodComplexity(classBody: string, methodName: string): number {
    // Simple complexity estimation based on control flow statements
    const methodRegex = new RegExp(`${methodName}\\s*\\([^)]*\\)[\\s\\S]*?(?=def|class|$)`, 'm');
    const methodBody = classBody.match(methodRegex)?.[0] || '';

    const complexityKeywords = ['if', 'else', 'for', 'while', 'switch', 'case', 'try', 'catch', '&&', '||'];
    let complexity = 1; // Base complexity

    complexityKeywords.forEach(keyword => {
      const matches = (methodBody.match(new RegExp(`\\b${keyword}\\b`, 'g')) || []).length;
      complexity += matches;
    });

    return complexity;
  }

  private analyzeMethodCoverage(method: ParsedMethod, fileCoverage: FileCoverage): MethodCoverage {
    // This would require more sophisticated analysis to map methods to coverage data
    return {
      name: method.name,
      signature: method.signature,
      coverage: {
        lines: 0, // Would be calculated from actual coverage data
        branches: 0,
        statements: 0
      },
      complexity: method.complexity,
      testCases: [], // Would be extracted from test files
      uncoveredPaths: []
    };
  }

  private analyzePropertyCoverage(property: ParsedProperty, fileCoverage: FileCoverage): PropertyCoverage {
    return {
      name: property.name,
      type: property.type,
      accessed: false, // Would be determined from coverage data
      modified: false,
      testCoverage: 0
    };
  }

  private calculateComponentCoverage(component: ParsedComponent, fileCoverage: FileCoverage): CoverageSummary {
    // Simplified - would need actual mapping between components and coverage
    return {
      lines: { lines: 0, functions: 0, branches: 0, statements: 0 },
      functions: { lines: 0, functions: 0, branches: 0, statements: 0 },
      branches: { lines: 0, functions: 0, branches: 0, statements: 0 },
      statements: { lines: 0, functions: 0, branches: 0, statements: 0 },
      files: 1,
      totalSize: 0,
      averageComplexity: 0
    };
  }

  private calculateComponentComplexity(component: ParsedComponent): ComponentComplexity {
    const totalComplexity = component.methods.reduce((sum, method) => sum + method.complexity, 0);
    const avgComplexity = component.methods.length > 0 ? totalComplexity / component.methods.length : 1;

    return {
      cyclomatic: avgComplexity,
      cognitive: avgComplexity * 1.2, // Estimated
      maintainability: Math.max(0, 100 - avgComplexity * 5),
      readability: Math.max(0, 100 - component.dependencies.length * 2)
    };
  }

  private calculateTestabilityScore(component: ParsedComponent): TestabilityScore {
    const factors: TestabilityFactor[] = [];
    let score = 100;

    // Dependency injection
    if (component.dependencies.length > 5) {
      factors.push({
        type: 'external-dependencies',
        impact: -15,
        description: 'High number of external dependencies'
      });
      score -= 15;
    }

    // Complexity
    const avgComplexity = component.methods.reduce((sum, m) => sum + m.complexity, 0) / Math.max(1, component.methods.length);
    if (avgComplexity > 10) {
      factors.push({
        type: 'complexity',
        impact: -20,
        description: 'High method complexity'
      });
      score -= 20;
    }

    return {
      overall: Math.max(0, score),
      isolation: Math.max(0, 100 - component.dependencies.length * 5),
      mocking: component.dependencies.length < 3 ? 100 : 60,
      setup: component.methods.length < 10 ? 100 : 70,
      assertions: avgComplexity < 5 ? 100 : 80,
      factors
    };
  }

  private calculateModuleCoverage(
    files: Map<string, FileCoverage>,
    components: Map<string, ComponentCoverage>
  ): ModuleCoverageData {
    const summary = this.aggregateFileCoverage(files);
    const byType = this.groupCoverageByType(components);
    const byComplexity = this.groupCoverageByComplexity(components);
    const byTestability = this.groupCoverageByTestability(components);

    return {
      summary,
      byType,
      byComplexity,
      byTestability,
      trends: []
    };
  }

  private aggregateFileCoverage(files: Map<string, FileCoverage>): CoverageSummary {
    if (files.size === 0) {
      return {
        lines: { lines: 0, functions: 0, branches: 0, statements: 0 },
        functions: { lines: 0, functions: 0, branches: 0, statements: 0 },
        branches: { lines: 0, functions: 0, branches: 0, statements: 0 },
        statements: { lines: 0, functions: 0, branches: 0, statements: 0 },
        files: 0,
        totalSize: 0,
        averageComplexity: 0
      };
    }

    let totalLines = 0, coveredLines = 0;
    let totalFunctions = 0, coveredFunctions = 0;
    let totalBranches = 0, coveredBranches = 0;
    let totalStatements = 0, coveredStatements = 0;
    let totalSize = 0, totalComplexity = 0;

    for (const file of files.values()) {
      totalLines += file.lines.total;
      coveredLines += file.lines.covered;
      totalFunctions += file.functions.total;
      coveredFunctions += file.functions.covered;
      totalBranches += file.branches.total;
      coveredBranches += file.branches.covered;
      totalStatements += file.statements.total;
      coveredStatements += file.statements.covered;
      totalSize += file.size;
      totalComplexity += file.complexity;
    }

    const calculate = (covered: number, total: number) =>
      total === 0 ? 100 : Math.round((covered / total) * 100 * 100) / 100;

    return {
      lines: { lines: calculate(coveredLines, totalLines), functions: 0, branches: 0, statements: 0 },
      functions: { lines: 0, functions: calculate(coveredFunctions, totalFunctions), branches: 0, statements: 0 },
      branches: { lines: 0, functions: 0, branches: calculate(coveredBranches, totalBranches), statements: 0 },
      statements: { lines: 0, functions: 0, branches: 0, statements: calculate(coveredStatements, totalStatements) },
      files: files.size,
      totalSize,
      averageComplexity: files.size > 0 ? totalComplexity / files.size : 0
    };
  }

  private groupCoverageByType(components: Map<string, ComponentCoverage>): Map<ComponentType, CoverageSummary> {
    const grouped = new Map<ComponentType, CoverageSummary>();
    const typeGroups = new Map<ComponentType, ComponentCoverage[]>();

    // Group components by type
    for (const component of components.values()) {
      if (!typeGroups.has(component.type)) {
        typeGroups.set(component.type, []);
      }
      typeGroups.get(component.type)!.push(component);
    }

    // Calculate coverage for each type
    for (const [type, componentList] of typeGroups.entries()) {
      grouped.set(type, this.aggregateComponentCoverage(componentList));
    }

    return grouped;
  }

  private groupCoverageByComplexity(components: Map<string, ComponentCoverage>): Map<ComplexityLevel, CoverageSummary> {
    const grouped = new Map<ComplexityLevel, CoverageSummary>();
    const complexityGroups = new Map<ComplexityLevel, ComponentCoverage[]>();

    for (const component of components.values()) {
      const level = this.getComplexityLevel(component.complexity.cyclomatic);
      if (!complexityGroups.has(level)) {
        complexityGroups.set(level, []);
      }
      complexityGroups.get(level)!.push(component);
    }

    for (const [level, componentList] of complexityGroups.entries()) {
      grouped.set(level, this.aggregateComponentCoverage(componentList));
    }

    return grouped;
  }

  private groupCoverageByTestability(components: Map<string, ComponentCoverage>): Map<TestabilityLevel, CoverageSummary> {
    const grouped = new Map<TestabilityLevel, CoverageSummary>();
    const testabilityGroups = new Map<TestabilityLevel, ComponentCoverage[]>();

    for (const component of components.values()) {
      const level = this.getTestabilityLevel(component.testability.overall);
      if (!testabilityGroups.has(level)) {
        testabilityGroups.set(level, []);
      }
      testabilityGroups.get(level)!.push(component);
    }

    for (const [level, componentList] of testabilityGroups.entries()) {
      grouped.set(level, this.aggregateComponentCoverage(componentList));
    }

    return grouped;
  }

  private aggregateComponentCoverage(components: ComponentCoverage[]): CoverageSummary {
    // Simplified aggregation - would need actual coverage data
    return {
      lines: { lines: 0, functions: 0, branches: 0, statements: 0 },
      functions: { lines: 0, functions: 0, branches: 0, statements: 0 },
      branches: { lines: 0, functions: 0, branches: 0, statements: 0 },
      statements: { lines: 0, functions: 0, branches: 0, statements: 0 },
      files: components.length,
      totalSize: 0,
      averageComplexity: 0
    };
  }

  private getComplexityLevel(complexity: number): ComplexityLevel {
    if (complexity <= 5) return 'simple';
    if (complexity <= 10) return 'moderate';
    if (complexity <= 20) return 'complex';
    return 'very-complex';
  }

  private getTestabilityLevel(score: number): TestabilityLevel {
    if (score >= 80) return 'easy';
    if (score >= 60) return 'moderate';
    if (score >= 40) return 'difficult';
    return 'very-difficult';
  }

  private async analyzeDependencies(
    moduleConfig: ModuleCoverageConfig,
    files: Map<string, FileCoverage>
  ): Promise<ModuleDependency[]> {
    const dependencies: ModuleDependency[] = [];

    // Analyze import/require statements across all files
    for (const [filePath] of files.entries()) {
      try {
        const sourceCode = await fs.readFile(filePath, 'utf-8');
        const fileDependencies = this.extractDependencies(sourceCode);

        for (const dep of fileDependencies) {
          const existing = dependencies.find(d => d.moduleId === dep);
          if (existing) {
            existing.strength += 0.1; // Increase strength for multiple references
          } else {
            dependencies.push({
              moduleId: dep,
              type: 'import',
              strength: 0.5,
              testCoupling: 0, // Would be calculated
              riskFactor: 0.3 // Would be calculated
            });
          }
        }
      } catch (error) {
        // File not accessible or readable
      }
    }

    return dependencies;
  }

  private async generateModuleMetadata(
    moduleConfig: ModuleCoverageConfig,
    files: Map<string, FileCoverage>
  ): Promise<ModuleMetadata> {
    return {
      owner: 'unknown',
      maintainers: [],
      lastModified: new Date(),
      createdDate: new Date(),
      version: '1.0.0',
      tags: moduleConfig.tags,
      criticality: moduleConfig.critical ? 'critical' : 'medium',
      businessValue: 'medium',
      technicalDebt: 'medium'
    };
  }

  private async loadModuleHistory(moduleId: string): Promise<ModuleHistoryPoint[]> {
    try {
      const historyFile = path.join(process.cwd(), 'coverage-history', `${moduleId}.json`);
      const data = await fs.readFile(historyFile, 'utf-8');
      const parsed = JSON.parse(data);
      return parsed.map((point: any) => ({
        ...point,
        timestamp: new Date(point.timestamp)
      }));
    } catch {
      return [];
    }
  }

  private generateModuleId(moduleConfig: ModuleCoverageConfig): string {
    return moduleConfig.name.toLowerCase().replace(/\s+/g, '-');
  }

  private inferModuleType(moduleConfig: ModuleCoverageConfig): ModuleType {
    const path = moduleConfig.path.toLowerCase();
    const tags = moduleConfig.tags.map(t => t.toLowerCase());

    if (tags.includes('api') || path.includes('controller') || path.includes('router')) {
      return 'api-controller';
    }
    if (tags.includes('data') || path.includes('repository') || path.includes('dao')) {
      return 'data-access';
    }
    if (tags.includes('service') || path.includes('service')) {
      return 'service';
    }
    if (tags.includes('util') || path.includes('util') || path.includes('helper')) {
      return 'utility';
    }
    if (path.includes('middleware')) {
      return 'middleware';
    }
    if (path.includes('config')) {
      return 'configuration';
    }
    if (path.includes('component')) {
      return 'component';
    }

    return 'business-logic';
  }

  async compareModules(moduleIds: string[]): Promise<ModuleComparisonResult> {
    const modules = moduleIds.map(id => this.modules.get(id)).filter(Boolean) as ModuleTracker[];

    const rankings = this.generateModuleRankings(modules);
    const insights = this.generateModuleInsights(modules);
    const recommendations = this.generateModuleRecommendations(modules);

    return {
      modules,
      rankings,
      insights,
      recommendations
    };
  }

  private generateModuleRankings(modules: ModuleTracker[]): ModuleRanking[] {
    const rankings: ModuleRanking[] = [];
    const categories: Array<'coverage' | 'quality' | 'testability' | 'maintainability'> =
      ['coverage', 'quality', 'testability', 'maintainability'];

    categories.forEach(category => {
      const scores = modules.map(module => ({
        moduleId: module.id,
        score: this.calculateModuleScore(module, category)
      }));

      scores.sort((a, b) => b.score - a.score);

      scores.forEach((item, index) => {
        rankings.push({
          moduleId: item.moduleId,
          rank: index + 1,
          score: item.score,
          category,
          percentile: ((modules.length - index) / modules.length) * 100
        });
      });
    });

    return rankings;
  }

  private calculateModuleScore(module: ModuleTracker, category: string): number {
    switch (category) {
      case 'coverage':
        return module.coverage.summary.lines.lines;
      case 'quality':
        return this.calculateQualityScore(module);
      case 'testability':
        return this.calculateModuleTestabilityScore(module);
      case 'maintainability':
        return this.calculateMaintainabilityScore(module);
      default:
        return 0;
    }
  }

  private calculateQualityScore(module: ModuleTracker): number {
    // Combine various quality metrics
    const coverage = module.coverage.summary.lines.lines;
    const complexity = Math.max(0, 100 - module.coverage.summary.averageComplexity * 2);
    const dependencyScore = Math.max(0, 100 - module.dependencies.length * 5);

    return (coverage + complexity + dependencyScore) / 3;
  }

  private calculateModuleTestabilityScore(module: ModuleTracker): number {
    const componentScores = Array.from(module.components.values())
      .map(c => c.testability.overall);

    return componentScores.length > 0
      ? componentScores.reduce((sum, score) => sum + score, 0) / componentScores.length
      : 0;
  }

  private calculateMaintainabilityScore(module: ModuleTracker): number {
    const componentComplexities = Array.from(module.components.values())
      .map(c => c.complexity.maintainability);

    return componentComplexities.length > 0
      ? componentComplexities.reduce((sum, score) => sum + score, 0) / componentComplexities.length
      : 100;
  }

  private generateModuleInsights(modules: ModuleTracker[]): ModuleInsight[] {
    const insights: ModuleInsight[] = [];

    // Identify high-performing modules
    const topPerformers = modules.filter(m =>
      m.coverage.summary.lines.lines > 90 &&
      this.calculateQualityScore(m) > 85
    );

    if (topPerformers.length > 0) {
      insights.push({
        type: 'strength',
        title: 'High-Performing Modules Identified',
        description: `${topPerformers.length} modules demonstrate excellent coverage and quality`,
        impact: 'high',
        actionable: true,
        recommendations: [
          'Use these modules as examples for best practices',
          'Share successful patterns with other teams',
          'Document and standardize approaches used'
        ]
      });
    }

    // Identify problematic modules
    const problematicModules = modules.filter(m =>
      m.coverage.summary.lines.lines < 60 ||
      this.calculateQualityScore(m) < 50
    );

    if (problematicModules.length > 0) {
      insights.push({
        type: 'risk',
        title: 'Modules Requiring Immediate Attention',
        description: `${problematicModules.length} modules have significant quality or coverage issues`,
        impact: 'high',
        actionable: true,
        recommendations: [
          'Prioritize testing efforts on these modules',
          'Consider refactoring high-complexity components',
          'Implement additional quality gates'
        ]
      });
    }

    return insights;
  }

  private generateModuleRecommendations(modules: ModuleTracker[]): ModuleRecommendation[] {
    const recommendations: ModuleRecommendation[] = [];

    modules.forEach(module => {
      const coverage = module.coverage.summary.lines.lines;
      const quality = this.calculateQualityScore(module);

      if (coverage < 70) {
        recommendations.push({
          moduleId: module.id,
          type: 'testing',
          priority: coverage < 50 ? 'high' : 'medium',
          description: `Increase test coverage from ${coverage}% to meet minimum standards`,
          effort: 'medium',
          impact: 'high'
        });
      }

      if (quality < 60) {
        recommendations.push({
          moduleId: module.id,
          type: 'refactoring',
          priority: 'medium',
          description: 'Refactor to improve code quality and maintainability',
          effort: 'high',
          impact: 'medium'
        });
      }

      if (module.dependencies.length > 10) {
        recommendations.push({
          moduleId: module.id,
          type: 'maintenance',
          priority: 'low',
          description: 'Reduce dependencies to improve modularity',
          effort: 'medium',
          impact: 'medium'
        });
      }
    });

    return recommendations;
  }

  getModule(moduleId: string): ModuleTracker | undefined {
    return this.modules.get(moduleId);
  }

  getAllModules(): ModuleTracker[] {
    return Array.from(this.modules.values());
  }

  async exportModuleData(moduleId: string, format: 'json' | 'csv' = 'json'): Promise<string> {
    const module = this.modules.get(moduleId);
    if (!module) {
      throw new Error(`Module ${moduleId} not found`);
    }

    if (format === 'json') {
      return JSON.stringify(module, null, 2);
    } else {
      return this.convertModuleToCSV(module);
    }
  }

  private convertModuleToCSV(module: ModuleTracker): string {
    const headers = ['Component', 'Type', 'Coverage', 'Complexity', 'Testability'];
    const rows = Array.from(module.components.values()).map(component => [
      component.name,
      component.type,
      component.coverage.lines.lines,
      component.complexity.cyclomatic,
      component.testability.overall
    ]);

    return [headers.join(','), ...rows.map(row => row.join(','))].join('\n');
  }
}

// Helper interfaces for parsing
interface ParsedComponent {
  name: string;
  type: ComponentType;
  methods: ParsedMethod[];
  properties: ParsedProperty[];
  dependencies: string[];
}

interface ParsedMethod {
  name: string;
  signature: string;
  complexity: number;
}

interface ParsedProperty {
  name: string;
  type: string;
  isPublic: boolean;
}