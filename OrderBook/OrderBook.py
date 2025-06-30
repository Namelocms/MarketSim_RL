from queue import PriorityQueue
from multiprocessing import Manager
from time import time
import logging
# Configure logging
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
    - bid_queue -> (-price, time, volume, id) [negated price so best bid is highest priority]
    - ask_queue -> (price, time, volume, id)
    - order_history -> {order_id: order}
    - agents -> {agent_id: agent}
    '''
    # Order/Agent ID info
    next_order_num = 1
    next_agent_num = 1
    MAX_ID_DIGITS = 12

    # Ticker Symbol
    SYMBOL_ID = 'COIN'

    # PriorityQueue.get() function timeout(seconds) so there is no freezing when queue is empty
    TIMEOUT = 0.1
    
    def __init__(self):
        self.manager = Manager()
        self.bid_queue = PriorityQueue()
        self.ask_queue = PriorityQueue()
        self.order_history = self.manager.dict()
        self.agents = self.manager.dict()

    def get_id(self, id_type):
        new_id = ''
        match id_type:
            case "ORDER":
                new_id += 'O-'
                char_num = len(str(self.next_order_num))
                remaining_chars = self.MAX_ID_DIGITS - char_num
                new_id += '0' * remaining_chars
                new_id += str(self.next_order_num)
                self.next_order_num += 1
                return new_id

            case "AGENT":
                new_id += 'A-'
                char_num = len(str(self.next_agent_num))
                remaining_chars = self.MAX_ID_DIGITS - char_num
                new_id += '0' * remaining_chars
                new_id += str(self.next_agent_num)
                self.next_agent_num += 1
                return new_id
            
            case _:
                log.error(f'INVALID ID TYPE @ OrderBook.get_id(id_type): {id_type}')
                return new_id
            
    def add_agent(self, agent: Agent):
        self.agents[agent.id] = agent
        
    def get_best(self, side: OrderAction):
        ''' Get the best active bid/ask limit order and remove it from the queue 
        \nReturn:
        - (price, time, volume, order_id)
        - () - Empty tuple if no best or error occured
        '''
        match side:
            case OrderAction.BID:
                try:
                    best = self.bid_queue.get(timeout=self.TIMEOUT)
                    return (-best[0], best[1], best[2], best[3])  # negate price to positive value
                except Exception as e:
                    log.error(f'BID QUEUE IS EMPTY! RETURNING EMPTY TUPLE FROM OrderBook.get_best(side)! {e}')
                    return ()
            case OrderAction.ASK:
                try:
                    return self.ask_queue.get(timeout=self.TIMEOUT)
                except Exception as e:
                    log.error(f'ASK QUEUE IS EMPTY! RETURNING EMPTY TUPLE FROM OrderBook.get_best(side)! {e}')
                    return ()
            case _:
                log.error(f'INVALID SIDE VALUE @ OrderBook.get_best(side): {side}')
                return ()

    def peek_best(self, side: OrderAction, n=1):
        ''' Get the best n active bid/ask limit order without removing it from the queue
        \nReturn:
        - [(price, time, volume, order_id), ...]
        - [] - Empty array if no best or error occured
        '''
        best_n = []
        for x in range(n):
            best = self.get_best(side)
            if best != ():
                best_n.append(best)
            else:  # queue is empty
                break

        for order in best_n:
            self._add_to_queue(side, order)  # requeue

        return best_n

    def _add_to_queue(self, side: OrderAction, info_tuple: tuple):
        ''' Add an order tuple into the bid/ask queue '''
        match side:
            case OrderAction.BID:
                try:
                    adjusted = (-info_tuple[0], info_tuple[1], info_tuple[2], info_tuple[3])  # negate the price so it is negative
                    self.bid_queue.put(adjusted)
                except Exception as e:
                    log.error(f'BID QUEUE IS FULL! @ OrderBook._add_to_queue(side, info_tuple)! {e}')
            case OrderAction.ASK:
                try:
                    self.ask_queue.put(info_tuple)
                except Exception as e:
                    log.error(f'ASK QUEUE IS FULL! @ OrderBook._add_to_queue(side, info_tuple)! {e}')
            case _:
                log.error(f'INVALID SIDE VALUE @ OrderBook._add_to_queue(side, info_tuple): {side}')

    def add_order(self, order: Order):
        ''' Add a new order to the bid/ask queue and orderbook '''
        self.order_history[order.id] = order
        info_tuple = (order.price, order.timestamp, order.volume, order.id)
        self._add_to_queue(order.side, info_tuple)

    def _remove_from_queue(self, side: OrderAction, order_id):
        ''' Remove an order tuple from the bid/ask queue '''
        requeue = []
        match side:
            case OrderAction.BID:
                # Iterate through each order in the queue until matching order_id found
                while not self.bid_queue.empty():
                    o = self.get_best(side)
                    if o[3] == order_id:
                        log.info(f'Order removed from bid_queue: {o}')
                        del o
                        break
                    else:
                        requeue.append(o) 
                # Requeue all orders without matching order_id
                for item in requeue:
                    self._add_to_queue(side, item)
            case OrderAction.ASK:
                while not self.ask_queue.empty():
                    o = self.get_best(side)
                    if o[3] == order_id:
                        log.info(f'Order removed from ask_queue: {o}')
                        del o
                        break
                    else:
                        requeue.append(o)
                for item in requeue:
                    self._add_to_queue(side, item)
            case _:
                log.error(f'INVALID SIDE VALUE @ OrderBook._remove_from_queue(side, info_tuple, order_id): {side.name}')

    def _return_assets(self, order: Order):
        ''' Return an agent's assets to them after an order is canceled '''
        agent: Agent = self.agents[order.agent_id]
        match order.side:
            case OrderAction.BID:
                agent.update_cash(order.price * order.volume)
                self.agents[agent.id] = agent
            case OrderAction.ASK:
                agent.update_holdings(order.price, order.volume)
                self.agents[agent.id] = agent  # reassign agent to push changes into multiprocessing dict
            case _:
                log.error(f'INVALID SIDE VALUE @ OrderBook._return_assets(order): {order.side.name}')

    def cancel_order(self, order_id: str):
        ''' Remove an order from the bid/ask queue, update the status to canceled, return assets if applicable'''
        order = self.order_history[order_id]
        order.status = OrderStatus.CANCELED
        self.order_history[order.id] = order  # reassign order to update multiporcessing dict
        self._remove_from_queue(order.side, order.id)
        self._return_assets(order)

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
                
    def match_order(self, order: Order):
        ''' Match the order to active order(s) in the Order Book
        - might want this to be a seperate class?
        '''
        # TODO
        pass