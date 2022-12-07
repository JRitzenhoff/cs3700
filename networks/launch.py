#!/usr/bin/env -S python3 -u
from typing import List, Tuple

import argparse

from networks.ipaddress import IPAddress
from networks.router import Router

from networks.utils import ConnectionType

from networks.constants import ADDRESS_MATCH


def parse_connections(raw_connections: List[str]) -> List[Tuple[int, IPAddress, ConnectionType]]:
    """
    :return: Parsed connections from the input strings
    """
    parsed_pairs: List[Tuple[int, IPAddress, ConnectionType]] = []

    for raw_pair in raw_connections:
        matching = ADDRESS_MATCH.fullmatch(raw_pair)

        if not matching:
            raise AttributeError(f"Could not extract IP address from String")

        raw_port, raw_address, raw_type = matching.groups()

        parsed_pairs.append((int(raw_port), IPAddress(raw_address), ConnectionType(raw_type)))

    return parsed_pairs


def launch_router(as_number: int, connections: List[Tuple[int, IPAddress, ConnectionType]]) -> None:
    """
    Run the router itself
    """
    router = Router(as_number, connections)
    router.run()


def create_parser() -> argparse.ArgumentParser:
    """
    ./exec <asn> <port-ip.add.re.ss-[peer,prov,cust]>

    :return: Parser for an Autonomous System Number
    and a positive number of (port ip-adress, connection-type) pairings
    """
    router_parser = argparse.ArgumentParser(description='route packets')
    router_parser.add_argument('asn', type=int, help="AS number of this router")
    router_parser.add_argument('connections', metavar='connections', type=str, nargs='+', help="connections")
    return router_parser


if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()

    parsed_connections = parse_connections(raw_connections=args.connections)

    launch_router(as_number=args.asn, connections=parsed_connections)

