---
name: finrl-training
description: Trains Reinforcement Learning agents (PPO, A2C, SAC) using FinRL framework. Learns trading strategy from rewards without requiring future targets, using 110 ML features as state space.
license: MIT
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
metadata:
  type: Machine Learning (RL Training)
  phase: ML Training (Phase 2)
  status: To Build
  priority: P1 (Important - alternative to supervised)
  port: 8009
  dependencies:
    - central-hub
    - clickhouse
    - nats
  version: 1.0.0
---

# FinRL Training Service

Trains Reinforcement Learning agents (PPO, A2C, DDPG, SAC, TD3) using FinRL framework. Learns optimal trading strategy from rewards without requiring future targets, making it suitable for environments where labeling is difficult.

## When to Use This Skill

Use this skill when:
- Training RL agents for trading strategies
- Implementing reward-based learning (no targets needed)
- Experimenting with different RL algorithms (PPO, SAC, etc.)
- Designing custom reward functions (Sharpe, profit, drawdown)
- Debugging agent convergence issues
- Tuning hyperparameters for RL agents

## Service Overview

**Type:** Machine Learning (Reinforcement Learning Training)
**Port:** 8009
**Input:** ClickHouse (`ml_features` table - historical, NO targets needed)
**Output:** ClickHouse (`agent_checkpoints`, `training_episodes`, `reward_history`)
**Messaging:** NATS (episodic training status)
**Framework:** FinRL (Financial Reinforcement Learning)
**Algorithms:** PPO, A2C, DDPG, SAC, TD3

**Dependencies:**
- **Upstream**: feature-engineering (provides ml_features, NO targets)
- **Downstream**: inference (loads trained agents)
- **Infrastructure**: ClickHouse, NATS cluster, GPU (recommended for faster training)

## Key Capabilities

- RL agent training without future targets
- Multiple algorithms (PPO, A2C, DDPG, SAC, TD3)
- Custom reward function design
- Trading environment simulation
- Episode tracking and reward history
- Agent checkpoint saving
- Hyperparameter tuning
- GPU acceleration support

## Architecture

### Data Flow

```
ClickHouse.ml_features (historical, no targets)
  ↓ (Load features as state)
finrl-training-service
  ├─→ Create trading environment
  ├─→ Initialize RL agent (PPO/SAC/etc.)
  ├─→ Train episodes (state → action → reward)
  ├─→ Update policy
  ├─→ Track episode rewards
  ↓
├─→ ClickHouse.agent_checkpoints (serialized agents)
├─→ ClickHouse.training_episodes (episode metadata)
├─→ ClickHouse.reward_history (learning curve)
└─→ NATS: training.rl.{status}.{run_id} (events)
```

### RL Components

**1. State Space (110 features):**
- All 110 ML features from feature-engineering
- Current portfolio state:
  - Cash balance
  - Position sizes
  - Unrealized PnL
  - Equity value

**2. Action Space:**

**Discrete Actions:**
- Buy (open long)
- Sell (open short)
- Hold (do nothing)
- Close (close position)

**Continuous Actions:**
- Position size (0.0 to 1.0, fraction of capital)

**3. Reward Function:**

```python
reward = (
    profit_reward +           # PnL from trades
    sharpe_reward +           # Risk-adjusted returns
    drawdown_penalty +        # Penalty for large drawdowns
    transaction_cost_penalty  # Spread and commission costs
)
```

**Components:**
- **Profit Reward**: +1 for profit, -1 for loss (scaled by amount)
- **Sharpe Reward**: Risk-adjusted returns (Return / StdDev)
- **Drawdown Penalty**: -10 for exceeding max drawdown threshold
- **Transaction Costs**: -0.01 per trade (spread + commission)

**4. RL Algorithms:**

| Algorithm | Type | Pros | Cons | Use Case |
|-----------|------|------|------|----------|
| **PPO** | On-policy | Stable, good default | Slower than off-policy | General trading |
| **A2C** | On-policy | Fast training | Less stable | Quick experiments |
| **DDPG** | Off-policy | Continuous actions | Hard to tune | Position sizing |
| **SAC** | Off-policy | Max entropy, robust | Complex | Exploration-heavy |
| **TD3** | Off-policy | Robust to hyperparams | Slower convergence | Continuous control |

### Configuration

