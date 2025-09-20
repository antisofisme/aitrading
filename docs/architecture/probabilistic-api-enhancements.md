# Probabilistic API Enhancements

## Overview

This document defines the comprehensive API enhancements to support confidence scoring, uncertainty quantification, and probabilistic decision making across all microservices in the AI trading platform.

## 1. Enhanced AI Orchestration Service API (Port 8003)

### 1.1 Probabilistic Trading Decision Endpoint

```typescript
// Enhanced endpoint with multi-layer probability confirmation
POST /api/v1/ai/trading-decision/probabilistic

Request:
{
  "symbol": "EURUSD",
  "timestamp": 1705738200000,
  "market_data": {
    "bid": 1.0850,
    "ask": 1.0852,
    "volume": 1000,
    "spread": 0.0002
  },
  "context": {
    "user_id": "uuid",
    "risk_tolerance": 0.7,
    "confidence_threshold": 0.75,
    "uncertainty_tolerance": 0.3
  },
  "options": {
    "enable_multi_layer_validation": true,
    "include_uncertainty_analysis": true,
    "require_meta_validation": true
  }
}

Response:
{
  "prediction_id": "uuid",
  "timestamp": 1705738200000,
  "symbol": "EURUSD",

  // Multi-layer probability results
  "probability_layers": {
    "layer_1_indicators": {
      "probabilities": [
        {
          "indicator": "rsi",
          "signal": "BUY",
          "confidence": 0.82,
          "probability": {
            "bullish": 0.78,
            "bearish": 0.15,
            "neutral": 0.07
          },
          "uncertainty": 0.18,
          "reliability": 0.85
        },
        {
          "indicator": "macd",
          "signal": "BUY",
          "confidence": 0.75,
          "probability": {
            "bullish": 0.72,
            "bearish": 0.20,
            "neutral": 0.08
          },
          "uncertainty": 0.25,
          "reliability": 0.88
        }
      ],
      "layer_confidence": 0.785
    },
    "layer_2_ensemble": {
      "aggregated_probability": {
        "bullish": 0.76,
        "bearish": 0.18,
        "neutral": 0.06
      },
      "consensus_strength": 0.82,
      "divergence": 0.18,
      "conflict_resolution": "weighted_consensus",
      "weighted_confidence": 0.79
    },
    "layer_3_meta_validation": {
      "meta_probability": 0.81,
      "model_confidence": 0.78,
      "anomaly_score": 0.12,
      "regime_compatibility": 0.85,
      "validation_result": "CONFIRMED"
    }
  },

  // Final decision with confidence metrics
  "decision": {
    "action": "BUY",
    "aggregated_confidence": 0.79,
    "uncertainty_metrics": {
      "epistemic_uncertainty": 0.15,  // Model uncertainty
      "aleatoric_uncertainty": 0.12,  // Data uncertainty
      "total_uncertainty": 0.21
    },
    "risk_assessment": {
      "position_size": 0.02,
      "confidence_adjusted_size": 0.018,
      "uncertainty_penalty": 0.1,
      "max_acceptable_loss": 0.015
    }
  },

  // Performance and execution metrics
  "performance": {
    "total_processing_time_ms": 85,
    "layer_processing_times": {
      "indicators": 35,
      "ensemble": 25,
      "meta_validation": 25
    },
    "cache_hit_ratio": 0.75
  },

  // Model metadata and versioning
  "model_metadata": {
    "model_versions": [
      {"name": "xgboost_ensemble", "version": "1.2.3"},
      {"name": "transformer_meta", "version": "2.1.0"}
    ],
    "last_training_update": "2024-01-20T10:30:00Z",
    "market_regime": "normal_volatility",
    "volatility_score": 0.25
  }
}
```

### 1.2 Confidence Calibration Check Endpoint

