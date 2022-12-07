from typing import Any, Tuple

from dataclasses import dataclass
from enum import Enum

from networks.utils import Replaceable, Deserializable, IncrementallyDeserialize, Serializable


class MessageType(str, Enum):
    """
    Represents the two legal types of packets that can be sent
    """
    BridgeProtocolDataUnit = "bpdu",
    DataMessage = "data"


@dataclass(frozen=True, order=True)
class BPDU(Replaceable, Serializable, Deserializable):
    """
    Representation of a Bridge Protocol Data Unit as defined in https://3700.network/docs/projects/bridge/
    """
    root: str
    cost: int
    port: int
    id: str

    @property
    def source_bridge_id(self):
        return self.id

    @property
    def source_bridge_port(self):
        return self.port

    @property
    def root_id(self):
        return self.root

#     def __cmp__(self, other: 'BPDU'):
#         return extract_bpdu_tuple(self).__cmp__(extract_bpdu_tuple(other))
#
#     def __lt__(self, other: 'BPDU'):
#         return extract_bpdu_tuple(self) < extract_bpdu_tuple(other)
#
#
# def extract_bpdu_tuple(bpdu: BPDU) -> Tuple[str, int, str, int]:
#     return bpdu.root_id, bpdu.cost, bpdu.source_bridge_id, bpdu.source_bridge_port


@dataclass(frozen=True)
class Packet(Replaceable, Serializable, Deserializable):
    """
    Representation of a Packet as defined in https://3700.network/docs/projects/bridge/
    """
    source: str
    dest: str
    msg_id: int
    type: MessageType
    message: IncrementallyDeserialize(BPDU, Any)

    def __post_init__(self) -> None:
        """
        Validate that a BPDU MessageType is paired with a BPDU message
        """
        if self.type == MessageType.BridgeProtocolDataUnit and not isinstance(self.message, BPDU):
            raise ValueError(f"Associated bpdu message of is {self.message} not {BPDU}")
