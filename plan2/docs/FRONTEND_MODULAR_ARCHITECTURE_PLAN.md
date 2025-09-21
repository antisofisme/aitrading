# Frontend Modular Architecture Plan
## Centralized Error Handling & Component Design

### Executive Summary

This document presents a comprehensive modular UI architecture that mirrors the backend's centralized "errordna" system. The architecture emphasizes centralized error handling, modular component design, real-time data flow, and consistent patterns throughout the application. The design ensures scalability, maintainability, and performance optimization for trading applications with sub-10ms update requirements.

---

## 1. CENTRALIZED ERROR HANDLING SYSTEM (Frontend ErrorDNA)

### 1.1 Architecture Overview

The Frontend ErrorDNA system mirrors the backend's centralized error handling approach, providing:
- Component-level error boundaries with intelligent recovery
- Error signature system for unique identification
- Context enrichment for trading sessions
- Recovery patterns and fallback mechanisms
- Seamless integration with backend error system

### 1.2 Error Signature System

```typescript
// Frontend ErrorDNA Core Implementation
interface ErrorSignature {
  id: string                    // Unique error identifier
  type: 'component' | 'network' | 'trading' | 'validation' | 'system'
  severity: 'low' | 'medium' | 'high' | 'critical'
  timestamp: Date
  fingerprint: string          // Generated from error stack + component
  context: ErrorContext
  recoveryStrategy: RecoveryStrategy
}

interface ErrorContext {
  component: string             // Component where error occurred
  route: string                // Current route/page
  userId?: string              // User identifier
  tradingSession?: string      // Active trading session
  marketConditions?: {         // Trading context
    symbol: string
    timeframe: string
    marketHours: boolean
    volatility: number
  }
  userAgent: string
  url: string
  state: Record<string, any>   // Component state at error time
}

interface RecoveryStrategy {
  immediate: 'retry' | 'fallback' | 'redirect' | 'refresh'
  fallback: {
    component?: React.ComponentType
    data?: any
    message?: string
  }
  retry: {
    maxAttempts: number
    backoffMs: number
    condition?: (error: Error) => boolean
  }
}
```

### 1.3 Frontend ErrorDNA Implementation

```typescript
// core/error-handling/frontend-error-dna.ts
class FrontendErrorDNA {
  private static instance: FrontendErrorDNA
  private errorHistory: Map<string, ErrorSignature[]> = new Map()
  private recoveryPatterns: Map<string, RecoveryStrategy> = new Map()
  private subscribers: Set<ErrorSubscriber> = new Set()

  static getInstance(): FrontendErrorDNA {
    if (!this.instance) {
      this.instance = new FrontendErrorDNA()
    }
    return this.instance
  }

  captureError(error: Error, context: Partial<ErrorContext>): ErrorSignature {
    const signature = this.generateErrorSignature(error, context)
    const enrichedContext = this.enrichErrorContext(context)

    // Store error for pattern analysis
    this.storeError(signature)

    // Notify subscribers (monitoring, analytics)
    this.notifySubscribers(signature)

    // Attempt recovery
    this.attemptRecovery(signature)

    // Send to backend ErrorDNA for correlation
    this.sendToBackend(signature)

    return signature
  }

  private generateErrorSignature(error: Error, context: Partial<ErrorContext>): ErrorSignature {
    const fingerprint = this.createFingerprint(error, context.component || 'unknown')

    return {
      id: `fe_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type: this.classifyError(error, context),
      severity: this.calculateSeverity(error, context),
      timestamp: new Date(),
      fingerprint,
      context: this.enrichErrorContext(context),
      recoveryStrategy: this.determineRecoveryStrategy(error, context)
    }
  }

  private createFingerprint(error: Error, component: string): string {
    // Create unique fingerprint similar to backend
    const stack = error.stack?.split('\n').slice(0, 3).join('|') || ''
    const message = error.message.slice(0, 50)
    return btoa(`${error.name}:${message}:${component}:${stack}`)
      .replace(/[^a-zA-Z0-9]/g, '')
      .substr(0, 32)
  }

  private classifyError(error: Error, context: Partial<ErrorContext>): ErrorSignature['type'] {
    if (error.name.includes('Network') || error.message.includes('fetch')) {
      return 'network'
    }
    if (context.component?.includes('Trading')) {
      return 'trading'
    }
    if (error.name.includes('Validation')) {
      return 'validation'
    }
    if (error.name.includes('Chunk') || error.name.includes('Loading')) {
      return 'system'
    }
    return 'component'
  }

  private calculateSeverity(error: Error, context: Partial<ErrorContext>): ErrorSignature['severity'] {
    // Critical: Trading operations, authentication
    if (context.component?.includes('Trading') ||
        context.component?.includes('Auth') ||
        error.message.includes('CRITICAL')) {
      return 'critical'
    }

    // High: Data loading, WebSocket connections
    if (error.name.includes('Network') ||
        context.component?.includes('Chart') ||
        context.component?.includes('Market')) {
      return 'high'
    }

    // Medium: UI components, validation
    if (context.component?.includes('Form') ||
        error.name.includes('Validation')) {
      return 'medium'
    }

    return 'low'
  }

  private enrichErrorContext(context: Partial<ErrorContext>): ErrorContext {
    return {
      component: context.component || 'Unknown',
      route: window.location.pathname,
      userId: getCurrentUser()?.id,
      tradingSession: getTradingSession()?.id,
      marketConditions: getMarketConditions(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      state: context.state || {},
      ...context
    }
  }

  private determineRecoveryStrategy(error: Error, context: Partial<ErrorContext>): RecoveryStrategy {
    // Trading operations: Immediate retry with fallback
    if (context.component?.includes('Trading')) {
      return {
        immediate: 'retry',
        retry: { maxAttempts: 3, backoffMs: 1000 },
        fallback: {
          component: TradingErrorFallback,
          message: 'Trading system temporarily unavailable. Please try again.'
        }
      }
    }

    // Network errors: Retry with exponential backoff
    if (error.name.includes('Network')) {
      return {
        immediate: 'retry',
        retry: { maxAttempts: 5, backoffMs: 2000 },
        fallback: {
          component: NetworkErrorFallback,
          message: 'Connection lost. Retrying...'
        }
      }
    }

    // Component errors: Fallback to error boundary
    return {
      immediate: 'fallback',
      fallback: {
        component: GenericErrorFallback,
        message: 'Something went wrong. Please refresh the page.'
      },
      retry: { maxAttempts: 1, backoffMs: 0 }
    }
  }

  private attemptRecovery(signature: ErrorSignature): void {
    const strategy = signature.recoveryStrategy

    switch (strategy.immediate) {
      case 'retry':
        this.scheduleRetry(signature)
        break
      case 'fallback':
        this.activateFallback(signature)
        break
      case 'redirect':
        this.performRedirect(signature)
        break
      case 'refresh':
        this.scheduleRefresh()
        break
    }
  }

  private sendToBackend(signature: ErrorSignature): void {
    // Send to backend ErrorDNA for correlation and analysis
    fetch('/api/errors/frontend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        errorSignature: signature,
        correlation: {
          sessionId: getSessionId(),
          timestamp: signature.timestamp,
          userJourney: getUserJourney()
        }
      })
    }).catch(err => {
      // Fallback: Store locally if backend is unavailable
      this.storeLocalError(signature)
    })
  }

  // Pattern analysis for proactive error prevention
  analyzeErrorPatterns(): ErrorPattern[] {
    const patterns: ErrorPattern[] = []

    for (const [component, errors] of this.errorHistory.entries()) {
      const recentErrors = errors.filter(e =>
        Date.now() - e.timestamp.getTime() < 3600000 // Last hour
      )

      if (recentErrors.length > 5) {
        patterns.push({
          component,
          frequency: recentErrors.length,
          commonFingerprints: this.getCommonFingerprints(recentErrors),
          suggestedActions: this.generateSuggestions(recentErrors)
        })
      }
    }

    return patterns
  }
}
```

### 1.4 Component-Level Error Boundaries

```typescript
// components/error-boundaries/TradingErrorBoundary.tsx
interface TradingErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ComponentType<ErrorFallbackProps>
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void
  recovery?: RecoveryOptions
}

interface RecoveryOptions {
  autoRetry?: boolean
  retryDelay?: number
  maxRetries?: number
  resetKeys?: string[]
}

export const TradingErrorBoundary: React.FC<TradingErrorBoundaryProps> = ({
  children,
  fallback: Fallback = TradingErrorFallback,
  onError,
  recovery = { autoRetry: true, retryDelay: 2000, maxRetries: 3 }
}) => {
  return (
    <ErrorBoundary
      FallbackComponent={Fallback}
      onError={(error, errorInfo) => {
        // Capture with Frontend ErrorDNA
        const errorDNA = FrontendErrorDNA.getInstance()
        errorDNA.captureError(error, {
          component: 'TradingErrorBoundary',
          state: errorInfo.componentStack
        })

        // Custom error handler
        onError?.(error, errorInfo)

        // Notify trading system
        notifyTradingSystem('error', { error, context: errorInfo })
      }}
      onReset={(details) => {
        // Reset trading state to safe defaults
        resetTradingStore()
        clearTradingCache()

        // Re-establish WebSocket connections
        reconnectTradingWebSocket()
      }}
      resetKeys={recovery.resetKeys}
      resetOnPropsChange={true}
    >
      {children}
    </ErrorBoundary>
  )
}

