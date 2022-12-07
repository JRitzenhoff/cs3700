from typing import List, Optional, Tuple, Dict, Any

from abc import ABC, abstractmethod
from collections import defaultdict

from networks.packet import Packet, PacketType, UpdateMsg, UpdatePing, DumpPing, NetworkDescription
from networks.ipaddress import IPAddress, SubnetMask

from networks.utils import ConnectionType


class Handler(ABC):
    """
    Abstract implementation for a Handler that accepts a 'Router' and processes input data
    """
    @abstractmethod
    def process(self, router: 'Router') -> None:
        ...

    @staticmethod
    def matched_subnet(destination_ip: IPAddress, entry: UpdateMsg) -> Optional[int]:
        """
        :return: Netmask length if the Destination IP works with the entry IP and subnet, otherwise None
        """
        match_shift = entry.netmask.prefix_shift_amount

        if (entry.network.binary >> match_shift) == (destination_ip.binary >> match_shift):
            return entry.netmask.length

        return None


class UpdatePacketHandler(Handler):
    """
    Implementation of a Handler that accepts Update Messages
    """

    def __init__(self, sender: IPAddress, msg: UpdateMsg):
        self.sender_ip: IPAddress = sender
        self.update_msg: UpdateMsg = msg

    def process(self, router: 'Router') -> None:
        """
        Accept an Update Message from a sender, update the forwarding table, and forward information
        """
        # print(f"** Received an UPDATE message on {self.sender_ip}", flush=True)

        # Add an entry in the forwarding table
        router.forwarding_table[self.update_msg] = self.sender_ip

        # Potentially send copies of the announcement ot neighboring routers
        update_data = UpdatePing(network=self.update_msg.network,
                                 netmask=self.update_msg.netmask,
                                 ASPath=[router.asn] + self.update_msg.ASPath)

        self._inform_neighbors(router, PacketType.UPDATE, inform_data=update_data)

    def _inform_neighbors(self, router: 'Router', inform_type: PacketType, inform_data: Any):
        """
        Pass along information to neighbors based on their connection status
        """
        src_conn_type = router.ip_conn_type_map[self.sender_ip]

        for (network_ip, socket_obj) in router.ip_socket_map.items():
            if network_ip == self.sender_ip:
                continue

            network_conn_type = router.ip_conn_type_map[network_ip]

            if (src_conn_type in (ConnectionType.PEER, ConnectionType.PROVIDER) and
                    not network_conn_type == ConnectionType.CUSTOMER):
                # Update received from a peer or a provider only goes to your customers
                continue

            router.send(network_ip,
                        Packet(src=network_ip.network_gateway(), dst=network_ip, type=inform_type, msg=inform_data))


