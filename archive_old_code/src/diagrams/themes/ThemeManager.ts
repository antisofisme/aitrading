import { ThemeName, ThemeConfig } from '../core/types';

export class ThemeManager {
  private themes: Map<ThemeName, ThemeConfig>;
  private currentTheme: ThemeName = 'default';

  constructor(customThemes?: Record<string, ThemeConfig>) {
    this.themes = new Map();
    this.loadDefaultThemes();

    // Load custom themes if provided
    if (customThemes) {
      Object.entries(customThemes).forEach(([name, config]) => {
        this.themes.set(name as ThemeName, config);
      });
    }
  }

  /**
   * Apply a theme to the diagram engine
   */
  async applyTheme(themeName: ThemeName): Promise<void> {
    if (!this.themes.has(themeName)) {
      throw new Error(`Theme '${themeName}' not found`);
    }

    this.currentTheme = themeName;
  }

  /**
   * Get theme configuration
   */
  getTheme(themeName: ThemeName): ThemeConfig | undefined {
    return this.themes.get(themeName);
  }

  /**
   * Get current theme
   */
  getCurrentTheme(): ThemeName {
    return this.currentTheme;
  }

  /**
   * Get theme variables for Mermaid configuration
   */
  getThemeVariables(themeName?: ThemeName): Record<string, string> {
    const theme = this.getTheme(themeName || this.currentTheme);
    if (!theme) return {};

    return {
      primaryColor: theme.primary,
      primaryTextColor: theme.text,
      primaryBorderColor: theme.border,
      lineColor: theme.border,
      sectionBkgColor: theme.background,
      altSectionBkgColor: this.lighten(theme.background, 0.05),
      gridColor: theme.border,
      tertiaryColor: theme.accent,
      backgroundColor: theme.background,
      mainBkg: theme.background,
      secondBkg: this.lighten(theme.background, 0.1),
      tertiaryBkg: this.lighten(theme.background, 0.15)
    };
  }

  /**
   * Get CSS variables for HTML output
   */
  getCSSVariables(themeName?: ThemeName): string {
    const theme = this.getTheme(themeName || this.currentTheme);
    if (!theme) return '';

    return `
:root {
  --primary-color: ${theme.primary};
  --secondary-color: ${theme.secondary};
  --accent-color: ${theme.accent};
  --background-color: ${theme.background};
  --text-color: ${theme.text};
  --border-color: ${theme.border};
  --success-color: ${theme.success};
  --warning-color: ${theme.warning};
  --error-color: ${theme.error};
  --font-family: ${theme.fontFamily || 'system-ui, sans-serif'};
  --font-size: ${theme.fontSize || 14}px;
}`;
  }

  /**
   * Add or update a theme
   */
  addTheme(name: ThemeName, config: ThemeConfig): void {
    this.themes.set(name, config);
  }

  /**
   * Remove a theme
   */
  removeTheme(name: ThemeName): boolean {
    return this.themes.delete(name);
  }

  /**
   * List all available themes
   */
  listThemes(): ThemeName[] {
    return Array.from(this.themes.keys());
  }

  /**
   * Generate theme preview
   */
  generateThemePreview(themeName: ThemeName): string {
    const theme = this.getTheme(themeName);
    if (!theme) return '';

    return `
graph LR
    A[Primary] --> B[Secondary]
    B --> C[Accent]
    C --> D[Success]
    style A fill:${theme.primary},color:${theme.text}
    style B fill:${theme.secondary},color:${theme.text}
    style C fill:${theme.accent},color:${theme.text}
    style D fill:${theme.success},color:${theme.text}
`;
  }

