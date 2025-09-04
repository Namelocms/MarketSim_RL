import random
import math
from copy import deepcopy

from Agent.TakerAgent import TakerAgent
from Agent.NoiseAgent import NoiseAgent
from Order.OrderAction import OrderAction
from OrderBook.OrderBook import OrderBook
from OrderBook.Matchmaker import MatchMaker

class Individual:
    ''' Represents a single Genetic Algorithm(GA) trader '''
    def __init__(self, _agent: TakerAgent):
        self.id = _agent.id
        self.genome_size = 23
        self.genome = [random.uniform(-1.0, 1.0) for _ in range(self.genome_size)]
        self.fitness = 0.0
        self.agent = _agent
        self.max_drawdown = 0.0 # Risk management, mesures percent change from best portfolio value to worst e.g. 100$ start -> 50$ = 50% drawdown -> 75$ = 25% drawdown ||| max is 50% drawdown
        self.peak_value = -math.inf

    def decide_action(self, state):
        ''' Decides which action to take based on current market state '''
        score = 0.0
        # Get dot-product of genome and market state (kinda like a single-layer neural network)
        for i in range(self.genome_size):
            score += (self.genome[i] * state[i])

        # Get action probabilities from genome
        bid_threshold = self.genome[self.genome_size - 2] if self.genome[self.genome_size - 2] else 0.3
        ask_threshold = self.genome[self.genome_size - 1] if self.genome[self.genome_size - 1] else -0.3

        if score > bid_threshold: return OrderAction.BID
        if score < ask_threshold: return OrderAction.ASK
        return OrderAction.HOLD
    
    def calc_fitness(self, start_cash, current_price, step):
        ''' Calculates the fitness of the individual at the end of each generation\n
         Fitness is the total return percent minus the riskiness (half max drawdown) '''
        curr_val = self.agent.cash + (self.agent.get_total_shares() * current_price)
        return_perc = ((curr_val - start_cash) / start_cash) * 100

        # Calc max_drawdown
        if curr_val > self.peak_value: self.peak_value = curr_val
        curr_drawdown = (self.peak_value - curr_val) / self.peak_value
        self.max_drawdown = max(curr_drawdown, self.max_drawdown)

        # Avoid division by zero
        #_step = step + 1

        self.fitness = (return_perc - (self.max_drawdown * 50))# - step

    def act(self, action: OrderAction, ob: OrderBook):
        mm = MatchMaker()
        max_purchasable = int(self.agent.cash / ob.current_price)

        # Refine action
        if action == OrderAction.BID and max_purchasable <= 0: action = OrderAction.HOLD
        if action == OrderAction.ASK and self.agent.get_total_shares() <= 0: action = OrderAction.HOLD

        match(action):
            case OrderAction.BID:
                if max_purchasable <= 0: return
                order = self.agent.make_market_bid(ob, max_purchasable)
                mm.match_market_bid(ob, order)
            case OrderAction.ASK:
                if self.agent.get_total_shares() <= 0: return
                order = self.agent.make_market_ask(ob, self.agent.get_total_shares())
                mm.match_market_ask(ob, order)
            case OrderAction.HOLD:
                pass
        self.agent = ob.agents[self.id]

