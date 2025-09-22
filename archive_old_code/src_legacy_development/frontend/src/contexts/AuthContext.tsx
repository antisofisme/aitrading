import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { AuthState, User, LoginCredentials, RegisterData } from '../types';
import { api, setTokens, clearTokens, API_ENDPOINTS } from '../services/api';

// Auth context interface
interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<{ success: boolean; message?: string; requires2FA?: boolean }>;
  register: (data: RegisterData) => Promise<{ success: boolean; message?: string }>;
  logout: () => Promise<void>;
  verifyEmail: (token: string) => Promise<{ success: boolean; message?: string }>;
  resetPassword: (email: string) => Promise<{ success: boolean; message?: string }>;
  updatePassword: (token: string, newPassword: string) => Promise<{ success: boolean; message?: string }>;
  updateProfile: (data: Partial<User>) => Promise<{ success: boolean; message?: string }>;
  checkAuth: () => Promise<void>;
}

// Auth action types
type AuthAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_USER'; payload: User | null }
  | { type: 'SET_TOKEN'; payload: string | null }
  | { type: 'LOGIN_SUCCESS'; payload: { user: User; token: string } }
  | { type: 'LOGOUT' }
  | { type: 'AUTH_ERROR'; payload: string };

// Initial state
const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
  token: null,
};

// Auth reducer
const authReducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };

    case 'SET_USER':
      return {
        ...state,
        user: action.payload,
        isAuthenticated: !!action.payload,
        isLoading: false,
      };

    case 'SET_TOKEN':
      return { ...state, token: action.payload };

    case 'LOGIN_SUCCESS':
      return {
        ...state,
        user: action.payload.user,
        token: action.payload.token,
        isAuthenticated: true,
        isLoading: false,
      };

    case 'LOGOUT':
      return {
        ...initialState,
        isLoading: false,
      };

    case 'AUTH_ERROR':
      return {
        ...state,
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
      };

    default:
      return state;
  }
};

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Security audit logger
class SecurityAuditLogger {
  private auditQueue: any[] = [];
  private flushInterval = 10000; // 10 seconds

  constructor() {
    this.startAuditFlush();
  }

  logSecurityEvent(eventType: string, details: any, severity: 'INFO' | 'WARNING' | 'CRITICAL' = 'INFO') {
    const event = {
      type: eventType,
      details: this.sanitizeLogData(details),
      severity,
      timestamp: Date.now(),
      sessionId: this.getSessionId(),
      userAgent: navigator.userAgent,
      url: window.location.href,
    };

    this.auditQueue.push(event);

    // Immediate flush for critical events
    if (severity === 'CRITICAL') {
      this.flushAuditLogs();
    }

    // Prevent queue overflow
    if (this.auditQueue.length > 100) {
      this.auditQueue = this.auditQueue.slice(-100);
    }
  }

  private sanitizeLogData(details: any): any {
    // Remove sensitive information from logs
    const sanitized = { ...details };
    delete sanitized.password;
    delete sanitized.token;
    delete sanitized.secret;
    return sanitized;
  }

  private getSessionId(): string {
    return sessionStorage.getItem('sessionId') || 'anonymous';
  }

  private async flushAuditLogs() {
    if (this.auditQueue.length === 0) return;

    try {
      await api.post('/api/security/audit', {
        events: this.auditQueue.splice(0),
      });
    } catch (error) {
      console.error('Failed to flush audit logs:', error);
    }
  }

  private startAuditFlush() {
    setInterval(() => {
      this.flushAuditLogs();
    }, this.flushInterval);
  }
}

const auditLogger = new SecurityAuditLogger();