class DumpPacketHandler(Handler):
    """
    Implementation of a Handler that accepts Dump Messages
    """

    def __init__(self, sender: IPAddress):
        self.sender_ip: IPAddress = sender

    def process(self, router: 'Router') -> None:
        """
        Accept a Dump Message from a sender, populate the Dump Table, and forward information
        """
        # print(f"** Received a DUMP message on {self.sender_ip}", flush=True)

        full_table: List[DumpPing] = []

        aggregated_table = self._aggregate_forwarding_table(router)

        for forwarding_update, forwarding_ip in aggregated_table.items():
            entry = DumpPing(
                network=forwarding_update.network,
                netmask=forwarding_update.netmask,
                peer=forwarding_ip,
                localpref=forwarding_update.localpref,
                ASPath=forwarding_update.ASPath,
                selfOrigin=forwarding_update.selfOrigin,
                origin=forwarding_update.origin
            )

            full_table.append(entry)

        router.send(self.sender_ip, Packet(src=self.sender_ip.network_gateway(), dst=self.sender_ip,
                                           type=PacketType.TABLE, msg=full_table))

    @classmethod
    def _aggregate_forwarding_table(cls, router: 'Router') -> Dict[UpdateMsg, IPAddress]:
        """
        Aggregate entries in the forwarding table if they are:
            (1) adjacent numerically
            (2) forward to the same next-hop router
            (3) have the same attributes (e.g., localpref, origin, etc.)

        For example, the networks
            192.168.0.0/24 and 192.168.1.0/24 are numerically adjacent.

            Assuming the next-hop router and attributes are the same,
            these can be combined into 192.168.0.0/23
        """
        # sort by sending IPAddress
        ip_filters = defaultdict(list)

        for update_msg, ip_addr in router.forwarding_table.items():
            ip_filters[ip_addr].append(update_msg)

        aggregrated_table = {}
        for ip_addr, aggregration_group in ip_filters.items():
            aggregrated = cls._aggregate_msg_group(aggregration_group)

            for update_msg in aggregrated:
                aggregrated_table[update_msg] = ip_addr

        return aggregrated_table

    @classmethod
    def _aggregate_msg_group(cls, group: List[UpdateMsg]) -> List[UpdateMsg]:
        """
        :param group: A Sequence of Update Messages that are all forwarded to the same neighbor
        :return: An aggregated
        """
        parsed_list = list(group)
        last_edited: Optional[UpdateMsg] = None

        while parsed_list[0] != last_edited:
            first_element = parsed_list.pop(0)

            if last_edited is None:
                last_edited = first_element

            combinations: List[UpdateMsg] = cls._find_matching_messages(reference=first_element, options=parsed_list)

            if combinations:
                # actually combine the combinations
                for combo in combinations:
                    parsed_list.remove(combo)

                last_edited = cls._calculate_aggregation(matches=[first_element] + combinations)
                parsed_list.append(last_edited)
            else:
                parsed_list.append(first_element)

        return parsed_list

    @classmethod
    def _find_matching_messages(cls, reference: UpdateMsg, options: List[UpdateMsg]) -> List[UpdateMsg]:
        """
        :param reference: The Update Message to which all others should be compared
        :param options: The Update Messages that should be searched for matches
        :return: The matches in the option group for the reference
        """
        matches: List[UpdateMsg] = []

        bit_shift_count = (reference.netmask.prefix_shift_amount + 1)

        for remaining_element in options:
            # if everything is the same except for the network
            if reference == remaining_element.replace(network=reference.network):
                first_network_prefix = reference.network.binary >> bit_shift_count
                remaining_network_prefix = remaining_element.network.binary >> bit_shift_count

                if first_network_prefix == remaining_network_prefix:
                    matches.append(remaining_element)

        return matches

    @classmethod
    def _calculate_aggregation(cls, matches: List[UpdateMsg]) -> UpdateMsg:
        """
        :param matches: A list of Update Messages that can all be combined based on rules defined in
        https://3700.network/docs/projects/router/#aggregation
        :return: The aggregated update message given a list of matches
        """
        sorted_messages = sorted(matches)
        smallest_message: UpdateMsg = sorted_messages[0]

        # need to remove another bit from the netmask
        bit_shift_count = (smallest_message.netmask.prefix_shift_amount + 1)

        updated_netmask = SubnetMask('255.255.255.255').binary >> bit_shift_count
        updated_netmask = updated_netmask << bit_shift_count

        return smallest_message.replace(netmask=SubnetMask.from_binary(updated_netmask))


class DataPacketHandler(Handler):
    """
    Implementation of a Handler that accepts Data Messages
    """

    def __init__(self, sender: IPAddress, packet: Packet):
        self.sender_ip: IPAddress = sender
        self.packet: Packet = packet

    def process(self, router: 'Router') -> None:
        """
        Accept a Data Message from a sender, find the largest prefix match, and forward data accordingly
        """
        # print(f"** Received a DATA message on {self.sender_ip}", flush=True)
        largest_ip_address: Optional[IPAddress] = None
        largest_update: Optional[UpdateMsg] = None
        largest_mask: int = 0

        for forwarding_update, forwarding_ip_addr in router.forwarding_table.items():
            # iterate through the forwarding table and find the best match
            mask_match: Optional[int] = self.matched_subnet(self.packet.destination_ip_address, entry=forwarding_update)

            if mask_match is None:
                continue

            if mask_match > largest_mask or (mask_match == 0 and largest_mask == 0 and largest_update is None):
                # if the new match is better, update the found one
                largest_ip_address, largest_mask, largest_update = (forwarding_ip_addr, mask_match, forwarding_update)
                continue

            if mask_match == largest_mask:
                # if the new match is equivalent, compare the other fields
                largest_ip_address, largest_update, largest_mask = self._determine_best_route(
                    largest_update_message=largest_update, largest_ip_address=largest_ip_address,
                    contending_update_msg=forwarding_update, contending_ip_address=forwarding_ip_addr)

        if not (largest_ip_address is None):
            self._forward_packet(router=router, next_ip_address=largest_ip_address,
                                 destination=self.packet.destination_ip_address)

    @staticmethod
    def _determine_best_route(largest_update_message: UpdateMsg, largest_ip_address: IPAddress,
                              contending_update_msg: UpdateMsg, contending_ip_address: IPAddress) -> \
            Tuple[IPAddress, NetworkDescription, int]:
        """
        Match with the longest prefix IPAddress/Mask.
        """
        largest_return = (largest_ip_address, largest_update_message, largest_update_message.netmask.length)
        contending_return = (contending_ip_address, contending_update_msg, contending_update_msg.netmask.length)

        # * The entry with the highest localpref wins. If the localprefs are equal…
        if largest_update_message.localpref > contending_update_msg.localpref:
            return largest_return

        if largest_update_message.localpref < contending_update_msg.localpref:
            return contending_return

        # * The entry with selfOrigin as true wins. If all selfOrigins are the equal…
        if not (largest_update_message.selfOrigin and contending_update_msg.selfOrigin):
            if largest_update_message.selfOrigin:
                return largest_return

            if contending_update_msg.selfOrigin:
                return contending_return

        # * The entry with the shortest ASPath wins. If multiple entries have the shortest length…
        if len(largest_update_message.ASPath) < len(contending_update_msg.ASPath):
            return largest_return

        if len(largest_update_message.ASPath) > len(contending_update_msg.ASPath):
            return contending_return

        # * The entry with the best origin wins, were IGP < EGP < UNK. If multiple entries have the best origin…
        if largest_update_message.origin < contending_update_msg.origin:
            return largest_return

        if largest_update_message.origin > contending_update_msg.origin:
            return contending_return

        # * The entry from the neighbor router (i.e., the src of the update message) with the lowest IP address.
        if largest_ip_address.binary < contending_ip_address.binary:
            return largest_return

        return contending_return

    def _forward_packet(self, router: 'Router', next_ip_address: IPAddress, destination: IPAddress) -> None:
        """
        Assuming that your router was able to find a entry for the given data message,
        the last step before sending it along is to make sure that the packet is being forwarded legally.
        """

        source_relation: ConnectionType = router.ip_conn_type_map[self.sender_ip]

        # * If the source router or destination router is a customer, then your router should forward the data.
        if source_relation == ConnectionType.CUSTOMER:
            router.send(next_ip_address, Packet(src=self.sender_ip.network_gateway(), dst=destination,
                                                type=PacketType.DATA, msg=self.packet.msg))
            return

        destination_relation: ConnectionType = router.ip_conn_type_map[next_ip_address]

        # If the source router is a peer or a provider, and the destination is a peer or a provider, then drop
        if (source_relation in (ConnectionType.PEER, ConnectionType.PROVIDER) and
                destination_relation in (ConnectionType.PEER, ConnectionType.PROVIDER)):

            # If your router drops a data message due to these restrictions,
            router.send(self.sender_ip, Packet(src=self.sender_ip.network_gateway(), dst=self.sender_ip,
                                               type=PacketType.ROUTELESS, msg={}))
            return

        # otherwise, forward the data
        router.send(next_ip_address, Packet(src=self.sender_ip.network_gateway(), dst=destination,
                                            type=PacketType.DATA, msg=self.packet.msg))


