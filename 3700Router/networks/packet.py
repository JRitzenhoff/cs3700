from typing import Any, List

from enum import Enum
from dataclasses import dataclass, field

from networks.utils import Deserializable, ConditionalField, Serializable, Replaceable
from networks.ipaddress import IPAddress, SubnetMask


class PacketType(str, Enum):
    UPDATE = "update"
    WITHDRAW = "withdraw"
    DATA = "data"
    ROUTELESS = "no route"
    DUMP = "dump"
    TABLE = "table"
    HANDSHAKE = "handshake"


class AutonomousSystemOrigin(str, Enum):
    LOCAL = "IGP"
    REMOTE = "EGP"
    UNKNOWN = "UNK"

    def __gt__(self, other):
        """
        :return: Is this AutonomousSystemOrigin greater than the "other"
        """
        if not isinstance(other, type(self)):
            raise ValueError("Cannot compare two different types of enumerations")

        if self == other:
            return False

        # other must be lower because they're not the same
        if self == AutonomousSystemOrigin.LOCAL:
            return True

        if other == AutonomousSystemOrigin.REMOTE:
            return False

        # other MUST be lower because they're not the same and this isn't the smallest
        if self == AutonomousSystemOrigin.REMOTE:
            return True

        return False

    def __lt__(self, other):
        """
        :return: Is this AutonomousSystemOrigin less than the "other"
        """
        if self == other or self > other:
            return False

        return True


@dataclass(frozen=True)
class NetworkDescription(Deserializable, Serializable, Replaceable):
    """
    Representation of a network description containing an IP Address and Mask
    """
    network: IPAddress  # "<network prefix>"             ... Example: 12.0.0.0
    netmask: SubnetMask  # "<associated subnet mask>"     ... Example: 255.0.0.0


@dataclass(frozen=True)
class UpdatePing(NetworkDescription):
    """
    Representation of the PUBLIC ONLY fields of the updates sent out from a router

    Includes all the fields of its parent
    """
    ASPath: List[int] = field(hash=False)   # "{<nid>, [nid], ...}"  ... Examples: [1] or [3, 4] or [1, 4, 3]
    """List of autonomous systems through which this was routed. Shorted path wins"""


@dataclass(frozen=True, order=True)
class UpdateMsg(UpdatePing):
    """
    Representation of an entire Update Message

    Includes all the fields of its parent
    """
    localpref: int  # "<weight>"                       ... Example: 100
    """Weight assigned to the route. Higher the better"""
    selfOrigin: bool    # "<true|false>"
    """Whether route was added by the local administrator. True is preferred"""
    origin: AutonomousSystemOrigin  # "<IGP|EGP|UNK>",
    """Where the route originated from. Local > Remote > Unknown"""


@dataclass(frozen=True)
class DumpPing(UpdateMsg):
    """
    Representation of an entry in the DUMP table.

    Includes all the fields of its parent
    """
    peer: IPAddress  # <associated peer address>"     ... Example: 12.128.0.0


@dataclass(frozen=True)
class Packet(Deserializable, Serializable):
    """
    Representation of a Packet as defined in https://3700.network/docs/projects/router/
    """
    src: IPAddress
    dst: IPAddress
    type: PacketType
    msg: ConditionalField = ConditionalField(var_name="type",
                                             mapping={
                                                 PacketType.UPDATE: UpdateMsg,
                                                 PacketType.DATA: Any,
                                                 PacketType.ROUTELESS: Any,
                                                 PacketType.HANDSHAKE: Any,
                                                 PacketType.WITHDRAW: List[NetworkDescription],
                                                 PacketType.DUMP: Any
                                             })

    @property
    def destination_ip_address(self) -> IPAddress:
        return self.dst

    @property
    def source_ip_address(self) -> IPAddress:
        return self.src
