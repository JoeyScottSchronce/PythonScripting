import sys
import io
from collections import Counter
from pathlib import Path

from CountLetters import letter_counter


def test_count_letters_in_text_basic():
    text = "Hello, World!"
    result = letter_counter.count_letters_in_text(text)
    # Uppercased counts
    expected = Counter({'L': 3, 'O': 2, 'H': 1, 'E': 1, 'W': 1, 'R': 1, 'D': 1})
    assert result == expected


def test_count_letters_in_file(tmp_path: Path):
    p = tmp_path / "sample.txt"
    p.write_text("abcABC123!\nAnother Line\n")

    result = letter_counter.count_letters_in_file(p)
    # Counts: A(3), B(2), C(2), N(2), O(1), T(1), H(1), E(2), R(1), L(1), I(1)
    assert result['A'] == 3
    assert result['B'] == 2
    assert result['C'] == 2
    assert result['N'] >= 1


def test_cli_reads_stdin(monkeypatch, capsys):
    monkeypatch.setattr(sys, 'stdin', io.StringIO('xXy'))
    rc = letter_counter.main([])
    out, err = capsys.readouterr()
    assert rc == 0
    # ensure output contains counts for X and Y
    assert 'X: 2' in out or 'Y: 1' in out


def test_cli_missing_file_returns_error():
    rc = letter_counter.main(['--file', 'this_file_does_not_exist.txt'])
    assert rc == 2


def test_format_counts_sorted_and_percentage():
    counts = {'A': 3, 'B': 1, 'C': 2}
    out = letter_counter.format_counts(counts)
    lines = out.splitlines()

    # Totals = 6 -> A 50.00%, C 33.33%, B 16.67%
    assert lines[0].startswith('A: 3 (50.00%')
    assert lines[1].startswith('C: 2 (33.33%')
    assert lines[2].startswith('B: 1 (16.67%')

