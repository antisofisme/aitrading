# Analytics Service

## 🎯 Purpose
**Comprehensive business intelligence and data analytics engine** yang menganalisis trading performance, user behavior, system metrics, dan business KPIs dengan real-time dashboards, automated reporting, dan actionable insights untuk data-driven decision making.

---

## 📊 ChainFlow Diagram

```
All Services → Analytics-Service → Business Intelligence → Stakeholders
     ↓              ↓                    ↓                 ↓
Performance Data  Data Processing     BI Dashboards     Business Insights
User Actions      Metrics Calculation  Report Generation  KPI Monitoring
System Events     Trend Analysis      Alert Systems      Strategic Planning
Trading Results   Pattern Detection   Automated Reports  Performance Optimization
```

---

## 🏗️ Analytics Architecture

### **Input Flow**: Performance data and metrics from all backend services
**Data Sources**: All services (trading results, user activity, system metrics)
**Format**: Protocol Buffers (PerformanceData, UserEvent, SystemMetric, TradingResult)
**Frequency**: 10,000+ data points/second across all analytics categories
**Performance Target**: <5ms real-time analytics queries and dashboard updates

### **Output Flow**: Business intelligence reports and real-time dashboards
**Destinations**: Executive dashboards, User analytics, Admin panels, External APIs
**Format**: JSON (dashboards), PDF/Excel (reports), API responses
**Processing**: Data aggregation + trend analysis + insight generation
**Performance Target**: <5ms real-time queries, <30 seconds report generation

---

## 🚀 Transport Architecture & Contract Integration

### **Transport Decision Matrix Applied**:

#### **Kategori A: High Volume + Mission Critical**
- **Primary Transport**: NATS + Protocol Buffers (<1ms latency)
- **Backup Transport**: Kafka + Protocol Buffers (guaranteed delivery)
- **Failover**: Automatic dengan sequence tracking
- **Services**: Real-time analytics streaming, performance metrics

#### **Kategori B: Medium Volume + Important**
- **Transport**: gRPC (HTTP/2 + Protocol Buffers)
- **Connection**: Pooling + circuit breaker
- **Services**: Business intelligence queries, report generation

#### **Kategori C: Low Volume + Standard**
- **Transport**: HTTP REST + JSON via Kong Gateway
- **Backup**: Redis Queue for reliability
- **Services**: Analytics configuration, dashboard management

### **Global Decisions Applied**:
✅ **Multi-Transport Architecture**: NATS+Kafka for streaming, gRPC for queries, HTTP for config
✅ **Protocol Buffers Communication**: 60% smaller analytics payloads, 10x faster serialization
✅ **Multi-Tenant Architecture**: Company/user-level data isolation and access control
✅ **Request Tracing**: Complete correlation ID tracking through analytics pipeline
✅ **Central-Hub Coordination**: Metrics registry and performance benchmarking
✅ **JWT + Protocol Buffers Auth**: Optimized authentication for analytics endpoints
✅ **Circuit Breaker Pattern**: External data source failover and caching

### **Schema Dependencies**:
```python
# Import from centralized schemas
import sys
sys.path.append('../../../01-core-infrastructure/central-hub/static/generated/python')

from analytics.performance_data_pb2 import PerformanceData, TradingMetrics, UserBehaviorMetrics
from analytics.business_intelligence_pb2 import BusinessInsights, KPIMetrics, TrendAnalysis
from analytics.report_generation_pb2 import ReportRequest, ReportResult, DashboardData
from analytics.user_analytics_pb2 import UserAnalytics, EngagementMetrics, RetentionAnalysis
from common.user_context_pb2 import UserContext, SubscriptionTier
from common.request_trace_pb2 import RequestTrace, TraceContext
from trading.trading_signals_pb2 import TradingSignal, TradingResult
```

### **Enhanced Analytics MessageEnvelope**:
```protobuf
message AnalyticsProcessingEnvelope {
  string message_type = 1;           // "analytics_data"
  string user_id = 2;                // Multi-tenant user identification
  string company_id = 3;             // Multi-tenant company identification
  bytes payload = 4;                 // AnalyticsData protobuf
  int64 timestamp = 5;               // Data timestamp
  string service_source = 6;         // "analytics-service"
  string correlation_id = 7;         // Request tracing
  TraceContext trace_context = 8;    // Distributed tracing
  DataClassification data_class = 9; // Data sensitivity classification
  AuthToken auth_token = 10;         // JWT + Protocol Buffers auth
}
```

