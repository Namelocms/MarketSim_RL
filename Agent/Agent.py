from random import randint
import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger(__name__)

class Agent:
    ''' Base class for an agent
    
    - id -> Agent's unique id
    - cash -> Amount of liquid cash available to the agent
    - holdings -> Current shares held and available to the agent -> {price: volume}
    '''
    def __init__(self, id, manager, cash=randint(10, 1000)):
        self.id = id
        self.cash = cash
        self.holdings = manager.dict()
        self.active_asks = manager.dict()
        self.active_bids = manager.dict()
        self.history = manager.dict()
        self.max_price_deviation = 0.025  # = x/100

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
                if self.holdings[price] == 0:
                    self.holdings.pop(price)
        except Exception as e:
            log.error(f'ERROR: PRICE {price} DOES NOT EXIST: ERROR DETAILS: {e}')

    def remove_holdings(self, volume):
        ''' Remove the given volume of holdings starting from lowest value share '''
        try:
            while volume > 0 and len(self.holdings.keys()) > 0:
                price, vol = self.get_lowest_value_share()
                if vol > volume:
                    self.remove_holding(price, volume)
                    volume = 0
                else:
                    self.remove_holding(price)
                    volume -= vol
        except Exception as e:
            log.error(f'ERROR: PRICE {price} DOES NOT EXIST: ERROR DETAILS: {e}')

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

    def get_total_shares(self):
        total_shares = 0
        for holding in self.holdings.keys():
            total_shares += self.holdings[holding]
        
        return total_shares

    def info(self):
        ''' Log information related to the agent to the console '''
        log.info('=' * 50)
        log.info(f'ID: {self.id}\nCASH: {self.cash}')
        for price in self.holdings.keys():
            log.info(f'SHARE: {self.holdings[price]} @ ${price}')
        log.info('=' * 50)
