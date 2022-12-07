
from typing import Any, Tuple, Union

import struct

from dataclasses import dataclass, field, InitVar

from networks.utils import Serializable


@dataclass(frozen=True, order=True)
class QuadrupleOctet(Serializable):
    address: InitVar[str]
    binary: int = field(init=False)

    def __post_init__(self, str_address: str) -> None:
        """
        Split the string address into 4 octets and pack into a single integer.
        """
        first_octet, second_octet, third_octet, fourth_octet = str_address.split('.')

        # 'B' is an unsigned byte
        octet_bytes = struct.pack(">BBBB", int(first_octet), int(second_octet),
                                  int(third_octet), int(fourth_octet))

        # 'I' is an unsigned integer
        # '>' indicates BIG endian (most significant byte first)
        integer_conversion, = struct.unpack(">I", octet_bytes)

        # integer_conversion = (int(a1) << 24) + (int(a2) << 16) + (int(a3) << 8) + int(a4)
        object.__setattr__(self, 'binary', integer_conversion)

    def network_gateway(self) -> 'IPAddress':
        """
        :return: The lowest IP Address in this network
        """
        o1, o2, o3, o4 = self._split_into_octets(self.binary)
        return IPAddress(self._stringify_octets(o1, o2, o3, 1))

    @staticmethod
    def _split_into_octets(binary_val: int) -> Tuple[int, int, int, int]:
        """
        :return: This IP Address represented by its four components
        """
        octet_bytes = struct.pack(">I", binary_val)
        return struct.unpack(">BBBB", octet_bytes)

    @classmethod
    def from_binary(cls, binary_val: int) -> 'Octet':
        """
        :return: An instance of this class given a binary representation of the QuadrupleOctet
        """
        return cls(cls._stringify_octets(*cls._split_into_octets(binary_val)))

    @staticmethod
    def _stringify_octets(o1: Union[int, str], o2: Union[int, str],
                          o3: Union[int, str], o4: Union[int, str]) -> str:
        """
        :return: The QuadrupleOctet string representation
        """
        return f"{o1}.{o2}.{o3}.{o4}"

    def __repr__(self):
        """
        :return: Debugging version of this object
        """
        return f"{type(self).__name__}({self.__str__()})"

    def __str__(self):
        """
        :return: String representation of the IPAddress
        """
        return self._stringify_octets(*self._split_into_octets(self.binary))

    def serialize(self) -> Any:
        """
        :return: JSON compatible equivalent of this Packet instance
        """
        return self.__str__()

    @property
    def BIT_LENGTH(self) -> int:
        """
        :return: read-only number of bits in the QuadrupleOctet
        """
        return 32


class SubnetMask(QuadrupleOctet):
    @property
    def length(self) -> int:
        """
        :return: Maximum number of consecutive 1's
        """
        count = 0
        for i in range(31, -1, -1):
            if (self.binary >> i) & 0x1 != 0x1:
                return count
            count += 1
        return count

    @property
    def prefix_shift_amount(self) -> int:
        """
        :return: The number of right-shifts required to match the prefix
        """
        return self.BIT_LENGTH - self.length


class IPAddress(QuadrupleOctet):
    """
    Representation of an IP Address
    """
    ...


