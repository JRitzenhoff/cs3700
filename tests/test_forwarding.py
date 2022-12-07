import unittest
from unittest.mock import Mock

from networks.router import Router
from networks.request_handler import UpdatePacketHandler, DataPacketHandler
from networks.packet import Packet, UpdateMsg, AutonomousSystemOrigin
from networks.ipaddress import IPAddress, SubnetMask
from networks.utils import ConnectionType


class TestUpdateFiltering(unittest.TestCase):

    def setUp(self) -> None:
        self.ip1 = IPAddress('172.77.0.2')
        self.ip2 = IPAddress('192.0.0.2')
        self.ip3 = IPAddress('192.168.12.2')
        self.ip4 = IPAddress('192.168.0.2')

        self.u1 = UpdateMsg(network=IPAddress('172.77.0.0'), netmask=SubnetMask('255.255.0.0'),
                            ASPath=[4], localpref=100, selfOrigin=True, origin=AutonomousSystemOrigin.REMOTE)
        self.u2 = UpdateMsg(network=IPAddress('192.0.0.0'), netmask=SubnetMask('255.0.0.0'),
                            ASPath=[1], localpref=100, selfOrigin=True, origin=AutonomousSystemOrigin.REMOTE)
        self.u3 = UpdateMsg(network=IPAddress('192.168.12.0'), netmask=SubnetMask('255.255.255.0'),
                            ASPath=[3], localpref=100, selfOrigin=True, origin=AutonomousSystemOrigin.REMOTE)
        self.u4 = UpdateMsg(network=IPAddress('192.168.0.0'), netmask=SubnetMask('255.255.0.0'),
                            ASPath=[2], localpref=100, selfOrigin=True, origin=AutonomousSystemOrigin.REMOTE)

        # 9 36528-192.0.0.2-cust 56074-192.168.0.2-cust 43055-192.168.12.2-cust 48793-172.77.0.2-cust'
        self.router = Router(asn=9,
                             connections=[(36528, self.ip2, ConnectionType.CUSTOMER),
                                          (56076, self.ip4, ConnectionType.CUSTOMER),
                                          (43055, self.ip3, ConnectionType.CUSTOMER),
                                          (48793, self.ip1, ConnectionType.CUSTOMER)])

        self.mocksock1 = Mock()
        self.mocksock2 = Mock()
        self.mocksock3 = Mock()
        self.mocksock4 = Mock()

        self.router.ip_socket_map[self.ip1] = self.mocksock1
        self.router.ip_socket_map[self.ip2] = self.mocksock2
        self.router.ip_socket_map[self.ip3] = self.mocksock3
        self.router.ip_socket_map[self.ip4] = self.mocksock4

        for handler in [UpdatePacketHandler(sender=self.ip1, msg=self.u1),
                        UpdatePacketHandler(sender=self.ip2, msg=self.u2),
                        UpdatePacketHandler(sender=self.ip3, msg=self.u3),
                        UpdatePacketHandler(sender=self.ip4, msg=self.u4)]:
            handler.process(self.router)

    def test_received_ports(self):
        data_packet = Packet.deserialize(**{"src": "192.168.0.1", "dst": "192.0.0.25",
                                            "type": "data", "msg": {"ignore": "this"}})

        data_handler = DataPacketHandler(sender=self.ip4, packet=data_packet)

        data_handler.process(self.router)

        print(self.mocksock1.mock_calls)
        print(self.mocksock2.mock_calls)
        print(self.mocksock3.mock_calls)
        print(self.mocksock4.mock_calls)


class TestRouteDetermining(unittest.TestCase):
    def test_unexpected_reception(self):
        peer1 = IPAddress("192.168.0.2")
        update1 = UpdateMsg.deserialize(**{"network": "12.0.0.0", "netmask": "255.0.0.0", "ASPath": [1, 4],
                                           "localpref": 150, "selfOrigin": False, "origin": "EGP"})

        peer2 = IPAddress("10.0.0.2")
        update2 = UpdateMsg.deserialize(**{"network": "12.0.0.0", "netmask": "255.0.0.0", "ASPath": [3, 4],
                                           "localpref": 150, "selfOrigin": False, "origin": "IGP"})

        larger = DataPacketHandler._determine_best_route(largest_update_message=update1,
                                                largest_ip_address=peer1,
                                                contending_update_msg=update2,
                                                contending_ip_address=peer2)

        print(larger)

