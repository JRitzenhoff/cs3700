import unittest

from networks.port import Port

class CalculateBridgeSource(unittest.TestCase):

    def setUp(self) -> None:
        self.port1 = Port()

        self.bridge = None