// Auth provider component
interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Check authentication on mount
  useEffect(() => {
    checkAuth();
  }, []);

  // Setup automatic token cleanup on browser close
  useEffect(() => {
    const handleBeforeUnload = () => {
      // Clear tokens from memory on browser close
      clearTokens();
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, []);

  // Check authentication status
  const checkAuth = async () => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });

      const response = await api.get(API_ENDPOINTS.AUTH.PROFILE);

      if (response.success && response.data) {
        dispatch({ type: 'SET_USER', payload: response.data });
        auditLogger.logSecurityEvent('AUTH_CHECK_SUCCESS', { userId: response.data.id });
      } else {
        dispatch({ type: 'AUTH_ERROR', payload: 'Authentication check failed' });
      }
    } catch (error: any) {
      console.error('Auth check failed:', error);
      dispatch({ type: 'AUTH_ERROR', payload: error.message });
      auditLogger.logSecurityEvent('AUTH_CHECK_FAILED', { error: error.message }, 'WARNING');
    }
  };

  // Login function
  const login = async (credentials: LoginCredentials) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });

      // Input validation
      if (!credentials.email || !credentials.password) {
        throw new Error('Email and password are required');
      }

      // Email format validation
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(credentials.email)) {
        throw new Error('Invalid email format');
      }

      const response = await api.post(API_ENDPOINTS.AUTH.LOGIN, {
        email: credentials.email.toLowerCase().trim(),
        password: credentials.password,
        rememberMe: credentials.rememberMe || false,
        clientFingerprint: generateClientFingerprint(),
        timestamp: Date.now(),
      });

      if (response.success) {
        // Check for 2FA requirement
        if (response.data.requires2FA) {
          auditLogger.logSecurityEvent('LOGIN_2FA_REQUIRED', { email: credentials.email });
          return {
            success: false,
            requires2FA: true,
            message: 'Two-factor authentication required',
          };
        }

        // Successful login
        const { user, accessToken, refreshToken } = response.data;

        // Store tokens securely
        setTokens(accessToken, refreshToken);

        dispatch({
          type: 'LOGIN_SUCCESS',
          payload: { user, token: accessToken },
        });

        auditLogger.logSecurityEvent('LOGIN_SUCCESS', {
          userId: user.id,
          tenantId: user.tenant?.id,
        });

        return { success: true };
      } else {
        auditLogger.logSecurityEvent('LOGIN_FAILED', {
          email: credentials.email,
          reason: response.message,
        }, 'WARNING');

        return {
          success: false,
          message: response.message || 'Login failed',
        };
      }
    } catch (error: any) {
      dispatch({ type: 'AUTH_ERROR', payload: error.message });
      auditLogger.logSecurityEvent('LOGIN_ERROR', {
        email: credentials.email,
        error: error.message,
      }, 'CRITICAL');

      return {
        success: false,
        message: error.message || 'Login failed',
      };
    }
  };

  // Register function
  const register = async (data: RegisterData) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });

      // Input validation
      if (!data.email || !data.password || !data.name) {
        throw new Error('All required fields must be filled');
      }

      if (!data.acceptTerms) {
        throw new Error('You must accept the terms and conditions');
      }

      // Password strength validation
      if (data.password.length < 8) {
        throw new Error('Password must be at least 8 characters long');
      }

      const response = await api.post(API_ENDPOINTS.AUTH.REGISTER, {
        email: data.email.toLowerCase().trim(),
        password: data.password,
        name: data.name.trim(),
        companyName: data.companyName?.trim(),
        acceptTerms: data.acceptTerms,
        clientFingerprint: generateClientFingerprint(),
        timestamp: Date.now(),
      });

      if (response.success) {
        auditLogger.logSecurityEvent('REGISTER_SUCCESS', {
          email: data.email,
          name: data.name,
        });

        return {
          success: true,
          message: response.message || 'Registration successful. Please check your email for verification.',
        };
      } else {
        auditLogger.logSecurityEvent('REGISTER_FAILED', {
          email: data.email,
          reason: response.message,
        }, 'WARNING');

        return {
          success: false,
          message: response.message || 'Registration failed',
        };
      }
    } catch (error: any) {
      dispatch({ type: 'AUTH_ERROR', payload: error.message });
      auditLogger.logSecurityEvent('REGISTER_ERROR', {
        email: data.email,
        error: error.message,
      }, 'CRITICAL');

      return {
        success: false,
        message: error.message || 'Registration failed',
      };
    }
  };

  // Logout function
  const logout = async () => {
    try {
      // Notify server of logout
      await api.post(API_ENDPOINTS.AUTH.LOGOUT);
    } catch (error) {
      console.error('Logout API call failed:', error);
    } finally {
      // Always clean up client state
      clearTokens();
      dispatch({ type: 'LOGOUT' });

      // Clear sensitive data from storage
      sessionStorage.clear();
      localStorage.removeItem('tenantId');

      auditLogger.logSecurityEvent('LOGOUT', {
        userId: state.user?.id,
      });
    }
  };

  // Verify email function
  const verifyEmail = async (token: string) => {
    try {
      const response = await api.post(API_ENDPOINTS.AUTH.VERIFY_EMAIL, { token });

      if (response.success) {
        auditLogger.logSecurityEvent('EMAIL_VERIFIED', { token: token.substring(0, 8) + '...' });
        return { success: true, message: 'Email verified successfully' };
      } else {
        return { success: false, message: response.message || 'Email verification failed' };
      }
    } catch (error: any) {
      auditLogger.logSecurityEvent('EMAIL_VERIFY_ERROR', { error: error.message }, 'WARNING');
      return { success: false, message: error.message || 'Email verification failed' };
    }
  };

  // Reset password function
  const resetPassword = async (email: string) => {
    try {
      const response = await api.post(API_ENDPOINTS.AUTH.RESET_PASSWORD, {
        email: email.toLowerCase().trim(),
        clientFingerprint: generateClientFingerprint(),
      });

      if (response.success) {
        auditLogger.logSecurityEvent('PASSWORD_RESET_REQUESTED', { email });
        return { success: true, message: 'Password reset instructions sent to your email' };
      } else {
        return { success: false, message: response.message || 'Password reset failed' };
      }
    } catch (error: any) {
      auditLogger.logSecurityEvent('PASSWORD_RESET_ERROR', { email, error: error.message }, 'WARNING');
      return { success: false, message: error.message || 'Password reset failed' };
    }
  };

  // Update password function
  const updatePassword = async (token: string, newPassword: string) => {
    try {
      // Password strength validation
      if (newPassword.length < 8) {
        throw new Error('Password must be at least 8 characters long');
      }

      const response = await api.post(API_ENDPOINTS.AUTH.UPDATE_PASSWORD, {
        token,
        newPassword,
        clientFingerprint: generateClientFingerprint(),
      });

      if (response.success) {
        auditLogger.logSecurityEvent('PASSWORD_UPDATED', { token: token.substring(0, 8) + '...' });
        return { success: true, message: 'Password updated successfully' };
      } else {
        return { success: false, message: response.message || 'Password update failed' };
      }
    } catch (error: any) {
      auditLogger.logSecurityEvent('PASSWORD_UPDATE_ERROR', { error: error.message }, 'WARNING');
      return { success: false, message: error.message || 'Password update failed' };
    }
  };

  // Update profile function
  const updateProfile = async (data: Partial<User>) => {
    try {
      const response = await api.put(API_ENDPOINTS.AUTH.PROFILE, data);

      if (response.success && response.data) {
        dispatch({ type: 'SET_USER', payload: response.data });
        auditLogger.logSecurityEvent('PROFILE_UPDATED', { userId: response.data.id });
        return { success: true, message: 'Profile updated successfully' };
      } else {
        return { success: false, message: response.message || 'Profile update failed' };
      }
    } catch (error: any) {
      auditLogger.logSecurityEvent('PROFILE_UPDATE_ERROR', { error: error.message }, 'WARNING');
      return { success: false, message: error.message || 'Profile update failed' };
    }
  };

  // Generate client fingerprint for security
  const generateClientFingerprint = (): string => {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    ctx?.fillText('Fingerprint', 10, 10);

    const fingerprint = {
      userAgent: navigator.userAgent,
      language: navigator.language,
      platform: navigator.platform,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      screen: `${screen.width}x${screen.height}`,
      canvas: canvas.toDataURL(),
      timestamp: Date.now(),
    };

    return btoa(JSON.stringify(fingerprint)).substring(0, 32);
  };

  const value: AuthContextType = {
    ...state,
    login,
    register,
    logout,
    verifyEmail,
    resetPassword,
    updatePassword,
    updateProfile,
    checkAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Hook to use auth context
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Export context for advanced usage
export { AuthContext };