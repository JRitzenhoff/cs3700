from typing import Optional, List

import argparse
import socket
import sys
import select

from networks.packet import TCPPacket, TCPHeader, TCPFlag, short, digest
from networks.constants import (
    ANY_BIND_ADDRESS, ANY_SOCKET_RECEIVE_PORT,
    DATA_ENCODING,
    EMPTY_CHECKSUM,
    DEFAULT_SLIDING_WINDOW_SIZE,
    MAX_UNSIGNED_INT
)


def log(message):
    sys.stderr.write(message + "\n")
    sys.stderr.flush()


class Receiver:
    """
    Representation of a TCP Receiver
    """

    def __init__(self, packet_io: socket.socket):
        self.udp_socket = packet_io

        self.simulator_host: Optional[int] = None
        self.simulator_port: Optional[int] = None

        self.highest_received_syn: Optional[int] = None
        """The highest SYN that has been received"""
        self.highest_acked: Optional[int] = None
        """The highest ACK that has been sent"""

        self.received_window_size: int = DEFAULT_SLIDING_WINDOW_SIZE

        self.window_size: int = DEFAULT_SLIDING_WINDOW_SIZE
        self.window_packets: List[TCPPacket] = []

    def send_packet(self, message: TCPPacket):
        """
        Serialize and send a provided packet
        """
        if not (self.simulator_host or self.simulator_port):
            log(f"Attempt to send data before receiving a destination")
            return

        self.highest_acked = message.header.sequence_number

        message_bytes = message.to_bytes()
        self.udp_socket.sendto(message_bytes, (self.simulator_host, self.simulator_port))

    def read_packet(self) -> TCPPacket:
        """
        :return: A deserialized packet read from the socket
        """
        packet_bytes, _addr = self.udp_socket.recvfrom(ANY_SOCKET_RECEIVE_PORT)

        if (self.simulator_host is None) or (self.simulator_port is None):
            self.simulator_host, self.simulator_port = _addr

        packet, _remaining_bytes = TCPPacket.from_bytes(packet_bytes)
        log(f"Received data message '{packet.data}'")

        if len(_remaining_bytes) > 0:
            log(f"Packet input for parsed {packet} has extra data {_remaining_bytes}")
        return packet

    def _in_ackable_range(self, sequence_number: int) -> bool:
        """
        :return: Whether the provided sequence number can still be acked
        """
        if not self.highest_acked:
            return True

        if sequence_number == self.highest_acked:
            # if this has already been acked, then it is not ackable
            return False

        largest_window_syn: int = (self.highest_acked + self.window_size) % MAX_UNSIGNED_INT

        if self.highest_acked < sequence_number < self.highest_received_syn or sequence_number < largest_window_syn:
            # if there has NOT been a loop around
            #   valid range is between the two values or within the window
            return True

        return False

    def _generate_error_packet_response(self) -> TCPPacket:
        """
        :return: A TCPPacket indicating that there was an error
        """
        error_ack_flags = TCPHeader.pack_flags([TCPFlag.ACKNOWLEDGEMENT, TCPFlag.ERRORS])

        # not looking at the ack anyways
        ack_val = self.highest_acked if not (self.highest_acked is None) else 0

        error_ack_header = TCPHeader(
            sequence_number=ack_val,
            flags=error_ack_flags,
            advertised_window=short(self.window_size),
            checksum=digest(EMPTY_CHECKSUM)
        )

        raw_packet = TCPPacket(header=error_ack_header, data_length=short(0), data=b'')
        return raw_packet.generate_packet_from_empty_checksum()

    def _generate_highest_ack_packet(self) -> TCPPacket:
        """
        :return: A TCPPacket with the highest possible ack
        """
        highest_ack_flags = TCPHeader.pack_flags([TCPFlag.ACKNOWLEDGEMENT])

        ack_val = self.highest_acked if not (self.highest_acked is None) else self.highest_received_syn

        highest_ack_header = TCPHeader(
            sequence_number=ack_val,
            flags=highest_ack_flags,
            advertised_window=short(self.window_size),
            checksum=digest(EMPTY_CHECKSUM)
        )

        raw_packet = TCPPacket(header=highest_ack_header, data_length=short(0), data=b'')
        return raw_packet.generate_packet_from_empty_checksum()

    def _get_sorted_window_packets(self) -> List[TCPPacket]:
        """
        :return: The window packets ordered by their sequence number
        """
        return list(sorted(self.window_packets, key=lambda p: p.header.sequence_number))

    def _check_for_malformation(self, packet: TCPPacket) -> Optional[TCPPacket]:
        """
        :return: A packet that can respond to a malformation
        """
        # if the packet is malformed, send the most-recent sequential ack possible
        received_checksum: digest = packet.header.checksum
        calculated_checksum = packet.calculate_original_checksum()

        if received_checksum != calculated_checksum:
            log("Received a mangled packet")
            # create an error packet
            return self._generate_error_packet_response()
        return None

    def _update_acked_packets(self) -> None:
        """
        Print out the packets that have been acked and can be removed from the sliding window
        """
        for pack in self.window_packets:
            if self.highest_acked is None:
                print(pack.data.decode(DATA_ENCODING), end='', flush=True)
                continue

            if pack.header.sequence_number == ((self.highest_acked + 1) % MAX_UNSIGNED_INT):
                self.highest_acked += 1
                print(pack.data.decode(DATA_ENCODING), end='', flush=True)

        self.window_packets = [pack for pack in self.window_packets
                               if self._in_ackable_range(pack.header.sequence_number)]

    def _handle_packet(self, packet: TCPPacket) -> None:
        """
        Process the received packet
        """
        error_packet = self._check_for_malformation(packet)

        if error_packet:
            self.send_packet(error_packet)
            return

        if packet in self.window_packets:
            return

        self.window_packets.append(packet)
        self.window_packets = self._get_sorted_window_packets()
        self.highest_received_syn = self.window_packets[-1].header.sequence_number

        if not self._in_ackable_range(packet.header.sequence_number):
            return

        self._update_acked_packets()

        highest_ack_packet = self._generate_highest_ack_packet()
        self.send_packet(highest_ack_packet)

    def run(self):
        """
        Actually run the packet receiver
        """
        port = self.udp_socket.getsockname()[1]
        log(f"Bound to port {port}")

        while True:
            ready_sources = select.select([self.udp_socket], [], [])[0]

            # there is only 1 read_source
            if not ready_sources:
                continue

            received_packet = self.read_packet()
            self._handle_packet(received_packet)

        return


def initialize_udp_socket() -> socket.socket:
    """
    :return: A socket bound to the UDP receiving address
    """
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(ANY_BIND_ADDRESS)

    return udp_socket


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='receive data')
    args = parser.parse_args(sys.argv[1:])

    udp_socket = initialize_udp_socket()

    sender = Receiver(packet_io=udp_socket)
    sender.run()