---

## 📋 Standard Implementation Pattern

### **BaseService Integration:**
```python
# Analytics Service implementation menggunakan Central Hub standards
from central_hub.static.utils import BaseService, ServiceConfig
from central_hub.static.utils.patterns import (
    StandardResponse, StandardDatabaseManager, StandardCacheManager,
    RequestTracer, StandardCircuitBreaker, PerformanceTracker, ErrorDNA
)

class AnalyticsService(BaseService):
    def __init__(self):
        config = ServiceConfig(
            service_name="analytics-service",
            version="4.0.0",
            port=8003,
            environment="production"
        )
        super().__init__(config)

        # Service-specific initialization
        self.performance_tracker = PerformanceTracker("analytics-service")
        self.error_analyzer = ErrorDNA("analytics-service")

    async def custom_health_checks(self):
        """Analytics-specific health checks"""
        return {
            "analytics_queries_24h": await self.get_daily_query_count(),
            "avg_dashboard_response_ms": await self.get_avg_dashboard_time(),
            "data_processing_success_rate": await self.get_processing_success_rate()
        }

    async def process_analytics_request(self, request_data, correlation_id):
        """Standard analytics processing with patterns"""
        return await self.process_with_tracing(
            "analytics_query",
            self._execute_analytics_query,
            correlation_id,
            request_data
        )
```

### **Standard Error Handling:**
```python
# ErrorDNA integration untuk intelligent error analysis
try:
    analytics_result = await self.process_business_intelligence(data)
except Exception as e:
    # Automatic error analysis dengan suggestions
    error_analysis = self.error_analyzer.analyze_error(
        error_message=str(e),
        stack_trace=traceback.format_exc(),
        correlation_id=correlation_id,
        context={"operation": "business_intelligence", "user_id": user_id}
    )

    # Log dengan ErrorDNA insights
    self.logger.error(f"Analytics processing failed: {error_analysis.suggested_actions}")

    return StandardResponse.error_response(
        error_message=str(e),
        correlation_id=correlation_id,
        service_name=self.service_name
    )
```

### **Standard Performance Monitoring:**
```python
# Automatic performance tracking untuk all analytics operations
with self.performance_tracker.measure("dashboard_generation", user_id=user_id):
    dashboard_data = await self.generate_real_time_dashboard(request)

# Get performance insights
performance_summary = self.performance_tracker.get_performance_summary()
```

### **Standard Database & Cache Access:**
```python
# Consistent database patterns
user_metrics = await self.db.fetch_many(
    "SELECT * FROM user_analytics WHERE user_id = $1 AND date >= $2",
    {"user_id": user_id, "date": start_date}
)

# Standard caching patterns
cached_result = await self.cache.get_or_set(
    f"analytics:dashboard:{user_id}",
    lambda: self.generate_dashboard_data(user_id),
    ttl=300  # 5 minutes
)
```

---

## 📈 Advanced Analytics Engine

