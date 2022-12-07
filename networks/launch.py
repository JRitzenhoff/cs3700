from typing import List, Any, Tuple, Dict

import sys
import argparse

from socket import socket, AF_INET, SOCK_DGRAM

from networks.bridge import Bridge
from networks.port import Port

from networks.constants import BRIDGE_ADDRESS


def launch_bridge(identity: str, port_numbers: List[int]) -> None:
    ports: List[Port] = []

    for index, port_num in enumerate(port_numbers):
        port_socket = socket(AF_INET, SOCK_DGRAM)
        port_socket.bind(BRIDGE_ADDRESS)
        ports.append(Port(index, port_num, port_socket))

    bridge = Bridge(identity=identity, ports=ports)
    bridge.launch()


def create_parser() -> argparse.ArgumentParser:
    """
    Generate parser for commandline arguments:

    bridge_id: "1234" or whatever
    lan_ports: local UDP ports that we use to send/receive packets on our LAN(s)
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(description='CS 3700 networks')
    parser.add_argument('bridge_id', type=str, help="Bridge ID (e.g., 02ab)")
    parser.add_argument('lan_ports', metavar='lan_port', type=int, nargs='+', help="UDP ports to connect to LANs")

    return parser


def main() -> None:
    parser = create_parser()
    args: argparse.Namespace = parser.parse_args(sys.argv[1:])

    launch_bridge(identity=args.bridge_id, port_numbers=args.lan_ports)

    # If the output isn't as expected:
    # print(stuff, flush=True)


if __name__ == '__main__':
    main()
