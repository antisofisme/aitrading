/**
 * ContextDetector - Project-aware context detection system
 * Analyzes project structure and content to provide intelligent routing
 */

const fs = require('fs').promises;
const path = require('path');
const { glob } = require('glob');

class ContextDetector {
  constructor(config = {}) {
    this.config = {
      projectRoot: config.projectRoot || process.cwd(),
      cacheTimeout: config.cacheTimeout || 300000, // 5 minutes
      maxFileAnalysis: config.maxFileAnalysis || 100,
      ...config
    };

    this.contextCache = new Map();
    this.projectSignature = null;
    this.analysisTimestamp = null;
  }

  /**
   * Detect comprehensive project context
   */
  async detectProjectContext() {
    const cacheKey = 'project-context';

    // Check cache first
    if (this.isContextCached(cacheKey)) {
      return this.contextCache.get(cacheKey);
    }

    try {
      console.log('🔍 Analyzing project context...');

      const context = {
        type: 'unknown',
        subtype: null,
        confidence: 0,
        features: [],
        technologies: [],
        architecture: {},
        documentation: {},
        aiTrading: {},
        recommendations: []
      };

      // Run all analysis methods in parallel
      const [
        packageAnalysis,
        structureAnalysis,
        contentAnalysis,
        aiTradingAnalysis,
        archAnalysis,
        docAnalysis
      ] = await Promise.all([
        this.analyzePackageJson(),
        this.analyzeProjectStructure(),
        this.analyzeCodeContent(),
        this.analyzeAiTradingFeatures(),
        this.analyzeArchitecture(),
        this.analyzeDocumentation()
      ]);

      // Merge all analysis results
      Object.assign(context, packageAnalysis);
      this.mergeAnalysis(context, structureAnalysis);
      this.mergeAnalysis(context, contentAnalysis);
      this.mergeAnalysis(context, aiTradingAnalysis);
      this.mergeAnalysis(context, archAnalysis);
      this.mergeAnalysis(context, docAnalysis);

      // Calculate final project type and confidence
      this.calculateProjectType(context);

      // Generate recommendations
      context.recommendations = this.generateRecommendations(context);

      // Cache the result
      this.contextCache.set(cacheKey, context);
      this.analysisTimestamp = Date.now();

      console.log(`✅ Project context detected: ${context.type}${context.subtype ? ` (${context.subtype})` : ''} - Confidence: ${context.confidence}%`);

      return context;
    } catch (error) {
      console.error('❌ Failed to detect project context:', error);
      throw error;
    }
  }

  /**
   * Analyze package.json for technology indicators
   */
  async analyzePackageJson() {
    const packagePath = path.join(this.config.projectRoot, 'package.json');
    const context = {
      technologies: [],
      features: [],
      metadata: {}
    };

    try {
      if (await this.fileExists(packagePath)) {
        const packageContent = await fs.readFile(packagePath, 'utf8');
        const packageJson = JSON.parse(packageContent);

        context.metadata = {
          name: packageJson.name,
          version: packageJson.version,
          description: packageJson.description,
          keywords: packageJson.keywords || []
        };

        // Analyze dependencies
        const allDeps = {
          ...packageJson.dependencies,
          ...packageJson.devDependencies,
          ...packageJson.peerDependencies
        };

        this.analyzeDependencies(allDeps, context);
        this.analyzeScripts(packageJson.scripts || {}, context);
      }
    } catch (error) {
      console.warn('Failed to analyze package.json:', error.message);
    }

    return context;
  }

  /**
   * Analyze project directory structure
   */
  async analyzeProjectStructure() {
    const context = {
      architecture: {
        type: 'unknown',
        patterns: [],
        complexity: 'simple'
      },
      features: []
    };

    try {
      const items = await fs.readdir(this.config.projectRoot);
      const directories = [];
      const files = [];

      for (const item of items) {
        const itemPath = path.join(this.config.projectRoot, item);
        const stats = await fs.stat(itemPath);

        if (stats.isDirectory()) {
          directories.push(item);
        } else {
          files.push(item);
        }
      }

      // Analyze directory patterns
      this.analyzeDirectoryPatterns(directories, context);
      this.analyzeProjectFiles(files, context);
      this.calculateComplexity(directories, files, context);

    } catch (error) {
      console.warn('Failed to analyze project structure:', error.message);
    }

    return context;
  }

