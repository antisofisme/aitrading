import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { Tenant, TenantSettings, TenantBranding, SubscriptionTier } from '../types';
import { api } from '../services/api';

// Tenant context interface
interface TenantContextType {
  tenant: Tenant | null;
  isLoading: boolean;
  error: string | null;
  loadTenant: (tenantId: string) => Promise<void>;
  updateTenant: (updates: Partial<Tenant>) => Promise<void>;
  updateSettings: (settings: Partial<TenantSettings>) => Promise<void>;
  updateBranding: (branding: Partial<TenantBranding>) => Promise<void>;
  switchTenant: (tenantId: string) => Promise<void>;
  hasFeature: (feature: string) => boolean;
  canAccess: (requiredTier: SubscriptionTier) => boolean;
  getRemainingLimits: () => { [key: string]: number };
}

// Tenant action types
type TenantAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_TENANT'; payload: Tenant | null }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'UPDATE_TENANT'; payload: Partial<Tenant> }
  | { type: 'UPDATE_SETTINGS'; payload: Partial<TenantSettings> }
  | { type: 'UPDATE_BRANDING'; payload: Partial<TenantBranding> };

// Initial state
interface TenantState {
  tenant: Tenant | null;
  isLoading: boolean;
  error: string | null;
}

const initialState: TenantState = {
  tenant: null,
  isLoading: true,
  error: null,
};

// Tenant reducer
const tenantReducer = (state: TenantState, action: TenantAction): TenantState => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };

    case 'SET_TENANT':
      return {
        ...state,
        tenant: action.payload,
        isLoading: false,
        error: null,
      };

    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
        isLoading: false,
      };

    case 'UPDATE_TENANT':
      return {
        ...state,
        tenant: state.tenant ? { ...state.tenant, ...action.payload } : null,
      };

    case 'UPDATE_SETTINGS':
      return {
        ...state,
        tenant: state.tenant
          ? {
              ...state.tenant,
              settings: { ...state.tenant.settings, ...action.payload },
            }
          : null,
      };

    case 'UPDATE_BRANDING':
      return {
        ...state,
        tenant: state.tenant
          ? {
              ...state.tenant,
              branding: { ...state.tenant.branding, ...action.payload },
            }
          : null,
      };

    default:
      return state;
  }
};

// Multi-tenant security manager
class MultiTenantSecurityManager {
  private tenantValidator = new TenantValidator();
  private featureGate = new FeatureGateManager();
  private auditLogger = new SecurityAuditLogger();

  // Validate tenant access
  async validateTenantAccess(tenantId: string, userId: string) {
    try {
      const response = await api.post('/api/auth/validate-tenant', {
        tenantId,
        userId,
        clientFingerprint: this.getClientFingerprint(),
        timestamp: Date.now(),
      });

      if (!response.data.authorized) {
        this.auditLogger.logUnauthorizedTenantAccess(tenantId, userId);
        throw new Error('Unauthorized tenant access');
      }

      return response.data.tenantContext;
    } catch (error) {
      this.auditLogger.logTenantContextFailure(tenantId, error);
      throw error;
    }
  }

  // Load secure tenant context
  async loadSecureTenantContext(tenantId: string) {
    try {
      const context = await this.validateTenantAccess(tenantId, this.getCurrentUserId());

      // Server-validated feature access
      const features = context.authorizedFeatures; // From server, not client
      const limits = context.resourceLimits; // Server-enforced limits
      const branding = context.safeBrandingData; // Sanitized branding only

      return {
        tenantId: context.tenantId,
        displayName: context.displayName, // Safe for display
        tier: context.tier,
        features: features,
        limits: limits,
        theme: branding.theme,
        logo: branding.logoUrl, // Pre-validated URL
      };
    } catch (error) {
      this.auditLogger.logTenantContextFailure(tenantId, error);
      throw error;
    }
  }

  // Validate feature access with server validation
  async validateFeatureAccess(requiredFeature: string) {
    try {
      const response = await api.get(`/api/tenant/validate-feature/${requiredFeature}`);
      return response.data;
    } catch (error) {
      this.auditLogger.logUnauthorizedFeatureAccess(requiredFeature);
      return { authorized: false };
    }
  }

  private getClientFingerprint(): string {
    return 'client_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  private getCurrentUserId(): string {
    // Get from auth context or storage
    return localStorage.getItem('userId') || 'anonymous';
  }
}

// Security audit logger for tenant operations
class SecurityAuditLogger {
  logUnauthorizedTenantAccess(tenantId: string, userId: string) {
    console.warn(`Unauthorized tenant access attempt: ${userId} -> ${tenantId}`);
    // In production, send to security monitoring
  }

