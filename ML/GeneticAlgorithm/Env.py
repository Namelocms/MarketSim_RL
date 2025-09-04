import random
import math
import json

from Agent.TakerAgent import TakerAgent
from Agent.NoiseAgent import NoiseAgent
from Order.Order import Order
from Order.OrderAction import OrderAction
from Order.OrderType import OrderType
from Order.OrderStatus import OrderStatus
from OrderBook.OrderBook import OrderBook
from OrderBook.Matchmaker import MatchMaker


class Individual:
    ''' Represents a single Genetic Algorithm(GA) trader '''
    def __init__(self, _agent: TakerAgent):
        self.id = _agent.id
        self.genome_size = 6
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
    
    def calc_fitness(self, start_cash, state: list, step: int):
        ''' Calculates the fitness of the individual at the end of each generation\n
         Fitness is the total return percent minus the riskiness (half max drawdown) '''
        current_price = state[0]
        curr_val = self.agent.cash + (self.agent.get_total_shares() * current_price)
        return_perc = ((curr_val - start_cash) / start_cash) * 100

        # Calc max_drawdown
        if curr_val > self.peak_value: self.peak_value = curr_val
        curr_drawdown = (self.peak_value - curr_val) / self.peak_value
        self.max_drawdown = max(curr_drawdown, self.max_drawdown)

        # Avoid division by zero
        _step = step + 1

        self.fitness = (return_perc - (self.max_drawdown * 50))# / _step

    def act(self, action: OrderAction, state: list, ob: OrderBook):
        ''' Simplified actions to fit in GA training environment. Does not account for individual's effect on the market'''
        current_price = state[0]
        max_purchasable = int(self.agent.cash / current_price)
        match(action):
            case OrderAction.BID:
                self.agent.cash -= (max_purchasable * current_price)
                self.agent.update_holdings(current_price, max_purchasable)
                _order = Order(ob.get_id('ORDER'), self.id, current_price, max_purchasable, OrderAction.BID, OrderType.MARKET)
                _order.volume = 0
                self.agent.history[_order.id] = _order
                
            case OrderAction.ASK:
                self.agent.cash += (self.agent.get_total_shares() * current_price)
                _order = Order(ob.get_id('ORDER'), self.id, current_price, self.agent.get_total_shares(), OrderAction.ASK, OrderType.MARKET)
                _order.volume = 0
                self.agent.holdings.clear()
                self.agent.history[_order.id] = _order

            case OrderAction.HOLD:
                pass
    

