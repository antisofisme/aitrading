# Chain-Aware Debugging Procedures

## Overview

This document outlines comprehensive debugging procedures for the AI Trading System's embedded chain mapping capabilities. Chain-aware debugging enables rapid issue identification, root cause analysis, and impact assessment without requiring additional services.

## Chain Debugging Architecture

### 1. Debug Information Flow

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                             CHAIN-AWARE DEBUGGING                              │
├────────────────────────────────────────────────────────────────────────────────────┤
│  Issue Detection        ──►  Chain Analysis       ──►  Impact Assessment     │
│  │                              │                             │                      │
│  ├─ Service Errors              ├─ Dependency Mapping         ├─ Affected Services      │
│  ├─ Performance Degradation     ├─ Request Flow Tracing       ├─ User Impact            │
│  ├─ Resource Exhaustion         ├─ Error Propagation Path     ├─ Business Impact        │
│  └─ Anomaly Detection           └─ Performance Bottlenecks    └─ Recovery Priority      │
│                                                                                 │
│  Root Cause Analysis    ──►  Recovery Actions     ──►  Preventive Measures    │
│  │                              │                             │                      │
│  ├─ Chain Pattern Recognition   ├─ Service Restart/Scale      ├─ Alert Tuning           │
│  ├─ Historical Correlation      ├─ Traffic Rerouting          ├─ Capacity Planning      │
│  ├─ Code/Config Changes         ├─ Circuit Breaker Activation ├─ Code Improvements      │
│  └─ External Dependency Issues  └─ Rollback Procedures        └─ Architecture Updates   │
└────────────────────────────────────────────────────────────────────────────────────┘
```

## Debugging Procedures

### 1. Real-Time Issue Detection

#### 1.1 Chain Health Monitoring
```python
class ChainHealthMonitor:
    def __init__(self):
        self.alert_thresholds = {
            'chain_duration_p99': 5000,  # 5 seconds
            'error_rate': 0.01,  # 1%
            'dependency_failure_rate': 0.005,  # 0.5%
            'bottleneck_duration_ratio': 0.7  # 70% of total time
        }

    async def monitor_chain_health(self):
        """Continuously monitor chain health metrics"""
        while True:
            try:
                # Get active chains
                active_chains = await self.get_active_chains()

                for chain_id in active_chains:
                    health_metrics = await self.analyze_chain_health(chain_id)

                    # Check for anomalies
                    anomalies = self.detect_anomalies(health_metrics)

                    if anomalies:
                        await self.trigger_chain_investigation(chain_id, anomalies)

            except Exception as e:
                logger.error(f"Chain health monitoring error: {e}")

            await asyncio.sleep(10)  # Monitor every 10 seconds

    async def analyze_chain_health(self, chain_id: str) -> ChainHealthMetrics:
        """Analyze health metrics for a specific chain"""

        # Get chain events from the last hour
        events = await self.get_recent_chain_events(chain_id, hours=1)

        # Calculate performance metrics
        duration_metrics = self.calculate_duration_metrics(events)
        error_metrics = self.calculate_error_metrics(events)
        dependency_metrics = self.calculate_dependency_metrics(events)

        return ChainHealthMetrics(
            chain_id=chain_id,
            total_requests=len(events),
            avg_duration=duration_metrics['avg'],
            p99_duration=duration_metrics['p99'],
            error_rate=error_metrics['rate'],
            dependency_failure_rate=dependency_metrics['failure_rate'],
            bottleneck_services=dependency_metrics['bottlenecks'],
            health_score=self.calculate_overall_health_score(
                duration_metrics, error_metrics, dependency_metrics
            )
        )
