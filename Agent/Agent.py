from random import randint
import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger(__name__)

class Agent:
    ''' Base class for an agent
    
    - id -> Agent's unique id
    - cash -> Amount of liquid cash available to the agent
    - holdings -> Current shares held and available to the agent -> {price: volume}
    - manager -> Multiproccessing manager for concurrency
    '''
    def __init__(self, id, manager, cash=randint(10, 1000)):
        self.id = id
        self.cash = cash
        self.holdings = manager.dict()
        self.manager = manager

    def update_cash(self, amt):
        ''' Update the cash holdings of this agent [Negative amt decreses cash] '''
        self.cash += amt

    def update_holdings(self, price, volume):
        ''' Update/add a share in the agent's holdings '''
        if price in self.holdings:
            self.holdings[price] += volume
        else:
            self.holdings[price] = volume

    def remove_holding(self, price, volume=0):
        ''' Remove the specified volume from a share [volume=0 -> remove all shares at price] '''
        try:
            if volume == 0:
                self.holdings.pop(price)
            else:
                self.holdings[price] -= volume
        except Exception as e:
            log.error(f'ERROR: PRICE {price} DOES NOT EXIST')

    def get_highest_value_share(self):
        ''' Get the most valuble share and volume from agent's holdings
        
        Returns -> (price, volume) tuple
        '''
        highest_price = max(self.holdings.keys())
        volume = self.holdings[highest_price]
        return (highest_price, volume)

    def get_lowest_value_share(self):
        ''' Get the least valuble share and volume from agent's holdings
        
        Returns -> (price, volume) tuple
        '''
        lowest_price = min(self.holdings.keys())
        volume = self.holdings[lowest_price]
        return (lowest_price, volume)

    def info(self):
        ''' Log information related to the agent to the console '''
        log.info('=' * 50)
        log.info(f'ID: {self.id}\nCASH: {self.cash}')
        for price in self.holdings.keys():
            log.info(f'SHARE: {self.holdings[price]} @ ${price}')
        log.info('=' * 50)
