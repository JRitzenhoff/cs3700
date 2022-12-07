import re
from typing import Tuple, Optional

import logging
import argparse
import socket
import ssl

from datetime import datetime
from pathlib import Path

from networks.crawler import Crawler
from networks.constants import (
    DEFAULT_SERVER, DEFAULT_PORT,
    DEFAULT_LOG_FILE_ENDING, DEFAULT_LOG_FILE_ENDING_PATTERN, OVERWRITE_FILE_MODE
)

logger = logging.getLogger(__name__)


def create_logging_directory_for_path(output_path: Path) -> None:
    """
    """
    base_name = output_path.parts[-1]
    pattern = re.compile(DEFAULT_LOG_FILE_ENDING_PATTERN)
    if pattern.fullmatch(base_name):
        # make the parent directories
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        output_path.mkdir(parents=True, exist_ok=True)


def configure_global_debug_logger(output_path: Optional[Path]) -> None:
    """
    Create necessary directories to log to
    """
    if not output_path:
        return

    if not output_path.exists():
        create_logging_directory_for_path(output_path=output_path)

    if output_path.is_dir():
        # generate a file_name
        run_timestamp = datetime.today()
        log_file_name = run_timestamp.strftime(f"%Y_%m_%d-%H_%M.{DEFAULT_LOG_FILE_ENDING}")
        output_path = output_path / log_file_name

    logging.basicConfig(filename=output_path, level=logging.DEBUG, filemode=OVERWRITE_FILE_MODE)


def create_cmdline_parser() -> argparse.ArgumentParser:
    """
    :return: A commandline parser for the webcrawler
    """
    cmdline_parser = argparse.ArgumentParser(description='crawl Fakebook')
    cmdline_parser.add_argument('-s', dest="server", type=str, default=DEFAULT_SERVER, help="The server to crawl")
    cmdline_parser.add_argument('-p', dest="port", type=int, default=DEFAULT_PORT, help="The port to use")
    cmdline_parser.add_argument('username', type=str, help="The username to use")
    cmdline_parser.add_argument('password', type=str, help="The password to use")
    cmdline_parser.add_argument('-o', dest="log_path", type=Path, help="The output path for the log file")

    return cmdline_parser


def launch_crawler(address: Tuple[str, int], username: str, password: str) -> None:
    """
    Open a secure socket and launch the actual web-crawler
    """
    ssl_context = ssl.create_default_context()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as web_socket:
        web_socket.connect(address)

        hostname, _port = address
        with ssl_context.wrap_socket(web_socket, server_hostname=hostname) as secure_web_socket:
            web_crawler = Crawler(web_connection=secure_web_socket, username=username, password=password)
            web_crawler.run()


if __name__ == '__main__':
    parser = create_cmdline_parser()
    args = parser.parse_args()

    configure_global_debug_logger(output_path=args.log_path)
    launch_crawler(address=(args.server, args.port), username=args.username, password=args.password)
