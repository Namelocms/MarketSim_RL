from Agent.Agent import Agent
from OrderBook.OrderBook import OrderBook
from Order.Order import Order
from Order.OrderAction import OrderAction
from Order.OrderType import OrderType

class TakerAgent(Agent):
    ''' Agent only makes Market Orders '''

    def make_market_bid(self, ob: OrderBook, volume):
        ''' Buy at current price and desired volume '''
        mb_order = Order(
            id=         ob.get_id('ORDER'), 
            agent_id=   self.id, 
            price=      -1,
            volume=     volume, 
            side=       OrderAction.BID,
            type=       OrderType.MARKET
        )

        self.history[mb_order.id] = mb_order
        ob.upsert_agent(self)
        
        return mb_order
    
    def make_market_ask(self, ob: OrderBook, volume):
        removed_shares = self.remove_holdings(volume)

        ma_order = Order(
            id=             ob.get_id('ORDER'), 
            agent_id=       self.id, 
            price=          -1, 
            volume=         volume, 
            side=           OrderAction.ASK,
            type=           OrderType.MARKET,
            reserved_shares= removed_shares
        )
        
        self.history[ma_order.id] = ma_order
        ob.upsert_agent(self)
        
        return ma_order