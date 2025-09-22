/**
 * Probability Calibration Accuracy Measurement System
 * Measures and validates the accuracy of probabilistic predictions
 */

const EventEmitter = require('events');

class ProbabilityCalibrationMeasurer extends EventEmitter {
  constructor(config = {}) {
    super();

    this.config = {
      binCount: config.binCount || 10,
      minSampleSize: config.minSampleSize || 100,
      confidenceLevel: config.confidenceLevel || 0.95,
      slidingWindowSize: config.slidingWindowSize || 1000,
      recalibrationThreshold: config.recalibrationThreshold || 0.1,
      ...config
    };

    this.predictions = [];
    this.calibrationHistory = [];
    this.calibrationBins = [];
    this.reliabilityDiagram = null;
    this.isMonitoring = false;
  }

  /**
   * Initialize calibration measurement system
   */
  async initialize() {
    this.initializeCalibrationBins();
    this.startMonitoring();
    this.emit('initialized', { timestamp: Date.now() });
  }

  initializeCalibrationBins() {
    this.calibrationBins = Array.from({ length: this.config.binCount }, (_, i) => ({
      binIndex: i,
      lowerBound: i / this.config.binCount,
      upperBound: (i + 1) / this.config.binCount,
      predictions: [],
      actualOutcomes: [],
      count: 0,
      accuracy: 0,
      confidence: 0
    }));
  }

  /**
   * Record a probabilistic prediction and its eventual outcome
   */
  recordPrediction(predictionId, probability, metadata = {}) {
    if (probability < 0 || probability > 1) {
      throw new Error('Probability must be between 0 and 1');
    }

    const prediction = {
      id: predictionId,
      probability: probability,
      timestamp: Date.now(),
      metadata: metadata,
      outcome: null,
      resolved: false
    };

    this.predictions.push(prediction);

    // Add to appropriate calibration bin
    const binIndex = Math.min(
      Math.floor(probability * this.config.binCount),
      this.config.binCount - 1
    );

    this.calibrationBins[binIndex].predictions.push(prediction);

    this.emit('predictionRecorded', { predictionId, probability, timestamp: prediction.timestamp });

    return prediction;
  }

  /**
   * Record the actual outcome for a prediction
   */
  recordOutcome(predictionId, outcome, timestamp = Date.now()) {
    const prediction = this.predictions.find(p => p.id === predictionId);

    if (!prediction) {
      throw new Error(`Prediction with ID ${predictionId} not found`);
    }

    if (prediction.resolved) {
      throw new Error(`Prediction ${predictionId} already resolved`);
    }

    // Convert outcome to binary (0 or 1)
    const binaryOutcome = outcome ? 1 : 0;

    prediction.outcome = binaryOutcome;
    prediction.resolved = true;
    prediction.resolutionTime = timestamp;

    // Update calibration bin
    const binIndex = Math.min(
      Math.floor(prediction.probability * this.config.binCount),
      this.config.binCount - 1
    );

    this.calibrationBins[binIndex].actualOutcomes.push(binaryOutcome);
    this.calibrationBins[binIndex].count++;

    this.emit('outcomeRecorded', { predictionId, outcome: binaryOutcome, timestamp });

    // Trigger calibration update if enough samples
    if (this.getResolvedPredictionsCount() % 100 === 0) {
      this.updateCalibrationMetrics();
    }

    return prediction;
  }

  /**
   * Calculate comprehensive calibration metrics
   */
  calculateCalibrationMetrics() {
    const resolvedPredictions = this.predictions.filter(p => p.resolved);

    if (resolvedPredictions.length < this.config.minSampleSize) {
      return null;
    }

    const metrics = {
      timestamp: Date.now(),
      sampleSize: resolvedPredictions.length,
      brierScore: this.calculateBrierScore(resolvedPredictions),
      calibrationError: this.calculateCalibrationError(),
      reliability: this.calculateReliability(),
      resolution: this.calculateResolution(resolvedPredictions),
      sharpness: this.calculateSharpness(resolvedPredictions),
      uncertainty: this.calculateUncertainty(resolvedPredictions),
      binMetrics: this.calculateBinMetrics(),
      reliabilityDiagram: this.generateReliabilityDiagram()
    };

    // Calculate derived metrics
    metrics.skillScore = metrics.resolution - metrics.reliability;
    metrics.refinement = metrics.sharpness - metrics.uncertainty;
    metrics.calibrationSlope = this.calculateCalibrationSlope();
    metrics.calibrationIntercept = this.calculateCalibrationIntercept();

    return metrics;
  }

