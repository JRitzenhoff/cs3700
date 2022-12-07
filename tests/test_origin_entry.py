import unittest

from networks.router import Router
from networks.packet import AutonomousSystemOrigin


class TestAutonomousSystemOrdering(unittest.TestCase):
    def test_order_of_operations(self):
        self.assertTrue(AutonomousSystemOrigin.LOCAL > AutonomousSystemOrigin.REMOTE)
        self.assertTrue(AutonomousSystemOrigin.REMOTE > AutonomousSystemOrigin.UNKNOWN)

        self.assertTrue(AutonomousSystemOrigin.LOCAL > AutonomousSystemOrigin.UNKNOWN)