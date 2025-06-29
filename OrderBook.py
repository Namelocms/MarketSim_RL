from queue import PriorityQueue
import logging as log

from Order.OrderAction import OrderAction
from Order.OrderStatus import OrderStatus

''' TODO

- Orders sorted 1st by price, 2nd by time placed (FIFO)
    - Need to figure out a way to sort this simply, probably need to redo a bunch of functions to match this 
        queue.put((order.price, order.time, order.vol, order.id))

'''

class OrderBook:
    '''
    Holds information for active ask and bid orders
    - bid_queue -> (-price, time, volume, id) [negated price so best bid is highest priority]
    - ask_queue -> (price, time, volume, id)
    - order_history -> {order_id: order}
    - agents -> {agent_id: agent}
    '''
    def __init__(self):
        self.bid_queue = PriorityQueue()
        self.ask_queue = PriorityQueue()
        self.order_history = {}
        self.agents = {}
        
    def get_best(self, side):
        ''' Get the best active bid/ask limit order and remove it from the queue 
        \nReturn:
        - (price, time, volume, order_id)
        - () - Empty tuple if no best or error occured
        '''
        match side:
            case OrderAction.BID:
                try:
                    best = self.bid_queue.get()
                    return (-best[0], best[1], best[2], best[3])  # negate price to positive value
                except Exception as e:
                    log.error(f'BID QUEUE IS EMPTY! RETURNING EMPTY TUPLE FROM OrderBook.get_best(side)! {e}')
                    return ()
            case OrderAction.ASK:
                try:
                    return self.ask_queue.get()
                except Exception as e:
                    log.error(f'ASK QUEUE IS EMPTY! RETURNING EMPTY TUPLE FROM OrderBook.get_best(side)! {e}')
                    return ()
            case _:
                log.error(f'INVALID SIDE VALUE @ OrderBook.get_best(side): {side.name}')
                return ()

    def peek_best(self, side):
        ''' Get the best active bid/ask limit order without removing it from the queue
        \nReturn:
        - (price, time, volume, order_id)
        - () - Empty tuple if no best or error occured
        '''
        best = self.get_best(side)
        if best != ():
            self._add_to_queue(side, best)  # requeue
        return best

    def _add_to_queue(self, side, info_tuple):
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
                log.error(f'INVALID SIDE VALUE @ OrderBook._add_to_queue(side, info_tuple): {side.name}')

    def add_order(self, order):
        ''' Add a new order to the bid/ask queue and orderbook '''
        self.order_history[order.id] = order
        info_tuple = (order.price, order.timestamp, order.volume, order.id)
        self._add_to_queue(order.side, info_tuple)

    def _remove_from_queue(self, side, order_id):
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

    def _return_assets(self, order):
        ''' Return an agent's assets to them after an order is canceled '''
        agent = self.agents[order.agent_id]
        match order.side:
            case OrderAction.BID:
                agent.cash += (order.price * order.volume)
            case OrderAction.ASK:
                # TODO: need to finish agent first for object structure info
                pass
            case _:
                log.error(f'INVALID SIDE VALUE @ OrderBook._return_assets(order): {order.side.name}')

    def cancel_order(self, order_id):
        ''' Remove an order from the bid/ask queue, update the status to canceled, return assets if applicable'''
        order = self.order_history[order_id]
        order.status = OrderStatus.CANCELED
        self._remove_from_queue(order.side, order.id)
        self._return_assets(order)

    def match_order(self, order):
        ''' Match the order to active order(s) in the Order Book
        - might want this to be a seperate class?
        '''
        pass

    def get_snapshot(self, depth=5):
        '''
        Get a snapshot of the current state of the Order Book\n
        Something like this:\n
        ```observation = {
            "bid_prices": [100.30, 100.29, ..., 100.21],   # top N levels
            "bid_sizes": [500, 300, ..., 50],
            "ask_prices": [100.31, 100.32, ..., 100.40],
            "ask_sizes": [600, 250, ..., 70],
            "last_price": 100.305,
            "inventory": 120,
            "cash": 9200,
            "recent_trades": [...],  # (optional)
            "time": t,               # (optional)
        }
        '''
        pass
                