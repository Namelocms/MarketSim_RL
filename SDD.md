# Simulated Stock Market Environment for Reinforcement Learning Agents

#### Author:
Sean Coleman

#### Last Updated:
2025-06-25

## Table of Contents
- [Overview](#overview)
- [Goals and Objectives](#goals-and-objectives)
- [System Architecture](#system-architecture)
- [Key Components](#key-components)
- [Data Flow and Lifecycle](#data-flow-and-lifecycle)
- [ML Training Strategies](#ml-training-strategies)
- [Technology Stack](#technology-stack)
- [Assumptions and Constraints](#assumptions-and-constraints)
- [Future Extensions](#future-extensions)
- [Appendix](#appendix)

## Overview
This document outlines the design for a modular, agent-based stock market simulation framework with a realistic limit order book. The system is designed primarily to support the development and training of ML and RL agents on order book data in both offline and online settings. The long-term goal is to transition from simulated to real market data for live agent evaluation.

## Goals and Objectives
### Primary Goals
- Build a realistic limit order book-based market simulator.
- Enable online and offline reinforcement learning training of agents.
- Support multiple agent types to model diverse market behaviors.
- Provide scalable tools to collect and visualize order book state, trades, and agent actions.

### Secondary Goals
- Create modular interfaces to swap in real market data.
- Allow performance benchmarking for various ML strategies.
- Build support for parallel simulation environments to speed up training.

## System Architecture
### High-Level Diagram
```sql
 +------------------+         +----------------------+
 |   RL Agent(s)    |<------->|  Simulation Env (Gym)|
 +------------------+         +----------+-----------+
                                        |
                                        v
                        +---------------+---------------+
                        |     Order Book Engine         |
                        +---------------+---------------+
                                        |
         +------------------------------+-----------------------------+
         |               |              |              |              |
         v               v              v              v              v
+---------------+ +-------------+ +-------------+ +-------------+ +-------------+
| Noise Traders | | MM Agents   | | Trend Agents| | MeanRev     | | Custom Bots |
+---------------+ +-------------+ +-------------+ +-------------+ +-------------+
```

## Key Components
### Environment API
#### Standard Gym Interface:
```python
reset()
step(action)
render()
observation_space
action_space
```
#### Observation Space:
- LOB state (depth levels)
- Recent trades
- Agent portfolio info

#### Action Space:
- Discrete or continuous action options:
- Place market order
- Place limit order (at price X, size Y)
- Cancel order
- Hold

### Order Book Engine
#### Data Structures:
- Bid and ask queues (price -> quantity)
- Time-priority matching engine
- Order ID tracking for cancellation

#### Functions:
```python
add_order(agent_id, side, price, size)
cancel_order(order_id)
match_orders()
get_snapshot(depth_n=1...n)
```
### Agent Framework
#### Common Agent Interface
```python 
class Agent:
    def act(self, observation) -> Action
    def update(self, experience)
```
#### Agent Types
- Noise Trader: Randomized behavior
- Market Maker: Quoting around midprice
- Momentum Trader: Trend-following
- Mean-Reversion Trader: Price bouncing logic
- RL Agent: Learns from experience
- Arbitrageur (optional): For cross-asset simulation

### Simulation Manager
- Time control (tick-based or event-based)
- Agent scheduler
- Logging and replay
- Dataset generator for offline learning
- Episode boundaries and termination conditions

## Data Flow and Lifecycle
### Simulation Flow
1. Initialize agents and order book
2. For each time step:
    - Capture LOB snapshot
    - Ask each agent to act
    - Process orders in matching engine
    - Log trade and LOB state
    - Send updated observation to ML agents
    - Apply reward function and store transition

## ML Training Strategies
### Offline Training
- Collect simulation rollouts: (state, action, reward, next_state)
- Store in replay buffer or file
- Train using offline RL algorithms (e.g., TD3+BC, CQL)

### Online Training
- Agent trains step-by-step using rewards from live simulation
- Requires slower, step-synchronized simulation loop
- Supports on-policy algorithms (e.g., PPO, SAC)

## Technology Stack
- Component___________Tool/Library
- Language____________Python 3.10+
- Simulation Env______gymnasium (or gym)
- RL Training_________stable-baselines3, RLlib, d3rlpy
- Data Handling_______pandas, numpy, ta-lib
- Visualization_______matplotlib, plotly, streamlit
- Logging_____________wandb, tensorboard, JSON logs
- Parallelism_________multiprocessing, gym.vector

## Assumptions and Constraints
- Market operates on a simplified tick-based system (not real-time).
- Simulation is single-asset initially (multi-asset optional).
- No regulatory/market microstructure quirks like auction phases or dark pools modeled initially.
- Reward function must be crafted with real-world goals in mind (e.g., profit, risk-adjusted return, inventory control).
- All agents share the same time horizon and tick speed.

## Future Extensions
- Real-time data ingestion via APIs (e.g., Binance, Alpaca)
- Paper trading support
- Multi-agent reinforcement learning
- Multi-asset markets and portfolio strategies
- Latency modeling and slippage
- Integration with existing LOB datasets (e.g., LOBSTER, FI-2010)

## Appendix
### Example Observation Vector
```python
observation = {
    "best_bid": 100.25,
    "best_ask": 100.30,
    "bid_depths": [10, 5, 3, ...],
    "ask_depths": [8, 7, 2, ...],
    "last_price": 100.27,
    "agent_inventory": 120,
    "cash_balance": 9200
}
```
### Example Action Format
```python
action = {
    "type": "LIMIT",
    "side": "BUY",
    "price": 100.26,
    "quantity": 5
}
```