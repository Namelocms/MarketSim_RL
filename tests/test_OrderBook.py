import unittest
from OrderBook.OrderBook import OrderBook
from Order.Order import Order
from Order.OrderAction import OrderAction
from Order.OrderStatus import OrderStatus
from Agent.Agent import Agent

class TestOrderBook(unittest.TestCase):

    def test_ob_init(self):
        ob = OrderBook()
        self.assertIsNotNone(ob.manager)
        self.assertIsNotNone(ob.bid_queue)
        self.assertIsNotNone(ob.ask_queue)
        self.assertIsNotNone(ob.order_history)
        self.assertIsNotNone(ob.agents)

    def test_get_id_agent(self):
        ob = OrderBook()
        id = ob.get_id('AGENT')
        id2 = ob.get_id('AGENT')
        self.assertEqual(id, 'A-000000000001')
        self.assertEqual(id2, 'A-000000000002')

    def test_get_id_order(self):
        ob = OrderBook()
        id = ob.get_id('ORDER')
        id2 = ob.get_id('ORDER')
        self.assertEqual(id, 'O-000000000001')
        self.assertEqual(id2, 'O-000000000002')

    def test_get_id_fail(self):
        ob = OrderBook()
        id = ob.get_id('TEST_FAIL')
        id2 = ob.get_id('TEST_FAIL')
        self.assertEqual(id, '')
        self.assertEqual(id2, '')

    def test_get_best_ask(self):
        ob = OrderBook()
        o1 = Order(1, 1, 1.00, 10, OrderAction.ASK)
        o2 = Order(2, 1, 1.10, 10, OrderAction.ASK)
        o3 = Order(3, 1, 0.90, 10, OrderAction.ASK)
        o4 = Order(4, 1, 1.00, 20, OrderAction.ASK)

        ob.ask_queue.put((o1.price, o1.timestamp, o1.volume, o1.id))
        ob.ask_queue.put((o2.price, o2.timestamp, o2.volume, o2.id))
        ob.ask_queue.put((o3.price, o3.timestamp, o3.volume, o3.id))
        ob.ask_queue.put((o4.price, o4.timestamp, o4.volume, o4.id))

        b1 = ob.get_best(OrderAction.ASK)
        b2 = ob.get_best(OrderAction.ASK)

        self.assertEqual(b1[0], 0.90)
        self.assertEqual(b1[2], 10)
        self.assertEqual(b2[0], 1.00)
        self.assertEqual(b2[2], 10)

    def test_get_best_bid(self):
        ob = OrderBook()
        o1 = Order(1, 1, 1.00, 10, OrderAction.BID)
        o2 = Order(2, 1, 1.10, 10, OrderAction.BID)
        o3 = Order(3, 1, 0.90, 10, OrderAction.BID)
        o4 = Order(4, 1, 1.00, 20, OrderAction.BID)

        ob.bid_queue.put((-o1.price, o1.timestamp, o1.volume, o1.id))
        ob.bid_queue.put((-o2.price, o2.timestamp, o2.volume, o2.id))
        ob.bid_queue.put((-o3.price, o3.timestamp, o3.volume, o3.id))
        ob.bid_queue.put((-o4.price, o4.timestamp, o4.volume, o4.id))

        b1 = ob.get_best(OrderAction.BID)
        b2 = ob.get_best(OrderAction.BID)

        self.assertEqual(b1[0], 1.10)
        self.assertEqual(b1[2], 10)
        self.assertEqual(b2[0], 1.00)
        self.assertEqual(b2[2], 10)

    def test_get_best_fail(self):
        ob = OrderBook()
        o1 = Order(1, 1, 1.00, 10, OrderAction.ASK)
        o2 = Order(2, 1, 1.10, 10, OrderAction.ASK)
        o3 = Order(3, 1, 0.90, 10, OrderAction.ASK)
        o4 = Order(4, 1, 1.00, 20, OrderAction.ASK)
        o5 = Order(5, 1, 1.00, 10, OrderAction.BID)
        o6 = Order(6, 1, 1.10, 10, OrderAction.BID)
        o7 = Order(7, 1, 0.90, 10, OrderAction.BID)
        o8 = Order(8, 1, 1.00, 20, OrderAction.BID)

        ob.ask_queue.put((o1.price, o1.timestamp, o1.volume, o1.id))
        ob.ask_queue.put((o2.price, o2.timestamp, o2.volume, o2.id))
        ob.ask_queue.put((o3.price, o3.timestamp, o3.volume, o3.id))
        ob.ask_queue.put((o4.price, o4.timestamp, o4.volume, o4.id))
        ob.bid_queue.put((o5.price, o5.timestamp, o5.volume, o5.id))
        ob.bid_queue.put((o6.price, o6.timestamp, o6.volume, o6.id))
        ob.bid_queue.put((o7.price, o7.timestamp, o7.volume, o7.id))
        ob.bid_queue.put((o8.price, o8.timestamp, o8.volume, o8.id))

        b1 = ob.get_best('ASK')
        b2 = ob.get_best(OrderAction.HOLD)
        b3 = ob.get_best('BID')
        b4 = ob.get_best(OrderAction.CANCEL)

        self.assertEqual(b1, ())
        self.assertEqual(b2, ())
        self.assertEqual(b3, ())
        self.assertEqual(b4, ())

    def test_peek_best_ask(self):
        ob = OrderBook()
        o1 = Order(1, 1, 1.00, 10, OrderAction.ASK)
        o2 = Order(2, 1, 1.10, 10, OrderAction.ASK)
        o3 = Order(3, 1, 0.90, 10, OrderAction.ASK)
        o4 = Order(4, 1, 1.00, 20, OrderAction.ASK)

        ob.ask_queue.put((o1.price, o1.timestamp, o1.volume, o1.id))
        ob.ask_queue.put((o2.price, o2.timestamp, o2.volume, o2.id))
        ob.ask_queue.put((o3.price, o3.timestamp, o3.volume, o3.id))
        ob.ask_queue.put((o4.price, o4.timestamp, o4.volume, o4.id))

        b1 = ob.peek_best(OrderAction.ASK)
        b2 = ob.peek_best(OrderAction.ASK, 2)

        self.assertEqual(b1[0], b2[0])
        self.assertEqual(b2[1], (o1.price, o1.timestamp, o1.volume, o1.id))

    def test_peek_best_bid(self):
        ob = OrderBook()
        o1 = Order(1, 1, 1.00, 10, OrderAction.BID)
        o2 = Order(2, 1, 1.10, 10, OrderAction.BID)
        o3 = Order(3, 1, 0.90, 10, OrderAction.BID)
        o4 = Order(4, 1, 1.00, 20, OrderAction.BID)

        ob.bid_queue.put((-o1.price, o1.timestamp, o1.volume, o1.id))
        ob.bid_queue.put((-o2.price, o2.timestamp, o2.volume, o2.id))
        ob.bid_queue.put((-o3.price, o3.timestamp, o3.volume, o3.id))
        ob.bid_queue.put((-o4.price, o4.timestamp, o4.volume, o4.id))

        b1 = ob.peek_best(OrderAction.BID)
        b2 = ob.peek_best(OrderAction.BID, 2)

        self.assertEqual(b1[0], b2[0])
        self.assertEqual(b2[1], (o1.price, o1.timestamp, o1.volume, o1.id))

    def test_peek_best_fail(self):
        ob = OrderBook()
        o1 = Order(1, 1, 1.00, 10, OrderAction.ASK)
        o2 = Order(2, 1, 1.10, 10, OrderAction.ASK)
        o3 = Order(3, 1, 0.90, 10, OrderAction.ASK)
        o4 = Order(4, 1, 1.00, 20, OrderAction.ASK)
        o5 = Order(5, 1, 1.00, 10, OrderAction.BID)
        o6 = Order(6, 1, 1.10, 10, OrderAction.BID)
        o7 = Order(7, 1, 0.90, 10, OrderAction.BID)
        o8 = Order(8, 1, 1.00, 20, OrderAction.BID)

        b0 = ob.peek_best(OrderAction.ASK)
        b00 = ob.peek_best(OrderAction.BID)

        self.assertEqual(b0, [])
        self.assertEqual(b00, [])

        ob.ask_queue.put((o1.price, o1.timestamp, o1.volume, o1.id))
        ob.ask_queue.put((o2.price, o2.timestamp, o2.volume, o2.id))
        ob.ask_queue.put((o3.price, o3.timestamp, o3.volume, o3.id))
        ob.ask_queue.put((o4.price, o4.timestamp, o4.volume, o4.id))
        ob.bid_queue.put((o5.price, o5.timestamp, o5.volume, o5.id))
        ob.bid_queue.put((o6.price, o6.timestamp, o6.volume, o6.id))
        ob.bid_queue.put((o7.price, o7.timestamp, o7.volume, o7.id))
        ob.bid_queue.put((o8.price, o8.timestamp, o8.volume, o8.id))

        b1 = ob.peek_best('ASK')
        b2 = ob.peek_best(OrderAction.HOLD)
        b3 = ob.peek_best('BID')
        b4 = ob.peek_best(OrderAction.CANCEL)

        self.assertEqual(b1, [])
        self.assertEqual(b2, [])
        self.assertEqual(b3, [])
        self.assertEqual(b4, [])

    def test_add_to_queue_ask(self):
        ob = OrderBook()
        o1 = Order(1, 1, 1.00, 10, OrderAction.ASK)
        info_tuple = (o1.price, o1.timestamp, o1.volume, o1.id)

        ob._add_to_queue(o1.side, info_tuple)

        self.assertEqual(ob.ask_queue.get(), info_tuple)

    def test_add_to_queue_bid(self):
        ob = OrderBook()
        o1 = Order(1, 1, 1.00, 10, OrderAction.BID)
        info_tuple = (-o1.price, o1.timestamp, o1.volume, o1.id)

        ob._add_to_queue(o1.side, info_tuple)

        self.assertEqual(ob.get_best(o1.side), info_tuple)

    def test_add_to_queue_fail(self):
        ob = OrderBook()
        o1 = Order(1, 1, 1.00, 10, OrderAction.ASK)
        info_tuple = (o1.price, o1.timestamp, o1.volume, o1.id)
        o2 = Order(2, 1, 1.00, 10, OrderAction.BID)
        info_tuple2 = (-o2.price, o2.timestamp, o2.volume, o2.id)

        ob._add_to_queue(OrderAction.HOLD, info_tuple)
        ob._add_to_queue(OrderAction.CANCEL, info_tuple2)
        self.assertEqual((), ob.get_best(o1.side))
        self.assertEqual((), ob.get_best(o2.side))

        ob._add_to_queue('ASK', info_tuple)
        ob._add_to_queue('BID', info_tuple2)
        self.assertEqual((), ob.get_best(o1.side))
        self.assertEqual((), ob.get_best(o2.side))

    def test_add_order_ask(self):
        ob = OrderBook()
        o1 = Order(1, 1, 1.00, 10, OrderAction.ASK)
        info_tuple = (o1.price, o1.timestamp, o1.volume, o1.id)

        ob.add_order(o1)

        self.assertIn(o1.id, ob.order_history)
        self.assertEqual(ob.get_best(o1.side), info_tuple)

    def test_add_order_bid(self):
        ob = OrderBook()
        o1 = Order(1, 1, 1.00, 10, OrderAction.BID)
        info_tuple = (o1.price, o1.timestamp, o1.volume, o1.id)

        ob.add_order(o1)

        self.assertIn(o1.id, ob.order_history)
        self.assertEqual(ob.get_best(o1.side), info_tuple)

    def test_remove_from_queue_ask(self):
        ob = OrderBook()
        o1 = Order(1, 1, 1.00, 10, OrderAction.ASK)
        o2 = Order(2, 1, 1.10, 10, OrderAction.ASK)
        o3 = Order(3, 1, 0.90, 10, OrderAction.ASK)
        o4 = Order(4, 1, 1.00, 20, OrderAction.ASK)

        ob.ask_queue.put((o1.price, o1.timestamp, o1.volume, o1.id))
        ob.ask_queue.put((o2.price, o2.timestamp, o2.volume, o2.id))
        ob.ask_queue.put((o3.price, o3.timestamp, o3.volume, o3.id))
        ob.ask_queue.put((o4.price, o4.timestamp, o4.volume, o4.id))

        ob._remove_from_queue(o2.side, o2.id)
        
        queue_list = ob.peek_best(o2.side, 4)
        self.assertEqual(queue_list[0][0], o3.price)
        self.assertEqual(queue_list[1][0], o1.price)
        self.assertEqual(queue_list[2][0], o4.price)
        self.assertEqual(len(queue_list), 3)

    def test_remove_from_queue_bid(self):
        ob = OrderBook()
        o1 = Order(1, 1, 1.00, 10, OrderAction.BID)
        o2 = Order(2, 1, 1.10, 10, OrderAction.BID)
        o3 = Order(3, 1, 0.90, 10, OrderAction.BID)
        o4 = Order(4, 1, 1.00, 20, OrderAction.BID)

        ob.bid_queue.put((-o1.price, o1.timestamp, o1.volume, o1.id))
        ob.bid_queue.put((-o2.price, o2.timestamp, o2.volume, o2.id))
        ob.bid_queue.put((-o3.price, o3.timestamp, o3.volume, o3.id))
        ob.bid_queue.put((-o4.price, o4.timestamp, o4.volume, o4.id))

        ob._remove_from_queue(o3.side, o3.id)
        
        queue_list = ob.peek_best(o3.side, 4)
        self.assertEqual(queue_list[0][0], o2.price)
        self.assertEqual(queue_list[1][0], o1.price)
        self.assertEqual(queue_list[2][0], o4.price)
        self.assertEqual(len(queue_list), 3)

    def test_remove_from_queue_fail(self):
        pass

    def test_return_assets_ask(self):
        ob = OrderBook()
        a = Agent(1, ob.manager, 100)
        o = Order(1, a.id, 1.00, 10, OrderAction.ASK)

        ob.add_agent(a)
        ob._return_assets(o)

        self.assertEqual(a.holdings[1.00], 10)
        self.assertEqual(a.cash, 100)
        self.assertEqual(ob.agents[a.id].holdings[1.00], 10)
        self.assertEqual(ob.agents[a.id].cash, 100)

    def test_return_assets_bid(self):
        ob = OrderBook()
        a = Agent(1, ob.manager, 100)
        o = Order(1, a.id, 1.00, 10, OrderAction.BID)

        ob.add_agent(a)
        ob._return_assets(o)

        self.assertEqual(a.cash, 100)
        self.assertEqual(len(ob.agents[a.id].holdings.keys()), 0)
        self.assertEqual(ob.agents[a.id].cash, 110)

    def test_return_assets_fail(self):
        pass

    def test_cancel_order_ask(self):
        ob = OrderBook()
        a = Agent(1, ob.manager, 100)
        o = Order(1, a.id, 1.00, 10, OrderAction.ASK)

        ob.add_agent(a)
        ob.add_order(o)
        ob.cancel_order(o.id)

        self.assertEqual(ob.order_history[o.id].status, OrderStatus.CANCELED)
        self.assertEqual((), ob.get_best(o.side))
        self.assertIn(1.00, a.holdings)

    def test_cancel_order_bid(self):
        ob = OrderBook()
        a = Agent(1, ob.manager, 100)
        o = Order(1, a.id, 1.00, 10, OrderAction.BID)

        ob.add_agent(a)
        ob.add_order(o)
        ob.cancel_order(o.id)

        self.assertEqual(ob.order_history[o.id].status, OrderStatus.CANCELED)
        self.assertEqual((), ob.get_best(o.side))
        self.assertEqual(ob.agents[a.id].cash, 110)

    def test_cancel_order_fail(self):
        pass

    def test_get_snapshot(self):
        ob = OrderBook()
        o1 = Order(1, 1, 1.00, 10, OrderAction.BID)
        o2 = Order(1, 2, 1.10, 10, OrderAction.ASK)
        o3 = Order(3, 1, 0.90, 10, OrderAction.ASK)
        o4 = Order(4, 1, 1.00, 20, OrderAction.ASK)
        o5 = Order(5, 1, 1.00, 10, OrderAction.BID)
        o6 = Order(6, 1, 1.10, 10, OrderAction.BID)
        o7 = Order(7, 1, 0.90, 10, OrderAction.BID)
        o8 = Order(8, 1, 1.00, 20, OrderAction.BID)

        ob.add_order(o1)
        ob.add_order(o2)
        ob.add_order(o3)
        ob.add_order(o4)
        ob.add_order(o5)
        ob.add_order(o6)
        ob.add_order(o7)
        ob.add_order(o8)

        snap = ob.get_snapshot()
        print(snap)
        self.assertEqual(snap[0]['asks'][0]['price'], 0.90)
        self.assertEqual(snap[0]['asks'][0]['size'], 10)
        self.assertEqual(snap[0]['bids'][0]['price'], 1.10)
        self.assertEqual(snap[0]['bids'][0]['size'], 10)

    def test_get_snapshot_empty_ask(self):
        pass

    def test_get_snapshot_empty_bid(self):
        pass

    def test_get_snapshot_empty_both(self):
        pass