// Specialized error fallback for trading components
const TradingErrorFallback: React.FC<ErrorFallbackProps> = ({ error, resetErrorBoundary }) => {
  const [retrying, setRetrying] = useState(false)
  const [countdown, setCountdown] = useState(0)

  const handleRetry = async () => {
    setRetrying(true)

    try {
      // Attempt to restore trading state
      await restoreTradingState()
      await validateMarketConnection()

      // Reset error boundary
      resetErrorBoundary()
    } catch (retryError) {
      // If retry fails, escalate
      const errorDNA = FrontendErrorDNA.getInstance()
      errorDNA.captureError(retryError as Error, {
        component: 'TradingErrorFallback',
        context: 'retry_failed'
      })
    } finally {
      setRetrying(false)
    }
  }

  return (
    <Card className="border-red-200 bg-red-50">
      <CardHeader>
        <CardTitle className="text-red-800 flex items-center">
          <AlertTriangle className="mr-2" />
          Trading System Error
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-red-700 mb-4">
          A critical error occurred in the trading system. Your positions are safe.
        </p>
        <div className="space-y-2">
          <p className="text-sm text-red-600">
            Error ID: {error.message.slice(0, 32)}...
          </p>
          <p className="text-sm text-red-600">
            Time: {new Date().toLocaleTimeString()}
          </p>
        </div>
        <div className="mt-4 space-x-2">
          <Button
            onClick={handleRetry}
            disabled={retrying}
            variant="destructive"
          >
            {retrying ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Reconnecting...
              </>
            ) : (
              'Retry Connection'
            )}
          </Button>
          <Button variant="outline" onClick={() => window.location.reload()}>
            Refresh Page
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
```

### 1.5 Context Enrichment for Trading Sessions

```typescript
// hooks/useErrorContext.ts
export const useErrorContext = (componentName: string) => {
  const tradingSession = useTradingSession()
  const marketData = useMarketData()
  const userState = useUserState()

  return useMemo(() => ({
    component: componentName,
    tradingSession: tradingSession?.id,
    marketConditions: {
      symbol: marketData?.currentSymbol,
      timeframe: marketData?.timeframe,
      marketHours: marketData?.isMarketOpen,
      volatility: marketData?.volatility
    },
    userState: {
      authenticated: userState.isAuthenticated,
      permissions: userState.permissions,
      preferences: userState.preferences
    },
    performance: {
      memoryUsage: (performance as any).memory?.usedJSHeapSize,
      timing: performance.timing,
      navigation: performance.navigation
    }
  }), [componentName, tradingSession, marketData, userState])
}

// components/trading/TradingPositionCard.tsx
export const TradingPositionCard: React.FC<PositionCardProps> = ({ position }) => {
  const errorContext = useErrorContext('TradingPositionCard')

  const handleError = useCallback((error: Error) => {
    const errorDNA = FrontendErrorDNA.getInstance()
    errorDNA.captureError(error, {
      ...errorContext,
      state: { position, timestamp: Date.now() }
    })
  }, [errorContext, position])

  return (
    <TradingErrorBoundary onError={handleError}>
      {/* Component implementation */}
    </TradingErrorBoundary>
  )
}
```

---

## 2. MODULAR COMPONENT ARCHITECTURE

### 2.1 Feature-Based Module Organization

The architecture mirrors backend services with clear separation of concerns:

```
src/
├── modules/                          # Feature modules (mirrors backend services)
│   ├── trading-engine/              # Trading operations and components
│   │   ├── components/              # Trading-specific UI components
│   │   │   ├── TradingDashboard.tsx
│   │   │   ├── PositionManager.tsx
│   │   │   ├── OrderEntry.tsx
│   │   │   └── RiskManager.tsx
│   │   ├── hooks/                   # Trading business logic hooks
│   │   │   ├── useTradingEngine.ts
│   │   │   ├── useOrderManagement.ts
│   │   │   └── useRiskAssessment.ts
│   │   ├── services/                # API communication layer
│   │   │   ├── trading.service.ts
│   │   │   └── orders.service.ts
│   │   ├── stores/                  # State management
│   │   │   ├── trading.store.ts
│   │   │   └── positions.store.ts
│   │   ├── types/                   # TypeScript definitions
│   │   │   └── trading.types.ts
│   │   └── index.ts                 # Module exports
│   │
│   ├── market-data/                 # Market data handling
│   │   ├── components/
│   │   │   ├── MarketOverview.tsx
│   │   │   ├── PriceChart.tsx
│   │   │   ├── MarketDepth.tsx
│   │   │   └── TickerList.tsx
│   │   ├── hooks/
│   │   │   ├── useMarketData.ts
│   │   │   ├── useWebSocketData.ts
│   │   │   └── useChartData.ts
│   │   ├── services/
│   │   │   ├── market-data.service.ts
│   │   │   └── websocket.service.ts
│   │   ├── stores/
│   │   │   ├── market.store.ts
│   │   │   └── chart.store.ts
│   │   └── types/
│   │       └── market.types.ts
│   │
│   ├── user-management/             # User features and authentication
│   │   ├── components/
│   │   │   ├── UserProfile.tsx
│   │   │   ├── AuthForms.tsx
│   │   │   ├── AccountSettings.tsx
│   │   │   └── PermissionGuard.tsx
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   ├── useUserProfile.ts
│   │   │   └── usePermissions.ts
│   │   ├── services/
│   │   │   ├── auth.service.ts
│   │   │   └── user.service.ts
│   │   ├── stores/
│   │   │   ├── auth.store.ts
│   │   │   └── user.store.ts
│   │   └── types/
│   │       └── user.types.ts
│   │
│   ├── analytics/                   # Analytics and reporting
│   │   ├── components/
│   │   │   ├── PerformanceCharts.tsx
│   │   │   ├── ReportsGenerator.tsx
│   │   │   ├── MetricsDashboard.tsx
│   │   │   └── DataVisualization.tsx
│   │   ├── hooks/
│   │   │   ├── useAnalytics.ts
│   │   │   ├── useReporting.ts
│   │   │   └── useMetrics.ts
│   │   ├── services/
│   │   │   ├── analytics.service.ts
│   │   │   └── reporting.service.ts
│   │   ├── stores/
│   │   │   ├── analytics.store.ts
│   │   │   └── reports.store.ts
│   │   └── types/
│   │       └── analytics.types.ts
│   │
│   └── ai-orchestration/            # AI features and predictions
│       ├── components/
│       │   ├── AIPredictions.tsx
│       │   ├── ModelStatus.tsx
│       │   ├── ConfidenceMetrics.tsx
│       │   └── AIInsights.tsx
│       ├── hooks/
│       │   ├── useAIPredictions.ts
│       │   ├── useModelStatus.ts
│       │   └── useAIInsights.ts
│       ├── services/
│       │   ├── ai.service.ts
│       │   └── predictions.service.ts
│       ├── stores/
│       │   ├── ai.store.ts
│       │   └── predictions.store.ts
│       └── types/
│           └── ai.types.ts
│
├── components/                      # Shared component library
│   ├── ui/                         # Base UI primitives (ShadCN)
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   ├── input.tsx
│   │   ├── table.tsx
│   │   └── index.ts
│   │
│   ├── trading/                    # Trading-specific shared components
│   │   ├── CurrencyPair.tsx
│   │   ├── PriceDisplay.tsx
│   │   ├── TradingButton.tsx
│   │   ├── PositionBadge.tsx
│   │   └── index.ts
│   │
│   ├── charts/                     # Chart components
│   │   ├── TradingViewChart.tsx
│   │   ├── PerformanceChart.tsx
│   │   ├── VolumeChart.tsx
│   │   └── index.ts
│   │
│   ├── forms/                      # Form components
│   │   ├── FormField.tsx
│   │   ├── FormValidation.tsx
│   │   ├── TradingForm.tsx
│   │   └── index.ts
│   │
│   └── layout/                     # Layout components
│       ├── AppLayout.tsx
│       ├── Sidebar.tsx
│       ├── Header.tsx
│       ├── Footer.tsx
│       └── index.ts
│
├── core/                           # Core system functionality
│   ├── error-handling/             # Frontend ErrorDNA implementation
│   │   ├── frontend-error-dna.ts
│   │   ├── error-boundaries.tsx
│   │   ├── error-recovery.ts
│   │   └── index.ts
│   │
│   ├── api/                        # API communication layer
│   │   ├── api-client.ts
│   │   ├── endpoints.ts
│   │   ├── middleware.ts
│   │   └── index.ts
│   │
│   ├── websocket/                  # Real-time communication
│   │   ├── websocket-manager.ts
│   │   ├── message-handlers.ts
│   │   ├── connection-recovery.ts
│   │   └── index.ts
│   │
│   ├── performance/                # Performance monitoring
│   │   ├── metrics-collector.ts
│   │   ├── performance-monitor.ts
│   │   ├── bundle-analyzer.ts
│   │   └── index.ts
│   │
│   └── security/                   # Security utilities
│       ├── auth-guard.ts
│       ├── xss-protection.ts
│       ├── csrf-protection.ts
│       └── index.ts
│
├── stores/                         # Global state management
│   ├── root.store.ts              # Root store configuration
│   ├── app.store.ts               # Application state
│   ├── theme.store.ts             # Theme and UI preferences
│   └── index.ts
│
├── hooks/                          # Global custom hooks
│   ├── useWebSocket.ts            # WebSocket management
│   ├── usePerformance.ts          # Performance monitoring
│   ├── useErrorBoundary.ts        # Error boundary utilities
│   ├── useLocalStorage.ts         # Local storage management
│   └── index.ts
│
├── services/                       # Cross-module services
│   ├── notification.service.ts    # Notification system
│   ├── cache.service.ts           # Caching layer
│   ├── logger.service.ts          # Logging service
│   └── index.ts
│
├── utils/                          # Shared utilities
│   ├── formatters/                # Data formatting utilities
│   │   ├── currency.ts
│   │   ├── date.ts
│   │   ├── percentage.ts
│   │   └── index.ts
│   │
│   ├── validators/                # Validation utilities
│   │   ├── trading.validators.ts
│   │   ├── form.validators.ts
│   │   ├── number.validators.ts
│   │   └── index.ts
│   │
│   ├── constants/                 # Application constants
│   │   ├── trading.constants.ts
│   │   ├── api.constants.ts
│   │   ├── ui.constants.ts
│   │   └── index.ts
│   │
│   └── helpers/                   # Helper functions
│       ├── calculations.ts
│       ├── transformations.ts
│       ├── debounce.ts
│       └── index.ts
│
├── types/                          # Global TypeScript definitions
│   ├── api.types.ts               # API response types
│   ├── trading.types.ts           # Trading domain types
│   ├── user.types.ts              # User domain types
│   ├── common.types.ts            # Common types
│   └── index.ts
│
└── config/                         # Configuration files
    ├── api.config.ts              # API configuration
    ├── websocket.config.ts        # WebSocket configuration
    ├── theme.config.ts            # Theme configuration
    ├── performance.config.ts      # Performance configuration
    └── index.ts
```

### 2.2 Module Pattern Implementation

```typescript
// modules/trading-engine/index.ts - Module exports
export { TradingDashboard, PositionManager, OrderEntry } from './components'
export { useTradingEngine, useOrderManagement } from './hooks'
export { tradingService, ordersService } from './services'
export { tradingStore, positionsStore } from './stores'
export type {
  TradingPosition,
  OrderRequest,
  RiskParameters,
  TradingSession
} from './types'

// Module configuration and initialization
export const TradingEngineModule = {
  name: 'trading-engine',
  version: '1.0.0',
  dependencies: ['market-data', 'user-management'],

  initialize: async () => {
    // Initialize stores
    await tradingStore.initialize()
    await positionsStore.initialize()

    // Setup WebSocket connections
    await tradingService.connect()

    // Register error handlers
    FrontendErrorDNA.getInstance().registerModule('trading-engine', {
      criticalComponents: ['OrderEntry', 'PositionManager'],
      recoveryStrategies: tradingRecoveryStrategies
    })
  },

  cleanup: async () => {
    // Cleanup connections and listeners
    await tradingService.disconnect()
    tradingStore.reset()
    positionsStore.reset()
  }
}
```

### 2.3 Shared Component Library Structure

```typescript
// components/ui/index.ts - ShadCN UI exports
export * from './button'
export * from './card'
export * from './dialog'
export * from './input'
export * from './table'
export * from './form'
export * from './select'
export * from './checkbox'
export * from './radio-group'
export * from './switch'
export * from './textarea'
export * from './label'
export * from './badge'
export * from './alert'
export * from './toast'
export * from './progress'
export * from './skeleton'
export * from './tooltip'
export * from './dropdown-menu'
export * from './navigation-menu'
export * from './tabs'
export * from './accordion'
export * from './separator'
export * from './avatar'
export * from './calendar'
export * from './command'
export * from './context-menu'
export * from './hover-card'
export * from './menubar'
export * from './popover'
export * from './scroll-area'
export * from './sheet'
export * from './slider'
export * from './toggle'

// components/trading/index.ts - Trading-specific components
export { CurrencyPair } from './CurrencyPair'
export { PriceDisplay } from './PriceDisplay'
export { TradingButton } from './TradingButton'
export { PositionBadge } from './PositionBadge'
export { PnLDisplay } from './PnLDisplay'
export { LeverageSelector } from './LeverageSelector'
export { StopLossInput } from './StopLossInput'
export { TakeProfitInput } from './TakeProfitInput'
export { VolumeSelector } from './VolumeSelector'
export { TradingStatus } from './TradingStatus'

// Trading-specific component example
export const PriceDisplay: React.FC<PriceDisplayProps> = ({
  price,
  symbol,
  size = 'md',
  showChange = true,
  precision = 'auto'
}) => {
  const errorContext = useErrorContext('PriceDisplay')

  const formatPrice = useMemo(() => {
    try {
      return formatCurrency(price, symbol, precision)
    } catch (error) {
      FrontendErrorDNA.getInstance().captureError(error as Error, {
        ...errorContext,
        state: { price, symbol, precision }
      })
      return '---'
    }
  }, [price, symbol, precision, errorContext])

  return (
    <TradingErrorBoundary>
      <span className={cn(
        'font-mono',
        size === 'sm' && 'text-sm',
        size === 'md' && 'text-base',
        size === 'lg' && 'text-lg'
      )}>
        {formatPrice}
      </span>
    </TradingErrorBoundary>
  )
}
```

### 2.4 Service Layer Abstraction

```typescript
// services/base.service.ts - Base service class
abstract class BaseService {
  protected apiClient: APIClient
  protected errorDNA: FrontendErrorDNA

  constructor(baseURL: string) {
    this.apiClient = new APIClient({ baseURL })
    this.errorDNA = FrontendErrorDNA.getInstance()
  }

  protected async handleRequest<T>(
    operation: () => Promise<T>,
    context: Partial<ErrorContext>
  ): Promise<T> {
    try {
      return await operation()
    } catch (error) {
      this.errorDNA.captureError(error as Error, context)
      throw error
    }
  }
}

// modules/trading-engine/services/trading.service.ts
class TradingService extends BaseService {
  constructor() {
    super(process.env.REACT_APP_TRADING_API_URL!)
  }

  async getPositions(): Promise<TradingPosition[]> {
    return this.handleRequest(
      () => this.apiClient.get<TradingPosition[]>('/positions'),
      { component: 'TradingService.getPositions' }
    )
  }

  async executeOrder(order: OrderRequest): Promise<OrderResult> {
    return this.handleRequest(
      () => this.apiClient.post<OrderResult>('/orders', order),
      {
        component: 'TradingService.executeOrder',
        state: { order },
        severity: 'critical'
      }
    )
  }

  async closePosition(positionId: string): Promise<ClosePositionResult> {
    return this.handleRequest(
      () => this.apiClient.delete<ClosePositionResult>(`/positions/${positionId}`),
      {
        component: 'TradingService.closePosition',
        state: { positionId },
        severity: 'high'
      }
    )
  }
}

export const tradingService = new TradingService()
```

### 2.5 State Management Per Module

```typescript
// modules/trading-engine/stores/trading.store.ts
interface TradingState {
  positions: TradingPosition[]
  activeOrders: Order[]
  tradingSession: TradingSession | null
  isConnected: boolean
  lastUpdate: Date | null
  errors: ErrorSignature[]
}

export const useTradingStore = create<TradingState & TradingActions>((set, get) => ({
  // State
  positions: [],
  activeOrders: [],
  tradingSession: null,
  isConnected: false,
  lastUpdate: null,
  errors: [],

  // Actions
  updatePosition: (position: TradingPosition) => {
    set((state) => ({
      positions: updatePositionInArray(state.positions, position),
      lastUpdate: new Date()
    }))
  },

  addOrder: (order: Order) => {
    set((state) => ({
      activeOrders: [...state.activeOrders, order],
      lastUpdate: new Date()
    }))
  },

  removeOrder: (orderId: string) => {
    set((state) => ({
      activeOrders: state.activeOrders.filter(o => o.id !== orderId),
      lastUpdate: new Date()
    }))
  },

  setConnectionStatus: (connected: boolean) => {
    set({ isConnected: connected })

    if (!connected) {
      // Capture connection error
      FrontendErrorDNA.getInstance().captureError(
        new Error('Trading connection lost'),
        { component: 'TradingStore.setConnectionStatus' }
      )
    }
  },

  addError: (error: ErrorSignature) => {
    set((state) => ({
      errors: [...state.errors.slice(-9), error] // Keep last 10 errors
    }))
  },

  clearErrors: () => {
    set({ errors: [] })
  },

  reset: () => {
    set({
      positions: [],
      activeOrders: [],
      tradingSession: null,
      isConnected: false,
      lastUpdate: null,
      errors: []
    })
  }
}))

// Store persistence and sync
useTradingStore.subscribe(
  (state) => state.positions,
  (positions) => {
    // Persist critical trading data
    localStorage.setItem('trading:positions', JSON.stringify(positions))
  }
)

// Error monitoring
useTradingStore.subscribe(
  (state) => state.errors,
  (errors) => {
    const criticalErrors = errors.filter(e => e.severity === 'critical')
    if (criticalErrors.length > 0) {
      // Escalate critical errors
      notifyTradingSystem('critical_errors', { errors: criticalErrors })
    }
  }
)
```

---

## 3. REAL-TIME DATA FLOW ARCHITECTURE

### 3.1 WebSocket Integration Patterns

```typescript
// core/websocket/websocket-manager.ts
interface WebSocketConfig {
  url: string
  protocols?: string[]
  maxReconnectAttempts: number
  reconnectInterval: number
  heartbeatInterval: number
  messageQueueSize: number
}

interface MessageHandler<T = any> {
  type: string
  handler: (data: T) => void
  errorHandler?: (error: Error) => void
}

class WebSocketManager {
  private ws: WebSocket | null = null
  private config: WebSocketConfig
  private messageHandlers = new Map<string, MessageHandler[]>()
  private messageQueue: any[] = []
  private reconnectAttempts = 0
  private heartbeatTimer: NodeJS.Timeout | null = null
  private errorDNA: FrontendErrorDNA

  constructor(config: WebSocketConfig) {
    this.config = config
    this.errorDNA = FrontendErrorDNA.getInstance()
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.config.url, this.config.protocols)

        this.ws.onopen = () => {
          console.log('WebSocket connected')
          this.reconnectAttempts = 0
          this.startHeartbeat()
          this.processMessageQueue()
          resolve()
        }

        this.ws.onmessage = (event) => {
          this.handleMessage(event)
        }

        this.ws.onclose = (event) => {
          this.handleDisconnection(event)
        }

        this.ws.onerror = (error) => {
          this.handleError(error)
          reject(error)
        }

      } catch (error) {
        this.errorDNA.captureError(error as Error, {
          component: 'WebSocketManager.connect',
          state: { url: this.config.url }
        })
        reject(error)
      }
    })
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const message = JSON.parse(event.data)
      const handlers = this.messageHandlers.get(message.type) || []

      // Process with <10ms target
      const startTime = performance.now()

      for (const { handler, errorHandler } of handlers) {
        try {
          handler(message.data)
        } catch (error) {
          errorHandler?.(error as Error)
          this.errorDNA.captureError(error as Error, {
            component: 'WebSocketManager.handleMessage',
            state: { messageType: message.type, message }
          })
        }
      }

      const processingTime = performance.now() - startTime
      if (processingTime > 10) {
        console.warn(`WebSocket message processing took ${processingTime}ms (target: <10ms)`)
      }

    } catch (error) {
      this.errorDNA.captureError(error as Error, {
        component: 'WebSocketManager.handleMessage',
        state: { rawMessage: event.data }
      })
    }
  }

  private handleDisconnection(event: CloseEvent): void {
    console.log('WebSocket disconnected:', event.code, event.reason)
    this.stopHeartbeat()

    if (this.reconnectAttempts < this.config.maxReconnectAttempts) {
      setTimeout(() => {
        this.reconnectAttempts++
        this.connect().catch(() => {
          // Reconnection failed, will try again
        })
      }, this.config.reconnectInterval * Math.pow(2, this.reconnectAttempts))
    } else {
      this.errorDNA.captureError(new Error('WebSocket max reconnect attempts exceeded'), {
        component: 'WebSocketManager.handleDisconnection',
        state: { attempts: this.reconnectAttempts }
      })
    }
  }

  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping', timestamp: Date.now() })
      }
    }, this.config.heartbeatInterval)
  }

  subscribe<T>(type: string, handler: (data: T) => void, errorHandler?: (error: Error) => void): () => void {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, [])
    }

    const messageHandler: MessageHandler<T> = { type, handler, errorHandler }
    this.messageHandlers.get(type)!.push(messageHandler)

    // Return unsubscribe function
    return () => {
      const handlers = this.messageHandlers.get(type) || []
      const index = handlers.indexOf(messageHandler)
      if (index > -1) {
        handlers.splice(index, 1)
      }
    }
  }

  send(data: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      // Queue message for when connection is restored
      if (this.messageQueue.length < this.config.messageQueueSize) {
        this.messageQueue.push(data)
      }
    }
  }

  private processMessageQueue(): void {
    while (this.messageQueue.length > 0 && this.ws?.readyState === WebSocket.OPEN) {
      const message = this.messageQueue.shift()
      this.ws.send(JSON.stringify(message))
    }
  }
}
```

### 3.2 State Synchronization Strategies

```typescript
// hooks/useWebSocketData.ts
interface WebSocketDataConfig<T> {
  type: string
  initialData?: T
  transform?: (data: any) => T
  throttleMs?: number
  persistLocal?: boolean
  validateData?: (data: T) => boolean
}

