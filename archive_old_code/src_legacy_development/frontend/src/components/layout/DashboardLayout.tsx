import React, { useState, ReactNode } from 'react';
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Avatar,
  Menu,
  MenuItem,
  Divider,
  Badge,
  useTheme,
  useMediaQuery,
  Tooltip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard,
  TrendingUp,
  Settings,
  Notifications,
  User,
  LogOut,
  ChevronLeft,
  Bell,
  BrainCircuit,
  BarChart3,
  CreditCard,
  Shield,
  Wifi,
  WifiOff,
} from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useTenant } from '../../contexts/TenantContext';
import { StatusIndicator } from '../ui/StatusIndicator';
import { LoadingSpinner } from '../ui/LoadingSpinner';

interface DashboardLayoutProps {
  children: ReactNode;
}

interface NavigationItem {
  id: string;
  label: string;
  icon: React.ComponentType<any>;
  path: string;
  requireFeature?: string;
  badge?: number;
}

const DRAWER_WIDTH = 280;

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const { tenant, hasFeature } = useTenant();
  const isDesktop = useMediaQuery(theme.breakpoints.up('md'));

  const [drawerOpen, setDrawerOpen] = useState(isDesktop);
  const [userMenuAnchor, setUserMenuAnchor] = useState<null | HTMLElement>(null);
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  // Navigation items
  const navigationItems: NavigationItem[] = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: Dashboard,
      path: '/dashboard',
    },
    {
      id: 'trading',
      label: 'Trading',
      icon: TrendingUp,
      path: '/trading',
    },
    {
      id: 'analytics',
      label: 'Analytics',
      icon: BarChart3,
      path: '/analytics',
      requireFeature: 'advanced_analytics',
    },
    {
      id: 'ai-insights',
      label: 'AI Insights',
      icon: BrainCircuit,
      path: '/ai-insights',
      requireFeature: 'ai_insights',
    },
    {
      id: 'notifications',
      label: 'Notifications',
      icon: Bell,
      path: '/notifications',
      badge: 3, // This would come from a notifications context
    },
    {
      id: 'subscription',
      label: 'Subscription',
      icon: CreditCard,
      path: '/subscription',
    },
    {
      id: 'settings',
      label: 'Settings',
      icon: Settings,
      path: '/settings',
    },
  ];

  // Filter navigation items based on features
  const filteredNavigationItems = navigationItems.filter(item => {
    if (item.requireFeature) {
      return hasFeature(item.requireFeature);
    }
    return true;
  });

  // Handle online/offline status
  React.useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const handleDrawerToggle = () => {
    setDrawerOpen(!drawerOpen);
  };

  const handleUserMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setUserMenuAnchor(event.currentTarget);
  };

  const handleUserMenuClose = () => {
    setUserMenuAnchor(null);
  };

  const handleNavigation = (path: string) => {
    navigate(path);
    if (!isDesktop) {
      setDrawerOpen(false);
    }
  };

  const handleLogout = async () => {
    handleUserMenuClose();
    await logout();
    navigate('/auth/login');
  };

  // Loading state
  if (!user || !tenant) {
    return <LoadingSpinner fullScreen message="Loading dashboard..." />;
  }

  const drawerContent = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Tenant Branding Header */}
      <Box
        sx={{
          p: 2,
          background: `linear-gradient(135deg, ${tenant.branding.primaryColor || theme.palette.primary.main}, ${tenant.branding.secondaryColor || theme.palette.secondary.main})`,
          color: 'white',
          textAlign: 'center',
        }}
      >
        {tenant.branding.logo ? (
          <img
            src={tenant.branding.logo}
            alt={tenant.name}
            style={{ height: 40, marginBottom: 8 }}
          />
        ) : (
          <Typography variant="h5" fontWeight={600}>
            {tenant.name}
          </Typography>
        )}
        <Typography variant="caption" sx={{ opacity: 0.9 }}>
          {tenant.tier.charAt(0).toUpperCase() + tenant.tier.slice(1)} Plan
        </Typography>
      </Box>

      {/* Navigation Items */}
      <List sx={{ flex: 1, p: 1 }}>
        {filteredNavigationItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;

          return (
            <ListItem key={item.id} disablePadding sx={{ mb: 0.5 }}>
              <ListItemButton
                onClick={() => handleNavigation(item.path)}
                sx={{
                  borderRadius: 2,
                  mx: 1,
                  backgroundColor: isActive ? theme.palette.primary.main : 'transparent',
                  color: isActive ? 'white' : 'inherit',
                  '&:hover': {
                    backgroundColor: isActive
                      ? theme.palette.primary.dark
                      : theme.palette.action.hover,
                  },
                }}
              >
                <ListItemIcon
                  sx={{
                    color: isActive ? 'white' : theme.palette.text.secondary,
                    minWidth: 40,
                  }}
                >
                  {item.badge ? (
                    <Badge badgeContent={item.badge} color="error">
                      <Icon size={20} />
                    </Badge>
                  ) : (
                    <Icon size={20} />
                  )}
                </ListItemIcon>
                <ListItemText
                  primary={item.label}
                  primaryTypographyProps={{
                    fontSize: '0.875rem',
                    fontWeight: isActive ? 600 : 400,
                  }}
                />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>

      {/* Connection Status */}
      <Box sx={{ p: 2, borderTop: `1px solid ${theme.palette.divider}` }}>
        <StatusIndicator
          status={isOnline ? 'online' : 'offline'}
          label={isOnline ? 'Connected' : 'Offline'}
          variant="dot"
          size="small"
        />
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      {/* App Bar */}
      <AppBar
        position="fixed"
        sx={{
          zIndex: theme.zIndex.drawer + 1,
          backgroundColor: theme.palette.background.paper,
          color: theme.palette.text.primary,
          boxShadow: 'none',
          borderBottom: `1px solid ${theme.palette.divider}`,
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2 }}
          >
            {drawerOpen ? <ChevronLeft /> : <MenuIcon />}
          </IconButton>

          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            AI Trading Platform
          </Typography>

          {/* Connection Status */}
          <Box sx={{ mr: 2 }}>
            <Tooltip title={isOnline ? "Connected" : "Offline"}>
              <Box>
                {isOnline ? (
                  <Wifi size={20} style={{ color: theme.palette.success.main }} />
                ) : (
                  <WifiOff size={20} style={{ color: theme.palette.error.main }} />
                )}
              </Box>
            </Tooltip>
          </Box>

          {/* Notifications */}
          <IconButton color="inherit" sx={{ mr: 1 }}>
            <Badge badgeContent={3} color="error">
              <Notifications size={20} />
            </Badge>
          </IconButton>

          {/* User Menu */}
          <IconButton
            color="inherit"
            onClick={handleUserMenuOpen}
            sx={{ p: 0.5 }}
          >
            <Avatar
              src={user.avatar}
              alt={user.name}
              sx={{ width: 32, height: 32 }}
            >
              {user.name.charAt(0).toUpperCase()}
            </Avatar>
          </IconButton>

          <Menu
            anchorEl={userMenuAnchor}
            open={Boolean(userMenuAnchor)}
            onClose={handleUserMenuClose}
            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          >
            <MenuItem onClick={handleUserMenuClose}>
              <Box display="flex" flexDirection="column" alignItems="flex-start">
                <Typography variant="subtitle2">{user.name}</Typography>
                <Typography variant="caption" color="text.secondary">
                  {user.email}
                </Typography>
              </Box>
            </MenuItem>
            <Divider />
            <MenuItem onClick={() => { handleUserMenuClose(); navigate('/profile'); }}>
              <ListItemIcon>
                <User size={16} />
              </ListItemIcon>
              Profile
            </MenuItem>
            <MenuItem onClick={() => { handleUserMenuClose(); navigate('/security'); }}>
              <ListItemIcon>
                <Shield size={16} />
              </ListItemIcon>
              Security
            </MenuItem>
            <Divider />
            <MenuItem onClick={handleLogout}>
              <ListItemIcon>
                <LogOut size={16} />
              </ListItemIcon>
              Logout
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

      {/* Drawer */}
      <Drawer
        variant={isDesktop ? "persistent" : "temporary"}
        open={drawerOpen}
        onClose={handleDrawerToggle}
        sx={{
          width: DRAWER_WIDTH,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: DRAWER_WIDTH,
            boxSizing: 'border-box',
            borderRight: `1px solid ${theme.palette.divider}`,
          },
        }}
        ModalProps={{
          keepMounted: true, // Better open performance on mobile
        }}
      >
        <Toolbar /> {/* Spacer for app bar */}
        {drawerContent}
      </Drawer>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          bgcolor: theme.palette.background.default,
          transition: theme.transitions.create('margin', {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
          marginLeft: isDesktop && drawerOpen ? 0 : `-${DRAWER_WIDTH}px`,
          height: '100vh',
          overflow: 'auto',
        }}
      >
        <Toolbar /> {/* Spacer for app bar */}
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      </Box>
    </Box>
  );
};

export default DashboardLayout;