  logTenantContextFailure(tenantId: string, error: any) {
    console.error(`Tenant context failure for ${tenantId}:`, error);
    // In production, send to error monitoring
  }

  logUnauthorizedFeatureAccess(feature: string) {
    console.warn(`Unauthorized feature access attempt: ${feature}`);
    // In production, send to security monitoring
  }
}

// Tenant validator for client-side validation
class TenantValidator {
  validateTenantData(tenant: any): tenant is Tenant {
    return (
      typeof tenant === 'object' &&
      tenant !== null &&
      typeof tenant.id === 'string' &&
      typeof tenant.name === 'string' &&
      typeof tenant.slug === 'string' &&
      this.isValidTier(tenant.tier)
    );
  }

  private isValidTier(tier: any): tier is SubscriptionTier {
    return ['free', 'basic', 'pro', 'enterprise'].includes(tier);
  }
}

// Feature gate manager
class FeatureGateManager {
  private static tierHierarchy = {
    free: 0,
    basic: 1,
    pro: 2,
    enterprise: 3,
  };

  hasFeature(tenant: Tenant | null, feature: string): boolean {
    if (!tenant) return false;

    // Check if feature is in tenant's feature list
    return tenant.features.includes(feature) || tenant.features.includes('all');
  }

  canAccess(tenant: Tenant | null, requiredTier: SubscriptionTier): boolean {
    if (!tenant) return false;

    const currentTierLevel = FeatureGateManager.tierHierarchy[tenant.tier];
    const requiredTierLevel = FeatureGateManager.tierHierarchy[requiredTier];

    return currentTierLevel >= requiredTierLevel;
  }

  getRemainingLimits(tenant: Tenant | null): { [key: string]: number } {
    if (!tenant) return {};

    // In production, this would fetch current usage from API
    // For now, return the limits as remaining
    return {
      users: tenant.limits.maxUsers,
      positions: tenant.limits.maxPositions,
      alerts: tenant.limits.maxAlerts,
      apiCalls: tenant.limits.apiCallsPerMonth,
    };
  }
}

// Utility function to extract tenant ID from URL
const extractTenantFromRoute = (): string | null => {
  // Check subdomain first
  const hostname = window.location.hostname;
  const subdomain = hostname.split('.')[0];

  if (subdomain && !['www', 'app', 'localhost'].includes(subdomain)) {
    return subdomain;
  }

  // Check path segments
  const pathSegments = window.location.pathname.split('/');
  if (pathSegments[1] && pathSegments[1] !== 'auth') {
    return pathSegments[1];
  }

  // Check stored tenant ID
  return localStorage.getItem('tenantId') || null;
};

// Create context
const TenantContext = createContext<TenantContextType | undefined>(undefined);

// Tenant provider component
interface TenantProviderProps {
  children: ReactNode;
}

