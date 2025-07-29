import random
import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger(__name__)

from Agent.Agent import Agent
from Order.Order import Order
from Order.OrderAction import OrderAction
from Order.OrderType import OrderType
from OrderBook.OrderBook import OrderBook
from OrderBook.Matchmaker import MatchMaker
from Util.Util import Util

class NoiseAgent(Agent):
    ''' Makes random actions based on it's available holdings, cash, and active orders '''

    def _get_action(self, ob: OrderBook) -> OrderAction:
        ''' Choose a random OrderAction given the agent's current holdings and cash '''
        available_actions = [OrderAction.HOLD]  # HOLD is always available
        
        if self.cash >= ob.current_price:
            available_actions.append(OrderAction.BID)
        
        if self.get_total_shares() > 0:
            available_actions.append(OrderAction.ASK)
        
        if len(self.active_asks.keys()) > 0 or len(self.active_bids.keys()) > 0:
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
        ob.upsert_agent(self)
        
        return mb_order

    def _execute_limit_bid(self, ob: OrderBook):
        ''' Choose random price and volume then make an order '''
        chosen_val = self._get_beta_price(ob.current_price, OrderAction.BID)
        
        max_purchasable = int(self.cash / chosen_val)
        chosen_vol = random.randint(1, max_purchasable)

        total_value = round(chosen_val * chosen_vol, Util.ROUND_NDIGITS)
        
        lb_order = Order(
            id=         ob.get_id('ORDER'),
            agent_id=   self.id,
            price=      chosen_val,
            volume=     chosen_vol,
            side=       OrderAction.BID,
            type=       OrderType.LIMIT
        )
        
        self.history[lb_order.id] = lb_order
        self.update_cash(-total_value)
        ob.upsert_agent(self)

        return lb_order

    def _execute_market_ask(self, ob: OrderBook):
        ''' Choose a random volume to sell at current price and make an order '''
        assert self.get_total_shares() > 0, "Attempted to place market ask with zero holdings"

        chosen_vol = random.randint(1, self.get_total_shares())
        removed_shares = self.remove_holdings(chosen_vol)

        ma_order = Order(
            id=             ob.get_id('ORDER'), 
            agent_id=       self.id, 
            price=          -1, 
            volume=         chosen_vol, 
            side=           OrderAction.ASK,
            type=           OrderType.MARKET,
            reserved_shares= removed_shares
        )
        
        self.history[ma_order.id] = ma_order
        ob.upsert_agent(self)
        
        return ma_order

    def _execute_limit_ask(self, ob: OrderBook):
        assert self.get_total_shares() > 0, "Attempted to place limit ask with zero holdings"

        chosen_val = self._get_beta_price(ob.current_price, OrderAction.ASK)
        
        chosen_vol = random.randint(1, self.get_total_shares())
        removed_shares = self.remove_holdings(chosen_vol)

        la_order = Order(
            id=             ob.get_id('ORDER'),
            agent_id=       self.id,
            price=          chosen_val,
            volume=         chosen_vol,
            side=           OrderAction.ASK,
            type=           OrderType.LIMIT,
            reserved_shares= removed_shares
        )
        
        self.history[la_order.id] = la_order
        ob.upsert_agent(self)
        
        return la_order

    def _execute_cancel(self, ob: OrderBook):
        ''' Cancels a random order '''
        choices = []
        if len(self.active_asks.keys()) > 0:
            choices.append(OrderAction.ASK)
        if len(self.active_bids.keys()) > 0:
            choices.append(OrderAction.BID)
        chosen_side = random.choice(choices)

        match chosen_side:
            case OrderAction.BID:
                chosen_order_id = random.choice(list(self.active_bids.keys()))
                ob.cancel_order(chosen_order_id, self)
            case OrderAction.ASK:
                chosen_order_id = random.choice(list(self.active_asks.keys()))
                ob.cancel_order(chosen_order_id, self)
            case _:
                pass

    def _execute_hold(self, ob: OrderBook):
        # Do nothing here?
        pass
    
    def act(self, ob: OrderBook):
        ''' Perform random OrderAction '''
        mm = MatchMaker() 
        action = self._get_action(ob)
        order_type = random.choice([OrderType.MARKET, OrderType.LIMIT])

        match action:
            case OrderAction.BID:
                match order_type:
                    case OrderType.MARKET:
                        ready_order = self._execute_market_bid(ob)
                        mm.match_market_bid(ob, ready_order)
                    case OrderType.LIMIT:
                        ready_order = self._execute_limit_bid(ob)
                        mm.match_limit_bid(ob, ready_order)
                    case _:
                        pass

            case OrderAction.ASK:
                match order_type:
                    case OrderType.MARKET:
                        ready_order = self._execute_market_ask(ob)
                        mm.match_market_ask(ob, ready_order)
                    case OrderType.LIMIT:
                        ready_order = self._execute_limit_ask(ob)
                        mm.match_limit_ask(ob, ready_order)
                    case _:
                        pass

            case OrderAction.CANCEL:
                self._execute_cancel(ob)

            case OrderAction.HOLD:
                self._execute_hold(ob)

            case _:
                log.error(f'INVALID ACTION VALUE @ NoiseAgent.act(ob): {action}')