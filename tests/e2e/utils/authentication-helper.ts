import { Page, BrowserContext } from '@playwright/test';
import axios from 'axios';
import { TestDataManager } from './test-data-manager';
import * as path from 'path';

/**
 * Helper for authentication-related operations in E2E tests
 */
export class AuthenticationHelper {
  private testDataManager: TestDataManager;
  private authStateFile = path.join(__dirname, '../.auth/auth-state.json');

  constructor() {
    this.testDataManager = new TestDataManager();
  }

  /**
   * Create test users in the system
   */
  async createTestUsers(): Promise<void> {
    console.log('Creating test users...');

    const users = this.testDataManager.getTestData('users');
    const apiUrl = process.env.API_BASE_URL || 'http://localhost:8000/api/v1';

    for (const user of users) {
      try {
        await axios.post(`${apiUrl}/auth/register`, {
          email: user.email,
          password: user.password,
          firstName: user.firstName,
          lastName: user.lastName,
          role: user.role
        });

        // Verify email automatically for test users
        await axios.post(`${apiUrl}/auth/verify-email`, {
          email: user.email,
          token: 'test-verification-token'
        });

        console.log(`✅ Created user: ${user.email}`);
      } catch (error) {
        if (error.response?.status === 409) {
          console.log(`ℹ️ User already exists: ${user.email}`);
        } else {
          console.error(`❌ Failed to create user ${user.email}:`, error.message);
        }
      }
    }
  }

  /**
   * Generate authentication tokens for test users
   */
  async generateTestTokens(): Promise<void> {
    console.log('Generating authentication tokens...');

    const users = this.testDataManager.getTestData('users');
    const apiUrl = process.env.API_BASE_URL || 'http://localhost:8000/api/v1';
    const tokens: Record<string, string> = {};

    for (const user of users) {
      try {
        const response = await axios.post(`${apiUrl}/auth/login`, {
          email: user.email,
          password: user.password
        });

        tokens[user.id] = response.data.token;
        console.log(`✅ Generated token for: ${user.email}`);
      } catch (error) {
        console.error(`❌ Failed to generate token for ${user.email}:`, error.message);
      }
    }

    // Save tokens for use in tests
    await this.testDataManager.saveToFixtures('auth-tokens.json', tokens);
  }

  /**
   * Login and save authentication state
   */
  async loginAndSaveState(page: Page, context: BrowserContext): Promise<void> {
    console.log('Logging in and saving authentication state...');

    const credentials = this.testDataManager.getTestCredentials('admin');
    const baseUrl = process.env.BASE_URL || 'http://localhost:3000';

    try {
      // Navigate to login page
      await page.goto(`${baseUrl}/login`);

      // Fill login form
      await page.fill('[data-testid="email-input"]', credentials.email);
      await page.fill('[data-testid="password-input"]', credentials.password);

      // Submit login form
      await page.click('[data-testid="login-button"]');

      // Wait for successful login
      await page.waitForURL('**/dashboard**');

      // Save authentication state
      await context.storageState({ path: this.authStateFile });

      console.log('✅ Authentication state saved');
    } catch (error) {
      console.error('❌ Failed to login and save state:', error);
      throw error;
    }
  }

  /**
   * Login with specific user credentials
   */
  async loginAs(page: Page, role: string = 'trader'): Promise<void> {
    const credentials = this.testDataManager.getTestCredentials(role);
    const baseUrl = process.env.BASE_URL || 'http://localhost:3000';

    await page.goto(`${baseUrl}/login`);
    await page.fill('[data-testid="email-input"]', credentials.email);
    await page.fill('[data-testid="password-input"]', credentials.password);
    await page.click('[data-testid="login-button"]');
    await page.waitForURL('**/dashboard**');
  }

  /**
   * Logout current user
   */
  async logout(page: Page): Promise<void> {
    await page.click('[data-testid="user-menu"]');
    await page.click('[data-testid="logout-button"]');
    await page.waitForURL('**/login**');
  }

  /**
   * Perform two-factor authentication
   */
  async performTwoFactorAuth(page: Page, code: string = '123456'): Promise<void> {
    await page.waitForSelector('[data-testid="2fa-input"]');
    await page.fill('[data-testid="2fa-input"]', code);
    await page.click('[data-testid="2fa-verify-button"]');
    await page.waitForURL('**/dashboard**');
  }

  /**
   * Reset password flow
   */
  async resetPassword(page: Page, email: string): Promise<void> {
    const baseUrl = process.env.BASE_URL || 'http://localhost:3000';

    await page.goto(`${baseUrl}/forgot-password`);
    await page.fill('[data-testid="email-input"]', email);
    await page.click('[data-testid="reset-password-button"]');

    // Wait for success message
    await page.waitForSelector('[data-testid="reset-password-success"]');
  }

  /**
   * Verify email flow
   */
  async verifyEmail(page: Page, token: string): Promise<void> {
    const baseUrl = process.env.BASE_URL || 'http://localhost:3000';

    await page.goto(`${baseUrl}/verify-email?token=${token}`);
    await page.waitForSelector('[data-testid="email-verified-success"]');
  }

  /**
   * Check if user is authenticated
   */
  async isAuthenticated(page: Page): Promise<boolean> {
    try {
      await page.waitForSelector('[data-testid="user-menu"]', { timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Get current user role from page
   */
  async getCurrentUserRole(page: Page): Promise<string> {
    const roleElement = await page.locator('[data-testid="user-role"]');
    return await roleElement.textContent() || 'unknown';
  }

  /**
   * Switch user context (for admin users)
   */
  async switchUserContext(page: Page, targetUserId: string): Promise<void> {
    await page.click('[data-testid="admin-menu"]');
    await page.click('[data-testid="switch-user-button"]');
    await page.fill('[data-testid="user-search-input"]', targetUserId);
    await page.click(`[data-testid="user-option-${targetUserId}"]`);
    await page.waitForSelector('[data-testid="switched-user-banner"]');
  }

  /**
   * Get authentication state file path
   */
  getAuthStateFile(): string {
    return this.authStateFile;
  }

  /**
   * Clear authentication state
   */
  async clearAuthState(): Promise<void> {
    try {
      const fs = await import('fs/promises');
      await fs.unlink(this.authStateFile);
    } catch (error) {
      // File might not exist
    }
  }

  /**
   * Generate API authentication headers
   */
  async getAPIAuthHeaders(userId: string): Promise<Record<string, string>> {
    const tokens = await this.testDataManager.loadFromFixtures('auth-tokens.json');
    const token = tokens[userId];

    if (!token) {
      throw new Error(`No token found for user: ${userId}`);
    }

    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  /**
   * Validate session
   */
  async validateSession(page: Page): Promise<boolean> {
    try {
      const response = await page.evaluate(async () => {
        const response = await fetch('/api/auth/validate', {
          method: 'GET',
          credentials: 'include'
        });
        return response.ok;
      });

      return response;
    } catch (error) {
      return false;
    }
  }

  /**
   * Refresh authentication token
   */
  async refreshToken(page: Page): Promise<void> {
    await page.evaluate(async () => {
      await fetch('/api/auth/refresh', {
        method: 'POST',
        credentials: 'include'
      });
    });
  }
}