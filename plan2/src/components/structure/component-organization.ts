// Component Organization Patterns and Guidelines

/**
 * COMPONENT HIERARCHY LEVELS
 *
 * 1. UI Components (src/components/ui/) - Atomic design system components
 * 2. Bridge Components (src/components/bridge/) - Integration layer
 * 3. Domain Components (src/components/[domain]/) - Business logic components
 * 4. Feature Modules (src/features/[feature]/) - Complete feature implementations
 * 5. Page Components (src/pages/) - Route-level components
 */

// ============================================================================
// 1. UI COMPONENT PATTERNS
// ============================================================================

/**
 * ShadCN UI Component Structure
 * Location: src/components/ui/
 *
 * These are low-level, highly reusable components that form the design system.
 */

// Example: Button component structure
export interface UIComponentStructure {
  // Core component file
  component: 'button.tsx';

  // Variant definitions
  variants: {
    default: 'primary styling';
    destructive: 'error/danger styling';
    outline: 'border-only styling';
    secondary: 'muted styling';
    ghost: 'transparent styling';
    link: 'text-only styling';
  };

  // Size variants
  sizes: {
    default: 'standard size';
    sm: 'small size';
    lg: 'large size';
    icon: 'icon-only size';
  };

  // Props interface
  props: 'React.ButtonHTMLAttributes & VariantProps';
}

// ============================================================================
// 2. BRIDGE COMPONENT PATTERNS
// ============================================================================

/**
 * Material UI + ShadCN Integration Components
 * Location: src/components/bridge/
 *
 * These components provide seamless integration between UI libraries.
 */

export interface BridgeComponentStructure {
  // Core bridge component
  component: 'mui-shadcn-bridge.tsx';

  // Integration patterns
  patterns: {
    conditional: 'Switch between libraries based on context';
    wrapper: 'Wrap one library with another for styling';
    hybrid: 'Combine features from both libraries';
    proxy: 'Forward props to appropriate library component';
  };

  // Context-aware selection
  contexts: {
    trading: 'Use Material UI for data-heavy components';
    forms: 'Use ShadCN for modern form controls';
    navigation: 'Use Material UI for complex navigation';
    content: 'Use ShadCN for content presentation';
  };
}

// ============================================================================
// 3. DOMAIN COMPONENT PATTERNS
// ============================================================================

/**
 * Trading Domain Components
 * Location: src/components/trading/
 *
 * Business logic components specific to trading functionality.
 */

export interface TradingComponentStructure {
  // Order management
  orderComponents: {
    'order-form.tsx': 'Order creation and modification';
    'order-book.tsx': 'Real-time order book display';
    'order-history.tsx': 'Historical order tracking';
    'order-status.tsx': 'Live order status updates';
  };

  // Position management
  positionComponents: {
    'position-manager.tsx': 'Active position management';
    'position-summary.tsx': 'Position overview and metrics';
    'position-details.tsx': 'Detailed position information';
  };

  // Risk management
  riskComponents: {
    'risk-calculator.tsx': 'Position risk calculations';
    'risk-limits.tsx': 'Risk limit configuration';
    'risk-alerts.tsx': 'Risk threshold notifications';
  };

  // Market data
  marketComponents: {
    'ticker-display.tsx': 'Real-time price display';
    'market-depth.tsx': 'Market depth visualization';
    'trade-feed.tsx': 'Live trade feed';
  };
}

/**
 * Portfolio Domain Components
 * Location: src/components/portfolio/
 */

export interface PortfolioComponentStructure {
  overviewComponents: {
    'portfolio-overview.tsx': 'High-level portfolio metrics';
    'asset-allocation.tsx': 'Asset distribution visualization';
    'performance-summary.tsx': 'Performance metrics and charts';
  };

  managementComponents: {
    'portfolio-manager.tsx': 'Portfolio editing and rebalancing';
    'asset-selector.tsx': 'Asset search and selection';
    'allocation-editor.tsx': 'Target allocation modification';
  };

  analyticsComponents: {
    'performance-chart.tsx': 'Historical performance visualization';
    'risk-metrics.tsx': 'Portfolio risk analysis';
    'correlation-matrix.tsx': 'Asset correlation display';
  };
}

