# Data Bridge Business Features

## 🎯 Purpose
**Multi-tenant business logic implementation** untuk Data Bridge Service yang mengimplementasikan subscription-based data filtering, usage tracking, dan tier-based validation sesuai Plan1/2/3 requirements.

---

## 💼 Business Requirements Implementation

### **Revenue Protection & Subscription Enforcement**
- **Subscription tier validation**: Real-time enforcement of Free/Pro/Enterprise limits
- **Data access control**: Symbol filtering, update frequency throttling per tier
- **Usage tracking**: Accurate billing data collection untuk semua API calls
- **Fair usage enforcement**: Rate limiting dan quota management per tenant

### **Multi-Tenant Isolation & Performance**
- **Tenant data isolation**: Complete separation antar company data streams
- **User session management**: Independent data flows per individual user
- **Performance SLAs**: Tier-specific performance guarantees
- **Resource allocation**: Fair resource distribution berdasarkan subscription tier

---

## 🏢 Multi-Tenant Data Filtering Engine

### **Subscription Tier Configuration**
```python
class SubscriptionTierConfig:
    """Business logic untuk subscription tier limits"""

    TIER_LIMITS = {
        'free': {
            'symbols': ['EURUSD', 'GBPUSD', 'USDJPY', 'EURGBP', 'AUDUSD'],  # 5 major pairs
            'update_frequency_ms': 1000,  # 1 second updates
            'data_quality': 'basic',
            'daily_api_calls': 1000,
            'concurrent_connections': 1,
            'historical_data_days': 7,
            'sla_uptime': 0.99,  # 99% uptime
            'support_level': 'community'
        },
        'pro': {
            'symbols': 'major_pairs',  # 28 major forex pairs
            'update_frequency_ms': 100,  # 100ms updates
            'data_quality': 'high',
            'daily_api_calls': 50000,
            'concurrent_connections': 5,
            'historical_data_days': 90,
            'sla_uptime': 0.999,  # 99.9% uptime
            'support_level': 'email'
        },
        'enterprise': {
            'symbols': 'all',  # All available symbols
            'update_frequency_ms': 10,  # 10ms updates (real-time)
            'data_quality': 'premium',
            'daily_api_calls': 'unlimited',
            'concurrent_connections': 50,
            'historical_data_days': 365,
            'sla_uptime': 0.9999,  # 99.99% uptime
            'support_level': 'phone'
        }
    }

    @classmethod
    def get_tier_limits(cls, subscription_tier: str) -> dict:
        """Get limits untuk specific subscription tier"""
        return cls.TIER_LIMITS.get(subscription_tier, cls.TIER_LIMITS['free'])

    @classmethod
    def validate_tier_access(cls, user_context: dict, requested_action: str) -> bool:
        """Validate if user's tier allows requested action"""
        tier_limits = cls.get_tier_limits(user_context['subscription_tier'])

        # Implementation validation logic berdasarkan requested_action
        # Returns True if allowed, False if upgrade required
        pass
```

