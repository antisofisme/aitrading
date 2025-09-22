/**
 * AnomalyDetector
 * ML-powered anomaly detection for chain health monitoring
 */

import { Matrix } from 'ml-matrix';
import logger from '../utils/logger.js';
import { Anomaly } from '../models/Anomaly.js';

export class AnomalyDetector {
  constructor({ database, redis }) {
    this.database = database;
    this.redis = redis;

    this.models = {};
    this.trainedModels = new Map();
    this.featureExtractors = new Map();

    // Model configuration
    this.config = {
      windowSize: 50, // Number of historical points for analysis
      threshold: parseFloat(process.env.ANOMALY_DETECTION_THRESHOLD) || 0.8,
      minTrainingData: 100,
      retrainInterval: 86400000, // 24 hours
      features: [
        'duration_p99',
        'duration_avg',
        'error_rate',
        'dependency_failure_rate',
        'request_count',
        'health_score'
      ]
    };

    this.isInitialized = false;
  }

  async initialize() {
    try {
      logger.info('Initializing AnomalyDetector...');

      // Load or train models for different chain types
      await this.loadModels();

      // Initialize feature extractors
      this.initializeFeatureExtractors();

      this.isInitialized = true;
      logger.info('AnomalyDetector initialized successfully');

    } catch (error) {
      logger.error('Failed to initialize AnomalyDetector:', error);
      throw error;
    }
  }

  async detectAnomalies(healthMetrics, baseline) {
    try {
      if (!this.isInitialized) {
        logger.warn('AnomalyDetector not initialized, skipping ML detection');
        return [];
      }

      const anomalies = [];

      // Extract features from health metrics
      const features = this.extractFeatures(healthMetrics, baseline);

      // Get or create model for this chain type
      const chainType = this.determineChainType(healthMetrics.chainId);
      const model = await this.getModel(chainType);

      if (!model) {
        logger.debug(`No trained model available for chain type: ${chainType}`);
        return anomalies;
      }

      // Detect anomalies using different techniques
      const statisticalAnomalies = this.detectStatisticalAnomalies(features, baseline);
      const patternAnomalies = await this.detectPatternAnomalies(features, model);
      const timeSeriesAnomalies = this.detectTimeSeriesAnomalies(healthMetrics, baseline);

      // Combine and deduplicate anomalies
      anomalies.push(...statisticalAnomalies);
      anomalies.push(...patternAnomalies);
      anomalies.push(...timeSeriesAnomalies);

      // Filter by confidence threshold
      const filteredAnomalies = anomalies.filter(anomaly =>
        anomaly.confidence >= this.config.threshold
      );

      logger.debug(`Detected ${filteredAnomalies.length} ML anomalies for chain ${healthMetrics.chainId}`);

      return filteredAnomalies;

    } catch (error) {
      logger.error('Failed to detect anomalies:', error);
      return [];
    }
  }

  extractFeatures(healthMetrics, baseline) {
    const features = {};

    // Current metrics
    features.duration_p99 = healthMetrics.p99Duration || 0;
    features.duration_avg = healthMetrics.avgDuration || 0;
    features.error_rate = healthMetrics.errorRate || 0;
    features.dependency_failure_rate = healthMetrics.dependencyFailureRate || 0;
    features.request_count = healthMetrics.totalRequests || 0;
    features.health_score = healthMetrics.healthScore || 0;

    // Baseline comparison features
    if (baseline) {
      features.duration_p99_ratio = baseline.p99Duration > 0 ?
        features.duration_p99 / baseline.p99Duration : 1;
      features.duration_avg_ratio = baseline.avgDuration > 0 ?
        features.duration_avg / baseline.avgDuration : 1;
      features.error_rate_ratio = baseline.errorRate > 0 ?
        features.error_rate / baseline.errorRate : 1;
      features.dependency_failure_ratio = baseline.dependencyFailureRate > 0 ?
        features.dependency_failure_rate / baseline.dependencyFailureRate : 1;
      features.request_count_ratio = baseline.totalRequests > 0 ?
        features.request_count / baseline.totalRequests : 1;
      features.health_score_diff = features.health_score - (baseline.healthScore || 0);
    } else {
      // Default ratios when no baseline available
      features.duration_p99_ratio = 1;
      features.duration_avg_ratio = 1;
      features.error_rate_ratio = 1;
      features.dependency_failure_ratio = 1;
      features.request_count_ratio = 1;
      features.health_score_diff = 0;
    }

    // Derived features
    features.error_severity = this.calculateErrorSeverity(healthMetrics);
    features.performance_degradation = this.calculatePerformanceDegradation(features);
    features.system_stress = this.calculateSystemStress(features);

    return features;
  }