**Operational Config (Central Hub):**
```json
{
  "operational": {
    "algorithm": "ppo",
    "training_config": {
      "total_timesteps": 1000000,
      "n_episodes": 5000,
      "learning_rate": 0.0003,
      "gamma": 0.99,
      "clip_range": 0.2
    },
    "environment": {
      "initial_capital": 10000,
      "max_position_size": 0.1,
      "transaction_cost": 0.001,
      "state_features": 110
    },
    "reward_function": {
      "profit_weight": 1.0,
      "sharpe_weight": 0.5,
      "drawdown_penalty_weight": 2.0,
      "transaction_cost_weight": 0.1
    },
    "checkpointing": {
      "save_every_episodes": 100,
      "keep_best_only": true,
      "metric": "sharpe_ratio"
    }
  }
}
```

## Examples

### Example 1: Fetch Config from Central Hub

```python
from shared.components.config import ConfigClient

# Initialize client
client = ConfigClient(
    service_name="finrl-training",
    safe_defaults={
        "operational": {
            "algorithm": "ppo",
            "training_config": {"total_timesteps": 1000000}
        }
    }
)
await client.init_async()

# Get config
config = await client.get_config()
algorithm = config['operational']['algorithm']
timesteps = config['operational']['training_config']['total_timesteps']
print(f"Training {algorithm} for {timesteps} timesteps")
```

### Example 2: Create Trading Environment

```python
from finrl_trainer import TradingEnvironment

# Load historical features (no targets needed!)
features_df = await load_features_from_clickhouse(
    symbol="EURUSD",
    timeframe="5m",
    start_date="2023-01-01",
    end_date="2024-12-31"
)

# Create RL environment
env = TradingEnvironment(
    df=features_df,
    initial_capital=10000,
    transaction_cost=0.001,
    state_features=110  # All ML features
)

# Environment will provide:
# - state: 110 features + portfolio state
# - action: buy/sell/hold/close + position_size
# - reward: based on custom reward function
```

### Example 3: Train PPO Agent

```python
from stable_baselines3 import PPO
from finrl_trainer import FinRLTrainer

trainer = FinRLTrainer()

# Initialize PPO agent
agent = PPO(
    policy="MlpPolicy",
    env=env,
    learning_rate=0.0003,
    n_steps=2048,
    batch_size=64,
    gamma=0.99,
    verbose=1
)

# Train agent
trained_agent, reward_history = await trainer.train(
    agent=agent,
    total_timesteps=1000000,
    save_every=100_000
)

# Save checkpoint
await trainer.save_checkpoint(trained_agent, version="ppo-v1.0.0")
```

### Example 4: Monitor Training Progress

```sql
-- Check episode rewards (should trend upward)
SELECT
    episode,
    total_reward,
    sharpe_ratio,
    max_drawdown,
    final_equity
FROM training_episodes
WHERE run_id = 'ppo_eurusd_5m_run1'
ORDER BY episode DESC
LIMIT 50;

-- Plot learning curve
SELECT
    episode,
    AVG(total_reward) OVER (ORDER BY episode ROWS BETWEEN 99 PRECEDING AND CURRENT ROW) as avg_reward_100ep
FROM training_episodes
WHERE run_id = 'ppo_eurusd_5m_run1'
ORDER BY episode;
```

### Example 5: Compare RL Algorithms

```python
from finrl_trainer import AlgorithmComparison

comparator = AlgorithmComparison()

# Train multiple algorithms
results = await comparator.compare_algorithms(
    algorithms=["ppo", "a2c", "sac"],
    env=env,
    timesteps=500000,
    n_runs=3  # Multiple seeds
)

# Results:
# {
#   "ppo": {"avg_reward": 1250, "sharpe": 1.8, "max_dd": -0.12},
#   "a2c": {"avg_reward": 980, "sharpe": 1.5, "max_dd": -0.15},
#   "sac": {"avg_reward": 1320, "sharpe": 1.9, "max_dd": -0.10}
# }
```

## Guidelines

- **ALWAYS** use ConfigClient for operational settings (algorithm, hyperparameters)
- **NEVER** require targets (RL learns from rewards, not labels!)
- **ALWAYS** define reward function clearly (Sharpe, profit, drawdown)
- **VERIFY** state space = 110 features (matches ml_features)
- **ENSURE** action space appropriate (discrete or continuous)
- **VALIDATE** agent converges (check reward history trending up)

## Critical Rules

1. **Config Hierarchy:**
   - Algorithm, hyperparameters → Central Hub (operational config)
   - Safe defaults → ConfigClient fallback
   - No secrets needed

2. **NO Targets Needed (Key Advantage):**
   - **NEVER** require future_return targets
   - **ONLY** use 110 features as state
   - **LEARN** from rewards (profit, Sharpe, drawdown)

