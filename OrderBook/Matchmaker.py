from OrderBook.OrderBook import OrderBook
from Agent.Agent import Agent
from Order.Order import Order
from Order.OrderAction import OrderAction
from Order.OrderStatus import OrderStatus
import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger(__name__)

def match_market_bid(ob: OrderBook, order: Order):
    # Bidding agent
    ba_id = order.agent_id
    ba: Agent = ob.agents[ba_id]

    while order.volume > 0 and ob.ask_queue.not_empty():
        best_ask = ob.get_best(OrderAction.ASK)
        if best_ask == (): 
            log.error('BEST ASK IS EMPTY! @ MatchMaker.match_market_bid()')
            pass

        best_ask_price = best_ask[0]
        best_ask_time = best_ask[1]
        best_ask_volume = best_ask[2]
        best_ask_oid = best_ask[3]

        # Asking agent
        aa_id = ob.order_history[best_ask_oid].agent_id
        aa: Agent = ob.agents[aa_id]
        aa_order: Order = aa.history[best_ask_oid]
        
        if aa_order.volume <= order.volume:
            aa.update_cash(aa_order.volume * aa_order.price)
            aa.remove_active_ask(aa_order.id)
            aa_order.status = OrderStatus.CLOSED
            aa.history[aa_order.id] = aa_order

            ob[aa_id] = aa
            ob.fill_order(aa_order.id)

            ba.update_holdings(aa_order.price, aa_order.volume)
            ba.update_cash(-aa_order.price * aa_order.volume)
            
            ob.upsert_agent(ba)
            ob.upsert_agent(aa)

            order.volume -= aa_order.volume
            
        elif aa_order.volume > order.volume:
            aa.update_cash(aa_order.price * order.volume)
            aa.upsert_active_ask(aa_order)

            ba.update_holdings(aa_order.price, order.volume)
            ba.update_cash(-aa_order.price * order.volume)
            order.status = OrderStatus.CLOSED
            ba.history[order.id] = order
            
            ob.partial_fill_order(aa_order, order.volume)
            ob.upsert_agent(ba)
            ob.upsert_agent(aa)

            order.volume = 0
            
    if order.volume > 0:
        order.status = OrderStatus.CANCELED
        ba.history[order.id] = order
        ob.upsert_agent(ba)

def match_limit_bid(ob: OrderBook, order: Order):
    # peek the best ask
    # if best ask is <= bid price
    # while there are asks <= bid price and order has volume
        # get best ask
        # subtract ask volume from bid 
        # add money to asking agent
        # subtract bid volume from ask
        # add holdings to bidding agent
        # peek best order to determine if next ask meets price threshold
    # if order still has volume
        # add order to ob.bid_queue
        # update order in agent's active bids
    pass

def match_market_ask(ob: OrderBook, order: Order):
    # while order has volume and there are bids remaining in ob.bid_queue
        # get best bid
        # subtract bid volume from ask
        # add money to asking agent
        # subtract ask volume from bid
        # add holdings to bidding agent
    # if order still has volume
        # cancel order and return holdings to asking agent
    pass

def match_limit_ask(ob: OrderBook, order: Order):
    # peek best bid
    # if best bid >= ask price
    # while there are bids >= ask price and order has volume
        # get best bid
        # subtract bid volume from ask 
        # add money to asking agent
        # subtract ask volume from bid
        # add holdings to bidding agent
        # peek best order to determine if next bid meets price threshold
    # if order still has volume
        # add order to ob.ask_queue
        # update order in agent's active asks
    pass