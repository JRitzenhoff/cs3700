from typing import Tuple, Optional, List, TextIO, Dict

import argparse
import socket
import select
import sys
import time

from networks.packet import TCPPacket, TCPHeader, TCPFlag, short, digest

from networks.constants import (
    ANY_BIND_ADDRESS, ANY_SOCKET_RECEIVE_PORT,
    SOURCE_READ_TIMEOUT, SENDER_DATA_SIZE,
    DEFAULT_SLIDING_WINDOW_SIZE, DEFAULT_SYN_STARTING_NUMBER,
    DEFAULT_ROUND_TRIP_SEC_TIME, RTT_MULTIPLIER,
    MAX_UNSIGNED_INT,
    EMPTY_CHECKSUM
)


def log(message: str) -> None:
    sys.stderr.write(f"{message}\n")
    sys.stderr.flush()


class Sender:
    """
    Representation of a TCP Sender
    """

    def __init__(self, text_reader: TextIO, packet_io: socket.socket, packet_address: Tuple[str, int]):
        self.text_reader = text_reader
        self.packet_io = packet_io
        self.packet_address = packet_address

        self.packets_in_flight: Dict[TCPPacket, float] = {}

        self.sliding_window_size: int = DEFAULT_SLIDING_WINDOW_SIZE
        self.syn_number = DEFAULT_SYN_STARTING_NUMBER
        self.ack_number = DEFAULT_SYN_STARTING_NUMBER

        self.sent_all_messages = False

    def send_packet(self, message: TCPPacket) -> None:
        """
        :return: Accept a packet, serialize it, and send it on the socket
        """
        log(f"Sending message '{message.data}'")  # REQUIRED

        packet_bytes = message.to_bytes()
        self.packet_io.sendto(packet_bytes, self.packet_address)

        # update the packet's that are currently in flight
        self.packets_in_flight[message] = time.time()

    def read_packet(self) -> TCPPacket:
        """
        :return: A deserialized packet read from the socket
        """
        packet_bytes, _addr = self.packet_io.recvfrom(ANY_SOCKET_RECEIVE_PORT)
        packet, _remaining_bytes = TCPPacket.from_bytes(packet_bytes)
        log(f"Received message '{packet.data}'")

        if len(_remaining_bytes) > 0:
            log(f"Packet input for parsed {packet} has extra data {_remaining_bytes}")
        return packet

    def _select_ready_sources(self) -> List[TextIO]:
        """
        :return: the sources in this sender that are ready to read
        """
        data_sources = [self.packet_io]

        if len(self.packets_in_flight) < self.sliding_window_size:
            data_sources.append(self.text_reader)

        # wait for the "ready for reading", "ready for writing" and "has error" lists
        #   only the reading is being waited on here
        return select.select(data_sources, [], [], SOURCE_READ_TIMEOUT)[0]

    def _prepare_send_packet(self) -> Optional[TCPPacket]:
        """
        :return: a prepared packet based on the reader input
        """
        byte_data = self.text_reader.buffer.read(SENDER_DATA_SIZE)
        byte_count = len(byte_data)
        if byte_count == 0:
            return None

        binary_flags: short = TCPHeader.pack_flags([TCPFlag.SYNCHRONIZATION])

        empty_checksum_packet = TCPPacket(
            header=TCPHeader(sequence_number=self.syn_number,
                             flags=binary_flags,
                             advertised_window=short(self.sliding_window_size),
                             checksum=digest(EMPTY_CHECKSUM)),
            data_length=short(byte_count),
            data=byte_data)

        return empty_checksum_packet.generate_packet_from_empty_checksum()

    def _in_ackable_range(self, sequence_number: int) -> bool:
        """
        :return: Whether the provided sequence number can still be acked
        """

        if sequence_number == self.ack_number:
            return False

        if self.ack_number > self.syn_number and self.syn_number < sequence_number < self.ack_number:
            # handles when the syn number has looped around
            return False

        if self.ack_number < self.syn_number and \
                (sequence_number < self.ack_number or sequence_number > self.syn_number):
            # handles the normal case
            return False

        return True

    def _packets_still_in_flight(self) -> Dict[TCPPacket, float]:
        """
        Removes the packets in flight that have been acked
        """
        # log(f"ACK {repr(self.ack_number)} == SYN {repr(self.syn_number)}")
        if self.ack_number == self.syn_number:
            # if the two are caught up, there are no more packets in flight
            return {}

        return {
            packet: sent_time for packet, sent_time in self.packets_in_flight.items()
            if self._in_ackable_range(packet.header.sequence_number)
        }

    def _handle_response_packet(self, sent_packet: Optional[TCPPacket], received_packet: TCPPacket) -> \
            Optional[TCPPacket]:
        """
        :param packet: The packet that was received as a response from the receiver
        :param window_packets: The current packets in flight
        :return: A possible reply to the receiver response and the current packets that haven't been received
        """
        if not sent_packet or (TCPFlag.ERRORS in received_packet.header.enum_flags):
            # determine which packet the ack/nack is for
            return self._find_matching_packet_from_sequence_number(self.ack_number)

        if sent_packet and not self._in_ackable_range(received_packet.header.sequence_number):
            # Do nothing... This is a duplicate
            return None

        # update the number that has most recently been acked
        self.ack_number = sent_packet.header.sequence_number
        return None

    def _find_matching_packet_from_sequence_number(self, sequence_number: int) -> Optional[TCPPacket]:
        """
        :return: The packet in_flight that matches the syn_number
        """
        for packet, _sent_time in self.packets_in_flight.items():
            if packet.header.sequence_number == sequence_number:
                return packet

        return None

    def _find_matching_sent_packet(self, received_packet: TCPPacket) -> Optional[TCPPacket]:
        """
        :param received_packet:
        :return: The packet in_flight that matches the syn_number of the received
        """
        # check whether the packet is received correctly
        received_checksum: digest = received_packet.header.checksum
        calculated_checksum: digest = received_packet.calculate_original_checksum()

        if received_checksum != calculated_checksum:
            return None

        return self._find_matching_packet_from_sequence_number(received_packet.header.sequence_number)

    def _resend_timeout_packets(self):
        """
        Find the packets that have timedout and resend them
        """
        for packet, sent_time in self.packets_in_flight.items():
            if time.time() - sent_time > RTT_MULTIPLIER * DEFAULT_ROUND_TRIP_SEC_TIME:
                self.send_packet(packet)

    def run(self) -> None:
        """
        Actually run the packet receiver
        """
        self.sent_all_messages = False

        while True:
            for source in self._select_ready_sources():
                if source == self.packet_io:
                    response_packet = self.read_packet()
                    sent_packet_match = self._find_matching_sent_packet(received_packet=response_packet)
                    resend_packet = self._handle_response_packet(sent_packet=sent_packet_match,
                                                                 received_packet=response_packet)
                    self.packets_in_flight = self._packets_still_in_flight()

                    if resend_packet:
                        self.send_packet(resend_packet)
                    if self.sent_all_messages and not self.packets_in_flight:
                        break
                elif source == self.text_reader and not self.sent_all_messages:
                    prepared_packet = self._prepare_send_packet()

                    if not prepared_packet:
                        self.sent_all_messages = True
                        log("All done!")
                        if not self.packets_in_flight:
                            break
                        continue

                    self.send_packet(prepared_packet)
                    self.syn_number += 1 % MAX_UNSIGNED_INT
            else:
                self._resend_timeout_packets()
                continue
            # only reached by break in the "for" loop
            log("Breaking out of the for loop")
            break

        return None


def create_parser() -> argparse.ArgumentParser:
    """
    :return: A parser for the `./3700send <recv_host> <recv_port>`
    """
    parser = argparse.ArgumentParser(description='send data')
    parser.add_argument('host', type=str, help="Remote host to connect to")
    parser.add_argument('port', type=int, help="UDP port number to connect to")

    return parser


def initialize_udp_socket(simulator_host: str, simulator_port: int) -> socket.socket:
    """
    :return: A UDP socket that binds to the provided host and port
    """
    log(f"Sender starting up using port {simulator_port}")

    simulator_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    simulator_socket.bind(ANY_BIND_ADDRESS)

    return simulator_socket


if __name__ == "__main__":
    sender_parser = create_parser()
    sender_args = sender_parser.parse_args(sys.argv[1:])

    udp_socket = initialize_udp_socket(simulator_host=sender_args.host, simulator_port=sender_args.port)

    sender = Sender(text_reader=sys.stdin, packet_io=udp_socket, packet_address=(sender_args.host, sender_args.port))
    sender.run()