### **Real-Time Data Filtering Implementation**
```python
class MultiTenantDataFilter:
    """Core business logic untuk real-time data filtering per subscription tier"""

    def __init__(self):
        self.tier_config = SubscriptionTierConfig()
        self.usage_tracker = UsageTracker()
        self.performance_monitor = PerformanceMonitor()

    async def filter_market_data(self, raw_data: List[MarketTick], user_context: dict) -> FilteredData:
        """
        Main business logic: Filter market data berdasarkan user's subscription tier
        """
        start_time = time.time()
        tier_limits = self.tier_config.get_tier_limits(user_context['subscription_tier'])

        # 1. Symbol Filtering (Business Rule)
        allowed_symbols = await self._get_allowed_symbols(tier_limits['symbols'])
        filtered_symbols = [tick for tick in raw_data if tick.symbol in allowed_symbols]

        # 2. Update Frequency Throttling (Business Rule)
        throttled_data = await self._apply_frequency_throttling(
            filtered_symbols,
            tier_limits['update_frequency_ms'],
            user_context['user_id']
        )

        # 3. Data Quality Enhancement (Business Rule)
        quality_enhanced_data = await self._apply_quality_filter(
            throttled_data,
            tier_limits['data_quality']
        )

        # 4. Usage Tracking (Business Revenue)
        await self.usage_tracker.record_data_consumption(
            user_context=user_context,
            data_points=len(quality_enhanced_data),
            processing_time=time.time() - start_time
        )

        # 5. Performance SLA Monitoring (Business SLA)
        await self.performance_monitor.record_user_performance(
            user_context=user_context,
            processing_time=time.time() - start_time,
            expected_sla=tier_limits['sla_uptime']
        )

        return FilteredData(
            data=quality_enhanced_data,
            tier_applied=user_context['subscription_tier'],
            filter_stats=self._generate_filter_stats(raw_data, quality_enhanced_data),
            billing_info=await self.usage_tracker.get_current_usage(user_context['user_id'])
        )

    async def _get_allowed_symbols(self, symbol_config: str) -> List[str]:
        """Business logic untuk symbol access per tier"""
        if symbol_config == 'all':
            return await self.get_all_available_symbols()
        elif symbol_config == 'major_pairs':
            return [
                'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'USDCAD', 'AUDUSD', 'NZDUSD',
                'EURGBP', 'EURJPY', 'EURCHF', 'EURCAD', 'EURAUD', 'EURNZD', 'GBPJPY',
                'GBPCHF', 'GBPCAD', 'GBPAUD', 'GBPNZD', 'CHFJPY', 'CADJPY', 'AUDJPY',
                'NZDJPY', 'AUDCAD', 'AUDCHF', 'AUDNZD', 'CADCHF', 'NZDCAD', 'NZDCHF'
            ]
        elif isinstance(symbol_config, list):
            return symbol_config
        else:
            return ['EURUSD']  # Default fallback

    async def _apply_frequency_throttling(self, data: List[MarketTick],
                                        frequency_ms: int, user_id: str) -> List[MarketTick]:
        """Business logic untuk update frequency control"""
        last_update_cache_key = f"last_update:{user_id}"
        current_time = time.time() * 1000  # Convert to milliseconds

        last_update = await self.cache_service.get(last_update_cache_key)

        if last_update and (current_time - last_update) < frequency_ms:
            # Frequency limit not yet reached, return empty data
            return []

        # Update last update timestamp
        await self.cache_service.set(last_update_cache_key, current_time, ttl=3600)

        return data

    async def _apply_quality_filter(self, data: List[MarketTick], quality_level: str) -> List[MarketTick]:
        """Business logic untuk data quality enhancement per tier"""
        if quality_level == 'basic':
            # Basic quality: Remove obvious outliers only
            return [tick for tick in data if self._is_basic_valid(tick)]

        elif quality_level == 'high':
            # High quality: Advanced market validation + spread analysis
            validated_data = []
            for tick in data:
                if self._is_basic_valid(tick) and await self._is_market_hours_valid(tick):
                    tick.quality_score = await self._calculate_quality_score(tick)
                    validated_data.append(tick)
            return validated_data

        elif quality_level == 'premium':
            # Premium quality: AI-enhanced validation + signal enrichment
            premium_data = []
            for tick in data:
                if await self._is_premium_quality(tick):
                    tick.quality_score = await self._calculate_premium_quality_score(tick)
                    tick.market_context = await self._enrich_market_context(tick)
                    tick.liquidity_score = await self._calculate_liquidity_score(tick)
                    premium_data.append(tick)
            return premium_data

        return data

    def _generate_filter_stats(self, original_data: List[MarketTick],
                             filtered_data: List[MarketTick]) -> dict:
        """Generate filtering statistics untuk user transparency"""
        return {
            'original_count': len(original_data),
            'filtered_count': len(filtered_data),
            'filter_efficiency': len(filtered_data) / len(original_data) if original_data else 0,
            'symbols_available': len(set(tick.symbol for tick in filtered_data)),
            'quality_improvement': 'applied' if len(filtered_data) < len(original_data) else 'none'
        }
```

---

## 📊 Usage Tracking & Billing Integration

