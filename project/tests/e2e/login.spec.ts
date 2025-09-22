import { test, expect } from '@playwright/test';
import { AuthenticationHelper } from '../../utils/authentication-helper';
import { TestDataManager } from '../../utils/test-data-manager';

test.describe('Authentication - Login Flow', () => {
  let authHelper: AuthenticationHelper;
  let testDataManager: TestDataManager;

  test.beforeEach(async () => {
    authHelper = new AuthenticationHelper();
    testDataManager = new TestDataManager();
  });

  test.describe('@smoke Login Functionality', () => {
    test('should login with valid trader credentials', async ({ page }) => {
      const credentials = testDataManager.getTestCredentials('trader');

      await page.goto('/login');

      // Verify login page elements
      await expect(page.locator('[data-testid="login-form"]')).toBeVisible();
      await expect(page.locator('[data-testid="email-input"]')).toBeVisible();
      await expect(page.locator('[data-testid="password-input"]')).toBeVisible();
      await expect(page.locator('[data-testid="login-button"]')).toBeVisible();

      // Fill login form
      await page.fill('[data-testid="email-input"]', credentials.email);
      await page.fill('[data-testid="password-input"]', credentials.password);

      // Submit login
      await page.click('[data-testid="login-button"]');

      // Verify successful login
      await expect(page).toHaveURL(/.*\/dashboard.*/);
      await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
      await expect(page.locator('[data-testid="welcome-message"]')).toContainText('Welcome');
    });

    test('should login with admin credentials and show admin features', async ({ page }) => {
      const credentials = testDataManager.getTestCredentials('admin');

      await page.goto('/login');
      await page.fill('[data-testid="email-input"]', credentials.email);
      await page.fill('[data-testid="password-input"]', credentials.password);
      await page.click('[data-testid="login-button"]');

      // Verify admin dashboard
      await expect(page).toHaveURL(/.*\/dashboard.*/);
      await expect(page.locator('[data-testid="admin-menu"]')).toBeVisible();
      await expect(page.locator('[data-testid="user-management-link"]')).toBeVisible();
      await expect(page.locator('[data-testid="system-settings-link"]')).toBeVisible();
    });

    test('should login with premium trader and show premium features', async ({ page }) => {
      const credentials = testDataManager.getTestCredentials('premium_trader');

      await page.goto('/login');
      await page.fill('[data-testid="email-input"]', credentials.email);
      await page.fill('[data-testid="password-input"]', credentials.password);
      await page.click('[data-testid="login-button"]');

      // Verify premium features
      await expect(page).toHaveURL(/.*\/dashboard.*/);
      await expect(page.locator('[data-testid="premium-badge"]')).toBeVisible();
      await expect(page.locator('[data-testid="advanced-analytics-link"]')).toBeVisible();
      await expect(page.locator('[data-testid="premium-strategies-link"]')).toBeVisible();
    });
  });

  test.describe('@regression Login Validation', () => {
    test('should show error for invalid email format', async ({ page }) => {
      await page.goto('/login');

      await page.fill('[data-testid="email-input"]', 'invalid-email');
      await page.fill('[data-testid="password-input"]', 'password123');
      await page.click('[data-testid="login-button"]');

      await expect(page.locator('[data-testid="email-error"]')).toContainText('Please enter a valid email address');
    });

    test('should show error for empty credentials', async ({ page }) => {
      await page.goto('/login');

      await page.click('[data-testid="login-button"]');

      await expect(page.locator('[data-testid="email-error"]')).toContainText('Email is required');
      await expect(page.locator('[data-testid="password-error"]')).toContainText('Password is required');
    });

    test('should show error for wrong credentials', async ({ page }) => {
      await page.goto('/login');

      await page.fill('[data-testid="email-input"]', 'nonexistent@test.com');
      await page.fill('[data-testid="password-input"]', 'wrongpassword');
      await page.click('[data-testid="login-button"]');

      await expect(page.locator('[data-testid="login-error"]')).toContainText('Invalid email or password');
    });

    test('should show error for suspended account', async ({ page }) => {
      const credentials = testDataManager.getTestCredentials('suspended');

      await page.goto('/login');
      await page.fill('[data-testid="email-input"]', credentials.email);
      await page.fill('[data-testid="password-input"]', credentials.password);
      await page.click('[data-testid="login-button"]');

      await expect(page.locator('[data-testid="account-suspended-error"]')).toContainText('Your account has been suspended');
    });

    test('should handle password visibility toggle', async ({ page }) => {
      await page.goto('/login');

      const passwordInput = page.locator('[data-testid="password-input"]');
      const toggleButton = page.locator('[data-testid="password-toggle"]');

      // Initially password should be hidden
      await expect(passwordInput).toHaveAttribute('type', 'password');

      // Toggle to show password
      await toggleButton.click();
      await expect(passwordInput).toHaveAttribute('type', 'text');

      // Toggle back to hide password
      await toggleButton.click();
      await expect(passwordInput).toHaveAttribute('type', 'password');
    });
  });

  test.describe('@integration Two-Factor Authentication', () => {
    test('should handle 2FA flow for enabled users', async ({ page }) => {
      const user = testDataManager.getTestUser('premium_trader');

      await page.goto('/login');
      await page.fill('[data-testid="email-input"]', user.email);
      await page.fill('[data-testid="password-input"]', user.password);
      await page.click('[data-testid="login-button"]');

      // Should redirect to 2FA page
      await expect(page).toHaveURL(/.*\/two-factor.*/);
      await expect(page.locator('[data-testid="2fa-form"]')).toBeVisible();
      await expect(page.locator('[data-testid="2fa-input"]')).toBeVisible();

      // Enter 2FA code
      await authHelper.performTwoFactorAuth(page, '123456');

      // Should complete login
      await expect(page).toHaveURL(/.*\/dashboard.*/);
      await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
    });

    test('should show error for invalid 2FA code', async ({ page }) => {
      const user = testDataManager.getTestUser('premium_trader');

      await page.goto('/login');
      await page.fill('[data-testid="email-input"]', user.email);
      await page.fill('[data-testid="password-input"]', user.password);
      await page.click('[data-testid="login-button"]');

      await page.waitForURL(/.*\/two-factor.*/);
      await page.fill('[data-testid="2fa-input"]', '000000');
      await page.click('[data-testid="2fa-verify-button"]');

      await expect(page.locator('[data-testid="2fa-error"]')).toContainText('Invalid verification code');
    });

    test('should handle 2FA timeout', async ({ page }) => {
      const user = testDataManager.getTestUser('premium_trader');

      await page.goto('/login');
      await page.fill('[data-testid="email-input"]', user.email);
      await page.fill('[data-testid="password-input"]', user.password);
      await page.click('[data-testid="login-button"]');

      await page.waitForURL(/.*\/two-factor.*/);

      // Wait for timeout (simulate by waiting and then checking)
      await page.waitForTimeout(300000); // 5 minutes

      await expect(page.locator('[data-testid="2fa-timeout-error"]')).toContainText('Session expired');
    });
  });

  test.describe('@integration Remember Me Functionality', () => {
    test('should remember user when checkbox is checked', async ({ page, context }) => {
      const credentials = testDataManager.getTestCredentials('trader');

      await page.goto('/login');
      await page.fill('[data-testid="email-input"]', credentials.email);
      await page.fill('[data-testid="password-input"]', credentials.password);
      await page.check('[data-testid="remember-me-checkbox"]');
      await page.click('[data-testid="login-button"]');

      await expect(page).toHaveURL(/.*\/dashboard.*/);

      // Close and reopen browser
      await page.close();
      const newPage = await context.newPage();
      await newPage.goto('/dashboard');

      // Should still be logged in
      await expect(newPage.locator('[data-testid="user-menu"]')).toBeVisible();
    });

    test('should not remember user when checkbox is unchecked', async ({ page, context }) => {
      const credentials = testDataManager.getTestCredentials('trader');

      await page.goto('/login');
      await page.fill('[data-testid="email-input"]', credentials.email);
      await page.fill('[data-testid="password-input"]', credentials.password);
      // Don't check remember me
      await page.click('[data-testid="login-button"]');

      await expect(page).toHaveURL(/.*\/dashboard.*/);

      // Close and reopen browser
      await page.close();
      const newPage = await context.newPage();
      await newPage.goto('/dashboard');

      // Should be redirected to login
      await expect(newPage).toHaveURL(/.*\/login.*/);
    });
  });

  test.describe('@regression Session Management', () => {
    test('should handle concurrent logins', async ({ browser }) => {
      const credentials = testDataManager.getTestCredentials('trader');

      // Create two browser contexts
      const context1 = await browser.newContext();
      const context2 = await browser.newContext();

      const page1 = await context1.newPage();
      const page2 = await context2.newPage();

      // Login in both contexts
      await authHelper.loginAs(page1, 'trader');
      await authHelper.loginAs(page2, 'trader');

      // Both should be logged in
      await expect(page1.locator('[data-testid="user-menu"]')).toBeVisible();
      await expect(page2.locator('[data-testid="user-menu"]')).toBeVisible();

      await context1.close();
      await context2.close();
    });

    test('should handle session expiration', async ({ page }) => {
      await authHelper.loginAs(page, 'trader');
      await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();

      // Simulate session expiration by manipulating cookies
      await page.context().clearCookies();

      // Navigate to protected page
      await page.goto('/portfolio');

      // Should be redirected to login
      await expect(page).toHaveURL(/.*\/login.*/);
    });

    test('should auto-refresh expired tokens', async ({ page }) => {
      await authHelper.loginAs(page, 'trader');

      // Simulate token refresh
      await authHelper.refreshToken(page);

      // Should still be authenticated
      await page.reload();
      await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
    });
  });

  test.describe('@accessibility Login Accessibility', () => {
    test('should be accessible with keyboard navigation', async ({ page }) => {
      await page.goto('/login');

      // Tab through form elements
      await page.keyboard.press('Tab');
      await expect(page.locator('[data-testid="email-input"]')).toBeFocused();

      await page.keyboard.press('Tab');
      await expect(page.locator('[data-testid="password-input"]')).toBeFocused();

      await page.keyboard.press('Tab');
      await expect(page.locator('[data-testid="remember-me-checkbox"]')).toBeFocused();

      await page.keyboard.press('Tab');
      await expect(page.locator('[data-testid="login-button"]')).toBeFocused();
    });

    test('should have proper ARIA labels', async ({ page }) => {
      await page.goto('/login');

      await expect(page.locator('[data-testid="email-input"]')).toHaveAttribute('aria-label');
      await expect(page.locator('[data-testid="password-input"]')).toHaveAttribute('aria-label');
      await expect(page.locator('[data-testid="login-button"]')).toHaveAttribute('aria-label');
    });

    test('should support screen reader announcements', async ({ page }) => {
      await page.goto('/login');

      await page.fill('[data-testid="email-input"]', 'invalid-email');
      await page.click('[data-testid="login-button"]');

      // Check for aria-live regions
      await expect(page.locator('[aria-live="polite"]')).toBeVisible();
    });
  });
});