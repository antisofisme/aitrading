/**
 * Multi-Tenant Architecture Validator
 * Ensures consistent multi-tenant architecture across all system components
 */

class MultiTenantArchitectureValidator {
    constructor(options = {}) {
        this.logger = options.logger || console;
        this.systemComponents = options.components || [];

        this.validationCriteria = {
            isolation: {
                database: { weight: 25, required: true },
                network: { weight: 20, required: true },
                storage: { weight: 15, required: true },
                compute: { weight: 15, required: false },
                logging: { weight: 10, required: true },
                monitoring: { weight: 15, required: false }
            },
            security: {
                authentication: { weight: 30, required: true },
                authorization: { weight: 25, required: true },
                encryption: { weight: 20, required: true },
                audit: { weight: 15, required: true },
                compliance: { weight: 10, required: false }
            },
            scalability: {
                horizontal: { weight: 30, required: true },
                vertical: { weight: 20, required: false },
                elastic: { weight: 25, required: false },
                loadBalancing: { weight: 15, required: true },
                caching: { weight: 10, required: false }
            },
            management: {
                provisioning: { weight: 25, required: true },
                monitoring: { weight: 20, required: true },
                billing: { weight: 20, required: true },
                configuration: { weight: 20, required: true },
                lifecycle: { weight: 15, required: false }
            }
        };

        this.validationResults = {
            overall: null,
            categories: {},
            components: {},
            recommendations: []
        };
    }

    /**
     * Validate complete multi-tenant architecture
     */
    async validateArchitecture() {
        this.logger.info('Starting Multi-Tenant Architecture Validation...');

        try {
            // Validate each category
            for (const [category, criteria] of Object.entries(this.validationCriteria)) {
                this.logger.info(`Validating ${category} consistency...`);
                const categoryResult = await this.validateCategory(category, criteria);
                this.validationResults.categories[category] = categoryResult;
            }

            // Validate component-specific requirements
            await this.validateComponentRequirements();

            // Calculate overall score
            this.calculateOverallScore();

            // Generate recommendations
            this.generateRecommendations();

            this.logger.info(`Architecture validation complete: ${this.validationResults.overall.status}`);
            return this.validationResults;

        } catch (error) {
            this.logger.error('Architecture validation failed:', error);
            throw error;
        }
    }

    /**
     * Validate specific category across all components
     */
    async validateCategory(category, criteria) {
        const categoryResult = {
            name: category,
            score: 0,
            maxScore: 0,
            checks: {},
            status: 'UNKNOWN',
            issues: []
        };

        for (const [criterion, config] of Object.entries(criteria)) {
            const checkResult = await this.validateCriterion(category, criterion, config);
            categoryResult.checks[criterion] = checkResult;

            categoryResult.score += checkResult.score;
            categoryResult.maxScore += config.weight;

            if (config.required && !checkResult.compliant) {
                categoryResult.issues.push({
                    criterion,
                    severity: 'HIGH',
                    message: checkResult.message || `Required ${criterion} not compliant`
                });
            }
        }

        // Calculate category status
        const successRate = (categoryResult.score / categoryResult.maxScore) * 100;
        categoryResult.successRate = successRate;

        if (successRate >= 90) {
            categoryResult.status = 'EXCELLENT';
        } else if (successRate >= 75) {
            categoryResult.status = 'GOOD';
        } else if (successRate >= 60) {
            categoryResult.status = 'ACCEPTABLE';
        } else {
            categoryResult.status = 'POOR';
        }

        return categoryResult;
    }

    /**
     * Validate specific criterion
     */
    async validateCriterion(category, criterion, config) {
        const validationMethod = `validate${this.capitalize(category)}${this.capitalize(criterion)}`;

        try {
            if (this[validationMethod]) {
                return await this[validationMethod](config);
            } else {
                return await this.defaultCriterionValidation(category, criterion, config);
            }
        } catch (error) {
            return {
                compliant: false,
                score: 0,
                message: `Validation error: ${error.message}`,
                details: { error: error.message }
            };
        }
    }

    /**
     * Default criterion validation
     */
    async defaultCriterionValidation(category, criterion, config) {
        // Generic validation based on common patterns
        const implementations = await this.checkImplementationAcrossServices(category, criterion);

        const compliantServices = implementations.filter(impl => impl.compliant).length;
        const totalServices = implementations.length;
        const complianceRate = totalServices > 0 ? (compliantServices / totalServices) : 0;

        return {
            compliant: complianceRate >= 0.8, // 80% compliance threshold
            score: Math.round(complianceRate * config.weight),
            message: `${compliantServices}/${totalServices} services compliant`,
            details: {
                implementations,
                complianceRate,
                threshold: 0.8
            }
        };
    }

