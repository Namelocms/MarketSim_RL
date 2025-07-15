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
    for x in range(10):
        na = NoiseAgent(
            id = ob.get_id('AGENT'), 
            manager = ob.manager,
            cash = 100.00
        )
        # --OR--
        # For when you want to use a random cash amount $10 - $1000
        # Configurable in Agent parent class
            # na = NoiseAgent(
            #     id = ob.get_id('AGENT'), 
            #     manager = ob.manager
            # )
        ob.add_agent(na)
    ```
- Execute Agent Actions
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