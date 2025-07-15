import unittest
from multiprocessing import Manager
from Agent.Agent import Agent

class TestAgent(unittest.TestCase):

    def test_agent_init(self):
        AGENT = Agent(1, Manager(), 100)
        self.assertEqual(AGENT.id, 1)
        self.assertEqual(AGENT.cash, 100)
        self.assertEqual(len(AGENT.holdings.keys()), 0)
        self.assertEqual(len(AGENT.active_asks.keys()), 0)
        self.assertEqual(len(AGENT.active_bids.keys()), 0)
        self.assertEqual(len(AGENT.history.keys()), 0)

    def test_add_cash(self):
        AGENT = Agent(1, Manager(), 100)
        AGENT.update_cash(amt=100)
        self.assertEqual(AGENT.cash, 200)

    def test_remove_cash(self):
        AGENT = Agent(1, Manager(), 100)
        AGENT.update_cash(amt=-100)
        self.assertEqual(AGENT.cash, 0)

    def test_add_holding(self):
        AGENT = Agent(1, Manager(), 100)
        AGENT.update_holdings(1.00, 10)
        self.assertIn(1.00, AGENT.holdings)

    def test_update_holding(self):
        AGENT = Agent(1, Manager(), 100)
        AGENT.update_holdings(1.00, 10)
        AGENT.update_holdings(1.01, 10)
        AGENT.update_holdings(1.00, 10)
        self.assertEquals(AGENT.holdings[1.00], 20)

    def test_remove_holding_all_shares(self):
        AGENT = Agent(1, Manager(), 100)
        AGENT.update_holdings(1.00, 10)
        AGENT.update_holdings(1.01, 10)
        self.assertIn(1.00, AGENT.holdings)
        AGENT.remove_holding(1.00)
        self.assertNotIn(1.00, AGENT.holdings)
        self.assertIn(1.01, AGENT.holdings)

    def test_remove_holding_some_shares(self):
        AGENT = Agent(1, Manager(), 100)
        AGENT.update_holdings(1.00, 10)
        AGENT.update_holdings(1.01, 10)
        self.assertIn(1.00, AGENT.holdings)
        AGENT.remove_holding(1.00, 5)
        self.assertIn(1.00, AGENT.holdings)
        self.assertEqual(AGENT.holdings[1.00], 5)
        self.assertIn(1.01, AGENT.holdings)
        self.assertEqual(AGENT.holdings[1.01], 10)

    def test_getting_most_valuble_holding(self):
        AGENT = Agent(1, Manager(), 100)
        AGENT.update_holdings(1.00, 10)
        AGENT.update_holdings(1.01, 10)
        highest_value_share = AGENT.get_highest_value_share()
        self.assertEqual(highest_value_share[0], 1.01)
        self.assertEqual(highest_value_share[1], 10)

    def test_getting_least_valuble_holding(self):
        AGENT = Agent(1, Manager(), 100)
        AGENT.update_holdings(1.00, 10)
        AGENT.update_holdings(1.01, 10)
        lowest_value_share = AGENT.get_lowest_value_share()
        self.assertEqual(lowest_value_share[0], 1.00)
        self.assertEqual(lowest_value_share[1], 10)