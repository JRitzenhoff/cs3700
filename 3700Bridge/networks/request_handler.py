
import time

from abc import ABC, abstractmethod

from networks.port import Port, PortStatus
# from networks.bridge import Bridge  # can't import due to circular imports
from networks.packet import BPDU, Packet


class Request(ABC):
    @abstractmethod
    def handle(self, application: 'Bridge') -> bool:
        ...


class SpanningTreeRequest(Request):
    def __init__(self, received_port: Port, received_bpdu: BPDU):
        self.port = received_port
        self.bpdu = received_bpdu

    def handle(self, _application: 'Bridge') -> bool:
        """
        Updates the saved BPDUs and status of the port
        """
        if self.bpdu in self.port.seen_bpdus:
            saved_data = self.port.seen_bpdus[self.bpdu]
            count, last_time = saved_data

            self.port.seen_bpdus[self.bpdu] = (count + 1, time.time())
        else:
            self.port.seen_bpdus[self.bpdu] = (1, time.time())

        # clear out the BPDUs that haven't been seen in two cycles
        return self.port.calculate_status_update()


class ForwardingRequest(Request):
    def __init__(self, client_port: Port, packet: Packet):
        self.client_port = client_port
        self.packet = packet

    def handle(self, application: 'Bridge'):
        """
        Forwarding <source>/<msg_id> to port <port_id>
        Broadcasting <source>/<msg_id> to all active ports
        Not forwarding <source>/<msg_id>
        """
        # update the forwarding table
        # print(f"{self.packet.source} -> {self.packet.dest} on ({self.client_port.index}) w/ {application.forwarding_table}", flush=True)

        if self.packet.source not in application.forwarding_table:
            application.forwarding_table[self.packet.source] = self.client_port

        if self.client_port.status == PortStatus.DISABLED and self.client_port.index != application.root_port:
            print(f"Not forwarding {self.packet.source}/{self.packet.msg_id}", flush=True)
            return

        # if the destination is unknown and the source is legal
        #   "Broadcasting"
        if self.packet.dest not in application.forwarding_table:
            print(f"Broadcasting {self.packet.source}/{self.packet.msg_id} to all active ports", flush=True)

            for port in application.ports:
                if port != self.client_port and (port.status == PortStatus.DESIGNATED
                                                 or port.index == application.root_port):
                    # print(f"{port.index}", end='', flush=True)
                    port.send_packet(self.packet)

            return

        dest_port = application.forwarding_table[self.packet.dest]

        # if the destination is in the same lan as the source
        if dest_port == self.client_port:
            print(f"Not forwarding {self.packet.source}/{self.packet.msg_id}", flush=True)
            return

        print(f"Forwarding {self.packet.source}/{self.packet.msg_id} to port {dest_port.port_num}", flush=True)
        dest_port.send_packet(self.packet)
