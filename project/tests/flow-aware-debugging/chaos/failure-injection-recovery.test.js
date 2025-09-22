/**
 * Chaos Tests for Failure Injection and Recovery Validation
 * Tests system resilience under various failure scenarios and recovery mechanisms
 */

const ChaosMonkey = require('@mocks/chaos-monkey');
const FlowAwareSystem = require('@mocks/flow-aware-system');
const {
  createChaosScenarios,
  injectFailures,
  monitorRecovery,
  validateSystemResilience
} = require('@utils/chaos-helpers');

describe('Failure Injection and Recovery Chaos Tests', () => {
  let chaosMonkey;
  let flowSystem;
  let chaosConfig;

  beforeAll(async () => {
    chaosConfig = {
      failureTypes: [
        'service_crash',
        'network_partition',
        'resource_exhaustion',
        'database_failure',
        'message_queue_failure',
        'cpu_spike',
        'memory_leak',
        'disk_full',
        'network_latency',
        'cascading_failure'
      ],
      recoveryMechanisms: [
        'circuit_breaker',
        'retry_with_backoff',
        'fallback_service',
        'graceful_degradation',
        'auto_scaling',
        'service_restart',
        'load_balancing',
        'data_replication'
      ],
      resiliendeTarget: {
        maxDowntime: 30000,        // 30 seconds
        recoveryTime: 60000,       // 1 minute
        dataLossThreshold: 0,      // No data loss
        cascadeIsolation: true     // Prevent cascade failures
      }
    };

    chaosMonkey = new ChaosMonkey(chaosConfig);
    flowSystem = new FlowAwareSystem({
      resilience: 'high',
      autoRecovery: true,
      chaosMonitoring: true
    });

    await flowSystem.initialize();
    await chaosMonkey.initialize(flowSystem);
  });

  afterAll(async () => {
    await chaosMonkey.cleanup();
    await flowSystem.shutdown();
  });

  describe('Service Failure Scenarios', () => {
    it('should handle single service crash gracefully', async () => {
      const scenario = await createChaosScenarios.serviceCrash({
        targetService: 'trading-engine',
        crashType: 'sudden_termination',
        duration: 15000, // 15 seconds
        activeFlows: 50
      });

      const chaosExperiment = await chaosMonkey.startExperiment({
        name: 'single_service_crash',
        scenario,
        metrics: ['flow_completion_rate', 'error_propagation', 'recovery_time']
      });

      // Inject failure
      await chaosMonkey.injectFailure('service_crash', {
        serviceId: 'trading-engine',
        method: 'kill_process'
      });

      // Monitor system response
      const systemResponse = await chaosMonkey.monitorSystemResponse({
        duration: 60000, // 1 minute
        checkInterval: 1000
      });

      expect(systemResponse.circuitBreakerActivated).toBe(true);
      expect(systemResponse.timeToDetection).toBeLessThan(5000); // 5 seconds
      expect(systemResponse.failoverActivated).toBe(true);

      // Validate flow handling
      const flowImpact = await chaosMonkey.analyzeFlowImpact();
      expect(flowImpact.activeFlowsPreserved).toBeGreaterThan(45); // 90% preserved
      expect(flowImpact.newFlowsRedirected).toBe(true);

      // Verify automatic recovery
      await chaosMonkey.waitForRecovery({
        targetService: 'trading-engine',
        timeout: 30000
      });

      const recoveryStatus = await chaosMonkey.validateRecovery();
      expect(recoveryStatus.serviceHealthy).toBe(true);
      expect(recoveryStatus.flowsRestored).toBe(true);
      expect(recoveryStatus.dataConsistency).toBe('verified');
    });

    it('should isolate cascading failures effectively', async () => {
      const scenario = await createChaosScenarios.cascadingFailure({
        originService: 'database',
        dependentServices: ['auth-service', 'trading-engine', 'portfolio-service'],
        failureType: 'connection_pool_exhaustion',
        propagationDelay: 2000 // 2 seconds between cascades
      });

      const chaosExperiment = await chaosMonkey.startExperiment({
        name: 'cascading_failure_isolation',
        scenario
      });

      // Inject root failure
      await chaosMonkey.injectFailure('database_failure', {
        failureType: 'connection_pool_exhaustion',
        severity: 'severe'
      });

      // Monitor cascade propagation
      const cascadeMonitoring = await chaosMonkey.monitorCascade({
        maxDepth: 3,
        isolationThreshold: 2 // Stop cascade after 2 levels
      });

      expect(cascadeMonitoring.cascadeDepth).toBeLessThanOrEqual(2);
      expect(cascadeMonitoring.isolationEffective).toBe(true);
      expect(cascadeMonitoring.unaffectedServices).toContain('notification-service');

      // Verify bulkhead pattern effectiveness
      const bulkheadStatus = await chaosMonkey.checkBulkheadIsolation();
      expect(bulkheadStatus.isolatedServices).toContain('market-data-service');
      expect(bulkheadStatus.criticalPathProtected).toBe(true);

      const recoveryPlan = await chaosMonkey.executeRecoveryPlan();
      expect(recoveryPlan.prioritizedRecovery).toBe(true);
      expect(recoveryPlan.rootCauseAddressed).toBe(true);
    });

    it('should handle multiple simultaneous service failures', async () => {
      const scenario = await createChaosScenarios.multipleServiceFailures({
        failingServices: ['market-data', 'risk-engine', 'notification-service'],
        failureTypes: ['network_partition', 'memory_exhaustion', 'cpu_spike'],
        simultaneousFailures: true
      });

      const chaosExperiment = await chaosMonkey.startExperiment({
        name: 'multiple_simultaneous_failures',
        scenario
      });

      // Inject multiple failures simultaneously
      const failurePromises = [
        chaosMonkey.injectFailure('network_partition', { serviceId: 'market-data' }),
        chaosMonkey.injectFailure('memory_exhaustion', { serviceId: 'risk-engine' }),
        chaosMonkey.injectFailure('cpu_spike', { serviceId: 'notification-service' })
      ];

      await Promise.all(failurePromises);

      // Monitor system stability
      const stabilityMetrics = await chaosMonkey.monitorSystemStability({
        duration: 45000, // 45 seconds
        criticalServices: ['trading-engine', 'auth-service']
      });

      expect(stabilityMetrics.criticalServicesStable).toBe(true);
      expect(stabilityMetrics.overallSystemFunctional).toBe(true);
      expect(stabilityMetrics.gracefulDegradationActive).toBe(true);

      // Verify load balancing adjustments
      const loadBalancing = await chaosMonkey.checkLoadBalancing();
      expect(loadBalancing.trafficRerouted).toBe(true);
      expect(loadBalancing.healthyInstancesUtilized).toBe(true);

      // Validate staggered recovery
      const staggeredRecovery = await chaosMonkey.executeStaggeredRecovery();
      expect(staggeredRecovery.recoveryOrder).toEqual(['market-data', 'risk-engine', 'notification-service']);
      expect(staggeredRecovery.systemStableAfterEachStep).toBe(true);
    });
  });

  describe('Infrastructure Failure Scenarios', () => {
    it('should handle network partition scenarios', async () => {
      const scenario = await createChaosScenarios.networkPartition({
        partitionType: 'split_brain',
        affectedRegions: ['us-east', 'eu-west'],
        duration: 30000, // 30 seconds
        networkLatency: 5000 // 5 second delay
      });

      const chaosExperiment = await chaosMonkey.startExperiment({
        name: 'network_partition_handling',
        scenario
      });

      // Create network partition
      await chaosMonkey.injectFailure('network_partition', {
        partitionType: 'split_brain',
        regions: scenario.affectedRegions
      });

      // Monitor partition detection
      const partitionDetection = await chaosMonkey.monitorPartitionDetection();
      expect(partitionDetection.detectionTime).toBeLessThan(10000); // 10 seconds
      expect(partitionDetection.quorumMaintained).toBe(true);

      // Verify distributed consensus handling
      const consensusStatus = await chaosMonkey.checkDistributedConsensus();
      expect(consensusStatus.leaderElected).toBe(true);
      expect(consensusStatus.consistencyMaintained).toBe(true);
      expect(consensusStatus.splitBrainPrevented).toBe(true);

      // Validate data replication behavior
      const replicationStatus = await chaosMonkey.checkDataReplication();
      expect(replicationStatus.replicationPaused).toBe(true);
      expect(replicationStatus.conflictResolutionReady).toBe(true);

      // Test partition healing
      await chaosMonkey.healNetworkPartition();
      const healingMetrics = await chaosMonkey.monitorPartitionHealing();
      expect(healingMetrics.reconnectionTime).toBeLessThan(15000); // 15 seconds
      expect(healingMetrics.dataReconciliation).toBe('successful');
    });

    it('should handle resource exhaustion gracefully', async () => {
      const scenario = await createChaosScenarios.resourceExhaustion({
        resourceType: 'memory',
        targetService: 'trading-engine',
        exhaustionRate: 'gradual', // 10% per second
        memoryPressureThreshold: 90 // 90%
      });

      const chaosExperiment = await chaosMonkey.startExperiment({
        name: 'memory_exhaustion_handling',
        scenario
      });

      // Gradually exhaust memory
      await chaosMonkey.injectFailure('memory_exhaustion', {
        serviceId: 'trading-engine',
        exhaustionPattern: 'gradual',
        targetThreshold: 95 // 95% memory usage
      });

      // Monitor resource management
      const resourceMonitoring = await chaosMonkey.monitorResourceUsage({
        service: 'trading-engine',
        alertThresholds: { memory: 80, cpu: 70 }
      });

      expect(resourceMonitoring.alertsTriggered).toContain('memory_pressure');
      expect(resourceMonitoring.backpressureActivated).toBe(true);

      // Verify garbage collection optimization
      const gcMetrics = await chaosMonkey.analyzeGarbageCollection();
      expect(gcMetrics.emergencyGcTriggered).toBe(true);
      expect(gcMetrics.memoryReclaimed).toBeGreaterThan(0);

      // Validate graceful degradation
      const degradationStatus = await chaosMonkey.checkGracefulDegradation();
      expect(degradationStatus.nonEssentialFeaturesDisabled).toBe(true);
      expect(degradationStatus.coreFlowsPreserved).toBe(true);

      // Test auto-scaling response
      const autoScaling = await chaosMonkey.checkAutoScaling();
      expect(autoScaling.scaleUpTriggered).toBe(true);
      expect(autoScaling.additionalInstancesStarted).toBeGreaterThan(0);
    });

    it('should handle disk space exhaustion', async () => {
      const scenario = await createChaosScenarios.diskSpaceExhaustion({
        targetPath: '/var/logs',
        fillRate: '100MB/second',
        warningThreshold: 85, // 85%
        criticalThreshold: 95 // 95%
      });

      const chaosExperiment = await chaosMonkey.startExperiment({
        name: 'disk_space_exhaustion',
        scenario
      });

      // Fill disk space
      await chaosMonkey.injectFailure('disk_exhaustion', {
        path: '/var/logs',
        fillMethod: 'large_files'
      });

      // Monitor disk space management
      const diskMonitoring = await chaosMonkey.monitorDiskUsage();
      expect(diskMonitoring.warningAlertTriggered).toBe(true);
      expect(diskMonitoring.logRotationActivated).toBe(true);

      // Verify cleanup procedures
      const cleanupStatus = await chaosMonkey.checkDiskCleanup();
      expect(cleanupStatus.oldLogsDeleted).toBe(true);
      expect(cleanupStatus.tempFilesCleared).toBe(true);
      expect(cleanupStatus.spaceReclaimed).toBeGreaterThan(1024 * 1024 * 100); // 100MB

      // Validate emergency storage protocols
      const emergencyStorage = await chaosMonkey.checkEmergencyStorage();
      expect(emergencyStorage.fallbackStorageActivated).toBe(true);
      expect(emergencyStorage.criticalDataPreserved).toBe(true);
    });
  });

  describe('Data Consistency and Recovery', () => {
    it('should maintain data consistency during database failures', async () => {
      const scenario = await createChaosScenarios.databaseConsistencyTest({
        failureType: 'master_node_failure',
        transactionLoad: 'high',
        consistencyModel: 'strong',
        activeTransactions: 100
      });

      const chaosExperiment = await chaosMonkey.startExperiment({
        name: 'database_consistency_validation',
        scenario
      });

      // Start transaction load
      const transactionLoader = await chaosMonkey.startTransactionLoad({
        transactionsPerSecond: 50,
        transactionTypes: ['trade', 'portfolio_update', 'user_action']
      });

      // Inject database failure
      await chaosMonkey.injectFailure('database_master_failure', {
        failureMethod: 'network_isolation'
      });

      // Monitor failover process
      const failoverMetrics = await chaosMonkey.monitorDatabaseFailover();
      expect(failoverMetrics.failoverTime).toBeLessThan(15000); // 15 seconds
      expect(failoverMetrics.dataLossDuringFailover).toBe(0);
      expect(failoverMetrics.transactionsContinued).toBe(true);

      // Verify data consistency
      const consistencyCheck = await chaosMonkey.performConsistencyCheck();
      expect(consistencyCheck.dataIntegrityViolations).toBe(0);
      expect(consistencyCheck.orphanedRecords).toBe(0);
      expect(consistencyCheck.duplicateEntries).toBe(0);

      // Validate transaction atomicity
      const transactionAudit = await chaosMonkey.auditTransactions();
      expect(transactionAudit.partialTransactions).toBe(0);
      expect(transactionAudit.rollbacksSuccessful).toBe(100); // Percentage
    });

    it('should handle message queue failures with guaranteed delivery', async () => {
      const scenario = await createChaosScenarios.messageQueueFailure({
        queueType: 'critical_notifications',
        failureType: 'broker_crash',
        messageVolume: 'high',
        guaranteedDelivery: true
      });

      const chaosExperiment = await chaosMonkey.startExperiment({
        name: 'message_queue_resilience',
        scenario
      });

      // Generate message load
      const messageProducer = await chaosMonkey.startMessageProduction({
        messagesPerSecond: 100,
        messageTypes: ['trade_confirmations', 'risk_alerts', 'system_notifications']
      });

      // Inject queue failure
      await chaosMonkey.injectFailure('message_broker_crash', {
        brokerInstance: 'primary',
        crashType: 'sudden_termination'
      });

      // Monitor message handling
      const messageHandling = await chaosMonkey.monitorMessageDelivery();
      expect(messageHandling.messagesLost).toBe(0);
      expect(messageHandling.failoverActivated).toBe(true);
      expect(messageHandling.backupQueueActive).toBe(true);

      // Verify message persistence
      const persistenceCheck = await chaosMonkey.checkMessagePersistence();
      expect(persistenceCheck.unacknowledgedMessages).toBe(0);
      expect(persistenceCheck.messageOrderPreserved).toBe(true);

      // Validate replay mechanism
      const replayStatus = await chaosMonkey.checkMessageReplay();
      expect(replayStatus.replayCapabilityTested).toBe(true);
      expect(replayStatus.duplicateDetectionWorking).toBe(true);
    });

    it('should recover from distributed transaction failures', async () => {
      const scenario = await createChaosScenarios.distributedTransactionFailure({
        transactionType: 'multi_service_trade',
        involvedServices: ['trading-engine', 'portfolio-service', 'risk-engine', 'audit-service'],
        failureStage: 'commit_phase',
        compensationRequired: true
      });

      const chaosExperiment = await chaosMonkey.startExperiment({
        name: 'distributed_transaction_recovery',
        scenario
      });

      // Start distributed transaction
      const transactionId = await chaosMonkey.initiateDistributedTransaction({
        type: 'complex_trade',
        participants: scenario.involvedServices
      });

      // Inject failure during commit phase
      await chaosMonkey.injectFailure('transaction_coordinator_failure', {
        stage: 'commit_phase',
        transactionId
      });

      // Monitor compensation execution
      const compensationMetrics = await chaosMonkey.monitorCompensation();
      expect(compensationMetrics.compensationTriggered).toBe(true);
      expect(compensationMetrics.rollbackSuccessful).toBe(true);
      expect(compensationMetrics.dataConsistencyRestored).toBe(true);

      // Verify saga pattern execution
      const sagaStatus = await chaosMonkey.checkSagaExecution();
      expect(sagaStatus.compensatingActionsExecuted).toBe(true);
      expect(sagaStatus.systemStateRestored).toBe(true);

      // Validate idempotency handling
      const idempotencyCheck = await chaosMonkey.checkIdempotency();
      expect(idempotencyCheck.duplicateCompensationsPrevented).toBe(true);
      expect(idempotencyCheck.operationsSafeToRetry).toBe(true);
    });
  });

  describe('Performance Under Chaos', () => {
    it('should maintain acceptable performance during partial failures', async () => {
      const scenario = await createChaosScenarios.performanceUnderChaos({
        backgroundFailures: ['intermittent_network_issues', 'periodic_gc_pressure'],
        performanceTarget: {
          maxLatencyIncrease: '50%',
          minThroughputRetention: '80%',
          maxErrorRateIncrease: '5%'
        },
        duration: 180000 // 3 minutes
      });

      const chaosExperiment = await chaosMonkey.startExperiment({
        name: 'performance_under_chaos',
        scenario
      });

      // Establish performance baseline
      const baseline = await chaosMonkey.measurePerformanceBaseline({
        duration: 30000, // 30 seconds
        metrics: ['latency', 'throughput', 'error_rate']
      });

      // Inject background failures
      await chaosMonkey.startBackgroundChaos({
        failures: scenario.backgroundFailures,
        intensity: 'moderate'
      });

      // Measure performance under chaos
      const chaosPerformance = await chaosMonkey.measurePerformanceUnderChaos({
        duration: 120000, // 2 minutes
        comparisonBaseline: baseline
      });

      const latencyIncrease = (chaosPerformance.avgLatency - baseline.avgLatency) / baseline.avgLatency;
      const throughputRetention = chaosPerformance.throughput / baseline.throughput;
      const errorRateIncrease = chaosPerformance.errorRate - baseline.errorRate;

      expect(latencyIncrease).toBeLessThan(0.5); // 50% increase max
      expect(throughputRetention).toBeGreaterThan(0.8); // 80% retention min
      expect(errorRateIncrease).toBeLessThan(0.05); // 5% increase max

      // Verify adaptive performance tuning
      const adaptiveTuning = await chaosMonkey.checkAdaptivePerformanceTuning();
      expect(adaptiveTuning.autoTuningActive).toBe(true);
      expect(adaptiveTuning.performanceOptimizationsApplied).toBeGreaterThan(0);
    });

    it('should handle burst traffic during infrastructure issues', async () => {
      const scenario = await createChaosScenarios.trafficBurstWithInfraIssues({
        trafficMultiplier: 5, // 5x normal traffic
        infrastructureIssues: ['cpu_throttling', 'memory_pressure', 'network_congestion'],
        burstDuration: 60000 // 1 minute
      });

      const chaosExperiment = await chaosMonkey.startExperiment({
        name: 'burst_traffic_with_infra_issues',
        scenario
      });

      // Start infrastructure issues
      await chaosMonkey.injectMultipleFailures([
        { type: 'cpu_throttling', severity: 'moderate' },
        { type: 'memory_pressure', severity: 'moderate' },
        { type: 'network_congestion', severity: 'light' }
      ]);

      // Generate traffic burst
      const trafficBurst = await chaosMonkey.generateTrafficBurst({
        multiplier: scenario.trafficMultiplier,
        duration: scenario.burstDuration,
        requestTypes: ['api_calls', 'websocket_connections', 'database_queries']
      });

      // Monitor system response
      const systemResponse = await chaosMonkey.monitorSystemResponse({
        metrics: ['response_time', 'success_rate', 'resource_utilization'],
        alertThresholds: { responseTime: 2000, successRate: 95 }
      });

      expect(systemResponse.systemStableUnderLoad).toBe(true);
      expect(systemResponse.autoScalingTriggered).toBe(true);
      expect(systemResponse.rateLimitingEffective).toBe(true);

      // Verify load shedding mechanisms
      const loadShedding = await chaosMonkey.checkLoadShedding();
      expect(loadShedding.nonCriticalRequestsDropped).toBe(true);
      expect(loadShedding.criticalRequestsPreserved).toBe(true);
    });
  });

  describe('Security Resilience Under Chaos', () => {
    it('should maintain security controls during system stress', async () => {
      const scenario = await createChaosScenarios.securityUnderStress({
        stressFactors: ['high_cpu_load', 'memory_pressure', 'network_latency'],
        securityControls: ['authentication', 'authorization', 'encryption', 'audit_logging'],
        attackSimulation: true
      });

      const chaosExperiment = await chaosMonkey.startExperiment({
        name: 'security_resilience_under_chaos',
        scenario
      });

      // Apply system stress
      await chaosMonkey.applySystemStress(scenario.stressFactors);

      // Simulate security attacks during stress
      const securityTests = await chaosMonkey.simulateSecurityAttacks({
        attackTypes: ['brute_force', 'token_manipulation', 'privilege_escalation'],
        intensity: 'moderate'
      });

      // Verify security controls effectiveness
      const securityStatus = await chaosMonkey.checkSecurityControls();
      expect(securityStatus.authenticationBypassAttempts).toBe(0);
      expect(securityStatus.unauthorizedAccessPrevented).toBe(true);
      expect(securityStatus.encryptionIntegrityMaintained).toBe(true);
      expect(securityStatus.auditLogsComplete).toBe(true);

      // Validate incident response under stress
      const incidentResponse = await chaosMonkey.checkIncidentResponse();
      expect(incidentResponse.alertsTriggered).toBeGreaterThan(0);
      expect(incidentResponse.responseTimeUnderThreshold).toBe(true);
      expect(incidentResponse.escalationProceduresFollowed).toBe(true);
    });
  });

  describe('Chaos Engineering Best Practices Validation', () => {
    it('should demonstrate blast radius containment', async () => {
      const scenario = await createChaosScenarios.blastRadiusTest({
        primaryFailure: 'critical_service_failure',
        expectedBlastRadius: 2, // Should not affect more than 2 levels
        containmentMechanisms: ['circuit_breakers', 'bulkheads', 'timeouts']
      });

      const chaosExperiment = await chaosMonkey.startExperiment({
        name: 'blast_radius_containment',
        scenario
      });

      // Map service dependencies before failure
      const dependencyMap = await chaosMonkey.mapServiceDependencies();

      // Inject critical service failure
      await chaosMonkey.injectFailure('critical_service_failure', {
        serviceId: 'core-trading-engine',
        isolationTest: true
      });

      // Monitor blast radius expansion
      const blastRadiusMonitoring = await chaosMonkey.monitorBlastRadius({
        originService: 'core-trading-engine',
        maxRadius: scenario.expectedBlastRadius
      });

      expect(blastRadiusMonitoring.actualRadius).toBeLessThanOrEqual(scenario.expectedBlastRadius);
      expect(blastRadiusMonitoring.containmentEffective).toBe(true);
      expect(blastRadiusMonitoring.unaffectedCriticalServices).toHaveLength.greaterThan(0);

      // Verify containment mechanisms
      const containmentStatus = await chaosMonkey.checkContainmentMechanisms();
      expect(containmentStatus.circuitBreakersActivated).toBe(true);
      expect(containmentStatus.bulkheadIsolationWorking).toBe(true);
      expect(containmentStatus.timeoutsPreventingHangingCalls).toBe(true);
    });

    it('should validate observability during chaos events', async () => {
      const scenario = await createChaosScenarios.observabilityValidation({
        chaosEvents: ['service_failures', 'network_issues', 'resource_constraints'],
        observabilityRequirements: {
          metricsAvailable: true,
          logsAccessible: true,
          tracingFunctional: true,
          alertsTriggered: true
        }
      });

      const chaosExperiment = await chaosMonkey.startExperiment({
        name: 'observability_during_chaos',
        scenario
      });

      // Inject multiple chaos events
      await chaosMonkey.injectChaosEvents(scenario.chaosEvents);

      // Validate metrics collection
      const metricsValidation = await chaosMonkey.validateMetricsCollection();
      expect(metricsValidation.metricsStillCollected).toBe(true);
      expect(metricsValidation.metricsAccuracy).toBeGreaterThan(0.95);
      expect(metricsValidation.metricsLatency).toBeLessThan(10000); // 10 seconds

      // Validate logging functionality
      const logsValidation = await chaosMonkey.validateLogging();
      expect(logsValidation.logsStillWritten).toBe(true);
      expect(logsValidation.logSearchFunctional).toBe(true);
      expect(logsValidation.logAggregationWorking).toBe(true);

      // Validate distributed tracing
      const tracingValidation = await chaosMonkey.validateTracing();
      expect(tracingValidation.tracesGenerated).toBe(true);
      expect(tracingValidation.traceCompleteness).toBeGreaterThan(0.9);
      expect(tracingValidation.traceVisualizationAvailable).toBe(true);

      // Validate alerting system
      const alertingValidation = await chaosMonkey.validateAlerting();
      expect(alertingValidation.alertsTriggered).toBeGreaterThan(0);
      expect(alertingValidation.alertAccuracy).toBeGreaterThan(0.95);
      expect(alertingValidation.alertLatency).toBeLessThan(30000); // 30 seconds
    });
  });
});