```typescript
GET /api/v1/ai/calibration-status/{model_name}

Response:
{
  "model_name": "xgboost_ensemble",
  "calibration_metrics": {
    "overall_calibration": 0.88,
    "brier_score": 0.185,
    "log_loss": 0.412,
    "confidence_bins": [
      {
        "confidence_range": "0.0-0.1",
        "predicted_probability": 0.05,
        "observed_frequency": 0.08,
        "sample_count": 150,
        "calibration_error": 0.03
      },
      {
        "confidence_range": "0.7-0.8",
        "predicted_probability": 0.75,
        "observed_frequency": 0.73,
        "sample_count": 425,
        "calibration_error": 0.02
      }
    ]
  },
  "recommendations": [
    "Model is well-calibrated for confidence > 0.6",
    "Consider Platt scaling for low-confidence predictions"
  ],
  "last_calibration_check": "2024-01-20T10:30:00Z"
}
```

## 2. Enhanced ML Processing Service API (Port 8006)

### 2.1 Ensemble Probability Aggregation Endpoint

```typescript
POST /api/v1/ml/ensemble-probability

Request:
{
  "predictions": [
    {
      "model_id": "xgboost_v1_2",
      "prediction": "BUY",
      "confidence": 0.82,
      "probability_distribution": [0.78, 0.15, 0.07],
      "uncertainty": 0.18,
      "model_weight": 0.4
    },
    {
      "model_id": "lightgbm_v2_1",
      "prediction": "BUY",
      "confidence": 0.75,
      "probability_distribution": [0.72, 0.20, 0.08],
      "uncertainty": 0.25,
      "model_weight": 0.35
    },
    {
      "model_id": "random_forest_v1_5",
      "prediction": "HOLD",
      "confidence": 0.65,
      "probability_distribution": [0.30, 0.25, 0.45],
      "uncertainty": 0.35,
      "model_weight": 0.25
    }
  ],
  "aggregation_method": "uncertainty_weighted",
  "conflict_resolution": "confidence_weighted"
}

Response:
{
  "ensemble_result": {
    "aggregated_prediction": "BUY",
    "aggregated_probability": {
      "bullish": 0.65,
      "bearish": 0.19,
      "neutral": 0.16
    },
    "ensemble_confidence": 0.76,
    "consensus_strength": 0.72,
    "divergence_score": 0.28,
    "uncertainty_aggregate": 0.22
  },

  "conflict_analysis": {
    "conflicts_detected": true,
    "conflict_models": ["random_forest_v1_5"],
    "conflict_severity": "moderate",
    "resolution_method": "confidence_weighted_voting",
    "confidence_in_resolution": 0.74
  },

  "weight_analysis": {
    "effective_weights": {
      "xgboost_v1_2": 0.45,
      "lightgbm_v2_1": 0.38,
      "random_forest_v1_5": 0.17
    },
    "weight_adjustment_reason": "uncertainty_penalty_applied",
    "total_model_agreement": 0.72
  },

  "recommendation": {
    "proceed_with_prediction": true,
    "confidence_threshold_met": true,
    "uncertainty_acceptable": true,
    "suggested_position_size_multiplier": 0.9
  }
}
```

### 2.2 Model Performance Comparison Endpoint

```typescript
GET /api/v1/ml/model-performance/comparison

Query Parameters:
- time_range: "24h" | "7d" | "30d"
- metric: "accuracy" | "calibration" | "uncertainty" | "all"
- models: comma-separated list of model IDs

Response:
{
  "comparison_period": "7d",
  "models_compared": ["xgboost_v1_2", "lightgbm_v2_1", "transformer_v1_0"],

  "performance_metrics": {
    "xgboost_v1_2": {
      "accuracy": 0.78,
      "precision": 0.82,
      "recall": 0.75,
      "f1_score": 0.78,
      "calibration_score": 0.85,
      "brier_score": 0.175,
      "uncertainty_quality": 0.80,
      "prediction_count": 1547,
      "avg_confidence": 0.73,
      "sharpe_ratio": 1.85
    },
    "lightgbm_v2_1": {
      "accuracy": 0.76,
      "precision": 0.79,
      "recall": 0.73,
      "f1_score": 0.76,
      "calibration_score": 0.82,
      "brier_score": 0.188,
      "uncertainty_quality": 0.78,
      "prediction_count": 1523,
      "avg_confidence": 0.71,
      "sharpe_ratio": 1.72
    }
  },

  "ranking": [
    {
      "model_id": "xgboost_v1_2",
      "overall_score": 0.815,
      "rank": 1,
      "strengths": ["calibration", "uncertainty_quality"],
      "weaknesses": ["processing_time"]
    },
    {
      "model_id": "lightgbm_v2_1",
      "overall_score": 0.795,
      "rank": 2,
      "strengths": ["speed", "memory_efficiency"],
      "weaknesses": ["accuracy", "calibration"]
    }
  ],

  "recommendations": {
    "best_for_high_confidence": "xgboost_v1_2",
    "best_for_speed": "lightgbm_v2_1",
    "ensemble_weights": {
      "xgboost_v1_2": 0.45,
      "lightgbm_v2_1": 0.35,
      "transformer_v1_0": 0.20
    }
  }
}
```