  calculateErrorSeverity(healthMetrics) {
    const errorRate = healthMetrics.errorRate || 0;
    const dependencyFailureRate = healthMetrics.dependencyFailureRate || 0;

    // Weighted severity calculation
    return (errorRate * 0.7) + (dependencyFailureRate * 0.3);
  }

  calculatePerformanceDegradation(features) {
    // Calculate performance degradation score
    const durationScore = Math.max(0, (features.duration_p99_ratio - 1) / 4); // Normalize to 0-1
    const avgDurationScore = Math.max(0, (features.duration_avg_ratio - 1) / 4);

    return Math.min(1, (durationScore * 0.6) + (avgDurationScore * 0.4));
  }

  calculateSystemStress(features) {
    // Calculate system stress based on multiple factors
    const performanceStress = features.performance_degradation;
    const errorStress = features.error_severity;
    const volumeStress = Math.min(1, Math.max(0, (features.request_count_ratio - 1) / 2));

    return (performanceStress * 0.4) + (errorStress * 0.4) + (volumeStress * 0.2);
  }

  detectStatisticalAnomalies(features, baseline) {
    const anomalies = [];

    // Z-score based detection
    if (baseline) {
      const zScores = this.calculateZScores(features, baseline);

      for (const [metric, zScore] of Object.entries(zScores)) {
        if (Math.abs(zScore) > 2.5) { // 2.5 sigma threshold
          anomalies.push(new Anomaly({
            type: 'statistical_anomaly',
            severity: Math.abs(zScore) > 3 ? 'high' : 'medium',
            description: `Statistical anomaly detected in ${metric} (z-score: ${zScore.toFixed(2)})`,
            affectedMetric: metric,
            currentValue: features[metric],
            baselineValue: baseline[metric] || 0,
            confidence: Math.min(0.95, Math.abs(zScore) / 4),
            detectionMethod: 'z_score',
            rawData: { zScore }
          }));
        }
      }
    }

    // Threshold based detection
    const thresholdAnomalies = this.detectThresholdAnomalies(features);
    anomalies.push(...thresholdAnomalies);

    return anomalies;
  }

  calculateZScores(features, baseline) {
    const zScores = {};
    const metricsToCheck = ['duration_p99', 'duration_avg', 'error_rate', 'dependency_failure_rate'];

    for (const metric of metricsToCheck) {
      const currentValue = features[metric] || 0;
      const baselineValue = baseline[metric] || 0;
      const baselineStd = baseline[`${metric}_std`] || (baselineValue * 0.1); // Fallback std

      if (baselineStd > 0) {
        zScores[metric] = (currentValue - baselineValue) / baselineStd;
      }
    }

    return zScores;
  }

