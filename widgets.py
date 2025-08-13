# widgets.py

from textual.widgets import Static

class FallingNote(Static):
    """A widget representing a single falling note."""
    def __init__(self, note: str, duration: float, **kwargs) -> None:
        super().__init__("", **kwargs)
        self.note = note
        self.duration = duration
        self.styles.height = int(duration * 20)


class PianoKey(Static):
    """A single piano key widget."""
    def __init__(self, note: str, keyboard_key: str, is_black: bool, **kwargs) -> None:
        super().__init__(keyboard_key, **kwargs)
        self.note = note
        self.keyboard_key = keyboard_key
        self.is_black = is_black
        self.add_class("key")
        self.add_class("key--black" if is_black else "key--white")

    def on_click(self) -> None:
        # We find the screen and call its method
        self.screen.handle_player_note_press(self.note)