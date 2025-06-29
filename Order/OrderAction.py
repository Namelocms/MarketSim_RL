from enum import Enum

class OrderAction(Enum):
    BID = 0
    ASK = 1
    HOLD = 2
    CANCEL = 3
