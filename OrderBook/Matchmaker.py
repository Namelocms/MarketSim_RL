from OrderBook.OrderBook import OrderBook
from Agent.Agent import Agent
from Order.Order import Order
from Order.OrderAction import OrderAction
from Order.OrderStatus import OrderStatus
from Util.Util import Util
import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger(__name__)

class MatchMaker:
    def _get_affordable_vol(self, target_price, acting_agent_cash):
        return int(acting_agent_cash / target_price)

    def match_market_bid(self, ob: OrderBook, order: Order):
        assert(order.side is OrderAction.BID)

        ba: Agent = ob.agents[order.agent_id]

        while order.volume > 0 and not ob.ask_queue.empty():
            # Prevent agent from trading with itself
            if ob.peek_best(OrderAction.ASK)[0][3] == ba.id: continue

            best_ask = ob.get_best(OrderAction.ASK)
            if not best_ask:
                log.error('BEST ASK IS EMPTY! @ MatchMaker.match_market_bid()')
                break

            best_ask_price = best_ask[0]
            best_ask_time = best_ask[1]
            best_ask_volume = best_ask[2]
            best_ask_oid = best_ask[3]

            aa_id = ob.order_history[best_ask_oid].agent_id
            aa: Agent = ob.agents[aa_id]
            aa_order: Order = aa.history[best_ask_oid]

            affordable_volume = min(order.volume, self._get_affordable_vol(best_ask_price, ba.cash))

            if affordable_volume <= 0:
                continue  # Agent cannot afford anything at current ask price

            if aa_order.volume <= affordable_volume:
                total_value = round(aa_order.volume * aa_order.price, Util.ROUND_NDIGITS)

                aa.update_cash(total_value)
                aa.remove_active_ask(aa_order.id)
                aa_order.status = OrderStatus.CLOSED
                aa.history[aa_order.id] = aa_order

                ba.update_holdings(aa_order.price, aa_order.volume)
                ba.update_cash(-total_value)

                order.volume = round(order.volume - aa_order.volume, Util.ROUND_NDIGITS)

                ob.fill_order(aa_order)
                ob.current_price = aa_order.price

            else:
                total_value = round(affordable_volume * aa_order.price, Util.ROUND_NDIGITS)

                aa.update_cash(total_value)
                aa.upsert_active_ask(aa_order)

                ba.update_holdings(aa_order.price, affordable_volume)
                ba.update_cash(-total_value)

                ob.partial_fill_order(aa_order, affordable_volume)
                ob.current_price = aa_order.price

                order.volume = 0

            ob.upsert_agent(ba)
            ob.upsert_agent(aa)

        # Final status update
        if order.volume > 0:
            order.status = OrderStatus.CANCELED
        else:
            order.status = OrderStatus.CLOSED

        ba.history[order.id] = order
        ob.upsert_agent(ba)


    #def match_market_bid(self, ob: OrderBook, order: Order):
    #    assert(order.side is OrderAction.BID)
    #    # Bidding agent
    #    ba: Agent = ob.agents[order.agent_id]
#
    #    # Match until there are no more matches available or order volume is depleted
    #    while order.volume > 0 and not ob.ask_queue.empty():
    #        # Prevent agent trading with itself
    #        if ob.peek_best(OrderAction.ASK)[0][3] == ba.id: print('skipping');continue
    #            
    #        best_ask = ob.get_best(OrderAction.ASK)
    #        if not best_ask: 
    #            log.error('BEST ASK IS EMPTY! @ MatchMaker.match_market_bid()')
    #            break
#
    #        best_ask_price = best_ask[0]
    #        best_ask_time = best_ask[1]
    #        best_ask_volume = best_ask[2]
    #        best_ask_oid = best_ask[3]
#
    #        # Asking agent
    #        aa_id = ob.order_history[best_ask_oid].agent_id
    #        aa: Agent = ob.agents[aa_id]
    #        aa_order: Order = aa.history[best_ask_oid]
#
    #        if aa_order.volume <= order.volume:
    #            aa_order_total_value = round(aa_order.volume * aa_order.price, Util.ROUND_NDIGITS)
    #            aa.update_cash(aa_order_total_value)
    #            aa.remove_active_ask(aa_order.id)
    #            aa_order.status = OrderStatus.CLOSED
    #            aa.history[aa_order.id] = aa_order
