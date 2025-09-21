/**
 * AI Trading System Code Analysis Engine
 * Main entry point and public API
 */

export * from './types';
export * from './core/AnalysisEngine';
export * from './parsers/ParserManager';
export * from './parsers/TypeScriptParser';
export * from './parsers/TradingPatternParser';
export * from './generators/DiagramGenerator';
export * from './cache/CacheManager';
export * from './hooks/HooksIntegration';

// Additional parsers
export * from './parsers/JavaScriptParser';
export * from './parsers/DatabaseSchemaParser';
export * from './parsers/APIEndpointParser';

// Core analyzer
export * from './core/AnalyzerManager';

import { AnalysisEngine } from './core/AnalysisEngine';
import { Logger, AnalysisConfig } from './types';

/**
 * Default configuration for the analysis engine
 */
export const defaultConfig: AnalysisConfig = {
  include: [
    'src/**/*.ts',
    'src/**/*.tsx',
    'src/**/*.js',
    'src/**/*.jsx',
    'lib/**/*.ts',
    'lib/**/*.js'
  ],
  exclude: [
    'node_modules/**',
    'dist/**',
    'build/**',
    '**/*.test.ts',
    '**/*.spec.ts',
    '**/*.d.ts'
  ],
  parsers: [
    {
      name: 'typescript',
      enabled: true,
      filePatterns: ['**/*.ts', '**/*.tsx'],
      options: {}
    },
    {
      name: 'javascript',
      enabled: true,
      filePatterns: ['**/*.js', '**/*.jsx'],
      options: {}
    },
    {
      name: 'trading-pattern',
      enabled: true,
      filePatterns: ['**/*.ts', '**/*.js'],
      options: {}
    },
    {
      name: 'database-schema',
      enabled: true,
      filePatterns: ['**/*.sql', '**/*.ts'],
      options: {}
    },
    {
      name: 'api-endpoint',
      enabled: true,
      filePatterns: ['**/*.ts', '**/*.js'],
      options: {}
    }
  ],
  analyzers: [
    {
      name: 'complexity',
      enabled: true,
      priority: 1,
      options: {}
    },
    {
      name: 'dependencies',
      enabled: true,
      priority: 2,
      options: {}
    },
    {
      name: 'trading-patterns',
      enabled: true,
      priority: 3,
      options: {}
    },
    {
      name: 'risk-assessment',
      enabled: true,
      priority: 4,
      options: {}
    }
  ],
  cache: {
    enabled: true,
    ttl: 3600, // 1 hour
    strategy: 'claude-flow',
    namespace: 'aitrading-analysis'
  },
  hooks: {
    enabled: true,
    events: ['analysis-start', 'analysis-complete', 'file-analyzed'],
    incremental: true,
    notificationThreshold: 5
  },
  output: {
    formats: ['json', 'mermaid'],
    directory: './analysis-output',
    includeMetadata: true,
    compress: false
  }
};

/**
 * Default console logger
 */
export const defaultLogger: Logger = {
  debug: (message: string, ...args: any[]) => {
    if (process.env.DEBUG) {
      console.debug(`[DEBUG] ${message}`, ...args);
    }
  },
  info: (message: string, ...args: any[]) => {
    console.info(`[INFO] ${message}`, ...args);
  },
  warn: (message: string, ...args: any[]) => {
    console.warn(`[WARN] ${message}`, ...args);
  },
  error: (message: string, ...args: any[]) => {
    console.error(`[ERROR] ${message}`, ...args);
  }
};

/**
 * Create a new analysis engine with optional configuration
 */
export function createAnalysisEngine(
  config?: Partial<AnalysisConfig>,
  logger?: Logger
): AnalysisEngine {
  const mergedConfig = {
    ...defaultConfig,
    ...config,
    parsers: config?.parsers || defaultConfig.parsers,
    analyzers: config?.analyzers || defaultConfig.analyzers,
    cache: { ...defaultConfig.cache, ...config?.cache },
    hooks: { ...defaultConfig.hooks, ...config?.hooks },
    output: { ...defaultConfig.output, ...config?.output }
  };

  const engineLogger = logger || defaultLogger;

  return new AnalysisEngine(mergedConfig, engineLogger);
}

/**
 * Quick analysis function for simple use cases
 */
export async function analyzeCodebase(
  targetPath?: string,
  config?: Partial<AnalysisConfig>,
  logger?: Logger
) {
  const engine = createAnalysisEngine(config, logger);

  try {
    await engine.initialize();
    const result = await engine.analyze(targetPath);
    await engine.dispose();

    return result;
  } catch (error) {
    await engine.dispose();
    throw error;
  }
}

/**
 * Generate trading system summary
 */
export async function generateTradingSummary(
  targetPath?: string,
  config?: Partial<AnalysisConfig>,
  logger?: Logger
): Promise<string> {
  const engine = createAnalysisEngine(config, logger);

  try {
    await engine.initialize();
    const summary = await engine.generateSummary();
    await engine.dispose();

    return summary;
  } catch (error) {
    await engine.dispose();
    throw error;
  }
}

/**
 * Export for CLI usage
 */
export { AnalysisEngine as default };