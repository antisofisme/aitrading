import React, { useEffect, useRef, useMemo } from 'react';
import { Box, Paper, Typography, IconButton, Tooltip, useTheme } from '@mui/material';
import { TrendingUp, TrendingDown, Settings, Fullscreen } from 'lucide-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  ChartOptions,
  TooltipItem,
} from 'chart.js';
import { Chart } from 'react-chartjs-2';
import { ChartData, ChartConfig, MarketData } from '../../types';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  ChartTooltip,
  Legend
);

interface PriceChartProps {
  data: ChartData[];
  symbol: string;
  config?: Partial<ChartConfig>;
  height?: number;
  onSettingsClick?: () => void;
  onFullscreenClick?: () => void;
  isFullscreen?: boolean;
  showVolume?: boolean;
  showControls?: boolean;
  realTimeData?: MarketData;
}

export const PriceChart: React.FC<PriceChartProps> = ({
  data,
  symbol,
  config = {},
  height = 400,
  onSettingsClick,
  onFullscreenClick,
  isFullscreen = false,
  showVolume = true,
  showControls = true,
  realTimeData,
}) => {
  const theme = useTheme();
  const chartRef = useRef<ChartJS>(null);

  // Default chart configuration
  const defaultConfig: ChartConfig = {
    timeframe: '1h',
    indicators: [],
    chartType: 'candlestick',
    overlays: [],
    theme: theme.palette.mode,
  };

  const chartConfig = { ...defaultConfig, ...config };

  // Prepare chart data
  const chartData = useMemo(() => {
    if (!data || data.length === 0) return null;

    const labels = data.map(item => {
      const date = new Date(item.timestamp);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    });

    // Price data (candlestick or line)
    const priceData = data.map(item => {
      if (chartConfig.chartType === 'candlestick') {
        return {
          x: item.timestamp,
          o: item.open,
          h: item.high,
          l: item.low,
          c: item.close,
        };
      }
      return item.close;
    });

    // Volume data
    const volumeData = showVolume ? data.map(item => item.volume) : [];

    const datasets = [];

    // Main price dataset
    if (chartConfig.chartType === 'candlestick') {
      // For candlestick, we'll use a line chart with high/low representation
      datasets.push({
        label: symbol,
        data: data.map(item => item.close),
        borderColor: theme.palette.primary.main,
        backgroundColor: `${theme.palette.primary.main}20`,
        borderWidth: 2,
        fill: chartConfig.chartType === 'area',
        tension: 0.1,
        pointRadius: 0,
        pointHoverRadius: 4,
      });

      // Add high/low shadow
      datasets.push({
        label: 'High',
        data: data.map(item => item.high),
        borderColor: `${theme.palette.primary.main}40`,
        backgroundColor: 'transparent',
        borderWidth: 1,
        fill: false,
        pointRadius: 0,
        pointHoverRadius: 0,
      });

      datasets.push({
        label: 'Low',
        data: data.map(item => item.low),
        borderColor: `${theme.palette.primary.main}40`,
        backgroundColor: 'transparent',
        borderWidth: 1,
        fill: false,
        pointRadius: 0,
        pointHoverRadius: 0,
      });
    } else {
      // Line or area chart
      datasets.push({
        label: symbol,
        data: priceData,
        borderColor: theme.palette.primary.main,
        backgroundColor: chartConfig.chartType === 'area'
          ? `${theme.palette.primary.main}20`
          : 'transparent',
        borderWidth: 2,
        fill: chartConfig.chartType === 'area',
        tension: 0.1,
        pointRadius: 0,
        pointHoverRadius: 4,
      });
    }

    // Add volume dataset if enabled
    if (showVolume && volumeData.length > 0) {
      datasets.push({
        label: 'Volume',
        data: volumeData,
        backgroundColor: `${theme.palette.secondary.main}30`,
        borderColor: theme.palette.secondary.main,
        borderWidth: 1,
        yAxisID: 'volume',
        type: 'bar' as const,
      });
    }

    // Add indicators
    chartConfig.indicators.forEach(indicator => {
      if (indicator.visible && indicator.values.length === data.length) {
        datasets.push({
          label: indicator.name,
          data: indicator.values,
          borderColor: indicator.color,
          backgroundColor: 'transparent',
          borderWidth: 1,
          fill: false,
          pointRadius: 0,
          pointHoverRadius: 2,
        });
      }
    });

    return {
      labels,
      datasets,
    };
  }, [data, chartConfig, theme, symbol, showVolume]);

  // Chart options
  const options: ChartOptions<'line' | 'bar'> = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      intersect: false,
      mode: 'index',
    },
    scales: {
      x: {
        type: 'category',
        display: true,
        grid: {
          color: theme.custom.charts.grid,
          drawOnChartArea: true,
          drawTicks: true,
        },
        ticks: {
          color: theme.custom.charts.axis,
          maxTicksLimit: 10,
        },
      },
      y: {
        type: 'linear',
        display: true,
        position: 'right',
        grid: {
          color: theme.custom.charts.grid,
          drawOnChartArea: true,
          drawTicks: true,
        },
        ticks: {
          color: theme.custom.charts.axis,
          callback: function(value) {
            return new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: 'USD',
              minimumFractionDigits: 2,
              maximumFractionDigits: 4,
            }).format(value as number);
          },
        },
      },
      ...(showVolume && {
        volume: {
          type: 'linear' as const,
          display: false,
          position: 'right' as const,
          min: 0,
          max: Math.max(...(data?.map(d => d.volume) || [0])) * 4,
        },
      }),
    },
    plugins: {
      tooltip: {
        backgroundColor: theme.palette.background.paper,
        titleColor: theme.palette.text.primary,
        bodyColor: theme.palette.text.secondary,
        borderColor: theme.palette.divider,
        borderWidth: 1,
        cornerRadius: 8,
        displayColors: true,
        callbacks: {
          title: (context: TooltipItem<'line' | 'bar'>[]) => {
            const index = context[0].dataIndex;
            if (data && data[index]) {
              return new Date(data[index].timestamp).toLocaleString();
            }
            return '';
          },
          label: (context: TooltipItem<'line' | 'bar'>) => {
            const datasetLabel = context.dataset.label || '';
            const value = context.parsed.y;

            if (datasetLabel === 'Volume') {
              return `${datasetLabel}: ${value.toLocaleString()}`;
            }

            return `${datasetLabel}: ${new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: 'USD',
              minimumFractionDigits: 2,
              maximumFractionDigits: 4,
            }).format(value)}`;
          },
          afterBody: (context: TooltipItem<'line' | 'bar'>[]) => {
            const index = context[0].dataIndex;
            if (data && data[index] && chartConfig.chartType === 'candlestick') {
              const item = data[index];
              return [
                `Open: ${new Intl.NumberFormat('en-US', {
                  style: 'currency',
                  currency: 'USD',
                  minimumFractionDigits: 4,
                }).format(item.open)}`,
                `High: ${new Intl.NumberFormat('en-US', {
                  style: 'currency',
                  currency: 'USD',
                  minimumFractionDigits: 4,
                }).format(item.high)}`,
                `Low: ${new Intl.NumberFormat('en-US', {
                  style: 'currency',
                  currency: 'USD',
                  minimumFractionDigits: 4,
                }).format(item.low)}`,
                `Close: ${new Intl.NumberFormat('en-US', {
                  style: 'currency',
                  currency: 'USD',
                  minimumFractionDigits: 4,
                }).format(item.close)}`,
              ];
            }
            return [];
          },
        },
      },
      legend: {
        display: false,
      },
    },
    animation: {
      duration: 0, // Disable animations for real-time updates
    },
    elements: {
      point: {
        radius: 0,
        hoverRadius: 4,
      },
      line: {
        tension: 0.1,
      },
    },
  }), [theme, data, chartConfig, showVolume]);

  // Update chart with real-time data
  useEffect(() => {
    if (realTimeData && chartRef.current) {
      const chart = chartRef.current;

      // Update the last data point with real-time price
      if (chart.data.datasets[0] && chart.data.datasets[0].data) {
        const lastIndex = chart.data.datasets[0].data.length - 1;
        if (lastIndex >= 0) {
          (chart.data.datasets[0].data as number[])[lastIndex] = realTimeData.last;
          chart.update('none'); // Update without animation for performance
        }
      }
    }
  }, [realTimeData]);

  // Calculate price change
  const priceChange = useMemo(() => {
    if (!data || data.length < 2) return { value: 0, percent: 0 };

    const current = realTimeData?.last || data[data.length - 1]?.close || 0;
    const previous = data[data.length - 2]?.close || 0;
    const value = current - previous;
    const percent = (value / previous) * 100;

    return { value, percent };
  }, [data, realTimeData]);

  if (!chartData) {
    return (
      <Paper sx={{ p: 3, height }}>
        <Typography color="text.secondary" textAlign="center">
          No data available
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper
      sx={{
        height: isFullscreen ? '100vh' : height,
        position: isFullscreen ? 'fixed' : 'relative',
        top: isFullscreen ? 0 : 'auto',
        left: isFullscreen ? 0 : 'auto',
        right: isFullscreen ? 0 : 'auto',
        bottom: isFullscreen ? 0 : 'auto',
        zIndex: isFullscreen ? theme.zIndex.modal : 'auto',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Chart Header */}
      <Box
        display="flex"
        alignItems="center"
        justifyContent="space-between"
        p={2}
        borderBottom={`1px solid ${theme.palette.divider}`}
      >
        <Box display="flex" alignItems="center" gap={2}>
          <Typography variant="h6" fontWeight={600}>
            {symbol}
          </Typography>

          {realTimeData && (
            <Box display="flex" alignItems="center" gap={1}>
              <Typography variant="h6" fontWeight={600}>
                {new Intl.NumberFormat('en-US', {
                  style: 'currency',
                  currency: 'USD',
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 4,
                }).format(realTimeData.last)}
              </Typography>

              <Box display="flex" alignItems="center" gap={0.5}>
                {priceChange.value >= 0 ? (
                  <TrendingUp size={16} style={{ color: theme.custom.trading.profit }} />
                ) : (
                  <TrendingDown size={16} style={{ color: theme.custom.trading.loss }} />
                )}
                <Typography
                  variant="body2"
                  sx={{
                    color: priceChange.value >= 0
                      ? theme.custom.trading.profit
                      : theme.custom.trading.loss,
                  }}
                >
                  {priceChange.value >= 0 ? '+' : ''}{priceChange.value.toFixed(4)}
                  ({priceChange.percent >= 0 ? '+' : ''}{priceChange.percent.toFixed(2)}%)
                </Typography>
              </Box>
            </Box>
          )}
        </Box>

        {showControls && (
          <Box display="flex" alignItems="center" gap={1}>
            <Tooltip title="Chart Settings">
              <IconButton size="small" onClick={onSettingsClick}>
                <Settings size={16} />
              </IconButton>
            </Tooltip>

            <Tooltip title={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}>
              <IconButton size="small" onClick={onFullscreenClick}>
                <Fullscreen size={16} />
              </IconButton>
            </Tooltip>
          </Box>
        )}
      </Box>

      {/* Chart Canvas */}
      <Box flex={1} p={1}>
        <Chart
          ref={chartRef}
          type="line"
          data={chartData}
          options={options}
        />
      </Box>

      {/* Chart Footer with Timeframe */}
      <Box
        display="flex"
        alignItems="center"
        justifyContent="center"
        p={1}
        borderTop={`1px solid ${theme.palette.divider}`}
      >
        <Typography variant="caption" color="text.secondary">
          Timeframe: {chartConfig.timeframe.toUpperCase()} •
          Last updated: {new Date().toLocaleTimeString()}
        </Typography>
      </Box>
    </Paper>
  );
};

export default PriceChart;