#
    #            ba.update_holdings(aa_order.price, aa_order.volume)
    #            ba.update_cash(-aa_order_total_value)
#
    #            order.volume = round(order.volume - aa_order.volume, Util.ROUND_NDIGITS)
#
    #            ob.fill_order(aa_order)
    #            ob.current_price = aa_order.price
    #            ob.upsert_agent(ba)
    #            ob.upsert_agent(aa)
 #
    #        else:
    #            order_total_value = round(order.volume * aa_order.price, Util.ROUND_NDIGITS)
    #            aa.update_cash(order_total_value)
    #            aa.upsert_active_ask(aa_order)
    #            
    #            ba.update_holdings(aa_order.price, order.volume)
    #            ba.update_cash(-order_total_value)
    #            order.status = OrderStatus.CLOSED
    #            ba.history[order.id] = order
    #            
    #            ob.partial_fill_order(aa_order, order.volume)
    #            ob.current_price = aa_order.price
    #            ob.upsert_agent(ba)
    #            ob.upsert_agent(aa)
#
    #            order.volume = 0
    #            
    #    if order.volume > 0:
    #        order.status = OrderStatus.CANCELED
    #    else:
    #        order.status = OrderStatus.CLOSED
    #    
    #    ba.history[order.id] = order
    #    ob.upsert_agent(ba)

    def match_limit_bid(self, ob: OrderBook, order: Order):
        assert(order.side is OrderAction.BID)
        # Bidding agent
        ba: Agent = ob.agents[order.agent_id]
        
        while not ob.ask_queue.empty() and ob.peek_best(OrderAction.ASK)[0][0] <= order.price and order.volume > 0:
            # Prevent agent trading with itself
            if ob.peek_best(OrderAction.ASK)[0][3] == ba.id: continue

            best_ask = ob.get_best(OrderAction.ASK)
            if not best_ask: 
                log.error('BEST ASK IS EMPTY! @ MatchMaker.match_limit_bid()')
                break

            best_ask_price = best_ask[0]
            best_ask_time = best_ask[1]
            best_ask_volume = best_ask[2]
            best_ask_oid = best_ask[3]

            # Asking agent
            aa_id = ob.order_history[best_ask_oid].agent_id
            aa: Agent = ob.agents[aa_id]
            aa_order: Order = aa.history[best_ask_oid]

            if aa_order.volume <= order.volume:
                aa_order_total_value = round(aa_order.volume * aa_order.price, Util.ROUND_NDIGITS)
                aa.update_cash(aa_order_total_value)
                aa.remove_active_ask(aa_order.id)
                aa_order.status = OrderStatus.CLOSED
                aa.history[aa_order.id] = aa_order

                ba.update_holdings(aa_order.price, aa_order.volume)

                order.volume = round(order.volume - aa_order.volume, Util.ROUND_NDIGITS)

                ob.fill_order(aa_order)
                ob.current_price = aa_order.price
                ob.upsert_agent(ba)
                ob.upsert_agent(aa)

            else:
                order_total_value = round(order.volume * aa_order.price, Util.ROUND_NDIGITS)
                aa.update_cash(order_total_value)
                aa.upsert_active_ask(aa_order)

                ba.update_holdings(aa_order.price, order.volume)
                order.status = OrderStatus.CLOSED
                ba.history[order.id] = order

                ob.partial_fill_order(aa_order, order.volume)
                ob.current_price = aa_order.price
                ob.upsert_agent(ba)
                ob.upsert_agent(aa)

                order.volume = 0

        if order.volume > 0:
            ba.history[order.id] = order
            ba.upsert_active_bid(order)
            ob.upsert_agent(ba)
            ob.add_order(order)
        else:
            order.status = OrderStatus.CLOSED
            ba.history[order.id] = order
            ob.upsert_agent(ba)

    def match_market_ask(self, ob: OrderBook, order: Order):
        assert(order.side is OrderAction.ASK)
        # Asking agent
        aa: Agent = ob.agents[order.agent_id]
        
        while order.volume > 0 and not ob.bid_queue.empty():
            # Prevent agent trading with itself
            if ob.peek_best(OrderAction.BID)[0][3] == aa.id: print('skipping');continue

            best_bid = ob.get_best(OrderAction.BID)
            if not best_bid: 
                log.error('BEST BID IS EMPTY! @ MatchMaker.match_market_ask()')
                break

            best_bid_price = best_bid[0]
            best_bid_time = best_bid[1]
            best_bid_volume = best_bid[2]
            best_bid_oid = best_bid[3]

            # Bidding agent
            ba_id = ob.order_history[best_bid_oid].agent_id
            ba: Agent = ob.agents[ba_id]
            ba_order: Order = ba.history[best_bid_oid]

            if ba_order.volume <= order.volume:
                ba_order_total_value = round(ba_order.volume * ba_order.price, Util.ROUND_NDIGITS)
                aa.update_cash(ba_order_total_value)
                
                ba.update_holdings(ba_order.price, ba_order.volume)
                ba.remove_active_bid(ba_order.id)
                ba_order.status = OrderStatus.CLOSED
                ba.history[ba_order.id] = ba_order

                order.volume = round(order.volume - ba_order.volume, Util.ROUND_NDIGITS)

                ob.fill_order(ba_order)
                ob.current_price = ba_order.price
                ob.upsert_agent(aa)
                ob.upsert_agent(ba)

            else:
                order_total_value = round(order.volume * ba_order.price, Util.ROUND_NDIGITS)
                aa.update_cash(order_total_value)

                ba.update_holdings(ba_order.price, order.volume)
                ba.history[ba_order.id] = ba_order

                ob.partial_fill_order(ba_order, order.volume)
                ob.current_price = ba_order.price
                ob.upsert_agent(ba)
                ob.upsert_agent(aa)

                order.volume = 0
        if order.volume > 0:
            order.status = OrderStatus.CANCELED
            for price, volume in order.get_returnable_shares():
                aa.update_holdings(price, volume)
        else:
            order.status = OrderStatus.CLOSED
        
        aa.history[order.id] = order
        ob.upsert_agent(aa)

    def match_limit_ask(self, ob: OrderBook, order: Order):
        assert(order.side is OrderAction.ASK)
        # Asking Agent
        aa: Agent = ob.agents[order.agent_id]

        while not ob.bid_queue.empty() and ob.peek_best(OrderAction.BID)[0][0] >= order.price and order.volume > 0:
            # Prevent agent trading with itself
            if ob.peek_best(OrderAction.BID)[0][3] == aa.id: print('skipping');continue

            best_bid = ob.get_best(OrderAction.BID)
            if not best_bid: 
                log.error('BEST BID IS EMPTY! @ MatchMaker.match_limit_ask()')
                break
            
            best_bid_price = best_bid[0]
            best_bid_time = best_bid[1]
            best_bid_volume = best_bid[2]
            best_bid_oid = best_bid[3]

            # Bidding Agent
            ba_id = ob.order_history[best_bid_oid].agent_id
            ba: Agent = ob.agents[ba_id]
            ba_order: Order = ba.history[best_bid_oid]

            if ba_order.volume <= order.volume:
                ba_order_total_value = round(ba_order.volume * ba_order.price, Util.ROUND_NDIGITS)
                aa.update_cash(ba_order_total_value)
                
                ba.update_holdings(ba_order.price, ba_order.volume)
                ba.remove_active_bid(ba_order.id)
                ba_order.status = OrderStatus.CLOSED
                ba.history[ba_order.id] = ba_order
                
                order.volume = round(order.volume - ba_order.volume, Util.ROUND_NDIGITS)
                
                ob.fill_order(ba_order)
                ob.current_price = ba_order.price
                ob.upsert_agent(aa)
                ob.upsert_agent(ba)

                
            else:
                order_total_value = round(order.volume * ba_order.price, Util.ROUND_NDIGITS)
                aa.update_cash(order_total_value)

                ba.update_holdings(ba_order.price, order.volume)
                ba.history[ba_order.id] = ba_order

                ob.partial_fill_order(ba_order, order.volume)
                ob.current_price = ba_order.price
                ob.upsert_agent(ba)
                ob.upsert_agent(aa)

                order.volume = 0
        if order.volume > 0:
            aa.history[order.id] = order
            aa.upsert_active_ask(order)
            ob.upsert_agent(aa)
            ob.add_order(order)
        else:
            order.status = OrderStatus.CLOSED
            aa.history[order.id] = order
            ob.upsert_agent(aa)