// ============================================================================
// 4. FEATURE MODULE PATTERNS
// ============================================================================

/**
 * Feature-Based Organization
 * Location: src/features/[feature]/
 *
 * Complete feature implementations with co-located concerns.
 */

export interface FeatureModuleStructure {
  structure: {
    'components/': 'Feature-specific components';
    'hooks/': 'Feature-specific custom hooks';
    'store/': 'Feature state management';
    'types/': 'Feature type definitions';
    'utils/': 'Feature utility functions';
    'api/': 'Feature API layer';
    'constants/': 'Feature constants';
    'tests/': 'Feature test files';
  };

  // Example: Trading feature module
  tradingFeature: {
    'components/': {
      'TradingDashboard.tsx': 'Main trading interface';
      'OrderPanel.tsx': 'Order creation panel';
      'PositionsTable.tsx': 'Positions data table';
      'TradingChart.tsx': 'Chart component';
    };

    'hooks/': {
      'useTradingData.ts': 'Trading data fetching';
      'useOrderManagement.ts': 'Order operations';
      'usePositionTracking.ts': 'Position monitoring';
    };

    'store/': {
      'tradingStore.ts': 'Trading state management';
      'orderStore.ts': 'Order state management';
      'positionStore.ts': 'Position state management';
    };

    'types/': {
      'trading.ts': 'Trading type definitions';
      'orders.ts': 'Order type definitions';
      'positions.ts': 'Position type definitions';
    };
  };
}

// ============================================================================
// 5. COMPONENT COMPOSITION PATTERNS
// ============================================================================

/**
 * Composition Patterns for Complex Components
 */

export interface CompositionPatterns {
  // Compound Component Pattern
  compoundPattern: {
    description: 'Components that work together as a cohesive unit';
    example: {
      'TradingPanel': 'Root component';
      'TradingPanel.Header': 'Panel header';
      'TradingPanel.Content': 'Panel content';
      'TradingPanel.Footer': 'Panel footer';
    };
    benefits: [
      'Clear component relationships',
      'Flexible composition',
      'Reduced prop drilling',
      'Better encapsulation'
    ];
  };

  // Render Props Pattern
  renderPropsPattern: {
    description: 'Components that provide data and render logic separation';
    example: {
      'DataProvider': 'Provides data and loading states';
      'render': 'Function that receives data and renders UI';
    };
    useCases: [
      'Data fetching components',
      'State management components',
      'Animation components'
    ];
  };

  // Higher-Order Component Pattern
  hocPattern: {
    description: 'Components that enhance other components with additional functionality';
    example: {
      'withErrorBoundary': 'Adds error handling';
      'withLoading': 'Adds loading states';
      'withAuth': 'Adds authentication checks';
    };
    useCases: [
      'Cross-cutting concerns',
      'Component enhancement',
      'Code reuse'
    ];
  };

  // Custom Hook Pattern
  customHookPattern: {
    description: 'Reusable stateful logic extracted into hooks';
    example: {
      'useTradingData': 'Trading data management';
      'useWebSocket': 'WebSocket connection management';
      'useErrorRecovery': 'Error handling and recovery';
    };
    benefits: [
      'Logic reuse',
      'Separation of concerns',
      'Easier testing',
      'Better composition'
    ];
  };
}

// ============================================================================
// 6. IMPORT/EXPORT PATTERNS
// ============================================================================

/**
 * Standardized Import/Export Patterns
 */

export interface ImportExportPatterns {
  // Barrel Exports (index.ts files)
  barrelExports: {
    'src/components/ui/index.ts': 'Export all UI components';
    'src/components/trading/index.ts': 'Export all trading components';
    'src/hooks/index.ts': 'Export all custom hooks';
    'src/store/index.ts': 'Export all stores';
    'src/types/index.ts': 'Export all types';
  };

  // Named Exports (preferred)
  namedExports: {
    pattern: 'export const ComponentName = () => {}';
    benefits: [
      'Better tree shaking',
      'Explicit dependencies',
      'IDE support',
      'Refactoring safety'
    ];
  };

