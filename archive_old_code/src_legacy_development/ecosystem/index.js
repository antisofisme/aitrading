/**
 * Entry point for the Collaborative Documentation Ecosystem
 * Provides easy access to initialize and manage the ecosystem
 */

const CollaborativeEcosystem = require('./CollaborativeEcosystem');
const EcosystemConfig = require('./config/EcosystemConfig');

// Singleton instance
let ecosystemInstance = null;

/**
 * Initialize and start the collaborative ecosystem
 */
async function createEcosystem(config = {}) {
  if (ecosystemInstance) {
    console.warn('⚠️ Ecosystem instance already exists');
    return ecosystemInstance;
  }

  try {
    console.log('🚀 Creating collaborative documentation ecosystem...');

    ecosystemInstance = new CollaborativeEcosystem(config);
    await ecosystemInstance.initialize();

    console.log('✅ Collaborative ecosystem created successfully');
    return ecosystemInstance;
  } catch (error) {
    console.error('❌ Failed to create ecosystem:', error);
    throw error;
  }
}

/**
 * Get the current ecosystem instance
 */
function getEcosystem() {
  if (!ecosystemInstance) {
    throw new Error('Ecosystem not initialized. Call createEcosystem() first.');
  }
  return ecosystemInstance;
}

/**
 * Start the ecosystem
 */
async function startEcosystem(config = {}) {
  const ecosystem = ecosystemInstance || await createEcosystem(config);
  await ecosystem.start();
  return ecosystem;
}

/**
 * Stop the ecosystem
 */
async function stopEcosystem() {
  if (ecosystemInstance) {
    await ecosystemInstance.stop();
    ecosystemInstance = null;
  }
}

/**
 * Quick setup for AI trading projects
 */
async function setupAiTradingEcosystem(customConfig = {}) {
  const aiTradingConfig = {
    contextDetection: {
      aiTradingDetection: {
        enabled: true,
        confidenceThreshold: 30 // Lower threshold for AI trading
      }
    },
    agents: {
      'algorithm-agent': { enabled: true, priority: 'high' },
      'api-agent': { enabled: true, priority: 'high' },
      'architecture-agent': { enabled: true, priority: 'medium' }
    },
    monitoring: {
      watchPaths: [
        'src/**',
        'strategies/**',
        'algorithms/**',
        'indicators/**',
        'api/**',
        'routes/**'
      ]
    },
    mermaid: {
      diagramTypes: {
        algorithm: true,
        architecture: true,
        api: true,
        sequence: true
      }
    },
    ...customConfig
  };

  return createEcosystem({ configOverrides: aiTradingConfig });
}

/**
 * CLI integration
 */
async function runFromCLI() {
  try {
    const args = process.argv.slice(2);
    const command = args[0];

    switch (command) {
      case 'start':
        console.log('🚀 Starting collaborative ecosystem from CLI...');
        await startEcosystem();

        // Keep process alive
        process.on('SIGINT', async () => {
          console.log('\n⏹️ Stopping ecosystem...');
          await stopEcosystem();
          process.exit(0);
        });
        break;

      case 'stop':
        console.log('⏹️ Stopping ecosystem...');
        await stopEcosystem();
        break;

      case 'status':
        const ecosystem = getEcosystem();
        const status = ecosystem.getStatus();
        console.log('📊 Ecosystem Status:', JSON.stringify(status, null, 2));
        break;

      case 'ai-trading':
        console.log('🤖 Setting up AI trading ecosystem...');
        const aiEcosystem = await setupAiTradingEcosystem();
        await aiEcosystem.start();
        break;

      default:
        console.log(`
Usage: node ecosystem/index.js <command>

Commands:
  start      - Start the collaborative ecosystem
  stop       - Stop the ecosystem
  status     - Show ecosystem status
  ai-trading - Setup for AI trading projects

Environment Variables:
  ECOSYSTEM_CONFIG_PATH - Path to configuration file
  NODE_ENV             - Environment (development, production)
        `);
    }
  } catch (error) {
    console.error('❌ CLI execution failed:', error);
    process.exit(1);
  }
}

// Export the API
module.exports = {
  createEcosystem,
  getEcosystem,
  startEcosystem,
  stopEcosystem,
  setupAiTradingEcosystem,
  CollaborativeEcosystem,
  EcosystemConfig
};

// CLI detection
if (require.main === module) {
  runFromCLI();
}