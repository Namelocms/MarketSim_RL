import unittest
from OrderBook.OrderBook import OrderBook
from OrderBook.Matchmaker import MatchMaker
from Order.Order import Order
from Order.OrderAction import OrderAction
from Order.OrderType import OrderType
from Order.OrderStatus import OrderStatus
from Agent.Agent import Agent
from Agent.NoiseAgent import NoiseAgent

def setup():
    ob = OrderBook()
    
    a1 = Agent(ob.get_id('AGENT'), ob.manager, cash=100)
    a2 = Agent(ob.get_id('AGENT'), ob.manager, cash=100)
    a3 = Agent(ob.get_id('AGENT'), ob.manager, cash=100)
    a4 = Agent(ob.get_id('AGENT'), ob.manager, cash=100)
    
    ao1 = Order(ob.get_id('ORDER'), a1.id, 1.10, 10, OrderAction.ASK, OrderType.LIMIT)
    a1.history[ao1.id] = ao1
    a1.upsert_active_ask(ao1)
    ao2 = Order(ob.get_id('ORDER'), a2.id, 1.15, 10, OrderAction.ASK, OrderType.LIMIT)
    a2.history[ao2.id] = ao2
    a2.upsert_active_ask(ao2)
    bo1 = Order(ob.get_id('ORDER'), a3.id, 0.90, 10, OrderAction.BID, OrderType.LIMIT)
    a3.history[bo1.id] = bo1
    a3.upsert_active_bid(bo1)
    bo2 = Order(ob.get_id('ORDER'), a4.id, 0.85, 10, OrderAction.BID, OrderType.LIMIT)
    a4.history[bo2.id] = bo2
    a4.upsert_active_bid(bo2)

    ob.upsert_agent(a1)
    ob.upsert_agent(a2)
    ob.upsert_agent(a3)
    ob.upsert_agent(a4)

    ob.add_order(ao1)
    ob.add_order(ao2)
    ob.add_order(bo1)
    ob.add_order(bo2)
        
    return {
        'ob': ob,
        'a1': a1,
        'a2': a2,
        'a3': a3,
        'a4': a4,
        'ao1': ao1,
        'ao2': ao2,
        'bo1': bo1,
        'bo2': bo2,
    }

