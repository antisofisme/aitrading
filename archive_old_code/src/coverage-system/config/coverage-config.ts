/**
 * Coverage Configuration System
 * Manages thresholds, quality gates, and coverage requirements
 */

export interface CoverageThreshold {
  lines: number;
  functions: number;
  branches: number;
  statements: number;
}

export interface ModuleCoverageConfig {
  path: string;
  name: string;
  thresholds: CoverageThreshold;
  critical: boolean;
  priority: 'high' | 'medium' | 'low';
  tags: string[];
}

export interface QualityGate {
  id: string;
  name: string;
  description: string;
  conditions: QualityGateCondition[];
  enforced: boolean;
  blocking: boolean;
}

export interface QualityGateCondition {
  metric: 'coverage' | 'trend' | 'complexity' | 'debt';
  operator: 'gt' | 'gte' | 'lt' | 'lte' | 'eq';
  value: number;
  threshold: number;
  severity: 'blocker' | 'critical' | 'major' | 'minor' | 'info';
}

export interface CoverageConfig {
  global: CoverageThreshold;
  modules: ModuleCoverageConfig[];
  qualityGates: QualityGate[];
  reporting: ReportingConfig;
  cicd: CICDConfig;
  alerts: AlertConfig;
}

export interface ReportingConfig {
  formats: Array<'html' | 'json' | 'lcov' | 'xml' | 'markdown' | 'pdf'>;
  outputDir: string;
  includeSourceMaps: boolean;
  historicalTrends: boolean;
  detailedMetrics: boolean;
  visualCharts: boolean;
  generateSummary: boolean;
}

export interface CICDConfig {
  enabled: boolean;
  failOnThreshold: boolean;
  generateArtifacts: boolean;
  publishMetrics: boolean;
  slackNotifications: boolean;
  githubComments: boolean;
  autoRemediation: boolean;
}

export interface AlertConfig {
  enabled: boolean;
  thresholdDecreasePercent: number;
  consecutiveFailures: number;
  channels: Array<'slack' | 'email' | 'github' | 'webhook'>;
  webhookUrl?: string;
  emailRecipients?: string[];
  slackChannel?: string;
}

export class CoverageConfigManager {
  private static instance: CoverageConfigManager;
  private config: CoverageConfig;

  private constructor() {
    this.config = this.loadDefaultConfig();
  }

  public static getInstance(): CoverageConfigManager {
    if (!CoverageConfigManager.instance) {
      CoverageConfigManager.instance = new CoverageConfigManager();
    }
    return CoverageConfigManager.instance;
  }