class Env:
    ''' Environment for training Individuals of a Genetic Algorithm '''
    def __init__(self, _start_cash: float, _generations: int, _pop_size: int, _mutation_rate: float, _crossover_rate: float, _ob: OrderBook, _num_noise_agents: int, _version: str, _data_index: int = None):
        self.ob = _ob
        self.num_noise_agents = _num_noise_agents
        self.start_cash = _start_cash
        self.pop_size = _pop_size
        self.population = []
        self.mutation_rate = _mutation_rate
        self.crossover_rate = _crossover_rate
        self.generation = 0
        self.generations = _generations
        self.best_fitness = -math.inf
        self.best_individual = None
        self.market_info = {}
        self.version = _version
        self.data_index = _data_index

        self._init_individuals()
        self._load_market_data()
            

    def reset(self, version: str):
        self.population.clear()
        self.generation = 0
        self.market_info.clear()
        self.best_fitness = -math.inf
        self.best_individual = None
        self.version = version
        self.data_index = None
        self._init_individuals()
        #self._load_market_data()

    def generate_market_info(self, iterations: int):
        price_history = []
        
        # Run sim
        for i in range(iterations):
            for id, agent in self.ob.agents.items():
                agent.act(self.ob)
            price_history.append(self.ob.current_price)
            self._update_market_info(i, price_history)

    def train(self, save_increment = 10, enable_save = True, save_path='ML/GeneticAlgorithm/models/'):
        save_json_name = f'hof_{self.version}.json'

        # Sims used to train the current generation
        sims_used = [self.data_index]

        # Holds the best individuals at each save_increment
        hall_of_fame = []

        # Index of the current state of the market data
        index = 0

        while self.generation < self.generations:
            # Reset population parameters (not genome) every time market data changes
            if self.generation % 250 == 0:
                for i in self.population:
                    i.fitness = 0.0
                    i.max_drawdown = 0.0
                    i.peak_value = -math.inf
                    i.agent.reset(self.start_cash)

            state = self._get_state(index)
            for individual in self.population:
                action = individual.decide_action(state)
                individual.act(action, state, self.ob)

            self._evolve(state, index)
            
            # Save best individual
            if enable_save and self.generation % save_increment == 0:
                hall_of_fame.append(
                    {
                        'fitness': self.best_individual.fitness,
                        'genome': self.best_individual.genome.copy(),
                        'max_drawdown': self.best_individual.max_drawdown,
                        'id': self.best_individual.id,
                        'generation': self.generation,
                        'sims_used': sims_used,
                    }
                )
                print(self.best_individual.fitness)
                print(self.best_individual.genome)
                print('='*50)
            self.generation += 1
            index += 1

            # Get a new set of data if it has exceeded the chosen training data's size
            if self.generation % 249 == 0:
                #self.data_index = 8
                #self._load_market_data()
                #sims_used.append(self.data_index)
                index = 0

        # Save final best individual
        hall_of_fame.append(
            {
                'fitness': self.best_individual.fitness,
                'genome': self.best_individual.genome.copy(),
                'max_drawdown': self.best_individual.max_drawdown,
                'id': self.best_individual.id,
                'generation': self.generation,
                'sims_used': sims_used,
            }
        )
        print(self.best_individual.fitness)
        print(self.best_individual.genome)
        print('='*50)

        # Save Hall of Fame (hof) to JSON
        if enable_save:
            import os
            model_folder = f'hof_{self.generations}/'
            if os.path.isdir(save_path + model_folder):
                with open(save_path + model_folder + save_json_name, 'w') as f:
                    json.dump(hall_of_fame, f, indent=4)
                    f.close()
                print(f'DONE. Saved at [{save_path + model_folder + save_json_name}]')
            else:
                try:
                    os.makedirs(save_path + model_folder)
                    with open(save_path + model_folder + save_json_name, 'w') as f:
                        json.dump(hall_of_fame, f, indent=4)
                        f.close()
                    print(f'DONE. Saved at [{save_path + model_folder + save_json_name}]')
                except OSError:
                    print(f'Could not make directory: \'{save_path + model_folder}\'')
        else: print('Done.')

    def eval(self, model_path: str):
        min_cash = 10.00
        max_cash = 1000.00
        min_holdings = 0
        max_holdings = 1000
        running = True
        i = 1
        iterations = 1
        x = 0
        mm = MatchMaker()
        self.market_info.clear()

        model: Individual = self._load_model(model_path)
        if model == None: print('Model is \'None\'. Check model_path is correct.'); return

        model.agent.cash = self.start_cash

        for _ in range(self.num_noise_agents):
            cash = random.randint(min_cash, max_cash)
            agent = NoiseAgent(self.ob.get_id('AGENT'), cash)
            vol = random.randint(min_holdings, max_holdings)
            if vol > 0:
                agent.update_holdings(agent._get_beta_price(self.ob.current_price, random.choice([OrderAction.BID, OrderAction.ASK])), vol)
            self.ob.upsert_agent(agent)

        print('Maturing Market...')
        for _ in range(250):
            print(self.ob.current_price)
            for agent in list(self.ob.agents.values()):
                agent.act(self.ob)

        # Add Random action control agent to judge effectiveness
        control_agent = NoiseAgent('--CONTROL--', self.start_cash)
        self.ob.upsert_agent(control_agent)
        self.ob.upsert_agent(model.agent)
        price_history = [self.ob.current_price]
        self._update_market_info(x, price_history)
        state = self._get_state(x)
        order: Order = None

        # Run sim
        while running:
            for agent in self.ob.agents.values():
                if agent.id != model.id:
                    agent.act(self.ob)
                else:
                    price_history.append(self.ob.current_price)
                    self._update_market_info(x, price_history)

                    if order != None:
                        # Stop loss at 25% decrease  
                        stop_loss_price = order.price - (order.price * 0.25)
                        if order.side == OrderAction.BID and self.ob.current_price <= stop_loss_price:
                            order = model.agent.make_market_ask(self.ob, model.agent.get_total_shares())
                            mm.match_market_ask(self.ob, order)
                            print('Stop-loss triggered!')
                            order = None

                    state = self._get_state(x)
                    max_purchasable = int(model.agent.cash / self.ob.current_price)
                    action = model.decide_action(state)
                    match action:
                        case OrderAction.BID:
                            if max_purchasable > 0:
                                order = model.agent.make_market_bid(self.ob, max_purchasable)
                                mm.match_market_bid(self.ob, order)
                        case OrderAction.ASK:
                            if model.agent.get_total_shares() > 0:
                                order = model.agent.make_market_ask(self.ob, model.agent.get_total_shares())
                                mm.match_market_ask(self.ob, order)
                                # Model refuses to buy after sale so just reset market_info and x and it will buy again
                                #self.market_info.clear()
                                #x = 0
                        case OrderAction.HOLD:
                            pass
            print(f'Iteration ({i}) Current Price: {self.ob.current_price} | Action: {action} | Holdings: {model.agent.holdings} | Cash: {model.agent.cash} | Value: {(model.agent.get_total_shares() * self.ob.current_price) + model.agent.cash}')
            x += 1
            if i < iterations:
                i += 1
            # Get user input for next action
            else:
                i = 1
                iterations = 1
                print('===================================================')
                choice = int(input('\n1. Continue\n2. Print Snapshot\n3. Get Control Agent info\n4. Reset Model\n5. Get Model info\n6. Model history\n7. Exit\n\nChoice: '))
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
                        #_cash = model.agent.cash
                        #model.fitness = 0
                        #model.genome.clear()
                        #model.peak_value = -math.inf
                        #model = self._load_model(model_path)
                        #if model == None: print('Model is \'None\'. Check model_path is correct.'); return
                        #model.agent.cash = _cash
                        print('No.')
                    case 5:
                        print(self.ob.agents[model.agent.id].cash)
                        print(self.ob.agents[model.agent.id].holdings)
                        print(self.ob.agents[model.agent.id].get_total_shares())
                        print('===================================================')
                    case 6:
                        for order in model.agent.history.values():
                            print(order.info())
                    case 7:
                        running = False
                    case _:
                        pass

    def _evaluate_fittness(self, state: list, step: int):
        for individual in self.population:
            individual.calc_fitness(self.start_cash, state, step)

        # Sort by fitness (descending)
        self.population.sort(key=lambda x: x.fitness, reverse=True)

        # Update best individual
        #if self.population[0].fitness > self.best_fitness:
        self.best_fitness = self.population[0].fitness
        # Create new Individual to preserve methods
        self.best_individual = Individual(TakerAgent('BGA-' + self.ob.get_id('AGENT'), random.uniform(self.start_cash / 2, self.start_cash * 2)))
        self.best_individual.genome = self.population[0].genome.copy()
        self.best_individual.fitness = self.population[0].fitness
        self.best_individual.max_drawdown = self.population[0].max_drawdown

    def _update_market_info(self, iteration: int, price_history: list):
        prev_price = price_history[iteration - 1] if iteration > 0 else self.ob.current_price
        
        # Short-term Moving avg (5 iterations)
        ma5 = 0.0
        if iteration >= 4:
            ma5 = sum(price_history[-5:]) / 5

        # Long-term Moving avg (10 iterations)
        ma10 = 0.0
        if iteration >= 9:
            ma10 = sum(price_history[-10:]) / 10

        # Volatility (standard deviation of recent returns)
        volatility = 0.0
        if iteration >= 5:
            returns = []
            for i in range(1, 6):
                if iteration - i >= 0:
                    returns.append((price_history[iteration - i + 1] - price_history[iteration - i]) / price_history[iteration - i])
            avg_return = sum(returns) / len(returns)
            variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
            volatility = variance ** 0.5

        self.market_info[str(iteration)] = {
            "current_price": self.ob.current_price,
            "prev_price": prev_price,
            "price_change_perc": (self.ob.current_price - prev_price) / prev_price,
            "ma5": ma5,
            "ma10": ma10,
            "volatility": volatility
        }

    def _get_state(self, iteration):
        ''' Return the current state of the market '''
        _state = []
        _state.append(self.market_info[str(iteration)]['current_price'])
        _state.append(self.market_info[str(iteration)]['prev_price'])
        _state.append(self.market_info[str(iteration)]['price_change_perc'])
        _state.append(self.market_info[str(iteration)]['ma5'])
        _state.append(self.market_info[str(iteration)]['ma10'])
        _state.append(self.market_info[str(iteration)]['volatility'])

        return _state

    def _init_individuals(self):
        ''' Init and add GAs to the sim '''
        for i in range(self.pop_size):
            agent = TakerAgent('GA-' + str(i), random.uniform(self.start_cash / 2, self.start_cash * 2))
            individual = Individual(agent)
            self.population.append(individual)
            #self.ob.upsert_agent(agent)

    def _selection(self):
        ''' Tournament Selection '''
        tournament_size = 5
        selected = []

        for i in range(self.pop_size):
            tournament = []
            for j in range(tournament_size):
                random_index = random.randrange(len(self.population))
                tournament.append(self.population[random_index])

            tournament.sort(key=lambda x: x.fitness, reverse=True)
            selected.append(tournament[0])
        return selected

    def _crossover(self, parent1: Individual, parent2: Individual):
        if random.random() > self.crossover_rate:
            return [parent1, parent2]
        
        child1 = Individual(TakerAgent('GAC-' + self.ob.get_id('AGENT'), random.uniform(self.start_cash / 2, self.start_cash * 2)))
        child2 = Individual(TakerAgent('GAC-' + self.ob.get_id('AGENT'), random.uniform(self.start_cash / 2, self.start_cash * 2)))

        crossover_point = random.randrange(parent1.genome_size)
        for i in range(parent1.genome_size):
            if i < crossover_point:
                child1.genome[i] = parent1.genome[i]
                child2.genome[i] = parent2.genome[i]
            else:
                child1.genome[i] = parent2.genome[i]
                child2.genome[i] = parent1.genome[i]

        return [child1, child2]

    def _mutate(self, individual: Individual):
        for i in range(individual.genome_size):
            if random.random() < self.mutation_rate:
                individual.genome[i] += ((random.random() - 0.5) * 0.2) # Small mutation
                individual.genome[i] = max(min(individual.genome[i], 1), -1) # clamp to [-1, 1]

    def _evolve(self, state: list, step: int):
        ''' Evolve the population and replace it with a new population, retaining the top 10% of individuals from the original population '''
        self._evaluate_fittness(state, step)

        selected = self._selection()
        new_pop = []

        # Elitism: Keep top 10% of pop
        elite_count = int(self.pop_size * 0.1)
        for i in range(elite_count):
            # Create new instances to preserve methods
            elite = Individual(TakerAgent('EGA-' + self.ob.get_id('AGENT'), random.uniform(self.start_cash / 2, self.start_cash * 2)))
            elite.genome = self.population[i].genome.copy()
            new_pop.append(elite)

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

        # Repopulate orderbook agents to match new_pop
        #self.ob.agents.clear()
        #for individual in self.population:
        #    self.ob.upsert_agent(individual.agent)

    def _load_market_data(self):
        try:
            with open('ML/GeneticAlgorithm/market_data.json', 'r') as f:
                _full_market_data = json.load(f)
                if self.data_index != None:
                    self.market_info = _full_market_data[self.data_index]
                else:
                    self.data_index = random.randrange(len(_full_market_data))
                    self.market_info = _full_market_data[self.data_index]
                print(f'Using Market Data from Simulation #{self.data_index}')
        except OSError as e:
            print('ERROR! Check JSON: [market_data.json] exists in path: [ML/GeneticAlgorithm/]\n' + e)

    def _load_model(self, model_path):
        try:
            with open(f'ML/GeneticAlgorithm/models/{model_path}', 'r') as f:
                _models = json.load(f)
                _best = _models[9]
                i = Individual(TakerAgent('--GA_AGENT--'))
                i.fitness = _best['fitness']
                i.genome = _best['genome']
                i.max_drawdown = _best['max_drawdown']

                print(i.fitness)

                return i
                
        except OSError as e:
            print('ERROR! Check JSON: [market_data.json] exists in path: [ML/GeneticAlgorithm/]\n' + e)