import unittest

from networks.packet import Packet, PacketType, UpdateMsg, UpdatePing, AutonomousSystemOrigin, NetworkDescription
from networks.ipaddress import IPAddress, SubnetMask


class TestPacketDeserialization(unittest.TestCase):

    def test_data_packet(self):
        data_packet_json = {
            'src': '127.0.0.1',
            'dst': '10.0.0.18',
            'type': 'data',
            'msg': None
        }

        packet = Packet.deserialize(**data_packet_json)

        expected_packet = Packet(
            src=IPAddress('127.0.0.1'),
            dst=IPAddress('10.0.0.18'),
            type=PacketType.DATA,
            msg=None
        )

        self.assertEqual(expected_packet, packet)

    def test_update_packet(self):
        update_packet_json = {
            'src': '127.0.0.1',
            'dst': '10.0.0.18',
            'type': 'update',
            'msg': {
                "network":    "126.0.0.0",
                "netmask":    "254.0.0.0",
                "localpref":  10,
                "selfOrigin": True,
                "ASPath":     [3, 5],
                "origin":     "IGP"
              }
        }

        packet = Packet.deserialize(**update_packet_json)

        expected_packet = Packet(
            src=IPAddress('127.0.0.1'),
            dst=IPAddress('10.0.0.18'),
            type=PacketType.UPDATE,
            msg=UpdateMsg(
                network=IPAddress("126.0.0.0"),
                netmask=SubnetMask("254.0.0.0"),
                localpref=10,
                selfOrigin=True,
                ASPath=[3, 5],
                origin=AutonomousSystemOrigin.LOCAL
            )
        )

        self.assertEqual(expected_packet, packet)

    def test_simple_1_1_update_packet(self):
        simple_1_1_update_json = {
            'type': 'update',
            'src': '192.168.0.2',
            'dst': '192.168.0.1',
            'msg': {
                'network': '192.168.0.0',
                'netmask': '255.255.255.0',
                'localpref': 100,
                'ASPath': [1],
                'origin': 'EGP',
                'selfOrigin': True
            }
        }

        packet = Packet.deserialize(**simple_1_1_update_json)

        expected_packet = Packet(
            src=IPAddress('192.168.0.2'),
            dst=IPAddress('192.168.0.1'),
            type=PacketType.UPDATE,
            msg=UpdateMsg(
                network=IPAddress('192.168.0.0'),
                netmask=SubnetMask('255.255.255.0'),
                localpref=100,
                ASPath=[1],
                origin=AutonomousSystemOrigin.REMOTE,
                selfOrigin=True
            )
        )

        self.assertEqual(expected_packet, packet)

    def test_withdraw_packet(self):
        withdraw_packet_json = {
            'src': '127.0.0.1',
            'dst': '10.0.0.18',
            'type': 'withdraw',
            'msg': [
                {'network': '88.234.0.2', 'netmask': '255.255.0.0'},
                {'network': '10.0.0.20', 'netmask': '255.0.0.0'}
            ]
        }

        packet = Packet.deserialize(**withdraw_packet_json)

        expected_packet = Packet(
            src=IPAddress('127.0.0.1'),
            dst=IPAddress('10.0.0.18'),
            type=PacketType.WITHDRAW,
            msg=[NetworkDescription(network=IPAddress('88.234.0.2'), netmask=SubnetMask('255.255.0.0')),
                 NetworkDescription(network=IPAddress('10.0.0.20'), netmask=SubnetMask('255.0.0.0'))]
        )

        self.assertEqual(expected_packet, packet)


class TestPacketSerialization(unittest.TestCase):

    def test_data_packet(self):
        data_packet = Packet(
            src=IPAddress('127.0.0.1'),
            dst=IPAddress('10.0.0.18'),
            type=PacketType.DATA,
            msg=None
        )

        serialized_packet = data_packet.serialize()

        expected_packet = {
            'src': '127.0.0.1',
            'dst': '10.0.0.18',
            'type': 'data',
            'msg': None
        }

        self.assertEqual(expected_packet, serialized_packet)

    def test_update_ping_packet(self):
        update_packet = Packet(
            src=IPAddress('127.0.0.1'),
            dst=IPAddress('10.0.0.18'),
            type=PacketType.UPDATE,
            msg=UpdatePing(
                network=IPAddress("126.0.0.0"),
                netmask=SubnetMask("254.0.0.0"),
                ASPath=[3, 5]
            )
        )

        serialized_packet = update_packet.serialize()

        expected_packet = {
            'src': '127.0.0.1',
            'dst': '10.0.0.18',
            'type': 'update',
            'msg': {
                "network":    "126.0.0.0",
                "netmask":    "254.0.0.0",
                "ASPath":     [3, 5]
              }
        }

        self.assertEqual(expected_packet, serialized_packet)

    def test_withdraw_packet(self):
        withdraw_packet = Packet(
            src=IPAddress('127.0.0.1'),
            dst=IPAddress('10.0.0.18'),
            type=PacketType.WITHDRAW,
            msg=[NetworkDescription(network=IPAddress('88.234.0.2'), netmask=SubnetMask('255.255.0.0')),
                 NetworkDescription(network=IPAddress('10.0.0.20'), netmask=SubnetMask('255.0.0.0'))]
        )

        serialized_packet = withdraw_packet.serialize()

        expected_packet = {
            'src': '127.0.0.1',
            'dst': '10.0.0.18',
            'type': 'withdraw',
            'msg': [
                {'network': '88.234.0.2', 'netmask': '255.255.0.0'},
                {'network': '10.0.0.20', 'netmask': '255.0.0.0'}
            ]
        }

        self.assertEqual(expected_packet, serialized_packet)


if __name__ == '__main__':
    unittest.main()