### **1. Real-Time Analytics Processor**:
```python
class RealTimeAnalyticsEngine:
    def __init__(self, central_hub_client):
        self.central_hub = central_hub_client
        self.circuit_breaker = CircuitBreaker("external-data")
        self.time_series_db = TimeSeriesDatabase()
        self.cache_manager = AnalyticsCacheManager()

    async def process_analytics_data(self, data: AnalyticsData,
                                   trace_context: TraceContext) -> AnalyticsResult:
        """Real-time analytics processing with multi-tenant isolation"""

        # Request tracing
        with self.tracer.trace("analytics_processing", trace_context.correlation_id):
            start_time = time.time()

            analytics_result = AnalyticsResult()
            analytics_result.data_id = data.data_id
            analytics_result.correlation_id = trace_context.correlation_id

            # Multi-tenant data validation
            access_validation = await self.validate_data_access(data, trace_context)
            if not access_validation.allowed:
                analytics_result.status = AnalyticsStatus.ACCESS_DENIED
                analytics_result.error_message = access_validation.reason
                return analytics_result

            # Data classification and processing
            if data.data_type == DataType.TRADING_PERFORMANCE:
                analytics_result = await self.process_trading_analytics(
                    data, trace_context
                )
            elif data.data_type == DataType.USER_BEHAVIOR:
                analytics_result = await self.process_user_behavior_analytics(
                    data, trace_context
                )
            elif data.data_type == DataType.SYSTEM_METRICS:
                analytics_result = await self.process_system_metrics_analytics(
                    data, trace_context
                )
            elif data.data_type == DataType.BUSINESS_KPI:
                analytics_result = await self.process_business_kpi_analytics(
                    data, trace_context
                )

            # Real-time aggregation updates
            await self.update_real_time_aggregations(analytics_result, trace_context)

            # Performance metrics
            processing_time = (time.time() - start_time) * 1000
            analytics_result.processing_time_ms = processing_time

            return analytics_result

    async def process_trading_analytics(self, data: AnalyticsData,
                                      trace_context: TraceContext) -> AnalyticsResult:
        """Comprehensive trading performance analytics"""

        trading_metrics = TradingMetrics()
        trading_metrics.user_id = data.user_id
        trading_metrics.company_id = data.company_id
        trading_metrics.correlation_id = trace_context.correlation_id

        # Extract trading data
        trading_data = data.trading_performance_data

        # Performance calculations
        trading_metrics.total_trades = len(trading_data.trades)
        winning_trades = [t for t in trading_data.trades if t.pnl > 0]
        losing_trades = [t for t in trading_data.trades if t.pnl <= 0]

        trading_metrics.win_rate = len(winning_trades) / len(trading_data.trades) if trading_data.trades else 0
        trading_metrics.total_pnl = sum(t.pnl for t in trading_data.trades)
        trading_metrics.average_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        trading_metrics.average_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0

        # Risk metrics
        daily_returns = await self.calculate_daily_returns(trading_data.trades)
        trading_metrics.sharpe_ratio = await self.calculate_sharpe_ratio(daily_returns)
        trading_metrics.max_drawdown = await self.calculate_max_drawdown(daily_returns)
        trading_metrics.var_95 = np.percentile(daily_returns, 5) if daily_returns else 0

        # Strategy performance breakdown
        strategy_performance = await self.analyze_strategy_performance(trading_data.trades)
        trading_metrics.strategy_breakdown = strategy_performance

        # Symbol performance analysis
        symbol_performance = await self.analyze_symbol_performance(trading_data.trades)
        trading_metrics.symbol_breakdown = symbol_performance

        # Time-based analysis
        time_performance = await self.analyze_time_based_performance(trading_data.trades)
        trading_metrics.time_analysis = time_performance

        # Store in time series database
        await self.time_series_db.store_trading_metrics(trading_metrics)

        # Update real-time dashboards
        await self.update_trading_dashboards(trading_metrics)

        analytics_result = AnalyticsResult()
        analytics_result.status = AnalyticsStatus.SUCCESS
        analytics_result.trading_metrics = trading_metrics

        return analytics_result

    async def process_user_behavior_analytics(self, data: AnalyticsData,
                                            trace_context: TraceContext) -> AnalyticsResult:
        """User engagement and behavior pattern analysis"""

        user_metrics = UserBehaviorMetrics()
        user_metrics.user_id = data.user_id
        user_metrics.company_id = data.company_id
        user_metrics.correlation_id = trace_context.correlation_id

        # Extract user behavior data
        behavior_data = data.user_behavior_data

        # Engagement metrics
        user_metrics.session_duration_minutes = behavior_data.session_duration / 60000  # ms to minutes
        user_metrics.page_views = len(behavior_data.page_views)
        user_metrics.feature_usage = await self.analyze_feature_usage(behavior_data.feature_interactions)
        user_metrics.click_through_rate = await self.calculate_ctr(behavior_data.interactions)

        # User journey analysis
        user_journey = await self.analyze_user_journey(behavior_data.page_views)
        user_metrics.user_journey = user_journey

        # Conversion analysis
        conversion_metrics = await self.analyze_conversions(behavior_data.actions)
        user_metrics.conversion_metrics = conversion_metrics

        # Retention analysis
        retention_data = await self.calculate_user_retention(data.user_id)
        user_metrics.retention_analysis = retention_data

        # Behavioral segmentation
        user_segment = await self.determine_user_segment(user_metrics)
        user_metrics.user_segment = user_segment

        # Predictive analytics
        if await self.has_advanced_analytics_access(data.user_id):
            churn_probability = await self.predict_churn_probability(user_metrics)
            user_metrics.churn_probability = churn_probability

            lifetime_value = await self.predict_customer_lifetime_value(user_metrics)
            user_metrics.predicted_ltv = lifetime_value

        # Store user analytics
        await self.time_series_db.store_user_metrics(user_metrics)

        analytics_result = AnalyticsResult()
        analytics_result.status = AnalyticsStatus.SUCCESS
        analytics_result.user_metrics = user_metrics

        return analytics_result
```

