# AI Trading Platform - Frontend

A modern, responsive React frontend for the AI Trading Platform with Material-UI, real-time data visualization, and multi-tenant support.

## 🚀 Features

### Core Features
- **Progressive Web App (PWA)** - Installable, offline-capable web application
- **Real-time Trading Dashboard** - Live market data with sub-50ms updates
- **Multi-tenant Architecture** - Support for multiple organizations with custom branding
- **AI-powered Insights** - ML predictions and market regime analysis
- **Responsive Design** - Optimized for desktop, tablet, and mobile devices
- **Dark/Light Theme** - Automatic theme switching with custom tenant branding

### Trading Components
- **Real-time Price Charts** - Candlestick, line, and area charts with technical indicators
- **Position Management** - Live position tracking with P&L visualization
- **AI Predictions Display** - ML model confidence scores and market insights
- **Risk Management** - Stop loss, take profit, and risk metrics
- **Market Regime Detection** - Visual indicators for market conditions

### Technical Features
- **TypeScript** - Full type safety and IntelliSense support
- **Material-UI v5** - Modern component library with custom theming
- **WebSocket Integration** - Real-time data streaming
- **State Management** - React Context with optimized re-renders
- **Memory Coordination** - Backend synchronization for collaborative features
- **Performance Monitoring** - Core Web Vitals and custom metrics

## 📁 Project Structure

```
src/frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── ui/             # Generic UI components
│   │   ├── trading/        # Trading-specific components
│   │   ├── charts/         # Chart components
│   │   ├── forms/          # Form components
│   │   └── layout/         # Layout components
│   ├── pages/              # Page components
│   │   ├── dashboard/      # Dashboard pages
│   │   ├── auth/           # Authentication pages
│   │   ├── analytics/      # Analytics pages
│   │   └── settings/       # Settings pages
│   ├── contexts/           # React contexts
│   ├── services/           # API and external services
│   ├── hooks/              # Custom React hooks
│   ├── types/              # TypeScript type definitions
│   ├── utils/              # Utility functions
│   └── theme/              # Material-UI theme configuration
├── public/                 # Static assets
├── package.json           # Dependencies and scripts
├── vite.config.ts         # Vite configuration
└── tsconfig.json          # TypeScript configuration
```

## 🛠️ Technology Stack

### Core Technologies
- **React 18** - Modern React with concurrent features
- **TypeScript** - Static type checking
- **Vite** - Fast build tool and development server
- **Material-UI v5** - React component library
- **Emotion** - CSS-in-JS styling

### Data & State Management
- **React Query** - Server state management and caching
- **React Context** - Global state management
- **WebSocket** - Real-time data streaming
- **Memory Service** - Backend coordination and caching

### Visualization & Charts
- **Chart.js** - Flexible charting library
- **React-ChartJS-2** - React wrapper for Chart.js
- **D3.js** - Data visualization utilities
- **MUI X Charts** - Advanced Material-UI charts

### Development Tools
- **ESLint** - Code linting
- **Prettier** - Code formatting
- **Vitest** - Unit testing framework
- **TypeScript** - Type checking

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ and npm/yarn
- Access to the AI Trading backend services

### Installation

1. **Install dependencies:**
   ```bash
   cd src/frontend
   npm install
   ```

2. **Environment setup:**
   ```bash
   # Create environment file
   cp .env.example .env.local

   # Configure API endpoints
   echo "VITE_API_URL=http://localhost:8000" >> .env.local
   echo "VITE_WS_URL=ws://localhost:8000/ws" >> .env.local
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

4. **Open in browser:**
   ```
   http://localhost:3000
   ```

### Build for Production

```bash
# Build for production
npm run build

# Preview production build
npm run preview

# Type checking
npm run type-check

# Linting
npm run lint
```

## 🎨 Theming & Customization

### Tenant Branding
The frontend supports multi-tenant branding with:
- Custom primary/secondary colors
- Logo and favicon customization
- Light/dark/auto theme modes
- Typography customization

### Theme Configuration
```typescript
// Example tenant branding
const tenantBranding = {
  primaryColor: '#1976d2',
  secondaryColor: '#9c27b0',
  logo: 'https://example.com/logo.png',
  theme: 'auto' // 'light', 'dark', or 'auto'
};
```

### Custom Components
All components follow Material-UI theming and can be customized via:
- Theme overrides in `src/theme/index.ts`
- Component-specific styling
- CSS-in-JS with Emotion

## 📊 Real-time Features

### WebSocket Integration
```typescript
import { useWebSocket } from './services/websocket';

const { subscribe, on } = useWebSocket();

// Subscribe to price updates
subscribe('prices', { symbols: ['EURUSD', 'GBPUSD'] });

// Listen for updates
on('price_update', (data) => {
  console.log('New price:', data);
});
```

### Memory Coordination
```typescript
import { useBackendCoordination } from './services/memory';

