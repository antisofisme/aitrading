import React from 'react';
import { Box, Chip, Typography, useTheme } from '@mui/material';
import { CheckCircle, XCircle, AlertCircle, Clock, Wifi, WifiOff } from 'lucide-react';

type StatusType = 'success' | 'error' | 'warning' | 'info' | 'pending' | 'online' | 'offline';

interface StatusIndicatorProps {
  status: StatusType;
  label?: string;
  size?: 'small' | 'medium';
  variant?: 'dot' | 'chip' | 'icon';
  showIcon?: boolean;
}

const statusConfig = {
  success: {
    color: '#4caf50',
    icon: CheckCircle,
    label: 'Success',
  },
  error: {
    color: '#f44336',
    icon: XCircle,
    label: 'Error',
  },
  warning: {
    color: '#ff9800',
    icon: AlertCircle,
    label: 'Warning',
  },
  info: {
    color: '#2196f3',
    icon: AlertCircle,
    label: 'Info',
  },
  pending: {
    color: '#9e9e9e',
    icon: Clock,
    label: 'Pending',
  },
  online: {
    color: '#4caf50',
    icon: Wifi,
    label: 'Online',
  },
  offline: {
    color: '#f44336',
    icon: WifiOff,
    label: 'Offline',
  },
};

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  label,
  size = 'medium',
  variant = 'chip',
  showIcon = true,
}) => {
  const theme = useTheme();
  const config = statusConfig[status];
  const displayLabel = label || config.label;

  const iconSize = size === 'small' ? 16 : 20;
  const IconComponent = config.icon;

  if (variant === 'dot') {
    return (
      <Box display="flex" alignItems="center" gap={1}>
        <Box
          width={size === 'small' ? 8 : 10}
          height={size === 'small' ? 8 : 10}
          borderRadius="50%"
          bgcolor={config.color}
          sx={{
            animation: status === 'pending' ? 'pulse 2s infinite' : 'none',
            '@keyframes pulse': {
              '0%': { opacity: 1 },
              '50%': { opacity: 0.5 },
              '100%': { opacity: 1 },
            },
          }}
        />
        {displayLabel && (
          <Typography
            variant={size === 'small' ? 'caption' : 'body2'}
            color="text.secondary"
          >
            {displayLabel}
          </Typography>
        )}
      </Box>
    );
  }

  if (variant === 'icon') {
    return (
      <Box display="flex" alignItems="center" gap={1}>
        {showIcon && (
          <IconComponent
            size={iconSize}
            style={{ color: config.color }}
          />
        )}
        {displayLabel && (
          <Typography
            variant={size === 'small' ? 'caption' : 'body2'}
            color="text.secondary"
          >
            {displayLabel}
          </Typography>
        )}
      </Box>
    );
  }

  // Chip variant
  return (
    <Chip
      size={size}
      icon={
        showIcon ? (
          <IconComponent size={iconSize} style={{ color: config.color }} />
        ) : undefined
      }
      label={displayLabel}
      sx={{
        backgroundColor: `${config.color}20`,
        color: config.color,
        borderColor: config.color,
        '& .MuiChip-icon': {
          color: config.color,
        },
        animation: status === 'pending' ? 'pulse 2s infinite' : 'none',
        '@keyframes pulse': {
          '0%': { opacity: 1 },
          '50%': { opacity: 0.7 },
          '100%': { opacity: 1 },
        },
      }}
      variant="outlined"
    />
  );
};

export default StatusIndicator;