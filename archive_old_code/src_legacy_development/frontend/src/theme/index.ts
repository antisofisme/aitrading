import { createTheme, Theme, PaletteMode } from '@mui/material/styles';
import { Tenant } from '../types';

// Custom theme interface extending MUI theme
declare module '@mui/material/styles' {
  interface Theme {
    custom: {
      trading: {
        profit: string;
        loss: string;
        neutral: string;
      };
      status: {
        online: string;
        offline: string;
        warning: string;
      };
      charts: {
        grid: string;
        axis: string;
        candleUp: string;
        candleDown: string;
      };
    };
  }

  interface ThemeOptions {
    custom?: {
      trading?: {
        profit?: string;
        loss?: string;
        neutral?: string;
      };
      status?: {
        online?: string;
        offline?: string;
        warning?: string;
      };
      charts?: {
        grid?: string;
        axis?: string;
        candleUp?: string;
        candleDown?: string;
      };
    };
  }

  interface Typography {
    trading: TypographyStyle;
  }

  interface TypographyOptions {
    trading?: TypographyStyleOptions;
  }
}

// Base theme configuration
const baseTheme = {
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 600,
      lineHeight: 1.2,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 600,
      lineHeight: 1.3,
    },
    h3: {
      fontSize: '1.5rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h4: {
      fontSize: '1.25rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h5: {
      fontSize: '1.125rem',
      fontWeight: 600,
      lineHeight: 1.5,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
      lineHeight: 1.5,
    },
    body1: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
    },
    body2: {
      fontSize: '0.75rem',
      lineHeight: 1.43,
    },
    button: {
      textTransform: 'none' as const,
      fontWeight: 500,
    },
    trading: {
      fontFamily: '"JetBrains Mono", "Consolas", "Monaco", monospace',
      fontSize: '0.875rem',
      fontWeight: 500,
      lineHeight: 1.4,
    },
  },
  shape: {
    borderRadius: 8,
  },
  spacing: 8,
};

