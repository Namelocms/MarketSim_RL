from Order.OrderStatus import OrderStatus
from Order.OrderAction import OrderAction
from Order.OrderType import OrderType
from time import time
import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger(__name__)

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

    def info(self):
        return f"""
            ID: {self.id}
            AGENT_ID: {self.agent_id}
            PRICE: {self.price}
            VOLUME: {self.volume}
            TIMESTAMP: {self.timestamp}
            STATUS: {self.status}
            SIDE: {self.side}
            TYPE: {self.type}
        """