  calculateBrierScore(predictions) {
    if (predictions.length === 0) return 1;

    const brierSum = predictions.reduce((sum, pred) => {
      return sum + Math.pow(pred.probability - pred.outcome, 2);
    }, 0);

    return brierSum / predictions.length;
  }

  calculateCalibrationError() {
    let weightedError = 0;
    let totalWeight = 0;

    this.calibrationBins.forEach(bin => {
      if (bin.count > 0) {
        const meanPrediction = bin.predictions
          .filter(p => p.resolved)
          .reduce((sum, p) => sum + p.probability, 0) / bin.count;

        const meanOutcome = bin.actualOutcomes.reduce((sum, o) => sum + o, 0) / bin.count;

        const weight = bin.count;
        weightedError += weight * Math.pow(meanPrediction - meanOutcome, 2);
        totalWeight += weight;
      }
    });

    return totalWeight > 0 ? weightedError / totalWeight : 0;
  }

  calculateReliability() {
    // Reliability component of Brier score decomposition
    let reliability = 0;
    const totalCount = this.getResolvedPredictionsCount();

    this.calibrationBins.forEach(bin => {
      if (bin.count > 0) {
        const meanPrediction = bin.predictions
          .filter(p => p.resolved)
          .reduce((sum, p) => sum + p.probability, 0) / bin.count;

        const meanOutcome = bin.actualOutcomes.reduce((sum, o) => sum + o, 0) / bin.count;

        reliability += (bin.count / totalCount) * Math.pow(meanPrediction - meanOutcome, 2);
      }
    });

    return reliability;
  }

  calculateResolution(predictions) {
    if (predictions.length === 0) return 0;

    const overallMean = predictions.reduce((sum, p) => sum + p.outcome, 0) / predictions.length;
    let resolution = 0;
    const totalCount = predictions.length;

    this.calibrationBins.forEach(bin => {
      if (bin.count > 0) {
        const meanOutcome = bin.actualOutcomes.reduce((sum, o) => sum + o, 0) / bin.count;
        resolution += (bin.count / totalCount) * Math.pow(meanOutcome - overallMean, 2);
      }
    });

    return resolution;
  }

  calculateSharpness(predictions) {
    if (predictions.length === 0) return 0;

    const overallMeanPrediction = predictions.reduce((sum, p) => sum + p.probability, 0) / predictions.length;

    return predictions.reduce((sum, p) => {
      return sum + Math.pow(p.probability - overallMeanPrediction, 2);
    }, 0) / predictions.length;
  }

  calculateUncertainty(predictions) {
    if (predictions.length === 0) return 0;

    const meanOutcome = predictions.reduce((sum, p) => sum + p.outcome, 0) / predictions.length;
    return meanOutcome * (1 - meanOutcome);
  }

  calculateBinMetrics() {
    return this.calibrationBins.map(bin => {
      if (bin.count === 0) {
        return {
          binIndex: bin.binIndex,
          range: [bin.lowerBound, bin.upperBound],
          count: 0,
          meanPrediction: 0,
          meanOutcome: 0,
          accuracy: 0,
          confidence: 0
        };
      }

      const resolvedPredictions = bin.predictions.filter(p => p.resolved);
      const meanPrediction = resolvedPredictions.reduce((sum, p) => sum + p.probability, 0) / resolvedPredictions.length;
      const meanOutcome = bin.actualOutcomes.reduce((sum, o) => sum + o, 0) / bin.count;

      return {
        binIndex: bin.binIndex,
        range: [bin.lowerBound, bin.upperBound],
        count: bin.count,
        meanPrediction: meanPrediction,
        meanOutcome: meanOutcome,
        accuracy: Math.abs(meanPrediction - meanOutcome),
        confidence: this.calculateBinConfidenceInterval(bin)
      };
    });
  }

  calculateBinConfidenceInterval(bin) {
    if (bin.count < 10) return { lower: 0, upper: 1, width: 1 };

    const meanOutcome = bin.actualOutcomes.reduce((sum, o) => sum + o, 0) / bin.count;
    const variance = meanOutcome * (1 - meanOutcome) / bin.count;
    const stdError = Math.sqrt(variance);

    // 95% confidence interval
    const zScore = 1.96;
    const margin = zScore * stdError;

    return {
      lower: Math.max(0, meanOutcome - margin),
      upper: Math.min(1, meanOutcome + margin),
      width: 2 * margin
    };
  }