// Light theme configuration
const lightTheme = createTheme({
  ...baseTheme,
  palette: {
    mode: 'light' as PaletteMode,
    primary: {
      main: '#1976d2',
      light: '#42a5f5',
      dark: '#1565c0',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#9c27b0',
      light: '#ba68c8',
      dark: '#7b1fa2',
      contrastText: '#ffffff',
    },
    error: {
      main: '#d32f2f',
      light: '#ef5350',
      dark: '#c62828',
    },
    warning: {
      main: '#ed6c02',
      light: '#ff9800',
      dark: '#e65100',
    },
    info: {
      main: '#0288d1',
      light: '#03a9f4',
      dark: '#01579b',
    },
    success: {
      main: '#2e7d32',
      light: '#4caf50',
      dark: '#1b5e20',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
    text: {
      primary: 'rgba(0, 0, 0, 0.87)',
      secondary: 'rgba(0, 0, 0, 0.6)',
    },
  },
  custom: {
    trading: {
      profit: '#2e7d32',
      loss: '#d32f2f',
      neutral: '#757575',
    },
    status: {
      online: '#4caf50',
      offline: '#f44336',
      warning: '#ff9800',
    },
    charts: {
      grid: '#e0e0e0',
      axis: '#9e9e9e',
      candleUp: '#2e7d32',
      candleDown: '#d32f2f',
    },
  },
});

// Dark theme configuration
const darkTheme = createTheme({
  ...baseTheme,
  palette: {
    mode: 'dark' as PaletteMode,
    primary: {
      main: '#2196f3',
      light: '#64b5f6',
      dark: '#1976d2',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#ce93d8',
      light: '#f3e5f5',
      dark: '#ab47bc',
      contrastText: '#000000',
    },
    error: {
      main: '#f44336',
      light: '#e57373',
      dark: '#d32f2f',
    },
    warning: {
      main: '#ff9800',
      light: '#ffb74d',
      dark: '#f57c00',
    },
    info: {
      main: '#2196f3',
      light: '#64b5f6',
      dark: '#1976d2',
    },
    success: {
      main: '#4caf50',
      light: '#81c784',
      dark: '#388e3c',
    },
    background: {
      default: '#0a0a0a',
      paper: '#1a1a1a',
    },
    text: {
      primary: '#ffffff',
      secondary: 'rgba(255, 255, 255, 0.7)',
    },
  },
  custom: {
    trading: {
      profit: '#4caf50',
      loss: '#f44336',
      neutral: '#9e9e9e',
    },
    status: {
      online: '#4caf50',
      offline: '#f44336',
      warning: '#ff9800',
    },
    charts: {
      grid: '#333333',
      axis: '#666666',
      candleUp: '#4caf50',
      candleDown: '#f44336',
    },
  },
});

// Component overrides for both themes
const createComponentOverrides = (theme: Theme) => ({
  MuiCssBaseline: {
    styleOverrides: {
      body: {
        scrollbarWidth: 'thin',
        scrollbarColor: `${theme.palette.divider} ${theme.palette.background.paper}`,
        '&::-webkit-scrollbar, & *::-webkit-scrollbar': {
          width: 8,
          height: 8,
        },
        '&::-webkit-scrollbar-thumb, & *::-webkit-scrollbar-thumb': {
          borderRadius: 8,
          backgroundColor: theme.palette.divider,
          minHeight: 24,
        },
        '&::-webkit-scrollbar-track, & *::-webkit-scrollbar-track': {
          borderRadius: 8,
          backgroundColor: theme.palette.background.paper,
        },
      },
    },
  },
  MuiCard: {
    styleOverrides: {
      root: {
        borderRadius: 12,
        boxShadow: theme.palette.mode === 'light'
          ? '0 2px 8px rgba(0,0,0,0.1)'
          : '0 2px 8px rgba(0,0,0,0.3)',
        '&:hover': {
          boxShadow: theme.palette.mode === 'light'
            ? '0 4px 16px rgba(0,0,0,0.15)'
            : '0 4px 16px rgba(0,0,0,0.4)',
        },
        transition: 'box-shadow 0.2s ease-in-out',
      },
    },
  },
  MuiButton: {
    styleOverrides: {
      root: {
        borderRadius: 8,
        textTransform: 'none',
        fontWeight: 500,
        padding: '8px 16px',
      },
      contained: {
        boxShadow: 'none',
        '&:hover': {
          boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
        },
      },
    },
  },
  MuiTextField: {
    defaultProps: {
      variant: 'outlined' as const,
      size: 'small' as const,
    },
    styleOverrides: {
      root: {
        '& .MuiOutlinedInput-root': {
          borderRadius: 8,
        },
      },
    },
  },
  MuiDataGrid: {
    styleOverrides: {
      root: {
        border: 'none',
        borderRadius: 12,
        '& .MuiDataGrid-cell': {
          borderBottom: `1px solid ${theme.palette.divider}`,
        },
        '& .MuiDataGrid-columnHeaders': {
          backgroundColor: theme.palette.mode === 'light'
            ? 'rgba(0,0,0,0.02)'
            : 'rgba(255,255,255,0.02)',
          borderBottom: `2px solid ${theme.palette.divider}`,
        },
        '& .profit-row': {
          backgroundColor: theme.palette.mode === 'light'
            ? 'rgba(76, 175, 80, 0.1)'
            : 'rgba(76, 175, 80, 0.15)',
        },
        '& .loss-row': {
          backgroundColor: theme.palette.mode === 'light'
            ? 'rgba(244, 67, 54, 0.1)'
            : 'rgba(244, 67, 54, 0.15)',
        },
      },
    },
  },
  MuiChip: {
    styleOverrides: {
      root: {
        borderRadius: 6,
        fontWeight: 500,
      },
    },
  },
  MuiPaper: {
    styleOverrides: {
      root: {
        borderRadius: 12,
      },
    },
  },
  MuiDrawer: {
    styleOverrides: {
      paper: {
        borderRadius: 0,
        borderRight: `1px solid ${theme.palette.divider}`,
      },
    },
  },
  MuiAppBar: {
    styleOverrides: {
      root: {
        boxShadow: 'none',
        borderBottom: `1px solid ${theme.palette.divider}`,
        backgroundColor: theme.palette.background.paper,
        color: theme.palette.text.primary,
      },
    },
  },
});

// Create themed components
export const createTradingTheme = (mode: PaletteMode, tenant?: Tenant): Theme => {
  const baseThemeConfig = mode === 'light' ? lightTheme : darkTheme;

  // Apply tenant branding if available
  let customizedTheme = baseThemeConfig;

  if (tenant?.branding) {
    customizedTheme = createTheme({
      ...baseThemeConfig,
      palette: {
        ...baseThemeConfig.palette,
        primary: {
          ...baseThemeConfig.palette.primary,
          main: tenant.branding.primaryColor || baseThemeConfig.palette.primary.main,
        },
        secondary: {
          ...baseThemeConfig.palette.secondary,
          main: tenant.branding.secondaryColor || baseThemeConfig.palette.secondary.main,
        },
      },
    });
  }

  // Apply component overrides
  return createTheme({
    ...customizedTheme,
    components: createComponentOverrides(customizedTheme),
  });
};

// Export default themes
export const lightTradingTheme = createTradingTheme('light');
export const darkTradingTheme = createTradingTheme('dark');

// Theme utility functions
export const getThemeMode = (tenant?: Tenant): PaletteMode => {
  if (tenant?.branding?.theme === 'auto') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  return tenant?.branding?.theme || 'light';
};

export const validateColor = (color: string): boolean => {
  const hexColorRegex = /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/;
  return hexColorRegex.test(color);
};

export const validateFontFamily = (fontFamily: string): boolean => {
  const safeFonts = [
    'Inter',
    'Roboto',
    'Arial',
    'Helvetica',
    'sans-serif',
    'serif',
    'monospace',
    'JetBrains Mono',
    'Consolas',
    'Monaco'
  ];
  return safeFonts.includes(fontFamily);
};

// Responsive breakpoints
export const breakpoints = {
  xs: 0,
  sm: 768,
  md: 1024,
  lg: 1440,
  xl: 1920,
};

// Common color palettes for trading
export const tradingColors = {
  profit: {
    light: '#2e7d32',
    main: '#4caf50',
    dark: '#1b5e20',
  },
  loss: {
    light: '#d32f2f',
    main: '#f44336',
    dark: '#b71c1c',
  },
  neutral: {
    light: '#757575',
    main: '#9e9e9e',
    dark: '#424242',
  },
  warning: {
    light: '#ff9800',
    main: '#ff8a65',
    dark: '#e65100',
  },
  info: {
    light: '#2196f3',
    main: '#64b5f6',
    dark: '#1976d2',
  },
};

// Export everything
export { baseTheme };
export default createTradingTheme;