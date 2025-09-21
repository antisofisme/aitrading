#!/usr/bin/env node

/**
 * @fileoverview Workspace validation script for AI Trading Platform
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

const WORKSPACE_STRUCTURE = {
  'package.json': { type: 'file', required: true },
  'tsconfig.json': { type: 'file', required: true },
  'docker-compose.yml': { type: 'file', required: true },
  'docker-compose.dev.yml': { type: 'file', required: true },
  '.env.example': { type: 'file', required: true },
  'shared/': { type: 'directory', required: true },
  'shared/package.json': { type: 'file', required: true },
  'shared/tsconfig.json': { type: 'file', required: true },
  'shared/src/': { type: 'directory', required: true },
  'api-gateway/': { type: 'directory', required: true },
  'central-hub/': { type: 'directory', required: true },
  'database-service/': { type: 'directory', required: true },
  'data-bridge/': { type: 'directory', required: true },
  'config/': { type: 'directory', required: true },
  'monitoring/': { type: 'directory', required: true },
  'scripts/': { type: 'directory', required: true }
};

const SERVICES = ['api-gateway', 'central-hub', 'database-service', 'data-bridge'];

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
    const stat = await fs.stat(filePath);
    return { exists: true, isFile: stat.isFile(), isDirectory: stat.isDirectory() };
  } catch {
    return { exists: false, isFile: false, isDirectory: false };
  }
}

async function readJsonFile(filePath) {
  try {
    const content = await fs.readFile(filePath, 'utf8');
    return JSON.parse(content);
  } catch (error) {
    throw new Error(`Failed to read JSON file ${filePath}: ${error.message}`);
  }
}

function executeCommand(command, silent = false) {
  try {
    const output = execSync(command, {
      encoding: 'utf8',
      stdio: silent ? 'pipe' : 'inherit'
    });
    return { success: true, output };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

// =============================================================================
// VALIDATION FUNCTIONS
// =============================================================================

/**
 * Validate workspace structure
 */
async function validateWorkspaceStructure() {
  logHeader('📁 Validating workspace structure');

  let allValid = true;

  for (const [filePath, config] of Object.entries(WORKSPACE_STRUCTURE)) {
    const fullPath = path.join(__dirname, '..', filePath);
    const { exists, isFile, isDirectory } = await fileExists(fullPath);

    if (!exists) {
      if (config.required) {
        logError(`Missing required ${config.type}: ${filePath}`);
        allValid = false;
      } else {
        logWarning(`Optional ${config.type} not found: ${filePath}`);
      }
    } else {
      if (config.type === 'file' && !isFile) {
        logError(`Expected file but found directory: ${filePath}`);
        allValid = false;
      } else if (config.type === 'directory' && !isDirectory) {
        logError(`Expected directory but found file: ${filePath}`);
        allValid = false;
      } else {
        logSuccess(`${config.type}: ${filePath}`);
      }
    }
  }

  return allValid;
}

/**
 * Validate package.json configurations
 */
async function validatePackageConfigurations() {
  logHeader('📦 Validating package configurations');

  let allValid = true;

  // Validate root package.json
  try {
    const rootPackage = await readJsonFile(path.join(__dirname, '..', 'package.json'));

    // Check workspace configuration
    if (!rootPackage.workspaces) {
      logError('Root package.json missing workspaces configuration');
      allValid = false;
    } else {
      logSuccess('Root package.json has workspaces configuration');
    }

    // Check essential scripts
    const requiredScripts = ['dev', 'build', 'test', 'health'];
    for (const script of requiredScripts) {
      if (!rootPackage.scripts || !rootPackage.scripts[script]) {
        logError(`Root package.json missing required script: ${script}`);
        allValid = false;
      } else {
        logSuccess(`Script present: ${script}`);
      }
    }

  } catch (error) {
    logError(`Failed to validate root package.json: ${error.message}`);
    allValid = false;
  }

  // Validate service package.json files
  for (const service of SERVICES) {
    try {
      const servicePath = path.join(__dirname, '..', service, 'package.json');
      const { exists } = await fileExists(servicePath);

      if (!exists) {
        logWarning(`Service package.json not found: ${service}`);
        continue;
      }

      const servicePackage = await readJsonFile(servicePath);

      // Check service name follows convention
      if (!servicePackage.name.startsWith('@aitrading/')) {
        logWarning(`Service ${service} package name doesn't follow convention`);
      } else {
        logSuccess(`Service ${service} package name follows convention`);
      }

    } catch (error) {
      logError(`Failed to validate ${service} package.json: ${error.message}`);
      allValid = false;
    }
  }

  return allValid;
}

