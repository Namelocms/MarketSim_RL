import random
import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger(__name__)

from Agent.Agent import Agent
from Order.Order import Order
from Order.OrderAction import OrderAction
from Order.OrderType import OrderType
from OrderBook.OrderBook import OrderBook

class NoiseAgent(Agent):
    ''' Makes random actions based on it's available holdings, cash, and active orders '''

    def _get_action(self, ob: OrderBook) -> OrderAction:
        ''' Choose a random OrderAction given the agent's current holdings and cash '''
        available_actions = [OrderAction.HOLD]  # HOLD is always available
        
        if self.cash >= ob.current_price:
            available_actions.append(OrderAction.BID)
        
        elif len(self.holdings.keys()) > 0:
            available_actions.append(OrderAction.ASK)
        
        elif len(self.active_asks.keys()) > 0 or len(self.active_bids.keys()) > 0:
            available_actions.append(OrderAction.CANCEL)

        return random.choice(available_actions)
        
    def _execute_market_bid(self, ob: OrderBook):
        ''' Choose a random volume to buy at current price and make an order '''
        max_purchasable = int(self.cash / ob.current_price)
        chosen_vol = random.randint(1, max_purchasable)
        
        mb_order = Order(
            id=         ob.get_id('ORDER'), 
            agent_id=   self.id, 
            price=      -1,
            volume=     chosen_vol, 
            side=       OrderAction.BID,
            type=       OrderType.MARKET
        )
        
        self.history[mb_order.id] = mb_order
        
        return mb_order

    def _execute_limit_bid(self, ob: OrderBook):
        ''' Choose random price and volume then make an order '''
        perc_below = random.randint(0, 10)
        perc_mod = random.random()
        perc = perc_below + perc_mod
        amt_below = ob.current_price * perc
        chosen_val = ob.current_price - amt_below
        
        max_purchasable = int(self.cash / chosen_val)
        chosen_vol = random.randint(1, max_purchasable)

        total_value = chosen_val * chosen_vol
        
        lb_order = Order(
            id=         ob.get_id('ORDER'),
            agent_id=   self.id,
            price=      chosen_val,
            volume=     chosen_vol,
            side=       OrderAction.BID,
            type=       OrderType.LIMIT
        )
        
        self.active_bids[lb_order.id] = lb_order
        self.history[lb_order.id] = lb_order
        self.update_cash(-total_value)
        
        return lb_order

    def _execute_market_ask(self, ob: OrderBook):
        ''' Choose a random volume to sell at current price and make an order '''
        chosen_vol = random.randint(1, self.get_total_shares())
        
        ma_order = Order(
            id=         ob.get_id('ORDER'), 
            agent_id=   self.id, 
            price=      -1, 
            volume=     chosen_vol, 
            side=       OrderAction.ASK,
            type=       OrderType.MARKET
        )
        
        self.history[ma_order.id] = ma_order
        
        return ma_order

    def _execute_limit_ask(self, ob: OrderBook):
        # choose val
        perc_above = random.randint(0, 10)
        perc_mod = random.random()
        perc = perc_above + perc_mod
        amt_above = ob.current_price * perc
        chosen_val = ob.current_price + amt_above
        # choose vol
        chosen_vol = random.randint(1, self.get_total_shares())
        # make order
        la_order = Order(
            id=ob.get_id('ORDER'),
            agent_id=self.id,
            price=chosen_val,
            volume=chosen_vol,
            side=OrderAction.ASK,
            type=OrderType.LIMIT
        )
        self.active_asks[la_order.id] = la_order
        self.history[la_order.id] = la_order
        self.remove_holdings(chosen_vol)
        
        return la_order

    def _execute_cancel(self, ob: OrderBook):
        ''' Cancels a random order '''
        chosen_side = random.choice([OrderAction.BID, OrderAction.ASK])

        match chosen_side:
            case OrderAction.BID:
                chosen_order_id = random.choice(self.active_bids.keys())
                ob.cancel_order(chosen_order_id)
            case OrderAction.ASK:
                chosen_order_id = random.choice(self.active_asks.keys())
                ob.cancel_order(chosen_order_id)
            case _:
                pass

    def _execute_hold(self, ob: OrderBook):
        # Do nothing here?
        pass
    
    def act(self, ob: OrderBook) -> Order:
        ''' Perform random OrderAction '''
        action = self._get_action(ob)
        order_type = random.choice([OrderType.MARKET, OrderType.LIMIT])

        match action:
            case OrderAction.BID:
                match order_type:
                    case OrderType.MARKET:
                        self._execute_market_bid(ob)
                    case OrderType.LIMIT:
                        self._execute_limit_bid(ob)
                    case _:
                        pass

            case OrderAction.ASK:
                match order_type:
                    case OrderType.MARKET:
                        self._execute_market_ask(ob)
                    case OrderType.LIMIT:
                        self._execute_limit_ask(ob)
                    case _:
                        pass

            case OrderAction.CANCEL:
                self._execute_cancel(ob)
                pass

            case OrderAction.HOLD:
                self._execute_hold(ob)
                pass

            case _:
                log.error(f'INVALID ACTION VALUE @ NoiseAgent.act(ob): {action}')