  detectThresholdAnomalies(features) {
    const anomalies = [];

    // Hard threshold checks
    const thresholds = {
      duration_p99: 10000, // 10 seconds
      error_rate: 0.05, // 5%
      dependency_failure_rate: 0.02, // 2%
      system_stress: 0.8 // 80%
    };

    for (const [metric, threshold] of Object.entries(thresholds)) {
      if (features[metric] > threshold) {
        anomalies.push(new Anomaly({
          type: 'threshold_violation',
          severity: features[metric] > threshold * 1.5 ? 'critical' : 'high',
          description: `${metric} exceeded threshold: ${features[metric].toFixed(3)} > ${threshold}`,
          affectedMetric: metric,
          currentValue: features[metric],
          baselineValue: threshold,
          confidence: 0.9,
          detectionMethod: 'threshold'
        }));
      }
    }

    return anomalies;
  }

  async detectPatternAnomalies(features, model) {
    try {
      const anomalies = [];

      if (!model || !model.predict) {
        return anomalies;
      }

      // Prepare feature vector
      const featureVector = this.prepareFeatureVector(features);

      // Get prediction from model
      const prediction = model.predict(featureVector);

      // Check if prediction indicates anomaly
      if (prediction.isAnomaly) {
        anomalies.push(new Anomaly({
          type: 'pattern_anomaly',
          severity: prediction.severity || 'medium',
          description: `Pattern-based anomaly detected (score: ${prediction.score.toFixed(3)})`,
          affectedMetric: 'pattern',
          currentValue: prediction.score,
          baselineValue: model.threshold || 0.5,
          confidence: prediction.confidence || 0.7,
          detectionMethod: 'ml_pattern',
          rawData: { prediction, features }
        }));
      }

      return anomalies;

    } catch (error) {
      logger.error('Failed to detect pattern anomalies:', error);
      return [];
    }
  }

  detectTimeSeriesAnomalies(healthMetrics, baseline) {
    const anomalies = [];

    // Simple time series anomaly detection
    // In production, use more sophisticated methods like LSTM or Prophet

    if (!baseline || !baseline.recentHistory) {
      return anomalies;
    }

    const history = baseline.recentHistory;
    const currentMetrics = {
      duration: healthMetrics.p99Duration,
      errorRate: healthMetrics.errorRate,
      healthScore: healthMetrics.healthScore
    };

    for (const [metric, value] of Object.entries(currentMetrics)) {
      const historicalValues = history.map(h => h[metric]).filter(v => v != null);

      if (historicalValues.length >= 5) {
        const anomalyScore = this.calculateTimeSeriesAnomalyScore(value, historicalValues);

        if (anomalyScore > 0.8) {
          anomalies.push(new Anomaly({
            type: 'time_series_anomaly',
            severity: anomalyScore > 0.9 ? 'high' : 'medium',
            description: `Time series anomaly detected in ${metric}`,
            affectedMetric: metric,
            currentValue: value,
            baselineValue: this.calculateMedian(historicalValues),
            confidence: anomalyScore,
            detectionMethod: 'time_series',
            rawData: { historicalValues, anomalyScore }
          }));
        }
      }
    }

    return anomalies;
  }

  calculateTimeSeriesAnomalyScore(currentValue, historicalValues) {
    const mean = historicalValues.reduce((sum, val) => sum + val, 0) / historicalValues.length;
    const variance = historicalValues.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / historicalValues.length;
    const stdDev = Math.sqrt(variance);

    if (stdDev === 0) return 0;

    const zScore = Math.abs((currentValue - mean) / stdDev);

    // Convert z-score to anomaly score (0-1)
    return Math.min(1, zScore / 3);
  }

  calculateMedian(values) {
    const sorted = [...values].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);

