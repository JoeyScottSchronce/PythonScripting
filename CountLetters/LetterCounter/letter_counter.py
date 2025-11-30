"""Letter counting utilities.

This module provides functions to count alphabetic characters (A-Z) in
strings or files and a small command-line interface for quick usage.

Examples
--------
>>> from letter_counter import count_letters_in_text
>>> count_letters_in_text('Hello World!')
Counter({'L': 3, 'O': 2, 'H': 1, 'E': 1, 'W': 1, 'R': 1, 'D': 1})

The CLI prints counts in alphabetical order if run with a filename:

	python -m LetterCounter.letter_counter --file /path/to/dict.txt

"""

from collections import Counter
import argparse
import sys
from pathlib import Path
from typing import Counter as CounterType, Dict


def count_letters_in_text(text: str) -> CounterType[str]:
	"""Count letters A-Z in ``text`` (case-insensitive).

	Non-letter characters are ignored. Letters are normalized to uppercase
	so the counts are case-insensitive.

	Args:
		text: Input text to analyze.

	Returns:
		collections.Counter mapping uppercase letters to counts.
	"""
	# Filter to ASCII letters, convert to uppercase and count
	letters = (ch.upper() for ch in text if ch.isalpha())
	return Counter(letters)


def count_letters_in_file(path: str | Path, encoding: str = "utf-8") -> CounterType[str]:
	"""Count letters from a text file.

	Args:
		path: Path to a file to read.
		encoding: Encoding used to open the file.

	Returns:
		collections.Counter mapping uppercase letters to counts.
	"""
	p = Path(path)
	if not p.exists():
		raise FileNotFoundError(p)

	c: CounterType[str] = Counter()
	# Read in chunks in case of very large files
	with p.open("r", encoding=encoding, errors="ignore") as fh:
		for line in fh:
			c.update(count_letters_in_text(line))
	return c


def format_counts(counts: Dict[str, int]) -> str:
	"""Return a human readable string of the counts including percentages.

	The output lists letters with their count and the percentage of the total
	letters scanned, sorted from highest percentage to lowest. All letters
	A..Z are shown, formatted like:

		A: 12 (24.00%)
		B: 4 (8.00%)
		...

	Args:
		counts: Mapping of uppercase letters to counts.

	Returns:
		A multi-line string containing letters and their counts/percentages
		sorted by percentage (highest first).
	"""
	# Ensure counts contains entries for A..Z so sorting is consistent
	letters = list(map(chr, range(65, 91)))
	total = sum(counts.get(letter, 0) for letter in letters)

	def item_key(letter: str) -> float:
		# higher percentage sorts first; when equal, fallback to letter
		cnt = counts.get(letter, 0)
		pct = (cnt / total * 100.0) if total else 0.0
		return (-pct, letter)

	sorted_letters = sorted(letters, key=item_key)

	lines = []
	for letter in sorted_letters:
		cnt = counts.get(letter, 0)
		pct = (cnt / total * 100.0) if total else 0.0
		lines.append(f"{letter}: {cnt} ({pct:.2f}%)")

	return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
	"""Simple CLI to count letters in a file or from stdin.

	Returns a small integer exit code (0 success, non-zero on error).
	"""
	parser = argparse.ArgumentParser(description="Count letters A-Z in a file or stdin")
	parser.add_argument("--file", "-f", type=str, help="Path to a text file. If omitted, read from stdin.")
	args = parser.parse_args(argv)

	try:
		if args.file:
			counts = count_letters_in_file(args.file)
		else:
			# Read all of stdin (useful for piping)
			text = sys.stdin.read()
			counts = count_letters_in_text(text)

		# Print results
		print(format_counts(counts))
		return 0
	except FileNotFoundError as exc:
		print(f"ERROR: file not found: {exc}", file=sys.stderr)
		return 2
	except Exception as exc:  # pragma: no cover - defensive
		print(f"Unexpected error: {exc}", file=sys.stderr)
		return 1


if __name__ == "__main__":
	raise SystemExit(main())