## 3. New Probabilistic Learning Service API (Port 8011)

### 3.1 Real-time Adaptive Learning Endpoint

```typescript
POST /api/v1/probabilistic/adaptive-learning/feedback

Request:
{
  "feedback_data": {
    "prediction_id": "uuid",
    "actual_outcome": 0.0235,  // Actual return
    "expected_outcome": 0.0189,  // Predicted return
    "confidence_used": 0.78,
    "position_size_used": 0.02,
    "market_conditions": {
      "volatility": 0.25,
      "regime": "normal",
      "volume": "high"
    },
    "execution_latency_ms": 125,
    "timestamp": "2024-01-20T10:30:00Z"
  },
  "learning_options": {
    "immediate_update": true,
    "update_ensemble_weights": true,
    "trigger_recalibration": false
  }
}

Response:
{
  "feedback_processed": true,
  "impact_assessment": {
    "prediction_error": 0.0046,
    "error_magnitude": "small",
    "impact_score": 0.3,
    "learning_trigger": "incremental"
  },

  "model_updates": {
    "models_updated": ["xgboost_v1_2", "ensemble_aggregator"],
    "update_magnitude": 0.15,
    "new_model_weights": {
      "xgboost_v1_2": 0.42,  // Reduced from 0.45
      "lightgbm_v2_1": 0.38,  // Increased from 0.35
      "random_forest_v1_5": 0.20  // Increased from 0.17
    }
  },

  "calibration_impact": {
    "calibration_drift_detected": false,
    "new_calibration_score": 0.853,
    "recalibration_recommended": false
  },

  "performance_prediction": {
    "expected_accuracy_change": 0.005,  // Small improvement expected
    "confidence_adjustment": -0.02,  // Slightly less confident
    "uncertainty_adjustment": 0.01   // Slightly more uncertain
  }
}
```

### 3.2 Uncertainty Quantification Endpoint

```typescript
POST /api/v1/probabilistic/uncertainty/quantify

Request:
{
  "prediction_context": {
    "symbol": "EURUSD",
    "features": {
      "rsi": 65.5,
      "macd": 0.0012,
      "sma_20": 1.0845,
      "volatility": 0.25
    },
    "market_regime": "normal",
    "historical_similarity": 0.78
  },
  "uncertainty_methods": ["bayesian", "ensemble", "dropout"],
  "confidence_intervals": [0.68, 0.95, 0.99]
}

Response:
{
  "uncertainty_analysis": {
    "epistemic_uncertainty": 0.15,  // Model uncertainty
    "aleatoric_uncertainty": 0.12,  // Data/noise uncertainty
    "total_uncertainty": 0.19,

    "uncertainty_breakdown": {
      "model_uncertainty": {
        "parameter_uncertainty": 0.08,
        "architecture_uncertainty": 0.05,
        "training_data_uncertainty": 0.02
      },
      "data_uncertainty": {
        "measurement_noise": 0.07,
        "feature_uncertainty": 0.03,
        "temporal_uncertainty": 0.02
      }
    }
  },

  "confidence_intervals": {
    "68_percent": {
      "lower": 0.0145,
      "upper": 0.0234,
      "width": 0.0089
    },
    "95_percent": {
      "lower": 0.0089,
      "upper": 0.0289,
      "width": 0.0200
    },
    "99_percent": {
      "lower": 0.0034,
      "upper": 0.0345,
      "width": 0.0311
    }
  },

  "uncertainty_sources": [
    {
      "source": "limited_historical_data",
      "contribution": 0.35,
      "description": "Insufficient data for current market regime"
    },
    {
      "source": "model_disagreement",
      "contribution": 0.28,
      "description": "Ensemble models show divergent predictions"
    },
    {
      "source": "feature_correlation_change",
      "contribution": 0.37,
      "description": "Feature relationships differ from training period"
    }
  ],

  "recommendations": {
    "position_size_adjustment": -0.15,  // Reduce position by 15%
    "confidence_threshold_adjustment": 0.05,  // Require higher confidence
    "uncertainty_monitoring": "increased",
    "data_collection_priority": ["market_regime_indicators", "correlation_metrics"]
  }
}
```