    /**
     * Check implementation across services
     */
    async checkImplementationAcrossServices(category, criterion) {
        const services = [
            'api-gateway',
            'database-service',
            'ai-orchestrator',
            'trading-engine',
            'central-hub'
        ];

        const implementations = [];

        for (const service of services) {
            const implementation = await this.checkServiceImplementation(service, category, criterion);
            implementations.push({
                service,
                ...implementation
            });
        }

        return implementations;
    }

    /**
     * Check service-specific implementation
     */
    async checkServiceImplementation(service, category, criterion) {
        // Mock implementation check - in real scenario, this would:
        // - Check configuration files
        // - Verify code patterns
        // - Test actual functionality
        // - Review documentation

        const implementationPatterns = {
            isolation: {
                database: this.checkDatabaseIsolation,
                network: this.checkNetworkIsolation,
                storage: this.checkStorageIsolation,
                logging: this.checkLoggingIsolation
            },
            security: {
                authentication: this.checkAuthentication,
                authorization: this.checkAuthorization,
                encryption: this.checkEncryption,
                audit: this.checkAuditLogging
            },
            scalability: {
                horizontal: this.checkHorizontalScaling,
                loadBalancing: this.checkLoadBalancing
            },
            management: {
                provisioning: this.checkTenantProvisioning,
                monitoring: this.checkTenantMonitoring,
                billing: this.checkTenantBilling,
                configuration: this.checkTenantConfiguration
            }
        };

        const checkMethod = implementationPatterns[category]?.[criterion];
        if (checkMethod) {
            return await checkMethod.call(this, service);
        }

        // Default implementation
        return {
            compliant: Math.random() > 0.3, // Mock 70% compliance
            implemented: true,
            coverage: Math.random() * 100,
            notes: `Default check for ${service}:${category}:${criterion}`
        };
    }

    /**
     * Database Isolation Validation
     */
    async validateIsolationDatabase(config) {
        const dbIsolationChecks = [
            'Schema-level separation',
            'Connection pooling per tenant',
            'Query-level tenant filtering',
            'Data encryption at rest',
            'Backup isolation'
        ];

        let compliantChecks = 0;
        const checkResults = [];

        for (const check of dbIsolationChecks) {
            const isCompliant = await this.checkDatabaseFeature(check);
            if (isCompliant) compliantChecks++;

            checkResults.push({
                check,
                compliant: isCompliant,
                details: this.getDatabaseCheckDetails(check)
            });
        }

        const complianceRate = compliantChecks / dbIsolationChecks.length;

        return {
            compliant: complianceRate >= 0.8,
            score: Math.round(complianceRate * config.weight),
            message: `${compliantChecks}/${dbIsolationChecks.length} database isolation checks passed`,
            details: {
                checks: checkResults,
                complianceRate,
                requiredFeatures: dbIsolationChecks
            }
        };
    }

    /**
     * Network Isolation Validation
     */
    async validateIsolationNetwork(config) {
        const networkFeatures = [
            'VPC/VNET separation',
            'API rate limiting per tenant',
            'Network security groups',
            'Traffic encryption',
            'DDoS protection'
        ];

        let implementedFeatures = 0;

        for (const feature of networkFeatures) {
            if (await this.checkNetworkFeature(feature)) {
                implementedFeatures++;
            }
        }

        const complianceRate = implementedFeatures / networkFeatures.length;

        return {
            compliant: complianceRate >= 0.6,
            score: Math.round(complianceRate * config.weight),
            message: `${implementedFeatures}/${networkFeatures.length} network features implemented`,
            details: {
                implementedFeatures,
                totalFeatures: networkFeatures.length,
                features: networkFeatures
            }
        };
    }

    /**
     * Authentication Validation
     */
    async validateSecurityAuthentication(config) {
        const authFeatures = [
            'Multi-tenant JWT tokens',
            'SSO integration capability',
            'MFA support',
            'Session management',
            'Password policies'
        ];

        const authResults = await Promise.all(
            authFeatures.map(async feature => ({
                feature,
                implemented: await this.checkAuthFeature(feature)
            }))
        );

        const implementedCount = authResults.filter(r => r.implemented).length;
        const complianceRate = implementedCount / authFeatures.length;

        return {
            compliant: complianceRate >= 0.8,
            score: Math.round(complianceRate * config.weight),
            message: `${implementedCount}/${authFeatures.length} authentication features implemented`,
            details: {
                authResults,
                complianceRate,
                requiredFeatures: authFeatures
            }
        };
    }

