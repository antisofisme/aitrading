import { DiagramConfig, ThemeConfig } from '../core/types';

/**
 * Default diagram engine configuration
 */
export const defaultDiagramConfig: DiagramConfig = {
  defaultTheme: 'trading-light',
  outputDirectory: './diagrams/output',
  cacheEnabled: true,
  maxConcurrentGenerations: 5,
  themes: {
    // Trading platform optimized themes
    'trading-pro': {
      primary: '#1a7f64',
      secondary: '#2c3e50',
      accent: '#00c851',
      background: '#f8f9fa',
      text: '#1a7f64',
      border: '#28a745',
      success: '#00c851',
      warning: '#ffbb33',
      error: '#ff4444',
      fontFamily: 'Monaco, "SF Mono", "Segoe UI Mono", "Roboto Mono", monospace',
      fontSize: 12
    },
    'trading-terminal': {
      primary: '#00ff88',
      secondary: '#666666',
      accent: '#00ffff',
      background: '#000000',
      text: '#00ff88',
      border: '#333333',
      success: '#00ff88',
      warning: '#ffaa00',
      error: '#ff4444',
      fontFamily: 'Monaco, "SF Mono", "Segoe UI Mono", "Roboto Mono", monospace',
      fontSize: 11
    },
    'institutional': {
      primary: '#2c3e50',
      secondary: '#34495e',
      accent: '#3498db',
      background: '#ffffff',
      text: '#2c3e50',
      border: '#bdc3c7',
      success: '#27ae60',
      warning: '#f39c12',
      error: '#e74c3c',
      fontFamily: '"Segoe UI", Tahoma, Geneva, Verdana, sans-serif',
      fontSize: 13
    }
  }
};

/**
 * MCP Integration configuration
 */
export const mcpConfig = {
  enableHooks: true,
  enableMemoryCoordination: true,
  enableFileWatching: true,
  hookTimeout: 5000,
  memoryNamespace: 'diagram-engine',
  fileWatchDebounce: 1000
};

/**
 * Batch processing configuration
 */
export const batchConfig = {
  maxConcurrent: 5,
  retryAttempts: 3,
  retryDelay: 1000,
  priorityWeights: {
    critical: 1,
    high: 2,
    normal: 3,
    low: 4
  }
};

/**
 * Output format configuration
 */
export const outputConfig = {
  svg: {
    enableInteractivity: true,
    optimizeSize: true,
    includeMetadata: true
  },
  png: {
    resolution: 300,
    quality: 0.9,
    transparent: true,
    maxWidth: 2048,
    maxHeight: 2048
  },
  pdf: {
    format: 'A4',
    margin: 50,
    includeMetadata: true,
    embedFonts: true
  },
  html: {
    includeInteractivity: true,
    includeControls: true,
    responsive: true,
    darkModeToggle: true
  }
};

/**
 * Template-specific configurations
 */
export const templateConfigs = {
  'system-architecture': {
    defaultDirection: 'TB',
    enableGrouping: true,
    showLabels: true,
    includeMetadata: false,
    maxNodesPerGroup: 8
  },
  'trading-workflow': {
    includeTimestamps: true,
    showActivation: true,
    includeNotes: true,
    autonumber: true,
    maxStepsPerSection: 10
  },
  'er-diagram': {
    showAttributes: true,
    showDataTypes: true,
    showKeys: true,
    includeIndexes: false,
    groupBySchema: true
  },
  'component-graph': {
    clusterByModule: true,
    showVersions: true,
    includeDependencies: true,
    dependencyStyle: 'arrows',
    maxDepth: 3
  },
  'user-journey': {
    showEmotions: true,
    includeTouchpoints: true,
    groupByPhase: true,
    showSatisfactionScore: true,
    maxStepsPerPhase: 6
  }
};

/**
 * Trading-specific diagram patterns
 */
export const tradingPatterns = {
  // Common trading system components
  components: {
    'order-engine': {
      type: 'service',
      color: '#e3f2fd',
      shape: 'rect',
      icon: '📋'
    },
    'market-data': {
      type: 'external',
      color: '#f3e5f5',
      shape: 'circle',
      icon: '📊'
    },
    'trading-engine': {
      type: 'service',
      color: '#e8f5e8',
      shape: 'rect',
      icon: '⚡'
    },
    'portfolio-manager': {
      type: 'service',
      color: '#fff3e0',
      shape: 'rect',
      icon: '💼'
    },
    'risk-manager': {
      type: 'service',
      color: '#ffebee',
      shape: 'rect',
      icon: '🛡️'
    },
    'settlement': {
      type: 'service',
      color: '#f1f8e9',
      shape: 'rect',
      icon: '💳'
    }
  },

  // Common trading workflows
  workflows: {
    'order-lifecycle': [
      'Order Creation',
      'Risk Check',
      'Market Submission',
      'Execution',
      'Settlement',
      'Confirmation'
    ],
    'market-data-flow': [
      'Data Provider',
      'Market Gateway',
      'Normalization',
      'Distribution',
      'Consumer'
    ],
    'portfolio-update': [
      'Trade Execution',
      'Position Update',
      'P&L Calculation',
      'Risk Assessment',
      'Reporting'
    ]
  },

  // Database patterns for trading systems
  entities: {
    'order': {
      attributes: [
        'id', 'symbol', 'side', 'quantity', 'price', 'order_type',
        'status', 'created_at', 'updated_at', 'user_id'
      ]
    },
    'trade': {
      attributes: [
        'id', 'order_id', 'symbol', 'quantity', 'price', 'fee',
        'trade_time', 'trade_id'
      ]
    },
    'position': {
      attributes: [
        'id', 'user_id', 'symbol', 'quantity', 'average_price',
        'unrealized_pnl', 'realized_pnl', 'updated_at'
      ]
    },
    'market_data': {
      attributes: [
        'id', 'symbol', 'last_price', 'volume', 'timestamp',
        'bid_price', 'ask_price', 'high', 'low'
      ]
    }
  }
};

/**
 * Performance optimization settings
 */
export const performanceConfig = {
  enableCaching: true,
  cacheTimeout: 300000, // 5 minutes
  maxCacheSize: 100,
  enableCompression: true,
  lazyLoading: true,
  preloadTemplates: true,
  optimizeLayouts: true,
  enableWorkerThreads: false // Disabled by default for compatibility
};

/**
 * Validation rules
 */
export const validationRules = {
  maxNodes: 50,
  maxRelationships: 100,
  maxLabelLength: 100,
  maxNestingDepth: 5,
  allowedFileTypes: ['.js', '.ts', '.jsx', '.tsx', '.sql', '.md', '.json', '.yml', '.yaml'],
  allowedDiagramTypes: [
    'system-architecture',
    'sequence-diagram',
    'er-diagram',
    'component-graph',
    'user-journey',
    'trading-workflow',
    'data-flow'
  ]
};

/**
 * Export combined configuration
 */
export const diagramEngineConfig = {
  default: defaultDiagramConfig,
  mcp: mcpConfig,
  batch: batchConfig,
  output: outputConfig,
  templates: templateConfigs,
  trading: tradingPatterns,
  performance: performanceConfig,
  validation: validationRules
};