## 4. Enhanced Trading Engine API (Port 8007)

### 4.1 Confidence-Based Position Sizing Endpoint

```typescript
POST /api/v1/trading/position-sizing/confidence-based

Request:
{
  "signal": {
    "symbol": "EURUSD",
    "direction": "BUY",
    "entry_price": 1.0850,
    "confidence": 0.78,
    "uncertainty": 0.22
  },
  "probability_data": {
    "aggregated_confidence": 0.78,
    "epistemic_uncertainty": 0.15,
    "aleatoric_uncertainty": 0.12,
    "consensus_strength": 0.82,
    "divergence": 0.18
  },
  "risk_parameters": {
    "account_balance": 100000,
    "max_risk_per_trade": 0.02,
    "risk_tolerance": 0.7,
    "uncertainty_tolerance": 0.3
  }
}

Response:
{
  "position_sizing": {
    "base_position_size": 2000,  // 2% of account
    "confidence_multiplier": 0.85,
    "uncertainty_penalty": 0.12,
    "final_position_size": 1496,  // Adjusted size
    "position_size_percentage": 0.01496
  },

  "risk_assessment": {
    "risk_level": "MODERATE",
    "confidence_risk_score": 0.73,
    "uncertainty_risk_score": 0.22,
    "overall_risk_score": 0.48,
    "risk_justification": "High confidence but moderate uncertainty requires position reduction"
  },

  "dynamic_stops": {
    "stop_loss": 1.0820,  // 30 pips
    "take_profit": 1.0895,  // 45 pips
    "stop_distance_pips": 30,
    "take_profit_distance_pips": 45,
    "risk_reward_ratio": 1.5,

    "trailing_stop": {
      "activation_pips": 15,
      "step_pips": 5,
      "max_loss_pips": 35
    }
  },

  "confidence_adjustments": {
    "position_timeout_minutes": 240,  // 4 hours max hold
    "confidence_exit_threshold": 0.3,  // Exit if confidence drops below 30%
    "uncertainty_exit_threshold": 0.6,  // Exit if uncertainty exceeds 60%
    "partial_exit_levels": [
      {
        "confidence_threshold": 0.9,
        "exit_percentage": 0.5,
        "reason": "Take profits at high confidence"
      }
    ]
  },

  "monitoring_requirements": {
    "confidence_check_interval_seconds": 60,
    "uncertainty_monitoring": true,
    "model_agreement_monitoring": true,
    "market_regime_monitoring": true
  }
}
```

### 4.2 Risk Management with Uncertainty Endpoint