### **2. Business Intelligence Engine**:
```python
class BusinessIntelligenceEngine:
    async def generate_business_insights(self, insight_request: InsightRequest,
                                       user_context: UserContext,
                                       trace_context: TraceContext) -> BusinessInsights:
        """Generate actionable business insights with AI-powered analysis"""

        # Request tracing
        with self.tracer.trace("business_intelligence", trace_context.correlation_id):
            business_insights = BusinessInsights()
            business_insights.request_id = insight_request.request_id
            business_insights.correlation_id = trace_context.correlation_id

            # Multi-tenant data aggregation
            company_data = await self.aggregate_company_data(
                user_context.company_id, insight_request.time_period
            )

            # KPI Analysis
            kpi_metrics = await self.calculate_kpi_metrics(company_data, insight_request)
            business_insights.kpi_metrics = kpi_metrics

            # Trend Analysis
            trend_analysis = await self.perform_trend_analysis(company_data, insight_request)
            business_insights.trend_analysis = trend_analysis

            # Competitive Analysis (Enterprise only)
            if user_context.subscription_tier >= SubscriptionTier.ENTERPRISE:
                competitive_analysis = await self.perform_competitive_analysis(
                    company_data, insight_request
                )
                business_insights.competitive_analysis = competitive_analysis

            # Predictive Analytics
            predictive_insights = await self.generate_predictive_insights(
                company_data, user_context, trace_context
            )
            business_insights.predictive_insights = predictive_insights

            # Actionable Recommendations
            recommendations = await self.generate_recommendations(
                kpi_metrics, trend_analysis, predictive_insights
            )
            business_insights.recommendations = recommendations

            return business_insights

    async def calculate_kpi_metrics(self, company_data: CompanyData,
                                  insight_request: InsightRequest) -> KPIMetrics:
        """Calculate comprehensive business KPIs"""

        kpi_metrics = KPIMetrics()

        # Revenue KPIs
        kpi_metrics.revenue_metrics = await self.calculate_revenue_kpis(company_data)

        # User Acquisition KPIs
        kpi_metrics.acquisition_metrics = await self.calculate_acquisition_kpis(company_data)

        # User Retention KPIs
        kpi_metrics.retention_metrics = await self.calculate_retention_kpis(company_data)

        # Trading Performance KPIs
        kpi_metrics.trading_metrics = await self.calculate_trading_kpis(company_data)

        # System Performance KPIs
        kpi_metrics.system_metrics = await self.calculate_system_kpis(company_data)

        # Customer Satisfaction KPIs
        kpi_metrics.satisfaction_metrics = await self.calculate_satisfaction_kpis(company_data)

        return kpi_metrics

    async def calculate_revenue_kpis(self, company_data: CompanyData) -> RevenueMetrics:
        """Calculate revenue and financial KPIs"""

        revenue_metrics = RevenueMetrics()

        # Monthly Recurring Revenue (MRR)
        revenue_metrics.mrr = await self.calculate_mrr(company_data.subscription_data)
        revenue_metrics.mrr_growth_rate = await self.calculate_mrr_growth(company_data)

        # Annual Recurring Revenue (ARR)
        revenue_metrics.arr = revenue_metrics.mrr * 12

        # Average Revenue Per User (ARPU)
        active_users = len(company_data.active_users)
        revenue_metrics.arpu = revenue_metrics.mrr / active_users if active_users > 0 else 0

        # Customer Lifetime Value (CLV)
        revenue_metrics.customer_ltv = await self.calculate_customer_ltv(company_data)

        # Revenue by subscription tier
        tier_revenue = await self.calculate_revenue_by_tier(company_data.subscription_data)
        revenue_metrics.tier_breakdown = tier_revenue

        # Churn rate impact on revenue
        churn_rate = await self.calculate_churn_rate(company_data.user_activity)
        revenue_metrics.churn_rate = churn_rate
        revenue_metrics.revenue_at_risk = revenue_metrics.mrr * churn_rate

        return revenue_metrics

    async def perform_trend_analysis(self, company_data: CompanyData,
                                   insight_request: InsightRequest) -> TrendAnalysis:
        """Advanced trend analysis with seasonal decomposition"""

        trend_analysis = TrendAnalysis()

        # User growth trends
        user_growth_trend = await self.analyze_user_growth_trend(company_data)
        trend_analysis.user_growth_trend = user_growth_trend

        # Revenue trends
        revenue_trend = await self.analyze_revenue_trend(company_data)
        trend_analysis.revenue_trend = revenue_trend

        # Trading performance trends
        trading_trend = await self.analyze_trading_performance_trend(company_data)
        trend_analysis.trading_performance_trend = trading_trend

        # Feature adoption trends
        feature_adoption_trend = await self.analyze_feature_adoption_trend(company_data)
        trend_analysis.feature_adoption_trend = feature_adoption_trend

        # Seasonal patterns
        seasonal_patterns = await self.detect_seasonal_patterns(company_data)
        trend_analysis.seasonal_patterns = seasonal_patterns

        # Anomaly detection
        anomalies = await self.detect_anomalies(company_data, insight_request.time_period)
        trend_analysis.anomalies = anomalies

        return trend_analysis
```

