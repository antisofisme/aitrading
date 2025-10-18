# Skill: finrl-training-service Service

## Purpose
Train Reinforcement Learning agents (PPO, A2C, SAC) using FinRL framework. Learns trading strategy from rewards (no targets needed).

## Key Facts
- **Phase**: ML Training (Phase 2)
- **Status**: ⚠️ To Build
- **Priority**: P1 (Important - alternative to supervised learning)
- **Algorithms**: PPO, A2C, DDPG, SAC, TD3
- **Training data**: ClickHouse.ml_features (historical, NO targets needed)

## Data Flow
```
ClickHouse.ml_features (historical, no targets)
  → finrl-training-service (RL environment, train agent)
  → ClickHouse.agent_checkpoints
  → ClickHouse.training_episodes
  → ClickHouse.reward_history
  → NATS: training.rl.completed.{run_id} (status)
```

## Messaging
- **NATS Publish**: `training.rl.started.{run_id}`, `training.rl.episode.{run_id}.{episode}`, `training.rl.completed.{run_id}`
- **Pattern**: Episodic status events (track training progress)

## Dependencies
- **Upstream**: feature-engineering-service (provides ml_features, NO targets needed)
- **Downstream**: inference-service (loads trained agents)
- **Infrastructure**: ClickHouse, NATS cluster, GPU (recommended)

## Critical Rules
1. **NEVER** require targets (RL learns from rewards, not labels!)
2. **ALWAYS** define reward function clearly (Sharpe, profit, drawdown penalty)
3. **VERIFY** state space = 110 features (matches ml_features)
4. **ENSURE** action space = {buy, sell, hold, position_size}
5. **VALIDATE** agent converges (check reward history trending up)

## RL Components
### State Space
- 110 ML features (from ml_features table)
- Current portfolio state (positions, cash, equity)

### Action Space
- Discrete: {buy, sell, hold, close}
- Continuous: position_size (0.0 to 1.0)

### Reward Function
- Sharpe ratio (risk-adjusted returns)
- Profit/loss
- Drawdown penalty
- Transaction costs

### Algorithms
1. **PPO**: Proximal Policy Optimization (stable, recommended)
2. **A2C**: Advantage Actor-Critic (fast training)
3. **DDPG**: Deep Deterministic Policy Gradient (continuous actions)
4. **SAC**: Soft Actor-Critic (max entropy RL)
5. **TD3**: Twin Delayed DDPG (robust to hyperparameters)

## Validation
When working on this service, ALWAYS verify:
- [ ] ml_features has NO targets (RL doesn't need them)
- [ ] Reward function defined (Sharpe, profit, drawdown)
- [ ] Agent checkpoints saved to ClickHouse
- [ ] Episode rewards logged (trending upward = learning)
- [ ] NATS publishes RL training progress

## Reference Docs
- Planning guide: `PLANNING_SKILL_GUIDE.md` (Service 9, lines 1252-1450)
- Architecture: `SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 498-539)
- Flow + messaging: `SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 421-465)
- Database schema: `table_database_training.md` (to be designed)