class WithdrawPacketHandler(Handler):
    """
    Implementation of a Handler that accepts Withdraw Messages
    """

    def __init__(self, sender: IPAddress, revoked_paths: List[NetworkDescription]):
        self.sender_ip: IPAddress = sender
        self.withdrawals: List[NetworkDescription] = revoked_paths

    def process(self, router: 'Router') -> None:
        """
        Accept a Data Message from a sender, find the largest prefix match, and forward data accordingly
        """
        if self.sender_ip not in router.revoked_addresses:
            router.revoked_addresses[self.sender_ip] = set()

        # (1) save a copy of the revocation, in case you need it later
        router.revoked_addresses[self.sender_ip].update(set(self.withdrawals))

        # (2) remove the dead entry from the forwarding table
        for network_description in self.withdrawals:
            associated_update = self._get_associated_update(router, network_description)

            if associated_update:
                del router.forwarding_table[associated_update]

        # Potentially send copies of the announcement ot neighboring routers
        self._inform_neighbors(router)

    def _inform_neighbors(self, router: 'Router') -> None:
        """
        (3) possibly send copies of the revocation to other neighboring routers
            As with update messages, your router may need to send copies of the route revocation to its neighbors.
            This follows the same set of rules as update messages.

            Your route announcements must obey the following rules:
                * Update received from a customer: send updates to all other neighbors
                * Update received from a peer or a provider: only send updates to your customers
        """
        src_conn_type: ConnectionType = router.ip_conn_type_map[self.sender_ip]

        for (network_ip, socket_obj) in router.ip_socket_map.items():
            if network_ip == self.sender_ip:
                continue

            network_conn_type = router.ip_conn_type_map[network_ip]

            if (src_conn_type in (ConnectionType.PEER, ConnectionType.PROVIDER) and
                    not network_conn_type == ConnectionType.CUSTOMER):
                # Update received from a peer or a provider only goes to your customers
                continue

            router.send(network_ip, Packet(src=network_ip.network_gateway(), dst=network_ip,
                                           type=PacketType.WITHDRAW, msg=self.withdrawals))

    def _get_associated_update(self, router: 'Router', network_description: NetworkDescription) -> Optional[UpdateMsg]:
        """
        :param network_description: The withdrawal request to find in the forwarding table
        :return: The Update Message associated with a withdrawal request if it exists, Otherwise None
        """
        for update_msg, ip_address in router.forwarding_table.items():
            if ((update_msg.network == network_description.network
                 and update_msg.netmask == network_description.netmask)
                    and ip_address == self.sender_ip):
                return update_msg

        return None