export const TenantProvider: React.FC<TenantProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(tenantReducer, initialState);
  const securityManager = new MultiTenantSecurityManager();
  const featureGate = new FeatureGateManager();

  // Load tenant on mount
  useEffect(() => {
    const initializeTenant = async () => {
      try {
        const tenantId = extractTenantFromRoute();

        if (tenantId) {
          await loadTenant(tenantId);
        } else {
          dispatch({ type: 'SET_ERROR', payload: 'No tenant specified' });
        }
      } catch (error: any) {
        console.error('Tenant initialization failed:', error);
        dispatch({ type: 'SET_ERROR', payload: error.message });
      }
    };

    initializeTenant();
  }, []);

  // Load tenant data
  const loadTenant = async (tenantId: string) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });

      const response = await api.get(`/api/tenant/${tenantId}`);

      if (response.success && response.data) {
        // Validate tenant data
        const validator = new TenantValidator();
        if (!validator.validateTenantData(response.data)) {
          throw new Error('Invalid tenant data received');
        }

        dispatch({ type: 'SET_TENANT', payload: response.data });

        // Store tenant ID for future use
        localStorage.setItem('tenantId', tenantId);
      } else {
        throw new Error(response.message || 'Failed to load tenant');
      }
    } catch (error: any) {
      console.error('Failed to load tenant:', error);
      dispatch({ type: 'SET_ERROR', payload: error.message });
    }
  };

  // Update tenant data
  const updateTenant = async (updates: Partial<Tenant>) => {
    try {
      if (!state.tenant) {
        throw new Error('No tenant loaded');
      }

      const response = await api.put(`/api/tenant/${state.tenant.id}`, updates);

      if (response.success && response.data) {
        dispatch({ type: 'UPDATE_TENANT', payload: response.data });
      } else {
        throw new Error(response.message || 'Failed to update tenant');
      }
    } catch (error: any) {
      console.error('Failed to update tenant:', error);
      throw error;
    }
  };

  // Update tenant settings
  const updateSettings = async (settings: Partial<TenantSettings>) => {
    try {
      if (!state.tenant) {
        throw new Error('No tenant loaded');
      }

      const response = await api.put(`/api/tenant/${state.tenant.id}/settings`, settings);

      if (response.success && response.data) {
        dispatch({ type: 'UPDATE_SETTINGS', payload: response.data });
      } else {
        throw new Error(response.message || 'Failed to update settings');
      }
    } catch (error: any) {
      console.error('Failed to update settings:', error);
      throw error;
    }
  };

  // Update tenant branding
  const updateBranding = async (branding: Partial<TenantBranding>) => {
    try {
      if (!state.tenant) {
        throw new Error('No tenant loaded');
      }

      // Validate branding data on client side
      const validatedBranding = validateBranding(branding);

      const response = await api.put(`/api/tenant/${state.tenant.id}/branding`, validatedBranding);

      if (response.success && response.data) {
        dispatch({ type: 'UPDATE_BRANDING', payload: response.data });
      } else {
        throw new Error(response.message || 'Failed to update branding');
      }
    } catch (error: any) {
      console.error('Failed to update branding:', error);
      throw error;
    }
  };

  // Switch to different tenant
  const switchTenant = async (tenantId: string) => {
    try {
      // Clear current tenant
      dispatch({ type: 'SET_TENANT', payload: null });

      // Load new tenant
      await loadTenant(tenantId);

      // Update URL if needed
      const currentTenantId = extractTenantFromRoute();
      if (currentTenantId !== tenantId) {
        // In a real app, you might want to redirect or update the URL
        window.history.pushState(null, '', `/${tenantId}${window.location.pathname.replace(`/${currentTenantId}`, '')}`);
      }
    } catch (error: any) {
      console.error('Failed to switch tenant:', error);
      throw error;
    }
  };

  // Check if tenant has specific feature
  const hasFeature = (feature: string): boolean => {
    return featureGate.hasFeature(state.tenant, feature);
  };

  // Check if tenant can access specific tier features
  const canAccess = (requiredTier: SubscriptionTier): boolean => {
    return featureGate.canAccess(state.tenant, requiredTier);
  };

  // Get remaining limits
  const getRemainingLimits = (): { [key: string]: number } => {
    return featureGate.getRemainingLimits(state.tenant);
  };

  // Validate branding data
  const validateBranding = (branding: Partial<TenantBranding>): Partial<TenantBranding> => {
    const validated: Partial<TenantBranding> = {};

    // Validate colors
    if (branding.primaryColor && validateColor(branding.primaryColor)) {
      validated.primaryColor = branding.primaryColor;
    }

    if (branding.secondaryColor && validateColor(branding.secondaryColor)) {
      validated.secondaryColor = branding.secondaryColor;
    }

    // Validate theme
    if (branding.theme && ['light', 'dark', 'auto'].includes(branding.theme)) {
      validated.theme = branding.theme;
    }

    // Validate URLs (basic validation)
    if (branding.logo && validateUrl(branding.logo)) {
      validated.logo = branding.logo;
    }

    if (branding.favicon && validateUrl(branding.favicon)) {
      validated.favicon = branding.favicon;
    }

    return validated;
  };

  const validateColor = (color: string): boolean => {
    const hexColorRegex = /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/;
    return hexColorRegex.test(color);
  };

  const validateUrl = (url: string): boolean => {
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  };

  const value: TenantContextType = {
    ...state,
    loadTenant,
    updateTenant,
    updateSettings,
    updateBranding,
    switchTenant,
    hasFeature,
    canAccess,
    getRemainingLimits,
  };

  return <TenantContext.Provider value={value}>{children}</TenantContext.Provider>;
};

// Hook to use tenant context
export const useTenant = (): TenantContextType => {
  const context = useContext(TenantContext);
  if (context === undefined) {
    throw new Error('useTenant must be used within a TenantProvider');
  }
  return context;
};

// Feature gate component for conditional rendering
interface FeatureGateProps {
  feature: string;
  children: ReactNode;
  fallback?: ReactNode;
}

export const FeatureGate: React.FC<FeatureGateProps> = ({ feature, children, fallback = null }) => {
  const { hasFeature } = useTenant();

  return hasFeature(feature) ? <>{children}</> : <>{fallback}</>;
};

// Tier gate component for tier-based access
interface TierGateProps {
  requiredTier: SubscriptionTier;
  children: ReactNode;
  fallback?: ReactNode;
}

export const TierGate: React.FC<TierGateProps> = ({ requiredTier, children, fallback = null }) => {
  const { canAccess } = useTenant();

  return canAccess(requiredTier) ? <>{children}</> : <>{fallback}</>;
};

// Export context for advanced usage
export { TenantContext };