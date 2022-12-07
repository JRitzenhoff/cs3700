from typing import NewType, Generator, Optional, Type, List, Tuple, Any, Dict

import struct
from enum import Enum
import hashlib
import dataclasses

from networks.constants import DEFAULT_CHECKSUM_BIT_SIZE, EMPTY_CHECKSUM

# in Python, numbers are either integers or floats (no short, long, double exist)
short = NewType('short', int)
# needed a custom variable for the checksum digest
digest = NewType('digest', bytes)


class TCPFlag(Enum):
    SYNCHRONIZATION = 0
    ACKNOWLEDGEMENT = 1
    # DATA = 2
    CONNECTION_CLOSE = 3
    ERRORS = 4


@dataclasses.dataclass(frozen=True)
class Replaceable:

    def replace(self, **kwargs) -> 'Replaceable':
        return dataclasses.replace(self, **kwargs)


@dataclasses.dataclass(frozen=True)
class StructAdapter(Replaceable):
    @classmethod
    def from_bytes(cls, raw_data: bytes) -> Tuple['StructAdapter', bytes]:
        """
        :param raw_data:
        :return: The constructed type and the remaining bytes
        """
        # all but the last field
        class_format_generator = cls.types_to_format([f.type for f in dataclasses.fields(cls)])
        format_str = ''.join(class_format_generator)
        class_byte_size = struct.calcsize(format_str)
        return cls(*struct.unpack(format_str, raw_data[:class_byte_size])), raw_data[class_byte_size:]

    @classmethod
    def type_to_struct(cls, type_val: Type) -> str:
        """
        :return: the struct string associated with the unsigned provided Type
        """
        if type_val == short:
            return 'H'

        if type_val == int:
            return 'I'

        if type_val == digest:
            return f'{DEFAULT_CHECKSUM_BIT_SIZE}s'

        raise ValueError(f"Unknown type {type_val} provided")

    @classmethod
    def types_to_format(cls, cls_field_types: List[Type]) -> str:
        # define these as big endian
        return f">{''.join(cls.type_to_struct(field_type) for field_type in cls_field_types)}"

    @classmethod
    def variable_from_bytes(cls, raw_data: bytes, var_name: str) -> Tuple[bytes, bytes]:
        variable_type, = (f.type for f in dataclasses.fields(cls) if f.name == var_name)
        variable_format = cls.types_to_format([variable_type])
        variable_byte_len = struct.calcsize(variable_format)

        raw_variable_bytes = raw_data[:variable_byte_len]

        variable, = struct.unpack(variable_format, raw_variable_bytes)

        return variable, raw_data[variable_byte_len:]

    def to_bytes(self) -> bytes:
        field_types: List[Type] = []
        field_values: List[Any] = []

        for ordered_field in dataclasses.fields(self):
            field_types.append(ordered_field.type)
            field_values.append(getattr(self, ordered_field.name))

        format_str = self.types_to_format(field_types)

        return struct.pack(format_str, *field_values)

    def variable_to_bytes(self, var_name: str) -> bytes:
        variable_type, = (f.type for f in dataclasses.fields(self) if f.name == var_name)
        variable_format = self.types_to_format([variable_type])
        return struct.pack(variable_format, getattr(self, var_name))


@dataclasses.dataclass(frozen=True)
class TCPHeader(StructAdapter):
    sequence_number: int
    """Used to detect out of order, duplicate, and missing packets"""
    flags: short
    """Used for connection establishment (SYN), acknowledgement (ACK), connection close (FIN), and errors (RST)"""
    advertised_window: short
    """Used for flow control (protecting the receiver from overloading)"""
    checksum: digest
    """Used to validate that the contained contents are valid"""

    @property
    def enum_flags(self) -> List[TCPFlag]:
        """
        :return: The bit flags as a list of Enumerations
        """
        flag_list: List[TCPFlag] = []

        for flag in TCPFlag:
            if (self.flags >> flag.value) & 0x1:
                flag_list.append(flag)

        return flag_list

    @staticmethod
    def pack_flags(flag_list: List[TCPFlag]) -> short:
        """
        :return: A packed (binary) version of a list of flags
        """
        binary_flags: short = short(0)

        for flag in flag_list:
            binary_flags |= (0x1 << flag.value)

        return binary_flags


@dataclasses.dataclass(frozen=True)
class TCPPacket(StructAdapter):
    header: TCPHeader
    data_length: short
    data: bytes

    @classmethod
    def from_bytes(cls, raw_data: bytes) -> Tuple['TCPPacket', bytes]:
        """
        :param raw_data: The raw bytes that are structured in the form of a packet
        :return: The constructed type and the remaining bytes
        """
        header, remaining_bytes = TCPHeader.from_bytes(raw_data)
        data_len, remaining_bytes = cls.variable_from_bytes(remaining_bytes, 'data_length')

        data = remaining_bytes[:data_len]
        final_bytes = remaining_bytes[data_len:]

        return cls(header, data_len, data), final_bytes

    def to_bytes(self) -> bytes:
        """
        :return: This packet in byte representation
        """
        header_bytes = self.header.to_bytes()
        data_len_bytes = self.variable_to_bytes('data_length')

        return b''.join((header_bytes, data_len_bytes, self.data))

    def _replace_checksum(self, new_checksum: digest) -> 'TCPPacket':
        """
        :param new_checksum: The new checksum that should replace the existing one
        :return: A TCPPacket that contains a checksum for the entire packet
        """
        return self.replace(header=self.header.replace(checksum=new_checksum))

    @staticmethod
    def _calculate_checksum(from_bytes: bytes) -> digest:
        """
        :return: A checksum of the DEFAULT_CHECKSUM_BIT_SIZE which accepts the argument bytes as input
        """
        raw_bytes = hashlib.blake2b(from_bytes, digest_size=DEFAULT_CHECKSUM_BIT_SIZE).digest()
        return digest(raw_bytes)

    def generate_packet_from_empty_checksum(self) -> 'TCPPacket':
        """
        :return: A TCPPacket that contains a checksum in the header which hashes the entire packet with an
        empty checksum. If a single byte in the packet is changed from calculation, the recalculation will fail.
        """
        packet = self if self.header.checksum == digest(EMPTY_CHECKSUM) \
            else self._replace_checksum(digest(EMPTY_CHECKSUM))

        checksum_bytes = self._calculate_checksum(from_bytes=packet.to_bytes())
        return packet.replace(header=packet.header.replace(checksum=checksum_bytes))

    def calculate_original_checksum(self) -> digest:
        """
        :return: A checksum which hashes the entire packet with an empty checksum value
        """
        original_packet_recreation = self._replace_checksum(digest(EMPTY_CHECKSUM))
        return self._calculate_checksum(from_bytes=original_packet_recreation.to_bytes())
