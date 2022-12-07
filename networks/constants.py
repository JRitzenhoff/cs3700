import re

ADDRESS_MATCH = re.compile("(\d+)-(\d+.\d+.\d+.\d+)-(\w+)")
"""
Regex compilation for an IP address input <port-ipaddress-type>
"""

MAX_PACKET_BYTE_SIZE: int = 65535
"""
Value set by the starter code
"""

DEFAULT_SELECT_SEC_TIMEOUT: float = 0.1
"""
Value set by the starter code
"""
