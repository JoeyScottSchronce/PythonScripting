"""Small tkinter-based on-screen keyboard + typed-text display

Run this file to open a simple keyboard GUI. Click keys or type on your hardware
keyboard and the GUI will show pressed keys and insert characters into the text box.

This is intentionally lightweight and suitable as a starting point for a
typing tutor/dashboard project.
"""

import tkinter as tk
from functools import partial


KEY_ROWS = [
    ['`', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', 'Backspace'],
    ['Tab', 'q', 'h', 'o', 'u', 'x', 'g', 'c', 'r', 'f', 'z', '[', ']', '\\'],
    ['Caps', 'y', 'i', 'e', 'a', '/', 'd', 's', 't', 'n', 'b', ";", 'Enter'],
    ['Shift', 'j', ',', '.', 'k', '"', 'w', 'm', 'l', 'p', 'v', 'Shift'],
    ['Ctrl', 'Win', 'Alt', 'Space', 'Alt', 'Win', 'Menu', 'Ctrl']
]

# Keys to color specially on-screen (BEAKL main row focus - 'yieastnb')
BEAKL_HIGHLIGHT_KEYS = {k.lower() for k in list('yieastnb')}
BEAKL_HIGHLIGHT_BG = "#d2d2d2"  # light grey


class TypingDashboard(tk.Tk):
    """Main app window containing a text display and an on-screen keyboard."""

    def __init__(self):
        super().__init__()
        self.title("BEAKL 15 Dashboard")
        self.geometry("980x440")
        self.configure(bg="#f0f0f0")

        self.caps_lock = False
        # Track pending flash timers and original backgrounds so we can
        # cancel/reset color changes when keys are released (or re-flashed)
        # mapping: btn -> (after_id, orig_bg)
        self._flash_timers = {}

        # Top area: label and text box
        top_frame = tk.Frame(self, bg=self['bg'])
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 4))

        label = tk.Label(top_frame, text="Begin typing:", bg=self['bg'], font=(None, 11))
        label.pack(anchor='w')

        # Make the caret clearly visible: set insertbackground and insertwidth
        # and allow a focus highlight so the caret and focused state are obvious.
        self.text = tk.Text(
            top_frame,
            height=5,
            wrap='word',
            font=(None, 18),
            insertbackground='#000000',
            insertwidth=2,
            highlightthickness=2,
            highlightbackground='#cccccc',
        )
        self.text.pack(fill=tk.X, expand=True)
        # Ensure the text widget starts focused so the caret is visible.
        self.text.focus_set()
        # Clicking into the text widget should keep focus (and thus caret).
        self.text.bind('<1>', lambda e: self.text.focus_set())

        # Keyboard area
        kb_frame = tk.Frame(self, bg="#d9d9d9", padx=150, pady=8)
        kb_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(4, 12))

        self.key_buttons = {}

        for r, row in enumerate(KEY_ROWS):
            row_frame = tk.Frame(kb_frame, bg=kb_frame['bg'])
            row_frame.pack(anchor='w', pady=2, fill=tk.X)

            for c, key in enumerate(row):
                # color BEAKL-specific keys with a light-blue background
                bg = BEAKL_HIGHLIGHT_BG if key.lower() in BEAKL_HIGHLIGHT_KEYS else None
                btn = tk.Button(row_frame, text=key.upper() if len(key) == 1 else key,
                                width=self._key_width(key), height=2,
                                relief='raised', bg=bg)

                btn.pack(side=tk.LEFT, padx=3)
                btn.bind('<Button-1>', partial(self._on_button_click, key))
                self.key_buttons[key.lower()] = btn

        # Bind physical keypresses to highlight and insert
        self.bind_all('<KeyPress>', self._on_keypress)
        self.bind_all('<KeyRelease>', self._on_keyrelease)

        # Ensure the window is launched centered on the screen
        self.after(0, self._center_window)

    def _center_window(self):
        """Center the toplevel window on the current screen.

        We call this with after(0) so the window has been created and
        geometry has been applied. Using winfo_width/height gives the
        actual size including decorations on some platforms.
        """
        try:
            # Ensure layout is calculated
            self.update_idletasks()
            width = self.winfo_width()
            height = self.winfo_height()
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            x = max(0, (screen_w - width) // 2)
            y = max(0, (screen_h - height) // 2)
            self.geometry(f"{width}x{height}+{x}+{y}")
        except Exception:
            # If anything goes wrong, silently continue — app still usable
            pass

    def _key_width(self, key: str) -> int:
        """Return a reasonable width for a key based on its label."""
        match key:
            case k if len(k) == 1:
                return 4
            case "Space":
                return 35
            case "Enter" | "Backspace":
                return 11
            case "Tab":
                return 8
            case "Caps":
                return 10
            case "Shift":
                return 14
            case _:
                return 6

    def _on_button_click(self, key_label, _event):
        """Handle clicks on the on-screen key buttons."""
        key = key_label.lower()
        if key == 'backspace':
            self._backspace()
        elif key == 'space':
            self._insert_char(' ')
        elif key == 'tab':
            self._insert_char('\t')
        elif key == 'enter':
            self._insert_char('\n')
        elif key == 'caps':
            self.caps_lock = not self.caps_lock
            self._update_caps_visual()
        elif key == 'shift':
            # shift is handled as momentary toggle on virtual clicks
            self._momentary_shift()
        else:
            # letter or symbol
            self._insert_char(self._apply_case(key_label))

        # Visual highlight for clicks
        btn = self.key_buttons.get(key)
        if btn:
            self._flash_button(btn)
        # After a virtual key click, return focus to the text widget so the
        # caret remains visible for typing.
        try:
            self.text.focus_set()
        except Exception:
            pass

    def _on_keypress(self, event):
        
        key = event.keysym.lower()

        # Highlight corresponding button if exists
        btn = self.key_buttons.get(key)
        if btn:
            self._flash_button(btn)

    def _on_keyrelease(self, event):
        # When a physical key is released we should ensure the on-screen
        # button returns to its original color. If the key had an active
        # flash timer we cancel it and restore the stored original background.
        key = event.keysym.lower()
        btn = self.key_buttons.get(key)
        if not btn:
            return

        # If there is an active flash timer for this button cancel and
        # restore the original bg immediately.
        entry = self._flash_timers.pop(btn, None)
        if entry:
            timer_id, orig_bg = entry
            try:
                if timer_id:
                    self.after_cancel(timer_id)
            except Exception:
                # ignore if timer can't be cancelled
                pass
            try:
                btn.configure(bg=orig_bg)
            except Exception:
                pass
            return

        # If no flash timer recorded, fall back to expected default colors
        # (caps state or BEAKL highlight keys) so held keys are always
        # visually consistent after release.
        try:
            if key == 'caps':
                btn.configure(bg=('lightgreen' if self.caps_lock else 'SystemButtonFace'))
                return

            if key in BEAKL_HIGHLIGHT_KEYS:
                btn.configure(bg=BEAKL_HIGHLIGHT_BG)
            else:
                btn.configure(bg='SystemButtonFace')
        except Exception:
            pass

    def _momentary_shift(self):
        """Temporarily apply shift (capitalize next letter). Simulated for virtual clicks."""
        # Next inserted letters will be capitalized once — simple approach
        # We'll set a temporary flag in instance and consume in _insert_char
        self._shift_next = True

    def _apply_case(self, key_label: str) -> str:
        """Return the character adjusted for caps lock or a pending shift."""
        ch = key_label
        if len(ch) == 1 and ch.isalpha():
            # Shift has higher priority
            if getattr(self, '_shift_next', False):
                ch = ch.upper()
                self._shift_next = False
            elif self.caps_lock:
                ch = ch.upper()
        return ch

    def _insert_char(self, ch: str):
        self.text.insert('end', ch)
        self.text.see('end')

    def _backspace(self):
        # Delete previous character if any
        try:
            index = self.text.index('insert')
            # move to previous char
            prev = self.text.index('%s -1c' % index)
            self.text.delete(prev, index)
        except tk.TclError:
            pass

    def _update_caps_visual(self):
        # Update Caps button background to show on/off state
        btn = self.key_buttons.get('caps')
        if btn:
            btn.configure(bg=('lightgreen' if self.caps_lock else 'SystemButtonFace'))

    def _flash_button(self, btn: tk.Button, duration: int = 120):
        # If a flash is already pending, cancel its timer (we'll replace it)
        existing = self._flash_timers.get(btn)
        if existing:
            timer_id, orig = existing
            try:
                if timer_id:
                    self.after_cancel(timer_id)
            except Exception:
                # ignore cancel errors
                pass
        else:
            orig = btn.cget('bg')

        # Apply highlight
        try:
            btn.configure(bg='lightblue')
        except Exception:
            pass

        # Schedule reset and remember the timer id + original bg
        try:
            after_id = self.after(duration, lambda b=btn: self._reset_button_bg(b))
        except Exception:
            after_id = None

        self._flash_timers[btn] = (after_id, orig)

    def _reset_button_bg(self, btn: tk.Button):
        """Reset owned button background to the original color and clear timer."""
        entry = self._flash_timers.pop(btn, None)
        if not entry:
            return
        _, orig_bg = entry
        try:
            btn.configure(bg=orig_bg)
        except Exception:
            pass


def main():
    app = TypingDashboard()
    app.mainloop()


if __name__ == '__main__':
    main()