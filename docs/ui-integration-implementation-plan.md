# AI Trading Platform - UI Integration Implementation Plan

## Table of Contents
1. [Material UI + ShadCN UI Integration Strategy](#material-ui--shadcn-ui-integration-strategy)
2. [Frontend ErrorDNA Implementation](#frontend-errordna-implementation)
3. [Component Structure and Organization](#component-structure-and-organization)
4. [State Management Strategy](#state-management-strategy)
5. [Real-time Data Integration Patterns](#real-time-data-integration-patterns)

---

## 1. Material UI + ShadCN UI Integration Strategy

### Overview
This strategy combines Material UI's robust component ecosystem with ShadCN UI's modern design system and utility-first approach, optimizing for performance and developer experience.

### Library Allocation Strategy

#### Material UI Components (Production-Ready)
- **Data Display**: Tables, Charts, Grids
- **Navigation**: AppBar, Drawer, Tabs, Breadcrumbs
- **Feedback**: Snackbar, Progress indicators, Skeleton
- **Complex Inputs**: DatePicker, Autocomplete, Select
- **Layout**: Container, Grid, Stack, Box

#### ShadCN UI Components (Modern UX)
- **Form Controls**: Input, Button, Checkbox, Radio
- **Overlays**: Dialog, Sheet, Popover, Tooltip
- **Content**: Card, Badge, Avatar, Separator
- **Typography**: Text, Heading, Code
- **Data Display**: Table (when custom styling needed)

### Unified Theming Approach

```typescript
// src/config/theme/unified-theme.ts
import { createTheme } from '@mui/material/styles';
import { type Config } from 'tailwindcss';

// Base design tokens
export const designTokens = {
  colors: {
    primary: {
      50: '#f0f9ff',
      500: '#3b82f6',
      900: '#1e3a8a',
    },
    gray: {
      50: '#f9fafb',
      500: '#6b7280',
      900: '#111827',
    },
    success: '#10b981',
    error: '#ef4444',
    warning: '#f59e0b',
    info: '#3b82f6',
  },
  spacing: {
    xs: '0.5rem',
    sm: '0.75rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
  },
  borderRadius: {
    sm: '0.375rem',
    md: '0.5rem',
    lg: '0.75rem',
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
    },
  },
};

// Material UI Theme
export const muiTheme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: designTokens.colors.primary[500],
      light: designTokens.colors.primary[50],
      dark: designTokens.colors.primary[900],
    },
    grey: designTokens.colors.gray,
    success: { main: designTokens.colors.success },
    error: { main: designTokens.colors.error },
    warning: { main: designTokens.colors.warning },
    info: { main: designTokens.colors.info },
  },
  typography: {
    fontFamily: designTokens.typography.fontFamily,
    fontSize: 14,
  },
  shape: {
    borderRadius: parseInt(designTokens.borderRadius.md.replace('rem', '')) * 16,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 500,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
        },
      },
    },
  },
});

// Tailwind Config for ShadCN UI
export const tailwindConfig: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: designTokens.colors.primary[500],
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
      },
      fontFamily: {
        sans: designTokens.typography.fontFamily.split(','),
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
};
```

### CSS Variables Integration

```css
/* src/styles/globals.css */
@import '@mui/material/styles';
@import 'tailwindcss/base';
@import 'tailwindcss/components';
@import 'tailwindcss/utilities';

:root {
  /* ShadCN UI Variables */
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --card: 0 0% 100%;
  --card-foreground: 222.2 84% 4.9%;
  --popover: 0 0% 100%;
  --popover-foreground: 222.2 84% 4.9%;
  --primary: 221.2 83.2% 53.3%;
  --primary-foreground: 210 40% 98%;
  --secondary: 210 40% 96%;
  --secondary-foreground: 222.2 84% 4.9%;
  --muted: 210 40% 96%;
  --muted-foreground: 215.4 16.3% 46.9%;
  --accent: 210 40% 96%;
  --accent-foreground: 222.2 84% 4.9%;
  --destructive: 0 84.2% 60.2%;
  --destructive-foreground: 210 40% 98%;
  --border: 214.3 31.8% 91.4%;
  --input: 214.3 31.8% 91.4%;
  --ring: 221.2 83.2% 53.3%;
  --radius: 0.5rem;
}

.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  /* ... dark mode variables */
}

/* Material UI CSS Variables Override */
.MuiThemeProvider-root {
  --mui-palette-primary-main: hsl(var(--primary));
  --mui-palette-background-default: hsl(var(--background));
}
```

### Component Bridge Pattern

```typescript
// src/components/bridge/mui-shadcn-bridge.tsx
import { Button as MuiButton } from '@mui/material';
import { Button as ShadcnButton } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface BridgeButtonProps {
  variant?: 'mui' | 'shadcn';
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

export const BridgeButton: React.FC<BridgeButtonProps> = ({
  variant = 'shadcn',
  children,
  className,
  ...props
}) => {
  if (variant === 'mui') {
    return (
      <MuiButton
        className={cn('!text-sm !font-medium', className)}
        {...props}
      >
        {children}
      </MuiButton>
    );
  }

  return (
    <ShadcnButton className={className} {...props}>
      {children}
    </ShadcnButton>
  );
};

// Usage Component Wrapper
export const TradingButton: React.FC<{
  trading?: boolean;
  children: React.ReactNode;
}> = ({ trading, children, ...props }) => (
  <BridgeButton
    variant={trading ? 'mui' : 'shadcn'}
    className={trading ? 'trading-action-button' : ''}
    {...props}
  >
    {children}
  </BridgeButton>
);
```

### Bundle Size Optimization

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // Material UI Core
          'mui-core': ['@mui/material/styles', '@mui/material/useTheme'],
          'mui-components': [
            '@mui/material/Button',
            '@mui/material/Card',
            '@mui/material/Grid',
            '@mui/material/Table',
          ],
          'mui-icons': ['@mui/icons-material'],

          // ShadCN UI
          'shadcn-ui': [
            './src/components/ui/button',
            './src/components/ui/card',
            './src/components/ui/input',
            './src/components/ui/dialog',
          ],

          // Trading specific
          'trading-components': [
            './src/components/trading',
            './src/components/charts',
          ],

          // Vendor
          'vendor-charts': ['lightweight-charts', 'recharts'],
          'vendor-utils': ['date-fns', 'lodash-es'],
        },
      },
    },
  },
  optimizeDeps: {
    include: [
      '@mui/material/styles',
      '@mui/material/useTheme',
      'date-fns',
      'lightweight-charts',
    ],
  },
});
```

### Tree Shaking Configuration

```typescript
// src/lib/mui-imports.ts - Centralized MUI imports
export {
  Button,
  Card,
  CardContent,
  CardHeader,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  AppBar,
  Toolbar,
  Drawer,
  List,
  ListItem,
  ListItemText,
  Snackbar,
  Alert,
  CircularProgress,
  LinearProgress,
  Skeleton,
} from '@mui/material';

