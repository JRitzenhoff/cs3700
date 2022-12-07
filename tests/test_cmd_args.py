import unittest

from networks.launch import create_parser, parse_connections
from networks.router import ConnectionType
from networks.ipaddress import IPAddress


class TestParsing(unittest.TestCase):

    def test_fullscale(self):
        test_args = ["1824", "10-192.168.2.10-peer", "9023-10.244.19.205-cust"]

        parser = create_parser()
        args = parser.parse_args(test_args)

        parsed_conns = parse_connections(args.connections)

        expected_conns = [(10, IPAddress("192.168.2.10"), ConnectionType.PEER),
                          (9023, IPAddress("10.244.19.205"), ConnectionType.CUSTOMER)]

        self.assertEqual(expected_conns, parsed_conns)