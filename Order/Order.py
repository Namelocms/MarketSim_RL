from Order.OrderStatus import OrderStatus
from Order.OrderAction import OrderAction
from Order.OrderType import OrderType
from time import time

class Order:
    ''' Hold all information for one order '''
    def __init__(self, id: str, agent_id: str, price: float, volume: int, side: OrderAction, type: OrderType):
        self.id = id
        self.agent_id = agent_id
        self.price = price
        self.volume = volume
        self.timestamp = time()
        self.status = OrderStatus.OPEN
        self.side = side
        self.type = type