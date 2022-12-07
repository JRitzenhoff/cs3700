import unittest

import struct

from networks.ipaddress import IPAddress, SubnetMask


class TestIPAddress(unittest.TestCase):

    def test_construction(self):
        string_address = '127.0.0.1'

        address = IPAddress(string_address)

        expected_integer = (127 << 24) + 1
        self.assertEqual(expected_integer, address.binary)

    def test_fail_ip_range(self):
        string_address = '300.10.0.2'

        with self.assertRaisesRegex(struct.error, 'ubyte format requires 0 <= number <= 255'):
            IPAddress(string_address)

    def test_desconstruction(self):
        string_address = '127.0.0.1'

        address = IPAddress(string_address)
        self.assertEqual(string_address, str(address))


class TestSubnetMask(unittest.TestCase):

    def test_subnet_mask(self):
        mask = SubnetMask('255.128.0.0')

        self.assertEqual(9, mask.length)

    def test_no_subnet_mask(self):
        mask = SubnetMask('0.0.0.0')

        self.assertEqual(0, mask.length)

    def test_full_subnet_mask(self):
        mask = SubnetMask('255.255.255.255')

        self.assertEqual(32, mask.length)


if __name__ == '__main__':
    unittest().main()
