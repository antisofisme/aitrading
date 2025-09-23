/**
 * Global Test Teardown
 * Runs once after all tests complete
 */

module.exports = async () => {
  console.log('\n🧹 Cleaning up AI Pipeline Test Environment...');

  // Calculate total test duration
  const totalDuration = Date.now() - global.testStartTime;
  console.log(`⏱️  Total test duration: ${(totalDuration / 1000).toFixed(2)} seconds`);

  // Clean up any test artifacts
  const fs = require('fs');
  const path = require('path');

  // Remove temporary test files
  const tempFiles = [
    path.join(__dirname, '../../temp-test-data.json'),
    path.join(__dirname, '../../test-session.log')
  ];

  tempFiles.forEach(file => {
    if (fs.existsSync(file)) {
      try {
        fs.unlinkSync(file);
      } catch (error) {
        console.warn(`⚠️  Could not clean up temp file: ${file}`);
      }
    }
  });

  // Force garbage collection if available
  if (global.gc) {
    global.gc();
  }

  // Generate test completion summary
  const summary = {
    duration: totalDuration,
    timestamp: new Date().toISOString(),
    environment: {
      nodeVersion: process.version,
      platform: process.platform,
      memoryUsage: process.memoryUsage()
    }
  };

  // Save test summary
  try {
    fs.writeFileSync(
      path.join(__dirname, '../../test-results/test-summary.json'),
      JSON.stringify(summary, null, 2)
    );
  } catch (error) {
    console.warn('⚠️  Could not save test summary');
  }

  console.log('✅ Global test cleanup completed');
};