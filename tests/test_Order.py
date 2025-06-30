import unittest
from time import time
from Order.Order import Order
from Order.OrderAction import OrderAction
from Order.OrderStatus import OrderStatus

class TestOrder(unittest.TestCase):
    def test_order_init_ask(self):
        TIME = time()
        ORDER = Order(1, 1, 1.00, 10, OrderAction.ASK)
        self.assertEqual(ORDER.id, 1)
        self.assertEqual(ORDER.agent_id, 1)
        self.assertEqual(ORDER.price, 1.00)
        self.assertEqual(ORDER.volume, 10)
        self.assertAlmostEqual(ORDER.timestamp, TIME)
        self.assertEqual(ORDER.status, OrderStatus.OPEN)
        self.assertEqual(ORDER.side, OrderAction.ASK)

    def test_order_init_bid(self):
        TIME = time()
        ORDER = Order(1, 1, 1.00, 10, OrderAction.BID)
        self.assertEqual(ORDER.id, 1)
        self.assertEqual(ORDER.agent_id, 1)
        self.assertEqual(ORDER.price, 1.00)
        self.assertEqual(ORDER.volume, 10)
        self.assertAlmostEqual(ORDER.timestamp, TIME)
        self.assertEqual(ORDER.status, OrderStatus.OPEN)
        self.assertEqual(ORDER.side, OrderAction.BID)