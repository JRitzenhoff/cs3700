import urllib.parse
from typing import Optional, Tuple, Dict

import logging
from dataclasses import dataclass

from enum import Enum

from networks.constants import (
    ASSUMED_MAX_PACKAGE_SIZE, DEFAULT_HTTP_ENCODING, LINE_ENDING,
    HTTP_VERSION_VAR_NAME, HTTP_RESPONSE_CODE_VAR_NAME, HTTP_STATUS_VAR_NAME,
    HTTP_HEADER_COMPONENT_SEPARATOR, HEADER_KEY_VAL_SEPARATOR,
    HEADER_CONTENT_LENGTH_KEY
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HTTPResponse:
    header_values: Dict[str, str]
    component: str

    @classmethod
    def deserialize_header(cls, receiver) -> Tuple[Dict[str, str], str]:
        """
        :return: The dictionary of upper case header keys mapped to their values and also the remaining read contents
        """
        assumed_package_bytes = receiver.recv(ASSUMED_MAX_PACKAGE_SIZE)
        response_str: str = assumed_package_bytes.decode(DEFAULT_HTTP_ENCODING)

        header_line, _endline_str, remaining_response = response_str.partition(LINE_ENDING)
        http_version, response_code, *status = header_line.split(HTTP_HEADER_COMPONENT_SEPARATOR)

        header_values = {
            HTTP_VERSION_VAR_NAME: http_version,
            HTTP_RESPONSE_CODE_VAR_NAME: response_code,
            HTTP_STATUS_VAR_NAME: HTTP_HEADER_COMPONENT_SEPARATOR.join(status)
        }

        previous_remaining_response: str = ''
        while True:
            line, _endline_str, read_response = remaining_response.partition(LINE_ENDING)

            if not line:
                # this is the end of the header
                break

            if line == remaining_response:
                # reached the end of the line
                logger.warning(f"Read the response to completion {remaining_response}")
                break

            remaining_response = read_response

            if previous_remaining_response == remaining_response:
                logger.warning(f"Responses were the same {previous_remaining_response} \n\n "
                               f"AND \n\n {remaining_response}")
                break

            header_key, _sep, header_value = line.partition(HEADER_KEY_VAL_SEPARATOR)
            header_values[header_key.upper()] = header_value.lstrip()

            previous_remaining_response = remaining_response

        return header_values, remaining_response

    @classmethod
    def deserialize_response(cls, receiver) -> 'HTTPResponse':
        """
        :return: An HTTP Response deserialized from
        """
        header_dictionary, remaining_message = cls.deserialize_header(receiver=receiver)
        raw_content_size = header_dictionary.get(HEADER_CONTENT_LENGTH_KEY)

        if raw_content_size:
            content_size = int(raw_content_size)
            remaining_content_size = content_size - len(remaining_message)

            if remaining_content_size > 0:
                additional_bytes = receiver.recv(remaining_content_size)
                additional_message = additional_bytes.decode(DEFAULT_HTTP_ENCODING)
                remaining_message = ''.join((remaining_message, additional_message))

        return cls(header_dictionary, remaining_message)

