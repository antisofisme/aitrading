/**
 * ConflictResolution - Advanced conflict resolution system for parallel agents
 * Handles resource conflicts, decision conflicts, and coordination disputes
 */

class ConflictResolution {
  constructor(memoryCoordination, communicationSystem) {
    this.memoryCoordination = memoryCoordination;
    this.communicationSystem = communicationSystem;
    this.conflictQueue = [];
    this.resolutionStrategies = new Map();
    this.arbitrators = new Map();
    this.conflictHistory = [];
    this.activeNegotiations = new Map();
    this.setupResolutionStrategies();
  }

  /**
   * Setup conflict resolution strategies
   */
  setupResolutionStrategies() {
    this.resolutionStrategies.set('negotiation', this.negotiationStrategy.bind(this));
    this.resolutionStrategies.set('arbitration', this.arbitrationStrategy.bind(this));
    this.resolutionStrategies.set('priority', this.priorityStrategy.bind(this));
    this.resolutionStrategies.set('consensus', this.consensusStrategy.bind(this));
    this.resolutionStrategies.set('resource_sharing', this.resourceSharingStrategy.bind(this));
    this.resolutionStrategies.set('temporal_ordering', this.temporalOrderingStrategy.bind(this));
    this.resolutionStrategies.set('capability_matching', this.capabilityMatchingStrategy.bind(this));
  }

  /**
   * Detect and queue conflicts for resolution
   */
  async detectAndQueueConflicts(agentActivities) {
    const conflicts = [];

    // Resource conflicts
    const resourceConflicts = await this.detectResourceConflicts(agentActivities);
    conflicts.push(...resourceConflicts);

    // Decision conflicts
    const decisionConflicts = await this.detectDecisionConflicts(agentActivities);
    conflicts.push(...decisionConflicts);

    // Coordination conflicts
    const coordinationConflicts = await this.detectCoordinationConflicts(agentActivities);
    conflicts.push(...coordinationConflicts);

    // Queue all detected conflicts
    conflicts.forEach(conflict => this.queueConflict(conflict));

    return conflicts;
  }

  /**
   * Detect resource conflicts between agents
   */
  async detectResourceConflicts(agentActivities) {
    const conflicts = [];
    const resourceClaims = new Map();

    // Analyze resource claims from agent activities
    agentActivities.forEach(activity => {
      if (activity.resourceClaims) {
        activity.resourceClaims.forEach(claim => {
          const resourceKey = claim.resource;
          if (!resourceClaims.has(resourceKey)) {
            resourceClaims.set(resourceKey, []);
          }
          resourceClaims.get(resourceKey).push({
            agentId: activity.agentId,
            claim,
            timestamp: activity.timestamp
          });
        });
      }
    });

    // Check for conflicting claims
    resourceClaims.forEach((claims, resource) => {
      if (claims.length > 1) {
        // Check if claims are mutually exclusive
        const exclusiveClaims = claims.filter(claim =>
          claim.claim.exclusive || claim.claim.lockRequired
        );

        if (exclusiveClaims.length > 1) {
          conflicts.push({
            id: `resource_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            type: 'resource_conflict',
            subtype: 'exclusive_access',
            resource,
            agents: exclusiveClaims.map(c => c.agentId),
            claims: exclusiveClaims,
            severity: this.calculateResourceConflictSeverity(exclusiveClaims),
            timestamp: Date.now()
          });
        }
      }
    });

    return conflicts;
  }

  /**
   * Detect decision conflicts between agents
   */
  async detectDecisionConflicts(agentActivities) {
    const conflicts = [];
    const decisions = new Map();

    // Group decisions by subject/context
    agentActivities.forEach(activity => {
      if (activity.decisions) {
        activity.decisions.forEach(decision => {
          const decisionKey = decision.subject || decision.context;
          if (!decisions.has(decisionKey)) {
            decisions.set(decisionKey, []);
          }
          decisions.get(decisionKey).push({
            agentId: activity.agentId,
            decision,
            timestamp: activity.timestamp
          });
        });
      }
    });

    // Check for conflicting decisions
    decisions.forEach((agentDecisions, subject) => {
      if (agentDecisions.length > 1) {
        const uniqueDecisions = new Set(
          agentDecisions.map(d => JSON.stringify(d.decision.value))
        );

        if (uniqueDecisions.size > 1) {
          conflicts.push({
            id: `decision_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            type: 'decision_conflict',
            subject,
            agents: agentDecisions.map(d => d.agentId),
            decisions: agentDecisions,
            severity: this.calculateDecisionConflictSeverity(agentDecisions),
            timestamp: Date.now()
          });
        }
      }
    });

    return conflicts;
  }