### **Real-Time Usage Monitoring**
```python
class UsageTracker:
    """Business logic untuk accurate usage tracking dan billing data"""

    def __init__(self):
        self.db_service = DatabaseService()
        self.cache_service = DragonflyDBService()

    async def record_data_consumption(self, user_context: dict, data_points: int, processing_time: float):
        """Record data consumption untuk billing purposes"""
        usage_record = {
            'user_id': user_context['user_id'],
            'company_id': user_context['company_id'],
            'timestamp': datetime.utcnow(),
            'data_points_consumed': data_points,
            'processing_time_ms': processing_time * 1000,
            'subscription_tier': user_context['subscription_tier'],
            'api_endpoint': 'data_bridge_stream',
            'billing_period': self._get_current_billing_period()
        }

        # Store untuk billing calculation
        await self.db_service.clickhouse_insert('usage_tracking', usage_record)

        # Update real-time counters untuk quota enforcement
        await self._update_real_time_usage(user_context['user_id'], data_points)

    async def _update_real_time_usage(self, user_id: str, data_points: int):
        """Update real-time usage counters di cache"""
        today_key = f"usage:{user_id}:{datetime.now().strftime('%Y-%m-%d')}"
        current_usage = await self.cache_service.get(today_key) or 0
        new_usage = current_usage + data_points

        # Cache dengan TTL sampai end of day
        ttl = (datetime.now().replace(hour=23, minute=59, second=59) - datetime.now()).seconds
        await self.cache_service.set(today_key, new_usage, ttl=ttl)

        return new_usage

    async def check_usage_quota(self, user_context: dict) -> dict:
        """Check if user has exceeded their quota"""
        tier_limits = SubscriptionTierConfig.get_tier_limits(user_context['subscription_tier'])
        current_usage = await self.get_current_usage(user_context['user_id'])

        daily_limit = tier_limits.get('daily_api_calls', 1000)
        usage_percentage = (current_usage['daily_calls'] / daily_limit) * 100 if daily_limit != 'unlimited' else 0

        return {
            'within_quota': usage_percentage < 100,
            'usage_percentage': usage_percentage,
            'current_usage': current_usage,
            'daily_limit': daily_limit,
            'upgrade_recommended': usage_percentage > 80,
            'reset_time': self._get_quota_reset_time()
        }

    async def get_current_usage(self, user_id: str) -> dict:
        """Get current usage statistics untuk user"""
        today_key = f"usage:{user_id}:{datetime.now().strftime('%Y-%m-%d')}"
        daily_usage = await self.cache_service.get(today_key) or 0

        # Get monthly usage dari ClickHouse
        monthly_usage = await self.db_service.clickhouse_query(
            "SELECT COUNT(*) as monthly_calls FROM usage_tracking WHERE user_id = ? AND timestamp >= ?",
            [user_id, datetime.now().replace(day=1)]
        )

        return {
            'daily_calls': daily_usage,
            'monthly_calls': monthly_usage[0]['monthly_calls'],
            'last_updated': datetime.utcnow()
        }

    async def generate_billing_data(self, company_id: str, billing_period: str) -> dict:
        """Generate billing data untuk specific company dan period"""
        billing_query = """
        SELECT
            user_id,
            subscription_tier,
            COUNT(*) as total_api_calls,
            SUM(data_points_consumed) as total_data_points,
            AVG(processing_time_ms) as avg_processing_time,
            COUNT(DISTINCT DATE(timestamp)) as active_days
        FROM usage_tracking
        WHERE company_id = ? AND billing_period = ?
        GROUP BY user_id, subscription_tier
        """

        usage_data = await self.db_service.clickhouse_query(billing_query, [company_id, billing_period])

        # Calculate billing amount berdasarkan tier dan usage
        total_bill = 0
        user_bills = []

        for user_data in usage_data:
            user_bill = await self._calculate_user_bill(user_data)
            user_bills.append(user_bill)
            total_bill += user_bill['amount']

        return {
            'company_id': company_id,
            'billing_period': billing_period,
            'total_amount': total_bill,
            'user_breakdown': user_bills,
            'generated_at': datetime.utcnow()
        }
```

---

## 🔄 Multi-User Data Distribution Engine