```typescript
POST /api/v1/trading/risk-management/uncertainty-aware

Request:
{
  "portfolio": {
    "total_value": 100000,
    "open_positions": [
      {
        "symbol": "EURUSD",
        "size": 1500,
        "entry_price": 1.0850,
        "current_price": 1.0865,
        "confidence_at_entry": 0.78,
        "current_confidence": 0.72,
        "uncertainty": 0.25
      }
    ]
  },
  "new_signal": {
    "symbol": "GBPUSD",
    "direction": "SELL",
    "confidence": 0.82,
    "uncertainty": 0.18
  }
}

Response:
{
  "risk_analysis": {
    "portfolio_risk": {
      "current_exposure": 0.015,  // 1.5% of portfolio
      "confidence_weighted_exposure": 0.0108,  // Weighted by confidence
      "uncertainty_adjusted_risk": 0.019,  // Adjusted for uncertainty
      "max_drawdown_estimate": 0.025
    },

    "correlation_analysis": {
      "eur_gbp_correlation": 0.75,
      "correlation_risk_multiplier": 1.15,
      "diversification_benefit": 0.08
    }
  },

  "position_recommendation": {
    "approve_new_position": true,
    "recommended_size": 1200,
    "size_reduction_reason": "correlation_adjustment",
    "total_portfolio_risk_after": 0.032,
    "risk_limit_utilization": 0.64  // Using 64% of max risk budget
  },

  "ongoing_monitoring": {
    "positions_requiring_attention": [
      {
        "symbol": "EURUSD",
        "issue": "confidence_degradation",
        "current_confidence": 0.72,
        "threshold": 0.7,
        "recommended_action": "reduce_position_by_25_percent"
      }
    ],

    "portfolio_adjustments": {
      "rebalancing_required": false,
      "confidence_threshold_breaches": 0,
      "uncertainty_limit_breaches": 0
    }
  },

  "scenario_analysis": {
    "stress_test_results": {
      "high_uncertainty_scenario": {
        "portfolio_impact": -0.035,
        "confidence_degradation": 0.15,
        "recommended_hedge": "reduce_overall_exposure_by_20_percent"
      },
      "model_failure_scenario": {
        "fallback_strategy": "exit_all_low_confidence_positions",
        "estimated_loss": -0.018
      }
    }
  }
}
```

## 5. Enhanced Performance Analytics API (Port 8002)

### 5.1 Probabilistic Performance Analysis Endpoint

```typescript
GET /api/v1/analytics/performance/probabilistic

Query Parameters:
- period: "1d" | "7d" | "30d" | "90d"
- include_confidence_analysis: boolean
- include_uncertainty_impact: boolean
- breakdown_by_confidence_levels: boolean

Response:
{
  "analysis_period": "30d",
  "total_predictions": 3247,

  "overall_performance": {
    "accuracy": 0.76,
    "precision": 0.78,
    "recall": 0.74,
    "f1_score": 0.76,
    "sharpe_ratio": 1.89,
    "max_drawdown": -0.045,
    "total_return": 0.089
  },

  "confidence_analysis": {
    "calibration_score": 0.85,
    "brier_score": 0.182,
    "confidence_breakdown": [
      {
        "confidence_range": "0.8-1.0",
        "prediction_count": 892,
        "accuracy": 0.86,
        "avg_return": 0.0234,
        "calibration_error": 0.03
      },
      {
        "confidence_range": "0.6-0.8",
        "prediction_count": 1456,
        "accuracy": 0.74,
        "avg_return": 0.0178,
        "calibration_error": 0.05
      },
      {
        "confidence_range": "0.4-0.6",
        "prediction_count": 899,
        "accuracy": 0.68,
        "avg_return": 0.0089,
        "calibration_error": 0.08
      }
    ]
  },

  "uncertainty_impact": {
    "low_uncertainty_performance": {
      "uncertainty_range": "0.0-0.2",
      "prediction_count": 1234,
      "accuracy": 0.82,
      "avg_return": 0.0298,
      "volatility": 0.089
    },
    "high_uncertainty_performance": {
      "uncertainty_range": "0.4-1.0",
      "prediction_count": 445,
      "accuracy": 0.65,
      "avg_return": 0.0067,
      "volatility": 0.156
    }
  },

  "model_contribution": {
    "ensemble_performance": {
      "consensus_predictions": {
        "count": 2234,
        "accuracy": 0.81,
        "avg_confidence": 0.78
      },
      "conflict_predictions": {
        "count": 1013,
        "accuracy": 0.67,
        "avg_confidence": 0.65,
        "resolution_accuracy": 0.72
      }
    }
  },

  "recommendations": {
    "confidence_threshold_optimization": {
      "current_threshold": 0.7,
      "recommended_threshold": 0.75,
      "expected_accuracy_improvement": 0.04,
      "trade_volume_impact": -0.15
    },
    "uncertainty_management": {
      "high_uncertainty_position_reduction": 0.25,
      "uncertainty_monitoring_frequency": "increased",
      "additional_data_requirements": ["market_sentiment", "volume_profile"]
    }
  }
}
```