export function useWebSocketData<T>(
  config: WebSocketDataConfig<T>
): {
  data: T | undefined
  isConnected: boolean
  lastUpdate: Date | null
  error: Error | null
} {
  const [data, setData] = useState<T | undefined>(config.initialData)
  const [isConnected, setIsConnected] = useState(false)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [error, setError] = useState<Error | null>(null)

  const wsManager = useWebSocketManager()
  const errorContext = useErrorContext('useWebSocketData')

  // Throttled update handler
  const updateData = useMemo(
    () => throttle((newData: any) => {
      try {
        const transformedData = config.transform ? config.transform(newData) : newData

        if (config.validateData && !config.validateData(transformedData)) {
          throw new Error('Data validation failed')
        }

        setData(transformedData)
        setLastUpdate(new Date())
        setError(null)

        // Persist to local storage if configured
        if (config.persistLocal) {
          localStorage.setItem(`ws:${config.type}`, JSON.stringify(transformedData))
        }

      } catch (err) {
        const error = err as Error
        setError(error)
        FrontendErrorDNA.getInstance().captureError(error, {
          ...errorContext,
          state: { type: config.type, data: newData }
        })
      }
    }, config.throttleMs || 50),
    [config, errorContext]
  )

  useEffect(() => {
    // Load persisted data
    if (config.persistLocal) {
      try {
        const stored = localStorage.getItem(`ws:${config.type}`)
        if (stored) {
          const parsedData = JSON.parse(stored)
          if (!config.validateData || config.validateData(parsedData)) {
            setData(parsedData)
          }
        }
      } catch (err) {
        // Ignore localStorage errors
      }
    }

    // Subscribe to WebSocket messages
    const unsubscribe = wsManager.subscribe(
      config.type,
      updateData,
      (error) => {
        setError(error)
        FrontendErrorDNA.getInstance().captureError(error, {
          ...errorContext,
          state: { type: config.type }
        })
      }
    )

    // Monitor connection status
    const connectionUnsubscribe = wsManager.subscribe(
      'connection_status',
      (status: { connected: boolean }) => {
        setIsConnected(status.connected)
      }
    )

    return () => {
      unsubscribe()
      connectionUnsubscribe()
    }
  }, [config.type, updateData, wsManager, errorContext])

  return { data, isConnected, lastUpdate, error }
}

