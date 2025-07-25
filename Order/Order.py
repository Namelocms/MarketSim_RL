from Order.OrderStatus import OrderStatus
from Order.OrderAction import OrderAction
from Order.OrderType import OrderType
from time import time
import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger(__name__)

class Order:
    ''' Hold all information for one order '''
    def __init__(self, id: str, agent_id: str, price: float, volume: int, side: OrderAction, type: OrderType, reserved_shares: list[tuple[float, int]] = []):
        self.id = id
        self.agent_id = agent_id
        self.price = price
        self.volume = volume
        self.entry_volume = volume
        self.timestamp = time()
        self.status = OrderStatus.OPEN
        self.side = side
        self.type = type
        self.reserved_shares = reserved_shares

    def get_returnable_shares(self):
        returnable_shares = []
        remaining_volume = self.volume
        # Sort reserved_shares by price ascending
        sorted_reserved = sorted(self.reserved_shares, key=lambda x: x[0])
        for price, vol in sorted_reserved:
            if remaining_volume == 0:
                break
            use_vol = min(vol, remaining_volume)
            if use_vol > 0:
                returnable_shares.append((price, use_vol))
                remaining_volume -= use_vol
        return returnable_shares

    def info(self):
        return f"""
            ID: {self.id}
            AGENT_ID: {self.agent_id}
            PRICE: {self.price}
            VOLUME: {self.volume}
            ENTRY_VOLUME: {self.entry_volume}
            TIMESTAMP: {self.timestamp}
            STATUS: {self.status}
            SIDE: {self.side}
            TYPE: {self.type}
            RESERVED_SHARES: {self.reserved_shares}
        """