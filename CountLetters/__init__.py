"""Top-level package entry for CountLetters.

Re-export the nested `LetterCounter.letter_counter` module so callers can do

    from CountLetters import letter_counter

and the tests / example code will continue to work.
"""

# Import the nested submodule (this will load CountLetters.LetterCounter.letter_counter
# as the attribute `letter_counter` on the top-level package).
from .LetterCounter import letter_counter

__all__ = ["letter_counter"]