3. **Reward Function Design:**
   - **DEFINE** clearly (profit + Sharpe - drawdown - costs)
   - **BALANCE** weights (avoid overfitting to one component)
   - **TEST** different formulations

4. **Agent Convergence:**
   - **MONITOR** episode rewards (should trend upward)
   - **CHECK** policy stability (not oscillating)
   - **VALIDATE** performance on test data

5. **Checkpoint Management:**
   - **SAVE** best agent by metric (Sharpe, profit)
   - **TRACK** version and hyperparameters
   - **TEST** checkpoint loading before deployment

## Common Tasks

### Design Custom Reward Function
1. Identify trading objectives (profit, risk-adjusted, drawdown)
2. Define reward components with weights
3. Test reward function in simulation
4. Tune weights based on agent behavior
5. Validate aligns with trading goals

### Train New RL Agent
1. Load historical features (no targets!)
2. Create trading environment
3. Initialize RL algorithm (PPO recommended)
4. Train for sufficient timesteps (1M+)
5. Monitor convergence (reward trending up)
6. Save best checkpoint

### Debug Poor Agent Performance
1. Check reward function (is it well-defined?)
2. Verify environment setup (state/action spaces)
3. Review hyperparameters (learning rate, gamma)
4. Test simpler algorithm first (A2C baseline)
5. Increase training timesteps

### Tune RL Hyperparameters
1. Start with default values (PPO defaults good)
2. Tune learning rate (0.0001 - 0.001)
3. Adjust gamma (discount factor, 0.95 - 0.99)
4. Test clip_range for PPO (0.1 - 0.3)
5. Use grid search or Optuna

## Troubleshooting

### Issue 1: Agent Not Learning (Flat Reward Curve)
**Symptoms:** Episode rewards not increasing
**Solution:**
- Check reward function (is it too sparse?)
- Increase exploration (higher entropy coefficient)
- Verify environment correct (state/action mapping)
- Test with simpler reward (pure profit first)
- Increase training timesteps

### Issue 2: Agent Overfits to Training Data
**Symptoms:** Good training performance, poor test performance
**Solution:**
- Use walk-forward validation
- Add regularization to reward function
- Reduce model complexity (smaller network)
- Train on more diverse data
- Test on out-of-sample periods

### Issue 3: High Variance in Episode Rewards
**Symptoms:** Rewards oscillate wildly
**Solution:**
- Reduce learning rate (more stable updates)
- Increase batch size (smoother gradients)
- Use PPO instead of A2C (more stable)
- Add reward smoothing
- Check environment stochasticity

### Issue 4: Agent Learns to Always Hold
**Symptoms:** Agent never trades
**Solution:**
- Reduce transaction cost penalty
- Increase profit reward weight
- Add exploration bonus
- Check action space (ensure buy/sell accessible)
- Test reward function manually

### Issue 5: Training Takes Forever
**Symptoms:** Millions of timesteps, still not converged
**Solution:**
- Use GPU acceleration
- Try faster algorithm (A2C, SAC)
- Reduce environment complexity
- Parallelize training (multiple environments)
- Use smaller state space (feature selection)

## Validation Checklist

After making changes to this service:
- [ ] ml_features has NO targets (RL doesn't need them)
- [ ] Reward function defined (Sharpe, profit, drawdown)
- [ ] Agent checkpoints saved to ClickHouse
- [ ] Episode rewards logged (trending upward = learning)
- [ ] NATS publishes RL training progress
- [ ] State space = 110 features + portfolio state
- [ ] Action space appropriate (discrete or continuous)
- [ ] Convergence verified (reward curve analysis)
- [ ] ConfigClient fetching from Central Hub
- [ ] Hot-reload responding to config updates

## Related Skills

- `central-hub` - Provides operational config and service discovery
- `feature-engineering` - Provides 110 ML features (no targets!)
- `inference` - Loads trained RL agents for real-time trading
- `supervised-training` - Alternative supervised learning approach

## References

- Full Documentation: `docs/SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 498-539)
- Planning Guide: `docs/PLANNING_SKILL_GUIDE.md` (Service 9, lines 1252-1450)
- Flow + Messaging: `docs/SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 421-465)
- Database Schema: `docs/table_database_training.md` (to be designed)
- Config Architecture: `docs/CONFIG_ARCHITECTURE.md`
- Central Hub Skill: `.claude/skills/central-hub/SKILL.md`
- FinRL Documentation: https://github.com/AI4Finance-Foundation/FinRL
- Code: `03-machine-learning/finrl-training-service/`

---

**Created:** 2025-10-19
**Version:** 1.0.0
**Status:** To Build
