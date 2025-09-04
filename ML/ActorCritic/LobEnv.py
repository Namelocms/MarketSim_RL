from Agent.TakerAgent import TakerAgent
from Agent.NoiseAgent import NoiseAgent
from OrderBook.OrderBook import OrderBook
from OrderBook.Matchmaker import MatchMaker
from Order.Order import Order
from Order.OrderAction import OrderAction
from Order.OrderStatus import OrderStatus
from Order.OrderType import OrderType
from ML.ActorCritic.Networks import Actor, Critic

from random import random, randint, choice
import torch
import torch.optim as optim
import math
import numpy as np
import os


class LOBEnv:
    def __init__(self, _ob: OrderBook, _num_steps = 100, _num_agents = 250, _agent_start_cash = 100, _ob_depth = 10):
        self.ob = _ob
        self.mm = MatchMaker()
        self.ob_start_price = _ob.current_price
        self.num_steps = _num_steps
        self.current_step = 0
        self.num_agents = _num_agents
        self.agent_start_cash = _agent_start_cash
        self.ob_depth = _ob_depth
        self.actor_agent = TakerAgent('--ACTOR--', cash=_agent_start_cash)
        self.cash_prev = _agent_start_cash
        self.holdings_prev = 0
        self.price_prev = 0
        self.portfolio_value_prev = self.agent_start_cash
        self.transaction_cost = 0.001 # 0.1%
        self.risk_penalty = 0.0 # Higher means more penalty with more volatility in return amounts
        self.pl_history = []

        for _ in range(self.num_agents):
            agent = NoiseAgent(self.ob.get_id('AGENT'), cash=self.agent_start_cash)
            agent.update_holdings(agent._get_beta_price(self.ob.current_price, choice([OrderAction.ASK, OrderAction.BID])), randint(1, 1000))
            self.ob.upsert_agent(agent)
        self.ob.upsert_agent(self.actor_agent)

    def reset(self):
        self.ob.reset(self.ob_start_price)
        for agent in self.ob.agents.values():
            agent.reset(self.agent_start_cash)
            if agent.id != self.actor_agent.id:
                agent.update_holdings(self.ob.current_price, randint(1, 1000))
        self._mature_market()
        self.current_step = 0
        self.cash_prev = self.actor_agent.cash
        self.holdings_prev = 0
        self.price_prev = self.ob.current_price
        self.portfolio_value_prev = self.agent_start_cash
        self.pl_history.clear()

        return self._get_state(Order('PLACEHOLDER', self.actor_agent.id, -1, -1, OrderAction.HOLD, OrderType.MARKET))

    def step(self, action, prev_action):
        print(action)
        invalid_action = False
        self.current_step += 1
        reward = 0.0
        max_purchasable = int(self.actor_agent.cash / self.ob.current_price)

        self.cash_prev = self.actor_agent.cash
        self.holdings_prev = self.actor_agent.get_total_shares()
        self.price_prev = self.ob.current_price
        self.portfolio_value_prev = self.cash_prev + (self.holdings_prev * self.price_prev)

        order: Order = Order('PLACEHOLDER', self.actor_agent.id, -1, -1, OrderAction.HOLD, OrderType.MARKET)
        match action:
            case 0: # BID
                if max_purchasable > 0:
                    order = self.actor_agent.make_market_bid(self.ob, max_purchasable)
                    self.mm.match_market_bid(self.ob, order)
                    order = self.actor_agent.history[order.id] # Update order values
                    reward -= (self._get_transaction_cost(order) / self.portfolio_value_prev)
                else: 
                    invalid_action = True
                    #if prev_action == action: reward -= 1.0
            case 1: # ASK
                if self.actor_agent.get_total_shares() > 0:
                    print('ASK IF')
                    order = self.actor_agent.make_market_ask(self.ob, self.actor_agent.get_total_shares())
                    self.mm.match_market_ask(self.ob, order)
                    order = self.actor_agent.history[order.id] # Update order values
                    self.pl_history.append(self.actor_agent.cash + (self.actor_agent.get_total_shares() * self.ob.current_price) - self.agent_start_cash)
                    reward = self._get_reward(reward, order)
                    print(order.info())
                else: 
                    invalid_action = True
                    print('ASK ELSE')
                    #if prev_action == action: reward -= 1.0
            case 2: # HOLD
                reward = -0.01
                # Holding instead of realizing profit
                if self.actor_agent.get_total_shares() > 0 and self.actor_agent.get_highest_value_share()[0] < self.ob.current_price:
                    reward -= 0.25
                # Holding instead of realizing loss
                elif self.actor_agent.get_total_shares() > 0 and self.actor_agent.get_highest_value_share()[0] > self.ob.current_price:
                    reward += 0.5
                # 
                else:
                    reward -= 0.25
            case _: 
                print('BADDDDDDD')

        done = self.current_step >= self.num_steps
        
        #if done:
        #    if self.actor_agent.cash < self.agent_start_cash:
        #        reward -= abs(self.actor_agent.cash / self.agent_start_cash)
        #    elif self.actor_agent.cash > self.agent_start_cash:
        #        reward += (self.actor_agent.cash / self.agent_start_cash)
        #reward = self._get_reward(reward, order)
        #prev_action = action
        if invalid_action: reward = -1.0 # Penalize heavily for invalid actions
        reward = max(min(reward, 1.0), -1.0) # clamp to range (-1.0, 1.0)

        self._mature_market(steps=1) # Move the market forward

        return self._get_state(order), reward, done
        
    def train(self, actor_id, critic_id, learning_rate_actor, learning_rate_critic, gamma, episodes, enable_save_actor = False, enable_save_critic = False, actor_to_load: str = None, critic_to_load: str = None, episode_save_interval = 10):
        actor = Actor() if actor_to_load is None else self._load_actor(actor_to_load, path=f'RL/models/actors/{actor_to_load}/')
        critic = Critic() if critic_to_load is None else self._load_critic(critic_to_load, path=f'RL/models/critics/{critic_to_load}/')

        actor_optimizer = optim.Adam(actor.parameters(), lr=learning_rate_actor)
        critic_optimizer = optim.Adam(critic.parameters(), lr=learning_rate_critic)

        for episode in range(episodes):
            state = self.reset()
            done = False
            total_reward = 0 # Perfect score = num steps
            total_actor_loss = 0
            total_critic_loss = 0
            prev_action = 2

            while not done:
                # Actor chooses action
                action_probs = actor(state)
                dist = torch.distributions.Categorical(action_probs)
                action = dist.sample()

                # Env responds
                next_state, reward, done = self.step(action.item(), prev_action)

                # Critic computes TD error
                value = critic(state)
                next_value = critic(next_state)
                td_target = reward + gamma * next_value * (1-int(done))
                td_error = td_target - value

                # Critic update
                critic_loss = td_error.pow(2).mean()
                critic_optimizer.zero_grad()
                critic_loss.backward()
                critic_optimizer.step()

                # Actor update
                actor_loss = -dist.log_prob(action) * td_error.detach()
                actor_optimizer.zero_grad()
                actor_loss.backward()
                actor_optimizer.step()
                total_actor_loss += actor_loss

                # Move to next state
                prev_action = action
                state = next_state
                total_reward += reward

            learning_rate_actor -= 0.01
            print('='*50)
            print(f'ACTOR: Total episode loss = {total_actor_loss}')
            print(f'ACTOR: Last Action Probs: {action_probs}')
            print(f'ACTOR: Last State: {state}')
            print(f'CRITIC: Total episode loss = {total_critic_loss}')
            if episode % episode_save_interval == 0: 
                h_list = self.actor_agent.holdings
                h_val = 0
                for p, v in h_list.items(): h_val += (self.ob.current_price * v)
                print(f'Episode: {episode}, Total Reward: {total_reward:.2f}, Cash Change: {self.actor_agent.cash - self.agent_start_cash}, Total Cash: {self.actor_agent.cash}, Total Holdings: {self.actor_agent.get_total_shares()}, ENV Price: {self.ob.current_price}, Holdings: {self.actor_agent.holdings}, Holdings Value: {h_val}, Total P/L: {round((self.actor_agent.cash + h_val) - self.agent_start_cash, 2)}')
                # Save every 'episode_save_interval' number of episodes
                if enable_save_actor: self._save_actor(f'{actor_id}_{episode}', actor, path=f'RL/models/actors/{actor_id}/')
                if enable_save_critic: self._save_critic(f'{critic_id}_{episode}', critic, path=f'RL/models/critics/{critic_id}/')
        # Final save
        if enable_save_actor: self._save_actor(f'{actor_id}', actor, path=f'RL/models/actors/{actor_id}/')
        if enable_save_critic: self._save_critic(f'{critic_id}', critic, path=f'RL/models/critics/{critic_id}/')

    def eval(self, actor):
        self.reset()
        i = 1
        iterations = 1
        running = True
        _temp_order = Order('PLACEHOLDER', self.actor_agent.id, -1, -1, OrderAction.HOLD, OrderType.MARKET)
        order = _temp_order
        self._mature_market()
        # Add Random action control agent to judge effectiveness
        control_agent = NoiseAgent('--CONTROL--', self.agent_start_cash)
        self.ob.upsert_agent(control_agent)
        state = self._get_state(order)

        # Run sim
        while running:
            for agent in self.ob.agents.values():
                if agent.id != self.actor_agent.id:
                    agent.act(self.ob)
                else:
                    max_purchasable = int(self.actor_agent.cash / self.ob.current_price)
                    with torch.no_grad():
                        action_probs = actor(state)
                    dist = torch.distributions.Categorical(action_probs)
                    action = dist.sample().item()
                    #action = torch.argmax(action_probs, dim=-1) # get the action with the best probability @ current state
                    #action = randint(0, 2)
                    match action:
                        case 0:
                            order = self.actor_agent.make_market_bid(self.ob, max_purchasable)
                            self.mm.match_market_bid(self.ob, order)
                            order = self.actor_agent.history[order.id]
                        case 1:
                            order = self.actor_agent.make_market_ask(self.ob, self.actor_agent.get_total_shares())
                            self.mm.match_market_ask(self.ob, order) 
                            order = self.actor_agent.history[order.id]
                        case 2:
                            order = _temp_order
                            pass
            state = self._get_state(order)
            
            print(f'Iteration ({i}) Current Price: {self.ob.current_price} | Action: {action} | Holdings: {self.actor_agent.holdings}')
            
            if i < iterations:
                i += 1
            
            # Get user input for next action
            else:
                i = 1
                iterations = 1
                print("Action probs:", np.array(action_probs))
                print("Eval state:", self._get_state(order))
                print(f'Actor Cash: {self.ob.agents[self.actor_agent.id].cash}')
                print(f'Actor Holdings: {self.ob.agents[self.actor_agent.id].holdings}')
                print(f'Actor Total Shares: {self.ob.agents[self.actor_agent.id].get_total_shares()}')
                print('===================================================')
                choice = int(input('\n1. Continue\n2. Print Snapshot\n3. Get Control Agent info\n4. Reset ENV\n5. Get Actor info\n6. Set Current OB price\n7. Exit\n\nChoice: '))
                match (choice):
                    case 1:
                        iterations = int(input('Iterations to go forward: '))
                    case 2:
                        print(self.ob.current_price)
                        print(self.ob.get_snapshot())
                    case 3:
                        print(self.ob.agents[control_agent.id].cash)
                        print(self.ob.agents[control_agent.id].holdings)
                        print(self.ob.agents[control_agent.id].get_total_shares())
                        print('===================================================')
                    case 4:
                        self.reset()
                    case 5:
                        print(self.ob.agents[self.actor_agent.id].cash)
                        print(self.ob.agents[self.actor_agent.id].holdings)
                        print(self.ob.agents[self.actor_agent.id].get_total_shares())
                        print('===================================================')
                    case 6:
                        self.ob.current_price = float(input('Enter price: '))
                    case 7:
                        running = False
                    case _:
                        pass
    
    def _get_state(self, order: Order):
        features = []
        shares_traded = 0
        trade_cost = 0.00

        portfolio_value_prev = self.cash_prev + (self.holdings_prev * self.price_prev)
        portfolio_value_curr = self.actor_agent.cash + (self.actor_agent.get_total_shares() * self.ob.current_price)
        portfolio_perc_change = (portfolio_value_curr - portfolio_value_prev) / (portfolio_value_prev)

        if order.id != 'PLACEHOLDER':
            shares_traded = order.entry_volume - order.volume
            trade_cost = shares_traded * order.price * self.transaction_cost
        trade_cost_perc = (trade_cost / portfolio_value_prev)
        
        volatility = 0.0
        if len(self.pl_history) > 1:
            volatility = np.std(self.pl_history)

        snapshot = self.ob.get_snapshot(depth=self.ob_depth)
        asks = snapshot[0]['asks']
        bids = snapshot[0]['bids']

        best_ask = self.ob_start_price * 100
        best_bid = self.ob_start_price / 100
        worst_ask = self.ob_start_price * 200 # Worst in regards to the available ob depth
        worst_bid = self.ob_start_price / 200 # Worst in regards to the available ob depth
        if len(asks) > 0: best_ask = asks[0]['price']; worst_ask = asks[-1]['price']
        if len(bids) > 0: best_bid = bids[0]['price']; worst_bid = bids[-1]['price']

        # set price really high so it doesn't try to sell with no holdings
        highest_share = self.ob_start_price * 1000 if len(self.actor_agent.holdings) <= 0 else self.actor_agent.get_highest_value_share()[0]
        avg_holding_price = self.ob_start_price * 1000 if len(self.actor_agent.holdings) <= 0 else 0 
        lowest_share = self.ob_start_price * 1000 if len(self.actor_agent.holdings) <= 0 else self.actor_agent.get_lowest_value_share()[0]
        
        i = 0
        for price in self.actor_agent.holdings.keys():
            avg_holding_price += price
            i += 1
        avg_holding_price /= i if i > 0 else 1

        # 16 features
        features.extend([
            portfolio_value_prev, 
            portfolio_value_curr, 
            portfolio_perc_change, 
            trade_cost, 
            trade_cost_perc, 
            volatility, 
            best_ask, 
            worst_ask,
            best_bid,
            worst_bid,
            self.ob.current_price,
            self.actor_agent.get_total_shares(),
            round(self.actor_agent.cash, 2),
            highest_share,
            avg_holding_price,
            lowest_share,
        ])

        return torch.FloatTensor(features)

    def _mature_market(self, steps = 100):
        for _ in range(steps):
            for agent in self.ob.agents.values():
                if agent.id != self.actor_agent.id:
                    agent.act(self.ob)

    def _get_transaction_cost(self, order: Order):
        shares_traded = order.entry_volume - order.volume
        return (shares_traded * order.price) * self.transaction_cost

    def _get_reward(self, reward, order: Order):
        ''' Computes reward as percent change in portfolio value, adjusted for transaction costs and risk penalty '''
        #reward = 0.0
        epsilon = 0.01 

        # Portfolio value
        portfolio_value_prev = self.cash_prev + (self.holdings_prev * self.price_prev)
        portfolio_value_curr = self.actor_agent.cash + (self.actor_agent.get_total_shares() * self.ob.current_price)

        # Agent is broke
        if portfolio_value_prev <= epsilon or portfolio_value_curr <= epsilon:
            return -1.0 
        
        perc_change = (portfolio_value_curr - portfolio_value_prev) / (portfolio_value_prev)
        reward += perc_change
        #if perc_change == 0: reward -= 0.01

        # Transaction cost penalty as percent of previous portfolio value
        if order.id != 'PLACEHOLDER':
            trade_cost = self._get_transaction_cost(order)
            reward -= (trade_cost / portfolio_value_prev)

        if len(self.pl_history) > 1:
            volatility = np.std(self.pl_history)
            reward -= (self.risk_penalty * volatility)

        return reward

    def _save_critic(self, critic_id: str, critic: Critic, path = 'RL/models/critics/'):
        if os.path.isdir(path):
            torch.save(critic.state_dict(), path + f'{critic_id}.pth')
        else:
            try:
                os.makedirs(path)
                torch.save(critic.state_dict(), path + f'{critic_id}.pth')
            except OSError:
                print(f'Could not make directory: \'{path}\'')

    def _load_critic(self, critic_id: str, path = 'RL/models/critics/'):
        critic = Critic()
        critic.load_state_dict(torch.load(path + f'{critic_id}.pth'))
        critic.train()
        return critic

    def _save_actor(self, actor_id: str, actor: Actor, path = 'RL/models/actors/'):
        if os.path.isdir(path):
            torch.save(actor.state_dict(), path + f'{actor_id}.pth')
        else:
            try:
                os.makedirs(path)
                torch.save(actor.state_dict(), path + f'{actor_id}.pth')
            except OSError:
                print(f'Could not make directory: \'{path}\'')

    def _load_actor(self, actor_id: str, path = 'RL/models/actors/', eval_mode = False):
        actor = Actor()
        actor.load_state_dict(torch.load(path + f'{actor_id}.pth'))
        if eval_mode: actor.eval()
        else: actor.train()

        return actor
