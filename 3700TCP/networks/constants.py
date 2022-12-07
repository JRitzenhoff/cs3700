from typing import Tuple

SENDER_DATA_SIZE: int = 1375  # 1460
"""Calculated by subtracting the TCPHeader size from the 1500 MTU of the network (and adding some buffer)"""


ANY_BIND_ADDRESS: Tuple[str, int] = ('0.0.0.0', 0)
"""Address input indicating that any address can be received on"""


ANY_SOCKET_RECEIVE_PORT: int = 65535
"""Indicator that messages can be received on any port"""


SOURCE_READ_TIMEOUT: float = 0.1
"""The amount of time in seconds that will be waited before returning the sources that have something to read"""


DATA_ENCODING: str = 'utf-8'
"""Format used to encode and decode the data"""


DEFAULT_SLIDING_WINDOW_SIZE: int = 6
"""The initial and default sliding window size as defined in the Networks powerpoint slides"""


DEFAULT_CHECKSUM_BIT_SIZE: int = 16
"""The digest size used by the black2b library to generate a checksum"""


EMPTY_CHECKSUM: bytes = b'0' * DEFAULT_CHECKSUM_BIT_SIZE
"""An uninitialized checksum"""


DEFAULT_SYN_STARTING_NUMBER: int = 1  # 45
"""This number amuses me in hex"""


DEFAULT_ROUND_TRIP_SEC_TIME: float = 1
"""The default number of seconds that a packet is expected to travel between sender and receiver"""


RTT_MULTIPLIER: int = 2
"""The default multiplier for the Round Trip Time before resending a packet"""


MAX_UNSIGNED_INT: int = (0x1 << 33) - 0x1
"""The maximum unsigned 32-bit integer is 1 smaller than the next higher power of 2"""