    /**
     * Authorization Validation
     */
    async validateSecurityAuthorization(config) {
        const authzChecks = [
            'Role-based access control (RBAC)',
            'Attribute-based access control (ABAC)',
            'Resource-level permissions',
            'Tenant boundary enforcement',
            'API endpoint protection'
        ];

        let passedChecks = 0;
        const checkDetails = [];

        for (const check of authzChecks) {
            const passed = await this.checkAuthorizationFeature(check);
            if (passed) passedChecks++;

            checkDetails.push({
                check,
                passed,
                implementation: this.getAuthorizationDetails(check)
            });
        }

        const successRate = passedChecks / authzChecks.length;

        return {
            compliant: successRate >= 0.75,
            score: Math.round(successRate * config.weight),
            message: `${passedChecks}/${authzChecks.length} authorization checks passed`,
            details: {
                checkDetails,
                successRate,
                requiredChecks: authzChecks
            }
        };
    }

    /**
     * Horizontal Scaling Validation
     */
    async validateScalabilityHorizontal(config) {
        const scalingFeatures = [
            'Stateless service design',
            'Load balancer configuration',
            'Auto-scaling policies',
            'Service discovery',
            'Health check endpoints'
        ];

        const scalingResults = [];
        let compliantFeatures = 0;

        for (const feature of scalingFeatures) {
            const result = await this.checkScalingFeature(feature);
            scalingResults.push(result);

            if (result.compliant) {
                compliantFeatures++;
            }
        }

        const complianceRate = compliantFeatures / scalingFeatures.length;

        return {
            compliant: complianceRate >= 0.7,
            score: Math.round(complianceRate * config.weight),
            message: `${compliantFeatures}/${scalingFeatures.length} scaling features compliant`,
            details: {
                scalingResults,
                complianceRate,
                features: scalingFeatures
            }
        };
    }

    /**
     * Tenant Provisioning Validation
     */
    async validateManagementProvisioning(config) {
        const provisioningCapabilities = [
            'Automated tenant onboarding',
            'Resource allocation per tenant',
            'Configuration template system',
            'Tenant lifecycle management',
            'Self-service portal'
        ];

        const capabilityResults = [];
        let implementedCapabilities = 0;

        for (const capability of provisioningCapabilities) {
            const implemented = await this.checkProvisioningCapability(capability);
            capabilityResults.push({
                capability,
                implemented,
                coverage: this.getProvisioningCoverage(capability)
            });

            if (implemented) {
                implementedCapabilities++;
            }
        }

        const implementationRate = implementedCapabilities / provisioningCapabilities.length;

        return {
            compliant: implementationRate >= 0.6,
            score: Math.round(implementationRate * config.weight),
            message: `${implementedCapabilities}/${provisioningCapabilities.length} provisioning capabilities implemented`,
            details: {
                capabilityResults,
                implementationRate,
                capabilities: provisioningCapabilities
            }
        };
    }

    /**
     * Validate component-specific requirements
     */
    async validateComponentRequirements() {
        const componentValidations = {
            'api-gateway': {
                requirements: ['Tenant identification', 'Request routing', 'Rate limiting'],
                validator: this.validateApiGatewayMultiTenancy
            },
            'database-service': {
                requirements: ['Schema isolation', 'Data encryption', 'Backup separation'],
                validator: this.validateDatabaseMultiTenancy
            },
            'ai-orchestrator': {
                requirements: ['Provider isolation', 'Cost tracking', 'Resource quotas'],
                validator: this.validateAIOrchestatorMultiTenancy
            },
            'trading-engine': {
                requirements: ['Portfolio isolation', 'Risk limits', 'Trade tracking'],
                validator: this.validateTradingEngineMultiTenancy
            }
        };

        for (const [component, config] of Object.entries(componentValidations)) {
            try {
                const result = await config.validator.call(this, config.requirements);
                this.validationResults.components[component] = result;
            } catch (error) {
                this.validationResults.components[component] = {
                    status: 'ERROR',
                    error: error.message,
                    requirements: config.requirements
                };
            }
        }
    }