  // Type-only Imports
  typeOnlyImports: {
    pattern: 'import type { TypeName } from "./types"';
    benefits: [
      'Clear intent',
      'Better compilation',
      'Reduced bundle size'
    ];
  };

  // Absolute Imports
  absoluteImports: {
    pattern: 'import { Component } from "@/components/Component"';
    configuration: 'TypeScript path mapping in tsconfig.json';
    benefits: [
      'Consistent import paths',
      'Better refactoring',
      'Clearer dependencies'
    ];
  };
}

// ============================================================================
// 7. PERFORMANCE OPTIMIZATION PATTERNS
// ============================================================================

/**
 * Component Performance Optimization
 */

export interface PerformancePatterns {
  // React.memo for Pure Components
  memoization: {
    pattern: 'React.memo(Component, propsAreEqual?)';
    useCases: [
      'Components with expensive renders',
      'Components that re-render frequently',
      'Components with stable props'
    ];
  };

  // useMemo for Expensive Calculations
  useMemoPattern: {
    pattern: 'useMemo(() => expensiveCalculation(data), [data])';
    useCases: [
      'Complex data transformations',
      'Chart data processing',
      'Filter/sort operations'
    ];
  };

  // useCallback for Stable Functions
  useCallbackPattern: {
    pattern: 'useCallback((param) => action(param), [dependency])';
    useCases: [
      'Event handlers passed to children',
      'Functions in dependency arrays',
      'API call functions'
    ];
  };

  // Lazy Loading
  lazyLoading: {
    pattern: 'const Component = lazy(() => import("./Component"))';
    useCases: [
      'Route-level components',
      'Large feature modules',
      'Conditional components'
    ];
  };

  // Virtualization
  virtualization: {
    pattern: 'react-window or react-virtualized';
    useCases: [
      'Large data tables',
      'Long lists',
      'Trade history',
      'Order book data'
    ];
  };
}

// ============================================================================
// 8. TESTING PATTERNS
// ============================================================================

/**
 * Component Testing Organization
 */

export interface TestingPatterns {
  // Test File Co-location
  coLocation: {
    pattern: 'Component.tsx + Component.test.tsx in same directory';
    benefits: [
      'Easy test discovery',
      'Clear test ownership',
      'Better maintenance'
    ];
  };

  // Test Utilities
  testUtilities: {
    'src/test-utils/': {
      'render-with-providers.tsx': 'Render with store/theme providers';
      'mock-data.ts': 'Mock data generators';
      'test-helpers.ts': 'Common test helper functions';
    };
  };

  // Testing Library Patterns
  testingLibraryPatterns: {
    'user-events': 'userEvent for realistic interactions';
    'queries': 'Accessibility-first element queries';
    'assertions': 'Semantic assertions about component state';
    'mocking': 'MSW for API mocking';
  };
}

// ============================================================================
// IMPLEMENTATION GUIDELINES
// ============================================================================

export const componentGuidelines = {
  naming: {
    components: 'PascalCase (e.g., TradingPanel)',
    files: 'kebab-case (e.g., trading-panel.tsx)',
    directories: 'kebab-case (e.g., market-data)',
    hooks: 'camelCase with "use" prefix (e.g., useTradingData)',
    types: 'PascalCase (e.g., TradingOrder)',
    constants: 'SCREAMING_SNAKE_CASE (e.g., API_ENDPOINTS)',
  },

  fileSize: {
    components: 'Maximum 300 lines per component file',
    hooks: 'Maximum 150 lines per hook file',
    utils: 'Maximum 200 lines per utility file',
    splitting: 'Split larger files into smaller, focused modules',
  },

  dependencies: {
    external: 'Minimize external dependencies',
    internal: 'Use absolute imports with path mapping',
    circular: 'Avoid circular dependencies',
    coupling: 'Minimize coupling between modules',
  },

  documentation: {
    jsdoc: 'Document complex functions and components',
    readme: 'Include README.md in feature modules',
    examples: 'Provide usage examples for reusable components',
    types: 'Use TypeScript for self-documenting interfaces',
  },
};