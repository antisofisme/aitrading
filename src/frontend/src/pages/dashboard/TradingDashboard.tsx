import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Stack,
  Chip,
  IconButton,
  Tooltip,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  DollarSign,
  Target,
  AlertTriangle,
  RefreshCw,
  Settings,
} from 'lucide-react';
import { TradingPositionCard } from '../../components/trading/TradingPositionCard';
import { PriceChart } from '../../components/charts/PriceChart';
import { StatusIndicator } from '../../components/ui/StatusIndicator';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { useWebSocket } from '../../services/websocket';
import { useTenant } from '../../contexts/TenantContext';
import { useAuth } from '../../contexts/AuthContext';
import {
  TradingPosition,
  MarketData,
  ChartData,
  AIPrediction,
  Portfolio,
  PerformanceMetrics,
} from '../../types';

// Mock data for demonstration
const mockPositions: TradingPosition[] = [
  {
    id: '1',
    symbol: 'EURUSD',
    side: 'buy',
    size: 100000,
    entryPrice: 1.0845,
    currentPrice: 1.0867,
    pnl: 220,
    pnlPercent: 2.03,
    openTime: '2024-01-15T10:30:00Z',
    status: 'open',
    stopLoss: 1.0820,
    takeProfit: 1.0900,
    aiConfidence: 0.85,
    marketRegime: 'Trending',
  },
  {
    id: '2',
    symbol: 'GBPUSD',
    side: 'sell',
    size: 50000,
    entryPrice: 1.2675,
    currentPrice: 1.2632,
    pnl: 215,
    pnlPercent: 1.70,
    openTime: '2024-01-15T09:15:00Z',
    status: 'open',
    stopLoss: 1.2720,
    takeProfit: 1.2600,
    aiConfidence: 0.72,
    marketRegime: 'Volatile',
  },
  {
    id: '3',
    symbol: 'XAUUSD',
    side: 'buy',
    size: 10,
    entryPrice: 2025.50,
    currentPrice: 2018.30,
    pnl: -72,
    pnlPercent: -0.36,
    openTime: '2024-01-15T08:45:00Z',
    status: 'open',
    stopLoss: 2010.00,
    takeProfit: 2050.00,
    aiConfidence: 0.58,
    marketRegime: 'Sideways',
  },
];

const mockChartData: ChartData[] = Array.from({ length: 100 }, (_, i) => {
  const timestamp = new Date(Date.now() - (100 - i) * 60000).toISOString();
  const basePrice = 1.0850;
  const volatility = 0.002;
  const trend = (i - 50) * 0.00005;
  const random = (Math.random() - 0.5) * volatility;

  const close = basePrice + trend + random;
  const open = close + (Math.random() - 0.5) * volatility * 0.5;
  const high = Math.max(open, close) + Math.random() * volatility * 0.3;
  const low = Math.min(open, close) - Math.random() * volatility * 0.3;
  const volume = Math.floor(Math.random() * 1000000) + 500000;

  return {
    timestamp,
    open,
    high,
    low,
    close,
    volume,
  };
});

const mockAIPredictions: AIPrediction[] = [
  {
    id: '1',
    symbol: 'EURUSD',
    prediction: 'bullish',
    confidence: 0.85,
    timeframe: '4H',
    targetPrice: 1.0920,
    stopLoss: 1.0820,
    reasoning: ['Strong uptrend momentum', 'Positive correlation signals', 'Favorable market regime'],
    modelUsed: ['XGBoost', 'LSTM', 'Transformer'],
    marketRegime: 'Trending',
    riskLevel: 'medium',
    generatedAt: '2024-01-15T12:00:00Z',
    expiresAt: '2024-01-15T16:00:00Z',
  },
  {
    id: '2',
    symbol: 'GBPUSD',
    prediction: 'bearish',
    confidence: 0.72,
    timeframe: '1H',
    targetPrice: 1.2600,
    stopLoss: 1.2720,
    reasoning: ['Resistance level rejection', 'Negative sentiment indicators'],
    modelUsed: ['XGBoost', 'Random Forest'],
    marketRegime: 'Volatile',
    riskLevel: 'high',
    generatedAt: '2024-01-15T12:00:00Z',
    expiresAt: '2024-01-15T13:00:00Z',
  },
];