// Usage in trading components
export const useMarketData = (symbol: string) => {
  return useWebSocketData<MarketData>({
    type: `market_data_${symbol}`,
    transform: (data) => ({
      ...data,
      timestamp: new Date(data.timestamp),
      spread: data.ask - data.bid
    }),
    throttleMs: 50, // 20 updates per second max
    persistLocal: true,
    validateData: (data) =>
      data.bid > 0 &&
      data.ask > 0 &&
      data.ask >= data.bid &&
      data.volume >= 0
  })
}
```

### 3.3 Performance Optimization for <10ms Updates

```typescript
// core/performance/update-optimizer.ts
class UpdateOptimizer {
  private updateQueue = new Map<string, any>()
  private rafId: number | null = null
  private lastFrame = 0
  private targetFPS = 60
  private frameTime = 1000 / this.targetFPS

  scheduleUpdate<T>(key: string, data: T, updateFn: (data: T) => void): void {
    // Batch updates for single frame
    this.updateQueue.set(key, { data, updateFn })

    if (!this.rafId) {
      this.rafId = requestAnimationFrame(this.processUpdates.bind(this))
    }
  }

  private processUpdates(timestamp: number): void {
    const elapsed = timestamp - this.lastFrame

    if (elapsed >= this.frameTime) {
      // Process all batched updates
      for (const [key, { data, updateFn }] of this.updateQueue) {
        try {
          updateFn(data)
        } catch (error) {
          console.error(`Update error for ${key}:`, error)
        }
      }

      this.updateQueue.clear()
      this.lastFrame = timestamp
    }

    if (this.updateQueue.size > 0) {
      this.rafId = requestAnimationFrame(this.processUpdates.bind(this))
    } else {
      this.rafId = null
    }
  }
}

const updateOptimizer = new UpdateOptimizer()

// Optimized market data hook
export const useOptimizedMarketData = (symbol: string) => {
  const [marketData, setMarketData] = useState<MarketData>()
  const wsManager = useWebSocketManager()

  useEffect(() => {
    const unsubscribe = wsManager.subscribe(
      `market_data_${symbol}`,
      (data: MarketData) => {
        // Use update optimizer for high-frequency data
        updateOptimizer.scheduleUpdate(
          `market_${symbol}`,
          data,
          setMarketData
        )
      }
    )

    return unsubscribe
  }, [symbol, wsManager])

  return marketData
}

// Performance monitoring hook
export const usePerformanceMonitor = (componentName: string) => {
  const renderCount = useRef(0)
  const lastRender = useRef(Date.now())

  useEffect(() => {
    renderCount.current++
    const now = Date.now()
    const timeSinceLastRender = now - lastRender.current

    if (timeSinceLastRender < 16) { // Less than ~60fps
      console.warn(`${componentName} rendering too frequently: ${timeSinceLastRender}ms`)
    }

    lastRender.current = now
  })

  return {
    renderCount: renderCount.current,
    avgRenderTime: lastRender.current
  }
}
```

### 3.4 Trading Data Pipeline Design

```typescript
// modules/market-data/hooks/useTradingDataPipeline.ts
interface TradingDataPipeline {
  subscribe: (symbol: string, timeframe: string) => void
  unsubscribe: (symbol: string, timeframe: string) => void
  getLatestPrice: (symbol: string) => number | null
  getHistoricalData: (symbol: string, timeframe: string, count: number) => OHLC[]
  isConnected: boolean
  latency: number
}

export const useTradingDataPipeline = (): TradingDataPipeline => {
  const [subscriptions, setSubscriptions] = useState<Set<string>>(new Set())
  const [latestPrices, setLatestPrices] = useState<Map<string, number>>(new Map())
  const [historicalData, setHistoricalData] = useState<Map<string, OHLC[]>>(new Map())
  const [isConnected, setIsConnected] = useState(false)
  const [latency, setLatency] = useState(0)

  const wsManager = useWebSocketManager()
  const errorContext = useErrorContext('TradingDataPipeline')

  const subscribe = useCallback((symbol: string, timeframe: string) => {
    const subscriptionKey = `${symbol}_${timeframe}`

    if (!subscriptions.has(subscriptionKey)) {
      // Send subscription message
      wsManager.send({
        type: 'subscribe',
        symbol,
        timeframe,
        timestamp: Date.now()
      })

      setSubscriptions(prev => new Set([...prev, subscriptionKey]))
    }
  }, [subscriptions, wsManager])

  const unsubscribe = useCallback((symbol: string, timeframe: string) => {
    const subscriptionKey = `${symbol}_${timeframe}`

    if (subscriptions.has(subscriptionKey)) {
      wsManager.send({
        type: 'unsubscribe',
        symbol,
        timeframe,
        timestamp: Date.now()
      })

      setSubscriptions(prev => {
        const newSet = new Set(prev)
        newSet.delete(subscriptionKey)
        return newSet
      })
    }
  }, [subscriptions, wsManager])

  const getLatestPrice = useCallback((symbol: string): number | null => {
    return latestPrices.get(symbol) || null
  }, [latestPrices])

  const getHistoricalData = useCallback((symbol: string, timeframe: string, count: number): OHLC[] => {
    const key = `${symbol}_${timeframe}`
    const data = historicalData.get(key) || []
    return data.slice(-count)
  }, [historicalData])

  useEffect(() => {
    // Subscribe to price updates
    const unsubscribePrice = wsManager.subscribe(
      'price_update',
      (data: { symbol: string; price: number; timestamp: number }) => {
        const receiveTime = Date.now()
        const latencyMs = receiveTime - data.timestamp

        setLatency(latencyMs)
        setLatestPrices(prev => new Map(prev.set(data.symbol, data.price)))

        if (latencyMs > 10) {
          console.warn(`High latency detected: ${latencyMs}ms for ${data.symbol}`)
        }
      }
    )

    // Subscribe to historical data updates
    const unsubscribeHistorical = wsManager.subscribe(
      'historical_update',
      (data: { symbol: string; timeframe: string; ohlc: OHLC[] }) => {
        const key = `${data.symbol}_${data.timeframe}`
        setHistoricalData(prev => new Map(prev.set(key, data.ohlc)))
      }
    )

    // Subscribe to connection status
    const unsubscribeConnection = wsManager.subscribe(
      'connection_status',
      (data: { connected: boolean }) => {
        setIsConnected(data.connected)
      }
    )

    return () => {
      unsubscribePrice()
      unsubscribeHistorical()
      unsubscribeConnection()
    }
  }, [wsManager])

  return {
    subscribe,
    unsubscribe,
    getLatestPrice,
    getHistoricalData,
    isConnected,
    latency
  }
}
```

---

## 4. TECHNOLOGY INTEGRATION PLAN

### 4.1 ShadCN UI + Material UI Integration Strategy

```typescript
// config/ui-integration.config.ts
export const UIIntegrationConfig = {
  // Primary: ShadCN UI for custom trading components
  shadcn: {
    components: [
      'button', 'card', 'dialog', 'input', 'table', 'form',
      'select', 'checkbox', 'radio-group', 'switch', 'badge',
      'alert', 'toast', 'progress', 'skeleton', 'tooltip'
    ],
    customization: {
      tradingTheme: true,
      darkMode: true,
      animations: 'reduced', // For trading performance
      borderRadius: 'sm',
      colorPalette: 'trading' // Custom trading colors
    }
  },

  // Secondary: Material UI for complex data components
  materialUI: {
    components: [
      'DataGrid', 'DatePicker', 'TimePicker', 'Autocomplete',
      'TreeView', 'DataGridPro', 'Charts'
    ],
    theme: {
      integration: 'shadcn-compatible',
      performance: 'optimized',
      bundleSize: 'minimal'
    }
  },

  integration: {
    strategy: 'hybrid',
    priority: 'shadcn-first',
    fallback: 'material-ui',
    performance: {
      lazyLoading: true,
      codesplitting: true,
      treeshaking: true
    }
  }
}

// components/ui/integrated-theme.tsx
import { createTheme, ThemeProvider as MUIThemeProvider } from '@mui/material/styles'
import { ThemeProvider as ShadcnThemeProvider } from 'next-themes'

// Material UI theme that matches ShadCN design tokens
const muiTheme = createTheme({
  palette: {
    mode: 'dark', // Match trading theme
    primary: {
      main: 'hsl(210, 40%, 98%)', // ShadCN primary
    },
    secondary: {
      main: 'hsl(210, 40%, 96%)', // ShadCN secondary
    },
    background: {
      default: 'hsl(224, 71%, 4%)', // ShadCN background
      paper: 'hsl(213, 31%, 91%)', // ShadCN card
    },
    success: {
      main: 'hsl(142, 76%, 36%)', // Trading green
    },
    error: {
      main: 'hsl(0, 84%, 60%)', // Trading red
    }
  },
  typography: {
    fontFamily: 'var(--font-sans)', // ShadCN font
  },
  components: {
    MuiDataGrid: {
      styleOverrides: {
        root: {
          backgroundColor: 'hsl(213, 31%, 91%)',
          border: '1px solid hsl(214, 32%, 91%)',
          '& .MuiDataGrid-cell': {
            borderColor: 'hsl(214, 32%, 91%)',
          }
        }
      }
    }
  }
})

export const IntegratedThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <ShadcnThemeProvider attribute="class" defaultTheme="dark">
      <MUIThemeProvider theme={muiTheme}>
        {children}
      </MUIThemeProvider>
    </ShadcnThemeProvider>
  )
}

// Usage examples
// components/trading/TradingPositionsTable.tsx
import { DataGrid, GridColDef } from '@mui/x-data-grid'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