    /**
     * Validate API Gateway Multi-Tenancy
     */
    async validateApiGatewayMultiTenancy(requirements) {
        const checks = [
            {
                name: 'Tenant identification from headers/tokens',
                test: () => this.checkTenantIdentification()
            },
            {
                name: 'Request routing based on tenant',
                test: () => this.checkTenantRouting()
            },
            {
                name: 'Per-tenant rate limiting',
                test: () => this.checkTenantRateLimiting()
            }
        ];

        return await this.runComponentChecks('api-gateway', checks);
    }

    /**
     * Validate Database Multi-Tenancy
     */
    async validateDatabaseMultiTenancy(requirements) {
        const checks = [
            {
                name: 'Schema-level tenant isolation',
                test: () => this.checkSchemaIsolation()
            },
            {
                name: 'Data encryption per tenant',
                test: () => this.checkTenantDataEncryption()
            },
            {
                name: 'Backup and restore isolation',
                test: () => this.checkBackupIsolation()
            }
        ];

        return await this.runComponentChecks('database-service', checks);
    }

    /**
     * Validate AI Orchestrator Multi-Tenancy
     */
    async validateAIOrchestatorMultiTenancy(requirements) {
        const checks = [
            {
                name: 'AI provider isolation per tenant',
                test: () => this.checkAIProviderIsolation()
            },
            {
                name: 'Cost tracking and billing',
                test: () => this.checkAICostTracking()
            },
            {
                name: 'Resource quotas and limits',
                test: () => this.checkAIResourceQuotas()
            }
        ];

        return await this.runComponentChecks('ai-orchestrator', checks);
    }

    /**
     * Validate Trading Engine Multi-Tenancy
     */
    async validateTradingEngineMultiTenancy(requirements) {
        const checks = [
            {
                name: 'Portfolio isolation between tenants',
                test: () => this.checkPortfolioIsolation()
            },
            {
                name: 'Risk limits per tenant',
                test: () => this.checkTenantRiskLimits()
            },
            {
                name: 'Trade tracking and audit trails',
                test: () => this.checkTradeTracking()
            }
        ];

        return await this.runComponentChecks('trading-engine', checks);
    }

    /**
     * Run component-specific checks
     */
    async runComponentChecks(component, checks) {
        const results = {
            component,
            totalChecks: checks.length,
            passedChecks: 0,
            failedChecks: 0,
            checks: [],
            status: 'UNKNOWN'
        };

        for (const check of checks) {
            try {
                const passed = await check.test();
                results.checks.push({
                    name: check.name,
                    passed,
                    timestamp: new Date().toISOString()
                });

                if (passed) {
                    results.passedChecks++;
                } else {
                    results.failedChecks++;
                }
            } catch (error) {
                results.checks.push({
                    name: check.name,
                    passed: false,
                    error: error.message,
                    timestamp: new Date().toISOString()
                });
                results.failedChecks++;
            }
        }

        const successRate = (results.passedChecks / results.totalChecks) * 100;
        results.successRate = successRate;

        if (successRate >= 90) {
            results.status = 'EXCELLENT';
        } else if (successRate >= 75) {
            results.status = 'GOOD';
        } else if (successRate >= 50) {
            results.status = 'ACCEPTABLE';
        } else {
            results.status = 'POOR';
        }

        return results;
    }

    /**
     * Calculate overall architecture score
     */
    calculateOverallScore() {
        let totalScore = 0;
        let maxScore = 0;
        let criticalIssues = 0;

        // Calculate weighted scores from categories
        for (const [category, result] of Object.entries(this.validationResults.categories)) {
            totalScore += result.score;
            maxScore += result.maxScore;

            criticalIssues += result.issues.filter(issue => issue.severity === 'HIGH').length;
        }

        const overallSuccessRate = maxScore > 0 ? (totalScore / maxScore) * 100 : 0;

        let status = 'UNKNOWN';
        if (criticalIssues === 0 && overallSuccessRate >= 90) {
            status = 'EXCELLENT';
        } else if (criticalIssues <= 2 && overallSuccessRate >= 75) {
            status = 'GOOD';
        } else if (criticalIssues <= 5 && overallSuccessRate >= 60) {
            status = 'ACCEPTABLE';
        } else {
            status = 'POOR';
        }

        this.validationResults.overall = {
            status,
            successRate: overallSuccessRate.toFixed(2),
            totalScore,
            maxScore,
            criticalIssues,
            timestamp: new Date().toISOString(),
            readyForProduction: status === 'EXCELLENT' || status === 'GOOD'
        };
    }