### **User Session & Distribution Management**
```python
class MultiUserDataDistributor:
    """Business logic untuk isolated multi-user data streams"""

    def __init__(self):
        self.active_sessions = {}  # In-memory session tracking
        self.session_cache = DragonflyDBService()

    async def register_user_session(self, user_context: dict, websocket_connection) -> str:
        """Register new user session untuk data streaming"""
        session_id = f"{user_context['user_id']}_{uuid.uuid4().hex[:8]}"

        session_data = {
            'session_id': session_id,
            'user_id': user_context['user_id'],
            'company_id': user_context['company_id'],
            'subscription_tier': user_context['subscription_tier'],
            'websocket_connection': websocket_connection,
            'connected_at': datetime.utcnow(),
            'last_activity': datetime.utcnow(),
            'data_filter': MultiTenantDataFilter()
        }

        # Store in memory untuk fast access
        self.active_sessions[session_id] = session_data

        # Store in cache untuk recovery
        await self.session_cache.set(f"session:{session_id}", session_data, ttl=3600)

        return session_id

    async def distribute_to_all_users(self, raw_market_data: List[MarketTick]):
        """Main distribution logic: Send filtered data ke all active users"""
        distribution_tasks = []

        for session_id, session_data in self.active_sessions.items():
            # Create task untuk each user's data filtering dan sending
            task = self._send_to_user_session(session_id, session_data, raw_market_data)
            distribution_tasks.append(task)

        # Execute all distributions in parallel
        await asyncio.gather(*distribution_tasks, return_exceptions=True)

    async def _send_to_user_session(self, session_id: str, session_data: dict,
                                  raw_data: List[MarketTick]):
        """Send filtered data ke specific user session"""
        try:
            # 1. Apply tier-based filtering
            filtered_data = await session_data['data_filter'].filter_market_data(
                raw_data,
                {
                    'user_id': session_data['user_id'],
                    'company_id': session_data['company_id'],
                    'subscription_tier': session_data['subscription_tier']
                }
            )

            # 2. Check if user has data to receive
            if not filtered_data.data:
                return  # No data untuk this user's tier

            # 3. Send via WebSocket
            await self._send_websocket_data(
                session_data['websocket_connection'],
                filtered_data
            )

            # 4. Update session activity
            session_data['last_activity'] = datetime.utcnow()

        except Exception as e:
            # Handle user-specific errors (disconnection, etc.)
            await self._handle_user_session_error(session_id, e)

    async def _send_websocket_data(self, websocket, filtered_data: FilteredData):
        """Send data via WebSocket dengan proper error handling"""
        message = {
            'type': 'market_data',
            'data': filtered_data.data,
            'tier_applied': filtered_data.tier_applied,
            'filter_stats': filtered_data.filter_stats,
            'timestamp': datetime.utcnow().isoformat(),
            'billing_info': filtered_data.billing_info
        }

        try:
            await websocket.send_json(message)
        except ConnectionClosed:
            # User disconnected, cleanup session
            await self._cleanup_disconnected_session(websocket)
        except Exception as e:
            # Other WebSocket errors
            logger.error(f"WebSocket send error: {e}")

    async def cleanup_inactive_sessions(self):
        """Cleanup inactive sessions untuk resource management"""
        current_time = datetime.utcnow()
        inactive_sessions = []

        for session_id, session_data in self.active_sessions.items():
            last_activity = session_data['last_activity']
            if (current_time - last_activity).seconds > 300:  # 5 minutes inactive
                inactive_sessions.append(session_id)

        for session_id in inactive_sessions:
            await self._cleanup_session(session_id)

    async def get_active_sessions_stats(self) -> dict:
        """Get statistics about active sessions untuk monitoring"""
        tier_counts = {}
        total_sessions = len(self.active_sessions)

        for session_data in self.active_sessions.values():
            tier = session_data['subscription_tier']
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

        return {
            'total_active_sessions': total_sessions,
            'sessions_per_tier': tier_counts,
            'timestamp': datetime.utcnow()
        }
```

---

## ⚡ Performance SLA Management

