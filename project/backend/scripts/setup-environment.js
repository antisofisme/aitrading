#!/usr/bin/env node

/**
 * @fileoverview Environment setup script for AI Trading Platform
 * @version 1.0.0
 * @author AI Trading Platform Team
 */

const fs = require('fs').promises;
const path = require('path');
const { execSync } = require('child_process');

// =============================================================================
// CONFIGURATION
// =============================================================================

const COLORS = {
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  reset: '\x1b[0m',
  bright: '\x1b[1m'
};

const ENVIRONMENTS = {
  development: {
    suffix: '.development',
    description: 'Development environment with debugging enabled'
  },
  staging: {
    suffix: '.staging',
    description: 'Staging environment for testing'
  },
  production: {
    suffix: '.production',
    description: 'Production environment with security enabled'
  }
};

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

function log(message, color = COLORS.reset) {
  console.log(`${color}${message}${COLORS.reset}`);
}

function logHeader(message) {
  console.log(`\n${COLORS.bright}${COLORS.blue}${message}${COLORS.reset}\n`);
}

function logSuccess(message) {
  log(`✅ ${message}`, COLORS.green);
}

function logWarning(message) {
  log(`⚠️  ${message}`, COLORS.yellow);
}

function logError(message) {
  log(`❌ ${message}`, COLORS.red);
}

async function fileExists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

async function copyFile(source, destination) {
  try {
    const content = await fs.readFile(source, 'utf8');
    await fs.writeFile(destination, content);
    return true;
  } catch (error) {
    logError(`Failed to copy ${source} to ${destination}: ${error.message}`);
    return false;
  }
}

function executeCommand(command, description) {
  try {
    log(`Executing: ${description}`, COLORS.cyan);
    execSync(command, { stdio: 'inherit' });
    return true;
  } catch (error) {
    logError(`Failed to execute: ${description}`);
    return false;
  }
}

// =============================================================================
// SETUP FUNCTIONS
// =============================================================================

/**
 * Setup environment files
 */
async function setupEnvironmentFiles(environment) {
  logHeader('📄 Setting up environment files');

  const baseEnvFile = path.join(__dirname, '..', '.env.example');
  const targetEnvFile = path.join(__dirname, '..', '.env');
  const envSuffix = ENVIRONMENTS[environment]?.suffix || '';

  // Check if .env.example exists
  if (!(await fileExists(baseEnvFile))) {
    logError('.env.example not found');
    return false;
  }

  // Create .env file if it doesn't exist
  if (!(await fileExists(targetEnvFile))) {
    const success = await copyFile(baseEnvFile, targetEnvFile);
    if (success) {
      logSuccess('.env file created from .env.example');
    } else {
      return false;
    }
  } else {
    logWarning('.env file already exists, skipping');
  }

  // Create environment-specific files
  if (envSuffix) {
    const envSpecificFile = path.join(__dirname, '..', `.env${envSuffix}`);
    if (!(await fileExists(envSpecificFile))) {
      const success = await copyFile(baseEnvFile, envSpecificFile);
      if (success) {
        logSuccess(`Environment-specific file .env${envSuffix} created`);
      }
    } else {
      logWarning(`Environment-specific file .env${envSuffix} already exists`);
    }
  }

  // Setup service-specific environment files
  const services = ['api-gateway', 'central-hub', 'database-service', 'data-bridge'];

  for (const service of services) {
    const serviceDir = path.join(__dirname, '..', service);
    const serviceEnvExample = path.join(serviceDir, '.env.example');
    const serviceEnvFile = path.join(serviceDir, '.env');

    if (await fileExists(serviceDir)) {
      if (await fileExists(serviceEnvExample) && !(await fileExists(serviceEnvFile))) {
        const success = await copyFile(serviceEnvExample, serviceEnvFile);
        if (success) {
          logSuccess(`Environment file created for ${service}`);
        }
      }
    }
  }

  return true;
}

/**
 * Setup directories
 */
async function setupDirectories() {
  logHeader('📁 Creating required directories');

  const directories = [
    'logs',
    'data',
    'backups',
    'temp',
    'uploads',
    'monitoring/data',
    'config/ssl',
    'scripts/migrations'
  ];

  for (const dir of directories) {
    const dirPath = path.join(__dirname, '..', dir);
    try {
      await fs.mkdir(dirPath, { recursive: true });
      logSuccess(`Directory created: ${dir}`);
    } catch (error) {
      logError(`Failed to create directory ${dir}: ${error.message}`);
    }
  }

  return true;
}

/**
 * Install dependencies
 */
function installDependencies() {
  logHeader('📦 Installing dependencies');

  // Install root dependencies
  if (!executeCommand('npm install', 'Installing root dependencies')) {
    return false;
  }

  // Install workspace dependencies
  if (!executeCommand('npm run build:shared', 'Building shared package')) {
    logWarning('Failed to build shared package, continuing anyway');
  }

  return true;
}

/**
 * Setup database
 */