  private loadDefaultConfig(): CoverageConfig {
    return {
      global: {
        lines: 80,
        functions: 80,
        branches: 75,
        statements: 80
      },
      modules: [
        {
          path: 'src/coverage-system',
          name: 'Coverage System',
          thresholds: { lines: 95, functions: 95, branches: 90, statements: 95 },
          critical: true,
          priority: 'high',
          tags: ['core', 'testing', 'quality']
        },
        {
          path: 'src/trading',
          name: 'Trading Engine',
          thresholds: { lines: 90, functions: 90, branches: 85, statements: 90 },
          critical: true,
          priority: 'high',
          tags: ['trading', 'business-critical']
        },
        {
          path: 'src/ai',
          name: 'AI Services',
          thresholds: { lines: 85, functions: 85, branches: 80, statements: 85 },
          critical: true,
          priority: 'high',
          tags: ['ai', 'ml', 'algorithms']
        },
        {
          path: 'src/data',
          name: 'Data Layer',
          thresholds: { lines: 88, functions: 88, branches: 83, statements: 88 },
          critical: true,
          priority: 'high',
          tags: ['data', 'persistence']
        },
        {
          path: 'src/api',
          name: 'API Layer',
          thresholds: { lines: 85, functions: 85, branches: 80, statements: 85 },
          critical: false,
          priority: 'medium',
          tags: ['api', 'http']
        },
        {
          path: 'src/utils',
          name: 'Utilities',
          thresholds: { lines: 75, functions: 75, branches: 70, statements: 75 },
          critical: false,
          priority: 'low',
          tags: ['utils', 'helpers']
        }
      ],
      qualityGates: [
        {
          id: 'gate-1',
          name: 'Minimum Coverage Gate',
          description: 'Ensures minimum coverage thresholds are met',
          enforced: true,
          blocking: true,
          conditions: [
            {
              metric: 'coverage',
              operator: 'gte',
              value: 80,
              threshold: 80,
              severity: 'blocker'
            }
          ]
        },
        {
          id: 'gate-2',
          name: 'Critical Module Gate',
          description: 'Higher standards for critical business modules',
          enforced: true,
          blocking: true,
          conditions: [
            {
              metric: 'coverage',
              operator: 'gte',
              value: 90,
              threshold: 90,
              severity: 'blocker'
            }
          ]
        },
        {
          id: 'gate-3',
          name: 'Trend Analysis Gate',
          description: 'Prevents significant coverage degradation',
          enforced: true,
          blocking: false,
          conditions: [
            {
              metric: 'trend',
              operator: 'gt',
              value: -5,
              threshold: -5,
              severity: 'critical'
            }
          ]
        }
      ],
      reporting: {
        formats: ['html', 'json', 'lcov', 'markdown'],
        outputDir: 'coverage',
        includeSourceMaps: true,
        historicalTrends: true,
        detailedMetrics: true,
        visualCharts: true,
        generateSummary: true
      },
      cicd: {
        enabled: true,
        failOnThreshold: true,
        generateArtifacts: true,
        publishMetrics: true,
        slackNotifications: true,
        githubComments: true,
        autoRemediation: false
      },
      alerts: {
        enabled: true,
        thresholdDecreasePercent: 5,
        consecutiveFailures: 2,
        channels: ['slack', 'github'],
        slackChannel: '#quality-alerts'
      }
    };
  }

  public getConfig(): CoverageConfig {
    return { ...this.config };
  }

  public updateConfig(updates: Partial<CoverageConfig>): void {
    this.config = { ...this.config, ...updates };
  }

  public getModuleConfig(modulePath: string): ModuleCoverageConfig | undefined {
    return this.config.modules.find(module =>
      modulePath.startsWith(module.path)
    );
  }

  public getActiveQualityGates(): QualityGate[] {
    return this.config.qualityGates.filter(gate => gate.enforced);
  }

  public validateThresholds(coverage: CoverageThreshold): boolean {
    const { global } = this.config;
    return (
      coverage.lines >= global.lines &&
      coverage.functions >= global.functions &&
      coverage.branches >= global.branches &&
      coverage.statements >= global.statements
    );
  }

  public generateModuleThresholds(filePath: string): CoverageThreshold {
    const moduleConfig = this.getModuleConfig(filePath);
    return moduleConfig ? moduleConfig.thresholds : this.config.global;
  }

  public exportConfig(): string {
    return JSON.stringify(this.config, null, 2);
  }

  public importConfig(configJson: string): void {
    try {
      const parsed = JSON.parse(configJson);
      this.validateConfigStructure(parsed);
      this.config = parsed;
    } catch (error) {
      throw new Error(`Invalid configuration: ${error.message}`);
    }
  }

  private validateConfigStructure(config: any): void {
    const required = ['global', 'modules', 'qualityGates', 'reporting', 'cicd', 'alerts'];
    for (const field of required) {
      if (!config[field]) {
        throw new Error(`Missing required field: ${field}`);
      }
    }
  }

  public getCriticalModules(): ModuleCoverageConfig[] {
    return this.config.modules.filter(module => module.critical);
  }

  public getModulesByPriority(priority: 'high' | 'medium' | 'low'): ModuleCoverageConfig[] {
    return this.config.modules.filter(module => module.priority === priority);
  }

  public getModulesByTag(tag: string): ModuleCoverageConfig[] {
    return this.config.modules.filter(module => module.tags.includes(tag));
  }
}

export const coverageConfig = CoverageConfigManager.getInstance();