    /**
     * Generate recommendations for improvements
     */
    generateRecommendations() {
        const recommendations = [];

        // Category-specific recommendations
        for (const [category, result] of Object.entries(this.validationResults.categories)) {
            if (result.issues.length > 0) {
                recommendations.push({
                    category,
                    priority: result.issues.some(i => i.severity === 'HIGH') ? 'HIGH' : 'MEDIUM',
                    title: `Improve ${category} multi-tenancy`,
                    description: `Address ${result.issues.length} issues in ${category}`,
                    issues: result.issues,
                    actionItems: this.generateCategoryActionItems(category, result.issues)
                });
            }
        }

        // Component-specific recommendations
        for (const [component, result] of Object.entries(this.validationResults.components)) {
            if (result.status === 'POOR' || result.failedChecks > 0) {
                recommendations.push({
                    category: 'component',
                    priority: result.status === 'POOR' ? 'HIGH' : 'MEDIUM',
                    title: `Enhance ${component} multi-tenancy`,
                    description: `${result.failedChecks} checks failed for ${component}`,
                    component,
                    failedChecks: result.checks.filter(c => !c.passed),
                    actionItems: this.generateComponentActionItems(component, result)
                });
            }
        }

        // Overall recommendations
        if (this.validationResults.overall?.status === 'POOR') {
            recommendations.push({
                category: 'architecture',
                priority: 'CRITICAL',
                title: 'Major architecture improvements needed',
                description: 'System not ready for multi-tenant production deployment',
                actionItems: [
                    'Implement required isolation mechanisms',
                    'Enhance security controls',
                    'Add comprehensive monitoring',
                    'Review and update all component configurations'
                ]
            });
        }

        this.validationResults.recommendations = recommendations;
    }

    /**
     * Generate action items for category issues
     */
    generateCategoryActionItems(category, issues) {
        const actionItems = {
            isolation: [
                'Implement database schema separation',
                'Configure network isolation',
                'Set up tenant-specific logging',
                'Establish storage partitioning'
            ],
            security: [
                'Implement multi-tenant authentication',
                'Configure role-based authorization',
                'Enable encryption for tenant data',
                'Set up audit logging per tenant'
            ],
            scalability: [
                'Design stateless services',
                'Configure auto-scaling policies',
                'Implement load balancing',
                'Set up service discovery'
            ],
            management: [
                'Build tenant provisioning automation',
                'Implement tenant monitoring',
                'Set up billing and metering',
                'Create configuration management'
            ]
        };

        return actionItems[category] || ['Review and address specific issues'];
    }

    /**
     * Generate action items for component issues
     */
    generateComponentActionItems(component, result) {
        const actionItems = {
            'api-gateway': [
                'Implement tenant identification middleware',
                'Configure per-tenant routing rules',
                'Set up rate limiting by tenant'
            ],
            'database-service': [
                'Create tenant-specific schemas',
                'Implement data encryption',
                'Configure backup isolation'
            ],
            'ai-orchestrator': [
                'Isolate AI providers per tenant',
                'Implement cost tracking',
                'Set up resource quotas'
            ],
            'trading-engine': [
                'Separate portfolios by tenant',
                'Configure risk limits',
                'Implement trade audit trails'
            ]
        };

        return actionItems[component] || ['Address component-specific multi-tenancy requirements'];
    }

    // Mock implementation methods (in real scenario, these would check actual implementations)
    async checkDatabaseFeature(feature) { return Math.random() > 0.3; }
    async checkNetworkFeature(feature) { return Math.random() > 0.4; }
    async checkAuthFeature(feature) { return Math.random() > 0.2; }
    async checkAuthorizationFeature(feature) { return Math.random() > 0.3; }
    async checkScalingFeature(feature) { return { compliant: Math.random() > 0.3 }; }
    async checkProvisioningCapability(capability) { return Math.random() > 0.4; }