```

#### 1.2 Automated Anomaly Detection
```python
class ChainAnomalyDetector:
    def __init__(self):
        self.ml_model = load_anomaly_detection_model()
        self.baseline_calculator = BaselineCalculator()

    def detect_anomalies(self, health_metrics: ChainHealthMetrics) -> List[Anomaly]:
        """Detect anomalies in chain performance"""
        anomalies = []

        # Get baseline metrics
        baseline = self.baseline_calculator.get_baseline(
            health_metrics.chain_id
        )

        # Duration anomalies
        if health_metrics.p99_duration > baseline.p99_duration * 2:
            anomalies.append(Anomaly(
                type='performance_degradation',
                severity='high',
                description=f"P99 duration increased by {
                    (health_metrics.p99_duration / baseline.p99_duration - 1) * 100:.1f
                }%",
                affected_metric='p99_duration',
                current_value=health_metrics.p99_duration,
                baseline_value=baseline.p99_duration
            ))

        # Error rate anomalies
        if health_metrics.error_rate > baseline.error_rate * 3:
            anomalies.append(Anomaly(
                type='error_spike',
                severity='critical',
                description=f"Error rate increased to {health_metrics.error_rate:.3f}",
                affected_metric='error_rate',
                current_value=health_metrics.error_rate,
                baseline_value=baseline.error_rate
            ))

        # Dependency failure anomalies
        if health_metrics.dependency_failure_rate > self.alert_thresholds['dependency_failure_rate']:
            anomalies.append(Anomaly(
                type='dependency_failure',
                severity='high',
                description=f"Dependency failure rate: {health_metrics.dependency_failure_rate:.3f}",
                affected_metric='dependency_failure_rate',
                current_value=health_metrics.dependency_failure_rate,
                baseline_value=baseline.dependency_failure_rate
            ))

        # Use ML model for pattern-based anomaly detection
        ml_anomalies = self.ml_model.detect_anomalies(health_metrics)
        anomalies.extend(ml_anomalies)

        return anomalies
```

### 2. Chain Analysis and Investigation

#### 2.1 Chain Flow Tracing
```python
class ChainFlowTracer:
    def __init__(self):
        self.db = DatabaseConnection()
        self.graph_analyzer = DependencyGraphAnalyzer()

    async def trace_chain_flow(self, chain_id: str) -> ChainFlowTrace:
        """Trace complete flow of a chain through all services"""

        # Get all events for the chain
        events = await self.get_chain_events(chain_id)

        # Build dependency graph
        dependency_graph = self.build_dependency_graph(events)

        # Identify critical path
        critical_path = self.graph_analyzer.find_critical_path(dependency_graph)

        # Analyze timing
        timing_analysis = self.analyze_timing_patterns(events)

        # Identify bottlenecks
        bottlenecks = self.identify_bottlenecks(events, timing_analysis)

        return ChainFlowTrace(
            chain_id=chain_id,
            total_duration=timing_analysis['total_duration'],
            service_count=len(dependency_graph.nodes),
            dependency_graph=dependency_graph,
            critical_path=critical_path,
            bottlenecks=bottlenecks,
            timing_breakdown=timing_analysis['service_breakdown'],
            parallel_executions=timing_analysis['parallel_executions']
        )

    def build_dependency_graph(self, events: List[ChainEvent]) -> nx.DiGraph:
        """Build directed graph of service dependencies"""
        graph = nx.DiGraph()

        # Group events by service
        service_events = {}
        for event in events:
            service = event.service_name
            if service not in service_events:
                service_events[service] = []
            service_events[service].append(event)

        # Add nodes
        for service in service_events.keys():
            graph.add_node(service, events=service_events[service])

        # Add edges based on dependency calls
        for event in events:
            if event.dependencies:
                for dep in event.dependencies:
                    target_service = dep['target_service']
                    if target_service in service_events:
                        graph.add_edge(
                            event.service_name,
                            target_service,
                            duration=dep.get('duration_ms', 0),
                            status=dep.get('status', 'unknown')
                        )

        return graph

    def identify_bottlenecks(self, events: List[ChainEvent],
                           timing_analysis: dict) -> List[Bottleneck]:
        """Identify performance bottlenecks in the chain"""
        bottlenecks = []
        total_duration = timing_analysis['total_duration']

        for service, duration in timing_analysis['service_breakdown'].items():
            # Service takes more than 50% of total time
            if duration > total_duration * 0.5:
                bottlenecks.append(Bottleneck(
                    type='service_duration',
                    service_name=service,
                    duration_ms=duration,
                    percentage_of_total=duration / total_duration * 100,
                    severity='high'
                ))

            # Service has high error rate
            service_events = [e for e in events if e.service_name == service]
            error_count = len([e for e in service_events if e.event_type == 'error'])
            error_rate = error_count / len(service_events) if service_events else 0

            if error_rate > 0.1:  # 10% error rate
                bottlenecks.append(Bottleneck(
                    type='high_error_rate',
                    service_name=service,
                    error_rate=error_rate,
                    error_count=error_count,
                    severity='critical'
                ))

        return bottlenecks
