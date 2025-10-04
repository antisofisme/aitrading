/**
 * Central Hub SDK - Node.js/TypeScript
 *
 * Official client library for integrating services with Suho Central Hub
 *
 * @module @suho/central-hub-sdk
 * @version 1.0.0
 */

const CentralHubClient = require('./CentralHubClient');

module.exports = {
    CentralHubClient,
    // Convenience factory
    createClient: (options) => new CentralHubClient(options)
};

// ES6 default export
module.exports.default = CentralHubClient;