export type {
  ButtonProps,
  CardProps,
  GridProps,
  TableProps,
} from '@mui/material';

// src/lib/shadcn-imports.ts - Centralized ShadCN imports
export { Button } from '@/components/ui/button';
export { Input } from '@/components/ui/input';
export { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
export { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
export { Badge } from '@/components/ui/badge';
export { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
```

---

## 2. Frontend ErrorDNA Implementation

### Error Boundary Architecture

```typescript
// src/components/error-boundaries/trading-error-boundary.tsx
import React, { Component, ErrorInfo, ReactNode } from 'react';
import { ErrorDNA } from '@/lib/error-dna';
import { Alert, Button, Card, CardContent } from '@mui/material';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  context: string;
  critical?: boolean;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorId: string | null;
  retryCount: number;
}

export class TradingErrorBoundary extends Component<Props, State> {
  private errorDNA: ErrorDNA;
  private maxRetries = 3;

  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorId: null,
      retryCount: 0,
    };
    this.errorDNA = new ErrorDNA({
      context: props.context,
      critical: props.critical || false,
    });
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return {
      hasError: true,
      error,
    };
  }

  async componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    const errorSignature = await this.errorDNA.captureError(error, {
      componentStack: errorInfo.componentStack,
      context: this.props.context,
      retryCount: this.state.retryCount,
      userAgent: navigator.userAgent,
      timestamp: Date.now(),
      url: window.location.href,
      userId: this.getCurrentUserId(),
      sessionId: this.getSessionId(),
    });

    this.setState({ errorId: errorSignature.id });

    // Critical errors need immediate notification
    if (this.props.critical) {
      this.notifyErrorService(errorSignature);
    }
  }

  private getCurrentUserId = (): string => {
    // Get from auth context or state management
    return 'user-id';
  };

  private getSessionId = (): string => {
    return sessionStorage.getItem('sessionId') || 'unknown';
  };

  private notifyErrorService = (errorSignature: any) => {
    // Send to error tracking service
    fetch('/api/errors/critical', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(errorSignature),
    });
  };

  private handleRetry = () => {
    if (this.state.retryCount < this.maxRetries) {
      this.setState(prevState => ({
        hasError: false,
        error: null,
        errorId: null,
        retryCount: prevState.retryCount + 1,
      }));
    }
  };

  private handleReport = () => {
    if (this.state.errorId) {
      window.open(`/error-report/${this.state.errorId}`, '_blank');
    }
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <Card className="m-4 border-red-200 bg-red-50">
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-4">
              <AlertTriangle className="h-6 w-6 text-red-600" />
              <h3 className="text-lg font-semibold text-red-800">
                {this.props.critical ? 'Critical Error' : 'Something went wrong'}
              </h3>
            </div>

            <p className="text-red-700 mb-4">
              {this.props.critical
                ? 'A critical error occurred in the trading system. Our team has been notified.'
                : 'An error occurred in this component. You can try refreshing or continue using other features.'}
            </p>

            <div className="flex gap-2">
              <Button
                variant="contained"
                color="primary"
                startIcon={<RefreshCw className="h-4 w-4" />}
                onClick={this.handleRetry}
                disabled={this.state.retryCount >= this.maxRetries}
              >
                {this.state.retryCount > 0 ? `Retry (${this.maxRetries - this.state.retryCount} left)` : 'Retry'}
              </Button>

              <Button
                variant="outlined"
                onClick={this.handleReport}
                disabled={!this.state.errorId}
              >
                Report Issue
              </Button>
            </div>

            {process.env.NODE_ENV === 'development' && (
              <details className="mt-4">
                <summary className="cursor-pointer text-sm text-red-600">
                  Error Details (Development)
                </summary>
                <pre className="mt-2 text-xs bg-red-100 p-2 rounded overflow-auto">
                  {this.state.error?.stack}
                </pre>
              </details>
            )}
          </CardContent>
        </Card>
      );
    }

    return this.props.children;
  }
}
```

### ErrorDNA Core Implementation

```typescript
// src/lib/error-dna/index.ts
import { createHash } from 'crypto';