```

#### 2.2 Root Cause Analysis
```python
class ChainRootCauseAnalyzer:
    def __init__(self):
        self.pattern_recognizer = ChainPatternRecognizer()
        self.correlation_analyzer = CorrelationAnalyzer()
        self.external_factor_detector = ExternalFactorDetector()

    async def analyze_root_cause(self, chain_id: str,
                                anomalies: List[Anomaly]) -> RootCauseAnalysis:
        """Perform comprehensive root cause analysis"""

        # Get chain data
        chain_trace = await self.get_chain_trace(chain_id)
        historical_data = await self.get_historical_chain_data(chain_id, days=7)

        # Pattern recognition
        patterns = await self.pattern_recognizer.analyze_patterns(
            chain_trace, historical_data
        )

        # Correlation analysis
        correlations = await self.correlation_analyzer.find_correlations(
            anomalies, historical_data
        )

        # External factor analysis
        external_factors = await self.external_factor_detector.detect_factors(
            chain_trace.start_time, chain_trace.end_time
        )

        # Determine most likely root cause
        root_cause = self.determine_primary_root_cause(
            patterns, correlations, external_factors
        )

        return RootCauseAnalysis(
            chain_id=chain_id,
            primary_root_cause=root_cause,
            contributing_factors=patterns + correlations + external_factors,
            confidence_score=self.calculate_confidence_score(root_cause),
            evidence=self.gather_evidence(root_cause, chain_trace),
            recommended_actions=self.generate_recommended_actions(root_cause)
        )

    def determine_primary_root_cause(self, patterns, correlations,
                                   external_factors) -> RootCause:
        """Determine the most likely root cause"""
        all_factors = patterns + correlations + external_factors

        # Sort by confidence score
        all_factors.sort(key=lambda f: f.confidence_score, reverse=True)

        if not all_factors:
            return RootCause(
                type='unknown',
                description='Unable to determine root cause',
                confidence_score=0.0
            )

        return all_factors[0]
```

### 3. Impact Assessment

#### 3.1 Service Impact Analysis
```python
class ChainImpactAnalyzer:
    def __init__(self):
        self.dependency_mapper = DependencyMapper()
        self.user_impact_calculator = UserImpactCalculator()
        self.business_impact_calculator = BusinessImpactCalculator()

    async def assess_impact(self, chain_id: str,
                           anomalies: List[Anomaly]) -> ImpactAssessment:
        """Assess comprehensive impact of chain issues"""

        # Get affected services
        affected_services = await self.get_affected_services(chain_id, anomalies)

        # Calculate user impact
        user_impact = await self.user_impact_calculator.calculate_impact(
            affected_services
        )

        # Calculate business impact
        business_impact = await self.business_impact_calculator.calculate_impact(
            affected_services, user_impact
        )

        # Determine cascade risk
        cascade_risk = await self.assess_cascade_risk(affected_services)

        return ImpactAssessment(
            chain_id=chain_id,
            affected_services=affected_services,
            user_impact=user_impact,
            business_impact=business_impact,
            cascade_risk=cascade_risk,
            priority_level=self.determine_priority_level(
                user_impact, business_impact, cascade_risk
            ),
            estimated_recovery_time=self.estimate_recovery_time(affected_services)
        )

    async def assess_cascade_risk(self,
                                affected_services: List[str]) -> CascadeRisk:
        """Assess risk of cascading failures"""

        cascade_paths = []
        total_risk_score = 0.0

        for service in affected_services:
            # Get downstream dependencies
            downstream = await self.dependency_mapper.get_downstream_services(service)

            for downstream_service in downstream:
                # Calculate probability of cascade
                cascade_probability = await self.calculate_cascade_probability(
                    service, downstream_service
                )

                if cascade_probability > 0.3:  # 30% threshold
                    cascade_paths.append(CascadePath(
                        source_service=service,
                        target_service=downstream_service,
                        probability=cascade_probability,
                        impact_severity=await self.estimate_cascade_impact(
                            downstream_service
                        )
                    ))

                    total_risk_score += cascade_probability

        return CascadeRisk(
            risk_score=min(total_risk_score, 1.0),
            cascade_paths=cascade_paths,
            mitigation_strategies=self.generate_cascade_mitigation_strategies(
                cascade_paths
            )
        )