  generateReliabilityDiagram() {
    const diagram = {
      bins: [],
      perfectCalibrationLine: [],
      confidenceBands: []
    };

    this.calibrationBins.forEach(bin => {
      if (bin.count > 0) {
        const resolvedPredictions = bin.predictions.filter(p => p.resolved);
        const meanPrediction = resolvedPredictions.reduce((sum, p) => sum + p.probability, 0) / resolvedPredictions.length;
        const meanOutcome = bin.actualOutcomes.reduce((sum, o) => sum + o, 0) / bin.count;
        const confidence = this.calculateBinConfidenceInterval(bin);

        diagram.bins.push({
          x: meanPrediction,
          y: meanOutcome,
          size: bin.count,
          confidence: confidence
        });
      }
    });

    // Perfect calibration line (y = x)
    for (let i = 0; i <= 10; i++) {
      const point = i / 10;
      diagram.perfectCalibrationLine.push({ x: point, y: point });
    }

    return diagram;
  }

  calculateCalibrationSlope() {
    const points = this.calibrationBins
      .filter(bin => bin.count > 0)
      .map(bin => {
        const resolvedPredictions = bin.predictions.filter(p => p.resolved);
        const meanPrediction = resolvedPredictions.reduce((sum, p) => sum + p.probability, 0) / resolvedPredictions.length;
        const meanOutcome = bin.actualOutcomes.reduce((sum, o) => sum + o, 0) / bin.count;
        return { x: meanPrediction, y: meanOutcome };
      });

    if (points.length < 2) return 1;

    // Linear regression
    const n = points.length;
    const sumX = points.reduce((sum, p) => sum + p.x, 0);
    const sumY = points.reduce((sum, p) => sum + p.y, 0);
    const sumXY = points.reduce((sum, p) => sum + p.x * p.y, 0);
    const sumXX = points.reduce((sum, p) => sum + p.x * p.x, 0);

    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    return slope;
  }

  calculateCalibrationIntercept() {
    const points = this.calibrationBins
      .filter(bin => bin.count > 0)
      .map(bin => {
        const resolvedPredictions = bin.predictions.filter(p => p.resolved);
        const meanPrediction = resolvedPredictions.reduce((sum, p) => sum + p.probability, 0) / resolvedPredictions.length;
        const meanOutcome = bin.actualOutcomes.reduce((sum, o) => sum + o, 0) / bin.count;
        return { x: meanPrediction, y: meanOutcome };
      });

    if (points.length < 2) return 0;

    const n = points.length;
    const sumX = points.reduce((sum, p) => sum + p.x, 0);
    const sumY = points.reduce((sum, p) => sum + p.y, 0);
    const sumXY = points.reduce((sum, p) => sum + p.x * p.y, 0);
    const sumXX = points.reduce((sum, p) => sum + p.x * p.x, 0);

    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;

    return intercept;
  }

  /**
   * Update calibration metrics and trigger alerts if needed
   */
  updateCalibrationMetrics() {
    const metrics = this.calculateCalibrationMetrics();

    if (metrics) {
      this.calibrationHistory.push(metrics);

      // Check for calibration drift
      if (this.detectCalibrationDrift(metrics)) {
        this.emit('calibrationDrift', {
          metrics,
          threshold: this.config.recalibrationThreshold
        });
      }

      this.emit('calibrationUpdated', metrics);
    }
  }

  detectCalibrationDrift(currentMetrics) {
    if (this.calibrationHistory.length < 2) return false;

    const previousMetrics = this.calibrationHistory[this.calibrationHistory.length - 2];
    const errorIncrease = currentMetrics.calibrationError - previousMetrics.calibrationError;

    return errorIncrease > this.config.recalibrationThreshold;
  }

  /**
   * Get recent calibration performance
   */
  getRecentCalibrationPerformance(windowSize = null) {
    const window = windowSize || this.config.slidingWindowSize;
    const recentPredictions = this.predictions
      .filter(p => p.resolved)
      .slice(-window);

    if (recentPredictions.length === 0) return null;

    return {
      windowSize: recentPredictions.length,
      brierScore: this.calculateBrierScore(recentPredictions),
      timeRange: {
        start: recentPredictions[0].timestamp,
        end: recentPredictions[recentPredictions.length - 1].timestamp
      }
    };
  }

  getResolvedPredictionsCount() {
    return this.predictions.filter(p => p.resolved).length;
  }

  /**
   * Export calibration data
   */
  exportCalibrationData() {
    return {
      timestamp: Date.now(),
      config: this.config,
      predictions: this.predictions,
      calibrationHistory: this.calibrationHistory,
      currentMetrics: this.calculateCalibrationMetrics(),
      reliabilityDiagram: this.reliabilityDiagram
    };
  }

  startMonitoring() {
    this.isMonitoring = true;
    this.emit('monitoringStarted', { timestamp: Date.now() });
  }

  stopMonitoring() {
    this.isMonitoring = false;
    this.emit('monitoringStopped', { timestamp: Date.now() });
  }
}

module.exports = ProbabilityCalibrationMeasurer;