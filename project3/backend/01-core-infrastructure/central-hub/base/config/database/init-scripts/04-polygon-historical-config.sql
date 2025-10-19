--
-- Polygon Historical Downloader Service Configuration
-- Centralized operational config for gap filling service
--

-- Insert operational config for polygon-historical-downloader
INSERT INTO service_configs (service_name, config_data, version, active, created_by)
VALUES (
    'polygon-historical-downloader',
    '{
        "operational": {
            "symbols": ["EURUSD", "XAUUSD", "GBPUSD"],
            "timeframes": ["5m", "15m", "30m", "1h", "4h", "1d", "1w"],
            "check_period_days": 7,
            "completeness_threshold_intraday": 1.0,
            "completeness_threshold_daily": 0.8,
            "batch_size": 150,
            "schedule": {
                "hourly_check": "0 * * * *",
                "daily_check": "0 1 * * *",
                "weekly_check": "0 2 * * 0"
            },
            "gap_detection": {
                "enabled": true,
                "max_gap_days": 7
            },
            "download": {
                "start_date": "today-7days",
                "end_date": "today",
                "rate_limit_per_sec": 5
            }
        }
    }'::jsonb,
    1,
    true,
    'system'
)
ON CONFLICT (service_name, version) DO UPDATE
SET
    config_data = EXCLUDED.config_data,
    active = EXCLUDED.active,
    updated_at = CURRENT_TIMESTAMP;

-- Verify insertion
SELECT
    service_name,
    version,
    active,
    created_at,
    config_data->'operational'->'symbols' as symbols,
    config_data->'operational'->'check_period_days' as check_period
FROM service_configs
WHERE service_name = 'polygon-historical-downloader';