const { coordinate, getSwarmState } = useBackendCoordination();

// Coordinate with backend services
await coordinate('ml-service', { action: 'predict', symbol: 'EURUSD' });

// Get swarm state
const state = await getSwarmState('trading-swarm-1');
```

## 🔐 Authentication & Security

### Multi-tenant Authentication
- JWT-based authentication with refresh tokens
- Tenant isolation and validation
- Role-based access control
- Security audit logging

### Protected Routes
```typescript
import { ProtectedRoute } from './components/ProtectedRoute';

<ProtectedRoute requireFeature="ai_insights">
  <AIInsightsPage />
</ProtectedRoute>
```

### Feature Gates
```typescript
import { FeatureGate } from './contexts/TenantContext';

<FeatureGate feature="advanced_charts">
  <AdvancedChart />
</FeatureGate>
```

## 📱 Progressive Web App

### PWA Features
- **Offline Support** - Service worker with caching strategies
- **App Installation** - Add to home screen functionality
- **Push Notifications** - Real-time trading alerts
- **Background Sync** - Data synchronization when online

### Manifest Configuration
```json
{
  "name": "AI Trading Platform",
  "short_name": "AI Trading",
  "display": "standalone",
  "orientation": "portrait-primary",
  "theme_color": "#1976d2",
  "background_color": "#ffffff"
}
```

## 📈 Performance Optimization

### Performance Features
- **Code Splitting** - Lazy loading of routes and components
- **Bundle Optimization** - Tree shaking and minification
- **Image Optimization** - WebP support and lazy loading
- **Caching Strategies** - Service worker and HTTP caching

### Monitoring
- **Core Web Vitals** - LCP, FID, CLS tracking
- **Custom Metrics** - Trading-specific performance metrics
- **Error Tracking** - Global error boundary and reporting

## 🧪 Testing

### Testing Strategy
```bash
# Run unit tests
npm run test

# Run tests with UI
npm run test:ui

# Test coverage
npm run test:coverage
```

### Test Structure
- **Unit Tests** - Component and utility testing
- **Integration Tests** - API and context testing
- **E2E Tests** - Full user workflow testing

## 🚀 Deployment

### Production Build
```bash
# Build for production
npm run build

# Build output in dist/ folder
ls dist/
```

### Environment Variables
```bash
# Production environment
VITE_API_URL=https://api.aitrading.com
VITE_WS_URL=wss://api.aitrading.com/ws
VITE_SENTRY_DSN=your-sentry-dsn
```

### Docker Deployment
```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 🔧 Configuration

### Vite Configuration
- **Development Server** - Hot reload and proxy configuration
- **Build Optimization** - Code splitting and compression
- **PWA Plugin** - Service worker generation
- **Path Aliases** - Import path shortcuts

### TypeScript Configuration
- **Strict Mode** - Full type checking enabled
- **Path Mapping** - Absolute imports with aliases
- **Module Resolution** - ESNext with bundler resolution

## 📚 API Integration

### Service Layer
```typescript
// API service with authentication
import { api } from './services/api';

const response = await api.get('/trading/positions');
if (response.success) {
  console.log('Positions:', response.data);
}
```

### Error Handling
- **Global Error Boundary** - React error boundary
- **API Error Handling** - Centralized error processing
- **User Feedback** - Toast notifications and error states

## 🎯 Best Practices

### Code Quality
- **TypeScript** - Full type coverage
- **ESLint** - Code linting and formatting
- **Prettier** - Consistent code style
- **Husky** - Pre-commit hooks

### Performance
- **React.memo** - Component memoization
- **useMemo/useCallback** - Value and function memoization
- **Lazy Loading** - Route and component splitting
- **Virtualization** - Large list optimization

### Security
- **Input Validation** - Client-side validation
- **XSS Protection** - Content sanitization
- **CSRF Protection** - Token validation
- **Secure Storage** - Sensitive data handling

## 🐛 Troubleshooting

### Common Issues
1. **WebSocket Connection Issues**
   - Check CORS configuration
   - Verify WebSocket URL
   - Check authentication tokens

2. **Theme Not Loading**
   - Verify tenant configuration
   - Check theme provider setup
   - Validate color values

3. **Real-time Updates Not Working**
   - Check WebSocket connection
   - Verify subscription setup
   - Check memory service

### Debug Mode
```bash
# Enable debug logging
VITE_DEBUG=true npm run dev
```

## 📄 License

This project is part of the AI Trading Platform. See the main project README for licensing information.

## 🤝 Contributing

1. Follow the coding standards and TypeScript guidelines
2. Write tests for new components and features
3. Update documentation for API changes
4. Use conventional commit messages
5. Ensure responsive design compliance

## 📞 Support

For technical support and questions:
- Check the main project documentation
- Review the troubleshooting section
- Create an issue with detailed reproduction steps