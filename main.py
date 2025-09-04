import json
import copy
import random

from ML.ActorCritic.LobEnv import LOBEnv
from OrderBook.OrderBook import OrderBook
from Agent.NoiseAgent import NoiseAgent
from Order.OrderAction import OrderAction

#from ML.GeneticAlgorithm.Env import Env, Individual
from ML.ContinuousGeneticAlgorithm.Env import Env, Individual


ob = OrderBook()
ob.current_price = 0.75

# =======================Continuous Evolutionary Algorithm=======================
def trainCGA():
    env = Env(
        _start_cash= 100,
        _pop_size= 100,
        _mutation_rate= 0.10,
        _crossover_rate= 0.75,
        _ob= ob,
        _num_noise_agents= 250,
        _version= 'v4'
    )
    env.train()

trainCGA()

# =======================Evolutionary Algorithm=======================
# Indexes for certain market situations (bull = rising price, bear = falling price)
slow_bear = 7
slow_bull = 0
fast_bull = 1
valley = 8

def train_GA():
    DATA_INDEX = 8 # Change this to use a specific saved simulation (currently 0-24)
    GENERATIONS = 2500# 250 steps per sim
    VERSION = 0
    TARGET_VERSION = 1

    env = Env(
        _start_cash= 100,
        _generations= GENERATIONS,
        _pop_size= 1000,
        _mutation_rate= 0.1,
        _crossover_rate= 0.75,
        _ob= ob,
        _num_noise_agents= 250,
        _data_index= DATA_INDEX,
        _version= f'v{VERSION}', # Save model as this version
    )
    while VERSION < TARGET_VERSION:
        env.train(
            save_increment= env.generations // 10,
            enable_save= True,
        )
        print(f'DONE WITH VERSION {VERSION}')
        print('\n'*5)
        VERSION += 1
        env.reset(version=f'v{VERSION}')

def eval_GA():
    GENERATIONS = 25000 # 4x amount of available sim steps
    env = Env(
        _start_cash= 100,
        _generations= GENERATIONS,
        _pop_size= 100,
        _mutation_rate= 0.1,
        _crossover_rate= 0.7,
        _ob= ob,
        _num_noise_agents= 1000,
        _data_index= None,
        _version= ''
    )
    env.ob.current_price = random.uniform(0.10, 10.00)
    env.eval('hof_2500/hof_v0.json')

def make_data_GA():
    # Make market data for training
    data_to_json = []
    num_sims = 25
    num_iterations = 250
    min_agents = 10
    max_agents = 300
    min_cash = 10.00
    max_cash = 1000.00
    min_holdings = 0
    max_holdings = 100 # Higher = More likely to drop in price due to supply and demand (greater supply)
    min_ob_price = 0.10
    max_ob_price = 15.00

    ## TODO: need env

    for i in range(num_sims):
        avg_agent_vol = 0.0
        avg_agent_cash = 0.0
        list_cash = []
        list_vol = []
        print('Making agents...')
        env.ob.agents.clear()
        env.num_noise_agents = random.randint(min_agents, max_agents)
        print(f'Num Agents: {env.num_noise_agents} || OB Price: {env.ob.current_price}')
        for _ in range(env.num_noise_agents):
            cash = random.randint(min_cash, max_cash)
            avg_agent_cash += cash
            list_cash.append(cash)
            agent = NoiseAgent(env.ob.get_id('AGENT'), cash)
            vol = random.randint(min_holdings, max_holdings)
            if vol > 0:
                agent.update_holdings(agent._get_beta_price(env.ob.current_price, random.choice([OrderAction.BID, OrderAction.ASK])), vol)
                avg_agent_vol += vol
            list_vol.append(vol)
            env.ob.upsert_agent(agent)
        
        avg_agent_vol /= env.num_noise_agents
        avg_agent_cash /= env.num_noise_agents
        print(f'Avg Agent Vol: {avg_agent_vol} || Avg Agent Cash: {avg_agent_cash}')
        print(f'VOLS: {list_vol}')
        print(f'\nCASH: {list_cash}')

        print('Generating new market data...')
        env.generate_market_info(num_iterations)
        print(env.market_info[str(num_iterations - 1)])

        print('Copying data...')
        data_to_json.append(copy.deepcopy(env.market_info))

        print('Resetting ENV...')
        env.market_info.clear()
        env.ob.reset(random.uniform(min_ob_price, max_ob_price)) # reset with random initial price
        if i < num_sims - 1: print('Restarting...')
        print('='*50)
        print('\n')

    print('Saving market data...')
    with open('market_data.json', 'w') as f:
        json.dump(data_to_json, f, indent=4)
        f.close()
    print('Done.')


#train_GA()
#eval_GA()

# =======================Actor-Critic RL=======================
#ACTOR_BASE_PATH = 'RL/models/actors/'
#ACTOR_ID = 'actor_100x100_v1'
#ACTOR_PATH = ACTOR_BASE_PATH + ACTOR_ID + '/'
#CRITIC_BASE_PATH = 'RL/models/critics/'
#CRITIC_ID = 'critic_100x100_v1'
#CRITIC_PATH = CRITIC_BASE_PATH + CRITIC_ID + '/'
#
## Train an agent
#env = LOBEnv(
#    _ob=ob,
#    _num_steps=1440,
#    _num_agents=300,
#    _agent_start_cash=100,
#    _ob_depth=10
#)
#env.train(
#    actor_id=               ACTOR_ID,
#    critic_id=              CRITIC_ID,
#    learning_rate_actor=    0.01,
#    learning_rate_critic=   0.01,
#    gamma=                  0.90, # Closer to 1, prioritizes future rewards (overfit potential), closer to 0 prioritizes immediate rewards (underfit potential)
#    episodes=               10, 
#    enable_save_actor=      True,
#    enable_save_critic=     True,
#    actor_to_load=          None,
#    critic_to_load=         None,
#    episode_save_interval=  2,
#)

# Evaluate a trained agent
#actor = env._load_actor(ACTOR_ID + '_8', path=ACTOR_PATH, eval_mode=True)
#env.eval(actor)