class Env:
    def __init__(self, _start_cash: float, _pop_size: int, _mutation_rate: float, _crossover_rate: float, _ob: OrderBook, _num_noise_agents: int, _version: str):
        self.ob = _ob
        self.num_noise_agents = _num_noise_agents
        self.start_cash = _start_cash
        self.pop_size = _pop_size
        self.population: list[Individual] = []
        self.mutation_rate = _mutation_rate
        self.crossover_rate = _crossover_rate
        self.best_fitness = -math.inf
        self.best_individual = None
        self.temp_best = None
        self.market_info = {}
        self.price_history: list[float] = []
        self.version = _version

        self._reset_market(self.num_noise_agents)
        self._init_individuals()
        self.best_individual = self.population[0]
        self.temp_best = self.best_individual

    def train(self):
        running = True
        step = 0
        target_steps = 0

        # Best agents Hall of Fame
        hof = []

        while running:
            choice = 0

            if step >= target_steps:
                step = 0
                target_steps = 0

                while choice not in (1, 8):
                    print('='*50)
                    try:
                        choice = int(input('\n1. Continue\n2. Print Snapshot\n3. Best Agent Info\n4. Reset Sim\n5. Control Agent info\n6. Population\n7. Save Best\n8. Save and Exit\n-->'))
                    except:
                        running = False
                        break

                    match choice:
                        # Continue
                        case 1:
                            try:
                                target_steps = int(input('Steps to go forward: '))
                                if target_steps <= 0: raise ValueError(f'Invalid target_steps: {target_steps}')
                            except:
                                target_steps = 1
                        # Print Snapshot
                        case 2:
                            try:
                                depth = int(input('Snapshot Depth: '))
                                if depth <= 0: raise ValueError(f'Invalid depth: {depth}')
                            except:
                                depth = 1
                            snapshot = self.ob.get_snapshot(depth)[0]
                            asks = snapshot['asks']
                            bids = snapshot['bids']

                            print(f'Asks: ({len(asks)})')
                            for ask in asks:
                                print(f'${ask["price"]}: {ask["size"]}')
                            print('_'*50)
                            print(f'Bids: ({len(bids)})')
                            for bid in bids:
                                print(f'${bid["price"]}: {bid["size"]}')
                            print('='*50)
                            
                        # Best Agent Info
                        case 3:
                            if self.temp_best != None:
                                print(f'Temp-Genome: {self.temp_best.genome}')
                                print(f'Temp-Fitness: {self.temp_best.fitness}')
                                print(f'Temp-Max Drawdown: {self.temp_best.max_drawdown}')
                                print(f'Temp-Peak value: {self.temp_best.peak_value}')
                                print(f'Temp-Current value: {(self.temp_best.agent.get_total_shares() * self.ob.current_price) + self.temp_best.agent.cash}')
                                print(self.temp_best.agent.info())
                                print('='*50)
                                print(f'BEST-Genome: {self.best_individual.genome}')
                                print(f'BEST-Fitness: {self.best_individual.fitness}')
                                print(f'BEST-Max Drawdown: {self.best_individual.max_drawdown}')
                                print(f'BEST-Peak value: {self.best_individual.peak_value}')
                                print(f'BEST-Current value: {(self.best_individual.agent.get_total_shares() * self.ob.current_price) + self.best_individual.agent.cash}')
                                print(self.best_individual.agent.info())
                            else:
                                print('No best CGAA yet!')
                        # Reset Sim
                        case 4:
                            try:
                                initial_price = float(input('OB Initial Price: '))
                                if initial_price <= 0: raise ValueError(f'Invalid initial_price: {initial_price}')
                                num_agents = int(input('Number of Noise Agents (<= 1000 reccomended): '))
                                if num_agents <= 0: raise ValueError(f'Invalid num_agents: {num_agents}')
                                max_holdings = int(input('Max start holdings for Noise Agents: '))
                                if max_holdings <= 0: raise ValueError(f'Invalid max_holdings: {max_holdings}')
                                max_cash = float(input('Max start cash for Noise Agents: '))
                                if max_cash <= 0: raise ValueError(f'Invalid max_cash: {max_cash}')
                            except Exception as e:
                                initial_price = 1.00
                                num_agents = 100
                                max_holdings = 1000
                                max_cash = 1000.00
                                print(f'Defaulting to Initial price: ${initial_price} and Num agents: {num_agents}\nDue to Exception: {e}')
                            self.ob.reset(initial_price)
                            self.ob.agents.clear()
                            self.price_history.clear()
                            self.market_info.clear()
                            self._reset_market(num_agents, max_cash, max_holdings, steps_to_mature=25)
                            # Control Agent
                            control_agent = NoiseAgent('--CONTROL--', self.start_cash)
                            self.ob.upsert_agent(control_agent)
                            # CGAAgents
                            for cgaa in self.population:
                                cgaa.agent.reset(cash=self.start_cash)
                                cgaa.peak_value = -math.inf
                                cgaa.fitness = 0.00
                                cgaa.max_drawdown = 0.00
                                self.ob.upsert_agent(cgaa.agent)
                            if self.temp_best != None:
                                hof.append(
                                    {
                                        'fitness': self.temp_best.fitness,
                                        'genome': self.temp_best.genome.copy(),
                                        'max_drawdown': self.temp_best.max_drawdown,
                                        'peak_value': self.temp_best.peak_value,
                                        'id': self.temp_best.id,
                                        'generation': len(self.price_history),
                                        'agent_cash': self.temp_best.agent.cash,
                                        'agent_total_shares': self.temp_best.agent.get_total_shares(),
                                        'trade_history': deepcopy(self.temp_best.agent.history)
                                    }
                                )
                            self.best_fitness = 0.0
                            self.best_individual = self.population[0]
                            self.temp_best = self.population[0]

                        # Control agent info
                        case 5:
                            print(self.ob.agents['--CONTROL--'].info())
                            #try:
                            #    agents_to_add = int(input('Number of agents to add: '))
                            #    if agents_to_add <= 0: raise ValueError(f'Invalid agents_to_add: {agents_to_add}')
                            #    holdings_per_agent = int(input('Start holdings for each agent (0 -> Bull market target, > 0 -> Bear market target): '))
                            #    if holdings_per_agent < 0: raise ValueError(f'Invalid holdings_per_agent: {holdings_per_agent}')
                            #    cash_per_agent = int(input('Start cash for each agent: '))
                            #    if cash_per_agent < 0: raise ValueError(f'Invalid cash_per_agent: {cash_per_agent}')
                            #except Exception as e:
                            #    agents_to_add = 0
                            #    holdings_per_agent = 0
                            #    cash_per_agent = 0.00
                            #    print(f'Adding no agents due to exception: {e}')
                            #
                            #for a in range(agents_to_add):
                            #    _agent = NoiseAgent(f'--LIQUID_A{a}--', cash_per_agent)
                            #    if holdings_per_agent > 0: _agent.update_holdings(_agent._get_beta_price(self.ob.current_price, random.choice([OrderAction.ASK, OrderAction.BID])), holdings_per_agent)
                            #    self.ob.upsert_agent(_agent)
                            
                        # Remove Liquid
                        case 6:
                            for p in self.population: print(f'ID: {p.id}\nGenome: {p.genome}\nFitness: {p.fitness}\nMax Drawdown: {p.max_drawdown}\nPeak Value: {p.peak_value}')
                            #try:
                            #    agents_to_remove = int(input(f'Number of agents to remove (Current = {len(self.ob.agents.keys())}): '))
                            #    if agents_to_remove <= 0 or agents_to_remove >= len(self.ob.agents.keys()): raise ValueError(f'Invalid agents_to_remove: {agents_to_remove}')
                            #except Exception as e:
                            #    agents_to_remove = 0
                            #    print(f'Removing 0 agents due to exception: {e}')
