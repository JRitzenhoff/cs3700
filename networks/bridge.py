from typing import Optional, List, Dict, Tuple, Generator

import select
import time
import json
import itertools

from abc import ABC, abstractmethod
from socket import socket
from collections import deque
from enum import Enum
from unittest.mock import sentinel

from networks.port import Port, PortStatus
from networks.packet import MessageType, BPDU
from networks.request_handler import SpanningTreeRequest, ForwardingRequest

from networks.constants import MESSAGE_SECOND_TIMEOUT


class Bridge:
    """
    Representation of a networking networks
    """
    def __init__(self, identity: str, ports: List[Port]):
        self.identity = identity
        self.ports: List[Port] = ports

        self.forwarding_table: Dict[str, Port] = {}

        self.last_sent_bpdu = time.time()

        self._root_port: int = sentinel.NotSet
        self._root_bpdu: BPDU = sentinel.NotSet

        self.active = False  # for testing purposes

        self.DEFAULT_ROOT_PORT: int = None
        self.DEFAULT_ROOT_BPDU: BPDU = BPDU(id=self.identity, root=self.identity, cost=0, port=self.DEFAULT_ROOT_PORT)

    @property
    def root_port(self) -> int:
        return self._root_port

    @root_port.setter
    def root_port(self, new_port: int):
        if new_port != self._root_port:
            self._root_port = new_port
            print(f"Root port: {self.root_port}", flush=True)

    @property
    def root_bpdu(self) -> BPDU:
        return self._root_bpdu

    @root_bpdu.setter
    def root_bpdu(self, new_bpdu: BPDU):
        if new_bpdu != self._root_bpdu:
            self._root_bpdu = new_bpdu
            print(f"New root: {self.root_bpdu.root_id} cost {self.root_bpdu.cost}", flush=True)

    def accept_requests(self, sec_timeout: float) -> Tuple[List[SpanningTreeRequest], List[ForwardingRequest]]:
        """
        accepts all simultaneous requests and sorts them into their respective categories
        :return:
        """
        ready_ports, _, failed_ports = select.select(self.ports, [], self.ports, sec_timeout)

        spanning_requests: List[SpanningTreeRequest] = []
        forwarding_requests: List[ForwardingRequest] = []

        for port in ready_ports:
            packet = port.read_packet()

            if packet.type == MessageType.BridgeProtocolDataUnit:
                # want all of the BPDUs to be handled first
                spanning_requests.append(SpanningTreeRequest(port, packet.message))
            elif packet.type == MessageType.DataMessage:
                forwarding_requests.append(ForwardingRequest(port, packet))
            else:
                raise NotImplementedError(f"Unknown packet type {packet.type}")

        return spanning_requests, forwarding_requests

    def launch(self):
        """
        1. Accept all selects
        2. Filter based on BPDU's and normal messages
        3. Update the spanning tree based on the BPDU packets
        4. Queue the normal messages until the tree has been re-established
        """
        print("Bridge starting up", flush=True)  # REQUIRED by assignment
        self.root_port = self.DEFAULT_ROOT_PORT
        self.root_bpdu = self.DEFAULT_ROOT_BPDU

        self.send_bpdus()

        self.active = True
        while self.active:
            simultaneous_spanning, simultaneous_forwarding = self.accept_requests(sec_timeout=MESSAGE_SECOND_TIMEOUT)

            any_port_updated: bool = False
            for spanning_request in simultaneous_spanning:
                any_port_updated = any_port_updated or spanning_request.handle(self)

            if any_port_updated:
                self.forwarding_table = self.calculate_forwarding_table()
                root_changed = self.calculated_root_changed()
                # print(f"Port update: {any_port_updated} and root updated: {root_changed}", flush=True)

            for forwarding_request in simultaneous_forwarding:
                forwarding_request.handle(self)

            if (any_port_updated and root_changed) or (time.time() - self.last_sent_bpdu > MESSAGE_SECOND_TIMEOUT):
                # print("Sending BPDUs", flush=True)
                self.send_bpdus()

    def send_bpdus(self):
        """
        BPDU - Bridge Protocol Data Unit

        This method sends a BPDU on this port.  Right now, it only sends a
        BPDU that says this networks believes its the root; obviously, this
        will need to be updated.
        """
        self.last_sent_bpdu = time.time()

        for port in self.ports:
            port.send_bpdu(bridge_id=self.identity, bpdu=self.root_bpdu)

    def _all_port_bpdus_pairs(self) -> Generator[Tuple[int, BPDU], None, None]:
        """
        :return: Generator of all the port, BPDU pairs
        """
        for port in self.ports:
            for bpdu in port.seen_bpdus:
                yield (port.index, bpdu)

    def calculated_root_changed(self) -> bool:
        """
        :return: True if the recalculated root port/bpdu has changed, otherwise False
        """
        def update_port(new_port: int) -> bool:
            different = new_port != self.root_port
            self.root_port = new_port
            return different

        def update_bpdu(new_bpdu: BPDU) -> bool:
            different = new_bpdu != self.root_bpdu
            self.root_bpdu = new_bpdu
            return different

        # print(f"DBG: Sorted pairs {list(self._all_port_bpdus_pairs())}")
        sorted_bpdus_pairs = sorted(self._all_port_bpdus_pairs(), key=lambda port_bpdu_pair: port_bpdu_pair[1])

        # if there is nothing present, this is the root
        if len(sorted_bpdus_pairs) == 0:
            return update_port(new_port=self.DEFAULT_ROOT_PORT) or update_bpdu(new_bpdu=self.DEFAULT_ROOT_BPDU)

        possible_root_port_index, possible_root_bpdu = sorted_bpdus_pairs[0]

        # if the best bpdu lists this as the root
        if possible_root_bpdu.root == self.identity:
            return update_port(new_port=self.DEFAULT_ROOT_PORT) or update_bpdu(new_bpdu=self.DEFAULT_ROOT_BPDU)

        cost_adjusted_bpdu = possible_root_bpdu.replace(cost=possible_root_bpdu.cost + 1)

        # if the possible is better than the existing root
        if cost_adjusted_bpdu < self.root_bpdu:
            possible_root_port = self.ports[possible_root_port_index]
            if possible_root_port.status != PortStatus.DISABLED:
                # this should always be the case as this port has NOT sent the best BPDU on the LAN
                raise RuntimeError(f"Some reason the port {possible_root_port_index} not disabled")

            new_bridge_bpdu = cost_adjusted_bpdu.replace(id=self.identity)
            return update_port(new_port=possible_root_port_index) or update_bpdu(new_bpdu=new_bridge_bpdu)

        return False

    def calculate_forwarding_table(self) -> Dict[str, Port]:
        """
        :return: A new forwarding table from the enabled Ports
        """
        forwarding_table: Dict[str, Port] = {}

        for p in self.ports:
            if p.status == PortStatus.DISABLED and p.index != self.root_port:
                continue

            for bpdu in p.seen_bpdus:
                if bpdu.source_bridge_id in forwarding_table:
                    # print(f"Port# {p.index} tried to add {bpdu.source_bridge_id} again even though it already exists "
                    #       f"under {forwarding_table[bpdu.source_bridge_id].index}", flush=True)

                    # ports are iterated through... Smaller port wins
                    continue

                forwarding_table[bpdu.source_bridge_id] = p

        return forwarding_table




