import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Checkbox,
  FormControlLabel,
  Link,
  Alert,
  Divider,
  CircularProgress,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import { Eye, EyeOff, Shield, Lock, Mail } from 'lucide-react';
import { useNavigate, useLocation, Link as RouterLink } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useTenant } from '../../contexts/TenantContext';
import { LoginCredentials } from '../../types';

interface LocationState {
  from?: {
    pathname: string;
  };
}

export const LoginPage: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isLoading } = useAuth();
  const { tenant } = useTenant();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const [formData, setFormData] = useState<LoginCredentials>({
    email: '',
    password: '',
    rememberMe: false,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<{ [key: string]: string }>({});
  const [submitError, setSubmitError] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Get redirect location
  const from = (location.state as LocationState)?.from?.pathname || '/dashboard';

  // Clear errors when form data changes
  useEffect(() => {
    if (errors.email && formData.email) setErrors(prev => ({ ...prev, email: '' }));
    if (errors.password && formData.password) setErrors(prev => ({ ...prev, password: '' }));
    if (submitError) setSubmitError('');
  }, [formData.email, formData.password, errors.email, errors.password, submitError]);

  // Form validation
  const validateForm = (): boolean => {
    const newErrors: { [key: string]: string } = {};

    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters long';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError('');

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      const result = await login(formData);

      if (result.success) {
        // Successful login
        navigate(from, { replace: true });
      } else if (result.requires2FA) {
        // Redirect to 2FA page
        navigate('/auth/2fa', {
          state: { email: formData.email },
        });
      } else {
        // Login failed
        setSubmitError(result.message || 'Login failed. Please try again.');
      }
    } catch (error: any) {
      setSubmitError(error.message || 'An unexpected error occurred. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle input changes
  const handleInputChange = (field: keyof LoginCredentials) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = field === 'rememberMe' ? e.target.checked : e.target.value;
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  // Get tenant branding
  const brandingColors = {
    primary: tenant?.branding?.primaryColor || theme.palette.primary.main,
    secondary: tenant?.branding?.secondaryColor || theme.palette.secondary.main,
  };

  return (
    <Box
      minHeight="100vh"
      display="flex"
      alignItems="center"
      justifyContent="center"
      sx={{
        background: `linear-gradient(135deg, ${brandingColors.primary}15, ${brandingColors.secondary}15)`,
        p: 2,
      }}
    >
      <Card
        sx={{
          maxWidth: 440,
          width: '100%',
          boxShadow: theme.shadows[8],
          borderRadius: 3,
        }}
      >
        <CardContent sx={{ p: 4 }}>
          {/* Header */}
          <Box textAlign="center" mb={4}>
            {tenant?.branding?.logo ? (
              <img
                src={tenant.branding.logo}
                alt={tenant.name}
                style={{ height: 48, marginBottom: 16 }}
              />
            ) : (
              <Box
                mb={2}
                display="flex"
                alignItems="center"
                justifyContent="center"
                gap={1}
              >
                <Shield size={32} style={{ color: brandingColors.primary }} />
                <Typography variant="h4" fontWeight={700} color={brandingColors.primary}>
                  AI Trading
                </Typography>
              </Box>
            )}

            <Typography variant="h5" fontWeight={600} gutterBottom>
              Welcome Back
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Sign in to your {tenant?.name || 'AI Trading'} account
            </Typography>
          </Box>

          {/* Error Alert */}
          {submitError && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {submitError}
            </Alert>
          )}

          {/* Login Form */}
          <Box component="form" onSubmit={handleSubmit}>
            {/* Email Field */}
            <TextField
              fullWidth
              label="Email Address"
              type="email"
              value={formData.email}
              onChange={handleInputChange('email')}
              error={!!errors.email}
              helperText={errors.email}
              margin="normal"
              disabled={isSubmitting}
              InputProps={{
                startAdornment: (
                  <Mail size={20} style={{ marginRight: 8, color: theme.palette.text.secondary }} />
                ),
              }}
              sx={{ mb: 2 }}
            />

            {/* Password Field */}
            <TextField
              fullWidth
              label="Password"
              type={showPassword ? 'text' : 'password'}
              value={formData.password}
              onChange={handleInputChange('password')}
              error={!!errors.password}
              helperText={errors.password}
              margin="normal"
              disabled={isSubmitting}
              InputProps={{
                startAdornment: (
                  <Lock size={20} style={{ marginRight: 8, color: theme.palette.text.secondary }} />
                ),
                endAdornment: (
                  <Button
                    size="small"
                    onClick={() => setShowPassword(!showPassword)}
                    sx={{ minWidth: 'auto', p: 1 }}
                    disabled={isSubmitting}
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </Button>
                ),
              }}
              sx={{ mb: 1 }}
            />

            {/* Remember Me & Forgot Password */}
            <Box
              display="flex"
              justifyContent="space-between"
              alignItems="center"
              mb={3}
            >
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.rememberMe}
                    onChange={handleInputChange('rememberMe')}
                    disabled={isSubmitting}
                    size="small"
                  />
                }
                label={
                  <Typography variant="body2">
                    Remember me
                  </Typography>
                }
              />

              <Link
                component={RouterLink}
                to="/auth/forgot-password"
                variant="body2"
                color="primary"
                underline="hover"
              >
                Forgot password?
              </Link>
            </Box>

            {/* Submit Button */}
            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              disabled={isSubmitting || isLoading}
              sx={{
                mb: 3,
                py: 1.5,
                backgroundColor: brandingColors.primary,
                '&:hover': {
                  backgroundColor: `${brandingColors.primary}dd`,
                },
              }}
            >
              {isSubmitting || isLoading ? (
                <Box display="flex" alignItems="center" gap={1}>
                  <CircularProgress size={20} color="inherit" />
                  Signing In...
                </Box>
              ) : (
                'Sign In'
              )}
            </Button>

            {/* Divider */}
            <Divider sx={{ mb: 3 }}>
              <Typography variant="caption" color="text.secondary">
                or
              </Typography>
            </Divider>

            {/* Social Login Options */}
            <Box display="flex" gap={2} mb={3}>
              <Button
                fullWidth
                variant="outlined"
                disabled={isSubmitting}
                sx={{ py: 1.5 }}
              >
                <img
                  src="https://developers.google.com/identity/images/g-logo.png"
                  alt="Google"
                  style={{ width: 20, height: 20, marginRight: 8 }}
                />
                Google
              </Button>

              <Button
                fullWidth
                variant="outlined"
                disabled={isSubmitting}
                sx={{ py: 1.5 }}
              >
                <Box
                  component="img"
                  src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iIzAwMDAwMCI+PHBhdGggZD0iTTI0IDEyLjA3M2MwLTYuNjI3LTUuMzczLTEyLTEyLTEycy0xMiA1LjM3My0xMiAxMmMwIDUuOTkgNC4zODggMTAuOTU0IDEwLjEyNSAxMS45Mjd2LTguNDM3SDcuMDc4di0zLjQ5aDMuMDQ3VjkuNDNjMC0zLjAwNyAxLjc5Mi00LjY2OSA0LjUzMy00LjY2OSAxLjMxMiAwIDIuNjg2LjIzNCAyLjY4Ni4yMzR2Mi45NTNoLTEuNTEzYy0xLjQ5MSAwLTEuOTU1LjkyNS0xLjk1NSAxLjg3NHYyLjI1aDMuMzI4bC0uNTMyIDMuNDloLTIuNzk2djguNDM3QzE5LjYxMiAyMy4wMjcgMjQgMTguMDYyIDI0IDEyLjA3M3oiLz48L3N2Zz4="
                  alt="Facebook"
                  sx={{ width: 20, height: 20, mr: 1 }}
                />
                Facebook
              </Button>
            </Box>

            {/* Sign Up Link */}
            <Box textAlign="center">
              <Typography variant="body2" color="text.secondary">
                Don't have an account?{' '}
                <Link
                  component={RouterLink}
                  to="/auth/register"
                  color="primary"
                  fontWeight={500}
                  underline="hover"
                >
                  Sign up here
                </Link>
              </Typography>
            </Box>
          </Box>

          {/* Security Notice */}
          <Box
            mt={4}
            p={2}
            borderRadius={2}
            sx={{ backgroundColor: theme.palette.action.hover }}
          >
            <Box display="flex" alignItems="center" gap={1} mb={1}>
              <Shield size={16} style={{ color: theme.palette.primary.main }} />
              <Typography variant="caption" fontWeight={600} color="primary">
                Security Notice
              </Typography>
            </Box>
            <Typography variant="caption" color="text.secondary">
              Your data is protected with bank-level encryption. We use multi-factor
              authentication and continuous monitoring to keep your account secure.
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default LoginPage;