## 6. Webhook and Event-Driven API Enhancements

### 6.1 Confidence Change Webhook

```typescript
// Webhook payload for confidence changes
POST /webhook/confidence-change

Payload:
{
  "webhook_id": "uuid",
  "timestamp": "2024-01-20T10:30:00Z",
  "event_type": "confidence_change",

  "prediction_context": {
    "prediction_id": "uuid",
    "symbol": "EURUSD",
    "model_id": "xgboost_v1_2"
  },

  "confidence_change": {
    "previous_confidence": 0.78,
    "current_confidence": 0.65,
    "change_magnitude": -0.13,
    "change_reason": "market_regime_shift",
    "threshold_breach": true,
    "threshold_value": 0.7
  },

  "recommended_actions": [
    {
      "action": "reduce_position_size",
      "urgency": "medium",
      "parameter": "reduce_by_30_percent"
    },
    {
      "action": "increase_monitoring",
      "urgency": "high",
      "parameter": "check_every_30_seconds"
    }
  ]
}
```

### 6.2 Uncertainty Alert Webhook

```typescript
// Webhook payload for uncertainty alerts
POST /webhook/uncertainty-alert

Payload:
{
  "webhook_id": "uuid",
  "timestamp": "2024-01-20T10:30:00Z",
  "event_type": "uncertainty_alert",

  "uncertainty_context": {
    "symbol": "EURUSD",
    "current_uncertainty": 0.67,
    "uncertainty_threshold": 0.6,
    "uncertainty_type": "epistemic",  // or "aleatoric" or "total"
    "breach_duration_seconds": 180
  },

  "uncertainty_analysis": {
    "primary_sources": [
      {
        "source": "model_disagreement",
        "contribution": 0.45
      },
      {
        "source": "data_quality_degradation",
        "contribution": 0.32
      }
    ],
    "trend": "increasing",
    "predicted_duration": "unknown"
  },

  "risk_assessment": {
    "risk_level": "HIGH",
    "recommended_position_adjustment": -0.4,
    "alternative_strategies": [
      "wait_for_uncertainty_reduction",
      "hedge_with_correlated_asset",
      "exit_position_completely"
    ]
  }
}
```

## 7. Authentication and Rate Limiting for Probabilistic APIs

### 7.1 Enhanced Rate Limiting with Confidence Tiers

```python
# Rate limiting based on confidence requirements
CONFIDENCE_TIER_LIMITS = {
    "high_confidence": {  # Confidence > 0.8
        "requests_per_minute": 120,
        "uncertainty_analysis_per_hour": 50,
        "adaptive_learning_per_day": 1000
    },
    "medium_confidence": {  # Confidence 0.6-0.8
        "requests_per_minute": 80,
        "uncertainty_analysis_per_hour": 30,
        "adaptive_learning_per_day": 500
    },
    "low_confidence": {  # Confidence < 0.6
        "requests_per_minute": 40,
        "uncertainty_analysis_per_hour": 10,
        "adaptive_learning_per_day": 100
    }
}
```

### 7.2 API Key Permissions for Probabilistic Features

```json
{
  "api_key_permissions": {
    "basic": [
      "read:confidence_scores",
      "read:basic_uncertainty"
    ],
    "professional": [
      "read:confidence_scores",
      "read:uncertainty_analysis",
      "write:confidence_preferences",
      "read:model_performance"
    ],
    "enterprise": [
      "read:*",
      "write:*",
      "admin:model_management",
      "admin:uncertainty_configuration"
    ]
  }
}
```

This comprehensive API enhancement provides full probabilistic capabilities while maintaining backward compatibility with existing clients and ensuring proper access controls and performance optimization.