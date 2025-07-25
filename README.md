# Simulated Stock Market for ML/RL Agent Training
DESCRIPTION
## Installation

## Usage
- Initialize the OrderBook (1 per session)
    ```python
    ob = OrderBook()
    ```
- Make Agents and Add to OrderBook
    ```python
    # Maker agent(s) maintain market liquidity (this will be its own Agent sub-class eventually)
    MAKER_AGENT = NoiseAgent(id='MAKER', cash=10000)
    MAKER_AGENT.update_holdings(price=ob.current_price, volume=100000000)
    MAKER_AGENT.max_price_deviation = 0.001  # 0.001 * 100 = 0.1% max deviation +-
    ob.upsert_agent(MAKER_AGENT)

    # Add normal agents to the orderbook
    NUM_AGENTS_IN_SIM = 100
    for x in range(NUM_AGENTS_IN_SIM):
        na = NoiseAgent(
            id = ob.get_id('AGENT')
            cash = 100.00
        )
        # --OR--
        # For when you want to use a random cash amount $10 - $1000
        # Configurable in Agent parent class
            # na = NoiseAgent(
            #     id = ob.get_id('AGENT')r
            # )
        ob.upsert_agent(na)
    ```
- Execute Agent Actions and Match to other available orders
    ```python
    for agent in ob.agents.values():
        agent.act(ob)
    ```
- Check Current OrderBook Info
    ```python
    ob.get_snapshot() # base depth = 10
    # --OR--
    #ob.get_snapshot(depth=DESIRED_DEPTH)
    ```