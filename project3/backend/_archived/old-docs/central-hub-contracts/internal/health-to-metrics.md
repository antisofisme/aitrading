# Internal Contract: Health Monitor to Metrics Aggregation

## Overview
Internal coordination antara Health Monitor dan Metrics Aggregation untuk real-time health analytics.

## Data Flow
```
Health Reports → Health Monitor → Metrics Aggregator → Health Analytics & Alerts
```

## Interface Specification

### Input: Health Data Processing
```javascript
{
    processing_type: "real_time_analysis" | "batch_aggregation" | "anomaly_detection",
    health_data: {
        service_name: string,
        instance_id: string,
        timestamp: number,
        metrics: {
            cpu_usage: number,
            memory_usage: number,
            active_connections: number,
            response_time_ms: number,
            error_rate: number,
            custom_metrics: object
        },
        health_status: "healthy" | "degraded" | "unhealthy" | "critical",
        anomalies: object[],
        trends: object
    },
    aggregation_requirements: {
        time_windows: string[], // ["1m", "5m", "15m", "1h"]
        aggregation_functions: string[], // ["avg", "max", "p95", "count"]
        alert_thresholds: object
    }
}
```

### Output: Metrics Update
```javascript
{
    metrics_update_id: string,
    aggregated_metrics: {
        service_name: string,
        time_window: string,
        aggregations: {
            avg_cpu: number,
            max_cpu: number,
            avg_memory: number,
            max_memory: number,
            avg_response_time: number,
            p95_response_time: number,
            total_requests: number,
            error_count: number,
            error_rate: number
        },
        health_score: number, // 0-100
        trend_indicators: {
            cpu_trend: "increasing" | "decreasing" | "stable",
            memory_trend: "increasing" | "decreasing" | "stable",
            performance_trend: "improving" | "degrading" | "stable"
        }
    },
    alert_triggers: [
        {
            alert_type: "threshold_exceeded" | "anomaly_detected" | "trend_warning",
            severity: "low" | "medium" | "high" | "critical",
            message: string,
            affected_services: string[],
            recommended_actions: string[]
        }
    ],
    storage_updates: {
        time_series_data: object[],
        historical_aggregates: object[],
        alert_history: object[]
    }
}
```

## Processing Rules

### Real-time Analysis
1. Process incoming health data within 1 second
2. Update rolling window calculations
3. Check against alert thresholds
4. Trigger immediate alerts for critical conditions

### Batch Aggregation
1. Aggregate data for specified time windows
2. Calculate statistical summaries
3. Update historical trends
4. Generate health scores

### Anomaly Detection
1. Compare current metrics against baselines
2. Identify statistical outliers
3. Detect pattern deviations
4. Generate anomaly reports

## Alert Coordination

### Threshold-based Alerts
- CPU > 90% for 5 minutes
- Memory > 95% for 3 minutes
- Response time > 5000ms average
- Error rate > 10% for 2 minutes

### Trend-based Alerts
- Continuous degradation over 30 minutes
- Capacity approaching limits
- Performance regression patterns

### Anomaly-based Alerts
- Sudden metric spikes
- Unusual traffic patterns
- Behavioral deviations

## Storage Strategy
- Real-time data: 1-hour retention in memory
- Hourly aggregates: 30-day retention
- Daily summaries: 1-year retention
- Alert history: Permanent retention