# Frontend - AI Trading Platform

## Structure Overview

React-based frontend with real-time trading interface, subscription management, and responsive design optimized for <200ms load times.

## 📁 Folder Structure

```
frontend/
├── src/
│   ├── components/           # Reusable UI Components
│   │   ├── common/          # Generic components (Button, Modal, Form, Input, etc.)
│   │   ├── layout/          # Layout components (Header, Sidebar, Navigation, Footer)
│   │   └── charts/          # Trading-specific chart components (TradingView, Indicators)
│   ├── pages/               # Route-based Page Components
│   │   ├── auth/            # Authentication pages (Login, Register, ForgotPassword)
│   │   ├── dashboard/       # Main trading dashboard and overview
│   │   ├── trading/         # Trading interface (Orders, Portfolio, Positions)
│   │   └── settings/        # User settings (Profile, Subscription, Preferences)
│   ├── hooks/               # Custom React Hooks
│   ├── services/            # External Service Integration
│   ├── utils/               # Helper Functions & Utilities
│   └── assets/              # Static Assets
│       ├── styles/          # CSS files, themes, global styles
│       ├── images/          # Icons, logos, images
│       └── fonts/           # Custom fonts
├── public/                  # Static Public Files
└── package.json            # Dependencies & Scripts
```

---

## 🧩 Components Structure

### `/src/components/common/`
**Purpose**: MUI-based reusable components for trading interface
- `TradingButton.jsx` - MUI Button with ShadCN icons and trading variants
- `TradingModal.jsx` - MUI Dialog with ShadCN icons for confirmations
- `Form/` - MUI form components (TextField, Select, Switch, etc.)
- `DataTable.jsx` - MUI DataGrid with ShadCN icons for actions
- `LoadingStates.jsx` - MUI Skeleton and CircularProgress
- `Notifications.jsx` - MUI Snackbar with ShadCN status icons

### `/src/components/layout/`
**Purpose**: MUI layout components for professional trading interface
- `Header.jsx` - MUI AppBar with user menu and notifications
- `Sidebar.jsx` - MUI Drawer with trading navigation
- `Navigation.jsx` - MUI Tabs and Breadcrumbs
- `Footer.jsx` - MUI Container footer
- `Layout.jsx` - MUI Box layout with responsive breakpoints

### `/src/components/charts/`
**Purpose**: Trading-specific visualization components
- `TradingChart.jsx` - Main price chart component
- `TechnicalIndicators.jsx` - RSI, MACD, SMA overlays
- `OrderBook.jsx` - Real-time order book display
- `PriceAlert.jsx` - Price alert visualization

---

## 📄 Pages Structure

### `/src/pages/auth/`
**Purpose**: User authentication and account management
- `Login.jsx` - User login form
- `Register.jsx` - User registration form
- `ForgotPassword.jsx` - Password recovery
- `VerifyEmail.jsx` - Email verification

### `/src/pages/dashboard/`
**Purpose**: Main trading dashboard and overview
- `MainDashboard.jsx` - Trading overview dashboard
- `MarketOverview.jsx` - Market summary and trends
- `PerformanceMetrics.jsx` - Trading performance analytics

### `/src/pages/trading/`
**Purpose**: Core trading functionality
- `TradingInterface.jsx` - Main trading page
- `OrderManagement.jsx` - Order placement and management
- `Portfolio.jsx` - Portfolio overview and positions
- `TradingHistory.jsx` - Trading history and logs

### `/src/pages/settings/`
**Purpose**: User settings and account management
- `UserProfile.jsx` - Profile settings and preferences
- `SubscriptionManagement.jsx` - Billing and tier management
- `TradingPreferences.jsx` - Trading-specific settings
- `APISettings.jsx` - API keys and integrations

---

## 🔧 Services & Utilities

### `/src/hooks/`
**Purpose**: Custom React hooks for reusable logic
- `useWebSocket.js` - WebSocket connection management
- `useAuth.js` - Authentication state management
- `useTrading.js` - Trading-specific hooks
- `useSubscription.js` - Subscription tier management
- `useRealTime.js` - Real-time data handling