/**
 * Validate TypeScript configuration
 */
async function validateTypeScriptConfiguration() {
  logHeader('🔧 Validating TypeScript configuration');

  let allValid = true;

  // Validate root tsconfig.json
  try {
    const rootTsConfig = await readJsonFile(path.join(__dirname, '..', 'tsconfig.json'));

    if (!rootTsConfig.references) {
      logError('Root tsconfig.json missing project references');
      allValid = false;
    } else {
      logSuccess('Root tsconfig.json has project references');
    }

    if (!rootTsConfig.compilerOptions?.paths) {
      logError('Root tsconfig.json missing path mapping');
      allValid = false;
    } else {
      logSuccess('Root tsconfig.json has path mapping');
    }

  } catch (error) {
    logError(`Failed to validate root tsconfig.json: ${error.message}`);
    allValid = false;
  }

  // Validate shared tsconfig.json
  try {
    const sharedTsConfig = await readJsonFile(path.join(__dirname, '..', 'shared', 'tsconfig.json'));

    if (!sharedTsConfig.compilerOptions?.composite) {
      logError('Shared tsconfig.json missing composite configuration');
      allValid = false;
    } else {
      logSuccess('Shared tsconfig.json properly configured for project references');
    }

  } catch (error) {
    logError(`Failed to validate shared tsconfig.json: ${error.message}`);
    allValid = false;
  }

  return allValid;
}

/**
 * Validate Docker configuration
 */
async function validateDockerConfiguration() {
  logHeader('🐳 Validating Docker configuration');

  let allValid = true;

  // Check Docker Compose files
  const composeFiles = ['docker-compose.yml', 'docker-compose.dev.yml'];

  for (const file of composeFiles) {
    const { exists } = await fileExists(path.join(__dirname, '..', file));
    if (exists) {
      logSuccess(`Docker Compose file present: ${file}`);
    } else {
      logError(`Docker Compose file missing: ${file}`);
      allValid = false;
    }
  }

  // Check service Dockerfiles
  for (const service of SERVICES) {
    const dockerfilePath = path.join(__dirname, '..', service, 'Dockerfile');
    const { exists } = await fileExists(dockerfilePath);

    if (exists) {
      logSuccess(`Dockerfile present for service: ${service}`);
    } else {
      logWarning(`Dockerfile missing for service: ${service}`);
    }
  }

  // Validate Docker Compose syntax
  const validateResult = executeCommand('docker-compose -f docker-compose.yml config', true);
  if (validateResult.success) {
    logSuccess('Docker Compose configuration is valid');
  } else {
    logError('Docker Compose configuration has syntax errors');
    allValid = false;
  }

  return allValid;
}

/**
 * Validate build system
 */
async function validateBuildSystem() {
  logHeader('🔨 Validating build system');

  let allValid = true;

  // Check if dependencies are installed
  const { exists: nodeModulesExists } = await fileExists(path.join(__dirname, '..', 'node_modules'));
  if (nodeModulesExists) {
    logSuccess('Dependencies installed');
  } else {
    logError('Dependencies not installed. Run: npm install');
    allValid = false;
  }

  // Check if shared package builds successfully
  const buildResult = executeCommand('npm run build:shared', true);
  if (buildResult.success) {
    logSuccess('Shared package builds successfully');
  } else {
    logError('Shared package build failed');
    allValid = false;
  }

  // Check if shared package dist exists
  const { exists: distExists } = await fileExists(path.join(__dirname, '..', 'shared', 'dist'));
  if (distExists) {
    logSuccess('Shared package compiled output exists');
  } else {
    logError('Shared package compiled output missing');
    allValid = false;
  }

  return allValid;
}

/**
 * Validate service dependencies
 */
async function validateServiceDependencies() {
  logHeader('🔗 Validating service dependencies');

  let allValid = true;

  // Check if services can import shared package
  for (const service of SERVICES) {
    const serviceDir = path.join(__dirname, '..', service);
    const { exists: serviceDirExists } = await fileExists(serviceDir);

    if (!serviceDirExists) {
      logWarning(`Service directory not found: ${service}`);
      continue;
    }

    // Check if service has proper dependency on shared package
    try {
      const servicePackage = await readJsonFile(path.join(serviceDir, 'package.json'));

      if (servicePackage.dependencies?.['@aitrading/shared'] ||
          servicePackage.devDependencies?.['@aitrading/shared']) {
        logSuccess(`Service ${service} depends on shared package`);
      } else {
        logWarning(`Service ${service} doesn't depend on shared package`);
      }
    } catch {
      logWarning(`Could not check dependencies for service: ${service}`);
    }
  }

  return allValid;
}

