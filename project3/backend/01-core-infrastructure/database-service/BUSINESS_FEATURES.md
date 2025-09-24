# Database Service Business Features

## 🎯 Purpose
**Multi-tenant business data management** untuk Database Service yang mengimplementasikan subscription-based data storage, tenant isolation, dan revenue-optimized database operations sesuai Plan1/2/3 requirements.

---

## 💼 Business Requirements Implementation

### **Revenue Data Management**
- **Subscription data storage**: User tiers, billing cycles, payment history
- **Usage analytics storage**: Detailed usage tracking untuk accurate billing
- **Multi-tenant isolation**: Complete data separation per company
- **Compliance data**: Audit trails, regulatory reporting data

### **Performance-Based Storage Strategy**
- **Tier-based storage allocation**: Different storage limits per subscription tier
- **Query performance optimization**: Faster queries for premium users
- **Backup strategies**: Enhanced backup for premium tiers
- **Data retention policies**: Longer retention for higher tiers

---

## 🏢 Multi-Tenant Database Schema Design

### **Company-Level Schema Isolation**
```sql
-- Dynamic schema creation untuk new companies
CREATE OR REPLACE FUNCTION create_company_schema(company_id VARCHAR(50))
RETURNS VOID AS $$
DECLARE
    schema_name VARCHAR(60);
BEGIN
    schema_name := 'tenant_' || company_id;

    -- Create company-specific schema
    EXECUTE format('CREATE SCHEMA IF NOT EXISTS %I', schema_name);

    -- Set appropriate permissions
    EXECUTE format('GRANT USAGE ON SCHEMA %I TO database_service_role', schema_name);

    -- Create company-specific tables
    PERFORM create_company_tables(schema_name);

    -- Initialize company configuration
    PERFORM initialize_company_config(company_id, schema_name);
END;
$$ LANGUAGE plpgsql;

-- Company-specific table creation
CREATE OR REPLACE FUNCTION create_company_tables(schema_name VARCHAR(60))
RETURNS VOID AS $$
BEGIN
    -- Users table per company
    EXECUTE format('
        CREATE TABLE %I.users (
            user_id VARCHAR(50) PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            subscription_tier VARCHAR(20) NOT NULL DEFAULT ''free'',
            subscription_status VARCHAR(20) NOT NULL DEFAULT ''active'',
            subscription_start_date TIMESTAMPTZ,
            subscription_end_date TIMESTAMPTZ,
            subscription_limits JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            last_activity TIMESTAMPTZ DEFAULT NOW()
        )', schema_name);

    -- MT5 accounts per company
    EXECUTE format('
        CREATE TABLE %I.mt5_accounts (
            account_id BIGINT PRIMARY KEY,
            user_id VARCHAR(50) REFERENCES %I.users(user_id),
            account_number VARCHAR(50) NOT NULL,
            broker VARCHAR(100),
            account_type VARCHAR(20) CHECK (account_type IN (''demo'', ''live'')),
            balance DECIMAL(15,2),
            equity DECIMAL(15,2),
            margin DECIMAL(15,2),
            leverage INTEGER,
            currency VARCHAR(3) DEFAULT ''USD'',
            status VARCHAR(20) DEFAULT ''active'',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            last_sync TIMESTAMPTZ DEFAULT NOW()
        )', schema_name, schema_name);

    -- Trading positions per company
    EXECUTE format('
        CREATE TABLE %I.trading_positions (
            position_id BIGSERIAL PRIMARY KEY,
            user_id VARCHAR(50) REFERENCES %I.users(user_id),
            mt5_account_id BIGINT REFERENCES %I.mt5_accounts(account_id),
            symbol VARCHAR(20) NOT NULL,
            position_type VARCHAR(10) CHECK (position_type IN (''buy'', ''sell'')),
            volume DECIMAL(10,2) NOT NULL,
            open_price DECIMAL(10,5) NOT NULL,
            current_price DECIMAL(10,5),
            stop_loss DECIMAL(10,5),
            take_profit DECIMAL(10,5),
            profit_loss DECIMAL(15,2),
            opened_at TIMESTAMPTZ DEFAULT NOW(),
            closed_at TIMESTAMPTZ,
            status VARCHAR(20) DEFAULT ''open''
        )', schema_name, schema_name, schema_name);

    -- Create indexes untuk performance
    EXECUTE format('CREATE INDEX idx_%I_users_subscription ON %I.users(subscription_tier, subscription_status)',
                  replace(schema_name, 'tenant_', ''), schema_name);
    EXECUTE format('CREATE INDEX idx_%I_positions_user_symbol ON %I.trading_positions(user_id, symbol, status)',
                  replace(schema_name, 'tenant_', ''), schema_name);
END;
$$ LANGUAGE plpgsql;
```