### `/src/services/`
**Purpose**: External API and service integration
- `api.js` - Main API client configuration
- `websocket.js` - WebSocket service for real-time data
- `auth.js` - Authentication API calls
- `trading.js` - Trading API integration
- `subscription.js` - Billing and subscription APIs

### `/src/utils/`
**Purpose**: Helper functions and utilities
- `formatters.js` - Number, currency, date formatting
- `validators.js` - Form validation functions
- `constants.js` - API endpoints, configuration
- `helpers.js` - General utility functions

---

## 🎨 Assets Structure

### `/src/assets/styles/`
- `theme.js` - MUI theme configuration (colors, typography, spacing)
- `trading-theme.js` - Trading-specific theme (dark mode optimized)
- `global-styles.js` - MUI GlobalStyles for overrides
- `responsive.js` - MUI breakpoints and responsive utilities

### `/src/assets/images/`
- `logos/` - Application logos and branding
- `charts/` - Chart-related images and overlays

### `/src/components/icons/`
- **ShadCN/UI Icons Integration**: Modern, consistent icon system
- `TradingIcons.jsx` - Trading-specific icons (buy, sell, portfolio, alerts)
- `NavigationIcons.jsx` - App navigation icons (dashboard, settings, profile)
- `StatusIcons.jsx` - Status indicators (success, error, warning, loading)
- `ChartIcons.jsx` - Chart and analysis icons (indicators, tools, timeframes)

### `/src/assets/fonts/`
- Custom font files for branding consistency

---

## ⚡ Performance Features

### **Real-time Data Management**
- **WebSocket Integration**: Live market data streaming
- **State Management**: Efficient real-time state updates
- **Chart Optimization**: Smooth 60fps chart animations
- **Memory Management**: Automatic cleanup of old data

### **Load Time Optimization**
- **Code Splitting**: Route-based lazy loading
- **Asset Optimization**: Compressed images and fonts
- **Caching Strategy**: Service worker for offline capability
- **Bundle Optimization**: Tree shaking and minification

### **Target Performance**
- **Initial Load**: <200ms (as per plan3 requirements)
- **Route Navigation**: <100ms between pages
- **Real-time Updates**: <50ms data reflection
- **Chart Rendering**: 60fps smooth animations

---

## 🚀 Key Technologies

- **React 18**: Latest React with concurrent features
- **TypeScript**: Type safety for better development
- **Material-UI (MUI)**: Professional design system for financial apps
- **ShadCN/UI Icons**: High-quality icon system for trading interface
- **Vite**: Fast build tool and dev server
- **WebSocket**: Real-time data communication
- **Chart Libraries**: TradingView or Recharts (MUI-compatible)
- **State Management**: Context API or Zustand for lightweight state
- **Styling**: MUI Theme system + emotion/styled
- **Testing**: Jest + React Testing Library + MUI Testing Utils

---

## 📱 Responsive Design

### **Breakpoints**
- **Mobile**: 320px - 768px (Compact trading interface)
- **Tablet**: 768px - 1024px (Adaptive layout)
- **Desktop**: 1024px+ (Full trading dashboard)

### **Mobile Optimizations**
- Touch-optimized trading controls
- Simplified chart interactions
- Collapsible navigation
- Essential features prioritization

---

## 🔄 Integration with Backend

### **API Communication**
- REST API calls for user management and settings
- WebSocket for real-time trading data
- Authentication via JWT tokens
- Error handling and retry logic

### **Data Flow**
```
Backend WebSocket → Frontend Service → React State → UI Components
          ↓
Real-time charts, order book, portfolio updates
```

### **Hybrid Architecture Support**
- Optimized for <30ms total latency target
- Efficient data visualization of pre-processed client data
- Real-time reflection of AI decision results
- Subscription-based feature toggling

---

**Key Innovation**: Clean, developer-friendly structure without numbering for better maintainability and standard React development patterns.