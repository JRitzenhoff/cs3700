from typing import Optional, Dict, List, Tuple, Set

import logging
import socket

import urllib.parse


from networks.http_response import HTTPResponse
from networks.constants import (
    DEFAULT_HTTP_ENCODING, LINE_ENDING,
    LOGIN_COOKIE_KEY,
    HEADER_COOKIE_PATTERN, MIDDLEWARE_COOKIE_PATTERN, HEADER_SESSION_PATTERN,
    POST_USERNAME_KEY, POST_PASSWORD_KEY, POST_MIDDLEWARE_CSRF_KEY,
    URL_MATCH_PATTERN,
    HIDDEN_FLAG_COUNT,
    HTTP_RESPONSE_CODE_VAR_NAME,
    HTTP_REDIRECT_CODE, HTTP_REDIRECT_LOCATION,
    HTTP_FORBIDDEN_CODE, HTTP_NO_FOUND_CODE, HTTP_SERVER_ERROR_CODE
)

logger = logging.getLogger(__name__)


class Crawler:
    def __init__(self, web_connection: socket.socket, username: str, password: str):
        self.web_socket = web_connection
        self.username = username
        self.password = password

        self.server_name: Optional[str] = None
        self.port_name: Optional[str] = None

    def send_request(self, request: str) -> None:
        """
        Communicate with the web_socket and send off a prepared request
        """
        # logger.debug(f"SENDING: \n{request}")
        self.web_socket.send(request.encode(DEFAULT_HTTP_ENCODING))

    def read_response(self) -> HTTPResponse:
        # read just the header
        return HTTPResponse.deserialize_response(receiver=self.web_socket)

    def get(self, url: str, cookie: Optional[str] = None) -> HTTPResponse:
        """
        Send a GET request to the URL
        """
        header_keys = [f"GET {url} HTTP/1.1", f"Host: {self.server_name}", f"Connection: keep-alive"]
        if cookie:
            header_keys.append(f"Cookie: {cookie}")
        get_header = LINE_ENDING.join(header_keys)

        get_request = f"{get_header}{LINE_ENDING}{LINE_ENDING}"

        # logger.debug(f"GET request to {self.server_name}:{self.port_name}")
        self.send_request(request=get_request)

        return self.read_response()

    @staticmethod
    def _prepare_component_str(content_components: Dict[str, str]) -> str:
        """
        :return: a URL safe query of key-value pairs
        """
        encoded_pairs: List[str] = []
        for key, value in content_components.items():
            encoded_value = urllib.parse.quote_plus(value)
            encoded_pairs.append(f"{key}={encoded_value}")

        return '&'.join(encoded_pairs)

    def post(self, url: str, body: str, cookie: Optional[str] = None) -> HTTPResponse:
        """
        Send a POST request with the provided parameters
        """
        header_keys = [f"POST {url} HTTP/1.1", f"Host: {self.server_name}",
                       f"Content-Type: application/x-www-form-urlencoded", f"Content-Length: {len(body)}"]
        if cookie:
            header_keys.append(f"Cookie: {cookie}")
        post_header = LINE_ENDING.join(header_keys)

        post_request = f"{post_header}{LINE_ENDING}{LINE_ENDING}{body}"
        self.send_request(request=post_request)

        return self.read_response()

    @staticmethod
    def _parse_header_cookie(header: Dict[str, str]) -> str:
        """
        :return: An extracted cookie from the header
        """
        raw_cookie = header.get(LOGIN_COOKIE_KEY)
        if not raw_cookie:
            raise ValueError(f"Need a cookie")

        cookie, = HEADER_COOKIE_PATTERN.findall(raw_cookie)
        return cookie

    @staticmethod
    def _parse_header_session_id(header: Dict[str, str]) -> str:
        """
        :return: An extracted session-id from the header
        """
        raw_session_id = header.get(LOGIN_COOKIE_KEY)
        if not raw_session_id:
            raise ValueError(f"Need a header session-id")
        session_id, = HEADER_SESSION_PATTERN.findall(raw_session_id)
        return session_id

    @staticmethod
    def _parse_middleware_cookie(body: str) -> str:
        """
        :return: An extracted middleware cookie from the body
        """
        middleware_cookie, = MIDDLEWARE_COOKIE_PATTERN.findall(body)
        if not middleware_cookie:
            raise ValueError(f"Need a middleware cookie")
        return middleware_cookie

    def login(self) -> Tuple[str, HTTPResponse]:
        """
        :return: The cookie received after logging in and the redirection url
        """
        get_response = self.get('/accounts/login/?next=/fakebook/')

        header_cookie = self._parse_header_cookie(get_response.header_values)
        middleware_cookie = self._parse_middleware_cookie(get_response.component)

        post_body = self._prepare_component_str(content_components={POST_USERNAME_KEY: self.username,
                                                                    POST_PASSWORD_KEY: self.password,
                                                                    POST_MIDDLEWARE_CSRF_KEY: middleware_cookie,
                                                                    'next': ''})

        cookie_str = f"csrftoken={header_cookie}"
        post_response = self.post('/accounts/login/?next=/fakebook/', body=post_body, cookie=cookie_str)

        session_id = self._parse_header_session_id(post_response.header_values)

        full_cookie = f"{header_cookie}; sessionid={session_id}"
        return full_cookie, post_response


    def extract_response_data(self, response: HTTPResponse) -> Tuple[Optional[str], Set[str]]:
        """
        :return: A flag if one has been found and a set of new URL's to parse
        """
        found_urls: Set[str] = set(URL_MATCH_PATTERN.findall(response.component))

        response_code = int(response.header_values[HTTP_RESPONSE_CODE_VAR_NAME])

        if response_code == HTTP_REDIRECT_CODE:
            redirect_url = response.header_values[HTTP_REDIRECT_LOCATION]
            found_urls.add(redirect_url)

        elif response_code in (HTTP_NO_FOUND_CODE, HTTP_FORBIDDEN_CODE):
            # don't add this to the found urls
            pass

        elif response_code == HTTP_SERVER_ERROR_CODE:
            raise ValueError(f"Need to retry")

        else:
            logger.warning(f"Unknown error code {response_code}")

        #TODO: Implment Flag return (handle multiple on one page too)
        ...






    def run(self) -> None:
        """
        Run the actual crawler
        """
        self.server_name, self.port_name = self.web_socket.getpeername()

        cookie, http_response = self.login()

        found_flags: Set[str] = set()

        seen_urls: Set[str] = set()
        queued_urls: Set[str] = set()

        found_flag, new_urls = self.extract_response_data(http_response)

        # while len(found_flags) < HIDDEN_FLAG_COUNT:
        #     pass