### **Subscription-Based Storage Limits**
```sql
-- Business logic untuk storage limits per subscription tier
CREATE OR REPLACE FUNCTION check_storage_quota(company_id VARCHAR(50), data_size_mb INTEGER)
RETURNS BOOLEAN AS $$
DECLARE
    company_tier VARCHAR(20);
    current_usage_mb INTEGER;
    storage_limit_mb INTEGER;
    schema_name VARCHAR(60);
BEGIN
    schema_name := 'tenant_' || company_id;

    -- Get company's subscription tier
    EXECUTE format('SELECT subscription_tier FROM %I.users LIMIT 1', schema_name)
    INTO company_tier;

    -- Define storage limits per tier
    storage_limit_mb := CASE company_tier
        WHEN 'free' THEN 100        -- 100MB for free tier
        WHEN 'pro' THEN 10240       -- 10GB for pro tier
        WHEN 'enterprise' THEN -1   -- Unlimited for enterprise
        ELSE 100
    END;

    -- Check if enterprise (unlimited)
    IF storage_limit_mb = -1 THEN
        RETURN TRUE;
    END IF;

    -- Calculate current storage usage
    SELECT COALESCE(
        (SELECT pg_total_relation_size(schemaname||'.'||tablename)
         FROM pg_tables WHERE schemaname = schema_name) / 1024 / 1024, 0)
    INTO current_usage_mb;

    -- Check if adding new data would exceed limit
    RETURN (current_usage_mb + data_size_mb) <= storage_limit_mb;
END;
$$ LANGUAGE plpgsql;

-- Business logic untuk automatic cleanup berdasarkan tier
CREATE OR REPLACE FUNCTION cleanup_old_data_by_tier(company_id VARCHAR(50))
RETURNS INTEGER AS $$
DECLARE
    schema_name VARCHAR(60);
    company_tier VARCHAR(20);
    retention_days INTEGER;
    deleted_rows INTEGER := 0;
BEGIN
    schema_name := 'tenant_' || company_id;

    -- Get company tier
    EXECUTE format('SELECT subscription_tier FROM %I.users LIMIT 1', schema_name)
    INTO company_tier;

    -- Set retention policy berdasarkan tier
    retention_days := CASE company_tier
        WHEN 'free' THEN 30         -- 30 days retention
        WHEN 'pro' THEN 365         -- 1 year retention
        WHEN 'enterprise' THEN 1095 -- 3 years retention
        ELSE 30
    END;

    -- Cleanup old trading data
    EXECUTE format('
        DELETE FROM %I.trading_positions
        WHERE closed_at < NOW() - INTERVAL ''%s days''
    ', schema_name, retention_days);

    GET DIAGNOSTICS deleted_rows = ROW_COUNT;

    -- Log cleanup activity
    INSERT INTO public.data_cleanup_log (company_id, retention_days, deleted_rows, cleanup_date)
    VALUES (company_id, retention_days, deleted_rows, NOW());

    RETURN deleted_rows;
END;
$$ LANGUAGE plpgsql;
```

---