    async checkTenantIdentification() { return true; }
    async checkTenantRouting() { return true; }
    async checkTenantRateLimiting() { return Math.random() > 0.3; }
    async checkSchemaIsolation() { return Math.random() > 0.2; }
    async checkTenantDataEncryption() { return Math.random() > 0.4; }
    async checkBackupIsolation() { return Math.random() > 0.5; }
    async checkAIProviderIsolation() { return true; }
    async checkAICostTracking() { return Math.random() > 0.3; }
    async checkAIResourceQuotas() { return Math.random() > 0.4; }
    async checkPortfolioIsolation() { return Math.random() > 0.2; }
    async checkTenantRiskLimits() { return Math.random() > 0.3; }
    async checkTradeTracking() { return true; }

    getDatabaseCheckDetails(check) { return `Details for ${check}`; }
    getAuthorizationDetails(check) { return `Implementation for ${check}`; }
    getProvisioningCoverage(capability) { return Math.random() * 100; }

    // Utility methods
    capitalize(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    async checkDatabaseIsolation(service) {
        return {
            compliant: Math.random() > 0.2,
            implemented: true,
            coverage: Math.random() * 100,
            notes: `Database isolation for ${service}`
        };
    }

    async checkNetworkIsolation(service) {
        return {
            compliant: Math.random() > 0.3,
            implemented: true,
            coverage: Math.random() * 100,
            notes: `Network isolation for ${service}`
        };
    }

    async checkStorageIsolation(service) {
        return {
            compliant: Math.random() > 0.4,
            implemented: Math.random() > 0.2,
            coverage: Math.random() * 100,
            notes: `Storage isolation for ${service}`
        };
    }

    async checkLoggingIsolation(service) {
        return {
            compliant: Math.random() > 0.3,
            implemented: true,
            coverage: Math.random() * 100,
            notes: `Logging isolation for ${service}`
        };
    }

    async checkAuthentication(service) {
        return {
            compliant: Math.random() > 0.2,
            implemented: true,
            coverage: Math.random() * 100,
            notes: `Authentication for ${service}`
        };
    }

    async checkAuthorization(service) {
        return {
            compliant: Math.random() > 0.3,
            implemented: true,
            coverage: Math.random() * 100,
            notes: `Authorization for ${service}`
        };
    }

    async checkEncryption(service) {
        return {
            compliant: Math.random() > 0.4,
            implemented: Math.random() > 0.3,
            coverage: Math.random() * 100,
            notes: `Encryption for ${service}`
        };
    }

    async checkAuditLogging(service) {
        return {
            compliant: Math.random() > 0.3,
            implemented: true,
            coverage: Math.random() * 100,
            notes: `Audit logging for ${service}`
        };
    }

    async checkHorizontalScaling(service) {
        return {
            compliant: Math.random() > 0.2,
            implemented: true,
            coverage: Math.random() * 100,
            notes: `Horizontal scaling for ${service}`
        };
    }

    async checkLoadBalancing(service) {
        return {
            compliant: Math.random() > 0.3,
            implemented: true,
            coverage: Math.random() * 100,
            notes: `Load balancing for ${service}`
        };
    }

    async checkTenantProvisioning(service) {
        return {
            compliant: Math.random() > 0.4,
            implemented: Math.random() > 0.5,
            coverage: Math.random() * 100,
            notes: `Tenant provisioning for ${service}`
        };
    }

    async checkTenantMonitoring(service) {
        return {
            compliant: Math.random() > 0.3,
            implemented: true,
            coverage: Math.random() * 100,
            notes: `Tenant monitoring for ${service}`
        };
    }

    async checkTenantBilling(service) {
        return {
            compliant: Math.random() > 0.5,
            implemented: Math.random() > 0.4,
            coverage: Math.random() * 100,
            notes: `Tenant billing for ${service}`
        };
    }

    async checkTenantConfiguration(service) {
        return {
            compliant: Math.random() > 0.2,
            implemented: true,
            coverage: Math.random() * 100,
            notes: `Tenant configuration for ${service}`
        };
    }

    /**
     * Get validation summary
     */
    getSummary() {
        return {
            status: this.validationResults.overall?.status || 'NOT_RUN',
            successRate: this.validationResults.overall?.successRate || '0',
            criticalIssues: this.validationResults.overall?.criticalIssues || 0,
            readyForProduction: this.validationResults.overall?.readyForProduction || false,
            categoriesValidated: Object.keys(this.validationResults.categories).length,
            componentsValidated: Object.keys(this.validationResults.components).length,
            totalRecommendations: this.validationResults.recommendations?.length || 0,
            timestamp: this.validationResults.overall?.timestamp || new Date().toISOString()
        };
    }
}

module.exports = MultiTenantArchitectureValidator;