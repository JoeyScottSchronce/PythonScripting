# LetterCounter

Small utility to count letters (A-Z) in a text string or file. Counts are
case-insensitive and non-letter characters are ignored.

## Features

- Count letters in-memory via `count_letters_in_text`
- Count letters from a file via `count_letters_in_file`
- Simple CLI for scripting and piping

## Quick usage

Python API:

```py
from LetterCounter.letter_counter import count_letters_in_text

print(count_letters_in_text('Hello, world!'))
# Counter({'L': 3, 'O': 2, 'H': 1, 'E': 1, 'W': 1, 'R': 1, 'D': 1})
```

CLI:


Read a file (output shows count and percent, highest-first):

```powershell
python -m LetterCounter.letter_counter --file C:\path\to\file.txt
```

Read from stdin (useful in pipelines):

```powershell
Get-Content sample.txt | python -m LetterCounter.letter_counter

Example CLI output (sorted by percentage):

```
A: 120 (12.34%)
E: 110 (11.28%)
O: 90  (9.24%)
... rest of letters ...
Z: 0   (0.00%)
```
```

## Tests

This project uses pytest. From the repository root:

```powershell
python -m pytest -q
```

## Notes

- Non-letter characters are ignored (numbers, punctuation, spaces).
- Letters are normalized to uppercase in counts.