### **3. Report Generation Engine**:
```python
class ReportGenerationEngine:
    def __init__(self):
        self.pdf_generator = PDFReportGenerator()
        self.excel_generator = ExcelReportGenerator()
        self.template_manager = ReportTemplateManager()

    async def generate_report(self, report_request: ReportRequest,
                            user_context: UserContext,
                            trace_context: TraceContext) -> ReportResult:
        """Generate comprehensive business reports in multiple formats"""

        # Request tracing
        with self.tracer.trace("report_generation", trace_context.correlation_id):
            report_result = ReportResult()
            report_result.request_id = report_request.request_id
            report_result.correlation_id = trace_context.correlation_id

            # Validate report access permissions
            if not await self.validate_report_access(report_request, user_context):
                report_result.status = ReportStatus.ACCESS_DENIED
                report_result.error_message = "Insufficient permissions for this report"
                return report_result

            # Data collection and aggregation
            report_data = await self.collect_report_data(report_request, user_context)

            # Generate report based on format
            if report_request.format == ReportFormat.PDF:
                report_result = await self.generate_pdf_report(
                    report_request, report_data, user_context
                )
            elif report_request.format == ReportFormat.EXCEL:
                report_result = await self.generate_excel_report(
                    report_request, report_data, user_context
                )
            elif report_request.format == ReportFormat.JSON:
                report_result = await self.generate_json_report(
                    report_request, report_data, user_context
                )

            return report_result

    async def generate_pdf_report(self, report_request: ReportRequest,
                                report_data: ReportData,
                                user_context: UserContext) -> ReportResult:
        """Generate professional PDF reports with charts and tables"""

        report_result = ReportResult()

        # Load report template
        template = await self.template_manager.get_report_template(
            report_request.report_type, ReportFormat.PDF
        )

        # Prepare report context
        report_context = await self.prepare_report_context(
            report_request, report_data, user_context
        )

        # Generate charts and visualizations
        charts = await self.generate_report_charts(report_data, report_request)
        report_context['charts'] = charts

        # Company branding
        branding = await self.get_company_branding(user_context.company_id)
        report_context['branding'] = branding

        # Generate PDF
        pdf_buffer = await self.pdf_generator.generate_pdf(template, report_context)

        # Store report file
        file_path = await self.store_report_file(
            pdf_buffer, report_request, user_context, "pdf"
        )

        report_result.status = ReportStatus.SUCCESS
        report_result.file_path = file_path
        report_result.file_size_bytes = len(pdf_buffer)
        report_result.download_url = await self.generate_download_url(file_path)

        return report_result

    async def generate_excel_report(self, report_request: ReportRequest,
                                  report_data: ReportData,
                                  user_context: UserContext) -> ReportResult:
        """Generate Excel reports with multiple worksheets and data analysis"""

        report_result = ReportResult()

        # Create Excel workbook
        workbook = await self.excel_generator.create_workbook()

        # Add summary worksheet
        summary_sheet = await self.excel_generator.add_summary_worksheet(
            workbook, report_data.summary_data
        )

        # Add detailed data worksheets
        if report_request.include_detailed_data:
            await self.excel_generator.add_detailed_worksheets(
                workbook, report_data.detailed_data
            )

        # Add charts and visualizations
        if report_request.include_charts:
            await self.excel_generator.add_chart_worksheets(
                workbook, report_data.chart_data
            )

        # Add pivot tables (Pro+ feature)
        if (user_context.subscription_tier >= SubscriptionTier.PRO and
            report_request.include_pivot_tables):
            await self.excel_generator.add_pivot_tables(
                workbook, report_data.pivot_data
            )

        # Save Excel file
        excel_buffer = await self.excel_generator.save_workbook(workbook)

        # Store report file
        file_path = await self.store_report_file(
            excel_buffer, report_request, user_context, "xlsx"
        )

        report_result.status = ReportStatus.SUCCESS
        report_result.file_path = file_path
        report_result.file_size_bytes = len(excel_buffer)
        report_result.download_url = await self.generate_download_url(file_path)

        return report_result
```