  /**
   * Analyze code content for patterns and features
   */
  async analyzeCodeContent() {
    const context = {
      features: [],
      patterns: [],
      languages: []
    };

    try {
      // Find all code files
      const codeFiles = await glob('**/*.{js,ts,jsx,tsx,py,java,cpp,h}', {
        cwd: this.config.projectRoot,
        ignore: ['node_modules/**', 'dist/**', 'build/**', '.git/**'],
        absolute: true
      });

      // Limit analysis to prevent timeout
      const filesToAnalyze = codeFiles.slice(0, this.config.maxFileAnalysis);

      // Analyze files in batches
      const batchSize = 10;
      for (let i = 0; i < filesToAnalyze.length; i += batchSize) {
        const batch = filesToAnalyze.slice(i, i + batchSize);
        const batchPromises = batch.map(file => this.analyzeCodeFile(file));
        const batchResults = await Promise.allSettled(batchPromises);

        batchResults.forEach(result => {
          if (result.status === 'fulfilled') {
            this.mergeAnalysis(context, result.value);
          }
        });
      }

      // Deduplicate and sort results
      context.features = [...new Set(context.features)];
      context.patterns = [...new Set(context.patterns)];
      context.languages = [...new Set(context.languages)];

    } catch (error) {
      console.warn('Failed to analyze code content:', error.message);
    }

    return context;
  }

  /**
   * Analyze AI trading specific features
   */
  async analyzeAiTradingFeatures() {
    const context = {
      aiTrading: {
        isAiTrading: false,
        confidence: 0,
        features: [],
        strategies: [],
        indicators: [],
        platforms: []
      }
    };

    try {
      // Check for AI trading indicators in various places
      const indicators = await Promise.all([
        this.checkAiTradingKeywords(),
        this.checkTradingFiles(),
        this.checkTradingDependencies(),
        this.checkTradingConfigs()
      ]);

      const totalScore = indicators.reduce((sum, score) => sum + score, 0);
      const maxScore = indicators.length * 100;

      context.aiTrading.confidence = Math.round((totalScore / maxScore) * 100);
      context.aiTrading.isAiTrading = context.aiTrading.confidence > 50;

      if (context.aiTrading.isAiTrading) {
        await this.analyzeAiTradingDetails(context.aiTrading);
      }

    } catch (error) {
      console.warn('Failed to analyze AI trading features:', error.message);
    }

    return context;
  }

  /**
   * Analyze system architecture patterns
   */
  async analyzeArchitecture() {
    const context = {
      architecture: {
        patterns: [],
        layers: [],
        components: [],
        dataFlow: 'unknown'
      }
    };

    try {
      // Analyze architectural patterns
      const patterns = await Promise.all([
        this.detectMvcPattern(),
        this.detectMicroservicesPattern(),
        this.detectLayeredPattern(),
        this.detectEventDrivenPattern(),
        this.detectModularPattern()
      ]);

      context.architecture.patterns = patterns.filter(Boolean);

      // Analyze data flow
      context.architecture.dataFlow = await this.analyzeDataFlow();

      // Identify components
      context.architecture.components = await this.identifyComponents();

    } catch (error) {
      console.warn('Failed to analyze architecture:', error.message);
    }

    return context;
  }

  /**
   * Analyze existing documentation
   */
  async analyzeDocumentation() {
    const context = {
      documentation: {
        existing: [],
        gaps: [],
        quality: 'unknown',
        coverage: 0
      }
    };

    try {
      // Find existing documentation
      const docFiles = await glob('**/*.{md,txt,rst,adoc}', {
        cwd: this.config.projectRoot,
        ignore: ['node_modules/**'],
        absolute: true
      });

      context.documentation.existing = await Promise.all(
        docFiles.map(file => this.analyzeDocFile(file))
      );

      // Calculate coverage and quality
      context.documentation.coverage = this.calculateDocCoverage(context.documentation.existing);
      context.documentation.quality = this.assessDocQuality(context.documentation.existing);

      // Identify gaps
      context.documentation.gaps = this.identifyDocGaps(context);

    } catch (error) {
      console.warn('Failed to analyze documentation:', error.message);
    }

    return context;
  }

