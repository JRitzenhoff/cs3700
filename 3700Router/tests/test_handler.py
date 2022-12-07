import unittest

from networks.request_handler import Handler
from networks.packet import NetworkDescription
from networks.ipaddress import IPAddress, SubnetMask


class TestForwardingMask(unittest.TestCase):

    def test_forwarding_mask_logic(self):
        forwarding_entry = NetworkDescription(network=IPAddress("192.168.0.1"), netmask=SubnetMask("255.255.255.0"))
        dest_ip = IPAddress("192.168.0.25")

        self.assertEqual(24, Handler.matched_subnet(dest_ip, forwarding_entry))

    def test_forwarding_logic(self):
        forwarding_entry = NetworkDescription(network=IPAddress("192.168.12.2"), netmask=SubnetMask("255.255.255.0"))
        dest_ip = IPAddress("192.168.0.25")

        self.assertIsNone(Handler.matched_subnet(dest_ip, forwarding_entry))