### **Tier-Based Performance Monitoring**
```python
class PerformanceSLAManager:
    """Business logic untuk performance SLA enforcement per subscription tier"""

    def __init__(self):
        self.sla_configs = SubscriptionTierConfig.TIER_LIMITS
        self.performance_db = DatabaseService()

    async def monitor_user_performance(self, user_context: dict, processing_time: float):
        """Monitor user's performance against their SLA"""
        tier_sla = self.sla_configs[user_context['subscription_tier']]['sla_uptime']
        expected_latency = self._get_expected_latency(user_context['subscription_tier'])

        performance_record = {
            'user_id': user_context['user_id'],
            'subscription_tier': user_context['subscription_tier'],
            'processing_time_ms': processing_time * 1000,
            'expected_latency_ms': expected_latency,
            'sla_met': (processing_time * 1000) <= expected_latency,
            'timestamp': datetime.utcnow()
        }

        # Store untuk SLA reporting
        await self.performance_db.clickhouse_insert('performance_sla', performance_record)

        # Check for SLA violations
        if not performance_record['sla_met']:
            await self._handle_sla_violation(user_context, processing_time)

    def _get_expected_latency(self, subscription_tier: str) -> float:
        """Get expected latency berdasarkan tier"""
        latency_expectations = {
            'free': 1000,      # 1000ms - best effort
            'pro': 100,        # 100ms - business grade
            'enterprise': 10   # 10ms - premium grade
        }
        return latency_expectations.get(subscription_tier, 1000)

    async def generate_sla_report(self, company_id: str, period_days: int = 30) -> dict:
        """Generate SLA compliance report untuk company"""
        sla_query = """
        SELECT
            subscription_tier,
            COUNT(*) as total_requests,
            SUM(CASE WHEN sla_met THEN 1 ELSE 0 END) as sla_met_requests,
            AVG(processing_time_ms) as avg_latency,
            MAX(processing_time_ms) as max_latency,
            MIN(processing_time_ms) as min_latency
        FROM performance_sla
        WHERE timestamp >= NOW() - INTERVAL ? DAY
        AND user_id IN (SELECT user_id FROM users WHERE company_id = ?)
        GROUP BY subscription_tier
        """

        sla_data = await self.performance_db.clickhouse_query(sla_query, [period_days, company_id])

        report = {
            'company_id': company_id,
            'report_period_days': period_days,
            'generated_at': datetime.utcnow(),
            'tier_performance': {}
        }

        for tier_data in sla_data:
            tier = tier_data['subscription_tier']
            sla_percentage = (tier_data['sla_met_requests'] / tier_data['total_requests']) * 100

            report['tier_performance'][tier] = {
                'sla_compliance_percentage': round(sla_percentage, 2),
                'total_requests': tier_data['total_requests'],
                'average_latency_ms': round(tier_data['avg_latency'], 2),
                'max_latency_ms': tier_data['max_latency'],
                'sla_target': self.sla_configs[tier]['sla_uptime'] * 100,
                'sla_met': sla_percentage >= (self.sla_configs[tier]['sla_uptime'] * 100)
            }

        return report

    async def _handle_sla_violation(self, user_context: dict, actual_latency: float):
        """Handle SLA violation dengan appropriate business action"""
        violation_data = {
            'user_id': user_context['user_id'],
            'subscription_tier': user_context['subscription_tier'],
            'actual_latency': actual_latency,
            'expected_latency': self._get_expected_latency(user_context['subscription_tier']),
            'timestamp': datetime.utcnow()
        }

        # Log violation untuk analysis
        await self.performance_db.postgresql_insert('sla_violations', violation_data)

        # Business actions berdasarkan tier
        if user_context['subscription_tier'] == 'enterprise':
            # Enterprise customers: Immediate alert
            await self._send_enterprise_sla_alert(violation_data)
        elif user_context['subscription_tier'] == 'pro':
            # Pro customers: Track violations, alert if pattern
            await self._track_pro_violations(violation_data)

        # Free tier: Log only, no immediate action
```

---

## 📈 Business Intelligence & Reporting

