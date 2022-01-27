# AUTHOR: Jan Ritzenhoff

from typing import Tuple, List

from enum import Enum
from collections import Counter


# ----------------------------------------------------------------
# CONSTANTS
MAX_CLIENT_GUESSES = 500

SECRET_MESSAGE = 'rekt_nerd' # if wordle is completed, this is the expected message
# ----------------------------------------------------------------

class InvalidPlayerException(Exception):
    pass

class InvalidGuessException(Exception):
    pass


class LetterIndicator(Enum):
    NOT_PRESENT = 0
    WRONG_POSITION = 1
    CORRECT_POSITION = 2


class Wordle:
    game_word: str
    player_guesses: List[Tuple[str, List[LetterIndicator]]]

    def __init__(self, game_word, player_id) -> None:
        self.game_word = game_word
        self.player_id = player_id

        self.player_guesses = []

    def guess_limit_reached(self) -> bool:
        return len(self.player_guesses) >= MAX_CLIENT_GUESSES

    def _correct_and_remaining_chars(self, guess) -> Tuple[List[LetterIndicator], Counter, Counter]:
        guess_counter = Counter(guess)
        actual_counter = Counter(self.game_word)

        marks: List[LetterIndicator] = []

        for guess_char, actual_char in zip(guess, self.game_word):
            if guess_char == actual_char:
                marks.append(LetterIndicator.CORRECT_POSITION)
                guess_counter[guess_char] -= 1
                actual_counter[actual_char] -= 1
            else:
                marks.append(LetterIndicator.NOT_PRESENT)

        return marks, guess_counter, actual_counter
    
    def _presence_from_remaining_letters(self, guess, marks, guess_counter, actual_counter) -> Tuple[List[LetterIndicator]]:
        for index, (guess_char, actual_char) in enumerate(zip(guess, self.game_word)):
            if marks[index] == LetterIndicator.CORRECT_POSITION:
                continue

            if guess_counter.get(guess_char) and actual_counter.get(guess_char):
                marks[index] = LetterIndicator.WRONG_POSITION
                guess_counter[guess_char] -= 1
                actual_counter[guess_char] -= 1
                continue

            marks[index] = LetterIndicator.NOT_PRESENT

        return marks

    def make_guess(self, guesser_id: int, guess: str) -> List[LetterIndicator]:
        if not guesser_id == self.player_id:
            raise InvalidPlayerException()

        if not len(guess) == len(self.game_word):
            raise InvalidGuessException()

        # first pass to check for correct character positions
        correct_marks, remaining_guess_chars, remaining_actual_chars = self._correct_and_remaining_chars(guess)

        if sum((val for _, val in remaining_guess_chars.items())) == 0:
            return correct_marks, SECRET_MESSAGE
        
        # second pass to take care of stragglers
        final_marks = self._presence_from_remaining_letters(guess, correct_marks, remaining_guess_chars, remaining_actual_chars)

        self.player_guesses.append((guess, final_marks))
        return final_marks, self.player_guesses[:-1]


if __name__ == "__main__":
    player_id = "heyo"
    game = Wordle(player_id=player_id, game_word="hello")

    translator = lambda res: [li.value for li in res]

    for g in ["hhhhh", "hlhlf", "hello"]:
        result, more = game.make_guess(player_id, g)

        debug_result = translator(result)
        debug_more = [(prev, translator(guess)) for (prev, guess) in more] if not isinstance(more, str) else more
        print(f"{g} = {debug_result} + {debug_more}")