```

### 4. Recovery Procedures

#### 4.1 Automated Recovery Actions
```python
class ChainRecoveryOrchestrator:
    def __init__(self):
        self.service_controller = ServiceController()
        self.traffic_manager = TrafficManager()
        self.circuit_breaker = CircuitBreakerManager()

    async def execute_recovery_plan(self,
                                  impact_assessment: ImpactAssessment) -> RecoveryResult:
        """Execute automated recovery procedures"""

        recovery_actions = []

        for service in impact_assessment.affected_services:
            # Determine appropriate recovery action
            action_type = self.determine_recovery_action_type(
                service, impact_assessment
            )

            if action_type == 'restart':
                result = await self.restart_service(service)
                recovery_actions.append(result)

            elif action_type == 'scale':
                result = await self.scale_service(service)
                recovery_actions.append(result)

            elif action_type == 'circuit_break':
                result = await self.activate_circuit_breaker(service)
                recovery_actions.append(result)

            elif action_type == 'traffic_redirect':
                result = await self.redirect_traffic(service)
                recovery_actions.append(result)

        # Wait for services to stabilize
        await asyncio.sleep(30)

        # Verify recovery
        recovery_verification = await self.verify_recovery(
            impact_assessment.chain_id
        )

        return RecoveryResult(
            chain_id=impact_assessment.chain_id,
            actions_taken=recovery_actions,
            recovery_successful=recovery_verification.successful,
            recovery_time=recovery_verification.duration,
            remaining_issues=recovery_verification.remaining_issues
        )

    async def restart_service(self, service_name: str) -> RecoveryAction:
        """Restart a problematic service"""
        try:
            start_time = time.time()

            # Graceful shutdown
            await self.service_controller.graceful_shutdown(service_name)

            # Wait for shutdown
            await asyncio.sleep(10)

            # Restart service
            await self.service_controller.start_service(service_name)

            # Wait for startup
            await self.wait_for_service_health(service_name, timeout=60)

            duration = time.time() - start_time

            return RecoveryAction(
                type='restart',
                service_name=service_name,
                success=True,
                duration=duration,
                details='Service restarted successfully'
            )

        except Exception as e:
            return RecoveryAction(
                type='restart',
                service_name=service_name,
                success=False,
                duration=time.time() - start_time,
                error=str(e)
            )
```

#### 4.2 Manual Recovery Procedures

```markdown
## Manual Recovery Procedures

### Emergency Response Checklist

#### Level 1: Service-Specific Issues
1. **Identify Affected Service**
   - Check chain trace for bottleneck services
   - Review service-specific logs
   - Verify service health endpoints

2. **Quick Fixes**
   - Restart service containers: `docker-compose restart <service-name>`
   - Scale service replicas: `docker-compose up -d --scale <service-name>=3`
   - Clear service cache: `curl -X POST http://localhost:<port>/admin/cache/clear`

3. **Verification**
   - Monitor chain health metrics
   - Test end-to-end chain flow
   - Verify user-facing functionality

#### Level 2: Multi-Service Chain Issues
1. **Chain Analysis**
   - Use chain tracing tools to identify problem area
   - Review dependency graph for circular dependencies
   - Check for resource contention

2. **Systematic Recovery**
   - Restart services in dependency order (leaf nodes first)
   - Implement circuit breakers for failing dependencies
   - Reroute traffic to healthy service instances

3. **Monitoring**
   - Watch for cascade effects
   - Monitor chain completion rates
   - Track error propagation patterns