  /**
   * Detect coordination conflicts between agents
   */
  async detectCoordinationConflicts(agentActivities) {
    const conflicts = [];
    const coordinationAttempts = [];

    // Analyze coordination attempts
    agentActivities.forEach(activity => {
      if (activity.coordinationAttempts) {
        coordinationAttempts.push(...activity.coordinationAttempts.map(attempt => ({
          ...attempt,
          agentId: activity.agentId,
          timestamp: activity.timestamp
        })));
      }
    });

    // Check for conflicting coordination attempts
    const conflictingAttempts = this.findConflictingCoordination(coordinationAttempts);

    conflictingAttempts.forEach(conflictGroup => {
      conflicts.push({
        id: `coordination_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        type: 'coordination_conflict',
        agents: conflictGroup.map(c => c.agentId),
        attempts: conflictGroup,
        severity: 'medium',
        timestamp: Date.now()
      });
    });

    return conflicts;
  }

  /**
   * Queue conflict for resolution
   */
  queueConflict(conflict) {
    conflict.queuedAt = Date.now();
    conflict.status = 'queued';
    conflict.resolutionAttempts = 0;

    // Priority queue based on severity
    const severityOrder = { 'high': 3, 'medium': 2, 'low': 1 };
    const priority = severityOrder[conflict.severity] || 1;

    conflict.priority = priority;

    // Insert in priority order
    let insertIndex = this.conflictQueue.findIndex(
      queued => queued.priority < priority
    );

    if (insertIndex === -1) {
      this.conflictQueue.push(conflict);
    } else {
      this.conflictQueue.splice(insertIndex, 0, conflict);
    }

    // Store in memory for coordination
    this.memoryCoordination.store(
      'coord/conflicts',
      conflict.id,
      conflict,
      'system'
    );

    return conflict.id;
  }

  /**
   * Process next conflict in queue
   */
  async processNextConflict() {
    if (this.conflictQueue.length === 0) {
      return null;
    }

    const conflict = this.conflictQueue.shift();
    conflict.status = 'processing';
    conflict.processingStarted = Date.now();

    try {
      const resolution = await this.resolveConflict(conflict);
      conflict.resolution = resolution;
      conflict.status = 'resolved';
      conflict.resolvedAt = Date.now();

      // Notify involved agents
      await this.notifyResolution(conflict);

      // Store resolution in history
      this.conflictHistory.push(conflict);

      return resolution;
    } catch (error) {
      conflict.error = error.message;
      conflict.status = 'failed';
      conflict.resolutionAttempts++;

      // Retry if not exceeded max attempts
      if (conflict.resolutionAttempts < 3) {
        conflict.status = 'queued';
        this.conflictQueue.push(conflict); // Re-queue
      }

      throw error;
    }
  }

  /**
   * Resolve conflict using appropriate strategy
   */
  async resolveConflict(conflict) {
    const strategy = this.selectResolutionStrategy(conflict);
    const resolutionFunction = this.resolutionStrategies.get(strategy);

    if (!resolutionFunction) {
      throw new Error(`Unknown resolution strategy: ${strategy}`);
    }

    const resolution = await resolutionFunction(conflict);

    resolution.strategy = strategy;
    resolution.timestamp = Date.now();
    resolution.conflictId = conflict.id;

    return resolution;
  }

  /**
   * Select appropriate resolution strategy for conflict
   */
  selectResolutionStrategy(conflict) {
    switch (conflict.type) {
      case 'resource_conflict':
        return conflict.subtype === 'exclusive_access' ? 'arbitration' : 'resource_sharing';

      case 'decision_conflict':
        return conflict.severity === 'high' ? 'arbitration' : 'consensus';

      case 'coordination_conflict':
        return 'negotiation';

      default:
        return 'priority';
    }
  }

  /**
   * Negotiation strategy for conflict resolution
   */
  async negotiationStrategy(conflict) {
    const negotiationId = `neg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    const negotiation = {
      id: negotiationId,
      conflict: conflict.id,
      participants: conflict.agents,
      rounds: [],
      maxRounds: 5,
      status: 'active',
      started: Date.now()
    };

    this.activeNegotiations.set(negotiationId, negotiation);

    try {
      // Start negotiation rounds
      for (let round = 1; round <= negotiation.maxRounds; round++) {
        const roundResult = await this.conductNegotiationRound(negotiation, round);

        if (roundResult.agreement) {
          negotiation.status = 'success';
          negotiation.agreement = roundResult.agreement;
          break;
        }

        if (round === negotiation.maxRounds) {
          negotiation.status = 'failed';
          throw new Error('Negotiation failed to reach agreement');
        }
      }

      return {
        type: 'negotiated',
        agreement: negotiation.agreement,
        rounds: negotiation.rounds.length,
        participants: negotiation.participants
      };

    } finally {
      this.activeNegotiations.delete(negotiationId);
    }
  }

  /**
   * Conduct a single negotiation round
   */
  async conductNegotiationRound(negotiation, roundNumber) {
    const round = {
      number: roundNumber,
      proposals: [],
      responses: [],
      timestamp: Date.now()
    };

    // Collect proposals from all participants
    const proposalPromises = negotiation.participants.map(agentId =>
      this.requestNegotiationProposal(agentId, negotiation, roundNumber)
    );

    round.proposals = await Promise.all(proposalPromises);

    // Evaluate proposals for agreement
    const agreement = this.evaluateProposalsForAgreement(round.proposals);

    if (agreement) {
      round.agreement = agreement;
      negotiation.rounds.push(round);
      return { agreement };
    }

    // Request responses to proposals
    const responsePromises = negotiation.participants.map(agentId =>
      this.requestProposalResponse(agentId, round.proposals, negotiation)
    );

    round.responses = await Promise.all(responsePromises);
    negotiation.rounds.push(round);

    return { agreement: null };
  }

  /**
   * Request negotiation proposal from agent
   */
  async requestNegotiationProposal(agentId, negotiation, round) {
    const request = {
      type: 'negotiation_proposal_request',
      negotiationId: negotiation.id,
      conflictId: negotiation.conflict,
      round,
      deadline: Date.now() + 30000 // 30 second timeout
    };

    // Send request via communication system
    await this.communicationSystem.sendMessage(
      'system',
      agentId,
      request,
      { type: 'negotiation', priority: 'high' }
    );

    // Wait for response (simplified - in real implementation, use proper async handling)
    return {
      agentId,
      proposal: 'mock_proposal', // This would be the actual agent response
      timestamp: Date.now()
    };
  }

  /**
   * Request response to proposals from agent
   */
  async requestProposalResponse(agentId, proposals, negotiation) {
    const request = {
      type: 'negotiation_response_request',
      negotiationId: negotiation.id,
      proposals,
      deadline: Date.now() + 30000
    };

    await this.communicationSystem.sendMessage(
      'system',
      agentId,
      request,
      { type: 'negotiation', priority: 'high' }
    );

    return {
      agentId,
      response: 'mock_response',
      timestamp: Date.now()
    };
  }

  /**
   * Evaluate proposals for potential agreement
   */
  evaluateProposalsForAgreement(proposals) {
    // Simplified agreement detection
    const proposalValues = proposals.map(p => JSON.stringify(p.proposal));
    const uniqueProposals = [...new Set(proposalValues)];

    if (uniqueProposals.length === 1) {
      return {
        type: 'unanimous',
        proposal: proposals[0].proposal,
        supporters: proposals.map(p => p.agentId)
      };
    }

    // Check for majority agreement
    const proposalCounts = new Map();
    proposalValues.forEach(proposal => {
      proposalCounts.set(proposal, (proposalCounts.get(proposal) || 0) + 1);
    });

    const maxCount = Math.max(...proposalCounts.values());
    if (maxCount > proposals.length / 2) {
      const majorityProposal = [...proposalCounts.entries()]
        .find(([proposal, count]) => count === maxCount)[0];

      return {
        type: 'majority',
        proposal: JSON.parse(majorityProposal),
        supporters: proposals
          .filter(p => JSON.stringify(p.proposal) === majorityProposal)
          .map(p => p.agentId)
      };
    }

    return null; // No agreement
  }

  /**
   * Arbitration strategy for conflict resolution
   */
  async arbitrationStrategy(conflict) {
    const arbitrator = this.selectArbitrator(conflict);

    const arbitration = {
      arbitrator: arbitrator.id,
      conflict: conflict.id,
      evidence: await this.gatherEvidence(conflict),
      decision: null,
      timestamp: Date.now()
    };

    // Arbitrator makes decision based on evidence
    arbitration.decision = await arbitrator.makeDecision(arbitration.evidence, conflict);

    return {
      type: 'arbitrated',
      arbitrator: arbitrator.id,
      decision: arbitration.decision,
      binding: true
    };
  }

  /**
   * Priority strategy for conflict resolution
   */
  async priorityStrategy(conflict) {
    const agentPriorities = await this.getAgentPriorities(conflict.agents);

    const highestPriorityAgent = agentPriorities.reduce((highest, current) =>
      current.priority > highest.priority ? current : highest
    );

    return {
      type: 'priority_based',
      winner: highestPriorityAgent.agentId,
      priority: highestPriorityAgent.priority,
      reason: 'Selected agent with highest priority'
    };
  }

  /**
   * Consensus strategy for conflict resolution
   */
  async consensusStrategy(conflict) {
    const consensusThreshold = 0.67; // 67% agreement required

    // Collect votes from all agents
    const votes = await this.collectConsensusVotes(conflict);

    // Count votes for each option
    const voteCounts = new Map();
    votes.forEach(vote => {
      const option = JSON.stringify(vote.option);
      voteCounts.set(option, (voteCounts.get(option) || 0) + 1);
    });

    // Check for consensus
    const totalVotes = votes.length;
    const consensusOption = [...voteCounts.entries()]
      .find(([option, count]) => count / totalVotes >= consensusThreshold);

    if (consensusOption) {
      return {
        type: 'consensus',
        option: JSON.parse(consensusOption[0]),
        support: consensusOption[1] / totalVotes,
        threshold: consensusThreshold
      };
    } else {
      throw new Error('Failed to reach consensus');
    }
  }

  /**
   * Resource sharing strategy for conflict resolution
   */
  async resourceSharingStrategy(conflict) {
    const sharedResource = conflict.resource;
    const agents = conflict.agents;

    // Calculate fair allocation
    const allocation = this.calculateResourceAllocation(sharedResource, agents);

    return {
      type: 'resource_shared',
      resource: sharedResource,
      allocation,
      agents,
      sharing_rules: this.generateSharingRules(allocation)
    };
  }

  /**
   * Temporal ordering strategy for conflict resolution
   */
  async temporalOrderingStrategy(conflict) {
    const agents = conflict.agents;
    const requests = conflict.claims || conflict.decisions || [];

    // Order by timestamp
    const orderedRequests = requests.sort((a, b) =>
      (a.timestamp || 0) - (b.timestamp || 0)
    );

    return {
      type: 'temporal_ordering',
      order: orderedRequests.map(req => req.agentId),
      schedule: this.generateExecutionSchedule(orderedRequests)
    };
  }

  /**
   * Capability matching strategy for conflict resolution
   */
  async capabilityMatchingStrategy(conflict) {
    const agents = conflict.agents;
    const task = conflict.task || conflict.resource;

    // Get agent capabilities
    const capabilities = await this.getAgentCapabilities(agents);

    // Match capabilities to task requirements
    const bestMatch = this.findBestCapabilityMatch(task, capabilities);

    return {
      type: 'capability_matched',
      selectedAgent: bestMatch.agentId,
      matchScore: bestMatch.score,
      capabilities: bestMatch.capabilities
    };
  }

  /**
   * Calculate resource conflict severity
   */
  calculateResourceConflictSeverity(claims) {
    const priorities = claims.map(c => c.claim.priority || 0);
    const maxPriority = Math.max(...priorities);
    const urgencies = claims.map(c => c.claim.urgent ? 1 : 0);
    const urgentClaims = urgencies.reduce((sum, urgent) => sum + urgent, 0);

    if (maxPriority > 8 || urgentClaims > 1) {
      return 'high';
    } else if (maxPriority > 5 || urgentClaims > 0) {
      return 'medium';
    } else {
      return 'low';
    }
  }

  /**
   * Calculate decision conflict severity
   */
  calculateDecisionConflictSeverity(decisions) {
    const impacts = decisions.map(d => d.decision.impact || 'low');
    const hasHighImpact = impacts.some(impact => impact === 'high');
    const hasCritical = decisions.some(d => d.decision.critical);

    if (hasHighImpact || hasCritical) {
      return 'high';
    } else if (impacts.some(impact => impact === 'medium')) {
      return 'medium';
    } else {
      return 'low';
    }
  }

  /**
   * Notify agents of conflict resolution
   */
  async notifyResolution(conflict) {
    const notification = {
      type: 'conflict_resolved',
      conflictId: conflict.id,
      resolution: conflict.resolution,
      timestamp: Date.now()
    };

    const notificationPromises = conflict.agents.map(agentId =>
      this.communicationSystem.sendMessage(
        'system',
        agentId,
        notification,
        { type: 'resolution', priority: 'high' }
      )
    );

    await Promise.all(notificationPromises);
  }

  /**
   * Get conflict resolution statistics
   */
  getConflictStatistics() {
    const totalConflicts = this.conflictHistory.length;
    const resolvedConflicts = this.conflictHistory.filter(c => c.status === 'resolved').length;

    const strategyCounts = {};
    this.conflictHistory.forEach(conflict => {
      if (conflict.resolution && conflict.resolution.strategy) {
        const strategy = conflict.resolution.strategy;
        strategyCounts[strategy] = (strategyCounts[strategy] || 0) + 1;
      }
    });

    const averageResolutionTime = this.conflictHistory
      .filter(c => c.resolvedAt && c.processingStarted)
      .reduce((sum, c) => sum + (c.resolvedAt - c.processingStarted), 0) / resolvedConflicts || 0;

    return {
      totalConflicts,
      resolvedConflicts,
      resolutionRate: totalConflicts > 0 ? (resolvedConflicts / totalConflicts) * 100 : 0,
      queuedConflicts: this.conflictQueue.length,
      activeNegotiations: this.activeNegotiations.size,
      strategyCounts,
      averageResolutionTime
    };
  }

  /**
   * Helper methods (simplified implementations)
   */

  findConflictingCoordination(attempts) {
    // Simplified conflict detection
    return [];
  }

  selectArbitrator(conflict) {
    return {
      id: 'system_arbitrator',
      makeDecision: async (evidence, conflict) => ({
        decision: 'arbitrator_decision',
        reasoning: 'Based on evidence analysis'
      })
    };
  }

  async gatherEvidence(conflict) {
    return { evidence: 'gathered_evidence' };
  }

  async getAgentPriorities(agents) {
    return agents.map(agentId => ({ agentId, priority: Math.random() }));
  }

  async collectConsensusVotes(conflict) {
    return conflict.agents.map(agentId => ({
      agentId,
      option: 'consensus_option'
    }));
  }

  calculateResourceAllocation(resource, agents) {
    const equalShare = 1 / agents.length;
    return agents.reduce((allocation, agentId) => {
      allocation[agentId] = equalShare;
      return allocation;
    }, {});
  }

  generateSharingRules(allocation) {
    return {
      timeSharing: true,
      maxUsageDuration: 300000, // 5 minutes
      queueingEnabled: true
    };
  }

  generateExecutionSchedule(orderedRequests) {
    return orderedRequests.map((req, index) => ({
      agentId: req.agentId,
      position: index + 1,
      estimatedStart: Date.now() + (index * 60000) // 1 minute intervals
    }));
  }

  async getAgentCapabilities(agents) {
    return agents.map(agentId => ({
      agentId,
      capabilities: ['default_capability']
    }));
  }

  findBestCapabilityMatch(task, capabilities) {
    return {
      agentId: capabilities[0].agentId,
      score: 0.8,
      capabilities: capabilities[0].capabilities
    };
  }

  /**
   * Cleanup conflict resolution system
   */
  cleanup() {
    this.conflictQueue = [];
    this.conflictHistory = [];
    this.activeNegotiations.clear();
  }
}

module.exports = ConflictResolution;