export interface ErrorContext {
  componentStack?: string;
  context: string;
  retryCount?: number;
  userAgent?: string;
  timestamp: number;
  url: string;
  userId?: string;
  sessionId?: string;
  tradeId?: string;
  portfolioId?: string;
  marketData?: any;
}

export interface ErrorSignature {
  id: string;
  fingerprint: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  category: string;
  message: string;
  stack: string;
  context: ErrorContext;
  patterns: string[];
  suggestions: string[];
}

export class ErrorDNA {
  private context: string;
  private critical: boolean;

  constructor(config: { context: string; critical: boolean }) {
    this.context = config.context;
    this.critical = config.critical;
  }

  async captureError(error: Error, context: ErrorContext): Promise<ErrorSignature> {
    const fingerprint = this.generateFingerprint(error, context);
    const category = this.categorizeError(error);
    const severity = this.calculateSeverity(error, context, category);
    const patterns = this.extractPatterns(error, context);
    const suggestions = this.generateSuggestions(error, category, patterns);

    const signature: ErrorSignature = {
      id: this.generateId(fingerprint, context.timestamp),
      fingerprint,
      severity,
      category,
      message: error.message,
      stack: error.stack || '',
      context,
      patterns,
      suggestions,
    };

    // Store locally for correlation
    this.storeErrorSignature(signature);

    // Send to backend for processing
    await this.sendToBackend(signature);

    return signature;
  }