export const TradingDashboard: React.FC = () => {
  const theme = useTheme();
  const isTablet = useMediaQuery(theme.breakpoints.down('lg'));
  const { user } = useAuth();
  const { tenant, hasFeature } = useTenant();
  const { subscribe, on, off } = useWebSocket();

  const [positions, setPositions] = useState<TradingPosition[]>(mockPositions);
  const [chartData, setChartData] = useState<ChartData[]>(mockChartData);
  const [aiPredictions, setAIPredictions] = useState<AIPrediction[]>(mockAIPredictions);
  const [marketData, setMarketData] = useState<MarketData | null>(null);
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  // Portfolio metrics calculation
  const portfolioMetrics = React.useMemo(() => {
    const totalPnL = positions.reduce((sum, pos) => sum + pos.pnl, 0);
    const totalValue = positions.reduce((sum, pos) => sum + (pos.size * pos.currentPrice), 0);
    const totalPnLPercent = totalValue > 0 ? (totalPnL / totalValue) * 100 : 0;
    const openPositions = positions.filter(pos => pos.status === 'open').length;
    const profitablePositions = positions.filter(pos => pos.pnl > 0).length;
    const winRate = positions.length > 0 ? (profitablePositions / positions.length) * 100 : 0;

    return {
      totalPnL,
      totalPnLPercent,
      totalValue,
      openPositions,
      winRate,
    };
  }, [positions]);

  // WebSocket subscriptions
  useEffect(() => {
    if (user && tenant) {
      // Subscribe to real-time data
      subscribe('portfolio', { userId: user.id });
      subscribe('prices', { symbols: ['EURUSD', 'GBPUSD', 'XAUUSD'] });
      subscribe('ai_predictions', { symbols: ['EURUSD', 'GBPUSD', 'XAUUSD'] });

      // Set up event listeners
      const handlePositionUpdate = (data: any) => {
        setPositions(prev => {
          const index = prev.findIndex(pos => pos.id === data.id);
          if (index >= 0) {
            const updated = [...prev];
            updated[index] = { ...updated[index], ...data };
            return updated;
          }
          return prev;
        });
      };

      const handlePriceUpdate = (data: MarketData) => {
        setMarketData(data);
        setLastUpdate(new Date());
      };

      const handleAIPrediction = (data: AIPrediction) => {
        setAIPredictions(prev => {
          const filtered = prev.filter(p => p.symbol !== data.symbol || p.timeframe !== data.timeframe);
          return [data, ...filtered].slice(0, 10); // Keep last 10 predictions
        });
      };

      on('position_update', handlePositionUpdate);
      on('price_update', handlePriceUpdate);
      on('ai_prediction', handleAIPrediction);

      // Simulate loading
      setTimeout(() => setIsLoading(false), 1500);

      return () => {
        off('position_update', handlePositionUpdate);
        off('price_update', handlePriceUpdate);
        off('ai_prediction', handleAIPrediction);
      };
    }
  }, [user, tenant, subscribe, on, off]);

  // Handle refresh
  const handleRefresh = () => {
    setIsLoading(true);
    // In a real app, this would trigger data reload
    setTimeout(() => {
      setIsLoading(false);
      setLastUpdate(new Date());
    }, 1000);
  };

  if (isLoading) {
    return <LoadingSpinner fullScreen message="Loading trading dashboard..." />;
  }

  return (
    <Box>
      {/* Dashboard Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" fontWeight={600} gutterBottom>
            Trading Dashboard
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Welcome back, {user?.name}. Last updated: {lastUpdate.toLocaleTimeString()}
          </Typography>
        </Box>

        <Box display="flex" alignItems="center" gap={1}>
          <StatusIndicator
            status="online"
            label="Live"
            variant="chip"
            size="small"
          />

          <Tooltip title="Refresh">
            <IconButton onClick={handleRefresh} disabled={isLoading}>
              <RefreshCw size={20} />
            </IconButton>
          </Tooltip>

          <Tooltip title="Settings">
            <IconButton>
              <Settings size={20} />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Portfolio Overview Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} lg={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Total P&L
                  </Typography>
                  <Typography
                    variant="h5"
                    fontWeight={600}
                    sx={{
                      color: portfolioMetrics.totalPnL >= 0
                        ? theme.custom.trading.profit
                        : theme.custom.trading.loss,
                    }}
                  >
                    ${portfolioMetrics.totalPnL.toFixed(2)}
                  </Typography>
                  <Typography
                    variant="caption"
                    sx={{
                      color: portfolioMetrics.totalPnL >= 0
                        ? theme.custom.trading.profit
                        : theme.custom.trading.loss,
                    }}
                  >
                    {portfolioMetrics.totalPnLPercent >= 0 ? '+' : ''}{portfolioMetrics.totalPnLPercent.toFixed(2)}%
                  </Typography>
                </Box>
                <Box
                  p={2}
                  borderRadius="50%"
                  sx={{
                    backgroundColor: `${portfolioMetrics.totalPnL >= 0
                      ? theme.custom.trading.profit
                      : theme.custom.trading.loss}20`,
                  }}
                >
                  {portfolioMetrics.totalPnL >= 0 ? (
                    <TrendingUp style={{ color: theme.custom.trading.profit }} />
                  ) : (
                    <TrendingDown style={{ color: theme.custom.trading.loss }} />
                  )}
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} lg={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Portfolio Value
                  </Typography>
                  <Typography variant="h5" fontWeight={600}>
                    ${portfolioMetrics.totalValue.toLocaleString()}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Across {portfolioMetrics.openPositions} positions
                  </Typography>
                </Box>
                <Box
                  p={2}
                  borderRadius="50%"
                  sx={{ backgroundColor: `${theme.palette.primary.main}20` }}
                >
                  <DollarSign style={{ color: theme.palette.primary.main }} />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} lg={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Win Rate
                  </Typography>
                  <Typography variant="h5" fontWeight={600}>
                    {portfolioMetrics.winRate.toFixed(1)}%
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Last 30 days
                  </Typography>
                </Box>
                <Box
                  p={2}
                  borderRadius="50%"
                  sx={{ backgroundColor: `${theme.palette.success.main}20` }}
                >
                  <Target style={{ color: theme.palette.success.main }} />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} lg={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Open Positions
                  </Typography>
                  <Typography variant="h5" fontWeight={600}>
                    {portfolioMetrics.openPositions}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Active trades
                  </Typography>
                </Box>
                <Box
                  p={2}
                  borderRadius="50%"
                  sx={{ backgroundColor: `${theme.palette.info.main}20` }}
                >
                  <Activity style={{ color: theme.palette.info.main }} />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Main Content Grid */}
      <Grid container spacing={3}>
        {/* Charts Section */}
        <Grid item xs={12} lg={8}>
          <Stack spacing={3}>
            {/* Price Chart */}
            <PriceChart
              data={chartData}
              symbol="EURUSD"
              height={400}
              realTimeData={marketData}
              showVolume={true}
              showControls={true}
            />

            {/* AI Predictions */}
            {hasFeature('ai_insights') && (
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" justifyContent="between" mb={2}>
                    <Typography variant="h6" fontWeight={600}>
                      AI Predictions
                    </Typography>
                    <Chip
                      label="Live"
                      size="small"
                      color="success"
                      variant="outlined"
                    />
                  </Box>

                  <Stack spacing={2}>
                    {aiPredictions.map((prediction) => (
                      <Box
                        key={prediction.id}
                        p={2}
                        borderRadius={2}
                        sx={{
                          backgroundColor: theme.palette.action.hover,
                          border: `1px solid ${theme.palette.divider}`,
                        }}
                      >
                        <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                          <Box display="flex" alignItems="center" gap={1}>
                            <Typography variant="subtitle2" fontWeight={600}>
                              {prediction.symbol}
                            </Typography>
                            <Chip
                              label={prediction.prediction.toUpperCase()}
                              size="small"
                              color={prediction.prediction === 'bullish' ? 'success' : 'error'}
                              variant="outlined"
                            />
                            <Typography variant="caption" color="text.secondary">
                              {prediction.timeframe}
                            </Typography>
                          </Box>
                          <Typography
                            variant="body2"
                            fontWeight={600}
                            sx={{
                              color: prediction.confidence >= 0.8
                                ? theme.palette.success.main
                                : prediction.confidence >= 0.6
                                ? theme.palette.warning.main
                                : theme.palette.error.main,
                            }}
                          >
                            {Math.round(prediction.confidence * 100)}% confidence
                          </Typography>
                        </Box>

                        <Box display="flex" gap={2} mb={1}>
                          <Typography variant="caption">
                            Target: ${prediction.targetPrice?.toFixed(4)}
                          </Typography>
                          <Typography variant="caption">
                            Stop: ${prediction.stopLoss?.toFixed(4)}
                          </Typography>
                          <Typography variant="caption">
                            Risk: {prediction.riskLevel}
                          </Typography>
                        </Box>

                        <Typography variant="caption" color="text.secondary">
                          Models: {prediction.modelUsed.join(', ')}
                        </Typography>
                      </Box>
                    ))}
                  </Stack>
                </CardContent>
              </Card>
            )}
          </Stack>
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} lg={4}>
          <Stack spacing={3}>
            {/* Active Positions */}
            <Card>
              <CardContent>
                <Typography variant="h6" fontWeight={600} gutterBottom>
                  Active Positions
                </Typography>

                <Stack spacing={2}>
                  {positions.slice(0, isTablet ? 2 : 3).map((position) => (
                    <TradingPositionCard
                      key={position.id}
                      position={position}
                      showAIInsights={hasFeature('ai_insights')}
                      showRiskMetrics={true}
                    />
                  ))}
                </Stack>

                {positions.length > (isTablet ? 2 : 3) && (
                  <Box mt={2} textAlign="center">
                    <Typography variant="caption" color="text.secondary">
                      +{positions.length - (isTablet ? 2 : 3)} more positions
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>

            {/* Market Status */}
            <Card>
              <CardContent>
                <Typography variant="h6" fontWeight={600} gutterBottom>
                  Market Status
                </Typography>

                <Stack spacing={2}>
                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Typography variant="body2">Market Session</Typography>
                    <Chip label="London Open" color="success" size="small" />
                  </Box>

                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Typography variant="body2">Volatility</Typography>
                    <Chip label="Medium" color="warning" size="small" />
                  </Box>

                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Typography variant="body2">News Risk</Typography>
                    <Chip label="Low" color="success" size="small" />
                  </Box>

                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Typography variant="body2">Spread Quality</Typography>
                    <StatusIndicator status="success" label="Good" variant="dot" size="small" />
                  </Box>
                </Stack>
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card>
              <CardContent>
                <Typography variant="h6" fontWeight={600} gutterBottom>
                  Quick Actions
                </Typography>

                <Stack spacing={1}>
                  <Box p={1.5} borderRadius={1} sx={{ backgroundColor: theme.palette.action.hover, cursor: 'pointer' }}>
                    <Typography variant="body2" fontWeight={500}>
                      New Trade
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Open a new position
                    </Typography>
                  </Box>

                  <Box p={1.5} borderRadius={1} sx={{ backgroundColor: theme.palette.action.hover, cursor: 'pointer' }}>
                    <Typography variant="body2" fontWeight={500}>
                      Risk Analysis
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Review portfolio risk
                    </Typography>
                  </Box>

                  <Box p={1.5} borderRadius={1} sx={{ backgroundColor: theme.palette.action.hover, cursor: 'pointer' }}>
                    <Typography variant="body2" fontWeight={500}>
                      AI Recommendations
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Get ML-powered insights
                    </Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Stack>
        </Grid>
      </Grid>
    </Box>
  );
};

export default TradingDashboard;