async function setupDatabase(environment) {
  logHeader('🗄️  Setting up database');

  if (environment === 'production') {
    logWarning('Skipping database setup in production environment');
    return true;
  }

  // Check if Docker is available
  try {
    execSync('docker --version', { stdio: 'ignore' });
  } catch {
    logWarning('Docker not available, skipping database setup');
    return true;
  }

  // Start database services
  const success = executeCommand(
    'docker-compose -f docker-compose.dev.yml up -d postgres-dev redis-dev',
    'Starting development databases'
  );

  if (success) {
    logSuccess('Development databases started');

    // Wait a moment for databases to be ready
    log('Waiting for databases to be ready...', COLORS.cyan);
    await new Promise(resolve => setTimeout(resolve, 10000));

    // Run migrations
    if (executeCommand('npm run setup:db', 'Running database migrations')) {
      logSuccess('Database migrations completed');
    } else {
      logWarning('Database migrations failed, manual setup may be required');
    }
  }

  return success;
}

/**
 * Setup monitoring
 */
function setupMonitoring(environment) {
  logHeader('📊 Setting up monitoring');

  if (environment === 'development') {
    logWarning('Skipping advanced monitoring in development environment');
    return true;
  }

  // Create monitoring configuration
  const success = executeCommand(
    'npm run setup:monitoring',
    'Setting up monitoring infrastructure'
  );

  if (success) {
    logSuccess('Monitoring infrastructure configured');
  } else {
    logWarning('Monitoring setup failed, manual configuration may be required');
  }

  return success;
}

/**
 * Validate setup
 */
async function validateSetup() {
  logHeader('✅ Validating setup');

  const validations = [
    {
      name: 'Environment files',
      check: () => fileExists(path.join(__dirname, '..', '.env'))
    },
    {
      name: 'Shared package build',
      check: () => fileExists(path.join(__dirname, '..', 'shared', 'dist', 'index.js'))
    },
    {
      name: 'Node modules',
      check: () => fileExists(path.join(__dirname, '..', 'node_modules'))
    }
  ];

  let allValid = true;

  for (const validation of validations) {
    try {
      const isValid = await validation.check();
      if (isValid) {
        logSuccess(validation.name);
      } else {
        logError(validation.name);
        allValid = false;
      }
    } catch (error) {
      logError(`${validation.name}: ${error.message}`);
      allValid = false;
    }
  }

  return allValid;
}

// =============================================================================
// MAIN EXECUTION
// =============================================================================

async function main() {
  const args = process.argv.slice(2);
  const environment = args[0] || 'development';

  if (!Object.keys(ENVIRONMENTS).includes(environment)) {
    logError(`Invalid environment: ${environment}`);
    log('Valid environments: ' + Object.keys(ENVIRONMENTS).join(', '));
    process.exit(1);
  }

  logHeader(`🚀 AI Trading Platform - Environment Setup`);
  log(`Setting up ${COLORS.bright}${environment}${COLORS.reset} environment`);
  log(ENVIRONMENTS[environment].description);

  try {
    // Setup environment files
    if (!(await setupEnvironmentFiles(environment))) {
      throw new Error('Environment setup failed');
    }

    // Setup directories
    if (!(await setupDirectories())) {
      throw new Error('Directory setup failed');
    }

    // Install dependencies
    if (!installDependencies()) {
      throw new Error('Dependency installation failed');
    }

    // Setup database (only for dev/staging)
    if (environment !== 'production') {
      await setupDatabase(environment);
    }

    // Setup monitoring (only for staging/production)
    if (environment !== 'development') {
      setupMonitoring(environment);
    }

    // Validate setup
    const isValid = await validateSetup();

    if (isValid) {
      logHeader('🎉 Setup completed successfully!');
      log(`Environment: ${COLORS.bright}${environment}${COLORS.reset}`);

      if (environment === 'development') {
        log('\nNext steps:', COLORS.cyan);
        log('1. Review and update .env file with your configuration');
        log('2. Start development services: npm run dev');
        log('3. Run health check: npm run health');
      } else {
        log('\nNext steps:', COLORS.cyan);
        log('1. Review and update environment-specific configuration');
        log('2. Configure SSL certificates for production');
        log('3. Set up external monitoring and alerting');
      }
    } else {
      logError('Setup completed with warnings. Please review the issues above.');
      process.exit(1);
    }

  } catch (error) {
    logError(`Setup failed: ${error.message}`);
    process.exit(1);
  }
}

// Show usage if help requested
if (process.argv.includes('--help') || process.argv.includes('-h')) {
  console.log(`
${COLORS.bright}AI Trading Platform - Environment Setup${COLORS.reset}

Usage: node setup-environment.js [environment]

Environments:
  development  Set up development environment (default)
  staging      Set up staging environment
  production   Set up production environment

Examples:
  node setup-environment.js                # Development setup
  node setup-environment.js development    # Development setup
  node setup-environment.js production     # Production setup

What this script does:
  ✅ Creates environment files from templates
  ✅ Sets up required directories
  ✅ Installs and builds dependencies
  ✅ Configures databases (dev/staging only)
  ✅ Sets up monitoring (staging/production only)
  ✅ Validates the setup
`);
  process.exit(0);
}

// Run the setup
main().catch(error => {
  logError(`Environment setup failed: ${error.message}`);
  process.exit(1);
});