  private generateFingerprint(error: Error, context: ErrorContext): string {
    const stackTrace = this.normalizeStackTrace(error.stack || '');
    const errorType = error.constructor.name;
    const componentContext = context.componentStack?.split('\n')[0] || '';

    const fingerprintData = `${errorType}:${error.message}:${stackTrace}:${componentContext}`;

    return createHash('sha256')
      .update(fingerprintData)
      .digest('hex')
      .substring(0, 16);
  }

  private normalizeStackTrace(stack: string): string {
    return stack
      .split('\n')
      .slice(0, 5) // First 5 lines for fingerprinting
      .map(line => line.replace(/:\d+:\d+/g, ':X:X')) // Remove line numbers
      .map(line => line.replace(/\?[^)]*\)/g, ')')) // Remove query params
      .join('|');
  }

  private categorizeError(error: Error): string {
    const message = error.message.toLowerCase();
    const stack = error.stack?.toLowerCase() || '';
    const name = error.constructor.name;

    // Network errors
    if (message.includes('fetch') || message.includes('network') || name === 'TypeError' && message.includes('failed to fetch')) {
      return 'network';
    }

    // Trading specific errors
    if (message.includes('trade') || message.includes('order') || message.includes('position')) {
      return 'trading';
    }

    // Data/State errors
    if (message.includes('undefined') || message.includes('null') || name === 'TypeError') {
      return 'data';
    }

    // React errors
    if (stack.includes('react') || stack.includes('reconciler')) {
      return 'react';
    }

    // Rendering errors
    if (name === 'ChunkLoadError' || message.includes('loading chunk')) {
      return 'chunk-loading';
    }

    // Permission errors
    if (message.includes('permission') || message.includes('unauthorized')) {
      return 'permission';
    }

    // Validation errors
    if (message.includes('validation') || message.includes('invalid')) {
      return 'validation';
    }

    return 'unknown';
  }

  private calculateSeverity(error: Error, context: ErrorContext, category: string): 'low' | 'medium' | 'high' | 'critical' {
    // Critical contexts
    if (this.critical || context.context.includes('trading') || context.context.includes('order')) {
      return 'critical';
    }

    // High severity categories
    if (['trading', 'network', 'permission'].includes(category)) {
      return 'high';
    }

    // Medium severity
    if (['data', 'validation'].includes(category) || context.retryCount && context.retryCount > 1) {
      return 'medium';
    }

    return 'low';
  }

  private extractPatterns(error: Error, context: ErrorContext): string[] {
    const patterns: string[] = [];

    // Timing patterns
    const hour = new Date(context.timestamp).getHours();
    if (hour >= 9 && hour <= 16) patterns.push('market-hours');
    if (hour >= 0 && hour <= 6) patterns.push('low-activity-hours');

    // User behavior patterns
    if (context.retryCount && context.retryCount > 0) patterns.push('user-retry');
    if (context.url.includes('dashboard')) patterns.push('dashboard-context');
    if (context.url.includes('trading')) patterns.push('trading-context');

    // Error frequency patterns
    const recentErrors = this.getRecentErrors(context.sessionId || '');
    if (recentErrors.length > 3) patterns.push('error-burst');
    if (recentErrors.filter(e => e.fingerprint === this.generateFingerprint(error, context)).length > 1) {
      patterns.push('recurring-error');
    }

    // Browser/device patterns
    if (context.userAgent?.includes('Mobile')) patterns.push('mobile-device');
    if (context.userAgent?.includes('Chrome')) patterns.push('chrome-browser');

    return patterns;
  }

  private generateSuggestions(error: Error, category: string, patterns: string[]): string[] {
    const suggestions: string[] = [];

    switch (category) {
      case 'network':
        suggestions.push('Check your internet connection');
        suggestions.push('Try refreshing the page');
        if (patterns.includes('market-hours')) {
          suggestions.push('High market activity may be causing delays');
        }
        break;

      case 'trading':
        suggestions.push('Verify your trading permissions');
        suggestions.push('Check if the market is open');
        suggestions.push('Ensure sufficient buying power');
        break;

      case 'data':
        suggestions.push('Try refreshing the data');
        suggestions.push('Check if you have the required permissions');
        break;

      case 'chunk-loading':
        suggestions.push('Clear your browser cache');
        suggestions.push('Check your internet connection');
        suggestions.push('Try hard refreshing (Ctrl+F5)');
        break;

      case 'validation':
        suggestions.push('Check your input values');
        suggestions.push('Ensure all required fields are filled');
        break;
    }

    if (patterns.includes('recurring-error')) {
      suggestions.push('This error has occurred multiple times - consider reporting it');
    }

    if (patterns.includes('mobile-device')) {
      suggestions.push('Try using the desktop version for full functionality');
    }

    return suggestions;
  }

  private generateId(fingerprint: string, timestamp: number): string {
    return `${fingerprint}-${timestamp.toString(36)}`;
  }

  private storeErrorSignature(signature: ErrorSignature): void {
    const stored = JSON.parse(localStorage.getItem('errorDNA') || '[]');
    stored.push({
      ...signature,
      stored: Date.now(),
    });

    // Keep only last 50 errors
    if (stored.length > 50) {
      stored.splice(0, stored.length - 50);
    }

    localStorage.setItem('errorDNA', JSON.stringify(stored));
  }

  private getRecentErrors(sessionId: string): ErrorSignature[] {
    const stored = JSON.parse(localStorage.getItem('errorDNA') || '[]');
    const oneHourAgo = Date.now() - (60 * 60 * 1000);

    return stored.filter((error: any) =>
      error.context.sessionId === sessionId &&
      error.context.timestamp > oneHourAgo
    );
  }

  private async sendToBackend(signature: ErrorSignature): Promise<void> {
    try {
      await fetch('/api/errors/capture', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(signature),
      });
    } catch (err) {
      console.warn('Failed to send error to backend:', err);
    }
  }
}
```

### Error Recovery Mechanisms

```typescript
// src/hooks/use-error-recovery.ts
import { useState, useCallback, useRef } from 'react';
import { ErrorDNA } from '@/lib/error-dna';