## 📊 Multi-Database Business Operations

### **Usage Analytics Storage (ClickHouse)**
```sql
-- ClickHouse schema untuk usage analytics dan billing
CREATE TABLE usage_tracking (
    user_id String,
    company_id String,
    timestamp DateTime,
    subscription_tier LowCardinality(String),
    service_name LowCardinality(String),
    api_endpoint String,
    data_points_consumed UInt32,
    processing_time_ms Float32,
    billing_period String,
    revenue_attributed Float32
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (company_id, user_id, timestamp)
TTL timestamp + INTERVAL 2 YEAR; -- Auto-cleanup after 2 years

-- Business intelligence aggregation table
CREATE MATERIALIZED VIEW usage_analytics_hourly
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (company_id, subscription_tier, service_name, toStartOfHour(timestamp))
AS SELECT
    company_id,
    subscription_tier,
    service_name,
    toStartOfHour(timestamp) as hour,
    count() as total_requests,
    sum(data_points_consumed) as total_data_points,
    avg(processing_time_ms) as avg_processing_time,
    sum(revenue_attributed) as total_revenue
FROM usage_tracking
GROUP BY company_id, subscription_tier, service_name, hour;

-- Monthly billing aggregation
CREATE MATERIALIZED VIEW billing_monthly
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (company_id, user_id, billing_period)
AS SELECT
    company_id,
    user_id,
    subscription_tier,
    billing_period,
    count() as total_api_calls,
    sum(data_points_consumed) as total_data_consumption,
    sum(revenue_attributed) as monthly_revenue_attributed,
    max(timestamp) as last_activity
FROM usage_tracking
GROUP BY company_id, user_id, subscription_tier, billing_period;
```

### **Real-Time Subscription Cache (DragonflyDB)**
```python
class SubscriptionCacheManager:
    """Business logic untuk subscription data caching dengan DragonflyDB"""

    def __init__(self):
        self.cache = DragonflyDBClient()
        self.cache_ttl = {
            'subscription_data': 3600,      # 1 hour
            'usage_quota': 900,             # 15 minutes
            'tier_limits': 7200,            # 2 hours
            'billing_period': 86400         # 24 hours
        }

    async def cache_user_subscription(self, user_id: str, subscription_data: dict):
        """Cache user subscription data untuk fast access"""
        cache_key = f"subscription:{user_id}"

        # Enrich dengan business logic
        enhanced_data = {
            **subscription_data,
            'tier_limits': await self._get_tier_limits(subscription_data['subscription_tier']),
            'usage_quota': await self._get_usage_quota(user_id),
            'billing_status': await self._get_billing_status(user_id),
            'cached_at': datetime.utcnow().isoformat()
        }

        await self.cache.setex(
            cache_key,
            self.cache_ttl['subscription_data'],
            json.dumps(enhanced_data)
        )

    async def get_user_subscription(self, user_id: str) -> dict:
        """Get user subscription dengan cache-first strategy"""
        cache_key = f"subscription:{user_id}"
        cached_data = await self.cache.get(cache_key)

        if cached_data:
            return json.loads(cached_data)

        # Cache miss - load from PostgreSQL
        subscription_data = await self._load_from_database(user_id)
        if subscription_data:
            await self.cache_user_subscription(user_id, subscription_data)
            return subscription_data

        return None

    async def update_usage_quota(self, user_id: str, usage_increment: int):
        """Update real-time usage quota dengan atomic operations"""
        quota_key = f"quota:{user_id}:{datetime.now().strftime('%Y-%m-%d')}"

        # Atomic increment
        current_usage = await self.cache.incr(quota_key, usage_increment)

        # Set TTL if new key
        if current_usage == usage_increment:
            # New key, set TTL to end of day
            ttl = (datetime.now().replace(hour=23, minute=59, second=59) - datetime.now()).seconds
            await self.cache.expire(quota_key, ttl)

        return current_usage

    async def check_quota_exceeded(self, user_id: str) -> dict:
        """Business logic untuk quota checking"""
        subscription_data = await self.get_user_subscription(user_id)
        if not subscription_data:
            return {'exceeded': True, 'reason': 'no_subscription'}

        tier_limits = subscription_data.get('tier_limits', {})
        daily_limit = tier_limits.get('daily_api_calls', 1000)

        if daily_limit == 'unlimited':
            return {'exceeded': False, 'usage': 'unlimited'}

        current_usage = await self.get_daily_usage(user_id)
        exceeded = current_usage >= daily_limit

        return {
            'exceeded': exceeded,
            'current_usage': current_usage,
            'daily_limit': daily_limit,
            'usage_percentage': (current_usage / daily_limit) * 100,
            'reset_time': self._get_quota_reset_time()
        }

    async def cache_company_configuration(self, company_id: str, config_data: dict):
        """Cache company-wide configuration"""
        config_key = f"company_config:{company_id}"

        # Add business logic validation
        validated_config = await self._validate_company_config(config_data)

        await self.cache.setex(
            config_key,
            self.cache_ttl['tier_limits'],
            json.dumps(validated_config)
        )

    async def _validate_company_config(self, config_data: dict) -> dict:
        """Business validation untuk company configuration"""
        # Ensure required business fields
        required_fields = ['company_id', 'subscription_tier', 'max_users', 'billing_email']
        for field in required_fields:
            if field not in config_data:
                raise ValueError(f"Missing required field: {field}")

        # Add business defaults
        config_data.setdefault('features_enabled', self._get_default_features(config_data['subscription_tier']))
        config_data.setdefault('support_level', self._get_support_level(config_data['subscription_tier']))

        return config_data

    def _get_default_features(self, subscription_tier: str) -> list:
        """Business logic untuk default features per tier"""
        features_map = {
            'free': ['basic_trading', 'email_notifications'],
            'pro': ['basic_trading', 'advanced_analytics', 'email_notifications', 'sms_notifications', 'api_access'],
            'enterprise': ['all_features']
        }
        return features_map.get(subscription_tier, features_map['free'])
```

