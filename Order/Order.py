from Order.OrderStatus import OrderStatus
from time import time

class Order:
    def __init__(self, id, agent_id, price, volume, side):
        self.id = id
        self.agent_id = agent_id
        self.price = price
        self.volume = volume
        self.timestamp = time()
        self.status = OrderStatus.OPEN
        self.side = side