#### Level 3: System-Wide Issues
1. **Infrastructure Check**
   - Database connectivity and performance
   - Network latency and packet loss
   - Resource utilization (CPU, memory, disk)

2. **External Dependencies**
   - Third-party API status
   - Market data feed health
   - MT5 connection status

3. **Rollback Procedures**
   - Revert to last known good configuration
   - Deploy previous stable version
   - Activate disaster recovery procedures
```

### 5. Debugging Tools and Commands

#### 5.1 Chain Analysis Commands
```bash
# Get chain health overview
curl "http://localhost:8000/api/v1/debug/chains/health"

# Trace specific chain
curl "http://localhost:8000/api/v1/debug/chains/{chain_id}/trace"

# Get chain performance metrics
curl "http://localhost:8000/api/v1/debug/chains/{chain_id}/metrics"

# Find chains with similar patterns
curl "http://localhost:8000/api/v1/debug/chains/similar?pattern=high_latency"

# Get real-time chain events
wscat -c "ws://localhost:8000/ws/debug/chains/events"
```

#### 5.2 Service Debugging Commands
```bash
# Check service dependencies
curl "http://localhost:8000/api/v1/debug/services/{service_name}/dependencies"

# Get service chain participation
curl "http://localhost:8000/api/v1/debug/services/{service_name}/chains"

# Service performance impact analysis
curl "http://localhost:8000/api/v1/debug/services/{service_name}/impact"

# Test service with chain context
curl -H "X-Chain-ID: test-123" \
     -H "X-Debug: true" \
     "http://localhost:{port}/api/v1/health"
```

### 6. Chain-Aware Alerting

#### 6.1 Alert Rules Configuration
```yaml
chain_alerts:
  - name: "Chain Duration P99 High"
    condition: "chain_duration_p99_ms > 5000"
    severity: "warning"
    frequency: "5m"

  - name: "Chain Error Rate High"
    condition: "chain_error_rate > 0.01"
    severity: "critical"
    frequency: "1m"

  - name: "Chain Bottleneck Detected"
    condition: "service_duration_ratio > 0.7"
    severity: "warning"
    frequency: "2m"

  - name: "Chain Cascade Risk High"
    condition: "cascade_risk_score > 0.8"
    severity: "critical"
    frequency: "30s"
```

#### 6.2 Alert Enrichment
```python
class ChainAwareAlerting:
    def __init__(self):
        self.alert_enricher = AlertEnricher()
        self.notification_router = NotificationRouter()

    async def process_chain_alert(self, alert: Alert):
        """Process and enrich chain-related alerts"""

        # Enrich with chain context
        enriched_alert = await self.alert_enricher.enrich_with_chain_context(
            alert
        )

        # Add impact assessment
        impact = await self.assess_alert_impact(enriched_alert)
        enriched_alert.impact_assessment = impact

        # Add recovery recommendations
        recommendations = await self.generate_recovery_recommendations(
            enriched_alert
        )
        enriched_alert.recovery_recommendations = recommendations

        # Route to appropriate channels
        await self.notification_router.route_alert(enriched_alert)

        # Trigger automated recovery if configured
        if enriched_alert.severity == 'critical' and impact.auto_recovery_enabled:
            await self.trigger_automated_recovery(enriched_alert)
```

## Best Practices

### 1. Proactive Monitoring
- Implement baseline performance tracking for all chains
- Set up predictive alerts for performance degradation
- Monitor chain dependency health continuously
- Track chain pattern changes over time

### 2. Efficient Debugging
- Use chain IDs to trace issues across services
- Correlate chain events with system metrics
- Leverage historical chain data for pattern analysis
- Implement automated root cause suggestions

### 3. Recovery Optimization
- Test recovery procedures regularly
- Implement gradual recovery strategies
- Monitor recovery effectiveness
- Update recovery procedures based on lessons learned

### 4. Documentation and Training
- Maintain up-to-date debugging runbooks
- Train team on chain-aware debugging techniques
- Document common failure patterns and solutions
- Share knowledge across team members

This comprehensive chain-aware debugging framework enables rapid issue resolution, minimal service disruption, and continuous improvement of system reliability.