### **4. Real-Time Dashboard Engine**:
```python
class RealTimeDashboardEngine:
    def __init__(self):
        self.websocket_manager = WebSocketManager()
        self.cache_manager = DashboardCacheManager()

    async def get_dashboard_data(self, dashboard_request: DashboardRequest,
                               user_context: UserContext,
                               trace_context: TraceContext) -> DashboardData:
        """Get real-time dashboard data with caching optimization"""

        # Request tracing
        with self.tracer.trace("dashboard_data", trace_context.correlation_id):
            dashboard_data = DashboardData()
            dashboard_data.dashboard_id = dashboard_request.dashboard_id
            dashboard_data.correlation_id = trace_context.correlation_id

            # Check cache first
            cached_data = await self.cache_manager.get_cached_dashboard_data(
                dashboard_request, user_context
            )

            if cached_data and not dashboard_request.force_refresh:
                dashboard_data = cached_data
                dashboard_data.cache_hit = True
            else:
                # Generate fresh dashboard data
                dashboard_data = await self.generate_dashboard_data(
                    dashboard_request, user_context, trace_context
                )

                # Cache the results
                await self.cache_manager.cache_dashboard_data(
                    dashboard_request, user_context, dashboard_data
                )

            return dashboard_data

    async def generate_dashboard_data(self, dashboard_request: DashboardRequest,
                                    user_context: UserContext,
                                    trace_context: TraceContext) -> DashboardData:
        """Generate fresh dashboard data from all analytics sources"""

        dashboard_data = DashboardData()

        # Executive Dashboard
        if dashboard_request.dashboard_type == DashboardType.EXECUTIVE:
            dashboard_data = await self.generate_executive_dashboard(
                dashboard_request, user_context
            )

        # Trading Dashboard
        elif dashboard_request.dashboard_type == DashboardType.TRADING:
            dashboard_data = await self.generate_trading_dashboard(
                dashboard_request, user_context
            )

        # User Analytics Dashboard
        elif dashboard_request.dashboard_type == DashboardType.USER_ANALYTICS:
            dashboard_data = await self.generate_user_analytics_dashboard(
                dashboard_request, user_context
            )

        # System Performance Dashboard
        elif dashboard_request.dashboard_type == DashboardType.SYSTEM_PERFORMANCE:
            dashboard_data = await self.generate_system_dashboard(
                dashboard_request, user_context
            )

        dashboard_data.generated_at = int(time.time() * 1000)
        dashboard_data.cache_hit = False

        return dashboard_data

    async def stream_dashboard_updates(self, user_context: UserContext,
                                     dashboard_subscriptions: List[str]):
        """Stream real-time dashboard updates via WebSocket"""

        # Establish WebSocket connection
        connection = await self.websocket_manager.create_connection(user_context.user_id)

        try:
            while connection.is_active():
                # Check for data updates
                for dashboard_id in dashboard_subscriptions:
                    updated_data = await self.check_dashboard_updates(
                        dashboard_id, user_context
                    )

                    if updated_data:
                        # Send update via WebSocket
                        await connection.send_update({
                            "type": "dashboard_update",
                            "dashboard_id": dashboard_id,
                            "data": updated_data.SerializeToString().decode('latin1'),
                            "timestamp": int(time.time() * 1000)
                        })

                # Wait before next check
                await asyncio.sleep(5)  # 5-second update interval

        except Exception as e:
            await connection.close()
            raise e
```