  /**
   * Helper methods for dependency analysis
   */
  analyzeDependencies(deps, context) {
    const depNames = Object.keys(deps);
    const depString = depNames.join(' ').toLowerCase();

    // Framework detection
    if (deps.express) context.technologies.push('express', 'nodejs', 'web-api');
    if (deps.react) context.technologies.push('react', 'frontend', 'spa');
    if (deps.vue) context.technologies.push('vue', 'frontend', 'spa');
    if (deps.angular) context.technologies.push('angular', 'frontend', 'spa');

    // Database detection
    if (deps.mongoose || deps.mongodb) context.technologies.push('mongodb', 'nosql');
    if (deps.pg || deps.postgres) context.technologies.push('postgresql', 'sql');
    if (deps.mysql) context.technologies.push('mysql', 'sql');
    if (deps.redis) context.technologies.push('redis', 'cache');

    // AI/ML detection
    if (deps.tensorflow || deps['@tensorflow/tfjs']) {
      context.technologies.push('tensorflow', 'machine-learning', 'ai');
      context.features.push('neural-networks');
    }
    if (deps.pytorch) {
      context.technologies.push('pytorch', 'machine-learning', 'ai');
    }

    // Trading specific libraries
    const tradingLibs = ['ccxt', 'binance', 'alpaca', 'ib', 'interactive-brokers', 'tradingview'];
    tradingLibs.forEach(lib => {
      if (deps[lib]) {
        context.technologies.push('trading-api', 'financial-data');
        context.features.push('algorithmic-trading');
      }
    });

    // Testing frameworks
    if (deps.jest || deps.mocha || deps.jasmine) {
      context.technologies.push('testing');
      context.features.push('unit-testing');
    }
  }

  analyzeScripts(scripts, context) {
    const scriptCommands = Object.values(scripts).join(' ').toLowerCase();

    if (scriptCommands.includes('test')) context.features.push('automated-testing');
    if (scriptCommands.includes('build')) context.features.push('build-system');
    if (scriptCommands.includes('lint')) context.features.push('code-quality');
    if (scriptCommands.includes('deploy')) context.features.push('deployment');
  }

  /**
   * Directory pattern analysis
   */
  analyzeDirectoryPatterns(directories, context) {
    const dirNames = directories.map(d => d.toLowerCase());

    // MVC pattern
    if (dirNames.includes('models') && dirNames.includes('views') && dirNames.includes('controllers')) {
      context.architecture.patterns.push('mvc');
    }

    // Layered architecture
    if (dirNames.includes('services') && dirNames.includes('repositories')) {
      context.architecture.patterns.push('layered');
    }

    // Microservices
    if (dirNames.includes('services') && directories.length > 5) {
      context.architecture.patterns.push('microservices');
    }

    // Trading specific
    const tradingDirs = ['strategies', 'indicators', 'algorithms', 'trading', 'backtesting'];
    if (tradingDirs.some(dir => dirNames.includes(dir))) {
      context.features.push('algorithmic-trading');
    }
  }

