import re

DEFAULT_SERVER: str = "project5.3700.network"
"""
Default server provided by the assignment
"""

DEFAULT_PORT: int = 443
"""
Default port provided by the assignment
"""

# DEFAULT_HTTP_ENCODING: str = 'ascii'
DEFAULT_HTTP_ENCODING: str = 'utf-8'
"""
The default data encoding for HTTP requests/responses
"""

ASSUMED_MAX_PACKAGE_SIZE: int = 3200
"""
The initial number of bytes read from an HTTP response to parse out the total content-length
"""


LINE_ENDING: str = '\r\n'

POST_USERNAME_KEY: str = "username"
POST_PASSWORD_KEY: str = "password"
POST_MIDDLEWARE_CSRF_KEY: str = "csrfmiddlewaretoken"
DEFAULT_CSRF_KEY: str = "FGnLL5hupsJMJn9VZpdIodCLSCCzje7bwFBJJTCHDUlJsCGhyfAfolfO9tL8FVY3"

HTTP_VERSION_VAR_NAME: str = "VERSION_NAME"
HTTP_RESPONSE_CODE_VAR_NAME: str = "RESPONSE_CODE"
HTTP_STATUS_VAR_NAME: str = "RESPONSE_STATUS"

LOGIN_COOKIE_KEY: str = 'SET-COOKIE'

HTTP_REDIRECT_CODE: int = 302
HTTP_FORBIDDEN_CODE: int = 401
HTTP_NO_FOUND_CODE: int = 404

HTTP_SERVER_ERROR_CODE: int = 500


HTTP_REDIRECT_LOCATION: str = 'LOCATION'

HEADER_COOKIE_PATTERN = re.Pattern = re.compile('csrftoken=(.*); expires=')
MIDDLEWARE_COOKIE_PATTERN: re.Pattern = re.compile('<input type="hidden" name="csrfmiddlewaretoken" value="(.*)">')
HEADER_SESSION_PATTERN: re.Pattern = re.compile('sessionid=(.*); expires=')

SECRET_KEY_PATTERN: re.Pattern = re.compile('<h3 class=\'secret_flag\' style="color:red">([a-zA-Z0-9]{64})</h3>')

URL_MATCH_PATTERN: re.Pattern = re.compile('<a href="(.*)">.*</a>')

HIDDEN_FLAG_COUNT: int = 5


HTTP_HEADER_COMPONENT_SEPARATOR: str = ' '
"""
The string value that separates the three components in the HTTP Header qualifier
"""

HEADER_KEY_VAL_SEPARATOR: str = ':'
"""
The string vale that separates the key from the value in the HTTP Header lines
"""

HEADER_CONTENT_LENGTH_KEY: str = 'CONTENT-LENGTH'


DEFAULT_LOG_FILE_ENDING: str = 'log'
"""
Default file ending for a log file
"""

DEFAULT_LOG_FILE_ENDING_PATTERN: str = f'.*\.{DEFAULT_LOG_FILE_ENDING}'
"""
Regex pattern that full-matches a log-file
"""

OVERWRITE_FILE_MODE: str = 'w'
"""
File OPEN mode for overwriting a file
"""