---

## 🔍 Performance & Security

### **Service Health Check**:
```python
@app.get("/health")
async def health_check():
    """Comprehensive analytics service health check"""

    health_status = {
        "service": "analytics-service",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "4.0.0"
    }

    try:
        # Analytics performance
        health_status["avg_query_time_ms"] = await self.get_avg_query_time()
        health_status["data_processing_success_rate"] = await self.get_processing_success_rate()

        # Data pipeline health
        health_status["time_series_db_status"] = await self.check_time_series_db()
        health_status["data_warehouse_status"] = await self.check_data_warehouse()
        health_status["cache_cluster_status"] = await self.check_cache_cluster()

        # Business intelligence metrics
        health_status["reports_generated_24h"] = await self.get_daily_report_count()
        health_status["dashboard_queries_24h"] = await self.get_daily_dashboard_queries()
        health_status["avg_report_generation_time"] = await self.get_avg_report_time()

        # Real-time processing
        health_status["real_time_data_lag_ms"] = await self.get_data_lag()
        health_status["active_dashboard_connections"] = await self.get_active_connections()

        # Data quality metrics
        health_status["data_completeness_rate"] = await self.get_data_completeness()
        health_status["data_accuracy_score"] = await self.get_data_accuracy()

        # Cache performance
        health_status["analytics_cache_hit_rate"] = await self.get_cache_hit_rate()
        health_status["dashboard_cache_hit_rate"] = await self.get_dashboard_cache_hit_rate()

    except Exception as e:
        health_status["status"] = "degraded"
        health_status["error"] = str(e)

    return health_status
```

---

## 🎯 Business Value

### **Business Intelligence Excellence**:
- **Sub-5ms Real-Time Queries**: Fast analytics without performance impact
- **Comprehensive KPI Tracking**: 50+ business metrics across all dimensions
- **AI-Powered Insights**: Predictive analytics and trend detection
- **Multi-Format Reporting**: PDF, Excel, JSON with professional templates

### **Data-Driven Decision Making**:
- **Executive Dashboards**: High-level KPIs for strategic planning
- **Subscription-Based Analytics**: Tiered analytics capabilities
- **Competitive Analysis**: Market positioning and benchmarking (Enterprise)
- **Predictive Modeling**: Churn prediction and lifetime value forecasting

### **Operational Excellence**:
- **Real-Time Streaming**: WebSocket-based dashboard updates
- **Multi-Tenant Data Isolation**: Secure company/user data segregation
- **Advanced Caching**: Optimized performance for repeated queries
- **Comprehensive Audit Trail**: Complete data lineage and access logging

---

## 🔗 Service Contract Specifications

### **Analytics Service Proto Contract**:
- **Service Definition**: `/01-core-infrastructure/central-hub/static/proto/services/analytics_service.proto`
- **gRPC Methods**: 40+ RPCs for chart data, technical indicators, AI insights, market analytics
- **Real-time Streaming**: GetChartDataStream(), GetTechnicalIndicatorStream(), GetMarketInsightStream()

### **HTTP REST API Contract**:
- **OpenAPI Specification**: `/01-core-infrastructure/central-hub/static/proto/http/analytics_api.yaml`
- **Configuration Endpoints**: Analytics settings, dashboard management, report scheduling
- **Kong Gateway Integration**: External API access dengan rate limiting dan authentication

---

**Input Flow**: All Services (performance data) → Analytics-Service (processing)
**Output Flow**: Analytics-Service → Dashboards + Reports + Business Intelligence
**Key Innovation**: Sub-5ms real-time business intelligence dengan multi-transport architecture, comprehensive KPI tracking, AI-powered insights, dan multi-format reporting untuk data-driven decision making.