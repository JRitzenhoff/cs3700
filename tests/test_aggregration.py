import unittest
from unittest.mock import Mock

from networks.router import Router
from networks.request_handler import UpdatePacketHandler, DumpPacketHandler
from networks.packet import UpdateMsg, AutonomousSystemOrigin
from networks.ipaddress import IPAddress, SubnetMask
from networks.utils import ConnectionType


class TestUpdateFiltering(unittest.TestCase):

    def setUp(self) -> None:
        self.ip_address = IPAddress('192.168.0.2')

        self.u1 = UpdateMsg.deserialize(**{'network': '192.168.0.0', 'netmask': '255.255.255.0',
                                           'ASPath': [1], 'localpref': 100, 'selfOrigin': True,
                                           'origin': 'EGP'})
        self.u2 = UpdateMsg.deserialize(**{'network': '192.168.1.0', 'netmask': '255.255.255.0',
                                           'ASPath': [1], 'localpref': 100, 'selfOrigin': True,
                                           'origin': 'EGP'})
        self.u3 = UpdateMsg.deserialize(**{'network': '192.168.2.0', 'netmask': '255.255.255.0',
                                           'ASPath': [1], 'localpref': 100, 'selfOrigin': True,
                                           'origin': 'EGP'})
        self.u4 = UpdateMsg.deserialize(**{'network': '192.168.3.0', 'netmask': '255.255.255.0',
                                           'ASPath': [1], 'localpref': 100, 'selfOrigin': True,
                                           'origin': 'EGP'})

        # 9 36528-192.168.0.2-cust
        self.router = Router(asn=9,
                             connections=[(36528, self.ip_address, ConnectionType.CUSTOMER)])

        for handler in [UpdatePacketHandler(sender=self.ip_address, msg=self.u1),
                        UpdatePacketHandler(sender=self.ip_address, msg=self.u2),
                        UpdatePacketHandler(sender=self.ip_address, msg=self.u3),
                        UpdatePacketHandler(sender=self.ip_address, msg=self.u4)]:
            handler.process(self.router)

    def test_received_ports(self):
        from pprint import pprint
        pprint(self.router.forwarding_table)

        DumpPacketHandler._aggregate_forwarding_table(self.router)

        pprint(self.router.forwarding_table)

    def test_complex_group_aggregration(self):
        final_grouping, = DumpPacketHandler._aggregate_msg_group([self.u1, self.u2, self.u3, self.u4])

        self.assertEqual(UpdateMsg(network=IPAddress('192.168.0.0'), netmask=SubnetMask('255.255.252.0'),
                                   ASPath=[1], localpref=100, selfOrigin=True, origin=AutonomousSystemOrigin.REMOTE),
                         final_grouping)

    def test_simple_aggregration(self):
        final_grouping, = DumpPacketHandler._aggregate_msg_group([self.u4, self.u3])

        self.assertEqual(UpdateMsg(network=IPAddress('192.168.2.0'), netmask=SubnetMask('255.255.254.0'),
                                   ASPath=[1], localpref=100, selfOrigin=True, origin=AutonomousSystemOrigin.REMOTE),
                         final_grouping)

