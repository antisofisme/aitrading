/**
 * Model Version Manager
 * Manages ML model versions, deployment, and rollback capabilities
 */

import { EventEmitter } from 'events';
import { ModelVersion, MLModelConfig, ModelPerformance } from '../types';

export class ModelVersionManager extends EventEmitter {
  private modelVersions: Map<string, ModelVersion[]> = new Map();
  private activeVersions: Map<string, string> = new Map();
  private deploymentHistory: Map<string, any[]> = new Map();
  private performanceMetrics: Map<string, ModelPerformance[]> = new Map();
  private lastUpdateTime: number = 0;
  private isInitialized: boolean = false;

  constructor() {
    super();
  }

  async initialize(): Promise<void> {
    try {
      console.log('Initializing Model Version Manager...');

      // Load existing model versions
      await this.loadModelVersions();

      // Load deployment history
      await this.loadDeploymentHistory();

      // Load performance metrics
      await this.loadPerformanceMetrics();

      this.isInitialized = true;
      console.log('Model Version Manager initialized');
    } catch (error) {
      console.error('Failed to initialize model version manager:', error);
      throw error;
    }
  }

  async createNewVersion(
    modelType: string,
    config: MLModelConfig,
    modelPath: string,
    performance: ModelPerformance
  ): Promise<string> {
    const version = this.generateVersionString();

    const modelVersion: ModelVersion = {
      version,
      createdAt: Date.now(),
      modelPath,
      config,
      performance,
      status: 'training'
    };

    // Add to versions list
    if (!this.modelVersions.has(modelType)) {
      this.modelVersions.set(modelType, []);
    }
    this.modelVersions.get(modelType)!.push(modelVersion);

    // Save to storage
    await this.saveModelVersion(modelType, modelVersion);

    this.emit('versionCreated', { modelType, version });
    return version;
  }

  async deployVersion(modelType: string, version: string): Promise<void> {
    const versions = this.modelVersions.get(modelType);
    if (!versions) {
      throw new Error(`No versions found for model type: ${modelType}`);
    }

    const targetVersion = versions.find(v => v.version === version);
    if (!targetVersion) {
      throw new Error(`Version ${version} not found for model type: ${modelType}`);
    }

    if (targetVersion.status !== 'validating' && targetVersion.status !== 'active') {
      throw new Error(`Cannot deploy version ${version} with status: ${targetVersion.status}`);
    }

    // Get current active version for rollback
    const currentActive = this.activeVersions.get(modelType);

    try {
      // Deploy new version
      await this.performDeployment(modelType, targetVersion);

      // Update status
      targetVersion.status = 'active';
      targetVersion.deployedAt = Date.now();
      if (currentActive) {
        targetVersion.rollbackVersion = currentActive;
      }

      // Deactivate previous version
      if (currentActive) {
        const previousVersion = versions.find(v => v.version === currentActive);
        if (previousVersion) {
          previousVersion.status = 'deprecated';
        }
      }

      // Set as active
      this.activeVersions.set(modelType, version);

      // Record deployment
      this.recordDeployment(modelType, version, 'deploy', true);

      this.emit('versionDeployed', { modelType, version, previousVersion: currentActive });
      console.log(`Successfully deployed ${modelType} version ${version}`);
    } catch (error) {
      this.recordDeployment(modelType, version, 'deploy', false, error);
      throw error;
    }
  }

  async rollbackVersion(modelType: string, targetVersion?: string): Promise<void> {
    const currentVersion = this.activeVersions.get(modelType);
    if (!currentVersion) {
      throw new Error(`No active version found for model type: ${modelType}`);
    }

    const versions = this.modelVersions.get(modelType)!;
    const current = versions.find(v => v.version === currentVersion);

    if (!current) {
      throw new Error(`Current version ${currentVersion} not found`);
    }

    // Determine rollback target
    const rollbackTo = targetVersion || current.rollbackVersion;
    if (!rollbackTo) {
      throw new Error('No rollback version available');
    }

    const rollbackVersion = versions.find(v => v.version === rollbackTo);
    if (!rollbackVersion) {
      throw new Error(`Rollback version ${rollbackTo} not found`);
    }

    try {
      // Perform rollback deployment
      await this.performDeployment(modelType, rollbackVersion);

      // Update statuses
      current.status = 'deprecated';
      rollbackVersion.status = 'active';
      rollbackVersion.deployedAt = Date.now();

      // Update active version
      this.activeVersions.set(modelType, rollbackTo);

      // Record rollback
      this.recordDeployment(modelType, rollbackTo, 'rollback', true);

      this.emit('versionRolledBack', {
        modelType,
        fromVersion: currentVersion,
        toVersion: rollbackTo
      });
      console.log(`Successfully rolled back ${modelType} from ${currentVersion} to ${rollbackTo}`);
    } catch (error) {
      this.recordDeployment(modelType, rollbackTo, 'rollback', false, error);
      throw error;
    }
  }