---

## 🔄 Business Data Operations

### **Subscription Management Operations**
```python
class SubscriptionBusinessLogic:
    """Core business operations untuk subscription management"""

    def __init__(self):
        self.postgres_db = PostgreSQLService()
        self.clickhouse_db = ClickHouseService()
        self.cache = SubscriptionCacheManager()

    async def create_new_subscription(self, company_data: dict, initial_user: dict) -> dict:
        """Business logic untuk creating new company subscription"""

        # 1. Create company schema
        company_id = company_data['company_id']
        await self._create_company_database_schema(company_id)

        # 2. Insert initial user dengan free tier
        user_data = {
            **initial_user,
            'subscription_tier': 'free',
            'subscription_status': 'active',
            'subscription_start_date': datetime.utcnow(),
            'subscription_limits': self._get_tier_limits('free')
        }

        await self._insert_user_to_company_schema(company_id, user_data)

        # 3. Initialize company configuration
        company_config = {
            **company_data,
            'created_at': datetime.utcnow(),
            'subscription_tier': 'free',
            'max_users': 1,
            'features_enabled': self._get_default_features('free')
        }

        await self._insert_company_config(company_config)

        # 4. Cache initial data
        await self.cache.cache_user_subscription(user_data['user_id'], user_data)
        await self.cache.cache_company_configuration(company_id, company_config)

        # 5. Initialize usage tracking
        await self._initialize_usage_tracking(company_id, user_data['user_id'])

        return {
            'company_id': company_id,
            'initial_user_id': user_data['user_id'],
            'subscription_tier': 'free',
            'database_schema': f"tenant_{company_id}",
            'created_at': datetime.utcnow()
        }

    async def upgrade_subscription(self, company_id: str, new_tier: str, payment_data: dict) -> dict:
        """Business logic untuk subscription upgrades"""

        # 1. Validate upgrade path
        current_subscription = await self._get_company_subscription(company_id)
        if not self._is_valid_upgrade(current_subscription['tier'], new_tier):
            raise ValueError(f"Invalid upgrade from {current_subscription['tier']} to {new_tier}")

        # 2. Calculate prorated billing
        billing_adjustment = await self._calculate_prorated_billing(
            company_id, current_subscription['tier'], new_tier
        )

        # 3. Update all users in company
        schema_name = f"tenant_{company_id}"
        await self.postgres_db.execute(f"""
            UPDATE {schema_name}.users
            SET subscription_tier = %s,
                subscription_limits = %s,
                updated_at = NOW()
        """, [new_tier, json.dumps(self._get_tier_limits(new_tier))])

        # 4. Update company configuration
        await self._update_company_tier(company_id, new_tier)

        # 5. Record billing transaction
        await self._record_billing_transaction({
            'company_id': company_id,
            'transaction_type': 'upgrade',
            'old_tier': current_subscription['tier'],
            'new_tier': new_tier,
            'amount': billing_adjustment['amount'],
            'payment_data': payment_data
        })

        # 6. Invalidate cache
        await self._invalidate_company_cache(company_id)

        # 7. Apply new tier benefits immediately
        await self._apply_tier_benefits(company_id, new_tier)

        return {
            'company_id': company_id,
            'upgraded_from': current_subscription['tier'],
            'upgraded_to': new_tier,
            'billing_adjustment': billing_adjustment,
            'effective_date': datetime.utcnow()
        }

    async def handle_subscription_expiry(self, company_id: str) -> dict:
        """Business logic untuk handling expired subscriptions"""

        # 1. Downgrade to free tier
        await self._downgrade_to_free_tier(company_id)

        # 2. Apply free tier restrictions
        restrictions_applied = await self._apply_free_tier_restrictions(company_id)

        # 3. Notify users about expiry
        await self._notify_subscription_expiry(company_id)

        # 4. Record expiry event
        await self._record_subscription_event(company_id, 'expired')

        return {
            'company_id': company_id,
            'action': 'downgraded_to_free',
            'restrictions_applied': restrictions_applied,
            'expiry_handled_at': datetime.utcnow()
        }

    async def _apply_tier_benefits(self, company_id: str, new_tier: str):
        """Apply immediate benefits dari tier upgrade"""
        tier_benefits = {
            'pro': {
                'increased_storage': '10GB',
                'advanced_features': ['real_time_alerts', 'advanced_charts'],
                'support_level': 'email'
            },
            'enterprise': {
                'unlimited_storage': True,
                'premium_features': ['ai_predictions', 'custom_indicators', 'api_access'],
                'support_level': 'phone',
                'dedicated_resources': True
            }
        }

        benefits = tier_benefits.get(new_tier, {})

        # Update database dengan new benefits
        if benefits.get('unlimited_storage'):
            await self._enable_unlimited_storage(company_id)

        if benefits.get('premium_features'):
            await self._enable_premium_features(company_id, benefits['premium_features'])

        # Update cache dengan new capabilities
        await self._update_tier_cache(company_id, new_tier, benefits)
```