    return sorted.length % 2 === 0
      ? (sorted[mid - 1] + sorted[mid]) / 2
      : sorted[mid];
  }

  prepareFeatureVector(features) {
    const vectorFeatures = [
      features.duration_p99_ratio || 1,
      features.duration_avg_ratio || 1,
      features.error_rate || 0,
      features.dependency_failure_rate || 0,
      features.error_severity || 0,
      features.performance_degradation || 0,
      features.system_stress || 0
    ];

    return new Matrix([vectorFeatures]);
  }

  determineChainType(chainId) {
    // Classify chains by their characteristics
    // This could be made more sophisticated with actual ML classification

    if (chainId.includes('trading')) return 'trading';
    if (chainId.includes('payment')) return 'payment';
    if (chainId.includes('user')) return 'user';
    if (chainId.includes('data')) return 'data';

    return 'default';
  }

  async getModel(chainType) {
    try {
      // Check if model is already loaded
      if (this.trainedModels.has(chainType)) {
        return this.trainedModels.get(chainType);
      }

      // Load model from database or create new one
      const model = await this.loadModel(chainType);

      if (model) {
        this.trainedModels.set(chainType, model);
        return model;
      }

      // Train new model if enough data available
      const trainingData = await this.getTrainingData(chainType);

      if (trainingData.length >= this.config.minTrainingData) {
        const newModel = await this.trainModel(chainType, trainingData);
        this.trainedModels.set(chainType, newModel);
        return newModel;
      }

      return null;

    } catch (error) {
      logger.error(`Failed to get model for chain type ${chainType}:`, error);
      return null;
    }
  }

  async loadModel(chainType) {
    try {
      const query = `
        SELECT model_data, created_at, accuracy
        FROM ml_models
        WHERE model_type = 'anomaly_detection' AND chain_type = $1
        ORDER BY created_at DESC
        LIMIT 1
      `;

      const result = await this.database.query(query, [chainType]);

      if (result.rows.length === 0) {
        return null;
      }

      const modelData = result.rows[0].model_data;

      // Deserialize model (simplified)
      return this.deserializeModel(modelData);

    } catch (error) {
      logger.error(`Failed to load model for chain type ${chainType}:`, error);
      return null;
    }
  }

  async getTrainingData(chainType) {
    try {
      const query = `
        SELECT hm.*, ca.type as anomaly_type
        FROM chain_health_metrics hm
        LEFT JOIN chain_anomalies ca ON hm.chain_id = ca.chain_id
          AND abs(extract(epoch from (hm.timestamp - ca.timestamp))) < 300
        WHERE hm.chain_id LIKE $1
          AND hm.timestamp > $2
        ORDER BY hm.timestamp DESC
        LIMIT 10000
      `;

      const result = await this.database.query(query, [
        `%${chainType}%`,
        new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) // Last 30 days
      ]);

      return result.rows;

    } catch (error) {
      logger.error(`Failed to get training data for chain type ${chainType}:`, error);
      return [];
    }
  }

  async trainModel(chainType, trainingData) {
    try {
      logger.info(`Training anomaly detection model for chain type: ${chainType}`);

      // Prepare training features and labels
      const { features, labels } = this.prepareTrainingData(trainingData);

      if (features.length === 0) {
        logger.warn(`No valid training data for chain type ${chainType}`);
        return null;
      }

      // Simple anomaly detection model (in production, use more sophisticated models)
      const model = this.createSimpleAnomalyModel(features, labels);

      // Evaluate model
      const accuracy = this.evaluateModel(model, features, labels);

      logger.info(`Model trained for ${chainType} with accuracy: ${accuracy.toFixed(3)}`);

      // Save model
      await this.saveModel(chainType, model, accuracy);

      return model;

    } catch (error) {
      logger.error(`Failed to train model for chain type ${chainType}:`, error);
      return null;
    }
  }

  prepareTrainingData(rawData) {
    const features = [];
    const labels = [];

    for (const record of rawData) {
      try {
        // Extract features
        const feature = {
          duration_p99: record.p99_duration || 0,
          duration_avg: record.avg_duration || 0,
          error_rate: record.error_rate || 0,
          dependency_failure_rate: record.dependency_failure_rate || 0,
          health_score: record.health_score || 0
        };

        // Calculate derived features
        feature.error_severity = this.calculateErrorSeverity(feature);
        feature.performance_degradation = feature.duration_p99 > 5000 ? 1 : 0;

        features.push(feature);

        // Label: 1 if anomaly was detected, 0 otherwise
        labels.push(record.anomaly_type ? 1 : 0);

      } catch (error) {
        logger.debug('Skipping invalid training record:', error);
      }
    }

    return { features, labels };
  }

  createSimpleAnomalyModel(features, labels) {
    // Simple threshold-based model with learned thresholds
    const model = {
      type: 'threshold_ensemble',
      thresholds: {},
      weights: {},
      threshold: 0.6,
      predict: null
    };

    // Calculate optimal thresholds for each feature
    const featureNames = Object.keys(features[0] || {});

    for (const featureName of featureNames) {
      const featureValues = features.map(f => f[featureName]);
      const anomalyValues = featureValues.filter((_, i) => labels[i] === 1);
      const normalValues = featureValues.filter((_, i) => labels[i] === 0);

      if (anomalyValues.length > 0 && normalValues.length > 0) {
        // Use 95th percentile of normal values as threshold
        const sortedNormal = normalValues.sort((a, b) => a - b);
        const thresholdIndex = Math.floor(sortedNormal.length * 0.95);
        model.thresholds[featureName] = sortedNormal[thresholdIndex];

        // Calculate feature importance
        const separation = this.calculateSeparation(normalValues, anomalyValues);
        model.weights[featureName] = separation;
      }
    }

    // Normalize weights
    const totalWeight = Object.values(model.weights).reduce((sum, w) => sum + w, 0);
    if (totalWeight > 0) {
      for (const feature in model.weights) {
        model.weights[feature] /= totalWeight;
      }
    }

    // Add prediction function
    model.predict = (featureVector) => {
      const features = this.vectorToFeatures(featureVector);
      let score = 0;

      for (const [feature, value] of Object.entries(features)) {
        if (model.thresholds[feature] && model.weights[feature]) {
          const exceedsThreshold = value > model.thresholds[feature] ? 1 : 0;
          score += exceedsThreshold * model.weights[feature];
        }
      }

      return {
        isAnomaly: score > model.threshold,
        score,
        confidence: Math.min(0.95, score),
        severity: score > 0.8 ? 'high' : score > 0.6 ? 'medium' : 'low'
      };
    };

    return model;
  }

  calculateSeparation(normalValues, anomalyValues) {
    const normalMean = normalValues.reduce((sum, v) => sum + v, 0) / normalValues.length;
    const anomalyMean = anomalyValues.reduce((sum, v) => sum + v, 0) / anomalyValues.length;

    const normalStd = Math.sqrt(
      normalValues.reduce((sum, v) => sum + Math.pow(v - normalMean, 2), 0) / normalValues.length
    );

    const anomalyStd = Math.sqrt(
      anomalyValues.reduce((sum, v) => sum + Math.pow(v - anomalyMean, 2), 0) / anomalyValues.length
    );

    // Fisher's discriminant ratio
    const pooledStd = Math.sqrt((normalStd * normalStd + anomalyStd * anomalyStd) / 2);

    return pooledStd > 0 ? Math.abs(anomalyMean - normalMean) / pooledStd : 0;
  }

  vectorToFeatures(featureVector) {
    const vector = featureVector.data ? featureVector.data[0] : featureVector;

    return {
      duration_p99_ratio: vector[0] || 1,
      duration_avg_ratio: vector[1] || 1,
      error_rate: vector[2] || 0,
      dependency_failure_rate: vector[3] || 0,
      error_severity: vector[4] || 0,
      performance_degradation: vector[5] || 0,
      system_stress: vector[6] || 0
    };
  }

  evaluateModel(model, features, labels) {
    let correct = 0;

    for (let i = 0; i < features.length; i++) {
      const featureVector = this.prepareFeatureVector(features[i]);
      const prediction = model.predict(featureVector);
      const predicted = prediction.isAnomaly ? 1 : 0;

      if (predicted === labels[i]) {
        correct++;
      }
    }

    return correct / features.length;
  }

  async saveModel(chainType, model, accuracy) {
    try {
      const query = `
        INSERT INTO ml_models (model_type, chain_type, model_data, accuracy, created_at)
        VALUES ($1, $2, $3, $4, $5)
      `;

      const serializedModel = this.serializeModel(model);

      await this.database.query(query, [
        'anomaly_detection',
        chainType,
        serializedModel,
        accuracy,
        new Date()
      ]);

    } catch (error) {
      logger.error('Failed to save model:', error);
    }
  }

  serializeModel(model) {
    // Serialize model (excluding functions)
    const serializable = {
      type: model.type,
      thresholds: model.thresholds,
      weights: model.weights,
      threshold: model.threshold
    };

    return JSON.stringify(serializable);
  }

  deserializeModel(modelData) {
    try {
      const data = JSON.parse(modelData);

      // Reconstruct model with prediction function
      const model = {
        ...data,
        predict: (featureVector) => {
          const features = this.vectorToFeatures(featureVector);
          let score = 0;

          for (const [feature, value] of Object.entries(features)) {
            if (data.thresholds[feature] && data.weights[feature]) {
              const exceedsThreshold = value > data.thresholds[feature] ? 1 : 0;
              score += exceedsThreshold * data.weights[feature];
            }
          }

          return {
            isAnomaly: score > data.threshold,
            score,
            confidence: Math.min(0.95, score),
            severity: score > 0.8 ? 'high' : score > 0.6 ? 'medium' : 'low'
          };
        }
      };

      return model;

    } catch (error) {
      logger.error('Failed to deserialize model:', error);
      return null;
    }
  }

  async loadModels() {
    try {
      logger.info('Loading anomaly detection models...');

      const query = `
        SELECT DISTINCT chain_type FROM ml_models
        WHERE model_type = 'anomaly_detection'
      `;

      const result = await this.database.query(query);

      for (const row of result.rows) {
        const model = await this.loadModel(row.chain_type);
        if (model) {
          this.trainedModels.set(row.chain_type, model);
        }
      }

      logger.info(`Loaded ${this.trainedModels.size} anomaly detection models`);

    } catch (error) {
      logger.error('Failed to load models:', error);
    }
  }

  initializeFeatureExtractors() {
    // Initialize feature extraction functions
    this.featureExtractors.set('statistical', this.extractStatisticalFeatures.bind(this));
    this.featureExtractors.set('temporal', this.extractTemporalFeatures.bind(this));
    this.featureExtractors.set('comparative', this.extractComparativeFeatures.bind(this));
  }

  extractStatisticalFeatures(healthMetrics) {
    return {
      mean_duration: healthMetrics.avgDuration,
      max_duration: healthMetrics.p99Duration,
      error_rate: healthMetrics.errorRate,
      variance_estimation: this.estimateVariance(healthMetrics)
    };
  }

  extractTemporalFeatures(healthMetrics) {
    return {
      timestamp: healthMetrics.timestamp,
      hour_of_day: healthMetrics.timestamp.getHours(),
      day_of_week: healthMetrics.timestamp.getDay(),
      is_weekend: [0, 6].includes(healthMetrics.timestamp.getDay())
    };
  }

  extractComparativeFeatures(healthMetrics, baseline) {
    if (!baseline) return {};

    return {
      duration_change: healthMetrics.p99Duration - (baseline.p99Duration || 0),
      error_rate_change: healthMetrics.errorRate - (baseline.errorRate || 0),
      health_score_change: healthMetrics.healthScore - (baseline.healthScore || 0)
    };
  }

  estimateVariance(healthMetrics) {
    // Simple variance estimation based on available metrics
    const duration = healthMetrics.p99Duration || 0;
    const avgDuration = healthMetrics.avgDuration || 0;

    return Math.max(0, duration - avgDuration);
  }
}