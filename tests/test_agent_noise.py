import unittest
from multiprocessing import Manager
from Agent.NoiseAgent import NoiseAgent
from OrderBook.OrderBook import OrderBook
from Order.OrderAction import OrderAction
from Order.OrderType import OrderType
from Order.OrderStatus import OrderStatus
from Order.Order import Order

class TestNoiseAgent(unittest.TestCase):

    def test_get_action(self):
        ob = OrderBook()
        ob.current_price = 1
        na = NoiseAgent(1, ob.manager, 0.1)
        action = na._get_action(ob)
        self.assertEquals(action, OrderAction.HOLD)

        na.update_cash(1)
        action = na._get_action(ob)
        if (action is OrderAction.HOLD or action is OrderAction.BID):
            self.assertTrue(True)

        na.update_cash(-2)
        na.update_holdings(1.00, 10)
        action = na._get_action(ob)
        if (action is OrderAction.HOLD or action is OrderAction.ASK):
            self.assertTrue(True)

        na.remove_holding(1.00)
        na.active_asks[1] = Order(1, na.id, 1.11, 11, OrderAction.ASK, OrderType.LIMIT)
        action = na._get_action(ob)
        if (action is OrderAction.HOLD or action is OrderAction.CANCEL):
            self.assertTrue(True)

    def test_execute_market_bid(self):
        ob = OrderBook()
        ob.current_price = 1.00
        na = NoiseAgent(1, ob.manager, 10.00)
        
        order = na._execute_market_bid(ob)

        self.assertEqual(order.id, 'O-000000000001')
        self.assertEqual(order.agent_id, na.id)
        self.assertEqual(order.price, -1)
        if 1 <= order.volume <= 10:
            self.assertTrue(True, 'Order volume in acceptable range')
        else:
            self.assertTrue(False, 'Order volume unacceptable')
        self.assertEqual(order.side, OrderAction.BID)
        self.assertEqual(order.type, OrderType.MARKET)

    def test_execute_limit_bid(self):
        ob = OrderBook()
        ob.current_price = 1.00
        na = NoiseAgent(1, ob.manager, 10.00)
        start_cash = na.cash
        lowest_possible_price = ob.current_price - (ob.current_price * na.max_price_deviation)

        order = na._execute_limit_bid(ob)

        self.assertEqual(order.id, 'O-000000000001')
        self.assertEqual(order.agent_id, na.id)
        if lowest_possible_price <= order.price <= ob.current_price:
            self.assertTrue(True, 'Order price in acceptable range')
        else:
            self.assertTrue(False, 'Order price unnacceptable')
        if 1 <= order.volume <= 10:
            self.assertTrue(True, 'Order volume in acceptable range')
        else:
            self.assertTrue(False, 'Order volume unacceptable')
        self.assertEqual(order.side, OrderAction.BID)
        self.assertEqual(order.type, OrderType.LIMIT)
        self.assertLess(na.cash, start_cash)

    def test_execute_market_ask(self):
        ob = OrderBook()
        ob.current_price = 1.00
        na = NoiseAgent(1, ob.manager, 10.00)
        na.update_holdings(1.00, 5)

        order = na._execute_market_ask(ob)

        self.assertEqual(order.id, 'O-000000000001')
        self.assertEqual(order.agent_id, na.id)
        self.assertEqual(order.price, -1)
        if 1 <= order.volume <= 5:
            self.assertTrue(True, 'Order volume in acceptable range')
        else:
            self.assertTrue(False, 'Order volume unacceptable')
        self.assertEqual(order.side, OrderAction.ASK)
        self.assertEqual(order.type, OrderType.MARKET)

    def test_execute_limit_ask(self):
        ob = OrderBook()
        ob.current_price = 1.00
        na = NoiseAgent(1, ob.manager, 10.00)
        na.update_holdings(1.00, 5)
        highest_possible_price = ob.current_price + (ob.current_price * na.max_price_deviation)

        order = na._execute_limit_ask(ob)

        self.assertEqual(order.id, 'O-000000000001')
        self.assertEqual(order.agent_id, na.id)
        if ob.current_price <= order.price <= highest_possible_price:
            self.assertTrue(True, 'Order price in acceptable range')
        else:
            self.assertTrue(False, 'Order price unnacceptable')
        if 1 <= order.volume <= 5:
            self.assertTrue(True, 'Order volume in acceptable range')
        else:
            self.assertTrue(False, 'Order volume unacceptable')
        self.assertEqual(order.side, OrderAction.ASK)
        self.assertEqual(order.type, OrderType.LIMIT)
        if order.volume == 5:
            self.assertNotIn(order.price, na.holdings)
        else:
            self.assertIn(order.price, na.holdings)
            self.assertEqual(na.holdings[order.price], 5-order.volume)

    def test_execute_cancel_ask(self):
        ob = OrderBook()
        ob.current_price = 1.00
        na = NoiseAgent(1, ob.manager, 10.00)
        ob.add_agent(na)

        o = Order(ob.get_id('ORDER'), na.id, 1.00, 10, OrderAction.ASK, OrderType.LIMIT)

        na.active_asks[o.id] = o
        na.history[o.id] = o
        ob.add_order(o)

        na._execute_cancel(ob)
        
        self.assertNotIn(o.id, na.active_asks)
        self.assertEqual(na.history[o.id].status, OrderStatus.CANCELED)
        self.assertIn(o.price, na.holdings)
        self.assertEqual(na.holdings[o.price], 10)

    def test_execute_cancel_bid(self):
        ob = OrderBook()
        ob.current_price = 1.00
        na = NoiseAgent(1, ob.manager, 10.00)
        ob.add_agent(na)

        o = Order(ob.get_id('ORDER'), na.id, 1.00, 10, OrderAction.BID, OrderType.LIMIT)

        na.active_bids[o.id] = o
        na.history[o.id] = o
        ob.add_order(o)

        na._execute_cancel(ob)

        self.assertNotIn(o.id, na.active_bids)
        self.assertEqual(na.history[o.id].status, OrderStatus.CANCELED)
        self.assertNotIn(o.price, na.holdings)
        self.assertEqual(ob.agents[na.id].cash, 20.00)
        self.assertEqual(na.cash, 20.00)

    def test_act(self):
        ob = OrderBook()
        ob.current_price = 1.00
        na = NoiseAgent(1, ob.manager, 100.00)
        na2 = NoiseAgent(2, ob.manager, 50.00)
        ob.add_agent(na)
        ob.add_agent(na2)

        o = Order('MAKER', 'MAKER', 1.00, 1000, OrderAction.ASK, OrderType.LIMIT)
        ob.add_order(o)
        try:
            for x in range(5):
                action = na.act(ob)
                action2 = na2.act(ob)
                if action != None:
                    print(action.info())
                if action2 != None:
                    print(action2.info())

            print(na.info())
            print(na2.info())
        except:
            self.assertTrue(True)