class TestMatchMaker(unittest.TestCase):
    # Market Bids
    def test_match_market_bid__partial_fill(self):
        ''' Partially fill the bid then cancel it '''
        s = setup()
        ob: OrderBook = s['ob']
        ao1: Order = s['ao1']
        ao2: Order = s['ao2']

        mm = MatchMaker()

        # Bidding agent
        ba = NoiseAgent(ob.get_id('AGENT'), ob.manager, cash=100)
        order = Order(ob.get_id('ORDER'), ba.id, -1, 25, OrderAction.BID, OrderType.MARKET)
        ba.history[order.id] = order
        ob.upsert_agent(ba)

        mm.match_market_bid(ob, order)

        ba_after: Agent = ob.agents[ba.id]
        aa1_after: Agent = ob.agents[s['a1'].id]
        aa2_after: Agent = ob.agents[s['a2'].id]
        ao1_after: Order = ob.order_history[ao1.id]
        ao2_after: Order = ob.order_history[ao2.id]

        # Check bidding agent cash
        self.assertEqual(ba_after.cash, ba.cash - (ao1.price * ao1.volume) - (ao2.price * ao2.volume))
        # Check bidding agent holdings
        self.assertEqual(ba_after.get_total_shares(), 20)
        # Check bidding agent history
        self.assertIn(order.id, ba_after.history)
        # Check asking agent cash
        self.assertEqual(aa1_after.cash, s['a1'].cash + (ao1.price * ao1.volume))
        self.assertEqual(aa2_after.cash, s['a2'].cash + (ao2.price * ao2.volume))
        # Check asking agent active_asks
        self.assertNotIn(ao1.id, aa1_after.active_asks)
        self.assertNotIn(ao2.id, aa2_after.active_asks)
        # Check asking agent history
        self.assertIn(ao1.id, aa1_after.history)
        self.assertIn(ao2.id, aa2_after.history)
        # Check ask orders are closed
        self.assertEqual(ao1_after.status, OrderStatus.CLOSED)
        self.assertEqual(ao2_after.status, OrderStatus.CLOSED)
        # Check ask order volume is 0
        self.assertEqual(ao1_after.volume, 0)
        self.assertEqual(ao2_after.volume, 0)
    def test_match_market_bid__exact_fill(self):
        ''' Bid volume and ask volume match '''
        s = setup()
        ob: OrderBook = s['ob']
        ao1: Order = s['ao1']
        ao2: Order = s['ao2']

        mm = MatchMaker()

        # Bidding agent
        ba = NoiseAgent(ob.get_id('AGENT'), ob.manager, cash=100)
        order = Order(ob.get_id('ORDER'), ba.id, -1, 10, OrderAction.BID, OrderType.MARKET)
        ba.history[order.id] = order
        ob.upsert_agent(ba)

        mm.match_market_bid(ob, order)

        ba_after: Agent = ob.agents[ba.id]
        aa1_after: Agent = ob.agents[s['a1'].id]
        aa2_after: Agent = ob.agents[s['a2'].id]
        ao1_after: Order = ob.order_history[ao1.id]
        ao2_after: Order = ob.order_history[ao2.id]

        # Check bidding agent cash
        self.assertEqual(ba_after.cash, ba.cash - (ao1.price * ao1.volume))
        # Check bidding agent holdings
        self.assertEqual(ba_after.get_total_shares(), 10)
        # Check bidding agent history
        self.assertIn(order.id, ba_after.history)
        # Check asking agent cash
        self.assertEqual(aa1_after.cash, s['a1'].cash + (ao1.price * ao1.volume))
        self.assertEqual(aa2_after.cash, s['a2'].cash)
        # Check asking agent active_asks
        self.assertNotIn(ao1.id, aa1_after.active_asks)
        self.assertIn(ao2.id, aa2_after.active_asks)
        # Check asking agent history
        self.assertIn(ao1.id, aa1_after.history)
        self.assertIn(ao2.id, aa2_after.history)
        # Check ask orders are closed
        self.assertEqual(ao1_after.status, OrderStatus.CLOSED)
        self.assertEqual(ao2_after.status, OrderStatus.OPEN)
        # Check ask order volume is 0
        self.assertEqual(ao1_after.volume, 0)
        self.assertEqual(ao2_after.volume, 10)
    def test_match_market_bid__full_fill(self):
        ''' Bid volume is less than ask volume '''
        s = setup()
        ob: OrderBook = s['ob']
        ao1: Order = s['ao1']
        ao2: Order = s['ao2']

        mm = MatchMaker()

        # Bidding agent
        ba = NoiseAgent(ob.get_id('AGENT'), ob.manager, cash=100)
        order = Order(ob.get_id('ORDER'), ba.id, -1, 5, OrderAction.BID, OrderType.MARKET)
        ba.history[order.id] = order
        ob.upsert_agent(ba)

        mm.match_market_bid(ob, order)

        ba_after: Agent = ob.agents[ba.id]
        aa1_after: Agent = ob.agents[s['a1'].id]
        aa2_after: Agent = ob.agents[s['a2'].id]
        ao1_after: Order = ob.order_history[ao1.id]
        ao2_after: Order = ob.order_history[ao2.id]

        # Check bidding agent cash
        self.assertEqual(ba_after.cash, ba.cash - (ao1.price * order.entry_volume))
        # Check bidding agent holdings
        self.assertEqual(ba_after.get_total_shares(), order.entry_volume)
        # Check bidding agent history
        self.assertIn(order.id, ba_after.history)
        # Check asking agent cash
        self.assertEqual(aa1_after.cash, s['a1'].cash + (ao1.price * order.entry_volume))
        self.assertEqual(aa2_after.cash, s['a2'].cash)
        # Check asking agent active_asks
        self.assertIn(ao1.id, aa1_after.active_asks)
        self.assertIn(ao2.id, aa2_after.active_asks)
        # Check asking agent history
        self.assertIn(ao1.id, aa1_after.history)
        self.assertIn(ao2.id, aa2_after.history)
        # Check ask orders are open
        self.assertEqual(ao1_after.status, OrderStatus.OPEN)
        self.assertEqual(ao2_after.status, OrderStatus.OPEN)
        # Check ask order volume is 5
        self.assertEqual(ao1_after.volume, 5)
        self.assertEqual(ao2_after.volume, 10)
    def test_match_market_bid__no_matches(self):
        ''' No asks exist in the OrderBook '''
        s = setup()
        ob: OrderBook = s['ob']
        ao1: Order = s['ao1']
        ao2: Order = s['ao2']

        mm = MatchMaker()

        # Bidding agent
        ba = NoiseAgent(ob.get_id('AGENT'), ob.manager, cash=100)
        order = Order(ob.get_id('ORDER'), ba.id, -1, 5, OrderAction.BID, OrderType.MARKET)
        ba.history[order.id] = order
        ob.upsert_agent(ba)

        ob.cancel_order(ao1.id, s['a1'])
        ob.cancel_order(ao2.id, s['a2'])

        mm.match_market_bid(ob, order)

        ba_after: Agent = ob.agents[ba.id]
        aa1_after: Agent = ob.agents[s['a1'].id]
        aa2_after: Agent = ob.agents[s['a2'].id]

        # Check bidding agent cash
        self.assertEqual(ba_after.cash, 100)
        # Check bidding agent holdings
        self.assertEqual(ba_after.get_total_shares(), 0)
        # Check bid order status is canceled
        self.assertEqual(ba_after.history[order.id].status, OrderStatus.CANCELED)
        # Check bidding agent history
        self.assertIn(order.id, ba_after.history)
        # Check asking agent cash
        self.assertEqual(aa1_after.cash, 100)
        self.assertEqual(aa2_after.cash, 100)

    # Limit Bids
    def test_match_limit_bid__partial_fill(self):
        ''' Partially fill the bid then add it to bid_queue '''
        s = setup()
        ob: OrderBook = s['ob']
        ao1: Order = s['ao1']
        ao2: Order = s['ao2']

        mm = MatchMaker()

        # Bidding agent
        ba = NoiseAgent(ob.get_id('AGENT'), ob.manager, cash=100)
        order = Order(ob.get_id('ORDER'), ba.id, 1.20, 25, OrderAction.BID, OrderType.LIMIT)
        ba.history[order.id] = order
        ob.upsert_agent(ba)

        mm.match_limit_bid(ob, order)
        
        ba_after: Agent = ob.agents[ba.id]
        aa1_after: Agent = ob.agents[s['a1'].id]
        aa2_after: Agent = ob.agents[s['a2'].id]
        ao1_after: Order = ob.order_history[ao1.id]
        ao2_after: Order = ob.order_history[ao2.id]

        # Check bidding agent cash
        self.assertEqual(ba_after.cash, ba.cash - (ao1.price * ao1.volume) - (ao2.price * ao2.volume))
        # Check bidding agent holdings
        self.assertEqual(ba_after.get_total_shares(), 20)
        # Check bidding agent history
        self.assertIn(order.id, ba_after.history)
        # Check bidding agent active bids
        self.assertIn(order.id, ba_after.active_bids)
        # Check Order book bid queue
        self.assertIsNotNone(ob._find_order_in_queue(order.id))
        # Check asking agent cash
        self.assertEqual(aa1_after.cash, s['a1'].cash + (ao1.price * ao1.volume))
        self.assertEqual(aa2_after.cash, s['a2'].cash + (ao2.price * ao2.volume))
        # Check asking agent active_asks
        self.assertNotIn(ao1.id, aa1_after.active_asks)
        self.assertNotIn(ao2.id, aa2_after.active_asks)
        # Check asking agent history
        self.assertIn(ao1.id, aa1_after.history)
        self.assertIn(ao2.id, aa2_after.history)
        # Check ask orders are closed
        self.assertEqual(ao1_after.status, OrderStatus.CLOSED)
        self.assertEqual(ao2_after.status, OrderStatus.CLOSED)
        # Check ask order volume is 0
        self.assertEqual(ao1_after.volume, 0)
        self.assertEqual(ao2_after.volume, 0)
    def test_match_limit_bid__exact_fill(self):
        ''' Bid volume and ask volume match '''
        s = setup()
        ob: OrderBook = s['ob']
        ao1: Order = s['ao1']
        ao2: Order = s['ao2']

        mm = MatchMaker()

        # Bidding agent
        ba = NoiseAgent(ob.get_id('AGENT'), ob.manager, cash=100)
        order = Order(ob.get_id('ORDER'), ba.id, 1.10, 10, OrderAction.BID, OrderType.LIMIT)
        ba.history[order.id] = order
        ob.upsert_agent(ba)

        ob.cancel_order(s['bo1'].id, s['a3'])
        ob.cancel_order(s['bo2'].id, s['a4'])

        mm.match_limit_bid(ob, order)
        
        ba_after: Agent = ob.agents[ba.id]
        aa1_after: Agent = ob.agents[s['a1'].id]
        aa2_after: Agent = ob.agents[s['a2'].id]
        ao1_after: Order = ob.order_history[ao1.id]
        ao2_after: Order = ob.order_history[ao2.id]

        # Check bidding agent cash
        self.assertEqual(ba_after.cash, ba.cash - (ao1.price * ao1.volume))
        # Check bidding agent holdings
        self.assertEqual(ba_after.get_total_shares(), 10)
        # Check bidding agent history
        self.assertIn(order.id, ba_after.history)
        # Check bidding agent active bids
        self.assertNotIn(order.id, ba_after.active_bids)
        # Check Order book bid queue
        self.assertTrue(ob.bid_queue.empty())
        # Check asking agent cash
        self.assertEqual(aa1_after.cash, s['a1'].cash + (ao1.price * ao1.volume))
        self.assertEqual(aa2_after.cash, s['a2'].cash)
        # Check asking agent active_asks
        self.assertNotIn(ao1.id, aa1_after.active_asks)
        self.assertIn(ao2.id, aa2_after.active_asks)
        # Check asking agent history
        self.assertIn(ao1.id, aa1_after.history)
        self.assertIn(ao2.id, aa2_after.history)
        # Check ask orders are closed
        self.assertEqual(ao1_after.status, OrderStatus.CLOSED)
        self.assertEqual(ao2_after.status, OrderStatus.OPEN)
        # Check ask order volume is 0
        self.assertEqual(ao1_after.volume, 0)
        self.assertEqual(ao2_after.volume, 10)
    def test_match_limit_bid__full_fill(self):
        ''' Bid volume is less than ask volume '''
        s = setup()
        ob: OrderBook = s['ob']
        ao1: Order = s['ao1']
        ao2: Order = s['ao2']

        mm = MatchMaker()

        # Bidding agent
        ba = NoiseAgent(ob.get_id('AGENT'), ob.manager, cash=100)
        order = Order(ob.get_id('ORDER'), ba.id, 1.10, 5, OrderAction.BID, OrderType.LIMIT)
        ba.history[order.id] = order
        ob.upsert_agent(ba)

        ob.cancel_order(s['bo1'].id, s['a3'])
        ob.cancel_order(s['bo2'].id, s['a4'])

        mm.match_limit_bid(ob, order)
        
        ba_after: Agent = ob.agents[ba.id]
        aa1_after: Agent = ob.agents[s['a1'].id]
        aa2_after: Agent = ob.agents[s['a2'].id]
        ao1_after: Order = ob.order_history[ao1.id]
        ao2_after: Order = ob.order_history[ao2.id]

        # Check bidding agent cash
        self.assertEqual(ba_after.cash, ba.cash - (ao1.price * order.entry_volume))
        # Check bidding agent holdings
        self.assertEqual(ba_after.get_total_shares(), 5)
        # Check bidding agent history
        self.assertIn(order.id, ba_after.history)
        # Check bidding agent active bids
        self.assertNotIn(order.id, ba_after.active_bids)
        # Check Order book bid queue
        self.assertTrue(ob.bid_queue.empty())
        # Check asking agent cash
        self.assertEqual(aa1_after.cash, s['a1'].cash + (ao1.price * order.entry_volume))
        self.assertEqual(aa2_after.cash, s['a2'].cash)
        # Check asking agent active_asks
        self.assertIn(ao1.id, aa1_after.active_asks)
        self.assertIn(ao2.id, aa2_after.active_asks)
        # Check asking agent history
        self.assertIn(ao1.id, aa1_after.history)
        self.assertIn(ao2.id, aa2_after.history)
        # Check ask orders are closed
        self.assertEqual(ao1_after.status, OrderStatus.OPEN)
        self.assertEqual(ao2_after.status, OrderStatus.OPEN)
        # Check ask order volume is 0
        self.assertEqual(ao1_after.volume, 5)
        self.assertEqual(ao2_after.volume, 10)
    def test_match_limit_bid__no_matches(self):
        ''' No asks exist in the OrderBook '''
        s = setup()
        ob: OrderBook = s['ob']
        ao1: Order = s['ao1']
        ao2: Order = s['ao2']

        mm = MatchMaker()

        # Bidding agent
        ba = NoiseAgent(ob.get_id('AGENT'), ob.manager, cash=100)
        order = Order(ob.get_id('ORDER'), ba.id, 1.10, 5, OrderAction.BID, OrderType.LIMIT)
        ba.history[order.id] = order
        ob.upsert_agent(ba)

        ob.cancel_order(s['bo1'].id, s['a3'])
        ob.cancel_order(s['bo2'].id, s['a4'])
        ob.cancel_order(ao1.id, s['a1'])
        ob.cancel_order(ao2.id, s['a2'])

        mm.match_limit_bid(ob, order)
        
        ba_after: Agent = ob.agents[ba.id]
        aa1_after: Agent = ob.agents[s['a1'].id]
        aa2_after: Agent = ob.agents[s['a2'].id]
        ao1_after: Order = ob.order_history[ao1.id]
        ao2_after: Order = ob.order_history[ao2.id]

        # Check bidding agent cash
        self.assertEqual(ba_after.cash, ba.cash)
        # Check bidding agent holdings
        self.assertEqual(ba_after.get_total_shares(), 0)
        # Check bidding agent history
        self.assertIn(order.id, ba_after.history)
        # Check bidding agent active bids
        self.assertIn(order.id, ba_after.active_bids)
        # Check Order book bid queue
        self.assertFalse(ob.bid_queue.empty())

    # Market Asks
    def test_match_market_ask__partial_fill(self):
        ''' Partially fill the ask then cancel it '''
        s = setup()
        ob: OrderBook = s['ob']
        bo1: Order = s['bo1']
        bo2: Order = s['bo2']

        mm = MatchMaker()

        # Asking agent
        aa = NoiseAgent(ob.get_id('AGENT'), ob.manager, cash=100)
        order = Order(ob.get_id('ORDER'), aa.id, -1, 25, OrderAction.ASK, OrderType.MARKET)
        aa.history[order.id] = order
        ob.upsert_agent(aa)

        mm.match_market_ask(ob, order)

        aa_after: Agent = ob.agents[aa.id]
        ba1_after: Agent = ob.agents[s['a3'].id]
        ba2_after: Agent = ob.agents[s['a4'].id]
        bo1_after: Order = ob.order_history[bo1.id]
        bo2_after: Order = ob.order_history[bo2.id]

        self.assertEqual(aa_after.cash, aa.cash + (bo1.volume * bo1.price) + (bo2.volume * bo2.price))
        self.assertEqual(aa_after.history[order.id].status, OrderStatus.CANCELED)
        self.assertEqual(ba1_after.get_total_shares(), bo1.volume)
        self.assertEqual(ba2_after.get_total_shares(), bo2.volume)
        self.assertNotIn(bo1.id, ba1_after.active_bids)
        self.assertNotIn(bo2.id, ba2_after.active_bids)
        self.assertEqual(ba1_after.history[bo1.id].status, OrderStatus.CLOSED)
        self.assertEqual(ba2_after.history[bo2.id].status, OrderStatus.CLOSED)
        self.assertEqual(bo1_after.volume, 0)
        self.assertEqual(bo2_after.volume, 0)
    def test_match_market_ask__exact_fill(self):
        ''' Ask volume and bid volume match '''
        s = setup()
        ob: OrderBook = s['ob']
        bo1: Order = s['bo1']
        bo2: Order = s['bo2']

        mm = MatchMaker()

        # Asking agent
        aa = NoiseAgent(ob.get_id('AGENT'), ob.manager, cash=100)
        order = Order(ob.get_id('ORDER'), aa.id, -1, 10, OrderAction.ASK, OrderType.MARKET)
        aa.history[order.id] = order
        ob.upsert_agent(aa)

        mm.match_market_ask(ob, order)

        aa_after: Agent = ob.agents[aa.id]
        ba1_after: Agent = ob.agents[s['a3'].id]
        ba2_after: Agent = ob.agents[s['a4'].id]
        bo1_after: Order = ob.order_history[bo1.id]
        bo2_after: Order = ob.order_history[bo2.id]

        self.assertEqual(aa_after.cash, aa.cash + (bo1.volume * bo1.price))
        self.assertEqual(aa_after.history[order.id].status, OrderStatus.CLOSED)
        self.assertEqual(ba1_after.get_total_shares(), bo1.volume)
        self.assertNotIn(bo1.id, ba1_after.active_bids)
        self.assertIn(bo2.id, ba2_after.active_bids)
        self.assertEqual(ba1_after.history[bo1.id].status, OrderStatus.CLOSED)
        self.assertEqual(ba2_after.history[bo2.id].status, OrderStatus.OPEN)
        self.assertEqual(bo1_after.volume, 0)
        self.assertEqual(bo2_after.volume, 10)
    def test_match_market_ask__full_fill(self):
        ''' Ask volume is less than bid volume '''
        s = setup()
        ob: OrderBook = s['ob']
        bo1: Order = s['bo1']
        bo2: Order = s['bo2']

        mm = MatchMaker()

        # Asking agent
        aa = NoiseAgent(ob.get_id('AGENT'), ob.manager, cash=100)
        order = Order(ob.get_id('ORDER'), aa.id, -1, 5, OrderAction.ASK, OrderType.MARKET)
        aa.history[order.id] = order
        ob.upsert_agent(aa)

        mm.match_market_ask(ob, order)

        aa_after: Agent = ob.agents[aa.id]
        ba1_after: Agent = ob.agents[s['a3'].id]
        ba2_after: Agent = ob.agents[s['a4'].id]
        bo1_after: Order = ob.order_history[bo1.id]
        bo2_after: Order = ob.order_history[bo2.id]

        self.assertEqual(aa_after.cash, aa.cash + (order.entry_volume * bo1.price))
        self.assertEqual(aa_after.history[order.id].status, OrderStatus.CLOSED)
        self.assertEqual(ba1_after.get_total_shares(), order.entry_volume)
        self.assertIn(bo1.id, ba1_after.active_bids)
        self.assertIn(bo2.id, ba2_after.active_bids)
        self.assertEqual(ba1_after.history[bo1.id].status, OrderStatus.OPEN)
        self.assertEqual(ba2_after.history[bo2.id].status, OrderStatus.OPEN)
        self.assertEqual(bo1_after.volume, 5)
        self.assertEqual(bo2_after.volume, 10)
    def test_match_market_ask__no_matches(self):
        ''' No bids exist in the OrderBook '''
        s = setup()
        ob: OrderBook = s['ob']
        bo1: Order = s['bo1']
        bo2: Order = s['bo2']

        mm = MatchMaker()

        # Asking agent
        aa = NoiseAgent(ob.get_id('AGENT'), ob.manager, cash=100)
        reserved_shares = [(1.10, 2), (1.05, 3)]
        order = Order(ob.get_id('ORDER'), aa.id, -1, 5, OrderAction.ASK, OrderType.MARKET, reserved_shares)
        aa.history[order.id] = order
        ob.upsert_agent(aa)

        ob.cancel_order(bo1.id, s['a3'])
        ob.cancel_order(bo2.id, s['a4'])

        mm.match_market_ask(ob, order)

        aa_after: Agent = ob.agents[aa.id]

        # Check asking agent cash
        self.assertEqual(aa_after.cash, 100)
        # Check asking agent holdings
        self.assertEqual(aa_after.get_total_shares(), order.entry_volume)
        # Check ask order status is canceled
        self.assertEqual(aa_after.history[order.id].status, OrderStatus.CANCELED)
        # Check asking agent history
        self.assertIn(order.id, aa_after.history)

    # Limit Asks
    def test_match_limit_ask__partial_fill(self):
        ''' Partially fill the ask then add it to ask_queue '''
        s = setup()
        ob: OrderBook = s['ob']
        bo1: Order = s['bo1']
        bo2: Order = s['bo2']

        mm = MatchMaker()

        # Asking agent
        aa = NoiseAgent(ob.get_id('AGENT'), ob.manager, cash=100)
        order = Order(ob.get_id('ORDER'), aa.id, 0.80, 25, OrderAction.ASK, OrderType.LIMIT)
        aa.history[order.id] = order
        ob.upsert_agent(aa)

        mm.match_limit_ask(ob, order)

        aa_after: Agent = ob.agents[aa.id]
        ba1_after: Agent = ob.agents[s['a3'].id]
        ba2_after: Agent = ob.agents[s['a4'].id]
        bo1_after: Order = ob.order_history[bo1.id]
        bo2_after: Order = ob.order_history[bo2.id]

        self.assertEqual(aa_after.cash, aa.cash + (bo1.volume * bo1.price) + (bo2.volume * bo2.price))
        self.assertEqual(aa_after.history[order.id].status, OrderStatus.OPEN)
        self.assertEqual(ba1_after.get_total_shares(), bo1.volume)
        self.assertEqual(ba2_after.get_total_shares(), bo2.volume)
        self.assertNotIn(bo1.id, ba1_after.active_bids)
        self.assertNotIn(bo2.id, ba2_after.active_bids)
        self.assertEqual(ba1_after.history[bo1.id].status, OrderStatus.CLOSED)
        self.assertEqual(ba2_after.history[bo2.id].status, OrderStatus.CLOSED)
        self.assertEqual(bo1_after.volume, 0)
        self.assertEqual(bo2_after.volume, 0)
    def test_match_limit_ask__exact_fill(self):
        ''' Ask volume and bid volume match '''
        s = setup()
        ob: OrderBook = s['ob']
        bo1: Order = s['bo1']
        bo2: Order = s['bo2']

        mm = MatchMaker()

        # Asking agent
        aa = NoiseAgent(ob.get_id('AGENT'), ob.manager, cash=100)
        order = Order(ob.get_id('ORDER'), aa.id, 0.80, 10, OrderAction.ASK, OrderType.LIMIT)
        aa.history[order.id] = order
        ob.upsert_agent(aa)

        mm.match_limit_ask(ob, order)

        aa_after: Agent = ob.agents[aa.id]
        ba1_after: Agent = ob.agents[s['a3'].id]
        ba2_after: Agent = ob.agents[s['a4'].id]
        bo1_after: Order = ob.order_history[bo1.id]
        bo2_after: Order = ob.order_history[bo2.id]

        self.assertEqual(aa_after.cash, aa.cash + (bo1.entry_volume * bo1.price))
        self.assertEqual(aa_after.history[order.id].status, OrderStatus.CLOSED)
        self.assertEqual(ba1_after.get_total_shares(), bo1.volume)
        self.assertNotIn(bo1.id, ba1_after.active_bids)
        self.assertIn(bo2.id, ba2_after.active_bids)
        self.assertEqual(ba1_after.history[bo1.id].status, OrderStatus.CLOSED)
        self.assertEqual(ba2_after.history[bo2.id].status, OrderStatus.OPEN)
        self.assertEqual(bo1_after.volume, 0)
        self.assertEqual(bo2_after.volume, 10)
    def test_match_limit_ask__full_fill(self):
        ''' Ask volume is less than bid volume '''
        s = setup()
        ob: OrderBook = s['ob']
        bo1: Order = s['bo1']
        bo2: Order = s['bo2']

        mm = MatchMaker()

        # Asking agent
        aa = NoiseAgent(ob.get_id('AGENT'), ob.manager, cash=100)
        order = Order(ob.get_id('ORDER'), aa.id, 0.80, 5, OrderAction.ASK, OrderType.LIMIT)
        aa.history[order.id] = order
        ob.upsert_agent(aa)

        mm.match_limit_ask(ob, order)

        aa_after: Agent = ob.agents[aa.id]
        ba1_after: Agent = ob.agents[s['a3'].id]
        ba2_after: Agent = ob.agents[s['a4'].id]
        bo1_after: Order = ob.order_history[bo1.id]
        bo2_after: Order = ob.order_history[bo2.id]

        self.assertEqual(aa_after.cash, aa.cash + (order.entry_volume * bo1.price))
        self.assertEqual(aa_after.history[order.id].status, OrderStatus.CLOSED)
        self.assertEqual(ba1_after.get_total_shares(), order.entry_volume)
        self.assertIn(bo1.id, ba1_after.active_bids)
        self.assertIn(bo2.id, ba2_after.active_bids)
        self.assertEqual(ba1_after.history[bo1.id].status, OrderStatus.OPEN)
        self.assertEqual(ba2_after.history[bo2.id].status, OrderStatus.OPEN)
        self.assertEqual(bo1_after.volume, 5)
        self.assertEqual(bo2_after.volume, 10)
    def test_match_limit_ask__no_matches(self):
        ''' No bids exist in the OrderBook '''
        s = setup()
        ob: OrderBook = s['ob']
        bo1: Order = s['bo1']
        bo2: Order = s['bo2']

        mm = MatchMaker()

        # Asking agent
        aa = NoiseAgent(ob.get_id('AGENT'), ob.manager, cash=100)
        reserved_shares = [(1.10, 2), (1.05, 3)]
        order = Order(ob.get_id('ORDER'), aa.id, 0.80, 5, OrderAction.ASK, OrderType.LIMIT, reserved_shares)
        aa.history[order.id] = order
        ob.upsert_agent(aa)

        ob.cancel_order(bo1.id, s['a3'])
        ob.cancel_order(bo2.id, s['a4'])

        mm.match_limit_ask(ob, order)

        aa_after: Agent = ob.agents[aa.id]

        # Check asking agent cash
        self.assertEqual(aa_after.cash, aa.cash)
        # Check asking agent holdings
        self.assertEqual(aa_after.get_total_shares(), 0)
        # Check ask order status is canceled
        self.assertEqual(aa_after.history[order.id].status, OrderStatus.OPEN)
        # Check asking agent history
        self.assertIn(order.id, aa_after.history)
        # Check asking agent active asks
        self.assertIn(order.id, aa_after.active_asks)
        # Check Order book ask queue
        self.assertFalse(ob.ask_queue.empty())