  /**
   * Calculate project type and confidence
   */
  calculateProjectType(context) {
    const scores = {
      'ai-trading': 0,
      'web-api': 0,
      'frontend': 0,
      'ml-project': 0,
      'library': 0,
      'cli-tool': 0
    };

    // AI Trading scoring
    if (context.aiTrading?.isAiTrading) {
      scores['ai-trading'] += context.aiTrading.confidence;
    }

    // Technology-based scoring
    if (context.technologies.includes('express')) scores['web-api'] += 30;
    if (context.technologies.includes('react')) scores['frontend'] += 30;
    if (context.technologies.includes('tensorflow')) scores['ml-project'] += 25;

    // Feature-based scoring
    if (context.features.includes('algorithmic-trading')) scores['ai-trading'] += 40;
    if (context.features.includes('neural-networks')) scores['ml-project'] += 20;
    if (context.features.includes('web-api')) scores['web-api'] += 20;

    // Find the highest scoring type
    const maxScore = Math.max(...Object.values(scores));
    const projectType = Object.keys(scores).find(type => scores[type] === maxScore);

    context.type = maxScore > 20 ? projectType : 'unknown';
    context.confidence = Math.min(maxScore, 100);

    // Determine subtype for AI trading projects
    if (context.type === 'ai-trading') {
      context.subtype = this.determineAiTradingSubtype(context);
    }
  }

  /**
   * Generate context-aware recommendations
   */
  generateRecommendations(context) {
    const recommendations = [];

    if (context.type === 'ai-trading') {
      recommendations.push({
        type: 'documentation',
        priority: 'high',
        agent: 'algorithm-agent',
        description: 'Document trading strategies and algorithms with flow diagrams'
      });

      if (context.technologies.includes('tensorflow')) {
        recommendations.push({
          type: 'documentation',
          priority: 'medium',
          agent: 'api-agent',
          description: 'Document ML model APIs and prediction endpoints'
        });
      }
    }

    if (context.technologies.includes('express')) {
      recommendations.push({
        type: 'documentation',
        priority: 'high',
        agent: 'api-agent',
        description: 'Generate OpenAPI documentation for REST endpoints'
      });
    }

    if (context.documentation.coverage < 50) {
      recommendations.push({
        type: 'documentation',
        priority: 'medium',
        agent: 'user-guide-agent',
        description: 'Create comprehensive user guides and examples'
      });
    }

    return recommendations;
  }

  /**
   * Utility methods
   */
  async fileExists(filePath) {
    try {
      await fs.access(filePath);
      return true;
    } catch {
      return false;
    }
  }

  isContextCached(key) {
    if (!this.contextCache.has(key)) return false;

    const age = Date.now() - (this.analysisTimestamp || 0);
    return age < this.config.cacheTimeout;
  }

  mergeAnalysis(target, source) {
    Object.keys(source).forEach(key => {
      if (Array.isArray(source[key])) {
        target[key] = [...(target[key] || []), ...source[key]];
      } else if (typeof source[key] === 'object' && source[key] !== null) {
        target[key] = { ...(target[key] || {}), ...source[key] };
      } else if (source[key] !== undefined) {
        target[key] = source[key];
      }
    });
  }

  /**
   * AI Trading specific analysis methods
   */
  async checkAiTradingKeywords() {
    // Implementation for keyword analysis
    return 0; // Placeholder
  }

  async checkTradingFiles() {
    // Implementation for trading file analysis
    return 0; // Placeholder
  }

  async checkTradingDependencies() {
    // Implementation for trading dependency analysis
    return 0; // Placeholder
  }

  async checkTradingConfigs() {
    // Implementation for trading config analysis
    return 0; // Placeholder
  }

  async analyzeAiTradingDetails(aiTrading) {
    // Implementation for detailed AI trading analysis
  }

  determineAiTradingSubtype(context) {
    // Implementation for subtype determination
    return null;
  }

  // Additional placeholder methods for complete implementation
  async analyzeCodeFile(filePath) { return {}; }
  async detectMvcPattern() { return null; }
  async detectMicroservicesPattern() { return null; }
  async detectLayeredPattern() { return null; }
  async detectEventDrivenPattern() { return null; }
  async detectModularPattern() { return null; }
  async analyzeDataFlow() { return 'unknown'; }
  async identifyComponents() { return []; }
  async analyzeDocFile(filePath) { return {}; }
  calculateDocCoverage(docs) { return 0; }
  assessDocQuality(docs) { return 'unknown'; }
  identifyDocGaps(context) { return []; }
  calculateComplexity(dirs, files, context) {}
  analyzeProjectFiles(files, context) {}
}

module.exports = ContextDetector;