  async validateVersion(modelType: string, version: string): Promise<boolean> {
    const versions = this.modelVersions.get(modelType);
    if (!versions) {
      throw new Error(`No versions found for model type: ${modelType}`);
    }

    const targetVersion = versions.find(v => v.version === version);
    if (!targetVersion) {
      throw new Error(`Version ${version} not found`);
    }

    try {
      targetVersion.status = 'validating';

      // Perform validation tests
      const validationResults = await this.performValidation(modelType, targetVersion);

      if (validationResults.passed) {
        targetVersion.status = 'validating'; // Ready for deployment
        targetVersion.performance = validationResults.performance;

        this.emit('versionValidated', { modelType, version, results: validationResults });
        return true;
      } else {
        targetVersion.status = 'deprecated';
        this.emit('versionValidationFailed', { modelType, version, results: validationResults });
        return false;
      }
    } catch (error) {
      targetVersion.status = 'deprecated';
      console.error(`Validation failed for ${modelType} version ${version}:`, error);
      return false;
    }
  }

  async compareVersions(
    modelType: string,
    version1: string,
    version2: string
  ): Promise<any> {
    const versions = this.modelVersions.get(modelType);
    if (!versions) {
      throw new Error(`No versions found for model type: ${modelType}`);
    }

    const v1 = versions.find(v => v.version === version1);
    const v2 = versions.find(v => v.version === version2);

    if (!v1 || !v2) {
      throw new Error('One or both versions not found');
    }

    return {
      version1: v1.version,
      version2: v2.version,
      performance: {
        accuracy: {
          v1: v1.performance.accuracy,
          v2: v2.performance.accuracy,
          improvement: v2.performance.accuracy - v1.performance.accuracy
        },
        precision: {
          v1: v1.performance.precision,
          v2: v2.performance.precision,
          improvement: v2.performance.precision - v1.performance.precision
        },
        recall: {
          v1: v1.performance.recall,
          v2: v2.performance.recall,
          improvement: v2.performance.recall - v1.performance.recall
        },
        f1Score: {
          v1: v1.performance.f1Score,
          v2: v2.performance.f1Score,
          improvement: v2.performance.f1Score - v1.performance.f1Score
        }
      },
      config: {
        differences: this.compareConfigs(v1.config, v2.config)
      },
      recommendation: this.generateComparisonRecommendation(v1, v2)
    };
  }

  async getVersionHistory(modelType: string): Promise<ModelVersion[]> {
    const versions = this.modelVersions.get(modelType) || [];
    return versions.sort((a, b) => b.createdAt - a.createdAt);
  }

  async getActiveVersions(): Promise<Record<string, string>> {
    return Object.fromEntries(this.activeVersions.entries());
  }

  async getPerformanceHistory(modelType: string): Promise<ModelPerformance[]> {
    return this.performanceMetrics.get(modelType) || [];
  }

  async cleanupOldVersions(modelType: string, keepLatest: number = 5): Promise<void> {
    const versions = this.modelVersions.get(modelType);
    if (!versions) return;

    // Sort by creation date (newest first)
    const sortedVersions = versions.sort((a, b) => b.createdAt - a.createdAt);

    // Keep active version and specified number of latest versions
    const activeVersion = this.activeVersions.get(modelType);
    const toKeep = new Set<string>();

    if (activeVersion) {
      toKeep.add(activeVersion);
    }

    // Add latest versions
    sortedVersions.slice(0, keepLatest).forEach(v => toKeep.add(v.version));

    // Remove old versions
    const toRemove = sortedVersions.filter(v => !toKeep.has(v.version));

    for (const version of toRemove) {
      await this.removeVersion(modelType, version.version);
    }

    console.log(`Cleaned up ${toRemove.length} old versions for ${modelType}`);
  }

  async exportModel(modelType: string, version: string): Promise<Buffer> {
    const versions = this.modelVersions.get(modelType);
    if (!versions) {
      throw new Error(`No versions found for model type: ${modelType}`);
    }

    const targetVersion = versions.find(v => v.version === version);
    if (!targetVersion) {
      throw new Error(`Version ${version} not found`);
    }

    // Mock export - would read actual model file
    const exportData = {
      modelType,
      version: targetVersion.version,
      config: targetVersion.config,
      performance: targetVersion.performance,
      metadata: {
        createdAt: targetVersion.createdAt,
        exportedAt: Date.now()
      }
    };

    return Buffer.from(JSON.stringify(exportData, null, 2));
  }

  async importModel(modelType: string, modelData: Buffer): Promise<string> {
    try {
      const importData = JSON.parse(modelData.toString());

      // Validate import data
      if (!importData.version || !importData.config) {
        throw new Error('Invalid model data format');
      }

      // Create new version from import
      const version = await this.createNewVersion(
        modelType,
        importData.config,
        `imported_${importData.version}`,
        importData.performance || {
          accuracy: 0,
          precision: 0,
          recall: 0,
          f1Score: 0,
          auc: 0,
          lastEvaluated: Date.now(),
          validationMethod: 'imported'
        }
      );

      console.log(`Successfully imported ${modelType} version ${version}`);
      return version;
    } catch (error) {
      console.error('Failed to import model:', error);
      throw error;
    }
  }