### **Revenue Analytics & Insights**
```python
class BusinessIntelligenceReporter:
    """Business analytics untuk Data Bridge revenue dan performance insights"""

    async def generate_revenue_analysis(self, period_days: int = 30) -> dict:
        """Generate comprehensive revenue analysis"""

        # Usage by tier analysis
        usage_analysis = await self._analyze_usage_by_tier(period_days)

        # Upgrade opportunity analysis
        upgrade_opportunities = await self._identify_upgrade_opportunities(period_days)

        # Performance cost analysis
        performance_costs = await self._analyze_performance_costs(period_days)

        return {
            'period_days': period_days,
            'usage_analysis': usage_analysis,
            'upgrade_opportunities': upgrade_opportunities,
            'performance_costs': performance_costs,
            'recommendations': await self._generate_business_recommendations(usage_analysis, upgrade_opportunities),
            'generated_at': datetime.utcnow()
        }

    async def _analyze_usage_by_tier(self, period_days: int) -> dict:
        """Analyze usage patterns per subscription tier"""
        query = """
        SELECT
            subscription_tier,
            COUNT(DISTINCT user_id) as active_users,
            SUM(data_points_consumed) as total_data_consumption,
            AVG(data_points_consumed) as avg_data_per_user,
            COUNT(*) as total_api_calls
        FROM usage_tracking
        WHERE timestamp >= NOW() - INTERVAL ? DAY
        GROUP BY subscription_tier
        """

        usage_data = await self.performance_db.clickhouse_query(query, [period_days])

        analysis = {}
        for row in usage_data:
            tier = row['subscription_tier']
            analysis[tier] = {
                'active_users': row['active_users'],
                'total_data_consumption': row['total_data_consumption'],
                'avg_data_per_user': row['avg_data_per_user'],
                'total_api_calls': row['total_api_calls'],
                'revenue_potential': self._calculate_tier_revenue(tier, row['active_users'])
            }

        return analysis

    async def _identify_upgrade_opportunities(self, period_days: int) -> list:
        """Identify users yang likely to upgrade"""
        # Users hitting limits frequently
        heavy_usage_query = """
        SELECT user_id, subscription_tier, COUNT(*) as usage_count
        FROM usage_tracking
        WHERE timestamp >= NOW() - INTERVAL ? DAY
        GROUP BY user_id, subscription_tier
        HAVING usage_count > (
            CASE subscription_tier
                WHEN 'free' THEN 800
                WHEN 'pro' THEN 40000
                ELSE 999999
            END
        )
        """

        heavy_users = await self.performance_db.clickhouse_query(heavy_usage_query, [period_days])

        opportunities = []
        for user in heavy_users:
            opportunity = {
                'user_id': user['user_id'],
                'current_tier': user['subscription_tier'],
                'recommended_tier': self._get_recommended_upgrade(user['subscription_tier']),
                'usage_count': user['usage_count'],
                'potential_revenue_increase': self._calculate_upgrade_revenue(user['subscription_tier'])
            }
            opportunities.append(opportunity)

        return opportunities

    def _calculate_tier_revenue(self, tier: str, user_count: int) -> dict:
        """Calculate revenue potential per tier"""
        tier_pricing = {
            'free': 0,
            'pro': 99,      # $99/month
            'enterprise': 499  # $499/month
        }

        monthly_revenue = tier_pricing.get(tier, 0) * user_count
        return {
            'monthly_revenue': monthly_revenue,
            'annual_revenue': monthly_revenue * 12,
            'user_count': user_count
        }
```

---

## 🔗 Integration Points

### **Database Service Integration**
```python
# Usage data storage
await db_service.clickhouse_insert('usage_tracking', usage_data)

# Real-time caching
await db_service.dragonflydb_set(cache_key, data, ttl=3600)

# User subscription queries
subscription_data = await db_service.postgresql_query('SELECT * FROM subscriptions WHERE user_id = ?', [user_id])
```

### **Central Hub Integration**
```python
# Register business capabilities
await central_hub.register_business_capability({
    'service_name': 'data-bridge',
    'business_features': ['multi_tenant_filtering', 'usage_tracking', 'sla_management'],
    'revenue_impact': 'primary'
})

# Report business metrics
await central_hub.report_business_metrics({
    'active_subscriptions': subscription_stats,
    'revenue_data': monthly_revenue,
    'sla_compliance': sla_stats
})
```

### **Billing Service Integration**
```python
# Send billing events
await billing_service.record_usage_event({
    'user_id': user_id,
    'event_type': 'data_consumption',
    'quantity': data_points,
    'timestamp': datetime.utcnow()
})
```

---

## 🎯 Business Success Metrics

### **Revenue Protection Metrics**
- **Subscription Enforcement Rate**: 99.9% (no free users getting paid features)
- **Usage Tracking Accuracy**: 99.99% (accurate billing data)
- **Quota Compliance**: 100% (no tier limit violations)

### **Customer Experience Metrics**
- **Upgrade Conversion Rate**: Target 15% monthly (free → pro)
- **Customer Retention**: Target 95% (pro/enterprise)
- **SLA Compliance**: 99%+ for paid tiers

### **Operational Efficiency Metrics**
- **Multi-tenant Isolation**: 100% (no cross-tenant data leakage)
- **Performance Per Tier**: Meet all SLA targets
- **Resource Utilization**: Optimal allocation per subscription tier

---

**Key Innovation**: Complete business logic implementation yang transforms technical architecture menjadi revenue-generating multi-tenant SaaS platform dengan enterprise-grade features dan comprehensive analytics.