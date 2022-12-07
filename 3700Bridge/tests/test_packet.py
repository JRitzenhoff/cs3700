
import unittest

from networks.packet import Packet, BPDU, MessageType


class TestBDPU(unittest.TestCase):
    def test_networks_example(self):
        example_bdpu_json = {
            "id": "92b4",
            "root": "02a1",
            "cost": 3,
            "port": 2
        }

        bpdu = BPDU.deserialize(**example_bdpu_json)

        self.assertEqual("92b4", bpdu.id)
        self.assertEqual("02a1", bpdu.root)
        self.assertEqual(3, bpdu.cost)
        self.assertEqual(2, bpdu.port)

    def test_bpdu_equals(self):
        example_bdpu_json = {
            "id": "92b4",
            "root": "02a1",
            "cost": 3,
            "port": 2
        }

        bpdu = BPDU.deserialize(**example_bdpu_json)

        self.assertEqual(
            BPDU(id="92b4", root="02a1", cost=3, port=2),
            bpdu
        )


class TestPacket(unittest.TestCase):
    def test_networks_bpdu_example(self):
        example_bdpu_json = {
            "id": "92b4",
            "root": "02a1",
            "cost": 3,
            "port": 2
        }

        example_packet_json = {
            "source": "92b4",
            "dest": "ffff",
            "msg_id": 27,
            "type": "bpdu",
            "message": example_bdpu_json
        }

        packet = Packet.deserialize(**example_packet_json)

        self.assertEqual("92b4", packet.source)
        self.assertEqual("ffff", packet.dest)
        self.assertEqual(27, packet.msg_id)
        self.assertEqual(MessageType.BridgeProtocolDataUnit, packet.type)

        expected_bpdu = BPDU(id="92b4", root="02a1", cost=3, port=2)
        self.assertEqual(expected_bpdu, packet.message)

    def test_networks_data_example(self):
        example_message_json = {
            "favorite_color": "green",
            "best_teacher": "alden",
            "best_courses": ["CS 3700", "CS 3650"]
        }

        example_data_json = {
            "source": "28aa",
            "dest": "97bf",
            "msg_id": 4,
            "type": "data",
            "message": example_message_json
        }

        packet = Packet.deserialize(**example_data_json)

        self.assertEqual("28aa", packet.source)
        self.assertEqual("97bf", packet.dest)
        self.assertEqual(4, packet.msg_id)
        self.assertEqual(MessageType.DataMessage, packet.type)

        self.assertEqual(example_message_json, packet.message)

    def test_networks_bdpu_to_json(self):
        packet = Packet(
            source="92b4", dest="ffff", msg_id= 27,
            type="bpdu",
            message=BPDU(id="92b4", root="02a1", cost=3, port=2)
        )

        expected_packet = {
            "source": "92b4",
            "dest": "ffff",
            "msg_id": 27,
            "type": "bpdu",
            "message": {"id": "92b4", "root": "02a1", "cost": 3, "port": 2}
        }

        self.assertEqual(expected_packet, packet.serialize())

    def test_provided_bdpu(self):
        bpdu = BPDU(id="92b4", root="02a1", cost=3, port=2)

        example_packet_json = {
            "source": "92b4",
            "dest": "ffff",
            "msg_id": 27,
            "type": "bpdu",
            "message": bpdu
        }

        packet = Packet(**example_packet_json)

        self.assertEqual("92b4", packet.source)
        self.assertEqual("ffff", packet.dest)
        self.assertEqual(27, packet.msg_id)
        self.assertEqual(MessageType.BridgeProtocolDataUnit, packet.type)
        self.assertEqual(bpdu, packet.message)
