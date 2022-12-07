import struct
import unittest

from networks.packet import TCPHeader, TCPPacket, short, digest
from networks.constants import EMPTY_CHECKSUM, DEFAULT_CHECKSUM_BIT_SIZE


class TestTCPHeader(unittest.TestCase):
    def setUp(self) -> None:
        seq_num = 10234
        flags = short(8)
        window = short(10)
        checksum = digest(EMPTY_CHECKSUM)

        self.header_bytes = struct.pack(f'>IHH{DEFAULT_CHECKSUM_BIT_SIZE}s',
                                        seq_num, flags, window, checksum)

        self.expected_header = TCPHeader(
            sequence_number=seq_num,
            flags=flags,
            advertised_window=window,
            checksum=digest(checksum)
        )

    def test_from_bytes_header(self):
        header, remaining_bytes = TCPHeader.from_bytes(self.header_bytes)

        self.assertEqual(b'', remaining_bytes)
        self.assertEqual(self.expected_header, header)

    def test_from_bytes_packet_without_data(self):
        data_len = 0
        source_bytes = self.header_bytes + struct.pack(">H", data_len)

        tcp_packet, remaining_bytes = TCPPacket.from_bytes(source_bytes)

        self.assertEqual(TCPPacket(header=self.expected_header, data_length=short(data_len), data=b''), tcp_packet)
        self.assertEqual(b'', remaining_bytes)

    def test_from_bytes_packet_with_100_bytes_data(self):
        data_len = 100
        data_bytes = b'1' * data_len
        source_bytes = self.header_bytes + struct.pack(">H", data_len) + data_bytes

        tcp_packet, remaining_bytes = TCPPacket.from_bytes(source_bytes)

        self.assertEqual(TCPPacket(header=self.expected_header, data_length=short(data_len), data=data_bytes),
                         tcp_packet)
        self.assertEqual(b'', remaining_bytes)

    def test_from_bytes_packet_with_1000_bytes_and_remainder(self):
        data_len = 1000
        remainder = b'01' * 50
        data_bytes = b'1' * data_len
        source_bytes = self.header_bytes + struct.pack(">H", data_len) + data_bytes + remainder

        tcp_packet, remaining_bytes = TCPPacket.from_bytes(source_bytes)

        self.assertEqual(TCPPacket(header=self.expected_header, data_length=short(data_len), data=data_bytes),
                         tcp_packet)
        self.assertEqual(remainder, remaining_bytes)

    def test_to_bytes_header(self):
        generated_bytes = self.expected_header.to_bytes()

        self.assertEqual(self.header_bytes, generated_bytes)

    def test_to_bytes_packet_without_data(self):
        data_len = 0
        source_packet = TCPPacket(header=self.expected_header, data_length=short(data_len), data=b'')

        generated_bytes = source_packet.to_bytes()

        expected_bytes = self.header_bytes + struct.pack(">H", data_len)
        self.assertEqual(expected_bytes, generated_bytes)

    def test_to_bytes_packet_with_100_bytes_data(self):
        data_len = 100
        data_bytes = b'010023402304900203940190590091905909290359235' + (b'1' * 55)
        self.assertEqual(data_len, len(data_bytes))

        source_packet = TCPPacket(header=self.expected_header, data_length=short(data_len), data=data_bytes)
        generated_bytes = source_packet.to_bytes()

        expected_bytes = self.header_bytes + struct.pack(">H", data_len) + data_bytes
        self.assertEqual(expected_bytes, generated_bytes)


if __name__ == '__main__':
    unittest.main()
