from Order.OrderStatus import OrderStatus

class Order:
    def __init__(self, id, agent_id, price, volume, timestamp, side):
        self.id = id
        self.agent_id = agent_id
        self.price = price
        self.volume = volume
        self.timestamp = timestamp
        self.status = OrderStatus.OPEN
        self.side = side