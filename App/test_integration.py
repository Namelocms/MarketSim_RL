from time import time
from OrderBook.OrderBook import OrderBook
from Agent.NoiseAgent import NoiseAgent


def test_integration(num_agents=100, maker_agent_cash=10000, maker_agent_volume=19900000, ob_start_price=1.00):
    
    # Init OrderBook
    ob = OrderBook()
    ob.current_price = ob_start_price
    
    # Maker Agent(s) (this will be its own Agent sub-class eventually)
    MAKER_AGENT = NoiseAgent('MAKER', cash=maker_agent_cash)
    MAKER_AGENT.update_holdings(ob.current_price, maker_agent_volume)
    ob.upsert_agent(MAKER_AGENT)

    # Noise Agents
    for x in range(num_agents):
        agent = NoiseAgent(ob.get_id('AGENT'), cash=1)
        ob.upsert_agent(agent)

    # Run Sim
    i = 1
    iterations = 1
    running = True
    start_time = time()
    run_time = 0
    a_total_times = 0
    total_just_agents = 0
    while running:
        for agent in ob.agents.values():
            a_time = time()
            agent.act(ob)
            a_time_total = time() - a_time
            a_total_times += a_time_total
        
        print(f'Iteration ({i}) Total Agent Action Time: {a_total_times}')
        total_just_agents += a_total_times
        a_total_times = 0
        
        if i < iterations:
            i += 1
        else:
            i = 1
            iterations = 1
            run_time = time() - start_time
            print(f'AGENT TOTALS: {total_just_agents}s')
            print(f'RUN_TIME: {run_time}s')

            choice = int(input('\n1. Continue\n2. Print Snapshot\n3. Print Agents\n4. Add new MAKER holdings\n5. Get MAKER info\n6. Get Current OB price\n7. Exit\n\nChoice: '))
            match (choice):
                case 1:
                    iterations = int(input('Iterations to go forward: '))
                    run_time = 0
                    total_just_agents = 0
                    start_time = time()
                case 2:
                    run_time = 0
                    total_just_agents = 0
                    start_time = time()
                    print(ob.get_snapshot())
                case 3:
                    run_time = 0
                    total_just_agents = 0
                    start_time = time()
                    for agent in ob.agents.values():
                        print(agent.info())
                        print(agent.get_total_shares())
                        print('===================================================')
                case 4:
                    run_time = 0
                    total_just_agents = 0
                    start_time = time()
                    price = float(input(f'Enter price (CURRENT={ob.current_price}): '))
                    volume = int(input('Enter volume: '))
                    NEW_MAKER_AGENT = NoiseAgent('MAKER' + ob.get_id('AGENT'), 10000)
                    NEW_MAKER_AGENT.update_holdings(price, volume)
                    ob.upsert_agent(NEW_MAKER_AGENT)
                case 5:
                    run_time = 0
                    total_just_agents = 0
                    start_time = time()
                    print(ob.agents[MAKER_AGENT.id].cash)
                    print(ob.agents[MAKER_AGENT.id].holdings)
                    print(ob.agents[MAKER_AGENT.id].get_total_shares())
                    print('===================================================')
                case 6:
                    run_time = 0
                    total_just_agents = 0
                    start_time = time()
                    print(ob.current_price)
                case 7:
                    run_time = 0
                    total_just_agents = 0
                    start_time = time()
                    running = False
                case _:
                    run_time = 0
                    total_just_agents = 0
                    start_time = time()