  async createNewVersions(): Promise<void> {
    // This would be called after training new models
    const modelTypes = ['anomaly', 'pattern', 'prediction'];

    for (const modelType of modelTypes) {
      const newVersion = await this.createNewVersion(
        modelType,
        this.getDefaultConfig(modelType),
        `models/${modelType}_${Date.now()}`,
        this.getDefaultPerformance()
      );

      console.log(`Created new ${modelType} model version: ${newVersion}`);
    }

    this.lastUpdateTime = Date.now();
  }

  getLastUpdateTime(): number {
    return this.lastUpdateTime;
  }

  private generateVersionString(): string {
    const date = new Date();
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hour = String(date.getHours()).padStart(2, '0');
    const minute = String(date.getMinutes()).padStart(2, '0');

    return `v${year}.${month}.${day}.${hour}${minute}`;
  }

  private async loadModelVersions(): Promise<void> {
    // Mock loading from storage
    console.log('Loading model versions from storage...');
  }

  private async loadDeploymentHistory(): Promise<void> {
    // Mock loading deployment history
    console.log('Loading deployment history...');
  }

  private async loadPerformanceMetrics(): Promise<void> {
    // Mock loading performance metrics
    console.log('Loading performance metrics...');
  }

  private async saveModelVersion(modelType: string, version: ModelVersion): Promise<void> {
    // Mock saving to storage
    console.log(`Saving ${modelType} version ${version.version} to storage...`);
  }

  private async performDeployment(modelType: string, version: ModelVersion): Promise<void> {
    // Mock deployment process
    console.log(`Deploying ${modelType} version ${version.version}...`);

    // Simulate deployment time
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  private recordDeployment(
    modelType: string,
    version: string,
    action: 'deploy' | 'rollback',
    success: boolean,
    error?: any
  ): void {
    if (!this.deploymentHistory.has(modelType)) {
      this.deploymentHistory.set(modelType, []);
    }

    this.deploymentHistory.get(modelType)!.push({
      version,
      action,
      success,
      timestamp: Date.now(),
      error: error?.message
    });
  }

  private async performValidation(
    modelType: string,
    version: ModelVersion
  ): Promise<{ passed: boolean; performance: ModelPerformance }> {
    // Mock validation process
    console.log(`Validating ${modelType} version ${version.version}...`);

    // Simulate validation time
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Mock validation results
    const performance: ModelPerformance = {
      accuracy: 0.85 + Math.random() * 0.1,
      precision: 0.8 + Math.random() * 0.15,
      recall: 0.8 + Math.random() * 0.15,
      f1Score: 0.8 + Math.random() * 0.15,
      auc: 0.85 + Math.random() * 0.1,
      lastEvaluated: Date.now(),
      validationMethod: 'cross_validation'
    };

    const passed = performance.accuracy > 0.8 && performance.f1Score > 0.75;

    return { passed, performance };
  }

  private compareConfigs(config1: MLModelConfig, config2: MLModelConfig): any {
    return {
      modelType: config1.modelType !== config2.modelType,
      parameters: JSON.stringify(config1.parameters) !== JSON.stringify(config2.parameters),
      features: config1.features.length !== config2.features.length ||
                !config1.features.every(f => config2.features.includes(f))
    };
  }

  private generateComparisonRecommendation(v1: ModelVersion, v2: ModelVersion): string {
    const p1 = v1.performance;
    const p2 = v2.performance;

    if (p2.accuracy > p1.accuracy && p2.f1Score > p1.f1Score) {
      return `Version ${v2.version} shows superior performance and should be deployed`;
    } else if (p1.accuracy > p2.accuracy && p1.f1Score > p2.f1Score) {
      return `Version ${v1.version} maintains better performance and should be kept active`;
    } else {
      return 'Mixed performance results - requires detailed analysis before deployment decision';
    }
  }

  private async removeVersion(modelType: string, version: string): Promise<void> {
    const versions = this.modelVersions.get(modelType);
    if (!versions) return;

    const index = versions.findIndex(v => v.version === version);
    if (index !== -1) {
      versions.splice(index, 1);
      console.log(`Removed ${modelType} version ${version}`);
    }
  }

  private getDefaultConfig(modelType: string): MLModelConfig {
    return {
      modelType: modelType as any,
      version: '1.0.0',
      parameters: {},
      features: ['executionTime', 'errorCount', 'memoryUsage'],
      trainingData: {
        startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
        endDate: new Date().toISOString(),
        sampleSize: 10000
      },
      performance: this.getDefaultPerformance()
    };
  }

  private getDefaultPerformance(): ModelPerformance {
    return {
      accuracy: 0.8,
      precision: 0.75,
      recall: 0.8,
      f1Score: 0.77,
      auc: 0.85,
      lastEvaluated: Date.now(),
      validationMethod: 'holdout'
    };
  }
}