/**
 * Validate configuration files
 */
async function validateConfigurationFiles() {
  logHeader('⚙️ Validating configuration files');

  let allValid = true;

  const configFiles = [
    'config/consul/consul.hcl',
    'config/consul/services.json',
    'config/redis/redis.conf',
    'monitoring/prometheus/prometheus.yml'
  ];

  for (const configFile of configFiles) {
    const { exists } = await fileExists(path.join(__dirname, '..', configFile));
    if (exists) {
      logSuccess(`Configuration file present: ${configFile}`);
    } else {
      logError(`Configuration file missing: ${configFile}`);
      allValid = false;
    }
  }

  return allValid;
}

/**
 * Validate scripts and tools
 */
async function validateScriptsAndTools() {
  logHeader('🛠️ Validating scripts and tools');

  let allValid = true;

  const scripts = [
    'scripts/health-check.js',
    'scripts/setup-environment.js'
  ];

  for (const script of scripts) {
    const { exists } = await fileExists(path.join(__dirname, '..', script));
    if (exists) {
      logSuccess(`Script present: ${script}`);
    } else {
      logError(`Script missing: ${script}`);
      allValid = false;
    }
  }

  // Check if scripts are executable
  const healthCheckResult = executeCommand('node scripts/health-check.js --help', true);
  if (healthCheckResult.success) {
    logSuccess('Health check script is functional');
  } else {
    logError('Health check script has issues');
    allValid = false;
  }

  return allValid;
}

/**
 * Generate validation report
 */
function generateValidationReport(results) {
  logHeader('📊 Validation Report');

  const totalChecks = Object.keys(results).length;
  const passedChecks = Object.values(results).filter(result => result).length;
  const failedChecks = totalChecks - passedChecks;

  log(`Total checks: ${totalChecks}`);
  log(`Passed: ${passedChecks}`, COLORS.green);
  log(`Failed: ${failedChecks}`, failedChecks > 0 ? COLORS.red : COLORS.green);

  console.log('\nDetailed results:');
  for (const [check, passed] of Object.entries(results)) {
    const status = passed ? '✅ PASS' : '❌ FAIL';
    const color = passed ? COLORS.green : COLORS.red;
    log(`  ${status} ${check}`, color);
  }

  if (failedChecks === 0) {
    logSuccess('\n🎉 All validations passed! Workspace is properly configured.');
    return 0;
  } else {
    logError(`\n⚠️ ${failedChecks} validation(s) failed. Please address the issues above.`);
    return 1;
  }
}

// =============================================================================
// MAIN EXECUTION
// =============================================================================

async function main() {
  logHeader('🔍 AI Trading Platform - Workspace Validation');

  const validationResults = {
    'Workspace Structure': await validateWorkspaceStructure(),
    'Package Configurations': await validatePackageConfigurations(),
    'TypeScript Configuration': await validateTypeScriptConfiguration(),
    'Docker Configuration': await validateDockerConfiguration(),
    'Build System': await validateBuildSystem(),
    'Service Dependencies': await validateServiceDependencies(),
    'Configuration Files': await validateConfigurationFiles(),
    'Scripts and Tools': await validateScriptsAndTools()
  };

  const exitCode = generateValidationReport(validationResults);

  if (exitCode === 0) {
    logHeader('🚀 Next Steps');
    log('1. Run: npm run setup (if not already done)');
    log('2. Start services: npm run dev');
    log('3. Check health: npm run health');
    log('4. View monitoring: http://localhost:3000 (Grafana)');
  }

  process.exit(exitCode);
}

// Show usage if help requested
if (process.argv.includes('--help') || process.argv.includes('-h')) {
  console.log(`
${COLORS.bright}AI Trading Platform - Workspace Validation${COLORS.reset}

Usage: node validate-workspace.js

This script validates:
  ✅ Workspace directory structure
  ✅ Package.json configurations
  ✅ TypeScript setup and project references
  ✅ Docker and Docker Compose configuration
  ✅ Build system functionality
  ✅ Inter-service dependencies
  ✅ Configuration files
  ✅ Scripts and tools

Exit Codes:
  0  All validations passed
  1  One or more validations failed
`);
  process.exit(0);
}

// Run validation
main().catch(error => {
  logError(`Validation failed: ${error.message}`);
  process.exit(1);
});