# AUTHOR: Jan Ritzenhoff

from typing import List, Tuple

import sys

from argparse import ArgumentParser, SUPPRESS as SUPPRESSED_ARGUMENT
from pathlib import Path

import remote

# ----------------------------------------------------------------
# CONSTANTS
DEFAULT_HOSTNAME = 'localhost' #'proj1.3700.network'
DEFAULT_PORT = 27993
DEFAULT_TLS_PORT = 27994
DEFAULT_TLS_STATUS = False

HOST_ARG_STR = 'host_address'
PORT_ARG_STR = 'port'
TLS_ARG_STR = 'encrypt'
# ----------------------------------------------------------------


def create_argparser() -> ArgumentParser:
    p = ArgumentParser(description="Setup Wordle server")

    # NOTE: SUPPRESSED_ARGUMENT won't add the key to the kwargs of the parse if the flag isn't provided
    p.add_argument('-a', dest=HOST_ARG_STR, required=False, default=SUPPRESSED_ARGUMENT, type=str)
    p.add_argument('-p', dest=PORT_ARG_STR, required=False, default=SUPPRESSED_ARGUMENT, type=int)
    p.add_argument('-s', dest=TLS_ARG_STR, required=False, default=SUPPRESSED_ARGUMENT, action='store_true')
    p.add_argument('-w', dest='word_list_path', required=False, default="word_list.txt", type=Path)

    return p

def parse_port(suppressed_arguments: ArgumentParser) -> int:
    """
    Determine whether a provided port, default port, or default TLS port should be used
    """
    if PORT_ARG_STR in suppressed_arguments:
        port = getattr(suppressed_arguments, PORT_ARG_STR)
    elif TLS_ARG_STR in suppressed_arguments:
        port = DEFAULT_TLS_PORT
    else:
        port = DEFAULT_PORT

    return port

def parse_host(suppressed_arguments: ArgumentParser) -> str:
    """
    Determine whether a provided or default host name should be used
    """
    return getattr(suppressed_arguments, HOST_ARG_STR) if HOST_ARG_STR in suppressed_arguments else DEFAULT_HOSTNAME

def parse_tls(suppressed_arguments: ArgumentParser) -> bool:
    """
    Determine whether to encrypt the server messages using TLS
    """
    return getattr(suppressed_arguments, TLS_ARG_STR) if TLS_ARG_STR in suppressed_arguments else DEFAULT_TLS_STATUS

def parse_arguments(args: List[str]) -> Tuple[Tuple[str, int], bool, Path]:
    parser = create_argparser()
    suppressed_args = parser.parse_args()

    host = parse_host(suppressed_args)
    port = parse_port(suppressed_args)
    encrypt = parse_tls(suppressed_args)
    word_list_path = suppressed_args.word_list_path

    return (host, port), encrypt, word_list_path


def main():
    address, use_tls, list_path = parse_arguments(sys.argv)
    
    with open(list_path, 'r') as words_file:
        word_list = [ word.strip() for word in words_file.readlines() ]
        remote.run_server(address=address, use_tls=use_tls, word_options=word_list)


if __name__ == "__main__":
    main()