export const TradingPositionsTable: React.FC<PositionsTableProps> = ({ positions }) => {
  const columns: GridColDef[] = [
    {
      field: 'symbol',
      headerName: 'Symbol',
      width: 120,
      renderCell: (params) => (
        <Badge variant="outline">{params.value}</Badge>
      )
    },
    {
      field: 'pnl',
      headerName: 'P&L',
      width: 120,
      renderCell: (params) => (
        <Badge variant={params.value >= 0 ? 'success' : 'destructive'}>
          {formatCurrency(params.value)}
        </Badge>
      )
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 200,
      renderCell: (params) => (
        <div className="space-x-2">
          <Button size="sm" variant="outline">
            Modify
          </Button>
          <Button size="sm" variant="destructive">
            Close
          </Button>
        </div>
      )
    }
  ]

  return (
    <TradingErrorBoundary>
      <DataGrid
        rows={positions}
        columns={columns}
        pageSize={10}
        checkboxSelection={false}
        disableSelectionOnClick
        autoHeight
      />
    </TradingErrorBoundary>
  )
}
```

### 4.2 Zustand + TanStack Query Implementation

```typescript
// stores/store-integration.config.ts
export const StoreIntegrationConfig = {
  zustand: {
    // Client state (UI, forms, temporary data)
    stores: [
      'trading', 'market', 'user', 'ui', 'theme', 'notifications'
    ],
    persistence: {
      storage: 'localStorage',
      partialize: ['user', 'theme'], // Only persist specific stores
      migrate: true // Handle version migrations
    }
  },

  tanstackQuery: {
    // Server state (API data, caching)
    queryClient: {
      defaultOptions: {
        queries: {
          staleTime: 5 * 60 * 1000, // 5 minutes
          cacheTime: 10 * 60 * 1000, // 10 minutes
          retry: 3,
          retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000)
        },
        mutations: {
          retry: 1,
          retryDelay: 1000
        }
      }
    },

    integration: {
      errorHandling: 'frontend-error-dna',
      optimisticUpdates: true,
      backgroundRefetch: true
    }
  }
}

// stores/root.store.ts
import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'

// Root store combining all module stores
interface RootStore {
  trading: TradingState
  market: MarketState
  user: UserState
  ui: UIState
  theme: ThemeState
  notifications: NotificationState
}

export const useRootStore = create<RootStore>()(
  persist(
    immer((set, get) => ({
      // Trading store slice
      trading: createTradingSlice(set, get),

      // Market data store slice
      market: createMarketSlice(set, get),

      // User store slice
      user: createUserSlice(set, get),

      // UI state store slice
      ui: createUISlice(set, get),

      // Theme store slice
      theme: createThemeSlice(set, get),

      // Notifications store slice
      notifications: createNotificationSlice(set, get)
    })),
    {
      name: 'ai-trading-store',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        theme: state.theme,
        ui: {
          sidebarCollapsed: state.ui.sidebarCollapsed,
          preferredLayout: state.ui.preferredLayout
        }
      })
    }
  )
)

// TanStack Query setup with error handling
// config/query-client.config.ts
import { QueryClient } from '@tanstack/react-query'
import { FrontendErrorDNA } from '@/core/error-handling'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      cacheTime: 10 * 60 * 1000,
      retry: (failureCount, error) => {
        // Don't retry on 4xx errors
        if (error instanceof Error && error.message.includes('4')) {
          return false
        }
        return failureCount < 3
      },
      onError: (error) => {
        FrontendErrorDNA.getInstance().captureError(error as Error, {
          component: 'TanStackQuery',
          type: 'network'
        })
      }
    },
    mutations: {
      retry: 1,
      onError: (error, variables, context) => {
        FrontendErrorDNA.getInstance().captureError(error as Error, {
          component: 'TanStackQuery.mutation',
          type: 'network',
          state: { variables, context }
        })
      }
    }
  }
})

// Integrated hook example
// modules/trading-engine/hooks/useTradingEngine.ts
export const useTradingEngine = () => {
  // Zustand for client state
  const {
    positions,
    updatePosition,
    addOrder,
    removeOrder
  } = useRootStore(state => state.trading)

  // TanStack Query for server state
  const {
    data: serverPositions,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['trading', 'positions'],
    queryFn: () => tradingService.getPositions(),
    refetchInterval: 5000, // Refresh every 5 seconds
    onSuccess: (data) => {
      // Sync server data with client store
      data.forEach(updatePosition)
    }
  })

  const executeOrderMutation = useMutation({
    mutationFn: tradingService.executeOrder,
    onMutate: async (orderRequest) => {
      // Optimistic update
      const tempOrder = {
        ...orderRequest,
        id: `temp_${Date.now()}`,
        status: 'pending'
      }
      addOrder(tempOrder)

      return { tempOrder }
    },
    onSuccess: (result, variables, context) => {
      // Replace temp order with real order
      removeOrder(context!.tempOrder.id)
      addOrder(result)
    },
    onError: (error, variables, context) => {
      // Rollback optimistic update
      if (context?.tempOrder) {
        removeOrder(context.tempOrder.id)
      }
    }
  })

  return {
    positions,
    isLoading,
    error,
    executeOrder: executeOrderMutation.mutate,
    isExecuting: executeOrderMutation.isLoading,
    refetch
  }
}
```

### 4.3 TradingView Charts Integration

```typescript
// components/charts/TradingViewChart.tsx
import { useEffect, useRef, useCallback } from 'react'
import { createChart, IChartApi, ISeriesApi, LineData, UTCTimestamp } from 'lightweight-charts'

interface TradingViewChartProps {
  symbol: string
  timeframe: string
  height?: number
  width?: number
  theme?: 'light' | 'dark'
  onCrosshairMove?: (data: any) => void
  onVisibleRangeChange?: (range: any) => void
}

export const TradingViewChart: React.FC<TradingViewChartProps> = ({
  symbol,
  timeframe,
  height = 400,
  width,
  theme = 'dark',
  onCrosshairMove,
  onVisibleRangeChange
}) => {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const seriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null)

  const errorContext = useErrorContext('TradingViewChart')

  // Chart initialization
  const initChart = useCallback(() => {
    if (!chartContainerRef.current) return

    try {
      const chart = createChart(chartContainerRef.current, {
        width: width || chartContainerRef.current.clientWidth,
        height,
        layout: {
          backgroundColor: theme === 'dark' ? '#1a1a1a' : '#ffffff',
          textColor: theme === 'dark' ? '#d1d1d1' : '#333333',
        },
        grid: {
          vertLines: {
            color: theme === 'dark' ? '#2B2B43' : '#e1e1e1',
          },
          horzLines: {
            color: theme === 'dark' ? '#2B2B43' : '#e1e1e1',
          },
        },
        rightPriceScale: {
          borderColor: theme === 'dark' ? '#2B2B43' : '#cccccc',
        },
        timeScale: {
          borderColor: theme === 'dark' ? '#2B2B43' : '#cccccc',
          timeVisible: true,
          secondsVisible: false,
        },
        handleScroll: {
          mouseWheel: true,
          pressedMouseMove: true,
        },
        handleScale: {
          axisPressedMouseMove: true,
          mouseWheel: true,
          pinch: true,
        },
      })

      const candlestickSeries = chart.addCandlestickSeries({
        upColor: '#4bdc90',
        downColor: '#ff4747',
        borderDownColor: '#ff4747',
        borderUpColor: '#4bdc90',
        wickDownColor: '#ff4747',
        wickUpColor: '#4bdc90',
      })

      // Event handlers
      chart.subscribeCrosshairMove((param) => {
        onCrosshairMove?.(param)
      })

      chart.timeScale().subscribeVisibleTimeRangeChange((range) => {
        onVisibleRangeChange?.(range)
      })

      chartRef.current = chart
      seriesRef.current = candlestickSeries

    } catch (error) {
      FrontendErrorDNA.getInstance().captureError(error as Error, {
        ...errorContext,
        state: { symbol, timeframe, theme }
      })
    }
  }, [symbol, timeframe, height, width, theme, onCrosshairMove, onVisibleRangeChange, errorContext])

  // Chart data management
  const { data: chartData, isLoading } = useQuery({
    queryKey: ['chart', symbol, timeframe],
    queryFn: () => marketDataService.getChartData(symbol, timeframe),
    refetchInterval: 5000,
    onSuccess: (data) => {
      if (seriesRef.current && data) {
        seriesRef.current.setData(data)
      }
    }
  })

  // Real-time updates
  const { data: realtimeData } = useWebSocketData<OHLC>({
    type: `chart_${symbol}_${timeframe}`,
    throttleMs: 100, // Limit to 10fps for chart updates
    transform: (data) => ({
      time: data.timestamp as UTCTimestamp,
      open: data.open,
      high: data.high,
      low: data.low,
      close: data.close
    })
  })

  useEffect(() => {
    if (realtimeData && seriesRef.current) {
      seriesRef.current.update(realtimeData)
    }
  }, [realtimeData])

  // Initialize chart
  useEffect(() => {
    initChart()

    return () => {
      if (chartRef.current) {
        chartRef.current.remove()
        chartRef.current = null
        seriesRef.current = null
      }
    }
  }, [initChart])

  // Handle resize
  useEffect(() => {
    const handleResize = () => {
      if (chartRef.current && chartContainerRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height
        })
      }
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [height])

  return (
    <TradingErrorBoundary>
      <div className="relative">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/80 z-10">
            <div className="flex items-center space-x-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Loading chart data...</span>
            </div>
          </div>
        )}
        <div
          ref={chartContainerRef}
          className="w-full border border-border rounded-lg"
          style={{ height }}
        />
      </div>
    </TradingErrorBoundary>
  )
}

// Chart integration with trading signals
export const EnhancedTradingChart: React.FC<EnhancedTradingChartProps> = ({
  symbol,
  timeframe,
  showSignals = true,
  showIndicators = true,
  ...props
}) => {
  const { data: aiSignals } = useQuery({
    queryKey: ['ai-signals', symbol, timeframe],
    queryFn: () => aiService.getSignals(symbol, timeframe),
    enabled: showSignals
  })

  const handleCrosshairMove = useCallback((param: any) => {
    // Show AI prediction data on crosshair move
    if (param.time && aiSignals) {
      const signal = aiSignals.find(s => s.timestamp === param.time)
      if (signal) {
        // Update tooltip with AI insights
        updateAITooltip(signal)
      }
    }
  }, [aiSignals])

  return (
    <div className="space-y-4">
      <TradingViewChart
        symbol={symbol}
        timeframe={timeframe}
        onCrosshairMove={handleCrosshairMove}
        {...props}
      />

      {showSignals && aiSignals && (
        <AISignalsOverlay signals={aiSignals} />
      )}

      {showIndicators && (
        <TechnicalIndicators symbol={symbol} timeframe={timeframe} />
      )}
    </div>
  )
}
```

### 4.4 TypeScript Configuration and Patterns

```typescript
// tsconfig.json - Optimized for trading application
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "es6", "ES2022"],
    "allowJs": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noFallthroughCasesInSwitch": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@/components/*": ["./src/components/*"],
      "@/modules/*": ["./src/modules/*"],
      "@/stores/*": ["./src/stores/*"],
      "@/services/*": ["./src/services/*"],
      "@/hooks/*": ["./src/hooks/*"],
      "@/utils/*": ["./src/utils/*"],
      "@/types/*": ["./src/types/*"],
      "@/core/*": ["./src/core/*"]
    },
    "strictNullChecks": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true
  },
  "include": [
    "next-env.d.ts",
    "**/*.ts",
    "**/*.tsx",
    ".next/types/**/*.ts"
  ],
  "exclude": [
    "node_modules"
  ]
}

