# AUTHOR: Jan Ritzenhoff

from typing import Tuple, List, Any, Callable, Dict, Generator

import socket
import ssl
import json
import random

from dataclasses import dataclass
from enum import Enum

from wordle import (
    Wordle,
    LetterIndicator,
    InvalidGuessException, InvalidPlayerException
)

# ----------------------------------------------------------------
# CONSTANTS

DEFAULT_BUFFER = 1024
DEFAULT_ENCODING = 'utf-8'

MESSAGE_TERMINATOR = b'\n'

TYPE_KEY = 'type'
USERNAME_KEY = 'northeastern_username'
ID_KEY = 'id'
GUESS_KEY = 'word'
MESSAGE_KEY = 'message'
PREVIOUS_ATTEMPTS_KEY = 'guesses'
SCORE_KEY = 'marks'
SECRET_KEY = 'flag'
# ----------------------------------------------------------------

def select_word(word_list: List[str]):
    """
    Pick a word from the path to an endline separated word list
    """
    raw_word = random.choice(word_list.readlines())
    # remove endline
    return raw_word.strip()


class MessageType(Enum):
    HELLO = "hello"
    GUESS = "guess"
    UNKNOWN = ""

class ResponseType(Enum):
    ERROR = "error"
    START = "start"
    RETRY = "retry"
    BYE = "bye"

@dataclass
class Response:
    form: ResponseType
    contents: Dict[str, str]

@dataclass
class ErrorResponse(Response):
    form = ResponseType.ERROR

    @classmethod
    def from_msg(cls, msg: str) -> 'ErrorResponse':
        return ErrorResponse(cls.form, contents={MESSAGE_KEY: msg})


def read_terminated_msg(read_bytes: Callable[[int, int], bytes]) -> bytes:
    """
    Continue reading bytes until a termination character has been reached
    """
    msg = b''
    while True:
        msg = b''.join((msg, read_bytes(DEFAULT_BUFFER)))
        if msg.endswith(MESSAGE_TERMINATOR):
            return msg

def read_terminated_json(reader: Callable[[int, int], bytes]) -> Any:
    """
    Read an entire terminated JSON message
    """
    raw_msg = read_terminated_msg(reader)

    msg_str = str(raw_msg, DEFAULT_ENCODING)

    try:
        json_msg = json.loads(msg_str)
    except json.JSONDecodeError:
        json_msg = None

    return json_msg

def parse_message_type(msg_str: str) -> MessageType:
    try:
        message = MessageType(msg_str)
    except KeyError:
        message = MessageType.UNKNOWN

    return message


def respond(client_sock: socket.socket, resp: Response):
    """
    Send a formatted response back to the client socket
    """
    full_contents = {TYPE_KEY: resp.form.value, **resp.contents}
    serialized_message = json.dumps(full_contents)

    byte_message = serialized_message.encode()
    terminated_message = b''.join((byte_message, MESSAGE_TERMINATOR))

    client_sock.send(terminated_message)


def generate_player_id(username: str) -> str:
    return username[:-2] if len(username) > 4 else username
 


def classify_message(received_msg: Any, *msg_args) -> Generator[Tuple[bool, Any], None, None]:
    """
    Extract the components from a received message or return False if they do not exist
    """
    if not isinstance(received_msg, dict):
        yield False, None
        return

    yield True

    raw_msg_type = received_msg.get(TYPE_KEY, False)
    yield parse_message_type(raw_msg_type)

    for arg in msg_args:
        yield received_msg.get(arg, False)


def form_hello_response(received_message: Any) -> Tuple[bool, Response]:
    """
    Handles signing up a potential player for a game.

    :return: (True, <playername>) if valid else (False, <err_msg>)
    """
    valid, msg_type, username = classify_message(received_message, USERNAME_KEY)

    if not valid:
        return False, ErrorResponse.from_msg("Unknown message format")

    if not msg_type == MessageType.HELLO:
        return False, ErrorResponse.from_msg("Need to send a hello message as the first contact")
        
    if not username:
        return False, ErrorResponse.from_msg("Malformed message")

    player_id = generate_player_id(username)
    return player_id, Response(ResponseType.START, contents={ID_KEY: player_id})
    

def make_guess(game, player_id, guess) -> Tuple[bool, Response]:
    if game.guess_limit_reached():
        return False, ErrorResponse.from_msg("Took too many attempts to guess the word")

    try:
        marks, package = game.make_guess(player_id, guess)
    except InvalidPlayerException as err:
        return False, ErrorResponse.from_msg(f"Unknown player id {player_id}")
    except InvalidGuessException as err:
        return False, ErrorResponse.from_msg(f"Guess did not match expected format")
    
    if all((m == LetterIndicator.CORRECT_POSITION for m in marks)):
        return False, Response(ResponseType.BYE, contents={ID_KEY: player_id, SECRET_KEY: package})

    else:
        mark_converter = lambda score: [letter_indicator.value for letter_indicator in score]
        all_marks = [{GUESS_KEY: g, SCORE_KEY: mark_converter(m)} 
                    for (g,m) in 
                    package + [(guess, marks)]]
        return True, Response(ResponseType.RETRY, contents=all_marks)


def form_guess_response(received_message: Any, game: Wordle) -> Tuple[bool, Response]:
    """
    Indicate whether the game should continue and what the player response should be. 

    :return: (False, <response>) if game is over else (True, <response>)
    """
    valid, msg_type, player_id, word = classify_message(received_message, USERNAME_KEY, ID_KEY, GUESS_KEY)

    if not valid:
        return False, ErrorResponse.from_msg("Unknown message format")

    if not msg_type == MessageType.GUESS:
        return False, ErrorResponse.from_msg("Need to send a guess message after first contact")

    return make_guess(game, player_id, word)


def run_client_game(server_sock: socket.socket, with_words: List[str]):
    """
    Accept a single client and communicate until game is over
    """
    client_sock, addr = server_sock.accept()

    with client_sock:
        hello_json = read_terminated_json(client_sock.recv)
        player_id, response = form_hello_response(hello_json)

        respond(client_sock, response)

        if not player_id:
            return

        player_word = select_word(with_words)
        game = Wordle(player_word, player_id) # this is jank

        game_active = True
        while game_active:
            guess_json = read_terminated_json(client_sock.recv)
            game_active, response = form_guess_response(guess_json, game)

            respond(client_sock, response)
            
def run_server(address: Tuple[str, int], use_tls: bool, word_options: List[str]):
    """
    Run the server that can be connected to by clients
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as sock:
        sock.bind(address)

        client_backlog = 1
        sock.listen(client_backlog) 

        if not use_tls:
            run_client_game(sock, with_words=word_options)
        else:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

            with context.wrap_socket(sock, server_side=True) as wrapped_sock: 
                run_client_game(wrapped_sock, with_words=word_options)