---

## 📊 Revenue Analytics & Business Intelligence

### **Revenue Tracking Database Operations**
```python
class RevenueAnalyticsManager:
    """Business intelligence dan revenue tracking operations"""

    async def calculate_company_revenue(self, company_id: str, period_months: int = 12) -> dict:
        """Calculate comprehensive revenue data untuk company"""

        # Monthly revenue dari ClickHouse
        revenue_query = """
        SELECT
            toStartOfMonth(timestamp) as month,
            subscription_tier,
            sum(revenue_attributed) as monthly_revenue,
            count(distinct user_id) as active_users,
            sum(total_api_calls) as total_api_usage
        FROM billing_monthly
        WHERE company_id = ? AND timestamp >= subtractMonths(now(), ?)
        GROUP BY month, subscription_tier
        ORDER BY month DESC
        """

        revenue_data = await self.clickhouse_db.query(revenue_query, [company_id, period_months])

        # Calculate trends dan insights
        total_revenue = sum(row['monthly_revenue'] for row in revenue_data)
        avg_monthly_revenue = total_revenue / period_months if period_months > 0 else 0

        # Growth analysis
        revenue_trend = self._calculate_revenue_trend(revenue_data)

        # User tier distribution
        tier_distribution = self._analyze_tier_distribution(revenue_data)

        return {
            'company_id': company_id,
            'period_months': period_months,
            'total_revenue': total_revenue,
            'avg_monthly_revenue': avg_monthly_revenue,
            'revenue_trend': revenue_trend,
            'tier_distribution': tier_distribution,
            'monthly_breakdown': revenue_data,
            'analysis_date': datetime.utcnow()
        }

    async def identify_upsell_opportunities(self, company_id: str) -> list:
        """Identify users yang candidates untuk tier upgrades"""

        # Find heavy users yang might benefit dari upgrades
        heavy_usage_query = """
        SELECT
            user_id,
            subscription_tier,
            avg(total_api_calls) as avg_daily_calls,
            avg(total_data_consumption) as avg_daily_data,
            count() as active_days
        FROM billing_monthly
        WHERE company_id = ? AND timestamp >= subtractMonths(now(), 1)
        GROUP BY user_id, subscription_tier
        HAVING avg_daily_calls > (
            CASE subscription_tier
                WHEN 'free' THEN 800    -- 80% of free limit
                WHEN 'pro' THEN 40000   -- 80% of pro limit
                ELSE 999999
            END
        )
        ORDER BY avg_daily_calls DESC
        """

        heavy_users = await self.clickhouse_db.query(heavy_usage_query, [company_id])

        upsell_opportunities = []
        for user in heavy_users:
            opportunity_score = self._calculate_upsell_score(user)
            recommended_tier = self._recommend_tier_upgrade(user['subscription_tier'], user['avg_daily_calls'])

            upsell_opportunities.append({
                'user_id': user['user_id'],
                'current_tier': user['subscription_tier'],
                'recommended_tier': recommended_tier,
                'opportunity_score': opportunity_score,
                'current_usage': {
                    'avg_daily_calls': user['avg_daily_calls'],
                    'avg_daily_data': user['avg_daily_data'],
                    'active_days': user['active_days']
                },
                'potential_revenue_increase': self._calculate_revenue_increase(
                    user['subscription_tier'], recommended_tier
                )
            })

        return upsell_opportunities

    async def generate_churn_risk_analysis(self, company_id: str) -> dict:
        """Analyze churn risk berdasarkan usage patterns"""

        # Users dengan declining usage
        declining_usage_query = """
        SELECT
            user_id,
            subscription_tier,
            arrayElement(groupArray(total_api_calls), -1) as current_month_calls,
            arrayElement(groupArray(total_api_calls), -2) as previous_month_calls,
            arrayElement(groupArray(total_api_calls), -3) as two_months_ago_calls
        FROM billing_monthly
        WHERE company_id = ? AND timestamp >= subtractMonths(now(), 3)
        GROUP BY user_id, subscription_tier
        HAVING current_month_calls < previous_month_calls
           AND previous_month_calls < two_months_ago_calls
        """

        declining_users = await self.clickhouse_db.query(declining_usage_query, [company_id])

        churn_risks = []
        for user in declining_users:
            churn_risk_score = self._calculate_churn_risk(user)
            retention_strategy = self._recommend_retention_strategy(user, churn_risk_score)

            churn_risks.append({
                'user_id': user['user_id'],
                'subscription_tier': user['subscription_tier'],
                'churn_risk_score': churn_risk_score,
                'usage_trend': {
                    'current_month': user['current_month_calls'],
                    'previous_month': user['previous_month_calls'],
                    'two_months_ago': user['two_months_ago_calls'],
                    'decline_percentage': self._calculate_decline_percentage(user)
                },
                'retention_strategy': retention_strategy
            })

        return {
            'company_id': company_id,
            'total_at_risk_users': len(churn_risks),
            'churn_risks': churn_risks,
            'recommended_actions': self._recommend_company_retention_actions(churn_risks),
            'analysis_date': datetime.utcnow()
        }

    def _calculate_upsell_score(self, user_data: dict) -> float:
        """Calculate upsell opportunity score (0-100)"""
        usage_score = min(user_data['avg_daily_calls'] / 1000, 1.0) * 40  # 40% weight
        activity_score = min(user_data['active_days'] / 30, 1.0) * 30     # 30% weight
        tier_score = {'free': 30, 'pro': 20, 'enterprise': 0}[user_data['subscription_tier']]  # 30% weight

        return usage_score + activity_score + tier_score

    def _calculate_churn_risk(self, user_data: dict) -> float:
        """Calculate churn risk score (0-100, higher = more risk)"""
        current = user_data['current_month_calls']
        previous = user_data['previous_month_calls']
        two_months = user_data['two_months_ago_calls']

        # Calculate decline rate
        if two_months > 0:
            decline_rate = (two_months - current) / two_months
            return min(decline_rate * 100, 100)

        return 50  # Default medium risk
```