// types/trading.types.ts - Comprehensive trading type definitions
export interface TradingPosition {
  readonly id: string
  readonly symbol: string
  readonly side: 'long' | 'short'
  readonly size: number
  readonly entryPrice: number
  readonly currentPrice: number
  readonly pnl: number
  readonly pnlPercent: number
  readonly margin: number
  readonly leverage: number
  readonly stopLoss?: number
  readonly takeProfit?: number
  readonly timestamp: Date
  readonly lastUpdate: Date
}

export interface OrderRequest {
  readonly symbol: string
  readonly side: 'buy' | 'sell'
  readonly type: 'market' | 'limit' | 'stop' | 'stop-limit'
  readonly size: number
  readonly price?: number
  readonly stopPrice?: number
  readonly timeInForce: 'GTC' | 'IOC' | 'FOK'
  readonly reduceOnly?: boolean
  readonly postOnly?: boolean
  readonly clientOrderId?: string
}

export interface MarketData {
  readonly symbol: string
  readonly bid: number
  readonly ask: number
  readonly last: number
  readonly volume: number
  readonly change: number
  readonly changePercent: number
  readonly high24h: number
  readonly low24h: number
  readonly timestamp: Date
}

export interface OHLC {
  readonly timestamp: UTCTimestamp
  readonly open: number
  readonly high: number
  readonly low: number
  readonly close: number
  readonly volume: number
}

// Branded types for enhanced type safety
export type UserId = string & { readonly __brand: 'UserId' }
export type SymbolCode = string & { readonly __brand: 'SymbolCode' }
export type Price = number & { readonly __brand: 'Price' }
export type Volume = number & { readonly __brand: 'Volume' }

// Utility types for trading operations
export type PositionSide = TradingPosition['side']
export type OrderSide = OrderRequest['side']
export type OrderType = OrderRequest['type']

// Error handling types
export interface TradingError extends Error {
  readonly code: string
  readonly details?: Record<string, unknown>
  readonly recoverable: boolean
}

// API response types
export interface APIResponse<T> {
  readonly success: boolean
  readonly data?: T
  readonly error?: {
    readonly code: string
    readonly message: string
    readonly details?: Record<string, unknown>
  }
  readonly timestamp: Date
}

// WebSocket message types
export interface WebSocketMessage<T = unknown> {
  readonly type: string
  readonly data: T
  readonly timestamp: number
  readonly id?: string
}

// State management types
export interface StoreSlice<T> {
  readonly state: T
  readonly actions: Record<string, (...args: any[]) => void>
  readonly selectors: Record<string, (state: T) => any>
}

// Performance monitoring types
export interface PerformanceMetrics {
  readonly componentName: string
  readonly renderTime: number
  readonly memoryUsage: number
  readonly updateFrequency: number
  readonly errorCount: number
}

// Type guards for runtime type checking
export const isTradingPosition = (obj: unknown): obj is TradingPosition => {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'id' in obj &&
    'symbol' in obj &&
    'side' in obj &&
    'size' in obj &&
    'entryPrice' in obj
  )
}

export const isMarketData = (obj: unknown): obj is MarketData => {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'symbol' in obj &&
    'bid' in obj &&
    'ask' in obj &&
    'last' in obj
  )
}

// Utility type for making properties optional
export type PartialBy<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>

// Utility type for making properties required
export type RequiredBy<T, K extends keyof T> = T & Required<Pick<T, K>>

// Deep readonly utility type
export type DeepReadonly<T> = {
  readonly [P in keyof T]: T[P] extends object ? DeepReadonly<T[P]> : T[P]
}
```

---

## 5. DEVELOPMENT GUIDELINES

### 5.1 Component Naming Conventions

```typescript
// Component naming standards
export const ComponentNamingConventions = {
  // 1. Component files: PascalCase with descriptive names
  files: {
    components: 'TradingPositionCard.tsx',
    hooks: 'useTradingEngine.ts',
    services: 'trading.service.ts',
    stores: 'trading.store.ts',
    types: 'trading.types.ts',
    utils: 'trading.utils.ts'
  },

  // 2. Component names: Domain + Purpose + Type
  patterns: {
    trading: 'Trading + [Feature] + [Component]',
    market: 'Market + [Feature] + [Component]',
    user: 'User + [Feature] + [Component]',
    ai: 'AI + [Feature] + [Component]'
  },

  // 3. Examples of good naming
  examples: {
    components: [
      'TradingPositionCard',      // Domain: Trading, Purpose: Position, Type: Card
      'MarketDataTable',          // Domain: Market, Purpose: Data, Type: Table
      'UserProfileForm',          // Domain: User, Purpose: Profile, Type: Form
      'AISignalIndicator',        // Domain: AI, Purpose: Signal, Type: Indicator
      'TradingOrderEntry',        // Domain: Trading, Purpose: Order, Type: Entry
      'MarketChartDisplay',       // Domain: Market, Purpose: Chart, Type: Display
      'UserPermissionGuard',      // Domain: User, Purpose: Permission, Type: Guard
      'AIPredictionChart'         // Domain: AI, Purpose: Prediction, Type: Chart
    ],
    hooks: [
      'useTradingEngine',         // Domain: Trading, Purpose: Engine management
      'useMarketData',           // Domain: Market, Purpose: Data fetching
      'useUserAuth',             // Domain: User, Purpose: Authentication
      'useAIPredictions',        // Domain: AI, Purpose: Predictions
      'useTradingWebSocket',     // Domain: Trading, Purpose: WebSocket
      'useMarketSubscription',   // Domain: Market, Purpose: Subscription
      'useUserPermissions',      // Domain: User, Purpose: Permissions
      'useAIModelStatus'         // Domain: AI, Purpose: Model status
    ],
    services: [
      'trading.service.ts',      // Domain service
      'market-data.service.ts',  // Domain service with hyphen
      'user-auth.service.ts',    // Domain service with hyphen
      'ai-orchestration.service.ts' // Domain service with hyphen
    ]
  },

  // 4. Folder structure naming
  folders: {
    modules: 'kebab-case',       // trading-engine, market-data
    components: 'kebab-case',    // trading-position, market-chart
    hooks: 'camelCase',          // useTradingEngine
    utils: 'kebab-case'          // format-currency
  },

  // 5. Variable and function naming
  variables: {
    constants: 'SCREAMING_SNAKE_CASE',    // TRADING_SYMBOLS, API_ENDPOINTS
    variables: 'camelCase',                // tradingPosition, marketData
    functions: 'camelCase',                // calculatePnL, formatPrice
    types: 'PascalCase',                   // TradingPosition, MarketData
    interfaces: 'PascalCase + I prefix',   // ITradingEngine, IMarketDataService
    enums: 'PascalCase'                    // OrderType, PositionSide
  }
}

// Implementation examples
// components/trading/TradingPositionCard.tsx
export const TradingPositionCard: React.FC<TradingPositionCardProps> = ({ position }) => {
  // Internal state and handlers use camelCase
  const [isExpanded, setIsExpanded] = useState(false)
  const [showDetails, setShowDetails] = useState(false)

  // Handlers are verb + noun format
  const handleExpandToggle = useCallback(() => {
    setIsExpanded(prev => !prev)
  }, [])

  const handleClosePosition = useCallback(async () => {
    await tradingService.closePosition(position.id)
  }, [position.id])

  return (
    <Card className="trading-position-card">
      {/* Component implementation */}
    </Card>
  )
}

// hooks/useTradingEngine.ts
export const useTradingEngine = (config?: TradingEngineConfig) => {
  // Return object uses descriptive names
  return {
    positions,              // Noun for data
    isLoading,             // Boolean with 'is' prefix
    hasError,              // Boolean with 'has' prefix
    canTrade,              // Boolean with 'can' prefix
    executeOrder,          // Verb for action
    closePosition,         // Verb for action
    updateStopLoss,        // Verb for action
    refreshPositions       // Verb for action
  }
}

// Constants naming
export const TRADING_CONSTANTS = {
  MAX_LEVERAGE: 100,
  MIN_ORDER_SIZE: 0.01,
  DEFAULT_TIMEFRAME: '1h',
  SUPPORTED_SYMBOLS: ['EURUSD', 'GBPUSD', 'USDJPY'],
  ORDER_TYPES: {
    MARKET: 'market',
    LIMIT: 'limit',
    STOP: 'stop',
    STOP_LIMIT: 'stop-limit'
  } as const,
  POSITION_SIDES: {
    LONG: 'long',
    SHORT: 'short'
  } as const
} as const
```

### 5.2 File Organization Standards

```typescript
// File organization structure with detailed guidelines
export const FileOrganizationStandards = {
  // 1. Module-based organization (mirrors backend services)
  moduleStructure: {
    path: 'src/modules/[module-name]/',
    required: ['components/', 'hooks/', 'services/', 'stores/', 'types/', 'index.ts'],
    optional: ['utils/', 'constants/', 'styles/', '__tests__/'],

    // Each module must have clear boundaries
    boundaries: {
      dependencies: 'Modules can depend on shared components, not other modules',
      communication: 'Modules communicate through shared stores or services',
      isolation: 'Module internals are not exposed outside the module'
    }
  },

  // 2. Component organization within modules
  componentStructure: {
    // Feature components (business logic)
    feature: 'modules/[domain]/components/[FeatureName]/',

    // Shared UI components
    ui: 'components/ui/[component-name]/',

    // Domain-specific shared components
    domain: 'components/[domain]/[component-name]/',

    // Layout components
    layout: 'components/layout/[component-name]/'
  },

  // 3. File naming patterns
  fileNaming: {
    components: {
      main: '[ComponentName].tsx',
      styles: '[ComponentName].module.css',
      test: '[ComponentName].test.tsx',
      stories: '[ComponentName].stories.tsx',
      types: '[ComponentName].types.ts'
    },
    hooks: {
      main: 'use[HookName].ts',
      test: 'use[HookName].test.ts',
      types: 'use[HookName].types.ts'
    },
    services: {
      main: '[domain].service.ts',
      test: '[domain].service.test.ts',
      types: '[domain].service.types.ts',
      mock: '[domain].service.mock.ts'
    },
    stores: {
      main: '[domain].store.ts',
      test: '[domain].store.test.ts',
      types: '[domain].store.types.ts'
    },
    utils: {
      main: '[utility-name].ts',
      test: '[utility-name].test.ts',
      types: '[utility-name].types.ts'
    }
  },

  // 4. Import organization
  importOrder: [
    '// 1. React and React-related imports',
    'react',
    'react-dom',
    'react-router-dom',
    '',
    '// 2. Third-party libraries',
    'lodash',
    'zustand',
    '@tanstack/react-query',
    'lightweight-charts',
    '',
    '// 3. Internal imports - UI components',
    '@/components/ui',
    '',
    '// 4. Internal imports - Domain components',
    '@/components/trading',
    '@/components/charts',
    '',
    '// 5. Internal imports - Modules',
    '@/modules/trading-engine',
    '@/modules/market-data',
    '',
    '// 6. Internal imports - Core',
    '@/core/error-handling',
    '@/core/api',
    '',
    '// 7. Internal imports - Utils and types',
    '@/utils',
    '@/types',
    '',
    '// 8. Relative imports',
    './RelativeComponent',
    '../ParentComponent'
  ],

  // 5. Export patterns
  exportPatterns: {
    // Barrel exports for modules
    moduleIndex: `
      // modules/trading-engine/index.ts
      export { TradingDashboard, PositionManager } from './components'
      export { useTradingEngine, useOrderManagement } from './hooks'
      export { tradingService } from './services'
      export { tradingStore } from './stores'
      export type { TradingPosition, OrderRequest } from './types'
    `,

    // Component exports
    componentExport: `
      // Default export for main component
      export default TradingPositionCard

      // Named exports for types and utilities
      export type { TradingPositionCardProps }
      export { formatPositionData, calculatePnL }
    `,

    // Service exports
    serviceExport: `
      // Single service instance export
      export const tradingService = new TradingService()

      // Type exports
      export type { TradingServiceConfig, OrderRequest, OrderResult }
    `
  }
}