#
                            #_to_remove = []
                            #for id, agent in self.ob.agents.items():
                            #    if agents_to_remove <= 0: break
                            #    if 'CGA' not in id: 
                            #        _to_remove.append(id)
                            #        agents_to_remove -= 1
#
                            #for id in _to_remove:
                            #    del self.ob.agents[id]

                        # Save Best
                        case 7:
                            if self.temp_best != None:
                                hof.append(
                                    {
                                        'fitness': self.temp_best.fitness,
                                        'genome': self.temp_best.genome.copy(),
                                        'max_drawdown': self.temp_best.max_drawdown,
                                        'peak_value': self.temp_best.peak_value,
                                        'id': self.temp_best.id,
                                        'generation': len(self.price_history),
                                        'agent_cash': self.temp_best.agent.cash,
                                        'agent_total_shares': self.temp_best.agent.get_total_shares()
                                    }
                                )
                            else: print('No best CGAA yet!')
                        # Exit
                        case 8:
                            running = False
                            print('Saving and Exiting...')
                            self._save_hof(hof)
                            break
                        # Invalid choice
                        case _:
                            running = False
                            break

            else:
                for agent in self.ob.agents.values():
                    # Skip CGAAs
                    if 'CGA' not in agent.id:
                        agent.act(self.ob)
                self.price_history.append(self.ob.current_price)

                # Get the current state of the market for CGAAs
                for cgaa in self.population:
                    # Get new state for each CGAA
                    state = self._get_state(cgaa)
                    action = cgaa.decide_action(state)
                    if self.best_individual != None and cgaa.id == self.best_individual.id: print(action)
                    cgaa.act(action, self.ob)

                # Evolve every 10 steps
                if step % 1440 == 0:
                    self._evolve()
                step += 1

                # Save best after run completed to HoF
                if step >= target_steps:
                    if self.temp_best != None:
                        hof.append(
                            {
                                'fitness': self.temp_best.fitness,
                                'genome': self.temp_best.genome.copy(),
                                'max_drawdown': self.temp_best.max_drawdown,
                                'peak_value': self.temp_best.peak_value,
                                'id': self.temp_best.id,
                                'generation': len(self.price_history),
                                'agent_cash': self.temp_best.agent.cash,
                                'agent_total_shares': self.temp_best.agent.get_total_shares()
                            }
                        )

    def eval(self):
        pass

    def _evaluate_fitness(self):
        for i in self.population:
            i.calc_fitness(self.start_cash, self.ob.current_price, len(self.price_history))
        
        self.population.sort(key=lambda x: x.fitness, reverse=True)
        self.temp_best = deepcopy(self.population[0])
        if self.population[0].fitness > self.best_individual.fitness:
            #if self.best_individual != None and self.population[0].id != self.best_individual.id:
            #    print(self.population[0].genome)
            #    print(self.population[0].fitness)
            #    print(self.population[0].max_drawdown)
            #    print(self.population[0].peak_value)
            #    print(self.population[0].agent.info())
            #    print('='*50)

            self.best_fitness = self.population[0].fitness
            self.best_individual = deepcopy(self.population[0])#Individual(TakerAgent(f'B{len(self.price_history)}-CGA{self.ob.get_id("AGENT")}', cash=self.start_cash))
            print(f'Best ID: {self.best_individual.id}')
            #self.best_individual.genome = self.population[0].genome.copy()
            #self.best_individual.fitness = self.population[0].fitness
            #self.best_individual.max_drawdown = self.population[0].max_drawdown

    def _selection(self, pop_perc=0.05):
        ''' Tournament Selection of X% population'''
        tournament_size = math.floor(self.pop_size * pop_perc)
        selected = []
        used_indexs = []

        for i in range(self.pop_size):
            tournament = []
            for j in range(tournament_size):
                random_index = random.randrange(self.pop_size)
                if random_index in used_indexs: random_index = random.randrange(self.pop_size)
                used_indexs.append(random_index)
                tournament.append(self.population[random_index])
            tournament.sort(key=lambda x: x.fitness, reverse=True)
            selected.append(tournament[0])
        return selected

    def _crossover(self, parent1: Individual, parent2: Individual):
        if random.random() > self.crossover_rate:
            return [parent1, parent2]
        
        child1 = Individual(TakerAgent(f'C-CGA{self.ob.get_id("AGENT")}', cash=self.start_cash))
        child2 = Individual(TakerAgent(f'C-CGA{self.ob.get_id("AGENT")}', cash=self.start_cash))

        crossover_point = random.randrange(parent1.genome_size)
        for i in range(parent1.genome_size):
            if i < crossover_point:
                child1.genome[i] = parent1.genome[i]
                child2.genome[i] = parent2.genome[i]
            else:
                child1.genome[i] = parent2.genome[i]
                child2.genome[i] = parent1.genome[i]
        return [child1, child2]

    def _mutate(self, i: Individual):
        for x in range(i.genome_size):
            if random.random() < self.mutation_rate:
                i.genome[x] += ((random.random() - 0.50) * 0.20)
                i.genome[x] = max(min(i.genome[x], 1), -1)

    def _evolve(self, retain_perc=0.10):
        ''' Evolve population, replace with new pop, retain top X% '''
        self._evaluate_fitness()
        
        selected = self._selection()
        new_pop = []

        # Keep elites
        elite_count = int(self.pop_size * retain_perc)
        self.population.sort(key=lambda x: x.fitness, reverse=True)
        for i in range(elite_count):
            elite = deepcopy(self.population[i])#Individual(TakerAgent(f'E-CGA{self.ob.get_id("AGENT")}', cash=self.start_cash))
            elite.agent.reset(self.start_cash)
            elite.fitness = 0.0
            elite.max_drawdown = 0.0
            elite.peak_value = -math.inf
            #elite.genome = self.population[i].genome.copy()
            new_pop.append(elite)
        print('='*50)
        #for p in new_pop: print(f'ID: {p.id}\nGenome: {p.genome}\nFitness: {p.fitness}\nMax Drawdown: {p.max_drawdown}\nPeak Value: {p.peak_value}')

        # Generate offspring
        while len(new_pop) < self.pop_size:
            parent1 = random.choice(selected)
            parent2 = random.choice(selected)

            child1, child2 = self._crossover(parent1, parent2)

            self._mutate(child1)
            self._mutate(child2)

            new_pop.append(child1)
            if len(new_pop) < self.pop_size:
                new_pop.append(child2)

        self.population = new_pop

        # Remove old CGAAs from ob and replace with new_pop CGAAs
        _to_delete = []
        for id, agent in self.ob.agents.items():
            if 'CGA' in id:
                _to_delete.append(id)
                for order_id in agent.active_asks.keys():
                    self.ob._remove_from_queue(order_id)
                for order_id in agent.active_bids.keys():
                    self.ob._remove_from_queue(order_id)
        for id in _to_delete:
            del self.ob.agents[id]
        for i in self.population:
            self.ob.upsert_agent(i.agent)

    def _update_market_info(self, ob_depth_window=10, short_term_window=5, long_term_window=10, volatility_window=5):
        # Price history length
        phl = len(self.price_history)
        prev_price = self.price_history[-1] if phl > 0 else self.ob.current_price
        price_change_perc = (self.ob.current_price - prev_price) / prev_price

        # Short-term moving avg
        stma = 0.0
        if phl >= short_term_window:
            stma = sum(self.price_history[-short_term_window:]) / short_term_window
        # Long-term moving avg
        ltma = 0.0
        if phl >= long_term_window:
            ltma = sum(self.price_history[-long_term_window:]) / long_term_window

        # Volatility (std deviation of recent returns)
        v = 0.0
        if phl > volatility_window:
            returns = []
            for i in range(1, volatility_window + 1):
                returns.append(
                    (self.price_history[phl - i] - self.price_history[phl - i - 1]) 
                    / self.price_history[phl - i - 1]
                )
            avg_return = sum(returns) / len(returns)
            variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
            v = variance ** 0.50

        snapshot = self.ob.get_snapshot(ob_depth_window)
        asks = snapshot[0]['asks']
        asks_size = len(asks)
        bids = snapshot[0]['bids']
        bids_size = len(bids)
        spread = 0.0
        largest_ask_price = 0.00
        largest_ask_vol = 0
        largest_ask_position = 0
        largest_bid_price = 0.00
        largest_bid_vol = 0
        largest_bid_position = 0
        best_ask_price = 0.00
        best_ask_vol = 0
        best_bid_price = 0.00
        best_bid_vol = 0
        
        if asks_size > 0:
            best_ask_price = asks[0]['price']
            best_ask_vol = asks[0]['size']
            for a in range(asks_size):
                if asks[a]['size'] > largest_ask_vol:
                    largest_ask_vol = asks[a]['size']
                    largest_ask_price = asks[a]['price']
                    largest_ask_position = a
        if bids_size > 0:
            best_bid_price = bids[0]['price']
            best_bid_vol = bids[0]['size']
            for b in range(bids_size):
                if bids[b]['size'] > largest_bid_vol:
                    largest_bid_vol = bids[b]['size']
                    largest_bid_price = bids[b]['price']
                    largest_bid_position = b
        if asks_size > 0 and bids_size > 0:
            spread = asks[0]['price'] - bids[0]['price']

        # 19 market indicators
        self.market_info[str(phl)] = {
            'current_price': self.ob.current_price,
            'prev_price': prev_price,
            'price_change_perc': price_change_perc,
            'stma': stma,
            'ltma': ltma,
            'volatility': v,
            'num_asks': asks_size,
            'num_bids': bids_size,
            'spread': spread,
            'largest_ask_price': largest_ask_price,
            'largest_ask_vol': largest_ask_vol,
            'largest_ask_position': largest_ask_position,
            'largest_bid_price': largest_bid_price,
            'largest_bid_vol': largest_bid_vol,
            'largest_bid_position': largest_bid_position,
            'best_ask_price': best_ask_price,
            'best_ask_vol': best_ask_vol,
            'best_bid_price': best_bid_price,
            'best_bid_vol': best_bid_vol,
        }
        return str(phl)
    
    def _get_state(self, cgaa: Individual):
        ''' Return the current state of the market '''
        data_index = self._update_market_info(
            ob_depth_window= 20,
            short_term_window= 5,
            long_term_window= 10,
            volatility_window= 10
        )

        avg_share_price = 0.0
        if cgaa.agent.get_total_shares() > 0:
            for price in cgaa.agent.holdings.keys():
                avg_share_price += price
            avg_share_price /= cgaa.agent.get_total_shares()
        portfolio_value = (cgaa.agent.get_total_shares() * self.ob.current_price) + cgaa.agent.cash

        _state = []
        _state.append(self.market_info[data_index]['current_price'])
        _state.append(self.market_info[data_index]['prev_price'])
        _state.append(self.market_info[data_index]['price_change_perc'])
        _state.append(self.market_info[data_index]['stma'])
        _state.append(self.market_info[data_index]['ltma'])
        _state.append(self.market_info[data_index]['volatility'])
        _state.append(self.market_info[data_index]['num_asks'])
        _state.append(self.market_info[data_index]['num_bids'])
        _state.append(self.market_info[data_index]['spread'])
        _state.append(self.market_info[data_index]['largest_ask_price'])
        _state.append(self.market_info[data_index]['largest_ask_vol'])
        _state.append(self.market_info[data_index]['largest_ask_position'])
        _state.append(self.market_info[data_index]['largest_bid_price'])
        _state.append(self.market_info[data_index]['largest_bid_vol'])
        _state.append(self.market_info[data_index]['largest_bid_position'])
        _state.append(self.market_info[data_index]['best_ask_price'])
        _state.append(self.market_info[data_index]['best_ask_vol'])
        _state.append(self.market_info[data_index]['best_bid_price'])
        _state.append(self.market_info[data_index]['best_bid_vol'])
        _state.append(cgaa.agent.cash)
        _state.append(cgaa.agent.get_total_shares())
        _state.append(avg_share_price)
        _state.append(portfolio_value)

        # 23 total indicators
        return _state

    def _reset_market(self, num_agents, _max_cash: float=1000.00, _max_holdings: int=1000, steps_to_mature=25):
        min_cash = 10.00
        max_cash = _max_cash
        min_holdings = 0
        max_holdings = _max_holdings

        # Noise Agents
        for _ in range(num_agents):
            _cash = random.randint(min_cash, max_cash)
            agent: NoiseAgent = NoiseAgent(self.ob.get_id('AGENT'), cash=_cash)
            vol = random.randint(min_holdings, max_holdings)
            if vol > 0:
                agent.update_holdings(agent._get_beta_price(self.ob.current_price, random.choice([OrderAction.BID, OrderAction.ASK])), vol)
            self.ob.upsert_agent(agent)
        
        # Mature market
        for _ in range(steps_to_mature):
            for agent in self.ob.agents.values():
                agent.act(self.ob)
            self.price_history.append(self.ob.current_price)

        # Control Agent
        control_agent = NoiseAgent('--CONTROL--', self.start_cash)
        self.ob.upsert_agent(control_agent)

    def _init_individuals(self):
        for _ in range(self.pop_size):
            i = Individual(TakerAgent(f'CGA{self.ob.get_id("AGENT")}', cash=self.start_cash))
            self.population.append(i)
        for i in self.population:
            self.ob.upsert_agent(i.agent)

    def _save_hof(self, hof, save_path='ML/ContinuousGeneticAlgorithm/models/'):
        ''' Saves the current Hall of Fame for all the best CGAAs in this training run'''
        import os, json

        save_json_name = f'hof_{len(self.price_history)}.json'
        model_folder = f'hof_{self.version}/'

        if os.path.isdir(save_path + model_folder):
            with open(save_path + model_folder + save_json_name, 'w') as f:
                json.dump(hof, f, indent=4)
                f.close()
            print(f'DONE. Saved at [{save_path + model_folder + save_json_name}]')
        else:
            try:
                os.makedirs(save_path + model_folder)
                with open(save_path + model_folder + save_json_name, 'w') as f:
                    json.dump(hof, f, indent=4)
                    f.close()
                print(f'DONE. Saved at [{save_path + model_folder + save_json_name}]')
            except OSError:
                print(f'Could not make directory: \'{save_path + model_folder}\'')