interface RecoveryOptions {
  maxRetries?: number;
  backoffMs?: number;
  context: string;
  onError?: (error: Error) => void;
  onRecover?: () => void;
}

export const useErrorRecovery = (options: RecoveryOptions) => {
  const [isRecovering, setIsRecovering] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const errorDNA = useRef(new ErrorDNA({
    context: options.context,
    critical: options.context.includes('trading')
  }));

  const executeWithRecovery = useCallback(async <T>(
    operation: () => Promise<T>,
    fallback?: () => Promise<T>
  ): Promise<T> => {
    try {
      const result = await operation();

      // Reset retry count on success
      if (retryCount > 0) {
        setRetryCount(0);
        options.onRecover?.();
      }

      return result;
    } catch (error) {
      const currentRetry = retryCount;
      const maxRetries = options.maxRetries || 3;

      // Capture error with ErrorDNA
      await errorDNA.current.captureError(error as Error, {
        context: options.context,
        retryCount: currentRetry,
        timestamp: Date.now(),
        url: window.location.href,
        userId: 'current-user-id', // Get from auth
        sessionId: sessionStorage.getItem('sessionId') || 'unknown',
      });

      options.onError?.(error as Error);

      // Try recovery if retries available
      if (currentRetry < maxRetries) {
        setIsRecovering(true);
        setRetryCount(currentRetry + 1);

        // Exponential backoff
        const backoffMs = (options.backoffMs || 1000) * Math.pow(2, currentRetry);
        await new Promise(resolve => setTimeout(resolve, backoffMs));

        setIsRecovering(false);
        return executeWithRecovery(operation, fallback);
      }

      // If fallback available, try it
      if (fallback) {
        try {
          return await fallback();
        } catch (fallbackError) {
          throw error; // Throw original error if fallback fails
        }
      }

      throw error;
    }
  }, [retryCount, options]);

  const reset = useCallback(() => {
    setRetryCount(0);
    setIsRecovering(false);
  }, []);

  return {
    executeWithRecovery,
    isRecovering,
    retryCount,
    reset,
    hasExceededRetries: retryCount >= (options.maxRetries || 3),
  };
};
```

---

*[Continuing with Component Structure, State Management, and Real-time Data Integration in the next parts...]*