// Implementation example: Trading module structure
/*
src/modules/trading-engine/
├── components/
│   ├── TradingDashboard/
│   │   ├── TradingDashboard.tsx
│   │   ├── TradingDashboard.module.css
│   │   ├── TradingDashboard.test.tsx
│   │   └── index.ts
│   ├── PositionManager/
│   │   ├── PositionManager.tsx
│   │   ├── PositionManager.types.ts
│   │   ├── PositionManager.test.tsx
│   │   └── index.ts
│   └── index.ts
├── hooks/
│   ├── useTradingEngine.ts
│   ├── useTradingEngine.test.ts
│   ├── useOrderManagement.ts
│   └── index.ts
├── services/
│   ├── trading.service.ts
│   ├── trading.service.test.ts
│   ├── trading.service.types.ts
│   └── index.ts
├── stores/
│   ├── trading.store.ts
│   ├── trading.store.test.ts
│   └── index.ts
├── types/
│   ├── trading.types.ts
│   ├── orders.types.ts
│   └── index.ts
├── utils/
│   ├── calculations.ts
│   ├── formatters.ts
│   └── index.ts
└── index.ts
*/

// Barrel export example
// modules/trading-engine/index.ts
export {
  TradingDashboard,
  PositionManager,
  OrderEntry,
  RiskManager
} from './components'

export {
  useTradingEngine,
  useOrderManagement,
  useRiskAssessment,
  useTradingWebSocket
} from './hooks'

export {
  tradingService,
  ordersService,
  riskService
} from './services'

export {
  tradingStore,
  positionsStore,
  ordersStore
} from './stores'

export type {
  TradingPosition,
  OrderRequest,
  OrderResult,
  RiskParameters,
  TradingSession,
  TradingEngineConfig
} from './types'

// Re-export commonly used utilities
export {
  calculatePnL,
  formatPrice,
  formatVolume,
  validateOrderRequest
} from './utils'
```

### 5.3 Testing Strategies

```typescript
// Testing strategy implementation
export const TestingStrategies = {
  // 1. Testing pyramid for trading application
  pyramid: {
    unit: '60%',        // Component logic, hooks, utilities
    integration: '30%', // Component integration, API integration
    e2e: '10%'         // Critical trading workflows
  },

  // 2. Testing tools configuration
  tools: {
    unit: 'Vitest + React Testing Library',
    integration: 'Vitest + MSW + React Testing Library',
    e2e: 'Playwright',
    performance: 'Lighthouse CI + Custom metrics'
  },

  // 3. Testing patterns for trading components
  patterns: {
    errorBoundary: 'Test error scenarios and recovery',
    realtime: 'Mock WebSocket connections and data flow',
    state: 'Test state management and persistence',
    performance: 'Test rendering performance and memory usage'
  }
}

// Unit testing example for trading components
// components/trading/TradingPositionCard.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { TradingPositionCard } from './TradingPositionCard'
import { mockTradingPosition } from '@/test/mocks/trading.mocks'
import { FrontendErrorDNA } from '@/core/error-handling'

// Mock error DNA
jest.mock('@/core/error-handling')
const mockErrorDNA = {
  captureError: jest.fn(),
  getInstance: jest.fn(() => mockErrorDNA)
}
;(FrontendErrorDNA.getInstance as jest.Mock).mockReturnValue(mockErrorDNA)

// Test wrapper with providers
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } }
  })

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

describe('TradingPositionCard', () => {
  const defaultPosition = mockTradingPosition({
    symbol: 'EURUSD',
    pnl: 150.50,
    pnlPercent: 2.5,
    side: 'long'
  })

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should display position information correctly', () => {
    render(
      <TestWrapper>
        <TradingPositionCard position={defaultPosition} />
      </TestWrapper>
    )

    expect(screen.getByText('EURUSD')).toBeInTheDocument()
    expect(screen.getByText('$150.50')).toBeInTheDocument()
    expect(screen.getByText('2.5%')).toBeInTheDocument()
    expect(screen.getByText('Long')).toBeInTheDocument()
  })

  it('should handle close position action', async () => {
    const onClosePosition = jest.fn()

    render(
      <TestWrapper>
        <TradingPositionCard
          position={defaultPosition}
          onClosePosition={onClosePosition}
        />
      </TestWrapper>
    )

    const closeButton = screen.getByRole('button', { name: /close/i })
    fireEvent.click(closeButton)

    await waitFor(() => {
      expect(onClosePosition).toHaveBeenCalledWith(defaultPosition.id)
    })
  })

  it('should handle errors gracefully', () => {
    const positionWithError = {
      ...defaultPosition,
      pnl: NaN // Invalid data that should trigger error
    }

    render(
      <TestWrapper>
        <TradingPositionCard position={positionWithError} />
      </TestWrapper>
    )

    expect(mockErrorDNA.captureError).toHaveBeenCalledWith(
      expect.any(Error),
      expect.objectContaining({
        component: 'TradingPositionCard'
      })
    )
  })

  it('should update in real-time', async () => {
    const { rerender } = render(
      <TestWrapper>
        <TradingPositionCard position={defaultPosition} />
      </TestWrapper>
    )

    expect(screen.getByText('$150.50')).toBeInTheDocument()

    const updatedPosition = { ...defaultPosition, pnl: 200.75 }
    rerender(
      <TestWrapper>
        <TradingPositionCard position={updatedPosition} />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('$200.75')).toBeInTheDocument()
    })
  })
})

// Integration testing example
// modules/trading-engine/integration.test.tsx
import { renderHook, act } from '@testing-library/react'
import { rest } from 'msw'
import { setupServer } from 'msw/node'
import { useTradingEngine } from './hooks/useTradingEngine'
import { TestWrapper } from '@/test/utils/TestWrapper'

const server = setupServer(
  rest.get('/api/trading/positions', (req, res, ctx) => {
    return res(ctx.json({
      success: true,
      data: [mockTradingPosition()]
    }))
  }),

  rest.post('/api/trading/orders', (req, res, ctx) => {
    return res(ctx.json({
      success: true,
      data: { id: 'order123', status: 'filled' }
    }))
  })
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

describe('Trading Engine Integration', () => {
  it('should fetch positions and execute orders', async () => {
    const { result, waitForNextUpdate } = renderHook(
      () => useTradingEngine(),
      { wrapper: TestWrapper }
    )

    // Wait for initial data load
    await waitForNextUpdate()

    expect(result.current.positions).toHaveLength(1)
    expect(result.current.isLoading).toBe(false)

    // Test order execution
    await act(async () => {
      await result.current.executeOrder({
        symbol: 'EURUSD',
        side: 'buy',
        type: 'market',
        size: 0.1,
        timeInForce: 'GTC'
      })
    })

    expect(result.current.isExecuting).toBe(false)
  })
})

// E2E testing example
// tests/e2e/trading-workflow.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Trading Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Setup test environment
    await page.goto('/dashboard')
    await page.waitForSelector('[data-testid="market-data-loaded"]')
  })

  test('complete trading workflow', async ({ page }) => {
    // 1. Verify market data is loading
    await expect(page.locator('[data-testid="price-display"]')).toBeVisible()

    // 2. Open order entry form
    await page.click('[data-testid="new-order-button"]')
    await expect(page.locator('[data-testid="order-form"]')).toBeVisible()

    // 3. Fill order details
    await page.selectOption('[data-testid="symbol-select"]', 'EURUSD')
    await page.selectOption('[data-testid="side-select"]', 'buy')
    await page.fill('[data-testid="size-input"]', '0.1')

    // 4. Submit order
    await page.click('[data-testid="submit-order"]')

    // 5. Verify order appears in positions
    await expect(page.locator('[data-testid="position-card"]')).toBeVisible()
    await expect(page.locator('[data-testid="position-symbol"]')).toContainText('EURUSD')

    // 6. Close position
    await page.click('[data-testid="close-position-button"]')
    await page.click('[data-testid="confirm-close"]')

    // 7. Verify position is closed
    await expect(page.locator('[data-testid="position-card"]')).not.toBeVisible()
  })

  test('error handling during network failure', async ({ page }) => {
    // Simulate network failure
    await page.route('/api/trading/**', route => route.abort())

    // Attempt to place order
    await page.click('[data-testid="new-order-button"]')
    await page.fill('[data-testid="size-input"]', '0.1')
    await page.click('[data-testid="submit-order"]')

    // Verify error handling
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible()
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible()

    // Test retry functionality
    await page.unroute('/api/trading/**')
    await page.click('[data-testid="retry-button"]')

    // Verify recovery
    await expect(page.locator('[data-testid="position-card"]')).toBeVisible()
  })
})

// Performance testing
// tests/performance/trading-performance.test.ts
import { test, expect } from '@playwright/test'

