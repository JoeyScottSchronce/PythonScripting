# TypingDashboard

A simple Tkinter-based typing dashboard and on-screen keyboard.

This repository contains a small, lightweight GUI useful as an assisting aid in learning to type with a BEAKL 15 keyboard and it's a good starting point
for building a typing tutor or dashboard. It shows a text entry area and an
on-screen keyboard that highlights keys when clicked or when pressed on the
physical keyboard.

## Features

- Minimal, dependency-free (uses Python's stdlib tkinter)
- On-screen BEAKL 15 keyboard with clickable keys and visual highlights
- Displays typed text and keeps caret visible
- Toggleable Caps Lock and momentary Shift for virtual keys

## File

- `dashboard.py` — main application file. Run this to launch the typing
  dashboard UI.

## Requirements

- Python 3.8+ (or a current Python 3)
- tkinter (usually bundled with the standard Python distribution on
  Windows and many Linux distributions)

## Run

Open a terminal in this folder and run:

```pwsh
python dashboard.py
```

On Windows, if your Python executable is `python3` or you use a virtual
environment, adjust the command accordingly.

## Notes

- The UI is intentionally small and simple so it can be adapted and extended
  for exercises, lessons, or keyboard layout experiments.
- There are no external dependencies or configuration required.

## License

See the project-level LICENSE file in the repository root.