---

## 🔗 Service Integration Points

### **Data Bridge Integration**
```python
# Real-time subscription validation
async def validate_user_subscription(user_id: str) -> dict:
    subscription_data = await database_service.get_user_subscription(user_id)
    return {
        'valid': subscription_data['subscription_status'] == 'active',
        'tier': subscription_data['subscription_tier'],
        'limits': subscription_data['subscription_limits']
    }

# Usage tracking storage
async def record_usage_event(usage_data: dict):
    await database_service.clickhouse_insert('usage_tracking', usage_data)
    await database_service.update_usage_quota(usage_data['user_id'], usage_data['data_points'])
```

### **Central Hub Integration**
```python
# Company configuration distribution
async def distribute_company_config(company_id: str):
    config = await database_service.get_company_configuration(company_id)
    await central_hub.broadcast_config_update(company_id, config)

# Business metrics reporting
async def report_business_metrics():
    metrics = await database_service.get_business_metrics()
    await central_hub.report_metrics('database-service', metrics)
```

### **Billing Service Integration**
```python
# Monthly billing data export
async def export_billing_data(company_id: str, billing_period: str):
    billing_data = await database_service.generate_billing_export(company_id, billing_period)
    await billing_service.process_monthly_billing(billing_data)
```

---

## 🎯 Business Success Metrics

### **Revenue Metrics**
- **Revenue per User (ARPU)**: Track monthly ARPU per tier
- **Subscription Conversion**: Free → Pro conversion rate (target: 15%)
- **Customer Lifetime Value (CLV)**: Average CLV per subscription tier
- **Churn Rate**: Monthly churn rate per tier (target: <5%)

### **Data Operations Metrics**
- **Storage Efficiency**: Storage cost per dollar of revenue
- **Query Performance per Tier**: Meet SLA targets for each tier
- **Data Retention Compliance**: 100% compliance with tier-based retention policies
- **Multi-tenant Isolation**: Zero cross-tenant data leakage incidents

### **Business Intelligence Metrics**
- **Upsell Success Rate**: Successful tier upgrades from recommendations
- **Usage Trend Accuracy**: Accuracy of churn risk predictions
- **Revenue Forecast Accuracy**: Monthly revenue prediction accuracy
- **Customer Health Score**: Overall customer health across all tenants

---

**Key Innovation**: Revenue-optimized multi-tenant database architecture yang tidak hanya menyimpan data, tetapi actively drives business growth melalui intelligent analytics, automated upselling, dan proactive churn prevention.