test.describe('Trading Performance', () => {
  test('chart rendering performance', async ({ page }) => {
    // Navigate to trading dashboard
    await page.goto('/dashboard')

    // Measure chart load time
    const chartLoadStart = Date.now()
    await page.waitForSelector('[data-testid="trading-chart"]')
    const chartLoadTime = Date.now() - chartLoadStart

    expect(chartLoadTime).toBeLessThan(2000) // Chart should load in <2s

    // Measure real-time update performance
    const updateStart = Date.now()
    await page.waitForFunction(() => {
      const chart = document.querySelector('[data-testid="price-display"]')
      return chart && chart.textContent !== 'Loading...'
    })
    const updateTime = Date.now() - updateStart

    expect(updateTime).toBeLessThan(100) // Updates should be <100ms
  })

  test('memory usage during extended session', async ({ page }) => {
    await page.goto('/dashboard')

    // Get initial memory baseline
    const initialMemory = await page.evaluate(() => {
      return (performance as any).memory?.usedJSHeapSize || 0
    })

    // Simulate 1 hour of trading activity
    for (let i = 0; i < 60; i++) {
      // Trigger data updates
      await page.dispatchEvent('[data-testid="price-display"]', 'dataupdate')
      await page.waitForTimeout(1000) // 1 second interval

      // Check memory every 10 iterations
      if (i % 10 === 0) {
        const currentMemory = await page.evaluate(() => {
          return (performance as any).memory?.usedJSHeapSize || 0
        })

        const memoryIncrease = currentMemory - initialMemory
        const increasePercent = (memoryIncrease / initialMemory) * 100

        // Memory should not increase by more than 50% over 1 hour
        expect(increasePercent).toBeLessThan(50)
      }
    }
  })
})
```

### 5.4 Performance Optimization Rules

```typescript
// Performance optimization guidelines for trading applications
export const PerformanceOptimizationRules = {
  // 1. React optimization patterns
  react: {
    // Use React.memo for expensive components
    memoization: `
      export const TradingPositionCard = React.memo<TradingPositionCardProps>(({ position }) => {
        // Component implementation
      }, (prevProps, nextProps) => {
        // Custom comparison for trading-specific updates
        return (
          prevProps.position.id === nextProps.position.id &&
          prevProps.position.pnl === nextProps.position.pnl &&
          prevProps.position.currentPrice === nextProps.position.currentPrice
        )
      })
    `,

    // Use useMemo for expensive calculations
    calculations: `
      const pnlCalculation = useMemo(() => {
        return calculateComplexPnL(position, marketData, fees)
      }, [position.size, position.entryPrice, marketData.currentPrice, fees])
    `,

    // Use useCallback for event handlers
    callbacks: `
      const handleOrderSubmit = useCallback(async (orderData: OrderRequest) => {
        try {
          await tradingService.executeOrder(orderData)
        } catch (error) {
          errorDNA.captureError(error, { component: 'OrderEntry' })
        }
      }, [tradingService, errorDNA])
    `,

    // Optimize re-renders with proper dependencies
    dependencies: `
      useEffect(() => {
        // Only re-run when essential data changes
        updateTradingState(position)
      }, [position.id, position.pnl]) // Don't include entire position object
    `
  },

  // 2. WebSocket and real-time data optimization
  realtime: {
    // Throttle high-frequency updates
    throttling: `
      const throttledPriceUpdate = useCallback(
        throttle((price: number) => {
          setCurrentPrice(price)
        }, 50), // Limit to 20 updates per second
        []
      )
    `,

    // Batch updates using requestAnimationFrame
    batching: `
      class UpdateBatcher {
        private pending = new Map<string, any>()
        private rafId: number | null = null

        schedule<T>(key: string, data: T, updateFn: (data: T) => void) {
          this.pending.set(key, { data, updateFn })

          if (!this.rafId) {
            this.rafId = requestAnimationFrame(() => {
              this.flush()
            })
          }
        }

        private flush() {
          for (const [key, { data, updateFn }] of this.pending) {
            updateFn(data)
          }
          this.pending.clear()
          this.rafId = null
        }
      }
    `,

    // Virtual scrolling for large datasets
    virtualScrolling: `
      import { FixedSizeList as List } from 'react-window'

      const TradingHistoryList: React.FC = ({ trades }) => {
        const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => (
          <div style={style}>
            <TradeHistoryItem trade={trades[index]} />
          </div>
        )

        return (
          <List
            height={400}
            itemCount={trades.length}
            itemSize={60}
            width="100%"
          >
            {Row}
          </List>
        )
      }
    `
  },

  // 3. Bundle optimization
  bundleOptimization: {
    // Code splitting by route and feature
    routing: `
      const TradingDashboard = lazy(() => import('./pages/TradingDashboard'))
      const AnalyticsDashboard = lazy(() => import('./pages/AnalyticsDashboard'))
      const UserSettings = lazy(() => import('./pages/UserSettings'))

      // Route-based code splitting
      <Routes>
        <Route path="/trading" element={
          <Suspense fallback={<DashboardSkeleton />}>
            <TradingDashboard />
          </Suspense>
        } />
      </Routes>
    `,

    // Dynamic imports for heavy components
    dynamicImports: `
      const TradingViewChart = lazy(() =>
        import('./components/TradingViewChart').then(module => ({
          default: module.TradingViewChart
        }))
      )

      // Use with suspense and error boundary
      <TradingErrorBoundary>
        <Suspense fallback={<ChartSkeleton />}>
          <TradingViewChart symbol={symbol} />
        </Suspense>
      </TradingErrorBoundary>
    `,

    // Tree shaking optimization
    treeShaking: `
      // Import only what you need
      import { debounce, throttle } from 'lodash'
      // Instead of: import _ from 'lodash'

      // Use barrel exports carefully
      export { Button } from './Button'
      export { Card } from './Card'
      // Instead of: export * from './components'
    `
  },

  // 4. Memory management
  memoryManagement: {
    // Cleanup subscriptions and timers
    cleanup: `
      useEffect(() => {
        const subscription = tradingWebSocket.subscribe(handleUpdate)
        const interval = setInterval(refreshData, 5000)

        return () => {
          subscription.unsubscribe()
          clearInterval(interval)
        }
      }, [])
    `,

    // Avoid memory leaks in stores
    storeCleanup: `
      const useTradingStore = create<TradingState>((set, get) => ({
        positions: [],
        cleanup: () => {
          set({ positions: [] })
          // Clear any cached data
          positionCache.clear()
        }
      }))
    `,

    // Weak references for large objects
    weakReferences: `
      class ChartDataCache {
        private cache = new WeakMap<Symbol, ChartData>()

        set(symbol: Symbol, data: ChartData) {
          this.cache.set(symbol, data)
        }

        get(symbol: Symbol): ChartData | undefined {
          return this.cache.get(symbol)
        }
      }
    `
  },

  // 5. Performance monitoring
  monitoring: {
    // Performance metrics collection
    metricsCollection: `
      const usePerformanceMetrics = (componentName: string) => {
        const renderCount = useRef(0)
        const renderTimes = useRef<number[]>([])

        useEffect(() => {
          const start = performance.now()
          renderCount.current++

          return () => {
            const end = performance.now()
            const renderTime = end - start
            renderTimes.current.push(renderTime)

            // Alert on slow renders
            if (renderTime > 16) { // 60fps threshold
              console.warn(\`Slow render in \${componentName}: \${renderTime}ms\`)
            }

            // Report metrics periodically
            if (renderCount.current % 100 === 0) {
              reportPerformanceMetrics(componentName, {
                avgRenderTime: renderTimes.current.reduce((a, b) => a + b) / renderTimes.current.length,
                renderCount: renderCount.current
              })
            }
          }
        })
      }
    `,

    // Memory usage tracking
    memoryTracking: `
      const useMemoryMonitor = () => {
        useEffect(() => {
          const checkMemory = () => {
            const memory = (performance as any).memory
            if (memory) {
              const usedMB = memory.usedJSHeapSize / 1024 / 1024
              const limitMB = memory.jsHeapSizeLimit / 1024 / 1024
              const usagePercent = (usedMB / limitMB) * 100

              if (usagePercent > 80) {
                console.warn(\`High memory usage: \${usagePercent.toFixed(1)}%\`)
                // Trigger cleanup
                triggerMemoryCleanup()
              }
            }
          }

          const interval = setInterval(checkMemory, 30000) // Check every 30s
          return () => clearInterval(interval)
        }, [])
      }
    `,

    // Bundle size monitoring
    bundleMonitoring: `
      // webpack-bundle-analyzer configuration
      const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin

      module.exports = {
        plugins: [
          new BundleAnalyzerPlugin({
            analyzerMode: 'static',
            openAnalyzer: false,
            generateStatsFile: true,
            statsFilename: 'bundle-stats.json'
          })
        ]
      }
    `
  }
}

// Performance budget and targets
export const PerformanceBudget = {
  // Initial load performance
  initialLoad: {
    firstContentfulPaint: '<1.5s',
    largestContentfulPaint: '<2s',
    firstInputDelay: '<100ms',
    cumulativeLayoutShift: '<0.1',
    totalBlockingTime: '<300ms'
  },

  // Runtime performance
  runtime: {
    chartUpdateLatency: '<10ms',
    webSocketLatency: '<50ms',
    orderExecutionTime: '<500ms',
    componentRenderTime: '<16ms', // 60fps
    memoryUsageIncrease: '<50% per hour'
  },

  // Bundle size targets
  bundleSize: {
    initialBundle: '<500KB gzipped',
    tradingModule: '<200KB gzipped',
    chartingLibrary: '<150KB gzipped',
    totalAssets: '<2MB gzipped'
  },

  // Network performance
  network: {
    apiResponseTime: '<200ms (95th percentile)',
    webSocketReconnection: '<3s',
    assetLoadTime: '<1s per asset',
    offlineCapability: 'Basic functionality'
  }
}
```

---

## CONCLUSION

This comprehensive modular UI architecture plan provides a robust foundation for the AI trading platform frontend that:

### ✅ **Centralized Error Handling**
- **Frontend ErrorDNA** system mirrors backend architecture
- Component-level error boundaries with intelligent recovery
- Context enrichment for trading sessions and market conditions
- Seamless integration with backend error correlation

### ✅ **Modular Component Architecture**
- **Feature-based modules** mirroring backend services (trading-engine, market-data, user-management, analytics, ai-orchestration)
- **Shared component library** with ShadCN UI + Material UI integration
- **Service layer abstraction** for API communication
- **State management per module** with Zustand + TanStack Query

### ✅ **Real-time Data Flow**
- **WebSocket integration** with <10ms update optimization
- **State synchronization** strategies with performance monitoring
- **Trading data pipeline** with latency tracking
- **Update batching** using RequestAnimationFrame

### ✅ **Technology Integration**
- **ShadCN UI + Material UI** hybrid approach for optimal performance
- **Zustand + TanStack Query** for client/server state separation
- **TradingView Charts** integration with AI signals overlay
- **TypeScript** comprehensive type safety throughout

### ✅ **Development Guidelines**
- **Component naming conventions** following domain-driven patterns
- **File organization standards** with module boundaries
- **Testing strategies** covering unit, integration, and E2E scenarios
- **Performance optimization rules** with monitoring and budgets

### 🎯 **Key Performance Targets**
- **Real-time updates**: <10ms WebSocket processing
- **Chart rendering**: 60fps performance
- **Initial load**: <2s for dashboard
- **Bundle size**: <500KB initial bundle
- **Memory usage**: <50% increase per hour

This architecture ensures scalability, maintainability, and exceptional performance for trading applications while maintaining consistency with the backend's centralized design principles.
