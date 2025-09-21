# Component Structure and Organization

## Overview
This document outlines the file and folder organization patterns for the AI Trading Platform frontend, focusing on scalability, maintainability, and developer experience.

## Directory Structure

```
src/
├── components/                 # Reusable UI components
│   ├── ui/                    # ShadCN UI components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── input.tsx
│   │   └── ...
│   ├── bridge/                # Material UI + ShadCN bridge components
│   │   ├── mui-shadcn-bridge.tsx
│   │   └── trading-button.tsx
│   ├── layout/                # Layout components
│   │   ├── app-layout.tsx
│   │   ├── sidebar.tsx
│   │   ├── header.tsx
│   │   └── footer.tsx
│   ├── forms/                 # Form components
│   │   ├── trading-form.tsx
│   │   ├── portfolio-form.tsx
│   │   └── validation/
│   ├── charts/                # Chart components
│   │   ├── trading-chart.tsx
│   │   ├── portfolio-chart.tsx
│   │   └── indicators/
│   ├── trading/               # Trading-specific components
│   │   ├── order-book.tsx
│   │   ├── position-manager.tsx
│   │   ├── trade-history.tsx
│   │   └── risk-management.tsx
│   ├── portfolio/             # Portfolio components
│   │   ├── portfolio-overview.tsx
│   │   ├── asset-allocation.tsx
│   │   └── performance-metrics.tsx
│   ├── market-data/           # Market data components
│   │   ├── ticker-list.tsx
│   │   ├── market-overview.tsx
│   │   └── news-feed.tsx
│   ├── error-boundaries/      # Error boundary components
│   │   ├── trading-error-boundary.tsx
│   │   ├── data-error-boundary.tsx
│   │   └── global-error-boundary.tsx
│   └── shared/                # Shared utility components
│       ├── loading.tsx
│       ├── error-fallback.tsx
│       ├── confirmation-dialog.tsx
│       └── data-table.tsx
├── features/                  # Feature-based modules
│   ├── trading/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── store/
│   │   ├── types/
│   │   └── utils/
│   ├── portfolio/
│   ├── market-data/
│   ├── auth/
│   └── analytics/
├── hooks/                     # Global custom hooks
│   ├── use-trading-data.ts
│   ├── use-websocket.ts
│   ├── use-error-recovery.ts
│   └── use-performance-monitor.ts
├── store/                     # Zustand stores
│   ├── trading-store.ts
│   ├── portfolio-store.ts
│   ├── market-data-store.ts
│   ├── auth-store.ts
│   └── app-store.ts
├── lib/                       # Utility libraries
│   ├── api/
│   ├── websocket/
│   ├── error-dna/
│   ├── performance/
│   ├── utils.ts
│   └── constants.ts
├── types/                     # TypeScript type definitions
│   ├── trading.ts
│   ├── portfolio.ts
│   ├── market-data.ts
│   ├── auth.ts
│   └── api.ts
├── styles/                    # Global styles
│   ├── globals.css
│   ├── components.css
│   └── utilities.css
└── config/                    # Configuration files
    ├── theme/
    ├── api.ts
    ├── websocket.ts
    └── constants.ts
```