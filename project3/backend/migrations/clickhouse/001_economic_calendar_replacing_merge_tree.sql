-- Migration: Convert economic_calendar to ReplacingMergeTree
-- This allows automatic deduplication - latest collected_at wins
-- Perfect for UPDATE scenario (event gets actual value later)

-- Step 1: Create new table with ReplacingMergeTree engine
CREATE TABLE IF NOT EXISTS suho_analytics.external_economic_calendar_new
(
    `date` Date,
    `time` String,
    `currency` String,
    `event` String,
    `forecast` Nullable(String),
    `previous` Nullable(String),
    `actual` Nullable(String),
    `impact` String,
    `source` String DEFAULT 'mql5',
    `collected_at` DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree(collected_at)  -- Version column: latest wins
ORDER BY (date, time, currency, event)     -- Deduplication key
TTL toDateTime(date) + toIntervalDay(730)
SETTINGS index_granularity = 8192;

-- Step 2: Copy existing data
INSERT INTO suho_analytics.external_economic_calendar_new
SELECT * FROM suho_analytics.external_economic_calendar;

-- Step 3: Drop old table
DROP TABLE suho_analytics.external_economic_calendar;

-- Step 4: Rename new table to original name
RENAME TABLE suho_analytics.external_economic_calendar_new
TO suho_analytics.external_economic_calendar;

-- Step 5: Force merge to apply deduplication
OPTIMIZE TABLE suho_analytics.external_economic_calendar FINAL;
