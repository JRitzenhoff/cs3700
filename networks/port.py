from typing import Optional, Dict, Tuple

import json
import time

from socket import socket
from enum import Enum

from networks.packet import Packet, BPDU, MessageType

from networks.constants import DEFAULT_PACKET_SIZE, MESSAGE_ENCODING, MESSAGE_SECOND_TIMEOUT, ALL_LANS_ID


# The root port is only relevant for updating the BPDU
#   a port itself doesn't need to know if it's the root, just that it's designated
class PortStatus(Enum):
    DESIGNATED = 0
    DISABLED = 1


class Port:
    """
    Representation of a Port on a networks
    """
    def __init__(self, index: int, port_num: int, comm_line: socket):
        self.index = index
        self.port_num = port_num
        self.socket = comm_line

        self.message_count = 0
        self.last_bpdu_sent: Optional[BPDU] = None

        # map all BPDUs to a (count, last_seen_time)
        self.seen_bpdus: Dict[BPDU, Tuple[int, float]] = {}

        self._status: PortStatus = PortStatus.DESIGNATED

    @property
    def status(self) -> PortStatus:
        return self._status

    @status.setter
    def status(self, new_status: PortStatus):
        if new_status != self._status:
            self._status = new_status

            if new_status == PortStatus.DISABLED:
                print(f"Disabled port: {self.index}", flush=True)
            elif new_status == PortStatus.DESIGNATED:
                print(f"Designated port: {self.index}", flush=True)

    def fileno(self):
        """
        :return: a wrapped file number for select convenience
        """
        return self.socket.fileno()

    def send_bpdu(self, bridge_id: str, bpdu: BPDU) -> None:
        """
        Send a BPDU
        """
        sendable_bpdu = bpdu.replace(id=bridge_id, port=self.index)

        self.send_packet(Packet(source=bridge_id, dest=ALL_LANS_ID,
                                msg_id=self.message_count,
                                type=MessageType.BridgeProtocolDataUnit, message=sendable_bpdu))
        self.last_bpdu_sent = sendable_bpdu

    def send_packet(self, packet: Packet) -> None:
        formatted_packet = packet.serialize()
        json_packet = json.dumps(formatted_packet)
        self._send(json_packet.encode(MESSAGE_ENCODING))

    def _send(self, message_data: bytes):
        """
         This method sends the provided "data" to the LAN, using the UDP connection.
        :param message_data: bytes to be sent
        """
        # print("Sending message on port %d" % self.index, flush=True)  # REQUIRED by assignment

        self.socket.sendto(message_data, ('localhost', self.port_num))
        self.message_count += 1

    def read_packet(self, byte_count=None) -> Packet:
        byte_count = byte_count if byte_count else DEFAULT_PACKET_SIZE

        packet_bytes, _address = self.socket.recvfrom(byte_count)
        raw_packet = packet_bytes.decode(MESSAGE_ENCODING)
        json_packet = json.loads(raw_packet)

        return Packet.deserialize(**json_packet)

    def get_flushed_bpdus(self) -> Dict[BPDU, Tuple[int, float]]:
        """
        Remove any BPDUs that are expired
        """
        return {
            key: (count, last_seen_time)
            for key, (count, last_seen_time) in self.seen_bpdus.items()
            if time.time() - last_seen_time < MESSAGE_SECOND_TIMEOUT * 2
        }

    def calculate_status_update(self) -> bool:
        """
        Calculate whether this port is a designated or disabled port
        """
        def update_status_change(new_status: PortStatus) -> bool:
            different = new_status != self.status
            self.status = new_status
            return different

        self.seen_bpdus = self.get_flushed_bpdus()

        # print(f"DBG: Seen BPDUs on port {self.index} = {self.seen_bpdus}", flush=True)

        sorted_bpdus = sorted(self.seen_bpdus)

        if len(sorted_bpdus) == 0 or self.last_bpdu_sent is None:
            return update_status_change(PortStatus.DESIGNATED)

        best_received = sorted_bpdus[0]

        if best_received < self.last_bpdu_sent:
            # print(f"DBG: PORT LT {best_received} < {self.last_bpdu_sent}", flush=True)
            # NOTE: If two ports are on the same LAN
            #   BOTH ports will receive the other's BPDU... So the
            return update_status_change(PortStatus.DISABLED)

        return update_status_change(PortStatus.DESIGNATED)