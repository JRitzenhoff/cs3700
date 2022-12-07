from typing import List, Tuple, Dict, Optional, Set

import socket
import json
import select

from networks.ipaddress import IPAddress
from networks.packet import Packet, PacketType, UpdateMsg, NetworkDescription
from networks.request_handler import (
    Handler, UpdatePacketHandler, DumpPacketHandler, DataPacketHandler,
    WithdrawPacketHandler
)
from networks.utils import ConnectionType

from networks.constants import MAX_PACKET_BYTE_SIZE, DEFAULT_SELECT_SEC_TIMEOUT


class Router:
    """
    Representation of a Router from https://3700.network/docs/projects/router/
    """
    ip_conn_type_map: Dict[IPAddress, ConnectionType] = {}
    ip_socket_map: Dict[IPAddress, socket.socket] = {}
    ip_port_map: Dict[IPAddress, int] = {}

    forwarding_table: Dict[UpdateMsg, IPAddress] = {}
    """
    Save a mapping of the entire UpdateMsg (including IPAddress and SubnetMask) to the forwarding IPAddress  
    """

    revoked_addresses: Dict[IPAddress, Set[NetworkDescription]] = {}

    def __init__(self, asn: int, connections: List[Tuple[int, IPAddress, ConnectionType]]):
        self.asn = asn
        self._active = False

        for port, neighbor_ip, relation in connections:
            self.ip_port_map[neighbor_ip] = port
            self.ip_conn_type_map[neighbor_ip] = relation

    def send(self, ip_address: IPAddress, message: Packet):
        """
        Actually send the byte data to the correct IP Address on the associated socket
        """
        serialized_packet = message.serialize()
        json_packet = json.dumps(serialized_packet)

        address_socket = self.ip_socket_map[ip_address]
        address_socket.sendto(json_packet.encode('utf-8'), ('localhost', self.ip_port_map[ip_address]))

    def _select_src_ip(self, connection_socket: socket.socket) -> Optional[IPAddress]:
        """
        :return: the IPAddress associated with a provided socket
        """
        for address in self.ip_socket_map:
            if self.ip_socket_map[address] == connection_socket:
                return address

        return None

    @staticmethod
    def _assign_handler(source_address: IPAddress, packet: Packet) -> Optional[Handler]:
        """
        :return: The handler that accepts a provided packet from its associated address
        """
        if packet.type == PacketType.UPDATE:
            update_msg: UpdateMsg = packet.msg # guaranteed from the typing above
            return UpdatePacketHandler(sender=source_address, msg=update_msg)

        if packet.type == PacketType.DUMP:
            return DumpPacketHandler(sender=source_address)

        if packet.type == PacketType.DATA:
            return DataPacketHandler(sender=source_address, packet=packet)

        if packet.type == PacketType.WITHDRAW:
            withdrawals: List[NetworkDescription] = packet.msg
            return WithdrawPacketHandler(sender=source_address, revoked_paths=withdrawals)

        # print(f"** Received a {packet.type} message", flush=True)
        return None

    def _select_handlers(self, second_timeout: float) -> List[Handler]:
        """
        :param second_timeout: Number of seconds to wait before returning with active connections
        :return: A sequence of handlers that can process the received packets
        """
        handlers: List[Handler] = []

        for conn in select.select(self.ip_socket_map.values(), [], [], second_timeout)[0]:
            srcif: Optional[IPAddress] = self._select_src_ip(connection_socket=conn)

            k, addr = conn.recvfrom(MAX_PACKET_BYTE_SIZE)
            msg = k.decode('utf-8')

            print("Received message '%s' from %s" % (msg, srcif), flush=True)
            json_msg = json.loads(msg)
            packet = Packet.deserialize(**json_msg)

            assigned_handler = self._assign_handler(source_address=srcif, packet=packet)
            if assigned_handler:
                handlers.append(assigned_handler)

        return handlers

    def run(self):
        """
        Actually open the connections and run the router
        """
        print("Router at AS %s starting up" % self.asn, flush=True)

        for ip_address in self.ip_conn_type_map:
            self.ip_socket_map[ip_address] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.ip_socket_map[ip_address].bind(('localhost', 0))

            # send the handshake
            self.send(ip_address,
                      Packet(src=ip_address.network_gateway(), dst=ip_address, type=PacketType.HANDSHAKE, msg={}))

        # allow for loop control through mocking
        self._active = True

        while self._active:
            packet_handlers: List[Handler] = self._select_handlers(second_timeout=DEFAULT_SELECT_SEC_TIMEOUT)

            for handler in packet_handlers:
                handler.process(self)
