from copy import copy
from heapdict import heapdict
from heapq import nsmallest
from time import time
import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger(__name__)

from Order.OrderAction import OrderAction
from Order.OrderStatus import OrderStatus
from Order.Order import Order
from Agent.Agent import Agent


class OrderBook:
    '''
    Holds information for active ask and bid orders
    - manager -> Multiproccessing manager for concurrency
    - current_price -> Last sale price
    - bid_queue -> [order_id] = (-price, time, volume, order_id) [negated price so best bid is highest priority]
    - ask_queue -> [order_id] = (price, time, volume, order_id)
    - order_history -> {order_id: order}
    - agents -> {agent_id: agent}
    '''
    # Order/Agent ID info
    next_order_num = 1
    next_agent_num = 1
    MAX_ID_DIGITS = 12

    # Ticker Symbol
    SYMBOL_ID = 'COIN'

    # Singleton Instance
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, initial_price=1.00):
        if not hasattr(self, '_initialized'):
            self.current_price = initial_price
            self.bid_queue = heapdict()
            self.ask_queue = heapdict()
            self.order_history: dict[str, Order] = {}
            self.agents: dict[str, Agent] = {}

    def reset(self, initial_price=1.00):
        ''' Resets the orderbook to its initial state '''
        self.current_price = initial_price
        self.bid_queue.clear()
        self.ask_queue.clear()
        self.order_history.clear()

    def get_id(self, id_type):
        ''' Returns a unique incremented id for id_types: "ORDER" or "AGENT" '''
        new_id = ''
        match id_type:
            case "ORDER":
                new_id += 'O-'
                char_num = len(str(self.next_order_num))
                remaining_chars = self.MAX_ID_DIGITS - char_num
                new_id += '0' * remaining_chars
                new_id += str(self.next_order_num)
                self.next_order_num += 1

            case "AGENT":
                new_id += 'A-'
                char_num = len(str(self.next_agent_num))
                remaining_chars = self.MAX_ID_DIGITS - char_num
                new_id += '0' * remaining_chars
                new_id += str(self.next_agent_num)
                self.next_agent_num += 1
            
            case _:
                log.error(f'INVALID ID TYPE @ OrderBook.get_id(id_type): {id_type}')
        return new_id
            
    def upsert_agent(self, agent: Agent):
        ''' Add or update an agent in the agents dictionary '''
        self.agents[agent.id] = agent
    
    def get_agent_by_id(self, agent_id: str):
        ''' Returns an agent obj with matching agent_id '''
        return self.agents[agent_id]
        
    def get_best(self, side: OrderAction):
        ''' Get the best active bid/ask limit order and remove it from the queue 
        \nReturn:
        - (price, time, volume, order_id)
        - () - Empty tuple if no best or error occured
        '''
        best = ()
        match side:
            case OrderAction.BID:
                try:
                    id, _best = self.bid_queue.popitem()
                    best = (-_best[0], _best[1], _best[2], _best[3])  # negate price to positive value, append id for lookups
                except KeyError as e:
                    log.error(f'BID QUEUE IS EMPTY! RETURNING EMPTY TUPLE FROM OrderBook.get_best(BID)! {e}')
            case OrderAction.ASK:
                try:
                    id, best = self.ask_queue.popitem()
                except KeyError as e:
                    log.error(f'ASK QUEUE IS EMPTY! RETURNING EMPTY TUPLE FROM OrderBook.get_best(ASK)! {e}')
            case _:
                log.error(f'INVALID SIDE VALUE @ OrderBook.get_best(side): {side}')
        return best

    def peek_best(self, side: OrderAction, n=1):
        ''' Get the best n active bid/ask limit order without removing it from the queue
        \nReturn:
        - [(price, time, volume, order_id), ...]
        - [] - Empty array if no best or error occured
        '''
        best_n = []
        match side:
            case OrderAction.BID:
                best_n = [(-i[0], *i[1:]) for k, i in nsmallest(n, list(self.bid_queue.items()))]
            case OrderAction.ASK:
                best_n = [i for k, i in nsmallest(n, list(self.ask_queue.items()))]
            case _:
                log.error(f'INVALID SIDE VALUE @ OrderBook.get_best(side): {side}')

        return best_n

    def _add_to_queue(self, order: Order):
        ''' Add an order tuple into the bid/ask queue '''
        match order.side:
            case OrderAction.BID:
                try:
                    self.bid_queue[order.id] = (-order.price, order.timestamp, order.volume, order.id)  # put best bid price at top (highest price)
                except Exception as e:
                    log.error(f'Exception Occured @ OrderBook._add_to_queue(BID, info_tuple)! {e}')
            case OrderAction.ASK:
                try:
                    self.ask_queue[order.id] = (order.price, order.timestamp, order.volume, order.id)
                except Exception as e:
                    log.error(f'Exception Occured @ OrderBook._add_to_queue(ASK, info_tuple)! {e}')
            case _:
                log.error(f'INVALID SIDE VALUE @ OrderBook._add_to_queue(side, info_tuple): {order.side}')

    def add_order(self, order: Order):
        ''' Add a new order to the bid/ask queue and orderbook '''
        self.order_history[order.id] = order
        self._add_to_queue(order)

    def _remove_from_queue(self, side: OrderAction, order_id):
        ''' Remove an order tuple from the bid/ask queue '''
        match side:
            case OrderAction.BID:
                try:
                    del self.bid_queue[order_id]
                except KeyError:
                    pass#log.error(f'INVALID KEY VALUE (Order ID does not exist to remove!): {order_id}')
            case OrderAction.ASK:
                try:
                    del self.ask_queue[order_id]
                except KeyError:
                    pass#log.error(f'INVALID KEY VALUE (Order ID does not exist to remove!): {order_id}')
            case _:
                log.error(f'INVALID SIDE VALUE @ OrderBook._remove_from_queue(side, info_tuple, order_id): {side}')

    def _return_assets(self, order: Order, agent: Agent):
        ''' Return an agent's assets to them after an order is canceled '''
        match order.side:
            case OrderAction.BID:
                agent.update_cash(order.price * order.volume)
                del agent.active_bids[order.id]
                agent.history[order.id] = order
                self.upsert_agent(agent)
            case OrderAction.ASK:
                returnable_shares = order.get_returnable_shares()
                for price, volume in returnable_shares:
                    agent.update_holdings(price, volume)
                del agent.active_asks[order.id]
                agent.history[order.id] = order
                self.upsert_agent(agent)
            case _:
                log.error(f'INVALID SIDE VALUE @ OrderBook._return_assets(order): {order.side}')

    def cancel_order(self, order_id: str, agent: Agent):
        ''' Remove an order from the bid/ask queue, update the status to canceled, return assets if applicable'''
        order = self.order_history[order_id]
        order.status = OrderStatus.CANCELED
        self.order_history[order.id] = order
        self._remove_from_queue(order.side, order.id)
        self._return_assets(order, agent)

    def fill_order(self, order: Order):
        ''' Order was filled, remove from queue, update status to CLOSED '''
        order.status = OrderStatus.CLOSED
        order.volume = 0
        self.order_history[order.id] = order

    def partial_fill_order(self, order: Order, vol_filled: int):
        ''' Order was partially filled, update volume, re-add it to queue '''
        order.volume -= vol_filled
        self.add_order(order)

    def _find_order_in_queue(self, order_id) -> tuple:
        ''' Get the Order Info tuple with matching order_id\n
        Returns: (price, time, volume, order_id)
        '''
        order: Order = self.order_history[order_id]
        matched = ()

        match order.side:
            case OrderAction.BID:
                try:
                    matched = self.ask_queue[order_id]
                except KeyError:
                    log.error(f'INVALID KEY VALUE (Order ID does not exist to find!): {order_id}')
            case OrderAction.ASK:
                try:
                    matched = self.ask_queue[order_id]
                except KeyError:
                    log.error(f'INVALID KEY VALUE (Order ID does not exist to find!): {order_id}')
            case _:
                log.error(f'INVALID SIDE VALUE @ OrderBook._remove_from_queue(side, info_tuple, order_id): {order.side}')
        return matched

    def get_snapshot(self, depth=10):
        '''
        Get a snapshot of the current state of the Order Book\n
        Like this:\n
        ```ob_snapshot = 
        [
            {
                "symbol_id": "BITSTAMP_SPOT_BTC_USD",
                "time_exchange": "2013-09-28T22:40:50.0000000Z",
                "time_coinapi": "2017-03-18T22:42:21.3763342Z",
                "current_price": 1.00,
                "asks": [
                {
                    "price": 456.35,
                    "size": 123
                },
                {
                    "price": 456.36,
                    "size": 23
                }
                ],
                "bids": [
                {
                    "price": 456.1,
                    "size": 42
                },
                {
                    "price": 456.09,
                    "size": 5
                }
                ]
            }
        ]
        '''
        ob_snapshot = [
            {
                'symbol_id': self.SYMBOL_ID,
                'time_exchange': time(),
                'time_coinapi': time(),
                'current_price': self.current_price,
                'asks': [],
                'bids': []
            }
        ]
        
        # Peek best n orders in ask and bid
        asks = self.peek_best(OrderAction.ASK, n=depth)
        bids = self.peek_best(OrderAction.BID, n=depth)

        # Add order info to snapshot
        for order in asks:
            ob_snapshot[0]['asks'].append(
                {
                    'price': order[0],
                    'size': order[2]
                }
            )
        for order in bids:
            ob_snapshot[0]['bids'].append(
                {
                    'price': order[0],
                    'size': order[2]
                }
            )

        return ob_snapshot
                