  /**
   * Load default themes
   */
  private loadDefaultThemes(): void {
    // Default light theme
    this.themes.set('default', {
      primary: '#0066cc',
      secondary: '#6c757d',
      accent: '#28a745',
      background: '#ffffff',
      text: '#212529',
      border: '#dee2e6',
      success: '#28a745',
      warning: '#ffc107',
      error: '#dc3545',
      fontFamily: 'system-ui, -apple-system, sans-serif',
      fontSize: 14
    });

    // Dark theme
    this.themes.set('dark', {
      primary: '#4dabf7',
      secondary: '#868e96',
      accent: '#51cf66',
      background: '#1a1a1a',
      text: '#ffffff',
      border: '#495057',
      success: '#51cf66',
      warning: '#ffd43b',
      error: '#ff6b6b',
      fontFamily: 'system-ui, -apple-system, sans-serif',
      fontSize: 14
    });

    // Neutral theme
    this.themes.set('neutral', {
      primary: '#495057',
      secondary: '#6c757d',
      accent: '#adb5bd',
      background: '#f8f9fa',
      text: '#212529',
      border: '#dee2e6',
      success: '#198754',
      warning: '#fd7e14',
      error: '#dc3545',
      fontFamily: 'system-ui, -apple-system, sans-serif',
      fontSize: 14
    });

    // Forest theme
    this.themes.set('forest', {
      primary: '#2d5a27',
      secondary: '#52734d',
      accent: '#7cb342',
      background: '#f1f8e9',
      text: '#1b5e20',
      border: '#4caf50',
      success: '#4caf50',
      warning: '#ff9800',
      error: '#f44336',
      fontFamily: 'system-ui, -apple-system, sans-serif',
      fontSize: 14
    });

    // Base theme
    this.themes.set('base', {
      primary: '#1976d2',
      secondary: '#424242',
      accent: '#ff4081',
      background: '#fafafa',
      text: '#212121',
      border: '#e0e0e0',
      success: '#4caf50',
      warning: '#ff9800',
      error: '#f44336',
      fontFamily: 'system-ui, -apple-system, sans-serif',
      fontSize: 14
    });

    // Trading-specific themes
    this.themes.set('trading-light', {
      primary: '#1a7f64',
      secondary: '#6c757d',
      accent: '#00c851',
      background: '#f8f9fa',
      text: '#1a7f64',
      border: '#28a745',
      success: '#00c851',
      warning: '#ffbb33',
      error: '#ff4444',
      fontFamily: 'Monaco, "Lucida Console", monospace',
      fontSize: 13
    });

    this.themes.set('trading-dark', {
      primary: '#00ff88',
      secondary: '#888888',
      accent: '#00ffff',
      background: '#0a0a0a',
      text: '#00ff88',
      border: '#333333',
      success: '#00ff88',
      warning: '#ffaa00',
      error: '#ff4444',
      fontFamily: 'Monaco, "Lucida Console", monospace',
      fontSize: 13
    });

    // Professional theme
    this.themes.set('professional', {
      primary: '#2c3e50',
      secondary: '#7f8c8d',
      accent: '#3498db',
      background: '#ffffff',
      text: '#2c3e50',
      border: '#bdc3c7',
      success: '#27ae60',
      warning: '#f39c12',
      error: '#e74c3c',
      fontFamily: '"Segoe UI", Tahoma, Geneva, Verdana, sans-serif',
      fontSize: 14
    });

    // Minimal theme
    this.themes.set('minimal', {
      primary: '#000000',
      secondary: '#666666',
      accent: '#333333',
      background: '#ffffff',
      text: '#000000',
      border: '#cccccc',
      success: '#000000',
      warning: '#666666',
      error: '#000000',
      fontFamily: '"Helvetica Neue", Helvetica, Arial, sans-serif',
      fontSize: 14
    });
  }

  /**
   * Lighten a color by a factor (0-1)
   */
  private lighten(color: string, factor: number): string {
    // Simple color lightening (works for hex colors)
    if (color.startsWith('#')) {
      const hex = color.slice(1);
      const num = parseInt(hex, 16);
      const r = Math.min(255, Math.floor((num >> 16) + ((255 - (num >> 16)) * factor)));
      const g = Math.min(255, Math.floor(((num >> 8) & 0x00FF) + ((255 - ((num >> 8) & 0x00FF)) * factor)));
      const b = Math.min(255, Math.floor((num & 0x0000FF) + ((255 - (num & 0x0000FF)) * factor)));
      return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
    }
    return color;
  }

  /**
   * Darken a color by a factor (0-1)
   */
  private darken(color: string, factor: number): string {
    // Simple color darkening (works for hex colors)
    if (color.startsWith('#')) {
      const hex = color.slice(1);
      const num = parseInt(hex, 16);
      const r = Math.max(0, Math.floor((num >> 16) * (1 - factor)));
      const g = Math.max(0, Math.floor(((num >> 8) & 0x00FF) * (1 - factor)));
      const b = Math.max(0, Math.floor((num & 0x0000FF) * (1 - factor)));
      return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
    }
    return color;
  }

  /**
   * Get contrast color (black or white) for a given background
   */
  getContrastColor(backgroundColor: string): string {
    // Simple contrast calculation
    if (backgroundColor.startsWith('#')) {
      const hex = backgroundColor.slice(1);
      const num = parseInt(hex, 16);
      const r = (num >> 16) & 255;
      const g = (num >> 8) & 255;
      const b = num & 255;
      const brightness = (r * 299 + g * 587 + b * 114) / 1000;
      return brightness > 128 ? '#000000' : '#ffffff';
    }
    return '#000000';
  }

  /**
   * Generate a color palette based on a base color
   */
  generatePalette(baseColor: string): Record<string, string> {
    return {
      primary: baseColor,
      secondary: this.darken(baseColor, 0.2),
      accent: this.lighten(baseColor, 0.3),
      light: this.lighten(baseColor, 0.4),
      dark: this.darken(baseColor, 0.4),
      text: this.getContrastColor(baseColor),
      border: this.lighten(baseColor, 0.6)
    };
  }
}