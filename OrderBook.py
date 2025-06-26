from queue import PriorityQueue
import logging as log

from Order.OrderAction import OrderAction

class OrderBook:
    '''
    Holds information for active ask and bid orders
    - bid_queue -> (-price, volume) [negated price so best bid is highest priority]
    - ask_queue -> (price, volume)
    '''
    def __init__(self):
        self.bid_queue = PriorityQueue()
        self.ask_queue = PriorityQueue()
        
    def get_best(self, side):
        ''' Get the best active bid/ask limit order and remove it from the queue '''
        match side:
            case OrderAction.BID:
                try:
                    best = self.bid_queue.get_nowait()
                    return (-best[0], best[1])  # negate price to positive value
                except Exception as e:
                    log.error(f'BID QUEUE IS EMPTY! RETURNING EMPTY TUPLE FROM OrderBook.get_best(side)! {e}')
                    return ()
            case OrderAction.ASK:
                try:
                    return self.ask_queue.get_nowait()
                except Exception as e:
                    log.error(f'ASK QUEUE IS EMPTY! RETURNING EMPTY TUPLE FROM OrderBook.get_best(side)! {e}')
                    return ()
            case _:
                log.error(f'INVALID SIDE VALUE @ OrderBook.get_best(side): {side.name}')
                return ()

    def peek_best(self, side):
        ''' Get the best active bid/ask limit order without removing it from the queue
        \nReturn:
        - (price, volume)
        - () - Empty tuple if no best or error occured
        '''
        best = self.get_best(side)
        if best != ():
            self.add_to_queue(side, best)  # requeue
        return best

    def add_order(self, order):
        ''' Add a new order to the bid/ask queue and orderbook '''
        pass

    def cancel_order(self, order_id):
        ''' Remove an order from the bid/ask queue and update the status to canceled'''
        pass

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

    def add_to_queue(self, side, info_tuple):
        ''' Add an order tuple into the bid/ask queue '''
        match side:
            case OrderAction.BID:
                try:
                    adjusted = (-info_tuple[0], info_tuple[1])  # negate the price so it is negative
                    self.bid_queue.put_nowait(adjusted)
                except Exception as e:
                    log.error(f'BID QUEUE IS FULL! @ OrderBook.add_to_queue(side, info_tuple)! {e}')
            case OrderAction.ASK:
                try:
                    self.ask_queue.put_nowait(info_tuple)
                except Exception as e:
                    log.error(f'ASK QUEUE IS FULL! @ OrderBook.add_to_queue(side, info_tuple)! {e}')
            case _:
                log.error(f'INVALID SIDE VALUE @ OrderBook.add_to_queue(side, info_tuple): {side.name}')
                