from math import pi, sin, log
from scipy.stats import beta
from Order.Order import Order
from Order.OrderAction import OrderAction
from Util.Util import Util
import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class Agent:
    ''' Base class for an agent
    
    - id -> Agent's unique id
    - cash -> Amount of liquid cash available to the agent
    - holdings -> Current shares held and available to the agent -> {price: volume}
    - active_asks, active_bids -> Active orders in the market -> {order_id: Order}
    - history -> All orders that were placed on the market -> {order_id: Order}
    '''
    def __init__(self, id, cash=100):
        self.id: str = id
        self.cash: float = cash
        self.holdings: dict[float, int] = {}
        self.active_asks: dict[str, Order] = {}
        self.active_bids: dict[str, Order] = {}
        self.history: dict[str, Order] = {}

    def reset(self, cash=100):
        ''' Resets the agent to its initial state '''
        self.cash = cash
        self.holdings.clear()
        self.active_asks.clear()
        self.active_bids.clear()
        self.history.clear()

    def holdings_to_list(self):
        holdings_list = []
        for price, volume in self.holdings.items():
            holdings_list.append((price, volume))

    def update_cash(self, amt):
        ''' Update the cash holdings of this agent [Negative amt decreses cash] '''
        self.cash = round(self.cash + amt, Util.ROUND_NDIGITS)

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
            logger.error(f'ERROR: PRICE {price} DOES NOT EXIST: ERROR DETAILS: {e}')

    def remove_holdings(self, volume):
        ''' Remove the given volume of holdings starting from lowest value share, return the list of (price, volume) tuples of the removed shares '''
        removed_shares = []
        try:
            while volume > 0 and len(self.holdings.keys()) > 0:
                price, vol = self.get_lowest_value_share()
                if vol > volume:
                    self.remove_holding(price, volume)
                    removed_shares.append((price, volume))
                    volume = 0
                else:
                    self.remove_holding(price)
                    removed_shares.append((price, vol))
                    volume -= vol
        except Exception as e:
            logger.error(f'ERROR: PRICE {price} DOES NOT EXIST: ERROR DETAILS: {e}')
        return removed_shares

    def upsert_active_ask(self, order):
        self.active_asks[order.id] = order

    def upsert_active_bid(self, order):
        self.active_bids[order.id] = order

    def remove_active_ask(self, order_id):
        try:
            del self.active_asks[order_id]
        except KeyError:
            logger.error(f'Active order does not exist to delete with ID: {order_id}')

    def remove_active_bid(self, order_id):
        try:
            del self.active_bids[order_id]
        except KeyError:
            logger.error(f'Active order does not exist to delete with ID: {order_id}')

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
        return sum(self.holdings.values())

    def _get_max_variance(self, price, scale=0.1, decay_rate=0.25, amplitude=0.1, frequency=pi*2):
        '''
        Get the max variance in price (how much the computed price will differ from passed price)

        scale = Scale factor, controls the overall height of the curve\n
        decay_rate = The power-law decay rate, larger decay_rate -> variance falls off faster as price increases\n
        amplitude = The sinusoidal amplitude, controls how much the variance "wiggles" above/below the base curve. Set to 0 to disable sine behavior\n
        frequency = The frequency of the sine (in log space), higher frequency -> more wiggles per log unit of price\n

        PRICE__||  max_variance\n
        0.1____||  0.17783\n
        1______||  0.10000\n
        10_____||  0.05623\n
        100____||  0.03162\n
        1000___||  0.01778\n
        10000__||  0.01000\n
        100000_||  0.00562
        '''
        return scale * (price ** -decay_rate) * (1 + (amplitude * sin(frequency * log(price))))

    def _get_beta_price(self, current_price: float, side: OrderAction, a=2, b=5, epsilon = 1e-6):
        ''' Can be shaped to hug the current price without reaching it: [a > b: hugs lower end || a < b: hugs upper end]\n
            Has a nice distribution just a little past/before the current price is where most orders will be placed\n

            a = Higher favors right side (larger x)\n
            b = Higher favors left side (smaller x)\n
            epsilon = Minimum possible price (for bids only)\n
        '''
        max_variance = self._get_max_variance(
            current_price,
            scale=0.05,
            decay_rate=0.25,
            amplitude=0.1,
            frequency=pi*2
        )
        match side:
            case OrderAction.BID:
                x = beta.rvs(a, b)
                discount = x * max_variance
                return round(max(current_price * (1 - discount), epsilon), Util.ROUND_NDIGITS)
            case OrderAction.ASK:
                x = beta.rvs(a, b)
                premium = x * max_variance
                return round(current_price * (1 + premium), Util.ROUND_NDIGITS)
    
    def info(self):
        last_items = list(self.history.items())[-5:]  # get last 5 entries
        return f"""
=======================================================
    ID: {self.id}
    CASH: {self.cash}
    HOLDINGS: {self.holdings}
    ACTIVE_ASKS: {self.active_asks}
    ACTIVE_BIDS: {self.active_bids}
    HISTORY: 
        {'- '.join(f'{id}: {order.info()}' for id, order in last_items)}
=======================================================
            """


