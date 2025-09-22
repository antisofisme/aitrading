import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  LinearProgress,
  IconButton,
  Tooltip,
  useTheme,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  MoreVertical,
  Target,
  Shield,
  Brain,
} from 'lucide-react';
import { TradingPosition } from '../../types';
import { StatusIndicator } from '../ui/StatusIndicator';

interface TradingPositionCardProps {
  position: TradingPosition;
  onClick?: () => void;
  onMenuClick?: () => void;
  showAIInsights?: boolean;
  showRiskMetrics?: boolean;
}

export const TradingPositionCard: React.FC<TradingPositionCardProps> = ({
  position,
  onClick,
  onMenuClick,
  showAIInsights = true,
  showRiskMetrics = true,
}) => {
  const theme = useTheme();
  const isProfit = position.pnl > 0;
  const isLoss = position.pnl < 0;

  // Format currency values
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  // Format percentage
  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  // Get PnL color
  const getPnLColor = () => {
    if (isProfit) return theme.custom.trading.profit;
    if (isLoss) return theme.custom.trading.loss;
    return theme.custom.trading.neutral;
  };

  // Get position status color
  const getStatusColor = () => {
    switch (position.status) {
      case 'open':
        return 'success';
      case 'pending':
        return 'warning';
      case 'closed':
        return 'info';
      default:
        return 'info';
    }
  };

  // Calculate AI confidence level
  const getConfidenceLevel = (confidence?: number): string => {
    if (!confidence) return 'N/A';
    if (confidence >= 0.8) return 'High';
    if (confidence >= 0.6) return 'Medium';
    return 'Low';
  };

  // Get confidence color
  const getConfidenceColor = (confidence?: number): string => {
    if (!confidence) return theme.palette.grey[500];
    if (confidence >= 0.8) return theme.palette.success.main;
    if (confidence >= 0.6) return theme.palette.warning.main;
    return theme.palette.error.main;
  };

  return (
    <Card
      sx={{
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.2s ease-in-out',
        '&:hover': onClick
          ? {
              transform: 'translateY(-2px)',
              boxShadow: theme.shadows[4],
            }
          : {},
        border: `1px solid ${theme.palette.divider}`,
        className: isProfit ? 'profit-row' : isLoss ? 'loss-row' : '',
      }}
      onClick={onClick}
    >
      <CardContent>
        {/* Header */}
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Box display="flex" alignItems="center" gap={1}>
            {/* Trend Icon */}
            {isProfit ? (
              <TrendingUp size={20} style={{ color: theme.custom.trading.profit }} />
            ) : isLoss ? (
              <TrendingDown size={20} style={{ color: theme.custom.trading.loss }} />
            ) : (
              <Activity size={20} style={{ color: theme.custom.trading.neutral }} />
            )}

            {/* Symbol */}
            <Typography variant="h6" fontWeight={600}>
              {position.symbol}
            </Typography>

            {/* Side Badge */}
            <Chip
              label={position.side.toUpperCase()}
              size="small"
              color={position.side === 'buy' ? 'success' : 'error'}
              variant="outlined"
            />
          </Box>

          <Box display="flex" alignItems="center" gap={1}>
            {/* Status */}
            <StatusIndicator
              status={getStatusColor() as any}
              label={position.status}
              size="small"
              variant="dot"
            />

            {/* Menu */}
            {onMenuClick && (
              <IconButton size="small" onClick={onMenuClick}>
                <MoreVertical size={16} />
              </IconButton>
            )}
          </Box>
        </Box>

        {/* Position Details */}
        <Box display="flex" justifyContent="space-between" mb={2}>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Size
            </Typography>
            <Typography variant="body2" fontWeight={500}>
              {position.size.toLocaleString()}
            </Typography>
          </Box>

          <Box textAlign="center">
            <Typography variant="caption" color="text.secondary">
              Entry Price
            </Typography>
            <Typography variant="body2" fontWeight={500}>
              {formatCurrency(position.entryPrice)}
            </Typography>
          </Box>

          <Box textAlign="right">
            <Typography variant="caption" color="text.secondary">
              Current Price
            </Typography>
            <Typography variant="body2" fontWeight={500}>
              {formatCurrency(position.currentPrice)}
            </Typography>
          </Box>
        </Box>

        {/* PnL Section */}
        <Box mb={showAIInsights || showRiskMetrics ? 2 : 0}>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="caption" color="text.secondary">
              P&L
            </Typography>
            <Box textAlign="right">
              <Typography
                variant="h6"
                fontWeight={600}
                sx={{ color: getPnLColor() }}
              >
                {formatCurrency(position.pnl)}
              </Typography>
              <Typography
                variant="caption"
                sx={{ color: getPnLColor() }}
              >
                {formatPercent(position.pnlPercent)}
              </Typography>
            </Box>
          </Box>

          {/* PnL Progress Bar */}
          <LinearProgress
            variant="determinate"
            value={Math.min(Math.abs(position.pnlPercent), 100)}
            sx={{
              mt: 1,
              height: 4,
              borderRadius: 2,
              backgroundColor: theme.palette.grey[300],
              '& .MuiLinearProgress-bar': {
                backgroundColor: getPnLColor(),
              },
            }}
          />
        </Box>

        {/* AI Insights */}
        {showAIInsights && position.aiConfidence && (
          <Box mb={showRiskMetrics ? 2 : 0}>
            <Box display="flex" alignItems="center" gap={1} mb={1}>
              <Brain size={16} style={{ color: theme.palette.primary.main }} />
              <Typography variant="caption" color="text.secondary">
                AI Analysis
              </Typography>
            </Box>

            <Box display="flex" justifyContent="space-between" alignItems="center">
              <Box>
                <Typography variant="body2" fontWeight={500}>
                  Confidence: {getConfidenceLevel(position.aiConfidence)}
                </Typography>
                {position.marketRegime && (
                  <Typography variant="caption" color="text.secondary">
                    Regime: {position.marketRegime}
                  </Typography>
                )}
              </Box>

              <Box
                width={40}
                height={40}
                borderRadius="50%"
                display="flex"
                alignItems="center"
                justifyContent="center"
                sx={{
                  backgroundColor: `${getConfidenceColor(position.aiConfidence)}20`,
                  border: `2px solid ${getConfidenceColor(position.aiConfidence)}`,
                }}
              >
                <Typography
                  variant="caption"
                  fontWeight={600}
                  sx={{ color: getConfidenceColor(position.aiConfidence) }}
                >
                  {Math.round((position.aiConfidence || 0) * 100)}%
                </Typography>
              </Box>
            </Box>
          </Box>
        )}

        {/* Risk Metrics */}
        {showRiskMetrics && (
          <Box>
            <Box display="flex" alignItems="center" gap={1} mb={1}>
              <Shield size={16} style={{ color: theme.palette.warning.main }} />
              <Typography variant="caption" color="text.secondary">
                Risk Management
              </Typography>
            </Box>

            <Box display="flex" justifyContent="space-between">
              {position.stopLoss && (
                <Tooltip title="Stop Loss">
                  <Box textAlign="center">
                    <Typography variant="caption" color="text.secondary">
                      SL
                    </Typography>
                    <Typography variant="body2" fontSize="0.75rem">
                      {formatCurrency(position.stopLoss)}
                    </Typography>
                  </Box>
                </Tooltip>
              )}

              {position.takeProfit && (
                <Tooltip title="Take Profit">
                  <Box textAlign="center">
                    <Typography variant="caption" color="text.secondary">
                      TP
                    </Typography>
                    <Typography variant="body2" fontSize="0.75rem">
                      {formatCurrency(position.takeProfit)}
                    </Typography>
                  </Box>
                </Tooltip>
              )}

              <Tooltip title="Position opened">
                <Box textAlign="right">
                  <Typography variant="caption" color="text.secondary">
                    Opened
                  </Typography>
                  <Typography variant="body2" fontSize="0.75rem">
                    {new Date(position.openTime).toLocaleDateString()}
                  </Typography>
                </Box>
              </Tooltip>
            </Box>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default TradingPositionCard;